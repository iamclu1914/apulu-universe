# Social Scene Presence + Clothing Graphics Clarity Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix NB2 image prompts so the subject feels embedded in social scenes with real people around him, and brand logos/graphics on clothing are described in ways that render cleanly without distortion.

**Architecture:** Five targeted string edits inside the `buildPromptSystem` function in `index.html`. All changes are additions or replacements to the NB2 guidelines block — no logic changes, no new files, no backend changes. The LLM applies the new rules conditionally based on reading the user's scene description.

**Tech Stack:** Plain HTML/JS — no build step, no framework. Edit `index.html` directly and test in browser.

> **Line number note:** Tasks 1 and 2 are replacements (same number of lines — no line number drift). Task 3 inserts a new line after line 1647, shifting all subsequent lines by +1. Tasks 4 and 5 reference line numbers **after** Task 3's insertion (i.e., what was line 1651 becomes 1652, what was line 1653 becomes 1654). Execute tasks in order.

---

## Chunk 1: Clothing Realism + Background Figures + Social Body Language

### Task 1: Extend the Clothing Realism Rule (line 1630)

**Files:**
- Modify: `index.html:1630`

The existing clothing realism rule ends with `"bomber worn open over a tucked ribbed tank."` Append the new clothing graphics guidance immediately after that sentence, on the same line, before any newline.

- [ ] **Step 1: Locate line 1630**

Find this exact text:
```
- Clothing realism: describe garments using silhouette, drape, and fabric weight — NOT fine surface patterns, small text logos, or intricate embroidery (these cause distortion). Use solid colorways or simple large-scale design elements. Specify fit precisely: "relaxed double-knee cargo pants sitting low on the hips." When layering, describe how garments interact physically, e.g. "bomber worn open over a tucked ribbed tank."
```

- [ ] **Step 2: Replace with extended version**

Replace the entire line with:
```
- Clothing realism: describe garments using silhouette, drape, and fabric weight — NOT fine surface patterns, small text logos, or intricate embroidery (these cause distortion). Use solid colorways or simple large-scale design elements. Specify fit precisely: "relaxed double-knee cargo pants sitting low on the hips." When layering, describe how garments interact physically, e.g. "bomber worn open over a tucked ribbed tank." When a garment has a brand logo, text, or graphic design, describe it as a bold, single-color, large-scale, graphically simple mark only — never fine script, multi-color layered graphics, intricate embroidery, or detailed pattern fills, as these always distort in render. Describe a logo as a clean flat mark: "a clean white Palace box logo centered on the chest," "a bold red Trapstar star mark on the left breast." For pattern-heavy brands (Wacko Maria, Kapital, Needles, Engineered Garments), describe the pattern as a bold large-scale simplified version: "oversized two-color Hawaiian print" not "intricate floral embroidery with fine line detail." The brand name informs silhouette and colorway; its graphic element must appear only in the simplest, boldest form NB2 can execute without distortion.
```

- [ ] **Step 3: Verify the edit**

Confirm all three of the following:
1. Line 1630 ends with the exact phrase `simplest, boldest form NB2 can execute without distortion.`
2. Line 1630 contains the Palace box logo example: `"a clean white Palace box logo centered on the chest"`
3. The surrounding lines are unchanged — line 1629 ends with `Never dress the artist in something forgettable or generic.` and line 1631 starts with `- Scene consistency:`

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat: extend clothing realism rule with render-safe brand graphics guidance"
```

---

### Task 2: Replace the Background Figures Rule (line 1646)

**Files:**
- Modify: `index.html:1646`

The existing background figures rule at line 1646 is removed entirely and replaced with the new "People in frame" depth layering rule. The `- Background depth of field:` rule at line 1633 is **not touched**.

- [ ] **Step 1: Locate line 1646**

Find this exact text:
```
- Background figures: people in the background must be doing what people in that location actually do — fans watching the game, pedestrians walking past, patrons at tables. Background figures should never look directly at the camera, never be posed artificially, and must be described as diverse in appearance. Always describe them as softly blurred and incidental, not sharp or prominent.
```

- [ ] **Step 2: Replace with the new People in frame rule**

Replace the entire line with:
```
- People in frame: when the scene includes other people, use depth layering to make the subject feel physically embedded rather than isolated. Three tools — (1) FOREGROUND PRESENCE: a partially visible figure, shoulder, arm, or back between the lens and the subject, softly blurred, signals the subject is inside a space with people, not performing in front of one; (2) EDGE FIGURES: people partially entering the frame at the left or right border, naturally cut off the way real crowds work — never fully posed, just the natural overflow of a populated space; (3) DIFFERENTIAL SHARPNESS: the subject is the sharpest and most lit element in the frame, background and foreground figures fall off through depth of field or motion blur, preserving his visual prominence while making the social environment feel alive and real. Background figures must be doing what people in that location actually do — fans watching the game, pedestrians walking, patrons at tables — diverse in appearance, never looking directly at the camera, never artificially posed.
```

- [ ] **Step 3: Verify the edit**

Confirm all four of the following:
1. Line 1646 now starts with `- People in frame:`
2. The string `Background figures:` no longer appears anywhere in the file (search the entire file to confirm)
3. Line 1633 (`- Background depth of field:`) is unchanged — it still starts with `- Background depth of field: describe background elements as naturally out of focus`
4. Line 1647 (`- Pose physics:`) is unchanged immediately after line 1646

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat: replace background figures rule with depth layering people-in-frame rule"
```

---

### Task 3: Add Social Body Language Rule (after line 1647)

**Files:**
- Modify: `index.html:1647`

A new line is inserted immediately after the pose physics rule at line 1647. This is an insertion (not a replacement), so all lines after 1647 shift by +1. Tasks 4 and 5 use line numbers that account for this shift.

- [ ] **Step 1: Locate line 1647**

Find this exact text:
```
- Pose physics: all body positions must be gravity-consistent and physically natural. Seated poses should name contact points (back against seat, feet flat on floor, elbows resting on knees). Standing poses need grounded weight distribution. No floating, hovering, or anatomically impossible angles.
```

- [ ] **Step 2: Insert the social body language rule immediately after it**

After the pose physics line, insert a new line:
```
- Social body language: when the scene description includes other people — crew, a girl, friends, a crowd, a party — the subject's pose and expression must reflect genuine social awareness. He is not squared to the camera in isolation. His body may be angled toward someone. His head may be slightly turned. His expression reacts to the moment — not a neutral editorial pose, but the face of someone inside a situation with other people present. Eye contact can be directed at someone in the scene rather than the lens. The social geometry of who he's with must be physically readable in how he stands, sits, or moves. When the scene is solo, apply standard pose physics rules unchanged.
```

- [ ] **Step 3: Verify the edit**

Confirm the order of lines is now:
1. `- Pose physics: all body positions must be gravity-consistent...` (unchanged)
2. `- Social body language: when the scene description includes other people...` (new)
3. `- Order: subject appearance and outfit (including shoes and accessories) →...` (previously immediately after pose physics — confirm it still immediately follows the new insertion)

To verify item 3: search for the text `- Order: subject appearance` and confirm it appears on the line directly after the new social body language line.

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat: add social body language rule for scenes with other people"
```

---

## Chunk 2: Photographer Extensions + Negative Prompt

> **Line number reminder:** Task 3 inserted one new line after line 1647. What was line 1651 is now line 1652. What was line 1653 is now line 1654. Tasks 4 and 5 use the post-insertion line numbers. If you are unsure, search for the anchor text rather than relying on line numbers.

### Task 4: Extend Five Photographer Descriptions (now line 1652)

**Files:**
- Modify: `index.html:1652` (was 1651 before Task 3 insertion)

The photographer reference rule is a single long line. Five photographers get a social scene extension appended as a second sentence immediately after their existing description. DANA SCRUGGS, QUIL LEMONS, and KERBY JEAN-RAYMOND are not changed.

- [ ] **Step 1: Locate the photographer reference line**

Search for this anchor text (do not rely on line number alone):
```
- Style anchor and photographer reference: anchor each scene to ONE specific photographer's visual language
```

- [ ] **Step 2: Replace with the extended version**

Replace the entire photographer reference line with:
```
- Style anchor and photographer reference: anchor each scene to ONE specific photographer's visual language — rotate across scenes for variety. CAM KIRK → warm, intimate, golden-toned hip-hop portraits, rich shadow detail, subjects feel at ease and powerful simultaneously. In social scenes: warm amber room light wraps multiple people, physical closeness is real — arms around shoulders, leaning in, bodies sharing the same space naturally, other faces visible and warm-lit without competing with the subject. TYLER MITCHELL → soft natural light, airy and dream-like, pastel tones, feels like editorial fashion shot in a real moment. In social scenes: the subject is not always facing the lens — body turned toward someone, caught mid-exchange, the social relationship between people in the frame legible and genuine. RENELL MEDRANO → high-contrast gritty urban realism, flash-assisted, raw texture, unfiltered street energy. In social scenes: high-contrast flash, people partially enter the frame at edges, some cut off by the border — the subject is embedded in the scene's energy, not elevated above it, figures in the foreground may be partially visible between the lens and the subject. GUNNER STAHL → direct flash candid style, hard light, honest and unposed, feels like a real behind-the-scenes moment elevated to editorial. In social scenes: direct flash freezes the subject sharp while people around him are mid-motion, slightly blurred from movement — he is commanding and still inside a moving crowd, the flash creating a halo of stillness around him while the scene breathes around it. DANA SCRUGGS → dramatic and powerful, deep shadows, strong silhouettes, subjects command the frame with presence. SHANIQWA JARVIS → documentary intimacy, soft grain, subjects caught between posed and candid, warm and human. In social scenes: multiple people share the frame naturally the way a real moment looks — nobody posed, everyone present. QUIL LEMONS → painterly and ethereal, soft diffused light, subjects feel otherworldly yet grounded. KERBY JEAN-RAYMOND → bold editorial fashion photography, strong graphic composition, color-forward. State the photographer reference as a mood description woven into the scene, e.g. "the image carries Cam Kirk's warmth — rich amber shadows and an intimate connection between subject and camera" — never just a name tag at the end.
```

- [ ] **Step 3: Verify the edit**

Confirm all of the following:
1. CAM KIRK, TYLER MITCHELL, RENELL MEDRANO, GUNNER STAHL, and SHANIQWA JARVIS each have an `In social scenes:` sentence immediately after their base description
2. DANA SCRUGGS, QUIL LEMONS, and KERBY JEAN-RAYMOND have no `In social scenes:` addition
3. The closing instruction (`State the photographer reference as a mood description woven into the scene`) is unchanged at the end of the line
4. The phrase `In social scenes:` appears exactly 5 times in the file

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat: add social scene extensions to five photographer references"
```

---

### Task 5: Extend the Negative Prompt List (now line 1654)

**Files:**
- Modify: `index.html:1654` (was 1653 before Task 3 insertion)

Eight new entries are appended to the existing negative_prompt list. All existing entries remain intact.

- [ ] **Step 1: Locate the negative_prompt line**

Search for this anchor text:
```
cloned background figures, inconsistent shadows, wrong season clothing
```

- [ ] **Step 2: Append new entries**

Replace that ending segment with:
```
cloned background figures, inconsistent shadows, wrong season clothing, cloned foreground figures, repeated foreground silhouettes, distorted text on clothing, warped logos, melted graphics, blurred print on fabric, illegible embroidery, multi-color layered graphic on clothing
```

> Note: `cloned background figures` already existed — it must be retained. `cloned foreground figures` is new and distinct. Both must be present after this edit.

- [ ] **Step 3: Verify the edit**

Confirm all of the following:
1. Both `cloned background figures` AND `cloned foreground figures` are present as separate entries
2. All eight new entries are present: `cloned foreground figures`, `repeated foreground silhouettes`, `distorted text on clothing`, `warped logos`, `melted graphics`, `blurred print on fabric`, `illegible embroidery`, `multi-color layered graphic on clothing`
3. The existing entries `illegible text on clothing` and `distorted patterns` are still present (unchanged)

- [ ] **Step 4: Final smoke test**

Open the app in a browser. Generate a scene using this description:
> "Vawn at a house party in someone's living room, laughing with his crew, late night"

Check the generated image prompt for:
- Social body language cues (body angled, not squared to camera, or eye contact toward someone in the scene)
- Foreground presence, edge figures, or differential sharpness language
- A photographer's `In social scenes:` behavior described in the output
- Clothing graphics described as bold, single-color, large-scale marks if any brand with a logo is mentioned

Then generate a solo scene:
> "Vawn on a rooftop at golden hour, alone"

Confirm:
- No foreground figures appear in the prompt
- Pose language is standard editorial (no social body language cues)
- Background depth of field language is present (from the unchanged line 1633 rule)

- [ ] **Step 5: Commit**

```bash
git add index.html
git commit -m "feat: extend negative_prompt with clothing graphics and foreground figure guards"
```
