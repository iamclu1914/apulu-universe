# Generate Image Button — Design Spec
**Date:** 2026-03-18
**Status:** Approved
**Scope:** `server.js` + `index.html` — add in-app image generation from NB2 JSON prompt

---

## Problem

After generating a structured JSON image prompt, users must manually copy it into Nano Banana 2 (NB2) to generate the image. This breaks the workflow — the app should be able to call NB2 directly and display the result in the scene card.

---

## Solution

Add a "Generate Image" button to every NB2 scene card. Clicking it serializes the `image_prompt` JSON object into a natural-language prompt, POSTs it to a new backend endpoint, which calls `gemini-3.1-flash-image-preview` (the NB2 model), and returns the image as base64. The image renders in the card with Download and Set as Reference actions.

---

## Architecture

### Backend — new endpoint in `server.js`

**Route:** `POST /api/generate-image`

**Request body:**
```json
{ "image_prompt": { ...NB2 JSON object... } }
```

**Prompt serialization logic** (server-side):
Converts the structured JSON into a natural-language string in this order:
```
[Subject joined] wearing [MadeOutOf joined]. [Arrangement]. [Lighting]. Camera: [Camera.type], [Camera.lens], [Camera.body]. [Background]. [Mood]. [OutputStyle]. Negative: [NegativePrompt joined with ", "].
```

**Gemini API call:**
- Model: `gemini-3.1-flash-image-preview` (NB2 = Gemini 3.1 Flash Image; verify exact model ID against Google AI Studio at implementation time — fall back to `gemini-2.0-flash-preview-image-generation` if needed)
- `responseModalities: ["IMAGE"]`
- Auth: existing `GEMINI_API_KEY` env var — no new credentials

**Response:**
```json
{ "image": "<base64 string>", "mimeType": "image/png" }
```

**Error handling:** Returns `{ "error": "..." }` with appropriate HTTP status on failure.

---

### Frontend — changes to `index.html`

#### 1. "Generate Image" button on NB2 scene cards

Added below the `<pre class="sc-prompt-text">` JSON block in `renderScenes`, only when `sc.image_prompt` exists:

```html
<button class="btn-gen-img" onclick="generateImage(this, 's${i}')">Generate Image</button>
<div class="gen-img-result" id="genImg_s${i}"></div>
```

#### 2. `generateImage(btn, sceneKey)` function

- Sets button to loading state ("Generating…", disabled)
- Parses scene index from sceneKey: `const idx = parseInt(sceneKey.slice(1))` → reads `allScenes[idx].image_prompt`
- POSTs to `/api/generate-image`
- On success: renders `<img>` + Download link + Set as Reference button inside `#genImg_<sceneKey>`
- On error: shows error message, re-enables button
- On complete: restores button label

#### 3. Download action

Creates a temporary `<a>` with `href="data:image/png;base64,..."` and `download="apulu-scene.png"`, clicks it programmatically.

#### 4. Set as Reference action

Takes the base64 string, sets `imgBase64 = base64`, updates `#imgPreview` src and adds `filled` class to `#imgZone` — identical to what `loadVawnReference()` does.

#### 5. CSS

New styles for `.btn-gen-img`, `.gen-img-result`, and `.gen-img-actions` (Download + Set as Reference buttons). Follows existing button class patterns.

---

## Data Flow

```
User clicks "Generate Image"
  → generateImage() parses index from sceneKey ('s0' → 0) → reads allScenes[idx].image_prompt
  → POST /api/generate-image { image_prompt: {...} }
  → server.js serializes JSON → prompt string
  → Gemini gemini-3.1-flash-image-preview called
  → returns inlineData base64 image
  → { image: "...", mimeType: "image/png" } sent to frontend
  → <img> rendered in scene card
  → Download button: saves as apulu-scene.png
  → Set as Reference: sets imgBase64, updates reference image UI
```

---

## Success Criteria

- "Generate Image" button appears on every NB2 scene card (image_prompt present)
- Clicking generates and displays the image in the card
- Download saves a valid PNG file
- Set as Reference updates the character reference image (same as manual upload)
- Loading state prevents double-clicks
- Errors display inline without crashing the card
- No change to Kling scene cards (video_prompt only)
- No new API keys required
