
// API — call Render directly to avoid Vercel proxy timeouts on cold starts
const API_BASE = window.APULU_PROMPT_API_BASE || '/api/prompt-generator';

// STATE
let outputMode     = 'both';
let currentMode    = 'lyrics';
let hfMode              = 'story';      // 'story' | 'tiktok'
let tiktokShotCount     = 4;            // 3-6 shots for TikTok mode
let nb2SceneCount       = 1;            // 1/3/4/6 lookbook variants for NB2 desc mode
let nb2StylePreset      = 'vawn-editorial'; // cinematographer style preset for NB2 — see agents/cinematographer.js
let uploadedAudio       = null;         // { fileUri, mimeType } after upload
let hfInputMode         = 'track';      // 'track' | 'desc' — HF MV only
let currentAudioAnalysis= null;         // last audio analysis result
let imgBase64   = null;
let shirtBase64 = null;
let allScenes     = [];
let currentTreatment = null;
let qaWarnings    = [];
let promptMap     = {};
let lastReqBody   = null; // saved context for per-scene regeneration
let currentArtist = '';  // artist name preserved for per-scene regeneration

// UTIL
function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 130) + 'px';
}

function escHtml(s) {
  return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// Vawn hybrid narrative template (Nano Banana 2026 pipeline).
// Opener prefix is style-preset aware — see OPENERS map below. Includes
// "implied narrative", FilmStock + visible film grain, the influence
// carried in Mood, and closes with "photorealistic, no text".
//
// IMPORTANT: keep this map in sync with agents/cinematographer.js OPENERS.
const STYLE_OPENERS = {
  'vawn-editorial':       'A candid lifestyle photograph of the subject from the reference photo',
  '90s-disposable':       'Candid 1990s point-and-shoot snapshot of the subject from the reference photo',
  '70s-warm-film':        'Candid warm 1970s family-album photograph of the subject from the reference photo',
  'kodachrome-daylight':  'Candid 1980s daylight color-slide photograph of the subject from the reference photo',
  'cinestill-night':      'Candid grainy CineStill night photograph of the subject from the reference photo',
  'super8-dusk':          'Candid 1970s Super 8 film-frame still of the subject from the reference photo',
  'contax-highkey':       'Candid 2000s Contax T2 snapshot of the subject from the reference photo',
};

function cleanPromptText(v) {
  return String(v == null ? '' : v)
    .replace(/\bSUBJECT_ACTION IS LAW:\s*/gi, '')
    .replace(/\s+/g, ' ')
    .trim();
}

function normalizePromptPart(v) {
  return cleanPromptText(v)
    .toLowerCase()
    .replace(/[^\w\s]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

function uniquePromptParts(parts) {
  const seen = new Set();
  const out = [];
  for (const raw of parts) {
    const part = cleanPromptText(raw);
    if (!part) continue;
    const key = normalizePromptPart(part);
    if (!key || seen.has(key)) continue;
    seen.add(key);
    out.push(part);
  }
  return out;
}

function cleanMoodForPrompt(v) {
  return cleanPromptText(v)
    .replace(/\b(?:carries\s+)?[A-Z][A-Za-z .'-]+(?:'s)\s+/g, '')
    .replace(/\bin the spirit of [A-Z][A-Za-z .'-]+/gi, '')
    .replace(/\b(?:the\s+)?(?:high-key\s+)?[A-Z][A-Z .'-]{2,}\s+(?:fashion style|style)\s+(?:\u2014|-|\?)\s*/g, 'high-key snapshot style - ')
    .replace(/\s+/g, ' ')
    .trim();
}

function buildLeanConstraints(negativePrompt, hasShirtReference) {
  const source = [].concat(negativePrompt || []).map(cleanPromptText).join(', ').toLowerCase();
  const terms = ['no text', 'no watermark', 'no distorted hands', 'no extra limbs', 'no face warping'];
  if (hasShirtReference) {
    terms.push('no warped shirt graphic', 'no wrong shirt color');
  } else if (/warped clothing|morphed fabric/.test(source)) {
    terms.push('no warped clothing');
  }
  terms.push('no AI-smooth skin', 'no cinematic grade');
  return uniquePromptParts(terms).join(', ');
}

// Assemble the cinematographer's structured fields into a Nano Banana Pro
// prompt using the documented 7-Part Structure (Subject → Action → Setting →
// Composition → Lighting → Style → Constraints). Order matters — earlier
// sections carry more prompt weight. Section labels are explicit so NB2 can
// parse them as discrete instruction blocks.
//
// Field-to-section mapping (kept in lockstep with agents/cinematographer.js):
//   [Subject]      ← style-preset opener + Subject (expression/gaze) + MadeOutOf wardrobe
//   [Action]       ← Arrangement (what the body is doing)
//   [Setting]      ← Background (place + atmosphere)
//   [Composition]  ← Camera (type/lens/body) + Composition (framing/angle/focus)
//   [Lighting]     ← Lighting + ColorPalette.mood
//   [Style]        ← FilmStock + Mood (carries influence + "implied narrative")
//   [Constraints]  ← NegativePrompt
function flattenImagePrompt(p) {
  if (!p || typeof p !== 'object') return typeof p === 'string' ? p : '';

  const punct = s => (!s ? '' : (/[.!?]$/.test(s) ? s : s + '.'));
  const sect = (label, body) => (body ? `[${label}] ${punct(body)}` : '');

  // [Subject] — opener + expression/gaze + locked wardrobe. Identity comes from
  // the reference photo; never re-describe face, hair, or build.
  const baseOpener = STYLE_OPENERS[p.style_preset] || STYLE_OPENERS['vawn-editorial'];
  const subjBits = [].concat(p.Subject || []).filter(Boolean).map(cleanPromptText).filter(Boolean).join(', ');
  const outfitBits = [].concat(p.MadeOutOf || [])
    .map(cleanPromptText)
    .filter(s => s && !/^none\b/i.test(s));
  const hasShirtReference = outfitBits.some(s => /uploaded reference|@image|reference t-?shirt|shirt reference/i.test(s));
  const wardrobePrefix = hasShirtReference
    ? 'He wears the uploaded reference T-shirt as the visible top garment; preserve its color, fit, fabric texture, and graphic placement. Outfit coordinates naturally with'
    : 'He wears';
  const wardrobe = outfitBits.length ? `${wardrobePrefix} ${outfitBits.join(', ')}` : '';
  const subjectBody = [baseOpener, subjBits, wardrobe].filter(Boolean).join('. ');

  // [Action] — pure activity. The cinematographer's Arrangement field.
  const action = cleanPromptText(p.Arrangement);

  // [Setting] — pure place + atmosphere.
  const setting = cleanPromptText(p.Background);

  // [Composition] — camera body/lens + framing/angle/focus.
  const cam = p.Camera || {};
  const camStr = uniquePromptParts([cam.type, cam.lens, cam.body]).join(', ');
  const comp = p.Composition || {};
  const compParts = uniquePromptParts([comp.framing, comp.angle, comp.focus])
    .filter(part => normalizePromptPart(part) !== normalizePromptPart(cam.type));
  const compStr = compParts.join('. ');
  const composition = [camStr, compStr].filter(Boolean).join('. ');

  // [Lighting] — direction/quality/source + palette mood.
  const lighting = uniquePromptParts([p.Lighting, p.ColorPalette?.mood]).join(' ');

  // [Style] — film stock with grain + photographer influence + implied narrative.
  // Always include "photorealistic" so NB2 locks the medium.
  const filmStock = cleanPromptText(p.FilmStock);
  const mood = cleanMoodForPrompt(p.Mood);
  const styleCore = [filmStock, mood].filter(Boolean).join('. ');
  const style = styleCore
    ? (/photorealistic/i.test(styleCore) ? styleCore : `${styleCore}. Photorealistic`)
    : 'Photorealistic';

  // [Constraints] — comma-separated negatives. Always include "no text".
  const constraints = buildLeanConstraints(p.NegativePrompt, hasShirtReference);

  const blocks = [
    p.label || '',
    sect('Subject', subjectBody),
    sect('Action', action),
    sect('Setting', setting),
    sect('Composition', composition),
    sect('Lighting', lighting),
    sect('Style', style),
    sect('Constraints', constraints),
  ].filter(Boolean);

  return blocks.join('\n\n');
}

// HISTORY
const HIST_KEY = 'apulu_history';
const HIST_MAX = 25;

function loadHistory(){
  try{ return JSON.parse(localStorage.getItem(HIST_KEY)||'[]'); }catch(e){ return []; }
}

function saveToHistory(){
  const mode = currentMode;
  const ids = { lyrics:'lyricsInput', desc:'descInput', frames:'framesInput', grid:'gridStoryInput' };
  const el = document.getElementById(ids[mode] || 'contextInput');
  const text = el ? el.value.trim() : '';
  if(!text) return;
  const artist = document.getElementById('artistName').value.trim();
  let hist = loadHistory();
  // remove duplicate (same mode + same text)
  hist = hist.filter(e => !(e.inputMode===mode && e.text===text));
  hist.unshift({ id:Date.now(), inputMode:mode, artist, text, ts:Date.now(), scenes: allScenes.length ? allScenes : undefined });
  if(hist.length > HIST_MAX) hist = hist.slice(0, HIST_MAX);
  localStorage.setItem(HIST_KEY, JSON.stringify(hist));
}

function timeAgo(ts){
  const s = Math.floor((Date.now()-ts)/1000);
  if(s < 60)  return 'just now';
  const m = Math.floor(s/60);
  if(m < 60)  return m+'m ago';
  const h = Math.floor(m/60);
  if(h < 24)  return h+'h ago';
  return Math.floor(h/24)+'d ago';
}

function toggleHistory(){
  const panel = document.getElementById('histPanel');
  const btn   = document.getElementById('histToggleBtn');
  const open  = panel.classList.toggle('show');
  btn.classList.toggle('active', open);
  if(open) renderHistory();
}

function renderHistory(){
  const hist  = loadHistory();
  const panel = document.getElementById('histPanel');
  if(!hist.length){
    panel.innerHTML = '<div class="hist-empty">No history yet — generate something first</div>';
    return;
  }
  const labels = { lyrics:'Lyrics', desc:'Description', frames:'Start+End', grid:'9-Grid', context:'Context' };
  let html = hist.map((e,i) => {
    const label   = labels[e.inputMode] || e.inputMode;
    const ctxCls  = e.inputMode==='context' ? ' context' : '';
    const meta    = e.artist || '';
    const preview = e.text.length > 90 ? e.text.slice(0,90)+'…' : e.text;
    return `<div class="hist-entry" onclick="restoreHistory(${i})">
      <div class="hist-entry-body">
        <div class="hist-entry-meta">
          <span class="hist-mode-tag${ctxCls}">${escHtml(label)}</span>
          ${meta ? `<span class="hist-artist">${escHtml(meta)}</span>` : ''}
          <span class="hist-time">${timeAgo(e.ts)}</span>
        </div>
        <div class="hist-text">${escHtml(preview)}</div>
      </div>
      <button class="hist-del" onclick="event.stopPropagation();deleteHistory(${i})" title="Remove">✕</button>
    </div>`;
  }).join('');
  html += `<div class="hist-footer"><button class="hist-clear" onclick="clearHistory()">Clear all history</button></div>`;
  panel.innerHTML = html;
}

function restoreHistory(idx){
  const hist = loadHistory();
  const e = hist[idx];
  if(!e) return;
  // restore artist
  document.getElementById('artistName').value = e.artist || '';
  // switch output mode if needed for frames
  if((e.inputMode === 'frames' || e.inputMode === 'grid') && outputMode !== 'nb2') setOutputMode('nb2');
  // switch input mode
  if(e.inputMode !== 'context') setMode(e.inputMode);
  // populate the textarea
  const ids = { lyrics:'lyricsInput', desc:'descInput', frames:'framesInput', grid:'gridStoryInput', context:'contextInput' };
  const el = document.getElementById(ids[e.inputMode]);
  if(el){ el.value = e.text; autoResize(el); }
  // restore generated scenes if available
  if(e.scenes && e.scenes.length){
    allScenes = e.scenes;
    const artist = e.artist || '';
    currentArtist = artist;
    renderScenes(artist);
  }
  // close panel
  const panel = document.getElementById('histPanel');
  const btn   = document.getElementById('histToggleBtn');
  panel.classList.remove('show');
  btn.classList.remove('active');
}

function deleteHistory(idx){
  let hist = loadHistory();
  hist.splice(idx, 1);
  localStorage.setItem(HIST_KEY, JSON.stringify(hist));
  renderHistory();
}

function clearHistory(){
  localStorage.removeItem(HIST_KEY);
  renderHistory();
}

// IMAGE COMPRESSION
function compressImage(file, cb) {
  const MAX = 4*1024*1024, DIM = 1568;
  const reader = new FileReader();
  reader.onload = ev => {
    const img = new Image();
    img.onload = () => {
      let {width:w, height:h} = img;
      if(w>DIM||h>DIM){const r=Math.min(DIM/w,DIM/h);w=Math.round(w*r);h=Math.round(h*r);}
      const c=document.createElement('canvas');c.width=w;c.height=h;
      c.getContext('2d').drawImage(img,0,0,w,h);
      let q=0.88, url=c.toDataURL('image/jpeg',q);
      while(url.length*0.75>MAX&&q>0.3){q-=0.08;url=c.toDataURL('image/jpeg',q);}
      cb(url.split(',')[1],url);
    };
    img.src=ev.target.result;
  };
  reader.readAsDataURL(file);
}

function handleImg(e, slot) {
  const file=e.target.files[0]; if(!file) return;
  compressImage(file,(b64,url)=>{
    if(slot==='main'){imgBase64=b64;document.getElementById('imgPreview').src=url;document.getElementById('imgZone').classList.add('filled');}
    if(slot==='shirt'){shirtBase64=b64;document.getElementById('shirtPreview').src=url;document.getElementById('shirtZone').classList.add('filled');}
  });
  e.target.value='';
}

function clearImg(slot){
  if(slot==='main'){imgBase64=null;document.getElementById('imgPreview').src='';document.getElementById('imgZone').classList.remove('filled');}
  if(slot==='shirt'){shirtBase64=null;document.getElementById('shirtPreview').src='';document.getElementById('shirtZone').classList.remove('filled');}
}


// 9-GRID removed — grid9Container no longer exists

// MODE SETTERS
function setOutputMode(mode){
  // Deactivate studio FIRST so canvas + bottomBar are restored before UI updates run
  deactivateStudio();
  outputMode=mode;
  ['omBoth','omNb2','omVideo'].forEach(id=>{const el=document.getElementById(id);if(el)el.classList.remove('active');});
  const activeTab=document.getElementById({both:'omBoth',nb2:'omNb2',video:'omVideo'}[mode]);
  if(activeTab) activeTab.classList.add('active');

  // Phase 1: Image/Video/Both modes now route to the unified Create Prompt workspace.
  // The legacy canvas + composer remain in the DOM for Studio compatibility but
  // are hidden when in any non-Studio mode.
  const canvas    = document.getElementById('canvas');
  const bottomBar = document.getElementById('bottomBar');
  if (canvas)    canvas.style.display    = 'none';
  if (bottomBar) bottomBar.style.display = 'none';

  if (typeof showCreate === 'function') showCreate(mode);
}

/* ── Studio Tab ── */
function activateStudio() {
  // Mark Studio tab active, others inactive
  document.querySelectorAll('.h-tab').forEach(t => t.classList.remove('active'));
  const studioTab = document.getElementById('tabStudio');
  if (studioTab) studioTab.classList.add('active');

  // Keep output mode buttons VISIBLE so user can click them to exit Studio
  // (setOutputMode already calls deactivateStudio when clicked)
  // Hide only the prompt-mode badges
  const badgeNb2 = document.getElementById('badgeNb2');
  if (badgeNb2) badgeNb2.style.display = 'none';
  const badgeHf = document.getElementById('badgeHf');
  if (badgeHf) badgeHf.style.display = 'none';

  // Show studio badge
  const badgeStudio = document.getElementById('badgeStudio');
  if (badgeStudio) badgeStudio.style.display = 'flex';

  // Hide canvas + bottom bar + create view, show studio view
  const canvas = document.getElementById('canvas');
  if (canvas) canvas.style.display = 'none';
  const bottomBar = document.getElementById('bottomBar');
  if (bottomBar) bottomBar.style.display = 'none';
  if (typeof hideCreate === 'function') hideCreate();

  if (typeof showStudio === 'function') showStudio();
}

function deactivateStudio() {
  const studioTab = document.getElementById('tabStudio');
  if (studioTab) studioTab.classList.remove('active');

  // Restore prompt-mode badges (output mode buttons stay visible always)
  const badgeNb2 = document.getElementById('badgeNb2');
  if (badgeNb2) badgeNb2.style.display = '';
  const badgeHf = document.getElementById('badgeHf');
  if (badgeHf) badgeHf.style.display = '';

  // Hide studio badge
  const badgeStudio = document.getElementById('badgeStudio');
  if (badgeStudio) badgeStudio.style.display = 'none';

  // Force-hide studio view (canvas + bottomBar stay hidden — Create view handles non-studio modes)
  const studioView = document.getElementById('studioView');
  if (studioView) studioView.style.display = 'none';

  if (typeof hideStudio === 'function') hideStudio();
}


function setHfMode(mode){
  hfMode=mode;
  // Toggle tiktok-active class on composer pill for CSS targeting
  const pill=document.getElementById('composerPill');
  if(pill) pill.classList.toggle('tiktok-active', mode==='tiktok');
  // Button active states
  ['hwStory','hwTiktok'].forEach(id=>{
    const el=document.getElementById(id);
    if(el) el.className='ctrl-btn';
  });
  const activeId={story:'hwStory',tiktok:'hwTiktok'}[mode];
  if(activeId) document.getElementById(activeId).className='ctrl-btn active-hf';

  // TikTok is description-driven: always force desc mode
  if(mode==='tiktok') setHfInputMode('desc');

  // Audio uploader: hidden in TikTok, shown in story mode (no toggle — always available)
  const audioEl=document.getElementById('hfAudioUpload');
  if(mode==='tiktok'){
    if(audioEl) audioEl.style.display='none';
  } else {
    if(audioEl) audioEl.style.display='';
  }
  // Style selector: hide in story/tiktok
  const styleEl=document.getElementById('videoStyleSelect');
  if(styleEl) styleEl.style.display='none';

  // TikTok-specific UI
  const tiktokShots=document.getElementById('ctrlTiktokShots');
  if(tiktokShots) tiktokShots.style.display=mode==='tiktok'?'flex':'none';
  const expandBtn=document.getElementById('btnGenerateDescription');
  if(expandBtn) expandBtn.style.display=mode==='tiktok'?'':'none';

  const lyricsEl=document.getElementById('lyricsInput');
  if(mode==='tiktok'){
    lyricsEl.placeholder='Type a rough idea — location, vibe, what happens...';
    lyricsEl.style.display='block';
  } else if(mode==='story'){
    lyricsEl.placeholder='Paste lyrics or describe your track — or upload audio below and Apulu will listen.';
  } else {
    lyricsEl.placeholder='Paste lyrics or describe your track...';
  }

  updatePanels();
  updateInputArea();
  if(mode==='tiktok'&&lyricsEl) lyricsEl.style.display='block';
  updateGenBtn();
  updateEmptyState();
}

function setTiktokShotCount(n){
  tiktokShotCount=n;
  [3,4,5,6].forEach(v=>{
    const el=document.getElementById('tiktokShot'+v);
    if(el) el.className='tiktok-shot-chip'+(v===n?' active':'');
  });
}

function setNb2SceneCount(n){
  nb2SceneCount=n;
  [1,3,4,6].forEach(v=>{
    const el=document.getElementById('nb2Shot'+v);
    if(el) el.className='tiktok-shot-chip'+(v===n?' active':'');
  });
}

function setNb2StylePreset(preset){
  nb2StylePreset = preset || 'vawn-editorial';
  const el = document.getElementById('nb2StylePreset');
  if(el && el.value !== nb2StylePreset) el.value = nb2StylePreset;
}

async function generateDescription(){
  const textarea=document.getElementById('lyricsInput')||document.getElementById('descInput');
  const idea=(textarea?.value||'').trim();
  if(!idea){alert('Type a rough idea first');return;}
  const btn=document.getElementById('btnGenerateDescription');
  if(btn){btn.disabled=true;btn.textContent='Expanding...';}
  try{
    const resp=await fetch(API_BASE+'/api/generate-description',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({idea})
    });
    if(!resp.ok) throw new Error('Failed');
    const data=await resp.json();
    if(data.description&&textarea) textarea.value=data.description;
  }catch(err){
    alert('Could not expand idea: '+err.message);
  }finally{
    if(btn){btn.disabled=false;btn.textContent='Expand Idea';}
  }
}

async function handleAudioFile(input){
  const file=input.files[0];
  if(!file) return;
  const label=document.getElementById('hfAudioLabelText');
  label.textContent=`${file.name} (${(file.size/1024/1024).toFixed(1)} MB) — uploading…`;
  uploadedAudio=null;
  const mimeType=file.type||'audio/mpeg';
  try{
    if(file.size > 94*1024*1024) throw new Error('file too large (max ~94 MB)');
    const url=`${API_BASE}/api/upload-audio?mime=${encodeURIComponent(mimeType)}&name=${encodeURIComponent(file.name)}`;
    const resp=await fetch(url,{
      method:'POST',
      headers:{'Content-Type':'application/octet-stream'},
      body:file,
    });
    const data=await resp.json();
    if(!resp.ok) throw new Error(data.error||`Upload failed (${resp.status})`);
    uploadedAudio={fileUri:data.fileUri,mimeType:data.mimeType};
    label.textContent=`✓ ${file.name} — ready`;
    document.getElementById('hfAudioRemove').style.display='';
  }catch(err){
    label.textContent=`Upload failed: ${err.message}`;
    console.error('Audio upload error:',err);
  }
}

function clearAudioTrack(){
  uploadedAudio=null;
  document.getElementById('hfAudioLabelText').textContent='Drop audio or click to upload';
  document.getElementById('hfAudioRemove').style.display='none';
  document.getElementById('audioFileInput').value='';
}

// Image mode: upload a track → Apulu listens → fills #descInput with a 1-2 sentence concept.
async function handleConceptAudio(input){
  const file=input.files&&input.files[0];
  if(!file) return;
  const status=document.getElementById('conceptAudioStatus');
  const btn=document.getElementById('btnConceptFromAudio');
  const descEl=document.getElementById('descInput');
  const mimeType=file.type||'audio/mpeg';
  const setStatus=(t,kind)=>{ if(!status) return; status.textContent=t; status.dataset.kind=kind||''; };
  try{
    if(file.size>94*1024*1024) throw new Error('file too large (max ~94 MB)');
    btn.disabled=true; const original=btn.textContent; btn.textContent='Listening…';
    setStatus(`Uploading ${file.name} (${(file.size/1024/1024).toFixed(1)} MB)…`, 'info');

    // Stage 1 — upload to Gemini Files API
    const upUrl=`${API_BASE}/api/upload-audio?mime=${encodeURIComponent(mimeType)}&name=${encodeURIComponent(file.name)}`;
    const upResp=await fetch(upUrl,{method:'POST',headers:{'Content-Type':'application/octet-stream'},body:file});
    const upData=await upResp.json();
    if(!upResp.ok) throw new Error(upData.error||`Upload failed (${upResp.status})`);

    // Stage 2 — analyze + condense
    setStatus('Apulu is listening to the track…', 'info');
    const artistDescription=(document.getElementById('artistName')?.value||'').trim();
    const cResp=await fetch(`${API_BASE}/api/concept-from-audio`,{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({fileUri:upData.fileUri,mimeType:upData.mimeType,artistDescription}),
    });
    const cData=await cResp.json();
    if(!cResp.ok) throw new Error(cData.error||`Concept failed (${cResp.status})`);
    if(!cData.concept) throw new Error('Empty concept returned');

    if(descEl){ descEl.value=cData.concept; if(typeof autoResize==='function') autoResize(descEl); }
    const tag=cData.analysis?.title&&cData.analysis.title!=='Unknown'?cData.analysis.title:file.name;
    setStatus(`✓ Concept written from ${tag}`, 'ok');
    btn.textContent=original||'🎵 Concept from audio';
  }catch(err){
    console.error('Concept-from-audio error:',err);
    setStatus(`Failed: ${err.message}`, 'err');
    btn.textContent='🎵 Concept from audio';
  }finally{
    btn.disabled=false;
    input.value='';
  }
}

function setHfInputMode(mode){
  // Toggle removed — kept as a no-op stub so legacy callers (e.g. setHfMode('tiktok')) don't break.
  hfInputMode=mode;
}


function updatePanels(){
  const showPhoto=outputMode==='nb2';
  document.getElementById('imgZone').style.display=showPhoto?'flex':'none';
  const shirtZone=document.getElementById('shirtZone');
  if(shirtZone) shirtZone.style.display=showPhoto?'flex':'none';
  document.getElementById('composerPill').style.borderRadius='18px';
  document.getElementById('composerPill').style.borderTop='';
}

function updateInputArea(){
  const isMV=outputMode==='nb2';
  // In TikTok mode, always show lyricsInput, hide everything else
  if(hfMode==='tiktok'&&outputMode!=='nb2'){
    document.getElementById('ctrlInputMode').style.display='none';
    document.getElementById('lyricsInput').style.display='block';
    const descEl=document.getElementById('descInput');
    if(descEl) descEl.style.display='none';
    return;
  }
  document.getElementById('ctrlInputMode').style.display=isMV?'flex':'none';
  document.getElementById('lyricsInput').style.display=(isMV&&currentMode==='lyrics')||(!isMV)?'block':'none';
  const descEl=document.getElementById('descInput');
  if(descEl) descEl.style.display=isMV&&currentMode==='desc'?'block':'none';
  const descHelpers=document.getElementById('descHelpers');
  if(descHelpers) descHelpers.style.display=isMV&&currentMode==='desc'?'flex':'none';
  const nb2Shots=document.getElementById('ctrlNb2Shots');
  if(nb2Shots) nb2Shots.style.display=isMV&&currentMode==='desc'?'flex':'none';
  // Style preset selector — visible for any NB2 output (both lyrics and desc modes).
  const nb2Style=document.getElementById('ctrlNb2Style');
  if(nb2Style) nb2Style.style.display=isMV?'flex':'none';
}

function updateGenBtn(){
  const btn=document.getElementById('genBtn');
  if(outputMode==='nb2'){btn.textContent='Generate';btn.className='gen-btn';return;}
  if(hfMode==='tiktok'){btn.textContent='Generate TikTok';btn.className='gen-btn violet';return;}
  if(hfMode==='story'){btn.textContent='Generate Story';btn.className='gen-btn violet';return;}
  btn.textContent='Generate';btn.className='gen-btn';
}

function updateCopyBtns(){
  document.getElementById('copyImgBtn').style.display=outputMode!=='video'?'inline-flex':'none';
  document.getElementById('copyVidBtn').style.display=outputMode!=='nb2'?'inline-flex':'none';
}

function updateEmptyState(){
  const hints={
    nb2:'Upload a photo · Paste lyrics · Hit Generate',
    story:'Upload a track or describe your story · Hit Generate Story',
    tiktok:'Type a rough idea · Expand Idea · Hit Generate TikTok',
  };
  const hint=outputMode==='nb2'?hints.nb2:(hints[hfMode]||hints.story);
  document.getElementById('emptyTxt').textContent=hint;
}

function setMode(mode){
  currentMode=mode;
  const lyricsBtn = document.getElementById('modeLyrics');
  if (lyricsBtn) lyricsBtn.classList.toggle('active', mode==='lyrics');
  const descBtn = document.getElementById('modeDesc');
  if (descBtn) descBtn.classList.toggle('active', mode==='desc');
  // modeFrames / modeGrid removed with Kling modes — guard with null checks
  const framesBtn = document.getElementById('modeFrames');
  if (framesBtn) framesBtn.classList.toggle('active', mode==='frames');
  const gridBtn = document.getElementById('modeGrid');
  if (gridBtn) gridBtn.classList.toggle('active', mode==='grid');
  updateInputArea();
  updateEmptyState();
}

// JSON REPAIR
function repairJSON(raw){
  raw=raw.replace(/,\s*([}\]])/g,'$1');
  let inStr=false,escape=false;const stack=[];
  for(let i=0;i<raw.length;i++){
    const c=raw[i];
    if(escape){escape=false;continue;}
    if(c==='\\'){escape=true;continue;}
    if(c==='"'&&!inStr){inStr=true;continue;}
    if(c==='"'&&inStr){inStr=false;continue;}
    if(inStr)continue;
    if(c==='{')stack.push('}');
    if(c==='[')stack.push(']');
    if(c==='}'||c===']')stack.pop();
  }
  if(inStr)raw+='"';
  while(stack.length)raw+=stack.pop();
  return raw;
}

// GENERATE DISPATCHER
async function generate(){
  try {
    saveToHistory();
    if(outputMode==='nb2') return generateMV();  // NB2 image-only mode
    if(hfMode==='tiktok') return generateStory(tiktokShotCount);
    if(hfMode==='story') return generateStory();
  } catch (err) {
    console.error('Generate error:', err);
    showError(err.message || 'Generation failed');
  }
}

// UI HELPERS
function showLoading(msg){
  document.getElementById('emptyState').style.display='none';
  document.getElementById('loadingState').classList.add('on');
  document.getElementById('loadTxt').textContent=msg;
  document.getElementById('genBtn').disabled=true;
}

let _loadingInterval = null;

function startPipelineLoadingCycle() {
  const stages = [
    'WAKING UP THE SERVER...',
    'READING THE ROOM...',
    'STYLING THE LOOK...',
    'SETTING THE SHOT...',
    'DIRECTING THE MOTION...',
  ];
  let i = 0;
  document.getElementById('loadTxt').textContent = stages[0];
  _loadingInterval = setInterval(() => {
    i = (i + 1) % stages.length;
    document.getElementById('loadTxt').textContent = stages[i];
  }, 8000);
}

function stopPipelineLoadingCycle() {
  if (_loadingInterval) {
    clearInterval(_loadingInterval);
    _loadingInterval = null;
  }
}

function hideLoading(){
  document.getElementById('loadingState').classList.remove('on');
  document.getElementById('genBtn').disabled=false;
  collapseAllPanels();
}
function collapseAllPanels(){
  // No expandable panels remaining — this is a no-op kept for compatibility
}
function showError(msg){
  hideProgress();
  hideLoading();
  document.getElementById('emptyState').style.display='flex';
  document.getElementById('emptyState').innerHTML=`<div style="font-size:28px">⚠</div><div style="font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:1px;text-transform:uppercase;color:var(--red);margin-top:10px;max-width:480px;text-align:center;">${escHtml(msg)}</div>`;
}

// ── WARDROBE MEMORY ─────────────────────────────────────────────────────────
function loadWardrobe(){
  try{
    const raw=localStorage.getItem('apulu_wardrobe');
    const parsed=raw?JSON.parse(raw):{};
    return{
      shirts:Array.isArray(parsed.shirts)?parsed.shirts:[],
      pants:Array.isArray(parsed.pants)?parsed.pants:[],
      jackets:Array.isArray(parsed.jackets)?parsed.jackets:[],
      hats:Array.isArray(parsed.hats)?parsed.hats:[]
    };
  }catch(e){return{shirts:[],pants:[],jackets:[],hats:[]};}
}

function wardrobeCount(){
  const w=loadWardrobe();
  return(Array.isArray(w.shirts)?w.shirts.length:0)
       +(Array.isArray(w.pants)?w.pants.length:0)
       +(Array.isArray(w.jackets)?w.jackets.length:0)
       +(Array.isArray(w.hats)?w.hats.length:0);
}

function updateWardrobeCountLabel(){
  const el=document.getElementById('wardrobeCountLabel');
  if(!el)return;
  const n=wardrobeCount();
  el.textContent=n===0?'Wardrobe: empty':`Wardrobe: ${n} pieces`;
}

function clearWardrobe(){
  localStorage.removeItem('apulu_wardrobe');
  updateWardrobeCountLabel();
}

function saveWardrobe(scenes){
  if(!Array.isArray(scenes))return;
  const w=loadWardrobe();
  const MAP={shirt:'shirts',pants:'pants',jacket:'jackets',hat:'hats'};
  scenes.forEach(s=>{
    const u=s&&s.wardrobe_used;
    if(!u||typeof u!=='object')return;
    Object.entries(MAP).forEach(([key,arr])=>{
      const val=(u[key]||'').trim();
      if(!val||val.toLowerCase()==='none')return;
      if(!w[arr].some(x=>x.toLowerCase()===val.toLowerCase())){
        w[arr].push(val);
      }
    });
  });
  // Cap at 40 per category — keep ~7 generations of memory while staying
  // small enough that the model can actually reason against the list
  // (200 was effectively unbounded and made repeats more likely).
  Object.keys(MAP).forEach(k=>{const a=MAP[k];if(w[a].length>40)w[a]=w[a].slice(-40);});
  localStorage.setItem('apulu_wardrobe',JSON.stringify(w));
  updateWardrobeCountLabel();
}

function buildWardrobePromptBlock(w){
  const lines=[];
  if(w.shirts.length)lines.push(`Shirts used: ${w.shirts.join(', ')}`);
  if(w.pants.length)lines.push(`Pants used: ${w.pants.join(', ')}`);
  if(w.jackets.length)lines.push(`Jackets used: ${w.jackets.join(', ')}`);
  if(w.hats.length)lines.push(`Hats used: ${w.hats.join(', ')}`);
  if(!lines.length)return'';
  return`WARDROBE MEMORY — these garment pieces have already been used in previous generations. Do NOT repeat or closely resemble any item on this list. Every scene in this generation must use entirely new garment choices not on this list.\n${lines.join('\n')}\n\n`;
}
// ── END WARDROBE MEMORY ──────────────────────────────────────────────────────
// ── ARTIST PERSISTENCE ───────────────────────────────────────────────────────
function loadArtistFields(){
  const a=localStorage.getItem('apulu_artist');
  if(a)document.getElementById('artistName').value=a;
}
function saveArtistFields(artist){
  if(artist)localStorage.setItem('apulu_artist',artist);
}
// ── END ARTIST PERSISTENCE ───────────────────────────────────────────────────
// ── STYLE WORLD MEMORY ───────────────────────────────────────────────────────
function loadStyleWorlds(){
  try{
    const raw=localStorage.getItem('apulu_styleworlds');
    const parsed=raw?JSON.parse(raw):{};
    return{worlds:Array.isArray(parsed.worlds)?parsed.worlds:[]};
  }catch(e){return{worlds:[]};}
}

function styleWorldCount(){
  const sw=loadStyleWorlds();
  return Array.isArray(sw.worlds)?sw.worlds.length:0;
}

function updateStyleWorldLabel(){
  const el=document.getElementById('styleWorldLabel');
  if(!el)return;
  el.textContent=`Worlds: ${styleWorldCount()}/4 used`;
}

function clearStyleWorlds(){
  localStorage.removeItem('apulu_styleworlds');
  updateStyleWorldLabel();
}

function saveStyleWorlds(scenes){
  if(!Array.isArray(scenes))return;
  const sw=loadStyleWorlds();
  scenes.forEach(s=>{
    const val=((s&&s.style_world)||'').trim();
    if(!val||val.toLowerCase()==='none')return;
    if(!sw.worlds.some(x=>x.toLowerCase()===val.toLowerCase())){
      sw.worlds.push(val);
    }
  });
  if(sw.worlds.length>4)sw.worlds=sw.worlds.slice(-4);
  localStorage.setItem('apulu_styleworlds',JSON.stringify(sw));
  updateStyleWorldLabel();
}

function buildStyleWorldPromptBlock(sw){
  if(!Array.isArray(sw.worlds)||!sw.worlds.length)return'';
  return`STYLE WORLD MEMORY — these style worlds have already been used in previous generations. Do NOT use any world on this list. Every scene in this generation must use a style world not on this list.\nWorlds used: ${sw.worlds.join(', ')}\n\n`;
}
// ── END STYLE WORLD MEMORY ───────────────────────────────────────────────────

// ── VARIETY MEMORY (generic helpers) ─────────────────────────────────────────
// All cross-generation "do not repeat" tracks share one storage shape:
// localStorage[key] = JSON array of strings (most recent at end).
function _loadList(key){
  try{ const raw=localStorage.getItem(key); const p=raw?JSON.parse(raw):[]; return Array.isArray(p)?p:[]; }
  catch(e){ return []; }
}
function _pushAndSave(key, items, cap){
  let arr=_loadList(key);
  items.forEach(it=>{
    if(!it) return;
    const v=String(it).trim();
    if(!v) return;
    if(!arr.some(x=>x.toLowerCase()===v.toLowerCase())) arr.push(v);
  });
  if(arr.length>cap) arr=arr.slice(-cap);
  localStorage.setItem(key, JSON.stringify(arr));
  return arr;
}
function _clearList(key){ localStorage.removeItem(key); }

// ── LOCATION MEMORY ──────────────────────────────────────────────────────────
// Tracks the last N locations used across generations so the architect can
// avoid repeating them. Mirror of the style world memory pattern above.
const LOCATION_MEMORY_MAX = 12;

function loadLocations(){
  try{
    const raw=localStorage.getItem('apulu_locations');
    const parsed=raw?JSON.parse(raw):{};
    return{locations:Array.isArray(parsed.locations)?parsed.locations:[]};
  }catch(e){return{locations:[]};}
}

function clearLocations(){
  localStorage.removeItem('apulu_locations');
}

function saveLocations(scenes){
  if(!Array.isArray(scenes))return;
  const lm=loadLocations();
  scenes.forEach(s=>{
    const loc=((s&&s.image_prompt&&s.image_prompt.label)||'').trim();
    // The pipeline writes label as "WORLD X — NAME | location, time_of_day".
    // Pull the location half (after the pipe, before the comma).
    const afterPipe=loc.split('|')[1]||'';
    const locationOnly=afterPipe.split(',')[0].trim();
    if(!locationOnly)return;
    // Case-insensitive dedupe; normalize to lowercase for comparison
    if(!lm.locations.some(x=>x.toLowerCase()===locationOnly.toLowerCase())){
      lm.locations.push(locationOnly);
    }
  });
  if(lm.locations.length>LOCATION_MEMORY_MAX) lm.locations=lm.locations.slice(-LOCATION_MEMORY_MAX);
  localStorage.setItem('apulu_locations',JSON.stringify(lm));
}

function buildLocationPromptBlock(lm){
  if(!Array.isArray(lm.locations)||!lm.locations.length)return'';
  return`LOCATION MEMORY — these locations have appeared in recent generations. Do NOT use any of them again. Pick fresh locations that haven't appeared recently. Substantive variation only — a "different laundromat" is still a laundromat.\nLocations used recently: ${lm.locations.join(' | ')}`;
}
// ── END LOCATION MEMORY ──────────────────────────────────────────────────────

// ── VARIETY MEMORY: camera angles / lighting / influences / jewelry / headwear ──
// These keep cross-generation variety on the cinematographer + stylist side.
// Caps deliberately small so the prompt stays digestible AND the model has a
// shrinking-but-not-yet-empty pool to pick from.
const ANGLE_MEMORY_MAX     = 16;  // 26 unique angles total → keep last ~3 generations
const LIGHTING_MEMORY_MAX  = 12;  // 18 unique setups → keep last ~3 generations
const INFLUENCE_MEMORY_MAX = 8;   // ~10-12 photographers per preset → keep last ~2 generations
const JEWELRY_MEMORY_MAX   = 8;   // 11 jewelry options → keep last ~2 generations
const HEADWEAR_MEMORY_MAX  = 10;  // 20 headwear types → keep last ~2 generations

// Extract the angle name from an Arrangement string like "LEANING CASUAL — subject..."
function extractAngle(arrangement){
  if(typeof arrangement !== 'string') return '';
  const m = arrangement.match(/^([A-Z][A-Z0-9 \/\-']{2,40}?)\s+—\s+/);
  return m ? m[1].trim() : '';
}
// Extract lighting setup name from Lighting string like "GOLDEN HOUR NATURAL — low sun..."
function extractLighting(lighting){
  if(typeof lighting !== 'string') return '';
  const m = lighting.match(/^([A-Z][A-Z0-9 \/\-']{2,40}?)\s+—\s+/);
  return m ? m[1].trim() : '';
}
// Extract photographer name from Mood string. Matches the explicit "PHOTOGRAPHER" caps tokens.
const KNOWN_INFLUENCES = [
  'HYPE WILLIAMS','GORDON PARKS','ROY DECARAVA','JAMEL SHABAZZ','GREGORY CREWDSON',
  'RICKY POWELL','NAN GOLDIN','LARRY CLARK','WILLIAM EGGLESTON','SAUL LEITER',
  'JOEL MEYEROWITZ','ERNST HAAS','GORDON WILLIS','HARRIS SAVIDES','ROBBY MULLER',
  'WONG KAR-WAI','HEDI SLIMANE','COREY OLSEN','JUERGEN TELLER','TYRONE LEBON',
  'MARIO SORRENTI','DARYL PEVETO','TODD HIDO','VIVIAN MAIER',
];
function extractInfluence(mood){
  if(typeof mood !== 'string') return '';
  for(const name of KNOWN_INFLUENCES){
    if(mood.includes(name)) return name;
  }
  return '';
}

function loadAngles(){     return { items: _loadList('apulu_angles') };     }
function loadLighting(){   return { items: _loadList('apulu_lighting') };   }
function loadInfluences(){ return { items: _loadList('apulu_influences') }; }
function loadJewelry(){    return { items: _loadList('apulu_jewelry') };    }
function loadHeadwear(){   return { items: _loadList('apulu_headwear') };   }

function clearAngles(){     _clearList('apulu_angles');     }
function clearLighting(){   _clearList('apulu_lighting');   }
function clearInfluences(){ _clearList('apulu_influences'); }
function clearJewelry(){    _clearList('apulu_jewelry');    }
function clearHeadwear(){   _clearList('apulu_headwear');   }

function saveVarietyFromScenes(scenes){
  if(!Array.isArray(scenes)) return;
  const angles=[], lighting=[], influences=[], jewelry=[], headwear=[];
  scenes.forEach(s=>{
    const ip = s && s.image_prompt;
    if(!ip) return;
    const angle = extractAngle(ip.Arrangement || '');
    if(angle) angles.push(angle);
    const lit = extractLighting(ip.Lighting || '');
    if(lit) lighting.push(lit);
    const inf = extractInfluence(ip.Mood || '');
    if(inf) influences.push(inf);
    // Jewelry: stylist puts it as the last MadeOutOf item (pipeline appends s2.jewelry).
    // Save the full last entry verbatim for memory matching.
    const made = Array.isArray(ip.MadeOutOf) ? ip.MadeOutOf : [];
    const lastMade = made.length ? String(made[made.length-1]).trim() : '';
    // Heuristic: jewelry strings are short and start with "A " or contain "chain", "watch", "bracelet", "earring", "necklace", "cuff", "bangle"
    if(/\b(chain|watch|bracelet|earring|necklace|cuff|bangle|pendant)\b/i.test(lastMade)) jewelry.push(lastMade);
    // Headwear: MadeOutOf[3] per the stylist's locked slot order.
    const hat = made[3] ? String(made[3]).trim() : '';
    if(hat && !/^none\b/i.test(hat)) headwear.push(hat);
  });
  if(angles.length)     _pushAndSave('apulu_angles',     angles,     ANGLE_MEMORY_MAX);
  if(lighting.length)   _pushAndSave('apulu_lighting',   lighting,   LIGHTING_MEMORY_MAX);
  if(influences.length) _pushAndSave('apulu_influences', influences, INFLUENCE_MEMORY_MAX);
  if(jewelry.length)    _pushAndSave('apulu_jewelry',    jewelry,    JEWELRY_MEMORY_MAX);
  if(headwear.length)   _pushAndSave('apulu_headwear',   headwear,   HEADWEAR_MEMORY_MAX);
}

function buildAngleMemoryBlock(){
  const items = loadAngles().items;
  if(!items.length) return '';
  return `CAMERA ANGLE MEMORY — these angles have been used in recent generations. Do NOT pick any of them. If every angle on this list is the only fit for a scene, pick the one that appears EARLIEST (oldest). Verification step: before finalizing each scene's angle, confirm it does not appear on this list.\nAngles used recently: ${items.join(' | ')}`;
}
function buildLightingMemoryBlock(){
  const items = loadLighting().items;
  if(!items.length) return '';
  return `LIGHTING SETUP MEMORY — these lighting setups have been used in recent generations. Do NOT pick any of them. Verification step: before finalizing each scene's lighting, confirm it does not appear on this list.\nLighting setups used recently: ${items.join(' | ')}`;
}
function buildInfluenceMemoryBlock(){
  const items = loadInfluences().items;
  if(!items.length) return '';
  return `PHOTOGRAPHER INFLUENCE MEMORY — these photographer references have been used in recent generations. Do NOT name any of them in the Mood field. Pick fresh influences from the active preset's APPROVED list.\nInfluences used recently: ${items.join(' | ')}`;
}
function buildJewelryMemoryBlock(){
  const items = loadJewelry().items;
  if(!items.length) return '';
  return `JEWELRY MEMORY — these jewelry choices have been used in recent generations. Do NOT use them again. Pick a different jewelry option from the JEWELRY rotation list.\nJewelry used recently: ${items.join(' | ')}`;
}
function buildHeadwearMemoryBlock(){
  const items = loadHeadwear().items;
  if(!items.length) return '';
  return `HEADWEAR MEMORY — these headwear choices have been used in recent generations. Do NOT use them again. Pick a different hat from the HEADWEAR rotation list.\nHeadwear used recently: ${items.join(' | ')}`;
}
// ── END VARIETY MEMORY ──────────────────────────────────────────────────────

// SSE STREAMING HELPER
// Connects to a POST endpoint that returns Server-Sent Events.
// Returns a cancel function.
function connectSSE(url, body, handlers) {
  const ctrl = new AbortController();

  fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal: ctrl.signal,
  }).then(async (response) => {
    if (!response.ok) {
      let errMsg = `API error: ${response.status}`;
      try { const j = await response.json(); if (j.error) errMsg = j.error; } catch (_) {}
      handlers.onError(new Error(errMsg));
      return;
    }
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    while (true) {
      let chunk;
      try { chunk = await reader.read(); } catch (e) {
        if (ctrl.signal.aborted) return;
        handlers.onError(e); return;
      }
      if (chunk.done) break;
      buffer += decoder.decode(chunk.value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop(); // keep incomplete last line
      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith(':')) continue; // ignore keep-alives
        if (trimmed.startsWith('data: ')) {
          const payload = trimmed.slice(6);
          try {
            const event = JSON.parse(payload);
            handlers.onEvent(event);
          } catch (e) {
            // skip malformed lines
          }
        }
      }
    }
  }).catch((err) => {
    if (ctrl.signal.aborted) return;
    handlers.onError(err);
  });

  return () => ctrl.abort();
}

// PROGRESS BAR HELPERS
let _cancelSSE = null;

function showProgress(stages) {
  document.getElementById('emptyState').style.display = 'none';
  document.getElementById('loadingState').classList.remove('on');
  document.getElementById('progressBar').classList.add('on');
  document.getElementById('genBtn').disabled = true;
  const container = document.getElementById('progressStages');
  container.innerHTML = '';
  stages.forEach((s) => {
    const row = document.createElement('div');
    row.className = 'progress-stage';
    row.id = 'pstage_' + s.key;
    row.innerHTML = `<span class="progress-stage-icon">⏳</span><span class="progress-stage-name">${escHtml(s.label)}</span>`;
    container.appendChild(row);
  });
}

function updateProgressStage(key, status) {
  const row = document.getElementById('pstage_' + key);
  if (!row) return;
  const icon = row.querySelector('.progress-stage-icon');
  row.className = 'progress-stage ' + status;
  if (status === 'running')   icon.textContent = '🔄';
  else if (status === 'complete') icon.textContent = '✅';
  else if (status === 'skipped')  icon.textContent = '⏭️';
  else                            icon.textContent = '⏳';
}

function hideProgress() {
  document.getElementById('progressBar').classList.remove('on');
  document.getElementById('genBtn').disabled = false;
  _cancelSSE = null;
}

function cancelGeneration() {
  if (_cancelSSE) { _cancelSSE(); _cancelSSE = null; }
  hideProgress();
  if (allScenes.length === 0) {
    document.getElementById('emptyState').style.display = '';
  }
  collapseAllPanels();
}

// GENERATE STORY CHAIN (hf-story mode) — audio analysis + single-agent story director
function generateStory(overrideSceneCount){
  const artist=document.getElementById('artistName').value.trim()||'Artist';
  saveArtistFields(artist);
  // Read from whichever textarea is visible (lyricsInput or descInput)
  const lyricsVal=document.getElementById('lyricsInput')?.value?.trim()||'';
  const descVal=document.getElementById('descInput')?.value?.trim()||'';
  const concept=lyricsVal||descVal;

  if(!uploadedAudio && !concept){
    alert(hfMode==='tiktok'?'Type a rough idea first — or use Expand Idea to generate one.':'Upload an audio file or enter a concept/direction to generate a story chain.');
    return;
  }

  const stages=[
    ...(uploadedAudio?[{key:'audio_analyzer',label:'Listening to Track'}]:[]),
    {key:'story_director',label:'Story Director'},
    ...(hfMode==='tiktok'?[{key:'edit_director',label:'Edit Director'}]:[]),
  ];
  showProgress(stages);
  collapseAllPanels();

  const reqBody={
    fileUri:uploadedAudio?.fileUri||null,
    mimeType:uploadedAudio?.mimeType||null,
    concept:concept||null,
    mode:hfMode,
    ...(overrideSceneCount?{sceneCount:overrideSceneCount}:{}),
  };

  _cancelSSE=connectSSE(API_BASE+'/api/generate-story-stream', reqBody, {
    onEvent(event){
      if(event.type==='stage'){
        updateProgressStage(event.name, event.status);
        if(event.type==='stage' && event.name==='audio_analyzer' && event.status==='complete' && event.audioAnalysis){
          currentAudioAnalysis=event.audioAnalysis;
        }
      } else if(event.type==='done'){
        hideProgress();
        const data=event.result||{};
        currentArtist=artist;
        lastReqBody=null;
        qaWarnings=data.qa_warnings||[];
        renderStoryShots(data.shots||[], artist, data.audio_analysis||null, data);
      } else if(event.type==='error'){
        hideProgress();
        showError(event.message||'Story generation failed');
      }
    },
    onError(err){hideProgress();showError(err.message||'Story generation failed');}
  });
}

// GENERATE MV (Main workflow) — uses SSE streaming endpoint, or Director API for hf-mv
function generateMV(){
  const artist=document.getElementById('artistName').value.trim()||'Artist';
  saveArtistFields(artist);
  const inputText=currentMode==='lyrics'
    ?document.getElementById('lyricsInput').value.trim()
    :document.getElementById('descInput').value.trim();
  // HF MV / multishot modes were removed — only NB2 image-only flows through here now
  const isHfMv = false;
  const isHfMultishot = false;
  if(!inputText){
    alert('Please enter lyrics or a description.');return;
  }
  // Kling 'mv' mode removed 2026-04-16 — Video tab routes to Higgsfield/Seedance.
  const mode = outputMode==='nb2'?'nb2':'hf-mv';

  // Higgsfield MV → streaming Director pipeline (audio analysis + Claude director)
  if(mode==='hf-mv'){
    const videoStyle=document.getElementById('videoStyleSelect')?.value||'hybrid';
    const stages=[];
    if(uploadedAudio) stages.push({key:'audio_analysis', label:'Audio Analyzer'});
    stages.push({key:'director', label:'Director (Claude Sonnet)'});
    showProgress(stages);
    collapseAllPanels();

    const reqBody={
      lyrics:inputText,
      videoStyle,
      platform:'16:9',
      fileUri:uploadedAudio?.fileUri||null,
      mimeType:uploadedAudio?.mimeType||null,
    };

    _cancelSSE=connectSSE(API_BASE+'/api/music-video-director-stream', reqBody, {
      onEvent:(event)=>{
        if(event.type==='stage'){
          updateProgressStage(event.key, event.status);
        } else if(event.type==='done'){
          hideProgress();
          const data=event.result||{};
          currentTreatment=data.treatment||null;
          qaWarnings=[];
          currentArtist=artist;
          lastReqBody=null;
          renderShots(data.shots||[], data.treatment||null, artist);
        } else if(event.type==='error'){
          hideProgress();
          console.error('Director error:', event.message);
          showError(event.message||'Director generation failed');
        }
      },
      onError:(err)=>{
        hideProgress();
        console.error('Director stream error:', err);
        showError(err.message||'Director generation failed');
      },
    });
    return;
  }

  // Kling / NB2 → existing SSE pipeline
  const stagesForMode = [];
  if(mode==='nb2'&&shirtBase64) stagesForMode.push({key:'shirt_reference', label:'Shirt Reference'});
  stagesForMode.push({key:'scene_architect', label:'Scene Architect'});
  stagesForMode.push({key:'stylist', label:'Stylist'});
  stagesForMode.push({key:'cinematographer', label:'Cinematographer'});
  stagesForMode.push({key:'video_director', label:'Director'});

  showProgress(stagesForMode);
  collapseAllPanels();

  const anchorBlock=imgBase64?`\n\nA reference photo is provided. The subject's face, skin tone, and hair must remain exactly consistent across all scenes. Because a reference photo is locked, set the Subject array in every image_prompt to ["subject from reference photo"] — do not describe facial features, skin tone, build, or hair. The reference image defines the subject.`:'';
  const wardrobeBlock=buildWardrobePromptBlock(loadWardrobe());
  const styleWorldBlock=buildStyleWorldPromptBlock(loadStyleWorlds());
  const locationBlock=buildLocationPromptBlock(loadLocations());
  const angleBlock=buildAngleMemoryBlock();
  const lightingBlock=buildLightingMemoryBlock();
  const influenceBlock=buildInfluenceMemoryBlock();
  const jewelryBlock=buildJewelryMemoryBlock();
  const headwearBlock=buildHeadwearMemoryBlock();

  const reqBody={
    mode,
    userInput: (currentMode==='lyrics'
      ?`Artist: ${artist}\n\nLYRICS:\n${inputText}`
      :`Artist: ${artist}\n\nSCENE DESCRIPTION:\n${inputText}`),
    anchorBlock,
    wardrobeMemory: wardrobeBlock,
    styleWorldMemory: styleWorldBlock,
    locationMemory: locationBlock,
    angleMemory: angleBlock,
    lightingMemory: lightingBlock,
    influenceMemory: influenceBlock,
    jewelryMemory: jewelryBlock,
    headwearMemory: headwearBlock,
    ...(mode==='nb2'&&shirtBase64?{shirtReferenceImage:shirtBase64}:{}),
    ...(mode==='nb2'&&currentMode==='desc'?{sceneCount:nb2SceneCount}:{}),
    ...(mode==='nb2'?{stylePreset:nb2StylePreset}:{}),
  };
  lastReqBody = reqBody;

  _cancelSSE = connectSSE(API_BASE+'/api/generate-prompts-stream', reqBody, {
    onEvent(event){
      if(event.type==='stage'){
        updateProgressStage(event.name, event.status);
      } else if(event.type==='done'){
        hideProgress();
        const data=event.result||{};
        allScenes=data.scenes||[];
        currentTreatment=data.treatment||null;
        qaWarnings=data.qa_warnings||[];
        saveWardrobe(allScenes);
        saveStyleWorlds(allScenes);
        saveLocations(allScenes);
        saveVarietyFromScenes(allScenes);
        if(data.shirt_reference && lastReqBody) lastReqBody.shirtReference=data.shirt_reference;
        currentArtist = artist;
        renderScenes(artist);
        // Render multishot generations if present
        if(data.multishot_mode && data.multishot_generations){
          renderMultishotGenerations(data.multishot_generations);
        }
      } else if(event.type==='error'){
        hideProgress();
        showError(event.message||'Generation failed');
      }
    },
    onError(err){
      hideProgress();
      console.error(err);
      showError(err.message||'Connection error');
    },
  });
}

// GENERATE 9-GRID STORY (Image Only mode)

// GENERATE FRAME PAIRS (Start & End mode)

// GENERATE START+END

// GENERATE 9-GRID

// GENERATE SEQUENTIAL

// GENERATE HF START+END

// GENERATE HF 9-GRID

// GENERATE HF SEQUENTIAL

// GENERATE FROM IMAGE

// RENDER QA WARNINGS
// RENDER STORY CHAIN SHOTS (hf-story mode)
function renderStoryShots(shots, artist, audioAnalysis, fullData){
  const editBySnum = new Map();
  (fullData?.edit_specs||[]).forEach(spec => {
    if(spec?.shot_number) editBySnum.set(spec.shot_number, spec);
  });
  // Normalize to allScenes and re-use renderShots machinery, but add story-specific fields
  const normalised = shots.map((shot, i) => {
    const isHero = shot.requires_new_hero_frame || false;
    // For continuation shots, replace the literal "extracted_from_previous_clip" start_frame
    // with a human-readable workflow note — it clutters the HF meta otherwise.
    const vp = shot.video_prompt ? { ...shot.video_prompt } : null;
    if (vp && !isHero && vp.start_frame === 'extracted_from_previous_clip') {
      vp.start_frame = ''; // hide it — the clip_chain_note below carries the instruction
    }
    return {
      ...shot,
      video_prompt: vp,
      // Fields renderShots expects
      shot_number: shot.shot_number || `S${String(i+1).padStart(2,'0')}`,
      scene_description: shot.story_beat || `Shot ${i+1}`,
      song_section: shot.song_section || '',
      is_hero_shot: isHero,
      clip_chain_note: isHero
        ? `Step 1: Generate image below in NB2  →  Step 2: Upload to Higgsfield as start frame  →  Step 3: Add video prompt`
        : `🔗 In Higgsfield: open previous clip → Extract End Frame → paste video prompt as "Continue Story"`,
      // Pass image_prompt through — new format is already { location_prompt, hero_prompt, ... }
      // Old format was a plain string; wrap it for backward compat
      image_prompt: isHero && shot.image_prompt
        ? (typeof shot.image_prompt === 'object'
            ? shot.image_prompt
            : { hero_prompt: shot.image_prompt, model: 'NB2', resolution: '4K', aspect_ratio: '16:9' })
        : null,
      carries_from: null,
      _chain_shot: !isHero,   // signals a continuation shot (no new image needed)
      _edit_spec: editBySnum.get(shot.shot_number) || null,
    };
  });
  renderShots(normalised, null, artist);
  renderEditDirectorCard(fullData);

  // Show audio analysis card if present
  if(audioAnalysis){
    const resultsEl=document.getElementById('results');
    const existing=resultsEl.querySelector('.audio-analysis-card');
    if(existing) existing.remove();
    const card=document.createElement('div');
    card.className='audio-analysis-card';
    card.innerHTML=`
      <div class="aa-header">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>
        <span>Track Analysis</span>
        ${audioAnalysis.title&&audioAnalysis.title!=='Unknown'?`<span class="aa-title">${escHtml(audioAnalysis.title)}</span>`:''}
      </div>
      <div class="aa-body">
        ${audioAnalysis.emotional_arc?`<div class="aa-row"><strong>Emotional arc:</strong> ${escHtml(audioAnalysis.emotional_arc)}</div>`:''}
        ${audioAnalysis.sonic_texture?`<div class="aa-row"><strong>Sonic texture:</strong> ${escHtml(audioAnalysis.sonic_texture)}</div>`:''}
        ${audioAnalysis.beat_drops?.length?`<div class="aa-row"><strong>Beat drops:</strong> ${audioAnalysis.beat_drops.map(escHtml).join(' · ')}</div>`:''}
        ${audioAnalysis.camera_language_suggestion?`<div class="aa-row"><strong>Camera language:</strong> ${escHtml(audioAnalysis.camera_language_suggestion)}</div>`:''}
      </div>
    `;
    resultsEl.insertBefore(card, resultsEl.firstChild);
  }
}

function renderEditDirectorCard(data){
  if(!data) return;
  const hasEditData = data.signature_moment || data.density_map?.length
    || data.energy_arc || data.effects_inventory?.length;
  if(!hasEditData) return;

  const resultsEl=document.getElementById('results');
  if(!resultsEl) return;
  const existing=resultsEl.querySelector('.edit-director-card');
  if(existing) existing.remove();

  const card=document.createElement('div');
  card.className='edit-director-card';

  let html = `
    <div class="ed-header">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3h18v18H3z"/><path d="M9 3v18M15 3v18M3 9h18M3 15h18"/></svg>
      <span>Edit Director — TikTok Cut</span>
    </div>
    <div class="ed-body">
  `;

  if(data.signature_moment){
    const sm=data.signature_moment;
    html += `
      <div class="ed-section">
        <div class="ed-label">Signature Moment — ${escHtml(sm.shot_number||'')}</div>
        ${sm.effect?`<div class="ed-row"><strong>Effect:</strong> ${escHtml(sm.effect)}</div>`:''}
        ${sm.rationale?`<div class="ed-row"><em>${escHtml(sm.rationale)}</em></div>`:''}
      </div>
    `;
  }

  if(data.density_map?.length){
    html += `<div class="ed-section"><div class="ed-label">Density Map</div>`;
    data.density_map.forEach(d=>{
      const density=(d.density||'').toUpperCase();
      const klass=density==='HIGH'?'high':density==='LOW'?'low':'med';
      html += `
        <div class="ed-density-row ${klass}">
          <span class="ed-density-pill">${escHtml(density)}</span>
          <span class="ed-density-seg">${escHtml(d.segment||'')}</span>
          ${d.effect_count?`<span class="ed-density-count">${d.effect_count} fx</span>`:''}
          ${d.notes?`<div class="ed-density-notes">${escHtml(d.notes)}</div>`:''}
        </div>
      `;
    });
    html += `</div>`;
  }

  if(data.energy_arc){
    const ea=data.energy_arc;
    html += `<div class="ed-section"><div class="ed-label">Energy Arc</div>`;
    if(ea.act_1) html += `<div class="ed-row"><strong>Act 1:</strong> ${escHtml(ea.act_1)}</div>`;
    if(ea.act_2) html += `<div class="ed-row"><strong>Act 2:</strong> ${escHtml(ea.act_2)}</div>`;
    if(ea.act_3) html += `<div class="ed-row"><strong>Act 3:</strong> ${escHtml(ea.act_3)}</div>`;
    html += `</div>`;
  }

  if(data.effects_inventory?.length){
    html += `<div class="ed-section"><div class="ed-label">Effects Inventory</div>`;
    data.effects_inventory.forEach(fx=>{
      const shots=(fx.in_shots||[]).join(', ');
      html += `
        <div class="ed-fx-row">
          <span class="ed-fx-name">${escHtml(fx.effect||'')}</span>
          ${fx.uses?`<span class="ed-fx-uses">× ${fx.uses}</span>`:''}
          ${shots?`<span class="ed-fx-shots">${escHtml(shots)}</span>`:''}
          ${fx.role?`<div class="ed-fx-role">${escHtml(fx.role)}</div>`:''}
        </div>
      `;
    });
    html += `</div>`;
  }

  html += `</div>`;
  card.innerHTML = html;
  resultsEl.insertBefore(card, resultsEl.firstChild);
}

function renderQAWarnings(){
  const el=document.getElementById('qaWarnings');
  if(!el)return;
  if(!qaWarnings||qaWarnings.length===0){el.style.display='none';el.innerHTML='';return;}
  el.style.display='';
  el.innerHTML=qaWarnings.map(w=>`<div>⚠️ Quality check: ${escHtml(w)}</div>`).join('');
}

// RENDER SCENES
function renderTreatmentCard(){
  const el=document.getElementById('treatmentCard');
  if(!currentTreatment||!currentTreatment.concept){el.innerHTML='';return;}
  const t=currentTreatment;
  let html=`<div class="treatment-card">`;
  html+=`<div class="tc-label">Director's Treatment</div>`;
  html+=`<div class="tc-concept">${escHtml(t.concept)}</div>`;
  if(t.emotional_journey){html+=`<div class="tc-concept" style="opacity:0.6;font-size:12px;">${escHtml(t.emotional_journey)}</div>`;}
  if(t.hero_shots?.length){
    html+=`<div class="tc-hero-label">Hero Shots</div>`;
    t.hero_shots.forEach(h=>{html+=`<div class="tc-hero">${escHtml(h)}</div>`;});
  }
  if(t.visual_identity?.color_palette?.length){
    html+=`<div class="tc-palette">`;
    t.visual_identity.color_palette.forEach(c=>{
      const label=typeof c==='object'?`${c.color} — ${c.meaning}`:c;
      html+=`<span class="tc-pill">${escHtml(label)}</span>`;
    });
    html+=`</div>`;
  }
  html+=`</div>`;
  el.innerHTML=html;
}

function renderScenes(artist){
  hideLoading();
  document.getElementById('results').style.display='block';
  document.getElementById('copyBar').classList.add('on');
  document.getElementById('totalScenes').textContent=allScenes.length;
  document.getElementById('trackLabel').textContent=artist||'Scenes';
  renderTreatmentCard();
  renderQAWarnings();

  const wrap=document.getElementById('scenesOut');
  wrap.innerHTML='';
  promptMap={};

  allScenes.forEach((sc,i)=>{
    const card=document.createElement('div');
    card.className='scene-card';
    card.style.setProperty('--i', i);
    card.setAttribute('data-num', String(sc.scene_number||i+1).padStart(2,'0'));

    let badges='';
    if(sc.image_prompt||sc.start_frame_prompt)badges+=`<span class="sc-badge nb2"><span class="sc-badge-dot"></span>NB2</span>`;
    if(sc.video_prompt){
      // All video prompts are Higgsfield/Seedance now (Kling removed 2026-04-16).
      badges+=`<span class="sc-badge hf"><span class="sc-badge-dot"></span>Higgsfield</span>`;
    }
    if(sc.archetype)badges+=`<span class="sc-badge seq">${escHtml(sc.archetype)}</span>`;

    let html=`
      <div class="sc-header">
        <div class="sc-num">${String(sc.scene_number||i+1).padStart(2,'0')}</div>
        <div class="sc-meta">
          <div class="sc-title">${escHtml(sc.title||'Scene')}</div>
          ${sc.lyric_ref?`<div class="sc-lyric">${escHtml(sc.lyric_ref)}</div>`:''}
          <div class="sc-badges">${badges}</div>
        </div>
        <button class="btn-regen" title="Regenerate this scene" onclick="regenerateScene(${i+1})">↺</button>
      </div>
    `;

    if(sc.director_note){
      html+=`<div class="sc-note">${escHtml(sc.director_note)}</div>`;
    }

    html+=`<div class="sc-divider"></div>`;

    if(sc.image_prompt){
      const kImg=`s${i}_img`;
      const kImgJson=`s${i}_img_json`;
      const imgObj=typeof sc.image_prompt==='object'?sc.image_prompt:null;
      const imgJson=imgObj?JSON.stringify(imgObj,null,2):(sc.image_prompt||'');
      const flatStr=imgObj?flattenImagePrompt(imgObj):(sc.image_prompt||'');
      promptMap[kImg]=flatStr;
      promptMap[kImgJson]=imgJson;
      const labelPreview=(imgObj&&imgObj.label)?imgObj.label:(flatStr.slice(0,90)+'…');
      html+=`
        <div class="sc-prompt img-block">
          <div class="sc-prompt-header">
            <div class="sc-prompt-label">
              <div class="sc-prompt-dot"></div>
              <span class="sc-prompt-name">Image Prompt</span>
              <span class="sc-prompt-tool">· NB2</span>
            </div>
            <div style="display:flex;gap:6px;align-items:center;">
              <button class="btn-toggle-json" onclick="toggleImgPrompt(this)">▸ Expand</button>
              <button class="btn-copy" onclick="copyPrompt(this,'${kImgJson}')">+ JSON</button>
              <button class="btn-copy" onclick="copyPrompt(this,'${kImg}')">Copy</button>
            </div>
          </div>
          <div class="sc-prompt-preview" onclick="toggleImgPrompt(this.closest('.sc-prompt').querySelector('.btn-toggle-json'))">${escHtml(labelPreview)}</div>
          <pre class="sc-prompt-text sc-collapsed">${escHtml(flatStr)}</pre>
        </div>
      `;
    }

    if(sc.start_frame_prompt){
      const kSt=`s${i}_start`,kEn=`s${i}_end`;
      promptMap[kSt]=sc.start_frame_prompt;
      promptMap[kEn]=sc.end_frame_prompt||'';
      html+=`
        <div class="sc-prompt img-block">
          <div class="sc-prompt-header">
            <div class="sc-prompt-label">
              <div class="sc-prompt-dot"></div>
              <span class="sc-prompt-name">Frame Pair</span>
              <span class="sc-prompt-tool">· Kling Start+End</span>
            </div>
          </div>
          <div class="frames-pair">
            <div>
              <div class="frame-panel-label">Start Frame</div>
              <div class="sc-prompt-text">${escHtml(sc.start_frame_prompt)}</div>
              <button class="btn-copy" style="margin-top:8px;" onclick="copyPrompt(this,'${kSt}')">Copy</button>
            </div>
            <div>
              <div class="frame-panel-label">End Frame</div>
              <div class="sc-prompt-text">${escHtml(sc.end_frame_prompt||'')}</div>
              <button class="btn-copy" style="margin-top:8px;" onclick="copyPrompt(this,'${kEn}')">Copy</button>
            </div>
          </div>
        </div>
      `;
    }

    if(sc.video_prompt){
      const kVid=`s${i}_vid`;promptMap[kVid]=sc.video_prompt;
      const isHf=!!sc.hf_camera_movement;
      const formattedVid=isHf?escHtml(sc.video_prompt):formatKlingPrompt(sc.video_prompt);
      const toolLabel=isHf?'· Higgsfield Cinema Studio':'· Kling 3.0';
      const copyClass=isHf?'btn-copy':'btn-copy teal';
      let hfMeta='';
      if(isHf){
        const items=[];
        if(sc.hf_camera_movement) items.push(`<strong>Camera:</strong> ${escHtml(sc.hf_camera_movement)}`);
        if(sc.hf_genre) items.push(`<strong>Genre:</strong> ${escHtml(sc.hf_genre)}`);
        if(sc.hf_duration) items.push(`<strong>Duration:</strong> ${escHtml(sc.hf_duration)}`);
        if(sc.hf_emotions) items.push(`<strong>Emotions:</strong> ${escHtml(sc.hf_emotions)}`);
        if(sc.hf_start_frame) items.push(`<strong>Start:</strong> ${escHtml(sc.hf_start_frame)}`);
        if(sc.hf_end_frame) items.push(`<strong>End:</strong> ${escHtml(sc.hf_end_frame)}`);
        hfMeta=`<div class="hf-meta">${items.map(t=>`<span class="hf-meta-item">${t}</span>`).join('')}</div>`;
      }
      html+=`
        <div class="sc-prompt vid-block">
          <div class="sc-prompt-header">
            <div class="sc-prompt-label">
              <div class="sc-prompt-dot"></div>
              <span class="sc-prompt-name">Video Prompt</span>
              <span class="sc-prompt-tool">${toolLabel}</span>
            </div>
            <button class="${copyClass}" onclick="copyPrompt(this,'${kVid}')">Copy</button>
          </div>
          <div class="sc-prompt-text">${formattedVid}</div>
          ${hfMeta}
        </div>
      `;
    }

    card.innerHTML=html;
    wrap.appendChild(card);
  });

  updateCopyBtns();
}

// RENDER MULTISHOT GENERATIONS (from hf-multishot pipeline)

// RENDER DIRECTOR SHOTS (from /api/music-video-director)
function renderShots(shots, treatment, artist){
  hideLoading();
  // Normalize shots → allScenes format for compatibility (Generate All Images, etc.)
  // Enforce clip-chain: start_frame[i] must equal end_frame[i-1]
  // Do this before normalisation so the source data is consistent
  for (let i = 1; i < shots.length; i++) {
    const prevEnd = shots[i-1].video_prompt?.end_frame;
    if (prevEnd && shots[i].video_prompt) {
      shots[i].video_prompt.start_frame = prevEnd;
    }
  }

  allScenes = shots.map((shot,i)=>({
    scene_number: parseInt((shot.shot_number||'').replace(/\D/g,''))||i+1,
    title: shot.scene_description||`Shot ${i+1}`,
    lyric_ref: shot.song_section||'',
    director_note: shot.clip_chain_note||'',
    _is_hero: shot.is_hero_shot||false,
    _chain_shot: shot._chain_shot||false,
    _shot_num: shot.shot_number||`S${String(i+1).padStart(2,'0')}`,
    _carries_from: shot.carries_from||null,
    image_prompt: shot.image_prompt||null,
    _location_prompt: shot.image_prompt?.location_prompt||null,
    _flat_prompt: shot.image_prompt?.hero_prompt||shot.image_prompt?.prompt||null,
    video_prompt: shot.video_prompt?.full_prompt||'',
    hf_camera_movement: shot.video_prompt?.camera||'',
    hf_genre: shot.video_prompt?.genre||'',
    hf_duration: shot.video_prompt?.duration||'',
    hf_emotions: shot.video_prompt?.emotions||'',
    hf_start_frame: shot.video_prompt?.start_frame||'',
    hf_end_frame: shot.video_prompt?.end_frame||'',
  }));

  document.getElementById('results').style.display='block';
  document.getElementById('copyBar').classList.add('on');
  document.getElementById('totalScenes').textContent=allScenes.length;
  document.getElementById('trackLabel').textContent=artist||'Shots';
  renderTreatmentCard();
  renderQAWarnings();


  const wrap=document.getElementById('scenesOut');
  wrap.innerHTML='';
  promptMap={};

  allScenes.forEach((sc,i)=>{
    const card=document.createElement('div');
    card.className='scene-card';
    card.style.setProperty('--i', i);

    const heroBadge=sc._is_hero?`<span class="sc-hero-badge">HERO FRAME</span>`:sc._chain_shot?`<span class="sc-chain-badge">CHAIN</span>`:'';
    const shotNumHtml=`<span class="sc-shot-num">${escHtml(sc._shot_num||String(sc.scene_number).padStart(2,'0'))}</span>${heroBadge}`;

    let html=`
      <div class="sc-header">
        <div class="sc-num">${shotNumHtml}</div>
        <div class="sc-meta">
          <div class="sc-title">${escHtml(sc.title)}</div>
          ${sc.lyric_ref?`<div class="sc-lyric">${escHtml(sc.lyric_ref)}</div>`:''}
          <div class="sc-badges">
            <span class="sc-badge nb2"><span class="sc-badge-dot"></span>NB2</span>
            <span class="sc-badge hf"><span class="sc-badge-dot"></span>Higgsfield</span>
          </div>
        </div>
      </div>
    `;

    html+=`<div class="sc-divider"></div>`;

    // Location prompt block (environment-only, no character — generate before hero frame)
    if(sc._location_prompt){
      const kLoc=`s${i}_loc`;
      promptMap[kLoc]=sc._location_prompt;
      const locPreview=sc._location_prompt.slice(0,90)+'…';
      html+=`
        <div class="sc-prompt img-block" style="border-left-color:rgba(80,180,140,0.5);">
          <div class="sc-prompt-header">
            <div class="sc-prompt-label">
              <div class="sc-prompt-dot" style="background:rgba(80,180,140,0.8);"></div>
              <span class="sc-prompt-name">Location Prompt</span>
              <span class="sc-prompt-tool">· NB2 · Step 1 — environment only, no character</span>
            </div>
            <div style="display:flex;gap:6px;align-items:center;">
              <button class="btn-toggle-json" onclick="toggleImgPrompt(this)">▸ Expand</button>
              <button class="btn-copy" onclick="copyPrompt(this,'${kLoc}')">Copy</button>
            </div>
          </div>
          <div class="sc-prompt-preview" onclick="toggleImgPrompt(this.closest('.sc-prompt').querySelector('.btn-toggle-json'))">${escHtml(locPreview)}</div>
          <pre class="sc-prompt-text sc-collapsed">${escHtml(sc._location_prompt)}</pre>
        </div>
      `;
    }

    // Image prompt block (hero frame — character composited into location)
    if(sc._flat_prompt||sc.image_prompt){
      const kImg=`s${i}_img`;
      const kImgJson=`s${i}_img_json`;
      const flatStr=sc._flat_prompt||'';
      const fullJson=sc.image_prompt?JSON.stringify(sc.image_prompt,null,2):'';
      promptMap[kImg]=flatStr;
      promptMap[kImgJson]=fullJson;
      const preview=flatStr.slice(0,90)+'…';
      const heroLabel=sc._location_prompt?'Hero Frame Prompt':'Image Prompt';
      const heroNote=sc._location_prompt?'· NB2 · Step 2 — composite character into location':'· NB2';
      html+=`
        <div class="sc-prompt img-block">
          <div class="sc-prompt-header">
            <div class="sc-prompt-label">
              <div class="sc-prompt-dot"></div>
              <span class="sc-prompt-name">${heroLabel}</span>
              <span class="sc-prompt-tool">${heroNote}</span>
            </div>
            <div style="display:flex;gap:6px;align-items:center;">
              <button class="btn-toggle-json" onclick="toggleImgPrompt(this)">▸ JSON</button>
              <button class="btn-copy" onclick="copyPrompt(this,'${kImgJson}')">+ JSON</button>
              <button class="btn-copy" onclick="copyPrompt(this,'${kImg}')">Copy</button>
            </div>
          </div>
          <div class="sc-prompt-preview" onclick="toggleImgPrompt(this.closest('.sc-prompt').querySelector('.btn-toggle-json'))">${escHtml(preview)}</div>
          <pre class="sc-prompt-text sc-collapsed">${escHtml(flatStr)}</pre>
        </div>
      `;
    }

    // Video prompt block
    if(sc.video_prompt){
      const kVid=`s${i}_vid`;promptMap[kVid]=sc.video_prompt;
      const items=[];
      if(sc.hf_camera_movement) items.push(`<strong>Camera:</strong> ${escHtml(sc.hf_camera_movement)}`);
      if(sc.hf_genre) items.push(`<strong>Genre:</strong> ${escHtml(sc.hf_genre)}`);
      if(sc.hf_duration) items.push(`<strong>Duration:</strong> ${escHtml(sc.hf_duration)}`);
      if(sc.hf_emotions) items.push(`<strong>Emotions:</strong> ${escHtml(sc.hf_emotions)}`);
      if(sc.hf_start_frame) items.push(`<strong>Start:</strong> ${escHtml(sc.hf_start_frame)}`);
      if(sc.hf_end_frame) items.push(`<strong>End:</strong> ${escHtml(sc.hf_end_frame)}`);
      const hfMeta=items.length?`<div class="hf-meta">${items.map(t=>`<span class="hf-meta-item">${t}</span>`).join('')}</div>`:'';
      html+=`
        <div class="sc-prompt vid-block">
          <div class="sc-prompt-header">
            <div class="sc-prompt-label">
              <div class="sc-prompt-dot"></div>
              <span class="sc-prompt-name">Video Prompt</span>
              <span class="sc-prompt-tool">· Higgsfield Cinema Studio</span>
            </div>
            <button class="btn-copy" onclick="copyPrompt(this,'${kVid}')">Copy</button>
          </div>
          <div class="sc-prompt-text">${escHtml(sc.video_prompt)}</div>
          ${hfMeta}
        </div>
      `;
    }

    // Clip chain note
    if(sc.director_note){
      html+=`<div class="sc-clip-chain">↳ ${escHtml(sc.director_note)}</div>`;
    }

    card.innerHTML=html;
    wrap.appendChild(card);
  });

  updateCopyBtns();
}


async function regenerateScene(sceneIndex){
  if(!lastReqBody){
    alert('No generation context found. Please generate scenes first.');
    return;
  }
  const idx=sceneIndex-1; // 0-based index into allScenes
  const scenesWrap=document.getElementById('scenesOut');
  const cards=scenesWrap.querySelectorAll('.scene-card');
  const card=cards[idx];
  if(!card){return;}

  const btn=card.querySelector('.btn-regen');
  card.classList.add('scene-card--regenerating');
  if(btn){btn.disabled=true;}

  try{
    const body={
      mode: lastReqBody.mode,
      sceneIndex,
      sceneCount: allScenes.length,
      userInput: lastReqBody.userInput,
      anchorBlock: lastReqBody.anchorBlock||'',
      wardrobeMemory: lastReqBody.wardrobeMemory||'',
      styleWorldMemory: lastReqBody.styleWorldMemory||'',
      locationMemory: lastReqBody.locationMemory||'',
      angleMemory: lastReqBody.angleMemory||'',
      lightingMemory: lastReqBody.lightingMemory||'',
      influenceMemory: lastReqBody.influenceMemory||'',
      jewelryMemory: lastReqBody.jewelryMemory||'',
      headwearMemory: lastReqBody.headwearMemory||'',
      shirtReference: lastReqBody.shirtReference||'',
      ...(lastReqBody.stylePreset?{stylePreset:lastReqBody.stylePreset}:{}),
    };
    const resp=await fetch(API_BASE+'/api/regenerate-scene',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify(body),
    });
    const data=await resp.json();
    if(!resp.ok||data.error){throw new Error(data.error||`API error: ${resp.status}`);}

    // Preserve scene_number if the pipeline returned scene_number=1
    const newScene={...data.scene, scene_number: sceneIndex};
    allScenes[idx]=newScene;

    // Re-render just this card by re-rendering all scenes (preserves order, fast enough)
    renderScenes(currentArtist);
  }catch(err){
    console.error('Regenerate scene error:',err);
    // Show inline error on card
    card.classList.remove('scene-card--regenerating');
    if(btn){btn.disabled=false;}
    const errDiv=document.createElement('div');
    errDiv.style.cssText='padding:8px 22px;font-size:10px;color:var(--red);';
    errDiv.textContent='Regeneration failed: '+err.message;
    card.appendChild(errDiv);
    setTimeout(()=>errDiv.remove(),5000);
    return;
  }
  // No need to restore card state — renderScenes rebuilt it
}

function copyPrompt(btn, key){
  navigator.clipboard.writeText(promptMap[key]||'').then(()=>{
    btn.textContent='Copied!';
    btn.classList.add('copied');
    setTimeout(()=>{btn.textContent='Copy';btn.classList.remove('copied');},1500);
  });
}

function copyAllPrompts(btnId, label, getter){
  const parts=[];
  allScenes.forEach((s,i)=>{
    const items=getter(s);
    items.forEach(({suffix,text})=>{
      if(text) parts.push(`--- Scene ${i+1}: ${s.title||''}${suffix} ---\n${text}`);
    });
  });
  navigator.clipboard.writeText(parts.join('\n\n')).then(()=>{
    const btn=document.getElementById(btnId);
    btn.textContent='Copied!';
    setTimeout(()=>{btn.textContent=label;},1500);
  });
}

function copyAllImg(){
  copyAllPrompts('copyImgBtn','Copy All Images',s=>[
    {suffix:'',          text:typeof s.image_prompt==='object'?JSON.stringify(s.image_prompt,null,2):s.image_prompt},
    {suffix:' [Start]',  text:s.start_frame_prompt},
    {suffix:' [End]',    text:s.end_frame_prompt},
  ]);
}

function copyAllVid(){
  copyAllPrompts('copyVidBtn','Copy All Videos',s=>[
    {suffix:'',text:s.video_prompt},
  ]);
}

function resetAll(){
  // Clear state
  imgBase64=null;shirtBase64=null;allScenes=[];currentTreatment=null;qaWarnings=[];promptMap={};

  // Clear all "fresh-mode" variety memory so the next generation has zero
  // anti-repeat constraints (lets the user start over from a clean slate).
  // Wardrobe and style-world memory are preserved intentionally — they're
  // accumulated session memory for outfit/world variety across runs.
  clearLocations();
  clearAngles();
  clearLighting();
  clearInfluences();
  clearJewelry();
  clearHeadwear();

  // Clear UI
  clearImg('main');
  clearImg('shirt');
  loadVawnReference();
  document.getElementById('lyricsInput').value='';
  const descEl=document.getElementById('descInput');if(descEl)descEl.value='';
  document.getElementById('hfExtras')?.classList.remove('visible');

  // Reset views
  document.getElementById('results').style.display='none';
  document.getElementById('copyBar').classList.remove('on');
  document.getElementById('scenesOut').innerHTML='';
  document.getElementById('treatmentCard').innerHTML='';
  const qaEl=document.getElementById('qaWarnings');if(qaEl){qaEl.style.display='none';qaEl.innerHTML='';}
  document.getElementById('emptyState').style.display='flex';
  document.getElementById('emptyState').innerHTML=`<div class="empty-title">START CREATING WITH<br><span>Apulu Generation</span></div><div class="empty-sub" id="emptyTxt">Upload a photo · Paste lyrics · Hit Generate</div>`;

  // Reset modes
  setOutputMode('both');
  setMode('lyrics');
  setHfMode('story');
  updateGenBtn();
}

// Initialize
setOutputMode(outputMode);
setHfMode(hfMode);
updatePanels();
updateInputArea();
updateGenBtn();
updateWardrobeCountLabel();
updateStyleWorldLabel();
loadArtistFields();
if (typeof initStudio === 'function') initStudio();
if (typeof initCreate === 'function') initCreate();

function toggleImgPrompt(btn){
  const block=btn.closest('.sc-prompt');
  const pre=block.querySelector('.sc-prompt-text');
  const preview=block.querySelector('.sc-prompt-preview');
  const collapsed=pre.classList.contains('sc-collapsed');
  if(collapsed){
    pre.classList.remove('sc-collapsed');
    btn.textContent='▾ JSON';
    btn.classList.add('open');
    if(preview)preview.style.display='none';
  }else{
    pre.classList.add('sc-collapsed');
    btn.textContent='▸ JSON';
    btn.classList.remove('open');
    if(preview)preview.style.display='';
  }
}

async function generateImage(btn,sceneKey){
  const idx=parseInt(sceneKey.slice(1));
  const sc=allScenes[idx];
  if(!sc||!sc.image_prompt){alert('No image prompt for this scene.');return;}
  btn.textContent='Generating…';
  btn.disabled=true;
  const resultEl=document.getElementById(`genImg_${sceneKey}`);
  resultEl.innerHTML='';
  try{
    const resp=await fetch(API_BASE+'/api/generate-image',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({image_prompt:sc.image_prompt,reference_image:imgBase64||null,shirt_reference_image:shirtBase64||null}),
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

async function generateImageShot(btn,sceneKey){
  const idx=parseInt(sceneKey.slice(1));
  const sc=allScenes[idx];
  if(!sc||!sc._flat_prompt){alert('No image prompt for this shot.');return;}
  btn.textContent='Generating…';
  btn.disabled=true;
  const resultEl=document.getElementById(`genImg_${sceneKey}`);
  resultEl.innerHTML='';
  try{
    const resp=await fetch(API_BASE+'/api/generate-image',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({flat_prompt:sc._flat_prompt,reference_image:imgBase64||null,shirt_reference_image:shirtBase64||null}),
    });
    const data=await resp.json();
    if(!resp.ok||data.error)throw new Error(data.error||`Error ${resp.status}`);
    const src=`data:${data.mimeType};base64,${data.image}`;
    resultEl.innerHTML=`
      <img src="${src}" alt="Generated shot"/>
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

async function generateLocationShot(btn,sceneKey){
  const idx=parseInt(sceneKey.slice(1));
  const sc=allScenes[idx];
  if(!sc||!sc._location_prompt){alert('No location prompt for this shot.');return;}
  btn.textContent='Generating…';
  btn.disabled=true;
  const resultEl=document.getElementById(`genLocImg_${sceneKey}`);
  resultEl.innerHTML='';
  try{
    const resp=await fetch(API_BASE+'/api/generate-image',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({flat_prompt:sc._location_prompt,reference_image:null}),
    });
    const data=await resp.json();
    if(!resp.ok||data.error)throw new Error(data.error||`Error ${resp.status}`);
    const src=`data:${data.mimeType};base64,${data.image}`;
    resultEl.innerHTML=`
      <img src="${src}" alt="Generated location"/>
      <div class="gen-img-actions">
        <button class="btn-gen-action" onclick="downloadGenLocImg('${sceneKey}')">Download</button>
      </div>
    `;
    resultEl.dataset.b64=data.image;
    resultEl.dataset.mime=data.mimeType;
  }catch(err){
    resultEl.innerHTML=`<div style="color:rgba(224,100,88,0.8);font-size:11px;margin-top:6px;">${escHtml(err.message)}</div>`;
  }finally{
    btn.textContent='Generate Location';
    btn.disabled=false;
  }
}

function downloadGenLocImg(sceneKey){
  const el=document.getElementById(`genLocImg_${sceneKey}`);
  const b64=el?.dataset.b64;
  const mime=el?.dataset.mime||'image/png';
  if(!b64)return;
  const a=document.createElement('a');
  a.href=`data:${mime};base64,${b64}`;
  a.download=`location_${sceneKey}.png`;
  a.click();
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

// Batch image generation
let _batchCancelled = false;

function cancelBatchGeneration(){
  _batchCancelled = true;
}

async function generateAllImages(){
  const scenes = allScenes.filter(s=>s.image_prompt||s._flat_prompt);
  if(!scenes.length){ alert('No scenes with image prompts.'); return; }

  _batchCancelled = false;
  const total = scenes.length;
  const genAllBtn = document.getElementById('genAllBtn');
  const cancelBatchBtn = document.getElementById('cancelBatchBtn');
  const batchProgress = document.getElementById('batchProgress');

  genAllBtn.disabled = true;
  cancelBatchBtn.classList.add('visible');
  batchProgress.classList.add('visible');
  batchProgress.textContent = `Generating images 0/${total}…`;

  let completed = 0;
  let processed = 0;
  for(let i=0; i<allScenes.length; i++){
    if(_batchCancelled) break;
    const sc = allScenes[i];
    if(!sc || (!sc.image_prompt && !sc._flat_prompt)) continue;

    const sceneKey = `s${i}`;
    const resultEl = document.getElementById(`genImg_${sceneKey}`);
    // Support both regular scenes and director shots
    const isDirectorShot = !!sc._flat_prompt;
    const perBtn = isDirectorShot
      ? document.querySelector(`[onclick="generateImageShot(this,'${sceneKey}')"]`)
      : document.querySelector(`[onclick="generateImage(this,'${sceneKey}')"]`);

    if(perBtn){ perBtn.textContent='Generating…'; perBtn.disabled=true; }
    if(resultEl) resultEl.innerHTML='';

    try{
      const reqPayload = isDirectorShot
        ? {flat_prompt:sc._flat_prompt, reference_image:imgBase64||null, shirt_reference_image:shirtBase64||null}
        : {image_prompt:sc.image_prompt, reference_image:imgBase64||null, shirt_reference_image:shirtBase64||null};
      const resp = await fetch(API_BASE+'/api/generate-image',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify(reqPayload),
      });
      const data = await resp.json();
      if(!resp.ok||data.error) throw new Error(data.error||`Error ${resp.status}`);
      const src = `data:${data.mimeType};base64,${data.image}`;
      if(resultEl){
        resultEl.innerHTML=`
          <img src="${src}" alt="Generated scene"/>
          <div class="gen-img-actions">
            <button class="btn-gen-action" onclick="downloadGenImg('${sceneKey}')">Download</button>
            <button class="btn-gen-action" onclick="setGenImgAsRef('${sceneKey}')">Set as Reference</button>
          </div>
        `;
        resultEl.dataset.b64=data.image;
        resultEl.dataset.mime=data.mimeType;
      }
      completed++;
    }catch(err){
      console.error(`Batch image gen failed for scene ${i+1}:`, err);
      if(resultEl) resultEl.innerHTML=`<div style="color:rgba(224,100,88,0.8);font-size:11px;margin-top:6px;">${escHtml(err.message)}</div>`;
    }finally{
      if(perBtn){ perBtn.textContent='Generate Image'; perBtn.disabled=false; }
    }

    ++processed;
    batchProgress.textContent = _batchCancelled
      ? `Cancelled (${completed}/${total} done)`
      : `Generating images ${processed}/${total}…`;
  }

  // Restore button state
  genAllBtn.disabled = false;
  cancelBatchBtn.classList.remove('visible');
  if(!_batchCancelled){
    batchProgress.textContent = `Done — ${completed}/${total} images generated`;
    setTimeout(()=>{ batchProgress.classList.remove('visible'); batchProgress.textContent=''; }, 3000);
  } else {
    // cancelled — hide progress after a brief delay
    setTimeout(()=>{
      batchProgress.classList.remove('visible');
      cancelBatchBtn.classList.remove('visible');
    }, 2000);
  }
}

// Auto-load Vawn reference image for character consistency.
// Paints to BOTH the legacy imgZone (still used by code paths that
// read `imgBase64`) AND the new Create-view face zone so the locked
// reference is visible in the redesigned UI.
async function loadVawnReference(){
  try{
    const resp=await fetch('vawn-reference.jpg');
    if(!resp.ok) throw new Error('not found');
    const blob=await resp.blob();
    const reader=new FileReader();
    reader.onload=function(e){
      const url=e.target.result;
      const b64=url.split(',')[1];

      // Legacy globals + zone (kept for compatibility)
      imgBase64=b64;
      const legacyImg = document.getElementById('imgPreview');
      const legacyZone = document.getElementById('imgZone');
      if (legacyImg)  legacyImg.src = url;
      if (legacyZone) legacyZone.classList.add('filled');

      // New Create-view face zone
      if (typeof window.createSetRef === 'function') {
        window.createSetRef('face', b64);
      }
    };
    reader.readAsDataURL(blob);
  }catch(err){
    console.warn('Could not auto-load Vawn reference image:',err);
  }
}
loadVawnReference();
