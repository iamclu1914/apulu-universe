# Apulu Prompt Generator — Overview

**Source files:** `🏠 Home.md`, `Apulu Prompt Generator.md`
**Compiled:** 2026-04-07

---

## Summary

An AI-powered creative direction system that transforms lyrics, descriptions, or audio tracks into photorealistic image and video prompts — scene by scene, outfit by outfit, shot by shot. Built for the [[vawn-project/overview|Vawn]] artist project.

- **Live app:** [apulu-prompt-generator.vercel.app](https://apulu-prompt-generator.vercel.app)
- **GitHub:** [iamclu1914/apulu-prompt-generator](https://github.com/iamclu1914/apulu-prompt-generator)
- **Backend:** [apulu-backend.onrender.com](https://apulu-backend.onrender.com)

## What It Does

- User pastes **lyrics** or a **description**, optionally uploads a **reference image** and **audio track**
- System generates complete creative direction prompts for:
  - **NB2 (Nano Banana 2)** — image-only prompts
  - **Kling 3.0** — image + video prompts
  - **Higgsfield** — image + video prompts optimized for Cinema Studio modes
- Each scene includes: fully dressed subject (outfit, shoes, jewelry, headwear), cinematography brief, and video prompt

## Design Principles

- **No prompt engineering by the user** — agents handle all creative direction internally
- **Character consistency** — reference image locks subject identity; agents never describe hair/skin/build
- **Wardrobe memory** — previously used garments tracked and excluded to prevent repeats
- **Style world rotation** — 7 fashion aesthetics rotated so no two scenes share the same world
- **Shoe color-lock** — shoes must match dominant shirt color via lookup table (see [[style-system]])

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vanilla JS + HTML/CSS (Vercel) |
| Backend | Node.js / Express (Render) |
| Primary AI | Gemini 2.5 Flash (all MV agents) |
| Story Director | Claude Sonnet 4.6 (Higgsfield story chain only) |
| Audio | Gemini Files API (upload + multimodal analysis) |
| Image Gen | NB2 API (via backend proxy) |

## Modes

| Mode | Platform | Scenes | Video Prompts |
|------|----------|--------|---------------|
| MV | Kling | 6–8 | Yes |
| NB2 | — | 6–8 | No |
| 9-Grid | Kling / HF | 9 | Yes |
| Start+End | Kling / HF | 2–4 | Yes |
| Sequential | Kling / HF | N | Yes |
| MV | Higgsfield | 6–8 | Yes (HF format) |
| Story Chain | Higgsfield | 4–12 | Yes (chained) |

See [[ui-modes-and-pipeline]] for full mode details and agent pipeline.

## Key Takeaways

- Zero prompt engineering for the end user — all creative direction is AI-driven
- 4 core agents in sequence (Scene Architect → Stylist → Cinematographer → Video Director) plus optional Treatment Director (Stage 0) and a separate Story Chain pipeline (Audio Analyzer + Story Director)
- Multi-platform output: NB2, Kling 3.0, [[ai-filmmaking/ai-short-film-prompt-library|Higgsfield Cinema Studio]]
- Character consistency via reference images + wardrobe/style world memory
- Vanilla JS frontend, no framework — single-page app with SSE streaming
