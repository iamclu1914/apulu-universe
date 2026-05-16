# Image to Video — "From Image" Kling Mode — Design Spec
**Date:** 2026-03-12
**Status:** Approved
**Scope:** `index.html` only — new Kling sub-mode

---

## Problem

When a user generates an image externally (Midjourney, NB2 on another site, etc.) and wants a Kling video of that exact scene, there is no path to do it. The existing Kling modes (Start/End, 9-Grid, Sequential) all interpret uploaded images as **video frames to connect**, not as **scenes to derive video prompts from**. The MV flow (Lyrics/Description) requires text input and generates its own scene context — it cannot read an existing image.

---

## Solution

Add a new Kling sub-mode `img2vid` — "From Image" — as a 5th button in the `ctrlKlingWf` tab bar. User uploads one generated image. Gemini reads the full scene (subject, attire, environment, lighting, mood, camera angle) and generates a complete Kling timestamped video prompt of that exact scene. Optional context textarea for motion direction.

---

## Tab Visibility Rules

**Video Only / Both output modes** (when `ctrlKlingWf` is shown): From Image, MV, Start+End, 9-Grid, Sequential — all 5 tabs visible.

**Image Only output mode**: From Image tab is NOT shown (ctrlKlingWf is already hidden in nb2 mode — no change needed).

---

## Changes

### 1. HTML — New panel `panelImg2Vid`

Add before `panelStartEnd` inside the `<div class="bottom-bar" id="bottomBar">`:

```html
<!-- Expandable: From Image -->
<div class="exp-panel" id="panelImg2Vid" style="max-width:860px;margin:0 auto;">
  <div class="exp-panel-title">From Image</div>
  <div class="exp-panel-hint">Upload a generated image. AI reads the full scene and writes a Kling video prompt that matches it.</div>
  <div class="frame-pair" style="justify-content:center;">
    <div class="frame-slot">
      <div class="frame-slot-lbl">Scene Image</div>
      <div class="frame-drop" id="img2vidZone" onclick="document.getElementById('img2vidFile').click()">
        <img id="img2vidPreview" src="" alt=""/>
        <span class="frame-drop-ph">+ Image</span>
        <div class="frame-drop-ov">
          <div class="frame-ov-btn" onclick="event.stopPropagation();document.getElementById('img2vidFile').click()">Change</div>
          <div class="frame-ov-btn del" onclick="event.stopPropagation();clearImg('img2vid')">Remove</div>
        </div>
      </div>
    </div>
  </div>
</div>
```

### 2. HTML — New hidden file input

Add alongside `#startFile`, `#endFile`, `#seqFile`:

```html
<input type="file" id="img2vidFile" accept="image/*" onchange="handleImg(event,'img2vid')"/>
```

### 3. HTML — New Kling tab button `kwImg2Vid`

Add as the first button in `#ctrlKlingWf` (before `kwMv`):

```html
<button class="ctrl-btn" id="kwImg2Vid" onclick="setKlingMode('img2vid')">From Image</button>
```

### 4. JS — New state variable

Add alongside `startFrameB64`, `endFrameB64`:

```javascript
let img2vidB64 = null;
```

### 5. JS — `handleImg` — add `img2vid` slot

```javascript
else if(slot==='img2vid'){img2vidB64=b64;document.getElementById('img2vidPreview').src=url;document.getElementById('img2vidZone').classList.add('filled');}
```

### 6. JS — `clearImg` — add `img2vid` slot

```javascript
else if(slot==='img2vid'){img2vidB64=null;document.getElementById('img2vidPreview').src='';document.getElementById('img2vidZone').classList.remove('filled');}
```

### 7. JS — `setKlingMode` — add `img2vid` to panelMap and active button lookup

**panelMap** (inside setKlingMode toggle logic):
```javascript
const panelMap={startend:'panelStartEnd',grid9:'panelGrid9',sequential:'panelSeq',img2vid:'panelImg2Vid'};
```

**forEach deactivate** — add `kwImg2Vid`:
```javascript
['kwMv','kwStartEnd','kwGrid9','kwSeq','kwImg2Vid'].forEach(id=>{
  document.getElementById(id).classList.remove('active-teal','active');
});
```

**Active button lookup** — add `img2vid` entry:
```javascript
document.getElementById({mv:'kwMv',startend:'kwStartEnd',grid9:'kwGrid9',sequential:'kwSeq',img2vid:'kwImg2Vid'}[mode]).classList.add('active-teal');
```

> **Implementation note:** There are 3 distinct edits inside `setKlingMode`. All 3 must be applied: panelMap, forEach array, and active-button lookup. The HTML tab button (Change 3) must also exist before `setKlingMode` runs, as `getElementById('kwImg2Vid')` will throw if the element is absent.

### 8. JS — `updatePanels` — show/hide `panelImg2Vid`

Add alongside the other panel toggles:
```javascript
document.getElementById('panelImg2Vid').classList.toggle('show', !isMV&&klingMode==='img2vid');
```

### 9. JS — `updateGenBtn` — add `img2vid` label

```javascript
const labels={startend:'Generate Motion',grid9:'Generate Mini Movie',sequential:seqHistory.length>0?'Continue →':'Generate Scene 1',img2vid:'Generate from Image'};
```

### 10. JS — `updateEmptyState` — add `img2vid` hint

```javascript
img2vid:'Upload a generated image above · Hit Generate from Image',
```

### 11. JS — `generate()` — route `img2vid`

Add alongside existing routes inside the `generate()` function (not `handleGenerate` — the live function is named `generate`):
```javascript
if(klingMode==='img2vid') return generateImg2Vid();
```

### 12. JS — `collapseAllPanels` — add `panelImg2Vid`

The live `collapseAllPanels` function collapses all Kling panels when the output mode switches. Add `'panelImg2Vid'` to its array:

```javascript
['panelStartEnd','panelGrid9','panelSeq','panelImg2Vid'].forEach(id=>{
  document.getElementById(id).classList.remove('show');
});
```

### 13. JS — `resetAll` — clear `img2vidB64`

Add to the state clear block:
```javascript
img2vidB64=null;
```

Add to the UI clear block:
```javascript
clearImg('img2vid');
```

### 14. JS — New function `generateImg2Vid`

```javascript
async function generateImg2Vid(){
  if(!img2vidB64){alert('Please upload a scene image.');return;}
  const context=document.getElementById('contextInput').value.trim();
  showLoading('Reading scene...');

  const systemPrompt=`You are a Kling 3.0 video prompt specialist. Given a single reference image, analyze the full scene — subject, attire, environment, lighting, mood, and camera framing — and generate a complete Kling 3.0 video prompt that produces a natural, realistic video clip of that exact scene.\nCHARACTER CONSISTENCY: Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description. The subject's face must read as the same person in every frame. This is non-negotiable.\nATTIRE LOCK: Describe the subject's outfit exactly as visible in the provided reference image. Do NOT invent, substitute, or alter any clothing item. Every shot block must reference only garments actually shown in the image — exact colors, garment types, and layering as photographed.\nPROP LOCK: Do NOT add any accessories, props, or objects not visible in the provided reference image. No headphones, earphones, sunglasses, hats, jewelry, or any item not photographed on the subject.\nMOTION DISCIPLINE: All movements are subtle and grounded. Use precise verbs with physical scale (e.g., "chin drops 2 cm", "left shoulder rises 1 cm"). Do NOT use adverbs like "energetically", "dramatically", "aggressively", "rapidly", or "intensely". Maximum 2 motion actions per shot block.\nSCENE LOCK: The background environment is completely static. No new objects enter frame. No objects disappear. Lighting is described only as physical fixtures (overhead fluorescent, window light from left, neon sign on wall) — never as animated effects, pulsing strobes, or changing intensity.\nCAMERA DISCIPLINE: Camera is locked-off or on an ultra-slow drift only. No orbit, spin, rapid pan, crash zoom, or handheld shake. Movements must be imperceptible — the viewer should feel stillness.\nKLING MOTION: Do NOT use "freeze-frame", "static freeze", or "freeze" to describe an end state. Kling generates continuous motion throughout — describe the final moment as motion naturally slowing to stillness, a composed held stare, or a gradual deceleration instead.\nSHOT FORMULA: Every timestamped block must follow this structure exactly: [CAMERA TYPE + DISTANCE], [SUBJECT POSITION + ANCHOR]. [MICRO-MOTION with scale]. [LIGHTING SOURCE as physical fixture]. Audio: [ambient sound].\nNEGATIVE PROMPT: Every video_prompt must end with "Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, altered bone structure, drifting features, morphing eyes, face deformation, character inconsistency, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features, glowing orbs, energy effects, supernatural light, sci-fi glow, lens flare orbs, light emanating from subject, magical effects, flickering background, shifting environment, morphing walls, background objects appearing, new objects entering frame, animated lighting, pulsing lights, strobe effects, fast motion, sudden movement, exaggerated gestures, camera spin, camera orbit, rapid pan, handheld shake, headphones, earphones, added accessories, spontaneous props, props not in reference"\nReturn ONLY valid JSON.`;

  const userPrompt=`Analyze this image and create a Kling 3.0 video prompt. Read the full scene — who is in it, what they're wearing, where they are, how it's lit, and what mood it carries. Generate a timestamped video prompt showing a natural 5-15 second clip of this exact scene.
${context?`Motion direction: ${context}`:''}

Return:
{
  "video_prompt": "Full timestamped Kling prompt...",
  "title": "Short descriptive title"
}`;

  try{
    const resp=await fetch('/api/messages',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({
        model:'gemini-3-flash-preview',
        max_tokens:2000,
        system:systemPrompt,
        messages:[{role:'user',content:[
          {type:'image',source:{type:'base64',media_type:'image/jpeg',data:img2vidB64}},
          {type:'text',text:userPrompt}
        ]}]
      })
    });
    if(!resp.ok){const e=await resp.json().catch(()=>({}));throw new Error(e.error||`API error: ${resp.status}`);}
    const data=await resp.json();
    const txt=data.content?.[0]?.text||'';
    const jsonMatch=txt.match(/\{[\s\S]*\}/);
    if(!jsonMatch)throw new Error('No JSON in response');
    const parsed=JSON.parse(repairJSON(jsonMatch[0]));
    allScenes=[{scene_number:1,title:parsed.title||'Scene',video_prompt:parsed.video_prompt,archetype:'IMG2VID'}];
    renderScenes('','From Image');
  }catch(err){
    console.error(err);
    showError(err.message);
  }
}
```

---

## Success Criteria

- "From Image" tab appears in Video Only and Both output modes, absent in Image Only
- Uploading an image to the panel and hitting "Generate from Image" calls `generateImg2Vid()`
- Missing image shows alert (no crash)
- Output renders as a single scene card with video_prompt + title
- All Kling quality rules applied (CHARACTER CONSISTENCY through full negative list)
- Reset clears `img2vidB64` and removes the preview image
- No change to any existing Kling mode behavior
- No UI changes outside the new panel, tab button, and file input
