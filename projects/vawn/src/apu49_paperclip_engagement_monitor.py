"""
apu49_paperclip_engagement_monitor.py — APU-49 Paperclip-Integrated Engagement Monitor

Department-aware engagement monitoring system integrated with Apulu Records' Paperclip infrastructure.
Builds upon APU-48 community features with department routing and organizational workflow integration.

Created by: Dex - Community Agent (APU-49)

Enhancements over APU-48:
- Paperclip department integration (Legal, A&R, Creative & Revenue, COO)
- Department-specific engagement routing and alerts
- Organizational workflow coordination
- Multi-department collaboration tracking
- Executive dashboard for chairman (Clu) oversight
"""

import json
import sys
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import (
    load_json, save_json, ENGAGEMENT_LOG, RESEARCH_LOG, METRICS_LOG,
    VAWN_DIR, log_run, today_str, get_anthropic_client
)

# Import APU-48 functions
sys.path.insert(0, r"C:\Users\rdyal\Vawn\src")
try:
    from apu48_community_engagement_monitor import (
        analyze_community_health, detect_community_trends,
        generate_community_recommendations, COMMUNITY_THRESHOLDS
    )
except ImportError:
    print("[WARNING] APU-48 functions not available - using fallback methods")

# Configuration
MONITOR_LOG = VAWN_DIR / "research" / "apu49_paperclip_engagement_monitor_log.json"
DEPARTMENT_REPORTS_DIR = VAWN_DIR / "research" / "department_reports"
DEPARTMENT_REPORTS_DIR.mkdir(exist_ok=True)

# Apulu Records Department Structure (from Paperclip integration memory)
DEPARTMENTS = {
    "chairman": {
        "head": "Clu",
        "role": "Chairman of the Board / Creative Director",
        "focus": ["strategic_oversight", "creative_direction", "final_decisions"],
        "engagement_priorities": ["overall_brand", "strategic_partnerships", "crisis_management"]
    },
    "legal": {
        "head": "Nelly",
        "role": "Head of Legal",
        "focus": ["copyright", "licensing", "compliance", "contracts"],
        "engagement_priorities": ["copyright_claims", "dmca_issues", "legal_mentions", "compliance_risks"]
    },
    "a_and_r": {
        "head": "Timbo",
        "role": "President of A&R",
        "focus": ["artist_development", "music_discovery", "talent_scouting"],
        "engagement_priorities": ["artist_feedback", "music_discovery", "talent_identification", "industry_trends"]
    },
    "creative_revenue": {
        "head": "Letitia",
        "role": "President Creative & Revenue",
        "focus": ["marketing", "revenue_optimization", "creative_campaigns"],
        "engagement_priorities": ["conversion_tracking", "revenue_metrics", "campaign_performance", "brand_alignment"]
    },
    "operations": {
        "head": "Nari",
        "role": "COO",
        "focus": ["operational_efficiency", "resource_management", "workflow_optimization"],
        "engagement_priorities": ["process_improvement", "resource_allocation", "system_health", "productivity_metrics"]
    }
}

# Department-specific engagement thresholds
DEPARTMENT_THRESHOLDS = {
    "legal": {
        "urgent_keywords": ["copyright", "dmca", "takedown", "lawsuit", "infringement"],
        "response_time_hours": 2,  # Legal issues need fast response
        "escalation_threshold": 1  # Single legal mention escalates
    },
    "a_and_r": {
        "urgent_keywords": ["demo", "submission", "talent", "collaboration", "feature"],
        "response_time_hours": 24,
        "escalation_threshold": 3
    },
    "creative_revenue": {
        "urgent_keywords": ["conversion", "sales", "revenue", "campaign", "brand"],
        "response_time_hours": 6,
        "escalation_threshold": 5
    },
    "operations": {
        "urgent_keywords": ["system", "down", "broken", "error", "problem"],
        "response_time_hours": 4,
        "escalation_threshold": 2
    }
}


def analyze_department_specific_engagement() -> Dict[str, Any]:
    """Analyze engagement metrics specific to each department's priorities."""
    try:
        engagement_log = load_json(ENGAGEMENT_LOG)
        recent_engagement = get_recent_engagement_data(engagement_log, days=7)

        department_analytics = {}

        for dept_key, dept_info in DEPARTMENTS.items():
            if dept_key == "chairman":  # Chairman gets aggregate view
                continue

            dept_analytics = {
                "total_relevant_interactions": 0,
                "urgent_issues": [],
                "response_times": [],
                "department_health_score": 0.0,
                "key_topics": [],
                "recommendations": [],
                "alerts": []
            }

            # Analyze interactions relevant to this department
            for entry in recent_engagement:
                comment_text = entry.get("comment", "").lower()
                reply_text = entry.get("reply", "").lower()

                # Check for department-relevant keywords
                dept_priorities = dept_info.get("engagement_priorities", [])
                relevance_score = 0

                for priority in dept_priorities:
                    if priority.replace("_", " ") in comment_text:
                        relevance_score += 1
                        dept_analytics["total_relevant_interactions"] += 1

                # Check for urgent keywords
                urgent_keywords = DEPARTMENT_THRESHOLDS.get(dept_key, {}).get("urgent_keywords", [])
                for keyword in urgent_keywords:
                    if keyword in comment_text:
                        dept_analytics["urgent_issues"].append({
                            "keyword": keyword,
                            "comment": comment_text[:100],
                            "timestamp": entry.get("date"),
                            "platform": entry.get("platform", "unknown")
                        })

                # Calculate response time for relevant interactions
                if relevance_score > 0 and entry.get("date") and entry.get("reply_date"):
                    try:
                        comment_time = datetime.fromisoformat(entry["date"])
                        reply_time = datetime.fromisoformat(entry["reply_date"])
                        response_time = (reply_time - comment_time).total_seconds() / 3600  # hours
                        dept_analytics["response_times"].append(response_time)
                    except:
                        pass

            # Calculate department health score
            dept_analytics["department_health_score"] = calculate_department_health(
                dept_analytics, dept_key
            )

            # Generate department-specific recommendations
            dept_analytics["recommendations"] = generate_department_recommendations(
                dept_analytics, dept_key
            )

            # Generate alerts for urgent issues
            dept_analytics["alerts"] = generate_department_alerts(
                dept_analytics, dept_key
            )

            department_analytics[dept_key] = dept_analytics

        # Generate chairman's executive summary
        department_analytics["chairman"] = generate_executive_summary(department_analytics)

        return department_analytics

    except Exception as e:
        return {"error": str(e), "timestamp": datetime.now().isoformat()}


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


def calculate_department_health(dept_analytics: Dict, dept_key: str) -> float:
    """Calculate health score specific to department priorities."""
    score = 0.0

    # Response time score
    response_times = dept_analytics.get("response_times", [])
    if response_times:
        avg_response_time = sum(response_times) / len(response_times)
        target_response_time = DEPARTMENT_THRESHOLDS.get(dept_key, {}).get("response_time_hours", 12)
        response_score = max(0, 1 - (avg_response_time / target_response_time))
        score += response_score * 0.4
    else:
        score += 0.2  # Neutral if no data

    # Urgent issue management score
    urgent_issues = len(dept_analytics.get("urgent_issues", []))
    escalation_threshold = DEPARTMENT_THRESHOLDS.get(dept_key, {}).get("escalation_threshold", 5)
    urgency_score = max(0, 1 - (urgent_issues / escalation_threshold))
    score += urgency_score * 0.3

    # Interaction volume score (normalized)
    interactions = dept_analytics.get("total_relevant_interactions", 0)
    interaction_score = min(1.0, interactions / 10)  # Scale of 10 interactions = perfect
    score += interaction_score * 0.3

    return min(score, 1.0)


def generate_department_recommendations(dept_analytics: Dict, dept_key: str) -> List[str]:
    """Generate actionable recommendations for specific departments."""
    recommendations = []
    dept_info = DEPARTMENTS.get(dept_key, {})

    urgent_issues = len(dept_analytics.get("urgent_issues", []))
    response_times = dept_analytics.get("response_times", [])
    interactions = dept_analytics.get("total_relevant_interactions", 0)

    if urgent_issues > 0:
        recommendations.append(f"URGENT: {urgent_issues} issues requiring {dept_info.get('head')} attention")
        if dept_key == "legal":
            recommendations.append("Immediate legal review required - potential compliance risk")
        elif dept_key == "a_and_r":
            recommendations.append("Artist/talent opportunities identified - schedule review meeting")

    if response_times and sum(response_times) / len(response_times) > DEPARTMENT_THRESHOLDS.get(dept_key, {}).get("response_time_hours", 12):
        recommendations.append(f"Improve response times - currently averaging {sum(response_times)/len(response_times):.1f}h")

    if interactions < 3:
        if dept_key == "legal":
            recommendations.append("Monitor for copyright and legal mentions more actively")
        elif dept_key == "a_and_r":
            recommendations.append("Increase monitoring of artist discovery and demo submissions")
        elif dept_key == "creative_revenue":
            recommendations.append("Track campaign performance and conversion metrics more closely")
        elif dept_key == "operations":
            recommendations.append("Monitor system health and operational feedback")

    if not recommendations:
        recommendations.append(f"Department operating within normal parameters for {dept_info.get('focus', [])}")

    return recommendations


def generate_department_alerts(dept_analytics: Dict, dept_key: str) -> List[Dict]:
    """Generate alerts for department-specific issues."""
    alerts = []

    urgent_issues = dept_analytics.get("urgent_issues", [])
    escalation_threshold = DEPARTMENT_THRESHOLDS.get(dept_key, {}).get("escalation_threshold", 5)

    if len(urgent_issues) >= escalation_threshold:
        alerts.append({
            "type": "escalation_required",
            "severity": "high",
            "message": f"{len(urgent_issues)} urgent issues require {DEPARTMENTS[dept_key]['head']} escalation",
            "department": dept_key,
            "issues": urgent_issues[:3]  # Show first 3 issues
        })

    response_times = dept_analytics.get("response_times", [])
    if response_times:
        avg_response = sum(response_times) / len(response_times)
        target = DEPARTMENT_THRESHOLDS.get(dept_key, {}).get("response_time_hours", 12)
        if avg_response > target * 1.5:  # 50% over target
            alerts.append({
                "type": "slow_response",
                "severity": "medium",
                "message": f"Response times averaging {avg_response:.1f}h (target: {target}h)",
                "department": dept_key
            })

    return alerts


def generate_executive_summary(department_analytics: Dict) -> Dict[str, Any]:
    """Generate executive summary for chairman oversight."""
    total_urgent_issues = 0
    departments_at_risk = []
    overall_health_scores = []

    for dept_key, analytics in department_analytics.items():
        if dept_key == "chairman":
            continue

        urgent_count = len(analytics.get("urgent_issues", []))
        health_score = analytics.get("department_health_score", 0.0)

        total_urgent_issues += urgent_count
        overall_health_scores.append(health_score)

        if health_score < 0.6:
            departments_at_risk.append({
                "department": dept_key,
                "head": DEPARTMENTS[dept_key]["head"],
                "health_score": health_score,
                "urgent_issues": urgent_count
            })

    avg_health = sum(overall_health_scores) / len(overall_health_scores) if overall_health_scores else 0

    return {
        "overall_organizational_health": avg_health,
        "total_urgent_issues": total_urgent_issues,
        "departments_at_risk": departments_at_risk,
        "strategic_recommendations": generate_strategic_recommendations(avg_health, departments_at_risk),
        "executive_alerts": generate_executive_alerts(avg_health, total_urgent_issues)
    }


def generate_strategic_recommendations(avg_health: float, departments_at_risk: List[Dict]) -> List[str]:
    """Generate strategic recommendations for chairman."""
    recommendations = []

    if avg_health < 0.5:
        recommendations.append("CRITICAL: Multiple departments require immediate attention")
        recommendations.append("Consider emergency department head meeting")

    if len(departments_at_risk) > 0:
        dept_names = [d["head"] for d in departments_at_risk]
        recommendations.append(f"Schedule 1:1 with department heads: {', '.join(dept_names)}")

    if avg_health > 0.8:
        recommendations.append("Organization performing well - consider expansion opportunities")
        recommendations.append("Review department resource allocation for optimization")

    return recommendations


def generate_executive_alerts(avg_health: float, total_urgent_issues: int) -> List[Dict]:
    """Generate executive-level alerts."""
    alerts = []

    if total_urgent_issues > 5:
        alerts.append({
            "type": "high_urgency_volume",
            "severity": "high",
            "message": f"{total_urgent_issues} urgent issues across departments require executive attention"
        })

    if avg_health < 0.4:
        alerts.append({
            "type": "organizational_health_critical",
            "severity": "critical",
            "message": f"Organizational health at {avg_health:.1%} - immediate intervention required"
        })

    return alerts


def route_to_paperclip_departments(department_analytics: Dict) -> Dict[str, Any]:
    """Route department-specific findings to Paperclip agent coordination."""
    routing_actions = {}

    for dept_key, analytics in department_analytics.items():
        if dept_key == "chairman":
            continue

        alerts = analytics.get("alerts", [])
        urgent_issues = analytics.get("urgent_issues", [])

        if alerts or urgent_issues:
            routing_actions[dept_key] = {
                "department_head": DEPARTMENTS[dept_key]["head"],
                "priority": "high" if len(urgent_issues) > 0 else "medium",
                "action_required": True,
                "paperclip_routing": {
                    "agent_type": f"department_{dept_key}",
                    "task_priority": "urgent" if len(urgent_issues) > 0 else "normal",
                    "context": {
                        "alerts": alerts,
                        "urgent_issues": urgent_issues,
                        "recommendations": analytics.get("recommendations", [])
                    }
                }
            }

    return routing_actions


def generate_apu49_dashboard() -> str:
    """Generate APU-49 Paperclip-integrated dashboard."""

    # Get APU-48 community analysis (if available)
    try:
        community_health = analyze_community_health()
        trends = detect_community_trends()
    except Exception as e:
        community_health = {"overall_score": 0.0, "status": "unavailable", "error": str(e)}
        trends = {"trending_topics": [], "error": str(e)}

    # Get APU-49 department analysis
    department_analytics = analyze_department_specific_engagement()

    dashboard = []
    dashboard.append("=" * 90)
    dashboard.append("[*] VAWN PAPERCLIP ENGAGEMENT MONITOR - APU-49")
    dashboard.append("[*] Apulu Records Department Integration")
    dashboard.append(f"[DATE] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    dashboard.append("=" * 90)

    # Executive Summary (Chairman View)
    if "chairman" in department_analytics:
        exec_summary = department_analytics["chairman"]
        org_health = exec_summary.get("overall_organizational_health", 0.0)
        urgent_issues = exec_summary.get("total_urgent_issues", 0)

        dashboard.append(f"\n[EXECUTIVE SUMMARY] Chairman (Clu) Dashboard:")
        dashboard.append(f"  • Organizational Health: {org_health:.1%}")
        dashboard.append(f"  • Total Urgent Issues: {urgent_issues}")
        dashboard.append(f"  • Departments at Risk: {len(exec_summary.get('departments_at_risk', []))}")

    # Department Status
    dashboard.append(f"\n[DEPARTMENT STATUS] Apulu Records Divisions:")

    for dept_key, dept_info in DEPARTMENTS.items():
        if dept_key == "chairman":
            continue

        analytics = department_analytics.get(dept_key, {})
        health_score = analytics.get("department_health_score", 0.0)
        urgent_count = len(analytics.get("urgent_issues", []))

        status_icon = "[OK]" if health_score > 0.7 else "[WARN]" if health_score > 0.4 else "[ERROR]"

        dashboard.append(f"  {status_icon} {dept_info['head']} ({dept_info['role']}):")
        dashboard.append(f"     Health: {health_score:.1%} | Urgent Issues: {urgent_count}")
        dashboard.append(f"     Focus: {', '.join(dept_info['focus'][:2])}")

    # Community Health (from APU-48)
    dashboard.append(f"\n[COMMUNITY HEALTH] APU-48 Integration:")
    community_score = community_health.get("overall_score", 0.0)
    community_status = community_health.get("status", "unknown")
    dashboard.append(f"  • Community Score: {community_score:.1%} ({community_status.upper()})")

    # Trending Topics
    trending_topics = trends.get("trending_topics", [])
    dashboard.append(f"  • Trending Topics: {len(trending_topics)}")
    if trending_topics:
        for topic in trending_topics[:3]:
            dashboard.append(f"    - {topic['topic']}: {topic['mentions']} mentions")

    # Paperclip Integration Status
    routing_actions = route_to_paperclip_departments(department_analytics)
    dashboard.append(f"\n[PAPERCLIP INTEGRATION] Department Routing:")
    dashboard.append(f"  • Active Department Routes: {len(routing_actions)}")

    for dept, action in routing_actions.items():
        priority_icon = "[HIGH]" if action["priority"] == "high" else "[MED]"
        dashboard.append(f"  {priority_icon} {DEPARTMENTS[dept]['head']} ({dept.upper()}): {action['priority']} priority")

    dashboard.append(f"\n" + "=" * 90)
    return "\n".join(dashboard)


def save_apu49_monitoring_report():
    """Save comprehensive APU-49 monitoring data with department breakdowns."""

    # Get all analytics
    try:
        community_health = analyze_community_health()
        trends = detect_community_trends()
    except:
        community_health = {"overall_score": 0.0, "status": "unavailable"}
        trends = {"trending_topics": []}

    department_analytics = analyze_department_specific_engagement()
    routing_actions = route_to_paperclip_departments(department_analytics)

    # Main report
    report = {
        "timestamp": datetime.now().isoformat(),
        "version": "apu49_paperclip_v1",
        "apulu_records_integration": True,
        "community_health": community_health,  # APU-48 data
        "trending_topics": trends,  # APU-48 data
        "department_analytics": department_analytics,  # APU-49 data
        "paperclip_routing": routing_actions,  # APU-49 data
        "executive_summary": department_analytics.get("chairman", {}),
        "overall_status": determine_overall_organizational_status(department_analytics)
    }

    # Save main monitoring log
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

    # Save individual department reports
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for dept_key, analytics in department_analytics.items():
        if dept_key != "chairman":
            dept_report_path = DEPARTMENT_REPORTS_DIR / f"{dept_key}_{timestamp}.json"
            dept_report = {
                "department": dept_key,
                "head": DEPARTMENTS[dept_key]["head"],
                "timestamp": datetime.now().isoformat(),
                "analytics": analytics,
                "routing": routing_actions.get(dept_key, {})
            }
            save_json(dept_report_path, dept_report)

    return report


def determine_overall_organizational_status(department_analytics: Dict) -> str:
    """Determine overall organizational status."""
    exec_summary = department_analytics.get("chairman", {})
    org_health = exec_summary.get("overall_organizational_health", 0.0)
    urgent_issues = exec_summary.get("total_urgent_issues", 0)

    if urgent_issues > 10 or org_health < 0.3:
        return "critical"
    elif urgent_issues > 5 or org_health < 0.5:
        return "warning"
    elif org_health > 0.8:
        return "excellent"
    else:
        return "healthy"


def main():
    """APU-49 Paperclip Engagement Monitor main function."""
    print("\n[*] Vawn Paperclip Engagement Monitor - APU-49 Starting...")
    print("[*] Integrating with Apulu Records Department Structure...")

    # Generate and display Paperclip-integrated dashboard
    dashboard = generate_apu49_dashboard()
    print(dashboard)

    # Save comprehensive monitoring report
    report = save_apu49_monitoring_report()

    # Enhanced logging with department and Paperclip integration
    exec_summary = report.get("executive_summary", {})
    org_health = exec_summary.get("overall_organizational_health", 0.0)
    total_urgent = exec_summary.get("total_urgent_issues", 0)
    overall_status = report.get("overall_status", "unknown")
    routing_count = len(report.get("paperclip_routing", {}))

    status = "ok" if overall_status in ["healthy", "excellent"] else "warning" if overall_status == "warning" else "error"
    detail = f"Org health: {org_health:.1%}, Urgent issues: {total_urgent}, Dept routes: {routing_count}, Status: {overall_status}"

    log_run("PaperclipEngagementMonitorAPU49", status, detail)

    print(f"\n[APU-49] Paperclip integration complete - Organizational Health: {org_health:.1%}")
    print(f"[APU-49] Department routing: {routing_count} active routes")

    return report


if __name__ == "__main__":
    report = main()

    # Exit based on overall organizational health
    overall_status = report.get("overall_status", "unknown")

    if overall_status == "critical":
        print("\n[CRITICAL] Organizational health requires immediate executive attention!")
        sys.exit(2)
    elif overall_status == "warning":
        print("\n[WARNING] Multiple departments need attention")
        sys.exit(1)
    else:
        print("\n[OK] Apulu Records departments operating within parameters")
        sys.exit(0)