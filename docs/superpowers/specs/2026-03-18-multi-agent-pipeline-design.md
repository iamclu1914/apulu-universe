# Multi-Agent Prompt Generation Pipeline — Design Spec
**Date:** 2026-03-18
**Status:** Approved for implementation
**Scope:** Backend orchestration + agent system prompts + minor frontend loading UX

---

## 1. Problem Statement

The current architecture makes a single Gemini API call with a ~5,000-word system prompt. One generalist model simultaneously acts as creative director, celebrity stylist, director of photography, and motion director — while tracking cross-scene consistency rules (brand no-repeat, shoe no-repeat, style world no-repeat) across 6–9 scenes. This produces rule violations and lower output quality than specialized agents would.

---

## 2. Solution Overview

A 4-stage sequential agent pipeline where each agent receives the accumulated output of all prior agents. The frontend makes one request to a new `/api/generate-prompts` endpoint. The backend orchestrates all 4 calls and returns a single assembled response in the existing JSON schema.

---

## 3. Architecture

### Pipeline Flow

```
User Input
    ↓
[Agent 1: Scene Architect]
    → N scene briefs (style world, location, time of day, season, narrative beat)
    ↓
[Agent 2: Stylist]
    → receives ALL N briefs simultaneously
    → outputs: Subject, MadeOutOf, headwear, jewelry per scene
    ↓
[Agent 3: Cinematographer]
    → receives briefs + locked outfits
    → outputs: Arrangement, Lighting, Camera, Background, Composition,
               ColorPalette, Mood, OutputStyle, NegativePrompt per scene
    ↓
[Agent 4: Video Director]  ← see mode routing table for when this runs
    → receives complete assembled image prompt per scene
    → outputs: video_prompt per scene
    ↓
Merge by index → existing frontend JSON schema (zero frontend parser changes)
```

### New Endpoint

```
POST /api/generate-prompts
```

**Request body (all fields):**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `mode` | string | Yes | One of: `"mv"`, `"nb2"`, `"kling-9grid"`, `"kling-startend"` |
| `userInput` | string | Yes | Raw user text (lyrics, description, or mood) |
| `anchorBlock` | string | No | Reference image context string; empty string if no reference image |
| `wardrobeMemory` | string | No | Prior wardrobe items to exclude; empty string if none |
| `styleWorldMemory` | string | No | Prior style worlds to exclude; empty string if none |
| `sceneCount` | integer | No | Requested number of scenes; defaults per mode if omitted (see mode routing table) |

**Validation:** If `mode` is not one of the four valid values, return HTTP 400 immediately before any agent calls.

### Mode Routing Table

| Mode | Agent 1 | Agent 2 | Agent 3 | Agent 4 | Default sceneCount | Min | Max |
|------|---------|---------|---------|---------|-------------------|-----|-----|
| `mv` | Yes | Yes | Yes | Yes | 6 | 6 | 8 |
| `nb2` | Yes | Yes | Yes | No | 6 | 6 | 8 |
| `kling-9grid` | Yes | Yes | Yes | Yes | 9 | 9 | 9 |
| `kling-startend` | Yes | Yes | Yes | Yes | 2 | 2 | 4 |

If `sceneCount` is provided but outside the min/max for the mode, clamp it to the valid range server-side.

### Agent Output Schemas

These are the strict contracts between agents. All fields marked required must be present; optional fields may be omitted.

**Agent 1 output:**
```json
{
  "scenes": [
    {
      "index": 1,
      "style_world": 3,
      "style_world_name": "FRENCH LUXURY STREETWEAR",
      "location": "rooftop terrace, Paris",
      "time_of_day": "golden hour",
      "season": "summer",
      "narrative_beat": "reflective, looking out over the city alone"
    }
  ]
}
```

| Field | Type | Required |
|-------|------|----------|
| `index` | integer (1-based) | Yes |
| `style_world` | integer (1–8) | Yes |
| `style_world_name` | string | Yes |
| `location` | string | Yes |
| `time_of_day` | string | Yes |
| `season` | string | Yes |
| `narrative_beat` | string | Yes |

**Agent 2 output:**
```json
{
  "scenes": [
    {
      "index": 1,
      "Subject": ["string", "..."],
      "MadeOutOf": ["string", "..."],
      "headwear": "fitted cap in ivory, pulled low over edge-up",
      "jewelry": "thick gold Cuban link chain resting flat against chest"
    }
  ]
}
```

| Field | Type | Required |
|-------|------|----------|
| `index` | integer (1-based) | Yes |
| `Subject` | array of strings | Yes |
| `MadeOutOf` | array of strings | Yes |
| `headwear` | string | Yes |
| `jewelry` | string | Yes |

**Agent 3 output:**
```json
{
  "scenes": [
    {
      "index": 1,
      "Arrangement": "string",
      "Lighting": "string",
      "Camera": { "type": "string", "lens": "string", "body": "string" },
      "Background": "string",
      "Mood": "string",
      "OutputStyle": "cinematic photo, 4K ultra-HD",
      "Composition": { "framing": "string", "angle": "string", "focus": "string" },
      "ColorPalette": { "dominant": ["#hex1", "#hex2"], "mood": "string" },
      "NegativePrompt": ["string", "..."]
    }
  ]
}
```

| Field | Type | Required |
|-------|------|----------|
| `index` | integer (1-based) | Yes |
| `Arrangement` | string | Yes |
| `Lighting` | string | Yes |
| `Camera` | object: `{ type, lens, body }` all strings | Yes |
| `Background` | string | Yes |
| `Mood` | string | Yes |
| `OutputStyle` | string | Yes |
| `Composition` | object: `{ framing, angle, focus }` all strings | Yes |
| `ColorPalette` | object: `{ dominant: string[], mood: string }` | Yes |
| `NegativePrompt` | array of strings | Yes |

**Agent 4 output:**
```json
{
  "scenes": [
    {
      "index": 1,
      "video_prompt": "[0:00-0:03] ..."
    }
  ]
}
```

| Field | Type | Required |
|-------|------|----------|
| `index` | integer (1-based) | Yes |
| `video_prompt` | string | Yes |

### Scene Count Mismatch Policy

LLM outputs are non-deterministic. If any agent returns a different number of scene objects than requested:

- **If Agent 1 returns fewer scenes than `sceneCount`:** proceed with however many were returned. Do not retry. All downstream agents receive the actual returned count as the new effective N.
- **If Agent 1 returns more scenes than `sceneCount`:** truncate to `sceneCount` before passing to Agent 2.
- **If Agent 2 or Agent 3 returns fewer scene objects than received from the previous stage:** the missing indices produce incomplete assembled objects. These scenes are excluded from the final response array. The response includes a `scenes_generated` count so the frontend can detect this.
- **If Agent 4 returns fewer scene objects than received:** missing `video_prompt` values default to `null` for those scenes (non-fatal).

### Merge Strategy

Merge is performed by matching the `index` field across all four agent outputs. For each index present in Agent 3's output (the minimum required for an image prompt):

```
assembled_scene = {
  image_prompt: {
    label: `WORLD ${agent1[i].style_world} — ${agent1[i].style_world_name} | ${agent1[i].location}, ${agent1[i].time_of_day}`,
    Subject:       agent2[i].Subject,
    MadeOutOf:     agent2[i].MadeOutOf,
    Arrangement:   agent3[i].Arrangement,
    Lighting:      agent3[i].Lighting,
    Camera:        agent3[i].Camera,
    Background:    agent3[i].Background,
    Mood:          agent3[i].Mood,
    OutputStyle:   agent3[i].OutputStyle,
    Composition:   agent3[i].Composition,
    ColorPalette:  agent3[i].ColorPalette,
    NegativePrompt: agent3[i].NegativePrompt
  },
  video_prompt: agent4?.[i]?.video_prompt ?? null
}
```

If an index is present in Agent 1 but missing from Agent 2 or Agent 3, that scene is dropped from the response entirely (not substituted with nulls).

The `label` field is constructed by the merge step (not by any individual agent) using: `` `WORLD ${agent1[i].style_world} — ${agent1[i].style_world_name} | ${agent1[i].location}, ${agent1[i].time_of_day}` ``

### Final Assembled Response

`scenes_generated` equals the count of scenes in the assembled `scenes` array after all merges and drops — not the count Agent 1 returned. If `scenes_generated < scenes_requested`, one or more scenes were dropped due to missing Agent 2 or Agent 3 data for those indices.

The complete `image_prompt` object for each scene contains exactly these 12 fields (all required):

| Field | Source Agent |
|-------|-------------|
| `label` | Constructed at merge (from Agent 1 data) |
| `Subject` | Agent 2 |
| `MadeOutOf` | Agent 2 |
| `Arrangement` | Agent 3 |
| `Lighting` | Agent 3 |
| `Camera` | Agent 3 |
| `Background` | Agent 3 |
| `Mood` | Agent 3 |
| `OutputStyle` | Agent 3 |
| `Composition` | Agent 3 |
| `ColorPalette` | Agent 3 |
| `NegativePrompt` | Agent 3 |

```json
{
  "scenes": [
    {
      "image_prompt": {
        "label": "WORLD 3 — FRENCH LUXURY STREETWEAR | rooftop terrace, golden hour",
        "Subject": ["male subject, deep brown skin, defined facial structure..."],
        "MadeOutOf": ["Celine by Hedi Slimane ivory silk bowling shirt..."],
        "Arrangement": "THREE-QUARTER LOW angle, subject standing with weight on left hip...",
        "Lighting": "GOLDEN HOUR NATURAL — low sun at 15 degrees...",
        "Camera": { "type": "medium portrait", "lens": "85mm f/1.4", "body": "Sony A7R V" },
        "Background": "Paris rooftop terrace, city skyline softly blurred...",
        "Mood": "carries Tyler Mitchell's airy editorial warmth...",
        "OutputStyle": "cinematic photo, 4K ultra-HD, 4:5 aspect ratio",
        "Composition": { "framing": "cowboy shot", "angle": "three-quarter low", "focus": "subject sharp, rooftops dissolved into bokeh" },
        "ColorPalette": { "dominant": ["#F5F0E8", "#C8922A"], "mood": "warm ivory and gold, sun-drenched softness" },
        "NegativePrompt": ["cartoonish", "illustrated", "distorted hands", "extra limbs", "..."]
      },
      "video_prompt": "[0:00-0:03] ... | null if Agent 4 skipped or failed"
    }
  ],
  "scenes_generated": 6,
  "scenes_requested": 6
}
```

The frontend already handles `video_prompt: null` correctly — NB2 mode today produces scenes with no `video_prompt` field, and the renderer checks for its presence before rendering. Confirmed compatible.

---

## 4. Agent Specifications

### Agent 1 — Scene Architect

**Role:** Creative director. Reads user input and decides the full scene structure.

**Responsibilities:**
- Determine scene count (N) appropriate to mode
- Assign each scene a unique style world number (no repeats)
- Assign location, time of day, season, narrative beat per scene

**System prompt focus:** ~500 words. No outfits, no cameras, no lighting — pure scene structure.

**Input:** Raw user input + mode context + `sceneCount`
**Output:** Agent 1 schema defined above

---

### Agent 2 — Stylist

**Role:** Celebrity stylist. Receives all N scene briefs simultaneously to enforce cross-scene rules.

**Responsibilities:**
- Apply all style world brand rules per scene
- Enforce brand no-repeat across all scenes
- Apply shoe color-lock rule (shoe dominant color matches shirt dominant color)
- Enforce shoe model no-repeat across scenes
- Rotate headwear per scene
- Apply `wardrobeMemory` and `styleWorldMemory` constraints

**System prompt focus:** ~800 words. Fashion and styling rules only.

**Input:** All N scene briefs (Agent 1 output) + `wardrobeMemory` + `styleWorldMemory`
**Output:** Agent 2 schema defined above

---

### Agent 3 — Cinematographer

**Role:** Director of Photography. Receives scene briefs + locked outfits. Decides all visual and technical specifications.

**Responsibilities:**
- Select camera angle from 26-angle library (rotate across scenes, no same angle twice)
- Select lighting setup from 18-setup library (vary across scenes)
- Choose camera body and lens appropriate to shot type
- Determine depth of field, background treatment, social framing
- Write pose physics and social body language
- Select photographer reference per scene (rotate across 8 named photographers)
- Generate NegativePrompt list

**System prompt focus:** ~1,200 words. Visual and technical specs only.

**Expanded Camera Angles (26 total):**

Original 16:
1. LOW HERO ANGLE — camera at knee/hip looking up, dominance and scale
2. EYE-LEVEL INTIMATE — straight on or slight 3/4, emotional connection
3. THREE-QUARTER LOW — waist height, 15-20° up, classic hip-hop portrait
4. OVER-THE-SHOULDER — behind and beside subject, depth and mystery
5. DUTCH TILT — 10-15° rotation, tension or swagger
6. TIGHT CLOSE-UP — face chin to hairline, 85mm+, emotional intensity
7. WIDE ENVIRONMENTAL — 35mm, subject in lower third of location
8. COWBOY SHOT — mid-thigh to face, outfit visible head to toe
9. FIRST-PERSON POV — subject's eye level looking out, never visible from outside
10. MIRROR SELFIE — full-length mirror, phone at chest/face height
11. LOOKING DOWN TOP-DOWN — directly above looking down at hands/object
12. SEATED CANDID — eye level or slightly above, body turned, relaxed
13. WALKING MID-STRIDE — camera facing subject as they walk toward lens
14. THROUGH GLASS / WINDOW — outside looking in, reflections add authenticity
15. DETAIL CLOSE-UP — single object fills 70% of frame, extreme shallow DoF
16. LEANING CASUAL — subject leaning against surface, effortless and unposed

New additions (17–26):
17. BIRD'S EYE OVERHEAD — camera directly above, omniscient, subject against floor texture
18. HIGH ANGLE VULNERABLE — camera elevated looking down, subject appears human/approachable
19. EXTREME CLOSE-UP DETAIL — single feature fills frame (eye, jaw, jewelry, fabric texture)
20. TELEPHOTO COMPRESSED — 200mm+, background flattened dramatically into abstract color wash
21. STEADICAM FOLLOW — camera gliding behind/beside subject mid-stride, immersive momentum
22. CRANE REVEAL — camera descends from high to eye level or rises to expose environment scale
23. TWO-SHOT RELATIONAL — two subjects framed together, spatial relationship visible
24. MACRO TEXTURE — extreme close-up of surface (fabric weave, sneaker sole, skin pores)
25. SPLIT FRAME — subject occupies one half, environment/object the other, visual tension
26. DUTCH TILT AGGRESSIVE — 20-45° rotation, full swagger/instability statement

**Expanded Lighting Setups (18 total):**

Original 8:
1. GOLDEN HOUR NATURAL — low sun 10-20°, warm 2800-3200K backlight, amber rim
2. BLUE HOUR / DUSK — cerulean sky 8000K + warm practicals 2700K
3. NIGHT STREET PRACTICAL — sodium vapor 2100K, neon fill, car headlight rim
4. ARENA / STADIUM — overhead LED floods 5600K + warm courtside practicals 3200K
5. OVERCAST DIFFUSED — cloud cover as softbox, 6500K, even exposure
6. REMBRANDT PORTRAIT — single key 45° above and to side, triangle of light on cheek
7. STUDIO BEAUTY DISH — large octabox/beauty dish at 45°, clean and even
8. FLASH FILL OUTDOOR — ambient natural + direct or bounced strobe fill

New additions (9–18):
9. BUTTERFLY / GLAMOUR — key centered directly above, symmetrical shadow under nose
10. CLAMSHELL BEAUTY — key above + fill below, removes all shadows, skin/garment clarity
11. SPLIT LIGHT — key at 90°, half face lit / half dark, high drama editorial
12. SHORT LIGHTING — key illuminates side of face turned away from camera
13. THREE-POINT STUDIO — key at 45° + fill at 50% + back rim light
14. BACK / RIM LIGHT HALO — single light behind at 45-90°, glowing edge on hair/shoulders
15. HARSH EDITORIAL HARD LIGHT — specular directional key, defined shadows, sharp edges
16. STRIPBOX EDGE — narrow vertical striplight, edge definition, luxury fashion standard
17. GEL / COLOR MOOD — colored gels (magenta, cobalt, amber) for music video atmosphere
18. TOP LIGHT DRAMATIC — single light directly overhead, deep eye socket shadows

**Input:** Agent 1 scene briefs + Agent 2 outfit output (merged per index)
**Output:** Agent 3 schema defined above

---

### Agent 4 — Video Director *(skipped per mode routing table)*

**Role:** Kling 3.0 motion specialist. Writes production-quality video prompts from fully assembled image scenes.

**Responsibilities:**
- Write 3-5 timestamped shot blocks, MAX 15 seconds total
- Apply character consistency lock on every shot block
- Apply attire lock referencing exact image prompt outfit
- Specify named camera movement per block
- Specify named transition type into each new block
- Specify subject performance energy and eyeline per block
- Align cut timing to musical section (verse/chorus pacing rules)
- Include end-state on final shot

**Camera Movement Vocabulary:**
- Dolly In / Out — camera moves physically closer or farther
- Pan Left / Right — horizontal pivot from fixed position
- Tilt Up / Down — vertical pivot from fixed position
- Orbital / 360° — camera rotates around subject
- Crane Rise / Descend — camera mounted on arm, sweeps high arc
- Steadicam Follow — smooth gimbal tracking through space
- Handheld — natural jitter, raw documentary energy
- Whip Pan — fast horizontal blur between subjects
- Rack Focus — focus shifts from foreground to background element
- Speed Ramp — footage transitions between normal/slow-motion/fast-motion

**Named Transition Types:**
- Smash Cut — on exact percussion hit/bass drop, maximum impact
- Hard Cut — clean on-beat cut, default
- Match Cut — two shots share same composition/gesture across scenes
- Dissolve — smooth connection between thematically linked moments
- Freeze Frame — holds on impact moment 1-3 frames then resumes
- Whip Pan Transition — fast horizontal blur bridges two subjects
- Jump Cut — repetitive action emphasis, edgy sections
- Fade to Black — major scene separation, emotional pause

**Audio-Visual Sync Rules:**

| Section | Shot Duration | Cut Rhythm |
|---------|--------------|------------|
| Verse | 3–5 sec | Moderate, phrase-aligned |
| Pre-chorus | 2–3 sec | Increasing pace, building |
| Chorus | 1–2 sec | Fast, on-beat smash cuts |
| Bridge | 4–6 sec | Shift in visual approach |
| Outro | 5–8 sec | Slow dissolves, pull-back |

**Performance Direction Vocabulary:**
- Energy levels: Static / Subtle / Natural / Energetic / Explosive
- Eyeline: direct to camera / off-screen left / off-screen right / downward / upward
- Body language: strut / slink / stomp / controlled stillness / mid-stride
- Micro-expressions: furrowed brow, set jaw, soft eyes, direct intensity

**Output format example:**
```
[0:00-0:03] ESTABLISHING — Maintaining subject's identical facial features, bone structure,
and skin tone throughout — Concert stage, fog rolling, blue-purple practicals. Wide shot,
camera dollies in slowly. Static energy, direct eyeline to camera. Smash cut on beat drop. →

[0:03-0:08] VERSE — Maintaining subject's identical facial features, bone structure, and
skin tone throughout — Medium close-up, steadicam tracks left with subject mid-stride.
Natural energy, off-screen right eyeline. Hard cut on downbeat. →

[0:08-0:13] CHORUS — Maintaining subject's identical facial features, bone structure, and
skin tone throughout — Tight close-up, face fills frame, camera holds static. Speed ramps
to slow-motion as lyric peaks. Explosive energy, jaw set, direct camera contact. Freeze
one frame on impact, then dissolve. →

[0:13-0:15] END STATE — Maintaining subject's identical facial features, bone structure,
and skin tone throughout — Wide crane shot rising. Subject center frame, crowd visible
behind. Motion holds in slow-motion. Scene locked on final frame.
```

**Input:** Complete merged scene object (all fields from Agents 1–3)
**Output:** Agent 4 schema defined above

---

## 5. Backend Orchestration (server.js)

### Per-Stage Timeout and Retry Policy

| Stage | Timeout | Retry on transient error | Behavior on timeout/failure |
|-------|---------|--------------------------|----------------------------|
| Agent 1 | 30s | 1 retry | Abort pipeline, return HTTP 500 with `{ error: 'scene_architect_failed', stage: 1 }` |
| Agent 2 | 45s | 1 retry | Abort pipeline, return HTTP 500 with `{ error: 'stylist_failed', stage: 2 }` |
| Agent 3 | 60s | 1 retry | Abort pipeline, return HTTP 500 with `{ error: 'cinematographer_failed', stage: 3 }` |
| Agent 4 | 45s | 1 retry | Non-fatal — return image prompts with `video_prompt: null` per scene, HTTP 200 |

Transient error definition: HTTP 429 (rate limit) or HTTP 503 from Gemini. Any other error is not retried.

### Error Response Shapes

```json
// Stages 1-3 fatal failure
{
  "error": "scene_architect_failed",
  "stage": 1
}

// Stage 4 non-fatal — still HTTP 200
{
  "scenes": [...],
  "scenes_generated": 6,
  "scenes_requested": 6,
  "video_prompts_failed": true
}
```

---

## 6. Frontend Changes

### 1. Null `video_prompt` handling
Confirmed: the existing frontend renderer checks for `video_prompt` presence before rendering. `null` is handled the same as absence — no new frontend change needed.

### 2. Loading UX — Stage Progress Text

The existing `.load-txt` element currently shows static text. Replace with a cycling label that advances on a fixed interval while the request is pending. The timer is approximate — it reflects expected stage timing, not actual stage completion.

**Interval:** 10 seconds per stage
**Labels:**
```
0s  → "READING THE ROOM..."       (Scene Architect — ~8-12s expected)
10s → "STYLING THE LOOK..."       (Stylist — ~10-15s expected)
20s → "SETTING THE SHOT..."       (Cinematographer — ~12-18s expected)
30s → "DIRECTING THE MOTION..."   (Video Director — ~10-15s expected)
```

**Behavior:** `setInterval` starts when request begins. Clears immediately when response arrives regardless of which label is active. If the response arrives before all labels cycle, the displayed label will not match the actual stage — this is acceptable for this implementation. The label resets to the first stage on the next generation.

This is the only frontend change needed beyond the new fetch endpoint.

---

## 7. Testing Plan

### Phase 1 — Agent Isolation
Call each agent independently with hardcoded inputs matching the defined schemas. Assert:
- Output JSON parses without error
- All required fields are present per schema
- `index` values are sequential integers starting at 1

### Phase 2 — Pipeline Integration
Run full 4-stage chain with a simple 6-scene MV input. Assert:
- Merge produces valid assembled schema
- All 6 scenes have complete `image_prompt` with all required keys including `Composition` and `ColorPalette`
- `video_prompt` is a non-null string per scene
- `scenes_generated` matches `scenes_requested`

### Phase 3 — Mode Coverage
| Mode | Expected | Assert |
|------|----------|--------|
| `mv` | 6 scenes, Agent 4 runs | `video_prompt` non-null per scene |
| `nb2` | 6 scenes, Agent 4 skipped | `video_prompt` is null per scene |
| `kling-9grid` | 9 scenes, Agent 4 runs | 9 assembled scenes returned |
| `kling-startend` | 2 scenes, Agent 4 runs | 2 assembled scenes returned |

### Phase 4 — Failure Recovery
| Test | How to simulate | Assert |
|------|----------------|--------|
| Stage 1 failure | Return invalid JSON from mock Agent 1 | HTTP 500, `{ error: 'scene_architect_failed', stage: 1 }` |
| Stage 2 failure | Return invalid JSON from mock Agent 2 | HTTP 500, `{ error: 'stylist_failed', stage: 2 }` |
| Stage 3 failure | Return invalid JSON from mock Agent 3 | HTTP 500, `{ error: 'cinematographer_failed', stage: 3 }` |
| Stage 4 failure | Return invalid JSON from mock Agent 4 | HTTP 200, image prompts present, `video_prompts_failed: true`, `video_prompt: null` per scene |
| Scene count mismatch | Agent 1 returns 5 scenes when 6 requested | HTTP 200, `scenes_generated: 5`, `scenes_requested: 6`, 5 complete scenes returned |

### Phase 5 — Rule Validation (per generation)
Check output of a 6-scene MV generation:
- No brand appears more than once across scenes
- No shoe model repeats across scenes
- No style world number repeats
- Shoe dominant color matches shirt dominant color (color-lock)
- Camera angle varies across all scenes (no same angle twice)
- Lighting setup varies across scenes

---

## 8. Key Design Decisions

1. **Frontend makes one request** — all orchestration is server-side. No SSE or streaming.
2. **Agent 2 receives all scene briefs simultaneously** — required for cross-scene brand/shoe/world no-repeat enforcement. This is the architectural decision that eliminates the most common rule violations.
3. **Agent 4 is non-fatal** — a video prompt failure degrades gracefully to image-only output, matching existing NB2 behavior. Frontend confirmed to handle `video_prompt: null`.
4. **Existing `/api/messages` endpoint unchanged** — backward compatible. Only `/api/generate-prompts` is new.
5. **Zero frontend parser changes** — assembled output schema is identical to current format. `scenes_generated` and `scenes_requested` are new fields the frontend can optionally surface.
6. **Scene count mismatch is non-retrying** — proceed with whatever the model returned rather than making additional API calls. Downstream agents adapt to actual count.
7. **Each agent uses a short, focused system prompt** — ~500-1,200 words each vs. 5,000 words today. Models perform significantly better with focused constraints.
8. **Timer-based loading UX is approximate by design** — chose simplicity over accuracy. Acknowledged in spec.
