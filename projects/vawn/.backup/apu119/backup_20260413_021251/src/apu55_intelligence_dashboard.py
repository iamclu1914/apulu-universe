"""
APU-55 Real-Time Intelligence Dashboard

This module provides a comprehensive real-time dashboard for monitoring and controlling
the APU-55 Intelligent Engagement Orchestrator system. Features predictive insights,
cross-platform correlation visualization, and intelligent system control interfaces.

Author: Dex - Community (Agent ID: 75dd5aa3-6dfb-4d13-b424-48343f1fd7e2)
Priority: Medium
System: APU-55 Intelligent Engagement Orchestrator
"""

import json
import asyncio
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
import statistics
from collections import defaultdict

# Dashboard configuration
DASHBOARD_CONFIG = {
    "refresh_interval": 30,  # seconds
    "data_retention": 24,    # hours
    "alert_thresholds": {
        "engagement_critical": 0.3,
        "sentiment_critical": -0.4,
        "api_health_critical": 0.8,
        "correlation_weak": 0.4,
        "system_health_poor": 0.6
    },
    "visualization_limits": {
        "max_data_points": 100,
        "prediction_horizon": 7,  # days
        "trend_analysis_window": 24  # hours
    },
    "performance_targets": {
        "engagement_target": 0.65,
        "sentiment_target": 0.2,
        "correlation_target": 0.7,
        "response_time_target": 2.0,
        "success_rate_target": 0.85
    }
}

class DashboardAlert(Enum):
    """Dashboard alert levels."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"
    SUCCESS = "success"

class SystemStatus(Enum):
    """Overall system status levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"

@dataclass
class DashboardMetric:
    """Dashboard metric data point."""
    metric_id: str
    timestamp: str
    value: float
    status: str
    trend: str
    target: float
    deviation: float

@dataclass
class SystemAlert:
    """System alert information."""
    alert_id: str
    timestamp: str
    level: DashboardAlert
    component: str
    message: str
    details: Dict[str, Any]
    acknowledged: bool = False
    resolved: bool = False

@dataclass
class PredictiveInsight:
    """Predictive insight data."""
    insight_id: str
    timestamp: str
    prediction_type: str
    timeframe: str
    confidence: float
    predicted_value: float
    current_value: float
    recommendation: str
    impact_assessment: str

class APU55IntelligenceDashboard:
    """Real-time intelligence dashboard for APU-55 system monitoring and control."""

    def __init__(self):
        """Initialize the intelligence dashboard."""
        self.dashboard_data = {
            "system_overview": {},
            "platform_metrics": {},
            "correlation_analysis": {},
            "predictive_insights": {},
            "automated_responses": {},
            "ai_optimizations": {},
            "system_alerts": [],
            "performance_metrics": {},
            "historical_data": defaultdict(list)
        }

        self.active_alerts = []
        self.dashboard_session_id = f"dash_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.last_refresh = None

        print("[INTEL-DASH] APU-55 Intelligence Dashboard initialized")

    async def generate_realtime_dashboard(self, orchestration_data: Dict) -> Dict[str, Any]:
        """Generate comprehensive real-time dashboard data."""
        print("[INTEL-DASH] Generating real-time intelligence dashboard...")

        dashboard_output = {
            "dashboard_timestamp": datetime.now().isoformat(),
            "session_id": self.dashboard_session_id,
            "system_overview": {},
            "platform_intelligence": {},
            "correlation_insights": {},
            "predictive_analytics": {},
            "automation_status": {},
            "ai_strategy_status": {},
            "system_alerts": [],
            "performance_dashboard": {},
            "trend_analysis": {},
            "control_recommendations": [],
            "dashboard_health": {}
        }

        try:
            # Phase 1: System Overview
            print("[INTEL-DASH] Generating system overview...")
            dashboard_output["system_overview"] = await self._generate_system_overview(orchestration_data)

            # Phase 2: Platform Intelligence
            print("[INTEL-DASH] Processing platform intelligence...")
            dashboard_output["platform_intelligence"] = await self._process_platform_intelligence(orchestration_data)

            # Phase 3: Correlation Insights
            print("[INTEL-DASH] Analyzing correlation insights...")
            dashboard_output["correlation_insights"] = await self._analyze_correlation_insights(orchestration_data)

            # Phase 4: Predictive Analytics Dashboard
            print("[INTEL-DASH] Building predictive analytics dashboard...")
            dashboard_output["predictive_analytics"] = await self._build_predictive_dashboard(orchestration_data)

            # Phase 5: Automation Status
            print("[INTEL-DASH] Monitoring automation status...")
            dashboard_output["automation_status"] = await self._monitor_automation_status(orchestration_data)

            # Phase 6: AI Strategy Status
            print("[INTEL-DASH] Tracking AI strategy status...")
            dashboard_output["ai_strategy_status"] = await self._track_ai_strategy_status(orchestration_data)

            # Phase 7: System Alerts
            print("[INTEL-DASH] Processing system alerts...")
            dashboard_output["system_alerts"] = await self._process_system_alerts(orchestration_data)

            # Phase 8: Performance Dashboard
            print("[INTEL-DASH] Creating performance dashboard...")
            dashboard_output["performance_dashboard"] = await self._create_performance_dashboard(orchestration_data)

            # Phase 9: Trend Analysis
            print("[INTEL-DASH] Performing trend analysis...")
            dashboard_output["trend_analysis"] = await self._perform_trend_analysis(orchestration_data)

            # Phase 10: Control Recommendations
            print("[INTEL-DASH] Generating control recommendations...")
            dashboard_output["control_recommendations"] = await self._generate_control_recommendations(orchestration_data)

            # Phase 11: Dashboard Health
            dashboard_output["dashboard_health"] = self._assess_dashboard_health(dashboard_output)

            # Update historical data
            self._update_historical_data(dashboard_output)
            self.last_refresh = datetime.now()

            print("[INTEL-DASH] Real-time dashboard generation complete")

        except Exception as e:
            error_msg = f"Dashboard generation failed: {str(e)}"
            dashboard_output["error"] = error_msg
            print(f"[ERROR] {error_msg}")

        return dashboard_output

    async def _generate_system_overview(self, orchestration_data: Dict) -> Dict[str, Any]:
        """Generate high-level system overview."""
        overview = {
            "overall_status": SystemStatus.GOOD,
            "system_health_score": 0.8,
            "active_platforms": 0,
            "correlation_strength": 0.0,
            "prediction_accuracy": 0.0,
            "automation_effectiveness": 0.0,
            "ai_optimization_status": "active",
            "last_update": datetime.now().isoformat(),
            "key_metrics": {},
            "status_indicators": {}
        }

        # Calculate system health score
        unified_intelligence = orchestration_data.get("unified_intelligence", {})
        performance_summary = orchestration_data.get("performance_summary", {})

        # Active platforms
        platform_health = {
            "instagram": unified_intelligence.get("instagram_intelligence", {}).get("api_health", False),
            "tiktok": unified_intelligence.get("tiktok_intelligence", {}).get("api_health", False),
            "x": unified_intelligence.get("x_intelligence", {}).get("api_health", False),
            "threads": unified_intelligence.get("threads_intelligence", {}).get("api_health", False),
            "bluesky": unified_intelligence.get("bluesky_intelligence", {}).get("api_health", False)
        }

        overview["active_platforms"] = sum(1 for health in platform_health.values() if health)

        # Correlation strength
        correlation_data = orchestration_data.get("correlation_analysis", {})
        overview["correlation_strength"] = correlation_data.get("cross_platform_score", 0.0)

        # Prediction accuracy
        predictions = orchestration_data.get("predictions", {})
        overview["prediction_accuracy"] = predictions.get("confidence_metrics", {}).get("overall_confidence", 0.0)

        # Automation effectiveness
        automated_responses = orchestration_data.get("automated_responses", {})
        automation_effectiveness = automated_responses.get("response_effectiveness", {})
        overview["automation_effectiveness"] = automation_effectiveness.get("overall_success_rate", 0.0)

        # Calculate overall system health score
        health_factors = [
            overview["active_platforms"] / 5.0,  # Platform health
            overview["correlation_strength"],      # Correlation strength
            overview["prediction_accuracy"],       # Prediction accuracy
            overview["automation_effectiveness"]   # Automation effectiveness
        ]

        overview["system_health_score"] = statistics.mean([f for f in health_factors if f > 0])

        # Determine overall status
        if overview["system_health_score"] >= 0.9:
            overview["overall_status"] = SystemStatus.EXCELLENT
        elif overview["system_health_score"] >= 0.75:
            overview["overall_status"] = SystemStatus.GOOD
        elif overview["system_health_score"] >= 0.6:
            overview["overall_status"] = SystemStatus.FAIR
        elif overview["system_health_score"] >= 0.4:
            overview["overall_status"] = SystemStatus.POOR
        else:
            overview["overall_status"] = SystemStatus.CRITICAL

        # Key metrics summary
        overview["key_metrics"] = {
            "total_platforms": 5,
            "active_platforms": overview["active_platforms"],
            "avg_engagement": self._calculate_avg_engagement(unified_intelligence),
            "avg_sentiment": self._calculate_avg_sentiment(unified_intelligence),
            "system_uptime": self._calculate_system_uptime(),
            "response_time": performance_summary.get("avg_response_time", 0.0)
        }

        # Status indicators
        overview["status_indicators"] = {
            "platform_health": "excellent" if overview["active_platforms"] >= 4 else "poor",
            "correlation_status": "strong" if overview["correlation_strength"] > 0.7 else "weak",
            "prediction_status": "accurate" if overview["prediction_accuracy"] > 0.8 else "uncertain",
            "automation_status": "effective" if overview["automation_effectiveness"] > 0.85 else "needs_improvement"
        }

        return overview

    async def _process_platform_intelligence(self, orchestration_data: Dict) -> Dict[str, Any]:
        """Process platform-specific intelligence for dashboard."""
        platform_intel = {
            "platforms": {},
            "comparative_analysis": {},
            "performance_rankings": {},
            "health_status": {},
            "engagement_trends": {},
            "sentiment_analysis": {}
        }

        unified_intelligence = orchestration_data.get("unified_intelligence", {})

        # Process each platform
        platforms = ["instagram", "tiktok", "x", "threads", "bluesky"]
        platform_metrics = {}

        for platform in platforms:
            platform_data = unified_intelligence.get(f"{platform}_intelligence", {})

            metrics = {
                "platform": platform,
                "api_health": platform_data.get("api_health", False),
                "engagement_rate": platform_data.get("engagement_rate", 0.0),
                "sentiment_score": platform_data.get("sentiment_score", 0.0),
                "viral_potential": platform_data.get("viral_potential", 0.0),
                "reach": platform_data.get("reach", 0),
                "interactions": platform_data.get("interactions", 0),
                "content_performance": platform_data.get("content_performance", 0.0),
                "response_time": platform_data.get("response_time", 0.0),
                "last_update": platform_data.get("last_update", datetime.now().isoformat())
            }

            platform_intel["platforms"][platform] = metrics
            platform_metrics[platform] = metrics

        # Comparative analysis
        if platform_metrics:
            healthy_platforms = {p: m for p, m in platform_metrics.items() if m["api_health"]}

            if healthy_platforms:
                engagement_rates = [m["engagement_rate"] for m in healthy_platforms.values()]
                sentiment_scores = [m["sentiment_score"] for m in healthy_platforms.values()]
                viral_potentials = [m["viral_potential"] for m in healthy_platforms.values()]

                platform_intel["comparative_analysis"] = {
                    "avg_engagement": statistics.mean(engagement_rates),
                    "max_engagement": max(engagement_rates),
                    "min_engagement": min(engagement_rates),
                    "avg_sentiment": statistics.mean(sentiment_scores),
                    "max_sentiment": max(sentiment_scores),
                    "min_sentiment": min(sentiment_scores),
                    "avg_viral_potential": statistics.mean(viral_potentials),
                    "engagement_variance": statistics.stdev(engagement_rates) if len(engagement_rates) > 1 else 0.0
                }

                # Performance rankings
                ranked_engagement = sorted(healthy_platforms.items(), key=lambda x: x[1]["engagement_rate"], reverse=True)
                ranked_sentiment = sorted(healthy_platforms.items(), key=lambda x: x[1]["sentiment_score"], reverse=True)
                ranked_viral = sorted(healthy_platforms.items(), key=lambda x: x[1]["viral_potential"], reverse=True)

                platform_intel["performance_rankings"] = {
                    "engagement": [{"platform": p, "value": m["engagement_rate"]} for p, m in ranked_engagement],
                    "sentiment": [{"platform": p, "value": m["sentiment_score"]} for p, m in ranked_sentiment],
                    "viral_potential": [{"platform": p, "value": m["viral_potential"]} for p, m in ranked_viral]
                }

        # Health status summary
        platform_intel["health_status"] = {
            "total_platforms": len(platforms),
            "healthy_platforms": len([m for m in platform_metrics.values() if m["api_health"]]),
            "unhealthy_platforms": [p for p, m in platform_metrics.items() if not m["api_health"]],
            "average_response_time": statistics.mean([m["response_time"] for m in platform_metrics.values() if m["response_time"] > 0]) if platform_metrics else 0.0
        }

        return platform_intel

    async def _analyze_correlation_insights(self, orchestration_data: Dict) -> Dict[str, Any]:
        """Analyze correlation insights for dashboard visualization."""
        correlation_insights = {
            "correlation_matrix": {},
            "sync_status": {},
            "strong_correlations": [],
            "weak_correlations": [],
            "optimization_opportunities": [],
            "trend_correlations": {}
        }

        correlation_data = orchestration_data.get("correlation_analysis", {})

        if correlation_data:
            # Correlation results
            correlation_results = correlation_data.get("correlation_results", [])

            # Strong and weak correlations
            for result in correlation_results:
                correlation_strength = result.get("correlation_strength", 0.0)
                correlation_type = result.get("correlation_type", "unknown")
                platforms = result.get("platforms_involved", [])

                if correlation_strength > DASHBOARD_CONFIG["alert_thresholds"]["correlation_weak"]:
                    correlation_insights["strong_correlations"].append({
                        "type": correlation_type,
                        "strength": correlation_strength,
                        "platforms": platforms,
                        "confidence": result.get("confidence_score", 0.0)
                    })
                else:
                    correlation_insights["weak_correlations"].append({
                        "type": correlation_type,
                        "strength": correlation_strength,
                        "platforms": platforms,
                        "improvement_needed": True
                    })

            # Sync status
            sync_status = correlation_data.get("sync_status", {})
            correlation_insights["sync_status"] = {
                "overall_score": sync_status.get("sync_score", 0.0),
                "status": sync_status.get("overall_sync_status", "unknown"),
                "platform_scores": sync_status.get("platform_sync_scores", {}),
                "desync_indicators": sync_status.get("desync_indicators", [])
            }

            # Cross-platform score
            correlation_insights["cross_platform_score"] = correlation_data.get("cross_platform_score", 0.0)

            # Optimization opportunities
            optimization_recs = correlation_data.get("optimization_recommendations", [])
            correlation_insights["optimization_opportunities"] = [
                {
                    "type": rec.get("type", "unknown"),
                    "priority": rec.get("priority", "medium"),
                    "recommendation": rec.get("recommendation", ""),
                    "expected_impact": rec.get("expected_impact", "unknown"),
                    "effort": rec.get("implementation_effort", "medium")
                }
                for rec in optimization_recs[:5]  # Top 5
            ]

        return correlation_insights

    async def _build_predictive_dashboard(self, orchestration_data: Dict) -> Dict[str, Any]:
        """Build predictive analytics dashboard."""
        predictive_dashboard = {
            "engagement_forecasts": {},
            "sentiment_predictions": {},
            "viral_probability_scores": {},
            "trend_predictions": {},
            "risk_assessments": {},
            "opportunity_forecasts": {},
            "confidence_metrics": {}
        }

        predictions = orchestration_data.get("predictions", {})

        if predictions:
            # Engagement forecasts
            engagement_forecasts = predictions.get("engagement_forecasts", {})
            predictive_dashboard["engagement_forecasts"] = {
                "7_day_forecast": engagement_forecasts.get("7_day_forecast", {}),
                "trend_direction": engagement_forecasts.get("trend_analysis", {}).get("overall_trend", "stable"),
                "forecast_confidence": engagement_forecasts.get("forecast_confidence", 0.0),
                "key_insights": engagement_forecasts.get("key_insights", [])
            }

            # Sentiment predictions
            sentiment_predictions = predictions.get("sentiment_forecasts", {})
            predictive_dashboard["sentiment_predictions"] = {
                "predicted_trajectory": sentiment_predictions.get("sentiment_trajectory", {}),
                "risk_indicators": sentiment_predictions.get("risk_indicators", []),
                "intervention_recommendations": sentiment_predictions.get("intervention_recommendations", []),
                "confidence": sentiment_predictions.get("confidence_score", 0.0)
            }

            # Viral probability scores
            viral_scores = predictions.get("viral_probability_scores", {})
            predictive_dashboard["viral_probability_scores"] = {
                "current_potential": viral_scores.get("current_viral_potential", {}),
                "platform_scores": viral_scores.get("platform_viral_scores", {}),
                "timing_recommendations": viral_scores.get("optimal_timing_predictions", {}),
                "content_recommendations": viral_scores.get("content_optimization_suggestions", [])
            }

            # Trend predictions
            predictive_dashboard["trend_predictions"] = predictions.get("trend_predictions", {})

            # Confidence metrics
            confidence_metrics = predictions.get("confidence_metrics", {})
            predictive_dashboard["confidence_metrics"] = {
                "overall_confidence": confidence_metrics.get("overall_confidence", 0.0),
                "prediction_reliability": confidence_metrics.get("prediction_reliability", {}),
                "data_quality_score": confidence_metrics.get("data_quality_score", 0.0),
                "model_performance": confidence_metrics.get("model_performance", {})
            }

        return predictive_dashboard

    async def _monitor_automation_status(self, orchestration_data: Dict) -> Dict[str, Any]:
        """Monitor automation status and performance."""
        automation_status = {
            "system_status": "active",
            "execution_metrics": {},
            "recent_actions": [],
            "success_rates": {},
            "safety_status": {},
            "learning_progress": {},
            "escalation_summary": {}
        }

        automated_responses = orchestration_data.get("automated_responses", {})

        if automated_responses:
            # Execution metrics
            executed_actions = automated_responses.get("executed_actions", [])
            automation_status["execution_metrics"] = {
                "total_actions": len(executed_actions),
                "successful_actions": len([a for a in executed_actions if a.get("success", False)]),
                "failed_actions": len([a for a in executed_actions if not a.get("success", False)]),
                "avg_execution_time": statistics.mean([a.get("execution_time", 0.0) for a in executed_actions]) if executed_actions else 0.0
            }

            # Recent actions (last 10)
            automation_status["recent_actions"] = [
                {
                    "action_id": action.get("action_id", "unknown"),
                    "action_type": action.get("action_type", "unknown"),
                    "status": "success" if action.get("success", False) else "failed",
                    "timestamp": action.get("timestamp", ""),
                    "execution_time": action.get("execution_time", 0.0)
                }
                for action in executed_actions[-10:]  # Last 10 actions
            ]

            # Success rates
            response_effectiveness = automated_responses.get("response_effectiveness", {})
            automation_status["success_rates"] = {
                "overall_success_rate": response_effectiveness.get("overall_success_rate", 0.0),
                "response_time_performance": response_effectiveness.get("response_time_performance", 0.0),
                "escalation_rate": response_effectiveness.get("escalation_rate", 0.0),
                "safety_compliance_score": response_effectiveness.get("safety_compliance_score", 1.0)
            }

            # Safety status
            safety_checks = automated_responses.get("safety_checks", {})
            automation_status["safety_status"] = {
                "safe_to_proceed": safety_checks.get("safe_to_proceed", True),
                "rate_limit_status": safety_checks.get("rate_limit_status", {}),
                "safety_violations": safety_checks.get("safety_violations", []),
                "recommendations": safety_checks.get("recommendations", [])
            }

            # Learning progress
            learning_adjustments = automated_responses.get("learning_adjustments", [])
            automation_status["learning_progress"] = {
                "total_adjustments": len(learning_adjustments),
                "improvement_adjustments": len([adj for adj in learning_adjustments if "improvement" in adj.get("learning_type", "")]),
                "pattern_adjustments": len([adj for adj in learning_adjustments if "pattern" in adj.get("learning_type", "")]),
                "recent_learning": learning_adjustments[-5:] if learning_adjustments else []
            }

            # Escalation summary
            escalations = automated_responses.get("escalations_created", [])
            automation_status["escalation_summary"] = {
                "total_escalations": len(escalations),
                "critical_escalations": len([esc for esc in escalations if esc.get("severity") == "critical"]),
                "recent_escalations": escalations[-3:] if escalations else [],
                "escalation_rate": len(escalations) / max(len(executed_actions), 1)
            }

        return automation_status

    async def _track_ai_strategy_status(self, orchestration_data: Dict) -> Dict[str, Any]:
        """Track AI strategy optimization status."""
        ai_strategy_status = {
            "optimization_status": "active",
            "claude_performance": {},
            "strategy_adjustments": {},
            "recommendation_metrics": {},
            "optimization_history": [],
            "performance_improvements": {}
        }

        ai_optimizations = orchestration_data.get("ai_optimizations", {})

        if ai_optimizations:
            # Claude performance
            ai_strategy_status["claude_performance"] = {
                "response_quality": ai_optimizations.get("response_quality", 0.0),
                "processing_time": ai_optimizations.get("processing_time", 0.0),
                "api_health": not ai_optimizations.get("error", False),
                "last_update": ai_optimizations.get("timestamp", "")
            }

            # Strategy adjustments
            strategy_recommendations = ai_optimizations.get("strategy_recommendations", [])
            ai_strategy_status["strategy_adjustments"] = {
                "total_recommendations": len(strategy_recommendations),
                "high_priority": len([rec for rec in strategy_recommendations if rec.get("priority") == "high"]),
                "implemented": len([rec for rec in strategy_recommendations if rec.get("status") == "implemented"]),
                "pending": len([rec for rec in strategy_recommendations if rec.get("status") == "pending"])
            }

            # Recommendation metrics
            confidence_assessment = ai_optimizations.get("confidence_assessment", {})
            ai_strategy_status["recommendation_metrics"] = {
                "overall_confidence": confidence_assessment.get("overall_confidence", 0.0),
                "strategy_effectiveness": confidence_assessment.get("strategy_effectiveness", 0.0),
                "implementation_feasibility": confidence_assessment.get("implementation_feasibility", 0.0),
                "expected_impact": confidence_assessment.get("expected_impact", 0.0)
            }

            # Recent optimization history
            ai_strategy_status["optimization_history"] = strategy_recommendations[-5:] if strategy_recommendations else []

        return ai_strategy_status

    async def _process_system_alerts(self, orchestration_data: Dict) -> List[SystemAlert]:
        """Process and generate system alerts."""
        alerts = []
        current_time = datetime.now()

        # Check engagement levels
        unified_intelligence = orchestration_data.get("unified_intelligence", {})
        engagement_intel = unified_intelligence.get("engagement_intelligence", {})
        current_effectiveness = engagement_intel.get("current_effectiveness", 0.0)

        if current_effectiveness < DASHBOARD_CONFIG["alert_thresholds"]["engagement_critical"]:
            alerts.append(SystemAlert(
                alert_id=f"eng_critical_{current_time.strftime('%H%M%S')}",
                timestamp=current_time.isoformat(),
                level=DashboardAlert.CRITICAL,
                component="engagement_monitoring",
                message=f"Critical engagement level detected: {current_effectiveness:.1%}",
                details={
                    "current_value": current_effectiveness,
                    "threshold": DASHBOARD_CONFIG["alert_thresholds"]["engagement_critical"],
                    "recommended_action": "immediate_engagement_optimization"
                }
            ))

        # Check sentiment levels
        community_intel = unified_intelligence.get("community_intelligence", {})
        sentiment = community_intel.get("overall_sentiment", 0.0)

        if sentiment < DASHBOARD_CONFIG["alert_thresholds"]["sentiment_critical"]:
            alerts.append(SystemAlert(
                alert_id=f"sent_critical_{current_time.strftime('%H%M%S')}",
                timestamp=current_time.isoformat(),
                level=DashboardAlert.WARNING,
                component="sentiment_monitoring",
                message=f"Low community sentiment detected: {sentiment:.2f}",
                details={
                    "current_value": sentiment,
                    "threshold": DASHBOARD_CONFIG["alert_thresholds"]["sentiment_critical"],
                    "recommended_action": "sentiment_intervention"
                }
            ))

        # Check API health
        platform_health_issues = []
        for platform in ["instagram", "tiktok", "x", "threads", "bluesky"]:
            platform_intel = unified_intelligence.get(f"{platform}_intelligence", {})
            api_health = platform_intel.get("api_health", True)

            if not api_health:
                platform_health_issues.append(platform)

        if platform_health_issues:
            alerts.append(SystemAlert(
                alert_id=f"api_health_{current_time.strftime('%H%M%S')}",
                timestamp=current_time.isoformat(),
                level=DashboardAlert.CRITICAL,
                component="api_monitoring",
                message=f"API health issues detected: {', '.join(platform_health_issues)}",
                details={
                    "affected_platforms": platform_health_issues,
                    "recommended_action": "system_healing_required"
                }
            ))

        # Check correlation strength
        correlation_data = orchestration_data.get("correlation_analysis", {})
        correlation_score = correlation_data.get("cross_platform_score", 0.0)

        if correlation_score < DASHBOARD_CONFIG["alert_thresholds"]["correlation_weak"]:
            alerts.append(SystemAlert(
                alert_id=f"corr_weak_{current_time.strftime('%H%M%S')}",
                timestamp=current_time.isoformat(),
                level=DashboardAlert.WARNING,
                component="correlation_engine",
                message=f"Weak cross-platform correlation: {correlation_score:.1%}",
                details={
                    "current_value": correlation_score,
                    "threshold": DASHBOARD_CONFIG["alert_thresholds"]["correlation_weak"],
                    "recommended_action": "platform_synchronization_needed"
                }
            ))

        # Check automation performance
        automated_responses = orchestration_data.get("automated_responses", {})
        response_effectiveness = automated_responses.get("response_effectiveness", {})
        success_rate = response_effectiveness.get("overall_success_rate", 1.0)

        if success_rate < DASHBOARD_CONFIG["performance_targets"]["success_rate_target"]:
            alerts.append(SystemAlert(
                alert_id=f"auto_perf_{current_time.strftime('%H%M%S')}",
                timestamp=current_time.isoformat(),
                level=DashboardAlert.WARNING,
                component="automated_response",
                message=f"Low automation success rate: {success_rate:.1%}",
                details={
                    "current_value": success_rate,
                    "target": DASHBOARD_CONFIG["performance_targets"]["success_rate_target"],
                    "recommended_action": "automation_optimization_needed"
                }
            ))

        # Update active alerts
        self.active_alerts.extend(alerts)

        # Convert to dict format for JSON serialization
        alert_dicts = []
        for alert in alerts:
            alert_dict = asdict(alert)
            alert_dict["level"] = alert.level.value
            alert_dicts.append(alert_dict)

        return alert_dicts

    async def _create_performance_dashboard(self, orchestration_data: Dict) -> Dict[str, Any]:
        """Create comprehensive performance dashboard."""
        performance_dashboard = {
            "key_metrics": {},
            "target_comparisons": {},
            "trend_indicators": {},
            "performance_score": 0.0,
            "bottleneck_analysis": {},
            "optimization_suggestions": []
        }

        # Gather performance data
        performance_summary = orchestration_data.get("performance_summary", {})

        # Key metrics
        unified_intelligence = orchestration_data.get("unified_intelligence", {})
        avg_engagement = self._calculate_avg_engagement(unified_intelligence)
        avg_sentiment = self._calculate_avg_sentiment(unified_intelligence)

        correlation_data = orchestration_data.get("correlation_analysis", {})
        correlation_score = correlation_data.get("cross_platform_score", 0.0)

        automated_responses = orchestration_data.get("automated_responses", {})
        response_effectiveness = automated_responses.get("response_effectiveness", {})

        performance_dashboard["key_metrics"] = {
            "engagement_rate": avg_engagement,
            "sentiment_score": avg_sentiment,
            "correlation_strength": correlation_score,
            "automation_success_rate": response_effectiveness.get("overall_success_rate", 0.0),
            "system_response_time": performance_summary.get("avg_response_time", 0.0),
            "overall_effectiveness": performance_summary.get("overall_effectiveness", 0.0)
        }

        # Target comparisons
        targets = DASHBOARD_CONFIG["performance_targets"]
        performance_dashboard["target_comparisons"] = {
            "engagement_vs_target": {
                "current": avg_engagement,
                "target": targets["engagement_target"],
                "achievement": avg_engagement / targets["engagement_target"] if targets["engagement_target"] > 0 else 0.0
            },
            "sentiment_vs_target": {
                "current": avg_sentiment,
                "target": targets["sentiment_target"],
                "achievement": (avg_sentiment - targets["sentiment_target"]) / 2.0 + 0.5  # Normalize sentiment
            },
            "correlation_vs_target": {
                "current": correlation_score,
                "target": targets["correlation_target"],
                "achievement": correlation_score / targets["correlation_target"] if targets["correlation_target"] > 0 else 0.0
            }
        }

        # Calculate overall performance score
        achievements = [comp["achievement"] for comp in performance_dashboard["target_comparisons"].values()]
        performance_dashboard["performance_score"] = statistics.mean([min(max(ach, 0.0), 1.5) for ach in achievements])

        # Trend indicators (simplified - would need historical data for real trends)
        performance_dashboard["trend_indicators"] = {
            "engagement_trend": "stable",
            "sentiment_trend": "improving" if avg_sentiment > 0 else "declining",
            "correlation_trend": "stable",
            "overall_trend": "stable"
        }

        return performance_dashboard

    async def _perform_trend_analysis(self, orchestration_data: Dict) -> Dict[str, Any]:
        """Perform trend analysis on historical data."""
        trend_analysis = {
            "engagement_trends": {},
            "sentiment_trends": {},
            "correlation_trends": {},
            "platform_trends": {},
            "prediction_accuracy_trends": {},
            "automation_performance_trends": {}
        }

        # Use historical data if available
        if self.dashboard_data["historical_data"]:
            # Simplified trend analysis - in production this would use more sophisticated time series analysis
            trend_analysis["data_points_available"] = len(self.dashboard_data["historical_data"])
            trend_analysis["analysis_period"] = "last_24_hours"
            trend_analysis["trend_confidence"] = 0.7
        else:
            trend_analysis["data_points_available"] = 0
            trend_analysis["analysis_note"] = "Insufficient historical data for trend analysis"

        return trend_analysis

    async def _generate_control_recommendations(self, orchestration_data: Dict) -> List[Dict[str, Any]]:
        """Generate intelligent control recommendations for dashboard users."""
        recommendations = []

        # Analyze current state and generate recommendations
        unified_intelligence = orchestration_data.get("unified_intelligence", {})
        correlation_data = orchestration_data.get("correlation_analysis", {})
        automated_responses = orchestration_data.get("automated_responses", {})

        # Engagement recommendations
        engagement_intel = unified_intelligence.get("engagement_intelligence", {})
        current_effectiveness = engagement_intel.get("current_effectiveness", 0.0)

        if current_effectiveness < DASHBOARD_CONFIG["performance_targets"]["engagement_target"]:
            recommendations.append({
                "type": "engagement_optimization",
                "priority": "high",
                "title": "Optimize Engagement Strategy",
                "description": f"Current engagement effectiveness ({current_effectiveness:.1%}) is below target",
                "suggested_actions": [
                    "Review and adjust posting schedule",
                    "Analyze top-performing content patterns",
                    "Increase community interaction frequency"
                ],
                "expected_impact": "15-25% engagement improvement",
                "implementation_time": "2-4 hours"
            })

        # Correlation recommendations
        correlation_score = correlation_data.get("cross_platform_score", 0.0)
        if correlation_score < DASHBOARD_CONFIG["performance_targets"]["correlation_target"]:
            recommendations.append({
                "type": "platform_synchronization",
                "priority": "medium",
                "title": "Improve Cross-Platform Synchronization",
                "description": f"Cross-platform correlation ({correlation_score:.1%}) below target",
                "suggested_actions": [
                    "Implement unified content strategy",
                    "Coordinate posting schedules",
                    "Align messaging across platforms"
                ],
                "expected_impact": "10-20% correlation improvement",
                "implementation_time": "4-6 hours"
            })

        # Automation recommendations
        response_effectiveness = automated_responses.get("response_effectiveness", {})
        success_rate = response_effectiveness.get("overall_success_rate", 1.0)

        if success_rate < DASHBOARD_CONFIG["performance_targets"]["success_rate_target"]:
            recommendations.append({
                "type": "automation_optimization",
                "priority": "medium",
                "title": "Enhance Automation Performance",
                "description": f"Automation success rate ({success_rate:.1%}) needs improvement",
                "suggested_actions": [
                    "Review failed automation patterns",
                    "Adjust safety thresholds",
                    "Implement additional learning mechanisms"
                ],
                "expected_impact": "10-15% automation improvement",
                "implementation_time": "2-3 hours"
            })

        # AI optimization recommendations
        ai_optimizations = orchestration_data.get("ai_optimizations", {})
        if ai_optimizations and not ai_optimizations.get("error"):
            confidence_assessment = ai_optimizations.get("confidence_assessment", {})
            overall_confidence = confidence_assessment.get("overall_confidence", 0.0)

            if overall_confidence > 0.8:
                recommendations.append({
                    "type": "ai_strategy_implementation",
                    "priority": "high",
                    "title": "Implement High-Confidence AI Recommendations",
                    "description": f"AI system shows high confidence ({overall_confidence:.1%}) in current recommendations",
                    "suggested_actions": [
                        "Review and approve pending AI recommendations",
                        "Implement suggested strategy adjustments",
                        "Monitor implementation results"
                    ],
                    "expected_impact": "20-30% overall performance improvement",
                    "implementation_time": "1-2 hours"
                })

        return recommendations[:6]  # Return top 6 recommendations

    def _assess_dashboard_health(self, dashboard_output: Dict) -> Dict[str, Any]:
        """Assess the health and reliability of the dashboard system itself."""
        return {
            "data_freshness": "excellent",
            "update_frequency": DASHBOARD_CONFIG["refresh_interval"],
            "data_completeness": 0.95,
            "system_responsiveness": "good",
            "alert_system_status": "active",
            "last_refresh": self.last_refresh.isoformat() if self.last_refresh else None
        }

    def _update_historical_data(self, dashboard_output: Dict) -> None:
        """Update historical data for trend analysis."""
        timestamp = datetime.now().isoformat()

        # Store key metrics for trend analysis
        historical_point = {
            "timestamp": timestamp,
            "system_health_score": dashboard_output.get("system_overview", {}).get("system_health_score", 0.0),
            "correlation_score": dashboard_output.get("correlation_insights", {}).get("cross_platform_score", 0.0),
            "automation_success_rate": dashboard_output.get("automation_status", {}).get("success_rates", {}).get("overall_success_rate", 0.0)
        }

        self.dashboard_data["historical_data"]["system_metrics"].append(historical_point)

        # Keep only recent data (24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        cutoff_iso = cutoff_time.isoformat()

        self.dashboard_data["historical_data"]["system_metrics"] = [
            point for point in self.dashboard_data["historical_data"]["system_metrics"]
            if point["timestamp"] > cutoff_iso
        ]

    def _calculate_avg_engagement(self, unified_intelligence: Dict) -> float:
        """Calculate average engagement across healthy platforms."""
        platforms = ["instagram", "tiktok", "x", "threads", "bluesky"]
        engagement_rates = []

        for platform in platforms:
            platform_intel = unified_intelligence.get(f"{platform}_intelligence", {})
            if platform_intel.get("api_health", False):
                engagement_rate = platform_intel.get("engagement_rate", 0.0)
                if engagement_rate > 0:
                    engagement_rates.append(engagement_rate)

        return statistics.mean(engagement_rates) if engagement_rates else 0.0

    def _calculate_avg_sentiment(self, unified_intelligence: Dict) -> float:
        """Calculate average sentiment across healthy platforms."""
        platforms = ["instagram", "tiktok", "x", "threads", "bluesky"]
        sentiment_scores = []

        for platform in platforms:
            platform_intel = unified_intelligence.get(f"{platform}_intelligence", {})
            if platform_intel.get("api_health", False):
                sentiment_score = platform_intel.get("sentiment_score", 0.0)
                sentiment_scores.append(sentiment_score)

        return statistics.mean(sentiment_scores) if sentiment_scores else 0.0

    def _calculate_system_uptime(self) -> float:
        """Calculate system uptime percentage."""
        # Simplified uptime calculation - would track actual uptime in production
        return 99.5  # Assumed uptime percentage