# JSON Image Prompt Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace all NB2 `image_prompt` prose strings with structured JSON objects using NB2 Pro standard keys, folding `negative_prompt` into the JSON as `NegativePrompt`.

**Architecture:** 5 targeted edits to `index.html` — update output spec strings, replace NB2 guidelines opening, update all user prompt placeholders (3 locations), update renderScenes display to pretty-print JSON in a `<pre>` block, update copy logic to stringify the JSON object. No new files.

**Tech Stack:** Plain HTML/JS, no build step.

**Spec:** `docs/superpowers/specs/2026-03-18-json-image-prompt-design.md`

---

## Task 1: Output spec strings + NB2 guidelines opening

**Files:**
- Modify: `G:\My Drive\Apulu Prompt Generator\index.html` (~lines 1769–1778)

**Context:** `buildPromptSystem()` defines the output spec and the opening NB2 guideline. The output spec tells the AI what JSON shape to return. The opening guideline tells it HOW to write the image_prompt. Both need to change.

- [ ] **Step 1: Update output spec strings**

Find (~line 1769):
```javascript
  const outputSpec=onlyOutput==='nb2'
    ?`{ "image_prompt": "...", "negative_prompt": "..." }`
    :onlyOutput==='kling'
    ?`{ "video_prompt": "..." }`
    :`{ "image_prompt": "...", "video_prompt": "...", "negative_prompt": "..." }`;
```

Replace with:
```javascript
  const outputSpec=onlyOutput==='nb2'
    ?`{ "image_prompt": { "label": "...", "Subject": [...], "MadeOutOf": [...], "Arrangement": "...", "Lighting": "...", "Camera": {...}, "Background": "...", "Mood": "...", "OutputStyle": "...", "NegativePrompt": [...] } }`
    :onlyOutput==='kling'
    ?`{ "video_prompt": "..." }`
    :`{ "image_prompt": { "label": "...", "Subject": [...], "MadeOutOf": [...], "Arrangement": "...", "Lighting": "...", "Camera": {...}, "Background": "...", "Mood": "...", "OutputStyle": "...", "NegativePrompt": [...] }, "video_prompt": "..." }`;
```

- [ ] **Step 2: Replace NB2 guidelines opening line**

Find (~line 1778):
```
- Write in natural flowing prose as if briefing a human photographer — no labeled slots, no keyword lists
```

Replace with:
```
- Output image_prompt as a structured JSON object using NB2 Pro standard keys — NOT prose. This isolates each scene element to prevent concept bleeding. Use exactly these 10 keys for every image_prompt:
  "label": short descriptor combining style world + location (e.g. "WORLD 3 — FRENCH LUXURY STREETWEAR | rooftop terrace, golden hour")
  "Subject": array — character description matching the reference photo: skin tone, facial features, hair shape, expression, build. Never describe clothing here.
  "MadeOutOf": array — one item per garment/accessory: brand + fabric + colorway + fit. Include top, bottom, footwear (exact model + colorway from approved list), and any accessories. Apply all style world, color lock, and headwear rules here.
  "Arrangement": string — exact pose, named camera angle (use one of the 16 named angles), body position, framing. Apply all pose physics and social body language rules here.
  "Lighting": string — named lighting setup with physical light sources and color temperature. Apply all lighting realism rules here.
  "Camera": object — {"type": "shot type", "lens": "focal length + aperture", "body": "camera body model"}. Apply all camera body and lens selection rules here.
  "Background": string — location, environment, time of day, season, depth of field description. Apply all scene consistency and background blur rules here.
  "Mood": string — photographer reference woven with emotional tone (e.g. "carries Cam Kirk's warmth — rich amber shadows and intimate connection between subject and camera"). Apply photographer reference rules here.
  "OutputStyle": string — always include "cinematic photo, 4K ultra-HD" plus aspect ratio if relevant.
  "NegativePrompt": array — full list of negative terms (see below). This replaces the separate negative_prompt field.
```

- [ ] **Step 3: Verify**

```bash
grep -c "Output image_prompt as a structured JSON object" "G:\My Drive\Apulu Prompt Generator\index.html"
```
Expected: 1

- [ ] **Step 4: Commit**

```bash
cd "G:\My Drive\Apulu Prompt Generator"
git add index.html
git commit -m "feat: update output spec and NB2 guidelines opening for JSON image prompts"
```

---

## Task 2: Update user prompt placeholders (3 locations)

**Files:**
- Modify: `G:\My Drive\Apulu Prompt Generator\index.html` (~lines 1877, 1899, 1990)

**Context:** Three locations in the user prompts show the AI the expected JSON structure. All use `"image_prompt": "Full NB2 prompt..."` and have a separate `"negative_prompt": "..."` field in the scene object. Both need updating: image_prompt becomes a JSON object template, negative_prompt line is removed from the scene structure (it now lives inside image_prompt).

- [ ] **Step 1: Update Location 1 — lyrics/description user prompt (line ~1877)**

Find:
```javascript
      ${outputMode!=='kling'?'"image_prompt": "Full NB2 prompt...",':""}
```
And nearby:
```javascript
      "negative_prompt": "smiling, laughing, cartoonish..."
```

Replace the image_prompt line with:
```javascript
      ${outputMode!=='kling'?`"image_prompt": {"label":"WORLD N — STYLE | location","Subject":["character description"],"MadeOutOf":["top","bottom","footwear","accessories"],"Arrangement":"pose + named angle","Lighting":"named setup + sources","Camera":{"type":"shot type","lens":"focal length + aperture","body":"camera body"},"Background":"location + time + depth of field","Mood":"photographer reference + emotional tone","OutputStyle":"cinematic photo, 4K ultra-HD","NegativePrompt":["cartoonish","illustrated","soft focus","blurry artifacts","distorted hands","extra limbs","face warping","AI artifacts","anime style","warped clothing","morphed fabric","melting garments","distorted patterns","illegible text on clothing","fused fabric layers","unrealistic drape","plastic-looking material","impossible lighting","mismatched environments","floating subjects","distorted shoes","melted footwear","floating jewelry","tangled chains","cloned background figures","inconsistent shadows","inconsistent outfit","outfit change without story justification"]},`:""}
```

Remove the `"negative_prompt": "smiling, laughing, cartoonish..."` line from this scene object.

- [ ] **Step 2: Update Location 2 — description mode user prompt (line ~1899)**

Find:
```javascript
      ${outputMode!=='kling'?'"image_prompt": "Full NB2 prompt...",':""}
```
And nearby:
```javascript
      "negative_prompt": "smiling, laughing, cartoonish..."
```

Apply the same replacement as Step 1 (same template, same negative_prompt removal).

- [ ] **Step 3: Update Location 3 — 9-Grid user prompt (line ~1990)**

Find:
```javascript
      "image_prompt": "Full NB2 prompt — include where this scene picks up from the previous end state, and describe the end state this image leaves off on...",
```
And nearby:
```javascript
      "negative_prompt": "smiling, laughing, cartoonish..."
```

Replace image_prompt with:
```javascript
      "image_prompt": {"label":"WORLD N — STYLE | location","Subject":["character description"],"MadeOutOf":["top","bottom","footwear","accessories"],"Arrangement":"pose + named angle — include where this scene picks up from previous end state and describe end state for next scene","Lighting":"named setup + sources","Camera":{"type":"shot type","lens":"focal length + aperture","body":"camera body"},"Background":"location + time + depth of field","Mood":"photographer reference + emotional tone","OutputStyle":"cinematic photo, 4K ultra-HD","NegativePrompt":["cartoonish","illustrated","soft focus","blurry artifacts","distorted hands","extra limbs","face warping","AI artifacts","anime style","warped clothing","morphed fabric","melting garments","distorted patterns","illegible text on clothing","fused fabric layers","unrealistic drape","plastic-looking material","impossible lighting","mismatched environments","floating subjects","distorted shoes","melted footwear","floating jewelry","tangled chains","cloned background figures","inconsistent shadows","inconsistent outfit","outfit change without story justification"]},
```

Remove the `"negative_prompt": "smiling, laughing, cartoonish..."` line from this scene object.

- [ ] **Step 4: Verify — no more prose image_prompt placeholders**

```bash
grep -n '"image_prompt": "Full NB2 prompt' "G:\My Drive\Apulu Prompt Generator\index.html"
```
Expected: 0 results

```bash
grep -c "NegativePrompt" "G:\My Drive\Apulu Prompt Generator\index.html"
```
Expected: ≥3 (one per user prompt location)

- [ ] **Step 5: Commit**

```bash
cd "G:\My Drive\Apulu Prompt Generator"
git add index.html
git commit -m "feat: update all user prompt placeholders to JSON image_prompt object template"
```

---

## Task 3: Update renderScenes display + copy logic

**Files:**
- Modify: `G:\My Drive\Apulu Prompt Generator\index.html` (~lines 2341–2353, 2455)

**Context:** `sc.image_prompt` is now a JS object (parsed from JSON). The display currently uses `escHtml(sc.image_prompt)` inside a `<div>` — this must become `escHtml(JSON.stringify(sc.image_prompt, null, 2))` inside a `<pre>` for readable formatting. The copy logic stores `sc.image_prompt` directly — it must stringify it first. `copyAllImg` also references `s.image_prompt` raw.

- [ ] **Step 1: Update promptMap storage and display in renderScenes**

Find (~line 2341):
```javascript
    if(sc.image_prompt){
      const kImg=`s${i}_img`;promptMap[kImg]=sc.image_prompt;
      html+=`
        <div class="sc-prompt img-block">
          <div class="sc-prompt-header">
            <div class="sc-prompt-label">
              <div class="sc-prompt-dot"></div>
              <span class="sc-prompt-name">Image Prompt</span>
              <span class="sc-prompt-tool">· NB2</span>
            </div>
            <button class="btn-copy" onclick="copyPrompt(this,'${kImg}')">Copy</button>
          </div>
          <div class="sc-prompt-text">${escHtml(sc.image_prompt)}</div>
        </div>
      `;
    }
```

Replace with:
```javascript
    if(sc.image_prompt){
      const kImg=`s${i}_img`;
      const imgJson=typeof sc.image_prompt==='object'?JSON.stringify(sc.image_prompt,null,2):sc.image_prompt;
      promptMap[kImg]=imgJson;
      html+=`
        <div class="sc-prompt img-block">
          <div class="sc-prompt-header">
            <div class="sc-prompt-label">
              <div class="sc-prompt-dot"></div>
              <span class="sc-prompt-name">Image Prompt</span>
              <span class="sc-prompt-tool">· NB2</span>
            </div>
            <button class="btn-copy" onclick="copyPrompt(this,'${kImg}')">Copy</button>
          </div>
          <pre class="sc-prompt-text">${escHtml(imgJson)}</pre>
        </div>
      `;
    }
```

- [ ] **Step 2: Update copyAllImg**

Find (~line 2455):
```javascript
    {suffix:'',          text:s.image_prompt},
```

Replace with:
```javascript
    {suffix:'',          text:typeof s.image_prompt==='object'?JSON.stringify(s.image_prompt,null,2):s.image_prompt},
```

- [ ] **Step 3: Add CSS for pre block**

Find the existing `.sc-prompt-text` CSS rule and ensure it handles `<pre>` correctly. Search for:
```css
.sc-prompt-text
```

Add `white-space: pre-wrap; word-break: break-word;` if not already present, so long JSON lines wrap inside the block.

Find any existing `.sc-prompt-text` style and add/update:
```css
.sc-prompt-text{white-space:pre-wrap;word-break:break-word;}
```

- [ ] **Step 4: Verify counts**

```bash
grep -c "sc-prompt-text" "G:\My Drive\Apulu Prompt Generator\index.html"
```
Expected: ≥2 (CSS definition + at least one HTML usage)

```bash
grep -c "JSON.stringify" "G:\My Drive\Apulu Prompt Generator\index.html"
```
Expected: ≥2

- [ ] **Step 5: Commit and push**

```bash
cd "G:\My Drive\Apulu Prompt Generator"
git add index.html
git commit -m "feat: render image_prompt as formatted JSON in pre block, stringify for copy"
git push origin main
```
