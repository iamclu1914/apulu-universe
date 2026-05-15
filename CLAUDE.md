# Apulu Records — Project Instructions

@VAULT.md

## What This Is
**Apulu Records** is an AI-powered record label. The orchestration layer is **Apulu HQ** (at `projects/apulu-hq/`): a FastAPI + SQLite backend with a desktop shell, plus a CEO command-center dashboard. 16 agents under 3 division presidents (A&R/Marketing/Operations), managing artist Vawn as the first client (multi-artist extensible).

## Paperclip Retired (2026-05-15)
Apulu Records used to run on [Paperclip](https://github.com/paperclipai/paperclip) — Paperclip was the orchestration layer at `localhost:3100`. As of **2026-05-15** Paperclip is retired. The full agent registry, chat threads, scheduled routines, and dispatch history were migrated into Apulu HQ. Agent chat now routes through the **Hermes ACP** adapter (`apulu_hq/chat/hermes_local.py`), and the scheduler in `apulu_hq/dispatch/` owns all cron-fired routines (defaults to live mode).

If you see references to "Paperclip" in the codebase or docs, they are historical context. The relevant artifacts have moved:
- `scripts/paperclip/` → `scripts/seeds/` (seed JSON the importer reads)
- `localhost:3100` API → `localhost:8741` (Apulu HQ FastAPI)
- Paperclip's web UI → `http://127.0.0.1:8741/ui/` (CEO command center)
- `paperclip/server/...` directory → dormant on disk, can be archived/deleted when ready
- The 3 `\Vawn\Paperclip*` scheduled tasks → disabled

## Apulu HQ (Agent Orchestration)
Apulu HQ runs at `http://127.0.0.1:8741`. The desktop shell (`python -m apulu_hq.shell`) launches it with a system-tray icon. Backend-only mode for dev: `python projects/apulu-hq/scripts/run_dev.py` (auto-reloads).

### Org Structure (16 agents — current, 2026-04-16)
```
Clu (Chairman & CEO — you)
│
├── Camdyn (A&R President)  ← was "Timbo"
│   ├── Cole (In-House Producer & Songwriter)
│   ├── Onyx (Studio & Post-Production Lead)
│   └── Rhythm (A&R Scout & Discovery Analyst)
│
├── Oaklyn (Marketing President)  ← was "Letitia"
│   ├── Sage & Khari (Content & Visuals Team)  ← merged process agent
│   ├── Dex (Community & Fan Engagement Manager)
│   ├── Echo (Head of Publicity & DSP Relations)
│   └── Sable (Artist Relations Manager)
│
└── Aspyn (Operations President)  ← was "Nari"
    ├── Rex (CTO & AI Infrastructure Lead)
    ├── Nova (Analytics & Streaming Strategy Lead)
    ├── Cipher (CFO & Finance Lead)
    └── Vibe (Head of Partnerships & Revenue)

+ Nelly (General Counsel & Head of Business Affairs) — reports to Clu
```

Agents marked `process` (heartbeat-enabled, run Python scripts):
- Sage & Khari → `marketing_dispatch.py` (posting)
- Dex → `engagement_agent.py` (engagement)
- Nova → `metrics_agent.py` (analytics)

All others are `claude_local` (Claude Code spawned on-demand by routine or issue assignment).

### Your Role (Clu)
- **Chairman**: Set company direction, final authority on all major decisions
- **Creative Director**: Approve lyrics, mixes, masters, music video treatments
- Marketing and Research run **fully autonomous** — no approval needed
- Production and Post-Production gate through your creative approval
- Three division presidents (Camdyn, Oaklyn, Aspyn) + Nelly (Legal) report to you

### Paperclip Scripts
```bash
# Setup (already done)
python scripts/paperclip/setup_company.py           # Create company
python scripts/paperclip/setup_agents.py            # Create agents
python scripts/paperclip/setup_marketing.py         # Create 16 marketing routines
python scripts/paperclip/expand_org.py              # Add new departments
python scripts/paperclip/update_all_instructions.py # Update agent instructions/titles
python scripts/paperclip/update_cos_adapter.py      # Wire CoS to briefing script

# Testing
python scripts/paperclip/test_heartbeat.py              # Test all Research agents
python scripts/paperclip/test_heartbeat.py --check-only  # Verify without triggering
python scripts/paperclip/cos_briefing.py                 # Run CoS briefing manually

# Config files
scripts/paperclip/company_id.txt       # Company UUID
scripts/paperclip/agent_ids.json       # All 16 agent UUIDs (keyed by agent name)
scripts/paperclip/routine_ids.json     # All 16 routine UUIDs
```

### Skills (22 custom skills — mapped to current 16-agent org)
Skills marked `(unassigned)` belong to roles that existed in the older 32-agent
plan but aren't wired to a current agent — Clu invokes these directly until an
agent is created.
```
~/.claude/skills/
├── ar-music/              # Camdyn — A&R creative direction, project planning
├── music-composition-skill/ # Cole — Suno v5.5 lyrics + production
├── humanizer/             # Cole, Sage & Khari — strip AI writing patterns
├── social-content/        # Sage & Khari — platform-specific captions
├── community-management/  # Dex — fan engagement strategy
├── visual-production/     # Sage & Khari — lyric cards, Ken Burns video
├── content-analytics/     # Nova — metrics, weekly digests
├── music-publicity/       # Echo — press pitches, narrative building
├── artist-management/     # Sable — career strategy, day-to-day
├── release-strategy/      # (unassigned) — rollout timeline, cadence (Clu or Oaklyn)
├── higgsfield-cinema-studio/ # (unassigned) — AI video direction (Clu direct)
├── film-tv-development/   # (unassigned) — artist IP into content
├── touring-live/          # (unassigned) — booking, tour planning
├── vawn-mix-engine/       # Onyx — 5-stage REAPER pipeline (mix/master/QC merged)
├── music-legal/           # Nelly — contracts, clearances, copyright
├── business-affairs/      # Nelly — deal negotiation, term sheets (VP role merged)
├── music-finance/         # Cipher — P&L, streaming economics
├── royalties-admin/       # Cipher — split tracking, audit (analyst role merged)
├── label-operations/      # Aspyn — KPIs, ops cadence, scaling
├── streaming-strategy/    # Nova — DSP relations, playlisting
├── brand-partnerships/    # Vibe — endorsements, co-marketing
└── sync-licensing/        # Vibe — film/TV/ad placement
```

### Production Workflow (Suno)
```
Camdyn (A&R) → Creative Brief via ar-music skill
  → Cole → Full Suno v5.5 package (lyrics + production + style prompt)
    → Clu → Creative approval
      → Generate in Suno → Stems to Onyx (mix + master + QC — single studio lead)
        → Clu → Final approval → Release
```

### Mix Engine (projects/vawn/Ai Mix Engineer/vawn-mix-engine/)
Automated 5-stage hip-hop mixing pipeline for REAPER via reapy.
```bash
python -m src.main mix config/<song>.yaml            # Full pipeline against REAPER
python -m src.main mix config/<song>.yaml --dry-run   # Analysis only (no REAPER)
python -m src.main mix config/<song>.yaml --stage 2   # Single stage
python -m src.main enumerate-live "VST3: Ozone 12 (iZotope)"  # Live param dump
```
**Signal chain:** Relay → RX 11 (individual modules) → Nectar 4 (vocals) / Neutron 5 (instruments) → Ozone 12 + TBC3 (master)
**Key features:** iZotope AI Assistants (Vocal + Mix Assistant via playback), Unmask (instruments duck for vocal), FX buses (Reverb + Delay with vocal sends), LUFS feedback loop targeting -7.5, section-aware bus automation, `stems.exclude` config for skipping stems.
**Level consistency (commit ad39457, 2026-04-14):** Boundary fade ramps on bus rides (pre 1.0s / post 0.5s), pre-Nectar lead vocal clip-gain envelope (75ms RMS, target −18 dBFS), BASS/808 BUS section ride differential, ride depth capped at ±1.2 dB, Nectar limiter wired (−1.0 dBTP), kick→bass-bus sidechain duck, signed LUFS adjustment (can attenuate hot mixes). Stage 4 (instrument processing) + bus processing now enabled by default.
**Config:** Per-song YAML in `config/`, inherits from `default_config.yaml`. Set `ai_source: "suno"` for Suno stems. Suno bass stems are 808-style — use 808 treatment, not regular BASS EQ. **Stems paths:** point to local `sessions/<song>/stems/`, not G drive (G drive folders are stale).
**Sessions:** `config/i_fell_in_love.yaml`, `config/on_my_way.yaml`, `config/on_my_way_kendrick_target.yaml` (MCA-bound, Kendrick reference)
**Mix rules:** `wiki/vawn-mix-engine/mix-rules.md` — codified 2026-04-16 from real REAPER session. **Read this BEFORE any Vawn mix work.** Covers vocal peak clamp (engine fix done), clip-gain envelope folding (engine fix done), Sculptor on bass (manual fix until engine patched), TrackFX_SetParamNormalized requiring open FX UI (REAPER bug), master fader is not for balance, MCA workflow (`--mix-only`), and per-stem RMS targets.
**Known issues:** (1) Param maps drift — `nectar4` `eq1_b5_*` and `neutron5` `eq_b5/b6_*` referenced but don't exist (silent warnings). Regenerate with `enumerate_fx_params.py`. (2) Pre-master LUFS came in at −32 on On My Way test mix, 25 dB below target — internal gain staging is too quiet; maximizer can't make it up. **Resolved 2026-04-16 by removing the over-conservative vocal peak clamp** in `src/decision_engine.py`. (3) Mix Assistant on bass stems sets Compressor 1 Band 1 ratio at 4-7:1 and enables Sculptor "Reduce Boxiness" — both crush the bass fundamental. Disable manually until engine fix lands. (4) `TrackFX_SetParamNormalized` silently fails when FX UI is closed — wrap with `TrackFX_SetOpen(true)` before set, `TrackFX_SetOpen(false)` after.

### Marketing Dispatcher
All Marketing agents use `Vawn/marketing_dispatch.py` as their process adapter. When a Paperclip routine fires, it creates an issue, wakes the agent, and the dispatcher reads the issue title to determine which script to run. The dispatcher now wraps every script execution through `dispatch_runner.run_with_retries` — see Bulletproofing Infrastructure below.
```bash
python marketing_dispatch.py --slot morning-early --dry-run  # Test locally
python marketing_dispatch.py --slot morning-early --no-retry  # Bypass retry wrapper
```

### Bulletproofing Infrastructure (built 2026-04-16)

Multi-layered resilience stack to prevent silent failures. Live dashboard at `C:\Users\rdyal\Vawn\STATUS.md` (regenerated hourly).

**Automated monitoring (Windows Task Scheduler under `\Vawn\`)**:
| Task | Cadence | Script | Purpose |
|---|---|---|---|
| `ValidateAdapters` | Daily 5:45am | `validate_adapters.py` | Smoke-tests every process-adapter config + every marketing dispatch slot. Catches argparse-level bugs before routines fire. |
| `BackendHealthProbe` | 10 min | `backend_health_probe.py` | Probes `apulustudio.onrender.com` endpoints. Writes `backend_health.json` that `post_vawn.py` reads. Pre-warms Render free tier. |
| `PaperclipRunMonitor` | 15 min | `paperclip_run_monitor.py` | Detects failed `heartbeat_runs` + stuck agents (status=error >30min). Signature detection: `claude_auth_expired`, `backend_5xx`, `missing_cron_arg`, `bluesky_auth`, `rate_limit`. |
| `StatusBoard` | Hourly | `render_status.py` | Regenerates `STATUS.md` — unified dashboard of agents, backend, auth, dispatch history, DLQ, undelivered alerts. |

**Dispatcher retry wrapper (`Vawn/dispatch_runner.py`)**:
- Up to 3 retries with exponential backoff (30s, 2min, 8min) on transient failures
- Short-circuits on non-retryable exit codes: **exit 2** (argparse/config bug), **exit 3** (circuit breaker tripped)
- Failure-signature detection auto-classifies + alerts with specific action hints
- Structured logging to `dispatch_log.jsonl`; exhausted retries write to `dead_letter.jsonl`

**Circuit breaker in `post_vawn.py`**:
Before generating Suno content, checks `backend_health.json`. If `overall == "degraded"` (and check is fresh <30min), exits 3 (retryable) without burning Suno tokens.

**Retry-aware dedup in `post_vawn.py`**:
`mark_slot_posted` tracks per-platform state. A slot only locks as `true` when ALL platforms succeed; partial failures store `{x: false, bluesky: false, instagram: true}` so next retry attempts only the failed ones.

**Alert fallback (`Vawn/alert_fallback.jsonl`)**:
When SMTP fails, `email_notify.send_notification` persists the alert to JSONL so nothing vanishes. The status dashboard shows pending count. Flush once SMTP is working:
```bash
python flush_alerts.py --clear-delivered
```

**Dead-letter queue (`Vawn/dlq.py`)**:
```bash
python dlq.py list                 # Show all DLQ entries
python dlq.py show <id>            # Full detail
python dlq.py replay <id>          # Re-run the original command
python dlq.py clear --delivered    # Remove already-replayed entries
python dlq.py stats                # Group by slot/signature/date
```

**Diagnostic commands**:
```bash
type C:\Users\rdyal\Vawn\STATUS.md              # Current snapshot
python validate_adapters.py --verbose            # Spot-check adapter configs
python paperclip_run_monitor.py --dry-run --window 1440  # Recent failures (24h)
python backend_health_probe.py                   # Force-refresh backend probe
python claude_auth_probe.py                      # Check Claude Code auth (manual — WTS can't read keychain)
```

**Common failure signatures + fixes**:
| Signature | Cause | Action |
|---|---|---|
| `claude_auth_expired` | Claude Code OAuth token expired | Run `claude /login` — all 11 claude_local agents unblock |
| `apulu_backend_5xx` | Apulu Studio handler bug or Render cold-start | Check Render logs at github.com/iamclu1914/ApuluStudio |
| `missing_cron_arg` | Adapter points directly at post_vawn.py without args | Adapter must invoke `marketing_dispatch.py`, not `post_vawn.py` |
| `bluesky_auth` | Bluesky app password wrong/expired | Regenerate at bsky.app settings, update `credentials.json` |
| `rate_limit` | Suno / X rate-limited | Self-heals via retry backoff |

### Multi-Artist Config
```
artists/
└── vawn/
    ├── config.json            # Platforms, niches, voice, schedule, paths
    ├── content_rules.json     # Symlink → pipeline/config/content_rules.json
    └── pillar_schedule.json   # Symlink → pipeline/config/pillar_context.json
```
Adding artist 2: create config dir, clone Marketing + Production agents with new tag, update CoS routing.

### Paperclip DB Access (embedded PostgreSQL)
```bash
# From paperclip/ dir, via Node.js:
node -e "const{Client}=require('./node_modules/.pnpm/pg@8.18.0/node_modules/pg');const c=new Client({host:'127.0.0.1',port:54329,user:'paperclip',password:'paperclip',database:'paperclip'});c.connect().then(async()=>{const r=await c.query('SELECT name,status FROM agents');console.table(r.rows);await c.end()})"
```

## Vault Structure
```
Apulu Universe/
├── CLAUDE.md                ← You are here (project instructions)
├── VAULT.md                 ← Entry point for vault readers (domain → hub map)
├── paperclip/               ← Paperclip installation (gitignored)
├── artists/                 ← Per-artist config (multi-tenant)
│   └── vawn/
│       ├── config.json      ← Artist config (platforms, niches, voice, schedule)
│       ├── content_rules.json
│       └── pillar_schedule.json
├── scripts/paperclip/       ← Paperclip setup & management scripts
├── docs/                    ← Design specs + implementation plans
│   └── superpowers/
│       ├── specs/
│       └── plans/
├── projects/
│   ├── vawn/                ← Junction → C:\Users\rdyal\Vawn
│   └── apulu-prompt-generator/ ← Symlink → G:\My Drive\Apulu Prompt Generator
├── pipeline/                ← Content pipeline (configurable per project)
│   ├── pipeline_config.py   ← Shared config loader + helpers
│   ├── obsidian_formatter.py← All output → Obsidian markdown
│   ├── bridge.py            ← Connects pipeline ↔ Vawn posting system
│   ├── brain/               ← Daily briefing + health monitor (CoS agent scripts)
│   ├── config/              ← vawn.json, content_rules, pillar_context, engagement_feedback
│   ├── discovery/           ← Phase 0: Apify scrapers (X, IG, TikTok, Reddit, YouTube)
│   ├── ideation/            ← Phase 2: Competitive analysis + ranked content ideas
│   ├── scripting/           ← Phase 3: Hooks, outlines, titles
│   ├── cascade/             ← Phase 4: Video → platform-specific posts
│   └── prompt-research/     ← AI video prompt research
├── journals/                ← Dated operational notes (read with coffee)
│   └── vawn/
│       ├── briefings/       ← Daily briefings (incl. Infrastructure status block)
│       ├── health/          ← Rex's daily health reports
│       └── discovery/       ← Dated discovery summaries
├── research/                ← Formal research tickets (APU-xxx) + dated research docs
│   └── vawn/
│       ├── press-opportunities/    ← Echo's weekly scans
│       ├── sync-opportunities/     ← Vibe's weekly scans
│       └── [other tickets]
├── catalogs/                ← Structured reference data (e.g., vawn-lyrics.md)
├── wiki/                    ← LLM-compiled knowledge base (topic hubs)
│   ├── _master-index.md
│   ├── infrastructure/      ← NEW: runbooks + architecture for bulletproofing stack
│   ├── vawn-mix-engine/
│   ├── vawn-project/
│   ├── apulu-prompt-generator/
│   ├── ai-filmmaking/
│   ├── design-engineering/
│   └── cross-topic/
├── wiki-archive/            ← Older/deprecated wiki content
├── skills/                  ← Packaged .skill files
├── raw/                     ← Source material (skill drafts, etc.)
└── output/                  ← General output staging
```

## Key Projects

### Apulu Prompt Generator (G:\My Drive\Apulu Prompt Generator → projects/apulu-prompt-generator/)
AI-powered music video creative direction tool. Node.js web app with server, agents, Vercel deployment. Generates style prompts for Higgsfield/Kling video production across 7 style worlds.

### Vawn (C:\Users\rdyal\Vawn\ → projects/vawn/ via junction)
First artist on Apulu Records. Brooklyn-raised, Atlanta-based hip-hop. Fully autonomous social media + music production system orchestrated by Paperclip. Oaklyn's division handles marketing (16 cron routines, 3x daily posts to 5 platforms). Camdyn's division handles A&R + studio (Suno generation via Cole, mixing via Onyx). Aspyn's division handles research, streaming strategy, analytics, and infrastructure.

**Core posting files:**
- `post_vawn.py` — Main posting engine (all 5 platforms, engagement-weighted image selection, retry-aware dedup, circuit breaker)
- `text_post_agent.py` — Text-only posts for X/Threads/Bluesky
- `marketing_dispatch.py` — Dispatcher for Sage & Khari's process adapter; reads Paperclip issue title, routes via DISPATCH_TABLE, wraps subprocess through `dispatch_runner.run_with_retries`
- `dispatch_runner.py` — Retry wrapper (3x exp backoff), signature detection, DLQ on exhaustion
- `posted_log.json` — Per-platform slot state (supports partial-success retry)

**Infrastructure monitoring (see Bulletproofing Infrastructure):**
- `paperclip_run_monitor.py` — Failed `heartbeat_runs` + stuck agents; runs every 15 min
- `backend_health_probe.py` — Apulu Studio endpoint probes; writes `backend_health.json`
- `claude_auth_probe.py` — Claude CLI auth check (manual-only; WTS can't read keychain)
- `validate_adapters.py` — Adapter config + dispatch table smoke test; runs daily 5:45am
- `render_status.py` — Regenerates `STATUS.md`; runs hourly
- `email_notify.py` — Shared SMTP helper; `APULU_GMAIL_APP_PASSWORD` env var override
- `flush_alerts.py` — Replays undelivered alerts once SMTP works
- `dlq.py` — Dead-letter queue CLI (list/show/replay/clear/stats)

**Data/state files (consumed by dashboard + briefing):**
- `STATUS.md` — Live infrastructure dashboard (regenerated hourly)
- `backend_health.json` — Current + 24h probe history
- `claude_auth_state.json` — Last probe result
- `paperclip_monitor_state.json` — Dedup state for already-reported failures
- `dispatch_log.jsonl` — All dispatch attempts (structured outcome per run)
- `dead_letter.jsonl` — Permanently-failed dispatches
- `alert_fallback.jsonl` — Alerts that couldn't send via SMTP
- `validator_state.json` — Last adapter validation status

**Other:**
- `research_company.py` — Orchestrates 4 agents (trend, audience, catalog, content calendar)
- `vawn_config.py` — Shared config, PILLAR_SCHEDULE, VAWN_PROFILE
- `config.json` — Anthropic API key + Apify token
- `credentials.json` — Bluesky direct-post creds + Apulu Studio API tokens

**Image source:** `Social_Media_Exports/Instagram_Reel_1080x1920_9-16/` — all platforms use same 9:16 images, backend passes through original dimensions (no cropping).

**Content pillar rotation:** Mon=Awareness, Tue=Lyric, Wed=BTS, Thu=Engagement, Fri=Conversion, Sat=Audience, Sun=Video

**Content rules (enforced everywhere):** Never say "stream"/"listen"/"press play". No track name references. No gospel. No generic cliches. Threads = no hashtags (uses Topics). Bluesky max 250 chars. All captions humanized via shared content_rules.json.

### Bridge (pipeline/bridge.py)
Connects the pipeline to Vawn's posting system. Runs at 6:25am daily.
- `enrich_daily_brief()` — Appends pipeline discovery trends to Vawn's daily_brief.json
- `export_pillar_context()` — Writes pillar schedule for ideation
- `export_content_rules()` — Shared humanizer rules + voice + platform constraints
- `export_engagement_scores()` — Per-pillar scores for ideation feedback
- `stage_cascade_posts()` — Queues cascade output for posting
```bash
python pipeline/bridge.py           # full run
python pipeline/bridge.py --dry-run # preview without writing
```

### Content Pipeline (pipeline/)
4-phase configurable content system. Per-project config in `config/<project>.json`.

```bash
# Discovery — scrape all platforms via Apify
python pipeline/discovery/run_all.py --project vawn
python pipeline/discovery/run_all.py --only x,tiktok

# Ideation — reads discovery, generates pillar-aware ideas with engagement feedback
python pipeline/ideation/ideation_engine.py --project vawn
python pipeline/ideation/ideation_engine.py --focus "suno ai"

# Scripting — hooks, outlines, titles (reads from ideation)
python pipeline/scripting/hooks_engine.py --from-ideation
python pipeline/scripting/outline_engine.py --from-ideation --format short
python pipeline/scripting/titles_engine.py --from-ideation

# Cascade — video → platform-specific posts (enforces content rules)
python pipeline/cascade/content_cascade.py "https://youtube.com/watch?v=..."
```

### Research Pipeline Skill
End-to-end automated: topic → YouTube search → auto-select best 5-8 → NotebookLM → analysis → optional deliverable.
```bash
python ~/.claude/skills/research-pipeline/scripts/research_pipeline.py "topic"
python ~/.claude/skills/research-pipeline/scripts/research_pipeline.py "topic" --deliverable audio
python ~/.claude/skills/research-pipeline/scripts/research_pipeline.py "topic" --deliverable slide-deck
```

### Prompt Research Pipeline (pipeline/prompt-research/)
Researches AI video prompting techniques for the Apulu Prompt Generator. Runs 2-3x/week.
```bash
# Full run (Reddit + video quality + ingest)
python pipeline/prompt-research/run_prompt_research.py

# Individual scrapers
python pipeline/prompt-research/run_prompt_research.py --only reddit
python pipeline/prompt-research/run_prompt_research.py --only video

# YouTube deep-dive (on-demand, uses NotebookLM)
python pipeline/prompt-research/run_prompt_research.py --youtube "higgsfield character consistency"

# Prompt database
python pipeline/prompt-research/prompt_db.py stats
python pipeline/prompt-research/prompt_db.py search "character consistency"
python pipeline/prompt-research/prompt_db.py export
```

### Brain Layer → Chief of Staff (pipeline/brain/ → Paperclip CoS agent)
The CoS agent replaced the standalone brain layer scripts. It runs `health_monitor.py` then `daily_briefing.py` via `scripts/paperclip/cos_briefing.py`.
- `health_monitor.py` — Checks NotebookLM auth, Apify freshness, posting failures, image supply, catalog fallbacks
- `daily_briefing.py` — Reads everything, writes one Obsidian note: today's plan, yesterday's performance, top ideation pick, discovery highlights
- `catalog_local.py` — Local lyrics database (24 tracks, 210 bars)

Output: `research/vawn/briefings/`

## Schedule (all times ET)

### Aspyn's Division — Research (Paperclip routines + WTS)
```
5:30am  PipelineDiscovery (WTS)  → Apify scrape (X, IG, TikTok, Reddit, YouTube)
5:45am  ValidateAdapters (WTS)   → Catch adapter-config bugs before 6am routines
5:50am  PipelineIdeation (WTS)   → Competitive analysis + pillar-aware ideas
6:10am  ResearchCompany (WTS)    → trend_agent, audience_agent, catalog_agent
6:25am  Bridge (WTS)             → Merges pipeline intel into daily_brief.json
7:15am  HealthMonitor (WTS)      → Pipeline health (notebook auth, Apify freshness)
7:30am  DailyBriefing (WTS)      → Daily Obsidian briefing (incl. Infrastructure block)
7:20am  EmailBriefing (WTS)      → Email briefing to clu@apuluthegod.com

Rex     system-health-check (Paperclip, daily 10am UTC / 6am ET)
Rhythm  artist-discovery-scan (Paperclip, daily 9:30am)
Rhythm  playlist-monitor (Paperclip, daily 1pm)
Rhythm  competitor-tracking (Paperclip, Fri 3pm UTC)
```

### Oaklyn's Division — Marketing (Paperclip routines via marketing_dispatch.py)
```
6:00am  Sage & Khari: hashtag-scan       → Trending hashtags for all platforms
6:30am  Sage & Khari: lyric-card         → Generate lyric card images
6:45am  Sage & Khari: video-daily        → Ken Burns video from images
8:00am  Sage & Khari: morning-early      → X + Bluesky (image + caption)
9:15am  Sage & Khari: morning-main       → TikTok + IG Reel + Threads
10:30am Sage & Khari: text-post-morning  → X + Threads + Bluesky text-only
12:00pm Sage & Khari: midday-early       → X + Bluesky
12:45pm Sage & Khari: midday-main        → TikTok + IG + Threads
3:30pm  Sage & Khari: text-post-afternoon→ X thread + Threads + Bluesky
6:00pm  Sage & Khari: evening-early      → X + Bluesky + IG slideshow Reel
8:15pm  Sage & Khari: evening-main       → TikTok + Threads

Every2h Dex: engagement-monitor → Comment monitoring + auto-reply
Every5h Dex: engagement-bot     → Bluesky likes
Sun 7am Sage & Khari: video-cinematic → Higgsfield cinematic video
Sun 2pm Sage & Khari: recycle   → Recycle top 30-day-old images

Echo: press-opportunity-scan    (Wed 2pm)
```

### Aspyn Division — Analytics, Finance, Partnerships
```
11am    Nova: content-performance-daily  → Per-post metrics
Sun 9am Nova: analytics-digest          → Weekly performance report
Sun 10pm Aspyn: weekly-ops-digest       → Weekly ops summary
Mon 12pm Cipher: streaming-revenue-check → DSP revenue reconciliation
Mon 2pm Vibe: sync-opportunity-scan     → Weekly sync licensing scan
```

### Camdyn's Division — A&R + Studio (event-driven)
Triggered when Clu creates issues in Paperclip assigned to Camdyn.
```
Camdyn → Creative Brief → Cole → Suno prompt → Clu approval → Generate
Stems → Onyx → mix/master/QC → Clu approval → Release
```

**Cultural Intelligence (Camdyn reads before every creative decision):**
- Live radar: `research/vawn/ar-intel/Cultural Radar -- 2026-04-22.md` (updated biweekly via `vawn-cultural-radar` scheduled task)
- Wiki article: `wiki/vawn-project/ar-cultural-intel.md` (compiled directives + competitor watchlist)
- Key April 2026 signal: No dominant ATL sound exists. Bass-baritone cinematic lane is structurally uncrowded. Hollywood Toray is the only named competitor. Vibecession audience rewards specificity + earned authority over polish.

### Infrastructure WTS tasks (bulletproofing stack, see section above)
```
Every 10 min  BackendHealthProbe      → Apulu Studio probes + Render pre-warm
Every 15 min  PaperclipRunMonitor     → Failed runs + stuck agents
Every hour    StatusBoard             → Regenerate C:\Users\rdyal\Vawn\STATUS.md
Daily 5:45am  ValidateAdapters        → Adapter config + dispatch table smoke test
```

### Legacy WTS tasks (infrastructure, not posting)
```
6:25am  Bridge             → pipeline/bridge.py
Wed 10am LyricAnnotation   → lyric_annotation_agent.py
Mon+Thu 6am PromptResearch  → prompt research scrapers
```

### ⚠️ WTS posting tasks DISABLED (2026-04-16)
Previously 17 WTS tasks duplicated Paperclip routines for posting. All disabled to prevent double-firing. Paperclip routines now own posting exclusively. **Do NOT re-enable** unless Paperclip is down for an extended period.
Disabled tasks: MorningEarly, MorningMain, TextPostMorning, MiddayEarly, MiddayMain, TextPostAfternoon, EveningEarly, EveningMain, HashtagScan, LyricCardAgent, VideoAgent, VideoAgentCinematic, RecycleAgent, EngagementAgent, EngagementBot, AnalyticsDigest, MetricsAgent.

## Platforms
X, Bluesky, Instagram, Threads, TikTok. **No LinkedIn. No blog posts.**

## Niches
Lyrical rap, lyrical hip-hop, Suno music, AI music, underground hip-hop, independent artist.

## APIs & Credentials
- **Anthropic**: `C:\Users\rdyal\Vawn\config.json` → `anthropic_api_key`
- **Apify**: Same file → `apify_api_token`
- **NotebookLM**: Browser auth at `~/.notebooklm/storage_state.json`
- **Apulu Studio**: `https://apulustudio.onrender.com/api` (GitHub: iamclu1914/ApuluStudio)
- **LATE/Zernio**: Posts to IG, TikTok, Threads, X via Apulu Studio backend
- **Bluesky**: Direct AT Protocol posting via `credentials.json` — 19-char app password format (NOT account password). Regenerate at bsky.app settings if Bluesky posts start failing with auth errors.
- **Gmail SMTP**: `clu@apuluthegod.com` via Google app password in `email_notify.py`. Rotate password at https://myaccount.google.com/apppasswords when it's revoked (Google does this periodically). Prefer env var `APULU_GMAIL_APP_PASSWORD` over hard-coding. When SMTP is broken, alerts queue in `alert_fallback.jsonl`; flush with `python flush_alerts.py --clear-delivered`.
- **Claude Code**: OAuth token shared by all 11 claude_local agents. When expired (signature: `Not logged in · Please run /login` in failed runs), fix by running `claude /login` in a terminal. `PaperclipRunMonitor` detects this via signature match.

## Data Flow
```
Apify scrapers → discovery JSON → ideation engine → bridge → daily_brief.json
                                                           → content_calendar.json
                                                           → post_vawn.py (captions)
                                                           → text_post_agent.py (text posts)
metrics_agent → metrics_log.json → bridge → engagement_feedback.json → ideation (loop)
```

## Humanizer
All captions run through a two-pass humanizer. Rules live in `pipeline/config/content_rules.json` (single source of truth). The posting system (`post_vawn.py`) and the pipeline (`cascade`) both read from it. Voice: anti-hype, quiet authority, T.I. authority + J. Cole depth. Brooklyn/Atlanta.

## Ruflo
Always start ruflo at the beginning of sessions in this folder:
```bash
npx ruflo@latest start
```
Use ruflo tools for: memory (`ruflo memory store/search`), agent swarms (`ruflo agent spawn`), code analysis (`ruflo analyze`), health checks (`ruflo doctor`). Config at `.claude-flow/config.yaml`.

## Conventions
- All pipeline output goes to `research/<project>/<phase>/`
- All output is dual-format: JSON (data) + Obsidian markdown (human-readable)
- Obsidian notes use frontmatter with tags, callouts, wikilinks between related notes
- File names: descriptive with date (e.g., `X Pipeline — 2026-04-08.md`)
- Use [[wikilinks]] when referencing other notes in the vault

## Wiki System
The `wiki/` folder is an LLM-compiled knowledge base. See wiki/_master-index.md for the entry point. When compiling raw material: read → categorize → write wiki article → update indexes → cross-link.
