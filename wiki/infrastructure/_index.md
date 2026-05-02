---
type: hub
topic: infrastructure
---

# Infrastructure

## When to reference this hub

Start here for anything about Paperclip's monitoring, retry, alerting, and self-healing stack. Specifically:

- A routine fired and nothing happened
- An agent is stuck in `status='error'`
- Posts stopped shipping for a platform
- An email alert came in and you need to diagnose root cause
- You're modifying `marketing_dispatch.py`, `post_vawn.py`, or any agent's `adapter_config`
- You're adding a new Paperclip agent and need to decide adapter type + monitoring hooks

For live data, read `C:\Users\rdyal\Vawn\STATUS.md` — regenerated hourly. This hub is the *architecture + runbook* layer behind that dashboard.

## Reading order for Claude

1. This file (context + when to use).
2. [[bulletproofing-overview]] — the full resilience architecture (retry wrapper, probes, circuit breaker, DLQ).
3. [[runbooks]] — common failure signatures and fixes (Claude auth expired, backend 5xx, adapter config bug, etc.).
4. [[monitoring-stack]] — every WTS task, what it does, and where it writes state.

## Notes in this topic

- **[[bulletproofing-overview]]** — Architecture of the retry/probe/alert/DLQ stack built 2026-04-16. How the layers compose.
- **[[runbooks]]** — Failure signatures and specific remediations. Reach for this first when something breaks.
- **[[monitoring-stack]]** — Inventory of Windows Task Scheduler tasks and the state files they produce/consume.

## Live state files (not wiki notes — read directly)

- `C:\Users\rdyal\Vawn\STATUS.md` — Live dashboard (agents, backend, auth, DLQ)
- `C:\Users\rdyal\Vawn\backend_health.json` — Apulu Studio probe state (now includes the `real_upload` probe added 2026-04-28)
- `C:\Users\rdyal\Vawn\claude_auth_state.json` — Claude CLI auth probe result
- `C:\Users\rdyal\Vawn\dispatch_log.jsonl` — Every dispatch attempt (success + retry history)
- `C:\Users\rdyal\Vawn\dead_letter.jsonl` — Permanently-failed dispatches awaiting manual replay
- `C:\Users\rdyal\Vawn\alert_fallback.jsonl` — Alerts SMTP couldn't deliver
- `C:\Users\rdyal\Vawn\posting_liveness.json` — Outcome-verification snapshot (hourly, `posted_log_invariant.py`)
- `~\.paperclip-watchdog-state.json` — Watchdog up/down state + alert dedup

## Recent incidents

- [[../../journals/vawn/incidents/2026-04-27-storage-quota-and-lyrics-cutover]] — 4-day silent posting outage. Three stacked failures: (1) Supabase SDK `.text`-on-dict regression masked errors as 500s, (2) dispatcher swallowed exit-0+signature as success, (3) bare-endpoint probe stayed green because it never sent a body. Produced structural defenses: `posted_log_invariant.py` (hourly), `real_upload` probe, `paperclip_watchdog_notify.py` (10-min downtime alerts), `cleanup_stale_issues.py` (daily).

## Related hubs

- [[../vawn-project/_index]] — Vawn as an artist; posting pipeline feeds off this.
- [[../cross-topic/_index]] — cross-cutting pipeline patterns.

## Related journals / research

- `journals/vawn/health/` — Rex's daily system-health reports (Paperclip routine `system-health-check`, 6am). Still active here.
- `research/vawn/briefings/Daily Briefing -- YYYY-MM-DD.md` — CoS daily briefing (migrated from `journals/vawn/briefings/` on 2026-04-14). Includes an Infrastructure status block.
- `research/vawn/briefings/Health -- YYYY-MM-DD.md` — CoS pipeline-health output (covers data freshness, Apify, NotebookLM auth — different surface than Rex's health notes).
