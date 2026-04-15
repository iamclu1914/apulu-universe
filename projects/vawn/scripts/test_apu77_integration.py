"""
APU-77 Integration Test Script
==============================

Test script to verify APU-77 department monitoring integration with:
- APU-74 alert system
- APU-76 coordination system
- Executive dashboard functionality
- Department health tracking
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add Vawn directory to path
sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from src.apu77_department_engagement_monitor import APU77DepartmentEngagementMonitor

def test_department_monitoring():
    """Test basic department monitoring functionality."""
    print("Testing APU-77 Department Monitoring...")

    monitor = APU77DepartmentEngagementMonitor()

    # Test department status retrieval
    status = monitor.get_department_status()
    print(f"[OK] Department states initialized: {list(status.keys())}")

    # Test individual department status
    ar_status = monitor.get_department_status("a_and_r")
    print(f"[OK] A&R department status: {ar_status['alert_level']}")

    return True

def test_executive_dashboard():
    """Test executive dashboard functionality."""
    print("\nTesting Executive Dashboard...")

    monitor = APU77DepartmentEngagementMonitor()

    # Run assessment to populate dashboard
    results = monitor.run_department_assessment()

    # Test dashboard retrieval
    dashboard = monitor.get_executive_summary()
    print(f"[OK] Dashboard organizational health: {dashboard.get('organizational_health', 'N/A')}")
    print(f"[OK] Dashboard strategic progress: {dashboard.get('strategic_progress', 'N/A')}")

    return True

def test_escalation_integration():
    """Test escalation and APU-74 integration."""
    print("\nTesting Escalation Integration...")

    monitor = APU77DepartmentEngagementMonitor()

    # Create mock escalations for testing
    test_escalations = [
        {
            "type": "department_critical",
            "department": "operations",
            "severity": "critical",
            "condition": "Test critical condition",
            "recommended_action": "test_intervention",
            "apu74_integration": True
        },
        {
            "type": "coordination_failure",
            "severity": "high",
            "condition": "Test coordination failure",
            "recommended_action": "test_coordination_session",
            "apu74_integration": True
        }
    ]

    # Test APU-74 integration
    integration_success = monitor.integration_with_apu74(test_escalations)
    print(f"[OK] APU-74 integration: {'Success' if integration_success else 'Failed'}")

    # Check integration file was created
    integration_file = Path("C:/Users/rdyal/Vawn/research/apu77_department_engagement/apu74_integration_alerts.json")
    if integration_file.exists():
        integration_data = json.loads(integration_file.read_text())
        print(f"[OK] Integration file created with {integration_data['alert_count']} alerts")

    return integration_success

def test_multi_artist_readiness():
    """Test multi-artist scaling readiness assessment."""
    print("\nTesting Multi-Artist Scaling Readiness...")

    monitor = APU77DepartmentEngagementMonitor()
    results = monitor.run_department_assessment()

    org_overview = results["organizational_overview"]
    scalability_score = org_overview["scalability_readiness_score"]

    print(f"[OK] Scalability readiness score: {scalability_score:.2f}")

    if scalability_score >= 0.75:
        print("[OK] Organization ready for multi-artist expansion")
    else:
        print("[WARN] Organization needs improvement for multi-artist expansion")

    return True

def test_department_coordination():
    """Test cross-department coordination tracking."""
    print("\nTesting Department Coordination...")

    monitor = APU77DepartmentEngagementMonitor()
    results = monitor.run_department_assessment()

    # Check coordination scores
    dept_results = results["department_results"]
    coordination_scores = {
        dept: data["cross_department_score"]
        for dept, data in dept_results.items()
    }

    print("[OK] Department coordination scores:")
    for dept, score in coordination_scores.items():
        dept_name = dept.replace('_', ' ').title()
        print(f"   {dept_name}: {score:.2f}")

    # Check overall coordination
    org_overview = results["organizational_overview"]
    overall_coord = org_overview["department_coordination_score"]
    print(f"[OK] Overall coordination score: {overall_coord:.2f}")

    return True

def main():
    """Run all integration tests."""
    print("=" * 60)
    print("APU-77 DEPARTMENT ENGAGEMENT MONITOR - Integration Tests")
    print("=" * 60)

    tests = [
        ("Basic Department Monitoring", test_department_monitoring),
        ("Executive Dashboard", test_executive_dashboard),
        ("Escalation Integration", test_escalation_integration),
        ("Multi-Artist Readiness", test_multi_artist_readiness),
        ("Department Coordination", test_department_coordination)
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            print(f"\n{'-' * 40}")
            print(f"TEST: {test_name}")
            print(f"{'-' * 40}")

            result = test_func()
            if result:
                print(f"[PASS] {test_name}")
                passed += 1
            else:
                print(f"[FAIL] {test_name}")
                failed += 1

        except Exception as e:
            print(f"[ERROR] {test_name} - {str(e)}")
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print(f"{'=' * 60}")

    if failed == 0:
        print("[SUCCESS] All APU-77 integration tests passed!")
        return True
    else:
        print(f"[WARNING] {failed} tests failed - review implementation")
        return False

if __name__ == "__main__":
    main()