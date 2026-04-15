"""
apu44_enhanced_engagement_monitor.py — APU-44 Enhanced monitoring system for Vawn's engagement.
Fixes misleading alerts by distinguishing between API infrastructure issues and genuine engagement problems.

Created by: Dex - Community Agent (APU-44)
Enhancements over enhanced_engagement_monitor.py:
- Separates API availability issues from engagement performance issues
- More accurate alert generation with actionable recommendations
- Clear distinction between infrastructure and community problems
"""

import json
import sys
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import subprocess
import time

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import (
    load_json, save_json, ENGAGEMENT_LOG, RESEARCH_LOG, METRICS_LOG,
    VAWN_DIR, log_run, today_str, get_anthropic_client
)

# Configuration
MONITOR_LOG = VAWN_DIR / "research" / "apu44_engagement_monitor_log.json"
ALERT_THRESHOLD = {
    "no_activity_days": 2,  # Alert if no successful runs for 2+ days
    "low_engagement_rate": 0.05,  # Alert if engagement rate drops below 5%
    "actual_failure_hours": 6,  # Alert only if agents actually fail for 6+ hours
    "consecutive_failures": 3,  # Alert if 3+ consecutive failures
    "api_availability_threshold": 0.8,  # Alert if <80% of posts have API data
}

PLATFORMS = ["instagram", "tiktok", "x", "threads", "bluesky"]

# Agent status classification
AGENT_STATUS = {
    "healthy": "Agent running and processing work successfully",
    "idle": "Agent running but no work available (normal)",
    "warning": "Agent has some issues but still functional",
    "failed": "Agent not running or consistently failing",
    "unknown": "Unable to determine agent status"
}


def get_real_time_agent_status() -> Dict[str, Any]:
    """
    Enhanced agent health check from enhanced_engagement_monitor.py.
    Reused without modification as it properly distinguishes idle vs failed states.
    """
    research_log = load_json(RESEARCH_LOG)
    today = today_str()
    yesterday = str((datetime.now() - timedelta(days=1)).date())

    # Get recent entries for analysis (last 24 hours)
    recent_entries = []
    for date in [today, yesterday]:
        if date in research_log:
            cutoff = datetime.now() - timedelta(hours=24)
            for entry in research_log[date]:
                entry_time = datetime.fromisoformat(entry["time"])
                if entry_time > cutoff and entry["agent"] in ["EngagementAgent", "EngagementBot"]:
                    recent_entries.append(entry)

    # Analyze each agent separately
    agents = {}
    for agent_name in ["EngagementAgent", "EngagementBot"]:
        agent_entries = [e for e in recent_entries if e["agent"] == agent_name]

        if not agent_entries:
            status = "unknown"
            health_score = 0
            last_activity = None
            activity_pattern = "no_recent_activity"
        else:
            # Sort by time
            agent_entries.sort(key=lambda x: x["time"])
            last_entry = agent_entries[-1]
            last_activity = last_entry["time"]

            # Analyze success/failure pattern
            statuses = [e["status"] for e in agent_entries[-10:]]  # Last 10 runs
            success_rate = statuses.count("ok") / len(statuses) if statuses else 0

            # Determine status based on recent pattern
            if success_rate >= 0.8:
                if "No comments to process" in last_entry.get("detail", ""):
                    status = "idle"  # Working but no work available
                    activity_pattern = "healthy_idle"
                else:
                    status = "healthy"  # Working and processing
                    activity_pattern = "active_processing"
                health_score = success_rate
            elif success_rate >= 0.5:
                status = "warning"
                activity_pattern = "intermittent_issues"
                health_score = success_rate
            else:
                status = "failed"
                activity_pattern = "consistent_failures"
                health_score = success_rate

        # Calculate work metrics
        work_entries = [e for e in agent_entries if "ok" == e["status"]]
        comments_processed = 0
        engagement_actions = 0

        for entry in work_entries:
            detail = entry.get("detail", "")
            # Extract metrics from details
            if "likes" in detail:
                try:
                    engagement_actions += int(detail.split()[0]) if detail.split()[0].isdigit() else 0
                except:
                    pass
            if "replies generated" in detail:
                try:
                    comments_processed += int(detail.split()[0]) if detail.split()[0].isdigit() else 0
                except:
                    pass

        agents[agent_name.lower()] = {
            "last_activity": last_activity,
            "status": status,
            "health_score": health_score,
            "activity_pattern": activity_pattern,
            "runs_24h": len(agent_entries),
            "success_rate": success_rate,
            "comments_processed": comments_processed,
            "engagement_actions": engagement_actions,
            "recent_statuses": statuses[-5:] if statuses else [],
            "status_description": AGENT_STATUS[status]
        }

    return agents


def analyze_platform_performance() -> Dict[str, Any]:
    """
    Enhanced platform analysis with detailed API availability tracking.
    Based on enhanced_engagement_monitor.py with APU-44 improvements for API status detection.
    """
    metrics_log = load_json(METRICS_LOG)
    engagement_log = load_json(ENGAGEMENT_LOG)

    platform_stats = {}
    total_posts = 0
    total_engagement = 0
    api_posts = 0  # Posts with API data

    # Analyze platform metrics with detailed API tracking
    for image, dates in metrics_log.items():
        for date, platforms in dates.items():
            total_posts += len(platforms)
            for platform, data in platforms.items():
                if platform not in platform_stats:
                    platform_stats[platform] = {
                        "posts": 0,
                        "total_likes": 0,
                        "total_comments": 0,
                        "total_saves": 0,
                        "total_reposts": 0,
                        "api_status": "unknown",
                        "last_activity": None,
                        "api_posts": 0,  # APU-44: Track API vs manual posts
                        "manual_posts": 0,  # APU-44: Track manual entry posts
                        "api_availability_rate": 0.0  # APU-44: Percentage of posts with API data
                    }

                platform_stats[platform]["posts"] += 1
                platform_stats[platform]["last_activity"] = date

                if isinstance(data, dict) and "_note" not in data:
                    # API data available
                    platform_stats[platform]["total_likes"] += data.get("likes", 0)
                    platform_stats[platform]["total_comments"] += data.get("comments", 0)
                    platform_stats[platform]["total_saves"] += data.get("saves", 0) + data.get("reposts", 0)
                    platform_stats[platform]["api_status"] = "available"
                    platform_stats[platform]["api_posts"] += 1
                    total_engagement += data.get("likes", 0) + data.get("comments", 0)
                    api_posts += 1
                else:
                    # Manual entry needed or contains "_note"
                    platform_stats[platform]["api_status"] = "manual_entry_needed"
                    platform_stats[platform]["manual_posts"] += 1

    # Calculate performance metrics and API availability rates
    for platform in platform_stats:
        stats = platform_stats[platform]
        if stats["posts"] > 0:
            # Calculate API availability rate
            stats["api_availability_rate"] = stats["api_posts"] / stats["posts"]

            # Only calculate engagement metrics for posts with API data
            if stats["api_posts"] > 0:
                stats["avg_engagement"] = (stats["total_likes"] + stats["total_comments"]) / stats["api_posts"]
                stats["engagement_rate"] = stats["avg_engagement"] / max(stats["api_posts"], 1)

                # Performance classification (only for platforms with API data)
                if stats["avg_engagement"] > 5:
                    stats["performance"] = "excellent"
                elif stats["avg_engagement"] > 1:
                    stats["performance"] = "good"
                elif stats["avg_engagement"] > 0.5:
                    stats["performance"] = "moderate"
                elif stats["avg_engagement"] > 0:
                    stats["performance"] = "low"
                else:
                    stats["performance"] = "none"
            else:
                # No API data available - cannot assess performance
                stats["avg_engagement"] = 0
                stats["engagement_rate"] = 0
                stats["performance"] = "no_api_data"
        else:
            stats["avg_engagement"] = 0
            stats["engagement_rate"] = 0
            stats["performance"] = "no_data"
            stats["api_availability_rate"] = 0

    # Comment processing analysis (unchanged from enhanced version)
    comment_stats = {
        "total_comments_seen": len(engagement_log.get("replied_ids", [])),
        "replies_sent": len(engagement_log.get("history", [])),
        "response_rate": 0.0,
        "recent_activity": False,
        "api_status": "unknown"
    }

    if comment_stats["total_comments_seen"] > 0:
        comment_stats["response_rate"] = comment_stats["replies_sent"] / comment_stats["total_comments_seen"]

    # Check recent comment activity
    recent_history = [
        h for h in engagement_log.get("history", [])
        if datetime.fromisoformat(h["date"]) > datetime.now() - timedelta(days=1)
    ]
    comment_stats["recent_activity"] = len(recent_history) > 0

    # Determine comment API status based on agent logs
    research_log = load_json(RESEARCH_LOG)
    today = today_str()
    if today in research_log:
        recent_agent_logs = [e for e in research_log[today] if e["agent"] == "EngagementAgent"]
        if any("404" in e.get("detail", "") or "not available" in e.get("detail", "") for e in recent_agent_logs):
            comment_stats["api_status"] = "unavailable_404"
        elif any("No comments to process" in e.get("detail", "") for e in recent_agent_logs):
            comment_stats["api_status"] = "available_no_comments"
        else:
            comment_stats["api_status"] = "available"

    return {
        "platform_stats": platform_stats,
        "comment_stats": comment_stats,
        "overall_engagement_rate": total_engagement / max(api_posts, 1),  # Only count API posts
        "total_posts": total_posts,
        "api_posts": api_posts,
        "api_coverage_rate": api_posts / max(total_posts, 1),
        "top_performer": max(
            [p for p in platform_stats.keys() if platform_stats[p]["performance"] not in ["no_api_data", "no_data"]],
            key=lambda p: platform_stats[p]["avg_engagement"],
            default=None
        )
    }


def generate_apu44_intelligent_alerts(agents: Dict, metrics: Dict) -> List[Dict[str, str]]:
    """
    APU-44 Enhanced alert generation that properly distinguishes between:
    1. Infrastructure issues (missing APIs, broken integrations)
    2. Community engagement issues (content not performing well)
    3. Technical issues (agent failures, system problems)
    """
    alerts = []

    # Agent health alerts (unchanged - works correctly)
    for agent_name, agent_data in agents.items():
        if agent_data["status"] == "failed":
            alerts.append({
                "type": "agent_failure",
                "severity": "high",
                "message": f"{agent_name} has failed consistently (success rate: {agent_data['success_rate']:.1%})",
                "agent": agent_name,
                "action": "Check agent logs and restart if needed",
                "category": "technical"  # APU-44: Categorize alert types
            })
        elif agent_data["status"] == "warning":
            alerts.append({
                "type": "agent_degraded",
                "severity": "medium",
                "message": f"{agent_name} has intermittent issues (success rate: {agent_data['success_rate']:.1%})",
                "agent": agent_name,
                "action": "Monitor for patterns and investigate if continues",
                "category": "technical"
            })
        elif agent_data["status"] == "unknown":
            alerts.append({
                "type": "agent_unknown",
                "severity": "medium",
                "message": f"{agent_name} status unknown - no recent activity",
                "agent": agent_name,
                "action": "Check if agent is scheduled and running",
                "category": "technical"
            })

    # APU-44 ENHANCEMENT: Separate infrastructure alerts from engagement alerts
    infrastructure_issues = []
    engagement_issues = []

    for platform, stats in metrics["platform_stats"].items():
        # Check API availability first
        if stats["api_availability_rate"] < ALERT_THRESHOLD["api_availability_threshold"] and stats["posts"] > 3:
            infrastructure_issues.append({
                "platform": platform,
                "availability": stats["api_availability_rate"],
                "api_posts": stats["api_posts"],
                "manual_posts": stats["manual_posts"]
            })
        elif stats["api_availability_rate"] >= ALERT_THRESHOLD["api_availability_threshold"] and stats["performance"] == "none":
            # Platform has API access but zero engagement - genuine content issue
            engagement_issues.append({
                "platform": platform,
                "engagement": stats["avg_engagement"],
                "posts": stats["api_posts"]
            })

    # Generate infrastructure alerts
    if infrastructure_issues:
        if len(infrastructure_issues) >= 3:
            alerts.append({
                "type": "api_infrastructure_gap",
                "severity": "high",
                "message": f"API integration missing for {len(infrastructure_issues)} platforms: {', '.join([i['platform'] for i in infrastructure_issues])}",
                "platforms": [i['platform'] for i in infrastructure_issues],
                "action": "Implement missing API integrations (see platform-api-integration-roadmap.md)",
                "category": "infrastructure"
            })
        else:
            for issue in infrastructure_issues:
                alerts.append({
                    "type": "api_integration_partial",
                    "severity": "medium",
                    "message": f"{issue['platform']} API integration incomplete ({issue['availability']:.1%} coverage)",
                    "platform": issue['platform'],
                    "action": f"Fix API integration for {issue['platform']} - {issue['manual_posts']} posts require manual entry",
                    "category": "infrastructure"
                })

    # Generate engagement alerts (only for platforms with working APIs)
    if engagement_issues:
        if len(engagement_issues) >= 2:
            alerts.append({
                "type": "multi_platform_engagement_low",
                "severity": "medium",
                "message": f"Low engagement on platforms with working APIs: {', '.join([i['platform'] for i in engagement_issues])}",
                "platforms": [i['platform'] for i in engagement_issues],
                "action": "Review content strategy for these platforms - API data shows genuine low engagement",
                "category": "community"
            })
        else:
            for issue in engagement_issues:
                alerts.append({
                    "type": "platform_engagement_low",
                    "severity": "low",
                    "message": f"{issue['platform']} showing low engagement ({issue['engagement']:.1f} avg over {issue['posts']} posts)",
                    "platform": issue['platform'],
                    "action": f"Optimize content strategy for {issue['platform']}",
                    "category": "community"
                })

    # Comment processing alerts (unchanged - works correctly)
    comment_stats = metrics["comment_stats"]
    if comment_stats["api_status"] == "unavailable_404":
        alerts.append({
            "type": "comment_api_unavailable",
            "severity": "low",
            "message": "Comment API endpoint returning 404 - feature may not be deployed yet",
            "action": "Check with backend team about comment API availability",
            "category": "infrastructure"
        })
    elif not comment_stats["recent_activity"] and comment_stats["total_comments_seen"] > 0:
        alerts.append({
            "type": "comment_processing_stalled",
            "severity": "medium",
            "message": "Comment processing appears stalled despite available comments",
            "action": "Check engagement agent functionality",
            "category": "technical"
        })

    # Overall system health alert
    api_coverage = metrics.get("api_coverage_rate", 0)
    if api_coverage < 0.5:
        alerts.append({
            "type": "api_coverage_low",
            "severity": "high",
            "message": f"Low API coverage across platforms ({api_coverage:.1%}) - most data requires manual entry",
            "action": "Prioritize API integration development (see APU-44 roadmap)",
            "category": "infrastructure"
        })

    return alerts


def create_apu44_dashboard() -> str:
    """Generate APU-44 enhanced dashboard with clear separation of issues."""
    agents = get_real_time_agent_status()
    metrics = analyze_platform_performance()
    alerts = generate_apu44_intelligent_alerts(agents, metrics)

    dashboard = []
    dashboard.append("=" * 75)
    dashboard.append("[*] APU-44 ENHANCED ENGAGEMENT MONITOR")
    dashboard.append(f"[DATE] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    dashboard.append("=" * 75)

    # Agent Health Section (unchanged)
    dashboard.append("\n[AGENTS] REAL-TIME AGENT STATUS:")
    for agent_name, agent_data in agents.items():
        status_emoji = {
            "healthy": "[HEALTHY]",
            "idle": "[IDLE]",
            "warning": "[WARN]",
            "failed": "[FAILED]",
            "unknown": "[UNKNOWN]"
        }.get(agent_data["status"], "[?]")

        dashboard.append(f"  {status_emoji} {agent_name.replace('engagement', 'Engagement').replace('agent', 'Agent').replace('bot', 'Bot')}:")
        dashboard.append(f"     Status: {agent_data['status_description']}")
        dashboard.append(f"     Last Activity: {agent_data['last_activity'] or 'None'}")
        dashboard.append(f"     Success Rate: {agent_data['success_rate']:.1%}")

    # APU-44 Enhanced Platform Section with API Status
    dashboard.append(f"\n[PLATFORMS] API INTEGRATION & PERFORMANCE:")
    dashboard.append(f"  API Coverage: {metrics.get('api_coverage_rate', 0):.1%} | API Posts: {metrics.get('api_posts', 0)}/{metrics['total_posts']}")
    if metrics.get('top_performer'):
        dashboard.append(f"  Top Performer (API Data): {metrics['top_performer'].upper()}")

    for platform, stats in metrics["platform_stats"].items():
        # APU-44: Enhanced status indicators
        if stats["api_availability_rate"] >= 0.8:
            api_indicator = "[API-READY]"
        elif stats["api_availability_rate"] > 0:
            api_indicator = f"[API-PARTIAL {stats['api_availability_rate']:.0%}]"
        else:
            api_indicator = "[NO-API]"

        perf_indicator = {
            "excellent": "[FIRE]", "good": "[GOOD]", "moderate": "[WARN]",
            "low": "[LOW]", "none": "[ZERO]", "no_api_data": "[NO-DATA]", "no_data": "[NONE]"
        }.get(stats["performance"], "[UNKNOWN]")

        dashboard.append(f"  {perf_indicator} {platform.upper()}: {stats['avg_engagement']:.1f} avg | {stats['api_posts']}/{stats['posts']} posts | {api_indicator}")

    # Comment Section (unchanged)
    dashboard.append(f"\n[COMMENTS] PROCESSING STATUS:")
    comment_status = metrics["comment_stats"]
    api_status_msg = {
        "unavailable_404": "API Unavailable (404) - Normal for new deployment",
        "available_no_comments": "API Available - No comments to process",
        "available": "API Available - Processing comments",
        "unknown": "Status Unknown"
    }.get(comment_status["api_status"], "Unknown")

    dashboard.append(f"  API Status: {api_status_msg}")
    dashboard.append(f"  Comments Seen: {comment_status['total_comments_seen']}")
    dashboard.append(f"  Replies Sent: {comment_status['replies_sent']}")

    # APU-44 Enhanced Alerts Section with Categories
    alerts_by_category = {"infrastructure": [], "community": [], "technical": []}
    for alert in alerts:
        category = alert.get("category", "technical")
        alerts_by_category[category].append(alert)

    total_alerts = len(alerts)
    dashboard.append(f"\n[ALERTS] CATEGORIZED ALERTS ({total_alerts}):")

    for category, category_alerts in alerts_by_category.items():
        if category_alerts:
            dashboard.append(f"  {category.upper()} ({len(category_alerts)}):")
            for alert in category_alerts:
                severity_emoji = {"high": "[HIGH]", "medium": "[WARN]", "low": "[INFO]"}.get(alert["severity"], "[ALERT]")
                dashboard.append(f"    {severity_emoji} {alert['message']}")
                if "action" in alert:
                    dashboard.append(f"        Action: {alert['action']}")
        else:
            dashboard.append(f"  {category.upper()} (0): [OK] No {category} issues")

    # APU-44 System Health Summary
    infrastructure_alerts = len(alerts_by_category["infrastructure"])
    community_alerts = len(alerts_by_category["community"])
    technical_alerts = len(alerts_by_category["technical"])

    healthy_agents = sum(1 for a in agents.values() if a["status"] in ["healthy", "idle"])
    total_agents = len(agents)

    dashboard.append(f"\n[SUMMARY] APU-44 SYSTEM HEALTH:")
    dashboard.append(f"  Agents: {healthy_agents}/{total_agents} healthy/idle")
    dashboard.append(f"  Infrastructure: {infrastructure_alerts} alerts | Community: {community_alerts} alerts | Technical: {technical_alerts} alerts")
    dashboard.append(f"  Overall Status: {'[OPERATIONAL]' if infrastructure_alerts == 0 and technical_alerts == 0 else '[NEEDS ATTENTION]'}")

    dashboard.append("\n" + "=" * 75)

    return "\n".join(dashboard)


def save_apu44_monitor_report():
    """Save APU-44 enhanced monitoring data with detailed analytics."""
    agents = get_real_time_agent_status()
    metrics = analyze_platform_performance()
    alerts = generate_apu44_intelligent_alerts(agents, metrics)

    # Categorize alerts for summary
    alerts_by_category = {"infrastructure": [], "community": [], "technical": []}
    for alert in alerts:
        category = alert.get("category", "technical")
        alerts_by_category[category].append(alert)

    report = {
        "timestamp": datetime.now().isoformat(),
        "version": "apu44_enhanced_v1",
        "agents": agents,
        "metrics": metrics,
        "alerts": alerts,
        "alerts_by_category": alerts_by_category,
        "summary": {
            "healthy_agents": sum(1 for a in agents.values() if a["status"] in ["healthy", "idle"]),
            "total_agents": len(agents),
            "total_alerts": len(alerts),
            "infrastructure_alerts": len(alerts_by_category["infrastructure"]),
            "community_alerts": len(alerts_by_category["community"]),
            "technical_alerts": len(alerts_by_category["technical"]),
            "system_status": "operational" if len(alerts_by_category["infrastructure"]) == 0 and len(alerts_by_category["technical"]) == 0 else "needs_attention",
            "api_coverage": metrics.get("api_coverage_rate", 0),
            "top_platform": metrics.get("top_performer", "none"),
            "overall_health_score": sum(a["health_score"] for a in agents.values()) / len(agents) if agents else 0
        }
    }

    # Load existing monitor log
    monitor_log = load_json(MONITOR_LOG)
    today = today_str()

    if today not in monitor_log:
        monitor_log[today] = []

    monitor_log[today].append(report)

    # Keep only last 30 days
    cutoff_date = (datetime.now() - timedelta(days=30)).date()
    monitor_log = {k: v for k, v in monitor_log.items() if datetime.fromisoformat(k + "T00:00:00").date() >= cutoff_date}

    save_json(MONITOR_LOG, monitor_log)
    return report


def main():
    """APU-44 Enhanced main monitoring function."""
    print("\n[*] APU-44 Enhanced Engagement Monitor Starting...\n")

    # Generate and display enhanced dashboard
    dashboard = create_apu44_dashboard()
    print(dashboard)

    # Save enhanced monitoring report
    report = save_apu44_monitor_report()

    # Log enhanced summary
    summary = report["summary"]
    log_run(
        "APU44EngagementMonitor",
        "ok" if summary["system_status"] == "operational" else "warning",
        f"APU-44: {summary['healthy_agents']}/{summary['total_agents']} agents healthy, "
        f"API coverage {summary['api_coverage']:.1%}, "
        f"alerts: {summary['infrastructure_alerts']} infra, {summary['community_alerts']} community, {summary['technical_alerts']} tech"
    )

    print(f"\n[SAVE] APU-44 monitoring report saved")
    print(f"[API] Coverage: {summary['api_coverage']:.1%}")
    print(f"[SCORE] System Health Score: {summary['overall_health_score']:.2f}/1.0")

    return report["alerts"]


if __name__ == "__main__":
    alerts = main()

    # APU-44 Enhanced exit logic - separate infrastructure from operational issues
    high_priority = [a for a in alerts if a["severity"] == "high"]
    infrastructure_issues = [a for a in alerts if a.get("category") == "infrastructure"]

    if high_priority:
        print(f"\n[ALERT] {len(high_priority)} HIGH PRIORITY ALERTS REQUIRE ATTENTION")
        if infrastructure_issues:
            print(f"[INFO] {len(infrastructure_issues)} alerts are infrastructure issues (not operational failures)")
        exit(1)
    else:
        print(f"\n[OK] APU-44 monitoring complete - {len(alerts)} total alerts")
        if infrastructure_issues:
            print(f"[INFO] {len(infrastructure_issues)} infrastructure improvements available")
        exit(0)