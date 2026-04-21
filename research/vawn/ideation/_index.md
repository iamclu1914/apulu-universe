---
type: hub
topic: vawn-research-ideation
---

# Vawn Ideation

Output from `pipeline/ideation/ideation_engine.py`. Runs daily at 5:50am ET (after discovery, before briefings).

## File

- **`Content Ideation -- YYYY-MM-DD.md`** — Ranked, pillar-aware content ideas with engagement-feedback scoring

## Inputs

- Discovery pipeline output ([[../discovery/_index]])
- `pipeline/config/pillar_context.json` — weekly pillar rotation
- `pipeline/config/content_rules.json` — voice, platform constraints, forbidden phrases
- `pipeline/config/engagement_feedback.json` — historical per-pillar engagement scores (loop-closing feedback)

## Downstream

- `pipeline/scripting/` — hooks, outlines, titles generated from top ideas (see [[../scripting/_index]])
- `post_vawn.py` + `text_post_agent.py` read today's ideation when writing captions

## Content pillar rotation

Mon=Awareness, Tue=Lyric, Wed=BTS, Thu=Engagement, Fri=Conversion, Sat=Audience, Sun=Video

## Related

- Parent hub: [[../_index]]
- Cascade pipeline: [[../../../wiki/cross-topic/_index]]
