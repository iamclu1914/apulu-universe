"""
tiktok_pipeline.py -- TikTok discovery pipeline.
Scrapes trending videos by keyword and from tracked accounts using Apify.
Scores by views velocity, engagement rate, and virality signals.

Usage:
    python tiktok_pipeline.py                  # uses vawn config
    python tiktok_pipeline.py --project vawn
    python tiktok_pipeline.py --keywords-only
    python tiktok_pipeline.py --accounts-only
"""

import argparse
import math
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline_config import (
    load_project_config, get_apify_token, get_output_dir,
    save_json, today_str, now_iso,
)
from discovery.apify_client import ApifyRunner


def score_video(video):
    """Score a TikTok video by virality and engagement signals."""
    likes = video.get("diggCount", 0) or video.get("likes", 0) or 0
    comments = video.get("commentCount", 0) or video.get("comments", 0) or 0
    shares = video.get("shareCount", 0) or video.get("shares", 0) or 0
    plays = video.get("playCount", 0) or video.get("plays", 0) or 0
    followers = video.get("authorMeta", {}).get("fans", 0) or 0

    engagement = likes + (comments * 3) + (shares * 5)

    # Engagement rate relative to plays
    eng_rate = (engagement / max(plays, 1)) * 100 if plays > 0 else 0

    # Virality: shares are the strongest TikTok signal
    virality = shares * 5 + (plays / max(1, followers)) if followers > 0 else shares * 5

    # Velocity
    created = video.get("createTime", 0)
    hours_old = 24
    if created and isinstance(created, (int, float)) and created > 1000000000:
        try:
            dt = datetime.fromtimestamp(created)
            hours_old = max(1, (datetime.now() - dt).total_seconds() / 3600)
        except (ValueError, OSError):
            pass
    velocity = engagement / hours_old

    # Discovery: underdog bonus -- low followers, high plays
    discovery = 0
    if followers > 0 and plays > 0:
        discovery = math.log10(max(plays / followers, 1)) * 10

    total = velocity + virality + (eng_rate * 2) + discovery

    return {
        "score": round(total, 2),
        "velocity": round(velocity, 2),
        "virality": round(virality, 2),
        "engagement": engagement,
        "engagement_rate": round(eng_rate, 2),
        "discovery": round(discovery, 2),
        "plays": plays,
        "shares": shares,
        "hours_old": round(hours_old, 1),
    }


def normalize_video(video):
    """Extract relevant fields from raw Apify TikTok data."""
    author = video.get("authorMeta", {})
    music = video.get("musicMeta", {})
    return {
        "id": video.get("id", ""),
        "text": video.get("text", ""),
        "author": {
            "username": author.get("name", video.get("author", "")),
            "nickname": author.get("nickName", ""),
            "followers": author.get("fans", 0),
            "verified": author.get("verified", False),
        },
        "plays": video.get("playCount", 0) or video.get("plays", 0) or 0,
        "likes": video.get("diggCount", 0) or video.get("likes", 0) or 0,
        "comments": video.get("commentCount", 0) or video.get("comments", 0) or 0,
        "shares": video.get("shareCount", 0) or video.get("shares", 0) or 0,
        "duration": video.get("videoMeta", {}).get("duration", 0) or video.get("duration", 0),
        "created": video.get("createTime", ""),
        "url": video.get("webVideoUrl", f"https://tiktok.com/@{author.get('name', '')}/video/{video.get('id', '')}"),
        "music": music.get("musicName", "") if music else "",
        "hashtags": [h.get("name", "") for h in video.get("hashtags", []) if h],
    }


def search_keywords(runner, keywords, max_results=50):
    """Search TikTok for videos matching keywords."""
    print(f"\n[TikTok Pipeline] Searching {len(keywords)} keywords...")
    input_data = {
        "searchQueries": keywords[:10],
        "resultsPerPage": min(max_results, 50),
        "shouldDownloadVideos": False,
    }

    try:
        items = runner.run_actor("clockworks/tiktok-scraper", input_data, timeout=180)
        return items
    except Exception as e:
        print(f"  [ERROR] Keyword search failed: {e}")
        return []


def scrape_accounts(runner, accounts, max_per_account=20):
    """Scrape recent videos from tracked TikTok accounts."""
    profiles = [f"https://www.tiktok.com/@{a.lstrip('@')}" for a in accounts]

    print(f"\n[TikTok Pipeline] Scraping {len(accounts)} accounts...")
    input_data = {
        "profiles": profiles,
        "resultsPerPage": max_per_account,
        "shouldDownloadVideos": False,
    }

    try:
        items = runner.run_actor("clockworks/tiktok-scraper", input_data, timeout=180)
        return items
    except Exception as e:
        print(f"  [ERROR] Account scrape failed: {e}")
        return []


def deduplicate(videos):
    """Remove duplicates by video ID."""
    seen = set()
    unique = []
    for v in videos:
        vid = v.get("id", "")
        if vid and vid not in seen:
            seen.add(vid)
            unique.append(v)
    return unique


def run(project_name="vawn", keywords_only=False, accounts_only=False):
    """Run the TikTok discovery pipeline."""
    config = load_project_config(project_name)
    tt_config = config["pipelines"]["tiktok"]

    if not tt_config.get("enabled"):
        print("[TikTok Pipeline] Disabled in config, skipping.")
        return None

    token = get_apify_token(config)
    runner = ApifyRunner(token)
    output_dir = get_output_dir(config, "discovery")

    all_raw = []

    if not accounts_only:
        keyword_videos = search_keywords(
            runner,
            tt_config["keywords"],
            max_results=tt_config.get("max_results", 50),
        )
        all_raw.extend(keyword_videos)

    if not keywords_only:
        account_videos = scrape_accounts(
            runner,
            tt_config["accounts"],
            max_per_account=20,
        )
        all_raw.extend(account_videos)

    all_raw = deduplicate(all_raw)
    print(f"\n[TikTok Pipeline] {len(all_raw)} unique videos after dedup")

    results = []
    for raw in all_raw:
        video = normalize_video(raw)
        scoring = score_video(raw)
        video["scoring"] = scoring
        results.append(video)

    results.sort(key=lambda v: v["scoring"]["score"], reverse=True)

    output = {
        "pipeline": "tiktok",
        "project": project_name,
        "generated": now_iso(),
        "total_videos": len(results),
        "top_20": results[:20],
        "all_results": results,
    }

    output_path = output_dir / "tiktok_pipeline_results.json"
    save_json(output_path, output)
    print(f"\n[TikTok Pipeline] Saved {len(results)} videos to {output_path}")

    # Print top 5
    print(f"\n{'='*60}")
    print(f"  TikTok Pipeline -- Top 5 ({today_str()})")
    print(f"{'='*60}")
    for i, v in enumerate(results[:5], 1):
        s = v["scoring"]
        print(f"\n  #{i}  @{v['author']['username']} ({v['plays']:,} plays)")
        print(f"  Score: {s['score']} | Virality: {s['virality']} | {s['shares']} shares")
        print(f"  {v['text'][:120]}")
        print(f"  {v['url']}")
    print(f"\n{'='*60}\n")

    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TikTok discovery pipeline")
    parser.add_argument("--project", default="vawn", help="Project config to use")
    parser.add_argument("--keywords-only", action="store_true")
    parser.add_argument("--accounts-only", action="store_true")
    args = parser.parse_args()

    run(args.project, args.keywords_only, args.accounts_only)
