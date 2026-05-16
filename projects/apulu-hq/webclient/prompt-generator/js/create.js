/* ── Apulu Studio — Create Prompt Workspace (Phase 1) ── */
(function () {
  'use strict';

  const STORAGE_KEY = 'apulu_create_state';
  const REFS_KEY    = 'apulu_create_refs';

  let activeSource    = 'lyrics';
  let activeMode      = 'image';        // 'image' | 'video' | 'both' — driven by header tab
  let isGenerating    = false;
  let lastOutput      = null;           // single result OR { image, video } for both mode
  let lastRequest     = null;
  let abortCtrl       = null;
  let referenceImage  = null;
  let wardrobeImage   = null;

  /* ── State persistence ── */
  function saveState() {
    try {
      const state = {
        source: activeSource,
        mode:   activeMode,
        songTitle:   gv('createSongTitle'),
        artistName:  gv('createArtistName'),
        lyrics:      gv('createLyrics'),
        description: gv('createDescription'),
        blank:       gv('createBlank'),
        focus:       gv('createFocus'),
        lastOutput,
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (_) {}
  }

  function saveRefs() {
    try {
      localStorage.setItem(REFS_KEY, JSON.stringify({
        face:     referenceImage,
        wardrobe: wardrobeImage,
      }));
    } catch (_) {}
  }

  function restoreRefs() {
    try {
      const raw = localStorage.getItem(REFS_KEY);
      if (!raw) return;
      const r = JSON.parse(raw);
      if (r.face)     { referenceImage = r.face;     paintRef('face',     r.face); }
      if (r.wardrobe) { wardrobeImage  = r.wardrobe; paintRef('wardrobe', r.wardrobe); }
    } catch (_) {}
  }

  function restoreState() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return;
      const s = JSON.parse(raw);
      if (s.source) setSource(s.source, true);
      sv('createSongTitle',  s.songTitle);
      sv('createArtistName', s.artistName);
      sv('createLyrics',     s.lyrics);
      sv('createDescription',s.description);
      sv('createBlank',      s.blank);
      sv('createFocus',      s.focus);
      if (s.mode) activeMode = s.mode;
      if (s.lastOutput) {
        lastOutput = s.lastOutput;
        renderOutput(lastOutput);
      }
      updateModeLabel();
    } catch (_) {}
  }

  /* ── Reference image handlers ── */
  function paintRef(slot, b64) {
    const zoneId = slot === 'face' ? 'createFaceZone' : 'createWardrobeZone';
    const imgId  = slot === 'face' ? 'createFaceImg'  : 'createWardrobeImg';
    const zone   = document.getElementById(zoneId);
    const img    = document.getElementById(imgId);
    if (!zone) {
      console.warn('[create] paintRef: zone not found for slot', slot);
      return;
    }
    if (b64) {
      const dataUrl = 'data:image/jpeg;base64,' + b64;
      zone.style.backgroundImage = "url('" + dataUrl + "')";
      if (img) {
        img.src = dataUrl;
        img.style.display = 'block';
      }
      zone.classList.add('is-filled');
    } else {
      zone.style.backgroundImage = '';
      if (img) {
        img.removeAttribute('src');
        img.style.display = 'none';
      }
      zone.classList.remove('is-filled');
    }
  }

  function compressImage(file, cb) {
    const MAX = 4 * 1024 * 1024, DIM = 1568;
    const reader = new FileReader();
    reader.onload = ev => {
      const img = new Image();
      img.onload = () => {
        let w = img.width, h = img.height;
        if (w > DIM || h > DIM) {
          const r = Math.min(DIM / w, DIM / h);
          w = Math.round(w * r); h = Math.round(h * r);
        }
        const c = document.createElement('canvas');
        c.width = w; c.height = h;
        c.getContext('2d').drawImage(img, 0, 0, w, h);
        let q = 0.88, url = c.toDataURL('image/jpeg', q);
        while (url.length * 0.75 > MAX && q > 0.3) {
          q -= 0.08;
          url = c.toDataURL('image/jpeg', q);
        }
        cb(url.split(',')[1]);
      };
      img.src = ev.target.result;
    };
    reader.readAsDataURL(file);
  }

  function handleRef(e, slot) {
    const file = e.target.files && e.target.files[0];
    if (!file) return;
    compressImage(file, b64 => {
      if (slot === 'face')     referenceImage = b64;
      if (slot === 'wardrobe') wardrobeImage  = b64;
      paintRef(slot, b64);
      saveRefs();
    });
    e.target.value = '';
  }

  /* Programmatic setter — used by app.js auto-loader to push the
     bundled Vawn reference into the Create view's face slot. */
  function setRef(slot, b64) {
    if (!b64) { clearRef(slot); return; }
    if (slot === 'face')     referenceImage = b64;
    if (slot === 'wardrobe') wardrobeImage  = b64;
    paintRef(slot, b64);
    saveRefs();
  }

  function clearRef(slot) {
    if (slot === 'face')     referenceImage = null;
    if (slot === 'wardrobe') wardrobeImage  = null;
    paintRef(slot, null);
    saveRefs();
  }

  function gv(id) { const el = document.getElementById(id); return el ? (el.value || '') : ''; }
  function sv(id, v) { const el = document.getElementById(id); if (el && v != null) el.value = v; }

  /* ── Source switching ── */
  function setSource(source, skipFocus) {
    activeSource = source;
    document.querySelectorAll('.create-source-tab').forEach(t => {
      t.classList.toggle('is-active', t.dataset.source === source);
    });
    document.querySelectorAll('.create-input-pane').forEach(p => {
      p.hidden = p.dataset.pane !== source;
    });
    if (!skipFocus) {
      const visiblePane = document.querySelector('.create-input-pane[data-pane="' + source + '"]');
      const firstInput  = visiblePane && visiblePane.querySelector('textarea, input');
      if (firstInput) setTimeout(() => firstInput.focus(), 0);
    }
    saveState();
  }

  /* ── Source text resolver ── */
  function resolveSourceText() {
    switch (activeSource) {
      case 'lyrics':      return gv('createLyrics');
      case 'description': return gv('createDescription');
      case 'blank':       return gv('createBlank');
      default:            return '';
    }
  }

  /* ── Mode label ── */
  function updateModeLabel() {
    const el = document.getElementById('createModeLabel');
    if (!el) return;
    const labels = { image: 'Image Prompt', video: 'Video Prompt', both: 'Image + Video Prompts' };
    el.textContent = labels[activeMode] || 'Image Prompt';
  }

  /* ── Generate ── */
  async function generate() {
    if (isGenerating) return;

    const sourceText = resolveSourceText();
    if (activeSource !== 'blank' && !sourceText.trim()) {
      flashError('Add some ' + activeSource + ' content first.');
      return;
    }

    const baseReq = {
      sourceType:     activeSource,
      sourceText:     sourceText.trim(),
      songTitle:      gv('createSongTitle'),
      artistName:     gv('createArtistName'),
      focus:          gv('createFocus'),
      referenceImage: referenceImage,
      wardrobeImage:  wardrobeImage,
    };
    lastRequest = baseReq;

    isGenerating = true;
    setBusy(true);
    abortCtrl = new AbortController();

    const apiBase = window.APULU_PROMPT_API_BASE || '/api/prompt-generator';

    try {
      if (activeMode === 'both') {
        showSkeleton('both');
        const [imgRes, vidRes] = await Promise.all([
          fetchPrompt(apiBase, { ...baseReq, outputType: 'image' }),
          fetchPrompt(apiBase, { ...baseReq, outputType: 'video' }),
        ]);
        lastOutput = { image: imgRes, video: vidRes };
      } else {
        showSkeleton(activeMode);
        const data = await fetchPrompt(apiBase, { ...baseReq, outputType: activeMode });
        lastOutput = data;
      }
      renderOutput(lastOutput);
      saveState();
    } catch (err) {
      if (err.name === 'AbortError') return;
      flashError(err.message || 'Generation failed');
      renderOutput(lastOutput);
    } finally {
      isGenerating = false;
      setBusy(false);
      abortCtrl = null;
    }
  }

  async function fetchPrompt(apiBase, body) {
    const resp = await fetch(apiBase + '/prompt/single', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(body),
      signal:  abortCtrl ? abortCtrl.signal : undefined,
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.error || 'Generation failed');
    return data;
  }

  function setBusy(busy) {
    const btn = document.getElementById('createGenerateBtn');
    if (btn) {
      btn.disabled = busy;
      const labelEl = btn.querySelector('span');
      if (labelEl) labelEl.textContent = busy ? 'Generating…' : 'Generate Prompt';
    }
  }

  /* ── Render ── */
  function showSkeleton(mode) {
    const empty = document.getElementById('createOutputEmpty');
    const cards = document.getElementById('createOutputCards');
    const sub   = document.getElementById('createOutputSub');
    if (empty) empty.style.display = 'none';
    if (sub)   sub.textContent     = mode === 'both'
      ? 'Generating image + video prompts…'
      : 'Generating your prompt…';
    if (!cards) return;
    cards.hidden = false;

    const sections = mode === 'both' ? ['IMAGE PROMPT', 'VIDEO PROMPT'] : ['PROMPT'];
    cards.innerHTML = sections.map(label => skelBlock(label)).join('');
  }

  function skelBlock(label) {
    return '<div class="create-out-card is-primary create-out-skel">'
      + '<div class="create-out-head"><span class="create-out-label">' + label + '</span></div>'
      + '<div class="create-out-skel-body">'
      +   '<div class="create-skel-line"></div>'
      +   '<div class="create-skel-line"></div>'
      +   '<div class="create-skel-line" style="width:88%"></div>'
      +   '<div class="create-skel-line" style="width:62%"></div>'
      + '</div></div>';
  }

  function renderOutput(data) {
    const empty   = document.getElementById('createOutputEmpty');
    const cards   = document.getElementById('createOutputCards');
    const sub     = document.getElementById('createOutputSub');
    const copyAll = document.getElementById('createCopyAllBtn');
    const regen   = document.getElementById('createRegenBtn');

    if (!data) {
      if (empty) empty.style.display = '';
      if (cards) { cards.hidden = true; cards.innerHTML = ''; }
      if (sub)   sub.textContent     = 'Your generated prompt will appear here.';
      if (copyAll) copyAll.style.display = 'none';
      if (regen)   regen.style.display   = 'none';
      return;
    }

    if (empty)   empty.style.display = 'none';
    if (copyAll) { copyAll.style.display = ''; copyAll.textContent = 'Copy all'; }
    if (regen)   regen.style.display   = '';
    if (!cards) return;

    /* Both mode: render two prompt blocks */
    const isBoth = data && data.image && data.video;
    if (isBoth) {
      if (sub) sub.textContent = 'Image + video prompts ready.';
      cards.innerHTML =
        renderMetaRow('both', data) +
        renderPromptBlock('IMAGE PROMPT',  data.image, 'image') +
        renderPromptBlock('VIDEO PROMPT',  data.video, 'video');
    } else {
      const isVideo = data.outputType === 'video' || data.outputType === 'music_video_scene';
      if (sub) sub.textContent = data.title || 'Prompt ready.';
      cards.innerHTML =
        renderMetaRow(isVideo ? 'video' : 'image', data) +
        renderPromptBlock('PROMPT', data, isVideo ? 'video' : 'image');
    }
    cards.hidden = false;

    /* Wire copy buttons */
    cards.querySelectorAll('.create-out-copy').forEach(btn => {
      btn.addEventListener('click', function () {
        const text = this.dataset.copyText;
        if (text) {
          copyText(text);
          const o = this.textContent;
          this.textContent = 'Copied';
          setTimeout(() => { this.textContent = o; }, 1400);
        }
      });
    });
  }

  function renderMetaRow(mode, data) {
    const items = [];
    if (mode === 'both') {
      items.push(metaItem('Output', 'Image + Video'));
    } else {
      items.push(metaItem('Type', mode === 'video' ? 'Video' : 'Image'));
      if (mode === 'video' && data.duration) items.push(metaItem('Duration', data.duration));
    }
    if (referenceImage || wardrobeImage) {
      const refs = [];
      if (referenceImage) refs.push('Face');
      if (wardrobeImage)  refs.push('Wardrobe');
      items.push(metaItem('References', refs.join(' + ')));
    }
    return '<div class="create-out-meta">' + items.join('') + '</div>';
  }

  function metaItem(label, value) {
    return '<span class="create-out-meta-item"><span class="create-out-meta-label">' + escHtml(label) + '</span>' + escHtml(value) + '</span>';
  }

  function renderPromptBlock(label, data, kind) {
    const promptText = data.prompt || data.mainPrompt || '';
    const titleStr   = data.title ? '<div class="create-out-title">' + escHtml(data.title) + '</div>' : '';

    return '<div class="create-out-card is-primary">'
      + '<div class="create-out-head">'
      +   '<span class="create-out-label">' + label + '</span>'
      +   '<span class="create-out-charcount">' + promptText.length + ' chars</span>'
      +   '<button class="create-out-copy" data-copy-text="' + escAttr(promptText) + '">Copy</button>'
      + '</div>'
      + titleStr
      + '<pre class="create-out-body">' + escHtml(promptText) + '</pre>'
      + '</div>';
  }

  function copyAllPrompt() {
    if (!lastOutput) return;
    let out = '';
    if (lastOutput.image && lastOutput.video) {
      const i = lastOutput.image.prompt || lastOutput.image.mainPrompt || '';
      const v = lastOutput.video.prompt || lastOutput.video.mainPrompt || '';
      out = (i ? `IMAGE PROMPT\n${i}` : '') + (i && v ? '\n\n' : '') + (v ? `VIDEO PROMPT\n${v}` : '');
    } else {
      out = lastOutput.prompt || lastOutput.mainPrompt || '';
    }
    if (out) copyText(out);
  }

  function escAttr(s) {
    return String(s).replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/'/g,'&#39;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  function escHtml(s) {
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).catch(fallbackCopy.bind(null, text));
    } else {
      fallbackCopy(text);
    }
  }
  function fallbackCopy(text) {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.cssText = 'position:fixed;left:-9999px';
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
  }

  /* ── Error flash ── */
  function flashError(msg) {
    const sub = document.getElementById('createOutputSub');
    if (!sub) return;
    const orig = sub.textContent;
    sub.textContent = '⚠ ' + msg;
    sub.classList.add('create-error');
    setTimeout(() => { sub.textContent = orig; sub.classList.remove('create-error'); }, 3000);
  }

  /* ── Show / Hide ── */
  function showCreate(mode) {
    /* mode: 'both' | 'nb2' | 'video' — drives the active output mode */
    const view = document.getElementById('createView');
    if (view) view.style.display = 'flex';
    if (mode === 'nb2')   activeMode = 'image';
    else if (mode === 'video') activeMode = 'video';
    else activeMode = 'both';
    updateModeLabel();
    saveState();
  }

  function hideCreate() {
    const view = document.getElementById('createView');
    if (view) view.style.display = 'none';
  }

  /* ── Init ── */
  function initCreate() {
    document.querySelectorAll('.create-source-tab').forEach(tab => {
      if (tab.disabled) return;
      tab.addEventListener('click', () => setSource(tab.dataset.source));
    });

    const genBtn = document.getElementById('createGenerateBtn');
    if (genBtn) genBtn.addEventListener('click', generate);

    const copyAllBtn = document.getElementById('createCopyAllBtn');
    if (copyAllBtn) copyAllBtn.addEventListener('click', copyAllPrompt);

    const regenBtn = document.getElementById('createRegenBtn');
    if (regenBtn) regenBtn.addEventListener('click', generate);

    /* Persist on change */
    ['createSongTitle','createArtistName','createLyrics','createDescription','createBlank',
     'createFocus']
      .forEach(id => {
        const el = document.getElementById(id);
        if (!el) return;
        const evt = (el.tagName === 'SELECT' || el.type === 'text') ? 'change' : 'input';
        el.addEventListener(evt, saveState);
        if (el.tagName === 'TEXTAREA' || el.type === 'text') el.addEventListener('input', saveState);
      });

    /* Enter to generate (Ctrl/Cmd+Enter in textareas) */
    document.querySelectorAll('.create-textarea').forEach(ta => {
      ta.addEventListener('keydown', e => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') { e.preventDefault(); generate(); }
      });
    });

    restoreRefs();
    restoreState();

    /* If the legacy app.js auto-loader has already populated
       imgBase64 (Vawn reference) but we haven't picked it up yet,
       sync it into the Create view's face slot now. */
    if (!referenceImage && typeof window.imgBase64 === 'string' && window.imgBase64) {
      setRef('face', window.imgBase64);
    }
  }

  /* ── Exports ── */
  window.initCreate      = initCreate;
  window.showCreate      = showCreate;
  window.hideCreate      = hideCreate;
  window.createHandleRef = handleRef;
  window.createClearRef  = clearRef;
  window.createSetRef    = setRef;

})();
