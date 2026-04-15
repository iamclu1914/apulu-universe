"""
deploy_apu101.py — APU-101 Enhanced Engagement Monitor Deployment Script

Easy deployment and management of the APU-101 enhanced engagement monitoring system.
Provides setup, configuration validation, and deployment options.

Created by: Dex - Community Agent (APU-101)
Usage:
  python deploy_apu101.py --setup     # Initial setup and configuration
  python deploy_apu101.py --check     # Validate system readiness
  python deploy_apu101.py --start     # Start monitoring (single run)
  python deploy_apu101.py --monitor   # Start continuous monitoring
  python deploy_apu101.py --status    # Show system status
"""

import json
import sys
import subprocess
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import VAWN_DIR, load_json, save_json, CREDS_FILE

class APU101Deployer:
    """APU-101 system deployment and management."""

    def __init__(self):
        self.vawn_dir = Path(VAWN_DIR)
        self.config_dir = self.vawn_dir / "config"
        self.src_dir = self.vawn_dir / "src"
        self.research_dir = self.vawn_dir / "research"

    def validate_environment(self) -> Dict[str, bool]:
        """Validate that the environment is ready for APU-101."""
        checks = {
            "vawn_directory": self.vawn_dir.exists(),
            "config_directory": self.config_dir.exists(),
            "src_directory": self.src_dir.exists(),
            "research_directory": self.research_dir.exists(),
            "credentials_file": (self.vawn_dir / "credentials.json").exists(),
            "apu101_monitor": (self.src_dir / "apu101_engagement_monitor.py").exists(),
            "apu101_coordinator": (self.vawn_dir / "apu101_engagement_coordinator.py").exists(),
            "apu101_config": (self.config_dir / "apu101_engagement_config.json").exists(),
            "vawn_config": (self.vawn_dir / "vawn_config.py").exists(),
            "existing_engagement": (self.vawn_dir / "engagement_agent.py").exists()
        }

        return checks

    def setup_directories(self):
        """Create necessary directories for APU-101."""
        print("[SETUP] Creating directory structure...")

        directories = [
            self.config_dir,
            self.research_dir,
            self.src_dir
        ]

        for directory in directories:
            directory.mkdir(exist_ok=True)
            print(f"  [OK] {directory.name}/ directory")

        print("[SETUP] Directory structure ready")

    def validate_credentials(self) -> bool:
        """Validate that required credentials are available."""
        try:
            creds = load_json(CREDS_FILE)
            required_keys = ["access_token", "refresh_token"]

            missing = [key for key in required_keys if not creds.get(key)]
            if missing:
                print(f"[ERROR] Missing credentials: {', '.join(missing)}")
                return False

            print("[SETUP] Credentials validated")
            return True

        except Exception as e:
            print(f"[ERROR] Could not validate credentials: {e}")
            return False

    def test_imports(self) -> bool:
        """Test that all required modules can be imported."""
        print("[SETUP] Testing module imports...")

        test_modules = [
            ("requests", "HTTP client library"),
            ("anthropic", "Claude AI client"),
            ("pathlib", "Path handling"),
            ("json", "JSON processing"),
            ("datetime", "Date/time utilities")
        ]

        success = True
        for module, description in test_modules:
            try:
                __import__(module)
                print(f"  [OK] {module} - {description}")
            except ImportError:
                print(f"  [ERROR] {module} - {description} [MISSING]")
                success = False

        if not success:
            print("[ERROR] Some required modules are missing. Run: pip install requests anthropic")
            return False

        # Test APU-101 specific imports
        try:
            from src.apu101_engagement_monitor import APU101EngagementMonitor
            print(f"  [OK] APU101EngagementMonitor - Core monitoring system")
        except ImportError as e:
            print(f"  [ERROR] APU101EngagementMonitor - {e}")
            success = False

        try:
            import apu101_engagement_coordinator
            print(f"  [OK] APU101EngagementCoordinator - Coordination system")
        except ImportError as e:
            print(f"  [ERROR] APU101EngagementCoordinator - {e}")
            success = False

        return success

    def run_setup(self) -> bool:
        """Run complete APU-101 setup process."""
        print("\n" + "=" * 60)
        print("[*] APU-101 ENHANCED ENGAGEMENT MONITOR SETUP")
        print("=" * 60)

        # Create directories
        self.setup_directories()

        # Validate environment
        print("\n[SETUP] Validating environment...")
        checks = self.validate_environment()

        failed_checks = [name for name, passed in checks.items() if not passed]
        if failed_checks:
            print(f"[ERROR] Environment validation failed:")
            for check in failed_checks:
                print(f"  [ERROR] {check}")
            return False
        else:
            print("[SETUP] Environment validation passed")

        # Validate credentials
        if not self.validate_credentials():
            return False

        # Test imports
        if not self.test_imports():
            return False

        print("\n" + "=" * 60)
        print("[SUCCESS] APU-101 setup completed successfully!")
        print("=" * 60)
        print("\nNext steps:")
        print("  python deploy_apu101.py --check   # Verify system readiness")
        print("  python deploy_apu101.py --start   # Run single monitoring cycle")
        print("  python deploy_apu101.py --monitor # Start continuous monitoring")
        print("")

        return True

    def run_system_check(self) -> bool:
        """Run comprehensive system readiness check."""
        print("\n" + "=" * 60)
        print("[*] APU-101 SYSTEM READINESS CHECK")
        print("=" * 60)

        # Environment validation
        print("\n[CHECK] Environment validation...")
        checks = self.validate_environment()
        all_passed = all(checks.values())

        for name, passed in checks.items():
            status = "[OK]" if passed else "[ERROR]"
            print(f"  {status} {name.replace('_', ' ').title()}")

        if not all_passed:
            print("[ERROR] Environment checks failed. Run --setup to initialize.")
            return False

        # Test system initialization
        print("\n[CHECK] System initialization test...")
        try:
            from src.apu101_engagement_monitor import APU101EngagementMonitor
            monitor = APU101EngagementMonitor()
            print("  [OK] APU-101 monitor initialized successfully")
            print(f"  [OK] Configuration loaded: {len(monitor.config)} sections")
            print(f"  [OK] Monitoring interval: {monitor.config['monitoring']['check_interval_minutes']} minutes")
            print(f"  [OK] Auto-reply enabled: {monitor.config['auto_reply']['enabled']}")
        except Exception as e:
            print(f"  [ERROR] APU-101 monitor initialization failed: {e}")
            return False

        # Test coordination system
        try:
            import apu101_engagement_coordinator
            coordinator = apu101_engagement_coordinator.EngagementCoordinator()
            print("  [OK] APU-101 coordinator initialized successfully")
            print(f"  [OK] APU-44 integration: {coordinator.stats['apu44_integration']}")
            print(f"  [OK] Real-time monitoring: {coordinator.stats['apu101_active']}")
        except Exception as e:
            print(f"  [ERROR] APU-101 coordinator initialization failed: {e}")
            return False

        print("\n" + "=" * 60)
        print("[SUCCESS] APU-101 system is ready for deployment!")
        print("=" * 60)

        return True

    def start_single_monitoring(self) -> bool:
        """Start a single monitoring cycle."""
        print("\n[APU-101] Starting single monitoring cycle...")

        try:
            result = subprocess.run([
                sys.executable, "-c",
                "from src.apu101_engagement_monitor import main; main()"
            ], cwd=self.vawn_dir, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                print("[SUCCESS] Single monitoring cycle completed")
                if result.stdout:
                    print("Output:", result.stdout)
                return True
            else:
                print(f"[ERROR] Monitoring failed with exit code {result.returncode}")
                if result.stderr:
                    print("Error:", result.stderr)
                return False

        except subprocess.TimeoutExpired:
            print("[ERROR] Monitoring cycle timed out after 5 minutes")
            return False
        except Exception as e:
            print(f"[ERROR] Failed to start monitoring: {e}")
            return False

    def start_continuous_monitoring(self):
        """Start continuous monitoring."""
        print("\n[APU-101] Starting continuous monitoring...")
        print("Press Ctrl+C to stop monitoring")

        try:
            subprocess.run([
                sys.executable, "apu101_engagement_coordinator.py",
                "--mode", "continuous"
            ], cwd=self.vawn_dir)
        except KeyboardInterrupt:
            print("\n[APU-101] Monitoring stopped by user")
        except Exception as e:
            print(f"[ERROR] Monitoring failed: {e}")

    def show_status(self):
        """Show current system status."""
        print("\n[APU-101] Current system status:")

        # Check if monitoring is running
        try:
            status_file = self.research_dir / "apu101_coordinator_status.json"
            if status_file.exists():
                status = load_json(status_file)
                print(f"Last Update: {status.get('timestamp', 'Unknown')}")

                coordinator = status.get('coordinator', {})
                print(f"Coordinator: {'Running' if coordinator.get('running') else 'Stopped'}")
                print(f"Total Cycles: {coordinator.get('total_cycles', 0)}")
                print(f"Success Rate: {coordinator.get('success_rate', 0):.1%}")

                apu101 = status.get('apu101', {})
                if apu101.get('available'):
                    stats = apu101.get('session_stats', {})
                    print(f"Comments Processed: {stats.get('total_comments', 0)}")
                    print(f"Replies Posted: {stats.get('total_replies', 0)}")
                else:
                    print("APU-101 Monitor: Not available")
            else:
                print("No status information available. System may not have run yet.")

        except Exception as e:
            print(f"Error reading status: {e}")


def main():
    """Main deployment script function."""
    parser = argparse.ArgumentParser(
        description="APU-101 Enhanced Engagement Monitor Deployment"
    )
    parser.add_argument("--setup", action="store_true",
                       help="Run initial setup and configuration")
    parser.add_argument("--check", action="store_true",
                       help="Validate system readiness")
    parser.add_argument("--start", action="store_true",
                       help="Start single monitoring cycle")
    parser.add_argument("--monitor", action="store_true",
                       help="Start continuous monitoring")
    parser.add_argument("--status", action="store_true",
                       help="Show system status")

    args = parser.parse_args()

    if not any(vars(args).values()):
        parser.print_help()
        return 1

    deployer = APU101Deployer()

    if args.setup:
        success = deployer.run_setup()
        return 0 if success else 1

    elif args.check:
        success = deployer.run_system_check()
        return 0 if success else 1

    elif args.start:
        success = deployer.start_single_monitoring()
        return 0 if success else 1

    elif args.monitor:
        deployer.start_continuous_monitoring()
        return 0

    elif args.status:
        deployer.show_status()
        return 0

    return 0


if __name__ == "__main__":
    exit(main())