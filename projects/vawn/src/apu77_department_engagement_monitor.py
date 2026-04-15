"""
APU-77 Department-Specific Engagement Monitor
=============================================
Created by: Claude Code Implementation Agent (APU-77)

Advanced department-specific engagement monitoring system for Apulu Records
organizational health tracking. Focuses on strategic department performance
rather than crisis response, enabling data-driven organizational optimization.

Key Features:
- Department-specific health metrics for A&R, Creative Revenue, Operations, Legal
- Strategic oversight dashboard for Chairman/CoS organizational coordination
- Multi-artist scaling preparation with department coordination tracking
- Integration with APU-74 alert system for escalation management
- Department success metrics aligned with Apulu Records strategic objectives
- Cross-department coordination tracking and optimization recommendations

Department Structure:
- A&R (Timbo): talent_discovery, community_insights, collaboration_tracking
- Creative Revenue (Letitia): campaign_effectiveness, content_performance, revenue_optimization
- Operations (Nari): system_reliability, performance_tracking, operational_efficiency
- Legal (Nelly): compliance_rates, brand_protection, legal_risk_mitigation
- Chairman (CoS): organizational_health, strategic_coordination, performance_oversight

Core Innovation:
Transforms departmental monitoring from reactive crisis management to proactive
organizational health optimization, enabling strategic decision-making and
department coordination at the executive level.
"""

import json
import sys
import time
import statistics
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional, Union
import re
from dataclasses import dataclass, asdict
from collections import defaultdict
import traceback

# Add Vawn directory to Python path
sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import (
    load_json, save_json, ENGAGEMENT_LOG, RESEARCH_LOG, METRICS_LOG,
    VAWN_DIR, log_run, today_str, get_anthropic_client
)

# APU-77 Configuration
APU77_LOG_DIR = VAWN_DIR / "research" / "apu77_department_engagement"
APU77_LOG_DIR.mkdir(exist_ok=True)

# Department-Specific Log Files
DEPARTMENT_HEALTH_LOG = APU77_LOG_DIR / "department_health.json"
ORGANIZATIONAL_OVERVIEW_LOG = APU77_LOG_DIR / "organizational_overview.json"
DEPARTMENT_COORDINATION_LOG = APU77_LOG_DIR / "department_coordination.json"
STRATEGIC_METRICS_LOG = APU77_LOG_DIR / "strategic_metrics.json"
CROSS_DEPARTMENT_ANALYTICS_LOG = APU77_LOG_DIR / "cross_department_analytics.json"
EXECUTIVE_DASHBOARD_LOG = APU77_LOG_DIR / "executive_dashboard.json"
DEPARTMENT_TRENDS_LOG = APU77_LOG_DIR / "department_trends.json"

# Integration with APU Ecosystem
APU74_ALERT_LOG = VAWN_DIR / "research" / "apu74_intelligent_engagement" / "live_response_dashboard.json"
APU76_COORDINATION_LOG = VAWN_DIR / "research" / "apu76_unified_coordination" / "unified_dashboard.json"
APU68_UNIVERSE_LOG = VAWN_DIR / "research" / "apu68_apulu_universe_log.json"

# Department Configuration
DEPARTMENT_CONFIG = {
    "a_and_r": {
        "head": "Timbo",
        "department_name": "A&R",
        "focus_areas": ["talent_discovery", "community_insights", "collaboration_tracking"],
        "success_metrics": {
            "talent_discovery_rate": {"target": 2.0, "weight": 0.3},  # discoveries per week
            "community_engagement_growth": {"target": 5.0, "weight": 0.3},  # % weekly growth
            "collaboration_facilitation": {"target": 1.0, "weight": 0.25},  # collaborations per month
            "artist_relationship_strength": {"target": 0.8, "weight": 0.15}  # relationship score
        },
        "health_indicators": [
            "discovery_pipeline_strength",
            "community_sentiment_score",
            "collaboration_success_rate",
            "industry_network_reach"
        ],
        "operational_metrics": {
            "response_time_hours": {"target": 4, "weight": 0.4},
            "quality_assessment_score": {"target": 0.85, "weight": 0.35},
            "follow_through_rate": {"target": 0.9, "weight": 0.25}
        }
    },
    "creative_revenue": {
        "head": "Letitia",
        "department_name": "Creative Revenue",
        "focus_areas": ["campaign_effectiveness", "content_performance", "revenue_optimization"],
        "success_metrics": {
            "campaign_roi": {"target": 3.5, "weight": 0.35},  # return on investment
            "content_engagement_rate": {"target": 0.08, "weight": 0.25},  # 8% average engagement
            "revenue_growth": {"target": 15.0, "weight": 0.3},  # % monthly growth
            "conversion_optimization": {"target": 0.12, "weight": 0.1}  # conversion rate
        },
        "health_indicators": [
            "campaign_performance_consistency",
            "content_quality_score",
            "revenue_stream_diversification",
            "market_positioning_strength"
        ],
        "operational_metrics": {
            "campaign_launch_efficiency": {"target": 0.9, "weight": 0.3},
            "content_production_velocity": {"target": 12, "weight": 0.35},  # pieces per week
            "revenue_tracking_accuracy": {"target": 0.98, "weight": 0.35}
        }
    },
    "operations": {
        "head": "Nari",
        "department_name": "Operations",
        "focus_areas": ["system_reliability", "performance_tracking", "operational_efficiency"],
        "success_metrics": {
            "system_uptime": {"target": 99.5, "weight": 0.4},  # % uptime
            "performance_optimization": {"target": 20.0, "weight": 0.25},  # % improvement monthly
            "operational_cost_efficiency": {"target": 85.0, "weight": 0.2},  # efficiency score
            "incident_resolution_time": {"target": 2.0, "weight": 0.15}  # hours average
        },
        "health_indicators": [
            "infrastructure_stability",
            "automation_coverage",
            "process_optimization_level",
            "technical_debt_management"
        ],
        "operational_metrics": {
            "deployment_success_rate": {"target": 0.98, "weight": 0.3},
            "monitoring_coverage": {"target": 0.95, "weight": 0.25},
            "backup_recovery_time": {"target": 30, "weight": 0.25},  # minutes
            "security_compliance_score": {"target": 0.95, "weight": 0.2}
        }
    },
    "legal": {
        "head": "Nelly",
        "department_name": "Legal",
        "focus_areas": ["compliance_rates", "brand_protection", "legal_risk_mitigation"],
        "success_metrics": {
            "compliance_adherence": {"target": 98.0, "weight": 0.35},  # % compliance rate
            "brand_protection_effectiveness": {"target": 95.0, "weight": 0.25},  # protection score
            "risk_mitigation_success": {"target": 90.0, "weight": 0.25},  # % risks mitigated
            "contract_negotiation_efficiency": {"target": 7.0, "weight": 0.15}  # days average
        },
        "health_indicators": [
            "regulatory_compliance_status",
            "intellectual_property_protection",
            "contract_portfolio_health",
            "litigation_risk_level"
        ],
        "operational_metrics": {
            "legal_review_turnaround": {"target": 2, "weight": 0.3},  # days
            "compliance_audit_score": {"target": 0.95, "weight": 0.3},
            "brand_monitoring_coverage": {"target": 0.9, "weight": 0.2},
            "risk_assessment_accuracy": {"target": 0.88, "weight": 0.2}
        }
    }
}

# Chairman/CoS Strategic Oversight Configuration
STRATEGIC_OVERSIGHT_CONFIG = {
    "organizational_health_metrics": {
        "cross_department_coordination": {"target": 0.85, "weight": 0.25},
        "strategic_objective_alignment": {"target": 0.9, "weight": 0.3},
        "resource_allocation_efficiency": {"target": 0.8, "weight": 0.2},
        "organizational_agility_score": {"target": 0.75, "weight": 0.25}
    },
    "executive_kpis": {
        "department_synergy_score": {"target": 0.8, "critical": True},
        "strategic_initiative_progress": {"target": 0.85, "critical": True},
        "organizational_culture_health": {"target": 0.9, "critical": False},
        "scalability_readiness": {"target": 0.75, "critical": True}
    },
    "escalation_thresholds": {
        "department_health_critical": 0.6,
        "coordination_failure": 0.5,
        "strategic_deviation": 0.7,
        "operational_crisis": 0.4
    }
}

# Multi-Artist Scaling Preparation
SCALING_METRICS = {
    "infrastructure_readiness": {
        "system_capacity_headroom": {"target": 40.0, "weight": 0.3},  # % capacity available
        "process_scalability_score": {"target": 0.8, "weight": 0.25},
        "team_expansion_readiness": {"target": 0.75, "weight": 0.25},
        "technology_stack_maturity": {"target": 0.85, "weight": 0.2}
    },
    "department_expansion_readiness": {
        "a_and_r": {"current_capacity": 1.0, "scaling_target": 3.0, "readiness": 0.7},
        "creative_revenue": {"current_capacity": 1.0, "scaling_target": 4.0, "readiness": 0.6},
        "operations": {"current_capacity": 1.0, "scaling_target": 2.0, "readiness": 0.8},
        "legal": {"current_capacity": 1.0, "scaling_target": 2.0, "readiness": 0.65}
    }
}

@dataclass
class DepartmentMetrics:
    """Department-specific performance metrics."""
    department_id: str
    department_name: str
    head: str
    timestamp: str

    # Core Success Metrics
    success_score: float
    operational_efficiency: float
    health_score: float

    # Detailed Metrics
    success_metrics: Dict[str, float]
    operational_metrics: Dict[str, float]
    health_indicators: Dict[str, float]

    # Coordination Metrics
    cross_department_score: float
    strategic_alignment: float

    # Performance Trends
    trend_direction: str  # "improving", "stable", "declining"
    trend_velocity: float

    # Action Items
    recommendations: List[str]
    alerts: List[str]
    achievements: List[str]

@dataclass
class OrganizationalOverview:
    """Executive-level organizational health overview."""
    timestamp: str

    # Overall Health
    organizational_health_score: float
    department_coordination_score: float
    strategic_alignment_score: float

    # Department Summaries
    department_health_summary: Dict[str, float]
    department_trends: Dict[str, str]

    # Strategic Metrics
    strategic_objectives_progress: float
    scalability_readiness_score: float
    resource_allocation_efficiency: float

    # Executive Actions
    executive_alerts: List[str]
    strategic_recommendations: List[str]
    coordination_opportunities: List[str]

    # Performance Indicators
    organizational_momentum: str  # "accelerating", "steady", "decelerating"
    department_synergy_level: float
    crisis_risk_assessment: float

class APU77DepartmentEngagementMonitor:
    """Department-specific engagement monitoring with strategic oversight."""

    def __init__(self):
        self.name = "APU77DepartmentEngagementMonitor"
        self.version = "1.0.0"
        self.departments = list(DEPARTMENT_CONFIG.keys())
        self.client = get_anthropic_client()

        # Initialize department tracking
        self.department_state = self._initialize_department_state()

        # Performance tracking
        self.performance_history = self._load_performance_history()

        print(f"[INIT] {self.name} v{self.version} initialized")
        print(f"[INIT] Monitoring departments: {', '.join(self.departments)}")
        print(f"[INIT] Strategic oversight: Chairman/CoS level")

    def _initialize_department_state(self) -> Dict[str, Dict]:
        """Initialize department state tracking."""
        state = {}
        for dept_id in self.departments:
            dept_config = DEPARTMENT_CONFIG[dept_id]
            state[dept_id] = {
                "last_assessment": None,
                "current_health": 1.0,  # Start optimistically
                "performance_trend": "stable",
                "coordination_score": 0.8,
                "alert_level": "normal"
            }
        return state

    def _load_performance_history(self) -> Dict[str, List]:
        """Load historical performance data."""
        if DEPARTMENT_TRENDS_LOG.exists():
            return load_json(DEPARTMENT_TRENDS_LOG)
        return {dept: [] for dept in self.departments}

    def run_department_assessment(self) -> Dict[str, Any]:
        """Run comprehensive department assessment."""
        timestamp = datetime.now().isoformat()

        print(f"[ASSESS] Starting department assessment at {timestamp}")

        # Assess each department
        department_results = {}
        for dept_id in self.departments:
            print(f"[ASSESS] Evaluating {dept_id.upper()} department...")
            dept_metrics = self._assess_department(dept_id, timestamp)
            department_results[dept_id] = dept_metrics

            # Update department state
            self._update_department_state(dept_id, dept_metrics)

        # Generate organizational overview
        org_overview = self._generate_organizational_overview(department_results, timestamp)

        # Store results
        self._store_assessment_results(department_results, org_overview)

        # Check for escalations
        escalations = self._check_escalation_conditions(department_results, org_overview)

        # Update performance history
        self._update_performance_history(department_results)

        print(f"[ASSESS] Department assessment completed")
        print(f"[ASSESS] Organizational health: {org_overview.organizational_health_score:.2f}")

        return {
            "status": "completed",
            "timestamp": timestamp,
            "department_results": {k: asdict(v) for k, v in department_results.items()},
            "organizational_overview": asdict(org_overview),
            "escalations": escalations
        }

    def _assess_department(self, dept_id: str, timestamp: str) -> DepartmentMetrics:
        """Assess individual department performance."""
        dept_config = DEPARTMENT_CONFIG[dept_id]

        # Calculate success metrics
        success_metrics = self._calculate_success_metrics(dept_id)
        success_score = self._calculate_weighted_score(success_metrics, dept_config["success_metrics"])

        # Calculate operational metrics
        operational_metrics = self._calculate_operational_metrics(dept_id)
        operational_efficiency = self._calculate_weighted_score(operational_metrics, dept_config["operational_metrics"])

        # Calculate health indicators
        health_indicators = self._calculate_health_indicators(dept_id)
        health_score = statistics.mean(health_indicators.values()) if health_indicators else 0.8

        # Calculate coordination metrics
        cross_dept_score = self._calculate_cross_department_coordination(dept_id)
        strategic_alignment = self._calculate_strategic_alignment(dept_id)

        # Determine trends
        trend_direction, trend_velocity = self._analyze_performance_trends(dept_id)

        # Generate recommendations and alerts
        recommendations = self._generate_department_recommendations(dept_id, success_score, operational_efficiency, health_score)
        alerts = self._generate_department_alerts(dept_id, success_score, operational_efficiency)
        achievements = self._identify_department_achievements(dept_id, success_metrics, operational_metrics)

        return DepartmentMetrics(
            department_id=dept_id,
            department_name=dept_config["department_name"],
            head=dept_config["head"],
            timestamp=timestamp,
            success_score=success_score,
            operational_efficiency=operational_efficiency,
            health_score=health_score,
            success_metrics=success_metrics,
            operational_metrics=operational_metrics,
            health_indicators=health_indicators,
            cross_department_score=cross_dept_score,
            strategic_alignment=strategic_alignment,
            trend_direction=trend_direction,
            trend_velocity=trend_velocity,
            recommendations=recommendations,
            alerts=alerts,
            achievements=achievements
        )

    def _calculate_success_metrics(self, dept_id: str) -> Dict[str, float]:
        """Calculate department-specific success metrics."""
        # This would integrate with real data sources in production
        # For now, simulate realistic department performance

        base_performance = {
            "a_and_r": {
                "talent_discovery_rate": 1.8,  # slightly below target
                "community_engagement_growth": 6.2,  # above target
                "collaboration_facilitation": 0.8,  # below target
                "artist_relationship_strength": 0.85  # above target
            },
            "creative_revenue": {
                "campaign_roi": 3.8,  # above target
                "content_engagement_rate": 0.075,  # below target
                "revenue_growth": 18.5,  # above target
                "conversion_optimization": 0.11  # below target
            },
            "operations": {
                "system_uptime": 99.7,  # above target
                "performance_optimization": 22.0,  # above target
                "operational_cost_efficiency": 82.0,  # below target
                "incident_resolution_time": 1.8  # above target
            },
            "legal": {
                "compliance_adherence": 97.5,  # below target
                "brand_protection_effectiveness": 96.0,  # above target
                "risk_mitigation_success": 92.0,  # above target
                "contract_negotiation_efficiency": 6.5  # above target
            }
        }

        return base_performance.get(dept_id, {})

    def _calculate_operational_metrics(self, dept_id: str) -> Dict[str, float]:
        """Calculate department operational efficiency metrics."""
        base_operational = {
            "a_and_r": {
                "response_time_hours": 3.5,  # above target
                "quality_assessment_score": 0.88,  # above target
                "follow_through_rate": 0.85  # below target
            },
            "creative_revenue": {
                "campaign_launch_efficiency": 0.92,  # above target
                "content_production_velocity": 14,  # above target
                "revenue_tracking_accuracy": 0.96  # below target
            },
            "operations": {
                "deployment_success_rate": 0.99,  # above target
                "monitoring_coverage": 0.93,  # below target
                "backup_recovery_time": 25,  # above target
                "security_compliance_score": 0.97  # above target
            },
            "legal": {
                "legal_review_turnaround": 1.8,  # above target
                "compliance_audit_score": 0.96,  # above target
                "brand_monitoring_coverage": 0.88,  # below target
                "risk_assessment_accuracy": 0.90  # above target
            }
        }

        return base_operational.get(dept_id, {})

    def _calculate_health_indicators(self, dept_id: str) -> Dict[str, float]:
        """Calculate department health indicators."""
        # Simulate health indicators based on department focus
        base_health = {
            "a_and_r": {
                "discovery_pipeline_strength": 0.82,
                "community_sentiment_score": 0.88,
                "collaboration_success_rate": 0.75,
                "industry_network_reach": 0.85
            },
            "creative_revenue": {
                "campaign_performance_consistency": 0.86,
                "content_quality_score": 0.89,
                "revenue_stream_diversification": 0.78,
                "market_positioning_strength": 0.84
            },
            "operations": {
                "infrastructure_stability": 0.94,
                "automation_coverage": 0.87,
                "process_optimization_level": 0.82,
                "technical_debt_management": 0.79
            },
            "legal": {
                "regulatory_compliance_status": 0.95,
                "intellectual_property_protection": 0.91,
                "contract_portfolio_health": 0.88,
                "litigation_risk_level": 0.92  # higher is better (lower risk)
            }
        }

        return base_health.get(dept_id, {})

    def _calculate_weighted_score(self, metrics: Dict[str, float], targets: Dict[str, Dict]) -> float:
        """Calculate weighted performance score against targets."""
        if not metrics or not targets:
            return 0.8  # Default score

        total_weight = 0.0
        weighted_score = 0.0

        for metric_name, metric_value in metrics.items():
            if metric_name in targets:
                target_config = targets[metric_name]
                target_value = target_config["target"]
                weight = target_config["weight"]

                # Calculate performance ratio (handle different metric types)
                if "time" in metric_name.lower() or "hours" in metric_name.lower():
                    # Lower is better for time metrics
                    performance_ratio = min(target_value / max(metric_value, 0.1), 2.0)
                else:
                    # Higher is better for most metrics
                    performance_ratio = min(metric_value / max(target_value, 0.1), 2.0)

                weighted_score += performance_ratio * weight
                total_weight += weight

        return weighted_score / max(total_weight, 0.1)

    def _calculate_cross_department_coordination(self, dept_id: str) -> float:
        """Calculate cross-department coordination effectiveness."""
        # Simulate coordination based on department interactions
        coordination_matrix = {
            "a_and_r": {"creative_revenue": 0.85, "operations": 0.75, "legal": 0.80},
            "creative_revenue": {"a_and_r": 0.85, "operations": 0.82, "legal": 0.78},
            "operations": {"a_and_r": 0.75, "creative_revenue": 0.82, "legal": 0.88},
            "legal": {"a_and_r": 0.80, "creative_revenue": 0.78, "operations": 0.88}
        }

        if dept_id in coordination_matrix:
            scores = list(coordination_matrix[dept_id].values())
            return statistics.mean(scores)

        return 0.8  # Default coordination score

    def _calculate_strategic_alignment(self, dept_id: str) -> float:
        """Calculate department alignment with strategic objectives."""
        # Simulate strategic alignment based on department performance
        alignment_factors = {
            "a_and_r": 0.83,      # Strong artist focus
            "creative_revenue": 0.87,  # Revenue-driven alignment
            "operations": 0.85,    # Infrastructure support
            "legal": 0.82         # Compliance focus
        }

        return alignment_factors.get(dept_id, 0.8)

    def _analyze_performance_trends(self, dept_id: str) -> Tuple[str, float]:
        """Analyze department performance trends."""
        # Get recent performance history
        if dept_id in self.performance_history:
            recent_scores = self.performance_history[dept_id][-5:]  # Last 5 assessments

            if len(recent_scores) >= 2:
                # Calculate trend
                trend_slope = (recent_scores[-1] - recent_scores[0]) / len(recent_scores)

                if trend_slope > 0.02:
                    return "improving", abs(trend_slope)
                elif trend_slope < -0.02:
                    return "declining", abs(trend_slope)
                else:
                    return "stable", abs(trend_slope)

        return "stable", 0.01

    def _generate_department_recommendations(self, dept_id: str, success_score: float,
                                           operational_efficiency: float, health_score: float) -> List[str]:
        """Generate department-specific recommendations."""
        recommendations = []
        dept_config = DEPARTMENT_CONFIG[dept_id]
        dept_name = dept_config["department_name"]

        # Performance-based recommendations
        if success_score < 0.8:
            recommendations.append(f"{dept_name}: Focus on core success metrics - performance below strategic targets")

        if operational_efficiency < 0.85:
            recommendations.append(f"{dept_name}: Optimize operational processes for improved efficiency")

        if health_score < 0.8:
            recommendations.append(f"{dept_name}: Address health indicators to strengthen department foundation")

        # Department-specific recommendations
        dept_specific = {
            "a_and_r": [
                "Expand talent discovery pipeline through community engagement",
                "Strengthen collaboration facilitation processes",
                "Develop systematic artist relationship management"
            ],
            "creative_revenue": [
                "Optimize campaign ROI through data-driven targeting",
                "Enhance content engagement strategies",
                "Diversify revenue stream development"
            ],
            "operations": [
                "Increase automation coverage for operational efficiency",
                "Strengthen monitoring and alerting systems",
                "Develop scalability infrastructure for multi-artist expansion"
            ],
            "legal": [
                "Enhance brand protection monitoring systems",
                "Streamline compliance audit processes",
                "Develop proactive risk mitigation strategies"
            ]
        }

        # Add 1-2 department-specific recommendations
        if dept_id in dept_specific:
            recommendations.extend(dept_specific[dept_id][:2])

        return recommendations[:4]  # Limit to 4 recommendations

    def _generate_department_alerts(self, dept_id: str, success_score: float,
                                  operational_efficiency: float) -> List[str]:
        """Generate department-specific alerts."""
        alerts = []
        dept_config = DEPARTMENT_CONFIG[dept_id]
        dept_name = dept_config["department_name"]

        # Critical performance alerts
        if success_score < 0.6:
            alerts.append(f"CRITICAL: {dept_name} success metrics significantly below targets")

        if operational_efficiency < 0.7:
            alerts.append(f"WARNING: {dept_name} operational efficiency requires immediate attention")

        # Department-specific alerts
        if dept_id == "a_and_r" and success_score < 0.75:
            alerts.append("A&R: Talent discovery pipeline may impact future artist roster growth")

        if dept_id == "creative_revenue" and operational_efficiency < 0.8:
            alerts.append("Creative Revenue: Campaign efficiency affecting revenue optimization")

        if dept_id == "operations" and success_score < 0.8:
            alerts.append("Operations: System reliability concerns for multi-artist scaling")

        if dept_id == "legal" and operational_efficiency < 0.8:
            alerts.append("Legal: Compliance processing delays creating operational risk")

        return alerts

    def _identify_department_achievements(self, dept_id: str, success_metrics: Dict[str, float],
                                        operational_metrics: Dict[str, float]) -> List[str]:
        """Identify department achievements and successes."""
        achievements = []
        dept_config = DEPARTMENT_CONFIG[dept_id]
        dept_name = dept_config["department_name"]

        # Check success metrics against targets
        for metric_name, metric_value in success_metrics.items():
            if metric_name in dept_config["success_metrics"]:
                target = dept_config["success_metrics"][metric_name]["target"]
                if metric_value >= target * 1.1:  # 10% above target
                    achievements.append(f"{dept_name}: Exceeded target for {metric_name.replace('_', ' ')}")

        # Check operational metrics
        for metric_name, metric_value in operational_metrics.items():
            if metric_name in dept_config["operational_metrics"]:
                target = dept_config["operational_metrics"][metric_name]["target"]
                if "time" in metric_name.lower():
                    # Lower is better for time metrics
                    if metric_value <= target * 0.9:  # 10% better than target
                        achievements.append(f"{dept_name}: Outstanding {metric_name.replace('_', ' ')} performance")
                else:
                    if metric_value >= target * 1.1:  # 10% above target
                        achievements.append(f"{dept_name}: Excellence in {metric_name.replace('_', ' ')}")

        return achievements[:3]  # Limit to 3 achievements

    def _generate_organizational_overview(self, department_results: Dict[str, DepartmentMetrics],
                                        timestamp: str) -> OrganizationalOverview:
        """Generate executive-level organizational overview."""

        # Calculate overall organizational health
        dept_health_scores = [metrics.health_score for metrics in department_results.values()]
        org_health_score = statistics.mean(dept_health_scores)

        # Calculate department coordination
        coord_scores = [metrics.cross_department_score for metrics in department_results.values()]
        dept_coordination_score = statistics.mean(coord_scores)

        # Calculate strategic alignment
        alignment_scores = [metrics.strategic_alignment for metrics in department_results.values()]
        strategic_alignment_score = statistics.mean(alignment_scores)

        # Department summaries
        dept_health_summary = {
            dept_id: metrics.health_score for dept_id, metrics in department_results.items()
        }
        dept_trends = {
            dept_id: metrics.trend_direction for dept_id, metrics in department_results.items()
        }

        # Calculate strategic metrics
        strategic_objectives_progress = self._calculate_strategic_progress(department_results)
        scalability_readiness = self._calculate_scalability_readiness(department_results)
        resource_allocation_efficiency = self._calculate_resource_efficiency(department_results)

        # Generate executive actions
        exec_alerts = self._generate_executive_alerts(department_results, org_health_score)
        strategic_recommendations = self._generate_strategic_recommendations(department_results)
        coordination_opportunities = self._identify_coordination_opportunities(department_results)

        # Determine organizational momentum
        improvement_trend = sum(1 for metrics in department_results.values() if metrics.trend_direction == "improving")
        declining_trend = sum(1 for metrics in department_results.values() if metrics.trend_direction == "declining")

        if improvement_trend > declining_trend + 1:
            org_momentum = "accelerating"
        elif declining_trend > improvement_trend + 1:
            org_momentum = "decelerating"
        else:
            org_momentum = "steady"

        # Calculate department synergy
        dept_synergy = statistics.mean(coord_scores) * strategic_alignment_score

        # Calculate crisis risk
        crisis_risk = self._calculate_crisis_risk(department_results)

        return OrganizationalOverview(
            timestamp=timestamp,
            organizational_health_score=org_health_score,
            department_coordination_score=dept_coordination_score,
            strategic_alignment_score=strategic_alignment_score,
            department_health_summary=dept_health_summary,
            department_trends=dept_trends,
            strategic_objectives_progress=strategic_objectives_progress,
            scalability_readiness_score=scalability_readiness,
            resource_allocation_efficiency=resource_allocation_efficiency,
            executive_alerts=exec_alerts,
            strategic_recommendations=strategic_recommendations,
            coordination_opportunities=coordination_opportunities,
            organizational_momentum=org_momentum,
            department_synergy_level=dept_synergy,
            crisis_risk_assessment=crisis_risk
        )

    def _calculate_strategic_progress(self, department_results: Dict[str, DepartmentMetrics]) -> float:
        """Calculate progress toward strategic objectives."""
        # Weight departments by their strategic importance
        strategic_weights = {"a_and_r": 0.25, "creative_revenue": 0.35, "operations": 0.25, "legal": 0.15}

        weighted_progress = 0.0
        for dept_id, metrics in department_results.items():
            dept_progress = (metrics.success_score + metrics.strategic_alignment) / 2
            weight = strategic_weights.get(dept_id, 0.25)
            weighted_progress += dept_progress * weight

        return weighted_progress

    def _calculate_scalability_readiness(self, department_results: Dict[str, DepartmentMetrics]) -> float:
        """Calculate readiness for multi-artist scaling."""
        scaling_scores = []

        for dept_id, metrics in department_results.items():
            # Combine operational efficiency with scaling readiness factors
            scaling_factor = SCALING_METRICS["department_expansion_readiness"][dept_id]["readiness"]
            dept_scaling_score = (metrics.operational_efficiency + scaling_factor) / 2
            scaling_scores.append(dept_scaling_score)

        return statistics.mean(scaling_scores)

    def _calculate_resource_efficiency(self, department_results: Dict[str, DepartmentMetrics]) -> float:
        """Calculate resource allocation efficiency across departments."""
        efficiency_scores = [metrics.operational_efficiency for metrics in department_results.values()]
        return statistics.mean(efficiency_scores)

    def _generate_executive_alerts(self, department_results: Dict[str, DepartmentMetrics],
                                 org_health_score: float) -> List[str]:
        """Generate executive-level alerts."""
        alerts = []

        # Organizational health alerts
        if org_health_score < 0.7:
            alerts.append("CRITICAL: Organizational health below acceptable threshold")

        # Department-specific executive alerts
        critical_depts = [
            dept_id for dept_id, metrics in department_results.items()
            if metrics.health_score < 0.6
        ]

        if critical_depts:
            alerts.append(f"URGENT: Critical performance in departments: {', '.join(critical_depts)}")

        # Coordination alerts
        poor_coordination = [
            dept_id for dept_id, metrics in department_results.items()
            if metrics.cross_department_score < 0.6
        ]

        if poor_coordination:
            alerts.append(f"COORDINATION: Poor cross-department coordination in: {', '.join(poor_coordination)}")

        # Scaling readiness alerts
        scaling_readiness = self._calculate_scalability_readiness(department_results)
        if scaling_readiness < 0.7:
            alerts.append("SCALING: Organization not ready for multi-artist expansion")

        return alerts

    def _generate_strategic_recommendations(self, department_results: Dict[str, DepartmentMetrics]) -> List[str]:
        """Generate strategic recommendations for executive action."""
        recommendations = []

        # Analyze department performance patterns
        underperforming = [
            dept_id for dept_id, metrics in department_results.items()
            if metrics.success_score < 0.75
        ]

        if underperforming:
            recommendations.append(f"Focus executive attention on underperforming departments: {', '.join(underperforming)}")

        # Coordination improvements
        poor_coordinators = [
            dept_id for dept_id, metrics in department_results.items()
            if metrics.cross_department_score < 0.75
        ]

        if poor_coordinators:
            recommendations.append("Implement cross-department coordination improvement initiatives")

        # Strategic alignment
        misaligned_depts = [
            dept_id for dept_id, metrics in department_results.items()
            if metrics.strategic_alignment < 0.8
        ]

        if misaligned_depts:
            recommendations.append("Conduct strategic alignment sessions with department heads")

        # Scaling preparation
        scaling_readiness = self._calculate_scalability_readiness(department_results)
        if scaling_readiness < 0.8:
            recommendations.append("Prioritize multi-artist scaling preparation initiatives")

        return recommendations[:4]  # Limit to 4 strategic recommendations

    def _identify_coordination_opportunities(self, department_results: Dict[str, DepartmentMetrics]) -> List[str]:
        """Identify cross-department coordination opportunities."""
        opportunities = []

        # Analyze potential synergies
        strong_performers = [
            dept_id for dept_id, metrics in department_results.items()
            if metrics.success_score > 0.85
        ]

        weak_performers = [
            dept_id for dept_id, metrics in department_results.items()
            if metrics.success_score < 0.75
        ]

        if strong_performers and weak_performers:
            opportunities.append(f"Pair high-performing departments ({', '.join(strong_performers)}) with developing departments for knowledge transfer")

        # Specific coordination opportunities
        opportunities.extend([
            "A&R and Creative Revenue: Joint artist development and campaign planning sessions",
            "Operations and Legal: Integrated compliance and system security protocols",
            "Creative Revenue and Operations: Campaign infrastructure optimization collaboration"
        ])

        return opportunities[:4]

    def _calculate_crisis_risk(self, department_results: Dict[str, DepartmentMetrics]) -> float:
        """Calculate organizational crisis risk assessment."""
        risk_factors = []

        for dept_id, metrics in department_results.items():
            # Department health risk
            health_risk = max(0, (0.8 - metrics.health_score))

            # Performance decline risk
            decline_risk = 0.1 if metrics.trend_direction == "declining" else 0

            # Coordination failure risk
            coord_risk = max(0, (0.7 - metrics.cross_department_score)) * 0.5

            dept_risk = health_risk + decline_risk + coord_risk
            risk_factors.append(dept_risk)

        # Overall organizational risk
        org_risk = statistics.mean(risk_factors)

        # Cap at 1.0 and normalize to 0-1 scale
        return min(org_risk, 1.0)

    def _check_escalation_conditions(self, department_results: Dict[str, DepartmentMetrics],
                                   org_overview: OrganizationalOverview) -> List[Dict[str, Any]]:
        """Check for conditions requiring escalation to APU-74 or executive action."""
        escalations = []
        escalation_config = STRATEGIC_OVERSIGHT_CONFIG["escalation_thresholds"]

        # Department health escalations
        for dept_id, metrics in department_results.items():
            if metrics.health_score < escalation_config["department_health_critical"]:
                escalations.append({
                    "type": "department_critical",
                    "department": dept_id,
                    "severity": "critical",
                    "condition": f"Department health score {metrics.health_score:.2f} below critical threshold",
                    "recommended_action": "immediate_executive_intervention",
                    "apu74_integration": True
                })

        # Coordination failure escalations
        if org_overview.department_coordination_score < escalation_config["coordination_failure"]:
            escalations.append({
                "type": "coordination_failure",
                "severity": "high",
                "condition": f"Cross-department coordination {org_overview.department_coordination_score:.2f} below threshold",
                "recommended_action": "emergency_coordination_session",
                "apu74_integration": True
            })

        # Strategic deviation escalations
        if org_overview.strategic_objectives_progress < escalation_config["strategic_deviation"]:
            escalations.append({
                "type": "strategic_deviation",
                "severity": "high",
                "condition": f"Strategic progress {org_overview.strategic_objectives_progress:.2f} significantly behind",
                "recommended_action": "strategic_realignment_session",
                "apu74_integration": False
            })

        # Operational crisis escalations
        if org_overview.crisis_risk_assessment > escalation_config["operational_crisis"]:
            escalations.append({
                "type": "operational_crisis_risk",
                "severity": "critical",
                "condition": f"Crisis risk assessment {org_overview.crisis_risk_assessment:.2f} exceeds threshold",
                "recommended_action": "crisis_prevention_protocol",
                "apu74_integration": True
            })

        return escalations

    def _update_department_state(self, dept_id: str, metrics: DepartmentMetrics):
        """Update internal department state tracking."""
        self.department_state[dept_id].update({
            "last_assessment": metrics.timestamp,
            "current_health": metrics.health_score,
            "performance_trend": metrics.trend_direction,
            "coordination_score": metrics.cross_department_score,
            "alert_level": "critical" if metrics.health_score < 0.6 else "warning" if metrics.health_score < 0.8 else "normal"
        })

    def _update_performance_history(self, department_results: Dict[str, DepartmentMetrics]):
        """Update performance history for trend analysis."""
        for dept_id, metrics in department_results.items():
            if dept_id not in self.performance_history:
                self.performance_history[dept_id] = []

            # Store combined performance score
            combined_score = (metrics.success_score + metrics.operational_efficiency + metrics.health_score) / 3
            self.performance_history[dept_id].append(combined_score)

            # Keep only last 20 entries for trend analysis
            if len(self.performance_history[dept_id]) > 20:
                self.performance_history[dept_id] = self.performance_history[dept_id][-20:]

        # Save updated history
        save_json(DEPARTMENT_TRENDS_LOG, self.performance_history)

    def _store_assessment_results(self, department_results: Dict[str, DepartmentMetrics],
                                org_overview: OrganizationalOverview):
        """Store assessment results to log files."""
        timestamp = datetime.now().isoformat()

        # Store department health
        dept_health_data = {
            "timestamp": timestamp,
            "departments": {dept_id: asdict(metrics) for dept_id, metrics in department_results.items()}
        }
        save_json(DEPARTMENT_HEALTH_LOG, dept_health_data)

        # Store organizational overview
        org_data = asdict(org_overview)
        save_json(ORGANIZATIONAL_OVERVIEW_LOG, org_data)

        # Store executive dashboard
        dashboard_data = {
            "last_updated": timestamp,
            "organizational_health": org_overview.organizational_health_score,
            "department_summary": org_overview.department_health_summary,
            "strategic_progress": org_overview.strategic_objectives_progress,
            "scalability_readiness": org_overview.scalability_readiness_score,
            "crisis_risk": org_overview.crisis_risk_assessment,
            "executive_alerts": org_overview.executive_alerts,
            "strategic_recommendations": org_overview.strategic_recommendations,
            "coordination_opportunities": org_overview.coordination_opportunities
        }
        save_json(EXECUTIVE_DASHBOARD_LOG, dashboard_data)

        # Update coordination tracking
        coordination_data = {
            "timestamp": timestamp,
            "department_coordination_scores": {
                dept_id: metrics.cross_department_score
                for dept_id, metrics in department_results.items()
            },
            "overall_coordination": org_overview.department_coordination_score,
            "synergy_level": org_overview.department_synergy_level
        }
        save_json(DEPARTMENT_COORDINATION_LOG, coordination_data)

    def get_department_status(self, dept_id: str = None) -> Dict[str, Any]:
        """Get current status for specific department or all departments."""
        if dept_id and dept_id in self.department_state:
            return self.department_state[dept_id]

        return self.department_state

    def get_executive_summary(self) -> Dict[str, Any]:
        """Get executive summary of organizational health."""
        if not EXECUTIVE_DASHBOARD_LOG.exists():
            return {"status": "no_data", "message": "No assessment data available"}

        return load_json(EXECUTIVE_DASHBOARD_LOG)

    def integration_with_apu74(self, escalations: List[Dict[str, Any]]) -> bool:
        """Integration hook for APU-74 alert processing."""
        if not escalations:
            return True

        # Filter escalations that require APU-74 integration
        apu74_escalations = [e for e in escalations if e.get("apu74_integration", False)]

        if not apu74_escalations:
            return True

        try:
            # Create APU-74 compatible alert format
            apu74_alerts = []
            for escalation in apu74_escalations:
                alert = {
                    "source": "APU77_DepartmentMonitor",
                    "alert_type": escalation["type"],
                    "severity": escalation["severity"],
                    "timestamp": datetime.now().isoformat(),
                    "condition": escalation["condition"],
                    "department": escalation.get("department", "organizational"),
                    "recommended_action": escalation["recommended_action"],
                    "requires_automated_response": escalation["severity"] == "critical"
                }
                apu74_alerts.append(alert)

            # Write to APU-74 integration file
            apu74_integration_file = APU77_LOG_DIR / "apu74_integration_alerts.json"
            integration_data = {
                "timestamp": datetime.now().isoformat(),
                "source": "APU77_DepartmentMonitor",
                "alert_count": len(apu74_alerts),
                "alerts": apu74_alerts
            }
            save_json(apu74_integration_file, integration_data)

            print(f"[APU74] Sent {len(apu74_alerts)} escalations to APU-74 for automated response")
            return True

        except Exception as e:
            print(f"[ERROR] APU-74 integration failed: {str(e)}")
            return False

def main():
    """Main execution function for APU-77 Department-Specific Engagement Monitor."""
    print("=" * 60)
    print("APU-77 DEPARTMENT-SPECIFIC ENGAGEMENT MONITOR")
    print("=" * 60)

    try:
        # Initialize monitor
        monitor = APU77DepartmentEngagementMonitor()

        # Run department assessment
        results = monitor.run_department_assessment()

        # Display results summary
        print("\n" + "=" * 60)
        print("EXECUTIVE SUMMARY")
        print("=" * 60)

        org_overview = results["organizational_overview"]
        print(f"Organizational Health Score: {org_overview['organizational_health_score']:.2f}")
        print(f"Department Coordination: {org_overview['department_coordination_score']:.2f}")
        print(f"Strategic Alignment: {org_overview['strategic_alignment_score']:.2f}")
        print(f"Scalability Readiness: {org_overview['scalability_readiness_score']:.2f}")
        print(f"Crisis Risk Assessment: {org_overview['crisis_risk_assessment']:.2f}")
        print(f"Organizational Momentum: {org_overview['organizational_momentum']}")

        # Display department summary
        print(f"\nDEPARTMENT HEALTH SUMMARY:")
        for dept_id, health_score in org_overview['department_health_summary'].items():
            dept_name = DEPARTMENT_CONFIG[dept_id]['department_name']
            status = "[GOOD]" if health_score >= 0.8 else "[WARN]" if health_score >= 0.6 else "[CRIT]"
            print(f"  {status} {dept_name}: {health_score:.2f}")

        # Display executive alerts
        if org_overview['executive_alerts']:
            print(f"\nEXECUTIVE ALERTS:")
            for alert in org_overview['executive_alerts']:
                print(f"  [ALERT] {alert}")

        # Display escalations
        if results["escalations"]:
            print(f"\nESCALATIONS ({len(results['escalations'])}):")
            for escalation in results["escalations"]:
                severity_icon = "[CRITICAL]" if escalation["severity"] == "critical" else "[WARNING]"
                print(f"  {severity_icon} {escalation['type']}: {escalation['condition']}")

        # Log successful execution
        log_run("APU77DepartmentMonitor", "completed", f"Organizational health: {org_overview['organizational_health_score']:.2f}")

        print(f"\n[SUCCESS] APU-77 Department monitoring completed successfully")
        print(f"[SUCCESS] Results saved to: {APU77_LOG_DIR}")

        return results

    except Exception as e:
        error_msg = f"APU-77 execution failed: {str(e)}"
        print(f"[ERROR] {error_msg}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")

        log_run("APU77DepartmentMonitor", "failed", error_msg)
        return None

if __name__ == "__main__":
    main()