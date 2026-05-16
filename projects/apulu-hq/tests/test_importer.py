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
