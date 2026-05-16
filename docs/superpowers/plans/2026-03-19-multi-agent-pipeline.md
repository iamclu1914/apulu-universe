# Multi-Agent Prompt Generation Pipeline — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the single-call Gemini generation with a 4-stage sequential agent pipeline (Scene Architect → Stylist → Cinematographer → Video Director) that produces higher quality, more consistent prompts.

**Architecture:** A new `POST /api/generate-prompts` endpoint in `server.js` orchestrates 4 sequential Gemini calls using focused agent modules in `agents/`. The frontend's 3 main generate functions are updated to call this endpoint; all result rendering is unchanged.

**Tech Stack:** Node.js/Express, CommonJS modules, Node built-in test runner (`node:test`), existing Gemini proxy in `server.js`.

**Spec:** `docs/superpowers/specs/2026-03-18-multi-agent-pipeline-design.md`

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `agents/scene-architect.js` | Scene Architect system prompt + `buildUserMessage()` |
| Create | `agents/stylist.js` | Stylist system prompt + `buildUserMessage()` |
| Create | `agents/cinematographer.js` | Cinematographer system prompt + `buildUserMessage()` |
| Create | `agents/video-director.js` | Video Director system prompt + `buildUserMessage()` |
| Create | `agents/pipeline.js` | Pure helpers + `runPipeline()` async orchestrator |
| Create | `tests/pipeline.test.js` | Unit tests for all pure functions in pipeline.js |
| Modify | `server.js` | Add `POST /api/generate-prompts` route |
| Modify | `index.html` | Update 3 generate functions + loading text cycling |
| Modify | `package.json` | Add `"test"` script |

**Do not touch:** `generateStartEnd()` in index.html (image-to-image, stays on `/api/messages`). The sequential NB2 and single-scene functions (lines ~2177–2310) are also out of scope.

---

## Task 1: Test Infrastructure

**Files:**
- Modify: `package.json`
- Create: `tests/pipeline.test.js` (stub)

- [ ] **Step 1.1: Add test script to package.json**

Open `package.json`. Replace the scripts block:

```json
{
  "name": "mv-prompt-generator",
  "version": "1.0.0",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "test": "node --test tests/**/*.test.js"
  },
  "dependencies": {
    "express": "^4.18.0",
    "dotenv": "^16.0.0"
  }
}
```

- [ ] **Step 1.2: Create stub test file**

```js
// tests/pipeline.test.js
const { describe, it } = require('node:test');
const assert = require('node:assert');

describe('pipeline stub', () => {
  it('test runner works', () => {
    assert.strictEqual(1 + 1, 2);
  });
});
```

- [ ] **Step 1.3: Run tests to confirm infrastructure works**

```bash
npm test
```

Expected output: `▶ pipeline stub` → `✔ test runner works` → `ℹ tests 1` → `ℹ pass 1`

- [ ] **Step 1.4: Commit**

```bash
git add package.json tests/pipeline.test.js
git commit -m "chore: add test infrastructure"
```

---

## Task 2: Pipeline Pure Functions

Build and test all pure (non-async) helpers before touching agents or the server.

**Files:**
- Create: `agents/pipeline.js` (pure functions only, no async yet)
- Modify: `tests/pipeline.test.js`

- [ ] **Step 2.1: Write failing tests for all pure functions**

Replace `tests/pipeline.test.js`:

```js
const { describe, it } = require('node:test');
const assert = require('node:assert/strict');
const {
  modeConfig,
  resolveSceneCount,
  buildLabel,
  mergeByIndex,
  buildWardrobeUsed,
} = require('../agents/pipeline');

describe('modeConfig', () => {
  it('mv runs all 4 agents', () => {
    const cfg = modeConfig('mv');
    assert.equal(cfg.runVideoDirector, true);
    assert.equal(cfg.defaultN, 6);
    assert.equal(cfg.minN, 6);
    assert.equal(cfg.maxN, 8);
  });

  it('nb2 skips video director', () => {
    assert.equal(modeConfig('nb2').runVideoDirector, false);
  });

  it('kling-9grid runs video director, N=9', () => {
    const cfg = modeConfig('kling-9grid');
    assert.equal(cfg.runVideoDirector, true);
    assert.equal(cfg.defaultN, 9);
    assert.equal(cfg.minN, 9);
    assert.equal(cfg.maxN, 9);
  });

  it('kling-startend runs video director, N=2-4', () => {
    const cfg = modeConfig('kling-startend');
    assert.equal(cfg.runVideoDirector, true);
    assert.equal(cfg.defaultN, 2);
    assert.equal(cfg.minN, 2);
    assert.equal(cfg.maxN, 4);
  });

  it('throws on unknown mode', () => {
    assert.throws(() => modeConfig('unknown'), /unknown mode/i);
  });
});

describe('resolveSceneCount', () => {
  it('uses default when not provided', () => {
    assert.equal(resolveSceneCount('mv', undefined), 6);
  });

  it('clamps below min to min', () => {
    assert.equal(resolveSceneCount('mv', 3), 6);
  });

  it('clamps above max to max', () => {
    assert.equal(resolveSceneCount('mv', 12), 8);
  });

  it('uses provided value when in range', () => {
    assert.equal(resolveSceneCount('mv', 7), 7);
  });

  it('9grid is always 9', () => {
    assert.equal(resolveSceneCount('kling-9grid', 5), 9);
  });
});

describe('buildLabel', () => {
  it('constructs label from agent1 scene fields', () => {
    const scene = {
      style_world: 3,
      style_world_name: 'FRENCH LUXURY STREETWEAR',
      location: 'rooftop terrace, Paris',
      time_of_day: 'golden hour',
    };
    const label = buildLabel(scene);
    assert.equal(label, 'WORLD 3 — FRENCH LUXURY STREETWEAR | rooftop terrace, Paris, golden hour');
  });
});

describe('buildWardrobeUsed', () => {
  it('extracts first 4 items from MadeOutOf into shirt/pants/jacket/hat slots', () => {
    const madeOf = [
      'Celine ivory silk bowling shirt',
      'wide-leg ivory trousers',
      'Loro Piana cashmere overcoat',
      'fitted ivory canvas hat',
    ];
    const w = buildWardrobeUsed(madeOf);
    assert.equal(w.shirt, madeOf[0]);
    assert.equal(w.pants, madeOf[1]);
    assert.equal(w.jacket, madeOf[2]);
    assert.equal(w.hat, madeOf[3]);
  });

  it('fills missing slots with "none"', () => {
    const w = buildWardrobeUsed(['only a shirt']);
    assert.equal(w.shirt, 'only a shirt');
    assert.equal(w.pants, 'none');
    assert.equal(w.jacket, 'none');
    assert.equal(w.hat, 'none');
  });
});

describe('mergeByIndex', () => {
  const a1 = [
    { index: 1, style_world: 3, style_world_name: 'FRENCH LUXURY STREETWEAR', location: 'Paris rooftop', time_of_day: 'golden hour', season: 'summer', narrative_beat: 'reflective' },
    { index: 2, style_world: 5, style_world_name: 'UK GRIME / LONDON UNDERGROUND', location: 'estate stairwell', time_of_day: 'night', season: 'winter', narrative_beat: 'defiant' },
  ];
  const a2 = [
    { index: 1, Subject: ['subject desc'], MadeOutOf: ['shirt', 'pants', 'jacket', 'hat'], headwear: 'fitted cap', jewelry: 'gold chain' },
    { index: 2, Subject: ['subject desc 2'], MadeOutOf: ['tracktop', 'shorts'], headwear: 'none', jewelry: 'none' },
  ];
  const a3 = [
    { index: 1, Arrangement: 'THREE-QUARTER LOW', Lighting: 'GOLDEN HOUR NATURAL', Camera: { type: 'cowboy', lens: '85mm f/1.4', body: 'Sony A7R V' }, Background: 'Paris rooftop...', Mood: 'Tyler Mitchell warmth', OutputStyle: 'cinematic photo, 4K ultra-HD', Composition: { framing: 'cowboy shot', angle: 'three-quarter low', focus: 'subject sharp' }, ColorPalette: { dominant: ['#F5F0E8', '#C8922A'], mood: 'warm ivory' }, NegativePrompt: ['cartoonish'] },
    { index: 2, Arrangement: 'LOW HERO ANGLE', Lighting: 'NIGHT STREET PRACTICAL', Camera: { type: 'full body', lens: '35mm f/1.8', body: 'Leica M11' }, Background: 'estate stairwell', Mood: 'Renell Medrano grit', OutputStyle: 'cinematic photo, 4K ultra-HD', Composition: { framing: 'full body', angle: 'low hero', focus: 'subject sharp, background deep shadow' }, ColorPalette: { dominant: ['#1A1A1A', '#FFCC00'], mood: 'high contrast night' }, NegativePrompt: ['cartoonish'] },
  ];
  const a4 = [
    { index: 1, video_prompt: '[0:00-0:03] establishing shot...' },
  ];

  it('merges all 4 agents by index into assembled scenes', () => {
    const result = mergeByIndex(a1, a2, a3, a4);
    assert.equal(result.scenes.length, 2);
    assert.equal(result.scenes_generated, 2);
    assert.equal(result.scenes_requested, 2);

    const s1 = result.scenes[0];
    assert.equal(s1.image_prompt.label, 'WORLD 3 — FRENCH LUXURY STREETWEAR | Paris rooftop, golden hour');
    assert.deepEqual(s1.image_prompt.Subject, ['subject desc']);
    assert.equal(s1.image_prompt.Arrangement, 'THREE-QUARTER LOW');
    assert.equal(s1.video_prompt, '[0:00-0:03] establishing shot...');

    // scene 2: no video_prompt (agent4 only had index 1)
    const s2 = result.scenes[1];
    assert.equal(s2.video_prompt, null);
  });

  it('drops scenes where agent3 data is missing', () => {
    const a3partial = [a3[0]]; // only index 1
    const result = mergeByIndex(a1, a2, a3partial, []);
    assert.equal(result.scenes.length, 1);
    assert.equal(result.scenes_generated, 1);
    assert.equal(result.scenes_requested, 2);
  });

  it('includes style_world and wardrobe_used for frontend localStorage compatibility', () => {
    const result = mergeByIndex(a1, a2, a3, a4);
    const s1 = result.scenes[0];
    assert.equal(s1.style_world, 'WORLD 3 — FRENCH LUXURY STREETWEAR');
    assert.equal(s1.wardrobe_used.shirt, 'shirt');
    assert.equal(s1.wardrobe_used.pants, 'pants');
  });
});
```

- [ ] **Step 2.2: Run tests to confirm they all fail**

```bash
npm test
```

Expected: all tests fail with `Cannot find module '../agents/pipeline'`

- [ ] **Step 2.3: Implement pipeline.js pure functions**

Create `agents/pipeline.js`:

```js
'use strict';

const MODE_CONFIG = {
  mv:             { runVideoDirector: true,  defaultN: 6, minN: 6, maxN: 8 },
  nb2:            { runVideoDirector: false, defaultN: 6, minN: 6, maxN: 8 },
  'kling-9grid':  { runVideoDirector: true,  defaultN: 9, minN: 9, maxN: 9 },
  'kling-startend': { runVideoDirector: true, defaultN: 2, minN: 2, maxN: 4 },
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
function mergeByIndex(a1Scenes, a2Scenes, a3Scenes, a4Scenes) {
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
        MadeOutOf:     s2.MadeOutOf,
        Arrangement:   s3.Arrangement,
        Lighting:      s3.Lighting,
        Camera:        s3.Camera,
        Background:    s3.Background,
        Mood:          s3.Mood,
        OutputStyle:   s3.OutputStyle,
        Composition:   s3.Composition,
        ColorPalette:  s3.ColorPalette,
        NegativePrompt: s3.NegativePrompt,
      },
      video_prompt: m4[i]?.video_prompt ?? null,
    };
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

module.exports = { modeConfig, resolveSceneCount, buildLabel, mergeByIndex, buildWardrobeUsed };
```

- [ ] **Step 2.4: Run tests to confirm all pass**

```bash
npm test
```

Expected: all tests in `mergeByIndex`, `modeConfig`, `resolveSceneCount`, `buildLabel`, `buildWardrobeUsed` suites pass.

- [ ] **Step 2.5: Commit**

```bash
git add agents/pipeline.js tests/pipeline.test.js package.json
git commit -m "feat: add pipeline pure functions with tests"
```

---

## Task 3: Scene Architect Agent

**Files:**
- Create: `agents/scene-architect.js`
- Modify: `tests/pipeline.test.js`

- [ ] **Step 3.1: Write failing test**

Add to `tests/pipeline.test.js`:

```js
const { systemPrompt: architectPrompt, buildUserMessage: architectMsg } = require('../agents/scene-architect');

describe('scene-architect', () => {
  it('exports a non-empty string systemPrompt', () => {
    assert.equal(typeof architectPrompt, 'string');
    assert.ok(architectPrompt.length > 100);
  });

  it('buildUserMessage includes mode, sceneCount, userInput, and anchorBlock', () => {
    const msg = architectMsg({
      userInput: 'reflective lyric about loss',
      mode: 'mv',
      sceneCount: 6,
      anchorBlock: 'Reference photo provided.',
    });
    assert.ok(msg.includes('reflective lyric'));
    assert.ok(msg.includes('6'));
    assert.ok(msg.includes('Reference photo'));
  });

  it('buildUserMessage works without anchorBlock', () => {
    const msg = architectMsg({ userInput: 'test', mode: 'mv', sceneCount: 6 });
    assert.equal(typeof msg, 'string');
    assert.ok(msg.length > 0);
  });
});
```

- [ ] **Step 3.2: Run to confirm failure**

```bash
npm test
```

Expected: `Cannot find module '../agents/scene-architect'`

- [ ] **Step 3.3: Implement scene-architect.js**

Create `agents/scene-architect.js`:

```js
'use strict';

const systemPrompt = `You are a music video creative director. Your job is to read the user's input and design the overall visual scene structure for a multi-scene generation. You do NOT write outfit details, camera angles, or lighting — only the scene framework.

Return ONLY valid JSON, nothing else. No markdown, no code fences.

OUTPUT SCHEMA:
{
  "scenes": [
    {
      "index": 1,
      "style_world": 3,
      "style_world_name": "FRENCH LUXURY STREETWEAR",
      "location": "rooftop terrace, Paris",
      "time_of_day": "golden hour",
      "season": "summer",
      "narrative_beat": "reflective, looking out over the city alone"
    }
  ]
}

RULES:
- Assign a unique style_world number (1–8) to each scene. No two scenes may share the same style world number.
- time_of_day must be one of: morning, midday, golden hour, dusk, night
- season must be one of: spring, summer, autumn, winter
- narrative_beat is one sentence describing the emotional or visual mood of the scene

STYLE WORLDS:
WORLD 1 — QUIET LUXURY / OLD MONEY: Loro Piana, Brunello Cucinelli, Zegna, The Row. Muted palette, no logos, relaxed silhouettes.
WORLD 2 — EUROPEAN HIGH FASHION EDGE: Rick Owens, Ann Demeulemeester, Yohji Yamamoto, Julius. Avant-garde silhouettes, dark palette.
WORLD 3 — FRENCH LUXURY STREETWEAR: Celine, AMI Paris, Casablanca, Jacquemus Homme. Fluid fabrics, resort-print, ivory/cobalt/terracotta palette.
WORLD 4 — JAPANESE STREET PRECISION: Needles, Wacko Maria, Kapital, Neighborhood, visvim. Reconstructed, patchwork, indigo/rust palette.
WORLD 5 — UK GRIME / LONDON UNDERGROUND: Corteiz, Palace, Trapstar, Martine Rose. Oversized, technical fabrics, acid yellow/royal blue/concrete grey palette.
WORLD 6 — AMERICANA WORKWEAR ELEVATED: Carhartt WIP, Engineered Garments, Noah, Filson. Chore coats, selvedge denim, tan/forest/burgundy palette.
WORLD 7 — SPORT LUXURY / ATHLETE FASHION: Representing, Rhude, Fear of God Athletics, Nike x Nocta. Premium fleece, track jackets, cobalt/cream/jet black palette.
WORLD 8 — AFRO-LUXURY / DIASPORA COUTURE: Kenneth Ize, Thebe Magugu, Daily Paper, Dapper Dan. Bold kente, brocade, gold/emerald/deep violet palette.

Assign worlds that fit the narrative mood. A night club scene suits World 5. A luxury penthouse suits World 1. A Tokyo alley suits World 4.`;

function buildUserMessage({ userInput, mode, sceneCount, anchorBlock = '' }) {
  const modeNote = mode === 'kling-9grid'
    ? 'This is for a 9-grid Instagram layout. All scenes should form a cohesive visual story.'
    : mode === 'kling-startend'
    ? 'This is for Kling start+end frame pairs. Scenes should represent distinct moments of motion or position change.'
    : 'This is for a music video with image and video prompts per scene.';

  return `${anchorBlock ? anchorBlock + '\n\n' : ''}${modeNote}

Generate exactly ${sceneCount} scenes for the following:

${userInput}

Return the scenes JSON array with exactly ${sceneCount} objects, each with all required fields.`;
}

module.exports = { systemPrompt, buildUserMessage };
```

- [ ] **Step 3.4: Run tests**

```bash
npm test
```

Expected: all scene-architect tests pass.

- [ ] **Step 3.5: Commit**

```bash
git add agents/scene-architect.js tests/pipeline.test.js
git commit -m "feat: add scene-architect agent module"
```

---

## Task 4: Stylist Agent

**Files:**
- Create: `agents/stylist.js`
- Modify: `tests/pipeline.test.js`

- [ ] **Step 4.1: Write failing tests**

Add to `tests/pipeline.test.js`:

```js
const { systemPrompt: stylistPrompt, buildUserMessage: stylistMsg } = require('../agents/stylist');

describe('stylist', () => {
  it('exports a non-empty string systemPrompt', () => {
    assert.equal(typeof stylistPrompt, 'string');
    assert.ok(stylistPrompt.length > 500);
  });

  it('buildUserMessage includes all scene briefs as JSON', () => {
    const scenes = [
      { index: 1, style_world: 3, style_world_name: 'FRENCH LUXURY STREETWEAR', location: 'Paris rooftop', time_of_day: 'golden hour', season: 'summer', narrative_beat: 'reflective' }
    ];
    const msg = stylistMsg({ scenes, wardrobeMemory: '', styleWorldMemory: '' });
    assert.ok(msg.includes('FRENCH LUXURY STREETWEAR'));
    assert.ok(msg.includes('"index": 1'));
  });

  it('buildUserMessage includes wardrobeMemory and styleWorldMemory when provided', () => {
    const msg = stylistMsg({
      scenes: [{ index: 1, style_world: 1, style_world_name: 'QUIET LUXURY', location: 'penthouse', time_of_day: 'dusk', season: 'autumn', narrative_beat: 'solitary' }],
      wardrobeMemory: 'WARDROBE MEMORY — Shirts used: ivory turtleneck',
      styleWorldMemory: 'STYLE WORLD MEMORY — Worlds used: WORLD 1',
    });
    assert.ok(msg.includes('WARDROBE MEMORY'));
    assert.ok(msg.includes('STYLE WORLD MEMORY'));
  });
});
```

- [ ] **Step 4.2: Run to confirm failure**

```bash
npm test
```

- [ ] **Step 4.3: Implement stylist.js**

Create `agents/stylist.js`. The system prompt contains all outfit rules extracted from `buildPromptSystem()` in `index.html` lines 1789–1852. Key sections to include:

```js
'use strict';

const systemPrompt = `You are a celebrity stylist — you style this artist the way Law Roach styles Zendaya or Zerina Akers styles Beyoncé. Every scene is a deliberate fashion MOMENT.

Return ONLY valid JSON, nothing else. No markdown, no code fences.

OUTPUT SCHEMA:
{
  "scenes": [
    {
      "index": 1,
      "Subject": ["male subject, deep brown skin with visible pores and subsurface scattering on ears, defined facial bone structure, low-cut fade with sharp edge-up, focused expression, athletic build"],
      "MadeOutOf": ["Celine by Hedi Slimane ivory silk bowling shirt, relaxed fit with compression folds at shoulder, ribbed collar", "wide-leg ivory tailored trousers with a hard crease, sitting high on the waist", "Air Jordan 1 Retro High OG 'Royal' in navy/black/white, flat and grounded", "fitted ivory canvas bucket hat, soft brim"],
      "headwear": "fitted ivory canvas bucket hat, soft brim pulled forward",
      "jewelry": "thick gold Cuban link chain resting flat against the chest"
    }
  ]
}

SUBJECT RULES:
- Subject array: describe the character's skin tone, facial features (exact structure), hair shape and texture, expression, and build. Include skin realism micro-details: visible pores, peach fuzz, subsurface scattering on ears and fingers, natural skin tone variations, faint vascularity on temples. Never describe clothing in Subject.

MADEOUTOF RULES:
- One item per array element: brand + specific fabric type + colorway + fit + fabric physics
- Include compression folds where fabric meets skin, realistic material tension on curves, visible fiber texture
- Include top, bottom, footwear (exact model + colorway from APPROVED LIST below), and any accessories
- Apply style world, color lock, and headwear rules here

STYLE WORLD ASSIGNMENT:
Each scene brief specifies a style_world number. Apply the exact brand universe and aesthetic for that world:
WORLD 1 — QUIET LUXURY: Loro Piana, Brunello Cucinelli, Zegna, The Row, Kiton, Brioni. Cashmere topcoats, fine-knit turtlenecks, wide-leg ivory trousers. Muted palette: oat, ecru, chalk, camel.
WORLD 2 — EUROPEAN HIGH FASHION EDGE: Rick Owens, Ann Demeulemeester, Yohji Yamamoto, Julius, Issey Miyake. Asymmetric hems, draped capes, deconstructed tailoring. Charcoal, dark olive, oxblood.
WORLD 3 — FRENCH LUXURY STREETWEAR: Celine, AMI Paris, Casablanca, Drôle de Monsieur, Jacquemus Homme. Silk bowling shirts, wide-leg trousers, resort-print co-ords. Ivory, cobalt, terracotta, champagne.
WORLD 4 — JAPANESE STREET PRECISION: Needles, Wacko Maria, Kapital, Neighborhood, visvim, Sacai. Reconstructed western shirts, sashiko-stitched denim, intarsia knitwear. Indigo, rust, forest green, raw ecru.
WORLD 5 — UK GRIME / LONDON UNDERGROUND: Corteiz, Palace, Trapstar, Martine Rose. Oversized stadium jackets, drill-era tracksuits, puffer vests. Acid yellow, royal blue, fire red, concrete grey.
WORLD 6 — AMERICANA WORKWEAR ELEVATED: Carhartt WIP, Engineered Garments, Noah, Filson, orSlow. Chore coats, selvedge denim, thermal henleys, CPO shirts. Tan, forest, burgundy, faded navy.
WORLD 7 — SPORT LUXURY / ATHLETE FASHION: Representing, Rhude, Fear of God Athletics, New Balance x Teddy Santis, Nike x Nocta. Premium fleece sets, track jackets, nylon windbreakers. Cobalt, cream, cardinal, jet black.
WORLD 8 — AFRO-LUXURY / DIASPORA COUTURE: Kenneth Ize, Thebe Magugu, Daily Paper, Studio 189, Orange Culture. Bold kente blazers, adire-dyed trousers, custom monogram overcoats. Gold, emerald, rust, deep violet.

BRAND NO-REPEAT RULE: No clothing brand may appear more than once across all scenes. Cycle through ALL brands listed in each world before repeating. Prioritize less-familiar brands.

CLOTHING REALISM:
- Describe silhouette, drape, and fabric weight — NOT fine surface patterns, small text logos, or intricate embroidery
- Use solid colorways or large-scale design elements only
- When a garment has a logo, describe it as a bold, single-color, large-scale, graphically simple mark only
- For pattern-heavy brands (Wacko Maria, Kapital, Needles), describe pattern as bold large-scale simplified version

SHOE COLOR-LOCK RULE — NO EXCEPTIONS:
The shoe's dominant color MUST match the shirt's dominant color. Use this lookup:
Orange/rust shirt → Air Jordan 1 "Shattered Backboard" or Nike Dunk Low "Syracuse"
Navy/cobalt shirt → Air Jordan 1 "Royal" or Air Jordan 12 "French Blue"
Black shirt → Air Jordan 4 "Black Cat" or Nike Air Force 1 Low "Black"
White/ivory shirt → Air Jordan 11 "Concord" or Nike Air Force 1 Low "White"
Red shirt → Air Jordan 5 "Fire Red" or Air Jordan 6 "Carmine"
Forest green shirt → Nike Dunk Low "Gorge Green" or Air Jordan 1 "Pine Green"
Olive/army green shirt → Air Jordan 4 "Taupe Haze" or Nike Air Max 90 "Medium Olive"
Camel/tan/brown shirt → Air Jordan 3 "Palomino" or Nike Air Force 1 "Wheat"
Grey shirt → Air Jordan 3 "Cool Grey" or Nike Air Max 90 "Wolf Grey"
Gold/yellow shirt → Air Jordan 4 "Lightning" or Nike Air Force 1 "Optic Yellow"
Purple shirt → Air Jordan 1 "Court Purple" or Nike Dunk Low "Psychic Purple"
Pink shirt → Air Jordan 3 "Pink Quartz" or Nike Dunk Low "Pink Foam"
SHOE MODEL NO-REPEAT: No shoe model may be used more than once across all scenes.

HEADWEAR: In roughly half of all scenes, the artist wears a hat matching the style world. Rotate through: fitted cap, snapback, vintage dad hat, wool bucket hat, vintage baseball cap, skully/beanie (cold weather), wide-brim felt fedora (luxury). When no hat is worn, describe hair intentionally (edge-up, waves, locs).

JEWELRY: Structurally simple only. "A thick gold Cuban link chain resting flat against the chest." "A clean silver watch on the left wrist." One or two accessories maximum. Never fine chain links or complex watch faces.

WINTER OUTERWEAR RULE: In any winter or cold-weather scene, the outer layer must be a North Face jacket. Choose from: North Face Nuptse 700-fill puffer, McMurdo Parka, Baltoro Heavy Down, 1996 Retro Nuptse, or Denali fleece. Name exact model and colorway.`;

function buildUserMessage({ scenes, wardrobeMemory = '', styleWorldMemory = '' }) {
  return `${wardrobeMemory}${styleWorldMemory}You are styling the artist for the following scenes. For each scene, assign a complete outfit following all rules above.

SCENE BRIEFS:
${JSON.stringify(scenes, null, 2)}

Return a scenes array with exactly ${scenes.length} objects — one per scene index above. Each object must have: index, Subject, MadeOutOf, headwear, jewelry.`;
}

module.exports = { systemPrompt, buildUserMessage };
```

- [ ] **Step 4.4: Run tests**

```bash
npm test
```

Expected: all stylist tests pass.

- [ ] **Step 4.5: Commit**

```bash
git add agents/stylist.js tests/pipeline.test.js
git commit -m "feat: add stylist agent module"
```

---

## Task 5: Cinematographer Agent

**Files:**
- Create: `agents/cinematographer.js`
- Modify: `tests/pipeline.test.js`

- [ ] **Step 5.1: Write failing tests**

Add to `tests/pipeline.test.js`:

```js
const { systemPrompt: cinPrompt, buildUserMessage: cinMsg } = require('../agents/cinematographer');

describe('cinematographer', () => {
  it('exports a non-empty string systemPrompt over 800 chars', () => {
    assert.equal(typeof cinPrompt, 'string');
    assert.ok(cinPrompt.length > 800);
  });

  it('systemPrompt references all 26 camera angle names', () => {
    assert.ok(cinPrompt.includes('LOW HERO ANGLE'));
    assert.ok(cinPrompt.includes('BIRD\'S EYE OVERHEAD'));
    assert.ok(cinPrompt.includes('TELEPHOTO COMPRESSED'));
    assert.ok(cinPrompt.includes('DUTCH TILT AGGRESSIVE'));
  });

  it('systemPrompt references all 18 lighting setup names', () => {
    assert.ok(cinPrompt.includes('GOLDEN HOUR NATURAL'));
    assert.ok(cinPrompt.includes('BUTTERFLY / GLAMOUR'));
    assert.ok(cinPrompt.includes('STRIPBOX EDGE'));
    assert.ok(cinPrompt.includes('TOP LIGHT DRAMATIC'));
  });

  it('buildUserMessage includes merged scene data', () => {
    const scenes = [{ index: 1, style_world: 3, location: 'Paris rooftop', time_of_day: 'golden hour', season: 'summer', narrative_beat: 'reflective', Subject: ['subject'], MadeOutOf: ['shirt', 'pants'] }];
    const msg = cinMsg({ scenes });
    assert.ok(msg.includes('Paris rooftop'));
    assert.ok(msg.includes('"index": 1'));
  });
});
```

- [ ] **Step 5.2: Run to confirm failure**

```bash
npm test
```

- [ ] **Step 5.3: Implement cinematographer.js**

Create `agents/cinematographer.js`:

```js
'use strict';

const systemPrompt = `You are a Director of Photography for a music video production. Your job is to determine the visual and technical specifications for each scene based on the scene brief and the locked outfit.

Return ONLY valid JSON, nothing else. No markdown, no code fences.

OUTPUT SCHEMA:
{
  "scenes": [
    {
      "index": 1,
      "Arrangement": "THREE-QUARTER LOW angle — subject standing with weight shifted to left hip, arms relaxed at sides, looking past camera to the right. Body positioned at a slight diagonal, giving natural asymmetry.",
      "Lighting": "GOLDEN HOUR NATURAL — low sun at 15 degrees above horizon, warm amber rim on subject's right shoulder and hair. Face lit by soft reflected fill from nearby rooftop surface. Long directional shadows stretching left across the terrace.",
      "Camera": { "type": "cowboy shot (mid-thigh to head)", "lens": "85mm f/1.4", "body": "Sony A7R V" },
      "Background": "Paris rooftop terrace, zinc chimney stacks and Haussmann rooflines stretching to the horizon. Sky a saturated gradient of amber and rose. Background softly dissolved by shallow depth of field.",
      "Mood": "carries Tyler Mitchell's airy editorial warmth — soft natural light, subjects feel present and unguarded, pastel tones with a dreamy quality",
      "OutputStyle": "cinematic photo, 4K ultra-HD, 4:5 aspect ratio",
      "Composition": { "framing": "cowboy shot", "angle": "three-quarter low (camera at waist height, angled up 15 degrees)", "focus": "subject sharp with clean edge definition, rooftops and sky dissolved into smooth bokeh" },
      "ColorPalette": { "dominant": ["#F5F0E8", "#C8922A"], "mood": "warm ivory and gold, sun-drenched softness with long amber shadows" },
      "NegativePrompt": ["cartoonish", "illustrated", "soft focus", "blurry artifacts", "distorted hands", "extra limbs", "face warping", "AI artifacts", "anime style", "warped clothing", "morphed fabric", "melting garments", "distorted patterns", "illegible text on clothing", "fused fabric layers", "unrealistic drape", "plastic-looking material", "impossible lighting", "mismatched environments", "floating subjects", "distorted shoes", "melted footwear", "floating jewelry", "tangled chains", "cloned background figures", "inconsistent shadows", "wrong season clothing", "cloned foreground figures", "distorted text on clothing", "warped logos"]
    }
  ]
}

CAMERA ANGLES — choose one per scene, rotate across scenes (no same angle twice in a set):
1. LOW HERO ANGLE — camera at knee or hip level looking up at the subject, creating dominance and scale
2. EYE-LEVEL INTIMATE — camera at subject's eye level, straight on or slight 3/4 turn
3. THREE-QUARTER LOW — camera at waist height angled up at 15-20 degrees, the classic hip-hop portrait angle
4. OVER-THE-SHOULDER — camera positioned behind and beside the subject looking past them toward the environment
5. DUTCH TILT — camera rotated 10-15 degrees clockwise, tension or swagger
6. TIGHT CLOSE-UP — camera fills frame with face from chin to hairline, 85mm or longer
7. WIDE ENVIRONMENTAL — camera pulls back to show subject as part of the location, 35mm
8. COWBOY SHOT — framed from mid-thigh up
9. FIRST-PERSON POV — camera at the subject's eye level looking out at what they see
10. MIRROR SELFIE — subject stands in front of a full-length mirror, phone held at chest or face height
11. LOOKING DOWN TOP-DOWN — camera positioned directly above looking straight down at hands or an object
12. SEATED CANDID — subject seated, camera at eye level or slightly above, body turned slightly
13. WALKING MID-STRIDE — camera at eye level facing the subject as they walk toward the lens
14. THROUGH GLASS / WINDOW — camera outside looking in through glass, reflections add authenticity
15. DETAIL CLOSE-UP — extreme tight shot of a single object filling 70% of the frame
16. LEANING CASUAL — subject leaning against a wall, car door, counter, or railing
17. BIRD'S EYE OVERHEAD — camera directly above, omniscient/disorienting, subject against floor or ground texture
18. HIGH ANGLE VULNERABLE — camera elevated looking down, subject appears human and approachable
19. EXTREME CLOSE-UP DETAIL — single feature fills frame (eye, jawline, jewelry, fabric texture)
20. TELEPHOTO COMPRESSED — 200mm+, background flattened dramatically into subject as abstract color wash
21. STEADICAM FOLLOW — camera gliding behind or beside subject mid-stride through environment
22. CRANE REVEAL — camera descends from high to eye level or rises to expose environment scale
23. TWO-SHOT RELATIONAL — two subjects framed together, spatial relationship and dynamic visible
24. MACRO TEXTURE — extreme close-up of surface (fabric weave, sneaker sole, skin pores, chain links)
25. SPLIT FRAME — subject occupies one half, environment or object the other
26. DUTCH TILT AGGRESSIVE — 20-45 degree rotation, full swagger or instability statement

LIGHTING SETUPS — choose one per scene, vary across scenes:
1. GOLDEN HOUR NATURAL — low sun 10-20 degrees, warm 2800-3200K backlight, amber rim on shoulder and hair
2. BLUE HOUR / DUSK — 10 min after sunset, cerulean sky 8000K + warm storefront practicals 2700K
3. NIGHT STREET PRACTICAL — sodium vapor 2100K, neon fill, car headlight rim, high contrast deep shadows
4. ARENA / STADIUM — overhead LED floods 5600K + warm courtside practicals 3200K
5. OVERCAST DIFFUSED — cloud cover as softbox, 6500K, even exposure, colors saturated without blown highlights
6. REMBRANDT PORTRAIT — single key at 45 degrees above and to one side, triangle of light on shadowed cheek
7. STUDIO BEAUTY DISH — large octabox or beauty dish at 45 degrees, clean and even
8. FLASH FILL OUTDOOR — ambient natural exposure plus direct or bounced strobe fill, Gunner Stahl editorial look
9. BUTTERFLY / GLAMOUR — key centered directly above subject, symmetrical butterfly shadow under nose
10. CLAMSHELL BEAUTY — key above + fill below both facing subject, removes all shadows
11. SPLIT LIGHT — key at exactly 90 degrees, half face lit and half dark, high drama editorial
12. SHORT LIGHTING — key illuminates the side of face turned away from camera, narrows face, increases contrast
13. THREE-POINT STUDIO — key at 45 degrees + fill opposite at 50% intensity + back rim light
14. BACK / RIM LIGHT HALO — single light behind at 45-90 degrees, glowing edge on hair and shoulders
15. HARSH EDITORIAL HARD LIGHT — specular directional key, defined shadows with sharp edges
16. STRIPBOX EDGE — narrow vertical striplight at side, edge definition and dramatic shadow fall-off
17. GEL / COLOR MOOD — colored gels (magenta, cobalt, amber) for music video atmosphere
18. TOP LIGHT DRAMATIC — single light directly overhead, deep eye socket shadows, strong cheekbone definition

CAMERA BODY + LENS SELECTION:
- Tight close-up portrait → 85mm f/1.2 or 135mm f/1.8 on Sony A7R V or Canon EOS R5
- Medium portrait → 85mm f/1.4 or 105mm f/1.4 on Sony A7R V
- Full-length outfit shot → 50mm f/1.4 at 8-10 feet on Canon EOS R5
- Environmental wide shot → 35mm f/1.8 on Leica M11 or Nikon Z9
- Low angle hero → 24-35mm f/2.8 at ground level on Canon 1DX Mark III
- Telephoto compression → 200mm f/2.8 on Nikon Z9 or Sony A7R V
- Luxury/fashion editorial → Hasselblad X2D 100C with 90mm f/2.5 or Phase One IQ4 150MP

SCENE CONSISTENCY: Every element in the scene must physically belong to the same real-world location. Do not mix incompatible environments.

LIGHTING REALISM: ONLY use light sources that physically exist in the described environment. Outdoor daytime → directional sunlight. Night streets → sodium streetlights, neon, car headlights. Never apply "soft natural fill" inside a dark club.

BACKGROUND DEPTH OF FIELD: Describe background elements as naturally out of focus. "The crowd softly blurred behind him by shallow depth of field." Real fast-lens photography always renders busy backgrounds this way.

PEOPLE IN FRAME: When the scene includes other people, FOREGROUND PRESENCE IS MANDATORY — always describe a partially visible figure, shoulder, arm, or back positioned between the lens and the subject. This is non-negotiable for scenes at venues, parties, or public spaces.

POSE PHYSICS: All body positions must be gravity-consistent and physically natural. No floating or anatomically impossible angles.

SOCIAL BODY LANGUAGE: When the scene includes other people, the subject's pose and expression must reflect genuine social awareness — not squared to the camera in isolation.

PHOTOGRAPHER REFERENCES (rotate across scenes):
CAM KIRK → warm, intimate, golden-toned hip-hop portraits, rich shadow detail
TYLER MITCHELL → soft natural light, airy and dream-like, pastel tones
RENELL MEDRANO → high-contrast gritty urban realism, flash-assisted, raw texture
GUNNER STAHL → direct flash candid, hard light, honest and unposed
DANA SCRUGGS → dramatic and powerful, deep shadows, strong silhouettes
SHANIQWA JARVIS → documentary intimacy, soft grain, warm and human
QUIL LEMONS → painterly and ethereal, soft diffused light
KERBY JEAN-RAYMOND → bold editorial fashion, strong graphic composition

SEASON AND WEATHER: Outfit weight, environment texture, and light quality must all agree on the same season. Never put a puffer jacket in a summer outdoor heat scene.

TIME OF DAY COMMITMENT: Every element must match the committed time of day. NBA and concert scenes are always evening or night.`;

function buildUserMessage({ scenes }) {
  return `You are setting the visual and technical specifications for the following scenes. Each scene brief includes the location, time of day, season, narrative beat, and the locked outfit.

SCENES WITH OUTFIT DATA:
${JSON.stringify(scenes, null, 2)}

Return a scenes array with exactly ${scenes.length} objects — one per scene index above. Each object must include all required fields: index, Arrangement, Lighting, Camera, Background, Mood, OutputStyle, Composition, ColorPalette, NegativePrompt.`;
}

module.exports = { systemPrompt, buildUserMessage };
```

- [ ] **Step 5.4: Run tests**

```bash
npm test
```

Expected: all cinematographer tests pass.

- [ ] **Step 5.5: Commit**

```bash
git add agents/cinematographer.js tests/pipeline.test.js
git commit -m "feat: add cinematographer agent module"
```

---

## Task 6: Video Director Agent

**Files:**
- Create: `agents/video-director.js`
- Modify: `tests/pipeline.test.js`

- [ ] **Step 6.1: Write failing tests**

Add to `tests/pipeline.test.js`:

```js
const { systemPrompt: dirPrompt, buildUserMessage: dirMsg } = require('../agents/video-director');

describe('video-director', () => {
  it('exports a non-empty string systemPrompt over 500 chars', () => {
    assert.equal(typeof dirPrompt, 'string');
    assert.ok(dirPrompt.length > 500);
  });

  it('systemPrompt references camera movement vocabulary', () => {
    assert.ok(dirPrompt.includes('Dolly'));
    assert.ok(dirPrompt.includes('Steadicam'));
    assert.ok(dirPrompt.includes('Speed Ramp'));
  });

  it('systemPrompt references transition types', () => {
    assert.ok(dirPrompt.includes('Smash Cut'));
    assert.ok(dirPrompt.includes('Match Cut'));
  });

  it('buildUserMessage includes scene data', () => {
    const scenes = [{
      index: 1,
      image_prompt: { label: 'WORLD 3 | Paris rooftop', Subject: ['subject'], MadeOutOf: ['shirt'], Arrangement: 'cowboy shot', Lighting: 'GOLDEN HOUR', Camera: { type: 'cowboy', lens: '85mm', body: 'Sony' }, Background: 'rooftop', Mood: 'warm', OutputStyle: '4K', Composition: { framing: 'cowboy', angle: 'three-quarter', focus: 'sharp' }, ColorPalette: { dominant: ['#fff'], mood: 'warm' }, NegativePrompt: [] }
    }];
    const msg = dirMsg({ scenes });
    assert.ok(msg.includes('Paris rooftop'));
  });
});
```

- [ ] **Step 6.2: Run to confirm failure**

```bash
npm test
```

- [ ] **Step 6.3: Implement video-director.js**

Create `agents/video-director.js`:

```js
'use strict';

const systemPrompt = `You are a Kling 3.0 video direction specialist. You receive fully assembled scene descriptions (with locked outfit, camera angle, and lighting) and write production-quality Kling video prompts.

Return ONLY valid JSON, nothing else. No markdown, no code fences.

OUTPUT SCHEMA:
{
  "scenes": [
    {
      "index": 1,
      "video_prompt": "[0:00-0:03] ESTABLISHING — Maintaining subject's identical facial features, bone structure, and skin tone throughout — Paris rooftop terrace, amber light, fog of golden hour haze. Wide shot, camera dollies in slowly. Subject stands still, direct eyeline to camera, controlled energy. Smash Cut on beat. →\n[0:03-0:08] VERSE — Maintaining subject's identical facial features, bone structure, and skin tone throughout — Medium close-up, steadicam tracks left with subject mid-stride. Natural energy, off-screen right eyeline. Hard cut on downbeat. →\n[0:08-0:13] CHORUS — Maintaining subject's identical facial features, bone structure, and skin tone throughout — Tight close-up, face fills frame. Camera holds static. Speed ramps to slow-motion. Explosive energy, jaw set, direct camera contact. Freeze one frame on impact, then dissolve. →\n[0:13-0:15] END STATE — Maintaining subject's identical facial features, bone structure, and skin tone throughout — Wide crane shot rising. Subject center frame, city behind. Motion holds in slow-motion. Scene locked on final frame."
    }
  ]
}

CHARACTER CONSISTENCY — NON-NEGOTIABLE:
Every timestamped shot block MUST begin with "Maintaining subject's identical facial features, bone structure, and skin tone throughout —" before any motion description.

ATTIRE LOCK:
Describe the subject's outfit exactly as specified in the provided image_prompt.MadeOutOf field. Do NOT invent, substitute, or alter any clothing item.

SHOT STRUCTURE:
- 3-5 timestamped blocks total
- MAX 15 seconds total duration
- Each block: [timestamp] LABEL — [character consistency lock] — [environment/setup]. [shot type], [camera movement]. [subject energy], [eyeline]. [transition type]. →
- Final block must include an explicit end state (e.g., "scene locked on final frame", "camera holds on subject")

CAMERA MOVEMENT VOCABULARY — name one per block:
Dolly In / Out — camera moves physically closer or farther on a track
Pan Left / Right — horizontal pivot from fixed position
Tilt Up / Down — vertical pivot from fixed position
Orbital / 360° — camera rotates around subject in circular motion
Crane Rise / Descend — camera sweeps through high arc
Steadicam Follow — smooth gimbal tracking through space
Handheld — natural jitter, raw documentary energy
Whip Pan — fast horizontal blur between subjects
Rack Focus — focus shifts from foreground to background element
Speed Ramp — footage transitions from normal speed to slow-motion or fast-motion

TRANSITION TYPES — name one at the end of each block:
Smash Cut — on exact percussion hit or bass drop, maximum impact
Hard Cut — clean on-beat cut, default transition
Match Cut — two shots share same composition or gesture across scenes
Dissolve — smooth connection between thematically linked moments
Freeze Frame — holds on impact moment 1-3 frames then resumes motion
Whip Pan Transition — fast horizontal blur bridges two subjects or locations
Jump Cut — repetitive action emphasis, edgy sections
Fade to Black — major scene separation, emotional pause

AUDIO-VISUAL SYNC PACING:
Verse sections: shot duration 3-5 seconds, moderate cuts, phrase-aligned
Pre-chorus: 2-3 seconds, increasing pace, building anticipation
Chorus: 1-2 seconds, fast on-beat smash cuts
Bridge: 4-6 seconds, shift in visual approach
Outro: 5-8 seconds, slow dissolves or crane pull-back

PERFORMANCE DIRECTION:
Energy: Static / Subtle / Natural / Energetic / Explosive
Eyeline: direct to camera / off-screen left / off-screen right / downward / upward
Body: strut / slink / stomp / controlled stillness / mid-stride
Micro-expression: furrowed brow / set jaw / soft eyes / direct intensity / open expression

NEGATIVE: Every video_prompt must end with "Negative: smiling, laughing, cartoonish, face warping, face morphing, identity shift, facial distortion, changing facial structure, inconsistent skin tone, blurry faces, AI artifacts, deepfake artifacts, face sliding, flickering features, added accessories, props not in reference, fast motion, camera spin, rapid pan, handheld shake if not specified"`;

function buildUserMessage({ scenes }) {
  return `Write Kling 3.0 video prompts for the following fully assembled scenes. Use the image_prompt fields to understand the visual setup, outfit, and mood for each scene.

ASSEMBLED SCENES:
${JSON.stringify(scenes, null, 2)}

Return a scenes array with exactly ${scenes.length} objects — one per scene index above. Each object must include: index, video_prompt.`;
}

module.exports = { systemPrompt, buildUserMessage };
```

- [ ] **Step 6.4: Run tests**

```bash
npm test
```

Expected: all video-director tests pass.

- [ ] **Step 6.5: Commit**

```bash
git add agents/video-director.js tests/pipeline.test.js
git commit -m "feat: add video-director agent module"
```

---

## Task 7: Pipeline runPipeline() + callAgent()

Add the async orchestration to `agents/pipeline.js`.

**Files:**
- Modify: `agents/pipeline.js`
- Modify: `tests/pipeline.test.js`

- [ ] **Step 7.1: Write failing tests for runPipeline with mocked callAgent**

Add to `tests/pipeline.test.js`:

```js
const { runPipeline } = require('../agents/pipeline');

// Minimal valid agent responses for each stage
const mockA1 = { scenes: [{ index: 1, style_world: 3, style_world_name: 'FRENCH LUXURY STREETWEAR', location: 'Paris rooftop', time_of_day: 'golden hour', season: 'summer', narrative_beat: 'reflective' }] };
const mockA2 = { scenes: [{ index: 1, Subject: ['subject'], MadeOutOf: ['ivory silk shirt', 'ivory trousers', 'Air Jordan 1 Royal', 'ivory bucket hat'], headwear: 'ivory bucket hat', jewelry: 'gold chain' }] };
const mockA3 = { scenes: [{ index: 1, Arrangement: 'THREE-QUARTER LOW', Lighting: 'GOLDEN HOUR NATURAL', Camera: { type: 'cowboy', lens: '85mm f/1.4', body: 'Sony A7R V' }, Background: 'Paris rooftop', Mood: 'Tyler Mitchell warmth', OutputStyle: 'cinematic photo, 4K ultra-HD', Composition: { framing: 'cowboy', angle: 'three-quarter low', focus: 'subject sharp' }, ColorPalette: { dominant: ['#F5F0E8'], mood: 'warm ivory' }, NegativePrompt: ['cartoonish'] }] };
const mockA4 = { scenes: [{ index: 1, video_prompt: '[0:00-0:03] establishing...' }] };

describe('runPipeline', () => {
  it('calls 4 agents for mv mode and returns assembled scenes', async () => {
    const calls = [];
    const mockCallAgent = async (systemPrompt, userMessage) => {
      calls.push({ systemPrompt: systemPrompt.slice(0, 30), userMessage: userMessage.slice(0, 30) });
      if (calls.length === 1) return JSON.stringify(mockA1);
      if (calls.length === 2) return JSON.stringify(mockA2);
      if (calls.length === 3) return JSON.stringify(mockA3);
      return JSON.stringify(mockA4);
    };

    const result = await runPipeline({
      mode: 'mv',
      userInput: 'reflective lyric',
      anchorBlock: '',
      wardrobeMemory: '',
      styleWorldMemory: '',
      sceneCount: 1,
    }, mockCallAgent);

    assert.equal(calls.length, 4);
    assert.equal(result.scenes.length, 1);
    assert.equal(result.scenes[0].image_prompt.label, 'WORLD 3 — FRENCH LUXURY STREETWEAR | Paris rooftop, golden hour');
    assert.equal(result.scenes[0].video_prompt, '[0:00-0:03] establishing...');
  });

  it('calls only 3 agents for nb2 mode', async () => {
    const calls = [];
    const mockCallAgent = async () => {
      calls.push(1);
      if (calls.length === 1) return JSON.stringify(mockA1);
      if (calls.length === 2) return JSON.stringify(mockA2);
      return JSON.stringify(mockA3);
    };

    const result = await runPipeline({
      mode: 'nb2',
      userInput: 'test',
      anchorBlock: '',
      wardrobeMemory: '',
      styleWorldMemory: '',
      sceneCount: 1,
    }, mockCallAgent);

    assert.equal(calls.length, 3);
    assert.equal(result.scenes[0].video_prompt, null);
  });

  it('stage 4 failure returns HTTP 200 with video_prompts_failed', async () => {
    let callCount = 0;
    const mockCallAgent = async () => {
      callCount++;
      if (callCount === 1) return JSON.stringify(mockA1);
      if (callCount === 2) return JSON.stringify(mockA2);
      if (callCount === 3) return JSON.stringify(mockA3);
      throw new Error('Stage 4 timeout');
    };

    const result = await runPipeline({
      mode: 'mv', userInput: 'test', anchorBlock: '', wardrobeMemory: '', styleWorldMemory: '', sceneCount: 1,
    }, mockCallAgent);

    assert.equal(result.video_prompts_failed, true);
    assert.equal(result.scenes[0].video_prompt, null);
    assert.equal(result.scenes[0].image_prompt.label, 'WORLD 3 — FRENCH LUXURY STREETWEAR | Paris rooftop, golden hour');
  });
});
```

- [ ] **Step 7.2: Run to confirm failure**

```bash
npm test
```

Expected: `runPipeline is not a function` or similar.

- [ ] **Step 7.3: Add runPipeline and callAgent to pipeline.js**

Add to the bottom of `agents/pipeline.js` (before the `module.exports` line):

```js
const { systemPrompt: architectPrompt, buildUserMessage: architectMsg } = require('./scene-architect');
const { systemPrompt: stylistPrompt, buildUserMessage: stylistMsg } = require('./stylist');
const { systemPrompt: cinPrompt, buildUserMessage: cinMsg } = require('./cinematographer');
const { systemPrompt: dirPrompt, buildUserMessage: dirMsg } = require('./video-director');

/**
 * Makes a single Gemini API call via the existing /api/messages proxy logic.
 * Parses the JSON response and returns the parsed object.
 * Throws on non-2xx HTTP, timeout, or invalid JSON.
 */
async function callGeminiAgent(systemPrompt, userMessage, fetchFn = fetch) {
  const controller = new AbortController();
  // timeout is set per-call by the caller wrapping this function
  const resp = await fetchFn('https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview:generateContent', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-goog-api-key': process.env.GEMINI_API_KEY,
    },
    body: JSON.stringify({
      system_instruction: { parts: [{ text: systemPrompt }] },
      contents: [{ role: 'user', parts: [{ text: userMessage }] }],
      generationConfig: { maxOutputTokens: 8000 },
    }),
    signal: controller.signal,
  });

  if (!resp.ok) {
    const errData = await resp.json().catch(() => ({}));
    throw new Error(`Gemini ${resp.status}: ${errData.error?.message || 'unknown error'}`);
  }

  const data = await resp.json();
  const text = data.candidates?.[0]?.content?.parts?.[0]?.text || '';
  const jsonMatch = text.match(/\{[\s\S]*\}/);
  if (!jsonMatch) throw new Error('Agent returned no JSON');
  return JSON.parse(jsonMatch[0]);
}

/**
 * Wraps a callAgent call with a per-stage timeout and 1 retry on 429/503.
 */
async function callWithTimeout(callAgentFn, systemPrompt, userMessage, timeoutMs) {
  const attempt = async () => {
    return new Promise(async (resolve, reject) => {
      const timer = setTimeout(() => reject(new Error(`Agent timed out after ${timeoutMs}ms`)), timeoutMs);
      try {
        const result = await callAgentFn(systemPrompt, userMessage);
        clearTimeout(timer);
        resolve(result);
      } catch (err) {
        clearTimeout(timer);
        reject(err);
      }
    });
  };

  try {
    return await attempt();
  } catch (err) {
    // retry once on rate limit or service unavailable
    if (err.message && (err.message.includes('429') || err.message.includes('503'))) {
      return await attempt();
    }
    throw err;
  }
}

/**
 * Main pipeline orchestrator.
 * @param {object} params - { mode, userInput, anchorBlock, wardrobeMemory, styleWorldMemory, sceneCount }
 * @param {function} callAgentFn - injectable for testing; defaults to callGeminiAgent
 */
async function runPipeline(params, callAgentFn = callGeminiAgent) {
  const { mode, userInput, anchorBlock = '', wardrobeMemory = '', styleWorldMemory = '' } = params;
  const cfg = modeConfig(mode);
  const n = resolveSceneCount(mode, params.sceneCount);

  // Stage 1: Scene Architect (30s timeout)
  let a1;
  try {
    const raw = await callWithTimeout(callAgentFn, architectPrompt, architectMsg({ userInput, mode, sceneCount: n, anchorBlock }), 30000);
    a1 = Array.isArray(raw.scenes) ? raw.scenes : [];
  } catch (err) {
    throw Object.assign(new Error('scene_architect_failed'), { stage: 1, cause: err });
  }

  // Truncate if over-count
  if (a1.length > n) a1 = a1.slice(0, n);

  // Stage 2: Stylist (45s timeout)
  let a2;
  try {
    const raw = await callWithTimeout(callAgentFn, stylistPrompt, stylistMsg({ scenes: a1, wardrobeMemory, styleWorldMemory }), 45000);
    a2 = Array.isArray(raw.scenes) ? raw.scenes : [];
  } catch (err) {
    throw Object.assign(new Error('stylist_failed'), { stage: 2, cause: err });
  }

  // Stage 3: Cinematographer (60s timeout)
  // Merge a1 + a2 by index before passing to cinematographer
  const byIdx1 = {};
  a1.forEach(s => { byIdx1[s.index] = s; });
  const byIdx2 = {};
  a2.forEach(s => { byIdx2[s.index] = s; });
  const mergedForCin = a1.map(s1 => {
    const s2 = byIdx2[s1.index] || {};
    return { ...s1, ...s2 };
  });

  let a3;
  try {
    const raw = await callWithTimeout(callAgentFn, cinPrompt, cinMsg({ scenes: mergedForCin }), 60000);
    a3 = Array.isArray(raw.scenes) ? raw.scenes : [];
  } catch (err) {
    throw Object.assign(new Error('cinematographer_failed'), { stage: 3, cause: err });
  }

  // Stage 4: Video Director (45s timeout) — only if mode requires it
  let a4 = [];
  let video_prompts_failed = false;

  if (cfg.runVideoDirector) {
    // Build assembled scenes for video director input
    const byIdx3 = {};
    a3.forEach(s => { byIdx3[s.index] = s; });
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
          Mood: s3.Mood,
          OutputStyle: s3.OutputStyle,
          Composition: s3.Composition,
          ColorPalette: s3.ColorPalette,
          NegativePrompt: s3.NegativePrompt,
        },
      };
    }).filter(s => s.image_prompt.Arrangement); // only scenes with a3 data

    try {
      const raw = await callWithTimeout(callAgentFn, dirPrompt, dirMsg({ scenes: mergedForDir }), 45000);
      a4 = Array.isArray(raw.scenes) ? raw.scenes : [];
    } catch (err) {
      // Stage 4 is non-fatal
      video_prompts_failed = true;
    }
  }

  const result = mergeByIndex(a1, a2, a3, a4);
  if (video_prompts_failed) result.video_prompts_failed = true;
  return result;
}
```

Update `module.exports` at the bottom of `agents/pipeline.js`:

```js
module.exports = { modeConfig, resolveSceneCount, buildLabel, mergeByIndex, buildWardrobeUsed, runPipeline };
```

- [ ] **Step 7.4: Run all tests**

```bash
npm test
```

Expected: all tests pass including all 3 `runPipeline` tests.

- [ ] **Step 7.5: Commit**

```bash
git add agents/pipeline.js tests/pipeline.test.js
git commit -m "feat: add runPipeline async orchestrator"
```

---

## Task 8: Server Endpoint

**Files:**
- Modify: `server.js`

- [ ] **Step 8.1: Add the /api/generate-prompts route to server.js**

Open `server.js`. After the `require` statements at the top, add:

```js
const { runPipeline } = require('./agents/pipeline');
```

After the existing `/api/messages` route (after line 66), add:

```js
app.post('/api/generate-prompts', async (req, res) => {
  try {
    const { mode, userInput, anchorBlock, wardrobeMemory, styleWorldMemory, sceneCount } = req.body;

    if (!mode || !['mv', 'nb2', 'kling-9grid', 'kling-startend'].includes(mode)) {
      return res.status(400).json({ error: 'Invalid or missing mode. Must be one of: mv, nb2, kling-9grid, kling-startend' });
    }
    if (!userInput || typeof userInput !== 'string' || !userInput.trim()) {
      return res.status(400).json({ error: 'userInput is required' });
    }

    const result = await runPipeline({
      mode,
      userInput: userInput.trim(),
      anchorBlock: anchorBlock || '',
      wardrobeMemory: wardrobeMemory || '',
      styleWorldMemory: styleWorldMemory || '',
      sceneCount: sceneCount ? parseInt(sceneCount, 10) : undefined,
    });

    res.json(result);

  } catch (err) {
    console.error('Pipeline error:', err);
    if (err.stage) {
      return res.status(500).json({ error: err.message, stage: err.stage });
    }
    res.status(500).json({ error: 'Pipeline failed: ' + err.message });
  }
});
```

- [ ] **Step 8.2: Start server and verify endpoint responds**

```bash
node server.js
```

In a separate terminal:

```bash
curl -s -X POST http://localhost:3000/api/generate-prompts \
  -H "Content-Type: application/json" \
  -d '{"mode":"invalid"}' | node -e "process.stdin.resume();let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>console.log(JSON.parse(d)))"
```

Expected: `{ error: 'Invalid or missing mode...' }` (HTTP 400)

- [ ] **Step 8.3: Commit**

```bash
git add server.js
git commit -m "feat: add /api/generate-prompts pipeline endpoint"
```

---

## Task 9: Frontend Updates

Update the 3 generate functions to call the new endpoint, and add stage-cycling loading text.

**Files:**
- Modify: `index.html`

- [ ] **Step 9.1: Add loading text cycling helper**

Find `function showLoading(msg)` at line ~1632 in `index.html`. It currently looks like:

```js
function showLoading(msg){
  // ... shows loading state, sets loadTxt
  document.getElementById('loadTxt').textContent=msg;
```

Add a new function directly after `showLoading`:

```js
let _loadingInterval = null;

function startPipelineLoadingCycle() {
  const stages = [
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
  }, 10000);
}

function stopPipelineLoadingCycle() {
  if (_loadingInterval) {
    clearInterval(_loadingInterval);
    _loadingInterval = null;
  }
}
```

- [ ] **Step 9.2: Update generateMV() to call new endpoint**

Find `generateMV()` at line ~1873 in `index.html`. Replace the `try` block (starting at `const resp = await fetch('/api/messages'` through `showError(err.message)`) with:

```js
  showLoading('Building your scene...');
  startPipelineLoadingCycle();

  const wardrobeBlock = buildWardrobePromptBlock(loadWardrobe());
  const styleWorldBlock = buildStyleWorldPromptBlock(loadStyleWorlds());
  const anchorBlock = imgBase64
    ? `\n\nA reference photo is provided. The subject's face, skin tone, and hair must remain exactly consistent across all scenes.`
    : '';

  const body = {
    mode: outputMode === 'nb2' ? 'nb2' : 'mv',
    userInput: (wardrobeBlock + styleWorldBlock + (currentMode === 'lyrics'
      ? `Artist: ${artist}\nTrack: ${track}\n\nLYRICS:\n${inputText}`
      : `Artist: ${artist}\n\nSCENE DESCRIPTION:\n${inputText}`)),
    anchorBlock,
    wardrobeMemory: wardrobeBlock,
    styleWorldMemory: styleWorldBlock,
  };

  try {
    const resp = await fetch('/api/generate-prompts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    stopPipelineLoadingCycle();
    if (!resp.ok) { const e = await resp.json().catch(() => ({})); throw new Error(e.error || `API error: ${resp.status}`); }
    const data = await resp.json();
    allScenes = data.scenes || [];
    saveWardrobe(allScenes);
    saveStyleWorlds(allScenes);
    renderScenes(artist, track);
  } catch (err) {
    stopPipelineLoadingCycle();
    console.error(err);
    showError(err.message);
  }
```

- [ ] **Step 9.3: Update generateGridStory() to call new endpoint**

Find `generateGridStory()` at line ~1962. Replace the `try` block similarly:

```js
  showLoading('Building 9-grid story...');
  startPipelineLoadingCycle();

  const anchorBlock = imgBase64
    ? `\n\nA reference photo is provided. The subject's face, skin tone, and hair must remain exactly consistent across all 9 images.`
    : '';

  const wardrobeBlock = buildWardrobePromptBlock(loadWardrobe());
  const styleWorldBlock = buildStyleWorldPromptBlock(loadStyleWorlds());

  try {
    const resp = await fetch('/api/generate-prompts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mode: 'kling-9grid',
        userInput: wardrobeBlock + styleWorldBlock + `Artist: ${artist}\n\n9-GRID STORY:\n${inputText}`,
        anchorBlock,
        wardrobeMemory: wardrobeBlock,
        styleWorldMemory: styleWorldBlock,
        sceneCount: 9,
      }),
    });
    stopPipelineLoadingCycle();
    if (!resp.ok) { const e = await resp.json().catch(() => ({})); throw new Error(e.error || `API error: ${resp.status}`); }
    const data = await resp.json();
    allScenes = data.scenes || [];
    saveWardrobe(allScenes);
    saveStyleWorlds(allScenes);
    renderScenes(artist, '9-Grid Story');
  } catch (err) {
    stopPipelineLoadingCycle();
    console.error(err);
    showError(err.message);
  }
```

- [ ] **Step 9.4: Update generateFramePair() to call new endpoint**

Find `generateFramePair()` at line ~2058. Replace the `try` block:

```js
  showLoading('Generating frame pairs...');
  startPipelineLoadingCycle();

  const anchorBlock = imgBase64
    ? `\n\nA reference photo is provided. Maintain the subject's exact facial features and skin tone in all frames.`
    : '';

  try {
    const resp = await fetch('/api/generate-prompts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mode: 'kling-startend',
        userInput: `Artist: ${artist}\n\nSCENE & MOTION DESCRIPTION:\n${inputText}`,
        anchorBlock,
        wardrobeMemory: '',
        styleWorldMemory: '',
      }),
    });
    stopPipelineLoadingCycle();
    if (!resp.ok) { const e = await resp.json().catch(() => ({})); throw new Error(e.error || `API error: ${resp.status}`); }
    const data = await resp.json();
    allScenes = data.scenes || [];
    renderScenes(artist, 'Frame Pairs');
  } catch (err) {
    stopPipelineLoadingCycle();
    console.error(err);
    showError(err.message);
  }
```

- [ ] **Step 9.5: Run all unit tests to confirm no regressions**

```bash
npm test
```

Expected: all tests still pass (no backend changes in this task).

- [ ] **Step 9.6: Commit**

```bash
git add index.html
git commit -m "feat: update frontend to use pipeline endpoint with stage loading UX"
```

---

## Task 10: Integration Smoke Test

Manual end-to-end test against the live backend.

- [ ] **Step 10.1: Start the server**

```bash
node server.js
```

- [ ] **Step 10.2: Test Stage 1–3 abort behavior (no API key needed)**

```bash
curl -s -X POST http://localhost:3000/api/generate-prompts \
  -H "Content-Type: application/json" \
  -d '{"mode":"mv","userInput":"test scene"}' | node -e "process.stdin.resume();let d='';process.stdin.on('data',c=>d+=c);process.stdin.on('end',()=>{const r=JSON.parse(d);console.log('stage:',r.stage,'error:',r.error);})"
```

Expected without GEMINI_API_KEY set: `stage: 1 error: scene_architect_failed` (HTTP 500) — confirms abort on Stage 1 failure.

- [ ] **Step 10.3: Live MV generation (requires GEMINI_API_KEY)**

Open `http://localhost:3000` in browser. Enter artist name and lyrics. Generate MV. Verify:

- Loading text cycles through 4 stage labels
- Results render correctly (same UI as before)
- Image prompts include all 12 fields including `Composition` and `ColorPalette`
- Video prompts include timestamped blocks with character consistency lock
- `style_world` and `wardrobe_used` saved to localStorage (check DevTools → Application → Local Storage)

- [ ] **Step 10.4: Rule validation check**

In the generated result, verify:
- No style world number repeats across scenes
- No shoe model repeats across scenes
- Camera angles vary across scenes

- [ ] **Step 10.5: NB2 mode test**

Switch to NB2 mode, generate. Verify `video_prompt` is null per scene and Kling section does not render.

- [ ] **Step 10.6: Final commit**

```bash
git add .
git commit -m "feat: complete multi-agent pipeline implementation"
```

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `npm test` | Run all unit tests |
| `npm start` | Start server on port 3000 |
| `curl -X POST http://localhost:3000/api/generate-prompts -H "Content-Type: application/json" -d '{"mode":"mv","userInput":"test"}'` | Test endpoint directly |

| File | What it does |
|------|-------------|
| `agents/scene-architect.js` | Scene Architect prompt + message builder |
| `agents/stylist.js` | Stylist prompt + message builder |
| `agents/cinematographer.js` | Cinematographer prompt + message builder |
| `agents/video-director.js` | Video Director prompt + message builder |
| `agents/pipeline.js` | Pure helpers + async `runPipeline()` |
| `tests/pipeline.test.js` | All unit tests |
| `server.js` | Express server with `/api/generate-prompts` route |
| `index.html` | Frontend SPA — updated 3 generate functions + loading text |
