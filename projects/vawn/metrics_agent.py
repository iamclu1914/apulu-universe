"""
metrics_agent.py — Daily engagement metrics pull for Vawn social media.
Runs daily at 7am. Pulls engagement data 24h after each post.
Schedule: Daily 7am via setup_scheduler.bat

Currently auto-pulls from:
  - Bluesky (via atproto API)

Manual/future support for:
  - Instagram, TikTok, Threads, X (no read API in LATE — posting only)

The real value is the SCORING and TRACKING infrastructure.
Even manual entries get scored and feed back into image selection.

Usage:
  python metrics_agent.py           # daily pull
  python metrics_agent.py --test    # dry run, no file writes
  python metrics_agent.py --add IMAGE DATE PLATFORM likes=N comments=N saves=N shares=N
"""

import argparse
import json
import sys
sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from vawn_config import (
    VAWN_DIR, RESEARCH_DIR, CREDS_FILE,
    load_json, save_json, log_run, today_str,
)

LOG_FILE = VAWN_DIR / "posted_log.json"
METRICS_FILE = RESEARCH_DIR / "metrics_log.json"
BASE_URL = "https://apulustudio.onrender.com/api"

# Engagement score weights — saves and shares are worth more because
# algorithms reward them (signals deeper intent than a double-tap).
WEIGHTS = {
    "likes": 1,
    "comments": 3,
    "saves": 5,
    "shares": 4,
    "reposts": 4,    # bluesky
    "retweets": 4,   # x
    "views": 0.01,   # tiktok — volume metric, low weight per unit
    "replies": 3,    # threads / bluesky
}


def load_metrics():
    """Load the metrics log. Returns dict keyed by image filename."""
    return load_json(METRICS_FILE)


def save_metrics(data):
    save_json(METRICS_FILE, data)


def calc_score(platform_data):
    """Calculate engagement score for a single platform's metrics dict."""
    score = 0
    for metric, value in platform_data.items():
        if metric.startswith("_") or not isinstance(value, (int, float)):
            continue
        weight = WEIGHTS.get(metric, 0)
        score += value * weight
    return score


def calc_image_total_score(image_data):
    """Sum engagement scores across all dates and platforms for one image."""
    total = 0
    for date_str, platforms in image_data.items():
        for platform, metrics in platforms.items():
            total += calc_score(metrics)
    return total


# ── Bluesky engagement pull ──────────────────────────────────────────────────

def fetch_bluesky_engagement(handle, app_password, posted_images, post_date):
    """
    Fetch engagement for Vawn's Bluesky posts from a given date.
    Searches the author feed and matches posts by date.
    Returns dict: {image_filename: {likes, reposts, replies}}
    """
    try:
        from atproto import Client
    except ImportError:
        print("[WARN] atproto not installed — skipping Bluesky metrics")
        return {}

    results = {}
    try:
        client = Client()
        client.login(handle, app_password)

        # Fetch recent posts from the author's feed
        # The feed returns posts in reverse chronological order
        feed = client.get_author_feed(actor=handle, limit=50)
        if not feed or not feed.feed:
            print("[WARN] Bluesky feed empty or inaccessible")
            return {}

        target_date = str(post_date)

        for item in feed.feed:
            post = item.post
            # Check if post is from the target date
            indexed = post.indexed_at or ""
            if not indexed.startswith(target_date):
                continue

            # We found a post from the target date — pull metrics
            metrics = {
                "likes": post.like_count or 0,
                "reposts": post.repost_count or 0,
                "replies": post.reply_count or 0,
            }

            # Match to an image if possible.
            # Bluesky posts don't carry the original filename, so we assign
            # metrics to whichever images were posted to bluesky on that date.
            # If there are multiple bluesky posts on the same day, we collect all.
            if not results:
                # First match — assign to the first image that posted to bluesky
                for img in posted_images:
                    results[img] = metrics
                    break
            else:
                # Additional bluesky posts — assign to next unmatched image
                for img in posted_images:
                    if img not in results:
                        results[img] = metrics
                        break

        if results:
            print(f"[OK] Bluesky: pulled metrics for {len(results)} post(s)")
        else:
            print(f"[INFO] Bluesky: no posts found for {target_date}")

    except Exception as e:
        print(f"[WARN] Bluesky engagement pull failed: {e}")

    return results


# ── Main pull logic ──────────────────────────────────────────────────────────

def get_yesterday_posts(log):
    """Find all images posted yesterday, grouped by platform."""
    yesterday = str(date.today() - timedelta(days=1))
    posts = {}  # {filename: [platforms]}

    for fname, entries in log.items():
        if fname.startswith("_"):
            continue
        if yesterday in entries:
            platforms = entries[yesterday]
            if isinstance(platforms, list):
                posts[fname] = platforms

    return yesterday, posts


def pull_metrics(test_mode=False):
    """Pull engagement metrics for yesterday's posts."""
    log = load_json(LOG_FILE)
    metrics = load_metrics()
    yesterday, posts = get_yesterday_posts(log)

    if not posts:
        print(f"[INFO] No posts found for {yesterday}")
        return metrics

    print(f"[OK] Found {len(posts)} image(s) posted on {yesterday}")
    for img, platforms in posts.items():
        print(f"  {img} -> {', '.join(platforms)}")

    # Load Bluesky credentials
    creds = load_json(CREDS_FILE)
    bsky_handle = creds.get("bluesky_handle", "")
    bsky_password = creds.get("bluesky_app_password", "")

    # Pull Bluesky engagement
    bluesky_images = [img for img, plats in posts.items() if "bluesky" in plats]
    bsky_metrics = {}
    if bluesky_images and bsky_handle and bsky_password:
        bsky_metrics = fetch_bluesky_engagement(
            bsky_handle, bsky_password, bluesky_images, yesterday,
        )

    # Build metrics entries for each image
    for img, platforms in posts.items():
        if img not in metrics:
            metrics[img] = {}
        if yesterday not in metrics[img]:
            metrics[img][yesterday] = {}

        day_data = metrics[img][yesterday]

        # Bluesky — auto-pulled
        if "bluesky" in platforms and img in bsky_metrics:
            day_data["bluesky"] = bsky_metrics[img]

        # Other platforms — stub entries so structure exists for manual updates
        for platform in platforms:
            if platform == "bluesky":
                continue  # already handled
            if platform not in day_data:
                day_data[platform] = {
                    "_note": "manual entry needed — no read API available",
                }

    if not test_mode:
        save_metrics(metrics)
        print(f"[OK] Metrics saved to {METRICS_FILE}")

    return metrics


# ── Daily summary ────────────────────────────────────────────────────────────

def print_summary(metrics):
    """Print a daily engagement summary: top 3, worst 3, totals."""
    scored = []
    for img, dates in metrics.items():
        total = calc_image_total_score(dates)
        scored.append((img, total))

    scored.sort(key=lambda x: -x[1])

    # Filter out zero-score images (no real data yet)
    with_data = [(img, s) for img, s in scored if s > 0]

    print(f"\n{'='*60}")
    print(f"  ENGAGEMENT SUMMARY — {today_str()}")
    print(f"{'='*60}")
    print(f"\n  Total images tracked: {len(scored)}")
    total_score = sum(s for _, s in scored)
    print(f"  Total engagement score: {total_score}")

    if with_data:
        print(f"\n  TOP 3 PERFORMERS:")
        for img, s in with_data[:3]:
            print(f"    {s:>6.0f}  {img}")

        print(f"\n  BOTTOM 3 PERFORMERS:")
        bottom = with_data[-3:] if len(with_data) >= 3 else with_data
        for img, s in reversed(bottom):
            print(f"    {s:>6.0f}  {img}")
    else:
        print(f"\n  No engagement data collected yet.")
        print(f"  Bluesky data will auto-pull. Other platforms need manual entry.")

    print(f"\n{'='*60}\n")


# ── Manual add ───────────────────────────────────────────────────────────────

def manual_add(image, date_str, platform, raw_metrics):
    """
    Manually add engagement metrics for an image.
    raw_metrics is a list of key=value strings like ["likes=12", "comments=3"]
    """
    metrics = load_metrics()

    parsed = {}
    for item in raw_metrics:
        if "=" not in item:
            print(f"[ERROR] Bad format: {item} — expected key=value")
            return
        k, v = item.split("=", 1)
        parsed[k.strip()] = int(v.strip())

    if image not in metrics:
        metrics[image] = {}
    if date_str not in metrics[image]:
        metrics[image][date_str] = {}

    metrics[image][date_str][platform] = parsed
    save_metrics(metrics)
    print(f"[OK] Added {platform} metrics for {image} on {date_str}: {parsed}")
    print(f"     Score: {calc_score(parsed)}")


# ── Entry point ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Vawn engagement metrics agent")
    parser.add_argument("--test", action="store_true", help="Dry run — no file writes")
    parser.add_argument(
        "--add", nargs="+", metavar="ARG",
        help="Manual add: IMAGE DATE PLATFORM key=value key=value ...",
    )
    args = parser.parse_args()

    if args.add:
        if len(args.add) < 4:
            print("[ERROR] Usage: --add IMAGE DATE PLATFORM likes=N comments=N ...")
            return
        image, date_str, platform = args.add[0], args.add[1], args.add[2]
        raw_metrics = args.add[3:]
        manual_add(image, date_str, platform, raw_metrics)
        return

    print(f"\n=== Metrics Agent — {today_str()} ===\n")

    metrics = pull_metrics(test_mode=args.test)
    print_summary(metrics)

    if not args.test:
        log_run("MetricsAgent", "ok", f"Pulled metrics for yesterday")

    print("=== Done ===\n")


if __name__ == "__main__":
    main()
