# Kling Comprehensive Video Quality Enhancement Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add PROP LOCK, MOTION DISCIPLINE, SCENE LOCK, CAMERA DISCIPLINE, SHOT FORMULA rules and expand negatives across all 4 Kling system prompt locations to eliminate prop injection, motion exaggeration, environment instability, camera chaos, and unstructured shot blocks.

**Architecture:** 4 direct string replacements in `index.html` — no new functions, no UI changes, no new files. Each replacement inserts 4 new rules between ATTIRE LOCK and KLING MOTION, adds SHOT FORMULA after KLING MOTION, and expands the negative list with 19 new terms.

**Tech Stack:** Plain HTML/JS — edit `index.html` directly. No build step.

**Spec:** `docs/superpowers/specs/2026-03-11-kling-video-quality-design.md`

---

## Task 1: Update buildPromptSystem() Kling block

**Files:**
- Modify: `G:\My Drive\Apulu Prompt Generator\index.html` (~lines 1804–1807)

**Context:** Inside `${onlyOutput!=='nb2'?`...`:''}` conditional — do NOT disturb the wrapper. Location 1 uses bullet-list format with physical newlines (not `\n`).

- [ ] **Step 1: Apply the replacement**

Search for (exact — 4 lines):
```
- CHARACTER CONSISTENCY: Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description. The subject's face must read as the same person in every frame. This is non-negotiable.
- ATTIRE LOCK: Describe the subject's outfit exactly as visible in the provided reference image. Do NOT invent, substitute, or alter any clothing item. Every shot block must reference only garments actually shown in the image — exact colors, garment types, and layering as photographed.
- KLING MOTION: Do NOT use "freeze-frame", "static freeze", or "freeze" to describe an end state. Kling generates continuous motion throughout — describe the final moment as motion naturally slowing to stillness, a composed held stare, or a gradual deceleration instead.
- End with Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, altered bone structure, drifting features, morphing eyes, face deformation, character inconsistency, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features, glowing orbs, energy effects, supernatural light, sci-fi glow, lens flare orbs, light emanating from subject, magical effects
```

Replace with (exact — 9 lines):
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

- [ ] **Step 2: Verify**

```bash
grep -c "PROP LOCK" "G:\My Drive\Apulu Prompt Generator\index.html"
```
Expected: 1

```bash
grep -c "props not in reference" "G:\My Drive\Apulu Prompt Generator\index.html"
```
Expected: 1

- [ ] **Step 3: Commit**

```bash
cd "G:\My Drive\Apulu Prompt Generator"
git add index.html
git commit -m "feat: add PROP LOCK, MOTION DISCIPLINE, SCENE LOCK, CAMERA DISCIPLINE, SHOT FORMULA to buildPromptSystem"
```

---

## Task 2: Update generateStartEnd, generateGrid9, generateSequential + push

**Files:**
- Modify: `G:\My Drive\Apulu Prompt Generator\index.html` (~lines 2073, 2122, 2171)

**Context:** Three inline system prompts using `\n` (escaped backslash-n) as separators — NOT physical newlines. Template literals must be preserved:
- Location 3 (`generateGrid9`): `${frames.length}`
- Location 4 (`generateSequential`): `${sceneNum}` and `${seqHistory.length>0?'Continue from the previous scene.':'Start the story.'}`

### Edit 1 — generateStartEnd (~line 2073)

Search for (exact single-line JS string):
```javascript
  const systemPrompt=`You are a Kling 3.0 video prompt specialist. Given a START frame and END frame, write a single video prompt that describes the motion connecting them.\nCHARACTER CONSISTENCY: Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description. The subject's face must read as the same person in every frame. This is non-negotiable.\nATTIRE LOCK: Describe the subject's outfit exactly as visible in the provided reference image. Do NOT invent, substitute, or alter any clothing item. Every shot block must reference only garments actually shown in the image — exact colors, garment types, and layering as photographed.\nKLING MOTION: Do NOT use "freeze-frame", "static freeze", or "freeze" to describe an end state. Kling generates continuous motion throughout — describe the final moment as motion naturally slowing to stillness, a composed held stare, or a gradual deceleration instead.\nNEGATIVE PROMPT: Every video_prompt must end with "Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, altered bone structure, drifting features, morphing eyes, face deformation, character inconsistency, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features, glowing orbs, energy effects, supernatural light, sci-fi glow, lens flare orbs, light emanating from subject, magical effects"\nReturn ONLY valid JSON.`;
```

Replace with:
```javascript
  const systemPrompt=`You are a Kling 3.0 video prompt specialist. Given a START frame and END frame, write a single video prompt that describes the motion connecting them.\nCHARACTER CONSISTENCY: Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description. The subject's face must read as the same person in every frame. This is non-negotiable.\nATTIRE LOCK: Describe the subject's outfit exactly as visible in the provided reference image. Do NOT invent, substitute, or alter any clothing item. Every shot block must reference only garments actually shown in the image — exact colors, garment types, and layering as photographed.\nPROP LOCK: Do NOT add any accessories, props, or objects not visible in the provided reference image. No headphones, earphones, sunglasses, hats, jewelry, or any item not photographed on the subject.\nMOTION DISCIPLINE: All movements are subtle and grounded. Use precise verbs with physical scale (e.g., "chin drops 2 cm", "left shoulder rises 1 cm"). Do NOT use adverbs like "energetically", "dramatically", "aggressively", "rapidly", or "intensely". Maximum 2 motion actions per shot block.\nSCENE LOCK: The background environment is completely static. No new objects enter frame. No objects disappear. Lighting is described only as physical fixtures (overhead fluorescent, window light from left, neon sign on wall) — never as animated effects, pulsing strobes, or changing intensity.\nCAMERA DISCIPLINE: Camera is locked-off or on an ultra-slow drift only. No orbit, spin, rapid pan, crash zoom, or handheld shake. Movements must be imperceptible — the viewer should feel stillness.\nKLING MOTION: Do NOT use "freeze-frame", "static freeze", or "freeze" to describe an end state. Kling generates continuous motion throughout — describe the final moment as motion naturally slowing to stillness, a composed held stare, or a gradual deceleration instead.\nSHOT FORMULA: Every timestamped block must follow this structure exactly: [CAMERA TYPE + DISTANCE], [SUBJECT POSITION + ANCHOR]. [MICRO-MOTION with scale]. [LIGHTING SOURCE as physical fixture]. Audio: [ambient sound].\nNEGATIVE PROMPT: Every video_prompt must end with "Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, altered bone structure, drifting features, morphing eyes, face deformation, character inconsistency, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features, glowing orbs, energy effects, supernatural light, sci-fi glow, lens flare orbs, light emanating from subject, magical effects, flickering background, shifting environment, morphing walls, background objects appearing, new objects entering frame, animated lighting, pulsing lights, strobe effects, fast motion, sudden movement, exaggerated gestures, camera spin, camera orbit, rapid pan, handheld shake, headphones, earphones, added accessories, spontaneous props, props not in reference"\nReturn ONLY valid JSON.`;
```

### Edit 2 — generateGrid9 (~line 2122)

Search for (exact — `${frames.length}` is a live template literal):
```javascript
  const systemPrompt=`You are a Kling 3.0 video prompt specialist. Given ${frames.length} frames in sequence, create a cohesive mini-movie that connects all frames narratively.\nCHARACTER CONSISTENCY: Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description. The subject's face must read as the same person in every frame. This is non-negotiable.\nATTIRE LOCK: Describe the subject's outfit exactly as visible in the provided reference image. Do NOT invent, substitute, or alter any clothing item. Every shot block must reference only garments actually shown in the image — exact colors, garment types, and layering as photographed.\nKLING MOTION: Do NOT use "freeze-frame", "static freeze", or "freeze" to describe an end state. Kling generates continuous motion throughout — describe the final moment as motion naturally slowing to stillness, a composed held stare, or a gradual deceleration instead.\nNEGATIVE PROMPT: Every video_prompt must end with "Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, altered bone structure, drifting features, morphing eyes, face deformation, character inconsistency, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features, glowing orbs, energy effects, supernatural light, sci-fi glow, lens flare orbs, light emanating from subject, magical effects"\nReturn ONLY valid JSON.`;
```

Replace with:
```javascript
  const systemPrompt=`You are a Kling 3.0 video prompt specialist. Given ${frames.length} frames in sequence, create a cohesive mini-movie that connects all frames narratively.\nCHARACTER CONSISTENCY: Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description. The subject's face must read as the same person in every frame. This is non-negotiable.\nATTIRE LOCK: Describe the subject's outfit exactly as visible in the provided reference image. Do NOT invent, substitute, or alter any clothing item. Every shot block must reference only garments actually shown in the image — exact colors, garment types, and layering as photographed.\nPROP LOCK: Do NOT add any accessories, props, or objects not visible in the provided reference image. No headphones, earphones, sunglasses, hats, jewelry, or any item not photographed on the subject.\nMOTION DISCIPLINE: All movements are subtle and grounded. Use precise verbs with physical scale (e.g., "chin drops 2 cm", "left shoulder rises 1 cm"). Do NOT use adverbs like "energetically", "dramatically", "aggressively", "rapidly", or "intensely". Maximum 2 motion actions per shot block.\nSCENE LOCK: The background environment is completely static. No new objects enter frame. No objects disappear. Lighting is described only as physical fixtures (overhead fluorescent, window light from left, neon sign on wall) — never as animated effects, pulsing strobes, or changing intensity.\nCAMERA DISCIPLINE: Camera is locked-off or on an ultra-slow drift only. No orbit, spin, rapid pan, crash zoom, or handheld shake. Movements must be imperceptible — the viewer should feel stillness.\nKLING MOTION: Do NOT use "freeze-frame", "static freeze", or "freeze" to describe an end state. Kling generates continuous motion throughout — describe the final moment as motion naturally slowing to stillness, a composed held stare, or a gradual deceleration instead.\nSHOT FORMULA: Every timestamped block must follow this structure exactly: [CAMERA TYPE + DISTANCE], [SUBJECT POSITION + ANCHOR]. [MICRO-MOTION with scale]. [LIGHTING SOURCE as physical fixture]. Audio: [ambient sound].\nNEGATIVE PROMPT: Every video_prompt must end with "Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, altered bone structure, drifting features, morphing eyes, face deformation, character inconsistency, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features, glowing orbs, energy effects, supernatural light, sci-fi glow, lens flare orbs, light emanating from subject, magical effects, flickering background, shifting environment, morphing walls, background objects appearing, new objects entering frame, animated lighting, pulsing lights, strobe effects, fast motion, sudden movement, exaggerated gestures, camera spin, camera orbit, rapid pan, handheld shake, headphones, earphones, added accessories, spontaneous props, props not in reference"\nReturn ONLY valid JSON.`;
```

### Edit 3 — generateSequential (~line 2171)

Search for (exact — preserve both `${sceneNum}` and `${seqHistory.length>0?'Continue from the previous scene.':'Start the story.'}`):
```javascript
  const systemPrompt=`You are a Kling 3.0 video prompt specialist creating scene ${sceneNum} of a sequential story. ${seqHistory.length>0?'Continue from the previous scene.':'Start the story.'}\nCHARACTER CONSISTENCY: Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description. The subject's face must read as the same person in every frame. This is non-negotiable.\nATTIRE LOCK: Describe the subject's outfit exactly as visible in the provided reference image. Do NOT invent, substitute, or alter any clothing item. Every shot block must reference only garments actually shown in the image — exact colors, garment types, and layering as photographed.\nKLING MOTION: Do NOT use "freeze-frame", "static freeze", or "freeze" to describe an end state. Kling generates continuous motion throughout — describe the final moment as motion naturally slowing to stillness, a composed held stare, or a gradual deceleration instead.\nNEGATIVE PROMPT: Every video_prompt must end with "Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, altered bone structure, drifting features, morphing eyes, face deformation, character inconsistency, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features, glowing orbs, energy effects, supernatural light, sci-fi glow, lens flare orbs, light emanating from subject, magical effects"\nReturn ONLY valid JSON.`;
```

Replace with:
```javascript
  const systemPrompt=`You are a Kling 3.0 video prompt specialist creating scene ${sceneNum} of a sequential story. ${seqHistory.length>0?'Continue from the previous scene.':'Start the story.'}\nCHARACTER CONSISTENCY: Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description. The subject's face must read as the same person in every frame. This is non-negotiable.\nATTIRE LOCK: Describe the subject's outfit exactly as visible in the provided reference image. Do NOT invent, substitute, or alter any clothing item. Every shot block must reference only garments actually shown in the image — exact colors, garment types, and layering as photographed.\nPROP LOCK: Do NOT add any accessories, props, or objects not visible in the provided reference image. No headphones, earphones, sunglasses, hats, jewelry, or any item not photographed on the subject.\nMOTION DISCIPLINE: All movements are subtle and grounded. Use precise verbs with physical scale (e.g., "chin drops 2 cm", "left shoulder rises 1 cm"). Do NOT use adverbs like "energetically", "dramatically", "aggressively", "rapidly", or "intensely". Maximum 2 motion actions per shot block.\nSCENE LOCK: The background environment is completely static. No new objects enter frame. No objects disappear. Lighting is described only as physical fixtures (overhead fluorescent, window light from left, neon sign on wall) — never as animated effects, pulsing strobes, or changing intensity.\nCAMERA DISCIPLINE: Camera is locked-off or on an ultra-slow drift only. No orbit, spin, rapid pan, crash zoom, or handheld shake. Movements must be imperceptible — the viewer should feel stillness.\nKLING MOTION: Do NOT use "freeze-frame", "static freeze", or "freeze" to describe an end state. Kling generates continuous motion throughout — describe the final moment as motion naturally slowing to stillness, a composed held stare, or a gradual deceleration instead.\nSHOT FORMULA: Every timestamped block must follow this structure exactly: [CAMERA TYPE + DISTANCE], [SUBJECT POSITION + ANCHOR]. [MICRO-MOTION with scale]. [LIGHTING SOURCE as physical fixture]. Audio: [ambient sound].\nNEGATIVE PROMPT: Every video_prompt must end with "Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, altered bone structure, drifting features, morphing eyes, face deformation, character inconsistency, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features, glowing orbs, energy effects, supernatural light, sci-fi glow, lens flare orbs, light emanating from subject, magical effects, flickering background, shifting environment, morphing walls, background objects appearing, new objects entering frame, animated lighting, pulsing lights, strobe effects, fast motion, sudden movement, exaggerated gestures, camera spin, camera orbit, rapid pan, handheld shake, headphones, earphones, added accessories, spontaneous props, props not in reference"\nReturn ONLY valid JSON.`;
```

- [ ] **Step 1: Apply all 3 edits above**

- [ ] **Step 2: Final verification**

```bash
grep -c "PROP LOCK" "G:\My Drive\Apulu Prompt Generator\index.html"
```
Expected: **4**

```bash
grep -c "MOTION DISCIPLINE" "G:\My Drive\Apulu Prompt Generator\index.html"
```
Expected: **4**

```bash
grep -c "SCENE LOCK" "G:\My Drive\Apulu Prompt Generator\index.html"
```
Expected: **4**

```bash
grep -c "CAMERA DISCIPLINE" "G:\My Drive\Apulu Prompt Generator\index.html"
```
Expected: **4**

```bash
grep -c "SHOT FORMULA" "G:\My Drive\Apulu Prompt Generator\index.html"
```
Expected: **4**

```bash
grep -c "props not in reference" "G:\My Drive\Apulu Prompt Generator\index.html"
```
Expected: **4**

- [ ] **Step 3: Commit and push**

```bash
cd "G:\My Drive\Apulu Prompt Generator"
git add index.html
git commit -m "feat: add PROP LOCK, MOTION DISCIPLINE, SCENE LOCK, CAMERA DISCIPLINE, SHOT FORMULA to all inline Kling prompts"
git push origin main
```
