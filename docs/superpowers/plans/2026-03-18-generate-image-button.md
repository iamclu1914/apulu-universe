# Generate Image Button Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "Generate Image" button to every NB2 scene card that calls the Gemini image generation API and displays the result inline with Download and Set as Reference actions.

**Architecture:** Two targeted edits — a new `POST /api/generate-image` endpoint in `server.js`, and three additions to `index.html`: CSS for the new UI elements, the `generateImage()` JS function, and a button + result container injected into each NB2 scene card by `renderScenes()`. No new files.

**Tech Stack:** Plain HTML/JS, Express/Node backend, Gemini image generation API (`gemini-3.1-flash-image-preview` or `gemini-2.0-flash-preview-image-generation` — verify at implementation time).

**Spec:** `docs/superpowers/specs/2026-03-18-generate-image-button-design.md`

---

## Task 1: Backend — `/api/generate-image` endpoint

**Files:**
- Modify: `G:\My Drive\Apulu Prompt Generator\server.js` (after line 66, before `const PORT`)

**Context:** `server.js` has one existing endpoint `POST /api/messages` that proxies text generation to Gemini. Add a second endpoint `POST /api/generate-image` that accepts the NB2 JSON `image_prompt` object, serializes it to a natural-language string, calls the Gemini image generation API, and returns `{ image, mimeType }`. The Gemini image generation API uses a different endpoint path and response shape than text generation — it returns `inlineData` (base64) in the response parts instead of text.

**Gemini image generation API details:**
- URL: `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent`
- Same URL pattern as text, but with image model name
- Body uses `responseModalities: ["IMAGE"]` inside `generationConfig`
- Response: `data.candidates[0].content.parts` — find the part where `part.inlineData` exists
- `part.inlineData.data` = base64 image string
- `part.inlineData.mimeType` = e.g. `"image/png"`

**Prompt serialization:** Convert the JSON object to a single natural-language string:
```
{Subject.join(', ')} wearing {MadeOutOf.join(', ')}. {Arrangement}. {Lighting}. Camera: {Camera.type}, {Camera.lens}, {Camera.body}. {Background}. {Mood}. {OutputStyle}. Negative: {NegativePrompt.join(', ')}.
```
Arrays are joined with `', '`. Camera is an object — access `.type`, `.lens`, `.body`. Guard against missing keys with `|| ''`.

- [ ] **Step 1: Add the `/api/generate-image` endpoint to `server.js`**

Find this line in `server.js`:
```javascript
const PORT = process.env.PORT || 3000;
```

Insert the following block IMMEDIATELY BEFORE it:

```javascript
app.post('/api/generate-image', async (req, res) => {
  try {
    const { image_prompt: ip } = req.body;
    if (!ip) return res.status(400).json({ error: 'image_prompt is required' });

    const subject    = Array.isArray(ip.Subject)       ? ip.Subject.join(', ')       : (ip.Subject || '');
    const madeOf     = Array.isArray(ip.MadeOutOf)     ? ip.MadeOutOf.join(', ')     : (ip.MadeOutOf || '');
    const negatives  = Array.isArray(ip.NegativePrompt)? ip.NegativePrompt.join(', '): (ip.NegativePrompt || '');
    const cam        = ip.Camera || {};

    const prompt = [
      subject && madeOf ? `${subject} wearing ${madeOf}.` : (subject || madeOf || ''),
      ip.Arrangement || '',
      ip.Lighting    || '',
      cam.type ? `Camera: ${cam.type}, ${cam.lens || ''}, ${cam.body || ''}.` : '',
      ip.Background  || '',
      ip.Mood        || '',
      ip.OutputStyle || '',
      negatives ? `Negative: ${negatives}.` : '',
    ].filter(Boolean).join(' ');

    const model = 'gemini-3.1-flash-image-preview';
    const apiKey = process.env.GEMINI_API_KEY;
    const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent`;

    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'x-goog-api-key': apiKey },
      body: JSON.stringify({
        contents: [{ role: 'user', parts: [{ text: prompt }] }],
        generationConfig: { responseModalities: ['IMAGE'] },
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      const errMsg = data.error?.message || JSON.stringify(data);
      console.error(`Image gen error ${response.status}:`, errMsg);
      return res.status(response.status).json({ error: `Gemini ${response.status}: ${errMsg}` });
    }

    const parts = data.candidates?.[0]?.content?.parts || [];
    const imgPart = parts.find(p => p.inlineData);
    if (!imgPart) return res.status(502).json({ error: 'No image returned from Gemini' });

    res.json({ image: imgPart.inlineData.data, mimeType: imgPart.inlineData.mimeType });

  } catch (err) {
    console.error('Image gen proxy error:', err);
    res.status(500).json({ error: 'Failed to generate image' });
  }
});

```

- [ ] **Step 2: Verify the endpoint is syntactically correct**

```bash
cd "G:\My Drive\Apulu Prompt Generator" && node -e "require('./server.js')" 2>&1 | head -5
```
Expected: server starts (prints "MV Prompt Generator running at...") with no syntax error. Press Ctrl+C after.

- [ ] **Step 3: Verify the model name**

Check Google AI Studio or the Gemini API docs. If `gemini-3.1-flash-image-preview` is not available, replace it with `gemini-2.0-flash-preview-image-generation` in the endpoint code above.

```bash
grep "gemini-3.1-flash-image-preview\|gemini-2.0-flash-preview-image-generation" "G:\My Drive\Apulu Prompt Generator\server.js"
```
Expected: 1 match with whichever model name is correct.

- [ ] **Step 4: Commit**

```bash
cd "G:\My Drive\Apulu Prompt Generator"
git add server.js
git commit -m "feat: add /api/generate-image endpoint for NB2 in-app image generation"
```

---

## Task 2: Frontend CSS — styles for Generate Image UI

**Files:**
- Modify: `G:\My Drive\Apulu Prompt Generator\index.html` (~line 434, after `.btn-copy.teal:hover`)

**Context:** The existing `.btn-copy` rule at line 416 defines the copy button style. New CSS for `.btn-gen-img`, `.gen-img-result`, and `.gen-img-actions` must follow the same design language: dark background, uppercase Raleway labels, gold accent on hover. The `.gen-img-result` container holds the rendered image. The `.gen-img-actions` row holds Download and Set as Reference buttons side by side.

- [ ] **Step 1: Add CSS after `.btn-copy.teal:hover`**

Find this exact line (~line 433):
```css
.btn-copy.teal:hover { border-color: rgba(24,168,138,0.4); color: var(--teal-text); background: var(--teal-dim); }
```

Add immediately after it:
```css
.btn-gen-img{padding:4px 12px;border:1px solid rgba(200,146,42,0.3);border-radius:3px;background:var(--gold-dim);color:var(--gold-text);font-family:'Raleway',sans-serif;font-size:7px;font-weight:700;letter-spacing:1.8px;text-transform:uppercase;cursor:pointer;transition:all 0.13s;margin-top:8px;display:block;}
.btn-gen-img:hover{opacity:0.75;}
.btn-gen-img:disabled{opacity:0.4;cursor:not-allowed;}
.gen-img-result{margin-top:10px;}
.gen-img-result img{width:100%;border-radius:4px;display:block;}
.gen-img-actions{display:flex;gap:8px;margin-top:8px;}
.btn-gen-action{padding:4px 12px;border:1px solid var(--border-hi);border-radius:3px;background:transparent;color:var(--text-dim);font-family:'Raleway',sans-serif;font-size:7px;font-weight:700;letter-spacing:1.8px;text-transform:uppercase;cursor:pointer;transition:all 0.13s;}
.btn-gen-action:hover{border-color:rgba(200,146,42,0.4);color:var(--gold-text);background:var(--gold-dim);}
```

- [ ] **Step 2: Verify CSS was added**

```bash
grep -c "btn-gen-img" "G:\My Drive\Apulu Prompt Generator\index.html"
```
Expected: 1 (CSS definition only — HTML usage is added in Task 4)

- [ ] **Step 3: Commit**

```bash
cd "G:\My Drive\Apulu Prompt Generator"
git add index.html
git commit -m "feat: add CSS for generate image button and result UI"
```

---

## Task 3: Frontend JS — `generateImage()` function

**Files:**
- Modify: `G:\My Drive\Apulu Prompt Generator\index.html` (add function near other generation functions)

**Context:** `allScenes` is a plain JS array populated by `renderScenes()`. The sceneKey passed to `generateImage()` is `'s0'`, `'s1'`, etc. — the index is parsed with `parseInt(sceneKey.slice(1))`. The `imgBase64`, `#imgPreview`, and `#imgZone` variables/elements are the existing character reference image system set by `loadVawnReference()`.

Find `loadVawnReference` to identify the right location — add `generateImage` immediately before `loadVawnReference`.

- [ ] **Step 1: Add `generateImage` function before `loadVawnReference`**

Find this line (near the bottom of the script section):
```javascript
async function loadVawnReference(){
```

Insert the following block IMMEDIATELY BEFORE it:

```javascript
async function generateImage(btn,sceneKey){
  const idx=parseInt(sceneKey.slice(1));
  const sc=allScenes[idx];
  if(!sc||!sc.image_prompt){alert('No image prompt for this scene.');return;}
  btn.textContent='Generating…';
  btn.disabled=true;
  const resultEl=document.getElementById(`genImg_${sceneKey}`);
  resultEl.innerHTML='';
  try{
    const resp=await fetch('/api/generate-image',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({image_prompt:sc.image_prompt}),
    });
    const data=await resp.json();
    if(!resp.ok||data.error)throw new Error(data.error||`Error ${resp.status}`);
    const src=`data:${data.mimeType};base64,${data.image}`;
    resultEl.innerHTML=`
      <img src="${src}" alt="Generated scene"/>
      <div class="gen-img-actions">
        <button class="btn-gen-action" onclick="downloadGenImg('${sceneKey}')">Download</button>
        <button class="btn-gen-action" onclick="setGenImgAsRef('${sceneKey}')">Set as Reference</button>
      </div>
    `;
    resultEl.dataset.b64=data.image;
    resultEl.dataset.mime=data.mimeType;
  }catch(err){
    resultEl.innerHTML=`<div style="color:rgba(224,100,88,0.8);font-size:11px;margin-top:6px;">${escHtml(err.message)}</div>`;
  }finally{
    btn.textContent='Generate Image';
    btn.disabled=false;
  }
}

function downloadGenImg(sceneKey){
  const el=document.getElementById(`genImg_${sceneKey}`);
  const b64=el?.dataset.b64;
  const mime=el?.dataset.mime||'image/png';
  if(!b64)return;
  const a=document.createElement('a');
  a.href=`data:${mime};base64,${b64}`;
  a.download='apulu-scene.png';
  a.click();
}

function setGenImgAsRef(sceneKey){
  const el=document.getElementById(`genImg_${sceneKey}`);
  const b64=el?.dataset.b64;
  const mime=el?.dataset.mime||'image/png';
  if(!b64)return;
  imgBase64=b64;
  const url=`data:${mime};base64,${b64}`;
  document.getElementById('imgPreview').src=url;
  document.getElementById('imgZone').classList.add('filled');
}

```

- [ ] **Step 2: Verify function was added**

```bash
grep -c "generateImage" "G:\My Drive\Apulu Prompt Generator\index.html"
```
Expected: ≥2 (function declaration + call in renderScenes added in Task 4)

- [ ] **Step 3: Commit**

```bash
cd "G:\My Drive\Apulu Prompt Generator"
git add index.html
git commit -m "feat: add generateImage, downloadGenImg, setGenImgAsRef JS functions"
```

---

## Task 4: Frontend HTML — button + result container in `renderScenes`

**Files:**
- Modify: `G:\My Drive\Apulu Prompt Generator\index.html` (~line 2363, inside the `if(sc.image_prompt)` block)

**Context:** The `if(sc.image_prompt)` block in `renderScenes` currently ends with:
```javascript
          <pre class="sc-prompt-text">${escHtml(imgJson)}</pre>
        </div>
      `;
    }
```
The "Generate Image" button and result `<div>` go inside the `.sc-prompt img-block` div, after the `<pre>` and before the closing `</div>`.

- [ ] **Step 1: Add the button and result container inside the image prompt block**

Find this exact block (~line 2362):
```javascript
          <pre class="sc-prompt-text">${escHtml(imgJson)}</pre>
        </div>
      `;
    }
```

Replace with:
```javascript
          <pre class="sc-prompt-text">${escHtml(imgJson)}</pre>
          <button class="btn-gen-img" onclick="generateImage(this,'s${i}')">Generate Image</button>
          <div class="gen-img-result" id="genImg_s${i}"></div>
        </div>
      `;
    }
```

- [ ] **Step 2: Verify the button appears in the HTML template**

```bash
grep -c "btn-gen-img" "G:\My Drive\Apulu Prompt Generator\index.html"
```
Expected: ≥2 (CSS + HTML)

```bash
grep -c "genImg_s" "G:\My Drive\Apulu Prompt Generator\index.html"
```
Expected: ≥2 (HTML template + JS function)

- [ ] **Step 3: Commit and push**

```bash
cd "G:\My Drive\Apulu Prompt Generator"
git add index.html
git commit -m "feat: inject Generate Image button and result container into NB2 scene cards"
git push origin main
```
