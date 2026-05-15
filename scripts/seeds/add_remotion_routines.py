#!/usr/bin/env python3
"""
add_remotion_routines.py — Add the 3 Remotion content routines to Paperclip.

Idempotent: skips any routine whose title already exists. Uses the current
'Sage & Khari' agent (Content & Visuals Team) as assignee -- they already own
the marketing_dispatch.py process adapter, so these routines will route to
remotion_agent.py via the existing DISPATCH_TABLE wiring.

Schedule (America/New_York):
  track-teaser    Tue 19:00  (lyric pillar day, evening listening slot)

Usage:
    python scripts/paperclip/add_remotion_routines.py
    python scripts/paperclip/add_remotion_routines.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE_URL = "http://localhost:3100/api"
SCRIPT_DIR = Path(__file__).parent
COMPANY_ID_FILE = SCRIPT_DIR / "company_id.txt"
AGENT_IDS_FILE = SCRIPT_DIR / "agent_ids.json"
ROUTINE_IDS_FILE = SCRIPT_DIR / "routine_ids.json"
ASSIGNEE_AGENT_KEY = "Sage & Khari"

ROUTINES = [
    {
        "title": "track-teaser",
        "description": "Remotion TrackTeaser - waveform + track title over 9:16 background (Tue, lyric pillar)",
        "cronExpression": "0 19 * * 2",
        "priority": "medium",
    },
]


def api_get(path: str) -> dict:
    req = urllib.request.Request(
        f"{BASE_URL}{path}", headers={"Accept": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def api_post(path: str, payload: dict) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def get_existing_routines(company_id: str) -> dict:
    result = api_get(f"/companies/{company_id}/routines")
    items = result if isinstance(result, list) else result.get("data", [])
    return {r["title"]: r["id"] for r in items if "title" in r and "id" in r}


def create_routine(company_id: str, agent_id: str, r: dict) -> str:
    payload = {
        "title": r["title"],
        "description": r["description"],
        "assigneeAgentId": agent_id,
        "priority": r["priority"],
        "status": "paused",
        "concurrencyPolicy": "skip_if_active",
        "catchUpPolicy": "skip_missed",
    }
    result = api_post(f"/companies/{company_id}/routines", payload)
    data = result.get("data") or result.get("routine") or result
    rid = data.get("id") or data.get("_id")
    if not rid:
        raise RuntimeError(f"No id in response for '{r['title']}': {result}")
    return rid


def create_trigger(routine_id: str, cron: str) -> None:
    payload = {
        "kind": "schedule",
        "cronExpression": cron,
        "timezone": "America/New_York",
        "enabled": True,
    }
    api_post(f"/routines/{routine_id}/triggers", payload)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true",
                   help="Print what would be created without calling Paperclip.")
    args = p.parse_args()

    if not COMPANY_ID_FILE.exists():
        raise SystemExit(f"Missing {COMPANY_ID_FILE} — run setup_company.py first.")
    if not AGENT_IDS_FILE.exists():
        raise SystemExit(f"Missing {AGENT_IDS_FILE} — run setup_agents.py first.")

    company_id = COMPANY_ID_FILE.read_text(encoding="utf-8").strip()
    agent_ids = json.loads(AGENT_IDS_FILE.read_text(encoding="utf-8"))

    if ASSIGNEE_AGENT_KEY not in agent_ids:
        raise SystemExit(
            f"Agent '{ASSIGNEE_AGENT_KEY}' not found in {AGENT_IDS_FILE}. "
            f"Available: {list(agent_ids.keys())}"
        )
    agent_id = agent_ids[ASSIGNEE_AGENT_KEY]

    if args.dry_run:
        print(f"[dry-run] company: {company_id}")
        print(f"[dry-run] agent:   {ASSIGNEE_AGENT_KEY} -> {agent_id}")
        for r in ROUTINES:
            print(f"[dry-run] would create: {r['title']:<16} cron={r['cronExpression']}")
        return 0

    print(f"Company: {company_id}")
    print(f"Assignee: {ASSIGNEE_AGENT_KEY} ({agent_id})")
    print("Checking existing routines...")
    existing = get_existing_routines(company_id)
    print(f"  Found {len(existing)} existing routine(s).")

    # Load existing routine_ids.json so we merge rather than overwrite
    routine_ids = {}
    if ROUTINE_IDS_FILE.exists():
        try:
            routine_ids = json.loads(ROUTINE_IDS_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            routine_ids = {}

    created, skipped = [], []
    for r in ROUTINES:
        title = r["title"]
        if title in existing:
            rid = existing[title]
            print(f"  SKIP   {title}  (already exists, id={rid})")
            routine_ids[title] = rid
            skipped.append(title)
            continue
        rid = create_routine(company_id, agent_id, r)
        create_trigger(rid, r["cronExpression"])
        print(f"  CREATE {title}  cron={r['cronExpression']}  id={rid}")
        routine_ids[title] = rid
        created.append(title)

    ROUTINE_IDS_FILE.write_text(
        json.dumps(routine_ids, indent=2), encoding="utf-8"
    )
    print(f"\nroutine_ids.json updated.")
    print(f"Created: {len(created)} ({', '.join(created) or 'none'})")
    print(f"Skipped: {len(skipped)} ({', '.join(skipped) or 'none'})")
    print("\nAll new routines are created in 'paused' status. Unpause them in")
    print("Paperclip when you're ready for them to fire.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except urllib.error.URLError as exc:
        raise SystemExit(
            f"Paperclip API unreachable at {BASE_URL}. Is Paperclip running? ({exc})"
        )
