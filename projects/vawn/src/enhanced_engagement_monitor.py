"""
enhanced_engagement_monitor.py — Enhanced monitoring system for Vawn's engagement.
Fixes APU-33 issues: proper agent health detection, accurate status reporting,
and intelligent alerting that distinguishes failure vs. no-work-available.

Created by: Dex - Community Agent (APU-33)
Enhancements over original: Real-time agent status, accurate health detection,
better alerting logic, and comprehensive dashboard improvements.
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
MONITOR_LOG = VAWN_DIR / "research" / "enhanced_engagement_monitor_log.json"
ALERT_THRESHOLD = {
    "no_activity_days": 2,  # Alert if no successful runs for 2+ days
    "low_engagement_rate": 0.05,  # Alert if engagement rate drops below 5%
    "actual_failure_hours": 6,  # Alert only if agents actually fail for 6+ hours
    "consecutive_failures": 3,  # Alert if 3+ consecutive failures
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
    Enhanced agent health check that looks at recent activity patterns,
    not just timestamps. Fixes APU-33 core issue.
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
    """Enhanced platform analysis with API availability tracking."""
    metrics_log = load_json(METRICS_LOG)
    engagement_log = load_json(ENGAGEMENT_LOG)

    platform_stats = {}
    total_posts = 0
    total_engagement = 0

    # Analyze platform metrics
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
                        "last_activity": None
                    }

                platform_stats[platform]["posts"] += 1
                platform_stats[platform]["last_activity"] = date

                if isinstance(data, dict):
                    platform_stats[platform]["total_likes"] += data.get("likes", 0)
                    platform_stats[platform]["total_comments"] += data.get("comments", 0)
                    platform_stats[platform]["total_saves"] += data.get("saves", 0) + data.get("reposts", 0)
                    platform_stats[platform]["api_status"] = "available"
                    total_engagement += data.get("likes", 0) + data.get("comments", 0)
                else:
                    platform_stats[platform]["api_status"] = "manual_entry_needed"

    # Calculate performance metrics
    for platform in platform_stats:
        stats = platform_stats[platform]
        if stats["posts"] > 0:
            stats["avg_engagement"] = (stats["total_likes"] + stats["total_comments"]) / stats["posts"]
            stats["engagement_rate"] = stats["avg_engagement"] / max(stats["posts"], 1)

            # Performance classification
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
            stats["avg_engagement"] = 0
            stats["engagement_rate"] = 0
            stats["performance"] = "no_data"

    # Comment processing analysis
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
        "overall_engagement_rate": total_engagement / max(total_posts, 1),
        "total_posts": total_posts,
        "top_performer": max(platform_stats.keys(), key=lambda p: platform_stats[p]["avg_engagement"]) if platform_stats else None
    }


def generate_intelligent_alerts(agents: Dict, metrics: Dict) -> List[Dict[str, str]]:
    """
    Enhanced alert generation that distinguishes between real problems
    and normal operational states. Fixes APU-33 false positive alerts.
    """
    alerts = []

    # Agent health alerts (enhanced logic)
    for agent_name, agent_data in agents.items():
        if agent_data["status"] == "failed":
            alerts.append({
                "type": "agent_failure",
                "severity": "high",
                "message": f"{agent_name} has failed consistently (success rate: {agent_data['success_rate']:.1%})",
                "agent": agent_name,
                "action": "Check agent logs and restart if needed"
            })
        elif agent_data["status"] == "warning":
            alerts.append({
                "type": "agent_degraded",
                "severity": "medium",
                "message": f"{agent_name} has intermittent issues (success rate: {agent_data['success_rate']:.1%})",
                "agent": agent_name,
                "action": "Monitor for patterns and investigate if continues"
            })
        elif agent_data["status"] == "unknown":
            alerts.append({
                "type": "agent_unknown",
                "severity": "medium",
                "message": f"{agent_name} status unknown - no recent activity",
                "agent": agent_name,
                "action": "Check if agent is scheduled and running"
            })
        # Note: "idle" and "healthy" agents do not generate alerts

    # Platform performance alerts
    top_performer = metrics.get("top_performer", "")
    platform_issues = []
    for platform, stats in metrics["platform_stats"].items():
        if stats["performance"] == "none" and stats["posts"] > 5:
            platform_issues.append(platform)

    if len(platform_issues) > 2:
        alerts.append({
            "type": "platform_performance",
            "severity": "medium",
            "message": f"Multiple platforms showing zero engagement: {', '.join(platform_issues)}",
            "platforms": platform_issues,
            "action": "Check API connections and engagement strategies"
        })

    # Comment processing alerts (enhanced)
    comment_stats = metrics["comment_stats"]
    if comment_stats["api_status"] == "unavailable_404":
        alerts.append({
            "type": "comment_api_unavailable",
            "severity": "low",
            "message": "Comment API endpoint returning 404 - feature may not be deployed yet",
            "action": "Check with backend team about comment API availability"
        })
    elif comment_stats["api_status"] == "available_no_comments":
        # This is normal - no alert needed
        pass
    elif not comment_stats["recent_activity"] and comment_stats["total_comments_seen"] > 0:
        alerts.append({
            "type": "comment_processing_stalled",
            "severity": "medium",
            "message": "Comment processing appears stalled despite available comments",
            "action": "Check engagement agent functionality"
        })

    # Overall engagement health
    if metrics["overall_engagement_rate"] < ALERT_THRESHOLD["low_engagement_rate"]:
        alerts.append({
            "type": "low_overall_engagement",
            "severity": "low",
            "message": f"Overall engagement rate is {metrics['overall_engagement_rate']:.1%} (below {ALERT_THRESHOLD['low_engagement_rate']:.1%})",
            "action": "Review content strategy and hashtag performance"
        })

    return alerts


def create_enhanced_dashboard() -> str:
    """Generate enhanced dashboard with clearer status indicators."""
    agents = get_real_time_agent_status()
    metrics = analyze_platform_performance()
    alerts = generate_intelligent_alerts(agents, metrics)

    dashboard = []
    dashboard.append("=" * 70)
    dashboard.append("[*] ENHANCED VAWN ENGAGEMENT MONITOR (APU-33)")
    dashboard.append(f"[DATE] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    dashboard.append("=" * 70)

    # Enhanced Agent Health Section
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
        dashboard.append(f"     24h Runs: {agent_data['runs_24h']}")
        dashboard.append(f"     Success Rate: {agent_data['success_rate']:.1%}")
        if agent_data['comments_processed'] > 0:
            dashboard.append(f"     Comments Processed: {agent_data['comments_processed']}")
        if agent_data['engagement_actions'] > 0:
            dashboard.append(f"     Engagement Actions: {agent_data['engagement_actions']}")

    # Enhanced Platform Section
    dashboard.append(f"\n[PLATFORMS] PERFORMANCE ANALYSIS:")
    dashboard.append(f"  Overall Rate: {metrics['overall_engagement_rate']:.2%} | Total Posts: {metrics['total_posts']}")
    if metrics['top_performer']:
        dashboard.append(f"  Top Performer: {metrics['top_performer'].upper()}")

    for platform, stats in metrics["platform_stats"].items():
        perf_indicator = {
            "excellent": "[FIRE]", "good": "[GOOD]", "moderate": "[WARN]",
            "low": "[LOW]", "none": "[NONE]", "no_data": "[NO_DATA]"
        }.get(stats["performance"], "[UNKNOWN]")

        api_indicator = "[API]" if stats["api_status"] == "available" else "[Manual]"
        dashboard.append(f"  {perf_indicator} {platform.upper()}: {stats['avg_engagement']:.1f} avg | {stats['posts']} posts | {api_indicator}")

    # Enhanced Comment Section
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
    if comment_status['total_comments_seen'] > 0:
        dashboard.append(f"  Response Rate: {comment_status['response_rate']:.1%}")

    # Enhanced Alerts Section
    alert_count = len(alerts)
    high_alerts = len([a for a in alerts if a["severity"] == "high"])

    dashboard.append(f"\n[ALERTS] INTELLIGENT ALERTS ({alert_count}):")
    if alerts:
        for alert in alerts:
            severity_emoji = {"high": "[HIGH]", "medium": "[WARN]", "low": "[INFO]"}.get(alert["severity"], "[ALERT]")
            dashboard.append(f"  {severity_emoji} {alert['message']}")
            if "action" in alert:
                dashboard.append(f"      Action: {alert['action']}")
    else:
        dashboard.append("  [OK] All systems operating normally")

    # System Health Summary
    healthy_agents = sum(1 for a in agents.values() if a["status"] in ["healthy", "idle"])
    total_agents = len(agents)

    dashboard.append(f"\n[SUMMARY] SYSTEM HEALTH:")
    dashboard.append(f"  Agents: {healthy_agents}/{total_agents} healthy/idle | High Alerts: {high_alerts}")
    dashboard.append(f"  Status: {'[OPERATIONAL]' if high_alerts == 0 else '[ISSUES_DETECTED]'}")

    dashboard.append("\n" + "=" * 70)

    return "\n".join(dashboard)


def save_enhanced_monitor_report():
    """Save enhanced monitoring data with detailed analytics."""
    agents = get_real_time_agent_status()
    metrics = analyze_platform_performance()
    alerts = generate_intelligent_alerts(agents, metrics)

    report = {
        "timestamp": datetime.now().isoformat(),
        "version": "enhanced_v1_apu33",
        "agents": agents,
        "metrics": metrics,
        "alerts": alerts,
        "summary": {
            "healthy_agents": sum(1 for a in agents.values() if a["status"] in ["healthy", "idle"]),
            "total_agents": len(agents),
            "total_alerts": len(alerts),
            "high_priority_alerts": len([a for a in alerts if a["severity"] == "high"]),
            "system_status": "operational" if len([a for a in alerts if a["severity"] == "high"]) == 0 else "issues_detected",
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
    """Enhanced main monitoring function for APU-33."""
    print("\n[*] Enhanced Engagement Monitor (APU-33) Starting...\n")

    # Generate and display enhanced dashboard
    dashboard = create_enhanced_dashboard()
    print(dashboard)

    # Save enhanced monitoring report
    report = save_enhanced_monitor_report()

    # Log enhanced summary
    summary = report["summary"]
    log_run(
        "EnhancedEngagementMonitor",
        "ok" if summary["system_status"] == "operational" else "warning",
        f"APU-33: {summary['healthy_agents']}/{summary['total_agents']} agents healthy, "
        f"{summary['total_alerts']} alerts, health score {summary['overall_health_score']:.2f}"
    )

    print(f"\n[SAVE] Enhanced monitoring report saved")
    print(f"[SCORE] System Health Score: {summary['overall_health_score']:.2f}/1.0")

    return report["alerts"]


if __name__ == "__main__":
    alerts = main()

    # Enhanced exit logic - only exit with error for real failures
    high_priority = [a for a in alerts if a["severity"] == "high"]
    if high_priority:
        print(f"\n[ALERT] {len(high_priority)} HIGH PRIORITY ALERTS REQUIRE ATTENTION")
        exit(1)
    else:
        print(f"\n[OK] Enhanced monitoring complete - {len(alerts)} total alerts (normal operation)")
        exit(0)