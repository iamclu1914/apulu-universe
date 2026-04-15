"""
analytics_agent.py — Weekly analytics digest.
Summarizes posting activity, identifies top performers, flags issues.
Schedule: Sunday 9am weekly.
"""

import argparse
import json
import sys
sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

from vawn_config import VAWN_DIR, load_json, save_json, log_run, today_str

LOG_FILE = VAWN_DIR / "posted_log.json"
ENGAGEMENT_LOG = VAWN_DIR / "research" / "engagement_log.json"
REPORT_FILE = VAWN_DIR / "research" / "weekly_report.json"


def analyze_week():
    """Analyze the past 7 days of posting activity."""
    log = load_json(LOG_FILE)
    today = date.today()
    week_start = today - timedelta(days=7)

    # Count posts per platform per day
    daily_posts = defaultdict(lambda: defaultdict(int))
    image_usage = Counter()
    platform_totals = Counter()
    failed_days = []

    for fname, entries in log.items():
        if fname.startswith("_"):
            continue
        for d, platforms in entries.items():
            try:
                post_date = date.fromisoformat(d)
            except (ValueError, TypeError):
                continue
            if week_start <= post_date <= today:
                if isinstance(platforms, list):
                    for p in platforms:
                        daily_posts[d][p] += 1
                        platform_totals[p] += 1
                    image_usage[fname] += len(platforms)

    # Find busiest and quietest days
    day_totals = {d: sum(plats.values()) for d, plats in daily_posts.items()}
    busiest = max(day_totals, key=day_totals.get) if day_totals else None
    quietest = min(day_totals, key=day_totals.get) if day_totals else None

    # Top images
    top_images = image_usage.most_common(5)

    # Days with zero posts
    zero_days = []
    for i in range(7):
        d = str(week_start + timedelta(days=i))
        if d not in daily_posts:
            zero_days.append(d)

    # Engagement data if available
    eng_log = load_json(ENGAGEMENT_LOG)
    total_replies = 0
    if eng_log:
        for d, entries in eng_log.items():
            try:
                if week_start <= date.fromisoformat(d) <= today:
                    if isinstance(entries, list):
                        total_replies += len(entries)
            except (ValueError, TypeError):
                pass

    report = {
        "week": f"{week_start} to {today}",
        "generated": str(today),
        "total_posts": sum(platform_totals.values()),
        "platform_breakdown": dict(platform_totals),
        "daily_activity": {d: dict(plats) for d, plats in sorted(daily_posts.items())},
        "busiest_day": busiest,
        "quietest_day": quietest,
        "zero_post_days": zero_days,
        "top_images": [{"image": img, "post_count": cnt} for img, cnt in top_images],
        "engagement_replies": total_replies,
        "recommendations": [],
    }

    # Generate recommendations
    recs = report["recommendations"]
    if zero_days:
        recs.append(f"Missed {len(zero_days)} day(s): {', '.join(zero_days)}. Check scheduler.")
    if platform_totals.get("tiktok", 0) < 5:
        recs.append("TikTok posting below target (< 5/week). Check video generation.")
    if platform_totals.get("instagram", 0) < 5:
        recs.append("Instagram posting below target. Check Reel generation.")
    if total_replies == 0:
        recs.append("Zero engagement replies this week. Check engagement_agent.")
    expected = 7 * 5 * 3  # 7 days * 5 platforms * 3 posts/day
    actual = sum(platform_totals.values())
    if actual < expected * 0.5:
        recs.append(f"Only {actual}/{expected} expected posts delivered. Investigate failures.")
    if not recs:
        recs.append("All systems nominal. Keep going.")

    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    print(f"\n=== Weekly Analytics Digest — {today_str()} ===\n")

    report = analyze_week()

    print(f"Week: {report['week']}")
    print(f"Total posts: {report['total_posts']}")
    print(f"\nPlatform breakdown:")
    for p, cnt in sorted(report['platform_breakdown'].items()):
        print(f"  {p:>12s}: {cnt}")
    print(f"\nBusiest day: {report['busiest_day']}")
    print(f"Quietest day: {report['quietest_day']}")
    if report['zero_post_days']:
        print(f"Zero-post days: {', '.join(report['zero_post_days'])}")
    print(f"\nTop images:")
    for item in report['top_images']:
        print(f"  {item['post_count']}x — {item['image']}")
    print(f"\nEngagement replies: {report['engagement_replies']}")
    print(f"\nRecommendations:")
    for r in report['recommendations']:
        print(f"  - {r}")

    if not args.test:
        save_json(REPORT_FILE, report)
        print(f"\n[OK] Report saved to {REPORT_FILE}")

    log_run("AnalyticsAgent", "ok", f"Week: {report['total_posts']} posts")
    print(f"\n=== Done ===\n")


if __name__ == "__main__":
    main()
