/* ── Studio Chat Module — MVP Rebuild ── */
(function () {
  'use strict';

  const STORAGE_KEY               = 'apulu_studio_messages';
  const SESSIONS_KEY              = 'apulu_studio_sessions';
  const MAX_STORED                = 50;
  const MAX_SESSIONS              = 20;
  const MAX_API_MESSAGES          = 12;
  const MAX_API_USER_CHARS        = 5000;
  const MAX_API_ASSISTANT_CHARS   = 6500;
  const MAX_API_OLDER_CHARS       = 1800;
  const STREAM_RENDER_INTERVAL    = 80;

  let studioMessages    = [];
  let isStreaming        = false;
  let abortCtrl         = null;
  let outputBlocks      = [];
  let streamRenderTimer = null;

  /* Card definitions — order controls render order in output panel */
  const CARD_DEFS = [
    {
      extractLabel: 'Lyrics',
      displayLabel: 'LYRICS',
      cardCls:      'studio-card-lyrics',
      charWarnMin:  2700,
      charWarnMax:  3200,
      charHardMax:  3615,
    },
    {
      extractLabel: 'Production Prompt',
      displayLabel: 'SUNO PRODUCTION PROMPT',
      cardCls:      '',
      charMax:      980,
    },
    {
      extractLabel: 'Exclude Styles',
      displayLabel: 'EXCLUDES',
      cardCls:      '',
      charMax:      400,
    },
    {
      extractLabel: 'Final Recording Prompt',
      displayLabel: 'FINAL RECORDING PROMPT',
      cardCls:      '',
    },
  ];

  /* ── localStorage helpers ── */
  function save() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(studioMessages.slice(-MAX_STORED)));
    } catch (_) {}
  }

  function restore() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) studioMessages = JSON.parse(raw);
    } catch (_) { studioMessages = []; }
  }

  /* ── Session archive ── */
  function loadSessions() {
    try {
      const raw = localStorage.getItem(SESSIONS_KEY);
      if (!raw) return [];
      const arr = JSON.parse(raw);
      return Array.isArray(arr) ? arr : [];
    } catch (_) { return []; }
  }

  function saveSessions(arr) {
    try { localStorage.setItem(SESSIONS_KEY, JSON.stringify(arr.slice(0, MAX_SESSIONS))); }
    catch (_) {}
  }

  function deriveSessionTitle(msgs) {
    const first = msgs.find(m => m.role === 'user' && m.content);
    if (first) {
      const line  = first.content.split('\n').find(l => l.trim()) || first.content;
      const clean = line.trim().replace(/\s+/g, ' ');
      return clean.length > 80 ? clean.slice(0, 80) + '…' : clean;
    }
    return 'Untitled session';
  }

  function archiveCurrentSession() {
    if (!studioMessages.length) return;
    const sessions = loadSessions();
    sessions.unshift({
      id:           's_' + Date.now() + '_' + Math.random().toString(36).slice(2, 8),
      title:        deriveSessionTitle(studioMessages),
      createdAt:    Date.now(),
      messageCount: studioMessages.length,
      messages:     studioMessages.slice(),
    });
    saveSessions(sessions);
  }

  function loadSessionById(id) {
    const sessions = loadSessions();
    const hit = sessions.find(s => s.id === id);
    if (!hit || !Array.isArray(hit.messages)) return false;
    archiveCurrentSession();
    saveSessions(sessions.filter(s => s.id !== id));
    studioMessages = hit.messages.slice();
    outputBlocks   = [];
    save();
    renderMessages();
    renderOutputPanel();
    return true;
  }

  function deleteSessionById(id) {
    saveSessions(loadSessions().filter(s => s.id !== id));
  }

  function formatSessionTime(ts) {
    const d   = new Date(ts);
    const now = new Date();
    const opts = d.toDateString() === now.toDateString()
      ? { hour: 'numeric', minute: '2-digit' }
      : { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' };
    try { return d.toLocaleString(undefined, opts); }
    catch (_) { return d.toISOString(); }
  }

  /* ── Minimal markdown renderer ── */
  function renderMarkdown(src) {
    if (!src) return '';
    const lines = src.split('\n');
    let html  = '';
    let inCode = false;
    let codeLines = [];
    let inUl = false, inOl = false;

    function closeList() {
      if (inUl) { html += '</ul>'; inUl = false; }
      if (inOl) { html += '</ol>'; inOl = false; }
    }

    function inline(t) {
      t = t.replace(/`([^`]+)`/g, '<code class="studio-inline-code">$1</code>');
      t = t.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
      t = t.replace(/\*(.+?)\*/g, '<em>$1</em>');
      return t;
    }

    for (let i = 0; i < lines.length; i++) {
      const line    = lines[i];
      const trimmed = line.trim();

      if (trimmed.startsWith('```')) {
        if (!inCode) {
          closeList(); inCode = true; codeLines = [];
        } else {
          const id = 'cb_' + Date.now() + '_' + i;
          html += '<div class="studio-code-block">'
            + '<button class="studio-code-copy" onclick="navigator.clipboard.writeText(document.getElementById(\'' + id + '\').textContent)">Copy</button>'
            + '<pre id="' + id + '"><code>'
            + codeLines.join('\n').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            + '</code></pre></div>';
          inCode = false;
        }
        continue;
      }
      if (inCode) { codeLines.push(line); continue; }

      if (/^(-{3,}|━{3,})$/.test(trimmed)) { closeList(); html += '<hr class="studio-hr">'; continue; }

      const hm = line.match(/^(#{1,6})\s+(.+)/);
      if (hm) { closeList(); html += '<h' + hm[1].length + ' class="studio-h">' + inline(hm[2]) + '</h' + hm[1].length + '>'; continue; }

      if (/^[-*]\s+/.test(line.trimStart())) {
        if (inOl) { html += '</ol>'; inOl = false; }
        if (!inUl) { html += '<ul class="studio-list">'; inUl = true; }
        html += '<li>' + inline(line.trimStart().replace(/^[-*]\s+/, '')) + '</li>';
        continue;
      }

      const olm = line.trimStart().match(/^\d+\.\s+(.+)/);
      if (olm) {
        if (inUl) { html += '</ul>'; inUl = false; }
        if (!inOl) { html += '<ol class="studio-list">'; inOl = true; }
        html += '<li>' + inline(olm[1]) + '</li>';
        continue;
      }

      if (!trimmed) { closeList(); html += '<div class="studio-spacer"></div>'; continue; }

      closeList();
      html += '<p>' + inline(line) + '</p>';
    }

    if (inCode && codeLines.length) {
      html += '<div class="studio-code-block"><pre><code>'
        + codeLines.join('\n').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        + '</code></pre></div>';
    }
    closeList();
    return html;
  }

  /* ── Strip captured contract blocks from chat view ── */
  function stripCapturedBlocks(text) {
    if (!text) return text;
    const lines = text.split('\n');
    let cutoff = -1;
    for (let i = 0; i < lines.length; i++) {
      const t = lines[i].trim();
      const label = t.replace(/^[#*\s]+/, '').replace(/[*:\s]+$/, '').trim();
      if (/^(song title|production prompt|exclude styles|final recording prompt|lyrics)$/i.test(label)) {
        cutoff = i; break;
      }
      if (/^[#*\s]*song title\s*\*{0,2}\s*:\s*.+/i.test(t)) { cutoff = i; break; }
      if (/^\[(Intro|Verse|Hook|Chorus|Bridge|Outro|Pre-Chorus|Pre-Hook)\b/i.test(t)) { cutoff = i; break; }
    }
    if (cutoff < 0) return text;
    return lines.slice(0, cutoff).join('\n').replace(/\s+$/, '');
  }

  /* ── Render messages ── */
  function renderMessages() {
    const container = document.getElementById('studioMessages');
    if (!container) return;

    extractBlocks();

    let lastAiIdx = -1;
    for (let i = studioMessages.length - 1; i >= 0; i--) {
      if (studioMessages[i].role === 'assistant' && studioMessages[i].content) {
        lastAiIdx = i; break;
      }
    }

    let out = '';
    for (let i = 0; i < studioMessages.length; i++) {
      const msg = studioMessages[i];

      if (msg.role === 'user') {
        out += '<div class="studio-msg studio-msg-user">'
          + '<div class="studio-user-bubble">'
          + msg.content.replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>')
          + '</div></div>';

      } else {
        const chatText            = stripCapturedBlocks(msg.content);
        const isLoadingPlaceholder = isStreaming && i === studioMessages.length - 1 && !msg.content;
        const ts   = msg.ts ? new Date(msg.ts) : new Date();
        const time = ts.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });

        let html = '<div class="studio-msg studio-msg-ai">'
          + '<div class="studio-ai-meta">'
          + '<span class="studio-ai-name">Apulu Agent</span>'
          + '<span class="studio-ai-time">' + time + '</span>'
          + '</div>';

        const hasContract = outputBlocks.some(b =>
          CARD_DEFS.some(d => d.extractLabel === b.label)
        );

        if (isLoadingPlaceholder) {
          html += '<div class="studio-loading" aria-live="polite" aria-label="Working on it">'
            + '<span>Working on it</span>'
            + '<span class="studio-dot" aria-hidden="true"></span>'
            + '<span class="studio-dot" aria-hidden="true"></span>'
            + '<span class="studio-dot" aria-hidden="true"></span>'
            + '</div>';
        } else if (chatText) {
          html += '<div class="studio-ai-bubble">'
            + renderMarkdown(chatText)
            + '</div>';
          if (!isStreaming && hasContract) {
            html += '<div class="studio-track-ready">Track package ready — see output panel</div>';
          }
        } else if (!isStreaming && hasContract) {
          html += '<div class="studio-track-ready">Track package ready — see output panel</div>';
        } else if (isStreaming && msg.content) {
          /* contract is being streamed — show nothing in chat, output panel handles it */
        } else if (!isStreaming && msg.content) {
          /* edge case: non-empty content but nothing stripped — show it */
          html += '<div class="studio-ai-bubble">' + renderMarkdown(msg.content) + '</div>';
        }

        html += '</div>';
        out  += html;
      }
    }

    container.innerHTML = out;

    container.querySelectorAll('.studio-track-tab').forEach(btn => {
      btn.addEventListener('click', function () {
        const idx = parseInt(this.dataset.blockIdx);
        if (!isNaN(idx) && outputBlocks[idx]) openTrackSheet(idx);
      });
    });

    scrollToBottom();
    renderOutputPanel();
  }

  /* ── Mobile track tabs (visible via CSS only on small screens) ── */
  function renderMobileTrackTabs() {
    if (!outputBlocks.length) return '';
    const bySong = {};
    outputBlocks.forEach((b, idx) => {
      const key = b.song || '';
      if (!bySong[key]) bySong[key] = [];
      bySong[key].push({ block: b, idx });
    });
    let html = '<div class="studio-track-tabs-wrap">';
    Object.keys(bySong).forEach(song => {
      if (song) html += '<div class="studio-track-tabs-song">' + song.replace(/</g, '&lt;') + '</div>';
      html += '<div class="studio-track-tabs">';
      bySong[song].forEach(({ block, idx }) => {
        const short = block.label
          .replace(/\s*Prompt$/i, '')
          .replace(/^Final Recording$/i, 'Final')
          .replace(/^Exclude Styles$/i, 'Exclude');
        html += '<button class="studio-track-tab" data-block-idx="' + idx + '">'
          + '<span class="studio-track-tab-label">' + short + '</span>'
          + '</button>';
      });
      html += '</div>';
    });
    return html + '</div>';
  }

  /* ── Bottom sheet (mobile) ── */
  function openTrackSheet(idx) {
    const block   = outputBlocks[idx];
    if (!block) return;
    const sheet   = document.getElementById('studioTrackSheet');
    const labelEl = document.getElementById('studioSheetLabel');
    const countEl = document.getElementById('studioSheetCount');
    const bodyEl  = document.getElementById('studioSheetBody');
    const copyBtn = document.getElementById('studioSheetCopy');
    if (!sheet || !labelEl || !bodyEl || !copyBtn) return;

    labelEl.textContent = block.label;
    const cc = block.content.length;
    let countText = cc + ' chars';
    if (/prompt/i.test(block.label)) countText += ' / 980 max';
    if (block.label === 'Lyrics') {
      const dur = cc * 0.065;
      countText += ' · ~' + Math.floor(dur / 60) + ':' + String(Math.round(dur % 60)).padStart(2, '0');
    }
    if (countEl) countEl.textContent = countText;
    bodyEl.textContent = block.content;

    copyBtn.onclick = function () {
      copyText(block.content);
      copyBtn.textContent = 'Copied';
      setTimeout(() => { copyBtn.textContent = 'Copy'; }, 1400);
    };

    sheet.hidden = false;
    requestAnimationFrame(() => sheet.classList.add('studio-track-sheet-open'));
  }

  function closeTrackSheet() {
    const sheet = document.getElementById('studioTrackSheet');
    if (!sheet) return;
    sheet.classList.remove('studio-track-sheet-open');
    setTimeout(() => { sheet.hidden = true; }, 260);
  }

  document.addEventListener('click', function (e) {
    if (e.target && e.target.hasAttribute && e.target.hasAttribute('data-sheet-close')) closeTrackSheet();
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      closeTrackSheet();
      const m = document.getElementById('studioSessionsModal');
      if (m && !m.hidden) closeSessionsModal();
    }
  });

  function scrollToBottom() {
    const c = document.getElementById('studioMessages');
    if (c) c.scrollTop = c.scrollHeight;
  }

  function scheduleStreamingRender() {
    if (streamRenderTimer) return;
    streamRenderTimer = setTimeout(() => {
      streamRenderTimer = null;
      renderMessages();
    }, STREAM_RENDER_INTERVAL);
  }

  function flushStreamingRender() {
    if (!streamRenderTimer) return;
    clearTimeout(streamRenderTimer);
    streamRenderTimer = null;
    renderMessages();
  }

  /* ── API message building ── */
  function compactAssistantForApi(content) {
    const compact = stripCapturedBlocks(content || '').trim();
    return compact || String(content || '').slice(0, MAX_API_OLDER_CHARS);
  }

  function buildApiMessages() {
    const recent = studioMessages
      .filter(m => m.content)
      .map(m => ({ role: m.role, content: m.content }))
      .slice(-MAX_API_MESSAGES);

    let latestAiIdx = -1;
    for (let i = recent.length - 1; i >= 0; i--) {
      if (recent[i].role === 'assistant') { latestAiIdx = i; break; }
    }

    return recent.map((m, idx) => {
      const limit = m.role === 'user'
        ? MAX_API_USER_CHARS
        : idx === latestAiIdx ? MAX_API_ASSISTANT_CHARS : MAX_API_OLDER_CHARS;
      const content = (m.role === 'assistant' && idx !== latestAiIdx)
        ? compactAssistantForApi(m.content)
        : m.content;
      return { role: m.role, content: content.slice(0, limit) };
    });
  }

  /* ── Send message with SSE streaming ── */
  async function sendMessage() {
    const textarea = document.getElementById('studioInput');
    if (!textarea) return;
    const text = textarea.value.trim();
    if (!text || isStreaming) return;

    studioMessages.push({ role: 'user',      content: text, ts: Date.now() });
    studioMessages.push({ role: 'assistant', content: '',   ts: Date.now() });
    textarea.value      = '';
    textarea.style.height = 'auto';
    renderMessages();

    isStreaming = true;
    updateSendBtn();
    renderOutputPanel(); /* show skeleton immediately */
    abortCtrl = new AbortController();

    const apiMessages = buildApiMessages();
    const apiBase     = window.APULU_PROMPT_API_BASE || '/api/prompt-generator';

    try {
      const resp = await fetch(apiBase + '/studio/chat', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ messages: apiMessages }),
        signal:  abortCtrl.signal,
      });

      if (!resp.ok) {
        const errText = await resp.text().catch(() => '');
        let errMsg = 'Studio not configured on server';
        if (resp.status === 429) errMsg = 'Sonnet is busy — try again in a moment';
        else if (errText) try { errMsg = JSON.parse(errText).error || errMsg; } catch (_) {}
        throw new Error(errMsg);
      }

      const reader  = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer    = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop();

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const payload = line.slice(6).trim();
          if (!payload) continue;
          try {
            const evt = JSON.parse(payload);
            if (evt.type === 'delta' && evt.text) {
              studioMessages[studioMessages.length - 1].content += evt.text;
              scheduleStreamingRender();
            } else if (evt.type === 'error') {
              throw new Error(evt.message || 'Stream error');
            }
          } catch (parseErr) {
            if (parseErr.message && !parseErr.message.includes('JSON')) throw parseErr;
          }
        }
      }
    } catch (err) {
      if (err.name === 'AbortError') return;
      flushStreamingRender();
      const last = studioMessages[studioMessages.length - 1];
      if (last && last.role === 'assistant') {
        const prefix = last.content ? last.content + '\n\n' : '';
        last.content = prefix + '⚠ ' + (err.message || 'Connection lost');
      }
      renderMessages();
    } finally {
      flushStreamingRender();
      isStreaming = false;
      abortCtrl   = null;
      updateSendBtn();
      save();
      renderMessages();
    }
  }

  function updateSendBtn() {
    const btn = document.getElementById('studioSendBtn');
    if (btn) {
      btn.disabled = isStreaming;
      btn.setAttribute('aria-busy', String(isStreaming));
    }
    const regen = document.getElementById('studioRegenAll');
    if (regen) regen.disabled = isStreaming;
  }

  /* ── Regenerate All ── */
  function regenerateAll() {
    if (isStreaming) return;
    const ta = document.getElementById('studioInput');
    if (ta) {
      ta.value = 'Please regenerate all sections of the track package.';
      ta.style.height = 'auto';
      ta.style.height = Math.min(ta.scrollHeight, 160) + 'px';
      sendMessage();
    }
  }

  /* ── New Session ── */
  function newSession() {
    if (isStreaming && abortCtrl) abortCtrl.abort();
    archiveCurrentSession();
    studioMessages = [];
    outputBlocks   = [];
    localStorage.removeItem(STORAGE_KEY);
    renderMessages();
    renderOutputPanel();
  }

  /* ── Sessions modal ── */
  function escHtml(s) {
    return String(s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function renderSessionsList() {
    const list = document.getElementById('studioSessionsList');
    if (!list) return;
    const sessions = loadSessions();
    if (!sessions.length) {
      list.innerHTML = '<div class="studio-session-empty">No previous sessions yet. Start a new session to archive the current one here.</div>';
      return;
    }
    list.innerHTML = sessions.map(s => {
      const count = s.messageCount || (s.messages && s.messages.length) || 0;
      return '<div class="studio-session-item" data-session-id="' + escHtml(s.id) + '">'
        + '<div class="studio-session-main">'
        + '<div class="studio-session-title">' + escHtml(s.title || 'Untitled session') + '</div>'
        + '<div class="studio-session-meta">' + escHtml(formatSessionTime(s.createdAt)) + ' · ' + count + ' msg' + (count === 1 ? '' : 's') + '</div>'
        + '</div>'
        + '<button class="studio-session-delete" data-action="delete" data-session-id="' + escHtml(s.id) + '" aria-label="Delete session">🗑</button>'
        + '</div>';
    }).join('');
  }

  function openSessionsModal() {
    const modal = document.getElementById('studioSessionsModal');
    if (!modal) return;
    renderSessionsList();
    modal.hidden = false;
  }

  function closeSessionsModal() {
    const modal = document.getElementById('studioSessionsModal');
    if (modal) modal.hidden = true;
  }

  /* ── Copy helpers ── */
  function copyLast() {
    const last = [...studioMessages].reverse().find(m => m.role === 'assistant' && m.content);
    if (last) copyText(last.content);
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

  function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).catch(() => fallbackCopy(text));
    } else {
      fallbackCopy(text);
    }
  }

  /* ── Block extraction ── */
  function extractBlocks() {
    outputBlocks = [];
    const assistantMsgs = studioMessages.filter(m => m.role === 'assistant' && m.content);
    const msgsToScan    = assistantMsgs.filter(msg =>
      /song title|production prompt|final recording prompt|exclude styles|^\[(?:Intro|Verse|Hook|Chorus|Bridge|Outro|Pre-Chorus|Pre-Hook)\b/im.test(msg.content)
    );
    if (!msgsToScan.length) return;

    let scanMsgIdx = -1;
    for (const msg of msgsToScan) {
      scanMsgIdx++;
      const msgIdx  = scanMsgIdx;
      const lines   = msg.content.split('\n');
      let currentLabel = null;
      let currentLines = [];
      let songTitle    = null;

      function flush() {
        if (!currentLabel || !currentLines.length) { currentLabel = null; currentLines = []; return; }
        const content = currentLines.join('\n').trim();
        if (content) {
          let blockSong = songTitle || '';
          if (currentLabel === 'Song Title') {
            songTitle = content.split('\n').find(Boolean)?.trim() || songTitle || '';
            blockSong = songTitle;
          }
          const existingIdx = outputBlocks.findIndex(b => b.label === currentLabel && b.song === blockSong);
          if (existingIdx >= 0) {
            if (currentLabel === 'Lyrics' && outputBlocks[existingIdx]._msgIdx === msgIdx) {
              outputBlocks[existingIdx].content += '\n\n' + content;
            } else {
              Object.assign(outputBlocks[existingIdx], { content, _msgIdx: msgIdx, song: blockSong });
            }
          } else {
            outputBlocks.push({ label: currentLabel, content, song: blockSong, _msgIdx: msgIdx });
          }
        }
        currentLabel = null;
        currentLines = [];
      }

      const LYRICS_TERM = /^(\*\*[^*]*(?:a&r|closing|final|note|commentary|summary|breakdown)[^*]*\*\*|#{1,6}\s+.*(?:a&r|closing|final|note|commentary))/i;

      for (let i = 0; i < lines.length; i++) {
        const line    = lines[i];
        const trimmed = line.trim();

        if (/^```/.test(trimmed)) continue;
        if (currentLabel === 'Lyrics' && /^-{3,}\s*$/.test(trimmed)) continue;
        if (currentLabel === 'Lyrics' && LYRICS_TERM.test(trimmed)) { flush(); continue; }

        const ls = trimmed.replace(/^[#*\s]+/, '').replace(/[*:\s]+$/, '').trim();

        if (/^song title$/i.test(ls)) { flush(); currentLabel = 'Song Title'; continue; }
        const titleInline = trimmed.match(/^[#*\s]*song title\s*\*{0,2}\s*:\s*(.+)/i);
        if (titleInline && !currentLabel) { flush(); currentLabel = 'Song Title'; currentLines.push(titleInline[1]); flush(); continue; }
        const headingTitle = trimmed.match(/^#+\s+(.+)/);
        if (headingTitle && !currentLabel) {
          const c = headingTitle[1].replace(/\*+/g, '').trim();
          if (c && c.length < 80 && !/production|recording|exclude|lyrics|prompt/i.test(c)) songTitle = c;
        }
        if (/^production prompt$/i.test(ls)) { flush(); currentLabel = 'Production Prompt'; continue; }
        if (/^final recording prompt$/i.test(ls)) { flush(); currentLabel = 'Final Recording Prompt'; continue; }
        if (/^exclude styles$/i.test(ls)) { flush(); currentLabel = 'Exclude Styles'; continue; }
        const excInline = trimmed.match(/^exclude styles\s*:\s*(.+)/i);
        if (excInline && !currentLabel) { flush(); currentLabel = 'Exclude Styles'; currentLines.push(excInline[1]); continue; }
        if (/^lyrics$/i.test(ls) && currentLabel !== 'Lyrics') { flush(); currentLabel = 'Lyrics'; continue; }
        if (/^\[(?:Intro|Verse|Hook|Chorus|Bridge|Outro|Pre-Chorus|Pre-Hook)\b/i.test(trimmed) && currentLabel !== 'Lyrics') {
          flush(); currentLabel = 'Lyrics'; currentLines.push(line); continue;
        }

        if (currentLabel) {
          if (!trimmed && i + 1 < lines.length) {
            const next = lines[i + 1].trim();
            if (/^(song title|production prompt|final recording prompt|exclude styles|lyrics|#{1,6}\s|\[(?:Intro|Verse|Hook|Chorus|Bridge|Outro))/i.test(next)) {
              flush(); continue;
            }
            if (currentLabel === 'Lyrics') { currentLines.push(''); continue; }
            if (currentLines.length && currentLines[currentLines.length - 1] === '') { flush(); continue; }
            currentLines.push('');
            continue;
          }
          if (trimmed || currentLabel === 'Lyrics') currentLines.push(line);
        }
      }
      flush();
    }
  }

  /* ── Skeleton card HTML ── */
  function buildSkeletonCard(displayLabel) {
    return '<div class="studio-skeleton-card">'
      + '<div class="studio-card-header"><span class="studio-card-label">' + displayLabel + '</span></div>'
      + '<div class="studio-skeleton-body">'
      + '<div class="studio-skeleton-line"></div>'
      + '<div class="studio-skeleton-line" style="width:82%"></div>'
      + '<div class="studio-skeleton-line" style="width:66%"></div>'
      + '<div class="studio-skeleton-line" style="width:45%"></div>'
      + '</div>'
      + '</div>';
  }

  /* ── Card action handler ── */
  function handleCardAction(e) {
    const btn    = e.currentTarget;
    const action = btn.dataset.cardAction;
    const idx    = parseInt(btn.dataset.idx);
    const block  = outputBlocks[idx];
    const card   = btn.closest('.studio-output-card');

    if (action === 'copy') {
      if (!block) return;
      copyText(block.content);
      const orig = btn.textContent;
      btn.textContent = 'Copied';
      setTimeout(() => { btn.textContent = orig; }, 1500);

    } else if (action === 'edit') {
      if (!block || !card) return;
      card.classList.add('studio-card-editing');
      const ta = card.querySelector('.studio-card-edit-area textarea');
      if (ta) {
        ta.value = block.content;
        ta.style.height = 'auto';
        ta.style.height = ta.scrollHeight + 'px';
        setTimeout(() => ta.focus(), 0);
      }

    } else if (action === 'cancel') {
      if (!card) return;
      card.classList.remove('studio-card-editing');
      if (block) {
        const ta = card.querySelector('.studio-card-edit-area textarea');
        if (ta) ta.value = block.content;
      }

    } else if (action === 'save') {
      if (!block || !card) return;
      const ta = card.querySelector('.studio-card-edit-area textarea');
      if (ta) {
        block.content = ta.value;
        save();
        const bodyEl = card.querySelector('.studio-card-body');
        if (bodyEl) bodyEl.textContent = block.content;
      }
      card.classList.remove('studio-card-editing');
    }
  }

  /* ── Render output panel ── */
  function renderOutputPanel() {
    extractBlocks();
    const cards      = document.getElementById('studioOutputCards');
    const emptyState = document.getElementById('studioEmptyState');
    const regenBtn   = document.getElementById('studioRegenAll');
    const outputSub  = document.getElementById('studioOutputSub');
    if (!cards) return;

    /* Find the most recent song title block, then prefer its track's blocks */
    let latestSongIdx = -1;
    let latestSong    = '';
    for (let i = outputBlocks.length - 1; i >= 0; i--) {
      if (outputBlocks[i].label === 'Song Title') {
        latestSongIdx = i;
        latestSong    = (outputBlocks[i].content || '').split('\n').find(Boolean) || '';
        break;
      }
    }

    /* Helper: pick the latest block matching this card def.
       Prefer one whose song matches latestSong; else fall back to the last
       block with that label that appears at-or-after latestSongIdx; else the
       last block with that label anywhere. */
    function pickLatest(def) {
      let bySong    = null;
      let afterSong = null;
      let anywhere  = null;
      for (let i = outputBlocks.length - 1; i >= 0; i--) {
        const b = outputBlocks[i];
        if (b.label !== def.extractLabel) continue;
        if (!anywhere) anywhere = b;
        if (!afterSong && i >= latestSongIdx) afterSong = b;
        if (latestSong && b.song === latestSong) { bySong = b; break; }
      }
      return bySong || afterSong || anywhere;
    }

    const hasBlocks = CARD_DEFS.some(def => !!pickLatest(def));

    /* ── Empty state ── */
    if (!hasBlocks && !isStreaming) {
      cards.style.display = 'none';
      if (emptyState) emptyState.style.display = 'flex';
      if (regenBtn)   regenBtn.style.display   = 'none';
      if (outputSub)  outputSub.textContent     = 'Start by describing the song you want to create.';
      return;
    }

    /* ── Generating or populated ── */
    if (emptyState) emptyState.style.display = 'none';
    cards.style.display = 'flex';

    if (regenBtn) regenBtn.style.display = hasBlocks ? '' : 'none';
    if (outputSub) {
      if (isStreaming) {
        outputSub.textContent = 'Generating your track package…';
      } else if (latestSong) {
        outputSub.textContent = latestSong;
      } else {
        outputSub.textContent = "Here's your complete track package.";
      }
    }

    let html = '';

    if (isStreaming && !hasBlocks) {
      /* Full skeletons before any blocks arrive */
      CARD_DEFS.forEach(def => { html += buildSkeletonCard(def.displayLabel); });
    } else {
      CARD_DEFS.forEach(def => {
        const block = pickLatest(def);
        if (!block) {
          if (isStreaming) html += buildSkeletonCard(def.displayLabel);
          return;
        }

        const cc       = block.content.length;
        const isLyrics = def.extractLabel === 'Lyrics';
        const overMax  = def.charMax && cc > def.charMax;
        const lyrOver  = isLyrics && cc > (def.charHardMax || 3615);
        const lyrWarn  = isLyrics && !lyrOver
          && (cc < (def.charWarnMin || 0) || cc > (def.charWarnMax || Infinity));

        let cntCls  = 'studio-card-count';
        if (overMax || lyrOver) cntCls += ' studio-card-over';
        else if (lyrWarn)       cntCls += ' studio-card-warn';

        let cntTxt = cc + ' chars';
        if (def.charMax) cntTxt += ' / ' + def.charMax + ' max';
        if (isLyrics) {
          const dur = cc * 0.065;
          cntTxt += ' · ~' + Math.floor(dur / 60) + ':' + String(Math.round(dur % 60)).padStart(2, '0');
        }
        if (overMax || lyrOver) cntTxt += ' ⚠';

        const srcIdx  = outputBlocks.indexOf(block);
        const overCls = (overMax || lyrOver) ? ' studio-card-overlimit' : '';
        const cardCls = def.cardCls ? ' ' + def.cardCls : '';

        html += '<div class="studio-output-card' + overCls + cardCls + '" data-card-idx="' + srcIdx + '">'
          + '<div class="studio-card-header">'
          + '<span class="studio-card-label">' + def.displayLabel + '</span>'
          + '<span class="' + cntCls + '">' + cntTxt + '</span>'
          + '<div class="studio-card-actions">'
          + '<button class="studio-card-action-btn" data-card-action="copy" data-idx="' + srcIdx + '" aria-label="Copy ' + def.displayLabel + '">Copy</button>'
          + '<button class="studio-card-action-btn" data-card-action="edit" data-idx="' + srcIdx + '" aria-label="Edit ' + def.displayLabel + '">Edit</button>'
          + '</div>'
          + '</div>'
          + '<pre class="studio-card-body">' + block.content.replace(/</g, '&lt;').replace(/>/g, '&gt;') + '</pre>'
          + '<div class="studio-card-edit-area">'
          + '<textarea rows="4" aria-label="Edit ' + def.displayLabel + '"></textarea>'
          + '<div class="studio-card-edit-actions">'
          + '<button class="studio-card-action-btn studio-cancel-btn" data-card-action="cancel" data-idx="' + srcIdx + '">Cancel</button>'
          + '<button class="studio-card-action-btn studio-save-btn"   data-card-action="save"   data-idx="' + srcIdx + '">Save</button>'
          + '</div>'
          + '</div>'
          + '</div>';
      });
    }

    cards.innerHTML = html;

    cards.querySelectorAll('[data-card-action]').forEach(btn => {
      btn.addEventListener('click', handleCardAction);
    });

    cards.querySelectorAll('.studio-card-edit-area textarea').forEach(ta => {
      ta.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = this.scrollHeight + 'px';
      });
    });
  }

  /* ── Show / Hide ── */
  function showStudio() {
    restore();
    renderMessages();
    renderOutputPanel();
    const view = document.getElementById('studioView');
    if (view) view.style.display = 'flex';
  }

  function hideStudio() {
    const view = document.getElementById('studioView');
    if (view) view.style.display = 'none';
  }

  /* ── Init ── */
  function initStudio() {
    const ta = document.getElementById('studioInput');
    if (ta) {
      ta.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 160) + 'px';
      });
      ta.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
      });
    }

    const sendBtn  = document.getElementById('studioSendBtn');
    if (sendBtn)   sendBtn.addEventListener('click', sendMessage);

    const regenBtn = document.getElementById('studioRegenAll');
    if (regenBtn)  regenBtn.addEventListener('click', regenerateAll);

    const newBtn   = document.getElementById('studioNewSession');
    if (newBtn)    newBtn.addEventListener('click', newSession);

    const sessBtn  = document.getElementById('studioSessions');
    if (sessBtn)   sessBtn.addEventListener('click', openSessionsModal);

    const sessModal = document.getElementById('studioSessionsModal');
    if (sessModal) {
      sessModal.addEventListener('click', function (e) {
        if (e.target.closest('[data-sessions-close]')) { closeSessionsModal(); return; }
        const del = e.target.closest('[data-action="delete"]');
        if (del) {
          e.stopPropagation();
          const id = del.getAttribute('data-session-id');
          if (id && confirm('Delete this session?')) { deleteSessionById(id); renderSessionsList(); }
          return;
        }
        const item = e.target.closest('.studio-session-item');
        if (item) {
          const id = item.getAttribute('data-session-id');
          if (id && loadSessionById(id)) closeSessionsModal();
        }
      });
    }

    const copyBtn = document.getElementById('studioCopyLast');
    if (copyBtn)  copyBtn.addEventListener('click', copyLast);
  }

  /* ── Exports ── */
  window.initStudio  = initStudio;
  window.showStudio  = showStudio;
  window.hideStudio  = hideStudio;

})();
