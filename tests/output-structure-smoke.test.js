'use strict';
// Smoke test: Nano Banana Pro 7-Part Structure assembly + FilmStock piping.
// Verifies:
// - pipeline.mergeByIndex includes FilmStock from a3
// - flattenImagePrompt (extracted from js/app.js) emits the labelled 7-Part
//   sections in the correct order: [Subject] [Action] [Setting]
//   [Composition] [Lighting] [Style] [Constraints]
// - Required Vawn keywords (cinematic editorial still, implied narrative,
//   film stock + visible grain, photorealistic, no text) all land inside
//   the right sections.

const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');

const { mergeByIndex } = require('../agents/pipeline');

// Reconstruct flattenImagePrompt + STYLE_OPENERS by extracting both from
// js/app.js (frontend file). Brace-balanced extraction — robust against
// CRLF endings and multi-line whitespace.
const appJsSrc = fs.readFileSync(path.join(__dirname, '..', 'js', 'app.js'), 'utf8');

// Pull the STYLE_OPENERS literal so the function's reference resolves.
const openersStart = appJsSrc.indexOf('const STYLE_OPENERS = {');
assert.ok(openersStart !== -1, 'STYLE_OPENERS must be defined in js/app.js');
const openersEnd = appJsSrc.indexOf('};', openersStart);
assert.ok(openersEnd !== -1, 'unable to find end of STYLE_OPENERS');
const openersSrc = appJsSrc.slice(openersStart, openersEnd + 2);

const helpersStart = appJsSrc.indexOf('function cleanPromptText(');
assert.ok(helpersStart !== -1, 'prompt helper functions must be defined in js/app.js');
const fnStart = appJsSrc.indexOf('function flattenImagePrompt(');
assert.ok(fnStart !== -1, 'flattenImagePrompt must be defined in js/app.js');
const helpersSrc = appJsSrc.slice(helpersStart, fnStart);
const bodyStart = appJsSrc.indexOf('{', fnStart);
let depth = 0, i = bodyStart, end = -1;
for (; i < appJsSrc.length; i++) {
  const c = appJsSrc[i];
  if (c === '{') depth++;
  else if (c === '}' && --depth === 0) { end = i; break; }
}
assert.ok(end !== -1, 'unable to find end of flattenImagePrompt');
const fnSrc = appJsSrc.slice(fnStart, end + 1);
// eslint-disable-next-line no-eval
const flattenImagePrompt = eval(
  openersSrc + ';\n' + helpersSrc + ';\n(' + fnSrc.replace('function flattenImagePrompt', 'function') + ')'
);

test('mergeByIndex pipes FilmStock through from a3', () => {
  const a1 = [{ index: 1, style_world: 3, style_world_name: 'French Luxury', location: 'Paris rooftop', time_of_day: 'dusk', narrative_beat: 'Overlooking city' }];
  const a2 = [{ index: 1, Subject: ['gaze off-frame'], MadeOutOf: ['Celine silk shirt'], jewelry: 'gold Cuban chain' }];
  const a3 = [{
    index: 1,
    Arrangement: 'LEANING CASUAL — weight on right shoulder',
    Lighting: 'GOLDEN HOUR NATURAL — low sun 15 degrees',
    Camera: { type: 'medium portrait', lens: '85mm f/1.4', body: 'Sony A7R V' },
    Background: 'Paris rooftop terrace, zinc chimneys',
    FilmStock: 'Kodak Portra 400 pushed one stop, visible film grain in the shadows',
    Mood: "carries Gregory Crewdson's cinematic stillness — desaturated, teal shadows, warm amber on skin, implied narrative of a figure before a decision",
    Composition: { framing: 'medium portrait', angle: 'eye-level', focus: 'subject sharp' },
    ColorPalette: { dominant: ['#F5F0E8'], mood: 'warm ivory and gold' },
    NegativePrompt: ['cartoonish'],
  }];
  const a4 = [];
  const merged = mergeByIndex(a1, a2, a3, a4);
  assert.strictEqual(merged.scenes.length, 1);
  assert.strictEqual(
    merged.scenes[0].image_prompt.FilmStock,
    'Kodak Portra 400 pushed one stop, visible film grain in the shadows'
  );
});

test('flattenImagePrompt emits the 7-Part Structure with required Vawn keywords', () => {
  const ip = {
    label: 'WORLD 3 — FRENCH LUXURY | Paris rooftop, dusk',
    Subject: ['gaze directed past the lens mid-thought'],
    MadeOutOf: [
      'Celine ivory silk bowling shirt',
      'wide-leg ivory trousers',
      'none (no outer layer this scene)',
      'fitted ivory bucket hat',
      'Air Jordan 1 Royal',
      'gold Cuban link chain',
    ],
    Arrangement: 'LEANING CASUAL — weight shifted right, phone in left hand',
    Lighting: 'GOLDEN HOUR NATURAL — amber rim on shoulder, directional shadows',
    Camera: { type: 'medium portrait', lens: '85mm f/1.4', body: 'Sony A7R V' },
    Background: 'Paris rooftop terrace, zinc chimneys, saturated amber sky',
    FilmStock: 'Kodak Portra 400 pushed one stop, visible film grain in the shadows',
    Mood: "carries Gregory Crewdson's cinematic stillness — desaturated, teal shadows, warm amber on skin, implied narrative of a figure before a decision",
    Composition: { framing: 'medium portrait', angle: 'eye-level', focus: 'subject sharp, rooftops dissolved into bokeh' },
    ColorPalette: { dominant: ['#F5F0E8'], mood: 'warm ivory and gold, amber shadows' },
    NegativePrompt: ['cartoonish', 'illustrated'],
  };
  const out = flattenImagePrompt(ip);

  // 7-Part Structure: every section label must appear in the correct order.
  const order = ['[Subject]', '[Action]', '[Setting]', '[Composition]', '[Lighting]', '[Style]', '[Constraints]'];
  let cursor = 0;
  for (const label of order) {
    const idx = out.indexOf(label, cursor);
    assert.ok(idx !== -1, `section label ${label} must appear`);
    cursor = idx + label.length;
  }

  // Required Vawn keywords:
  assert.match(out, /candid lifestyle photograph/i, 'opener "candid lifestyle photograph" must appear inside [Subject]');
  assert.match(out, /implied narrative/i, 'must include "implied narrative" (in [Style])');
  assert.match(out, /Kodak Portra 400/, 'must include the film stock');
  assert.match(out, /visible film grain/i, 'must include "visible film grain"');
  assert.match(out, /photorealistic/i, 'must include "photorealistic"');
  assert.match(out, /no text/i, 'must include "no text" inside [Constraints]');
  assert.doesNotMatch(out, /Gregory Crewdson/, 'photographer names should stay out of final NB prompt prose');

  // Wardrobe must be in [Subject] block; "none" placeholder must be filtered.
  assert.match(out, /Celine/, 'must include wardrobe brand');
  assert.doesNotMatch(out, /no outer layer this scene/, '"none" placeholders must be filtered out');

  // Camera body/lens should appear inside [Composition].
  assert.match(out, /85mm f\/1\.4/, 'must include lens spec');
  assert.match(out, /Sony A7R V/, 'must include camera body');

  // Negatives now ride inside [Constraints], not a "Negative:" line.
  const constraintsBlock = out.slice(out.indexOf('[Constraints]'));
  assert.match(constraintsBlock, /no distorted hands/i, 'lean constraints should include high-value anatomy negatives');
  assert.match(constraintsBlock, /no watermark/i, '[Constraints] auto-injects "no watermark"');
});

test('flattenImagePrompt handles missing FilmStock gracefully', () => {
  const ip = {
    label: 'No film stock scene',
    Subject: ['gaze down'],
    MadeOutOf: ['plain tee'],
    Background: 'Studio wall',
    Mood: "carries Hype Williams' tonal restraint — implied narrative",
  };
  const out = flattenImagePrompt(ip);
  assert.match(out, /\[Subject\]/);
  assert.match(out, /\[Style\]/);
  assert.match(out, /\[Constraints\]/);
  assert.match(out, /candid lifestyle photograph/i);
  assert.match(out, /implied narrative/i);
  assert.match(out, /photorealistic/i);
  assert.match(out, /no text/i);
  // Should not throw or include undefined
  assert.doesNotMatch(out, /undefined/);
});
