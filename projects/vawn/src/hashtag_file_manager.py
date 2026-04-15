"""
hashtag_file_manager.py — Unified hashtag file management and organization
Created by: Sage - Content Agent (APU-26)

Consolidates inconsistent hashtag file naming, implements cleanup routines,
and provides standardized file management across the hashtag system.
"""

import json
import shutil
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set
import sys

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import VAWN_DIR, EXPORTS_DIR, load_json, save_json

# File management configuration
HASHTAG_BASE_DIR = VAWN_DIR / "Social_Media_Exports" / "Trending_Hashtags"
HASHTAG_ARCHIVE_DIR = HASHTAG_BASE_DIR / "archive"
HASHTAG_BACKUP_DIR = HASHTAG_BASE_DIR / "backups"

# Standard file naming convention
CURRENT_FILENAME = "hashtags.txt"
ARCHIVE_FILENAME_FORMAT = "hashtags_{date}.txt"  # hashtags_2026-04-10.txt
LATEST_SYMLINK = "latest.txt"

PLATFORMS = ["Instagram", "TikTok", "X", "Threads", "Bluesky"]


class HashtagFileManager:
    """Unified hashtag file management system"""

    def __init__(self):
        self.base_dir = HASHTAG_BASE_DIR
        self.archive_dir = HASHTAG_ARCHIVE_DIR
        self.backup_dir = HASHTAG_BACKUP_DIR

        # Ensure directories exist
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def discover_file_patterns(self) -> Dict[str, Dict[str, List[Path]]]:
        """Discover all hashtag files and categorize by platform and type."""
        file_inventory = {platform: {"current": [], "dated": [], "latest": [], "other": []}
                         for platform in PLATFORMS}

        for platform in PLATFORMS:
            platform_dir = self.base_dir / platform
            if not platform_dir.exists():
                continue

            for file_path in platform_dir.iterdir():
                if not file_path.is_file():
                    continue

                filename = file_path.name.lower()

                # Categorize file types
                if filename == "hashtags.txt":
                    file_inventory[platform]["current"].append(file_path)
                elif filename == "latest.txt":
                    file_inventory[platform]["latest"].append(file_path)
                elif filename.startswith("hashtags_") and filename.endswith(".txt"):
                    file_inventory[platform]["dated"].append(file_path)
                else:
                    file_inventory[platform]["other"].append(file_path)

        return file_inventory

    def standardize_file_structure(self, backup: bool = True) -> Dict[str, any]:
        """Standardize all hashtag files to consistent naming convention."""
        inventory = self.discover_file_patterns()
        actions_taken = {
            "backups_created": 0,
            "files_archived": 0,
            "duplicates_removed": 0,
            "symlinks_created": 0,
            "errors": []
        }

        for platform in PLATFORMS:
            platform_dir = self.base_dir / platform
            platform_archive = self.archive_dir / platform
            platform_backup = self.backup_dir / platform

            if not platform_dir.exists():
                continue

            # Create archive and backup dirs
            platform_archive.mkdir(exist_ok=True)
            platform_backup.mkdir(exist_ok=True)

            platform_files = inventory[platform]

            try:
                # 1. Backup existing files if requested
                if backup:
                    backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    platform_backup_timestamped = platform_backup / backup_timestamp
                    platform_backup_timestamped.mkdir(exist_ok=True)

                    for file_category, files in platform_files.items():
                        for file_path in files:
                            backup_path = platform_backup_timestamped / file_path.name
                            shutil.copy2(file_path, backup_path)
                            actions_taken["backups_created"] += 1

                # 2. Identify the most current file
                current_file = None
                latest_date = None

                # Check current hashtags.txt first
                if platform_files["current"]:
                    current_file = platform_files["current"][0]
                    latest_date = current_file.stat().st_mtime

                # Check dated files for newer content
                for dated_file in platform_files["dated"]:
                    file_date = self._extract_date_from_filename(dated_file.name)
                    if file_date:
                        file_timestamp = file_date.timestamp()
                        if latest_date is None or file_timestamp > latest_date:
                            current_file = dated_file
                            latest_date = file_timestamp

                # Check latest.txt files
                for latest_file in platform_files["latest"]:
                    file_timestamp = latest_file.stat().st_mtime
                    if latest_date is None or file_timestamp > latest_date:
                        current_file = latest_file
                        latest_date = file_timestamp

                # 3. Create standardized current file
                if current_file:
                    standard_current = platform_dir / CURRENT_FILENAME

                    # If current file isn't already the standard name, create it
                    if current_file.name != CURRENT_FILENAME:
                        shutil.copy2(current_file, standard_current)

                # 4. Archive dated files (but keep most recent 7 days)
                cutoff_date = date.today() - timedelta(days=7)

                for dated_file in platform_files["dated"]:
                    file_date = self._extract_date_from_filename(dated_file.name)
                    if file_date and file_date < cutoff_date:
                        # Archive old dated files
                        archive_path = platform_archive / dated_file.name
                        shutil.move(str(dated_file), str(archive_path))
                        actions_taken["files_archived"] += 1

                # 5. Remove duplicate latest.txt files
                for latest_file in platform_files["latest"]:
                    if latest_file != current_file:
                        latest_file.unlink()
                        actions_taken["duplicates_removed"] += 1

                # 6. Create latest.txt symlink to current file
                latest_symlink = platform_dir / LATEST_SYMLINK
                current_standard = platform_dir / CURRENT_FILENAME

                if latest_symlink.exists():
                    latest_symlink.unlink()

                if current_standard.exists():
                    # Create copy instead of symlink for Windows compatibility
                    shutil.copy2(current_standard, latest_symlink)
                    actions_taken["symlinks_created"] += 1

            except Exception as e:
                actions_taken["errors"].append(f"{platform}: {str(e)}")

        return actions_taken

    def _extract_date_from_filename(self, filename: str) -> Optional[date]:
        """Extract date from filename like 'hashtags_2026-04-10.txt'."""
        import re

        # Pattern: hashtags_YYYY-MM-DD.txt
        pattern = r'hashtags_(\d{4})-(\d{2})-(\d{2})\.txt'
        match = re.search(pattern, filename)

        if match:
            year, month, day = map(int, match.groups())
            try:
                return date(year, month, day)
            except ValueError:
                pass

        return None

    def cleanup_old_files(self, days_to_keep: int = 30) -> Dict[str, int]:
        """Clean up old archived files beyond retention period."""
        cleanup_stats = {
            "files_deleted": 0,
            "space_freed_mb": 0,
            "errors": 0
        }

        cutoff_date = date.today() - timedelta(days=days_to_keep)

        for platform in PLATFORMS:
            platform_archive = self.archive_dir / platform
            if not platform_archive.exists():
                continue

            for archive_file in platform_archive.iterdir():
                if not archive_file.is_file():
                    continue

                try:
                    # Check file age
                    file_date = self._extract_date_from_filename(archive_file.name)
                    if file_date and file_date < cutoff_date:
                        file_size = archive_file.stat().st_size
                        archive_file.unlink()
                        cleanup_stats["files_deleted"] += 1
                        cleanup_stats["space_freed_mb"] += file_size / (1024 * 1024)
                except Exception:
                    cleanup_stats["errors"] += 1

        return cleanup_stats

    def create_daily_snapshot(self, custom_date: Optional[date] = None) -> Dict[str, bool]:
        """Create daily snapshot of current hashtags with standardized naming."""
        snapshot_date = custom_date or date.today()
        snapshot_filename = ARCHIVE_FILENAME_FORMAT.format(date=snapshot_date.isoformat())

        results = {}

        for platform in PLATFORMS:
            platform_dir = self.base_dir / platform
            current_file = platform_dir / CURRENT_FILENAME
            snapshot_file = platform_dir / snapshot_filename

            if current_file.exists() and not snapshot_file.exists():
                try:
                    shutil.copy2(current_file, snapshot_file)
                    results[platform] = True
                except Exception:
                    results[platform] = False
            else:
                results[platform] = False

        return results

    def validate_file_integrity(self) -> Dict[str, Dict[str, any]]:
        """Validate hashtag file integrity and content."""
        validation_results = {}

        for platform in PLATFORMS:
            platform_dir = self.base_dir / platform
            current_file = platform_dir / CURRENT_FILENAME

            platform_results = {
                "file_exists": False,
                "is_readable": False,
                "hashtag_count": 0,
                "valid_hashtags": 0,
                "issues": []
            }

            if current_file.exists():
                platform_results["file_exists"] = True

                try:
                    content = current_file.read_text(encoding="utf-8")
                    platform_results["is_readable"] = True

                    hashtags = [line.strip() for line in content.splitlines() if line.strip()]
                    platform_results["hashtag_count"] = len(hashtags)

                    # Validate hashtag format
                    valid_count = 0
                    for hashtag in hashtags:
                        if hashtag.startswith("#") and len(hashtag) > 1 and hashtag[1:].replace("_", "").isalnum():
                            valid_count += 1
                        else:
                            platform_results["issues"].append(f"Invalid hashtag format: {hashtag}")

                    platform_results["valid_hashtags"] = valid_count

                    # Check for duplicates
                    if len(hashtags) != len(set(hashtags)):
                        duplicates = len(hashtags) - len(set(hashtags))
                        platform_results["issues"].append(f"{duplicates} duplicate hashtags found")

                except Exception as e:
                    platform_results["issues"].append(f"Read error: {str(e)}")

            else:
                platform_results["issues"].append("Current hashtags file missing")

            validation_results[platform] = platform_results

        return validation_results

    def generate_status_report(self) -> Dict[str, any]:
        """Generate comprehensive file management status report."""
        inventory = self.discover_file_patterns()
        validation = self.validate_file_integrity()

        report = {
            "timestamp": datetime.now().isoformat(),
            "base_directory": str(self.base_dir),
            "platforms": PLATFORMS,
            "file_inventory": {
                platform: {
                    file_type: len(files) for file_type, files in platform_files.items()
                }
                for platform, platform_files in inventory.items()
            },
            "validation_results": validation,
            "total_files": sum(
                sum(len(files) for files in platform_files.values())
                for platform_files in inventory.values()
            ),
            "healthy_platforms": [
                platform for platform, results in validation.items()
                if results["file_exists"] and results["valid_hashtags"] > 0
            ]
        }

        return report


def main():
    """Main file management execution."""
    print("\n[*] Hashtag File Manager - APU-26")
    print("=" * 50)

    manager = HashtagFileManager()

    # 1. Generate status report
    print("\n[1] Analyzing current file structure...")
    report = manager.generate_status_report()

    print(f"Total Files: {report['total_files']}")
    print(f"Healthy Platforms: {len(report['healthy_platforms'])}/{len(PLATFORMS)}")

    for platform in PLATFORMS:
        inventory = report['file_inventory'][platform]
        total_platform_files = sum(inventory.values())
        print(f"  {platform}: {total_platform_files} files ({inventory})")

    # 2. Standardize file structure
    print(f"\n[2] Standardizing file structure...")
    standardization_results = manager.standardize_file_structure(backup=True)

    print(f"Backups Created: {standardization_results['backups_created']}")
    print(f"Files Archived: {standardization_results['files_archived']}")
    print(f"Duplicates Removed: {standardization_results['duplicates_removed']}")
    print(f"Symlinks Created: {standardization_results['symlinks_created']}")

    if standardization_results['errors']:
        print(f"Errors: {len(standardization_results['errors'])}")
        for error in standardization_results['errors']:
            print(f"  - {error}")

    # 3. Validate integrity
    print(f"\n[3] Validating file integrity...")
    validation = manager.validate_file_integrity()

    issues_found = 0
    for platform, results in validation.items():
        if results['issues']:
            issues_found += len(results['issues'])
            print(f"  {platform}: {len(results['issues'])} issues")
            for issue in results['issues'][:2]:  # Show first 2 issues
                print(f"    - {issue}")

    if issues_found == 0:
        print("  All files validated successfully!")

    # 4. Create daily snapshot
    print(f"\n[4] Creating daily snapshot...")
    snapshot_results = manager.create_daily_snapshot()
    successful_snapshots = sum(snapshot_results.values())
    print(f"Snapshots Created: {successful_snapshots}/{len(PLATFORMS)}")

    # 5. Cleanup old files
    print(f"\n[5] Cleaning up old files...")
    cleanup_results = manager.cleanup_old_files(days_to_keep=30)
    print(f"Files Deleted: {cleanup_results['files_deleted']}")
    print(f"Space Freed: {cleanup_results['space_freed_mb']:.1f} MB")

    print(f"\n[OK] File management optimization complete!")
    print(f"[STATUS] {len(report['healthy_platforms'])}/{len(PLATFORMS)} platforms healthy")

    return report


if __name__ == "__main__":
    main()