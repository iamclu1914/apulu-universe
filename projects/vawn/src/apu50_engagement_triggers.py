"""
apu50_engagement_triggers.py — APU-50 Engagement Trigger Automation

Automated engagement trigger system that deploys conversation starters strategically
based on optimal timing, platform dynamics, and community momentum analysis.

Created by: Dex - Community Agent (APU-50)

Features:
- Time-based trigger automation
- Platform-specific engagement optimization
- Momentum-based topic selection
- Quality feedback loops
- Cross-platform coordination
"""

import json
import sys
import random
import schedule
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
sys.path.insert(0, r"C:\Users\rdyal\Vawn\src")

from vawn_config import (
    load_json, save_json, VAWN_DIR, log_run, today_str,
    get_anthropic_client, VAWN_PROFILE
)
from apu50_community_conversation_engine import CommunityConversationEngine

# Configuration
TRIGGERS_LOG = VAWN_DIR / "research" / "apu50_engagement_triggers_log.json"
CONVERSATION_TEMPLATES = VAWN_DIR / "src" / "conversation_templates" / "vawn_conversation_starters.json"

# Engagement timing strategy
ENGAGEMENT_SCHEDULE = {
    "monday": {
        "09:00": {"category": "motivation_monday", "platforms": ["bluesky", "instagram"], "priority": "high"},
        "13:00": {"category": "music_discovery", "platforms": ["threads"], "priority": "medium"},
        "19:00": {"category": "industry_insights", "platforms": ["bluesky"], "priority": "medium"}
    },
    "tuesday": {
        "10:00": {"category": "creative_process", "platforms": ["instagram", "bluesky"], "priority": "high"},
        "15:00": {"category": "music_opinions", "platforms": ["x", "threads"], "priority": "medium"},
        "20:00": {"category": "community_challenges", "platforms": ["tiktok"], "priority": "high"}
    },
    "wednesday": {
        "09:00": {"category": "music_discovery", "platforms": ["bluesky"], "priority": "medium"},
        "14:00": {"category": "creative_process", "platforms": ["instagram"], "priority": "high"},
        "18:00": {"category": "music_opinions", "platforms": ["threads", "x"], "priority": "medium"}
    },
    "thursday": {
        "11:00": {"category": "industry_insights", "platforms": ["bluesky", "threads"], "priority": "medium"},
        "16:00": {"category": "cultural_moments", "platforms": ["x", "bluesky"], "priority": "high"},
        "21:00": {"category": "community_challenges", "platforms": ["tiktok", "instagram"], "priority": "high"}
    },
    "friday": {
        "10:00": {"category": "music_discovery", "platforms": ["bluesky"], "priority": "medium"},
        "17:00": {"category": "weekend_vibes", "platforms": ["instagram", "tiktok"], "priority": "high"},
        "22:00": {"category": "community_challenges", "platforms": ["tiktok"], "priority": "medium"}
    },
    "saturday": {
        "12:00": {"category": "weekend_vibes", "platforms": ["instagram"], "priority": "high"},
        "18:00": {"category": "music_discovery", "platforms": ["bluesky", "tiktok"], "priority": "medium"},
        "23:00": {"category": "cultural_moments", "platforms": ["x"], "priority": "low"}
    },
    "sunday": {
        "11:00": {"category": "weekend_vibes", "platforms": ["instagram"], "priority": "medium"},
        "16:00": {"category": "music_opinions", "platforms": ["bluesky", "threads"], "priority": "medium"},
        "20:00": {"category": "creative_process", "platforms": ["bluesky"], "priority": "high"}
    }
}

# Platform-specific engagement strategies
PLATFORM_ENGAGEMENT_RULES = {
    "bluesky": {
        "max_daily_posts": 4,
        "min_interval_hours": 3,
        "engagement_style": "conversation_focused",
        "follow_up_strategy": "active_discussion",
        "peak_hours": ["09:00", "13:00", "19:00"]
    },
    "instagram": {
        "max_daily_posts": 2,
        "min_interval_hours": 6,
        "engagement_style": "visual_storytelling",
        "follow_up_strategy": "story_engagement",
        "peak_hours": ["11:00", "14:00", "17:00"]
    },
    "tiktok": {
        "max_daily_posts": 3,
        "min_interval_hours": 4,
        "engagement_style": "trend_participation",
        "follow_up_strategy": "response_videos",
        "peak_hours": ["06:00", "10:00", "19:00"]
    },
    "threads": {
        "max_daily_posts": 3,
        "min_interval_hours": 4,
        "engagement_style": "thought_leadership",
        "follow_up_strategy": "discussion_threads",
        "peak_hours": ["08:00", "12:00", "20:00"]
    },
    "x": {
        "max_daily_posts": 5,
        "min_interval_hours": 2,
        "engagement_style": "real_time_commentary",
        "follow_up_strategy": "rapid_responses",
        "peak_hours": ["08:00", "12:00", "17:00"]
    }
}


class EngagementTriggerSystem:
    """Automated engagement trigger deployment system."""

    def __init__(self):
        self.engine = CommunityConversationEngine()
        self.templates = self._load_conversation_templates()
        self.triggers_log = load_json(TRIGGERS_LOG) if Path(TRIGGERS_LOG).exists() else {}
        self.daily_post_counts = defaultdict(lambda: defaultdict(int))

    def _load_conversation_templates(self) -> Dict:
        """Load conversation templates from JSON file."""
        try:
            return load_json(CONVERSATION_TEMPLATES)
        except Exception as e:
            print(f"[WARNING] Could not load conversation templates: {e}")
            return {}

    def should_trigger_engagement(self, time_slot: str, platform: str, category: str) -> bool:
        """Determine if engagement should be triggered based on various factors."""

        # Check daily post limits
        today = today_str()
        platform_rules = PLATFORM_ENGAGEMENT_RULES.get(platform, {})
        max_daily = platform_rules.get("max_daily_posts", 3)
        current_count = self.daily_post_counts[today][platform]

        if current_count >= max_daily:
            return False

        # Check minimum interval between posts
        min_interval = platform_rules.get("min_interval_hours", 3)
        last_post_time = self._get_last_post_time(platform)

        if last_post_time:
            time_since_last = datetime.now() - last_post_time
            if time_since_last.total_seconds() < (min_interval * 3600):
                return False

        # Check if it's peak engagement time
        peak_hours = platform_rules.get("peak_hours", [])
        if time_slot not in peak_hours:
            # Lower probability for non-peak hours
            return random.random() > 0.7

        return True

    def trigger_engagement(self, category: str, platforms: List[str], priority: str) -> Dict[str, Any]:
        """Trigger engagement across specified platforms."""

        results = {
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "platforms": platforms,
            "priority": priority,
            "deployments": {},
            "success_count": 0,
            "errors": []
        }

        for platform in platforms:
            try:
                if not self.should_trigger_engagement(datetime.now().strftime("%H:%M"), platform, category):
                    results["deployments"][platform] = {
                        "status": "skipped",
                        "reason": "rate_limiting_or_timing"
                    }
                    continue

                # Generate conversation for platform
                conversation = self.engine.generate_conversation_starter(category, platform)

                if "error" in conversation:
                    results["errors"].append(f"{platform}: {conversation['error']}")
                    continue

                # Deploy conversation (in real implementation, this would post to platform)
                deployment = self._deploy_conversation(conversation, platform)

                results["deployments"][platform] = deployment
                if deployment["status"] == "success":
                    results["success_count"] += 1
                    self.daily_post_counts[today_str()][platform] += 1

            except Exception as e:
                error_msg = f"{platform}: {str(e)}"
                results["errors"].append(error_msg)

        return results

    def _deploy_conversation(self, conversation: Dict, platform: str) -> Dict[str, Any]:
        """Deploy conversation to specific platform (simulation for now)."""

        # In real implementation, this would use platform APIs
        # For now, we simulate deployment and log the content

        deployment = {
            "status": "success",
            "platform": platform,
            "content": conversation["content"],
            "category": conversation["category"],
            "engagement_potential": conversation["engagement_potential"],
            "deployment_time": datetime.now().isoformat(),
            "simulation": True  # Remove when real APIs are integrated
        }

        # Add platform-specific metadata
        platform_rules = PLATFORM_ENGAGEMENT_RULES.get(platform, {})
        deployment["engagement_style"] = platform_rules.get("engagement_style")
        deployment["follow_up_strategy"] = platform_rules.get("follow_up_strategy")

        return deployment

    def _get_last_post_time(self, platform: str) -> Optional[datetime]:
        """Get timestamp of last post to platform."""

        today = today_str()
        if today not in self.triggers_log:
            return None

        last_time = None
        for entry in self.triggers_log[today]:
            deployments = entry.get("deployments", {})
            if platform in deployments:
                platform_deploy = deployments[platform]
                if platform_deploy.get("status") == "success":
                    try:
                        timestamp = datetime.fromisoformat(platform_deploy["deployment_time"])
                        if not last_time or timestamp > last_time:
                            last_time = timestamp
                    except:
                        continue

        return last_time

    def run_scheduled_engagement(self):
        """Run engagement triggers based on current day/time schedule."""

        now = datetime.now()
        day_name = now.strftime("%A").lower()
        current_time = now.strftime("%H:%M")

        if day_name not in ENGAGEMENT_SCHEDULE:
            return {"status": "no_schedule", "day": day_name}

        day_schedule = ENGAGEMENT_SCHEDULE[day_name]

        # Find closest scheduled time (within 15 minutes)
        for scheduled_time, engagement_config in day_schedule.items():
            scheduled_dt = datetime.strptime(scheduled_time, "%H:%M").time()
            current_dt = now.time()

            # Calculate time difference in minutes
            scheduled_minutes = scheduled_dt.hour * 60 + scheduled_dt.minute
            current_minutes = current_dt.hour * 60 + current_dt.minute
            time_diff = abs(scheduled_minutes - current_minutes)

            if time_diff <= 15:  # Within 15 minutes of scheduled time
                print(f"[TRIGGER] Executing scheduled engagement: {engagement_config}")

                result = self.trigger_engagement(
                    engagement_config["category"],
                    engagement_config["platforms"],
                    engagement_config["priority"]
                )

                # Log the trigger execution
                self._log_trigger_execution(result)

                return result

        return {"status": "no_matching_schedule", "time": current_time, "day": day_name}

    def run_momentum_based_engagement(self) -> Dict[str, Any]:
        """Trigger engagement based on detected topic momentum."""

        # Get trending topics from momentum tracking
        trending_topics = self.engine._get_trending_topics()

        if not trending_topics:
            return {"status": "no_trending_topics"}

        # Select top trending topic
        top_topic = max(trending_topics.items(), key=lambda x: x[1])
        topic_name, mention_count = top_topic

        # Choose appropriate category based on trending topic
        category = self._categorize_trending_topic(topic_name)

        # Select platforms based on topic momentum
        platforms = self._select_platforms_for_topic(topic_name, mention_count)

        print(f"[MOMENTUM] Triggering engagement for trending topic: {topic_name} ({mention_count} mentions)")

        result = self.trigger_engagement(category, platforms, "high")
        result["triggered_by"] = "momentum"
        result["trending_topic"] = {"name": topic_name, "mentions": mention_count}

        self._log_trigger_execution(result)
        return result

    def _categorize_trending_topic(self, topic: str) -> str:
        """Categorize trending topic to select appropriate conversation category."""

        topic_lower = topic.lower()

        # Industry/tech topics
        if any(word in topic_lower for word in ["streaming", "ai", "nft", "web3", "industry"]):
            return "industry_insights"

        # Cultural moments
        elif any(word in topic_lower for word in ["beef", "collab", "awards", "viral"]):
            return "cultural_moments"

        # Creative process
        elif any(word in topic_lower for word in ["studio", "beat", "production", "sample"]):
            return "creative_process"

        # Music discovery
        elif any(word in topic_lower for word in ["album", "song", "artist", "track"]):
            return "music_discovery"

        # Default to music opinions for debates/discussions
        else:
            return "music_opinions"

    def _select_platforms_for_topic(self, topic: str, mention_count: int) -> List[str]:
        """Select optimal platforms based on topic characteristics and momentum."""

        # High momentum topics go to more platforms
        if mention_count > 10:
            return ["bluesky", "x", "threads", "instagram"]
        elif mention_count > 5:
            return ["bluesky", "x", "threads"]
        else:
            return ["bluesky", "threads"]

    def _log_trigger_execution(self, result: Dict[str, Any]):
        """Log trigger execution for monitoring and analysis."""

        today = today_str()
        if today not in self.triggers_log:
            self.triggers_log[today] = []

        self.triggers_log[today].append(result)

        # Keep only last 30 days
        cutoff_date = (datetime.now() - timedelta(days=30)).date()
        self.triggers_log = {
            k: v for k, v in self.triggers_log.items()
            if datetime.fromisoformat(k + "T00:00:00").date() >= cutoff_date
        }

        save_json(TRIGGERS_LOG, self.triggers_log)

    def generate_engagement_report(self) -> Dict[str, Any]:
        """Generate comprehensive engagement trigger performance report."""

        recent_data = self._get_recent_trigger_data(days=7)

        report = {
            "period": "7_days",
            "total_triggers": len(recent_data),
            "success_rate": 0.0,
            "platform_performance": defaultdict(lambda: {"attempts": 0, "successes": 0}),
            "category_performance": defaultdict(lambda: {"attempts": 0, "successes": 0}),
            "daily_activity": defaultdict(int),
            "recommendations": []
        }

        successful_triggers = 0

        for trigger in recent_data:
            trigger_date = trigger["timestamp"][:10]
            report["daily_activity"][trigger_date] += 1

            category = trigger.get("category", "unknown")
            deployments = trigger.get("deployments", {})

            for platform, deployment in deployments.items():
                platform_perf = report["platform_performance"][platform]
                category_perf = report["category_performance"][category]

                platform_perf["attempts"] += 1
                category_perf["attempts"] += 1

                if deployment.get("status") == "success":
                    platform_perf["successes"] += 1
                    category_perf["successes"] += 1
                    successful_triggers += 1

        # Calculate success rate
        if report["total_triggers"] > 0:
            report["success_rate"] = successful_triggers / sum(
                len(t.get("deployments", {})) for t in recent_data
            )

        # Generate recommendations
        report["recommendations"] = self._generate_performance_recommendations(report)

        return report

    def _get_recent_trigger_data(self, days: int = 7) -> List[Dict]:
        """Get trigger execution data from recent days."""

        cutoff = datetime.now() - timedelta(days=days)
        recent_triggers = []

        for date_str, triggers in self.triggers_log.items():
            try:
                date_obj = datetime.fromisoformat(date_str + "T00:00:00")
                if date_obj >= cutoff:
                    recent_triggers.extend(triggers)
            except:
                continue

        return recent_triggers

    def _generate_performance_recommendations(self, report: Dict) -> List[str]:
        """Generate actionable recommendations based on performance data."""

        recommendations = []

        # Success rate recommendations
        if report["success_rate"] < 0.7:
            recommendations.append("Review trigger timing and platform selection criteria")

        # Platform performance
        platform_perf = report["platform_performance"]
        worst_platform = min(platform_perf.keys(),
                           key=lambda p: platform_perf[p]["successes"] / max(platform_perf[p]["attempts"], 1))

        if platform_perf[worst_platform]["attempts"] > 0:
            success_rate = platform_perf[worst_platform]["successes"] / platform_perf[worst_platform]["attempts"]
            if success_rate < 0.5:
                recommendations.append(f"Investigate {worst_platform} deployment issues - low success rate")

        # Activity level
        avg_daily = sum(report["daily_activity"].values()) / max(len(report["daily_activity"]), 1)
        if avg_daily < 2:
            recommendations.append("Increase trigger frequency - currently below optimal engagement levels")
        elif avg_daily > 8:
            recommendations.append("Consider reducing trigger frequency to avoid audience fatigue")

        return recommendations


def run_engagement_automation():
    """Main automation function - run this periodically."""

    print("\n[*] APU-50 Engagement Trigger Automation Starting...")

    trigger_system = EngagementTriggerSystem()

    # Run scheduled engagement
    scheduled_result = trigger_system.run_scheduled_engagement()
    print(f"[SCHEDULED] {scheduled_result}")

    # Run momentum-based engagement (less frequently)
    if random.random() > 0.7:  # 30% chance
        momentum_result = trigger_system.run_momentum_based_engagement()
        print(f"[MOMENTUM] {momentum_result}")

    # Generate performance report
    report = trigger_system.generate_engagement_report()
    print(f"[REPORT] Success rate: {report['success_rate']:.1%}, Total triggers: {report['total_triggers']}")

    # Log overall status
    status = "ok" if report["success_rate"] > 0.7 else "warning" if report["success_rate"] > 0.4 else "error"
    detail = f"Success rate: {report['success_rate']:.1%}, Triggers: {report['total_triggers']}"
    log_run("EngagementTriggersAPU50", status, detail)

    return {
        "scheduled": scheduled_result,
        "momentum": momentum_result if 'momentum_result' in locals() else None,
        "performance": report
    }


if __name__ == "__main__":
    result = run_engagement_automation()

    # Exit codes based on performance
    performance = result.get("performance", {})
    success_rate = performance.get("success_rate", 0.0)

    if success_rate < 0.4:
        print(f"\n[ERROR] Engagement trigger success rate critically low: {success_rate:.1%}")
        sys.exit(2)
    elif success_rate < 0.7:
        print(f"\n[WARNING] Engagement trigger success rate below target: {success_rate:.1%}")
        sys.exit(1)
    else:
        print(f"\n[OK] Engagement triggers performing well: {success_rate:.1%}")
        sys.exit(0)