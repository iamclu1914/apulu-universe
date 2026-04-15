# Mix Engine Pro Workflow Alignment — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align the Vawn Mix Engine with the 2026 professional-grade iZotope workflow: Relay on every track, Nectar Vocal Assistant + Neutron Mix Assistant AI-driven analysis, Unmask for vocal clarity, Reverb/Delay FX buses, correct RX module ordering, and fix the broken Ozone param map.

**Architecture:** The engine currently sets VST params directly via normalized values, bypassing iZotope's AI Assistants entirely. The new architecture triggers the Assistants via REAPER playback (they need live audio to analyze), then reads back the AI-suggested params. For Relay/Unmask/FX buses, we add new track creation + routing in Stage 1. The Ozone param map gets re-enumerated live from REAPER so indices are empirically correct.

**Tech Stack:** Python, reapy (RPR API), REAPER actions, iZotope Relay/Nectar 4/Neutron 5/Ozone 12, pyloudnorm

**Key Files:**
- `src/stages/stage1_import.py` — MODIFY: add Relay insertion, FX bus creation, FX bus sends
- `src/stages/stage2_cleanup.py` — MODIFY: correct RX module ordering per iZotope's official chain
- `src/stages/stage3_vocal.py` — MODIFY: trigger Nectar Vocal Assistant via playback, then read back params
- `src/stages/stage4_instrument.py` — MODIFY: trigger Neutron Mix Assistant, enable Unmask vs vocal
- `src/stages/stage5_master.py` — MODIFY: use re-enumerated Ozone param map, target -7.5 LUFS
- `src/reaper/client.py` — MODIFY: add `trigger_fx_assistant()`, `read_fx_params()` helpers
- `src/reaper/param_enumerator.py` — NEW: live param enumeration from REAPER (replaces stale YAML)
- `config/param_maps/ozone12.yaml` — REGENERATE: re-enumerate all 876 params from live REAPER
- `config/default_config.yaml` — MODIFY: update LUFS target, add FX bus config

---

## Task 1: Re-Enumerate Ozone 12 Param Map from Live REAPER

The current `ozone12.yaml` has wrong indices for most modules (only `max_input_gain` at 120 and `max_output_level` at 121 are verified). This task creates a script that reads ALL params from a live Ozone 12 instance in REAPER and writes a fresh YAML with correct indices + formatted display values.

**Files:**
- Create: `src/reaper/param_enumerator.py`
- Regenerate: `config/param_maps/ozone12.yaml`

- [ ] Write `enumerate_plugin_params(reaper_client, track_index, fx_index)` that iterates all params via `TrackFX_GetParamName` + `TrackFX_FormatParamValueNormalized` and returns a dict of `{name: {index, formatted_default, min, max}}`
- [ ] Write `save_param_map(params, plugin_name, output_path)` that writes the YAML in the existing format
- [ ] Add a CLI command `python -m src.main enumerate-live <plugin_name>` that connects to REAPER, finds the plugin on track 1, runs the enumeration, and saves to `config/param_maps/`
- [ ] Run it against Ozone 12 in the live REAPER session: `python -m src.main enumerate-live "VST3: Ozone 12 (iZotope)"` — verify the output has correct indices for `MAX: Input Gain`, `MAX: Output Level`, `DYN: Bypass`, `DYN: Stereo/Main Global Gain`, `IMP: Bypass`, `LEF: Bypass`, etc.
- [ ] Update `decision_engine.py` to use the new param names from the regenerated map (the current code references `lef_bypass`, `imp_bypass`, etc. which may need name updates to match whatever Ozone reports)

Test: Compare the new map's `MAX: Input Gain` index against the empirically verified 120. They must match.

---

## Task 2: Insert iZotope Relay on Every Track

Relay is the inter-plugin communication layer that lets Neutron's Mix Assistant + Visual Mixer "see" the entire session. Without it, Neutron operates blind per-track.

**Files:**
- Modify: `src/stages/stage1_import.py`
- Modify: `src/reaper/client.py` (if needed for plugin name lookup)

- [ ] In `_create_stem_tracks()`, after importing audio and setting track color, insert `iZotope Relay` as the FIRST plugin on the track: `reaper_client.add_fx(track, "VST3: Relay (iZotope)")` at position 0
- [ ] In `_create_bus_tracks()`, also insert Relay as the first plugin on each sub-bus (VOCAL/DRUM/BASS/INST BUS). Do NOT put Relay on MASTER BUS.
- [ ] Add a config flag `relay.enabled` (default True) so users can skip Relay if they don't have it installed
- [ ] Handle the case where Relay VST is not found (log a warning, continue without it — don't crash the pipeline)
- [ ] Verify: FX VERIFY log should show Relay on every stem + sub-bus track (e.g., `0 Lead Vocals=1` before any other stage adds FX)

Test: After Stage 1, every stem track and sub-bus should have exactly 1 FX (Relay). MASTER BUS should have 0.

---

## Task 3: Create FX Buses (Reverb + Delay)

Hip-hop needs short reverb for space and 1/8-dotted delay for rhythmic bounce. These are separate FX return tracks with sends from vocals.

**Files:**
- Modify: `src/stages/stage1_import.py`

- [ ] Add two new tracks after the existing bus tracks: `REVERB BUS` and `DELAY BUS`
- [ ] Store their indices in `SessionLayout` (add `fx_bus_tracks: dict[str, int]` field)
- [ ] Add REAPER's built-in `ReaVerbate` on REVERB BUS with: room size small, decay 1.2s, wet 100% (sends control wet/dry balance). OR use Nectar's reverb if available.
- [ ] Add REAPER's built-in `ReaDelay` on DELAY BUS with: 1/8 dotted at project BPM, feedback 28%, wet 100%
- [ ] Create post-fader sends from Lead Vocal track to REVERB BUS at -15 dB and to DELAY BUS at -15 dB
- [ ] Create the same sends from any ADLIB-type vocal tracks
- [ ] Route REVERB BUS and DELAY BUS direct to MASTER BUS (via send, with their own main send disabled)
- [ ] Add config flags: `fx_buses.reverb.enabled`, `fx_buses.delay.enabled` (default True), `fx_buses.reverb.send_db` (default -15), `fx_buses.delay.send_db` (default -15)

Test: Dry-run should show the new FX buses in the session summary. FX VERIFY should show 1 FX each on REVERB BUS and DELAY BUS.

---

## Task 4: Fix RX 11 Module Ordering

The current Stage 2 uses RX 11 Repair Assistant (auto mode) which is a single-plugin catch-all. The pro workflow calls for ordered individual modules: De-click → De-plosive → Spectral Repair → Breath Control → De-noise → Dialogue Isolate.

**Files:**
- Modify: `src/stages/stage2_cleanup.py`
- Modify: `src/decision_engine.py` (if RX decision logic needs updating)

- [ ] Check if the individual RX 11 VST modules are available in REAPER: `VST3: RX 11 De-click`, `VST3: RX 11 De-plosive`, `VST3: RX 11 Spectral De-noise`, `VST3: RX 11 Breath Control`, `VST3: RX 11 Dialogue Isolate`. If they exist, use them; if not, fall back to Repair Assistant.
- [ ] For vocal stems, insert modules in this order (after Relay):
  1. RX 11 De-click (mouth noise removal)
  2. RX 11 De-plosive (p/b bursts)
  3. RX 11 Spectral De-noise (broadband, trained on silence — use default auto settings)
  4. RX 11 Dialogue Isolate (suno source: cut reverb -4 dB — keep existing logic)
- [ ] For instrument stems, insert only:
  1. RX 11 De-click (clicks/crackle)
  2. RX 11 Spectral De-noise (light, auto mode)
- [ ] Keep the existing Repair Assistant as the fallback when individual modules aren't installed
- [ ] Add config flag `rx_cleanup.use_individual_modules` (default True, falls back to Repair Assistant on False or if modules not found)

Test: FX VERIFY after Stage 2 should show 4 RX modules on vocal stems (or 1 if fallback) and 2 on instrument stems.

---

## Task 5: Trigger Nectar 4 Vocal Assistant via Playback

The current Stage 3 sets Nectar params directly (hardcoded EQ/comp/de-esser values). The pro workflow says: let Vocal Assistant analyze live audio, accept its suggestions, THEN refine. The Assistant needs ~8 bars of audio playback to analyze.

**Files:**
- Modify: `src/stages/stage3_vocal.py`
- Modify: `src/reaper/client.py`
- Modify: `src/reaper/transport.py`

- [ ] Add `ReaperClient.trigger_fx_assistant(track, fx_index, play_seconds=15)` that:
  1. Solos the track
  2. Sets cursor to a verse section (use detected sections if available, else 30s into the song)
  3. Starts playback for `play_seconds` (the Assistant analyzes during playback)
  4. Stops playback
  5. Unsolos the track
  6. Returns True/False based on whether playback completed without error
- [ ] In Stage 3, after inserting Nectar 4, call `trigger_fx_assistant()` to let Vocal Assistant analyze
- [ ] After playback, read back what the Assistant set via `TrackFX_GetParam` for key params (compression ratio, EQ points, de-esser threshold) and log them
- [ ] THEN apply the hip-hop refinement overrides from `decide_nectar_params()` — only override params that the decision engine has strong opinions about (e.g., reverb wet cap, compression ratio bounds), leave the rest as the Assistant set them
- [ ] Add config flag `vocal_processing.use_assistant` (default True). When False, use existing direct-param behavior.
- [ ] Guard with timeout: if playback hangs or the Assistant doesn't seem to engage (all params unchanged), fall back to direct param setting

Test: Log should show "Vocal Assistant analyzed" with the AI-suggested values before overrides. Compare against the old hardcoded values — they should be different per song.

---

## Task 6: Trigger Neutron 5 Mix Assistant + Enable Unmask

The current Stage 4 sets Neutron params directly. The pro workflow says: insert Neutron on each instrument stem, then run Mix Assistant ONCE to analyze the full session (via Relay). Also enable Unmask targeting the vocal.

**Files:**
- Modify: `src/stages/stage4_instrument.py`
- Modify: `src/reaper/client.py`

- [ ] After inserting Neutron 5 on ALL instrument stems, trigger Mix Assistant on ONE of them (typically the drums stem — the Assistant scans all Relay-connected tracks from there)
- [ ] Use the same `trigger_fx_assistant()` helper: solo=False (Mix Assistant needs full-session context), play 15 seconds of a chorus section
- [ ] After playback, read back what Mix Assistant set on each instrument stem and log the results
- [ ] Then apply per-stem refinement overrides from `decide_neutron_params()` — only override where the decision engine has specific hip-hop opinions (transient shaping on drums, bass EQ, etc.)
- [ ] Enable Unmask on each instrument stem targeting the Lead Vocal: set `unmask_bypass=0.0` and `unmask_amount=0.5` (already partially coded in `decision_engine.py:845-851`, verify the param indices are correct in the regenerated param map)
- [ ] Add config flag `instrument_processing.use_assistant` (default True)

Test: Log should show "Mix Assistant analyzed session" with per-stem AI-suggested values before overrides.

---

## Task 7: Update Master LUFS Target + Config

Hip-hop streaming sweet spot is -7.5 LUFS per the pro spec, not -9.0.

**Files:**
- Modify: `config/default_config.yaml`
- Modify: `config/i_fell_in_love.yaml`

- [ ] Change `references.loudness_target_lufs` from -9.0 to -7.5 in `default_config.yaml`
- [ ] Change `references.loudness_target_lufs` from -9.0 to -7.5 in `i_fell_in_love.yaml` (if present, else it inherits from default)
- [ ] Add `references.loudness_tolerance_lufs: 1.5` (slightly wider tolerance for hip-hop — the spec says "targeting" not "must hit exactly")

Test: Dry-run should show "target -7.5 LUFS" in the mastering section.

---

## Task 8: Fix Stem Direct-Send Double-Sum (already coded, verify)

This was already fixed in this session — `set_main_send(track, False)` called in `_route_stems_to_buses`. Verify it's working by checking that stem tracks have `B_MAINSEND=0` in the REAPER session.

**Files:**
- Verify: `src/stages/stage1_import.py:168` (the `set_main_send` call)
- Verify: `src/reaper/client.py:376` (the `set_main_send` method)

- [ ] Run the pipeline and query `GetMediaTrackInfo_Value(track.id, "B_MAINSEND")` on each stem track after Stage 1. All should return 0.0.
- [ ] Query the same on each BUS track — they should return 1.0 (buses DO send to master).

Test: Script that probes B_MAINSEND on all tracks after pipeline completes.

---

## Task 9: Wire LUFS Feedback Loop (already coded, verify)

This was already implemented — `run_lufs_feedback` is called from `run_stage5` after initial Ozone params. Verify it iterates and converges.

**Files:**
- Verify: `src/stages/stage5_master.py` (the feedback loop wiring)

- [ ] Run the full pipeline and check logs for "LUFS feedback loop" entries showing iteration count, LUFS per iteration, and whether it reached target
- [ ] If it doesn't converge within 5 iterations, check the damping/max_gr values

Test: Log should show at least 1 feedback iteration and the final LUFS should be closer to -7.5 than the initial measurement.

---

## Verification

After all tasks are complete:

1. Run `python -m src.main mix config/i_fell_in_love.yaml --dry-run` — should show Relay on tracks, FX buses, correct module ordering, and -7.5 LUFS target
2. Run the full pipeline against REAPER with I Fell In Love stems
3. Measure final rendered master: `python scripts/measure_rendered.py <output.wav> -7.5`
4. Targets: LUFS within -7.5 ±1.5, peak ≤ -0.5 dBFS, 0 clipped samples
5. Play back in REAPER — verify reverb/delay space on vocals, vocal clarity against instruments (Unmask), section-aware bus automation still working
