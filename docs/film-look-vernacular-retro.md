# Vernacular Retro Prompts for NB2 Pro

**Why this file exists:** the earlier pipeline-format prompts (`docs/film-look-pipeline-outputs.md`) spoke *technical cinematographer vocabulary* (film stock, lens, body) — NB2 Pro interprets that as color, not texture, and renders it with modern digital polish. This file rewrites the same six scenes using **vernacular stylistic retro language** the model actually recognizes — the language Gemini explicitly highlights as NB2 Pro's strength ("90s mall portrait", "grainy faded print", "80s family album").

**Key moves per prompt:**
1. Open with the retro instruction *first* — before subject, before scene
2. Remove "A cinematic editorial still of the subject from the reference photo" — this pushes modern polish
3. Remove the "expensive and detached" Mood grade — this pulls toward prestige-TV color
4. Use vernacular era anchors ("1978", "family album photograph", "scanned 35mm print") instead of technical specs
5. Triple down on texture words: "heavy grain", "slightly faded", "aged print", "soft focus", "imperfect"
6. Strengthen negatives: add "digital clean look, modern HDR, AI-smooth skin, clinical sharpness, oversaturated, plastic skin"

Paste each code block directly into NB2.

---

## 1. 1970s WARM FILM PHOTOGRAPH (Portra-adjacent) ✅ test this first

```
A grainy warm film photograph from a 1978 family album, scanned from a 35mm color print that has aged gently over time. Slight color fade in the highlights, warm golden cast throughout, soft focus across the whole frame with no digital sharpness, heavy visible film grain in every part of the image, mild chromatic aberration at the edges, subtle halation where the sunlight hits bright surfaces. The print has imperfect focus and slightly uneven exposure.

The photograph shows a Black man leaning casually against the iron railing of a Brooklyn brownstone stoop at golden hour in summer. His weight is on his right hip, his left hand rests loose at his side, his right hand holds a half-smoked cigarette at waist level between index and middle finger, a small curl of smoke visible rising past his jaw. His gaze drifts to the far end of the block, jaw relaxed, caught mid-exhale. He wears an ecru linen camp-collar shirt open at the neck, wide-leg oat wool trousers with a hard crease, worn wheat-colored Timberland boots creased at the vamp, and a thick gold Cuban link chain resting flat against his chest.

Clinton Hill brownstone rowhouses recede down the block behind him, wrought-iron fences and mature sycamore trees softly dissolved in the shallow focus, the sky above a faded amber-rose gradient. Long warm directional shadow stretches across the stoop behind him from the low sun raking across the brick facade. The vintage print has the natural soft character of late-70s American street photography — Gordon Parks' observational warmth, or a family archive photo pulled out of a shoebox.

Rendered as a scanned vintage color print, grain structure visible across skin and sky alike, soft edges, warm shadows not cool shadows, slightly lifted blacks, no modern clarity, no digital cleanup. The photograph feels overheard rather than posed.

Negative: cartoonish, illustrated, digital clean look, modern HDR, AI-smooth skin, clinical sharpness, oversaturated, plastic skin, sculpted studio lighting, teal shadows, prestige TV color grade, magazine editorial polish, cinematic still, Sony A7R V look, clean digital edges, distorted hands, extra limbs, face warping, warped clothing, morphed fabric, floating jewelry, warped logos, hat brim touching.
```

---

## 2a. 1996 BED-STUY STOOP — SATURDAY AFTERNOON (FULL-FRAME, NO BORDERS) ⭐ test this

```
A 1990s photograph shot on Kodak Gold 200 35mm consumer film, scanned full-frame with no border, no frame, no polaroid edge — just the photograph itself filling the entire image. The scan shows fine visible film grain across the whole frame, a warm golden cast with slight magenta bias from aged film, flat consumer-film tonality with gentle rolled highlights, slightly soft focus from a point-and-shoot plastic lens, mild natural vignette darkening the corners. Not cinematic, not staged — this is a candid snapshot from the middle of a real afternoon.

A young Black man sits on the top step of a Bed-Stuy brownstone stoop in summer, weight settled back on his palms, legs extended down the steps in front of him, head turned slightly off-camera mid-laugh at something somebody just said off-frame. Natural warm afternoon sun lights his face. He wears a vintage Polo Sport cream cotton crewneck sweatshirt with a small red-and-blue flag graphic on the chest, faded indigo Levi's 501 jeans worn loose, and clean white and black Air Jordan 12 "Taxi" sneakers. A thick gold Cuban link chain rests against the sweatshirt. A black New York Yankees fitted cap sits on his head, worn forward.

Behind him, the brownstone's wrought-iron railing frames the camera-right side of the frame, and the block recedes — a parked maroon mid-90s Buick sedan at the curb, a corner bodega visible a half-block down with a faded green-and-red sign, mature sycamore trees stretching over the street, a few neighbors on their own stoops softly out of focus. The sidewalk has a faded hopscotch grid chalked in. Pale summer blue sky with heat haze.

Rendered in the style of Jamel Shabazz's early-NYC hip-hop documentary photography crossed with Ricky Powell's corner-of-the-block candor — warm, unstaged, authentic. Grainy film character, aged print color response, documentary rather than editorial.

Negative: polaroid, polaroid border, white matte border, instant film frame, white edges, photo border, scalloped edge, date stamp, timestamp, orange LED date, text overlay, watermark, caption, cartoonish, illustrated, digital clean look, modern HDR, AI-smooth skin, clinical sharpness, cinematic still, magazine editorial, Sony A7R V look, clean digital edges, prestige TV color grade, teal shadows, sculpted studio lighting, overprocessed, 4K detail, contemporary fashion, distorted hands, extra limbs, face warping, warped clothing, morphed fabric, floating jewelry, warped logos, hat brim touching.
```

**Changes from the first draft:**
- Removed the date stamp line entirely
- Removed the "fingerprint smudge" and "age-yellowing" signifiers (too gimmicky)
- Added *"scanned full-frame with no border, no frame, no polaroid edge — just the photograph itself filling the entire image"* as positive instruction
- Added explicit negatives: *polaroid, polaroid border, white matte border, instant film frame, white edges, photo border, scalloped edge, date stamp, timestamp, orange LED date, text overlay, watermark, caption*
- Kept everything that was working — grain, warm cast, soft focus, Shabazz/Powell reference, period wardrobe, block details, candid body language

---

## 2b. 1990s NIGHT FLASH DISPOSABLE (true 90s street feel)

```
A 1990s point-and-shoot disposable camera photograph from a Bed-Stuy laundromat at 11 at night. Scanned from a consumer color negative print, slight magenta color cast, slightly overexposed highlights from the hard on-camera flash, flat fluorescent fill in the background, visible grain throughout, soft plastic-lens focus, hard shadow cast behind the subject on the wall from the direct flash. An orange date stamp in the bottom-right corner reads "05 18 97". This is a casual snapshot, not a posed photo.

A Black man leans his lower back against the front edge of a running front-load washing machine, weight on his left hip, right heel kicked up against the machine's base, a mesh laundry bag slumped at his feet. His head is tilted back a few degrees mid-laugh, eyes glancing off-frame camera-right at someone unseen. He wears a burnt-orange rugby shirt with a thick cream horizontal stripe across the chest, cream wide-leg track pants with burgundy side piping, a black fitted cap worn forward, and grey sneakers. A thin gold rope chain sits on his neck.

Behind him, a row of running washing machines, a folding counter stacked with neatly folded whites, and a change machine on the back wall, all lit by overhead fluorescent tubes. The photograph has the casual unstaged character of a 90s disposable — somebody grabbed the camera and took the shot while hanging out.

Rendered as a scanned Kodak Funsaver disposable camera print, 32mm fixed plastic lens, ISO 400 consumer film, hard flash shadow, slightly blown highlights on skin, fingerprint smudge vignette in one corner, amateur framing, authentic 90s consumer photo tonality.

Negative: cartoonish, illustrated, digital clean look, modern HDR, AI-smooth skin, clinical sharpness, cinematic still, magazine editorial, professional lighting, teal shadows, Sony A7R V look, polished composition, prestige TV color grade, distorted hands, extra limbs, face warping, warped clothing, morphed fabric, floating jewelry, warped logos, hat brim touching.
```

---

## 3. CINESTILL 800T NIGHT STREET (halated night)

```
A grainy cinematic 35mm film photograph shot on tungsten-balanced night film, heavy red halation rings blooming around every neon and streetlight source, strong color bleed, magenta cast in the midtones, deep cyan shadows, visible coarse film grain across the whole frame, imperfect focus, slight softness characteristic of pushed low-light film. Scanned from a negative, not digitally cleaned.

A Black man stands three feet out from beneath the yellow awning of an Atlanta bodega at 2 in the morning in autumn, breath visible as vapor in front of his face in the cold, weight evenly distributed, right hand holding a phone face-down at waist level, left hand buried in his coat pocket. His head is turned toward the street, eyes tracking a passing car off-frame, jaw set. He wears a dark olive waffle-knit thermal henley with two buttons undone at the neck, faded indigo selvedge denim breaking once over the boot, a dark olive waxed-cotton chore coat worn open with the collar turned up against the cold, and scuffed black nubuck Timberland boots. A leather-strap vintage watch sits on his left wrist.

A single sodium-vapor streetlamp overhead casts deep warm orange on the wet sidewalk. Yellow bodega signage spills from camera-left creating intense red halation bleeding into his left cheekbone and jacket shoulder. Car headlights off-frame-right add a cool cyan rim on his right side. Across the street a closed auto-body shop with chain-link and graffiti, a single parked sedan at the far curb softly out of focus. Wet pavement reflects the neon.

Rendered in the style of a CineStill 800T 35mm night frame — tungsten color, halation blooming, grain structure dominant, cinematic low-light character. The image has the restless quiet of a Gregory Crewdson still pulled out of a real street corner.

Negative: cartoonish, illustrated, digital clean look, modern HDR, AI-smooth skin, clinical sharpness, no grain, no halation, daylight balance, clean highlights, prestige TV teal-and-orange, Sony A7R V look, distorted hands, extra limbs, face warping, warped clothing, morphed fabric, floating jewelry, warped logos, hat brim touching.
```

---

## 4. 80s KODACHROME TRAVEL SLIDE (saturated daylight)

```
A 1980s Kodachrome 64 color slide photograph, scanned from the mounted transparency. Signature Kodachrome color response — deep saturated reds, warm golden yellows, crisp cyan sky, hard-edged shadows with defined high-contrast falloff, punchy mid-range, slight green shift in foliage. Fine tight film grain, slight directional sharpness from a manual-focus prime lens, authentic slide-film transparency tonality. NOT desaturated, NOT faded — this is vivid saturated daylight film.

A Black man sits on the hood of a sun-bleached burgundy 1984 sedan parked at the edge of an empty Bed-Stuy asphalt lot at midday in summer. His legs are extended out toward the camera, arms crossed loose across his chest, weight resting back on his palms pressed to the hood, shoulders relaxed, head tilted slightly, a faint smirk directed at the lens. He wears a cobalt cotton short-sleeve polo with a ribbed collar, cream drawstring track pants with a single black side stripe, and clean grey sneakers. A single diamond stud earring sits in his left ear.

The empty asphalt lot has faded yellow parking-stripe paint, a chain-link fence at the rear, a brick warehouse wall in the background, and a bright high-summer sky overhead. Direct midday sun overhead casts hard-edged shadows under the sedan and under his feet on the hood.

Rendered as an authentic 1980s Kodachrome slide scan — Jamel Shabazz's street documentary color, saturated and warm, vivid without being digitally processed.

Negative: cartoonish, illustrated, digital clean look, modern HDR, AI-smooth skin, clinical sharpness, desaturated, teal shadows, muted colors, prestige TV color grade, Sony A7R V look, clean digital edges, distorted hands, extra limbs, face warping, warped clothing, morphed fabric, floating jewelry, warped logos, hat brim touching.
```

---

## 5. 1970s SUPER 8 DUSK CINEMA FRAME

```
A 1970s Super 8 motion-picture film frame captured as a single cinema still, telecined from the original film print. Heavy organic grain structure visible across the whole image, slight gate weave, color bleed in the warm practicals, soft edges from the small 8mm frame, authentic vintage cinema tonality. Warm orange and deep teal split-tone. Imperfect focus, slight motion blur, genuine film character — NOT digital.

A Black man walks mid-stride down a narrow Atlanta alley between two low-rise cinderblock warehouses at dusk on an autumn evening, three-quarters back turned to the lens, his right hand trailing fingertips along the chain-link fence at shoulder height, left arm swinging naturally. His head is bowed a few degrees with his gaze on the pavement ahead as his weight transfers onto his right foot. He wears a charcoal wool fine-gauge mock-neck sweater with a dropped shoulder, drop-crotch black cotton trousers tapered at the ankle, an oversized black wool long coat worn unbuttoned with hems grazing mid-calf, and black nubuck Timberland boots. A polished titanium chain with a flat pendant rests beneath the mock-neck.

The sky is cerulean at dusk overhead. A single buzzing sodium-vapor alley fixture halfway down casts a pool of warm amber on the pavement he is walking into, his long shadow receding behind him. The alley is flanked by cinderblock walls, chain-link fence running along camera-right, a dumpster at the far end softly out of focus, power lines crossing the dusk sky above.

Rendered as a Super 8 frame — Roy DeCarava's jazz-quiet intimacy pulled into a warm 70s cinema palette. Grain dominant, character authentic, the image feels overheard.

Negative: cartoonish, illustrated, digital clean look, modern HDR, AI-smooth skin, clinical sharpness, no grain, clean edges, 4K detail, prestige TV color grade, Sony A7R V look, distorted hands, extra limbs, face warping, warped clothing, morphed fabric, floating jewelry, warped logos, hat brim touching.
```

---

## 6. 2000s CONTAX T2 CASTING-TAPE OVEREXPOSED

```
A 2000s fashion casting-tape photograph shot on a Contax T2 compact camera with Fuji Pro 400H film, deliberately overexposed one stop for the signature Hedi Slimane blown-highlight look. Slightly blown whites, cool green-cyan shadow bias, creamy desaturated midtones, high-key lifted exposure, very fine visible film grain, Zeiss Sonnar 38mm optical character with subtle edge falloff. Scanned from the original print. The photograph has the casual-but-deliberate casting-tape feel — almost a snapshot, but the composition holds.

A Black man sits on the top step of a Bed-Stuy brownstone stoop in direct morning summer sun, legs extended straight down the steps in front of him, left hand resting on the top step beside his hip, right hand loose on his right knee, shoulders squared to the lens but weight settled back on his left palm, a direct neutral gaze at the camera, mouth relaxed. He wears an ivory silk bowling shirt in a relaxed fit open at the collar, wide-leg cream tailored trousers with a hard crease breaking softly over the shoe, and pristine pale ivory low-profile sneakers. A simple thin gold 22-inch rope chain sits on his neck.

Direct morning sun at 25 degrees above the horizon from camera-left provides a warm directional key on his left side. Subtle reflected fill from the opposite brownstone facade bounces cool light back onto his right, with clean shadow falloff down the steps. Wrought-iron railings flank the stoop on both sides, a painted wooden door visible in the distance softly out of focus.

Rendered in the high-key Hedi Slimane Contax T2 fashion style — Fuji 400H cool pastel skin, bright exposure, minimalist composition, snapshot character.

Negative: cartoonish, illustrated, digital clean look, AI-smooth skin, clinical sharpness, underexposed, dark shadows, moody, prestige TV color grade, teal shadows, cinematic still, Sony A7R V look, distorted hands, extra limbs, face warping, warped clothing, morphed fabric, floating jewelry, warped logos, hat brim touching.
```

---

## What to test

Run prompt **#1** first. It's the closest in subject and scene to the output you already shared (Clinton Hill stoop, golden hour, cream linen, cigarette exhale). Compare side-by-side with the pipeline version you generated. The difference between the two is entirely about **which language the model hears** — vernacular retro vs technical cinematographer.

If #1 finally hits the look you want, we know the fix: rewrite the cinematographer's Mood template and opener to use vernacular retro language instead of technical camera/grade specs. That's a ~30-line change in `agents/cinematographer.js`.

If #1 still doesn't hit, we have a bigger conversation — either the target aesthetic is underspecified, or we need to look at post-process grain/halation filters (Dehancer, FilmConvert) applied after generation.
