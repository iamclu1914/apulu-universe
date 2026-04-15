"""
apu52_unified_engagement_monitor.py - APU-52 Unified Engagement Monitor

Coordinates and integrates all engagement systems:
- APU-50 Enhanced Engagement Bot (health monitoring, performance tracking)
- APU-49 Paperclip Department Monitor (organizational oversight, routing)
- Real-time coordination and data pipeline management
- Unified dashboard and alerting system

Created by: Dex - Community Agent (APU-52)

Integration Architecture:
1. Execute enhanced engagement bot (APU-50)
2. Collect and process bot performance data
3. Feed data into Paperclip monitoring system (APU-49)
4. Generate unified organizational dashboard
5. Route alerts to appropriate departments
6. Provide executive summary for chairman oversight
"""

import json
import sys
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict

# Add Vawn directory to Python path
sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import (
    load_json, save_json, ENGAGEMENT_LOG, RESEARCH_LOG, METRICS_LOG,
    VAWN_DIR, log_run, today_str, get_anthropic_client
)

# Add src directory for APU components
sys.path.insert(0, r"C:\Users\rdyal\Vawn\src")

# Configuration
UNIFIED_MONITOR_LOG = VAWN_DIR / "research" / "apu52_unified_engagement_monitor_log.json"
COORDINATION_LOG = VAWN_DIR / "research" / "engagement_coordination_log.json"
UNIFIED_REPORTS_DIR = VAWN_DIR / "research" / "unified_reports"
UNIFIED_REPORTS_DIR.mkdir(exist_ok=True)

# System Component Paths
ENHANCED_BOT_PATH = VAWN_DIR / "engagement_bot_enhanced.py"
ENHANCED_BOT_LOG_PATH = VAWN_DIR / "research" / "engagement_bot_enhanced_log.json"
HEALTH_LOG_PATH = VAWN_DIR / "research" / "engagement_health_log.json"

# Integration thresholds
COORDINATION_THRESHOLDS = {
    "bot_execution_timeout": 300,  # 5 minutes max for bot execution
    "health_degradation_threshold": 0.6,  # API health below 60%
    "engagement_effectiveness_threshold": 0.5,  # Success rate below 50%
    "department_escalation_threshold": 3,  # 3+ urgent issues trigger escalation
    "organizational_health_critical": 0.4,  # Overall health below 40%
}


def execute_enhanced_engagement_bot() -> Dict[str, Any]:
    """Execute the enhanced engagement bot and capture results."""
    print("[EXEC] Starting enhanced engagement bot (APU-50)...")

    bot_execution_result = {
        "execution_time": datetime.now().isoformat(),
        "success": False,
        "bot_metrics": {},
        "health_data": {},
        "execution_details": {},
        "errors": []
    }

    try:
        # Execute the enhanced bot
        start_time = datetime.now()

        process = subprocess.run(
            [sys.executable, str(ENHANCED_BOT_PATH)],
            capture_output=True,
            text=True,
            timeout=COORDINATION_THRESHOLDS["bot_execution_timeout"],
            cwd=str(VAWN_DIR)
        )

        execution_time = (datetime.now() - start_time).total_seconds()

        bot_execution_result["execution_details"] = {
            "return_code": process.returncode,
            "execution_time_seconds": execution_time,
            "stdout_lines": len(process.stdout.split('\n')) if process.stdout else 0,
            "stderr_lines": len(process.stderr.split('\n')) if process.stderr else 0
        }

        if process.returncode == 0:
            bot_execution_result["success"] = True
            print(f"[OK] Enhanced bot completed in {execution_time:.1f}s")

            # Parse bot metrics from recent logs
            bot_execution_result["bot_metrics"] = extract_bot_metrics()
            bot_execution_result["health_data"] = extract_health_data()

        else:
            bot_execution_result["errors"].append(f"Bot execution failed with code {process.returncode}")
            if process.stderr:
                bot_execution_result["errors"].append(f"STDERR: {process.stderr[:200]}")
            print(f"[FAIL] Enhanced bot failed with code {process.returncode}")

    except subprocess.TimeoutExpired:
        bot_execution_result["errors"].append(f"Bot execution timed out after {COORDINATION_THRESHOLDS['bot_execution_timeout']}s")
        print(f"[TIMEOUT] Enhanced bot timed out after {COORDINATION_THRESHOLDS['bot_execution_timeout']}s")

    except Exception as e:
        bot_execution_result["errors"].append(f"Bot execution error: {str(e)}")
        print(f"[ERROR] Enhanced bot execution error: {e}")

    return bot_execution_result


def extract_bot_metrics() -> Dict[str, Any]:
    """Extract metrics from enhanced bot logs."""
    try:
        if not ENHANCED_BOT_LOG_PATH.exists():
            return {"error": "Enhanced bot log not found"}

        enhanced_log = load_json(ENHANCED_BOT_LOG_PATH)
        today = today_str()

        if today in enhanced_log and enhanced_log[today]:
            latest_entry = enhanced_log[today][-1]  # Get most recent entry
            return latest_entry.get("metrics", {})

        return {"error": "No today's enhanced bot data"}

    except Exception as e:
        return {"error": f"Error extracting bot metrics: {e}"}


def extract_health_data() -> Dict[str, Any]:
    """Extract API health data from health logs."""
    try:
        if not HEALTH_LOG_PATH.exists():
            return {"error": "Health log not found"}

        health_log = load_json(HEALTH_LOG_PATH)
        today = today_str()

        if today in health_log and health_log[today]:
            latest_health = health_log[today][-1]  # Get most recent health check
            return latest_health

        return {"error": "No today's health data"}

    except Exception as e:
        return {"error": f"Error extracting health data: {e}"}


def execute_paperclip_monitoring() -> Dict[str, Any]:
    """Execute APU-49 Paperclip monitoring and capture results."""
    print("[EXEC] Starting Paperclip department monitoring (APU-49)...")

    try:
        from apu49_paperclip_engagement_monitor import (
            analyze_department_specific_engagement,
            route_to_paperclip_departments,
            generate_executive_summary,
            determine_overall_organizational_status
        )

        # Get department analytics
        department_analytics = analyze_department_specific_engagement()

        # Get routing actions
        routing_actions = route_to_paperclip_departments(department_analytics)

        # Get overall organizational status
        overall_status = determine_overall_organizational_status(department_analytics)

        paperclip_result = {
            "execution_time": datetime.now().isoformat(),
            "success": True,
            "department_analytics": department_analytics,
            "routing_actions": routing_actions,
            "overall_status": overall_status,
            "errors": []
        }

        print(f"[OK] Paperclip monitoring completed - Status: {overall_status}")
        return paperclip_result

    except Exception as e:
        print(f"[ERROR] Paperclip monitoring failed: {e}")
        return {
            "execution_time": datetime.now().isoformat(),
            "success": False,
            "errors": [f"Paperclip monitoring error: {str(e)}"]
        }


def integrate_system_data(bot_result: Dict, paperclip_result: Dict) -> Dict[str, Any]:
    """Integrate data from both systems into unified view."""

    integration = {
        "timestamp": datetime.now().isoformat(),
        "integration_version": "apu52_unified_v1",
        "system_coordination": {
            "bot_execution": bot_result["success"],
            "paperclip_monitoring": paperclip_result["success"],
            "data_integration_status": "healthy",
            "coordination_errors": []
        },
        "unified_metrics": {},
        "department_coordination": {},
        "organizational_health": {},
        "alerts": [],
        "recommendations": []
    }

    # Integrate bot metrics with department data
    if bot_result["success"] and paperclip_result["success"]:
        bot_metrics = bot_result.get("bot_metrics", {})
        health_data = bot_result.get("health_data", {})
        department_analytics = paperclip_result.get("department_analytics", {})

        # Create unified metrics combining both systems
        integration["unified_metrics"] = {
            "engagement_bot": {
                "likes": bot_metrics.get("likes", 0),
                "follows": bot_metrics.get("follows", 0),
                "errors": bot_metrics.get("errors", 0),
                "api_health": health_data.get("available", False),
                "response_time_ms": health_data.get("response_time_ms", 0),
                "search_term": bot_metrics.get("search_term", "unknown"),
                "posts_processed": bot_metrics.get("posts_processed", 0),
                "effectiveness": calculate_bot_effectiveness(bot_metrics)
            },
            "department_health": {
                dept_key: analytics.get("department_health_score", 0.0)
                for dept_key, analytics in department_analytics.items()
                if dept_key != "chairman"
            },
            "organizational": {
                "overall_health": department_analytics.get("chairman", {}).get("overall_organizational_health", 0.0),
                "urgent_issues": department_analytics.get("chairman", {}).get("total_urgent_issues", 0),
                "departments_at_risk": len(department_analytics.get("chairman", {}).get("departments_at_risk", []))
            }
        }

        # Coordinate department actions with bot performance
        integration["department_coordination"] = coordinate_department_actions(
            bot_metrics, department_analytics, paperclip_result.get("routing_actions", {})
        )

        # Generate unified alerts
        integration["alerts"] = generate_unified_alerts(integration["unified_metrics"])

        # Generate unified recommendations
        integration["recommendations"] = generate_unified_recommendations(integration["unified_metrics"])

    else:
        integration["system_coordination"]["data_integration_status"] = "degraded"
        if not bot_result["success"]:
            integration["system_coordination"]["coordination_errors"].extend(bot_result.get("errors", []))
        if not paperclip_result["success"]:
            integration["system_coordination"]["coordination_errors"].extend(paperclip_result.get("errors", []))

    return integration


def calculate_bot_effectiveness(bot_metrics: Dict) -> float:
    """Calculate engagement bot effectiveness score."""
    if not bot_metrics:
        return 0.0

    likes = bot_metrics.get("likes", 0)
    errors = bot_metrics.get("errors", 0)
    posts_processed = bot_metrics.get("posts_processed", 0)

    if posts_processed == 0:
        return 0.0

    # Calculate effectiveness based on success rate and engagement ratio
    success_rate = max(0, 1 - (errors / max(1, likes + errors)))
    engagement_rate = likes / posts_processed if posts_processed > 0 else 0

    # Weight both factors
    effectiveness = (success_rate * 0.6) + (min(1.0, engagement_rate * 4) * 0.4)

    return effectiveness


def coordinate_department_actions(bot_metrics: Dict, department_analytics: Dict, routing_actions: Dict) -> Dict[str, Any]:
    """Coordinate department actions based on bot performance and engagement data."""
    coordination = {
        "bot_performance_impact": {},
        "department_action_priorities": {},
        "cross_system_recommendations": []
    }

    bot_effectiveness = calculate_bot_effectiveness(bot_metrics)
    api_health = bot_metrics.get("api_health", {}).get("available", False)

    # Assess impact of bot performance on departments
    if bot_effectiveness < COORDINATION_THRESHOLDS["engagement_effectiveness_threshold"]:
        coordination["cross_system_recommendations"].append(
            "PRIORITY: Engagement bot effectiveness below threshold - review strategy and targeting"
        )

        # Prioritize A&R and Creative & Revenue for strategy review
        coordination["bot_performance_impact"]["a_and_r"] = {
            "impact_level": "high",
            "reason": "Low bot effectiveness impacts artist discovery and audience engagement",
            "recommended_action": "Review search terms and engagement strategy"
        }

        coordination["bot_performance_impact"]["creative_revenue"] = {
            "impact_level": "medium",
            "reason": "Poor engagement effectiveness may reduce campaign reach",
            "recommended_action": "Analyze engagement data for campaign optimization"
        }

    if not api_health:
        coordination["cross_system_recommendations"].append(
            "CRITICAL: API health issues detected - operations team review required"
        )

        coordination["bot_performance_impact"]["operations"] = {
            "impact_level": "critical",
            "reason": "API health issues prevent automated engagement",
            "recommended_action": "Immediate technical review and system health check"
        }

    # Prioritize department actions based on unified data
    for dept_key, routing in routing_actions.items():
        if routing.get("action_required", False):
            coordination["department_action_priorities"][dept_key] = {
                "priority": routing.get("priority", "medium"),
                "bot_context": {
                    "effectiveness": bot_effectiveness,
                    "api_health": api_health,
                    "recent_activity": bot_metrics.get("likes", 0) + bot_metrics.get("follows", 0)
                },
                "recommended_timing": "immediate" if routing.get("priority") == "high" else "within_24h"
            }

    return coordination


def generate_unified_alerts(unified_metrics: Dict) -> List[Dict[str, Any]]:
    """Generate alerts based on unified system metrics."""
    alerts = []

    org_health = unified_metrics.get("organizational", {}).get("overall_health", 0.0)
    bot_effectiveness = unified_metrics.get("engagement_bot", {}).get("effectiveness", 0.0)
    api_health = unified_metrics.get("engagement_bot", {}).get("api_health", False)
    urgent_issues = unified_metrics.get("organizational", {}).get("urgent_issues", 0)

    # Critical organizational health
    if org_health < COORDINATION_THRESHOLDS["organizational_health_critical"]:
        alerts.append({
            "type": "organizational_health_critical",
            "severity": "critical",
            "system": "unified",
            "message": f"Organizational health critical at {org_health:.1%} - immediate intervention required",
            "components_affected": ["paperclip_monitoring", "all_departments"],
            "recommended_action": "Emergency department head meeting and strategic review"
        })

    # API health degradation
    if not api_health:
        alerts.append({
            "type": "api_health_failure",
            "severity": "high",
            "system": "engagement_bot",
            "message": "Engagement bot API health failure - automated engagement disabled",
            "components_affected": ["engagement_bot", "community_growth"],
            "recommended_action": "Technical review and API connectivity diagnosis"
        })

    # Low bot effectiveness
    if bot_effectiveness < COORDINATION_THRESHOLDS["engagement_effectiveness_threshold"]:
        alerts.append({
            "type": "engagement_effectiveness_low",
            "severity": "medium",
            "system": "engagement_bot",
            "message": f"Bot effectiveness at {bot_effectiveness:.1%} - strategy review needed",
            "components_affected": ["engagement_bot", "a_and_r", "creative_revenue"],
            "recommended_action": "Review search terms, targeting strategy, and engagement timing"
        })

    # High urgent issue volume
    if urgent_issues >= COORDINATION_THRESHOLDS["department_escalation_threshold"]:
        alerts.append({
            "type": "high_urgent_issue_volume",
            "severity": "high",
            "system": "paperclip_monitoring",
            "message": f"{urgent_issues} urgent issues across departments require attention",
            "components_affected": ["paperclip_monitoring", "multiple_departments"],
            "recommended_action": "Coordinate cross-department response and escalation"
        })

    return alerts


def generate_unified_recommendations(unified_metrics: Dict) -> List[str]:
    """Generate actionable recommendations based on unified system analysis."""
    recommendations = []

    bot_metrics = unified_metrics.get("engagement_bot", {})
    org_metrics = unified_metrics.get("organizational", {})
    dept_health = unified_metrics.get("department_health", {})

    # Bot performance recommendations
    if bot_metrics.get("effectiveness", 0) < 0.7:
        recommendations.append("Optimize engagement bot search terms and targeting strategy")
        recommendations.append("Review engagement timing to align with peak community activity")

    if bot_metrics.get("response_time_ms", 0) > 2000:
        recommendations.append("Investigate API performance - response times above optimal threshold")

    # Organizational recommendations
    if org_metrics.get("overall_health", 0) < 0.6:
        recommendations.append("Schedule department head coordination meeting")
        recommendations.append("Review resource allocation across departments")

    # Department-specific recommendations
    low_health_depts = [dept for dept, health in dept_health.items() if health < 0.5]
    if low_health_depts:
        dept_names = ", ".join(low_health_depts).replace("_", " ").title()
        recommendations.append(f"Priority attention needed for departments: {dept_names}")

    # Integration recommendations
    if not recommendations:
        recommendations.append("Systems operating within normal parameters - maintain current strategy")
        recommendations.append("Consider proactive optimization opportunities for continued improvement")

    return recommendations


def generate_unified_dashboard(integration_data: Dict) -> str:
    """Generate unified dashboard combining all engagement systems."""

    unified_metrics = integration_data.get("unified_metrics", {})
    coordination = integration_data.get("system_coordination", {})
    alerts = integration_data.get("alerts", [])

    dashboard = []
    dashboard.append("=" * 100)
    dashboard.append("[*] VAWN UNIFIED ENGAGEMENT MONITOR - APU-52")
    dashboard.append("[*] Coordinated Bot Execution + Paperclip Department Integration")
    dashboard.append(f"[DATE] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    dashboard.append("=" * 100)

    # System Coordination Status
    dashboard.append(f"\n[SYSTEM COORDINATION] APU-50 + APU-49 Integration:")
    bot_status = "[OK] ACTIVE" if coordination.get("bot_execution", False) else "[FAIL] FAILED"
    paperclip_status = "[OK] ACTIVE" if coordination.get("paperclip_monitoring", False) else "[FAIL] FAILED"
    integration_status = coordination.get("data_integration_status", "unknown").upper()

    dashboard.append(f"  * Enhanced Bot (APU-50): {bot_status}")
    dashboard.append(f"  * Paperclip Monitor (APU-49): {paperclip_status}")
    dashboard.append(f"  * Data Integration: {integration_status}")

    # Unified Metrics Summary
    dashboard.append(f"\n[ENGAGEMENT METRICS] Combined System Performance:")

    if "engagement_bot" in unified_metrics:
        bot = unified_metrics["engagement_bot"]
        dashboard.append(f"  [BOT] Bot Activity: {bot.get('likes', 0)} likes, {bot.get('follows', 0)} follows")
        dashboard.append(f"     Effectiveness: {bot.get('effectiveness', 0):.1%} | API Health: {'[OK]' if bot.get('api_health', False) else '[FAIL]'}")
        dashboard.append(f"     Search Term: '{bot.get('search_term', 'N/A')}' | Posts: {bot.get('posts_processed', 0)}")

    if "organizational" in unified_metrics:
        org = unified_metrics["organizational"]
        dashboard.append(f"  [ORG] Organization: Health {org.get('overall_health', 0):.1%} | Urgent Issues: {org.get('urgent_issues', 0)}")
        dashboard.append(f"     Departments at Risk: {org.get('departments_at_risk', 0)}")

    # Department Health Matrix
    dashboard.append(f"\n[DEPARTMENT HEALTH] Apulu Records Status:")

    dept_names = {
        "legal": "Legal (Nelly)",
        "a_and_r": "A&R (Timbo)",
        "creative_revenue": "Creative & Revenue (Letitia)",
        "operations": "Operations (Nari)"
    }

    for dept_key, dept_name in dept_names.items():
        if dept_key in unified_metrics.get("department_health", {}):
            health = unified_metrics["department_health"][dept_key]
            status_icon = "[OK]" if health > 0.7 else "[WARN]" if health > 0.4 else "[FAIL]"
            dashboard.append(f"  {status_icon} {dept_name}: {health:.1%}")

    # Unified Alerts
    if alerts:
        dashboard.append(f"\n[UNIFIED ALERTS] Cross-System Notifications:")
        for alert in alerts[:5]:  # Show top 5 alerts
            severity_icon = {"critical": "[CRITICAL]", "high": "[HIGH]", "medium": "[INFO]"}.get(alert.get("severity", "medium"), "[INFO]")
            dashboard.append(f"  {severity_icon} {alert.get('message', 'Unknown alert')}")

    # Coordination Actions
    if "department_coordination" in integration_data:
        coord = integration_data["department_coordination"]
        if coord.get("cross_system_recommendations"):
            dashboard.append(f"\n[COORDINATION] Cross-System Actions:")
            for rec in coord["cross_system_recommendations"][:3]:
                dashboard.append(f"  * {rec}")

    dashboard.append(f"\n" + "=" * 100)
    return "\n".join(dashboard)


def save_unified_monitoring_report(integration_data: Dict, bot_result: Dict, paperclip_result: Dict):
    """Save comprehensive unified monitoring report."""

    # Main unified report
    report = {
        "timestamp": datetime.now().isoformat(),
        "version": "apu52_unified_v1",
        "system_integration": integration_data.get("system_coordination", {}),
        "unified_metrics": integration_data.get("unified_metrics", {}),
        "department_coordination": integration_data.get("department_coordination", {}),
        "alerts": integration_data.get("alerts", []),
        "recommendations": integration_data.get("recommendations", []),
        "component_results": {
            "enhanced_bot": bot_result,
            "paperclip_monitoring": paperclip_result
        },
        "coordination_effectiveness": calculate_coordination_effectiveness(integration_data)
    }

    # Save main unified monitoring log
    unified_log = load_json(UNIFIED_MONITOR_LOG) if UNIFIED_MONITOR_LOG.exists() else {}
    today = today_str()

    if today not in unified_log:
        unified_log[today] = []

    unified_log[today].append(report)

    # Keep only last 30 days
    cutoff_date = (datetime.now() - timedelta(days=30)).date()
    unified_log = {
        k: v for k, v in unified_log.items()
        if datetime.fromisoformat(k + "T00:00:00").date() >= cutoff_date
    }

    save_json(UNIFIED_MONITOR_LOG, unified_log)

    # Save coordination log for system health tracking
    coordination_entry = {
        "timestamp": datetime.now().isoformat(),
        "bot_execution": bot_result["success"],
        "paperclip_monitoring": paperclip_result["success"],
        "data_integration": integration_data["system_coordination"]["data_integration_status"],
        "coordination_errors": integration_data["system_coordination"]["coordination_errors"],
        "effectiveness": report["coordination_effectiveness"]
    }

    coord_log = load_json(COORDINATION_LOG) if COORDINATION_LOG.exists() else []
    coord_log.append(coordination_entry)

    # Keep only last 1000 entries
    if len(coord_log) > 1000:
        coord_log = coord_log[-1000:]

    save_json(COORDINATION_LOG, coord_log)

    # Save unified report file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unified_report_path = UNIFIED_REPORTS_DIR / f"unified_engagement_report_{timestamp}.json"
    save_json(unified_report_path, report)

    return report


def calculate_coordination_effectiveness(integration_data: Dict) -> float:
    """Calculate effectiveness of system coordination."""
    score = 0.0

    coordination = integration_data.get("system_coordination", {})

    # Component execution success
    if coordination.get("bot_execution", False):
        score += 0.3
    if coordination.get("paperclip_monitoring", False):
        score += 0.3

    # Data integration quality
    integration_status = coordination.get("data_integration_status", "degraded")
    if integration_status == "healthy":
        score += 0.3
    elif integration_status == "degraded":
        score += 0.15

    # Error handling
    error_count = len(coordination.get("coordination_errors", []))
    error_penalty = min(0.1, error_count * 0.025)
    score = max(0, score - error_penalty)

    return score


def main():
    """APU-52 Unified Engagement Monitor main function."""
    print("\n[*] Vawn Unified Engagement Monitor - APU-52 Starting...")
    print("[*] Coordinating Enhanced Bot (APU-50) + Paperclip Monitor (APU-49)...")

    # Step 1: Execute enhanced engagement bot (APU-50)
    print("\n" + "="*60)
    print("[PHASE 1] Enhanced Engagement Bot Execution")
    print("="*60)

    bot_result = execute_enhanced_engagement_bot()

    # Step 2: Execute Paperclip monitoring (APU-49)
    print("\n" + "="*60)
    print("[PHASE 2] Paperclip Department Monitoring")
    print("="*60)

    paperclip_result = execute_paperclip_monitoring()

    # Step 3: Integrate systems and generate unified view
    print("\n" + "="*60)
    print("[PHASE 3] System Integration & Coordination")
    print("="*60)

    integration_data = integrate_system_data(bot_result, paperclip_result)

    # Step 4: Generate unified dashboard
    print("\n" + "="*60)
    print("[PHASE 4] Unified Dashboard Generation")
    print("="*60)

    dashboard = generate_unified_dashboard(integration_data)
    print(dashboard)

    # Step 5: Save comprehensive reports
    report = save_unified_monitoring_report(integration_data, bot_result, paperclip_result)

    # Final logging and status
    coordination_status = integration_data["system_coordination"]["data_integration_status"]
    coordination_effectiveness = report["coordination_effectiveness"]
    total_alerts = len(integration_data.get("alerts", []))

    status = "ok" if coordination_status == "healthy" and coordination_effectiveness > 0.8 else "warning" if coordination_status == "degraded" else "error"
    detail = f"Coord: {coordination_effectiveness:.1%}, Status: {coordination_status}, Alerts: {total_alerts}"

    log_run("UnifiedEngagementMonitorAPU52", status, detail)

    print(f"\n[APU-52] Unified monitoring complete - Coordination: {coordination_effectiveness:.1%}")
    print(f"[APU-52] System status: {coordination_status.upper()}")
    print(f"[APU-52] Active alerts: {total_alerts}")

    return report


if __name__ == "__main__":
    try:
        report = main()

        # Exit based on system coordination health
        coordination_effectiveness = report.get("coordination_effectiveness", 0.0)
        system_status = report.get("system_integration", {}).get("data_integration_status", "unknown")

        if system_status == "degraded" or coordination_effectiveness < 0.5:
            print("\n[WARNING] System coordination needs attention")
            sys.exit(1)
        elif coordination_effectiveness < 0.3:
            print("\n[CRITICAL] System coordination failure - immediate attention required")
            sys.exit(2)
        else:
            print("\n[OK] Unified engagement monitoring systems operating effectively")
            sys.exit(0)

    except Exception as e:
        print(f"\n[CRITICAL] Unified monitor failure: {e}")
        log_run("UnifiedEngagementMonitorAPU52", "error", f"Critical failure: {str(e)[:100]}")
        sys.exit(2)