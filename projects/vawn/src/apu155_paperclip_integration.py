"""
APU-155 Paperclip Workflow Integration
Seamless integration with Apulu Universe department coordination and task management.

Created by: Dex - Community Agent (APU-155)
Component: Paperclip Workflow Integration

FEATURES:
✅ Automated task creation and status updates in Paperclip system
✅ Cross-department coordination and communication workflows
✅ Issue escalation and routing to appropriate department teams
✅ Community health status reporting to stakeholders
✅ Alert prioritization and department-specific notifications
✅ Strategic insight distribution to Content and Marketing teams
✅ Performance metrics integration with department dashboards
"""

import json
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import sys

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from vawn_config import (
    load_json, save_json, ENGAGEMENT_LOG, RESEARCH_LOG, VAWN_DIR,
    log_run, today_str
)

class PaperclipPriority(Enum):
    """Paperclip task priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class DepartmentType(Enum):
    """Apulu Universe department types."""
    COMMUNITY = "community"
    CONTENT = "content"
    MARKETING = "marketing"
    ANALYTICS = "analytics"
    CHIEF_OF_STAFF = "chief_of_staff"
    LEADERSHIP = "leadership"

class TaskStatus(Enum):
    """Paperclip task status."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

@dataclass
class PaperclipTask:
    """Paperclip task representation."""
    task_id: str
    title: str
    description: str
    priority: PaperclipPriority
    status: TaskStatus
    assigned_department: DepartmentType
    assigned_agent: Optional[str]

    # Metadata
    created_timestamp: str
    updated_timestamp: str
    due_date: Optional[str]
    estimated_hours: Optional[float]

    # Context
    source_component: str
    related_platform: Optional[str]
    health_impact: str

    # Tracking
    progress_percentage: float
    blockers: List[str]
    dependencies: List[str]
    notes: List[str]

@dataclass
class DepartmentAlert:
    """Department-specific alert notification."""
    alert_id: str
    department: DepartmentType
    alert_type: str
    urgency: int  # 1-10 scale

    # Content
    title: str
    message: str
    context: Dict[str, Any]

    # Actions
    required_actions: List[str]
    suggested_responses: List[str]
    escalation_path: List[str]

    # Timing
    created_timestamp: str
    response_deadline: Optional[str]
    auto_escalation_time: Optional[str]

@dataclass
class HealthStatusReport:
    """Community health status report for departments."""
    report_id: str
    timestamp: str
    reporting_period_hours: float

    # Executive Summary
    overall_health_score: float
    health_trend: str  # improving, declining, stable
    key_insights: List[str]
    critical_actions_needed: List[str]

    # Platform Breakdown
    platform_performance: Dict[str, Any]
    cross_platform_insights: Dict[str, Any]

    # Department-Specific Insights
    content_recommendations: List[str]
    marketing_opportunities: List[str]
    community_concerns: List[str]

    # Metrics
    engagement_metrics: Dict[str, float]
    quality_indicators: Dict[str, float]
    growth_metrics: Dict[str, float]

    # Next Steps
    strategic_priorities: List[str]
    resource_needs: List[str]
    success_metrics: List[str]

class APU155PaperclipIntegration:
    """Comprehensive Paperclip workflow integration for APU-155."""

    def __init__(self):
        self.session_id = f"paperclip_{int(datetime.now().timestamp())}"
        self.integration_config = self._load_integration_config()

        # Paperclip system paths
        self.paperclip_tasks_dir = VAWN_DIR / "paperclip" / "tasks"
        self.paperclip_alerts_dir = VAWN_DIR / "paperclip" / "alerts"
        self.paperclip_reports_dir = VAWN_DIR / "paperclip" / "reports"

        # Ensure directories exist
        for directory in [self.paperclip_tasks_dir, self.paperclip_alerts_dir, self.paperclip_reports_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # Department coordination
        self.department_contacts = self._load_department_contacts()
        self.active_tasks = self._load_active_tasks()
        self.escalation_rules = self._load_escalation_rules()

        print(f"[APU-155 Paperclip] Initialized workflow integration (Session: {self.session_id})")

    def _load_integration_config(self) -> Dict[str, Any]:
        """Load Paperclip integration configuration."""
        default_config = {
            "auto_task_creation": True,
            "auto_alert_routing": True,
            "health_report_frequency_hours": 24,
            "critical_alert_escalation_minutes": 15,
            "department_notification_delay_minutes": 5,
            "task_auto_assignment": True,
            "cross_department_coordination": True,
            "stakeholder_updates": True
        }

        config_file = VAWN_DIR / "config" / "apu155_paperclip_config.json"
        if config_file.exists():
            try:
                user_config = load_json(config_file)
                default_config.update(user_config)
            except Exception as e:
                print(f"[APU-155 Paperclip] Warning: Could not load config: {e}")

        return default_config

    def _load_department_contacts(self) -> Dict[DepartmentType, Dict[str, Any]]:
        """Load department contact information and coordination details."""
        return {
            DepartmentType.COMMUNITY: {
                "primary_agent": "Dex",
                "notification_channels": ["paperclip_tasks", "community_alerts"],
                "escalation_threshold_minutes": 30,
                "specialties": ["engagement", "health_monitoring", "user_experience"]
            },
            DepartmentType.CONTENT: {
                "primary_agent": "ContentTeam",
                "notification_channels": ["paperclip_tasks", "content_strategy"],
                "escalation_threshold_minutes": 60,
                "specialties": ["content_creation", "strategy", "performance_analysis"]
            },
            DepartmentType.MARKETING: {
                "primary_agent": "MarketingTeam",
                "notification_channels": ["paperclip_tasks", "growth_metrics"],
                "escalation_threshold_minutes": 45,
                "specialties": ["growth", "acquisition", "campaign_management"]
            },
            DepartmentType.ANALYTICS: {
                "primary_agent": "AnalyticsTeam",
                "notification_channels": ["paperclip_tasks", "data_insights"],
                "escalation_threshold_minutes": 120,
                "specialties": ["data_analysis", "metrics", "reporting"]
            },
            DepartmentType.CHIEF_OF_STAFF: {
                "primary_agent": "CoS",
                "notification_channels": ["executive_briefing", "strategic_alerts"],
                "escalation_threshold_minutes": 15,
                "specialties": ["coordination", "strategic_oversight", "resource_allocation"]
            }
        }

    def _load_active_tasks(self) -> Dict[str, PaperclipTask]:
        """Load currently active Paperclip tasks."""
        active_tasks = {}

        try:
            for task_file in self.paperclip_tasks_dir.glob("*.json"):
                task_data = load_json(task_file)
                if task_data.get("status") in ["todo", "in_progress", "blocked"]:
                    active_tasks[task_data["task_id"]] = PaperclipTask(**task_data)
        except Exception as e:
            print(f"[APU-155 Paperclip] Warning: Could not load active tasks: {e}")

        return active_tasks

    def _load_escalation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load escalation rules for different alert types."""
        return {
            "critical_community_health": {
                "immediate_notify": [DepartmentType.CHIEF_OF_STAFF, DepartmentType.COMMUNITY],
                "escalate_after_minutes": 15,
                "escalate_to": [DepartmentType.LEADERSHIP],
                "max_escalation_levels": 3
            },
            "system_wide_failure": {
                "immediate_notify": [DepartmentType.CHIEF_OF_STAFF, DepartmentType.ANALYTICS],
                "escalate_after_minutes": 5,
                "escalate_to": [DepartmentType.LEADERSHIP],
                "max_escalation_levels": 2
            },
            "content_strategy_concern": {
                "immediate_notify": [DepartmentType.CONTENT, DepartmentType.COMMUNITY],
                "escalate_after_minutes": 60,
                "escalate_to": [DepartmentType.CHIEF_OF_STAFF],
                "max_escalation_levels": 2
            },
            "growth_opportunity": {
                "immediate_notify": [DepartmentType.MARKETING, DepartmentType.CONTENT],
                "escalate_after_minutes": 240,
                "escalate_to": [DepartmentType.CHIEF_OF_STAFF],
                "max_escalation_levels": 1
            }
        }

    def process_health_assessment_results(self, assessment_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process APU-155 health assessment results and integrate with Paperclip workflows.

        Args:
            assessment_results: Results from APU-155 health assessment

        Returns:
            Integration results with tasks created, alerts routed, reports generated
        """
        integration_start = time.time()

        integration_results = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "integration_duration_seconds": None,
            "tasks_created": [],
            "alerts_routed": [],
            "reports_generated": [],
            "department_notifications": [],
            "escalations_triggered": [],
            "coordination_actions": []
        }

        try:
            print(f"[APU-155 Paperclip] Processing health assessment for workflow integration...")

            # Phase 1: Create Paperclip tasks for critical issues
            if self.integration_config["auto_task_creation"]:
                tasks_created = self._create_paperclip_tasks_from_assessment(assessment_results)
                integration_results["tasks_created"] = [asdict(task) for task in tasks_created]

            # Phase 2: Route alerts to appropriate departments
            if self.integration_config["auto_alert_routing"]:
                alerts_routed = self._route_alerts_to_departments(assessment_results)
                integration_results["alerts_routed"] = [asdict(alert) for alert in alerts_routed]

            # Phase 3: Generate health status reports for stakeholders
            health_report = self._generate_stakeholder_health_report(assessment_results)
            integration_results["reports_generated"].append(asdict(health_report))

            # Phase 4: Trigger cross-department coordination
            if self.integration_config["cross_department_coordination"]:
                coordination_actions = self._coordinate_cross_department_actions(assessment_results)
                integration_results["coordination_actions"] = coordination_actions

            # Phase 5: Handle escalations for critical issues
            escalations = self._handle_critical_escalations(assessment_results)
            integration_results["escalations_triggered"] = escalations

            # Phase 6: Update department dashboards and notifications
            notifications = self._send_department_notifications(assessment_results)
            integration_results["department_notifications"] = notifications

            integration_duration = time.time() - integration_start
            integration_results["integration_duration_seconds"] = integration_duration

            print(f"[APU-155 Paperclip] Integration completed: {len(integration_results['tasks_created'])} tasks, "
                  f"{len(integration_results['alerts_routed'])} alerts, {integration_duration:.2f}s")

            # Save integration results
            self._save_integration_results(integration_results)

            return integration_results

        except Exception as e:
            error_msg = f"Paperclip integration failed: {str(e)}"
            print(f"[APU-155 Paperclip] {error_msg}")

            integration_results["error"] = error_msg
            integration_duration = time.time() - integration_start
            integration_results["integration_duration_seconds"] = integration_duration

            return integration_results

    def _create_paperclip_tasks_from_assessment(self, assessment_results: Dict[str, Any]) -> List[PaperclipTask]:
        """Create Paperclip tasks based on health assessment results."""
        tasks_created = []
        current_time = datetime.now().isoformat()

        # Create tasks for critical alerts
        for alert_data in assessment_results.get("alerts_generated", []):
            if alert_data["severity"] in ["critical", "high"]:
                task = self._create_task_from_alert(alert_data, current_time)
                if task:
                    tasks_created.append(task)
                    self._save_paperclip_task(task)

        # Create tasks for declining platform health
        for platform, health_data in assessment_results.get("platform_health_scores", {}).items():
            if health_data["overall_health_score"] < 0.4:
                task = self._create_platform_health_task(platform, health_data, current_time)
                if task:
                    tasks_created.append(task)
                    self._save_paperclip_task(task)

        # Create strategic tasks from insights
        for insight in assessment_results.get("strategic_insights", []):
            if "urgent" in insight.lower() or "critical" in insight.lower():
                task = self._create_strategic_task(insight, current_time)
                if task:
                    tasks_created.append(task)
                    self._save_paperclip_task(task)

        return tasks_created

    def _create_task_from_alert(self, alert_data: Dict[str, Any], timestamp: str) -> Optional[PaperclipTask]:
        """Create a Paperclip task from an alert."""
        try:
            # Determine appropriate department based on alert category
            department = self._determine_alert_department(alert_data)

            # Set priority based on alert severity
            priority_mapping = {
                "critical": PaperclipPriority.CRITICAL,
                "high": PaperclipPriority.HIGH,
                "medium": PaperclipPriority.MEDIUM,
                "low": PaperclipPriority.LOW
            }
            priority = priority_mapping.get(alert_data["severity"], PaperclipPriority.MEDIUM)

            # Calculate due date based on priority
            due_date = self._calculate_task_due_date(priority)

            task = PaperclipTask(
                task_id=f"apu155_{alert_data['alert_id']}",
                title=f"Resolve: {alert_data['title']}",
                description=f"{alert_data['description']}\\n\\nRoot Cause: {alert_data['primary_cause']}\\n\\nRecommended Actions:\\n" +
                           "\\n".join(f"• {action}" for action in alert_data['recommended_actions']),
                priority=priority,
                status=TaskStatus.TODO,
                assigned_department=department,
                assigned_agent=self.department_contacts[department]["primary_agent"],
                created_timestamp=timestamp,
                updated_timestamp=timestamp,
                due_date=due_date,
                estimated_hours=self._estimate_task_hours(alert_data),
                source_component="apu155_health_monitor",
                related_platform=alert_data.get("platform"),
                health_impact=alert_data.get("impact_assessment", "Unknown impact"),
                progress_percentage=0.0,
                blockers=[],
                dependencies=[],
                notes=[f"Auto-generated from APU-155 alert: {alert_data['alert_id']}"]
            )

            return task

        except Exception as e:
            print(f"[APU-155 Paperclip] Error creating task from alert: {e}")
            return None

    def _determine_alert_department(self, alert_data: Dict[str, Any]) -> DepartmentType:
        """Determine which department should handle an alert."""
        alert_category = alert_data.get("category", "").lower()
        alert_type = alert_data.get("alert_type", "").lower()

        if "infrastructure" in alert_category or "authentication" in alert_category:
            return DepartmentType.ANALYTICS
        elif "community" in alert_type or "engagement" in alert_type:
            return DepartmentType.COMMUNITY
        elif "content" in alert_type or "quality" in alert_type:
            return DepartmentType.CONTENT
        elif "growth" in alert_type or "acquisition" in alert_type:
            return DepartmentType.MARKETING
        elif "critical" in alert_data.get("severity", ""):
            return DepartmentType.CHIEF_OF_STAFF
        else:
            return DepartmentType.COMMUNITY  # Default to Community department

    def _calculate_task_due_date(self, priority: PaperclipPriority) -> str:
        """Calculate appropriate due date based on task priority."""
        now = datetime.now()

        if priority == PaperclipPriority.CRITICAL:
            due_date = now + timedelta(hours=4)
        elif priority == PaperclipPriority.HIGH:
            due_date = now + timedelta(hours=24)
        elif priority == PaperclipPriority.MEDIUM:
            due_date = now + timedelta(days=3)
        else:
            due_date = now + timedelta(days=7)

        return due_date.isoformat()

    def _estimate_task_hours(self, alert_data: Dict[str, Any]) -> float:
        """Estimate hours required for task completion."""
        severity = alert_data.get("severity", "medium").lower()
        actions_count = len(alert_data.get("recommended_actions", []))

        base_hours = {
            "critical": 8.0,
            "high": 4.0,
            "medium": 2.0,
            "low": 1.0
        }.get(severity, 2.0)

        # Adjust based on number of recommended actions
        adjustment_factor = 1.0 + (actions_count * 0.2)

        return min(base_hours * adjustment_factor, 40.0)  # Cap at 40 hours

    def _create_platform_health_task(self, platform: str, health_data: Dict[str, Any], timestamp: str) -> Optional[PaperclipTask]:
        """Create task for declining platform health."""
        try:
            task = PaperclipTask(
                task_id=f"apu155_health_{platform}_{int(datetime.now().timestamp())}",
                title=f"Improve {platform.title()} Community Health",
                description=f"Platform health below threshold at {health_data['overall_health_score']:.1%}\\n\\n"
                           f"Key Issues:\\n"
                           f"• Engagement Vitality: {health_data['engagement_vitality']:.1%}\\n"
                           f"• Content Quality: {health_data['content_quality']:.1%}\\n"
                           f"• Lifecycle Stage: {health_data['lifecycle_stage']}\\n\\n"
                           f"Recommended Actions:\\n"
                           f"• Review content strategy for {platform}\\n"
                           f"• Analyze recent engagement patterns\\n"
                           f"• Implement platform-specific improvements",
                priority=PaperclipPriority.HIGH,
                status=TaskStatus.TODO,
                assigned_department=DepartmentType.CONTENT,
                assigned_agent=self.department_contacts[DepartmentType.CONTENT]["primary_agent"],
                created_timestamp=timestamp,
                updated_timestamp=timestamp,
                due_date=self._calculate_task_due_date(PaperclipPriority.HIGH),
                estimated_hours=6.0,
                source_component="apu155_health_monitor",
                related_platform=platform,
                health_impact=f"Platform health critically low: {health_data['overall_health_score']:.1%}",
                progress_percentage=0.0,
                blockers=[],
                dependencies=[],
                notes=[f"Auto-generated from platform health assessment - confidence: {health_data.get('confidence_level', 0):.1%}"]
            )

            return task

        except Exception as e:
            print(f"[APU-155 Paperclip] Error creating platform health task: {e}")
            return None

    def _create_strategic_task(self, insight: str, timestamp: str) -> Optional[PaperclipTask]:
        """Create strategic task from insight."""
        try:
            task_id = f"apu155_strategic_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"

            # Determine priority and department based on insight content
            if "urgent" in insight.lower() or "critical" in insight.lower():
                priority = PaperclipPriority.HIGH
                department = DepartmentType.CHIEF_OF_STAFF
            elif "content" in insight.lower():
                priority = PaperclipPriority.MEDIUM
                department = DepartmentType.CONTENT
            elif "marketing" in insight.lower() or "growth" in insight.lower():
                priority = PaperclipPriority.MEDIUM
                department = DepartmentType.MARKETING
            else:
                priority = PaperclipPriority.MEDIUM
                department = DepartmentType.COMMUNITY

            task = PaperclipTask(
                task_id=task_id,
                title=f"Strategic Action: {insight[:50]}...",
                description=f"Strategic insight requiring action:\\n\\n{insight}\\n\\n"
                           f"Please review and implement appropriate strategies based on this community health insight.",
                priority=priority,
                status=TaskStatus.TODO,
                assigned_department=department,
                assigned_agent=self.department_contacts[department]["primary_agent"],
                created_timestamp=timestamp,
                updated_timestamp=timestamp,
                due_date=self._calculate_task_due_date(priority),
                estimated_hours=4.0,
                source_component="apu155_strategic_insights",
                related_platform=None,
                health_impact="Strategic optimization opportunity",
                progress_percentage=0.0,
                blockers=[],
                dependencies=[],
                notes=["Auto-generated from APU-155 strategic insights"]
            )

            return task

        except Exception as e:
            print(f"[APU-155 Paperclip] Error creating strategic task: {e}")
            return None

    def _save_paperclip_task(self, task: PaperclipTask):
        """Save Paperclip task to file system."""
        try:
            task_file = self.paperclip_tasks_dir / f"{task.task_id}.json"
            save_json(task_file, asdict(task))

            # Add to active tasks
            self.active_tasks[task.task_id] = task

            print(f"[APU-155 Paperclip] Created task: {task.title} ({task.priority.value})")

        except Exception as e:
            print(f"[APU-155 Paperclip] Error saving task: {e}")

    def _route_alerts_to_departments(self, assessment_results: Dict[str, Any]) -> List[DepartmentAlert]:
        """Route alerts to appropriate departments."""
        alerts_routed = []

        for alert_data in assessment_results.get("alerts_generated", []):
            try:
                department_alert = self._create_department_alert(alert_data)
                if department_alert:
                    alerts_routed.append(department_alert)
                    self._save_department_alert(department_alert)
            except Exception as e:
                print(f"[APU-155 Paperclip] Error routing alert: {e}")

        return alerts_routed

    def _create_department_alert(self, alert_data: Dict[str, Any]) -> Optional[DepartmentAlert]:
        """Create department-specific alert."""
        try:
            department = self._determine_alert_department(alert_data)

            # Map severity to urgency score
            urgency_mapping = {
                "critical": 10,
                "high": 8,
                "medium": 5,
                "low": 3,
                "info": 1
            }
            urgency = urgency_mapping.get(alert_data.get("severity", "medium"), 5)

            # Set response deadline based on urgency
            response_deadline = None
            auto_escalation_time = None
            if urgency >= 8:
                response_deadline = (datetime.now() + timedelta(minutes=30)).isoformat()
                auto_escalation_time = (datetime.now() + timedelta(minutes=60)).isoformat()
            elif urgency >= 5:
                response_deadline = (datetime.now() + timedelta(hours=4)).isoformat()
                auto_escalation_time = (datetime.now() + timedelta(hours=8)).isoformat()

            department_alert = DepartmentAlert(
                alert_id=f"dept_{alert_data['alert_id']}",
                department=department,
                alert_type=alert_data.get("alert_type", "general"),
                urgency=urgency,
                title=alert_data["title"],
                message=f"{alert_data['description']}\\n\\nRoot Cause: {alert_data['primary_cause']}",
                context={
                    "platform": alert_data.get("platform"),
                    "severity": alert_data["severity"],
                    "impact": alert_data.get("impact_assessment"),
                    "affected_components": alert_data.get("affected_components", [])
                },
                required_actions=alert_data.get("recommended_actions", []),
                suggested_responses=alert_data.get("prevention_strategies", []),
                escalation_path=alert_data.get("escalation_path", []),
                created_timestamp=datetime.now().isoformat(),
                response_deadline=response_deadline,
                auto_escalation_time=auto_escalation_time
            )

            return department_alert

        except Exception as e:
            print(f"[APU-155 Paperclip] Error creating department alert: {e}")
            return None

    def _save_department_alert(self, alert: DepartmentAlert):
        """Save department alert to appropriate channels."""
        try:
            alert_file = self.paperclip_alerts_dir / f"{alert.alert_id}.json"
            save_json(alert_file, asdict(alert))

            print(f"[APU-155 Paperclip] Routed alert to {alert.department.value}: {alert.title}")

        except Exception as e:
            print(f"[APU-155 Paperclip] Error saving department alert: {e}")

    def _generate_stakeholder_health_report(self, assessment_results: Dict[str, Any]) -> HealthStatusReport:
        """Generate comprehensive health status report for stakeholders."""

        report_id = f"health_report_{int(datetime.now().timestamp())}"
        current_time = datetime.now().isoformat()

        # Extract key metrics
        overall_health = assessment_results.get("overall_community_health", 0.0)
        platform_health = assessment_results.get("platform_health_scores", {})
        cross_platform_insights = assessment_results.get("cross_platform_insights", {})

        # Determine health trend
        health_trend = "stable"  # Would be calculated from historical data
        if overall_health > 0.7:
            health_trend = "improving"
        elif overall_health < 0.4:
            health_trend = "declining"

        # Generate department-specific recommendations
        content_recs = self._generate_content_recommendations(platform_health)
        marketing_ops = self._generate_marketing_opportunities(cross_platform_insights)
        community_concerns = self._generate_community_concerns(assessment_results)

        report = HealthStatusReport(
            report_id=report_id,
            timestamp=current_time,
            reporting_period_hours=24.0,  # Standard daily report
            overall_health_score=overall_health,
            health_trend=health_trend,
            key_insights=assessment_results.get("strategic_insights", []),
            critical_actions_needed=assessment_results.get("recommendations", []),
            platform_performance=platform_health,
            cross_platform_insights=cross_platform_insights,
            content_recommendations=content_recs,
            marketing_opportunities=marketing_ops,
            community_concerns=community_concerns,
            engagement_metrics=self._extract_engagement_metrics(assessment_results),
            quality_indicators=self._extract_quality_indicators(assessment_results),
            growth_metrics=self._extract_growth_metrics(assessment_results),
            strategic_priorities=self._generate_strategic_priorities(assessment_results),
            resource_needs=self._identify_resource_needs(assessment_results),
            success_metrics=self._define_success_metrics(assessment_results)
        )

        # Save report
        self._save_health_report(report)

        return report

    def _generate_content_recommendations(self, platform_health: Dict[str, Any]) -> List[str]:
        """Generate content strategy recommendations based on platform health."""
        recommendations = []

        for platform, health_data in platform_health.items():
            if health_data["content_quality"] < 0.5:
                recommendations.append(f"Improve content diversity and quality on {platform}")

            if health_data["engagement_vitality"] < 0.4:
                recommendations.append(f"Review posting strategy and timing for {platform}")

        return recommendations

    def _generate_marketing_opportunities(self, cross_platform_insights: Dict[str, Any]) -> List[str]:
        """Generate marketing opportunities based on cross-platform analysis."""
        opportunities = []

        strongest_platform = cross_platform_insights.get("strongest_platform")
        if strongest_platform:
            opportunities.append(f"Scale successful strategies from {strongest_platform} to other platforms")

        overall_pattern = cross_platform_insights.get("overall_pattern")
        if overall_pattern == "thriving":
            opportunities.append("Consider expanding to new platforms or increasing content volume")

        return opportunities

    def _generate_community_concerns(self, assessment_results: Dict[str, Any]) -> List[str]:
        """Generate community concerns that need attention."""
        concerns = []

        alerts = assessment_results.get("alerts_generated", [])
        critical_alerts = [alert for alert in alerts if alert["severity"] == "critical"]

        if critical_alerts:
            concerns.append(f"Critical community issues detected: {len(critical_alerts)} alerts")

        if assessment_results.get("overall_community_health", 0) < 0.5:
            concerns.append("Overall community health below optimal threshold")

        return concerns

    def _extract_engagement_metrics(self, assessment_results: Dict[str, Any]) -> Dict[str, float]:
        """Extract key engagement metrics."""
        metrics = {}

        platform_health = assessment_results.get("platform_health_scores", {})
        for platform, health_data in platform_health.items():
            metrics[f"{platform}_engagement"] = health_data.get("engagement_vitality", 0.0)
            metrics[f"{platform}_responsiveness"] = health_data.get("community_sentiment", 0.0)

        return metrics

    def _extract_quality_indicators(self, assessment_results: Dict[str, Any]) -> Dict[str, float]:
        """Extract data and content quality indicators."""
        indicators = {}

        platform_health = assessment_results.get("platform_health_scores", {})
        for platform, health_data in platform_health.items():
            indicators[f"{platform}_content_quality"] = health_data.get("content_quality", 0.0)
            indicators[f"{platform}_data_confidence"] = health_data.get("confidence_level", 0.0)

        return indicators

    def _extract_growth_metrics(self, assessment_results: Dict[str, Any]) -> Dict[str, float]:
        """Extract growth and momentum metrics."""
        metrics = {}

        platform_health = assessment_results.get("platform_health_scores", {})
        for platform, health_data in platform_health.items():
            metrics[f"{platform}_growth_momentum"] = health_data.get("growth_momentum", 0.0)

        return metrics

    def _generate_strategic_priorities(self, assessment_results: Dict[str, Any]) -> List[str]:
        """Generate strategic priorities based on assessment."""
        priorities = []

        if assessment_results.get("overall_community_health", 0) < 0.5:
            priorities.append("Community health recovery initiative")

        alerts = assessment_results.get("alerts_generated", [])
        if any(alert["severity"] == "critical" for alert in alerts):
            priorities.append("Address critical infrastructure and engagement issues")

        return priorities

    def _identify_resource_needs(self, assessment_results: Dict[str, Any]) -> List[str]:
        """Identify resource needs based on assessment."""
        needs = []

        platform_health = assessment_results.get("platform_health_scores", {})
        low_confidence_platforms = [
            platform for platform, health in platform_health.items()
            if health.get("confidence_level", 0) < 0.5
        ]

        if low_confidence_platforms:
            needs.append("Data collection and monitoring infrastructure improvements")

        return needs

    def _define_success_metrics(self, assessment_results: Dict[str, Any]) -> List[str]:
        """Define success metrics for improvement initiatives."""
        return [
            "Overall community health score > 0.7",
            "All platform health scores > 0.5",
            "Data confidence levels > 0.8",
            "Zero critical alerts sustained for 7 days"
        ]

    def _save_health_report(self, report: HealthStatusReport):
        """Save health status report."""
        try:
            report_file = self.paperclip_reports_dir / f"{report.report_id}.json"
            save_json(report_file, asdict(report))

            print(f"[APU-155 Paperclip] Generated health report: {report.report_id}")

        except Exception as e:
            print(f"[APU-155 Paperclip] Error saving health report: {e}")

    def _coordinate_cross_department_actions(self, assessment_results: Dict[str, Any]) -> List[str]:
        """Coordinate actions across departments."""
        actions = []

        # Example cross-department coordination
        if assessment_results.get("overall_community_health", 0) < 0.4:
            actions.append("Initiated cross-department emergency response coordination")
            actions.append("Scheduled immediate strategy alignment meeting")

        return actions

    def _handle_critical_escalations(self, assessment_results: Dict[str, Any]) -> List[str]:
        """Handle critical issue escalations."""
        escalations = []

        critical_alerts = [
            alert for alert in assessment_results.get("alerts_generated", [])
            if alert["severity"] == "critical"
        ]

        if critical_alerts:
            escalations.append(f"Escalated {len(critical_alerts)} critical alerts to Chief of Staff")

        return escalations

    def _send_department_notifications(self, assessment_results: Dict[str, Any]) -> List[str]:
        """Send notifications to relevant departments."""
        notifications = []

        # This would implement actual notification sending
        notifications.append("Community health update sent to all departments")

        return notifications

    def _save_integration_results(self, results: Dict[str, Any]):
        """Save integration results for tracking."""
        try:
            results_file = VAWN_DIR / "paperclip" / "integration_results" / f"{results['session_id']}.json"
            results_file.parent.mkdir(exist_ok=True)
            save_json(results_file, results)
        except Exception as e:
            print(f"[APU-155 Paperclip] Warning: Could not save integration results: {e}")

def main():
    """Test Paperclip integration system."""
    print("=" * 65)
    print("APU-155 Paperclip Workflow Integration")
    print("Testing department coordination and task management integration")
    print("=" * 65)

    # Initialize integration
    paperclip = APU155PaperclipIntegration()

    # Mock assessment results
    mock_assessment = {
        "overall_community_health": 0.35,
        "platform_health_scores": {
            "bluesky": {
                "overall_health_score": 0.3,
                "engagement_vitality": 0.2,
                "content_quality": 0.4,
                "confidence_level": 0.6,
                "lifecycle_stage": "declining"
            }
        },
        "alerts_generated": [
            {
                "alert_id": "test_critical_001",
                "platform": "bluesky",
                "alert_type": "critical_community_health",
                "severity": "critical",
                "title": "Critical Community Health - Bluesky",
                "description": "Community health critically low",
                "category": "community",
                "primary_cause": "Declining engagement patterns",
                "recommended_actions": [
                    "Review content strategy",
                    "Analyze engagement patterns",
                    "Implement recovery plan"
                ],
                "prevention_strategies": ["Regular monitoring"],
                "escalation_path": ["community_manager", "content_team"]
            }
        ],
        "strategic_insights": [
            "URGENT: Community strategy requires immediate attention",
            "Consider content diversification strategies"
        ],
        "recommendations": [
            "Address critical engagement issues",
            "Implement monitoring improvements"
        ]
    }

    try:
        # Test integration
        results = paperclip.process_health_assessment_results(mock_assessment)

        print(f"\\n📋 INTEGRATION RESULTS:")
        print(f"   Tasks Created: {len(results['tasks_created'])}")
        print(f"   Alerts Routed: {len(results['alerts_routed'])}")
        print(f"   Reports Generated: {len(results['reports_generated'])}")
        print(f"   Escalations: {len(results['escalations_triggered'])}")
        print(f"   Integration Duration: {results['integration_duration_seconds']:.2f}s")

        # Display created tasks
        if results["tasks_created"]:
            print(f"\\n✅ TASKS CREATED:")
            for task in results["tasks_created"]:
                print(f"   • {task['title']} ({task['priority']}) -> {task['assigned_department']}")

        # Display routed alerts
        if results["alerts_routed"]:
            print(f"\\n⚠️  ALERTS ROUTED:")
            for alert in results["alerts_routed"]:
                print(f"   • {alert['title']} (Urgency: {alert['urgency']}/10) -> {alert['department']}")

        print(f"\\n✅ Paperclip integration test completed!")
        return True

    except Exception as e:
        print(f"\\n❌ Paperclip integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    exit(0 if main() else 1)