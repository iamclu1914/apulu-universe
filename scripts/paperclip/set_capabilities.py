"""Set agent capabilities for task routing in Paperclip."""
import json
import urllib.request
from pathlib import Path

BASE = "http://localhost:3100/api"
SCRIPT_DIR = Path(__file__).parent
company_id = (SCRIPT_DIR / "company_id.txt").read_text().strip()

# Get all agents
url = f"{BASE}/companies/{company_id}/agents"
req = urllib.request.Request(url, headers={"Accept": "application/json"})
with urllib.request.urlopen(req) as resp:
    agents = json.loads(resp.read().decode())
by_name = {a.get("name", ""): a["id"] for a in agents}

CAPABILITIES = {
    "Clu": [
        "final-approval:release",
        "final-approval:signing",
        "final-approval:budget",
        "final-approval:creative-direction",
        "strategic-planning:company-vision",
        "strategic-planning:artist-roster",
        "decision:p-and-l",
        "decision:partnership-approval",
        "artist-relationship:management",
        "crisis-management:executive",
    ],
    "Nelly": [
        "contract:draft-recording-agreement",
        "contract:draft-publishing-deal",
        "contract:draft-360-deal",
        "contract:negotiate-terms",
        "contract:review-and-redline",
        "legal:clearance-sample",
        "legal:clearance-interpolation",
        "legal:copyright-registration",
        "legal:dispute-resolution",
        "legal:ai-licensing-compliance",
        "legal:royalty-split-structuring",
        "compliance:content-rights-audit",
        "deal-structuring:advance-calculation",
        "deal-structuring:recoupment-modeling",
    ],
    "Timbo": [
        "a-and-r:artist-evaluation",
        "a-and-r:signing-recommendation",
        "a-and-r:creative-brief",
        "a-and-r:producer-network-management",
        "a-and-r:release-pipeline-planning",
        "a-and-r:sonic-direction",
        "a-and-r:track-selection",
        "a-and-r:album-sequencing",
        "talent-development:artist-development-plan",
        "talent-development:collaboration-matching",
    ],
    "Rhythm": [
        "discovery:streaming-data-mining",
        "discovery:tiktok-breakout-detection",
        "discovery:soundcloud-scouting",
        "discovery:playlist-signal-analysis",
        "discovery:live-show-scouting",
        "discovery:shortlist-generation",
        "analytics:artist-growth-scoring",
        "analytics:market-trend-identification",
        "research:competitive-landscape-scan",
        "research:genre-trend-tracking",
    ],
    "Cole": [
        "production:beat-creation",
        "production:track-arrangement",
        "production:songwriting",
        "production:co-writing-session",
        "production:suno-prompt-generation",
        "production:lyrics-formatting",
        "production:demo-recording",
        "production:master-delivery",
        "production:genre-blending",
        "creative:hook-writing",
        "creative:concept-development",
    ],
    "Onyx": [
        "studio:session-scheduling",
        "studio:recording-engineering",
        "studio:mixing",
        "studio:mastering",
        "studio:quality-control",
        "studio:stem-delivery",
        "studio:dsp-delivery-spec",
        "studio:vinyl-delivery-spec",
        "studio:gear-management",
        "studio:signal-chain-optimization",
        "studio:reaper-automation",
        "studio:izotope-processing",
    ],
    "Echo": [
        "publicity:press-pitch",
        "publicity:press-release-draft",
        "publicity:interview-prep",
        "publicity:narrative-building",
        "publicity:media-relationship-management",
        "dsp:playlist-pitch",
        "dsp:editorial-pitch",
        "dsp:release-radar-optimization",
        "dsp:discover-weekly-targeting",
        "publicity:review-solicitation",
        "publicity:coverage-tracking",
    ],
    "Sage & Khari": [
        "content:social-caption-writing",
        "content:reel-creation",
        "content:tiktok-clip-creation",
        "content:music-video-production",
        "content:lyric-card-generation",
        "content:ken-burns-video",
        "content:artwork-design",
        "content:ugc-campaign-creation",
        "content:platform-formatting",
        "content:hashtag-strategy",
        "content:content-calendar-execution",
        "visual:thumbnail-creation",
        "visual:story-creation",
        "visual:slideshow-reel",
    ],
    "Dex": [
        "community:discord-management",
        "community:fan-club-operations",
        "community:comment-monitoring",
        "community:comment-response",
        "community:ugc-curation",
        "community:sentiment-monitoring",
        "community:engagement-bot-operations",
        "community:retention-loop-design",
        "community:direct-to-fan-revenue",
        "community:platform-engagement",
    ],
    "Sable": [
        "artist-relations:day-to-day-support",
        "artist-relations:image-management",
        "artist-relations:dispute-mediation",
        "artist-relations:touring-coordination",
        "artist-relations:schedule-management",
        "artist-relations:career-strategy",
        "artist-relations:expectation-alignment",
        "artist-relations:wellness-check",
    ],
    "Letitia": [
        "marketing:campaign-strategy",
        "marketing:campaign-execution",
        "marketing:fan-acquisition",
        "marketing:roi-forecasting",
        "marketing:budget-allocation",
        "marketing:cross-platform-coordination",
        "marketing:launch-planning",
        "marketing:audience-segmentation",
        "revenue:non-traditional-revenue-strategy",
        "revenue:merch-strategy",
    ],
    "Nari": [
        "operations:infrastructure-management",
        "operations:process-optimization",
        "operations:cross-department-coordination",
        "operations:kpi-tracking",
        "operations:vendor-management",
        "finance:cash-flow-oversight",
        "finance:budget-approval",
        "tech:stack-decisions",
        "revenue:high-margin-revenue-oversight",
    ],
    "Rex": [
        "tech:system-architecture",
        "tech:scheduled-task-management",
        "tech:postgres-administration",
        "tech:ai-orchestration",
        "tech:api-integration",
        "tech:prompt-engineering-tooling",
        "tech:monitoring-and-alerting",
        "tech:failover-design",
        "tech:deployment-automation",
        "tech:paperclip-administration",
        "tech:pipeline-maintenance",
    ],
    "Cipher": [
        "finance:forecasting",
        "finance:budgeting",
        "finance:cash-management",
        "finance:royalty-tracking",
        "finance:royalty-payment-processing",
        "finance:distrokid-revenue-analysis",
        "finance:streaming-economics",
        "finance:variance-analysis",
        "finance:p-and-l-reporting",
        "finance:advance-recoupment-tracking",
    ],
    "Nova": [
        "analytics:dashboard-management",
        "analytics:streaming-optimization",
        "analytics:trend-detection",
        "analytics:weekly-performance-digest",
        "analytics:platform-benchmark",
        "analytics:a-and-r-decision-support",
        "analytics:marketing-decision-support",
        "analytics:audience-insights",
        "analytics:content-performance-analysis",
        "analytics:cross-source-data-synthesis",
    ],
    "Vibe": [
        "sync:film-placement",
        "sync:tv-placement",
        "sync:advertising-placement",
        "sync:gaming-placement",
        "sync:pitch-creation",
        "partnerships:brand-deal-negotiation",
        "partnerships:endorsement-evaluation",
        "partnerships:co-marketing",
        "touring:booking",
        "touring:production-planning",
        "touring:venue-selection",
        "revenue:merch-opportunity",
        "revenue:opportunity-valuation",
    ],
}

updated = 0
for name, caps in CAPABILITIES.items():
    if name not in by_name:
        print(f"[SKIP] {name}: not found")
        continue
    aid = by_name[name]
    data = json.dumps({"capabilities": ", ".join(caps)}).encode()
    req = urllib.request.Request(
        f"{BASE}/agents/{aid}", data=data, method="PATCH",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            updated += 1
            print(f"[OK] {name:20s} ({len(caps)} capabilities)")
    except Exception as e:
        print(f"[ERR] {name}: {e}")

print(f"\nUpdated {updated}/{len(CAPABILITIES)} agents with capabilities.")

# Print routing summary
print("\n=== CAPABILITY ROUTING INDEX ===\n")
domains = {}
for name, caps in CAPABILITIES.items():
    for cap in caps:
        domain = cap.split(":")[0]
        if domain not in domains:
            domains[domain] = []
        domains[domain].append((cap, name))

for domain in sorted(domains):
    print(f"  {domain}:")
    for cap, agent in sorted(domains[domain]):
        print(f"    {cap:45s} -> {agent}")
    print()
