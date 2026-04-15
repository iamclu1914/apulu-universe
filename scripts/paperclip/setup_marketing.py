#!/usr/bin/env python3
"""
setup_marketing.py -- Create 16 Marketing department routines with cron triggers in Paperclip.

Usage:
    python scripts/paperclip/setup_marketing.py

Reads:  scripts/paperclip/company_id.txt
        scripts/paperclip/agent_ids.json
Saves:  scripts/paperclip/routine_ids.json
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
ROUTINE_IDS_FILE = SCRIPT_DIR / "routine_ids.json"

# ---------------------------------------------------------------------------
# Routine definitions
# ---------------------------------------------------------------------------

CONTENT_CREATOR_ROUTINES = [
    {
        "title": "hashtag-scan",
        "description": "Generate trending hashtags for all platforms",
        "cronExpression": "0 6 * * *",
        "priority": "medium",
    },
    {
        "title": "morning-early",
        "description": "Post to X and Bluesky -- morning energy",
        "cronExpression": "0 8 * * *",
        "priority": "high",
    },
    {
        "title": "morning-main",
        "description": "Post to TikTok, Instagram, Threads -- morning",
        "cronExpression": "15 9 * * *",
        "priority": "high",
    },
    {
        "title": "text-post-morning",
        "description": "Text-only posts to X, Threads, Bluesky",
        "cronExpression": "30 10 * * *",
        "priority": "medium",
    },
    {
        "title": "midday-early",
        "description": "Post to X and Bluesky -- midday swagger",
        "cronExpression": "0 12 * * *",
        "priority": "high",
    },
    {
        "title": "midday-main",
        "description": "Post to TikTok, Instagram, Threads -- midday",
        "cronExpression": "45 12 * * *",
        "priority": "high",
    },
    {
        "title": "text-post-afternoon",
        "description": "Text-only posts + X thread from ideation",
        "cronExpression": "30 15 * * *",
        "priority": "medium",
    },
    {
        "title": "evening-early",
        "description": "Post to X, Bluesky, Instagram slideshow Reel",
        "cronExpression": "0 18 * * *",
        "priority": "high",
    },
    {
        "title": "evening-main",
        "description": "Post to TikTok, Threads -- evening storytelling",
        "cronExpression": "15 20 * * *",
        "priority": "high",
    },
    {
        "title": "recycle",
        "description": "Recycle top 30-day-old images with fresh captions",
        "cronExpression": "0 14 * * 0",
        "priority": "low",
    },
]

VISUAL_CONTENT_ROUTINES = [
    {
        "title": "lyric-card",
        "description": "Generate lyric card images for today",
        "cronExpression": "30 6 * * *",
        "priority": "medium",
    },
    {
        "title": "video-daily",
        "description": "Create Ken Burns video from images",
        "cronExpression": "45 6 * * *",
        "priority": "medium",
    },
    {
        "title": "video-cinematic",
        "description": "Create Higgsfield cinematic video (Sunday)",
        "cronExpression": "0 7 * * 0",
        "priority": "low",
    },
]

ENGAGEMENT_ROUTINES = [
    {
        "title": "engagement-monitor",
        "description": "Monitor comments and auto-reply across platforms",
        "cronExpression": "0 */2 * * *",
        "priority": "medium",
    },
    {
        "title": "engagement-bot",
        "description": "Bluesky likes on trending hip-hop posts",
        "cronExpression": "0 */5 * * *",
        "priority": "low",
    },
]

ANALYTICS_ROUTINES = [
    {
        "title": "analytics-digest",
        "description": "Weekly analytics digest and recommendations",
        "cronExpression": "0 9 * * 0",
        "priority": "low",
    },
]


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def api_get(path: str) -> dict:
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


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def get_existing_routines(company_id: str) -> dict:
    """Return a dict of {title: routine_id} for all existing routines."""
    try:
        result = api_get(f"/companies/{company_id}/routines")
    except urllib.error.URLError as exc:
        print(f"ERROR: Could not fetch existing routines -- {exc}")
        sys.exit(1)

    routines = result if isinstance(result, list) else result.get("data", [])
    return {r["title"]: r["id"] for r in routines if "title" in r and "id" in r}


def create_routine(company_id: str, agent_id: str, title: str, description: str,
                   priority: str, concurrency_policy: str) -> str:
    """POST a new routine and return its ID."""
    payload = {
        "title": title,
        "description": description,
        "assigneeAgentId": agent_id,
        "priority": priority,
        "status": "paused",
        "concurrencyPolicy": concurrency_policy,
        "catchUpPolicy": "skip_missed",
    }
    try:
        result = api_post(f"/companies/{company_id}/routines", payload)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        print(f"  ERROR creating routine '{title}': {exc.code} {body}")
        sys.exit(1)

    # Handle possible envelope
    data = result.get("data") or result.get("routine") or result
    routine_id = data.get("id") or data.get("_id")
    if not routine_id:
        print(f"  ERROR: No ID in response for '{title}': {json.dumps(result)}")
        sys.exit(1)
    return routine_id


def create_trigger(routine_id: str, cron_expression: str) -> None:
    """POST a cron trigger for a routine."""
    payload = {
        "kind": "schedule",
        "cronExpression": cron_expression,
        "timezone": "America/New_York",
        "enabled": True,
    }
    try:
        api_post(f"/routines/{routine_id}/triggers", payload)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        print(f"  ERROR creating trigger for routine {routine_id}: {exc.code} {body}")
        sys.exit(1)


def process_group(company_id: str, agent_id: str, agent_name: str,
                  routines: list, concurrency_policy: str,
                  existing: dict, routine_ids: dict,
                  created: list, skipped: list) -> None:
    """Create routines + triggers for one agent group."""
    print(f"\n[{agent_name}] ({len(routines)} routines, concurrency={concurrency_policy})")
    for r in routines:
        title = r["title"]
        if title in existing:
            routine_id = existing[title]
            print(f"  SKIP  {title} (already exists, id={routine_id})")
            routine_ids[title] = routine_id
            skipped.append(title)
        else:
            routine_id = create_routine(
                company_id, agent_id, title, r["description"],
                r["priority"], concurrency_policy
            )
            create_trigger(routine_id, r["cronExpression"])
            print(f"  CREATE {title} -- cron={r['cronExpression']}  id={routine_id}")
            routine_ids[title] = routine_id
            created.append(title)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=== setup_marketing.py -- Apulu Records Marketing Routines ===\n")

    # Read company ID
    if not COMPANY_ID_FILE.exists():
        print(f"ERROR: {COMPANY_ID_FILE} not found. Run setup_company.py first.")
        sys.exit(1)
    company_id = COMPANY_ID_FILE.read_text().strip()
    print(f"Company ID: {company_id}")

    # Read agent IDs
    if not AGENT_IDS_FILE.exists():
        print(f"ERROR: {AGENT_IDS_FILE} not found. Run setup_agents.py first.")
        sys.exit(1)
    agent_ids = json.loads(AGENT_IDS_FILE.read_text())

    required_agents = ["content-creator", "visual-content", "engagement", "analytics"]
    for name in required_agents:
        if name not in agent_ids:
            print(f"ERROR: Agent '{name}' not found in {AGENT_IDS_FILE}")
            sys.exit(1)

    # Fetch existing routines for idempotency
    print("Checking existing routines...")
    existing = get_existing_routines(company_id)
    print(f"  Found {len(existing)} existing routine(s): {list(existing.keys()) or 'none'}")

    # Accumulate results
    routine_ids: dict = {}
    created: list = []
    skipped: list = []

    process_group(
        company_id, agent_ids["content-creator"], "content-creator",
        CONTENT_CREATOR_ROUTINES, "skip_if_active",
        existing, routine_ids, created, skipped
    )
    process_group(
        company_id, agent_ids["visual-content"], "visual-content",
        VISUAL_CONTENT_ROUTINES, "skip_if_active",
        existing, routine_ids, created, skipped
    )
    process_group(
        company_id, agent_ids["engagement"], "engagement",
        ENGAGEMENT_ROUTINES, "coalesce_if_active",
        existing, routine_ids, created, skipped
    )
    process_group(
        company_id, agent_ids["analytics"], "analytics",
        ANALYTICS_ROUTINES, "skip_if_active",
        existing, routine_ids, created, skipped
    )

    # Save routine IDs
    ROUTINE_IDS_FILE.write_text(json.dumps(routine_ids, indent=2))
    print(f"\nRoutine IDs saved to: {ROUTINE_IDS_FILE}")

    # Summary
    total = len(created) + len(skipped)
    print(f"\n=== Summary ===")
    print(f"  Total routines:  {total}/16")
    print(f"  Created:         {len(created)}")
    print(f"  Already existed: {len(skipped)}")
    if created:
        print(f"\n  Newly created:")
        for t in created:
            print(f"    + {t}")
    if skipped:
        print(f"\n  Skipped (existing):")
        for t in skipped:
            print(f"    ~ {t}")
    print(f"\nAll routines start PAUSED. Activate manually after validation.")
    print("Done.")


if __name__ == "__main__":
    main()
