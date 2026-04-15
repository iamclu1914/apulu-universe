"""
enhanced_sentiment_analyzer.py - APU-51 Enhanced Sentiment Analysis
Improved sentiment analysis with better error handling and fallback methods.

Created by: Dex - Community Agent (APU-51)
Purpose: Robust sentiment analysis system for community intelligence

Features:
- Enhanced Claude AI integration with better error handling
- Fallback sentiment analysis using pattern matching
- Diagnostic logging for troubleshooting
- Configurable analysis methods
"""

import json
import re
import statistics
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional

import sys
sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import get_anthropic_client, save_json, VAWN_DIR

# Configuration
SENTIMENT_LOG = VAWN_DIR / "research" / "enhanced_sentiment_log.json"

class EnhancedSentimentAnalyzer:
    """Enhanced sentiment analysis with fallbacks and diagnostics."""

    def __init__(self):
        self.claude_client = get_anthropic_client()
        self.analysis_log = []

    def analyze_sentiment_with_fallback(self, comments: List[Dict]) -> Dict[str, Any]:
        """Analyze sentiment with multiple fallback methods."""

        if not comments:
            return self._empty_sentiment_result()

        print(f"[SENTIMENT] Analyzing {len(comments)} comments...")

        # Primary method: Claude AI analysis
        primary_result = self._analyze_with_claude(comments)

        # Check if Claude analysis succeeded
        if primary_result["analyzed_count"] > 0 and primary_result["overall_sentiment"] != 0.0:
            print("[SENTIMENT] Claude AI analysis successful")
            return primary_result

        # Fallback method: Pattern-based analysis
        print("[SENTIMENT] Claude AI failed, using pattern-based fallback")
        fallback_result = self._analyze_with_patterns(comments)

        # Enhanced logging for diagnostics
        self._log_analysis_attempt(comments, primary_result, fallback_result)

        return fallback_result

    def _analyze_with_claude(self, comments: List[Dict]) -> Dict[str, Any]:
        """Primary analysis method using Claude AI."""

        sentiment_scores = []
        emotional_themes = []
        satisfaction_indicators = []

        # Process comments in smaller batches
        batch_size = 10  # Reduced from 50 for better success rate

        for i in range(0, len(comments), batch_size):
            batch = comments[i:i + batch_size]

            try:
                batch_result = self._analyze_batch_with_claude(batch)

                if batch_result["success"]:
                    sentiment_scores.extend(batch_result["sentiment_scores"])
                    emotional_themes.extend(batch_result["emotional_themes"])
                    satisfaction_indicators.extend(batch_result["satisfaction_indicators"])
                else:
                    # Log the specific failure
                    print(f"[SENTIMENT] Batch {i//batch_size + 1} failed: {batch_result.get('error', 'Unknown error')}")
                    # Add neutral scores for failed batch
                    sentiment_scores.extend([0.0] * len(batch))
                    satisfaction_indicators.extend([0.5] * len(batch))

            except Exception as e:
                print(f"[SENTIMENT] Exception in batch {i//batch_size + 1}: {e}")
                sentiment_scores.extend([0.0] * len(batch))
                satisfaction_indicators.extend([0.5] * len(batch))

        return self._compile_sentiment_result(sentiment_scores, emotional_themes, satisfaction_indicators, "claude_ai")

    def _analyze_batch_with_claude(self, batch: List[Dict]) -> Dict[str, Any]:
        """Analyze a single batch with Claude AI."""

        batch_text = "\n".join([
            f"Comment {i+1} ({comment.get('platform', 'unknown')}): {comment.get('text', comment.get('comment', ''))}"
            for i, comment in enumerate(batch)
        ])

        prompt = f"""Analyze the sentiment in these community comments about Vawn's music.

Comments:
{batch_text}

Please provide:
1. SENTIMENT_SCORES: A list of numbers from -1.0 (very negative) to +1.0 (very positive) for each comment
2. EMOTIONAL_THEMES: Key emotional themes you detect (excitement, appreciation, criticism, etc.)
3. SATISFACTION_SCORES: Numbers from 0.0 to 1.0 indicating satisfaction with Vawn's content

Format your response EXACTLY like this:
SENTIMENT_SCORES: [0.8, 0.6, -0.2, 0.9]
EMOTIONAL_THEMES: [excitement, appreciation, curiosity]
SATISFACTION_SCORES: [0.9, 0.7, 0.4, 0.8]

Only include the scores and themes, no additional text."""

        try:
            response = self.claude_client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )

            analysis = response.content[0].text
            print(f"[CLAUDE] Raw response: {analysis[:200]}...")  # Debug logging

            # Parse the response
            sentiment_scores = self._extract_scores(analysis, "SENTIMENT_SCORES:", len(batch))
            emotional_themes = self._extract_themes(analysis, "EMOTIONAL_THEMES:")
            satisfaction_scores = self._extract_scores(analysis, "SATISFACTION_SCORES:", len(batch))

            return {
                "success": True,
                "sentiment_scores": sentiment_scores,
                "emotional_themes": emotional_themes,
                "satisfaction_indicators": satisfaction_scores
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "sentiment_scores": [],
                "emotional_themes": [],
                "satisfaction_indicators": []
            }

    def _extract_scores(self, text: str, marker: str, expected_count: int) -> List[float]:
        """Extract numerical scores from Claude's response."""

        try:
            if marker in text:
                line = text.split(marker)[1].split("\n")[0]
                # Extract numbers with regex
                numbers = re.findall(r'-?[01]?\.\d+|-?[01]', line)
                scores = [max(-1.0, min(1.0, float(num))) for num in numbers[:expected_count]]

                # Pad with neutral scores if needed
                while len(scores) < expected_count:
                    scores.append(0.0)

                print(f"[PARSE] Extracted {len(scores)} scores: {scores}")  # Debug
                return scores[:expected_count]
            else:
                print(f"[PARSE] Marker '{marker}' not found in response")
                return [0.0] * expected_count
        except Exception as e:
            print(f"[PARSE] Error extracting scores: {e}")
            return [0.0] * expected_count

    def _extract_themes(self, text: str, marker: str) -> List[str]:
        """Extract emotional themes from Claude's response."""

        try:
            if marker in text:
                line = text.split(marker)[1].split("\n")[0]
                # Clean and extract themes
                themes = line.replace('[', '').replace(']', '').replace('"', '')
                theme_list = [theme.strip().lower() for theme in themes.split(',')]
                return [theme for theme in theme_list if theme and len(theme) > 2]
            else:
                return []
        except:
            return []

    def _analyze_with_patterns(self, comments: List[Dict]) -> Dict[str, Any]:
        """Fallback sentiment analysis using pattern matching."""

        positive_patterns = [
            r'\b(love|amazing|incredible|awesome|perfect|great|fantastic|excellent)\b',
            r'\b(fire|🔥|💯|hits different|unmatched|fresh)\b',
            r'\b(waiting for|been following|day one|hooked)\b'
        ]

        negative_patterns = [
            r'\b(hate|terrible|awful|bad|disappointing|worst)\b',
            r'\b(not sure|preferred earlier|disappointed)\b'
        ]

        neutral_patterns = [
            r'\b(okay|fine|decent|alright|not bad)\b'
        ]

        sentiment_scores = []
        emotional_themes = []

        for comment in comments:
            text = comment.get('text', comment.get('comment', '')).lower()

            positive_score = sum(len(re.findall(pattern, text)) for pattern in positive_patterns)
            negative_score = sum(len(re.findall(pattern, text)) for pattern in negative_patterns)
            neutral_score = sum(len(re.findall(pattern, text)) for pattern in neutral_patterns)

            # Calculate sentiment based on pattern matches
            if positive_score > negative_score:
                sentiment = min(0.8, 0.3 + (positive_score * 0.2))
                themes = ["positive_engagement"]
            elif negative_score > positive_score:
                sentiment = max(-0.8, -0.3 - (negative_score * 0.2))
                themes = ["constructive_feedback"]
            else:
                sentiment = 0.0
                themes = ["neutral_observation"]

            sentiment_scores.append(sentiment)
            emotional_themes.extend(themes)

        satisfaction_scores = [0.6 + (score * 0.3) for score in sentiment_scores]

        return self._compile_sentiment_result(sentiment_scores, emotional_themes, satisfaction_scores, "pattern_matching")

    def _compile_sentiment_result(self, sentiment_scores: List[float], emotional_themes: List[str],
                                satisfaction_indicators: List[float], method: str) -> Dict[str, Any]:
        """Compile final sentiment analysis result."""

        if not sentiment_scores:
            return self._empty_sentiment_result()

        overall_sentiment = statistics.mean(sentiment_scores)
        community_satisfaction = statistics.mean(satisfaction_indicators)

        # Categorize sentiment distribution
        positive_count = len([s for s in sentiment_scores if s > 0.3])
        negative_count = len([s for s in sentiment_scores if s < -0.3])
        neutral_count = len(sentiment_scores) - positive_count - negative_count

        return {
            "overall_sentiment": round(overall_sentiment, 3),
            "sentiment_distribution": {
                "positive": positive_count,
                "neutral": neutral_count,
                "negative": negative_count
            },
            "emotional_themes": list(set(emotional_themes))[:10],
            "community_satisfaction": round(community_satisfaction, 3),
            "analyzed_count": len(sentiment_scores),
            "analysis_method": method,
            "sentiment_trend": self._calculate_trend(sentiment_scores),
            "satisfaction_trend": self._calculate_trend(satisfaction_indicators)
        }

    def _empty_sentiment_result(self) -> Dict[str, Any]:
        """Return empty sentiment result structure."""
        return {
            "overall_sentiment": 0.0,
            "sentiment_distribution": {"positive": 0, "neutral": 0, "negative": 0},
            "emotional_themes": [],
            "community_satisfaction": 0.0,
            "analyzed_count": 0,
            "analysis_method": "none",
            "sentiment_trend": "unknown",
            "satisfaction_trend": "unknown"
        }

    def _calculate_trend(self, scores: List[float]) -> str:
        """Calculate trend direction from scores."""
        if not scores or len(scores) < 2:
            return "unknown"

        # Compare first half to second half
        mid = len(scores) // 2
        first_half_avg = statistics.mean(scores[:mid]) if mid > 0 else 0
        second_half_avg = statistics.mean(scores[mid:]) if mid < len(scores) else 0

        diff = second_half_avg - first_half_avg

        if diff > 0.15:
            return "improving"
        elif diff < -0.15:
            return "declining"
        else:
            return "stable"

    def _log_analysis_attempt(self, comments: List[Dict], primary_result: Dict, fallback_result: Dict):
        """Log analysis attempts for diagnostics."""

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "comment_count": len(comments),
            "primary_method": "claude_ai",
            "primary_success": primary_result["analyzed_count"] > 0,
            "fallback_method": "pattern_matching",
            "final_sentiment": fallback_result["overall_sentiment"],
            "final_method": fallback_result["analysis_method"]
        }

        self.analysis_log.append(log_entry)

        # Save diagnostic log
        try:
            log_data = {"analysis_attempts": self.analysis_log}
            save_json(SENTIMENT_LOG, log_data)
        except:
            pass  # Don't fail on logging errors


def test_enhanced_analyzer():
    """Test the enhanced sentiment analyzer."""

    # Sample test comments
    test_comments = [
        {"text": "Love this new track! The beat is incredible 🔥", "platform": "instagram"},
        {"text": "Not sure about this direction... preferred the earlier style", "platform": "bluesky"},
        {"text": "Vawn's flow on this is unmatched. Been waiting for this drop", "platform": "x"}
    ]

    analyzer = EnhancedSentimentAnalyzer()
    result = analyzer.analyze_sentiment_with_fallback(test_comments)

    print("\n[TEST] Enhanced Sentiment Analysis Results:")
    print(f"Overall Sentiment: {result['overall_sentiment']:+.3f}")
    print(f"Community Satisfaction: {result['community_satisfaction']:.3f}")
    print(f"Analysis Method: {result['analysis_method']}")
    print(f"Distribution: +{result['sentiment_distribution']['positive']} "
          f"~{result['sentiment_distribution']['neutral']} "
          f"-{result['sentiment_distribution']['negative']}")
    print(f"Emotional Themes: {result['emotional_themes']}")

    return result


if __name__ == "__main__":
    test_enhanced_analyzer()