# Kling Attire Lock + Motion Rules + Expanded Negatives Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add ATTIRE LOCK, KLING MOTION, and expanded supernatural-artifact negatives to all 4 Kling system prompt locations to prevent hallucinated outfits, freeze-frame misinterpretations, and glowing energy orb artifacts.

**Architecture:** 4 direct string replacements in `index.html` — no new functions, no UI changes, no new files. Each replacement inserts two new rule clauses (ATTIRE LOCK, KLING MOTION) between the existing CHARACTER CONSISTENCY rule and the NEGATIVE PROMPT, and expands the negative list with 7 new terms.

**Tech Stack:** Plain HTML/JS — edit `index.html` directly. No build step.

---

## Task 1: Update buildPromptSystem() Kling block

**Files:**
- Modify: `G:\My Drive\Apulu Prompt Generator\index.html` (~lines 1804–1805)

**Context:** Inside `${onlyOutput!=='nb2'?`...`:''}` conditional — do NOT disturb the wrapper.

- [ ] **Step 1: Apply the replacement**

Search for (exact):
```
- CHARACTER CONSISTENCY: Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description. The subject's face must read as the same person in every frame. This is non-negotiable.
- End with Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, altered bone structure, drifting features, morphing eyes, face deformation, character inconsistency, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features
```

Replace with:
```
- CHARACTER CONSISTENCY: Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description. The subject's face must read as the same person in every frame. This is non-negotiable.
- ATTIRE LOCK: Describe the subject's outfit exactly as visible in the provided reference image. Do NOT invent, substitute, or alter any clothing item. Every shot block must reference only garments actually shown in the image — exact colors, garment types, and layering as photographed.
- KLING MOTION: Do NOT use "freeze-frame", "static freeze", or "freeze" to describe an end state. Kling generates continuous motion throughout — describe the final moment as motion naturally slowing to stillness, a composed held stare, or a gradual deceleration instead.
- End with Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, altered bone structure, drifting features, morphing eyes, face deformation, character inconsistency, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features, glowing orbs, energy effects, supernatural light, sci-fi glow, lens flare orbs, light emanating from subject, magical effects
```

- [ ] **Step 2: Verify**

```bash
grep -c "ATTIRE LOCK" "G:\My Drive\Apulu Prompt Generator\index.html"
```
Expected: 1

```bash
grep -c "KLING MOTION" "G:\My Drive\Apulu Prompt Generator\index.html"
```
Expected: 1

- [ ] **Step 3: Commit**

```bash
cd "G:\My Drive\Apulu Prompt Generator"
git add index.html
git commit -m "feat: add ATTIRE LOCK, KLING MOTION rules and expanded negatives to buildPromptSystem"
```

---

## Task 2: Update generateStartEnd, generateGrid9, generateSequential + push

**Files:**
- Modify: `G:\My Drive\Apulu Prompt Generator\index.html` (~lines 2071, 2120, 2169)

**Context:** Three inline system prompts. Template literals must be preserved:
- Location 3 (`generateGrid9`): `${frames.length}`
- Location 4 (`generateSequential`): `${sceneNum}` and `${seqHistory.length>0?'Continue from the previous scene.':'Start the story.'}`

### Edit 1 — generateStartEnd (~line 2071)

Search for (exact):
```javascript
  const systemPrompt=`You are a Kling 3.0 video prompt specialist. Given a START frame and END frame, write a single video prompt that describes the motion connecting them.\nCHARACTER CONSISTENCY: Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description. The subject's face must read as the same person in every frame. This is non-negotiable.\nNEGATIVE PROMPT: Every video_prompt must end with "Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, altered bone structure, drifting features, morphing eyes, face deformation, character inconsistency, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features"\nReturn ONLY valid JSON.`;
```

Replace with:
```javascript
  const systemPrompt=`You are a Kling 3.0 video prompt specialist. Given a START frame and END frame, write a single video prompt that describes the motion connecting them.\nCHARACTER CONSISTENCY: Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description. The subject's face must read as the same person in every frame. This is non-negotiable.\nATTIRE LOCK: Describe the subject's outfit exactly as visible in the provided reference image. Do NOT invent, substitute, or alter any clothing item. Every shot block must reference only garments actually shown in the image — exact colors, garment types, and layering as photographed.\nKLING MOTION: Do NOT use "freeze-frame", "static freeze", or "freeze" to describe an end state. Kling generates continuous motion throughout — describe the final moment as motion naturally slowing to stillness, a composed held stare, or a gradual deceleration instead.\nNEGATIVE PROMPT: Every video_prompt must end with "Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, altered bone structure, drifting features, morphing eyes, face deformation, character inconsistency, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features, glowing orbs, energy effects, supernatural light, sci-fi glow, lens flare orbs, light emanating from subject, magical effects"\nReturn ONLY valid JSON.`;
```

### Edit 2 — generateGrid9 (~line 2120)

Search for (exact — `${frames.length}` is a live template literal):
```javascript
  const systemPrompt=`You are a Kling 3.0 video prompt specialist. Given ${frames.length} frames in sequence, create a cohesive mini-movie that connects all frames narratively.\nCHARACTER CONSISTENCY: Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description. The subject's face must read as the same person in every frame. This is non-negotiable.\nNEGATIVE PROMPT: Every video_prompt must end with "Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, altered bone structure, drifting features, morphing eyes, face deformation, character inconsistency, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features"\nReturn ONLY valid JSON.`;
```

Replace with:
```javascript
  const systemPrompt=`You are a Kling 3.0 video prompt specialist. Given ${frames.length} frames in sequence, create a cohesive mini-movie that connects all frames narratively.\nCHARACTER CONSISTENCY: Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description. The subject's face must read as the same person in every frame. This is non-negotiable.\nATTIRE LOCK: Describe the subject's outfit exactly as visible in the provided reference image. Do NOT invent, substitute, or alter any clothing item. Every shot block must reference only garments actually shown in the image — exact colors, garment types, and layering as photographed.\nKLING MOTION: Do NOT use "freeze-frame", "static freeze", or "freeze" to describe an end state. Kling generates continuous motion throughout — describe the final moment as motion naturally slowing to stillness, a composed held stare, or a gradual deceleration instead.\nNEGATIVE PROMPT: Every video_prompt must end with "Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, altered bone structure, drifting features, morphing eyes, face deformation, character inconsistency, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features, glowing orbs, energy effects, supernatural light, sci-fi glow, lens flare orbs, light emanating from subject, magical effects"\nReturn ONLY valid JSON.`;
```

### Edit 3 — generateSequential (~line 2169)

Search for (exact — preserve both `${sceneNum}` and `${seqHistory.length>0?'Continue from the previous scene.':'Start the story.'}`):
```javascript
  const systemPrompt=`You are a Kling 3.0 video prompt specialist creating scene ${sceneNum} of a sequential story. ${seqHistory.length>0?'Continue from the previous scene.':'Start the story.'}\nCHARACTER CONSISTENCY: Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description. The subject's face must read as the same person in every frame. This is non-negotiable.\nNEGATIVE PROMPT: Every video_prompt must end with "Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, altered bone structure, drifting features, morphing eyes, face deformation, character inconsistency, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features"\nReturn ONLY valid JSON.`;
```

Replace with:
```javascript
  const systemPrompt=`You are a Kling 3.0 video prompt specialist creating scene ${sceneNum} of a sequential story. ${seqHistory.length>0?'Continue from the previous scene.':'Start the story.'}\nCHARACTER CONSISTENCY: Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description. The subject's face must read as the same person in every frame. This is non-negotiable.\nATTIRE LOCK: Describe the subject's outfit exactly as visible in the provided reference image. Do NOT invent, substitute, or alter any clothing item. Every shot block must reference only garments actually shown in the image — exact colors, garment types, and layering as photographed.\nKLING MOTION: Do NOT use "freeze-frame", "static freeze", or "freeze" to describe an end state. Kling generates continuous motion throughout — describe the final moment as motion naturally slowing to stillness, a composed held stare, or a gradual deceleration instead.\nNEGATIVE PROMPT: Every video_prompt must end with "Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, altered bone structure, drifting features, morphing eyes, face deformation, character inconsistency, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features, glowing orbs, energy effects, supernatural light, sci-fi glow, lens flare orbs, light emanating from subject, magical effects"\nReturn ONLY valid JSON.`;
```

- [ ] **Step 1: Apply all 3 edits above**

- [ ] **Step 2: Final verification**

```bash
grep -c "ATTIRE LOCK" "G:\My Drive\Apulu Prompt Generator\index.html"
```
Expected: **4**

```bash
grep -c "KLING MOTION" "G:\My Drive\Apulu Prompt Generator\index.html"
```
Expected: **4**

```bash
grep -c "magical effects" "G:\My Drive\Apulu Prompt Generator\index.html"
```
Expected: **4**

- [ ] **Step 3: Commit and push**

```bash
cd "G:\My Drive\Apulu Prompt Generator"
git add index.html
git commit -m "feat: add ATTIRE LOCK, KLING MOTION rules and expanded negatives to all inline Kling prompts"
git push origin main
```
