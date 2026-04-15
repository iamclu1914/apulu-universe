"""
apu50_community_conversation_engine.py — APU-50 Community Conversation Engine

Proactive community engagement system that generates meaningful conversations and builds topic momentum.
Addresses core gaps identified in APU-49 monitoring: 0% engagement quality, 0% conversation health.

Created by: Dex - Community Agent (APU-50)

Key Features:
- Proactive conversation starters and engaging questions
- Topic momentum tracking and trending topic amplification
- Cross-platform engagement coordination
- Community challenge and poll generation
- Integration with APU-49 department monitoring

Architecture:
┌─────────────────────────────────────────────────────────────────┐
│                 APU-50 Community Conversation Engine            │
├─────────────────────────────────────────────────────────────────┤
│ [Conversation Starter] → [Topic Tracker] → [Platform Coordinator] │
│         ↓                      ↓                     ↓            │
│ [Engagement Templates] → [Momentum Engine] → [Cross-Platform API] │
│         ↓                      ↓                     ↓            │
│ [Community Analytics] ← [APU-49 Integration] ← [Quality Metrics]  │
└─────────────────────────────────────────────────────────────────┘
"""

import json
import sys
import random
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import (
    load_json, save_json, VAWN_DIR, log_run, today_str,
    get_anthropic_client, VAWN_PROFILE
)

# Configuration
CONVERSATION_ENGINE_LOG = VAWN_DIR / "research" / "apu50_conversation_engine_log.json"
TOPIC_MOMENTUM_LOG = VAWN_DIR / "research" / "apu50_topic_momentum_log.json"
CONVERSATION_TEMPLATES_DIR = VAWN_DIR / "src" / "conversation_templates"
CONVERSATION_TEMPLATES_DIR.mkdir(exist_ok=True)

# Community Conversation Categories
CONVERSATION_TYPES = {
    "music_discovery": {
        "description": "Posts about discovering new music and artists",
        "engagement_potential": 0.8,
        "platforms": ["bluesky", "instagram", "tiktok"],
        "frequency": "daily"
    },
    "creative_process": {
        "description": "Behind-the-scenes content about music creation",
        "engagement_potential": 0.9,
        "platforms": ["bluesky", "instagram", "threads"],
        "frequency": "3x_weekly"
    },
    "community_challenges": {
        "description": "Interactive challenges and contests",
        "engagement_potential": 0.95,
        "platforms": ["tiktok", "instagram", "bluesky"],
        "frequency": "weekly"
    },
    "music_opinions": {
        "description": "Thought-provoking questions about hip-hop and music",
        "engagement_potential": 0.85,
        "platforms": ["bluesky", "threads", "x"],
        "frequency": "daily"
    },
    "industry_insights": {
        "description": "Commentary on music industry trends",
        "engagement_potential": 0.7,
        "platforms": ["bluesky", "threads"],
        "frequency": "2x_weekly"
    }
}

# Conversation Templates
CONVERSATION_TEMPLATES = {
    "music_discovery": [
        "What's the last track that made you stop everything and just listen?",
        "Drop the most underrated artist you discovered this year 👇",
        "Name a song that hit different when you heard it for the first time",
        "What's your go-to deep cut that you play for people who 'get it'?",
        "Share a track that changed how you think about {genre}",
        "What's the most slept-on album from {current_year}?",
        "Drop a song that sounds like {current_season} to you"
    ],
    "creative_process": [
        "Studio question: Do you write to the beat or create the beat to the words?",
        "What's your creative process when you're feeling blocked?",
        "Collaborations vs solo work - which brings out your best ideas?",
        "How do you know when a track is actually finished?",
        "What's the weirdest place you've gotten a melody or lyric idea?",
        "Do you prefer writing in silence or with background music?",
        "What's one production technique that completely changed your sound?"
    ],
    "community_challenges": [
        "16 Bar Challenge: Drop your hardest 16 bars in the comments",
        "Remix Challenge: Take this hook and flip it your way",
        "Beat Battle: Make a beat using only sounds from your environment",
        "Lyric Cipher: Continue this story in 8 bars",
        "Producer Challenge: Create a beat in under 10 minutes",
        "Flow Challenge: Rap over this drum pattern",
        "Freestyle Friday: Drop a 4-bar freestyle about your week"
    ],
    "music_opinions": [
        "Hot take: The best hip-hop albums are under 40 minutes long. Agree?",
        "What makes a beat timeless vs just trendy?",
        "Is technical skill or emotional connection more important in rap?",
        "Which era had the best production: 90s boom bap or 2010s trap?",
        "Do features make albums better or take away from the artist's vision?",
        "Should artists stick to their lane or experiment across genres?",
        "What's the most overrated thing in hip-hop right now?"
    ],
    "industry_insights": [
        "The streaming game has changed everything. Good or bad for artists?",
        "Social media presence vs musical talent - what matters more today?",
        "Independent vs label - what's the better path for new artists?",
        "How has TikTok changed how we discover and consume music?",
        "What skills do artists need now that weren't important 10 years ago?",
        "Are music videos still important in the TikTok era?",
        "What's the future of live performances and touring?"
    ]
}

# Topic momentum tracking keywords
MOMENTUM_KEYWORDS = {
    "hip_hop_trends": [
        "trap", "drill", "boom bap", "conscious rap", "melodic rap",
        "atlanta", "nyc", "chicago", "la", "memphis", "detroit"
    ],
    "music_technology": [
        "ai music", "stem player", "nft music", "web3", "blockchain",
        "streaming", "tiktok music", "reels music"
    ],
    "industry_events": [
        "grammy", "bet awards", "rolling loud", "coachella", "sxsw",
        "album drop", "mixtape", "ep release"
    ],
    "cultural_moments": [
        "cypher", "beef", "collaboration", "remix", "sample",
        "viral moment", "trending sound"
    ]
}

# Cross-platform engagement strategies
PLATFORM_STRATEGIES = {
    "bluesky": {
        "optimal_length": 280,
        "hashtag_limit": 3,
        "engagement_style": "conversational",
        "best_times": ["12:00", "18:00", "21:00"],
        "content_types": ["text", "links", "threads"]
    },
    "instagram": {
        "optimal_length": 125,  # First line before "more"
        "hashtag_limit": 10,
        "engagement_style": "visual_first",
        "best_times": ["11:00", "14:00", "17:00"],
        "content_types": ["posts", "stories", "reels"]
    },
    "tiktok": {
        "optimal_length": 100,
        "hashtag_limit": 5,
        "engagement_style": "trend_based",
        "best_times": ["06:00", "10:00", "19:00"],
        "content_types": ["videos", "duets", "stitches"]
    },
    "threads": {
        "optimal_length": 500,
        "hashtag_limit": 2,
        "engagement_style": "discussion_based",
        "best_times": ["09:00", "13:00", "20:00"],
        "content_types": ["text", "threads", "replies"]
    },
    "x": {
        "optimal_length": 240,
        "hashtag_limit": 2,
        "engagement_style": "quick_wit",
        "best_times": ["08:00", "12:00", "17:00"],
        "content_types": ["tweets", "threads", "spaces"]
    }
}


class CommunityConversationEngine:
    """Main engine for generating and tracking community conversations."""

    def __init__(self):
        self.anthropic_client = get_anthropic_client()
        self.conversation_log = load_json(CONVERSATION_ENGINE_LOG) if Path(CONVERSATION_ENGINE_LOG).exists() else {}
        self.momentum_log = load_json(TOPIC_MOMENTUM_LOG) if Path(TOPIC_MOMENTUM_LOG).exists() else {}

    def generate_conversation_starter(self, category: str, platform: str = "bluesky") -> Dict[str, Any]:
        """Generate an engaging conversation starter for a specific category and platform."""

        if category not in CONVERSATION_TYPES:
            raise ValueError(f"Unknown category: {category}")

        platform_config = PLATFORM_STRATEGIES.get(platform, PLATFORM_STRATEGIES["bluesky"])
        conversation_type = CONVERSATION_TYPES[category]
        templates = CONVERSATION_TEMPLATES.get(category, [])

        if not templates:
            return {"error": "No templates available for category"}

        # Select template and customize
        base_template = random.choice(templates)

        # Context-aware customization
        current_season = self._get_current_season()
        current_year = datetime.now().year
        trending_topics = self._get_trending_topics()

        # Replace placeholders
        customized_prompt = base_template.replace("{current_season}", current_season)
        customized_prompt = customized_prompt.replace("{current_year}", str(current_year))

        if "{genre}" in customized_prompt and trending_topics:
            genre = random.choice(list(trending_topics.keys()))
            customized_prompt = customized_prompt.replace("{genre}", genre)

        # Generate platform-optimized version
        optimized_content = self._optimize_for_platform(customized_prompt, platform_config)

        return {
            "category": category,
            "platform": platform,
            "content": optimized_content,
            "engagement_potential": conversation_type["engagement_potential"],
            "timestamp": datetime.now().isoformat(),
            "template_used": base_template,
            "trending_context": trending_topics
        }

    def track_topic_momentum(self, topics: List[str]) -> Dict[str, Any]:
        """Track and analyze momentum for specific topics."""

        today = today_str()
        if today not in self.momentum_log:
            self.momentum_log[today] = {"topics": {}, "trend_score": 0.0}

        topic_data = self.momentum_log[today]["topics"]

        for topic in topics:
            if topic not in topic_data:
                topic_data[topic] = {
                    "mentions": 0,
                    "engagement_score": 0.0,
                    "first_seen": datetime.now().isoformat(),
                    "platforms": set()
                }

            topic_data[topic]["mentions"] += 1
            topic_data[topic]["last_seen"] = datetime.now().isoformat()

        # Calculate overall trend score
        self.momentum_log[today]["trend_score"] = self._calculate_trend_score(topic_data)

        return {
            "date": today,
            "tracked_topics": len(topic_data),
            "trending_topics": self._get_top_trending_topics(topic_data, limit=5),
            "trend_score": self.momentum_log[today]["trend_score"]
        }

    def coordinate_cross_platform_engagement(self, content: str, platforms: List[str]) -> Dict[str, Any]:
        """Coordinate engagement strategy across multiple platforms."""

        coordination_plan = {
            "primary_content": content,
            "platform_adaptations": {},
            "timing_strategy": {},
            "engagement_sequence": []
        }

        for platform in platforms:
            if platform not in PLATFORM_STRATEGIES:
                continue

            platform_config = PLATFORM_STRATEGIES[platform]

            # Adapt content for platform
            adapted_content = self._optimize_for_platform(content, platform_config)
            coordination_plan["platform_adaptations"][platform] = adapted_content

            # Determine optimal timing
            best_times = platform_config["best_times"]
            coordination_plan["timing_strategy"][platform] = {
                "optimal_times": best_times,
                "recommended_time": random.choice(best_times),
                "content_type": random.choice(platform_config["content_types"])
            }

        # Create engagement sequence
        coordination_plan["engagement_sequence"] = self._create_engagement_sequence(platforms)

        return coordination_plan

    def analyze_conversation_quality(self) -> Dict[str, Any]:
        """Analyze the quality of generated conversations and their impact."""

        recent_conversations = self._get_recent_conversations(days=7)

        quality_metrics = {
            "total_conversations_generated": len(recent_conversations),
            "average_engagement_potential": 0.0,
            "category_distribution": Counter(),
            "platform_distribution": Counter(),
            "trending_topic_coverage": 0.0,
            "conversation_quality_score": 0.0
        }

        if not recent_conversations:
            return quality_metrics

        # Calculate metrics
        engagement_potentials = [conv.get("engagement_potential", 0) for conv in recent_conversations]
        quality_metrics["average_engagement_potential"] = sum(engagement_potentials) / len(engagement_potentials)

        for conv in recent_conversations:
            quality_metrics["category_distribution"][conv.get("category", "unknown")] += 1
            quality_metrics["platform_distribution"][conv.get("platform", "unknown")] += 1

        # Calculate trending topic coverage
        trending_topics = self._get_trending_topics()
        conversations_with_trends = sum(1 for conv in recent_conversations if conv.get("trending_context"))
        quality_metrics["trending_topic_coverage"] = conversations_with_trends / len(recent_conversations)

        # Overall quality score
        quality_metrics["conversation_quality_score"] = self._calculate_conversation_quality_score(quality_metrics)

        return quality_metrics

    def generate_community_challenge(self) -> Dict[str, Any]:
        """Generate a community challenge to boost engagement."""

        challenge_types = [
            "remix_challenge",
            "lyric_challenge",
            "beat_challenge",
            "freestyle_challenge",
            "producer_challenge"
        ]

        challenge_type = random.choice(challenge_types)
        challenge_templates = CONVERSATION_TEMPLATES.get("community_challenges", [])

        if not challenge_templates:
            return {"error": "No challenge templates available"}

        challenge_prompt = random.choice([t for t in challenge_templates if challenge_type.split('_')[0] in t.lower()])

        # Generate challenge details
        challenge = {
            "type": challenge_type,
            "prompt": challenge_prompt,
            "duration_days": random.choice([3, 7, 14]),
            "platforms": ["tiktok", "instagram", "bluesky"],
            "engagement_hooks": [
                "Tag 3 friends who need to see this",
                "Best submission gets a feature",
                "Use #VawnChallenge to participate",
                "Drop your submission in the comments"
            ],
            "success_metrics": {
                "target_participants": random.choice([50, 100, 200]),
                "target_submissions": random.choice([20, 40, 80]),
                "target_engagement_rate": random.choice([0.05, 0.08, 0.12])
            }
        }

        return challenge

    # Helper methods
    def _get_current_season(self) -> str:
        """Get current season for contextual content."""
        month = datetime.now().month
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:
            return "fall"

    def _get_trending_topics(self) -> Dict[str, int]:
        """Get currently trending topics from momentum tracking."""
        recent_topics = {}

        # Look at last 3 days of momentum data
        for i in range(3):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            if date in self.momentum_log:
                topics = self.momentum_log[date].get("topics", {})
                for topic, data in topics.items():
                    recent_topics[topic] = recent_topics.get(topic, 0) + data.get("mentions", 0)

        return recent_topics

    def _optimize_for_platform(self, content: str, platform_config: Dict) -> str:
        """Optimize content for specific platform requirements."""

        # Length optimization
        max_length = platform_config["optimal_length"]
        if len(content) > max_length:
            # Intelligently truncate while preserving meaning
            sentences = content.split('. ')
            optimized = sentences[0]
            for sentence in sentences[1:]:
                if len(optimized + '. ' + sentence) <= max_length:
                    optimized += '. ' + sentence
                else:
                    break
            content = optimized

        # Style optimization based on platform
        style = platform_config["engagement_style"]
        if style == "quick_wit":
            content = content.replace("?", "? 🤔")
        elif style == "visual_first":
            content += " 📸"
        elif style == "trend_based":
            content += " ✨"

        return content

    def _calculate_trend_score(self, topic_data: Dict) -> float:
        """Calculate overall trend score for the day."""
        if not topic_data:
            return 0.0

        total_mentions = sum(data.get("mentions", 0) for data in topic_data.values())
        unique_topics = len(topic_data)

        # Score based on volume and diversity
        volume_score = min(total_mentions / 20, 1.0)  # Normalize to max 20 mentions
        diversity_score = min(unique_topics / 10, 1.0)  # Normalize to max 10 topics

        return (volume_score * 0.6 + diversity_score * 0.4)

    def _get_top_trending_topics(self, topic_data: Dict, limit: int = 5) -> List[Dict]:
        """Get top trending topics sorted by mentions."""
        topics = [(topic, data.get("mentions", 0)) for topic, data in topic_data.items()]
        topics.sort(key=lambda x: x[1], reverse=True)

        return [{"topic": topic, "mentions": mentions} for topic, mentions in topics[:limit]]

    def _create_engagement_sequence(self, platforms: List[str]) -> List[Dict]:
        """Create a sequence for rolling out content across platforms."""
        sequence = []

        # Primary platform (usually the one with best engagement)
        primary = platforms[0] if platforms else "bluesky"
        sequence.append({
            "order": 1,
            "platform": primary,
            "action": "initial_post",
            "timing": "immediate"
        })

        # Secondary platforms with staggered timing
        for i, platform in enumerate(platforms[1:], 2):
            sequence.append({
                "order": i,
                "platform": platform,
                "action": "cross_post",
                "timing": f"{i * 15} minutes later"
            })

        return sequence

    def _get_recent_conversations(self, days: int = 7) -> List[Dict]:
        """Get conversations generated in the last N days."""
        cutoff = datetime.now() - timedelta(days=days)
        recent = []

        for date_str, conversations in self.conversation_log.items():
            try:
                conv_date = datetime.fromisoformat(date_str)
                if conv_date >= cutoff:
                    if isinstance(conversations, list):
                        recent.extend(conversations)
                    else:
                        recent.append(conversations)
            except ValueError:
                continue

        return recent

    def _calculate_conversation_quality_score(self, metrics: Dict) -> float:
        """Calculate overall conversation quality score."""

        engagement_score = metrics.get("average_engagement_potential", 0.0)
        trend_coverage = metrics.get("trending_topic_coverage", 0.0)
        volume_score = min(metrics.get("total_conversations_generated", 0) / 10, 1.0)

        # Weighted average
        quality_score = (engagement_score * 0.4 + trend_coverage * 0.3 + volume_score * 0.3)

        return quality_score

    def save_logs(self):
        """Save conversation and momentum logs."""
        save_json(CONVERSATION_ENGINE_LOG, self.conversation_log)
        save_json(TOPIC_MOMENTUM_LOG, self.momentum_log)


def generate_daily_conversation_plan() -> Dict[str, Any]:
    """Generate a daily plan for community conversations across platforms."""

    engine = CommunityConversationEngine()

    # Morning conversation (music discovery)
    morning_conv = engine.generate_conversation_starter("music_discovery", "bluesky")

    # Afternoon conversation (creative process or music opinions)
    afternoon_category = random.choice(["creative_process", "music_opinions"])
    afternoon_conv = engine.generate_conversation_starter(afternoon_category, "instagram")

    # Evening conversation (community challenge or industry insights)
    evening_category = random.choice(["community_challenges", "industry_insights"])
    evening_conv = engine.generate_conversation_starter(evening_category, "tiktok")

    daily_plan = {
        "date": today_str(),
        "conversations": {
            "morning": morning_conv,
            "afternoon": afternoon_conv,
            "evening": evening_conv
        },
        "cross_platform_strategy": engine.coordinate_cross_platform_engagement(
            morning_conv["content"],
            ["bluesky", "threads"]
        ),
        "weekly_challenge": engine.generate_community_challenge(),
        "quality_analysis": engine.analyze_conversation_quality()
    }

    # Log the plan
    today = today_str()
    if today not in engine.conversation_log:
        engine.conversation_log[today] = []

    engine.conversation_log[today].append(daily_plan)
    engine.save_logs()

    return daily_plan


def main():
    """APU-50 Community Conversation Engine main function."""
    print("\n[*] Vawn Community Conversation Engine - APU-50 Starting...")
    print("[*] Generating proactive community engagement content...")

    try:
        # Generate daily conversation plan
        daily_plan = generate_daily_conversation_plan()

        print(f"\n[DAILY PLAN] {daily_plan['date']}")
        print("=" * 60)

        for time_slot, conversation in daily_plan["conversations"].items():
            print(f"\n[{time_slot.upper()}] {conversation['platform'].title()} - {conversation['category']}")
            print(f"Content: {conversation['content']}")
            print(f"Engagement Potential: {conversation['engagement_potential']:.1%}")

        # Weekly challenge
        challenge = daily_plan["weekly_challenge"]
        print(f"\n[WEEKLY CHALLENGE] {challenge['type'].replace('_', ' ').title()}")
        print(f"Prompt: {challenge['prompt']}")
        print(f"Platforms: {', '.join(challenge['platforms'])}")

        # Quality metrics
        quality = daily_plan["quality_analysis"]
        print(f"\n[QUALITY METRICS]")
        print(f"Recent Conversations: {quality['total_conversations_generated']}")
        print(f"Avg Engagement Potential: {quality['average_engagement_potential']:.1%}")
        print(f"Trending Topic Coverage: {quality['trending_topic_coverage']:.1%}")
        print(f"Quality Score: {quality['conversation_quality_score']:.1%}")

        # Cross-platform coordination
        cross_platform = daily_plan["cross_platform_strategy"]
        print(f"\n[CROSS-PLATFORM] {len(cross_platform['platform_adaptations'])} platform adaptations")
        for platform, timing in cross_platform["timing_strategy"].items():
            print(f"  {platform}: {timing['recommended_time']} ({timing['content_type']})")

        # Log success
        quality_score = quality["conversation_quality_score"]
        total_conversations = quality["total_conversations_generated"]
        status = "ok" if quality_score > 0.6 else "warning" if quality_score > 0.3 else "error"
        detail = f"Quality: {quality_score:.1%}, Conversations: {total_conversations}, Challenges: 1"

        log_run("CommunityConversationEngineAPU50", status, detail)

        print(f"\n[APU-50] Community conversation generation complete - Quality Score: {quality_score:.1%}")

        return daily_plan

    except Exception as e:
        error_msg = f"Error in conversation engine: {e}"
        log_run("CommunityConversationEngineAPU50", "error", error_msg)
        print(f"[ERROR] {error_msg}")
        return {"error": error_msg}


if __name__ == "__main__":
    result = main()

    # Exit based on conversation quality
    if "error" in result:
        sys.exit(2)
    elif result.get("quality_analysis", {}).get("conversation_quality_score", 0) < 0.3:
        print("\n[WARNING] Conversation quality below threshold")
        sys.exit(1)
    else:
        print("\n[OK] Community conversations generated successfully")
        sys.exit(0)