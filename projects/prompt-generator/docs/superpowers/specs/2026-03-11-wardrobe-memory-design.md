# Wardrobe Memory — Design Spec
**Date:** 2026-03-11
**Status:** Approved
**Scope:** `index.html` — generation functions, system prompt, controls UI

---

## Problem

Outfit pieces (shirts, pants, jackets, hats) repeat across generation runs because the LLM has no memory of what it has previously chosen. Shoes/sneakers are exempt — they may repeat. The user wants a permanent wardrobe log that survives browser sessions and prevents any shirt, pant, jacket, or hat from being reused until manually reset.

---

## Solution Overview

Four components working together:

1. **LLM self-reports wardrobe** — each scene's JSON response includes a `wardrobe_used` field the LLM fills in
2. **localStorage store** — the app accumulates those pieces in `apulu_wardrobe`, capped at 200 per category
3. **Prompt injection + system rule** — before each generation, the wardrobe log is injected into the user prompt; a system prompt rule enforces no repeats
4. **Reset Wardrobe UI** — a button in the controls bar with a live piece count

---

## Section 1 — LLM Self-Reports Wardrobe

**What changes:** The JSON format instruction in the user prompt (the block that tells the LLM what fields to return per scene) gets one new field: `wardrobe_used`.

**Field schema:**
```json
"wardrobe_used": {
  "shirt": "exact description of the shirt chosen, or 'none'",
  "pants": "exact description of the pants chosen, or 'none'",
  "jacket": "exact description of the jacket chosen, or 'none'",
  "hat": "exact description of the hat chosen, or 'none'"
}
```

**Rules:**
- Shoes are excluded — not tracked
- If a category is not present in the scene (e.g. no jacket), the value is the string `"none"`
- The description must be specific enough to identify the garment: brand + garment type + colorway (e.g. `"ivory Casablanca silk bowling shirt with terracotta botanical print"`)
- This field is added to all scene JSON schemas that produce NB2 image prompts: the lyrics-mode branch and description-mode branch inside `generateMV()`, and `generateGridStory()`
- Kling-only modes (start/end, sequential) do not require this field — no outfit generation

**Affected user prompt locations:**
- Lyrics-mode user prompt inside `generateMV()` (~line 1686) — the JSON format block ending with `"negative_prompt": "smiling..."`
- Description-mode user prompt inside `generateMV()` (~line 1706) — the else-branch JSON format block
- `generateGridStory()` user prompt — wherever it defines the per-scene JSON schema

---

## Section 2 — localStorage Wardrobe Store

**Key:** `apulu_wardrobe`

**Structure:**
```json
{
  "shirts": ["ivory Casablanca silk bowling shirt...", "..."],
  "pants": ["sage green wide-leg tailored trousers", "..."],
  "jackets": ["black Rick Owens asymmetric draped cape", "..."],
  "hats": ["flat-brim fitted cap in forest green", "..."]
}
```

**Write behavior (after generation) — `saveWardrobe(scenes)`:**
- Iterate over all returned scenes
- For each scene, read `wardrobe_used` — skip the scene entirely if the field is missing or not an object
- For each category (shirt, pants, jacket, hat): if value is not `"none"` and not empty string, append to the corresponding array
- Deduplicate across both the incoming scenes in this run AND existing stored entries — skip any value that already exists in the array (case-insensitive comparison). This prevents both within-run duplicates (two scenes using the same jacket) and cross-run duplicates
- After appending, trim each array to the last 200 entries (drop oldest if over cap)
- Save back to `localStorage.setItem('apulu_wardrobe', JSON.stringify(...))`
- Immediately after saving, call `updateWardrobeCountLabel()` to refresh the UI count

**Read behavior (before generation) — `loadWardrobe()`:**
- `JSON.parse(localStorage.getItem('apulu_wardrobe') || '{}')`
- If key missing or malformed JSON (wrap in try/catch), return `{ shirts: [], pants: [], jackets: [], hats: [] }`
- Always return an object with all four keys as arrays, even if the stored object is missing some keys

**Helper functions to add:**
- `loadWardrobe()` — reads and parses localStorage, returns object with empty arrays as defaults for all four categories
- `saveWardrobe(scenes)` — extracts `wardrobe_used` from scenes array, deduplicates, appends to store, saves, calls `updateWardrobeCountLabel()`
- `clearWardrobe()` — removes `apulu_wardrobe` from localStorage, calls `updateWardrobeCountLabel()`
- `wardrobeCount()` — returns total number of entries across all categories; guards against non-array values: `Array.isArray(arr) ? arr.length : 0` per category
- `updateWardrobeCountLabel()` — reads `wardrobeCount()` and updates the count display element in the UI

---

## Section 3 — Prompt Injection + System Prompt Rule

### 3a — User Prompt Injection

Before each generation call, `loadWardrobe()` is called. If any category has entries, a WARDROBE MEMORY block is prepended to the user prompt text:

```
WARDROBE MEMORY — these garment pieces have already been used in previous generations. Do NOT repeat or closely resemble any item on this list. Every scene in this generation must use entirely new garment choices not on this list.
Shirts used: [comma-separated list]
Pants used: [comma-separated list]
Jackets used: [comma-separated list]
Hats used: [comma-separated list]

```

Categories with zero entries are omitted from the block entirely (e.g. if no hats have been used, the "Hats used:" line is not included).

If all categories are empty, nothing is prepended — no change to the user prompt.

**Applies to:** `generateMV()` (both lyrics and description modes) and `generateGridStory()`.

### 3b — System Prompt Rule

A new rule added to the NB2 guidelines block in `buildPromptSystem`:

```
- Wardrobe memory: if a WARDROBE MEMORY block appears in the user message, treat it as a hard constraint. No shirt, pant, jacket, or hat in any scene may match or closely resemble any item on the list — not the same garment type, not the same brand in the same colorway, not the same silhouette in the same color. Every generation must produce entirely fresh outfit choices across all scenes. Shoes are exempt from this constraint.
```

---

## Section 4 — Reset Wardrobe UI

**Placement:** Added to the existing controls bar (`.ctrl-row` area near the existing control buttons).

**Elements:**
- A "Reset Wardrobe" button styled consistently with existing `.ctrl-btn` buttons
- A live count label immediately beside it: `"Wardrobe: 47 pieces"` or `"Wardrobe: empty"`

**Behavior:**
- Clicking the button calls `clearWardrobe()` — which internally calls `updateWardrobeCountLabel()` — immediately showing `"Wardrobe: empty"`
- No confirmation dialog — single click clears
- Count label reflects current stored piece count at all times

**Count display update triggers (all handled by `updateWardrobeCountLabel()`):**
- Page load — called once on DOMContentLoaded or equivalent init
- After each successful generation — called inside `saveWardrobe(scenes)`
- After Reset Wardrobe is clicked — called inside `clearWardrobe()`

---

## Implementation

**File:** `index.html` only. No backend changes. No new files.

**Changes (in order):**
1. Add `loadWardrobe()`, `saveWardrobe(scenes)`, `clearWardrobe()`, `wardrobeCount()`, `updateWardrobeCountLabel()` helper functions to the JS section
2. Add wardrobe memory rule to `buildPromptSystem` NB2 guidelines block
3. Add `wardrobe_used` field to JSON format instructions in:
   - Lyrics-mode branch inside `generateMV()` (~line 1686 JSON block)
   - Description-mode branch inside `generateMV()` (~line 1706 JSON block)
   - `generateGridStory()` JSON schema block
4. In `generateMV()` and `generateGridStory()`: call `loadWardrobe()` before building the user prompt; if wardrobe has entries, prepend the WARDROBE MEMORY block to the user prompt text
5. In `generateMV()` and `generateGridStory()`: after successful scene parse (`allScenes = parsed.scenes`), call `saveWardrobe(allScenes)` — this also triggers `updateWardrobeCountLabel()`
6. Add Reset Wardrobe button + count label HTML to the controls bar
7. Call `updateWardrobeCountLabel()` on page load (after DOM ready)

---

## Success Criteria

- After generating a set of scenes, the shirt/pant/jacket/hat pieces are stored in localStorage
- On the next generation, those pieces do not appear again in any scene
- Within a single generation run, two scenes cannot share the same garment piece
- Shoes are never tracked or injected into the wardrobe memory
- The wardrobe count in the UI reflects the current number of stored pieces accurately
- Clicking Reset Wardrobe clears all stored pieces and resets the count to "Wardrobe: empty"
- If localStorage is empty, cleared, or contains malformed data, generation works exactly as before with no errors
- Categories with no stored items are omitted from the WARDROBE MEMORY prompt block
