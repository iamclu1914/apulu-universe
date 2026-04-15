"""
president_router.py -- Routing script for Apulu Records presidents.
When a president receives an issue, this script reads it, matches keywords
to the right team member, creates a sub-issue assigned to them, and exits.

No thinking. No doing. Pure delegation.

Usage (via Paperclip process adapter):
    python president_router.py

Env vars (injected by Paperclip):
    PAPERCLIP_AGENT_ID   -- the president's agent ID
    PAPERCLIP_COMPANY_ID -- company ID
    PAPERCLIP_API_URL    -- API base URL
"""

import json
import os
import sys
import urllib.request
import urllib.error


API_URL = os.environ.get("PAPERCLIP_API_URL", "http://localhost:3100")
AGENT_ID = os.environ.get("PAPERCLIP_AGENT_ID")
COMPANY_ID = os.environ.get("PAPERCLIP_COMPANY_ID")


def api(method, path, data=None):
    url = f"{API_URL}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


# ── Routing tables per president ──

ROUTING = {
    # Timbo - A&R
    "timbo": {
        "keywords": {
            "cole": ["song", "lyrics", "write", "track", "suno", "music production", "hook", "verse", "bar", "composition", "publish"],
            "onyx": ["mix", "master", "studio", "audio", "stems", "reaper", "izotope", "sound", "engineer"],
            "tempo": ["release", "rollout", "schedule", "drop", "single", "album", "ep", "launch"],
            "rhythm": ["beat", "producer", "instrumental", "sourcing"],
        },
        "default": "cole",
        "team_names": {
            "cole": "Cole - Writer/Producer",
            "onyx": "Onyx - Studio",
            "tempo": "Tempo - Release Strategy",
            "rhythm": "Rhythm - Beat Scout",
        },
    },

    # Letitia - Creative & Revenue
    "letitia": {
        "keywords": {
            "sage": ["caption", "post", "content", "social media", "text post", "hashtag"],
            "dex": ["comment", "reply", "engage", "community", "fan", "dm"],
            "khari": ["visual", "lyric card", "image", "video clip", "ken burns", "photo"],
            "echo": ["press", "media", "interview", "publicity", "pr", "journalist", "coverage", "narrative"],
            "sable": ["artist", "management", "career", "schedule", "development", "day-to-day"],
            "tempo": ["release", "rollout", "launch", "drop date", "pre-save"],
            "lens": ["music video", "higgsfield", "cinema", "video director", "shot", "film", "seedance", "visual direction"],
            "road": ["tour", "live", "show", "concert", "booking", "venue", "performance"],
        },
        "default": "sage",
        "team_names": {
            "sage": "Sage - Content",
            "dex": "Dex - Community",
            "khari": "Khari - Visual",
            "echo": "Echo - Publicity",
            "sable": "Sable - Artist Mgmt",
            "tempo": "Tempo - Release Strategy",
            "lens": "Lens - Music Video",
            "road": "Road - Touring",
        },
    },

    # Nari - Operations & Strategy
    "nari": {
        "keywords": {
            "rex": ["tech", "infrastructure", "paperclip", "api", "bug", "deploy", "server", "system", "code"],
            "cipher": ["finance", "budget", "revenue", "money", "p&l", "distrokid", "payment", "cost"],
            "ledger": ["royalt", "split", "audit", "mechanical", "statement"],
            "nova": ["analytics", "metrics", "performance", "report", "data", "stats", "weekly"],
            "scout": ["scrape", "discovery", "apify", "platform data", "competitive"],
            "indigo": ["ideation", "ideas", "content plan", "pillar", "brainstorm"],
            "pulse": ["trend", "market", "audience", "insight", "cultural"],
            "pixel": ["research", "notebooklm", "obsidian", "youtube", "prompt", "ai video", "higgsfield", "seedance", "cinema studio", "pipeline"],
            "stream": ["streaming", "spotify", "apple music", "playlist", "dsp", "amazon"],
            "ace": ["brand", "partnership", "endorsement", "sponsor", "deal", "commercial"],
            "vibe": ["sync", "licensing", "film placement", "tv placement", "ad placement", "commercial placement"],
        },
        "default": "pixel",
        "team_names": {
            "rex": "Rex - CTO",
            "cipher": "Cipher - CFO",
            "ledger": "Ledger - Royalties",
            "nova": "Nova - Analytics",
            "scout": "Scout - Discovery",
            "indigo": "Indigo - Ideation",
            "pulse": "Pulse - Trends",
            "pixel": "Pixel - Research",
            "stream": "Stream - Streaming",
            "ace": "Ace - Partnerships",
            "vibe": "Vibe - Sync",
        },
    },

    # Nelly - Legal
    "nelly": {
        "keywords": {
            "maven": ["deal", "contract", "negotiate", "term sheet", "agreement", "partnership", "structure"],
        },
        "default": "maven",
        "team_names": {
            "maven": "Maven - Biz Affairs",
        },
    },
}


def identify_president(agent_name):
    """Match agent name to routing table."""
    name_lower = agent_name.lower()
    for key in ROUTING:
        if key in name_lower:
            return key
    return None


def match_team_member(president_key, title, description):
    """Match issue text to the best team member."""
    routing = ROUTING[president_key]
    text = f"{title} {description}".lower()

    # Score each team member by keyword matches
    scores = {}
    for member, keywords in routing["keywords"].items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scores[member] = score

    if scores:
        best = max(scores, key=scores.get)
        return best, scores[best]

    return routing["default"], 0


def get_my_issues():
    """Get open issues assigned to this president."""
    url = f"/api/companies/{COMPANY_ID}/issues?assigneeAgentId={AGENT_ID}&status=todo&includeRoutineExecutions=true"
    try:
        issues = api("GET", url)
        if isinstance(issues, dict):
            issues = issues.get("data", [])
        return issues
    except Exception as e:
        print(f"[router] Error fetching issues: {e}")
        return []


def get_agent_id_by_name(name):
    """Find agent ID by display name."""
    try:
        agents = api("GET", f"/api/companies/{COMPANY_ID}/agents")
        if isinstance(agents, dict):
            agents = agents.get("data", [])
        for a in agents:
            if a["name"] == name:
                return a["id"]
    except Exception as e:
        print(f"[router] Error finding agent {name}: {e}")
    return None


def create_sub_issue(parent_id, title, description, assignee_id):
    """Create a sub-issue assigned to a team member."""
    try:
        result = api("POST", f"/api/companies/{COMPANY_ID}/issues", {
            "title": title,
            "description": description,
            "assigneeAgentId": assignee_id,
            "parentId": parent_id,
            "status": "todo",
            "priority": "high",
        })
        return result
    except Exception as e:
        print(f"[router] Error creating sub-issue: {e}")
        return None


def add_comment(issue_id, text):
    """Add a comment to the parent issue."""
    try:
        api("POST", f"/api/issues/{issue_id}/comments", {"body": text})
    except Exception:
        pass


def main():
    if not AGENT_ID or not COMPANY_ID:
        print("[router] Missing PAPERCLIP_AGENT_ID or PAPERCLIP_COMPANY_ID")
        sys.exit(1)

    # Get this president's info
    try:
        me = api("GET", f"/api/agents/{AGENT_ID}")
    except Exception as e:
        print(f"[router] Cannot fetch agent info: {e}")
        sys.exit(1)

    my_name = me.get("name", "")
    president_key = identify_president(my_name)
    if not president_key:
        print(f"[router] Cannot identify president from name: {my_name}")
        sys.exit(1)

    print(f"[router] President: {my_name} ({president_key})")

    # Get open issues
    issues = get_my_issues()
    if not issues:
        print("[router] No open issues to route.")
        return

    routing = ROUTING[president_key]

    for issue in issues:
        title = issue.get("title", "")
        desc = issue.get("description", "") or ""
        issue_id = issue["id"]

        # Skip if this issue already has sub-issues (already routed)
        # Check by looking at sub-issues
        try:
            detail = api("GET", f"/api/issues/{issue_id}")
            children = detail.get("children", detail.get("subIssues", []))
            if children:
                print(f"[router] Skip '{title[:40]}' -- already has sub-issues")
                continue
        except Exception:
            pass

        # Match to team member
        member_key, score = match_team_member(president_key, title, desc)
        member_name = routing["team_names"][member_key]
        member_id = get_agent_id_by_name(member_name)

        if not member_id:
            print(f"[router] Cannot find agent: {member_name}")
            continue

        print(f"[router] Routing '{title[:40]}' -> {member_name} (score: {score})")

        # Create sub-issue
        sub_title = title
        sub_desc = f"Delegated by {my_name}.\n\nOriginal request:\n{desc}" if desc else f"Delegated by {my_name}."
        sub = create_sub_issue(issue_id, sub_title, sub_desc, member_id)

        if sub:
            sub_id = sub.get("id", "?")
            print(f"[router] Created sub-issue {sub_id[:12]} assigned to {member_name}")
            add_comment(issue_id, f"Delegated to {member_name}. Sub-issue created.")

            # Mark parent as in_progress
            try:
                api("PATCH", f"/api/issues/{issue_id}", {"status": "in_progress"})
            except Exception:
                pass
        else:
            print(f"[router] Failed to create sub-issue for '{title[:40]}'")


if __name__ == "__main__":
    main()
