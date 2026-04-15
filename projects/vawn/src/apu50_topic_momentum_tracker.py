"""
apu50_topic_momentum_tracker.py — APU-50 Topic Momentum Tracking & Amplification

Advanced topic momentum tracking system that identifies emerging trends in hip-hop culture
and strategically amplifies relevant topics to build community engagement momentum.

Created by: Dex - Community Agent (APU-50)

Features:
- Real-time topic momentum detection
- Strategic topic amplification campaigns
- Cross-platform trend coordination
- Cultural moment identification
- Topic lifecycle tracking
- Viral potential analysis
"""

import json
import sys
import re
import math
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import requests
from textblob import TextBlob

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
sys.path.insert(0, r"C:\Users\rdyal\Vawn\src")

from vawn_config import (
    load_json, save_json, VAWN_DIR, log_run, today_str,
    get_anthropic_client, VAWN_PROFILE
)

# Configuration
MOMENTUM_TRACKER_LOG = VAWN_DIR / "research" / "apu50_momentum_tracker_log.json"
TOPIC_AMPLIFICATION_LOG = VAWN_DIR / "research" / "apu50_topic_amplification_log.json"
VIRAL_POTENTIAL_LOG = VAWN_DIR / "research" / "apu50_viral_potential_log.json"

# Hip-hop and music culture keywords for momentum tracking
HIP_HOP_KEYWORDS = {
    "genres": [
        "trap", "drill", "boom bap", "conscious rap", "melodic rap", "mumble rap",
        "old school", "underground", "mainstream", "conscious", "gangsta rap",
        "alternative hip hop", "experimental", "cloud rap", "jazz rap", "abstract"
    ],
    "regional": [
        "atlanta", "nyc", "chicago", "la", "memphis", "detroit", "houston",
        "miami", "new orleans", "bay area", "dmv", "philly", "brooklyn",
        "queens", "south side", "west coast", "east coast", "down south"
    ],
    "industry": [
        "major label", "independent", "streaming", "spotify", "apple music",
        "soundcloud", "bandcamp", "tidal", "youtube music", "playlist",
        "algorithm", "royalties", "publishing", "distribution", "A&R"
    ],
    "cultural": [
        "cypher", "freestyle", "battle rap", "collaboration", "remix", "sample",
        "interpolation", "producer tag", "studio session", "mixtape", "ep",
        "album rollout", "music video", "behind the scenes", "documentary"
    ],
    "technology": [
        "auto-tune", "vocoder", "808", "hi-hats", "snare", "kick", "bass",
        "analog", "digital", "daw", "pro tools", "logic", "ableton", "fl studio",
        "plugins", "vst", "midi", "stems", "multitrack", "mixing", "mastering"
    ]
}

# Topic momentum calculation factors
MOMENTUM_FACTORS = {
    "velocity": 0.25,      # Rate of mention increase
    "volume": 0.20,        # Total mention count
    "diversity": 0.15,     # Platform distribution
    "sentiment": 0.15,     # Overall sentiment
    "engagement": 0.15,    # Likes, shares, comments
    "recency": 0.10        # How recent the mentions are
}

# Viral potential indicators
VIRAL_INDICATORS = {
    "controversy": ["beef", "diss", "response", "clap back", "shots fired"],
    "celebration": ["birthday", "anniversary", "milestone", "achievement", "award"],
    "collaboration": ["featuring", "collab", "remix", "sample", "interpolation"],
    "breaking_news": ["breaking", "announced", "confirmed", "revealed", "exclusive"],
    "cultural_moments": ["viral", "trending", "moment", "iconic", "legendary"],
    "community_driven": ["challenge", "cipher", "freestyle", "battle", "competition"]
}

# Platform-specific momentum weights
PLATFORM_WEIGHTS = {
    "bluesky": 1.0,        # Equal weight - good for real conversations
    "x": 1.2,              # Higher weight - trend-setting platform
    "tiktok": 1.5,         # Highest weight - viral content origin
    "instagram": 0.9,      # Slightly lower - more visual focused
    "threads": 0.8,        # Lower weight - newer platform
    "youtube": 1.1,        # Good weight - long-form content
    "soundcloud": 1.3      # Higher weight - music-specific
}


class TopicMomentumTracker:
    """Advanced topic momentum tracking and amplification system."""

    def __init__(self):
        self.anthropic_client = get_anthropic_client()
        self.momentum_log = load_json(MOMENTUM_TRACKER_LOG) if Path(MOMENTUM_TRACKER_LOG).exists() else {}
        self.amplification_log = load_json(TOPIC_AMPLIFICATION_LOG) if Path(TOPIC_AMPLIFICATION_LOG).exists() else {}
        self.viral_potential_log = load_json(VIRAL_POTENTIAL_LOG) if Path(VIRAL_POTENTIAL_LOG).exists() else {}

    def detect_trending_topics(self, content_sources: List[Dict] = None) -> Dict[str, Any]:
        """Detect trending topics from various content sources."""

        # In real implementation, this would pull from platform APIs
        # For now, we'll simulate with sample data and analyze patterns

        trending_analysis = {
            "timestamp": datetime.now().isoformat(),
            "detected_topics": {},
            "momentum_scores": {},
            "viral_potential": {},
            "platform_distribution": {},
            "cultural_significance": {}
        }

        # Simulate trending topic detection (replace with real API calls)
        simulated_trends = self._simulate_trending_topics()

        for topic, mentions in simulated_trends.items():
            # Calculate momentum score
            momentum_score = self._calculate_momentum_score(topic, mentions)
            trending_analysis["momentum_scores"][topic] = momentum_score

            # Analyze viral potential
            viral_score = self._analyze_viral_potential(topic, mentions)
            trending_analysis["viral_potential"][topic] = viral_score

            # Analyze platform distribution
            platform_dist = self._analyze_platform_distribution(topic, mentions)
            trending_analysis["platform_distribution"][topic] = platform_dist

            # Assess cultural significance
            cultural_score = self._assess_cultural_significance(topic)
            trending_analysis["cultural_significance"][topic] = cultural_score

            trending_analysis["detected_topics"][topic] = {
                "mention_count": len(mentions),
                "momentum_score": momentum_score,
                "viral_potential": viral_score,
                "cultural_significance": cultural_score,
                "platforms": list(platform_dist.keys()),
                "first_detected": min(m.get("timestamp", datetime.now().isoformat()) for m in mentions),
                "latest_activity": max(m.get("timestamp", datetime.now().isoformat()) for m in mentions)
            }

        return trending_analysis

    def amplify_strategic_topics(self, topics: Dict[str, Any], amplification_strategy: str = "balanced") -> Dict[str, Any]:
        """Strategically amplify selected topics based on Vawn's brand and goals."""

        amplification_plan = {
            "timestamp": datetime.now().isoformat(),
            "strategy": amplification_strategy,
            "selected_topics": {},
            "amplification_actions": [],
            "expected_impact": {},
            "coordination_sequence": []
        }

        # Select topics for amplification based on strategy
        selected_topics = self._select_topics_for_amplification(topics, amplification_strategy)

        for topic, topic_data in selected_topics.items():
            amplification_tactics = self._design_amplification_tactics(topic, topic_data)

            amplification_plan["selected_topics"][topic] = {
                "reason_for_selection": amplification_tactics["selection_reason"],
                "amplification_potential": amplification_tactics["amplification_potential"],
                "brand_alignment": amplification_tactics["brand_alignment"],
                "tactics": amplification_tactics["tactics"]
            }

            amplification_plan["amplification_actions"].extend(amplification_tactics["actions"])

            # Calculate expected impact
            expected_impact = self._calculate_expected_impact(topic, amplification_tactics)
            amplification_plan["expected_impact"][topic] = expected_impact

        # Create coordination sequence across platforms
        amplification_plan["coordination_sequence"] = self._create_amplification_sequence(
            selected_topics, amplification_strategy
        )

        return amplification_plan

    def track_amplification_results(self, amplification_plan: Dict) -> Dict[str, Any]:
        """Track the results of topic amplification efforts."""

        results = {
            "timestamp": datetime.now().isoformat(),
            "plan_reference": amplification_plan.get("timestamp"),
            "topic_performance": {},
            "overall_effectiveness": 0.0,
            "lessons_learned": [],
            "optimization_suggestions": []
        }

        for topic in amplification_plan.get("selected_topics", {}):
            performance = self._measure_topic_performance(topic, amplification_plan["timestamp"])
            results["topic_performance"][topic] = performance

        # Calculate overall effectiveness
        if results["topic_performance"]:
            effectiveness_scores = [perf.get("effectiveness_score", 0) for perf in results["topic_performance"].values()]
            results["overall_effectiveness"] = sum(effectiveness_scores) / len(effectiveness_scores)

        # Generate lessons learned
        results["lessons_learned"] = self._extract_lessons_learned(results["topic_performance"])

        # Generate optimization suggestions
        results["optimization_suggestions"] = self._generate_optimization_suggestions(results)

        return results

    def identify_cultural_moments(self) -> Dict[str, Any]:
        """Identify significant cultural moments in hip-hop that warrant attention."""

        cultural_analysis = {
            "timestamp": datetime.now().isoformat(),
            "identified_moments": {},
            "significance_scores": {},
            "response_opportunities": {},
            "timing_recommendations": {}
        }

        # Look for cultural moment indicators
        trending_data = self.detect_trending_topics()

        for topic, data in trending_data["detected_topics"].items():
            cultural_indicators = self._identify_cultural_indicators(topic, data)

            if cultural_indicators["is_cultural_moment"]:
                cultural_analysis["identified_moments"][topic] = cultural_indicators

                # Calculate significance score
                significance = self._calculate_cultural_significance(topic, cultural_indicators)
                cultural_analysis["significance_scores"][topic] = significance

                # Identify response opportunities
                opportunities = self._identify_response_opportunities(topic, cultural_indicators)
                cultural_analysis["response_opportunities"][topic] = opportunities

                # Recommend timing for response
                timing = self._recommend_response_timing(topic, cultural_indicators)
                cultural_analysis["timing_recommendations"][topic] = timing

        return cultural_analysis

    # Helper methods for momentum calculation
    def _simulate_trending_topics(self) -> Dict[str, List[Dict]]:
        """Simulate trending topics data (replace with real API integration)."""

        # This simulates what would come from platform APIs
        simulated_data = {
            "atlanta hip hop": [
                {"platform": "tiktok", "mentions": 15, "sentiment": 0.8, "timestamp": datetime.now().isoformat()},
                {"platform": "instagram", "mentions": 8, "sentiment": 0.7, "timestamp": datetime.now().isoformat()},
                {"platform": "bluesky", "mentions": 12, "sentiment": 0.9, "timestamp": datetime.now().isoformat()}
            ],
            "boom bap revival": [
                {"platform": "x", "mentions": 25, "sentiment": 0.6, "timestamp": datetime.now().isoformat()},
                {"platform": "youtube", "mentions": 18, "sentiment": 0.8, "timestamp": datetime.now().isoformat()},
                {"platform": "soundcloud", "mentions": 22, "sentiment": 0.9, "timestamp": datetime.now().isoformat()}
            ],
            "freestyle friday": [
                {"platform": "tiktok", "mentions": 35, "sentiment": 0.9, "timestamp": datetime.now().isoformat()},
                {"platform": "instagram", "mentions": 20, "sentiment": 0.8, "timestamp": datetime.now().isoformat()},
                {"platform": "bluesky", "mentions": 15, "sentiment": 0.9, "timestamp": datetime.now().isoformat()}
            ]
        }

        return simulated_data

    def _calculate_momentum_score(self, topic: str, mentions: List[Dict]) -> float:
        """Calculate momentum score based on multiple factors."""

        if not mentions:
            return 0.0

        # Velocity - rate of increase
        velocity_score = self._calculate_velocity_score(mentions)

        # Volume - total mentions with platform weights
        volume_score = self._calculate_volume_score(mentions)

        # Diversity - platform distribution
        diversity_score = self._calculate_diversity_score(mentions)

        # Sentiment - overall sentiment
        sentiment_score = self._calculate_sentiment_score(mentions)

        # Engagement - simulated engagement metrics
        engagement_score = self._calculate_engagement_score(mentions)

        # Recency - how recent the activity is
        recency_score = self._calculate_recency_score(mentions)

        # Weighted sum
        momentum_score = (
            velocity_score * MOMENTUM_FACTORS["velocity"] +
            volume_score * MOMENTUM_FACTORS["volume"] +
            diversity_score * MOMENTUM_FACTORS["diversity"] +
            sentiment_score * MOMENTUM_FACTORS["sentiment"] +
            engagement_score * MOMENTUM_FACTORS["engagement"] +
            recency_score * MOMENTUM_FACTORS["recency"]
        )

        return min(momentum_score, 1.0)  # Cap at 1.0

    def _calculate_velocity_score(self, mentions: List[Dict]) -> float:
        """Calculate velocity score based on mention rate increase."""
        # Simplified velocity calculation
        if len(mentions) < 2:
            return 0.5

        # Sort by timestamp
        sorted_mentions = sorted(mentions, key=lambda x: x.get("timestamp", ""))

        # Calculate rate of increase (simplified)
        early_count = len(sorted_mentions[:len(sorted_mentions)//2])
        late_count = len(sorted_mentions[len(sorted_mentions)//2:])

        if early_count == 0:
            return 1.0

        velocity = late_count / early_count
        return min(velocity / 2, 1.0)  # Normalize

    def _calculate_volume_score(self, mentions: List[Dict]) -> float:
        """Calculate volume score with platform weights."""
        weighted_volume = 0
        total_weight = 0

        for mention in mentions:
            platform = mention.get("platform", "unknown")
            mention_count = mention.get("mentions", 1)
            weight = PLATFORM_WEIGHTS.get(platform, 1.0)

            weighted_volume += mention_count * weight
            total_weight += weight

        # Normalize based on expected volume (arbitrary threshold of 50 weighted mentions)
        normalized_score = weighted_volume / 50
        return min(normalized_score, 1.0)

    def _calculate_diversity_score(self, mentions: List[Dict]) -> float:
        """Calculate diversity score based on platform distribution."""
        platforms = set(mention.get("platform", "unknown") for mention in mentions)
        max_platforms = len(PLATFORM_WEIGHTS)
        diversity_score = len(platforms) / max_platforms
        return diversity_score

    def _calculate_sentiment_score(self, mentions: List[Dict]) -> float:
        """Calculate average sentiment score."""
        sentiments = [mention.get("sentiment", 0.5) for mention in mentions]
        if not sentiments:
            return 0.5
        return sum(sentiments) / len(sentiments)

    def _calculate_engagement_score(self, mentions: List[Dict]) -> float:
        """Calculate engagement score (simulated)."""
        # In real implementation, this would use actual engagement metrics
        total_mentions = sum(mention.get("mentions", 1) for mention in mentions)

        # Simulate engagement based on platform and volume
        engagement_multiplier = 0.1  # 10% of mentions result in engagement
        estimated_engagement = total_mentions * engagement_multiplier

        # Normalize based on expected engagement (arbitrary threshold)
        normalized_score = estimated_engagement / 20
        return min(normalized_score, 1.0)

    def _calculate_recency_score(self, mentions: List[Dict]) -> float:
        """Calculate recency score based on how recent the activity is."""
        if not mentions:
            return 0.0

        # Get most recent mention
        try:
            most_recent = max(
                datetime.fromisoformat(mention.get("timestamp", datetime.now().isoformat()))
                for mention in mentions
            )
            hours_ago = (datetime.now() - most_recent).total_seconds() / 3600

            # Score decreases with age, full score for last 6 hours
            if hours_ago <= 6:
                return 1.0
            elif hours_ago <= 24:
                return 0.7
            elif hours_ago <= 72:
                return 0.4
            else:
                return 0.1
        except:
            return 0.5  # Default if timestamp parsing fails

    def _analyze_viral_potential(self, topic: str, mentions: List[Dict]) -> float:
        """Analyze the viral potential of a topic."""

        viral_score = 0.0
        topic_lower = topic.lower()

        # Check for viral indicators
        for category, indicators in VIRAL_INDICATORS.items():
            if any(indicator in topic_lower for indicator in indicators):
                if category == "controversy":
                    viral_score += 0.3
                elif category == "collaboration":
                    viral_score += 0.2
                elif category == "breaking_news":
                    viral_score += 0.25
                elif category == "cultural_moments":
                    viral_score += 0.35
                elif category == "community_driven":
                    viral_score += 0.3
                else:
                    viral_score += 0.15

        # Platform factor - TikTok and X are more viral-friendly
        platform_viral_factor = 0
        for mention in mentions:
            platform = mention.get("platform", "")
            if platform == "tiktok":
                platform_viral_factor += 0.3
            elif platform == "x":
                platform_viral_factor += 0.2
            elif platform == "instagram":
                platform_viral_factor += 0.15

        viral_score += min(platform_viral_factor / len(mentions), 0.3)

        return min(viral_score, 1.0)

    def _analyze_platform_distribution(self, topic: str, mentions: List[Dict]) -> Dict[str, int]:
        """Analyze how the topic is distributed across platforms."""

        distribution = defaultdict(int)

        for mention in mentions:
            platform = mention.get("platform", "unknown")
            mention_count = mention.get("mentions", 1)
            distribution[platform] += mention_count

        return dict(distribution)

    def _assess_cultural_significance(self, topic: str) -> float:
        """Assess the cultural significance of a topic in hip-hop."""

        significance_score = 0.0
        topic_lower = topic.lower()

        # Check against hip-hop keyword categories
        for category, keywords in HIP_HOP_KEYWORDS.items():
            matches = sum(1 for keyword in keywords if keyword in topic_lower)
            if matches > 0:
                if category == "cultural":
                    significance_score += 0.4 * min(matches / len(keywords), 1.0)
                elif category == "genres":
                    significance_score += 0.3 * min(matches / len(keywords), 1.0)
                elif category == "regional":
                    significance_score += 0.2 * min(matches / len(keywords), 1.0)
                else:
                    significance_score += 0.1 * min(matches / len(keywords), 1.0)

        return min(significance_score, 1.0)

    def _select_topics_for_amplification(self, topics: Dict, strategy: str) -> Dict[str, Any]:
        """Select topics for amplification based on strategy."""

        topic_scores = {}

        for topic, data in topics.get("detected_topics", {}).items():
            score = 0.0

            if strategy == "aggressive":
                # Prioritize viral potential and momentum
                score = (data.get("viral_potential", 0) * 0.4 +
                        data.get("momentum_score", 0) * 0.4 +
                        data.get("cultural_significance", 0) * 0.2)
            elif strategy == "conservative":
                # Prioritize cultural significance and brand alignment
                score = (data.get("cultural_significance", 0) * 0.5 +
                        data.get("momentum_score", 0) * 0.3 +
                        data.get("viral_potential", 0) * 0.2)
            else:  # balanced
                # Equal weight to all factors
                score = (data.get("momentum_score", 0) * 0.33 +
                        data.get("viral_potential", 0) * 0.33 +
                        data.get("cultural_significance", 0) * 0.33)

            topic_scores[topic] = score

        # Select top 3 topics
        sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)
        selected = dict(sorted_topics[:3])

        return {topic: topics["detected_topics"][topic] for topic in selected.keys()}

    def _design_amplification_tactics(self, topic: str, topic_data: Dict) -> Dict[str, Any]:
        """Design specific amplification tactics for a topic."""

        tactics = {
            "selection_reason": f"Topic momentum: {topic_data.get('momentum_score', 0):.2f}, Viral potential: {topic_data.get('viral_potential', 0):.2f}",
            "amplification_potential": topic_data.get("viral_potential", 0),
            "brand_alignment": self._assess_brand_alignment(topic),
            "tactics": [],
            "actions": []
        }

        # Design tactics based on topic characteristics
        if topic_data.get("viral_potential", 0) > 0.7:
            tactics["tactics"].append("viral_acceleration")
            tactics["actions"].append({
                "type": "create_viral_content",
                "description": f"Create shareable content around {topic}",
                "platforms": ["tiktok", "instagram", "x"],
                "timing": "immediate"
            })

        if topic_data.get("cultural_significance", 0) > 0.6:
            tactics["tactics"].append("cultural_commentary")
            tactics["actions"].append({
                "type": "cultural_commentary",
                "description": f"Provide thoughtful commentary on {topic}",
                "platforms": ["bluesky", "threads"],
                "timing": "within_2_hours"
            })

        if topic_data.get("momentum_score", 0) > 0.8:
            tactics["tactics"].append("momentum_riding")
            tactics["actions"].append({
                "type": "join_conversation",
                "description": f"Join ongoing {topic} conversation with unique perspective",
                "platforms": topic_data.get("platforms", ["bluesky"]),
                "timing": "immediate"
            })

        return tactics

    def _assess_brand_alignment(self, topic: str) -> float:
        """Assess how well a topic aligns with Vawn's brand."""

        topic_lower = topic.lower()
        alignment_score = 0.0

        # Vawn brand keywords (from VAWN_PROFILE)
        vawn_keywords = ["atlanta", "lyrical", "authentic", "storytelling", "hip hop", "rap", "music"]

        matches = sum(1 for keyword in vawn_keywords if keyword in topic_lower)
        alignment_score = matches / len(vawn_keywords)

        return min(alignment_score, 1.0)

    def _calculate_expected_impact(self, topic: str, tactics: Dict) -> Dict[str, Any]:
        """Calculate expected impact of amplification efforts."""

        base_impact = tactics.get("amplification_potential", 0)
        brand_multiplier = tactics.get("brand_alignment", 0.5)

        expected_impact = {
            "engagement_increase": base_impact * brand_multiplier * 0.3,
            "reach_increase": base_impact * 0.4,
            "brand_association_strength": brand_multiplier,
            "viral_probability": base_impact * 0.6,
            "community_building_potential": brand_multiplier * 0.8
        }

        return expected_impact

    def _create_amplification_sequence(self, topics: Dict, strategy: str) -> List[Dict]:
        """Create a coordinated sequence for amplifying multiple topics."""

        sequence = []

        for i, (topic, data) in enumerate(topics.items()):
            sequence.append({
                "order": i + 1,
                "topic": topic,
                "timing": f"{i * 2} hours after start",
                "primary_platform": data.get("platforms", ["bluesky"])[0],
                "action": "initiate_amplification",
                "follow_up_platforms": data.get("platforms", ["bluesky"])[1:3]
            })

        return sequence

    # Additional helper methods for tracking and analysis
    def _measure_topic_performance(self, topic: str, start_time: str) -> Dict[str, Any]:
        """Measure how well a topic performed after amplification."""

        # Simulated performance metrics (replace with real data)
        performance = {
            "topic": topic,
            "measurement_period": "24_hours",
            "engagement_metrics": {
                "likes": random.randint(50, 500),
                "shares": random.randint(10, 100),
                "comments": random.randint(20, 200),
                "mentions": random.randint(30, 300)
            },
            "reach_metrics": {
                "impressions": random.randint(1000, 10000),
                "unique_users": random.randint(500, 5000)
            },
            "effectiveness_score": random.uniform(0.3, 0.9)
        }

        return performance

    def _extract_lessons_learned(self, performance_data: Dict) -> List[str]:
        """Extract lessons learned from amplification performance."""

        lessons = []

        avg_effectiveness = sum(
            perf.get("effectiveness_score", 0)
            for perf in performance_data.values()
        ) / len(performance_data) if performance_data else 0

        if avg_effectiveness > 0.7:
            lessons.append("High-momentum topics with strong brand alignment perform well")
        elif avg_effectiveness < 0.5:
            lessons.append("Need better topic selection or timing optimization")

        lessons.append("Continue monitoring topic lifecycle for optimal entry points")
        lessons.append("Cross-platform coordination improves overall amplification effectiveness")

        return lessons

    def _generate_optimization_suggestions(self, results: Dict) -> List[str]:
        """Generate suggestions for optimizing future amplification efforts."""

        suggestions = []

        effectiveness = results.get("overall_effectiveness", 0)

        if effectiveness < 0.6:
            suggestions.append("Focus on topics with higher cultural significance scores")
            suggestions.append("Improve timing of amplification efforts")

        suggestions.append("Experiment with different content formats for topic amplification")
        suggestions.append("Track competitor amplification strategies for insights")

        return suggestions

    def _identify_cultural_indicators(self, topic: str, data: Dict) -> Dict[str, Any]:
        """Identify indicators that suggest a topic is a cultural moment."""

        indicators = {
            "is_cultural_moment": False,
            "moment_type": None,
            "significance_factors": [],
            "response_urgency": "low"
        }

        topic_lower = topic.lower()
        momentum = data.get("momentum_score", 0)
        viral_potential = data.get("viral_potential", 0)

        # High momentum + viral potential = likely cultural moment
        if momentum > 0.7 and viral_potential > 0.6:
            indicators["is_cultural_moment"] = True
            indicators["response_urgency"] = "high"

        # Check for specific cultural moment indicators
        if any(word in topic_lower for word in ["beef", "diss", "response"]):
            indicators["moment_type"] = "controversy"
            indicators["significance_factors"].append("conflict_drama")

        if any(word in topic_lower for word in ["collab", "featuring", "remix"]):
            indicators["moment_type"] = "collaboration"
            indicators["significance_factors"].append("artist_connection")

        return indicators

    def _calculate_cultural_significance(self, topic: str, indicators: Dict) -> float:
        """Calculate the cultural significance score of a moment."""

        base_score = 0.5

        if indicators["moment_type"] == "controversy":
            base_score += 0.3
        elif indicators["moment_type"] == "collaboration":
            base_score += 0.2

        significance_multiplier = len(indicators["significance_factors"]) * 0.1

        return min(base_score + significance_multiplier, 1.0)

    def _identify_response_opportunities(self, topic: str, indicators: Dict) -> List[Dict]:
        """Identify specific opportunities for responding to cultural moments."""

        opportunities = []

        if indicators["moment_type"] == "controversy":
            opportunities.append({
                "type": "diplomatic_commentary",
                "description": "Provide balanced perspective on the situation",
                "risk_level": "medium",
                "potential_benefit": "thought_leadership"
            })

        if indicators["moment_type"] == "collaboration":
            opportunities.append({
                "type": "collaboration_celebration",
                "description": "Celebrate the artistic collaboration",
                "risk_level": "low",
                "potential_benefit": "community_building"
            })

        opportunities.append({
            "type": "trend_participation",
            "description": f"Participate in {topic} conversation organically",
            "risk_level": "low",
            "potential_benefit": "visibility"
        })

        return opportunities

    def _recommend_response_timing(self, topic: str, indicators: Dict) -> Dict[str, Any]:
        """Recommend optimal timing for responding to cultural moments."""

        timing = {
            "urgency": indicators.get("response_urgency", "low"),
            "optimal_window": "6-24_hours",
            "latest_response_time": "72_hours",
            "reasoning": "Standard cultural moment response timing"
        }

        if indicators["moment_type"] == "controversy":
            timing.update({
                "urgency": "high",
                "optimal_window": "2-6_hours",
                "reasoning": "Controversies move fast - early response has more impact"
            })

        return timing

    def save_logs(self):
        """Save all momentum tracking logs."""
        save_json(MOMENTUM_TRACKER_LOG, self.momentum_log)
        save_json(TOPIC_AMPLIFICATION_LOG, self.amplification_log)
        save_json(VIRAL_POTENTIAL_LOG, self.viral_potential_log)


def run_topic_momentum_analysis():
    """Main function to run complete topic momentum analysis."""

    print("\n[*] APU-50 Topic Momentum Tracker Starting...")

    tracker = TopicMomentumTracker()

    # Detect trending topics
    trending_analysis = tracker.detect_trending_topics()
    print(f"[DETECTED] {len(trending_analysis['detected_topics'])} trending topics")

    # Amplify strategic topics
    amplification_plan = tracker.amplify_strategic_topics(trending_analysis, "balanced")
    print(f"[AMPLIFICATION] {len(amplification_plan['selected_topics'])} topics selected for amplification")

    # Identify cultural moments
    cultural_moments = tracker.identify_cultural_moments()
    print(f"[CULTURAL] {len(cultural_moments['identified_moments'])} cultural moments identified")

    # Log everything
    today = today_str()

    tracker.momentum_log[today] = trending_analysis
    tracker.amplification_log[today] = amplification_plan
    tracker.viral_potential_log[today] = cultural_moments

    tracker.save_logs()

    # Generate summary report
    summary = {
        "date": today,
        "trending_topics_count": len(trending_analysis["detected_topics"]),
        "amplification_targets": len(amplification_plan["selected_topics"]),
        "cultural_moments": len(cultural_moments["identified_moments"]),
        "top_momentum_score": max(
            (data.get("momentum_score", 0) for data in trending_analysis["detected_topics"].values()),
            default=0
        ),
        "highest_viral_potential": max(
            (data.get("viral_potential", 0) for data in trending_analysis["detected_topics"].values()),
            default=0
        )
    }

    # Log summary
    status = "ok" if summary["top_momentum_score"] > 0.5 else "warning" if summary["top_momentum_score"] > 0.2 else "low_activity"
    detail = f"Topics: {summary['trending_topics_count']}, Max momentum: {summary['top_momentum_score']:.2f}, Cultural moments: {summary['cultural_moments']}"
    log_run("TopicMomentumTrackerAPU50", status, detail)

    print(f"\n[SUMMARY] Momentum tracking complete")
    print(f"  • Trending topics: {summary['trending_topics_count']}")
    print(f"  • Amplification targets: {summary['amplification_targets']}")
    print(f"  • Cultural moments: {summary['cultural_moments']}")
    print(f"  • Top momentum score: {summary['top_momentum_score']:.2f}")

    return summary


if __name__ == "__main__":
    import random  # For simulation
    result = run_topic_momentum_analysis()

    if result["top_momentum_score"] < 0.2:
        print("\n[LOW ACTIVITY] Limited topic momentum detected")
        sys.exit(1)
    else:
        print(f"\n[OK] Topic momentum analysis complete")
        sys.exit(0)