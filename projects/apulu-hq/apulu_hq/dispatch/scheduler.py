"""APScheduler-driven routine dispatcher.

Cron-fires every enabled routine. Each fire runs through `run_with_retries`
and writes dispatch + DLQ rows. **Defaults to live mode** — every enabled
routine executes its real command on its cron schedule.

Shadow mode (dry-run) is opt-in via ``HQ_DISPATCHER_SHADOW=1`` or the
``/api/scheduler/shadow`` runtime toggle. In shadow, fires log + write
audit rows but the subprocess is never spawned; useful for staging.

History: shadow used to be the default during the Paperclip→Apulu HQ
soak. Once cutover completed we flipped the default to live.
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
    """Live by default. Opt back in to shadow with HQ_DISPATCHER_SHADOW=1."""
    return os.environ.get("HQ_DISPATCHER_SHADOW", "0") == "1"


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
        # Drift-detection fingerprint of the routines table — used by the
        # auto-reload watcher to pick up direct SQL UPDATEs (i.e. bulk-enable
        # outside the API). Format: (enabled_count, max_updated_at).
        self._routines_fingerprint: tuple = (0, "")

    async def start(self) -> None:
        async with self._lock:
            if self._scheduler is not None:
                return
            self._scheduler = AsyncIOScheduler(timezone="America/New_York")
            self._scheduler.start()
            await self.reload_jobs()
            # Watcher: every 5 min, reload if the routines table changed under us.
            # Catches direct SQL writes (e.g. bulk-enable via sqlite3 CLI).
            self._scheduler.add_job(
                self._auto_reload_if_drifted,
                trigger="interval",
                minutes=5,
                id="__auto_reload_watcher__",
                name="auto-reload routines on drift",
                replace_existing=True,
                misfire_grace_time=60,
                coalesce=True,
                max_instances=1,
            )
            log.info(
                "HQScheduler started (shadow=%s, %d job(s) loaded, auto-reload watcher every 5 min)",
                self.shadow,
                len(self._scheduler.get_jobs()) - 1,
            )

    def _compute_routines_fingerprint(self) -> tuple:
        """Cheap signal of routines-table state: (enabled_count, max(updated_at))."""
        row = get_conn().execute(
            "SELECT COUNT(*) AS c, COALESCE(MAX(updated_at),'') AS m "
            "FROM routines WHERE enabled=1"
        ).fetchone()
        return (int(row["c"]), str(row["m"]))

    async def _auto_reload_if_drifted(self) -> None:
        """Watcher: reload jobs if the routines fingerprint changed."""
        if self._scheduler is None:
            return
        current = self._compute_routines_fingerprint()
        if current != self._routines_fingerprint:
            log.info(
                "auto-reload: routines fingerprint drifted %s → %s — reloading jobs",
                self._routines_fingerprint, current,
            )
            await self.reload_jobs()

    async def stop(self) -> None:
        async with self._lock:
            if self._scheduler is None:
                return
            self._scheduler.shutdown(wait=False)
            self._scheduler = None

    async def reload_jobs(self) -> None:
        """Drop all routine jobs and rebuild from the routines table.

        Preserves the auto-reload watcher job.
        """
        if self._scheduler is None:
            return
        for job in self._scheduler.get_jobs():
            if job.id == "__auto_reload_watcher__":
                continue
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
        # Refresh the drift fingerprint so the watcher only fires on real changes.
        try:
            self._routines_fingerprint = self._compute_routines_fingerprint()
        except Exception:
            pass
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
            if j.id != "__auto_reload_watcher__"
        ]
