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

SCHEMA_VERSION = 3


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

CREATE TABLE IF NOT EXISTS releases (
    id                  TEXT PRIMARY KEY,
    title               TEXT NOT NULL,
    artist              TEXT NOT NULL DEFAULT 'Vawn',
    type                TEXT NOT NULL DEFAULT 'single',
    status              TEXT NOT NULL DEFAULT 'planning',
    release_date        TEXT,
    distributor         TEXT NOT NULL DEFAULT 'DistroKid',
    artwork_status      TEXT NOT NULL DEFAULT 'pending',
    master_status       TEXT NOT NULL DEFAULT 'pending',
    metadata_status     TEXT NOT NULL DEFAULT 'pending',
    distributor_status  TEXT NOT NULL DEFAULT 'pending',
    publishing_status   TEXT NOT NULL DEFAULT 'pending',
    budget              REAL,
    spend_to_date       REAL NOT NULL DEFAULT 0,
    notes               TEXT,
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_releases_status ON releases(status, release_date);

CREATE TABLE IF NOT EXISTS campaigns (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    artist          TEXT NOT NULL DEFAULT 'Vawn',
    release_id      TEXT REFERENCES releases(id),
    objective       TEXT NOT NULL DEFAULT 'awareness',
    status          TEXT NOT NULL DEFAULT 'draft',
    start_date      TEXT,
    end_date        TEXT,
    platforms       TEXT NOT NULL DEFAULT '[]',
    budget          REAL,
    spend_to_date   REAL NOT NULL DEFAULT 0,
    primary_metric  TEXT,
    target_value    REAL,
    notes           TEXT,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status, start_date, end_date);

CREATE TABLE IF NOT EXISTS approvals (
    id              TEXT PRIMARY KEY,
    title           TEXT NOT NULL,
    category        TEXT NOT NULL DEFAULT 'operations',
    priority        TEXT NOT NULL DEFAULT 'medium',
    status          TEXT NOT NULL DEFAULT 'open',
    requested_by    TEXT,
    assigned_to     TEXT,
    due_at          TEXT,
    linked_type     TEXT,
    linked_id       TEXT,
    decision_note   TEXT,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals(status, priority, due_at);

CREATE TABLE IF NOT EXISTS finance_entries (
    id              TEXT PRIMARY KEY,
    entry_type      TEXT NOT NULL DEFAULT 'expense',
    source          TEXT,
    vendor          TEXT,
    category        TEXT NOT NULL DEFAULT 'operations',
    amount          REAL NOT NULL DEFAULT 0,
    entry_date      TEXT NOT NULL,
    linked_type     TEXT,
    linked_id       TEXT,
    notes           TEXT,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_finance_entries_date ON finance_entries(entry_date DESC, entry_type);

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
    if current < 3:
        cols = {r["name"] for r in conn.execute("PRAGMA table_info(releases)").fetchall()}
        if "distributor" not in cols:
            conn.execute("ALTER TABLE releases ADD COLUMN distributor TEXT NOT NULL DEFAULT 'DistroKid'")
        conn.execute(
            "UPDATE releases SET distributor='DistroKid' "
            "WHERE artist='Vawn' AND (distributor IS NULL OR distributor='' OR distributor='pending')"
        )
    _seed_command_center(conn)
    if current < SCHEMA_VERSION:
        conn.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES('schema_version', ?)",
            (str(SCHEMA_VERSION),),
        )
    conn.commit()


def _seed_command_center(conn: sqlite3.Connection) -> None:
    """Create starter label-ops records without inventing financial results."""
    release_count = conn.execute("SELECT COUNT(*) AS c FROM releases").fetchone()["c"]
    if release_count == 0:
        now = "2026-05-16T00:00:00+00:00"
        conn.execute(
            """INSERT INTO releases
               (id, title, artist, type, status, release_date, distributor, artwork_status,
                master_status, metadata_status, distributor_status, publishing_status,
                budget, spend_to_date, notes, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "rel-vawn-debut",
                "Vawn Debut Project",
                "Vawn",
                "album",
                "production",
                None,
                "DistroKid",
                "in_progress",
                "in_progress",
                "pending",
                "pending",
                "pending",
                None,
                0,
                "Starter release record. Replace with final title, date, and delivery status.",
                now,
                now,
            ),
        )

    campaign_count = conn.execute("SELECT COUNT(*) AS c FROM campaigns").fetchone()["c"]
    if campaign_count == 0:
        now = "2026-05-16T00:00:00+00:00"
        conn.execute(
            """INSERT INTO campaigns
               (id, name, artist, release_id, objective, status, start_date, end_date,
                platforms, budget, spend_to_date, primary_metric, target_value, notes,
                created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "camp-vawn-rollout",
                "Vawn Social Rollout",
                "Vawn",
                "rel-vawn-debut",
                "awareness",
                "active",
                "2026-05-12",
                None,
                json.dumps(["instagram", "tiktok", "threads", "x", "bluesky", "facebook"]),
                None,
                0,
                "successful_posts",
                None,
                "Starter campaign connected to the current social posting ledger.",
                now,
                now,
            ),
        )

    approval_count = conn.execute("SELECT COUNT(*) AS c FROM approvals").fetchone()["c"]
    if approval_count == 0:
        now = "2026-05-16T00:00:00+00:00"
        conn.execute(
            """INSERT INTO approvals
               (id, title, category, priority, status, requested_by, assigned_to,
                due_at, linked_type, linked_id, decision_note, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "appr-release-readiness",
                "Confirm release readiness checklist",
                "release",
                "high",
                "open",
                "Operations",
                "CEO",
                None,
                "release",
                "rel-vawn-debut",
                None,
                now,
                now,
            ),
        )


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
