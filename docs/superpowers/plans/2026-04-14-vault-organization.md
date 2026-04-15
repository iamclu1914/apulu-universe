# Vault Organization Implementation Plan (Compressed)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganize the knowledge-note layer of `C:\Users\rdyal\Apulu Universe\` into a hub-centric Obsidian vault optimized for Claude to read before starting any project.

**Architecture:** Approach 1.5 — Hub-Centric with Minimal Frontmatter. `VAULT.md` at root provides a global domain → hub decision map. Each topic in `wiki/` has an `_index.md` hub with reading order and linked-note summaries. Frontmatter is added only to note types where it earns retrieval value (journals, research tickets, hubs). Non-note content (JSON pipeline outputs, config) is evicted from the note layer.

**Tech Stack:** Git, PowerShell (Windows file ops), bash, markdown.

**Spec:** See `docs/superpowers/specs/2026-04-14-vault-organization-design.md`.

**Working directory:** `C:\Users\rdyal\Apulu Universe`

---

## Progress marker

**Tasks already complete** (committed to `main`):
- Phase 0.1 — git init + hardened `.gitignore` (commit `c44d3b7`)
- Phase 0.2 — initial vault snapshot (commit `765ede2`) [credentials remediation included]
- Phase 1.1 — shell-mishap junk cleanup at vault root (commit `66c1ec0`)
- Phase 1.2 — pipeline/scripts audit for JSON path references: zero hits (commit `e45bda1`)

---

## Compression note

This plan was compressed from an original 32-task granular plan. Per-phase tasks that were purely mechanical file operations (delete, move, rename) have been merged into per-outcome tasks. Full subagent-driven review (spec + code quality) still applies to each consolidated task. The original granular plan structure is preserved in git history prior to this compression.

---

## Task A: Move pipeline JSON outputs out of notes layer

**Intent:** Pipeline-generated JSON files (`cos_log_*.json`, `*_pipeline_results.json`, `discovery_brief.json`, etc.) currently live in `research/vawn/briefings/`, `research/vawn/discovery/`, and `research/vawn/catalog/`. These are pipeline artifacts, not knowledge notes. Relocate to `pipeline/output/vawn/{briefings,discovery,catalog}/` where they conceptually belong. No code updates required (Phase 1.2 confirmed zero hardcoded references).

**Files:**
- Create: `pipeline/output/vawn/briefings/`, `pipeline/output/vawn/discovery/`, `pipeline/output/vawn/catalog/`
- Move: all `*.json` from `research/vawn/briefings/`, `research/vawn/discovery/`, `research/vawn/catalog/` into corresponding `pipeline/output/vawn/*` destinations

- [ ] **Step 1: Create destination folders**

```bash
powershell -Command "
New-Item -ItemType Directory -Force -Path 'C:\Users\rdyal\Apulu Universe\pipeline\output\vawn\briefings' | Out-Null
New-Item -ItemType Directory -Force -Path 'C:\Users\rdyal\Apulu Universe\pipeline\output\vawn\discovery' | Out-Null
New-Item -ItemType Directory -Force -Path 'C:\Users\rdyal\Apulu Universe\pipeline\output\vawn\catalog' | Out-Null
"
```

- [ ] **Step 2: Move JSONs from each source to its destination**

```bash
powershell -Command "
foreach (\$pair in @(
  @{ Src='C:\Users\rdyal\Apulu Universe\research\vawn\briefings'; Dst='C:\Users\rdyal\Apulu Universe\pipeline\output\vawn\briefings' },
  @{ Src='C:\Users\rdyal\Apulu Universe\research\vawn\discovery'; Dst='C:\Users\rdyal\Apulu Universe\pipeline\output\vawn\discovery' },
  @{ Src='C:\Users\rdyal\Apulu Universe\research\vawn\catalog'; Dst='C:\Users\rdyal\Apulu Universe\pipeline\output\vawn\catalog' }
)) {
  if (Test-Path \$pair.Src) {
    Get-ChildItem -Path \$pair.Src -Filter '*.json' -ErrorAction SilentlyContinue | ForEach-Object {
      Move-Item -Path \$_.FullName -Destination \$pair.Dst
      Write-Host (\"Moved: \" + \$_.Name + ' -> ' + \$pair.Dst)
    }
  }
}
"
```

- [ ] **Step 3: Verify no JSONs remain in research/vawn/**

```bash
cd "C:/Users/rdyal/Apulu Universe" && find research/vawn -name "*.json" 2>&1 | head -10
```
Expected: empty.

- [ ] **Step 4: Commit**

Note: `pipeline/output/` is gitignored (set in Phase 0.1), so the move itself will appear in git as deletions only — the files are staged as deleted from `research/vawn/` and their new location is ignored. This is intentional: pipeline outputs are ephemeral and shouldn't be in git history.

```bash
cd "C:/Users/rdyal/Apulu Universe" && git add -A && git commit -m "chore(vault): relocate pipeline JSON outputs to gitignored pipeline/output/"
```

---

## Task B: Relocate non-note content out of the notes layer

**Intent:** Three unrelated relocations that all achieve the same purpose — keeping the notes layer pure markdown:
1. Audit code for `artists/` path references.
2. Move `artists/vawn/*.json` (config data, not notes) to `projects/vawn/config/`.
3. Move loose root `.md` prose file into the appropriate `wiki/` topic folder.

**Files:**
- Inspect: `pipeline/`, `scripts/`, `projects/` for `artists/` references
- Create: `projects/vawn/config/`
- Move: `artists/vawn/*` → `projects/vawn/config/`
- Delete: `artists/` (empty after move)
- Move: `Vawn - Noir Music Video Production Package.md` → `wiki/vawn-project/Noir Music Video Production Package.md`
- Append to: `.migration-notes.md` (audit finding)
- Modify: any code files from audit that reference `artists/`

- [ ] **Step 1: Grep for artists/ references in code**

```bash
cd "C:/Users/rdyal/Apulu Universe" && grep -rln "artists[/\\\\]vawn\|artists\\\\vawn" pipeline/ scripts/ projects/ 2>&1 | head -40
```

- [ ] **Step 2: Append audit finding to `.migration-notes.md`**

Append a new section:

```markdown

## artists/ path references (Phase 2.1)
- [list each file:line hit, or: "No hardcoded references found"]
```

- [ ] **Step 3: Create `projects/vawn/config/` and move artists JSONs**

```bash
powershell -Command "
New-Item -ItemType Directory -Force -Path 'C:\Users\rdyal\Apulu Universe\projects\vawn\config' | Out-Null
Move-Item -Path 'C:\Users\rdyal\Apulu Universe\artists\vawn\*' -Destination 'C:\Users\rdyal\Apulu Universe\projects\vawn\config\'
Write-Host 'Moved. New location contents:'
Get-ChildItem 'C:\Users\rdyal\Apulu Universe\projects\vawn\config'
"
```

- [ ] **Step 4: Remove empty `artists/` directory tree**

```bash
powershell -Command "
\$path = 'C:\Users\rdyal\Apulu Universe\artists'
if (Test-Path \$path) {
  Remove-Item -Recurse -Force \$path
  Write-Host 'Removed artists/'
}
"
```

- [ ] **Step 5: Update code references from Step 1 (if any)**

For each hit recorded in `.migration-notes.md`, replace `artists/vawn/...` with `projects/vawn/config/...`. Skip if zero hits.

- [ ] **Step 6: Move loose root `.md` file into wiki/vawn-project/**

```bash
powershell -Command "
Move-Item -Path 'C:\Users\rdyal\Apulu Universe\Vawn - Noir Music Video Production Package.md' -Destination 'C:\Users\rdyal\Apulu Universe\wiki\vawn-project\Noir Music Video Production Package.md'
"
```

- [ ] **Step 7: Verify**

```bash
cd "C:/Users/rdyal/Apulu Universe" && ls projects/vawn/config/ && echo "---" && ls wiki/vawn-project/ && echo "---" && ls artists 2>&1 | head -2
```
Expected: config JSONs in `projects/vawn/config/`; noir .md in `wiki/vawn-project/`; `artists` not found.

- [ ] **Step 8: Commit**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git add -A && git commit -m "chore(vault): relocate non-note content (artists config, noir video note) out of notes layer"
```

---

## Task C: Restructure research/ into journals + research

**Intent:** Split the current `research/vawn/briefings/` content by type. Daily, cadence-based notes (briefings, health, discovery) move to `journals/vawn/`. One-off research docs (APU-xxx tickets, dated alignment docs) stay in `research/vawn/` but with standardized naming. All journal entries and research docs get date-first kebab-case names.

**Naming rules:**
- Journal entries: `YYYY-MM-DD-<slug>.md` where slug is `daily-briefing`, `health`, or `discovery-brief`
- Research tickets: `<TICKET-ID>-<kebab-slug>.md`
- Dated research docs (non-ticket): `YYYY-MM-DD-<kebab-slug>.md`

**Files:**
- Create: `journals/vawn/briefings/`, `journals/vawn/health/`, `journals/vawn/discovery/`
- Move + rename: all `Daily Briefing*.md` → `journals/vawn/briefings/YYYY-MM-DD-daily-briefing.md`
- Move + rename: all `Discovery Brief*.md` → `journals/vawn/discovery/YYYY-MM-DD-discovery-brief.md`
- Move + rename: all `Health*.md` → `journals/vawn/health/YYYY-MM-DD-health.md`
- Rename in place: `research/vawn/briefings/APU-107_Mix_Engine_Enhancement_Research.md` → `research/vawn/APU-107-mix-engine-enhancement-research.md`
- Rename in place: `research/vawn/briefings/APU-108_Hip_Hop_Mix_AI_Prompting_Research.md` → `research/vawn/APU-108-hip-hop-mix-ai-prompting-research.md`
- Rename in place: `research/vawn/briefings/Mix Engine Pro Alignment -- 2026-04-12.md` → `research/vawn/2026-04-12-mix-engine-pro-alignment.md`
- Rename in place: `research/vawn/briefings/Higgsfield-Seedance-Best-Practices-2026-04-10.md` → `research/vawn/2026-04-10-higgsfield-seedance-best-practices.md`
- Delete: empty `research/vawn/briefings/`, `research/vawn/discovery/`

- [ ] **Step 1: Create journals/vawn/ subfolders**

```bash
powershell -Command "
New-Item -ItemType Directory -Force -Path 'C:\Users\rdyal\Apulu Universe\journals\vawn\briefings' | Out-Null
New-Item -ItemType Directory -Force -Path 'C:\Users\rdyal\Apulu Universe\journals\vawn\health' | Out-Null
New-Item -ItemType Directory -Force -Path 'C:\Users\rdyal\Apulu Universe\journals\vawn\discovery' | Out-Null
"
```

- [ ] **Step 2: Inventory source files before moving**

```bash
cd "C:/Users/rdyal/Apulu Universe" && ls research/vawn/briefings/ && echo "---" && ls research/vawn/discovery/
```
This is diagnostic — note what's there so you can verify after.

- [ ] **Step 3: Move + rename daily briefings**

```bash
powershell -Command "
\$src = 'C:\Users\rdyal\Apulu Universe\research\vawn\briefings'
\$dst = 'C:\Users\rdyal\Apulu Universe\journals\vawn\briefings'
Get-ChildItem -Path \$src -Filter 'Daily Briefing*.md' | ForEach-Object {
  if (\$_.Name -match '(\d{4}-\d{2}-\d{2})') {
    \$date = \$matches[1]
    \$newName = \"\$date-daily-briefing.md\"
    Move-Item -Path \$_.FullName -Destination (Join-Path \$dst \$newName)
    Write-Host (\"-> \$newName\")
  } else {
    Write-Host (\"WARN: No date in \" + \$_.Name + ' — not moved')
  }
}
"
```

- [ ] **Step 4: Move + rename discovery briefs**

```bash
powershell -Command "
\$src = 'C:\Users\rdyal\Apulu Universe\research\vawn\discovery'
\$dst = 'C:\Users\rdyal\Apulu Universe\journals\vawn\discovery'
Get-ChildItem -Path \$src -Filter '*.md' | Where-Object { \$_.Name -match 'Discovery Brief' } | ForEach-Object {
  if (\$_.Name -match '(\d{4}-\d{2}-\d{2})') {
    \$date = \$matches[1]
    \$newName = \"\$date-discovery-brief.md\"
    Move-Item -Path \$_.FullName -Destination (Join-Path \$dst \$newName)
    Write-Host (\"-> \$newName\")
  } else {
    Write-Host (\"WARN: No date in \" + \$_.Name + ' — not moved')
  }
}
"
```

- [ ] **Step 5: Move + rename health notes**

```bash
powershell -Command "
\$src = 'C:\Users\rdyal\Apulu Universe\research\vawn\briefings'
\$dst = 'C:\Users\rdyal\Apulu Universe\journals\vawn\health'
Get-ChildItem -Path \$src -Filter 'Health*.md' | ForEach-Object {
  if (\$_.Name -match '(\d{4}-\d{2}-\d{2})') {
    \$date = \$matches[1]
    \$newName = \"\$date-health.md\"
    Move-Item -Path \$_.FullName -Destination (Join-Path \$dst \$newName)
    Write-Host (\"-> \$newName\")
  } else {
    Write-Host (\"WARN: No date in \" + \$_.Name + ' — not moved')
  }
}
"
```

- [ ] **Step 6: Rename research tickets and dated research docs**

```bash
powershell -Command "
\$renames = @(
  @{ Src='C:\Users\rdyal\Apulu Universe\research\vawn\briefings\APU-107_Mix_Engine_Enhancement_Research.md'; Dst='C:\Users\rdyal\Apulu Universe\research\vawn\APU-107-mix-engine-enhancement-research.md' },
  @{ Src='C:\Users\rdyal\Apulu Universe\research\vawn\briefings\APU-108_Hip_Hop_Mix_AI_Prompting_Research.md'; Dst='C:\Users\rdyal\Apulu Universe\research\vawn\APU-108-hip-hop-mix-ai-prompting-research.md' },
  @{ Src='C:\Users\rdyal\Apulu Universe\research\vawn\briefings\Mix Engine Pro Alignment -- 2026-04-12.md'; Dst='C:\Users\rdyal\Apulu Universe\research\vawn\2026-04-12-mix-engine-pro-alignment.md' },
  @{ Src='C:\Users\rdyal\Apulu Universe\research\vawn\briefings\Higgsfield-Seedance-Best-Practices-2026-04-10.md'; Dst='C:\Users\rdyal\Apulu Universe\research\vawn\2026-04-10-higgsfield-seedance-best-practices.md' }
)
foreach (\$r in \$renames) {
  if (Test-Path \$r.Src) {
    Move-Item -Path \$r.Src -Destination \$r.Dst
    Write-Host ('Renamed: ' + (Split-Path -Leaf \$r.Src) + ' -> ' + (Split-Path -Leaf \$r.Dst))
  } else {
    Write-Host ('SKIP (not found): ' + \$r.Src)
  }
}
"
```

- [ ] **Step 7: Verify briefings/ and discovery/ are empty, then remove**

```bash
powershell -Command "
foreach (\$p in @('C:\Users\rdyal\Apulu Universe\research\vawn\briefings','C:\Users\rdyal\Apulu Universe\research\vawn\discovery')) {
  if (Test-Path \$p) {
    \$children = Get-ChildItem -Path \$p -Force
    if (\$children.Count -eq 0) {
      Remove-Item -Path \$p -Force
      Write-Host ('Removed empty: ' + \$p)
    } else {
      Write-Host ('Not empty, left in place: ' + \$p)
      \$children | Select-Object Name | Format-Table -AutoSize
    }
  }
}
"
```

- [ ] **Step 8: Verify final structure**

```bash
cd "C:/Users/rdyal/Apulu Universe" && echo "=== journals/vawn ===" && find journals/vawn -type f | sort && echo "" && echo "=== research/vawn ===" && ls research/vawn/
```

- [ ] **Step 9: Commit**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git add -A && git commit -m "chore(vault): restructure research/ into journals/ and research/ with standardized naming"
```

---

## Task D: Move Vawn lyrics catalog to catalogs/

**Files:**
- Create: `catalogs/`
- Move: `research/vawn/catalog/Vawn Lyrics Catalog.md` → `catalogs/vawn-lyrics.md`
- Delete: empty `research/vawn/catalog/` (if empty after move)

- [ ] **Step 1: Create `catalogs/` and move file**

```bash
powershell -Command "
New-Item -ItemType Directory -Force -Path 'C:\Users\rdyal\Apulu Universe\catalogs' | Out-Null
Move-Item -Path 'C:\Users\rdyal\Apulu Universe\research\vawn\catalog\Vawn Lyrics Catalog.md' -Destination 'C:\Users\rdyal\Apulu Universe\catalogs\vawn-lyrics.md'
"
```

- [ ] **Step 2: Remove empty `research/vawn/catalog/` if empty**

```bash
powershell -Command "
\$p = 'C:\Users\rdyal\Apulu Universe\research\vawn\catalog'
if (Test-Path \$p) {
  \$children = Get-ChildItem -Path \$p -Force
  if (\$children.Count -eq 0) {
    Remove-Item -Path \$p -Force
    Write-Host ('Removed empty: ' + \$p)
  } else {
    Write-Host ('Not empty, left in place: ' + \$p)
    \$children | Select-Object Name | Format-Table -AutoSize
  }
}
"
```

- [ ] **Step 3: Commit**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git add -A && git commit -m "chore(vault): move Vawn lyrics catalog to catalogs/"
```

---

## Task E: Add frontmatter to all time-stamped and hub notes

**Intent:** Add minimal frontmatter to the 5 note types that need it for Claude retrieval. Use idempotent scripts (skip files that already have frontmatter) so the task is safely re-runnable.

**Frontmatter schemas:**

Daily briefings (`journals/vawn/briefings/*.md`):
```yaml
---
date: <YYYY-MM-DD from filename>
type: daily-briefing
briefing-for: vawn
---
```

Health notes (`journals/vawn/health/*.md`):
```yaml
---
date: <YYYY-MM-DD from filename>
type: health
briefing-for: vawn
---
```

Discovery briefs (`journals/vawn/discovery/*.md`):
```yaml
---
date: <YYYY-MM-DD from filename>
type: discovery
briefing-for: vawn
---
```

Research tickets and dated research docs (`research/vawn/*.md`):
- APU-107: `ticket: APU-107`, `type: research`, `status: closed`, `updated: 2026-04-14`
- APU-108: `ticket: APU-108`, `type: research`, `status: closed`, `updated: 2026-04-14`
- 2026-04-12 mix engine pro alignment: `type: research`, `status: closed`, `updated: 2026-04-12` (no ticket field)
- 2026-04-10 higgsfield seedance: `type: research`, `status: closed`, `updated: 2026-04-10` (no ticket field)

Topic hubs (`wiki/_master-index.md`, `wiki/*/_index.md`):
```yaml
---
type: hub
topic: <slug>
---
```
Slug is the folder name (e.g., `vawn-mix-engine`, `apulu-prompt-generator`). For `wiki/_master-index.md`, slug is `wiki-root`.

**Files:**
- Create: `scripts/add-frontmatter-journals.ps1` (one script for all 3 journal types)
- Modify: every file in `journals/vawn/briefings/`, `journals/vawn/health/`, `journals/vawn/discovery/`
- Modify: 4 files in `research/vawn/` (APU-107, APU-108, 2026-04-12 mix, 2026-04-10 higgs)
- Modify: `wiki/_master-index.md` and 6 `wiki/*/_index.md` files

- [ ] **Step 1: Write journal frontmatter helper script**

Create `C:/Users/rdyal/Apulu Universe/scripts/add-frontmatter-journals.ps1`:

```powershell
# Idempotent: skips files that already start with frontmatter.
# Covers journals/vawn/{briefings,health,discovery} with appropriate type values.
$specs = @(
    @{ Dir = 'C:\Users\rdyal\Apulu Universe\journals\vawn\briefings'; Pattern = '^(\d{4}-\d{2}-\d{2})-daily-briefing\.md$'; Type = 'daily-briefing' },
    @{ Dir = 'C:\Users\rdyal\Apulu Universe\journals\vawn\health'; Pattern = '^(\d{4}-\d{2}-\d{2})-health\.md$'; Type = 'health' },
    @{ Dir = 'C:\Users\rdyal\Apulu Universe\journals\vawn\discovery'; Pattern = '^(\d{4}-\d{2}-\d{2})-discovery-brief\.md$'; Type = 'discovery' }
)
foreach ($spec in $specs) {
    if (-not (Test-Path $spec.Dir)) { continue }
    Get-ChildItem -Path $spec.Dir -Filter '*.md' | ForEach-Object {
        $content = Get-Content -Path $_.FullName -Raw
        if ($content -match '^---\s*\r?\n') {
            Write-Host ("Skip (already has frontmatter): " + $_.Name)
            return
        }
        if ($_.Name -match $spec.Pattern) {
            $date = $matches[1]
            $fm = "---`ndate: $date`ntype: $($spec.Type)`nbriefing-for: vawn`n---`n`n"
            Set-Content -Path $_.FullName -Value ($fm + $content) -NoNewline
            Write-Host ("Added FM [" + $spec.Type + "]: " + $_.Name)
        } else {
            Write-Host ("Pattern mismatch (not touching): " + $_.Name)
        }
    }
}
```

- [ ] **Step 2: Run the journal frontmatter script**

```bash
powershell -ExecutionPolicy Bypass -File "C:/Users/rdyal/Apulu Universe/scripts/add-frontmatter-journals.ps1"
```
Expected: one "Added FM [type]: filename" line per file; no pattern mismatches.

- [ ] **Step 3: Spot-check one file of each type**

```bash
cd "C:/Users/rdyal/Apulu Universe" && for dir in journals/vawn/briefings journals/vawn/health journals/vawn/discovery; do echo "=== $dir ==="; head -6 "$(ls "$dir"/*.md | head -1)"; done
```
Expected: each file starts with `---` frontmatter including `date:`, `type:`, `briefing-for:`.

- [ ] **Step 4: Add frontmatter to research tickets**

For each of the 4 research files, use the `Edit` tool to prepend the appropriate frontmatter block (see schemas above) plus a blank line.

Target files:
- `research/vawn/APU-107-mix-engine-enhancement-research.md`
- `research/vawn/APU-108-hip-hop-mix-ai-prompting-research.md`
- `research/vawn/2026-04-12-mix-engine-pro-alignment.md`
- `research/vawn/2026-04-10-higgsfield-seedance-best-practices.md`

Before prepending, read each file to verify it doesn't already have frontmatter. If it does, skip.

- [ ] **Step 5: Verify research frontmatter**

```bash
cd "C:/Users/rdyal/Apulu Universe" && for f in research/vawn/*.md; do echo "=== $f ==="; head -6 "$f"; done
```
Expected: all 4 files start with `---` frontmatter.

- [ ] **Step 6: Add frontmatter to topic hubs**

For each of these 7 files, prepend `---\ntype: hub\ntopic: <slug>\n---\n\n`:

- `wiki/_master-index.md` — `topic: wiki-root`
- `wiki/ai-filmmaking/_index.md` — `topic: ai-filmmaking`
- `wiki/apulu-prompt-generator/_index.md` — `topic: apulu-prompt-generator`
- `wiki/cross-topic/_index.md` — `topic: cross-topic`
- `wiki/design-engineering/_index.md` — `topic: design-engineering`
- `wiki/vawn-mix-engine/_index.md` — `topic: vawn-mix-engine`
- `wiki/vawn-project/_index.md` — `topic: vawn-project`

Before prepending, read each file to verify it doesn't already have frontmatter. If it does, skip.

- [ ] **Step 7: Verify hub frontmatter**

```bash
cd "C:/Users/rdyal/Apulu Universe" && for f in wiki/_master-index.md wiki/*/_index.md; do echo "=== $f ==="; head -4 "$f"; done
```
Expected: every hub file starts with `type: hub` frontmatter.

- [ ] **Step 8: Commit**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git add -A && git commit -m "feat(vault): add frontmatter to journals, research tickets, and topic hubs"
```

---

## Task F: Write VAULT.md at vault root

**Files:**
- Create: `VAULT.md`

- [ ] **Step 1: Create the file**

Write `C:/Users/rdyal/Apulu Universe/VAULT.md` with the following exact content:

```markdown
# Apulu Universe Vault

Knowledge base for Claude. **Read this first when starting any project.**

## How to use this vault

1. Identify the project domain (see table below).
2. Read the matching topic hub at `wiki/<topic>/_index.md`.
3. Follow links from the hub to deeper notes as needed.
4. For daily context, check `journals/vawn/briefings/` for the most recent entries.

## Domain → Hub Map

| If the project involves... | Start with |
|---|---|
| Vawn mixing, mastering, iZotope plugins | [wiki/vawn-mix-engine/_index.md](wiki/vawn-mix-engine/_index.md) |
| Vawn as an artist (music, releases, identity, videos) | [wiki/vawn-project/_index.md](wiki/vawn-project/_index.md) |
| Apulu Prompt Generator web app | [wiki/apulu-prompt-generator/_index.md](wiki/apulu-prompt-generator/_index.md) |
| AI video/film (Higgsfield, Kling, Seedance) | [wiki/ai-filmmaking/_index.md](wiki/ai-filmmaking/_index.md) |
| Design engineering, frontend quality | [wiki/design-engineering/_index.md](wiki/design-engineering/_index.md) |
| Prompt engineering, creative pipelines | [wiki/cross-topic/_index.md](wiki/cross-topic/_index.md) |
| Apulu Records operations (labels, deals, A&R) | `paperclip/` (separate workspace, out of vault reorganization scope) |

## Recent context for Vawn work

- **Latest daily briefing:** newest file in `journals/vawn/briefings/` — sorted by filename (YYYY-MM-DD-daily-briefing.md)
- **Latest health note:** newest file in `journals/vawn/health/`
- **Latest discovery brief:** newest file in `journals/vawn/discovery/`

## Research tickets

Formal research lives in `research/vawn/` (APU-xxx tickets and dated research docs).

## Reference catalogs

Structured reference material lives in `catalogs/` (e.g., `catalogs/vawn-lyrics.md`).

## Anti-patterns — do NOT do these

- Don't read `research/` before checking if `wiki/` has a digested version of the same subject.
- Don't read pipeline JSON outputs in `pipeline/output/` — they're raw machine data, not knowledge.
- Don't treat files in `paperclip/` as part of this vault's knowledge layer; it's a separate workspace with its own structure.
- Don't add frontmatter to reference notes in `wiki/` — folders and hubs are the filter.
```

- [ ] **Step 2: Commit**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git add VAULT.md && git commit -m "feat(vault): add VAULT.md root entry point with domain->hub map"
```

---

## Task G: Rewrite all topic hubs

**Intent:** Replace each topic's `_index.md` body (preserving the frontmatter added in Task E) with a standardized structure: "When to reference", "Reading order for Claude", "Notes in this topic" (with one-line summaries), "Related hubs". Also rewrite `wiki/_master-index.md` as a lightweight topic list.

**Files:**
- Modify: `wiki/_master-index.md`
- Modify: `wiki/ai-filmmaking/_index.md`
- Modify: `wiki/apulu-prompt-generator/_index.md`
- Modify: `wiki/cross-topic/_index.md`
- Modify: `wiki/design-engineering/_index.md`
- Modify: `wiki/vawn-mix-engine/_index.md`
- Modify: `wiki/vawn-project/_index.md`

### Standard hub body (after frontmatter)

Each hub follows this structure (content obviously varies):

```markdown
# <Topic Name>

## When to reference this hub

<1–2 sentences: what projects/questions should start here>

## Reading order for Claude

1. This file (context + scope).
2. [[note-a]] — <one-line what>.
3. [[note-b]] — <one-line what>.
4. ... (optional)

## Notes in this topic

- **[[note-a]]** — <one-line summary>.
- **[[note-b]]** — <one-line summary>.

## Related hubs

- [[../other-topic/_index]] — <relationship>.
```

### Per-hub content

**`wiki/_master-index.md`** (topic: wiki-root) — lightweight topic list:

```markdown
# Wiki Root

Entry point for the `wiki/` folder. For vault-wide entry, read `../VAULT.md` instead.

## Topic hubs

- [[ai-filmmaking/_index]] — AI video generation (Higgsfield, Kling, Seedance).
- [[apulu-prompt-generator/_index]] — the web app at `projects/apulu-prompt-generator/`.
- [[cross-topic/_index]] — cross-cutting pipeline and prompt-engineering patterns.
- [[design-engineering/_index]] — frontend design quality and polish.
- [[vawn-mix-engine/_index]] — Vawn mixing and mastering.
- [[vawn-project/_index]] — Vawn as an artist.
```

**`wiki/ai-filmmaking/_index.md`:**

```markdown
# AI Filmmaking

## When to reference this hub

Start here for any project involving AI video generation — Higgsfield Cinema Studio, Kling, Seedance, or AI-generated film/music-video work. Also for prompt engineering specific to cinematic video output.

## Reading order for Claude

1. This file (context + scope).
2. [[ai-short-film-prompt-library]] — catalog of working prompts by shot type.
3. [[higgsfield-vs-kling]] — platform comparison, capability differences.

## Notes in this topic

- **[[ai-short-film-prompt-library]]** — Working prompt library for short-film generation organized by shot/lens/mood.
- **[[higgsfield-vs-kling]]** — Comparison of Higgsfield Cinema Studio vs. Kling: strengths, failure modes, use-case fit.

## Related hubs

- [[../cross-topic/_index]] — broader prompt engineering patterns that apply across AI tools.
- [[../vawn-project/_index]] — when AI video is for Vawn music videos specifically.
```

**`wiki/apulu-prompt-generator/_index.md`:**

```markdown
# Apulu Prompt Generator

## When to reference this hub

Start here for any work on the Apulu Prompt Generator web app at `C:\Users\rdyal\Apulu Universe\projects\apulu-prompt-generator\`. Covers architecture, deployment, style system, UI modes, and internal agents.

## Reading order for Claude

1. This file (context + scope).
2. [[overview]] — what the app does, user-facing features.
3. [[architecture-and-deployment]] — system structure, how it ships.
4. [[agent-deep-dives]] — internal agent details (required before modifying agents).
5. [[style-system]] — design tokens and style conventions.
6. [[ui-modes-and-pipeline]] — UI state model and request pipeline.

## Notes in this topic

- **[[overview]]** — Product overview and capabilities.
- **[[architecture-and-deployment]]** — Architecture, deploy targets (Vercel/Render), env config.
- **[[agent-deep-dives]]** — Detailed breakdowns of each agent in the pipeline.
- **[[style-system]]** — Tokens, fonts, components, design conventions.
- **[[ui-modes-and-pipeline]]** — UI modes, state machine, prompt pipeline flow.

## Related hubs

- [[../cross-topic/_index]] — consistency patterns and creative-pipeline engineering that inform this app.
- [[../design-engineering/_index]] — frontend quality standards this app aims at.
```

**`wiki/cross-topic/_index.md`:**

```markdown
# Cross-Topic Patterns

## When to reference this hub

Start here for cross-cutting concerns that apply to multiple projects: general prompt-engineering principles, consistency patterns across AI outputs, and creative-pipeline design. Use this hub when no single topic hub is a clean fit for the question at hand.

## Reading order for Claude

1. This file (context).
2. [[creative-pipelines-and-prompt-engineering]] — pipeline design and prompt-engineering fundamentals.
3. [[consistency-patterns]] — techniques for consistent output across AI generations (character, style, wardrobe, etc.).

## Notes in this topic

- **[[creative-pipelines-and-prompt-engineering]]** — General principles for designing creative AI pipelines and writing effective prompts.
- **[[consistency-patterns]]** — Patterns for holding identity, style, or wardrobe constant across multiple generations.

## Related hubs

- [[../ai-filmmaking/_index]] — AI video-specific prompting patterns.
- [[../apulu-prompt-generator/_index]] — applied pipeline engineering in a specific web app.
```

**`wiki/design-engineering/_index.md`:**

```markdown
# Design Engineering

## When to reference this hub

Start here for frontend design quality, UI polish standards, animation decisions, and the principles behind high-taste interface work. Apply when building UI or reviewing design quality.

## Reading order for Claude

1. This file (context).
2. [[impeccable-frontend-design]] — comprehensive design quality standards.
3. [[emil-kowalski-philosophy]] — UI polish and motion philosophy.

## Notes in this topic

- **[[impeccable-frontend-design]]** — Standards and rules for production-grade frontend work (typography, spacing, components, motion).
- **[[emil-kowalski-philosophy]]** — Philosophy and principles behind UI polish and component design.

## Related hubs

- [[../apulu-prompt-generator/_index]] — the live web app where these principles are applied.
```

**`wiki/vawn-mix-engine/_index.md`:**

```markdown
# Vawn Mix Engine

## When to reference this hub

Start here for any Vawn mixing, mastering, or iZotope-plugin work. Covers the mix-engine architecture, gain-staging standards, plugin usage, and session-log/mix-report conventions.

## Reading order for Claude

1. This file (context).
2. [[overview-and-architecture]] — end-to-end mix-engine architecture and data flow.
3. [[levels-and-gain-staging]] — target levels, LUFS, gain-staging rules.
4. [[izotope-plugin-guide]] — iZotope plugin roles and parameter conventions.
5. [[mix-report-and-session-log]] — reporting format and session log schema.

## Notes in this topic

- **[[overview-and-architecture]]** — Mix-engine architecture, stages, and data flow between modules.
- **[[levels-and-gain-staging]]** — Gain-staging standards; target LUFS -7.5, headroom rules.
- **[[izotope-plugin-guide]]** — iZotope plugins (RX 11, Nectar 4, Neutron 5, TBC3, Ozone 12) — what each does in the chain.
- **[[mix-report-and-session-log]]** — Format and schema for mix reports and session logs.

## Related hubs

- [[../vawn-project/_index]] — Vawn as an artist; sessions belong to tracks from this project.
```

**`wiki/vawn-project/_index.md`:**

```markdown
# Vawn Project

## When to reference this hub

Start here for anything about Vawn as an artist — identity, music catalog, releases, videos, social content, brand direction. For mixing-specific work, go to [[../vawn-mix-engine/_index]].

## Reading order for Claude

1. This file (context).
2. [[overview]] — who Vawn is, sound, positioning.
3. [[Noir Music Video Production Package]] — when current music-video work is relevant.

## Notes in this topic

- **[[overview]]** — Vawn project overview: artist identity, sound, positioning, current phase.
- **[[Noir Music Video Production Package]]** — Production package and creative brief for the noir music video series.

## Related hubs

- [[../vawn-mix-engine/_index]] — mixing and mastering for Vawn tracks.
- [[../ai-filmmaking/_index]] — AI video tooling used for Vawn visuals.
- [[../cross-topic/_index]] — pipeline and prompt patterns used in Vawn content production.

## Related catalogs and journals

- `catalogs/vawn-lyrics.md` — full lyrics catalog.
- `journals/vawn/briefings/` — daily briefings on Vawn status and activity.
- `journals/vawn/discovery/` — discovery research briefs.
- `journals/vawn/health/` — daily health notes.
```

- [ ] **Step 1: Rewrite each hub**

For each of the 7 files listed above: read the current content, preserve the frontmatter block from Task E (lines `---` to `---`), replace everything after the frontmatter with the corresponding new body content from the spec above.

- [ ] **Step 2: Verify all hubs have both frontmatter and new body**

```bash
cd "C:/Users/rdyal/Apulu Universe" && for f in wiki/_master-index.md wiki/*/_index.md; do echo "=== $f ==="; head -10 "$f"; echo ""; done
```

- [ ] **Step 3: Verify linked notes exist**

```bash
cd "C:/Users/rdyal/Apulu Universe" && for dir in ai-filmmaking apulu-prompt-generator cross-topic design-engineering vawn-mix-engine vawn-project; do echo "=== wiki/$dir ==="; ls wiki/$dir/*.md 2>&1; done
```
Expected: every file referenced in the hubs exists in its folder.

- [ ] **Step 4: Commit**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git add -A && git commit -m "feat(vault): rewrite all topic hubs with reading order and note summaries"
```

---

## Task H: Archive audit

**Intent:** Apply the supersession rule to the 3 existing files in `wiki-archive/`. Each gets a supersession pointer or is deleted.

**Files:**
- Modify: `wiki-archive/emil-design-eng-skill.md`
- Modify OR Delete: `wiki-archive/higgsfield-ai-short-film-guide.md`
- Modify: `wiki-archive/impeccable-frontend-design-skill.md`

### Decision table

| File | Action | Supersession target |
|---|---|---|
| `emil-design-eng-skill.md` | Add pointer | `C:/Users/rdyal/.claude/skills/emil-design-eng/SKILL.md` (external target is OK) |
| `higgsfield-ai-short-film-guide.md` | Compare content against `wiki/ai-filmmaking/ai-short-film-prompt-library.md`. If superseded, add pointer. If not superseded, delete (no orphaned archives per spec rule). | TBD by inspection |
| `impeccable-frontend-design-skill.md` | Add pointer | `[[../wiki/design-engineering/impeccable-frontend-design]]` |

- [ ] **Step 1: Add pointer to emil-design-eng-skill.md**

Use `Edit` tool to prepend this line, followed by a blank line, to `wiki-archive/emil-design-eng-skill.md`:

```markdown
> **Archived 2026-04-14.** Superseded by `C:/Users/rdyal/.claude/skills/emil-design-eng/SKILL.md`.
```

- [ ] **Step 2: Decide and act on higgsfield-ai-short-film-guide.md**

Read both files:

```bash
cd "C:/Users/rdyal/Apulu Universe" && echo "=== ARCHIVED ===" && cat wiki-archive/higgsfield-ai-short-film-guide.md && echo "" && echo "=== CURRENT ===" && cat wiki/ai-filmmaking/ai-short-film-prompt-library.md
```

If the current note fully covers the archived one's subject matter → prepend a pointer line:

```markdown
> **Archived 2026-04-14.** Superseded by [[../wiki/ai-filmmaking/ai-short-film-prompt-library]].
```

If the archived note contains material not covered in the current one → delete the archive file (the supersession rule forbids orphans; if needed content is lost, record in `.migration-notes.md` for later merging):

```bash
powershell -Command "Remove-Item -Force 'C:\Users\rdyal\Apulu Universe\wiki-archive\higgsfield-ai-short-film-guide.md'"
```

Record your decision (kept with pointer OR deleted, with reasoning) in `.migration-notes.md`.

- [ ] **Step 3: Add pointer to impeccable-frontend-design-skill.md**

Use `Edit` tool to prepend to `wiki-archive/impeccable-frontend-design-skill.md`:

```markdown
> **Archived 2026-04-14.** Superseded by [[../wiki/design-engineering/impeccable-frontend-design]].
```

- [ ] **Step 4: Verify**

```bash
cd "C:/Users/rdyal/Apulu Universe" && for f in wiki-archive/*.md; do echo "=== $f ==="; head -3 "$f"; done
```
Expected: each remaining file starts with the archive blockquote.

- [ ] **Step 5: Commit**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git add -A && git commit -m "chore(vault): archive audit — add supersession pointers, resolve higgsfield guide"
```

---

## Task I: Final verification, dead-link scan, and tag

**Intent:** Verify the full reorganization is internally consistent. Scan for broken wikilinks. Confirm final structure matches the spec. Tag the completion.

**Files:**
- Create: `scripts/dead-link-check.ps1`
- Inspect only: all `.md` in vault (excluding `paperclip/`, `node_modules/`, `.git/`, `.claude/`)
- Delete: `.migration-notes.md` if clean

- [ ] **Step 1: Write dead-link checker**

Create `C:/Users/rdyal/Apulu Universe/scripts/dead-link-check.ps1`:

```powershell
$root = 'C:\Users\rdyal\Apulu Universe'
$excluded = @('paperclip','node_modules','.git','.claude')
$mdFiles = Get-ChildItem -Path $root -Recurse -Filter '*.md' -File | Where-Object {
    $rel = $_.FullName.Substring($root.Length).TrimStart('\')
    -not ($excluded | Where-Object { $rel.StartsWith($_) })
}

$deadLinks = @()
foreach ($f in $mdFiles) {
    $content = Get-Content -Path $f.FullName -Raw
    $wikilinks = [regex]::Matches($content, '\[\[([^\]\|]+)(?:\|[^\]]*)?\]\]') | ForEach-Object { $_.Groups[1].Value }
    foreach ($link in $wikilinks) {
        $linkFile = if ($link -match '\.md$') { $link } else { "$link.md" }
        $dir = Split-Path -Parent $f.FullName
        $candidate = Join-Path $dir $linkFile
        if (-not (Test-Path $candidate)) {
            $bareName = Split-Path -Leaf $linkFile
            $found = Get-ChildItem -Path $root -Recurse -Filter $bareName -ErrorAction SilentlyContinue | Where-Object {
                $rel = $_.FullName.Substring($root.Length).TrimStart('\')
                -not ($excluded | Where-Object { $rel.StartsWith($_) })
            } | Select-Object -First 1
            if (-not $found) {
                $deadLinks += [PSCustomObject]@{ File = $f.FullName.Substring($root.Length).TrimStart('\'); Link = $link }
            }
        }
    }
}

if ($deadLinks.Count -eq 0) {
    Write-Host "No dead links found."
} else {
    Write-Host ("Dead links: " + $deadLinks.Count)
    $deadLinks | Format-Table -AutoSize
}
```

- [ ] **Step 2: Run scan**

```bash
powershell -ExecutionPolicy Bypass -File "C:/Users/rdyal/Apulu Universe/scripts/dead-link-check.ps1"
```
Expected: "No dead links found." OR a list of broken wikilinks.

- [ ] **Step 3: Fix dead links if any**

For each reported dead link, either correct the target filename in the referencing file, remove the link if the concept no longer exists, or create the referenced file. Re-run Step 2 until clean.

- [ ] **Step 4: Print final top-level structure**

```bash
powershell -Command "Get-ChildItem 'C:\Users\rdyal\Apulu Universe' -Force | Select-Object Name, @{N='Type';E={if(\$_.PSIsContainer){'dir'}else{'file'}}} | Format-Table -AutoSize"
```
Expected: legitimate folders only (no `artists/` — now dissolved; `journals/` and `catalogs/` now present; `VAULT.md` at root; shell-mishap junk gone).

- [ ] **Step 5: Print git log summary**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git log --oneline
```
Expected: commits covering all tasks.

- [ ] **Step 6: Delete `.migration-notes.md` if all findings resolved**

```bash
powershell -Command "Remove-Item -Force 'C:\Users\rdyal\Apulu Universe\.migration-notes.md' -ErrorAction SilentlyContinue"
```

- [ ] **Step 7: Commit cleanup commit (if anything was fixed in Step 3 or Step 6)**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git add -A && git commit -m "chore(vault): final verification and migration-notes cleanup" 2>&1 | tail -5
```
If there's nothing to commit, skip.

- [ ] **Step 8: Tag the reorganization complete**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git tag -a vault-reorg-2026-04-14 -m "Vault reorganization complete (Approach 1.5, compressed execution)"
```

- [ ] **Step 9: Print final tag**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git tag -l -n
```
Expected: `vault-reorg-2026-04-14` listed.
