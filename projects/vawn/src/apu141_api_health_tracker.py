"""
apu141_api_health_tracker.py — Independent API Endpoint Health Tracking
Tracks API health separately from engagement metrics to provide accurate system status.

Created by: Dex - Community Agent (APU-141)

KEY INNOVATION:
Separates infrastructure health (API availability) from business metrics (engagement rates).
This prevents false negatives when APIs are down but agents are working correctly.
"""

import json
import requests
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from vawn_config import load_json, save_json, VAWN_DIR, CREDS_FILE

# API health tracking configuration
API_HEALTH_LOG = VAWN_DIR / "research" / "apu141_api_health_log.json"
API_STATUS_CACHE = VAWN_DIR / "research" / "apu141_api_status_cache.json"
REALTIME_API_STATUS = VAWN_DIR / "research" / "apu141_realtime_api_status.json"

class APIEndpointHealthTracker:
    """Independent API endpoint health tracking system."""

    def __init__(self):
        self.base_url = ""
        self.access_token = ""
        self.endpoints = {
            # Core API endpoints
            "health_check": "/health",
            "api_status": "/status",
            "user_profile": "/user/profile",

            # Posts endpoints
            "posts_list": "/posts",
            "posts_limited": "/posts?limit=5",

            # Comments endpoints (the problematic ones)
            "comments_all": "/comments",
            "posts_comments": "/posts/comments",

            # Platform-specific endpoints
            "instagram_posts": "/posts?platform=instagram&limit=3",
            "tiktok_posts": "/posts?platform=tiktok&limit=3",
            "x_posts": "/posts?platform=x&limit=3",
            "threads_posts": "/posts?platform=threads&limit=3",
            "bluesky_posts": "/posts?platform=bluesky&limit=3",
        }

        self.health_thresholds = {
            "response_time_warning_ms": 5000,     # 5 seconds
            "response_time_critical_ms": 10000,   # 10 seconds
            "consecutive_failures_warning": 3,
            "consecutive_failures_critical": 5,
            "overall_health_degraded": 0.7,       # 70% endpoints healthy
            "overall_health_critical": 0.5        # 50% endpoints healthy
        }

    def load_credentials(self) -> bool:
        """Load API credentials and configuration."""
        try:
            creds = load_json(CREDS_FILE)
            self.base_url = creds.get("base_url", "")
            self.access_token = creds.get("access_token", "")

            if not self.base_url or not self.access_token:
                print("[APU-141] ERROR: Missing base_url or access_token in credentials")
                return False

            return True

        except Exception as e:
            print(f"[APU-141] ERROR: Failed to load credentials: {e}")
            return False

    def test_single_endpoint(self, endpoint_name: str, endpoint_path: str, timeout: int = 10) -> Dict[str, Any]:
        """Test a single API endpoint and return detailed health metrics."""
        url = self.base_url + endpoint_path
        headers = {"Authorization": f"Bearer {self.access_token}"}

        test_result = {
            "endpoint": endpoint_name,
            "path": endpoint_path,
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "status": "unknown",
            "http_code": None,
            "response_time_ms": None,
            "error": None,
            "data_received": False,
            "auth_valid": None,
            "connectivity": "unknown"
        }

        try:
            start_time = time.time()
            response = requests.get(url, headers=headers, timeout=timeout)
            end_time = time.time()

            test_result["http_code"] = response.status_code
            test_result["response_time_ms"] = int((end_time - start_time) * 1000)
            test_result["connectivity"] = "connected"

            # Analyze response
            if response.status_code == 200:
                test_result["status"] = "healthy"
                test_result["auth_valid"] = True
                try:
                    data = response.json()
                    test_result["data_received"] = bool(data)
                except:
                    test_result["data_received"] = bool(response.text.strip())

            elif response.status_code == 401:
                test_result["status"] = "auth_failed"
                test_result["auth_valid"] = False
                test_result["error"] = "Authentication failed - token may be expired"

            elif response.status_code == 403:
                test_result["status"] = "forbidden"
                test_result["auth_valid"] = True  # Token is valid but insufficient permissions
                test_result["error"] = "Access forbidden - insufficient permissions"

            elif response.status_code == 404:
                test_result["status"] = "not_found"
                test_result["auth_valid"] = True  # Auth worked but endpoint doesn't exist
                test_result["error"] = "Endpoint not found - API may have changed"

            elif response.status_code >= 500:
                test_result["status"] = "server_error"
                test_result["auth_valid"] = True  # Server error, not auth issue
                test_result["error"] = f"Server error: HTTP {response.status_code}"

            else:
                test_result["status"] = "error"
                test_result["error"] = f"HTTP {response.status_code}: {response.text[:100]}"

            # Check response time warnings
            if test_result["response_time_ms"] > self.health_thresholds["response_time_critical_ms"]:
                test_result["response_time_status"] = "critical"
            elif test_result["response_time_ms"] > self.health_thresholds["response_time_warning_ms"]:
                test_result["response_time_status"] = "warning"
            else:
                test_result["response_time_status"] = "good"

        except requests.exceptions.Timeout:
            test_result["status"] = "timeout"
            test_result["connectivity"] = "timeout"
            test_result["error"] = f"Request timeout after {timeout} seconds"

        except requests.exceptions.ConnectionError:
            test_result["status"] = "connection_failed"
            test_result["connectivity"] = "failed"
            test_result["error"] = "Failed to connect to server"

        except Exception as e:
            test_result["status"] = "exception"
            test_result["error"] = str(e)

        return test_result

    def run_comprehensive_health_check(self, max_workers: int = 5) -> Dict[str, Any]:
        """Run comprehensive health check on all endpoints concurrently."""
        if not self.load_credentials():
            return {"error": "Failed to load credentials", "timestamp": datetime.now().isoformat()}

        print(f"[APU-141] Running comprehensive API health check...")
        health_check = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "total_endpoints": len(self.endpoints),
            "endpoints": {},
            "summary": {
                "healthy": 0,
                "auth_failed": 0,
                "not_found": 0,
                "server_error": 0,
                "connection_failed": 0,
                "timeout": 0,
                "other": 0
            },
            "performance": {
                "total_test_time_ms": None,
                "average_response_time_ms": None,
                "slowest_endpoint": None,
                "fastest_endpoint": None
            },
            "authentication": {
                "token_valid": None,
                "auth_test_passed": False,
                "endpoints_requiring_auth": []
            },
            "critical_endpoints": {
                "posts_available": False,
                "comments_available": False,
                "core_api_available": False
            }
        }

        start_time = time.time()

        # Test all endpoints concurrently for faster results
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all endpoint tests
            future_to_endpoint = {
                executor.submit(self.test_single_endpoint, name, path): name
                for name, path in self.endpoints.items()
            }

            # Collect results as they complete
            for future in as_completed(future_to_endpoint):
                endpoint_name = future_to_endpoint[future]
                try:
                    result = future.result()
                    health_check["endpoints"][endpoint_name] = result

                    # Update summary counts
                    status = result["status"]
                    if status in health_check["summary"]:
                        health_check["summary"][status] += 1
                    else:
                        health_check["summary"]["other"] += 1

                except Exception as e:
                    print(f"[APU-141] Error testing {endpoint_name}: {e}")

        end_time = time.time()
        health_check["performance"]["total_test_time_ms"] = int((end_time - start_time) * 1000)

        # Analyze results
        self.analyze_health_results(health_check)

        # Save results
        self.save_health_results(health_check)

        return health_check

    def analyze_health_results(self, health_check: Dict[str, Any]) -> None:
        """Analyze health check results and add insights."""
        endpoints = health_check["endpoints"]

        # Performance analysis
        response_times = [
            ep["response_time_ms"] for ep in endpoints.values()
            if ep["response_time_ms"] is not None
        ]

        if response_times:
            health_check["performance"]["average_response_time_ms"] = int(sum(response_times) / len(response_times))

            # Find slowest and fastest
            slowest = max(endpoints.items(), key=lambda x: x[1]["response_time_ms"] or 0)
            fastest = min(endpoints.items(), key=lambda x: x[1]["response_time_ms"] or float('inf'))

            health_check["performance"]["slowest_endpoint"] = {
                "name": slowest[0],
                "response_time_ms": slowest[1]["response_time_ms"]
            }
            health_check["performance"]["fastest_endpoint"] = {
                "name": fastest[0],
                "response_time_ms": fastest[1]["response_time_ms"]
            }

        # Authentication analysis
        auth_results = [ep for ep in endpoints.values() if ep["auth_valid"] is not None]
        if auth_results:
            auth_valid_count = sum(1 for ep in auth_results if ep["auth_valid"])
            health_check["authentication"]["token_valid"] = auth_valid_count > 0
            health_check["authentication"]["auth_test_passed"] = auth_valid_count > len(auth_results) * 0.5

        # Critical endpoints analysis
        health_check["critical_endpoints"]["posts_available"] = any(
            ep["status"] == "healthy" for name, ep in endpoints.items()
            if "posts" in name and "comment" not in name
        )

        health_check["critical_endpoints"]["comments_available"] = any(
            ep["status"] == "healthy" for name, ep in endpoints.items()
            if "comment" in name
        )

        health_check["critical_endpoints"]["core_api_available"] = any(
            ep["status"] == "healthy" for name, ep in endpoints.items()
            if name in ["health_check", "api_status", "user_profile"]
        )

        # Overall health calculation
        total_endpoints = health_check["total_endpoints"]
        healthy_endpoints = health_check["summary"]["healthy"]
        health_percentage = healthy_endpoints / total_endpoints if total_endpoints > 0 else 0

        if health_percentage >= self.health_thresholds["overall_health_degraded"]:
            health_check["overall_status"] = "healthy"
        elif health_percentage >= self.health_thresholds["overall_health_critical"]:
            health_check["overall_status"] = "degraded"
        else:
            health_check["overall_status"] = "critical"

        health_check["health_percentage"] = health_percentage

    def save_health_results(self, health_check: Dict[str, Any]) -> None:
        """Save health results for monitoring and historical tracking."""

        # Save real-time status for immediate monitoring
        realtime_status = {
            "timestamp": health_check["timestamp"],
            "overall_status": health_check.get("overall_status", "unknown"),
            "health_percentage": health_check.get("health_percentage", 0.0),
            "critical_endpoints": health_check["critical_endpoints"],
            "authentication_status": health_check["authentication"]["token_valid"],
            "summary": health_check["summary"]
        }

        REALTIME_API_STATUS.parent.mkdir(exist_ok=True)
        save_json(REALTIME_API_STATUS, realtime_status)

        # Save detailed results to health log
        api_health_log = load_json(API_HEALTH_LOG) if API_HEALTH_LOG.exists() else {}
        today = datetime.now().strftime("%Y-%m-%d")

        if today not in api_health_log:
            api_health_log[today] = []

        api_health_log[today].append(health_check)

        # Keep last 7 days of detailed logs
        cutoff_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        api_health_log = {k: v for k, v in api_health_log.items() if k >= cutoff_date}

        save_json(API_HEALTH_LOG, api_health_log)

    def get_current_api_status(self) -> Dict[str, Any]:
        """Get current API status from cache."""
        try:
            return load_json(REALTIME_API_STATUS)
        except:
            return {
                "timestamp": None,
                "overall_status": "unknown",
                "health_percentage": 0.0,
                "error": "No recent health check data available"
            }

def main():
    """Run API health check and display results."""
    tracker = APIEndpointHealthTracker()

    print("APU-141 Independent API Health Tracking")
    print("=" * 50)

    # Run comprehensive health check
    results = tracker.run_comprehensive_health_check()

    if "error" in results:
        print(f"[ERROR] {results['error']}")
        return 1

    # Display summary
    summary = results["summary"]
    performance = results["performance"]
    critical = results["critical_endpoints"]
    auth = results["authentication"]

    print(f"\n[SUMMARY] API Health Overview:")
    print(f"  Overall Status: {results.get('overall_status', 'unknown').upper()}")
    print(f"  Health Percentage: {results.get('health_percentage', 0):.1%}")
    print(f"  Total Test Time: {performance['total_test_time_ms']}ms")

    print(f"\n[ENDPOINT STATUS]:")
    print(f"  ✅ Healthy: {summary['healthy']}")
    print(f"  🔐 Auth Failed: {summary['auth_failed']}")
    print(f"  ❌ Not Found: {summary['not_found']}")
    print(f"  🔥 Server Error: {summary['server_error']}")
    print(f"  🌐 Connection Failed: {summary['connection_failed']}")
    print(f"  ⏰ Timeout: {summary['timeout']}")

    print(f"\n[CRITICAL SYSTEMS]:")
    print(f"  Posts API: {'✅ Available' if critical['posts_available'] else '❌ Unavailable'}")
    print(f"  Comments API: {'✅ Available' if critical['comments_available'] else '❌ Unavailable'}")
    print(f"  Core API: {'✅ Available' if critical['core_api_available'] else '❌ Unavailable'}")
    print(f"  Authentication: {'✅ Valid' if auth['token_valid'] else '❌ Invalid'}")

    if performance.get("average_response_time_ms"):
        print(f"\n[PERFORMANCE]:")
        print(f"  Average Response Time: {performance['average_response_time_ms']}ms")
        if performance.get("slowest_endpoint"):
            print(f"  Slowest: {performance['slowest_endpoint']['name']} ({performance['slowest_endpoint']['response_time_ms']}ms)")

    print(f"\n[APU-141] Health tracking results saved to:")
    print(f"  Real-time: {REALTIME_API_STATUS}")
    print(f"  Historical: {API_HEALTH_LOG}")

    return 0 if results.get("health_percentage", 0) > 0.5 else 1

if __name__ == "__main__":
    exit(main())