# iZotope Plugin Guide for Hip-Hop

**Source file:** `Hip-Hop-Mixing-iZotope-Research.md`
**Compiled:** 2026-04-07

---

## Summary

Research compilation on using iZotope's plugin suite for hip-hop mixing and mastering. Covers RX 11, Nectar 4, Neutron 5, Ozone 12, and Tonal Balance Control 3 — the same chain used by the [[overview-and-architecture|Vawn Mix Engine]].

## Signal Chain Order

1. **RX Audio Editor** — pre-mix vocal cleanup (standalone)
2. **Nectar 4** — vocal channel strip (per vocal track)
3. **Neutron 5** — instrument channel strip (per instrument track)
4. **Tonal Balance Control 3** — mix referencing (master bus)
5. **Ozone 12** — mastering chain (master bus)

## RX 11 — Vocal Cleanup

**Golden rule:** "Do the least amount of damage that will suffice."

**Workflow order:**
1. Listen in context first — note problems you can hear over the beat
2. Compress hard temporarily to expose hidden issues (diagnostic only)
3. Fix micro-problems: Mouth De-click → De-plosive → De-click → De-crackle → De-clip → Deconstruct → Spectral Repair → Interpolate → Breath Control
4. Fix broadband issues: De-hum (only if needed) → Dialogue De-reverb → Spectral De-noise → Dialogue Isolate (nuclear option)
5. Export cleaned vocal, keep original as backup

**Key decisions:**
- Breath Control: reduce volume, don't eliminate — breaths add energy in hip-hop
- Spectral De-noise: train on silent section, apply focused processing
- Dialogue Isolate: powerful but artifacts increase with heavy use

## Nectar 4 — Vocal Processing

**Vocal Assistant** analyzes input and auto-sets: level, character EQ, dynamics, sibilance detection, compressor, reverb. Select **Rap** target for hip-hop-specific processing.

**Key modules for hip-hop:**
- **Auto-Level** — rides gain for consistent level; critical for rap dynamics
- **Follow EQ** — nodes track harmonics as pitch changes
- **De-esser** — isolate to verify target frequencies; close-mic rap has aggressive sibilance
- **Compressor** — gain trace visualization; tight compression for fast delivery
- **Reverb** — keep subtle for rap; use post-EQ to prevent wash
- **Delay** — critical for vocal throws; 100% mix on duplicate track
- **Pitch/Formant Shifting** — shift formant on doubles to separate from lead
- **Unmask** — uses Relay on instrumental bus to carve frequency pocket for vocal

**Community consensus:** Excellent starting point, but experienced engineers bypass Assistant and set modules manually. Treat AI suggestions as starting points, not final settings.

## Neutron 5 — Instrument Processing

**808 mixing:**
- EQ notch at kick fundamental (~62 Hz) using Dynamic EQ with kick sidechain
- Sidechain compression: low threshold, medium ratio, short release
- Target: −3 to 0 on K-20 meter
- Bass splitting trick: duplicate bass, pure sine for sub, high-pass original at 60–90 Hz

**Parallel compression for drums:**
- Apply compression, drag Mix slider to blend compressed/uncompressed
- "New York compression" — punch + preserved transients

**Unmask:** Same frequency-pocket technique as Nectar, for competing instruments.

## Tonal Balance Control 3

**What it does:** Analysis/referencing plugin comparing your mix against target curves (30+ genre targets including Hip-Hop).

**Four meters:** Tonal Balance, Vocal Balance, Dynamics, Stereo Width.

**New in v3.0:** Built-in Hybrid EQ for corrections, standalone desktop app for capturing references from any source (Spotify, YouTube), Target Blender for hybrid genre curves.

**Hip-hop workflow:**
1. Load on master bus with Hip-Hop target
2. Use Leveled View to identify deviations
3. Check Vocal Balance for forward vocals
4. Verify mono-ish low end with wider mids/highs

**Critical caveat:** "Useful as a sanity check, not as a target." Mix deviations may be intentional. Use to catch room acoustic blind spots, not as gospel.

## Ozone 12 — Mastering

**Module chain:** EQ → Dynamics → Imager → Maximizer

**Hip-hop EQ profile:**
- Low shelf boost: 60–80 Hz (808 weight)
- Presence: 3–5 kHz (vocal clarity)
- Air: 10–12 kHz (modern brightness)

**Dynamics:** Gentle low-band compression (808 sustain), moderate mid-band (vocal consistency), light high-band (harsh hi-hats).

**Imager:** Mono below ~200 Hz, widen mids slightly, widen highs for air. "Modern Width" preset as starting point.

**Maximizer:** Ceiling −1.0 dBTP, IRC IV for transparent limiting, push threshold to −8 to −10 LUFS. If 808 causes pumping, it's a mix problem.

**Community consensus:** Master Assistant is a good starting point but tends conservative on hip-hop. Always tweak afterward.

## Common Mistakes

- Over-processing in RX — only fix what you hear in context
- Trusting AI Assistants blindly — they're starting points
- Too much reverb on rap vocals — need upfront intelligibility
- Not leaving headroom — mixing too hot
- Fixing mastering problems in the master instead of the mix
- Ignoring mono compatibility

## Key Takeaways

- RX is pre-mix cleanup only — fix problems before they get baked in
- All three Assistants (Nectar, Neutron, Ozone) are starting points, never final
- Unmask/Relay IPC creates frequency pockets automatically between compatible plugins
- TBC3 is a sanity check, not a mixing target
- For hip-hop, master louder than streaming normalization (−8 to −10 LUFS) — the tonal character of a louder master comes through even after normalization
- See [[levels-and-gain-staging]] for all level targets
