'use strict';

const NEGATIVE_PROMPT = [
  'cartoonish','illustrated','soft focus','blurry artifacts','distorted hands',
  'extra limbs','face warping','AI artifacts','anime style','warped clothing',
  'morphed fabric','melting garments','distorted patterns','illegible text on clothing',
  'fused fabric layers','unrealistic drape','plastic-looking material','impossible lighting',
  'mismatched environments','floating subjects','distorted shoes','melted footwear',
  'floating jewelry','tangled chains','cloned background figures','inconsistent shadows',
  'wrong season clothing','cloned foreground figures','distorted text on clothing','warped logos',
];

// Prompt guardrail constants
const MAX_PROMPT_CHARS = 1500;
const MAX_NEGATIVE_TERMS = 8;
// Seedance 2.0 Skill EN openers. Every video prompt should begin with one of
// these top-level section labels. "Style & Mood:" is the canonical opener;
// "Narrative Summary:" is allowed when the model leads with a one-sentence
// summary before Style & Mood. Used for positive validation (soft warning).
const SEEDANCE_OPENING_RE = /^(style\s*&\s*mood|narrative\s+summary)\s*:/i;
// Bare retired Director's Upgrade tags ("Setting:", "Subject:", "Camera:",
// "Lighting:") at the very start of a video prompt. The Seedance Skill EN
// format embeds these concepts inside Style & Mood / Dynamic / Static — never
// as bare top-level labels. Note: "Style & Mood:" does NOT match this regex.
const BANNED_TAGGED_OPENING_RE = /^(setting|subject|camera|lighting)\s*:/i;

// ───────────────────────────────────────────────────────────────
// Seedance 2.0 compliance validators
// Rules canonical source: agents/seedance-rules.js, also wiki/vawn-mix-engine/... no
// the canonical source is the same SEEDANCE_RULES constant referenced by hf-* directors.
// These post-output validators catch LLM slip-ups against the hard limits.
// ───────────────────────────────────────────────────────────────

// Trigger words that activate global filters and ruin generations.
// "stuttering" included as alias for "strobing" — both trigger the same low-shutter filter.
const SEEDANCE_BANNED_TRIGGER_RE = /\b(strobing|stuttering|step[- ]printing|undercranking|symmetrical|mirrored|prismatic|petzval)\b/gi;

// Reflection mechanics — Seedance duplicates/warps characters in reflections.
// Match phrases like "mirror reflection", "reflected in", "reflection in the glass/water/blade".
const SEEDANCE_REFLECTION_RE = /\b(reflected in (?:the )?(?:mirror|glass|window|water|puddle|blade|knife|chrome)|mirror reflection|reflection (?:in|on) (?:the )?(?:mirror|glass|window|water|puddle|blade|knife|chrome|tile))\b/gi;

// Focal lengths above 75mm — engine has no presets above this; use shot size terms (choker/ECU).
// Match e.g. 85mm, 100mm, 135mm, 200mm, 300mm. Exclude 7-75mm range explicitly.
const SEEDANCE_LONG_FOCAL_RE = /\b(8[5-9]|9\d|1\d{2}|2\d{2}|3\d{2}|4\d{2})\s?mm\b/gi;

// "Negative:" field has no equivalent in Seedance/Higgsfield global_prompt — strip on hf-* modes.
const NEGATIVE_FIELD_RE = /(^|\n)\s*Negative:\s*/i;

/**
 * Scan a prompt for Seedance rule violations. Returns { issues: [...], cleaned: <string> }.
 * Does not auto-fix banned trigger words or reflections (those need creative rewrites)
 * but DOES auto-strip the Negative: field for Higgsfield-targeted prompts and warns.
 */
function checkSeedanceCompliance(prompt, label, isHiggsfield = false) {
  const issues = [];
  let cleaned = prompt;

  // Banned trigger words
  const triggerMatches = [...new Set((cleaned.match(SEEDANCE_BANNED_TRIGGER_RE) || []).map(m => m.toLowerCase()))];
  if (triggerMatches.length) {
    issues.push(`${label}: Seedance banned trigger word(s): ${triggerMatches.join(', ')} — these activate global filters (e.g., low-shutter strobe) and ruin generations. Rewrite as concrete physical cause (e.g., "fixture vibrates from impact" instead of "strobing").`);
  }

  // Reflection mechanics
  const reflectMatches = [...new Set((cleaned.match(SEEDANCE_REFLECTION_RE) || []).map(m => m.toLowerCase()))];
  if (reflectMatches.length) {
    issues.push(`${label}: Seedance reflection mechanic(s) detected: ${reflectMatches.join('; ')} — Seedance duplicates/warps characters in mirrors/glass/water. Cut reflection mechanic; use direct shot of subject instead.`);
  }

  // Focal length > 75mm
  const focalMatches = [...new Set((cleaned.match(SEEDANCE_LONG_FOCAL_RE) || []))];
  if (focalMatches.length) {
    issues.push(`${label}: Focal length(s) above 75mm: ${focalMatches.join(', ')} — engine has no preset above 75mm. Use shot size terms (choker, ECU, tight close-up) instead of long focal lengths.`);
  }

  // Negative field on Higgsfield (Seedance has no global negative field per chat rules)
  if (isHiggsfield && NEGATIVE_FIELD_RE.test(cleaned)) {
    // Auto-strip — safe transformation since the negative field has no effect anyway.
    cleaned = cleaned.replace(/(^|\n)\s*Negative:[^\n]*$/im, '$1').replace(/\n\s*\n+$/, '\n').trimEnd();
    issues.push(`${label}: stripped 'Negative:' field — Seedance/Higgsfield has no global_prompt negative field; the entries had no effect.`);
  }

  return { issues, cleaned };
}

function pushWarning(warnings, msg) {
  if (msg && !warnings.includes(msg)) warnings.push(msg);
}

/**
 * Trim negative list to top N terms, truncate overall prompt, and run Seedance
 * 2.0 compliance checks. Returns the (possibly trimmed/cleaned) prompt string.
 *
 * The `isHiggsfield` flag is retained for API compatibility but defaults to true
 * since Kling 3.0 support was removed 2026-04-16 — every prompt this pipeline
 * produces now targets Higgsfield Cinema Studio 3.0 / Seedance 2.0.
 */
function applyPromptGuardrails(prompt, label, warnings, isHiggsfield = true) {
  if (typeof prompt !== 'string' || !prompt) return prompt;
  // Trim negative list if too long
  const negIdx = prompt.lastIndexOf('Negative:');
  if (negIdx !== -1) {
    const before = prompt.slice(0, negIdx);
    const negPart = prompt.slice(negIdx + 'Negative:'.length).trim();
    const terms = negPart.split(',').map(t => t.trim()).filter(Boolean);
    if (terms.length > MAX_NEGATIVE_TERMS) {
      const trimmed = terms.slice(0, MAX_NEGATIVE_TERMS).join(', ');
      prompt = before + 'Negative: ' + trimmed;
      pushWarning(warnings, `${label}: negative list trimmed from ${terms.length} to ${MAX_NEGATIVE_TERMS} terms`);
    }
  }
  // Truncate if over character limit
  if (prompt.length > MAX_PROMPT_CHARS) {
    pushWarning(warnings, `${label}: prompt truncated from ${prompt.length} to ${MAX_PROMPT_CHARS} chars`);
    prompt = prompt.slice(0, MAX_PROMPT_CHARS);
  }
  // Seedance 2.0 compliance — always runs since Kling was removed.
  if (isHiggsfield) {
    const { issues, cleaned } = checkSeedanceCompliance(prompt, label, true);
    issues.forEach(i => pushWarning(warnings, i));
    prompt = cleaned;
  }
  return prompt;
}

/**
 * Lightweight format validation — warns (does not block) on video-prompt
 * format issues. As of 2026-04-29 the Seedance 2.0 Skill EN format is the
 * canonical structure: every video prompt opens with "Style & Mood:" and
 * contains, in order, "Style & Mood: …", "Dynamic Description: …", and
 * "Static Description: …" sections. Bare retired tags at the start
 * ("Setting:", "Subject:", "Camera:", "Lighting:") are flagged.
 *
 * The `expectedFormat` arg is retained for API compatibility — accepts
 * 'PHYSICS_FIRST' (legacy alias) and 'SEEDANCE_SKILL' (new). Any other value
 * is a no-op so legacy call sites don't crash.
 */
function validatePromptFormat(prompt, expectedFormat, label, warnings) {
  if (typeof prompt !== 'string' || !prompt) return;
  if (expectedFormat !== 'PHYSICS_FIRST' && expectedFormat !== 'SEEDANCE_SKILL') return;
  const trimmed = prompt.trim();
  if (BANNED_TAGGED_OPENING_RE.test(trimmed)) {
    pushWarning(warnings, `${label}: prompt opens with a bare retired tag ("Setting:/Subject:/Camera:/Lighting:"). Rewrite using Seedance 2.0 Skill EN format opening with "Style & Mood:".`);
    return;
  }
  if (!SEEDANCE_OPENING_RE.test(trimmed)) {
    pushWarning(warnings, `${label}: prompt does not open with "Style & Mood:" (Seedance 2.0 Skill EN format). The model may have skipped the section header.`);
    return;
  }
  // Spot-check the two other mandatory section labels appear somewhere later.
  if (!/dynamic\s+description\s*:/i.test(trimmed)) {
    pushWarning(warnings, `${label}: missing "Dynamic Description:" section (Seedance 2.0 Skill EN format requires it).`);
  }
  if (!/static\s+description\s*:/i.test(trimmed)) {
    pushWarning(warnings, `${label}: missing "Static Description:" section (Seedance 2.0 Skill EN format requires it).`);
  }
}

// All video modes route through Higgsfield Cinema Studio 3.0 / Seedance 2.0.
// Kling 3.0 modes ('mv', 'kling-*') were removed 2026-04-16 — Seedance is the
// canonical video target. See wiki/vawn-mix-engine/mix-rules.md for context.
const MODE_CONFIG = {
  mv:             { runVideoDirector: true,  defaultN: 6, minN: 6, maxN: 8 },
  nb2:            { runVideoDirector: false, defaultN: 6, minN: 1, maxN: 8 },
  'hf-mv':        { runVideoDirector: true,  defaultN: 6, minN: 6, maxN: 8 },
  'hf-multishot': { runVideoDirector: true,  defaultN: 6, minN: 6, maxN: 8, multishot: true },
  'kling-9grid':  { runVideoDirector: true,  defaultN: 9, minN: 9, maxN: 9 },
  'kling-startend': { runVideoDirector: true, defaultN: 2, minN: 2, maxN: 4 },
  'hf-9grid':     { runVideoDirector: true,  defaultN: 9, minN: 9, maxN: 9 },
  'hf-startend':  { runVideoDirector: true,  defaultN: 2, minN: 2, maxN: 4 },
  'hf-story':     { runVideoDirector: false, defaultN: 8, minN: 4, maxN: 12 },
  'hf-tiktok':    { runVideoDirector: false, defaultN: 4, minN: 3, maxN: 6 },
};

function modeConfig(mode) {
  const cfg = MODE_CONFIG[mode];
  if (!cfg) throw new Error(`Unknown mode: ${mode}`);
  return cfg;
}

function resolveSceneCount(mode, requested) {
  const { defaultN, minN, maxN } = modeConfig(mode);
  if (requested == null) return defaultN;
  return Math.min(maxN, Math.max(minN, requested));
}

function buildLabel(a1Scene) {
  return `WORLD ${a1Scene.style_world} — ${a1Scene.style_world_name} | ${a1Scene.location}, ${a1Scene.time_of_day}`;
}

/**
 * Map the first 4 items from Agent 2's MadeOutOf array to named wardrobe slots.
 * IMPORTANT: The Stylist agent (agents/stylist.js) MUST output MadeOutOf items
 * in this exact order: [top/shirt, bottom/pants, outerwear/jacket, headwear/hat, footwear/shoes].
 * Only indices 0-3 are stored in wardrobe memory. Shoes (index 4) are intentionally excluded
 * because the frontend wardrobe memory tracks shirt/pants/jacket/hat only — shoes use
 * the Shoe Color-Lock Rule and Shoe Model No-Repeat Rule instead.
 * If the stylist changes this order, wardrobe_used will be silently wrong.
 */
function buildWardrobeUsed(madeOf = []) {
  const slots = ['shirt', 'pants', 'jacket', 'hat'];
  const result = {};
  slots.forEach((slot, i) => {
    result[slot] = madeOf[i] || 'none';
  });
  return result;
}

/**
 * Merge 4 agent outputs by index into the final assembled response.
 * scenes_requested = a1.length (after count mismatch policy applied upstream)
 */
function mergeByIndex(a1Scenes, a2Scenes, a3Scenes, a4Scenes, stylePreset = null) {
  const byIndex = (arr) => {
    const map = {};
    (arr || []).forEach(s => { map[s.index] = s; });
    return map;
  };

  const m1 = byIndex(a1Scenes);
  const m2 = byIndex(a2Scenes);
  const m3 = byIndex(a3Scenes);
  const m4 = byIndex(a4Scenes);

  const scenes = [];

  // Agent 3 is the authoritative index set — only assemble scenes with a3 data
  Object.values(m3).forEach(s3 => {
    const i = s3.index;
    const s1 = m1[i];
    const s2 = m2[i];
    if (!s1 || !s2) return; // drop scene if a1 or a2 data missing

    const scene = {
      scene_number: i,
      title: s1.narrative_beat || '',
      style_world: `WORLD ${s1.style_world} — ${s1.style_world_name}`,
      wardrobe_used: buildWardrobeUsed(s2.MadeOutOf),
      image_prompt: {
        label:         buildLabel(s1),
        Subject:       s2.Subject,
        MadeOutOf:     s2.jewelry ? [...(s2.MadeOutOf || []), s2.jewelry] : (s2.MadeOutOf || []),
        Arrangement:   s3.Arrangement,
        Lighting:      s3.Lighting,
        Camera:        s3.Camera,
        Background:    s3.Background,
        FilmStock:     s3.FilmStock,
        Mood:          s3.Mood,
        Composition:   s3.Composition,
        ColorPalette:  s3.ColorPalette,
        NegativePrompt: s3.NegativePrompt || NEGATIVE_PROMPT,
        // Carry the active style preset so frontend renderers + image-gen
        // endpoints know which assembly opener (e.g. "70s family-album
        // photograph" vs "cinematic editorial still") to use.
        ...(stylePreset ? { style_preset: stylePreset } : {}),
      },
      video_prompt: m4[i]?.video_prompt ?? null,
    };

    // Higgsfield-specific fields (present when using hf- modes)
    const s4 = m4[i];
    if (s4) {
      if (s4.camera_movement) scene.hf_camera_movement = s4.camera_movement;
      if (s4.genre)           scene.hf_genre = s4.genre;
      if (s4.duration)        scene.hf_duration = s4.duration;
      if (s4.start_frame)     scene.hf_start_frame = s4.start_frame;
      if (s4.end_frame)       scene.hf_end_frame = s4.end_frame;
      if (s4.emotions)        scene.hf_emotions = s4.emotions;
    }

    scenes.push(scene);
  });

  // sort by scene_number to preserve ordering
  scenes.sort((a, b) => a.scene_number - b.scene_number);

  return {
    scenes,
    scenes_generated: scenes.length,
    scenes_requested: a1Scenes.length,
  };
}

const { systemPrompt: architectPrompt, buildUserMessage: architectMsg } = require('./scene-architect');
const { systemPrompt: stylistPrompt, buildUserMessage: stylistMsg } = require('./stylist');
const { buildSystemPrompt: cinBuildPrompt, buildUserMessage: cinMsg, STYLE_PRESETS: CIN_STYLE_PRESETS, DEFAULT_PRESET: CIN_DEFAULT_PRESET } = require('./cinematographer');
const { systemPrompt: hfDirPrompt, buildUserMessage: hfDirMsg } = require('./higgsfield-director');
const { systemPrompt: treatmentPrompt, buildUserMessage: treatmentMsg, toAnchorBlock } = require('./treatment-director');
const { systemPrompt: audioAnalyzerPrompt, buildUserMessage: audioAnalyzerMsg } = require('./audio-analyzer');
const { systemPrompt: storyDirPrompt, buildUserMessage: storyDirMsg } = require('./higgsfield-story-director');
const { systemPrompt: hfMultishotPrompt, buildUserMessage: hfMultishotMsg } = require('./higgsfield-multishot-director');
const { systemPrompt: descGenPrompt, buildUserMessage: descGenMsg } = require('./description-generator');
const { systemPrompt: editDirPrompt, buildUserMessage: editDirMsg } = require('./tiktok-edit-director');

/**
 * Makes a single Gemini API call directly via the Gemini REST API.
 * Returns the parsed JSON object from the agent's response.
 * Throws on non-2xx HTTP, timeout, or invalid JSON.
 */
function parseAgentResponse(raw) {
  // Strip markdown code fences if present
  const text = raw.replace(/^```(?:json)?\n?|\n?```$/gm, '').trim();
  // Extract outermost JSON object (or array) using balanced bracket counting
  const objStart = text.indexOf('{');
  const arrStart = text.indexOf('[');
  let start, openCh, closeCh;
  if (objStart === -1 && arrStart === -1) {
    console.error('Agent response has no JSON object or array. First 300 chars:', raw.slice(0, 300));
    throw new Error('Agent returned no JSON');
  } else if (objStart === -1) {
    start = arrStart; openCh = '['; closeCh = ']';
  } else if (arrStart === -1) {
    start = objStart; openCh = '{'; closeCh = '}';
  } else {
    start = Math.min(objStart, arrStart);
    openCh = text[start]; closeCh = openCh === '{' ? '}' : ']';
  }
  let depth = 0, inStr = false, esc = false, end = -1;
  for (let i = start; i < text.length; i++) {
    const c = text[i];
    if (esc) { esc = false; continue; }
    if (c === '\\' && inStr) { esc = true; continue; }
    if (c === '"') { inStr = !inStr; continue; }
    if (inStr) continue;
    if (c === openCh) depth++;
    else if (c === closeCh && --depth === 0) { end = i; break; }
  }
  if (end === -1) {
    console.error('Agent JSON truncated (no closing bracket). Response length:', text.length, 'Last 200 chars:', text.slice(-200));
    throw new Error('Agent returned no JSON');
  }
  // Sanitize control characters inside JSON string values
  const extracted = text.slice(start, end + 1);
  let sanitized = '', inString = false, escaped = false;
  for (let i = 0; i < extracted.length; i++) {
    const c = extracted[i];
    if (escaped) { sanitized += c; escaped = false; continue; }
    if (c === '\\' && inString) { sanitized += c; escaped = true; continue; }
    if (c === '"') { inString = !inString; sanitized += c; continue; }
    if (inString) {
      if (c === '\n') { sanitized += '\\n'; continue; }
      if (c === '\r') { sanitized += '\\r'; continue; }
      if (c === '\t') { sanitized += '\\t'; continue; }
      const code = c.charCodeAt(0);
      if (code < 0x20) { sanitized += `\\u${code.toString(16).padStart(4, '0')}`; continue; }
    }
    sanitized += c;
  }
  const parsed = JSON.parse(sanitized);
  if (Array.isArray(parsed)) return { scenes: parsed };
  return parsed;
}

async function callGeminiAgent(systemPrompt, userMessage, signal) {
  const resp = await fetch('https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-goog-api-key': process.env.GEMINI_API_KEY,
    },
    body: JSON.stringify({
      system_instruction: { parts: [{ text: systemPrompt }] },
      contents: [{ role: 'user', parts: [{ text: userMessage }] }],
      generationConfig: { maxOutputTokens: 16000, thinkingConfig: { thinkingBudget: 1024 } },
      safetySettings: [
        { category: 'HARM_CATEGORY_HARASSMENT',        threshold: 'BLOCK_NONE' },
        { category: 'HARM_CATEGORY_HATE_SPEECH',       threshold: 'BLOCK_NONE' },
        { category: 'HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold: 'BLOCK_NONE' },
        { category: 'HARM_CATEGORY_DANGEROUS_CONTENT', threshold: 'BLOCK_NONE' },
      ],
    }),
    signal,
  });

  if (!resp.ok) {
    const errData = await resp.json().catch(() => ({}));
    const err = new Error(`Gemini ${resp.status}: ${errData.error?.message || 'unknown error'}`);
    err.statusCode = resp.status;
    throw err;
  }

  const data = await resp.json();
  const candidate = data.candidates?.[0];
  const finishReason = candidate?.finishReason;
  const raw = candidate?.content?.parts?.[0]?.text || '';
  if (!raw) {
    const blocked = data.promptFeedback?.blockReason;
    console.error('Agent empty response — finishReason:', finishReason, 'blockReason:', blocked);
    throw new Error('Agent returned no JSON');
  }
  // Log finishReason on every response so truncation cause is visible in logs
  if (finishReason && finishReason !== 'STOP') {
    console.warn('Agent finishReason:', finishReason, '— response length:', raw.length);
  }
  return parseAgentResponse(raw);
}

/**
 * Call an Anthropic Claude model with extended thinking enabled.
 * Extended thinking lets the model deliberate before writing the final output —
 * noticeably better for narrative/creative reasoning tasks like MV treatment
 * writing. Response content[] contains thinking blocks BEFORE the text block, so
 * we find the type:'text' block rather than taking content[0].
 *
 * @param {string} model - Anthropic model ID (e.g. 'claude-sonnet-4-6', 'claude-opus-4-6')
 */
async function callClaudeAgent(systemPrompt, userMessage, signal, model = 'claude-sonnet-4-6') {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) throw new Error('ANTHROPIC_API_KEY not configured');

  const resp = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01',
    },
    body: JSON.stringify({
      model,
      max_tokens: 24000,
      thinking: { type: 'enabled', budget_tokens: 8000 },
      system: systemPrompt,
      messages: [{ role: 'user', content: userMessage }],
    }),
    signal,
  });

  if (!resp.ok) {
    const errData = await resp.json().catch(() => ({}));
    const err = new Error(`Anthropic ${resp.status}: ${errData.error?.message || 'unknown error'}`);
    err.statusCode = resp.status;
    throw err;
  }

  const data = await resp.json();
  // Extended thinking: content[] contains thinking blocks then text blocks.
  // Find the text block — thinking blocks are internal reasoning, not the answer.
  const textBlock = data.content?.find(b => b.type === 'text');
  const raw = textBlock?.text || '';
  if (!raw) throw new Error('Agent returned no content');
  return parseAgentResponse(raw);
}

// Backwards-compatible alias — some callers still reference the old name
const callClaudeOpusAgent = callClaudeAgent;

/**
 * Wraps a callAgent call with a per-stage timeout and 1 retry on 429/503.
 * Each attempt gets its own AbortController so the fetch is cancelled when timeout fires.
 * NOTE: Each retry gets a fresh full timeout window (not remaining budget) since no
 * outer Express request timeout exists — this is intentional.
 */
async function callWithTimeout(callAgentFn, systemPrompt, userMessage, timeoutMs) {
  const attempt = async () => {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const result = await callAgentFn(systemPrompt, userMessage, controller.signal);
      clearTimeout(timer);
      return result;
    } catch (err) {
      clearTimeout(timer);
      if (err.name === 'AbortError') {
        throw new Error(`Agent timed out after ${timeoutMs}ms`);
      }
      throw err;
    }
  };

  try {
    return await attempt();
  } catch (err) {
    const is429 = err.statusCode === 429 || (err.message && err.message.includes('429'));
    const is5xx = err.statusCode === 500 || err.statusCode === 503 ||
        (err.message && (err.message.includes('500') || err.message.includes('503')));
    // retry once on rate limit or server error — wait before retrying a 429
    if (is429 || is5xx) {
      const delay = is429 ? 8000 : 1000;
      await new Promise(r => setTimeout(r, delay));
      return await attempt();
    }
    throw err;
  }
}

/**
 * Main pipeline orchestrator.
 * @param {object} params - { mode, userInput, anchorBlock, wardrobeMemory, styleWorldMemory, sceneCount }
 * @param {function} callAgentFn - injectable for testing; defaults to callGeminiAgent
 * @param {function} onProgress - optional callback for stage progress events; defaults to no-op
 */
async function runPipeline(params, callAgentFn = callGeminiAgent, onProgress = () => {}) {
  const {
    mode, userInput,
    anchorBlock = '',
    wardrobeMemory = '', styleWorldMemory = '', locationMemory = '',
    angleMemory = '', lightingMemory = '', influenceMemory = '',
    jewelryMemory = '', headwearMemory = '', shirtReference = '',
  } = params;
  const cfg = modeConfig(mode);
  let n = resolveSceneCount(mode, params.sceneCount);
  // Resolve cinematographer style preset — unknown keys fall back silently to default.
  const stylePreset = (params.stylePreset && CIN_STYLE_PRESETS[params.stylePreset])
    ? params.stylePreset
    : CIN_DEFAULT_PRESET;
  const cinPrompt = cinBuildPrompt(stylePreset);

  // Stage 0: Treatment Director (60s timeout) — only for hf-mv/hf-multishot, non-fatal
  // Analyzes lyrics for emotional arc and produces a musically-aware shot plan.
  // Runs on Claude Opus 4.6 with extended thinking — this is the most
  // reasoning-heavy stage and sets the creative direction for everything else.
  // Falls back silently if Anthropic credits/key are unavailable (non-fatal).
  let enrichedAnchorBlock = anchorBlock;
  let treatment = null;

  if (mode === 'hf-mv' || mode === 'hf-multishot') {
    onProgress({ type: 'stage', stage: 0, name: 'treatment_director', status: 'running' });
    try {
      // Use Claude Opus 4.6 explicitly for the treatment stage — callAgentFn
      // (which defaults to Gemini) is bypassed here because this stage benefits
      // disproportionately from Opus-level reasoning.
      const treatmentAgent = (sys, msg, sig) => callClaudeAgent(sys, msg, sig, 'claude-opus-4-6');
      treatment = await callWithTimeout(
        treatmentAgent, treatmentPrompt,
        treatmentMsg({ userInput, sceneCount: params.sceneCount }),
        60000
      );
      if (treatment?.shot_plan?.length) {
        enrichedAnchorBlock = toAnchorBlock(treatment);
        // Let the treatment's shot count drive the pipeline if user didn't specify
        if (params.sceneCount == null) {
          n = Math.min(cfg.maxN, Math.max(cfg.minN, treatment.shot_plan.length));
        }
      }
      onProgress({ type: 'stage', stage: 0, name: 'treatment_director', status: 'complete' });
      if (treatment && treatment.concept) onProgress({ type: 'treatment', treatment: { concept: treatment.concept, hero_shots: treatment.hero_shots, visual_identity: treatment.visual_identity } });
    } catch (err) {
      // Stage 0 is non-fatal — fall back to generic pipeline behavior
      console.error('Treatment director failed (non-fatal), proceeding without:', err.message);
      onProgress({ type: 'stage', stage: 0, name: 'treatment_director', status: 'skipped' });
    }
  }

  // Stage 1: Scene Architect (30s timeout)
  onProgress({ type: 'stage', stage: 1, name: 'scene_architect', status: 'running' });
  let a1;
  try {
    const raw = await callWithTimeout(callAgentFn, architectPrompt, architectMsg({ userInput, mode, sceneCount: n, anchorBlock: enrichedAnchorBlock, locationMemory, stylePreset }), 30000);
    a1 = Array.isArray(raw.scenes) ? raw.scenes : [];
    onProgress({ type: 'stage', stage: 1, name: 'scene_architect', status: 'complete', count: a1.length });
  } catch (err) {
    throw Object.assign(new Error('scene_architect_failed'), { stage: 1, cause: err });
  }

  // Truncate if over-count
  if (a1.length > n) a1 = a1.slice(0, n);

  // Stage 2: Stylist (45s timeout, retry once on parse error or empty)
  onProgress({ type: 'stage', stage: 2, name: 'stylist', status: 'running' });
  let a2;
  try {
    let raw;
    try {
      raw = await callWithTimeout(callAgentFn, stylistPrompt, stylistMsg({ scenes: a1, wardrobeMemory, styleWorldMemory, jewelryMemory, headwearMemory, shirtReference }), 45000);
    } catch (firstErr) {
      console.error('Stylist first attempt failed, retrying once:', firstErr.message);
      raw = await callWithTimeout(callAgentFn, stylistPrompt, stylistMsg({ scenes: a1, wardrobeMemory, styleWorldMemory, jewelryMemory, headwearMemory, shirtReference }), 45000);
    }
    a2 = Array.isArray(raw.scenes) ? raw.scenes : [];
    if (a2.length === 0) {
      console.error('Stylist returned empty scenes, retrying...');
      const raw2 = await callWithTimeout(callAgentFn, stylistPrompt, stylistMsg({ scenes: a1, wardrobeMemory, styleWorldMemory, jewelryMemory, headwearMemory, shirtReference }), 45000);
      a2 = Array.isArray(raw2.scenes) ? raw2.scenes : [];
    }
    onProgress({ type: 'stage', stage: 2, name: 'stylist', status: 'complete' });
  } catch (err) {
    throw Object.assign(new Error('stylist_failed'), { stage: 2, cause: err });
  }

  // Stage 3: Cinematographer (60s timeout)
  // Merge a1 + a2 by index before passing to cinematographer
  const byIdx2 = {};
  a2.forEach(s => { byIdx2[s.index] = s; });
  const mergedForCin = a1.map(s1 => {
    const s2 = byIdx2[s1.index] || {};
    return { ...s1, ...s2 };
  });

  onProgress({ type: 'stage', stage: 3, name: 'cinematographer', status: 'running' });
  let a3;
  try {
    const raw = await callWithTimeout(callAgentFn, cinPrompt, cinMsg({ scenes: mergedForCin, angleMemory, lightingMemory, influenceMemory }), 60000);
    a3 = Array.isArray(raw.scenes) ? raw.scenes : [];
    onProgress({ type: 'stage', stage: 3, name: 'cinematographer', status: 'complete' });
  } catch (err) {
    throw Object.assign(new Error('cinematographer_failed'), { stage: 3, cause: err });
  }

  // Stage 4: Video Director (45s timeout) — only if mode requires it, non-fatal
  let a4 = [];
  let multishotGenerations = [];
  let video_prompts_failed = false;
  const qaWarnings = [];

  if (cfg.runVideoDirector) {
    const byIdx3 = {};
    a3.forEach(s => { byIdx3[s.index] = s; });
    // uses byIdx2 built during stage 3 merge (both stages share the same function scope)
    const mergedForDir = a1.map(s1 => {
      const s2 = byIdx2[s1.index] || {};
      const s3 = byIdx3[s1.index] || {};
      return {
        index: s1.index,
        image_prompt: {
          label: buildLabel(s1),
          Subject: s2.Subject,
          MadeOutOf: s2.MadeOutOf,
          Arrangement: s3.Arrangement,
          Lighting: s3.Lighting,
          Camera: s3.Camera,
          Background: s3.Background,
          FilmStock: s3.FilmStock,
          Mood: s3.Mood,
          OutputStyle: s3.OutputStyle,
          Composition: s3.Composition,
          ColorPalette: s3.ColorPalette,
          NegativePrompt: s3.NegativePrompt || NEGATIVE_PROMPT,
        },
      };
    }).filter(s => s.image_prompt.Arrangement); // only scenes with a3 data

    // All video modes are Higgsfield/Seedance — Kling path was removed 2026-04-16.
    const isHiggsfield = true;
    const isMultishot = cfg.multishot === true;
    const vdSystemPrompt = isMultishot ? hfMultishotPrompt : hfDirPrompt;
    const vdBuildMsg = isMultishot ? hfMultishotMsg : hfDirMsg;

    // Extract visual lock from treatment so the director can enforce lighting
    // consistency and creative concept across all generated video prompts.
    // Soul ID reference photo handles identity, so prompts should not re-describe appearance.
    const hfTreatmentContext = treatment ? {
      // Keep empty intentionally: Soul ID lock handles identity in the reference photo.
      character: '',
      soulIdLocked: true,
      lighting: treatment.visual_identity?.lighting_philosophy || '',
      wardrobe: '',
      concept: treatment.concept || '',
      emotionalArc: treatment.hero_shots?.join('; ') || '',
    } : undefined;

    onProgress({ type: 'stage', stage: 4, name: isMultishot ? 'multishot_director' : 'video_director', status: 'running' });
    try {
      // Multishot director gets a longer timeout (60s) due to complex grouping logic
      const timeout = isMultishot ? 60000 : 45000;
      const raw = await callWithTimeout(callAgentFn, vdSystemPrompt, vdBuildMsg({ scenes: mergedForDir, treatment: hfTreatmentContext }), timeout);

      if (isMultishot) {
        // Multishot is always Higgsfield-targeted (it's the hf-multishot mode).
        multishotGenerations = Array.isArray(raw.generations) ? raw.generations : [];
        multishotGenerations = multishotGenerations.map((g, gi) => {
          const genNo = g.generation_number || gi + 1;
          const multiPrompt = applyPromptGuardrails(g.multi_shot_prompt, `multishot gen ${genNo}`, qaWarnings, true);
          const shots = Array.isArray(g.shots) ? g.shots.map((shot, si) => {
            const desc = applyPromptGuardrails(shot.description, `multishot gen ${genNo} shot ${si + 1}`, qaWarnings, true);
            return { ...shot, description: desc };
          }) : g.shots;
          return { ...g, multi_shot_prompt: multiPrompt, shots };
        });
      } else {
        a4 = Array.isArray(raw.scenes) ? raw.scenes : [];
        a4 = a4.map(scene => {
          const label = `scene ${scene.index || '?'} video_prompt`;
          const vp = applyPromptGuardrails(scene.video_prompt, label, qaWarnings, true);
          if (typeof vp === 'string') {
            validatePromptFormat(vp, 'PHYSICS_FIRST', label, qaWarnings);
          }
          return { ...scene, video_prompt: vp };
        });
      }
      onProgress({ type: 'stage', stage: 4, name: isMultishot ? 'multishot_director' : 'video_director', status: 'complete' });
    } catch (err) {
      // Stage 4 is non-fatal
      video_prompts_failed = true;
    }
  }

  const result = mergeByIndex(a1, a2, a3, a4, stylePreset);

  // Attach multishot generations as a separate top-level field
  if (multishotGenerations.length > 0) {
    result.multishot_generations = multishotGenerations;
    result.multishot_mode = true;

    // Camera move uniqueness check across all multishot generations
    const allMoves = multishotGenerations.flatMap(g =>
      (g.shots || []).map(s => s.camera).filter(Boolean)
    );
    const seen = new Set();
    const duplicates = [];
    allMoves.forEach(move => {
      if (seen.has(move)) duplicates.push(move);
      seen.add(move);
    });
    if (duplicates.length > 0) {
      pushWarning(qaWarnings, `Duplicate camera moves in multishot: ${[...new Set(duplicates)].join(', ')}`);
    }
  } else {
    // Standard per-scene camera move check
    const cameraMoves = result.scenes
      .map(s => s.hf_camera_movement)
      .filter(Boolean);
    const seen = new Set();
    const duplicates = [];
    cameraMoves.forEach(move => {
      if (seen.has(move)) duplicates.push(move);
      seen.add(move);
    });
    if (duplicates.length > 0) {
      pushWarning(qaWarnings, `Duplicate camera moves detected: ${[...new Set(duplicates)].join(', ')}`);
    }
  }

  if (qaWarnings.length > 0) result.qa_warnings = qaWarnings;
  if (video_prompts_failed) result.video_prompts_failed = true;
  // Attach treatment data so frontend can display the director's vision
  if (treatment) {
    result.treatment = {
      concept: treatment.concept || null,
      hero_shots: treatment.hero_shots || [],
      visual_identity: treatment.visual_identity || null,
    };
  }
  return result;
}

/**
 * Gemini API call that includes an uploaded file (e.g. audio) alongside a text prompt.
 * fileUri and mimeType come from the Gemini Files API upload.
 */
async function callGeminiAgentWithFile(systemPrompt, userMessage, signal, { fileUri, mimeType }) {
  const resp = await fetch('https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-goog-api-key': process.env.GEMINI_API_KEY,
    },
    body: JSON.stringify({
      system_instruction: { parts: [{ text: systemPrompt }] },
      contents: [{
        role: 'user',
        parts: [
          { fileData: { mimeType, fileUri } },
          { text: userMessage },
        ],
      }],
      generationConfig: { maxOutputTokens: 16000, thinkingConfig: { thinkingBudget: 2048 } },
      safetySettings: [
        { category: 'HARM_CATEGORY_HARASSMENT',        threshold: 'BLOCK_NONE' },
        { category: 'HARM_CATEGORY_HATE_SPEECH',       threshold: 'BLOCK_NONE' },
        { category: 'HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold: 'BLOCK_NONE' },
        { category: 'HARM_CATEGORY_DANGEROUS_CONTENT', threshold: 'BLOCK_NONE' },
      ],
    }),
    signal,
  });

  if (!resp.ok) {
    const errData = await resp.json().catch(() => ({}));
    const err = new Error(`Gemini ${resp.status}: ${errData.error?.message || 'unknown error'}`);
    err.statusCode = resp.status;
    throw err;
  }

  const data = await resp.json();
  const raw = data.candidates?.[0]?.content?.parts?.[0]?.text || '';
  if (!raw) throw new Error('Audio analyzer returned no response');

  const text = raw.replace(/^```(?:json)?\n?|\n?```$/gm, '').trim();
  return JSON.parse(text);
}

/**
 * hf-story pipeline: single-agent story chain with optional audio analysis.
 * Stage 0 (optional): Gemini listens to the uploaded track → structured analysis
 * Stage 1: Story Director generates N chained shots with hero frame / continuation flags
 */
async function runStoryChain(params, onProgress = () => {}) {
  const { userInput, fileUri, mimeType, artistDescription, sceneCount, mode } = params;
  const isTiktok = mode === 'tiktok' || mode === 'hf-tiktok';
  const resolveKey = isTiktok ? 'hf-tiktok' : 'hf-story';
  const n = resolveSceneCount(resolveKey, sceneCount);

  let audioAnalysis = null;

  // Stage 0: Audio analysis — only when an uploaded file is present
  if (fileUri && mimeType) {
    onProgress({ type: 'stage', stage: 0, name: 'audio_analyzer', status: 'running' });
    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 90000);
      audioAnalysis = await callGeminiAgentWithFile(
        audioAnalyzerPrompt,
        audioAnalyzerMsg({ concept: userInput }),
        controller.signal,
        { fileUri, mimeType }
      );
      clearTimeout(timer);
      onProgress({ type: 'stage', stage: 0, name: 'audio_analyzer', status: 'complete', audioAnalysis });
    } catch (err) {
      console.error('Audio analysis failed (non-fatal):', err.message);
      onProgress({ type: 'stage', stage: 0, name: 'audio_analyzer', status: 'skipped' });
    }
  }

  // Stage 1: Story Director — single call generates all chained shots
  onProgress({ type: 'stage', stage: 1, name: 'story_director', status: 'running' });
  let raw;
  try {
    raw = await callWithTimeout(
      callClaudeOpusAgent,
      storyDirPrompt,
      storyDirMsg({ audioAnalysis, concept: userInput, artistDescription, sceneCount: n }),
      180000
    );
  } catch (err) {
    throw Object.assign(new Error('story_director_failed'), { stage: 1, cause: err });
  }

  const storyQaWarnings = [];
  const shots = (Array.isArray(raw.shots) ? raw.shots : []).map((shot, idx) => {
    const label = `story shot ${shot.shot_number || idx + 1}`;
    if (shot.video_prompt?.full_prompt) {
      // hf-story is always Higgsfield-targeted — apply Seedance compliance.
      const trimmed = applyPromptGuardrails(shot.video_prompt.full_prompt, label, storyQaWarnings, true);
      // Lightweight format check — physics-first prose is the only allowed format
      validatePromptFormat(trimmed, 'PHYSICS_FIRST', label, storyQaWarnings);
      return { ...shot, video_prompt: { ...shot.video_prompt, full_prompt: trimmed } };
    }
    return shot;
  });

  // Camera move uniqueness check
  const cameraMoves = shots.map(s => s.video_prompt?.camera).filter(Boolean);
  const seen = new Set();
  const duplicates = [];
  cameraMoves.forEach(move => {
    if (seen.has(move)) duplicates.push(move);
    seen.add(move);
  });

  onProgress({ type: 'stage', stage: 1, name: 'story_director', status: 'complete', count: shots.length });

  const result = {
    shots,
    shots_generated: shots.length,
    shots_requested: n,
    mode: isTiktok ? 'hf-tiktok' : 'hf-story',
  };

  // Stage 2 (tiktok only): annotate shots with edit-layer metadata
  // (effects, density, energy arc, signature moment). Additive to physics-first prose.
  if (isTiktok && shots.length > 0) {
    onProgress({ type: 'stage', stage: 2, name: 'edit_director', status: 'running' });
    try {
      const trackMood = audioAnalysis
        ? [audioAnalysis.genre, audioAnalysis.mood, audioAnalysis.tempo].filter(Boolean).join(' / ')
        : '';
      // 120s timeout — edit director uses Claude extended thinking (8K budget)
      // and the per-shot prose adds up; 60s was hitting timeout on 6+ shot
      // TikToks with full-prose payloads. Stage is non-fatal so the only cost
      // of timing out is missing edit metadata.
      const editRaw = await callWithTimeout(
        callClaudeAgent,
        editDirPrompt,
        editDirMsg({ shots, concept: userInput, trackMood }),
        120000,
      );
      if (editRaw && typeof editRaw === 'object') {
        if (Array.isArray(editRaw.edit_specs)) result.edit_specs = editRaw.edit_specs;
        if (Array.isArray(editRaw.effects_inventory)) result.effects_inventory = editRaw.effects_inventory;
        if (Array.isArray(editRaw.density_map)) result.density_map = editRaw.density_map;
        if (editRaw.energy_arc) result.energy_arc = editRaw.energy_arc;
        if (editRaw.signature_moment) result.signature_moment = editRaw.signature_moment;
      }
      onProgress({ type: 'stage', stage: 2, name: 'edit_director', status: 'complete' });
    } catch (err) {
      console.error('Edit director failed (non-fatal):', err.message);
      onProgress({ type: 'stage', stage: 2, name: 'edit_director', status: 'skipped' });
      pushWarning(storyQaWarnings, `Edit director skipped: ${err.message}`);
    }
  }

  if (audioAnalysis) result.audio_analysis = audioAnalysis;
  if (duplicates.length > 0) pushWarning(storyQaWarnings, `Duplicate camera moves: ${[...new Set(duplicates)].join(', ')}`);
  if (storyQaWarnings.length > 0) result.qa_warnings = storyQaWarnings;

  return result;
}

/* Lightweight Gemini text-only call (no file upload, low token budget) */
async function callGeminiText(systemPrompt, userMessage) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 15000);
  try {
    const resp = await fetch('https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-goog-api-key': process.env.GEMINI_API_KEY,
      },
      body: JSON.stringify({
        system_instruction: { parts: [{ text: systemPrompt }] },
        contents: [{ role: 'user', parts: [{ text: userMessage }] }],
        generationConfig: { maxOutputTokens: 500 },
        safetySettings: [
          { category: 'HARM_CATEGORY_HARASSMENT',        threshold: 'BLOCK_NONE' },
          { category: 'HARM_CATEGORY_HATE_SPEECH',       threshold: 'BLOCK_NONE' },
          { category: 'HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold: 'BLOCK_NONE' },
          { category: 'HARM_CATEGORY_DANGEROUS_CONTENT', threshold: 'BLOCK_NONE' },
        ],
      }),
      signal: controller.signal,
    });
    clearTimeout(timer);
    if (!resp.ok) {
      const errData = await resp.json().catch(() => ({}));
      throw new Error(`Gemini ${resp.status}: ${errData.error?.message || 'unknown error'}`);
    }
    const data = await resp.json();
    const text = data.candidates?.[0]?.content?.parts?.[0]?.text || '';
    if (!text) throw new Error('Description generator returned empty response');
    return text.trim();
  } catch (err) {
    clearTimeout(timer);
    throw err;
  }
}

async function expandDescription(params) {
  const { idea, artistDescription } = params;
  return callGeminiText(descGenPrompt, descGenMsg({ idea, artistDescription }));
}

module.exports = { modeConfig, resolveSceneCount, buildLabel, mergeByIndex, buildWardrobeUsed, runPipeline, runStoryChain, expandDescription, callGeminiAgent, callGeminiAgentWithFile, callClaudeAgent, callGeminiText, applyPromptGuardrails, checkSeedanceCompliance, STYLE_PRESETS: CIN_STYLE_PRESETS, DEFAULT_STYLE_PRESET: CIN_DEFAULT_PRESET };
