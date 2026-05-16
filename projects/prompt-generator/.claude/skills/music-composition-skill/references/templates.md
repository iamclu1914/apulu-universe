# Templates & Examples Reference

## ⚠️ MANDATORY FORMAT: JSON STRUCTURE ONLY

**ALL prompts MUST use the JSON structure with keys like `"genre":`, `"mood":`, `"tempo":`, etc.**

**NEVER output prompts as prose/paragraphs. This is incorrect and will be rejected.**

❌ **WRONG:** `Aggressive trap hip-hop. 140 BPM. Roland TR-808 bass, hard snares...`

✅ **CORRECT:** `{ "genre": "Aggressive trap hip-hop", "tempo": "140 BPM locked", "instruments": "Roland TR-808 bass, hard snares..." }`

---

## Two-Prompt System

Each track requires TWO separate prompts:
1. **Production Prompt** - Instrumental only (no vocals)
2. **Final Recording Prompt** - Full track with vocals + lyrics

---

## Production Prompt Template (Instrumental)

**Purpose:** Generate the instrumental/beat first
**Character Limit:** Under 980 characters
**Format:** Meta tags + JSON object (NOT prose)

```
[Is_MAX_MODE: MAX] (MAX)
[QUALITY: MAX] (MAX)
[REALISM: MAX] (MAX)
[REAL_INSTRUMENTS: MAX] (MAX)
{
  "genre": "[Genre description] instrumental",
  "mood": "[1-2 word emotional anchor]",
  "tempo": "[XX] BPM locked",
  "instruments": "[Instrument 1 (sonic characteristics)], [Instrument 2 (sonic characteristics)], [Instrument 3 (sonic characteristics)]",
  "structure": "[Intro type], [verse energy], [hook peak], [bridge contrast], [outro resolution]",
  "mix": "[Key element] dominant, [element] punctuating, [element] driving, dynamic progression, [overall vibe], no AI artifacts, arranged NOT looped"
}
```

### Production Prompt Example: "Come Up"

**Character Count:** ~750 ✅

```
[Is_MAX_MODE: MAX] (MAX)
[QUALITY: MAX] (MAX)
[REALISM: MAX] (MAX)
[REAL_INSTRUMENTS: MAX] (MAX)
{
  "genre": "Aggressive trap-influenced hip-hop banger instrumental",
  "mood": "hungry relentless",
  "tempo": "78 BPM locked",
  "instruments": "Roland TR-808 sub-bass (prominent sliding deep rumble), layered horn samples (urgent brass stabs), crisp snare claps (hard-hitting layered), rapid hi-hat rolls (triplet patterns metallic), distorted synth stab (dark ominous texture)",
  "structure": "Ambient tension intro, aggressive verse groove, horns-heavy hook peak, stripped 808 bridge, maximum energy outro",
  "mix": "808 dominant in low end, horns punctuating urgency, snares cracking through, hi-hats driving momentum, dynamic progression, raw streetwise intensity, no AI artifacts, arranged NOT looped"
}
```

---

## Final Recording Prompt Template (With Vocals)

**Purpose:** Full track with Vawn vocals over the beat
**Character Limit:** Under 980 characters
**Format:** Meta tags + JSON object (NOT prose)

```
[Is_MAX_MODE: MAX] (MAX)
[QUALITY: MAX] (MAX)
[REALISM: MAX] (MAX)
[REAL_INSTRUMENTS: MAX] (MAX)
[REAL_VOCALS: MAX] (MAX)
[CLEAR_VOCALS: MAX] (MAX)
{
  "genre": "[Genre description]",
  "mood": "[1-2 word emotional anchor]",
  "tempo": "[XX] BPM locked",
  "instruments": "[Same instruments from production prompt]",
  "vocal_style": "Deep baritone male rap, [delivery style] with emotional dynamics, clear pronunciation, authentic Southern drawl, [intensity], commanding ad-libs ([specific ad-libs])",
  "recording": "Close-mic dry booth sound, no reverb, vocals raw and upfront, [additional recording quality]",
  "structure": "[Intro type], [verse energy], [hook peak], [bridge contrast], [outro resolution]",
  "mix": "[Key element] dominant, vocals cutting through raw, [drums], dynamic progression, [overall vibe], no AI artifacts, arranged NOT looped"
}
```

### Final Recording Prompt Example: "Come Up"

**Character Count:** ~995 ✅

```
[Is_MAX_MODE: MAX] (MAX)
[QUALITY: MAX] (MAX)
[REALISM: MAX] (MAX)
[REAL_INSTRUMENTS: MAX] (MAX)
[REAL_VOCALS: MAX] (MAX)
[CLEAR_VOCALS: MAX] (MAX)
{
  "genre": "Aggressive trap-influenced hip-hop banger",
  "mood": "hungry relentless",
  "tempo": "78 BPM locked",
  "instruments": "Roland TR-808 sub-bass (sliding rumble), horn samples (urgent stabs), snare claps (hard-hitting), hi-hat rolls (triplet metallic), synth stab (dark ominous)",
  "vocal_style": "Deep baritone male rap, hungry aggressive delivery with emotional dynamics, clear pronunciation, Southern drawl, raw intensity, commanding ad-libs (grrah, yuh, come on)",
  "recording": "Close-mic dry booth, no reverb, vocals raw upfront, breathing adds urgency",
  "structure": "Tension intro, aggressive verse groove, horns-heavy hook peak, stripped 808 bridge, maximum outro",
  "mix": "808 dominant, horns punctuating, vocals cutting through, snares cracking, dynamic progression, streetwise intensity, no AI artifacts, arranged NOT looped"
}
```

---

## Lyrics Template

**Character Limit:** Under 5000 characters

**REQUIRED:** Start with `///*****///` header and include an [Intro] section.

**REPLAY VALUE REQUIRED:** Every track must reward repeated listens:
- ✅ Double entendres / layered meanings (2+ per song)
- ✅ Quotable bars that stand alone (2+ per verse)
- ✅ Callbacks / internal references between sections
- ✅ Hook variation on final repeat (not copy-paste)
- ✅ "Full circle" moment in outro

**VOCABULARY FRESHNESS REQUIRED:** No repeated words across tracks:
- ✅ Key words unique to this track (check against previous tracks)
- ✅ Rhyme words not recycled from other songs
- ✅ Metaphors/imagery used ONCE per project
- ✅ No crutch words in every song (grind, hustle, haters, etc.)

**Standard Bar Lengths:**
- Verses: 16 bars (or 12 for shorter tracks)
- Hooks/Choruses: **8 bars** (standard) or 4 bars repeated
- Bridge: 4 bars
- Intro/Outro: 2-4 bars

```
///*****///

[Intro]
[BPM: XX] [Key: X Minor/Major] [Mood: descriptor, descriptor]
[Production: intro elements active]
[Spoken/ad-lib/SFX opener]

[Verse 1: 16 bars]
[Production: specific elements active]

[Ad-lib opener]
[Lyrics with (ad-libs) in parentheses at end of lines]

[Hook: 8 bars]
[Production: what changes/intensifies]

[Hook lyrics with (ad-libs) - 8 lines or 4 lines repeated]

[Verse 2: 16 bars]
[Production: how it evolved from V1]

[Lyrics with (ad-libs)]

[Bridge: 4 bars]
[Production: stripped element, everything else drops]

[Bridge lyrics - contrast in energy]

[Final Hook: 8 bars]
[Production: everything returns maximum]

[Hook variation with (intensified ad-libs)]

[Outro: 2-4 bars]
[Production: how it ends]

[Outro content]

[End - Transitions to Track X: "Title"]
```

**Hook Length Notes:**
- **8 bars** = industry standard, provides catchiness without overpowering verses
- **4 bars repeated** = effectively 8 bars, common in trap (same 4 lines sung twice)
- **4 bars (short)** = works for aggressive/minimal tracks, faster energy
- **16 bars** = extended hooks for buildup/anthems (less common)

### Complete Lyrics Example: "Come Up"

```
///*****///

[Intro]
[BPM: 78] [Key: E Minor] [Mood: Hungry, Relentless]
[Production: 808 slides in low, hi-hats tease, horns build tension]
(phone static)
Yeah... it's Vawn
(horn stab)
Let's get it

[Verse 1: 16 bars]
[Production: Full beat drops - 808 slides, hi-hats roll, horns stab]

Grrah, yuh
Empty fridge but the vision was full (full)
Roaches in the kitchen I was plotting on a jewel
Seventeen with a hunger they could never understand
Notebook full of dreams and a pen in my hand
Closet was the studio blankets on the wall (on the wall)
Neighbors banging telling me to turn it down the hall
Couldn't stop the mission had to answer to the call
Every no I got just made me stand a little more tall
Come on
Watched my brothers take the fast route to the paper (paper)
Said I'd catch up but I knew I had to take the stairs
Something in my gut said the shortcut was a caper
Chose the long road even when nobody cared (grrah)
Ramen noodle winters stomach growling all night
But the fire in my chest kept the future looking bright
First check seventeen dollars felt like a million
Cashed it at the corner store I knew I'd make a billion

[Hook: 8 bars]
[Production: Horns hit hard, 808 slides, snares crack]

This the come up they could never fabricate (never)
Started in the basement now I'm taking the estate (yuh)
Hunger in my belly that'll never dissipate (grrah)
Come up on my mind every single day I wake (let's go)
This the come up they could never fabricate (never)
From the bottom to the top I'm staking my estate (yuh)
Every single setback made my drive accelerate (grrah)
Come up never stops this hunger won't abate (let's go)

[Verse 2: 16 bars]
[Production: Hi-hats double up, 808 slides harder, intensity rises]

Yuh, back at it
Eviction notice on the door we moving boxes (boxes)
Mama crying but she hiding it behind her talking
Told her one day I'ma change the whole situation
Now she living in a crib that feel like a vacation
Landlord knocking I was ducking out the back (out the back)
Lights got cut we lit candles that's a fact
Did my homework by the flame couldn't hold me back
Education plus the streets that's the real impact (come on)
Grrah
They don't know the math behind where I'm positioned
Compound interest on the years I spent committed
Every rejection was a lesson I've submitted
To the curriculum of life and I'm equipped with it
Application denied times a hundred maybe more
Interview after interview they showed me the door
Something in my spirit said just wait there's something more
Now I'm everything they said I'd never be and more

[Hook: 8 bars]
[Production: Everything intensifies, horns blaring]

This the come up they could never replicate (never)
Rose up from the concrete now I'm feeling great (yuh)
Appetite the engine running at a heavy rate (grrah)
Come up never stops I just accelerate (let's go)
This the come up they could never replicate (never)
Turned the pain to fuel now watch me elevate (yuh)
Destiny was written I was born to dominate (grrah)
Come up in my DNA it's just my fate (let's go)

[Bridge: 4 bars]
[Production: 808 only, everything else drops]

They want the glory but won't talk about the struggle
Won't acknowledge all the nights I almost crumbled
From the bottom of the bottom watch me juggle
Every obstacle I faced I turned to muscle

[Final Hook: 8 bars]
[Production: Everything returns maximum, horns urgent]

This the come up they could never duplicate (never)
From the mud up to the top I sealed my fate (yuh)
Hunger tattooed on my soul it won't evaporate (grrah)
Come up story what I live it's not debate (let's go)
This the come up they could never duplicate (never)
Started with a dream now I'm living what I create (yuh)
Every doubter every hater now they celebrate (grrah)
Come up is forever watch me dominate (let's go)

[Outro: 2 bars]
[Production: 808 sustains, horn stab, cuts hard]

The come up (yuh)
Never stops

[End - Transitions to Track 4: "Loyalty"]
```

---

## Cryo Mix AI Prompts

**Purpose:** Short supplementary prompt for mixing stage
**Character Limit:** 170 characters max

**Formula:**
```
[Genre/style] [concept]. Vocal [characteristic] upfront. [Key element 1] [descriptor]. [Key element 2] [descriptor]. [Mood/energy]. [Production note].
```

### Cryo Mix Examples

**Aggressive Trap Banger:**
```
Aggressive trap come-up anthem. Vocal hungry raw upfront. 808 sliding dominant. Horns urgent stabs. Snares cracking. Hi-hats driving. Streetwise intensity. Relentless energy.
```
(170 characters)

**Triumphant Roc-A-Fella:**
```
Triumphant Roc-A-Fella empire anthem. Vocal commanding upfront. Orchestral horns dramatic. Epic strings. Soul samples. Hard drums. Polished gritty victory. Business mind.
```
(168 characters)

**Dark Atlanta Trap:**
```
Haunted Atlanta trap darkness. Vocal menacing upfront. 808 thunderous dominant. Piano melodic runs. Sparse arrangement. Street grit authentic. Melancholic energy.
```
(162 characters)

---

## Character Trimming Techniques

When over 980 characters, use these techniques:

| Verbose | Trimmed |
|---------|---------|
| "with sonic characteristics" | direct connection |
| "hard-hitting punchy" | "punchy" |
| "drum machine" | just model name |
| "Roland TR-808 drum machine" | "Roland TR-808" |
| "in the style of" | remove entirely |
| "featuring" | comma separation |
| "beautiful lush" | "lush" |

**Formula for quick trim:** Remove adjective stacking. One descriptor per instrument is often enough.

---

## Avoid These Common Mistakes

### ❌ CRITICAL FORMAT ERROR (Most Common)
- ❌ **Using prose/paragraph format instead of JSON structure**
- ❌ Missing curly braces `{ }` around the JSON object
- ❌ Missing JSON keys (`"genre":`, `"mood":`, `"tempo":`, etc.)
- ❌ Writing descriptions as sentences instead of key-value pairs

### Production Prompt Mistakes
- ❌ Using prose format (MUST use JSON structure)
- ❌ Including vocal instructions (save for Final Recording)
- ❌ Missing "instrumental" in genre
- ❌ Missing `"mood"` key
- ❌ Missing `"structure"` key
- ❌ Generic instruments without sonic characteristics
- ❌ Over 980 characters

### Final Recording Prompt Mistakes
- ❌ Using prose format (MUST use JSON structure)
- ❌ Missing `[CLEAR_VOCALS: MAX] (MAX)` tag
- ❌ Missing `"mood"` key
- ❌ Missing `"structure"` key
- ❌ Missing `"vocal_style"` key
- ❌ Missing `"recording"` key
- ❌ Generic ad-libs (be specific: "grrah, yuh, come on")
- ❌ Over 980 characters
- ❌ Missing Vawn vocal essentials

### Lyrics Mistakes
- ❌ Over 5000 characters
- ❌ Missing BPM/Key/Mood in first verse
- ❌ No production notes per section
- ❌ Same energy throughout (no bridge contrast)
- ❌ Ad-libs outside parentheses
- ❌ Missing transition note at end
- ❌ Missing `///*****///` header
- ❌ Missing [Intro] section
- ❌ No double entendres or layered meanings (lacks replay value)
- ❌ No quotable standalone bars (forgettable)
- ❌ Copy-paste hooks with no variation (lazy, boring)
- ❌ No callbacks or internal references (disconnected sections)
- ❌ Reusing key words from other tracks (stale vocabulary)
- ❌ Recycled rhyme schemes across songs (lazy writing)
- ❌ Same metaphors/imagery in multiple tracks (unoriginal)
- ❌ Crutch words in every song: grind, hustle, haters, win (repetitive)

---

## Pronunciation Tips for Lyrics

Suno AI occasionally mispronounces words. These techniques help ensure clarity:

### Syllable Breaks with Hyphens

Prevents slurring on multisyllabic words:

| Slurred | Fixed |
|---------|-------|
| "editing" (ee-dee-ting) | "ed-it-ing" |
| "comfortable" | "comf-ter-bull" |
| "probably" | "prob-ab-lee" |

### Capitalization for Stress

Caps shift emphasis to the correct syllable:

| Word | Stress Pattern |
|------|----------------|
| "de-SCENT" | Emphasis on second syllable (going down) |
| "DEE-scent" | Emphasis on first syllable (ancestry) |
| "pre-SENT" | Verb (to give) |
| "PREZ-ent" | Noun (a gift) |

### Punctuation for Pacing

| Technique | Effect |
|-----------|--------|
| Commas, periods | Create natural pauses |
| Em-dash (—) | Hard break/pause |
| Extended vowels "hellooo" | Drawl/sustained sound |
| Ellipsis "wait..." | Trailing off |

### When to Apply

- ✅ Complex multisyllabic words in dense wordplay
- ✅ Names, places, foreign words
- ✅ Homographs (words spelled same, pronounced different)
- ❌ Ad-libs (looseness is authentic)
- ❌ Common words Suno handles well
- ❌ Southern drawl "mispronunciations" (that's the style)

### Iteration is Key

Suno is probabilistic. Generate 3-5 variants and pick the cleanest pronunciation. The `[CLEAR_VOCALS: MAX]` meta tag combined with `clear pronunciation` in your vocal_style prompt helps, but some words need lyric-level fixes.

**Note:** Vawn's Southern drawl naturally elongates vowels and drops g's ("nothin'" not "nothing"). This isn't mispronunciation—it's authenticity. Don't "fix" intentional dialect.
