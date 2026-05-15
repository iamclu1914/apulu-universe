def test_schema_bootstrap_creates_tables():
    from apulu_hq.db import get_conn

    conn = get_conn()
    tables = {
        r["name"]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    expected = {
        "meta",
        "agents",
        "routines",
        "dispatches",
        "dlq",
        "chat_threads",
        "chat_messages",
        "events",
    }
    assert expected <= tables, f"missing tables: {expected - tables}"


def test_schema_version_recorded():
    from apulu_hq.db import SCHEMA_VERSION, get_conn

    row = get_conn().execute(
        "SELECT value FROM meta WHERE key='schema_version'"
    ).fetchone()
    assert row is not None
    assert int(row["value"]) == SCHEMA_VERSION
