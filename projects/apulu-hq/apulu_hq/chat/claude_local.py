"""claude_local adapter — subprocess to the `claude` CLI, OAuth via Claude Pro/Max
subscription (no API key needed).

Uses `claude -p --print --output-format stream-json` and parses the NDJSON
output stream. Yields chat.token events as content_block_delta arrives,
then a chat.done event with cost + duration metadata from the result line.

Notes:
- `apiKeySource: "none"` in the init event confirms OAuth/subscription auth.
- `total_cost_usd` is the metered equivalent — covered by subscription, not billed.
- We deliberately do NOT use `--bare`: that mode disables OAuth and demands
  ANTHROPIC_API_KEY. We pay a small startup cost (~2-4s for hooks/init)
  but get to use the subscription.
- We use `--no-session-persistence` for clean per-message invocations.
  History is passed inline in the prompt (rebuilt from SQLite each call).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
from typing import AsyncIterator

from ..events import Event

log = logging.getLogger(__name__)


def _find_claude_cli() -> str | None:
    """Locate the claude executable, accounting for Windows npm-wrapper shims."""
    override = os.environ.get("APULU_HQ_CLAUDE_BIN")
    if override:
        return override
    # Common Windows location: %APPDATA%\npm\claude.cmd
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
    # System prompt is passed via flag, not in the body.
    for msg in history:
        role = msg.get("role", "user").upper()
        content = msg.get("content", "")
        lines.append(f"[{role}]\n{content}")
    lines.append(f"[USER]\n{user_message}")
    return "\n\n".join(lines)


async def stream_claude_local(
    *,
    agent_id: str,
    thread_id: str,
    user_message: str,
    history: list[dict],
    system_prompt: str | None,
    model: str | None = None,
) -> AsyncIterator[Event]:
    """Stream a reply from the claude CLI. Yields chat.token + chat.done events.

    Raises FileNotFoundError if the `claude` CLI isn't found.
    """
    bin_path = _find_claude_cli()
    if not bin_path:
        raise FileNotFoundError(
            "claude CLI not found. Install Claude Code "
            "(npm i -g @anthropic-ai/claude-code) or set APULU_HQ_CLAUDE_BIN."
        )

    args = [
        bin_path,
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

    log.info("[claude_local] spawn agent=%s thread=%s msg_chars=%d hist=%d model=%s",
             agent_id, thread_id, len(user_message), len(history), model or "default")

    proc = await asyncio.create_subprocess_exec(
        *args,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    # Write the prompt and close stdin so the CLI proceeds.
    assert proc.stdin is not None
    proc.stdin.write(prompt.encode("utf-8"))
    await proc.stdin.drain()
    proc.stdin.close()

    assert proc.stdout is not None
    final_text: list[str] = []
    cost_usd: float | None = None
    duration_ms: int | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    model_used: str | None = model
    errored = False

    async def _read_stderr() -> str:
        assert proc.stderr is not None
        chunks: list[bytes] = []
        async for line in proc.stderr:
            chunks.append(line)
        return b"".join(chunks).decode("utf-8", errors="replace")

    stderr_task = asyncio.create_task(_read_stderr())

    try:
        async for raw in proc.stdout:
            line = raw.decode("utf-8", errors="replace").strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
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
                # Capture which model the CLI actually used.
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
    finally:
        return_code = await proc.wait()
        stderr_text = await stderr_task

    if return_code != 0 and not final_text:
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
            "subscription": True,  # OAuth/subscription billing — no actual charge
            "errored": errored,
            "exit_code": return_code,
        },
    )
