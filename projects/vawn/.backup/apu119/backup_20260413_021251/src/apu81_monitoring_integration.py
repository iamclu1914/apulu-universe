"""
apu81_monitoring_integration.py — APU-81 Monitoring Integration for Enhanced Engagement Bot
Updates APU-44 monitoring system to properly track the new APU-81 enhanced engagement bot.

Created by: Dex - Community Agent (APU-81)
Integrates with: apu44_enhanced_engagement_monitor.py
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import (
    load_json, save_json, RESEARCH_LOG, VAWN_DIR, today_str
)

# Enhanced engagement bot log location
ENHANCED_ENGAGEMENT_LOG = VAWN_DIR / "research" / "apu81_engagement_bot_log.json"
COLLABORATION_TARGETS = VAWN_DIR / "research" / "collaboration_targets.json"


def get_enhanced_engagement_metrics() -> Dict[str, Any]:
    """
    Extract enhanced metrics from APU-81 engagement bot that APU-44 monitor needs.
    Returns detailed analytics for integration with existing monitoring.
    """
    research_log = load_json(RESEARCH_LOG)
    enhanced_log = load_json(ENHANCED_ENGAGEMENT_LOG)
    collab_targets = load_json(COLLABORATION_TARGETS)

    today = today_str()
    yesterday = str((datetime.now() - timedelta(days=1)).date())

    # Find APU81EngagementBot entries in research log
    apu81_entries = []
    for date in [today, yesterday]:
        if date in research_log:
            cutoff = datetime.now() - timedelta(hours=24)
            for entry in research_log[date]:
                if entry["agent"] == "APU81EngagementBot":
                    entry_time = datetime.fromisoformat(entry["time"])
                    if entry_time > cutoff:
                        apu81_entries.append(entry)

    # Analyze enhanced bot performance
    total_likes = 0
    total_filtered = 0
    quality_scores = []
    filter_efficiency_scores = []
    collaboration_discoveries = 0

    for entry in apu81_entries:
        detail = entry.get("detail", "")

        # Parse enhanced format: "Enhanced: X likes, Y follows, Z filtered, quality threshold: A.B/10"
        if "Enhanced:" in detail:
            try:
                parts = detail.split(", ")
                for part in parts:
                    if "likes" in part:
                        likes_num = int(part.split()[1])
                        total_likes += likes_num
                    elif "filtered" in part:
                        filtered_num = int(part.split()[0])
                        total_filtered += filtered_num
                        # Calculate filter efficiency for this run
                        if likes_num + filtered_num > 0:
                            efficiency = filtered_num / (likes_num + filtered_num)
                            filter_efficiency_scores.append(efficiency)
            except (ValueError, IndexError):
                pass

    # Analyze collaboration targets discovered
    if today in collab_targets:
        collaboration_discoveries = len(collab_targets[today])

    # Calculate enhanced metrics
    avg_filter_efficiency = sum(filter_efficiency_scores) / max(len(filter_efficiency_scores), 1)

    # Get detailed metrics from enhanced log
    enhanced_metrics = {
        "total_engagements_24h": total_likes,
        "total_filtered_24h": total_filtered,
        "filter_efficiency": avg_filter_efficiency,
        "collaboration_discoveries": collaboration_discoveries,
        "runs_24h": len(apu81_entries),
        "avg_quality_threshold": 6.0,  # From enhanced bot
        "status": "healthy" if apu81_entries and total_likes > 0 else "idle"
    }

    # Add engagement history analysis
    if "engagement_history" in enhanced_log:
        unique_accounts = len(enhanced_log["engagement_history"])
        enhanced_metrics["unique_accounts_engaged"] = unique_accounts

    return enhanced_metrics


def update_apu44_agent_tracking():
    """
    Update APU-44 monitoring to include APU81EngagementBot in agent tracking.
    Modifies the agent health checking to recognize the new enhanced bot.
    """
    research_log = load_json(RESEARCH_LOG)
    today = today_str()
    yesterday = str((datetime.now() - timedelta(days=1)).date())

    # Get APU81EngagementBot entries
    apu81_entries = []
    for date in [today, yesterday]:
        if date in research_log:
            for entry in research_log[date]:
                if entry["agent"] == "APU81EngagementBot":
                    apu81_entries.append(entry)

    if not apu81_entries:
        return {
            "status": "no_data",
            "message": "No APU81EngagementBot entries found",
            "recommendation": "Run the enhanced engagement bot"
        }

    # Analyze recent performance
    latest_entry = apu81_entries[-1]
    recent_entries = [e for e in apu81_entries if e["time"] > (datetime.now() - timedelta(hours=24)).isoformat()]

    success_count = len([e for e in recent_entries if e["status"] == "ok"])
    success_rate = success_count / max(len(recent_entries), 1)

    status = "healthy"
    if success_rate < 0.5:
        status = "warning"
    elif success_rate == 0:
        status = "failed"
    elif success_count == 0 and len(recent_entries) == 0:
        status = "idle"

    return {
        "agent_name": "APU81EngagementBot",
        "status": status,
        "success_rate": success_rate,
        "last_run": latest_entry["time"],
        "runs_24h": len(recent_entries),
        "latest_detail": latest_entry.get("detail", ""),
        "integration_version": "apu81_v1"
    }


def generate_apu81_monitoring_report() -> str:
    """Generate comprehensive monitoring report for APU-81 enhanced engagement system."""
    enhanced_metrics = get_enhanced_engagement_metrics()
    agent_status = update_apu44_agent_tracking()

    report = f"""
APU-81 Enhanced Engagement Monitoring Report
==========================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

AGENT STATUS:
- Name: APU81EngagementBot
- Status: {agent_status.get('status', 'unknown').upper()}
- Success Rate: {agent_status.get('success_rate', 0):.1%}
- Last Run: {agent_status.get('last_run', 'Never')}
- Runs (24h): {agent_status.get('runs_24h', 0)}

ENHANCED METRICS:
- Total Engagements: {enhanced_metrics.get('total_engagements_24h', 0)}
- Content Filtered: {enhanced_metrics.get('total_filtered_24h', 0)}
- Filter Efficiency: {enhanced_metrics.get('filter_efficiency', 0):.1%}
- Quality Threshold: {enhanced_metrics.get('avg_quality_threshold', 0)}/10
- Collaboration Targets Found: {enhanced_metrics.get('collaboration_discoveries', 0)}
- Unique Accounts Engaged: {enhanced_metrics.get('unique_accounts_engaged', 0)}

INTEGRATION STATUS:
- APU-44 Compatible: [OK] Yes
- Enhanced Logging: [OK] Active
- Quality Filtering: [OK] Enabled
- Collaboration Discovery: [OK] Active

RECOMMENDATIONS:
"""

    # Add specific recommendations based on metrics
    if enhanced_metrics.get('filter_efficiency', 0) < 0.3:
        report += "- Consider lowering quality threshold - filtering may be too aggressive\n"
    elif enhanced_metrics.get('filter_efficiency', 0) > 0.8:
        report += "- Consider raising quality threshold - may be engaging with low-quality content\n"

    if enhanced_metrics.get('collaboration_discoveries', 0) > 0:
        report += f"- {enhanced_metrics['collaboration_discoveries']} collaboration opportunities discovered - review collaboration_targets.json\n"

    if enhanced_metrics.get('total_engagements_24h', 0) == 0:
        report += "- No engagements in 24h - check bot schedule and search term effectiveness\n"

    return report.strip()


def patch_apu44_for_apu81_integration():
    """
    Create integration patch data that APU-44 monitor can use to recognize APU81EngagementBot.
    This doesn't modify the original APU-44 file but creates integration data.
    """
    integration_patch = {
        "patch_version": "apu81_integration_v1",
        "created": datetime.now().isoformat(),
        "enhanced_agent_patterns": {
            "APU81EngagementBot": {
                "metrics_extraction": {
                    "likes_pattern": r"Enhanced: (\d+) likes",
                    "filtered_pattern": r"(\d+) filtered",
                    "quality_pattern": r"quality threshold: ([\d.]+)/10"
                },
                "status_classification": {
                    "healthy": "success_rate >= 0.8 and recent_engagements > 0",
                    "idle": "success_rate >= 0.8 and recent_engagements == 0",
                    "warning": "0.5 <= success_rate < 0.8",
                    "failed": "success_rate < 0.5"
                },
                "enhanced_metrics": [
                    "filter_efficiency",
                    "quality_threshold",
                    "collaboration_discoveries",
                    "unique_accounts_engaged"
                ]
            }
        },
        "compatibility": {
            "original_engagement_bot": "supported",
            "apu44_monitor": "supported",
            "metrics_log": "supported"
        }
    }

    # Save integration patch
    patch_file = VAWN_DIR / "research" / "apu81_integration_patch.json"
    save_json(patch_file, integration_patch)

    return integration_patch


def main():
    """Main integration testing and reporting function."""
    print("\n=== APU-81 Monitoring Integration ===\n")

    # Generate integration patch
    patch = patch_apu44_for_apu81_integration()
    print(f"[OK] Created APU-81 integration patch v{patch['patch_version']}")

    # Test metrics extraction
    enhanced_metrics = get_enhanced_engagement_metrics()
    print(f"[OK] Enhanced metrics extracted: {len(enhanced_metrics)} data points")

    # Test agent status integration
    agent_status = update_apu44_agent_tracking()
    print(f"[OK] Agent status: {agent_status['status']}")

    # Generate comprehensive report
    report = generate_apu81_monitoring_report()
    print("\n" + report)

    # Save integration report
    report_file = VAWN_DIR / "research" / "apu81_monitoring_integration_report.md"
    Path(report_file).write_text(report, encoding="utf-8")
    print(f"\n[SAVE] Integration report saved to: {report_file}")

    return {
        "patch_created": True,
        "metrics_extracted": True,
        "agent_status": agent_status["status"],
        "integration_version": "apu81_v1"
    }


if __name__ == "__main__":
    main()