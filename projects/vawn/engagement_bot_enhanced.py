"""
engagement_bot_enhanced.py — Enhanced proactive engagement on Bluesky with health monitoring.
Enhanced for APU-50 by Dex - Community Agent with APU-37 resilience patterns.

Features:
- API health checking and performance monitoring
- Enhanced error handling with classification
- Structured logging for analytics
- Graceful degradation and recovery strategies
- Engagement effectiveness tracking

Schedule: Runs after each posting slot (9:30am, 1pm, 8:30pm).
"""

import argparse
import json
import random
import sys
import time
sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from datetime import date, datetime, timedelta
from pathlib import Path

from vawn_config import VAWN_DIR, load_json, save_json, log_run, today_str

ENGAGEMENT_BOT_LOG = VAWN_DIR / "research" / "engagement_bot_enhanced_log.json"
ENGAGEMENT_HEALTH_LOG = VAWN_DIR / "research" / "engagement_health_log.json"

# Bluesky search terms for finding relevant posts
SEARCH_TERMS = [
    "hip hop", "rap", "new music", "indie rap", "boom bap",
    "lyrical rap", "atlanta rap", "underground hip hop",
    "trap soul", "new artist", "bars", "freestyle",
    "producer", "beat maker", "studio", "recording",
]

# Enhanced configuration
MAX_LIKES_PER_RUN = 10
MAX_FOLLOWS_PER_RUN = 3
API_TIMEOUT = 10  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Quality filters - skip posts with these patterns
SKIP_PATTERNS = [
    "follow me", "check my", "dm me", "collab?", "promo",
    "buy my", "stream my", "check out my", "listen to my",
    "follow for follow", "f4f", "like for like", "l4l",
]


def get_bluesky_credentials():
    """Get Bluesky handle and app password from credentials with validation."""
    try:
        creds = load_json(VAWN_DIR / "credentials.json")
        handle = creds.get("bluesky_handle")
        app_password = creds.get("bluesky_app_password")

        if not handle or not app_password:
            return None, None, "Missing bluesky_handle or bluesky_app_password in credentials.json"

        # Basic validation
        if not handle or len(handle) < 5:
            return None, None, "Invalid bluesky_handle format"

        if not app_password or len(app_password) < 10:
            return None, None, "Invalid bluesky_app_password format"

        return handle, app_password, None

    except Exception as e:
        return None, None, f"Error loading credentials: {e}"


def check_bluesky_health(client):
    """Check Bluesky API health and measure response time."""
    start_time = datetime.now()

    try:
        # Simple API test - get own profile
        profile = client.get_profile(client.me.did)
        response_time = (datetime.now() - start_time).total_seconds() * 1000

        return {
            "available": True,
            "response_time_ms": int(response_time),
            "timestamp": datetime.now().isoformat(),
            "status": "healthy"
        }

    except Exception as e:
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        return {
            "available": False,
            "response_time_ms": int(response_time),
            "timestamp": datetime.now().isoformat(),
            "status": "unhealthy",
            "error": str(e)
        }


def log_health_status(health_data):
    """Log API health data for monitoring."""
    try:
        health_log = load_json(ENGAGEMENT_HEALTH_LOG)
        today = today_str()

        if today not in health_log:
            health_log[today] = []

        health_log[today].append(health_data)

        # Keep only last 30 days
        cutoff_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        health_log = {k: v for k, v in health_log.items() if k >= cutoff_date}

        save_json(ENGAGEMENT_HEALTH_LOG, health_log)
    except Exception as e:
        print(f"[WARN] Could not log health data: {e}")


def filter_quality_posts(posts, handle):
    """Filter out low-quality posts and promotional content."""
    filtered_posts = []

    for post in posts:
        # Skip own posts
        if post.author.handle == handle:
            continue

        # Get post text
        post_text = getattr(post.record, 'text', '').lower()

        # Skip posts with promotional patterns
        if any(pattern in post_text for pattern in SKIP_PATTERNS):
            continue

        # Skip very short posts (likely low engagement)
        if len(post_text.strip()) < 10:
            continue

        # Skip posts with too many hashtags (likely spam)
        hashtag_count = post_text.count('#')
        if hashtag_count > 5:
            continue

        filtered_posts.append(post)

    return filtered_posts


def engage_with_retries(client, action, *args, **kwargs):
    """Execute engagement action with retry logic."""
    for attempt in range(MAX_RETRIES):
        try:
            result = action(*args, **kwargs)
            return True, None
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                return False, str(e)

            # Wait before retry
            time.sleep(RETRY_DELAY * (attempt + 1))

    return False, "Max retries exceeded"


def bluesky_engagement():
    """Enhanced Bluesky engagement with health checking and analytics."""
    # Initialize metrics
    metrics = {
        "likes": 0,
        "follows": 0,
        "errors": 0,
        "search_term": None,
        "posts_processed": 0,
        "posts_filtered": 0,
        "api_health": {},
        "performance": {},
        "start_time": datetime.now().isoformat()
    }

    # Get credentials
    handle, app_password, cred_error = get_bluesky_credentials()

    if cred_error:
        print(f"[FAIL] Credential error: {cred_error}")
        print("[INFO] Add 'bluesky_handle' and 'bluesky_app_password' to credentials.json")
        print("[INFO] Example: {\"bluesky_handle\": \"vawn.bsky.social\", \"bluesky_app_password\": \"xxxx-xxxx-xxxx-xxxx\"}")
        metrics["errors"] += 1
        return metrics

    # Check dependencies
    try:
        from atproto import Client
    except ImportError:
        print("[FAIL] atproto not installed. Run: pip install atproto")
        metrics["errors"] += 1
        return metrics

    # Initialize client
    client = Client()

    # Authenticate with retry logic
    login_success = False
    for attempt in range(MAX_RETRIES):
        try:
            client.login(handle, app_password)
            login_success = True
            print(f"[OK] Logged into Bluesky as {handle}")
            break
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                print(f"[FAIL] Bluesky login failed after {MAX_RETRIES} attempts: {e}")
                metrics["errors"] += 1
                return metrics
            time.sleep(RETRY_DELAY * (attempt + 1))

    if not login_success:
        metrics["errors"] += 1
        return metrics

    # Check API health
    print("[INFO] Checking Bluesky API health...")
    health_data = check_bluesky_health(client)
    metrics["api_health"] = health_data
    log_health_status(health_data)

    if not health_data["available"]:
        print(f"[WARN] API health check failed: {health_data.get('error', 'Unknown error')}")
        print("[INFO] Proceeding with reduced functionality...")
    else:
        print(f"[OK] API healthy (response: {health_data['response_time_ms']}ms)")

    # Select search term
    term = random.choice(SEARCH_TERMS)
    metrics["search_term"] = term
    print(f"[OK] Searching Bluesky for: '{term}'")

    # Search with timeout
    search_start = datetime.now()
    try:
        results = client.app.bsky.feed.search_posts({"q": term, "limit": 25})
        search_time = (datetime.now() - search_start).total_seconds() * 1000
        metrics["performance"]["search_time_ms"] = int(search_time)

        posts = results.posts if hasattr(results, 'posts') else []
        metrics["posts_processed"] = len(posts)

        # Filter for quality
        filtered_posts = filter_quality_posts(posts, handle)
        metrics["posts_filtered"] = len(posts) - len(filtered_posts)

        print(f"[OK] Found {len(posts)} posts, {len(filtered_posts)} after quality filtering")

    except Exception as e:
        print(f"[FAIL] Search failed: {e}")
        metrics["errors"] += 1
        return metrics

    # Engage with posts
    engagement_start = datetime.now()
    random.shuffle(filtered_posts)

    for post in filtered_posts:
        if metrics["likes"] >= MAX_LIKES_PER_RUN:
            break

        # Like the post with retry logic
        success, error = engage_with_retries(
            client, client.like,
            uri=post.uri, cid=post.cid
        )

        if success:
            metrics["likes"] += 1
            # Handle Unicode in post text safely for Windows console
            safe_text = post.record.text[:60].encode('ascii', 'replace').decode('ascii')
            print(f"  [LIKE] @{post.author.handle}: {safe_text}...")
        else:
            print(f"  [FAIL] Like failed for @{post.author.handle}: {error}")
            metrics["errors"] += 1

    engagement_time = (datetime.now() - engagement_start).total_seconds() * 1000
    metrics["performance"]["engagement_time_ms"] = int(engagement_time)

    # Calculate total time
    total_time = (datetime.now() - datetime.fromisoformat(metrics["start_time"])).total_seconds() * 1000
    metrics["performance"]["total_time_ms"] = int(total_time)

    print(f"\n[OK] Engagement complete: {metrics['likes']} likes, {metrics['follows']} follows")
    print(f"[OK] Performance: {metrics['performance']['total_time_ms']}ms total, {metrics['errors']} errors")

    return metrics


def main():
    parser = argparse.ArgumentParser(description="Enhanced Bluesky engagement bot")
    parser.add_argument("--test", action="store_true", help="Test mode - don't save logs")
    parser.add_argument("--health-only", action="store_true", help="Only check API health")
    args = parser.parse_args()

    today = today_str()
    now = datetime.now().strftime("%H:%M")
    print(f"\n=== Enhanced Engagement Bot — {today} {now} ===\n")

    if args.health_only:
        # Quick health check mode
        try:
            from atproto import Client
            handle, app_password, error = get_bluesky_credentials()
            if error:
                print(f"[FAIL] {error}")
                return

            client = Client()
            client.login(handle, app_password)
            health_data = check_bluesky_health(client)
            log_health_status(health_data)

            if health_data["available"]:
                print(f"[OK] API healthy (response: {health_data['response_time_ms']}ms)")
            else:
                print(f"[FAIL] API unhealthy: {health_data.get('error', 'Unknown error')}")
        except Exception as e:
            print(f"[FAIL] Health check failed: {e}")
        return

    # Full engagement run
    print("--- Enhanced Bluesky Engagement ---")
    metrics = bluesky_engagement()

    # Other platforms — reminder with analytics suggestion
    print("\n--- Other Platforms (manual) ---")
    print("[INFO] Instagram: Use the app to like/comment on similar artists' posts")
    print("[INFO] TikTok: Engage with #fyp content in Vawn's niche")
    print("[INFO] X: Like/retweet from comparable artists' followers")
    print("[INFO] Threads: Reply to trending conversations in hip-hop")
    print("[INFO] Consider tracking manual engagement metrics for full picture")

    # Enhanced logging
    if not args.test:
        # Main engagement log
        log = load_json(ENGAGEMENT_BOT_LOG)
        if today not in log:
            log[today] = []

        log_entry = {
            "time": datetime.now().isoformat(),
            "version": "enhanced",
            "bluesky": {
                "likes": metrics["likes"],
                "follows": metrics["follows"]
            },
            "metrics": metrics,
            "success": metrics["errors"] == 0
        }

        log[today].append(log_entry)
        save_json(ENGAGEMENT_BOT_LOG, log)

    # Log to main system
    status = "ok" if metrics["errors"] == 0 else "warning"
    summary = f"Enhanced: {metrics['likes']} likes, {metrics['follows']} follows"
    if metrics["errors"] > 0:
        summary += f", {metrics['errors']} errors"
    if metrics.get("performance", {}).get("total_time_ms"):
        summary += f", {metrics['performance']['total_time_ms']}ms"

    log_run("EngagementBotEnhanced", status, summary)

    print(f"\n=== Enhanced Engagement Complete ===")
    print(f"Results: {summary}")
    print(f"Health: API {'[OK] healthy' if metrics['api_health'].get('available', False) else '[WARN] degraded'}")
    print()


if __name__ == "__main__":
    main()