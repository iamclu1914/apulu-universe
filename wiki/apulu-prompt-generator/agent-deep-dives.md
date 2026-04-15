# Apulu — Agent Deep Dives

**Source files:** `Agent Pipeline.md`, `Architecture.md`, `UI Modes.md`
**Compiled:** 2026-04-07

---

## Summary

Detailed breakdown of each agent in the [[overview|Apulu Prompt Generator]] pipeline. Each agent is a JS module (`agents/*.js`) exporting `{ systemPrompt, buildUserMessage }`, called sequentially by the [[ui-modes-and-pipeline|pipeline orchestrator]].

---

## Treatment Director (Stage 0)

- **File:** `treatment-director.js`
- **Model:** Gemini 2.5 Flash
- **When:** HF MV mode only (non-fatal, optional)
- **Timeout:** 30s

**What it does:**
- Analyzes lyrics for emotional arc
- Produces a structured shot plan: concept, hero shots, visual identity, lighting philosophy
- Now includes **acquisition context** per shot: camera body, lens, focal length (e.g., "ARRI ALEXA 35, Cooke S4 50mm, f/2.8")
- Outputs **prompt style** recommendation per shot: `physics_first` (vivid action, trust the engine) or `director_upgrade` (Setting/Subject/Camera/Lighting/Style structure)
- Can recommend **speed ramp** presets: "Impact" (accelerate at collision) or "Bullet Time" (dilate at hit)
- Output enriches the `anchorBlock` passed to Scene Architect

**Failure mode:** Pipeline continues without it — graceful degradation. Scene Architect works fine with raw lyrics alone; Treatment Director just provides richer context.

**Key insight:** This is the only agent that acts as an enhancer rather than a required pipeline stage. It pre-digests creative intent so downstream agents make better decisions. Since the April 2026 philosophy shift, the Treatment Director also guides which shots should use vivid physics-first prompting vs. director-level acquisition context.

---

## Scene Architect (Stage 1)

- **File:** `scene-architect.js`
- **Model:** Gemini 2.5 Flash
- **Fatal:** Yes
- **Timeout:** 30s

**What it does:**
- Assigns one of the 7 [[style-system|style worlds]] per scene
- Sets location, time of day, season
- Produces `narrative_beat` and `subject_action` per scene
- Enforces: no two scenes share the same style world (for sets ≤7)
- Uses `styleWorldMemory` from the frontend to avoid worlds used in prior generations within the session

**Receives:** Lyrics/description + optional Treatment Director anchor block
**Outputs:** Array of scene objects with structure metadata

**Key insight:** The Scene Architect makes the highest-leverage creative decisions in the pipeline — style world assignment determines the entire visual direction, brand palette, and color options for everything downstream.

---

## Stylist (Stage 2)

- **File:** `stylist.js`
- **Model:** Gemini 2.5 Flash
- **Fatal:** Yes (1 retry on empty scenes array)
- **Timeout:** 45s

**What it does:**
- Assigns full outfit per scene: top, bottom, outerwear, headwear, footwear, jewelry
- Enforces the [[style-system|shoe color-lock rule]] — shoe dominant color must match shirt dominant color via 16-row lookup table
- Enforces brand no-repeat across all scenes
- Enforces shirt color family no-repeat across all scenes
- Enforces shoe model + colorway no-repeat
- Rotates through 20 headwear types and 11 jewelry pieces
- Uses `wardrobeMemory` from the frontend to exclude previously used garments

**Receives:** Scene Architect output + wardrobe memory + style world memory
**Outputs:** Scene objects enriched with `wardrobe_used` and `MadeOutOf` arrays

**Failure mode:** Gets one retry if it returns an empty scenes array. This is the most complex agent in the system — the style rules create a large constraint space that occasionally produces invalid outputs.

**Key insight:** The Stylist is where constraint-driven creativity is most visible. The combination of color-lock + brand no-repeat + style world restriction forces the agent into novel combinations it wouldn't choose freely. The `wardrobeMemory` carries across generations within a session, so repeated "Generate" clicks produce fresh outfits.

---

## Cinematographer (Stage 3)

- **File:** `cinematographer.js`
- **Model:** Gemini 2.5 Flash
- **Fatal:** Yes
- **Timeout:** 60s (longest of the core agents)

**What it does:**
- Receives merged Scene Architect + Stylist data
- Outputs per scene: Arrangement, Lighting, Camera, Background, Mood, Composition, ColorPalette, NegativePrompt

**Receives:** Merged A1 + A2 scene data
**Outputs:** Complete image prompt components per scene

**Special role:** The Cinematographer is the **authoritative index set**. A scene only appears in the final output if the Cinematographer has data for it. If Scene Architect or Stylist data is missing for a given index, that scene is dropped. This makes Agent 3 the quality gate for the entire pipeline.

**Key insight:** The 60s timeout (longest in the pipeline) reflects the complexity of this agent's task — it must generate coherent visual direction across 8+ fields for every scene while maintaining consistency with the style world's palette and the outfit's color story.

---

## Video Director (Stage 4)

- **File:** `video-director.js` (Kling) / `higgsfield-director.js` (HF) / `higgsfield-multishot-director.js` (HF Multishot)
- **Model:** Gemini 2.5 Flash
- **Fatal:** No
- **Timeout:** 45s (single-shot) / 60s (multishot)

**What it does:**
- Receives merged A1 + A2 + A3 data
- **Kling output:** single `video_prompt` string per scene
- **Higgsfield output:** `camera_movement`, `genre`, `duration`, `start_frame`, `end_frame`, `emotions` per scene
- **Higgsfield Multishot output:** grouped 2–4 shot generations with combined `multi_shot_prompt` and per-shot `description` fields

**Prompt Philosophy (April 2026 shift):**

The HF directors now use two prompt modes based on the viral Reddit prompt insight:

1. **Physics-First mode** — for action/VFX/spectacle scenes. Vivid descriptions of forces, collisions, weight, and speed. Trusts Seedance 2.0's physics engine and cinematic reasoning. Example: *"Post-apocalyptic trucks escaping asteroid shower, asteroids crash into sand creating towering heavy debris explosions, energetic camera movements, cinematic epic action."*

2. **Director's Upgrade mode** — for character/intimate/establishing scenes. Uses acquisition context structure: Setting → Subject → Camera (body + lens + focal length + aperture) → Lighting (source + direction + quality) → Style (genre + aesthetic + scale). Example: *"Setting: Rooftop at dusk. Subject: @Vawn leaning on the railing, wind pulling at his jacket. Camera: ARRI ALEXA 35, Cooke S4, 50mm, shallow f/2.8. Lighting: golden hour backlight, warm rim highlights. Style: intimate drama."*

The agent chooses which mode based on the scene's content — action scenes get physics-first, character moments get Director's Upgrade.

**Failure mode:** Result returns without video prompts (`video_prompts_failed: true`). The frontend still displays image prompts — video is optional enrichment.

**Key insight:** The Video Director is platform-aware — separate agent files exist for Kling vs. Higgsfield vs. Higgsfield Multishot. The Higgsfield directors now balance between trusting the engine (for physics-heavy scenes) and providing precise directorial constraints (for character work). This dual-mode approach was validated by the r/generativeAI community's viral prompt analysis.

---

## Audio Analyzer (Story Chain Stage 0)

- **File:** `audio-analyzer.js`
- **Model:** Gemini 2.5 Flash + Gemini Files API
- **Fatal:** No
- **Timeout:** 90s

**What it does:**
- Only runs if an audio file was uploaded
- Calls Gemini with the audio file via Files API (multimodal)
- Returns structured analysis: BPM, energy arc, sections, mood labels

**Key insight:** This is the only agent that processes non-text input. The 90s timeout accounts for audio upload and multimodal analysis. Its output enriches the Story Director but isn't required — the Story Director can work from concept text alone.

---

## Higgsfield Story Director (Story Chain Stage 1)

- **File:** `higgsfield-story-director.js`
- **Model:** Claude Sonnet 4.6 (the only agent NOT using Gemini)
- **Fatal:** Yes
- **Timeout:** 120s (longest timeout in the system)

**What it does:**
- Receives audio analysis + optional concept text
- Generates chained shots with `is_hero_frame` and `is_continuation` flags
- Produces 4–12 shots depending on config

**Key insight:** This is the only agent powered by Claude instead of Gemini. The 120s timeout and separate `runStoryChain()` pipeline reflect the complexity of generating narratively coherent, chained shot sequences. The `is_hero_frame` flag lets the frontend highlight key moments, while `is_continuation` enables shot-to-shot visual continuity in [[ai-filmmaking/ai-short-film-prompt-library|Higgsfield Cinema Studio]].

---

## Agent Interaction Map

```
Treatment Director (optional)
        ↓ anchorBlock
  Scene Architect ──→ style worlds, locations, narrative beats
        ↓ scenes[]
    Stylist ──→ outfits, shoes, headwear, jewelry
        ↓ scenes[] + wardrobe
  Cinematographer ──→ lighting, camera, composition (AUTHORITATIVE INDEX)
        ↓ scenes[] + wardrobe + cinematography
  Video Director ──→ platform-specific video prompts (optional)
        ↓
  Final Output (merged by scene.index)
```

## Key Takeaways

- 7 agents total across two pipelines, but the core MV pipeline uses 4 (+ optional Treatment Director)
- Each agent has a clear single responsibility — no agent touches another's domain
- Fatal vs. non-fatal distinction allows graceful degradation (Treatment Director, Video Director, Audio Analyzer can fail without killing the pipeline)
- The Cinematographer's role as authoritative index is a deliberate quality gate — not a quirk
- The Stylist is the most constrained agent, operating within shoe color-lock + brand no-repeat + style world palette rules
- Only the Story Director uses Claude — everything else runs on Gemini 2.5 Flash
- See [[ui-modes-and-pipeline]] for pipeline orchestration, [[style-system]] for fashion rules
