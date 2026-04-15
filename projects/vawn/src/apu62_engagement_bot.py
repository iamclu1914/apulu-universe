"""
apu62_engagement_bot.py — APU-62 Intelligent Multi-Platform Engagement Bot
Enhanced by Dex - Community Agent for improved department integration and cross-platform coordination.

Key Enhancements:
- Department-context driven targeting (Legal, A&R, Creative Revenue, Operations)
- Intelligent content quality scoring with cultural context
- Cross-platform engagement opportunity detection
- Adaptive timing optimization based on department priorities
- Enhanced reliability with circuit breaker pattern
- Smart notification system for manual platform engagement

Schedule: Runs after each posting slot (9:30am, 1pm, 8:30pm) with department-aware optimization.
"""

import argparse
import json
import random
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import VAWN_DIR, load_json, save_json, log_run, today_str

# Configuration files
APU62_LOG = VAWN_DIR / "research" / "apu62_engagement_bot_log.json"
APU62_ANALYTICS_LOG = VAWN_DIR / "research" / "apu62_analytics_log.json"
DEPARTMENT_CONTEXT_FILE = VAWN_DIR / "research" / "unified_reports" / f"unified_engagement_report_{datetime.now().strftime('%Y%m%d')}_latest.json"

# Department-aware search terms
DEPARTMENT_SEARCH_TERMS = {
    "legal": ["copyright", "licensing", "legal music", "rights management", "music law"],
    "a_and_r": ["new talent", "demo submission", "artist discovery", "unsigned artists", "emerging artists"],
    "creative_revenue": ["music marketing", "streaming strategy", "fan engagement", "conversion", "campaign"],
    "operations": ["studio life", "music production", "workflow", "industry insights", "behind the scenes"],
    "general": ["hip hop", "rap", "new music", "indie rap", "boom bap", "lyrical rap", "atlanta rap", "underground hip hop", "trap soul", "new artist", "bars", "freestyle", "producer", "beat maker"]
}

# Platform-specific configuration
PLATFORM_CONFIG = {
    "bluesky": {
        "enabled": True,
        "max_likes": 12,
        "max_follows": 2,
        "api_timeout": 10,
        "retry_limit": 3
    },
    "instagram": {
        "enabled": False,  # Manual engagement
        "detection_keywords": ["#hiphop", "#rap", "#newmusic", "#producer"],
        "engagement_suggestions": ["like_story", "comment_post", "follow_artist"]
    },
    "tiktok": {
        "enabled": False,  # Manual engagement
        "detection_keywords": ["#fyp", "#rap", "#hiphop", "#newartist"],
        "engagement_suggestions": ["like_video", "follow_creator", "share_content"]
    },
    "x": {
        "enabled": False,  # Manual engagement
        "detection_keywords": ["#hiphop", "#rap", "#newmusic"],
        "engagement_suggestions": ["retweet", "like", "reply"]
    },
    "threads": {
        "enabled": False,  # Manual engagement
        "detection_keywords": ["hip-hop", "rap", "music"],
        "engagement_suggestions": ["like", "reply", "follow"]
    }
}

# Circuit breaker for API reliability
class CircuitBreaker:
    def __init__(self, failure_threshold=3, timeout_duration=300):
        self.failure_threshold = failure_threshold
        self.timeout_duration = timeout_duration
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open

    def call(self, func, *args, **kwargs):
        if self.state == "open":
            if datetime.now().timestamp() - self.last_failure_time > self.timeout_duration:
                self.state = "half_open"
            else:
                raise Exception("Circuit breaker is open")

        try:
            result = func(*args, **kwargs)
            if self.state == "half_open":
                self.state = "closed"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now().timestamp()

            if self.failure_count >= self.failure_threshold:
                self.state = "open"

            raise e


def load_department_context():
    """Load current department health and priority data."""
    try:
        # Try to load the latest unified report
        pattern = VAWN_DIR / "research" / "unified_reports" / "unified_engagement_report_*_*.json"
        import glob
        reports = glob.glob(str(pattern))

        if reports:
            latest_report = max(reports, key=lambda x: Path(x).stat().st_mtime)
            context_data = load_json(Path(latest_report))

            return {
                "department_health": context_data.get("unified_metrics", {}).get("department_health", {}),
                "organizational": context_data.get("unified_metrics", {}).get("organizational", {}),
                "recommendations": context_data.get("recommendations", []),
                "timestamp": context_data.get("timestamp", datetime.now().isoformat())
            }
    except Exception as e:
        print(f"[WARN] Could not load department context: {e}")

    return {
        "department_health": {"legal": 0.5, "a_and_r": 0.5, "creative_revenue": 0.5, "operations": 0.5},
        "organizational": {"overall_health": 0.5, "urgent_issues": 0},
        "recommendations": [],
        "timestamp": datetime.now().isoformat()
    }


def calculate_department_priority(department_context):
    """Calculate which department needs most engagement focus."""
    health_scores = department_context.get("department_health", {})

    # Lower health score = higher priority (more engagement needed)
    priority_scores = {}
    for dept, health in health_scores.items():
        priority_scores[dept] = 1.0 - health  # Inverse priority

    # Sort by priority (highest first)
    sorted_priorities = sorted(priority_scores.items(), key=lambda x: x[1], reverse=True)

    return {
        "primary_focus": sorted_priorities[0][0] if sorted_priorities else "general",
        "priority_scores": priority_scores,
        "needs_attention": [dept for dept, score in sorted_priorities if score > 0.3]
    }


def intelligent_search_term_selection(department_priorities):
    """Select search terms based on department priorities and context."""
    primary_focus = department_priorities.get("primary_focus", "general")

    # Weight selection based on department needs
    if primary_focus in DEPARTMENT_SEARCH_TERMS:
        # 70% chance to use department-specific terms, 30% general
        if random.random() < 0.7:
            selected_terms = DEPARTMENT_SEARCH_TERMS[primary_focus]
        else:
            selected_terms = DEPARTMENT_SEARCH_TERMS["general"]
    else:
        selected_terms = DEPARTMENT_SEARCH_TERMS["general"]

    return random.choice(selected_terms)


def content_quality_analyzer(post_text, department_focus):
    """Analyze content quality with department context awareness."""
    quality_score = 0.5  # Base score

    # Department relevance scoring
    dept_keywords = DEPARTMENT_SEARCH_TERMS.get(department_focus, [])
    for keyword in dept_keywords:
        if keyword.lower() in post_text.lower():
            quality_score += 0.2

    # Quality indicators
    positive_indicators = [
        "new track", "debut", "just dropped", "fresh", "original",
        "independent", "underground", "authentic", "real hip hop"
    ]

    negative_indicators = [
        "follow me", "check my", "dm me", "promo", "buy my",
        "stream my", "f4f", "l4l", "collab?", "clout"
    ]

    for indicator in positive_indicators:
        if indicator in post_text.lower():
            quality_score += 0.15

    for indicator in negative_indicators:
        if indicator in post_text.lower():
            quality_score -= 0.25

    # Content depth scoring
    if len(post_text.strip()) > 50:
        quality_score += 0.1

    hashtag_count = post_text.count('#')
    if hashtag_count <= 3:
        quality_score += 0.1
    elif hashtag_count > 6:
        quality_score -= 0.2

    return max(0.0, min(1.0, quality_score))


def enhanced_bluesky_engagement(department_context, circuit_breaker):
    """Enhanced Bluesky engagement with department-context intelligence."""
    metrics = {
        "likes": 0,
        "follows": 0,
        "errors": 0,
        "department_focus": None,
        "search_term": None,
        "posts_processed": 0,
        "quality_filtered": 0,
        "api_health": {},
        "performance": {},
        "department_context": department_context,
        "start_time": datetime.now().isoformat()
    }

    # Calculate department priorities
    dept_priorities = calculate_department_priority(department_context)
    metrics["department_focus"] = dept_priorities["primary_focus"]

    print(f"[INFO] Department Focus: {metrics['department_focus']}")
    print(f"[INFO] Departments needing attention: {dept_priorities['needs_attention']}")

    # Get credentials
    try:
        creds = load_json(VAWN_DIR / "credentials.json")
        handle = creds.get("bluesky_handle")
        app_password = creds.get("bluesky_app_password")

        if not handle or not app_password:
            print("[FAIL] Missing Bluesky credentials in credentials.json")
            metrics["errors"] += 1
            return metrics
    except Exception as e:
        print(f"[FAIL] Credential error: {e}")
        metrics["errors"] += 1
        return metrics

    # Initialize Bluesky client
    try:
        from atproto import Client
    except ImportError:
        print("[FAIL] atproto not installed. Run: pip install atproto")
        metrics["errors"] += 1
        return metrics

    client = Client()

    # Authenticate with circuit breaker protection
    try:
        circuit_breaker.call(client.login, handle, app_password)
        print(f"[OK] Logged into Bluesky as {handle}")
    except Exception as e:
        print(f"[FAIL] Bluesky login failed: {e}")
        metrics["errors"] += 1
        return metrics

    # Intelligent search term selection
    search_term = intelligent_search_term_selection(dept_priorities)
    metrics["search_term"] = search_term
    print(f"[OK] Intelligent search term selected: '{search_term}'")

    # Enhanced search with department context
    try:
        search_start = datetime.now()
        results = circuit_breaker.call(
            client.app.bsky.feed.search_posts,
            {"q": search_term, "limit": 30}
        )
        search_time = (datetime.now() - search_start).total_seconds() * 1000
        metrics["performance"]["search_time_ms"] = int(search_time)

        posts = results.posts if hasattr(results, 'posts') else []
        metrics["posts_processed"] = len(posts)

        # Intelligent content filtering with department context
        filtered_posts = []
        for post in posts:
            if post.author.handle == handle:
                continue

            post_text = getattr(post.record, 'text', '')
            quality_score = content_quality_analyzer(post_text, metrics["department_focus"])

            # Higher quality threshold for department-focused engagement
            quality_threshold = 0.6 if metrics["department_focus"] != "general" else 0.4

            if quality_score >= quality_threshold:
                filtered_posts.append((post, quality_score))

        # Sort by quality score (highest first)
        filtered_posts.sort(key=lambda x: x[1], reverse=True)
        metrics["quality_filtered"] = len(posts) - len(filtered_posts)

        print(f"[OK] Found {len(posts)} posts, {len(filtered_posts)} passed quality filter")

    except Exception as e:
        print(f"[FAIL] Enhanced search failed: {e}")
        metrics["errors"] += 1
        return metrics

    # Smart engagement execution
    engagement_start = datetime.now()
    config = PLATFORM_CONFIG["bluesky"]

    for post, quality_score in filtered_posts[:config["max_likes"]]:
        try:
            circuit_breaker.call(client.like, uri=post.uri, cid=post.cid)
            metrics["likes"] += 1

            # Safe text display for Windows console
            safe_text = post.record.text[:50].encode('ascii', 'replace').decode('ascii')
            print(f"  [LIKE] @{post.author.handle} (Q:{quality_score:.2f}): {safe_text}...")

        except Exception as e:
            print(f"  [FAIL] Like failed: {e}")
            metrics["errors"] += 1

    engagement_time = (datetime.now() - engagement_start).total_seconds() * 1000
    metrics["performance"]["engagement_time_ms"] = int(engagement_time)

    total_time = (datetime.now() - datetime.fromisoformat(metrics["start_time"])).total_seconds() * 1000
    metrics["performance"]["total_time_ms"] = int(total_time)

    print(f"\n[OK] Enhanced engagement complete: {metrics['likes']} quality likes")

    return metrics


def cross_platform_opportunity_detector(department_context):
    """Detect engagement opportunities on manual platforms."""
    dept_priorities = calculate_department_priority(department_context)
    primary_focus = dept_priorities["primary_focus"]

    opportunities = []

    for platform, config in PLATFORM_CONFIG.items():
        if platform == "bluesky" or config["enabled"]:
            continue

        # Generate smart engagement suggestions
        relevant_keywords = DEPARTMENT_SEARCH_TERMS.get(primary_focus, DEPARTMENT_SEARCH_TERMS["general"])

        opportunity = {
            "platform": platform,
            "priority": "high" if primary_focus != "general" else "medium",
            "department_focus": primary_focus,
            "search_suggestions": relevant_keywords[:3],
            "engagement_actions": config["engagement_suggestions"],
            "detection_keywords": config["detection_keywords"]
        }

        opportunities.append(opportunity)

    return opportunities


def main():
    parser = argparse.ArgumentParser(description="APU-62 Intelligent Multi-Platform Engagement Bot")
    parser.add_argument("--test", action="store_true", help="Test mode - don't save logs")
    parser.add_argument("--department", choices=list(DEPARTMENT_SEARCH_TERMS.keys()), help="Force department focus")
    parser.add_argument("--analytics-only", action="store_true", help="Generate analytics and opportunities only")
    args = parser.parse_args()

    today = today_str()
    now = datetime.now().strftime("%H:%M")
    print(f"\n=== APU-62 Intelligent Engagement Bot — {today} {now} ===\n")

    # Load department context
    print("[INFO] Loading department context and priorities...")
    department_context = load_department_context()

    if args.department:
        # Override with manual department focus
        department_context["department_health"][args.department] = 0.3  # Force low health = high priority

    # Initialize circuit breaker for reliability
    circuit_breaker = CircuitBreaker(failure_threshold=3, timeout_duration=300)

    if args.analytics_only:
        print("--- Analytics & Opportunity Detection Mode ---")
        opportunities = cross_platform_opportunity_detector(department_context)

        print(f"Department Health Status:")
        for dept, health in department_context["department_health"].items():
            status = "[GOOD]" if health > 0.7 else "[WARN]" if health > 0.4 else "[CRITICAL]"
            print(f"  {status} {dept.title()}: {health:.1f}")

        print(f"\nCross-Platform Opportunities:")
        for opp in opportunities:
            print(f"  [PLATFORM] {opp['platform'].title()} ({opp['priority']} priority)")
            print(f"     Focus: {opp['department_focus']}")
            print(f"     Search: {', '.join(opp['search_suggestions'])}")
            print(f"     Actions: {', '.join(opp['engagement_actions'])}")
        return

    # Enhanced Bluesky engagement
    print("--- Enhanced Bluesky Engagement ---")
    bluesky_metrics = enhanced_bluesky_engagement(department_context, circuit_breaker)

    # Cross-platform opportunity detection
    print("\n--- Cross-Platform Opportunities ---")
    opportunities = cross_platform_opportunity_detector(department_context)

    print("Smart engagement opportunities detected:")
    for opp in opportunities:
        print(f"\n[PLATFORM] {opp['platform'].title()} ({opp['priority']} priority)")
        print(f"   [FOCUS] {opp['department_focus']} department")
        print(f"   [SEARCH] Search for: {', '.join(opp['search_suggestions'])}")
        print(f"   [ACTIONS] {', '.join(opp['engagement_actions'])}")

    # Enhanced logging
    if not args.test:
        # Main log
        log = load_json(APU62_LOG)
        if today not in log:
            log[today] = []

        log_entry = {
            "time": datetime.now().isoformat(),
            "version": "apu62_intelligent",
            "bluesky_metrics": bluesky_metrics,
            "department_context": department_context,
            "cross_platform_opportunities": opportunities,
            "success": bluesky_metrics["errors"] == 0,
            "circuit_breaker_state": circuit_breaker.state
        }

        log[today].append(log_entry)
        save_json(APU62_LOG, log)

        # Analytics log
        analytics = load_json(APU62_ANALYTICS_LOG)
        if today not in analytics:
            analytics[today] = []

        analytics_entry = {
            "timestamp": datetime.now().isoformat(),
            "department_priorities": calculate_department_priority(department_context),
            "engagement_effectiveness": 1.0 - (bluesky_metrics["errors"] / max(1, bluesky_metrics["likes"] + bluesky_metrics["errors"])),
            "platform_coverage": len([opp for opp in opportunities if opp["priority"] == "high"]),
            "quality_ratio": 1.0 - (bluesky_metrics.get("quality_filtered", 0) / max(1, bluesky_metrics.get("posts_processed", 1)))
        }

        analytics[today].append(analytics_entry)
        save_json(APU62_ANALYTICS_LOG, analytics)

    # System logging
    status = "ok" if bluesky_metrics["errors"] == 0 else "warning"
    summary = f"APU-62: {bluesky_metrics['likes']} quality likes, {len(opportunities)} platform opportunities"
    if bluesky_metrics["errors"] > 0:
        summary += f", {bluesky_metrics['errors']} errors"

    log_run("APU62_EngagementBot", status, summary)

    print(f"\n=== APU-62 Enhanced Engagement Complete ===")
    print(f"[FOCUS] Department Focus: {bluesky_metrics['department_focus']}")
    print(f"[BLUESKY] Bluesky: {bluesky_metrics['likes']} quality likes")
    print(f"[PLATFORMS] Opportunities: {len(opportunities)} platforms identified")
    print(f"[PERFORMANCE] Performance: {bluesky_metrics.get('performance', {}).get('total_time_ms', 0)}ms")
    print(f"[CIRCUIT] Circuit Breaker: {circuit_breaker.state}")
    print()


if __name__ == "__main__":
    main()