"""Versioned WebSocket event schema. Validated with Pydantic.

Adding a new field to an existing event is backwards-compatible.
Renaming or removing a field requires bumping SCHEMA_VERSION and migrating consumers.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


SCHEMA_VERSION = 1


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


EventType = Literal[
    "agent.state_changed",
    "agent.status_changed",
    "routine.started",
    "routine.succeeded",
    "routine.failed",
    "dispatch.retry_scheduled",
    "breaker.tripped",
    "breaker.cleared",
    "dlq.appended",
    "dlq.replayed",
    "chat.token",
    "chat.done",
    "briefing.ready",
    "health.snapshot",
    "heartbeat",
]


class Event(BaseModel):
    type: EventType
    ts: str = Field(default_factory=_now)
    payload: dict[str, Any] = Field(default_factory=dict)
    v: int = SCHEMA_VERSION

    def to_wire(self) -> dict[str, Any]:
        return self.model_dump()
