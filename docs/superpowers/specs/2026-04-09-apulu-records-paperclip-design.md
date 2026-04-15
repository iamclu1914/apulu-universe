# Apulu Records — Paperclip Integration Design Spec

**Date**: 2026-04-09  
**Status**: Draft  
**Author**: Claude + rdyal  

---

## 1. Overview

Apulu Records is an AI-powered record label built on [Paperclip](https://github.com/paperclipai/paperclip), an open-source orchestration platform for managing teams of AI agents as an autonomous business. The label uses Paperclip's company structure, budgeting, scheduling, and audit capabilities to coordinate departments that handle marketing, research, music production, post-production, and creative direction.

### Business Model

- **Primary**: Artist services label — builds artist careers through automated marketing, content, and production
- **Extensible to**: Production house (license the pipeline) and tech-enabled label (traditional functions, AI execution)
- **Sequence**: Build for Vawn (artist 1) → prove the model → add artists → license the stack

### Human Role

The user operates as **CEO + Creative Director** (Board level):
- Sets strategy, approves budgets, reviews weekly reports
- Creative gates: approves lyrics, mixes, masters, music video treatments, brand voice decisions
- Daily touchpoint: reads the morning briefing, intervenes only when creative decisions are needed
- Marketing and Research run fully autonomous — no approval needed

---

## 2. Organizational Structure

### Architecture: Hub-and-Spoke

Flat departments coordinated by a Chief of Staff (CoS) agent. The CoS handles cross-department handoffs, daily briefing synthesis, health monitoring, and artist routing. Departments report to the CoS for coordination; creative output gates through the Board (user).

```
APULU RECORDS (Paperclip Company: apulu-records)
│
│  Board: User (CEO + Creative Director)
│
├── Chief of Staff (CoS Agent)
│   ├── Cross-department coordination & handoffs
│   ├── Daily briefing synthesis
│   ├── Health monitoring
│   ├── Artist routing (Vawn now, extensible)
│   └── Escalation: budget exceeded, creative decision needed, system failure
│
├── MARKETING DEPARTMENT
│   ├── Social Media Manager (department head)
│   ├── Content Creator Agent
│   ├── Engagement Agent
│   ├── Visual Content Agent
│   └── Analytics Agent
│
├── RESEARCH DEPARTMENT
│   ├── Research Director (department head)
│   ├── Discovery Agent
│   ├── Ideation Agent
│   ├── Trend Agent
│   └── Prompt Research Agent
│
├── PRODUCTION DEPARTMENT
│   ├── Producer (department head)
│   ├── Songwriter Agent
│   ├── Beat Scout Agent
│   ├── Music Video Director Agent
│   └── Content Calendar Agent
│
├── POST-PRODUCTION DEPARTMENT
│   ├── Chief Engineer (department head)
│   ├── Mix Engineer Agent
│   ├── Master Engineer Agent
│   └── QC Agent
│
└── SHARED SERVICES (no department budget)
    ├── Apulu Prompt Generator (Higgsfield/Kling prompt generation)
    ├── Humanizer (content_rules.json enforcement)
    └── Bridge (data routing between departments)
```

### Department Responsibilities

**Marketing**: Social media posting (3x daily across 5 platforms), engagement monitoring, lyric cards, social video clips, metrics tracking. Fully autonomous — no creative approval needed. Enforces content rules via shared Humanizer service.

**Research**: Platform scraping via Apify, competitive analysis, content ideation (pillar-aware), market intelligence, AI video prompt technique research. Produces intelligence consumed by Marketing and Production. Own schedule, own cadence.

**Production**: Songwriting (lyrics, hooks, structures), beat sourcing, music video creative direction, release planning. Event-driven — activated when a song enters the pipeline. All creative output gates through Board approval.

**Post-Production**: Mixing (REAPER + iZotope automation), mastering (Ozone 12), quality control (reference checking, format validation). Event-driven — activated when Production hands off recorded stems. Mix and master gate through Board approval.

**Shared Services**: Tools consumed by departments, not organizational units. No budget, no agents, no heartbeats. Costs roll up to the requesting department.

---

## 3. Agent Registry

### Agent Definitions

| Agent ID | Department | Runtime | Budget/mo | Heartbeat | Role |
|---|---|---|---|---|---|
| `cos` | — | Claude Code | $15 | 6:00am daily + event | Coordination, briefing, health, routing |
| `social-media-mgr` | Marketing | Claude Code | $10 | 7:30am daily | Platform strategy, posting schedule |
| `content-creator` | Marketing | Bash/Python | $8 | 8am/12pm/6pm | Captions, text posts, hashtags |
| `engagement` | Marketing | Bash/Python | $5 | Every 2h | Comment monitoring, auto-reply, likes |
| `visual-content` | Marketing | Bash/Python | $5 | 6:30am daily | Lyric cards, video clips, image selection |
| `analytics` | Marketing | Bash/Python | $3 | 7:00am daily | Metrics collection, performance scoring |
| `research-director` | Research | Claude Code | $8 | 5:15am daily | Research prioritization, output synthesis |
| `discovery` | Research | Bash/Python | $3 | 5:30am daily | Apify scraping (X, IG, TikTok, Reddit) |
| `ideation` | Research | Claude Code | $8 | 5:50am daily | Content ideas, competitive analysis |
| `trend` | Research | Bash/Python | $3 | 6:10am daily | Market intelligence, audience insights |
| `prompt-research` | Research | Bash/Python | $3 | Mon/Wed/Thu 6am | AI video technique research |
| `producer` | Production | Claude Code | $10 | Event-driven | Song pipeline management |
| `songwriter` | Production | Claude Code | $10 | Event-driven | Lyrics, hooks, structures |
| `beat-scout` | Production | Claude Code | $5 | Weekly scan | Beat sourcing, Suno generation |
| `mv-director` | Production | Claude Code | $5 | Event-driven | Music video creative direction |
| `content-calendar` | Production | Claude Code | $5 | Weekly | Release planning, rollout strategy |
| `mix-engineer` | Post-Prod | Bash/Python | $5 | Event-driven | REAPER + iZotope automation |
| `master-engineer` | Post-Prod | Bash/Python | $3 | Event-driven | Ozone 12 mastering |
| `qc` | Post-Prod | Bash/Python | $2 | Event-driven | Reference checking, format validation |

### Budget Summary

| Department | Monthly Ceiling | Notes |
|---|---|---|
| Chief of Staff | $15 | Coordinates everything |
| Marketing | $31 | Highest volume — 3x daily |
| Research | $25 | Daily scheduled + periodic |
| Production | $35 | Claude Code heavy, but event-driven (actual ~$15-20) |
| Post-Production | $10 | Only active during song pipeline |
| **Total ceiling** | **$116/mo** | **Actual estimate: ~$60-80** due to event-driven agents idling |

### Runtime Selection

- **Claude Code**: Agents needing reasoning, creativity, complex decisions (CoS, songwriter, ideation, producer)
- **Bash/Python**: Agents executing existing scripts with minimal decision-making (discovery, content-creator, mix-engineer)

---

## 4. Data Flow & Handoffs

### Daily Intelligence Flow (5:30am - 7:30am)

```
Research Dept                    CoS                        Marketing Dept
─────────────                   ───                        ──────────────
Discovery ──scrape──→                                      
Ideation ──ideas───→  synthesized intel  ──→ Social Media Manager
Trend ────trends──→   package            ──→ Content Creator
                                         ──→ Visual Content
                                         ──→ Daily Briefing → Board (You)
```

### Content Publishing Flow (8:00am - 8:15pm)

Fully autonomous — no approval gates.

```
Content Creator → Humanizer (shared svc) → Platform APIs
Visual Content → post schedule → publish
Engagement Agent → monitor → auto-reply
Analytics Agent → metrics → feedback loop → Research
```

### Song Production Flow (event-driven)

```
Songwriter ──lyrics──→ BOARD APPROVAL ──→ (recording happens)
Beat Scout ──beats───→ BOARD APPROVAL      │
                                      stems uploaded
                                           │
                                      CoS routes to Post-Production
                                           │
                              Mix Engineer ──mix──→ Chief Engineer QC
                              Master Engineer ──master──→ BOARD APPROVAL
                                                              │
                                                         CoS notifies Marketing
                                                         "new release incoming"
```

### Music Video Flow (event-driven)

```
MV Director ──request──→ Prompt Generator (shared svc)
            ←──prompts──
MV Director ──treatment──→ BOARD APPROVAL ──→ render
                                                │
                                           CoS routes clips to Marketing
```

### Approval Rules

```yaml
approval_rules:
  - type: "creative_output"
    departments: [production, post-production]
    outputs: [lyrics, mix, master, music_video_treatment]
    requires: "board_approval"

  - type: "content_publishing"
    departments: [marketing]
    outputs: [social_post, text_post, engagement_reply]
    requires: "none"

  - type: "budget_alert"
    condition: "agent_budget > 80%"
    requires: "board_notification"

  - type: "system_failure"
    condition: "health_check_failed"
    requires: "cos_escalation"
```

### Feedback Loops

- Analytics → Research: content performance informs ideation
- QC → Mix Engineer: reference check failures trigger remix
- CoS → Board: weekly summary, budget alerts, anomalies

---

## 5. Multi-Artist Architecture

### Design Principle

Single Paperclip company, config-driven artist isolation. Some departments are shared (Research, Post-Production, CoS), others are duplicated per artist (Marketing, Production). This avoids agent sprawl while maintaining complete data isolation.

### Shared vs. Per-Artist

| Component | Per-Artist? | Rationale |
|---|---|---|
| Marketing agents | Yes | Different voice, platforms, audience, schedule |
| Production agents | Yes | Different creative direction, different songs |
| Research agents | No | Market intelligence benefits all artists |
| Post-Production agents | No | Same REAPER/iZotope chain, different input stems |
| CoS | No | Routes by artist tag, single coordinator |
| Shared services | No | Tools, not departments |
| Config/data | Yes | Complete isolation per artist |

### Artist Config Structure

```
artists/
├── vawn/
│   ├── config.json            (API keys, platform accounts)
│   ├── content_rules.json     (voice, banned words, humanizer rules)
│   ├── pillar_schedule.json   (content rotation)
│   └── catalog/               (lyrics, tracks, 210 bars)
└── <artist2>/
    ├── config.json
    ├── content_rules.json
    ├── pillar_schedule.json
    └── catalog/
```

### Adding a New Artist (Playbook)

1. Create artist config directory with voice/rules/platforms
2. Clone Marketing department agents with new artist tag
3. Clone Production department agents with new artist tag
4. CoS adds artist to routing table
5. Research includes artist's niche in discovery queries
6. No infrastructure changes, no new departments

### Cost Impact Per Additional Artist

~$45-55/mo ceiling (Marketing $31 + Production $35, minus shared agents). Actual spend lower due to event-driven idling.

---

## 6. Existing Code Mapping

### Scripts → Agent Mapping

| Existing Script | Maps To Agent | Migration |
|---|---|---|
| `post_vawn.py` | `content-creator` | Wrap as Bash agent (image+caption posts) |
| `text_post_agent.py` | `content-creator` | Wrap as Bash agent (text-only posts, same agent, different mode) |
| `engagement_agent.py` | `engagement` | Wrap as Bash agent |
| `engagement_bot.py` | `engagement` | Merge into engagement |
| `lyric_card_agent.py` | `visual-content` | Wrap as Bash agent |
| `video_agent.py` | `visual-content` | Wrap as Bash agent |
| `metrics_agent.py` | `analytics` | Wrap as Bash agent |
| `analytics_agent.py` | `analytics` | Merge into analytics |
| `scan_hashtags.py` | `content-creator` | Subtask of content-creator |
| `research_company.py` | `research-director` | Orchestrator becomes dept head |
| `pipeline/discovery/` | `discovery` | Wrap as Bash agent |
| `pipeline/ideation/` | `ideation` | Wrap as Claude Code agent |
| `pipeline/scripting/` | `producer` | Subtask of producer |
| `pipeline/cascade/` | `content-creator` | Subtask of content-creator |
| `pipeline/prompt-research/` | `prompt-research` | Wrap as Bash agent |
| `pipeline/brain/daily_briefing.py` | `cos` | Absorbed into CoS |
| `pipeline/brain/health_monitor.py` | `cos` | Absorbed into CoS |
| `pipeline/brain/catalog_local.py` | `songwriter` | Subtask of songwriter |
| `pipeline/bridge.py` | `cos` | Absorbed into CoS |
| `Ai Mix Engineer/` | `mix-engineer` + `master-engineer` | Split across two agents |
| `Apulu Prompt Generator/` | Shared service | No agent — called via API |
| `vawn_config.py` | `artists/vawn/config.json` | Migrate to artist config |
| `content_rules.json` | `artists/vawn/content_rules.json` | Move to artist config |
| `recycle_agent.py` | `content-creator` | Subtask — recycles old content |
| `lyric_annotation_agent.py` | `songwriter` | Subtask of songwriter |

### Windows Scheduled Tasks → Paperclip Heartbeats

All 26 Windows scheduled tasks will be replaced by Paperclip agent heartbeats. The heartbeat schedule in the Agent Registry (Section 3) maps 1:1 to the current task schedule.

---

## 7. Migration Plan

### Guiding Principle

Never break the working system. Run Paperclip agents in parallel with existing scheduled tasks, validate output matches, then cut over.

### Phase 0: Install & Skeleton (Day 1-2)

- Clone Paperclip, run locally
- Create `apulu-records` company with full org structure
- Define all agent roles, budgets, heartbeats
- No agents execute — skeleton only
- **Exit criteria**: Paperclip dashboard shows all departments and agents

### Phase 1: CoS + Research (Week 1)

- Wire Research agents to existing pipeline scripts
- Wire CoS to replace `daily_briefing.py` and `health_monitor.py`
- Keep Windows Task Scheduler running for Marketing/Production
- **Validation**: CoS daily briefing matches `daily_briefing.py` output
- **Rollback**: Re-enable brain layer scripts

### Phase 2: Marketing (Week 2-3)

- Wire Marketing agents to existing posting scripts
- Paperclip heartbeats replace Windows Task Scheduler for posting
- Run in parallel with existing scheduler for 3 days
- Cut over when outputs match
- **Validation**: Same posts, same times, same platforms, same metrics
- **Rollback**: Re-enable Windows scheduled tasks

### Phase 3: Post-Production (Week 3-4)

- Wire Post-Production agents to Ai Mix Engineer
- Event-driven — CoS triggers on stem upload
- **Validation**: Process test song, compare to manual run
- **Rollback**: Run Ai Mix Engineer manually

### Phase 4: Production (Week 4+)

- Wire songwriter to catalog system
- Build beat-scout agent (new capability)
- Wire mv-director to Prompt Generator
- Wire content-calendar to existing content_agent
- **Validation**: End-to-end song pipeline test
- **Rollback**: Manual production workflow

### Migration Rules

1. Never disable a Windows scheduled task until its Paperclip agent has succeeded for 3+ days
2. Each phase has a rollback plan (re-enable the scheduled task)
3. CoS daily briefing includes migration status
4. Board approves each phase cutover

---

## 8. Technical Requirements

### Infrastructure

- **Paperclip**: Node.js 20+, pnpm 9.15+, PostgreSQL (embedded for local dev)
- **Existing**: Python 3.x, Windows Task Scheduler, REAPER + iZotope
- **APIs**: Anthropic, Apify, AT Protocol (Bluesky), Apulu Studio (Render)
- **Local**: All agents run locally on user's Windows machine

### Repository Structure

```
Apulu Universe/
├── paperclip/                    ← Paperclip installation
│   ├── companies/
│   │   └── apulu-records/        ← Company config
│   │       ├── org.yaml          ← Org structure, departments, roles
│   │       ├── agents/           ← Agent definitions
│   │       ├── budgets/          ← Per-agent budget configs
│   │       └── approval-rules/   ← Creative gates, escalation rules
│   └── ...
├── artists/                      ← Per-artist config (multi-tenant)
│   └── vawn/
│       ├── config.json
│       ├── content_rules.json
│       ├── pillar_schedule.json
│       └── catalog/
├── projects/
│   ├── vawn/                     ← Existing Vawn code (junction)
│   └── apulu-prompt-generator/   ← Existing Prompt Generator (symlink)
├── pipeline/                     ← Existing pipeline code
├── research/                     ← Existing research output
└── ...existing structure
```

### Future Departments (Not Built Now)

- **Distribution**: When DistroKid integration needs automation beyond a button press
- **A&R**: When artist 2 arrives and scouting becomes a function (skill exists)
- **Finance**: When there's revenue to track

---

## 9. Success Criteria

- All 26 Windows scheduled tasks replaced by Paperclip heartbeats
- Daily briefing produced by CoS agent, not standalone script
- Marketing posts autonomously without approval delays
- Creative output (lyrics, mixes, masters) gates through Board approval in Paperclip UI
- Budget tracking visible per agent and per department
- Adding artist 2 requires only config + agent cloning, no structural changes
- Full audit trail of all agent actions in Paperclip
