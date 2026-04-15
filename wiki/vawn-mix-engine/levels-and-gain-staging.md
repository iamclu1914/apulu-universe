# Hip-Hop Levels & Gain Staging Guide

**Source file:** `Hip-Hop-Levels-Guide.md`
**Compiled:** 2026-04-07

---

## Summary

Definitive gain staging reference for hip-hop mixing and mastering. Every level decision serves one purpose: keep the signal clean and controlled at every stage so plugins, buses, and the final master have room to breathe. These targets are used by the [[overview-and-architecture|Vawn Mix Engine]]'s decision engine.

## The Magic Number: −18 dBFS

- Corresponds to 0 VU on analog gear
- Sweet spot where most plugins (especially analog-modeled) are designed to operate
- Provides ~18 dB of headroom before digital clipping

## Level Targets by Stage

### Recording / Input
- **Average:** −18 dBFS
- **Peaks:** below −6 dBFS

### Individual Channels (Mixing)

| Element | Peak (dBFS) | Notes |
|---------|-------------|-------|
| Kick | −10 to −8 | Loudest transient; drives the mix |
| 808 / Bass | −12 to −10 | Just below kick; shaped by sidechain. Decision engine uses −11.0 dBFS. |
| Snare | −12 to −10 | Punchy but not overpowering kick |
| Hi-hats / Cymbals | −18 to −14 | Sit on top without dominating |
| Lead Vocal | −12 to −10 | Forward and present; focal point |
| Double / BG Vocals | −18 to −14 | Supporting, not competing |
| Synths / Pads | −18 to −14 | Fill space without masking |
| Percs / FX | −20 to −16 | Texture and movement |

**Critical:** Set levels using gain/trim or instrument output knob, NOT the channel fader. Faders are for mix balance later.

### Buses / Groups
- **Average:** −18 dBFS RMS
- **Peaks:** −10 to −8 dBFS per bus
- Standard buses: Drum, 808/Bass, Vocal, Instrument, FX

### Master Bus Input (Pre-Mastering)
- **Peaks:** −6 to −3 dBFS
- **Average:** −18 to −14 dBFS

### Mastering Output (Ozone 12)
- **True peak ceiling:** −1.0 dBTP (streaming standard)
- **Competitive hip-hop:** −8 to −10 LUFS integrated
- **Conservative/dynamic:** −10 to −12 LUFS
- **Club/DJ:** −6 to −8 LUFS
- **Gain reduction sweet spot:** 1–3 dB clean, 3–5 dB aggressive, 5+ dB means mix problems

## Hip-Hop Element Priority Stack

1. Kick drum — loudest transient
2. 808 / Bass — just below kick
3. Snare / Clap — punchy, forward
4. Lead Vocal — centerpiece
5. Synths / Melodic — supporting
6. Percs / Hi-hats — texture
7. Background vocals / Ad-libs — depth and width
8. FX / Ambient — ear candy

## Sidechain Ducking (Critical for Hip-Hop)

808/bass bus sidechained to kick: low threshold, medium ratio (4:1), fast attack (0.1–1ms), short release (50–150ms).

## K-System Metering

- K-20: 0 on meter = −20 dBFS
- Green (below 0): safe | Yellow (0 to +4): healthy average | Red (above +4): getting loud
- 808 should read −3 to 0 on K-20
- Vocals should average 0 to +2 on K-20

## Common Mistakes

- Recording too hot (−3 dBFS instead of −18 dBFS)
- Confusing faders with gain staging (faders adjust after inserts)
- 808 too loud → forces limiter to crush everything
- A/B testing with mismatched levels (louder always sounds "better")
- Stacking plugins that each add gain without compensating
- Mastering to a LUFS number instead of ears
- Not checking in mono (phone speakers, earbuds, car systems)

## Key Takeaways

- −18 dBFS is the universal mixing target — it's where plugins work best
- Set levels at the source (gain/trim), not the fader
- If you need 5+ dB of limiting to hit LUFS target, fix the mix, not the master
- Always check mono compatibility — hip-hop lives on phone speakers
- These exact targets are encoded in the [[overview-and-architecture|Mix Engine]]'s `decision_engine.py`
- See [[izotope-plugin-guide]] for plugin-specific level expectations
