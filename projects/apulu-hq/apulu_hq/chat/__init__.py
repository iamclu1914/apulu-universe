"""Per-agent chat router.

Each agent owns one or more chat threads. Messages stream back over WebSocket
via `chat.token` events. History is persisted in SQLite.
"""

from __future__ import annotations

import asyncio
import logging
import sqlite3
from datetime import datetime, timezone
from typing import AsyncIterator

from anthropic import AsyncAnthropic

from ..config import settings
from ..db import get_conn, tx
from ..events import Event, get_bus
from ..models import new_id, now_iso

log = logging.getLogger(__name__)

DEFAULT_MAX_TOKENS = 1024
HISTORY_TURNS = 20  # how many prior messages to include


def _get_or_create_thread(conn: sqlite3.Connection, agent_id: str, thread_id: str | None) -> str:
    if thread_id:
        row = conn.execute(
            "SELECT id FROM chat_threads WHERE id=? AND agent_id=?",
            (thread_id, agent_id),
        ).fetchone()
        if row:
            return thread_id
    new_thread_id = new_id()
    conn.execute(
        "INSERT INTO chat_threads(id, agent_id, title, created_at, updated_at) VALUES(?, ?, ?, ?, ?)",
        (new_thread_id, agent_id, None, now_iso(), now_iso()),
    )
    return new_thread_id


def _load_history(conn: sqlite3.Connection, thread_id: str, limit: int) -> list[dict]:
    rows = conn.execute(
        "SELECT role, content FROM chat_messages WHERE thread_id=? ORDER BY created_at DESC LIMIT ?",
        (thread_id, limit),
    ).fetchall()
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]


def _persist_message(
    conn: sqlite3.Connection,
    thread_id: str,
    role: str,
    content: str,
    tokens_in: int | None = None,
    tokens_out: int | None = None,
) -> str:
    msg_id = new_id()
    conn.execute(
        "INSERT INTO chat_messages(id, thread_id, role, content, tokens_in, tokens_out, created_at) "
        "VALUES(?, ?, ?, ?, ?, ?, ?)",
        (msg_id, thread_id, role, content, tokens_in, tokens_out, now_iso()),
    )
    conn.execute(
        "UPDATE chat_threads SET updated_at=? WHERE id=?",
        (now_iso(), thread_id),
    )
    return msg_id


async def stream_chat(
    *,
    agent_id: str,
    user_message: str,
    thread_id: str | None = None,
) -> AsyncIterator[Event]:
    """Stream an agent reply. Yields chat.token events and a final chat.done event.

    Side effects: persists both the user message and the assistant reply.
    """
    conn = get_conn()
    agent = conn.execute(
        "SELECT id, display_name, system_prompt, model, provider FROM agents WHERE id=?",
        (agent_id,),
    ).fetchone()
    if not agent:
        raise ValueError(f"Unknown agent: {agent_id}")

    with tx() as conn_tx:
        thread_id = _get_or_create_thread(conn_tx, agent_id, thread_id)
        _persist_message(conn_tx, thread_id, "user", user_message)

    history = _load_history(conn, thread_id, HISTORY_TURNS)
    system_prompt = agent["system_prompt"] or (
        f"You are {agent['display_name']}, an agent at Apulu Records."
    )
    model = agent["model"] or settings.default_chat_model

    if not settings.anthropic_api_key:
        # Graceful no-key fallback so v0 demos work without burning tokens.
        fake = (
            f"[no ANTHROPIC_API_KEY set — running in mock mode]\n\n"
            f"{agent['display_name']} would respond here. You said: {user_message!r}"
        )
        with tx() as conn_tx:
            _persist_message(conn_tx, thread_id, "assistant", fake)
        yield Event(type="chat.token", payload={"thread_id": thread_id, "agent_id": agent_id, "token": fake})
        yield Event(type="chat.done", payload={"thread_id": thread_id, "agent_id": agent_id, "mock": True})
        return

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    collected: list[str] = []

    try:
        async with client.messages.stream(
            model=model,
            max_tokens=DEFAULT_MAX_TOKENS,
            system=system_prompt,
            messages=history,
        ) as stream:
            async for text in stream.text_stream:
                if not text:
                    continue
                collected.append(text)
                yield Event(
                    type="chat.token",
                    payload={
                        "thread_id": thread_id,
                        "agent_id": agent_id,
                        "token": text,
                    },
                )
            final = await stream.get_final_message()
            usage = final.usage
    except Exception as exc:
        log.exception("chat stream failed")
        err = f"[chat error: {exc!s}]"
        collected.append(err)
        yield Event(
            type="chat.token",
            payload={"thread_id": thread_id, "agent_id": agent_id, "token": err},
        )
        usage = None

    full_text = "".join(collected)
    with tx() as conn_tx:
        _persist_message(
            conn_tx,
            thread_id,
            "assistant",
            full_text,
            tokens_in=getattr(usage, "input_tokens", None) if usage else None,
            tokens_out=getattr(usage, "output_tokens", None) if usage else None,
        )
    yield Event(
        type="chat.done",
        payload={"thread_id": thread_id, "agent_id": agent_id, "model": model},
    )


async def publish_chat(agent_id: str, user_message: str, thread_id: str | None = None) -> str:
    """Run a chat and publish every event on the global bus. Returns the thread_id."""
    bus = get_bus()
    resolved_thread = thread_id
    async for ev in stream_chat(agent_id=agent_id, user_message=user_message, thread_id=thread_id):
        resolved_thread = ev.payload.get("thread_id", resolved_thread)
        await bus.publish(ev)
    return resolved_thread or ""
