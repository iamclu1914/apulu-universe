"""FastAPI app factory and REST routes for Apulu HQ v0.

Endpoints (Phase 1):
  GET    /api/health
  GET    /api/agents
  GET    /api/agents/{id}
  PATCH  /api/agents/{id}              (model/provider/system_prompt only in v0)
  POST   /api/agents/{id}/chat         (streams via WS; returns thread_id)
  GET    /api/agents/{id}/threads      (list chat threads)
  GET    /api/threads/{id}/messages    (full message history)
  GET    /api/routines
  PATCH  /api/routines/{id}            (enable / disable / disabled_reason)
  GET    /api/dlq
  WS     /ws                           (subscribes to live event stream)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import (
    FastAPI,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ..__init__ import __version__
from ..config import settings
from ..db import get_conn, json_loads_safe
from ..events import Event, get_bus
from ..tailer import TailerConfig, start_tailers, stop_tailers

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic request/response models
# ---------------------------------------------------------------------------


class AgentOut(BaseModel):
    id: str
    legacy_id: str | None
    display_name: str
    department: str
    role: str
    adapter_type: str
    model: str | None
    provider: str | None
    system_prompt: str | None
    desk_x: int
    desk_y: int
    sprite_key: str
    enabled: bool


class AgentPatch(BaseModel):
    model: str | None = None
    provider: str | None = None
    system_prompt: str | None = None
    enabled: bool | None = None


class RoutineOut(BaseModel):
    id: str
    display_name: str
    agent_id: str
    cron_expr: str
    timezone: str
    description: str | None
    priority: str
    enabled: bool
    disabled_reason: str | None


class RoutinePatch(BaseModel):
    enabled: bool | None = None
    disabled_reason: str | None = None


class ChatRequest(BaseModel):
    message: str
    thread_id: str | None = None


# ---------------------------------------------------------------------------
# Heartbeat task — emits one event every 10s so the UI knows the WS is alive
# ---------------------------------------------------------------------------


async def _heartbeat_loop() -> None:
    bus = get_bus()
    while True:
        try:
            conn = get_conn()
            n_agents = conn.execute("SELECT COUNT(*) AS c FROM agents").fetchone()["c"]
            n_routines = conn.execute("SELECT COUNT(*) AS c FROM routines").fetchone()["c"]
            enabled = conn.execute(
                "SELECT COUNT(*) AS c FROM routines WHERE enabled=1"
            ).fetchone()["c"]
            await bus.publish(
                Event(
                    type="heartbeat",
                    payload={
                        "agents": n_agents,
                        "routines": n_routines,
                        "enabled_routines": enabled,
                        "subscribers": bus.subscriber_count,
                    },
                )
            )
        except Exception:
            log.exception("heartbeat failed")
        await asyncio.sleep(10)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.ensure_dirs()
    # Touch DB to ensure schema bootstrap
    get_conn()
    heartbeat = asyncio.create_task(_heartbeat_loop())
    tailers: list[asyncio.Task] = []
    if os.environ.get("APULU_HQ_DISABLE_TAILERS") != "1":
        try:
            tailers = await start_tailers()
        except Exception:
            log.exception("failed to start tailers")

    # Scheduler — defaults to shadow mode (HQ_DISPATCHER_SHADOW != "0").
    # Disabled in tests by APULU_HQ_DISABLE_SCHEDULER=1.
    app.state.scheduler = None
    if os.environ.get("APULU_HQ_DISABLE_SCHEDULER") != "1":
        try:
            from ..dispatch import HQScheduler
            app.state.scheduler = HQScheduler(bus=get_bus(), cwd=str(settings.data_dir))
            await app.state.scheduler.start()
        except Exception:
            log.exception("failed to start scheduler")

    try:
        yield
    finally:
        heartbeat.cancel()
        try:
            await heartbeat
        except asyncio.CancelledError:
            pass
        if tailers:
            await stop_tailers(tailers)
        if app.state.scheduler is not None:
            try:
                await app.state.scheduler.stop()
            except Exception:
                log.exception("scheduler shutdown error")


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    app = FastAPI(
        title="Apulu HQ",
        version=__version__,
        description="Interactive label operations app (replaces Paperclip orchestration).",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # local-only app; binds to 127.0.0.1
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ---- health ----
    @app.get("/api/health")
    def health():
        conn = get_conn()
        agents = conn.execute("SELECT COUNT(*) AS c FROM agents").fetchone()["c"]
        routines = conn.execute("SELECT COUNT(*) AS c FROM routines").fetchone()["c"]
        return {
            "ok": True,
            "version": __version__,
            "data_dir": str(settings.data_dir),
            "db_path": str(settings.db_path),
            "agents": agents,
            "routines": routines,
            "anthropic_key_set": bool(settings.anthropic_api_key),
            "model": settings.default_chat_model,
        }

    # ---- agents ----
    @app.get("/api/agents")
    def list_agents() -> list[AgentOut]:
        rows = get_conn().execute(
            "SELECT id, legacy_id, display_name, department, role, adapter_type, model, "
            "provider, system_prompt, desk_x, desk_y, sprite_key, enabled "
            "FROM agents ORDER BY department, display_name"
        ).fetchall()
        return [AgentOut(**{**dict(r), "enabled": bool(r["enabled"])}) for r in rows]

    @app.get("/api/agents/{agent_id}")
    def get_agent(agent_id: str) -> AgentOut:
        row = get_conn().execute(
            "SELECT id, legacy_id, display_name, department, role, adapter_type, model, "
            "provider, system_prompt, desk_x, desk_y, sprite_key, enabled "
            "FROM agents WHERE id=?",
            (agent_id,),
        ).fetchone()
        if not row:
            raise HTTPException(404, f"Agent not found: {agent_id}")
        return AgentOut(**{**dict(row), "enabled": bool(row["enabled"])})

    @app.patch("/api/agents/{agent_id}")
    def patch_agent(agent_id: str, body: AgentPatch) -> AgentOut:
        conn = get_conn()
        cur = conn.execute("SELECT id FROM agents WHERE id=?", (agent_id,)).fetchone()
        if not cur:
            raise HTTPException(404, f"Agent not found: {agent_id}")
        fields = body.model_dump(exclude_unset=True)
        if not fields:
            return get_agent(agent_id)
        sets = ", ".join(f"{k}=:{k}" for k in fields)
        params = {**fields, "id": agent_id}
        if "enabled" in params:
            params["enabled"] = 1 if params["enabled"] else 0
        conn.execute(f"UPDATE agents SET {sets}, updated_at=datetime('now') WHERE id=:id", params)
        conn.commit()
        return get_agent(agent_id)

    @app.get("/api/agents/{agent_id}/threads")
    def list_threads(agent_id: str):
        rows = get_conn().execute(
            "SELECT id, title, created_at, updated_at FROM chat_threads WHERE agent_id=? "
            "ORDER BY updated_at DESC LIMIT 50",
            (agent_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    @app.get("/api/threads/{thread_id}/messages")
    def get_messages(thread_id: str):
        rows = get_conn().execute(
            "SELECT id, role, content, tokens_in, tokens_out, created_at "
            "FROM chat_messages WHERE thread_id=? ORDER BY created_at ASC",
            (thread_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    # ---- chat (kicks off streaming via WS) ----
    @app.post("/api/agents/{agent_id}/chat")
    async def post_chat(agent_id: str, body: ChatRequest):
        # Verify agent exists
        row = get_conn().execute("SELECT id FROM agents WHERE id=?", (agent_id,)).fetchone()
        if not row:
            raise HTTPException(404, f"Agent not found: {agent_id}")

        from ..chat import publish_chat  # local import to avoid circular at startup

        async def _run_chat():
            try:
                await publish_chat(
                    agent_id=agent_id,
                    user_message=body.message,
                    thread_id=body.thread_id,
                )
            except Exception:
                log.exception(
                    "chat task crashed agent=%s thread=%s",
                    agent_id, body.thread_id,
                )

        # Fire and forget — caller subscribes to WS for tokens
        task = asyncio.create_task(_run_chat())
        # Hold a strong ref so the task isn't GC'd mid-flight (a Python 3.11+ pitfall).
        if not hasattr(app.state, "chat_tasks"):
            app.state.chat_tasks = set()
        app.state.chat_tasks.add(task)
        task.add_done_callback(app.state.chat_tasks.discard)

        return {"accepted": True, "agent_id": agent_id, "thread_id_hint": body.thread_id}

    # ---- routines ----
    @app.get("/api/routines")
    def list_routines() -> list[RoutineOut]:
        rows = get_conn().execute(
            "SELECT id, display_name, agent_id, cron_expr, timezone, description, priority, "
            "enabled, disabled_reason FROM routines ORDER BY display_name"
        ).fetchall()
        return [RoutineOut(**{**dict(r), "enabled": bool(r["enabled"])}) for r in rows]

    @app.patch("/api/routines/{routine_id}")
    async def patch_routine(routine_id: str, body: RoutinePatch) -> RoutineOut:
        conn = get_conn()
        row = conn.execute("SELECT id FROM routines WHERE id=?", (routine_id,)).fetchone()
        if not row:
            raise HTTPException(404, f"Routine not found: {routine_id}")
        fields = body.model_dump(exclude_unset=True)
        reload_needed = "enabled" in fields or "cron_expr" in fields or "command" in fields or "args" in fields
        if "enabled" in fields:
            fields["enabled"] = 1 if fields["enabled"] else 0
        if not fields:
            sets = ""
        else:
            sets = ", ".join(f"{k}=:{k}" for k in fields)
        params = {**fields, "id": routine_id}
        if sets:
            conn.execute(
                f"UPDATE routines SET {sets}, updated_at=datetime('now') WHERE id=:id", params
            )
            conn.commit()
        # Reload scheduler jobs when enabled/schedule/command changed
        sched = getattr(app.state, "scheduler", None)
        if reload_needed and sched is not None:
            try:
                await sched.reload_jobs()
            except Exception:
                log.exception("scheduler reload failed after routine patch")
        out = conn.execute(
            "SELECT id, display_name, agent_id, cron_expr, timezone, description, priority, "
            "enabled, disabled_reason FROM routines WHERE id=?",
            (routine_id,),
        ).fetchone()
        return RoutineOut(**{**dict(out), "enabled": bool(out["enabled"])})

    # ---- scheduler ----
    @app.get("/api/scheduler")
    def scheduler_status():
        sched = getattr(app.state, "scheduler", None)
        if sched is None:
            return {"started": False, "shadow": None, "jobs": []}
        return {
            "started": sched.started,
            "shadow": sched.shadow,
            "jobs": sched.list_jobs(),
        }

    @app.post("/api/scheduler/reload")
    async def scheduler_reload():
        sched = getattr(app.state, "scheduler", None)
        if sched is None:
            raise HTTPException(status_code=503, detail="scheduler not running")
        await sched.reload_jobs()
        return {"ok": True, "jobs": sched.list_jobs()}

    @app.post("/api/routines/{routine_id}/fire")
    async def fire_routine(routine_id: str):
        sched = getattr(app.state, "scheduler", None)
        if sched is None:
            raise HTTPException(status_code=503, detail="scheduler not running")
        row = get_conn().execute(
            "SELECT id FROM routines WHERE id=?", (routine_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="routine not found")
        dispatch_id = await sched.fire_now(routine_id)
        return {"ok": True, "dispatch_id": dispatch_id, "shadow": sched.shadow}

    # ---- dispatches ----
    @app.get("/api/dispatches")
    def list_dispatches(limit: int = 50, agent_id: str | None = None, routine_id: str | None = None):
        sql = (
            "SELECT d.id, d.routine_id, d.agent_id, d.started_at, d.ended_at, "
            "d.attempt, d.outcome, d.exit_code, d.signature, d.duration_ms, "
            "r.display_name AS routine_name, a.display_name AS agent_name "
            "FROM dispatches d "
            "LEFT JOIN routines r ON r.id = d.routine_id "
            "LEFT JOIN agents a ON a.id = d.agent_id "
        )
        clauses = []
        params: list = []
        if agent_id:
            clauses.append("d.agent_id = ?")
            params.append(agent_id)
        if routine_id:
            clauses.append("d.routine_id = ?")
            params.append(routine_id)
        if clauses:
            sql += "WHERE " + " AND ".join(clauses) + " "
        sql += "ORDER BY d.started_at DESC LIMIT ?"
        params.append(max(1, min(int(limit), 500)))
        rows = get_conn().execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    # ---- dlq ----
    @app.get("/api/dlq")
    def list_dlq():
        rows = get_conn().execute(
            "SELECT id, dispatch_id, routine_id, agent_id, signature, payload, "
            "appended_at, replayed_at, replay_outcome, discarded_at "
            "FROM dlq WHERE replayed_at IS NULL AND discarded_at IS NULL "
            "ORDER BY appended_at DESC LIMIT 200"
        ).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["payload"] = json_loads_safe(d["payload"], {})
            out.append(d)
        return out

    # ---- WebSocket gateway ----
    @app.websocket("/ws")
    async def ws(ws: WebSocket):
        await ws.accept()
        bus = get_bus()
        sub = await bus.subscribe()
        try:
            await ws.send_json(Event(type="heartbeat", payload={"hello": True}).to_wire())
            async for ev in sub.stream():
                await ws.send_json(ev.to_wire())
        except WebSocketDisconnect:
            pass
        except Exception:
            log.exception("ws gateway error")
        finally:
            await sub.close()

    # ---- static test client ----
    webclient_dir = Path(__file__).resolve().parents[2] / "webclient"
    if webclient_dir.is_dir():
        app.mount("/ui", StaticFiles(directory=str(webclient_dir), html=True), name="ui")

        @app.get("/")
        def root_redirect():
            return JSONResponse(
                {"ok": True, "ui": "/ui/", "api_health": "/api/health", "ws": "/ws"}
            )

    return app


app = create_app()
