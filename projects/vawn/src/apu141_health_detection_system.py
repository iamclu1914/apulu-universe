"""
apu141_health_detection_system.py — Enhanced Health Detection System
Addresses critical issues identified in APU-120 and APU-141 diagnostics.

Created by: Dex - Community Agent (APU-141)

CORE PROBLEM SOLVED:
- Distinguishes agent failures vs API failures vs no-work scenarios
- Separates API health from engagement metrics
- Provides accurate health scoring that accounts for external dependencies
- Enables proper alerting for different types of issues

DESIGN PRINCIPLES:
1. Multi-layered health assessment (Agent/API/Infrastructure/Auth)
2. Context-aware health scoring (don't penalize for external issues)
3. Detailed status categorization for accurate alerting
4. Real-time dependency tracking
"""

import json
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from vawn_config import load_json, save_json, VAWN_DIR

# APU-141 health system configuration
HEALTH_LOG = VAWN_DIR / "research" / "apu141_health_detection_log.json"
HEALTH_STATUS = VAWN_DIR / "research" / "apu141_current_health_status.json"

class HealthStatus(Enum):
    """Health status categories for accurate classification."""
    HEALTHY = "healthy"                    # Everything working normally
    DEGRADED = "degraded"                  # Working but with issues
    API_UNAVAILABLE = "api_unavailable"    # External API issues
    AUTH_FAILED = "auth_failed"            # Authentication problems
    AGENT_FAILED = "agent_failed"          # Agent code issues
    NO_WORK_AVAILABLE = "no_work_available"  # Successfully ran but no work to do
    INFRASTRUCTURE_DOWN = "infrastructure_down"  # Server/network issues
    UNKNOWN = "unknown"                    # Status cannot be determined

class HealthImpact(Enum):
    """Impact levels for different health issues."""
    NONE = 0        # No impact (e.g., no work available)
    LOW = 1         # Minor issues, functionality intact
    MEDIUM = 2      # Some degradation, needs attention
    HIGH = 3        # Major issues, significant impact
    CRITICAL = 4    # Complete failure, immediate action required

class APU141HealthDetector:
    """Enhanced health detection system for engagement monitoring."""

    def __init__(self):
        self.health_history = []
        self.api_endpoints = [
            "/health", "/status", "/posts", "/comments", "/posts/comments"
        ]

    def assess_agent_health(self, agent_name: str, agent_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess agent health with enhanced categorization.

        Returns detailed health assessment distinguishing between different failure types.
        """
        assessment = {
            "agent": agent_name,
            "timestamp": datetime.now().isoformat(),
            "status": HealthStatus.UNKNOWN.value,
            "health_score": 0.0,
            "impact_level": HealthImpact.CRITICAL.value,
            "issues": [],
            "recommendations": [],
            "dependencies": {
                "api_health": None,
                "auth_status": None,
                "network_status": None
            },
            "metrics": {
                "execution_time": agent_result.get("execution_time", 0),
                "errors_count": len(agent_result.get("errors", [])),
                "success_operations": agent_result.get("successful_operations", 0),
                "total_operations": agent_result.get("total_operations", 0)
            }
        }

        # Step 1: Check for agent execution issues (code-level failures)
        if "exception" in agent_result or "critical_error" in agent_result:
            assessment["status"] = HealthStatus.AGENT_FAILED.value
            assessment["health_score"] = 0.0
            assessment["impact_level"] = HealthImpact.CRITICAL.value
            assessment["issues"].append("Agent code execution failed")
            assessment["recommendations"].append("Review agent code for bugs or logic errors")
            return assessment

        # Step 2: Check API and authentication dependencies
        auth_status = self.check_authentication_health(agent_result)
        api_status = self.check_api_endpoints_health(agent_result)

        assessment["dependencies"]["auth_status"] = auth_status
        assessment["dependencies"]["api_health"] = api_status

        # Step 3: Categorize based on dependency health
        if auth_status and auth_status["status"] == "failed":
            assessment["status"] = HealthStatus.AUTH_FAILED.value
            assessment["health_score"] = 0.2  # Low but not zero - agent code is fine
            assessment["impact_level"] = HealthImpact.HIGH.value
            assessment["issues"].append("Authentication failed - token expired or invalid")
            assessment["recommendations"].append("Refresh access token or check credentials")

        elif api_status and api_status["healthy_endpoints"] == 0:
            assessment["status"] = HealthStatus.INFRASTRUCTURE_DOWN.value
            assessment["health_score"] = 0.3  # Agent code fine, external issue
            assessment["impact_level"] = HealthImpact.HIGH.value
            assessment["issues"].append("All API endpoints unavailable")
            assessment["recommendations"].append("Check server status and network connectivity")

        elif api_status and api_status["healthy_endpoints"] < len(self.api_endpoints) * 0.5:
            assessment["status"] = HealthStatus.API_UNAVAILABLE.value
            assessment["health_score"] = 0.5
            assessment["impact_level"] = HealthImpact.MEDIUM.value
            assessment["issues"].append("Multiple API endpoints unavailable")
            assessment["recommendations"].append("Investigate API service health")

        # Step 4: Check for successful execution with no work scenario
        elif (agent_result.get("success", False) and
              agent_result.get("comments_found", 0) == 0 and
              len(agent_result.get("errors", [])) == 0):
            assessment["status"] = HealthStatus.NO_WORK_AVAILABLE.value
            assessment["health_score"] = 1.0  # Perfect - agent did its job correctly
            assessment["impact_level"] = HealthImpact.NONE.value
            assessment["issues"].append("No comments or engagement found to process")
            assessment["recommendations"].append("Normal operation - no action required")

        # Step 5: Check for successful execution with work
        elif (agent_result.get("success", False) and
              agent_result.get("responses_posted", 0) > 0):
            assessment["status"] = HealthStatus.HEALTHY.value
            assessment["health_score"] = 1.0
            assessment["impact_level"] = HealthImpact.NONE.value
            assessment["recommendations"].append("System operating normally")

        # Step 6: Check for degraded performance
        elif agent_result.get("success", False) and len(agent_result.get("errors", [])) > 0:
            assessment["status"] = HealthStatus.DEGRADED.value
            error_ratio = len(agent_result.get("errors", [])) / max(1, agent_result.get("total_operations", 1))
            assessment["health_score"] = max(0.4, 1.0 - error_ratio)
            assessment["impact_level"] = HealthImpact.LOW.value if error_ratio < 0.3 else HealthImpact.MEDIUM.value
            assessment["issues"].append(f"Some errors encountered: {len(agent_result.get('errors', []))} errors")
            assessment["recommendations"].append("Review error logs and address recurring issues")

        else:
            # Unknown state - couldn't categorize
            assessment["status"] = HealthStatus.UNKNOWN.value
            assessment["health_score"] = 0.1
            assessment["impact_level"] = HealthImpact.MEDIUM.value
            assessment["issues"].append("Cannot determine agent health status")
            assessment["recommendations"].append("Review agent logs and execution results")

        return assessment

    def check_authentication_health(self, agent_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check authentication status from agent results."""
        errors = agent_result.get("errors", [])

        # Look for auth-related errors in the results
        auth_errors = [
            error for error in errors
            if any(keyword in str(error).lower() for keyword in
                  ["401", "unauthorized", "token", "auth", "forbidden"])
        ]

        if auth_errors:
            return {
                "status": "failed",
                "errors": auth_errors,
                "last_check": datetime.now().isoformat()
            }
        elif agent_result.get("success", False):
            return {
                "status": "healthy",
                "errors": [],
                "last_check": datetime.now().isoformat()
            }

        return None

    def check_api_endpoints_health(self, agent_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check API endpoint health from agent results."""
        errors = agent_result.get("errors", [])

        # Count API-related errors
        api_errors = [
            error for error in errors
            if any(keyword in str(error).lower() for keyword in
                  ["404", "500", "503", "connection", "timeout", "api"])
        ]

        # Estimate healthy endpoints (rough calculation)
        total_endpoints = len(self.api_endpoints)
        error_endpoints = min(len(api_errors), total_endpoints)
        healthy_endpoints = total_endpoints - error_endpoints

        return {
            "healthy_endpoints": healthy_endpoints,
            "total_endpoints": total_endpoints,
            "health_percentage": (healthy_endpoints / total_endpoints) if total_endpoints > 0 else 0,
            "api_errors": api_errors,
            "last_check": datetime.now().isoformat()
        }

    def calculate_system_health_score(self, agent_assessments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate overall system health score that accounts for different failure types.

        This is the key innovation - proper weighting that doesn't penalize external issues.
        """
        if not agent_assessments:
            return {
                "overall_score": 0.0,
                "status": HealthStatus.UNKNOWN.value,
                "impact_level": HealthImpact.CRITICAL.value
            }

        # Separate assessments by failure type
        healthy_agents = []
        degraded_agents = []
        external_issue_agents = []  # API/auth/infrastructure issues
        agent_failure_agents = []   # Actual agent code issues
        no_work_agents = []

        for assessment in agent_assessments:
            status = assessment["status"]
            if status == HealthStatus.HEALTHY.value:
                healthy_agents.append(assessment)
            elif status == HealthStatus.DEGRADED.value:
                degraded_agents.append(assessment)
            elif status in [HealthStatus.API_UNAVAILABLE.value,
                           HealthStatus.AUTH_FAILED.value,
                           HealthStatus.INFRASTRUCTURE_DOWN.value]:
                external_issue_agents.append(assessment)
            elif status == HealthStatus.AGENT_FAILED.value:
                agent_failure_agents.append(assessment)
            elif status == HealthStatus.NO_WORK_AVAILABLE.value:
                no_work_agents.append(assessment)

        total_agents = len(agent_assessments)

        # Calculate weighted health score
        # Key insight: Don't heavily penalize external issues that are not our fault
        health_score = 0.0

        # Healthy and no-work agents contribute full score
        health_score += (len(healthy_agents) + len(no_work_agents)) * 1.0

        # Degraded agents contribute partial score
        health_score += len(degraded_agents) * 0.7

        # External issues get partial score (not our fault, but affects functionality)
        health_score += len(external_issue_agents) * 0.4

        # Agent failures get no score (our fault)
        health_score += len(agent_failure_agents) * 0.0

        # Normalize to 0-1 scale
        overall_score = health_score / total_agents if total_agents > 0 else 0.0

        # Determine overall status
        if overall_score >= 0.9:
            overall_status = HealthStatus.HEALTHY.value
            impact = HealthImpact.NONE.value
        elif overall_score >= 0.7:
            overall_status = HealthStatus.DEGRADED.value
            impact = HealthImpact.LOW.value
        elif len(agent_failure_agents) > 0:
            overall_status = HealthStatus.AGENT_FAILED.value
            impact = HealthImpact.CRITICAL.value
        elif len(external_issue_agents) > len(healthy_agents):
            overall_status = HealthStatus.API_UNAVAILABLE.value
            impact = HealthImpact.HIGH.value
        else:
            overall_status = HealthStatus.DEGRADED.value
            impact = HealthImpact.MEDIUM.value

        return {
            "overall_score": overall_score,
            "status": overall_status,
            "impact_level": impact,
            "breakdown": {
                "healthy": len(healthy_agents),
                "degraded": len(degraded_agents),
                "external_issues": len(external_issue_agents),
                "agent_failures": len(agent_failure_agents),
                "no_work": len(no_work_agents),
                "total": total_agents
            }
        }

    def generate_actionable_recommendations(self, system_health: Dict[str, Any],
                                          agent_assessments: List[Dict[str, Any]]) -> List[str]:
        """Generate prioritized, actionable recommendations based on health assessment."""
        recommendations = []

        # Prioritize by impact level
        critical_issues = [a for a in agent_assessments if a["impact_level"] == HealthImpact.CRITICAL.value]
        high_issues = [a for a in agent_assessments if a["impact_level"] == HealthImpact.HIGH.value]

        if critical_issues:
            recommendations.append("[CRITICAL] Agent code failures detected - review logs immediately")

        if high_issues:
            auth_issues = [a for a in high_issues if a["status"] == HealthStatus.AUTH_FAILED.value]
            if auth_issues:
                recommendations.append("[HIGH] Refresh authentication tokens - multiple auth failures")

            api_issues = [a for a in high_issues if a["status"] == HealthStatus.INFRASTRUCTURE_DOWN.value]
            if api_issues:
                recommendations.append("[HIGH] Check API server status - endpoints unavailable")

        # System-level recommendations
        if system_health["overall_score"] < 0.5:
            recommendations.append("Overall system health is low - coordinate recovery efforts")

        if not recommendations:
            recommendations.append("System operating within acceptable parameters")

        return recommendations

    def save_health_assessment(self, system_health: Dict[str, Any],
                              agent_assessments: List[Dict[str, Any]]) -> None:
        """Save health assessment results for monitoring and historical analysis."""

        # Current status for real-time monitoring
        current_status = {
            "timestamp": datetime.now().isoformat(),
            "system_health": system_health,
            "agent_count": len(agent_assessments),
            "recommendations": self.generate_actionable_recommendations(system_health, agent_assessments)
        }

        HEALTH_STATUS.parent.mkdir(exist_ok=True)
        save_json(HEALTH_STATUS, current_status)

        # Historical log for trend analysis
        health_log = load_json(HEALTH_LOG) if HEALTH_LOG.exists() else {}
        today = datetime.now().strftime("%Y-%m-%d")

        if today not in health_log:
            health_log[today] = []

        health_log[today].append({
            "timestamp": datetime.now().isoformat(),
            "system_health": system_health,
            "agent_assessments": agent_assessments,
            "recommendations": current_status["recommendations"]
        })

        # Keep last 30 days
        cutoff_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        health_log = {k: v for k, v in health_log.items() if k >= cutoff_date}

        save_json(HEALTH_LOG, health_log)

# Example usage and testing functions
def test_apu141_health_detection():
    """Test the enhanced health detection with various scenarios."""
    detector = APU141HealthDetector()

    # Test scenarios based on real issues from APU-120/127
    test_scenarios = [
        {
            "name": "auth_failure_scenario",
            "agent_result": {
                "success": False,
                "errors": ["HTTP 401: Unauthorized", "Token expired"],
                "comments_found": 0,
                "responses_posted": 0
            }
        },
        {
            "name": "no_work_scenario",
            "agent_result": {
                "success": True,
                "errors": [],
                "comments_found": 0,
                "responses_posted": 0,
                "platforms_checked": 5
            }
        },
        {
            "name": "healthy_scenario",
            "agent_result": {
                "success": True,
                "errors": [],
                "comments_found": 3,
                "responses_posted": 2,
                "platforms_checked": 5
            }
        }
    ]

    assessments = []
    for scenario in test_scenarios:
        assessment = detector.assess_agent_health(scenario["name"], scenario["agent_result"])
        assessments.append(assessment)
        print(f"[TEST] {scenario['name']}: {assessment['status']} (score: {assessment['health_score']})")

    system_health = detector.calculate_system_health_score(assessments)
    print(f"[SYSTEM] Overall health: {system_health['status']} (score: {system_health['overall_score']:.2f})")

    return assessments, system_health

if __name__ == "__main__":
    print("APU-141 Enhanced Health Detection System")
    print("=" * 50)
    test_apu141_health_detection()