"""
APU-51 Community Intelligence Engine (PATCHED)
Enhanced with fixed sentiment analysis system.
"""

import sys
sys.path.insert(0, r"C:\Users\rdyal\Vawn\src")

# Import patched components
from enhanced_sentiment_analyzer import EnhancedSentimentAnalyzer

# Import original APU-51 components (excluding broken sentiment analysis)
sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import (
    load_json, save_json, ENGAGEMENT_LOG, RESEARCH_LOG, METRICS_LOG,
    VAWN_DIR, log_run, today_str, get_anthropic_client
)

from datetime import datetime, timedelta

# Enhanced APU-51 runner with fixed sentiment analysis
def run_patched_apu51():
    """Run APU-51 with enhanced sentiment analysis."""

    print("\n[*] APU-51 Community Intelligence Engine (PATCHED)")
    print("[VERSION] Community Intelligence v1.1 (Sentiment Analysis Fixed)")

    # Get comments for analysis
    engagement_log = load_json(ENGAGEMENT_LOG)
    recent_comments = []

    # Get comments from last 24 hours
    cutoff = datetime.now() - timedelta(days=1)

    for entry in engagement_log.get("history", []):
        try:
            entry_date = datetime.fromisoformat(entry["date"])
            if entry_date >= cutoff:
                recent_comments.append({
                    "text": entry.get("comment", ""),
                    "platform": entry.get("platform", "unknown"),
                    "timestamp": entry["date"],
                    "author": entry.get("author", "unknown")
                })
        except:
            # Handle date parsing errors
            recent_comments.append({
                "text": entry.get("comment", ""),
                "platform": entry.get("platform", "unknown"),
                "timestamp": entry.get("date", ""),
                "author": entry.get("author", "unknown")
            })

    print(f"[DATA] Found {len(recent_comments)} recent comments for analysis")

    if recent_comments:
        # Use enhanced sentiment analyzer
        print("[ANALYSIS] Running ENHANCED sentiment analysis...")
        analyzer = EnhancedSentimentAnalyzer()
        sentiment_analysis = analyzer.analyze_sentiment_with_fallback(recent_comments)

        print(f"[RESULTS] Sentiment Analysis Complete!")
        print(f"  Overall Sentiment: {sentiment_analysis['overall_sentiment']:+.3f}")
        print(f"  Community Satisfaction: {sentiment_analysis['community_satisfaction']:.3f}")
        print(f"  Analysis Method: {sentiment_analysis['analysis_method']}")
        print(f"  Comments Analyzed: {sentiment_analysis['analyzed_count']}")

        # Simple community health calculation
        sentiment_score = max(0, (sentiment_analysis['overall_sentiment'] + 1) / 2)  # Convert -1,1 to 0,1
        satisfaction_score = sentiment_analysis['community_satisfaction']

        community_health = (sentiment_score + satisfaction_score) / 2

        if community_health >= 0.7:
            health_status = "good"
        elif community_health >= 0.5:
            health_status = "fair"
        else:
            health_status = "needs_attention"

        print(f"\n[HEALTH] Community Health Score: {community_health:.3f} ({health_status})")

        # Log results
        log_entry = (f"PATCHED APU-51: Sentiment {sentiment_analysis['overall_sentiment']:+.2f}, "
                    f"Satisfaction {sentiment_analysis['community_satisfaction']:.2f}, "
                    f"Health {community_health:.2f} ({health_status}), "
                    f"Method: {sentiment_analysis['analysis_method']}")

        log_run("PatchedAPU51", "ok" if health_status != "needs_attention" else "warning", log_entry)

        return {
            "sentiment_analysis": sentiment_analysis,
            "community_health": community_health,
            "health_status": health_status
        }
    else:
        print("[ANALYSIS] ⚠️ No comments to analyze")
        return None

if __name__ == "__main__":
    result = run_patched_apu51()
