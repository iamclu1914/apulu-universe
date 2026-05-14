"""Live observers — tail the Paperclip-era state files and project them into
SQLite rows + WebSocket events.

This is the bridge that lets HQ "watch" Paperclip without yet replacing it.
Each tailer:

1. Reads its last byte offset from the `meta` table.
2. Polls its file for new content (default 2s interval).
3. Parses each new JSONL line / JSON snapshot and:
   - inserts/updates a row in the appropriate table
   - publishes an Event on the bus (which fans out to WS subscribers)
4. Persists the new offset transactionally with the row write.

Restart-safe: offsets are namespaced by absolute file path so multiple
universes (Vawn now, future artists) don't collide.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Awaitable, Callable, Iterable

from .config import settings
from .db import get_conn, tx
from .events import Event, get_bus
from .models import new_id, now_iso

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Offset persistence (meta table)
# ---------------------------------------------------------------------------

OFFSET_KEY_PREFIX = "tailer.offset."
HEALTH_KEY_PREFIX = "tailer.health."


def _meta_key_for(path: Path, prefix: str = OFFSET_KEY_PREFIX) -> str:
    return f"{prefix}{path.resolve().as_posix()}"


def get_offset(path: Path) -> int:
    row = get_conn().execute(
        "SELECT value FROM meta WHERE key=?",
        (_meta_key_for(path),),
    ).fetchone()
    return int(row["value"]) if row else 0


def set_offset(conn: sqlite3.Connection, path: Path, offset: int) -> None:
    conn.execute(
        "INSERT INTO meta(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (_meta_key_for(path), str(offset)),
    )


def get_meta(key: str) -> str | None:
    row = get_conn().execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return row["value"] if row else None


def set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO meta(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )


# ---------------------------------------------------------------------------
# Helpers: look up routine + agent by slot name
# ---------------------------------------------------------------------------


@dataclass
class _SlotResolution:
    routine_id: str | None
    agent_id: str | None
    routine_name: str


def _resolve_slot(conn: sqlite3.Connection, slot: str) -> _SlotResolution:
    """Look up routine + assignee by slot name. Returns None ids if unknown
    so we still record the dispatch but flag it as orphan."""
    row = conn.execute(
        "SELECT id, agent_id FROM routines WHERE display_name=?",
        (slot,),
    ).fetchone()
    if not row:
        return _SlotResolution(None, None, slot)
    return _SlotResolution(row["id"], row["agent_id"], slot)


# ---------------------------------------------------------------------------
# Dispatch log tailer
# ---------------------------------------------------------------------------


def _parse_iso(s: str) -> str:
    """Normalise an ISO timestamp to our stored format. Pass-through if good."""
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc).isoformat(timespec="seconds")
    except (TypeError, ValueError):
        return s or now_iso()


def _normalize_signature(sig) -> str | None:
    """Older log entries store signature as a string; newer ones store a dict
    with {name, severity, hint, retryable}. We keep only the canonical name
    in the DB column so it stays queryable."""
    if sig is None:
        return None
    if isinstance(sig, dict):
        return sig.get("name") or sig.get("signature") or None
    return str(sig)


def _interpret_dispatch_row(row: dict) -> tuple[str, list[Event]]:
    """Decide outcome + events emitted for one dispatch_log line.

    Returns (outcome, [events]). Outcome is what we store in dispatches.outcome.
    """
    slot = row.get("slot") or "<unknown>"
    attempt = int(row.get("attempt") or 1)
    final = bool(row.get("final"))
    success = bool(row.get("success"))
    exit_code = row.get("exit_code")
    signature = _normalize_signature(row.get("signature"))
    duration_s = row.get("duration_sec")

    events: list[Event] = []

    if final and success:
        outcome = "success"
        if attempt == 1:
            # First-try success — emit a routine.started before the success
            # so the UI animation has a "walking to desk" beat.
            events.append(Event(
                type="routine.started",
                payload={"slot": slot, "attempt": attempt},
            ))
        events.append(Event(
            type="routine.succeeded",
            payload={
                "slot": slot,
                "attempt": attempt,
                "duration_ms": int((duration_s or 0) * 1000),
            },
        ))
    elif final and not success:
        outcome = "failure"
        events.append(Event(
            type="routine.failed",
            payload={
                "slot": slot,
                "attempt": attempt,
                "exit_code": exit_code,
                "signature": signature,
                "duration_ms": int((duration_s or 0) * 1000),
            },
        ))
    else:
        outcome = "retry"
        events.append(Event(
            type="dispatch.retry_scheduled",
            payload={
                "slot": slot,
                "attempt": attempt,
                "exit_code": exit_code,
                "signature": signature,
            },
        ))

    return outcome, events


def _persist_dispatch(
    conn: sqlite3.Connection,
    row: dict,
    outcome: str,
) -> tuple[str | None, str | None, str]:
    """Insert a dispatches row. Returns (routine_id, agent_id, dispatch_id)."""
    slot = row.get("slot") or "<unknown>"
    resolved = _resolve_slot(conn, slot)
    dispatch_id = new_id()
    started = _parse_iso(row.get("timestamp", ""))
    duration_s = row.get("duration_sec")
    duration_ms = int(duration_s * 1000) if duration_s is not None else None

    # We don't know routine_id/agent_id if the slot isn't in our seed list.
    # Insert a placeholder routine/agent in those cases so FK holds — but only
    # if absolutely necessary. For now, skip the insert if unresolved and just
    # emit the event without persistence.
    if not resolved.routine_id or not resolved.agent_id:
        return None, None, dispatch_id

    conn.execute(
        """INSERT INTO dispatches
           (id, routine_id, agent_id, started_at, ended_at, attempt, outcome,
            exit_code, signature, stderr_tail, duration_ms)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            dispatch_id,
            resolved.routine_id,
            resolved.agent_id,
            started,
            started,  # we don't have a separate end timestamp from the log
            int(row.get("attempt") or 1),
            outcome,
            row.get("exit_code"),
            _normalize_signature(row.get("signature")),
            None,
            duration_ms,
        ),
    )
    return resolved.routine_id, resolved.agent_id, dispatch_id


async def tail_dispatch_log(path: Path, *, poll_interval: float = 2.0) -> None:
    """Forever-loop watcher for dispatch_log.jsonl."""
    bus = get_bus()
    while True:
        try:
            if not path.is_file():
                await asyncio.sleep(poll_interval)
                continue
            size = path.stat().st_size
            offset = get_offset(path)
            if offset > size:
                # File was rotated / truncated. Restart from 0.
                log.warning("Dispatch log shrank (%s < %s) — restarting from 0",
                            size, offset)
                offset = 0
            if size <= offset:
                await asyncio.sleep(poll_interval)
                continue

            with path.open("rb") as f:
                f.seek(offset)
                chunk = f.read(size - offset)
                new_offset = f.tell()

            text = chunk.decode("utf-8", errors="replace")
            lines = text.splitlines()
            # If last line is partial (no trailing newline), back off to its
            # start so we re-read it next tick.
            consumed_bytes = len(chunk)
            if chunk and not chunk.endswith(b"\n"):
                last_line = lines[-1]
                consumed_bytes -= len(last_line.encode("utf-8"))
                lines = lines[:-1]
            commit_offset = offset + consumed_bytes

            events_to_publish: list[Event] = []
            with tx() as conn:
                for ln in lines:
                    if not ln.strip():
                        continue
                    try:
                        row = json.loads(ln)
                    except json.JSONDecodeError:
                        log.warning("skipping malformed dispatch line: %r", ln[:80])
                        continue
                    outcome, events = _interpret_dispatch_row(row)
                    routine_id, agent_id, dispatch_id = _persist_dispatch(conn, row, outcome)
                    for ev in events:
                        ev.payload.setdefault("routine_id", routine_id)
                        ev.payload.setdefault("agent_id", agent_id)
                        ev.payload.setdefault("dispatch_id", dispatch_id)
                        events_to_publish.append(ev)
                set_offset(conn, path, commit_offset)

            for ev in events_to_publish:
                await bus.publish(ev)

        except Exception:
            log.exception("dispatch tailer iteration failed")
        await asyncio.sleep(poll_interval)


# ---------------------------------------------------------------------------
# Dead letter tailer
# ---------------------------------------------------------------------------


async def tail_dead_letter(path: Path, *, poll_interval: float = 2.0) -> None:
    bus = get_bus()
    while True:
        try:
            if not path.is_file():
                await asyncio.sleep(poll_interval)
                continue
            size = path.stat().st_size
            offset = get_offset(path)
            if offset > size:
                offset = 0
            if size <= offset:
                await asyncio.sleep(poll_interval)
                continue

            with path.open("rb") as f:
                f.seek(offset)
                chunk = f.read(size - offset)

            text = chunk.decode("utf-8", errors="replace")
            lines = text.splitlines()
            consumed = len(chunk)
            if chunk and not chunk.endswith(b"\n"):
                last_line = lines[-1]
                consumed -= len(last_line.encode("utf-8"))
                lines = lines[:-1]
            commit_offset = offset + consumed

            events: list[Event] = []
            with tx() as conn:
                for ln in lines:
                    if not ln.strip():
                        continue
                    try:
                        row = json.loads(ln)
                    except json.JSONDecodeError:
                        continue
                    slot = row.get("slot") or "<unknown>"
                    resolved = _resolve_slot(conn, slot)
                    entry_id = new_id()
                    appended_at = _parse_iso(row.get("timestamp", ""))
                    sig = _normalize_signature(row.get("signature"))
                    if resolved.routine_id and resolved.agent_id:
                        conn.execute(
                            """INSERT INTO dlq
                               (id, dispatch_id, routine_id, agent_id, signature,
                                payload, appended_at)
                               VALUES (?, ?, ?, ?, ?, ?, ?)""",
                            (
                                entry_id,
                                None,
                                resolved.routine_id,
                                resolved.agent_id,
                                sig,
                                json.dumps(row),
                                appended_at,
                            ),
                        )
                    events.append(Event(
                        type="dlq.appended",
                        payload={
                            "entry_id": entry_id,
                            "slot": slot,
                            "routine_id": resolved.routine_id,
                            "agent_id": resolved.agent_id,
                            "signature": sig,
                            "appended_at": appended_at,
                        },
                    ))
                set_offset(conn, path, commit_offset)

            for ev in events:
                await bus.publish(ev)

        except Exception:
            log.exception("dlq tailer iteration failed")
        await asyncio.sleep(poll_interval)


# ---------------------------------------------------------------------------
# Backend health tailer (single-document, polls on mtime change)
# ---------------------------------------------------------------------------


HEALTH_STATE_KEY = f"{HEALTH_KEY_PREFIX}backend_health.overall"
HEALTH_MTIME_KEY = f"{HEALTH_KEY_PREFIX}backend_health.mtime"


async def tail_backend_health(path: Path, *, poll_interval: float = 5.0) -> None:
    bus = get_bus()
    while True:
        try:
            if not path.is_file():
                await asyncio.sleep(poll_interval)
                continue
            stat = path.stat()
            mtime = str(int(stat.st_mtime_ns))
            last_mtime = get_meta(HEALTH_MTIME_KEY)
            if last_mtime == mtime:
                await asyncio.sleep(poll_interval)
                continue
            text = path.read_text(encoding="utf-8")
            try:
                doc = json.loads(text)
            except json.JSONDecodeError:
                await asyncio.sleep(poll_interval)
                continue
            overall = doc.get("overall") or "unknown"
            last_overall = get_meta(HEALTH_STATE_KEY)
            events: list[Event] = [Event(
                type="health.snapshot",
                payload={"overall": overall, "components": doc},
            )]
            if last_overall != overall:
                if overall != "healthy":
                    events.append(Event(
                        type="breaker.tripped",
                        payload={
                            "component": "apulu_studio_backend",
                            "reason": overall,
                        },
                    ))
                elif last_overall and last_overall != "healthy":
                    events.append(Event(
                        type="breaker.cleared",
                        payload={"component": "apulu_studio_backend"},
                    ))
            with tx() as conn:
                set_meta(conn, HEALTH_STATE_KEY, overall)
                set_meta(conn, HEALTH_MTIME_KEY, mtime)
            for ev in events:
                await bus.publish(ev)
        except Exception:
            log.exception("health tailer iteration failed")
        await asyncio.sleep(poll_interval)


# ---------------------------------------------------------------------------
# Tailer manager (called from FastAPI lifespan)
# ---------------------------------------------------------------------------


@dataclass
class TailerConfig:
    dispatch_log: Path | None
    dead_letter: Path | None
    backend_health: Path | None

    @classmethod
    def from_env(cls) -> "TailerConfig":
        def _resolve(env_key: str, fallback: str) -> Path | None:
            val = os.environ.get(env_key, fallback)
            if not val:
                return None
            p = Path(val)
            return p if p.parent.exists() else None

        return cls(
            dispatch_log=_resolve("APULU_HQ_DISPATCH_LOG", r"C:\Users\rdyal\Vawn\dispatch_log.jsonl"),
            dead_letter=_resolve("APULU_HQ_DEAD_LETTER", r"C:\Users\rdyal\Vawn\dead_letter.jsonl"),
            backend_health=_resolve("APULU_HQ_BACKEND_HEALTH", r"C:\Users\rdyal\Vawn\backend_health.json"),
        )


async def start_tailers(cfg: TailerConfig | None = None) -> list[asyncio.Task]:
    cfg = cfg or TailerConfig.from_env()
    tasks: list[asyncio.Task] = []
    if cfg.dispatch_log:
        log.info("tailing dispatch log: %s", cfg.dispatch_log)
        tasks.append(asyncio.create_task(tail_dispatch_log(cfg.dispatch_log)))
    if cfg.dead_letter:
        log.info("tailing dead letter: %s", cfg.dead_letter)
        tasks.append(asyncio.create_task(tail_dead_letter(cfg.dead_letter)))
    if cfg.backend_health:
        log.info("tailing backend health: %s", cfg.backend_health)
        tasks.append(asyncio.create_task(tail_backend_health(cfg.backend_health)))
    return tasks


async def stop_tailers(tasks: Iterable[asyncio.Task]) -> None:
    for t in tasks:
        t.cancel()
    await asyncio.gather(*[asyncio.shield(t) for t in tasks], return_exceptions=True)
