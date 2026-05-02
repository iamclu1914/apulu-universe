---
type: note
topic: vawn-mix-engine
---

# Mix Rules — Codified from 2026-04-16 session

Hard-won mixing rules learned the night Vawn's "On My Way" went through the engine end-to-end against REAPER. These rules apply to BOTH the autonomous mix engine AND any manual REAPER editing on Vawn (or future artist) sessions. The engine has been partially patched to enforce some of these; others are workflow rules for engineers and future Claude sessions.

## 1. Master fader is for the mastering stage, not for balance

**Wrong move:** "vocals too quiet → push master fader."

**Why:** Master fader uniformly lifts everything. It does not change the relative balance between vocal and drums. It just brings the whole mix closer to clipping with no peak control.

**Correct move:** If something is too quiet/loud relative to other elements, adjust **that element**, not master. The master is for outputting the final balanced mix. When mastering through Master Channel AI, master should sit at 0 dB and let MCA handle loudness.

## 2. Push the under-prominent element, don't crush the dominant one

**Wrong move:** Drums dominate vocals → cut drum bus by -10 dB.

**Why:** Crushing drums makes the song sound under-powered. Cuts of more than -4 dB on a bus are usually a sign you're treating the wrong knob.

**Correct move:** Push the vocal first (often by significant amounts — +10 to +15 dB above its native RMS for Suno stems is normal). THEN modestly cut the dominant element by -3 to -6 dB max. Never -10. Hip-hop balance: vocal sits 2-4 dB above drums on the bus meter, not 10+ dB above.

## 3. Vocal stems should bypass the peak-headroom clamp

**Engine fix already applied:** `compute_gain_offset` in `src/decision_engine.py` now skips the peak clamp for vocal stems (LEAD/DBL/HOOK/ADLIB).

**Why:** Suno vocals come out near 0 dBFS peak. The previous -3 dBFS peak ceiling clamped vocal gain offset to ~-1 dB instead of the +9 dB target. Nectar 4's compressor + limiter handle vocal peaks downstream; the raw-peak clamp is reacting to peaks that won't exist post-Nectar.

**Test guard:** `tests/test_decision_engine.py::TestGainStaging::test_vocal_has_no_peak_clamp`.

## 4. Clip-gain envelope must fold base fader into its points

**Engine fix already applied:** `_write_pre_nectar_clip_gain` in `src/stages/stage3_vocal.py` now reads the track's current fader value and incorporates it into every envelope point (then zeros the fader so envelope is sole source of truth).

**Why:** REAPER's Volume envelope in Read automation mode REPLACES the fader during playback. Stage 1 sets the fader to (e.g.) +9.3 dB; Stage 3 creates an envelope; Read mode then ignores the +9.3 fader, costing 9 dB of vocal level. The fix folds Stage 1's gain into the envelope baseline.

**Audible symptom if regressed:** "Vocals are extremely low" despite gain offsets being correctly computed.

## 5. Sculptor doesn't belong on bass stems

**Why:** Sculptor's Action Region defaults to ~95-391 Hz with "Reduce Boxiness" or "Add Fullness" modes. On a BASS stem, that region IS the fundamental — Sculptor pulls down or modulates exactly the energy you want bass to have.

**Engine fix needed (deferred):** Skip Sculptor on `BASS_TYPES = {"808", "BASS"}` stems automatically. For now: every BASS stem mix run requires a manual `SC Amount=0, SC Global Mix=0` post-step.

**Audible symptom:** "The bass took the tonal sound away" — fundamental scooped, bass feels hollow.

## 6. Multiband compressor band 1 ratio must be ≤2:1 on bass stems

**Why:** Neutron 5 Mix Assistant tends to set Compressor 1 Band 1 (the low band) at 4-7:1 ratio when it sees a bass stem. That's heavy compression on the very transients (kick body, 808 sustain) that make bass punchy. Result: a flat, lifeless bass.

**Engine fix needed (deferred):** Force C1 B1 ratio ≤2:1 on bass stems. For now: every BASS stem post-Mix-Assistant requires a manual ratio reset.

**Audible symptom:** Same as Sculptor — bass feels weak/scooped, even when EQ shows flat.

## 7. Sculptor on multiple buses simultaneously is overkill

**Why:** When Mix Assistant is run separately on multiple buses (DRUM, BASS, INST, VOCAL all get their own Neutron via the engine's stage1 bus FX template), each Sculptor instance targets the same 95-391 Hz region. Multiple buses processing the same frequency range stack up and can cause buildup or phase issues at the master bus sum.

**Rule of thumb:** Sculptor in at most ONE place. If you want it for vocal warmth, use it on VOCAL BUS only. For instrument buses, leave it disabled (`SC Amount=0`).

## 8. `TrackFX_SetParamNormalized` silently fails when FX UI is closed

**Why (REAPER bug, not ours):** REAPER's `TrackFX_SetParamNormalized` returns success but doesn't actually apply the value if the FX UI window isn't open at the time of the call. Affects Neutron, Nectar, Ozone — all the iZotope plugins.

**Engine fix needed (deferred):** Wrap every FX param-set in the engine with:
```python
RPR.TrackFX_SetOpen(track.id, fx_idx, True)
time.sleep(0.4)
RPR.TrackFX_SetParamNormalized(track.id, fx_idx, param_idx, value)
time.sleep(0.2)
RPR.TrackFX_SetOpen(track.id, fx_idx, False)
```

**Audible symptom:** "FX Assistant may not have engaged (0 params changed)" warning during pipeline run. The Assistant DID try, but the post-Assistant param sets never landed.

**Workaround until engine fix:** When manually patching params via reapy, always open the FX UI first.

## 9. Master Channel AI replaces Stage 5

**Why:** When using Master Channel AI for the final master, the engine's Ozone 12 + TBC3 maximizer chain in Stage 5 is redundant. Running Stage 5 wastes time on iterative LUFS feedback loops that MCA will undo.

**Workflow:** Use `python -m src.main mix config/<song>.yaml --mix-only` for MCA-bound tracks. The pre-master WAV that gets rendered is what uploads to MCA.

**Pre-master target:** -14 LUFS with peaks below -1 dBFS gives MCA the headroom it needs to do its mastering job. Don't try to hit -7 to -9 LUFS on the pre-master — that's MCA's territory.

## 10. Drum bus envelope cuts override fader changes (and vice versa)

**Why:** When `I_AUTOMODE` is set to Read (1), the Volume envelope on a track replaces the static fader during playback. UI shows the fader value, but envelope dictates audible level. Setting the fader does nothing perceptible without also patching every envelope point.

**Rule:** Before adjusting a bus fader on a track that has bus automation rides (envelope from Stage 4.5), first check `I_AUTOMODE`. If it's Read, multiply every envelope point by the desired gain factor instead of (or in addition to) the fader change.

**Tool:** Boost-envelope helper pattern:
```python
def boost_envelope(track, db_offset):
    env = RPR.GetTrackEnvelope(track.id, 0)
    sm = int(RPR.GetEnvelopeScalingMode(env))
    factor = 10 ** (db_offset / 20)
    for i in range(RPR.CountEnvelopePoints(env)):
        res = RPR.GetEnvelopePoint(env, i, 0, 0, 0, 0, False)
        v_lin = RPR.ScaleFromEnvelopeMode(sm, res[4])
        new = RPR.ScaleToEnvelopeMode(sm, v_lin * factor)
        RPR.SetEnvelopePoint(env, i, res[3], new, res[5], res[6], res[7], True)
```

## 11. Engine over-applies Neutron — sometimes raw stems sound better

**Why:** Mix Assistant is vocal-centric. It sees an instrument stem and applies cuts/compression based on what it would do for "balanced" vocal-forward output. For hip-hop where the bass IS the bed, this often makes things worse than the raw Suno output.

**Workflow note:** If Mix Assistant has clearly hurt instrument tone, **deleting Neutron entirely from instrument stems and buses** (keeping just RX cleanup) often produces a better-sounding mix than fighting Neutron's settings. Vocals (Nectar) should usually stay.

**Engine improvement deferred:** Add a `vocal_processing.use_neutron_on_buses` config flag (default false for hip-hop) that skips the bus-level Neutron template entirely for instrument buses.

## 12. Pre-render the reference into the session for A/B

**Workflow:** When mastering against a reference (e.g., Kendrick "Not Like Us" / `ref7.wav`), drag the reference WAV onto a new muted track in REAPER. Unmute to A/B during playback; remute before render. The engine has logic to import the reference automatically (Stage 5) but with `--mix-only` runs you do it manually.

**Why:** Match EQ in Ozone needs the reference loaded as a track to capture its tonal curve. For pre-master + MCA workflow, the reference is mainly for ear-level comparison during mixing.

## Quick reference: Vawn target levels

| Stem | RMS target (dBFS) | Notes |
|---|---|---|
| LEAD vocal | -14 | Anchor — sits on top |
| DBL (doubles) | -18 | -4 dB from lead |
| ADLIB | -19 | -5 dB from lead |
| KICK | -15 | Hits hard |
| SNR | -16 | Crack through |
| PERC | -16 | Same band as snare |
| HAT | -19 | Groove, not dominant |
| 808 | -15 | Massive, felt |
| BASS | -16 | Foundation |
| KEYS / SYN / GTR / STR | -19 | Present support |
| PAD | -20 | Atmosphere |
| FX | -21 | Feel it, don't spike |

These targets are the engine's `LEVEL_TARGETS` in `src/decision_engine.py`. They're correct for hip-hop. The peak-clamp problem (rule 3) was preventing them from being hit.

## Quick reference: Final mix balance heuristic

When checking a Vawn mix on bus meters during a vocal-heavy section:
- VOCAL BUS peak ≈ DRUM BUS peak (within 2-3 dB)
- BASS BUS peak 3-5 dB below vocal/drum
- INST BUS peak 6-10 dB below vocal/drum
- MASTER BUS peak around -6 to -8 dBFS for pre-master WAV (gives MCA headroom)
- MASTER BUS LUFS-I around -14 to -12 for pre-master (MCA target output is -9 LUFS)

If VOCAL BUS reads >5 dB below DRUM BUS, vocal needs more push. Push the vocal, not master.
