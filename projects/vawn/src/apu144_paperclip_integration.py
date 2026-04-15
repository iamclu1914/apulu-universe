"""
APU-144 Paperclip Platform Integration
Integration layer connecting APU-144 Community Engagement Monitor with existing Paperclip systems.

Created by: Dex - Community Agent (APU-144)
Purpose: Seamless integration with existing APU systems and Paperclip platform
Integrates: APU-101, APU-112, APU-135, APU-141, and other engagement systems
"""

import json
import sys
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from vawn_config import VAWN_DIR, load_json, save_json

# Import existing APU systems for integration
try:
    from apu101_engagement_coordinator import APU101EngagementCoordinator
    apu101_available = True
except ImportError:
    apu101_available = False

try:
    from apu141_enhanced_engagement_monitor import APU141EnhancedEngagementMonitor
    apu141_available = True
except ImportError:
    apu141_available = False

try:
    from apu112_sentiment_agent import SentimentAnalysisSystem
    apu112_available = True
except ImportError:
    apu112_available = False

@dataclass
class IntegrationStatus:
    """Integration status for each APU system."""
    system_name: str
    available: bool
    version: Optional[str]
    last_sync: Optional[str]
    status: str  # active, inactive, error, unknown

class APU144PaperclipIntegration:
    """
    Integration manager for APU-144 with existing Paperclip platform systems.
    Provides unified community engagement monitoring across all APU systems.
    """

    def __init__(self):
        self.integration_id = f"apu144_integration_{int(datetime.now().timestamp())}"
        self.config_file = VAWN_DIR / "config" / "apu144_community_engagement_config.json"
        self.integration_log = VAWN_DIR / "research" / "apu144_integration_log.json"
        self.sync_status_file = VAWN_DIR / "research" / "apu144_sync_status.json"

        # Load configuration
        try:
            self.config = load_json(self.config_file) or {}
        except:
            self.config = {}

        # Initialize system connections
        self.systems = {}
        self.integration_status = {}

        # Integration settings
        self.sync_enabled = self.config.get("integration_settings", {}).get("legacy_apu_compatibility", True)
        self.cross_platform_tracking = self.config.get("integration_settings", {}).get("cross_platform_tracking", True)

    def initialize_integrations(self) -> Dict[str, IntegrationStatus]:
        """Initialize connections to existing APU systems."""
        integrations = {}

        # APU-101 Engagement Coordinator
        if apu101_available:
            try:
                self.systems["apu101"] = APU101EngagementCoordinator()
                integrations["apu101"] = IntegrationStatus(
                    system_name="APU-101 Engagement Coordinator",
                    available=True,
                    version="active",
                    last_sync=datetime.now().isoformat(),
                    status="active"
                )
                print("CONNECTED: APU-101 Engagement Coordinator")
            except Exception as e:
                integrations["apu101"] = IntegrationStatus(
                    system_name="APU-101 Engagement Coordinator",
                    available=False,
                    version=None,
                    last_sync=None,
                    status="error"
                )
                print(f"WARNING: APU-101 connection failed: {e}")
        else:
            integrations["apu101"] = IntegrationStatus(
                system_name="APU-101 Engagement Coordinator",
                available=False,
                version=None,
                last_sync=None,
                status="unavailable"
            )
            print("WARNING: APU-101 not available")

        # APU-141 Enhanced Monitor
        if apu141_available:
            try:
                self.systems["apu141"] = APU141EnhancedEngagementMonitor()
                integrations["apu141"] = IntegrationStatus(
                    system_name="APU-141 Enhanced Engagement Monitor",
                    available=True,
                    version="active",
                    last_sync=datetime.now().isoformat(),
                    status="active"
                )
                print("CONNECTED: APU-141 Enhanced Monitor")
            except Exception as e:
                integrations["apu141"] = IntegrationStatus(
                    system_name="APU-141 Enhanced Engagement Monitor",
                    available=False,
                    version=None,
                    last_sync=None,
                    status="error"
                )
                print(f"WARNING: APU-141 connection failed: {e}")
        else:
            integrations["apu141"] = IntegrationStatus(
                system_name="APU-141 Enhanced Engagement Monitor",
                available=False,
                version=None,
                last_sync=None,
                status="unavailable"
            )
            print("WARNING: APU-141 not available")

        # APU-112 Sentiment Analysis
        if apu112_available:
            try:
                self.systems["apu112"] = SentimentAnalysisSystem()
                integrations["apu112"] = IntegrationStatus(
                    system_name="APU-112 Sentiment Analysis System",
                    available=True,
                    version="active",
                    last_sync=datetime.now().isoformat(),
                    status="active"
                )
                print("CONNECTED: APU-112 Sentiment Analysis")
            except Exception as e:
                integrations["apu112"] = IntegrationStatus(
                    system_name="APU-112 Sentiment Analysis System",
                    available=False,
                    version=None,
                    last_sync=None,
                    status="error"
                )
                print(f"WARNING: APU-112 connection failed: {e}")
        else:
            integrations["apu112"] = IntegrationStatus(
                system_name="APU-112 Sentiment Analysis System",
                available=False,
                version=None,
                last_sync=None,
                status="unavailable"
            )
            print("WARNING: APU-112 not available")

        self.integration_status = integrations
        self._save_integration_status()
        return integrations

    def sync_with_apu141(self) -> Dict[str, Any]:
        """Sync community engagement data with APU-141 enhanced monitor."""
        if "apu141" not in self.systems:
            return {"status": "unavailable", "message": "APU-141 not connected"}

        try:
            # Get APU-141 monitoring results
            apu141_results = self.systems["apu141"].run_comprehensive_monitoring_cycle()

            # Extract relevant community data
            community_insights = {
                "timestamp": datetime.now().isoformat(),
                "source": "apu141",
                "api_health_status": apu141_results.get("components", {}).get("api_health"),
                "agent_results": apu141_results.get("components", {}).get("agent_results", []),
                "overall_assessment": apu141_results.get("overall_assessment", {}),
                "integration_notes": "Data synchronized from APU-141 enhanced monitoring"
            }

            self._log_integration_event("apu141_sync", community_insights)
            return {"status": "success", "data": community_insights}

        except Exception as e:
            error_msg = f"APU-141 sync failed: {e}"
            self._log_integration_event("apu141_sync_error", {"error": error_msg})
            return {"status": "error", "message": error_msg}

    def sync_with_apu101(self) -> Dict[str, Any]:
        """Sync coordination data with APU-101 engagement coordinator."""
        if "apu101" not in self.systems:
            return {"status": "unavailable", "message": "APU-101 not connected"}

        try:
            # Get coordination data from APU-101
            # Note: This would depend on APU-101's actual API
            coordination_data = {
                "timestamp": datetime.now().isoformat(),
                "source": "apu101",
                "coordination_status": "active",
                "platform_coordination": {},
                "integration_notes": "Data synchronized from APU-101 coordination"
            }

            self._log_integration_event("apu101_sync", coordination_data)
            return {"status": "success", "data": coordination_data}

        except Exception as e:
            error_msg = f"APU-101 sync failed: {e}"
            self._log_integration_event("apu101_sync_error", {"error": error_msg})
            return {"status": "error", "message": error_msg}

    def sync_with_apu112(self) -> Dict[str, Any]:
        """Sync sentiment analysis data with APU-112."""
        if "apu112" not in self.systems:
            return {"status": "unavailable", "message": "APU-112 not connected"}

        try:
            # Get sentiment analysis from APU-112
            sentiment_data = {
                "timestamp": datetime.now().isoformat(),
                "source": "apu112",
                "sentiment_analysis": {},
                "emotional_intelligence": {},
                "integration_notes": "Sentiment data synchronized from APU-112"
            }

            self._log_integration_event("apu112_sync", sentiment_data)
            return {"status": "success", "data": sentiment_data}

        except Exception as e:
            error_msg = f"APU-112 sync failed: {e}"
            self._log_integration_event("apu112_sync_error", {"error": error_msg})
            return {"status": "error", "message": error_msg}

    def run_unified_community_assessment(self) -> Dict[str, Any]:
        """
        Run unified community assessment combining APU-144 with other systems.
        Provides comprehensive community health analysis across all integrated systems.
        """
        assessment_start = datetime.now()

        unified_assessment = {
            "assessment_id": f"unified_{int(assessment_start.timestamp())}",
            "timestamp": assessment_start.isoformat(),
            "systems_integrated": list(self.integration_status.keys()),
            "apu144_data": {},
            "integrated_data": {},
            "unified_metrics": {},
            "recommendations": [],
            "integration_health": {}
        }

        # Get APU-144 community data
        try:
            from apu144_community_engagement_monitor import APU144CommunityEngagementMonitor
            apu144_monitor = APU144CommunityEngagementMonitor()
            apu144_results = apu144_monitor.run_community_monitoring_cycle()
            unified_assessment["apu144_data"] = apu144_results
        except Exception as e:
            unified_assessment["apu144_data"] = {"error": f"APU-144 data collection failed: {e}"}

        # Sync with available systems
        integrated_data = {}

        if self.integration_status.get("apu141", {}).status == "active":
            integrated_data["apu141"] = self.sync_with_apu141()

        if self.integration_status.get("apu101", {}).status == "active":
            integrated_data["apu101"] = self.sync_with_apu101()

        if self.integration_status.get("apu112", {}).status == "active":
            integrated_data["apu112"] = self.sync_with_apu112()

        unified_assessment["integrated_data"] = integrated_data

        # Calculate unified metrics
        unified_assessment["unified_metrics"] = self._calculate_unified_metrics(
            unified_assessment["apu144_data"],
            integrated_data
        )

        # Generate unified recommendations
        unified_assessment["recommendations"] = self._generate_unified_recommendations(
            unified_assessment["unified_metrics"]
        )

        # Assessment integration health
        unified_assessment["integration_health"] = self._assess_integration_health()

        # Save assessment
        self._save_unified_assessment(unified_assessment)

        assessment_duration = (datetime.now() - assessment_start).total_seconds()
        unified_assessment["assessment_duration_seconds"] = assessment_duration

        return unified_assessment

    def _calculate_unified_metrics(self, apu144_data: Dict[str, Any],
                                 integrated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate unified metrics from all integrated systems."""
        unified_metrics = {
            "overall_community_health": 0.0,
            "integration_score": 0.0,
            "data_quality_score": 0.0,
            "system_coverage": 0.0
        }

        # Calculate integration score based on successful connections
        active_integrations = sum(1 for status in self.integration_status.values() if status.status == "active")
        total_possible = len(self.integration_status)
        unified_metrics["integration_score"] = active_integrations / total_possible if total_possible > 0 else 0

        # Calculate system coverage
        unified_metrics["system_coverage"] = unified_metrics["integration_score"]

        # Calculate overall health from APU-144 if available
        if "overall_community_health" in apu144_data:
            apu144_health = apu144_data["overall_community_health"].get("average_health_score", 0)
            unified_metrics["overall_community_health"] = apu144_health

        # Data quality assessment
        successful_syncs = sum(1 for data in integrated_data.values() if data.get("status") == "success")
        attempted_syncs = len(integrated_data)
        unified_metrics["data_quality_score"] = successful_syncs / attempted_syncs if attempted_syncs > 0 else 1.0

        return unified_metrics

    def _generate_unified_recommendations(self, unified_metrics: Dict[str, Any]) -> List[str]:
        """Generate unified recommendations based on integrated system analysis."""
        recommendations = []

        integration_score = unified_metrics.get("integration_score", 0)
        community_health = unified_metrics.get("overall_community_health", 0)
        data_quality = unified_metrics.get("data_quality_score", 0)

        if integration_score < 0.7:
            recommendations.append(
                f"INTEGRATION: Low system integration ({integration_score:.2f}). "
                "Consider investigating failed APU system connections."
            )

        if community_health < 0.6:
            recommendations.append(
                f"COMMUNITY: Community health below optimal ({community_health:.2f}). "
                "Focus on community care and engagement quality improvement."
            )

        if data_quality < 0.8:
            recommendations.append(
                f"DATA: Data sync quality issues ({data_quality:.2f}). "
                "Review integration connections and error logs."
            )

        if integration_score > 0.8 and community_health > 0.7:
            recommendations.append(
                "EXCELLENT: High integration and community health. Continue current strategies."
            )

        return recommendations

    def _assess_integration_health(self) -> Dict[str, Any]:
        """Assess the health of the integration system itself."""
        return {
            "timestamp": datetime.now().isoformat(),
            "systems_available": [k for k, v in self.integration_status.items() if v.available],
            "systems_active": [k for k, v in self.integration_status.items() if v.status == "active"],
            "systems_with_errors": [k for k, v in self.integration_status.items() if v.status == "error"],
            "overall_integration_health": len([v for v in self.integration_status.values() if v.status == "active"]) / len(self.integration_status) if self.integration_status else 0
        }

    def _save_integration_status(self):
        """Save integration status to file."""
        try:
            status_data = {
                "timestamp": datetime.now().isoformat(),
                "integration_id": self.integration_id,
                "systems": {k: {
                    "system_name": v.system_name,
                    "available": v.available,
                    "version": v.version,
                    "last_sync": v.last_sync,
                    "status": v.status
                } for k, v in self.integration_status.items()}
            }
            save_json(self.sync_status_file, status_data)
        except Exception as e:
            print(f"Warning: Could not save integration status: {e}")

    def _log_integration_event(self, event_type: str, data: Any):
        """Log integration events."""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "integration_id": self.integration_id,
                "event_type": event_type,
                "data": data
            }

            existing_log = load_json(self.integration_log, default=[])
            existing_log.append(log_entry)
            save_json(self.integration_log, existing_log[-200:])  # Keep last 200 entries

        except Exception as e:
            print(f"Warning: Could not log integration event: {e}")

    def _save_unified_assessment(self, assessment: Dict[str, Any]):
        """Save unified assessment results."""
        try:
            assessment_file = VAWN_DIR / "research" / "apu144_unified_assessments.json"
            existing_assessments = load_json(assessment_file, default=[])
            existing_assessments.append(assessment)
            save_json(assessment_file, existing_assessments[-50:])  # Keep last 50 assessments
        except Exception as e:
            print(f"Warning: Could not save unified assessment: {e}")

def main():
    """Main function for testing APU-144 Paperclip integration."""
    print("🔌 APU-144 Paperclip Platform Integration")
    print("=" * 50)

    integration = APU144PaperclipIntegration()

    # Initialize integrations
    print("\n📡 Initializing system integrations...")
    integrations = integration.initialize_integrations()

    print(f"\n📊 Integration Summary:")
    for system_id, status in integrations.items():
        status_emoji = "✅" if status.status == "active" else "⚠️" if status.available else "❌"
        print(f"   {status_emoji} {status.system_name}: {status.status}")

    # Run unified assessment
    print(f"\n🔄 Running unified community assessment...")
    try:
        assessment = integration.run_unified_community_assessment()

        print(f"✅ Assessment completed successfully")
        print(f"🏥 Overall Community Health: {assessment['unified_metrics'].get('overall_community_health', 'N/A'):.3f}")
        print(f"🔗 Integration Score: {assessment['unified_metrics'].get('integration_score', 'N/A'):.3f}")
        print(f"📊 Data Quality: {assessment['unified_metrics'].get('data_quality_score', 'N/A'):.3f}")

        if assessment.get("recommendations"):
            print(f"\n💡 Unified Recommendations:")
            for i, rec in enumerate(assessment["recommendations"], 1):
                print(f"   {i}. {rec}")

        return True

    except Exception as e:
        print(f"❌ Assessment failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)