"""APScheduler-driven routine dispatcher.

Cron-fires every enabled routine. Each fire runs through `run_with_retries`
and writes dispatch + DLQ rows. **Defaults to shadow mode** — until you
flip `shadow=False`, no real commands are executed; the scheduler only
publishes events and writes audit rows. This lets Phase 3 soak the
scheduler alongside Paperclip without dual-fire risk.

Flipping a routine to "real fire":
  1) Set HQ_DISPATCHER_SHADOW=0 in the environment (global)
  2) OR set per-routine: `routines.shadow_only = 0` via PATCH endpoint (v2)

For v1 the env var is the on/off switch. The 3-day soak in shadow mode
should be the gate to flipping the env var.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shlex
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from ..db import get_conn
from ..events.bus import EventBus
from .persist import write_dispatch, write_dlq
from .runner import run_with_retries

log = logging.getLogger(__name__)


def _shadow_default() -> bool:
    """Shadow mode unless HQ_DISPATCHER_SHADOW is explicitly set to '0'."""
    return os.environ.get("HQ_DISPATCHER_SHADOW", "1") != "0"


def _parse_cron(cron_expr: str, tz: str) -> CronTrigger:
    """Build an APScheduler CronTrigger from a standard 5-field cron string."""
    parts = cron_expr.strip().split()
    if len(parts) != 5:
        raise ValueError(f"cron_expr must have 5 fields, got {cron_expr!r}")
    minute, hour, day, month, dow = parts
    return CronTrigger(
        minute=minute,
        hour=hour,
        day=day,
        month=month,
        day_of_week=dow,
        timezone=tz,
    )


def _build_command(routine: dict[str, Any]) -> list[str]:
    """Resolve a routine row into an argv list.

    `routines.command` is a shell-style string; `routines.args` is JSON list.
    Empty command → fall back to a no-op echo (lets us shadow-soak even
    routines that haven't been wired up to a real subprocess yet).
    """
    command = (routine.get("command") or "").strip()
    args_json = routine.get("args") or "[]"
    try:
        extra: list[str] = json.loads(args_json) if args_json else []
        if not isinstance(extra, list):
            extra = []
    except json.JSONDecodeError:
        log.warning("routine %s args is not valid JSON: %r", routine.get("id"), args_json)
        extra = []

    if not command:
        # Shadow placeholder — never actually executed in shadow mode.
        name = routine.get("display_name") or "unnamed"
        return ["python", "-c", f"print('shadow routine {name}')"]

    base = shlex.split(command, posix=False)
    return base + [str(x) for x in extra]


class HQScheduler:
    """Owns the APScheduler instance and the FastAPI app's reference to it."""

    def __init__(
        self,
        bus: EventBus,
        *,
        cwd: str = ".",
        shadow: bool | None = None,
    ) -> None:
        self.bus = bus
        self.cwd = cwd
        self.shadow = _shadow_default() if shadow is None else shadow
        self._scheduler: AsyncIOScheduler | None = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        async with self._lock:
            if self._scheduler is not None:
                return
            self._scheduler = AsyncIOScheduler(timezone="America/New_York")
            self._scheduler.start()
            await self.reload_jobs()
            log.info(
                "HQScheduler started (shadow=%s, %d job(s) loaded)",
                self.shadow,
                len(self._scheduler.get_jobs()),
            )

    async def stop(self) -> None:
        async with self._lock:
            if self._scheduler is None:
                return
            self._scheduler.shutdown(wait=False)
            self._scheduler = None

    async def reload_jobs(self) -> None:
        """Drop all jobs and rebuild from the routines table (enabled only)."""
        if self._scheduler is None:
            return
        for job in self._scheduler.get_jobs():
            self._scheduler.remove_job(job.id)

        rows = get_conn().execute(
            "SELECT id, legacy_id, display_name, agent_id, cron_expr, timezone, "
            "command, args, priority, enabled, disabled_reason "
            "FROM routines WHERE enabled=1"
        ).fetchall()

        added = 0
        for r in rows:
            row = dict(r)
            try:
                trigger = _parse_cron(row["cron_expr"], row["timezone"] or "America/New_York")
            except Exception as e:
                log.warning("Skipping routine %s — bad cron %r: %s",
                            row["display_name"], row["cron_expr"], e)
                continue
            self._scheduler.add_job(
                self._fire,
                trigger=trigger,
                id=row["id"],
                name=row["display_name"],
                kwargs={"routine_id": row["id"]},
                replace_existing=True,
                misfire_grace_time=120,
                coalesce=True,
                max_instances=1,
            )
            added += 1
        log.info("reload_jobs: %d enabled routine(s) scheduled (shadow=%s)", added, self.shadow)

    async def fire_now(self, routine_id: str) -> str:
        """Manually fire a routine immediately. Returns the dispatch_id."""
        result = await self._fire(routine_id=routine_id)
        if result is None:
            raise RuntimeError(f"routine {routine_id} vanished during fire")
        return result.dispatch_id

    async def _fire(self, routine_id: str):
        row = get_conn().execute(
            "SELECT id, display_name, agent_id, cron_expr, timezone, command, args "
            "FROM routines WHERE id=?",
            (routine_id,),
        ).fetchone()
        if row is None:
            log.warning("scheduled routine vanished: %s", routine_id)
            return None
        rd = dict(row)
        cmd = _build_command(rd)
        log.info(
            "firing routine %s (shadow=%s) cmd=%s",
            rd["display_name"], self.shadow, " ".join(cmd[:6]),
        )
        result = await run_with_retries(
            routine_id=rd["id"],
            routine_name=rd["display_name"],
            agent_id=rd["agent_id"],
            cmd=cmd,
            cwd=self.cwd,
            shadow=self.shadow,
            bus=self.bus,
        )
        write_dispatch(result)
        if not result.success:
            write_dlq(result)
        return result

    @property
    def started(self) -> bool:
        return self._scheduler is not None and self._scheduler.running

    def list_jobs(self) -> list[dict[str, Any]]:
        if self._scheduler is None:
            return []
        return [
            {
                "id": j.id,
                "name": j.name,
                "next_run_time": j.next_run_time.isoformat() if j.next_run_time else None,
                "trigger": str(j.trigger),
            }
            for j in self._scheduler.get_jobs()
        ]
