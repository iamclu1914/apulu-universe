# Kling Comprehensive Video Quality Enhancement — Design Spec
**Date:** 2026-03-11
**Status:** Approved
**Scope:** `index.html` only — same 4 Kling system prompt locations

---

## Problem

Six categories of output failure in Kling video generation:

1. **Prop injection** — Kling infers contextually "appropriate" accessories (headphones, earphones) not present in the reference image
2. **Motion exaggeration** — Vague motion language ("moves energetically") produces jerky or dramatic movement instead of subtle, grounded action
3. **Environment instability** — Background objects appear/disappear mid-clip; walls shift; lighting pulses or flickers as animated effects
4. **Camera chaos** — No camera constraint produces orbit, rapid pan, or handheld shake that destabilizes the frame
5. **Freeze-frame misinterpretation** — Kling interprets "freeze" as a dramatic cinematic instruction, adding sci-fi energy effects (already partially addressed — reinforced here)
6. **Unstructured shot blocks** — Without a formula, shot blocks vary wildly in what they describe, producing inconsistent output

---

## Solution

Add 4 new rules + 1 structural formula to all 4 Kling system prompt locations, in this insertion order after ATTIRE LOCK and before KLING MOTION:

1. **PROP LOCK** — No accessories/props not visible in reference image
2. **MOTION DISCIPLINE** — Precise verbs with physical scale, no adverbs, max 2 actions per block
3. **SCENE LOCK** — Static background, physical lighting fixtures only, no new objects
4. **CAMERA DISCIPLINE** — Locked-off or ultra-slow drift only

And after KLING MOTION:

5. **SHOT FORMULA** — Mandatory per-block structure

And expand the negative list with environment + prop terms.

---

## New Rule Text

### PROP LOCK
```
PROP LOCK: Do NOT add any accessories, props, or objects not visible in the provided reference image. No headphones, earphones, sunglasses, hats, jewelry, or any item not photographed on the subject.
```

### MOTION DISCIPLINE
```
MOTION DISCIPLINE: All movements are subtle and grounded. Use precise verbs with physical scale (e.g., "chin drops 2 cm", "left shoulder rises 1 cm"). Do NOT use adverbs like "energetically", "dramatically", "aggressively", "rapidly", or "intensely". Maximum 2 motion actions per shot block.
```

### SCENE LOCK
```
SCENE LOCK: The background environment is completely static. No new objects enter frame. No objects disappear. Lighting is described only as physical fixtures (overhead fluorescent, window light from left, neon sign on wall) — never as animated effects, pulsing strobes, or changing intensity.
```

### CAMERA DISCIPLINE
```
CAMERA DISCIPLINE: Camera is locked-off or on an ultra-slow drift only. No orbit, spin, rapid pan, crash zoom, or handheld shake. Movements must be imperceptible — the viewer should feel stillness.
```

### SHOT FORMULA
```
SHOT FORMULA: Every timestamped block must follow this structure exactly: [CAMERA TYPE + DISTANCE], [SUBJECT POSITION + ANCHOR]. [MICRO-MOTION with scale]. [LIGHTING SOURCE as physical fixture]. Audio: [ambient sound].
```

### Expanded negative additions
Add to the end of every existing negative list:
```
flickering background, shifting environment, morphing walls, background objects appearing, new objects entering frame, animated lighting, pulsing lights, strobe effects, fast motion, sudden movement, exaggerated gestures, camera spin, camera orbit, rapid pan, handheld shake, headphones, earphones, added accessories, spontaneous props, props not in reference
```

---

## Affected Locations

### Location 1 — `buildPromptSystem()` Kling block (~lines 1804–1807)

**Search for (exact):**
```
- CHARACTER CONSISTENCY: Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description. The subject's face must read as the same person in every frame. This is non-negotiable.
- ATTIRE LOCK: Describe the subject's outfit exactly as visible in the provided reference image. Do NOT invent, substitute, or alter any clothing item. Every shot block must reference only garments actually shown in the image — exact colors, garment types, and layering as photographed.
- KLING MOTION: Do NOT use "freeze-frame", "static freeze", or "freeze" to describe an end state. Kling generates continuous motion throughout — describe the final moment as motion naturally slowing to stillness, a composed held stare, or a gradual deceleration instead.
- End with Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, altered bone structure, drifting features, morphing eyes, face deformation, character inconsistency, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features, glowing orbs, energy effects, supernatural light, sci-fi glow, lens flare orbs, light emanating from subject, magical effects
```

**Replace with:**
```
- CHARACTER CONSISTENCY: Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description. The subject's face must read as the same person in every frame. This is non-negotiable.
- ATTIRE LOCK: Describe the subject's outfit exactly as visible in the provided reference image. Do NOT invent, substitute, or alter any clothing item. Every shot block must reference only garments actually shown in the image — exact colors, garment types, and layering as photographed.
- PROP LOCK: Do NOT add any accessories, props, or objects not visible in the provided reference image. No headphones, earphones, sunglasses, hats, jewelry, or any item not photographed on the subject.
- MOTION DISCIPLINE: All movements are subtle and grounded. Use precise verbs with physical scale (e.g., "chin drops 2 cm", "left shoulder rises 1 cm"). Do NOT use adverbs like "energetically", "dramatically", "aggressively", "rapidly", or "intensely". Maximum 2 motion actions per shot block.
- SCENE LOCK: The background environment is completely static. No new objects enter frame. No objects disappear. Lighting is described only as physical fixtures (overhead fluorescent, window light from left, neon sign on wall) — never as animated effects, pulsing strobes, or changing intensity.
- CAMERA DISCIPLINE: Camera is locked-off or on an ultra-slow drift only. No orbit, spin, rapid pan, crash zoom, or handheld shake. Movements must be imperceptible — the viewer should feel stillness.
- KLING MOTION: Do NOT use "freeze-frame", "static freeze", or "freeze" to describe an end state. Kling generates continuous motion throughout — describe the final moment as motion naturally slowing to stillness, a composed held stare, or a gradual deceleration instead.
- SHOT FORMULA: Every timestamped block must follow this structure exactly: [CAMERA TYPE + DISTANCE], [SUBJECT POSITION + ANCHOR]. [MICRO-MOTION with scale]. [LIGHTING SOURCE as physical fixture]. Audio: [ambient sound].
- End with Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, altered bone structure, drifting features, morphing eyes, face deformation, character inconsistency, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features, glowing orbs, energy effects, supernatural light, sci-fi glow, lens flare orbs, light emanating from subject, magical effects, flickering background, shifting environment, morphing walls, background objects appearing, new objects entering frame, animated lighting, pulsing lights, strobe effects, fast motion, sudden movement, exaggerated gestures, camera spin, camera orbit, rapid pan, handheld shake, headphones, earphones, added accessories, spontaneous props, props not in reference
```

---

### Location 2 — `generateStartEnd()` system prompt (~line 2073)

**Search for (exact):**
```javascript
  const systemPrompt=`You are a Kling 3.0 video prompt specialist. Given a START frame and END frame, write a single video prompt that describes the motion connecting them.\nCHARACTER CONSISTENCY: Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description. The subject's face must read as the same person in every frame. This is non-negotiable.\nATTIRE LOCK: Describe the subject's outfit exactly as visible in the provided reference image. Do NOT invent, substitute, or alter any clothing item. Every shot block must reference only garments actually shown in the image — exact colors, garment types, and layering as photographed.\nKLING MOTION: Do NOT use "freeze-frame", "static freeze", or "freeze" to describe an end state. Kling generates continuous motion throughout — describe the final moment as motion naturally slowing to stillness, a composed held stare, or a gradual deceleration instead.\nNEGATIVE PROMPT: Every video_prompt must end with "Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, altered bone structure, drifting features, morphing eyes, face deformation, character inconsistency, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features, glowing orbs, energy effects, supernatural light, sci-fi glow, lens flare orbs, light emanating from subject, magical effects"\nReturn ONLY valid JSON.`;
```

**Replace with:**
```javascript
  const systemPrompt=`You are a Kling 3.0 video prompt specialist. Given a START frame and END frame, write a single video prompt that describes the motion connecting them.\nCHARACTER CONSISTENCY: Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description. The subject's face must read as the same person in every frame. This is non-negotiable.\nATTIRE LOCK: Describe the subject's outfit exactly as visible in the provided reference image. Do NOT invent, substitute, or alter any clothing item. Every shot block must reference only garments actually shown in the image — exact colors, garment types, and layering as photographed.\nPROP LOCK: Do NOT add any accessories, props, or objects not visible in the provided reference image. No headphones, earphones, sunglasses, hats, jewelry, or any item not photographed on the subject.\nMOTION DISCIPLINE: All movements are subtle and grounded. Use precise verbs with physical scale (e.g., "chin drops 2 cm", "left shoulder rises 1 cm"). Do NOT use adverbs like "energetically", "dramatically", "aggressively", "rapidly", or "intensely". Maximum 2 motion actions per shot block.\nSCENE LOCK: The background environment is completely static. No new objects enter frame. No objects disappear. Lighting is described only as physical fixtures (overhead fluorescent, window light from left, neon sign on wall) — never as animated effects, pulsing strobes, or changing intensity.\nCAMERA DISCIPLINE: Camera is locked-off or on an ultra-slow drift only. No orbit, spin, rapid pan, crash zoom, or handheld shake. Movements must be imperceptible — the viewer should feel stillness.\nKLING MOTION: Do NOT use "freeze-frame", "static freeze", or "freeze" to describe an end state. Kling generates continuous motion throughout — describe the final moment as motion naturally slowing to stillness, a composed held stare, or a gradual deceleration instead.\nSHOT FORMULA: Every timestamped block must follow this structure exactly: [CAMERA TYPE + DISTANCE], [SUBJECT POSITION + ANCHOR]. [MICRO-MOTION with scale]. [LIGHTING SOURCE as physical fixture]. Audio: [ambient sound].\nNEGATIVE PROMPT: Every video_prompt must end with "Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, altered bone structure, drifting features, morphing eyes, face deformation, character inconsistency, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features, glowing orbs, energy effects, supernatural light, sci-fi glow, lens flare orbs, light emanating from subject, magical effects, flickering background, shifting environment, morphing walls, background objects appearing, new objects entering frame, animated lighting, pulsing lights, strobe effects, fast motion, sudden movement, exaggerated gestures, camera spin, camera orbit, rapid pan, handheld shake, headphones, earphones, added accessories, spontaneous props, props not in reference"\nReturn ONLY valid JSON.`;
```

---

### Location 3 — `generateGrid9()` system prompt (~line 2122)

`${frames.length}` must be preserved exactly.

**Search for (exact):**
```javascript
  const systemPrompt=`You are a Kling 3.0 video prompt specialist. Given ${frames.length} frames in sequence, create a cohesive mini-movie that connects all frames narratively.\nCHARACTER CONSISTENCY: Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description. The subject's face must read as the same person in every frame. This is non-negotiable.\nATTIRE LOCK: Describe the subject's outfit exactly as visible in the provided reference image. Do NOT invent, substitute, or alter any clothing item. Every shot block must reference only garments actually shown in the image — exact colors, garment types, and layering as photographed.\nKLING MOTION: Do NOT use "freeze-frame", "static freeze", or "freeze" to describe an end state. Kling generates continuous motion throughout — describe the final moment as motion naturally slowing to stillness, a composed held stare, or a gradual deceleration instead.\nNEGATIVE PROMPT: Every video_prompt must end with "Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, altered bone structure, drifting features, morphing eyes, face deformation, character inconsistency, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features, glowing orbs, energy effects, supernatural light, sci-fi glow, lens flare orbs, light emanating from subject, magical effects"\nReturn ONLY valid JSON.`;
```

**Replace with:**
```javascript
  const systemPrompt=`You are a Kling 3.0 video prompt specialist. Given ${frames.length} frames in sequence, create a cohesive mini-movie that connects all frames narratively.\nCHARACTER CONSISTENCY: Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description. The subject's face must read as the same person in every frame. This is non-negotiable.\nATTIRE LOCK: Describe the subject's outfit exactly as visible in the provided reference image. Do NOT invent, substitute, or alter any clothing item. Every shot block must reference only garments actually shown in the image — exact colors, garment types, and layering as photographed.\nPROP LOCK: Do NOT add any accessories, props, or objects not visible in the provided reference image. No headphones, earphones, sunglasses, hats, jewelry, or any item not photographed on the subject.\nMOTION DISCIPLINE: All movements are subtle and grounded. Use precise verbs with physical scale (e.g., "chin drops 2 cm", "left shoulder rises 1 cm"). Do NOT use adverbs like "energetically", "dramatically", "aggressively", "rapidly", or "intensely". Maximum 2 motion actions per shot block.\nSCENE LOCK: The background environment is completely static. No new objects enter frame. No objects disappear. Lighting is described only as physical fixtures (overhead fluorescent, window light from left, neon sign on wall) — never as animated effects, pulsing strobes, or changing intensity.\nCAMERA DISCIPLINE: Camera is locked-off or on an ultra-slow drift only. No orbit, spin, rapid pan, crash zoom, or handheld shake. Movements must be imperceptible — the viewer should feel stillness.\nKLING MOTION: Do NOT use "freeze-frame", "static freeze", or "freeze" to describe an end state. Kling generates continuous motion throughout — describe the final moment as motion naturally slowing to stillness, a composed held stare, or a gradual deceleration instead.\nSHOT FORMULA: Every timestamped block must follow this structure exactly: [CAMERA TYPE + DISTANCE], [SUBJECT POSITION + ANCHOR]. [MICRO-MOTION with scale]. [LIGHTING SOURCE as physical fixture]. Audio: [ambient sound].\nNEGATIVE PROMPT: Every video_prompt must end with "Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, altered bone structure, drifting features, morphing eyes, face deformation, character inconsistency, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features, glowing orbs, energy effects, supernatural light, sci-fi glow, lens flare orbs, light emanating from subject, magical effects, flickering background, shifting environment, morphing walls, background objects appearing, new objects entering frame, animated lighting, pulsing lights, strobe effects, fast motion, sudden movement, exaggerated gestures, camera spin, camera orbit, rapid pan, handheld shake, headphones, earphones, added accessories, spontaneous props, props not in reference"\nReturn ONLY valid JSON.`;
```

---

### Location 4 — `generateSequential()` system prompt (~line 2171)

`${sceneNum}` and `${seqHistory.length>0?'Continue from the previous scene.':'Start the story.'}` must be preserved exactly.

**Search for (exact):**
```javascript
  const systemPrompt=`You are a Kling 3.0 video prompt specialist creating scene ${sceneNum} of a sequential story. ${seqHistory.length>0?'Continue from the previous scene.':'Start the story.'}\nCHARACTER CONSISTENCY: Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description. The subject's face must read as the same person in every frame. This is non-negotiable.\nATTIRE LOCK: Describe the subject's outfit exactly as visible in the provided reference image. Do NOT invent, substitute, or alter any clothing item. Every shot block must reference only garments actually shown in the image — exact colors, garment types, and layering as photographed.\nKLING MOTION: Do NOT use "freeze-frame", "static freeze", or "freeze" to describe an end state. Kling generates continuous motion throughout — describe the final moment as motion naturally slowing to stillness, a composed held stare, or a gradual deceleration instead.\nNEGATIVE PROMPT: Every video_prompt must end with "Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, altered bone structure, drifting features, morphing eyes, face deformation, character inconsistency, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features, glowing orbs, energy effects, supernatural light, sci-fi glow, lens flare orbs, light emanating from subject, magical effects"\nReturn ONLY valid JSON.`;
```

**Replace with:**
```javascript
  const systemPrompt=`You are a Kling 3.0 video prompt specialist creating scene ${sceneNum} of a sequential story. ${seqHistory.length>0?'Continue from the previous scene.':'Start the story.'}\nCHARACTER CONSISTENCY: Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description. The subject's face must read as the same person in every frame. This is non-negotiable.\nATTIRE LOCK: Describe the subject's outfit exactly as visible in the provided reference image. Do NOT invent, substitute, or alter any clothing item. Every shot block must reference only garments actually shown in the image — exact colors, garment types, and layering as photographed.\nPROP LOCK: Do NOT add any accessories, props, or objects not visible in the provided reference image. No headphones, earphones, sunglasses, hats, jewelry, or any item not photographed on the subject.\nMOTION DISCIPLINE: All movements are subtle and grounded. Use precise verbs with physical scale (e.g., "chin drops 2 cm", "left shoulder rises 1 cm"). Do NOT use adverbs like "energetically", "dramatically", "aggressively", "rapidly", or "intensely". Maximum 2 motion actions per shot block.\nSCENE LOCK: The background environment is completely static. No new objects enter frame. No objects disappear. Lighting is described only as physical fixtures (overhead fluorescent, window light from left, neon sign on wall) — never as animated effects, pulsing strobes, or changing intensity.\nCAMERA DISCIPLINE: Camera is locked-off or on an ultra-slow drift only. No orbit, spin, rapid pan, crash zoom, or handheld shake. Movements must be imperceptible — the viewer should feel stillness.\nKLING MOTION: Do NOT use "freeze-frame", "static freeze", or "freeze" to describe an end state. Kling generates continuous motion throughout — describe the final moment as motion naturally slowing to stillness, a composed held stare, or a gradual deceleration instead.\nSHOT FORMULA: Every timestamped block must follow this structure exactly: [CAMERA TYPE + DISTANCE], [SUBJECT POSITION + ANCHOR]. [MICRO-MOTION with scale]. [LIGHTING SOURCE as physical fixture]. Audio: [ambient sound].\nNEGATIVE PROMPT: Every video_prompt must end with "Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, altered bone structure, drifting features, morphing eyes, face deformation, character inconsistency, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features, glowing orbs, energy effects, supernatural light, sci-fi glow, lens flare orbs, light emanating from subject, magical effects, flickering background, shifting environment, morphing walls, background objects appearing, new objects entering frame, animated lighting, pulsing lights, strobe effects, fast motion, sudden movement, exaggerated gestures, camera spin, camera orbit, rapid pan, handheld shake, headphones, earphones, added accessories, spontaneous props, props not in reference"\nReturn ONLY valid JSON.`;
```

---

## Implementation Order

1. Location 1 — `buildPromptSystem()` bullet list
2. Locations 2, 3, 4 — inline system prompts
3. Commit and push

---

## Success Criteria

- `grep -c "PROP LOCK" index.html` = 4
- `grep -c "MOTION DISCIPLINE" index.html` = 4
- `grep -c "SCENE LOCK" index.html` = 4
- `grep -c "CAMERA DISCIPLINE" index.html` = 4
- `grep -c "SHOT FORMULA" index.html` = 4
- `grep -c "props not in reference" index.html` = 4
- Template literals `${frames.length}`, `${sceneNum}`, `${seqHistory.length>0?...:...}` preserved in Locations 3 and 4
- No UI changes
