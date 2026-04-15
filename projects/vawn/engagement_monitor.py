"""
engagement_monitor.py — Comprehensive monitoring system for Vawn's cross-platform engagement.
Tracks health of engagement agents, provides dashboard, and alerts for issues.
Created by: Dex - Community Agent (APU-23)
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
MONITOR_LOG = VAWN_DIR / "research" / "engagement_monitor_log.json"
ALERT_THRESHOLD = {
    "no_comments_days": 3,  # Alert if no comments processed for 3+ days
    "low_engagement_rate": 0.05,  # Alert if engagement rate drops below 5%
    "agent_failure_hours": 4,  # Alert if agents haven't run in 4+ hours
}

PLATFORMS = ["instagram", "tiktok", "x", "threads", "bluesky"]


def initialize_engagement_log():
    """Initialize the missing engagement_log.json that engagement_agent.py expects."""
    if not Path(ENGAGEMENT_LOG).exists():
        initial_data = {
            "replied_ids": [],
            "history": [],
            "last_updated": datetime.now().isoformat(),
            "initialized_by": "engagement_monitor",
            "stats": {
                "total_comments_processed": 0,
                "total_replies_sent": 0,
                "spam_filtered": 0,
                "reply_success_rate": 0.0
            }
        }
        save_json(ENGAGEMENT_LOG, initial_data)
        print(f"[INIT] Created missing {ENGAGEMENT_LOG}")
        return True
    return False


def check_agent_health() -> Dict[str, Any]:
    """Check if engagement agents are running and healthy."""
    research_log = load_json(RESEARCH_LOG)
    today = today_str()
    yesterday = str((datetime.now() - timedelta(days=1)).date())

    # Find recent EngagementAgent and EngagementBot entries
    engagement_runs = []
    bot_runs = []

    for date in [today, yesterday]:
        if date in research_log:
            for entry in research_log[date]:
                if entry["agent"] == "EngagementAgent":
                    engagement_runs.append(entry)
                elif entry["agent"] == "EngagementBot":
                    bot_runs.append(entry)

    # Analyze health
    health = {
        "engagement_agent": {
            "last_run": None,
            "runs_today": 0,
            "recent_errors": 0,
            "comments_processed": 0,
            "status": "unknown"
        },
        "engagement_bot": {
            "last_run": None,
            "runs_today": 0,
            "recent_errors": 0,
            "status": "unknown"
        }
    }

    # Analyze EngagementAgent
    if engagement_runs:
        health["engagement_agent"]["last_run"] = engagement_runs[-1]["time"]
        health["engagement_agent"]["runs_today"] = len([r for r in engagement_runs if r["time"].startswith(today)])
        health["engagement_agent"]["recent_errors"] = len([r for r in engagement_runs if r["status"] == "error"])

        # Extract comments processed from details
        for run in engagement_runs:
            if "replies generated" in run["detail"]:
                try:
                    count = int(run["detail"].split()[0])
                    health["engagement_agent"]["comments_processed"] += count
                except:
                    pass

        # Determine status
        last_run_time = datetime.fromisoformat(health["engagement_agent"]["last_run"])
        hours_since = (datetime.now() - last_run_time).total_seconds() / 3600

        if hours_since > ALERT_THRESHOLD["agent_failure_hours"]:
            health["engagement_agent"]["status"] = "stale"
        elif health["engagement_agent"]["recent_errors"] > 0:
            health["engagement_agent"]["status"] = "error"
        else:
            health["engagement_agent"]["status"] = "healthy"

    # Analyze EngagementBot
    if bot_runs:
        health["engagement_bot"]["last_run"] = bot_runs[-1]["time"]
        health["engagement_bot"]["runs_today"] = len([r for r in bot_runs if r["time"].startswith(today)])
        health["engagement_bot"]["recent_errors"] = len([r for r in bot_runs if r["status"] == "error"])

        # Determine status
        last_run_time = datetime.fromisoformat(health["engagement_bot"]["last_run"])
        hours_since = (datetime.now() - last_run_time).total_seconds() / 3600

        if hours_since > ALERT_THRESHOLD["agent_failure_hours"]:
            health["engagement_bot"]["status"] = "stale"
        elif health["engagement_bot"]["recent_errors"] > 0:
            health["engagement_bot"]["status"] = "error"
        else:
            health["engagement_bot"]["status"] = "healthy"

    return health


def analyze_engagement_metrics() -> Dict[str, Any]:
    """Analyze engagement metrics across all platforms."""
    metrics_log = load_json(METRICS_LOG)
    engagement_log = load_json(ENGAGEMENT_LOG)

    # Calculate platform engagement rates
    platform_stats = {}
    total_posts = 0
    total_engagement = 0

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
                        "api_available": True
                    }

                platform_stats[platform]["posts"] += 1

                if isinstance(data, dict):
                    platform_stats[platform]["total_likes"] += data.get("likes", 0)
                    platform_stats[platform]["total_comments"] += data.get("comments", 0)
                    platform_stats[platform]["total_saves"] += data.get("saves", 0) + data.get("reposts", 0)
                    total_engagement += data.get("likes", 0) + data.get("comments", 0)
                else:
                    # Manual entry needed - mark as unavailable
                    platform_stats[platform]["api_available"] = False

    # Calculate engagement rates
    for platform in platform_stats:
        stats = platform_stats[platform]
        if stats["posts"] > 0:
            stats["avg_engagement"] = (stats["total_likes"] + stats["total_comments"]) / stats["posts"]
            stats["engagement_rate"] = stats["avg_engagement"] / max(stats["posts"], 1)
        else:
            stats["avg_engagement"] = 0
            stats["engagement_rate"] = 0

    # Analyze comment responses
    comment_stats = {
        "total_comments_seen": len(engagement_log.get("replied_ids", [])),
        "replies_sent": len(engagement_log.get("history", [])),
        "response_rate": 0.0,
        "recent_activity": False
    }

    if comment_stats["total_comments_seen"] > 0:
        comment_stats["response_rate"] = comment_stats["replies_sent"] / comment_stats["total_comments_seen"]

    # Check for recent activity (last 24 hours)
    recent_history = [
        h for h in engagement_log.get("history", [])
        if datetime.fromisoformat(h["date"]) > datetime.now() - timedelta(days=1)
    ]
    comment_stats["recent_activity"] = len(recent_history) > 0

    return {
        "platform_stats": platform_stats,
        "comment_stats": comment_stats,
        "overall_engagement_rate": total_engagement / max(total_posts, 1),
        "total_posts": total_posts
    }


def generate_alerts() -> List[Dict[str, str]]:
    """Generate alerts based on current system health."""
    alerts = []
    health = check_agent_health()
    metrics = analyze_engagement_metrics()

    # Agent health alerts
    for agent_name, agent_health in health.items():
        if agent_health["status"] == "stale":
            alerts.append({
                "type": "agent_stale",
                "severity": "high",
                "message": f"{agent_name} hasn't run in {ALERT_THRESHOLD['agent_failure_hours']}+ hours",
                "agent": agent_name
            })
        elif agent_health["status"] == "error":
            alerts.append({
                "type": "agent_error",
                "severity": "medium",
                "message": f"{agent_name} has recent errors",
                "agent": agent_name
            })

    # Engagement rate alerts
    if metrics["overall_engagement_rate"] < ALERT_THRESHOLD["low_engagement_rate"]:
        alerts.append({
            "type": "low_engagement",
            "severity": "medium",
            "message": f"Overall engagement rate dropped to {metrics['overall_engagement_rate']:.2%}",
            "value": metrics["overall_engagement_rate"]
        })

    # Comment processing alerts
    if not metrics["comment_stats"]["recent_activity"]:
        alerts.append({
            "type": "no_comments",
            "severity": "low",
            "message": "No comments processed in the last 24 hours",
            "suggestion": "Check if comment API endpoints are working"
        })

    return alerts


def create_dashboard() -> str:
    """Generate a text dashboard of engagement status."""
    health = check_agent_health()
    metrics = analyze_engagement_metrics()
    alerts = generate_alerts()

    dashboard = []
    dashboard.append("=" * 60)
    dashboard.append("[*] VAWN ENGAGEMENT MONITOR DASHBOARD")
    dashboard.append(f"[DATE] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    dashboard.append("=" * 60)

    # Agent Health Section
    dashboard.append("\n[AGENTS] AGENT HEALTH:")
    for agent_name, agent_health in health.items():
        status_emoji = {
            "healthy": "[OK]",
            "stale": "[WARN]",
            "error": "[ERROR]",
            "unknown": "[?]"
        }.get(agent_health["status"], "[?]")

        dashboard.append(f"  {status_emoji} {agent_name}:")
        dashboard.append(f"     Last run: {agent_health['last_run'] or 'Never'}")
        dashboard.append(f"     Runs today: {agent_health['runs_today']}")
        dashboard.append(f"     Status: {agent_health['status'].upper()}")

    # Platform Stats Section
    dashboard.append(f"\n[METRICS] PLATFORM ENGAGEMENT:")
    dashboard.append(f"  Overall Rate: {metrics['overall_engagement_rate']:.2%}")
    dashboard.append(f"  Total Posts: {metrics['total_posts']}")

    for platform, stats in metrics["platform_stats"].items():
        api_status = "[API]" if stats["api_available"] else "[Manual]"
        dashboard.append(f"  • {platform.upper()}: {stats['avg_engagement']:.1f} avg | {api_status}")

    # Comment Stats Section
    dashboard.append(f"\n[COMMENTS] COMMENT MONITORING:")
    dashboard.append(f"  Comments Seen: {metrics['comment_stats']['total_comments_seen']}")
    dashboard.append(f"  Replies Sent: {metrics['comment_stats']['replies_sent']}")
    dashboard.append(f"  Response Rate: {metrics['comment_stats']['response_rate']:.1%}")
    dashboard.append(f"  Recent Activity: {'[YES]' if metrics['comment_stats']['recent_activity'] else '[NO]'}")

    # Alerts Section
    dashboard.append(f"\n[ALERTS] ALERTS ({len(alerts)}):")
    if alerts:
        for alert in alerts:
            severity_emoji = {"high": "[HIGH]", "medium": "[MED]", "low": "[LOW]"}.get(alert["severity"], "[INFO]")
            dashboard.append(f"  {severity_emoji} {alert['message']}")
    else:
        dashboard.append("  [OK] All systems normal")

    dashboard.append("\n" + "=" * 60)

    return "\n".join(dashboard)


def save_monitor_report():
    """Save monitoring data to log file."""
    health = check_agent_health()
    metrics = analyze_engagement_metrics()
    alerts = generate_alerts()

    report = {
        "timestamp": datetime.now().isoformat(),
        "health": health,
        "metrics": metrics,
        "alerts": alerts,
        "summary": {
            "agents_healthy": sum(1 for h in health.values() if h["status"] == "healthy"),
            "total_alerts": len(alerts),
            "high_priority_alerts": len([a for a in alerts if a["severity"] == "high"])
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
    """Main monitoring function."""
    print("\n[*] Vawn Engagement Monitor Starting...")

    # Initialize missing files
    initialized = initialize_engagement_log()
    if initialized:
        log_run("EngagementMonitor", "info", "Initialized missing engagement_log.json")

    # Generate and display dashboard
    dashboard = create_dashboard()
    print(dashboard)

    # Save monitoring report
    report = save_monitor_report()

    # Log summary
    summary = report["summary"]
    log_run(
        "EngagementMonitor",
        "ok" if summary["high_priority_alerts"] == 0 else "warning",
        f"{summary['agents_healthy']}/2 agents healthy, {summary['total_alerts']} alerts"
    )

    # Return alerts for potential notification system
    return report["alerts"]


if __name__ == "__main__":
    alerts = main()

    # If there are high-priority alerts, exit with error code
    high_priority = [a for a in alerts if a["severity"] == "high"]
    if high_priority:
        print(f"\n[WARNING] {len(high_priority)} HIGH PRIORITY ALERTS FOUND!")
        sys.exit(1)
    else:
        print(f"\n[OK] Monitoring complete - {len(alerts)} total alerts")
        sys.exit(0)