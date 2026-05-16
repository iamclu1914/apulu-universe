---
name: music-composition-skill
description: Creates original tracks for the Vawn hip-hop project. Handles Suno v5.5 style prompts using concise prose, role-based instrumentation, combined lyric brackets, J. Cole / T.I. / Jadakiss lyric modes with humanizer layer, and professional five-component delivery.
---

# Music Composition Skill — Vawn Project
# Suno v5.5 — Architecture v2.1

> **Version note (v2.1):** This file replaces the v1 JSON-field/MAX-tag architecture and tightens the v2 prompt doctrine.
> Three structural changes from v1:
> 1. **MAX tags removed.** They are not documented Suno controls. They were
>    consuming character budget without verified effect. If APULU Studio's parser
>    requires them, treat them as a Studio-side concern and inject them at the
>    rendering layer, not at the prompt-construction layer.
> 2. **JSON field format → prose.** Field labels and quotes were decoration; Suno
>    reads the values, not the keys. Prose recovers character budget for actual
>    descriptors.
> 3. **Performance direction migrated out of the style prompt.** Bar-by-bar
>    performance belongs in the lyrics box as combined section cues. The style
>    prompt is global sound DNA only.
>
> Architecture is five parts: Identity, Universal Suno Doctrine, Vawn-Specific
> Format, Lyrics + Humanizer, Studio Output Contract. Producer reference library
> retained. v2.1 adds concise word-count targets, instrument-role language,
> combined lyric brackets, and stricter separation between positive style prompts
> and the Exclude field.

---

# PART A — VAWN IDENTITY

This is the anchor. Before writing a brief, a lyric, or a prompt — know what
Vawn's work draws from. The specificity diagnostic in Part D only functions
if you know who this person is. The voice and sonic locks below define how
he sounds. The territories below define what he is actually saying and why
only he can say it.

## North Star

Vawn is dark cinematic trap-soul with a deep dry bass-baritone vocal,
Atlanta-weighted 808s, gospel organ shadows, dusty soul chops, snapping
drums, warm analog tape texture, and grown-man lyrics about ownership,
love, pressure, family, and what it costs to carry them.

## Core Fear

Failing. Not making it after all the sacrifice. Being irrelevant after the
years spent. This fear doesn't stay in the background — it lives in how
Vawn moves, how he talks about money, loyalty, and time. Every flex has
this fear underneath it. Every brag is partly a prayer. Do not sanitize
it. Write toward the fear, not around it.

## What He Thinks About That Others Don't

Being the person people depend on. Not just personal success — being the
one others call when things collapse. The specific weight of that. Who
counts on him. What it costs to hold them. Whether being reliable is
strength or just another way to get used. Most Atlanta rappers flex the
result. Vawn carries the cost. That gap is where his artistic identity
lives.

## The Contradiction He Holds (Do Not Resolve It)

Marriage and love. It's the thing he wants most and the thing that's done
the most damage. He loves women deeply — not as a flex, not casually.
That same depth is why it costs him. Great and damaging aren't opposites
in his experience; they are the same feeling at different moments with the
same person. Lines about love must carry both without choosing a side.
The moment a song resolves this contradiction it becomes generic.

## The Pre-Brief Check

Before writing any lyric, name which territory this track lives in:

1. Fear of failure and what he does with it
2. The weight of being the person others depend on
3. Love that costs as much as it gives

If the answer is none of them — the brief needs work. Fix it before
touching the lyrics.

## Voice (Locked Every Track)

1. Deep bass-baritone male rap — sub-100Hz, commanding
2. Thick Atlanta drawl — specific regional identity, not exaggerated
3. Layered doubles — stacked vocal doubles for depth
4. Chest-voice dominant — no falsetto, no heavy auto-tune
5. Close-mic dry booth — raw, no reverb on lead vocals

## Sonic Standards (Vawn Signature)

- 808 = dominant, sliding, trunk-rattling
- Organs = Hammond B3, churchy/gospel
- Keys = Fender Rhodes, soul chops, Zaytoven-style piano
- Drums = hard kicks, snapping snares
- Mix = SSL punchy, warm analog, heavy tape saturation
- Vocal texture = Tascam 388 tape saturation, dry close-mic

## What Vawn Is NOT

- Mumble rap / melodic trap drift
- Heavy auto-tune
- Female vocals or high-pitched leads
- Shouting or screaming
- Robotic or metallic vocal texture
- Generic flexing without substance

## What Makes Vawn Distinct

The avoid list above tells you what to refuse. This table tells you what
to be instead. The mistake is making Vawn sound like a generic dark trap
artist. The distinction is in how each element is used, not just what's
present.

| Element       | Generic trap artist        | Vawn                                              |
|---------------|----------------------------|---------------------------------------------------|
| 808s          | Loud low end               | Sliding, trunk-heavy, emotional pressure          |
| Soul samples  | Decoration                 | Memory, inheritance, regret                       |
| Organ         | Churchy effect             | Spiritual weight without preaching                |
| Vocal         | Melodic / autotuned        | Dry bass-baritone chest voice                     |
| Lyrics        | Flex / status              | Ownership, dependability, family, cost            |
| Mood          | Dark / cool                | Triumphant but burdened                           |
| Mix           | Glossy trap                | Warm analog, SSL punch, dry vocal                 |

If a track lands on the left column for any row, it isn't Vawn yet. Push
the brief or the prompt until every row sits on the right.

---

# PART B — UNIVERSAL SUNO PROMPTING (DOCTRINE)

This is the platform-level doctrine. It applies to any artist, not just Vawn.
Part C will apply this doctrine specifically to Vawn.

## The Three-Field Architecture

Suno v5.5 has three distinct fields with distinct jobs. Mixing the jobs
weakens output.

- **Style Prompt = global sound DNA.** Genre, tempo, key, mood, vocal
  identity, instruments, arrangement architecture, production texture,
  mix atmosphere. NOT bar-by-bar control.
- **Lyrics Prompt = timeline, sections, performance, and words.** Section
  tags, combined bracket cues, the actual words, ad-libs, and delivery
  cues. This is where section-by-section control lives.
- **Exclude Field = things you do not want.** All negatives go here.
  Never embed negatives inside the style prompt or lyrics box.

## The Nine-Element Style Prompt Order

Every style prompt should move through these elements in order. Each
element removes a decision Suno would otherwise guess at. More descriptors
does not mean more control — it means weaker prioritization. One anchor,
then build outward.

1. **Genre / subgenre** — ONE primary genre, specific
2. **Tempo / key / time feel** — BPM, key with vibe word, groove feel
3. **Mood / emotional direction** — emotional anchor, not just vibe
4. **Vocal identity** — global timbre, register, mic treatment (NOT
   section-by-section performance)
5. **Main instruments** — 4–6 anchor timbres with clear musical roles;
   brand names only when they sharpen the sound
6. **Groove / drum feel** — pocket, drum pattern character
7. **Arrangement movement** — global arc shape (sparse verses → wide
   chorus, etc.) NOT section-specific commands
8. **Production texture** — analog warmth, tape saturation, dusty sample
   grain, polished sheen, room tone, etc.
9. **Mix atmosphere** — wide vs intimate, punchy vs warm, dominant
   element

## Master Style Prompt Shape

The nine elements above collapse into this practical shape:

> Anchor → tempo/key/groove → emotional contradiction → vocal identity
> (Final Recording Prompt only) → instrument roles → drum/bass behavior →
> arrangement arc → texture/mix.

Default Vawn shape:
> Dark cinematic southern trap-soul, [BPM] BPM, [key + vibe],
> [mood contradiction], [vocal identity if Final Recording Prompt],
> [808 role], [organ/soul chop/key role], [drum pocket],
> [sparse verse → wider hook movement], [analog/tape texture],
> [dry forward vocal or 808-dominant mix].

Use this as a checklist, not a reason to overfill the prompt. If a clause
is not giving Suno a musical decision, cut it.

## Instrument Role Doctrine

Instrument role beats instrument name. Suno gets more useful direction
from what an instrument does than from a bare gear list.

Weak:
> Hammond B3, Rhodes, 808, soul chop, strings

Strong:
> TR-808 sliding sub-bass anchors the hook, Hammond B3 answers the vocal,
> dusty SP-1200 soul chop carries memory, Fender Rhodes cushions the verse,
> strings widen the final hook

Use 4–6 anchor instruments with roles. Brand names are allowed only when
they make the sound more specific.

## Format Rule: Prose, Not JSON

Style prompts are written as comma-separated prose. No field labels, no
quotes, no pipes, no JSON syntax. Suno reads the values; the syntax
overhead just eats character budget.

## Approved Mood Descriptors (Element 3)

The mood field is where most prompts go generic. "Dark," "moody," "cool,"
"vibey" — flat single-word moods produce flat single-mood beats.

Vawn's emotional palette runs in pairs. The contradiction is the point.
Pick one pair as the mood anchor, or combine two if the track earns it.

- triumphant but haunted
- expensive but burdened
- street but polished
- romantic but damaged
- confident but aware of the cost
- spiritual without becoming gospel
- cinematic without becoming movie-score rap

These plug directly into element 3 of the nine-element order. Example:
"Dark cinematic trap-soul, 128 BPM, minor key, *triumphant but haunted*,
deep bass-baritone..."

Banned mood-word reminder: "legacy" is on the humanizer purge list for
lyrics. Do not let it leak into mood descriptors either. Use "what it
costs to carry it," "the weight," or one of the pairs above instead.

## What Belongs Where (The Hard Lines)

**Belongs in style prompt:** genre, BPM, key, mood, global vocal identity,
instruments, groove, arrangement architecture, production texture, mix.

**Belongs in lyrics box:** section tags, combined bracket cues
([Hook - Energy: High], [Bridge - Breakdown, spoken word]), the actual
words, ad-libs, delivery cues, and localized energy/performance signals.

**Belongs in exclude field:** every negative — wrong vocal types, wrong
genres, unwanted instruments, robotic vocals, excessive autotune, muddy
mix, shouting, etc.

**Belongs nowhere in any prompt field:** exact mixing/mastering targets
(LUFS, dBTP, HPF frequencies, compression ratios, EQ values). Those are
for post-production in Reaper / Ozone / Neutron. Suno does not reliably
parse them.

## Documented vs Experimental

Treat the following as DOCUMENTED Suno behavior (high confidence):

- Custom Mode
- Style prompt as natural-language descriptor
- Lyrics prompt with structure tags
- Exclude field
- Section tags ([Verse], [Chorus], [Bridge], [Outro])
- Creative Sliders (Weirdness, Style Influence, Audio Influence)
- Studio editor / Replace Section / stem export

Treat the following as EXPERIMENTAL / community-discovered (lower
confidence — test before depending on):

- Combined-bracket vocal cues ([Verse 1 - chest voice], [Bridge - spoken word])
- Advanced structure cues inside section brackets ([Bridge - Atmospheric Shift])
- Exact gear/brand-name obedience
- Per-bar key/tempo control mid-song

When something experimental fails, the failure is in the experiment, not
the system. Fall back to documented controls.

## Character Economics

- Style prompts:
  - Simple tracks: 45–75 words
  - Standard Vawn tracks: 70–110 words
  - Complex fusion tracks: 110–140 words max
  - Hard ceiling: under 980 characters
- Lyrics box: 2,800–3,100 characters (3:00–3:20 runtime)
- 1 character of lyrics ≈ 0.065 seconds of audio
- 3:00 ≈ 2,770 chars | 3:10 ≈ 2,920 | 3:20 ≈ 3,080

## Generation Hygiene

Generate multiple versions before changing the prompt. Suno interpretation
varies between generations even with identical input. If three generations
all miss the same way, the prompt is wrong. If two of three land, the
prompt is fine — pick the best.

---

# PART C — VAWN-SPECIFIC PROMPT FORMAT

This is Part B applied to Vawn. The doctrine doesn't change; the
content does.

## Two Prompts Per Track

Every Vawn track requires TWO style prompts:

1. **Production Prompt** — instrumental only, no vocal identity
2. **Final Recording Prompt** — same beat, plus global vocal identity

The two-prompt workflow lets you generate the instrumental cleanly first,
then layer Vawn's vocal identity on top. Both prompts are prose. Standard
Vawn prompts target 70–110 words, complex fusion prompts cap at 140 words,
and all prompts stay under 980 characters. Neither contains MAX tags.

## Production Prompt Template

Prose, comma-separated, follows the nine-element order from Part B.
NO vocal identity. NO performance direction. NO MAX tags. Write positive
instructions only; negatives belong in Exclude Styles.

Template skeleton:
> [Primary genre], [BPM] BPM, [key with vibe word], [mood contradiction],
> [808/bass role], [organ/key/sample role], [drum pocket],
> [arrangement architecture], [production texture and analog warmth],
> [mix focus].

Example (dark cinematic southern trap-soul, 128 BPM):
> Dark cinematic southern trap-soul, 128 BPM, D minor brooding,
> triumphant but haunted, TR-808 sliding sub-bass anchors the hook,
> Hammond B3 answers the vocal with church-shadow weight, dusty SP-1200
> soul chop carries memory, MPC3000 kicks and snapping snares lock a
> heavy half-time pocket, sparse verses open into an organ-led hook,
> Tascam 388 tape warmth, SSL punchy dark mix, clean low-end separation,
> 808 dominant.

## Final Recording Prompt Template

Same as Production Prompt, plus global vocal identity inserted as element
4 (after mood, before instruments). NO bar-by-bar performance — that
moves to lyrics box as combined bracket cues.

Vawn's locked vocal identity (paste this into every Final Recording
Prompt):
> deep bass-baritone male rap with thick Atlanta drawl, chest-voice
> dominant, layered doubles, dry close-mic booth recording, grounded
> human delivery, crisp consonants, controlled low-register authority

Full example:
> Dark cinematic southern trap-soul, 128 BPM, D minor brooding,
> triumphant but haunted, deep bass-baritone male rap with thick Atlanta
> drawl, chest-voice dominant, layered doubles, dry close-mic booth
> recording, grounded human delivery, crisp consonants, controlled
> low-register authority, TR-808 sliding sub-bass anchors the hook,
> Hammond B3 answers the vocal with church-shadow weight, dusty SP-1200
> soul chop carries memory, MPC3000 kicks and snapping snares lock a
> heavy half-time pocket, sparse verses open into an organ-led hook,
> Tascam 388 tape warmth, SSL punchy dark mix, dry forward vocal,
> 808 dominant.

## Hard Rules for Vawn Style Prompts

### No Artist or Producer Names

Suno's frontend accepts artist names silently, but the backend replaces
them at generation time. Use sound descriptors only — see REFERENCE
section at the end of this file for producer descriptor library.

### Prompt Length Rule

Default Vawn style prompts target 70–110 words. Use 45–75 words for simple
tracks and 110–140 words only for complex fusion. The 980-character limit
is a hard ceiling, not the target.

### Instrument Role Rule

Use 4–6 anchor instruments with roles. Do not write bare instrument lists
when a role would clarify the song.

WRONG: "TR-808, Hammond B3, SP-1200 soul chop, Rhodes, strings"
RIGHT: "TR-808 sliding sub-bass anchors the hook, Hammond B3 answers the
vocal, dusty SP-1200 soul chop carries memory, Rhodes cushions the verse"

### Genre Tag Rule

Genre slot contains ONE primary genre. Mood words go in mood slot, not
genre slot.

WRONG: "Dark cinematic southern trap, moody atmospheric, late-night..."
RIGHT: "Dark cinematic southern trap, ..., late night cinematic
melancholy mood, ..."

### Key Names — Use Vibe Words, Not Theory

- Bb major = warm and triumphant
- D minor = dark and brooding
- F minor = heavy and cinematic
- C# minor = tense and menacing
- F# minor = anguished, tense
- A minor = melancholic, introspective

### Analog Warmth Signal — Always Include

Every Vawn prompt includes an analog warmth or recording aesthetic
descriptor. Standard form: "Tascam 388 analog warmth" or "tape saturation
and analog warmth."

### BPM Reference by Genre

- 60–75 = ballad, ambient, slow R&B
- 76–95 = hip-hop, lo-fi, soul, boom bap
- 96–115 = pop, indie, mid-tempo trap, Motown × trap fusion
- 116–130 = OVO / moody atmospheric hip hop
- 128–138 = dark cinematic southern trap, Don Cannon / OVO hybrid
- 131–150 = fast trap, southern trap, club trap
- 151+ = drum and bass, extreme

## Standard Vawn Exclude Styles

Default exclude block (paste into Exclude Styles field):

> female vocals, high-pitched vocals, choir, female humming, mumble
> rap, shouting, screaming, robotic vocals, metallic vocals, heavy
> auto-tune, monotone delivery, bedroom lo-fi mix, thin lo-fi vocals,
> muddy mix, weak low end, cluttered arrangement, AI artifacts,
> reverb on lead vocals, falsetto

Adjust per track only when the track's brief explicitly requires it.

---

# PART D — LYRICS + HUMANIZER

## Lyrics Box Contents — The Hard Rule

The lyrics box contains ONLY:

- Actual words to be rapped or sung
- [Section tags] — [Intro], [Verse 1], [Hook], [Bridge], [Outro]
- Combined bracket cues — [Hook - Energy: High], [Bridge - Breakdown, spoken word]
- (Ad-libs and delivery cues in parentheses)
- Localized energy, structure, and performance signals inside the section bracket

**Never put in the lyrics box:** BPM, key, mood, instrument descriptions,
production notes, mix language. Suno will rap them aloud.

## Section Tag Placement (v5.5 Primary Control Surface)

In v5.5, section tags are the highest-value control layer. Section
identity comes from the writing — a chorus written like a chorus
responds better than a verse with a chorus bracket.

**Top-load the palette** in the style prompt's mood/arrangement fields,
not in the lyrics box.

**Localize hard turns** by combining the section label, cue, and
performance direction into one bracket. This keeps the instruction tied
to the section instead of creating adjacent standalone tags.

Do this:
```
[Verse 1 - chest voice]
lyric lines

[Pre-Chorus - Build-Up]
shorter anticipation lines

[Hook - Energy: High, soulful, full chest]
hook lines
```

Not this:
```
[Hook]
[Energy: High]
[soulful]
hook lines
```

Plain section tags are fine when no extra instruction is needed:
```
[Intro]
[Verse 1]
[Hook]
[Outro]
```

## Cue Budget

Use 4–8 enriched section cues per song.

Plain section tags do not count:
> [Verse 1], [Hook], [Outro]

Enriched cues count:
> [Hook - Energy: High]
> [Bridge - Breakdown, spoken word]
> [Final Hook - Final Surge, layered]

If Suno ignores cues, simplify. Do not add more tags.

## Vocal Cue Vocabulary (Performance Direction Lives Here)

Use vocal cues inside the combined section bracket. Use sparingly — only
where delivery shift matters.

- chest voice — deep resonant lower register
- raspy — gritty, textured delivery
- soulful — emotionally rich R&B/gospel
- aggressive — forceful, intense
- whispered — quiet, close-mic
- spoken word — non-melodic spoken delivery
- harmonized — adds backing harmony to section
- layered — multiple vocal stacks

These cues are the new home for what used to live in the style prompt's
"performance:" field. Migrate performance direction here, not into the
style prompt.

## Advanced Structure Cues (Section-Level Musical Control)

Use structure cues inside combined section brackets for section-level
musical control. Place them where you need the effect, not only at the
top.

- Atmospheric Shift — abrupt mood/texture change
- Tension Build — ratchets up harmonic tension
- Dynamic Contrast — loud/quiet variation within section
- Breakdown — stripped-back, fewer elements
- Build — gradual crescendo to drop or chorus
- Build-Up — rising tension into chorus or drop
- Drop — heavier impact lane after the build
- Post-Chorus — section after chorus, additional hook energy
- Cold Ending — abrupt hard stop, no fade
- Fade Out — gradual volume decrease at end
- Instrumental — no vocals, purely musical section

## Standard Structure Template

```
[Intro - Sparse Entrance]
(instrumental — brief cue)

[Verse 1 - chest voice]
(delivery cue)
Lyric lines
(grrah / ayy)

[Pre-Chorus - Build-Up]
(anticipation lines — shorter, tighter phrasing)

[Hook - Energy: High, soulful, full chest]
(production cue)
Hook lines
(ayy / grrah)

[Verse 2 - chest voice]
(delivery cue)
Lyric lines
(grrah / ayy / talk to me)

[Pre-Chorus - Build-Up]
(anticipation lines)

[Hook - Energy: High, soulful, full chest]
Hook lines
(ayy / that's right)

[Bridge - Breakdown, spoken word]
Short bridge lines
(grrah...)

[Build - Tension Build]
(short lift into the final hook)

[Final Hook - Final Surge, layered]
(biggest — production cue)
Hook lines
(ayy / let's go / grrah / that's right)

[Outro - Fade Out]
(Ad-lib fade: ...)
```

## Lyric Writing Modes

### J. Cole Foundation

14-line verse arc:
- Setup (4 lines) — establish the scene specifically
- Development (6 lines) — observation, complication, internal pivot
- Revelation (4 lines) — the uncomfortable or honest truth

Core techniques:
- Internal rhyme chains — rhyme mid-line AND end-line
- Syllable density — 12–16 syllables per line, consistent
- Conversational pivots — "See what I'm saying is..." / "Nah for real though..."
- Earned complexity — mixed feelings over clean takeaways
- Rhythm variation — short punchy lines mixed with long ones

### T.I. Foundation

16-bar verse arc:
- Position (4 bars) — declare the stance with authority, lock into the
  beat's pocket
- Defense (8 bars) — rapid-fire development, internal rhymes accelerate,
  anticipate critics and answer them in the same bars
- Punchline close (4 bars) — drop velocity, go deliberate, land the truth
  bomb or double entendre

Core techniques:
- Syncopated pocket lock — flow snaps to the hi-hat pattern, not just the
  downbeat
- Velocity shift — accelerate through the middle 8, then drop hard before
  the punchline
- Internal rhyme acceleration — 2–3 internal rhymes per bar in development
- Alliteration burst — 3–4 consecutive words starting with the same sound
- Counterpunch structure — state position, imagine objection, demolish it
- Bankhead specificity — name real places, real textures, real street
  logic (not generic hood)
- Southern drawl held natural — Atlanta twang as part of the rhythm
- King framing — every self-reference carries royal authority, earned

### Jadakiss Foundation (Earned Clarity Mode)

Use when the track calls for: lived-in authority, stacked punchlines,
compressed storytelling, the calm confidence of someone who already came
through.

16-bar verse arc:
- Scene-entry (4 bars) — drop into the middle of the situation. No
  preamble. The listener is already behind.
- Compression zone (8 bars) — stack 3–4 consecutive punchlines here,
  not just at the end. Each bar should stand alone. Internal rhymes
  double up inside the line; end rhymes shift every 2–4 bars.
- Exit line + punctuation (4 bars) — most quotable bar last, delivered
  flat with no explanation. Then a short dismissive closer.

Core techniques:
- Mid-tempo pocket, slightly behind the beat — relaxed but intentional
- Punchline stacking — multiple quotable lines per verse
- Compressed storytelling — full scene in 2–4 bars; no extended setup
- Rasp as instrument — write bars that land better said slowly and gravelly
- Rhetorical punchline — frame the hardest observation as a question or
  plain statement that implicates without explaining
- Survivor's authority — speak from experience, not aspiration
- Exit punctuation — a short, flat closer. Not a celebration. A period.
- Yonkers specificity → Vawn specificity: replace street locale with
  emotional locale. The immigrant block. The follower years. The weight
  of being depended on.

### Mode Selection

- **Jadakiss mode** — fear already processed, earned clarity, stacked
  punchlines, compressed authority, gritty confidence
- **J. Cole mode** — active introspection, emotional reveals, slow
  narrative builds
- **T.I. mode** — street assertion, trap production, velocity and
  confrontation

Can layer:
- Jadakiss-cadenced compression in the body → Cole-style revelation at
  the close
- T.I. velocity in the setup → Jadakiss exit punctuation to close

## Vawn's Own Techniques (Beyond the References)

Cole, T.I., and Jadakiss are inputs, not the output. These are Vawn's
specific moves. Use at least one per track.

**The Dependability Verse**
Verse from the position of the person others lean on. Not a flex — a
reckoning. What he carries. Who doesn't see the cost. The verse ends on
an image, not a conclusion: "Still picked up on the second ring."

**The Love Damage Structure**
The verse celebrates. The hook reveals the wound. Not as a twist — as
the truth that was always there. By the bridge, the listener should feel
that the celebration and the damage were the same thing all along. This
mirrors the Part A contradiction — do not resolve it.

## Brief-Specificity Diagnostic

If the AI reaches for generic language — "testament," "legacy," "grind,"
"foundation," "blueprint" — the brief wasn't specific enough. These
words are what an AI writes when it doesn't know the actual angle.

Before running the humanizer checklist, ask:
- Does this verse name the specific territory from Part A?
- Does it have one concrete image only Vawn could provide?
- Does it know exactly what emotional moment it's capturing?

If any answer is no — fix the brief and regenerate. Word bans are a
last-resort cleanup tool, not a substitute for specificity upstream.

## Humanizer Audit

Purge these patterns:
- "testament to resilience" → "I watched them glass towers stack up
  where the old spots used to breathe"
- "the journey / the grind" (abstract) → name the specific thing:
  "4am sessions", "rewrote the verse 30 times"
- "it means everything" → show it with an image or action
- "we rise together" → name who, what, when
- Generic positive closer → end on a specific truth or image, not uplift
- Three-synonym stack → pick one, drop two
- -ing tack-ons ("reflecting on my journey") → cut the tail, let the
  line stand

Audit checklist:
- [ ] No significance inflation (testament, legacy, journey, pivotal)
- [ ] No vague emotional claims — every feeling is shown, not stated
- [ ] No anthem/slogan language — specific to THIS man, not "a rapper"
- [ ] No rule-of-three synonym stacks
- [ ] No generic positive closer
- [ ] Every line could only be written by this specific person
- [ ] Mixed feelings where appropriate

The specificity test: ask "Could another rapper write this exact line?"
If yes → rewrite.

## Banned Crutch Lines

- "Mama always told me..." / "Daddy wasn't there..."
- "Started from the bottom..." / "Came from nothing..."
- "They don't want me to win..." / "Real ones know..."
- "God got me..." / "Back against the wall..."
- "Haters gonna hate..." / "Can't stop won't stop..."

## Banned Lazy Themes (Once Used, Closed for Project)

- Generic "proving doubters wrong"
- Abstract grind/hustle flexing
- Generic spirituality without complication

## Vocabulary Freshness

Words used in one track cannot appear in another in the same project.

Active banned vocabulary:

- **Never Fold:** pressure, fold, survivors, cold, shoulders, consequence
- **Move in Silence:** silence, numbers, ground, crown, co-sign
- **The Plug:** plug, clientele, pipeline, wholesale, retail
- **Nothing Lines Up:** fracture, strobe, static, residue, archive, fragment, dissolve
- **Without Permission:** permission, greenlit, validation, friction, lane
- **From the Mud:** negotiate, excavate, leveraged, foundation, assembled, concrete, terrain, circuit, backing, sponsor, admission, blueprint, ledgers, bedrock, bandwidth, marble
- **The Woman That Almost Got Away:** accumulate, calculations, certainty, oxygen, rationing, conserve, intimacy, timeline, stayed
- **Paid on Friday:** deposit, barber, cleaner, valet, pending, alarm
- **80s double entendre:** tambourine, dame, wavelength, jewelry, returning, groove
- **Down Here in the A:** reckoning, cathedrals, precision, cascade, incision, permanent, layered
- **Before The Room:** inbox, legal pad, ledge, clapped, propping, waiting room, consistent, resolve, afforded, oath
- **The Version I Promised:** rehearsal, voicemail, arrival, particular, promised
- **First On The List:** emergency, contact, resource, list, useful, unruled, vivid, adrift, stressing, file, emergencies, activates, practice, pressing, reliable, code, trained
- **The Table:** table, seat, chair, owe, earned, early, doors, builder, arithmetic, proximity, grievance, sparse, cousin, rewrite
- **The Between Time:** season, quiet, between, calendar, swallowed, motion, surfaced, curated, stripped, volume, signal, answering, cooking, ritual, habit, riot, burned out, noise
- **Second Wind:** explain, loaded, receipt, dial, walk inside, ceiling, heat, locked, chest, broke, quarter, files, notes, co-sign, lunch, meeting link, calculating, breath, whisper, next move, drought, retire, safety, Tuesday

---

# PART E — STUDIO OUTPUT CONTRACT

## The Five Components

Every completed Vawn track must deliver these five components, in this
order:

1. Song Title
2. Production Prompt (prose, instrumental, no vocals)
3. Exclude Styles
4. Final Recording Prompt (prose, with vocal identity)
5. Lyrics

## Default Delivery: Structured Text

Clean, clearly labelled sections with a blank line between each block.
Durable, copy-pasteable, works everywhere without maintenance.

## Enhanced Delivery: HTML Card

Use when the workflow benefits from individual copy buttons per block.

HTML card format:
- Each block gets its own Copy button
- Lyrics block renders section tags in gold
- Hidden textarea for clean copy
- ALWAYS use `document.execCommand` fallback — never `navigator.clipboard`
  alone (sandboxed environments break the modern API)
- Use `getElementById` event listeners with fixed-position textarea, not
  hidden absolute-positioned

The content is the product. The delivery format is a preference, not a
requirement. Do not let HTML rendering issues block a track from being
delivered.

## Structural Variety Rule

Every track must have a different structure than the prior tracks in
the project.

Structure options:
- **Hook First:** Hook → V1 → Hook → V2 → Bridge → Hook (immediate impact)
- **Verse First:** V1 → Hook → V2 → Hook → Bridge → Hook (storytelling)
- **Cole Structure:** V1(14) → Hook(4–6) → V2(14) → Hook → Bridge → V3(8)
  → Hook (introspective)
- **Recurring Tag:** tag throughout verses + short hook (hype/energy)
- **Cinematic Narrative:** setup → rising action → climax, chorus
  meaning flips (story with twist)
- **Confessional:** melodic intro → chorus first → confessions deepen →
  MY → YOUR shift (emotional)
- **Subversive:** chant + full chorus alternate, no resolution
  (trojan horse)
- **Pre-Chorus Build:** V1 → Pre-Hook → Hook → V2 → Pre-Hook → Hook →
  Bridge → Hook

Vary per track:
- Intro style: spoken, instrumental, cold open, question, statement
- Hook length: 4 bars = punch, 6–8 = anthem
- Verse length: 8, 12, 14, 16 — content-driven
- Bridge style: spoken, stripped, chant, [Bridge - Atmospheric Shift]
- Outro: [Outro - Cold Ending], [Outro - Fade Out], spoken truth, extended ad-lib

## Studio Workflow (Post-Generation)

After generating, open Studio before accepting or discarding:

1. **Check structure first** — is the section logic right? Verse/chorus
   contrast clear? If yes, the track has salvage value.
2. **Use Quick Replace** on sections that didn't land — not the whole
   song.
3. **Export stems** if the arrangement is right but the mix needs cleanup.
4. **Finish in DaVinci Resolve or DAW** when the track earns it.

Common Studio fixes:
- Outro ends too abruptly → use [Outro - Fade Out] + keep final lyric short →
  apply fade out in Studio on the region
- Chorus doesn't lift → shorten the hook, rewrite the bracket as
  [Hook - Energy: High, soulful] or [Final Hook - Final Surge, layered]
- Verse repeats or drifts → make Verse 2 clearly different in angle,
  image, or detail from Verse 1
- Bridge sounds like Verse 3 → strip the arrangement or change the
  rhythmic feel with [Breakdown]

Protect credits: only refine songs that already prove they have
structure, identity, and emotional purpose. Move on from tracks that
don't.

---

# REFERENCE: PRODUCER SOUND DESCRIPTORS

Use these in place of artist/producer names. All entries are formatted
as prose-ready style prompts. Performance direction is shown separately so it can be translated into
combined section brackets in the lyrics box, not placed in the style prompt.

When pulling from this library, paste the **Style** line into the prompt
and translate the **Performance** line into combined section bracket cues
inside the lyrics box.

---

## VAWN SIGNATURE SOUNDS

**Dark cinematic trap / OVO hybrid (128 BPM)**
Style: Dark cinematic southern trap, 128 BPM, minor key brooding melancholy, late night cinematic melancholy with held tension, SP-1200 dusty soul chop dominant, Roland JX-3P dark reverb pads, Hammond B3 church organ, TR-808 melodic sliding sub-bass, MPC3000 trap kicks, snapping snares, sparse hi-hats, half-time trap pocket measured and deliberate, sparse verses lifting into wider chorus with organ swells, Tascam 388 analog warmth and tape saturation, SSL warm punchy mix wide and dark, 808 melodic and heavy, clean low-end separation.
Performance (lyrics box): [Verse - chest voice, measured cadence], [Hook - Energy: High, held authority, steady tone].

**Orchestral soul / boom bap (triumphant, 88–96 BPM)**
Style: Orchestral soul hip hop, 92 BPM, minor key introspective, triumphant grit and earned energy, flipped gospel soul brass loop, triumphant horn stabs, lush string swells, Hammond B3 gospel chords, TR-808 sliding sub-bass, MPC3000-style hard kicks, snapping snare on 2 and 4, tight hi-hats, deliberate boom bap pocket, sparse verses opening into anthemic chorus, Tascam 388 analog warmth, SSL punchy wide mix, brass dominant, snare snapping, strings lush in chorus, tape saturation, clean low-end separation.
Performance (lyrics box): [Verse - chest voice, deliberate and grounded], [Hook - Energy: High, full chest, open and commanding].

**Psychedelic boom bap (dark, meditative, 75–88 BPM)**
Style: Psychedelic boom bap, 82 BPM, minor key dark, dark and meditative dusty cinematic introspection, single dusty jazz-soul melodic loop chopped and filtered dominant, MPC3000-style hard kick, heavy snare on 2 and 4, sparse hi-hats, Fender Rhodes dark accent, upright bass anchor, sparse string stabs, dusty meditative pocket, Tascam 388 vinyl analog warmth, SSL warm wide mix, loop dominant and raw, vinyl texture, raw vinyl character, clean low-end separation.
Performance (lyrics box): [Verse - chest voice, internal close-mic, measured], [Hook - chest voice, darker intensity, restrained].

**Atlanta southern trap (menacing, 130–142 BPM)**
Style: Atlanta southern trap, 138 BPM, minor key heavy, heavy and cinematic menacing energy, SP-1200 soul chops, TR-808 massive sliding sub-bass dominant, hard trap kicks, snapping snares, Hammond B3 church organ swells, hard percussive trap pocket, Tascam 388 analog warmth, SSL punchy mix, 808 trunk-rattling dominant, organ warm, tape saturation, clean low-end separation.
Performance (lyrics box): [Verse - aggressive, hard percussive cadence], [Hook - chest voice, heavy authority, dominant].

**Atlanta trap with organ-led chorus**
Style: Atlanta southern trap, 135 BPM, minor key soulful, heavy dark verses lifting into gospel pride at chorus, SP-1200 soul chops and melodic loops, TR-808 massive sliding sub-bass dominant, MPC3000-style trap kicks and snares, Hammond B3 church organ full melodic chorus lead, Fender Rhodes verse accent, dark verse pocket opening into wide gospel hook, Tascam 388 analog warmth, SSL punchy mix, 808 dominant verses, organ melodic wide at chorus, tape saturation, clean low-end separation.
Performance (lyrics box): [Verse - chest voice, measured and low], [Hook - Energy: High, soulful, organ rises, full chest].

**Motown soul × Atlanta trap (celebratory, 108–118 BPM)**
Style: Motown soul Atlanta trap, 114 BPM, major key bright, bright celebratory Friday-night energy, TR-808 bouncy warm sub-bass dominant, MPC3000-style crisp trap kicks and snares, Hammond B3 Motown organ groove, Fender Rhodes warm 80s keys, lush string chorus swell, bouncy mid-tempo pocket, Tascam 388 analog warmth, SSL wide warm mix, 808 bouncy and present, organ bright, strings lush in chorus, tape saturation, clean low-end separation.
Performance (lyrics box): [Verse - chest voice, smooth and conversational], [Hook - soulful, bright and warm, controlled energy].

**Dreamville soulful hip hop with 808s (88–96 BPM)**
Style: Soulful orchestral hip hop, 92 BPM, minor key uplifting, gritty uplifting earned honest energy, flipped soul brass or gospel loop, triumphant horn stabs, lush string swells, Hammond B3 chords, TR-808 sliding sub-bass dominant throughout, MPC3000-style kicks, snapping snare, rolling hi-hats, grounded narrative pocket, Tascam 388 analog warmth, SSL punchy wide mix, 808 warm and present, brass dominant, strings lush in chorus, tape saturation, clean low-end separation.
Performance (lyrics box): [Verse - chest voice, grounded and narrative-driven], [Hook - Energy: High, full chest, emotional lift].

---

## PRODUCER SOUND LIBRARY

**Scott Storch — Piano-Led Cinematic Soul**
Style: Piano-led cinematic soul hip hop, 95 BPM, minor key dramatic, cinematic drama and moody introspection, grand piano dominant, live electric guitar lead lines, Latin percussion clave and congas, TR-808 sub-bass, MPC-style kicks and snares, orchestral string stabs, brass accents, Neve 1073 analog warmth, SSL punchy wide mix, piano dominant and live, Latin percussion prominent, strings lush at hook, organic analog character.
Performance: [Verse - chest voice, melodic and measured, emotional weight], [Hook - chest voice, full and open, controlled power].

**Justice League — Anthemic Southern Trap / Organ-Driven**
Style: Anthemic southern trap, 134 BPM, minor key gospel-inflected, triumphant and hard street gospel energy, Hammond B3 organ dominant, triumphant horn stabs, TR-808 thundering sub-bass, snapping trap snare, punchy kick, gospel choir swells, SP-1200 soul chop, Neve 8078 analog warmth, SSL punchy wide mix, organ dominant, 808 thundering, snare bright and snapping, clean low-end separation.
Performance: [Verse - aggressive, hard and authoritative], [Hook - Energy: High, soulful, full chest, gospel power].

**The Runners — Breezy Miami Hip-Hop / Caribbean Bounce**
Style: Miami hip hop Caribbean trap, 100 BPM, major key bright, breezy warm feel-good energy, steel drum melodic loop, Caribbean percussion dominant, TR-808 bouncy sub-bass, clean snap snare, punchy kick, live horn accents, Fender Rhodes warm accent, SSL 4000 analog warmth, warm wide mix, Caribbean percussion present and bright, 808 bouncy, bright open bounce.
Performance: [Verse - chest voice, smooth and flowing easy cadence], [Hook - soulful, bright and easy, celebratory].

**Mike WiLL Made-It — Trap Minimalism / Space & Silence**
Style: Minimalist Atlanta trap, 135 BPM, minor key eerie, dark eerie cinematic tension, sparse eerie synth melody minimal, TR-808 massive sub-bass dominant, hard snapping trap snare, punchy trap kick, layered hi-hat rolls, finger snaps, deliberate silence between elements, minimal arrangement, Neve 1073 analog warmth, SSL punchy mix, 808 massive and dominant, snare snapping, deliberate space and silence, uncluttered arrangement.
Performance: [Verse - aggressive, hard and staccato percussive delivery], [Hook - chest voice, heavy and authoritative, commanding drops].

**Hit-Boy — Soulful Boom Bap / Polished Trap**
Style: Soulful boom bap polished trap, 95 BPM, minor key soulful, triumphant nostalgic soul introspective clarity, flipped soul vocal chop or melodic loop dominant, SP-1200 dusty samples, live piano accents, TR-808 warm sub-bass, MPC3000-style hard kicks, crisp snapping snare, rolling hi-hats, organ swells at hook, Neve 8078 analog warmth, SSL punchy wide mix, soul chop or loop dominant, 808 warm and present, snare bright and snapping, tape saturation, clean low-end separation.
Performance: [Verse - chest voice, measured and deliberate, narrative weight], [Hook - Energy: High, soulful, triumphant and full, earned energy].

**Mike Dean — Psychedelic Synthesizer Hip-Hop / Cosmic Trap**
Style: Psychedelic synthesizer hip hop, 90 BPM, minor key cosmic, cosmic psychedelic hypnotic introspection, analog synthesizer lead dominant multi-layered, Prophet-5 or Minimoog warm synth pads, TR-808 sliding sub-bass, MPC-style drums, distorted guitar accent, vintage keyboard melodic layers, psychedelic FX processing, Tascam 388 tape saturation, SSL wide warm mix, synth dominant and layered, 808 melodic, psychedelic space and depth, warm analog character.
Performance: [Verse - chest voice, hypnotic and meditative deliberate], [Hook - chest voice, epic and expansive, commanding].

**Swizz Beatz — Hard-Knocking New York Hip-Hop / Electronic Trap**
Style: Hard-knocking New York hip hop, 100 BPM, minor key aggressive, hard-knocking aggressive energy and triumph, electronic synth stab dominant, hard punching snare dominant, booming kick, TR-808 sub-bass accent, brass horn stab, Middle Eastern melodic element, live guitar accent, Neve 8078 punchy mix, SSL punchy hard mix, snare dominant and snapping, synth stabs sharp, bass punchy, clean low-end separation.
Performance: [Verse - aggressive, hard staccato cadence], [Hook - Energy: High, triumphant and powerful, commanding].

**Pharrell Williams — Minimalist Neo-Soul Hip-Hop / Syncopated Funk**
Style: Minimalist neo-soul hip hop, 98 BPM, major key syncopated, playful infectious groove with sunny introspection, Roland TR-808 minimalist drum programming, funky guitar riff or synth melody, minimal live bass or 808 sub-bass, vintage Wurlitzer keyboard accent, syncopated drum machine groove dominant, sparse Fender Rhodes accent, Neve 1073 warm mix, SSL wide warm mix, groove dominant, syncopated drum programming front, bass warm and understated, understated minimalist polish.
Performance: [Verse - chest voice, conversational groove-locked playful], [Hook - soulful, melodic and infectious warm delivery].

**Juicy J — Triple Six Memphis Trap / Horror Cinematic**
Style: Memphis trap horror cinematic, 138 BPM, minor key ominous, ominous dark hypnotic menace, horror film synth sample or ominous loop dominant, TR-808 massive sub-bass dominant, hard snapping trap snare, punchy trap kicks, dark orchestral stabs, pitch-shifted vocal chop eerie, lo-fi texture, Tascam 388 tape saturation, SSL punchy mix, 808 massive dominant, ominous loop dominant, snare snapping, lo-fi tape texture, dark and heavy.
Performance: [Verse - aggressive, ominous and hypnotic low and menacing], [Hook - chest voice, heavy and repetitive, commanding weight].

**Bangladesh — Eccentric Atlanta Crunk-Trap / Hard-Knocking Synth**
Style: Eccentric Atlanta crunk trap, 120 BPM, minor key chaotic, chaotic energy aggressive club-ready, eccentric synth stab or melodic riff dominant, TR-808 thundering sub-bass dominant, snapping crunk snare, hard punching kicks, handclap pattern, brass stab accent, deliberately unpredictable arrangement, Neve 8078 punchy mix, SSL punchy hard mix, synth stabs sharp and eccentric, 808 thundering, snare punching, energetic and raw.
Performance: [Verse - aggressive, unpredictable percussive cadence], [Hook - Energy: High, chaotic energy commanding].

**Timbaland — Rhythmic Percussion-Forward Electronic Funk**
Style: Rhythmic percussion-forward electronic hip hop, 100 BPM, minor key exotic scale, futuristic groove with rhythmic complexity and global energy, complex live drum programming multi-layered dominant, talking drum or tabla percussion, electronic synth arp or melodic riff, TR-808 sub-bass accent, futuristic sound design FX, stuttered vocal chop rhythmic, Triton keyboard stab, SSL 4000 wide mix, percussion dominant and layered, synth melodic, sub-bass warm, rhythmic depth and movement.
Performance: [Verse - chest voice, conversational and rhythmically precise], [Hook - soulful, melodic memorable rhythmically infectious].

**DJ Mustard — West Coast Ratchet / Minimal Bounce**
Style: West Coast ratchet trap, 110 BPM, minor key club-ready, club energy West Coast bounce minimal cool, minimal synth melody dominant, TR-808 bouncy sub-bass dominant, snapping snare dominant, four-on-the-floor trap kick, hi-hat rolls tight, deliberate minimal arrangement, handclap, Yamaha DX7 synth accent, SSL 4000 clean mix, 808 bouncy and dominant, snare snapping, minimal space deliberate, minimal uncluttered bounce.
Performance: [Verse - chest voice, smooth low-energy West Coast cadence], [Hook - Energy: High, catchy and minimal infectious repetition].

**Tay Keith — Anthem Trap / Aggressive Orchestral**
Style: Anthem trap orchestral, 150 BPM, minor key cinematic, aggressive triumphant anthem with crowd energy, dramatic orchestral string stabs dominant, brass triumphant hits, TR-808 thundering sub-bass dominant, snapping aggressive trap snare, punching trap kicks, hi-hat rolls rapid, dramatic build-up FX, Neve 1073 punchy mix, SSL punchy hard wide mix, strings dominant and dramatic, 808 thundering, snare snapping aggressive, energetic and loud.
Performance: [Verse - aggressive, fast high-energy cadence], [Hook - Energy: High, anthemic and powerful, full authority].

**Polow Da Don — Futuristic Southern R&B-Pop**
Style: Futuristic southern R&B pop trap, 110 BPM, minor key sleek, futuristic cool polished energy aspirational, electronic synth melody dominant futuristic, TR-808 sub-bass dominant, crisp electronic drum kit, synth bass line, arp synth texture, electronic clap and snap pattern, Neve 8078 polished mix, SSL polished wide mix, synth dominant and futuristic, 808 smooth, clean and crisp, clean low-end separation.
Performance: [Verse - chest voice, smooth and contemporary sung-rap], [Hook - soulful, melodic and catchy polished energy].

**Boi-1da — Dark Cinematic Boom Bap**
Style: Dark cinematic boom bap, 92 BPM, minor key cinematic, dark and cinematic with lyrical urgency, cinematic string loop or orchestral sample dominant, SP-1200 dusty sample chop, MPC3000-style hard kicks, snapping snare on 2 and 4, sparse hi-hats, dark piano accent, orchestral horn stab, Neve 1073 analog warmth, SSL punchy wide mix, cinematic sample dominant, kick hard and punching, snare snapping, tape saturation, organic analog character.
Performance: [Verse - chest voice, intense and deliberate lyrical and measured], [Hook - chest voice, dark intensity commanding authority].

**40 (Noah Shebib) — OVO Hazy Introspective R&B-Rap**
Style: OVO hazy R&B trap, 78 BPM, minor key melancholic, hazy introspection late-night melancholy with emotional weight, piano or Rhodes sample chopped melodic dominant, lush reverb string pads, hazy lo-fi vocal sample chop, TR-808 melodic sub-bass, minimal sparse trap kick, light brushed snare, sparse hi-hats, ambient texture layers, Tascam 388 tape warmth, SSL warm hazy mix, piano or Rhodes dominant, 808 melodic, lush reverb space, tape warmth, dark hazy softness.
Performance: [Verse - chest voice, introspective and melodic low and close-mic], [Hook - soulful, emotional and open melodic lift].

**Jermaine Dupri — Bounce-Heavy Atlanta Hip-Hop / Playful Soul Chops**
Style: Bounce-heavy Atlanta hip hop, 102 BPM, major key playful, party energy bounce fun with Atlanta pride, bouncy synth melody dominant playful, SP-1200 soul chop accent, TR-808 bouncy sub-bass dominant, crisp snap snare dominant, four-on-the-floor kick, hi-hat rolling tight, Yamaha DX7 synth accent, SSL 4000 warm mix, warm punchy wide mix, bouncy synth dominant, 808 bouncy and warm, snare snapping, energetic and light-footed.
Performance: [Verse - chest voice, smooth and bouncy playful cadence], [Hook - Energy: High, catchy and upbeat crowd-ready].

**Bryan-Michael Cox — Smooth Contemporary R&B**
Style: Smooth contemporary R&B soul, 88 BPM, major key smooth, smooth romance aspirational polished emotion, electric guitar smooth riff dominant, Rhodes warm chord dominant, live bass guitar groove, live drum kit brushed groove, lush string arrangement, warm brass accent, smooth vocal harmony layers, SSL 4000 warm mix, warm wide mix, guitar and Rhodes dominant, live drums warm, strings lush, smooth, polished, and rounded.
Performance: [Verse - soulful, smooth and melodic sung-rap], [Hook - soulful, emotional and open full melodic].

**Stargate — Polished Scandinavian Pop-Soul R&B**
Style: Polished Scandinavian pop-soul R&B, 100 BPM, major key bright, uplifting polished feel-good emotion, synth lead melody dominant catchy, live acoustic guitar accent, polished electronic drum kit, TR-808 or live bass accent, lush string arrangement, warm piano chord accent, smooth vocal hook layer, Neve 1073 polished mix, SSL polished wide mix, synth melody dominant, strings lush, drums crisp and bright, smooth, uplifting, and clean.
Performance: [Verse - chest voice, smooth and melodic pop-rap hybrid], [Hook - Energy: High, soulful, uplifting and catchy bright and full].

**T-Minus — Atmospheric OVO Trap**
Style: Atmospheric OVO trap, 88 BPM, minor key atmospheric, atmospheric tension OVO melancholy nocturnal, atmospheric synth pad layers dominant, melodic piano or Rhodes accent, TR-808 sub-bass dominant, sparse trap kick, light snare brush, sparse hi-hats, ambient texture and reverb wash, Tascam 388 tape warmth, SSL warm atmospheric mix, synth pads dominant, 808 melodic, ambient reverb space, tape warmth, soft atmospheric warmth.
Performance: [Verse - chest voice, low and atmospheric introspective], [Hook - soulful, emotional lift melodic controlled].

**Ye — Chipmunk Soul / Maximalist Gospel Rap**
Style: Chipmunk soul gospel rap, 90 BPM, major key soulful, triumphant maximalist spiritual energy, chipmunk soul vocal sample chopped dominant, dramatic orchestral strings and brass, Hammond B3 gospel organ, live drum kit hard kick, snapping snare, TR-808 sub-bass accent, gospel choir swells, Tascam 388 tape saturation, SSL wide dramatic mix, soul chop dominant, strings and brass triumphant, organ warm, tape saturation, maximalist and unrestrained.
Performance: [Verse - chest voice, conversational and raw emotional directness], [Hook - Energy: High, soulful, triumphant gospel energy full chest].

**The Weeknd — Dark Synth-Pop R&B / Nocturnal Cinematic**
Style: Dark synth-pop R&B, 108 BPM, minor key nocturnal, nocturnal dark romance cinematic melancholy, analog synthesizer dominant layered, dark synth-pop drum machine, TR-808 sub-bass accent, live electric guitar dark riff, lush reverb vocal processing, orchestral string swells, arp synth texture, SSL 4000 wide mix, wide dark mix, synth dominant, drum machine punchy, strings lush, reverb space cinematic, wide cinematic reverb space.
Performance: [Verse - chest voice, smooth and melodic dark and close], [Hook - soulful, melodic and soaring emotional chest lift].

**Missy Elliott — Electronic Hip-Hop / Future Bass Funk**
Style: Electronic hip hop future bass funk, 105 BPM, minor key futuristic, futuristic funk energetic experimental, futuristic electronic synth dominant unpredictable, TR-808 or electronic drum machine rhythmic dominant, electronic bass line, glitchy FX and sound design, reversed and chopped vocal samples, electronic clap and snap, arp synth texture, Neve 1073 futuristic mix, SSL wide punchy mix, electronic elements dominant, FX sound design present, rhythmically layered, futuristic and nontraditional.
Performance: [Verse - aggressive, rhythmically inventive staccato], [Hook - Energy: High, energetic and catchy commanding].

**Dr. Luke — Polished Pop-Rap / Anthemic Electro-Trap**
Style: Polished pop-rap anthemic electro, 115 BPM, major key anthemic, anthemic polished hit-driven energy, anthemic synth lead dominant catchy, electronic drum kit polished, TR-808 sub-bass accent, synth bass drop, layered vocal hook, bright piano accent, build-up electronic FX, SSL 4000 polished mix, polished wide mix, synth lead dominant, drums crisp and punchy, build-up dramatic, bright and clean, commercial ready.
Performance: [Verse - chest voice, pop-rap hybrid melodic and punchy], [Hook - Energy: High, anthemic and catchy full and bright].

**Louis Bell / Cirkut — Polished Pop-Rap Crossover / Melodic Trap**
Style: Polished pop-rap melodic trap crossover, 135 BPM, minor key contemporary, contemporary polished emotional crossover hit-driven, piano melody accent emotional, contemporary trap drum programming, TR-808 sub-bass dominant, synth pad layers, melodic vocal hook layers prominent, crisp snare and hi-hat rolls, arp synth texture, SSL 4000 clean polished mix, polished wide mix, piano melodic present, 808 smooth and dominant, vocal melody up front, clean and polished, polished clean texture.
Performance: [Verse - soulful, melodic and contemporary sung-rap], [Hook - Energy: High, soulful, emotional and catchy full vocal].

**DJ Toomp — T.I. Signature Atlanta Trap / Authoritative Southern Swagger**
Style: Authoritative Atlanta southern trap, 136 BPM, minor key commanding, street authority cinematic Bankhead swagger earned menace, eerie synth loop or soul organ riff dominant, TR-808 thundering sliding sub-bass dominant, hard snapping trap snare on 2 and 4, punching trap kicks, Hammond B3 gospel organ accent, SP-1200 soul chop texture, hi-hat rolls tight and syncopated, sparse brass stab, Neve 1073 warm punchy mix, SSL punchy hard mix, 808 thundering and dominant, organ warm and present, snare snapping bright, syncopated hi-hats locked, tape saturation, clean low-end separation.
Performance: [Verse - aggressive, rapid-fire syncopated pocket locked to hi-hat, velocity shifts hard before punchline, Atlanta twang natural and controlled], [Hook - Energy: High, chantable authority chest dominant commanding and simple].

**DJ Toomp — T.I. Crossover / Polished Trap-Soul (Paper Trail era)**
Style: Polished trap-soul crossover, 108 BPM, minor key aspirational, triumphant ambition street made polished earned swagger, lush string arrangement swell, gospel organ accent, SP-1200 soul chop or live piano melodic lead, TR-808 warm sub-bass dominant, crisp trap drum kit, snapping snare, rolling hi-hats, live bass guitar groove accent, Neve 1073 polished warm mix, SSL wide polished mix, strings lush and present, 808 warm and dominant, snare snapping, piano or soul chop melodic, tape warmth, polished clean texture.
Performance: [Verse - chest voice, deliberate and measured authoritative drawl, punchline drop at bar 12-16], [Hook - Energy: High, anthemic and chantable full chest crowd-ready].
