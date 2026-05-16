def test_import_populates_16_agents_and_26_routines():
    from apulu_hq.db import get_conn
    from apulu_hq.importer import import_all

    counts = import_all()
    assert counts == {"agents": 16, "routines": 26}, counts

    conn = get_conn()
    names = {
        r["display_name"]
        for r in conn.execute("SELECT display_name FROM agents").fetchall()
    }
    expected = {
        "Clu", "Nelly", "Dex", "Nova", "Sage & Khari", "Rex", "Rhythm",
        "Cipher", "Onyx", "Cole", "Echo", "Vibe", "Sable", "Camdyn",
        "Oaklyn", "Aspyn",
    }
    assert names == expected, names ^ expected
    assert not {"Timbo", "Letitia", "Nari"} & names


def test_current_presidents_keep_legacy_ids_and_hermes_adapter():
    import json

    from apulu_hq.config import settings
    from apulu_hq.db import get_conn
    from apulu_hq.importer import import_all

    import_all()
    legacy = json.loads(
        (settings.repo_root / "scripts" / "seeds" / "agent_ids.json").read_text()
    )
    rows = get_conn().execute(
        "SELECT id, display_name, department, adapter_type, enabled "
        "FROM agents WHERE display_name IN ('Aspyn', 'Oaklyn', 'Camdyn')"
    ).fetchall()
    by_name = {r["display_name"]: dict(r) for r in rows}

    assert set(by_name) == {"Aspyn", "Oaklyn", "Camdyn"}
    assert by_name["Aspyn"]["id"] == legacy["Aspyn"]
    assert by_name["Oaklyn"]["id"] == legacy["Oaklyn"]
    assert by_name["Camdyn"]["id"] == legacy["Camdyn"]
    assert by_name["Aspyn"]["department"] == "operations"
    assert by_name["Oaklyn"]["department"] == "marketing"
    assert by_name["Camdyn"]["department"] == "production"
    assert {row["adapter_type"] for row in by_name.values()} == {"hermes_local"}
    assert {row["enabled"] for row in by_name.values()} == {1}


def test_current_presidents_are_wired_to_department_task_ownership():
    from apulu_hq.db import get_conn
    from apulu_hq.importer import import_all

    import_all()
    conn = get_conn()

    weekly_ops = conn.execute(
        "SELECT a.display_name AS owner FROM routines r "
        "JOIN agents a ON a.id=r.agent_id WHERE r.display_name='weekly-ops-digest'"
    ).fetchone()
    assert weekly_ops["owner"] == "Aspyn"

    marketing_daily = conn.execute(
        "SELECT COUNT(*) AS c FROM routines r JOIN agents a ON a.id=r.agent_id "
        "WHERE a.department='marketing' AND r.cron_expr LIKE '%* * *'"
    ).fetchone()["c"]
    assert marketing_daily >= 8

    production_head = conn.execute(
        "SELECT display_name, adapter_type FROM agents "
        "WHERE department='production' AND display_name='Camdyn'"
    ).fetchone()
    assert production_head["adapter_type"] == "hermes_local"


def test_import_is_idempotent():
    from apulu_hq.importer import import_all

    c1 = import_all()
    c2 = import_all()
    assert c1 == c2 == {"agents": 16, "routines": 26}


def test_disabled_routines_carry_reason():
    from apulu_hq.db import get_conn
    from apulu_hq.importer import import_all

    import_all()
    rows = get_conn().execute(
        "SELECT display_name, enabled, disabled_reason FROM routines "
        "WHERE display_name IN ('lyric-card', 'video-cinematic')"
    ).fetchall()
    assert len(rows) == 2
    for r in rows:
        assert r["enabled"] == 0
        assert r["disabled_reason"]


def test_import_defaults_keep_daily_routines_active():
    from apulu_hq.db import get_conn
    from apulu_hq.importer import import_all

    import_all()
    conn = get_conn()
    active = conn.execute("SELECT COUNT(*) AS c FROM routines WHERE enabled=1").fetchone()["c"]
    inactive = {
        r["display_name"]
        for r in conn.execute("SELECT display_name FROM routines WHERE enabled=0").fetchall()
    }

    assert active == 24
    assert inactive == {"lyric-card", "video-cinematic"}


def test_import_preserves_user_routine_toggles_when_registry_is_active():
    from apulu_hq.db import get_conn
    from apulu_hq.importer import import_all

    import_all()
    conn = get_conn()
    conn.execute(
        "UPDATE routines SET enabled=0, disabled_reason='paused by operator' "
        "WHERE display_name='hashtag-scan'"
    )
    conn.execute(
        "UPDATE routines SET enabled=1, disabled_reason=NULL "
        "WHERE display_name='lyric-card'"
    )
    conn.commit()

    import_all()
    rows = {
        r["display_name"]: dict(r)
        for r in conn.execute(
            "SELECT display_name, enabled, disabled_reason FROM routines "
            "WHERE display_name IN ('hashtag-scan', 'lyric-card')"
        ).fetchall()
    }

    assert rows["hashtag-scan"]["enabled"] == 0
    assert rows["hashtag-scan"]["disabled_reason"] == "paused by operator"
    assert rows["lyric-card"]["enabled"] == 1
    assert rows["lyric-card"]["disabled_reason"] is None


def test_routine_ids_match_seed_legacy():
    """Every routine row must have a legacy_id == its id."""
    import json
    from pathlib import Path

    from apulu_hq.config import settings
    from apulu_hq.db import get_conn
    from apulu_hq.importer import import_all

    import_all()
    legacy = json.loads(
        (settings.repo_root / "scripts" / "seeds" / "routine_ids.json").read_text()
    )
    rows = get_conn().execute(
        "SELECT id, legacy_id, display_name FROM routines"
    ).fetchall()
    for r in rows:
        assert r["id"] == r["legacy_id"], r["display_name"]
        assert legacy[r["display_name"]] == r["id"], r["display_name"]
