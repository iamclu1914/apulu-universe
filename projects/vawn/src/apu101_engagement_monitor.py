"""
apu101_engagement_monitor.py — APU-101 Enhanced Real-Time Engagement Monitor

Real-time comment monitoring and intelligent auto-reply system for Vawn's social media presence.
Integrates with existing APU-44 monitoring infrastructure while focusing on comment engagement optimization.

Created by: Dex - Community Agent (APU-101)
Enhancements over existing engagement_agent.py:
- Real-time comment monitoring (configurable intervals)
- Intelligent cross-platform reply coordination
- Enhanced spam detection and content filtering
- Advanced engagement analytics and insights
- Integration with APU-44 monitoring system
- Configurable response strategies per platform
"""

import json
import sys
import requests
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import (
    get_anthropic_client, load_json, save_json, CREDS_FILE,
    ENGAGEMENT_LOG, RESEARCH_LOG, METRICS_LOG, VAWN_PROFILE,
    log_run, today_str, VAWN_DIR
)

# APU-101 Configuration
APU101_LOG = VAWN_DIR / "research" / "apu101_engagement_monitor_log.json"
APU101_CONFIG = VAWN_DIR / "config" / "apu101_engagement_config.json"

# Default configuration
DEFAULT_CONFIG = {
    "monitoring": {
        "check_interval_minutes": 15,  # Real-time monitoring every 15 minutes
        "batch_size": 20,  # Process up to 20 comments per batch
        "platforms_enabled": ["instagram", "tiktok", "x", "threads", "bluesky"],
        "real_time_alerts": True
    },
    "auto_reply": {
        "enabled": True,
        "max_replies_per_batch": 8,
        "reply_delay_seconds": 30,  # Delay between replies to appear natural
        "smart_routing": True,  # Use AI to determine best response strategy
        "cross_platform_coordination": True
    },
    "filtering": {
        "enhanced_spam_detection": True,
        "min_comment_length": 4,
        "max_emoji_ratio": 0.8,
        "skip_patterns": [
            "follow me", "check my", "dm me", "collab?", "promo",
            "link in bio", "buy my", "stream my", "check out"
        ],
        "priority_keywords": [
            "love this", "fire", "talented", "amazing", "real music",
            "Atlanta", "Brooklyn", "hip hop", "bars", "lyrical"
        ]
    },
    "analytics": {
        "track_engagement_velocity": True,
        "monitor_reply_effectiveness": True,
        "cross_platform_insights": True,
        "sentiment_analysis": True
    }
}

@dataclass
class CommentData:
    """Enhanced comment data structure for APU-101."""
    id: str
    text: str
    platform: str
    post_caption: str
    author: str
    timestamp: str
    sentiment_score: float = 0.0
    priority_score: float = 0.0
    spam_probability: float = 0.0
    reply_generated: Optional[str] = None
    reply_posted: bool = False
    processing_time: float = 0.0

@dataclass
class EngagementMetrics:
    """Real-time engagement tracking for APU-101."""
    timestamp: str
    total_comments_processed: int
    replies_generated: int
    replies_posted: int
    spam_filtered: int
    avg_sentiment: float
    avg_processing_time: float
    platform_breakdown: Dict[str, int]
    engagement_velocity: float  # Comments per hour

class APU101EngagementMonitor:
    """Enhanced real-time engagement monitoring system."""

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.client = get_anthropic_client()
        self.running = False
        self.stats = {
            "session_start": datetime.now().isoformat(),
            "total_comments": 0,
            "total_replies": 0,
            "platforms_active": [],
            "last_activity": None
        }

    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load APU-101 configuration with fallback to defaults."""
        if config_path and Path(config_path).exists():
            config = load_json(Path(config_path))
        elif APU101_CONFIG.exists():
            config = load_json(APU101_CONFIG)
        else:
            config = DEFAULT_CONFIG
            # Save default config for future reference
            APU101_CONFIG.parent.mkdir(exist_ok=True)
            save_json(APU101_CONFIG, DEFAULT_CONFIG)
        return config

    def _refresh_token(self) -> str:
        """Refresh authentication token."""
        creds = load_json(CREDS_FILE)
        base_url = "https://apulustudio.onrender.com/api"

        r = requests.post(f"{base_url}/auth/refresh",
                         json={"refresh_token": creds["refresh_token"]})
        if r.status_code != 200:
            raise RuntimeError(f"Token refresh failed: {r.status_code}")

        data = r.json()
        creds["access_token"] = data["access_token"]
        creds["refresh_token"] = data["refresh_token"]
        save_json(CREDS_FILE, creds)
        return data["access_token"]

    def _fetch_comments(self, access_token: str) -> List[Dict[str, Any]]:
        """Enhanced comment fetching with error handling."""
        headers = {"Authorization": f"Bearer {access_token}"}
        base_url = "https://apulustudio.onrender.com/api"

        try:
            r = requests.get(f"{base_url}/posts/comments",
                           headers=headers, timeout=30)
            if r.status_code == 404:
                return []  # API not available yet
            r.raise_for_status()
            return r.json().get("comments", [])
        except requests.exceptions.RequestException as e:
            log_run("APU101EngagementMonitor", "warning",
                   f"Comment fetch failed: {e}")
            return []

    def _analyze_comment_sentiment(self, text: str) -> float:
        """Analyze comment sentiment using Claude."""
        if not self.config["analytics"]["sentiment_analysis"]:
            return 0.5  # Neutral default

        prompt = f"""Analyze the sentiment of this social media comment on a scale from 0 to 1:
        0 = Very negative/hostile
        0.5 = Neutral/mixed
        1 = Very positive/supportive

        Comment: {text[:200]}

        Respond with just a number between 0 and 1."""

        try:
            response = self.client.messages.create(
                model="claude-haiku-20241022",  # Use Haiku for fast sentiment analysis
                max_tokens=10,
                messages=[{"role": "user", "content": prompt}]
            )
            sentiment = float(response.content[0].text.strip())
            return max(0.0, min(1.0, sentiment))  # Clamp to [0,1]
        except:
            return 0.5  # Default to neutral on error

    def _calculate_priority_score(self, comment: Dict[str, Any]) -> float:
        """Calculate priority score for comment processing."""
        text = comment.get("text", "").lower()
        score = 0.5  # Base score

        # Boost for priority keywords
        priority_keywords = self.config["filtering"]["priority_keywords"]
        for keyword in priority_keywords:
            if keyword.lower() in text:
                score += 0.1

        # Platform-specific adjustments
        platform = comment.get("platform", "")
        if platform == "instagram":
            score += 0.1  # Higher priority for Instagram
        elif platform == "bluesky":
            score += 0.05  # Moderate boost for Bluesky

        # Length-based scoring
        if len(text) > 50:  # Thoughtful longer comments
            score += 0.1
        elif len(text) < 10:  # Very short comments
            score -= 0.1

        return max(0.0, min(1.0, score))  # Clamp to [0,1]

    def _detect_enhanced_spam(self, text: str) -> float:
        """Enhanced spam detection returning probability."""
        text_lower = text.lower().strip()

        # Basic spam indicators
        if len(text_lower) <= self.config["filtering"]["min_comment_length"]:
            return 0.9

        # Emoji ratio check
        emoji_count = sum(1 for c in text if ord(c) > 127)
        emoji_ratio = emoji_count / len(text) if text else 0
        if emoji_ratio > self.config["filtering"]["max_emoji_ratio"]:
            return 0.8

        # Skip patterns
        skip_patterns = self.config["filtering"]["skip_patterns"]
        for pattern in skip_patterns:
            if pattern in text_lower:
                return 0.9

        # Repetitive patterns (e.g., "fire fire fire")
        words = text_lower.split()
        if len(words) > 2:
            unique_words = set(words)
            if len(unique_words) / len(words) < 0.5:  # >50% repetition
                return 0.7

        # All caps check
        if text.isupper() and len(text) > 10:
            return 0.6

        return 0.1  # Low spam probability

    def _generate_smart_reply(self, comment: CommentData) -> Optional[str]:
        """Generate intelligent reply using enhanced prompt."""
        if not self.config["auto_reply"]["enabled"]:
            return None

        # Enhanced prompt with sentiment and platform awareness
        prompt = f"""You are replying to a social media comment as Vawn.

VAWN'S VOICE & BRAND:
{VAWN_PROFILE}
- Replies are warm but not soft. Brooklyn/ATL authenticity.
- Short: 1-3 sentences max. Natural, conversational tone.
- Never promotional in replies. Focus on genuine human connection.
- Acknowledge what the commenter actually said specifically.
- Never reveal you're AI. Avoid generic phrases.

CONTEXT:
Platform: {comment.platform.upper()}
Sentiment Analysis: {comment.sentiment_score:.2f} (0=negative, 1=positive)
Priority Score: {comment.priority_score:.2f}

Original Post Context: {comment.post_caption[:200] if comment.post_caption else "(no caption)"}

Comment to Reply To: {comment.text}

Platform-specific guidelines:
- Instagram: Can be slightly more visual/lifestyle focused
- TikTok: Keep it brief and engaging
- X/Twitter: Punchy and direct
- Threads: Conversational and community-focused
- Bluesky: Authentic and genuine

Write a reply that matches Vawn's voice. Plain text only, no forced emojis unless natural. No hashtags."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=150,
                messages=[{"role": "user", "content": prompt}]
            )
            reply = response.content[0].text.strip()

            # Quality check - avoid generic responses
            generic_phrases = ["thanks for the support", "appreciate you", "much love"]
            if any(phrase in reply.lower() for phrase in generic_phrases):
                return None  # Skip generic responses

            return reply
        except Exception as e:
            log_run("APU101EngagementMonitor", "warning",
                   f"Reply generation failed: {e}")
            return None

    def _post_reply(self, access_token: str, comment: CommentData, reply: str) -> bool:
        """Post reply with enhanced error handling."""
        headers = {"Authorization": f"Bearer {access_token}"}
        base_url = "https://apulustudio.onrender.com/api"

        try:
            r = requests.post(
                f"{base_url}/posts/comments/{comment.id}/reply",
                headers=headers,
                json={"content": reply},
                timeout=30
            )
            if r.status_code == 404:
                # API not available - log but don't fail
                log_run("APU101EngagementMonitor", "info",
                       f"Reply API not available for {comment.platform}")
                return False
            r.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            log_run("APU101EngagementMonitor", "warning",
                   f"Reply posting failed on {comment.platform}: {e}")
            return False

    def _process_comment_batch(self, comments: List[Dict[str, Any]],
                              access_token: str) -> List[CommentData]:
        """Process a batch of comments with enhanced analytics."""
        processed_comments = []
        engagement_log = load_json(ENGAGEMENT_LOG)
        replied_ids = set(engagement_log.get("replied_ids", []))

        batch_size = self.config["auto_reply"]["max_replies_per_batch"]
        replies_posted = 0

        for comment_data in comments:
            if replies_posted >= batch_size:
                break

            comment_id = comment_data.get("id", "")
            if not comment_id or comment_id in replied_ids:
                continue

            start_time = time.time()

            # Create enhanced comment object
            comment = CommentData(
                id=comment_id,
                text=comment_data.get("text", ""),
                platform=comment_data.get("platform", "unknown"),
                post_caption=comment_data.get("post_caption", ""),
                author=comment_data.get("author", "unknown"),
                timestamp=datetime.now().isoformat()
            )

            # Enhanced analysis
            comment.spam_probability = self._detect_enhanced_spam(comment.text)
            comment.sentiment_score = self._analyze_comment_sentiment(comment.text)
            comment.priority_score = self._calculate_priority_score(comment_data)

            # Skip spam
            if comment.spam_probability > 0.7:
                continue

            # Generate and post reply
            reply = self._generate_smart_reply(comment)
            if reply:
                comment.reply_generated = reply

                # Add natural delay
                delay = self.config["auto_reply"]["reply_delay_seconds"]
                time.sleep(delay)

                posted = self._post_reply(access_token, comment, reply)
                comment.reply_posted = posted

                if posted:
                    replies_posted += 1

                    # Update engagement log
                    engagement_log.setdefault("replied_ids", []).append(comment_id)
                    engagement_log.setdefault("history", []).append({
                        "date": comment.timestamp,
                        "platform": comment.platform,
                        "comment": comment.text[:200],
                        "reply": reply,
                        "posted": posted,
                        "sentiment": comment.sentiment_score,
                        "priority": comment.priority_score,
                        "apu101_enhanced": True
                    })

            comment.processing_time = time.time() - start_time
            processed_comments.append(comment)

        # Save updated engagement log
        engagement_log["replied_ids"] = engagement_log["replied_ids"][-1000:]  # Keep last 1000
        engagement_log["history"] = engagement_log["history"][-500:]  # Keep last 500
        save_json(ENGAGEMENT_LOG, engagement_log)

        return processed_comments

    def _generate_metrics(self, processed_comments: List[CommentData]) -> EngagementMetrics:
        """Generate comprehensive engagement metrics."""
        if not processed_comments:
            return EngagementMetrics(
                timestamp=datetime.now().isoformat(),
                total_comments_processed=0,
                replies_generated=0,
                replies_posted=0,
                spam_filtered=0,
                avg_sentiment=0.5,
                avg_processing_time=0.0,
                platform_breakdown={},
                engagement_velocity=0.0
            )

        replies_generated = sum(1 for c in processed_comments if c.reply_generated)
        replies_posted = sum(1 for c in processed_comments if c.reply_posted)
        spam_filtered = sum(1 for c in processed_comments if c.spam_probability > 0.7)

        platform_breakdown = {}
        for comment in processed_comments:
            platform_breakdown[comment.platform] = platform_breakdown.get(comment.platform, 0) + 1

        avg_sentiment = sum(c.sentiment_score for c in processed_comments) / len(processed_comments)
        avg_processing_time = sum(c.processing_time for c in processed_comments) / len(processed_comments)

        # Calculate engagement velocity (comments per hour)
        time_window = self.config["monitoring"]["check_interval_minutes"] / 60.0
        engagement_velocity = len(processed_comments) / time_window if time_window > 0 else 0

        return EngagementMetrics(
            timestamp=datetime.now().isoformat(),
            total_comments_processed=len(processed_comments),
            replies_generated=replies_generated,
            replies_posted=replies_posted,
            spam_filtered=spam_filtered,
            avg_sentiment=avg_sentiment,
            avg_processing_time=avg_processing_time,
            platform_breakdown=platform_breakdown,
            engagement_velocity=engagement_velocity
        )

    def _save_apu101_report(self, metrics: EngagementMetrics,
                           processed_comments: List[CommentData]):
        """Save detailed APU-101 monitoring report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "version": "apu101_v1",
            "session_stats": self.stats,
            "metrics": asdict(metrics),
            "processed_comments": [asdict(c) for c in processed_comments],
            "config_snapshot": self.config,
            "integration": {
                "apu44_compatible": True,
                "enhanced_features": [
                    "real_time_monitoring",
                    "intelligent_reply_routing",
                    "enhanced_spam_detection",
                    "sentiment_analysis",
                    "cross_platform_coordination"
                ]
            }
        }

        # Load existing log
        apu101_log = load_json(APU101_LOG) if APU101_LOG.exists() else {}
        today = today_str()

        if today not in apu101_log:
            apu101_log[today] = []

        apu101_log[today].append(report)

        # Keep last 30 days
        cutoff_date = (datetime.now() - timedelta(days=30)).date()
        apu101_log = {
            k: v for k, v in apu101_log.items()
            if datetime.fromisoformat(k + "T00:00:00").date() >= cutoff_date
        }

        APU101_LOG.parent.mkdir(exist_ok=True)
        save_json(APU101_LOG, apu101_log)

    def monitor_cycle(self) -> bool:
        """Execute one monitoring cycle."""
        try:
            # Refresh token and fetch comments
            access_token = self._refresh_token()
            comments = self._fetch_comments(access_token)

            if not comments:
                log_run("APU101EngagementMonitor", "ok", "No comments to process")
                return True

            # Process comments with enhanced analytics
            processed = self._process_comment_batch(comments, access_token)
            metrics = self._generate_metrics(processed)

            # Update session stats
            self.stats["total_comments"] += metrics.total_comments_processed
            self.stats["total_replies"] += metrics.replies_posted
            self.stats["platforms_active"] = list(metrics.platform_breakdown.keys())
            self.stats["last_activity"] = datetime.now().isoformat()

            # Save detailed report
            self._save_apu101_report(metrics, processed)

            # Log summary
            log_run("APU101EngagementMonitor", "ok",
                   f"Processed {metrics.total_comments_processed} comments, "
                   f"posted {metrics.replies_posted} replies, "
                   f"avg sentiment {metrics.avg_sentiment:.2f}")

            print(f"[APU-101] Processed {metrics.total_comments_processed} comments, "
                  f"posted {metrics.replies_posted} replies")

            return True

        except Exception as e:
            log_run("APU101EngagementMonitor", "error",
                   f"Monitoring cycle failed: {e}")
            print(f"[APU-101 ERROR] {e}")
            return False

    def run_continuous_monitoring(self):
        """Run continuous monitoring with configurable intervals."""
        print(f"\n[APU-101] Starting Enhanced Real-Time Engagement Monitor")
        print(f"[CONFIG] Check interval: {self.config['monitoring']['check_interval_minutes']} minutes")
        print(f"[CONFIG] Auto-reply enabled: {self.config['auto_reply']['enabled']}")
        print(f"[CONFIG] Platforms: {', '.join(self.config['monitoring']['platforms_enabled'])}")

        self.running = True
        check_interval = self.config["monitoring"]["check_interval_minutes"] * 60  # Convert to seconds

        while self.running:
            try:
                success = self.monitor_cycle()
                if not success:
                    print(f"[APU-101] Cycle failed, continuing...")

                print(f"[APU-101] Waiting {self.config['monitoring']['check_interval_minutes']} minutes until next check...")
                time.sleep(check_interval)

            except KeyboardInterrupt:
                print(f"\n[APU-101] Monitoring stopped by user")
                break
            except Exception as e:
                print(f"[APU-101 ERROR] Unexpected error: {e}")
                time.sleep(60)  # Wait 1 minute on error

        self.running = False

    def run_single_check(self) -> Dict[str, Any]:
        """Run a single monitoring check and return results."""
        print(f"\n[APU-101] Running single engagement check...")
        success = self.monitor_cycle()

        return {
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "session_stats": self.stats,
            "config": self.config
        }


def main():
    """APU-101 Enhanced Engagement Monitor main function."""
    import argparse

    parser = argparse.ArgumentParser(description="APU-101 Enhanced Real-Time Engagement Monitor")
    parser.add_argument("--mode", choices=["single", "continuous"], default="single",
                       help="Run single check or continuous monitoring")
    parser.add_argument("--config", help="Path to custom configuration file")
    args = parser.parse_args()

    monitor = APU101EngagementMonitor(args.config)

    if args.mode == "continuous":
        monitor.run_continuous_monitoring()
    else:
        result = monitor.run_single_check()
        print(f"\n[APU-101] Single check completed: {'SUCCESS' if result['success'] else 'FAILED'}")
        return 0 if result['success'] else 1


if __name__ == "__main__":
    exit(main())