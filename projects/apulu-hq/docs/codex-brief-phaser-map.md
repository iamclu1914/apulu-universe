# Apulu HQ — Phase 6: Phaser HQ Map

> **Codex job brief.** Build the interactive top-down map of Apulu Records HQ
> with agent avatars that react to live WebSocket events. This document is
> the contract; everything you need to know is here.

## Mission

Add a top-down 2D map of Apulu Records HQ to the existing `webclient/`. Agents
appear as avatars at their desks, walk around when idle, animate state changes
when WebSocket events arrive from the backend, and respond to clicks by
opening the existing chat panel. The chat panel stays exactly where it is on
the right side; the map replaces the empty center area between the agent
list and the chat panel.

Success criterion: when Paperclip fires `morning-early` at 8am, Sage & Khari's
sprite walks from their desk over to a "working" pose, a particle effect
plays, then a ✅ pops above their head when `routine.succeeded` arrives — all
driven by WS events that are already flowing.

## What exists already (do NOT modify)

You are working inside `projects/apulu-hq/`. Read these first; they are the
contract you build against:

| File | Why it matters |
|---|---|
| `apulu_hq/events/schema.py` | The 15 versioned event types (Pydantic). Every event has `{type, ts, payload, v}`. |
| `apulu_hq/api/app.py` | REST endpoints — `/api/agents`, `/api/dispatches`, `/api/dlq`, `/ws`. Do not change. |
| `webclient/index.html` | The current UI. 3-column grid (agents / chat / events). Vanilla JS, no build step. Dark editorial palette. |
| `apulu_hq/importer.py` | Seeds 16 agents with `desk_x`, `desk_y`, `sprite_key`, `department`, `role`. The desk coords are intentionally laid out per the spec — use them. |
| `docs/superpowers/specs/2026-05-13-apulu-hq-design.md` | Full spec. Section 3 ("Layer 1 — Presentation") has the HQ floor plan + sprite state machine. Read it. |

Do NOT touch any Python file. This is a pure-frontend ticket. The only file
you should be creating or editing is under `projects/apulu-hq/webclient/`.

## Constraints

1. **No build step.** Vanilla JS + ESM imports from CDN (esm.run / esm.sh /
   skypack — pick one and stick with it). The existing `index.html` is a
   single file served by FastAPI's `StaticFiles`. Match that pattern.
2. **Phaser 3 from CDN.** `https://cdn.jsdelivr.net/npm/phaser@3.85.2/dist/phaser.min.js`
   (or the latest 3.x). Standard global `Phaser`.
3. **Dark editorial palette** — same CSS vars already in `index.html`:
   `--bg #1a1410`, `--surface #2a1f18`, `--gold #c8a35b`, `--text #f4ecdf`,
   `--muted #9a8a78`, `--ok #8bc28b`, `--error #d96565`. The map background
   should be a tasteful warm dark, not pure black.
4. **Free sprites.** No paid assets. Use one of:
   - 32×32 CC0 pixel sprites from OpenGameArt / LPC base
   - A procedural sprite generator (shapes + colors) you write inline, so the
     map is self-contained and ships with the repo
   - Inline SVG converted to texture via Phaser's `textures.addBase64`
   - Whatever you pick must be **redistributable** and **committed to the repo**.
     Do NOT pull binary assets from random URLs at runtime.
5. **Backwards compatible.** The existing chat panel, agent list, event
   ticker, dispatch tab, DLQ tab must all still work. Don't break the
   3-column layout — just add a 4th view (the map) inside the center column,
   replacing the current chat-message area when a map mode is active.
6. **WebSocket reuse.** Open ONE WebSocket connection shared by chat + map.
   The current code opens one in `connectWs()`; refactor so both consumers
   share it. Don't open two.
7. **No new HTTP endpoints.** Everything you need is exposed already. If you
   feel like you need one, raise it in the PR description instead of adding it.

## The floor plan

From the spec (Section 3, "Floor plan v1"). Render a 24×16 tile grid
(each tile ~40 px, total canvas ~960×640). Rooms are blocked out as
floor regions; walls are decorative borders.

```
+----+--------------------+----------------+
| CEO|  Marketing Bullpen | Production     |
|    |  S&K · Dex · Nova  | Cole · Camdyn  |
|----|  Oaklyn · Echo     |  · Onyx        |
| CoS|--------------------+----------------|
| Nl |  Research Lab      | Post-prod      |
| Sa |  Rex · Rhythm      | Rhythm desk    |
|    |  Sable · Aspyn     |                |
|    |  Cipher · Vibe     |                |
+----+--------------------+----------------+
              [Hallway / common area]
```

Desk coordinates come from the database (`desk_x`, `desk_y` columns on
`agents`). They are deliberately spread out; honor them. If two desks
visually collide, that's a future ticket — for v1 just render them.

## Sprite state machine

Each agent sprite has one of these states, driven by WS events:

| State | When entered | Visual |
|---|---|---|
| `idle` | Default; no recent activity | Sitting/standing at desk, gentle breathing animation |
| `walking` | Wandering or moving to target | 4-frame walk cycle, sprite glides between tiles |
| `working` | `routine.started` for this agent | Seated at desk, small particle effect or animated "..." floater |
| `chatting` | User selected this agent in chat panel | Sprite turns toward CEO, speech bubble icon |
| `error` | `routine.failed` or `dlq.appended` for this agent | Sprite tinted red, "!" floater for 6s, then back to idle |
| `success` | `routine.succeeded` for this agent | Brief green "✅" floater for 3s, then back to idle |

Default behavior loop (every ~15s per agent): pick a random tile within the
agent's department region, walk there, dwell 5–10s, walk back to own desk.
This makes the map feel alive even when no events are firing.

## Events you must handle

Subscribe to `ws://127.0.0.1:8741/ws`. Events arrive as `{type, ts, payload, v}`.
You need these:

| Event type | Payload fields | UI reaction |
|---|---|---|
| `routine.started` | `agent_id`, `slot`, `dispatch_id` | Agent → walking → desk → working |
| `routine.succeeded` | `agent_id`, `slot`, `duration_ms` | Agent → success floater (3s) → idle |
| `routine.failed` | `agent_id`, `slot`, `signature`, `exit_code` | Agent → error floater (6s) → idle |
| `dispatch.retry_scheduled` | `agent_id`, `slot`, `attempt` | Subtle yellow pulse on agent |
| `dlq.appended` | `agent_id`, `slot`, `signature` | Agent → error floater + persistent ⚠️ on desk until DLQ tab opened |
| `breaker.tripped` | `component`, `reason` | Banner already handles this. Optional: dim the map. |
| `breaker.cleared` | `component` | Un-dim. |
| `chat.token`, `chat.done` | (existing chat path) | Don't touch. |
| `heartbeat` | `agents`, `routines`, `subscribers` | Ignore for map purposes. |

Backend may emit unknown event types in the future. Be permissive: log and skip.

## UX

- **Default landing.** When the user first opens the page, show the map view
  in the center column with chat collapsed/hidden.
- **Clicking an agent sprite** → opens the chat panel on the right side (the
  current chat panel is already there; just trigger the same selectAgent code
  path the agent-list buttons use today).
- **Selecting an agent from the left list** → camera pans to that agent's
  sprite, sprite turns to "chatting" state.
- **Mode toggle** (optional but nice): a small toggle in the top bar to switch
  between "Map view" and "List view" for the center column. List view is
  basically the current chat-message-only layout.
- **Camera.** Fixed top-down, no zoom required for v1. Pan with arrow keys or
  click-and-drag if the map is bigger than the viewport.

## Don't gold-plate

These are explicit NON-goals for this ticket:

- ❌ The CEO sprite walking around. v1 has agents only; you the operator
  are the camera.
- ❌ Tiled-editor maps. Hand-author the layout in code (a JSON or 2D
  array literal in a `mapdata.js` file is fine).
- ❌ Pathfinding beyond Manhattan walking. Naive "step toward target, one
  tile at a time" is good enough for 16 sprites.
- ❌ Sound effects. Add a `// TODO: audio?` and leave it.
- ❌ Mobile. Desktop only.
- ❌ New Python tests. Pure frontend. Add a small `webclient/test.html`
  manual test page if useful, but no pytest.

## Suggested file layout

```
webclient/
  index.html          (edit: add the Phaser canvas + mode toggle, refactor WS to be shared)
  hq-map.js           (new: Phaser scene, sprite state machine, event handlers)
  hq-map.css          (new: optional, or inline in index.html)
  sprites/            (new: if you commit any sprite assets, put them here)
  mapdata.js          (new: the floor plan + desk → tile mapping)
```

Use ES modules with `<script type="module">`. Keep `hq-map.js` framework-free
beyond Phaser — no React, no Vue, no jQuery, no Tailwind.

## How to test what you've built

1. From the project root: `python scripts/run_dev.py` (server runs on 8741)
2. Open `http://127.0.0.1:8741/ui` in any modern browser
3. Map view should be the default. You should see 16 sprites at their desks.
4. In a separate terminal, append a synthetic line to `dispatch_log.jsonl`
   to trigger an event without waiting for Paperclip:

```bash
echo '{"timestamp":"2026-05-14T20:00:00+00:00","slot":"hashtag-scan","attempt":1,"max_attempts":3,"exit_code":0,"duration_sec":2.1,"signature":null,"retryable":true,"final":true,"success":true}' >> C:/Users/rdyal/Vawn/dispatch_log.jsonl
```

(`hashtag-scan` is assigned to Sage & Khari. Within ~2 seconds, you should see
Sage & Khari's sprite go through walking → working → success floater.
**REMOVE that test line afterward** so you don't pollute production logs:
`Get-Content -Path C:/Users/rdyal/Vawn/dispatch_log.jsonl | Select-Object -SkipLast 1 | Set-Content ...`
or use a tmp file and `mv` it back.)

5. Click any agent on the left list — sprite should highlight and chat should
   open. Send a message; existing claude_local adapter still works.
6. Click an agent's sprite directly on the map — same effect.

## Commit + PR rules

- One commit per logical unit (refactor WS sharing → 1 commit, add Phaser map
  → 1 commit, hook up events → 1 commit). Don't squash everything into one.
- Commit messages in the repo style (`feat(apulu-hq): ...`, present tense,
  body explains the why).
- After the work is done, push the branch and open a PR against `main`
  titled `feat(apulu-hq): Phase 6 — interactive HQ map (Phaser 3)`.
- Reference both PR #8 (the spec) and PR #9 (Phase 0+1+2 work) in the PR body.
- Include a "How to test" section in the PR body that's copy-pasteable.
- Don't merge — leave for human review.

## When you finish

Print a one-line summary like:
```
DONE. Branch feat/apulu-hq-phaser-map ready, PR opened at <url>. N commits, M files changed.
```

If you hit a wall, commit what you have, push the branch, and write a short
`PROGRESS.md` in the repo describing the state and what's blocking — don't
silently abandon.

Good luck. Make it feel like a place.
