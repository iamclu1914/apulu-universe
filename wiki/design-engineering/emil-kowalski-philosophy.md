# Emil Kowalski's Design Engineering Philosophy

**Source file:** `raw/emil-design-eng-skill.md`
**Compiled:** 2026-04-07

---

## Summary

A complete design engineering framework from Emil Kowalski (creator of Sonner, Vaul). Covers animation decisions, easing curves, component building, gesture interactions, and performance rules. The core thesis: **taste is trained, unseen details compound, and beauty is leverage.**

## Core Philosophy

- **Taste is trained, not innate** — develop it by studying great work, reverse-engineering animations, inspecting interactions
- **Unseen details compound** — when a feature works exactly as expected, users proceed without thinking. That's the goal.
- **Beauty is leverage** — people select tools based on overall experience, not just functionality. Good defaults and animations are real differentiators.

## The Animation Decision Framework

### 1. Should this animate at all?

| Frequency | Decision |
|-----------|----------|
| 100+ times/day (keyboard shortcuts, command palette) | No animation. Ever. |
| Tens of times/day (hover, list navigation) | Remove or drastically reduce |
| Occasional (modals, drawers, toasts) | Standard animation |
| Rare/first-time (onboarding, celebrations) | Can add delight |

**Never animate keyboard-initiated actions.** Raycast has no open/close animation — that's optimal for something used hundreds of times daily.

### 2. What easing should it use?

- **Entering/exiting** → `ease-out` (starts fast, feels responsive)
- **Moving/morphing on screen** → `ease-in-out`
- **Hover/color change** → `ease`
- **Constant motion (marquee, progress)** → `linear`

**Critical:** Use custom easing curves — built-in CSS easings are too weak:

```css
--ease-out: cubic-bezier(0.23, 1, 0.32, 1);
--ease-in-out: cubic-bezier(0.77, 0, 0.175, 1);
--ease-drawer: cubic-bezier(0.32, 0.72, 0, 1);  /* iOS-like */
```

**Never use `ease-in` for UI animations.** It starts slow, making interfaces feel sluggish.

### 3. How fast should it be?

| Element | Duration |
|---------|----------|
| Button press feedback | 100–160ms |
| Tooltips, small popovers | 125–200ms |
| Dropdowns, selects | 150–250ms |
| Modals, drawers | 200–500ms |

**Rule: UI animations should stay under 300ms.**

## Component Building Rules

- **Buttons:** Add `transform: scale(0.97)` on `:active` — instant feedback
- **Never animate from `scale(0)`** — start from `scale(0.95)` with `opacity: 0`
- **Popovers:** Set `transform-origin` to trigger location, not center. Exception: modals stay centered.
- **Tooltips:** Skip delay + animation on subsequent hovers after the first one opens
- **Use CSS transitions over keyframes** for interruptible UI (toasts, toggling states)
- **Use blur to mask imperfect transitions** — `filter: blur(2px)` during crossfades bridges visual gaps
- **Use `@starting-style`** for CSS-only enter animations (replaces `useEffect` + `mounted` pattern)

## Spring Animations

- Springs feel more natural because they simulate real physics
- Use for: drag interactions, "alive" elements, interruptible gestures, decorative mouse-tracking
- Springs maintain velocity when interrupted — CSS animations restart from zero
- Keep bounce subtle (0.1–0.3) — avoid bounce in most UI contexts

```js
// Apple's approach (easier to reason about)
{ type: "spring", duration: 0.5, bounce: 0.2 }
```

## Gesture & Drag Interactions

- **Momentum-based dismissal** — calculate velocity (`distance / time`), dismiss if >0.11 regardless of distance
- **Damping at boundaries** — the more they drag past boundary, the less it moves
- **Pointer capture** — set element to capture all pointer events once dragging starts
- **Multi-touch protection** — ignore additional touch points after drag begins
- **Friction instead of hard stops** — allow drag with increasing friction, not invisible walls

## `clip-path` Techniques

- `clip-path: inset()` for rectangular reveal animations
- **Tabs:** Duplicate tab list, clip the "active" copy, animate clip on tab change — perfect color transitions
- **Hold-to-delete:** `inset(0 100% 0 0)` → `inset(0 0 0 0)` over 2s linear on `:active`, snap back 200ms on release
- **Image reveals on scroll:** Start `inset(0 0 100% 0)`, animate to `inset(0 0 0 0)` on viewport entry
- **Comparison sliders:** Clip top image, adjust inset value based on drag position

## Performance Rules

- **Only animate `transform` and `opacity`** — they skip layout and paint, run on GPU
- **Don't use CSS variables for per-frame updates** — changing a CSS var recalculates all children. Update `transform` directly.
- **Framer Motion `x`/`y` props are NOT hardware-accelerated** — use `transform: "translateX()"` instead
- **CSS animations beat JS under load** — they run off main thread. Use CSS for predetermined animations, JS for dynamic/interruptible ones.
- **Use WAAPI** (Web Animations API) for programmatic CSS-performance animations

## The Sonner Principles

From building Sonner (13M+ weekly npm downloads):

1. **Developer experience is key** — no hooks, no context, no complex setup
2. **Good defaults matter more than options** — most users never customize
3. **Naming creates identity** — sacrifice discoverability for memorability
4. **Handle edge cases invisibly** — pause timers on tab hidden, fill gaps between stacked toasts
5. **Use transitions, not keyframes, for dynamic UI**
6. **Build a great documentation site** — let people touch the product before using it

## Review Checklist

| Issue | Fix |
|-------|-----|
| `transition: all` | Specify exact properties |
| `scale(0)` entry | Start from `scale(0.95)` + `opacity: 0` |
| `ease-in` on UI element | Switch to `ease-out` or custom curve |
| `transform-origin: center` on popover | Set to trigger location (modals exempt) |
| Animation on keyboard action | Remove entirely |
| Duration >300ms on UI element | Reduce to 150–250ms |
| Hover without media query | Add `@media (hover: hover) and (pointer: fine)` |
| Keyframes on rapidly-triggered element | Use CSS transitions |
| Framer Motion `x`/`y` under load | Use `transform` string |
| Same enter/exit speed | Make exit faster than enter |
| All elements appear at once | Add stagger (30–80ms between items) |

## Accessibility

- **`prefers-reduced-motion`** — fewer/gentler animations, not zero. Keep opacity/color transitions.
- **Touch device hover** — gate hover animations behind `@media (hover: hover) and (pointer: fine)`

## Key Takeaways

- Animation frequency determines animation need — the more often users see it, the less it should animate
- Custom easing curves (`cubic-bezier`) are non-negotiable — built-in easings are too weak
- `ease-out` is the default for almost everything — `ease-in` is almost never correct for UI
- UI animations should stay under 300ms — perceived speed matters as much as actual speed
- Only animate `transform` and `opacity` — everything else triggers expensive layout/paint
- Transitions beat keyframes for dynamic UI because they're interruptible
- Good defaults > many options — most users never customize (the Sonner principle)
- Review animations the next day with fresh eyes — you miss imperfections during development
- This philosophy aligns with the [[apulu-prompt-generator/overview|Apulu]] design principle of "good defaults over configuration" and the [[cross-topic/consistency-patterns|consistency pattern]] of constraint-driven creativity
