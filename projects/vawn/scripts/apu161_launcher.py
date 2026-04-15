#!/usr/bin/env python3
"""
apu161_launcher.py — Launch Script for APU-161 Intelligent Engagement Monitor
Simple launcher with configuration options and deployment management.

Created by: Dex - Community Agent (APU-161)
Purpose: Easy deployment and management of APU-161 monitoring system
"""

import sys
import time
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def print_banner():
    """Print APU-161 banner."""
    banner = """
================================================================
                  APU-161 INTELLIGENT MONITOR
              API-Resilient Engagement Intelligence
================================================================
  * Adaptive Monitoring Modes    * Predictive Analytics
  * API Health Assessment        * Community Insights
  * Intelligent Fallbacks        * Real-time Intelligence
================================================================
    """
    print(banner)

def run_monitor():
    """Run the APU-161 intelligent monitor."""
    print("[AI] Starting APU-161 Intelligent Engagement Monitor...")
    print("[INIT] Initializing intelligent systems...")

    try:
        from src.apu161_engagement_monitor import main
        return main()
    except ImportError as e:
        print(f"[ERROR] ERROR: Could not import APU-161 monitor: {e}")
        print("[TIP] Please ensure APU-161 is properly installed in src/ directory")
        return 1
    except Exception as e:
        print(f"[ERROR] ERROR: Monitor execution failed: {e}")
        return 1

def run_tests():
    """Run APU-161 test suite."""
    print("[TEST] Starting APU-161 Test Suite...")
    print("[CHECK] Testing intelligent monitoring capabilities...")

    try:
        from test_apu161_intelligent_monitor import main as test_main
        return 0 if test_main() else 1
    except ImportError as e:
        print(f"[ERROR] ERROR: Could not import APU-161 test suite: {e}")
        print("[TIP] Please ensure test_apu161_intelligent_monitor.py exists")
        return 1
    except Exception as e:
        print(f"[ERROR] ERROR: Test execution failed: {e}")
        return 1

def show_status():
    """Show current APU-161 status."""
    print("[STATUS] APU-161 System Status")
    print("=" * 40)

    # Check if monitor files exist
    base_path = Path(__file__).parent.parent
    monitor_file = base_path / "src" / "apu161_engagement_monitor.py"
    test_file = base_path / "test_apu161_intelligent_monitor.py"
    db_file = base_path / "database" / "apu161_engagement_intelligence.db"

    print(f"[FILE] Monitor File: {'[OK] Present' if monitor_file.exists() else '[ERROR] Missing'}")
    print(f"[TEST] Test File: {'[OK] Present' if test_file.exists() else '[ERROR] Missing'}")
    print(f"[DB] Database: {'[OK] Present' if db_file.exists() else '[ERROR] Not Created'}")

    # Check for recent logs
    log_files = [
        base_path / "research" / "apu161_monitor_log.json",
        base_path / "research" / "apu161_intelligence_log.json",
        base_path / "research" / "apu161_insights_log.json"
    ]

    recent_logs = [log for log in log_files if log.exists()]
    print(f"[LOGS] Recent Logs: {len(recent_logs)}/{len(log_files)} present")

    if recent_logs:
        from vawn_config import load_json
        try:
            latest_log = load_json(recent_logs[0])
            print(f"[TIME] Last Activity: Recent logs detected")
        except:
            print(f"[TIME] Last Activity: Unknown")
    else:
        print(f"[TIME] Last Activity: No previous runs detected")

    print("\n[TIP] Use --monitor to run monitoring or --test to run tests")

def show_features():
    """Show APU-161 features and capabilities."""
    print("[FEATURES] APU-161 Intelligent Features")
    print("=" * 45)

    features = [
        ("[RESILIENT]  API-Resilient Architecture", "Works with any API availability state"),
        ("[AI] Predictive Intelligence", "Insights even with limited data"),
        ("[STATUS] Adaptive Monitoring", "Optimizes based on available resources"),
        ("[CHECK] Community Insights", "Actionable intelligence for community growth"),
        ("[FAST] Real-time Health Scoring", "Continuous system assessment"),
        ("[FEATURES] Smart Alert Prioritization", "Action-focused recommendations"),
        ("[PREDICT] Trend Prediction", "ML-based community trend analysis"),
        ("[INIT] Intelligent Fallbacks", "Multiple data source strategies"),
        ("[LOGS] Comprehensive Dashboard", "Real-time intelligence overview"),
        ("[UNIFIED] Cross-platform Analysis", "Unified community health view")
    ]

    for feature, description in features:
        print(f"  {feature}")
        print(f"    └─ {description}")

    print(f"\n[READY] APU-161 addresses API limitations while providing advanced intelligence!")

def main():
    """Main launcher function."""
    parser = argparse.ArgumentParser(
        description="APU-161 Intelligent Engagement Monitor Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python apu161_launcher.py --monitor     # Run monitoring cycle
  python apu161_launcher.py --test        # Run test suite
  python apu161_launcher.py --status      # Show system status
  python apu161_launcher.py --features    # Show available features
        """
    )

    parser.add_argument("--monitor", action="store_true",
                       help="Run APU-161 intelligent monitoring cycle")
    parser.add_argument("--test", action="store_true",
                       help="Run APU-161 test suite")
    parser.add_argument("--status", action="store_true",
                       help="Show current system status")
    parser.add_argument("--features", action="store_true",
                       help="Show APU-161 features and capabilities")
    parser.add_argument("--quiet", action="store_true",
                       help="Suppress banner output")

    args = parser.parse_args()

    # Show banner unless quiet mode
    if not args.quiet:
        print_banner()

    # Handle commands
    if args.test:
        return run_tests()
    elif args.monitor:
        return run_monitor()
    elif args.status:
        show_status()
        return 0
    elif args.features:
        show_features()
        return 0
    else:
        # Default behavior: show status and available commands
        show_status()
        print(f"\n[TIP] Available Commands:")
        print(f"   --monitor    Run intelligent monitoring cycle")
        print(f"   --test       Run comprehensive test suite")
        print(f"   --status     Show detailed system status")
        print(f"   --features   Show intelligent features")
        print(f"\nFor help: python apu161_launcher.py --help")
        return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n[STOP] Operation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n[ERROR] FATAL ERROR: {e}")
        sys.exit(1)