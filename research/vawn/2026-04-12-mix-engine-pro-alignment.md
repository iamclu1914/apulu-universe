---
tags: [mix-engine, production, reaper, izotope, session-notes]
date: 2026-04-12
artist: Apulu
status: complete
---

# Mix Engine Pro Alignment -- 2026-04-12

## Summary

Completed 9-task pro workflow alignment for the Vawn Mix Engine. Shifts the architecture from hardcoded VST params to iZotope AI Assistant-driven analysis with hip-hop overrides.

## Changes Shipped

### New Capabilities
- **iZotope Relay** on every stem + sub-bus for inter-plugin communication
- **FX Buses** -- REVERB BUS (ReaVerbate, 1.2s decay) + DELAY BUS (ReaDelay, 1/8 dotted) with vocal sends at -15 dB
- **Nectar 4 Vocal Assistant** -- plays 15s of audio, reads back AI-suggested params, then applies hip-hop overrides
- **Neutron 5 Mix Assistant** -- triggers once for full session scan via Relay, enables Unmask vs Lead Vocal
- **RX 11 individual modules** -- De-click -> De-plosive -> Spectral De-noise -> Dialogue Isolate (ordered per iZotope spec, falls back to Repair Assistant)
- **Param enumerator** -- `enumerate-live` CLI command reads all params from a live REAPER plugin instance

### Config Changes
- LUFS target: -9.0 -> **-7.5** (hip-hop streaming sweet spot)
- LUFS tolerance: 1.0 -> **1.5**
- New config flags: `relay.enabled`, `fx_buses.reverb/delay.enabled`, `vocal_processing.use_assistant`, `instrument_processing.use_assistant`, `rx_cleanup.use_individual_modules`, `stems.exclude`
- New `SessionLayout.fx_bus_tracks` field

## First Mix: "On My Way" (7 stems)

| Stem | Type | Gain | Chain |
|------|------|------|-------|
| 0 Lead Vocals | LEAD | -6.7 dB | Relay -> RX -> Nectar 4 |
| 1 Backing Vocals | DBL | +8.4 dB | Relay -> RX -> Nectar 4 |
| 2 Drums | PERC | -8.5 dB | Relay -> RX -> Neutron 5 |
| 3 Bass | BASS | -4.8 dB | Relay -> RX -> Neutron 5 |
| 4 Keyboard | UNKNOWN | +1.8 dB | Relay -> RX -> Neutron 5 |
| 5 Percussion | PERC | -1.8 dB | Relay -> RX -> Neutron 5 |
| 6 Synth | SYN | -1.1 dB | Relay -> RX -> Neutron 5 |

**Results:**
- All 5 stages passed (1252s total)
- 44 FX across 14 tracks
- Mix + Vocal Assistants both engaged successfully
- Rendered: `On_My_Way_24bit.wav` (53.7 MB)

### Issues Found
1. **LUFS didn't converge** -- pre-master at -29 LUFS, feedback loop maxed at 10 dB push, landed at -15.7 (target -7.5). Gap too large for maximizer alone.
2. **Bass classified as BASS, not 808** -- Suno's bass is 808-style sub-bass. The BASS EQ chain cuts 350Hz mud and over-compresses (4:1), killing the thump. Fixed live by switching to 808 settings (sub boost 60Hz, 2:1 comp, transient attack).
3. **Keyboard/Instrumental classified as UNKNOWN** -- stem classifier needs patterns for these names.

### Live Adjustments Made
- Bass stem +3 dB, BASS BUS +1.5 dB
- Bass Unmask reduced 0.50 -> 0.15
- Bass Neutron reconfigured for 808 character (sub boost, lighter comp, transient emphasis)

## Next Steps
- [ ] Fix stem classifier: `keyboard` -> KEYS, `instrumental` -> exclude by default for Suno
- [ ] Treat BASS as 808 when `ai_source: "suno"` (Suno doesn't produce upright/electric bass)
- [ ] Raise `max_gain_reduction_db` or add pre-master gain normalization to close large LUFS gaps
- [ ] Run `enumerate-live` against Ozone 12 in REAPER to regenerate verified param map

## Files Modified
```
src/reaper/param_enumerator.py     -- NEW
src/reaper/client.py               -- trigger_fx_assistant(), read_fx_params()
src/stages/stage1_import.py        -- Relay, FX buses, fx_bus_tracks
src/stages/stage2_cleanup.py       -- Individual RX modules with fallback
src/stages/stage3_vocal.py         -- Vocal Assistant integration
src/stages/stage4_instrument.py    -- Mix Assistant + Unmask
src/main.py                        -- enumerate-live CLI command
src/audio_analyzer.py              -- stems.exclude support
src/stages/pipeline.py             -- stems.exclude passthrough
config/default_config.yaml         -- LUFS -7.5, tolerance 1.5
config/i_fell_in_love.yaml         -- LUFS -7.5, tolerance 1.5
config/on_my_way.yaml              -- NEW session config
```
