# Apulu — UI Modes & Agent Pipeline

**Source files:** `UI Modes.md`, `Agent Pipeline.md`
**Compiled:** 2026-04-07

---

## Summary

The app supports 9 generation modes across three platforms (NB2, Kling, Higgsfield). Each mode runs through a sequenced agent pipeline with different configurations. The pipeline is orchestrated by `agents/pipeline.js`.

## Agent Pipeline

### Main Pipeline: `runPipeline()`

Used for all modes except `hf-story`.

| Stage | Agent | Model | Fatal? | Timeout |
|-------|-------|-------|--------|---------|
| 0 | Treatment Director (HF MV only) | Gemini 2.5 Flash | No | 30s |
| 1 | Scene Architect | Gemini 2.5 Flash | Yes | 30s |
| 2 | Stylist | Gemini 2.5 Flash | Yes (1 retry) | 45s |
| 3 | Cinematographer | Gemini 2.5 Flash | Yes | 60s |
| 4 | Video Director | Gemini 2.5 Flash | No | 45s |

- **Stage 0:** Analyzes lyrics for emotional arc, produces shot plan with acquisition context (camera body, lens, focal length per shot), prompt style recommendations (physics_first or director_upgrade), and optional speed ramp presets. Enriches Scene Architect input. Graceful degradation if it fails.
- **Stage 1:** Assigns style worlds (1–7), locations, time of day, `narrative_beat`, `subject_action` per scene. No two scenes share the same world (≤7 scenes).
- **Stage 2:** Full outfit assignment per scene. Enforces [[style-system|shoe color-lock]], brand no-repeat, wardrobe memory.
- **Stage 3:** Outputs Arrangement, Lighting, Camera, Background, Mood, Composition, ColorPalette, NegativePrompt.
- **Stage 4:** Platform-specific video prompts. HF directors use two prompt modes: physics-first (action/VFX) or Director's Upgrade (character/intimate) with acquisition context. If it fails, result returns without video prompts (`video_prompts_failed: true`).

### Story Chain Pipeline: `runStoryChain()`

Used only for `hf-story` mode. Two stages.

| Stage | Agent | Model | Fatal? | Timeout |
|-------|-------|-------|--------|---------|
| 0 | Audio Analyzer | Gemini 2.5 Flash + Files API | No | 90s |
| 1 | Story Director | Claude Sonnet 4.6 | Yes | 120s |

### Output Assembly

- **Agent 3 (Cinematographer) is the authoritative index set** — a scene only appears in final output if A3 has data for it
- Merged by `scene.index` across all agents
- Final scene object includes: style world, wardrobe, image prompt fields, video prompt, HF-specific fields
- **Wardrobe memory** tracks slots 0–3 (shirt, pants, jacket, hat). Shoes excluded — governed by color-lock rule.

## UI Modes

- **Platform selection:** NB2 (image only), Kling (image + video), Higgsfield (image + video)
- **Input modes:** Lyrics mode or Description mode
- **HF MV sub-modes:** Track mode (audio upload → Treatment Director analysis) or Description mode (text only)

### Mode Config

| Mode | Scenes | Video Director? | Pipeline |
|------|--------|-----------------|----------|
| `mv` | 6–8 | Yes | `runPipeline()` |
| `nb2` | 6–8 | No | `runPipeline()` |
| `kling-9grid` | 9 | Yes | `runPipeline()` |
| `kling-startend` | 2–4 | Yes | `runPipeline()` |
| `hf-mv` | 6–8 | Yes (HF) | `runPipeline()` |
| `hf-9grid` | 9 | Yes (HF) | `runPipeline()` |
| `hf-startend` | 2–4 | Yes (HF) | `runPipeline()` |
| `hf-story` | 4–12 | Separate | `runStoryChain()` |

## Retry & Timeout Logic

- `callWithTimeout()` wraps each agent call with AbortController
- On 429 → wait 8s → retry once
- On 500/503 → wait 1s → retry once
- Other errors → rethrow immediately

## QA Checks

After assembly, checks for duplicate camera moves (HF modes only). Attaches `qa_warnings` if found.

## Key Takeaways

- 4-agent sequential pipeline with clear fatal/non-fatal distinction
- Cinematographer (Agent 3) is the authoritative index — controls which scenes appear in output
- Story chain is a separate pipeline using Claude (not Gemini) for chained narrative shots
- Treatment Director is optional enrichment — pipeline continues without it
- Retry logic handles rate limiting (429) and service issues (500/503) gracefully
- See [[overview]] for project context, [[style-system]] for fashion rules
