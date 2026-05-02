---
type: research
topic: vawn-mix-engine
date: 2026-04-21
tags:
  - suno
  - mixing
  - mastering
  - research
  - izotope
---

# Suno AI Mixing & Mastering — Research Consensus

Compiled from 7 sources (5 iZotope articles, 3 YouTube tutorials, 1 Reddit guide) while troubleshooting the *Come See About Me* mix. Use this as the canonical reference when designing Suno-source pipelines going forward.

## Sources reviewed

| # | Source | Type | Core value |
|---|---|---|---|
| 1 | [iZotope — Crafting a Basic Vocal Chain](https://www.izotope.com/en/learn/crafting-a-basic-vocal-chain) | Article | Canonical chain order |
| 2 | [iZotope — Mixing Vocals: 8 Pro Steps](https://www.izotope.com/en/learn/mixing-vocals-what-makes-a-professional-vocal-sound) | Article | Comprehensive vocal ref |
| 3 | [iZotope — 8 Tips for Mixing Rap & Hip-Hop](https://www.izotope.com/en/learn/8-tips-for-mixing-rap-and-hip-hop) | Article | Genre-specific moves |
| 4 | [iZotope — Mastering with Ozone Elements](https://www.izotope.com/en/learn/mastering-with-essential-tools-in-ozone-elements) | Article | Ozone 12 workflow |
| 5 | Lu Diaz — Kick/808 Relationship (YT Xmm-6mb7KwU) | Video | Hip-hop low-end |
| 6 | BusyWorksBeats — Make Suno Realistic (YT cDCSWPW1Vic) | Video | Suno artifact removal |
| 7 | Chill Panicified — Mix Suno Stems (YT Nn4PVSebOSQ) | Video | Suno masking philosophy |
| 8 | [Reddit r/SunoAI — Stems & Mastering Guide (nokia7110)](https://www.reddit.com/r/SunoAI/comments/1nav6ep/suno_ai_stems_and_mastering_guide/) | Reddit | Practical DAW-agnostic guide |

## Canonical vocal chain order

iZotope consensus (confirmed by two separate articles):

```
1. Pitch correction          (skip for rap)
2. EQ
3. Compressor                (3-7 dB GR)
4. De-esser                  (above 3 kHz)
5. Delay
6. Reverb
7. Saturation / creative
```

**EQ before compression** is house position. De-esser can optionally go pre-comp if the compressor is introducing sibilance.

## Numeric targets (cross-source)

| Parameter | Value | Sources |
|---|---|---|
| Vocal GR | 3–7 dB | iZotope (x2) |
| HPF | 100–120 Hz | iZotope, Chill Panicified |
| Mud cut | 200–400 Hz | iZotope |
| Presence boost | 2–5 kHz | iZotope |
| Air / mask AI cutoff | 8–10 kHz | BusyWorks |
| De-ess range | Above 3 kHz | iZotope |
| Suno-specific DS | 3k split-band, 2 dB cut | BusyWorks |
| Saturation | Tape, ~50% | iZotope |
| Attack | 5–15 ms | iZotope |
| Release | 50–150 ms | iZotope |
| Double-track timing tolerance | <20 ms | iZotope |
| Bass-split crossover | 60–90 Hz | iZotope, Reddit |

## Suno artifact signature (unanimous across sources)

- High-frequency buildup at **1 kHz, 3 kHz, 5 kHz** (piercing resonances)
- **"Suno sheen"** — baked reverb/artificial wetness, especially on hooks
- **15 kHz hard cutoff** — AI top-end rolloff signature
- **Mono-folded highs** — stems lack stereo width above ~3 kHz
- **Inconsistent section-to-section levels** (AI splices phrases without matching)
- **Stem bleed** — separated stems retain fragments of other stems
- **Drum stems washy/flat** (consensus from multiple sources)

## Two opposing philosophies for AI artifacts

### Philosophy A — Remove
BusyWorksBeats, iZotope
- DSer at 3 kHz split-band, ~2 dB cut
- Boost 8 kHz to mask 15 kHz cutoff
- Soothe2 or TDR Nova on master for harshness
- Gate on synths at lowest-possible threshold (kills many artifacts cheaply)

### Philosophy B — Mask
Chill Panicified, Lu Diaz implicit
- Layer added reverb/shimmer so baked reverb feels intentional
- Soothe (dynamic resonance) instead of static de-ess
- Parallel pingpong delay + distortion for width/character
- "Slam into limiter" as final vocal stage for attitude

Both work. **B is more robust for hooks with baked ambience**; A is cleaner but risks nasal/hollow artifacts when pushed.

## Hip-Hop specific moves

### Kick & 808 as one unit (Lu Diaz)
- Never process separately then smash together
- Sidechain kick → 808 via dynamic EQ/comp to carve space
- EQ stacking on kick (3 EQs): F6 dynamic → SSL E-channel → API for character
- Bump 7k/6k on kick for attack (you want to *hear* it more, not *louder*)
- Mono-center kicks/snares/bass

### Bass architecture (Reddit + iZotope)
Double the bass:

```
Original bass stem
  → Copy A (low): mono, high-cut up to where bass presence starts to die
  → Copy B (mid/hi): low-cut (don't compete with A), high-cut pulled down slowly
  → If mid-hi cut kills character: add saturation to regenerate harmonics
  → Gentle sidechain from drum bus (don't pump)
```

### Synth/instrument artifact removal (Reddit)

```
1. Low-end cut
2. Extreme high-end cut
3. Gate threshold as low as possible before it sounds gated
   (kills significant AI artifact between notes)
4. Narrow-band sweep → find harsh frequencies + artifact zones
5. Surgical EQ cuts
```

The gate at step 3 is a cheap, high-impact move we haven't been doing.

### Genre-specific panning (Reddit AI analysis)
- **Low-cut every instrument EXCEPT drums, bass, percussion** (prevents mud)
- **Bass, vocal, drums dead center**
- **Other instruments slightly off-center** for width
- **Zero reverb** — clean, dry, upfront is the hip-hop aesthetic (explicit choice, not omission)

## Mastering (Ozone 12 canonical)

Modern Ozone 12 workflow (more sophisticated than our pipeline currently uses):

- **Master Assistant: Auto-Master OR Custom** mode
- **Custom**: pick genre target before analysis (Hip-Hop, Trap, Classic Hip-Hop, RnB/Soul, etc.)
- **Analyze the loudest section** — the chorus (iZotope explicit recommendation)
- **Intensity slider** — subtle → transformative
- **Tonal Balance curve** — visual match against target
- **Width Match** — mid/side ratio matching (critical for Suno's mono highs)
- **Stabilizer** — dynamic resonance control across playback environments
- **Vocal Balance** — auto-detects if vocal needs louder/softer
- **True-peak protection** for streaming
- **Gain Match** for honest A/B

## Tools & free alternatives

| Paid tool | Free alternative | Role |
|---|---|---|
| FabFilter Pro-Q | **TDR Nova** | EQ |
| FabFilter Pro-MB | Convergence Free | Multiband comp |
| Soothe 2 | **TDR Nova (dynamic mode)** | Resonance suppression |
| FabFilter Pro-DS | Kilohearts Compressor | De-esser |
| Ozone 12 | No free equivalent (~$80 used keys) | Mastering |

## Working methodology (universal)

- **"Carving a sculpture, not hitting it with a sledgehammer"** — never push controls to extremes just to hear a difference
- **Ear fatigue**: drop master fader 4-6 dB while working
- **Trust your ears**, A/B constantly
- **Learn one thing at a time** — don't stack techniques before you understand each
- **Level automation is non-negotiable** (all sources)

## How this maps to [[overview-and-architecture|mix-engine]]

### What our current pipeline gets right

- ✓ Leslie-aligned vocal chain matches iZotope canon
- ✓ Dry vocal mode default (minimal reverb — matches "less is more")
- ✓ Envelope-based automation (v9 decay-to-unity + tail protection — matches "automation is non-negotiable")
- ✓ Guru M/S carve-out on instrumental buses (creates vocal space)
- ✓ Bus balance as gain staging layer (see [[levels-and-gain-staging]])
- ✓ `ai_source: suno` triggering RX Dialogue Isolate
- ✓ Skipping ALM + Vintage Comp for Suno sources (lesson learned — "AI is already semi-processed, go lighter")

### Gap list (new pipeline opportunities)

| Gap | Priority | Notes |
|---|---|---|
| **Soothe-equivalent on master** (TDR Nova dynamic) | HIGH | #1 tool for AI harshness — missing entirely |
| **Gate on synth/keys stems** | HIGH | Cheapest artifact killer per Reddit |
| **Split-band DSer at 3 kHz on vocal** | HIGH | For the nasal resonance complaint |
| **Double-bass architecture** (sub + mid/high) | MEDIUM | Current pipeline treats bass as single path |
| **Saturation stage on vocal chain** | MEDIUM | Tape ~40% for warmth |
| **Ozone Imager to widen Suno mono highs** | MEDIUM | Suno stems mono above ~3 kHz |
| **Genre-targeted mastering (Custom mode)** | MEDIUM | Currently generic; Ozone 12 has specific Hip-Hop / Trap targets |
| **Zero-reverb default for hip-hop** | MEDIUM | Reddit AI analysis says clean/dry is the genre target |
| **Drum stem replacement or aggressive HPF + 8kHz LPF on cymbals** | HIGH | "Washy, flat" is consensus on Suno drums |
| **Parallel compression on DRUM BUS** | MEDIUM | iZotope recommendation for punch |

## Philosophical decisions pending

Before building a new pipeline, pick:

1. **Artifact philosophy**: remove (A) or mask (B)?
2. **Saturation yes/no** on vocal chain?
3. **Double-bass split** architecture?
4. **Mastering**: generic target or **Custom Hip-Hop** with Stabilizer + Width Match?
5. **Parallel comp** on DRUM BUS / VOCAL BUS?
6. **Ozone Imager** for widening Suno mono highs?
7. **Split-band DSer at 3 kHz** on vocal stem?
8. **Low-threshold gate** on KEYS/SYN/INST stems?
9. **Zero-reverb default** for hip-hop aesthetic?

## Related

- [[mix-rules]] — our current codified rules
- [[overview-and-architecture]] — pipeline as built
- [[levels-and-gain-staging]] — gain staging conventions
- [[izotope-plugin-guide]] — plugin inventory
