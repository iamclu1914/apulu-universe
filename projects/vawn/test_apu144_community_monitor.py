#!/usr/bin/env python3
"""
Test Suite for APU-144 Community Engagement Monitor
Comprehensive testing of community monitoring functionality and Paperclip integration.

Created by: Dex - Community Agent (APU-144)
Purpose: Validate APU-144 system functionality and integration capabilities
"""

import sys
import json
import time
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent))

from vawn_config import VAWN_DIR, load_json, save_json

class APU144TestSuite:
    """Comprehensive test suite for APU-144 Community Engagement Monitor."""

    def __init__(self):
        self.test_session_id = f"test_apu144_{int(datetime.now().timestamp())}"
        self.test_results = []
        self.test_log = VAWN_DIR / "research" / "apu144_test_results.json"

    def log_test_result(self, test_name: str, status: str, details: Dict[str, Any] = None):
        """Log individual test results."""
        result = {
            "test_name": test_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.test_results.append(result)

        status_emoji = "[PASS]" if status == "PASS" else "[FAIL]" if status == "FAIL" else "[WARN]"
        print(f"{status_emoji} {test_name}: {status}")

        if details and status == "FAIL":
            print(f"   Details: {details}")

    def test_import_apu144_monitor(self) -> bool:
        """Test importing APU-144 community engagement monitor."""
        try:
            from src.apu144_community_engagement_monitor import APU144CommunityEngagementMonitor
            self.log_test_result("Import APU-144 Monitor", "PASS")
            return True
        except Exception as e:
            self.log_test_result("Import APU-144 Monitor", "FAIL", {"error": str(e)})
            return False

    def test_apu144_initialization(self) -> bool:
        """Test APU-144 monitor initialization."""
        try:
            from src.apu144_community_engagement_monitor import APU144CommunityEngagementMonitor
            monitor = APU144CommunityEngagementMonitor()

            # Check basic attributes
            if hasattr(monitor, 'session_id') and hasattr(monitor, 'platforms'):
                self.log_test_result("APU-144 Initialization", "PASS", {
                    "session_id": monitor.session_id,
                    "platforms": monitor.platforms
                })
                return True
            else:
                self.log_test_result("APU-144 Initialization", "FAIL",
                                   {"error": "Missing required attributes"})
                return False

        except Exception as e:
            self.log_test_result("APU-144 Initialization", "FAIL", {"error": str(e)})
            return False

    def test_community_health_assessment(self) -> bool:
        """Test community health assessment functionality."""
        try:
            from src.apu144_community_engagement_monitor import APU144CommunityEngagementMonitor
            monitor = APU144CommunityEngagementMonitor()

            # Test health assessment for a platform
            platform = "instagram"
            health_metrics = monitor.assess_community_health(platform)

            if hasattr(health_metrics, 'platform') and hasattr(health_metrics, 'sentiment_balance'):
                self.log_test_result("Community Health Assessment", "PASS", {
                    "platform": health_metrics.platform,
                    "sentiment_balance": health_metrics.sentiment_balance,
                    "conversation_depth": health_metrics.conversation_depth_score
                })
                return True
            else:
                self.log_test_result("Community Health Assessment", "FAIL",
                                   {"error": "Invalid health metrics structure"})
                return False

        except Exception as e:
            self.log_test_result("Community Health Assessment", "FAIL", {"error": str(e)})
            return False

    def test_engagement_quality_analysis(self) -> bool:
        """Test engagement quality analysis."""
        try:
            from src.apu144_community_engagement_monitor import APU144CommunityEngagementMonitor
            monitor = APU144CommunityEngagementMonitor()

            # Test engagement quality analysis
            platform = "tiktok"
            quality_metrics = monitor.analyze_engagement_quality(platform)

            if hasattr(quality_metrics, 'quality_ratio') and hasattr(quality_metrics, 'total_interactions'):
                self.log_test_result("Engagement Quality Analysis", "PASS", {
                    "platform": quality_metrics.platform,
                    "quality_ratio": quality_metrics.quality_ratio,
                    "total_interactions": quality_metrics.total_interactions
                })
                return True
            else:
                self.log_test_result("Engagement Quality Analysis", "FAIL",
                                   {"error": "Invalid quality metrics structure"})
                return False

        except Exception as e:
            self.log_test_result("Engagement Quality Analysis", "FAIL", {"error": str(e)})
            return False

    def test_community_health_scoring(self) -> bool:
        """Test community health score calculation."""
        try:
            from src.apu144_community_engagement_monitor import APU144CommunityEngagementMonitor, CommunityHealthMetrics
            monitor = APU144CommunityEngagementMonitor()

            # Create test metrics
            test_metrics = CommunityHealthMetrics(
                timestamp=datetime.now().isoformat(),
                platform="test",
                active_members=100,
                conversation_depth_score=0.7,
                sentiment_balance=0.5,
                engagement_authenticity=0.8,
                growth_sustainability=0.6,
                community_cohesion=0.75,
                moderator_effectiveness=0.9
            )

            # Calculate health score
            health_score = monitor.calculate_community_health_score(test_metrics)

            if isinstance(health_score, float) and 0 <= health_score <= 1:
                self.log_test_result("Community Health Scoring", "PASS", {
                    "health_score": health_score,
                    "test_metrics": {
                        "conversation_depth": test_metrics.conversation_depth_score,
                        "sentiment_balance": test_metrics.sentiment_balance
                    }
                })
                return True
            else:
                self.log_test_result("Community Health Scoring", "FAIL",
                                   {"error": f"Invalid health score: {health_score}"})
                return False

        except Exception as e:
            self.log_test_result("Community Health Scoring", "FAIL", {"error": str(e)})
            return False

    def test_alert_generation(self) -> bool:
        """Test community alert generation."""
        try:
            from src.apu144_community_engagement_monitor import (
                APU144CommunityEngagementMonitor, CommunityHealthMetrics, EngagementQualityMetrics
            )
            monitor = APU144CommunityEngagementMonitor()

            # Create test metrics that should trigger alerts
            health_metrics = CommunityHealthMetrics(
                timestamp=datetime.now().isoformat(),
                platform="test",
                active_members=50,
                conversation_depth_score=0.3,  # Low - should trigger alert
                sentiment_balance=-0.3,  # Negative - should trigger alert
                engagement_authenticity=0.4,
                growth_sustainability=0.4,  # Low - should trigger alert
                community_cohesion=0.5,
                moderator_effectiveness=0.7
            )

            quality_metrics = EngagementQualityMetrics(
                timestamp=datetime.now().isoformat(),
                platform="test",
                total_interactions=100,
                meaningful_conversations=20,
                superficial_interactions=80,
                quality_ratio=0.2,  # Low - should trigger alert
                average_response_time=300,
                conversation_persistence=0.3,
                cross_platform_threads=5
            )

            # Generate alerts
            alerts = monitor.generate_community_alerts(health_metrics, quality_metrics)

            if isinstance(alerts, list) and len(alerts) > 0:
                self.log_test_result("Alert Generation", "PASS", {
                    "alerts_generated": len(alerts),
                    "alert_types": [alert.category for alert in alerts],
                    "severities": [alert.severity for alert in alerts]
                })
                return True
            else:
                self.log_test_result("Alert Generation", "FAIL",
                                   {"error": "No alerts generated for problematic metrics"})
                return False

        except Exception as e:
            self.log_test_result("Alert Generation", "FAIL", {"error": str(e)})
            return False

    def test_database_operations(self) -> bool:
        """Test database initialization and operations."""
        try:
            from src.apu144_community_engagement_monitor import APU144CommunityEngagementMonitor
            monitor = APU144CommunityEngagementMonitor()

            # Check if database file was created
            if monitor.db_path.exists():
                self.log_test_result("Database Operations", "PASS", {
                    "database_path": str(monitor.db_path),
                    "file_size": monitor.db_path.stat().st_size
                })
                return True
            else:
                self.log_test_result("Database Operations", "FAIL",
                                   {"error": "Database file not created"})
                return False

        except Exception as e:
            self.log_test_result("Database Operations", "FAIL", {"error": str(e)})
            return False

    def test_monitoring_cycle(self) -> bool:
        """Test full monitoring cycle execution."""
        try:
            from src.apu144_community_engagement_monitor import APU144CommunityEngagementMonitor
            monitor = APU144CommunityEngagementMonitor()

            # Run monitoring cycle
            results = monitor.run_community_monitoring_cycle()

            # Validate results structure
            expected_keys = ["session_id", "cycle_timestamp", "platforms_monitored",
                           "overall_community_health", "alerts_generated"]

            if all(key in results for key in expected_keys):
                self.log_test_result("Monitoring Cycle", "PASS", {
                    "session_id": results["session_id"],
                    "platforms_monitored": len(results["platforms_monitored"]),
                    "cycle_duration": results.get("cycle_duration_seconds"),
                    "alerts_count": len(results["alerts_generated"])
                })
                return True
            else:
                missing_keys = [key for key in expected_keys if key not in results]
                self.log_test_result("Monitoring Cycle", "FAIL",
                                   {"error": f"Missing keys: {missing_keys}"})
                return False

        except Exception as e:
            self.log_test_result("Monitoring Cycle", "FAIL", {"error": str(e)})
            return False

    def test_paperclip_integration_import(self) -> bool:
        """Test importing Paperclip integration module."""
        try:
            from src.apu144_paperclip_integration import APU144PaperclipIntegration
            self.log_test_result("Import Paperclip Integration", "PASS")
            return True
        except Exception as e:
            self.log_test_result("Import Paperclip Integration", "FAIL", {"error": str(e)})
            return False

    def test_integration_initialization(self) -> bool:
        """Test Paperclip integration initialization."""
        try:
            from src.apu144_paperclip_integration import APU144PaperclipIntegration
            integration = APU144PaperclipIntegration()

            # Initialize integrations
            integrations = integration.initialize_integrations()

            if isinstance(integrations, dict):
                active_systems = [k for k, v in integrations.items() if v.status == "active"]
                self.log_test_result("Integration Initialization", "PASS", {
                    "total_systems": len(integrations),
                    "active_systems": len(active_systems),
                    "system_names": list(integrations.keys())
                })
                return True
            else:
                self.log_test_result("Integration Initialization", "FAIL",
                                   {"error": "Invalid integrations result"})
                return False

        except Exception as e:
            self.log_test_result("Integration Initialization", "FAIL", {"error": str(e)})
            return False

    def test_launcher_import(self) -> bool:
        """Test importing launcher script."""
        try:
            from scripts.apu144_community_monitor_launcher import APU144Launcher
            self.log_test_result("Import Launcher", "PASS")
            return True
        except Exception as e:
            self.log_test_result("Import Launcher", "FAIL", {"error": str(e)})
            return False

    def test_configuration_loading(self) -> bool:
        """Test configuration file loading."""
        try:
            config_file = VAWN_DIR / "config" / "apu144_community_engagement_config.json"
            if config_file.exists():
                config = load_json(config_file)
                if "monitor_info" in config and "monitoring_settings" in config:
                    self.log_test_result("Configuration Loading", "PASS", {
                        "config_file": str(config_file),
                        "monitor_name": config["monitor_info"].get("name"),
                        "version": config["monitor_info"].get("version")
                    })
                    return True
                else:
                    self.log_test_result("Configuration Loading", "FAIL",
                                       {"error": "Missing required config sections"})
                    return False
            else:
                self.log_test_result("Configuration Loading", "FAIL",
                                   {"error": "Configuration file not found"})
                return False

        except Exception as e:
            self.log_test_result("Configuration Loading", "FAIL", {"error": str(e)})
            return False

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all APU-144 tests and return summary."""
        print("TEST: Starting APU-144 Community Engagement Monitor Test Suite")
        print("=" * 65)

        test_start = datetime.now()

        # Define test methods
        test_methods = [
            self.test_import_apu144_monitor,
            self.test_apu144_initialization,
            self.test_community_health_assessment,
            self.test_engagement_quality_analysis,
            self.test_community_health_scoring,
            self.test_alert_generation,
            self.test_database_operations,
            self.test_monitoring_cycle,
            self.test_paperclip_integration_import,
            self.test_integration_initialization,
            self.test_launcher_import,
            self.test_configuration_loading
        ]

        # Run tests
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                test_name = test_method.__name__.replace("test_", "").replace("_", " ").title()
                self.log_test_result(test_name, "FAIL", {"error": f"Test execution failed: {e}"})

        # Calculate results
        test_end = datetime.now()
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])

        test_summary = {
            "test_session_id": self.test_session_id,
            "start_time": test_start.isoformat(),
            "end_time": test_end.isoformat(),
            "duration_seconds": (test_end - test_start).total_seconds(),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
            "test_results": self.test_results
        }

        # Display summary
        print(f"\n" + "=" * 65)
        print(f"COMPLETE: Test Suite Completed")
        print(f"STATS: Total Tests: {total_tests}")
        print(f"PASS: Passed: {passed_tests}")
        print(f"FAIL: Failed: {failed_tests}")
        print(f"RATE: Success Rate: {test_summary['success_rate']:.1%}")
        print(f"TIME: Duration: {test_summary['duration_seconds']:.2f} seconds")

        if failed_tests > 0:
            print(f"\nFAILED TESTS:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"   • {result['test_name']}")

        # Save results
        self._save_test_results(test_summary)

        return test_summary

    def _save_test_results(self, summary: Dict[str, Any]):
        """Save test results to file."""
        try:
            try:
                existing_results = load_json(self.test_log) or []
            except:
                existing_results = []
            existing_results.append(summary)
            save_json(self.test_log, existing_results[-20:])  # Keep last 20 test runs
            print(f"\n📝 Test results saved to: {self.test_log}")
        except Exception as e:
            print(f"WARNING: Could not save test results: {e}")

def main():
    """Main function for running APU-144 tests."""
    test_suite = APU144TestSuite()

    try:
        summary = test_suite.run_all_tests()

        # Exit with appropriate code
        if summary["success_rate"] == 1.0:
            print(f"\nSUCCESS: All tests passed! APU-144 is ready for deployment.")
            return True
        else:
            print(f"\nWARNING: Some tests failed. Please review and fix issues before deployment.")
            return False

    except Exception as e:
        print(f"\nERROR: Test suite execution failed: {e}")
        print(f"TRACE: Traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)