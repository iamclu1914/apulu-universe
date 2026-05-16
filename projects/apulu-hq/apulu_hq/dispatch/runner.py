"""Apulu HQ dispatch runner — ported from Vawn/dispatch_runner.py.

Same retry / signature-detection / DLQ semantics as Paperclip, but adapted
to the HQ runtime:

  - Returns a structured DispatchResult (not just an exit code)
  - Async-native: subprocess managed via asyncio so we don't block the loop
  - Publishes events to the bus at every state transition so the UI animates
  - Writes dispatch + DLQ rows to SQLite via the same connection pool the
    tailers use
  - **Shadow-fire mode**: when `shadow=True`, the subprocess command is NOT
    executed. Instead we synthesize a successful outcome, log it as
    "shadow" so it never gets confused with a real run, and emit the full
    event sequence. This lets Phase 3 soak the scheduler against the real
    routines list without touching production while Paperclip keeps driving.

Exit code conventions (kept identical to Paperclip for parity):
    0 = success
    2 = argparse / config bug → NO RETRY, alert immediately
    3 = circuit breaker tripped → NO RETRY (intentional skip)
  other nonzero = transient → retry with backoff
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from ..events.bus import EventBus
from ..events.schema import Event

log = logging.getLogger(__name__)

# Retry schedule (seconds). Length determines max_retries default.
RETRY_BACKOFF: tuple[int, ...] = (30, 120, 480)

# Exit codes that mean "don't retry"
NO_RETRY_CODES: frozenset[int] = frozenset({2, 3})


# ---------------------------------------------------------------------------
# Failure signatures — identical to Paperclip; this is intentional so DLQ
# entries from either system can be replayed by the other.
# ---------------------------------------------------------------------------

FAILURE_SIGNATURES: list[tuple[str, str, re.Pattern, str, bool]] = [
    (
        "claude_auth_expired",
        "critical",
        re.compile(r"Not logged in\s*\S+\s*Please run /login", re.I),
        "Run `claude /login` -- all claude_local agents are blocked.",
        False,
    ),
    (
        "claude_auth_expired",
        "critical",
        re.compile(r"Not logged in\s*·\s*Please run /login|invalid_token|authentication.*expired", re.I),
        "Run `claude /login` — all claude_local agents are blocked.",
        False,
    ),
    (
        "anthropic_invalid_api_key",
        "critical",
        re.compile(
            r"anthropic\.AuthenticationError.*(?:Error code:\s*)?401.*invalid x-api-key|invalid x-api-key.*anthropic",
            re.I | re.S,
        ),
        "Anthropic API key is invalid. Rotate/update credentials before replaying DLQ entries.",
        False,
    ),
    (
        "apulu_backend_5xx",
        "high",
        re.compile(r"apulustudio\.onrender\.com.*50[0-9]|Internal Server Error.*upload|Bad Gateway", re.I),
        "Apulu Studio backend is failing. See github.com/iamclu1914/ApuluStudio.",
        True,
    ),
    (
        "token_refresh_fail",
        "high",
        re.compile(r"/api/auth/refresh.*50[0-9]|Token refresh failed", re.I),
        "Apulu Studio auth endpoint is down. Backend probe should detect this.",
        True,
    ),
    (
        "missing_cron_arg",
        "critical",
        re.compile(r"required: --cron", re.I),
        "Adapter config is wrong — not passing --cron. Check agent adapter_config.",
        False,
    ),
    (
        "suno_rate_limit",
        "medium",
        re.compile(r"suno.*rate.?limit|429.*suno", re.I),
        "Suno API rate limit hit. Will recover with backoff.",
        True,
    ),
    (
        "x_rate_limit",
        "medium",
        re.compile(r"Twitter.*429|X.*rate.?limit", re.I),
        "X API rate-limited. Will recover with backoff.",
        True,
    ),
    (
        "bluesky_auth",
        "high",
        re.compile(r"bluesky.*auth|AuthenticationRequired|invalid.?creds.*bsky", re.I),
        "Bluesky credentials rejected. Check credentials.json app password.",
        False,
    ),
]


def detect_signature(output: str) -> dict | None:
    """Return the first matching failure signature, or None."""
    for name, severity, pattern, hint, retryable in FAILURE_SIGNATURES:
        if pattern.search(output):
            return {
                "name": name,
                "severity": severity,
                "hint": hint,
                "retryable": retryable,
            }
    return None


# ---------------------------------------------------------------------------
# Structured result
# ---------------------------------------------------------------------------


@dataclass
class DispatchResult:
    dispatch_id: str
    routine_id: str
    agent_id: str
    routine_name: str
    started_at: str
    ended_at: str
    attempts: int
    final_exit_code: int
    success: bool
    signature: dict | None
    output_tail: str
    duration_sec: float
    shadow: bool = False
    attempt_log: list[dict] = field(default_factory=list)

    def to_dispatch_row(self) -> dict:
        """Shape that maps onto the `dispatches` table."""
        return {
            "id": self.dispatch_id,
            "routine_id": self.routine_id,
            "agent_id": self.agent_id,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "attempt": self.attempts,
            "outcome": (
                "shadow_ok" if self.shadow and self.success
                else "shadow_fail" if self.shadow
                else "ok" if self.success
                else "fail"
            ),
            "exit_code": self.final_exit_code,
            "signature": self.signature["name"] if self.signature else None,
            "stderr_tail": self.output_tail[-2000:],
            "duration_ms": int(self.duration_sec * 1000),
        }


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


async def _publish(bus: EventBus | None, event_type: str, payload: dict) -> None:
    if bus is None:
        return
    try:
        await bus.publish(Event(type=event_type, payload=payload))  # type: ignore[arg-type]
    except Exception:
        log.exception("event publish failed for type=%s", event_type)


async def _run_subprocess(cmd: list[str], cwd: str | Path) -> tuple[int, str, float]:
    """Run cmd, capture combined stdout+stderr, return (exit, output, duration)."""
    started = time.monotonic()
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(cwd),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
    except (FileNotFoundError, NotImplementedError) as exc:
        # NotImplementedError fires on Windows SelectorEventLoop.
        # Fall back to the synchronous subprocess via a worker thread.
        log.debug("create_subprocess_exec failed (%s); falling back to threadpool", exc)
        return await _run_subprocess_threaded(cmd, cwd, started)

    stdout_data, _ = await proc.communicate()
    duration = time.monotonic() - started
    output = stdout_data.decode("utf-8", errors="replace")
    assert proc.returncode is not None
    return proc.returncode, output, duration


async def _run_subprocess_threaded(
    cmd: list[str], cwd: str | Path, started: float
) -> tuple[int, str, float]:
    import subprocess  # stdlib, here to keep top of file clean

    def _sync_run() -> tuple[int, str]:
        result = subprocess.run(
            cmd,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return result.returncode, result.stdout or ""

    loop = asyncio.get_running_loop()
    exit_code, output = await loop.run_in_executor(None, _sync_run)
    return exit_code, output, time.monotonic() - started


async def run_with_retries(
    *,
    routine_id: str,
    routine_name: str,
    agent_id: str,
    cmd: list[str],
    cwd: str | Path,
    max_retries: int = 3,
    backoff_schedule: Iterable[int] = RETRY_BACKOFF,
    shadow: bool = False,
    bus: EventBus | None = None,
    sleep: Iterable[int] | None = None,  # test hook
) -> DispatchResult:
    """Run a routine with retries + signature detection.

    Emits these events on the bus:
      - routine.started          (payload: routine_id, routine_name, agent_id, dispatch_id, attempt)
      - dispatch.retry_scheduled (payload: ..., delay_sec, reason)
      - routine.succeeded        (payload: ..., duration_sec)
      - routine.failed           (payload: ..., signature, output_tail)
      - dlq.appended             (only if final attempt failed and was non-success)
    """
    backoff = list(backoff_schedule)
    if len(backoff) < max_retries:
        backoff += [backoff[-1] if backoff else 60] * (max_retries - len(backoff))

    sleep_fn = (lambda s: asyncio.sleep(s)) if sleep is None else None
    sleep_iter = iter(sleep) if sleep is not None else None

    dispatch_id = str(uuid.uuid4())
    started_at = _now_iso()
    started_mono = time.monotonic()

    common_payload = {
        "dispatch_id": dispatch_id,
        "routine_id": routine_id,
        "routine_name": routine_name,
        "agent_id": agent_id,
        "shadow": shadow,
    }

    last_exit = 1
    last_output = ""
    last_signature: dict | None = None
    attempt_log: list[dict] = []

    attempt = 0
    for attempt in range(1, max_retries + 1):
        await _publish(
            bus,
            "routine.started",
            {**common_payload, "attempt": attempt, "max_attempts": max_retries},
        )

        if shadow:
            # Simulate a fast successful run.
            exit_code, output, duration = 0, f"[shadow] would run: {' '.join(cmd)}\n", 0.05
            await asyncio.sleep(0)  # yield to loop for fairness
        else:
            exit_code, output, duration = await _run_subprocess(cmd, cwd)

        signature = detect_signature(output)
        last_exit = exit_code
        last_output = output
        last_signature = signature
        attempt_log.append({
            "attempt": attempt,
            "exit_code": exit_code,
            "duration_sec": round(duration, 3),
            "signature": signature["name"] if signature else None,
        })

        # Clean success: exit 0 and no critical/high signature swallowed
        clean_success = exit_code == 0 and (
            signature is None or signature["severity"] not in ("critical", "high")
        )
        if clean_success:
            ended_at = _now_iso()
            total = time.monotonic() - started_mono
            await _publish(
                bus,
                "routine.succeeded",
                {
                    **common_payload,
                    "attempt": attempt,
                    "duration_sec": round(total, 3),
                },
            )
            return DispatchResult(
                dispatch_id=dispatch_id,
                routine_id=routine_id,
                agent_id=agent_id,
                routine_name=routine_name,
                started_at=started_at,
                ended_at=ended_at,
                attempts=attempt,
                final_exit_code=0,
                success=True,
                signature=signature,
                output_tail=output[-2000:],
                duration_sec=total,
                shadow=shadow,
                attempt_log=attempt_log,
            )

        # Non-success path — decide retry
        no_retry_by_code = exit_code in NO_RETRY_CODES
        no_retry_by_sig = signature is not None and not signature["retryable"]
        will_retry = attempt < max_retries and not no_retry_by_code and not no_retry_by_sig

        if not will_retry:
            break

        delay = backoff[attempt - 1]
        reason = "exit_code" if exit_code != 0 else f"signature:{signature['name']}"
        await _publish(
            bus,
            "dispatch.retry_scheduled",
            {
                **common_payload,
                "attempt": attempt,
                "next_attempt": attempt + 1,
                "delay_sec": delay,
                "reason": reason,
                "signature": signature["name"] if signature else None,
            },
        )
        if sleep_iter is not None:
            await asyncio.sleep(next(sleep_iter, 0))
        else:
            await sleep_fn(delay)  # type: ignore[misc]

    # All attempts exhausted (or non-retryable). Final = failure.
    ended_at = _now_iso()
    total = time.monotonic() - started_mono
    payload = {
        **common_payload,
        "attempt": attempt,
        "max_attempts": max_retries,
        "exit_code": last_exit,
        "signature": last_signature["name"] if last_signature else None,
        "signature_severity": last_signature["severity"] if last_signature else None,
        "hint": last_signature["hint"] if last_signature else None,
        "output_tail": last_output[-1500:],
        "duration_sec": round(total, 3),
    }
    await _publish(bus, "routine.failed", payload)
    await _publish(bus, "dlq.appended", payload)

    return DispatchResult(
        dispatch_id=dispatch_id,
        routine_id=routine_id,
        agent_id=agent_id,
        routine_name=routine_name,
        started_at=started_at,
        ended_at=ended_at,
        attempts=attempt,
        final_exit_code=last_exit if last_exit != 0 else 1,
        success=False,
        signature=last_signature,
        output_tail=last_output[-2000:],
        duration_sec=total,
        shadow=shadow,
        attempt_log=attempt_log,
    )
