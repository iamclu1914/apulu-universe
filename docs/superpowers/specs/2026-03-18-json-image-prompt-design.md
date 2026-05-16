# JSON Image Prompt — Design Spec
**Date:** 2026-03-18
**Status:** Approved
**Scope:** `index.html` only — change NB2 image prompt format from prose to JSON

---

## Problem

The current `image_prompt` output is natural language prose. This causes "concept bleeding" where details from one section (e.g. background colors) unintentionally affect another (e.g. clothing). It also makes iteration harder — changing one element requires regenerating the whole description.

---

## Solution

Switch `image_prompt` to a structured JSON object using NB2 Pro standard keys. All existing guideline knowledge (style worlds, footwear color lock, lighting setups, camera specs, photographer references) maps directly into the values of these keys — nothing is removed, just restructured.

The `negative_prompt` top-level field is removed and folded into the JSON as `NegativePrompt`.

---

## JSON Schema

```json
{
  "label": "short scene descriptor (style world + location)",
  "Subject": ["character description — skin tone, facial features, hair, expression, build"],
  "MadeOutOf": ["top garment with brand/fabric/colorway/fit", "bottom garment", "footwear model + colorway", "accessories"],
  "Arrangement": "pose, body position, named camera angle, framing",
  "Lighting": "named lighting setup with color temperature and physical light sources",
  "Camera": {"type": "shot type", "lens": "focal length + aperture", "body": "camera body model"},
  "Background": "location, environment, time of day, depth of field treatment",
  "Mood": "photographer reference and emotional tone",
  "OutputStyle": "cinematic photo, 4K ultra-HD, aspect ratio",
  "NegativePrompt": ["cartoonish", "illustrated", "distorted hands", "...full existing list"]
}
```

---

## Changes

### 1. System prompt output spec (buildPromptSystem)

**NB2-only output format:**
```
{ "image_prompt": { ...JSON object... } }
```

**Both (NB2 + Kling) output format:**
```
{ "image_prompt": { ...JSON object... }, "video_prompt": "..." }
```

`negative_prompt` removed as a top-level field — it is now `NegativePrompt` inside `image_prompt`.

### 2. NB2 guidelines opening line

Replace: "Write in natural flowing prose as if briefing a human photographer — no labeled slots, no keyword lists"

With: Instruction to output a JSON object using the 10 standard NB2 Pro keys, with per-key guidance on what to include. All existing style world, footwear, lighting, camera, photographer reference rules apply — they express as values within the appropriate key.

### 3. User prompt placeholders

All `"image_prompt": "Full NB2 prompt..."` placeholders in generateMV, generateGrid9, etc. updated to show the JSON object structure so the AI knows exactly what format to return.

### 4. renderScenes display

`sc.image_prompt` is now an object. Display as `JSON.stringify(sc.image_prompt, null, 2)` inside a `<pre>` monospace block. Wrap with `escHtml` to prevent XSS.

### 5. Copy logic

`promptMap[kImg]` stores `JSON.stringify(sc.image_prompt, null, 2)` — the formatted JSON string — ready to paste directly into NB2 Pro.

---

## Success Criteria

- Every generated image prompt is a valid JSON object with all 10 keys
- `negative_prompt` no longer appears as a separate output field
- Copy button copies clean formatted JSON string
- Display renders as readable formatted JSON in a monospace block
- All existing guideline rules (style worlds, footwear, lighting, camera, etc.) still expressed — just as JSON values
- No change to video prompt format or Kling mode behavior
