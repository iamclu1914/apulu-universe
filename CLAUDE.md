# Apulu Records — Project Instructions

## What This Is
**Apulu Records** is an AI-powered record label running on [Paperclip](https://github.com/paperclipai/paperclip) — an open-source orchestration platform for managing teams of AI agents as a business. The label has 32 agents across 15 departments, organized under 4 division presidents, and manages artist Vawn as its first client (multi-artist extensible).

## Paperclip (Agent Orchestration)
Paperclip runs at `http://localhost:3100`. Start it with:
```bash
cd "C:/Users/rdyal/Apulu Universe/paperclip" && pnpm dev
```

### Org Structure
```
Clu (Chairman of the Board / Creative Director)
│
├── Nelly — Head of Legal
│   └── Maven (VP Business Affairs)
│
├── Timbo — President of A&R
│   ├── Cole (Staff Writer & Music Producer — full Suno v5.5 workflow)
│   ├── Onyx (VP Studio / Post-Production)
│   │   ├── Freq (Mix Engineer — REAPER + iZotope)
│   │   ├── Slate (Mastering Engineer — Ozone 12)
│   │   └── Proof (QC Engineer)
│   └── Rhythm (Beat Scout) [paused — merged into Cole]
│
├── Letitia — President, Creative & Revenue
│   ├── Sage (Content Creator — captions, text posts)
│   ├── Dex (Community Manager — engagement, replies)
│   ├── Khari (Visual Producer — lyric cards, video)
│   ├── Echo (Head of Publicity — earned media, press)
│   ├── Sable (Head of Artist Management)
│   ├── Tempo (Release Strategist — rollout timing)
│   ├── Lens (Head of Visual & Music Video)
│   │   └── Arc (Head of Film & TV)
│   └── Road (Head of Touring & Live)
│
└── Nari — President, Operations & Strategy
    ├── Rex (CTO — Paperclip, APIs, infrastructure)
    ├── Cipher (CFO — P&L, DistroKid, streaming revenue)
    │   └── Ledger (Royalties Analyst)
    ├── Nova (Analytics Lead — serves all divisions)
    ├── Scout (Discovery Analyst — Apify scraping)
    ├── Indigo (Ideation Strategist)
    ├── Pulse (Trend Analyst)
    ├── Pixel (AI Prompt Researcher)
    ├── Stream (VP Streaming Strategy — DSP relations)
    ├── Ace (Head of Brand Partnerships)
    └── Vibe (Head of Sync & Licensing)
```

### Your Role (Clu)
- **Chairman**: Set company direction, final authority on all major decisions
- **Creative Director**: Approve lyrics, mixes, masters, music video treatments
- Marketing and Research run **fully autonomous** — no approval needed
- Production and Post-Production gate through your creative approval
- Four direct reports: Nelly (Legal), Timbo (A&R), Letitia (Creative & Revenue), Nari (Operations)

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
scripts/paperclip/agent_ids.json       # All 32 agent UUIDs (keyed by original role)
scripts/paperclip/routine_ids.json     # All 16 routine UUIDs
```

### Skills (22 custom skills mapped to agents)
```
~/.claude/skills/
├── ar-music/              # Timbo — A&R creative direction, project planning
├── music-composition-skill/ # Cole — Suno v5.5 lyrics + production
├── humanizer/             # Cole, Sage — strip AI writing patterns
├── social-content/        # Sage — platform-specific captions
├── community-management/  # Dex — fan engagement strategy
├── visual-production/     # Khari — lyric cards, Ken Burns video
├── content-analytics/     # Nova — metrics, weekly digests
├── music-publicity/       # Echo — press pitches, narrative building
├── artist-management/     # Sable — career strategy, day-to-day
├── release-strategy/      # Tempo — rollout timeline, cadence
├── higgsfield-cinema-studio/ # Lens — AI video direction
├── film-tv-development/   # Arc — artist IP into content
├── touring-live/          # Road — booking, tour planning
├── vawn-mix-engine/       # Onyx/Freq/Slate — 5-stage REAPER pipeline
├── music-legal/           # Nelly — contracts, clearances, copyright
├── business-affairs/      # Maven — deal negotiation, term sheets
├── music-finance/         # Cipher — P&L, streaming economics
├── royalties-admin/       # Ledger — split tracking, audit
├── label-operations/      # Nari — KPIs, ops cadence, scaling
├── streaming-strategy/    # Stream — DSP relations, playlisting
├── brand-partnerships/    # Ace — endorsements, co-marketing
└── sync-licensing/        # Vibe — film/TV/ad placement
```

### Production Workflow (Suno)
```
Timbo (A&R) → Creative Brief via ar-music skill
  → Cole → Full Suno v5.5 package (lyrics + production + style prompt)
    → Clu → Creative approval
      → Generate in Suno → Stems to Onyx → Freq (mix) → Slate (master) → Proof (QC)
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
**Sessions:** `config/i_fell_in_love.yaml`, `config/on_my_way.yaml`
**Known issues:** (1) Param maps drift — `nectar4` `eq1_b5_*` and `neutron5` `eq_b5/b6_*` referenced but don't exist (silent warnings). Regenerate with `enumerate_fx_params.py`. (2) Pre-master LUFS came in at −32 on On My Way test mix, 25 dB below target — internal gain staging is too quiet; maximizer can't make it up. Investigate before next mix.

### Marketing Dispatcher
All Marketing agents use `Vawn/marketing_dispatch.py` as their process adapter. When a Paperclip routine fires, it creates an issue, wakes the agent, and the dispatcher reads the issue title to determine which script to run.
```bash
python marketing_dispatch.py --slot morning-early --dry-run  # Test locally
```

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
├── CLAUDE.md                ← You are here
├── paperclip/               ← Paperclip installation (gitignored)
├── artists/                 ← Per-artist config (multi-tenant)
│   └── vawn/
│       ├── config.json      ← Artist config (platforms, niches, voice, schedule)
│       ├── content_rules.json
│       └── pillar_schedule.json
├── scripts/paperclip/       ← Paperclip setup & management scripts
├── docs/superpowers/specs/  ← Design specs
├── docs/superpowers/plans/  ← Implementation plans
├── projects/
│   ├── vawn/                ← Junction → C:\Users\rdyal\Vawn
│   └── apulu-prompt-generator/ ← Symlink → G:\My Drive\Apulu Prompt Generator
├── pipeline/                ← Content pipeline (configurable per project)
│   ├── pipeline_config.py   ← Shared config loader + helpers
│   ├── obsidian_formatter.py← All output → Obsidian markdown
│   ├── bridge.py            ← Connects pipeline ↔ Vawn posting system
│   ├── config/
│   │   ├── vawn.json        ← Project config (niches, accounts, keywords)
│   │   ├── bridge_config.json
│   │   ├── content_rules.json   ← Shared humanizer + voice + platform rules
│   │   ├── pillar_context.json  ← Today's pillar + 7-day rotation
│   │   └── engagement_feedback.json ← Best-performing pillar + scores
│   ├── discovery/           ← Phase 0: Apify scrapers (X, IG, TikTok, Reddit, YouTube)
│   ├── ideation/            ← Phase 2: Competitive analysis + ranked content ideas (pillar-aware)
│   ├── scripting/           ← Phase 3: Hooks, outlines, titles
│   ├── cascade/             ← Phase 4: Video → platform-specific posts (content rules enforced)
│   └── prompt-research/     ← AI video prompt research (Reddit, TikTok/X scoring, YouTube+NLM, prompt DB)
├── research/                ← All pipeline output (per project, per phase)
│   └── vawn/
│       ├── discovery/       ← Scraped data + Obsidian notes
│       ├── ideation/        ← Content ideas + competitive landscape
│       ├── scripting/       ← Hooks, outlines, titles
│       └── cascade/         ← Repurposed platform posts
├── skills/                  ← Packaged .skill files
├── wiki/                    ← LLM-compiled knowledge base
├── raw/                     ← Source material (skill drafts, etc.)
└── output/                  ← General output staging
```

## Key Projects

### Apulu Prompt Generator (G:\My Drive\Apulu Prompt Generator → projects/apulu-prompt-generator/)
AI-powered music video creative direction tool. Node.js web app with server, agents, Vercel deployment. Generates style prompts for Higgsfield/Kling video production across 7 style worlds.

### Vawn (C:\Users\rdyal\Vawn\ → projects/vawn/ via junction)
First artist on Apulu Records. Brooklyn-raised, Atlanta-based hip-hop. Fully autonomous social media + music production system orchestrated by Paperclip. Letitia's division handles marketing (16 cron routines, 3x daily posts to 5 platforms). Timbo's division handles A&R + studio (Suno generation via Cole, mixing via Onyx's team). Nari's division handles research, streaming strategy, analytics.

**Key files:**
- `post_vawn.py` — Main posting engine (all 5 platforms, engagement-weighted image selection)
- `text_post_agent.py` — Text-only posts for X/Threads/Bluesky
- `research_company.py` — Orchestrates 4 agents (trend, audience, catalog, content calendar)
- `vawn_config.py` — Shared config, PILLAR_SCHEDULE, VAWN_PROFILE
- `config.json` — Anthropic API key + Apify token

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

## Schedule (Paperclip Routines — all times ET)

### Nari's Division — Research (Paperclip heartbeats)
```
5:30am  Scout (discovery)  → Apify scrape (X, IG, TikTok, Reddit)
5:50am  Indigo (ideation)  → Competitive analysis + pillar-aware ideas
6:10am  Pulse (trend)      → trend_agent, audience_agent, catalog_agent
6:25am  Bridge             → Merges pipeline intel into daily_brief.json (Windows task)
7:15am  CoS briefing       → Health monitor + daily briefing (read with coffee)
```

### Letitia's Division — Marketing (Paperclip routines via marketing_dispatch.py)
```
6:00am  Sage: hashtag-scan       → Trending hashtags for all platforms
6:30am  Khari: lyric-card       → Generate lyric card images
6:45am  Khari: video-daily      → Ken Burns video from images
8:00am  Sage: morning-early     → X + Bluesky (image + caption)
9:15am  Sage: morning-main      → TikTok + IG Reel + Threads
10:30am Sage: text-post-morning → X + Threads + Bluesky text-only
12:00pm Sage: midday-early      → X + Bluesky
12:45pm Sage: midday-main       → TikTok + IG + Threads
3:30pm  Sage: text-post-afternoon→ X thread + Threads + Bluesky
6:00pm  Sage: evening-early     → X + Bluesky + IG slideshow Reel
8:15pm  Sage: evening-main      → TikTok + Threads
Every2h Dex: engagement-monitor → Comment monitoring + auto-reply
Every5h Dex: engagement-bot    → Bluesky likes
Sun 7am Khari: video-cinematic → Higgsfield cinematic video
Sun 9am Nova: analytics-digest → Weekly performance report
Sun 2pm Sage: recycle          → Recycle top 30-day-old images
```

### Timbo's Division — A&R + Studio (event-driven)
Triggered by creating issues in Paperclip assigned to Timbo.
```
Timbo → Creative Brief → Cole → Suno prompt → Clu approval → Generate
Stems → Onyx → Freq (mix) → Slate (master) → Proof (QC) → Clu approval
```

### Still on Windows Task Scheduler (parallel with Paperclip)
```
6:25am  Bridge             → pipeline/bridge.py
7:00am  MetricsAgent       → metrics_agent.py
Wed 10am LyricAnnotation   → lyric_annotation_agent.py
Mon+Thu 6am PromptResearch  → prompt research scrapers
All posting tasks          → Running in parallel with Paperclip routines
```

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
- **Bluesky**: Direct AT Protocol posting via credentials.json

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
