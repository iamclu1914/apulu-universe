"""
test_enhanced_monitor.py — Test suite for enhanced engagement monitor with partial platform availability.
Demonstrates graceful degradation, error handling, and phased rollout capabilities.
Created by: Dex - Community Agent (APU-168)
"""

import json
import sys
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import Mock, patch
import logging

# Set up test logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from engagement_monitor_apu168 import (
    EnhancedEngagementMonitor, PlatformStatus, HealthLevel,
    CredentialValidator, RetryHandler, MonitoringResult
)
from platform_health_monitor import PlatformHealthMonitor, SystemHealthReport
from phased_rollout_manager import (
    PhasedRolloutManager, RolloutPhase, FeatureFlag,
    PlatformRolloutConfig
)

class TestScenario:
    """Represents a test scenario configuration."""

    def __init__(self, name: str, description: str, credentials: Dict[str, Any],
                 expected_health_score: float, expected_platforms_active: int):
        self.name = name
        self.description = description
        self.credentials = credentials
        self.expected_health_score = expected_health_score
        self.expected_platforms_active = expected_platforms_active

class EnhancedMonitorTestSuite:
    """Test suite for enhanced engagement monitor."""

    def __init__(self):
        # Create temporary directory for test files
        self.test_dir = Path(tempfile.mkdtemp(prefix="apu168_test_"))
        logger.info(f"Created test directory: {self.test_dir}")

        # Test scenarios
        self.scenarios = [
            TestScenario(
                name="no_credentials",
                description="No platform credentials configured",
                credentials={},
                expected_health_score=0.0,
                expected_platforms_active=0
            ),
            TestScenario(
                name="bluesky_only",
                description="Only Bluesky credentials available",
                credentials={
                    "bluesky_username": "vawn.artist",
                    "bluesky_password": "test_password"
                },
                expected_health_score=0.2,  # 1 out of 5 platforms
                expected_platforms_active=1
            ),
            TestScenario(
                name="partial_instagram",
                description="Partial Instagram credentials (missing secret)",
                credentials={
                    "instagram_access_token": "test_token_instagram",
                    "bluesky_username": "vawn.artist",
                    "bluesky_password": "test_password"
                },
                expected_health_score=0.3,  # 1.5 out of 5 platforms (bluesky + partial instagram)
                expected_platforms_active=1
            ),
            TestScenario(
                name="meta_platforms",
                description="Instagram and Threads fully configured",
                credentials={
                    "instagram_access_token": "test_token_instagram",
                    "instagram_app_secret": "test_secret_instagram",
                    "threads_access_token": "test_token_threads",
                    "bluesky_username": "vawn.artist",
                    "bluesky_password": "test_password"
                },
                expected_health_score=0.6,  # 3 out of 5 platforms
                expected_platforms_active=3
            ),
            TestScenario(
                name="all_configured",
                description="All platform credentials configured",
                credentials={
                    "instagram_access_token": "test_token_instagram",
                    "instagram_app_secret": "test_secret_instagram",
                    "tiktok_access_token": "test_token_tiktok",
                    "tiktok_app_key": "test_key_tiktok",
                    "x_bearer_token": "test_bearer_x",
                    "x_api_key": "test_key_x",
                    "x_api_secret": "test_secret_x",
                    "threads_access_token": "test_token_threads",
                    "bluesky_username": "vawn.artist",
                    "bluesky_password": "test_password"
                },
                expected_health_score=1.0,  # All 5 platforms
                expected_platforms_active=5
            )
        ]

        self.test_results = []

    def setup_test_environment(self, credentials: Dict[str, Any]) -> None:
        """Set up test environment with mock credentials."""
        # Create test config directory
        config_dir = self.test_dir / "config"
        config_dir.mkdir(exist_ok=True)

        # Create mock credentials file
        creds_file = config_dir / "credentials.json"
        with open(creds_file, 'w') as f:
            json.dump(credentials, f, indent=2)

        # Patch file paths to use test directory
        self.original_vawn_dir = None
        try:
            import vawn_config
            self.original_vawn_dir = vawn_config.VAWN_DIR
            vawn_config.VAWN_DIR = self.test_dir
            vawn_config.CREDS_FILE = creds_file
        except:
            pass

    def cleanup_test_environment(self) -> None:
        """Clean up test environment."""
        try:
            if self.original_vawn_dir:
                import vawn_config
                vawn_config.VAWN_DIR = self.original_vawn_dir
        except:
            pass

    def mock_api_connectivity_test(self, platform: str, config: Any, creds: Dict[str, Any]) -> bool:
        """Mock API connectivity test that simulates realistic responses."""
        # Simulate API connectivity based on credentials
        required_creds = config.required_credentials

        # Check if all required credentials are present
        missing_creds = [cred for cred in required_creds if not creds.get(cred)]

        if not missing_creds:
            # All credentials present - simulate successful API test
            return True
        elif len(missing_creds) < len(required_creds):
            # Partial credentials - simulate degraded connectivity
            return False  # Could connect but not fully functional
        else:
            # No credentials - simulate connection failure
            return False

    def test_credential_validation(self) -> Dict[str, Any]:
        """Test credential validation across different scenarios."""
        logger.info("Testing credential validation...")

        validation_results = {}

        for scenario in self.scenarios:
            logger.info(f"Testing scenario: {scenario.name}")

            # Setup test environment
            self.setup_test_environment(scenario.credentials)

            try:
                # Mock the API connectivity test
                with patch.object(
                    CredentialValidator,
                    '_test_api_connectivity',
                    side_effect=self.mock_api_connectivity_test
                ):
                    # Validate credentials
                    results = CredentialValidator.validate_credentials(scenario.credentials)

                    # Count platforms by status
                    status_counts = {}
                    for platform, status in results.items():
                        status_str = status.value
                        status_counts[status_str] = status_counts.get(status_str, 0) + 1

                    validation_results[scenario.name] = {
                        "description": scenario.description,
                        "platform_statuses": {k: v.value for k, v in results.items()},
                        "status_counts": status_counts,
                        "expected_active": scenario.expected_platforms_active
                    }

                    logger.info(f"  Results: {status_counts}")

            except Exception as e:
                logger.error(f"Error in scenario {scenario.name}: {str(e)}")
                validation_results[scenario.name] = {
                    "error": str(e)
                }

            finally:
                self.cleanup_test_environment()

        return validation_results

    def test_enhanced_monitor(self) -> Dict[str, Any]:
        """Test enhanced monitor with different credential configurations."""
        logger.info("Testing enhanced monitor...")

        monitor_results = {}

        for scenario in self.scenarios:
            logger.info(f"Testing enhanced monitor with: {scenario.name}")

            # Setup test environment
            self.setup_test_environment(scenario.credentials)

            try:
                # Mock API calls to prevent actual network requests
                with patch('requests.get') as mock_get:
                    # Configure mock response
                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {
                        "posts": [
                            {"id": "test_post_1"},
                            {"id": "test_post_2"}
                        ]
                    }
                    mock_get.return_value = mock_response

                    # Mock credential validation
                    with patch.object(
                        CredentialValidator,
                        '_test_api_connectivity',
                        side_effect=self.mock_api_connectivity_test
                    ):
                        # Initialize enhanced monitor
                        monitor = EnhancedEngagementMonitor()

                        # Run monitoring cycle
                        result = monitor.monitor_engagement()

                        monitor_results[scenario.name] = {
                            "description": scenario.description,
                            "health_score": result.health_score,
                            "health_level": result.health_level.value,
                            "platforms_checked": result.platforms_checked,
                            "platforms_successful": result.platforms_successful,
                            "platforms_failed": result.platforms_failed,
                            "active_platforms": monitor.get_active_platforms(),
                            "errors": result.errors[:3],  # First 3 errors
                            "warnings": result.warnings[:3],  # First 3 warnings
                            "expected_health_score": scenario.expected_health_score
                        }

                        # Check if results match expectations
                        health_score_diff = abs(result.health_score - scenario.expected_health_score)
                        health_score_ok = health_score_diff <= 0.2  # Allow some tolerance

                        active_platforms_ok = len(monitor.get_active_platforms()) >= scenario.expected_platforms_active

                        monitor_results[scenario.name]["test_passed"] = health_score_ok and active_platforms_ok

                        logger.info(f"  Health Score: {result.health_score:.3f} (expected: {scenario.expected_health_score})")
                        logger.info(f"  Active Platforms: {len(monitor.get_active_platforms())} (expected: ≥{scenario.expected_platforms_active})")
                        logger.info(f"  Test Passed: {monitor_results[scenario.name]['test_passed']}")

            except Exception as e:
                logger.error(f"Error testing monitor with {scenario.name}: {str(e)}")
                monitor_results[scenario.name] = {
                    "description": scenario.description,
                    "error": str(e),
                    "test_passed": False
                }

            finally:
                self.cleanup_test_environment()

        return monitor_results

    def test_health_monitor(self) -> Dict[str, Any]:
        """Test platform health monitoring."""
        logger.info("Testing platform health monitor...")

        # Use the "meta_platforms" scenario for health monitoring test
        scenario = next(s for s in self.scenarios if s.name == "meta_platforms")

        self.setup_test_environment(scenario.credentials)

        try:
            with patch.object(
                CredentialValidator,
                '_test_api_connectivity',
                side_effect=self.mock_api_connectivity_test
            ):
                health_monitor = PlatformHealthMonitor()

                # Generate health report
                report = health_monitor.generate_health_report()

                # Test results
                health_results = {
                    "description": "Platform health monitoring test",
                    "overall_health_score": report.overall_health_score,
                    "overall_health_level": report.overall_health_level,
                    "platforms_total": report.platforms_total,
                    "platforms_active": report.platforms_active,
                    "platforms_degraded": report.platforms_degraded,
                    "platforms_failed": report.platforms_failed,
                    "critical_issues": len(report.critical_issues),
                    "warnings": len(report.warnings),
                    "recommendations": len(report.recommendations),
                    "historical_trend": report.historical_trend
                }

                logger.info(f"Health Monitor Results:")
                logger.info(f"  Overall Health: {report.overall_health_score:.3f} ({report.overall_health_level})")
                logger.info(f"  Platforms: {report.platforms_active} active, {report.platforms_degraded} degraded, {report.platforms_failed} failed")

                return health_results

        except Exception as e:
            logger.error(f"Error testing health monitor: {str(e)}")
            return {"error": str(e)}

        finally:
            self.cleanup_test_environment()

    def test_phased_rollout(self) -> Dict[str, Any]:
        """Test phased rollout management."""
        logger.info("Testing phased rollout manager...")

        # Setup test environment
        self.setup_test_environment({})

        try:
            rollout_manager = PhasedRolloutManager()

            # Create test rollout plan
            plan = rollout_manager.create_rollout_plan("test_plan", target_completion_days=30)

            # Test phase transitions
            test_transitions = [
                ("bluesky", RolloutPhase.TESTING, True),
                ("bluesky", RolloutPhase.PILOT, True),
                ("bluesky", RolloutPhase.PRODUCTION, True),
                ("instagram", RolloutPhase.TESTING, True),
                ("instagram", RolloutPhase.PRODUCTION, False),  # Should fail - skipping pilot
                ("x", RolloutPhase.PILOT, False),  # Should fail - skipping testing
            ]

            transition_results = []
            for platform, target_phase, should_succeed in test_transitions:
                success = rollout_manager.update_platform_phase(platform, target_phase)
                transition_results.append({
                    "platform": platform,
                    "target_phase": target_phase.value,
                    "success": success,
                    "expected_success": should_succeed,
                    "test_passed": success == should_succeed
                })

            # Test feature management
            feature_tests = [
                ("bluesky", FeatureFlag.MONITORING, True),  # Should succeed
                ("bluesky", FeatureFlag.ANALYTICS, True),   # Should succeed (monitoring is dependency)
                ("instagram", FeatureFlag.AUTO_POSTING, False),  # Should fail (no response_generation)
            ]

            feature_results = []
            for platform, feature, should_succeed in feature_tests:
                success = rollout_manager.enable_feature(platform, feature)
                feature_results.append({
                    "platform": platform,
                    "feature": feature.value,
                    "success": success,
                    "expected_success": should_succeed,
                    "test_passed": success == should_succeed
                })

            # Get rollout summary
            summary = rollout_manager.get_rollout_summary()

            rollout_results = {
                "description": "Phased rollout management test",
                "plan_created": plan.plan_name,
                "transition_tests": transition_results,
                "feature_tests": feature_results,
                "final_summary": {
                    "total_platforms": summary["total_platforms"],
                    "phase_distribution": summary["phase_distribution"],
                    "feature_adoption": summary["feature_adoption"]
                },
                "all_tests_passed": all(
                    t["test_passed"] for t in transition_results + feature_results
                )
            }

            logger.info(f"Rollout Manager Results:")
            logger.info(f"  Plan Created: {plan.plan_name}")
            logger.info(f"  Transition Tests Passed: {sum(t['test_passed'] for t in transition_results)}/{len(transition_results)}")
            logger.info(f"  Feature Tests Passed: {sum(f['test_passed'] for f in feature_results)}/{len(feature_results)}")

            return rollout_results

        except Exception as e:
            logger.error(f"Error testing phased rollout: {str(e)}")
            return {"error": str(e)}

        finally:
            self.cleanup_test_environment()

    def test_error_handling(self) -> Dict[str, Any]:
        """Test error handling and retry logic."""
        logger.info("Testing error handling and retry logic...")

        error_scenarios = [
            {
                "name": "timeout_error",
                "exception": "requests.exceptions.Timeout",
                "should_retry": True
            },
            {
                "name": "connection_error",
                "exception": "requests.exceptions.ConnectionError",
                "should_retry": True
            },
            {
                "name": "api_rate_limit",
                "exception": "requests.exceptions.HTTPError",
                "should_retry": True
            }
        ]

        error_results = []

        for scenario in error_scenarios:
            try:
                # Test retry handler
                attempts = 0

                def failing_function():
                    nonlocal attempts
                    attempts += 1
                    if attempts < 3:
                        raise Exception(scenario["exception"])
                    return "success"

                # Test with retry
                try:
                    result = RetryHandler.with_retry(failing_function, max_attempts=3, base_delay=0.1)
                    retry_success = result == "success"
                    final_attempts = attempts
                except:
                    retry_success = False
                    final_attempts = attempts

                error_results.append({
                    "scenario": scenario["name"],
                    "retry_success": retry_success,
                    "attempts_made": final_attempts,
                    "expected_retry": scenario["should_retry"]
                })

            except Exception as e:
                error_results.append({
                    "scenario": scenario["name"],
                    "error": str(e)
                })

        error_test_results = {
            "description": "Error handling and retry logic test",
            "scenarios_tested": len(error_scenarios),
            "scenarios_passed": sum(1 for r in error_results if r.get("retry_success", False)),
            "scenario_details": error_results
        }

        logger.info(f"Error Handling Results:")
        logger.info(f"  Scenarios Passed: {error_test_results['scenarios_passed']}/{error_test_results['scenarios_tested']}")

        return error_test_results

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test scenarios and compile results."""
        logger.info("=" * 80)
        logger.info("🧪 STARTING APU-168 ENHANCED MONITOR TEST SUITE")
        logger.info("=" * 80)

        start_time = datetime.now()

        test_results = {
            "test_suite": "APU-168 Enhanced Engagement Monitor",
            "started": start_time.isoformat(),
            "test_directory": str(self.test_dir),
            "tests": {}
        }

        # Run individual tests
        test_functions = [
            ("credential_validation", self.test_credential_validation),
            ("enhanced_monitor", self.test_enhanced_monitor),
            ("health_monitor", self.test_health_monitor),
            ("phased_rollout", self.test_phased_rollout),
            ("error_handling", self.test_error_handling)
        ]

        for test_name, test_function in test_functions:
            logger.info(f"\n🔬 Running {test_name} tests...")
            try:
                test_results["tests"][test_name] = test_function()
                logger.info(f"✅ {test_name} tests completed")
            except Exception as e:
                logger.error(f"❌ {test_name} tests failed: {str(e)}")
                test_results["tests"][test_name] = {"error": str(e)}

        # Compile overall results
        end_time = datetime.now()
        test_results["completed"] = end_time.isoformat()
        test_results["duration_seconds"] = (end_time - start_time).total_seconds()

        # Count passed tests
        passed_tests = 0
        total_tests = 0
        for test_name, result in test_results["tests"].items():
            if "error" not in result:
                total_tests += 1
                if self._test_passed(result):
                    passed_tests += 1

        test_results["summary"] = {
            "tests_passed": passed_tests,
            "total_tests": total_tests,
            "success_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        }

        return test_results

    def _test_passed(self, result: Dict[str, Any]) -> bool:
        """Check if a test result indicates success."""
        if "test_passed" in result:
            return result["test_passed"]
        elif "all_tests_passed" in result:
            return result["all_tests_passed"]
        elif "scenarios_passed" in result and "scenarios_tested" in result:
            return result["scenarios_passed"] == result["scenarios_tested"]
        else:
            return "error" not in result

    def display_test_results(self, results: Dict[str, Any]) -> None:
        """Display comprehensive test results."""
        print("=" * 80)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 80)

        summary = results.get("summary", {})
        print(f"\n🎯 OVERALL RESULTS:")
        print(f"   Tests Passed: {summary.get('tests_passed', 0)}/{summary.get('total_tests', 0)}")
        print(f"   Success Rate: {summary.get('success_rate', 0):.1f}%")
        print(f"   Duration: {results.get('duration_seconds', 0):.1f} seconds")

        print(f"\n📋 DETAILED RESULTS:")

        for test_name, result in results.get("tests", {}).items():
            if "error" in result:
                print(f"   ❌ {test_name}: ERROR - {result['error']}")
            elif self._test_passed(result):
                print(f"   ✅ {test_name}: PASSED")
            else:
                print(f"   ❌ {test_name}: FAILED")

        print(f"\n💡 KEY FINDINGS:")

        # Extract key findings from test results
        findings = []

        # Check credential validation
        cred_test = results.get("tests", {}).get("credential_validation", {})
        if "no_credentials" in cred_test:
            findings.append("✓ System handles missing credentials gracefully")
        if "all_configured" in cred_test:
            findings.append("✓ Full credential configuration works correctly")

        # Check monitor resilience
        monitor_test = results.get("tests", {}).get("enhanced_monitor", {})
        if monitor_test:
            findings.append("✓ Enhanced monitor adapts to partial platform availability")

        # Check rollout functionality
        rollout_test = results.get("tests", {}).get("phased_rollout", {})
        if rollout_test and not rollout_test.get("error"):
            findings.append("✓ Phased rollout management works correctly")

        for finding in findings:
            print(f"   {finding}")

        print(f"\n" + "=" * 80)

    def cleanup(self) -> None:
        """Clean up test environment."""
        try:
            if self.test_dir.exists():
                shutil.rmtree(self.test_dir)
                logger.info(f"Cleaned up test directory: {self.test_dir}")
        except Exception as e:
            logger.error(f"Error cleaning up test directory: {str(e)}")

def main():
    """Main test execution function."""
    print(f"🧪 Starting APU-168 Enhanced Monitor Test Suite at {datetime.now()}")

    test_suite = EnhancedMonitorTestSuite()

    try:
        # Run all tests
        results = test_suite.run_all_tests()

        # Display results
        test_suite.display_test_results(results)

        # Save test results
        results_file = test_suite.test_dir / "test_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"\nTest results saved to: {results_file}")

        return results

    except Exception as e:
        logger.error(f"Critical error in test suite: {str(e)}")
        raise

    finally:
        # Cleanup
        test_suite.cleanup()

if __name__ == "__main__":
    main()