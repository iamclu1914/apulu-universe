---
type: note
topic: paperclip-operations
status: active
last-incident: 2026-04-25
---

# Paperclip — Incidents and Recovery

The recurring failure mode is a `dev:watch` hang at startup. This note captures the symptom, the recovery procedure that actually unsticks it, the cost of that recovery, and the observability gap that keeps these outages silent for hours.

## The recurring failure mode: `dev:watch` hang

**Symptom signature** (reproduced 2026-04-20, 2026-04-25):

`pnpm dev` reaches this line in `start-paperclip.bat` →
```
> @paperclipai/server@0.3.1 dev:watch C:\Users\rdyal\Apulu Universe\paperclip\server
> cross-env PAPERCLIP_MIGRATION_PROMPT=never PAPERCLIP_MIGRATION_AUTO_APPLY=true tsx ./scripts/dev-watch.ts
```

…and then **goes silent**. All ~9 child node processes sit at 0% CPU. Embedded postgres never spawns. Port 3100 never binds. The watchdog at `run_paperclip_watchdog.cmd` keeps relaunching the hidden starter every 5 min, leaving zombie node and postgres processes that pile up — by the third or fourth fire, you can have 15-20 orphan procs across both binaries.

The hang is **inside `dev-watch.ts` or one of its imports**, not in postgres startup. The 0% CPU on all children is the tell — they're waiting on something (probably a spawn or top-level `await`) that never returns.

## What does NOT fix it

- **Killing zombies and restarting** alone — the watchdog will spawn a new dev-watcher within 5 min that hangs the same way.
- **`pnpm install`** — no version drift fix. Tested 2026-04-25 with `cross-env 10.1.0` and 4 other dep updates. No effect.
- **Reading TS source quickly** — needs real diagnostic time, not a 30-min Saturday-night attempt.

## Working recovery procedure (2026-04-25)

```powershell
# 1. Kill everything paperclip-tagged (PowerShell)
Get-CimInstance Win32_Process -Filter "Name='node.exe' OR Name='postgres.exe'" `
  | Where-Object { $_.CommandLine -match 'paperclip' } `
  | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }

# 2. Rename instances/ as a reversible backup
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
Rename-Item "C:\Users\rdyal\Apulu Universe\paperclip\.paperclip-data\instances" `
            -NewName "instances-backup-$ts"

# 3. Re-run start-paperclip.bat — preflight kills any new orphan postgres
& cmd.exe /c "C:\Users\rdyal\Apulu Universe\paperclip\start-paperclip.bat"
```

This brings the server up at HTTP 503 (initializing). If 503 transitions to 200 within 2-3 minutes, you're back. If it stays at 503 indefinitely, postgres still isn't binding 54329 — you've now confirmed the hang is **before** postgres init, which means the next diagnostic step is reading `paperclip/scripts/dev-runner.ts` and `paperclip/server/scripts/dev-watch.ts` to find what's blocking.

**To roll back the wipe:** kill paperclip procs, delete or rename the empty `instances/`, rename `instances-backup-<ts>` back to `instances/`, restart.

## Cost of the postgres wipe

The wipe destroys the embedded postgres database holding:
- Company UUID
- All 32 agent UUIDs
- All 16 marketing routine UUIDs
- Issue history (every routine fire, every result, every comment)
- All run logs

Recovering from a successful wipe requires re-running the bootstrap chain (in order):
```bash
python scripts/paperclip/setup_company.py
python scripts/paperclip/setup_agents.py
python scripts/paperclip/setup_marketing.py
python scripts/paperclip/expand_org.py
python scripts/paperclip/update_all_instructions.py
python scripts/paperclip/update_cos_adapter.py
```

The setup scripts are idempotent (skip-if-exists) but they do not write to populate ID files when the DB is empty — they will create new UUIDs and overwrite `scripts/paperclip/{company_id.txt, agent_ids.json, routine_ids.json}`. Any external system that hardcoded the old UUIDs needs to be re-pointed.

**Don't wipe unless you're sure the hang is postgres-related.** If `dev:watch` is hanging before postgres spawn, the wipe doesn't help — you'll just lose state for nothing.

## Observability gap (root cause of the silent outage problem)

`run_paperclip_watchdog.cmd` runs every 5 min via Windows Task Scheduler, probes `http://localhost:3100/api/health`, logs failures to `~/.paperclip-watchdog.log`, and re-launches the hidden VBS starter on failure. That works as far as detection goes.

The signal **never reaches a human notification channel.** Outages have run 2+ hours unnoticed (2026-04-20, 2026-04-25). The `paperclip_run_monitor.py` is supposed to email Clu on failed routine runs, but the failure class it detects is "a routine run failed" — not "Paperclip itself is unreachable." When Paperclip is fully down, no routines fire, no failures get logged, and the monitor stays quiet.

**Punch list:** wire the watchdog's "Paperclip unresponsive" event to an actual notification (email, Pushover, ntfy, etc.) so the next outage gets noticed in <15 min.

## Marketing-posting blast radius

If Paperclip is down, **Marketing posting is silent.** No `post_vawn` / `text_post_agent` / `engagement_agent` task exists in Windows Task Scheduler — the posting chain is Paperclip-only. Verified 2026-04-25.

The `APU68*` Task Scheduler entries (`apu68_apulu_universe_integration.py`, `apu68_unified_engagement_bot.py`, `apu68_video_engagement_engine.py`, etc.) are a **separate engagement and integration system**, not posting backups. They run regardless of Paperclip's state but they don't post.

## Cosmetic noise

`start-paperclip.bat` REM lines fail to parse (probably the em-dash on line 7) — they error noisily with messages like `'Paperclip' is not recognized as an internal or external command`. The actual `set` / `powershell` / `pnpm dev` lines all execute correctly, so this is cosmetic only. Don't waste time chasing it.

## Related

- `C:\Users\rdyal\Apulu Universe\CLAUDE.md` § "Known issues" — short-form version of this note for in-conversation context.
- [[_index]] — Paperclip operations hub.
- [[../infrastructure/_index]] — Where the watchdog→alert wiring should live once it's built.
- `C:\Users\rdyal\Vawn\STATUS.md` — Live operational dashboard.
