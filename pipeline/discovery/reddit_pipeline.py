"""
reddit_pipeline.py -- Reddit discovery pipeline.
Scrapes hot/top posts from configured subreddits using Apify.
Scores by upvote velocity, comment depth, and discussion quality.

Usage:
    python reddit_pipeline.py                  # uses vawn config
    python reddit_pipeline.py --project vawn
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
    """Score a Reddit post by discussion quality and engagement."""
    upvotes = post.get("upVotes", 0) or post.get("score", 0) or 0
    comments = post.get("numberOfComments", 0) or post.get("numComments", 0) or 0
    upvote_ratio = post.get("upVoteRatio", 0.5) or 0.5
    awards = post.get("totalAwards", 0) or 0

    engagement = upvotes + (comments * 3) + (awards * 10)

    # Comment-to-upvote ratio = discussion depth
    discussion = (comments / max(upvotes, 1)) * 100

    # Controversy signal: lower ratio = more divisive = more interesting
    controversy = (1 - upvote_ratio) * 50

    # Velocity
    created = post.get("createdAt", "") or post.get("created", "")
    hours_old = 24
    if created:
        try:
            if isinstance(created, (int, float)):
                dt = datetime.fromtimestamp(created)
            else:
                dt = datetime.fromisoformat(str(created).replace("Z", "+00:00"))
            hours_old = max(1, (datetime.now(dt.tzinfo if dt.tzinfo else None) - dt).total_seconds() / 3600)
        except (ValueError, TypeError, OSError):
            pass
    velocity = engagement / hours_old

    total = velocity + discussion + controversy + math.log10(max(engagement, 1)) * 5

    return {
        "score": round(total, 2),
        "velocity": round(velocity, 2),
        "discussion": round(discussion, 2),
        "controversy": round(controversy, 2),
        "engagement": engagement,
        "upvotes": upvotes,
        "comments": comments,
        "upvote_ratio": upvote_ratio,
        "hours_old": round(hours_old, 1),
    }


def normalize_post(post):
    """Extract relevant fields from raw Apify Reddit data."""
    return {
        "id": post.get("id", ""),
        "title": post.get("title", ""),
        "text": (post.get("body", "") or post.get("selftext", "") or "")[:1000],
        "author": post.get("username", post.get("author", "")),
        "subreddit": post.get("communityName", post.get("subreddit", "")),
        "upvotes": post.get("upVotes", 0) or post.get("score", 0) or 0,
        "comments": post.get("numberOfComments", 0) or post.get("numComments", 0) or 0,
        "upvote_ratio": post.get("upVoteRatio", 0),
        "created": post.get("createdAt", ""),
        "url": post.get("url", ""),
        "is_video": post.get("isVideo", False),
        "flair": post.get("flair", ""),
    }


def scrape_subreddits(runner, subreddits, sort="hot", max_results=30, actor="trudax/reddit-scraper-lite"):
    """Scrape posts from configured subreddits."""
    urls = [f"https://www.reddit.com/r/{sub}/{sort}/" for sub in subreddits]

    print(f"\n[Reddit Pipeline] Scraping {len(subreddits)} subreddits ({sort})...")
    input_data = {
        "startUrls": [{"url": u} for u in urls],
        "maxItems": max_results,
        "maxPostCount": max_results,
        "sort": sort,
    }

    try:
        items = runner.run_actor(actor, input_data, timeout=180)
        return items
    except Exception as e:
        print(f"  [ERROR] Subreddit scrape failed: {e}")
        return []


def deduplicate(posts):
    """Remove duplicates by post ID."""
    seen = set()
    unique = []
    for p in posts:
        pid = p.get("id", "")
        if pid and pid not in seen:
            seen.add(pid)
            unique.append(p)
    return unique


def run(project_name="vawn"):
    """Run the Reddit discovery pipeline."""
    config = load_project_config(project_name)
    reddit_config = config["pipelines"]["reddit"]

    if not reddit_config.get("enabled"):
        print("[Reddit Pipeline] Disabled in config, skipping.")
        return None

    token = get_apify_token(config)
    runner = ApifyRunner(token)
    output_dir = get_output_dir(config, "discovery")

    raw_posts = scrape_subreddits(
        runner,
        reddit_config["subreddits"],
        sort=reddit_config.get("sort", "hot"),
        max_results=reddit_config.get("max_results", 30),
        actor=reddit_config.get("actor", "trudax/reddit-scraper-lite"),
    )

    raw_posts = deduplicate(raw_posts)
    print(f"\n[Reddit Pipeline] {len(raw_posts)} unique posts after dedup")

    results = []
    for raw in raw_posts:
        post = normalize_post(raw)
        scoring = score_post(raw)
        post["scoring"] = scoring
        results.append(post)

    results.sort(key=lambda p: p["scoring"]["score"], reverse=True)

    output = {
        "pipeline": "reddit",
        "project": project_name,
        "generated": now_iso(),
        "total_posts": len(results),
        "top_20": results[:20],
        "all_results": results,
    }

    output_path = output_dir / "reddit_pipeline_results.json"
    save_json(output_path, output)
    print(f"\n[Reddit Pipeline] Saved {len(results)} posts to {output_path}")

    # Print top 5
    print(f"\n{'='*60}")
    print(f"  Reddit Pipeline -- Top 5 ({today_str()})")
    print(f"{'='*60}")
    for i, p in enumerate(results[:5], 1):
        s = p["scoring"]
        print(f"\n  #{i}  r/{p['subreddit']} -- u/{p['author']}")
        print(f"  Score: {s['score']} | {s['upvotes']} upvotes | {s['comments']} comments")
        print(f"  {p['title'][:120]}")
        if p["url"]:
            print(f"  {p['url']}")
    print(f"\n{'='*60}\n")

    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reddit discovery pipeline")
    parser.add_argument("--project", default="vawn", help="Project config to use")
    args = parser.parse_args()

    run(args.project)
