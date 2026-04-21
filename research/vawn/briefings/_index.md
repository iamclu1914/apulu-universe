---
type: hub
topic: vawn-research-briefings
---

# Vawn Briefings

CoS agent output. Two daily files:

- **`Daily Briefing -- YYYY-MM-DD.md`** — Today's plan + yesterday's performance + top ideation pick + discovery highlights + infrastructure status block.
- **`Health -- YYYY-MM-DD.md`** — Pipeline health snapshot (NotebookLM auth, Apify freshness, posting failures, image supply, catalog fallbacks).

Sort newest-first by filename to find the most recent.

## History

This folder became canonical on **2026-04-14**. Before that, briefings lived at `journals/vawn/briefings/` (now frozen). See [[../../../journals/vawn/_index]] for the legacy location.

## Related

- Source scripts: `pipeline/brain/daily_briefing.py`, `pipeline/brain/health_monitor.py`
- Orchestrator: `scripts/paperclip/cos_briefing.py`
- Parent hub: [[../_index]]
- Infrastructure dashboard consumed by the briefing: `C:\Users\rdyal\Vawn\STATUS.md`
- Digested architecture: [[../../../wiki/infrastructure/_index]]
