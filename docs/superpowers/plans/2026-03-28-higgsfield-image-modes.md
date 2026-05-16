# Higgsfield Image Modes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Start+End, 9-Grid, and Sequential image-upload modes to Higgsfield — mirroring the existing Kling workflow buttons — generating Higgsfield-formatted prompts (full_prompt + camera + genre + duration + emotions + start_frame + end_frame) instead of Kling timestamped shots.

**Architecture:** All changes are in `index.html`. Three new `generate*` functions call `/api/messages` directly with Higgsfield-specific system prompts, same as Kling's equivalents do. The shared `panelStartEnd`, `panelGrid9`, `panelSeq` panels are reused as-is. `updatePanels()` and `updateInputArea()` gain Higgsfield awareness. No server.js changes needed.

**Tech Stack:** Vanilla JS, existing `/api/messages` Gemini proxy, Higgsfield scene schema (`video_prompt` string + `hf_camera_movement`, `hf_genre`, `hf_duration`, `hf_emotions`, `hf_start_frame`, `hf_end_frame` flat fields)

---

## File Map

- Modify: `index.html` — all changes below are in this single file

---

## Key Data Model

Higgsfield scenes in `allScenes` use this flat shape (see `renderShots()` at line ~3075):
```js
{
  scene_number: 1,
  title: 'Title',
  video_prompt: 'full_prompt string here',   // NOT an object
  hf_camera_movement: 'Orbital',
  hf_genre: 'dark',
  hf_duration: '5s',
  hf_emotions: '@serene 80%',
  hf_start_frame: 'subject standing...',
  hf_end_frame: 'subject walking away...',
  archetype: 'HF_STARTEND'                   // or 'HF_GRID9', 'HF_SEQUENTIAL'
}
```
`renderScenes()` at line 2906 detects Higgsfield via `!!sc.hf_camera_movement` (lines 2937/3024). The `video_prompt` field is a plain string (the `full_prompt`).

---

## Task 1: Add 3 new buttons to ctrlHfWf

**Files:**
- Modify: `index.html:1538-1541`

Current:
```html
<div class="ctrl-group" id="ctrlHfWf" style="display:none;">
  <button class="ctrl-btn active-hf" id="hwMv"    onclick="setHfMode('mv')">MV</button>
  <button class="ctrl-btn"           id="hwStory" onclick="setHfMode('story')">Story Chain</button>
</div>
```

- [ ] **Step 1: Replace the ctrlHfWf div content**

Replace with:
```html
<div class="ctrl-group" id="ctrlHfWf" style="display:none;">
  <button class="ctrl-btn active-hf" id="hwMv"       onclick="setHfMode('mv')">MV</button>
  <button class="ctrl-btn"           id="hwStory"    onclick="setHfMode('story')">Story Chain</button>
  <button class="ctrl-btn"           id="hwStartEnd" onclick="setHfMode('startend')">Start+End</button>
  <button class="ctrl-btn"           id="hwGrid9"    onclick="setHfMode('grid9')">9-Grid</button>
  <button class="ctrl-btn"           id="hwSeq"      onclick="setHfMode('seq')">Sequential</button>
</div>
```

- [ ] **Step 2: Verify in browser** — Higgsfield platform selected → 5 buttons visible. No new functionality yet.

---

## Task 2: Add state variable for hf sequential history

**Files:**
- Modify: `index.html:1583` (where `let hfMode = 'mv';` is declared)

- [ ] **Step 1: Add new variable after `hfMode`**

Find:
```js
let hfMode              = 'mv';         // 'mv' | 'story'
```

Replace with:
```js
let hfMode              = 'mv';         // 'mv' | 'story' | 'startend' | 'grid9' | 'seq'
let hfSeqHistory        = [];           // Higgsfield sequential scene accumulator
```

Note: `hfSeqHistory` is separate from Kling's `seqHistory`. Both modes reuse the same seq panel DOM (seqZone, seqStrip, seqCurrentB64) — this is fine because platforms are mutually exclusive.

---

## Task 3: Rewrite setHfMode()

**Files:**
- Modify: `index.html:1854-1866`

Current `setHfMode()`:
```js
function setHfMode(mode){
  hfMode=mode;
  document.getElementById('hwMv').className=mode==='mv'?'ctrl-btn active-hf':'ctrl-btn';
  document.getElementById('hwStory').className=mode==='story'?'ctrl-btn active-hf':'ctrl-btn';
  document.getElementById('hfAudioUpload').style.display=mode==='story'?'':'none';
  // Story mode: audio is the primary input — video style selector is redundant
  document.getElementById('videoStyleSelect').style.display=mode==='story'?'none':'';
  const lyricsEl=document.getElementById('lyricsInput');
  lyricsEl.placeholder=mode==='story'
    ?'Optional: story direction, mood, or concept — the audio track guides the generation...'
    :'Paste lyrics or describe your track — AI maps the emotional arc to camera moves, start/end frames & Higgsfield video prompts...';
  updateGenBtn();
}
```

- [ ] **Step 1: Replace setHfMode() with the version below**

```js
function setHfMode(mode){
  hfMode=mode;
  const isImageMode=['startend','grid9','seq'].includes(mode);
  // Button active states
  ['hwMv','hwStory','hwStartEnd','hwGrid9','hwSeq'].forEach(id=>{
    const el=document.getElementById(id);
    if(el) el.className='ctrl-btn';
  });
  const activeId={mv:'hwMv',story:'hwStory',startend:'hwStartEnd',grid9:'hwGrid9',seq:'hwSeq'}[mode];
  if(activeId) document.getElementById(activeId).className='ctrl-btn active-hf';

  // Audio upload: story only
  document.getElementById('hfAudioUpload').style.display=mode==='story'?'':'none';
  // Style selector: hide in story and image modes (no lyrics needed)
  document.getElementById('videoStyleSelect').style.display=isImageMode||mode==='story'?'none':'';

  // Placeholder for lyrics/context
  const lyricsEl=document.getElementById('lyricsInput');
  lyricsEl.placeholder=mode==='story'
    ?'Optional: story direction, mood, or concept — the audio track guides the generation...'
    :'Paste lyrics or describe your track — AI maps the emotional arc to camera moves, start/end frames & Higgsfield video prompts...';

  updatePanels();
  updateInputArea();
  updateGenBtn();
  updateEmptyState();
}
```

- [ ] **Step 2: Verify** — clicking each HF button highlights it correctly; Start+End/9-Grid/Seq do not show panels yet (that's Task 4).

---

## Task 4: Update updatePanels() for Higgsfield modes

**Files:**
- Modify: `index.html:1919-1930`

Current:
```js
function updatePanels(){
  const isMV=outputMode==='nb2'||klingMode==='mv';
  document.getElementById('panelStartEnd').classList.toggle('show', !isMV&&klingMode==='startend');
  document.getElementById('panelGrid9').classList.toggle('show', !isMV&&klingMode==='grid9');
  document.getElementById('panelSeq').classList.toggle('show', !isMV&&klingMode==='sequential');
  document.getElementById('panelImg2Vid').classList.toggle('show', !isMV&&klingMode==='img2vid');
  const showPhoto=(outputMode!=='kling')||(klingMode==='mv');
  document.getElementById('imgZone').style.display=showPhoto?'flex':'none';
  const anyPanel=!isMV&&(klingMode!=='mv');
  document.getElementById('composerPill').style.borderRadius=anyPanel?'0 0 18px 18px':'18px';
  document.getElementById('composerPill').style.borderTop=anyPanel?'1px solid var(--border)':'';
}
```

- [ ] **Step 1: Replace updatePanels() with Higgsfield-aware version**

```js
function updatePanels(){
  const isHf=videoPlatform==='higgsfield';
  const hfImageMode=isHf&&['startend','grid9','seq'].includes(hfMode);
  const isMV=outputMode==='nb2'||klingMode==='mv'||(isHf&&!hfImageMode);

  if(isHf){
    document.getElementById('panelStartEnd').classList.toggle('show', hfMode==='startend');
    document.getElementById('panelGrid9').classList.toggle('show', hfMode==='grid9');
    document.getElementById('panelSeq').classList.toggle('show', hfMode==='seq');
    document.getElementById('panelImg2Vid').classList.remove('show');
  } else {
    document.getElementById('panelStartEnd').classList.toggle('show', !isMV&&klingMode==='startend');
    document.getElementById('panelGrid9').classList.toggle('show', !isMV&&klingMode==='grid9');
    document.getElementById('panelSeq').classList.toggle('show', !isMV&&klingMode==='sequential');
    document.getElementById('panelImg2Vid').classList.toggle('show', !isMV&&klingMode==='img2vid');
  }

  const showPhoto=isHf?!hfImageMode:(outputMode!=='kling'||klingMode==='mv');
  document.getElementById('imgZone').style.display=showPhoto?'flex':'none';

  const anyPanel=hfImageMode||(!isHf&&!isMV&&klingMode!=='mv');
  document.getElementById('composerPill').style.borderRadius=anyPanel?'0 0 18px 18px':'18px';
  document.getElementById('composerPill').style.borderTop=anyPanel?'1px solid var(--border)':'';
}
```

- [ ] **Step 2: Verify** — switching to HF Start+End shows the `panelStartEnd` div with frame slots. Switching back to HF MV hides it. Kling modes still work.

---

## Task 5: Update updateInputArea() for Higgsfield image modes

**Files:**
- Modify: `index.html:1932-1940`

Current:
```js
function updateInputArea(){
  const isMV=outputMode==='nb2'||klingMode==='mv';
  document.getElementById('ctrlInputMode').style.display=isMV?'flex':'none';
  document.getElementById('lyricsInput').style.display=isMV&&currentMode==='lyrics'?'block':'none';
  document.getElementById('descInput').style.display=isMV&&currentMode==='desc'?'block':'none';
  document.getElementById('framesInput').style.display=outputMode==='nb2'&&currentMode==='frames'?'block':'none';
  document.getElementById('gridStoryInput').style.display=outputMode==='nb2'&&currentMode==='grid'?'block':'none';
  document.getElementById('contextInput').style.display=!isMV?'block':'none';
}
```

- [ ] **Step 1: Replace updateInputArea() with Higgsfield-aware version**

```js
function updateInputArea(){
  const isHf=videoPlatform==='higgsfield';
  const hfImageMode=isHf&&['startend','grid9','seq'].includes(hfMode);
  const isMV=outputMode==='nb2'||klingMode==='mv'||(isHf&&!hfImageMode);
  document.getElementById('ctrlInputMode').style.display=(isMV&&!hfImageMode)?'flex':'none';
  document.getElementById('lyricsInput').style.display=isMV&&currentMode==='lyrics'?'block':'none';
  document.getElementById('descInput').style.display=isMV&&currentMode==='desc'?'block':'none';
  document.getElementById('framesInput').style.display=outputMode==='nb2'&&currentMode==='frames'?'block':'none';
  document.getElementById('gridStoryInput').style.display=outputMode==='nb2'&&currentMode==='grid'?'block':'none';
  document.getElementById('contextInput').style.display=(!isMV||hfImageMode)?'block':'none';
}
```

---

## Task 6: Update updateGenBtn() and updateEmptyState()

**Files:**
- Modify: `index.html:1942-1953` (updateGenBtn)
- Modify: `index.html:1960-~1980` (updateEmptyState)

Current updateGenBtn():
```js
function updateGenBtn(){
  const btn=document.getElementById('genBtn');
  // Higgsfield story chain gets its own label
  if(videoPlatform==='higgsfield' && hfMode==='story'){
    btn.textContent='Generate Story';btn.className='gen-btn';return;
  }
  const isMV=outputMode==='nb2'||klingMode==='mv'||videoPlatform==='higgsfield';
  if(isMV){btn.textContent='Generate';btn.className='gen-btn';return;}
  const labels={startend:'Generate Motion',grid9:'Generate Mini Movie',sequential:seqHistory.length>0?'Continue →':'Generate Scene 1',img2vid:'Generate from Image'};
  btn.textContent=labels[klingMode]||'Generate';
  btn.className='gen-btn teal';
}
```

- [ ] **Step 1: Replace updateGenBtn() to handle new HF modes**

```js
function updateGenBtn(){
  const btn=document.getElementById('genBtn');
  if(videoPlatform==='higgsfield' && hfMode==='story'){
    btn.textContent='Generate Story';btn.className='gen-btn';return;
  }
  if(videoPlatform==='higgsfield' && hfMode==='startend'){
    btn.textContent='Generate Motion';btn.className='gen-btn teal';return;
  }
  if(videoPlatform==='higgsfield' && hfMode==='grid9'){
    btn.textContent='Generate Mini Movie';btn.className='gen-btn teal';return;
  }
  if(videoPlatform==='higgsfield' && hfMode==='seq'){
    btn.textContent=hfSeqHistory.length>0?'Continue →':'Generate Scene 1';
    btn.className='gen-btn teal';return;
  }
  const isMV=outputMode==='nb2'||klingMode==='mv'||videoPlatform==='higgsfield';
  if(isMV){btn.textContent='Generate';btn.className='gen-btn';return;}
  const labels={startend:'Generate Motion',grid9:'Generate Mini Movie',sequential:seqHistory.length>0?'Continue →':'Generate Scene 1',img2vid:'Generate from Image'};
  btn.textContent=labels[klingMode]||'Generate';
  btn.className='gen-btn teal';
}
```

- [ ] **Step 2: Update updateEmptyState() to add HF image mode hints**

File: `index.html:1960-1975`. The full current function:
```js
function updateEmptyState(){
  const isMV=outputMode==='nb2'||klingMode==='mv';
  const hints={
    mv:'Upload a photo · Paste lyrics · Hit Generate',
    startend:'Upload a Start Frame + End Frame above · Hit Generate Motion',
    grid9:'Load 2-9 frames in the grid · Hit Generate Mini Movie',
    sequential:'Upload Frame 1 in the panel above · Hit Generate Scene 1',
    img2vid:'Upload a generated image above · Hit Generate from Image',
    frames:'Upload a photo · Describe the scene & motion · Hit Generate',
    grid:'Upload a photo · Describe your 9-grid story arc · Hit Generate',
  };
  const hint=isMV
    ?(currentMode==='frames'?hints.frames:currentMode==='grid'?hints.grid:hints.mv)
    :(hints[klingMode]||hints.mv);
  document.getElementById('emptyTxt').textContent=hint;
}
```

Replace with:
```js
function updateEmptyState(){
  const isHf=videoPlatform==='higgsfield';
  const isMV=outputMode==='nb2'||klingMode==='mv'||(isHf&&!['startend','grid9','seq'].includes(hfMode));
  const hints={
    mv:'Upload a photo · Paste lyrics · Hit Generate',
    startend:'Upload a Start Frame + End Frame above · Hit Generate Motion',
    grid9:'Load 2-9 frames in the grid · Hit Generate Mini Movie',
    sequential:'Upload Frame 1 in the panel above · Hit Generate Scene 1',
    img2vid:'Upload a generated image above · Hit Generate from Image',
    frames:'Upload a photo · Describe the scene & motion · Hit Generate',
    grid:'Upload a photo · Describe your 9-grid story arc · Hit Generate',
    hf_startend:'Upload start + end frames · Hit Generate Motion',
    hf_grid9:'Upload 2–9 frames · Hit Generate Mini Movie',
    hf_seq:'Upload a frame · Hit Generate Scene 1',
  };
  const hfKey=isHf?`hf_${hfMode}`:null;
  const hint=isMV
    ?(currentMode==='frames'?hints.frames:currentMode==='grid'?hints.grid:hints.mv)
    :((hfKey&&hints[hfKey])||hints[klingMode]||hints.mv);
  document.getElementById('emptyTxt').textContent=hint;
}
```

---

## Task 7: Update generate() dispatcher

**Files:**
- Modify: `index.html:2007-2018`

Current:
```js
async function generate(){
  saveToHistory();
  if(videoPlatform==='higgsfield' && hfMode==='story') return generateStory();
  if(currentMode==='frames') return generateFramePair();
  if(currentMode==='grid') return generateGridStory();
  if(outputMode==='nb2'||klingMode==='mv') return generateMV();
  if(klingMode==='startend') return generateStartEnd();
  if(klingMode==='grid9') return generateGrid9();
  if(klingMode==='sequential') return generateSequential();
  if(klingMode==='img2vid') return generateImg2Vid();
}
```

- [ ] **Step 1: Add HF image mode dispatch before the Kling checks**

```js
async function generate(){
  saveToHistory();
  if(videoPlatform==='higgsfield' && hfMode==='story') return generateStory();
  if(videoPlatform==='higgsfield' && hfMode==='startend') return generateHfStartEnd();
  if(videoPlatform==='higgsfield' && hfMode==='grid9') return generateHfGrid9();
  if(videoPlatform==='higgsfield' && hfMode==='seq') return generateHfSequential();
  if(currentMode==='frames') return generateFramePair();
  if(currentMode==='grid') return generateGridStory();
  if(outputMode==='nb2'||klingMode==='mv') return generateMV();
  if(klingMode==='startend') return generateStartEnd();
  if(klingMode==='grid9') return generateGrid9();
  if(klingMode==='sequential') return generateSequential();
  if(klingMode==='img2vid') return generateImg2Vid();
}
```

---

## Task 8: Add generateHfStartEnd()

**Files:**
- Modify: `index.html` — insert after the `generateStartEnd()` function (after line ~2662)

- [ ] **Step 1: Add generateHfStartEnd() function**

Insert after the closing `}` of `generateStartEnd()`:

```js
// GENERATE HF START+END
async function generateHfStartEnd(){
  if(!startFrameB64||!endFrameB64){alert('Please upload both start and end frames.');return;}
  const context=document.getElementById('contextInput').value.trim();
  showLoading('Analyzing motion path...');

  const systemPrompt=`You are a Higgsfield Cinema Studio video prompt specialist. Given a START frame and END frame, write a single Higgsfield video prompt describing the motion that connects them.

CHARACTER LOCK: Describe the subject exactly as visible in the frames. Copy this description verbatim into full_prompt. Never paraphrase or invent details.
CAMERA: Name a specific Higgsfield-compatible camera move (Orbital, Dolly In, Dolly Out, Handheld Push, FPV, Crane Up, Crane Down, Whip Pan, Static). Never use generic words like "moves" or "goes".
GENRE: One of: epic, intimate, dark, cinematic, documentary, ethereal, gritty, surreal.
EMOTIONS: Format as "@emotion XX%" — choose the dominant emotion (e.g. @serene 80%, @tense 70%).
START_FRAME / END_FRAME: Precise, literal descriptions of the opening and closing compositions — match what is actually shown in the uploaded images.
NEGATIVE PROMPT: full_prompt must end with "Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features, added accessories, props not in reference, deformed hands, incorrect finger count, asymmetrical facial features, unnatural joint angles, body warping, extra limbs, motion blur, temporal flickering, floating objects"

Return ONLY valid JSON:
{
  "title": "Short descriptive title",
  "video_prompt": {
    "full_prompt": "Camera move. Subject + action. Environment. Lighting. Mood. Negative: ...",
    "camera": "Named camera move",
    "genre": "cinematic style",
    "duration": "5s",
    "emotions": "@emotion XX%",
    "start_frame": "Exact opening composition matching the uploaded start frame",
    "end_frame": "Exact closing composition matching the uploaded end frame"
  }
}`;

  const userPrompt=`Create a Higgsfield video prompt that smoothly transitions from the START frame to the END frame.
${context?`Context: ${context}`:''}

Return valid JSON only.`;

  try{
    const resp=await fetch(API_BASE+'/api/messages',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({
        model:'gemini-3-flash-preview',
        max_tokens:1500,
        system:systemPrompt,
        messages:[{role:'user',content:[
          {type:'text',text:'START FRAME:'},
          {type:'image',source:{type:'base64',media_type:'image/jpeg',data:startFrameB64}},
          {type:'text',text:'END FRAME:'},
          {type:'image',source:{type:'base64',media_type:'image/jpeg',data:endFrameB64}},
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
    const vp=parsed.video_prompt||{};
    allScenes=[{
      scene_number:1,
      title:parsed.title||'Motion Transition',
      video_prompt:vp.full_prompt||'',
      hf_camera_movement:vp.camera||'',
      hf_genre:vp.genre||'',
      hf_duration:vp.duration||'5s',
      hf_emotions:vp.emotions||'',
      hf_start_frame:vp.start_frame||'',
      hf_end_frame:vp.end_frame||'',
      archetype:'HF_STARTEND'
    }];
    renderScenes('');
  }catch(err){
    console.error(err);
    showError(err.message);
  }
}
```

- [ ] **Step 2: Manual test** — Switch to Higgsfield → Start+End → upload two images → Generate Motion → verify scene card shows Higgsfield badge, camera, start/end frame metadata.

---

## Task 9: Add generateHfGrid9()

**Files:**
- Modify: `index.html` — insert after the closing `}` of `generateGrid9()` (around line ~2712)

- [ ] **Step 1: Add generateHfGrid9() function**

```js
// GENERATE HF 9-GRID
async function generateHfGrid9(){
  const frames=gridImages.filter(Boolean);
  if(frames.length<2){alert('Please upload at least 2 frames.');return;}
  const context=document.getElementById('contextInput').value.trim();
  showLoading('Building Higgsfield mini-movie...');

  const systemPrompt=`You are a Higgsfield Cinema Studio video prompt specialist. Given ${frames.length} reference frames in order, create a connected cinematic sequence where each frame becomes one video clip.

CONTINUITY: Each scene's start_frame must describe the same state as the previous scene's end_frame. Lock character description, lighting, and wardrobe across all scenes.
CHARACTER LOCK: Describe the subject exactly as visible in the frames. Copy the description verbatim into every full_prompt.
CAMERA: Use a different named Higgsfield-compatible camera move per scene (Orbital, Dolly In, Dolly Out, Handheld Push, FPV, Crane Up, Crane Down, Whip Pan, Static).
NEGATIVE PROMPT: Every full_prompt must end with "Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features, added accessories, props not in reference, deformed hands, incorrect finger count, asymmetrical facial features, unnatural joint angles, body warping, extra limbs, motion blur, temporal flickering, floating objects"

Return ONLY valid JSON:
{
  "title": "Project title",
  "scenes": [
    {
      "scene_number": 1,
      "title": "Scene title",
      "video_prompt": {
        "full_prompt": "Camera move. Subject + action. Environment. Lighting. Mood. Negative: ...",
        "camera": "Named camera move",
        "genre": "cinematic style",
        "duration": "5s",
        "emotions": "@emotion XX%",
        "start_frame": "Exact opening composition",
        "end_frame": "Exact closing composition — this feeds the next scene's start"
      }
    }
  ]
}`;

  const content=[];
  frames.forEach((f,i)=>{
    content.push({type:'text',text:`FRAME ${i+1}:`});
    content.push({type:'image',source:{type:'base64',media_type:'image/jpeg',data:f}});
  });
  content.push({type:'text',text:`Create a ${frames.length}-scene Higgsfield sequence.${context?`\nContext: ${context}`:''}\nReturn valid JSON only.`});

  try{
    const resp=await fetch(API_BASE+'/api/messages',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({model:'gemini-3-flash-preview',max_tokens:3000,system:systemPrompt,messages:[{role:'user',content}]})
    });
    if(!resp.ok){const e=await resp.json().catch(()=>({}));throw new Error(e.error||`API error: ${resp.status}`);}
    const data=await resp.json();
    const txt=data.content?.[0]?.text||'';
    const jsonMatch=txt.match(/\{[\s\S]*\}/);
    if(!jsonMatch)throw new Error('No JSON in response');
    const parsed=JSON.parse(repairJSON(jsonMatch[0]));
    allScenes=(parsed.scenes||[]).map((sc,i)=>{
      const vp=sc.video_prompt||{};
      return {
        scene_number:sc.scene_number||i+1,
        title:sc.title||`Scene ${i+1}`,
        video_prompt:vp.full_prompt||'',
        hf_camera_movement:vp.camera||'',
        hf_genre:vp.genre||'',
        hf_duration:vp.duration||'5s',
        hf_emotions:vp.emotions||'',
        hf_start_frame:vp.start_frame||'',
        hf_end_frame:vp.end_frame||'',
        archetype:'HF_GRID9'
      };
    });
    renderScenes('');
  }catch(err){
    console.error(err);
    showError(err.message);
  }
}
```

- [ ] **Step 2: Manual test** — HF → 9-Grid → upload 3+ images → Generate Mini Movie → verify multiple scene cards with Higgsfield badges and continuity in start/end frames.

---

## Task 10: Add generateHfSequential()

**Files:**
- Modify: `index.html` — insert after closing `}` of `generateSequential()` (around line ~2770)

Note: reuses the same `seqCurrentB64`, `seqFile`, `seqZone`, `seqPreview`, `seqStrip`, `seqInfo` DOM elements as Kling sequential. Uses `hfSeqHistory` instead of `seqHistory`.

- [ ] **Step 1: Add generateHfSequential() function**

```js
// GENERATE HF SEQUENTIAL
async function generateHfSequential(){
  if(!seqCurrentB64){alert('Please upload a frame.');return;}
  const context=document.getElementById('contextInput').value.trim();
  const sceneNum=hfSeqHistory.length+1;
  showLoading(`Generating Higgsfield scene ${sceneNum}...`);

  const prevScene=hfSeqHistory.length>0?hfSeqHistory[hfSeqHistory.length-1]:null;

  const systemPrompt=`You are a Higgsfield Cinema Studio video prompt specialist creating scene ${sceneNum} of a sequential story.${prevScene?` Continue from the previous scene — the new clip must open exactly where the previous one ended.`:''}

CHARACTER LOCK: Describe the subject exactly as visible in the reference image. Copy this description verbatim into full_prompt across all scenes.
CONTINUITY: start_frame must match the previous scene's end_frame word-for-word.${prevScene?`\nPREVIOUS END FRAME: "${prevScene.hf_end_frame}"`:''}
CAMERA: Name a specific Higgsfield-compatible camera move. Vary the move from scene to scene.
NEGATIVE PROMPT: full_prompt must end with "Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features, added accessories, props not in reference, deformed hands, incorrect finger count, asymmetrical facial features, unnatural joint angles, body warping, extra limbs, motion blur, temporal flickering, floating objects"

Return ONLY valid JSON:
{
  "title": "Scene title",
  "video_prompt": {
    "full_prompt": "Camera move. Subject + action. Environment. Lighting. Mood. Negative: ...",
    "camera": "Named camera move",
    "genre": "cinematic style",
    "duration": "5s",
    "emotions": "@emotion XX%",
    "start_frame": "${prevScene?`Must match previous end: ${prevScene.hf_end_frame}`:'Opening composition from the uploaded frame'}",
    "end_frame": "Precise closing composition — feeds into next scene"
  }
}`;

  const content=[];
  if(prevScene){
    content.push({type:'text',text:`PREVIOUS SCENE PROMPT:\n${prevScene.video_prompt}\n\nNEW FRAME:`});
  }
  content.push({type:'image',source:{type:'base64',media_type:'image/jpeg',data:seqCurrentB64}});
  content.push({type:'text',text:`Create scene ${sceneNum}.${context?`\nContext: ${context}`:''}\nReturn valid JSON only.`});

  try{
    const resp=await fetch(API_BASE+'/api/messages',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({model:'gemini-3-flash-preview',max_tokens:1500,system:systemPrompt,messages:[{role:'user',content}]})
    });
    if(!resp.ok){const e=await resp.json().catch(()=>({}));throw new Error(e.error||`API error: ${resp.status}`);}
    const data=await resp.json();
    const txt=data.content?.[0]?.text||'';
    const jsonMatch=txt.match(/\{[\s\S]*\}/);
    if(!jsonMatch)throw new Error('No JSON in response');
    const parsed=JSON.parse(repairJSON(jsonMatch[0]));
    const vp=parsed.video_prompt||{};

    const newScene={
      scene_number:sceneNum,
      title:parsed.title||`Scene ${sceneNum}`,
      video_prompt:vp.full_prompt||'',
      hf_camera_movement:vp.camera||'',
      hf_genre:vp.genre||'',
      hf_duration:vp.duration||'5s',
      hf_emotions:vp.emotions||'',
      hf_start_frame:vp.start_frame||'',
      hf_end_frame:vp.end_frame||'',
      archetype:'HF_SEQUENTIAL',
      frameB64:seqCurrentB64
    };
    hfSeqHistory.push(newScene);
    allScenes=hfSeqHistory;

    const strip=document.getElementById('seqStrip');
    const thumb=document.createElement('img');
    thumb.className='seq-hist-thumb';
    thumb.src='data:image/jpeg;base64,'+seqCurrentB64;
    strip.appendChild(thumb);

    document.getElementById('seqInfo').textContent=`Scene ${sceneNum} complete — upload frame ${sceneNum+1}`;
    clearImg('seq');
    updateGenBtn();
    renderScenes('');
  }catch(err){
    console.error(err);
    showError(err.message);
  }
}
```

- [ ] **Step 2: Reset hfSeqHistory when leaving sequential mode**

In `setHfMode()`, add a reset guard so switching away from `seq` clears history. Add at the very top of `setHfMode()`, before `hfMode=mode`:
```js
// Add at the very top of setHfMode(), before hfMode=mode:
if(hfMode==='seq' && mode!=='seq'){
  hfSeqHistory=[];
  seqCurrentB64=null;  // shared DOM slot — clear the actual state variable
  document.getElementById('seqStrip').innerHTML='';
  document.getElementById('seqInfo').textContent='Upload frame 1 to begin';
}
```

- [ ] **Step 3: Manual test** — HF → Sequential → upload frame → Generate Scene 1 → verify scene card → upload second frame → Continue → verify scene 2 start_frame matches scene 1 end_frame.

---

## Task 11: Reset hfSeqHistory in resetAll()

**Files:**
- Modify: `index.html:3322`

Current line 3322:
```js
seqCurrentB64=null;img2vidB64=null;seqHistory=[];allScenes=[];currentTreatment=null;qaWarnings=[];promptMap={};
```

- [ ] **Step 1: Add hfSeqHistory reset to line 3322**

Replace with:
```js
seqCurrentB64=null;img2vidB64=null;seqHistory=[];hfSeqHistory=[];allScenes=[];currentTreatment=null;qaWarnings=[];promptMap={};
```

---

## Task 12: Commit

- [ ] **Step 1: Commit**

```bash
git add index.html
git commit -m "feat: add Start+End, 9-Grid, Sequential modes to Higgsfield

Same image-upload workflow as Kling modes but generates Higgsfield-formatted
prompts (full_prompt + camera + genre + duration + emotions + start/end frames).
Reuses existing panels and clearImg/seqStrip DOM. hfSeqHistory tracks Higgsfield
sequential state separately from Kling seqHistory."
```

---

## Smoke Test Checklist

After all tasks complete, manually verify:

- [ ] Higgsfield platform → 5 buttons visible (MV, Story Chain, Start+End, 9-Grid, Sequential)
- [ ] HF MV and Story Chain: no regression, work as before
- [ ] HF Start+End: panel shows, upload 2 images, Generate Motion → Higgsfield badge on card
- [ ] HF 9-Grid: panel shows, upload 3+ images, Generate Mini Movie → multiple cards with HF badges
- [ ] HF Sequential: panel shows, upload frame → Generate → upload next → Continue → start_frame continuity correct
- [ ] Switching back to Kling: Kling modes work, panels are not cross-contaminated
- [ ] Switching HF Sequential → HF MV → back to Sequential: history is cleared
