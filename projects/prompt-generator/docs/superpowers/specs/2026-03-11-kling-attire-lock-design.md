# Kling Prompt Hardening — Attire Lock, Motion Rules, Expanded Negatives — Design Spec
**Date:** 2026-03-11
**Status:** Approved
**Scope:** `index.html` only — same 4 Kling system prompt locations as character consistency

---

## Problem

Three issues with current Kling video prompt generation:

1. **Hallucinated attire** — LLM invents clothing instead of reading the reference image (e.g., generates "silver reflective cropped windbreaker" when reference shows a dark charcoal zip hoodie)
2. **Freeze-frame language** — LLM writes "ending in a sharp, static freeze-frame" which Kling doesn't support; Kling interprets it as a dramatic flourish and adds sci-fi effects
3. **Supernatural light artifacts** — "pulsing strobes" + dramatic end instruction causes Kling to generate glowing energy orbs emanating from the subject's body

---

## Solution

Three new rules added to all 4 Kling system prompt locations, in this order after CHARACTER CONSISTENCY:

1. **ATTIRE LOCK** — describe outfit exactly from reference image, never invent
2. **KLING MOTION** — no freeze-frame language; describe endings as motion slowing to stillness
3. **Expanded negative prompt** — add supernatural/energy artifact terms to existing negative list

---

## Rule Text

### ATTIRE LOCK
```
ATTIRE LOCK: Describe the subject's outfit exactly as visible in the provided reference image. Do NOT invent, substitute, or alter any clothing item. Every shot block must reference only garments actually shown in the image — exact colors, garment types, and layering as photographed.
```

### KLING MOTION
```
KLING MOTION: Do NOT use "freeze-frame", "static freeze", or "freeze" to describe an end state. Kling generates continuous motion throughout — describe the final moment as motion naturally slowing to stillness, a composed held stare, or a gradual deceleration instead.
```

### Expanded negative additions
Add to the end of every existing negative list:
```
glowing orbs, energy effects, supernatural light, sci-fi glow, lens flare orbs, light emanating from subject, magical effects
```

---

## Affected Locations

### Location 1 — `buildPromptSystem()` Kling block (~lines 1804–1805)

**Search for:**
```
- CHARACTER CONSISTENCY: Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description. The subject's face must read as the same person in every frame. This is non-negotiable.
- End with Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, altered bone structure, drifting features, morphing eyes, face deformation, character inconsistency, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features
```

**Replace with:**
```
- CHARACTER CONSISTENCY: Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description. The subject's face must read as the same person in every frame. This is non-negotiable.
- ATTIRE LOCK: Describe the subject's outfit exactly as visible in the provided reference image. Do NOT invent, substitute, or alter any clothing item. Every shot block must reference only garments actually shown in the image — exact colors, garment types, and layering as photographed.
- KLING MOTION: Do NOT use "freeze-frame", "static freeze", or "freeze" to describe an end state. Kling generates continuous motion throughout — describe the final moment as motion naturally slowing to stillness, a composed held stare, or a gradual deceleration instead.
- End with Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, altered bone structure, drifting features, morphing eyes, face deformation, character inconsistency, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features, glowing orbs, energy effects, supernatural light, sci-fi glow, lens flare orbs, light emanating from subject, magical effects
```

---

### Location 2 — `generateStartEnd()` system prompt (~line 2071)

**Search for:**
```javascript
  const systemPrompt=`You are a Kling 3.0 video prompt specialist. Given a START frame and END frame, write a single video prompt that describes the motion connecting them.\nCHARACTER CONSISTENCY: Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description. The subject's face must read as the same person in every frame. This is non-negotiable.\nNEGATIVE PROMPT: Every video_prompt must end with "Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, altered bone structure, drifting features, morphing eyes, face deformation, character inconsistency, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features"\nReturn ONLY valid JSON.`;
```

**Replace with:**
```javascript
  const systemPrompt=`You are a Kling 3.0 video prompt specialist. Given a START frame and END frame, write a single video prompt that describes the motion connecting them.\nCHARACTER CONSISTENCY: Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description. The subject's face must read as the same person in every frame. This is non-negotiable.\nATTIRE LOCK: Describe the subject's outfit exactly as visible in the provided reference image. Do NOT invent, substitute, or alter any clothing item. Every shot block must reference only garments actually shown in the image — exact colors, garment types, and layering as photographed.\nKLING MOTION: Do NOT use "freeze-frame", "static freeze", or "freeze" to describe an end state. Kling generates continuous motion throughout — describe the final moment as motion naturally slowing to stillness, a composed held stare, or a gradual deceleration instead.\nNEGATIVE PROMPT: Every video_prompt must end with "Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, altered bone structure, drifting features, morphing eyes, face deformation, character inconsistency, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features, glowing orbs, energy effects, supernatural light, sci-fi glow, lens flare orbs, light emanating from subject, magical effects"\nReturn ONLY valid JSON.`;
```

---

### Location 3 — `generateGrid9()` system prompt (~line 2120)

`${frames.length}` must be preserved exactly.

**Search for:**
```javascript
  const systemPrompt=`You are a Kling 3.0 video prompt specialist. Given ${frames.length} frames in sequence, create a cohesive mini-movie that connects all frames narratively.\nCHARACTER CONSISTENCY: Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description. The subject's face must read as the same person in every frame. This is non-negotiable.\nNEGATIVE PROMPT: Every video_prompt must end with "Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, altered bone structure, drifting features, morphing eyes, face deformation, character inconsistency, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features"\nReturn ONLY valid JSON.`;
```

**Replace with:**
```javascript
  const systemPrompt=`You are a Kling 3.0 video prompt specialist. Given ${frames.length} frames in sequence, create a cohesive mini-movie that connects all frames narratively.\nCHARACTER CONSISTENCY: Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description. The subject's face must read as the same person in every frame. This is non-negotiable.\nATTIRE LOCK: Describe the subject's outfit exactly as visible in the provided reference image. Do NOT invent, substitute, or alter any clothing item. Every shot block must reference only garments actually shown in the image — exact colors, garment types, and layering as photographed.\nKLING MOTION: Do NOT use "freeze-frame", "static freeze", or "freeze" to describe an end state. Kling generates continuous motion throughout — describe the final moment as motion naturally slowing to stillness, a composed held stare, or a gradual deceleration instead.\nNEGATIVE PROMPT: Every video_prompt must end with "Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, altered bone structure, drifting features, morphing eyes, face deformation, character inconsistency, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features, glowing orbs, energy effects, supernatural light, sci-fi glow, lens flare orbs, light emanating from subject, magical effects"\nReturn ONLY valid JSON.`;
```

---

### Location 4 — `generateSequential()` system prompt (~line 2169)

`${sceneNum}` and `${seqHistory.length>0?'Continue from the previous scene.':'Start the story.'}` must be preserved exactly.

**Search for:**
```javascript
  const systemPrompt=`You are a Kling 3.0 video prompt specialist creating scene ${sceneNum} of a sequential story. ${seqHistory.length>0?'Continue from the previous scene.':'Start the story.'}\nCHARACTER CONSISTENCY: Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description. The subject's face must read as the same person in every frame. This is non-negotiable.\nNEGATIVE PROMPT: Every video_prompt must end with "Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, altered bone structure, drifting features, morphing eyes, face deformation, character inconsistency, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features"\nReturn ONLY valid JSON.`;
```

**Replace with:**
```javascript
  const systemPrompt=`You are a Kling 3.0 video prompt specialist creating scene ${sceneNum} of a sequential story. ${seqHistory.length>0?'Continue from the previous scene.':'Start the story.'}\nCHARACTER CONSISTENCY: Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description. The subject's face must read as the same person in every frame. This is non-negotiable.\nATTIRE LOCK: Describe the subject's outfit exactly as visible in the provided reference image. Do NOT invent, substitute, or alter any clothing item. Every shot block must reference only garments actually shown in the image — exact colors, garment types, and layering as photographed.\nKLING MOTION: Do NOT use "freeze-frame", "static freeze", or "freeze" to describe an end state. Kling generates continuous motion throughout — describe the final moment as motion naturally slowing to stillness, a composed held stare, or a gradual deceleration instead.\nNEGATIVE PROMPT: Every video_prompt must end with "Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, altered bone structure, drifting features, morphing eyes, face deformation, character inconsistency, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features, glowing orbs, energy effects, supernatural light, sci-fi glow, lens flare orbs, light emanating from subject, magical effects"\nReturn ONLY valid JSON.`;
```

---

## Implementation Order

1. Location 1 — `buildPromptSystem()` Kling block
2. Locations 2, 3, 4 — inline system prompts
3. Commit and push

---

## Success Criteria

- `grep -c "ATTIRE LOCK" index.html` = 4
- `grep -c "KLING MOTION" index.html` = 4
- `grep -c "magical effects" index.html` = 4
- `grep -c "freeze-frame" index.html` = 0 (rule prevents LLM from using it; rule text itself uses it in quotes within a prohibition — acceptable)
- Template literals preserved in Locations 3 and 4
- No UI changes
