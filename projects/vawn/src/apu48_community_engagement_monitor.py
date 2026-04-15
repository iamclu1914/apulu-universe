"""
apu48_community_engagement_monitor.py — APU-48 Community-Centric Engagement Monitor
Enhanced monitoring system focused on community building and proactive engagement discovery.

Created by: Dex - Community Agent (APU-48)
Enhancements over APU-44:
- Proactive community opportunity detection
- Social listening and trend analysis
- Community health scoring beyond basic metrics
- Enhanced community building recommendations
- Real-time community vitality assessment
"""

import json
import sys
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import re
from collections import defaultdict

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import (
    load_json, save_json, ENGAGEMENT_LOG, RESEARCH_LOG, METRICS_LOG,
    VAWN_DIR, log_run, today_str, get_anthropic_client
)

# Configuration
MONITOR_LOG = VAWN_DIR / "research" / "apu48_community_engagement_monitor_log.json"
COMMUNITY_INSIGHTS_LOG = VAWN_DIR / "research" / "community_insights_log.json"

# Community-focused thresholds
COMMUNITY_THRESHOLDS = {
    "healthy_engagement_rate": 0.08,  # 8% minimum for healthy community
    "conversation_starter_threshold": 5,  # Comments that generate responses
    "community_health_score_min": 0.7,  # Minimum community health score
    "trend_detection_mentions": 3,  # Mentions needed to identify trends
    "engagement_quality_score_min": 0.6,  # Quality engagement threshold
}

PLATFORMS = ["instagram", "tiktok", "x", "threads", "bluesky"]

# Community engagement patterns for detection
ENGAGEMENT_PATTERNS = {
    "conversation_starters": [
        r"\?",  # Questions
        r"what do you think",
        r"thoughts on",
        r"agree with",
        r"disagree with",
        r"opinion",
    ],
    "community_builders": [
        r"everyone",
        r"community",
        r"together",
        r"support",
        r"love this",
        r"amazing work",
    ],
    "trend_indicators": [
        r"viral",
        r"trending",
        r"everyone's talking about",
        r"hot topic",
        r"blowing up",
    ]
}


def analyze_community_health() -> Dict[str, Any]:
    """Analyze overall community health and vitality."""
    try:
        metrics_log = load_json(METRICS_LOG)
        engagement_log = load_json(ENGAGEMENT_LOG)

        # Get recent data (last 7 days)
        recent_data = get_recent_metrics_data(metrics_log, days=7)
        recent_engagement = get_recent_engagement_data(engagement_log, days=7)

        # Calculate community health metrics
        health_metrics = {
            "engagement_quality": calculate_engagement_quality(recent_data),
            "conversation_health": analyze_conversation_patterns(recent_engagement),
            "community_growth": calculate_community_growth(recent_data),
            "platform_diversity": calculate_platform_diversity(recent_data),
            "response_quality": analyze_response_quality(recent_engagement),
        }

        # Calculate overall community health score
        health_score = sum(health_metrics.values()) / len(health_metrics)

        # Determine community status
        if health_score >= COMMUNITY_THRESHOLDS["community_health_score_min"]:
            status = "healthy"
        elif health_score >= 0.5:
            status = "moderate"
        else:
            status = "needs_attention"

        return {
            "overall_score": health_score,
            "status": status,
            "metrics": health_metrics,
            "timestamp": datetime.now().isoformat(),
            "recommendations": generate_community_recommendations(health_metrics)
        }

    except Exception as e:
        return {
            "overall_score": 0.0,
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def get_recent_metrics_data(metrics_log: Dict, days: int = 7) -> List[Dict]:
    """Extract recent metrics data for analysis."""
    cutoff = datetime.now() - timedelta(days=days)
    recent_data = []

    for image, dates in metrics_log.items():
        for date_str, platforms in dates.items():
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                if date_obj >= cutoff:
                    for platform, data in platforms.items():
                        if isinstance(data, dict):
                            recent_data.append({
                                "image": image,
                                "date": date_str,
                                "platform": platform,
                                "data": data
                            })
            except (ValueError, TypeError):
                continue

    return recent_data


def get_recent_engagement_data(engagement_log: Dict, days: int = 7) -> List[Dict]:
    """Extract recent engagement data for analysis."""
    cutoff = datetime.now() - timedelta(days=days)
    recent_engagement = []

    for entry in engagement_log.get("history", []):
        try:
            entry_date = datetime.fromisoformat(entry["date"])
            if entry_date >= cutoff:
                recent_engagement.append(entry)
        except (ValueError, KeyError):
            continue

    return recent_engagement


def calculate_engagement_quality(recent_data: List[Dict]) -> float:
    """Calculate quality of engagement beyond raw numbers."""
    if not recent_data:
        return 0.0

    total_posts = len(recent_data)
    quality_indicators = 0

    for post in recent_data:
        data = post["data"]
        likes = data.get("likes", 0)
        comments = data.get("comments", 0)
        saves = data.get("saves", 0)

        # Quality scoring: saves and comments weighted higher than likes
        quality_score = (comments * 3 + saves * 2 + likes * 1) / max(likes + comments + saves, 1)

        # Posts with good comment-to-like ratio indicate engagement quality
        if likes > 0 and comments / likes > 0.1:  # 10% comment rate is excellent
            quality_indicators += 1

        # Posts with saves indicate valuable content
        if saves > 0:
            quality_indicators += 0.5

    return min(quality_indicators / total_posts, 1.0)


def analyze_conversation_patterns(recent_engagement: List[Dict]) -> float:
    """Analyze the quality of conversations and community interaction."""
    if not recent_engagement:
        return 0.0

    conversation_quality = 0
    total_interactions = len(recent_engagement)

    for entry in recent_engagement:
        comment_text = entry.get("comment", "").lower()
        reply_text = entry.get("reply", "").lower()

        # Check for conversation starters
        for pattern in ENGAGEMENT_PATTERNS["conversation_starters"]:
            if re.search(pattern, comment_text):
                conversation_quality += 0.3
                break

        # Check for community building language
        for pattern in ENGAGEMENT_PATTERNS["community_builders"]:
            if re.search(pattern, comment_text) or re.search(pattern, reply_text):
                conversation_quality += 0.2
                break

        # Quality replies that ask follow-up questions
        if "?" in reply_text:
            conversation_quality += 0.2

        # Personalized responses (contain "you", "your")
        if any(word in reply_text for word in ["you", "your", "thanks"]):
            conversation_quality += 0.1

    return min(conversation_quality / max(total_interactions, 1), 1.0)


def calculate_community_growth(recent_data: List[Dict]) -> float:
    """Calculate community growth trends."""
    if len(recent_data) < 2:
        return 0.5  # Neutral if insufficient data

    # Group by date to track growth over time
    daily_engagement = defaultdict(lambda: {"likes": 0, "comments": 0, "saves": 0})

    for post in recent_data:
        date = post["date"]
        data = post["data"]
        daily_engagement[date]["likes"] += data.get("likes", 0)
        daily_engagement[date]["comments"] += data.get("comments", 0)
        daily_engagement[date]["saves"] += data.get("saves", 0)

    # Calculate trend (simple linear growth check)
    dates = sorted(daily_engagement.keys())
    if len(dates) < 3:
        return 0.5

    early_avg = sum(
        daily_engagement[date]["likes"] + daily_engagement[date]["comments"] + daily_engagement[date]["saves"]
        for date in dates[:len(dates)//2]
    ) / (len(dates)//2)

    late_avg = sum(
        daily_engagement[date]["likes"] + daily_engagement[date]["comments"] + daily_engagement[date]["saves"]
        for date in dates[len(dates)//2:]
    ) / (len(dates) - len(dates)//2)

    if early_avg == 0:
        return 1.0 if late_avg > 0 else 0.5

    growth_rate = (late_avg - early_avg) / early_avg
    return min(max(0.5 + growth_rate, 0.0), 1.0)


def calculate_platform_diversity(recent_data: List[Dict]) -> float:
    """Calculate how well-distributed engagement is across platforms."""
    if not recent_data:
        return 0.0

    platform_counts = defaultdict(int)
    for post in recent_data:
        platform_counts[post["platform"]] += 1

    # Calculate diversity score (closer to equal distribution = higher score)
    total_posts = len(recent_data)
    ideal_per_platform = total_posts / len(PLATFORMS)

    diversity_score = 0
    for platform in PLATFORMS:
        platform_ratio = platform_counts[platform] / total_posts
        ideal_ratio = 1 / len(PLATFORMS)
        # Lower penalty for being close to ideal distribution
        diversity_score += 1 - abs(platform_ratio - ideal_ratio)

    return diversity_score / len(PLATFORMS)


def analyze_response_quality(recent_engagement: List[Dict]) -> float:
    """Analyze the quality of responses generated by engagement agents."""
    if not recent_engagement:
        return 0.0

    total_responses = len(recent_engagement)
    quality_score = 0

    for entry in recent_engagement:
        reply = entry.get("reply", "").lower()

        # Quality indicators in responses
        quality_indicators = 0

        # Personalized responses
        if any(word in reply for word in ["you", "your", "thanks", "appreciate"]):
            quality_indicators += 1

        # Questions that encourage further engagement
        if "?" in reply:
            quality_indicators += 1

        # Specific references to content
        if any(word in reply for word in ["post", "photo", "video", "track", "music"]):
            quality_indicators += 1

        # Authentic language (not robotic)
        if len(reply.split()) > 5 and not reply.startswith("thank you for"):
            quality_indicators += 1

        # Emotional engagement
        if any(word in reply for word in ["love", "amazing", "great", "fantastic", "awesome"]):
            quality_indicators += 0.5

        quality_score += min(quality_indicators / 4, 1.0)  # Normalize to 0-1

    return quality_score / total_responses if total_responses > 0 else 0.0


def generate_community_recommendations(health_metrics: Dict[str, float]) -> List[str]:
    """Generate actionable recommendations for community building."""
    recommendations = []

    if health_metrics.get("engagement_quality", 0) < 0.5:
        recommendations.append("Focus on creating more engaging content that encourages comments and saves")
        recommendations.append("Ask questions and create polls to stimulate community discussion")

    if health_metrics.get("conversation_health", 0) < 0.5:
        recommendations.append("Improve reply quality with more personalized, question-asking responses")
        recommendations.append("Create content that naturally invites community participation")

    if health_metrics.get("community_growth", 0) < 0.5:
        recommendations.append("Analyze successful posts to identify growth patterns")
        recommendations.append("Increase posting frequency on platforms showing growth potential")

    if health_metrics.get("platform_diversity", 0) < 0.6:
        recommendations.append("Balance content distribution more evenly across all platforms")
        recommendations.append("Identify underperforming platforms and adjust strategy")

    if health_metrics.get("response_quality", 0) < 0.6:
        recommendations.append("Enhance engagement agent responses to be more conversational")
        recommendations.append("Train agents to ask follow-up questions and show genuine interest")

    if not recommendations:
        recommendations.append("Community health is good - maintain current strategies")
        recommendations.append("Consider expanding to new platforms or content types")

    return recommendations


def detect_community_trends() -> Dict[str, Any]:
    """Detect trending topics and community interests."""
    try:
        engagement_log = load_json(ENGAGEMENT_LOG)
        recent_engagement = get_recent_engagement_data(engagement_log, days=3)

        # Extract keywords and topics from comments
        topic_mentions = defaultdict(int)
        trend_indicators = []

        for entry in recent_engagement:
            comment_text = entry.get("comment", "").lower()

            # Check for trend indicators
            for pattern in ENGAGEMENT_PATTERNS["trend_indicators"]:
                if re.search(pattern, comment_text):
                    trend_indicators.append({
                        "text": comment_text,
                        "date": entry.get("date"),
                        "pattern": pattern
                    })

            # Extract potential topics (simple keyword extraction)
            words = re.findall(r'\w+', comment_text)
            for word in words:
                if len(word) > 3 and word not in ["this", "that", "with", "your", "really", "just"]:
                    topic_mentions[word] += 1

        # Identify trending topics
        trending_topics = [
            {"topic": topic, "mentions": count}
            for topic, count in topic_mentions.items()
            if count >= COMMUNITY_THRESHOLDS["trend_detection_mentions"]
        ]
        trending_topics.sort(key=lambda x: x["mentions"], reverse=True)

        return {
            "trending_topics": trending_topics[:10],  # Top 10
            "trend_indicators": trend_indicators,
            "total_conversations": len(recent_engagement),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {
            "trending_topics": [],
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def generate_apu48_dashboard() -> str:
    """Generate APU-48 community-focused dashboard."""
    community_health = analyze_community_health()
    trends = detect_community_trends()

    dashboard = []
    dashboard.append("=" * 80)
    dashboard.append("[*] VAWN COMMUNITY ENGAGEMENT MONITOR - APU-48")
    dashboard.append(f"[DATE] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    dashboard.append("=" * 80)

    # Community Health Section
    health_status = community_health.get("status", "unknown").upper()
    health_score = community_health.get("overall_score", 0.0)
    dashboard.append(f"\n[COMMUNITY HEALTH] Overall Score: {health_score:.2f} ({health_status})")

    if "metrics" in community_health:
        metrics = community_health["metrics"]
        dashboard.append(f"  • Engagement Quality: {metrics.get('engagement_quality', 0):.2f}")
        dashboard.append(f"  • Conversation Health: {metrics.get('conversation_health', 0):.2f}")
        dashboard.append(f"  • Community Growth: {metrics.get('community_growth', 0):.2f}")
        dashboard.append(f"  • Platform Diversity: {metrics.get('platform_diversity', 0):.2f}")
        dashboard.append(f"  • Response Quality: {metrics.get('response_quality', 0):.2f}")

    # Trending Topics Section
    dashboard.append(f"\n[TRENDING TOPICS] Community Interests:")
    trending_topics = trends.get("trending_topics", [])
    if trending_topics:
        for topic in trending_topics[:5]:  # Top 5
            dashboard.append(f"  • {topic['topic']}: {topic['mentions']} mentions")
    else:
        dashboard.append("  • No trending topics detected (low activity)")

    # Community Recommendations
    dashboard.append(f"\n[RECOMMENDATIONS] Community Building Actions:")
    recommendations = community_health.get("recommendations", [])
    for i, rec in enumerate(recommendations[:5], 1):  # Top 5 recommendations
        dashboard.append(f"  {i}. {rec}")

    # Activity Summary
    total_conversations = trends.get("total_conversations", 0)
    dashboard.append(f"\n[ACTIVITY SUMMARY]")
    dashboard.append(f"  • Recent Conversations: {total_conversations}")
    dashboard.append(f"  • Community Status: {health_status}")
    dashboard.append(f"  • Health Score: {health_score:.1%}")

    dashboard.append("\n" + "=" * 80)
    return "\n".join(dashboard)


def save_apu48_monitoring_report():
    """Save comprehensive APU-48 monitoring data."""
    community_health = analyze_community_health()
    trends = detect_community_trends()

    report = {
        "timestamp": datetime.now().isoformat(),
        "version": "apu48_community_v1",
        "community_health": community_health,
        "trending_topics": trends,
        "alert_level": determine_alert_level(community_health),
        "next_actions": generate_next_actions(community_health, trends)
    }

    # Save to monitoring log
    monitor_log = load_json(MONITOR_LOG) if Path(MONITOR_LOG).exists() else {}
    today = today_str()

    if today not in monitor_log:
        monitor_log[today] = []

    monitor_log[today].append(report)

    # Keep only last 30 days
    cutoff_date = (datetime.now() - timedelta(days=30)).date()
    monitor_log = {
        k: v for k, v in monitor_log.items()
        if datetime.fromisoformat(k + "T00:00:00").date() >= cutoff_date
    }

    save_json(MONITOR_LOG, monitor_log)

    # Save community insights separately
    insights_log = load_json(COMMUNITY_INSIGHTS_LOG) if Path(COMMUNITY_INSIGHTS_LOG).exists() else {}
    insights_log[datetime.now().isoformat()] = {
        "health_score": community_health.get("overall_score", 0.0),
        "trending_topics": trends.get("trending_topics", [])[:5],
        "recommendations": community_health.get("recommendations", [])[:3]
    }

    # Keep only last 100 insights
    if len(insights_log) > 100:
        sorted_keys = sorted(insights_log.keys())
        insights_log = {k: insights_log[k] for k in sorted_keys[-100:]}

    save_json(COMMUNITY_INSIGHTS_LOG, insights_log)
    return report


def determine_alert_level(community_health: Dict) -> str:
    """Determine alert level based on community health."""
    score = community_health.get("overall_score", 0.0)

    if score >= 0.8:
        return "healthy"
    elif score >= 0.6:
        return "moderate"
    elif score >= 0.4:
        return "warning"
    else:
        return "critical"


def generate_next_actions(community_health: Dict, trends: Dict) -> List[str]:
    """Generate specific next actions based on analysis."""
    actions = []

    health_score = community_health.get("overall_score", 0.0)

    if health_score < 0.5:
        actions.append("IMMEDIATE: Review engagement strategy and content quality")
        actions.append("IMMEDIATE: Increase personalized responses and community interaction")

    if len(trends.get("trending_topics", [])) == 0:
        actions.append("Create content around current events to spark conversations")
        actions.append("Ask community questions to identify interests")

    if health_score >= 0.7:
        actions.append("Maintain current successful strategies")
        actions.append("Consider expanding community initiatives")

    return actions


def main():
    """APU-48 Community Engagement Monitor main function."""
    print("\n[*] Vawn Community Engagement Monitor - APU-48 Starting...")

    # Generate and display community-focused dashboard
    dashboard = generate_apu48_dashboard()
    print(dashboard)

    # Save comprehensive monitoring report
    report = save_apu48_monitoring_report()

    # Enhanced logging with community focus
    health_score = report["community_health"].get("overall_score", 0.0)
    alert_level = report["alert_level"]

    status = "ok" if health_score >= 0.7 else "warning" if health_score >= 0.5 else "error"
    detail = f"Community health: {health_score:.1%}, Status: {alert_level}, Trending topics: {len(report['trending_topics'].get('trending_topics', []))}"

    log_run("CommunityEngagementMonitorAPU48", status, detail)

    print(f"\n[APU-48] Community monitoring complete - Health Score: {health_score:.1%}")
    return report


if __name__ == "__main__":
    report = main()

    # Exit based on community health
    health_score = report["community_health"].get("overall_score", 0.0)

    if health_score < 0.4:
        print("\n[CRITICAL] Community health requires immediate attention!")
        sys.exit(2)
    elif health_score < 0.6:
        print("\n[WARNING] Community health needs improvement")
        sys.exit(1)
    else:
        print("\n[OK] Community health is acceptable")
        sys.exit(0)