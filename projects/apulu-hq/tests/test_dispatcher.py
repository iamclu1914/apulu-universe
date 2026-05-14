"""Tests for the dispatcher: runner, signature detection, shadow mode, persistence."""

from __future__ import annotations

import asyncio
import sys

import pytest


# ---------------------------------------------------------------------------
# Signature detection — direct unit tests
# ---------------------------------------------------------------------------


def test_detect_signature_returns_none_for_clean_output():
    from apulu_hq.dispatch import detect_signature
    assert detect_signature("All systems nominal. Posted 3 items.") is None


def test_detect_signature_finds_claude_auth():
    from apulu_hq.dispatch import detect_signature
    sig = detect_signature("Not logged in · Please run /login")
    assert sig is not None
    assert sig["name"] == "claude_auth_expired"
    assert sig["severity"] == "critical"
    assert sig["retryable"] is False


def test_detect_signature_finds_anthropic_invalid_key():
    from apulu_hq.dispatch import detect_signature
    output = (
        "anthropic.AuthenticationError: Error code: 401 - "
        "{'error': {'message': 'invalid x-api-key'}}"
    )
    sig = detect_signature(output)
    assert sig is not None
    assert sig["name"] == "anthropic_invalid_api_key"


def test_detect_signature_finds_retryable_backend_5xx():
    from apulu_hq.dispatch import detect_signature
    output = "POST https://apulustudio.onrender.com/upload returned 502 Bad Gateway"
    sig = detect_signature(output)
    assert sig is not None
    assert sig["name"] == "apulu_backend_5xx"
    assert sig["retryable"] is True


def test_failure_signature_inventory_matches_paperclip():
    """The set of signatures must stay aligned with Paperclip for DLQ replay."""
    from apulu_hq.dispatch import FAILURE_SIGNATURES
    names = {row[0] for row in FAILURE_SIGNATURES}
    expected = {
        "claude_auth_expired",
        "anthropic_invalid_api_key",
        "apulu_backend_5xx",
        "token_refresh_fail",
        "missing_cron_arg",
        "suno_rate_limit",
        "x_rate_limit",
        "bluesky_auth",
    }
    assert names == expected


# ---------------------------------------------------------------------------
# Runner — shadow mode (no real subprocess)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_shadow_run_succeeds_without_executing_command():
    from apulu_hq.dispatch import run_with_retries
    from apulu_hq.events.bus import EventBus

    bus = EventBus()
    received: list[str] = []

    async def consume():
        async with await bus.subscribe() as sub:
            while len(received) < 2:
                ev = await asyncio.wait_for(sub._queue.get(), timeout=2)
                received.append(ev.type)

    consumer = asyncio.create_task(consume())
    await asyncio.sleep(0)

    # A command that would FAIL if actually executed
    result = await run_with_retries(
        routine_id="r-1",
        routine_name="shadow-test",
        agent_id="a-1",
        cmd=["nonexistent-binary-xyz", "--definitely-not-here"],
        cwd=".",
        shadow=True,
        bus=bus,
    )

    await asyncio.wait_for(consumer, timeout=3)

    assert result.success is True
    assert result.shadow is True
    assert result.attempts == 1
    assert result.final_exit_code == 0
    assert "routine.started" in received
    assert "routine.succeeded" in received


# ---------------------------------------------------------------------------
# Runner — real subprocess via shadow=False, deterministic exit codes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_real_run_exit_zero_is_success():
    from apulu_hq.dispatch import run_with_retries
    result = await run_with_retries(
        routine_id="r-1",
        routine_name="echo-ok",
        agent_id="a-1",
        cmd=[sys.executable, "-c", "print('ok')"],
        cwd=".",
        shadow=False,
    )
    assert result.success is True
    assert result.attempts == 1
    assert "ok" in result.output_tail


@pytest.mark.asyncio
async def test_real_run_nonretryable_exit_does_not_retry():
    """Exit code 2 (argparse) must not retry — fail fast."""
    from apulu_hq.dispatch import run_with_retries
    result = await run_with_retries(
        routine_id="r-1",
        routine_name="fail-2",
        agent_id="a-1",
        cmd=[sys.executable, "-c", "import sys; sys.exit(2)"],
        cwd=".",
        shadow=False,
        max_retries=3,
        sleep=[0, 0, 0],
    )
    assert result.success is False
    assert result.final_exit_code == 2
    assert result.attempts == 1


@pytest.mark.asyncio
async def test_real_run_transient_failure_retries_then_dlq():
    """Exit code 1 with no signature → retry up to max_retries, then DLQ."""
    from apulu_hq.dispatch import run_with_retries
    result = await run_with_retries(
        routine_id="r-1",
        routine_name="always-fail",
        agent_id="a-1",
        cmd=[sys.executable, "-c", "import sys; sys.exit(1)"],
        cwd=".",
        shadow=False,
        max_retries=3,
        sleep=[0, 0, 0],
    )
    assert result.success is False
    assert result.final_exit_code == 1
    assert result.attempts == 3
    assert len(result.attempt_log) == 3


@pytest.mark.asyncio
async def test_real_run_swallowed_signature_is_treated_as_failure():
    """Exit 0 with a critical signature in output = failure (matches Paperclip)."""
    from apulu_hq.dispatch import run_with_retries
    script = (
        "print('Not logged in · Please run /login')\n"
        "import sys; sys.exit(0)\n"
    )
    result = await run_with_retries(
        routine_id="r-1",
        routine_name="swallowed",
        agent_id="a-1",
        cmd=[sys.executable, "-c", script],
        cwd=".",
        shadow=False,
        max_retries=2,
        sleep=[0, 0],
    )
    assert result.success is False
    assert result.signature is not None
    assert result.signature["name"] == "claude_auth_expired"
    # Non-retryable signature → exactly 1 attempt
    assert result.attempts == 1


# ---------------------------------------------------------------------------
# Persistence — write to SQLite
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_persist_dispatch_and_dlq():
    from apulu_hq.db import get_conn
    from apulu_hq.dispatch import run_with_retries, write_dispatch, write_dlq
    from apulu_hq.importer import import_all

    import_all()
    conn = get_conn()
    routine_row = conn.execute(
        "SELECT r.id AS routine_id, r.display_name AS rname, a.id AS agent_id "
        "FROM routines r JOIN agents a ON a.id = r.agent_id LIMIT 1"
    ).fetchone()
    assert routine_row is not None
    routine_id = routine_row["routine_id"]
    agent_id = routine_row["agent_id"]

    result = await run_with_retries(
        routine_id=routine_id,
        routine_name=routine_row["rname"],
        agent_id=agent_id,
        cmd=[sys.executable, "-c", "import sys; sys.exit(1)"],
        cwd=".",
        max_retries=1,
        sleep=[0],
    )
    write_dispatch(result)
    write_dlq(result)

    dispatches = conn.execute("SELECT id, outcome FROM dispatches").fetchall()
    assert any(d["id"] == result.dispatch_id for d in dispatches)
    fail_row = next(d for d in dispatches if d["id"] == result.dispatch_id)
    assert fail_row["outcome"] == "fail"

    dlq = conn.execute("SELECT dispatch_id FROM dlq WHERE dispatch_id=?",
                       (result.dispatch_id,)).fetchall()
    assert len(dlq) == 1


# ---------------------------------------------------------------------------
# Scheduler endpoints
# ---------------------------------------------------------------------------


def test_scheduler_status_endpoint_when_disabled():
    """With APULU_HQ_DISABLE_SCHEDULER=1, status returns started=False."""
    from fastapi.testclient import TestClient
    from apulu_hq.api.app import create_app

    with TestClient(create_app()) as c:
        r = c.get("/api/scheduler")
        assert r.status_code == 200
        body = r.json()
        assert body["started"] is False
        assert body["jobs"] == []


def test_scheduler_fire_endpoint_requires_scheduler_running():
    from fastapi.testclient import TestClient
    from apulu_hq.api.app import create_app

    with TestClient(create_app()) as c:
        r = c.post("/api/routines/nonexistent/fire")
        assert r.status_code == 503
