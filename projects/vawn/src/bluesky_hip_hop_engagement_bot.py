"""
Enhanced Bluesky Engagement Bot for Trending Hip-Hop Posts
APU-164: Enhanced targeting for trending hip-hop content on Bluesky
"""

import argparse
import json
import random
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from vawn_config import VAWN_DIR, load_json, save_json, log_run, today_str

ENGAGEMENT_LOG = VAWN_DIR / "database" / "bluesky_hip_hop_engagement.json"

# Hip-hop specific search terms for better targeting
HIP_HOP_SEARCH_TERMS = [
    "hip hop music", "rap music", "new rap song", "hip hop artist",
    "rap bars", "freestyle rap", "hip hop beat", "trap music",
    "boom bap", "lyrical rap", "underground hip hop", "indie rap",
    "hip hop producer", "rap album", "hip hop single", "rap verse",
    "hip hop track", "rap artist", "hip hop drops", "new hip hop",
    "#hiphop", "#rap", "#rapmusic", "#hiphopmusic", "#newmusic",
    "#rapper", "#hiphopculture", "#freestyle", "#bars"
]

# Keywords to identify music posts vs other content
MUSIC_KEYWORDS = [
    "song", "track", "album", "single", "music", "beat", "lyrics",
    "verse", "bars", "freestyle", "mixtape", "producer", "studio",
    "recording", "drop", "release", "listen", "stream", "spotify",
    "soundcloud", "bandcamp", "audio", "melody", "rhythm"
]

# Minimum engagement thresholds for "trending" content
MIN_LIKES_FOR_TRENDING = 5
MIN_REPOSTS_FOR_TRENDING = 2
MAX_LIKES_PER_RUN = 15
MAX_FOLLOWS_PER_RUN = 3

class BlueskyHipHopBot:
    def __init__(self):
        self.client = None
        self.handle = None
        self.liked_count = 0
        self.followed_count = 0
        self.session_stats = {
            "searches_performed": 0,
            "posts_evaluated": 0,
            "hip_hop_posts_found": 0,
            "trending_posts_found": 0,
            "likes_given": 0,
            "follows_given": 0
        }

    def get_credentials(self):
        """Get Bluesky credentials from config"""
        creds = load_json(VAWN_DIR / "credentials.json")
        handle = creds.get("bluesky_handle")
        app_password = creds.get("bluesky_app_password")
        return handle, app_password

    def connect(self):
        """Connect to Bluesky"""
        try:
            from atproto import Client
        except ImportError:
            print("[ERROR] atproto library not installed. Run: pip install atproto")
            return False

        handle, app_password = self.get_credentials()
        if not handle or not app_password:
            print("[ERROR] Bluesky credentials not found in credentials.json")
            return False

        self.client = Client()
        try:
            self.client.login(handle, app_password)
            self.handle = handle
            print(f"[OK] Connected to Bluesky as {handle}")
            return True
        except Exception as e:
            print(f"[ERROR] Bluesky login failed: {e}")
            return False

    def is_music_post(self, post_text):
        """Check if post is actually about music"""
        text_lower = post_text.lower()
        music_score = sum(1 for keyword in MUSIC_KEYWORDS if keyword in text_lower)
        return music_score >= 2  # Require at least 2 music-related keywords

    def is_trending_post(self, post):
        """Determine if a post is trending based on engagement"""
        try:
            like_count = post.like_count if hasattr(post, 'like_count') else 0
            repost_count = post.repost_count if hasattr(post, 'repost_count') else 0
            reply_count = post.reply_count if hasattr(post, 'reply_count') else 0

            # Calculate engagement score
            engagement_score = (like_count * 1) + (repost_count * 2) + (reply_count * 1.5)

            # Check if meets trending thresholds
            is_trending = (
                like_count >= MIN_LIKES_FOR_TRENDING or
                repost_count >= MIN_REPOSTS_FOR_TRENDING or
                engagement_score >= 10
            )

            if is_trending:
                self.session_stats["trending_posts_found"] += 1

            return is_trending, engagement_score
        except Exception:
            return False, 0

    def search_and_engage(self, search_term, max_results=20):
        """Search for posts and engage with trending hip-hop content"""
        try:
            print(f"[SEARCH] Searching for: '{search_term}'")
            results = self.client.app.bsky.feed.search_posts({
                "q": search_term,
                "limit": max_results
            })

            posts = results.posts if hasattr(results, 'posts') else []
            self.session_stats["searches_performed"] += 1

            # Shuffle to randomize engagement pattern
            random.shuffle(posts)

            for post in posts:
                if self.liked_count >= MAX_LIKES_PER_RUN:
                    break

                self.session_stats["posts_evaluated"] += 1

                # Skip own posts
                if post.author.handle == self.handle:
                    continue

                post_text = post.record.text if hasattr(post.record, 'text') else ""

                # Check if it's actually about music
                if not self.is_music_post(post_text):
                    continue

                self.session_stats["hip_hop_posts_found"] += 1

                # Check if it's trending
                is_trending, engagement_score = self.is_trending_post(post)

                if is_trending:
                    success = self.like_post(post, engagement_score)
                    if success:
                        # Small delay to avoid rate limiting
                        time.sleep(random.uniform(1, 3))

        except Exception as e:
            print(f"[WARN] Search failed for '{search_term}': {e}")

    def like_post(self, post, engagement_score):
        """Like a post and log the action"""
        try:
            self.client.like(uri=post.uri, cid=post.cid)
            self.liked_count += 1
            self.session_stats["likes_given"] += 1

            author_handle = post.author.handle
            post_preview = post.record.text[:80] + "..." if len(post.record.text) > 80 else post.record.text

            print(f"  [LIKE] @{author_handle} (score: {engagement_score:.1f})")
            print(f"      {post_preview}")

            return True
        except Exception as e:
            print(f"  [WARN] Failed to like post: {e}")
            return False

    def run_engagement_session(self, test_mode=False):
        """Run a full engagement session"""
        if not self.connect():
            return {"error": "Connection failed"}

        print(f"\n=== Hip-Hop Engagement Session - {datetime.now().strftime('%Y-%m-%d %H:%M')} ===")

        # Select random search terms for this session
        session_terms = random.sample(HIP_HOP_SEARCH_TERMS, min(5, len(HIP_HOP_SEARCH_TERMS)))

        for term in session_terms:
            if self.liked_count >= MAX_LIKES_PER_RUN:
                break
            self.search_and_engage(term)

            # Brief pause between searches
            time.sleep(random.uniform(2, 5))

        # Log results
        if not test_mode:
            self.log_session()

        print(f"\n[STATS] Session Summary:")
        print(f"    Searches: {self.session_stats['searches_performed']}")
        print(f"    Posts evaluated: {self.session_stats['posts_evaluated']}")
        print(f"    Hip-hop posts found: {self.session_stats['hip_hop_posts_found']}")
        print(f"    Trending posts: {self.session_stats['trending_posts_found']}")
        print(f"    Likes given: {self.liked_count}")
        print(f"    Follows: {self.followed_count}")

        return {
            "likes": self.liked_count,
            "follows": self.followed_count,
            "stats": self.session_stats
        }

    def log_session(self):
        """Log the engagement session"""
        ENGAGEMENT_LOG.parent.mkdir(parents=True, exist_ok=True)

        log_data = load_json(ENGAGEMENT_LOG) if ENGAGEMENT_LOG.exists() else {}
        today = today_str()

        if today not in log_data:
            log_data[today] = []

        session_log = {
            "timestamp": datetime.now().isoformat(),
            "likes": self.liked_count,
            "follows": self.followed_count,
            "stats": self.session_stats
        }

        log_data[today].append(session_log)
        save_json(ENGAGEMENT_LOG, log_data)

        # Also log to main system
        log_run("BlueskyHipHopBot", "success",
               f"Likes: {self.liked_count}, Trending posts: {self.session_stats['trending_posts_found']}")

def main():
    parser = argparse.ArgumentParser(description="Enhanced Bluesky Hip-Hop Engagement Bot")
    parser.add_argument("--test", action="store_true", help="Test mode (no logging)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    bot = BlueskyHipHopBot()
    results = bot.run_engagement_session(test_mode=args.test)

    if "error" in results:
        print(f"\n[ERROR] {results['error']}")
        sys.exit(1)

    print(f"\n=== Session Complete ===")

if __name__ == "__main__":
    main()