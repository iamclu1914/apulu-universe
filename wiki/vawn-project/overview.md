# The Vawn Project — Overview

**Compiled:** 2026-04-07
**Sources:** All wiki topics

---

## Summary

Vawn is a hip-hop artist project with a technology-first approach to music production and visual content creation. The project has built multiple AI-powered systems that automate creative workflows across audio and visual domains.

## Systems

### Visual Pipeline: [[apulu-prompt-generator/overview|Apulu Prompt Generator]]

- AI-powered creative direction system that transforms lyrics into complete image and video prompts
- 4-agent sequential pipeline (Scene Architect → Stylist → Cinematographer → Video Director)
- Generates prompts for NB2 (image), Kling 3.0 (video), and [[ai-filmmaking/ai-short-film-prompt-library|Higgsfield]] (video)
- [[apulu-prompt-generator/style-system|Style system]] with 7 fashion worlds, shoe color-lock rule, and wardrobe memory
- Live at [apulu-prompt-generator.vercel.app](https://apulu-prompt-generator.vercel.app)

### Audio Pipeline: [[vawn-mix-engine/overview-and-architecture|Vawn Mix Engine]]

- Automated hip-hop mixing and mastering using REAPER + iZotope plugins
- 5-stage pipeline: RX cleanup → Nectar vocal mix → Neutron instrument mix → TBC3 reference → Ozone mastering
- Python orchestrates REAPER via reapy — never processes audio directly
- [[vawn-mix-engine/levels-and-gain-staging|Gain staging]] targets and [[vawn-mix-engine/izotope-plugin-guide|plugin-specific workflows]] derived from extensive research
- Phase 4 complete (327 tests passing), Phase 5 (reports) in progress

### AI Filmmaking Knowledge: [[ai-filmmaking/]]

- Production techniques for AI-generated video using Higgsfield Cinema Studio and Soul Cinema
- Character consistency via Soul ID tags and reference sheets
- Scene-by-scene prompting with camera direction, aesthetic descriptors, and B-roll strategies

## The Common Thread

All Vawn systems share a design philosophy:

- **Constraint-driven creativity** — hard rules (shoe color-lock, level targets, identity tags) produce more consistent output than open-ended generation
- **Pipeline orchestration** — complex creative tasks decomposed into sequential specialist stages
- **AI as starting point, not final word** — iZotope Assistants, Gemini agents, and Soul ID all provide foundations that get refined
- **Transparency** — mix reports, scene cards, and pipeline stage tracking make every decision visible

See [[cross-topic/creative-pipelines-and-prompt-engineering|Creative Pipelines Comparison]] for a detailed analysis of how these systems relate.

## Key Takeaways

- Vawn is the unifying project behind all major systems in this knowledge base
- Visual (Apulu) and audio (Mix Engine) pipelines are independent but share architectural patterns
- Both pipelines prioritize consistency through constraint systems over manual discipline
- The project treats creative tools as automation targets — if a workflow is repeatable, it gets systematized
