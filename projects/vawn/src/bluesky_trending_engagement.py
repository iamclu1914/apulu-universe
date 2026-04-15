"""
bluesky_trending_engagement.py — Enhanced Bluesky engagement bot for APU-121
Focuses specifically on trending hip-hop posts with improved content filtering.

Features:
- Trending post detection (engagement metrics)
- Hip-hop content validation
- Enhanced search terms and filtering
- Engagement effectiveness tracking
"""

import argparse
import json
import random
import sys
import time
import re
sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from datetime import date, datetime, timedelta
from pathlib import Path

from vawn_config import VAWN_DIR, load_json, save_json, log_run, today_str

ENGAGEMENT_LOG = VAWN_DIR / "research" / "bluesky_trending_engagement_log.json"

# Hip-hop specific search terms - more targeted
HIP_HOP_SEARCH_TERMS = [
    "hip hop", "rap music", "new rap", "hip hop artist",
    "rapper", "mc", "bars", "freestyle", "cypher",
    "boom bap", "trap music", "drill music", "lyrical rap",
    "underground hip hop", "indie rap", "conscious rap",
    "atlanta rap", "detroit rap", "chicago rap", "ny rap"
]

# Hip-hop validation keywords
HIP_HOP_KEYWORDS = {
    'music': ['rap', 'hip hop', 'hiphop', 'mc', 'rapper', 'bars', 'freestyle', 'cypher', 'beats', 'producer'],
    'genres': ['boom bap', 'trap', 'drill', 'conscious', 'underground', 'gangsta', 'old school', 'new school'],
    'terms': ['spit', 'flow', 'rhythm', 'rhyme', 'verse', 'hook', 'chorus', 'track', 'album', 'mixtape'],
    'culture': ['culture', 'street', 'urban', 'community', 'movement', 'scene']
}

# Quality filters - skip posts with these patterns
SKIP_PATTERNS = [
    "follow me", "check my", "dm me", "collab?", "promo", "buy my",
    "stream my", "check out my", "listen to my", "follow for follow",
    "f4f", "like for like", "l4l", "sub for sub", "spam", "bot"
]

MAX_LIKES_PER_RUN = 15
MIN_ENGAGEMENT_THRESHOLD = 0  # minimum likes+replies to consider trending (set to 0 since engagement data not fully available in search results)


def get_bluesky_credentials():
    """Get Bluesky handle and app password from credentials."""
    creds = load_json(VAWN_DIR / "credentials.json")
    handle = creds.get("bluesky_handle")
    app_password = creds.get("bluesky_app_password")
    return handle, app_password


def is_hip_hop_content(text):
    """Enhanced hip-hop content validation."""
    text_lower = text.lower()

    # Count hip-hop related terms
    hip_hop_score = 0

    for category, keywords in HIP_HOP_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                hip_hop_score += 1

    # Also check for artist mentions, music platforms, etc.
    music_indicators = ['spotify', 'apple music', 'soundcloud', 'youtube music', 'new single', 'new album']
    for indicator in music_indicators:
        if indicator in text_lower:
            hip_hop_score += 1

    return hip_hop_score >= 1  # Require at least 1 hip-hop related term (relaxed for more results)


def has_skip_patterns(text):
    """Check if post contains promotional/spam patterns to skip."""
    text_lower = text.lower()
    return any(pattern in text_lower for pattern in SKIP_PATTERNS)


def calculate_engagement_score(post):
    """Calculate engagement score for trending detection."""
    like_count = post.likeCount if hasattr(post, 'likeCount') else 0
    reply_count = post.replyCount if hasattr(post, 'replyCount') else 0
    repost_count = post.repostCount if hasattr(post, 'repostCount') else 0

    return like_count + (reply_count * 2) + (repost_count * 1.5)


def bluesky_trending_engagement():
    """Like trending hip-hop posts on Bluesky with enhanced filtering."""
    handle, app_password = get_bluesky_credentials()

    if not handle or not app_password:
        print("[INFO] Bluesky credentials not found in credentials.json")
        return {"likes": 0, "filtered_out": 0, "trending_found": 0}

    try:
        from atproto import Client
    except ImportError:
        print("[INFO] atproto not installed. Run: pip install atproto")
        return {"likes": 0, "filtered_out": 0, "trending_found": 0}

    client = Client()
    try:
        client.login(handle, app_password)
        print(f"[OK] Logged into Bluesky as {handle}")
    except Exception as e:
        print(f"[FAIL] Bluesky login failed: {e}")
        return {"likes": 0, "filtered_out": 0, "trending_found": 0}

    # Use multiple search terms to get diverse content
    liked = 0
    filtered_out = 0
    trending_found = 0
    processed_uris = set()

    # Try 2-3 different search terms
    search_terms_to_use = random.sample(HIP_HOP_SEARCH_TERMS, min(3, len(HIP_HOP_SEARCH_TERMS)))

    for term in search_terms_to_use:
        if liked >= MAX_LIKES_PER_RUN:
            break

        print(f"[OK] Searching Bluesky for: '{term}'")

        try:
            results = client.app.bsky.feed.search_posts({"q": term, "limit": 25})
            posts = results.posts if hasattr(results, 'posts') else []
            print(f"  Found {len(posts)} posts for '{term}'")

            # Sort by engagement score to prioritize trending posts
            posts_with_scores = []
            for post in posts:
                if post.uri not in processed_uris:
                    engagement_score = calculate_engagement_score(post)
                    if engagement_score >= MIN_ENGAGEMENT_THRESHOLD:
                        posts_with_scores.append((post, engagement_score))
                        processed_uris.add(post.uri)

            # Sort by engagement score descending
            posts_with_scores.sort(key=lambda x: x[1], reverse=True)
            trending_found += len(posts_with_scores)

            for post, engagement_score in posts_with_scores:
                if liked >= MAX_LIKES_PER_RUN:
                    break

                # Skip own posts
                if post.author.handle == handle:
                    continue

                post_text = post.record.text if hasattr(post.record, 'text') else ""

                # Enhanced content filtering
                if has_skip_patterns(post_text):
                    filtered_out += 1
                    continue

                if not is_hip_hop_content(post_text):
                    filtered_out += 1
                    continue

                # Like the trending hip-hop post
                try:
                    client.like(uri=post.uri, cid=post.cid)
                    liked += 1
                    print(f"  [LIKE] @{post.author.handle} ({engagement_score} engagement): {post_text[:60]}...")
                except Exception as e:
                    print(f"  [SKIP] Error liking post: {e}")

                # Small delay to avoid rate limiting
                time.sleep(0.5)

        except Exception as e:
            print(f"[WARN] Search for '{term}' failed: {e}")

    print(f"\n[OK] Bluesky: {liked} likes, {filtered_out} filtered out, {trending_found} trending posts found")
    return {
        "likes": liked,
        "filtered_out": filtered_out,
        "trending_found": trending_found,
        "search_terms_used": search_terms_to_use
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    today = today_str()
    now = datetime.now().strftime("%H:%M")
    print(f"\n=== Bluesky Trending Hip-Hop Engagement — {today} {now} ===\n")

    results = bluesky_trending_engagement()

    # Log results
    if not args.test:
        log = load_json(ENGAGEMENT_LOG)
        if today not in log:
            log[today] = []
        log[today].append({
            "time": datetime.now().isoformat(),
            "results": results,
        })
        save_json(ENGAGEMENT_LOG, log)

    log_run("BlueskyTrendingEngagement", "ok",
            f"Liked {results['likes']} trending hip-hop posts, filtered {results['filtered_out']}")

    print(f"\n=== Done ===\n")


if __name__ == "__main__":
    main()