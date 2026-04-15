#!/usr/bin/env python3
"""
APU-144 Community Engagement Monitor Launcher
Initialization and management script for the community monitoring system.

Created by: Dex - Community Agent (APU-144)
Purpose: Launch, manage, and monitor the APU-144 community engagement system
"""

import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from vawn_config import VAWN_DIR, load_json, save_json
from src.apu144_community_engagement_monitor import APU144CommunityEngagementMonitor

class APU144Launcher:
    """Launcher and management system for APU-144 Community Engagement Monitor."""

    def __init__(self):
        self.config_file = VAWN_DIR / "config" / "apu144_community_engagement_config.json"
        self.status_file = VAWN_DIR / "research" / "apu144_launcher_status.json"
        self.log_file = VAWN_DIR / "research" / "apu144_launcher_log.json"

        self.config = self._load_config()
        self.monitor = None

    def _load_config(self) -> Dict[str, Any]:
        """Load APU-144 configuration settings."""
        try:
            config = load_json(self.config_file)
            print(f"✅ Loaded APU-144 configuration from {self.config_file}")
            return config
        except Exception as e:
            print(f"⚠️  Warning: Could not load config from {self.config_file}: {e}")
            print("📝 Using default configuration")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration if config file is not available."""
        return {
            "monitoring_settings": {
                "check_interval_seconds": 45,
                "platforms": ["instagram", "tiktok", "x", "threads", "bluesky"],
                "auto_recovery_enabled": True,
                "community_care_mode": True
            },
            "alert_settings": {
                "enable_real_time_alerts": True,
                "auto_resolve_enabled": True
            }
        }

    def initialize_system(self) -> bool:
        """Initialize the APU-144 community engagement monitoring system."""
        try:
            print("🏘️  Initializing APU-144 Community Engagement Monitor")
            print("=" * 60)

            # Create necessary directories
            directories = [
                VAWN_DIR / "database",
                VAWN_DIR / "research",
                VAWN_DIR / "config",
                VAWN_DIR / "scripts"
            ]

            for directory in directories:
                directory.mkdir(exist_ok=True)
                print(f"📁 Ensured directory: {directory}")

            # Initialize monitor
            self.monitor = APU144CommunityEngagementMonitor()
            print("✅ APU-144 monitor initialized successfully")

            # Update status
            status = {
                "initialization_timestamp": datetime.now().isoformat(),
                "status": "initialized",
                "platforms_configured": self.config["monitoring_settings"]["platforms"],
                "community_care_mode": self.config["monitoring_settings"]["community_care_mode"],
                "version": self.config.get("monitor_info", {}).get("version", "1.0.0")
            }

            save_json(self.status_file, status)
            self._log_event("system_initialized", "APU-144 system initialized successfully")

            print("🎯 Focus: Community Health • Sustainable Engagement • Quality Conversations")
            return True

        except Exception as e:
            print(f"❌ Error during initialization: {e}")
            self._log_event("initialization_error", f"Error: {e}")
            return False

    def run_monitoring_cycle(self) -> Dict[str, Any]:
        """Run a single monitoring cycle."""
        if not self.monitor:
            raise RuntimeError("Monitor not initialized. Call initialize_system() first.")

        print("\n🔄 Running community monitoring cycle...")
        cycle_start = time.time()

        try:
            results = self.monitor.run_community_monitoring_cycle()
            cycle_duration = time.time() - cycle_start

            print(f"✅ Monitoring cycle completed in {cycle_duration:.2f} seconds")

            # Log successful cycle
            self._log_event("monitoring_cycle_completed", {
                "duration_seconds": cycle_duration,
                "platforms_monitored": len(results.get("platforms_monitored", [])),
                "alerts_generated": len(results.get("alerts_generated", [])),
                "overall_health_score": results.get("overall_community_health", {}).get("average_health_score")
            })

            return results

        except Exception as e:
            print(f"❌ Error during monitoring cycle: {e}")
            self._log_event("monitoring_cycle_error", f"Error: {e}")
            raise

    def run_continuous_monitoring(self, duration_minutes: Optional[int] = None):
        """Run continuous monitoring for specified duration or indefinitely."""
        if not self.monitor:
            if not self.initialize_system():
                return False

        check_interval = self.config["monitoring_settings"]["check_interval_seconds"]
        end_time = time.time() + (duration_minutes * 60) if duration_minutes else None

        print(f"\n🔄 Starting continuous monitoring (check interval: {check_interval}s)")
        if duration_minutes:
            print(f"⏱️  Duration: {duration_minutes} minutes")
        else:
            print("⏱️  Duration: Indefinite (Ctrl+C to stop)")

        cycle_count = 0

        try:
            while True:
                if end_time and time.time() >= end_time:
                    break

                cycle_count += 1
                print(f"\n--- Monitoring Cycle #{cycle_count} ---")

                try:
                    results = self.run_monitoring_cycle()

                    # Display key metrics
                    health_score = results.get("overall_community_health", {}).get("average_health_score")
                    alerts_count = len(results.get("alerts_generated", []))

                    if health_score:
                        print(f"🏥 Community Health: {health_score:.3f}")
                    if alerts_count > 0:
                        print(f"🚨 New Alerts: {alerts_count}")

                except Exception as e:
                    print(f"❌ Cycle #{cycle_count} failed: {e}")

                # Wait for next cycle
                print(f"⏳ Waiting {check_interval} seconds until next cycle...")
                time.sleep(check_interval)

        except KeyboardInterrupt:
            print(f"\n🛑 Monitoring stopped by user after {cycle_count} cycles")

        print(f"✅ Continuous monitoring completed ({cycle_count} total cycles)")
        return True

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status and health report."""
        try:
            # Get launcher status
            launcher_status = load_json(self.status_file, default={})

            # Get community health report if monitor is available
            health_report = {}
            if self.monitor:
                health_report = self.monitor.get_community_health_report()

            return {
                "launcher_status": launcher_status,
                "community_health_report": health_report,
                "config_summary": {
                    "platforms": self.config["monitoring_settings"]["platforms"],
                    "check_interval": self.config["monitoring_settings"]["check_interval_seconds"],
                    "community_care_mode": self.config["monitoring_settings"]["community_care_mode"]
                }
            }

        except Exception as e:
            return {"error": f"Failed to get system status: {e}"}

    def _log_event(self, event_type: str, details: Any):
        """Log launcher events."""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "details": details
            }

            existing_log = load_json(self.log_file, default=[])
            existing_log.append(log_entry)

            # Keep last 100 log entries
            save_json(self.log_file, existing_log[-100:])

        except Exception as e:
            print(f"Warning: Could not log event: {e}")

def main():
    """Main function with command-line interface."""
    import argparse

    parser = argparse.ArgumentParser(description="APU-144 Community Engagement Monitor Launcher")
    parser.add_argument("--action", choices=["init", "run", "continuous", "status"],
                       default="run", help="Action to perform")
    parser.add_argument("--duration", type=int, help="Duration in minutes for continuous monitoring")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    launcher = APU144Launcher()

    if args.action == "init":
        print("🚀 Initializing APU-144 Community Engagement Monitor...")
        success = launcher.initialize_system()
        sys.exit(0 if success else 1)

    elif args.action == "run":
        print("▶️  Running single APU-144 monitoring cycle...")
        if launcher.initialize_system():
            try:
                results = launcher.run_monitoring_cycle()
                if args.verbose:
                    print(f"\n📊 Detailed Results:")
                    print(json.dumps(results, indent=2))
                sys.exit(0)
            except Exception as e:
                print(f"❌ Monitoring failed: {e}")
                sys.exit(1)
        else:
            sys.exit(1)

    elif args.action == "continuous":
        print("🔄 Starting continuous APU-144 monitoring...")
        success = launcher.run_continuous_monitoring(args.duration)
        sys.exit(0 if success else 1)

    elif args.action == "status":
        print("📊 Getting APU-144 system status...")
        status = launcher.get_system_status()
        print(json.dumps(status, indent=2))

if __name__ == "__main__":
    main()