"""
daily_briefing.py -- Morning synthesis note for Apulu Universe.
Reads everything the system produced, distills it into one Obsidian note.
The one note you read with coffee.

Runs at 7:30am after all prep tasks.

Usage:
    python daily_briefing.py
"""

import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline_config import load_json, save_json, now_iso, today_str

VAWN_DIR = Path(r"C:\Users\rdyal\Vawn")
RESEARCH_DIR = Path(r"C:\Users\rdyal\Apulu Universe\research\vawn")
PIPELINE_CONFIG = Path(r"C:\Users\rdyal\Apulu Universe\pipeline\config")
BRIEFINGS_DIR = RESEARCH_DIR / "briefings"


def _human(n):
    if n is None:
        return "N/A"
    n = int(n)
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return f"{n:,}"


def load_health():
    """Load today's health check results."""
    return load_json(BRIEFINGS_DIR / "health_results.json")


def load_infra_status() -> dict:
    """Read infrastructure probes + rolled-up signals for the morning briefing.

    Pulls from the bulletproofing stack we wired up in April 2026:
      - backend_health.json   (Apulu Studio probe, 10-min cadence)
      - claude_auth_state.json (shared Claude login, manual cadence)
      - dead_letter.jsonl      (permanently-failed dispatches)
      - alert_fallback.jsonl   (alerts SMTP could not deliver)

    Returns a dict with clear fields the briefing can render without
    knowing the internals of each data source.
    """
    backend = load_json(VAWN_DIR / "backend_health.json")
    auth = load_json(VAWN_DIR / "claude_auth_state.json")

    def _jsonl_count(path: Path, filter_undelivered: bool = False) -> int:
        if not path.exists():
            return 0
        n = 0
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                if filter_undelivered:
                    try:
                        if json.loads(line).get("delivered", False):
                            continue
                    except Exception:
                        pass
                n += 1
        except Exception:
            return 0
        return n

    dlq_count = _jsonl_count(VAWN_DIR / "dead_letter.jsonl")
    undelivered_alerts = _jsonl_count(VAWN_DIR / "alert_fallback.jsonl",
                                       filter_undelivered=True)

    issues: list[str] = []
    overall = (backend or {}).get("overall", "unknown")
    if overall == "degraded":
        issues.append("Apulu Studio backend DEGRADED — X/Bluesky posts gated by breaker")
    elif overall == "partial":
        issues.append("Apulu Studio backend partial (non-critical endpoint down)")

    if (auth or {}).get("last_status") == "expired":
        issues.append("Claude Code auth EXPIRED — 11 claude_local agents blocked")

    if dlq_count:
        issues.append(f"{dlq_count} entries in dead-letter queue")
    if undelivered_alerts:
        issues.append(f"{undelivered_alerts} undelivered alerts (SMTP)")

    return {
        "backend_overall": overall,
        "backend_last_check": (backend or {}).get("last_check"),
        "auth_status": (auth or {}).get("last_status", "unknown"),
        "auth_last_check": (auth or {}).get("last_check"),
        "dlq_count": dlq_count,
        "undelivered_alerts": undelivered_alerts,
        "issues": issues,
    }


def load_pillar():
    """Load today's pillar context."""
    return load_json(PIPELINE_CONFIG / "pillar_context.json")


def load_engagement():
    """Load engagement feedback."""
    return load_json(PIPELINE_CONFIG / "engagement_feedback.json")


def load_ideation():
    """Load today's ideation results."""
    return load_json(RESEARCH_DIR / "ideation" / "ideation_results.json")


def load_discovery_summary():
    """Summarize what the discovery pipelines found."""
    discovery_dir = RESEARCH_DIR / "discovery"
    summary = {}
    files = {
        "x": "x_pipeline_results.json",
        "tiktok": "tiktok_pipeline_results.json",
        "instagram": "ig_pipeline_results.json",
        "reddit": "reddit_pipeline_results.json",
    }
    for name, filename in files.items():
        data = load_json(discovery_dir / filename)
        if not data:
            continue
        top = data.get("top_20", [])[:3]
        total_key = f"total_{'tweets' if name == 'x' else 'posts' if name in ('instagram', 'reddit') else 'videos'}"
        summary[name] = {
            "total": data.get(total_key, 0),
            "highlights": [],
        }
        for item in top:
            if name == "x":
                author = item.get("author", {}).get("handle", "?")
                text = (item.get("text", "") or "")[:100]
                summary[name]["highlights"].append(f"@{author}: {text}")
            elif name == "tiktok":
                author = item.get("author", {}).get("username", "?")
                plays = _human(item.get("plays", 0))
                text = (item.get("text", "") or "")[:80]
                summary[name]["highlights"].append(f"@{author} ({plays} plays): {text}")
            elif name == "instagram":
                author = item.get("author", {}).get("username", "?")
                likes = _human(item.get("likes", 0))
                summary[name]["highlights"].append(f"@{author} ({likes} likes)")
            elif name == "reddit":
                sub = item.get("subreddit", "?")
                title = (item.get("title", "") or "")[:80]
                summary[name]["highlights"].append(f"r/{sub}: {title}")
    return summary


def load_yesterday_performance():
    """Load yesterday's posting and engagement data."""
    yesterday = str(date.today() - timedelta(days=1))
    log = load_json(VAWN_DIR / "posted_log.json")
    metrics = load_json(VAWN_DIR / "research" / "metrics_log.json")

    posted_images = []
    for fname, entries in log.items():
        if fname.startswith("_"):
            continue
        if yesterday in entries:
            posted_images.append(fname)

    slots = log.get("_posted_slots", {}).get(yesterday, {})

    # Get scores for yesterday's posts
    scored = []
    weights = {"likes": 1, "comments": 3, "saves": 5, "shares": 4,
               "reposts": 4, "retweets": 4, "views": 0.01, "replies": 3}
    for fname in posted_images:
        img_metrics = metrics.get(fname, {}).get(yesterday, {})
        total = 0
        for platform, pdata in img_metrics.items():
            if not isinstance(pdata, dict):
                continue
            for metric, value in pdata.items():
                if not metric.startswith("_"):
                    total += value * weights.get(metric, 0)
        scored.append((fname, total))
    scored.sort(key=lambda x: -x[1])

    return {
        "images_posted": len(posted_images),
        "slots_completed": sum(1 for v in slots.values() if v),
        "top_image": scored[0] if scored else None,
        "worst_image": scored[-1] if len(scored) > 1 else None,
        "total_score": sum(s for _, s in scored),
    }


def load_calendar_today():
    """Load today's content calendar."""
    cal = load_json(VAWN_DIR / "research" / "content_calendar.json")
    today = str(date.today())
    for day in cal.get("calendar", []):
        if day.get("date") == today:
            return day
    return None


def run():
    """Generate the daily briefing note."""
    BRIEFINGS_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")

    print(f"\n{'='*60}")
    print(f"  Daily Briefing -- {today}")
    print(f"{'='*60}")

    # Gather everything
    health = load_health()
    infra = load_infra_status()
    pillar = load_pillar()
    engagement = load_engagement()
    ideation = load_ideation()
    discovery = load_discovery_summary()
    yesterday = load_yesterday_performance()
    calendar = load_calendar_today()

    # Build the note
    lines = [
        "---",
        f"title: Daily Briefing -- {today}",
        f"date: {today}",
        "tags:",
        "  - briefing",
        "  - project/vawn",
        "---",
        "",
        f"# Daily Briefing -- {today}",
        "",
    ]

    # Health status (content pipeline health)
    critical = health.get("critical", [])
    warnings = health.get("warnings", [])
    if critical:
        lines.append("> [!danger] System Issues")
        for c in critical:
            lines.append(f"> {c}")
        lines.append("")
    elif warnings:
        lines.append("> [!warning] {0} warning(s) -- see [[Health -- {1}]]".format(len(warnings), today))
        lines.append("")
    else:
        lines.append("> [!success] All systems healthy")
        lines.append("")

    # Infrastructure status (bulletproofing stack: backend probe, auth, DLQ, alerts)
    infra_issues = infra.get("issues", [])
    if infra_issues:
        lines.append("> [!danger] Infrastructure Issues")
        for issue in infra_issues:
            lines.append(f"> - {issue}")
        lines.append(f">")
        lines.append(f"> Full detail: `C:\\Users\\rdyal\\Vawn\\STATUS.md`")
        lines.append("")
    else:
        lines.append("## Infrastructure")
        lines.append("")
        lines.append("| Layer | Status |")
        lines.append("|---|---|")
        lines.append(f"| Apulu Studio backend | {infra.get('backend_overall','unknown').upper()} |")
        lines.append(f"| Claude auth | {infra.get('auth_status','unknown').upper()} |")
        lines.append(f"| Dead-letter queue | {infra.get('dlq_count',0)} entries |")
        lines.append(f"| Undelivered alerts | {infra.get('undelivered_alerts',0)} pending |")
        lines.append("")
        lines.append("> [!success] Infrastructure green — full detail in `STATUS.md`")
        lines.append("")

    # Today's plan
    today_pillar = pillar.get("today", {}).get("pillar", "Unknown")
    today_day = pillar.get("today", {}).get("day", "")
    lines.append(f"## Today's Plan")
    lines.append("")
    lines.append(f"**Pillar:** =={today_pillar}== ({today_day})")
    lines.append("")

    if calendar:
        for slot_name in ["morning", "midday", "evening"]:
            slot = calendar.get("slots", {}).get(slot_name, {})
            anchor = slot.get("anchor_line", "")
            if anchor:
                lines.append(f"- **{slot_name.title()}:** {anchor}")
        lines.append("")

    # Engagement feedback
    if engagement.get("recommendation"):
        lines.append(f"> [!tip] Engagement Insight")
        lines.append(f"> {engagement['recommendation']}")
        lines.append("")

    # Yesterday's performance
    lines.append("## Yesterday")
    lines.append("")
    lines.append(f"- **Images posted:** {yesterday['images_posted']}")
    lines.append(f"- **Slots completed:** {yesterday['slots_completed']}")
    lines.append(f"- **Total engagement score:** {yesterday['total_score']:.0f}")
    if yesterday.get("top_image"):
        fname, score = yesterday["top_image"]
        lines.append(f"- **Best:** {fname} (score: {score:.0f})")
    lines.append("")

    # Top ideation pick
    ide = ideation.get("ideation", {})
    picks = ide.get("priority_picks", [])
    ideas = ide.get("content_ideas", [])
    if picks:
        top = picks[0]
        lines.append("## Recommended Content")
        lines.append("")
        lines.append(f"> [!abstract] Top Pick: {top.get('title', '')}")
        lines.append(f"> {top.get('reason', '')}")
        lines.append("")
        # Show the full idea details if available
        for idea in ideas:
            if idea.get("rank") == top.get("rank"):
                lines.append(f"| Detail | Value |")
                lines.append(f"|--------|-------|")
                lines.append(f"| Format | {idea.get('format', '?')} |")
                lines.append(f"| Platforms | {', '.join(idea.get('platforms', []))} |")
                lines.append(f"| Confidence | {idea.get('confidence', '?')} |")
                lines.append(f"| Gap | {idea.get('competitive_gap', '?')} |")
                lines.append("")
                break

    # Discovery highlights
    if discovery:
        lines.append("## Discovery Highlights")
        lines.append("")
        for platform, data in discovery.items():
            total = data.get("total", 0)
            lines.append(f"### {platform.upper()} ({total} items)")
            for h in data.get("highlights", [])[:2]:
                lines.append(f"- {h}")
            lines.append("")

    # Week ahead
    week = pillar.get("week_ahead", [])
    if week:
        lines.append("## Week Ahead")
        lines.append("")
        lines.append("| Day | Pillar |")
        lines.append("|-----|--------|")
        for d in week:
            marker = " **← today**" if d.get("date") == str(date.today()) else ""
            lines.append(f"| {d.get('day', '')[:3]} | {d.get('pillar', '')}{marker} |")
        lines.append("")

    # Competitive landscape
    landscape = ide.get("competitive_landscape", {})
    gaps = landscape.get("open_gaps", [])
    if gaps:
        lines.append("## Open Gaps (from ideation)")
        lines.append("")
        for gap in gaps[:3]:
            if isinstance(gap, dict):
                lines.append(f"- {gap.get('description', str(gap))}")
            else:
                lines.append(f"- {gap}")
        lines.append("")

    # Links
    lines.append("## Links")
    lines.append("")
    lines.append(f"- [[Health -- {today}]]")
    lines.append(f"- [[Content Ideation -- {today}]]")
    lines.append(f"- [[X Pipeline -- {today}]]")
    lines.append(f"- [[TikTok Pipeline -- {today}]]")
    lines.append(f"- [[Instagram Pipeline -- {today}]]")
    lines.append(f"- [[Vawn Lyrics Catalog]]")
    lines.append("")

    # Write note
    md_path = BRIEFINGS_DIR / f"Daily Briefing -- {today}.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  [Obsidian] Wrote {md_path.name}")

    # Also save JSON
    save_json(BRIEFINGS_DIR / "daily_briefing_results.json", {
        "date": today,
        "generated": now_iso(),
        "pillar": today_pillar,
        "yesterday": yesterday,
        "health_issues": len(critical) + len(warnings),
        "ideation_top_pick": picks[0] if picks else None,
        "discovery_totals": {k: v.get("total", 0) for k, v in discovery.items()},
    })

    print(f"  Pillar: {today_pillar} | Yesterday: {yesterday['images_posted']} posts, {yesterday['total_score']:.0f} score")
    print(f"{'='*60}\n")

    return True


if __name__ == "__main__":
    run()
