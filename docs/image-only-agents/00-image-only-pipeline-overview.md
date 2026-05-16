# Image-Only Pipeline Overview

This documents the NB2 image-only prompt generation path.

In `nb2` mode, the app runs three prompt agents:

1. Scene Architect
2. Stylist
3. Cinematographer

The Video Director does not run for image-only output. The final result is a structured `image_prompt` object per scene, then the app flattens that object into a generation prompt using the Nano Banana Pro 7-part structure.

## Runtime Flow

1. `runPipeline()` receives the user's creative brief.
2. Scene Architect creates scene frameworks.
3. Stylist adds subject expression, wardrobe, shoes, jewelry, and headwear.
4. Cinematographer adds action framing, lighting, camera, background, film stock, mood, composition, palette, and negative prompt.
5. `mergeByIndex()` combines the three agent outputs into final scene cards.
6. `flattenImagePrompt()` assembles the structured object into the final prompt text.
7. `/api/generate-image` sends the assembled prompt to the image model.

## Final Prompt Structure

The final image-generation prompt is assembled in this order:

1. Subject
2. Action
3. Setting
4. Composition
5. Lighting
6. Style
7. Constraints

Earlier sections carry more prompt weight. The agents are separated so each one controls only its own layer of the final image.

## Code References

- Pipeline: `agents/pipeline.js`
- Scene Architect: `agents/scene-architect.js`
- Stylist: `agents/stylist.js`
- Cinematographer: `agents/cinematographer.js`
- Frontend prompt flattener: `js/app.js`
- Server image endpoint: `server.js`
