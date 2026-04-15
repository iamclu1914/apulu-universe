"""
apu141_api_diagnostics.py — APU-141 API Health Diagnostics
Diagnose API connectivity and endpoint health issues identified in APU-120.
Created by: Dex - Community Agent (APU-141)
"""

import json
import requests
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys

# Add parent directory to path for vawn_config
sys.path.insert(0, str(Path(__file__).parent.parent))
from vawn_config import load_json, save_json, VAWN_DIR, CREDS_FILE

# APU-141 diagnostic results
DIAGNOSTICS_LOG = VAWN_DIR / "research" / "apu141_api_diagnostics.json"

def test_api_endpoint(url: str, headers: Dict[str, str], endpoint_name: str) -> Dict[str, Any]:
    """Test specific API endpoint and return detailed results."""
    test_result = {
        "endpoint": endpoint_name,
        "url": url,
        "timestamp": datetime.now().isoformat(),
        "status": "unknown",
        "response_code": None,
        "response_time_ms": None,
        "error": None,
        "response_data": None
    }

    try:
        start_time = time.time()
        response = requests.get(url, headers=headers, timeout=30)
        end_time = time.time()

        test_result["response_code"] = response.status_code
        test_result["response_time_ms"] = int((end_time - start_time) * 1000)

        if response.status_code == 200:
            test_result["status"] = "healthy"
            try:
                test_result["response_data"] = response.json()
            except:
                test_result["response_data"] = {"raw": response.text[:200]}
        elif response.status_code == 404:
            test_result["status"] = "endpoint_not_found"
            test_result["error"] = "Endpoint returns 404 - not implemented or incorrect URL"
        elif response.status_code == 401:
            test_result["status"] = "auth_failed"
            test_result["error"] = "Authentication failed - token may be expired"
        elif response.status_code == 403:
            test_result["status"] = "forbidden"
            test_result["error"] = "Access forbidden - insufficient permissions"
        else:
            test_result["status"] = "error"
            test_result["error"] = f"HTTP {response.status_code}: {response.text[:100]}"

    except requests.exceptions.Timeout:
        test_result["status"] = "timeout"
        test_result["error"] = "Request timeout after 30 seconds"
    except requests.exceptions.ConnectionError:
        test_result["status"] = "connection_error"
        test_result["error"] = "Failed to connect to server"
    except Exception as e:
        test_result["status"] = "exception"
        test_result["error"] = str(e)

    return test_result

def run_comprehensive_api_diagnostics() -> Dict[str, Any]:
    """Run comprehensive API diagnostics on all engagement-related endpoints."""
    print(f"[APU-141] Starting comprehensive API diagnostics at {datetime.now()}")

    # Load credentials
    try:
        creds = load_json(CREDS_FILE)
        base_url = creds.get("base_url", "")
        access_token = creds.get("access_token", "")

        if not base_url or not access_token:
            return {
                "error": "Missing base_url or access_token in credentials",
                "timestamp": datetime.now().isoformat()
            }

    except Exception as e:
        return {
            "error": f"Failed to load credentials: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

    headers = {"Authorization": f"Bearer {access_token}"}

    # Define endpoints to test based on APU-120 analysis and current monitor code
    endpoints_to_test = [
        # Core API health
        ("API Health Check", f"{base_url}/health"),
        ("API Status", f"{base_url}/status"),

        # Posts endpoints
        ("Get Posts", f"{base_url}/posts"),
        ("Get Posts (limited)", f"{base_url}/posts?limit=5"),

        # Comments endpoints (the problematic ones from APU-120)
        ("Get All Comments", f"{base_url}/comments"),
        ("Get Post Comments", f"{base_url}/posts/comments"),

        # Platform-specific endpoints
        ("Instagram Posts", f"{base_url}/posts?platform=instagram&limit=5"),
        ("TikTok Posts", f"{base_url}/posts?platform=tiktok&limit=5"),
        ("X Posts", f"{base_url}/posts?platform=x&limit=5"),
        ("Threads Posts", f"{base_url}/posts?platform=threads&limit=5"),
        ("Bluesky Posts", f"{base_url}/posts?platform=bluesky&limit=5"),

        # User/profile endpoints
        ("User Profile", f"{base_url}/user/profile"),
        ("User Stats", f"{base_url}/user/stats"),
    ]

    diagnostics_result = {
        "diagnostic_run": datetime.now().isoformat(),
        "base_url": base_url,
        "total_endpoints": len(endpoints_to_test),
        "endpoints": {},
        "summary": {
            "healthy": 0,
            "endpoint_not_found": 0,
            "auth_failed": 0,
            "connection_error": 0,
            "timeout": 0,
            "other_errors": 0
        },
        "critical_issues": [],
        "recommendations": []
    }

    # Test each endpoint
    for endpoint_name, url in endpoints_to_test:
        print(f"[APU-141] Testing: {endpoint_name}")

        result = test_api_endpoint(url, headers, endpoint_name)
        diagnostics_result["endpoints"][endpoint_name] = result

        # Update summary counts
        status = result["status"]
        if status in diagnostics_result["summary"]:
            diagnostics_result["summary"][status] += 1
        else:
            diagnostics_result["summary"]["other_errors"] += 1

        # Identify critical issues
        if endpoint_name in ["Get Post Comments", "Get Posts"] and status != "healthy":
            diagnostics_result["critical_issues"].append({
                "endpoint": endpoint_name,
                "issue": result["error"] or f"Status: {status}",
                "impact": "High - Core engagement monitoring affected"
            })

        # Small delay between requests
        time.sleep(0.5)

    # Generate recommendations based on results
    summary = diagnostics_result["summary"]

    if summary["auth_failed"] > 0:
        diagnostics_result["recommendations"].append(
            "Authentication issues detected - refresh access token"
        )

    if summary["endpoint_not_found"] > 3:
        diagnostics_result["recommendations"].append(
            "Multiple 404 errors suggest API structure has changed or base URL is incorrect"
        )

    if summary["connection_error"] > 0 or summary["timeout"] > 0:
        diagnostics_result["recommendations"].append(
            "Network connectivity issues - check server status and network connection"
        )

    if len(diagnostics_result["critical_issues"]) > 0:
        diagnostics_result["recommendations"].append(
            "Critical engagement monitoring endpoints are failing - immediate attention required"
        )

    # Calculate overall health score
    total_tests = len(endpoints_to_test)
    healthy_tests = summary["healthy"]
    health_score = healthy_tests / total_tests if total_tests > 0 else 0
    diagnostics_result["overall_health_score"] = health_score

    # Save results
    DIAGNOSTICS_LOG.parent.mkdir(exist_ok=True)
    save_json(DIAGNOSTICS_LOG, diagnostics_result)

    return diagnostics_result

def main():
    """Run APU-141 API diagnostics and display results."""
    print("=" * 60)
    print("APU-141 ENGAGEMENT API DIAGNOSTICS")
    print("=" * 60)

    # Run diagnostics
    results = run_comprehensive_api_diagnostics()

    if "error" in results:
        print(f"[ERROR] {results['error']}")
        return 1

    # Display summary
    summary = results["summary"]
    print(f"\n[SUMMARY] API Health Overview:")
    print(f"  Total endpoints tested: {results['total_endpoints']}")
    print(f"  Healthy: {summary['healthy']}")
    print(f"  Failed (404): {summary['endpoint_not_found']}")
    print(f"  Auth failed: {summary['auth_failed']}")
    print(f"  Connection errors: {summary['connection_error']}")
    print(f"  Timeouts: {summary['timeout']}")
    print(f"  Other errors: {summary['other_errors']}")
    print(f"  Overall health score: {results['overall_health_score']:.2%}")

    # Display critical issues
    if results["critical_issues"]:
        print(f"\n[CRITICAL ISSUES]:")
        for issue in results["critical_issues"]:
            print(f"  • {issue['endpoint']}: {issue['issue']}")
            print(f"    Impact: {issue['impact']}")

    # Display recommendations
    if results["recommendations"]:
        print(f"\n[RECOMMENDATIONS]:")
        for rec in results["recommendations"]:
            print(f"  • {rec}")

    # Display detailed endpoint results
    print(f"\n[DETAILED RESULTS]:")
    for endpoint_name, endpoint_data in results["endpoints"].items():
        status = endpoint_data["status"]
        response_code = endpoint_data["response_code"]
        response_time = endpoint_data.get("response_time_ms", "N/A")

        status_emoji = {
            "healthy": "✅",
            "endpoint_not_found": "❌",
            "auth_failed": "🔐",
            "connection_error": "🌐",
            "timeout": "⏰",
            "error": "⚠️"
        }.get(status, "❓")

        print(f"  {status_emoji} {endpoint_name}: HTTP {response_code} ({response_time}ms)")

        if endpoint_data.get("error"):
            print(f"    Error: {endpoint_data['error']}")

    print(f"\n[APU-141] Diagnostics complete. Results saved to:")
    print(f"  {DIAGNOSTICS_LOG}")

    return 0 if results["overall_health_score"] > 0.5 else 1

if __name__ == "__main__":
    exit(main())