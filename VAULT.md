# Apulu Universe Vault

Knowledge base for Claude. **Read this first when starting any project.**

## How to use this vault

1. Identify the project domain (see table below).
2. Read the matching topic hub at `wiki/<topic>/_index.md`.
3. Follow links from the hub to deeper notes as needed.
4. For daily context, check `journals/vawn/briefings/` for the most recent entries.

## Domain → Hub Map

| If the project involves... | Start with |
|---|---|
| Vawn mixing, mastering, iZotope plugins | [wiki/vawn-mix-engine/_index.md](wiki/vawn-mix-engine/_index.md) |
| Vawn as an artist (music, releases, identity, videos) | [wiki/vawn-project/_index.md](wiki/vawn-project/_index.md) |
| Apulu Prompt Generator web app | [wiki/apulu-prompt-generator/_index.md](wiki/apulu-prompt-generator/_index.md) |
| AI video/film (Higgsfield, Kling, Seedance) | [wiki/ai-filmmaking/_index.md](wiki/ai-filmmaking/_index.md) |
| Design engineering, frontend quality | [wiki/design-engineering/_index.md](wiki/design-engineering/_index.md) |
| Prompt engineering, creative pipelines | [wiki/cross-topic/_index.md](wiki/cross-topic/_index.md) |
| **Paperclip monitoring, retry/alert/breaker systems, agent failures** | [wiki/infrastructure/_index.md](wiki/infrastructure/_index.md) |
| Apulu Records operations (org chart, routines, dispatcher, DLQ) | [wiki/paperclip-operations/_index.md](wiki/paperclip-operations/_index.md) |
| Apulu Records *code* (Paperclip source) | `paperclip/` (separate workspace, out of vault reorganization scope) |

## Recent context for Vawn work

- **Latest daily briefing:** newest file in `research/vawn/briefings/` — named `Daily Briefing -- YYYY-MM-DD.md`. Briefing includes an **Infrastructure status** block surfacing backend/auth/DLQ state. (Older briefings through 2026-04-14 live at `journals/vawn/briefings/` — archived location.)
- **Latest health note:** newest file in `journals/vawn/health/` (daily Rex output) OR `research/vawn/briefings/Health -- YYYY-MM-DD.md` (CoS output). Both active in parallel — see [[research/vawn/_index]] for which is which.
- **Latest discovery brief:** newest file in `research/vawn/discovery/` — named `Discovery Brief -- YYYY-MM-DD.md` plus per-platform pipeline notes. (Older briefs through 2026-04-14 live at `journals/vawn/discovery/` — archived location.)
- **Live infrastructure snapshot:** `C:\Users\rdyal\Vawn\STATUS.md` — regenerated hourly by `\Vawn\StatusBoard` WTS task. Agents, backend probes, dispatch retries, DLQ, undelivered alerts. See [wiki/infrastructure/](wiki/infrastructure/_index.md) for architecture + runbooks.

## Research tickets

Formal research lives in `research/vawn/` (APU-xxx tickets and dated research docs).

## Reference catalogs

Structured reference material lives in `catalogs/` (e.g., `catalogs/vawn-lyrics.md`).

## Anti-patterns — do NOT do these

- Don't read `research/` before checking if `wiki/` has a digested version of the same subject.
- Don't read pipeline JSON outputs in `pipeline/output/` — they're raw machine data, not knowledge.
- Don't treat files in `paperclip/` as part of this vault's knowledge layer; it's a separate workspace with its own structure.
- Don't add frontmatter to reference notes in `wiki/` — folders and hubs are the filter.
