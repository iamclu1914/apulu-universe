#!/usr/bin/env python3
"""
run_apu151_engagement_monitor.py — APU-151 Engagement Monitor Launcher

Quick launcher script for the APU-151 Enhanced Engagement Monitor
Created by: Dex - Community Agent (APU-151)
"""

import sys
import subprocess
from pathlib import Path

# Add paths
vawn_dir = Path(__file__).parent.parent
src_dir = vawn_dir / "src"
sys.path.insert(0, str(vawn_dir))
sys.path.insert(0, str(src_dir))

def main():
    """Run APU-151 Enhanced Engagement Monitor"""
    try:
        print("[*] APU-151 Engagement Monitor Launcher")
        print("[*] Starting enhanced community engagement monitoring...")
        print()

        # Import and run the monitor
        from apu151_engagement_monitor import main as apu151_main

        result = apu151_main()

        system_status = result.get("system_status", "unknown")
        health_score = result.get("summary", {}).get("overall_health_score", 0.0)

        print(f"\n[LAUNCHER] Monitoring complete")
        print(f"[RESULT] System Status: {system_status.upper()}")
        print(f"[RESULT] Health Score: {health_score:.1%}")

        return result

    except KeyboardInterrupt:
        print("\n[LAUNCHER] Monitoring interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n[ERROR] Failed to run APU-151 monitor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    result = main()

    # Exit with appropriate code based on system status
    system_status = result.get("system_status", "unknown")

    if system_status == "critical":
        sys.exit(2)
    elif system_status == "warning":
        sys.exit(1)
    else:
        sys.exit(0)