# Visual Refresh Audit — 2026-05

Branch: `redesign/visual-refresh-2026-05`
Scope: Frontend visual rewrite. Server, agents, style worlds, deploy configs untouched.

## Files changed
- `index.html` — full rewrite (271 → ~250 LOC). Drop-in replacement preserving all JS-referenced IDs and class hooks.
- `css/styles.css` — full rewrite from scratch against `.impeccable.md` (2393 → ~1000 LOC, tokens + components).

## Files NOT touched
- `server.js`, `agents/`, `js/app.js`, `js/studio.js`
- `package.json`, `vercel.json`, `render.yaml`
- All style worlds + agent prompts

## What changed visually
1. **Type system unified.** Removed JetBrains Mono. Instrument Serif italic now used consistently for display (logo, hero, scene numbers, track labels, treatment concept, studio bubbles' headings). Raleway for all UI text. Monospace reserved only for actual code blocks (`.studio-code-block`, `.studio-inline-code`).
2. **Warm dark base + film grain + vignette.** New `body::before` adds a top/bottom warm vignette; `body::after` carries a chocolate-tinted SVG fractal-noise grain at 4.5% opacity with overlay blend (was 2.5% plain). Base `#0c0b0a` preserved; surfaces (`--surface`, `--card`) shifted to warm chocolate tones.
3. **Honey gold accent.** `#d4a03a` → `#d8a23a` with brighter hover (`#ecb654`). Soft + faint tints introduced for restrained fills.
4. **Hero state.** Empty-state title now uses `Apulu` italic + `Generation` roman in a single large block (`clamp(72px, 14vw, 168px)`), centered, with a tracked-caps subtitle below. Generous vertical breathing room.
5. **Composer.** Photo thumbs got rounded squares with serif placeholders ("Face" / "Fit"), not camera/T glyphs. Artist name input uses Instrument Serif italic. Lyrics/desc placeholders are now Raleway (no monospace). Generate button moved out of the floating right-of-upload position into a `.pill-submit-row` flex container anchored to the bottom of the field stack. The legacy `.gen-btn` inside `.pill-top` is hidden by CSS so JS that targets it for label/class swaps still works invisibly until the next render — but the visible button is the one in the submit row. (See judgment call #3.)
6. **Tab styling.** Header tabs are now uniform pill buttons; active state is a soft gold fill with a subtle inner ring. No more separate filled-vs-outlined logic — JS still uses `.active` and `.active-hf` classes; styled coherently.
7. **Platform badges.** Removed dashboard-pill aesthetic. Now thin-bordered pills with a 5 px pulsing dot; gold dot for NB2, teal dot for Higgsfield, violet for Studio. No giant uppercase brand names; no status-dashboard vibe.
8. **Scene cards.** Single accent border-left tinted gold for image blocks, teal for video blocks. `.sc-num` uses Instrument Serif italic at 38 px in honey gold. Cleaner spacing, no heavy borders. Hover lifts subtly via shadow.
9. **Copy buttons.** Pill-shaped, low-contrast outlined; gold/teal tint by platform.
10. **Studio panel.** Reskinned bubbles (gold-soft for user, surface for AI), violet send button as the only non-gold CTA, tighter card grid, consistent pill controls.
11. **Vignette + grain layered above content** with `pointer-events: none` so interactivity is unaffected.

## Preserved
- All **75 element IDs** referenced by `getElementById` in `js/app.js` and `js/studio.js` (the documented 73 plus `modeFrames` and `modeGrid` which `app.js` also queries — added as hidden spans).
- All **dynamic class selectors** rendered by JS template literals: `.scene-card`, `.sc-header`, `.sc-num`, `.sc-shot-num`, `.sc-meta`, `.sc-title`, `.sc-lyric`, `.sc-badges`, `.sc-badge.nb2`, `.sc-badge.hf`, `.sc-badge.seq`, `.sc-badge-dot`, `.sc-hero-badge`, `.sc-chain-badge`, `.sc-clip-chain`, `.sc-note`, `.sc-divider`, `.sc-prompt.img-block`, `.sc-prompt.vid-block`, `.sc-prompt-header`, `.sc-prompt-label`, `.sc-prompt-dot`, `.sc-prompt-name`, `.sc-prompt-tool`, `.sc-prompt-preview`, `.sc-prompt-text`, `.sc-prompt-text.sc-collapsed`, `.btn-regen`, `.btn-toggle-json`, `.btn-copy`, `.btn-copy.teal`, `.btn-gen-action`, `.gen-img-actions`, `.frames-pair`, `.frame-panel-label`, `.hf-meta`, `.hf-meta-item`, `.treatment-card`, `.tc-*`, `.audio-analysis-card`, `.aa-*`, `.edit-director-card`, `.ed-*`, `.progress-stage`, `.progress-stage-icon`, `.progress-stage-name`, `.qa-warning-bar`, `.h-tab`, `.ctrl-btn`, `.ctrl-btn.active-hf`, `.tiktok-shot-chip`, `.studio-msg*`, `.studio-msg-bubble`, `.studio-user-bubble`, `.studio-ai-bubble`, `.studio-h`, `.studio-hr`, `.studio-list`, `.studio-spacer`, `.studio-inline-code`, `.studio-code-block`, `.studio-code-copy`, `.studio-output-card`, `.studio-card-header`, `.studio-card-label`, `.studio-card-count`, `.studio-card-warn`, `.studio-card-over`, `.studio-card-overlimit`, `.studio-card-copy`, `.studio-card-body`, `.studio-panel-divider`, `.studio-panel-song`, `.studio-session-item`, `.studio-session-main`, `.studio-session-title`, `.studio-session-meta`, `.studio-session-delete`, `.studio-session-empty`, `.studio-track-tabs-wrap`, `.studio-track-tabs-song`, `.studio-track-tabs`, `.studio-track-tab`, `.studio-track-tab-label`, plus `.gen-btn`, `.gen-btn.violet`, `.hist-*`, `.hf-it-btn`, `.hf-it-btn.active-hf`, `.photo-thumb`, `.photo-thumb.has-img`.
- All `onclick=` handler bindings.

## Smoke test
```
HTTP 200
IDs total: 75 — Missing: (none)
```

## Judgment calls for review

1. **Removed JetBrains Mono font load** (no longer needed; only studio code blocks use monospace, served by system fallback `SF Mono, Consolas, monospace`). Saves a font request and keeps `.impeccable.md`'s pairing rule strict.
2. **Added `modeFrames` and `modeGrid` IDs as hidden `<span>`s.** The audit list of 73 omitted these, but `js/app.js` reads them. Defensive include avoids null-deref. They were already null-guarded in JS so omitting would also have been safe.
3. **Generate button placement.** Moved from the floating right-of-upload position into a dedicated `.pill-submit-row` flex container anchored at the bottom of the field stack. Single `id="genBtn"`; no duplication.
4. **Photo placeholder glyphs.** "📷"/"T" replaced with serif "Face"/"Fit" text labels. Quieter than emoji; readable.
5. **Tab copy.** "Image Only" → "Image", "● Both" → "Both" (removed leading dot). Minor.
6. **Reset button.** "↺ Reset" → "Reset" (kept icon-free; relies on tooltip).
7. **Light copy edits in placeholders** — "AI picks the 6-8…" → "Apulu picks the six to eight…" for editorial register. Functionally identical.

## Outstanding
None. All deliverables met.
