# Bulletproofing Overview

Built 2026-04-16 after a day-long silent failure where `Sage & Khari`'s adapter config was invoking `post_vawn.py` without its required `--cron` argument. Paperclip fired the routine 8+ times; every run crashed within milliseconds; nothing alerted Clu; 8 post slots were lost. The *email alert channel itself* was also broken (Google had revoked the app password), so even if detection had existed, Clu wouldn't have heard about it.

The resilience stack is designed around one principle: **every failure must be visible within 15 minutes, even when parts of the system are lying or dead**.

## Architecture layers

```
  ┌──────────────────────────────────────────────────────────────┐
  │  Layer 5: Dashboard                                          │
  │    STATUS.md (hourly) — single file, read by humans + agents │
  └──────────────────────────────────────────────────────────────┘
              ▲
              │ reads
              │
  ┌──────────────────────────────────────────────────────────────┐
  │  Layer 4: Monitors (scheduled probes)                        │
  │    • PaperclipRunMonitor (15 min) — failed runs + stuck      │
  │      agents, signature detection                             │
  │    • BackendHealthProbe (10 min) — Apulu Studio endpoints    │
  │    • ValidateAdapters (daily 5:45am) — config smoke-test     │
  └──────────────────────────────────────────────────────────────┘
              ▲
              │ queries
              │
  ┌──────────────────────────────────────────────────────────────┐
  │  Layer 3: Retry wrapper + DLQ                                │
  │    dispatch_runner.run_with_retries:                         │
  │      • 3x exp backoff (30s / 2min / 8min)                    │
  │      • Short-circuit on exit 2 (config) and exit 3 (breaker) │
  │      • Signature detection (8 known patterns)                │
  │      • dispatch_log.jsonl + dead_letter.jsonl                │
  └──────────────────────────────────────────────────────────────┘
              ▲
              │ wraps
              │
  ┌──────────────────────────────────────────────────────────────┐
  │  Layer 2: Circuit breaker                                    │
  │    post_vawn.py reads backend_health.json before burning     │
  │    Suno tokens. Exit 3 if backend is degraded <30 min old.   │
  └──────────────────────────────────────────────────────────────┘
              ▲
              │ checks
              │
  ┌──────────────────────────────────────────────────────────────┐
  │  Layer 1: Per-platform dedup                                 │
  │    post_vawn.py mark_slot_posted tracks per-platform state.  │
  │    Slot locks only on FULL success. Partial failures         │
  │    become retry-eligible for the next routine run.           │
  └──────────────────────────────────────────────────────────────┘
              ▲
              │ executes
              │
  ┌──────────────────────────────────────────────────────────────┐
  │  Layer 0: Alert delivery                                     │
  │    email_notify.send_notification → SMTP (Gmail).            │
  │    On SMTP failure → alert_fallback.jsonl (local persist).   │
  │    flush_alerts.py replays the queue once SMTP recovers.     │
  └──────────────────────────────────────────────────────────────┘
```

## Why these specific layers

### Layer 1: Per-platform dedup (`post_vawn.py`)
Before the rewrite, a partial post (IG succeeded, X failed) marked the slot as done, blocking retry. Now the slot state is either `True` (complete) or a dict `{x: false, bluesky: false, instagram: true}` so the next run retries only failed platforms. The dedup guard runs earliest — nothing else matters if this is wrong.

### Layer 2: Circuit breaker
Suno tokens cost real money. When Apulu Studio's `/api/posts/upload` returns 500, `post_vawn.py` used to generate a full image + caption + slideshow before failing at upload. The breaker reads `backend_health.json` and exits 3 (retryable) *before* Suno is invoked. Backend health must be <30 min old — otherwise we don't trust it and let the post try.

### Layer 3: Retry wrapper (`dispatch_runner.py`)
Paperclip doesn't retry failed routine runs. Before this, a one-second transient failure meant losing the slot for 2+ hours until the next cron. The wrapper lives at the dispatcher (not in Paperclip core) because it has semantic knowledge Paperclip doesn't: exit 2 = config bug (don't retry, alert now), exit 3 = breaker (don't retry, will pick up next slot), other nonzero = transient (retry).

Signature detection classifies failures from stdout/stderr: `claude_auth_expired`, `apulu_backend_5xx`, `missing_cron_arg`, `bluesky_auth`, `rate_limit`, etc. Each has an `is_retryable` flag and a specific action hint surfaced in the alert email.

### Layer 4: Monitors
Background polls that catch what the dispatcher couldn't (claude_local agent failures, agents stuck in error state, backend degradation trending over time). `ValidateAdapters` runs *before* the 6am posting routines so today's bug class is caught before routines fire, not after.

### Layer 5: Dashboard (`STATUS.md`)
One file, single source of truth. Read by Clu, read by Rex's daily health routine, read by the CoS briefing. Regenerated hourly. Everything critical should be visible here within 1 hour of happening.

### Layer 0: Alert delivery (the outer shell)
The whole stack assumes alerts reach Clu. So alerts themselves need a fallback: if Gmail SMTP fails, writes are appended to `alert_fallback.jsonl`. The dashboard shows "N undelivered alerts" — visible via any layer above. `flush_alerts.py --clear-delivered` replays the queue when SMTP is fixed.

## Known blind spots (things still not covered)

- **Claude Code auth** — `claude_auth_probe.py` exists but can't run under Windows Task Scheduler context (WTS can't read the user's keychain). Detection falls back to: `paperclip_run_monitor.py` catches the `claude_auth_expired` signature in any failed claude_local run. So the first failing routine surfaces the problem, not a proactive probe.
- **Paperclip itself crashing** — The `Paperclip` WTS task restarts `pnpm dev` if it dies, but no alert if it's unhealthy (responds slow, leaks memory, etc). Not yet instrumented.
- **Postgres crashing** — No explicit probe. If the DB is down, every other probe fails with DB errors which would eventually alert.
- **Disk full** — Not monitored. Would surface as all probes failing with IO errors.
- **Stems-to-release pipeline** — Camdyn → Cole → Onyx flow is event-driven and has no monitoring. If a Creative Brief issue stalls, nobody notices.

## Alert fatigue design

Every monitor uses **transition-based alerting**, not poll-based:
- `BackendHealthProbe`: alert on transition healthy→degraded. Re-alert every 2h while still degraded.
- `PaperclipRunMonitor`: dedup via `paperclip_monitor_state.json` — same run ID only alerts once.
- `ValidateAdapters`: alert only on 0 failures → N failures transition.
- `email_notify`: priority + subtitle distinguish source; subject prefix (🚨 / ⚠️ / 📰) hints severity at a glance.

The goal is: every alert is actionable. If Clu gets 3 emails in a row saying "still broken," the monitors are wrong — one email per incident is the target.
