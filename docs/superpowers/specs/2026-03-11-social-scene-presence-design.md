# Social Scene Presence + Clothing Graphics Clarity — Design Spec
**Date:** 2026-03-11
**Status:** Approved
**Scope:** NB2 image prompt system (`buildPromptSystem` in `index.html`)

---

## Problem

Two issues with generated images:

**Issue 1 — Social isolation:** The subject feels visually alone even when described amongst people. Root causes:
1. The existing "background figures" rule forces all people to be softly blurred and incidental, erasing social presence.
2. The subject's pose and expression are always solo-editorial — squared to the camera, no social awareness.
3. Compositions have no depth layering — no foreground figures, no edge figures, nothing that makes the subject feel embedded in a populated space.

**Issue 2 — Clothing graphics distortion:** Brand logos, text, and graphic designs on garments warp and distort in generated images. Root causes:
1. The existing clothing realism rule bans "small text logos" but allows "simple large-scale design elements" — the AI still attempts to render complex brand graphics.
2. The negative prompt entry ("illegible text on clothing, distorted patterns") targets the symptom but doesn't prevent the AI from describing graphics in ways NB2 can't execute cleanly.
3. Style world descriptions reference brands known for graphic-heavy designs (Palace, Trapstar, Wacko Maria, Kapital, Needles) without specifying how to describe those brand elements in render-safe terms.

---

## Solution Overview

Six targeted changes to the NB2 guidelines in `buildPromptSystem`. All rules are always present in the system prompt. The LLM applies them conditionally based on reading the user's description. No JavaScript keyword detection or UI changes required.

---

## Section 1 — Social Body Language Rule

**Placement:** New rule added to the NB2 guidelines block, after the existing pose physics rule (~line 1647).

**Rule text:**
- Social body language: when the scene description includes other people — crew, a girl, friends, a crowd, a party — the subject's pose and expression must reflect genuine social awareness. He is not squared to the camera in isolation. His body may be angled toward someone. His head may be slightly turned. His expression reacts to the moment — not a neutral editorial pose, but the face of someone inside a situation with other people present. Eye contact can be directed at someone in the scene rather than the lens. The social geometry of who he's with must be physically readable in how he stands, sits, or moves. When the scene is solo, apply standard pose physics rules unchanged.

---

## Section 2 — Per-Photographer Social Scene Extensions

**Placement:** Each extension is appended as a second sentence immediately after the existing description for that photographer in the `- Style anchor and photographer reference:` rule (~line 1651).

**Concrete example — before and after for Cam Kirk:**

*Before:*
`CAM KIRK → warm, intimate, golden-toned hip-hop portraits, rich shadow detail, subjects feel at ease and powerful simultaneously.`

*After:*
`CAM KIRK → warm, intimate, golden-toned hip-hop portraits, rich shadow detail, subjects feel at ease and powerful simultaneously. In social scenes: warm amber room light wraps multiple people, physical closeness is real — arms around shoulders, leaning in, bodies sharing the same space naturally, other faces visible and warm-lit without competing with the subject.`

**All photographer extensions (append to each):**

- **CAM KIRK:** In social scenes: warm amber room light wraps multiple people, physical closeness is real — arms around shoulders, leaning in, bodies sharing the same space naturally, other faces visible and warm-lit without competing with the subject.

- **GUNNER STAHL:** In social scenes: direct flash freezes the subject sharp while people around him are mid-motion, slightly blurred from movement — he is commanding and still inside a moving crowd, the flash creating a halo of stillness around him while the scene breathes around it.

- **RENELL MEDRANO:** In social scenes: high-contrast flash, people partially enter the frame at edges, some cut off by the border — the subject is embedded in the scene's energy, not elevated above it, figures in the foreground may be partially visible between the lens and the subject.

- **TYLER MITCHELL:** In social scenes: the subject is not always facing the lens — body turned toward someone, caught mid-exchange, the social relationship between people in the frame legible and genuine.

- **SHANIQWA JARVIS:** In social scenes: documentary intimacy, multiple people share the frame naturally the way a real moment looks — nobody posed, everyone present.

*(Dana Scruggs, Quil Lemons, Kerby Jean-Raymond: no social extension required — their existing descriptions focus on solo portraiture and do not conflict.)*

---

## Section 3 — Depth and Crowd Layering Rule (replaces existing Background Figures rule)

**Placement:** The existing `- Background figures:` rule at line 1646 is removed entirely and replaced with this rule. The separate `- Background depth of field:` rule at line 1633 is retained unchanged — it continues to govern solo-scene background blur behavior. Section 3 applies to social scenes only; line 1633 handles solo-scene DOF. The Section 3 DIFFERENTIAL SHARPNESS bullet complements line 1633's language rather than duplicating it — line 1633 describes the photographic behavior, Section 3 describes how to use it compositionally when people are present.

**Replacement rule text:**
- People in frame: when the scene includes other people, use depth layering to make the subject feel physically embedded rather than isolated. Three tools — (1) FOREGROUND PRESENCE: a partially visible figure, shoulder, arm, or back between the lens and the subject, softly blurred, signals the subject is inside a space with people, not performing in front of one; (2) EDGE FIGURES: people partially entering the frame at the left or right border, naturally cut off the way real crowds work — never fully posed, just the natural overflow of a populated space; (3) DIFFERENTIAL SHARPNESS: the subject is the sharpest and most lit element in the frame, background and foreground figures fall off through depth of field or motion blur, preserving his visual prominence while making the social environment feel alive and real. Background figures must be doing what people in that location actually do — fans watching the game, pedestrians walking, patrons at tables — diverse in appearance, never looking directly at the camera, never artificially posed.

---

## Section 4 — Clothing Graphics Rule (extends existing Clothing Realism rule)

**Placement:** Append to the existing `- Clothing realism:` rule at line 1630, after the current final sentence.

**Addition text:**
When a garment has a brand logo, text, or graphic design, describe it as a bold, single-color, large-scale, graphically simple mark only — never fine script, multi-color layered graphics, intricate embroidery, or detailed pattern fills, as these always distort in render. Describe a logo as a clean flat mark: "a clean white Palace box logo centered on the chest," "a bold red Trapstar star mark on the left breast." For pattern-heavy brands (Wacko Maria, Kapital, Needles, Engineered Garments), describe the pattern as a bold large-scale simplified version: "oversized two-color Hawaiian print" not "intricate floral embroidery with fine line detail." The brand name informs silhouette and colorway; its graphic element must appear only in the simplest, boldest form NB2 can execute without distortion.

---

## Section 5 — Negative Prompt Additions

**Placement:** Append to the existing `negative_prompt` must-include list at line 1653.

**Additions:**
`cloned foreground figures, repeated foreground silhouettes, distorted text on clothing, warped logos, melted graphics, blurred print on fabric, illegible embroidery, multi-color layered graphic on clothing`

**Notes for implementer:**
- `cloned foreground figures` and `repeated foreground silhouettes` are NEW — they guard against the new foreground depth figures introduced in Section 3. Do not confuse with `cloned background figures` which already exists in the list and must be retained.
- `distorted text on clothing`, `warped logos`, `melted graphics`, `blurred print on fabric`, `illegible embroidery`, `multi-color layered graphic on clothing` are NEW additions for Issue 2 (clothing graphics). The existing entries `illegible text on clothing` and `distorted patterns` remain in place — these new entries strengthen and extend them with more specific terms.

---

## Implementation

**File:** `index.html`
**Function:** `buildPromptSystem` (~line 1609)

**Changes (in order):**
1. Remove the existing `- Background figures:` rule at line 1646 entirely; add Section 3 "People in frame" rule in its place. Retain the `- Background depth of field:` rule at line 1633 unchanged.
2. Add the Section 1 "Social body language" rule after the pose physics rule (~line 1647)
3. Extend the following five photographers' descriptions with their social scene extensions (Section 2) — append as a second sentence immediately after each photographer's existing description. Photographers to extend: CAM KIRK, GUNNER STAHL, RENELL MEDRANO, TYLER MITCHELL, SHANIQWA JARVIS. Do NOT add extensions to DANA SCRUGGS, QUIL LEMONS, or KERBY JEAN-RAYMOND.
4. Append the Section 4 clothing graphics text to the end of the existing `- Clothing realism:` rule at line 1630
5. Append Section 5 negative prompt additions to the negative_prompt list at line 1653. See Section 5 notes for which entries are new vs. which already exist.

No UI changes. No backend changes. No new files.

---

## Success Criteria

- When the user describes the subject with other people, generated prompts include foreground depth figures, social body language cues, and photographer-specific social scene language
- When the user describes a solo scene, no change to existing behavior
- The subject remains the clear visual focal point in all social scenes
- No cloned or symmetrically repeated foreground figures appear
- Brand logos and text on garments are described in bold, single-color, large-scale terms only — no fine detail that causes distortion
- Pattern-heavy brand garments are described as bold simplified versions of their signature patterns
