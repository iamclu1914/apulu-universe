"""
start_engagement_monitor.py — Background monitoring launcher for APU-133.
Launches real-time engagement monitoring with proper logging and error handling.
"""

import sys
import subprocess
from pathlib import Path

# Add Vawn directory to path
VAWN_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(VAWN_DIR))

def start_monitor():
    """Start the engagement monitor as a background process."""
    monitor_script = VAWN_DIR / "src" / "engagement_monitor.py"

    if not monitor_script.exists():
        print(f"❌ Monitor script not found: {monitor_script}")
        return False

    try:
        print("🚀 Starting Engagement Monitor (APU-133)...")
        print(f"📂 Script: {monitor_script}")
        print("ℹ️  Use Ctrl+C to stop monitoring")
        print("=" * 50)

        # Run the monitor script
        subprocess.run([sys.executable, str(monitor_script)], check=True)

    except subprocess.CalledProcessError as e:
        print(f"❌ Monitor failed with exit code {e.returncode}")
        return False
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")
        return True
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

    return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Start Vawn Engagement Monitor")
    parser.add_argument("--status", action="store_true", help="Check monitor status instead of starting")
    parser.add_argument("--dashboard", action="store_true", help="Show dashboard instead of starting monitor")
    args = parser.parse_args()

    if args.status:
        # Check status
        monitor_script = VAWN_DIR / "src" / "engagement_monitor.py"
        subprocess.run([sys.executable, str(monitor_script), "--status"])
    elif args.dashboard:
        # Show dashboard
        dashboard_script = VAWN_DIR / "src" / "engagement_dashboard.py"
        subprocess.run([sys.executable, str(dashboard_script)])
    else:
        # Start monitoring
        start_monitor()