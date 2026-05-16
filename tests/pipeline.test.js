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

  it('treats 0 as below min and clamps to min (not default)', () => {
    assert.equal(resolveSceneCount('mv', 0), 6); // 0 < minN(6) → clamps to 6
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
    assert.ok(msg.includes('exactly 6 scenes'));
    assert.ok(msg.includes('Reference photo'));
  });

  it('buildUserMessage works without anchorBlock', () => {
    const msg = architectMsg({ userInput: 'test', mode: 'mv', sceneCount: 6 });
    assert.equal(typeof msg, 'string');
    assert.ok(msg.length > 0);
  });
});

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

const { systemPrompt: cinPrompt, buildUserMessage: cinMsg } = require('../agents/cinematographer');

describe('cinematographer', () => {
  it('exports a non-empty string systemPrompt over 800 chars', () => {
    assert.equal(typeof cinPrompt, 'string');
    assert.ok(cinPrompt.length > 800);
  });

  it('systemPrompt references all 26 camera angle names', () => {
    const angles = [
      'LOW HERO ANGLE', 'EYE-LEVEL INTIMATE', 'THREE-QUARTER LOW', 'OVER-THE-SHOULDER',
      'DUTCH TILT', 'TIGHT CLOSE-UP', 'WIDE ENVIRONMENTAL', 'COWBOY SHOT',
      'FIRST-PERSON POV', 'MIRROR SELFIE', 'LOOKING DOWN TOP-DOWN', 'SEATED CANDID',
      'WALKING MID-STRIDE', 'THROUGH GLASS / WINDOW', 'DETAIL CLOSE-UP', 'LEANING CASUAL',
      "BIRD'S EYE OVERHEAD", 'HIGH ANGLE VULNERABLE', 'EXTREME CLOSE-UP DETAIL',
      'TELEPHOTO COMPRESSED', 'STEADICAM FOLLOW', 'CRANE REVEAL', 'TWO-SHOT RELATIONAL',
      'MACRO TEXTURE', 'SPLIT FRAME', 'DUTCH TILT AGGRESSIVE',
    ];
    angles.forEach(angle => assert.ok(cinPrompt.includes(angle), `Missing angle: ${angle}`));
  });

  it('systemPrompt references all 18 lighting setup names', () => {
    const lights = [
      'GOLDEN HOUR NATURAL', 'BLUE HOUR / DUSK', 'NIGHT STREET PRACTICAL',
      'ARENA / STADIUM', 'OVERCAST DIFFUSED', 'REMBRANDT PORTRAIT',
      'STUDIO BEAUTY DISH', 'FLASH FILL OUTDOOR', 'BUTTERFLY / GLAMOUR',
      'CLAMSHELL BEAUTY', 'SPLIT LIGHT', 'SHORT LIGHTING',
      'THREE-POINT STUDIO', 'BACK / RIM LIGHT HALO', 'HARSH EDITORIAL HARD LIGHT',
      'STRIPBOX EDGE', 'GEL / COLOR MOOD', 'TOP LIGHT DRAMATIC',
    ];
    lights.forEach(light => assert.ok(cinPrompt.includes(light), `Missing lighting: ${light}`));
  });

  it('buildUserMessage includes merged scene data', () => {
    const scenes = [{ index: 1, style_world: 3, location: 'Paris rooftop', time_of_day: 'golden hour', season: 'summer', narrative_beat: 'reflective', Subject: ['subject'], MadeOutOf: ['shirt', 'pants'] }];
    const msg = cinMsg({ scenes });
    assert.ok(msg.includes('Paris rooftop'));
    assert.ok(msg.includes('"index": 1'));
  });
});

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

const { runPipeline } = require('../agents/pipeline');

// Minimal valid agent responses for each stage
const mockA1 = { scenes: [{ index: 1, style_world: 3, style_world_name: 'FRENCH LUXURY STREETWEAR', location: 'Paris rooftop', time_of_day: 'golden hour', season: 'summer', narrative_beat: 'reflective' }] };
const mockA2 = { scenes: [{ index: 1, Subject: ['subject'], MadeOutOf: ['ivory silk shirt', 'ivory trousers', 'none', 'ivory bucket hat', 'Air Jordan 1 Royal'], headwear: 'ivory bucket hat', jewelry: 'gold chain' }] };
const mockA3 = { scenes: [{ index: 1, Arrangement: 'THREE-QUARTER LOW', Lighting: 'GOLDEN HOUR NATURAL', Camera: { type: 'cowboy', lens: '85mm f/1.4', body: 'Sony A7R V' }, Background: 'Paris rooftop', Mood: 'Tyler Mitchell warmth', OutputStyle: 'cinematic photo, 4K ultra-HD', Composition: { framing: 'cowboy', angle: 'three-quarter low', focus: 'subject sharp' }, ColorPalette: { dominant: ['#F5F0E8'], mood: 'warm ivory' }, NegativePrompt: ['cartoonish'] }] };
const mockA4 = { scenes: [{ index: 1, video_prompt: '[0:00-0:03] establishing...' }] };

describe('runPipeline', () => {
  it('calls 4 agents for mv mode and returns assembled scenes', async () => {
    const calls = [];
    const mockCallAgent = async (systemPrompt, userMessage) => {
      calls.push({ systemPrompt: systemPrompt.slice(0, 30), userMessage: userMessage.slice(0, 30) });
      if (calls.length === 1) return mockA1;
      if (calls.length === 2) return mockA2;
      if (calls.length === 3) return mockA3;
      return mockA4;
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
      if (calls.length === 1) return mockA1;
      if (calls.length === 2) return mockA2;
      return mockA3;
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

  it('stage 1 failure throws with stage:1', async () => {
    const mockCallAgent = async () => { throw new Error('network error'); };
    await assert.rejects(
      () => runPipeline({ mode: 'mv', userInput: 'test', anchorBlock: '', wardrobeMemory: '', styleWorldMemory: '', sceneCount: 1 }, mockCallAgent),
      (err) => {
        assert.equal(err.stage, 1);
        return true;
      }
    );
  });

  it('stage 2 failure throws with stage:2', async () => {
    let callCount = 0;
    const mockCallAgent = async () => {
      callCount++;
      if (callCount === 1) return mockA1;
      throw new Error('stage 2 error');
    };
    await assert.rejects(
      () => runPipeline({ mode: 'mv', userInput: 'test', anchorBlock: '', wardrobeMemory: '', styleWorldMemory: '', sceneCount: 1 }, mockCallAgent),
      (err) => {
        assert.equal(err.stage, 2);
        return true;
      }
    );
  });

  it('stage 3 failure throws with stage:3', async () => {
    let callCount = 0;
    const mockCallAgent = async () => {
      callCount++;
      if (callCount === 1) return mockA1;
      if (callCount === 2) return mockA2;
      throw new Error('stage 3 error');
    };
    await assert.rejects(
      () => runPipeline({ mode: 'mv', userInput: 'test', anchorBlock: '', wardrobeMemory: '', styleWorldMemory: '', sceneCount: 1 }, mockCallAgent),
      (err) => {
        assert.equal(err.stage, 3);
        return true;
      }
    );
  });

  it('stage 4 failure returns HTTP 200 with video_prompts_failed', async () => {
    let callCount = 0;
    const mockCallAgent = async () => {
      callCount++;
      if (callCount === 1) return mockA1;
      if (callCount === 2) return mockA2;
      if (callCount === 3) return mockA3;
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
