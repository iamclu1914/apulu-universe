"""
engagement_monitor_apu37.py — Enhanced monitoring system for APU-37 resolution.
Comprehensive monitoring with API health visibility and improved alerting.
Created by: Dex - Community Agent (APU-37)
"""

import json
import sys
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import (
    load_json, save_json, ENGAGEMENT_LOG, RESEARCH_LOG, METRICS_LOG,
    VAWN_DIR, log_run, today_str, get_anthropic_client, CREDS_FILE
)

# Configuration
MONITOR_LOG = VAWN_DIR / "research" / "apu37_engagement_monitor_log.json"
API_HEALTH_LOG = VAWN_DIR / "research" / "api_health_log.json"
BASE_URL = "https://apulustudio.onrender.com/api"

ALERT_THRESHOLD = {
    "no_comments_days": 3,
    "low_engagement_rate": 0.05,
    "agent_failure_hours": 4,
    "api_response_time_ms": 5000,  # Alert if API response > 5 seconds
    "api_downtime_minutes": 30,    # Alert if API down for 30+ minutes
}

PLATFORMS = ["instagram", "tiktok", "x", "threads", "bluesky"]


def check_api_health() -> Dict[str, Any]:
    """Check current API health status."""
    try:
        creds = load_json(CREDS_FILE)
        headers = {"Authorization": f"Bearer {creds['access_token']}"}
        start_time = datetime.now()

        r = requests.get(f"{BASE_URL}/posts/comments", headers=headers, timeout=10)
        response_time = (datetime.now() - start_time).total_seconds() * 1000

        return {
            "available": r.status_code != 404,
            "status_code": r.status_code,
            "response_time_ms": int(response_time),
            "timestamp": datetime.now().isoformat(),
            "healthy": r.status_code != 404 and response_time < ALERT_THRESHOLD["api_response_time_ms"]
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e),
            "response_time_ms": 0,
            "timestamp": datetime.now().isoformat(),
            "healthy": False
        }


def get_api_health_history() -> List[Dict[str, Any]]:
    """Get recent API health history."""
    health_log = load_json(API_HEALTH_LOG) if Path(API_HEALTH_LOG).exists() else {}
    recent_entries = []

    # Get last 24 hours of data
    cutoff = datetime.now() - timedelta(hours=24)

    for date, entries in health_log.items():
        for entry in entries:
            entry_time = datetime.fromisoformat(entry["timestamp"])
            if entry_time >= cutoff:
                recent_entries.append(entry)

    # Sort by timestamp
    recent_entries.sort(key=lambda x: x["timestamp"])
    return recent_entries


def analyze_api_status() -> Dict[str, Any]:
    """Analyze API status and health trends."""
    current_health = check_api_health()
    history = get_api_health_history()

    if not history:
        return {
            "current": current_health,
            "availability_24h": 0.0,
            "avg_response_time_24h": 0.0,
            "downtime_incidents": 0,
            "status": "no_history"
        }

    # Calculate availability over last 24 hours
    available_count = sum(1 for h in history if h.get("available", False))
    availability_24h = (available_count / len(history)) * 100

    # Calculate average response time (only for successful calls)
    successful_calls = [h for h in history if h.get("available", False) and h.get("response_time_ms", 0) > 0]
    avg_response_time = sum(h["response_time_ms"] for h in successful_calls) / len(successful_calls) if successful_calls else 0

    # Count downtime incidents (consecutive unavailable periods)
    downtime_incidents = 0
    in_downtime = False

    for entry in history:
        if not entry.get("available", False):
            if not in_downtime:
                downtime_incidents += 1
                in_downtime = True
        else:
            in_downtime = False

    # Determine overall status
    if not current_health["available"]:
        status = "down"
    elif availability_24h < 90:
        status = "unstable"
    elif avg_response_time > ALERT_THRESHOLD["api_response_time_ms"]:
        status = "slow"
    else:
        status = "healthy"

    return {
        "current": current_health,
        "availability_24h": availability_24h,
        "avg_response_time_24h": int(avg_response_time),
        "downtime_incidents": downtime_incidents,
        "status": status,
        "total_checks_24h": len(history)
    }


def initialize_engagement_log():
    """Initialize the missing engagement_log.json that engagement_agent.py expects."""
    if not Path(ENGAGEMENT_LOG).exists():
        initial_data = {
            "replied_ids": [],
            "history": [],
            "last_updated": datetime.now().isoformat(),
            "initialized_by": "engagement_monitor_apu37",
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

    # Find recent agent entries
    agent_runs = {
        "EngagementAgent": [],
        "EngagementAgentEnhanced": [],
        "EngagementBot": []
    }

    for date in [today, yesterday]:
        if date in research_log:
            for entry in research_log[date]:
                agent_name = entry["agent"]
                if agent_name in agent_runs:
                    agent_runs[agent_name].append(entry)

    # Analyze health for each agent type
    health = {}

    for agent_name, runs in agent_runs.items():
        if not runs:
            health[agent_name.lower()] = {
                "last_run": None,
                "runs_today": 0,
                "recent_errors": 0,
                "status": "never_run"
            }
            continue

        # Get the most recent run
        latest_run = max(runs, key=lambda x: x["time"])
        runs_today = len([r for r in runs if r["time"].startswith(today)])
        recent_errors = len([r for r in runs if r["status"] in ["error", "warning"]])

        # Determine status
        last_run_time = datetime.fromisoformat(latest_run["time"])
        hours_since = (datetime.now() - last_run_time).total_seconds() / 3600

        if hours_since > ALERT_THRESHOLD["agent_failure_hours"]:
            status = "stale"
        elif recent_errors > runs_today // 2:  # More than half the runs had errors
            status = "error_prone"
        elif latest_run["status"] == "error":
            status = "last_run_failed"
        else:
            status = "healthy"

        health[agent_name.lower()] = {
            "last_run": latest_run["time"],
            "runs_today": runs_today,
            "recent_errors": recent_errors,
            "status": status,
            "last_detail": latest_run.get("detail", "")
        }

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

    # Analyze comment responses (enhanced with API awareness)
    comment_stats = {
        "total_comments_seen": len(engagement_log.get("replied_ids", [])),
        "replies_sent": len(engagement_log.get("history", [])),
        "response_rate": 0.0,
        "recent_activity": False,
        "api_dependent": True  # Comments depend on API availability
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
    api_status = analyze_api_status()

    # API Health Alerts (NEW - Critical for APU-37)
    if api_status["status"] == "down":
        alerts.append({
            "type": "api_down",
            "severity": "critical",
            "message": f"Comments API is unavailable (HTTP {api_status['current'].get('status_code', 'unknown')})",
            "detail": "Comment processing cannot function",
            "action": "Check backend API deployment"
        })
    elif api_status["status"] == "slow":
        alerts.append({
            "type": "api_slow",
            "severity": "medium",
            "message": f"API response time is slow ({api_status['avg_response_time_24h']}ms avg)",
            "detail": "May affect agent performance",
            "action": "Monitor API performance"
        })
    elif api_status["availability_24h"] < 90:
        alerts.append({
            "type": "api_unstable",
            "severity": "high",
            "message": f"API availability is {api_status['availability_24h']:.1f}% (last 24h)",
            "detail": f"{api_status['downtime_incidents']} downtime incidents",
            "action": "Investigate API stability"
        })

    # Agent health alerts (enhanced with API context)
    for agent_name, agent_health in health.items():
        if agent_health["status"] == "stale":
            # Check if staleness might be due to API issues
            if api_status["status"] == "down":
                severity = "low"  # Reduce severity if API is known to be down
                message = f"{agent_name} appears stale but API is down"
            else:
                severity = "high"
                message = f"{agent_name} hasn't run in {ALERT_THRESHOLD['agent_failure_hours']}+ hours"

            alerts.append({
                "type": "agent_stale",
                "severity": severity,
                "message": message,
                "agent": agent_name,
                "action": "Check agent scheduler" if api_status["status"] != "down" else "Wait for API recovery"
            })
        elif agent_health["status"] in ["error_prone", "last_run_failed"]:
            alerts.append({
                "type": "agent_error",
                "severity": "medium",
                "message": f"{agent_name} has recent errors",
                "agent": agent_name,
                "detail": agent_health.get("last_detail", ""),
                "action": "Review agent logs"
            })

    # Engagement rate alerts (with API context)
    if metrics["overall_engagement_rate"] < ALERT_THRESHOLD["low_engagement_rate"]:
        alerts.append({
            "type": "low_engagement",
            "severity": "medium",
            "message": f"Overall engagement rate dropped to {metrics['overall_engagement_rate']:.2%}",
            "value": metrics["overall_engagement_rate"],
            "action": "Review content strategy"
        })

    # Comment processing alerts (enhanced with API awareness)
    if not metrics["comment_stats"]["recent_activity"]:
        if api_status["status"] == "down":
            alerts.append({
                "type": "no_comments_api_down",
                "severity": "info",
                "message": "No comments processed due to API unavailability",
                "action": "Normal - wait for API recovery"
            })
        else:
            alerts.append({
                "type": "no_comments",
                "severity": "low",
                "message": "No comments processed in the last 24 hours",
                "suggestion": "Check if comment sources are active",
                "action": "Investigate comment sources"
            })

    return alerts


def create_enhanced_dashboard() -> str:
    """Generate enhanced dashboard with API health visibility."""
    health = check_agent_health()
    metrics = analyze_engagement_metrics()
    alerts = generate_alerts()
    api_status = analyze_api_status()

    dashboard = []
    dashboard.append("=" * 70)
    dashboard.append("[*] VAWN ENGAGEMENT MONITOR - APU-37 ENHANCED")
    dashboard.append(f"[DATE] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    dashboard.append("=" * 70)

    # API Health Section (NEW - Critical for APU-37)
    api_emoji = {
        "healthy": "[OK]",
        "slow": "[WARN]",
        "unstable": "[WARN]",
        "down": "[FAIL]"
    }.get(api_status["status"], "[?]")

    dashboard.append(f"\n[API] COMMENTS API HEALTH:")
    dashboard.append(f"  {api_emoji} Status: {api_status['status'].upper()}")
    dashboard.append(f"     Current: {'Available' if api_status['current']['available'] else 'Unavailable'}")
    dashboard.append(f"     Response: {api_status['current']['response_time_ms']}ms")
    if api_status["status"] != "down":
        dashboard.append(f"     Availability (24h): {api_status['availability_24h']:.1f}%")
        dashboard.append(f"     Avg Response (24h): {api_status['avg_response_time_24h']}ms")
        dashboard.append(f"     Downtime Incidents: {api_status['downtime_incidents']}")

    # Agent Health Section (enhanced)
    dashboard.append(f"\n[AGENTS] AGENT HEALTH:")
    for agent_name, agent_health in health.items():
        status_emoji = {
            "healthy": "[OK]",
            "stale": "[WARN]",
            "error_prone": "[ERROR]",
            "last_run_failed": "[ERROR]",
            "never_run": "[?]"
        }.get(agent_health["status"], "[?]")

        dashboard.append(f"  {status_emoji} {agent_name}:")
        dashboard.append(f"     Last run: {agent_health['last_run'] or 'Never'}")
        dashboard.append(f"     Runs today: {agent_health['runs_today']}")
        dashboard.append(f"     Status: {agent_health['status'].replace('_', ' ').upper()}")
        if agent_health.get("last_detail"):
            dashboard.append(f"     Detail: {agent_health['last_detail'][:50]}")

    # Platform Stats Section
    dashboard.append(f"\n[METRICS] PLATFORM ENGAGEMENT:")
    dashboard.append(f"  Overall Rate: {metrics['overall_engagement_rate']:.2%}")
    dashboard.append(f"  Total Posts: {metrics['total_posts']}")

    for platform, stats in metrics["platform_stats"].items():
        api_status_marker = "[API]" if stats["api_available"] else "[Manual]"
        dashboard.append(f"  • {platform.upper()}: {stats['avg_engagement']:.1f} avg | {api_status_marker}")

    # Comment Stats Section (enhanced with API context)
    dashboard.append(f"\n[COMMENTS] COMMENT MONITORING:")
    dashboard.append(f"  API Status: {'Available' if api_status['current']['available'] else 'Unavailable'}")
    dashboard.append(f"  Comments Seen: {metrics['comment_stats']['total_comments_seen']}")
    dashboard.append(f"  Replies Sent: {metrics['comment_stats']['replies_sent']}")
    dashboard.append(f"  Response Rate: {metrics['comment_stats']['response_rate']:.1%}")
    dashboard.append(f"  Recent Activity: {'[YES]' if metrics['comment_stats']['recent_activity'] else '[NO]'}")

    # Alerts Section (enhanced)
    dashboard.append(f"\n[ALERTS] SYSTEM ALERTS ({len(alerts)}):")
    if alerts:
        for alert in alerts:
            severity_emoji = {
                "critical": "[CRIT]",
                "high": "[HIGH]",
                "medium": "[MED]",
                "low": "[LOW]",
                "info": "[INFO]"
            }.get(alert["severity"], "[INFO]")
            dashboard.append(f"  {severity_emoji} {alert['message']}")
            if alert.get("action"):
                dashboard.append(f"         -> {alert['action']}")
    else:
        dashboard.append("  [OK] All systems normal")

    dashboard.append("\n" + "=" * 70)

    return "\n".join(dashboard)


def save_monitor_report():
    """Save comprehensive monitoring data to log file."""
    health = check_agent_health()
    metrics = analyze_engagement_metrics()
    alerts = generate_alerts()
    api_status = analyze_api_status()

    report = {
        "timestamp": datetime.now().isoformat(),
        "api_status": api_status,
        "agent_health": health,
        "engagement_metrics": metrics,
        "alerts": alerts,
        "summary": {
            "api_healthy": api_status["status"] in ["healthy", "slow"],
            "agents_healthy": sum(1 for h in health.values() if h["status"] == "healthy"),
            "total_alerts": len(alerts),
            "critical_alerts": len([a for a in alerts if a["severity"] == "critical"]),
            "high_priority_alerts": len([a for a in alerts if a["severity"] in ["critical", "high"]])
        }
    }

    # Load existing monitor log
    monitor_log = load_json(MONITOR_LOG) if Path(MONITOR_LOG).exists() else {}
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
    """Enhanced main monitoring function for APU-37."""
    print("\n[*] Vawn Engagement Monitor - APU-37 Enhanced Starting...")

    # Initialize missing files
    initialized = initialize_engagement_log()
    if initialized:
        log_run("EngagementMonitorAPU37", "info", "Initialized missing engagement_log.json")

    # Generate and display enhanced dashboard
    dashboard = create_enhanced_dashboard()
    print(dashboard)

    # Save monitoring report
    report = save_monitor_report()

    # Enhanced logging with API status
    summary = report["summary"]
    api_healthy = "API healthy" if summary["api_healthy"] else "API unhealthy"
    status = "ok" if summary["critical_alerts"] == 0 else "error" if summary["critical_alerts"] > 0 else "warning"

    log_run(
        "EngagementMonitorAPU37",
        status,
        f"{api_healthy}, {summary['agents_healthy']}/3 agents healthy, {summary['total_alerts']} alerts"
    )

    # Return alerts for potential notification system
    return report["alerts"]


if __name__ == "__main__":
    alerts = main()

    # Enhanced exit code logic with API awareness
    critical_alerts = [a for a in alerts if a["severity"] == "critical"]
    high_priority_alerts = [a for a in alerts if a["severity"] in ["critical", "high"]]

    if critical_alerts:
        print(f"\n[CRITICAL] {len(critical_alerts)} CRITICAL ALERTS FOUND!")
        print("System requires immediate attention")
        sys.exit(2)
    elif high_priority_alerts:
        print(f"\n[WARNING] {len(high_priority_alerts)} HIGH PRIORITY ALERTS FOUND!")
        sys.exit(1)
    else:
        print(f"\n[OK] Enhanced monitoring complete - {len(alerts)} total alerts")
        sys.exit(0)