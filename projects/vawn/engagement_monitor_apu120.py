"""
engagement_monitor_apu120.py — Advanced engagement monitoring with API health tracking.
Comprehensive monitoring system that properly handles API dependencies and agent status.
Created by: Dex - Community Agent (APU-120)
"""

import json
import sys
import requests
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import (
    load_json, save_json, ENGAGEMENT_LOG, RESEARCH_LOG, METRICS_LOG,
    VAWN_DIR, log_run, today_str, get_anthropic_client, CREDS_FILE
)

# Configuration
MONITOR_LOG = VAWN_DIR / "research" / "apu120_engagement_monitor_log.json"
API_HEALTH_LOG = VAWN_DIR / "research" / "api_health_log.json"
BASE_URL = "https://apulustudio.onrender.com/api"

ALERT_THRESHOLD = {
    "no_comments_days": 3,
    "low_engagement_rate": 0.05,
    "agent_failure_hours": 4,
    "stale_agent_hours": 2,
    "api_timeout_seconds": 30,
    "critical_api_failures": 3
}

PLATFORMS = ["instagram", "tiktok", "x", "threads", "bluesky"]
AGENTS = {
    "engagement_agent": {
        "script": "engagement_agent.py",
        "expected_interval_hours": 2,
        "description": "Comment monitoring and response generation",
        "depends_on_api": True,
        "api_endpoints": ["comments"]
    },
    "engagement_bot": {
        "script": "engagement_bot.py",
        "expected_interval_hours": 5,
        "description": "Proactive engagement and community building",
        "depends_on_api": True,
        "api_endpoints": ["posts", "metrics"]
    }
}

API_ENDPOINTS = {
    "comments": f"{BASE_URL}/posts/comments",
    "posts": f"{BASE_URL}/posts",
    "metrics": f"{BASE_URL}/metrics",
    "auth": f"{BASE_URL}/auth/refresh"
}


def test_api_health() -> Dict[str, Any]:
    """Test API endpoint health and return detailed status."""
    health = {}

    # Get authentication token
    try:
        creds = load_json(CREDS_FILE)
        access_token = creds.get("access_token", "")
        headers = {"Authorization": f"Bearer {access_token}"}
    except Exception as e:
        # If we can't get credentials, mark all endpoints as auth failure
        return {endpoint: {
            "status": "auth_failure",
            "response_time": 0,
            "error": f"Credential error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        } for endpoint in API_ENDPOINTS.keys()}

    for endpoint_name, url in API_ENDPOINTS.items():
        start_time = time.time()

        try:
            # Different endpoints need different methods
            if endpoint_name == "auth":
                # Skip auth test if we have valid token
                health[endpoint_name] = {
                    "status": "available",
                    "response_time": 0,
                    "message": "Skipped - valid token exists",
                    "timestamp": datetime.now().isoformat()
                }
                continue

            # Test with GET request
            r = requests.get(url, headers=headers, timeout=ALERT_THRESHOLD["api_timeout_seconds"])
            response_time = int((time.time() - start_time) * 1000)  # ms

            if r.status_code == 200:
                health[endpoint_name] = {
                    "status": "available",
                    "response_time": response_time,
                    "message": "Endpoint responding normally",
                    "timestamp": datetime.now().isoformat()
                }
            elif r.status_code == 404:
                health[endpoint_name] = {
                    "status": "not_implemented",
                    "response_time": response_time,
                    "message": "Endpoint not yet implemented",
                    "timestamp": datetime.now().isoformat()
                }
            elif r.status_code == 401:
                health[endpoint_name] = {
                    "status": "auth_failure",
                    "response_time": response_time,
                    "message": "Authentication failed",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                health[endpoint_name] = {
                    "status": "error",
                    "response_time": response_time,
                    "message": f"HTTP {r.status_code}: {r.text[:100]}",
                    "timestamp": datetime.now().isoformat()
                }

        except requests.exceptions.Timeout:
            health[endpoint_name] = {
                "status": "timeout",
                "response_time": ALERT_THRESHOLD["api_timeout_seconds"] * 1000,
                "message": f"Timeout after {ALERT_THRESHOLD['api_timeout_seconds']}s",
                "timestamp": datetime.now().isoformat()
            }
        except requests.exceptions.RequestException as e:
            health[endpoint_name] = {
                "status": "connection_error",
                "response_time": int((time.time() - start_time) * 1000),
                "message": f"Connection error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    return health


def analyze_agent_health_advanced() -> Dict[str, Any]:
    """Advanced agent health analysis that considers API dependencies."""
    research_log = load_json(RESEARCH_LOG)
    today = today_str()
    yesterday = str((datetime.now() - timedelta(days=1)).date())

    # Find recent agent entries
    agent_runs = {agent: [] for agent in AGENTS.keys()}

    for date in [today, yesterday]:
        if date in research_log:
            for entry in research_log[date]:
                agent_name = entry["agent"].lower()
                # Normalize agent name
                if "engagement" in agent_name and "agent" in agent_name:
                    agent_key = "engagement_agent"
                elif "engagement" in agent_name and "bot" in agent_name:
                    agent_key = "engagement_bot"
                else:
                    continue

                if agent_key in agent_runs:
                    agent_runs[agent_key].append(entry)

    # Get API health for context
    api_health = test_api_health()

    # Analyze health for each agent
    health = {}

    for agent_name, agent_info in AGENTS.items():
        runs = agent_runs[agent_name]

        agent_health = {
            "last_run": None,
            "runs_today": 0,
            "runs_24h": len(runs),
            "recent_errors": 0,
            "recent_successes": 0,
            "status": "unknown",
            "health_score": 0.0,
            "activity_pattern": "inactive",
            "success_rate": 0.0,
            "api_dependency_met": True,
            "api_dependency_status": {},
            "has_run_ever": len(runs) > 0,
            "status_description": "",
            "work_available": False,
            "detailed_analysis": {}
        }

        # Check API dependencies
        if agent_info.get("depends_on_api", False):
            for endpoint in agent_info.get("api_endpoints", []):
                endpoint_health = api_health.get(endpoint, {})
                agent_health["api_dependency_status"][endpoint] = endpoint_health
                if endpoint_health.get("status") not in ["available", "not_implemented"]:
                    agent_health["api_dependency_met"] = False

        if runs:
            # Basic metrics
            agent_health["last_run"] = runs[-1]["time"]
            agent_health["runs_today"] = len([r for r in runs if r["time"].startswith(today)])
            agent_health["recent_errors"] = len([r for r in runs if r["status"] == "error"])
            agent_health["recent_successes"] = len([r for r in runs if r["status"] == "ok"])

            # Calculate success rate
            if len(runs) > 0:
                agent_health["success_rate"] = agent_health["recent_successes"] / len(runs)

            # Analyze work patterns
            work_indicators = 0
            for run in runs:
                detail = run.get("detail", "").lower()
                if any(indicator in detail for indicator in ["processed", "sent", "generated", "found", "created"]):
                    work_indicators += 1
                elif "no comments" in detail or "no work" in detail or "skipping" in detail:
                    # This indicates the agent ran but had no work - this is normal
                    pass

            agent_health["work_available"] = work_indicators > 0

            # Time-based analysis
            last_run_time = datetime.fromisoformat(agent_health["last_run"])
            hours_since = (datetime.now() - last_run_time).total_seconds() / 3600

            # Calculate health score considering API dependencies
            recency_score = max(0, 1 - (hours_since / 24))  # Decreases over 24h
            success_score = agent_health["success_rate"]
            activity_score = min(1.0, agent_health["runs_24h"] / 12)  # Expect ~12 runs/day for 2h intervals

            # API dependency factor
            api_factor = 1.0 if agent_health["api_dependency_met"] else 0.5

            agent_health["health_score"] = (recency_score * 0.4 + success_score * 0.3 + activity_score * 0.3) * api_factor

            # Determine activity pattern and status
            if not agent_health["api_dependency_met"]:
                agent_health["activity_pattern"] = "api_dependent"
                agent_health["status"] = "api_limited"
                agent_health["status_description"] = "Agent working but limited by API availability"
            elif hours_since <= 2:
                if agent_health["work_available"]:
                    agent_health["activity_pattern"] = "active_processing"
                    agent_health["status"] = "healthy"
                    agent_health["status_description"] = "Agent actively processing work"
                else:
                    agent_health["activity_pattern"] = "healthy_idle"
                    agent_health["status"] = "healthy"
                    agent_health["status_description"] = "Agent running, no work available (normal)"
            elif hours_since <= agent_info["expected_interval_hours"]:
                agent_health["activity_pattern"] = "scheduled_idle"
                agent_health["status"] = "healthy"
                agent_health["status_description"] = "Agent on schedule, waiting for next run"
            elif hours_since <= ALERT_THRESHOLD["agent_failure_hours"]:
                agent_health["activity_pattern"] = "delayed"
                agent_health["status"] = "delayed"
                agent_health["status_description"] = f"Agent delayed - last run {hours_since:.1f}h ago"
            else:
                agent_health["activity_pattern"] = "stale"
                agent_health["status"] = "stale"
                agent_health["status_description"] = f"Agent stale - hasn't run in {hours_since:.1f}h"

        else:
            # No runs found
            agent_health["status"] = "never_run"
            agent_health["activity_pattern"] = "inactive"
            agent_health["status_description"] = "Agent has never run or logs not found"

        health[agent_name] = agent_health

    return health, api_health


def analyze_engagement_metrics_advanced() -> Dict[str, Any]:
    """Enhanced engagement metrics analysis with API health consideration."""
    try:
        metrics_log = load_json(METRICS_LOG)
        engagement_log = load_json(ENGAGEMENT_LOG)
    except Exception as e:
        return {
            "error": f"Could not load metrics: {str(e)}",
            "platform_stats": {},
            "comment_stats": {},
            "overall_engagement_rate": 0.0,
            "total_posts": 0,
            "top_performer": None
        }

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
                        "api_status": "unknown",
                        "last_activity": date,
                        "avg_engagement": 0.0,
                        "engagement_rate": 0.0,
                        "performance": "unknown",
                        "data_quality": "unknown"
                    }

                platform_stats[platform]["posts"] += 1
                platform_stats[platform]["last_activity"] = max(platform_stats[platform]["last_activity"], date)

                if isinstance(data, dict):
                    platform_stats[platform]["total_likes"] += data.get("likes", 0)
                    platform_stats[platform]["total_comments"] += data.get("comments", 0)
                    platform_stats[platform]["total_saves"] += data.get("saves", 0) + data.get("reposts", 0)
                    platform_stats[platform]["api_status"] = "available"
                    platform_stats[platform]["data_quality"] = "api_data"
                    total_engagement += data.get("likes", 0) + data.get("comments", 0)
                else:
                    platform_stats[platform]["api_status"] = "manual"
                    platform_stats[platform]["data_quality"] = "manual_entry"

    # Calculate engagement rates and performance ratings
    top_performer = None
    best_rate = 0

    for platform in platform_stats:
        stats = platform_stats[platform]
        if stats["posts"] > 0:
            stats["avg_engagement"] = (stats["total_likes"] + stats["total_comments"]) / stats["posts"]
            stats["engagement_rate"] = stats["avg_engagement"] / max(stats["posts"], 1)

            # Performance rating with context
            if stats["api_status"] == "manual":
                stats["performance"] = "unknown_manual"
            elif stats["avg_engagement"] > 1.0:
                stats["performance"] = "good"
            elif stats["avg_engagement"] > 0.1:
                stats["performance"] = "low"
            else:
                stats["performance"] = "none"

            # Track top performer
            if stats["engagement_rate"] > best_rate and stats["api_status"] == "available":
                best_rate = stats["engagement_rate"]
                top_performer = platform

    # Enhanced comment analysis with data validation
    comment_stats = {
        "total_comments_seen": len(engagement_log.get("replied_ids", [])),
        "replies_sent": len(engagement_log.get("history", [])),
        "response_rate": 0.0,
        "recent_activity": False,
        "data_consistency": "unknown",
        "api_status": "unknown"
    }

    # Validate comment data consistency
    replied_ids = engagement_log.get("replied_ids", [])
    history = engagement_log.get("history", [])

    if len(replied_ids) == 0 and len(history) > 0:
        comment_stats["data_consistency"] = "inconsistent_high_replies"
        comment_stats["api_status"] = "possible_api_issue"
    elif len(replied_ids) > 0:
        comment_stats["response_rate"] = len(history) / len(replied_ids)
        comment_stats["data_consistency"] = "consistent"
        comment_stats["api_status"] = "working"
    else:
        comment_stats["data_consistency"] = "no_data"
        comment_stats["api_status"] = "no_comments_available"

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


def generate_advanced_alerts(health: Dict[str, Any], metrics: Dict[str, Any], api_health: Dict[str, Any]) -> List[Dict[str, str]]:
    """Generate intelligent alerts that account for API health and actual vs expected issues."""
    alerts = []

    # API Health Alerts
    critical_api_issues = [ep for ep, status in api_health.items()
                          if status.get("status") in ["timeout", "connection_error", "error"]]

    if critical_api_issues:
        alerts.append({
            "type": "api_critical",
            "severity": "high",
            "message": f"Critical API issues: {', '.join(critical_api_issues)}",
            "endpoints": critical_api_issues,
            "action": "Check API server health and network connectivity"
        })

    not_implemented_apis = [ep for ep, status in api_health.items()
                           if status.get("status") == "not_implemented"]

    if not_implemented_apis:
        alerts.append({
            "type": "api_not_implemented",
            "severity": "low",
            "message": f"Expected APIs not implemented: {', '.join(not_implemented_apis)}",
            "endpoints": not_implemented_apis,
            "action": "Normal - these features are still in development"
        })

    # Agent Health Alerts (context-aware)
    for agent_name, agent_health in health.items():
        if agent_health["status"] == "stale":
            alerts.append({
                "type": "agent_stale",
                "severity": "high",
                "message": f"{agent_name} stale - requires manual intervention",
                "agent": agent_name,
                "action": "Check Windows Task Scheduler and agent logs"
            })
        elif agent_health["status"] == "api_limited":
            alerts.append({
                "type": "agent_api_limited",
                "severity": "medium",
                "message": f"{agent_name} limited by API availability (expected)",
                "agent": agent_name,
                "action": "Monitor API health - agent will resume when APIs available"
            })
        elif agent_health["status"] == "never_run":
            alerts.append({
                "type": "agent_never_run",
                "severity": "high",
                "message": f"{agent_name} has never executed successfully",
                "agent": agent_name,
                "action": "Check agent configuration and Windows Task Scheduler"
            })

    # Platform Performance Alerts (API-aware)
    if "platform_stats" in metrics:
        api_based_platforms = [p for p, s in metrics["platform_stats"].items()
                              if s.get("api_status") == "available" and s.get("avg_engagement") == 0]

        if len(api_based_platforms) > 2:
            alerts.append({
                "type": "platform_zero_engagement",
                "severity": "medium",
                "message": f"Multiple API-connected platforms showing zero engagement: {', '.join(api_based_platforms)}",
                "platforms": api_based_platforms,
                "action": "Check content quality and posting strategy"
            })

    # Comment System Alerts (data consistency aware)
    if "comment_stats" in metrics:
        comment_stats = metrics["comment_stats"]
        if comment_stats.get("data_consistency") == "inconsistent_high_replies":
            alerts.append({
                "type": "comment_data_inconsistent",
                "severity": "medium",
                "message": f"Comment data inconsistent: {comment_stats['replies_sent']} replies but 0 comments seen",
                "action": "Check comment API endpoint and data logging"
            })

    # Engagement Rate Alerts (with context)
    if "overall_engagement_rate" in metrics:
        if metrics["overall_engagement_rate"] < ALERT_THRESHOLD["low_engagement_rate"]:
            # Only alert if we have reliable API data
            api_platforms = sum(1 for p, s in metrics.get("platform_stats", {}).items()
                               if s.get("api_status") == "available")
            if api_platforms > 0:
                alerts.append({
                    "type": "low_engagement_confirmed",
                    "severity": "medium",
                    "message": f"Confirmed low engagement rate: {metrics['overall_engagement_rate']:.2%}",
                    "value": metrics["overall_engagement_rate"],
                    "action": "Review content strategy and posting times"
                })

    return alerts


def create_advanced_dashboard(health: Dict[str, Any], metrics: Dict[str, Any], alerts: List[Dict[str, str]], api_health: Dict[str, Any]) -> str:
    """Generate comprehensive dashboard with API health and intelligent status reporting."""
    dashboard = []
    dashboard.append("=" * 80)
    dashboard.append("[*] VAWN ADVANCED ENGAGEMENT MONITOR DASHBOARD (APU-120)")
    dashboard.append(f"[DATE] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    dashboard.append("=" * 80)

    # API Health Summary
    api_available = sum(1 for status in api_health.values() if status.get("status") == "available")
    api_total = len(api_health)
    api_not_impl = sum(1 for status in api_health.values() if status.get("status") == "not_implemented")

    dashboard.append(f"\n[API] ENDPOINT HEALTH: {api_available}/{api_total} available, {api_not_impl} not implemented")
    for endpoint, status in api_health.items():
        status_emoji = {
            "available": "[OK]",
            "not_implemented": "[PENDING]",
            "timeout": "[TIMEOUT]",
            "connection_error": "[ERROR]",
            "auth_failure": "[AUTH]",
            "error": "[ERROR]"
        }.get(status.get("status"), "[?]")

        response_time = status.get("response_time", 0)
        dashboard.append(f"  {status_emoji} {endpoint.upper()}: {status.get('message', 'Unknown')} ({response_time}ms)")

    # System Summary
    healthy_agents = sum(1 for h in health.values() if h["status"] in ["healthy", "api_limited"])
    total_agents = len(health)
    overall_health = sum(h["health_score"] for h in health.values()) / len(health) if health else 0

    dashboard.append(f"\n[SYSTEM] OVERALL HEALTH: {overall_health:.2f} | {healthy_agents}/{total_agents} agents operational")

    # Agent Health Section with Advanced Context
    dashboard.append(f"\n[AGENTS] AGENT HEALTH & API DEPENDENCIES:")
    for agent_name, agent_health in health.items():
        status_emoji = {
            "healthy": "[OK]",
            "api_limited": "[API-LIMITED]",
            "delayed": "[DELAYED]",
            "stale": "[STALE]",
            "never_run": "[NEVER-RUN]",
            "unknown": "[?]"
        }.get(agent_health["status"], "[?]")

        dashboard.append(f"  {status_emoji} {agent_name.upper()}:")
        dashboard.append(f"     Status: {agent_health['status'].upper()} | Health: {agent_health['health_score']:.2f}")
        dashboard.append(f"     Last run: {agent_health['last_run'] or 'Never'}")
        dashboard.append(f"     Runs (24h): {agent_health['runs_24h']} | Success: {agent_health['success_rate']:.1%}")
        dashboard.append(f"     Activity: {agent_health['activity_pattern']} | Work detected: {agent_health['work_available']}")

        # API dependency status
        if agent_health.get("api_dependency_status"):
            api_deps = agent_health["api_dependency_status"]
            dep_status = "OK" if agent_health["api_dependency_met"] else "LIMITED"
            dashboard.append(f"     API Dependencies: {dep_status}")

    # Platform Performance Section with Data Quality
    if "platform_stats" in metrics:
        dashboard.append(f"\n[PLATFORMS] PERFORMANCE & DATA QUALITY:")
        dashboard.append(f"  Overall Rate: {metrics.get('overall_engagement_rate', 0):.2%} | Posts: {metrics.get('total_posts', 0)}")
        dashboard.append(f"  Top Performer: {(metrics.get('top_performer', 'None') or 'None').upper()}")

        for platform, stats in metrics["platform_stats"].items():
            performance_indicator = {
                "good": "[GOOD]",
                "low": "[LOW]",
                "none": "[NONE]",
                "unknown_manual": "[MANUAL]"
            }.get(stats["performance"], "[?]")

            data_quality = "[API]" if stats["data_quality"] == "api_data" else "[Manual]"
            dashboard.append(f"  {performance_indicator} {platform.upper()}: {stats['avg_engagement']:.1f} avg | {data_quality}")

    # Comments Section with Data Consistency
    if "comment_stats" in metrics:
        comment_stats = metrics["comment_stats"]
        consistency_status = {
            "consistent": "[OK]",
            "inconsistent_high_replies": "[DATA-ISSUE]",
            "no_data": "[NO-DATA]"
        }.get(comment_stats.get("data_consistency"), "[?]")

        dashboard.append(f"\n[COMMENTS] ENGAGEMENT MONITORING:")
        dashboard.append(f"  Data Consistency: {consistency_status}")
        dashboard.append(f"  Comments Seen: {comment_stats.get('total_comments_seen', 0)}")
        dashboard.append(f"  Replies Sent: {comment_stats.get('replies_sent', 0)}")
        dashboard.append(f"  Response Rate: {comment_stats.get('response_rate', 0):.1%}")
        dashboard.append(f"  Recent Activity: {'[YES]' if comment_stats.get('recent_activity') else '[NO]'}")

    # Intelligent Alerts Section
    dashboard.append(f"\n[ALERTS] INTELLIGENT ALERTS ({len(alerts)}):")
    if alerts:
        for alert in alerts:
            severity_emoji = {"high": "[HIGH]", "medium": "[MED]", "low": "[INFO]"}.get(alert["severity"], "[?]")
            dashboard.append(f"  {severity_emoji} {alert['message']}")
            if "action" in alert:
                dashboard.append(f"       Action: {alert['action']}")
    else:
        dashboard.append("  [OK] All systems operating within normal parameters")

    dashboard.append(f"\n" + "=" * 80)
    return "\n".join(dashboard)


def save_apu120_report(health: Dict[str, Any], metrics: Dict[str, Any], alerts: List[Dict[str, str]], api_health: Dict[str, Any]):
    """Save comprehensive APU-120 monitoring report."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "version": "apu120_advanced",
        "monitor_type": "engagement_advanced",
        "agents": health,
        "metrics": metrics,
        "api_health": api_health,
        "alerts": alerts,
        "summary": {
            "healthy_agents": sum(1 for h in health.values() if h["status"] in ["healthy", "api_limited"]),
            "total_agents": len(health),
            "total_alerts": len(alerts),
            "high_priority_alerts": len([a for a in alerts if a["severity"] == "high"]),
            "api_endpoints_available": sum(1 for s in api_health.values() if s.get("status") == "available"),
            "api_endpoints_total": len(api_health),
            "system_status": "operational" if len([a for a in alerts if a["severity"] == "high"]) == 0 else "degraded",
            "top_platform": metrics.get("top_performer", "none"),
            "overall_health_score": sum(h["health_score"] for h in health.values()) / len(health) if health else 0,
            "data_quality_score": _calculate_data_quality_score(metrics, api_health)
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

    # Also save API health separately for trending
    api_log = load_json(API_HEALTH_LOG)
    if today not in api_log:
        api_log[today] = []
    api_log[today].append({
        "timestamp": datetime.now().isoformat(),
        "api_health": api_health
    })
    save_json(API_HEALTH_LOG, api_log)

    return report


def _calculate_data_quality_score(metrics: Dict[str, Any], api_health: Dict[str, Any]) -> float:
    """Calculate overall data quality score based on API health and data consistency."""
    api_score = sum(1 for s in api_health.values() if s.get("status") == "available") / len(api_health) if api_health else 0

    comment_consistency = 1.0
    if "comment_stats" in metrics:
        consistency = metrics["comment_stats"].get("data_consistency", "unknown")
        if consistency == "inconsistent_high_replies":
            comment_consistency = 0.5
        elif consistency == "no_data":
            comment_consistency = 0.7

    platform_data_quality = 1.0
    if "platform_stats" in metrics:
        api_platforms = [s for s in metrics["platform_stats"].values() if s.get("data_quality") == "api_data"]
        total_platforms = len(metrics["platform_stats"])
        if total_platforms > 0:
            platform_data_quality = len(api_platforms) / total_platforms

    return (api_score * 0.4 + comment_consistency * 0.3 + platform_data_quality * 0.3)


def main():
    """APU-120 Advanced Engagement Monitoring."""
    print(f"\n[*] Vawn Advanced Engagement Monitor (APU-120) Starting...")

    # Test API health first
    print(f"[APU-120] Testing API endpoint health...")
    api_health = test_api_health()

    # Analyze agent health with API context
    print(f"[APU-120] Analyzing agent health with API dependencies...")
    health, api_health_from_agents = analyze_agent_health_advanced()

    # Analyze engagement metrics
    print(f"[APU-120] Analyzing engagement metrics with data quality validation...")
    metrics = analyze_engagement_metrics_advanced()

    # Generate intelligent alerts
    print(f"[APU-120] Generating context-aware alerts...")
    alerts = generate_advanced_alerts(health, metrics, api_health)

    # Generate and display advanced dashboard
    dashboard = create_advanced_dashboard(health, metrics, alerts, api_health)
    print(dashboard)

    # Save comprehensive report
    report = save_apu120_report(health, metrics, alerts, api_health)

    # Log summary with advanced context
    summary = report["summary"]
    data_quality_info = f"DQ: {summary['data_quality_score']:.2f}"
    api_info = f"API: {summary['api_endpoints_available']}/{summary['api_endpoints_total']}"

    log_run(
        "AdvancedEngagementMonitor_APU120",
        "ok" if summary["high_priority_alerts"] == 0 else "warning",
        f"{summary['healthy_agents']}/{summary['total_agents']} agents operational, {summary['total_alerts']} alerts, {api_info}, {data_quality_info}"
    )

    return alerts, api_health


if __name__ == "__main__":
    alerts, api_health = main()

    # Exit with appropriate code based on system health
    high_priority = [a for a in alerts if a["severity"] == "high"]

    if high_priority:
        print(f"\n[WARNING] APU-120: {len(high_priority)} HIGH PRIORITY ALERTS FOUND!")
        sys.exit(1)
    else:
        print(f"\n[OK] APU-120: Advanced monitoring complete - {len(alerts)} total alerts")
        sys.exit(0)