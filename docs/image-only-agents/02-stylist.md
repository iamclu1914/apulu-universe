# Stylist

## Job

The Stylist turns each Scene Architect brief into a complete outfit and subject presentation. It controls wardrobe realism, style-world consistency, shoe matching, headwear, jewelry, and expression/gaze.

It does not write locations, lighting, camera, background, film stock, or final prompt prose.

## Input

Receives:

- Scene Architect output
- Optional wardrobe memory
- Optional style-world memory
- Optional jewelry memory
- Optional headwear memory
- Optional uploaded shirt reference analysis

## Output

Returns one object per scene with:

- `index`
- `Subject`
- `MadeOutOf`
- `headwear`
- `jewelry`

## Subject Field

`Subject` contains expression and gaze only.

It should not describe:

- Face
- Skin tone
- Hair
- Build
- Clothing

The reference image handles identity.

## MadeOutOf Order

The `MadeOutOf` array must always use this order:

1. Top / shirt
2. Bottom / pants / trousers
3. Outerwear / jacket
4. Headwear / hat
5. Footwear / shoes

This order is required by downstream code. The pipeline maps the first four slots into wardrobe memory as shirt, pants, jacket, and hat.

## What It Decides

- Subject expression and gaze direction
- Shirt/top
- Pants/bottoms
- Outerwear
- Headwear or no headwear
- Exact footwear model and colorway
- Jewelry or accessory choice
- How cohesive the whole set feels as an artist wardrobe

## Key Rules

- Build a recognizable artist uniform, then vary it subtly.
- Keep outfits wearable and repeatable, not costume-catalog variety.
- Use at most one named clothing brand per scene outside footwear and uploaded shirt references.
- If an uploaded shirt reference exists, it must be the visible top garment in every scene.
- Shoe color must match the shirt's dominant color using the approved lookup table.
- Do not repeat exact shoe model plus colorway across the set.
- Rotate headwear widely; do not describe hair.
- Avoid fine logos, intricate embroidery, or small text that image models distort.
- Use memory blocks as hard exclusions unless all options are exhausted.

## Downstream Dependency

The Cinematographer receives the outfit and must photograph it naturally. The final `image_prompt.Subject` and `image_prompt.MadeOutOf` come from this agent.

## Code Reference

`agents/stylist.js`
