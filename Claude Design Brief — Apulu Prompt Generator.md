# Claude Design Brief — Apulu Prompt Generator

Paste the sections below into claude.ai/design in this order. Sections 1–5 go as the initial project prompt. Section 6 is a checklist for you (don't paste it into Claude Design — it's your operator's manual for the setup flow).

---

## 1. What this product is

Apulu Prompt Generator is an AI-powered creative-direction tool for music video production. The primary user is Vawn — a Brooklyn-raised, Atlanta-based hip-hop artist — and his tight creative circle. They use it in focused desktop sessions to translate lyrics or descriptions into scene-by-scene image and video prompts for Nano Banana 2, Kling, and Higgsfield.

This is not a general-purpose AI tool. It is a creative instrument built for one artist's workflow. The UI should feel like a professional production suite, not a form.

Inputs: reference photo, artist name, lyrics (or free-form description), platform selection, optional audio track, style presets.

Outputs: treatment card + 6–8 scene cards, each containing an image prompt and a video prompt, plus "copy all" affordances.

Secondary surface: a Studio chat view for planning full tracks/albums via Claude Sonnet.

Tech stack (non-negotiable constraint): plain HTML/CSS/vanilla JS, served by an Express Node server. No React, no build step. The CSS uses custom properties. Any redesign must ship as HTML + CSS edits to the existing `index.html` and `css/styles.css`.

Live URL: https://apulu-prompt-generator.vercel.app/

---

## 2. Brand & aesthetic direction (already established)

Voice: Authoritative but understated. The interface does not explain itself. No hand-holding, no marketing copy, no unnecessary labels. Quiet confidence.

Aesthetic: Dark, editorial, cinematic. Warm-tinted darks (chocolate/espresso, never slate or charcoal). Gold as the primary accent. Teal and violet as secondary platform indicators. Warm off-white text. No pure black, no pure white.

Typography already in use:
- Instrument Serif (italic) — display, logo, empty-state title
- Raleway 300–800 — all UI
- JetBrains Mono — code/prompt display
Labels use very small sizes (8–9px) with heavy letter-spacing (1.2–4px), uppercase.

References: Runway, Pika — dark AI creative tools, but with more warmth and personality. Anti-references: generic AI tools (cyan-on-dark, purple gradients, ChatGPT-wrapper aesthetic), toy apps (rounded pastels), corporate dashboards, cluttered interfaces.

Film grain overlay at 0.025 opacity stays. It adds analog warmth.

---

## 3. Existing design tokens — enforce these, do not invent new ones

```css
/* Base surfaces — warm, not cold */
--bg: #0c0b0a;
--surface: #141312;
--raised: #1e1d1b;
--card: #181716;
--border:    rgba(240,220,180,0.04);
--border-hi: rgba(240,220,180,0.08);

/* Accents — role-coded */
--gold: #d4a03a;  /* primary / Nano Banana 2 */
--gold-bright: #e8b44a;
--gold-dim: rgba(212,160,58,0.07);
--teal: #1cb899;  /* Nano Banana platform active */
--teal-dim: rgba(28,184,153,0.07);
--violet: #9b6dff; /* Higgsfield platform active */
--violet-dim: rgba(155,109,255,0.07);

/* Text — warm off-white scale */
--text: #ede8e0;
--text-mid: #a89e93;
--text-dim: #6d6459;

/* Status */
--red: #d94535;
--green: #1a8c52;

/* Radii */
--radius-sm: 6px; --radius-md: 10px; --radius-lg: 14px;

/* Spacing */
--sp-xs:4 --sp-sm:8 --sp-md:16 --sp-lg:28 --sp-xl:48 --sp-2xl:72 (px)

/* Motion — exponential deceleration, never bounce */
--ease-out: cubic-bezier(0.16, 1, 0.3, 1);
--dur-fast: 150ms; --dur-base: 220ms; --dur-slow: 320ms;

/* Shadows — warm-tinted (chocolate, not pure black) */
--shadow-sm: 0 2px 8px rgba(20,14,8,0.32);
--shadow-md: 0 4px 16px rgba(20,14,8,0.36);
--shadow-lg: 0 8px 32px rgba(20,14,8,0.34);
--shadow-xl: 0 24px 72px rgba(14,10,6,0.62);
```

Color-role discipline: gold = primary accent and Nano Banana badge. Teal = "Nano Banana platform active" in the platform toggle. Violet = Higgsfield platform / Higgsfield badge. Don't use all three at once in the same surface — it competes visually.

---

## 4. Surface inventory — what exists today

**Header (52px tall):** Instrument Serif italic logo in gold → separator → output-mode tabs (Both / Image Only / Video / Studio, 9px uppercase tracked labels, active = gold-dim pill) → platform badges (pulsing dot, gold for NB2, violet for Higgsfield, teal for Claude Sonnet in Studio mode) → Reset button.

**Canvas (flex, overflow-scroll, 320px bottom padding to clear composer):**
- Empty state: huge Instrument Serif italic "Apulu Generation" at 7% opacity, 9px uppercase tracked subhead "Photo · Lyrics · Generate"
- Loading state: 28px spinning gold ring + uppercase "Finding key moments..."
- Progress bar: stage-by-stage generation progress with cancel
- Results: sticky results bar (scene count + track label + copy-all buttons) → treatment card → QA warnings → scenes grid

**Studio view (separate route):** Chat messages + textarea input bar + Send / New Session / Sessions / Copy Last buttons. Optional output panel showing track cards with copy-all. Mobile bottom sheet for tapped track block. Sessions modal for history.

**Bottom composer pill (fixed bottom):** Photo avatar thumb (with edit/delete overlay) + pill fields containing: artist name input, lyrics textarea, Higgsfield extras (Track vs Description toggle, video style select [hybrid/narrative/performance/abstract], audio upload block, description textarea, Expand Idea button).

---

## 5. Where to push — the actual creative direction

These are the leverage points. Don't polish chrome; rethink the hero surfaces.

**The composer pill is too dense.** It carries photo + artist + lyrics + mode toggle + style select + audio upload + description + Expand Idea button. For a "creative instrument" vision, it reads as a form. Explore: progressive disclosure, modal states for Higgsfield extras, or a two-row pill where advanced inputs only surface when the platform is selected. Goal: feel like a console, not a questionnaire.

**Scene cards are the product.** Users spend 90% of their time reading, comparing, and copying scene prompts. That surface needs the most love. Explore: typographic hierarchy between image prompt and video prompt, clearer scene-number treatment, copy affordance that doesn't require a separate button, hover states that reveal rather than decorate.

**Studio is a distinct mode and should feel like it.** Currently it shares the same chrome with different content. Explore whether Studio should feel like stepping into a different room — darker, more focused, less platform-indicator real estate since the platforms don't apply there.

**Empty state is subtle to the point of invisible.** "Apulu Generation" at 7% opacity looks refined but offers zero guidance. Keep the restraint, but give first-time users a clearer signal without adding copy.

**Header has four different purposes competing** — output mode, studio toggle, platform indicators, reset. Audit whether all four need equal weight at all times.

Preserve: the token system, the film grain, the exponential ease-out, the uppercase-tracked microtype language, the warm darks.

---

## 6. Your operator's checklist — don't paste this into Claude Design

### Before opening claude.ai/design
- If you're on an Incognito, Guest, or enterprise-managed Chrome window, close it and open a regular Chrome window. Tab groups need to work.
- Confirm you're signed into claude.ai with your Max account.

### In claude.ai/design
1. **Create a new project.** Name it "Apulu Prompt Generator — redesign."
2. **Paste sections 1–5 above as the initial prompt.**
3. **Use the web capture tool** on `https://apulu-prompt-generator.vercel.app/` — capture the landing / empty state first, then after pasting lyrics capture the results state, then capture the Studio view. This gives Claude Design real component references instead of mockup-ing blind.
4. **(Optional) Upload the codebase.** Point at `G:\My Drive\Apulu Prompt Generator\index.html` and `G:\My Drive\Apulu Prompt Generator\css\styles.css`. Claude Design will auto-build a design system from them — verify the tokens it inferred match section 3 before iterating.
5. **First ask:** "Redesign the bottom composer pill to feel like a creative instrument, not a form. Keep the existing design tokens. The platform is plain HTML/CSS — no React, no build step. Show three directions." Three directions > one "best answer" — you want optionality.
6. **Iterate surface by surface** in this order: composer pill → scene cards → Studio view → empty state → header cleanup. Don't try to redesign everything at once.
7. **When a direction locks in, export the handoff bundle.** Then hand that off to Claude Code (or bring it to me) to implement against the real `index.html` / `css/styles.css`. Claude Design does not ship production code directly for a plain-HTML app — the handoff step is mandatory.

### What to watch out for
- Claude Design is in research preview. If it generates React components, reject them — you're not on React.
- If it invents new color tokens, reject them. Section 3 is the source of truth.
- The "handoff bundle → Claude Code" path is the only one that ends in working code. Don't expect Claude Design to overwrite `index.html` directly.
