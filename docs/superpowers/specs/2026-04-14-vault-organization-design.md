# Apulu Universe Vault Organization — Design Spec

**Date:** 2026-04-14
**Status:** Design approved, awaiting final spec review before implementation planning
**Scope:** Knowledge-note layer of `C:\Users\rdyal\Apulu Universe\`

## Goal

Make the `Apulu Universe` vault a reliable reference base that Claude reads before starting any project. Optimize for agent retrieval (hub-first navigation, predictable paths, minimal noise) without burning time on frontmatter-heavy taxonomy that the vault's size doesn't warrant.

## Non-goals

- **Not reorganizing code or app workspaces.** `pipeline/`, `scripts/`, `projects/`, `paperclip/`, `.claude/`, `.git/` are explicitly out of scope for structural changes (though junk cleanup still applies).
- **Not adopting PARA, Zettelkasten, or other standard systems.** The existing topic-based `wiki/` structure is extended, not replaced.
- **Not building tag taxonomy.** Graduation path only: introduce tags if the vault grows past ~200 notes AND cross-cutting retrieval becomes a friction point.
- **Not touching `paperclip/`** (63k items, separate Apulu Records workspace).

## Design overview

Approach: **Hub-Centric with Minimal Frontmatter** (a.k.a. Approach 1.5).

- `VAULT.md` at vault root provides a global domain → hub decision table for Claude.
- Every topic has an `_index.md` hub with a "when to reference," reading order, and linked-note summaries.
- Frontmatter is added only to note types where it earns retrieval or filtering value (journals, research tickets, hubs). Reference notes in `wiki/` have none; folder structure is the filter.
- Non-note content (pipeline JSON outputs, config JSON) is evicted from the note layer.
- Archive rule: `wiki-archive/` is for *superseded* content only, never "stale" or "old."

## Section 1 — Final top-level structure

```
Apulu Universe/
├── VAULT.md                   ← NEW: global entry point
├── CLAUDE.md                  ← keep (project-level Claude config)
├── wiki/                      ← keep (topic hubs + reference notes)
├── wiki-archive/              ← keep (superseded-only)
├── journals/                  ← NEW
│   └── vawn/
│       ├── briefings/
│       ├── health/
│       └── discovery/
├── research/                  ← slimmed: formal research docs only (APU-xxx tickets)
├── catalogs/                  ← NEW: structured reference .md (lyrics, etc.)
├── docs/                      ← keep (superpowers plans/specs)
├── projects/                  ← keep (code)
├── pipeline/                  ← keep (code)
│   └── output/                ← NEW: destination for JSON pipeline outputs currently in research/
├── scripts/                   ← keep
├── skills/                    ← keep
├── paperclip/                 ← untouched
└── .claude, .git              ← untouched
```

Key moves:

1. **`research/` is split by type.** Daily briefings, health, discovery → `journals/` (high-cadence auto-generated). Formal APU-xxx research stays in `research/`.
2. **Pipeline JSON outputs leave the vault.** `cos_log_*.json`, `*_pipeline_results.json`, `discovery_brief.json` → `pipeline/output/`.
3. **`artists/` dissolves.** Contents move to `projects/vawn/config/` (subject to verification that Vawn pipeline code doesn't hardcode the old path).
4. **`catalogs/`** for structured-reference .md (e.g., `Vawn Lyrics Catalog.md`).
5. **Loose root `.md` files** (`Vawn - Noir Music Video Production Package.md`) move into the appropriate `wiki/` topic.

## Section 2 — Naming conventions

| Category | Convention | Example |
|---|---|---|
| Hubs & indexes | `_index.md` inside each topic folder | `wiki/vawn-mix-engine/_index.md` |
| Topic reference notes | Existing mix of Title Case and kebab-case is preserved | `wiki/vawn-mix-engine/izotope-plugin-guide.md` |
| Daily journal entries | `YYYY-MM-DD-<slug>.md`, lowercase kebab. Slug is `daily-briefing`, `health`, or `discovery-brief` matching subfolder | `journals/vawn/briefings/2026-04-14-daily-briefing.md` |
| Research tickets | `<TICKET-ID>-<kebab-slug>.md` | `research/vawn/APU-107-mix-engine-enhancement.md` |
| Project-specific prose | Title Case with spaces | `wiki/vawn-project/Noir Music Video Production Package.md` |
| Superpowers plans/specs | Existing `YYYY-MM-DD-<topic>.md` convention | keep |

Rules:

- **Dates are ISO `YYYY-MM-DD` everywhere.**
- **Date-first naming for journals** (sortable in any file explorer or grep).
- **Separator discipline:** machine-readable files use lowercase kebab; prose reference notes may use Title Case with spaces.
- **No double-dash artifacts.** Replace all `--` in existing filenames with single `-`.

Junk cleanup: delete all zero-byte files at the vault root whose names don't match a legitimate-file allowlist (same shell-mishap pattern cleaned from the web app folder earlier).

## Section 3 — VAULT.md + hub pattern

### VAULT.md (vault root)

One purpose: **decision tree** for which hub to read given the project at hand. Not a content dump.

Skeleton:

```markdown
# Apulu Universe Vault

Knowledge base for Claude. Read this first when starting any project.

## How to use this vault
1. Identify the project domain (see table below)
2. Read the matching topic hub at `wiki/<topic>/_index.md`
3. Follow links from the hub to deeper notes as needed
4. For daily context, check `journals/vawn/briefings/` for the most recent entries

## Domain → Hub Map

| If the project involves... | Start with |
|---|---|
| Vawn mixing, mastering, iZotope plugins | `wiki/vawn-mix-engine/_index.md` |
| Vawn as an artist (music, releases, identity) | `wiki/vawn-project/_index.md` |
| Apulu Prompt Generator web app | `wiki/apulu-prompt-generator/_index.md` |
| AI video/film (Higgsfield, Kling, etc.) | `wiki/ai-filmmaking/_index.md` |
| Design engineering, frontend quality | `wiki/design-engineering/_index.md` |
| Prompt engineering, creative pipelines | `wiki/cross-topic/_index.md` |
| Apulu Records operations (labels, deals) | `paperclip/` (separate workspace, not in scope) |

## Recent context
- Most recent daily briefing: `journals/vawn/briefings/<YYYY-MM-DD-daily-briefing>.md`
- Active projects: links

## Anti-patterns
- Don't read `research/` before checking if `wiki/` has the digested version
- Don't read pipeline JSON outputs in `pipeline/output/` — they are raw data, not knowledge
```

### Each topic's `_index.md`

Standard structure:

```markdown
---
type: hub
topic: <slug>
---

# <Topic Name>

## When to reference this hub
<1–2 sentences: what kinds of projects or questions should start here>

## Reading order for Claude
1. This file (context)
2. <link to overview.md>
3. <link to most-used reference>
4. ... (optional deeper reads)

## Notes in this topic
- **Overview:** [[overview]]
- **Key references:**
  - [[note-1]] — <one-line summary>
  - [[note-2]] — <one-line summary>
- **Archived:** see `wiki-archive/` for superseded versions

## Related hubs
- [[../other-topic/_index]] — <relationship>
```

Why this shape works for Claude:

- "When to reference" = self-describing relevance check before Claude reads anything deeper.
- "Reading order" = explicit sequence, no guesswork.
- Each note link has a one-line description = Claude can decide which to read without opening files.
- Related hubs = cross-topic navigation without fuzzy search.

## Section 4 — Frontmatter rules

Frontmatter is added only where it earns its keep.

| Note type | Frontmatter? | Schema |
|---|---|---|
| Daily briefings | Yes | `date`, `type`, `briefing-for` |
| Health notes | Yes | `date`, `type` |
| Discovery briefs | Yes | `date`, `type` |
| Research tickets (APU-xxx) | Yes | `ticket`, `type`, `status`, `updated` |
| Topic hubs (`_index.md`) | Yes | `type: hub`, `topic` |
| Reference notes in `wiki/` | No | Folder + hub does the filtering |
| Plans / specs in `docs/` | Existing conventions | Keep as-is |
| Archived notes | No | Folder (`wiki-archive/`) is the signal |

### Schemas

**Journal entries (briefings / health / discovery):**

```yaml
---
date: 2026-04-14
type: daily-briefing         # or: health | discovery
briefing-for: vawn
---
```

**Research tickets:**

```yaml
---
ticket: APU-107
type: research
status: open                 # or: in-progress | closed
updated: 2026-04-14
---
```

**Topic hubs:**

```yaml
---
type: hub
topic: vawn-mix-engine
---
```

### Tags

Skipped. Reasons:

- Flat tags would duplicate folder information (`#vawn-mix-engine` ≡ `wiki/vawn-mix-engine/`).
- Hierarchical tags require discipline that fails under deadline pressure.
- At current vault size (~60 notes), graph view + folder structure + hub pattern cover cross-cutting discovery.
- Graduation path: introduce tags only if the vault grows past ~200 notes AND cross-cutting queries become real friction.

## Section 5 — Archive rules

**Rule:** A note moves to `wiki-archive/` when its content is **superseded by a newer version in `wiki/`** — never because it's old or unused.

### Triggers

Archive when:

- A skill or philosophy note has been rewritten in `wiki/`.
- A guide document was refactored into new hub structure.
- An old overview was split across multiple new notes.

Do NOT archive for:

- Low-frequency reference ("haven't read in 6 months").
- Completed projects (still useful context for Claude).
- Looks stale — either update or delete, don't archive.

### Archive file marker

Every archived file MUST have the supersession pointer as the first content line after any existing frontmatter. If the supersession is ambiguous or the file is simply being deleted, the file leaves `wiki-archive/` entirely — no orphaned archive entries.

Example pointer format:

```markdown
> **Archived 2026-04-14.** Superseded by [[../topic/current-note]].
```

### Applied to existing archive contents

| File | Action |
|---|---|
| `wiki-archive/emil-design-eng-skill.md` | Add pointer to `C:/Users/rdyal/.claude/skills/emil-design-eng/SKILL.md` (external target is acceptable) |
| `wiki-archive/higgsfield-ai-short-film-guide.md` | Check supersession against `wiki/ai-filmmaking/ai-short-film-prompt-library.md`; add pointer if superseded, otherwise delete |
| `wiki-archive/impeccable-frontend-design-skill.md` | Add pointer to `wiki/design-engineering/impeccable-frontend-design.md` |

## Section 6 — Migration order

Execution phases. Each phase is reversible via `git reset` before the phase's commit lands.

### Phase 0: Safety net
1. Initialize `Apulu Universe/` as its own git repo (currently has no git at this level).
2. Initial commit capturing current state.

### Phase 1: Safe destructive cleanup
3. Delete shell-mishap junk files at vault root (zero-byte files whose names don't match a legitimate-file allowlist).
4. Move pipeline JSON outputs from `research/vawn/briefings/` and `research/vawn/discovery/` into `pipeline/output/`. If Vawn pipeline scripts reference the old paths, update them in the same commit.

### Phase 2: Move non-notes out of the notes layer
5. Move `artists/vawn/*` contents to `projects/vawn/config/`. Grep pipeline and script code for `artists/` path references before moving; update any hits.
6. Move loose root `.md` files into the appropriate `wiki/<topic>/` folder.

### Phase 3: Split research into journals + research
7. Create `journals/vawn/{briefings,health,discovery}/`.
8. Move `.md` files from `research/vawn/briefings/` to `journals/vawn/briefings/`, renaming to `YYYY-MM-DD-<slug>.md`.
9. Move `.md` files from `research/vawn/discovery/` to `journals/vawn/discovery/`, renaming similarly.
10. Move health files similarly.
11. Rename formal research tickets in `research/vawn/` to `<TICKET-ID>-<kebab-slug>.md`.

### Phase 4: Catalogs
12. Move `research/vawn/catalog/Vawn Lyrics Catalog.md` to `catalogs/vawn-lyrics.md`.

### Phase 5: Frontmatter
13. Add frontmatter to the six note types defined in Section 4 (journal types, research tickets, hubs).

### Phase 6: Hub authoring
14. Write `VAULT.md` at vault root.
15. Rewrite each `_index.md` in `wiki/` per the template in Section 3.

### Phase 7: Archive audit
16. Apply supersession rule to existing `wiki-archive/` contents (add pointer, or delete).

### Phase 8: Commit and verify
17. Commit changes in logical groups — one commit per phase.
18. Verify Claude can navigate from `VAULT.md` to hub to note without dead links (manual spot-check, potentially with an automated dead-link scan).

## Risks and open questions

- **Vawn pipeline path dependencies.** Phases 1.4 and 2.5 move files that Vawn code may import. Need a grep pass over `pipeline/` and `scripts/` before execution to identify path references that must be updated atomically with the move.
- **Git repo initialization timing.** Phase 0 turns `Apulu Universe/` into its own repo. If anything else in `Apulu Universe/` later wants its own scoped repo (unlikely given code is in `projects/apulu-prompt-generator/` which already has its own), it'd need to be a nested-repo or submodule scenario.
- **Wiki archive file fate.** For `wiki-archive/higgsfield-ai-short-film-guide.md` specifically, the "delete if not superseded" branch requires a judgment call during execution; flagging now so the implementation plan surfaces the decision point.
- **Paperclip reference.** `VAULT.md`'s domain table points Claude to `paperclip/` for Apulu Records operations, but `paperclip/` is explicitly out of scope for this reorganization. If `paperclip/` lacks its own entry-point doc, Claude won't have a good landing there. Out of scope for this spec; noted as follow-up.
