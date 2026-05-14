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
    assert nelly["adapter_type"] == "claude_local"
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


def test_chat_mock_mode_round_trip(client):
    """With no ANTHROPIC_API_KEY, chat should return a deterministic mock reply
    and persist both user + assistant messages."""
    agents = client.get("/api/agents").json()
    nelly = next(a for a in agents if a["display_name"] == "Nelly")

    r = client.post(
        f"/api/agents/{nelly['id']}/chat",
        json={"message": "ping"},
    )
    assert r.status_code == 200

    # Mock mode is synchronous-ish (no await on Anthropic) — but the task is
    # scheduled asynchronously. Poll the threads endpoint briefly.
    import time
    deadline = time.time() + 2.0
    while time.time() < deadline:
        threads = client.get(f"/api/agents/{nelly['id']}/threads").json()
        if threads:
            break
        time.sleep(0.05)
    assert threads, "no thread created"

    msgs = client.get(f"/api/threads/{threads[0]['id']}/messages").json()
    deadline = time.time() + 2.0
    while time.time() < deadline and len(msgs) < 2:
        time.sleep(0.05)
        msgs = client.get(f"/api/threads/{threads[0]['id']}/messages").json()
    assert len(msgs) >= 2
    assert msgs[0]["role"] == "user"
    assert msgs[0]["content"] == "ping"
    assert msgs[1]["role"] == "assistant"
    assert "mock mode" in msgs[1]["content"]


def test_websocket_emits_heartbeat(client):
    with client.websocket_connect("/ws") as ws:
        # First message is the synthetic hello
        first = ws.receive_json()
        assert first["type"] == "heartbeat"
        assert first["v"] == 1
