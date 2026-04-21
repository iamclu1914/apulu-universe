---
type: hub
topic: vawn-research-discovery
---

# Vawn Discovery

Raw output from the discovery pipeline (`pipeline/discovery/run_all.py`). Runs daily at 5:30am ET.

## File types

- **`{Platform} Pipeline -- YYYY-MM-DD.md`** — Daily per-platform scrape output (X, Instagram, TikTok, YouTube, Reddit) via Apify
- **`Discovery Brief -- YYYY-MM-DD.md`** — Consolidated cross-platform discovery summary
- **`Research Pipeline — {topic}.md`** — One-off NotebookLM-backed deep dives on specific topics (AI music, Suno, Higgsfield, etc.) — irregular cadence
- **`Seedance 2.0 Research -- YYYY-MM-DD.md`** — Topic-specific research output
- **`YYYY-MM-DD-playlist-monitor.md`** — Rhythm's daily playlist monitor (kebab-case, sits alongside Title-case pipeline notes — inconsistency)

## History

This folder became canonical on **2026-04-14**. Before that, discovery briefs lived at `journals/vawn/discovery/`. See [[../../../journals/vawn/_index]] for the legacy location.

## Naming drift to know about

Files on/before 2026-04-09 use real em-dash character (`—`). Files on/after 2026-04-10 use double-hyphens (`--`). Both represent the same pattern but break plain-text substring search.

## Related

- Parent hub: [[../_index]]
- Pipeline source: `pipeline/discovery/run_all.py` and per-platform subfolders
- Downstream: [[../ideation/_index]] reads this folder every morning at 5:50am
