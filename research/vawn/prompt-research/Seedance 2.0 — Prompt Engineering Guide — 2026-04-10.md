---
title: "Seedance 2.0 — Prompt Engineering Guide"
date: 2026-04-10
tags: [prompt-research, seedance, ai-video, apulu-prompt-generator, production]
source: APU-10
author: Nari (Operations & Strategy)
status: active
---

# Seedance 2.0 — Prompt Engineering Guide

> [!info] APU-10
> Research deliverable for updated Seedance 2.0 prompting best practices. Compiled from official guides, community resources, and API documentation.

## What Is Seedance 2.0

ByteDance's multimodal AI video generation model. Supports text-to-video, image-to-video, video-to-video, and audio-to-video. Generates up to 2K resolution video in multiple aspect ratios, 4-15 seconds duration. Native audio generation. Reference image tagging for character consistency.

**Key differentiator**: Multi-shot timeline scripting + omni-reference system (up to 9 images, 3 video clips, 3 audio clips per generation).

---

## The 6-Step Prompt Formula

The official recommended structure. Aim for **60-100 words** — every word should serve a purpose.

```
Subject → Action → Environment → Camera → Style → Constraints
```

| Step | What to Include | Example |
|------|----------------|---------|
| **Subject** | Who/what, one primary subject | "A young woman in a black leather jacket" |
| **Action** | Movement, behavior | "walks slowly through the crowd" |
| **Environment** | Setting, atmosphere | "in a rain-soaked Tokyo alley at night" |
| **Camera** | ONE movement type | "Camera follows from behind at waist height" |
| **Style** | Lighting, mood, film look | "warm neon reflections, cinematic grain, 35mm" |
| **Constraints** | What to preserve/avoid | "smooth motion, no jitter" |

> [!warning] Word Count Matters
> Too short = missing key details. Too long = conflicting instructions. Cut filler adjectives like "beautiful" or "amazing" that don't provide actual guidance.

---

## Camera Movements — The 8 Types

**Rule: ONE camera instruction per shot.** Use pacing words (slow, smooth, gentle) instead of technical parameters.

| Movement | Effect | Best For |
|----------|--------|----------|
| **Orbit** | Circles around subject | Reveals, product shots |
| **Aerial/Crane** | High angle, descending/ascending | Establishing shots, scale |
| **Zoom** | Push in or pull out | Emphasis, dramatic reveals |
| **Pan** | Horizontal sweep | Landscapes, following action |
| **Tilt** | Vertical sweep | Architecture, full-body reveals |
| **Follow/Track** | Moves with subject | Walking scenes, chase |
| **Handheld** | Micro-wobble, organic feel | Documentary, intimate |
| **Gimbal** | Smooth stabilized motion | Cinematic, polished |

> [!tip] Rig Metaphors
> "Handheld" adds micro-wobble. "Gimbal" stays smooth. "Dolly" gives controlled linear movement. "Crane" adds vertical sweep. These rig words map to specific motion profiles in the model.

---

## Timeline Prompting (Multi-Shot)

Break the video into time segments. Each segment = one camera position + one action + one atmospheric detail.

```
[0:00-0:04] Close-up of hands on piano keys, soft overhead lighting, 
camera slowly pushes in. Warm amber tones, shallow depth of field.

[0:04-0:08] Wide shot reveals the full room — empty concert hall, 
single spotlight. Camera holds fixed framing. Dust particles in the beam.

[0:08-0:12] Medium shot from the side, the pianist closes eyes and 
leans into the music. Camera drifts right on a slow dolly. Cool blue 
fills the background.
```

> [!warning] Keep Timestamps Simple
> One camera + one action + one mood per beat. Overloaded timestamps produce chaos.

---

## Reference Images (Omni-Reference System)

Tag reference images in prompts using `@image1`, `@image2`, etc.

- **Faces**: Character consistency across shots
- **Wardrobe**: Specific clothing items
- **Set pieces**: Environment elements
- **Products**: Brand/item consistency

```
@image1 shows the character's face. @image2 is the jacket they're wearing.
The character (@image1) walks through a warehouse wearing (@image2), 
camera tracks from the side at shoulder height. Industrial lighting, 
cool blue tones.
```

**Limits per generation**: Up to 9 images + 3 video clips (15s each) + 3 audio clips (15s each) + text prompt.

---

## Image-to-Video Best Practices

When converting a still image to video:

1. **Focus on movement and camera** — the visual is already defined
2. **Always include**: "preserve composition and colors" to maintain visual consistency
3. **Describe the motion** that should happen, not the appearance (that's in the image)
4. **Start simple**: Test with 3-second clips before committing to 8+ seconds

---

## Aspect Ratios & Settings

| Ratio | Resolution | Use Case |
|-------|-----------|----------|
| **16:9** | Up to 2K | YouTube, cinematic |
| **9:16** | Up to 2K | TikTok, IG Reels, YouTube Shorts |
| **1:1** | Up to 2K | Instagram feed, social posts |
| **4:3** | Up to 2K | Classic TV, presentations |
| **3:4** | Up to 2K | Portrait social |
| **21:9** | Up to 2K | Ultra-wide cinematic |

**Duration**: 4-15 seconds per generation.

> [!note] For Vawn Content
> Social posts use **9:16** (matches our existing image pipeline). Music video work uses **16:9**. IG feed posts use **1:1**.

---

## Lighting — The Highest-Leverage Element

> [!important] If you can only add one element to improve quality, add a lighting description.

Lighting descriptions have the single biggest impact on video quality among all prompt elements.

**High-impact lighting terms**:
- "golden hour sunlight streaming through windows"
- "single overhead spotlight in darkness"
- "neon reflections on wet pavement"
- "soft diffused overcast light"
- "harsh directional side lighting"
- "warm practical lights, no fill"

---

## Common Pitfalls & How to Avoid Them

### 1. Mixing Camera + Subject Movement
**Wrong**: "The dancer spins while the camera orbits around her and zooms in"
**Right**: "The dancer spins slowly in place. Camera holds fixed medium shot."

Separate subject action from camera action. The model can't handle both being complex simultaneously.

### 2. Using "Fast"
"Fast" is the word most likely to degrade video quality. Fast camera + fast cuts + busy scene = guaranteed jitter and artifacts.

**If you need pace**: Only make ONE element fast. Keep everything else slow/smooth.

### 3. Conflicting Descriptors
**Wrong**: "A dark, moody cave with bright, sunny tropical lighting"
**Right**: Pick one atmosphere and commit.

### 4. Overloading With Adjectives
The model responds better to specific visual instructions than to stacked adjectives.
**Wrong**: "A beautiful, stunning, gorgeous, amazing sunset"
**Right**: "Orange and purple sunset, low sun angle, long shadows on the sand"

### 5. Multiple Subjects Competing
Focus on ONE primary subject per generation. Multiple characters + complex backgrounds + detailed props all compete for the model's attention.

### 6. Inconsistent Subject References in Timeline
Keep the same name/description for your subject across all timestamps. Don't call them "the woman" in shot 1 and "she" in shot 2 and "the dancer" in shot 3.

---

## Preferred Motion Words

Use these for smooth, high-quality output:

| Word | Effect |
|------|--------|
| **Slow** | Reduces speed, improves quality |
| **Gentle** | Soft, controlled movement |
| **Continuous** | Unbroken flow |
| **Natural** | Organic, realistic |
| **Smooth** | Stabilized, clean |
| **Steady** | Minimal shake |
| **Gradual** | Progressive change |

---

## Prompt Templates for Apulu Use Cases

### Music Video — Performance Shot (16:9)
```
[Subject]: Vawn (@image1) stands center frame in a dimly lit warehouse, 
wearing [outfit description].
[Action]: He delivers lyrics directly to camera with controlled intensity, 
subtle hand gestures.
[Environment]: Industrial warehouse, concrete walls, hanging work lights.
[Camera]: Slow dolly push-in from medium to close-up.
[Style]: Cinematic grain, warm tungsten key light from the left, 
cool blue fill from behind. 35mm film look.
[Constraints]: Smooth motion, steady framing, no jitter.
```

### Social Content — Mood Piece (9:16)
```
[Subject]: Urban skyline at dusk, city lights beginning to glow.
[Action]: Traffic moves slowly below, clouds drift overhead.
[Environment]: Atlanta downtown, rooftop perspective.
[Camera]: Slow pan left to right, fixed elevation.
[Style]: Golden hour fading to blue hour. Warm highlights, 
cool shadows. Shallow depth of field on foreground railing.
[Constraints]: Gentle motion only, no sudden changes.
```

### Lyric Card Animation (9:16)
```
[Subject]: (@image1) lyric card centered in frame.
[Action]: Subtle particle effects drift upward around the text.
[Environment]: Dark background with soft bokeh lights.
[Camera]: Static, locked off. No camera movement.
[Style]: Moody, atmospheric. Warm amber particles against 
cool dark background.
[Constraints]: Preserve composition and colors. Text must remain 
sharp and readable. Minimal motion.
```

---

## Integration Notes for Apulu Prompt Generator

> [!note] For Rex / CTO
> The [[Apulu Prompt Generator]] should be updated to support Seedance 2.0 prompt structure. Key additions:
> - 6-step formula as structured input fields
> - Camera movement dropdown (8 types)
> - Timeline/multi-shot editor
> - Reference image tagging (@image1, @image2)
> - Aspect ratio selector with platform presets
> - Lighting preset library

**API Access**: Available via Segmind and official ByteDance API. Supports reference image arrays with @tag notation.

---

## Core Rules — In Order of Impact

### Structure

- **Who, where, doing what, what changes, mood** — in that order.
- **≤4 story beats per generation.**
- **≤3 characters per shot, ≤5 named total.**
- **Duration must match complexity** — Seedance stretches the same content slower for longer clips, it doesn't add events.

### Language

- **Concrete visual description only** — what the camera sees.
- **No emotion labels** (`angry`, `afraid`) — describe the physical manifestation (`jaw clenches`, `hands press flat against the wall`).
- **No metaphors the lens can't render** (`the city breathes` → `steam rises from grates, traffic flows`).
- **No abstract quality words** (`breathtaking`, `haunting`) — ignored or produce generic output.

### Characters

- **Give each character a unique visual anchor on first mention** — wardrobe color, silhouette, accessory.
- **State positions and movement direction explicitly.**
- **Re-anchor positions after every cut** — Seedance has no memory between shots.

### Camera

- **One dominant camera move per shot** — compound instructions (`orbit while zooming while tilting`) confuse the engine.
- **No focal lengths above 75mm** — use shot size terms instead (choker, ECU).
- **No reflections** (mirrors, water, glass, blades) — duplicates characters unpredictably.
- **No U-turns or 180° vehicle spins** — split across two shots instead.

### What to Avoid Entirely

- `Strobing`, `step-printing`, `undercranking` — triggers global low shutter, unsalvageable.
- `Symmetrical` or `mirrored` — renders a literal mirror line down the frame.
- **Film titles** — trigger content filters. Use director names only.
- **Hidden objects** (`gun under the table`) — if the camera didn't see it, it doesn't exist.
- **Prismatic or Petzval effects** — produce artifacts, not the intended look.

### Audio

Sound is rendered. Include it — ambient, foley, dialogue delivery. **Music is post only.**

### Language of the Prompt

Always English, regardless of chat language. Dialogue defaults to English — other languages only on explicit request.

---

## Advanced Craft — Structure, Characters, Dialogue, Pacing, Presets

### Prompt Structure

- **Open with environment before character** — give Seedance a stage to place people onto.
- **End with sound** — audio cues at the end of the prompt anchor mood without competing with visual description.
- **Describe light direction and quality explicitly**, even when a preset is set — presets set the system, in-prompt description fine-tunes the shot.
- **Name what's NOT moving** as well as what is — `camera locked, only the smoke drifts` gives Seedance a contrast reference.

### Characters (Continuity & Contact)

- **Wardrobe is continuity glue** across clips — lock it on first appearance and never change it mid-sequence.
- **Physical state over emotional state** — `shirt torn at the collar, knuckles scraped` tells Seedance more than `he looks beaten`.
- If two characters are **interacting physically, describe the contact point explicitly** — `his hand grips her wrist, thumb over the pulse point`.

### Dialogue

- **Mark the power-shift line** — the moment one character gains or loses leverage. That's where Seedance needs to hold the tightest frame.
- **4–6 lines maximum at 15 seconds.**
- **Write delivery into the line** — `flat and quiet`, `through her teeth`, `almost to himself` — as physical vocal behavior, not emotion labels.

### Pacing

- **Front-load the action** — don't build to something if the duration is under 8 seconds. Start at the peak.
- **15-second clips = 3 beats minimum, 4 maximum.** Two beats at 15 seconds feels empty.
- **State what changes between the first and last frame** — if nothing changes, the clip has no arc.

### Multi-Clip Sequences

- **Last frame of clip N must be described at the top of clip N+1** — spatial re-anchor.
- **Emotional temperature moves in one direction per clip** — don't oscillate within a single generation.
- **Genre can shift between clips; visual identity (Session Lock) cannot.**

### Presets

- **DP Combo recipes are the safest starting point** — tested combinations with no internal conflicts.
- When building a custom combination, **check the conflict zones before generating** — incompatible axes waste a generation.
- **Null axes are valid** — if uncertain about a parameter, leave it null and let the engine decide rather than setting something that conflicts.

---

## Sources

- [Seedance 2.0 Prompt Guide: 50+ Examples](https://www.seedance.tv/blog/seedance-2-0-prompt-guide)
- [How to Use Seedance 2.0: Complete Guide](https://www.seedance.tv/blog/how-to-use-seedance-2-0)
- [Official Prompt Guide: 6-Step Formula + Camera Movements](https://help.apiyi.com/en/seedance-2-0-prompt-guide-video-generation-camera-style-tips-en.html)
- [Complete Prompt Engineering Playbook](https://redreamality.com/blog/seedance-2-guide/)
- [Copy-Paste Framework for Motion + Camera + Style](https://wavespeed.ai/blog/posts/blog-seedance-2-0-prompt-template/)
- [Prompt Engineering: Exact Structure for Consistent Results](https://crepal.ai/blog/aivideo/blog-seedance-2-0-prompt-engineering-guide/)
- [Timeline Prompting for Cinematic AI Video](https://www.mindstudio.ai/blog/timeline-prompting-seedance-2-cinematic-ai-video)
- [500+ Curated Prompts (GitHub)](https://github.com/YouMind-OpenLab/awesome-seedance-2-prompts)
- [Image-to-Video Without Drift](https://magichour.ai/blog/how-to-use-seedance-20)
- [Omni-Reference Control](https://blog.segmind.com/seedance-2-0-is-now-on-segmind-cinematic-ai-video-with-omni-reference-control/)
- [NxCode: Complete Guide + API](https://www.nxcode.io/resources/news/seedance-2-0-complete-guide-ai-video-generation-2026)
- [Segmind: Real-World Use Cases](https://blog.segmind.com/ai-video-generation-api-seedance-2-0-review-real-world-use-cases-2026/)
