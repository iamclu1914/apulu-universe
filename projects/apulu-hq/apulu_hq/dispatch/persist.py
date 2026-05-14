"""Write dispatch + DLQ rows into the HQ SQLite database.

Kept separate from `runner.py` so the runner is testable without a DB —
unit tests use it directly, integration tests pair it with `persist.py`.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from ..db import tx
from .runner import DispatchResult

log = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def write_dispatch(result: DispatchResult) -> None:
    """Insert a row into the `dispatches` table. Idempotent on PK."""
    row = result.to_dispatch_row()
    try:
        with tx() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO dispatches
                (id, routine_id, agent_id, started_at, ended_at, attempt,
                 outcome, exit_code, signature, stderr_tail, duration_ms)
                VALUES
                (:id, :routine_id, :agent_id, :started_at, :ended_at, :attempt,
                 :outcome, :exit_code, :signature, :stderr_tail, :duration_ms)
                """,
                row,
            )
    except Exception:
        log.exception("failed to write dispatch row id=%s", row.get("id"))


def write_dlq(result: DispatchResult) -> None:
    """Insert a DLQ row for a failed dispatch. Skips successes."""
    if result.success:
        return
    try:
        with tx() as conn:
            conn.execute(
                """
                INSERT INTO dlq
                (id, dispatch_id, routine_id, agent_id, signature, payload, appended_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    result.dispatch_id,
                    result.routine_id,
                    result.agent_id,
                    result.signature["name"] if result.signature else None,
                    json.dumps({
                        "attempts": result.attempts,
                        "final_exit_code": result.final_exit_code,
                        "signature": result.signature,
                        "output_tail": result.output_tail[-2000:],
                        "shadow": result.shadow,
                        "attempt_log": result.attempt_log,
                    }),
                    _now_iso(),
                ),
            )
    except Exception:
        log.exception("failed to write DLQ row dispatch_id=%s", result.dispatch_id)
