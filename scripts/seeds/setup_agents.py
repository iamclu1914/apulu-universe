#!/usr/bin/env python3
"""
setup_agents.py -- Define all 19 Apulu Records agents in Paperclip.

Usage:
    python scripts/paperclip/setup_agents.py

Reads company_id from scripts/paperclip/company_id.txt
Saves all agent IDs to scripts/paperclip/agent_ids.json

API notes (discovered via exploration):
- POST /api/companies/{companyId}/agents  -- create agent
- PATCH /api/agents/{agentId}             -- update (reportsTo, status, title)
- GET  /api/companies/{companyId}/agents  -- list agents
- DELETE /api/agents/{agentId}            -- delete agent
- role field is an enum: ceo|cto|cmo|cfo|engineer|designer|pm|qa|devops|researcher|general
- title field accepts free text (used for human-readable role description)
- reportsTo field accepts a UUID agent ID
- status: "paused" | "idle"
"""

import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

BASE_URL = "http://localhost:3100/api"
SCRIPT_DIR = Path(__file__).parent
COMPANY_ID_FILE = SCRIPT_DIR / "company_id.txt"
AGENT_IDS_FILE = SCRIPT_DIR / "agent_ids.json"

# Active in Phase 0-1; all others will be paused
PHASE_0_1_AGENTS = {"cos", "research-director", "discovery", "ideation", "trend", "prompt-research"}


# ---------------------------------------------------------------------------
# Agent definitions
# Each entry:
#   name           -- unique slug
#   role           -- Paperclip enum role (best fit)
#   title          -- human-readable description (stored in title field)
#   adapterType    -- "claude_local" | "process"
#   adapterConfig  -- dict (cwd required; command required for process)
#   budget         -- budgetMonthlyCents (int)
#   manager        -- name of manager agent (resolved to ID after creation)
# ---------------------------------------------------------------------------

AGENT_DEFINITIONS = [
    # ── Chief of Staff ────────────────────────────────────────────────────
    {
        "name": "cos",
        "role": "ceo",
        "title": "Chief of Staff. Coordinates all departments at Apulu Records -- Research, Marketing, Production, and Post-Production. Hub-and-spoke orchestrator between the Board and department heads.",
        "adapterType": "claude_local",
        "adapterConfig": {"cwd": "C:/Users/rdyal/Apulu Universe"},
        "budget": 1500,
        "manager": None,
    },

    # ── Research Department ───────────────────────────────────────────────
    {
        "name": "research-director",
        "role": "researcher",
        "title": "Research Department head. Directs all intelligence-gathering and content strategy research for Apulu Records. Reports to Chief of Staff.",
        "adapterType": "claude_local",
        "adapterConfig": {"cwd": "C:/Users/rdyal/Apulu Universe/pipeline"},
        "budget": 800,
        "manager": "cos",
    },
    {
        "name": "discovery",
        "role": "researcher",
        "title": "Discovery agent. Runs Apify scrapers across X, Instagram, TikTok, Reddit to surface trending content and competitive intelligence. Reports to Research Director.",
        "adapterType": "process",
        "adapterConfig": {
            "command": "python C:/Users/rdyal/Apulu Universe/pipeline/discovery/run_all.py --project vawn",
            "cwd": "C:/Users/rdyal/Apulu Universe/pipeline",
        },
        "budget": 300,
        "manager": "research-director",
    },
    {
        "name": "ideation",
        "role": "researcher",
        "title": "Ideation agent. Reads discovery data and generates pillar-aware content ideas with engagement feedback scoring. Reports to Research Director.",
        "adapterType": "process",
        "adapterConfig": {
            "command": "python C:/Users/rdyal/Apulu Universe/pipeline/ideation/ideation_engine.py --project vawn",
            "cwd": "C:/Users/rdyal/Apulu Universe/pipeline",
        },
        "budget": 800,
        "manager": "research-director",
    },
    {
        "name": "trend",
        "role": "researcher",
        "title": "Trend agent. Orchestrates 4 research sub-agents (trend, audience, catalog, content calendar) to build Vawn's daily brief. Reports to Research Director.",
        "adapterType": "process",
        "adapterConfig": {
            "command": "python C:/Users/rdyal/Vawn/research_company.py",
            "cwd": "C:/Users/rdyal/Vawn",
        },
        "budget": 300,
        "manager": "research-director",
    },
    {
        "name": "prompt-research",
        "role": "researcher",
        "title": "Prompt Research agent. Researches AI video prompting techniques for the Apulu Prompt Generator via Reddit scrapers and video quality scorers. Reports to Research Director.",
        "adapterType": "process",
        "adapterConfig": {
            "command": "python C:/Users/rdyal/Apulu Universe/pipeline/prompt-research/run_prompt_research.py",
            "cwd": "C:/Users/rdyal/Apulu Universe/pipeline",
        },
        "budget": 300,
        "manager": "research-director",
    },

    # ── Marketing Department (paused) ─────────────────────────────────────
    {
        "name": "social-media-mgr",
        "role": "cmo",
        "title": "Social Media Manager. Marketing Department head. Oversees all social media activity across X, Instagram, TikTok, Threads, and Bluesky for Vawn. Reports to Chief of Staff.",
        "adapterType": "claude_local",
        "adapterConfig": {"cwd": "C:/Users/rdyal/Vawn"},
        "budget": 1000,
        "manager": "cos",
    },
    {
        "name": "content-creator",
        "role": "designer",
        "title": "Content Creator agent. Runs the main posting engine -- posts to all 5 platforms 3x daily with engagement-weighted image selection. Reports to Social Media Manager.",
        "adapterType": "process",
        "adapterConfig": {
            "command": "python C:/Users/rdyal/Vawn/post_vawn.py",
            "cwd": "C:/Users/rdyal/Vawn",
        },
        "budget": 800,
        "manager": "social-media-mgr",
    },
    {
        "name": "engagement",
        "role": "general",
        "title": "Engagement agent. Monitors comments across platforms and auto-replies to fan interactions every 2 hours. Reports to Social Media Manager.",
        "adapterType": "process",
        "adapterConfig": {
            "command": "python C:/Users/rdyal/Vawn/engagement_agent.py",
            "cwd": "C:/Users/rdyal/Vawn",
        },
        "budget": 500,
        "manager": "social-media-mgr",
    },
    {
        "name": "visual-content",
        "role": "designer",
        "title": "Visual Content agent. Generates lyric card assets and visual content for Vawn's social presence. Reports to Social Media Manager.",
        "adapterType": "process",
        "adapterConfig": {
            "command": "python C:/Users/rdyal/Vawn/lyric_card_agent.py",
            "cwd": "C:/Users/rdyal/Vawn",
        },
        "budget": 500,
        "manager": "social-media-mgr",
    },
    {
        "name": "analytics",
        "role": "general",
        "title": "Analytics agent. Tracks performance metrics across all platforms, logs to metrics_log.json, feeds engagement feedback loop. Reports to Social Media Manager.",
        "adapterType": "process",
        "adapterConfig": {
            "command": "python C:/Users/rdyal/Vawn/metrics_agent.py",
            "cwd": "C:/Users/rdyal/Vawn",
        },
        "budget": 300,
        "manager": "social-media-mgr",
    },

    # ── Production Department (paused) ────────────────────────────────────
    {
        "name": "producer",
        "role": "pm",
        "title": "Producer. Production Department head. Oversees songwriting, beat scouting, music video direction, and content calendar for Vawn. Reports to Chief of Staff.",
        "adapterType": "claude_local",
        "adapterConfig": {"cwd": "C:/Users/rdyal/Vawn"},
        "budget": 1000,
        "manager": "cos",
    },
    {
        "name": "songwriter",
        "role": "designer",
        "title": "Songwriter agent. AI lyric and song concept development aligned with Vawn's lyrical hip-hop voice and Brooklyn/Atlanta aesthetic. Reports to Producer.",
        "adapterType": "claude_local",
        "adapterConfig": {"cwd": "C:/Users/rdyal/Vawn"},
        "budget": 1000,
        "manager": "producer",
    },
    {
        "name": "beat-scout",
        "role": "researcher",
        "title": "Beat Scout agent. Researches and evaluates beats, production trends, and sonic direction for Vawn's releases. Reports to Producer.",
        "adapterType": "claude_local",
        "adapterConfig": {"cwd": "C:/Users/rdyal/Vawn"},
        "budget": 500,
        "manager": "producer",
    },
    {
        "name": "mv-director",
        "role": "designer",
        "title": "Music Video Director agent. Creative direction for AI-generated music videos using Higgsfield/Kling. Works with the Apulu Prompt Generator. Reports to Producer.",
        "adapterType": "claude_local",
        "adapterConfig": {"cwd": "C:/Users/rdyal/Apulu Universe"},
        "budget": 500,
        "manager": "producer",
    },
    {
        "name": "content-calendar",
        "role": "pm",
        "title": "Content Calendar agent. Plans and schedules Vawn's release cadence, pillar rotation, and cross-platform content strategy. Reports to Producer.",
        "adapterType": "claude_local",
        "adapterConfig": {"cwd": "C:/Users/rdyal/Vawn"},
        "budget": 500,
        "manager": "producer",
    },

    # ── Post-Production Department (paused) ───────────────────────────────
    {
        "name": "chief-engineer",
        "role": "cto",
        "title": "Chief Engineer. Post-Production Department head. Oversees AI mixing, mastering, and quality control for Vawn's audio releases. Reports to Chief of Staff.",
        "adapterType": "claude_local",
        "adapterConfig": {"cwd": "C:/Users/rdyal/Vawn/Ai Mix Engineer"},
        "budget": 500,
        "manager": "cos",
    },
    {
        "name": "mix-engineer",
        "role": "engineer",
        "title": "Mix Engineer agent. Runs the AI mixing pipeline on Vawn's stems to produce balanced, radio-ready mixes. Reports to Chief Engineer.",
        "adapterType": "process",
        "adapterConfig": {
            "command": "python src/main.py",
            "cwd": "C:/Users/rdyal/Vawn/Ai Mix Engineer/vawn-mix-engine",
        },
        "budget": 500,
        "manager": "chief-engineer",
    },
    {
        "name": "master-engineer",
        "role": "engineer",
        "title": "Mastering Engineer agent. Applies final mastering stage to Vawn's mixes for loudness, clarity, and distribution-ready output. Reports to Chief Engineer.",
        "adapterType": "process",
        "adapterConfig": {
            "command": "python src/main.py --stage master",
            "cwd": "C:/Users/rdyal/Vawn/Ai Mix Engineer/vawn-mix-engine",
        },
        "budget": 300,
        "manager": "chief-engineer",
    },
    {
        "name": "qc",
        "role": "qa",
        "title": "Quality Control agent. Validates final audio output against technical specs before release -- checks for clipping, artifacts, and metadata compliance. Reports to Chief Engineer.",
        "adapterType": "process",
        "adapterConfig": {
            "command": "python src/main.py --stage qc",
            "cwd": "C:/Users/rdyal/Vawn/Ai Mix Engineer/vawn-mix-engine",
        },
        "budget": 200,
        "manager": "chief-engineer",
    },
]


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def api_get(path: str) -> object:
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def api_post(path: str, payload: dict) -> dict:
    url = f"{BASE_URL}{path}"
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def api_patch(path: str, payload: dict) -> dict:
    url = f"{BASE_URL}{path}"
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="PATCH",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        return {"_error": True, "status": exc.code, "body": body}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # 1. Read company ID
    if not COMPANY_ID_FILE.exists():
        print(f"ERROR: {COMPANY_ID_FILE} not found. Run setup_company.py first.")
        sys.exit(1)
    company_id = COMPANY_ID_FILE.read_text().strip()
    print(f"Company ID: {company_id}")

    # 2. Fetch existing agents (skip already-created ones)
    print("\nChecking existing agents ...")
    try:
        existing_raw = api_get(f"/companies/{company_id}/agents")
    except urllib.error.URLError as exc:
        print(f"ERROR: Could not reach Paperclip API -- {exc}")
        sys.exit(1)

    existing_agents = existing_raw if isinstance(existing_raw, list) else existing_raw.get("data", [])
    existing_by_name = {a["name"]: a for a in existing_agents}
    print(f"  Found {len(existing_by_name)} existing agent(s): {list(existing_by_name.keys()) or 'none'}")

    # 3. Create agents (skip if already exist)
    agent_ids: dict[str, str] = {}  # name -> id

    # Pre-populate IDs for any already-existing agents
    for name, agent in existing_by_name.items():
        agent_ids[name] = agent["id"]

    print(f"\nCreating {len(AGENT_DEFINITIONS)} agents ...")
    for defn in AGENT_DEFINITIONS:
        name = defn["name"]

        if name in existing_by_name:
            print(f"  [SKIP] {name} already exists (id={agent_ids[name]})")
            continue

        # Build adapterConfig
        adapter_config = dict(defn["adapterConfig"])

        payload = {
            "name": name,
            "role": defn["role"],
            "title": defn["title"],
            "adapterType": defn["adapterType"],
            "adapterConfig": adapter_config,
            "budgetMonthlyCents": defn["budget"],
        }

        try:
            result = api_post(f"/companies/{company_id}/agents", payload)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode()
            print(f"  [FAIL] {name}: HTTP {exc.code} -- {body}")
            continue
        except urllib.error.URLError as exc:
            print(f"  [FAIL] {name}: {exc}")
            continue

        if "id" not in result:
            print(f"  [FAIL] {name}: unexpected response -- {json.dumps(result)}")
            continue

        agent_id = result["id"]
        agent_ids[name] = agent_id
        print(f"  [OK]   {name} -> {agent_id}")

    # 4. Set reporting relationships via PATCH /api/agents/{id}
    print(f"\nSetting reporting relationships ...")
    for defn in AGENT_DEFINITIONS:
        name = defn["name"]
        manager_name = defn["manager"]

        if not manager_name:
            print(f"  [SKIP] {name} -- no manager (top-level)")
            continue

        agent_id = agent_ids.get(name)
        manager_id = agent_ids.get(manager_name)

        if not agent_id:
            print(f"  [SKIP] {name} -- agent ID not available")
            continue
        if not manager_id:
            print(f"  [WARN] {name} -- manager '{manager_name}' ID not available, skipping")
            continue

        result = api_patch(f"/agents/{agent_id}", {"reportsTo": manager_id})
        if result.get("_error"):
            print(f"  [WARN] {name}.reportsTo failed: {result}")
        else:
            print(f"  [OK]   {name} -> reports to {manager_name} ({manager_id})")

    # 5. Pause Phase 2+ agents
    print(f"\nConfiguring agent statuses (pausing Phase 2+ agents) ...")
    for defn in AGENT_DEFINITIONS:
        name = defn["name"]
        agent_id = agent_ids.get(name)

        if not agent_id:
            print(f"  [SKIP] {name} -- ID not available")
            continue

        if name in PHASE_0_1_AGENTS:
            print(f"  [ACTIVE] {name} -- Phase 0-1, keeping idle")
        else:
            result = api_patch(f"/agents/{agent_id}", {"status": "paused"})
            if result.get("_error"):
                print(f"  [WARN] {name} pause failed: {result}")
            else:
                print(f"  [PAUSED] {name}")

    # 6. Save agent IDs
    AGENT_IDS_FILE.write_text(json.dumps(agent_ids, indent=2))
    print(f"\nAgent IDs saved to: {AGENT_IDS_FILE}")

    # 7. Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Total agents defined:  {len(AGENT_DEFINITIONS)}")
    print(f"IDs captured:          {len(agent_ids)}")
    active = [n for n in agent_ids if n in PHASE_0_1_AGENTS]
    paused = [n for n in agent_ids if n not in PHASE_0_1_AGENTS]
    print(f"Active (Phase 0-1):    {len(active)} -- {active}")
    print(f"Paused (Phase 2+):     {len(paused)}")

    if len(agent_ids) < len(AGENT_DEFINITIONS):
        missing = [d["name"] for d in AGENT_DEFINITIONS if d["name"] not in agent_ids]
        print(f"\nWARNING: {len(missing)} agent(s) not created: {missing}")
        sys.exit(1)

    print("\nDone.")


if __name__ == "__main__":
    main()
