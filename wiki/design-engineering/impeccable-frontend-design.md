# Impeccable Frontend Design (pbakaus)

**Source file:** `raw/impeccable-frontend-design-skill.md`
**Compiled:** 2026-04-07

---

## Summary

A frontend design framework from Paul Bakaus (Impeccable project) focused on creating distinctive, production-grade interfaces that avoid generic "AI slop" aesthetics. Covers typography, color, layout, motion, interaction, responsive design, and UX writing. Complementary to [[emil-kowalski-philosophy|Emil Kowalski's animation-focused philosophy]] — this framework covers the full design surface.

## Core Principle: The AI Slop Test

> If you showed this interface to someone and said "AI made this," would they believe you immediately? If yes, that's the problem.

A distinctive interface should make someone ask "how was this made?" not "which AI made this?"

## Design Direction

Commit to a **bold** aesthetic direction — not a safe middle ground:
- Pick an extreme tone: brutally minimal, maximalist chaos, retro-futuristic, organic, luxury, playful, editorial, brutalist, art deco, industrial...
- **Differentiation:** What makes this unforgettable? What's the one thing someone will remember?
- Bold maximalism and refined minimalism both work — the key is **intentionality, not intensity**
- Never converge on common choices across generations

## Typography

- **Use distinctive fonts** — avoid Inter, Roboto, Arial, Open Sans, system defaults
- Better alternatives: Instrument Sans, Plus Jakarta Sans, Outfit, Onest, Figtree, Fraunces
- Use a **modular type scale** with fluid sizing (`clamp()`) — 5 sizes covers most needs
- Vertical rhythm: line-height should be the base unit for all vertical spacing
- Max width: `65ch` for readability
- **Don't**: use monospace as lazy shorthand for "technical", large icons with rounded corners above every heading

## Color & Theme

- Use **modern CSS color functions**: `oklch()`, `color-mix()`, `light-dark()`
- **Tint neutrals** toward your brand hue — even subtle tinting creates cohesion
- Never use pure black (#000) or pure white (#fff) — always tint
- **Don't**: gray text on colored backgrounds, cyan-on-dark, purple-to-blue gradients, neon accents on dark, gradient text for "impact"
- **Don't default to dark mode** with glowing accents — it looks "cool" without requiring actual design decisions

## Layout & Space

- Create **visual rhythm through varied spacing** — tight groupings, generous separations
- Use `clamp()` for fluid spacing that breathes on larger screens
- Embrace **asymmetry** — break the grid intentionally for emphasis
- **Don't**: wrap everything in cards, nest cards inside cards, use identical card grids, center everything, use the same spacing everywhere, use the hero metric layout template

## Motion

Aligns with and extends [[emil-kowalski-philosophy|Emil Kowalski's framework]]:

- Focus on **high-impact moments** — one well-orchestrated page load beats scattered micro-interactions
- Use **exponential easing** (ease-out-quart/quint/expo) for natural deceleration
- The 100/300/500 rule: 100–150ms instant feedback, 200–300ms state changes, 300–500ms layout changes
- **Exit animations are faster** than entrances (~75% of enter duration)
- For height animations: use `grid-template-rows: 0fr → 1fr` instead of animating `height`
- **Don't**: animate layout properties (width, height, padding, margin), use bounce/elastic easing

## Interaction

- Use **progressive disclosure** — start simple, reveal sophistication through interaction
- **Optimistic UI** — update immediately, sync later
- Design **empty states that teach** the interface, not just say "nothing here"
- **Don't**: repeat the same information, make every button primary, use modals unless there's truly no better alternative

## Responsive

- Use **container queries** (`@container`) for component-level responsiveness
- Adapt the interface for different contexts — don't just shrink it
- **Don't** hide critical functionality on mobile — adapt, don't amputate

## UX Writing

- Make every word earn its place
- Don't repeat information users can already see

## Context Gathering Protocol

Before any design work, you need:
1. **Target audience** — who uses this and in what context?
2. **Use cases** — what jobs are they trying to get done?
3. **Brand personality/tone** — how should the interface feel?

These cannot be inferred from code. Check `.impeccable.md` in project root, or run `/teach-impeccable` to establish context.

## Key Takeaways

- The "AI slop" fingerprints: cyan-on-dark, purple gradients, card grids, gradient text, glassmorphism, Inter font, dark mode with glow — avoid all of these
- Intentionality > intensity — a refined minimalist design is as bold as maximalism
- Typography and color are the fastest ways to escape generic aesthetics
- Tint your neutrals, use `oklch()`, avoid pure black/white
- Motion should serve spatial consistency and state indication, not decoration (see [[emil-kowalski-philosophy]] for animation decision framework)
- Progressive disclosure > showing everything at once
- Container queries > media queries for component-level responsiveness
- These principles complement the [[apulu-prompt-generator/style-system|Apulu style system]]'s constraint-driven approach — both use hard rules to force distinctive output
