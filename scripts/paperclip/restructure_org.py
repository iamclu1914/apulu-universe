#!/usr/bin/env python3
"""Restructure Apulu Records org chart to new spec."""

import json
import requests
import sys
import time

API = "http://127.0.0.1:3100/api"
COMPANY_ID = "e8132e3c-561d-4519-90f0-a7f1ff655786"

def get_agents():
    r = requests.get(f"{API}/companies/{COMPANY_ID}/agents")
    r.raise_for_status()
    return r.json()

def delete_agent(agent_id, name):
    r = requests.delete(f"{API}/agents/{agent_id}")
    if r.status_code in (200, 204):
        print(f"  DELETED {name} ({agent_id})")
        return True
    else:
        print(f"  FAILED to delete {name}: {r.status_code} {r.text}")
        return False

def create_agent(name, title, url_key):
    body = {
        "name": name,
        "title": title,
        "urlKey": url_key,
        "status": "idle",
        "instructions": ""
    }
    r = requests.post(f"{API}/companies/{COMPANY_ID}/agents", json=body)
    if r.status_code in (200, 201):
        data = r.json()
        agent_id = data.get("id")
        print(f"  CREATED {name} ({agent_id})")
        return agent_id
    else:
        print(f"  FAILED to create {name}: {r.status_code} {r.text}")
        return None

def patch_agent(agent_id, name, updates):
    r = requests.patch(f"{API}/agents/{agent_id}", json=updates)
    if r.status_code == 200:
        print(f"  PATCHED {name} ({agent_id}): {list(updates.keys())}")
        return True
    else:
        print(f"  FAILED to patch {name}: {r.status_code} {r.text}")
        return False

def main():
    print("=== Step 1: Fetch all agents ===")
    agents = get_agents()
    name_map = {a["name"]: a["id"] for a in agents}
    print(f"Found {len(agents)} agents: {sorted(name_map.keys())}")

    # ── Step 2: Delete agents not in new org ──
    to_delete = [
        "Freq", "Slate", "Proof", "Tempo", "Lens", "Arc", "Road",
        "Maven", "Ledger", "Stream", "Ace", "Scout", "Indigo", "Pulse", "Pixel"
    ]

    print(f"\n=== Step 2: Delete {len(to_delete)} agents ===")
    for name in to_delete:
        if name in name_map:
            delete_agent(name_map[name], name)
            del name_map[name]
        else:
            print(f"  SKIP {name} (not found)")

    # ── Step 3: Merge Sage + Khari ──
    # Rename Sage to "Sage & Khari", then delete Khari
    print("\n=== Step 3: Merge Sage + Khari ===")
    if "Sage" in name_map:
        sage_id = name_map["Sage"]
        patch_agent(sage_id, "Sage -> Sage & Khari", {
            "name": "Sage & Khari",
            "title": "Content & Visuals Team"
        })
        del name_map["Sage"]
        name_map["Sage & Khari"] = sage_id
        print(f"  Renamed Sage to 'Sage & Khari' (id={sage_id})")
    else:
        print("  WARNING: Sage not found!")

    if "Khari" in name_map:
        delete_agent(name_map["Khari"], "Khari")
        del name_map["Khari"]
    else:
        print("  SKIP Khari (already gone)")

    # ── Step 4: Create missing agents (Rex, Cipher) ──
    print("\n=== Step 4: Create Rex and Cipher ===")
    if "Rex" not in name_map:
        rex_id = create_agent("Rex", "CTO & AI Infrastructure Lead", "rex")
        if rex_id:
            name_map["Rex"] = rex_id
    else:
        print(f"  Rex already exists ({name_map['Rex']})")

    if "Cipher" not in name_map:
        cipher_id = create_agent("Cipher", "CFO & Finance Lead", "cipher")
        if cipher_id:
            name_map["Cipher"] = cipher_id
    else:
        print(f"  Cipher already exists ({name_map['Cipher']})")

    # ── Step 5: Update all titles ──
    print("\n=== Step 5: Update titles ===")
    titles = {
        "Clu": "Chairman & CEO",
        "Nelly": "General Counsel & Head of Business Affairs",
        "Timbo": "President, A&R & Talent Development",
        "Rhythm": "A&R Scout & Discovery Analyst",
        "Cole": "In-House Producer & Songwriter",
        "Onyx": "Studio & Post-Production Lead",
        "Echo": "Head of Publicity & DSP Relations",
        "Sage & Khari": "Content & Visuals Team",
        "Dex": "Community & Fan Engagement Manager",
        "Sable": "Artist Relations Manager",
        "Letitia": "President, Marketing, Audience & Revenue",
        "Nari": "COO, Operations, Finance & Tech",
        "Rex": "CTO & AI Infrastructure Lead",
        "Cipher": "CFO & Finance Lead",
        "Nova": "Analytics & Streaming Strategy Lead",
        "Vibe": "Head of Partnerships & Revenue",
    }

    for name, title in titles.items():
        if name in name_map:
            patch_agent(name_map[name], name, {"title": title})
        else:
            print(f"  WARNING: {name} not found for title update!")

    # ── Step 6: Update all instructions ──
    print("\n=== Step 6: Update instructions ===")
    instructions = {
        "Clu": "Final authority on vision, signings, budgets, releases, and P&L. Owns artist relationships and long-term strategy. Key Skill: High-stakes prioritization under incomplete data.",
        "Nelly": "Negotiates and drafts all contracts (recording, 360, publishing, AI licensing). Handles clearances, disputes, compliance, deal structuring, advances, and royalties splits. Key Skill: Contract risk assessment and clause negotiation.",
        "Timbo": "Leads artist scouting, signing, and creative direction. Builds producer network and release pipeline. Key Skill: Hit prediction from partial signals (data + gut).",
        "Rhythm": "Mines streaming data, TikTok, SoundCloud, and playlists for breakout signals. Attends shows and feeds Timbo shortlists with analytics. Key Skill: Pattern recognition across noisy social/streaming datasets.",
        "Cole": "Writes and produces tracks for roster or co-writes. Runs sessions and delivers masters on deadline. Key Skill: Rapid genre-blending composition under tight deadlines.",
        "Onyx": "Manages recording, mixing, mastering, and QC workflow. Oversees gear, scheduling, and delivery specs for DSPs and vinyl. Key Skill: Technical audio signal chain optimization and QC.",
        "Echo": "Secures playlist adds, press, reviews, and editorial coverage. Builds narratives and pitches to DSP teams. Key Skill: Narrative framing and relationship mapping.",
        "Sage & Khari": "Creates social clips, Reels, music videos, artwork, and UGC. Executes campaigns under Letitia. Key Skill: High-volume visual asset generation at platform specs.",
        "Dex": "Builds and moderates Discord, fan clubs, and retention loops. Drives UGC and direct-to-fan revenue. Key Skill: Real-time sentiment detection and response calibration.",
        "Sable": "Provides day-to-day career support: image, disputes, and touring coordination. Key Skill: Conflict de-escalation and expectation alignment.",
        "Letitia": "Owns digital-first growth: campaigns, fan acquisition, content, publicity, and non-traditional revenue. Key Skill: Campaign ROI forecasting across fragmented platforms.",
        "Nari": "Runs infrastructure, cash flow, royalties, tech stack, and high-margin revenue (sync, live, partnerships).",
        "Rex": "Owns full tech stack, scheduled tasks, Postgres reliability, and AI orchestration. Embeds prompting tools for internal use. Key Skill: Fault-tolerant system orchestration and failover design.",
        "Cipher": "Handles forecasting, budgeting, and cash management. Oversees royalty tracking and payments. Key Skill: Cash-flow scenario modeling and variance analysis.",
        "Nova": "Owns data dashboards and optimization. Spots trends, supports A&R/marketing decisions, and drives streaming performance. Key Skill: Cross-source data synthesis and actionable insight extraction.",
        "Vibe": "Secures sync/licensing (film, TV, ads, games), brand deals, touring/live, and merch opportunities. Key Skill: Opportunity valuation and multi-stakeholder negotiation.",
    }

    for name, instr in instructions.items():
        if name in name_map:
            patch_agent(name_map[name], name, {"instructions": instr})
        else:
            print(f"  WARNING: {name} not found for instructions update!")

    # ── Step 7: Set reportsTo relationships ──
    print("\n=== Step 7: Set reportsTo relationships ===")

    clu_id = name_map.get("Clu")
    timbo_id = name_map.get("Timbo")
    letitia_id = name_map.get("Letitia")
    nari_id = name_map.get("Nari")

    reports_to = {
        "Clu": None,
        "Nelly": clu_id,
        "Timbo": clu_id,
        "Letitia": clu_id,
        "Nari": clu_id,
        "Rhythm": timbo_id,
        "Cole": timbo_id,
        "Onyx": timbo_id,
        "Echo": letitia_id,
        "Sage & Khari": letitia_id,
        "Dex": letitia_id,
        "Sable": letitia_id,
        "Rex": nari_id,
        "Cipher": nari_id,
        "Nova": nari_id,
        "Vibe": nari_id,
    }

    for name, manager_id in reports_to.items():
        if name in name_map:
            patch_agent(name_map[name], name, {"reportsTo": manager_id})
        else:
            print(f"  WARNING: {name} not found for reportsTo update!")

    # ── Step 8: Ensure all agents have status "idle" ──
    print("\n=== Step 8: Ensure all agents are idle ===")
    for name in name_map:
        patch_agent(name_map[name], name, {"status": "idle"})

    # ── Step 9: Save agent_ids.json ──
    print("\n=== Step 9: Save agent_ids.json ===")
    agent_ids_path = r"C:\Users\rdyal\Apulu Universe\scripts\paperclip\agent_ids.json"
    with open(agent_ids_path, "w") as f:
        json.dump(name_map, f, indent=2)
    print(f"  Saved {len(name_map)} agents to {agent_ids_path}")

    # ── Step 10: Verify final state ──
    print("\n=== Step 10: Verification ===")
    final_agents = get_agents()
    final_map = {a["name"]: a for a in final_agents}

    print(f"\nFinal org ({len(final_agents)} agents):")
    print("-" * 80)

    # Build tree
    roots = []
    children = {}
    for a in final_agents:
        parent = a["reportsTo"]
        if parent is None:
            roots.append(a)
        else:
            children.setdefault(parent, []).append(a)

    def print_tree(agent, indent=0):
        prefix = "  " * indent + ("└── " if indent > 0 else "")
        print(f"{prefix}{agent['name']} — {agent['title']} (reportsTo={'ROOT' if agent['reportsTo'] is None else agent['reportsTo'][:8] + '...'})")
        for child in sorted(children.get(agent["id"], []), key=lambda x: x["name"]):
            print_tree(child, indent + 1)

    for root in roots:
        print_tree(root)

    print("\nDone!")

if __name__ == "__main__":
    main()
