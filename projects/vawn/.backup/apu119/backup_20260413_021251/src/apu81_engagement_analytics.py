"""
apu81_engagement_analytics.py — APU-81 Engagement Analytics & ROI Tracking System
Comprehensive analytics and ROI tracking for Vawn's multi-platform engagement strategy.
Provides data-driven insights for optimizing community building and audience growth.

Created by: Dex - Community Agent (APU-81)
Integrates with: All APU-81 engagement systems
"""

import json
import sys
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import (
    VAWN_DIR, load_json, save_json, log_run, today_str, RESEARCH_LOG, METRICS_LOG
)

# Analytics configuration
ENGAGEMENT_ANALYTICS_LOG = VAWN_DIR / "research" / "apu81_engagement_analytics.json"
ROI_TRACKING_LOG = VAWN_DIR / "research" / "apu81_roi_tracking.json"
GROWTH_METRICS_LOG = VAWN_DIR / "research" / "apu81_growth_metrics.json"
PERFORMANCE_DASHBOARD = VAWN_DIR / "research" / "apu81_performance_dashboard.json"

# ROI calculation constants
HOURLY_VALUE_ESTIMATE = 50  # Estimated value of Vawn's time per hour
BASELINE_MANUAL_HOURS = 10  # Hours per week without automation

# Platform cost structure (monthly)
PLATFORM_COSTS = {
    "bluesky": 0,
    "x_twitter": 100,  # Basic API tier
    "youtube": 0,  # Free tier sufficient
    "instagram": 0,  # Manual only
    "tiktok": 0,  # Manual only
    "threads": 0   # Manual only
}

# Engagement value multipliers by platform
PLATFORM_VALUE_MULTIPLIERS = {
    "bluesky": 1.0,      # Baseline
    "x_twitter": 2.5,    # High reach and engagement
    "youtube": 2.0,      # High value for music artists
    "instagram": 3.0,    # High value but manual only
    "tiktok": 2.5,       # High viral potential
    "threads": 1.5       # Growing platform
}


class EngagementAnalytics:
    """Comprehensive engagement analytics and ROI tracking system."""

    def __init__(self):
        self.research_log = load_json(RESEARCH_LOG)
        self.metrics_log = load_json(METRICS_LOG)
        self.enhanced_engagement_log = load_json(VAWN_DIR / "research" / "apu81_engagement_bot_log.json")
        self.community_discovery_log = load_json(VAWN_DIR / "research" / "apu81_community_discovery.json")
        self.platform_research = load_json(VAWN_DIR / "research" / "apu81_platform_api_research.json")

    def extract_engagement_metrics(self, days_back: int = 30) -> Dict[str, Any]:
        """Extract engagement metrics from all APU-81 systems."""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        metrics = {
            "automated_engagement": defaultdict(lambda: {"likes": 0, "follows": 0, "filtered": 0}),
            "community_discoveries": defaultdict(int),
            "collaboration_targets": defaultdict(int),
            "quality_scores": defaultdict(list),
            "platform_activity": defaultdict(int),
            "time_saved_estimates": defaultdict(float),
            "total_processed": 0
        }

        # Extract from research log (all agent activities)
        for date_str, entries in self.research_log.items():
            date = datetime.fromisoformat(date_str + "T00:00:00")
            if date < cutoff_date:
                continue

            for entry in entries:
                agent = entry.get("agent", "")
                detail = entry.get("detail", "")

                if agent == "APU81EngagementBot":
                    # Parse enhanced engagement bot data
                    self._parse_engagement_bot_entry(entry, metrics)
                elif agent == "APU81CommunityDiscovery":
                    # Parse community discovery data
                    self._parse_community_discovery_entry(entry, metrics)
                elif agent in ["EngagementAgent", "EngagementBot"]:
                    # Parse original engagement systems
                    self._parse_legacy_engagement_entry(entry, metrics)

        # Extract from enhanced engagement log
        for date_str, day_entries in self.enhanced_engagement_log.items():
            date = datetime.fromisoformat(date_str + "T00:00:00")
            if date < cutoff_date:
                continue

            for entry in day_entries:
                if "bluesky" in entry:
                    bluesky_data = entry["bluesky"]
                    platform = "bluesky"
                    metrics["automated_engagement"][platform]["likes"] += bluesky_data.get("likes", 0)
                    metrics["automated_engagement"][platform]["follows"] += bluesky_data.get("follows", 0)
                    metrics["automated_engagement"][platform]["filtered"] += bluesky_data.get("filtered", 0)

                    # Extract engagement actions for quality analysis
                    if "engagement_actions" in bluesky_data:
                        for action in bluesky_data["engagement_actions"]:
                            metrics["quality_scores"][platform].append(action.get("quality_score", 0))

        # Calculate time saved estimates
        for platform in metrics["automated_engagement"]:
            total_actions = (metrics["automated_engagement"][platform]["likes"] +
                           metrics["automated_engagement"][platform]["follows"])
            # Estimate 1 minute saved per automated action
            metrics["time_saved_estimates"][platform] = total_actions * (1/60)  # Hours

        return dict(metrics)

    def _parse_engagement_bot_entry(self, entry: Dict, metrics: Dict):
        """Parse APU81EngagementBot entry for metrics."""
        detail = entry.get("detail", "")
        try:
            # Parse format: "Enhanced: X likes, Y follows, Z filtered, quality threshold: A.B/10"
            parts = detail.split(", ")
            for part in parts:
                if "likes" in part and "Enhanced:" in part:
                    likes = int(part.split()[1])
                    metrics["automated_engagement"]["bluesky"]["likes"] += likes
                elif "follows" in part:
                    follows = int(part.split()[0])
                    metrics["automated_engagement"]["bluesky"]["follows"] += follows
                elif "filtered" in part:
                    filtered = int(part.split()[0])
                    metrics["automated_engagement"]["bluesky"]["filtered"] += filtered
        except (ValueError, IndexError):
            pass

    def _parse_community_discovery_entry(self, entry: Dict, metrics: Dict):
        """Parse community discovery entry for metrics."""
        detail = entry.get("detail", "")
        try:
            # Parse format: "Discovered X hubs, Y influencers, Z high-value targets"
            if "hubs" in detail:
                hubs = int(detail.split()[1])
                metrics["community_discoveries"]["hubs"] += hubs
            if "influencers" in detail:
                # Find number before "influencers"
                parts = detail.split()
                for i, part in enumerate(parts):
                    if "influencers" in part and i > 0:
                        influencers = int(parts[i-1])
                        metrics["community_discoveries"]["influencers"] += influencers
        except (ValueError, IndexError):
            pass

    def _parse_legacy_engagement_entry(self, entry: Dict, metrics: Dict):
        """Parse legacy engagement system entries."""
        detail = entry.get("detail", "")
        agent = entry.get("agent", "")

        try:
            if agent == "EngagementBot" and "likes" in detail:
                # Original bot format
                likes = int(detail.split()[0]) if detail.split()[0].isdigit() else 0
                metrics["automated_engagement"]["bluesky_legacy"]["likes"] += likes
            elif agent == "EngagementAgent" and "replies generated" in detail:
                replies = int(detail.split()[0]) if detail.split()[0].isdigit() else 0
                metrics["automated_engagement"]["comments"]["replies"] += replies
        except (ValueError, IndexError):
            pass

    def calculate_roi_metrics(self, engagement_metrics: Dict, days_back: int = 30) -> Dict[str, Any]:
        """Calculate detailed ROI metrics for engagement activities."""
        roi_data = {
            "time_period_days": days_back,
            "platform_roi": {},
            "overall_roi": {},
            "cost_benefit_analysis": {},
            "efficiency_metrics": {}
        }

        total_time_saved = 0
        total_monthly_costs = 0
        total_value_generated = 0

        # Calculate ROI for each platform
        for platform, engagement_data in engagement_metrics["automated_engagement"].items():
            if not engagement_data or all(v == 0 for v in engagement_data.values()):
                continue

            # Calculate time saved
            time_saved_hours = engagement_metrics["time_saved_estimates"].get(platform, 0)
            time_saved_weekly = time_saved_hours * (7 / days_back)  # Normalize to weekly

            # Calculate value generated
            platform_multiplier = PLATFORM_VALUE_MULTIPLIERS.get(platform, 1.0)
            weekly_value = time_saved_weekly * HOURLY_VALUE_ESTIMATE * platform_multiplier

            # Calculate costs
            monthly_cost = PLATFORM_COSTS.get(platform, 0)

            # Calculate ROI
            monthly_value = weekly_value * 4
            net_monthly_value = monthly_value - monthly_cost
            roi_ratio = (net_monthly_value / monthly_cost) if monthly_cost > 0 else float('inf')

            # Calculate efficiency metrics
            total_actions = sum(engagement_data.values())
            efficiency = total_actions / max(time_saved_hours, 0.1)  # Actions per hour saved

            roi_data["platform_roi"][platform] = {
                "time_saved_hours_period": round(time_saved_hours, 2),
                "time_saved_weekly": round(time_saved_weekly, 2),
                "weekly_value": round(weekly_value, 0),
                "monthly_cost": monthly_cost,
                "monthly_value": round(monthly_value, 0),
                "net_monthly_value": round(net_monthly_value, 0),
                "roi_ratio": round(roi_ratio, 2) if roi_ratio != float('inf') else "infinite",
                "efficiency_actions_per_hour": round(efficiency, 1),
                "total_actions": total_actions
            }

            total_time_saved += time_saved_hours
            total_monthly_costs += monthly_cost
            total_value_generated += monthly_value

        # Calculate overall ROI
        overall_net_value = total_value_generated - total_monthly_costs
        overall_roi = (overall_net_value / total_monthly_costs) if total_monthly_costs > 0 else float('inf')

        roi_data["overall_roi"] = {
            "total_time_saved_hours": round(total_time_saved, 2),
            "total_monthly_value": round(total_value_generated, 0),
            "total_monthly_costs": total_monthly_costs,
            "net_monthly_value": round(overall_net_value, 0),
            "overall_roi_ratio": round(overall_roi, 2) if overall_roi != float('inf') else "infinite",
            "cost_per_hour_saved": round(total_monthly_costs / max(total_time_saved, 0.1), 2)
        }

        return roi_data

    def analyze_engagement_quality(self, engagement_metrics: Dict) -> Dict[str, Any]:
        """Analyze the quality and effectiveness of engagement activities."""
        quality_analysis = {
            "platform_quality_scores": {},
            "filtering_efficiency": {},
            "target_audience_fit": {},
            "recommendations": []
        }

        # Analyze quality scores by platform
        for platform, scores in engagement_metrics["quality_scores"].items():
            if scores:
                quality_analysis["platform_quality_scores"][platform] = {
                    "avg_quality_score": round(np.mean(scores), 2),
                    "min_score": round(min(scores), 2),
                    "max_score": round(max(scores), 2),
                    "score_distribution": {
                        "excellent (8-10)": sum(1 for s in scores if s >= 8),
                        "good (6-8)": sum(1 for s in scores if 6 <= s < 8),
                        "acceptable (4-6)": sum(1 for s in scores if 4 <= s < 6),
                        "poor (0-4)": sum(1 for s in scores if s < 4)
                    }
                }

        # Analyze filtering efficiency
        for platform, data in engagement_metrics["automated_engagement"].items():
            if data.get("filtered", 0) > 0 or data.get("likes", 0) > 0:
                total_processed = data.get("filtered", 0) + data.get("likes", 0)
                filter_rate = data.get("filtered", 0) / total_processed if total_processed > 0 else 0

                quality_analysis["filtering_efficiency"][platform] = {
                    "filter_rate": round(filter_rate, 3),
                    "total_processed": total_processed,
                    "engaged_with": data.get("likes", 0),
                    "filtered_out": data.get("filtered", 0)
                }

        # Generate quality recommendations
        recommendations = []

        # Check for low quality scores
        for platform, quality_data in quality_analysis["platform_quality_scores"].items():
            avg_score = quality_data["avg_quality_score"]
            if avg_score < 5:
                recommendations.append(f"{platform}: Low avg quality ({avg_score}) - consider raising threshold")
            elif avg_score > 8.5:
                recommendations.append(f"{platform}: High quality ({avg_score}) - consider expanding reach")

        # Check filtering efficiency
        for platform, filter_data in quality_analysis["filtering_efficiency"].items():
            filter_rate = filter_data["filter_rate"]
            if filter_rate > 0.8:
                recommendations.append(f"{platform}: High filter rate ({filter_rate:.1%}) - may be too restrictive")
            elif filter_rate < 0.3:
                recommendations.append(f"{platform}: Low filter rate ({filter_rate:.1%}) - may need better filtering")

        quality_analysis["recommendations"] = recommendations
        return quality_analysis

    def generate_growth_trends(self, days_back: int = 90) -> Dict[str, Any]:
        """Analyze growth trends over time."""
        # This would typically analyze historical data to show trends
        # For now, we'll create a framework for tracking growth metrics

        trends = {
            "engagement_growth": {},
            "efficiency_trends": {},
            "roi_trends": {},
            "recommendations": []
        }

        # Analyze different time periods
        periods = [7, 14, 30, 60, 90]  # days back
        historical_metrics = {}

        for period in periods:
            if period <= days_back:
                period_metrics = self.extract_engagement_metrics(period)
                historical_metrics[f"last_{period}_days"] = period_metrics

        # Calculate growth rates (simplified - would need more historical data for real trends)
        if len(historical_metrics) >= 2:
            recent = historical_metrics["last_7_days"]
            older = historical_metrics["last_30_days"]

            for platform in recent["automated_engagement"]:
                recent_actions = sum(recent["automated_engagement"][platform].values())
                older_actions = sum(older["automated_engagement"][platform].values())

                # Calculate weekly rate from 30-day period
                older_weekly = older_actions / 4.3  # Approximate weeks in 30 days

                if older_weekly > 0:
                    growth_rate = (recent_actions - older_weekly) / older_weekly
                    trends["engagement_growth"][platform] = {
                        "recent_weekly": recent_actions,
                        "historical_weekly": round(older_weekly, 1),
                        "growth_rate": round(growth_rate, 3),
                        "trend": "growing" if growth_rate > 0.1 else "stable" if growth_rate > -0.1 else "declining"
                    }

        return trends

    def create_performance_dashboard(self) -> Dict[str, Any]:
        """Create comprehensive performance dashboard."""
        print("[ANALYTICS] Generating performance dashboard...")

        # Get comprehensive metrics
        engagement_metrics = self.extract_engagement_metrics(30)
        roi_metrics = self.calculate_roi_metrics(engagement_metrics, 30)
        quality_analysis = self.analyze_engagement_quality(engagement_metrics)
        growth_trends = self.generate_growth_trends(90)

        dashboard = {
            "generated_at": datetime.now().isoformat(),
            "period": "last_30_days",
            "summary": {
                "total_automated_engagements": sum(
                    sum(data.values()) for data in engagement_metrics["automated_engagement"].values()
                ),
                "platforms_active": len([p for p in engagement_metrics["automated_engagement"] if any(engagement_metrics["automated_engagement"][p].values())]),
                "total_time_saved_hours": sum(roi_metrics["platform_roi"][p]["time_saved_hours_period"] for p in roi_metrics["platform_roi"]),
                "total_monthly_value": roi_metrics["overall_roi"]["total_monthly_value"],
                "total_monthly_costs": roi_metrics["overall_roi"]["total_monthly_costs"],
                "net_monthly_roi": roi_metrics["overall_roi"]["net_monthly_value"],
                "community_targets_discovered": sum(engagement_metrics["community_discoveries"].values())
            },
            "detailed_metrics": {
                "engagement": engagement_metrics,
                "roi": roi_metrics,
                "quality": quality_analysis,
                "trends": growth_trends
            },
            "platform_performance": {},
            "action_items": []
        }

        # Create platform performance summary
        for platform in engagement_metrics["automated_engagement"]:
            if platform in roi_metrics["platform_roi"]:
                roi_data = roi_metrics["platform_roi"][platform]
                dashboard["platform_performance"][platform] = {
                    "status": "active" if roi_data["total_actions"] > 0 else "inactive",
                    "monthly_roi": roi_data["net_monthly_value"],
                    "efficiency": roi_data["efficiency_actions_per_hour"],
                    "cost": roi_data["monthly_cost"],
                    "recommendation": self._get_platform_recommendation(platform, roi_data, quality_analysis)
                }

        # Generate action items
        dashboard["action_items"] = self._generate_action_items(roi_metrics, quality_analysis, growth_trends)

        return dashboard

    def _get_platform_recommendation(self, platform: str, roi_data: Dict, quality_analysis: Dict) -> str:
        """Generate recommendation for a specific platform."""
        if roi_data["net_monthly_value"] > 1000:
            return "Excellent ROI - maximize usage"
        elif roi_data["net_monthly_value"] > 500:
            return "Good ROI - maintain current level"
        elif roi_data["net_monthly_value"] > 0:
            return "Positive ROI - monitor and optimize"
        elif roi_data["monthly_cost"] == 0:
            return "Free platform - optimize for better results"
        else:
            return "Negative ROI - evaluate cost-benefit"

    def _generate_action_items(self, roi_metrics: Dict, quality_analysis: Dict, growth_trends: Dict) -> List[str]:
        """Generate actionable recommendations based on analytics."""
        action_items = []

        # ROI-based recommendations
        total_roi = roi_metrics["overall_roi"]["overall_roi_ratio"]
        if isinstance(total_roi, (int, float)) and total_roi < 2:
            action_items.append("Overall ROI below 2:1 - review automation strategy")

        # Platform-specific recommendations
        for platform, roi_data in roi_metrics["platform_roi"].items():
            if roi_data["monthly_cost"] > 0 and roi_data["roi_ratio"] < 1:
                action_items.append(f"{platform}: Negative ROI - consider reducing API usage or improving targeting")
            elif roi_data["net_monthly_value"] > 2000:
                action_items.append(f"{platform}: High ROI - consider expanding automation")

        # Quality-based recommendations
        action_items.extend(quality_analysis.get("recommendations", []))

        # Growth-based recommendations
        for platform, trend_data in growth_trends["engagement_growth"].items():
            if trend_data["trend"] == "declining":
                action_items.append(f"{platform}: Declining engagement - review content strategy")

        return action_items[:10]  # Top 10 action items

    def save_analytics_data(self, dashboard: Dict):
        """Save all analytics data to files."""
        # Save dashboard
        save_json(PERFORMANCE_DASHBOARD, dashboard)

        # Save detailed analytics
        analytics_data = {
            "timestamp": datetime.now().isoformat(),
            "engagement_metrics": dashboard["detailed_metrics"]["engagement"],
            "roi_metrics": dashboard["detailed_metrics"]["roi"],
            "quality_analysis": dashboard["detailed_metrics"]["quality"]
        }
        save_json(ENGAGEMENT_ANALYTICS_LOG, analytics_data)

        # Save growth metrics
        save_json(GROWTH_METRICS_LOG, {
            "timestamp": datetime.now().isoformat(),
            "growth_trends": dashboard["detailed_metrics"]["trends"]
        })

        return analytics_data


def main():
    """Main analytics function."""
    print("\n=== APU-81 Engagement Analytics & ROI Tracking ===\n")

    # Initialize analytics system
    analytics = EngagementAnalytics()

    # Generate comprehensive dashboard
    dashboard = analytics.create_performance_dashboard()

    # Save analytics data
    print("[SAVE] Saving analytics data...")
    analytics.save_analytics_data(dashboard)

    # Display summary
    summary = dashboard["summary"]
    print(f"\n=== Performance Summary (Last 30 Days) ===")
    print(f"Total Automated Engagements: {summary['total_automated_engagements']}")
    print(f"Active Platforms: {summary['platforms_active']}")
    print(f"Time Saved: {summary['total_time_saved_hours']:.1f} hours")
    print(f"Monthly Value Generated: ${summary['total_monthly_value']:,.0f}")
    print(f"Monthly Costs: ${summary['total_monthly_costs']}")
    print(f"Net Monthly ROI: ${summary['net_monthly_roi']:,.0f}")

    print(f"\n=== Platform Performance ===")
    for platform, perf in dashboard["platform_performance"].items():
        print(f"{platform.upper()}: {perf['recommendation']} (${perf['monthly_roi']}/month)")

    print(f"\n=== Top Action Items ===")
    for i, item in enumerate(dashboard["action_items"][:5], 1):
        print(f"{i}. {item}")

    # Log for monitoring integration
    log_run(
        "APU81EngagementAnalytics",
        "ok",
        f"Analytics generated: {summary['total_automated_engagements']} engagements, "
        f"${summary['net_monthly_roi']} net ROI, {len(dashboard['action_items'])} action items"
    )

    print(f"\n[SAVE] Analytics dashboard saved to: {PERFORMANCE_DASHBOARD}")
    print(f"[OK] Analytics complete - {len(dashboard['action_items'])} action items generated")

    return dashboard


if __name__ == "__main__":
    main()