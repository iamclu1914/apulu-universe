'use strict';

// ───────────────────────────────────────────────────────────────
// STYLE PRESETS — control color grade, film stock rotation, mood
// template, photographer references, and opener framing.
//
// 'vawn-editorial' = the default cohesive lifestyle framework
// (warm dark documentary polish, social-presence posture). All other presets
// are vernacular-retro variants per docs/film-look-vernacular-retro.md.
//
// To add a new preset: copy a vernacular block, swap the five fields,
// then add the key to STYLE_PRESETS. Pipeline.js validates against
// these keys; unknown presets fall back to 'vawn-editorial'.
// ───────────────────────────────────────────────────────────────

const VAWN_EDITORIAL = {
  label: 'Vawn Editorial',
  // The opener clause inserted in front of the model's Arrangement output.
  // For default: keep a polished lifestyle-documentary posture. For retro: explicitly drop it.
  openerDirective: `OPENER POSTURE: every scene reads as a real artist lifestyle photograph with implied narrative — candid, lived-in, social-media plausible, and never a generic posed portrait.`,
  filmStockRotation: [
    '"Kodak Portra 400 pushed one stop, visible film grain in the shadows"',
    '"Kodak Gold 200, visible film grain"',
    '"Kodak 500T 5219 motion-picture stock, visible grain lifted in highlights"',
    '"Fujifilm 400H, soft visible grain in midtones"',
    '"CineStill 800T, halation in practicals and visible grain"',
  ],
  filmStockGuidance: 'Pick the stock that matches the light — Portra 400 and Gold 200 for daylight, 500T and 800T for night practicals and tungsten.',
  colorGrade: `COLOR GRADE — APPLIES TO ALL SCENES WITHOUT EXCEPTION: warm dark documentary base, natural skin, amber practicals, controlled contrast, and mild desaturation. Nothing over-saturated. The image feels real, lived-in, and elevated without looking staged or detached.`,
  approvedInfluences: `HYPE WILLIAMS → tonal restraint, urban cinematic command, graphic split-tone between amber and teal, subjects moving with implied power against deep shadow
GORDON PARKS → street documentary authenticity, rich shadow detail, subjects rendered with dignity inside their real world, honest observational power
ROY DECARAVA → jazz-portrait intimacy, deep velvety shadows with lifted skin tone, humanist quiet, a composition that feels overheard rather than posed
JAMEL SHABAZZ → early-NYC hip-hop documentary warmth, direct but respectful framing, subjects embedded in their block, unforced candor
GREGORY CREWDSON → prestige-film cinematic stillness, single-source staged realism at dusk or pre-dawn, suburban/edge-of-city unease, every object in frame feels narratively placed
ROBERT FRANK → mid-century American road-trip melancholy, grain-forward black-and-white sensibility carried into color, restless observational distance
HENRI CARTIER-BRESSON → decisive-moment composition, geometric framing, the subject caught at the inflection of an action
GARRY WINOGRAND → busy-frame street energy, subjects glanced rather than posed, NYC density
SAUL LEITER → soft-color street poetry, layered reflections, atmospheric warmth
WILLIAM EGGLESTON → American color vernacular, banal-into-poetic, single-source available light`,
  moodTemplate: `MOOD FIELD TEMPLATE — COPY THIS STRUCTURE EXACTLY, filling in the blanks: "carries [APPROVED INFLUENCE]'s [QUALITY] — warm dark documentary color, natural skin, amber practicals, candid social-media realism, implied narrative of [ONE SENTENCE OF TENSION OR NARRATIVE WEIGHT]."
The phrase "implied narrative" is MANDATORY in every Mood value — the still must read as if something just happened or is about to.
BANNED WORDS in the Mood field: fashion campaign, studio portrait, posed, generic, stock photo, influencer, red carpet, vibrant, airy, dreamy, serene, cheerful, vibe. If you are about to write "vibrant", replace it with: charged, electric, kinetic, or restless. If you are about to write "moody", replace it with: sombre, weighted, quiet, or tense. These substitutions are mandatory.`,
  extraGuidance: '',
};

const NINETIES_DISPOSABLE = {
  label: '90s Disposable Flash',
  openerDirective: `OPENER POSTURE — VERNACULAR RETRO: this is NOT a cinematic editorial still. It is a casual 1990s point-and-shoot snapshot from real life, scanned from a consumer color print. Subject should NOT look like he is posing for editorial. The image must feel candid, unstaged, archival — somebody grabbed the camera and took the shot while hanging out. Do NOT force flash unless the lighting setup calls for it. Do NOT use "cinematic editorial still", "expensive and detached", or any prestige-TV posture.`,
  filmStockRotation: [
    '"Kodak Funsaver disposable camera, 32mm fixed plastic lens, ISO 400 consumer color negative, slight magenta print cast, visible grain throughout, soft plastic-lens focus, hard on-camera flash"',
    '"Fuji QuickSnap disposable, ISO 400 consumer film, warm magenta-amber cast, blown flash highlights on skin, fingerprint smudge vignette, amateur framing"',
    '"Kodak Gold 200 35mm consumer film scanned full-frame with no border, fine visible grain, warm golden cast with slight magenta bias, slightly soft point-and-shoot focus"',
  ],
  filmStockGuidance: 'All stocks are 90s consumer-grade. Match flash-lit interiors to disposable stocks; daylight or stoop scenes can use Kodak Gold 200.',
  colorGrade: `COLOR GRADE — VERNACULAR 90s CONSUMER PRINT: warm magenta-amber print cast, slightly overexposed flash highlights on skin, healthy warm midtones, soft tungsten ambient fill in backgrounds. NEVER green, NEVER fluorescent green skin, NEVER teal shadows, NEVER cyan shadows, NEVER cool color balance. The image must feel candid and amateur, not graded. NO date stamp, no timestamp, no text overlay, no numbers in frame.`,
  approvedInfluences: `JAMEL SHABAZZ → early-NYC hip-hop documentary warmth, direct but respectful framing, subjects embedded in their block
RICKY POWELL → corner-of-the-block candor, unposed, conversational, NYC vernacular
GORDON PARKS → street documentary authenticity, dignity inside the real world
NAN GOLDIN → archival flash intimacy, bedroom/bar/laundromat snapshots, unguarded
LARRY CLARK → unfiltered everyday teenage/young-adult vernacular, no editorial gloss
VIVIAN MAIER → archival street snapshot quality, found-photograph authenticity
WILLIAM KLEIN → grainy NYC flash street work, off-kilter framing, raw immediacy
DASH SNOW → 90s-into-2000s downtown vernacular flash photography, no posing, archive feel
MARK MORRISROE → flash-lit late-80s/early-90s candid intimacy, faded color
RYAN McGINLEY → raw youth-culture flash work, candid mid-action energy`,
  moodTemplate: `MOOD FIELD TEMPLATE — COPY THIS STRUCTURE EXACTLY: "the casual unstaged character of a 90s [SCENE TYPE] snapshot in the spirit of [APPROVED INFLUENCE] — somebody grabbed the camera and took the shot while [WHAT WAS ACTUALLY HAPPENING], implied narrative of [ONE SENTENCE OF NARRATIVE WEIGHT]."
The phrase "implied narrative" is MANDATORY. The Mood must NEVER use: cinematic, editorial, expensive, detached, prestige, magazine, polished, sculpted, refined. Replace with: casual, unposed, archival, overheard, candid, vernacular, snapshot.
BANNED WORDS in the Mood field: cinematic, editorial, expensive, detached, prestige, magazine, polished, sculpted, vibrant, dreamy, moody, vibe.`,
  extraGuidance: `NEGATIVE PROMPT REINFORCEMENT — every scene's NegativePrompt MUST include: "green color cast, fluorescent green skin, sickly green tint, cyan shadows, cool color balance, date stamp, timestamp, text overlay, cinematic still, magazine editorial, prestige TV color grade, teal shadows, Sony A7R V look, AI-smooth skin, clinical sharpness".`,
};

const SEVENTIES_WARM_FILM = {
  label: '70s Warm Film',
  openerDirective: `OPENER POSTURE — VERNACULAR RETRO: this is a grainy warm 1970s family-album photograph, scanned from a 35mm color print that has aged gently over time. NOT a cinematic editorial still. The image has imperfect focus, slightly uneven exposure, and feels overheard rather than posed. Do NOT use "cinematic editorial still" or prestige-TV posture.`,
  filmStockRotation: [
    '"Kodak Portra-adjacent 70s 35mm color negative, scanned from an aged print, warm golden cast throughout, heavy visible grain, mild chromatic aberration at the edges, subtle halation on highlights"',
    '"Kodachrome 64 mounted slide, scanned from the transparency, deep saturated reds and warm yellows, fine tight grain, hard-edged shadow falloff"',
    '"Kodak Ektachrome 200 1970s color slide film, slight green shift in foliage, punchy mid-range, signature transparency contrast"',
  ],
  filmStockGuidance: '70s family-album warmth dominates. Use Portra-adjacent for soft warm scenes, Kodachrome/Ektachrome for vivid daylight.',
  colorGrade: `COLOR GRADE — 1970s AGED PRINT: warm golden cast throughout, slight color fade in highlights, lifted blacks, warm shadows (NOT cool, NOT teal), heavy visible film grain in every part of the image. The image feels like it was pulled out of a shoebox — not graded. NEVER teal shadows, NEVER cyan, NEVER digital cleanup.`,
  approvedInfluences: `GORDON PARKS → 70s street documentary warmth, observational dignity
ROY DECARAVA → jazz-quiet intimacy, deep velvety shadows with lifted skin tone
JAMEL SHABAZZ → early NYC hip-hop documentary, subjects embedded in their block
WILLIAM EGGLESTON → 70s American color vernacular, banal-into-poetic
SAUL LEITER → soft-color street poetry, atmospheric warmth
JOEL MEYEROWITZ → vivid saturated street color, daylight observational warmth
ERNST HAAS → motion in saturated color, painterly daylight
STEPHEN SHORE → American color landscape, deadpan composition, soft warm 70s tonality
HELEN LEVITT → midcentury NYC street color, candid neighborhood life
ROBERT FRANK → mid-century American melancholy, road-trip distance`,
  moodTemplate: `MOOD FIELD TEMPLATE — COPY THIS STRUCTURE EXACTLY: "the natural soft character of late-70s [SCENE CONTEXT] photography — [APPROVED INFLUENCE]'s [QUALITY] — implied narrative of [ONE SENTENCE]."
The phrase "implied narrative" is MANDATORY. NEVER use: cinematic, editorial, expensive, prestige, polished, sculpted, sharp, clinical, modern.`,
  extraGuidance: `NEGATIVE PROMPT REINFORCEMENT: include "digital clean look, modern HDR, AI-smooth skin, clinical sharpness, oversaturated, plastic skin, teal shadows, prestige TV color grade, magazine editorial polish, Sony A7R V look".`,
};

const KODACHROME_DAYLIGHT = {
  label: 'Kodachrome Daylight',
  openerDirective: `OPENER POSTURE — VERNACULAR RETRO: this is an authentic 1980s Kodachrome 64 color slide photograph, scanned from a mounted transparency. Vivid saturated daylight film — NOT cinematic, NOT editorial, NOT desaturated. Direct sun, hard shadows, punchy color. Do NOT apply prestige-TV posture or split-tone grading.`,
  filmStockRotation: [
    '"Kodachrome 64 mounted color slide, scanned from the transparency, deep saturated reds and warm yellows, crisp cyan sky, hard-edged shadows with defined contrast, fine tight grain"',
    '"Kodachrome 25 slide film, finer grain, even more saturated mid-range, signature transparency contrast"',
    '"Fuji Velvia 50 daylight slide, ultra-saturated, punchy greens and reds, crisp directional shadow"',
  ],
  filmStockGuidance: 'All stocks are saturated daylight slide film. Use only for daylight or bright-overcast scenes — NOT for night or interior.',
  colorGrade: `COLOR GRADE — KODACHROME SATURATED DAYLIGHT: deep saturated reds, warm golden yellows, crisp cyan sky, hard-edged shadows with defined high-contrast falloff, punchy mid-range, slight green shift in foliage. Vivid saturated daylight film — NOT desaturated, NOT faded, NOT teal-shifted. NEVER apply teal/orange grade. NEVER apply prestige-TV split-tone.`,
  approvedInfluences: `JAMEL SHABAZZ → early-NYC hip-hop documentary saturation, subjects embedded in their block
WILLIAM EGGLESTON → 70s/80s American color vernacular, saturated banal scenes elevated
JOEL MEYEROWITZ → vivid saturated street color, daylight observational warmth
ERNST HAAS → motion in saturated color, painterly daylight
GORDON PARKS → street documentary dignity in vivid color
HELEN LEVITT → midcentury NYC street color, candid neighborhood life
STEPHEN SHORE → American color landscape, deadpan composition
GARRY WINOGRAND → busy-frame street energy translated to vivid daylight color
HARRY GRUYAERT → saturated international color photography, painterly daylight
LUIGI GHIRRI → European deadpan color, saturated atmospheric daylight`,
  moodTemplate: `MOOD FIELD TEMPLATE — COPY THIS STRUCTURE EXACTLY: "[APPROVED INFLUENCE]'s [QUALITY] — saturated and warm, vivid without being digitally processed, implied narrative of [ONE SENTENCE]."
"implied narrative" is MANDATORY. NEVER use: desaturated, teal, cinematic, editorial, expensive, prestige, polished, muted.`,
  extraGuidance: `NEGATIVE PROMPT REINFORCEMENT: include "desaturated, teal shadows, muted colors, prestige TV color grade, cinematic still, AI-smooth skin, clinical sharpness, modern HDR, Sony A7R V look".`,
};

const CINESTILL_NIGHT = {
  label: 'CineStill Night',
  openerDirective: `OPENER POSTURE — VERNACULAR RETRO: this is a grainy 35mm cinematic-stock night photograph, scanned from a negative — heavy halation on every light source. NOT a magazine editorial. Authentic film character, imperfect focus. Do NOT digitally clean.`,
  filmStockRotation: [
    '"CineStill 800T tungsten-balanced 35mm, pushed one stop, heavy red halation rings around every light source, magenta cast in midtones, deep cyan shadows, coarse visible grain"',
    '"Kodak Vision3 500T motion-picture stock cross-processed for stills, halation on practicals, lifted shadows, visible grain"',
    '"Fuji Eterna Vivid 250D night-pushed, slight halation, cool magenta-cyan split, visible grain"',
  ],
  filmStockGuidance: 'All stocks are tungsten night film. Use only for night exteriors with neon/sodium/streetlamp practicals — NOT for daylight.',
  colorGrade: `COLOR GRADE — CINESTILL TUNGSTEN NIGHT: tungsten color balance, heavy red halation rings around every neon and streetlamp source, strong color bleed, magenta cast in the midtones, deep cyan shadows, visible coarse film grain. Authentic low-light film character — NOT digitally cleaned, NOT modern HDR.`,
  approvedInfluences: `GREGORY CREWDSON → prestige-film cinematic stillness at dusk/night, single-source staged realism (USE SPARINGLY)
ROY DECARAVA → jazz-quiet intimacy in deep shadow
HYPE WILLIAMS → urban night cinematic command, halated practicals
DARYL PEVETO → contemporary low-light street, grain-forward
TODD HIDO → suburban-night atmospherics, glow through fog
WONG KAR-WAI → motion-blurred low-light intimacy, neon atmosphere
ROBBY MULLER → naturalistic low-light cinema warmth, sodium/tungsten
HARRIS SAVIDES → painterly low-light cinema, grain texture as voice
RINKO KAWAUCHI → soft low-light atmospheric color, quiet observation
DAIDO MORIYAMA → high-contrast Tokyo night street, harsh flash, raw grain`,
  moodTemplate: `MOOD FIELD TEMPLATE — COPY THIS STRUCTURE EXACTLY: "the restless quiet of a [APPROVED INFLUENCE] night frame — halation blooming, tungsten color, grain dominant, implied narrative of [ONE SENTENCE]."
"implied narrative" is MANDATORY. NEVER use: clean, daylight balance, digital, polished, AI-smooth.`,
  extraGuidance: `NEGATIVE PROMPT REINFORCEMENT: include "no grain, no halation, daylight balance, clean highlights, digital clean look, modern HDR, AI-smooth skin, clinical sharpness, prestige TV teal-and-orange, Sony A7R V look".`,
};

const SUPER8_DUSK = {
  label: 'Super 8 Dusk',
  openerDirective: `OPENER POSTURE — VERNACULAR RETRO: this is a 1970s Super 8 motion-picture frame captured as a single still, telecined from the original film print. Heavy organic grain, slight gate weave, color bleed. NOT a digital still. NOT a cinematic editorial — a vintage cinema frame. The image feels overheard.`,
  filmStockRotation: [
    '"1970s Super 8 Kodak Vision3 200T motion-picture color negative, telecined to digital, heavy organic grain structure, slight gate weave, color bleed in warm practicals, soft 8mm frame edges"',
    '"Kodak Ektachrome 160T Super 8 reversal stock, vivid color, fine grain for the format, telecined frame"',
    '"Kodak 500T 5219 16mm motion-picture stock telecined to digital, visible grain lifted in highlights, slight gate weave, color bleed on practicals"',
  ],
  filmStockGuidance: 'All stocks are vintage motion-picture film telecined to digital. Use for dusk/evening or low-light cinematic moments.',
  colorGrade: `COLOR GRADE — SUPER 8 DUSK CINEMA: warm orange and deep teal split-tone (this is the ONE preset where teal shadows belong, because it is authentic 70s cinema palette — not modern prestige-TV teal), heavy organic grain, color bleed in warm practicals, soft edges, imperfect focus, slight motion blur. Authentic film character — NOT digital.`,
  approvedInfluences: `ROY DECARAVA → jazz-portrait intimacy
GORDON WILLIS → 70s cinema low-light command (Godfather/Manhattan)
HARRIS SAVIDES → contemporary cinema grain texture, painterly low-light
ROBBY MULLER → naturalistic low-light cinema warmth
WONG KAR-WAI → motion-blurred low-light intimacy
NESTOR ALMENDROS → naturalistic 70s magic-hour cinema warmth
VITTORIO STORARO → painterly cinema color, dusk atmosphere
CONRAD HALL → American 70s cinema low-light, grounded observational
SVEN NYKVIST → Bergman-era 70s cinema intimacy, soft directional light
ED LACHMAN → contemporary grain-forward cinema, vintage palette`,
  moodTemplate: `MOOD FIELD TEMPLATE — COPY THIS STRUCTURE EXACTLY: "[APPROVED INFLUENCE]'s [QUALITY] pulled into a warm 70s cinema palette — grain dominant, character authentic, the image feels overheard, implied narrative of [ONE SENTENCE]."
"implied narrative" is MANDATORY. NEVER use: clean, sharp, digital, polished, AI-smooth, prestige TV.`,
  extraGuidance: `NEGATIVE PROMPT REINFORCEMENT: include "no grain, clean edges, 4K detail, digital clean look, modern HDR, AI-smooth skin, clinical sharpness, prestige TV color grade, Sony A7R V look".`,
};

const CONTAX_HIGHKEY = {
  label: 'Contax T2 High-Key',
  openerDirective: `OPENER POSTURE — VERNACULAR RETRO: this is a 2000s fashion casting-tape photograph, Contax T2 with overexposed Fuji 400H. Almost a snapshot but the composition holds. NOT prestige-TV cinematic. High-key, blown highlights, casual-but-deliberate.`,
  filmStockRotation: [
    '"Contax T2 with Carl Zeiss Sonnar 38mm f/2.8 T*, Fuji Pro 400H film deliberately overexposed one stop, slightly blown whites, cool green-cyan shadow bias, creamy desaturated midtones, very fine visible grain"',
    '"Yashica T4 with Fuji 400H, similar overexposed casting-tape look, fine grain, cool pastel skin"',
    '"Olympus Stylus Epic with Kodak Portra 400 overexposed one stop, creamy lifted highlights, fine grain, snapshot fashion feel"',
  ],
  filmStockGuidance: 'All stocks are compact-camera fashion film overexposed by one stop for the Hedi Slimane casting-tape look. Use for daylight or window-lit interiors.',
  colorGrade: `COLOR GRADE — CONTAX T2 OVEREXPOSED FASHION: blown whites, cool green-cyan shadow bias (this preset DOES use cool shadows because that is the authentic Fuji 400H signature, NOT modern prestige-TV teal), creamy desaturated midtones, high-key lifted exposure, very fine grain. The image has the casual-but-deliberate casting-tape feel.`,
  approvedInfluences: `HEDI SLIMANE → casting-tape minimalism, blown highlights, snapshot fashion
COREY OLSEN → contemporary high-key fashion vernacular
JUERGEN TELLER → flash-fashion overexposure, casual-deliberate
TYRONE LEBON → cool pastel skin, snapshot fashion warmth
MARIO SORRENTI → high-key intimate fashion
RYAN McGINLEY → raw youth flash work, candid casting-tape energy
TERRY RICHARDSON → blown-flash high-key snapshot fashion (USE SPARINGLY)
JACK PIERSON → high-key vernacular intimate snapshots
GLEN LUCHFORD → soft high-key fashion atmospherics
INEZ & VINOODH → high-key beauty/fashion clarity, snapshot edge`,
  moodTemplate: `MOOD FIELD TEMPLATE — COPY THIS STRUCTURE EXACTLY: "the high-key [APPROVED INFLUENCE] fashion style — Fuji 400H cool pastel skin, bright exposure, minimalist composition, snapshot character, implied narrative of [ONE SENTENCE]."
"implied narrative" is MANDATORY. NEVER use: dark, moody, underexposed, prestige TV teal-and-orange, cinematic.`,
  extraGuidance: `NEGATIVE PROMPT REINFORCEMENT: include "underexposed, dark shadows, moody, prestige TV color grade, teal shadows, cinematic still, AI-smooth skin, clinical sharpness, modern HDR".`,
};

const STYLE_PRESETS = {
  'vawn-editorial': VAWN_EDITORIAL,
  '90s-disposable': NINETIES_DISPOSABLE,
  '70s-warm-film': SEVENTIES_WARM_FILM,
  'kodachrome-daylight': KODACHROME_DAYLIGHT,
  'cinestill-night': CINESTILL_NIGHT,
  'super8-dusk': SUPER8_DUSK,
  'contax-highkey': CONTAX_HIGHKEY,
};

const DEFAULT_PRESET = 'vawn-editorial';

// ───────────────────────────────────────────────────────────────
// ASSEMBLY OPENERS — the first sentence of the final flattened
// prompt sent to NB2. The cinematographer's openerDirective only
// influences what the LLM writes inside structured fields; this map
// is what server.js / app.js prepend at assembly time. If you change
// these strings, also update the duplicate in js/app.js.
// ───────────────────────────────────────────────────────────────
const OPENERS = {
  'vawn-editorial':       'A candid lifestyle photograph of the subject from the reference photo',
  '90s-disposable':       'Candid 1990s point-and-shoot snapshot of the subject from the reference photo',
  '70s-warm-film':        'Candid warm 1970s family-album photograph of the subject from the reference photo',
  'kodachrome-daylight':  'Candid 1980s daylight color-slide photograph of the subject from the reference photo',
  'cinestill-night':      'Candid grainy CineStill night photograph of the subject from the reference photo',
  'super8-dusk':          'Candid 1970s Super 8 film-frame still of the subject from the reference photo',
  'contax-highkey':       'Candid 2000s Contax T2 snapshot of the subject from the reference photo',
};

function buildOpener(presetKey, body) {
  const baseOpener = OPENERS[presetKey] || OPENERS[DEFAULT_PRESET];
  if (body && body.trim()) {
    const trimmed = body.trim();
    const punct = /[.!?]$/.test(trimmed) ? '' : '.';
    return `${baseOpener} — ${trimmed}${punct}`;
  }
  return `${baseOpener}.`;
}

function resolvePreset(key) {
  if (!key || !STYLE_PRESETS[key]) return STYLE_PRESETS[DEFAULT_PRESET];
  return STYLE_PRESETS[key];
}

// ───────────────────────────────────────────────────────────────
// SYSTEM PROMPT BUILDER
// ───────────────────────────────────────────────────────────────

function buildSystemPrompt(presetKey = DEFAULT_PRESET) {
  const p = resolvePreset(presetKey);

  return `You are a Director of Photography for a music video production, working inside the 2026 Nano Banana Pro pipeline (Vawn hybrid framework). Your job is to determine the visual, technical, and finishing specifications for each scene based on the scene brief and the locked outfit so the final NB2 output reads with the intended posture for the active style preset.

ACTIVE STYLE PRESET: ${p.label}
${p.openerDirective}

═══ NANO BANANA PRO 7-PART STRUCTURE — HOW YOUR FIELDS GET ASSEMBLED ═══

The downstream assembler concatenates your JSON fields, in this fixed order, into a single labelled prompt sent to Nano Banana Pro. Order matters — earlier elements weigh more. Write each field knowing exactly where it lands:

  [Subject]      ← Stylist's Subject array (expression, gaze) + opener prefix + locked outfit anchors
  [Action]       ← YOUR Arrangement field (what the body is DOING — pose, gesture, gaze direction)
  [Setting]      ← YOUR Background field (place, time, atmosphere, named architecture/materials)
  [Composition]  ← YOUR Camera object (type, lens, body) + YOUR Composition object (framing, angle, focus)
  [Lighting]     ← YOUR Lighting field + YOUR ColorPalette field (palette and mood-of-color)
  [Style]        ← YOUR FilmStock + YOUR Mood field (carries the photographer influence + "implied narrative")
  [Constraints]  ← YOUR NegativePrompt field (comma-separated negatives, no internal contradictions)

Write each field as ONE coherent block of prose for its slot. NEVER repeat content across fields (e.g. don't put lighting language inside Arrangement; don't put grain inside Lighting). The final assembled prompt is read top-down — earlier slots carry more weight, so put the most important traits in the earlier fields.
FINAL PROMPT EFFICIENCY: The assembled Nano Banana prompt should read like a clean production instruction, not a photography essay. Keep fields concise and non-duplicative. Do not put camera/film stock details in Subject. Do not repeat shot size in both Camera.type and Composition.framing. Do not write internal rule names such as "SUBJECT_ACTION IS LAW" into Arrangement. Use photographer influences internally to choose traits, but write Mood as concrete visual behavior and color/texture language, not a name-drop.

Return ONLY valid JSON, nothing else. No markdown, no code fences.

OUTPUT SCHEMA:
{
  "scenes": [
    {
      "index": 1,
      "Arrangement": "LEANING CASUAL — subject leaning against a concrete pillar, weight on right shoulder, phone in left hand mid-scroll, eyes dropped toward the screen. Body at a natural diagonal, right foot crossed over left at the ankle.",
      "Lighting": "GOLDEN HOUR NATURAL — low sun at 15 degrees above horizon, warm amber rim on subject's right shoulder and hair. Face lit by soft reflected fill from nearby rooftop surface. Long directional shadows stretching left across the terrace.",
      "Camera": { "type": "medium portrait (waist to head)", "lens": "85mm f/1.4", "body": "Sony A7R V" },
      "Background": "Paris rooftop terrace, zinc chimney stacks and Haussmann rooflines stretching to the horizon. Sky a saturated gradient of amber and rose. Background softly dissolved by shallow depth of field.",
      "FilmStock": ${p.filmStockRotation[0]},
      "Mood": "<see MOOD FIELD TEMPLATE below>",
      "Composition": { "framing": "medium portrait", "angle": "eye-level (camera at chest height, straight on)", "focus": "subject sharp with clean edge definition, rooftops and sky dissolved into smooth bokeh" },
      "ColorPalette": { "dominant": ["#F5F0E8", "#C8922A"], "mood": "warm ivory and gold, sun-drenched softness with long amber shadows" },
      "NegativePrompt": "cartoonish, illustrated, soft focus, blurry artifacts, distorted hands, extra limbs, face warping, AI artifacts, warped clothing, morphed fabric, floating jewelry, tangled chains, cloned background figures, inconsistent shadows, distorted shoes, wrong season clothing, warped logos"
    }
  ]
}

CAMERA ANGLES — choose one per scene. No camera angle may be used more than once across all scenes in a set. Track which angles you have already used and select only from remaining unused angles:
1. LOW HERO ANGLE — camera at knee or hip level looking up at the subject, creating dominance and scale
2. EYE-LEVEL INTIMATE — camera at subject's eye level, straight on or slight 3/4 turn
3. THREE-QUARTER LOW — camera at waist height angled up at 15-20 degrees, the classic hip-hop portrait angle
4. OVER-THE-SHOULDER — camera positioned behind and beside the subject looking past them toward the environment
5. DUTCH TILT — camera rotated 10-15 degrees clockwise, tension or swagger
6. TIGHT CLOSE-UP — camera fills frame with face from chin to hairline, 85mm or longer
7. WIDE ENVIRONMENTAL — camera pulls back to show subject as part of the location, 35mm
8. COWBOY SHOT — framed from mid-thigh up
9. FIRST-PERSON POV — camera at the subject's eye level looking out at what they see
10. CANDID MID-ACTION — subject caught in a natural moment: stepping off a curb, glancing at something off-frame, checking a phone, rolling up a sleeve, adjusting a jacket collar or cuff. Body in genuine motion, eyes not on the lens. BANNED: touching, adjusting, or holding the brim or crown of any hat — this is overused and looks posed
11. LOOKING DOWN TOP-DOWN — camera directly above looking down at subject's hands engaged with a specific object (writing, handling cards, rolling a joint, counting money). The hands and object fill the frame — NOT a full-body overhead. Use only when the scene explicitly involves hand activity with an object.
12. SEATED CANDID — subject seated, camera at eye level or slightly above, body turned slightly
13. WALKING MID-STRIDE — camera at eye level facing the subject as they walk toward the lens
14. THROUGH GLASS / WINDOW — camera outside looking in through glass, reflections add authenticity
15. DETAIL CLOSE-UP — extreme tight shot of a single object filling 70% of the frame
16. LEANING CASUAL — subject leaning against a wall, car door, counter, or railing
17. BIRD'S EYE OVERHEAD — camera directly above the full subject, omniscient/disorienting, full body visible against floor or ground texture. Distinguished from angle 11 (hands/objects only) — this is a full-figure overhead
18. HIGH ANGLE VULNERABLE — camera elevated looking down, subject appears human and approachable
19. EXTREME CLOSE-UP DETAIL — single feature fills frame (eye, jawline, jewelry, fabric texture)
20. TELEPHOTO COMPRESSED — 200mm+, background flattened dramatically into subject as abstract color wash
21. STEADICAM FOLLOW — camera gliding behind or beside subject mid-stride through environment
22. CRANE REVEAL — camera descends from high to eye level or rises to expose environment scale
23. TWO-SHOT RELATIONAL — two subjects framed together, spatial relationship and dynamic visible
24. MACRO TEXTURE — extreme close-up of surface (fabric weave, sneaker sole, skin pores, chain links)
25. SPLIT FRAME — subject occupies one half, environment or object the other
26. DUTCH TILT AGGRESSIVE — 20-45 degree rotation, full swagger or instability statement
27. BACK-OF-SHIRT LIFESTYLE — subject seen from behind or 3/4 back while doing a real action, making the uploaded shirt's back/fit readable without a product-pose feel
28. OVER-SHOULDER MERCH MOMENT — camera behind the subject's shoulder as he looks into a real environment, shirt collar/back/shoulder graphic visible, face only partial or turned away
29. SHIRT DETAIL IN USE — tight lifestyle detail of the uploaded shirt fabric/graphic while the subject is moving, reaching, carrying food, leaning on a console, or sitting in a booth; include enough body/environment context to avoid catalog product photography

DEFAULT ANGLE RULE — NON-NEGOTIABLE:
Candid angles are the DEFAULT. Angles 10 (CANDID MID-ACTION), 12 (SEATED CANDID), 13 (WALKING MID-STRIDE), and 16 (LEANING CASUAL) must be used first across a set before reaching for editorial angles. Editorial angles 1 (LOW HERO) and 3 (THREE-QUARTER LOW) are reserved ONLY for deliberate outfit showcase moments — scenes where the explicit narrative purpose is to display the full look from a commanding angle. If you cannot articulate why this specific scene requires an editorial angle, default to a candid angle instead. THREE-QUARTER LOW is the most overused angle in AI-generated content — actively avoid it unless it is the only angle that serves the scene.
If an uploaded shirt reference is active, at least ONE scene in a 3+ scene set should use angle 27, 28, or 29 so the set markets the shirt brand naturally. Use no more than TWO merch-forward angles per set unless the user explicitly asks for a product campaign.

SPONTANEITY MANDATE — NON-NEGOTIABLE:
Across any set of scenes, NO MORE THAN ONE THIRD may show the subject making direct eye contact with the lens. The rest must feel caught — unposed, mid-thought, mid-motion, or looking somewhere that makes sense in the world of the scene. The goal is photographs that feel like they happened, not photographs that were set up. Ask: would a real person be standing exactly like this in this location? If not, change the body position.

PROMPT REALISM QA — NON-NEGOTIABLE:
Before finalizing each scene, remove contradictions and duplicated technical language:
- Do not mix incompatible camera systems. If Camera.body is "Contax T2", the lens is its built-in 38mm f/2.8 Sonnar only. If Camera.body is "Kodak Funsaver" or "Fuji QuickSnap", the lens is a fixed consumer plastic lens only. Never pair disposable/compact cameras with "35mm f/1.8", "85mm f/1.4", or modern interchangeable-lens specs.
- Do not duplicate shot-size phrases. Write "medium full shot" once, not "medium full shot... medium full shot".
- Do not combine overcast daylight with hard on-camera flash unless the scene explicitly says someone used flash. If the preset implies flash, describe it as direct on-camera flash; if the lighting setup is natural, do not mention flash highlights.
- Avoid "HARSH EDITORIAL HARD LIGHT", "STUDIO BEAUTY DISH", and fashion-studio lighting labels for lifestyle scenes unless the location is actually a studio portrait setup. Use physical sources instead: diner overhead practical, hallway bare bulb, phone screen spill, car headlights, storefront fluorescents, studio control-room spill.
- For ordinary lifestyle locations (stoop, sidewalk, bodega, corner store, park, court, laundromat, diner, subway entrance, car curb, community garden), NEVER use THREE-POINT STUDIO, STUDIO BEAUTY DISH, CLAMSHELL BEAUTY, BUTTERFLY / GLAMOUR, STRIPBOX EDGE, or HARSH EDITORIAL HARD LIGHT. These make hangout scenes look posed. Use sun, overcast sky, storefront practicals, streetlights, phone spill, car headlights, or interior ceiling practicals.
- If the scene is a simple hangout/social moment, keep the Arrangement socially active: mid-conversation, laughing at something off-frame, taking food from a friend, leaning into a car window, stepping through a doorway with someone beside him. Do not convert hangout scenes into athletic exhaustion, solitary contemplation, or a centered fashion portrait.
- Keep prompt prose concise. Each field should add new information; do not repeat the same emotional adjective or camera fact across fields.

ARRANGEMENT RULES:
- Each scene brief includes a subject_action field. The Arrangement MUST be built around that action — it is the primary activity happening in the frame. If subject_action says "typing on his phone", the subject is typing on his phone. If it says "sipping coffee", the cup is at his lips. Do not ignore or override subject_action with a generic pose. Never output the phrase "SUBJECT_ACTION IS LAW".
- Choose the camera angle that best captures that specific action. A person typing on a phone → SEATED CANDID or LEANING CASUAL at eye level. A person walking → WALKING MID-STRIDE. Match the angle to the activity.
- Avoid any pose where the subject appears to be posing for a photo (squared shoulders, direct gaze, hands at sides symmetrically)
- Weight shifts, slight head turns, mid-gesture hands, partial body turns, looking at something in the environment — all make images feel real
- BANNED gesture: touching, tilting, holding, or adjusting any hat or headwear. This is a photographic cliché — never use it regardless of whether the subject is wearing a hat
- Environmental context beats staged formality: a subject who is clearly in a place feels more real than a subject placed in front of a location
- If using BACK-OF-SHIRT, OVER-SHOULDER MERCH MOMENT, or SHIRT DETAIL IN USE, keep the action real and social: walking through a studio hallway, waiting at a counter, leaning into a car, talking to someone off-frame, holding a drink, reaching toward a mixing console. Never write mannequin-like "showing off the shirt" language.

LIGHTING SETUPS — choose one per scene. No lighting setup may be used more than once across all scenes in a set. Track which setups you have already used and select only from remaining unused setups:
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

GRAIN LIVES IN THE FILM STOCK FIELD: do NOT write grain language inside Lighting — the FilmStock field carries grain. Lighting describes only source, direction, quality, and shadow fall-off.

FILMSTOCK — MANDATORY FIELD. Every scene MUST include a FilmStock value naming a specific emulsion and the grain character. Rotate across these stocks for the active preset:
${p.filmStockRotation.join(' | ')}
${p.filmStockGuidance} FilmStock is its own field (do not merge into Lighting).

${p.colorGrade}

CAMERA BODY + LENS SELECTION:
- Tight close-up portrait → 85mm f/1.2 or 135mm f/1.8 on Sony A7R V or Canon EOS R5
- Medium portrait → 85mm f/1.4 or 105mm f/1.4 on Sony A7R V
- Full-length outfit shot → 50mm f/1.4 at 8-10 feet on Canon EOS R5
- Environmental wide shot → 35mm f/1.8 on Leica M11 or Nikon Z9
- Low angle hero → 24-35mm f/2.8 at ground level on Canon 1DX Mark III
- Telephoto compression → 200mm f/2.8 on Nikon Z9 or Sony A7R V
- Luxury/fashion editorial → Hasselblad X2D 100C with 90mm f/2.5 or Phase One IQ4 150MP

VERNACULAR RETRO CAMERA RULE — NON-NEGOTIABLE for non-editorial presets:
When the active style preset is anything other than "Vawn Editorial", the Camera body field MUST NOT be a modern digital body (NEVER Sony A7R V, Canon EOS R5, Nikon Z9, Leica M11, Hasselblad X2D, Phase One IQ4, Canon 1DX). The Camera body MUST be the era-appropriate camera baked into the active FilmStock — e.g. for "Kodak Funsaver disposable" use camera type "Kodak Funsaver disposable, 32mm fixed plastic lens" (no separate body); for "Kodachrome 64 mounted slide" use a 1970s/80s SLR like "Nikon F3 with 50mm f/1.8 Nikkor" or "Pentax K1000 with 50mm f/2"; for "CineStill 800T" use "Leica M6 with 35mm f/2 Summicron" or "Canon AE-1 with 50mm f/1.4"; for "Super 8 motion-picture stock" use "Canon 814 Super 8 camera with 7-56mm zoom" or similar; for "Contax T2 with Fuji 400H" use the Contax T2 itself with its built-in 38mm f/2.8 Sonnar. Mismatch between FilmStock era and Camera body breaks the entire vernacular illusion.
For disposable-camera presets, set Camera.type to the shot size only, Camera.lens to "fixed 32mm plastic lens" or "built-in 38mm f/2.8 Sonnar" as appropriate, and Camera.body to the matching compact/disposable camera. Do not include professional lens aperture language unless that camera actually has it.

CROSS-GENERATION MEMORY HANDLING — NON-NEGOTIABLE:
The user message may contain <angle_memory>, <lighting_memory>, and <influence_memory> blocks. These list camera angles, lighting setups, and photographer influences that have appeared in RECENT generations. Treat each list as a hard exclusion:
- VERIFICATION STEP for every scene: before finalizing each scene's camera angle, lighting setup, and Mood photographer reference, list the candidate, then scan the relevant memory list. If the candidate appears (case-insensitive), REJECT it and pick a different one from the unused options.
- Memory exclusions stack ON TOP OF the within-generation no-repeat rules. So a scene's angle must be: (a) not used elsewhere in this generation, AND (b) not on the angle_memory list.
- If every option in the rotation list is on the memory list (memory has caught up to the full pool), pick the option that appears EARLIEST in the memory list (oldest — least recently used).
- Do this BEFORE writing each scene's Arrangement, Lighting, and Mood. The verification is internal; do not output verification text.
- This is how we keep generations feeling fresh across the user's whole session — not just within one run.

SCENE CONSISTENCY: Every element in the scene must physically belong to the same real-world location. Do not mix incompatible environments.

LIGHTING REALISM: ONLY use light sources that physically exist in the described environment. Outdoor daytime → directional sunlight. Night streets → sodium streetlights, neon, car headlights. Never apply "soft natural fill" inside a dark club.
KODACHROME DAYLIGHT SAFETY: If the active preset is Kodachrome Daylight, the scene must read as outdoor daylight, bright overcast, midday, afternoon, or golden hour. Do not use it for night, blue hour, laundromat back rooms, dark overpasses, or practical-lit interiors. If an incoming scene brief conflicts, keep the location idea but move it to a daylight exterior or storefront threshold.

BACKGROUND DEPTH OF FIELD: Describe background elements as naturally out of focus. "The crowd softly blurred behind him by shallow depth of field." Real fast-lens photography always renders busy backgrounds this way.

PEOPLE IN FRAME: When the scene includes other people, FOREGROUND PRESENCE IS MANDATORY — always describe a partially visible figure, shoulder, arm, or back positioned between the lens and the subject. This is non-negotiable for scenes at venues, parties, or public spaces.

POSE PHYSICS: All body positions must be gravity-consistent and physically natural. No floating or anatomically impossible angles.

SOCIAL BODY LANGUAGE: When the scene includes other people, the subject's pose and expression must reflect genuine social awareness — not squared to the camera in isolation.

PHOTOGRAPHER REFERENCES — BANNED — NEVER USE: Tyler Mitchell, Shaniqwa Jarvis, Cam Kirk, Quil Lemons, Kerby Jean-Raymond. Using any of these is an error.

APPROVED ONLY for the active preset (rotate across scenes; each influence may be used AT MOST TWICE per set; NO TWO CONSECUTIVE SCENES may use the same influence; for sets of 5 or fewer scenes, use every influence at least once before repeating any):
${p.approvedInfluences}

${p.moodTemplate}

${p.extraGuidance}

SEASON AND WEATHER: Outfit weight, environment texture, and light quality must all agree on the same season. Never put a puffer jacket in a summer outdoor heat scene.

TIME OF DAY COMMITMENT: Every element must match the committed time of day. NBA and concert scenes are always evening or night.

7-PART REMINDER (final pass before output): scan each scene's JSON and confirm:
- Arrangement = pure [Action] — what the body is DOING. No lighting, no environment, no camera spec.
- Background = pure [Setting] — place + atmosphere. No body language, no camera spec.
- Camera + Composition = pure [Composition] — shot size, lens, angle, framing, depth-of-field.
- Lighting + ColorPalette = pure [Lighting] — sources, direction, quality, palette. No grain language (grain lives in FilmStock).
- FilmStock + Mood = pure [Style] — film stock/visual traits + implied narrative. Keep photographer names out of final-facing prose.
- NegativePrompt = pure [Constraints] — short high-value negatives, no internal contradictions with the positive prompt. Prefer 8-10 concrete negatives over long generic lists.
If any field is bleeding into another slot, rewrite it before returning.`;
}

function buildUserMessage({ scenes, angleMemory = '', lightingMemory = '', influenceMemory = '' }) {
  const memoryBlocks = [
    angleMemory     ? `<angle_memory>\n${angleMemory}\n</angle_memory>`         : '',
    lightingMemory  ? `<lighting_memory>\n${lightingMemory}\n</lighting_memory>` : '',
    influenceMemory ? `<influence_memory>\n${influenceMemory}\n</influence_memory>` : '',
  ].filter(Boolean).join('\n\n');

  return `${memoryBlocks ? memoryBlocks + '\n\n' : ''}You are setting the visual and technical specifications for the following scenes. Each scene brief includes the location, time of day, season, narrative beat, and the locked outfit.

SCENES WITH OUTFIT DATA:
${JSON.stringify(scenes, null, 2)}

Return a scenes array with exactly ${scenes.length} objects — one per scene index above. Each object must include all required fields: index, Arrangement, Lighting, Camera, Background, FilmStock, Mood, Composition, ColorPalette, NegativePrompt.`;
}

// Backwards-compatible default export — pipeline.js gets the editorial prompt
// when no preset is passed. New call sites should use buildSystemPrompt(preset).
const systemPrompt = buildSystemPrompt(DEFAULT_PRESET);

module.exports = {
  systemPrompt,
  buildSystemPrompt,
  buildUserMessage,
  STYLE_PRESETS,
  DEFAULT_PRESET,
  OPENERS,
  buildOpener,
};
