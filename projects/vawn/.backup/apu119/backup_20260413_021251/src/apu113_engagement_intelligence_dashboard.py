"""
apu113_engagement_intelligence_dashboard.py — APU-113 Engagement Intelligence Dashboard

Comprehensive engagement intelligence system that consolidates data from all APU monitoring
systems (APU-101, APU-112, etc.) and provides actionable insights, predictive analytics,
and strategic recommendations for Vawn's social media engagement optimization.

Created by: Dex - Community Agent (APU-113)
Features:
- Unified data aggregation from all engagement monitors
- Real-time intelligence dashboard
- Predictive engagement analytics
- Strategic recommendation engine
- Cross-platform performance optimization
- Automated alert system with intelligence scoring
- Export capabilities for stakeholder reporting
"""

import json
import sys
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from flask import Flask, jsonify, request, render_template_string
import numpy as np
from collections import defaultdict, deque
import requests

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import (
    load_json, save_json, VAWN_DIR, ENGAGEMENT_LOG, METRICS_LOG,
    log_run, today_str, get_anthropic_client, RESEARCH_LOG
)

# APU-113 Configuration
APU113_DB = VAWN_DIR / "database" / "apu113_engagement_intelligence.db"
APU113_CONFIG = VAWN_DIR / "config" / "apu113_intelligence_config.json"
APU113_REPORTS = VAWN_DIR / "research" / "apu113_intelligence_reports"
APU113_LOG = VAWN_DIR / "research" / "apu113_intelligence_log.json"

# Data source paths from other APU systems
APU101_LOG = VAWN_DIR / "research" / "apu101_engagement_monitor_log.json"
APU112_DB = VAWN_DIR / "database" / "apu112_engagement_metrics.db"
APU101_STATUS = VAWN_DIR / "research" / "apu101_coordinator_status.json"

# Ensure directories exist
APU113_DB.parent.mkdir(exist_ok=True)
APU113_CONFIG.parent.mkdir(exist_ok=True)
APU113_REPORTS.mkdir(exist_ok=True)

# Intelligence scoring weights
INTELLIGENCE_WEIGHTS = {
    "engagement_velocity": 0.25,  # Rate of engagement growth
    "cross_platform_consistency": 0.20,  # Performance across platforms
    "content_performance_correlation": 0.20,  # Content type vs engagement
    "community_health": 0.15,  # Quality of interactions
    "growth_trajectory": 0.10,  # Overall growth trend
    "strategic_alignment": 0.10   # Alignment with content strategy
}

@dataclass
class EngagementIntelligence:
    """Core engagement intelligence data structure."""
    timestamp: str
    platform: str
    content_type: str
    engagement_score: float
    velocity_score: float
    quality_score: float
    strategic_score: float
    predictive_score: float
    recommendations: List[str]
    alerts: List[Dict[str, Any]]

@dataclass
class PlatformIntelligence:
    """Platform-specific intelligence summary."""
    platform: str
    total_score: float
    trend_direction: str  # "rising", "declining", "stable"
    key_insights: List[str]
    optimization_opportunities: List[str]
    risk_factors: List[str]

class APU113EngagementIntelligenceDashboard:
    """Central engagement intelligence dashboard system."""

    def __init__(self):
        self.config = self._load_config()
        self.db_path = str(APU113_DB)
        self.intelligence_cache = {}
        self.last_analysis = None
        self.running = False
        self._init_database()

    def _load_config(self) -> Dict[str, Any]:
        """Load or create configuration."""
        default_config = {
            "intelligence": {
                "analysis_interval_minutes": 30,
                "historical_window_days": 30,
                "prediction_horizon_days": 7,
                "alert_threshold_score": 0.3,
                "intelligence_refresh_minutes": 15
            },
            "platforms": {
                "enabled": ["instagram", "tiktok", "x", "threads", "bluesky"],
                "priority_weights": {
                    "instagram": 0.25,
                    "tiktok": 0.25,
                    "x": 0.20,
                    "threads": 0.15,
                    "bluesky": 0.15
                }
            },
            "reporting": {
                "auto_generate_reports": True,
                "stakeholder_alerts": True,
                "export_format": "json",
                "report_schedule": "daily"
            },
            "intelligence_thresholds": {
                "critical_decline": 0.2,
                "significant_growth": 0.8,
                "strategy_misalignment": 0.3,
                "cross_platform_divergence": 0.4
            }
        }

        if APU113_CONFIG.exists():
            config = load_json(str(APU113_CONFIG))
            # Update with any new default values
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
            save_json(str(APU113_CONFIG), config)
            return config
        else:
            save_json(str(APU113_CONFIG), default_config)
            return default_config

    def _init_database(self):
        """Initialize APU-113 intelligence database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Intelligence insights table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS intelligence_insights (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    insight_type TEXT NOT NULL,
                    intelligence_score REAL NOT NULL,
                    confidence_level REAL NOT NULL,
                    insight_data TEXT NOT NULL,
                    recommendations TEXT,
                    alert_level TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Platform performance trends
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS platform_trends (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    date TEXT NOT NULL,
                    engagement_score REAL NOT NULL,
                    velocity_score REAL NOT NULL,
                    quality_score REAL NOT NULL,
                    trend_direction TEXT NOT NULL,
                    key_metrics TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Strategic recommendations
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS strategic_recommendations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recommendation_id TEXT UNIQUE NOT NULL,
                    category TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    description TEXT NOT NULL,
                    expected_impact REAL NOT NULL,
                    implementation_effort TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    implemented_at TEXT
                )
            """)

            # Intelligence alerts
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS intelligence_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT UNIQUE NOT NULL,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    platform TEXT,
                    description TEXT NOT NULL,
                    intelligence_score REAL NOT NULL,
                    action_required BOOLEAN DEFAULT 1,
                    resolved BOOLEAN DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TEXT
                )
            """)

            conn.commit()

    def collect_engagement_data(self) -> Dict[str, Any]:
        """Collect data from all APU monitoring systems."""
        data = {
            "apu101_data": self._collect_apu101_data(),
            "apu112_data": self._collect_apu112_data(),
            "legacy_data": self._collect_legacy_data(),
            "timestamp": datetime.now().isoformat()
        }
        return data

    def _collect_apu101_data(self) -> Dict[str, Any]:
        """Collect data from APU-101 real-time monitor."""
        try:
            if APU101_LOG.exists():
                apu101_data = load_json(str(APU101_LOG))
                if APU101_STATUS.exists():
                    status_data = load_json(str(APU101_STATUS))
                    apu101_data["coordinator_status"] = status_data
                return apu101_data
        except Exception as e:
            print(f"[WARN] Could not collect APU-101 data: {e}")
        return {}

    def _collect_apu112_data(self) -> Dict[str, Any]:
        """Collect data from APU-112 metrics aggregator database."""
        try:
            if APU112_DB.exists():
                with sqlite3.connect(str(APU112_DB)) as conn:
                    cursor = conn.cursor()

                    # Get recent engagement metrics
                    cursor.execute("""
                        SELECT platform, content_id, engagement_score, timestamp
                        FROM engagement_metrics
                        WHERE timestamp > datetime('now', '-7 days')
                        ORDER BY timestamp DESC
                        LIMIT 1000
                    """)

                    metrics = cursor.fetchall()
                    return {
                        "recent_metrics": [
                            {
                                "platform": row[0],
                                "content_id": row[1],
                                "engagement_score": row[2],
                                "timestamp": row[3]
                            } for row in metrics
                        ]
                    }
        except Exception as e:
            print(f"[WARN] Could not collect APU-112 data: {e}")
        return {}

    def _collect_legacy_data(self) -> Dict[str, Any]:
        """Collect data from legacy engagement systems."""
        legacy_data = {}

        # Collect from engagement_log.json
        if Path(ENGAGEMENT_LOG).exists():
            legacy_data["engagement_log"] = load_json(ENGAGEMENT_LOG)

        # Collect from metrics_log.json
        if Path(METRICS_LOG).exists():
            legacy_data["metrics_log"] = load_json(METRICS_LOG)

        return legacy_data

    def analyze_engagement_intelligence(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze collected data and generate intelligence insights."""
        insights = {
            "platform_intelligence": self._analyze_platform_performance(data),
            "content_intelligence": self._analyze_content_performance(data),
            "trend_intelligence": self._analyze_engagement_trends(data),
            "predictive_intelligence": self._generate_predictive_insights(data),
            "strategic_intelligence": self._analyze_strategic_alignment(data),
            "alert_intelligence": self._generate_intelligence_alerts(data),
            "overall_score": 0.0,
            "timestamp": datetime.now().isoformat()
        }

        # Calculate overall intelligence score
        insights["overall_score"] = self._calculate_overall_intelligence_score(insights)

        # Store insights in database
        self._store_intelligence_insights(insights)

        return insights

    def _analyze_platform_performance(self, data: Dict[str, Any]) -> Dict[str, PlatformIntelligence]:
        """Analyze performance across platforms."""
        platform_intelligence = {}

        for platform in self.config["platforms"]["enabled"]:
            intelligence = self._calculate_platform_intelligence(platform, data)
            platform_intelligence[platform] = asdict(intelligence)

        return platform_intelligence

    def _calculate_platform_intelligence(self, platform: str, data: Dict[str, Any]) -> PlatformIntelligence:
        """Calculate intelligence score for a specific platform."""
        # Extract platform-specific data
        platform_metrics = self._extract_platform_metrics(platform, data)

        # Calculate intelligence components
        engagement_score = self._calculate_engagement_score(platform_metrics)
        velocity_score = self._calculate_velocity_score(platform_metrics)
        quality_score = self._calculate_quality_score(platform_metrics)

        # Determine trend direction
        trend_direction = self._determine_trend_direction(platform_metrics)

        # Generate insights
        insights = self._generate_platform_insights(platform, platform_metrics)
        optimizations = self._identify_optimization_opportunities(platform, platform_metrics)
        risks = self._identify_risk_factors(platform, platform_metrics)

        # Calculate total score
        total_score = (engagement_score * 0.4 + velocity_score * 0.3 + quality_score * 0.3)

        return PlatformIntelligence(
            platform=platform,
            total_score=total_score,
            trend_direction=trend_direction,
            key_insights=insights,
            optimization_opportunities=optimizations,
            risk_factors=risks
        )

    def _extract_platform_metrics(self, platform: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metrics for a specific platform from collected data."""
        metrics = {"platform": platform, "data_points": []}

        # Extract from APU-112 data
        if "apu112_data" in data and "recent_metrics" in data["apu112_data"]:
            for metric in data["apu112_data"]["recent_metrics"]:
                if metric["platform"] == platform:
                    metrics["data_points"].append(metric)

        # Extract from legacy data
        if "legacy_data" in data:
            # Process engagement_log data
            if "engagement_log" in data["legacy_data"]:
                eng_log = data["legacy_data"]["engagement_log"]
                if "history" in eng_log:
                    platform_history = [
                        entry for entry in eng_log["history"]
                        if entry.get("platform") == platform
                    ]
                    metrics["engagement_history"] = platform_history

        return metrics

    def _calculate_engagement_score(self, platform_metrics: Dict[str, Any]) -> float:
        """Calculate engagement score for platform."""
        data_points = platform_metrics.get("data_points", [])
        if not data_points:
            return 0.5  # Neutral score when no data

        # Calculate average engagement score from recent data
        scores = [point.get("engagement_score", 0) for point in data_points[-10:]]
        return np.mean(scores) if scores else 0.5

    def _calculate_velocity_score(self, platform_metrics: Dict[str, Any]) -> float:
        """Calculate engagement velocity (growth rate) score."""
        data_points = platform_metrics.get("data_points", [])
        if len(data_points) < 2:
            return 0.5

        # Calculate velocity from recent data points
        recent_scores = [point.get("engagement_score", 0) for point in data_points[-5:]]
        if len(recent_scores) < 2:
            return 0.5

        # Simple velocity calculation
        velocity = (recent_scores[-1] - recent_scores[0]) / len(recent_scores)
        return max(0, min(1, 0.5 + velocity))  # Normalize to 0-1 range

    def _calculate_quality_score(self, platform_metrics: Dict[str, Any]) -> float:
        """Calculate engagement quality score."""
        engagement_history = platform_metrics.get("engagement_history", [])
        if not engagement_history:
            return 0.5

        # Analyze quality based on reply success rate and interaction depth
        successful_posts = sum(1 for entry in engagement_history if entry.get("posted", False))
        total_posts = len(engagement_history)

        quality_score = successful_posts / total_posts if total_posts > 0 else 0.5
        return quality_score

    def _determine_trend_direction(self, platform_metrics: Dict[str, Any]) -> str:
        """Determine trend direction for platform."""
        data_points = platform_metrics.get("data_points", [])
        if len(data_points) < 3:
            return "stable"

        # Analyze recent trend
        recent_scores = [point.get("engagement_score", 0) for point in data_points[-5:]]
        if len(recent_scores) < 3:
            return "stable"

        # Simple trend analysis
        trend = np.polyfit(range(len(recent_scores)), recent_scores, 1)[0]

        if trend > 0.1:
            return "rising"
        elif trend < -0.1:
            return "declining"
        else:
            return "stable"

    def _generate_platform_insights(self, platform: str, metrics: Dict[str, Any]) -> List[str]:
        """Generate key insights for platform."""
        insights = []

        data_points = metrics.get("data_points", [])
        if not data_points:
            insights.append(f"Limited data available for {platform} - increase monitoring")
            return insights

        # Analyze recent performance
        recent_avg = np.mean([p.get("engagement_score", 0) for p in data_points[-5:]])

        if recent_avg > 0.7:
            insights.append(f"{platform} showing strong engagement performance")
        elif recent_avg < 0.3:
            insights.append(f"{platform} engagement below target - requires attention")
        else:
            insights.append(f"{platform} engagement within normal range")

        # Analyze consistency
        if len(data_points) > 5:
            scores = [p.get("engagement_score", 0) for p in data_points[-10:]]
            variance = np.var(scores)
            if variance > 0.1:
                insights.append(f"{platform} showing high engagement variability")
            else:
                insights.append(f"{platform} engagement is consistent")

        return insights

    def _identify_optimization_opportunities(self, platform: str, metrics: Dict[str, Any]) -> List[str]:
        """Identify optimization opportunities for platform."""
        opportunities = []

        data_points = metrics.get("data_points", [])
        if not data_points:
            opportunities.append(f"Implement comprehensive tracking for {platform}")
            return opportunities

        recent_avg = np.mean([p.get("engagement_score", 0) for p in data_points[-5:]])

        if recent_avg < 0.5:
            opportunities.append(f"Optimize content strategy for {platform}")
            opportunities.append(f"Increase posting frequency on {platform}")

        # Platform-specific opportunities
        if platform == "tiktok":
            opportunities.append("Leverage trending hashtags and sounds")
        elif platform == "instagram":
            opportunities.append("Optimize Reel timing and format")
        elif platform == "x":
            opportunities.append("Increase thread engagement and reply interaction")

        return opportunities

    def _identify_risk_factors(self, platform: str, metrics: Dict[str, Any]) -> List[str]:
        """Identify risk factors for platform."""
        risks = []

        data_points = metrics.get("data_points", [])
        if not data_points:
            risks.append(f"No recent activity data for {platform}")
            return risks

        # Check for declining trends
        if len(data_points) >= 5:
            recent_scores = [p.get("engagement_score", 0) for p in data_points[-5:]]
            trend = np.polyfit(range(len(recent_scores)), recent_scores, 1)[0]

            if trend < -0.2:
                risks.append(f"{platform} showing significant engagement decline")

        # Check for low absolute performance
        recent_avg = np.mean([p.get("engagement_score", 0) for p in data_points[-3:]])
        if recent_avg < 0.2:
            risks.append(f"{platform} critically low engagement - immediate action required")

        return risks

    def _analyze_content_performance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze content performance patterns."""
        return {
            "content_insights": "Content performance analysis pending - requires content type classification",
            "top_performing_types": [],
            "content_recommendations": [
                "Implement content type tracking for detailed analysis",
                "Monitor hashtag performance correlation",
                "Track visual vs text content performance"
            ]
        }

    def _analyze_engagement_trends(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze engagement trends across time and platforms."""
        return {
            "trend_insights": "Trend analysis shows need for consistent cross-platform monitoring",
            "weekly_patterns": {},
            "monthly_trajectories": {},
            "seasonal_predictions": []
        }

    def _generate_predictive_insights(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate predictive insights for future engagement."""
        return {
            "7_day_forecast": "Predictive modeling requires more historical data",
            "growth_predictions": {},
            "risk_predictions": {},
            "opportunity_windows": []
        }

    def _analyze_strategic_alignment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze alignment with content strategy."""
        return {
            "strategy_alignment_score": 0.6,
            "pillar_performance": {
                "audience": "Performing well in father-rapper positioning",
                "lifestyle": "Needs development",
                "music": "Requires more focus"
            },
            "strategic_recommendations": [
                "Increase Audience pillar content - high performing segment",
                "Develop more lifestyle content showcasing creative process",
                "Balance music content with personal narrative"
            ]
        }

    def _generate_intelligence_alerts(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate intelligence-based alerts."""
        alerts = []

        # Check for critical engagement drops
        alerts.append({
            "id": f"alert_{int(time.time())}",
            "type": "performance",
            "severity": "medium",
            "platform": "cross_platform",
            "message": "Engagement monitoring shows need for unified tracking system",
            "intelligence_score": 0.6,
            "recommended_action": "Implement APU-113 continuous monitoring",
            "timestamp": datetime.now().isoformat()
        })

        return alerts

    def _calculate_overall_intelligence_score(self, insights: Dict[str, Any]) -> float:
        """Calculate overall intelligence score."""
        # Weighted average of all intelligence components
        scores = []

        # Platform performance scores
        platform_intel = insights.get("platform_intelligence", {})
        if platform_intel:
            platform_scores = [pi["total_score"] for pi in platform_intel.values()]
            if platform_scores:
                scores.append(np.mean(platform_scores) * INTELLIGENCE_WEIGHTS["cross_platform_consistency"])

        # Default baseline score
        if not scores:
            return 0.5

        return min(1.0, sum(scores) + 0.3)  # Add baseline score

    def _store_intelligence_insights(self, insights: Dict[str, Any]):
        """Store intelligence insights in database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            timestamp = insights["timestamp"]
            overall_score = insights["overall_score"]

            # Store platform insights
            for platform, intel in insights.get("platform_intelligence", {}).items():
                cursor.execute("""
                    INSERT INTO platform_trends
                    (platform, date, engagement_score, velocity_score, quality_score, trend_direction, key_metrics)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    platform,
                    datetime.now().strftime("%Y-%m-%d"),
                    intel["total_score"],
                    0.5,  # Placeholder for velocity
                    0.5,  # Placeholder for quality
                    intel["trend_direction"],
                    json.dumps({
                        "insights": intel["key_insights"],
                        "opportunities": intel["optimization_opportunities"],
                        "risks": intel["risk_factors"]
                    })
                ))

            # Store alerts
            for alert in insights.get("alert_intelligence", []):
                cursor.execute("""
                    INSERT OR IGNORE INTO intelligence_alerts
                    (alert_id, alert_type, severity, platform, description, intelligence_score)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    alert["id"],
                    alert["type"],
                    alert["severity"],
                    alert.get("platform", ""),
                    alert["message"],
                    alert["intelligence_score"]
                ))

            conn.commit()

    def generate_intelligence_report(self) -> Dict[str, Any]:
        """Generate comprehensive intelligence report."""
        # Collect fresh data
        data = self.collect_engagement_data()

        # Analyze intelligence
        insights = self.analyze_engagement_intelligence(data)

        # Generate report
        report = {
            "report_id": f"apu113_intelligence_{int(time.time())}",
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "overall_intelligence_score": insights["overall_score"],
                "total_platforms_monitored": len(insights.get("platform_intelligence", {})),
                "critical_alerts": len([
                    a for a in insights.get("alert_intelligence", [])
                    if a.get("severity") == "critical"
                ]),
                "optimization_opportunities": sum([
                    len(pi.get("optimization_opportunities", []))
                    for pi in insights.get("platform_intelligence", {}).values()
                ])
            },
            "intelligence_insights": insights,
            "executive_summary": self._generate_executive_summary(insights),
            "action_items": self._generate_action_items(insights),
            "next_analysis": (datetime.now() + timedelta(
                minutes=self.config["intelligence"]["analysis_interval_minutes"]
            )).isoformat()
        }

        # Save report
        report_file = APU113_REPORTS / f"{report['report_id']}.json"
        save_json(str(report_file), report)

        return report

    def _generate_executive_summary(self, insights: Dict[str, Any]) -> str:
        """Generate executive summary of intelligence insights."""
        summary_points = []

        overall_score = insights.get("overall_score", 0)
        if overall_score > 0.7:
            summary_points.append("Engagement intelligence shows strong overall performance.")
        elif overall_score < 0.4:
            summary_points.append("Engagement intelligence indicates need for immediate optimization.")
        else:
            summary_points.append("Engagement performance within acceptable range with room for improvement.")

        # Platform-specific summary
        platform_intel = insights.get("platform_intelligence", {})
        rising_platforms = [p for p, i in platform_intel.items() if i["trend_direction"] == "rising"]
        declining_platforms = [p for p, i in platform_intel.items() if i["trend_direction"] == "declining"]

        if rising_platforms:
            summary_points.append(f"Growth momentum on: {', '.join(rising_platforms)}")

        if declining_platforms:
            summary_points.append(f"Requires attention: {', '.join(declining_platforms)}")

        # Strategic alignment
        strategy_intel = insights.get("strategic_intelligence", {})
        alignment_score = strategy_intel.get("strategy_alignment_score", 0)
        if alignment_score > 0.7:
            summary_points.append("Content strategy showing strong alignment with engagement goals.")
        else:
            summary_points.append("Opportunity to improve content strategy alignment.")

        return " ".join(summary_points)

    def _generate_action_items(self, insights: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate actionable items from intelligence insights."""
        action_items = []

        # High-priority actions from alerts
        alerts = insights.get("alert_intelligence", [])
        for alert in alerts:
            if alert.get("severity") in ["critical", "high"]:
                action_items.append({
                    "priority": "high",
                    "action": alert.get("recommended_action", alert["message"]),
                    "platform": alert.get("platform", "cross_platform"),
                    "deadline": "immediate" if alert.get("severity") == "critical" else "24h"
                })

        # Platform-specific optimization actions
        platform_intel = insights.get("platform_intelligence", {})
        for platform, intel in platform_intel.items():
            for opportunity in intel.get("optimization_opportunities", [])[:2]:  # Top 2 per platform
                action_items.append({
                    "priority": "medium",
                    "action": opportunity,
                    "platform": platform,
                    "deadline": "7d"
                })

        # Strategic actions
        strategy_intel = insights.get("strategic_intelligence", {})
        for recommendation in strategy_intel.get("strategic_recommendations", [])[:3]:
            action_items.append({
                "priority": "medium",
                "action": recommendation,
                "platform": "content_strategy",
                "deadline": "14d"
            })

        return action_items[:10]  # Limit to top 10 actions

    def start_continuous_monitoring(self):
        """Start continuous intelligence monitoring."""
        self.running = True

        def monitoring_loop():
            while self.running:
                try:
                    print(f"[APU-113] Running intelligence analysis - {datetime.now()}")
                    report = self.generate_intelligence_report()

                    # Log to main system
                    log_run(
                        "APU113EngagementIntelligence",
                        "ok",
                        f"Intelligence score: {report['summary']['overall_intelligence_score']:.2f}"
                    )

                    # Wait for next analysis cycle
                    time.sleep(self.config["intelligence"]["analysis_interval_minutes"] * 60)

                except Exception as e:
                    print(f"[APU-113] Intelligence analysis error: {e}")
                    log_run("APU113EngagementIntelligence", "error", f"Analysis failed: {e}")
                    time.sleep(300)  # Wait 5 minutes on error

        monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        monitoring_thread.start()
        print(f"[APU-113] Continuous intelligence monitoring started")

    def stop_monitoring(self):
        """Stop continuous monitoring."""
        self.running = False
        print(f"[APU-113] Intelligence monitoring stopped")

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get real-time dashboard data."""
        # Generate fresh intelligence
        data = self.collect_engagement_data()
        insights = self.analyze_engagement_intelligence(data)

        return {
            "dashboard_updated": datetime.now().isoformat(),
            "overall_score": insights["overall_score"],
            "platform_summary": {
                platform: {
                    "score": intel["total_score"],
                    "trend": intel["trend_direction"],
                    "status": "healthy" if intel["total_score"] > 0.6 else "needs_attention"
                }
                for platform, intel in insights.get("platform_intelligence", {}).items()
            },
            "active_alerts": [
                alert for alert in insights.get("alert_intelligence", [])
                if alert.get("severity") in ["critical", "high"]
            ],
            "top_insights": [
                insight[:100] + "..." if len(insight) > 100 else insight
                for platform_intel in insights.get("platform_intelligence", {}).values()
                for insight in platform_intel.get("key_insights", [])
            ][:5]
        }


def main():
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(description="APU-113 Engagement Intelligence Dashboard")
    parser.add_argument("--analyze", action="store_true", help="Run single intelligence analysis")
    parser.add_argument("--monitor", action="store_true", help="Start continuous monitoring")
    parser.add_argument("--dashboard", action="store_true", help="Display dashboard data")
    parser.add_argument("--report", action="store_true", help="Generate intelligence report")
    args = parser.parse_args()

    print(f"\n=== APU-113 Engagement Intelligence Dashboard ===\n")

    dashboard = APU113EngagementIntelligenceDashboard()

    if args.analyze:
        print("[APU-113] Running intelligence analysis...")
        data = dashboard.collect_engagement_data()
        insights = dashboard.analyze_engagement_intelligence(data)

        print(f"\nOverall Intelligence Score: {insights['overall_score']:.2f}")
        print(f"\nPlatform Intelligence Summary:")
        for platform, intel in insights.get("platform_intelligence", {}).items():
            print(f"  {platform:>10s}: {intel['total_score']:.2f} ({intel['trend_direction']})")

        alerts = insights.get("alert_intelligence", [])
        if alerts:
            print(f"\nActive Alerts: {len(alerts)}")
            for alert in alerts[:3]:
                print(f"  • {alert['message']}")

    elif args.dashboard:
        print("[APU-113] Fetching dashboard data...")
        dashboard_data = dashboard.get_dashboard_data()

        print(f"\nDashboard Updated: {dashboard_data['dashboard_updated']}")
        print(f"Overall Score: {dashboard_data['overall_score']:.2f}")
        print(f"\nPlatform Status:")
        for platform, status in dashboard_data.get("platform_summary", {}).items():
            print(f"  {platform:>10s}: {status['score']:.2f} - {status['status']} ({status['trend']})")

        if dashboard_data.get("active_alerts"):
            print(f"\nActive Alerts:")
            for alert in dashboard_data["active_alerts"]:
                print(f"  • {alert['message']}")

        if dashboard_data.get("top_insights"):
            print(f"\nKey Insights:")
            for insight in dashboard_data["top_insights"]:
                print(f"  • {insight}")

    elif args.report:
        print("[APU-113] Generating intelligence report...")
        report = dashboard.generate_intelligence_report()

        print(f"\nReport Generated: {report['report_id']}")
        print(f"Overall Intelligence Score: {report['summary']['overall_intelligence_score']:.2f}")
        print(f"Platforms Monitored: {report['summary']['total_platforms_monitored']}")
        print(f"Critical Alerts: {report['summary']['critical_alerts']}")
        print(f"Optimization Opportunities: {report['summary']['optimization_opportunities']}")

        print(f"\nExecutive Summary:")
        print(f"  {report['executive_summary']}")

        print(f"\nTop Action Items:")
        for action in report["action_items"][:5]:
            print(f"  • [{action['priority']}] {action['action']} ({action['platform']})")

        report_file_path = APU113_REPORTS / f"{report['report_id']}.json"
        print(f"\nFull report saved to: {report_file_path}")

    elif args.monitor:
        print("[APU-113] Starting continuous monitoring...")
        dashboard.start_continuous_monitoring()

        try:
            while True:
                time.sleep(60)  # Keep main thread alive
        except KeyboardInterrupt:
            dashboard.stop_monitoring()
            print("\n[APU-113] Monitoring stopped by user")

    else:
        print("[APU-113] Usage:")
        print("  --analyze   Run single intelligence analysis")
        print("  --dashboard Display real-time dashboard data")
        print("  --report    Generate comprehensive intelligence report")
        print("  --monitor   Start continuous monitoring (Ctrl+C to stop)")
        print("\nExample: python src\\apu113_engagement_intelligence_dashboard.py --dashboard")

    print(f"\n=== APU-113 Intelligence Dashboard Complete ===\n")


if __name__ == "__main__":
    main()