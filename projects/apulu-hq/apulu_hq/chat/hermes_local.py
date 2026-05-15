"""hermes_local adapter — speaks ACP (Agent Client Protocol) to a Hermes
subprocess.

Launches Hermes' ACP server (``python -m acp_adapter``) using Hermes' own
virtualenv, then drives it via newline-delimited JSON-RPC over stdio.

Flow:
    1. spawn subprocess
    2. send ``initialize`` (handshake)
    3. send ``session/new`` to create a session bound to the agent's cwd
    4. send ``session/prompt`` with the user message
    5. stream ``session/update`` notifications back as chat.token events
    6. yield a final chat.done event when the prompt response arrives
    7. shut down the subprocess

Why a thread + sync subprocess instead of asyncio.create_subprocess_exec:
See claude_local.py — same Windows event-loop constraint.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, AsyncIterator

from ..events import Event

log = logging.getLogger(__name__)

_EXECUTOR: ThreadPoolExecutor | None = None
_EXECUTOR_LOCK = threading.Lock()


def _get_executor() -> ThreadPoolExecutor:
    global _EXECUTOR
    with _EXECUTOR_LOCK:
        if _EXECUTOR is None:
            _EXECUTOR = ThreadPoolExecutor(
                max_workers=4, thread_name_prefix="hermes-acp"
            )
    return _EXECUTOR


def _find_hermes_python() -> Path | None:
    """Locate Hermes' Python interpreter (its venv-bundled python.exe).

    Override via env: APULU_HQ_HERMES_PYTHON.
    Default: %LOCALAPPDATA%/hermes/hermes-agent/.venv/Scripts/python.exe
    """
    override = os.environ.get("APULU_HQ_HERMES_PYTHON")
    if override:
        p = Path(override)
        if p.is_file():
            return p
    local_app = os.environ.get("LOCALAPPDATA")
    if not local_app:
        return None
    candidates = [
        Path(local_app) / "hermes" / "hermes-agent" / ".venv" / "Scripts" / "python.exe",
        Path(local_app) / "hermes" / "hermes-agent" / ".venv" / "bin" / "python",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


def _build_prompt(system_prompt: str | None, history: list[dict], user_message: str) -> str:
    """Render the conversation as a single prompt text block.

    Hermes' ACP session supports streaming a single prompt with multi-modal
    content blocks, but the simplest mapping is one text block containing
    the system prompt + history + new user message.
    """
    parts: list[str] = []
    if system_prompt:
        parts.append(f"[SYSTEM]\n{system_prompt}")
    for msg in history:
        role = (msg.get("role") or "user").upper()
        content = msg.get("content", "")
        parts.append(f"[{role}]\n{content}")
    parts.append(f"[USER]\n{user_message}")
    return "\n\n".join(parts)


async def stream_hermes_local(
    *,
    agent_id: str,
    thread_id: str,
    system_prompt: str | None,
    history: list[dict],
    user_message: str,
    model: str | None,
    cwd: str | None = None,
    timeout_seconds: float = 300.0,
) -> AsyncIterator[Event]:
    """Stream a chat completion via Hermes' ACP adapter.

    Yields:
      Event(type="chat.token", payload={..., "token": str}) for each streamed chunk
      Event(type="chat.done",  payload={..., "duration_ms": int}) at the end
    """
    hermes_py = _find_hermes_python()
    if not hermes_py:
        yield Event(
            type="chat.done",
            payload={
                "agent_id": agent_id,
                "thread_id": thread_id,
                "error": "Hermes not installed (set APULU_HQ_HERMES_PYTHON or install at %LOCALAPPDATA%/hermes/hermes-agent/.venv).",
            },
        )
        return

    hermes_root = hermes_py.parent.parent.parent  # …/hermes-agent
    prompt_text = _build_prompt(system_prompt, history, user_message)
    session_cwd = cwd or str(hermes_root)

    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[dict | None] = asyncio.Queue()
    started_at = time.monotonic()

    def _run() -> None:
        """Driver thread: spawn ACP server, do handshake, stream prompt, push
        results into the asyncio queue via loop.call_soon_threadsafe."""
        proc = subprocess.Popen(
            [str(hermes_py), "-m", "acp_adapter"],
            cwd=str(hermes_root),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1,
            env={**os.environ, "PYTHONUNBUFFERED": "1", "HERMES_QUIET": "1"},
        )
        if proc.stdin is None or proc.stdout is None:
            log.error("Hermes ACP process missing stdio pipes")
            loop.call_soon_threadsafe(queue.put_nowait, None)
            return

        pending: dict[int, dict] = {}
        next_id = [1]
        lock = threading.Lock()

        def _send(method: str, params: dict, *, is_notification: bool = False) -> int | None:
            with lock:
                if is_notification:
                    msg = {"jsonrpc": "2.0", "method": method, "params": params}
                    proc.stdin.write(json.dumps(msg) + "\n")
                    proc.stdin.flush()
                    return None
                mid = next_id[0]
                next_id[0] += 1
                pending[mid] = {"method": method, "result": None, "error": None, "done": False}
                msg = {"jsonrpc": "2.0", "id": mid, "method": method, "params": params}
                proc.stdin.write(json.dumps(msg) + "\n")
                proc.stdin.flush()
                return mid

        def _wait(mid: int, timeout: float) -> dict:
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                state = pending.get(mid, {})
                if state.get("done"):
                    if state.get("error"):
                        raise RuntimeError(f"ACP error: {state['error']}")
                    return state.get("result") or {}
                time.sleep(0.01)
            raise TimeoutError(f"Timed out waiting for response to message id={mid}")

        def _reader() -> None:
            for line in proc.stdout:
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue
                # Response to a request we sent
                if "id" in msg and ("result" in msg or "error" in msg):
                    state = pending.get(msg["id"])
                    if state is not None:
                        state["result"] = msg.get("result")
                        state["error"] = msg.get("error")
                        state["done"] = True
                    continue
                # Notification from server
                method = msg.get("method") or ""
                if method == "session/update":
                    params = msg.get("params") or {}
                    update = params.get("update") or {}
                    kind = update.get("sessionUpdate") or ""
                    content = update.get("content") or {}
                    text = ""
                    if isinstance(content, dict):
                        text = str(content.get("text") or "")
                    if kind == "agent_message_chunk" and text:
                        loop.call_soon_threadsafe(
                            queue.put_nowait,
                            {"type": "token", "text": text},
                        )
                    continue
                # Server requests we just stub politely
                if "id" in msg and "method" in msg:
                    mid = msg.get("id")
                    response = {
                        "jsonrpc": "2.0",
                        "id": mid,
                        "result": {"outcome": "cancelled"},
                    }
                    try:
                        with lock:
                            proc.stdin.write(json.dumps(response) + "\n")
                            proc.stdin.flush()
                    except Exception:
                        pass

        reader = threading.Thread(target=_reader, daemon=True)
        reader.start()

        def _stderr_reader() -> None:
            if proc.stderr is None:
                return
            for line in proc.stderr:
                line = line.rstrip()
                if line:
                    log.warning("hermes-stderr: %s", line)
        stderr_thread = threading.Thread(target=_stderr_reader, daemon=True)
        stderr_thread.start()

        try:
            # 1. initialize
            init_id = _send(
                "initialize",
                {
                    "protocolVersion": 1,
                    "clientCapabilities": {"fs": {"readTextFile": True, "writeTextFile": True}},
                    "clientInfo": {"name": "apulu-hq", "title": "Apulu HQ", "version": "0.1.0"},
                },
            )
            _wait(init_id, timeout=20)

            # 2. session/new
            sess_id = _send("session/new", {"cwd": session_cwd, "mcpServers": []})
            session = _wait(sess_id, timeout=30)
            session_id = str(session.get("sessionId") or "").strip()
            if not session_id:
                raise RuntimeError("Hermes did not return a sessionId")

            # 3. session/prompt — streams chunks via session/update notifications
            prompt_id = _send(
                "session/prompt",
                {
                    "sessionId": session_id,
                    "prompt": [{"type": "text", "text": prompt_text}],
                },
            )
            _wait(prompt_id, timeout=timeout_seconds)
        except Exception as exc:
            log.exception("Hermes ACP driver failed")
            loop.call_soon_threadsafe(
                queue.put_nowait,
                {"type": "error", "message": str(exc)},
            )
        finally:
            try:
                proc.stdin.close()
            except Exception:
                pass
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
            loop.call_soon_threadsafe(queue.put_nowait, None)  # signal end

    # Run the driver in a worker thread; let it push events into the queue
    future = loop.run_in_executor(_get_executor(), _run)
    try:
        while True:
            item = await queue.get()
            if item is None:
                break
            if item["type"] == "token":
                yield Event(
                    type="chat.token",
                    payload={
                        "agent_id": agent_id,
                        "thread_id": thread_id,
                        "token": item["text"],
                    },
                )
            elif item["type"] == "error":
                yield Event(
                    type="chat.done",
                    payload={
                        "agent_id": agent_id,
                        "thread_id": thread_id,
                        "error": item["message"],
                    },
                )
                return
    finally:
        try:
            await future  # let the driver finish cleanly
        except Exception:
            pass

    yield Event(
        type="chat.done",
        payload={
            "agent_id": agent_id,
            "thread_id": thread_id,
            "duration_ms": int((time.monotonic() - started_at) * 1000),
        },
    )
