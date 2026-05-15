# Apulu Universe — Codex Instructions

This repository is Apulu Universe: the operating vault, automation layer, and creative pipeline system for Apulu Records, Vawn, the Apulu Prompt Generator, and related AI music/video workflows.

Do not treat this repo as a generic app repo.
Do not treat this repo as the APULU streetwear brand repo.

## Primary Operating Rule

Before doing work, identify the task domain and read the correct source of truth.

Use:

- `VAULT.md` for repo navigation
- `CLAUDE.md` for full project context
- `wiki/` for digested operational knowledge
- `pipeline/` for content pipeline work
- `projects/apulu-prompt-generator/` for the prompt generator app
- `scripts/seeds/` for the agent/routine seed JSON used by Apulu HQ (renamed from `scripts/paperclip/` on 2026-05-15 when Paperclip was retired; see CLAUDE.md "Paperclip Retired" section for the migration story)
- `skills/` for packaged workflow skills
- `research/` for formal research outputs
- `journals/` for historical notes and Vawn development context

Do not read the entire repo blindly. Route first, then inspect the relevant files.

## Repo Purpose

This repo supports:

- Apulu Records as an AI-powered record label
- Vawn as the first artist/client
- Paperclip-based agent orchestration
- Content discovery, ideation, scripting, cascade posting, and briefings
- Vawn marketing and release operations
- AI music-video prompt generation
- Research pipelines
- Skills and automation packaging
- Mix/master workflow documentation and tooling

## Core Safety Rules

- Never expose, print, summarize, or commit secrets, API keys, app passwords, tokens, credentials, or private config values.
- Treat files named `config.json`, `credentials.json`, `.env`, `*_ids.json`, token files, app-password files, and local path configs as sensitive.
- Do not modify credentials, tokens, Paperclip IDs, routine IDs, or agent IDs unless explicitly asked.
- Do not delete logs, DLQ files, posted logs, monitor state, alert fallback files, or status files unless explicitly asked.
- Do not assume local Windows paths exist in the current environment.
- Do not change scheduled-task behavior without explaining the operational impact.

## Existing System Boundaries

Respect these areas:

- `pipeline/` = configurable content pipeline
- `pipeline/bridge.py` = bridge from pipeline intelligence into Vawn posting context
- `scripts/paperclip/` = Paperclip setup and management scripts
- `skills/` = packaged skill files
- `wiki/` = digested knowledge base
- `research/` = formal research and dated outputs
- `journals/` = operational notes and historical context
- `projects/apulu-prompt-generator/` = Apulu Prompt Generator app/project area

## Work Style

- Inspect relevant files before editing.
- Make minimal, high-confidence changes.
- Preserve existing architecture, naming, folder organization, and workflow conventions.
- Do not rewrite unrelated files.
- Do not invent missing operational facts.
- If documentation conflicts, prefer the most specific, newest, task-relevant file.
- Call out stale docs, broken links, missing files, and assumptions clearly.

## Python / Script Rules

- Prefer dry-run mode when available.
- Before editing automation scripts, identify:
  - entry point
  - schedule or caller
  - input files
  - output files
  - state files touched
  - retry or DLQ behavior
- Do not remove retry logic, circuit breakers, deduplication, health checks, or failure-signature handling without a strong reason.
- When changing scripts, preserve CLI flags and backward compatibility unless explicitly told otherwise.
- Add or update smoke tests where practical.

## Content Pipeline Rules

For content pipeline work:

- Preserve project-config-driven behavior.
- Do not hardcode Vawn-specific behavior into shared pipeline files unless the file is explicitly Vawn-only.
- Keep discovery, ideation, scripting, cascade, and bridge stages separate.
- Respect existing content rules.
- Do not generate generic AI captions.
- Do not use banned Vawn marketing language if content rules prohibit it.

Known Vawn content rules:

- Do not say “stream,” “listen,” or “press play.”
- Do not reference track names unless rules allow it.
- No gospel framing.
- No generic clichés.
- Threads should not use hashtags.
- Bluesky max should stay conservative.

## Apulu Prompt Generator Rules

For Apulu Prompt Generator work:

- Plain HTML/CSS/vanilla JavaScript only unless the app has been intentionally migrated.
- No React unless explicitly requested.
- No new build step unless explicitly requested.
- Preserve the warm dark cinematic design system.
- Do not invent new design tokens unless requested.
- Main implementation surfaces are likely `index.html`, `css/styles.css`, and Express/server files.
- Scene cards are the product; prioritize prompt readability, copy affordance, and visual hierarchy.
- The UI should feel like a creative production instrument, not a generic AI form.

## AI Filmmaking / Prompt Rules

For Higgsfield, Kling, Seedance, Nano Banana, and music-video prompt work:

- Preserve character consistency.
- Avoid restricted/protected-content phrasing.
- Structure prompts for production use:
  - shot type
  - lens
  - motion
  - subject
  - environment
  - lighting
  - action
  - texture
  - continuity
  - negative constraints
- Separate static image prompts from video motion prompts when needed.
- Do not overstuff one prompt with duplicate camera instructions.
- Add transition/B-roll shots when the video needs movement between scenes.

## Vawn Music Rules

For Vawn creative work:

- Vawn is a deep, resonant male hip-hop/R&B artist with controlled, commanding delivery.
- Avoid robotic, over-polished, choir-like, or generic AI vocal direction.
- Preserve his Brooklyn-raised / Atlanta-based identity unless a specific concept changes the framing.
- For mix/master work, read the mix-engine wiki before editing or recommending changes.
- Do not change mix targets, LUFS strategy, iZotope chain behavior, or Reaper automation logic without explaining the tradeoff.

## Paperclip / Agent Ops Rules

For Paperclip or agent orchestration work:

- Understand which agent, routine, adapter, or schedule is affected before editing.
- Do not rename agents, departments, routines, or IDs casually.
- Do not break dispatch routing.
- Preserve DLQ, retry, circuit-breaker, health-probe, and alert-fallback behavior.
- Prefer check-only or dry-run commands first.
- If Claude auth, backend health, Bluesky auth, rate limits, or adapter config may be involved, inspect the relevant runbook or status file first.

## Testing / Verification

Use the most relevant available checks:

- Python syntax: `python -m py_compile <file>`
- Python tests: `pytest` if tests exist
- Dry-run scripts where available
- Node app checks: `npm test`, `npm run lint`, `npm run build`, or project-specific command
- Link checks for docs when editing wiki/vault files
- Manual verification steps if local dependencies are unavailable

If a command cannot be run, explain why and provide the exact command for local testing.

## Final Response Format

When you finish, report:

1. Files changed
2. Why those files
3. What changed
4. How to test
5. Risks / assumptions
6. Follow-up recommendations
