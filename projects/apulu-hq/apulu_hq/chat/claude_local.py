"""claude_local adapter — subprocess to the `claude` CLI, OAuth via Claude Pro/Max
subscription (no API key needed).

Uses `claude -p --print --output-format stream-json` and parses the NDJSON
output stream. Yields chat.token events as content_block_delta arrives,
then a chat.done event with cost + duration metadata from the result line.

Why a thread + sync subprocess instead of asyncio.create_subprocess_exec:
On Windows, uvicorn's `--reload` mode runs the app under the
`SelectorEventLoop`, which does NOT support `subprocess_exec` (raises
NotImplementedError). Only `ProactorEventLoop` does. Rather than fight
the event-loop policy across dev/prod/test environments, we use plain
`subprocess.Popen` in a worker thread and bridge stdout lines back into
the asyncio loop via `run_in_executor` + an asyncio.Queue. This works
on every loop type, on every OS, and gives us the same streaming UX.

Notes:
- `apiKeySource: "none"` in the init event confirms OAuth/subscription auth.
- `total_cost_usd` is the metered equivalent — covered by subscription, not billed.
- We use `--no-session-persistence` so each call is clean. History is
  passed inline in the rendered prompt.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import AsyncIterator

from ..events import Event

log = logging.getLogger(__name__)

# Shared executor so we don't spin up a new thread pool per call.
_EXECUTOR: ThreadPoolExecutor | None = None
_EXECUTOR_LOCK = threading.Lock()


def _get_executor() -> ThreadPoolExecutor:
    global _EXECUTOR
    with _EXECUTOR_LOCK:
        if _EXECUTOR is None:
            _EXECUTOR = ThreadPoolExecutor(
                max_workers=4, thread_name_prefix="claude-cli"
            )
    return _EXECUTOR


def _find_claude_cli() -> str | None:
    """Locate the claude executable, accounting for Windows npm-wrapper shims."""
    override = os.environ.get("APULU_HQ_CLAUDE_BIN")
    if override:
        return override
    appdata = os.environ.get("APPDATA")
    if appdata:
        for name in ("claude.cmd", "claude.ps1", "claude.bat", "claude"):
            p = os.path.join(appdata, "npm", name)
            if os.path.isfile(p):
                return p
    return shutil.which("claude")


def _build_prompt(system_prompt: str | None, history: list[dict], user_message: str) -> str:
    """Render history as a single text prompt block. The CLI's
    --append-system-prompt handles the persona; the prompt body is the
    multi-turn conversation."""
    lines: list[str] = []
    for msg in history:
        role = msg.get("role", "user").upper()
        content = msg.get("content", "")
        lines.append(f"[{role}]\n{content}")
    lines.append(f"[USER]\n{user_message}")
    return "\n\n".join(lines)


# Sentinel objects pushed onto the queue from the worker thread.
_STDOUT_LINE = "line"
_PROC_DONE = "done"
_PROC_ERROR = "error"


def _run_claude_blocking(
    *,
    bin_path: str,
    args: list[str],
    prompt: str,
    loop: asyncio.AbstractEventLoop,
    queue: asyncio.Queue,
) -> None:
    """Worker thread: spawn the CLI synchronously and stream stdout lines
    back into the asyncio queue on the caller's loop."""
    try:
        proc = subprocess.Popen(
            [bin_path] + args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            # On Windows, .cmd shims need shell=False but we let Popen handle
            # the .cmd suffix correctly via direct exec. Confirmed working
            # with %APPDATA%\npm\claude.cmd.
        )

        # Write the prompt and close stdin so the CLI proceeds.
        assert proc.stdin is not None
        proc.stdin.write(prompt)
        proc.stdin.close()

        # Read stderr concurrently so we don't deadlock on a full pipe.
        stderr_chunks: list[str] = []

        def _drain_stderr():
            assert proc.stderr is not None
            for chunk in proc.stderr:
                stderr_chunks.append(chunk)

        stderr_thread = threading.Thread(target=_drain_stderr, daemon=True)
        stderr_thread.start()

        assert proc.stdout is not None
        for line in proc.stdout:
            line = line.rstrip("\r\n")
            if not line:
                continue
            asyncio.run_coroutine_threadsafe(
                queue.put((_STDOUT_LINE, line)), loop
            )

        return_code = proc.wait()
        stderr_thread.join(timeout=2)
        stderr_text = "".join(stderr_chunks)
        asyncio.run_coroutine_threadsafe(
            queue.put((_PROC_DONE, {"rc": return_code, "stderr": stderr_text})),
            loop,
        )
    except Exception as exc:
        log.exception("claude CLI worker thread failed")
        asyncio.run_coroutine_threadsafe(
            queue.put((_PROC_ERROR, repr(exc))), loop
        )


async def stream_claude_local(
    *,
    agent_id: str,
    thread_id: str,
    user_message: str,
    history: list[dict],
    system_prompt: str | None,
    model: str | None = None,
) -> AsyncIterator[Event]:
    """Stream a reply from the claude CLI via a worker thread.

    Yields chat.token events as tokens stream in, then a chat.done event
    with cost/duration/usage metadata.

    Raises FileNotFoundError if the `claude` CLI isn't found.
    """
    bin_path = _find_claude_cli()
    if not bin_path:
        raise FileNotFoundError(
            "claude CLI not found. Install Claude Code "
            "(npm i -g @anthropic-ai/claude-code) or set APULU_HQ_CLAUDE_BIN."
        )

    args = [
        "-p",
        "--print",
        "--output-format", "stream-json",
        "--include-partial-messages",
        "--verbose",
        "--no-session-persistence",
        "--disable-slash-commands",
        "--permission-mode", "auto",
    ]
    if system_prompt:
        args += ["--append-system-prompt", system_prompt]
    if model:
        args += ["--model", model]

    prompt = _build_prompt(system_prompt, history, user_message)

    log.info(
        "[claude_local] spawn agent=%s thread=%s msg_chars=%d hist=%d model=%s",
        agent_id, thread_id, len(user_message), len(history), model or "default",
    )

    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()
    executor = _get_executor()

    # Kick off the worker. Don't await — we drain the queue while it runs.
    worker_future = loop.run_in_executor(
        executor,
        lambda: _run_claude_blocking(
            bin_path=bin_path,
            args=args,
            prompt=prompt,
            loop=loop,
            queue=queue,
        ),
    )

    final_text: list[str] = []
    cost_usd: float | None = None
    duration_ms: int | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    model_used: str | None = model
    errored = False
    return_code: int | None = None
    stderr_text = ""

    try:
        while True:
            kind, payload = await queue.get()

            if kind == _STDOUT_LINE:
                try:
                    ev = json.loads(payload)
                except json.JSONDecodeError:
                    continue
                ev_type = ev.get("type")
                if ev_type == "stream_event":
                    inner = ev.get("event", {})
                    if inner.get("type") == "content_block_delta":
                        delta = inner.get("delta", {})
                        text = delta.get("text")
                        if text:
                            final_text.append(text)
                            yield Event(
                                type="chat.token",
                                payload={
                                    "thread_id": thread_id,
                                    "agent_id": agent_id,
                                    "token": text,
                                },
                            )
                elif ev_type == "system" and ev.get("subtype") == "init":
                    model_used = ev.get("model") or model_used
                elif ev_type == "result":
                    cost_usd = ev.get("total_cost_usd")
                    duration_ms = ev.get("duration_ms")
                    usage = ev.get("usage") or {}
                    input_tokens = usage.get("input_tokens")
                    output_tokens = usage.get("output_tokens")
                    if ev.get("is_error"):
                        errored = True
                        err_msg = ev.get("result") or "claude CLI returned an error"
                        final_text.append(f"\n[claude error: {err_msg}]")
                        yield Event(
                            type="chat.token",
                            payload={
                                "thread_id": thread_id,
                                "agent_id": agent_id,
                                "token": f"\n[claude error: {err_msg}]",
                            },
                        )

            elif kind == _PROC_DONE:
                return_code = payload.get("rc")
                stderr_text = payload.get("stderr", "")
                break

            elif kind == _PROC_ERROR:
                errored = True
                err = f"[claude_local worker error: {payload}]"
                final_text.append(err)
                yield Event(
                    type="chat.token",
                    payload={"thread_id": thread_id, "agent_id": agent_id, "token": err},
                )
                break
    finally:
        # Make sure the worker thread has actually exited.
        try:
            await worker_future
        except Exception:
            log.exception("claude worker future raised")

    if return_code not in (None, 0) and not any("chat.token" in t for t in final_text):
        msg = f"[claude CLI exit {return_code}]"
        if stderr_text:
            msg += f"\n{stderr_text.strip()[:500]}"
        yield Event(
            type="chat.token",
            payload={"thread_id": thread_id, "agent_id": agent_id, "token": msg},
        )
        final_text.append(msg)
        errored = True

    yield Event(
        type="chat.done",
        payload={
            "thread_id": thread_id,
            "agent_id": agent_id,
            "model": model_used,
            "cost_usd": cost_usd,
            "duration_ms": duration_ms,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "subscription": True,
            "errored": errored,
            "exit_code": return_code,
        },
    )
