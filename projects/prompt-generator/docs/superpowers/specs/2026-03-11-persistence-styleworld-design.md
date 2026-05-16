# Artist Name Persistence + Style World Memory — Design Spec
**Date:** 2026-03-11
**Status:** Approved
**Scope:** `index.html` only — JS helpers, system prompt, JSON schemas, controls UI

---

## Problem

1. **Artist name is lost on every page load.** The user retypes the same artist name every session.
2. **Style worlds repeat across generation runs.** The LLM has no memory of which of the 8 style worlds it already used, so consecutive runs land in the same worlds.

---

## Solution Overview

Two independent features implemented in `index.html` only:

1. **Artist Name Persistence** — save/restore artist name field via localStorage on page load and before each generation
2. **Style World Memory** — LLM self-reports the style world used per scene; app accumulates them in localStorage and injects them as a hard constraint before each generation; auto-resets when all 8 worlds are used

---

## Section 1 — Artist Name Persistence

**localStorage key:** `apulu_artist`

**Write behavior:** At the top of `generateMV()`, `generateGridStory()`, and `generateFramePair()`, immediately after reading `document.getElementById('artistName').value`, call `saveArtistFields(artist)`. Only saves if non-empty. These are all generation paths that read the artist name field.

**Read behavior:** On page init (alongside `updateWardrobeCountLabel()`), call `loadArtistFields()` which reads `localStorage.getItem('apulu_artist')` and if non-empty, sets `document.getElementById('artistName').value`.

**Survival rule:** `resetAll()` is modified to skip clearing `#artistName` — remove the line `document.getElementById('artistName').value='';` from `resetAll()`. The saved name persists across resets.

**Track name:** Not persisted — track name is song-specific and changes each session.

**Helper functions:**
- `loadArtistFields()` — reads `apulu_artist` from localStorage; if non-empty, sets `#artistName` value
- `saveArtistFields(artist)` — if `artist` is a non-empty string, writes it to `apulu_artist` in localStorage

---

## Section 2 — Style World Memory

**localStorage key:** `apulu_styleworlds`

**Structure:**
```json
{ "worlds": ["WORLD 3 — FRENCH LUXURY STREETWEAR", "WORLD 7 — SPORT LUXURY / ATHLETE FASHION"] }
```

**Scope note:** Style world memory applies only to generation paths that use the NB2 style world system via `buildPromptSystem`: `generateMV()` and `generateGridStory()`. The Kling-only paths (`generateFramePair`, `generateStartEnd`, `generateGrid9`, `generateSequential`) do not use the NB2 style world system and are explicitly out of scope — no `style_world` schema field, no injection, no `saveStyleWorlds` call in these paths.

### 2a — LLM Self-Reports Style World

A new `style_world` field is added to the per-scene JSON schema in all three NB2 generation paths:

```json
"style_world": "WORLD N — NAME (e.g. WORLD 3 — FRENCH LUXURY STREETWEAR)"
```

The LLM fills this with the exact world name it chose for that scene. Value must match the world's full name as written in the outfit rule (e.g. `"WORLD 1 — QUIET LUXURY / OLD MONEY"`). If no outfit world applies, value is `"none"`.

**Affected JSON schemas:**
- Lyrics-mode branch inside `generateMV()`
- Description-mode branch inside `generateMV()`
- `generateGridStory()` inline system prompt schema

`style_world` is added immediately after the existing `wardrobe_used` field in each schema.

### 2b — localStorage Store

**Write behavior — `saveStyleWorlds(scenes)`:**
- Iterate over all returned scenes
- For each scene, read `style_world` — skip if missing, `"none"`, or empty string
- Deduplicate: skip any world already in the stored array (case-insensitive comparison)
- Append new unique entries
- After appending, cap array at 8 entries (there are exactly 8 style worlds)
- Save to localStorage
- **Auto-reset rule:** if the stored array length equals 8 after saving, immediately set the array to `[]` and save again — the next generation starts a fresh cycle
- Call `updateStyleWorldLabel()` exactly once, at the very end of the function (after all saves and any auto-reset) — this ensures the label shows `0/8` after an auto-reset, never a transient `8/8`

**Read behavior — `loadStyleWorlds()`:**
- `JSON.parse(localStorage.getItem('apulu_styleworlds') || '{}')`
- Wrap in try/catch; return `{ worlds: [] }` if missing, malformed, or `worlds` is not an array
- Always return object with `worlds` as array

**Helper functions:**
- `loadStyleWorlds()` — reads and normalises localStorage entry
- `saveStyleWorlds(scenes)` — extracts `style_world` from scenes, deduplicates, appends, caps at 8, auto-resets when full, saves, calls `updateStyleWorldLabel()` once at the end
- `clearStyleWorlds()` — removes `apulu_styleworlds` from localStorage, calls `updateStyleWorldLabel()`
- `styleWorldCount()` — returns `Array.isArray(w.worlds) ? w.worlds.length : 0` where `w = loadStyleWorlds()`
- `updateStyleWorldLabel()` — reads `styleWorldCount()` and sets `#styleWorldLabel` text to `"Worlds: N/8 used"`
- `buildStyleWorldPromptBlock(sw)` — if `sw.worlds.length === 0` returns `''`; otherwise returns the STYLE WORLD MEMORY block string

### 2c — Prompt Injection

Before each generation call in `generateMV()` and `generateGridStory()`, `loadStyleWorlds()` is called. If any worlds are stored, a block is prepended to the user prompt (alongside the wardrobe block — both may be present):

```
STYLE WORLD MEMORY — these style worlds have already been used in previous generations. Do NOT use any world on this list. Every scene in this generation must use a style world not on this list.
Worlds used: [comma-separated list]

```

If all entries are empty, nothing is prepended.

The style world block is prepended to the combined prompt text alongside the wardrobe block. Order: wardrobe block first, then style world block, then user prompt text.

### 2d — System Prompt Rule

A new rule added to the NB2 guidelines block in `buildPromptSystem`, immediately after the existing wardrobe memory rule (which is between the `- Include "4K ultra-HD"` line and the `- negative_prompt must include:` line):

```
- Style world memory: if a STYLE WORLD MEMORY block appears in the user message, treat it as a hard constraint. No scene may use any style world listed — not the same world number, not the same brand universe, not the same aesthetic register. Every generation must use only worlds not on the list.
```

### 2e — UI

Two elements added to the controls bar immediately after the existing wardrobe controls (wardrobeResetBtn and wardrobeCountLabel), before the History toggle:

- A `"Reset Worlds"` button: `class="ctrl-btn"`, `id="styleWorldResetBtn"`, `onclick="clearStyleWorlds()"`
- A count label: `id="styleWorldLabel"`, inline style matching wardrobeCountLabel, initial text `"Worlds: 0/8 used"` — always shows the fraction (never "empty")

**Count display triggers:**
- Page load — `updateStyleWorldLabel()` called in init block
- After each successful generation — called once at end of `saveStyleWorlds(scenes)`
- After Reset Worlds clicked — called inside `clearStyleWorlds()`

---

## Implementation

**File:** `index.html` only. No backend changes. No new files.

**Changes (in order):**
1. Add `loadArtistFields()`, `saveArtistFields(artist)` helper functions (near wardrobe helpers)
2. Add `loadStyleWorlds()`, `saveStyleWorlds(scenes)`, `clearStyleWorlds()`, `styleWorldCount()`, `updateStyleWorldLabel()`, `buildStyleWorldPromptBlock(sw)` helper functions (near wardrobe helpers)
3. Add style world memory rule to `buildPromptSystem` NB2 guidelines block (immediately after wardrobe memory rule)
4. Add `style_world` field to JSON schemas (immediately after `wardrobe_used` in each):
   - Lyrics-mode branch inside `generateMV()`
   - Description-mode branch inside `generateMV()`
   - `generateGridStory()` inline system prompt schema
5. In `generateMV()`, `generateGridStory()`, and `generateFramePair()`: call `saveArtistFields(artist)` at top (after artist is read)
6. In `generateMV()` and `generateGridStory()`: call `buildStyleWorldPromptBlock(loadStyleWorlds())` and prepend its result to the user prompt text (after the wardrobe block, before the user prompt)
7. In `generateMV()` and `generateGridStory()`: call `saveStyleWorlds(allScenes)` after `allScenes=parsed.scenes||[]`
8. In `resetAll()`: remove the line that clears `#artistName` (`document.getElementById('artistName').value='';`)
9. Add Reset Worlds button + style world label HTML to controls bar (immediately after wardrobeCountLabel, before History toggle)
10. Call `loadArtistFields()` and `updateStyleWorldLabel()` on page load (in the `// Initialize` block)

---

## Success Criteria

- Artist name field is pre-filled on every page load from the previous session
- Artist name survives `resetAll()` — clicking Start Fresh does not clear the artist name field
- Track name field is not persisted — it clears on reset as before
- Generating in any mode (MV, GridStory, or FramePair) saves the artist name
- After generating scenes, the style world(s) used are stored in localStorage
- On the next generation, used worlds do not appear again in any scene
- When all 8 worlds have been used, the log auto-resets — the label immediately shows `"Worlds: 0/8 used"` (no flash of 8/8)
- The `"Worlds: X/8 used"` label reflects current count accurately at all times
- Clicking Reset Worlds clears the log and shows `"Worlds: 0/8 used"`
- If localStorage is empty or malformed, both features degrade gracefully with no errors
- Style world memory does not apply to Kling-only generation paths
