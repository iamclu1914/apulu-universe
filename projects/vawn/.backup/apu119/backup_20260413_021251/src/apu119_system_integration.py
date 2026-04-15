"""
apu119_system_integration.py — APU Systems Integration Layer

Handles seamless integration and data flow between APU-119 and existing APU systems
(APU-101, APU-112, APU-113). Provides unified data access, real-time synchronization,
and enhanced coordination between all engagement monitoring components.

Created by: Dex - Community Agent (APU-119)
Integration Points:
- APU-101: Engagement coordination data and real-time status
- APU-112: Metrics aggregation and performance data
- APU-113: Intelligence dashboard data and consolidated insights
- Cross-system data flow optimization and reliability enhancement
"""

import json
import sys
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import (
    load_json, save_json, VAWN_DIR, RESEARCH_DIR
)

# APU Integration Configuration
APU101_LOG = RESEARCH_DIR / "apu101_engagement_monitor_log.json"
APU101_STATUS = RESEARCH_DIR / "apu101_coordinator_status.json"
APU112_DB = VAWN_DIR / "database" / "apu112_engagement_metrics.db"
APU113_DB = VAWN_DIR / "database" / "apu113_engagement_intelligence.db"
APU113_LOG = RESEARCH_DIR / "apu113_intelligence_log.json"

# APU-119 Integration Outputs
APU119_INTEGRATION_LOG = RESEARCH_DIR / "apu119_integration_log.json"
APU119_UNIFIED_METRICS = RESEARCH_DIR / "apu119_unified_metrics.json"

logger = logging.getLogger("APU119_Integration")

@dataclass
class APUSystemStatus:
    """Status of APU system integration"""
    system_name: str
    status: str  # active, inactive, degraded, error
    last_sync: datetime
    data_points: int
    error_count: int
    response_time: float
    details: Dict[str, Any]

@dataclass
class UnifiedMetrics:
    """Unified metrics across all APU systems"""
    timestamp: datetime
    apu101_coordination: Dict[str, Any]
    apu112_metrics: Dict[str, Any]
    apu113_intelligence: Dict[str, Any]
    apu119_optimization: Dict[str, Any]
    cross_system_health: Dict[str, Any]

class APU101Integration:
    """Integration with APU-101 Engagement Coordinator"""

    def __init__(self):
        self.last_sync = None
        self.coordination_data = {}

    def fetch_coordination_data(self) -> Dict[str, Any]:
        """Fetch latest coordination data from APU-101"""
        try:
            coordination_data = {"status": "no_data", "metrics": {}}

            # Load APU-101 status
            if APU101_STATUS.exists():
                status_data = load_json(APU101_STATUS)
                coordination_data["coordinator_status"] = status_data
                coordination_data["status"] = "active"

            # Load APU-101 logs
            if APU101_LOG.exists():
                log_data = load_json(APU101_LOG)
                if log_data:
                    latest_date = max(log_data.keys())
                    latest_entries = log_data[latest_date]
                    if latest_entries:
                        coordination_data["latest_metrics"] = latest_entries[-1]
                        coordination_data["log_entries"] = len(latest_entries)

            # Extract key coordination metrics
            if "latest_metrics" in coordination_data:
                metrics = coordination_data["latest_metrics"]
                coordination_data["metrics"] = {
                    "system_integration": metrics.get("system_integration", {}),
                    "unified_metrics": metrics.get("unified_metrics", {}),
                    "department_coordination": metrics.get("department_coordination", {}),
                    "alerts": len(metrics.get("alerts", [])),
                    "recommendations": len(metrics.get("recommendations", []))
                }

            self.coordination_data = coordination_data
            self.last_sync = datetime.now()
            return coordination_data

        except Exception as e:
            logger.error(f"Failed to fetch APU-101 data: {e}")
            return {"status": "error", "error": str(e), "metrics": {}}

    def get_real_time_status(self) -> Dict[str, Any]:
        """Get real-time APU-101 system status"""
        return {
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "data_available": bool(self.coordination_data),
            "coordinator_active": self.coordination_data.get("status") == "active",
            "metrics_count": len(self.coordination_data.get("metrics", {}))
        }

class APU112Integration:
    """Integration with APU-112 Engagement Metrics Aggregator"""

    def __init__(self):
        self.last_sync = None
        self.metrics_data = {}
        self.db_connection = None

    def connect_to_database(self) -> bool:
        """Connect to APU-112 database"""
        try:
            if APU112_DB.exists():
                self.db_connection = sqlite3.connect(str(APU112_DB), check_same_thread=False)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to connect to APU-112 database: {e}")
            return False

    def fetch_metrics_data(self) -> Dict[str, Any]:
        """Fetch latest metrics data from APU-112"""
        try:
            metrics_data = {"status": "no_data", "metrics": {}}

            if not self.db_connection:
                if not self.connect_to_database():
                    return {"status": "no_database", "metrics": {}}

            cursor = self.db_connection.cursor()

            # Get recent engagement metrics (last 24 hours)
            cursor.execute('''
                SELECT platform, timestamp, engagement_rate, sentiment_score, response_time
                FROM engagement_metrics
                WHERE timestamp > datetime('now', '-24 hours')
                ORDER BY timestamp DESC
                LIMIT 100
            ''')

            recent_metrics = cursor.fetchall()
            if recent_metrics:
                metrics_data["status"] = "active"
                metrics_data["recent_metrics"] = [
                    {
                        "platform": row[0],
                        "timestamp": row[1],
                        "engagement_rate": row[2],
                        "sentiment_score": row[3],
                        "response_time": row[4]
                    } for row in recent_metrics
                ]

                # Calculate aggregated metrics
                total_engagement = sum(row[2] for row in recent_metrics if row[2])
                avg_sentiment = sum(row[3] for row in recent_metrics if row[3]) / len(recent_metrics)
                avg_response_time = sum(row[4] for row in recent_metrics if row[4]) / len(recent_metrics)

                metrics_data["metrics"] = {
                    "total_engagement_rate": total_engagement,
                    "average_sentiment": avg_sentiment,
                    "average_response_time": avg_response_time,
                    "data_points": len(recent_metrics)
                }

            self.metrics_data = metrics_data
            self.last_sync = datetime.now()
            return metrics_data

        except Exception as e:
            logger.error(f"Failed to fetch APU-112 data: {e}")
            return {"status": "error", "error": str(e), "metrics": {}}

    def get_real_time_status(self) -> Dict[str, Any]:
        """Get real-time APU-112 system status"""
        return {
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "database_connected": bool(self.db_connection),
            "data_available": bool(self.metrics_data),
            "metrics_active": self.metrics_data.get("status") == "active",
            "data_points": len(self.metrics_data.get("recent_metrics", []))
        }

class APU113Integration:
    """Integration with APU-113 Engagement Intelligence Dashboard"""

    def __init__(self):
        self.last_sync = None
        self.intelligence_data = {}
        self.db_connection = None

    def connect_to_database(self) -> bool:
        """Connect to APU-113 database"""
        try:
            if APU113_DB.exists():
                self.db_connection = sqlite3.connect(str(APU113_DB), check_same_thread=False)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to connect to APU-113 database: {e}")
            return False

    def fetch_intelligence_data(self) -> Dict[str, Any]:
        """Fetch latest intelligence data from APU-113"""
        try:
            intelligence_data = {"status": "no_data", "intelligence": {}}

            # Try database connection first
            if not self.db_connection:
                self.connect_to_database()

            # Try log file if database not available
            if APU113_LOG.exists():
                log_data = load_json(APU113_LOG)
                if log_data:
                    intelligence_data["status"] = "active"
                    latest_date = max(log_data.keys())
                    latest_entries = log_data[latest_date]
                    if latest_entries:
                        intelligence_data["latest_intelligence"] = latest_entries[-1]

                        # Extract intelligence metrics
                        latest = latest_entries[-1]
                        intelligence_data["intelligence"] = {
                            "consolidation_status": latest.get("consolidation_status", "unknown"),
                            "predictive_insights": latest.get("predictive_insights", {}),
                            "strategic_recommendations": len(latest.get("recommendations", [])),
                            "cross_platform_analysis": latest.get("cross_platform_analysis", {}),
                            "intelligence_score": latest.get("intelligence_score", 0)
                        }

            self.intelligence_data = intelligence_data
            self.last_sync = datetime.now()
            return intelligence_data

        except Exception as e:
            logger.error(f"Failed to fetch APU-113 data: {e}")
            return {"status": "error", "error": str(e), "intelligence": {}}

    def get_real_time_status(self) -> Dict[str, Any]:
        """Get real-time APU-113 system status"""
        return {
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "database_connected": bool(self.db_connection),
            "data_available": bool(self.intelligence_data),
            "intelligence_active": self.intelligence_data.get("status") == "active",
            "intelligence_score": self.intelligence_data.get("intelligence", {}).get("intelligence_score", 0)
        }

class APUSystemsIntegrator:
    """Main APU systems integration coordinator"""

    def __init__(self):
        self.apu101 = APU101Integration()
        self.apu112 = APU112Integration()
        self.apu113 = APU113Integration()
        self.last_unified_sync = None
        self.integration_status = {}

    def sync_all_systems(self) -> Dict[str, Any]:
        """Synchronize data from all APU systems"""
        logger.info("Starting unified APU systems synchronization...")

        sync_results = {}
        start_time = time.time()

        # Sync APU-101 (Coordination)
        try:
            apu101_start = time.time()
            apu101_data = self.apu101.fetch_coordination_data()
            apu101_time = time.time() - apu101_start

            sync_results["apu101"] = APUSystemStatus(
                system_name="APU-101",
                status=apu101_data["status"],
                last_sync=datetime.now(),
                data_points=len(apu101_data.get("metrics", {})),
                error_count=1 if apu101_data["status"] == "error" else 0,
                response_time=apu101_time,
                details=apu101_data
            )
        except Exception as e:
            sync_results["apu101"] = APUSystemStatus(
                system_name="APU-101",
                status="error",
                last_sync=datetime.now(),
                data_points=0,
                error_count=1,
                response_time=0.0,
                details={"error": str(e)}
            )

        # Sync APU-112 (Metrics)
        try:
            apu112_start = time.time()
            apu112_data = self.apu112.fetch_metrics_data()
            apu112_time = time.time() - apu112_start

            sync_results["apu112"] = APUSystemStatus(
                system_name="APU-112",
                status=apu112_data["status"],
                last_sync=datetime.now(),
                data_points=len(apu112_data.get("recent_metrics", [])),
                error_count=1 if apu112_data["status"] == "error" else 0,
                response_time=apu112_time,
                details=apu112_data
            )
        except Exception as e:
            sync_results["apu112"] = APUSystemStatus(
                system_name="APU-112",
                status="error",
                last_sync=datetime.now(),
                data_points=0,
                error_count=1,
                response_time=0.0,
                details={"error": str(e)}
            )

        # Sync APU-113 (Intelligence)
        try:
            apu113_start = time.time()
            apu113_data = self.apu113.fetch_intelligence_data()
            apu113_time = time.time() - apu113_start

            sync_results["apu113"] = APUSystemStatus(
                system_name="APU-113",
                status=apu113_data["status"],
                last_sync=datetime.now(),
                data_points=len(apu113_data.get("intelligence", {})),
                error_count=1 if apu113_data["status"] == "error" else 0,
                response_time=apu113_time,
                details=apu113_data
            )
        except Exception as e:
            sync_results["apu113"] = APUSystemStatus(
                system_name="APU-113",
                status="error",
                last_sync=datetime.now(),
                data_points=0,
                error_count=1,
                response_time=0.0,
                details={"error": str(e)}
            )

        # Calculate overall integration status
        total_time = time.time() - start_time
        active_systems = sum(1 for status in sync_results.values() if status.status in ["active", "no_data"])
        total_systems = len(sync_results)

        self.integration_status = {
            "overall_status": "healthy" if active_systems == total_systems else "degraded",
            "active_systems": active_systems,
            "total_systems": total_systems,
            "total_sync_time": total_time,
            "timestamp": datetime.now().isoformat(),
            "systems": {name: asdict(status) for name, status in sync_results.items()}
        }

        self.last_unified_sync = datetime.now()

        logger.info(f"APU systems sync completed: {active_systems}/{total_systems} systems active ({total_time:.2f}s)")

        return self.integration_status

    def generate_unified_metrics(self) -> Dict[str, Any]:
        """Generate unified metrics across all APU systems"""
        if not self.integration_status:
            self.sync_all_systems()

        unified_metrics = {
            "timestamp": datetime.now().isoformat(),
            "integration_health": self.integration_status["overall_status"],
            "systems_status": {}
        }

        # APU-101 coordination metrics
        apu101_status = self.integration_status["systems"].get("apu101", {})
        if apu101_status.get("status") == "active":
            apu101_details = apu101_status.get("details", {})
            unified_metrics["coordination"] = {
                "alerts": apu101_details.get("metrics", {}).get("alerts", 0),
                "recommendations": apu101_details.get("metrics", {}).get("recommendations", 0),
                "integration_status": apu101_details.get("metrics", {}).get("system_integration", {})
            }

        # APU-112 metrics aggregation
        apu112_status = self.integration_status["systems"].get("apu112", {})
        if apu112_status.get("status") == "active":
            apu112_details = apu112_status.get("details", {})
            unified_metrics["engagement"] = {
                "total_engagement_rate": apu112_details.get("metrics", {}).get("total_engagement_rate", 0),
                "average_sentiment": apu112_details.get("metrics", {}).get("average_sentiment", 5.0),
                "average_response_time": apu112_details.get("metrics", {}).get("average_response_time", 0),
                "data_points": apu112_details.get("metrics", {}).get("data_points", 0)
            }

        # APU-113 intelligence insights
        apu113_status = self.integration_status["systems"].get("apu113", {})
        if apu113_status.get("status") == "active":
            apu113_details = apu113_status.get("details", {})
            unified_metrics["intelligence"] = {
                "consolidation_status": apu113_details.get("intelligence", {}).get("consolidation_status", "unknown"),
                "strategic_recommendations": apu113_details.get("intelligence", {}).get("strategic_recommendations", 0),
                "intelligence_score": apu113_details.get("intelligence", {}).get("intelligence_score", 0)
            }

        # APU-119 optimization contributions
        unified_metrics["optimization"] = {
            "integration_active": True,
            "systems_monitored": len(self.integration_status["systems"]),
            "overall_health": self.integration_status["overall_status"],
            "last_sync": self.last_unified_sync.isoformat() if self.last_unified_sync else None
        }

        return unified_metrics

    def log_integration_status(self) -> None:
        """Log integration status to research files"""
        try:
            # Log to integration-specific log
            if APU119_INTEGRATION_LOG.exists():
                log_data = load_json(APU119_INTEGRATION_LOG)
            else:
                log_data = {}

            today = datetime.now().strftime("%Y-%m-%d")
            if today not in log_data:
                log_data[today] = []

            integration_entry = {
                "timestamp": datetime.now().isoformat(),
                "integration_status": self.integration_status,
                "unified_metrics": self.generate_unified_metrics()
            }

            log_data[today].append(integration_entry)
            save_json(APU119_INTEGRATION_LOG, log_data)

            # Save unified metrics separately
            save_json(APU119_UNIFIED_METRICS, integration_entry["unified_metrics"])

            logger.info(f"Integration status logged: {APU119_INTEGRATION_LOG}")

        except Exception as e:
            logger.error(f"Failed to log integration status: {e}")

    def get_integration_summary(self) -> Dict[str, Any]:
        """Get comprehensive integration summary"""
        if not self.integration_status:
            self.sync_all_systems()

        summary = {
            "integration_health": self.integration_status["overall_status"],
            "systems": {},
            "unified_metrics": self.generate_unified_metrics(),
            "recommendations": []
        }

        # System-specific summaries
        for system_name, status in self.integration_status["systems"].items():
            summary["systems"][system_name] = {
                "status": status["status"],
                "response_time": status["response_time"],
                "data_points": status["data_points"],
                "error_count": status["error_count"]
            }

            # Add recommendations based on status
            if status["status"] == "error":
                summary["recommendations"].append(f"Investigate {system_name} integration errors")
            elif status["status"] == "no_data":
                summary["recommendations"].append(f"Verify {system_name} data availability")
            elif status["response_time"] > 5.0:
                summary["recommendations"].append(f"Optimize {system_name} response performance")

        return summary

def main():
    """Main integration test and demonstration"""
    print("\n=== APU-119 Systems Integration Layer ===")
    print("Testing integration with APU-101, APU-112, and APU-113")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    try:
        # Initialize integrator
        integrator = APUSystemsIntegrator()

        print("🔄 Synchronizing with all APU systems...")
        integration_status = integrator.sync_all_systems()

        print(f"\n📊 Integration Results:")
        print(f"   Overall Status: {integration_status['overall_status'].upper()}")
        print(f"   Active Systems: {integration_status['active_systems']}/{integration_status['total_systems']}")
        print(f"   Total Sync Time: {integration_status['total_sync_time']:.2f}s")

        for system_name, status in integration_status['systems'].items():
            status_icon = "✅" if status['status'] == "active" else "⚠️" if status['status'] == "no_data" else "❌"
            print(f"   {status_icon} {system_name}: {status['status']} ({status['response_time']:.3f}s, {status['data_points']} data points)")

        # Generate unified metrics
        print(f"\n🧠 Generating unified metrics...")
        unified_metrics = integrator.generate_unified_metrics()

        print(f"   Coordination Alerts: {unified_metrics.get('coordination', {}).get('alerts', 'N/A')}")
        print(f"   Engagement Data Points: {unified_metrics.get('engagement', {}).get('data_points', 'N/A')}")
        print(f"   Intelligence Score: {unified_metrics.get('intelligence', {}).get('intelligence_score', 'N/A')}")

        # Log integration status
        integrator.log_integration_status()

        # Get summary with recommendations
        summary = integrator.get_integration_summary()

        if summary["recommendations"]:
            print(f"\n💡 Recommendations:")
            for rec in summary["recommendations"]:
                print(f"   • {rec}")

        print(f"\n✅ APU systems integration test completed successfully!")
        print(f"📊 Integration logs: {APU119_INTEGRATION_LOG}")
        print(f"📊 Unified metrics: {APU119_UNIFIED_METRICS}")

        return {"status": "success", "integration_summary": summary}

    except Exception as e:
        print(f"\n❌ APU systems integration failed: {e}")
        logger.error(f"Integration failed: {e}")
        return {"status": "failed", "error": str(e)}

if __name__ == "__main__":
    result = main()
    sys.exit(0 if result["status"] == "success" else 1)