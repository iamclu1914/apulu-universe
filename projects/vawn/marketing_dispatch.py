"""
marketing_dispatch.py — Apulu Records Marketing Dispatcher for Paperclip

Single entry point for all Marketing department agents. Reads the current
in-progress issue from the Paperclip API to determine which routine fired,
then dispatches to the correct script with the correct arguments.

Usage (Paperclip):
    python marketing_dispatch.py

Usage (manual testing):
    python marketing_dispatch.py --slot morning-early
    python marketing_dispatch.py --slot morning-early --dry-run
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# ---------------------------------------------------------------------------
# Dispatch table: routine title → script + args
# ---------------------------------------------------------------------------

DISPATCH_TABLE = {
    "hashtag-scan": {
        "script": "scan_hashtags.py",
        "args": [],
    },
    "morning-early": {
        "script": "post_vawn.py",
        "args": ["--cron", "morning", "--platforms", "x,bluesky"],
    },
    "morning-main": {
        "script": "post_vawn.py",
        "args": ["--cron", "morning", "--platforms", "tiktok,instagram,threads"],
    },
    "text-post-morning": {
        "script": "text_post_agent.py",
        "args": [],
    },
    "midday-early": {
        "script": "post_vawn.py",
        "args": ["--cron", "midday", "--platforms", "x,bluesky"],
    },
    "midday-main": {
        "script": "post_vawn.py",
        "args": ["--cron", "midday", "--platforms", "tiktok,instagram,threads"],
    },
    "text-post-afternoon": {
        "script": "text_post_agent.py",
        "args": [],
    },
    "evening-early": {
        "script": "post_vawn.py",
        "args": ["--cron", "evening", "--platforms", "x,bluesky,instagram", "--slideshow"],
    },
    "evening-main": {
        "script": "post_vawn.py",
        "args": ["--cron", "evening", "--platforms", "tiktok,threads"],
    },
    "recycle": {
        "script": "recycle_agent.py",
        "args": [],
    },
    "lyric-card": {
        "script": "lyric_card_agent.py",
        "args": [],
    },
    "video-daily": {
        "script": "video_agent.py",
        "args": [],
    },
    "video-cinematic": {
        "script": "video_agent.py",
        "args": ["--cinematic"],
    },
    "engagement-monitor": {
        "script": "engagement_agent.py",
        "args": [],
    },
    "engagement-bot": {
        "script": "engagement_bot.py",
        "args": [],
    },
    "analytics-digest": {
        "script": "analytics_agent.py",
        "args": [],
    },
}

# Directory where all Vawn scripts live
VAWN_DIR = Path(__file__).parent.resolve()


# ---------------------------------------------------------------------------
# Paperclip API helpers
# ---------------------------------------------------------------------------

def get_env():
    """Return Paperclip env vars or None for each if not set."""
    return {
        "agent_id": os.environ.get("PAPERCLIP_AGENT_ID"),
        "company_id": os.environ.get("PAPERCLIP_COMPANY_ID"),
        "api_url": os.environ.get("PAPERCLIP_API_URL"),
    }


def fetch_issues(api_url: str, company_id: str, agent_id: str) -> list:
    """
    Fetch in-progress and todo issues assigned to this agent.
    Returns list of issue dicts.
    """
    issues = []
    for status in ("in_progress", "todo"):
        url = (
            f"{api_url.rstrip('/')}/api/companies/{company_id}/issues"
            f"?assigneeAgentId={agent_id}&status={status}&includeRoutineExecutions=true"
        )
        print(f"[dispatcher] Querying: {url}")
        req = Request(url, headers={"Accept": "application/json"})
        try:
            with urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                # API may return list directly or wrapped in {"issues": [...]}
                if isinstance(data, list):
                    issues.extend(data)
                elif isinstance(data, dict):
                    issues.extend(data.get("issues", data.get("data", [])))
        except HTTPError as e:
            print(f"[dispatcher] HTTP error {e.code} fetching issues (status={status}): {e.reason}")
        except URLError as e:
            raise RuntimeError(f"Cannot reach Paperclip API at {api_url}: {e.reason}") from e
    return issues


def resolve_slot_from_issues(issues: list) -> str | None:
    """
    Find the most relevant routine_execution issue and return its normalized title.
    Prefers in_progress over todo; among equals, takes the first returned.
    """
    routine_issues = [i for i in issues if i.get("originKind") == "routine_execution"]
    if not routine_issues:
        # Fall back to any issue if no routine ones found
        routine_issues = issues

    if not routine_issues:
        return None

    # Prefer in_progress
    in_progress = [i for i in routine_issues if i.get("status") == "in_progress"]
    candidates = in_progress if in_progress else routine_issues

    title = candidates[0].get("title", "")
    return title.strip().lower()


# ---------------------------------------------------------------------------
# Dispatch table matching
# ---------------------------------------------------------------------------

def match_slot(issue_title: str) -> str | None:
    """
    Match an issue title against dispatch table keys.
    Exact match first, then startswith/contains fallback.
    """
    normalized = issue_title.strip().lower()

    # 1. Exact match
    if normalized in DISPATCH_TABLE:
        return normalized

    # 2. Issue title starts with a known slot key (e.g. "morning-early 2026-04-09")
    for key in DISPATCH_TABLE:
        if normalized.startswith(key):
            return key

    # 3. Known slot key is contained anywhere in the title
    for key in DISPATCH_TABLE:
        if key in normalized:
            return key

    return None


# ---------------------------------------------------------------------------
# Dispatcher core
# ---------------------------------------------------------------------------

def dispatch(slot: str, dry_run: bool = False) -> int:
    """
    Run the script mapped to `slot`. Returns subprocess exit code.
    In dry_run mode, prints the command without executing.
    """
    entry = DISPATCH_TABLE[slot]
    script_path = VAWN_DIR / entry["script"]

    if not script_path.exists():
        print(f"[dispatcher] ERROR: Script not found: {script_path}")
        return 1

    cmd = [sys.executable, str(script_path)] + entry["args"]

    print(f"[dispatcher] Slot     : {slot}")
    print(f"[dispatcher] Script   : {script_path}")
    print(f"[dispatcher] Args     : {entry['args']}")
    print(f"[dispatcher] Command  : {' '.join(cmd)}")
    print(f"[dispatcher] CWD      : {VAWN_DIR}")

    if dry_run:
        print("[dispatcher] DRY RUN — skipping execution.")
        return 0

    print(f"[dispatcher] Launching {entry['script']}...")
    result = subprocess.run(cmd, cwd=str(VAWN_DIR))
    print(f"[dispatcher] {entry['script']} exited with code {result.returncode}")
    return result.returncode


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apulu Records Marketing Dispatcher for Paperclip"
    )
    parser.add_argument(
        "--slot",
        help="Manually specify the routine slot (for testing, bypasses API lookup)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be executed without actually running it",
    )
    args = parser.parse_args()

    slot = None

    # --- Manual override via --slot ---
    if args.slot:
        slot = args.slot.strip().lower()
        print(f"[dispatcher] Manual slot override: {slot}")
    else:
        # --- Paperclip env-driven path ---
        env = get_env()
        missing = [k for k, v in env.items() if not v]

        if missing:
            print(
                f"[dispatcher] ERROR: Missing Paperclip env vars: "
                f"{', '.join('PAPERCLIP_' + k.upper() for k in missing)}"
            )
            print("[dispatcher] Tip: use --slot <name> for manual testing.")
            return 1

        print(f"[dispatcher] Agent    : {env['agent_id']}")
        print(f"[dispatcher] Company  : {env['company_id']}")
        print(f"[dispatcher] API URL  : {env['api_url']}")

        try:
            issues = fetch_issues(env["api_url"], env["company_id"], env["agent_id"])
        except RuntimeError as e:
            print(f"[dispatcher] ERROR: {e}")
            return 1

        print(f"[dispatcher] Issues found: {len(issues)}")

        issue_title = resolve_slot_from_issues(issues)
        if not issue_title:
            print("[dispatcher] ERROR: No assignable issue found for this agent.")
            return 1

        print(f"[dispatcher] Issue title  : {issue_title}")
        slot = match_slot(issue_title)

    # --- Validate slot ---
    if not slot:
        print(f"[dispatcher] ERROR: Could not match issue title to any known slot.")
        return 1

    matched = match_slot(slot) if slot not in DISPATCH_TABLE else slot
    if not matched:
        print(
            f"[dispatcher] ERROR: Unrecognized slot '{slot}'. "
            f"Known slots: {', '.join(sorted(DISPATCH_TABLE.keys()))}"
        )
        return 1

    return dispatch(matched, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
