# Apulu Records — Phase 0 + Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Install Paperclip, create the Apulu Records company skeleton with all departments and agents defined, then wire up the CoS and Research department as the first operational agents.

**Architecture:** Paperclip runs locally as a Node.js server with embedded PostgreSQL. Agents are defined via API calls and configured with either `claude_local` (reasoning tasks) or `process` (script execution) adapters. Existing Python scripts are wrapped as process agents without modification.

**Tech Stack:** Node.js 20+, pnpm 9.15+, PostgreSQL (embedded), Python 3.x (existing scripts), Paperclip API (REST, localhost:3100)

**Spec:** `docs/superpowers/specs/2026-04-09-apulu-records-paperclip-design.md`

---

## File Structure

```
Apulu Universe/
├── paperclip/                         ← Paperclip repo clone
├── scripts/
│   └── paperclip/
│       ├── setup_company.py           ← Creates company + departments via API
│       ├── setup_agents.py            ← Creates all agent definitions via API
│       ├── setup_schedules.py         ← Configures heartbeat schedules
│       └── test_heartbeat.py          ← Validates a single agent heartbeat
├── artists/
│   └── vawn/
│       ├── config.json                ← Artist-specific config (migrated from vawn_config.py)
│       ├── content_rules.json         ← Symlink to pipeline/config/content_rules.json
│       └── pillar_schedule.json       ← Symlink to pipeline/config/pillar_context.json
└── docs/superpowers/plans/            ← This file
```

---

## Task 1: Install Paperclip

**Files:**
- Create: `Apulu Universe/paperclip/` (git clone)

- [ ] **Step 1: Verify Node.js and pnpm versions**

Run:
```bash
node --version && pnpm --version
```
Expected: Node.js 20+ and pnpm 9.15+. If pnpm is missing:
```bash
npm install -g pnpm@latest
```

- [ ] **Step 2: Clone Paperclip into the project**

```bash
cd "C:/Users/rdyal/Apulu Universe"
git clone https://github.com/paperclipai/paperclip.git paperclip
```

- [ ] **Step 3: Install dependencies**

```bash
cd "C:/Users/rdyal/Apulu Universe/paperclip"
pnpm install
```

- [ ] **Step 4: Start Paperclip in development mode**

```bash
cd "C:/Users/rdyal/Apulu Universe/paperclip"
pnpm dev
```

Expected: Server starts on `http://localhost:3100`. Embedded PostgreSQL auto-created. You should see the Paperclip dashboard in a browser at that URL.

- [ ] **Step 5: Run onboarding wizard**

In a separate terminal:
```bash
cd "C:/Users/rdyal/Apulu Universe/paperclip"
npx paperclipai onboard --yes
```

This creates the initial database and authentication setup.

- [ ] **Step 6: Verify API is responsive**

```bash
curl http://localhost:3100/api/companies
```

Expected: `200 OK` with an empty array `[]` or existing companies list.

- [ ] **Step 7: Commit**

```bash
cd "C:/Users/rdyal/Apulu Universe"
echo "paperclip/" >> .gitignore
git add .gitignore
git commit -m "chore: add paperclip/ to gitignore (cloned dependency)"
```

Note: We gitignore the Paperclip clone — it's a dependency, not our code.

---

## Task 2: Create the Apulu Records Company

**Files:**
- Create: `scripts/paperclip/setup_company.py`

- [ ] **Step 1: Create the setup script directory**

```bash
mkdir -p "C:/Users/rdyal/Apulu Universe/scripts/paperclip"
```

- [ ] **Step 2: Write the company setup script**

Create `scripts/paperclip/setup_company.py`:

```python
"""
setup_company.py — Create Apulu Records company in Paperclip.
Run once. Idempotent (checks if company exists first).

Usage:
    python scripts/paperclip/setup_company.py
"""

import json
import sys
import urllib.request
import urllib.error

API_BASE = "http://localhost:3100/api"


def api(method, path, data=None):
    """Make API call to Paperclip."""
    url = f"{API_BASE}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"API Error {e.code}: {error_body}")
        sys.exit(1)


def main():
    # Check if company already exists
    companies = api("GET", "/companies")
    for c in companies:
        if c.get("name") == "Apulu Records":
            print(f"Company 'Apulu Records' already exists (id: {c['id']})")
            return c

    # Create company
    company = api("POST", "/companies", {
        "name": "Apulu Records",
        "description": (
            "AI-powered record label. Departments: Marketing, Research, "
            "Production, Post-Production. Hub-and-spoke coordination via "
            "Chief of Staff agent. First artist: Vawn."
        ),
        "budgetMonthlyCents": 11600,  # $116/month ceiling
    })

    print(f"Created company 'Apulu Records' (id: {company['id']})")
    
    # Save company ID for other scripts
    with open("scripts/paperclip/company_id.txt", "w") as f:
        f.write(company["id"])
    
    return company


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run the script (Paperclip must be running)**

```bash
cd "C:/Users/rdyal/Apulu Universe"
python scripts/paperclip/setup_company.py
```

Expected: `Created company 'Apulu Records' (id: <uuid>)`

- [ ] **Step 4: Verify in the Paperclip dashboard**

Open `http://localhost:3100` in a browser. You should see "Apulu Records" listed.

- [ ] **Step 5: Commit**

```bash
cd "C:/Users/rdyal/Apulu Universe"
git add scripts/paperclip/setup_company.py
git commit -m "feat: add Apulu Records company setup script for Paperclip"
```

---

## Task 3: Define All Agents

**Files:**
- Create: `scripts/paperclip/setup_agents.py`

- [ ] **Step 1: Write the agent setup script**

Create `scripts/paperclip/setup_agents.py`:

```python
"""
setup_agents.py — Create all Apulu Records agents in Paperclip.
Run after setup_company.py. Idempotent (skips existing agents).

Usage:
    python scripts/paperclip/setup_agents.py
"""

import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

API_BASE = "http://localhost:3100/api"
APULU_DIR = Path(r"C:\Users\rdyal\Apulu Universe")
VAWN_DIR = Path(r"C:\Users\rdyal\Vawn")
PIPELINE_DIR = APULU_DIR / "pipeline"


def api(method, path, data=None):
    """Make API call to Paperclip."""
    url = f"{API_BASE}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"API Error {e.code}: {error_body}")
        sys.exit(1)


def get_company_id():
    """Read saved company ID."""
    id_file = Path("scripts/paperclip/company_id.txt")
    if not id_file.exists():
        print("Error: Run setup_company.py first")
        sys.exit(1)
    return id_file.read_text().strip()


def get_existing_agents(company_id):
    """Get set of existing agent names."""
    agents = api("GET", f"/companies/{company_id}/agents")
    return {a["name"]: a["id"] for a in agents}


# ─── Agent Definitions ───────────────────────────────────────

AGENTS = [
    # ── Chief of Staff ──
    {
        "name": "cos",
        "role": (
            "Chief of Staff at Apulu Records. You coordinate all departments: "
            "Marketing, Research, Production, Post-Production. You synthesize "
            "the daily briefing, monitor system health, route work between "
            "departments, and escalate to the Board (CEO/Creative Director) "
            "only when: budget is exceeded, a creative decision is needed, "
            "or a system failure occurs. You manage artist routing — currently "
            "Vawn is the only artist."
        ),
        "adapterType": "claude_local",
        "adapterConfig": {
            "cwd": str(APULU_DIR),
            "model": "claude-sonnet-4-20250514",
            "promptTemplate": (
                "You are {{name}}, the {{role}} at {{company.name}}. "
                "Today's date: {{date}}. "
                "Your current task: {{taskDescription}}"
            ),
        },
        "budgetMonthlyCents": 1500,
        "reportingManager": None,  # Reports to Board
    },

    # ── Research Department ──
    {
        "name": "research-director",
        "role": (
            "Research Director at Apulu Records. You manage the Research "
            "department: prioritize research requests, synthesize discovery "
            "and ideation output, deliver intelligence packages to other "
            "departments via the Chief of Staff."
        ),
        "adapterType": "claude_local",
        "adapterConfig": {
            "cwd": str(PIPELINE_DIR),
            "model": "claude-sonnet-4-20250514",
        },
        "budgetMonthlyCents": 800,
        "reportingManager": "cos",
    },
    {
        "name": "discovery",
        "role": (
            "Discovery Agent at Apulu Records Research department. "
            "You run platform scrapers via Apify to collect trending "
            "content from X, Instagram, TikTok, Reddit, and YouTube."
        ),
        "adapterType": "process",
        "adapterConfig": {
            "command": f"python {PIPELINE_DIR / 'discovery' / 'run_all.py'} --project vawn",
            "cwd": str(PIPELINE_DIR),
            "timeoutSec": 600,
        },
        "budgetMonthlyCents": 300,
        "reportingManager": "research-director",
    },
    {
        "name": "ideation",
        "role": (
            "Ideation Agent at Apulu Records Research department. "
            "You run competitive analysis and generate pillar-aware "
            "content ideas based on discovery output and engagement feedback."
        ),
        "adapterType": "process",
        "adapterConfig": {
            "command": f"python {PIPELINE_DIR / 'ideation' / 'ideation_engine.py'} --project vawn",
            "cwd": str(PIPELINE_DIR),
            "timeoutSec": 300,
        },
        "budgetMonthlyCents": 800,
        "reportingManager": "research-director",
    },
    {
        "name": "trend",
        "role": (
            "Trend Agent at Apulu Records Research department. "
            "You run market intelligence gathering — trend analysis, "
            "audience insights, catalog research."
        ),
        "adapterType": "process",
        "adapterConfig": {
            "command": f"python {VAWN_DIR / 'research_company.py'}",
            "cwd": str(VAWN_DIR),
            "timeoutSec": 600,
        },
        "budgetMonthlyCents": 300,
        "reportingManager": "research-director",
    },
    {
        "name": "prompt-research",
        "role": (
            "Prompt Research Agent at Apulu Records Research department. "
            "You research AI video prompting techniques for the Apulu "
            "Prompt Generator shared service."
        ),
        "adapterType": "process",
        "adapterConfig": {
            "command": f"python {PIPELINE_DIR / 'prompt-research' / 'run_prompt_research.py'}",
            "cwd": str(PIPELINE_DIR),
            "timeoutSec": 600,
        },
        "budgetMonthlyCents": 300,
        "reportingManager": "research-director",
    },

    # ── Marketing Department (defined but not wired until Phase 2) ──
    {
        "name": "social-media-mgr",
        "role": (
            "Social Media Manager at Apulu Records Marketing department. "
            "You own the posting schedule, platform strategy, and content "
            "calendar for all artists. Currently managing Vawn across "
            "X, Bluesky, Instagram, Threads, and TikTok."
        ),
        "adapterType": "claude_local",
        "adapterConfig": {
            "cwd": str(VAWN_DIR),
            "model": "claude-sonnet-4-20250514",
        },
        "budgetMonthlyCents": 1000,
        "reportingManager": "cos",
        "status": "paused",  # Phase 2
    },
    {
        "name": "content-creator",
        "role": (
            "Content Creator Agent at Apulu Records Marketing department. "
            "You generate captions, text posts, and hashtags for social media. "
            "All output runs through the Humanizer shared service."
        ),
        "adapterType": "process",
        "adapterConfig": {
            "command": f"python {VAWN_DIR / 'post_vawn.py'}",
            "cwd": str(VAWN_DIR),
            "timeoutSec": 300,
        },
        "budgetMonthlyCents": 800,
        "reportingManager": "social-media-mgr",
        "status": "paused",  # Phase 2
    },
    {
        "name": "engagement",
        "role": (
            "Engagement Agent at Apulu Records Marketing department. "
            "You monitor comments, auto-reply, and manage Bluesky likes."
        ),
        "adapterType": "process",
        "adapterConfig": {
            "command": f"python {VAWN_DIR / 'engagement_agent.py'}",
            "cwd": str(VAWN_DIR),
            "timeoutSec": 300,
        },
        "budgetMonthlyCents": 500,
        "reportingManager": "social-media-mgr",
        "status": "paused",  # Phase 2
    },
    {
        "name": "visual-content",
        "role": (
            "Visual Content Agent at Apulu Records Marketing department. "
            "You create lyric cards, social video clips, and select images."
        ),
        "adapterType": "process",
        "adapterConfig": {
            "command": f"python {VAWN_DIR / 'lyric_card_agent.py'}",
            "cwd": str(VAWN_DIR),
            "timeoutSec": 300,
        },
        "budgetMonthlyCents": 500,
        "reportingManager": "social-media-mgr",
        "status": "paused",  # Phase 2
    },
    {
        "name": "analytics",
        "role": (
            "Analytics Agent at Apulu Records Marketing department. "
            "You collect metrics and score content performance across platforms."
        ),
        "adapterType": "process",
        "adapterConfig": {
            "command": f"python {VAWN_DIR / 'metrics_agent.py'}",
            "cwd": str(VAWN_DIR),
            "timeoutSec": 300,
        },
        "budgetMonthlyCents": 300,
        "reportingManager": "social-media-mgr",
        "status": "paused",  # Phase 2
    },

    # ── Production Department (defined but not wired until Phase 4) ──
    {
        "name": "producer",
        "role": (
            "Producer at Apulu Records Production department. "
            "You manage the song pipeline from concept to recorded stems."
        ),
        "adapterType": "claude_local",
        "adapterConfig": {
            "cwd": str(VAWN_DIR),
            "model": "claude-sonnet-4-20250514",
        },
        "budgetMonthlyCents": 1000,
        "reportingManager": "cos",
        "status": "paused",  # Phase 4
    },
    {
        "name": "songwriter",
        "role": (
            "Songwriter Agent at Apulu Records Production department. "
            "You write lyrics, hooks, and song structures."
        ),
        "adapterType": "claude_local",
        "adapterConfig": {
            "cwd": str(VAWN_DIR),
            "model": "claude-sonnet-4-20250514",
        },
        "budgetMonthlyCents": 1000,
        "reportingManager": "producer",
        "status": "paused",  # Phase 4
    },
    {
        "name": "beat-scout",
        "role": (
            "Beat Scout Agent at Apulu Records Production department. "
            "You source beats, evaluate producers, and generate via Suno."
        ),
        "adapterType": "claude_local",
        "adapterConfig": {
            "cwd": str(VAWN_DIR),
            "model": "claude-sonnet-4-20250514",
        },
        "budgetMonthlyCents": 500,
        "reportingManager": "producer",
        "status": "paused",  # Phase 4
    },
    {
        "name": "mv-director",
        "role": (
            "Music Video Director at Apulu Records Production department. "
            "You develop creative treatments and direct music videos. "
            "You use the Apulu Prompt Generator shared service for "
            "Higgsfield/Kling prompt generation."
        ),
        "adapterType": "claude_local",
        "adapterConfig": {
            "cwd": str(APULU_DIR),
            "model": "claude-sonnet-4-20250514",
        },
        "budgetMonthlyCents": 500,
        "reportingManager": "producer",
        "status": "paused",  # Phase 4
    },
    {
        "name": "content-calendar",
        "role": (
            "Content Calendar Agent at Apulu Records Production department. "
            "You plan release schedules and rollout strategies."
        ),
        "adapterType": "claude_local",
        "adapterConfig": {
            "cwd": str(VAWN_DIR),
            "model": "claude-sonnet-4-20250514",
        },
        "budgetMonthlyCents": 500,
        "reportingManager": "producer",
        "status": "paused",  # Phase 4
    },

    # ── Post-Production Department (defined but not wired until Phase 3) ──
    {
        "name": "chief-engineer",
        "role": (
            "Chief Engineer at Apulu Records Post-Production department. "
            "You oversee mix and master quality control and approve final delivery."
        ),
        "adapterType": "claude_local",
        "adapterConfig": {
            "cwd": str(VAWN_DIR / "Ai Mix Engineer"),
            "model": "claude-sonnet-4-20250514",
        },
        "budgetMonthlyCents": 500,
        "reportingManager": "cos",
        "status": "paused",  # Phase 3
    },
    {
        "name": "mix-engineer",
        "role": (
            "Mix Engineer at Apulu Records Post-Production department. "
            "You automate mixing in REAPER using iZotope plugins."
        ),
        "adapterType": "process",
        "adapterConfig": {
            "command": "python src/main.py",
            "cwd": str(VAWN_DIR / "Ai Mix Engineer" / "vawn-mix-engine"),
            "timeoutSec": 1800,
        },
        "budgetMonthlyCents": 500,
        "reportingManager": "chief-engineer",
        "status": "paused",  # Phase 3
    },
    {
        "name": "master-engineer",
        "role": (
            "Master Engineer at Apulu Records Post-Production department. "
            "You run Ozone 12 mastering and hit loudness targets."
        ),
        "adapterType": "process",
        "adapterConfig": {
            "command": "python src/main.py --stage master",
            "cwd": str(VAWN_DIR / "Ai Mix Engineer" / "vawn-mix-engine"),
            "timeoutSec": 1800,
        },
        "budgetMonthlyCents": 300,
        "reportingManager": "chief-engineer",
        "status": "paused",  # Phase 3
    },
    {
        "name": "qc",
        "role": (
            "QC Agent at Apulu Records Post-Production department. "
            "You run reference checks and validate output format specs."
        ),
        "adapterType": "process",
        "adapterConfig": {
            "command": "python src/main.py --stage qc",
            "cwd": str(VAWN_DIR / "Ai Mix Engineer" / "vawn-mix-engine"),
            "timeoutSec": 600,
        },
        "budgetMonthlyCents": 200,
        "reportingManager": "chief-engineer",
        "status": "paused",  # Phase 3
    },
]


def main():
    company_id = get_company_id()
    existing = get_existing_agents(company_id)

    # First pass: create all agents and collect IDs
    agent_ids = {}
    for agent_def in AGENTS:
        name = agent_def["name"]
        if name in existing:
            print(f"  Agent '{name}' already exists (id: {existing[name]})")
            agent_ids[name] = existing[name]
            continue

        # Remove reportingManager for initial creation (set after all exist)
        manager = agent_def.pop("reportingManager", None)
        status = agent_def.pop("status", None)

        result = api("POST", f"/companies/{company_id}/agents", agent_def)
        agent_ids[name] = result["id"]
        print(f"  Created agent '{name}' (id: {result['id']})")

        # Restore for second pass
        agent_def["reportingManager"] = manager
        if status:
            agent_def["status"] = status

    # Second pass: set reporting relationships and pause future-phase agents
    for agent_def in AGENTS:
        name = agent_def["name"]
        agent_id = agent_ids[name]
        updates = {}

        manager_name = agent_def.get("reportingManager")
        if manager_name and manager_name in agent_ids:
            updates["reportingManager"] = agent_ids[manager_name]

        status = agent_def.get("status")
        if status:
            updates["status"] = status

        if updates:
            api("PATCH", f"/companies/{company_id}/agents/{agent_id}", updates)
            details = []
            if "reportingManager" in updates:
                details.append(f"reports to {manager_name}")
            if "status" in updates:
                details.append(f"status={status}")
            print(f"  Updated '{name}': {', '.join(details)}")

    print(f"\nAll {len(AGENTS)} agents configured.")
    print(f"Active (Phase 0-1): cos, research-director, discovery, ideation, trend, prompt-research")
    print(f"Paused (Phase 2+): all others")

    # Save agent ID map for other scripts
    with open("scripts/paperclip/agent_ids.json", "w") as f:
        json.dump(agent_ids, f, indent=2)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the script**

```bash
cd "C:/Users/rdyal/Apulu Universe"
python scripts/paperclip/setup_agents.py
```

Expected: 19 agents created, 6 active (CoS + Research), 13 paused.

- [ ] **Step 3: Verify in the dashboard**

Open `http://localhost:3100`. Navigate to the Apulu Records company. You should see:
- 19 agents listed
- Org chart showing CoS at top, department heads reporting to CoS, agents reporting to department heads
- 13 agents showing "paused" status

- [ ] **Step 4: Commit**

```bash
cd "C:/Users/rdyal/Apulu Universe"
git add scripts/paperclip/setup_agents.py
git commit -m "feat: add agent definitions for all 19 Apulu Records agents"
```

---

## Task 4: Create the Artist Config Directory

**Files:**
- Create: `artists/vawn/config.json`
- Create: symlinks for content_rules and pillar_schedule

- [ ] **Step 1: Create the artist directory**

```bash
mkdir -p "C:/Users/rdyal/Apulu Universe/artists/vawn"
```

- [ ] **Step 2: Create the artist config file**

Create `artists/vawn/config.json`:

```json
{
  "artist_name": "Vawn",
  "artist_id": "vawn",
  "platforms": ["x", "bluesky", "instagram", "threads", "tiktok"],
  "niches": [
    "lyrical rap",
    "lyrical hip-hop", 
    "Suno music",
    "AI music",
    "underground hip-hop",
    "independent artist"
  ],
  "voice": {
    "style": "anti-hype, quiet authority",
    "references": "T.I. authority + J. Cole depth",
    "geography": "Brooklyn/Atlanta"
  },
  "schedule": {
    "discovery": "5:30am",
    "ideation": "5:50am",
    "research": "6:10am",
    "morning_early": "8:00am",
    "morning_main": "9:15am",
    "text_morning": "10:30am",
    "midday_early": "12:00pm",
    "midday_main": "12:45pm",
    "text_afternoon": "3:30pm",
    "evening_early": "6:00pm",
    "evening_main": "8:15pm"
  },
  "paths": {
    "vawn_dir": "C:\\Users\\rdyal\\Vawn",
    "images_dir": "C:\\Users\\rdyal\\Vawn\\Social_Media_Exports\\Instagram_Reel_1080x1920_9-16",
    "research_dir": "C:\\Users\\rdyal\\Apulu Universe\\research\\vawn"
  },
  "credentials_ref": "C:\\Users\\rdyal\\Vawn\\config.json"
}
```

- [ ] **Step 3: Create symlinks to existing config files**

```bash
cd "C:/Users/rdyal/Apulu Universe/artists/vawn"
ln -s "../../pipeline/config/content_rules.json" content_rules.json
ln -s "../../pipeline/config/pillar_context.json" pillar_schedule.json
```

Note: On Windows, if symlinks fail due to permissions, copy the files instead and add a comment noting the canonical source.

- [ ] **Step 4: Verify symlinks resolve**

```bash
cat "C:/Users/rdyal/Apulu Universe/artists/vawn/content_rules.json" | head -5
cat "C:/Users/rdyal/Apulu Universe/artists/vawn/pillar_schedule.json" | head -5
```

Expected: Valid JSON content from the pipeline config files.

- [ ] **Step 5: Commit**

```bash
cd "C:/Users/rdyal/Apulu Universe"
git add artists/vawn/config.json
git commit -m "feat: add Vawn artist config for multi-artist Paperclip architecture"
```

---

## Task 5: Wire the CoS Agent — Daily Briefing

This is the first agent that actually does work. The CoS replaces `pipeline/brain/daily_briefing.py` and `pipeline/brain/health_monitor.py`.

**Files:**
- Create: `scripts/paperclip/cos_briefing.py`

- [ ] **Step 1: Write the CoS briefing wrapper**

This script wraps the existing `daily_briefing.py` and `health_monitor.py` into a single CoS invocation that Paperclip can trigger.

Create `scripts/paperclip/cos_briefing.py`:

```python
"""
cos_briefing.py — Chief of Staff daily briefing wrapper.
Called by Paperclip as a process agent. Runs health checks first,
then generates the daily briefing, then reports summary back.

Usage:
    python scripts/paperclip/cos_briefing.py
"""

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

PIPELINE_BRAIN = Path(r"C:\Users\rdyal\Apulu Universe\pipeline\brain")
BRIEFINGS_DIR = Path(r"C:\Users\rdyal\Apulu Universe\research\vawn\briefings")


def run_script(script_path, label):
    """Run a Python script and capture result."""
    print(f"\n{'='*50}")
    print(f"  CoS: Running {label}...")
    print(f"{'='*50}")
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(script_path.parent),
        )
        if result.returncode == 0:
            print(f"  {label}: OK")
            if result.stdout:
                print(result.stdout[-500:])  # Last 500 chars
            return {"status": "ok", "output": result.stdout[-200:]}
        else:
            print(f"  {label}: FAILED (exit code {result.returncode})")
            print(f"  stderr: {result.stderr[-300:]}")
            return {"status": "error", "detail": result.stderr[-200:]}
    except subprocess.TimeoutExpired:
        print(f"  {label}: TIMEOUT")
        return {"status": "timeout"}
    except Exception as e:
        print(f"  {label}: EXCEPTION — {e}")
        return {"status": "exception", "detail": str(e)[:200]}


def main():
    today = date.today().isoformat()
    print(f"\n  Apulu Records — Chief of Staff Daily Briefing")
    print(f"  Date: {today}")

    # 1. Run health monitor
    health_result = run_script(
        PIPELINE_BRAIN / "health_monitor.py",
        "Health Monitor"
    )

    # 2. Run daily briefing
    briefing_result = run_script(
        PIPELINE_BRAIN / "daily_briefing.py",
        "Daily Briefing"
    )

    # 3. Summary
    summary = {
        "date": today,
        "health": health_result["status"],
        "briefing": briefing_result["status"],
        "escalation_needed": (
            health_result["status"] != "ok"
            or briefing_result["status"] != "ok"
        ),
    }

    # Check if briefing was written
    briefing_file = BRIEFINGS_DIR / f"Daily Briefing — {today}.md"
    summary["briefing_file_exists"] = briefing_file.exists()

    print(f"\n{'='*50}")
    print(f"  CoS Summary:")
    print(f"  Health: {summary['health']}")
    print(f"  Briefing: {summary['briefing']}")
    print(f"  Briefing file: {'exists' if summary['briefing_file_exists'] else 'MISSING'}")
    if summary["escalation_needed"]:
        print(f"  *** ESCALATION NEEDED — Board notification required ***")
    print(f"{'='*50}")

    # Save CoS log
    BRIEFINGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = BRIEFINGS_DIR / f"cos_log_{today}.json"
    with open(log_file, "w") as f:
        json.dump(summary, f, indent=2)

    return 0 if not summary["escalation_needed"] else 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Test the CoS briefing script standalone**

```bash
cd "C:/Users/rdyal/Apulu Universe"
python scripts/paperclip/cos_briefing.py
```

Expected: Health monitor runs, daily briefing runs, summary printed, `cos_log_<date>.json` written to briefings directory. Exit code 0 if both succeed.

- [ ] **Step 3: Update the CoS agent to use this script**

Create `scripts/paperclip/update_cos_adapter.py`:

```python
"""
update_cos_adapter.py — Switch CoS agent to process adapter
running the briefing wrapper script.

Usage:
    python scripts/paperclip/update_cos_adapter.py
"""

import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

API_BASE = "http://localhost:3100/api"
APULU_DIR = Path(r"C:\Users\rdyal\Apulu Universe")


def api(method, path, data=None):
    url = f"{API_BASE}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"API Error {e.code}: {e.read().decode()}")
        sys.exit(1)


def main():
    company_id = Path("scripts/paperclip/company_id.txt").read_text().strip()
    agent_ids = json.loads(Path("scripts/paperclip/agent_ids.json").read_text())
    cos_id = agent_ids["cos"]

    # Update CoS to use process adapter for daily briefing
    api("PATCH", f"/companies/{company_id}/agents/{cos_id}", {
        "adapterType": "process",
        "adapterConfig": {
            "command": f"python {APULU_DIR / 'scripts' / 'paperclip' / 'cos_briefing.py'}",
            "cwd": str(APULU_DIR),
            "timeoutSec": 300,
        },
    })

    print(f"Updated CoS agent to process adapter (cos_briefing.py)")


if __name__ == "__main__":
    main()
```

```bash
cd "C:/Users/rdyal/Apulu Universe"
python scripts/paperclip/update_cos_adapter.py
```

Expected: `Updated CoS agent to process adapter (cos_briefing.py)`

- [ ] **Step 4: Trigger a test heartbeat via the API**

```bash
curl -X POST http://localhost:3100/api/agents/<cos-agent-id>/heartbeat/invoke
```

Replace `<cos-agent-id>` with the actual ID from `scripts/paperclip/agent_ids.json`.

Expected: The CoS agent runs `cos_briefing.py`, health monitor executes, daily briefing generates. Check the Paperclip dashboard for the run log.

- [ ] **Step 5: Commit**

```bash
cd "C:/Users/rdyal/Apulu Universe"
git add scripts/paperclip/cos_briefing.py scripts/paperclip/update_cos_adapter.py
git commit -m "feat: wire CoS agent to daily briefing and health monitor"
```

---

## Task 6: Wire Research Department Agents

**Files:**
- Create: `scripts/paperclip/test_heartbeat.py`

- [ ] **Step 1: Write the heartbeat test script**

This script triggers each Research agent's heartbeat and verifies the expected output.

Create `scripts/paperclip/test_heartbeat.py`:

```python
"""
test_heartbeat.py — Test agent heartbeats for Phase 1 agents.
Triggers each agent and checks for expected output files.

Usage:
    python scripts/paperclip/test_heartbeat.py              # all Phase 1 agents
    python scripts/paperclip/test_heartbeat.py discovery     # single agent
"""

import json
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

API_BASE = "http://localhost:3100/api"
RESEARCH_DIR = Path(r"C:\Users\rdyal\Apulu Universe\research\vawn")


def api(method, path, data=None):
    url = f"{API_BASE}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"API Error {e.code}: {e.read().decode()}")
        return None


PHASE1_AGENTS = {
    "cos": {
        "check_file": RESEARCH_DIR / "briefings",
        "check_type": "directory_not_empty",
        "description": "Chief of Staff — daily briefing + health",
    },
    "discovery": {
        "check_file": RESEARCH_DIR / "discovery",
        "check_type": "directory_not_empty",
        "description": "Discovery — Apify platform scraping",
    },
    "ideation": {
        "check_file": RESEARCH_DIR / "ideation",
        "check_type": "directory_not_empty",
        "description": "Ideation — content ideas + competitive analysis",
    },
    "trend": {
        "check_file": Path(r"C:\Users\rdyal\Vawn\research"),
        "check_type": "directory_not_empty",
        "description": "Trend — market intelligence",
    },
    "prompt-research": {
        "check_file": RESEARCH_DIR / "prompt-research",
        "check_type": "directory_exists",
        "description": "Prompt Research — AI video techniques",
    },
}


def check_output(agent_name, config):
    """Check if agent produced expected output."""
    path = config["check_file"]
    check = config["check_type"]

    if check == "directory_not_empty":
        if path.exists() and any(path.iterdir()):
            return True, f"Output directory exists and has files: {path}"
        return False, f"Output directory empty or missing: {path}"
    elif check == "directory_exists":
        if path.exists():
            return True, f"Output directory exists: {path}"
        return False, f"Output directory missing: {path}"
    return False, "Unknown check type"


def test_agent(agent_name, company_id, agent_ids):
    """Trigger heartbeat and check result."""
    if agent_name not in agent_ids:
        print(f"  SKIP: Agent '{agent_name}' not found in agent_ids.json")
        return False

    agent_id = agent_ids[agent_name]
    config = PHASE1_AGENTS[agent_name]

    print(f"\n  Testing: {agent_name} — {config['description']}")
    print(f"  Agent ID: {agent_id}")

    # Trigger heartbeat
    result = api("POST", f"/agents/{agent_id}/heartbeat/invoke")
    if result is None:
        print(f"  FAIL: Heartbeat invocation failed")
        return False

    print(f"  Heartbeat triggered. Waiting for completion...")

    # Give the agent time to run (process agents are synchronous-ish)
    time.sleep(5)

    # Check output
    ok, msg = check_output(agent_name, config)
    status = "PASS" if ok else "FAIL"
    print(f"  {status}: {msg}")
    return ok


def main():
    company_id = Path("scripts/paperclip/company_id.txt").read_text().strip()
    agent_ids = json.loads(Path("scripts/paperclip/agent_ids.json").read_text())

    target = sys.argv[1] if len(sys.argv) > 1 else None
    agents_to_test = {target: PHASE1_AGENTS[target]} if target else PHASE1_AGENTS

    results = {}
    for name in agents_to_test:
        results[name] = test_agent(name, company_id, agent_ids)

    print(f"\n{'='*50}")
    print(f"  Phase 1 Heartbeat Test Results")
    print(f"{'='*50}")
    for name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {status}: {name}")

    all_passed = all(results.values())
    print(f"\n  Overall: {'ALL PASSED' if all_passed else 'SOME FAILED'}")
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Test the discovery agent individually**

```bash
cd "C:/Users/rdyal/Apulu Universe"
python scripts/paperclip/test_heartbeat.py discovery
```

Expected: Discovery agent heartbeat triggers, Apify scraper runs, output appears in `research/vawn/discovery/`. PASS.

Note: This requires Apify credentials to be available. If it fails due to missing credentials, that's expected — the existing script has the same requirement. The agent wrapper doesn't change that.

- [ ] **Step 3: Test the ideation agent**

```bash
python scripts/paperclip/test_heartbeat.py ideation
```

Expected: Ideation engine runs, reads discovery output, generates content ideas. PASS.

- [ ] **Step 4: Test the CoS agent**

```bash
python scripts/paperclip/test_heartbeat.py cos
```

Expected: Health monitor + daily briefing runs, briefing note written. PASS.

- [ ] **Step 5: Run all Phase 1 agents**

```bash
python scripts/paperclip/test_heartbeat.py
```

Expected: All 5 agents pass (cos, discovery, ideation, trend, prompt-research). Some may show existing output from prior runs — that's fine, we're validating that Paperclip can trigger them.

- [ ] **Step 6: Commit**

```bash
cd "C:/Users/rdyal/Apulu Universe"
git add scripts/paperclip/test_heartbeat.py
git commit -m "feat: add heartbeat test script for Phase 1 agent validation"
```

---

## Task 7: Validate Phase 1 Against Existing System

**Files:** None created — this is a validation task.

- [ ] **Step 1: Compare CoS briefing output to daily_briefing.py output**

Run the existing script directly:
```bash
cd "C:/Users/rdyal/Apulu Universe/pipeline/brain"
python daily_briefing.py
```

Then check the output note in `research/vawn/briefings/`.

Run the CoS version:
```bash
cd "C:/Users/rdyal/Apulu Universe"
python scripts/paperclip/cos_briefing.py
```

Compare: The CoS version should produce the same briefing note (it calls the same underlying script). The only addition is the `cos_log_<date>.json` summary file.

- [ ] **Step 2: Verify Research agents match existing Windows scheduled task output**

Check that the Paperclip-triggered discovery output matches what the Windows scheduled task produces:

```bash
ls -la "C:/Users/rdyal/Apulu Universe/research/vawn/discovery/"
```

The files should be the same — the agents are wrapping the exact same Python scripts.

- [ ] **Step 3: Document Phase 1 completion**

If all validations pass, Phase 1 is complete. The existing Windows scheduled tasks for discovery (5:30am), ideation (5:50am), research (6:10am), health monitor (7:15am), and daily briefing (7:30am) can now be migrated to Paperclip heartbeats.

**Do NOT disable Windows scheduled tasks yet.** Run both in parallel for 3 days per the migration rules in the spec. After 3 successful days, disable the Windows tasks one at a time.

- [ ] **Step 4: Commit any final adjustments**

```bash
cd "C:/Users/rdyal/Apulu Universe"
git add -A scripts/paperclip/ artists/
git commit -m "feat: complete Phase 0+1 — Paperclip skeleton + CoS + Research operational"
```

---

## Next Plans

After Phase 1 is validated and running in parallel for 3+ days:

- **Phase 2 plan**: Wire Marketing department agents, replace posting scheduled tasks
- **Phase 3 plan**: Wire Post-Production agents to Ai Mix Engineer
- **Phase 4 plan**: Wire Production agents, build new capabilities (beat-scout)

Each phase gets its own plan document when you're ready to start it.
