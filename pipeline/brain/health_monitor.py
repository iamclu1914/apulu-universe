"""
health_monitor.py -- System health checks for Apulu Universe.
Runs at 7:15am. Checks every dependency and writes a status report.

Usage:
    python health_monitor.py
"""

import json
import os
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline_config import load_json, save_json, now_iso, today_str

VAWN_DIR = Path(r"C:\Users\rdyal\Vawn")
RESEARCH_DIR = Path(r"C:\Users\rdyal\Apulu Universe\research\vawn")
PIPELINE_CONFIG = Path(r"C:\Users\rdyal\Apulu Universe\pipeline\config")
BRIEFINGS_DIR = RESEARCH_DIR / "briefings"
EXPORTS_DIR = VAWN_DIR / "Social_Media_Exports" / "Instagram_Reel_1080x1920_9-16"


def check_notebooklm():
    """Check if NotebookLM auth is valid."""
    try:
        result = subprocess.run(
            ["notebooklm", "list"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0 and "Notebooks" in result.stdout:
            lines = result.stdout.strip().split("\n")
            count = sum(1 for l in lines if "|" in l and "ID" not in l and "---" not in l)
            return {"status": "ok", "notebooks": count}
        return {"status": "error", "detail": result.stderr[:200] or "Unknown error"}
    except Exception as e:
        return {"status": "error", "detail": str(e)[:200]}


def check_discovery_freshness():
    """Check if discovery pipeline results are fresh (< 24h)."""
    discovery_dir = RESEARCH_DIR / "discovery"
    pipelines = {
        "x": "x_pipeline_results.json",
        "tiktok": "tiktok_pipeline_results.json",
        "instagram": "ig_pipeline_results.json",
        "reddit": "reddit_pipeline_results.json",
    }
    results = {}
    cutoff = datetime.now() - timedelta(hours=24)

    for name, filename in pipelines.items():
        path = discovery_dir / filename
        if not path.exists():
            results[name] = {"status": "missing"}
            continue
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        if mtime > cutoff:
            results[name] = {"status": "fresh", "age_hours": round((datetime.now() - mtime).total_seconds() / 3600, 1)}
        else:
            results[name] = {"status": "stale", "age_hours": round((datetime.now() - mtime).total_seconds() / 3600, 1)}

    return results


def check_bridge():
    """Check if bridge ran today."""
    brief = load_json(VAWN_DIR / "research" / "daily_brief.json")
    enriched = brief.get("_pipeline_enriched", "")
    if enriched == str(date.today()):
        return {"status": "ok", "enriched_today": True}
    return {"status": "stale", "last_enriched": enriched}


def check_catalog_fallback():
    """Check if catalog_agent used fallback bars."""
    brief = load_json(VAWN_DIR / "research" / "daily_brief.json")
    catalog_lines = brief.get("catalog_lines", [])
    fallback_count = sum(1 for l in catalog_lines if l.get("_fallback"))
    if fallback_count > 0:
        return {"status": "warning", "fallback_bars": fallback_count, "total_bars": len(catalog_lines)}
    if not catalog_lines:
        return {"status": "warning", "detail": "No catalog lines in daily brief"}
    return {"status": "ok", "bars": len(catalog_lines)}


def check_posting():
    """Check yesterday's posting results."""
    log = load_json(VAWN_DIR / "posted_log.json")
    yesterday = str(date.today() - timedelta(days=1))

    posted = 0
    platforms_hit = set()
    for filename, entries in log.items():
        if filename.startswith("_"):
            continue
        if yesterday in entries:
            posted += 1
            if isinstance(entries[yesterday], dict):
                platforms_hit.update(entries[yesterday].keys())

    # Check slot tracking
    slots = log.get("_posted_slots", {}).get(yesterday, {})
    slots_completed = sum(1 for v in slots.values() if v)

    return {
        "status": "ok" if posted > 0 else "warning",
        "images_posted": posted,
        "slots_completed": slots_completed,
        "platforms": list(platforms_hit),
    }


def check_image_supply():
    """Check how many unposted images remain."""
    if not EXPORTS_DIR.exists():
        return {"status": "error", "detail": f"Exports dir not found: {EXPORTS_DIR}"}

    all_images = [f for f in os.listdir(EXPORTS_DIR) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    log = load_json(VAWN_DIR / "posted_log.json")
    today_str_val = str(date.today())

    posted_today = set()
    for fname, entries in log.items():
        if not fname.startswith("_") and today_str_val in entries:
            posted_today.add(fname)

    unposted = len(all_images) - len(posted_today)

    status = "ok"
    if unposted < 10:
        status = "warning"
    if unposted < 3:
        status = "critical"

    return {"status": status, "total_images": len(all_images), "unposted_today": unposted}


def check_engagement_feedback():
    """Check if engagement feedback is available."""
    path = PIPELINE_CONFIG / "engagement_feedback.json"
    if not path.exists():
        return {"status": "missing"}
    data = load_json(path)
    best = data.get("best_pillar", "unknown")
    score = data.get("best_pillar_score", 0)
    return {"status": "ok", "best_pillar": best, "score": score}


def check_local_catalog():
    """Check local lyrics catalog status."""
    path = RESEARCH_DIR / "catalog" / "lyrics.json"
    if not path.exists():
        return {"status": "missing"}
    data = load_json(path)
    return {
        "status": "ok",
        "tracks": data.get("track_count", 0),
        "bars": data.get("total_bars", 0),
    }


def run():
    """Run all health checks and write report."""
    BRIEFINGS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  Health Monitor -- {today_str()}")
    print(f"{'='*60}")

    checks = {
        "NotebookLM Auth": check_notebooklm(),
        "Discovery Freshness": check_discovery_freshness(),
        "Bridge": check_bridge(),
        "Catalog Fallback": check_catalog_fallback(),
        "Yesterday's Posts": check_posting(),
        "Image Supply": check_image_supply(),
        "Engagement Feedback": check_engagement_feedback(),
        "Local Catalog": check_local_catalog(),
    }

    # Print results
    critical = []
    warnings = []
    for name, result in checks.items():
        if isinstance(result, dict):
            status = result.get("status", "ok")
        else:
            status = "ok"

        if status in ("error", "critical"):
            marker = "[FAIL]"
            critical.append(name)
        elif status in ("warning", "stale", "missing"):
            marker = "[WARN]"
            warnings.append(name)
        else:
            marker = "[ OK ]"

        print(f"  {marker} {name}: {json.dumps(result, default=str)[:100]}")

    # Write Obsidian note
    today = datetime.now().strftime("%Y-%m-%d")
    _write_obsidian(checks, critical, warnings, today)

    # Save JSON
    save_json(BRIEFINGS_DIR / "health_results.json", {
        "date": today,
        "generated": now_iso(),
        "checks": checks,
        "critical": critical,
        "warnings": warnings,
    })

    print(f"\n  Critical: {len(critical)} | Warnings: {len(warnings)}")
    print(f"{'='*60}\n")

    return checks


def _write_obsidian(checks, critical, warnings, today):
    lines = [
        "---",
        f"title: Health -- {today}",
        f"date: {today}",
        "tags:",
        "  - health",
        "  - project/vawn",
        "  - briefing",
        "---",
        "",
        f"# System Health -- {today}",
        "",
    ]

    if critical:
        lines.append("> [!danger] Critical Issues")
        for c in critical:
            result = checks[c]
            detail = result.get("detail", json.dumps(result, default=str)[:150])
            lines.append(f"> **{c}**: {detail}")
        lines.append("")

    if warnings:
        lines.append("> [!warning] Warnings")
        for w in warnings:
            result = checks[w]
            if isinstance(result, dict):
                detail = result.get("detail", json.dumps(result, default=str)[:150])
            else:
                detail = str(result)[:150]
            lines.append(f"> **{w}**: {detail}")
        lines.append("")

    if not critical and not warnings:
        lines.append("> [!success] All Systems Healthy")
        lines.append("")

    lines.append("## Status")
    lines.append("")
    lines.append("| Check | Status | Detail |")
    lines.append("|-------|--------|--------|")

    for name, result in checks.items():
        if isinstance(result, dict):
            status = result.get("status", "ok")
            # Build detail string
            detail_parts = {k: v for k, v in result.items() if k != "status"}
            detail = ", ".join(f"{k}={v}" for k, v in detail_parts.items())[:80]
        else:
            status = "ok"
            detail = str(result)[:80]

        lines.append(f"| {name} | {status} | {detail} |")

    lines.append("")
    lines.append(f"## Links")
    lines.append(f"- [[Daily Briefing -- {today}]]")
    lines.append(f"- [[Vawn Lyrics Catalog]]")
    lines.append("")

    md_path = BRIEFINGS_DIR / f"Health -- {today}.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  [Obsidian] Wrote {md_path.name}")


if __name__ == "__main__":
    run()
