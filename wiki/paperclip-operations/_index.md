---
type: hub
topic: paperclip-operations
status: stub
---

# Paperclip Operations

Apulu Records as an AI-powered record label running on Paperclip: org chart, agents, routines, dispatcher, skills map.

> **Stub notice.** As of 2026-04-20 the operational detail still lives primarily in the project `CLAUDE.md` at `C:\Users\rdyal\Apulu Universe\CLAUDE.md`. This hub exists so the knowledge layer has a correct pointer while that content is migrated here. Each subsection below names the CLAUDE.md section to read until a dedicated note is written.

## When to reference this hub

- You need the org chart (who reports to whom, role → agent name → Paperclip routines)
- You're wiring a new Paperclip routine, agent, or process adapter
- You're deciding which skill to invoke for a given task (22 custom skills mapped to 16 agents)
- You're touching `marketing_dispatch.py`, `post_vawn.py`, or any adapter config
- You're adding a new artist under the label (multi-tenant extension)

For live state (which agents are failing, which dispatches retried) read `C:\Users\rdyal\Vawn\STATUS.md`. For architecture of the *monitoring* stack, go to [[../infrastructure/_index]].

## Planned notes (not yet written)

- **org-chart** — 16 agents under 3 division presidents + Nelly. Current names, roles, adapter type (`process` vs `claude_local`), reporting line. — *See CLAUDE.md § "Org Structure"*
- **routines** — All 16 marketing routines + research routines + event-driven studio flows. Cron, owner, purpose. — *See CLAUDE.md § "Schedule (all times ET)"*
- **dispatcher-and-dlq** — `marketing_dispatch.py` DISPATCH_TABLE, `dispatch_runner.py` retry wrapper, exit-code conventions (2 = argparse bug, 3 = circuit breaker), DLQ CLI. — *See CLAUDE.md § "Bulletproofing Infrastructure"*
- **skills-map** — Which of the 22 skills maps to which agent, when to invoke each. — *See CLAUDE.md § "Skills (22 custom skills mapped to agents)"*
- **production-workflow** — Creative brief → Cole → Suno → Clu approval → stems → Onyx → Freq → Slate → Proof → release. Gating rules. — *See CLAUDE.md § "Production Workflow (Suno)"*
- **multi-artist-config** — `artists/<slug>/config.json` schema, platform/niche/voice/schedule, how to add artist 2. — *See CLAUDE.md § "Multi-Artist Config"*
- **paperclip-db-access** — The one-liner for reading the embedded Postgres at `127.0.0.1:54329`. — *See CLAUDE.md § "Paperclip DB Access"*

## Related hubs

- [[../infrastructure/_index]] — Monitoring, retry, alerting, DLQ architecture
- [[../vawn-project/_index]] — The artist the label currently manages
- [[../vawn-mix-engine/_index]] — Onyx / Freq / Slate's mixing tooling
- [[../cross-topic/_index]] — Cross-cutting pipeline patterns

## Related live state

- `C:\Users\rdyal\Vawn\STATUS.md` — Live dashboard
- `scripts/paperclip/agent_ids.json` — All 32 agent UUIDs (keyed by original role)
- `scripts/paperclip/routine_ids.json` — All 16 routine UUIDs
- `scripts/paperclip/company_id.txt` — Company UUID
