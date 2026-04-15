"""
api_health_monitor.py - APU-51 API Health Monitoring System
Monitors API endpoint health and generates alerts for failures.

Created by: Dex - Community Agent (APU-51)
Purpose: Prevent community intelligence outages by monitoring API health

Features:
- Real-time API endpoint monitoring
- Health status tracking and alerting
- Fallback system activation
- Performance metrics collection
- Automated recovery suggestions
"""

import json
import sys
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import (
    load_json, save_json, VAWN_DIR, log_run, today_str
)

# Configuration
API_HEALTH_LOG = VAWN_DIR / "research" / "api_health_monitor_log.json"
API_ENDPOINTS_CONFIG = VAWN_DIR / "config" / "api_endpoints.json"

class APIHealthMonitor:
    """API health monitoring and alerting system."""

    def __init__(self):
        self.base_url = "https://apulustudio.onrender.com/api"
        self.endpoints_to_monitor = [
            {
                "name": "comments",
                "path": "/posts/comments",
                "critical": True,
                "expected_response": "json",
                "timeout": 10
            },
            {
                "name": "posts",
                "path": "/posts",
                "critical": True,
                "expected_response": "json",
                "timeout": 10
            },
            {
                "name": "health",
                "path": "/health",
                "critical": False,
                "expected_response": "json",
                "timeout": 5
            },
            {
                "name": "api_root",
                "path": "",
                "critical": False,
                "expected_response": "any",
                "timeout": 5
            }
        ]

        self.health_status = {
            "overall_status": "unknown",
            "endpoints": {},
            "last_check": None,
            "critical_failures": 0,
            "total_endpoints": len(self.endpoints_to_monitor)
        }

    def check_endpoint_health(self, endpoint: Dict[str, Any]) -> Dict[str, Any]:
        """Check health of a single API endpoint."""

        endpoint_name = endpoint["name"]
        url = f"{self.base_url}{endpoint['path']}"

        health_result = {
            "name": endpoint_name,
            "url": url,
            "status": "unknown",
            "response_time_ms": None,
            "error": None,
            "last_checked": datetime.now().isoformat(),
            "critical": endpoint["critical"]
        }

        try:
            print(f"[HEALTH] Checking {endpoint_name}: {url}")

            start_time = datetime.now()
            response = requests.get(url, timeout=endpoint["timeout"])
            end_time = datetime.now()

            response_time_ms = (end_time - start_time).total_seconds() * 1000

            health_result["response_time_ms"] = round(response_time_ms, 2)
            health_result["status_code"] = response.status_code

            if response.status_code == 200:
                health_result["status"] = "healthy"
                print(f"[HEALTH] PASS {endpoint_name}: Healthy ({response_time_ms:.1f}ms)")
            elif response.status_code == 404:
                health_result["status"] = "not_found"
                health_result["error"] = "Endpoint not implemented"
                print(f"[HEALTH] FAIL {endpoint_name}: Not Found (404)")
            else:
                health_result["status"] = "error"
                health_result["error"] = f"HTTP {response.status_code}"
                print(f"[HEALTH] FAIL {endpoint_name}: Error ({response.status_code})")

        except requests.exceptions.Timeout:
            health_result["status"] = "timeout"
            health_result["error"] = f"Timeout after {endpoint['timeout']}s"
            print(f"[HEALTH] FAIL {endpoint_name}: Timeout")

        except requests.exceptions.ConnectionError:
            health_result["status"] = "connection_error"
            health_result["error"] = "Cannot connect to server"
            print(f"[HEALTH] FAIL {endpoint_name}: Connection Error")

        except Exception as e:
            health_result["status"] = "error"
            health_result["error"] = str(e)
            print(f"[HEALTH] FAIL {endpoint_name}: Error - {e}")

        return health_result

    def check_all_endpoints(self) -> Dict[str, Any]:
        """Check health of all monitored endpoints."""

        print(f"\n[MONITOR] API Health Check Starting...")
        print(f"[MONITOR] Checking {len(self.endpoints_to_monitor)} endpoints")

        endpoint_results = []
        critical_failures = 0
        healthy_count = 0

        for endpoint in self.endpoints_to_monitor:
            result = self.check_endpoint_health(endpoint)
            endpoint_results.append(result)

            # Count failures
            if result["status"] != "healthy":
                if result["critical"]:
                    critical_failures += 1
            else:
                healthy_count += 1

        # Determine overall status
        if critical_failures > 0:
            overall_status = "critical"
        elif healthy_count == len(self.endpoints_to_monitor):
            overall_status = "healthy"
        else:
            overall_status = "degraded"

        self.health_status = {
            "overall_status": overall_status,
            "endpoints": {result["name"]: result for result in endpoint_results},
            "last_check": datetime.now().isoformat(),
            "critical_failures": critical_failures,
            "healthy_count": healthy_count,
            "total_endpoints": len(self.endpoints_to_monitor),
            "summary": {
                "healthy": healthy_count,
                "failed": len(self.endpoints_to_monitor) - healthy_count,
                "critical_failures": critical_failures
            }
        }

        print(f"\n[MONITOR] Health Check Complete")
        print(f"[MONITOR] Overall Status: {overall_status.upper()}")
        print(f"[MONITOR] Healthy: {healthy_count}/{len(self.endpoints_to_monitor)}")
        print(f"[MONITOR] Critical Failures: {critical_failures}")

        return self.health_status

    def generate_health_alerts(self) -> List[Dict[str, Any]]:
        """Generate alerts based on API health status."""

        alerts = []

        if not self.health_status["last_check"]:
            return alerts

        # Critical endpoint failures
        for endpoint_name, endpoint_result in self.health_status["endpoints"].items():
            if endpoint_result["critical"] and endpoint_result["status"] != "healthy":
                alerts.append({
                    "type": "critical_endpoint_failure",
                    "severity": "critical",
                    "message": f"Critical API endpoint '{endpoint_name}' is {endpoint_result['status']}",
                    "endpoint": endpoint_name,
                    "url": endpoint_result["url"],
                    "error": endpoint_result.get("error", "Unknown error"),
                    "impact": "Community intelligence data collection disabled",
                    "recommendation": "Activate alternative comment collection system",
                    "timestamp": datetime.now().isoformat()
                })

        # Overall system health
        if self.health_status["overall_status"] == "critical":
            alerts.append({
                "type": "api_system_critical",
                "severity": "high",
                "message": f"API system health is critical ({self.health_status['critical_failures']} critical failures)",
                "impact": "APU-51 intelligence engine operating with limited data",
                "recommendation": "Enable enhanced fallback systems and notify development team",
                "timestamp": datetime.now().isoformat()
            })

        # Performance warnings
        for endpoint_name, endpoint_result in self.health_status["endpoints"].items():
            if endpoint_result["status"] == "healthy" and endpoint_result["response_time_ms"]:
                if endpoint_result["response_time_ms"] > 5000:  # 5 seconds
                    alerts.append({
                        "type": "api_performance_degraded",
                        "severity": "medium",
                        "message": f"API endpoint '{endpoint_name}' responding slowly ({endpoint_result['response_time_ms']:.0f}ms)",
                        "endpoint": endpoint_name,
                        "response_time": endpoint_result["response_time_ms"],
                        "recommendation": "Monitor for potential service degradation",
                        "timestamp": datetime.now().isoformat()
                    })

        return alerts

    def create_health_dashboard(self) -> str:
        """Create a health dashboard display."""

        if not self.health_status["last_check"]:
            return "[HEALTH] No health check data available"

        dashboard = f"""
================================================================================
[*] APU-51 API HEALTH MONITOR DASHBOARD
[DATE] {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
================================================================================

[OVERALL STATUS] {self.health_status['overall_status'].upper()}
  Healthy Endpoints: {self.health_status['healthy_count']}/{self.health_status['total_endpoints']}
  Critical Failures: {self.health_status['critical_failures']}
  Last Check: {datetime.fromisoformat(self.health_status['last_check']).strftime('%H:%M:%S')}

[ENDPOINT HEALTH]"""

        for endpoint_name, endpoint_result in self.health_status["endpoints"].items():
            status_symbol = "PASS" if endpoint_result["status"] == "healthy" else "FAIL"
            critical_marker = "[CRITICAL]" if endpoint_result["critical"] else ""

            if endpoint_result["response_time_ms"]:
                timing = f" ({endpoint_result['response_time_ms']:.0f}ms)"
            else:
                timing = ""

            error_info = f" - {endpoint_result.get('error', '')}" if endpoint_result.get('error') else ""

            dashboard += f"""
  {status_symbol} {endpoint_name.upper()}: {endpoint_result['status'].upper()}{timing} {critical_marker}{error_info}"""

        dashboard += f"""

[RECOMMENDATIONS]"""

        if self.health_status["overall_status"] == "critical":
            dashboard += f"""
  [!] IMMEDIATE: Activate alternative comment collection system
  [!] ESCALATE: Notify development team of critical API failures
  [!] MONITOR: Check again in 5 minutes for recovery"""

        elif self.health_status["overall_status"] == "degraded":
            dashboard += f"""
  [!] ENABLE: Enhanced monitoring mode
  [!] PREPARE: Fallback systems for potential failures"""

        else:
            dashboard += f"""
  [OK] API systems healthy - normal operations"""

        dashboard += f"""

================================================================================"""

        return dashboard

    def save_health_log(self, alerts: List[Dict[str, Any]]):
        """Save health monitoring results to log."""

        health_log_data = load_json(API_HEALTH_LOG)

        today = today_str()
        if today not in health_log_data:
            health_log_data[today] = []

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "health_status": self.health_status,
            "alerts": alerts,
            "monitor_version": "apu51_v1.0"
        }

        health_log_data[today].append(log_entry)

        # Keep only last 30 days
        cutoff_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        health_log_data = {k: v for k, v in health_log_data.items() if k >= cutoff_date}

        save_json(API_HEALTH_LOG, health_log_data)

    def run_health_monitoring(self) -> Dict[str, Any]:
        """Run complete health monitoring cycle."""

        print("\n[*] APU-51 API Health Monitor Starting...")
        print("[VERSION] API Health Monitor v1.0")

        # Check all endpoints
        health_status = self.check_all_endpoints()

        # Generate alerts
        alerts = self.generate_health_alerts()

        # Create dashboard
        dashboard = self.create_health_dashboard()
        print(dashboard)

        # Save to log
        self.save_health_log(alerts)

        # Log summary
        status_code = "critical" if health_status["overall_status"] == "critical" else \
                     "warning" if health_status["overall_status"] == "degraded" else "ok"

        log_entry = (f"API Health: {health_status['overall_status']}, "
                    f"Healthy: {health_status['healthy_count']}/{health_status['total_endpoints']}, "
                    f"Critical Failures: {health_status['critical_failures']}, "
                    f"Alerts: {len(alerts)}")

        log_run("APIHealthMonitorAPU51", status_code, log_entry)

        print(f"\n[COMPLETE] API Health Monitor Complete")
        print(f"Status: {health_status['overall_status'].upper()}")
        print(f"Alerts Generated: {len(alerts)}")

        return {
            "health_status": health_status,
            "alerts": alerts,
            "dashboard": dashboard
        }


def main():
    """Main execution for API health monitoring."""

    monitor = APIHealthMonitor()
    results = monitor.run_health_monitoring()

    # Print any critical alerts
    critical_alerts = [a for a in results["alerts"] if a["severity"] == "critical"]
    if critical_alerts:
        print(f"\n[CRITICAL] {len(critical_alerts)} CRITICAL ALERTS!")
        for alert in critical_alerts:
            print(f"  - {alert['message']}")
            print(f"    Recommendation: {alert['recommendation']}")

    return results


if __name__ == "__main__":
    monitoring_results = main()