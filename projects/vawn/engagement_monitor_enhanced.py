"""
engagement_monitor_enhanced.py — Enhanced monitoring system with auto-recovery for APU-37.
Comprehensive monitoring system for Vawn's cross-platform engagement with automatic remediation.
Created by: Dex - Community Agent (APU-37)
"""

import json
import sys
import requests
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import (
    load_json, save_json, ENGAGEMENT_LOG, RESEARCH_LOG, METRICS_LOG,
    VAWN_DIR, log_run, today_str, get_anthropic_client
)

# Configuration
MONITOR_LOG = VAWN_DIR / "research" / "enhanced_engagement_monitor_log.json"
ALERT_THRESHOLD = {
    "no_comments_days": 3,
    "low_engagement_rate": 0.05,
    "agent_failure_hours": 4,
    "stale_agent_hours": 2,  # More aggressive detection for auto-recovery
}

PLATFORMS = ["instagram", "tiktok", "x", "threads", "bluesky"]
AGENTS = {
    "engagement_agent": {
        "script": "engagement_agent.py",
        "expected_interval_hours": 2,
        "description": "Comment monitoring and response generation"
    },
    "engagement_bot": {
        "script": "engagement_bot.py",
        "expected_interval_hours": 5,
        "description": "Proactive engagement and community building"
    }
}


def initialize_engagement_log():
    """Initialize the missing engagement_log.json that engagement_agent.py expects."""
    if not Path(ENGAGEMENT_LOG).exists():
        initial_data = {
            "replied_ids": [],
            "history": [],
            "last_updated": datetime.now().isoformat(),
            "initialized_by": "engagement_monitor_enhanced",
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


def run_agent_manually(agent_name: str) -> Tuple[bool, str]:
    """Manually execute an engagement agent."""
    agent_info = AGENTS.get(agent_name)
    if not agent_info:
        return False, f"Unknown agent: {agent_name}"

    script_path = VAWN_DIR / agent_info["script"]
    if not script_path.exists():
        return False, f"Script not found: {script_path}"

    try:
        print(f"[AUTO-RECOVERY] Starting {agent_name}...")

        # Run the agent
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            cwd=str(VAWN_DIR)
        )

        if result.returncode == 0:
            log_run(f"AutoRecovery_{agent_name}", "ok", f"Manual execution successful")
            return True, f"Successfully executed {agent_name}"
        else:
            error_msg = f"Exit code {result.returncode}: {result.stderr}"
            log_run(f"AutoRecovery_{agent_name}", "error", error_msg)
            return False, error_msg

    except subprocess.TimeoutExpired:
        error_msg = f"Agent {agent_name} timed out after 5 minutes"
        log_run(f"AutoRecovery_{agent_name}", "error", error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Failed to execute {agent_name}: {str(e)}"
        log_run(f"AutoRecovery_{agent_name}", "error", error_msg)
        return False, error_msg


def check_agent_health() -> Dict[str, Any]:
    """Enhanced agent health check with auto-recovery capability."""
    research_log = load_json(RESEARCH_LOG)
    today = today_str()
    yesterday = str((datetime.now() - timedelta(days=1)).date())

    # Find recent agent entries
    agent_runs = {agent: [] for agent in AGENTS.keys()}

    for date in [today, yesterday]:
        if date in research_log:
            for entry in research_log[date]:
                agent_key = entry["agent"].lower().replace("agent", "_agent").replace("bot", "_bot")
                if agent_key in agent_runs:
                    agent_runs[agent_key].append(entry)

    # Analyze health for each agent
    health = {}

    for agent_name, agent_info in AGENTS.items():
        runs = agent_runs[agent_name]

        agent_health = {
            "last_run": None,
            "runs_today": 0,
            "recent_errors": 0,
            "comments_processed": 0,
            "status": "unknown",
            "health_score": 0.0,
            "activity_pattern": "inactive",
            "auto_recovery_attempted": False,
            "auto_recovery_success": None,
            "runs_24h": len(runs),
            "success_rate": 0.0,
            "engagement_actions": 0,
            "recent_statuses": [],
            "status_description": ""
        }

        if runs:
            agent_health["last_run"] = runs[-1]["time"]
            agent_health["runs_today"] = len([r for r in runs if r["time"].startswith(today)])
            agent_health["recent_errors"] = len([r for r in runs if r["status"] == "error"])
            agent_health["recent_statuses"] = [r["status"] for r in runs[-5:]]

            # Calculate success rate
            if len(runs) > 0:
                successful_runs = len([r for r in runs if r["status"] == "ok"])
                agent_health["success_rate"] = successful_runs / len(runs)

            # Extract engagement metrics from details
            for run in runs:
                detail = run.get("detail", "")
                if "replies generated" in detail or "likes" in detail:
                    try:
                        # Extract numbers from detail string
                        import re
                        numbers = re.findall(r'\d+', detail)
                        if numbers:
                            agent_health["engagement_actions"] += sum(int(n) for n in numbers[:2])
                    except:
                        pass

            # Determine status and activity pattern
            last_run_time = datetime.fromisoformat(agent_health["last_run"])
            hours_since = (datetime.now() - last_run_time).total_seconds() / 3600

            # Calculate health score
            recency_score = max(0, 1 - (hours_since / 24))  # Decreases over 24h
            success_score = agent_health["success_rate"]
            activity_score = min(1.0, agent_health["runs_24h"] / 12)  # Expect ~12 runs/day for 2h intervals
            agent_health["health_score"] = (recency_score * 0.5 + success_score * 0.3 + activity_score * 0.2)

            # Determine activity pattern
            if hours_since <= 2:
                agent_health["activity_pattern"] = "active_processing"
                agent_health["status_description"] = "Agent running and processing work successfully"
            elif hours_since <= agent_info["expected_interval_hours"]:
                agent_health["activity_pattern"] = "healthy_idle"
                agent_health["status_description"] = "Agent running but no work available (normal)"
            else:
                agent_health["activity_pattern"] = "stale"
                agent_health["status_description"] = f"Agent stale - hasn't run in {hours_since:.1f}h"

            # Determine overall status
            if hours_since > ALERT_THRESHOLD["agent_failure_hours"]:
                agent_health["status"] = "stale"
            elif agent_health["recent_errors"] > 0:
                agent_health["status"] = "error"
            elif hours_since <= agent_info["expected_interval_hours"]:
                agent_health["status"] = "healthy"
            else:
                agent_health["status"] = "idle"

        health[agent_name] = agent_health

    return health


def auto_recover_stale_agents(health: Dict[str, Any]) -> List[Dict[str, str]]:
    """Automatically attempt to recover stale agents."""
    recovery_actions = []

    for agent_name, agent_health in health.items():
        if agent_health["status"] in ["stale", "error"]:
            last_run = agent_health.get("last_run")
            if last_run:
                last_run_time = datetime.fromisoformat(last_run)
                hours_since = (datetime.now() - last_run_time).total_seconds() / 3600

                # Only attempt recovery if agent has been stale for 2+ hours
                if hours_since >= ALERT_THRESHOLD["stale_agent_hours"]:
                    print(f"\n[AUTO-RECOVERY] Attempting to recover {agent_name} (stale for {hours_since:.1f}h)...")

                    success, message = run_agent_manually(agent_name)

                    recovery_action = {
                        "timestamp": datetime.now().isoformat(),
                        "agent": agent_name,
                        "reason": f"Stale for {hours_since:.1f}h",
                        "success": success,
                        "message": message,
                        "hours_stale": hours_since
                    }

                    recovery_actions.append(recovery_action)

                    # Update health status
                    health[agent_name]["auto_recovery_attempted"] = True
                    health[agent_name]["auto_recovery_success"] = success

                    if success:
                        print(f"[AUTO-RECOVERY] [SUCCESS] {agent_name} recovered successfully")
                        # Update status to indicate recent manual run
                        health[agent_name]["status"] = "recovered"
                        health[agent_name]["activity_pattern"] = "auto_recovered"
                        health[agent_name]["status_description"] = "Agent auto-recovered and running"
                    else:
                        print(f"[AUTO-RECOVERY] [FAILED] {agent_name} recovery failed: {message}")

    return recovery_actions


def analyze_engagement_metrics() -> Dict[str, Any]:
    """Analyze engagement metrics across all platforms with performance ratings."""
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
                        "api_status": "available",
                        "last_activity": date,
                        "avg_engagement": 0.0,
                        "engagement_rate": 0.0,
                        "performance": "unknown"
                    }

                platform_stats[platform]["posts"] += 1
                platform_stats[platform]["last_activity"] = max(platform_stats[platform]["last_activity"], date)

                if isinstance(data, dict):
                    platform_stats[platform]["total_likes"] += data.get("likes", 0)
                    platform_stats[platform]["total_comments"] += data.get("comments", 0)
                    platform_stats[platform]["total_saves"] += data.get("saves", 0) + data.get("reposts", 0)
                    total_engagement += data.get("likes", 0) + data.get("comments", 0)
                else:
                    platform_stats[platform]["api_status"] = "manual"

    # Calculate engagement rates and performance ratings
    top_performer = None
    best_rate = 0

    for platform in platform_stats:
        stats = platform_stats[platform]
        if stats["posts"] > 0:
            stats["avg_engagement"] = (stats["total_likes"] + stats["total_comments"]) / stats["posts"]
            stats["engagement_rate"] = stats["avg_engagement"] / max(stats["posts"], 1)

            # Performance rating
            if stats["avg_engagement"] > 1.0:
                stats["performance"] = "good"
            elif stats["avg_engagement"] > 0.1:
                stats["performance"] = "low"
            else:
                stats["performance"] = "none"

            # Track top performer
            if stats["engagement_rate"] > best_rate:
                best_rate = stats["engagement_rate"]
                top_performer = platform

    # Enhanced comment analysis
    comment_stats = {
        "total_comments_seen": len(engagement_log.get("replied_ids", [])),
        "replies_sent": len(engagement_log.get("history", [])),
        "response_rate": 0.0,
        "recent_activity": False,
        "api_status": "available_no_comments"
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
        "total_posts": total_posts,
        "top_performer": top_performer
    }


def generate_enhanced_alerts(health: Dict[str, Any], metrics: Dict[str, Any], recovery_actions: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Generate enhanced alerts including auto-recovery status."""
    alerts = []

    # Agent health alerts with auto-recovery status
    for agent_name, agent_health in health.items():
        if agent_health["status"] == "stale":
            if agent_health.get("auto_recovery_attempted"):
                if agent_health.get("auto_recovery_success"):
                    alerts.append({
                        "type": "auto_recovery_success",
                        "severity": "low",
                        "message": f"{agent_name} auto-recovered successfully",
                        "agent": agent_name
                    })
                else:
                    alerts.append({
                        "type": "auto_recovery_failed",
                        "severity": "high",
                        "message": f"{agent_name} auto-recovery failed - manual intervention required",
                        "agent": agent_name
                    })
            else:
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

    # Platform performance alerts
    zero_engagement_platforms = [p for p, s in metrics["platform_stats"].items() if s["avg_engagement"] == 0]
    if len(zero_engagement_platforms) > 2:
        alerts.append({
            "type": "platform_performance",
            "severity": "medium",
            "message": f"Multiple platforms showing zero engagement: {', '.join(zero_engagement_platforms)}",
            "platforms": zero_engagement_platforms,
            "action": "Check API connections and engagement strategies"
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


def create_enhanced_dashboard(health: Dict[str, Any], metrics: Dict[str, Any], alerts: List[Dict[str, str]], recovery_actions: List[Dict[str, str]]) -> str:
    """Generate enhanced dashboard with auto-recovery information."""
    dashboard = []
    dashboard.append("=" * 70)
    dashboard.append("[*] VAWN ENHANCED ENGAGEMENT MONITOR DASHBOARD (APU-37)")
    dashboard.append(f"[DATE] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    dashboard.append("=" * 70)

    # System Summary
    healthy_agents = sum(1 for h in health.values() if h["status"] in ["healthy", "idle", "recovered"])
    overall_health = sum(h["health_score"] for h in health.values()) / len(health) if health else 0

    dashboard.append(f"\n[SYSTEM] OVERALL HEALTH: {overall_health:.2f} | {healthy_agents}/{len(health)} agents healthy")

    # Agent Health Section with Enhanced Info
    dashboard.append(f"\n[AGENTS] AGENT HEALTH & AUTO-RECOVERY:")
    for agent_name, agent_health in health.items():
        status_emoji = {
            "healthy": "[OK]",
            "idle": "[OK]",
            "stale": "[WARN]",
            "error": "[ERROR]",
            "recovered": "[RECOVERED]",
            "unknown": "[?]"
        }.get(agent_health["status"], "[?]")

        dashboard.append(f"  {status_emoji} {agent_name.upper()}:")
        dashboard.append(f"     Status: {agent_health['status'].upper()} | Score: {agent_health['health_score']:.2f}")
        dashboard.append(f"     Last run: {agent_health['last_run'] or 'Never'}")
        dashboard.append(f"     Runs (24h): {agent_health['runs_24h']} | Success: {agent_health['success_rate']:.1%}")
        dashboard.append(f"     Activity: {agent_health['activity_pattern']}")

        if agent_health.get("auto_recovery_attempted"):
            recovery_status = "[SUCCESS]" if agent_health.get("auto_recovery_success") else "[FAILED]"
            dashboard.append(f"     Auto-recovery: {recovery_status}")

    # Platform Performance Section
    dashboard.append(f"\n[METRICS] PLATFORM PERFORMANCE:")
    dashboard.append(f"  Overall Rate: {metrics['overall_engagement_rate']:.2%} | Posts: {metrics['total_posts']}")
    dashboard.append(f"  Top Platform: {metrics.get('top_performer', 'None').upper()}")

    for platform, stats in metrics["platform_stats"].items():
        performance_indicator = {"good": "[GOOD]", "low": "[LOW]", "none": "[NONE]"}.get(stats["performance"], "[UNKNOWN]")
        api_status = "[API]" if stats["api_status"] == "available" else "[Manual]"
        dashboard.append(f"  {performance_indicator} {platform.upper()}: {stats['avg_engagement']:.1f} avg | {api_status}")

    # Comments Section
    dashboard.append(f"\n[COMMENTS] ENGAGEMENT MONITORING:")
    dashboard.append(f"  Comments Seen: {metrics['comment_stats']['total_comments_seen']}")
    dashboard.append(f"  Replies Sent: {metrics['comment_stats']['replies_sent']}")
    dashboard.append(f"  Response Rate: {metrics['comment_stats']['response_rate']:.1%}")
    dashboard.append(f"  Recent Activity: {'[YES]' if metrics['comment_stats']['recent_activity'] else '[NO]'}")

    # Auto-Recovery Actions
    if recovery_actions:
        dashboard.append(f"\n[AUTO-RECOVERY] RECENT ACTIONS ({len(recovery_actions)}):")
        for action in recovery_actions[-3:]:  # Show last 3 actions
            status_indicator = "[SUCCESS]" if action["success"] else "[FAILED]"
            dashboard.append(f"  {status_indicator} {action['agent']}: {action['message'][:50]}...")

    # Alerts Section
    dashboard.append(f"\n[ALERTS] SYSTEM ALERTS ({len(alerts)}):")
    if alerts:
        for alert in alerts:
            severity_emoji = {"high": "[HIGH]", "medium": "[MED]", "low": "[LOW]"}.get(alert["severity"], "[INFO]")
            dashboard.append(f"  {severity_emoji} {alert['message']}")
    else:
        dashboard.append("  [OK] All systems operational")

    dashboard.append(f"\n" + "=" * 70)

    return "\n".join(dashboard)


def save_enhanced_monitor_report(health: Dict[str, Any], metrics: Dict[str, Any], alerts: List[Dict[str, str]], recovery_actions: List[Dict[str, str]]):
    """Save enhanced monitoring data including auto-recovery actions."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "version": "enhanced_v2_apu37",
        "agents": health,
        "metrics": metrics,
        "alerts": alerts,
        "recovery_actions": recovery_actions,
        "summary": {
            "healthy_agents": sum(1 for h in health.values() if h["status"] in ["healthy", "idle", "recovered"]),
            "total_agents": len(health),
            "total_alerts": len(alerts),
            "high_priority_alerts": len([a for a in alerts if a["severity"] == "high"]),
            "auto_recoveries_attempted": len(recovery_actions),
            "auto_recoveries_successful": len([a for a in recovery_actions if a["success"]]),
            "system_status": "operational" if len([a for a in alerts if a["severity"] == "high"]) == 0 else "degraded",
            "top_platform": metrics.get("top_performer", "none"),
            "overall_health_score": sum(h["health_score"] for h in health.values()) / len(health) if health else 0
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
    """Enhanced main monitoring function with auto-recovery."""
    print(f"\n[*] Vawn Enhanced Engagement Monitor (APU-37) Starting...")

    # Initialize missing files
    initialized = initialize_engagement_log()
    if initialized:
        log_run("EnhancedEngagementMonitor", "info", "Initialized missing engagement_log.json")

    # Check agent health
    health = check_agent_health()

    # Attempt auto-recovery for stale agents
    recovery_actions = auto_recover_stale_agents(health)

    # Re-check health after recovery attempts
    if recovery_actions:
        print(f"[AUTO-RECOVERY] Performed {len(recovery_actions)} recovery attempts")
        # Give agents a moment to complete if they were started
        time.sleep(2)
        # Don't re-check immediately to avoid false positives

    # Analyze metrics
    metrics = analyze_engagement_metrics()

    # Generate alerts
    alerts = generate_enhanced_alerts(health, metrics, recovery_actions)

    # Generate and display enhanced dashboard
    dashboard = create_enhanced_dashboard(health, metrics, alerts, recovery_actions)
    print(dashboard)

    # Save enhanced monitoring report
    report = save_enhanced_monitor_report(health, metrics, alerts, recovery_actions)

    # Log summary with auto-recovery info
    summary = report["summary"]
    recovery_info = f", {summary['auto_recoveries_successful']}/{summary['auto_recoveries_attempted']} recoveries" if summary['auto_recoveries_attempted'] > 0 else ""

    log_run(
        "EnhancedEngagementMonitor",
        "ok" if summary["high_priority_alerts"] == 0 else "warning",
        f"{summary['healthy_agents']}/{summary['total_agents']} agents healthy, {summary['total_alerts']} alerts{recovery_info}"
    )

    return alerts, recovery_actions


if __name__ == "__main__":
    alerts, recovery_actions = main()

    # Exit with appropriate code based on system health
    high_priority = [a for a in alerts if a["severity"] == "high"]
    failed_recoveries = [a for a in recovery_actions if not a["success"]]

    if high_priority and failed_recoveries:
        print(f"\n[CRITICAL] {len(high_priority)} HIGH PRIORITY ALERTS + {len(failed_recoveries)} FAILED RECOVERIES!")
        sys.exit(2)
    elif high_priority:
        print(f"\n[WARNING] {len(high_priority)} HIGH PRIORITY ALERTS FOUND!")
        sys.exit(1)
    elif failed_recoveries:
        print(f"\n[WARNING] {len(failed_recoveries)} AUTO-RECOVERY FAILURES!")
        sys.exit(1)
    else:
        successful_recoveries = len([a for a in recovery_actions if a["success"]])
        recovery_msg = f" ({successful_recoveries} auto-recoveries)" if successful_recoveries > 0 else ""
        print(f"\n[OK] Enhanced monitoring complete - {len(alerts)} total alerts{recovery_msg}")
        sys.exit(0)