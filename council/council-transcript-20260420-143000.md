---
type: council-transcript
date: 2026-04-20
topic: Suno stem cleanup + mixing tool
---

# Council Transcript — 2026-04-20 14:30

## Original Question (verbatim)

> I use Reaper as my DAW. I use stems from Suno. Research on cleaning AI artifacts (16kHz shimmer, resonance suppression, UVR5 re-separation, Adobe Enhance Speech, subtractive EQ, dynamics restoration, drum replacement). I use iZotope (RX, Nectar 4, Neutron 5, Ozone 12, Tonal Balance 3). Research from Young Guru, Leslie Brathwaite, iZotope docs.
>
> Goal: near-professional mixing of Suno tracks. No mastering (handled externally).
>
> I want to create a program or app that allows me to accomplish this.
>
> council this

## Framed Question

Should Ricardo build a new program/app to clean and mix Suno stems in REAPER using his iZotope plugin chain, OR extend the existing tooling he already has, OR neither?

**Load-bearing context:**
- He already owns `vawn-mix-engine` — a 5-stage REAPER hip-hop mixing pipeline via reapy. Signal chain already wired: Relay → RX 11 → Nectar 4 / Neutron 5 → Ozone 12 + TBC3. Supports `ai_source: "suno"` per-song YAML config. Known issues documented: param map drift, Mix Assistant crushing bass, pre-master LUFS gain staging, Sculptor scooping bass fundamentals.
- He ALSO has `Ai Mix Engineer/backend` — a separate FastAPI agent-orchestrator project with Claude/Gemini clients, mix history models, session tracking. Parallel system addressing a similar problem.
- Running a live label (Apulu Records) with Vawn as artist. Production is event-driven (A&R → Suno → Onyx mix → master externally → release).
- Mix rules codified from real REAPER session on 2026-04-16 (`wiki/vawn-mix-engine/mix-rules.md`).
- Research Ricardo is citing introduces new techniques NOT currently in the engine: UVR5 re-separation, dedicated 16kHz AI-shimmer cleanup, Soothe2-style resonance suppression, drum replacement from Splice samples, expander/transient-shaper for restoring dynamics.

**What's at stake:** A third mix system would split effort three ways. But the research he's citing would genuinely improve output if integrated somewhere. The question is where, not whether.

## Context files consulted

- `C:\Users\rdyal\Apulu Universe\CLAUDE.md` (project instructions)
- `C:\Users\rdyal\Apulu Universe\wiki\vawn-mix-engine\mix-rules.md` (first 80 lines)
- Glob of `projects\vawn\**\*.py` (confirmed both mix systems exist)

---

## The Five Advisors

### 1. The Contrarian

This fails the same way your last two mix systems are failing — you keep building scaffolding around a source-quality problem that no signal chain can fix.

You already have vawn-mix-engine with documented bugs actively being patched (param map drift, Mix Assistant crushing bass on Suno bass stems, LUFS gain staging, Sculptor scooping fundamentals). You ALSO have Ai Mix Engineer/backend — a FastAPI service with its own agent orchestrator. Neither has hit "near professional." Building a third tool is how you end up with three half-broken systems and no finished mixes.

The bottleneck is not software architecture. It's decisions that require ears in the loop: which Suno generation is worth mixing vs. regenerating, when to re-separate with UVR5 vs. use Suno's native stems, when to replace AI drums with Splice samples vs. treat them, whether the 16kHz fizz on THIS particular track warrants a low-pass or just a dynamic EQ. No program automates taste.

Second failure: iZotope's AI Assistants (Vocal Assistant, Mix Assistant) were trained on studio recordings, not AI-generated audio. You're stacking one AI (Suno) → another AI (iZotope Assistants) → your custom logic. That chain is unpredictable by design. More automation layers on top makes it worse, not better.

Third: your "no mastering" constraint means the mix has to do 100% of the perceptual work. That's backwards from how professional workflows run — mixing gets you 90%, mastering closes the last 10%. If your mastering service is a LANDR-style pass-through, it's doing nothing. You're asking the mix to carry a burden it was never designed to carry.

### 2. The First Principles Thinker

The question as posed is wrong. "Build a program to mix Suno stems" presumes the answer is code. Strip that assumption out.

What's actually being solved? You want Suno tracks to sound near-professional. That problem decomposes into three independent layers that need separate diagnosis:

**Layer 1 — Source quality at ingest.** Suno's native stem separation leaves bleed (drums in vocals, vocals in instrumental). No mix chain fixes bad source. Question: are Suno's native stems acceptable, or do they need UVR5 re-separation first?

**Layer 2 — AI-specific artifact profile.** Shimmer at 16kHz, metallic resonances at specific frequencies, over-compressed dynamics. This is a **restoration** problem, not a mixing problem. It happens BEFORE Nectar or Neutron touches the audio.

**Layer 3 — Musical mixing.** Balance, EQ, compression, spatial placement. This is what vawn-mix-engine already does.

Your current engine collapses Layers 2 and 3 into one pass (Nectar/Neutron don't care that the stem has AI shimmer — they mix it as if it's a studio recording). That's why the output feels "off" despite correct mixing. You don't need a new program. You need a Stage 0 — restoration — inserted before Stage 1 in vawn-mix-engine.

The right question: "How do I add an AI-restoration pre-stage to vawn-mix-engine that uses RX 11 (De-click, De-hum, Spectral Repair), optionally UVR5 re-separation, and writes decision metadata per stem?" That's a one-week extension, not a new architecture.

### 3. The Expansionist

You're thinking about this at 10% of its real size.

A tool that mixes your own Suno tracks? Fine. A tool that mixes every indie artist's Suno tracks? That's a product. Every bedroom producer using Suno has the same problem you do — AI shimmer, muddy low-end, crushed dynamics, separation bleed. Most of them don't own iZotope. Most of them don't use REAPER. Most of them will never figure out a five-stage processing chain. You already have one.

Package it. "SunoFix for REAPER" ships as a Reaper extension that installs your processing templates, runs your restoration chain, and outputs mix-ready stems. $49 one-time, $9/month with updates as Suno versions change. Every Suno user is a potential customer; Suno has millions of users.

The bigger vision: Apulu Records isn't just a label, it's the reference implementation for how AI music gets professionally produced. You have Paperclip (agent orchestration), vawn-mix-engine (REAPER automation), Ai Mix Engineer backend (agent reasoning), research pipelines, marketing dispatcher. Nobody else has this stack. The category doesn't exist yet — "AI music production infrastructure" — and you're 18 months ahead of where the major labels will be forced to go.

10x version: skip REAPER dependency entirely. Build a standalone web app. Suno stems in → UVR5 re-separation in cloud → iZotope-inspired processing via open-source equivalents (or licensed iZotope Relay engine if you can get that deal) → mix-ready stems out. Every Suno track on Earth passes through your pipe. That's not a mix tool. That's infrastructure.

### 4. The Outsider

I don't know what Suno is. I don't know what REAPER is. I don't know why AI music sounds different from non-AI music. I've never heard of iZotope. So when you say you want a program for "near-professional mixing" — professional compared to what?

A radio pop song? A Kendrick Lamar record? A SoundCloud indie release? An Ariana Grande single? These sound nothing like each other. "Professional" isn't a single target. Which specific song, played back to back against your Suno track, makes you say "this is the gap I want to close"?

Second thing I'm confused about: you said mastering is handled by another service. In every audio production workflow I've ever heard described, mixing is step one and mastering is step two, and they interact. So if your mix doesn't sound "near professional" to you — how do you know that's a mix problem and not a mastering problem? Have you taken the EXACT same stems, had a human engineer mix them, run them through your mastering service, and compared to your current output? Because if a human mix through the same mastering service also fails to sound professional, the mastering service is the weak link and no mix tool fixes it.

Simple question that nobody's asked: what specifically sounds wrong to YOU right now? "Near professional" is vague. "My 808s sound like cardboard compared to Metro Boomin" is specific. "My vocals sound thin compared to J. Cole" is specific. Start there. The answer depends on which.

### 5. The Executor

No program this month. This week:

**Monday:** Pick one recent Vawn track you've already mixed with vawn-mix-engine. Bounce four versions from the same stems:
1. Current engine output (your baseline)
2. Same, but with manual RX 11 De-click + De-hum + 16kHz low-pass on every stem BEFORE the engine runs
3. Same stems run through UVR5 (Demucs v4 model) FIRST to re-separate, then current engine
4. Same stems with manual drum replacement (Splice kick/snare on the drum bus), then current engine

**Tuesday:** Send all four to your mastering service, unchanged processing on their end. Listen on three systems (studio monitors, AirPods, phone speaker). Rank them.

**Wednesday:** Make a single decision based on what won:
- If #2 won → add a `stage_0_restoration` to vawn-mix-engine. One Python function wrapping RX 11 Standalone via command-line. Update YAML schema with `restoration: {de_click: true, de_hum: auto, low_pass_hz: 16000}`. One day of work.
- If #3 won → UVR5 re-separation becomes a pre-pipeline step. Write a wrapper that calls UVR5 CLI on ingest.
- If #4 won → you need a drum-replacement layer. Add Splice sample library integration or manual drum-bus replacement template.
- If #1 won → the problem isn't processing. It's the Suno source material. Decision: regenerate or accept.

**Thursday/Friday:** Ship whichever won. Run the next five Vawn tracks through it.

No SaaS. No new app. No scope expansion. One test, one week, one decision, one PR into vawn-mix-engine.

---

## Peer Review (anonymized)

**Mapping:** A = Outsider, B = Executor, C = Contrarian, D = First Principles, E = Expansionist

### Review by Advisor (Contrarian, reviewing)

**Strongest:** B. Concrete experimental design, actionable in a week, produces a falsifiable decision at the end. The kind of thing that actually ships.

**Biggest blind spot:** E. Assumes there's a paying market for a Reaper extension aimed at Suno users. Most Suno users are hobbyists who aren't going to install REAPER, let alone pay for a plugin for it. The "SaaS" pivot at the end contradicts the Reaper-extension premise in the same response. And nothing in the current behavior of Suno's user base suggests they'll pay to mix properly — they'd rather generate 50 more songs.

**What all five missed:** Nobody addressed whether iZotope's AI Assistants are actively working AGAINST Suno stems. Mix Assistant on bass stems already sets Compressor 1 Band 1 at 4-7:1 and enables Sculptor "Reduce Boxiness" — the mix-rules doc literally says this crushes bass fundamentals. The AI Assistants are trained on studio recordings. They're making wrong decisions about AI-generated audio. The whole engine might need a "no AI Assistant" mode with fixed presets calibrated to Suno artifact profiles.

### Review by Advisor (First Principles, reviewing)

**Strongest:** D. Only response that properly decomposes the problem into independent layers (source quality, artifact restoration, musical mixing). Without this isolation, every other recommendation is guessing which layer is the bottleneck.

**Biggest blind spot:** E. Productization is in a different zip code from the actual question. User said "I want to create a program" — not "I want to build a SaaS for the Suno ecosystem." Jumping from personal workflow tool to category-creating infrastructure is a non-sequitur.

**What all five missed:** The "no mastering" constraint is load-bearing and nobody stress-tested it. If his mastering service is Master Channel AI or a LANDR-style pass-through, it's doing minimal processing and the mix needs to carry 100%. If it's a human engineer, they're compensating for mix flaws silently. The recommendation changes substantially depending on which it is. Ricardo should answer "what does my mastering service actually do" before optimizing what hits its input.

### Review by Advisor (Expansionist, reviewing)

**Strongest:** E. Only response pointing at real leverage. Everyone else is optimizing a personal workflow for a label with one artist. That's small thinking. The AI music production infrastructure market is being created right now; whoever builds the reference tooling wins the category.

**Biggest blind spot:** A. "What does professional mean" is a legitimate question but it's a stall. You can keep asking clarifying questions forever and never build anything. Paralysis through scope-clarification is how projects die.

**What all five missed:** The timing. AI music is about to go through the same transition that beat production went through 2010-2015 — from "toy producers use this" to "labels are forced to adopt this or lose." Ricardo is 6-12 months before the inflection point, not 2 years. Treating this as personal workflow optimization misses that he's sitting on a defensible position in a category that hasn't been claimed yet.

### Review by Advisor (Outsider, reviewing)

**Strongest:** A. Asks the only question that determines whether any of this work matters — what's the actual target, and how do you know the mix is the problem and not the mastering? Every other response is downstream of assumptions that haven't been verified.

**Biggest blind spot:** C. Correctly identifies failure modes but offers no path forward. "Your source is bad, iZotope Assistants work against AI audio, your mastering does all the work" — that's three problems and zero solutions. Doomsaying isn't the same as analysis.

**What all five missed:** Nobody asked about Ricardo's time budget. If he has 2 hours/week for this, C's "can't be automated" is load-bearing — focus on fixing one track manually. If he has 20 hours/week, E's "build a product" becomes viable. The answer genuinely depends on resources and nobody asked.

### Review by Advisor (Executor, reviewing)

**Strongest:** B. Only response that produces a decision by end of week. Everything else is abstract or months-out.

**Biggest blind spot:** D. Diagnostically correct — you do need to isolate layers — but delivers no timeline. "Isolate three root causes" can take a month of careful testing. That's how projects die.

**What all five missed:** Nobody said: "first, run the last 10 tracks you've already mixed through vawn-mix-engine, rank the failure modes by frequency, and fix the top 2 issues first." The fastest path isn't new architecture or new programs. It's iteration on what exists. The engine is documented as having known issues (param map drift, Sculptor on bass, LUFS staging). Fix those, re-run a backlog of 10 tracks, see if the gap closes. No new code until the current bugs are dead.

---

## Chairman Synthesis

### Where the Council Agrees

- **Don't build a new program.** The existing vawn-mix-engine already implements what Ricardo is describing. A third mix system (after vawn-mix-engine AND Ai Mix Engineer backend) fractures effort. (Contrarian, First Principles, Executor converge.)
- **AI stems need restoration BEFORE mix processing.** RX 11 should run before Nectar/Neutron touches the audio. This is a Stage 0 insertion, not a rearchitecture. (First Principles, Executor explicit; Contrarian implicit.)
- **Source material is a real bottleneck.** UVR5 re-separation deserves a pilot test. Suno's native stem separation leaves bleed. (Contrarian, First Principles, Executor converge.)
- **Test before building.** A/B a manual version against the engine output before writing code. (Executor, First Principles, Outsider converge.)

### Where the Council Clashes

- **Scale of ambition.** Expansionist pushes productization (SunoFix SaaS). Everyone else says fix personal workflow first. The Expansionist's argument has merit as a second-order move IF personal workflow hits the bar — but right now Ricardo's own tracks don't hit the bar, so productizing a broken process is premature. The dissent is noted but not adopted.
- **Diagnostic depth vs. speed.** First Principles wants three-layer decomposition before any action. Executor wants one experiment this week. These are sequential, not opposed — the Executor's four-version bounce test IS the first-principles decomposition, just run as a falsifiable experiment rather than abstract analysis.

### Blind Spots the Council Caught

- **The mastering service is an unexamined variable.** If it's Master Channel AI / LANDR pass-through, the mix has to do 100% of the perceptual work. If it's a human engineer, they're silently compensating. The recommendation changes depending on which it is. Ricardo needs to answer "what does my mastering service actually DO" before optimizing the mix for its input. (Caught in First Principles peer review.)
- **iZotope AI Assistants may be working against Suno stems.** Mix Assistant is documented as setting 4-7:1 compression ratios on bass stems and crushing fundamentals via Sculptor. These tools were trained on studio recordings. A "no AI Assistant" mode with fixed Suno-calibrated presets might outperform the current "let the Assistant decide" chain. (Caught in Contrarian peer review.)
- **"Near-professional" was never defined concretely.** Which specific reference track is Ricardo trying to match? "Sounds like J. Cole's Atlanta" vs "sounds like a polished SoundCloud indie release" are different targets with different tools. (Caught in Outsider peer review.)
- **Time budget wasn't discussed.** The right recommendation depends on whether Ricardo has 2 hrs/week or 20 hrs/week. Nobody asked. (Caught in Outsider peer review.)
- **The 10-track backlog audit was skipped.** Before new architecture, run the last 10 mixes through the existing engine and rank failure modes. Fix the top 2 issues first. Iteration over construction. (Caught in Executor peer review.)

### The Recommendation

**Extend vawn-mix-engine. Do not build a new program. Do not productize yet.**

Specifically, and in this order:

1. **Diagnostic week first.** Run Executor's four-version bounce test on one recent Vawn track. Baseline, +RX restoration, +UVR5 re-sep, +drum replacement. Send all four through your mastering service. Rank on three playback systems.
2. **Simultaneously, answer the mastering question.** What does your mastering service actually do? If it's MCA or LANDR, the mix is doing 100% of the work. If it's a human, they're compensating invisibly. This answer reshapes everything.
3. **Based on #1's winner, make ONE engine extension:**
   - If RX restoration wins → add Stage 0 `restoration` to vawn-mix-engine with `de_click`, `de_hum`, `low_pass_hz` YAML fields.
   - If UVR5 wins → add a pre-pipeline re-separation wrapper.
   - If drum replacement wins → add a drum-bus-replacement template layer.
   - If baseline wins → the problem is Suno source material; workflow shifts to "regenerate until good stems, accept the rest."
4. **Audit whether iZotope AI Assistants help or hurt on Suno stems.** Mix one track with Vocal/Mix Assistant ON, one with them OFF (fixed Suno-calibrated presets). Same mastering. Compare. This has been flagged in your own mix-rules doc for weeks and never tested.
5. **Only after vawn-mix-engine reliably produces near-professional output on Vawn tracks** — revisit the Expansionist's SaaS question. Productizing a broken workflow is premature. Productizing a proven one is a genuine option.

The Expansionist's productization argument is parked, not rejected. It's a real second-order move once the core workflow is solved. Right now it's a distraction.

### The One Thing to Do First

**Bounce the four-version comparison test on "On My Way" (already configured in `config/on_my_way.yaml`) this week: baseline, +RX restoration, +UVR5 re-sep, +drum replacement. Send all four to your mastering service. Rank them.**

That one experiment tells you which of three possible engine extensions to build — and eliminates the other two. You're currently debating all three simultaneously without data.

### Confidence Note

**Medium-high** on "don't build a new program, extend vawn-mix-engine" — grounded directly in your documented codebase, mix-rules, and the existence of Ai Mix Engineer backend as a second parallel system you already haven't fully integrated.

**Medium** on the specific extension recommendation (Stage 0 restoration) — it's the most likely winner given the research you cited on AI shimmer and iZotope's design intent, but this should be proven by the four-version test, not assumed.

**Low** on specific iZotope vs. UVR5 tradeoffs on YOUR particular Suno outputs — the council is reasoning from general AI-audio principles, not direct A/B testing of your actual stems. Trust the decision framework more than any specific plugin recommendation. The four-version bounce test is the truth-teller; the council's job was to frame the experiment, not predict its winner.

**Unknown** on whether your mastering service (unnamed in the question) is doing enough work for the mix to matter — this needs answering before #3 in the recommendation.
