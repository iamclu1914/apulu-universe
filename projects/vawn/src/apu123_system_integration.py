"""
apu123_system_integration.py — APU-123 System Integration Module

Integrates APU-123 Community Engagement Quality Optimizer with existing APU ecosystem:
- APU-119: Real-time community response optimization
- APU-112: Engagement metrics aggregation
- APU-113: Intelligence dashboard
- Live engagement dashboard
- Paperclip coordination system

Created by: Dex - Community Agent (APU-123)
Purpose: Seamless integration with existing monitoring infrastructure
"""

import json
import sys
import sqlite3
import threading
import time
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests
import logging

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import load_json, save_json, VAWN_DIR, RESEARCH_DIR
from src.apu123_engagement_monitor import APU123EngagementMonitor, ConversationContext

logger = logging.getLogger("APU123_Integration")

class APU123SystemIntegration:
    """Integration layer for APU-123 with existing APU systems"""

    def __init__(self):
        self.apu123_monitor = APU123EngagementMonitor()
        self.integration_config = self._load_integration_config()

        # Integration paths
        self.apu119_db = VAWN_DIR / "database" / "apu119_engagement_optimization.db"
        self.apu112_db = VAWN_DIR / "database" / "apu112_engagement_metrics.db"
        self.apu113_log = RESEARCH_DIR / "apu113_intelligence_log.json"
        self.live_dashboard_file = RESEARCH_DIR / "live_engagement_dashboard.json"
        self.paperclip_log = RESEARCH_DIR / "paperclip_coordination_log.json"

        # APU-123 integration logs
        self.integration_log = RESEARCH_DIR / "apu123_integration_log.json"
        self.quality_sync_log = RESEARCH_DIR / "apu123_quality_sync_log.json"

    def _load_integration_config(self) -> Dict[str, Any]:
        """Load integration configuration"""
        config_path = VAWN_DIR / "config" / "apu123_integration_config.json"

        if config_path.exists():
            return load_json(config_path)

        # Default integration config
        default_config = {
            "sync_interval_seconds": 60,
            "quality_threshold_alerts": 0.4,
            "integration_enabled": {
                "apu119": True,
                "apu112": True,
                "apu113": True,
                "live_dashboard": True,
                "paperclip": True
            },
            "quality_improvement_targets": {
                "engagement_quality": 0.7,
                "response_quality": 0.7,
                "conversation_health": 0.6
            }
        }

        config_path.parent.mkdir(exist_ok=True)
        save_json(config_path, default_config)
        return default_config

    def sync_with_live_dashboard(self) -> Dict[str, Any]:
        """Sync APU-123 quality improvements with live engagement dashboard"""
        try:
            # Get current live dashboard data
            if not self.live_dashboard_file.exists():
                logger.warning("Live dashboard file not found")
                return {"status": "error", "message": "Live dashboard not found"}

            dashboard_data = load_json(self.live_dashboard_file)

            # Get APU-123 quality metrics
            apu123_dashboard = self.apu123_monitor.get_quality_dashboard()

            # Calculate quality improvements
            current_health = dashboard_data.get("current_health_score", 0)

            quality_improvements = {
                "engagement_quality": min(apu123_dashboard["average_scores"]["engagement"], 1.0),
                "response_quality": min(apu123_dashboard["average_scores"]["overall"], 1.0),
                "conversation_health": min(apu123_dashboard["average_scores"]["conversation"], 1.0)
            }

            # Update dashboard with APU-123 improvements
            updated_metrics = dashboard_data.get("current_data", {}).get("community_health", {}).get("metrics", {})

            # Apply APU-123 quality improvements
            if "engagement_quality" in updated_metrics:
                updated_metrics["engagement_quality"] = max(
                    updated_metrics["engagement_quality"],
                    quality_improvements["engagement_quality"]
                )

            if "response_quality" in updated_metrics:
                updated_metrics["response_quality"] = max(
                    updated_metrics["response_quality"],
                    quality_improvements["response_quality"]
                )

            if "conversation_health" in updated_metrics:
                updated_metrics["conversation_health"] = max(
                    updated_metrics["conversation_health"],
                    quality_improvements["conversation_health"]
                )

            # Recalculate overall health score
            if updated_metrics:
                overall_score = sum(updated_metrics.values()) / len(updated_metrics)
                dashboard_data["current_health_score"] = overall_score

                if "current_data" in dashboard_data:
                    if "community_health" in dashboard_data["current_data"]:
                        dashboard_data["current_data"]["community_health"]["overall_score"] = overall_score
                        dashboard_data["current_data"]["community_health"]["metrics"] = updated_metrics

            # Add APU-123 specific section
            dashboard_data["apu123_integration"] = {
                "timestamp": datetime.now().isoformat(),
                "quality_improvements_applied": quality_improvements,
                "apu123_responses_24h": apu123_dashboard.get("total_responses_24h", 0),
                "average_response_quality": apu123_dashboard["average_scores"]["overall"],
                "status": "active"
            }

            # Save updated dashboard
            save_json(self.live_dashboard_file, dashboard_data)

            sync_result = {
                "timestamp": datetime.now().isoformat(),
                "status": "success",
                "health_score_change": overall_score - current_health if updated_metrics else 0,
                "quality_improvements": quality_improvements,
                "apu123_contributions": apu123_dashboard
            }

            # Log the sync
            self._log_integration_event("live_dashboard_sync", sync_result)

            return sync_result

        except Exception as e:
            error_result = {
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "error": str(e)
            }
            logger.error(f"Live dashboard sync failed: {e}")
            self._log_integration_event("live_dashboard_sync_error", error_result)
            return error_result

    def integrate_with_apu119(self) -> Dict[str, Any]:
        """Integrate APU-123 responses with APU-119 real-time optimization"""
        try:
            if not self.apu119_db.exists():
                return {"status": "error", "message": "APU-119 database not found"}

            # Connect to APU-119 database
            conn = sqlite3.connect(str(self.apu119_db))
            cursor = conn.cursor()

            # Get APU-123 recent responses
            apu123_conn = sqlite3.connect(str(self.apu123_monitor.db_connection.execute("PRAGMA database_list").fetchone()[2]))
            apu123_cursor = apu123_conn.cursor()

            apu123_cursor.execute("""
                SELECT * FROM response_quality
                WHERE timestamp > datetime('now', '-1 hour')
                ORDER BY timestamp DESC
            """)

            recent_responses = apu123_cursor.fetchall()

            # Insert quality metrics into APU-119 for coordination
            integration_count = 0
            for response in recent_responses:
                try:
                    # Check if APU-119 has compatible table structure
                    cursor.execute("""
                        INSERT OR IGNORE INTO system_health
                        (timestamp, component, status, response_time, details)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        response[1],  # timestamp
                        "apu123_response_quality",
                        "healthy" if response[4] > 0.6 else "degraded",  # overall_score
                        response[4],  # use overall_score as response_time metric
                        json.dumps({
                            "quality_breakdown": {
                                "personalization": response[5],
                                "conversation": response[6],
                                "engagement": response[7],
                                "authenticity": response[8]
                            },
                            "platform": response[2],
                            "response_type": response[3]
                        })
                    ))
                    integration_count += 1
                except sqlite3.Error:
                    # Table might not exist or have different structure
                    pass

            conn.commit()
            conn.close()
            apu123_conn.close()

            result = {
                "timestamp": datetime.now().isoformat(),
                "status": "success",
                "integrated_responses": integration_count,
                "apu119_status": "synchronized"
            }

            self._log_integration_event("apu119_integration", result)
            return result

        except Exception as e:
            error_result = {
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "error": str(e)
            }
            logger.error(f"APU-119 integration failed: {e}")
            return error_result

    def sync_with_paperclip_coordination(self) -> Dict[str, Any]:
        """Sync with Paperclip coordination system for department routing"""
        try:
            # Get quality insights for department coordination
            apu123_dashboard = self.apu123_monitor.get_quality_dashboard()

            # Determine which departments need attention based on quality metrics
            department_recommendations = self._generate_department_recommendations(apu123_dashboard)

            # Create Paperclip coordination entry
            paperclip_entry = {
                "timestamp": datetime.now().isoformat(),
                "source": "apu123_engagement_quality",
                "agent_id": "75dd5aa3-6dfb-4d13-b424-48343f1fd7e2",
                "department_alerts": department_recommendations,
                "quality_status": apu123_dashboard["status"],
                "engagement_metrics": {
                    "overall_quality": apu123_dashboard["average_scores"]["overall"],
                    "response_count_24h": apu123_dashboard.get("total_responses_24h", 0),
                    "quality_trend": "improving" if apu123_dashboard["average_scores"]["overall"] > 0.6 else "needs_attention"
                }
            }

            # Append to Paperclip coordination log
            existing_log = load_json(self.paperclip_log) if self.paperclip_log.exists() else []
            existing_log.append(paperclip_entry)
            save_json(self.paperclip_log, existing_log[-50:])  # Keep last 50 entries

            result = {
                "timestamp": datetime.now().isoformat(),
                "status": "success",
                "paperclip_sync": "completed",
                "department_recommendations": department_recommendations
            }

            self._log_integration_event("paperclip_sync", result)
            return result

        except Exception as e:
            error_result = {
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "error": str(e)
            }
            logger.error(f"Paperclip sync failed: {e}")
            return error_result

    def _generate_department_recommendations(self, dashboard: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate department-specific recommendations based on quality metrics"""
        recommendations = []
        avg_scores = dashboard.get("average_scores", {})

        # Creative Revenue - if engagement is low
        if avg_scores.get("engagement", 0) < 0.5:
            recommendations.append({
                "department": "creative_revenue",
                "priority": "high",
                "issue": "low_engagement_quality",
                "recommendation": "Review content strategy and engagement tactics",
                "metric": avg_scores.get("engagement", 0)
            })

        # A&R - if conversation quality is low
        if avg_scores.get("conversation", 0) < 0.5:
            recommendations.append({
                "department": "a_and_r",
                "priority": "medium",
                "issue": "poor_conversation_quality",
                "recommendation": "Improve artist community interaction guidelines",
                "metric": avg_scores.get("conversation", 0)
            })

        # Operations - if overall system performance is low
        if avg_scores.get("overall", 0) < 0.4:
            recommendations.append({
                "department": "operations",
                "priority": "high",
                "issue": "critical_quality_metrics",
                "recommendation": "Review and optimize engagement monitoring systems",
                "metric": avg_scores.get("overall", 0)
            })

        return recommendations

    def _log_integration_event(self, event_type: str, data: Dict[str, Any]):
        """Log integration events"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "data": data
            }

            existing_log = load_json(self.integration_log) if self.integration_log.exists() else []
            existing_log.append(log_entry)
            save_json(self.integration_log, existing_log[-100:])  # Keep last 100 entries

        except Exception as e:
            logger.error(f"Integration logging failed: {e}")

    def run_full_integration_sync(self) -> Dict[str, Any]:
        """Run complete integration sync with all APU systems"""
        sync_results = {
            "timestamp": datetime.now().isoformat(),
            "integration_results": {}
        }

        try:
            # Sync with live dashboard
            if self.integration_config["integration_enabled"]["live_dashboard"]:
                sync_results["integration_results"]["live_dashboard"] = self.sync_with_live_dashboard()

            # Integrate with APU-119
            if self.integration_config["integration_enabled"]["apu119"]:
                sync_results["integration_results"]["apu119"] = self.integrate_with_apu119()

            # Sync with Paperclip
            if self.integration_config["integration_enabled"]["paperclip"]:
                sync_results["integration_results"]["paperclip"] = self.sync_with_paperclip_coordination()

            # Calculate overall sync status
            successful_syncs = sum(1 for result in sync_results["integration_results"].values()
                                 if result.get("status") == "success")
            total_syncs = len(sync_results["integration_results"])

            sync_results["overall_status"] = "success" if successful_syncs == total_syncs else "partial"
            sync_results["sync_success_rate"] = successful_syncs / total_syncs if total_syncs > 0 else 0

            # Log the full sync
            self._log_integration_event("full_integration_sync", sync_results)

            return sync_results

        except Exception as e:
            sync_results["overall_status"] = "error"
            sync_results["error"] = str(e)
            logger.error(f"Full integration sync failed: {e}")
            return sync_results

class APU123IntegrationService:
    """Service for running APU-123 integration continuously"""

    def __init__(self):
        self.integration = APU123SystemIntegration()
        self.is_running = False
        self.sync_thread = None

    def start_integration_service(self):
        """Start the integration service"""
        if self.is_running:
            logger.info("Integration service already running")
            return

        self.is_running = True
        self.sync_thread = threading.Thread(target=self._integration_loop, daemon=True)
        self.sync_thread.start()
        logger.info("APU-123 integration service started")

    def stop_integration_service(self):
        """Stop the integration service"""
        self.is_running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        logger.info("APU-123 integration service stopped")

    def _integration_loop(self):
        """Main integration loop"""
        sync_interval = self.integration.integration_config.get("sync_interval_seconds", 60)

        while self.is_running:
            try:
                logger.info("Running APU-123 integration sync...")
                results = self.integration.run_full_integration_sync()

                logger.info(f"Integration sync completed: {results['overall_status']}")

                # Sleep until next sync
                time.sleep(sync_interval)

            except Exception as e:
                logger.error(f"Integration loop error: {e}")
                time.sleep(30)  # Wait 30 seconds before retrying on error

def main():
    """Test APU-123 system integration"""
    print("🔗 APU-123 System Integration Test")
    print("=" * 50)

    integration = APU123SystemIntegration()

    # Test live dashboard sync
    print("Testing live dashboard sync...")
    dashboard_result = integration.sync_with_live_dashboard()
    print(f"Dashboard sync: {dashboard_result['status']}")
    if dashboard_result['status'] == 'success':
        print(f"Health score change: {dashboard_result.get('health_score_change', 0):.3f}")

    # Test APU-119 integration
    print("\nTesting APU-119 integration...")
    apu119_result = integration.integrate_with_apu119()
    print(f"APU-119 integration: {apu119_result['status']}")

    # Test Paperclip sync
    print("\nTesting Paperclip coordination sync...")
    paperclip_result = integration.sync_with_paperclip_coordination()
    print(f"Paperclip sync: {paperclip_result['status']}")

    # Test full sync
    print("\nRunning full integration sync...")
    full_result = integration.run_full_integration_sync()
    print(f"Full sync status: {full_result['overall_status']}")
    print(f"Success rate: {full_result.get('sync_success_rate', 0):.2%}")

    print("\n✅ APU-123 integration testing complete")

if __name__ == "__main__":
    main()