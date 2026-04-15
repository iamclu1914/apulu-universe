"""
engagement_bot.py — Proactive engagement on Bluesky (only platform with full API access).
Likes and follows accounts in Vawn's niche after each posting slot.
Other platforms (IG, TikTok, X, Threads) require manual engagement or native app.
Schedule: Runs after each posting slot (9:30am, 1pm, 8:30pm).
"""

import argparse
import json
import random
import sys
sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from datetime import date, datetime
from pathlib import Path

from vawn_config import VAWN_DIR, load_json, save_json, log_run, today_str

ENGAGEMENT_BOT_LOG = VAWN_DIR / "research" / "engagement_bot_log.json"

# Bluesky search terms for finding relevant posts
SEARCH_TERMS = [
    "hip hop", "rap", "new music", "indie rap", "boom bap",
    "lyrical rap", "atlanta rap", "underground hip hop",
    "trap soul", "new artist", "bars",
]

MAX_LIKES_PER_RUN = 10
MAX_FOLLOWS_PER_RUN = 3


def get_bluesky_credentials():
    """Get Bluesky handle and app password from the Apulu Studio database or credentials."""
    # Try credentials.json first
    creds = load_json(VAWN_DIR / "credentials.json")
    handle = creds.get("bluesky_handle")
    app_password = creds.get("bluesky_app_password")

    if handle and app_password:
        return handle, app_password

    # If not in creds, we can't proceed
    return None, None


def bluesky_engagement():
    """Like and follow relevant posts/accounts on Bluesky."""
    handle, app_password = get_bluesky_credentials()

    if not handle or not app_password:
        print("[INFO] Bluesky credentials not found in credentials.json")
        print("[INFO] Add 'bluesky_handle' and 'bluesky_app_password' to credentials.json")
        print("[INFO] Example: {\"bluesky_handle\": \"vawn.bsky.social\", \"bluesky_app_password\": \"xxxx-xxxx-xxxx-xxxx\"}")
        return {"likes": 0, "follows": 0}

    try:
        from atproto import Client
    except ImportError:
        print("[INFO] atproto not installed. Run: pip install atproto")
        return {"likes": 0, "follows": 0}

    client = Client()
    try:
        client.login(handle, app_password)
        print(f"[OK] Logged into Bluesky as {handle}")
    except Exception as e:
        print(f"[FAIL] Bluesky login failed: {e}")
        return {"likes": 0, "follows": 0}

    # Search for relevant posts
    term = random.choice(SEARCH_TERMS)
    print(f"[OK] Searching Bluesky for: '{term}'")

    liked = 0
    followed = 0
    followed_dids = set()

    try:
        results = client.app.bsky.feed.search_posts({"q": term, "limit": 20})
        posts = results.posts if hasattr(results, 'posts') else []

        random.shuffle(posts)

        for post in posts:
            if liked >= MAX_LIKES_PER_RUN:
                break

            # Skip own posts
            if post.author.handle == handle:
                continue

            # Like the post
            try:
                client.like(uri=post.uri, cid=post.cid)
                liked += 1
                print(f"  [LIKE] @{post.author.handle}: {post.record.text[:60]}...")
            except Exception:
                pass

            # Auto-follow disabled — likes only to avoid cluttering the following list

    except Exception as e:
        print(f"[WARN] Search failed: {e}")

    print(f"\n[OK] Bluesky: {liked} likes, {followed} follows")
    return {"likes": liked, "follows": followed}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    today = today_str()
    now = datetime.now().strftime("%H:%M")
    print(f"\n=== Engagement Bot — {today} {now} ===\n")

    # Bluesky (full API access)
    print("--- Bluesky ---")
    bsky_results = bluesky_engagement()

    # Other platforms — log reminder
    print("\n--- Other Platforms (manual) ---")
    print("[INFO] Instagram: Use the app to like/comment on similar artists' posts")
    print("[INFO] TikTok: Engage with #fyp content in Vawn's niche")
    print("[INFO] X: Like/retweet from comparable artists' followers")
    print("[INFO] Threads: Reply to trending conversations in hip-hop")

    # Log
    if not args.test:
        log = load_json(ENGAGEMENT_BOT_LOG)
        if today not in log:
            log[today] = []
        log[today].append({
            "time": datetime.now().isoformat(),
            "bluesky": bsky_results,
        })
        save_json(ENGAGEMENT_BOT_LOG, log)

    log_run("EngagementBot", "ok",
            f"Bluesky: {bsky_results['likes']} likes, {bsky_results['follows']} follows")
    print(f"\n=== Done ===\n")


if __name__ == "__main__":
    main()
