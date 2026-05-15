# Apulu HQ — Interactive Label Operations App Design Spec

**Date**: 2026-05-13
**Status**: Draft
**Author**: Claude + rdyal
**Replaces (eventually)**: [2026-04-09-apulu-records-paperclip-design.md](2026-04-09-apulu-records-paperclip-design.md)

---

## 1. Overview

Apulu HQ is a self-hosted desktop application that replaces Paperclip as the orchestration layer for Apulu Records. Where Paperclip is a generic, headless, dashboard-style platform, Apulu HQ is a purpose-built, interactive operations app that renders the label as a navigable 2D office. The user — operating as CEO + Creative Director — sees agents as avatars moving through departments, can click any agent to open a streaming chat panel, watches dispatch outcomes animate in real time, and physically walks the floor when desired.

The app is local-first, runs 24/7 with no terminal windows, auto-starts at boot, and survives reboots — matching the operator's stated environment constraints. All 16 existing agents, 26 scheduled routines, and the full bulletproofing stack (retry wrapper, circuit breaker, DLQ, signature detection, status dashboard) are preserved end-to-end. Paperclip is replaced; the agents and pipelines that run beneath it are not.

### Why Replace Paperclip

- The recurring `dev:watch` hang causes silent outages requiring an embedded-postgres wipe to recover (last incidents 2026-04-20, 2026-04-25). Root cause is unidentified.
- Paperclip's startup chain (`pnpm` → `tsx` → embedded `postgres`) introduces dependency drift and orphan-process risk on Windows that has cost multiple late-night recoveries.
- The Paperclip UI is not designed for direct CEO-to-agent interaction. Talking to an agent today means opening Claude CLI, pasting context, and copying output back. There is no first-class chat surface.
- Paperclip's value-add — company/department model, budgeting, dispatcher — is implementable in a few thousand lines of Python that the operator fully owns and can debug.

### Why Make It Interactive

- Situational awareness: a moving, color-coded map communicates "what's the label doing right now?" faster than `STATUS.md` ever can.
- CEO ergonomics: clicking Rex to ask about Vawn's health is the natural gesture; opening a terminal is not.
- Identity: each agent is a character with a name, voice, and station. The HQ metaphor reinforces that the label is a *team*, not a dashboard.
- Extensibility: adding artist 2 becomes "add a second floor" — a concrete, visualizable operation.

### Non-Goals

- This is not a public-facing product. Single-operator app, runs locally, no auth layer in v1.
- This is not a game. The avatars and map serve operations; idle behavior is decorative but every interaction maps to a real backend action.
- This is not a multiplayer/shared workspace. Multi-tenant means multi-artist, not multi-user.

---

## 2. Architecture

### Three-Layer Model

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1: PRESENTATION  (Tauri desktop shell)               │
│    • React chrome: chat panel, briefing, DLQ tray, settings │
│    • Phaser 3 scene: top-down HQ map, agent avatars, CEO    │
│    • WebSocket client: subscribes to backend event stream   │
│    • Local-only: no auth, single operator                   │
└─────────────────────────────────────────────────────────────┘
                          ▲ WebSocket (real-time events)
                          ▲ REST (commands, history, config)
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 2: ORCHESTRATION  (FastAPI + APScheduler, Python)    │
│    • Agent registry        (replaces agent_ids.json)        │
│    • Routine scheduler     (replaces Paperclip routines)    │
│    • Dispatcher + retry    (port of dispatch_runner.py)     │
│    • Circuit breaker       (port of breaker logic)          │
│    • Signature detection   (port of 8 known patterns)       │
│    • DLQ + alert fallback  (port of jsonl writers)          │
│    • Chat router           (per-agent threads, streaming)   │
│    • Event bus             (in-process pub/sub → WS fanout) │
│    • SQLite database       (single file, no embedded pg)    │
└─────────────────────────────────────────────────────────────┘
                          ▲ subprocess / SDK calls
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 3: AGENTS  (unchanged from Paperclip-era)            │
│    • claude_local adapter → Claude CLI subprocess           │
│    • process adapter      → post_vawn.py, marketing_*.py    │
│    • api adapter (new)    → Anthropic/OpenAI/Ollama direct  │
│    • All existing scripts in pipeline/ remain untouched     │
└─────────────────────────────────────────────────────────────┘
```

### Component Choices and Rationale

| Component | Choice | Rationale |
|---|---|---|
| Desktop shell | **Tauri 2** | 5–10 MB single `.exe`, native window, no terminal, integrates with Windows startup folder. Avoids Electron bloat. |
| UI framework | **React 18 + TypeScript** | Standard, well-known to assistants and tooling. |
| Map / avatars | **Phaser 3** (embedded in React) | Mature 2D engine, top-down tilemap support, sprite animation, free, MIT. |
| Backend | **FastAPI** (Python 3.11+) | Same language as all existing pipelines. First-class async + WebSocket. |
| Scheduler | **APScheduler** | Cron-style triggers, persistent jobstore, in-process — no embedded postgres. |
| Database | **SQLite** (WAL mode) | Single-file, no startup hang failure mode. Migrate to Postgres only if multi-tenant ever requires it. |
| Real-time | **WebSocket** (FastAPI native) | One persistent connection per app instance pushes all events. |
| LLM SDK | **Anthropic SDK** + per-agent config | Each agent record stores `{provider, model, system_prompt}` — model choice decoupled from agent identity. |
| Process supervision | **Tauri sidecar** for backend + **Windows Task Scheduler** for monitors | Tauri launches FastAPI as a sidecar process; existing WTS tasks (`PaperclipRunMonitor`, `BackendHealthProbe`, `StatusBoard`) keep running. |

### What Stays From the Paperclip Era

- All 16 agents and their IDs (preserved verbatim in the new SQLite registry — see Section 5).
- All 26 routine names and schedules (preserved as APScheduler jobs).
- `post_vawn.py`, `marketing_dispatch.py`, every script under `pipeline/`.
- The five-layer bulletproofing stack — circuit breaker, retry wrapper, signature detection, DLQ, alert fallback — ported file-for-file.
- All Windows Task Scheduler monitors: `PaperclipRunMonitor` (renamed `HQRunMonitor`), `BackendHealthProbe`, `ValidateAdapters`, `StatusBoard`.
- All live state files: `STATUS.md`, `backend_health.json`, `claude_auth_state.json`, `dispatch_log.jsonl`, `dead_letter.jsonl`, `alert_fallback.jsonl`, `posting_liveness.json`.
- Two currently disabled routines (`lyric-card`, `video-cinematic`) stay disabled until catalog reseed.

### What Goes Away

- `dev:watch` startup chain, embedded postgres, `tsx`, `cross-env`, `pnpm dev`.
- The `start-paperclip.bat` / `run_paperclip_watchdog.cmd` recovery dance.
- Paperclip's company/agent/routine config files (data migrated into SQLite).
- The orphan-process pileup failure mode entirely.

---

## 3. Layer 1 — Presentation

### Tauri Shell

- One window, defaults to 1440×900, resizable, remembers last position/size.
- Title: "Apulu HQ".
- System tray icon with: Show/Hide, Pause All Routines, Resume All, Quit.
- Auto-starts via Windows shell:startup link installed by `apulu-hq-installer.exe`. No terminal window.
- Tauri sidecar launches the FastAPI backend on `127.0.0.1:8741` (random-ish port to avoid collisions). Backend lifetime is tied to the shell unless `--daemon` mode is used (see Section 9).

### React Chrome

Layout (single window, three regions):

```
┌─────────────────────────────────────────────────────────────────┐
│  Top bar: HQ title · current artist · health pill · clock       │
├─────────────────────────────────────────────────────────────────┤
│                                       │                         │
│                                       │   Right rail (320 px)   │
│                                       │   ─────────────────     │
│        Phaser canvas                  │   Chat panel            │
│        (the HQ map)                   │   (or briefing,         │
│                                       │    or DLQ tray,         │
│                                       │    or event ticker)     │
│                                       │                         │
│                                       │                         │
├─────────────────────────────────────────────────────────────────┤
│  Bottom bar: event ticker (last 5 events, click to expand)      │
└─────────────────────────────────────────────────────────────────┘
```

Right-rail tabs: **Chat · Briefing · DLQ · Events · Settings**.

- **Chat**: when an agent is selected, this tab shows the conversation. Streaming token-by-token. Conversation history persisted per-agent in SQLite. Markdown rendering. Code blocks with copy button.
- **Briefing**: today's daily briefing rendered inline (markdown). Generated by Nelly (CoS) at 06:00 ET — same logic as today.
- **DLQ**: list of dead-letter items. Each row shows routine, agent, last error signature, timestamps, and Replay / Discard buttons.
- **Events**: rolling event log with filters (severity, agent, type).
- **Settings**: agent configs (model, provider, system prompt), routine enable/disable, theme.

### Phaser Scene — "The HQ Floor"

One scene, one tilemap, ~2048×1536 world rendered into a ~1100×800 canvas with camera pan. Author the map in [Tiled](https://www.mapeditor.org/) (free, exports JSON Phaser reads natively).

**Floor plan (v1, single floor):**

```
┌──────────────────────────────────────────────────────────────────┐
│   CEO OFFICE (corner)                              ROOFTOP DECK  │
│   [Clu's desk]                                     [coffee, art] │
│                                                                  │
│   ─── glass partition ───                                        │
│                                                                  │
│   COS CORNER       │  MARKETING BULLPEN (5 desks)                │
│   [Nelly's desk]   │  [Sage & Khari · Dex · Nova · Vibe · Echo]  │
│   [briefing wall]  │                                             │
│                    │  ─── partition ───                          │
│                    │                                             │
│   RESEARCH LAB     │  PRODUCTION BOOTH                           │
│   (5 desks)        │  [Cole · Oaklyn · Aspyn]                    │
│   [Rex · Camdyn ·  │                                             │
│    Sable · Onyx ·  │  POST-PROD ROOM                             │
│    Cipher]         │  [Rhythm + QC station]                      │
│                    │                                             │
│   ─── hallway ───                                                │
│                                                                  │
│   COMMON AREA: couches, water cooler, incident board, DLQ bin    │
└──────────────────────────────────────────────────────────────────┘
```

Exact desk assignments derived from the agent registry; the table above is illustrative.

**Sprites:**
- 16 agent characters, 32×32 px, 4-directional walk cycles (down/up/left/right, 4 frames each).
- 1 CEO character (Clu).
- Recommended starter pack: **LimeZu — Modern Interiors** (commercial-friendly, ~$15) for furniture/tiles, generated portraits or LPC base for character bases. Final art can be AI-generated and swapped in without touching scene logic.

**Agent state machine (Phaser, per-sprite):**

```
                ┌──────────┐
       ┌──────► │   IDLE   │ ─────────┐
       │        └─────┬────┘          │
       │              ▼               ▼
       │        ┌──────────┐    ┌──────────┐
       │        │ WALKING  │    │ CHATTING │
       │        └─────┬────┘    └─────┬────┘
       │              ▼               │
       │        ┌──────────┐          │
       │        │ WORKING  │          │
       │        └─────┬────┘          │
       │              ▼               │
       │        ┌──────────┐          │
       └─────── │  ERROR   │ ◄────────┘
                └──────────┘
```

- `IDLE`: random wander within own department, dwell at desk for N seconds, repeat.
- `WALKING`: pathfind to target tile via simple A* on the tilemap.
- `WORKING`: seated at own desk, "typing" particle effect; entered when backend emits `routine.started` for this agent.
- `CHATTING`: seated at own desk, facing the CEO; entered when this agent is selected in the chat panel.
- `ERROR`: sprite tinted red, "!" floater above head; entered on `dispatch.failed`. Exits after 30s or on next `dispatch.success`.

**Status floaters:**
- Small icon above each sprite reflects current backend state:
  - 💼 idle / available
  - ⚙️ working (routine in flight)
  - 💬 chatting with CEO
  - ⚠️ recent failure
  - 🚫 disabled / paused
  - 💤 disabled by config (e.g. lyric-card right now)

**Decorative event animations:**
- `dispatch.success` → small ✅ pops over agent head, +1 in event ticker.
- `dispatch.failed` → red flash + "!" floater, paper sprite drops on the floor near the DLQ bin.
- `dlq.replay_succeeded` → paper sprite floats up and disappears.
- `claude_auth_expired` → *every* `claude_local` agent freezes in place with a lock icon for as long as the signature is active.
- `briefing.ready` → Nelly walks to the briefing wall, "posts" a note.

**CEO interaction:**
- Click any agent → camera centers on them, chat panel opens, agent enters `CHATTING`.
- Optional click-to-walk for the CEO sprite. Proximity (≤3 tiles) auto-opens that agent's chat.
- Keyboard: `Esc` closes chat, `Tab` cycles agents, `Ctrl+K` opens command palette (jump to agent by name).

### Performance Budget

- Phaser scene: 60 fps target, 30 fps acceptable. 17 sprites + tilemap + particles is well within budget on any modern Windows machine.
- WebSocket: ≤10 events/sec under normal operation; spikes during dispatch storms should still feel smooth (debounce floater animations).
- Backend → UI latency for status changes: target <200 ms.

---

## 4. Layer 2 — Orchestration Backend

### Process Model

- Single FastAPI process, ASGI (`uvicorn`).
- Three internal subsystems sharing the asyncio loop:
  1. **HTTP API** — REST endpoints for config, history, manual commands.
  2. **WebSocket gateway** — `/ws` endpoint, one connection per Tauri shell instance.
  3. **Scheduler** — APScheduler with SQLAlchemyJobStore pointing at the same SQLite file.
- Long-running dispatches (Claude CLI subprocess can take minutes) execute in a `ProcessPoolExecutor` so they don't block the event loop.

### REST API (v1)

```
GET    /api/agents                       → list all agents + state
GET    /api/agents/{id}                  → one agent
PATCH  /api/agents/{id}                  → update model/provider/prompt
POST   /api/agents/{id}/chat             → send a chat message (streams via WS)

GET    /api/routines                     → list all routines
PATCH  /api/routines/{id}                → enable/disable, change schedule
POST   /api/routines/{id}/run            → fire now (manual trigger)

GET    /api/dispatches?limit=100         → recent dispatch history
GET    /api/dlq                          → dead-letter queue contents
POST   /api/dlq/{id}/replay              → replay a DLQ entry
DELETE /api/dlq/{id}                     → discard a DLQ entry

GET    /api/briefing/today               → today's daily briefing markdown
GET    /api/health                       → aggregated health snapshot

WS     /ws                               → real-time event stream
```

### WebSocket Event Contract

All events are JSON with shape `{type, ts, payload}`. The contract is the *only* coupling between backend and UI animation logic.

| Type | Payload | UI Reaction |
|---|---|---|
| `agent.state_changed` | `{agent_id, from, to, reason}` | Sprite transitions state machine |
| `agent.status_changed` | `{agent_id, status, signature?}` | Update floater icon |
| `routine.started` | `{routine_id, agent_id, dispatch_id}` | Sprite walks to desk, enters WORKING |
| `routine.succeeded` | `{routine_id, agent_id, dispatch_id, duration_ms}` | ✅ pop, ticker line |
| `routine.failed` | `{routine_id, agent_id, dispatch_id, signature, retry_count}` | Red flash, "!" floater, paper drop |
| `dispatch.retry_scheduled` | `{dispatch_id, attempt, delay_s}` | Ticker line "retrying in 30s" |
| `breaker.tripped` | `{component, reason}` | Banner at top of UI |
| `breaker.cleared` | `{component}` | Banner clears |
| `dlq.appended` | `{entry_id, routine_id, signature}` | Paper sprite stays on floor |
| `dlq.replayed` | `{entry_id, outcome}` | Paper sprite floats up |
| `chat.token` | `{thread_id, token}` | Append to active chat stream |
| `chat.done` | `{thread_id}` | Finalize message |
| `briefing.ready` | `{date, path}` | Nelly walks to wall animation |
| `health.snapshot` | `{components: {...}}` | Top-bar health pill updates |

The contract is versioned in `apulu_hq/events/schema.py` and validated with Pydantic. Adding fields is backward-compatible; renaming requires a version bump.

### Dispatcher (Direct Port from Paperclip Era)

`apulu_hq/dispatch/runner.py` is a near-verbatim port of the existing `dispatch_runner.run_with_retries`:

- 3 attempts with exponential backoff: 30s, 2m, 8m.
- Short-circuit on exit code 2 (config error) — no retry, immediate DLQ.
- Short-circuit on exit code 3 (circuit breaker open) — no retry, schedule re-check after breaker window.
- Signature detection runs stderr against the 8 known patterns from the runbook (`claude_auth_expired`, `apulu_backend_5xx`, `missing_cron_arg`, `bluesky_auth_failed`, `smtp_rejected`, `postgres_connection_refused`, `claude_quota_exhausted`, `disk_full`).
- Every attempt appends to `dispatch_log.jsonl` (same file as today, format preserved).
- Permanent failures append to `dead_letter.jsonl` (same file as today, format preserved).
- Each transition emits the corresponding WS event so the UI animates correctly.

### Circuit Breaker

`apulu_hq/dispatch/breaker.py` reads `backend_health.json` (unchanged path, unchanged producer — `BackendHealthProbe` WTS task). Agents that touch the Apulu Studio backend (`post_vawn.py`, anything calling `/api/posts/upload`) consult the breaker before burning Suno tokens. Exit 3 if `degraded` is true and snapshot is <30 minutes old.

### Chat Router

Per-agent chat threads. Each thread:
- `thread_id` UUID, owned by agent_id.
- Messages stored in SQLite (`chat_messages` table).
- On send: build context = system prompt + agent persona + last N messages + optional pinned context from the wiki.
- Streams tokens via `chat.token` WS events.
- Token usage logged per message; daily and monthly totals visible in Settings.

The agent persona is editable per-agent in Settings → Agents → [Name] → System Prompt. Defaults seeded from the Paperclip-era `update_all_instructions.py` output.

### Event Bus

Simple in-process `asyncio.Queue` fanout. Every subsystem publishes to the bus; the WebSocket gateway and the SQLite event recorder both subscribe. No external broker needed at this scale.

---

## 5. Data Model (SQLite)

Single file at `%LOCALAPPDATA%\apulu-hq\hq.db`, WAL mode, `PRAGMA foreign_keys=ON`. Migrations via Alembic.

```sql
CREATE TABLE agents (
  id TEXT PRIMARY KEY,             -- preserves Paperclip-era IDs: Clu, Nelly, Dex, ...
  display_name TEXT NOT NULL,
  department TEXT NOT NULL,        -- marketing | research | production | post-prod | cos | board
  role TEXT NOT NULL,
  adapter_type TEXT NOT NULL,      -- claude_local | process | api
  adapter_config TEXT NOT NULL,    -- JSON
  model TEXT,                      -- e.g. claude-opus-4
  provider TEXT,                   -- anthropic | openai | ollama | none (for process)
  system_prompt TEXT,
  desk_x INTEGER NOT NULL,         -- tilemap coordinate
  desk_y INTEGER NOT NULL,
  sprite_key TEXT NOT NULL,        -- asset reference
  enabled INTEGER NOT NULL DEFAULT 1,
  budget_monthly_usd REAL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE routines (
  id TEXT PRIMARY KEY,             -- preserves Paperclip-era routine IDs
  display_name TEXT NOT NULL,
  agent_id TEXT NOT NULL REFERENCES agents(id),
  cron_expr TEXT NOT NULL,
  timezone TEXT NOT NULL DEFAULT 'America/New_York',
  command TEXT NOT NULL,           -- shell command or python entry point
  args TEXT NOT NULL,              -- JSON list of args
  enabled INTEGER NOT NULL DEFAULT 1,
  disabled_reason TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE dispatches (
  id TEXT PRIMARY KEY,
  routine_id TEXT NOT NULL REFERENCES routines(id),
  agent_id TEXT NOT NULL REFERENCES agents(id),
  started_at TEXT NOT NULL,
  ended_at TEXT,
  attempt INTEGER NOT NULL,
  outcome TEXT,                    -- success | failure | retry | dlq
  exit_code INTEGER,
  signature TEXT,                  -- matched pattern, if any
  stderr_tail TEXT,
  duration_ms INTEGER
);
CREATE INDEX idx_dispatches_started ON dispatches(started_at DESC);

CREATE TABLE dlq (
  id TEXT PRIMARY KEY,
  dispatch_id TEXT NOT NULL REFERENCES dispatches(id),
  routine_id TEXT NOT NULL REFERENCES routines(id),
  agent_id TEXT NOT NULL REFERENCES agents(id),
  signature TEXT,
  payload TEXT NOT NULL,           -- full context for replay
  appended_at TEXT NOT NULL,
  replayed_at TEXT,
  replay_outcome TEXT,
  discarded_at TEXT
);

CREATE TABLE chat_threads (
  id TEXT PRIMARY KEY,
  agent_id TEXT NOT NULL REFERENCES agents(id),
  title TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE chat_messages (
  id TEXT PRIMARY KEY,
  thread_id TEXT NOT NULL REFERENCES chat_threads(id),
  role TEXT NOT NULL,              -- user | assistant | system | tool
  content TEXT NOT NULL,
  tokens_in INTEGER,
  tokens_out INTEGER,
  cost_usd REAL,
  created_at TEXT NOT NULL
);
CREATE INDEX idx_messages_thread ON chat_messages(thread_id, created_at);

CREATE TABLE events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  type TEXT NOT NULL,
  payload TEXT NOT NULL            -- JSON
);
CREATE INDEX idx_events_ts ON events(ts DESC);
```

### Migration From Existing Files

A one-shot importer (`scripts/import_from_paperclip.py`) reads:
- `scripts/paperclip/agent_ids.json` → `agents` table (16 rows). All 16 IDs preserved verbatim: Clu, Nelly, Dex, Nova, Sage & Khari, Rex, Rhythm, Cipher, Onyx, Cole, Echo, Vibe, Sable, Camdyn, Oaklyn, Aspyn.
- `scripts/paperclip/routine_ids.json` + Paperclip cron exports → `routines` table (26 rows). All routine IDs and schedules preserved verbatim.
- `dispatch_log.jsonl` → `dispatches` table (historical).
- `dead_letter.jsonl` → `dlq` table.

The importer is idempotent and re-runnable. After import, the legacy JSON files become read-only references — the database is the source of truth.

---

## 6. Existing Code Mapping

| Paperclip-era artifact | Replaced by | Notes |
|---|---|---|
| `paperclip/` (entire workspace) | Apulu HQ backend + Tauri shell | Source workspace stays read-only during cutover. |
| `start-paperclip.bat` | Tauri sidecar launches FastAPI | Single executable, no batch file. |
| `run_paperclip_watchdog.cmd` | Tauri shell lifecycle + WTS task `HQHeartbeat` | Watchdog still scheduled, but it pings `/api/health`, not the dev-watcher. |
| `dev-watch.ts` / `tsx` / embedded postgres | Gone. SQLite + FastAPI. | The hang failure mode is structurally eliminated. |
| `scripts/paperclip/agent_ids.json` | `agents` table (SQLite) | One-shot importer; file kept read-only as historical reference. |
| `scripts/paperclip/routine_ids.json` | `routines` table (SQLite) | Same. |
| `scripts/paperclip/setup_*.py` | `scripts/seed_*.py` (Python, writes to SQLite) | Conceptually the same — seed the org. |
| `scripts/paperclip/cos_briefing.py` | Nelly's chat routine + scheduled job | The briefing is now generated as a routine on Nelly. |
| `scripts/paperclip/broadcast.py` | `POST /api/agents/broadcast` | UI button: "Send message to all department heads." |
| `dispatch_runner.run_with_retries` | `apulu_hq/dispatch/runner.py` | Near-verbatim port. |
| `paperclip_run_monitor.py` (WTS, 15 min) | Same script, renamed `hq_run_monitor.py` | Now queries SQLite instead of Paperclip's API. |
| `backend_health_probe.py` (WTS, 10 min) | Unchanged | Writes `backend_health.json` — same path, same consumers. |
| `validate_adapters.py` (WTS, daily 5:45) | Unchanged | Smoke tests against the new HQ API. |
| `status_board.py` (WTS, hourly) | Unchanged | Writes `STATUS.md` — same path, same format. New input source: SQLite. |
| `posted_log_invariant.py` (WTS, hourly) | Unchanged | Writes `posting_liveness.json`. |
| `~/.paperclip-watchdog-state.json` | `~/.apulu-hq-state.json` | New name, same purpose. |
| Paperclip dashboard UI | Tauri shell + Phaser scene + React panels | The actual product of this spec. |

### Pipeline Code (Untouched)

All of `pipeline/`, all of `projects/apulu-prompt-generator/`, all of `Ai Mix Engineer/`, all of `Apulu Prompt Generator/`. These are agent *bodies* — the orchestration layer changes but the work they do does not.

---

## 7. Migration Plan

### Guiding Principles

1. **Never break the working system.** HQ runs alongside Paperclip until every routine has succeeded under HQ for ≥3 consecutive days.
2. **One routine at a time.** Cut over the least-risky routines first.
3. **Read-only first.** Phase 1 and 2 do not fire any routines from HQ — HQ only observes.
4. **Rollback is always one cron flip away.** Re-enabling the Paperclip-side schedule restores the prior state at any phase.

### Phase 0 — Spec, schema, scaffolding (Week 1)

- This document, committed to `docs/superpowers/specs/`.
- Repo scaffold under `projects/apulu-hq/`: backend (`apps/backend`), Tauri shell (`apps/shell`), shared types (`packages/types`).
- SQLite schema + Alembic migrations.
- Importer for `agent_ids.json` and `routine_ids.json` written and tested against a copy of the production data.
- **Exit criteria**: `apulu-hq import` populates `hq.db` with 16 agents and 26 routines that match the Paperclip-era IDs exactly.

### Phase 1 — Backend MVP, observe-only (Weeks 2–3)

- FastAPI app exposes REST endpoints listed in Section 4.
- WebSocket gateway emits a subset of events: `agent.state_changed`, `health.snapshot`.
- Scheduler is loaded but every routine is `enabled=0`. HQ does not fire anything.
- A tail process reads the existing `dispatch_log.jsonl` and `dead_letter.jsonl` and replays them as WS events so the UI sees real activity during development.
- **Exit criteria**: `curl http://127.0.0.1:8741/api/agents` returns 16 agents; `curl /api/routines` returns 26 routines; WebSocket emits events as Paperclip continues to run.

### Phase 2 — Tauri shell, no avatars yet (Weeks 4–5)

- Tauri window opens, lists 16 agents in a left rail.
- Click an agent → chat panel works end-to-end. Streaming responses from Anthropic via the agent's configured model.
- Daily briefing tab renders today's briefing.
- DLQ tab lists existing DLQ entries (read-only).
- Event ticker streams live.
- **Exit criteria**: Operator can talk to any of the 16 agents from the Tauri window. This alone is the single biggest UX win and worth shipping as v0.1 even if the map never lands.

### Phase 3 — First routine cutover: `hashtag-scan` (Week 6)

- Single lowest-stakes routine flipped: HQ schedules it; Paperclip's copy is disabled.
- 3 consecutive successful days → keep cutover.
- Any failure → flip back, fix, retry.
- This is the dispatcher integration test.
- **Exit criteria**: `hashtag-scan` runs under HQ for 3 days with outcomes matching the Paperclip baseline.

### Phase 4 — Marketing cycle cutover (Weeks 7–8)

- Routines in order: `text-post-morning`, `text-post-afternoon`, `morning-early`, `morning-main`, `midday-early`, `midday-main`, `evening-early`, `evening-main`, `recycle`, `engagement-monitor`, `engagement-bot`.
- One per day, 24-hour soak each.
- Disabled routines (`lyric-card`, `video-cinematic`) carried over as disabled in HQ — same reasons, same flags.
- **Exit criteria**: All marketing routines firing under HQ; Paperclip's marketing schedule fully disabled.

### Phase 5 — Discovery, analytics, weekly routines (Week 9)

- `artist-discovery-scan`, `playlist-monitor`, `sync-opportunity-scan`, `press-opportunity-scan`, `streaming-revenue-check`, `analytics-digest`, `content-performance-daily`, `weekly-ops-digest`, `competitor-tracking`, `track-teaser`, `video-daily`, `system-health-check`.
- All remaining routines flipped, 48-hour soak per batch.
- **Exit criteria**: All 26 routines on HQ. Paperclip company config archived. `start-paperclip.bat` removed from startup folder.

### Phase 6 — Phaser map + avatars (Weeks 10–12)

- Tilemap authored in Tiled.
- Sprites integrated (LimeZu + character base).
- State machine wired to WS events.
- Click-to-chat parity with the list-based UI from Phase 2.
- **Exit criteria**: The map is fun. The operator uses it as the default view.

### Phase 7 — Decommission Paperclip (Week 13)

- Paperclip workspace renamed `paperclip.archive-2026-08-XX`.
- All WTS tasks pointing at `start-paperclip.bat` removed.
- `dev:watch` watchdog removed.
- Final status writeup: incident note + skill update on lessons learned.

### Rollback Plan (Every Phase)

For any phase, rollback is:
1. In HQ, set the relevant routines to `enabled=0`.
2. In the corresponding Paperclip schedule, re-enable.
3. Verify on next firing window that Paperclip resumed.

Because HQ writes to the same `dispatch_log.jsonl`, `dead_letter.jsonl`, and `STATUS.md` files, monitoring continuity is preserved across rollbacks.

---

## 8. Operational Concerns

### Auto-Start

`apulu-hq-installer.exe` installs:
- `%LOCALAPPDATA%\apulu-hq\apulu-hq.exe` (Tauri shell)
- A shortcut in `shell:startup` named `Apulu HQ.lnk` with `--minimized-to-tray`.
- The Tauri shell launches the FastAPI sidecar; nothing else needs to run separately.
- The shell exits to system tray on close; explicit Quit from tray menu shuts down backend.

A fallback `--daemon` mode runs the backend without the shell, used by an optional WTS task `HQDaemon` for the operator's "machine reboots and I'm not logged in yet" scenario. The shell connects to the daemon if it's already running.

### Logging

- Backend writes structured logs to `%LOCALAPPDATA%\apulu-hq\logs\hq-YYYY-MM-DD.log`. Rotation: daily, keep 30 days.
- Shell writes to `%LOCALAPPDATA%\apulu-hq\logs\shell-YYYY-MM-DD.log`.
- Existing `dispatch_log.jsonl`, `dead_letter.jsonl`, `alert_fallback.jsonl` paths unchanged.

### Secrets

- `%LOCALAPPDATA%\apulu-hq\secrets.json`, file ACL restricted to current user.
- Loaded once at startup; never written to logs, never sent over WS.
- Existing secret locations (`pipeline/config/*.json`, etc.) are read on demand by the process adapter, exactly as today.

### Backup

A nightly WTS task `HQBackup` copies `hq.db` to `%LOCALAPPDATA%\apulu-hq\backups\hq-YYYY-MM-DD.db`, keeps 14 days. SQLite WAL mode means the copy is consistent.

### Observability

- `GET /api/health` returns the same shape `STATUS.md` consumes, so the existing hourly StatusBoard generator can switch from "scrape Paperclip" to "GET /api/health" with one line of code.
- Per-agent token usage and cost visible in Settings, monthly totals in the briefing.

### Performance Targets

- Cold start (Tauri shell launch to first render): <2 s on a typical Windows machine.
- Backend cold start: <1 s.
- Memory: backend <150 MB resident, shell <250 MB resident.
- One agent dispatch (Claude CLI subprocess): not bounded by HQ — same as today.

### Single-User Scope

No auth in v1. Backend binds to `127.0.0.1` only. Multi-operator is explicitly out of scope.

---

## 9. Risks and Open Questions

### Risks

| Risk | Mitigation |
|---|---|
| Porting the dispatcher introduces a subtle behavior change that loses a post | Phase 3 (single low-stakes routine for 3 days) and Phase 4 (one-per-day cutover) catch this before it scales. |
| Tauri sidecar life-cycle bugs lose the backend on shell close | `--daemon` mode runs the backend independently; the shell becomes a thin client. |
| Phaser scene performance degrades with future feature creep | Scene is a v0 polish item — backend is the product, the map is the icing. Cap the budget. |
| `dispatch_log.jsonl` schema drifts between HQ and legacy monitors | Schema is locked at the existing format; HQ writes a strict superset only with new optional fields. |
| Claude CLI auth expiry still takes down 11 agents | Inherited problem. Open question (below). |

### Open Questions

1. ~~**Should we migrate `claude_local` agents to direct Anthropic SDK calls?**~~ **Decided 2026-05-13: defer.** `claude_local` adapter stays for v1 to preserve parity with the Paperclip-era behavior (slash commands, project context, existing agent prompts). The new `api` adapter type is available alongside and any *new* agent can opt into it; existing 11 `claude_local` agents migrate per-agent only when justified by a concrete win. The OAuth-expiry-blasts-11-agents failure mode is accepted for v1 — mitigation continues to be signature detection + 15-min alert via `hq_run_monitor.py`.
2. ~~**Where does the Apulu Prompt Generator live?**~~ **Decided 2026-05-13: v2.** v1 calls it via HTTP from the relevant agent's process adapter — zero new integration surface. Embedded Tauri UI button revisited in v2 once HQ has shipped and real usage patterns are visible.
3. ~~**Multi-artist UI?**~~ **Decided 2026-05-13: v2.** v1 is single-artist (Vawn). Schema already accommodates an `artist_id` column on `agents` / `routines` / `dispatches` (Section 10 success criteria); UI surfacing of multi-artist (tabs vs. multi-floor building) is a v2 decision once a second artist is signed.
4. ~~**Voice channel for the CEO chat?**~~ **Decided 2026-05-13: v2.** Text-only chat in v1. TTS/STT "talk to Nelly" mode is a natural follow-on once the chat surface and per-agent personas are stable.
5. ~~**Mobile companion?**~~ **Decided 2026-05-13: v2.** v1 is Windows-desktop-only. A read-only mobile view (status, briefing, DLQ count) served by the same FastAPI backend over Tailscale is the obvious v2 path — no architectural changes required, only a new frontend bundle.

---

## 10. Success Criteria

- All 16 agents and 26 routines preserved by ID and behavior; zero schedule drift relative to the Paperclip-era cron.
- Zero `dev:watch` startup hangs after Phase 7 (failure mode structurally eliminated).
- Operator can chat with any agent in <2 clicks from cold start.
- The HQ map renders at ≥30 fps and reflects backend state with <200 ms latency.
- `STATUS.md` continues to be the single source of truth for "what's the label doing right now," regenerated from the new `/api/health` endpoint.
- DLQ entries can be replayed from the UI with one click; existing manual `dlq_replay.py` workflow remains available as fallback.
- Adding artist 2 requires schema-level changes only (an `artist_id` column on `agents`, `routines`, `dispatches`); zero new infrastructure.
- A first-time setup on a fresh Windows machine (installer → import → first dispatch) completes in <15 minutes.
