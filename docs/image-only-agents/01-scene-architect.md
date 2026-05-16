# Scene Architect

## Job

The Scene Architect designs the image set at the scene-framework level. It turns the user's brief into real lifestyle moments that can later be styled and photographed.

It does not write wardrobe, camera, lighting, film stock, or final prompt prose.

## Input

Receives:

- User creative brief
- Mode, usually `nb2` for image-only
- Requested scene count
- Optional anchor context
- Optional location memory
- Optional active style preset

## Output

Returns one object per scene with:

- `index`
- `style_world`
- `style_world_name`
- `location`
- `time_of_day`
- `season`
- `narrative_beat`
- `subject_action`

## What It Decides

- Which style world applies to each scene
- Where the scene happens
- What time of day and season the scene uses
- What emotional or narrative beat the scene carries
- What the subject is physically doing

## Key Rules

- Build a cohesive artist lifestyle feed, not unrelated fashion concepts.
- Use 2-3 compatible style worlds unless the user asks for broad variety.
- Treat style worlds as wardrobe flavor, not separate universes.
- Every scene must feel like a real caught moment.
- `subject_action` must be an activity or micro-motion, not a static pose.
- Avoid repeating phone-checking, skyline-gazing, and abstract introspection.
- Keep locations grounded in Vawn's Brooklyn/Atlanta cultural context unless the user directs otherwise.
- If a shirt reference is uploaded, include natural scenes where the shirt can be seen without staged product-pose language.

## Downstream Dependency

The Stylist depends on these scene briefs to choose wardrobe that fits the assigned style world, season, setting, and action.

The Cinematographer later depends on `subject_action` as the core action for the frame.

## Code Reference

`agents/scene-architect.js`
