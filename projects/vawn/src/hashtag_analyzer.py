"""
hashtag_analyzer.py — Enhanced hashtag quality validation and performance analysis
Created by: Sage - Content Agent (APU-26)

Provides intelligent hashtag scoring, relevance analysis, and performance prediction
based on Vawn's brand profile and cross-platform optimization strategies.
"""

import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import Counter

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import (
    VAWN_DIR, RESEARCH_DIR, METRICS_LOG, load_json, save_json,
    VAWN_PROFILE, COMPARABLE_ARTISTS
)

# Analysis configuration
HASHTAG_ANALYSIS_LOG = RESEARCH_DIR / "hashtag_analysis.json"

@dataclass
class HashtagScore:
    """Comprehensive hashtag scoring data"""
    hashtag: str
    relevance_score: float  # 0-1: How well it matches Vawn's brand
    competition_score: float  # 0-1: Competition level (lower is better)
    growth_potential: float  # 0-1: Potential for discovery
    platform_fit: Dict[str, float]  # Platform-specific scores
    overall_score: float
    reasoning: str

# Vawn brand keywords and themes
BRAND_KEYWORDS = {
    "core_sound": {
        "psychedelic", "boom bap", "boombap", "atlanta", "trap", "soul",
        "orchestral", "trapsoul", "conscious", "lyrical"
    },
    "themes": {
        "fear", "failure", "dependability", "love", "journey", "growth",
        "pattern", "recognition", "authority", "quiet", "earned", "confidence"
    },
    "geography": {
        "brooklyn", "atlanta", "nyc", "atl", "east coast", "south",
        "georgia", "new york"
    },
    "brand_values": {
        "independent", "authentic", "real", "underground", "indie",
        "anti-hype", "genuine", "artist", "musician", "creative"
    }
}

# High competition hashtags to avoid
HIGH_COMPETITION = {
    "#music", "#rap", "#hiphop", "#newmusic", "#song", "#artist",
    "#rapper", "#beats", "#studio", "#producer", "#musician"
}

# Platform-specific optimization factors
PLATFORM_OPTIMIZATION = {
    "instagram": {
        "preferred_length": (10, 30),  # character count
        "max_count": 15,
        "growth_tags": {"reels", "explore", "fyp"},
        "avoid": {"followback", "like4like", "spam"}
    },
    "tiktok": {
        "preferred_length": (8, 20),
        "max_count": 5,
        "growth_tags": {"fyp", "foryou", "viral", "trending"},
        "avoid": {"cringe", "basic"}
    },
    "x": {
        "preferred_length": (6, 15),
        "max_count": 2,
        "growth_tags": {"trending", "breaking"},
        "avoid": {"spam", "bot"}
    },
    "bluesky": {
        "preferred_length": (8, 20),
        "max_count": 3,
        "growth_tags": {"newmusic", "independent", "discovery"},
        "avoid": {"spam"}
    },
    "threads": {
        "preferred_length": (0, 0),  # No hashtags - uses topics
        "max_count": 0,
        "growth_tags": set(),
        "avoid": set()
    }
}


def calculate_relevance_score(hashtag: str) -> Tuple[float, str]:
    """
    Calculate how well a hashtag matches Vawn's brand profile.
    Returns (score, reasoning).
    """
    tag_clean = hashtag.lower().replace("#", "")
    score = 0.0
    reasons = []

    # Core sound match (highest weight)
    for keyword in BRAND_KEYWORDS["core_sound"]:
        if keyword in tag_clean:
            score += 0.4
            reasons.append(f"matches core sound: {keyword}")

    # Thematic alignment
    for keyword in BRAND_KEYWORDS["themes"]:
        if keyword in tag_clean:
            score += 0.2
            reasons.append(f"aligns with theme: {keyword}")

    # Geographic relevance
    for keyword in BRAND_KEYWORDS["geography"]:
        if keyword in tag_clean:
            score += 0.15
            reasons.append(f"geographic relevance: {keyword}")

    # Brand values
    for keyword in BRAND_KEYWORDS["brand_values"]:
        if keyword in tag_clean:
            score += 0.1
            reasons.append(f"brand value: {keyword}")

    # Penalty for high competition
    if hashtag in HIGH_COMPETITION:
        score *= 0.6
        reasons.append("high competition penalty")

    # Cap at 1.0
    score = min(score, 1.0)

    reasoning = "; ".join(reasons) if reasons else "no specific brand alignment"
    return score, reasoning


def calculate_competition_score(hashtag: str) -> float:
    """
    Estimate competition level. Lower scores indicate less competition (better).
    """
    tag_clean = hashtag.lower().replace("#", "")

    # Ultra high competition
    if hashtag in HIGH_COMPETITION:
        return 0.9

    # Length-based heuristic (shorter = more competitive)
    if len(tag_clean) <= 6:
        return 0.8
    elif len(tag_clean) <= 10:
        return 0.6
    elif len(tag_clean) <= 15:
        return 0.4
    else:
        return 0.2


def calculate_growth_potential(hashtag: str, platform: str) -> float:
    """
    Estimate growth potential for a specific platform.
    """
    tag_clean = hashtag.lower().replace("#", "")
    platform_opts = PLATFORM_OPTIMIZATION.get(platform, {})

    base_score = 0.5

    # Length optimization
    preferred_range = platform_opts.get("preferred_length", (5, 20))
    tag_len = len(tag_clean)
    if preferred_range[0] <= tag_len <= preferred_range[1]:
        base_score += 0.2

    # Growth tag bonus
    growth_tags = platform_opts.get("growth_tags", set())
    for growth_tag in growth_tags:
        if growth_tag in tag_clean:
            base_score += 0.2
            break

    # Avoid penalty
    avoid_tags = platform_opts.get("avoid", set())
    for avoid_tag in avoid_tags:
        if avoid_tag in tag_clean:
            base_score -= 0.3
            break

    # Music-specific platform bonuses
    if platform == "instagram" and any(word in tag_clean for word in ["reels", "music", "artist"]):
        base_score += 0.1
    elif platform == "tiktok" and any(word in tag_clean for word in ["sound", "audio", "music"]):
        base_score += 0.1

    return min(max(base_score, 0.0), 1.0)


def calculate_platform_fitness(hashtag: str) -> Dict[str, float]:
    """Calculate platform-specific fitness scores."""
    return {
        platform: calculate_growth_potential(hashtag, platform)
        for platform in ["instagram", "tiktok", "x", "bluesky", "threads"]
    }


def analyze_hashtag(hashtag: str) -> HashtagScore:
    """Comprehensive hashtag analysis."""
    relevance_score, reasoning = calculate_relevance_score(hashtag)
    competition_score = calculate_competition_score(hashtag)
    platform_fitness = calculate_platform_fitness(hashtag)

    # Overall score calculation (weighted average)
    overall_score = (
        relevance_score * 0.4 +           # Brand alignment most important
        (1 - competition_score) * 0.3 +   # Lower competition is better
        sum(platform_fitness.values()) / len(platform_fitness) * 0.3
    )

    return HashtagScore(
        hashtag=hashtag,
        relevance_score=relevance_score,
        competition_score=competition_score,
        growth_potential=sum(platform_fitness.values()) / len(platform_fitness),
        platform_fit=platform_fitness,
        overall_score=overall_score,
        reasoning=reasoning
    )


def analyze_hashtag_set(hashtags: List[str], platform: str = "all") -> List[HashtagScore]:
    """Analyze a set of hashtags and return sorted by quality."""
    scores = [analyze_hashtag(tag) for tag in hashtags]

    # Sort by overall score (descending)
    scores.sort(key=lambda x: x.overall_score, reverse=True)

    return scores


def load_historical_performance() -> Dict[str, Dict]:
    """Load historical hashtag performance data from metrics."""
    metrics = load_json(METRICS_LOG)
    hashtag_performance = {}

    # Extract hashtag usage and engagement from metrics
    # This would be enhanced with actual performance data

    return hashtag_performance


def recommend_hashtag_mix(platform: str, count: int) -> List[str]:
    """Recommend optimized hashtag mix for a platform."""
    # Load current trending and rotation hashtags
    hashtags_dir = VAWN_DIR / "Social_Media_Exports" / "Trending_Hashtags"
    platform_map = {
        "instagram": "Instagram",
        "tiktok": "TikTok",
        "x": "X",
        "bluesky": "Bluesky"
    }

    all_hashtags = []

    # Get trending hashtags
    folder = platform_map.get(platform)
    if folder:
        hashtag_file = hashtags_dir / folder / "hashtags.txt"
        if hashtag_file.exists():
            tags = [line.strip() for line in hashtag_file.read_text().splitlines() if line.strip()]
            all_hashtags.extend(tags)

    # Get rotation hashtags
    try:
        sys.path.append(str(VAWN_DIR))
        from hashtag_engine import DISCOVERY, NICHE, BRANDED
        all_hashtags.extend([f"#{tag.replace('#', '')}" for tag in DISCOVERY + NICHE + BRANDED])
    except ImportError:
        pass

    # Remove duplicates
    all_hashtags = list(set(all_hashtags))

    # Analyze and score
    scored = analyze_hashtag_set(all_hashtags, platform)

    # Return top performers
    return [score.hashtag for score in scored[:count]]


def save_analysis_report(scores: List[HashtagScore], filename_suffix: str = ""):
    """Save detailed hashtag analysis to log."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "analysis_date": str(date.today()),
        "total_hashtags": len(scores),
        "avg_relevance": sum(s.relevance_score for s in scores) / len(scores) if scores else 0,
        "avg_competition": sum(s.competition_score for s in scores) / len(scores) if scores else 0,
        "hashtags": [
            {
                "hashtag": s.hashtag,
                "scores": {
                    "relevance": s.relevance_score,
                    "competition": s.competition_score,
                    "growth_potential": s.growth_potential,
                    "overall": s.overall_score
                },
                "platform_fitness": s.platform_fit,
                "reasoning": s.reasoning
            }
            for s in scores
        ]
    }

    # Load existing analysis log
    analysis_log = load_json(HASHTAG_ANALYSIS_LOG)
    today = str(date.today())

    if today not in analysis_log:
        analysis_log[today] = []

    analysis_log[today].append(report)

    # Keep only last 30 days
    cutoff = date.today() - timedelta(days=30)
    analysis_log = {
        k: v for k, v in analysis_log.items()
        if datetime.fromisoformat(k + "T00:00:00").date() >= cutoff
    }

    save_json(HASHTAG_ANALYSIS_LOG, analysis_log)
    return report


if __name__ == "__main__":
    # Test analysis on current hashtags
    from glob import glob

    print("\n[*] Hashtag Analyzer - APU-26 Enhancement")
    print("=" * 50)

    # Load current Instagram hashtags for analysis
    instagram_file = VAWN_DIR / "Social_Media_Exports" / "Trending_Hashtags" / "Instagram" / "hashtags.txt"
    if instagram_file.exists():
        hashtags = [line.strip() for line in instagram_file.read_text().splitlines() if line.strip()]

        print(f"\n[ANALYSIS] Current Instagram hashtags ({len(hashtags)}):")
        scores = analyze_hashtag_set(hashtags, "instagram")

        for i, score in enumerate(scores[:10]):  # Top 10
            print(f"{i+1:2d}. {score.hashtag:<20} | {score.overall_score:.2f} | {score.reasoning}")

        # Save analysis
        report = save_analysis_report(scores, "instagram_current")
        print(f"\n[OK] Analysis saved to {HASHTAG_ANALYSIS_LOG}")
        print(f"[METRICS] Avg Relevance: {report['avg_relevance']:.2f} | Avg Competition: {report['avg_competition']:.2f}")

        # Recommendations
        recommended = recommend_hashtag_mix("instagram", 10)
        print(f"\n[RECOMMENDATIONS] Top 10 optimized hashtags:")
        for i, tag in enumerate(recommended):
            print(f"{i+1:2d}. {tag}")

    else:
        print("[ERROR] No Instagram hashtags found. Run scan_hashtags.py first.")