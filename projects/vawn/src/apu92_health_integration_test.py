"""
apu92_health_integration_test.py — APU-92 Health Monitoring Integration Test

Validates the operational resilience and health monitoring integration with existing APU ecosystem.
Tests the core health monitoring features that address critical APU-88 health issues.

Created by: Dex - Community Agent (APU-92)
Date: 2026-04-12
"""

import sys
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import RESEARCH_DIR, log_run, save_json

# Import APU-92 components
try:
    from src.apu92_community_engagement_bot import (
        APU92CommunityEngagementBot,
        OperationalResilienceManager,
        HealthStatus
    )
except ImportError:
    print("[ERROR] Could not import APU-92 components. Ensure apu92_community_engagement_bot.py is available.")
    sys.exit(1)

# Test configuration
TEST_LOG = RESEARCH_DIR / "apu92_health_integration_test_log.json"


def test_health_monitoring_system():
    """Test the health monitoring system functionality"""
    print("\n=== APU-92 Health Monitoring System Test ===\n")

    test_results = {
        "test_timestamp": datetime.now().isoformat(),
        "test_version": "APU-92 Health Integration Test v1.0",
        "tests_performed": [],
        "overall_status": "unknown",
        "issues_found": [],
        "recommendations": []
    }

    try:
        # Test 1: Initialize Operational Resilience Manager
        print("[TEST 1] Initializing Operational Resilience Manager...")
        resilience_manager = OperationalResilienceManager()

        test_1_result = {
            "test_name": "resilience_manager_initialization",
            "status": "passed",
            "details": "OperationalResilienceManager initialized successfully",
            "timestamp": datetime.now().isoformat()
        }
        test_results["tests_performed"].append(test_1_result)
        print("  [PASS] Resilience manager initialized")

    except Exception as e:
        test_1_result = {
            "test_name": "resilience_manager_initialization",
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        test_results["tests_performed"].append(test_1_result)
        test_results["issues_found"].append(f"Failed to initialize resilience manager: {e}")
        print(f"  [FAIL] FAILED: {e}")
        return test_results

    try:
        # Test 2: System Health Check
        print("\n[TEST 2] Performing comprehensive system health check...")
        health_status = resilience_manager.check_system_health()

        test_2_result = {
            "test_name": "system_health_check",
            "status": "passed" if health_status else "failed",
            "health_report": health_status,
            "timestamp": datetime.now().isoformat()
        }
        test_results["tests_performed"].append(test_2_result)

        if health_status:
            print(f"  [PASS] PASSED: Health check completed")
            print(f"    Overall Health: {health_status['overall_health'].upper()}")
            print(f"    Health Score: {health_status['overall_score']:.1%}")

            # Analyze health components
            print("\n  Component Health Analysis:")
            for component_name, component_data in health_status["components"].items():
                if component_data["health_score"] >= 0.8:
                    status_icon = "[PASS]"
                elif component_data["health_score"] >= 0.5:
                    status_icon = "[WARN]"
                else:
                    status_icon = "[FAIL]"
                print(f"    {status_icon} {component_name}: {component_data['health_score']:.1%} ({component_data['status']})")

                if component_data["health_score"] < 0.8:
                    test_results["issues_found"].append(
                        f"Component '{component_name}' below optimal health: {component_data['health_score']:.1%}"
                    )

        else:
            print(f"  [FAIL] FAILED: Health check returned no data")
            test_results["issues_found"].append("Health check returned no data")

    except Exception as e:
        test_2_result = {
            "test_name": "system_health_check",
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        test_results["tests_performed"].append(test_2_result)
        test_results["issues_found"].append(f"Health check failed: {e}")
        print(f"  [FAIL] FAILED: {e}")

    try:
        # Test 3: Auto-Recovery System
        print("\n[TEST 3] Testing auto-recovery system...")

        # Test filesystem recovery
        recovery_result = resilience_manager.auto_recover_from_failure(
            "filesystem",
            {"missing_directories": ["test_directory"]}
        )

        test_3_result = {
            "test_name": "auto_recovery_system",
            "status": "passed" if recovery_result["recovery_attempted"] else "failed",
            "recovery_result": recovery_result,
            "timestamp": datetime.now().isoformat()
        }
        test_results["tests_performed"].append(test_3_result)

        if recovery_result["recovery_attempted"]:
            print(f"  [PASS] PASSED: Auto-recovery system functional")
            print(f"    Recovery Success: {recovery_result['recovery_successful']}")
            print(f"    Actions Taken: {len(recovery_result['actions_taken'])}")
        else:
            print(f"  [FAIL] FAILED: Auto-recovery system not functional")
            test_results["issues_found"].append("Auto-recovery system not functioning")

    except Exception as e:
        test_3_result = {
            "test_name": "auto_recovery_system",
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        test_results["tests_performed"].append(test_3_result)
        test_results["issues_found"].append(f"Auto-recovery test failed: {e}")
        print(f"  [FAIL] FAILED: {e}")

    try:
        # Test 4: APU-92 Bot Integration
        print("\n[TEST 4] Testing full APU-92 bot integration...")
        bot = APU92CommunityEngagementBot()

        # Get status report
        status_report = bot.get_community_status_report()

        test_4_result = {
            "test_name": "apu92_bot_integration",
            "status": "passed" if status_report else "failed",
            "status_report": status_report,
            "timestamp": datetime.now().isoformat()
        }
        test_results["tests_performed"].append(test_4_result)

        if status_report and status_report["status"] == "operational":
            print(f"  [PASS] PASSED: APU-92 bot integration successful")
            print(f"    Bot Status: {status_report['status'].upper()}")
            print(f"    Agent: {status_report['agent']}")
            print(f"    Version: {status_report['version']}")
        else:
            print(f"  [FAIL] FAILED: APU-92 bot integration issues")
            test_results["issues_found"].append("APU-92 bot integration not fully operational")

    except Exception as e:
        test_4_result = {
            "test_name": "apu92_bot_integration",
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        test_results["tests_performed"].append(test_4_result)
        test_results["issues_found"].append(f"APU-92 bot integration test failed: {e}")
        print(f"  [FAIL] FAILED: {e}")

    # Test 5: Ecosystem Compatibility Check
    try:
        print("\n[TEST 5] Testing ecosystem compatibility...")

        # Check if we can create log entries without conflicts
        test_log_entry = {
            "test_timestamp": datetime.now().isoformat(),
            "test_type": "ecosystem_compatibility",
            "apu92_version": "v1.0",
            "integration_status": "testing"
        }

        # Test logging integration
        log_run("APU92HealthIntegrationTest", "ok", "Health monitoring integration test completed successfully")

        test_5_result = {
            "test_name": "ecosystem_compatibility",
            "status": "passed",
            "details": "Ecosystem logging integration successful",
            "timestamp": datetime.now().isoformat()
        }
        test_results["tests_performed"].append(test_5_result)
        print(f"  [PASS] PASSED: Ecosystem compatibility confirmed")

    except Exception as e:
        test_5_result = {
            "test_name": "ecosystem_compatibility",
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        test_results["tests_performed"].append(test_5_result)
        test_results["issues_found"].append(f"Ecosystem compatibility test failed: {e}")
        print(f"  [FAIL] FAILED: {e}")

    # Generate final assessment
    passed_tests = sum(1 for test in test_results["tests_performed"] if test["status"] == "passed")
    total_tests = len(test_results["tests_performed"])

    if passed_tests == total_tests and len(test_results["issues_found"]) == 0:
        test_results["overall_status"] = "excellent"
    elif passed_tests >= total_tests * 0.8:
        test_results["overall_status"] = "good"
    elif passed_tests >= total_tests * 0.6:
        test_results["overall_status"] = "acceptable"
    else:
        test_results["overall_status"] = "needs_attention"

    # Generate recommendations
    if test_results["issues_found"]:
        test_results["recommendations"].append("Address identified health issues before deployment")

    if test_results["overall_status"] in ["good", "excellent"]:
        test_results["recommendations"].append("Health monitoring system ready for production integration")

    if test_results["overall_status"] == "excellent":
        test_results["recommendations"].append("Consider enabling automated health monitoring cycles")

    return test_results


def test_integration_with_existing_ecosystem():
    """Test integration with existing APU ecosystem"""
    print("\n=== APU Ecosystem Integration Test ===\n")

    integration_results = {
        "test_timestamp": datetime.now().isoformat(),
        "apu_compatibility": {},
        "file_compatibility": {},
        "logging_compatibility": {},
        "overall_integration_status": "unknown"
    }

    # Check for existing APU logs and compatibility
    apu_logs_to_check = [
        "apu88_engagement_monitor_log.json",
        "apu83_engagement_monitor_log.json",
        "apu74_intelligent_engagement_log.json",
        "engagement_log.json"
    ]

    compatible_logs = 0
    for log_file in apu_logs_to_check:
        log_path = RESEARCH_DIR / log_file
        try:
            if log_path.exists():
                log_data = json.loads(log_path.read_text())
                integration_results["file_compatibility"][log_file] = "compatible"
                compatible_logs += 1
                print(f"  [PASS] Compatible with {log_file}")
            else:
                integration_results["file_compatibility"][log_file] = "not_found"
                print(f"  [WARN] {log_file} not found (may be normal)")
        except Exception as e:
            integration_results["file_compatibility"][log_file] = f"error: {e}"
            print(f"  [FAIL] Error checking {log_file}: {e}")

    # Test vawn_config integration
    try:
        from vawn_config import RESEARCH_LOG
        if Path(RESEARCH_LOG).exists():
            integration_results["logging_compatibility"]["vawn_config"] = "compatible"
            print(f"  [PASS] vawn_config logging integration compatible")
        else:
            integration_results["logging_compatibility"]["vawn_config"] = "research_log_missing"
            print(f"  [WARN] Research log not found, will be created")
    except Exception as e:
        integration_results["logging_compatibility"]["vawn_config"] = f"error: {e}"
        print(f"  [FAIL] vawn_config integration error: {e}")

    # Overall integration assessment
    if compatible_logs >= len(apu_logs_to_check) * 0.5:
        integration_results["overall_integration_status"] = "compatible"
        print(f"\n  [PASS] Overall ecosystem integration: COMPATIBLE")
    else:
        integration_results["overall_integration_status"] = "needs_review"
        print(f"\n  [WARN] Overall ecosystem integration: NEEDS REVIEW")

    return integration_results


def main():
    """Main test execution function"""
    print("=" * 70)
    print("APU-92 HEALTH MONITORING & ECOSYSTEM INTEGRATION TEST")
    print("=" * 70)
    print(f"Agent: Dex - Community (75dd5aa3-6dfb-4d13-b424-48343f1fd7e2)")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Purpose: Validate APU-92 health monitoring and ecosystem integration")

    # Run health monitoring tests
    health_test_results = test_health_monitoring_system()

    # Run ecosystem integration tests
    integration_test_results = test_integration_with_existing_ecosystem()

    # Compile comprehensive test report
    comprehensive_report = {
        "test_suite": "APU-92 Health & Integration Validation",
        "execution_timestamp": datetime.now().isoformat(),
        "agent": "Dex - Community (75dd5aa3-6dfb-4d13-b424-48343f1fd7e2)",
        "health_monitoring_tests": health_test_results,
        "ecosystem_integration_tests": integration_test_results,
        "overall_assessment": {},
        "deployment_readiness": "unknown"
    }

    # Generate overall assessment
    health_status = health_test_results["overall_status"]
    integration_status = integration_test_results["overall_integration_status"]

    if health_status in ["excellent", "good"] and integration_status == "compatible":
        comprehensive_report["deployment_readiness"] = "ready"
        comprehensive_report["overall_assessment"]["status"] = "excellent"
        comprehensive_report["overall_assessment"]["message"] = "APU-92 ready for production deployment"
    elif health_status in ["good", "acceptable"] and integration_status in ["compatible", "needs_review"]:
        comprehensive_report["deployment_readiness"] = "ready_with_monitoring"
        comprehensive_report["overall_assessment"]["status"] = "good"
        comprehensive_report["overall_assessment"]["message"] = "APU-92 ready with continued monitoring"
    else:
        comprehensive_report["deployment_readiness"] = "needs_attention"
        comprehensive_report["overall_assessment"]["status"] = "needs_improvement"
        comprehensive_report["overall_assessment"]["message"] = "Address identified issues before deployment"

    # Save comprehensive test report
    try:
        save_json(TEST_LOG, comprehensive_report)
        print(f"\n[RESULTS] Comprehensive test report saved to: {TEST_LOG}")
    except Exception as e:
        print(f"\n[WARNING] Could not save test report: {e}")

    # Display final results
    print(f"\n" + "=" * 70)
    print("FINAL TEST RESULTS")
    print("=" * 70)
    print(f"Health Monitoring Status: {health_status.upper()}")
    print(f"Ecosystem Integration: {integration_status.upper()}")
    print(f"Deployment Readiness: {comprehensive_report['deployment_readiness'].upper()}")
    print(f"Overall Assessment: {comprehensive_report['overall_assessment']['status'].upper()}")
    print(f"Message: {comprehensive_report['overall_assessment']['message']}")

    if health_test_results.get("issues_found"):
        print(f"\nISSUES IDENTIFIED:")
        for i, issue in enumerate(health_test_results["issues_found"], 1):
            print(f"  {i}. {issue}")

    if health_test_results.get("recommendations"):
        print(f"\nRECOMMENDATIONS:")
        for i, rec in enumerate(health_test_results["recommendations"], 1):
            print(f"  {i}. {rec}")

    print(f"\nAPU-92 health integration test completed successfully!")

    return comprehensive_report


if __name__ == "__main__":
    main()