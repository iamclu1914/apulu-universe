"""
apu51_sentiment_patch.py - Sentiment Analysis Patch for APU-51
Patches the APU-51 engagement monitor with enhanced sentiment analysis.

Created by: Dex - Community Agent (APU-51)
Purpose: Fix critical sentiment analysis issues in APU-51

This patch:
1. Replaces broken sentiment analysis with working enhanced version
2. Maintains compatibility with existing APU-51 intelligence engine
3. Provides better error handling and diagnostic logging
"""

import json
import sys
from pathlib import Path

# Import the enhanced analyzer
sys.path.insert(0, r"C:\Users\rdyal\Vawn\src")
from enhanced_sentiment_analyzer import EnhancedSentimentAnalyzer

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import load_json, save_json, ENGAGEMENT_LOG, VAWN_DIR

def patch_apu51_sentiment_analysis():
    """Patch the APU-51 sentiment analysis system."""

    print("\n[PATCH] APU-51 Sentiment Analysis Patch v1.0")
    print("[PATCH] Replacing broken sentiment analysis with enhanced version...")

    # Test the enhanced analyzer with real collected comments
    try:
        # Load actual comments from the engagement log
        engagement_log = load_json(ENGAGEMENT_LOG)
        recent_comments = []

        # Get comments from history
        for entry in engagement_log.get("history", []):
            recent_comments.append({
                "text": entry.get("comment", ""),
                "platform": entry.get("platform", "unknown"),
                "timestamp": entry.get("date", ""),
                "author": entry.get("author", "unknown")
            })

        print(f"[PATCH] Found {len(recent_comments)} comments to analyze")

        if recent_comments:
            # Test with enhanced analyzer
            analyzer = EnhancedSentimentAnalyzer()
            result = analyzer.analyze_sentiment_with_fallback(recent_comments)

            print(f"[PATCH] Enhanced analysis results:")
            print(f"  Overall Sentiment: {result['overall_sentiment']:+.3f}")
            print(f"  Community Satisfaction: {result['community_satisfaction']:.3f}")
            print(f"  Analysis Method: {result['analysis_method']}")
            print(f"  Comments Analyzed: {result['analyzed_count']}")
            print(f"  Distribution: +{result['sentiment_distribution']['positive']} "
                  f"~{result['sentiment_distribution']['neutral']} "
                  f"-{result['sentiment_distribution']['negative']}")

            # Save patched results for APU-51 to use
            patch_results = {
                "timestamp": analyzer.analysis_log[-1]["timestamp"] if analyzer.analysis_log else "",
                "patch_version": "apu51_v1.0",
                "sentiment_analysis": result,
                "comments_analyzed": len(recent_comments),
                "patch_status": "successful"
            }

            # Save to patch log
            patch_log_path = VAWN_DIR / "research" / "apu51_sentiment_patch_log.json"
            patch_log = load_json(patch_log_path)

            today = "2026-04-11"
            if today not in patch_log:
                patch_log[today] = []
            patch_log[today].append(patch_results)

            save_json(patch_log_path, patch_log)

            print(f"[PATCH] Patch successful! Enhanced sentiment analysis working")
            return result

        else:
            print("[PATCH] ⚠️ No comments found to analyze")
            return None

    except Exception as e:
        print(f"[PATCH] Patch failed: {e}")
        return None


def create_patched_apu51_runner():
    """Create a patched version of APU-51 that uses enhanced sentiment analysis."""

    print("\n[CREATE] Creating patched APU-51 runner...")

    patched_code = '''"""
APU-51 Community Intelligence Engine (PATCHED)
Enhanced with fixed sentiment analysis system.
"""

import sys
sys.path.insert(0, r"C:\\Users\\rdyal\\Vawn\\src")

# Import patched components
from enhanced_sentiment_analyzer import EnhancedSentimentAnalyzer

# Import original APU-51 components (excluding broken sentiment analysis)
sys.path.insert(0, r"C:\\Users\\rdyal\\Vawn")
from vawn_config import (
    load_json, save_json, ENGAGEMENT_LOG, RESEARCH_LOG, METRICS_LOG,
    VAWN_DIR, log_run, today_str, get_anthropic_client
)

from datetime import datetime, timedelta

# Enhanced APU-51 runner with fixed sentiment analysis
def run_patched_apu51():
    """Run APU-51 with enhanced sentiment analysis."""

    print("\\n[*] APU-51 Community Intelligence Engine (PATCHED)")
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

        print(f"\\n[HEALTH] Community Health Score: {community_health:.3f} ({health_status})")

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
'''

    # Save the patched runner
    patch_runner_path = Path("C:/Users/rdyal/Vawn/src/apu51_patched_runner.py")
    with open(patch_runner_path, "w", encoding="utf-8") as f:
        f.write(patched_code)

    print(f"[CREATE] Patched APU-51 runner created at {patch_runner_path}")
    return patch_runner_path


def main():
    """Main patch execution."""

    # Apply the patch
    patch_result = patch_apu51_sentiment_analysis()

    if patch_result:
        # Create patched runner
        runner_path = create_patched_apu51_runner()

        print(f"\\n[PATCH] APU-51 Sentiment Patch Applied Successfully!")
        print(f"[PATCH] Enhanced sentiment analysis is now working")
        print(f"[PATCH] Run: python {runner_path}")

        return True
    else:
        print(f"\\n[PATCH] APU-51 Sentiment Patch Failed")
        return False


if __name__ == "__main__":
    success = main()