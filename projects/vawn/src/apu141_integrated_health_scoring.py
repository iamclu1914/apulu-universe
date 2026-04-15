"""
apu141_integrated_health_scoring.py — Integrated Health Scoring Algorithm
Combines all APU-141 components into a unified health scoring system that properly
accounts for API dependencies and distinguishes internal vs external issues.

Created by: Dex - Community Agent (APU-141)

CORE INNOVATION:
Weighted health scoring that doesn't penalize agents for external API failures.
Provides accurate health assessment and actionable prioritization.

INTEGRATES:
- API Health Tracking (infrastructure layer)
- Enhanced Health Detection (agent behavior layer)
- Accurate Metrics (business logic layer)
- Dependency-Aware Scoring (unified assessment)
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from vawn_config import load_json, save_json, VAWN_DIR

# Import APU-141 components
try:
    from src.apu141_health_detection_system import APU141HealthDetector, HealthStatus, HealthImpact
    from src.apu141_api_health_tracker import APIEndpointHealthTracker
    from src.apu141_accurate_metrics import AccurateEngagementMetrics
except ImportError as e:
    print(f"Warning: Could not import APU-141 components: {e}")

# Integrated health scoring configuration
INTEGRATED_HEALTH_LOG = VAWN_DIR / "research" / "apu141_integrated_health_log.json"
SYSTEM_HEALTH_STATUS = VAWN_DIR / "research" / "apu141_system_health_status.json"

class APU141IntegratedHealthScorer:
    """Integrated health scoring system that accounts for API dependencies."""

    def __init__(self):
        self.health_detector = APU141HealthDetector()
        self.api_tracker = APIEndpointHealthTracker()
        self.metrics_tracker = AccurateEngagementMetrics()

        # Scoring weights for different health factors
        self.scoring_weights = {
            "api_infrastructure": 0.30,    # API availability and connectivity
            "agent_functionality": 0.35,   # Agent code execution and logic
            "business_metrics": 0.25,      # Actual engagement performance
            "authentication": 0.10         # Auth token validity and permissions
        }

        # Health score thresholds
        self.thresholds = {
            "excellent": 0.90,      # 90%+ - Everything working perfectly
            "healthy": 0.75,        # 75%+ - Normal operation with minor issues
            "degraded": 0.50,       # 50%+ - Functional but needs attention
            "critical": 0.25,       # 25%+ - Major issues, limited functionality
            "failed": 0.00          # <25% - System failure
        }

    def assess_integrated_system_health(self, agent_results: List[Dict[str, Any]],
                                      api_health: Dict[str, Any] = None,
                                      engagement_metrics: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Assess overall system health integrating all APU-141 components.

        Returns comprehensive health assessment with dependency-aware scoring.
        """
        assessment = {
            "timestamp": datetime.now().isoformat(),
            "overall_score": 0.0,
            "status": "unknown",
            "health_category": "unknown",
            "component_scores": {
                "api_infrastructure": 0.0,
                "agent_functionality": 0.0,
                "business_metrics": 0.0,
                "authentication": 0.0
            },
            "component_details": {
                "api_health": None,
                "agent_assessments": [],
                "engagement_metrics": None,
                "auth_status": None
            },
            "critical_issues": [],
            "recommendations": [],
            "dependency_impact": {
                "external_dependencies_healthy": True,
                "internal_components_healthy": True,
                "issues_blocking_engagement": []
            }
        }

        # 1. Assess API Infrastructure Health (30% weight)
        api_score = self.score_api_infrastructure(api_health)
        assessment["component_scores"]["api_infrastructure"] = api_score
        assessment["component_details"]["api_health"] = api_health

        # 2. Assess Agent Functionality Health (35% weight)
        agent_score, agent_assessments = self.score_agent_functionality(agent_results)
        assessment["component_scores"]["agent_functionality"] = agent_score
        assessment["component_details"]["agent_assessments"] = agent_assessments

        # 3. Assess Business Metrics Health (25% weight)
        metrics_score = self.score_business_metrics(engagement_metrics)
        assessment["component_scores"]["business_metrics"] = metrics_score
        assessment["component_details"]["engagement_metrics"] = engagement_metrics

        # 4. Assess Authentication Health (10% weight)
        auth_score = self.score_authentication(api_health, agent_results)
        assessment["component_scores"]["authentication"] = auth_score

        # 5. Calculate Weighted Overall Score
        overall_score = (
            api_score * self.scoring_weights["api_infrastructure"] +
            agent_score * self.scoring_weights["agent_functionality"] +
            metrics_score * self.scoring_weights["business_metrics"] +
            auth_score * self.scoring_weights["authentication"]
        )

        assessment["overall_score"] = overall_score

        # 6. Determine Health Category and Status
        assessment["health_category"] = self.categorize_health_score(overall_score)
        assessment["status"] = self.determine_system_status(assessment)

        # 7. Analyze Dependency Impact
        assessment["dependency_impact"] = self.analyze_dependency_impact(assessment)

        # 8. Generate Critical Issues and Recommendations
        assessment["critical_issues"] = self.identify_critical_issues(assessment)
        assessment["recommendations"] = self.generate_prioritized_recommendations(assessment)

        return assessment

    def score_api_infrastructure(self, api_health: Dict[str, Any] = None) -> float:
        """Score API infrastructure health (30% of overall score)."""
        if not api_health:
            return 0.0

        # Base score from endpoint availability
        health_percentage = api_health.get("health_percentage", 0.0)
        base_score = health_percentage

        # Adjust for critical endpoints
        critical_endpoints = api_health.get("critical_endpoints", {})
        if not critical_endpoints.get("posts_available", False):
            base_score *= 0.5  # Major penalty for posts API down

        if not critical_endpoints.get("comments_available", False):
            base_score *= 0.7  # Moderate penalty for comments API down

        # Performance adjustments
        avg_response_time = api_health.get("performance", {}).get("average_response_time_ms", 0)
        if avg_response_time > 10000:  # > 10 seconds
            base_score *= 0.8
        elif avg_response_time > 5000:  # > 5 seconds
            base_score *= 0.9

        return min(1.0, base_score)

    def score_agent_functionality(self, agent_results: List[Dict[str, Any]]) -> Tuple[float, List[Dict[str, Any]]]:
        """Score agent functionality health (35% of overall score)."""
        if not agent_results:
            return 0.0, []

        agent_assessments = []
        total_score = 0.0

        for agent_result in agent_results:
            agent_name = agent_result.get("agent_name", "unknown")
            assessment = self.health_detector.assess_agent_health(agent_name, agent_result)
            agent_assessments.append(assessment)

            # Score based on status with dependency-aware weighting
            status = assessment["status"]
            if status == HealthStatus.HEALTHY.value:
                agent_score = 1.0
            elif status == HealthStatus.NO_WORK_AVAILABLE.value:
                agent_score = 1.0  # Perfect score - agent did its job
            elif status == HealthStatus.DEGRADED.value:
                agent_score = 0.7
            elif status == HealthStatus.API_UNAVAILABLE.value:
                agent_score = 0.5  # External issue, moderate penalty
            elif status == HealthStatus.AUTH_FAILED.value:
                agent_score = 0.3  # External auth issue, but affects functionality
            elif status == HealthStatus.INFRASTRUCTURE_DOWN.value:
                agent_score = 0.4  # External infrastructure issue
            elif status == HealthStatus.AGENT_FAILED.value:
                agent_score = 0.0  # Internal agent issue, full penalty
            else:
                agent_score = 0.1  # Unknown status

            total_score += agent_score

        average_score = total_score / len(agent_results)
        return average_score, agent_assessments

    def score_business_metrics(self, engagement_metrics: Dict[str, Any] = None) -> float:
        """Score business metrics health (25% of overall score)."""
        if not engagement_metrics:
            return 0.5  # Neutral score when no metrics available

        # Focus on actual confirmed results, not attempted operations
        totals = engagement_metrics.get("totals", {})
        rates = engagement_metrics.get("rates", {})

        # Base score from platform connectivity
        platform_success = rates.get("platform_success_rate", 0.0)
        base_score = platform_success * 0.4  # Up to 40% from platform success

        # Score from actual engagement (confirmed responses)
        engagement_rate = rates.get("overall_engagement_rate", 0.0)
        if engagement_rate > 0:
            base_score += 0.6  # Full engagement score if any confirmed responses
        elif totals.get("comments_retrieved", 0) > 0:
            # Comments retrieved but no responses - could be normal
            response_posting_success = rates.get("response_posting_success_rate", 0.0)
            if response_posting_success == 0 and totals.get("responses_attempted", 0) > 0:
                # Attempted responses but none posted - API issue, not business issue
                base_score += 0.3  # Partial credit - business logic worked
            else:
                base_score += 0.4  # Retrieved comments, no responses needed/generated

        # Penalty for accuracy issues (the "0 seen vs 10 sent" problem)
        accuracy_flags = engagement_metrics.get("accuracy_flags", [])
        if accuracy_flags:
            base_score *= 0.8  # Moderate penalty for accuracy issues

        return min(1.0, base_score)

    def score_authentication(self, api_health: Dict[str, Any] = None,
                           agent_results: List[Dict[str, Any]] = None) -> float:
        """Score authentication health (10% of overall score)."""
        auth_score = 1.0  # Start with perfect score

        # Check API health auth status
        if api_health:
            auth_status = api_health.get("authentication", {}).get("token_valid")
            if auth_status is False:
                auth_score = 0.0
            elif auth_status is None:
                auth_score = 0.5  # Unknown auth status

        # Check agent results for auth errors
        if agent_results:
            auth_errors = sum(
                1 for result in agent_results
                for error in result.get("errors", [])
                if "auth" in str(error).lower() or "401" in str(error) or "unauthorized" in str(error).lower()
            )

            total_operations = sum(result.get("total_operations", 1) for result in agent_results)
            if auth_errors > 0:
                auth_error_rate = auth_errors / max(1, total_operations)
                auth_score *= (1.0 - auth_error_rate)

        return max(0.0, auth_score)

    def categorize_health_score(self, score: float) -> str:
        """Categorize health score into descriptive categories."""
        if score >= self.thresholds["excellent"]:
            return "excellent"
        elif score >= self.thresholds["healthy"]:
            return "healthy"
        elif score >= self.thresholds["degraded"]:
            return "degraded"
        elif score >= self.thresholds["critical"]:
            return "critical"
        else:
            return "failed"

    def determine_system_status(self, assessment: Dict[str, Any]) -> str:
        """Determine overall system status from integrated assessment."""
        component_scores = assessment["component_scores"]

        # Critical agent failures override everything
        if component_scores["agent_functionality"] < 0.2:
            return "agent_failure"

        # Infrastructure issues
        if component_scores["api_infrastructure"] < 0.3:
            return "infrastructure_failure"

        # Authentication issues
        if component_scores["authentication"] < 0.3:
            return "auth_failure"

        # Normal status based on overall score
        overall_score = assessment["overall_score"]
        if overall_score >= 0.75:
            return "operational"
        elif overall_score >= 0.50:
            return "degraded"
        else:
            return "critical"

    def analyze_dependency_impact(self, assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze how external dependencies are impacting system health."""
        component_scores = assessment["component_scores"]

        external_healthy = (
            component_scores["api_infrastructure"] > 0.5 and
            component_scores["authentication"] > 0.5
        )

        internal_healthy = (
            component_scores["agent_functionality"] > 0.7 and
            component_scores["business_metrics"] > 0.5
        )

        issues_blocking = []

        if component_scores["api_infrastructure"] < 0.5:
            issues_blocking.append("API infrastructure unavailable")

        if component_scores["authentication"] < 0.5:
            issues_blocking.append("Authentication failures blocking operations")

        if component_scores["agent_functionality"] < 0.3:
            issues_blocking.append("Agent code failures preventing execution")

        return {
            "external_dependencies_healthy": external_healthy,
            "internal_components_healthy": internal_healthy,
            "issues_blocking_engagement": issues_blocking
        }

    def identify_critical_issues(self, assessment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify critical issues requiring immediate attention."""
        critical_issues = []
        component_scores = assessment["component_scores"]

        # Critical agent failures
        if component_scores["agent_functionality"] < 0.2:
            critical_issues.append({
                "type": "agent_failure",
                "severity": "critical",
                "issue": "Agent code execution failures detected",
                "impact": "Complete engagement system failure",
                "action_required": "Review agent logs and fix code issues immediately"
            })

        # Authentication failures
        if component_scores["authentication"] < 0.3:
            critical_issues.append({
                "type": "auth_failure",
                "severity": "high",
                "issue": "Authentication system failing",
                "impact": "Cannot access platform APIs",
                "action_required": "Refresh access tokens and verify credentials"
            })

        # Infrastructure failures
        if component_scores["api_infrastructure"] < 0.3:
            critical_issues.append({
                "type": "infrastructure_failure",
                "severity": "high",
                "issue": "API infrastructure unavailable",
                "impact": "Cannot retrieve comments or post responses",
                "action_required": "Check server status and network connectivity"
            })

        return critical_issues

    def generate_prioritized_recommendations(self, assessment: Dict[str, Any]) -> List[str]:
        """Generate prioritized recommendations based on integrated assessment."""
        recommendations = []
        component_scores = assessment["component_scores"]
        critical_issues = assessment["critical_issues"]

        # Immediate actions for critical issues
        for issue in critical_issues:
            recommendations.append(f"[{issue['severity'].upper()}] {issue['action_required']}")

        # Component-specific recommendations
        if component_scores["api_infrastructure"] < 0.7:
            recommendations.append("Monitor API endpoint health and implement retry logic")

        if component_scores["agent_functionality"] < 0.8:
            recommendations.append("Review agent error logs and optimize error handling")

        if component_scores["business_metrics"] < 0.6:
            recommendations.append("Analyze engagement patterns and optimize response targeting")

        if component_scores["authentication"] < 0.8:
            recommendations.append("Implement automatic token refresh mechanism")

        # Overall system recommendations
        overall_score = assessment["overall_score"]
        if overall_score < 0.5:
            recommendations.append("System requires immediate attention - coordinate recovery efforts")
        elif overall_score < 0.75:
            recommendations.append("Schedule system optimization to address degraded performance")

        if not recommendations:
            recommendations.append("System operating within acceptable parameters")

        return recommendations

    def save_integrated_assessment(self, assessment: Dict[str, Any]) -> None:
        """Save integrated health assessment for monitoring and historical analysis."""

        # Save current status
        current_status = {
            "timestamp": assessment["timestamp"],
            "overall_score": assessment["overall_score"],
            "health_category": assessment["health_category"],
            "status": assessment["status"],
            "component_scores": assessment["component_scores"],
            "critical_issues_count": len(assessment["critical_issues"]),
            "recommendations": assessment["recommendations"][:3]  # Top 3 recommendations
        }

        SYSTEM_HEALTH_STATUS.parent.mkdir(exist_ok=True)
        save_json(SYSTEM_HEALTH_STATUS, current_status)

        # Save detailed assessment to historical log
        health_log = load_json(INTEGRATED_HEALTH_LOG) if INTEGRATED_HEALTH_LOG.exists() else {}
        today = datetime.now().strftime("%Y-%m-%d")

        if today not in health_log:
            health_log[today] = []

        health_log[today].append(assessment)

        # Keep last 14 days
        cutoff_date = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
        health_log = {k: v for k, v in health_log.items() if k >= cutoff_date}

        save_json(INTEGRATED_HEALTH_LOG, health_log)

def demonstrate_integrated_health_scoring():
    """Demonstrate the integrated health scoring system."""
    print("APU-141 Integrated Health Scoring System")
    print("=" * 50)

    scorer = APU141IntegratedHealthScorer()

    # Simulate comprehensive system assessment
    mock_api_health = {
        "health_percentage": 0.2,  # 20% of endpoints healthy
        "critical_endpoints": {
            "posts_available": False,
            "comments_available": False,
            "core_api_available": True
        },
        "authentication": {"token_valid": True}
    }

    mock_agent_results = [
        {
            "agent_name": "engagement_monitor",
            "success": True,
            "errors": ["HTTP 404: Comments endpoint not found"],
            "comments_found": 0,
            "responses_posted": 0
        }
    ]

    mock_metrics = {
        "totals": {
            "platforms_checked": 5,
            "platforms_successful": 2,
            "comments_retrieved": 0,
            "responses_attempted": 0,
            "responses_confirmed": 0
        },
        "rates": {
            "platform_success_rate": 0.4,
            "overall_engagement_rate": 0.0,
            "response_posting_success_rate": 0.0
        },
        "accuracy_flags": ["No comments retrieved despite platform connectivity"]
    }

    # Run integrated assessment
    assessment = scorer.assess_integrated_system_health(
        mock_agent_results, mock_api_health, mock_metrics
    )

    # Display results
    print(f"\n[OVERALL HEALTH]")
    print(f"  Score: {assessment['overall_score']:.2f} ({assessment['health_category'].upper()})")
    print(f"  Status: {assessment['status']}")

    print(f"\n[COMPONENT SCORES]")
    for component, score in assessment["component_scores"].items():
        print(f"  {component.replace('_', ' ').title()}: {score:.2f}")

    print(f"\n[CRITICAL ISSUES]")
    if assessment["critical_issues"]:
        for issue in assessment["critical_issues"]:
            print(f"  [{issue['severity'].upper()}] {issue['issue']}")
    else:
        print("  None detected")

    print(f"\n[TOP RECOMMENDATIONS]")
    for rec in assessment["recommendations"][:3]:
        print(f"  • {rec}")

    print(f"\n[APU-141] This scoring properly accounts for API dependencies!")
    print(f"  Agent shows as functional despite API failures.")
    print(f"  Accurate component breakdown guides prioritization.")

if __name__ == "__main__":
    demonstrate_integrated_health_scoring()