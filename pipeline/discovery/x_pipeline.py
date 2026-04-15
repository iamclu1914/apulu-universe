"""
x_pipeline.py -- X/Twitter discovery pipeline.
Scrapes tweets by keyword and from tracked accounts using Apify.
Scores and ranks tweets by engagement velocity and relevance.
Outputs structured results to project output directory.

Usage:
    python x_pipeline.py                  # uses vawn config
    python x_pipeline.py --project vawn   # explicit project
    python x_pipeline.py --keywords-only  # skip account scraping
    python x_pipeline.py --accounts-only  # skip keyword search
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline_config import (
    load_project_config, get_apify_token, get_output_dir,
    save_json, load_json, today_str, now_iso,
)
from discovery.apify_client import ApifyRunner


def score_tweet(tweet):
    """Score a tweet by engagement velocity and signal quality.

    Scoring signals:
    - likes, retweets, replies, quotes, views
    - velocity: engagement relative to tweet age
    - authority: follower count of author
    """
    likes = tweet.get("likeCount", 0) or 0
    retweets = tweet.get("retweetCount", 0) or 0
    replies = tweet.get("replyCount", 0) or 0
    quotes = tweet.get("quoteCount", 0) or 0
    views = tweet.get("viewCount", 0) or 0
    followers = tweet.get("author", {}).get("followers", 0) or 0

    # Raw engagement score
    engagement = likes + (retweets * 3) + (replies * 2) + (quotes * 4)

    # Velocity: normalize by hours since posted
    created = tweet.get("createdAt", "")
    hours_old = 24  # default
    if created:
        try:
            dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            hours_old = max(1, (datetime.now(dt.tzinfo) - dt).total_seconds() / 3600)
        except (ValueError, TypeError):
            pass
    velocity = engagement / hours_old

    # Authority bonus (log scale to avoid mega-accounts dominating)
    import math
    authority = math.log10(max(followers, 1)) * 5

    # Views-to-engagement ratio (signals genuine interest vs bot traffic)
    engagement_rate = (engagement / max(views, 1)) * 100 if views > 0 else 0

    total = velocity + authority + (engagement_rate * 2)

    return {
        "score": round(total, 2),
        "velocity": round(velocity, 2),
        "authority": round(authority, 2),
        "engagement": engagement,
        "engagement_rate": round(engagement_rate, 2),
        "views": views,
        "hours_old": round(hours_old, 1),
    }


def normalize_tweet(tweet):
    """Extract relevant fields from raw Apify tweet data."""
    author = tweet.get("author", {})
    return {
        "id": tweet.get("id", ""),
        "text": tweet.get("text", tweet.get("full_text", "")),
        "author": {
            "handle": author.get("userName", author.get("screen_name", "")),
            "name": author.get("name", ""),
            "followers": author.get("followers", author.get("followersCount", 0)),
            "verified": author.get("isVerified", author.get("isBlueVerified", False)),
        },
        "created_at": tweet.get("createdAt", ""),
        "likes": tweet.get("likeCount", 0) or 0,
        "retweets": tweet.get("retweetCount", 0) or 0,
        "replies": tweet.get("replyCount", 0) or 0,
        "quotes": tweet.get("quoteCount", 0) or 0,
        "views": tweet.get("viewCount", 0) or 0,
        "url": tweet.get("url", ""),
        "media": [m.get("url", "") if isinstance(m, dict) else str(m) for m in tweet.get("media", []) if m],
        "hashtags": tweet.get("hashtags", []),
    }


def search_keywords(runner, keywords, max_results=100):
    """Search X for tweets matching keywords."""
    # Single OR query -- keeps it to one search
    query = " OR ".join(f'"{kw}"' for kw in keywords[:8])

    print(f"\n[X Pipeline] Searching: {query[:100]}...")
    input_data = {
        "searchTerms": [query],
        "maxTweets": max_results,
        "sort": "Top",
        "tweetLanguage": "en",
    }

    try:
        items = runner.run_actor("apidojo/tweet-scraper", input_data, timeout=120)
        return items
    except Exception as e:
        print(f"  [ERROR] Keyword search failed: {e}")
        return []


def scrape_accounts(runner, accounts, max_per_account=20):
    """Scrape recent tweets from tracked accounts."""
    all_tweets = []
    # Clean handles
    handles = [a.lstrip("@") for a in accounts]

    print(f"\n[X Pipeline] Scraping {len(handles)} accounts...")
    input_data = {
        "twitterHandles": handles,
        "maxTweets": max_per_account * len(handles),
        "sort": "Latest",
    }

    try:
        items = runner.run_actor("apidojo/tweet-scraper", input_data, timeout=180)
        return items
    except Exception as e:
        print(f"  [ERROR] Account scrape failed: {e}")
        return []


def deduplicate(tweets):
    """Remove duplicate tweets by ID."""
    seen = set()
    unique = []
    for t in tweets:
        tid = t.get("id", "")
        if tid and tid not in seen:
            seen.add(tid)
            unique.append(t)
    return unique


def run(project_name="vawn", keywords_only=False, accounts_only=False):
    """Run the X/Twitter discovery pipeline."""
    config = load_project_config(project_name)
    x_config = config["pipelines"]["x"]

    if not x_config.get("enabled"):
        print("[X Pipeline] Disabled in config, skipping.")
        return None

    token = get_apify_token(config)
    runner = ApifyRunner(token)
    output_dir = get_output_dir(config, "discovery")

    all_raw = []

    # Keyword search
    if not accounts_only:
        keyword_tweets = search_keywords(
            runner,
            x_config["keywords"],
            max_results=x_config.get("max_results", 100),
        )
        all_raw.extend(keyword_tweets)

    # Account scraping
    if not keywords_only:
        account_tweets = scrape_accounts(
            runner,
            x_config["accounts"],
            max_per_account=20,
        )
        all_raw.extend(account_tweets)

    # Deduplicate
    all_raw = deduplicate(all_raw)
    print(f"\n[X Pipeline] {len(all_raw)} unique tweets after dedup")

    # Normalize and score
    results = []
    for raw in all_raw:
        tweet = normalize_tweet(raw)
        scoring = score_tweet(raw)
        tweet["scoring"] = scoring
        results.append(tweet)

    # Sort by score descending
    results.sort(key=lambda t: t["scoring"]["score"], reverse=True)

    # Save full results
    output = {
        "pipeline": "x",
        "project": project_name,
        "generated": now_iso(),
        "total_tweets": len(results),
        "top_20": results[:20],
        "all_results": results,
    }

    output_path = output_dir / "x_pipeline_results.json"
    save_json(output_path, output)
    print(f"\n[X Pipeline] Saved {len(results)} tweets to {output_path}")

    # Print top 5
    print(f"\n{'='*60}")
    print(f"  X/Twitter Pipeline -- Top 5 ({today_str()})")
    print(f"{'='*60}")
    for i, t in enumerate(results[:5], 1):
        s = t["scoring"]
        print(f"\n  #{i}  @{t['author']['handle']} ({t['author']['followers']:,} followers)")
        print(f"  Score: {s['score']} | Velocity: {s['velocity']} | Engagement: {s['engagement']}")
        print(f"  {t['text'][:120]}...")
        if t["url"]:
            print(f"  {t['url']}")
    print(f"\n{'='*60}\n")

    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="X/Twitter discovery pipeline")
    parser.add_argument("--project", default="vawn", help="Project config to use")
    parser.add_argument("--keywords-only", action="store_true")
    parser.add_argument("--accounts-only", action="store_true")
    args = parser.parse_args()

    run(args.project, args.keywords_only, args.accounts_only)
