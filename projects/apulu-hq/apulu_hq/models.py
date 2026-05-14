"""Dataclasses + helpers used across the API and importer.

Kept deliberately thin — these mirror SQLite rows. Pydantic models live
next to the API endpoints to handle request/response shaping.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_id() -> str:
    return str(uuid.uuid4())


@dataclass
class Agent:
    id: str
    legacy_id: str | None
    display_name: str
    department: str
    role: str
    adapter_type: str  # claude_local | process | api
    adapter_config: dict[str, Any] = field(default_factory=dict)
    model: str | None = None
    provider: str | None = None
    system_prompt: str | None = None
    desk_x: int = 0
    desk_y: int = 0
    sprite_key: str = "default"
    enabled: bool = True
    budget_monthly_usd: float | None = None
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)

    @classmethod
    def from_row(cls, row) -> "Agent":
        d = dict(row)
        d["adapter_config"] = json.loads(d.get("adapter_config") or "{}")
        d["enabled"] = bool(d["enabled"])
        return cls(**d)

    def to_db(self) -> dict[str, Any]:
        d = asdict(self)
        d["adapter_config"] = json.dumps(d["adapter_config"])
        d["enabled"] = 1 if d["enabled"] else 0
        return d


@dataclass
class Routine:
    id: str
    legacy_id: str | None
    display_name: str
    agent_id: str
    cron_expr: str
    timezone: str = "America/New_York"
    command: str = ""
    args: list[str] = field(default_factory=list)
    description: str | None = None
    priority: str = "medium"
    enabled: bool = False
    disabled_reason: str | None = None
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)

    @classmethod
    def from_row(cls, row) -> "Routine":
        d = dict(row)
        d["args"] = json.loads(d.get("args") or "[]")
        d["enabled"] = bool(d["enabled"])
        return cls(**d)

    def to_db(self) -> dict[str, Any]:
        d = asdict(self)
        d["args"] = json.dumps(d["args"])
        d["enabled"] = 1 if d["enabled"] else 0
        return d
