# Vault Organization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganize the knowledge-note layer of `C:\Users\rdyal\Apulu Universe\` into a hub-centric Obsidian vault optimized for Claude to read before starting any project.

**Architecture:** Approach 1.5 — Hub-Centric with Minimal Frontmatter. `VAULT.md` at root provides a global domain → hub decision map. Each topic in `wiki/` has an `_index.md` hub with reading order and linked-note summaries. Frontmatter is added only to note types where it earns retrieval value (journals, research tickets, hubs). Non-note content (JSON pipeline outputs, config) is evicted from the note layer.

**Tech Stack:** Git, PowerShell (for Windows file ops), bash, grep, markdown.

**Spec:** See `docs/superpowers/specs/2026-04-14-vault-organization-design.md`.

**Working directory:** `C:\Users\rdyal\Apulu Universe`. All paths in this plan are relative to that root unless stated otherwise.

---

## Phase 0: Safety net

### Task 0.1: Initialize git repo at vault root

**Files:**
- Create: `.git/` (via `git init`)
- Create: `.gitignore`

- [ ] **Step 1: Verify no existing `.git` at vault root**

```bash
cd "C:/Users/rdyal/Apulu Universe" && ls -la .git 2>&1 | head -2
```
Expected: `ls: cannot access '.git': No such file or directory`

- [ ] **Step 2: Initialize git repo**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git init && git branch -M main
```
Expected: `Initialized empty Git repository in ...`

- [ ] **Step 3: Write `.gitignore`**

Create `C:/Users/rdyal/Apulu Universe/.gitignore` with contents:

```
# Code / build artifacts
node_modules/
*.log
__pycache__/
*.pyc
.venv/

# Editor
.vscode/
.idea/

# Claude runtime
.claude/worktrees/
.claude/.credentials.json
.claude/scheduled_tasks.lock

# Pipeline outputs (not tracked in vault history)
pipeline/output/

# Paperclip workspace (separate scope, out of reorganization)
paperclip/

# Projects with their own git repos
projects/apulu-prompt-generator/.git/
```

- [ ] **Step 4: Commit `.gitignore`**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git add .gitignore && git commit -m "chore: init vault git repo with gitignore"
```
Expected: commit created, 1 file changed.

---

### Task 0.2: Initial snapshot commit of current state

**Files:**
- All existing files in scope (respecting `.gitignore`)

- [ ] **Step 1: Preview what will be committed**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git status --short | wc -l
```
Expected: a large number (hundreds or thousands of files).

- [ ] **Step 2: Stage everything not gitignored**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git add -A
```

- [ ] **Step 3: Commit snapshot**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git commit -m "chore: initial vault snapshot before reorganization"
```
Expected: commit created with many files.

- [ ] **Step 4: Verify commit**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git log --oneline
```
Expected: 2 commits — `chore: initial vault snapshot ...` and `chore: init vault git repo ...`.

---

## Phase 1: Safe destructive cleanup

### Task 1.1: Delete shell-mishap junk files at vault root

**Files:**
- Delete: zero-byte files at vault root whose names don't match the legitimate allowlist.

- [ ] **Step 1: Inventory junk candidates**

Run this PowerShell script to list candidates:

```bash
powershell -Command "
\$root = 'C:\Users\rdyal\Apulu Universe'
\$legit = @('VAULT.md','CLAUDE.md','.gitignore','.git','.claude','.claude-flow','paperclip','wiki','wiki-archive','research','journals','catalogs','docs','pipeline','scripts','projects','skills','artists','output','raw','agentdb.rvf','agentdb.rvf.lock','Vawn - Noir Music Video Production Package.md')
Get-ChildItem -Path \$root -Force | Where-Object { \$legit -notcontains \$_.Name -and (-not \$_.PSIsContainer) -and \$_.Length -eq 0 } | Select-Object Name, Length | Format-Table -AutoSize
"
```
Expected: list of ~30+ zero-byte junk files (e.g., `'`, `0`, `%+.1f`, `0.01).sum()}`, etc.).

- [ ] **Step 2: Delete the junk files**

```bash
powershell -Command "
\$root = 'C:\Users\rdyal\Apulu Universe'
\$legit = @('VAULT.md','CLAUDE.md','.gitignore','.git','.claude','.claude-flow','paperclip','wiki','wiki-archive','research','journals','catalogs','docs','pipeline','scripts','projects','skills','artists','output','raw','agentdb.rvf','agentdb.rvf.lock','Vawn - Noir Music Video Production Package.md')
\$junk = Get-ChildItem -Path \$root -Force | Where-Object { \$legit -notcontains \$_.Name -and (-not \$_.PSIsContainer) -and \$_.Length -eq 0 }
\$count = \$junk.Count
\$junk | Remove-Item -Force -ErrorAction Continue
Write-Host ('Deleted: ' + \$count + ' junk files')
"
```
Expected: `Deleted: N junk files` where N matches the count from Step 1.

- [ ] **Step 3: Verify remaining top-level is clean**

```bash
powershell -Command "Get-ChildItem 'C:\Users\rdyal\Apulu Universe' -Force | Select-Object Name | Format-Table -AutoSize"
```
Expected: only legitimate folders and files — no more shell-mishap junk.

- [ ] **Step 4: Commit**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git add -A && git commit -m "chore(vault): remove shell-mishap junk files from vault root"
```

---

### Task 1.2: Grep pipeline and scripts for JSON-output path references

**Files:**
- Inspect only: `pipeline/**/*.py`, `pipeline/**/*.json`, `scripts/**/*.py`, `scripts/**/*.json`

- [ ] **Step 1: Find references to `research/vawn/briefings/` or `research/vawn/discovery/`**

```bash
cd "C:/Users/rdyal/Apulu Universe" && grep -rn "research[/\\\\]vawn[/\\\\]\(briefings\|discovery\|catalog\)" pipeline/ scripts/ 2>&1 | head -40
```
Expected output: either zero matches (no code depends on those paths) OR a list of file:line hits showing hardcoded paths that need updating.

- [ ] **Step 2: Record findings**

In a new scratch file `C:/Users/rdyal/Apulu Universe/.migration-notes.md`, record:

```markdown
# Migration notes
## JSON path references (Phase 1.2)
- [list each file:line with the specific path used]
- [OR: "No hardcoded references found"]
```

- [ ] **Step 3: Commit scratch file**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git add .migration-notes.md && git commit -m "chore(vault): record pipeline path audit findings"
```

---

### Task 1.3: Move pipeline JSON outputs to `pipeline/output/`

**Files:**
- Create: `pipeline/output/vawn/{briefings,discovery,catalog}/`
- Move: `research/vawn/briefings/*.json` → `pipeline/output/vawn/briefings/`
- Move: `research/vawn/discovery/*.json` → `pipeline/output/vawn/discovery/`
- Move: `research/vawn/catalog/*.json` → `pipeline/output/vawn/catalog/`
- Modify: pipeline code from Task 1.2 findings (if any)

- [ ] **Step 1: Create destination folders**

```bash
powershell -Command "
New-Item -ItemType Directory -Force -Path 'C:\Users\rdyal\Apulu Universe\pipeline\output\vawn\briefings' | Out-Null
New-Item -ItemType Directory -Force -Path 'C:\Users\rdyal\Apulu Universe\pipeline\output\vawn\discovery' | Out-Null
New-Item -ItemType Directory -Force -Path 'C:\Users\rdyal\Apulu Universe\pipeline\output\vawn\catalog' | Out-Null
"
```

- [ ] **Step 2: Move JSONs from briefings**

```bash
powershell -Command "
\$src = 'C:\Users\rdyal\Apulu Universe\research\vawn\briefings'
\$dst = 'C:\Users\rdyal\Apulu Universe\pipeline\output\vawn\briefings'
Get-ChildItem -Path \$src -Filter '*.json' | Move-Item -Destination \$dst
Write-Host 'Briefings JSONs moved:'; Get-ChildItem \$dst
"
```
Expected: `cos_log_*.json`, `daily_briefing_results.json`, `health_results.json`, etc. listed.

- [ ] **Step 3: Move JSONs from discovery**

```bash
powershell -Command "
\$src = 'C:\Users\rdyal\Apulu Universe\research\vawn\discovery'
\$dst = 'C:\Users\rdyal\Apulu Universe\pipeline\output\vawn\discovery'
Get-ChildItem -Path \$src -Filter '*.json' | Move-Item -Destination \$dst
Write-Host 'Discovery JSONs moved:'; Get-ChildItem \$dst
"
```
Expected: `discovery_brief.json`, `*_pipeline_results.json` listed.

- [ ] **Step 4: Move JSONs from catalog**

```bash
powershell -Command "
\$src = 'C:\Users\rdyal\Apulu Universe\research\vawn\catalog'
\$dst = 'C:\Users\rdyal\Apulu Universe\pipeline\output\vawn\catalog'
Get-ChildItem -Path \$src -Filter '*.json' -ErrorAction SilentlyContinue | Move-Item -Destination \$dst
"
```

- [ ] **Step 5: Update pipeline code references (if any from Task 1.2)**

For each hit recorded in `.migration-notes.md`, replace the old path with the new `pipeline/output/vawn/...` path. Use `Edit` tool per file. If no hits were found in Task 1.2, skip this step.

- [ ] **Step 6: Verify no JSONs remain in research/vawn/briefings|discovery**

```bash
cd "C:/Users/rdyal/Apulu Universe" && find research/vawn -name "*.json" 2>&1 | head -20
```
Expected: empty output (no JSONs in research/vawn/).

- [ ] **Step 7: Commit**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git add -A && git commit -m "chore(vault): relocate pipeline JSON outputs to pipeline/output/"
```

---

## Phase 2: Move non-notes out of the notes layer

### Task 2.1: Grep code for `artists/` path references

**Files:**
- Inspect only: `pipeline/**`, `scripts/**`, `projects/**`

- [ ] **Step 1: Find references**

```bash
cd "C:/Users/rdyal/Apulu Universe" && grep -rn "artists[/\\\\]vawn\|artists\\\\vawn" pipeline/ scripts/ projects/ 2>&1 | head -40
```
Expected: either zero matches or a list of file:line hits.

- [ ] **Step 2: Append findings to `.migration-notes.md`**

Add section:

```markdown
## artists/ path references (Phase 2.1)
- [list file:line hits, OR: "No hardcoded references found"]
```

- [ ] **Step 3: Commit**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git add .migration-notes.md && git commit -m "chore(vault): record artists/ path audit findings"
```

---

### Task 2.2: Move `artists/vawn/` to `projects/vawn/config/`

**Files:**
- Create: `projects/vawn/config/`
- Move: `artists/vawn/*.json` → `projects/vawn/config/`
- Delete: `artists/` (if empty after move)
- Modify: code references from Task 2.1 (if any)

- [ ] **Step 1: Verify current contents of `artists/vawn/`**

```bash
cd "C:/Users/rdyal/Apulu Universe" && ls -la artists/vawn/
```
Expected: 3 JSON files (`config.json`, `content_rules.json`, `pillar_schedule.json`).

- [ ] **Step 2: Create destination and move files**

```bash
powershell -Command "
New-Item -ItemType Directory -Force -Path 'C:\Users\rdyal\Apulu Universe\projects\vawn\config' | Out-Null
Move-Item -Path 'C:\Users\rdyal\Apulu Universe\artists\vawn\*' -Destination 'C:\Users\rdyal\Apulu Universe\projects\vawn\config\'
Write-Host 'Moved. New location contents:'
Get-ChildItem 'C:\Users\rdyal\Apulu Universe\projects\vawn\config'
"
```

- [ ] **Step 3: Remove empty `artists/` tree**

```bash
powershell -Command "
\$path = 'C:\Users\rdyal\Apulu Universe\artists'
if (Test-Path \$path) {
  Remove-Item -Recurse -Force \$path
  Write-Host 'Removed artists/'
}
"
```

- [ ] **Step 4: Update code path references (if any from Task 2.1)**

Edit each file:line recorded in `.migration-notes.md`, replacing `artists/vawn/...` with `projects/vawn/config/...`. Skip this step if no hits.

- [ ] **Step 5: Commit**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git add -A && git commit -m "chore(vault): move artists/vawn config to projects/vawn/config"
```

---

### Task 2.3: Move loose root `.md` files into `wiki/`

**Files:**
- Move: `Vawn - Noir Music Video Production Package.md` → `wiki/vawn-project/Noir Music Video Production Package.md`

- [ ] **Step 1: List loose `.md` files at vault root**

```bash
cd "C:/Users/rdyal/Apulu Universe" && ls *.md 2>/dev/null
```
Expected: `CLAUDE.md` (stays) and `Vawn - Noir Music Video Production Package.md` (moves).

- [ ] **Step 2: Move the Vawn music video note**

```bash
powershell -Command "
Move-Item -Path 'C:\Users\rdyal\Apulu Universe\Vawn - Noir Music Video Production Package.md' -Destination 'C:\Users\rdyal\Apulu Universe\wiki\vawn-project\Noir Music Video Production Package.md'
"
```

- [ ] **Step 3: Verify**

```bash
cd "C:/Users/rdyal/Apulu Universe" && ls wiki/vawn-project/ | grep -i noir
```
Expected: `Noir Music Video Production Package.md` appears.

- [ ] **Step 4: Commit**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git add -A && git commit -m "chore(vault): move loose Vawn noir video note into wiki/vawn-project/"
```

---

## Phase 3: Split research into journals + research

### Task 3.1: Create `journals/vawn/` subfolders

**Files:**
- Create: `journals/vawn/briefings/`
- Create: `journals/vawn/health/`
- Create: `journals/vawn/discovery/`

- [ ] **Step 1: Create folders**

```bash
powershell -Command "
New-Item -ItemType Directory -Force -Path 'C:\Users\rdyal\Apulu Universe\journals\vawn\briefings' | Out-Null
New-Item -ItemType Directory -Force -Path 'C:\Users\rdyal\Apulu Universe\journals\vawn\health' | Out-Null
New-Item -ItemType Directory -Force -Path 'C:\Users\rdyal\Apulu Universe\journals\vawn\discovery' | Out-Null
Get-ChildItem 'C:\Users\rdyal\Apulu Universe\journals\vawn'
"
```
Expected: 3 empty directories listed.

- [ ] **Step 2: Commit empty scaffolding (optional sanity checkpoint)**

Git doesn't track empty folders. Skip a commit here; folders become trackable in subsequent tasks when files land in them.

---

### Task 3.2: Move + rename daily briefings to `journals/vawn/briefings/`

**Files:**
- Move + rename: `research/vawn/briefings/Daily Briefing*.md` → `journals/vawn/briefings/YYYY-MM-DD-daily-briefing.md`

- [ ] **Step 1: List source files**

```bash
cd "C:/Users/rdyal/Apulu Universe" && ls "research/vawn/briefings/" | grep -i "daily briefing"
```
Expected: files like `Daily Briefing - 2026-04-08.md`, `Daily Briefing -- 2026-04-10.md`, etc.

- [ ] **Step 2: Rename-move each file**

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
  }
}
"
```
Expected: each file moved and renamed (e.g., `2026-04-08-daily-briefing.md`).

- [ ] **Step 3: Verify**

```bash
cd "C:/Users/rdyal/Apulu Universe" && ls journals/vawn/briefings/
```
Expected: all briefings now named `YYYY-MM-DD-daily-briefing.md`.

- [ ] **Step 4: Commit**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git add -A && git commit -m "chore(vault): relocate and rename daily briefings to journals/vawn/briefings/"
```

---

### Task 3.3: Move + rename discovery briefs

**Files:**
- Move + rename: `research/vawn/discovery/Discovery Brief*.md` → `journals/vawn/discovery/YYYY-MM-DD-discovery-brief.md`

- [ ] **Step 1: Rename-move each file**

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
  }
}
"
```

- [ ] **Step 2: Verify**

```bash
cd "C:/Users/rdyal/Apulu Universe" && ls journals/vawn/discovery/
```
Expected: all files named `YYYY-MM-DD-discovery-brief.md`.

- [ ] **Step 3: Commit**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git add -A && git commit -m "chore(vault): relocate and rename discovery briefs to journals/vawn/discovery/"
```

---

### Task 3.4: Move + rename health notes

**Files:**
- Move + rename: `research/vawn/briefings/Health*.md` → `journals/vawn/health/YYYY-MM-DD-health.md`

- [ ] **Step 1: Rename-move each file**

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
  }
}
"
```

- [ ] **Step 2: Verify**

```bash
cd "C:/Users/rdyal/Apulu Universe" && ls journals/vawn/health/
```
Expected: all files named `YYYY-MM-DD-health.md`.

- [ ] **Step 3: Commit**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git add -A && git commit -m "chore(vault): relocate and rename health notes to journals/vawn/health/"
```

---

### Task 3.5: Rename APU-xxx research tickets

**Files:**
- Rename: `research/vawn/briefings/APU-107_Mix_Engine_Enhancement_Research.md` → `research/vawn/APU-107-mix-engine-enhancement-research.md`
- Rename: `research/vawn/briefings/APU-108_Hip_Hop_Mix_AI_Prompting_Research.md` → `research/vawn/APU-108-hip-hop-mix-ai-prompting-research.md`
- Rename: `research/vawn/briefings/Mix Engine Pro Alignment -- 2026-04-12.md` — decide: is this a research doc or a journal? If research, rename to `research/vawn/2026-04-12-mix-engine-pro-alignment.md`; if journal, move to `journals/vawn/briefings/2026-04-12-mix-engine-pro-alignment.md`. **Decision:** treat as research (one-off architectural alignment doc).
- Rename: `research/vawn/briefings/Higgsfield-Seedance-Best-Practices-2026-04-10.md` → `research/vawn/2026-04-10-higgsfield-seedance-best-practices.md`

- [ ] **Step 1: Move APU-107 with rename**

```bash
powershell -Command "
Move-Item -Path 'C:\Users\rdyal\Apulu Universe\research\vawn\briefings\APU-107_Mix_Engine_Enhancement_Research.md' -Destination 'C:\Users\rdyal\Apulu Universe\research\vawn\APU-107-mix-engine-enhancement-research.md'
"
```

- [ ] **Step 2: Move APU-108 with rename**

```bash
powershell -Command "
Move-Item -Path 'C:\Users\rdyal\Apulu Universe\research\vawn\briefings\APU-108_Hip_Hop_Mix_AI_Prompting_Research.md' -Destination 'C:\Users\rdyal\Apulu Universe\research\vawn\APU-108-hip-hop-mix-ai-prompting-research.md'
"
```

- [ ] **Step 3: Move Mix Engine Pro Alignment**

```bash
powershell -Command "
Move-Item -Path 'C:\Users\rdyal\Apulu Universe\research\vawn\briefings\Mix Engine Pro Alignment -- 2026-04-12.md' -Destination 'C:\Users\rdyal\Apulu Universe\research\vawn\2026-04-12-mix-engine-pro-alignment.md'
"
```

- [ ] **Step 4: Move Higgsfield best practices**

```bash
powershell -Command "
Move-Item -Path 'C:\Users\rdyal\Apulu Universe\research\vawn\briefings\Higgsfield-Seedance-Best-Practices-2026-04-10.md' -Destination 'C:\Users\rdyal\Apulu Universe\research\vawn\2026-04-10-higgsfield-seedance-best-practices.md'
"
```

- [ ] **Step 5: Verify `research/vawn/briefings/` is now empty (or only contains unknowns)**

```bash
cd "C:/Users/rdyal/Apulu Universe" && ls research/vawn/briefings/ 2>&1
```
Expected: empty listing, OR if non-empty, the remaining files need a dispositional decision. Record anything unexpected in `.migration-notes.md` before proceeding.

- [ ] **Step 6: Remove empty `research/vawn/briefings/` and `research/vawn/discovery/` folders**

```bash
powershell -Command "
foreach (\$p in @('C:\Users\rdyal\Apulu Universe\research\vawn\briefings','C:\Users\rdyal\Apulu Universe\research\vawn\discovery')) {
  if (Test-Path \$p) {
    \$children = Get-ChildItem -Path \$p -Force
    if (\$children.Count -eq 0) { Remove-Item -Path \$p -Force; Write-Host ('Removed empty: ' + \$p) }
    else { Write-Host ('Not empty, skipped: ' + \$p); \$children | Select-Object Name }
  }
}
"
```

- [ ] **Step 7: Commit**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git add -A && git commit -m "chore(vault): rename research tickets to kebab-case and collapse empty briefings/discovery subfolders"
```

---

## Phase 4: Catalogs

### Task 4.1: Create `catalogs/` and move Vawn lyrics catalog

**Files:**
- Create: `catalogs/`
- Move: `research/vawn/catalog/Vawn Lyrics Catalog.md` → `catalogs/vawn-lyrics.md`
- Delete: `research/vawn/catalog/` (if empty after move)

- [ ] **Step 1: Create folder and move file**

```bash
powershell -Command "
New-Item -ItemType Directory -Force -Path 'C:\Users\rdyal\Apulu Universe\catalogs' | Out-Null
Move-Item -Path 'C:\Users\rdyal\Apulu Universe\research\vawn\catalog\Vawn Lyrics Catalog.md' -Destination 'C:\Users\rdyal\Apulu Universe\catalogs\vawn-lyrics.md'
"
```

- [ ] **Step 2: Remove empty `research/vawn/catalog/`**

```bash
powershell -Command "
\$p = 'C:\Users\rdyal\Apulu Universe\research\vawn\catalog'
if (Test-Path \$p) {
  \$children = Get-ChildItem -Path \$p -Force
  if (\$children.Count -eq 0) { Remove-Item -Path \$p -Force; Write-Host ('Removed empty: ' + \$p) }
  else { Write-Host ('Not empty, skipped: ' + \$p); \$children | Select-Object Name }
}
"
```

- [ ] **Step 3: Verify**

```bash
cd "C:/Users/rdyal/Apulu Universe" && ls catalogs/
```
Expected: `vawn-lyrics.md`.

- [ ] **Step 4: Commit**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git add -A && git commit -m "chore(vault): move Vawn lyrics catalog to catalogs/"
```

---

## Phase 5: Frontmatter

### Task 5.1: Add frontmatter to daily briefings

**Files:**
- Modify: every file in `journals/vawn/briefings/`

- [ ] **Step 1: Write a helper script that adds frontmatter idempotently**

Create `C:/Users/rdyal/Apulu Universe/scripts/add-frontmatter-briefings.ps1`:

```powershell
$dir = 'C:\Users\rdyal\Apulu Universe\journals\vawn\briefings'
Get-ChildItem -Path $dir -Filter '*.md' | ForEach-Object {
    $content = Get-Content -Path $_.FullName -Raw
    if ($content -match '^---\s*\n') {
        Write-Host ("Skipping (already has frontmatter): " + $_.Name)
        return
    }
    if ($_.Name -match '^(\d{4}-\d{2}-\d{2})-daily-briefing\.md$') {
        $date = $matches[1]
        $fm = "---`ndate: $date`ntype: daily-briefing`nbriefing-for: vawn`n---`n`n"
        $new = $fm + $content
        Set-Content -Path $_.FullName -Value $new -NoNewline
        Write-Host ("Added frontmatter: " + $_.Name)
    } else {
        Write-Host ("Name pattern mismatch, skipping: " + $_.Name)
    }
}
```

- [ ] **Step 2: Run the script**

```bash
powershell -ExecutionPolicy Bypass -File "C:/Users/rdyal/Apulu Universe/scripts/add-frontmatter-briefings.ps1"
```
Expected: one "Added frontmatter" line per briefing file.

- [ ] **Step 3: Spot-check one file**

```bash
cd "C:/Users/rdyal/Apulu Universe" && head -6 journals/vawn/briefings/*.md | head -10
```
Expected: file starts with `---`, `date:`, `type: daily-briefing`, `briefing-for: vawn`, `---`.

- [ ] **Step 4: Commit**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git add -A && git commit -m "feat(vault): add frontmatter to daily briefings"
```

---

### Task 5.2: Add frontmatter to health notes

**Files:**
- Modify: every file in `journals/vawn/health/`

- [ ] **Step 1: Create helper script**

Create `C:/Users/rdyal/Apulu Universe/scripts/add-frontmatter-health.ps1`:

```powershell
$dir = 'C:\Users\rdyal\Apulu Universe\journals\vawn\health'
Get-ChildItem -Path $dir -Filter '*.md' | ForEach-Object {
    $content = Get-Content -Path $_.FullName -Raw
    if ($content -match '^---\s*\n') {
        Write-Host ("Skipping (already has frontmatter): " + $_.Name)
        return
    }
    if ($_.Name -match '^(\d{4}-\d{2}-\d{2})-health\.md$') {
        $date = $matches[1]
        $fm = "---`ndate: $date`ntype: health`nbriefing-for: vawn`n---`n`n"
        $new = $fm + $content
        Set-Content -Path $_.FullName -Value $new -NoNewline
        Write-Host ("Added frontmatter: " + $_.Name)
    }
}
```

- [ ] **Step 2: Run the script**

```bash
powershell -ExecutionPolicy Bypass -File "C:/Users/rdyal/Apulu Universe/scripts/add-frontmatter-health.ps1"
```

- [ ] **Step 3: Spot-check**

```bash
cd "C:/Users/rdyal/Apulu Universe" && head -6 journals/vawn/health/$(ls journals/vawn/health/ | head -1)
```
Expected: valid frontmatter present.

- [ ] **Step 4: Commit**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git add -A && git commit -m "feat(vault): add frontmatter to health notes"
```

---

### Task 5.3: Add frontmatter to discovery briefs

**Files:**
- Modify: every file in `journals/vawn/discovery/`

- [ ] **Step 1: Create helper script**

Create `C:/Users/rdyal/Apulu Universe/scripts/add-frontmatter-discovery.ps1`:

```powershell
$dir = 'C:\Users\rdyal\Apulu Universe\journals\vawn\discovery'
Get-ChildItem -Path $dir -Filter '*.md' | ForEach-Object {
    $content = Get-Content -Path $_.FullName -Raw
    if ($content -match '^---\s*\n') {
        Write-Host ("Skipping (already has frontmatter): " + $_.Name)
        return
    }
    if ($_.Name -match '^(\d{4}-\d{2}-\d{2})-discovery-brief\.md$') {
        $date = $matches[1]
        $fm = "---`ndate: $date`ntype: discovery`nbriefing-for: vawn`n---`n`n"
        $new = $fm + $content
        Set-Content -Path $_.FullName -Value $new -NoNewline
        Write-Host ("Added frontmatter: " + $_.Name)
    }
}
```

- [ ] **Step 2: Run the script**

```bash
powershell -ExecutionPolicy Bypass -File "C:/Users/rdyal/Apulu Universe/scripts/add-frontmatter-discovery.ps1"
```

- [ ] **Step 3: Spot-check**

```bash
cd "C:/Users/rdyal/Apulu Universe" && head -6 journals/vawn/discovery/$(ls journals/vawn/discovery/ | head -1)
```

- [ ] **Step 4: Commit**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git add -A && git commit -m "feat(vault): add frontmatter to discovery briefs"
```

---

### Task 5.4: Add frontmatter to research tickets

**Files:**
- Modify: `research/vawn/APU-107-mix-engine-enhancement-research.md`
- Modify: `research/vawn/APU-108-hip-hop-mix-ai-prompting-research.md`

Other research files in `research/vawn/` (e.g., `2026-04-12-mix-engine-pro-alignment.md`, `2026-04-10-higgsfield-seedance-best-practices.md`) are dated research docs, not tickets — give them frontmatter matching the research-ticket schema but with `ticket` field omitted (leave `type: research`, `status`, `updated`).

- [ ] **Step 1: Add frontmatter to APU-107**

Use `Edit` tool. Prepend to the file:

```yaml
---
ticket: APU-107
type: research
status: closed
updated: 2026-04-14
---

```
(Then a blank line, then the existing content.)

Verification: the first non-blank existing line of the file should come right after the closing `---` line plus a blank line.

- [ ] **Step 2: Add frontmatter to APU-108**

Use `Edit` tool. Prepend:

```yaml
---
ticket: APU-108
type: research
status: closed
updated: 2026-04-14
---

```

- [ ] **Step 3: Add frontmatter to dated research docs (no ticket)**

For `2026-04-12-mix-engine-pro-alignment.md`, prepend:

```yaml
---
type: research
status: closed
updated: 2026-04-12
---

```

For `2026-04-10-higgsfield-seedance-best-practices.md`, prepend:

```yaml
---
type: research
status: closed
updated: 2026-04-10
---

```

- [ ] **Step 4: Verify all four have frontmatter**

```bash
cd "C:/Users/rdyal/Apulu Universe" && for f in research/vawn/*.md; do echo "=== $f ==="; head -6 "$f"; done
```
Expected: each file starts with `---` and has a valid block.

- [ ] **Step 5: Commit**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git add -A && git commit -m "feat(vault): add frontmatter to research tickets and dated research docs"
```

---

### Task 5.5: Add frontmatter to topic hubs

**Files:**
- Modify: `wiki/_master-index.md` (treat as `wiki/` root hub)
- Modify: `wiki/ai-filmmaking/_index.md`
- Modify: `wiki/apulu-prompt-generator/_index.md`
- Modify: `wiki/cross-topic/_index.md`
- Modify: `wiki/design-engineering/_index.md`
- Modify: `wiki/vawn-mix-engine/_index.md`
- Modify: `wiki/vawn-project/_index.md`

- [ ] **Step 1: Prepend frontmatter to each topic hub**

For each `wiki/<topic>/_index.md`, use `Edit` tool to prepend:

```yaml
---
type: hub
topic: <topic-slug>
---

```

Substitute `<topic-slug>` with the folder name (e.g., `vawn-mix-engine`, `apulu-prompt-generator`).

For `wiki/_master-index.md`, use `topic: wiki-root`.

- [ ] **Step 2: Verify**

```bash
cd "C:/Users/rdyal/Apulu Universe" && for f in wiki/_master-index.md wiki/*/_index.md; do echo "=== $f ==="; head -4 "$f"; done
```
Expected: each file starts with frontmatter containing `type: hub` and a `topic:` field.

- [ ] **Step 3: Commit**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git add -A && git commit -m "feat(vault): add frontmatter to topic hubs"
```

---

## Phase 6: Hub authoring

### Task 6.1: Write `VAULT.md` at vault root

**Files:**
- Create: `VAULT.md`

- [ ] **Step 1: Write file**

Create `C:/Users/rdyal/Apulu Universe/VAULT.md` with content:

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

### Task 6.2: Rewrite `wiki/ai-filmmaking/_index.md`

**Files:**
- Modify: `wiki/ai-filmmaking/_index.md`

- [ ] **Step 1: Read existing content and note all linked files**

```bash
cd "C:/Users/rdyal/Apulu Universe" && cat wiki/ai-filmmaking/_index.md && echo "---" && ls wiki/ai-filmmaking/
```
Expected: current hub content + list of notes in the folder. Existing notes: `ai-short-film-prompt-library.md`, `higgsfield-vs-kling.md`.

- [ ] **Step 2: Rewrite the hub**

Replace the entire file content (preserving the frontmatter from Task 5.5) with:

```markdown
---
type: hub
topic: ai-filmmaking
---

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

- [ ] **Step 3: Verify links resolve (filenames exist in folder)**

```bash
cd "C:/Users/rdyal/Apulu Universe" && ls wiki/ai-filmmaking/*.md
```
Expected: both linked filenames (`ai-short-film-prompt-library.md`, `higgsfield-vs-kling.md`) exist.

- [ ] **Step 4: Commit**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git add wiki/ai-filmmaking/_index.md && git commit -m "feat(vault): rewrite ai-filmmaking hub with reading order and note summaries"
```

---

### Task 6.3: Rewrite `wiki/apulu-prompt-generator/_index.md`

**Files:**
- Modify: `wiki/apulu-prompt-generator/_index.md`

- [ ] **Step 1: Inspect folder contents**

```bash
cd "C:/Users/rdyal/Apulu Universe" && ls wiki/apulu-prompt-generator/
```
Expected notes: `agent-deep-dives.md`, `architecture-and-deployment.md`, `overview.md`, `style-system.md`, `ui-modes-and-pipeline.md`.

- [ ] **Step 2: Rewrite the hub**

Replace file content with:

```markdown
---
type: hub
topic: apulu-prompt-generator
---

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

- [ ] **Step 3: Verify links**

```bash
cd "C:/Users/rdyal/Apulu Universe" && ls wiki/apulu-prompt-generator/*.md
```
Expected: all 5 linked filenames present.

- [ ] **Step 4: Commit**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git add wiki/apulu-prompt-generator/_index.md && git commit -m "feat(vault): rewrite apulu-prompt-generator hub"
```

---

### Task 6.4: Rewrite `wiki/cross-topic/_index.md`

**Files:**
- Modify: `wiki/cross-topic/_index.md`

- [ ] **Step 1: Inspect folder contents**

```bash
cd "C:/Users/rdyal/Apulu Universe" && ls wiki/cross-topic/
```
Expected notes: `consistency-patterns.md`, `creative-pipelines-and-prompt-engineering.md`.

- [ ] **Step 2: Rewrite the hub**

Replace file content with:

```markdown
---
type: hub
topic: cross-topic
---

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

- [ ] **Step 3: Verify + commit**

```bash
cd "C:/Users/rdyal/Apulu Universe" && ls wiki/cross-topic/*.md && git add wiki/cross-topic/_index.md && git commit -m "feat(vault): rewrite cross-topic hub"
```

---

### Task 6.5: Rewrite `wiki/design-engineering/_index.md`

**Files:**
- Modify: `wiki/design-engineering/_index.md`

- [ ] **Step 1: Inspect folder**

```bash
cd "C:/Users/rdyal/Apulu Universe" && ls wiki/design-engineering/
```
Expected notes: `emil-kowalski-philosophy.md`, `impeccable-frontend-design.md`.

- [ ] **Step 2: Rewrite**

Replace file content with:

```markdown
---
type: hub
topic: design-engineering
---

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

- [ ] **Step 3: Verify + commit**

```bash
cd "C:/Users/rdyal/Apulu Universe" && ls wiki/design-engineering/*.md && git add wiki/design-engineering/_index.md && git commit -m "feat(vault): rewrite design-engineering hub"
```

---

### Task 6.6: Rewrite `wiki/vawn-mix-engine/_index.md`

**Files:**
- Modify: `wiki/vawn-mix-engine/_index.md`

- [ ] **Step 1: Inspect folder**

```bash
cd "C:/Users/rdyal/Apulu Universe" && ls wiki/vawn-mix-engine/
```
Expected notes: `izotope-plugin-guide.md`, `levels-and-gain-staging.md`, `mix-report-and-session-log.md`, `overview-and-architecture.md`.

- [ ] **Step 2: Rewrite**

Replace file content with:

```markdown
---
type: hub
topic: vawn-mix-engine
---

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

- [ ] **Step 3: Verify + commit**

```bash
cd "C:/Users/rdyal/Apulu Universe" && ls wiki/vawn-mix-engine/*.md && git add wiki/vawn-mix-engine/_index.md && git commit -m "feat(vault): rewrite vawn-mix-engine hub"
```

---

### Task 6.7: Rewrite `wiki/vawn-project/_index.md`

**Files:**
- Modify: `wiki/vawn-project/_index.md`

- [ ] **Step 1: Inspect folder**

```bash
cd "C:/Users/rdyal/Apulu Universe" && ls wiki/vawn-project/
```
Expected notes: `overview.md`, and `Noir Music Video Production Package.md` (moved in Task 2.3).

- [ ] **Step 2: Rewrite**

Replace file content with:

```markdown
---
type: hub
topic: vawn-project
---

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

- [ ] **Step 3: Verify + commit**

```bash
cd "C:/Users/rdyal/Apulu Universe" && ls wiki/vawn-project/*.md && git add wiki/vawn-project/_index.md && git commit -m "feat(vault): rewrite vawn-project hub"
```

---

### Task 6.8: Update `wiki/_master-index.md`

**Files:**
- Modify: `wiki/_master-index.md`

- [ ] **Step 1: Inspect current content**

```bash
cd "C:/Users/rdyal/Apulu Universe" && cat wiki/_master-index.md
```

- [ ] **Step 2: Rewrite as a lightweight wiki root**

Replace file content with:

```markdown
---
type: hub
topic: wiki-root
---

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

- [ ] **Step 3: Commit**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git add wiki/_master-index.md && git commit -m "feat(vault): rewrite wiki master index as lightweight topic list"
```

---

## Phase 7: Archive audit

### Task 7.1: Audit `wiki-archive/emil-design-eng-skill.md`

**Files:**
- Modify: `wiki-archive/emil-design-eng-skill.md`

- [ ] **Step 1: Add supersession pointer**

Use `Edit` tool on the file. Find the first line of existing content (after any frontmatter). Immediately before it, insert a new blockquote line:

```markdown
> **Archived 2026-04-14.** Superseded by `C:/Users/rdyal/.claude/skills/emil-design-eng/SKILL.md`.
```

Leave one blank line between the blockquote and the original content.

- [ ] **Step 2: Verify**

```bash
cd "C:/Users/rdyal/Apulu Universe" && head -5 wiki-archive/emil-design-eng-skill.md
```
Expected: first line is the archive blockquote.

- [ ] **Step 3: Commit**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git add wiki-archive/emil-design-eng-skill.md && git commit -m "chore(vault): mark emil-design-eng-skill as archived with supersession pointer"
```

---

### Task 7.2: Audit `wiki-archive/higgsfield-ai-short-film-guide.md`

**Files:**
- Modify OR Delete: `wiki-archive/higgsfield-ai-short-film-guide.md`

- [ ] **Step 1: Compare against live replacement**

Inspect both files to determine if the current `wiki/ai-filmmaking/ai-short-film-prompt-library.md` truly supersedes the archived guide:

```bash
cd "C:/Users/rdyal/Apulu Universe" && echo "=== ARCHIVED ===" && cat wiki-archive/higgsfield-ai-short-film-guide.md && echo "" && echo "=== CURRENT ===" && cat wiki/ai-filmmaking/ai-short-film-prompt-library.md
```

Decision logic:
- If the current note covers the archived one's content → **Step 2a** (add pointer, keep).
- If the archived note has material not in the current one → delete it from archive and **merge useful content into the current note** (treat as a small sub-task; record decision in `.migration-notes.md`).
- If the archived note is superseded but not fully covered → add pointer AND record follow-up in `.migration-notes.md`.

- [ ] **Step 2a: If keeping — add supersession pointer**

Prepend to `wiki-archive/higgsfield-ai-short-film-guide.md`:

```markdown
> **Archived 2026-04-14.** Superseded by [[../wiki/ai-filmmaking/ai-short-film-prompt-library]].
```

- [ ] **Step 2b: If deleting — remove the file**

```bash
powershell -Command "Remove-Item -Force 'C:\Users\rdyal\Apulu Universe\wiki-archive\higgsfield-ai-short-film-guide.md'"
```

Record the deletion decision in `.migration-notes.md`.

- [ ] **Step 3: Commit**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git add -A && git commit -m "chore(vault): resolve higgsfield archive file (kept with pointer OR deleted — see migration notes)"
```

---

### Task 7.3: Audit `wiki-archive/impeccable-frontend-design-skill.md`

**Files:**
- Modify: `wiki-archive/impeccable-frontend-design-skill.md`

- [ ] **Step 1: Add supersession pointer**

Prepend to the file:

```markdown
> **Archived 2026-04-14.** Superseded by [[../wiki/design-engineering/impeccable-frontend-design]].
```

- [ ] **Step 2: Verify**

```bash
cd "C:/Users/rdyal/Apulu Universe" && head -5 wiki-archive/impeccable-frontend-design-skill.md
```

- [ ] **Step 3: Commit**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git add wiki-archive/impeccable-frontend-design-skill.md && git commit -m "chore(vault): mark impeccable-frontend-design-skill as archived with supersession pointer"
```

---

## Phase 8: Final verification

### Task 8.1: Dead-link scan

**Files:**
- Inspect only: all `.md` in vault (excluding `paperclip/`, `node_modules/`, `.git/`)

- [ ] **Step 1: Write a minimal dead-link checker**

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
    # Wikilinks [[target]]
    $wikilinks = [regex]::Matches($content, '\[\[([^\]\|]+)(?:\|[^\]]*)?\]\]') | ForEach-Object { $_.Groups[1].Value }
    foreach ($link in $wikilinks) {
        $linkFile = if ($link -match '\.md$') { $link } else { "$link.md" }
        # Resolve relative to current file dir
        $dir = Split-Path -Parent $f.FullName
        $candidate = Join-Path $dir $linkFile
        if (-not (Test-Path $candidate)) {
            # Try bare basename search in vault
            $bareName = Split-Path -Leaf $linkFile
            $found = Get-ChildItem -Path $root -Recurse -Filter $bareName -ErrorAction SilentlyContinue | Select-Object -First 1
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

- [ ] **Step 2: Run the scan**

```bash
powershell -ExecutionPolicy Bypass -File "C:/Users/rdyal/Apulu Universe/scripts/dead-link-check.ps1"
```
Expected: "No dead links found." OR a list of broken `[[link]]` references.

- [ ] **Step 3: Fix any dead links**

If dead links are reported, fix each one by editing the referencing file. Valid fixes:
- Correct the target filename.
- Remove the link if the referenced concept no longer exists.
- Create the referenced file if it should exist.

Re-run Step 2 after fixes until clean.

- [ ] **Step 4: Commit (only if fixes were made)**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git add -A && git commit -m "fix(vault): resolve dead wikilinks after reorganization" 2>&1 | tail -5
```

---

### Task 8.2: Final structural verification

**Files:**
- Inspect only: vault tree.

- [ ] **Step 1: Print final top-level layout**

```bash
powershell -Command "Get-ChildItem 'C:\Users\rdyal\Apulu Universe' -Force | Select-Object Name, @{N='Type';E={if(\$_.PSIsContainer){'dir'}else{'file'}}} | Format-Table -AutoSize"
```
Expected: only legitimate folders and files — match the structure in Section 1 of the spec.

- [ ] **Step 2: Verify no files lingering in `research/vawn/briefings/` or `research/vawn/discovery/`**

```bash
cd "C:/Users/rdyal/Apulu Universe" && ls research/vawn/briefings 2>&1; ls research/vawn/discovery 2>&1
```
Expected: both folders no longer exist (removed in Task 3.5).

- [ ] **Step 3: Verify `artists/` is gone**

```bash
cd "C:/Users/rdyal/Apulu Universe" && ls artists 2>&1 | head -2
```
Expected: "No such file or directory".

- [ ] **Step 4: Verify `VAULT.md` and all `_index.md` files exist and have frontmatter**

```bash
cd "C:/Users/rdyal/Apulu Universe" && for f in VAULT.md wiki/_master-index.md wiki/*/_index.md; do echo "=== $f ==="; head -4 "$f"; done
```
Expected: every file starts with `---` frontmatter block (except `VAULT.md`, which has none by design — its first line is `# Apulu Universe Vault`).

- [ ] **Step 5: Print git log summary**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git log --oneline
```
Expected: sequential commits covering Phases 0 through 7.

- [ ] **Step 6: Delete `.migration-notes.md`**

If all findings have been resolved, the scratch file is no longer needed.

```bash
powershell -Command "Remove-Item -Force 'C:\Users\rdyal\Apulu Universe\.migration-notes.md' -ErrorAction SilentlyContinue"
```

- [ ] **Step 7: Final commit**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git add -A && git commit -m "chore(vault): final verification pass, remove migration notes" 2>&1 | tail -5
```

- [ ] **Step 8: Tag the reorganization complete**

```bash
cd "C:/Users/rdyal/Apulu Universe" && git tag -a vault-reorg-2026-04-14 -m "Vault reorganization complete (Approach 1.5)"
```
