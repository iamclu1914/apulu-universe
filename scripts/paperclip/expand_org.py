"""
expand_org.py -- Create new department agents for Apulu Records full org chart.
Keeps existing departments in place, adds new ones.
"""
import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

API = "http://localhost:3100/api"
SCRIPTS = Path(__file__).parent
APULU = Path(r"C:\Users\rdyal\Apulu Universe")
VAWN = Path(r"C:\Users\rdyal\Vawn")


def api(method, path, data=None):
    url = f"{API}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def main():
    company_id = (SCRIPTS / "company_id.txt").read_text().strip()
    agent_ids = json.loads((SCRIPTS / "agent_ids.json").read_text())

    # Step 1: Fix renamed agents
    renames = {
        "producer": {"name": "Nelly", "title": "EVP of A&R. Talent engine. Creative direction, project planning, cultural radar. Direct line to Clu."},
        "social-media-mgr": {"name": "Letitia", "title": "SVP of Marketing. Platform strategy, content calendar, promotions."},
        "research-director": {"name": "Nari", "title": "VP of Research. Directs discovery, ideation, trend, prompt research."},
    }
    for key, payload in renames.items():
        api("PATCH", f"/agents/{agent_ids[key]}", payload)
        print(f"  Renamed: {payload['name']}")

    # Step 2: Disable board approval
    api("PATCH", f"/companies/{company_id}", {"requireBoardApprovalForNewAgents": False})

    # Step 3: Create new agents
    new_agents = [
        {"key": "artist-mgmt", "name": "Sable", "role": "pm",
         "title": "Head of Artist Management. Day-to-day management, career strategy.",
         "cwd": str(VAWN), "budget": 500},
        {"key": "publicity", "name": "Echo", "role": "general",
         "title": "Head of Publicity. Earned media, press, artist narrative.",
         "cwd": str(VAWN), "budget": 500},
        {"key": "cfo", "name": "Cipher", "role": "cfo",
         "title": "CFO. P&L, financial strategy, DistroKid revenue, streaming royalties.",
         "cwd": str(APULU), "budget": 500},
        {"key": "royalties", "name": "Ledger", "role": "general",
         "title": "Royalties Analyst. Royalty administration, streaming splits, audit.",
         "cwd": str(APULU), "budget": 300},
        {"key": "legal", "name": "Maven", "role": "general",
         "title": "General Counsel. Legal strategy, contracts, clearances, risk.",
         "cwd": str(APULU), "budget": 500},
        {"key": "sync", "name": "Vibe", "role": "general",
         "title": "Head of Sync & Licensing. Film, TV, advertising, gaming placement.",
         "cwd": str(APULU), "budget": 300},
        {"key": "streaming", "name": "Stream", "role": "general",
         "title": "VP of Streaming Strategy. DSP relations, playlist pitching, data.",
         "cwd": str(APULU), "budget": 500},
        {"key": "brand", "name": "Ace", "role": "general",
         "title": "Head of Brand Partnerships. Endorsements, co-marketing, product deals.",
         "cwd": str(APULU), "budget": 300},
        {"key": "touring", "name": "Road", "role": "general",
         "title": "Head of Touring & Live. Booking, production, tour coordination.",
         "cwd": str(VAWN), "budget": 300},
        {"key": "film-tv", "name": "Arc", "role": "general",
         "title": "Head of Film & TV. Artist IP into content, catalog licensing.",
         "cwd": str(APULU), "budget": 300},
    ]

    for agent in new_agents:
        # Check if already exists
        if agent["key"] in agent_ids:
            print(f"  Skip: {agent['name']} (already exists)")
            continue

        payload = {
            "name": agent["name"],
            "role": agent["role"],
            "title": agent["title"],
            "adapterType": "claude_local",
            "adapterConfig": {
                "cwd": agent["cwd"],
                "model": "claude-sonnet-4-20250514",
            },
            "budgetMonthlyCents": agent["budget"],
        }
        try:
            result = api("POST", f"/companies/{company_id}/agents", payload)
            aid = result.get("id") or result.get("data", {}).get("id")
            agent_ids[agent["key"]] = aid
            print(f"  Created: {agent['name']:8s} - {agent['title'][:50]}")
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:100]
            print(f"  ERROR {agent['name']}: {body}")

    # Step 4: Re-enable board approval
    api("PATCH", f"/companies/{company_id}", {"requireBoardApprovalForNewAgents": True})

    # Step 5: Save
    with open(SCRIPTS / "agent_ids.json", "w") as f:
        json.dump(agent_ids, f, indent=2)

    print(f"\n{len(agent_ids)} total agents in Apulu Records.")


if __name__ == "__main__":
    main()
