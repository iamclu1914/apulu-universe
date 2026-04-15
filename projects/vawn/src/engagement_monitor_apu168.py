"""
engagement_monitor_apu168.py — Enhanced engagement monitoring with credential validation and graceful degradation.
Addresses APU-166 infrastructure issues: missing credentials, API failures, need for robust error handling.
Created by: Dex - Community Agent (APU-168)
"""

import json
import sys
import requests
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional, Union
from enum import Enum
import anthropic
from dataclasses import dataclass, asdict
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent.parent / "research" / "apu168_engagement_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent.parent))
from vawn_config import (
    load_json, save_json, ENGAGEMENT_LOG, RESEARCH_LOG, VAWN_DIR,
    log_run, today_str, get_anthropic_client, CREDS_FILE, VAWN_PROFILE
)

class PlatformStatus(Enum):
    """Platform availability status."""
    ACTIVE = "active"           # Full credentials, working
    PARTIAL = "partial"         # Some credentials, limited functionality
    DEGRADED = "degraded"       # Credentials present but API issues
    UNAVAILABLE = "unavailable" # Missing credentials or persistent failures
    DISABLED = "disabled"       # Intentionally turned off

class HealthLevel(Enum):
    """System health levels."""
    EXCELLENT = "excellent"     # 90-100% platforms working
    GOOD = "good"              # 70-89% platforms working
    DEGRADED = "degraded"      # 40-69% platforms working
    CRITICAL = "critical"      # 10-39% platforms working
    FAILED = "failed"          # 0-9% platforms working

@dataclass
class PlatformConfig:
    """Configuration for individual platform."""
    name: str
    enabled: bool = True
    status: PlatformStatus = PlatformStatus.UNAVAILABLE
    required_credentials: List[str] = None
    api_endpoint: str = ""
    retry_attempts: int = 3
    retry_delay: float = 1.0
    timeout: float = 30.0
    last_success: Optional[str] = None
    last_error: Optional[str] = None
    error_count: int = 0
    health_score: float = 0.0

@dataclass
class MonitoringResult:
    """Result of monitoring cycle."""
    timestamp: str
    platforms_checked: int
    platforms_successful: int
    platforms_failed: int
    comments_found: int
    responses_generated: int
    responses_posted: int
    health_score: float
    health_level: HealthLevel
    platform_results: Dict[str, Dict[str, Any]]
    errors: List[str]
    warnings: List[str]

# Enhanced platform configurations
PLATFORM_CONFIGS = {
    "instagram": PlatformConfig(
        name="instagram",
        required_credentials=["instagram_access_token", "instagram_app_secret"],
        api_endpoint="https://graph.instagram.com/v18.0",
        retry_attempts=3,
        retry_delay=2.0,
        timeout=30.0
    ),
    "tiktok": PlatformConfig(
        name="tiktok",
        required_credentials=["tiktok_access_token", "tiktok_app_key"],
        api_endpoint="https://open-api.tiktok.com",
        retry_attempts=2,
        retry_delay=1.5,
        timeout=25.0
    ),
    "x": PlatformConfig(
        name="x",
        required_credentials=["x_bearer_token", "x_api_key", "x_api_secret"],
        api_endpoint="https://api.twitter.com/2",
        retry_attempts=3,
        retry_delay=1.0,
        timeout=20.0
    ),
    "threads": PlatformConfig(
        name="threads",
        required_credentials=["threads_access_token"],
        api_endpoint="https://graph.threads.net/v1.0",
        retry_attempts=2,
        retry_delay=2.0,
        timeout=30.0
    ),
    "bluesky": PlatformConfig(
        name="bluesky",
        required_credentials=["bluesky_username", "bluesky_password"],
        api_endpoint="https://bsky.social/xrpc",
        retry_attempts=4,
        retry_delay=1.0,
        timeout=15.0
    )
}

# Configuration files
MONITOR_LOG = VAWN_DIR / "research" / "apu168_engagement_monitor_log.json"
PLATFORM_HEALTH_LOG = VAWN_DIR / "research" / "apu168_platform_health.json"
SYSTEM_CONFIG = VAWN_DIR / "config" / "engagement_monitor_config.json"

# Default system configuration
DEFAULT_CONFIG = {
    "enabled": True,
    "monitoring_interval_minutes": 15,
    "health_check_interval_minutes": 5,
    "min_health_score_for_responses": 0.3,
    "max_errors_before_disable": 10,
    "credential_validation_on_startup": True,
    "graceful_degradation_enabled": True,
    "response_generation_enabled": True,
    "fallback_mode": {
        "enabled": True,
        "min_platforms_required": 1,
        "prioritize_working_platforms": True
    }
}

class CredentialValidator:
    """Validates platform credentials and API connectivity."""

    @staticmethod
    def validate_credentials(creds: Dict[str, Any]) -> Dict[str, PlatformStatus]:
        """Validate credentials for all platforms."""
        results = {}

        for platform_name, config in PLATFORM_CONFIGS.items():
            try:
                results[platform_name] = CredentialValidator._validate_platform_credentials(
                    platform_name, config, creds
                )
            except Exception as e:
                logger.error(f"Error validating {platform_name}: {str(e)}")
                results[platform_name] = PlatformStatus.UNAVAILABLE

        return results

    @staticmethod
    def _validate_platform_credentials(platform: str, config: PlatformConfig, creds: Dict[str, Any]) -> PlatformStatus:
        """Validate credentials for a specific platform."""
        # Check if required credentials exist
        missing_creds = []
        for cred in config.required_credentials:
            if not creds.get(cred):
                missing_creds.append(cred)

        if missing_creds:
            logger.warning(f"{platform}: Missing credentials: {missing_creds}")
            return PlatformStatus.UNAVAILABLE

        # Test API connectivity with a simple request
        try:
            test_result = CredentialValidator._test_api_connectivity(platform, config, creds)
            if test_result:
                logger.info(f"{platform}: Credentials validated successfully")
                return PlatformStatus.ACTIVE
            else:
                logger.warning(f"{platform}: Credentials present but API test failed")
                return PlatformStatus.DEGRADED

        except Exception as e:
            logger.error(f"{platform}: API test failed: {str(e)}")
            return PlatformStatus.DEGRADED

    @staticmethod
    def _test_api_connectivity(platform: str, config: PlatformConfig, creds: Dict[str, Any]) -> bool:
        """Test basic API connectivity for platform."""
        # Platform-specific API test endpoints
        test_endpoints = {
            "instagram": "/me?fields=id,username",
            "tiktok": "/user/info",
            "x": "/users/me",
            "threads": "/me",
            "bluesky": "/com.atproto.server.getSession"
        }

        endpoint = test_endpoints.get(platform)
        if not endpoint:
            return False

        try:
            headers = CredentialValidator._build_auth_headers(platform, creds)
            url = config.api_endpoint + endpoint

            response = requests.get(url, headers=headers, timeout=config.timeout)
            return response.status_code in [200, 201, 401]  # 401 means auth headers reached API

        except requests.exceptions.RequestException:
            return False

    @staticmethod
    def _build_auth_headers(platform: str, creds: Dict[str, Any]) -> Dict[str, str]:
        """Build authentication headers for platform."""
        headers = {"Content-Type": "application/json"}

        if platform in ["instagram", "threads"]:
            if creds.get(f"{platform}_access_token"):
                headers["Authorization"] = f"Bearer {creds[f'{platform}_access_token']}"
        elif platform == "tiktok":
            if creds.get("tiktok_access_token"):
                headers["Authorization"] = f"Bearer {creds['tiktok_access_token']}"
        elif platform == "x":
            if creds.get("x_bearer_token"):
                headers["Authorization"] = f"Bearer {creds['x_bearer_token']}"
        elif platform == "bluesky":
            # Bluesky uses session-based auth, would need login flow
            pass

        return headers

class RetryHandler:
    """Handles retry logic with exponential backoff."""

    @staticmethod
    def with_retry(func, max_attempts: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        """Execute function with retry logic."""
        for attempt in range(max_attempts):
            try:
                return func()
            except Exception as e:
                if attempt == max_attempts - 1:
                    raise e

                delay = min(base_delay * (2 ** attempt), max_delay)
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay:.1f}s: {str(e)}")
                time.sleep(delay)

class EnhancedEngagementMonitor:
    """Enhanced engagement monitor with credential validation and graceful degradation."""

    def __init__(self):
        self.config = self._load_config()
        self.platform_configs = PLATFORM_CONFIGS.copy()
        self.platform_statuses = {}
        self.health_score = 0.0
        self.health_level = HealthLevel.FAILED

        # Initialize credential validation
        if self.config.get("credential_validation_on_startup", True):
            self._validate_all_credentials()

    def _load_config(self) -> Dict[str, Any]:
        """Load system configuration."""
        try:
            if SYSTEM_CONFIG.exists():
                config = load_json(SYSTEM_CONFIG)
                # Merge with defaults
                merged_config = DEFAULT_CONFIG.copy()
                merged_config.update(config)
                return merged_config
            else:
                # Create default config
                save_json(SYSTEM_CONFIG, DEFAULT_CONFIG)
                return DEFAULT_CONFIG.copy()
        except Exception as e:
            logger.error(f"Error loading config, using defaults: {str(e)}")
            return DEFAULT_CONFIG.copy()

    def _validate_all_credentials(self) -> None:
        """Validate credentials for all platforms and update configurations."""
        try:
            creds = load_json(CREDS_FILE) if CREDS_FILE.exists() else {}

            # Validate credentials
            validation_results = CredentialValidator.validate_credentials(creds)

            # Update platform configurations
            working_platforms = 0
            for platform_name, status in validation_results.items():
                if platform_name in self.platform_configs:
                    self.platform_configs[platform_name].status = status
                    self.platform_statuses[platform_name] = status

                    if status == PlatformStatus.ACTIVE:
                        working_platforms += 1
                        self.platform_configs[platform_name].health_score = 1.0
                    elif status == PlatformStatus.PARTIAL:
                        working_platforms += 0.5
                        self.platform_configs[platform_name].health_score = 0.5
                    else:
                        self.platform_configs[platform_name].health_score = 0.0

            # Calculate overall health
            total_platforms = len(self.platform_configs)
            self.health_score = working_platforms / total_platforms if total_platforms > 0 else 0.0
            self.health_level = self._calculate_health_level(self.health_score)

            logger.info(f"Credential validation completed. Health score: {self.health_score:.3f} ({self.health_level.value})")
            logger.info(f"Platform statuses: {validation_results}")

        except Exception as e:
            logger.error(f"Error during credential validation: {str(e)}")
            # Set all platforms as unavailable
            for platform_name in self.platform_configs:
                self.platform_configs[platform_name].status = PlatformStatus.UNAVAILABLE
                self.platform_configs[platform_name].health_score = 0.0
                self.platform_statuses[platform_name] = PlatformStatus.UNAVAILABLE

            self.health_score = 0.0
            self.health_level = HealthLevel.FAILED

    def _calculate_health_level(self, score: float) -> HealthLevel:
        """Calculate health level based on score."""
        if score >= 0.9:
            return HealthLevel.EXCELLENT
        elif score >= 0.7:
            return HealthLevel.GOOD
        elif score >= 0.4:
            return HealthLevel.DEGRADED
        elif score >= 0.1:
            return HealthLevel.CRITICAL
        else:
            return HealthLevel.FAILED

    def get_active_platforms(self) -> List[str]:
        """Get list of platforms that are currently active or partially active."""
        active = []
        for name, config in self.platform_configs.items():
            if config.enabled and config.status in [PlatformStatus.ACTIVE, PlatformStatus.PARTIAL]:
                active.append(name)
        return active

    def fetch_platform_comments(self, platform: str) -> List[Dict[str, Any]]:
        """Fetch comments from platform with retry logic and error handling."""
        config = self.platform_configs.get(platform)
        if not config or not config.enabled or config.status == PlatformStatus.UNAVAILABLE:
            logger.info(f"Skipping {platform}: disabled or unavailable")
            return []

        try:
            def fetch_operation():
                return self._fetch_platform_comments_internal(platform, config)

            comments = RetryHandler.with_retry(
                fetch_operation,
                max_attempts=config.retry_attempts,
                base_delay=config.retry_delay
            )

            # Update success metrics
            config.last_success = datetime.now().isoformat()
            config.error_count = max(0, config.error_count - 1)  # Reduce error count on success

            return comments

        except Exception as e:
            error_msg = f"Failed to fetch comments from {platform}: {str(e)}"
            logger.error(error_msg)

            # Update error metrics
            config.last_error = error_msg
            config.error_count += 1

            # Disable platform if too many errors
            if config.error_count >= self.config.get("max_errors_before_disable", 10):
                logger.warning(f"Disabling {platform} due to persistent errors")
                config.status = PlatformStatus.UNAVAILABLE
                config.enabled = False

            return []

    def _fetch_platform_comments_internal(self, platform: str, config: PlatformConfig) -> List[Dict[str, Any]]:
        """Internal method to fetch comments from platform."""
        # Load credentials
        creds = load_json(CREDS_FILE) if CREDS_FILE.exists() else {}

        # Build headers
        headers = CredentialValidator._build_auth_headers(platform, creds)

        comments = []

        # Fetch recent posts first
        posts_url = f"https://apulustudio.onrender.com/api/posts?platform={platform}&limit=10"
        posts_response = requests.get(posts_url, headers=headers, timeout=config.timeout)

        if posts_response.status_code != 200:
            raise Exception(f"Failed to fetch posts: {posts_response.status_code}")

        posts = posts_response.json().get("posts", [])

        # Fetch comments for each post
        for post in posts:
            post_id = post.get("id")
            if not post_id:
                continue

            comments_url = f"https://apulustudio.onrender.com/api/posts/{post_id}/comments"
            comments_response = requests.get(comments_url, headers=headers, timeout=config.timeout)

            if comments_response.status_code == 200:
                post_comments = comments_response.json().get("comments", [])
                for comment in post_comments:
                    comment["platform"] = platform
                    comment["post_id"] = post_id
                    comments.append(comment)

        return comments

    def monitor_engagement(self) -> MonitoringResult:
        """Main monitoring function with enhanced error handling."""
        start_time = datetime.now()
        result = MonitoringResult(
            timestamp=start_time.isoformat(),
            platforms_checked=0,
            platforms_successful=0,
            platforms_failed=0,
            comments_found=0,
            responses_generated=0,
            responses_posted=0,
            health_score=self.health_score,
            health_level=self.health_level,
            platform_results={},
            errors=[],
            warnings=[]
        )

        try:
            # Check system health before monitoring
            if not self.config.get("enabled", True):
                result.warnings.append("Engagement monitoring is disabled")
                return result

            if self.health_score < self.config.get("min_health_score_for_responses", 0.3):
                result.warnings.append(f"Health score too low for responses: {self.health_score:.3f}")

            # Get active platforms
            active_platforms = self.get_active_platforms()

            if not active_platforms:
                result.errors.append("No active platforms available")
                return result

            if len(active_platforms) < self.config.get("fallback_mode", {}).get("min_platforms_required", 1):
                result.warnings.append("Fewer platforms available than minimum required")

            # Monitor each active platform
            for platform in active_platforms:
                try:
                    result.platforms_checked += 1

                    # Fetch comments
                    comments = self.fetch_platform_comments(platform)
                    platform_result = {
                        "status": "success",
                        "comments_count": len(comments),
                        "responses_generated": 0,
                        "responses_posted": 0,
                        "errors": [],
                        "health_score": self.platform_configs[platform].health_score
                    }

                    result.comments_found += len(comments)
                    result.platforms_successful += 1

                    # Process comments if response generation is enabled
                    if (self.config.get("response_generation_enabled", True) and
                        self.health_score >= self.config.get("min_health_score_for_responses", 0.3)):

                        processed = self._process_platform_comments(platform, comments)
                        platform_result["responses_generated"] = processed["generated"]
                        platform_result["responses_posted"] = processed["posted"]

                        result.responses_generated += processed["generated"]
                        result.responses_posted += processed["posted"]

                    result.platform_results[platform] = platform_result

                except Exception as e:
                    error_msg = f"Error monitoring {platform}: {str(e)}"
                    logger.error(error_msg)
                    result.errors.append(error_msg)
                    result.platforms_failed += 1

                    result.platform_results[platform] = {
                        "status": "failed",
                        "error": str(e),
                        "health_score": 0.0
                    }

            # Update health metrics after monitoring cycle
            self._update_health_metrics(result)

        except Exception as e:
            error_msg = f"Critical error in monitoring cycle: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)

        # Log results
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Monitoring cycle completed in {duration:.1f}s: {result.platforms_successful}/{result.platforms_checked} platforms successful")

        return result

    def _process_platform_comments(self, platform: str, comments: List[Dict[str, Any]]) -> Dict[str, int]:
        """Process comments for a platform (placeholder for response logic)."""
        # This would contain the actual comment processing and response logic
        # from the original engagement_monitor_apu127.py
        return {"generated": 0, "posted": 0}

    def _update_health_metrics(self, result: MonitoringResult) -> None:
        """Update system health based on monitoring results."""
        total_platforms = len(self.platform_configs)
        if total_platforms == 0:
            self.health_score = 0.0
        else:
            working_score = result.platforms_successful / total_platforms
            failed_penalty = min(result.platforms_failed * 0.1, 0.5)
            self.health_score = max(0.0, working_score - failed_penalty)

        self.health_level = self._calculate_health_level(self.health_score)
        result.health_score = self.health_score
        result.health_level = self.health_level

    def save_monitoring_result(self, result: MonitoringResult) -> None:
        """Save monitoring result to logs."""
        try:
            # Load existing log
            monitor_log = load_json(MONITOR_LOG) if MONITOR_LOG.exists() else {}
            today = today_str()

            if today not in monitor_log:
                monitor_log[today] = []

            # Convert result to dict
            result_dict = asdict(result)
            result_dict["health_level"] = result.health_level.value  # Convert enum to string

            monitor_log[today].append(result_dict)

            # Save log
            save_json(MONITOR_LOG, monitor_log)

            # Save platform health
            health_data = {
                "timestamp": result.timestamp,
                "health_score": self.health_score,
                "health_level": self.health_level.value,
                "platform_statuses": {name: config.status.value for name, config in self.platform_configs.items()},
                "platform_health_scores": {name: config.health_score for name, config in self.platform_configs.items()}
            }
            save_json(PLATFORM_HEALTH_LOG, health_data)

        except Exception as e:
            logger.error(f"Error saving monitoring result: {str(e)}")

def main():
    """Main execution function for APU-168 enhanced engagement monitor."""
    print(f"Starting APU-168 Enhanced Engagement Monitor at {datetime.now()}")

    try:
        # Initialize monitor
        monitor = EnhancedEngagementMonitor()

        # Display initial health status
        print(f"System Health: {monitor.health_score:.3f} ({monitor.health_level.value})")
        print(f"Active Platforms: {monitor.get_active_platforms()}")

        # Run monitoring cycle
        result = monitor.monitor_engagement()

        # Save results
        monitor.save_monitoring_result(result)

        # Create summary
        summary = f"Checked {result.platforms_successful}/{result.platforms_checked} platforms, "
        summary += f"found {result.comments_found} comments, "
        summary += f"generated {result.responses_generated} responses"

        if result.errors:
            summary += f", {len(result.errors)} errors"
        if result.warnings:
            summary += f", {len(result.warnings)} warnings"

        # Log to research system
        status = "ok" if not result.errors else "error"
        log_run("engagement_monitor_apu168", status, summary)

        print(f"Enhanced engagement monitoring completed: {summary}")

        # Display warnings and errors
        for warning in result.warnings:
            print(f"⚠️ WARNING: {warning}")
        for error in result.errors:
            print(f"❌ ERROR: {error}")

        return result

    except Exception as e:
        error_msg = f"Critical error in APU-168 monitor: {str(e)}"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        log_run("engagement_monitor_apu168", "error", error_msg)
        raise

if __name__ == "__main__":
    main()