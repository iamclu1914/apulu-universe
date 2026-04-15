"""
platform_optimizer.py — Platform-specific hashtag optimization strategies
Created for: APU-150 hashtag-scan enhancement
Author: Sage - Content Agent

Provides platform-specific optimization strategies for hashtag selection,
timing, and content adaptation across different social media platforms.
"""

import json
import sys
from datetime import datetime, time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import VAWN_DIR, RESEARCH_DIR, load_json, save_json


@dataclass
class PlatformStrategy:
    """Platform-specific optimization strategy"""
    name: str
    optimal_hashtag_count: int
    max_hashtag_count: int
    hashtag_style: str
    content_focus: str
    posting_times: List[str]
    engagement_factors: Dict[str, float]
    brand_weighting: float
    viral_potential: float
    algorithm_preferences: List[str]


class PlatformOptimizer:
    """Advanced platform-specific hashtag optimization"""

    def __init__(self):
        self.strategies = self._initialize_platform_strategies()
        self.vawn_brand_profile = self._load_vawn_brand_profile()

    def _initialize_platform_strategies(self) -> Dict[str, PlatformStrategy]:
        """Initialize optimization strategies for each platform"""
        return {
            "instagram": PlatformStrategy(
                name="Instagram",
                optimal_hashtag_count=12,
                max_hashtag_count=30,
                hashtag_style="detailed_and_niche",
                content_focus="visual_storytelling",
                posting_times=["7:30 AM", "1:00 PM", "7:00 PM"],
                engagement_factors={
                    "brand_hashtags": 1.8,
                    "geographic_hashtags": 1.5,
                    "niche_hashtags": 1.7,
                    "trending_hashtags": 1.3,
                    "generic_hashtags": 0.7,
                    "community_hashtags": 1.4
                },
                brand_weighting=0.6,
                viral_potential=0.8,
                algorithm_preferences=[
                    "consistent_branding",
                    "high_engagement_rate",
                    "story_integration",
                    "authentic_content",
                    "community_building"
                ]
            ),

            "tiktok": PlatformStrategy(
                name="TikTok",
                optimal_hashtag_count=4,
                max_hashtag_count=10,
                hashtag_style="viral_and_trendy",
                content_focus="entertainment_and_music",
                posting_times=["6:00 AM", "10:00 AM", "7:00 PM"],
                engagement_factors={
                    "viral_hashtags": 2.5,
                    "music_hashtags": 2.0,
                    "brand_hashtags": 1.5,
                    "challenge_hashtags": 2.2,
                    "trending_hashtags": 2.0,
                    "generic_hashtags": 0.6
                },
                brand_weighting=0.4,
                viral_potential=1.0,
                algorithm_preferences=[
                    "high_completion_rate",
                    "rapid_engagement",
                    "music_sync",
                    "trending_participation",
                    "shareability"
                ]
            ),

            "x": PlatformStrategy(
                name="X (Twitter)",
                optimal_hashtag_count=2,
                max_hashtag_count=4,
                hashtag_style="conversational",
                content_focus="thought_leadership",
                posting_times=["9:00 AM", "12:00 PM", "3:00 PM"],
                engagement_factors={
                    "conversation_hashtags": 1.8,
                    "brand_hashtags": 1.3,
                    "trending_hashtags": 1.6,
                    "news_hashtags": 1.4,
                    "generic_hashtags": 0.8
                },
                brand_weighting=0.7,
                viral_potential=0.6,
                algorithm_preferences=[
                    "engagement_velocity",
                    "reply_threads",
                    "retweet_potential",
                    "link_sharing",
                    "real_time_relevance"
                ]
            ),

            "threads": PlatformStrategy(
                name="Threads",
                optimal_hashtag_count=1,
                max_hashtag_count=3,
                hashtag_style="community_focused",
                content_focus="authentic_conversation",
                posting_times=["8:00 AM", "1:00 PM", "8:00 PM"],
                engagement_factors={
                    "community_hashtags": 1.9,
                    "brand_hashtags": 1.4,
                    "conversation_hashtags": 1.7,
                    "authentic_hashtags": 1.6,
                    "trending_hashtags": 1.2,
                    "generic_hashtags": 0.9
                },
                brand_weighting=0.8,
                viral_potential=0.5,
                algorithm_preferences=[
                    "authentic_engagement",
                    "community_building",
                    "meaningful_replies",
                    "follow_relationships",
                    "consistent_posting"
                ]
            ),

            "bluesky": PlatformStrategy(
                name="Bluesky",
                optimal_hashtag_count=3,
                max_hashtag_count=5,
                hashtag_style="niche_and_authentic",
                content_focus="community_and_discovery",
                posting_times=["10:00 AM", "2:00 PM", "9:00 PM"],
                engagement_factors={
                    "niche_hashtags": 2.0,
                    "community_hashtags": 1.8,
                    "brand_hashtags": 1.2,
                    "authentic_hashtags": 1.7,
                    "discovery_hashtags": 1.5,
                    "generic_hashtags": 1.0
                },
                brand_weighting=0.5,
                viral_potential=0.4,
                algorithm_preferences=[
                    "organic_discovery",
                    "niche_communities",
                    "authentic_content",
                    "network_effects",
                    "quality_engagement"
                ]
            )
        }

    def _load_vawn_brand_profile(self) -> Dict:
        """Load Vawn's brand profile for optimization"""
        return {
            "core_themes": [
                "psychedelic boom bap",
                "orchestral trap",
                "atlanta hip-hop",
                "brooklyn roots",
                "conscious rap",
                "independent artist",
                "anti-hype",
                "authentic sound"
            ],
            "geographic_focus": ["atlanta", "brooklyn", "nyc", "atl", "south", "east coast"],
            "music_styles": ["boom bap", "trap", "orchestral", "psychedelic", "soul", "conscious"],
            "brand_values": ["authentic", "independent", "anti-hype", "quality", "underground", "genuine"],
            "target_audience": ["hip-hop heads", "conscious rap fans", "independent music lovers", "atlanta scene"],
            "content_pillars": [
                "musical process",
                "authentic journey",
                "atlanta culture",
                "independent grind",
                "quality over quantity"
            ]
        }

    def optimize_hashtags_for_platform(self, hashtags: List[str], platform: str) -> Dict:
        """
        Optimize hashtag selection and ranking for specific platform

        Args:
            hashtags: List of candidate hashtags
            platform: Target platform name

        Returns:
            Dict with optimized hashtag recommendations
        """
        if platform.lower() not in self.strategies:
            raise ValueError(f"Platform {platform} not supported")

        strategy = self.strategies[platform.lower()]

        # Score each hashtag for this platform
        scored_hashtags = []
        for hashtag in hashtags:
            score = self._calculate_platform_score(hashtag, strategy)
            scored_hashtags.append({
                "hashtag": hashtag,
                "score": score,
                "reasoning": self._explain_score(hashtag, strategy, score)
            })

        # Sort by score and select optimal count
        scored_hashtags.sort(key=lambda x: x["score"], reverse=True)

        # Select hashtags based on strategy
        selected = self._select_optimal_mix(scored_hashtags, strategy)

        return {
            "platform": platform,
            "strategy": {
                "optimal_count": strategy.optimal_hashtag_count,
                "style": strategy.hashtag_style,
                "focus": strategy.content_focus
            },
            "selected_hashtags": selected[:strategy.optimal_hashtag_count],
            "all_scored": scored_hashtags,
            "optimization_notes": self._generate_optimization_notes(selected, strategy),
            "posting_recommendations": {
                "best_times": strategy.posting_times,
                "algorithm_tips": strategy.algorithm_preferences[:3]
            }
        }

    def _calculate_platform_score(self, hashtag: str, strategy: PlatformStrategy) -> float:
        """Calculate platform-specific score for hashtag"""

        base_score = 1.0
        hashtag_lower = hashtag.lower().replace("#", "")

        # Apply engagement factors based on hashtag type
        hashtag_type = self._classify_hashtag(hashtag_lower)
        engagement_multiplier = strategy.engagement_factors.get(hashtag_type, 1.0)
        score = base_score * engagement_multiplier

        # Brand alignment bonus
        brand_alignment = self._calculate_brand_alignment(hashtag_lower)
        score *= (1.0 + (brand_alignment * strategy.brand_weighting))

        # Platform-specific optimizations
        score *= self._apply_platform_specific_modifiers(hashtag_lower, strategy)

        return min(score, 5.0)  # Cap at 5.0

    def _classify_hashtag(self, hashtag: str) -> str:
        """Classify hashtag type for scoring"""

        # Brand hashtags
        if any(brand in hashtag for brand in ["vawn", "apulu"]):
            return "brand_hashtags"

        # Geographic hashtags
        if any(geo in hashtag for geo in self.vawn_brand_profile["geographic_focus"]):
            return "geographic_hashtags"

        # Music style hashtags
        if any(style in hashtag for style in self.vawn_brand_profile["music_styles"]):
            return "niche_hashtags"

        # Community hashtags
        if any(value in hashtag for value in ["indie", "underground", "independent", "conscious"]):
            return "community_hashtags"

        # Trending music hashtags
        if any(trend in hashtag for trend in ["rap", "hiphop", "music", "beats", "producer"]):
            return "trending_hashtags"

        # Viral potential hashtags
        if hashtag in ["wordplay", "bars", "lyricist", "flow", "freestyle"]:
            return "viral_hashtags"

        # Conversation starters
        if hashtag in ["thoughts", "real", "truth", "perspective", "opinion"]:
            return "conversation_hashtags"

        # Authentic hashtags
        if hashtag in ["real", "authentic", "genuine", "honest", "truth"]:
            return "authentic_hashtags"

        # Discovery hashtags
        if hashtag in ["discover", "newmusic", "emerging", "rising"]:
            return "discovery_hashtags"

        return "generic_hashtags"

    def _calculate_brand_alignment(self, hashtag: str) -> float:
        """Calculate how well hashtag aligns with Vawn brand"""

        alignment_score = 0.0

        # Core themes
        for theme_phrase in self.vawn_brand_profile["core_themes"]:
            theme_words = theme_phrase.split()
            if any(word in hashtag for word in theme_words):
                alignment_score += 0.3

        # Geographic alignment
        for geo in self.vawn_brand_profile["geographic_focus"]:
            if geo in hashtag:
                alignment_score += 0.2

        # Music style alignment
        for style in self.vawn_brand_profile["music_styles"]:
            if style in hashtag:
                alignment_score += 0.25

        # Brand values alignment
        for value in self.vawn_brand_profile["brand_values"]:
            if value in hashtag:
                alignment_score += 0.15

        return min(alignment_score, 1.0)

    def _apply_platform_specific_modifiers(self, hashtag: str, strategy: PlatformStrategy) -> float:
        """Apply platform-specific scoring modifiers"""

        modifier = 1.0

        # Instagram: favor detailed, niche hashtags
        if strategy.name == "Instagram":
            if len(hashtag) > 8:  # Longer, more specific hashtags
                modifier *= 1.2
            if any(niche in hashtag for niche in ["orchestral", "psychedelic", "conscious"]):
                modifier *= 1.3

        # TikTok: favor shorter, viral hashtags
        elif strategy.name == "TikTok":
            if len(hashtag) <= 6:  # Shorter hashtags
                modifier *= 1.3
            if hashtag in ["vawn", "wordplay", "bars", "flow"]:
                modifier *= 1.4

        # X: favor conversation starters
        elif strategy.name.startswith("X"):
            if hashtag in ["lyricist", "thoughts", "real", "hiphop"]:
                modifier *= 1.3
            if len(hashtag) <= 8:  # Prefer shorter for Twitter
                modifier *= 1.1

        # Threads: favor authentic, community-focused
        elif strategy.name == "Threads":
            if any(auth in hashtag for auth in ["real", "authentic", "indie", "underground"]):
                modifier *= 1.4

        # Bluesky: favor niche and discovery
        elif strategy.name == "Bluesky":
            if any(niche in hashtag for niche in ["psychedelic", "boom", "conscious", "orchestral"]):
                modifier *= 1.3

        return modifier

    def _explain_score(self, hashtag: str, strategy: PlatformStrategy, score: float) -> str:
        """Generate explanation for hashtag score"""

        hashtag_type = self._classify_hashtag(hashtag.lower().replace("#", ""))
        brand_alignment = self._calculate_brand_alignment(hashtag.lower().replace("#", ""))

        explanations = []

        explanations.append(f"Type: {hashtag_type}")

        if brand_alignment > 0.5:
            explanations.append(f"Strong brand alignment ({brand_alignment:.1f})")
        elif brand_alignment > 0.2:
            explanations.append(f"Moderate brand alignment ({brand_alignment:.1f})")
        else:
            explanations.append(f"Low brand alignment ({brand_alignment:.1f})")

        if score > 3.0:
            explanations.append("Excellent fit for platform")
        elif score > 2.0:
            explanations.append("Good fit for platform")
        elif score > 1.0:
            explanations.append("Acceptable for platform")
        else:
            explanations.append("Poor fit for platform")

        return " | ".join(explanations)

    def _select_optimal_mix(self, scored_hashtags: List[Dict], strategy: PlatformStrategy) -> List[Dict]:
        """Select optimal mix of hashtags based on platform strategy"""

        selected = []
        categories_used = {}

        # Ensure brand representation
        brand_hashtags = [h for h in scored_hashtags if "brand" in self._classify_hashtag(h["hashtag"].lower().replace("#", ""))]
        if brand_hashtags and strategy.brand_weighting > 0.5:
            selected.append(brand_hashtags[0])
            categories_used["brand"] = 1

        # Fill remaining slots with best scoring hashtags, ensuring diversity
        for hashtag_data in scored_hashtags:
            if len(selected) >= strategy.optimal_hashtag_count:
                break

            hashtag = hashtag_data["hashtag"]
            category = self._classify_hashtag(hashtag.lower().replace("#", ""))

            # Skip if already selected
            if hashtag_data in selected:
                continue

            # Limit category repetition (except for high-scoring ones)
            if categories_used.get(category, 0) < 2 or hashtag_data["score"] > 3.0:
                selected.append(hashtag_data)
                categories_used[category] = categories_used.get(category, 0) + 1

        return selected

    def _generate_optimization_notes(self, selected_hashtags: List[Dict], strategy: PlatformStrategy) -> List[str]:
        """Generate optimization notes for the hashtag selection"""

        notes = []

        # Count analysis
        count = len(selected_hashtags)
        if count < strategy.optimal_hashtag_count:
            notes.append(f"Consider adding {strategy.optimal_hashtag_count - count} more hashtags for optimal reach")
        elif count > strategy.optimal_hashtag_count:
            notes.append(f"Consider reducing to {strategy.optimal_hashtag_count} hashtags for better algorithm performance")

        # Quality analysis
        avg_score = sum(h["score"] for h in selected_hashtags) / max(len(selected_hashtags), 1)
        if avg_score > 2.5:
            notes.append(f"Excellent hashtag mix (avg score: {avg_score:.1f})")
        elif avg_score > 1.5:
            notes.append(f"Good hashtag mix (avg score: {avg_score:.1f})")
        else:
            notes.append(f"Hashtag mix could be improved (avg score: {avg_score:.1f})")

        # Brand presence analysis
        brand_count = sum(1 for h in selected_hashtags if "brand" in self._classify_hashtag(h["hashtag"].lower().replace("#", "")))
        if brand_count == 0 and strategy.brand_weighting > 0.5:
            notes.append("Consider adding brand-specific hashtags for better brand awareness")

        # Platform-specific notes
        if strategy.name == "Instagram" and count < 10:
            notes.append("Instagram performs better with 10-15 hashtags - consider expanding")
        elif strategy.name == "TikTok" and count > 5:
            notes.append("TikTok algorithm prefers 3-5 focused hashtags over many")
        elif strategy.name.startswith("X") and count > 2:
            notes.append("Twitter/X works best with 1-2 strategic hashtags to avoid looking spammy")

        return notes

    def optimize_all_platforms(self, base_hashtags: List[str]) -> Dict:
        """Optimize hashtags for all platforms simultaneously"""

        results = {}

        for platform in self.strategies.keys():
            try:
                platform_result = self.optimize_hashtags_for_platform(base_hashtags, platform)
                results[platform] = platform_result
            except Exception as e:
                results[platform] = {"error": str(e)}

        # Generate cross-platform insights
        cross_platform_insights = self._analyze_cross_platform_performance(results)

        return {
            "platform_optimizations": results,
            "cross_platform_insights": cross_platform_insights,
            "generated_at": datetime.now().isoformat(),
            "base_hashtags_count": len(base_hashtags)
        }

    def _analyze_cross_platform_performance(self, results: Dict) -> Dict:
        """Analyze performance patterns across platforms"""

        # Find hashtags that perform well across multiple platforms
        hashtag_scores = {}
        platform_count = len([r for r in results.values() if "error" not in r])

        for platform, result in results.items():
            if "error" in result:
                continue

            for hashtag_data in result.get("all_scored", []):
                hashtag = hashtag_data["hashtag"]
                score = hashtag_data["score"]

                if hashtag not in hashtag_scores:
                    hashtag_scores[hashtag] = []
                hashtag_scores[hashtag].append(score)

        # Identify top cross-platform performers
        top_performers = []
        for hashtag, scores in hashtag_scores.items():
            avg_score = sum(scores) / len(scores)
            consistency = 1.0 - (max(scores) - min(scores)) / max(max(scores), 1)

            top_performers.append({
                "hashtag": hashtag,
                "avg_score": avg_score,
                "consistency": consistency,
                "platform_count": len(scores)
            })

        top_performers.sort(key=lambda x: x["avg_score"], reverse=True)

        return {
            "top_cross_platform_hashtags": top_performers[:10],
            "platform_coverage": platform_count,
            "total_hashtags_analyzed": len(hashtag_scores),
            "recommendations": [
                f"Top performer: {top_performers[0]['hashtag']} (avg: {top_performers[0]['avg_score']:.1f})" if top_performers else "No clear top performer",
                f"Most consistent: {sorted(top_performers, key=lambda x: x['consistency'], reverse=True)[0]['hashtag']}" if top_performers else "Need more data",
                f"Best overall strategy: Focus on brand-aligned hashtags for consistency across platforms"
            ]
        }


def main():
    """Test the platform optimizer"""
    print("\n[*] Platform Hashtag Optimizer - APU-150")
    print("=" * 60)

    optimizer = PlatformOptimizer()

    # Test with current Vawn hashtags
    test_hashtags = [
        "#orchestralrap", "#apulurecords", "#rapmusic", "#boombap",
        "#psychedelichiphop", "#trapsoul", "#brooklynhiphop", "#atlhiphop",
        "#consciousrap", "#lyricalrap", "#indierap", "#vawn", "#wordplay"
    ]

    print(f"Testing optimization for {len(test_hashtags)} hashtags across all platforms...")

    results = optimizer.optimize_all_platforms(test_hashtags)

    # Display results
    for platform, result in results["platform_optimizations"].items():
        if "error" in result:
            print(f"\n{platform.upper()}: ERROR - {result['error']}")
            continue

        print(f"\n{platform.upper()}:")
        print(f"  Optimal count: {result['strategy']['optimal_count']}")
        print(f"  Style: {result['strategy']['style']}")

        print(f"  Selected hashtags:")
        for i, hashtag_data in enumerate(result["selected_hashtags"], 1):
            print(f"    {i}. {hashtag_data['hashtag']} (score: {hashtag_data['score']:.1f})")

        print(f"  Optimization notes:")
        for note in result["optimization_notes"]:
            print(f"    • {note}")

    # Cross-platform insights
    insights = results["cross_platform_insights"]
    print(f"\nCROSS-PLATFORM INSIGHTS:")
    print(f"  Platform coverage: {insights['platform_coverage']}")
    print(f"  Hashtags analyzed: {insights['total_hashtags_analyzed']}")

    print(f"  Top recommendations:")
    for rec in insights["recommendations"]:
        print(f"    • {rec}")

    # Save results
    output_path = RESEARCH_DIR / "platform_optimization_results.json"
    save_json(output_path, results)
    print(f"\n[OK] Optimization results saved to {output_path}")

    return results


if __name__ == "__main__":
    main()