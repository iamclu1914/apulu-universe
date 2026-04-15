# AI Short Film — Full Prompt Library

**Source:** [Higgsfield Blog](https://higgsfield.ai/blog/ai-short-film-youtube-guide)
**Compiled:** 2026-04-07

---

## Summary

A complete production guide for making a cinematic AI short film using [[Higgsfield Cinema Studio]] and [[Higgsfield Soul Cinema]]. Walks through the full pipeline: character creation, location building, scene-by-scene prompting, B-roll, and final assembly.

The example film follows two cops (Adil and Dave) through a comedy-to-surprise birthday story across three scenes.

## Production Pipeline

1. **Build characters** — Use [[Soul ID]] for facial consistency across all shots
2. **Create reference sheets** — Turnaround views (front/side/back/portrait) via [[Nano Banana Pro]]
3. **Build locations** — Generate key settings once, reference them throughout
4. **Create location reference sheets** — Architectural turnarounds for spatial consistency
5. **Write and prompt scenes** — Shot-by-shot with camera direction, duration, and dialogue
6. **Add B-roll** — Driving shots, detail close-ups, atmospheric footage

## Character Consistency

- Use [[Soul ID]] tags (`@Character-Name`) in every prompt to maintain identity
- Train Soul ID with reference images before production
- Generate a **character reference sheet** showing front, profile, back, and portrait views
- Reference sheet prompt includes: "perfect identity consistency across every panel"

## Location Consistency

- Use location tags (`@Location-Name`) to reference pre-built settings
- Generate a **location reference sheet** with wide views, angled perspectives, and detail close-ups
- Maintain architectural consistency, proportions, and lighting across panels

## Prompt Craft Techniques

### Two Prompt Modes (April 2026)

**Physics-First** (for action/VFX/spectacle scenes):
- Write what force does to a body — collisions, debris, weight, speed
- Trust Seedance 2.0's physics engine and cinematic reasoning
- "Energetic camera movements" lets the AI choose optimal camera work
- Example: *"Asteroid shower on desert while post apocalyptic mad max style cars and trucks are escaping fast from the asteroids. Asteroids hit the sand and explode in very high sand explosions. energetic camera movements. cinematic epic action."*

**Director's Upgrade** (for character/intimate/establishing shots):
- Structure: Setting → Subject → Camera (body/lens/focal/aperture) → Lighting → Style
- Acquisition context anchors the look: camera body (ARRI ALEXA 35, 70mm, 16mm), lens (Anamorphic, Cooke S4), focal length (8mm=immersive, 50mm=intimate), aperture (f/2.8=shallow, f/11=deep focus)
- Example: *"Setting: Dim apartment, warm practicals. Subject: @Adil-Cop enters slowly, shotgun raised. Camera: ARRI ALEXA 35, Cooke S4, 24mm, f/2.8. Lighting: single overhead practical, deep shadows. Style: gritty drama."*

### General Techniques (both modes)
- **Camera direction in prompt:** handheld, static, dashcam, POV, profile close-up
- **Shot duration:** specified directly (e.g., "7 seconds, handheld")
- **Aesthetic descriptors:** "DVR/security camera aesthetic, cheap wide-angle lens distortion, mild compression artifacts, low dynamic range"
- **Tonal control:** use environmental details and lighting language to set mood
- **Dialogue embedding:** character lines written directly into the prompt with speaker tags
- **Speed ramps:** "Impact" (accelerate at collision), "Bullet Time" (dilate at hit)

## B-Roll Strategies

- **Dashcam driving:** hood visible, residential street, washed-out colors, compression artifacts
- **Detail close-ups:** radio mic on uniform, shallow depth of field, film grain
- **Window shots:** side-window perspective from moving car, motion blur, documentary feel
- **Purpose:** ground the story in place, build tension, cover transitions

## Tools

| Tool | Role |
|------|------|
| [[Higgsfield Cinema Studio]] | Dialogue scenes, character acting, multi-character shots |
| [[Higgsfield Soul Cinema]] | Character generation, location generation, B-roll |
| [[Nano Banana Pro]] | Character and location reference sheets |

## Key Takeaways

- **Characters and locations first** — consistency is what makes every scene feel like the same film
- [[Soul ID]] tags are essential for maintaining character identity across shots
- Write camera direction, duration, and aesthetic style directly into prompts
- Reference sheets (character + location) are the foundation of visual cohesion
- B-roll with specific aesthetic language (dashcam, documentary, film grain) sells the genre
- Tonal shifts can be driven by prompt structure — comedy to tension via radio interruption
- The [[apulu-prompt-generator/overview|Apulu Prompt Generator]] automates this workflow — its Video Director agent outputs Higgsfield-format prompts including `camera_movement`, `start_frame`, `end_frame` (see [[apulu-prompt-generator/ui-modes-and-pipeline|agent pipeline]])
- See [[cross-topic/creative-pipelines-and-prompt-engineering|Creative Pipelines Comparison]] for how manual prompting compares to automated approaches
