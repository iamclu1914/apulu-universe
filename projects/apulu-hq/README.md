# Apulu HQ

Self-hosted, interactive desktop app that replaces Paperclip as the orchestration layer for Apulu Records.

**Spec:** [`docs/superpowers/specs/2026-05-13-apulu-hq-design.md`](../../docs/superpowers/specs/2026-05-13-apulu-hq-design.md)

## Status

- ✅ **Phase 0** — Spec + scaffolding + SQLite schema + importer
- 🚧 **Phase 1** — Backend MVP (observe-only)
- ⏳ **Phase 2** — Tauri shell + chat-with-agents
- ⏳ **Phase 3+** — Routine cutover, Phaser HQ map

Apulu HQ runs **alongside** Paperclip until each routine has been cut over individually and soaked for 3+ days. Nothing in `scripts/paperclip/`, `pipeline/`, or live state files is modified by this codebase.

## Layout

```
projects/apulu-hq/
├── README.md                 (this file)
├── pyproject.toml            Python deps (FastAPI, APScheduler, anthropic, etc.)
├── apulu_hq/
│   ├── __init__.py
│   ├── config.py             paths, env vars, ports
│   ├── db.py                 SQLite connection + schema + migrations
│   ├── models.py             dataclasses for Agent / Routine / Dispatch / DLQ
│   ├── events/
│   │   ├── bus.py            in-process pub/sub
│   │   └── schema.py         versioned WS event types (Pydantic)
│   ├── chat/
│   │   ├── router.py         per-agent threads, streaming via Anthropic
│   │   └── personas.py       default system prompts seeded into DB
│   ├── api/
│   │   ├── app.py            FastAPI app factory
│   │   ├── agents.py         /api/agents
│   │   ├── routines.py       /api/routines
│   │   ├── dispatches.py     /api/dispatches, /api/dlq
│   │   ├── chat.py           /api/agents/{id}/chat
│   │   ├── health.py         /api/health
│   │   └── ws.py             /ws (WebSocket gateway)
│   └── importer.py           one-shot Paperclip → SQLite migration
├── scripts/
│   ├── init_db.py            create empty hq.db with schema
│   ├── import_from_paperclip.py
│   └── run_dev.py            uvicorn launcher with reload
├── webclient/
│   └── index.html            zero-dep test UI (chat + WS event ticker)
└── tests/
    ├── test_schema.py
    ├── test_importer.py
    └── test_api_smoke.py
```

## Quick start (Phase 1, no Tauri shell yet)

```bash
cd projects/apulu-hq
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -e .

# Initialise an empty database
python scripts/init_db.py

# Import the 16 agents and 26 routines from Paperclip JSON
python scripts/import_from_paperclip.py

# Run the backend (defaults to 127.0.0.1:8741)
python scripts/run_dev.py

# Test UI: open webclient/index.html in any browser
```

Set `ANTHROPIC_API_KEY` in `%LOCALAPPDATA%\apulu-hq\secrets.env` or as a shell env var to enable chat.

## Desktop shell (no terminal, auto-start at boot)

Replaces the dev-loop above with a real Windows desktop window (pywebview +
Windows 11's built-in WebView2) and a system tray icon. Backend runs as a
hidden child process — no console window ever appears.

```powershell
# One-time setup
cd projects/apulu-hq
.\.venv\Scripts\Activate.ps1
pip install -e ".[desktop]"

# Install auto-start at user login
.\install_startup.ps1 install

# Or just launch it once without rebooting
.\install_startup.ps1 launch
```

The shell:
- Opens a 1440×900 native window pointing at the UI
- System tray icon: Show / Open in browser / Restart backend / Quit
- Closing the window minimizes to tray (does not quit)
- Survives reboots; starts on next user login
- Logs to `%LOCALAPPDATA%\apulu-hq\logs\shell.log`

Uninstall: `.\install_startup.ps1 uninstall`. Status: `.\install_startup.ps1 status`.

## What v0 does

- Seeds SQLite with all 16 agents and 26 routines (IDs preserved from Paperclip)
- Exposes `/api/agents`, `/api/routines`, `/api/health`, `/ws`
- Streaming chat with any agent via Anthropic (chat history persisted)
- WebSocket event ticker (currently emits heartbeat + chat events; dispatch events arrive in Phase 3)

## What v0 does NOT do yet

- Fire routines (scheduler is loaded with all routines `enabled=0` — observe-only)
- Render the Phaser HQ map (Phase 6)
- Replace Paperclip in production — Paperclip keeps running as-is
