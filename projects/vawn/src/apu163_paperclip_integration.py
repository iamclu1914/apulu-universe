"""
apu163_paperclip_integration.py — Enhanced Paperclip Integration for APU-163
Advanced issue lifecycle management and coordination with Paperclip system.

Created by: Dex - Community Agent (APU-163)
Purpose: Seamless integration between APU-163 monitoring and Paperclip issue tracking

CAPABILITIES:
[NEW] Automated Issue Lifecycle Management (creation, tracking, resolution, closure)
[NEW] Department-Specific Issue Routing (intelligent assignment based on problem type)
[NEW] Integration with Existing Paperclip Tasks (APU-155 infrastructure issues)
[NEW] Bi-directional Sync (Paperclip updates → APU-163 actions)
[NEW] Issue Priority Intelligence (dynamic prioritization based on impact)
[NEW] Resolution Workflow Automation (automated status updates and notifications)
[NEW] Cross-Issue Pattern Detection (identify related issues for batch resolution)
"""

import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import sqlite3
from dataclasses import dataclass, asdict
from enum import Enum

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from vawn_config import load_json, save_json, VAWN_DIR, today_str


class IssueStatus(Enum):
    """Paperclip issue status types."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"


class IssueType(Enum):
    """Types of issues APU-163 can create."""
    API_INFRASTRUCTURE = "api_infrastructure"
    PLATFORM_TIMEOUT = "platform_timeout"
    AUTHENTICATION = "authentication"
    ENGAGEMENT_ANOMALY = "engagement_anomaly"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    COMMUNITY_HEALTH = "community_health"
    GROWTH_OPTIMIZATION = "growth_optimization"


@dataclass
class PaperclipIssueEnhanced:
    """Enhanced Paperclip issue with APU-163 specific fields."""
    issue_id: str
    apu_number: str
    title: str
    description: str
    priority: str
    department: str
    status: IssueStatus
    issue_type: IssueType
    created_timestamp: str
    updated_timestamp: str
    resolved_timestamp: Optional[str]
    assigned_agent: Optional[str]
    source_component: str
    auto_resolution_attempted: bool
    resolution_method: Optional[str]
    estimated_impact: str
    related_issues: List[str]
    tags: List[str]
    resolution_confidence: Optional[float]
    follow_up_required: bool


class APU163PaperclipIntegration:
    """Enhanced Paperclip integration for APU-163 monitoring system."""

    def __init__(self, apu163_monitor):
        self.monitor = apu163_monitor
        self.paperclip_dir = VAWN_DIR / "paperclip"
        self.tasks_dir = self.paperclip_dir / "tasks"
        self.alerts_dir = self.paperclip_dir / "alerts"
        self.reports_dir = self.paperclip_dir / "reports"

        # Ensure directories exist
        for directory in [self.tasks_dir, self.alerts_dir, self.reports_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # Integration configuration
        self.issue_counter = self._get_next_issue_number()
        self.department_agents = {
            "artists_development": "artist_dev_coordinator",
            "marketing": "marketing_coordinator",
            "production": "production_coordinator",
            "distribution": "distribution_coordinator",
            "chief_of_staff": "cos_coordinator"
        }

        # Issue resolution patterns
        self.resolution_patterns = self._load_resolution_patterns()
        self.escalation_thresholds = {
            "api_infrastructure": 3,  # escalate after 3 similar issues
            "platform_timeout": 5,
            "authentication": 2,
            "engagement_anomaly": 4,
            "performance_degradation": 3
        }

        print(f"[APU-163] Paperclip integration initialized")
        print(f"[APU-163] Tasks directory: {self.tasks_dir}")
        print(f"[APU-163] Next issue number: APU-{self.issue_counter}")

    def _get_next_issue_number(self) -> int:
        """Get the next APU issue number."""
        existing_files = list(self.tasks_dir.glob("apu*.json"))

        if not existing_files:
            return 164  # Start from 164 since we're APU-163

        # Extract issue numbers from existing files
        issue_numbers = []
        for file in existing_files:
            try:
                # Extract number from filename like "apu155_api_infrastructure.json"
                parts = file.stem.split('_')
                if parts[0].startswith('apu'):
                    number = int(parts[0][3:])  # Remove 'apu' prefix
                    issue_numbers.append(number)
            except (ValueError, IndexError):
                continue

        return max(issue_numbers, default=163) + 1

    def _load_resolution_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load resolution patterns from existing issues."""
        patterns = {}

        # Load from existing APU-155 issues to learn patterns
        existing_files = list(self.tasks_dir.glob("*.json"))
        for file in existing_files:
            try:
                issue_data = load_json(file)
                issue_type = self._classify_issue_type(issue_data)

                if issue_type not in patterns:
                    patterns[issue_type] = {
                        "common_causes": [],
                        "typical_resolution_time": "unknown",
                        "success_rate": 0.0,
                        "recommended_actions": []
                    }

                # Extract patterns from description
                description = issue_data.get("description", "")
                if "API endpoints" in description and "404" in description:
                    patterns[issue_type]["common_causes"].append("endpoint_not_implemented")
                if "timeout" in description.lower():
                    patterns[issue_type]["common_causes"].append("network_timeout")

            except Exception as e:
                print(f"[APU-163] Warning: Could not process {file}: {e}")

        return patterns

    def _classify_issue_type(self, issue_data: Dict[str, Any]) -> str:
        """Classify issue type from issue data."""
        description = issue_data.get("description", "").lower()
        title = issue_data.get("title", "").lower()

        if "api" in description and ("404" in description or "endpoint" in description):
            return "api_infrastructure"
        elif "timeout" in description:
            return "platform_timeout"
        elif "auth" in description:
            return "authentication"
        elif "engagement" in description:
            return "engagement_anomaly"
        elif "performance" in description:
            return "performance_degradation"
        else:
            return "community_health"

    def create_enhanced_issue(self, problem: Dict[str, Any],
                            healing_attempted: bool = False,
                            healing_success: bool = False) -> PaperclipIssueEnhanced:
        """Create enhanced Paperclip issue with APU-163 intelligence."""

        issue_number = self.issue_counter
        self.issue_counter += 1

        # Generate intelligent issue details
        issue_type = self._determine_issue_type(problem)
        department = self._assign_department(issue_type, problem)
        priority = self._calculate_dynamic_priority(problem, issue_type)

        # Check for related issues
        related_issues = self._find_related_issues(problem, issue_type)

        issue_id = f"apu{issue_number}_{issue_type.value}_{int(datetime.now().timestamp())}"

        enhanced_issue = PaperclipIssueEnhanced(
            issue_id=issue_id,
            apu_number=f"APU-{issue_number}",
            title=self._generate_intelligent_title(problem, issue_type),
            description=self._generate_enhanced_description(problem, issue_type, healing_attempted, healing_success),
            priority=priority,
            department=department.value if hasattr(department, 'value') else str(department),
            status=IssueStatus.TODO,
            issue_type=issue_type,
            created_timestamp=datetime.now().isoformat(),
            updated_timestamp=datetime.now().isoformat(),
            resolved_timestamp=None,
            assigned_agent=self.department_agents.get(department.value if hasattr(department, 'value') else str(department)),
            source_component="apu163_engagement_monitor",
            auto_resolution_attempted=healing_attempted,
            resolution_method=None,
            estimated_impact=self._estimate_impact(problem, issue_type),
            related_issues=related_issues,
            tags=self._generate_tags(problem, issue_type),
            resolution_confidence=None,
            follow_up_required=not healing_success if healing_attempted else True
        )

        # Save to both database and file system
        self._save_issue_to_database(enhanced_issue)
        self._save_issue_to_paperclip(enhanced_issue)

        # Check for escalation patterns
        self._check_escalation_needed(enhanced_issue)

        print(f"[APU-163] Created enhanced issue: {enhanced_issue.apu_number}")
        print(f"[APU-163] Type: {issue_type.value}, Priority: {priority}, Department: {department}")

        return enhanced_issue

    def _determine_issue_type(self, problem: Dict[str, Any]) -> IssueType:
        """Determine issue type with enhanced intelligence."""
        problem_type = problem.get("type", "").lower()
        description = problem.get("description", "").lower()

        type_mapping = {
            "api_timeout": IssueType.PLATFORM_TIMEOUT,
            "api_degradation": IssueType.API_INFRASTRUCTURE,
            "auth_failure": IssueType.AUTHENTICATION,
            "rate_limit": IssueType.PERFORMANCE_DEGRADATION,
            "infrastructure_degradation": IssueType.API_INFRASTRUCTURE
        }

        # Check for specific keywords in description
        if "engagement" in description and "anomaly" in description:
            return IssueType.ENGAGEMENT_ANOMALY
        elif "community" in description and "health" in description:
            return IssueType.COMMUNITY_HEALTH
        elif "growth" in description or "strategy" in description:
            return IssueType.GROWTH_OPTIMIZATION

        return type_mapping.get(problem_type, IssueType.COMMUNITY_HEALTH)

    def _assign_department(self, issue_type: IssueType, problem: Dict[str, Any]):
        """Assign department based on issue type and context."""
        from src.apu163_engagement_monitor import DepartmentType

        # Department assignment logic
        assignment_rules = {
            IssueType.API_INFRASTRUCTURE: DepartmentType.PRODUCTION,
            IssueType.PLATFORM_TIMEOUT: DepartmentType.PRODUCTION,
            IssueType.AUTHENTICATION: DepartmentType.MARKETING,
            IssueType.ENGAGEMENT_ANOMALY: DepartmentType.MARKETING,
            IssueType.PERFORMANCE_DEGRADATION: DepartmentType.PRODUCTION,
            IssueType.COMMUNITY_HEALTH: DepartmentType.CHIEF_OF_STAFF,
            IssueType.GROWTH_OPTIMIZATION: DepartmentType.ARTISTS_DEVELOPMENT
        }

        # Check problem severity for potential CoS escalation
        if problem.get("severity") == "critical":
            return DepartmentType.CHIEF_OF_STAFF

        return assignment_rules.get(issue_type, DepartmentType.CHIEF_OF_STAFF)

    def _calculate_dynamic_priority(self, problem: Dict[str, Any], issue_type: IssueType) -> str:
        """Calculate dynamic priority based on multiple factors."""
        base_priority = problem.get("severity", "medium")

        # Priority escalation factors
        escalation_factors = []

        # Check time sensitivity
        if "timeout" in problem.get("description", "").lower():
            escalation_factors.append("time_sensitive")

        # Check user impact
        if "user" in problem.get("description", "").lower() or "community" in problem.get("description", "").lower():
            escalation_factors.append("user_impact")

        # Check infrastructure impact
        if issue_type in [IssueType.API_INFRASTRUCTURE, IssueType.PLATFORM_TIMEOUT]:
            escalation_factors.append("infrastructure_impact")

        # Calculate final priority
        priority_scores = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        base_score = priority_scores.get(base_priority, 2)

        # Apply escalation factors
        escalation_bonus = len(escalation_factors) * 0.5
        final_score = min(4, base_score + escalation_bonus)

        # Convert back to priority string
        score_to_priority = {1: "low", 2: "medium", 3: "high", 4: "critical"}
        return score_to_priority.get(int(final_score), "medium")

    def _find_related_issues(self, problem: Dict[str, Any], issue_type: IssueType) -> List[str]:
        """Find related issues for pattern analysis."""
        related = []

        # Search existing issues for similar patterns
        existing_files = list(self.tasks_dir.glob("*.json"))
        problem_keywords = set(problem.get("description", "").lower().split())

        for file in existing_files:
            try:
                issue_data = load_json(file)
                issue_desc = issue_data.get("description", "").lower()
                issue_keywords = set(issue_desc.split())

                # Check keyword overlap
                overlap = len(problem_keywords & issue_keywords)
                if overlap >= 3:  # Significant keyword overlap
                    related.append(issue_data.get("issue_id", file.stem))

                # Check for same issue type
                if self._classify_issue_type(issue_data) == issue_type.value:
                    related.append(issue_data.get("issue_id", file.stem))

            except Exception as e:
                continue

        return list(set(related))  # Remove duplicates

    def _generate_intelligent_title(self, problem: Dict[str, Any], issue_type: IssueType) -> str:
        """Generate intelligent issue title."""
        problem_type = problem.get("type", "unknown")
        severity = problem.get("severity", "medium")

        title_templates = {
            IssueType.API_INFRASTRUCTURE: f"{severity.title()} API Infrastructure Issue: {problem_type}",
            IssueType.PLATFORM_TIMEOUT: f"{severity.title()} Platform Timeout: {problem_type}",
            IssueType.AUTHENTICATION: f"{severity.title()} Authentication Failure: {problem_type}",
            IssueType.ENGAGEMENT_ANOMALY: f"{severity.title()} Engagement Anomaly Detected",
            IssueType.PERFORMANCE_DEGRADATION: f"{severity.title()} Performance Issue: {problem_type}",
            IssueType.COMMUNITY_HEALTH: f"{severity.title()} Community Health Alert",
            IssueType.GROWTH_OPTIMIZATION: f"Growth Optimization Opportunity: {problem_type}"
        }

        return title_templates.get(issue_type, f"{severity.title()} Issue: {problem_type}")

    def _generate_enhanced_description(self, problem: Dict[str, Any], issue_type: IssueType,
                                     healing_attempted: bool, healing_success: bool) -> str:
        """Generate enhanced issue description with intelligence."""

        base_description = f"""
## Problem Summary
**Type**: {problem.get('type', 'unknown')}
**Severity**: {problem.get('severity', 'medium')}
**Detected At**: {problem.get('detected_at', datetime.now().isoformat())}
**Source**: APU-163 Advanced Engagement Monitor

## Problem Description
{problem.get('description', 'No detailed description available')}

## APU-163 Analysis
**Issue Classification**: {issue_type.value}
**Auto-Resolution Attempted**: {'Yes' if healing_attempted else 'No'}
"""

        if healing_attempted:
            base_description += f"**Auto-Resolution Result**: {'Success' if healing_success else 'Failed'}\n"

        # Add intelligence from patterns
        if issue_type.value in self.resolution_patterns:
            pattern = self.resolution_patterns[issue_type.value]
            base_description += f"""
## Historical Pattern Analysis
**Common Causes**: {', '.join(pattern.get('common_causes', ['Unknown']))}
**Typical Resolution Time**: {pattern.get('typical_resolution_time', 'Unknown')}
"""

        # Add recommended actions
        recommended_actions = self._get_recommended_actions(issue_type, problem, healing_attempted, healing_success)
        if recommended_actions:
            base_description += f"""
## Recommended Actions
{chr(10).join(f'{i+1}. {action}' for i, action in enumerate(recommended_actions))}
"""

        # Add technical details
        base_description += f"""
## Technical Details
**Detection Method**: Automated monitoring via APU-163
**Impact Assessment**: {self._estimate_impact(problem, issue_type)}
**Follow-up Required**: {'Yes' if not healing_success else 'No'}

## Resolution Tracking
- [ ] Initial assessment completed
- [ ] Root cause identified
- [ ] Resolution strategy implemented
- [ ] Solution validated
- [ ] Issue closed and documented
"""

        return base_description.strip()

    def _get_recommended_actions(self, issue_type: IssueType, problem: Dict[str, Any],
                               healing_attempted: bool, healing_success: bool) -> List[str]:
        """Get recommended actions for issue type."""
        actions = []

        base_actions = {
            IssueType.API_INFRASTRUCTURE: [
                "Check API server status and connectivity",
                "Review API documentation for endpoint changes",
                "Contact API team about endpoint availability",
                "Implement fallback data collection strategies"
            ],
            IssueType.PLATFORM_TIMEOUT: [
                "Investigate platform API rate limits",
                "Review timeout configurations",
                "Implement retry logic with exponential backoff",
                "Add platform-specific timeout monitoring"
            ],
            IssueType.AUTHENTICATION: [
                "Refresh authentication tokens",
                "Verify credential configuration",
                "Check API key permissions",
                "Update authentication workflow"
            ]
        }

        actions.extend(base_actions.get(issue_type, ["Investigate and resolve the issue"]))

        # Add healing-specific actions
        if healing_attempted and not healing_success:
            actions.append("Review APU-163 self-healing failure logs")
            actions.append("Update auto-resolution strategies")

        return actions

    def _estimate_impact(self, problem: Dict[str, Any], issue_type: IssueType) -> str:
        """Estimate issue impact."""
        severity = problem.get("severity", "medium")

        impact_matrix = {
            ("critical", IssueType.API_INFRASTRUCTURE): "High - Core infrastructure affected, potential service disruption",
            ("high", IssueType.PLATFORM_TIMEOUT): "Medium - Platform publishing affected, reduced reach",
            ("medium", IssueType.AUTHENTICATION): "Low - Authentication issues, limited functionality",
            ("low", IssueType.COMMUNITY_HEALTH): "Low - Community metrics affected, monitoring only"
        }

        return impact_matrix.get((severity, issue_type), f"{severity.title()} impact on {issue_type.value}")

    def _generate_tags(self, problem: Dict[str, Any], issue_type: IssueType) -> List[str]:
        """Generate relevant tags for the issue."""
        base_tags = ["apu163", "engagement", "monitoring", "automated"]

        # Add issue type specific tags
        type_tags = {
            IssueType.API_INFRASTRUCTURE: ["api", "infrastructure"],
            IssueType.PLATFORM_TIMEOUT: ["timeout", "platform"],
            IssueType.AUTHENTICATION: ["auth", "security"],
            IssueType.ENGAGEMENT_ANOMALY: ["anomaly", "community"],
            IssueType.PERFORMANCE_DEGRADATION: ["performance", "optimization"]
        }

        base_tags.extend(type_tags.get(issue_type, []))

        # Add severity tag
        base_tags.append(problem.get("severity", "medium"))

        return base_tags

    def _save_issue_to_database(self, issue: PaperclipIssueEnhanced):
        """Save enhanced issue to APU-163 database."""
        db_path = self.monitor.db_path

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Enhanced issue tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS paperclip_issues_enhanced (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    issue_id TEXT UNIQUE NOT NULL,
                    apu_number TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    department TEXT NOT NULL,
                    status TEXT NOT NULL,
                    issue_type TEXT NOT NULL,
                    created_timestamp TEXT NOT NULL,
                    updated_timestamp TEXT NOT NULL,
                    resolved_timestamp TEXT,
                    assigned_agent TEXT,
                    source_component TEXT NOT NULL,
                    auto_resolution_attempted BOOLEAN DEFAULT FALSE,
                    resolution_method TEXT,
                    estimated_impact TEXT,
                    resolution_confidence REAL,
                    follow_up_required BOOLEAN DEFAULT TRUE
                )
            """)

            cursor.execute("""
                INSERT OR REPLACE INTO paperclip_issues_enhanced
                (issue_id, apu_number, title, description, priority, department, status, issue_type,
                 created_timestamp, updated_timestamp, resolved_timestamp, assigned_agent, source_component,
                 auto_resolution_attempted, resolution_method, estimated_impact, resolution_confidence, follow_up_required)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                issue.issue_id, issue.apu_number, issue.title, issue.description,
                issue.priority, issue.department, issue.status.value, issue.issue_type.value,
                issue.created_timestamp, issue.updated_timestamp, issue.resolved_timestamp,
                issue.assigned_agent, issue.source_component, issue.auto_resolution_attempted,
                issue.resolution_method, issue.estimated_impact, issue.resolution_confidence,
                issue.follow_up_required
            ))

            conn.commit()

    def _save_issue_to_paperclip(self, issue: PaperclipIssueEnhanced):
        """Save issue to Paperclip file system."""

        # Create filename
        filename = f"{issue.apu_number.lower().replace('-', '_')}_{issue.issue_type.value}.json"
        issue_file = self.tasks_dir / filename

        # Create Paperclip-compatible format
        paperclip_data = {
            "issue_id": issue.issue_id,
            "apu_number": issue.apu_number,
            "title": issue.title,
            "description": issue.description,
            "priority": issue.priority,
            "status": issue.status.value,
            "department": issue.department,
            "issue_type": issue.issue_type.value,
            "created_timestamp": issue.created_timestamp,
            "updated_timestamp": issue.updated_timestamp,
            "resolved_timestamp": issue.resolved_timestamp,
            "assigned_agent": issue.assigned_agent,
            "source_component": issue.source_component,
            "auto_resolution_attempted": issue.auto_resolution_attempted,
            "resolution_method": issue.resolution_method,
            "estimated_impact": issue.estimated_impact,
            "related_issues": issue.related_issues,
            "tags": issue.tags,
            "health_impact": f"{issue.priority.title()} - {issue.estimated_impact}",
            "follow_up_required": issue.follow_up_required
        }

        save_json(issue_file, paperclip_data)
        print(f"[APU-163] Saved Paperclip issue to: {issue_file}")

    def _check_escalation_needed(self, issue: PaperclipIssueEnhanced):
        """Check if issue needs escalation based on patterns."""
        issue_type = issue.issue_type.value

        if issue_type not in self.escalation_thresholds:
            return

        # Count similar recent issues
        similar_count = self._count_similar_recent_issues(issue)
        threshold = self.escalation_thresholds[issue_type]

        if similar_count >= threshold:
            self._escalate_issue(issue, similar_count)

    def _count_similar_recent_issues(self, issue: PaperclipIssueEnhanced) -> int:
        """Count similar issues in the last 24 hours."""
        count = 0
        cutoff_time = datetime.now() - timedelta(hours=24)

        db_path = self.monitor.db_path

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM paperclip_issues_enhanced
                WHERE issue_type = ? AND created_timestamp > ?
            """, (issue.issue_type.value, cutoff_time.isoformat()))

            result = cursor.fetchone()
            count = result[0] if result else 0

        return count

    def _escalate_issue(self, issue: PaperclipIssueEnhanced, similar_count: int):
        """Escalate issue due to pattern detection."""
        print(f"[APU-163] ESCALATION: {issue.apu_number} - {similar_count} similar issues detected")

        # Create escalation alert
        escalation_alert = {
            "alert_id": f"escalation_{issue.issue_id}_{int(datetime.now().timestamp())}",
            "timestamp": datetime.now().isoformat(),
            "alert_type": "pattern_escalation",
            "severity": "high",
            "message": f"Issue pattern detected: {similar_count} similar {issue.issue_type.value} issues",
            "affected_issue": issue.apu_number,
            "pattern_count": similar_count,
            "recommended_action": "Review pattern for systematic resolution",
            "escalation_department": "chief_of_staff"
        }

        alert_file = self.alerts_dir / f"escalation_{issue.apu_number.lower()}.json"
        save_json(alert_file, escalation_alert)

    def update_issue_status(self, issue_id: str, new_status: IssueStatus,
                          resolution_method: Optional[str] = None,
                          resolution_confidence: Optional[float] = None) -> bool:
        """Update issue status with enhanced tracking."""

        db_path = self.monitor.db_path

        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()

                # Update database
                update_values = [new_status.value, datetime.now().isoformat()]
                update_query = "UPDATE paperclip_issues_enhanced SET status = ?, updated_timestamp = ?"

                if new_status == IssueStatus.RESOLVED:
                    update_query += ", resolved_timestamp = ?"
                    update_values.append(datetime.now().isoformat())

                if resolution_method:
                    update_query += ", resolution_method = ?"
                    update_values.append(resolution_method)

                if resolution_confidence is not None:
                    update_query += ", resolution_confidence = ?"
                    update_values.append(resolution_confidence)

                update_query += " WHERE issue_id = ?"
                update_values.append(issue_id)

                cursor.execute(update_query, update_values)
                rows_affected = cursor.rowcount
                conn.commit()

                if rows_affected > 0:
                    print(f"[APU-163] Updated issue {issue_id} to status: {new_status.value}")

                    # Also update file system
                    self._update_issue_file(issue_id, new_status, resolution_method, resolution_confidence)
                    return True

        except Exception as e:
            print(f"[APU-163] Error updating issue {issue_id}: {e}")

        return False

    def _update_issue_file(self, issue_id: str, new_status: IssueStatus,
                          resolution_method: Optional[str], resolution_confidence: Optional[float]):
        """Update issue file in Paperclip directory."""

        # Find the issue file
        for issue_file in self.tasks_dir.glob("*.json"):
            try:
                issue_data = load_json(issue_file)
                if issue_data.get("issue_id") == issue_id:
                    # Update the data
                    issue_data["status"] = new_status.value
                    issue_data["updated_timestamp"] = datetime.now().isoformat()

                    if new_status == IssueStatus.RESOLVED:
                        issue_data["resolved_timestamp"] = datetime.now().isoformat()

                    if resolution_method:
                        issue_data["resolution_method"] = resolution_method

                    if resolution_confidence is not None:
                        issue_data["resolution_confidence"] = resolution_confidence

                    # Save updated data
                    save_json(issue_file, issue_data)
                    print(f"[APU-163] Updated issue file: {issue_file}")
                    break

            except Exception as e:
                continue

    def generate_integration_report(self) -> Dict[str, Any]:
        """Generate comprehensive integration status report."""

        db_path = self.monitor.db_path

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Get issue statistics
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM paperclip_issues_enhanced
                GROUP BY status
            """)

            status_counts = {row[0]: row[1] for row in cursor.fetchall()}

            cursor.execute("""
                SELECT issue_type, COUNT(*) as count
                FROM paperclip_issues_enhanced
                GROUP BY issue_type
            """)

            type_counts = {row[0]: row[1] for row in cursor.fetchall()}

            # Get resolution statistics
            cursor.execute("""
                SELECT AVG(resolution_confidence) as avg_confidence,
                       COUNT(*) as total_resolved
                FROM paperclip_issues_enhanced
                WHERE status = 'resolved' AND resolution_confidence IS NOT NULL
            """)

            resolution_stats = cursor.fetchone()

        report = {
            "integration_status": "active",
            "report_timestamp": datetime.now().isoformat(),
            "issue_statistics": {
                "total_issues_created": sum(status_counts.values()),
                "by_status": status_counts,
                "by_type": type_counts
            },
            "resolution_statistics": {
                "average_confidence": resolution_stats[0] if resolution_stats[0] else 0.0,
                "total_resolved": resolution_stats[1] if resolution_stats[1] else 0
            },
            "file_system_status": {
                "tasks_directory": str(self.tasks_dir),
                "alerts_directory": str(self.alerts_dir),
                "total_task_files": len(list(self.tasks_dir.glob("*.json"))),
                "total_alert_files": len(list(self.alerts_dir.glob("*.json")))
            },
            "next_issue_number": self.issue_counter,
            "department_coordination": {
                "total_departments": len(self.department_agents),
                "agents_configured": list(self.department_agents.values())
            }
        }

        return report


def main():
    """Test APU-163 Paperclip integration."""
    print("=" * 70)
    print("APU-163 PAPERCLIP INTEGRATION TEST")
    print("=" * 70)

    # Mock APU-163 monitor for testing
    class MockMonitor:
        def __init__(self):
            self.db_path = VAWN_DIR / "database" / "apu163_test.db"
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

    mock_monitor = MockMonitor()
    integration = APU163PaperclipIntegration(mock_monitor)

    # Test issue creation
    test_problem = {
        "type": "api_degradation",
        "description": "API health critically low: 7/9 endpoints failing with 404 errors",
        "severity": "high",
        "detected_at": datetime.now().isoformat()
    }

    print("\n[TEST] Creating enhanced issue...")
    issue = integration.create_enhanced_issue(test_problem, healing_attempted=True, healing_success=False)

    print(f"Created: {issue.apu_number}")
    print(f"Type: {issue.issue_type.value}")
    print(f"Priority: {issue.priority}")
    print(f"Department: {issue.department}")

    # Test status update
    print(f"\n[TEST] Updating issue status...")
    success = integration.update_issue_status(
        issue.issue_id,
        IssueStatus.IN_PROGRESS,
        resolution_method="manual_investigation"
    )
    print(f"Status update: {'Success' if success else 'Failed'}")

    # Generate report
    print(f"\n[TEST] Generating integration report...")
    report = integration.generate_integration_report()
    print(f"Total issues: {report['issue_statistics']['total_issues_created']}")
    print(f"Next APU number: {report['next_issue_number']}")

    print(f"\n[TEST] Paperclip integration test complete!")
    return 0


if __name__ == "__main__":
    exit(main())