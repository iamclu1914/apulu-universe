# Kling Character Consistency Hardening — Design Spec
**Date:** 2026-03-11
**Status:** Approved
**Scope:** `index.html` only — 4 Kling system prompt locations

---

## Problem

All Kling video generation paths produce face warping and morphing during playback. The LLM-generated video prompts contain no character consistency anchors per shot block, and the negative prompts on most paths are critically thin. Kling needs explicit per-shot lock language to maintain facial identity across frames.

---

## Solution Overview

Two changes applied uniformly to all 4 Kling system prompt locations:

1. **Consistency anchor rule** — mandate that every `[timestamp]` shot block opens with a fixed character lock phrase
2. **Expanded negative prompt** — replace the current minimal negative list with a comprehensive face-warping prevention list

No UI changes. No new fields. Pure system prompt hardening.

---

## Section 1 — Consistency Anchor Rule

Rule added to all 4 Kling system prompts:

> CHARACTER CONSISTENCY: Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description. The subject's face must read as the same person in every frame. This is non-negotiable.

### Expected LLM Output

```
[0:00-0:04] Maintaining subject's identical facial features, bone structure, and skin tone throughout — medium shot, artist stands at window, slow head turn left, golden hour light rakes across cheek. Audio: distant traffic hum.
```

---

## Section 2 — Expanded Negative Prompt

**Old:**
```
smiling, laughing, cartoonish, morphing, blurry faces
```

**New (all Kling paths):**
```
smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, altered bone structure, drifting features, morphing eyes, face deformation, character inconsistency, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features
```

---

## Section 3 — Exact Code Changes

### Location 1 — `buildPromptSystem()` Kling block (lines 1799–1805)

The Kling block is inside `${onlyOutput!=='nb2'?`...`:''}` — do not disturb the conditional wrapper.

**Search for (exact):**
```
${onlyOutput!=='nb2'?`KLING 3.0 VIDEO PROMPT GUIDELINES:
- 3-5 timestamped shot blocks, MAX 15 seconds total
- Format: [0:00-0:03] Environment first, then shot type, camera movement, micro-actions, audio layer
- 80-120 words total
- Include explicit end-state on final shot
- End with Negative: smiling, laughing, cartoonish, morphing, blurry faces
`:''}
```

**Replace with:**
```
${onlyOutput!=='nb2'?`KLING 3.0 VIDEO PROMPT GUIDELINES:
- 3-5 timestamped shot blocks, MAX 15 seconds total
- Format: [0:00-0:03] Environment first, then shot type, camera movement, micro-actions, audio layer
- 80-120 words total
- Include explicit end-state on final shot
- CHARACTER CONSISTENCY: Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description. The subject's face must read as the same person in every frame. This is non-negotiable.
- End with Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, altered bone structure, drifting features, morphing eyes, face deformation, character inconsistency, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features
`:''}
```

---

### Location 2 — `generateStartEnd()` system prompt (line 2070)

**Search for (exact):**
```javascript
  const systemPrompt=`You are a Kling 3.0 video prompt specialist. Given a START frame and END frame, write a single video prompt that describes the motion connecting them. Return ONLY valid JSON.`;
```

**Replace with:**
```javascript
  const systemPrompt=`You are a Kling 3.0 video prompt specialist. Given a START frame and END frame, write a single video prompt that describes the motion connecting them.\nCHARACTER CONSISTENCY: Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description. The subject's face must read as the same person in every frame. This is non-negotiable.\nNEGATIVE PROMPT: Every video_prompt must end with "Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, altered bone structure, drifting features, morphing eyes, face deformation, character inconsistency, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features"\nReturn ONLY valid JSON.`;
```

---

### Location 3 — `generateGrid9()` system prompt (line 2119)

**Search for (exact):**
```javascript
  const systemPrompt=`You are a Kling 3.0 video prompt specialist. Given ${frames.length} frames in sequence, create a cohesive mini-movie that connects all frames narratively. Return ONLY valid JSON.`;
```

**Replace with:**
```javascript
  const systemPrompt=`You are a Kling 3.0 video prompt specialist. Given ${frames.length} frames in sequence, create a cohesive mini-movie that connects all frames narratively.\nCHARACTER CONSISTENCY: Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description. The subject's face must read as the same person in every frame. This is non-negotiable.\nNEGATIVE PROMPT: Every video_prompt must end with "Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, altered bone structure, drifting features, morphing eyes, face deformation, character inconsistency, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features"\nReturn ONLY valid JSON.`;
```

Note: `${frames.length}` is a live template literal — preserve it exactly.

---

### Location 4 — `generateSequential()` system prompt (line 2168)

**Search for (exact):**
```javascript
  const systemPrompt=`You are a Kling 3.0 video prompt specialist creating scene ${sceneNum} of a sequential story. ${seqHistory.length>0?'Continue from the previous scene.':'Start the story.'} Return ONLY valid JSON.`;
```

**Replace with:**
```javascript
  const systemPrompt=`You are a Kling 3.0 video prompt specialist creating scene ${sceneNum} of a sequential story. ${seqHistory.length>0?'Continue from the previous scene.':'Start the story.'}\nCHARACTER CONSISTENCY: Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description. The subject's face must read as the same person in every frame. This is non-negotiable.\nNEGATIVE PROMPT: Every video_prompt must end with "Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, altered bone structure, drifting features, morphing eyes, face deformation, character inconsistency, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features"\nReturn ONLY valid JSON.`;
```

Note: `${sceneNum}` and `${seqHistory.length>0?...:...}` are live template literals — preserve them exactly.

---

## Implementation Order

1. Location 1 — `buildPromptSystem()` Kling block
2. Location 2 — `generateStartEnd()` system prompt
3. Location 3 — `generateGrid9()` system prompt
4. Location 4 — `generateSequential()` system prompt
5. Commit and push

---

## Success Criteria

- Every Kling-generated video prompt opens each shot block with the consistency anchor phrase
- The expanded negative list appears at the end of every Kling video prompt output
- All 4 Kling generation paths updated (verifiable via code diff)
- No UI changes introduced
- The conditional wrapper `${onlyOutput!=='nb2'?...''}` in Location 1 is intact
- Template literals (`${frames.length}`, `${sceneNum}`, `${seqHistory.length>0?...:...}`) in Locations 3 and 4 are preserved exactly
