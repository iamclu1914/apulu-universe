"""
broadcast.py -- Cross-department broadcast for Apulu Records.
When a release or major event is planned, this script creates issues
across all relevant departments simultaneously.

Usage:
    python broadcast.py release "Song Title" --date 2026-05-01
    python broadcast.py announcement "Message text"
    python broadcast.py campaign "Campaign Name" --brief "description"

This solves the lateral communication gap: when Tempo plans a release,
Stream, Echo, Sage, Khari, and Lens all need to know simultaneously.
"""

import argparse
import json
import sys
import urllib.request
from pathlib import Path

API = "http://localhost:3100/api"
SCRIPTS = Path(__file__).parent


def api(method, path, data=None):
    url = f"{API}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def get_agents():
    company_id = (SCRIPTS / "company_id.txt").read_text().strip()
    agents = api("GET", f"/companies/{company_id}/agents")
    if isinstance(agents, dict):
        agents = agents.get("data", [])
    return company_id, {a["name"]: a["id"] for a in agents}


# ── Broadcast Templates ──

RELEASE_BROADCAST = {
    "Stream - Streaming": {
        "title": "Playlist pitching: {title}",
        "desc": "New release dropping {date}. Submit to Spotify/Apple editorial playlists 4 weeks before. Use streaming-strategy skill.",
        "priority": "high",
    },
    "Echo - Publicity": {
        "title": "Press campaign: {title}",
        "desc": "New release dropping {date}. Begin media outreach 6 weeks before. Use music-publicity skill for press kit and pitch emails.",
        "priority": "high",
    },
    "Sage - Content": {
        "title": "Content calendar: {title}",
        "desc": "New release dropping {date}. Plan teaser content, countdown posts, release day blitz. Use social-content skill.",
        "priority": "high",
    },
    "Khari - Visual": {
        "title": "Visual assets: {title}",
        "desc": "New release dropping {date}. Prepare lyric cards, promo videos, social clips. Use visual-production skill.",
        "priority": "medium",
    },
    "Lens - Music Video": {
        "title": "Music video direction: {title}",
        "desc": "New release dropping {date}. Develop creative treatment and shot list. Use higgsfield-cinema-studio skill.",
        "priority": "medium",
    },
    "Vibe - Sync": {
        "title": "Sync readiness: {title}",
        "desc": "New release dropping {date}. Ensure stems, instrumentals, and metadata ready for sync pitching. Use sync-licensing skill.",
        "priority": "low",
    },
    "Ace - Partnerships": {
        "title": "Brand opportunities: {title}",
        "desc": "New release dropping {date}. Evaluate brand partnership opportunities around this release. Use brand-partnerships skill.",
        "priority": "low",
    },
}

ANNOUNCEMENT_BROADCAST = {
    "Sage - Content": {
        "title": "Post announcement: {title}",
        "desc": "Post this across all platforms immediately: {brief}",
        "priority": "urgent",
    },
    "Dex - Community": {
        "title": "Engagement alert: {title}",
        "desc": "Monitor engagement on announcement posts. Reply to key comments. {brief}",
        "priority": "high",
    },
    "Echo - Publicity": {
        "title": "Press alert: {title}",
        "desc": "Evaluate if this warrants a press release or media pitch: {brief}",
        "priority": "medium",
    },
}

CAMPAIGN_BROADCAST = {
    "Sage - Content": {
        "title": "Campaign content: {title}",
        "desc": "{brief}",
        "priority": "high",
    },
    "Khari - Visual": {
        "title": "Campaign visuals: {title}",
        "desc": "{brief}",
        "priority": "high",
    },
    "Dex - Community": {
        "title": "Campaign engagement: {title}",
        "desc": "{brief}",
        "priority": "medium",
    },
    "Nova - Analytics": {
        "title": "Track campaign: {title}",
        "desc": "Monitor performance metrics for this campaign. {brief}",
        "priority": "medium",
    },
}


def broadcast(template, title, date="TBD", brief=""):
    company_id, agents = get_agents()
    created = 0

    for agent_name, config in template.items():
        agent_id = agents.get(agent_name)
        if not agent_id:
            print(f"  SKIP: {agent_name} not found")
            continue

        issue_title = config["title"].format(title=title, date=date, brief=brief)
        issue_desc = config["desc"].format(title=title, date=date, brief=brief)

        result = api("POST", f"/companies/{company_id}/issues", {
            "title": issue_title,
            "description": issue_desc,
            "assigneeAgentId": agent_id,
            "status": "todo",
            "priority": config["priority"],
        })
        issue_id = result.get("id", "?")[:12]
        print(f"  {agent_name}: {issue_title} ({issue_id}...)")
        created += 1

    print(f"\nBroadcast complete: {created} issues created across departments.")


def main():
    parser = argparse.ArgumentParser(description="Apulu Records cross-department broadcast")
    parser.add_argument("type", choices=["release", "announcement", "campaign"])
    parser.add_argument("title", help="Release title, announcement text, or campaign name")
    parser.add_argument("--date", default="TBD", help="Release date (for release broadcasts)")
    parser.add_argument("--brief", default="", help="Additional context")
    args = parser.parse_args()

    templates = {
        "release": RELEASE_BROADCAST,
        "announcement": ANNOUNCEMENT_BROADCAST,
        "campaign": CAMPAIGN_BROADCAST,
    }

    print(f"\n[broadcast] Type: {args.type}")
    print(f"[broadcast] Title: {args.title}")
    if args.date != "TBD":
        print(f"[broadcast] Date: {args.date}")
    print()

    broadcast(templates[args.type], args.title, args.date, args.brief)


if __name__ == "__main__":
    main()
