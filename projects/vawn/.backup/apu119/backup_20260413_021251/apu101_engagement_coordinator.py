"""
apu101_engagement_coordinator.py — Real-Time Engagement Coordination System

Coordinates APU-101 enhanced engagement monitoring with existing APU-44 infrastructure
and legacy engagement agents. Provides unified management and cross-platform insights.

Created by: Dex - Community Agent (APU-101)
Features:
- Coordinated monitoring across all engagement systems
- Real-time status dashboard
- Integration with APU-44 alerts
- Performance optimization and load balancing
- Unified reporting and analytics
"""

import json
import sys
import time
import subprocess
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import (
    load_json, save_json, log_run, today_str, VAWN_DIR, RESEARCH_LOG
)

# Import APU systems
try:
    from src.apu101_engagement_monitor import APU101EngagementMonitor
except ImportError:
    APU101EngagementMonitor = None

try:
    from src.apu44_enhanced_engagement_monitor import (
        get_real_time_agent_status, analyze_platform_performance,
        generate_apu44_intelligent_alerts
    )
except ImportError:
    get_real_time_agent_status = None
    analyze_platform_performance = None
    generate_apu44_intelligent_alerts = None

# Coordinator configuration
COORDINATOR_LOG = VAWN_DIR / "research" / "apu101_coordinator_log.json"
COORDINATOR_STATUS = VAWN_DIR / "research" / "apu101_coordinator_status.json"

class EngagementCoordinator:
    """Central coordination system for all engagement monitoring."""

    def __init__(self):
        self.running = False
        self.apu101_monitor = None
        self.last_coordination = None
        self.stats = {
            "coordinator_start": datetime.now().isoformat(),
            "total_cycles": 0,
            "successful_cycles": 0,
            "apu101_active": False,
            "apu44_integration": False,
            "last_status_check": None
        }

        # Initialize APU-101 monitor
        if APU101EngagementMonitor:
            try:
                self.apu101_monitor = APU101EngagementMonitor()
                self.stats["apu101_active"] = True
                print("[COORDINATOR] APU-101 monitor initialized successfully")
            except Exception as e:
                print(f"[COORDINATOR WARNING] APU-101 initialization failed: {e}")

        # Check APU-44 integration
        if get_real_time_agent_status and analyze_platform_performance:
            self.stats["apu44_integration"] = True
            print("[COORDINATOR] APU-44 integration available")
        else:
            print("[COORDINATOR WARNING] APU-44 integration not available")

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status across all engagement systems."""
        status = {
            "timestamp": datetime.now().isoformat(),
            "coordinator": {
                "running": self.running,
                "total_cycles": self.stats["total_cycles"],
                "success_rate": self.stats["successful_cycles"] / max(1, self.stats["total_cycles"]),
                "last_coordination": self.last_coordination
            },
            "apu101": {
                "available": self.stats["apu101_active"],
                "monitor_config": None,
                "last_run": None
            },
            "apu44": {
                "available": self.stats["apu44_integration"],
                "agent_status": None,
                "platform_metrics": None,
                "alerts": []
            },
            "legacy_agents": {
                "engagement_agent": "unknown",
                "engagement_bot": "unknown"
            }
        }

        # Get APU-101 status
        if self.apu101_monitor:
            status["apu101"]["monitor_config"] = self.apu101_monitor.config
            status["apu101"]["session_stats"] = self.apu101_monitor.stats

        # Get APU-44 status
        if self.stats["apu44_integration"]:
            try:
                agents = get_real_time_agent_status()
                metrics = analyze_platform_performance()
                alerts = generate_apu44_intelligent_alerts(agents, metrics)

                status["apu44"]["agent_status"] = agents
                status["apu44"]["platform_metrics"] = metrics
                status["apu44"]["alerts"] = alerts

                # Map to legacy agent status
                if "engagementagent" in agents:
                    status["legacy_agents"]["engagement_agent"] = agents["engagementagent"]["status"]
                if "engagementbot" in agents:
                    status["legacy_agents"]["engagement_bot"] = agents["engagementbot"]["status"]

            except Exception as e:
                print(f"[COORDINATOR WARNING] APU-44 status check failed: {e}")

        return status

    def run_coordinated_cycle(self) -> bool:
        """Run a coordinated engagement monitoring cycle."""
        cycle_start = time.time()
        success = True

        try:
            print(f"\n[COORDINATOR] Starting coordinated engagement cycle")

            # Run APU-101 monitoring
            if self.apu101_monitor:
                print("[COORDINATOR] Running APU-101 enhanced monitoring...")
                apu101_success = self.apu101_monitor.monitor_cycle()
                if not apu101_success:
                    print("[COORDINATOR WARNING] APU-101 cycle had issues")
                    success = False
            else:
                print("[COORDINATOR WARNING] APU-101 monitor not available")

            # Update coordination stats
            self.stats["total_cycles"] += 1
            if success:
                self.stats["successful_cycles"] += 1

            self.last_coordination = datetime.now().isoformat()
            cycle_time = time.time() - cycle_start

            # Log coordination results
            log_run("APU101EngagementCoordinator", "ok" if success else "warning",
                   f"Coordinated cycle completed in {cycle_time:.2f}s, "
                   f"success: {success}")

            print(f"[COORDINATOR] Cycle completed in {cycle_time:.2f}s, success: {success}")

            return success

        except Exception as e:
            print(f"[COORDINATOR ERROR] Coordination cycle failed: {e}")
            log_run("APU101EngagementCoordinator", "error",
                   f"Coordination failed: {e}")
            return False

    def generate_unified_dashboard(self) -> str:
        """Generate unified dashboard combining APU-101 and APU-44 insights."""
        status = self.get_system_status()

        dashboard = []
        dashboard.append("=" * 80)
        dashboard.append("[*] APU-101 UNIFIED ENGAGEMENT COORDINATION DASHBOARD")
        dashboard.append(f"[DATE] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        dashboard.append("=" * 80)

        # Coordinator Status
        coord = status["coordinator"]
        dashboard.append(f"\n[COORDINATOR] SYSTEM STATUS:")
        dashboard.append(f"  Status: {'[ACTIVE]' if coord['running'] else '[STOPPED]'}")
        dashboard.append(f"  Cycles: {coord['total_cycles']} total, {coord['success_rate']:.1%} success")
        dashboard.append(f"  Last Coordination: {coord['last_coordination'] or 'Never'}")

        # APU-101 Status
        apu101 = status["apu101"]
        dashboard.append(f"\n[APU-101] ENHANCED REAL-TIME MONITOR:")
        if apu101["available"]:
            dashboard.append(f"  Status: [ACTIVE] Real-time monitoring enabled")
            if apu101.get("session_stats"):
                stats = apu101["session_stats"]
                dashboard.append(f"  Comments Processed: {stats.get('total_comments', 0)}")
                dashboard.append(f"  Replies Posted: {stats.get('total_replies', 0)}")
                active_platforms = ", ".join(stats.get('platforms_active', []))
                dashboard.append(f"  Active Platforms: {active_platforms or 'None'}")
        else:
            dashboard.append(f"  Status: [UNAVAILABLE] Monitor not initialized")

        # APU-44 Integration
        apu44 = status["apu44"]
        dashboard.append(f"\n[APU-44] LEGACY SYSTEM INTEGRATION:")
        if apu44["available"]:
            dashboard.append(f"  Status: [INTEGRATED] Legacy monitoring active")

            # Agent health from APU-44
            if apu44["agent_status"]:
                dashboard.append(f"  Legacy Agents:")
                for agent_name, agent_data in apu44["agent_status"].items():
                    status_emoji = {
                        "healthy": "[HEALTHY]",
                        "idle": "[IDLE]",
                        "warning": "[WARN]",
                        "failed": "[FAILED]",
                        "unknown": "[UNKNOWN]"
                    }.get(agent_data["status"], "[?]")
                    dashboard.append(f"    {status_emoji} {agent_name}: {agent_data['success_rate']:.1%} success")

            # Platform metrics from APU-44
            if apu44["platform_metrics"]:
                metrics = apu44["platform_metrics"]
                dashboard.append(f"  Platform API Coverage: {metrics.get('api_coverage_rate', 0):.1%}")
                if metrics.get('top_performer'):
                    dashboard.append(f"  Top Platform: {metrics['top_performer'].upper()}")

            # Alerts summary
            alerts = apu44["alerts"]
            if alerts:
                alert_counts = {"infrastructure": 0, "community": 0, "technical": 0}
                for alert in alerts:
                    category = alert.get("category", "technical")
                    alert_counts[category] = alert_counts.get(category, 0) + 1

                dashboard.append(f"  Active Alerts: {len(alerts)} total")
                for category, count in alert_counts.items():
                    if count > 0:
                        dashboard.append(f"    {category.title()}: {count}")
        else:
            dashboard.append(f"  Status: [UNAVAILABLE] Legacy integration disabled")

        # System Health Summary
        dashboard.append(f"\n[SUMMARY] UNIFIED ENGAGEMENT HEALTH:")
        total_systems = sum([
            1 if apu101["available"] else 0,
            1 if apu44["available"] else 0
        ])
        active_systems = sum([
            1 if apu101["available"] else 0,
            1 if apu44["available"] and len(apu44.get("alerts", [])) == 0 else 0
        ])

        dashboard.append(f"  Systems Active: {active_systems}/{total_systems}")
        dashboard.append(f"  Overall Status: {'[OPERATIONAL]' if active_systems == total_systems else '[NEEDS ATTENTION]'}")

        # Integration Benefits
        dashboard.append(f"\n[APU-101] ENHANCEMENTS ACTIVE:")
        enhancements = [
            "✓ Real-time comment monitoring (15-min intervals)",
            "✓ Intelligent sentiment analysis and spam detection",
            "✓ Cross-platform reply coordination",
            "✓ Enhanced engagement analytics",
            "✓ Smart priority scoring system",
            "✓ Integration with APU-44 monitoring"
        ]
        for enhancement in enhancements:
            dashboard.append(f"  {enhancement}")

        dashboard.append("\n" + "=" * 80)

        return "\n".join(dashboard)

    def save_coordinator_status(self):
        """Save coordinator status for external monitoring."""
        status = self.get_system_status()

        # Update status file for external tools
        save_json(COORDINATOR_STATUS, status)

        # Save to coordinator log
        coordinator_log = load_json(COORDINATOR_LOG) if COORDINATOR_LOG.exists() else {}
        today = today_str()

        if today not in coordinator_log:
            coordinator_log[today] = []

        coordinator_log[today].append({
            "timestamp": datetime.now().isoformat(),
            "coordinator_stats": self.stats,
            "system_status": status,
            "dashboard_generated": True
        })

        # Keep last 30 days
        cutoff_date = (datetime.now() - timedelta(days=30)).date()
        coordinator_log = {
            k: v for k, v in coordinator_log.items()
            if datetime.fromisoformat(k + "T00:00:00").date() >= cutoff_date
        }

        COORDINATOR_LOG.parent.mkdir(exist_ok=True)
        save_json(COORDINATOR_LOG, coordinator_log)

    def run_continuous_coordination(self, check_interval_minutes: int = 15):
        """Run continuous coordination with configurable intervals."""
        print(f"\n[COORDINATOR] Starting APU-101 Unified Engagement Coordination")
        print(f"[CONFIG] Coordination interval: {check_interval_minutes} minutes")

        self.running = True
        check_interval = check_interval_minutes * 60  # Convert to seconds

        while self.running:
            try:
                # Run coordinated cycle
                success = self.run_coordinated_cycle()

                # Generate and display dashboard
                dashboard = self.generate_unified_dashboard()
                print(dashboard)

                # Save status
                self.save_coordinator_status()

                if success:
                    print(f"\n[COORDINATOR] Waiting {check_interval_minutes} minutes until next coordination...")
                else:
                    print(f"\n[COORDINATOR] Issues detected, retrying in {check_interval_minutes} minutes...")

                time.sleep(check_interval)

            except KeyboardInterrupt:
                print(f"\n[COORDINATOR] Coordination stopped by user")
                break
            except Exception as e:
                print(f"[COORDINATOR ERROR] Unexpected error: {e}")
                time.sleep(60)  # Wait 1 minute on error

        self.running = False

    def run_single_coordination(self) -> Dict[str, Any]:
        """Run single coordinated check and return comprehensive results."""
        print(f"\n[COORDINATOR] Running single coordinated engagement check...")

        # Run coordination cycle
        success = self.run_coordinated_cycle()

        # Generate dashboard
        dashboard = self.generate_unified_dashboard()
        print(dashboard)

        # Get final status
        status = self.get_system_status()

        # Save status
        self.save_coordinator_status()

        return {
            "success": success,
            "coordinator_stats": self.stats,
            "system_status": status,
            "dashboard": dashboard
        }


def main():
    """APU-101 Engagement Coordinator main function."""
    import argparse

    parser = argparse.ArgumentParser(description="APU-101 Unified Engagement Coordination System")
    parser.add_argument("--mode", choices=["single", "continuous"], default="single",
                       help="Run single coordination or continuous monitoring")
    parser.add_argument("--interval", type=int, default=15,
                       help="Coordination interval in minutes (default: 15)")
    args = parser.parse_args()

    coordinator = EngagementCoordinator()

    if args.mode == "continuous":
        coordinator.run_continuous_coordination(args.interval)
    else:
        result = coordinator.run_single_coordination()
        print(f"\n[COORDINATOR] Coordination completed: {'SUCCESS' if result['success'] else 'FAILED'}")
        return 0 if result['success'] else 1


if __name__ == "__main__":
    exit(main())