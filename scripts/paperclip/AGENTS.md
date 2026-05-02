# scripts/paperclip/ — Codex Instructions

**HIGH RISK area.** These scripts manage live agent infrastructure: agents, routines, capabilities, dispatch routing. Mistakes here can silently break daily operations across 16 agents and ~30 scheduled routines.

See root `AGENTS.md` first, then `wiki/paperclip-operations/_index.md` and `wiki/infrastructure/_index.md` for operational context.

## What lives here

- `setup_company.py`, `setup_agents.py`, `setup_marketing.py`, `expand_org.py` — initial provisioning
- `restructure_org.py`, `set_capabilities.py`, `add_remotion_routines.py` — incremental org changes
- `update_all_instructions.py`, `update_cos_adapter.py` — agent instruction/adapter updates
- `cos_briefing.py` — Chief of Staff briefing entry point
- `test_heartbeat.py` — heartbeat smoke test (`--check-only` for read-only)
- `agent_ids.json`, `routine_ids.json`, `company_id.txt` — **state files. Do NOT edit by hand.**

## Read-only state files

These three files are written by the setup scripts and read by everything else. **Never edit them manually.** A typo here breaks dispatch routing across all routines.

- `company_id.txt` — single UUID
- `agent_ids.json` — `{ "<agent name>": "<uuid>" }` for all 16 agents
- `routine_ids.json` — `{ "<routine name>": "<uuid>" }` for all routines

If you need to add an agent or routine, run the matching setup script and let it append to these files.

## Operating rules

- **Check before write.** Run `python scripts/paperclip/test_heartbeat.py --check-only` before any change that touches an agent or routine.
- **Don't rename casually.** Renaming an agent, department, routine, or capability cascades into Paperclip DB rows, adapter configs, and the live dispatcher in `C:\Users\rdyal\Vawn\marketing_dispatch.py`. If a rename is needed, plan the full chain of updates first.
- **Preserve dispatch routing.** `marketing_dispatch.py` (in the `projects/vawn` workspace, gitignored here) reads issue titles to route to scripts. Adapter configs in Paperclip must match the routing table.
- **Preserve infra resilience.** Don't strip retry, DLQ, circuit-breaker, health-probe, or alert-fallback logic — see `wiki/infrastructure/runbooks.md` for what each piece does.
- **Dry-run first.** Most setup scripts print a plan. Read it before letting them write to the Paperclip DB.

## When something is failing

1. Check live dashboard: `C:\Users\rdyal\Vawn\STATUS.md` (regenerated hourly)
2. Match the failure signature in `wiki/infrastructure/runbooks.md`
3. Common signatures: `claude_auth_expired`, `apulu_backend_5xx`, `missing_cron_arg`, `bluesky_auth`, `rate_limit`
4. Then act — don't restart routines blindly

## Don't touch without explicit ask

- `agent_ids.json`, `routine_ids.json`, `company_id.txt` — state files
- Any `setup_*.py` script's idempotency / DB-write logic
- Adapter wiring in scripts that flow into `marketing_dispatch.py`
