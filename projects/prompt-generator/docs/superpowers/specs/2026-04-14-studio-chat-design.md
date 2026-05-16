# Studio Chat — Design Spec
**Date:** 2026-04-14

## Summary
Add a "Studio" tab to the Apulu Prompt Generator where the user chats with Claude Sonnet 4.6 to create tracks for Vawn. The AI combines A&R creative direction (album planning, creative briefs, producer selection) with music composition (Suno v5.5 style prompts, lyrics, song structure). Multi-turn conversation with SSE streaming, persisted to localStorage.

## Architecture

### New Files
- `js/studio.js` — Chat state, rendering, SSE streaming, localStorage persistence

### Modified Files
- `index.html` — Add Studio tab in header, add `#studioView` div in canvas area, add studio chat input bar, load `js/studio.js`
- `css/styles.css` — Studio chat styles (messages, input bar, badges)
- `server.js` — New `POST /api/studio/chat` SSE endpoint with combined A&R + Composition system prompt

## UI Design

### Header
- New "Studio" tab button after existing output mode tabs, separated by `h-sep` divider
- When Studio active: output mode tabs (Both/Image Only/Video) hide, HF/NB2 badges hide
- New badge appears: `● Claude Sonnet` (gold dot, warm styling)
- When any other tab clicked: Studio view hides, prompt generator shows

### Canvas (Studio active)
- Existing `#canvas` hides; new `#studioView` shows
- Chat messages scroll vertically, newest at bottom, auto-scroll on new content
- **User messages**: Right-aligned, gold-tinted background (`rgba(212,160,58,0.1)`), Raleway
- **AI messages**: Left-aligned, warm dark card (`#1a1816`), Raleway. Markdown rendered inline (headers, bold, italic, lists, code blocks, horizontal rules, `━━━` dividers)
- **Streaming indicator**: Pulsing gold cursor at end of AI message while streaming

### Bottom Bar (Studio active)
- Existing composer pill hides; studio input shows
- Auto-resizing textarea, placeholder: `"Plan an album, build a creative brief, write a track..."`
- Send button (gold accent)
- Enter sends, Shift+Enter for newlines
- Two utility buttons: `New Session` (clears chat + localStorage), `Copy Last` (copies last AI response raw markdown to clipboard)

### Markdown Rendering
- Inline minimal renderer — no external dependency
- Supports: `#`-`######` headers, `**bold**`, `*italic*`, `- ` and `1. ` lists, `` `code` `` inline, triple-backtick code blocks, `---`/`━━━` horizontal rules
- Code blocks get a subtle copy button

## Server Endpoint

### `POST /api/studio/chat`
**Request body:** `{ messages: [{ role: "user"|"assistant", content: "string" }] }`

**Response:** SSE stream
```
data: {"type":"delta","text":"..."}
data: {"type":"done"}
data: {"type":"error","message":"..."}
```

**Implementation:**
- System prompt held server-side (never sent to client) — combined A&R + Composition prompt
- Proxies to `https://api.anthropic.com/v1/messages` with `stream: true`
- Model: `claude-sonnet-4-6`
- `max_tokens: 16000`
- `thinking: { type: "enabled", budget_tokens: 10000 }` — thinking blocks NOT streamed
- Only streams `content_block_delta` events where `delta.type === "text_delta"`
- Sends `{"type":"done"}` on `message_stop`
- Sends `{"type":"error"}` on any failure

### System Prompt
Combined from two skill files:
- `c:/Users/rdyal/.claude/skills/ar-music/SKILL.md` — A&R creative direction
- `c:/Users/rdyal/.claude/skills/music-composition-skill/SKILL.md` — Composition rules

The merged prompt should:
- Open with identity: "You are the A&R and music composer for the Vawn project."
- Include A&R: Project Mode, Track Mode, Creative Brief format, Producer Sound Library, Lyric Mode Selection, A&R Judgment Standards, Song Selection criteria
- Include Composition (music-composition-skill v2 — Suno v5.5 Architecture v2):
  - **Part A — Vawn Identity** (North Star, Core Fear, Voice locks, Sonic Standards, What Vawn Is NOT, Distinction table)
  - **Part B — Universal Suno Prompting Doctrine** (Three-field architecture, Nine-element style prompt order, prose-not-JSON format rule, approved mood pairs, character economics)
  - **Part C — Vawn-Specific Prompt Format** (Production Prompt + Final Recording Prompt — both prose, comma-separated, NO MAX tags, NO JSON fields, under 980 chars; vocal identity in Final only; no bar-by-bar performance in style prompt)
  - **Part D — Lyrics + Humanizer** (lyrics box hard rule, section tag placement, inline vocal metatags as new home for performance direction, advanced structure metatags, J. Cole / T.I. / Jadakiss lyric modes, Vawn's own techniques, brief-specificity diagnostic, humanizer audit, banned crutch lines, banned lazy themes, vocabulary freshness)
  - **Part E — Studio Output Contract** (five components in order: Song Title, Production Prompt, Exclude Styles, Final Recording Prompt, Lyrics; default delivery is structured text; structural variety rule)
- Include full Producer Sound Library descriptors (Vawn signature sounds + producer styles, prose-formatted with separate Performance line for lyrics-box metatags)
- Include full banned vocabulary list
- Natural mode switching: A&R hat for planning/briefs, Composer hat for lyrics/Suno prompts
- Skip Cultural Radar web search instructions (not available in this context)
- Skip HTML card output (chat uses text, user copies what they need)

> **v2 update note (2026-05-03):** Composition skill migrated from v1 numbered Rules (0–8) with field-per-line JSON + MAX tags to v2 lettered Parts (A–E) with prose format and no MAX tags. The merged system prompt and `server.js` Rule 1 example outputs were updated accordingly. Performance direction now lives in the lyrics box as inline metatags ([chest voice], [Energy: High], etc.), not in the style prompt.

## localStorage Persistence

**Key:** `apulu_studio_messages`
**Value:** Array of `{ role, content, ts }` objects
- Saved after every completed AI response
- Capped at 50 messages (oldest trimmed from stored array; all messages stay visible in current session UI)
- Restored on page load when Studio tab is shown
- `New Session` clears this key and the UI

## Error Handling

- SSE stream failure mid-response: show partial text + error pill "Connection lost — click to retry"
- API 429: "Sonnet is busy — try again in a moment"
- API 500 / missing key: "Studio not configured on server"
- Render cold start: typing indicator pulses until first delta arrives (no timeout — connection stays open)

## Aesthetic
- Dark theme consistent with existing app (`#0c0b0a` base, `#d4a03a` gold accent)
- Film grain overlay stays
- Instrument Serif italic for any display text; Raleway for chat messages
- No borders on message cards — spacing and subtle background differentiation only
- Warm tints throughout — no cold grays
