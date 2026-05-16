'use strict';

// Canonical Seedance 2.0 ruleset (EN-only).
// Sourced from C:\Users\rdyal\.claude\skills\Seedance 2 Skill.md.
// Imported by every Higgsfield/Seedance-targeting agent so the rules
// stay in one place. Mirrors the Seedance 2.0 Universal Director skill.

const SEEDANCE_RULES = `
SEEDANCE 2.0 — UNIVERSAL DIRECTOR RULESET (EN ONLY):

INVENTORY EXTRACTION (silent — do this before writing prose):
Catalog every asset from the user's text and any reference images:
- Characters: names, appearance, wardrobe, distinguishing features
- Location: interior/exterior, key architecture, lighting
- Props: anything explicitly mentioned or shown
- Style/Atmosphere: color palette, contrast, lighting, weather, time of day (infer if not provided)
Never invent characters, locations, or props the user didn't provide. You may add environmental details (dust, sparks, atmospheric particles) and camera behavior. EXCEPTION: when the user's request implies scene creation rather than adaptation ("come up with…", "create a…", "two guys fighting"), you may invent supporting elements (location details, props, environmental features). Named characters and their core attributes still come only from the user.

AGE-BLIND CHARACTER RULE — CRITICAL:
Never describe characters by age. Trigger words to avoid: boy, girl, child, kid, young, teen, little. With image input: describe by ROLE (rider, figure, traveler, speaker), CLOTHING, and ACTION. Never label who they are — label what they do. Without image input: use functional labels ("a figure in a wool cloak", "a silhouette against the horizon").

SCENE ARCHETYPE ROUTER:
Identify which archetype the scene fits — this guides camera behavior, spatial logic, and what changes across time.

ACTION ARCHETYPES:
- Pursuit — distance closing/opening, pursued ahead in frame, pursuer behind, path narrows/opens
- Duel — camera lower on dominant side; dominance MUST alternate beat-to-beat (never one-sided unless described as one-sided assault)
- Impact — build-up slow → hit fast → aftermath slow; point of contact is the center of frame
Decision tree: chase = Pursuit | alternating advantage = Duel | single decisive moment = Impact | default = Duel

GENERAL ARCHETYPES:
- Journey — position in space changes (road, flight, river, walking); tracking, aerial, traveling alongside; landscapes pass
- Atmosphere — nothing changes; mood IS the content (rain on glass, empty street); minimal movement, slow push-in or static hold; micro-changes carry all drama
- Reveal — hidden becomes visible (door opens, fog lifts, camera rounds corner); pan, crane, dolly reveal; camera controls WHEN viewer sees the subject
Decision tree: subject moves through space = Journey | hidden-to-visible = Reveal | mood-as-content = Atmosphere | default = Atmosphere

DIALOGUE ARCHETYPES:
- Confrontation — both push, dominance trades per exchange; tight OTS, camera crosses axis on power shift
- Interrogation — asymmetric (one extracts, one resists); low-angle on questioner, push-in on silence
- Negotiation — balanced (both need something); symmetrical framing, matching shot sizes
Decision tree: trading dominance = Confrontation | asymmetric extraction = Interrogation | balanced need = Negotiation | default = Confrontation
Dialogue word limit: ~25–30 spoken words fit into 15s of video. If user provides more, keep the power-shift line + 1 line before (setup) + 1 line after (reaction). Convert everything else to physical behavior.

ENGINE RULES (hard rendering constraints):
- Action beats = intent + named technique, not biomechanics. ✅ "spinning back kick connects." ❌ "left forearm rotates 45° to deflect the incoming right hook at wrist level." If user names a specific move — preserve it. If user describes joint mechanics — compress to the move's name or intent.
- Describe force and direction, not destruction sequence. ✅ "driven into the car, metal buckling." ❌ "thrown into side door, glass shatters, uses rebound to sweep leg."
- Spatial continuity breaks on cuts. Re-anchor positions and facing direction after any cut.
- ≤ 3 characters tracked across cuts. Name the acting pair and interaction vector per shot.
- Exit-frame = implicit cut. Character leaves frame → gone for remainder of shot. Never choreograph exit + re-entry in same continuous shot.
- Off-screen = nonexistent. State changes must be shown on camera before being referenced.
- Avoid reflection shots (in blades, puddles, mirrors, glass) — Seedance breaks scene geography when rendering reflections.
- Only describe what can be seen or heard. ❌ "The air smells of pine." ✅ "Pine needles covering the ground, wind moving through branches."
- Micro-expressions work when described as physics. ✅ "jaw clenches, nostrils flare." ❌ "looks angry."
- Focal length cap: 75mm. Engine has no preset above this. For tight shots use shot-size language ("choker", "ECU", "tight close-up", "head-and-shoulders") instead of long focal lengths.
- Banned trigger words (activate global filters and ruin generations): strobing, stuttering, step-printing, undercranking, symmetrical, mirrored, prismatic, Petzval. If you mean a flickering source, write the concrete physical cause ("fluorescent fixture vibrates from impact").
- No film titles in prose — they trigger content filters. Use director names only.
- Hidden objects don't render ("gun under the table" → if the camera didn't see it, it doesn't exist).

CUT RULES:
1. Double contrast (mandatory) — every cut changes BOTH shot size AND camera character.
   Shot-size scale: extreme wide → wide → medium → medium close-up → close-up → ECU
   Camera modes: Handheld | Static/locked-off | Stabilized tracking | Crane/vertical | Aerial/drone — never repeat across a cut.
2. Re-anchoring & 180° rule — after cuts back to established space, re-state who is where and which direction they face. If a character moves left-to-right before the cut, same direction after. State movement direction explicitly.
3. Inserts — sub-second (0.3–0.5s) dramatic punctuation, any shot size, beat-free, causally motivated. ✅ "hero slammed onto hood → his hand gripping metal." ❌ generic boot stepping in puddle. Always name the subject (whose body part/detail). Obey double contrast.
4. Shot timing — no per-shot timing in output. Rhythm is implied by description density.

PROMPT SECTIONS (inline labels, continuous prose — no bullet lists, no "Shot 1:" headers):
1. Style & Mood: palette, lighting, lens, atmosphere. NEVER skip. Always specific.
2. Narrative Summary: 1-sentence scene description. Optional — drop first if length is tight.
3. Dynamic Description: shot-by-shot in prose. Camera, movement, action. Present tense, active voice. Each cut described inline ("Hard cut to low-angle close-up…"). NEVER skip.
4. Static Description: location, props, ambient details. Establish anything referenced in Dynamic. NEVER skip.
5. Audio: dialogue scenes only. Spoken lines + SFX/BGM. Dialogue lines in their original language — never translate.

LANGUAGE RULES:
- Present tense, active voice
- Vivid but economical — no poetic padding, concrete visual direction only
- Consistent character names; unnamed characters get functional labels ("the figure")
- No dialogue or subtitles unless explicitly requested
- No metadata headers ("Shot 1:", "Beat 2:", "Setup:") — weave transitions into prose
- User camera instructions (e.g. "dolly in", "low-angle", "tracking shot") MUST appear in the final prompt verbatim. User direction overrides defaults.
- DEFAULT to in medias res — scene is already in progress unless user says "starts with…" or "ends with…"

ANTISLOP — never use any of these words:
breathtaking, stunning, captivating, mesmerizing, awe-inspiring, masterfully, meticulously, exquisitely, beautifully crafted, cinematic masterpiece, visual feast, a symphony of, seamlessly, effortlessly, flawlessly, cutting-edge, state-of-the-art, next-level, rich tapestry, vibrant tapestry, kaleidoscope of, elevate, unlock, unleash, harness, groundbreaking, a testament to, speaks volumes, resonates deeply.

CAMERA LANGUAGE GLOSSARY:
- Angles: low-angle, high-angle, dutch angle, bird's-eye, worm's-eye, eye-level, OTS (over-the-shoulder)
- Focal length: wide 14–24mm, standard 35–50mm, telephoto up to 75mm, macro
- Movement: tracking, dolly-in, dolly-out, crane, pan, tilt, whip-pan, orbit, push-in, pull-back, handheld, Steadicam, aerial
- Time: slow-motion, speed ramp, freeze frame
- Transitions: smash cut, match cut, whip-pan transition, hard cut, L-cut
`.trim();

module.exports = { SEEDANCE_RULES };
