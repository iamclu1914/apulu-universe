# Apulu — Architecture & Deployment

**Source files:** `Architecture.md`, `Deployment.md`, `API Endpoints.md`
**Compiled:** 2026-04-07

---

## Summary

The system is a two-service architecture: a vanilla JS frontend on Vercel and an Express backend on Render. The backend acts as API proxy (keeps keys out of the browser), pipeline orchestrator, and audio relay.

## Architecture

- **Frontend** (`index.html` + `js/app.js`) — single-page app, no framework
  - Mode selection (NB2 / Kling / Higgsfield)
  - Reference image upload (4MB limit, 1568px max)
  - Audio upload for HF track analysis
  - SSE consumption for streaming progress
  - Wardrobe + style world memory tracking per session
- **Backend** (`server.js`) — Express on Render
  - API proxy for Gemini / Anthropic keys
  - Pipeline orchestrator — calls agents in sequence, streams SSE progress
  - Audio relay — uploads to Gemini Files API
- **Agent layer** (`agents/`) — each agent exports `{ systemPrompt, buildUserMessage }`

## Data Flow (MV Generation)

1. User pastes lyrics → Frontend `POST /api/generate-prompts-stream`
2. Backend calls Scene Architect → Stylist → Cinematographer → Video Director in sequence
3. Each stage streams SSE progress back to frontend
4. Final merged result renders as scene cards

## API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /api/generate-prompts-stream` | Main generation (all modes except hf-story) |
| `POST /api/generate-story-stream` | Higgsfield Story Chain generation |
| `POST /api/upload-audio` | Upload audio to Gemini Files API |
| `POST /api/gemini` | General Gemini proxy |
| `POST /api/generate-kling-prompts` | Kling video prompts (uses `promptId`, not raw prompts) |
| `POST /api/generate-hf-prompts` | Higgsfield video prompts (non-story) |

**Input limits:** lyrics 8000 chars, fields 500 chars, short strings 100 chars.

## Deployment

| Service | Platform | Auto-deploys on |
|---------|----------|----------------|
| Frontend | Vercel | `git push main` |
| Backend | Render (free tier) | `git push main` |

- `vercel.json` rewrites `/api/*` → Render backend (no CORS needed in browser)
- **Render cold start:** ~30s after 15 min inactivity
- `GEMINI_API_KEY` and `ANTHROPIC_API_KEY` live only in Render dashboard env vars — never in repo
- Body size limit: 50mb (for base64 image uploads)

## Key Takeaways

- Two-service split: static frontend (Vercel) + API backend (Render) with transparent `/api/*` rewrite
- All AI keys stored exclusively in Render env vars — never exposed to browser
- SSE streaming provides real-time pipeline progress to the user
- Render free tier cold-starts are a known UX issue (~30s first request)
- `promptId` pattern: clients send a prompt ID, server maps to system prompt internally — keeps prompts server-side
- See [[overview]] for project context, [[ui-modes-and-pipeline]] for agent details
