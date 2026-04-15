"""
platform_health_monitor.py — Real-time platform health and credential status monitoring.
Complements engagement_monitor_apu168.py with detailed health tracking and reporting.
Created by: Dex - Community Agent (APU-168)
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))
from vawn_config import load_json, save_json, RESEARCH_DIR, VAWN_DIR

logger = logging.getLogger(__name__)

# Import enhanced monitor classes
sys.path.insert(0, str(Path(__file__).parent))
from engagement_monitor_apu168 import (
    PlatformStatus, HealthLevel, PlatformConfig, PLATFORM_CONFIGS,
    CredentialValidator, EnhancedEngagementMonitor
)

@dataclass
class HealthMetric:
    """Individual health metric tracking."""
    timestamp: str
    platform: str
    status: str
    health_score: float
    response_time_ms: Optional[float] = None
    error_count: int = 0
    last_success: Optional[str] = None
    last_error: Optional[str] = None
    uptime_percentage: float = 0.0

@dataclass
class SystemHealthReport:
    """Comprehensive system health report."""
    timestamp: str
    overall_health_score: float
    overall_health_level: str
    platforms_total: int
    platforms_active: int
    platforms_degraded: int
    platforms_failed: int
    critical_issues: List[str]
    warnings: List[str]
    recommendations: List[str]
    platform_details: Dict[str, HealthMetric]
    historical_trend: str  # "improving", "stable", "declining"

class PlatformHealthMonitor:
    """Monitors platform health and credential status."""

    def __init__(self):
        self.health_log_file = RESEARCH_DIR / "apu168_platform_health_detailed.json"
        self.alerts_file = RESEARCH_DIR / "apu168_health_alerts.json"
        self.config_file = VAWN_DIR / "config" / "health_monitor_config.json"

        # Health thresholds
        self.health_thresholds = {
            "critical_health_score": 0.2,
            "warning_health_score": 0.5,
            "max_error_count": 5,
            "min_uptime_percentage": 80.0,
            "max_response_time_ms": 5000,
            "alert_cooldown_minutes": 30
        }

        self.load_config()

    def load_config(self) -> None:
        """Load health monitoring configuration."""
        try:
            if self.config_file.exists():
                config = load_json(self.config_file)
                self.health_thresholds.update(config.get("health_thresholds", {}))
            else:
                # Create default config
                default_config = {
                    "enabled": True,
                    "check_interval_minutes": 5,
                    "health_thresholds": self.health_thresholds,
                    "alerting_enabled": True,
                    "credential_check_enabled": True
                }
                save_json(self.config_file, default_config)
        except Exception as e:
            logger.error(f"Error loading health monitor config: {str(e)}")

    def check_credential_health(self) -> Dict[str, Dict[str, Any]]:
        """Check credential health for all platforms."""
        creds_file = VAWN_DIR / "config" / "credentials.json"

        if not creds_file.exists():
            return {name: {"status": "no_creds_file", "missing": config.required_credentials}
                   for name, config in PLATFORM_CONFIGS.items()}

        try:
            creds = load_json(creds_file)

            credential_health = {}
            for platform_name, config in PLATFORM_CONFIGS.items():
                health = {
                    "status": "checking",
                    "missing_credentials": [],
                    "present_credentials": [],
                    "api_connectivity": "unknown",
                    "validation_timestamp": datetime.now().isoformat()
                }

                # Check for required credentials
                for cred in config.required_credentials:
                    if creds.get(cred):
                        health["present_credentials"].append(cred)
                    else:
                        health["missing_credentials"].append(cred)

                # Determine credential status
                if not health["missing_credentials"]:
                    health["status"] = "all_present"
                    # Test API connectivity
                    try:
                        validation_result = CredentialValidator._validate_platform_credentials(
                            platform_name, config, creds
                        )
                        health["api_connectivity"] = validation_result.value
                    except Exception as e:
                        health["api_connectivity"] = f"test_failed: {str(e)}"
                elif len(health["present_credentials"]) > 0:
                    health["status"] = "partial"
                else:
                    health["status"] = "missing_all"

                credential_health[platform_name] = health

            return credential_health

        except Exception as e:
            logger.error(f"Error checking credential health: {str(e)}")
            return {name: {"status": "error", "error": str(e)}
                   for name in PLATFORM_CONFIGS.keys()}

    def collect_platform_metrics(self) -> Dict[str, HealthMetric]:
        """Collect current health metrics for all platforms."""
        metrics = {}

        try:
            # Get current platform health from enhanced monitor
            monitor = EnhancedEngagementMonitor()

            # Load recent health data
            health_log = load_json(self.health_log_file) if self.health_log_file.exists() else {}

            for platform_name, config in monitor.platform_configs.items():
                # Calculate uptime from recent logs
                uptime_percentage = self._calculate_uptime(platform_name, health_log)

                # Get response time (would need to be measured during actual API calls)
                avg_response_time = self._get_average_response_time(platform_name, health_log)

                metric = HealthMetric(
                    timestamp=datetime.now().isoformat(),
                    platform=platform_name,
                    status=config.status.value,
                    health_score=config.health_score,
                    response_time_ms=avg_response_time,
                    error_count=config.error_count,
                    last_success=config.last_success,
                    last_error=config.last_error,
                    uptime_percentage=uptime_percentage
                )

                metrics[platform_name] = metric

        except Exception as e:
            logger.error(f"Error collecting platform metrics: {str(e)}")
            # Return basic metrics even if enhanced monitor fails
            for platform_name in PLATFORM_CONFIGS.keys():
                metrics[platform_name] = HealthMetric(
                    timestamp=datetime.now().isoformat(),
                    platform=platform_name,
                    status="unknown",
                    health_score=0.0,
                    error_count=0,
                    uptime_percentage=0.0
                )

        return metrics

    def _calculate_uptime(self, platform: str, health_log: Dict[str, Any]) -> float:
        """Calculate uptime percentage for platform over last 24 hours."""
        try:
            now = datetime.now()
            cutoff = now - timedelta(hours=24)

            total_checks = 0
            successful_checks = 0

            # Look through recent log entries
            for date_str, entries in health_log.items():
                for entry in entries:
                    entry_time = datetime.fromisoformat(entry.get("timestamp", ""))
                    if entry_time >= cutoff:
                        platform_data = entry.get("platform_health_scores", {})
                        if platform in platform_data:
                            total_checks += 1
                            if platform_data[platform] > 0:
                                successful_checks += 1

            if total_checks == 0:
                return 0.0

            return (successful_checks / total_checks) * 100.0

        except Exception as e:
            logger.error(f"Error calculating uptime for {platform}: {str(e)}")
            return 0.0

    def _get_average_response_time(self, platform: str, health_log: Dict[str, Any]) -> Optional[float]:
        """Get average response time for platform (placeholder)."""
        # This would be implemented with actual response time tracking
        # For now, return None as placeholder
        return None

    def generate_health_report(self) -> SystemHealthReport:
        """Generate comprehensive system health report."""
        timestamp = datetime.now().isoformat()

        # Collect current metrics
        platform_metrics = self.collect_platform_metrics()
        credential_health = self.check_credential_health()

        # Calculate overall statistics
        platforms_total = len(platform_metrics)
        platforms_active = 0
        platforms_degraded = 0
        platforms_failed = 0
        total_health_score = 0.0

        critical_issues = []
        warnings = []
        recommendations = []

        for platform_name, metric in platform_metrics.items():
            total_health_score += metric.health_score

            if metric.status == PlatformStatus.ACTIVE.value:
                platforms_active += 1
            elif metric.status in [PlatformStatus.PARTIAL.value, PlatformStatus.DEGRADED.value]:
                platforms_degraded += 1
            else:
                platforms_failed += 1

            # Check for critical issues
            if metric.health_score < self.health_thresholds["critical_health_score"]:
                critical_issues.append(f"{platform_name}: Critical health score {metric.health_score:.3f}")

            if metric.error_count >= self.health_thresholds["max_error_count"]:
                critical_issues.append(f"{platform_name}: High error count {metric.error_count}")

            # Check for warnings
            if metric.health_score < self.health_thresholds["warning_health_score"]:
                warnings.append(f"{platform_name}: Low health score {metric.health_score:.3f}")

            if metric.uptime_percentage < self.health_thresholds["min_uptime_percentage"]:
                warnings.append(f"{platform_name}: Low uptime {metric.uptime_percentage:.1f}%")

            # Generate recommendations
            cred_health = credential_health.get(platform_name, {})
            if cred_health.get("missing_credentials"):
                recommendations.append(f"{platform_name}: Set up missing credentials: {cred_health['missing_credentials']}")

            if metric.status == PlatformStatus.UNAVAILABLE.value:
                recommendations.append(f"{platform_name}: Check API configuration and credentials")

        # Calculate overall health
        overall_health_score = total_health_score / platforms_total if platforms_total > 0 else 0.0

        if overall_health_score >= 0.9:
            overall_health_level = HealthLevel.EXCELLENT.value
        elif overall_health_score >= 0.7:
            overall_health_level = HealthLevel.GOOD.value
        elif overall_health_score >= 0.4:
            overall_health_level = HealthLevel.DEGRADED.value
        elif overall_health_score >= 0.1:
            overall_health_level = HealthLevel.CRITICAL.value
        else:
            overall_health_level = HealthLevel.FAILED.value

        # Determine trend (would need historical data)
        historical_trend = self._calculate_trend()

        report = SystemHealthReport(
            timestamp=timestamp,
            overall_health_score=overall_health_score,
            overall_health_level=overall_health_level,
            platforms_total=platforms_total,
            platforms_active=platforms_active,
            platforms_degraded=platforms_degraded,
            platforms_failed=platforms_failed,
            critical_issues=critical_issues,
            warnings=warnings,
            recommendations=recommendations,
            platform_details=platform_metrics,
            historical_trend=historical_trend
        )

        return report

    def _calculate_trend(self) -> str:
        """Calculate health trend over time."""
        try:
            # Load recent health data to calculate trend
            health_log = load_json(self.health_log_file) if self.health_log_file.exists() else {}

            # Get health scores from last few days
            recent_scores = []
            cutoff = datetime.now() - timedelta(days=3)

            for date_str, entries in health_log.items():
                for entry in entries:
                    entry_time = datetime.fromisoformat(entry.get("timestamp", ""))
                    if entry_time >= cutoff:
                        score = entry.get("overall_health_score", 0)
                        recent_scores.append((entry_time, score))

            if len(recent_scores) < 3:
                return "insufficient_data"

            # Simple trend calculation
            recent_scores.sort(key=lambda x: x[0])
            early_avg = sum(score for _, score in recent_scores[:len(recent_scores)//3]) / (len(recent_scores)//3)
            late_avg = sum(score for _, score in recent_scores[-len(recent_scores)//3:]) / (len(recent_scores)//3)

            if late_avg > early_avg + 0.1:
                return "improving"
            elif late_avg < early_avg - 0.1:
                return "declining"
            else:
                return "stable"

        except Exception as e:
            logger.error(f"Error calculating trend: {str(e)}")
            return "unknown"

    def save_health_report(self, report: SystemHealthReport) -> None:
        """Save health report to logs."""
        try:
            # Save to detailed health log
            health_log = load_json(self.health_log_file) if self.health_log_file.exists() else {}
            today = datetime.now().strftime("%Y-%m-%d")

            if today not in health_log:
                health_log[today] = []

            # Convert dataclasses to dicts for JSON serialization
            report_dict = asdict(report)
            report_dict["platform_details"] = {
                name: asdict(metric) for name, metric in report.platform_details.items()
            }

            health_log[today].append(report_dict)

            # Keep only last 30 days
            cutoff_date = datetime.now() - timedelta(days=30)
            health_log = {
                date: entries for date, entries in health_log.items()
                if datetime.strptime(date, "%Y-%m-%d") >= cutoff_date
            }

            save_json(self.health_log_file, health_log)

            # Generate alerts if needed
            self._check_and_generate_alerts(report)

        except Exception as e:
            logger.error(f"Error saving health report: {str(e)}")

    def _check_and_generate_alerts(self, report: SystemHealthReport) -> None:
        """Check for conditions that require alerts."""
        try:
            alerts = []

            # Critical health score
            if report.overall_health_score < self.health_thresholds["critical_health_score"]:
                alerts.append({
                    "level": "critical",
                    "message": f"System health critically low: {report.overall_health_score:.3f}",
                    "timestamp": report.timestamp,
                    "action_required": True
                })

            # No active platforms
            if report.platforms_active == 0:
                alerts.append({
                    "level": "critical",
                    "message": "No platforms are currently active",
                    "timestamp": report.timestamp,
                    "action_required": True
                })

            # High number of failed platforms
            if report.platforms_failed >= report.platforms_total * 0.7:
                alerts.append({
                    "level": "warning",
                    "message": f"High platform failure rate: {report.platforms_failed}/{report.platforms_total}",
                    "timestamp": report.timestamp,
                    "action_required": False
                })

            if alerts:
                # Save alerts
                alert_log = load_json(self.alerts_file) if self.alerts_file.exists() else []
                alert_log.extend(alerts)

                # Keep only last 1000 alerts
                alert_log = alert_log[-1000:]
                save_json(self.alerts_file, alert_log)

                # Log critical alerts
                for alert in alerts:
                    if alert["level"] == "critical":
                        logger.critical(f"HEALTH ALERT: {alert['message']}")
                    else:
                        logger.warning(f"HEALTH ALERT: {alert['message']}")

        except Exception as e:
            logger.error(f"Error generating alerts: {str(e)}")

    def display_health_dashboard(self) -> None:
        """Display comprehensive health dashboard."""
        report = self.generate_health_report()

        print("=" * 80)
        print("🏥 PLATFORM HEALTH MONITOR DASHBOARD (APU-168)")
        print("=" * 80)

        # Overall health
        health_icon = {
            "excellent": "💚",
            "good": "💛",
            "degraded": "🧡",
            "critical": "🔴",
            "failed": "💀"
        }.get(report.overall_health_level, "❓")

        print(f"\n{health_icon} OVERALL HEALTH: {report.overall_health_score:.3f} ({report.overall_health_level.upper()})")
        print(f"   Trend: {report.historical_trend}")
        print(f"   Active: {report.platforms_active}, Degraded: {report.platforms_degraded}, Failed: {report.platforms_failed}")

        # Platform details
        print(f"\n📊 PLATFORM STATUS")
        for platform_name, metric in report.platform_details.items():
            status_icon = {
                "active": "✅",
                "partial": "🟡",
                "degraded": "🟠",
                "unavailable": "❌",
                "disabled": "⏸️"
            }.get(metric.status, "❓")

            uptime_str = f"↗️{metric.uptime_percentage:.1f}%" if metric.uptime_percentage > 0 else "📊0%"
            error_str = f"❌{metric.error_count}" if metric.error_count > 0 else ""

            print(f"   {status_icon} {platform_name.upper()}: {metric.health_score:.3f} ({uptime_str} {error_str})".strip())

        # Critical issues
        if report.critical_issues:
            print(f"\n🚨 CRITICAL ISSUES")
            for issue in report.critical_issues:
                print(f"   • {issue}")

        # Warnings
        if report.warnings:
            print(f"\n⚠️ WARNINGS")
            for warning in report.warnings[:5]:  # Show first 5
                print(f"   • {warning}")

        # Recommendations
        if report.recommendations:
            print(f"\n💡 RECOMMENDATIONS")
            for rec in report.recommendations[:5]:  # Show first 5
                print(f"   • {rec}")

        print(f"\n" + "=" * 80)
        print(f"Health check completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        return report

def main():
    """Main execution function for platform health monitoring."""
    print(f"Starting APU-168 Platform Health Monitor at {datetime.now()}")

    try:
        monitor = PlatformHealthMonitor()

        # Generate and display health report
        report = monitor.display_health_dashboard()

        # Save the report
        monitor.save_health_report(report)

        print(f"\nHealth monitoring completed successfully")
        return report

    except Exception as e:
        error_msg = f"Error in platform health monitor: {str(e)}"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        raise

if __name__ == "__main__":
    main()