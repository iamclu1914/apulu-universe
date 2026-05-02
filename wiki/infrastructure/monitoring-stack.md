# Monitoring Stack

Full inventory of the Windows Task Scheduler tasks that make up the infrastructure layer. Every task is a `.cmd` wrapper that launches a Python script in `C:\Users\rdyal\Vawn\`.

## Tasks

### `\Vawn\ValidateAdapters`
- **Cadence:** Daily at 5:45am ET
- **Script:** `validate_adapters.py`
- **Launcher:** `run_validate_adapters.cmd`
- **What it does:** Smoke-tests every `process`-adapter agent (currently Dex, Nova, Sage & Khari) by py-compiling the target script. Then runs every slot in `marketing_dispatch.py`'s `DISPATCH_TABLE` via `--dry-run`.
- **Why 5:45am:** Runs *before* the 6:00am routines. Catches adapter config bugs (like today's `missing_cron_arg`) before they cause silent failures.
- **Alert trigger:** Healthy → failing transition. Uses `validator_state.json` to dedup.
- **State file:** `validator_state.json`

### `\Vawn\BackendHealthProbe`
- **Cadence:** Every 10 minutes
- **Script:** `backend_health_probe.py`
- **Launcher:** `run_backend_health_probe.cmd`
- **What it does:** Probes `apulustudio.onrender.com` on three endpoints:
  - `GET /` (root) — is the service up at all?
  - `GET /api/posts` (expects 401) — is auth middleware healthy?
  - `POST /api/posts/upload` (expects 401 without auth) — is the upload handler reachable?
- **Side effect:** Pre-warms Render free tier instance every 10 min, sidestepping cold-start 502s.
- **Alert trigger:** Transition healthy → degraded. Re-alert every 2 hours while still degraded. Recovery alert on degraded → healthy.
- **State file:** `backend_health.json` (includes 24h rolling history). Read by `post_vawn.py`'s circuit breaker.

### `\Vawn\PaperclipRunMonitor`
- **Cadence:** Every 15 minutes
- **Script:** `paperclip_run_monitor.py`
- **Launcher:** `run_paperclip_monitor.cmd`
- **What it does:** Two queries against the Paperclip Postgres:
  1. `heartbeat_runs` with status='failed' in the last 20 minutes → email per new failure with signature detection
  2. `agents` with status='error' and `updated_at > 30 min ago` → email per stuck agent
- **Dedup:** `paperclip_monitor_state.json` tracks reported run IDs (last 500) and stuck-agent snapshots (last 200) so repeated alerts for the same run don't fire.
- **Signature detection:** Matches against stderr for `claude_auth_expired`, `backend_5xx`, `adapter_config_bug`, `rate_limit`, `network_transient`.
- **State file:** `paperclip_monitor_state.json`

### `\Vawn\StatusBoard`
- **Cadence:** Every hour
- **Script:** `render_status.py`
- **Launcher:** `run_status_board.cmd`
- **What it does:** Reads every state file in the stack + queries Paperclip DB for agent list + 24h run stats. Rolls up into a single markdown file `STATUS.md` with sections: Active Issues, Backend, Claude Auth, Agents (16-row table), Recent Failures, Dispatch Attempts, Dead-Letter Queue, Undelivered Alerts, Today's Posts.
- **Overall status algorithm:** 🟢 HEALTHY (0 issues) / 🟡 DEGRADED (1-2 issues) / 🔴 CRITICAL (3+).
- **Output file:** `C:\Users\rdyal\Vawn\STATUS.md`
- **Consumed by:** Clu (human), Rex's daily health routine, daily CoS briefing.

## State file reference

| File | Written by | Consumed by | Lifetime |
|---|---|---|---|
| `STATUS.md` | `render_status.py` | Clu, Rex, briefing | Rewritten hourly |
| `backend_health.json` | `backend_health_probe.py` | `post_vawn.py` (breaker), dashboard, briefing | Last 24h of history |
| `claude_auth_state.json` | `claude_auth_probe.py` (manual) | Dashboard, briefing | Last check only |
| `dispatch_log.jsonl` | `dispatch_runner.py` | Dashboard | Append-only, audit |
| `dead_letter.jsonl` | `dispatch_runner.py` | `dlq.py`, dashboard | Append-only until cleared |
| `alert_fallback.jsonl` | `email_notify.py` on SMTP failure | `flush_alerts.py`, dashboard | Cleared after delivery |
| `paperclip_monitor_state.json` | `paperclip_run_monitor.py` | self (dedup) | Last 500 runs + 200 stuck-agent snapshots |
| `backend_health.json → history` | `backend_health_probe.py` | dashboard trend | 144 entries (24h at 10-min cadence) |
| `validator_state.json` | `validate_adapters.py` | self (transition detection) | Last check only |
| `posted_log.json` → `_posted_slots` | `post_vawn.py` | self (dedup), dashboard | Per-day, grows indefinitely |

## Launcher pattern

All `.cmd` launchers follow this shape:
```batch
@echo off
cd /d C:\Users\rdyal\Vawn
python <script>.py
exit /b %ERRORLEVEL%
```

Some need PATH adjustments for subprocess calls (e.g. `run_claude_auth_probe.cmd` prepends `C:\Users\rdyal\AppData\Roaming\npm` so `claude.cmd` is findable).

## Disabled tasks (2026-04-16)

Previously Paperclip and WTS both fired posting tasks in parallel — 17 WTS tasks duplicated every posting routine, causing erratic timing. All disabled via:

```powershell
@('MorningEarly','MorningMain','TextPostMorning','MiddayEarly','MiddayMain','TextPostAfternoon','EveningEarly','EveningMain','HashtagScan','LyricCardAgent','VideoAgent','VideoAgentCinematic','RecycleAgent','EngagementAgent','EngagementBot','AnalyticsDigest','MetricsAgent') | ForEach-Object { schtasks /Change /TN "\Vawn\$_" /DISABLE }
```

Paperclip routines are now the sole driver for posting. These stay disabled unless Paperclip is down for an extended period (manual failover procedure — not currently automated).

Still enabled on WTS (infrastructure, not posting):
- `Paperclip` (keepalive for `pnpm dev`)
- `Bridge` (6:25am — pipeline → post_vawn handoff)
- `DailyBriefing`, `EmailBriefing`, `HealthMonitor` (briefing generation)
- `LyricAnnotation` (Wed 10am)
- `PipelineDiscovery`, `PipelineIdeation`, `ResearchCompany` (5:30/5:50/6:10am)
- `PromptResearchReddit`, `PromptResearchVideo` (Mon/Thu 6am)
- `APU68*` tasks (engagement automation, separate system)
- `ValidateAdapters`, `BackendHealthProbe`, `PaperclipRunMonitor`, `StatusBoard` (the stack itself)
