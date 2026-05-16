# Visual Refresh + Frontend Rewrite — Plan

> Scope confirmed by user: visual + frontend rewrite. Server, agents, style worlds, agent prompts, deployment config: **untouched**. Branch + PR for review.

## Constraints (from AGENTS.md / .impeccable.md)

- Plain HTML / CSS / vanilla JS only. **No build step. No framework.**
- Preserve all 73 element IDs JS depends on (see Audit below) — JS continues working unchanged.
- Preserve the 11 dynamic class selectors (`.scene-card`, `.sc-prompt-preview`, `.sc-prompt-text`, `.h-tab`, `.studio-card-copy`, `.studio-track-tab`, `.btn-regen`, `.btn-toggle-json`, `.edit-director-card`, `.audio-analysis-card`, `.progress-stage-icon`) and any others rendered by `app.js` / `studio.js`.
- Design tokens from `.impeccable.md`: warm dark `#0c0b0a`, gold `#d4a03a`, off-white text, Instrument Serif italic + Raleway, film grain overlay.
- Server.js, agents/, vercel.json, package.json deps: **DO NOT TOUCH**.

## Goals (from vision audit of live site)

1. Coherent type system (kill the monospace placeholders, unify Instrument Serif + Raleway pairing).
2. Composer that feels like a creative instrument, not a form — anchor Generate to the form, fix spacing.
3. Restore warm cinematic depth (grain, subtle warm-dark tones, restrained gold) instead of flat near-black.
4. Tighten scene cards (the product) — better hierarchy, clearer copy affordance, less chrome.
5. Eliminate dashboard-styled status pills with tiny colored dots; replace with quieter platform indicators.
6. Higher legibility — fix near-illegible placeholder/secondary text contrast.

## Out of Scope

- Server-side prompt generation logic, agent prompts, scene generation API shape.
- Style worlds catalog content.
- Deployment config (`vercel.json`, `render.yaml`).
- React/Vue/build-step migration.

## Plan

### Phase 0 — Setup
- [ ] Create branch `redesign/visual-refresh-2026-05`.
- [ ] Audit existing `index.html` end-to-end; map every JS-referenced ID to its current DOM role + placement.
- [ ] Audit `app.js` / `studio.js` rendering functions; list every class selector + DOM shape they emit (so card markup stays drop-in compatible).
- [ ] Save audit notes to `tasks/audit.md`.

### Phase 1 — Design tokens (CSS)
- [ ] New `css/tokens.css` with the `.impeccable.md` system: warm-dark palette, type scale, spacing scale, radii, shadows, motion curves.
- [ ] Replace token usage in `css/styles.css` (keep file, rewrite progressively).
- [ ] Film grain SVG/PNG overlay served as data URL on `body::after` (no extra HTTP request).

### Phase 2 — Shell (HTML)
- [ ] Rewrite `index.html` `<head>` — Instrument Serif + Raleway via `<link>` Google Fonts (existing deploy already permits external fonts; verify by checking current HTML).
- [ ] Rewrite header (wordmark, mode switcher BOTH/IMAGE/VIDEO/STUDIO, RESET) with quieter affordances.
- [ ] Rewrite composer block — keep all input IDs (`artistName`, `lyricsInput`, `descInput`, `audioFileInput`, `genBtn`, `composerPill`, mode toggles, etc.).
- [ ] Anchor `genBtn` properly within the composer instead of floating beside the upload zone.

### Phase 3 — Scene cards
- [ ] Rebuild card CSS — typography-first hierarchy, single restrained accent, one-click copy as the primary action.
- [ ] Keep all class selectors and inner data attrs the JS produces.
- [ ] Verify `app.js` `renderScenes()` still attaches without modification.

### Phase 4 — Studio mode panel
- [ ] Reskin studio panel + chat (preserve all `studio*` IDs).
- [ ] Tighten card grid in the output panel.

### Phase 5 — Verification (per workflow.md "verification before done")
- [ ] `node --test` passes.
- [ ] `node server.js` boots locally; hit `/` and confirm app loads.
- [ ] Click through: enter artist name, paste lyrics, hit Generate, confirm scenes render (with mocked or live API depending on env).
- [ ] Studio mode opens, sends a message, copies output.
- [ ] No console errors. No broken IDs (smoke test from list).
- [ ] Visual side-by-side: live site vs local; capture screenshots into `tasks/before-after/`.

### Phase 6 — PR
- [ ] Commit incrementally per phase.
- [ ] Open PR with before/after screenshots + checklist of preserved IDs.
- [ ] Surface any judgment calls (token deviations from `.impeccable.md`, anything I dropped) in the PR body for user review.

## Verification gates

Workflow.md rule 4: "Never mark a task complete without proving it works." Each Phase ends with a check, not just a code drop.

## Review section
_(filled in at end with what changed, what didn't, what's left)_

## Lessons captured
_(append to `tasks/lessons.md` after any user correction)_
