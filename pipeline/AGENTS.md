# pipeline/ — Codex Instructions

The configurable, multi-project content pipeline. See root `AGENTS.md` first, then `CLAUDE.md` "Content Pipeline" section for full context.

## What lives here

- `discovery/` — Phase 0: Apify scrapers (X, IG, TikTok, Reddit, YouTube)
- `ideation/` — Phase 2: competitive analysis + pillar-aware ideas
- `scripting/` — Phase 3: hooks, outlines, titles
- `cascade/` — Phase 4: video → platform-specific posts
- `prompt-research/` — AI video prompt research (Reddit + YouTube + Apify)
- `brain/` — daily briefing + health monitor (Chief of Staff scripts)
- `bridge.py` — connects pipeline output to Vawn's posting system
- `config/` — per-project configs (`vawn.json`, `prompt-generator.json`, `content_rules.json`, `pillar_context.json`, `engagement_feedback.json`)
- `pipeline_config.py` — shared config loader + helpers
- `obsidian_formatter.py` — all human-readable output → Obsidian markdown

## Operating rules

- **Project-config-driven.** Every entry point takes `--project <name>` and resolves config from `pipeline/config/<name>.json`. Do not hardcode Vawn-specific behavior into shared files.
- **Stages are independent.** Discovery → ideation → scripting → cascade → bridge. Don't merge stages or have one stage reach into another's outputs except via documented JSON contracts.
- **Output goes to `research/<project>/<phase>/`** as dual-format: JSON (data) + Obsidian markdown (human-readable). Don't write to `pipeline/output/` (gitignored, raw machine data — see `VAULT.md` anti-patterns).
- **Content rules live in `pipeline/config/content_rules.json`** as the single source of truth. Both `cascade/` and Vawn's `post_vawn.py` (in the projects/vawn workspace) read from it.

## Dry-run discipline

Most entry points support `--dry-run`. Use it before any change that posts, scrapes a paid quota, or writes to operational state:

```bash
python pipeline/bridge.py --dry-run
python pipeline/discovery/run_all.py --project vawn --only x
python pipeline/ideation/ideation_engine.py --project vawn
python pipeline/cascade/content_cascade.py "https://youtube.com/watch?v=..."
```

## Don't touch without explicit ask

- `pipeline/config/*.json` — operational config; secrets adjacent
- `pipeline/discovery/apify_client.py` quota / circuit-breaker logic
- `pipeline/brain/health_monitor.py` thresholds
- Any state file under `pipeline/output/` or `research/<project>/`

## Adding a new artist/project

Create `pipeline/config/<artist>.json` mirroring `vawn.json` shape. Don't fork the engines — extend config.
