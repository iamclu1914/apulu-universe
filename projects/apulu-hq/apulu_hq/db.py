"""SQLite connection, schema bootstrap, and lightweight migrations.

v0 keeps things simple: a single `schema_version` row in `meta` drives
forward-only migration. Alembic can be introduced later if needed.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .config import settings

SCHEMA_VERSION = 1


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS agents (
    id              TEXT PRIMARY KEY,
    legacy_id       TEXT,
    display_name    TEXT NOT NULL,
    department      TEXT NOT NULL,
    role            TEXT NOT NULL,
    adapter_type    TEXT NOT NULL,
    adapter_config  TEXT NOT NULL DEFAULT '{}',
    model           TEXT,
    provider        TEXT,
    system_prompt   TEXT,
    desk_x          INTEGER NOT NULL DEFAULT 0,
    desk_y          INTEGER NOT NULL DEFAULT 0,
    sprite_key      TEXT NOT NULL DEFAULT 'default',
    enabled         INTEGER NOT NULL DEFAULT 1,
    budget_monthly_usd REAL,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS routines (
    id              TEXT PRIMARY KEY,
    legacy_id       TEXT,
    display_name    TEXT NOT NULL,
    agent_id        TEXT NOT NULL REFERENCES agents(id),
    cron_expr       TEXT NOT NULL,
    timezone        TEXT NOT NULL DEFAULT 'America/New_York',
    command         TEXT NOT NULL DEFAULT '',
    args            TEXT NOT NULL DEFAULT '[]',
    description     TEXT,
    priority        TEXT NOT NULL DEFAULT 'medium',
    enabled         INTEGER NOT NULL DEFAULT 0,
    disabled_reason TEXT,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dispatches (
    id              TEXT PRIMARY KEY,
    routine_id      TEXT NOT NULL REFERENCES routines(id),
    agent_id        TEXT NOT NULL REFERENCES agents(id),
    started_at      TEXT NOT NULL,
    ended_at        TEXT,
    attempt         INTEGER NOT NULL DEFAULT 1,
    outcome         TEXT,
    exit_code       INTEGER,
    signature       TEXT,
    stderr_tail     TEXT,
    duration_ms     INTEGER
);
CREATE INDEX IF NOT EXISTS idx_dispatches_started ON dispatches(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_dispatches_routine ON dispatches(routine_id, started_at DESC);

CREATE TABLE IF NOT EXISTS dlq (
    id              TEXT PRIMARY KEY,
    dispatch_id     TEXT REFERENCES dispatches(id),
    routine_id      TEXT NOT NULL REFERENCES routines(id),
    agent_id        TEXT NOT NULL REFERENCES agents(id),
    signature       TEXT,
    payload         TEXT NOT NULL DEFAULT '{}',
    appended_at     TEXT NOT NULL,
    replayed_at     TEXT,
    replay_outcome  TEXT,
    discarded_at    TEXT
);
CREATE INDEX IF NOT EXISTS idx_dlq_active ON dlq(appended_at DESC) WHERE replayed_at IS NULL AND discarded_at IS NULL;

CREATE TABLE IF NOT EXISTS chat_threads (
    id          TEXT PRIMARY KEY,
    agent_id    TEXT NOT NULL REFERENCES agents(id),
    title       TEXT,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chat_threads_agent ON chat_threads(agent_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS chat_messages (
    id          TEXT PRIMARY KEY,
    thread_id   TEXT NOT NULL REFERENCES chat_threads(id),
    role        TEXT NOT NULL,
    content     TEXT NOT NULL,
    tokens_in   INTEGER,
    tokens_out  INTEGER,
    cost_usd    REAL,
    created_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chat_messages_thread ON chat_messages(thread_id, created_at);

CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          TEXT NOT NULL,
    type        TEXT NOT NULL,
    payload     TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts DESC);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(type, ts DESC);
"""


_lock = threading.Lock()


def _connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or settings.db_path
    settings.ensure_dirs()
    conn = sqlite3.connect(path, check_same_thread=False, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn


_conn: sqlite3.Connection | None = None


def get_conn() -> sqlite3.Connection:
    """Return the shared module-level connection, initialising on first use."""
    global _conn
    with _lock:
        if _conn is None:
            _conn = _connect()
            init_schema(_conn)
        return _conn


def init_schema(conn: sqlite3.Connection) -> None:
    """Apply schema. Idempotent. Forward-only migrations live here."""
    conn.executescript(SCHEMA_SQL)
    row = conn.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
    current = int(row["value"]) if row else 0
    if current < SCHEMA_VERSION:
        conn.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES('schema_version', ?)",
            (str(SCHEMA_VERSION),),
        )
    conn.commit()


@contextmanager
def tx() -> Iterator[sqlite3.Connection]:
    """Transaction context manager that commits on success, rolls back on error."""
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def json_loads_safe(s: str | None, default):
    if not s:
        return default
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return default
