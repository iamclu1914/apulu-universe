---
type: hub
topic: vawn-journals
---

# Vawn Journals

Dated operational notes — "read with coffee" material. Pipeline outputs that are NOT formal research tickets.

## Current state (2026-04-20)

Most of this folder migrated to `research/vawn/` on 2026-04-14. Only **`health/`** is still actively written here.

| Subfolder | Status | Active location |
|---|---|---|
| `health/` | **ACTIVE** — still writing daily | `journals/vawn/health/YYYY-MM-DD-health.md` |
| `briefings/` | Frozen on 2026-04-14 | Now at [[../../research/vawn/briefings/_index]] |
| `discovery/` | Frozen on 2026-04-14 | Now at [[../../research/vawn/discovery/_index]] |

## Why two "health" notes exist in parallel

- `journals/vawn/health/YYYY-MM-DD-health.md` — Rex's daily system-health output (Paperclip routine `system-health-check`, 6am)
- `research/vawn/briefings/Health -- YYYY-MM-DD.md` — CoS agent's pipeline health output (WTS `HealthMonitor`, 7:15am)

They cover different surfaces. Rex = Paperclip + agent state. CoS = pipeline data freshness. Both are useful.

## Related

- Active research hub: [[../../research/vawn/_index]]
- Live infrastructure: `C:\Users\rdyal\Vawn\STATUS.md` (regenerated hourly)
- Infrastructure architecture: [[../../wiki/infrastructure/_index]]
