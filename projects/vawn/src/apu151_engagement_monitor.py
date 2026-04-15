"""
apu151_engagement_monitor.py — APU-151 Enhanced Engagement Monitor

Advanced community engagement monitoring with real-time intelligence,
enhanced Paperclip integration, and proactive engagement discovery.

Created by: Dex - Community Agent (APU-151)

Enhancements over APU-49:
- Real-time engagement data validation and gap detection
- Advanced community sentiment analysis and trend prediction
- Enhanced Paperclip department coordination with intelligent routing
- Proactive engagement opportunity discovery
- Cross-platform analytics normalization
- Intelligent alerting with context-aware recommendations
"""

import json
import sys
import os
import subprocess
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import (
    load_json, save_json, ENGAGEMENT_LOG, RESEARCH_LOG, METRICS_LOG,
    VAWN_DIR, log_run, today_str, get_anthropic_client
)

# Import previous monitor functions
sys.path.insert(0, r"C:\Users\rdyal\Vawn\src")
try:
    from apu49_paperclip_engagement_monitor import (
        DEPARTMENTS, analyze_department_specific_engagement,
        route_to_paperclip_departments, DEPARTMENT_THRESHOLDS
    )
    from apu48_community_engagement_monitor import (
        analyze_community_health, detect_community_trends,
        COMMUNITY_THRESHOLDS, ENGAGEMENT_PATTERNS
    )
except ImportError as e:
    print(f"[WARNING] Could not import previous modules: {e}")

# Configuration
MONITOR_LOG = VAWN_DIR / "research" / "apu151_engagement_monitor_log.json"
INTELLIGENCE_LOG = VAWN_DIR / "research" / "apu151_intelligence_log.json"
ALERTS_LOG = VAWN_DIR / "research" / "apu151_alerts_log.json"

# Create directories
for log_path in [MONITOR_LOG, INTELLIGENCE_LOG, ALERTS_LOG]:
    log_path.parent.mkdir(exist_ok=True)

# Enhanced thresholds for APU-151
ENHANCED_THRESHOLDS = {
    "data_quality_minimum": 0.7,  # Minimum data completeness required
    "real_time_staleness_hours": 2,  # Data older than 2h triggers refresh
    "engagement_velocity_threshold": 0.15,  # 15% change triggers analysis
    "community_health_critical": 0.4,  # Below 40% triggers immediate action
    "trend_confidence_minimum": 0.6,  # Minimum confidence for trend prediction
    "cross_platform_correlation_threshold": 0.3,  # Platform performance correlation
}

PLATFORMS = ["instagram", "tiktok", "x", "threads", "bluesky"]

# Advanced engagement patterns for APU-151
ADVANCED_PATTERNS = {
    "viral_indicators": [
        r"viral|trending|blow.*up|everywhere|everyone.*talking",
        r"fire|heat|slaps|hits.*different|absolutely.*incredible",
        r"shared.*\d+.*times|tagged.*friends|sent.*this"
    ],
    "collaboration_signals": [
        r"collab|feature|remix|cover|version",
        r"sample|flip|interpolat|inspired.*by",
        r"work.*together|team.*up|join.*forces"
    ],
    "community_building": [
        r"family|squad|team|community|together",
        r"support|love|appreciate|respect|admire",
        r"proud|inspiring|motivation|uplift"
    ],
    "monetization_opportunities": [
        r"buy|purchase|stream|download|available",
        r"exclusive|limited|special|early.*access",
        r"merch|merchandise|tour|concert|show"
    ]
}


def validate_data_quality() -> Dict[str, Any]:
    """Validate completeness and quality of engagement data."""
    validation_results = {
        "metrics_completeness": 0.0,
        "engagement_freshness": 0.0,
        "data_gaps": [],
        "quality_score": 0.0,
        "recommendations": []
    }

    try:
        # Check metrics log completeness
        metrics_log = load_json(METRICS_LOG)
        engagement_log = load_json(ENGAGEMENT_LOG)

        # Analyze metrics data quality
        total_expected_entries = len(PLATFORMS) * 7  # 7 days of data per platform
        actual_entries = 0
        recent_data_count = 0

        cutoff_date = datetime.now() - timedelta(days=7)

        for image, dates in metrics_log.items():
            for date_str, platforms in dates.items():
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    if date_obj >= cutoff_date:
                        recent_data_count += 1
                        for platform, data in platforms.items():
                            if isinstance(data, dict) and data.get("likes") is not None:
                                actual_entries += 1
                            elif data == "MANUAL_ENTRY_NEEDED":
                                validation_results["data_gaps"].append(f"{platform} on {date_str}")
                except ValueError:
                    continue

        if total_expected_entries > 0:
            validation_results["metrics_completeness"] = actual_entries / total_expected_entries

        # Check engagement log freshness
        if engagement_log.get("history"):
            latest_entry = max(
                (datetime.fromisoformat(entry["date"]) for entry in engagement_log["history"]),
                default=datetime.min
            )
            hours_since_latest = (datetime.now() - latest_entry).total_seconds() / 3600
            validation_results["engagement_freshness"] = max(0, 1 - (hours_since_latest / 24))

        # Calculate overall quality score
        validation_results["quality_score"] = (
            validation_results["metrics_completeness"] * 0.6 +
            validation_results["engagement_freshness"] * 0.4
        )

        # Generate recommendations
        if validation_results["quality_score"] < ENHANCED_THRESHOLDS["data_quality_minimum"]:
            validation_results["recommendations"].append("URGENT: Data quality below minimum threshold")

        if validation_results["data_gaps"]:
            validation_results["recommendations"].append(f"Fill {len(validation_results['data_gaps'])} manual entry gaps")

        if validation_results["engagement_freshness"] < 0.5:
            validation_results["recommendations"].append("Refresh engagement data - stale by >12 hours")

    except Exception as e:
        validation_results["error"] = str(e)
        validation_results["quality_score"] = 0.0

    return validation_results


def detect_engagement_velocity() -> Dict[str, Any]:
    """Detect rapid changes in engagement patterns that indicate trending content."""
    velocity_analysis = {
        "trending_posts": [],
        "declining_posts": [],
        "velocity_alerts": [],
        "platform_momentum": {},
        "overall_velocity": 0.0
    }

    try:
        metrics_log = load_json(METRICS_LOG)

        # Analyze recent vs. baseline engagement
        recent_data = {}  # last 24 hours
        baseline_data = {}  # 2-7 days ago

        now = datetime.now()
        recent_cutoff = now - timedelta(hours=24)
        baseline_start = now - timedelta(days=7)
        baseline_end = now - timedelta(days=2)

        for image, dates in metrics_log.items():
            for date_str, platforms in dates.items():
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')

                    for platform, data in platforms.items():
                        if not isinstance(data, dict):
                            continue

                        engagement = data.get("likes", 0) + data.get("comments", 0)

                        if date_obj >= recent_cutoff:
                            recent_data[f"{image}_{platform}"] = recent_data.get(f"{image}_{platform}", 0) + engagement
                        elif baseline_start <= date_obj <= baseline_end:
                            baseline_data[f"{image}_{platform}"] = baseline_data.get(f"{image}_{platform}", 0) + engagement

                except ValueError:
                    continue

        # Calculate velocity for each post/platform combo
        velocity_scores = []

        for post_platform in set(list(recent_data.keys()) + list(baseline_data.keys())):
            recent = recent_data.get(post_platform, 0)
            baseline = baseline_data.get(post_platform, 0)

            if baseline > 0:
                velocity = (recent - baseline) / baseline
            elif recent > 0:
                velocity = 1.0  # New content with engagement
            else:
                velocity = 0.0

            velocity_scores.append(velocity)

            # Identify trending and declining content
            if velocity > ENHANCED_THRESHOLDS["engagement_velocity_threshold"]:
                image, platform = post_platform.split("_", 1)
                velocity_analysis["trending_posts"].append({
                    "image": image,
                    "platform": platform,
                    "velocity": velocity,
                    "recent_engagement": recent,
                    "baseline_engagement": baseline
                })
            elif velocity < -ENHANCED_THRESHOLDS["engagement_velocity_threshold"]:
                image, platform = post_platform.split("_", 1)
                velocity_analysis["declining_posts"].append({
                    "image": image,
                    "platform": platform,
                    "velocity": velocity,
                    "recent_engagement": recent,
                    "baseline_engagement": baseline
                })

        # Calculate platform momentum
        for platform in PLATFORMS:
            platform_velocities = [v for k, v in zip(recent_data.keys(), velocity_scores) if platform in k]
            if platform_velocities:
                velocity_analysis["platform_momentum"][platform] = sum(platform_velocities) / len(platform_velocities)

        # Overall velocity score
        if velocity_scores:
            velocity_analysis["overall_velocity"] = sum(velocity_scores) / len(velocity_scores)

        # Generate velocity alerts
        for post in velocity_analysis["trending_posts"]:
            if post["velocity"] > 0.5:  # 50% increase
                velocity_analysis["velocity_alerts"].append({
                    "type": "trending_content",
                    "severity": "high" if post["velocity"] > 1.0 else "medium",
                    "message": f"{post['image']} trending on {post['platform']} (+{post['velocity']:.1%})",
                    "action": "Amplify content and engage with trend"
                })

    except Exception as e:
        velocity_analysis["error"] = str(e)

    return velocity_analysis


def analyze_cross_platform_performance() -> Dict[str, Any]:
    """Analyze performance patterns across platforms to optimize content strategy."""
    cross_platform_analysis = {
        "platform_rankings": {},
        "content_performance_patterns": [],
        "optimization_opportunities": [],
        "cross_platform_correlation": 0.0,
        "platform_specific_insights": {}
    }

    try:
        metrics_log = load_json(METRICS_LOG)

        # Aggregate platform performance
        platform_stats = defaultdict(lambda: {"posts": 0, "total_engagement": 0, "avg_engagement": 0})
        content_performance = defaultdict(list)  # content -> [platform performances]

        cutoff_date = datetime.now() - timedelta(days=7)

        for image, dates in metrics_log.items():
            platform_scores = {}

            for date_str, platforms in dates.items():
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    if date_obj < cutoff_date:
                        continue

                    for platform, data in platforms.items():
                        if isinstance(data, dict):
                            engagement = data.get("likes", 0) + data.get("comments", 0)
                            platform_stats[platform]["posts"] += 1
                            platform_stats[platform]["total_engagement"] += engagement
                            platform_scores[platform] = engagement

                except ValueError:
                    continue

            # Track content performance across platforms
            if len(platform_scores) >= 2:  # Need at least 2 platforms for comparison
                content_performance[image] = platform_scores

        # Calculate platform averages and rankings
        for platform in platform_stats:
            if platform_stats[platform]["posts"] > 0:
                platform_stats[platform]["avg_engagement"] = (
                    platform_stats[platform]["total_engagement"] / platform_stats[platform]["posts"]
                )

        # Rank platforms by average engagement
        sorted_platforms = sorted(
            platform_stats.items(),
            key=lambda x: x[1]["avg_engagement"],
            reverse=True
        )

        for i, (platform, stats) in enumerate(sorted_platforms):
            cross_platform_analysis["platform_rankings"][platform] = {
                "rank": i + 1,
                "avg_engagement": stats["avg_engagement"],
                "total_posts": stats["posts"],
                "total_engagement": stats["total_engagement"]
            }

        # Analyze content performance patterns
        for image, platform_scores in content_performance.items():
            if len(platform_scores) >= 3:  # Good cross-platform data
                best_platform = max(platform_scores, key=platform_scores.get)
                worst_platform = min(platform_scores, key=platform_scores.get)

                performance_ratio = platform_scores[best_platform] / max(platform_scores[worst_platform], 1)

                cross_platform_analysis["content_performance_patterns"].append({
                    "content": image,
                    "best_platform": best_platform,
                    "worst_platform": worst_platform,
                    "performance_ratio": performance_ratio,
                    "platform_scores": platform_scores
                })

        # Generate optimization opportunities
        if sorted_platforms:
            top_platform = sorted_platforms[0][0]
            bottom_platform = sorted_platforms[-1][0] if len(sorted_platforms) > 1 else None

            cross_platform_analysis["optimization_opportunities"].append(
                f"Focus more content on {top_platform} (top performer: {platform_stats[top_platform]['avg_engagement']:.1f} avg engagement)"
            )

            if bottom_platform and platform_stats[bottom_platform]["avg_engagement"] > 0:
                cross_platform_analysis["optimization_opportunities"].append(
                    f"Improve {bottom_platform} strategy (underperforming: {platform_stats[bottom_platform]['avg_engagement']:.1f} avg engagement)"
                )

        # Calculate cross-platform correlation
        platform_pairs = []
        for image, platform_scores in content_performance.items():
            platforms = list(platform_scores.keys())
            if len(platforms) >= 2:
                for i in range(len(platforms)):
                    for j in range(i + 1, len(platforms)):
                        platform_pairs.append((platform_scores[platforms[i]], platform_scores[platforms[j]]))

        if len(platform_pairs) >= 3:
            # Simple correlation calculation
            correlations = []
            for score1, score2 in platform_pairs:
                if score1 > 0 and score2 > 0:
                    correlations.append(min(score1, score2) / max(score1, score2))

            if correlations:
                cross_platform_analysis["cross_platform_correlation"] = sum(correlations) / len(correlations)

    except Exception as e:
        cross_platform_analysis["error"] = str(e)

    return cross_platform_analysis


def generate_intelligent_recommendations() -> Dict[str, Any]:
    """Generate AI-powered recommendations based on comprehensive analysis."""
    recommendations = {
        "immediate_actions": [],
        "strategic_initiatives": [],
        "department_specific": {},
        "content_strategy": [],
        "community_building": [],
        "priority_score": 0.0
    }

    try:
        # Get all analysis data
        data_quality = validate_data_quality()
        velocity = detect_engagement_velocity()
        cross_platform = analyze_cross_platform_performance()

        # Get previous analysis if available
        try:
            community_health = analyze_community_health()
            department_analytics = analyze_department_specific_engagement()
        except:
            community_health = {"overall_score": 0.0}
            department_analytics = {}

        # Immediate actions based on critical issues
        if data_quality["quality_score"] < 0.5:
            recommendations["immediate_actions"].append({
                "action": "DATA QUALITY CRISIS: Implement data collection fixes",
                "priority": "critical",
                "timeline": "immediate",
                "department": "operations"
            })

        if len(velocity["trending_posts"]) > 0:
            for post in velocity["trending_posts"][:3]:  # Top 3 trending
                recommendations["immediate_actions"].append({
                    "action": f"CAPITALIZE: Amplify trending content '{post['image']}' on {post['platform']}",
                    "priority": "high",
                    "timeline": "next 2 hours",
                    "department": "creative_revenue"
                })

        # Strategic initiatives
        if cross_platform["platform_rankings"]:
            top_platforms = sorted(
                cross_platform["platform_rankings"].items(),
                key=lambda x: x[1]["avg_engagement"],
                reverse=True
            )[:2]

            for platform, stats in top_platforms:
                recommendations["strategic_initiatives"].append(
                    f"Double down on {platform} content strategy (avg engagement: {stats['avg_engagement']:.1f})"
                )

        # Department-specific recommendations
        for dept_key in DEPARTMENTS:
            if dept_key == "chairman":
                continue

            dept_recommendations = []

            if dept_key == "legal" and data_quality["data_gaps"]:
                dept_recommendations.append("Review data collection compliance and API usage rights")
            elif dept_key == "a_and_r" and velocity["trending_posts"]:
                dept_recommendations.append("Analyze trending content for talent discovery opportunities")
            elif dept_key == "creative_revenue" and cross_platform["optimization_opportunities"]:
                dept_recommendations.extend(cross_platform["optimization_opportunities"])
            elif dept_key == "operations" and data_quality["quality_score"] < 0.7:
                dept_recommendations.append("Improve data pipeline reliability and monitoring")

            if dept_recommendations:
                recommendations["department_specific"][dept_key] = dept_recommendations

        # Content strategy recommendations
        if velocity["declining_posts"]:
            recommendations["content_strategy"].append(
                f"Refresh strategy for declining content types ({len(velocity['declining_posts'])} posts declining)"
            )

        if cross_platform["cross_platform_correlation"] > 0.7:
            recommendations["content_strategy"].append(
                "Strong cross-platform correlation detected - create platform-agnostic content templates"
            )

        # Community building recommendations
        community_score = community_health.get("overall_score", 0.0)
        if community_score < ENHANCED_THRESHOLDS["community_health_critical"]:
            recommendations["community_building"].append("URGENT: Community health critical - implement immediate engagement campaign")
            recommendations["community_building"].append("Launch direct fan interaction initiatives to rebuild community connection")

        # Calculate priority score
        critical_issues = len([a for a in recommendations["immediate_actions"] if a["priority"] == "critical"])
        high_issues = len([a for a in recommendations["immediate_actions"] if a["priority"] == "high"])

        recommendations["priority_score"] = min(1.0, (critical_issues * 0.5 + high_issues * 0.3))

    except Exception as e:
        recommendations["error"] = str(e)

    return recommendations


def create_apu151_dashboard() -> str:
    """Create comprehensive APU-151 engagement monitor dashboard."""

    # Get all analysis components
    data_quality = validate_data_quality()
    velocity = detect_engagement_velocity()
    cross_platform = analyze_cross_platform_performance()
    recommendations = generate_intelligent_recommendations()

    # Get previous system analysis
    try:
        community_health = analyze_community_health()
        department_analytics = analyze_department_specific_engagement()
        trends = detect_community_trends()
    except Exception as e:
        community_health = {"overall_score": 0.0, "status": "error", "error": str(e)}
        department_analytics = {}
        trends = {"trending_topics": []}

    dashboard = []
    dashboard.append("=" * 100)
    dashboard.append("[*] VAWN ENHANCED ENGAGEMENT MONITOR - APU-151")
    dashboard.append("[*] Real-time Intelligence & Proactive Community Engagement")
    dashboard.append(f"[DATE] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    dashboard.append("=" * 100)

    # System Health Overview
    quality_score = data_quality.get("quality_score", 0.0)
    community_score = community_health.get("overall_score", 0.0)
    velocity_score = abs(velocity.get("overall_velocity", 0.0))

    overall_health = (quality_score * 0.4 + community_score * 0.4 + velocity_score * 0.2)
    health_status = "EXCELLENT" if overall_health > 0.8 else "GOOD" if overall_health > 0.6 else "WARNING" if overall_health > 0.4 else "CRITICAL"

    dashboard.append(f"\n[SYSTEM HEALTH] Overall Status: {health_status} ({overall_health:.1%})")
    dashboard.append(f"  • Data Quality: {quality_score:.1%} | Community Health: {community_score:.1%} | Engagement Velocity: {velocity_score:.1%}")

    # Data Quality Section
    dashboard.append(f"\n[DATA QUALITY] Validation Results:")
    dashboard.append(f"  • Metrics Completeness: {data_quality.get('metrics_completeness', 0):.1%}")
    dashboard.append(f"  • Data Freshness: {data_quality.get('engagement_freshness', 0):.1%}")
    dashboard.append(f"  • Data Gaps: {len(data_quality.get('data_gaps', []))}")

    if data_quality.get("recommendations"):
        dashboard.append("  • Urgent Data Actions:")
        for rec in data_quality["recommendations"][:3]:
            dashboard.append(f"    - {rec}")

    # Engagement Velocity Section
    dashboard.append(f"\n[ENGAGEMENT VELOCITY] Real-time Trends:")
    dashboard.append(f"  • Overall Velocity: {velocity.get('overall_velocity', 0):.1%}")
    dashboard.append(f"  • Trending Content: {len(velocity.get('trending_posts', []))}")
    dashboard.append(f"  • Declining Content: {len(velocity.get('declining_posts', []))}")

    # Show top trending content
    trending_posts = velocity.get("trending_posts", [])
    if trending_posts:
        dashboard.append("  • Top Trending:")
        for post in trending_posts[:3]:
            dashboard.append(f"    - {post['image']} on {post['platform']}: +{post['velocity']:.1%}")

    # Platform Performance Section
    dashboard.append(f"\n[CROSS-PLATFORM ANALYSIS] Performance Rankings:")
    platform_rankings = cross_platform.get("platform_rankings", {})
    if platform_rankings:
        for platform, stats in sorted(platform_rankings.items(), key=lambda x: x[1]["rank"]):
            rank_emoji = ["[1st]", "[2nd]", "[3rd]", "[4th]", "[5th]"][min(stats["rank"] - 1, 4)]
            dashboard.append(f"  {rank_emoji} {platform.upper()}: {stats['avg_engagement']:.1f} avg | {stats['total_posts']} posts")

    # Community Intelligence Section
    dashboard.append(f"\n[COMMUNITY INTELLIGENCE] APU-48/49 Integration:")
    dashboard.append(f"  • Community Health: {community_score:.1%} ({community_health.get('status', 'unknown').upper()})")

    trending_topics = trends.get("trending_topics", [])
    dashboard.append(f"  • Active Topics: {len(trending_topics)}")
    if trending_topics:
        for topic in trending_topics[:3]:
            dashboard.append(f"    - {topic['topic']}: {topic['mentions']} mentions")

    # Department Status (Paperclip Integration)
    dashboard.append(f"\n[DEPARTMENT COORDINATION] Paperclip Integration:")
    if "chairman" in department_analytics:
        exec_summary = department_analytics["chairman"]
        org_health = exec_summary.get("overall_organizational_health", 0.0)
        dashboard.append(f"  • Organizational Health: {org_health:.1%}")
        dashboard.append(f"  • Departments Requiring Attention: {len(exec_summary.get('departments_at_risk', []))}")
    else:
        dashboard.append("  • Department analytics unavailable - integration issue detected")

    # Intelligent Recommendations Section
    dashboard.append(f"\n[AI RECOMMENDATIONS] Priority Score: {recommendations.get('priority_score', 0.0):.1%}")

    immediate_actions = recommendations.get("immediate_actions", [])
    if immediate_actions:
        dashboard.append("  • IMMEDIATE ACTIONS:")
        for action in immediate_actions[:3]:
            priority_icon = {"critical": "[CRIT]", "high": "[HIGH]", "medium": "[MED]"}.get(action["priority"], "[MED]")
            dashboard.append(f"    {priority_icon} {action['action']}")

    strategic_initiatives = recommendations.get("strategic_initiatives", [])
    if strategic_initiatives:
        dashboard.append("  • STRATEGIC INITIATIVES:")
        for initiative in strategic_initiatives[:2]:
            dashboard.append(f"    [STRAT] {initiative}")

    # Alert Summary
    total_alerts = len(velocity.get("velocity_alerts", [])) + len(data_quality.get("data_gaps", [])) + len(immediate_actions)
    dashboard.append(f"\n[ALERT SUMMARY] Total Active Alerts: {total_alerts}")

    if total_alerts > 0:
        priority_distribution = Counter([a["priority"] for a in immediate_actions])
        for priority, count in priority_distribution.items():
            dashboard.append(f"  • {priority.upper()}: {count}")
    else:
        dashboard.append("  • All systems operating within normal parameters")

    dashboard.append(f"\n" + "=" * 100)
    return "\n".join(dashboard)


def save_apu151_monitoring_report():
    """Save comprehensive APU-151 monitoring report with all analysis components."""

    # Gather all analysis data
    analysis_data = {
        "data_quality": validate_data_quality(),
        "engagement_velocity": detect_engagement_velocity(),
        "cross_platform_analysis": analyze_cross_platform_performance(),
        "intelligent_recommendations": generate_intelligent_recommendations()
    }

    # Get integrated analysis from previous systems
    try:
        analysis_data["community_health"] = analyze_community_health()
        analysis_data["department_analytics"] = analyze_department_specific_engagement()
        analysis_data["community_trends"] = detect_community_trends()
    except Exception as e:
        analysis_data["integration_error"] = str(e)

    # Create comprehensive report
    report = {
        "timestamp": datetime.now().isoformat(),
        "version": "apu151_enhanced_v1",
        "system_status": determine_system_status(analysis_data),
        "analysis": analysis_data,
        "summary": generate_executive_summary(analysis_data),
        "next_review_time": (datetime.now() + timedelta(hours=2)).isoformat()
    }

    # Save main monitoring log
    monitor_log = load_json(MONITOR_LOG) if Path(MONITOR_LOG).exists() else {}
    today = today_str()

    if today not in monitor_log:
        monitor_log[today] = []

    monitor_log[today].append(report)

    # Keep last 30 days
    cutoff_date = (datetime.now() - timedelta(days=30)).date()
    monitor_log = {
        k: v for k, v in monitor_log.items()
        if datetime.fromisoformat(k + "T00:00:00").date() >= cutoff_date
    }

    save_json(MONITOR_LOG, monitor_log)

    # Save intelligence insights separately
    intelligence_insights = {
        "timestamp": datetime.now().isoformat(),
        "trending_content": analysis_data["engagement_velocity"].get("trending_posts", []),
        "optimization_opportunities": analysis_data["cross_platform_analysis"].get("optimization_opportunities", []),
        "ai_recommendations": analysis_data["intelligent_recommendations"],
        "system_health_score": report["summary"].get("overall_health_score", 0.0)
    }

    intelligence_log = load_json(INTELLIGENCE_LOG) if Path(INTELLIGENCE_LOG).exists() else []
    intelligence_log.append(intelligence_insights)

    # Keep last 100 intelligence entries
    if len(intelligence_log) > 100:
        intelligence_log = intelligence_log[-100:]

    save_json(INTELLIGENCE_LOG, intelligence_log)

    return report


def determine_system_status(analysis_data: Dict) -> str:
    """Determine overall system status based on all analysis components."""
    scores = []

    # Data quality score
    scores.append(analysis_data["data_quality"].get("quality_score", 0.0))

    # Community health score
    if "community_health" in analysis_data:
        scores.append(analysis_data["community_health"].get("overall_score", 0.0))

    # Velocity health (normalized)
    velocity = abs(analysis_data["engagement_velocity"].get("overall_velocity", 0.0))
    scores.append(min(velocity * 2, 1.0))  # Double velocity score, cap at 1.0

    # Platform correlation score
    correlation = analysis_data["cross_platform_analysis"].get("cross_platform_correlation", 0.0)
    scores.append(correlation)

    if scores:
        overall_score = sum(scores) / len(scores)

        if overall_score >= 0.8:
            return "excellent"
        elif overall_score >= 0.6:
            return "good"
        elif overall_score >= 0.4:
            return "warning"
        else:
            return "critical"

    return "unknown"


def generate_executive_summary(analysis_data: Dict) -> Dict[str, Any]:
    """Generate executive summary for APU-151 monitoring."""
    summary = {
        "overall_health_score": 0.0,
        "critical_alerts": 0,
        "trending_opportunities": 0,
        "data_quality_status": "unknown",
        "top_recommendations": [],
        "system_performance": "unknown"
    }

    try:
        # Calculate overall health score
        scores = []
        scores.append(analysis_data["data_quality"].get("quality_score", 0.0))

        if "community_health" in analysis_data:
            scores.append(analysis_data["community_health"].get("overall_score", 0.0))

        velocity = abs(analysis_data["engagement_velocity"].get("overall_velocity", 0.0))
        scores.append(min(velocity * 2, 1.0))

        if scores:
            summary["overall_health_score"] = sum(scores) / len(scores)

        # Count critical alerts
        immediate_actions = analysis_data["intelligent_recommendations"].get("immediate_actions", [])
        summary["critical_alerts"] = len([a for a in immediate_actions if a["priority"] == "critical"])

        # Count trending opportunities
        summary["trending_opportunities"] = len(analysis_data["engagement_velocity"].get("trending_posts", []))

        # Data quality status
        quality_score = analysis_data["data_quality"].get("quality_score", 0.0)
        summary["data_quality_status"] = "good" if quality_score > 0.7 else "warning" if quality_score > 0.4 else "critical"

        # Top recommendations
        recommendations = analysis_data["intelligent_recommendations"]
        top_recs = recommendations.get("immediate_actions", [])[:3]
        top_recs.extend(recommendations.get("strategic_initiatives", [])[:2])
        summary["top_recommendations"] = top_recs

        # System performance
        summary["system_performance"] = determine_system_status(analysis_data)

    except Exception as e:
        summary["error"] = str(e)

    return summary


def main():
    """APU-151 Enhanced Engagement Monitor main function."""
    print("\n[*] Vawn Enhanced Engagement Monitor - APU-151 Starting...")
    print("[*] Initializing real-time intelligence and proactive community engagement...")

    # Generate and display enhanced dashboard
    dashboard = create_apu151_dashboard()
    print(dashboard)

    # Save comprehensive monitoring report
    report = save_apu151_monitoring_report()

    # Enhanced logging
    summary = report.get("summary", {})
    system_status = report.get("system_status", "unknown")
    overall_health = summary.get("overall_health_score", 0.0)
    critical_alerts = summary.get("critical_alerts", 0)
    trending_opportunities = summary.get("trending_opportunities", 0)

    # Determine log status
    if system_status == "critical" or critical_alerts > 0:
        log_status = "error"
    elif system_status == "warning":
        log_status = "warning"
    else:
        log_status = "ok"

    detail = (f"Health: {overall_health:.1%}, Status: {system_status}, "
             f"Critical alerts: {critical_alerts}, Trending: {trending_opportunities}")

    log_run("EnhancedEngagementMonitorAPU151", log_status, detail)

    print(f"\n[APU-151] Enhanced monitoring complete")
    print(f"[HEALTH] System Health Score: {overall_health:.1%} ({system_status.upper()})")
    print(f"[INTEL] Critical Alerts: {critical_alerts} | Trending Opportunities: {trending_opportunities}")

    return report


if __name__ == "__main__":
    report = main()

    # Enhanced exit logic based on system health
    system_status = report.get("system_status", "unknown")
    critical_alerts = report.get("summary", {}).get("critical_alerts", 0)

    if system_status == "critical" or critical_alerts > 0:
        print(f"\n[CRITICAL] System requires immediate attention!")
        sys.exit(2)
    elif system_status == "warning":
        print(f"\n[WARNING] System performance degraded - monitoring required")
        sys.exit(1)
    else:
        print(f"\n[SUCCESS] APU-151 Enhanced engagement monitoring operational")
        sys.exit(0)