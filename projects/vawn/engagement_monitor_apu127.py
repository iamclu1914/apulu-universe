"""
engagement_monitor_apu127.py — Active engagement monitoring with AI-powered auto-responses.
Real-time comment monitoring and intelligent response generation across all platforms.
Created by: Dex - Community Agent (APU-127)
"""

import json
import sys
import requests
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import anthropic

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import (
    load_json, save_json, ENGAGEMENT_LOG, RESEARCH_LOG, VAWN_DIR,
    log_run, today_str, get_anthropic_client, CREDS_FILE, VAWN_PROFILE
)

# Configuration
MONITOR_LOG = VAWN_DIR / "research" / "apu127_engagement_monitor_log.json"
COMMENTS_CACHE = VAWN_DIR / "research" / "apu127_comments_cache.json"
RESPONSES_LOG = VAWN_DIR / "research" / "apu127_responses_log.json"
BASE_URL = "https://apulustudio.onrender.com/api"

# Engagement thresholds and rules
ENGAGEMENT_CONFIG = {
    "response_rate_limit": {
        "max_responses_per_hour": 5,
        "max_responses_per_platform_per_hour": 2,
        "cooldown_between_responses_minutes": 15
    },
    "priority_scoring": {
        "verified_user_bonus": 50,
        "high_follower_threshold": 10000,
        "high_follower_bonus": 30,
        "negative_sentiment_penalty": -20,
        "positive_sentiment_bonus": 15,
        "question_bonus": 25,
        "mention_bonus": 40
    },
    "response_triggers": {
        "min_priority_score": 50,
        "always_respond_to_questions": True,
        "always_respond_to_mentions": True,
        "skip_automated_comments": True
    }
}

PLATFORMS = ["instagram", "tiktok", "x", "threads", "bluesky"]

# Vawn's response voice guidelines
RESPONSE_VOICE = {
    "tone": "conversational, authentic, humble confidence",
    "style": "short and direct, no corporate speak",
    "personality": "anti-hype, genuine gratitude, pattern recognition mindset",
    "avoid": ["excessive emojis", "generic responses", "promotional language", "hype words"],
    "signature_phrases": ["appreciate you", "that means everything", "real recognize real", "stay locked in"]
}

# Platform-specific response rules
PLATFORM_RESPONSE_RULES = {
    "instagram": {
        "max_length": 500,
        "allow_emojis": True,
        "max_emojis": 2,
        "include_cta": False
    },
    "tiktok": {
        "max_length": 150,
        "allow_emojis": True,
        "max_emojis": 1,
        "include_cta": False
    },
    "x": {
        "max_length": 280,
        "allow_emojis": True,
        "max_emojis": 1,
        "include_cta": False
    },
    "threads": {
        "max_length": 500,
        "allow_emojis": True,
        "max_emojis": 1,
        "include_cta": False
    },
    "bluesky": {
        "max_length": 300,
        "allow_emojis": True,
        "max_emojis": 1,
        "include_cta": False
    }
}


def get_comment_hash(comment: Dict[str, Any]) -> str:
    """Generate unique hash for comment to prevent duplicate responses."""
    comment_data = f"{comment.get('platform', '')}{comment.get('post_id', '')}{comment.get('id', '')}{comment.get('text', '')}{comment.get('author', '')}"
    return hashlib.md5(comment_data.encode()).hexdigest()


def load_comments_cache() -> Dict[str, Any]:
    """Load comment tracking cache."""
    return load_json(COMMENTS_CACHE)


def save_comments_cache(cache: Dict[str, Any]) -> None:
    """Save comment tracking cache."""
    save_json(COMMENTS_CACHE, cache)


def load_responses_log() -> Dict[str, Any]:
    """Load response activity log."""
    return load_json(RESPONSES_LOG)


def save_responses_log(log: Dict[str, Any]) -> None:
    """Save response activity log."""
    save_json(RESPONSES_LOG, log)


def fetch_platform_comments(platform: str, access_token: str) -> List[Dict[str, Any]]:
    """Fetch recent comments from a specific platform."""
    headers = {"Authorization": f"Bearer {access_token}"}
    comments = []

    try:
        # Fetch recent posts first
        posts_url = f"{BASE_URL}/posts?platform={platform}&limit=10"
        posts_response = requests.get(posts_url, headers=headers, timeout=30)

        if posts_response.status_code != 200:
            print(f"Failed to fetch posts from {platform}: {posts_response.status_code}")
            return comments

        posts = posts_response.json().get("posts", [])

        # Fetch comments for each post
        for post in posts:
            post_id = post.get("id")
            if not post_id:
                continue

            comments_url = f"{BASE_URL}/posts/{post_id}/comments"
            comments_response = requests.get(comments_url, headers=headers, timeout=30)

            if comments_response.status_code == 200:
                post_comments = comments_response.json().get("comments", [])
                for comment in post_comments:
                    comment["platform"] = platform
                    comment["post_id"] = post_id
                    comments.append(comment)
            elif comments_response.status_code != 404:  # 404 means no comments yet
                print(f"Failed to fetch comments for post {post_id} on {platform}")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching comments from {platform}: {str(e)}")

    return comments


def calculate_comment_priority(comment: Dict[str, Any]) -> int:
    """Calculate priority score for a comment to determine response likelihood."""
    score = 0
    config = ENGAGEMENT_CONFIG["priority_scoring"]

    # Author verification and follower count
    if comment.get("author", {}).get("verified", False):
        score += config["verified_user_bonus"]

    follower_count = comment.get("author", {}).get("followers", 0)
    if follower_count > config["high_follower_threshold"]:
        score += config["high_follower_bonus"]

    # Content analysis
    text = comment.get("text", "").lower()

    # Question detection
    if "?" in text or any(q in text for q in ["how", "what", "when", "where", "why", "who"]):
        score += config["question_bonus"]

    # Mention detection
    if any(mention in text for mention in ["@vawn", "vawn", "@"]):
        score += config["mention_bonus"]

    # Basic sentiment analysis
    positive_words = ["love", "amazing", "fire", "dope", "incredible", "talent", "respect", "appreciate"]
    negative_words = ["hate", "trash", "wack", "terrible", "awful", "disappointing"]

    positive_count = sum(1 for word in positive_words if word in text)
    negative_count = sum(1 for word in negative_words if word in text)

    if positive_count > negative_count:
        score += config["positive_sentiment_bonus"] * (positive_count - negative_count)
    elif negative_count > positive_count:
        score += config["negative_sentiment_penalty"] * (negative_count - positive_count)

    # Recency bonus (comments within last hour get priority)
    comment_time = datetime.fromisoformat(comment.get("created_at", ""))
    hours_old = (datetime.now() - comment_time).total_seconds() / 3600
    if hours_old < 1:
        score += 20
    elif hours_old < 6:
        score += 10

    return max(0, score)


def check_rate_limits() -> Tuple[bool, str]:
    """Check if we've hit response rate limits."""
    responses_log = load_responses_log()
    now = datetime.now()
    one_hour_ago = now - timedelta(hours=1)

    config = ENGAGEMENT_CONFIG["response_rate_limit"]

    # Count responses in last hour
    recent_responses = []
    for date_str, responses in responses_log.items():
        for response in responses:
            response_time = datetime.fromisoformat(response.get("timestamp", ""))
            if response_time > one_hour_ago:
                recent_responses.append(response)

    total_recent = len(recent_responses)

    # Check global limit
    if total_recent >= config["max_responses_per_hour"]:
        return False, f"Hit global rate limit: {total_recent}/{config['max_responses_per_hour']} responses in last hour"

    # Check per-platform limits
    platform_counts = {}
    for response in recent_responses:
        platform = response.get("platform", "unknown")
        platform_counts[platform] = platform_counts.get(platform, 0) + 1

    for platform, count in platform_counts.items():
        if count >= config["max_responses_per_platform_per_hour"]:
            return False, f"Hit {platform} rate limit: {count}/{config['max_responses_per_platform_per_hour']} responses"

    # Check cooldown period
    if recent_responses:
        last_response_time = max(datetime.fromisoformat(r.get("timestamp", "")) for r in recent_responses)
        cooldown_minutes = config["cooldown_between_responses_minutes"]
        if (now - last_response_time).total_seconds() < cooldown_minutes * 60:
            return False, f"In cooldown period: {cooldown_minutes} minutes between responses"

    return True, "Rate limits OK"


def generate_ai_response(comment: Dict[str, Any]) -> Optional[str]:
    """Generate AI-powered response using Anthropic Claude."""
    try:
        client = get_anthropic_client()

        comment_text = comment.get("text", "")
        author = comment.get("author", {}).get("username", "someone")
        platform = comment.get("platform", "social media")

        # Build context-aware prompt
        prompt = f"""You are Vawn, a Brooklyn-raised, Atlanta-based hip-hop artist responding to a comment on {platform}.

VAWN'S PROFILE:
{VAWN_PROFILE}

RESPONSE VOICE:
- Tone: {RESPONSE_VOICE['tone']}
- Style: {RESPONSE_VOICE['style']}
- Personality: {RESPONSE_VOICE['personality']}
- Avoid: {', '.join(RESPONSE_VOICE['avoid'])}
- Use phrases like: {', '.join(RESPONSE_VOICE['signature_phrases'])}

PLATFORM RULES:
- Max length: {PLATFORM_RESPONSE_RULES[platform]['max_length']} characters
- Max emojis: {PLATFORM_RESPONSE_RULES[platform]['max_emojis']}

COMMENT TO RESPOND TO:
From @{author}: "{comment_text}"

Generate a response that:
1. Feels personal and authentic to Vawn's voice
2. Shows genuine appreciation for engagement
3. Stays under character limit
4. Avoids generic social media speak
5. Matches the energy of the original comment

Response:"""

        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=150,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )

        generated_response = response.content[0].text.strip()

        # Validate response length
        platform_rules = PLATFORM_RESPONSE_RULES[platform]
        if len(generated_response) > platform_rules["max_length"]:
            generated_response = generated_response[:platform_rules["max_length"]-3] + "..."

        return generated_response

    except Exception as e:
        print(f"Error generating AI response: {str(e)}")
        return None


def should_respond_to_comment(comment: Dict[str, Any], comments_cache: Dict[str, Any]) -> Tuple[bool, str]:
    """Determine if we should respond to this comment."""
    comment_hash = get_comment_hash(comment)

    # Check if already responded
    if comment_hash in comments_cache.get("responded", []):
        return False, "Already responded to this comment"

    # Check rate limits
    can_respond, limit_reason = check_rate_limits()
    if not can_respond:
        return False, limit_reason

    # Calculate priority score
    priority = calculate_comment_priority(comment)

    config = ENGAGEMENT_CONFIG["response_triggers"]
    min_score = config["min_priority_score"]

    # Always respond to questions and mentions regardless of score
    text = comment.get("text", "").lower()

    if config["always_respond_to_questions"] and "?" in text:
        return True, f"Question detected (priority: {priority})"

    if config["always_respond_to_mentions"] and any(m in text for m in ["@vawn", "vawn"]):
        return True, f"Mention detected (priority: {priority})"

    # Skip automated/bot comments
    if config["skip_automated_comments"]:
        bot_indicators = ["follow for follow", "check out my", "link in bio", "dm me", "www.", "http"]
        if any(indicator in text for indicator in bot_indicators):
            return False, f"Automated comment detected (priority: {priority})"

    # Check priority threshold
    if priority >= min_score:
        return True, f"Priority score sufficient: {priority}/{min_score}"

    return False, f"Priority too low: {priority}/{min_score}"


def post_response_to_platform(comment: Dict[str, Any], response_text: str, access_token: str) -> bool:
    """Post response to the platform."""
    platform = comment.get("platform")
    post_id = comment.get("post_id")
    comment_id = comment.get("id")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "text": response_text,
        "reply_to": comment_id
    }

    try:
        response_url = f"{BASE_URL}/posts/{post_id}/comments"
        response = requests.post(response_url, headers=headers, json=payload, timeout=30)

        if response.status_code in [200, 201]:
            return True
        else:
            print(f"Failed to post response to {platform}: {response.status_code} - {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"Error posting response to {platform}: {str(e)}")
        return False


def log_response_activity(comment: Dict[str, Any], response_text: str, success: bool, reason: str = "") -> None:
    """Log response activity for monitoring."""
    responses_log = load_responses_log()
    today = today_str()

    if today not in responses_log:
        responses_log[today] = []

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "platform": comment.get("platform"),
        "post_id": comment.get("post_id"),
        "comment_id": comment.get("id"),
        "comment_author": comment.get("author", {}).get("username"),
        "comment_text": comment.get("text", "")[:100],  # First 100 chars
        "response_text": response_text,
        "success": success,
        "reason": reason,
        "priority_score": calculate_comment_priority(comment)
    }

    responses_log[today].append(log_entry)
    save_responses_log(responses_log)


def monitor_engagement() -> Dict[str, Any]:
    """Main engagement monitoring function."""
    results = {
        "timestamp": datetime.now().isoformat(),
        "platforms_checked": 0,
        "comments_found": 0,
        "responses_generated": 0,
        "responses_posted": 0,
        "errors": [],
        "activity_summary": []
    }

    try:
        # Load credentials
        creds = load_json(CREDS_FILE)
        access_token = creds.get("access_token", "")

        if not access_token:
            results["errors"].append("No access token found in credentials")
            return results

        # Load comment cache
        comments_cache = load_comments_cache()
        if "responded" not in comments_cache:
            comments_cache["responded"] = []
        if "processed" not in comments_cache:
            comments_cache["processed"] = []

        total_comments = 0

        # Check each platform
        for platform in PLATFORMS:
            try:
                results["platforms_checked"] += 1

                # Fetch comments
                comments = fetch_platform_comments(platform, access_token)
                total_comments += len(comments)

                print(f"Found {len(comments)} comments on {platform}")

                # Process each comment
                for comment in comments:
                    comment_hash = get_comment_hash(comment)

                    # Skip if already processed
                    if comment_hash in comments_cache["processed"]:
                        continue

                    # Mark as processed
                    comments_cache["processed"].append(comment_hash)

                    # Decide whether to respond
                    should_respond, reason = should_respond_to_comment(comment, comments_cache)

                    activity = {
                        "platform": platform,
                        "comment_author": comment.get("author", {}).get("username"),
                        "comment_text": comment.get("text", "")[:50],
                        "should_respond": should_respond,
                        "reason": reason,
                        "response_posted": False
                    }

                    if should_respond:
                        # Generate response
                        response_text = generate_ai_response(comment)

                        if response_text:
                            results["responses_generated"] += 1

                            # Post response
                            post_success = post_response_to_platform(comment, response_text, access_token)

                            if post_success:
                                results["responses_posted"] += 1
                                comments_cache["responded"].append(comment_hash)
                                activity["response_posted"] = True
                                activity["response_text"] = response_text[:50]

                            # Log activity
                            log_response_activity(comment, response_text, post_success, reason)
                        else:
                            results["errors"].append(f"Failed to generate response for comment on {platform}")

                    results["activity_summary"].append(activity)

            except Exception as e:
                error_msg = f"Error processing {platform}: {str(e)}"
                results["errors"].append(error_msg)
                print(error_msg)

        results["comments_found"] = total_comments

        # Clean up old cache entries (keep last 1000)
        for cache_type in ["processed", "responded"]:
            if len(comments_cache[cache_type]) > 1000:
                comments_cache[cache_type] = comments_cache[cache_type][-1000:]

        # Save updated cache
        save_comments_cache(comments_cache)

    except Exception as e:
        error_msg = f"Critical error in engagement monitor: {str(e)}"
        results["errors"].append(error_msg)
        print(error_msg)

    return results


def main():
    """Main execution function."""
    print(f"Starting APU-127 engagement monitor at {datetime.now()}")

    # Run engagement monitoring
    results = monitor_engagement()

    # Create summary
    summary_parts = []
    summary_parts.append(f"Checked {results['platforms_checked']}/{len(PLATFORMS)} platforms")
    summary_parts.append(f"Found {results['comments_found']} comments")
    summary_parts.append(f"Generated {results['responses_generated']} responses")
    summary_parts.append(f"Posted {results['responses_posted']} responses")

    if results["errors"]:
        summary_parts.append(f"Encountered {len(results['errors'])} errors")

    summary = ", ".join(summary_parts)

    # Log run to research log
    status = "ok" if not results["errors"] else "error"
    log_run("engagement_monitor_apu127", status, summary)

    # Save detailed results
    monitor_log = load_json(MONITOR_LOG)
    today = today_str()
    if today not in monitor_log:
        monitor_log[today] = []
    monitor_log[today].append(results)
    save_json(MONITOR_LOG, monitor_log)

    print(f"Engagement monitoring completed: {summary}")

    if results["errors"]:
        print("Errors encountered:")
        for error in results["errors"]:
            print(f"  - {error}")

    return results


if __name__ == "__main__":
    main()