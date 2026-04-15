"""
manual_engagement_tracker.py — Manual data entry tracking system for APU-44.
Bridge solution to handle platforms without API integrations while backend development is in progress.

Created by: Dex - Community Agent (APU-44)
Purpose: Provide structured manual data entry system and track completion status
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import (
    load_json, save_json, METRICS_LOG, VAWN_DIR, log_run, today_str
)

# Configuration
MANUAL_TRACKER_LOG = VAWN_DIR / "research" / "manual_engagement_tracker_log.json"
PLATFORMS = ["instagram", "tiktok", "x", "threads", "bluesky"]

def scan_manual_entry_needed() -> Dict[str, Any]:
    """
    Scan metrics_log.json to identify all posts requiring manual data entry.
    Returns organized data for manual entry tracking.
    """
    metrics_log = load_json(METRICS_LOG)
    manual_entries_needed = []

    for image_name, dates in metrics_log.items():
        for date, platforms in dates.items():
            for platform, data in platforms.items():
                # Check if manual entry is needed
                if isinstance(data, dict) and "_note" in data and "manual entry needed" in data["_note"]:
                    manual_entries_needed.append({
                        "image": image_name,
                        "date": date,
                        "platform": platform,
                        "status": "pending",
                        "note": data["_note"],
                        "created_at": datetime.now().isoformat()
                    })

    # Group by platform for easier tracking
    by_platform = {}
    for entry in manual_entries_needed:
        platform = entry["platform"]
        if platform not in by_platform:
            by_platform[platform] = []
        by_platform[platform].append(entry)

    # Calculate summary stats
    total_entries = len(manual_entries_needed)
    platforms_affected = len(by_platform)

    return {
        "scan_timestamp": datetime.now().isoformat(),
        "total_entries_needed": total_entries,
        "platforms_affected": platforms_affected,
        "entries": manual_entries_needed,
        "by_platform": by_platform,
        "summary": {platform: len(entries) for platform, entries in by_platform.items()}
    }


def create_manual_entry_template(platform: str, count: int = 1) -> str:
    """
    Create a template for manual data entry based on platform-specific metrics.
    """

    templates = {
        "instagram": """
# Instagram Manual Entry Template
# Copy and paste this template for each post requiring manual entry

{
    "likes": 0,          # Number of likes on the post
    "comments": 0,       # Number of comments on the post
    "saves": 0,          # Number of saves/bookmarks
    "shares": 0          # Number of shares/sends
}

# Instructions:
# 1. Go to Instagram post
# 2. Record the current engagement numbers
# 3. Replace the zeros above with actual numbers
# 4. Use update_manual_entry() function to save
""",

        "x": """
# X (Twitter) Manual Entry Template
# Copy and paste this template for each post requiring manual entry

{
    "likes": 0,          # Number of likes (hearts)
    "reposts": 0,        # Number of reposts/retweets
    "quotes": 0,         # Number of quote tweets
    "replies": 0,        # Number of replies
    "bookmarks": 0,      # Number of bookmarks (if visible)
    "views": 0           # Number of views (if available)
}

# Instructions:
# 1. Go to X/Twitter post
# 2. Record the current engagement numbers
# 3. Replace the zeros above with actual numbers
# 4. Use update_manual_entry() function to save
""",

        "tiktok": """
# TikTok Manual Entry Template
# Copy and paste this template for each post requiring manual entry

{
    "likes": 0,          # Number of likes (hearts)
    "comments": 0,       # Number of comments
    "shares": 0,         # Number of shares
    "saves": 0,          # Number of saves/favorites
    "views": 0,          # Number of views
    "play_time": 0       # Average play time % (if available)
}

# Instructions:
# 1. Go to TikTok post
# 2. Record the current engagement numbers
# 3. Replace the zeros above with actual numbers
# 4. Use update_manual_entry() function to save
""",

        "threads": """
# Threads Manual Entry Template
# Copy and paste this template for each post requiring manual entry

{
    "likes": 0,          # Number of likes
    "replies": 0,        # Number of replies
    "reposts": 0,        # Number of reposts
    "quotes": 0          # Number of quote posts
}

# Instructions:
# 1. Go to Threads post
# 2. Record the current engagement numbers
# 3. Replace the zeros above with actual numbers
# 4. Use update_manual_entry() function to save
""",

        "bluesky": """
# Bluesky Manual Entry Template
# Copy and paste this template for each post requiring manual entry

{
    "likes": 0,          # Number of likes
    "reposts": 0,        # Number of reposts
    "replies": 0,        # Number of replies
    "quotes": 0          # Number of quote posts
}

# Instructions:
# 1. Go to Bluesky post
# 2. Record the current engagement numbers
# 3. Replace the zeros above with actual numbers
# 4. Use update_manual_entry() function to save
"""
    }

    template = templates.get(platform, templates["instagram"])  # Default to Instagram format

    if count > 1:
        return f"# {platform.upper()} - {count} posts need manual entry\n" + template
    else:
        return template


def update_manual_entry(image_name: str, date: str, platform: str, engagement_data: dict) -> bool:
    """
    Update the metrics log with manually entered engagement data.
    """
    try:
        metrics_log = load_json(METRICS_LOG)

        # Validate input
        if image_name not in metrics_log:
            print(f"[ERROR] Image '{image_name}' not found in metrics log")
            return False

        if date not in metrics_log[image_name]:
            print(f"[ERROR] Date '{date}' not found for image '{image_name}'")
            return False

        if platform not in metrics_log[image_name][date]:
            print(f"[ERROR] Platform '{platform}' not found for {image_name} on {date}")
            return False

        # Update the entry
        old_data = metrics_log[image_name][date][platform]
        metrics_log[image_name][date][platform] = engagement_data

        # Add metadata about manual entry
        engagement_data["_manual_entry"] = {
            "updated_at": datetime.now().isoformat(),
            "previous_note": old_data.get("_note", ""),
            "updated_by": "manual_engagement_tracker"
        }

        # Save updated metrics
        save_json(METRICS_LOG, metrics_log)

        print(f"[SUCCESS] Updated {platform} data for {image_name} on {date}")
        print(f"[DATA] {engagement_data}")

        # Log the manual entry
        log_run("ManualEngagementTracker", "ok", f"Manual entry completed: {platform} - {image_name} ({date})")

        return True

    except Exception as e:
        print(f"[ERROR] Failed to update manual entry: {e}")
        log_run("ManualEngagementTracker", "error", f"Manual entry failed: {platform} - {image_name} - {e}")
        return False


def generate_manual_entry_report() -> str:
    """
    Generate a comprehensive report of manual entries needed and completion status.
    """
    scan_data = scan_manual_entry_needed()

    report = []
    report.append("=" * 60)
    report.append("[*] MANUAL ENGAGEMENT DATA ENTRY REPORT")
    report.append(f"[DATE] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 60)

    # Summary
    report.append(f"\n[SUMMARY]")
    report.append(f"  Total Entries Needed: {scan_data['total_entries_needed']}")
    report.append(f"  Platforms Affected: {scan_data['platforms_affected']}")

    # Breakdown by platform
    report.append(f"\n[BREAKDOWN BY PLATFORM]")
    for platform, count in scan_data['summary'].items():
        urgency = "HIGH" if count > 10 else "MEDIUM" if count > 5 else "LOW"
        report.append(f"  [{urgency}] {platform.upper()}: {count} entries needed")

    # Detailed entries
    if scan_data['total_entries_needed'] > 0:
        report.append(f"\n[DETAILED ENTRIES NEEDED]")
        for platform, entries in scan_data['by_platform'].items():
            report.append(f"\n  {platform.upper()} ({len(entries)} entries):")
            for i, entry in enumerate(entries[:10]):  # Show first 10
                report.append(f"    {i+1}. {entry['image']} ({entry['date']})")
            if len(entries) > 10:
                report.append(f"    ... and {len(entries) - 10} more")
    else:
        report.append(f"\n[STATUS] All manual entries complete! 🎉")

    # Instructions
    if scan_data['total_entries_needed'] > 0:
        report.append(f"\n[INSTRUCTIONS]")
        report.append(f"  1. Use create_manual_entry_template(platform) to get entry format")
        report.append(f"  2. Collect engagement data from platform")
        report.append(f"  3. Use update_manual_entry(image, date, platform, data) to save")
        report.append(f"  4. Run this report again to track progress")

    # Quick start commands
    if scan_data['total_entries_needed'] > 0:
        report.append(f"\n[QUICK START]")
        for platform in scan_data['summary']:
            count = scan_data['summary'][platform]
            report.append(f"  {platform}: print(create_manual_entry_template('{platform}', {count}))")

    report.append("\n" + "=" * 60)

    return "\n".join(report)


def save_manual_tracker_report():
    """Save manual entry tracking data to log."""
    scan_data = scan_manual_entry_needed()

    # Load existing tracker log
    tracker_log = load_json(MANUAL_TRACKER_LOG)
    today = today_str()

    if today not in tracker_log:
        tracker_log[today] = []

    # Add current scan results
    tracker_log[today].append(scan_data)

    # Keep only last 30 days
    cutoff_date = (datetime.now() - timedelta(days=30)).date()
    tracker_log = {k: v for k, v in tracker_log.items() if datetime.fromisoformat(k + "T00:00:00").date() >= cutoff_date}

    save_json(MANUAL_TRACKER_LOG, tracker_log)
    return scan_data


def main():
    """Main function for manual engagement tracking."""
    print("\n[*] Manual Engagement Tracker (APU-44) Starting...\n")

    # Generate and display report
    report = generate_manual_entry_report()
    print(report)

    # Save tracking data
    scan_data = save_manual_tracker_report()

    # Log summary
    log_run(
        "ManualEngagementTracker",
        "warning" if scan_data["total_entries_needed"] > 0 else "ok",
        f"APU-44: {scan_data['total_entries_needed']} manual entries needed across {scan_data['platforms_affected']} platforms"
    )

    print(f"\n[SAVE] Manual tracking data saved")

    return scan_data


# Helper functions for interactive use
def quick_entry_instagram(image_name: str, date: str, likes: int, comments: int, saves: int = 0, shares: int = 0):
    """Quick entry function for Instagram data."""
    data = {"likes": likes, "comments": comments, "saves": saves, "shares": shares}
    return update_manual_entry(image_name, date, "instagram", data)

def quick_entry_x(image_name: str, date: str, likes: int, reposts: int, replies: int = 0, bookmarks: int = 0):
    """Quick entry function for X/Twitter data."""
    data = {"likes": likes, "reposts": reposts, "replies": replies, "bookmarks": bookmarks}
    return update_manual_entry(image_name, date, "x", data)

def quick_entry_tiktok(image_name: str, date: str, likes: int, comments: int, shares: int = 0, views: int = 0):
    """Quick entry function for TikTok data."""
    data = {"likes": likes, "comments": comments, "shares": shares, "views": views}
    return update_manual_entry(image_name, date, "tiktok", data)

def quick_entry_threads(image_name: str, date: str, likes: int, replies: int, reposts: int = 0):
    """Quick entry function for Threads data."""
    data = {"likes": likes, "replies": replies, "reposts": reposts}
    return update_manual_entry(image_name, date, "threads", data)


if __name__ == "__main__":
    data = main()

    if data["total_entries_needed"] > 0:
        print(f"\n[ACTION NEEDED] {data['total_entries_needed']} manual entries required")
        print("[TIP] Use quick_entry_* functions for faster data entry")
        exit(1)
    else:
        print(f"\n[OK] All manual entries complete")
        exit(0)