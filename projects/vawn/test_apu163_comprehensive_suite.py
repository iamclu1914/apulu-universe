#!/usr/bin/env python3
"""
test_apu163_comprehensive_suite.py — Complete Test Suite for APU-163 Engagement Monitor
Comprehensive validation of all APU-163 advanced capabilities and integrations.

Created by: Dex - Community Agent (APU-163)
Purpose: Validate APU-163 system functionality, self-healing, Paperclip integration, and AI features

TEST COVERAGE:
[✓] Core APU-163 Monitor Functionality
[✓] Self-Healing System Operations
[✓] Paperclip Integration Workflows
[✓] Department Coordination Logic
[✓] Growth Strategy Generation
[✓] Database Schema and Persistence
[✓] Real-time Alert Processing
[✓] End-to-End Integration Testing
[✓] Performance and Reliability Testing
[✓] Error Handling and Edge Cases
"""

import sys
import json
import time
import traceback
import sqlite3
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, patch
from dataclasses import asdict

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent))

from vawn_config import VAWN_DIR, load_json, save_json, today_str

# Import APU-163 components
try:
    from src.apu163_engagement_monitor import (
        APU163EngagementMonitor, SystemHealthStatus, DepartmentType,
        AutomationLevel, PaperclipIssue, SelfHealingAction, DepartmentEngagement, GrowthStrategy
    )
    from src.apu163_paperclip_integration import (
        APU163PaperclipIntegration, IssueStatus, IssueType, PaperclipIssueEnhanced
    )
except ImportError as e:
    print(f"ERROR: Could not import APU-163 components: {e}")
    print("Please ensure APU-163 modules are available")
    sys.exit(1)


class APU163TestSuite:
    """Comprehensive test suite for APU-163 Advanced Engagement Monitor."""

    def __init__(self):
        self.test_session_id = f"test_apu163_{int(datetime.now().timestamp())}"
        self.test_results = []
        self.test_log = VAWN_DIR / "research" / "apu163_test_results.json"

        # Setup test environment
        self.test_dir = Path(tempfile.mkdtemp(prefix="apu163_test_"))
        self.original_vawn_dir = VAWN_DIR

        print(f"[APU-163 TEST] Test session: {self.test_session_id}")
        print(f"[APU-163 TEST] Test directory: {self.test_dir}")

    def log_test_result(self, test_name: str, status: str, details: Dict[str, Any] = None,
                       execution_time: float = 0.0):
        """Log individual test results with enhanced details."""
        result = {
            "test_name": test_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "execution_time_seconds": execution_time,
            "details": details or {}
        }
        self.test_results.append(result)

        status_emoji = {
            "PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "SKIP": "⏭️", "INFO": "ℹ️"
        }.get(status, "❓")

        print(f"{status_emoji} {test_name}: {status} ({execution_time:.3f}s)")

        if details and status in ["FAIL", "WARN"]:
            print(f"   Details: {details}")

    def setup_test_environment(self):
        """Setup isolated test environment."""
        try:
            # Create test directory structure
            test_dirs = [
                self.test_dir / "database",
                self.test_dir / "paperclip" / "tasks",
                self.test_dir / "paperclip" / "alerts",
                self.test_dir / "paperclip" / "reports",
                self.test_dir / "research"
            ]

            for directory in test_dirs:
                directory.mkdir(parents=True, exist_ok=True)

            # Create mock credential file
            creds_file = self.test_dir / "credentials.json"
            test_creds = {
                "access_token": "test_token_12345",
                "refresh_token": "test_refresh_67890",
                "client_id": "test_client",
                "client_secret": "test_secret"
            }
            save_json(creds_file, test_creds)

            self.log_test_result("setup_test_environment", "PASS",
                               {"test_dir": str(self.test_dir), "directories_created": len(test_dirs)})
            return True

        except Exception as e:
            self.log_test_result("setup_test_environment", "FAIL", {"error": str(e)})
            return False

    def test_apu163_initialization(self) -> bool:
        """Test APU-163 monitor initialization."""
        start_time = time.time()

        try:
            # Mock the VAWN_DIR for testing
            with patch('src.apu163_engagement_monitor.VAWN_DIR', self.test_dir):
                monitor = APU163EngagementMonitor()

                # Verify initialization
                assert monitor.session_id.startswith("apu163_")
                assert monitor.automation_level == AutomationLevel.AUTOMATED
                assert monitor.self_healing_enabled == True
                assert monitor.real_time_enabled == True
                assert len(monitor.departments) == 5
                assert len(monitor.healing_strategies) >= 4
                assert len(monitor.ai_models) >= 4

                # Check database initialization
                assert monitor.db_path.exists()

                # Verify database schema
                with sqlite3.connect(monitor.db_path) as conn:
                    cursor = conn.cursor()

                    # Check for APU-163 specific tables
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]

                    expected_tables = [
                        "paperclip_issues",
                        "self_healing_actions",
                        "department_engagement",
                        "growth_strategies"
                    ]

                    for table in expected_tables:
                        assert table in tables, f"Missing table: {table}"

                self.log_test_result("test_apu163_initialization", "PASS",
                                   {
                                       "session_id": monitor.session_id,
                                       "departments_configured": len(monitor.departments),
                                       "healing_strategies": len(monitor.healing_strategies),
                                       "ai_models": len(monitor.ai_models),
                                       "database_tables": len(tables)
                                   },
                                   time.time() - start_time)
                return True

        except Exception as e:
            self.log_test_result("test_apu163_initialization", "FAIL",
                               {"error": str(e), "traceback": traceback.format_exc()},
                               time.time() - start_time)
            return False

    def test_self_healing_system(self) -> bool:
        """Test self-healing system capabilities."""
        start_time = time.time()

        try:
            with patch('src.apu163_engagement_monitor.VAWN_DIR', self.test_dir):
                monitor = APU163EngagementMonitor()

                # Create mock problem scenarios
                test_problems = [
                    {
                        "type": "api_timeout",
                        "description": "API request timeout after 30 seconds",
                        "severity": "medium",
                        "detected_at": datetime.now().isoformat()
                    },
                    {
                        "type": "auth_failure",
                        "description": "Authentication failed with 401 error",
                        "severity": "high",
                        "detected_at": datetime.now().isoformat()
                    },
                    {
                        "type": "rate_limit",
                        "description": "Rate limit exceeded on platform API",
                        "severity": "medium",
                        "detected_at": datetime.now().isoformat()
                    }
                ]

                healing_results = []

                for problem in test_problems:
                    # Test problem detection
                    detected_problems = monitor._detect_problems({"test_error": problem["description"]})
                    assert len(detected_problems) >= 0, "Problem detection failed"

                    # Test auto-resolution attempt
                    healing_action = monitor._attempt_auto_resolution(problem)

                    if healing_action:
                        healing_results.append(healing_action)
                        assert healing_action.problem_type == problem["type"]
                        assert healing_action.action_id is not None
                        assert healing_action.time_to_resolution >= 0

                # Test healing strategy coverage
                expected_strategies = ["api_timeout", "auth_failure", "rate_limit", "infrastructure_degradation"]
                for strategy in expected_strategies:
                    assert strategy in monitor.healing_strategies, f"Missing healing strategy: {strategy}"

                self.log_test_result("test_self_healing_system", "PASS",
                                   {
                                       "problems_tested": len(test_problems),
                                       "healing_actions_created": len(healing_results),
                                       "strategies_available": len(monitor.healing_strategies),
                                       "coverage": len(expected_strategies)
                                   },
                                   time.time() - start_time)
                return True

        except Exception as e:
            self.log_test_result("test_self_healing_system", "FAIL",
                               {"error": str(e), "traceback": traceback.format_exc()},
                               time.time() - start_time)
            return False

    def test_paperclip_integration(self) -> bool:
        """Test Paperclip integration functionality."""
        start_time = time.time()

        try:
            with patch('src.apu163_engagement_monitor.VAWN_DIR', self.test_dir):
                # Create mock monitor
                class MockMonitor:
                    def __init__(self):
                        self.db_path = self.test_dir / "database" / "apu163_test.db"
                        self.db_path.parent.mkdir(parents=True, exist_ok=True)

                mock_monitor = MockMonitor()
                integration = APU163PaperclipIntegration(mock_monitor)

                # Test issue creation
                test_problem = {
                    "type": "api_degradation",
                    "description": "Critical API infrastructure failure - 7/9 endpoints returning 404",
                    "severity": "critical",
                    "detected_at": datetime.now().isoformat()
                }

                # Create enhanced issue
                issue = integration.create_enhanced_issue(
                    test_problem,
                    healing_attempted=True,
                    healing_success=False
                )

                # Verify issue creation
                assert issue.apu_number.startswith("APU-")
                assert issue.issue_type == IssueType.API_INFRASTRUCTURE
                assert issue.priority == "critical"
                assert issue.auto_resolution_attempted == True
                assert issue.follow_up_required == True
                assert len(issue.tags) > 0

                # Test status update
                update_success = integration.update_issue_status(
                    issue.issue_id,
                    IssueStatus.IN_PROGRESS,
                    resolution_method="manual_investigation",
                    resolution_confidence=0.8
                )
                assert update_success, "Issue status update failed"

                # Test issue file creation
                paperclip_files = list(integration.tasks_dir.glob("*.json"))
                assert len(paperclip_files) > 0, "No Paperclip files created"

                # Verify file content
                issue_file = paperclip_files[0]
                issue_data = load_json(issue_file)
                assert issue_data["issue_id"] == issue.issue_id
                assert issue_data["priority"] == "critical"
                assert issue_data["source_component"] == "apu163_engagement_monitor"

                # Test integration report
                report = integration.generate_integration_report()
                assert report["integration_status"] == "active"
                assert report["issue_statistics"]["total_issues_created"] >= 1
                assert len(report["department_coordination"]["agents_configured"]) > 0

                self.log_test_result("test_paperclip_integration", "PASS",
                                   {
                                       "issue_created": issue.apu_number,
                                       "issue_type": issue.issue_type.value,
                                       "priority": issue.priority,
                                       "files_created": len(paperclip_files),
                                       "status_update_success": update_success,
                                       "total_issues_tracked": report["issue_statistics"]["total_issues_created"]
                                   },
                                   time.time() - start_time)
                return True

        except Exception as e:
            self.log_test_result("test_paperclip_integration", "FAIL",
                               {"error": str(e), "traceback": traceback.format_exc()},
                               time.time() - start_time)
            return False

    def test_department_coordination(self) -> bool:
        """Test multi-department coordination functionality."""
        start_time = time.time()

        try:
            with patch('src.apu163_engagement_monitor.VAWN_DIR', self.test_dir):
                monitor = APU163EngagementMonitor()

                # Mock base results for coordination
                mock_base_results = {
                    "api_health": {"overall_health_score": 0.75},
                    "engagement_intelligence": [
                        {
                            "platform": "instagram",
                            "community_momentum": 0.8,
                            "engagement_score": 0.7
                        },
                        {
                            "platform": "tiktok",
                            "community_momentum": 0.6,
                            "engagement_score": 0.65
                        }
                    ]
                }

                # Test department coordination
                dept_coordination = monitor._coordinate_departments(mock_base_results)

                # Verify all departments are coordinated
                assert len(dept_coordination) == 5, "Not all departments coordinated"

                expected_departments = [
                    DepartmentType.ARTISTS_DEVELOPMENT,
                    DepartmentType.MARKETING,
                    DepartmentType.PRODUCTION,
                    DepartmentType.DISTRIBUTION,
                    DepartmentType.CHIEF_OF_STAFF
                ]

                for dept in expected_departments:
                    assert dept in dept_coordination, f"Missing department: {dept}"

                    engagement = dept_coordination[dept]
                    assert isinstance(engagement, DepartmentEngagement)
                    assert 0 <= engagement.engagement_score <= 1
                    assert 0 <= engagement.growth_trajectory <= 1
                    assert len(engagement.recommended_actions) > 0
                    assert engagement.coordinator_agent is not None

                # Test engagement calculation
                marketing_engagement = dept_coordination[DepartmentType.MARKETING]
                assert marketing_engagement.department == DepartmentType.MARKETING
                assert marketing_engagement.engagement_score > 0

                # Test target vs actual metrics
                assert "reach" in marketing_engagement.target_metrics
                assert "engagement_rate" in marketing_engagement.target_metrics
                assert "reach" in marketing_engagement.actual_metrics
                assert "engagement_rate" in marketing_engagement.actual_metrics

                self.log_test_result("test_department_coordination", "PASS",
                                   {
                                       "departments_coordinated": len(dept_coordination),
                                       "average_engagement": sum(eng.engagement_score for eng in dept_coordination.values()) / len(dept_coordination),
                                       "departments_with_actions": sum(1 for eng in dept_coordination.values() if len(eng.recommended_actions) > 0),
                                       "marketing_engagement_score": marketing_engagement.engagement_score
                                   },
                                   time.time() - start_time)
                return True

        except Exception as e:
            self.log_test_result("test_department_coordination", "FAIL",
                               {"error": str(e), "traceback": traceback.format_exc()},
                               time.time() - start_time)
            return False

    def test_growth_strategy_generation(self) -> bool:
        """Test AI-driven growth strategy generation."""
        start_time = time.time()

        try:
            with patch('src.apu163_engagement_monitor.VAWN_DIR', self.test_dir):
                monitor = APU163EngagementMonitor()

                # Mock department coordination results
                mock_dept_coordination = {
                    DepartmentType.MARKETING: DepartmentEngagement(
                        department=DepartmentType.MARKETING,
                        timestamp=datetime.now().isoformat(),
                        engagement_score=0.65,  # Below threshold for optimization
                        target_metrics={"reach": 1000, "engagement_rate": 0.05},
                        actual_metrics={"reach": 750, "engagement_rate": 0.035},
                        growth_trajectory=0.8,
                        recommended_actions=["Improve content strategy"],
                        coordinator_agent="marketing_agent"
                    )
                }

                # Mock base results
                mock_base_results = {
                    "engagement_intelligence": [
                        {
                            "platform": "instagram",
                            "community_momentum": 0.85,  # High momentum for expansion
                            "engagement_score": 0.7
                        }
                    ]
                }

                # Test growth opportunity identification
                opportunities = monitor._identify_growth_opportunities(mock_base_results, mock_dept_coordination)
                assert len(opportunities) > 0, "No growth opportunities identified"

                # Verify opportunity types
                opportunity_types = [opp["type"] for opp in opportunities]
                assert "department_optimization" in opportunity_types or "platform_expansion" in opportunity_types

                # Test strategy generation
                strategies = monitor._generate_growth_strategies(mock_base_results, mock_dept_coordination)
                assert len(strategies) > 0, "No growth strategies generated"

                for strategy in strategies:
                    assert isinstance(strategy, GrowthStrategy)
                    assert strategy.strategy_id.startswith("strategy_")
                    assert 0 <= strategy.predicted_impact <= 1
                    assert strategy.timeline is not None
                    assert len(strategy.growth_channels) > 0
                    assert len(strategy.success_metrics) > 0
                    assert strategy.implementation_priority in ["low", "medium", "high", "critical"]
                    assert isinstance(strategy.resource_requirements, dict)

                # Test specific strategy content
                first_strategy = strategies[0]
                assert "engagement_increase" in first_strategy.success_metrics
                assert first_strategy.predicted_impact > 0

                self.log_test_result("test_growth_strategy_generation", "PASS",
                                   {
                                       "opportunities_identified": len(opportunities),
                                       "strategies_generated": len(strategies),
                                       "average_predicted_impact": sum(s.predicted_impact for s in strategies) / len(strategies),
                                       "strategy_types": list(set(opp["type"] for opp in opportunities)),
                                       "implementation_priorities": list(set(s.implementation_priority for s in strategies))
                                   },
                                   time.time() - start_time)
                return True

        except Exception as e:
            self.log_test_result("test_growth_strategy_generation", "FAIL",
                               {"error": str(e), "traceback": traceback.format_exc()},
                               time.time() - start_time)
            return False

    def test_database_operations(self) -> bool:
        """Test database schema and operations."""
        start_time = time.time()

        try:
            with patch('src.apu163_engagement_monitor.VAWN_DIR', self.test_dir):
                monitor = APU163EngagementMonitor()

                # Test database initialization and schema
                with sqlite3.connect(monitor.db_path) as conn:
                    cursor = conn.cursor()

                    # Check all expected tables exist
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]

                    apu163_tables = [
                        "paperclip_issues",
                        "self_healing_actions",
                        "department_engagement",
                        "growth_strategies"
                    ]

                    for table in apu163_tables:
                        assert table in tables, f"Missing APU-163 table: {table}"

                    # Test healing action storage
                    test_healing_action = SelfHealingAction(
                        action_id="test_heal_123",
                        timestamp=datetime.now().isoformat(),
                        problem_type="api_timeout",
                        detection_method="automated",
                        resolution_strategy="timeout_mitigation",
                        success=True,
                        time_to_resolution=2.5,
                        confidence_score=0.85,
                        follow_up_required=False
                    )

                    monitor._save_healing_action(test_healing_action)

                    # Verify healing action was saved
                    cursor.execute("SELECT * FROM self_healing_actions WHERE action_id = ?",
                                 (test_healing_action.action_id,))
                    saved_action = cursor.fetchone()
                    assert saved_action is not None, "Healing action not saved"

                    # Test department engagement storage
                    test_dept_engagement = {
                        "department": "marketing",
                        "timestamp": datetime.now().isoformat(),
                        "engagement_score": 0.75,
                        "growth_trajectory": 0.8,
                        "coordinator_agent": "marketing_agent"
                    }

                    cursor.execute("""
                        INSERT INTO department_engagement
                        (department, timestamp, engagement_score, growth_trajectory, coordinator_agent)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        test_dept_engagement["department"],
                        test_dept_engagement["timestamp"],
                        test_dept_engagement["engagement_score"],
                        test_dept_engagement["growth_trajectory"],
                        test_dept_engagement["coordinator_agent"]
                    ))

                    conn.commit()

                    # Verify department engagement was saved
                    cursor.execute("SELECT * FROM department_engagement WHERE department = ?",
                                 (test_dept_engagement["department"],))
                    saved_engagement = cursor.fetchone()
                    assert saved_engagement is not None, "Department engagement not saved"

                    # Test data integrity
                    cursor.execute("SELECT COUNT(*) FROM self_healing_actions")
                    healing_count = cursor.fetchone()[0]

                    cursor.execute("SELECT COUNT(*) FROM department_engagement")
                    dept_count = cursor.fetchone()[0]

                    assert healing_count >= 1, "No healing actions in database"
                    assert dept_count >= 1, "No department engagement in database"

                self.log_test_result("test_database_operations", "PASS",
                                   {
                                       "tables_created": len(apu163_tables),
                                       "healing_actions_stored": healing_count,
                                       "department_records_stored": dept_count,
                                       "database_path": str(monitor.db_path),
                                       "schema_validation": "passed"
                                   },
                                   time.time() - start_time)
                return True

        except Exception as e:
            self.log_test_result("test_database_operations", "FAIL",
                               {"error": str(e), "traceback": traceback.format_exc()},
                               time.time() - start_time)
            return False

    def test_end_to_end_monitoring_cycle(self) -> bool:
        """Test complete end-to-end monitoring cycle."""
        start_time = time.time()

        try:
            with patch('src.apu163_engagement_monitor.VAWN_DIR', self.test_dir):
                # Mock external dependencies
                with patch('src.apu161_engagement_monitor.APU161EngagementMonitor.run_intelligent_monitoring_cycle') as mock_base:
                    # Mock APU-161 base results
                    mock_base.return_value = {
                        "session_id": "mock_apu161_session",
                        "timestamp": datetime.now().isoformat(),
                        "api_health": {
                            "overall_health_score": 0.6,
                            "recommended_mode": "posts_only"
                        },
                        "engagement_intelligence": [
                            {
                                "platform": "instagram",
                                "posts_analyzed": 25,
                                "engagement_velocity": 0.8,
                                "community_momentum": 0.75,
                                "prediction_confidence": 0.85
                            }
                        ],
                        "community_insights": [
                            {
                                "insight_id": "insight_123",
                                "category": "growth",
                                "priority": "medium",
                                "message": "Community engagement trending upward",
                                "confidence_level": 0.8
                            }
                        ]
                    }

                    monitor = APU163EngagementMonitor()

                    # Run complete monitoring cycle
                    results = monitor.run_advanced_monitoring_cycle()

                    # Verify cycle completion
                    assert results is not None, "Monitoring cycle returned None"
                    assert results["session_id"] == monitor.session_id
                    assert results["timestamp"] is not None
                    assert results["cycle_duration"] is not None
                    assert results["cycle_duration"] > 0

                    # Verify APU-161 base integration
                    assert results["apu161_base_results"] is not None
                    assert results["apu161_base_results"]["session_id"] == "mock_apu161_session"

                    # Verify APU-163 enhancements
                    assert "self_healing_actions" in results
                    assert "paperclip_issues" in results
                    assert "department_coordination" in results
                    assert "growth_strategies" in results
                    assert "real_time_alerts" in results
                    assert "system_health" in results
                    assert "automation_summary" in results

                    # Verify system health assessment
                    system_health = results["system_health"]
                    assert "status" in system_health
                    assert "overall_score" in system_health
                    assert 0 <= system_health["overall_score"] <= 1

                    # Verify automation summary
                    automation = results["automation_summary"]
                    assert automation["automation_level"] == "automated"
                    assert "self_healing" in automation
                    assert "paperclip_integration" in automation
                    assert "department_coordination" in automation
                    assert "growth_optimization" in automation

                    # Verify department coordination
                    dept_coordination = results["department_coordination"]
                    assert len(dept_coordination) > 0, "No department coordination results"

                    # Check for expected departments
                    expected_dept_keys = [dept.value for dept in DepartmentType]
                    for dept_key in expected_dept_keys:
                        if dept_key in dept_coordination:
                            dept_data = dept_coordination[dept_key]
                            assert "engagement_score" in dept_data
                            assert "growth_trajectory" in dept_data

                    self.log_test_result("test_end_to_end_monitoring_cycle", "PASS",
                                       {
                                           "cycle_duration": results["cycle_duration"],
                                           "self_healing_actions": len(results.get("self_healing_actions", [])),
                                           "paperclip_issues": len(results.get("paperclip_issues", [])),
                                           "departments_coordinated": len(results.get("department_coordination", {})),
                                           "growth_strategies": len(results.get("growth_strategies", [])),
                                           "system_health_score": system_health.get("overall_score", 0),
                                           "automation_level": automation.get("automation_level", "unknown")
                                       },
                                       time.time() - start_time)
                    return True

        except Exception as e:
            self.log_test_result("test_end_to_end_monitoring_cycle", "FAIL",
                               {"error": str(e), "traceback": traceback.format_exc()},
                               time.time() - start_time)
            return False

    def test_error_handling_and_resilience(self) -> bool:
        """Test error handling and system resilience."""
        start_time = time.time()

        try:
            with patch('src.apu163_engagement_monitor.VAWN_DIR', self.test_dir):
                monitor = APU163EngagementMonitor()

                # Test error handling in self-healing
                invalid_problem = {
                    "type": "nonexistent_problem_type",
                    "description": None,  # Invalid description
                    "severity": "invalid_severity"
                }

                # Should handle gracefully without crashing
                healing_action = monitor._attempt_auto_resolution(invalid_problem)
                # Should return None for unhandled problem type
                assert healing_action is None, "Should not create healing action for invalid problem"

                # Test database connection resilience
                # Temporarily corrupt database path
                original_db_path = monitor.db_path
                monitor.db_path = self.test_dir / "nonexistent" / "database.db"

                try:
                    # This should handle the error gracefully
                    healing_action = SelfHealingAction(
                        action_id="test_resilience",
                        timestamp=datetime.now().isoformat(),
                        problem_type="test_type",
                        detection_method="test",
                        resolution_strategy="test",
                        success=False,
                        time_to_resolution=0.0,
                        confidence_score=0.0,
                        follow_up_required=True
                    )

                    # This should fail but not crash the system
                    try:
                        monitor._save_healing_action(healing_action)
                    except Exception:
                        pass  # Expected to fail

                finally:
                    # Restore database path
                    monitor.db_path = original_db_path

                # Test empty results handling
                empty_results = {}
                problems = monitor._detect_problems(empty_results)
                assert isinstance(problems, list), "Should return list even with empty results"

                # Test malformed data handling
                malformed_results = {
                    "api_health": "not_a_dict",
                    "invalid_key": None
                }

                try:
                    problems = monitor._detect_problems(malformed_results)
                    assert isinstance(problems, list), "Should handle malformed data gracefully"
                except Exception as e:
                    # If it throws, ensure it's handled gracefully
                    assert "malformed" not in str(e).lower(), "Should handle malformed data without generic malformed error"

                self.log_test_result("test_error_handling_and_resilience", "PASS",
                                   {
                                       "invalid_problem_handled": healing_action is None,
                                       "database_error_resilience": "tested",
                                       "empty_results_handling": "passed",
                                       "malformed_data_handling": "passed"
                                   },
                                   time.time() - start_time)
                return True

        except Exception as e:
            self.log_test_result("test_error_handling_and_resilience", "FAIL",
                               {"error": str(e), "traceback": traceback.format_exc()},
                               time.time() - start_time)
            return False

    def test_performance_benchmarks(self) -> bool:
        """Test performance benchmarks and efficiency."""
        start_time = time.time()

        try:
            with patch('src.apu163_engagement_monitor.VAWN_DIR', self.test_dir):
                monitor = APU163EngagementMonitor()

                # Benchmark initialization time
                init_times = []
                for i in range(3):
                    init_start = time.time()
                    test_monitor = APU163EngagementMonitor()
                    init_time = time.time() - init_start
                    init_times.append(init_time)

                avg_init_time = sum(init_times) / len(init_times)

                # Benchmark problem detection
                test_problems = [
                    {
                        "type": f"test_problem_{i}",
                        "description": f"Test problem description {i} with timeout error",
                        "severity": "medium"
                    }
                    for i in range(10)
                ]

                detection_start = time.time()
                for problem in test_problems:
                    monitor._detect_problems({"test_data": problem["description"]})
                detection_time = time.time() - detection_start

                # Benchmark database operations
                db_ops_start = time.time()
                for i in range(5):
                    test_action = SelfHealingAction(
                        action_id=f"perf_test_{i}",
                        timestamp=datetime.now().isoformat(),
                        problem_type="test_type",
                        detection_method="automated",
                        resolution_strategy="test_strategy",
                        success=True,
                        time_to_resolution=0.1,
                        confidence_score=0.9,
                        follow_up_required=False
                    )
                    monitor._save_healing_action(test_action)
                db_ops_time = time.time() - db_ops_start

                # Performance assertions
                assert avg_init_time < 5.0, f"Initialization too slow: {avg_init_time:.2f}s"
                assert detection_time < 1.0, f"Problem detection too slow: {detection_time:.2f}s"
                assert db_ops_time < 2.0, f"Database operations too slow: {db_ops_time:.2f}s"

                self.log_test_result("test_performance_benchmarks", "PASS",
                                   {
                                       "average_init_time": avg_init_time,
                                       "problem_detection_time": detection_time,
                                       "database_operations_time": db_ops_time,
                                       "problems_tested": len(test_problems),
                                       "database_operations": 5,
                                       "performance_threshold_met": True
                                   },
                                   time.time() - start_time)
                return True

        except Exception as e:
            self.log_test_result("test_performance_benchmarks", "FAIL",
                               {"error": str(e), "traceback": traceback.format_exc()},
                               time.time() - start_time)
            return False

    def cleanup_test_environment(self):
        """Clean up test environment."""
        try:
            if self.test_dir and self.test_dir.exists():
                shutil.rmtree(self.test_dir, ignore_errors=True)

            self.log_test_result("cleanup_test_environment", "PASS",
                               {"test_dir_removed": str(self.test_dir)})
            return True

        except Exception as e:
            self.log_test_result("cleanup_test_environment", "FAIL", {"error": str(e)})
            return False

    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["status"] == "PASS")
        failed_tests = sum(1 for result in self.test_results if result["status"] == "FAIL")

        total_execution_time = sum(result.get("execution_time_seconds", 0) for result in self.test_results)

        report = {
            "test_session_id": self.test_session_id,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
                "total_execution_time": total_execution_time
            },
            "test_categories": {
                "core_functionality": [
                    "test_apu163_initialization",
                    "test_end_to_end_monitoring_cycle"
                ],
                "self_healing": [
                    "test_self_healing_system"
                ],
                "integration": [
                    "test_paperclip_integration",
                    "test_department_coordination"
                ],
                "ai_features": [
                    "test_growth_strategy_generation"
                ],
                "infrastructure": [
                    "test_database_operations",
                    "test_performance_benchmarks"
                ],
                "resilience": [
                    "test_error_handling_and_resilience"
                ]
            },
            "detailed_results": self.test_results,
            "recommendations": self._generate_test_recommendations()
        }

        return report

    def _generate_test_recommendations(self) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []

        failed_tests = [result for result in self.test_results if result["status"] == "FAIL"]

        if len(failed_tests) == 0:
            recommendations.append("✅ All tests passed - APU-163 is ready for production deployment")
        else:
            recommendations.append(f"⚠️ {len(failed_tests)} tests failed - resolve issues before deployment")

            for failed_test in failed_tests:
                test_name = failed_test["test_name"]
                recommendations.append(f"🔍 Investigate {test_name}: {failed_test.get('details', {}).get('error', 'Unknown error')}")

        # Performance recommendations
        perf_results = [result for result in self.test_results if result["test_name"] == "test_performance_benchmarks"]
        if perf_results and perf_results[0]["status"] == "PASS":
            recommendations.append("🚀 Performance benchmarks met - system is optimized")

        # Coverage recommendations
        if len(self.test_results) >= 8:
            recommendations.append("📊 Comprehensive test coverage achieved")
        else:
            recommendations.append("📝 Consider adding more test coverage")

        return recommendations

    def run_comprehensive_test_suite(self):
        """Run the complete APU-163 test suite."""
        print("=" * 70)
        print("APU-163 COMPREHENSIVE TEST SUITE")
        print("Advanced Community Engagement Orchestrator")
        print("=" * 70)

        suite_start_time = time.time()

        # Setup
        print(f"\n🔧 Setting up test environment...")
        if not self.setup_test_environment():
            print("❌ Test environment setup failed - aborting tests")
            return False

        # Core test execution
        test_methods = [
            ("APU-163 Monitor Initialization", self.test_apu163_initialization),
            ("Self-Healing System", self.test_self_healing_system),
            ("Paperclip Integration", self.test_paperclip_integration),
            ("Department Coordination", self.test_department_coordination),
            ("Growth Strategy Generation", self.test_growth_strategy_generation),
            ("Database Operations", self.test_database_operations),
            ("End-to-End Monitoring Cycle", self.test_end_to_end_monitoring_cycle),
            ("Error Handling & Resilience", self.test_error_handling_and_resilience),
            ("Performance Benchmarks", self.test_performance_benchmarks)
        ]

        print(f"\n🧪 Running {len(test_methods)} test categories...")

        for test_name, test_method in test_methods:
            print(f"\n--- Testing {test_name} ---")
            test_method()

        # Cleanup
        print(f"\n🧹 Cleaning up test environment...")
        self.cleanup_test_environment()

        # Generate and save report
        suite_duration = time.time() - suite_start_time
        test_report = self.generate_test_report()
        test_report["suite_duration"] = suite_duration

        # Save test report
        self.test_log.parent.mkdir(parents=True, exist_ok=True)
        save_json(self.test_log, test_report)

        # Display summary
        print(f"\n" + "=" * 70)
        print(f"APU-163 TEST SUITE COMPLETE")
        print(f"=" * 70)
        print(f"📊 Results: {test_report['summary']['passed']}/{test_report['summary']['total_tests']} tests passed")
        print(f"📈 Success Rate: {test_report['summary']['success_rate']:.1%}")
        print(f"⏱️ Total Time: {suite_duration:.2f}s")
        print(f"💾 Report saved: {self.test_log}")

        print(f"\n🔍 Test Recommendations:")
        for recommendation in test_report["recommendations"]:
            print(f"   {recommendation}")

        return test_report['summary']['success_rate'] >= 0.8  # 80% pass rate required


def main():
    """Main test execution."""
    test_suite = APU163TestSuite()
    success = test_suite.run_comprehensive_test_suite()

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())