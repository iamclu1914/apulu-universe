"""Dispatch subsystem — runner + scheduler + persistence.

The runner ports Paperclip's dispatch_runner with retries, signature
detection, and DLQ. The scheduler wraps APScheduler to cron-fire routines.
Persistence helpers write dispatch + DLQ rows back to the same SQLite the
tailers already populate.

Shadow mode (default): the scheduler fires every enabled routine on cron
but each fire is a no-op subprocess — events still flow, dispatch + DLQ
rows still get written with outcome='shadow_ok'/'shadow_fail'. This lets
us soak the scheduler alongside Paperclip without dual-fire risk.

To flip to real fire, set HQ_DISPATCHER_SHADOW=0 in the environment.
"""

from .persist import write_dispatch, write_dlq
from .runner import (
    DispatchResult,
    FAILURE_SIGNATURES,
    NO_RETRY_CODES,
    RETRY_BACKOFF,
    detect_signature,
    run_with_retries,
)
from .scheduler import HQScheduler

__all__ = [
    "DispatchResult",
    "FAILURE_SIGNATURES",
    "HQScheduler",
    "NO_RETRY_CODES",
    "RETRY_BACKOFF",
    "detect_signature",
    "run_with_retries",
    "write_dispatch",
    "write_dlq",
]
