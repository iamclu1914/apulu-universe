# Vawn Mix Engine — Overview & Architecture

**Source files:** `Vawn-Mix-Engine-README.md`, `Vawn-Mix-Platform-PRD.md`, `Vawn-Autonomous-Mix-Platform-Blueprint.md`
**Compiled:** 2026-04-07

---

## Summary

A Python application that automates hip-hop mixing and mastering inside REAPER using iZotope plugins. Feed it a folder of audio stems → it builds a REAPER session, processes every track through iZotope's plugin chain → outputs a mastered stereo file plus a mix report.

Built for the [[vawn-project/overview|Vawn]] artist project. Runs locally with REAPER v7+.

## Requirements

- **REAPER** v7+
- **iZotope plugins:** RX 11, Nectar 4, Neutron 5, Ozone 12, Tonal Balance Control 3
- **Python 3.12+** with `reapy` for external REAPER control
- One-time setup: configure Python DLL path in REAPER prefs, run `reapy.configure_reaper()`

## The 5 Pipeline Stages

| Stage | Plugin | Method | Fatal? |
|-------|--------|--------|--------|
| 1 — Vocal Cleanup | RX 11 | RX Batch Processor (semi-autonomous, v1 = manual mode) | Graceful |
| 2 — Vocal Mix | Nectar 4 | ReaScript FX params + Vocal Assistant trigger | Yes |
| 3 — Instrument Mix | Neutron 5 | ReaScript FX params + Mix Assistant trigger | Yes |
| 4 — Reference Analysis | TBC3 | Spectral analysis + bus-level correction (max 3 passes) | Yes |
| 5 — Mastering | Ozone 12 | Master Assistant + LUFS feedback loop (max 3 iterations) | Yes |

**Plugin chains:**
- Vocals: RX 11 → Nectar 4 → Neutron 5
- Instruments: RX 11 → Neutron 5
- Master Bus: TBC3 → Ozone 12

## The Fundamental Constraint

iZotope plugins have **no public API, no CLI, no scripting interface**. All interaction goes through:

| Tier | Method | Used For |
|------|--------|----------|
| 1 | ReaScript FX Params | Nectar 4, Neutron 5, Ozone 12, TBC3, Relay |
| 2 | Preset Loading | Quick plugin state config, A/B comparisons |
| 3 | External Orchestration | RX Batch Processor (SoundFlow/manual) |

Parameter maps translate human-readable names to VST parameter indices. Each plugin has hundreds of params (Nectar 4: 822, Ozone 12: 876). Maps must be enumerated per installation.

## Session Builder

Creates REAPER session from stems:
- Creates tracks per stem, imports audio, sets colors by type
- Applies gain offsets from decision engine
- Loads appropriate plugins (Nectar for vocals, Neutron for instruments)
- Creates 4 buses: VOCAL, DRUM, BASS, INST
- Sets up sidechain routing (kick → 808) if enabled
- Adds TBC3 + Ozone 12 on master bus

## Decision Engine

Rule-based processing decisions driven by audio analysis:
- **RX preset selection:** based on noise floor + clipping detection
- **Gain staging:** per-stem-type peak targets (see [[levels-and-gain-staging]])
- **Nectar params:** stem-type-specific compression, reverb, formant settings
- **Mastering feedback loop:** adjusts Maximizer threshold to hit LUFS target with 0.7 damping factor

## Stem Naming Convention

| Prefix | Type | Prefix | Type |
|--------|------|--------|------|
| LEAD | Lead vocal | 808 | 808 bass / sub |
| DBL | Double/BG vocal | BASS | Non-808 bass |
| ADLIB | Ad-lib vocal | SYN | Synthesizer |
| HOOK | Hook vocal | PAD | Pad / ambient |
| KICK | Kick drum | FX | Sound effects |
| SNR | Snare | KEYS | Piano / keys |
| HAT | Hi-hat | GTR | Guitar |
| PERC | Percussion | STR | Strings |

Unrecognized prefixes → `UNKNOWN` on generic track with Neutron 5.

## Build Phases

- **Phase 1:** Skeleton + Parameter Discovery ✅
- **Phase 2:** Audio Analysis + Decision Engine ✅
- **Phase 3:** Session Building + Single Stage ✅
- **Phase 4:** Full Pipeline ✅ (327 tests passing)
- **Phase 5:** Reports + Polish (in progress)

## Key Takeaways

- Python orchestrates REAPER — never processes audio directly (except analysis with librosa)
- iZotope Assistant trigger timing is non-deterministic — use conservative waits with polling
- Parameter map YAML files ship with placeholders — must be populated per installation via enumerator script
- RX cannot be controlled via reapy — Stage 1 is deliberately semi-autonomous for v1
- LUFS mastering uses a feedback loop: render → measure → adjust threshold → repeat (max 3)
- See [[levels-and-gain-staging]] for all level targets, [[izotope-plugin-guide]] for plugin-specific details
- See [[cross-topic/creative-pipelines-and-prompt-engineering|Creative Pipelines Comparison]] for how this pipeline compares to the visual pipelines
