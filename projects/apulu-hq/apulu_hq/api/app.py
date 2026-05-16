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
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, date as date_cls, timezone
from pathlib import Path

import httpx
from fastapi import (
    FastAPI,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
    Body,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ..__init__ import __version__
from ..config import settings
from ..db import get_conn, json_loads_safe
from ..events import Event, get_bus
from ..tailer import TailerConfig, start_tailers, stop_tailers

log = logging.getLogger(__name__)

PROMPT_GENERATOR_BACKEND_URL = os.environ.get(
    "APULU_PROMPT_GENERATOR_BACKEND_URL",
    "https://apulu-backend.onrender.com",
).rstrip("/")
HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
    "content-length",
    "content-encoding",
}


# ---------------------------------------------------------------------------
# Department metadata -- single source of truth for icon/color/description
# Keys are the *raw* department values stored on the agents table.
# ---------------------------------------------------------------------------

# Department heads -- the agent who manages each department and receives
# escalated tasks. CEO communicates with these heads; they coordinate
# within their teams.
DEPT_HEAD: dict[str, str] = {
    "board": "Clu",           # Chairman & CEO
    "cos": "Nelly",           # General Counsel & Head of Business Affairs
    "marketing": "Letitia",   # President, Marketing, Audience & Revenue
    "operations": "Nari",     # COO, Operations, Finance & Tech
    "production": "Timbo",    # President, A&R & Talent Development
    "post-prod": "Onyx",      # Studio & Post-Production Lead
    "research": "Rhythm",     # A&R Scout & Discovery Analyst
}


DEPT_META: dict[str, dict[str, str]] = {
    "board": {
        "label": "Office of the Chairman",
        "icon": "CEO",
        "color": "amber",
        "description": "Executive leadership, vision, and final authority on signings and strategy",
    },
    "cos": {
        "label": "Legal & Business Affairs",
        "icon": "L",
        "color": "purple",
        "description": "Contracts, licensing, publishing, clearances and artist relations",
    },
    "marketing": {
        "label": "Marketing, Audience & Revenue",
        "icon": "M",
        "color": "blue",
        "description": "Campaigns, fan acquisition, content, publicity and streaming strategy",
    },
    "operations": {
        "label": "Operations, Finance & Tech",
        "icon": "O",
        "color": "cyan",
        "description": "Infrastructure, finance, royalties, partnerships and AI orchestration",
    },
    "post-prod": {
        "label": "Post-Production",
        "icon": "PP",
        "color": "teal",
        "description": "Mixing, mastering and quality control",
    },
    "production": {
        "label": "A&R & Production",
        "icon": "AR",
        "color": "pink",
        "description": "Artist scouting, creative direction, songwriting and production",
    },
    "research": {
        "label": "Discovery & Research",
        "icon": "R",
        "color": "lime",
        "description": "Streaming/social data mining, trend analysis and breakout signal detection",
    },
}

SOCIAL_PLATFORM_META: dict[str, dict[str, str]] = {
    "instagram": {
        "label": "Instagram",
        "account_url": "https://www.instagram.com/therealvawn/",
        "website_label": "@therealvawn",
    },
    "tiktok": {
        "label": "TikTok",
        "account_url": "https://www.tiktok.com/@iamvawn",
        "website_label": "@iamvawn",
    },
    "threads": {
        "label": "Threads",
        "account_url": "https://www.threads.net/@therealvawn",
        "website_label": "@therealvawn",
    },
    "x": {
        "label": "X",
        "account_url": "https://x.com/iamvawn",
        "website_label": "@iamvawn",
    },
    "bluesky": {
        "label": "Bluesky",
        "account_url": "https://bsky.app/profile/therealvawn.bsky.social",
        "website_label": "therealvawn.bsky.social",
    },
    "facebook": {
        "label": "Facebook",
        "account_url": "",
        "website_label": "not configured",
    },
}

def _dept_meta(dept_id: str) -> dict[str, str]:
    return DEPT_META.get(
        dept_id,
        {"label": dept_id.title(), "icon": "D", "color": "purple", "description": dept_id},
    )


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


class ReleaseIn(BaseModel):
    title: str
    artist: str = "Vawn"
    type: str = "single"
    status: str = "planning"
    release_date: str | None = None
    distributor: str = "DistroKid"
    artwork_status: str = "pending"
    master_status: str = "pending"
    metadata_status: str = "pending"
    distributor_status: str = "pending"
    publishing_status: str = "pending"
    budget: float | None = None
    spend_to_date: float = 0
    notes: str | None = None


class ReleasePatch(BaseModel):
    title: str | None = None
    artist: str | None = None
    type: str | None = None
    status: str | None = None
    release_date: str | None = None
    distributor: str | None = None
    artwork_status: str | None = None
    master_status: str | None = None
    metadata_status: str | None = None
    distributor_status: str | None = None
    publishing_status: str | None = None
    budget: float | None = None
    spend_to_date: float | None = None
    notes: str | None = None


class CampaignIn(BaseModel):
    name: str
    artist: str = "Vawn"
    release_id: str | None = None
    objective: str = "awareness"
    status: str = "draft"
    start_date: str | None = None
    end_date: str | None = None
    platforms: list[str] = []
    budget: float | None = None
    spend_to_date: float = 0
    primary_metric: str | None = None
    target_value: float | None = None
    notes: str | None = None


class CampaignPatch(BaseModel):
    name: str | None = None
    artist: str | None = None
    release_id: str | None = None
    objective: str | None = None
    status: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    platforms: list[str] | None = None
    budget: float | None = None
    spend_to_date: float | None = None
    primary_metric: str | None = None
    target_value: float | None = None
    notes: str | None = None


class ApprovalIn(BaseModel):
    title: str
    category: str = "operations"
    priority: str = "medium"
    status: str = "open"
    requested_by: str | None = None
    assigned_to: str | None = "CEO"
    due_at: str | None = None
    linked_type: str | None = None
    linked_id: str | None = None
    decision_note: str | None = None


class ApprovalPatch(BaseModel):
    title: str | None = None
    category: str | None = None
    priority: str | None = None
    status: str | None = None
    requested_by: str | None = None
    assigned_to: str | None = None
    due_at: str | None = None
    linked_type: str | None = None
    linked_id: str | None = None
    decision_note: str | None = None


class FinanceEntryIn(BaseModel):
    entry_type: str = "expense"
    source: str | None = None
    vendor: str | None = None
    category: str = "operations"
    amount: float
    entry_date: str | None = None
    linked_type: str | None = None
    linked_id: str | None = None
    notes: str | None = None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _model_data(model: BaseModel) -> dict:
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_unset=True)
    return model.dict(exclude_unset=True)


def _model_all(model: BaseModel) -> dict:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _release_readiness(row: dict) -> dict:
    fields = [
        "artwork_status",
        "master_status",
        "metadata_status",
        "distributor_status",
        "publishing_status",
    ]
    done_values = {"done", "ready", "complete", "completed", "approved", "scheduled", "released"}
    done = sum(1 for key in fields if str(row.get(key) or "").lower() in done_values)
    blockers = [
        key.replace("_status", "").replace("_", " ").title()
        for key in fields
        if str(row.get(key) or "").lower() not in done_values
    ]
    next_milestone = blockers[0] if blockers else "Release ready"
    return {
        "readiness": round(100 * done / len(fields)),
        "blockers": blockers,
        "next_milestone": next_milestone,
    }


def _release_out(row) -> dict:
    data = dict(row)
    data.update(_release_readiness(data))
    return data


def _campaign_out(row) -> dict:
    data = dict(row)
    data["platforms"] = json_loads_safe(data.get("platforms"), [])
    return data


def _approval_out(row) -> dict:
    return dict(row)


def _finance_out(row) -> dict:
    return dict(row)


def _patch_row(table: str, item_id: str, payload: dict, allowed: set[str]) -> dict:
    data = {k: v for k, v in payload.items() if k in allowed}
    if not data:
        row = get_conn().execute(f"SELECT * FROM {table} WHERE id=?", (item_id,)).fetchone()
        if not row:
            raise HTTPException(404, f"{table[:-1]} not found")
        return dict(row)
    data["updated_at"] = _now_iso()
    sets = ", ".join(f"{k}=:{k}" for k in data)
    data["id"] = item_id
    conn = get_conn()
    cur = conn.execute(f"SELECT id FROM {table} WHERE id=?", (item_id,)).fetchone()
    if not cur:
        raise HTTPException(404, f"{table[:-1]} not found")
    conn.execute(f"UPDATE {table} SET {sets} WHERE id=:id", data)
    conn.commit()
    row = conn.execute(f"SELECT * FROM {table} WHERE id=?", (item_id,)).fetchone()
    return dict(row)


# ---------------------------------------------------------------------------
# Heartbeat task -- emits one event every 10s so the UI knows the WS is alive
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

    # Scheduler -- defaults to shadow mode (HQ_DISPATCHER_SHADOW != "0").
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

    # ---- departments ----
    @app.get("/api/departments")
    def list_departments():
        """All departments derived from agents, with metadata + counts + head agent."""
        conn = get_conn()
        rows = conn.execute(
            "SELECT department, COUNT(*) AS agent_count, "
            "SUM(CASE WHEN enabled=1 THEN 1 ELSE 0 END) AS online_count "
            "FROM agents GROUP BY department ORDER BY department"
        ).fetchall()
        # Build display_name -> agent_id lookup for resolving heads
        head_lookup = {
            r["display_name"]: r["id"]
            for r in conn.execute("SELECT id, display_name FROM agents").fetchall()
        }
        out = []
        for r in rows:
            meta = _dept_meta(r["department"])
            head_name = DEPT_HEAD.get(r["department"])
            out.append({
                "id": r["department"],
                "name": meta["label"],
                "icon": meta["icon"],
                "color": meta["color"],
                "description": meta["description"],
                "agentCount": r["agent_count"],
                "onlineAgentCount": int(r["online_count"] or 0),
                "headAgentId": head_lookup.get(head_name) if head_name else None,
                "headAgentName": head_name,
            })
        return out

    @app.get("/api/departments/{dept_id}/agents")
    def list_department_agents(dept_id: str):
        rows = get_conn().execute(
            "SELECT id, legacy_id, display_name, department, role, adapter_type, model, "
            "provider, system_prompt, desk_x, desk_y, sprite_key, enabled "
            "FROM agents WHERE department=? ORDER BY display_name",
            (dept_id,),
        ).fetchall()
        return [AgentOut(**{**dict(r), "enabled": bool(r["enabled"])}) for r in rows]

    # ---- agent functions (routines they own) ----
    @app.get("/api/agents/{agent_id}/routines")
    def list_agent_routines(agent_id: str):
        """Functions the agent performs -- the cron routines they own."""
        rows = get_conn().execute(
            "SELECT id, display_name, agent_id, cron_expr, timezone, description, "
            "priority, enabled, disabled_reason FROM routines WHERE agent_id=? "
            "ORDER BY enabled DESC, display_name",
            (agent_id,),
        ).fetchall()
        return [RoutineOut(**{**dict(r), "enabled": bool(r["enabled"])}) for r in rows]

    # ---- dashboard summary (KPIs) ----
    @app.get("/api/dashboard/summary")
    def dashboard_summary():
        conn = get_conn()
        total_agents = conn.execute("SELECT COUNT(*) AS c FROM agents").fetchone()["c"]
        active_agents = conn.execute(
            "SELECT COUNT(*) AS c FROM agents WHERE enabled=1"
        ).fetchone()["c"]
        total_routines = conn.execute("SELECT COUNT(*) AS c FROM routines").fetchone()["c"]
        active_routines = conn.execute(
            "SELECT COUNT(*) AS c FROM routines WHERE enabled=1"
        ).fetchone()["c"]
        n_departments = conn.execute(
            "SELECT COUNT(DISTINCT department) AS c FROM agents"
        ).fetchone()["c"]
        # Fires today
        fires_today = conn.execute(
            "SELECT COUNT(*) AS c FROM dispatches "
            "WHERE date(started_at) = date('now')"
        ).fetchone()["c"]
        # Failures + DLQ count = "pending tasks requiring attention"
        recent_failures = conn.execute(
            "SELECT COUNT(*) AS c FROM dispatches "
            "WHERE outcome IN ('failure','fail') AND date(started_at) >= date('now','-7 days')"
        ).fetchone()["c"]
        dlq_active = conn.execute(
            "SELECT COUNT(*) AS c FROM dlq "
            "WHERE replayed_at IS NULL AND discarded_at IS NULL"
        ).fetchone()["c"]
        return {
            "totalAgents": total_agents,
            "activeAgents": active_agents,
            "totalDepartments": n_departments,
            "totalRoutines": total_routines,
            "activeRoutines": active_routines,
            "firesToday": fires_today,
            "pendingTasks": recent_failures + dlq_active,
            "departmentAlerts": dlq_active,
        }

    # ---- live agent activity ----
    @app.get("/api/activity")
    def list_activity(window_minutes: int = 60):
        """Currently running dispatches + recent finished ones within a window.

        Returns:
          inProgress: dispatches with ended_at IS NULL (currently executing).
          recent: dispatches finished in the last `window_minutes` (default 60).
        """
        win = max(1, min(int(window_minutes), 1440))
        conn = get_conn()
        base = (
            "SELECT d.id, d.routine_id, d.agent_id, d.started_at, d.ended_at, "
            "d.outcome, d.duration_ms, d.attempt, "
            "r.display_name AS routine_name, r.description AS routine_description, "
            "a.display_name AS agent_name, a.department AS agent_department, "
            "a.role AS agent_role "
            "FROM dispatches d "
            "LEFT JOIN routines r ON r.id = d.routine_id "
            "LEFT JOIN agents a ON a.id = d.agent_id "
        )
        in_progress = conn.execute(
            base + "WHERE d.ended_at IS NULL ORDER BY d.started_at DESC LIMIT 20"
        ).fetchall()
        recent = conn.execute(
            base
            + "WHERE d.ended_at IS NOT NULL AND "
              "d.started_at > datetime('now', ?) "
              "ORDER BY d.started_at DESC LIMIT 30",
            (f"-{win} minutes",),
        ).fetchall()
        return {
            "inProgress": [dict(r) for r in in_progress],
            "recent": [dict(r) for r in recent],
            "windowMinutes": win,
        }

    # ---- social-media post activity (Vawn) ----
    @app.get("/api/social/platforms")
    def social_platform_status(hours: int = 24):
        """Return command-center status for Vawn social publishing channels."""
        from datetime import datetime, timezone, timedelta
        import json as _json

        window_hours = max(1, min(int(hours), 168))
        cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
        ledger_path = settings.vawn_dir / "post_ledger.jsonl"
        platforms: dict[str, dict] = {
            key: {
                "id": key,
                "label": meta["label"],
                "account_url": meta["account_url"],
                "website_label": meta["website_label"],
                "wired": bool(meta["account_url"]) or key == "facebook",
                "last_attempt_at": None,
                "last_success_at": None,
                "last_post_url": None,
                "last_post_id": None,
                "last_error": None,
                "next_scheduled_post": None,
                "ok_24h": 0,
                "fail_24h": 0,
                "media_types": set(),
                "status": "idle",
            }
            for key, meta in SOCIAL_PLATFORM_META.items()
        }

        def parse_ts(value: object) -> datetime | None:
            if not isinstance(value, str) or not value:
                return None
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                return parsed.astimezone(timezone.utc)
            except ValueError:
                return None

        def media_kind(record: dict) -> str | None:
            media = record.get("media") or record.get("image") or record.get("video_asset")
            suffix = ""
            if isinstance(media, dict):
                suffix = str(media.get("suffix") or media.get("name") or "")
            elif isinstance(media, str):
                suffix = media
            suffix = suffix.lower()
            if suffix.endswith((".mp4", ".mov", ".m4v")):
                return "video"
            if suffix.endswith((".png", ".jpg", ".jpeg", ".webp")):
                return "image"
            return None

        if ledger_path.is_file():
            try:
                with ledger_path.open("r", encoding="utf-8", errors="replace") as fh:
                    for line in fh:
                        try:
                            record = _json.loads(line)
                        except _json.JSONDecodeError:
                            continue
                        platform = str(record.get("platform") or "").lower()
                        if platform not in platforms:
                            continue
                        event_type = record.get("event") or ""
                        if event_type not in {
                            "post_attempt",
                            "story_repost_attempt",
                            "post_preflight_failed",
                            "post_exception",
                        }:
                            continue
                        ts = parse_ts(record.get("timestamp"))
                        if ts is None:
                            continue
                        item = platforms[platform]
                        kind = media_kind(record)
                        if kind:
                            item["media_types"].add(kind)
                        if item["last_attempt_at"] is None or ts.isoformat() > item["last_attempt_at"]:
                            item["last_attempt_at"] = ts.isoformat()
                            item["last_error"] = (
                                record.get("error")
                                or "; ".join(record.get("errors") or [])
                                or None
                            )
                            item["last_post_id"] = record.get("platform_post_id")
                        success = bool(record.get("success"))
                        if ts >= cutoff:
                            if success:
                                item["ok_24h"] += 1
                            else:
                                item["fail_24h"] += 1
                        if success and (item["last_success_at"] is None or ts.isoformat() > item["last_success_at"]):
                            item["last_success_at"] = ts.isoformat()
                            item["last_post_url"] = record.get("post_url")
                            item["last_post_id"] = record.get("platform_post_id")
            except OSError as exc:
                for item in platforms.values():
                    item["media_types"] = sorted(item["media_types"])
                return {"platforms": list(platforms.values()), "error": str(exc)}

        routine_rows = get_conn().execute(
            "SELECT display_name, cron_expr, description, command, args FROM routines "
            "WHERE enabled=1 ORDER BY display_name"
        ).fetchall()
        for key, item in platforms.items():
            for row in routine_rows:
                blob = " ".join(str(row[k] or "") for k in row.keys()).lower()
                if key in blob:
                    item["next_scheduled_post"] = {
                        "routine": row["display_name"],
                        "cron_expr": row["cron_expr"],
                    }
                    break

        for item in platforms.values():
            item["media_types"] = sorted(item["media_types"])
            if item["fail_24h"] and not item["ok_24h"]:
                item["status"] = "attention"
            elif item["last_success_at"]:
                item["status"] = "wired"
            elif item["last_attempt_at"]:
                item["status"] = "attention"
            elif item["wired"]:
                item["status"] = "wired"

        ordered = [platforms[key] for key in SOCIAL_PLATFORM_META]
        return {
            "window_hours": window_hours,
            "ledger_path": str(ledger_path),
            "platforms": ordered,
            "summary": {
                "wired": sum(1 for p in ordered if p["wired"]),
                "attention": sum(1 for p in ordered if p["status"] == "attention"),
                "ok_24h": sum(p["ok_24h"] for p in ordered),
                "fail_24h": sum(p["fail_24h"] for p in ordered),
            },
        }

    @app.get("/api/posts")
    def list_posts(date: str | None = None, limit: int = 200):
        """Read Vawn's post_ledger.jsonl and return events for a given date.

        Args:
            date: ISO date YYYY-MM-DD. Defaults to today (local).
            limit: cap on number of events returned (most-recent first).

        Returns:
            {
              "date": "2026-05-15",
              "events": [ <ledger entry> ... ],
              "summary": {
                "total": int, "succeeded": int, "failed": int,
                "by_platform": {"x": {"ok": n, "fail": n}, ...},
                "by_cron": {"morning": {...}, "midday": {...}, ...},
                "post_urls": [str, ...]
              }
            }
        """
        from datetime import datetime, date as _date_cls
        import json as _json

        ledger_path = settings.vawn_dir / "post_ledger.jsonl"
        if not ledger_path.is_file():
            return {
                "date": date or _date_cls.today().isoformat(),
                "events": [],
                "summary": {"total": 0, "succeeded": 0, "failed": 0, "by_platform": {}, "by_cron": {}, "post_urls": []},
                "note": f"post_ledger.jsonl not found at {ledger_path}",
            }

        target = date or _date_cls.today().isoformat()
        limit = max(1, min(int(limit), 1000))

        # Stream the file -- read only lines from `target`
        events: list[dict] = []
        try:
            with ledger_path.open("r", encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    line = line.strip()
                    if not line or target not in line:
                        # Cheap pre-filter: skip lines that can't contain the date
                        continue
                    try:
                        rec = _json.loads(line)
                    except _json.JSONDecodeError:
                        continue
                    ts = rec.get("timestamp", "")
                    if isinstance(ts, str) and ts.startswith(target):
                        events.append(rec)
        except OSError as exc:
            return {"date": target, "events": [], "summary": {}, "error": str(exc)}

        events.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
        events = events[:limit]

        # Summary
        by_platform: dict[str, dict[str, int]] = {}
        by_cron: dict[str, dict[str, int]] = {}
        post_urls: list[dict] = []
        succeeded = 0
        failed = 0
        for e in events:
            platform = (e.get("platform") or "unknown").lower()
            cron = e.get("cron") or "ad-hoc"
            success = bool(e.get("success"))
            event_type = e.get("event") or ""
            # Only count posting attempts (skip preflight-failed since those didn't try)
            if event_type in {"post_attempt", "story_repost_attempt"}:
                by_platform.setdefault(platform, {"ok": 0, "fail": 0})
                by_cron.setdefault(cron, {"ok": 0, "fail": 0})
                if success:
                    succeeded += 1
                    by_platform[platform]["ok"] += 1
                    by_cron[cron]["ok"] += 1
                    if e.get("post_url"):
                        post_urls.append({
                            "platform": platform,
                            "url": e["post_url"],
                            "caption_preview": (e.get("caption") or "")[:140],
                            "timestamp": e.get("timestamp"),
                            "cron": cron,
                        })
                else:
                    failed += 1
                    by_platform[platform]["fail"] += 1
                    by_cron[cron]["fail"] += 1

        return {
            "date": target,
            "events": events,
            "summary": {
                "total": succeeded + failed,
                "succeeded": succeeded,
                "failed": failed,
                "by_platform": by_platform,
                "by_cron": by_cron,
                "post_urls": post_urls,
            },
        }

    # ---- label command center ----
    @app.get("/api/releases")
    def list_releases():
        rows = get_conn().execute(
            "SELECT * FROM releases ORDER BY "
            "CASE status WHEN 'scheduled' THEN 0 WHEN 'ready' THEN 1 WHEN 'production' THEN 2 "
            "WHEN 'planning' THEN 3 WHEN 'released' THEN 4 ELSE 5 END, "
            "COALESCE(release_date, '9999-12-31'), updated_at DESC"
        ).fetchall()
        return [_release_out(r) for r in rows]

    @app.post("/api/releases")
    def create_release(body: ReleaseIn):
        now = _now_iso()
        item_id = _new_id("rel")
        data = _model_all(body)
        conn = get_conn()
        conn.execute(
            """INSERT INTO releases
               (id, title, artist, type, status, release_date, distributor, artwork_status,
                master_status, metadata_status, distributor_status, publishing_status,
                budget, spend_to_date, notes, created_at, updated_at)
               VALUES (:id, :title, :artist, :type, :status, :release_date, :distributor, :artwork_status,
                :master_status, :metadata_status, :distributor_status, :publishing_status,
                :budget, :spend_to_date, :notes, :created_at, :updated_at)""",
            {
                **data,
                "id": item_id,
                "created_at": now,
                "updated_at": now,
            },
        )
        conn.commit()
        return _release_out(conn.execute("SELECT * FROM releases WHERE id=?", (item_id,)).fetchone())

    @app.patch("/api/releases/{release_id}")
    def patch_release(release_id: str, body: ReleasePatch):
        row = _patch_row(
            "releases",
            release_id,
            _model_data(body),
            {
                "title", "artist", "type", "status", "release_date", "distributor", "artwork_status",
                "master_status", "metadata_status", "distributor_status", "publishing_status",
                "budget", "spend_to_date", "notes",
            },
        )
        return _release_out(row)

    @app.get("/api/campaigns")
    def list_campaigns():
        rows = get_conn().execute(
            "SELECT * FROM campaigns ORDER BY "
            "CASE status WHEN 'active' THEN 0 WHEN 'draft' THEN 1 WHEN 'paused' THEN 2 ELSE 3 END, "
            "COALESCE(start_date, '9999-12-31'), updated_at DESC"
        ).fetchall()
        return [_campaign_out(r) for r in rows]

    @app.post("/api/campaigns")
    def create_campaign(body: CampaignIn):
        now = _now_iso()
        item_id = _new_id("camp")
        data = _model_all(body)
        data["platforms"] = json.dumps(data.get("platforms") or [])
        conn = get_conn()
        conn.execute(
            """INSERT INTO campaigns
               (id, name, artist, release_id, objective, status, start_date, end_date,
                platforms, budget, spend_to_date, primary_metric, target_value, notes,
                created_at, updated_at)
               VALUES (:id, :name, :artist, :release_id, :objective, :status, :start_date,
                :end_date, :platforms, :budget, :spend_to_date, :primary_metric,
                :target_value, :notes, :created_at, :updated_at)""",
            {
                **data,
                "id": item_id,
                "created_at": now,
                "updated_at": now,
            },
        )
        conn.commit()
        return _campaign_out(conn.execute("SELECT * FROM campaigns WHERE id=?", (item_id,)).fetchone())

    @app.patch("/api/campaigns/{campaign_id}")
    def patch_campaign(campaign_id: str, body: CampaignPatch):
        data = _model_data(body)
        if "platforms" in data:
            data["platforms"] = json.dumps(data.get("platforms") or [])
        row = _patch_row(
            "campaigns",
            campaign_id,
            data,
            {
                "name", "artist", "release_id", "objective", "status", "start_date",
                "end_date", "platforms", "budget", "spend_to_date", "primary_metric",
                "target_value", "notes",
            },
        )
        return _campaign_out(row)

    @app.get("/api/approvals")
    def list_approvals(status: str | None = None):
        sql = "SELECT * FROM approvals"
        args: list[str] = []
        if status:
            sql += " WHERE status=?"
            args.append(status)
        sql += (
            " ORDER BY CASE priority WHEN 'urgent' THEN 0 WHEN 'high' THEN 1 "
            "WHEN 'medium' THEN 2 ELSE 3 END, COALESCE(due_at, '9999-12-31'), created_at DESC"
        )
        return [_approval_out(r) for r in get_conn().execute(sql, args).fetchall()]

    @app.post("/api/approvals")
    def create_approval(body: ApprovalIn):
        now = _now_iso()
        item_id = _new_id("appr")
        data = _model_all(body)
        conn = get_conn()
        conn.execute(
            """INSERT INTO approvals
               (id, title, category, priority, status, requested_by, assigned_to,
                due_at, linked_type, linked_id, decision_note, created_at, updated_at)
               VALUES (:id, :title, :category, :priority, :status, :requested_by,
                :assigned_to, :due_at, :linked_type, :linked_id, :decision_note,
                :created_at, :updated_at)""",
            {
                **data,
                "id": item_id,
                "created_at": now,
                "updated_at": now,
            },
        )
        conn.commit()
        return _approval_out(conn.execute("SELECT * FROM approvals WHERE id=?", (item_id,)).fetchone())

    @app.patch("/api/approvals/{approval_id}")
    def patch_approval(approval_id: str, body: ApprovalPatch):
        row = _patch_row(
            "approvals",
            approval_id,
            _model_data(body),
            {
                "title", "category", "priority", "status", "requested_by", "assigned_to",
                "due_at", "linked_type", "linked_id", "decision_note",
            },
        )
        return _approval_out(row)

    @app.get("/api/finance/entries")
    def list_finance_entries(limit: int = 100):
        lim = max(1, min(int(limit), 500))
        rows = get_conn().execute(
            "SELECT * FROM finance_entries ORDER BY entry_date DESC, created_at DESC LIMIT ?",
            (lim,),
        ).fetchall()
        return [_finance_out(r) for r in rows]

    @app.post("/api/finance/entries")
    def create_finance_entry(body: FinanceEntryIn):
        now = _now_iso()
        item_id = _new_id("fin")
        data = _model_all(body)
        data["entry_date"] = data.get("entry_date") or date_cls.today().isoformat()
        conn = get_conn()
        conn.execute(
            """INSERT INTO finance_entries
               (id, entry_type, source, vendor, category, amount, entry_date,
                linked_type, linked_id, notes, created_at, updated_at)
               VALUES (:id, :entry_type, :source, :vendor, :category, :amount,
                :entry_date, :linked_type, :linked_id, :notes, :created_at, :updated_at)""",
            {
                **data,
                "id": item_id,
                "created_at": now,
                "updated_at": now,
            },
        )
        conn.commit()
        return _finance_out(conn.execute("SELECT * FROM finance_entries WHERE id=?", (item_id,)).fetchone())

    @app.get("/api/finance/summary")
    def finance_summary():
        conn = get_conn()
        month = date_cls.today().isoformat()[:7]
        rows = conn.execute(
            "SELECT entry_type, category, SUM(amount) AS total FROM finance_entries "
            "WHERE substr(entry_date, 1, 7)=? GROUP BY entry_type, category",
            (month,),
        ).fetchall()
        spend = sum(float(r["total"] or 0) for r in rows if r["entry_type"] == "expense")
        revenue = sum(float(r["total"] or 0) for r in rows if r["entry_type"] == "revenue")
        cost_centers = [
            {"category": r["category"], "amount": float(r["total"] or 0)}
            for r in rows
            if r["entry_type"] == "expense"
        ]
        cost_centers.sort(key=lambda x: x["amount"], reverse=True)
        unassigned = conn.execute(
            "SELECT COUNT(*) AS c, COALESCE(SUM(amount), 0) AS total FROM finance_entries "
            "WHERE entry_type='expense' AND (linked_id IS NULL OR linked_id='')"
        ).fetchone()
        return {
            "month": month,
            "monthly_spend": spend,
            "monthly_revenue": revenue,
            "net": revenue - spend,
            "estimated_runway_months": None,
            "top_cost_centers": cost_centers[:5],
            "unassigned_expenses": {
                "count": unassigned["c"],
                "amount": float(unassigned["total"] or 0),
            },
        }

    @app.get("/api/command/summary")
    def command_summary():
        conn = get_conn()
        releases = [_release_out(r) for r in conn.execute("SELECT * FROM releases").fetchall()]
        campaigns = [_campaign_out(r) for r in conn.execute("SELECT * FROM campaigns").fetchall()]
        approvals = [_approval_out(r) for r in conn.execute(
            "SELECT * FROM approvals WHERE status='open' ORDER BY "
            "CASE priority WHEN 'urgent' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, "
            "COALESCE(due_at, '9999-12-31'), created_at DESC LIMIT 12"
        ).fetchall()]
        active_releases = [r for r in releases if r["status"] not in {"released", "archived"}]
        active_campaigns = [c for c in campaigns if c["status"] == "active"]
        posts = list_posts()
        social = social_platform_status()
        finance = finance_summary()
        dlq_active = conn.execute(
            "SELECT COUNT(*) AS c FROM dlq WHERE replayed_at IS NULL AND discarded_at IS NULL"
        ).fetchone()["c"]
        recent_failures = conn.execute(
            "SELECT COUNT(*) AS c FROM dispatches "
            "WHERE outcome IN ('failure','fail') AND date(started_at) >= date('now','-7 days')"
        ).fetchone()["c"]
        active_routines = conn.execute(
            "SELECT COUNT(*) AS c FROM routines WHERE enabled=1"
        ).fetchone()["c"]
        operational_alerts = (
            len([a for a in approvals if a["priority"] in {"urgent", "high"}])
            + int(social["summary"].get("attention") or 0)
            + int(posts["summary"].get("failed") or 0)
            + int(dlq_active)
            + int(recent_failures)
        )
        return {
            "kpis": {
                "postsToday": posts["summary"].get("succeeded", 0),
                "activeReleases": len(active_releases),
                "needsApproval": len(approvals),
                "operationalAlerts": operational_alerts,
                "activeRoutines": active_routines,
            },
            "releases": active_releases[:6],
            "campaigns": active_campaigns[:6],
            "approvals": approvals,
            "finance": finance,
            "posts": posts["summary"],
            "social": social["summary"],
            "alerts": {
                "dlq": dlq_active,
                "dispatchFailures7d": recent_failures,
                "socialAttention": social["summary"].get("attention", 0),
                "postFailuresToday": posts["summary"].get("failed", 0),
            },
        }

    # ---- recent message conversations ----
    @app.get("/api/messages/conversations")
    def list_conversations(limit: int = 20):
        rows = get_conn().execute(
            "SELECT t.id, t.agent_id, t.title, t.updated_at, a.display_name AS agent_name, "
            "a.department AS agent_department, "
            "(SELECT content FROM chat_messages m WHERE m.thread_id=t.id "
            "  ORDER BY m.created_at DESC LIMIT 1) AS last_message "
            "FROM chat_threads t "
            "LEFT JOIN agents a ON a.id = t.agent_id "
            "ORDER BY t.updated_at DESC LIMIT ?",
            (max(1, min(int(limit), 100)),),
        ).fetchall()
        return [dict(r) for r in rows]

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

        # Fire and forget -- caller subscribes to WS for tokens
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

    @app.post("/api/scheduler/shadow")
    async def scheduler_shadow(body: dict = Body(default_factory=dict)) -> dict[str, Any]:
        """Toggle scheduler shadow mode at runtime. body: {"shadow": true/false}"""
        sched = getattr(app.state, "scheduler", None)
        if sched is None:
            raise HTTPException(status_code=503, detail="scheduler not running")
        current = sched.shadow
        desired = body.get("shadow")
        if desired is None:
            return {"ok": True, "shadow": current, "changed": False}
        if not isinstance(desired, bool):
            raise HTTPException(status_code=422, detail="shadow must be a boolean")
        sched.shadow = desired
        return {"ok": True, "shadow": sched.shadow, "previous": current, "changed": current != sched.shadow}

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
        try:
            dispatch_id = await sched.fire_now(routine_id)
        except RuntimeError as e:
            raise HTTPException(status_code=410, detail=str(e))
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

    # ---- Prompt Generator bridge ----
    @app.get("/api/prompt-generator/status")
    def prompt_generator_status():
        return {
            "ok": True,
            "backend_url": PROMPT_GENERATOR_BACKEND_URL,
            "ui": "/ui/prompt-generator/",
        }

    @app.api_route(
        "/api/prompt-generator/{path:path}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    )
    async def prompt_generator_proxy(path: str, request: Request):
        target = f"{PROMPT_GENERATOR_BACKEND_URL}/api/{path}"
        body = await request.body()
        headers = {
            key: value
            for key, value in request.headers.items()
            if key.lower() not in HOP_BY_HOP_HEADERS and key.lower() != "host"
        }
        headers["origin"] = PROMPT_GENERATOR_BACKEND_URL

        timeout = httpx.Timeout(connect=15.0, read=None, write=120.0, pool=15.0)
        client = httpx.AsyncClient(timeout=timeout, follow_redirects=False)
        upstream = await client.send(
            client.build_request(
                request.method,
                target,
                params=request.query_params,
                content=body,
                headers=headers,
            ),
            stream=True,
        )

        response_headers = {
            key: value
            for key, value in upstream.headers.items()
            if key.lower() not in HOP_BY_HOP_HEADERS
        }

        async def body_iter():
            try:
                async for chunk in upstream.aiter_bytes():
                    yield chunk
            finally:
                await upstream.aclose()
                await client.aclose()

        return StreamingResponse(
            body_iter(),
            status_code=upstream.status_code,
            headers=response_headers,
            media_type=upstream.headers.get("content-type"),
        )

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
            return RedirectResponse(url="/ui/", status_code=307)

    return app


app = create_app()
