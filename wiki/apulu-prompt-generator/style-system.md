# Apulu — Style System

**Source file:** `Style System.md`
**Compiled:** 2026-04-07

---

## Summary

The style system governs all fashion decisions in the Apulu pipeline. Implemented in `agents/stylist.js`, it's based on the **VAWN Style Reference v2** — a personal style guide for the [[vawn-project/overview|Vawn]] artist. It defines 7 style worlds, a color palette, shoe color-lock rules, and rotation logic for headwear and jewelry.

## The 7 Style Worlds

Each scene gets one style world assigned by the Scene Architect. No two scenes share the same world (for sets ≤7).

| # | Name | Key Brands | Palette |
|---|------|-----------|---------|
| 1 | Quiet Luxury / Old Money | Loro Piana, Brunello Cucinelli, Zegna, The Row | Oat, ecru, chalk, camel, dove grey |
| 2 | European High Fashion Edge | Rick Owens, Ann Demeulemeester, Yohji Yamamoto | Charcoal, dark olive, oxblood, matte black |
| 3 | French Luxury Streetwear | Celine, AMI Paris, Casablanca, Jacquemus Homme | Ivory, cobalt, terracotta, champagne |
| 4 | Streetwear | Needles, Wacko Maria, Kapital, Corteiz, Palace | Indigo, rust, forest green, acid yellow |
| 5 | UK Grime / London Underground | Corteiz, Trapstar, Palace, Martine Rose | Acid yellow, royal blue, fire red |
| 6 | Americana Workwear Elevated | Carhartt WIP, Engineered Garments, RRL | Tan, forest green, burgundy, faded navy |
| 7 | Sport Luxury / Athlete Fashion | Represent, Rhude, Fear of God Athletics | Cobalt, cream, cardinal, jet black |

**World assignment heuristic:** Luxury penthouse → W1, Brutalist gallery → W2, Parisian terrace → W3, Street corner → W4, London estate → W5, Workshop/barn → W6, Gym/arena → W7.

## Shoe Color-Lock Rule

**The shoe's dominant color MUST match the shirt's dominant color.** No exceptions.

- **Approved brands:** Air Jordan 1–14 (no mids), Nike Air Max, Nike Dunks, New Balance (990 series, 9060, 550, 2002R, 1906R), Adidas Samba OG, Salomon XT-6 (Worlds 4/6/7 only), Timberland Classic 6-Inch Premium
- **Color lookup table:** 16 shirt color families mapped to specific colorway names (e.g., orange shirt → AJ1 "Shattered Backboard", AJ13 "Starfish", Dunk Low "Syracuse")

**Common mistakes:**
- Champagne/ecru/ivory → always Cream row, NEVER Gold/Yellow
- AJ14 "Ginger" → Camel/Tan row, NEVER Gold/Yellow
- Taupe Haze → only for olive/army green shirts

## Key Styling Rules

- **Brand no-repeat** — no clothing brand appears more than once across all scenes
- **Shirt color no-repeat** — dominant color family must differ every scene
- **Shoe model no-repeat** — no shoe model + colorway reused
- **Headwear rotation** — 20 types (fitted cap, snapback, bucket hat, beanie, fedora, etc.), never repeat within a generation
- **Jewelry rotation** — 11 structurally simple pieces (Cuban link, watch, bangles, etc.), never repeat within a generation
- **No hair descriptions** — hair controlled by reference image
- **Clothing realism** — silhouette + drape + fabric weight; no fine logos or text

## Key Takeaways

- 7 distinct style worlds ensure visual variety across scenes
- Shoe color-lock is the most complex rule — a 16-row lookup table mapping shirt colors to specific colorways
- All rotation rules (brand, color, shoe, headwear, jewelry) prevent repetition within a single generation
- The style system is tightly coupled with the [[ui-modes-and-pipeline|Stylist agent]] in the pipeline
- Winter outerwear must come from the scene's assigned world brand list
- The style system is a constraint system analogous to the [[vawn-mix-engine/levels-and-gain-staging|Mix Engine's level targets]] — both enforce hard rules that produce consistency (see [[cross-topic/creative-pipelines-and-prompt-engineering|Creative Pipelines Comparison]])
