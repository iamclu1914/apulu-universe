"""
instagram_pipeline.py -- Instagram discovery pipeline.
Scrapes posts by hashtag and from tracked accounts using Apify.
Scores content by engagement rate and discovery potential.

Usage:
    python instagram_pipeline.py                  # uses vawn config
    python instagram_pipeline.py --project vawn
    python instagram_pipeline.py --hashtags-only
    python instagram_pipeline.py --accounts-only
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


def score_post(post):
    """Score an Instagram post by engagement and discovery potential."""
    likes = post.get("likesCount", 0) or 0
    comments = post.get("commentsCount", 0) or 0
    views = post.get("videoViewCount", 0) or post.get("videoPlayCount", 0) or 0
    followers = post.get("ownerFollowerCount", 0) or post.get("followersCount", 0) or 0

    engagement = likes + (comments * 3)

    # Engagement rate relative to follower count
    eng_rate = (engagement / max(followers, 1)) * 100 if followers > 0 else 0

    # Velocity: engagement per hour
    timestamp = post.get("timestamp", "")
    hours_old = 24
    if timestamp:
        try:
            dt = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
            hours_old = max(1, (datetime.now(dt.tzinfo) - dt).total_seconds() / 3600)
        except (ValueError, TypeError):
            pass
    velocity = engagement / hours_old

    # Discovery score: small accounts with high engagement = underrated content
    discovery = eng_rate * math.log10(max(engagement, 1))

    total = velocity + discovery + (eng_rate * 2)

    return {
        "score": round(total, 2),
        "velocity": round(velocity, 2),
        "engagement": engagement,
        "engagement_rate": round(eng_rate, 2),
        "discovery": round(discovery, 2),
        "views": views,
        "likes": likes,
        "comments": comments,
        "hours_old": round(hours_old, 1),
    }


def normalize_post(post):
    """Extract relevant fields from raw Apify IG data."""
    music_info = post.get("musicInfo")
    music = ""
    if isinstance(music_info, dict):
        music = music_info.get("title", "") or music_info.get("music_title", "")
    return {
        "id": post.get("id", ""),
        "shortcode": post.get("shortCode", ""),
        "type": post.get("type", post.get("productType", "")),
        "caption": (post.get("caption", "") or "")[:500],
        "author": {
            "username": post.get("ownerUsername", ""),
            "full_name": post.get("ownerFullName", ""),
            "followers": post.get("ownerFollowerCount", 0) or post.get("followersCount", 0) or 0,
        },
        "likes": post.get("likesCount", 0) or 0,
        "comments": post.get("commentsCount", 0) or 0,
        "views": post.get("videoViewCount", 0) or post.get("videoPlayCount", 0) or 0,
        "timestamp": post.get("timestamp", ""),
        "url": post.get("url", f"https://instagram.com/p/{post.get('shortCode', '')}"),
        "hashtags": post.get("hashtags", []),
        "is_reel": post.get("productType") == "clips" or post.get("type") == "Video",
        "music": music,
    }


def search_hashtags(runner, hashtags, max_results=50):
    """Search Instagram for posts matching hashtags."""
    tags = [h.lstrip("#") for h in hashtags]
    urls = [f"https://www.instagram.com/explore/tags/{tag}/" for tag in tags]

    print(f"\n[IG Pipeline] Searching {len(tags)} hashtags...")
    input_data = {
        "directUrls": urls,
        "resultsLimit": max_results,
        "resultsType": "posts",
    }

    try:
        items = runner.run_actor("apify/instagram-scraper", input_data, timeout=180)
        return items
    except Exception as e:
        print(f"  [ERROR] Hashtag search failed: {e}")
        return []


def scrape_accounts(runner, accounts, max_per_account=20):
    """Scrape recent posts from tracked IG accounts."""
    urls = [f"https://instagram.com/{a.lstrip('@')}/" for a in accounts]

    print(f"\n[IG Pipeline] Scraping {len(accounts)} accounts...")
    input_data = {
        "directUrls": urls,
        "resultsLimit": max_per_account,
        "resultsType": "posts",
    }

    try:
        items = runner.run_actor("apify/instagram-scraper", input_data, timeout=240)
        return items
    except Exception as e:
        print(f"  [ERROR] Account scrape failed: {e}")
        return []


def deduplicate(posts):
    """Remove duplicate posts by ID or shortcode."""
    seen = set()
    unique = []
    for p in posts:
        pid = p.get("id", "") or p.get("shortCode", "")
        if pid and pid not in seen:
            seen.add(pid)
            unique.append(p)
    return unique


def run(project_name="vawn", hashtags_only=False, accounts_only=False):
    """Run the Instagram discovery pipeline."""
    config = load_project_config(project_name)
    ig_config = config["pipelines"]["instagram"]

    if not ig_config.get("enabled"):
        print("[IG Pipeline] Disabled in config, skipping.")
        return None

    token = get_apify_token(config)
    runner = ApifyRunner(token)
    output_dir = get_output_dir(config, "discovery")

    all_raw = []

    if not accounts_only:
        hashtag_posts = search_hashtags(
            runner,
            ig_config["hashtags"],
            max_results=ig_config.get("max_results", 50),
        )
        all_raw.extend(hashtag_posts)

    if not hashtags_only:
        account_posts = scrape_accounts(
            runner,
            ig_config["accounts"],
            max_per_account=20,
        )
        all_raw.extend(account_posts)

    all_raw = deduplicate(all_raw)
    print(f"\n[IG Pipeline] {len(all_raw)} unique posts after dedup")

    results = []
    for raw in all_raw:
        post = normalize_post(raw)
        scoring = score_post(raw)
        post["scoring"] = scoring
        results.append(post)

    results.sort(key=lambda p: p["scoring"]["score"], reverse=True)

    output = {
        "pipeline": "instagram",
        "project": project_name,
        "generated": now_iso(),
        "total_posts": len(results),
        "top_20": results[:20],
        "all_results": results,
    }

    output_path = output_dir / "ig_pipeline_results.json"
    save_json(output_path, output)
    print(f"\n[IG Pipeline] Saved {len(results)} posts to {output_path}")

    # Print top 5
    print(f"\n{'='*60}")
    print(f"  Instagram Pipeline -- Top 5 ({today_str()})")
    print(f"{'='*60}")
    for i, p in enumerate(results[:5], 1):
        s = p["scoring"]
        reel = " [REEL]" if p["is_reel"] else ""
        print(f"\n  #{i}  @{p['author']['username']}{reel}")
        print(f"  Score: {s['score']} | Eng Rate: {s['engagement_rate']}% | {s['likes']} likes")
        print(f"  {p['caption'][:120]}...")
        print(f"  {p['url']}")
    print(f"\n{'='*60}\n")

    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Instagram discovery pipeline")
    parser.add_argument("--project", default="vawn", help="Project config to use")
    parser.add_argument("--hashtags-only", action="store_true")
    parser.add_argument("--accounts-only", action="store_true")
    args = parser.parse_args()

    run(args.project, args.hashtags_only, args.accounts_only)
