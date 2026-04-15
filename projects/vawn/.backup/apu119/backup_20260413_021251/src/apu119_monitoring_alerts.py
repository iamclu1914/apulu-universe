"""
apu119_monitoring_alerts.py — APU-119 Comprehensive Monitoring and Alerting System

Advanced monitoring and intelligent alerting system for all APU engagement monitoring components.
Provides proactive issue detection, predictive analytics, and comprehensive system health monitoring
with smart alerting to prevent issues before they become critical.

Created by: Dex - Community Agent (APU-119)
Features:
- Real-time system health monitoring across all APU components
- Predictive alerting with machine learning-based pattern detection
- Intelligent alert prioritization and threshold management
- Comprehensive performance metrics and bottleneck detection
- Automated issue detection and resolution recommendations
- Cross-system correlation analysis and root cause identification
"""

import json
import sys
import sqlite3
import threading
import time
import smtplib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import statistics
import traceback

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import (
    load_json, save_json, VAWN_DIR, RESEARCH_DIR
)

# Import APU-119 components
try:
    from src.apu119_system_integration import APUSystemsIntegrator
    from src.apu119_engagement_monitor import ReliabilityEngine, APU119EngagementMonitor
except ImportError as e:
    print(f"Warning: Could not import APU-119 components: {e}")

# Monitoring Configuration
MONITORING_CONFIG = VAWN_DIR / "config" / "apu119_monitoring_config.json"
ALERTS_DB = VAWN_DIR / "database" / "apu119_alerts.db"
MONITORING_LOG = RESEARCH_DIR / "apu119_monitoring_log.json"
CRITICAL_ALERTS_LOG = RESEARCH_DIR / "apu119_critical_alerts.json"

# Ensure directories exist
ALERTS_DB.parent.mkdir(exist_ok=True)
RESEARCH_DIR.mkdir(exist_ok=True)

logger = logging.getLogger("APU119_Monitoring")

@dataclass
class Alert:
    """System alert with priority and metadata"""
    id: str
    alert_type: str  # performance, error, prediction, health
    severity: str   # low, medium, high, critical
    component: str
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    acknowledged: bool = False

@dataclass
class PerformanceMetric:
    """Performance metric tracking"""
    component: str
    metric_name: str
    value: float
    threshold: float
    timestamp: datetime
    trend: str  # improving, stable, degrading
    prediction: Optional[float] = None

@dataclass
class SystemThreshold:
    """System monitoring threshold"""
    component: str
    metric: str
    warning_threshold: float
    critical_threshold: float
    prediction_threshold: float
    check_interval: int

class AlertManager:
    """Intelligent alert management and prioritization"""

    def __init__(self):
        self.alerts = {}
        self.alert_history = deque(maxlen=1000)
        self.alert_counters = defaultdict(int)
        self.db_connection = None
        self.setup_database()

    def setup_database(self) -> None:
        """Setup alerts database"""
        try:
            self.db_connection = sqlite3.connect(str(ALERTS_DB), check_same_thread=False)
            cursor = self.db_connection.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    component TEXT NOT NULL,
                    message TEXT NOT NULL,
                    details TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolution_time DATETIME,
                    acknowledged BOOLEAN DEFAULT FALSE
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    component TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    threshold_value REAL NOT NULL,
                    timestamp DATETIME NOT NULL,
                    trend TEXT DEFAULT 'stable',
                    prediction REAL
                )
            ''')

            self.db_connection.commit()
            logger.info("Alerts database setup completed")

        except Exception as e:
            logger.error(f"Failed to setup alerts database: {e}")
            raise

    def create_alert(self, alert_type: str, severity: str, component: str,
                    message: str, details: Dict[str, Any]) -> Alert:
        """Create new alert with intelligent deduplication"""
        alert_id = f"{component}_{alert_type}_{int(time.time())}"

        # Check for recent similar alerts (deduplication)
        recent_alerts = [
            a for a in self.alert_history
            if a.component == component and a.alert_type == alert_type
            and (datetime.now() - a.timestamp).seconds < 300  # 5 minutes
        ]

        if recent_alerts and not any(a.severity == "critical" for a in recent_alerts):
            logger.debug(f"Suppressing duplicate alert: {component}_{alert_type}")
            return recent_alerts[-1]

        alert = Alert(
            id=alert_id,
            alert_type=alert_type,
            severity=severity,
            component=component,
            message=message,
            details=details,
            timestamp=datetime.now()
        )

        # Store alert
        self.alerts[alert_id] = alert
        self.alert_history.append(alert)
        self.alert_counters[f"{component}_{alert_type}"] += 1

        # Save to database
        try:
            cursor = self.db_connection.cursor()
            cursor.execute('''
                INSERT INTO alerts (id, alert_type, severity, component, message, details, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert.id, alert.alert_type, alert.severity, alert.component,
                alert.message, json.dumps(alert.details), alert.timestamp
            ))
            self.db_connection.commit()
        except Exception as e:
            logger.error(f"Failed to save alert to database: {e}")

        logger.warning(f"Alert created: {severity.upper()} - {component} - {message}")
        return alert

    def resolve_alert(self, alert_id: str, resolution_note: str = "") -> bool:
        """Resolve an active alert"""
        if alert_id in self.alerts:
            alert = self.alerts[alert_id]
            alert.resolved = True
            alert.resolution_time = datetime.now()

            if resolution_note:
                alert.details["resolution_note"] = resolution_note

            # Update database
            try:
                cursor = self.db_connection.cursor()
                cursor.execute('''
                    UPDATE alerts SET resolved = TRUE, resolution_time = ?
                    WHERE id = ?
                ''', (alert.resolution_time, alert_id))
                self.db_connection.commit()
            except Exception as e:
                logger.error(f"Failed to update alert resolution: {e}")

            logger.info(f"Alert resolved: {alert_id}")
            return True

        return False

    def get_active_alerts(self, severity_filter: Optional[str] = None) -> List[Alert]:
        """Get all active (unresolved) alerts"""
        active_alerts = [alert for alert in self.alerts.values() if not alert.resolved]

        if severity_filter:
            active_alerts = [alert for alert in active_alerts if alert.severity == severity_filter]

        # Sort by severity and timestamp
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        active_alerts.sort(
            key=lambda x: (severity_order.get(x.severity, 0), x.timestamp),
            reverse=True
        )

        return active_alerts

    def get_alert_summary(self) -> Dict[str, Any]:
        """Get comprehensive alert summary"""
        active_alerts = self.get_active_alerts()

        severity_counts = defaultdict(int)
        component_counts = defaultdict(int)

        for alert in active_alerts:
            severity_counts[alert.severity] += 1
            component_counts[alert.component] += 1

        return {
            "total_active": len(active_alerts),
            "by_severity": dict(severity_counts),
            "by_component": dict(component_counts),
            "most_alerts_component": max(component_counts.items(), key=lambda x: x[1])[0] if component_counts else None,
            "oldest_alert": min(active_alerts, key=lambda x: x.timestamp).timestamp.isoformat() if active_alerts else None
        }

class PerformanceMonitor:
    """Advanced performance monitoring with predictive analytics"""

    def __init__(self, alert_manager: AlertManager):
        self.alert_manager = alert_manager
        self.performance_history = defaultdict(lambda: deque(maxlen=100))
        self.thresholds = {}
        self.load_thresholds()

    def load_thresholds(self) -> None:
        """Load monitoring thresholds configuration"""
        default_thresholds = {
            "apu101": {
                "response_time": SystemThreshold("apu101", "response_time", 2.0, 5.0, 4.0, 60),
                "error_rate": SystemThreshold("apu101", "error_rate", 0.05, 0.15, 0.10, 60),
                "coordination_success": SystemThreshold("apu101", "coordination_success", 0.90, 0.70, 0.80, 120)
            },
            "apu112": {
                "response_time": SystemThreshold("apu112", "response_time", 1.5, 4.0, 3.0, 60),
                "data_freshness": SystemThreshold("apu112", "data_freshness", 300, 900, 600, 60),
                "metrics_availability": SystemThreshold("apu112", "metrics_availability", 0.95, 0.80, 0.85, 120)
            },
            "apu113": {
                "response_time": SystemThreshold("apu113", "response_time", 3.0, 8.0, 6.0, 60),
                "intelligence_score": SystemThreshold("apu113", "intelligence_score", 7.0, 4.0, 5.5, 300),
                "consolidation_health": SystemThreshold("apu113", "consolidation_health", 0.90, 0.60, 0.75, 180)
            },
            "apu119": {
                "response_time": SystemThreshold("apu119", "response_time", 1.0, 3.0, 2.0, 60),
                "integration_health": SystemThreshold("apu119", "integration_health", 0.95, 0.75, 0.85, 120),
                "optimization_score": SystemThreshold("apu119", "optimization_score", 8.0, 5.0, 6.5, 300)
            }
        }

        try:
            if MONITORING_CONFIG.exists():
                config = load_json(MONITORING_CONFIG)
                thresholds_config = config.get("thresholds", default_thresholds)
            else:
                thresholds_config = default_thresholds
                save_json(MONITORING_CONFIG, {"thresholds": thresholds_config})

            # Convert to SystemThreshold objects
            for component, metrics in thresholds_config.items():
                self.thresholds[component] = {}
                for metric_name, threshold_data in metrics.items():
                    if isinstance(threshold_data, dict):
                        self.thresholds[component][metric_name] = SystemThreshold(
                            component=component,
                            metric=metric_name,
                            warning_threshold=threshold_data.get("warning_threshold", 1.0),
                            critical_threshold=threshold_data.get("critical_threshold", 2.0),
                            prediction_threshold=threshold_data.get("prediction_threshold", 1.5),
                            check_interval=threshold_data.get("check_interval", 60)
                        )
                    else:
                        self.thresholds[component][metric_name] = threshold_data

        except Exception as e:
            logger.error(f"Failed to load thresholds, using defaults: {e}")
            self.thresholds = default_thresholds

    def record_metric(self, component: str, metric_name: str, value: float) -> None:
        """Record performance metric with trend analysis"""
        try:
            timestamp = datetime.now()
            threshold = self.thresholds.get(component, {}).get(metric_name)

            if not threshold:
                logger.warning(f"No threshold configured for {component}.{metric_name}")
                return

            # Add to history
            metric_key = f"{component}_{metric_name}"
            self.performance_history[metric_key].append((timestamp, value))

            # Calculate trend
            trend = self._calculate_trend(metric_key)
            prediction = self._predict_next_value(metric_key)

            # Create performance metric
            perf_metric = PerformanceMetric(
                component=component,
                metric_name=metric_name,
                value=value,
                threshold=threshold.warning_threshold,
                timestamp=timestamp,
                trend=trend,
                prediction=prediction
            )

            # Check thresholds and create alerts
            self._check_thresholds(perf_metric, threshold)

            # Store in database
            self._save_performance_metric(perf_metric, threshold)

        except Exception as e:
            logger.error(f"Failed to record metric {component}.{metric_name}: {e}")

    def _calculate_trend(self, metric_key: str, window: int = 10) -> str:
        """Calculate trend for performance metric"""
        history = list(self.performance_history[metric_key])
        if len(history) < window:
            return "stable"

        recent_values = [value for _, value in history[-window:]]
        older_values = [value for _, value in history[-window*2:-window]] if len(history) >= window*2 else recent_values

        recent_avg = statistics.mean(recent_values)
        older_avg = statistics.mean(older_values)

        if recent_avg > older_avg * 1.1:
            return "degrading" if metric_key.endswith("_time") or metric_key.endswith("_rate") else "improving"
        elif recent_avg < older_avg * 0.9:
            return "improving" if metric_key.endswith("_time") or metric_key.endswith("_rate") else "degrading"
        else:
            return "stable"

    def _predict_next_value(self, metric_key: str, steps_ahead: int = 3) -> Optional[float]:
        """Simple linear prediction for next value"""
        history = list(self.performance_history[metric_key])
        if len(history) < 5:
            return None

        # Use simple linear regression on recent points
        recent_points = history[-10:]  # Last 10 points
        x_values = list(range(len(recent_points)))
        y_values = [value for _, value in recent_points]

        n = len(recent_points)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)

        # Linear regression: y = mx + b
        m = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        b = (sum_y - m * sum_x) / n

        # Predict steps ahead
        prediction = m * (n + steps_ahead - 1) + b
        return max(0, prediction)  # Ensure non-negative

    def _check_thresholds(self, metric: PerformanceMetric, threshold: SystemThreshold) -> None:
        """Check performance thresholds and create alerts"""
        # Critical threshold
        if metric.value >= threshold.critical_threshold:
            self.alert_manager.create_alert(
                alert_type="performance",
                severity="critical",
                component=metric.component,
                message=f"{metric.metric_name} critical: {metric.value:.3f} >= {threshold.critical_threshold}",
                details={
                    "metric": metric.metric_name,
                    "current_value": metric.value,
                    "threshold": threshold.critical_threshold,
                    "trend": metric.trend,
                    "prediction": metric.prediction
                }
            )

        # Warning threshold
        elif metric.value >= threshold.warning_threshold:
            self.alert_manager.create_alert(
                alert_type="performance",
                severity="high" if metric.trend == "degrading" else "medium",
                component=metric.component,
                message=f"{metric.metric_name} warning: {metric.value:.3f} >= {threshold.warning_threshold}",
                details={
                    "metric": metric.metric_name,
                    "current_value": metric.value,
                    "threshold": threshold.warning_threshold,
                    "trend": metric.trend,
                    "prediction": metric.prediction
                }
            )

        # Predictive alert
        elif metric.prediction and metric.prediction >= threshold.prediction_threshold:
            self.alert_manager.create_alert(
                alert_type="prediction",
                severity="medium",
                component=metric.component,
                message=f"{metric.metric_name} predicted to reach {metric.prediction:.3f} (threshold: {threshold.prediction_threshold})",
                details={
                    "metric": metric.metric_name,
                    "current_value": metric.value,
                    "predicted_value": metric.prediction,
                    "threshold": threshold.prediction_threshold,
                    "trend": metric.trend
                }
            )

    def _save_performance_metric(self, metric: PerformanceMetric, threshold: SystemThreshold) -> None:
        """Save performance metric to database"""
        try:
            cursor = self.alert_manager.db_connection.cursor()
            cursor.execute('''
                INSERT INTO performance_metrics
                (component, metric_name, value, threshold_value, timestamp, trend, prediction)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                metric.component, metric.metric_name, metric.value,
                threshold.warning_threshold, metric.timestamp, metric.trend, metric.prediction
            ))
            self.alert_manager.db_connection.commit()
        except Exception as e:
            logger.error(f"Failed to save performance metric: {e}")

    def get_performance_summary(self, component: Optional[str] = None) -> Dict[str, Any]:
        """Get performance summary for components"""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "components": {},
            "overall_trend": "stable"
        }

        degrading_count = 0
        total_metrics = 0

        for metric_key, history in self.performance_history.items():
            comp_name, metric_name = metric_key.split("_", 1)

            if component and comp_name != component:
                continue

            if comp_name not in summary["components"]:
                summary["components"][comp_name] = {}

            if history:
                latest_value = history[-1][1]
                trend = self._calculate_trend(metric_key)
                prediction = self._predict_next_value(metric_key)

                summary["components"][comp_name][metric_name] = {
                    "current_value": latest_value,
                    "trend": trend,
                    "prediction": prediction,
                    "data_points": len(history)
                }

                if trend == "degrading":
                    degrading_count += 1
                total_metrics += 1

        # Calculate overall trend
        if total_metrics > 0:
            degrading_ratio = degrading_count / total_metrics
            if degrading_ratio > 0.3:
                summary["overall_trend"] = "degrading"
            elif degrading_ratio < 0.1:
                summary["overall_trend"] = "improving"

        return summary

class APU119MonitoringSystem:
    """Main comprehensive monitoring and alerting system"""

    def __init__(self):
        self.alert_manager = AlertManager()
        self.performance_monitor = PerformanceMonitor(self.alert_manager)
        self.integrator = None
        self.monitoring_thread = None
        self.is_monitoring = False

        try:
            self.integrator = APUSystemsIntegrator()
        except Exception as e:
            logger.warning(f"Could not initialize integrator: {e}")

    def start_monitoring(self, interval: int = 60) -> None:
        """Start continuous monitoring"""
        if self.is_monitoring:
            logger.warning("Monitoring already running")
            return

        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop, args=(interval,), daemon=True
        )
        self.monitoring_thread.start()
        logger.info(f"Monitoring started with {interval}s interval")

    def stop_monitoring(self) -> None:
        """Stop continuous monitoring"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("Monitoring stopped")

    def _monitoring_loop(self, interval: int) -> None:
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                self._run_monitoring_cycle()
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Monitoring cycle failed: {e}")
                time.sleep(interval)

    def _run_monitoring_cycle(self) -> None:
        """Run single monitoring cycle"""
        if not self.integrator:
            return

        try:
            # Sync all APU systems
            integration_status = self.integrator.sync_all_systems()

            # Monitor each system
            for system_name, status in integration_status['systems'].items():
                self._monitor_system(system_name, status)

            # Check overall integration health
            self._monitor_integration_health(integration_status)

            # Log monitoring status
            self._log_monitoring_status(integration_status)

        except Exception as e:
            logger.error(f"Monitoring cycle error: {e}")
            self.alert_manager.create_alert(
                alert_type="error",
                severity="high",
                component="monitoring",
                message=f"Monitoring cycle failed: {str(e)}",
                details={"error": str(e), "traceback": traceback.format_exc()}
            )

    def _monitor_system(self, system_name: str, status: Dict[str, Any]) -> None:
        """Monitor individual APU system"""
        component = system_name.lower().replace("-", "")

        # Record performance metrics
        self.performance_monitor.record_metric(component, "response_time", status['response_time'])

        # Check system status
        if status['status'] == "error":
            self.alert_manager.create_alert(
                alert_type="error",
                severity="high",
                component=component,
                message=f"{system_name} system error: {status['details'].get('error', 'Unknown error')}",
                details=status['details']
            )
        elif status['status'] == "no_data":
            self.alert_manager.create_alert(
                alert_type="health",
                severity="medium",
                component=component,
                message=f"{system_name} has no data available",
                details=status['details']
            )

        # Monitor error count
        if status['error_count'] > 0:
            self.performance_monitor.record_metric(component, "error_rate", status['error_count'] / 10.0)

    def _monitor_integration_health(self, integration_status: Dict[str, Any]) -> None:
        """Monitor overall integration health"""
        overall_status = integration_status['overall_status']
        active_systems = integration_status['active_systems']
        total_systems = integration_status['total_systems']

        # Record integration metrics
        health_score = active_systems / total_systems if total_systems > 0 else 0
        self.performance_monitor.record_metric("apu119", "integration_health", health_score)

        # Create alerts for integration issues
        if overall_status == "degraded":
            self.alert_manager.create_alert(
                alert_type="health",
                severity="high" if health_score < 0.5 else "medium",
                component="apu119",
                message=f"Integration health degraded: {active_systems}/{total_systems} systems active",
                details={
                    "active_systems": active_systems,
                    "total_systems": total_systems,
                    "health_score": health_score
                }
            )

    def _log_monitoring_status(self, integration_status: Dict[str, Any]) -> None:
        """Log monitoring status to research files"""
        try:
            monitoring_entry = {
                "timestamp": datetime.now().isoformat(),
                "integration_status": integration_status,
                "alert_summary": self.alert_manager.get_alert_summary(),
                "performance_summary": self.performance_monitor.get_performance_summary()
            }

            # Load existing log
            if MONITORING_LOG.exists():
                log_data = load_json(MONITORING_LOG)
            else:
                log_data = {}

            today = datetime.now().strftime("%Y-%m-%d")
            if today not in log_data:
                log_data[today] = []

            log_data[today].append(monitoring_entry)

            # Keep only last 7 days
            cutoff_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            log_data = {date: entries for date, entries in log_data.items() if date >= cutoff_date}

            save_json(MONITORING_LOG, log_data)

            # Save critical alerts separately
            critical_alerts = self.alert_manager.get_active_alerts("critical")
            if critical_alerts:
                critical_data = {
                    "timestamp": datetime.now().isoformat(),
                    "critical_alerts": [asdict(alert) for alert in critical_alerts]
                }
                save_json(CRITICAL_ALERTS_LOG, critical_data)

        except Exception as e:
            logger.error(f"Failed to log monitoring status: {e}")

    def get_monitoring_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive monitoring dashboard data"""
        active_alerts = self.alert_manager.get_active_alerts()
        alert_summary = self.alert_manager.get_alert_summary()
        performance_summary = self.performance_monitor.get_performance_summary()

        return {
            "timestamp": datetime.now().isoformat(),
            "monitoring_status": "active" if self.is_monitoring else "inactive",
            "system_health": {
                "total_alerts": alert_summary["total_active"],
                "critical_alerts": alert_summary["by_severity"].get("critical", 0),
                "degraded_components": len([c for c, m in performance_summary["components"].items()
                                         if any(metric["trend"] == "degrading" for metric in m.values())]),
                "overall_trend": performance_summary["overall_trend"]
            },
            "alerts": {
                "active_alerts": [asdict(alert) for alert in active_alerts[:10]],  # Latest 10
                "summary": alert_summary
            },
            "performance": performance_summary,
            "recommendations": self._generate_recommendations(active_alerts, performance_summary)
        }

    def _generate_recommendations(self, alerts: List[Alert], performance: Dict[str, Any]) -> List[str]:
        """Generate intelligent recommendations based on monitoring data"""
        recommendations = []

        # Alert-based recommendations
        critical_alerts = [a for a in alerts if a.severity == "critical"]
        if critical_alerts:
            recommendations.append(f"🚨 Immediate attention needed: {len(critical_alerts)} critical alerts active")

        error_alerts = [a for a in alerts if a.alert_type == "error"]
        if len(error_alerts) > 3:
            recommendations.append(f"🔧 System stability issues: {len(error_alerts)} error alerts detected")

        # Performance-based recommendations
        degrading_components = []
        for component, metrics in performance.get("components", {}).items():
            degrading_metrics = [m for m, data in metrics.items() if data.get("trend") == "degrading"]
            if degrading_metrics:
                degrading_components.append(f"{component}: {', '.join(degrading_metrics)}")

        if degrading_components:
            recommendations.append(f"📉 Performance degradation in: {'; '.join(degrading_components)}")

        # Predictive recommendations
        prediction_alerts = [a for a in alerts if a.alert_type == "prediction"]
        if prediction_alerts:
            recommendations.append(f"🔮 Proactive action recommended: {len(prediction_alerts)} predictive alerts")

        if not recommendations:
            recommendations.append("✅ All systems operating normally")

        return recommendations

def main():
    """Main monitoring system demonstration"""
    print("\n=== APU-119 Comprehensive Monitoring and Alerting System ===")
    print("Advanced monitoring with predictive analytics and intelligent alerting")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    try:
        # Initialize monitoring system
        monitor = APU119MonitoringSystem()

        print("✅ Alert manager initialized")
        print("✅ Performance monitor ready")
        print("✅ Database connections established")

        # Run initial monitoring cycle
        print("\n🔄 Running initial monitoring cycle...")
        monitor._run_monitoring_cycle()

        # Get monitoring dashboard
        dashboard = monitor.get_monitoring_dashboard()

        print(f"\n📊 Monitoring Dashboard:")
        print(f"   System Health: {dashboard['system_health']['overall_trend'].upper()}")
        print(f"   Total Alerts: {dashboard['system_health']['total_alerts']}")
        print(f"   Critical Alerts: {dashboard['system_health']['critical_alerts']}")
        print(f"   Degraded Components: {dashboard['system_health']['degraded_components']}")

        print(f"\n💡 Recommendations:")
        for rec in dashboard['recommendations']:
            print(f"   • {rec}")

        print(f"\n✅ Monitoring system ready!")
        print(f"📊 Monitoring logs: {MONITORING_LOG}")
        print(f"📊 Alerts database: {ALERTS_DB}")

        return {"status": "success", "dashboard": dashboard}

    except Exception as e:
        print(f"\n❌ Monitoring system initialization failed: {e}")
        logger.error(f"Monitoring failed: {e}")
        return {"status": "failed", "error": str(e)}

if __name__ == "__main__":
    result = main()
    sys.exit(0 if result["status"] == "success" else 1)