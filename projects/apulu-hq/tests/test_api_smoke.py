import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from apulu_hq.api import app
    from apulu_hq.importer import import_all

    import_all()
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True
    assert j["agents"] == 16
    assert j["routines"] == 26


def test_list_agents(client):
    r = client.get("/api/agents")
    assert r.status_code == 200
    agents = r.json()
    assert len(agents) == 16
    nelly = next(a for a in agents if a["display_name"] == "Nelly")
    assert nelly["department"] == "cos"
    assert nelly["adapter_type"] == "hermes_local"
    assert nelly["system_prompt"] is not None


def test_list_routines(client):
    r = client.get("/api/routines")
    assert r.status_code == 200
    routines = r.json()
    assert len(routines) == 26
    names = {x["display_name"] for x in routines}
    assert {"hashtag-scan", "morning-early", "video-cinematic", "lyric-card",
            "system-health-check", "track-teaser"} <= names

    # Disabled routines preserved
    disabled = [x for x in routines if not x["enabled"]]
    disabled_names = {x["display_name"] for x in disabled}
    assert {"lyric-card", "video-cinematic"} <= disabled_names


def test_patch_routine_enable(client):
    routines = client.get("/api/routines").json()
    target = next(x for x in routines if x["display_name"] == "video-cinematic")
    assert target["enabled"] is False
    r = client.patch(f"/api/routines/{target['id']}", json={"enabled": True})
    assert r.status_code == 200
    assert r.json()["enabled"] is True
    # Restore
    client.patch(f"/api/routines/{target['id']}", json={"enabled": False})


def test_patch_agent_system_prompt(client):
    agents = client.get("/api/agents").json()
    rex = next(a for a in agents if a["display_name"] == "Rex")
    r = client.patch(
        f"/api/agents/{rex['id']}",
        json={"system_prompt": "TEST PROMPT REX"},
    )
    assert r.status_code == 200
    assert r.json()["system_prompt"] == "TEST PROMPT REX"


def test_chat_hermes_local_uses_subprocess_adapter(client, monkeypatch):
    """All seeded agents now route through the hermes_local adapter. We stub
    it so the test doesn't actually spawn Hermes."""
    import time
    from apulu_hq.chat import hermes_local as hl

    async def fake_stream(*, agent_id, thread_id, user_message, history, system_prompt, model=None, cwd=None, timeout_seconds=300.0):
        from apulu_hq.events import Event
        yield Event(type="chat.token", payload={"thread_id": thread_id, "agent_id": agent_id, "token": "STUB "})
        yield Event(type="chat.token", payload={"thread_id": thread_id, "agent_id": agent_id, "token": "OK"})
        yield Event(type="chat.done", payload={"thread_id": thread_id, "agent_id": agent_id, "duration_ms": 12, "input_tokens": 5, "output_tokens": 2})

    monkeypatch.setattr(hl, "stream_hermes_local", fake_stream)

    agents = client.get("/api/agents").json()
    nelly = next(a for a in agents if a["display_name"] == "Nelly")
    assert nelly["adapter_type"] == "hermes_local"

    r = client.post(f"/api/agents/{nelly['id']}/chat", json={"message": "hi"})
    assert r.status_code == 200

    deadline = time.time() + 3.0
    msgs: list = []
    while time.time() < deadline:
        threads = client.get(f"/api/agents/{nelly['id']}/threads").json()
        if threads:
            msgs = client.get(f"/api/threads/{threads[0]['id']}/messages").json()
            if len(msgs) >= 2:
                break
        time.sleep(0.05)
    assert len(msgs) >= 2
    assert msgs[1]["role"] == "assistant"
    assert msgs[1]["content"] == "STUB OK"
    assert msgs[1]["tokens_in"] == 5
    assert msgs[1]["tokens_out"] == 2


def test_websocket_emits_heartbeat(client):
    with client.websocket_connect("/ws") as ws:
        # First message is the synthetic hello
        first = ws.receive_json()
        assert first["type"] == "heartbeat"
        assert first["v"] == 1


def test_dispatches_endpoint_returns_recent_rows(client):
    """After the tailer ingests a synthetic log line via direct insert,
    /api/dispatches should join routine + agent names."""
    from apulu_hq.db import get_conn

    # Insert a synthetic dispatch row directly
    agents = client.get("/api/agents").json()
    routines = client.get("/api/routines").json()
    nelly = next(a for a in agents if a["display_name"] == "Nelly")
    hashtag = next(r for r in routines if r["display_name"] == "hashtag-scan")

    conn = get_conn()
    conn.execute(
        """INSERT INTO dispatches
           (id, routine_id, agent_id, started_at, ended_at, attempt, outcome,
            exit_code, signature, stderr_tail, duration_ms)
           VALUES ('d1', ?, ?, '2026-05-14T03:00:00+00:00',
                   '2026-05-14T03:00:12+00:00', 1, 'success', 0, NULL, NULL, 12000)""",
        (hashtag["id"], nelly["id"]),
    )
    conn.commit()

    rows = client.get("/api/dispatches").json()
    assert len(rows) == 1
    assert rows[0]["routine_name"] == "hashtag-scan"
    assert rows[0]["agent_name"] == "Nelly"
    assert rows[0]["outcome"] == "success"
    assert rows[0]["duration_ms"] == 12000
