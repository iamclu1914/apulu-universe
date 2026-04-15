"""
apu81_enhanced_engagement_bot.py — APU-81 Enhanced engagement bot for Vawn.
Improvements over engagement_bot.py:
- Intelligent content filtering to avoid spam/promotional content
- Artist collaboration discovery
- Engagement timing optimization
- Integration with APU-44 monitoring
- Quality scoring for meaningful engagement

Created by: Dex - Community Agent (APU-81)
"""

import argparse
import json
import random
import sys
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import VAWN_DIR, load_json, save_json, log_run, today_str

# Configuration
ENHANCED_ENGAGEMENT_LOG = VAWN_DIR / "research" / "apu81_engagement_bot_log.json"
COLLABORATION_TARGETS = VAWN_DIR / "research" / "collaboration_targets.json"

# Enhanced search terms with quality indicators
SEARCH_TERMS = {
    "primary": ["hip hop", "rap", "new music", "indie rap", "boom bap"],
    "collaboration": ["collab", "feature", "open verse", "looking for", "need artist"],
    "community": ["atlanta rap", "brooklyn hip hop", "underground hip hop", "lyrical rap"],
    "industry": ["trap soul", "new artist", "bars", "freestyle", "cypher"]
}

# Content quality filters
SPAM_INDICATORS = [
    "follow me", "check my", "dm me", "promo", "buy now", "click link",
    "subscribe", "follow4follow", "f4f", "like4like", "l4l",
    "cashapp", "venmo", "paypal", "onlyfans", "🔗", "link in bio"
]

PROMOTIONAL_PATTERNS = [
    r"(?i)\b(promo|promotion|advertising|ad|sponsored)\b",
    r"(?i)\b(buy|purchase|sale|discount|\$\d+)\b",
    r"(?i)\b(follow.*back|follow.*follow|sub.*sub)\b",
    r"(?i)dm\s*me|message\s*me",
    r"(?i)link\s*in\s*bio|linktree",
]

QUALITY_INDICATORS = [
    "just dropped", "new track", "working on", "in the studio", "proud of",
    "excited to share", "grateful", "thank you", "blessed", "journey",
    "process", "creating", "inspired", "collaboration", "feature"
]

MAX_LIKES_PER_RUN = 12  # Increased from 10
MAX_FOLLOWS_PER_RUN = 2  # Decreased from 3 to be more selective
ENGAGEMENT_COOLDOWN_HOURS = 2  # Minimum hours between engagements with same account


def get_bluesky_credentials():
    """Get Bluesky handle and app password from credentials."""
    creds = load_json(VAWN_DIR / "credentials.json")
    handle = creds.get("bluesky_handle")
    app_password = creds.get("bluesky_app_password")

    if handle and app_password:
        return handle, app_password

    return None, None


def calculate_content_quality_score(post) -> Dict[str, Any]:
    """
    APU-81: Intelligent content quality scoring system.
    Returns score (0-10) and reasoning for engagement decision.
    """
    score = 5.0  # Base neutral score
    factors = {"reasons": [], "penalties": [], "bonuses": []}

    text = post.record.text.lower()
    author = post.author

    # SPAM PENALTIES (-3 to -5)
    for spam_word in SPAM_INDICATORS:
        if spam_word in text:
            score -= 3
            factors["penalties"].append(f"Spam indicator: '{spam_word}'")

    # PROMOTIONAL PATTERN PENALTIES (-2 to -4)
    for pattern in PROMOTIONAL_PATTERNS:
        if re.search(pattern, text):
            score -= 2
            factors["penalties"].append(f"Promotional pattern detected")

    # QUALITY BONUSES (+1 to +3)
    quality_found = []
    for indicator in QUALITY_INDICATORS:
        if indicator in text:
            score += 1.5
            quality_found.append(indicator)

    if quality_found:
        factors["bonuses"].append(f"Quality indicators: {', '.join(quality_found[:2])}")

    # AUTHOR QUALITY INDICATORS
    # Verified or established accounts get bonus
    if hasattr(author, 'verified') and author.verified:
        score += 2
        factors["bonuses"].append("Verified account")

    # Account with decent follower count (not spam, not mega-famous)
    if hasattr(author, 'followersCount'):
        followers = author.followersCount
        if 100 <= followers <= 50000:  # Sweet spot for real artists
            score += 1
            factors["bonuses"].append(f"Good follower range ({followers})")
        elif followers < 10:  # Likely spam or new account
            score -= 1
            factors["penalties"].append("Very low followers")

    # POST ENGAGEMENT INDICATORS
    # Good engagement ratio suggests quality content
    if hasattr(post, 'likeCount') and hasattr(post, 'repostCount'):
        total_engagement = (post.likeCount or 0) + (post.repostCount or 0)
        if total_engagement > 5:
            score += 1
            factors["bonuses"].append(f"Good engagement ({total_engagement})")

    # COLLABORATION OPPORTUNITY DETECTION
    collaboration_keywords = ["collab", "feature", "open verse", "need artist", "looking for"]
    if any(keyword in text for keyword in collaboration_keywords):
        score += 2
        factors["bonuses"].append("Collaboration opportunity")

    # LENGTH AND EFFORT INDICATORS
    if len(text) > 100:  # Longer posts often more thoughtful
        score += 0.5
        factors["bonuses"].append("Substantial content")
    elif len(text) < 20:  # Very short posts often spam
        score -= 0.5
        factors["penalties"].append("Very short content")

    # MUSIC/ARTIST RELEVANCE
    music_terms = ["track", "album", "single", "ep", "mixtape", "beat", "producer", "lyrics"]
    music_mentions = sum(1 for term in music_terms if term in text)
    if music_mentions >= 2:
        score += 1
        factors["bonuses"].append("Music-focused content")

    # Clamp score to 0-10 range
    final_score = max(0, min(10, score))

    return {
        "score": final_score,
        "threshold": 6.0,  # Minimum score for engagement
        "should_engage": final_score >= 6.0,
        "factors": factors,
        "text_preview": text[:100] + "..." if len(text) > 100 else text
    }


def load_engagement_history() -> Dict[str, Any]:
    """Load previous engagement history to avoid over-engaging with same accounts."""
    log = load_json(ENHANCED_ENGAGEMENT_LOG)
    if "engagement_history" not in log:
        log["engagement_history"] = {}
    return log


def should_engage_with_account(author_handle: str, history: Dict) -> bool:
    """Check if we should engage with this account based on recent history."""
    engagement_hist = history.get("engagement_history", {})

    if author_handle not in engagement_hist:
        return True

    last_engagement = engagement_hist[author_handle].get("last_engagement")
    if not last_engagement:
        return True

    # Check cooldown period
    last_time = datetime.fromisoformat(last_engagement)
    cooldown_ends = last_time + timedelta(hours=ENGAGEMENT_COOLDOWN_HOURS)

    return datetime.now() > cooldown_ends


def record_engagement(author_handle: str, engagement_type: str, quality_score: float, history: Dict):
    """Record engagement in history for future reference."""
    engagement_hist = history["engagement_history"]

    if author_handle not in engagement_hist:
        engagement_hist[author_handle] = {
            "total_engagements": 0,
            "last_engagement": None,
            "quality_scores": [],
            "engagement_types": []
        }

    account_data = engagement_hist[author_handle]
    account_data["total_engagements"] += 1
    account_data["last_engagement"] = datetime.now().isoformat()
    account_data["quality_scores"].append(quality_score)
    account_data["engagement_types"].append(engagement_type)

    # Keep only last 10 scores/types to prevent bloat
    account_data["quality_scores"] = account_data["quality_scores"][-10:]
    account_data["engagement_types"] = account_data["engagement_types"][-10:]


def enhanced_bluesky_engagement():
    """APU-81 Enhanced Bluesky engagement with intelligent filtering."""
    handle, app_password = get_bluesky_credentials()

    if not handle or not app_password:
        print("[INFO] Bluesky credentials not found in credentials.json")
        return {"likes": 0, "follows": 0, "filtered": 0, "errors": ["Missing credentials"]}

    try:
        from atproto import Client
    except ImportError:
        print("[INFO] atproto not installed. Run: pip install atproto")
        return {"likes": 0, "follows": 0, "filtered": 0, "errors": ["Missing atproto library"]}

    client = Client()
    try:
        client.login(handle, app_password)
        print(f"[OK] Logged into Bluesky as {handle}")
    except Exception as e:
        print(f"[FAIL] Bluesky login failed: {e}")
        return {"likes": 0, "follows": 0, "filtered": 0, "errors": [f"Login failed: {e}"]}

    # Load engagement history
    history = load_engagement_history()

    # Intelligent search term selection
    all_terms = []
    for category, terms in SEARCH_TERMS.items():
        all_terms.extend(terms)

    term = random.choice(all_terms)
    print(f"[OK] Searching Bluesky for: '{term}'")

    liked = 0
    followed = 0
    filtered_out = 0
    engagement_actions = []

    try:
        results = client.app.bsky.feed.search_posts({"q": term, "limit": 30})  # Increased to get more filtering opportunities
        posts = results.posts if hasattr(results, 'posts') else []

        # Shuffle for variety
        random.shuffle(posts)

        for post in posts:
            if liked >= MAX_LIKES_PER_RUN:
                break

            # Skip own posts
            if post.author.handle == handle:
                continue

            # Calculate content quality
            quality_analysis = calculate_content_quality_score(post)

            # Check engagement cooldown
            should_engage = should_engage_with_account(post.author.handle, history)

            if not quality_analysis["should_engage"]:
                filtered_out += 1
                print(f"  [FILTER] @{post.author.handle}: Score {quality_analysis['score']:.1f} < threshold")
                continue

            if not should_engage:
                filtered_out += 1
                print(f"  [COOLDOWN] @{post.author.handle}: Recent engagement, skipping")
                continue

            # Engage with high-quality content
            try:
                client.like(uri=post.uri, cid=post.cid)
                liked += 1

                # Record engagement
                record_engagement(post.author.handle, "like", quality_analysis["score"], history)

                engagement_actions.append({
                    "type": "like",
                    "author": post.author.handle,
                    "quality_score": quality_analysis["score"],
                    "factors": quality_analysis["factors"],
                    "text_preview": quality_analysis["text_preview"]
                })

                print(f"  [LIKE] @{post.author.handle} (Score: {quality_analysis['score']:.1f})")
                print(f"    Content: {quality_analysis['text_preview']}")

                # COLLABORATION OPPORTUNITY DETECTION
                if "collaboration opportunity" in [bonus.lower() for bonus in quality_analysis["factors"].get("bonuses", [])]:
                    # Save potential collaboration target
                    collab_targets = load_json(COLLABORATION_TARGETS)
                    today = today_str()
                    if today not in collab_targets:
                        collab_targets[today] = []

                    collab_targets[today].append({
                        "handle": post.author.handle,
                        "post_text": quality_analysis["text_preview"],
                        "quality_score": quality_analysis["score"],
                        "discovered_at": datetime.now().isoformat(),
                        "post_uri": post.uri
                    })
                    save_json(COLLABORATION_TARGETS, collab_targets)
                    print(f"    [COLLAB] Saved as potential collaboration target")

            except Exception as e:
                print(f"  [ERROR] Failed to like post from @{post.author.handle}: {e}")

    except Exception as e:
        print(f"[WARN] Search failed: {e}")
        return {"likes": liked, "follows": followed, "filtered": filtered_out, "errors": [f"Search failed: {e}"]}

    # Save updated engagement history
    save_json(ENHANCED_ENGAGEMENT_LOG, history)

    print(f"\n[OK] APU-81 Enhanced Bluesky: {liked} likes, {followed} follows, {filtered_out} filtered")
    print(f"[QUALITY] Average engagement score: {sum(a['quality_score'] for a in engagement_actions) / max(len(engagement_actions), 1):.1f}")

    return {
        "likes": liked,
        "follows": followed,
        "filtered": filtered_out,
        "engagement_actions": engagement_actions,
        "search_term": term
    }


def generate_engagement_report(results: Dict) -> str:
    """Generate detailed engagement report for APU-44 monitoring integration."""
    total_interactions = results["likes"] + results["follows"]
    filter_efficiency = results["filtered"] / max(results["filtered"] + total_interactions, 1)

    report = f"""
APU-81 Enhanced Engagement Report
================================
Search Term: {results.get('search_term', 'Unknown')}
Engagements: {results['likes']} likes, {results['follows']} follows
Filtered Out: {results['filtered']} (efficiency: {filter_efficiency:.1%})
Quality Threshold: 6.0/10.0

Top Engagement Reasons:
"""

    if results.get("engagement_actions"):
        # Analyze most common quality factors
        all_bonuses = []
        for action in results["engagement_actions"]:
            all_bonuses.extend(action["factors"].get("bonuses", []))

        from collections import Counter
        top_reasons = Counter(all_bonuses).most_common(3)

        for reason, count in top_reasons:
            report += f"- {reason}: {count} times\n"

    return report.strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    today = today_str()
    now = datetime.now().strftime("%H:%M")
    print(f"\n=== APU-81 Enhanced Engagement Bot — {today} {now} ===\n")

    # Enhanced Bluesky engagement
    print("--- Enhanced Bluesky Engagement ---")
    results = enhanced_bluesky_engagement()

    # Generate detailed report
    if args.verbose:
        report = generate_engagement_report(results)
        print(f"\n{report}")

    # Other platforms — enhanced reminders with specific actions
    print("\n--- Other Platforms (Manual Engagement Guidelines) ---")
    print("[INFO] Instagram: Target posts from Atlanta/Brooklyn hip-hop artists")
    print("[INFO] TikTok: Engage with #atlantarap #brooklynhiphop #boomtrap content")
    print("[INFO] X: Focus on music industry conversations and artist collaborations")
    print("[INFO] Threads: Reply to hip-hop discussions with thoughtful comments")

    # Enhanced logging
    if not args.test:
        log = load_json(ENHANCED_ENGAGEMENT_LOG)
        if today not in log:
            log[today] = []

        log[today].append({
            "time": datetime.now().isoformat(),
            "version": "apu81_enhanced_v1",
            "bluesky": results,
            "filter_efficiency": results["filtered"] / max(results["filtered"] + results["likes"] + results["follows"], 1),
            "quality_threshold": 6.0
        })
        save_json(ENHANCED_ENGAGEMENT_LOG, log)

    # Enhanced research log entry for APU-44 monitoring integration
    log_run(
        "APU81EngagementBot",
        "ok" if results["likes"] > 0 or results["follows"] > 0 else "info",
        f"Enhanced: {results['likes']} likes, {results['follows']} follows, "
        f"{results['filtered']} filtered, quality threshold: 6.0/10"
    )

    print(f"\n=== APU-81 Enhanced Engagement Complete ===\n")
    return results


if __name__ == "__main__":
    main()