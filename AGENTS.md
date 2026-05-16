# projects/apulu-prompt-generator/ — Codex Instructions

> **Note on location:** in `apulu-universe`, this path is a Windows symlink to the actual project repo on G drive. The Apulu Prompt Generator has its own git repo and Vercel deployment; this file lives in that repo, not in `apulu-universe`. Edits here apply to the prompt-generator project itself.

## What it is

AI-powered music-video creative direction tool. Generates style prompts for Higgsfield/Kling/Seedance video production across 7 style worlds. Node.js + Express server, plain frontend.

See root `AGENTS.md` first, then `wiki/apulu-prompt-generator/_index.md` for higher-level product context.

## Stack rules — non-negotiable unless explicitly migrated

- **Plain HTML / CSS / vanilla JavaScript only.** No React, no Vue, no SvelteKit.
- **No new build step.** No Vite/webpack/esbuild unless the user explicitly asks.
- **Express on the backend.** Don't swap for Next.js, Fastify, or any other framework without explicit ask.
- **Vercel deploy stays untouched.** Don't modify `vercel.json` or deployment config without explicit ask.

## Design system — preserve

- **Warm dark cinematic aesthetic.** Don't shift to bright/light themes or generic AI-form styling.
- **Existing tokens only.** Don't invent new design tokens (colors, spacing, type scales) unless asked.
- **Scene cards are the product.** Their readability, copy affordance (one-click prompt copy), and visual hierarchy take priority over decorative additions.
- **Feels like a creative production instrument**, not a chatbot or generic form.

## Main implementation surfaces

Likely (verify in the project tree before editing):

- `index.html` — main UI shell
- `css/styles.css` (or equivalent) — design tokens + scene card styling
- `server.js` / `server/` — Express endpoints + agent orchestration
- `agents/` — prompt generation agents

## Operating rules

- Read the existing scene-card HTML/CSS before adding a new card variant — visual consistency is load-bearing.
- Prompt generation logic lives server-side; don't move it to the client.
- Static prompts (image) and motion prompts (video) are conceptually separate. Don't merge their structure.
- For new style worlds, follow the existing 7-world pattern; don't refactor the worlds abstraction without an explicit ask.

## Don't touch without explicit ask

- `vercel.json`, deployment config
- `package.json` dependencies (no React/build tools added silently)
- The 7 style worlds catalog — substantive content changes need creative direction, not coding judgment
- Any agent prompt that's been tuned — copy edits are not equivalent to prompt edits
