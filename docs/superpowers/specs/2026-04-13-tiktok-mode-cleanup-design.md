# TikTok Mode + Mode Cleanup Design

## Summary

Simplify the app from 11 modes to 3. Add a TikTok-optimized short-form mode with a "Generate Description" assist step. Remove all Kling modes, HF MV, HF Multishot, HF Start+End, HF 9-Grid, HF Sequential.

## Final Mode Architecture

### What stays
- **NB2** — image-only prompts (top-level platform)
- **Higgsfield Story Chain** — full stories, 4-12 shots, audio upload support
- **Higgsfield TikTok** (NEW) — short-form, 3-6 shots, generate-description assist

### What gets removed
- HF MV (multi-agent pipeline)
- HF Multishot (Smart Multishot Auto)
- HF Start+End
- HF 9-Grid
- HF Sequential
- All Kling modes (MV, Start+End, 9-Grid, Sequential)
- Kling as a platform option entirely

### UI Changes
- Platform selector: `NB2 | Higgsfield` (remove Kling)
- HF sub-mode tabs: `Story Chain | TikTok` (remove MV, Multishot, Start+End, 9-Grid, Seq)
- Remove all Kling-specific UI panels (panelStartEnd, panelGrid9, panelSeq, panelImg2Vid for Kling)
- Remove Kling mode selector buttons

## TikTok Mode Design

### Pipeline
Reuses the existing `runStoryChain` pipeline (single-agent, Claude Opus story director). No new backend pipeline needed — just different defaults passed from the frontend.

### Defaults
- Shot count: 3-6, default 4
- Duration bias: 5s for action, 10s for narrative (same as story chain)
- Default protagonist: @Vawn (male)

### UI: Two-Step Flow

#### Step 1: Generate Description
- User types a rough idea in the concept textarea (e.g., "studio late night, hears own song")
- Hits "Generate Description" button
- Frontend calls a new lightweight endpoint `/api/generate-description`
- AI expands the rough idea into a polished 1-2 sentence story concept optimized for Seedance 2.0
- Result populates the concept textarea — user can edit before proceeding

#### Step 2: Generate Story
- User hits "Generate Story" (same as story chain)
- Calls `/api/story-chain` with `sceneCount` from the shot selector (default 4)
- Renders the same story chain output cards

### Shot Count Selector
- Small selector/stepper: 3 | 4 | 5 | 6
- Default: 4 (highlighted)
- Positioned near the generate button

### Generate Description Endpoint

`POST /api/generate-description`

Request:
```json
{
  "idea": "studio late night, hears own song play back",
  "artistDescription": "optional"
}
```

Response:
```json
{
  "description": "We find @Vawn alone in a dim recording studio at 3am — utterly still, staring at the mixing board like it owes him something. Then his own verse floods the monitors and everything changes."
}
```

Uses Gemini Flash (cheap, fast) with a focused system prompt that:
- Always makes @Vawn the protagonist (male, he/him)
- Writes 1-2 sentences max
- Optimizes for visual storytelling (physics, environment, emotion)
- Includes a hook moment and an arc hint
- Does NOT write prompts — just the concept description

### Agent: Description Generator

New lightweight agent file: `agents/description-generator.js`

System prompt focus:
- You expand rough video ideas into polished 1-2 sentence story concepts for Higgsfield Cinema Studio
- Default protagonist is always @Vawn — male hip-hop artist
- Write for visual storytelling: ground the concept in a specific place, time, and physical moment
- Include a hook (what grabs attention) and an arc (what changes)
- Keep it under 2 sentences — this feeds into a story chain generator, not a screenplay

## Backend Changes

### server.js
- Add `POST /api/generate-description` endpoint
- Keep `/api/story-chain` as-is (already accepts sceneCount)
- Remove Kling-specific endpoints and prompt IDs if any exist
- Remove MV/Multishot-specific server-side prompt templates if separate from pipeline

### agents/pipeline.js
- Remove MODE_CONFIG entries: `mv`, `kling-9grid`, `kling-startend`, `hf-mv`, `hf-multishot`, `hf-9grid`, `hf-startend`
- Add MODE_CONFIG entry: `hf-tiktok` with `{ runVideoDirector: false, defaultN: 4, minN: 3, maxN: 6 }`
- Keep `nb2` and `hf-story` configs
- Remove `runPipeline` function (MV pipeline) — only `runStoryChain` remains for HF
- Keep all shared utilities (parseAgentResponse, callGeminiAgent, callClaudeAgent, etc.)

### Frontend (js/app.js + index.html)
- Remove all Kling mode logic, UI panels, and event handlers
- Remove HF MV, Multishot, Start+End, 9-Grid, Sequential mode logic
- Add TikTok mode: shot count selector + generate description button + generate story button
- TikTok mode reuses the story chain rendering (same output cards)
- Remove `videoPlatform` state for Kling — Higgsfield is the only video platform
- Remove `klingMode` state variable entirely

### CSS (css/styles.css)
- Remove Kling-specific styles
- Remove styles for removed panels/modes
- Add minimal styles for TikTok shot selector and generate-description button

## Files Modified
- `index.html` — remove Kling platform option, remove old HF mode tabs, add TikTok tab + UI
- `js/app.js` — remove Kling logic, remove old HF modes, add TikTok mode logic
- `css/styles.css` — remove dead styles, add TikTok styles
- `server.js` — add /api/generate-description endpoint, remove dead Kling endpoints
- `agents/pipeline.js` — remove old MODE_CONFIG entries, add hf-tiktok, remove runPipeline
- `agents/description-generator.js` — NEW: lightweight description expansion agent

## Files NOT Modified (keep as-is)
- `agents/higgsfield-story-director.js` — TikTok reuses this
- `agents/audio-analyzer.js` — story chain still supports audio
- `agents/treatment-director.js` — may be useful later, no harm keeping
- `agents/higgsfield-director.js` — keep for reference, no longer called
- `agents/higgsfield-multishot-director.js` — keep for reference, no longer called

## Files Safe to Delete (dead code after removal)
- `agents/video-director.js` — Kling video director (if exists)
- Any Kling-specific agent files
