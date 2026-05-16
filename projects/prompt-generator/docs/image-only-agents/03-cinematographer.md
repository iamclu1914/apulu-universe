# Cinematographer

## Job

The Cinematographer turns the scene framework and locked outfit into the visual image prompt fields. It decides how the image is arranged, lit, photographed, styled, and constrained.

It does not change the core scene brief or outfit. It must respect the Scene Architect's `subject_action` and the Stylist's wardrobe.

## Input

Receives merged Scene Architect plus Stylist data:

- Scene index
- Style world
- Location
- Time of day
- Season
- Narrative beat
- Subject action
- Subject expression/gaze
- Full outfit
- Optional angle memory
- Optional lighting memory
- Optional influence memory
- Active cinematographer style preset

## Output

Returns one object per scene with:

- `index`
- `Arrangement`
- `Lighting`
- `Camera`
- `Background`
- `FilmStock`
- `Mood`
- `Composition`
- `ColorPalette`
- `NegativePrompt`

## What It Decides

- What the subject is doing in the frame
- Shot size, angle, lens, and camera body
- Lighting source, direction, and quality
- Background and environmental detail
- Film stock and grain character
- Mood and implied narrative
- Composition and depth of field
- Color palette
- Negative prompt constraints

## Key Rules

- `Arrangement` must be built around the Scene Architect's `subject_action`.
- Default to candid, mid-action image logic before editorial posing.
- Do not repeat camera angles within a set.
- Do not repeat lighting setups within a set.
- Use only light sources that physically belong in the environment.
- Keep scene, wardrobe, season, time of day, lighting, and background consistent.
- `FilmStock` carries grain language; `Lighting` should not.
- For non-editorial retro presets, use era-appropriate camera bodies and lenses.
- Avoid banned photographer references.
- Negative prompts should be concise and high-value.
- Keep fields separate: action in `Arrangement`, setting in `Background`, composition in `Camera` and `Composition`, style in `FilmStock` and `Mood`.

## Style Preset Responsibility

The Cinematographer owns the active image style preset. Presets control:

- Opener posture
- Film stock rotation
- Color grade
- Approved visual influences
- Mood-field structure
- Extra negative-prompt guidance

Examples include:

- `vawn-editorial`
- `nineties-disposable`
- `seventies-warm-film`
- `kodachrome-daylight`
- `cinestill-night`
- `super8-dusk`
- `contax-highkey`

## Downstream Dependency

The final `image_prompt` object is assembled mostly from this agent's fields, combined with the Stylist's `Subject` and `MadeOutOf` fields and the Scene Architect's label.

## Code Reference

`agents/cinematographer.js`
