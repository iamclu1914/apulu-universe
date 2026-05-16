# Kling Character Consistency Hardening Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a character consistency anchor rule and expanded negative prompt to all 4 Kling video generation system prompts to prevent face warping and morphing.

**Architecture:** 4 direct string replacements in `index.html` — no new functions, no UI changes, no new files. Each Kling system prompt gets a CHARACTER CONSISTENCY rule (mandating a per-shot lock phrase) and a full negative prompt list replacing the current minimal one.

**Tech Stack:** Plain HTML/JS — edit `index.html` directly. No build step.

---

## Chunk 1: All 4 System Prompt Changes

### Task 1: Update buildPromptSystem() Kling block

**Files:**
- Modify: `G:\My Drive\Apulu Prompt Generator\index.html` (~lines 1799–1805)

**Context:** The Kling guidelines block lives inside `${onlyOutput!=='nb2'?`...`:''}`. Do NOT disturb that conditional wrapper — only edit the text inside the backtick-quoted template literal.

- [ ] **Step 1: Locate the block**

Search for this exact text in `index.html`:
```
- End with Negative: smiling, laughing, cartoonish, morphing, blurry faces
```
Confirm it appears exactly once, inside the `KLING 3.0 VIDEO PROMPT GUIDELINES` block.

- [ ] **Step 2: Apply the replacement**

Search for:
```
${onlyOutput!=='nb2'?`KLING 3.0 VIDEO PROMPT GUIDELINES:
- 3-5 timestamped shot blocks, MAX 15 seconds total
- Format: [0:00-0:03] Environment first, then shot type, camera movement, micro-actions, audio layer
- 80-120 words total
- Include explicit end-state on final shot
- End with Negative: smiling, laughing, cartoonish, morphing, blurry faces
`:''}
```

Replace with:
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

- [ ] **Step 3: Verify**

```bash
grep -c "CHARACTER CONSISTENCY" "G:\My Drive\Apulu Prompt Generator\index.html"
```
Expected: 1

```bash
grep -c "face warping, face morphing" "G:\My Drive\Apulu Prompt Generator\index.html"
```
Expected: 1 (in buildPromptSystem; more will be added in Task 2)

- [ ] **Step 4: Commit**

```bash
cd "G:\My Drive\Apulu Prompt Generator"
git add index.html
git commit -m "feat: add character consistency rule and expanded negatives to buildPromptSystem Kling block"
```

---

### Task 2: Update generateStartEnd() system prompt

**Files:**
- Modify: `G:\My Drive\Apulu Prompt Generator\index.html` (~line 2070)

**Context:** `generateStartEnd` currently has a single-sentence system prompt. Replace the whole string — note there are no template literals in this string, so the replacement is straightforward.

- [ ] **Step 1: Apply the replacement**

Search for (exact):
```javascript
  const systemPrompt=`You are a Kling 3.0 video prompt specialist. Given a START frame and END frame, write a single video prompt that describes the motion connecting them. Return ONLY valid JSON.`;
```

Replace with:
```javascript
  const systemPrompt=`You are a Kling 3.0 video prompt specialist. Given a START frame and END frame, write a single video prompt that describes the motion connecting them.\nCHARACTER CONSISTENCY: Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description. The subject's face must read as the same person in every frame. This is non-negotiable.\nNEGATIVE PROMPT: Every video_prompt must end with "Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, altered bone structure, drifting features, morphing eyes, face deformation, character inconsistency, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features"\nReturn ONLY valid JSON.`;
```

- [ ] **Step 2: Verify**

```bash
grep -n "START frame and END frame" "G:\My Drive\Apulu Prompt Generator\index.html"
```
Expected: 1 hit, on the updated line that now contains `\nCHARACTER CONSISTENCY`.

- [ ] **Step 3: Commit**

```bash
cd "G:\My Drive\Apulu Prompt Generator"
git add index.html
git commit -m "feat: add character consistency rule and expanded negatives to generateStartEnd"
```

---

### Task 3: Update generateGrid9() system prompt

**Files:**
- Modify: `G:\My Drive\Apulu Prompt Generator\index.html` (~line 2119)

**Context:** `generateGrid9` system prompt contains `${frames.length}` — a live template literal. Preserve it exactly in the replacement.

- [ ] **Step 1: Apply the replacement**

Search for (exact):
```javascript
  const systemPrompt=`You are a Kling 3.0 video prompt specialist. Given ${frames.length} frames in sequence, create a cohesive mini-movie that connects all frames narratively. Return ONLY valid JSON.`;
```

Replace with:
```javascript
  const systemPrompt=`You are a Kling 3.0 video prompt specialist. Given ${frames.length} frames in sequence, create a cohesive mini-movie that connects all frames narratively.\nCHARACTER CONSISTENCY: Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description. The subject's face must read as the same person in every frame. This is non-negotiable.\nNEGATIVE PROMPT: Every video_prompt must end with "Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, altered bone structure, drifting features, morphing eyes, face deformation, character inconsistency, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features"\nReturn ONLY valid JSON.`;
```

- [ ] **Step 2: Verify**

```bash
grep -n "frames in sequence" "G:\My Drive\Apulu Prompt Generator\index.html"
```
Expected: 1 hit, on the updated line containing `\nCHARACTER CONSISTENCY`.

- [ ] **Step 3: Commit**

```bash
cd "G:\My Drive\Apulu Prompt Generator"
git add index.html
git commit -m "feat: add character consistency rule and expanded negatives to generateGrid9"
```

---

### Task 4: Update generateSequential() system prompt + push

**Files:**
- Modify: `G:\My Drive\Apulu Prompt Generator\index.html` (~line 2168)

**Context:** `generateSequential` system prompt contains TWO live template literals: `${sceneNum}` and `${seqHistory.length>0?'Continue from the previous scene.':'Start the story.'}`. Preserve both exactly.

- [ ] **Step 1: Apply the replacement**

Search for (exact):
```javascript
  const systemPrompt=`You are a Kling 3.0 video prompt specialist creating scene ${sceneNum} of a sequential story. ${seqHistory.length>0?'Continue from the previous scene.':'Start the story.'} Return ONLY valid JSON.`;
```

Replace with:
```javascript
  const systemPrompt=`You are a Kling 3.0 video prompt specialist creating scene ${sceneNum} of a sequential story. ${seqHistory.length>0?'Continue from the previous scene.':'Start the story.'}\nCHARACTER CONSISTENCY: Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description. The subject's face must read as the same person in every frame. This is non-negotiable.\nNEGATIVE PROMPT: Every video_prompt must end with "Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, altered bone structure, drifting features, morphing eyes, face deformation, character inconsistency, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features"\nReturn ONLY valid JSON.`;
```

- [ ] **Step 2: Final verification — all 4 locations updated**

```bash
grep -c "CHARACTER CONSISTENCY" "G:\My Drive\Apulu Prompt Generator\index.html"
```
Expected: **4**

```bash
grep -c "face warping, face morphing" "G:\My Drive\Apulu Prompt Generator\index.html"
```
Expected: **4**

```bash
grep -c "morphing, blurry faces" "G:\My Drive\Apulu Prompt Generator\index.html"
```
Expected: **0** (old negative list fully replaced everywhere)

- [ ] **Step 3: Commit and push**

```bash
cd "G:\My Drive\Apulu Prompt Generator"
git add index.html
git commit -m "feat: add character consistency rule and expanded negatives to generateSequential"
git push origin main
```
