---
type: hub
topic: vawn-scripting
---

# Vawn Scripting

Output from `pipeline/scripting/` engines — hooks, outlines, titles generated from ranked ideation.

## File pattern

- `Hooks — {truncated-idea-title}.md`
- `Outline — {truncated-idea-title}.md`
- `Titles — {truncated-idea-title}.md`

Generated via:
```
python pipeline/scripting/hooks_engine.py --from-ideation
python pipeline/scripting/outline_engine.py --from-ideation --format short
python pipeline/scripting/titles_engine.py --from-ideation
```

## Related

- Parent hub: [[../_index]]
- Upstream: [[../ideation/_index]]
- Downstream: Cascade pipeline (`pipeline/cascade/content_cascade.py`) writes to `post_vawn.py` staging
