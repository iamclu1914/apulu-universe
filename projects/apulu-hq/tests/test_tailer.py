"""Tailer integration tests — synthesize jsonl, drive the tailer once, assert."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest


@pytest.fixture
def seeded():
    """Import + run importer so we have routines for slot resolution."""
    from apulu_hq.importer import import_all

    import_all()
    yield


async def _drive_tailer_once(tailer_coro_factory, path: Path, *, max_wait: float = 2.5):
    """Run one of our forever-loop tailers in the background just long enough
    for it to consume the file, then cancel."""
    task = asyncio.create_task(tailer_coro_factory(path, poll_interval=0.1))
    try:
        # Spin until the offset moves or we time out.
        from apulu_hq.tailer import get_offset

        deadline = asyncio.get_event_loop().time() + max_wait
        while asyncio.get_event_loop().time() < deadline:
            await asyncio.sleep(0.1)
            if get_offset(path) >= path.stat().st_size:
                # Give one more tick so any final publish/IO completes.
                await asyncio.sleep(0.1)
                break
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


@pytest.mark.asyncio
async def test_dispatch_log_emits_routine_started_and_succeeded(seeded, tmp_path):
    from apulu_hq.db import get_conn
    from apulu_hq.events import get_bus
    from apulu_hq.tailer import tail_dispatch_log

    log_path = tmp_path / "dispatch_log.jsonl"
    log_path.write_text(
        json.dumps({
            "timestamp": "2026-05-14T01:00:00+00:00",
            "slot": "morning-early",
            "attempt": 1,
            "max_attempts": 3,
            "exit_code": 0,
            "duration_sec": 12.3,
            "signature": None,
            "retryable": True,
            "final": True,
            "success": True,
        }) + "\n",
        encoding="utf-8",
    )

    bus = get_bus()
    sub = await bus.subscribe()
    collected = []

    async def collect():
        async for ev in sub.stream():
            collected.append(ev)

    collector = asyncio.create_task(collect())
    await _drive_tailer_once(tail_dispatch_log, log_path)
    await asyncio.sleep(0.2)
    collector.cancel()
    await sub.close()

    types = [e.type for e in collected]
    assert "routine.started" in types
    assert "routine.succeeded" in types

    rows = get_conn().execute("SELECT outcome, attempt FROM dispatches").fetchall()
    assert len(rows) == 1
    assert rows[0]["outcome"] == "success"
    assert rows[0]["attempt"] == 1


@pytest.mark.asyncio
async def test_dispatch_log_emits_failed_with_signature(seeded, tmp_path):
    from apulu_hq.db import get_conn
    from apulu_hq.events import get_bus
    from apulu_hq.tailer import tail_dispatch_log

    log_path = tmp_path / "dispatch_log.jsonl"
    log_path.write_text(
        json.dumps({
            "timestamp": "2026-05-14T02:00:00+00:00",
            "slot": "evening-early",
            "attempt": 3,
            "max_attempts": 3,
            "exit_code": 1,
            "duration_sec": 27.9,
            "signature": "preflight_blocked_ai_word",
            "retryable": True,
            "final": True,
            "success": False,
        }) + "\n",
        encoding="utf-8",
    )

    bus = get_bus()
    sub = await bus.subscribe()
    collected = []

    async def collect():
        async for ev in sub.stream():
            collected.append(ev)

    collector = asyncio.create_task(collect())
    await _drive_tailer_once(tail_dispatch_log, log_path)
    await asyncio.sleep(0.2)
    collector.cancel()
    await sub.close()

    failed = [e for e in collected if e.type == "routine.failed"]
    assert len(failed) == 1
    assert failed[0].payload["signature"] == "preflight_blocked_ai_word"
    assert failed[0].payload["exit_code"] == 1

    row = get_conn().execute(
        "SELECT outcome, signature FROM dispatches"
    ).fetchone()
    assert row["outcome"] == "failure"
    assert row["signature"] == "preflight_blocked_ai_word"


@pytest.mark.asyncio
async def test_dispatch_log_offset_survives_restart(seeded, tmp_path):
    from apulu_hq.db import get_conn
    from apulu_hq.tailer import tail_dispatch_log

    log_path = tmp_path / "dispatch_log.jsonl"

    def append(row):
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")

    append({
        "timestamp": "2026-05-14T01:00:00+00:00", "slot": "morning-early",
        "attempt": 1, "max_attempts": 3, "exit_code": 0, "duration_sec": 1.0,
        "signature": None, "retryable": True, "final": True, "success": True,
    })

    await _drive_tailer_once(tail_dispatch_log, log_path)
    assert get_conn().execute("SELECT COUNT(*) AS c FROM dispatches").fetchone()["c"] == 1

    # Simulate restart by reading offset, appending, running tailer again.
    append({
        "timestamp": "2026-05-14T01:01:00+00:00", "slot": "morning-main",
        "attempt": 1, "max_attempts": 3, "exit_code": 0, "duration_sec": 2.0,
        "signature": None, "retryable": True, "final": True, "success": True,
    })

    await _drive_tailer_once(tail_dispatch_log, log_path)
    assert get_conn().execute("SELECT COUNT(*) AS c FROM dispatches").fetchone()["c"] == 2


@pytest.mark.asyncio
async def test_dead_letter_emits_event_and_persists(seeded, tmp_path):
    from apulu_hq.db import get_conn
    from apulu_hq.events import get_bus
    from apulu_hq.tailer import tail_dead_letter

    dlq_path = tmp_path / "dead_letter.jsonl"
    dlq_path.write_text(
        json.dumps({
            "timestamp": "2026-05-13T22:04:43.673534+00:00",
            "slot": "evening-early",
            "cmd": ["python", "post_vawn.py", "--cron", "evening"],
            "attempts": 3,
            "final_exit_code": 1,
            "signature": "preflight_blocked",
            "output_tail": "...trimmed...",
        }) + "\n",
        encoding="utf-8",
    )

    bus = get_bus()
    sub = await bus.subscribe()
    collected = []

    async def collect():
        async for ev in sub.stream():
            collected.append(ev)

    collector = asyncio.create_task(collect())
    await _drive_tailer_once(tail_dead_letter, dlq_path)
    await asyncio.sleep(0.2)
    collector.cancel()
    await sub.close()

    appended = [e for e in collected if e.type == "dlq.appended"]
    assert len(appended) == 1
    assert appended[0].payload["slot"] == "evening-early"
    assert appended[0].payload["signature"] == "preflight_blocked"

    rows = get_conn().execute(
        "SELECT signature, payload FROM dlq WHERE signature='preflight_blocked'"
    ).fetchall()
    assert len(rows) == 1
    assert "post_vawn.py" in rows[0]["payload"]


@pytest.mark.asyncio
async def test_dict_shaped_signature_is_normalized(seeded, tmp_path):
    """Newer Vawn dead_letter entries store signature as a dict; we must
    extract the canonical name into the column without crashing."""
    from apulu_hq.db import get_conn
    from apulu_hq.tailer import tail_dead_letter

    dlq_path = tmp_path / "dead_letter.jsonl"
    dlq_path.write_text(
        json.dumps({
            "timestamp": "2026-05-13T22:04:43.673534+00:00",
            "slot": "evening-early",
            "attempts": 3,
            "final_exit_code": 1,
            "signature": {
                "name": "apulu_backend_5xx",
                "severity": "high",
                "hint": "Apulu Studio backend is failing.",
                "retryable": True,
            },
            "output_tail": "trimmed",
        }) + "\n",
        encoding="utf-8",
    )

    await _drive_tailer_once(tail_dead_letter, dlq_path)
    row = get_conn().execute(
        "SELECT signature FROM dlq WHERE signature IS NOT NULL"
    ).fetchone()
    assert row is not None
    assert row["signature"] == "apulu_backend_5xx"


@pytest.mark.asyncio
async def test_backend_health_emits_snapshot_and_breaker_on_state_change(seeded, tmp_path):
    from apulu_hq.events import get_bus
    from apulu_hq.tailer import tail_backend_health

    h_path = tmp_path / "backend_health.json"
    h_path.write_text(json.dumps({"overall": "healthy"}), encoding="utf-8")

    bus = get_bus()
    sub = await bus.subscribe()
    collected = []

    async def collect():
        async for ev in sub.stream():
            collected.append(ev)

    collector = asyncio.create_task(collect())

    task = asyncio.create_task(tail_backend_health(h_path, poll_interval=0.1))
    await asyncio.sleep(0.3)
    # Flip to degraded
    h_path.write_text(json.dumps({"overall": "degraded"}), encoding="utf-8")
    await asyncio.sleep(0.6)
    # Flip back to healthy
    h_path.write_text(json.dumps({"overall": "healthy"}), encoding="utf-8")
    await asyncio.sleep(0.6)

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    collector.cancel()
    await sub.close()

    types = [e.type for e in collected]
    assert types.count("health.snapshot") >= 2
    assert "breaker.tripped" in types
    assert "breaker.cleared" in types
