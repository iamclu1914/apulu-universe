"""
apu112_sentiment_agent.py — Real-time sentiment analysis for APU-112 engagement monitoring
Hip-hop artist social media sentiment analysis with cultural context awareness

Features:
- Real-time sentiment scoring of comments/mentions across 5 platforms
- Emotion detection beyond basic sentiment (hype, technical appreciation, etc.)
- Hip-hop culture and slang context awareness
- Integration with existing engagement monitoring system
- Batch processing for historical data analysis
- Performance optimization and cost management

Runs: Every 30 minutes via Windows Task Scheduler
Integration: Works with engagement_agent.py and analytics_agent.py
"""

import json
import sys
import requests
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import re

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from vawn_config import (
    get_anthropic_client, load_json, save_json, CREDS_FILE,
    RESEARCH_DIR, log_run, today_str, VAWN_PROFILE
)

# Import sentiment configuration
from config.apu112_sentiment_config import (
    get_sentiment_config, get_cost_optimization_config,
    SENTIMENT_CONFIG, FINE_TUNING_CONFIG
)

# Constants
BASE_URL = "https://apulustudio.onrender.com/api"
SENTIMENT_LOG = RESEARCH_DIR / "sentiment_analysis_log.json"
PERFORMANCE_LOG = RESEARCH_DIR / "sentiment_performance.json"
CULTURAL_CONTEXT_LOG = RESEARCH_DIR / "cultural_context_hits.json"
MAX_COMMENTS_PER_RUN = 50

@dataclass
class SentimentResult:
    """Structured sentiment analysis result"""
    text: str
    platform: str
    timestamp: str
    comment_id: str

    # Sentiment analysis
    sentiment: str  # positive, negative, neutral, excited, critical
    sentiment_confidence: float

    # Emotion detection
    emotions: List[Dict[str, float]]  # [{"hype": 0.8}, {"anticipation": 0.6}]

    # Context analysis
    music_related: bool
    hip_hop_context: bool
    artist_mention: bool
    slang_detected: List[str]
    cultural_context: Optional[str]

    # Engagement metrics
    engagement_value: float  # 0.0-1.0
    response_priority: int   # 1-5

    # Technical
    processing_time_ms: int
    model_version: str

class APU112SentimentEngine:
    """
    Core sentiment analysis engine optimized for hip-hop social media content
    """

    def __init__(self):
        self.config = get_sentiment_config()
        self.cost_config = get_cost_optimization_config()
        self.anthropic_client = get_anthropic_client()

        # Performance tracking
        self.stats = {
            "total_analyzed": 0,
            "avg_processing_time": 0.0,
            "cultural_hits": 0,
            "accuracy_estimates": [],
            "cost_per_analysis": 0.0
        }

        # Load performance history
        self.performance_history = self._load_performance_history()

    def analyze_comment(self, text: str, platform: str, comment_id: str = "", metadata: Dict = None) -> SentimentResult:
        """
        Analyze a single comment for comprehensive sentiment and cultural context

        Args:
            text: Comment text to analyze
            platform: Source platform
            comment_id: Unique identifier for the comment
            metadata: Additional context data

        Returns:
            SentimentResult with comprehensive analysis
        """
        start_time = time.time()

        try:
            # Check cache first for similar text
            cached_result = self._check_cache(text)
            if cached_result:
                return cached_result

            # Primary sentiment classification
            sentiment, confidence = self._classify_sentiment(text, platform)

            # Emotion detection
            emotions = self._detect_emotions(text)

            # Cultural and music context analysis
            music_related = self._is_music_related(text)
            hip_hop_context = self._has_hiphop_context(text)
            artist_mention = self._mentions_vawn(text)
            slang_detected = self._detect_slang(text)
            cultural_context = self._analyze_cultural_context(text)

            # Engagement value and priority calculation
            engagement_value = self._calculate_engagement_value(text, sentiment, emotions, platform)
            response_priority = self._calculate_response_priority(sentiment, emotions, engagement_value)

            # Create result
            processing_time = int((time.time() - start_time) * 1000)
            result = SentimentResult(
                text=text,
                platform=platform,
                timestamp=datetime.now().isoformat(),
                comment_id=comment_id,
                sentiment=sentiment,
                sentiment_confidence=confidence,
                emotions=emotions,
                music_related=music_related,
                hip_hop_context=hip_hop_context,
                artist_mention=artist_mention,
                slang_detected=slang_detected,
                cultural_context=cultural_context,
                engagement_value=engagement_value,
                response_priority=response_priority,
                processing_time_ms=processing_time,
                model_version=self.config["model"]["primary_model"]
            )

            # Update stats
            self._update_stats(result)

            # Cache result
            self._cache_result(text, result)

            return result

        except Exception as e:
            # Fallback to basic analysis
            return self._fallback_analysis(text, platform, comment_id, str(e))

    def batch_analyze(self, comments: List[Dict]) -> List[SentimentResult]:
        """
        Batch analyze multiple comments for efficiency

        Args:
            comments: List of comment dicts with keys: text, platform, id, metadata

        Returns:
            List of SentimentResult objects
        """
        print(f"[INFO] Starting batch analysis of {len(comments)} comments")

        results = []
        batch_start = time.time()

        # Process in optimal batch sizes
        batch_size = self.cost_config["model_efficiency"]["batch_optimization"]["min_batch_size"]

        for i in range(0, len(comments), batch_size):
            batch = comments[i:i + batch_size]
            print(f"[INFO] Processing batch {i//batch_size + 1}/{(len(comments)-1)//batch_size + 1}")

            batch_results = []
            for comment_data in batch:
                try:
                    result = self.analyze_comment(
                        text=comment_data.get('text', ''),
                        platform=comment_data.get('platform', 'unknown'),
                        comment_id=comment_data.get('id', ''),
                        metadata=comment_data.get('metadata', {})
                    )
                    batch_results.append(result)
                except Exception as e:
                    print(f"[WARN] Failed to analyze comment {comment_data.get('id', 'unknown')}: {e}")
                    continue

            results.extend(batch_results)

            # Brief pause between batches to manage API rate limits
            time.sleep(0.1)

        total_time = time.time() - batch_start
        print(f"[INFO] Batch analysis completed: {len(results)} results in {total_time:.2f}s")

        return results

    def _classify_sentiment(self, text: str, platform: str) -> Tuple[str, float]:
        """
        Classify sentiment using Claude with hip-hop context awareness
        """
        # Get platform-specific context
        platform_config = self.config["platforms"].get(platform, {})
        context_sensitivity = platform_config.get("context_sensitivity", "medium")
        slang_adaptation = platform_config.get("slang_adaptation", "general")

        # Build context-aware prompt
        prompt = self._build_sentiment_prompt(text, context_sensitivity, slang_adaptation)

        try:
            response = self.anthropic_client.messages.create(
                model="claude-haiku-20241001",  # Fast model for sentiment
                max_tokens=150,
                messages=[{"role": "user", "content": prompt}]
            )

            result = response.content[0].text.strip()
            return self._parse_sentiment_response(result)

        except Exception as e:
            print(f"[WARN] Claude API error for sentiment: {e}")
            return self._fallback_sentiment_analysis(text)

    def _build_sentiment_prompt(self, text: str, context_sensitivity: str, slang_adaptation: str) -> str:
        """Build context-aware sentiment analysis prompt"""

        base_prompt = f"""Analyze the sentiment of this social media comment about hip-hop artist Vawn.

VAWN CONTEXT:
{VAWN_PROFILE}

HIP-HOP CULTURAL CONTEXT:
- Positive slang: fire, heat, slaps, banger, goes hard, flames, vibes, fresh, cold, nasty
- Critical terms: mid, trash, weak, basic, played out
- Technical appreciation: production, mix, engineer, quality, sound
- Regional markers: Atlanta (trap, atl), Brooklyn (boom bap, bk)

COMMENT TO ANALYZE:
"{text}"

Respond with ONLY this format:
SENTIMENT: [positive/negative/neutral/excited/critical]
CONFIDENCE: [0.0-1.0]
REASONING: [brief explanation]"""

        # Adjust for platform context
        if context_sensitivity == "very_high":
            base_prompt += "\n\nNOTE: This is from TikTok - expect heavy Gen-Z slang and viral culture references."
        elif slang_adaptation == "visual_culture":
            base_prompt += "\n\nNOTE: This is from Instagram - context may include visual content references."

        return base_prompt

    def _parse_sentiment_response(self, response: str) -> Tuple[str, float]:
        """Parse Claude's sentiment analysis response"""
        try:
            lines = response.strip().split('\n')

            sentiment = "neutral"
            confidence = 0.5

            for line in lines:
                if line.startswith("SENTIMENT:"):
                    sentiment = line.split(":", 1)[1].strip().lower()
                elif line.startswith("CONFIDENCE:"):
                    confidence = float(line.split(":", 1)[1].strip())

            # Validate sentiment
            valid_sentiments = ["positive", "negative", "neutral", "excited", "critical"]
            if sentiment not in valid_sentiments:
                sentiment = "neutral"
                confidence = 0.5

            return sentiment, confidence

        except Exception as e:
            print(f"[WARN] Failed to parse sentiment response: {e}")
            return "neutral", 0.5

    def _detect_emotions(self, text: str) -> List[Dict[str, float]]:
        """
        Detect specific emotions relevant to hip-hop engagement
        """
        emotions = []
        text_lower = text.lower()

        emotion_config = self.config["emotion_mapping"]

        for emotion_type, config in emotion_config.items():
            base_confidence = 0.0

            # Check for indicators
            for indicator in config["indicators"]:
                if indicator in text_lower:
                    base_confidence += config["confidence_boost"]

            # Apply context boosts
            if base_confidence > 0:
                # Boost for detailed comments
                if len(text.split()) > 10:
                    base_confidence += 0.1

                # Boost for specific cultural markers
                if emotion_type == "hype" and any(term in text_lower for term in ["atlanta", "brooklyn", "real"]):
                    base_confidence += 0.1

                # Cap at 1.0
                base_confidence = min(1.0, base_confidence)

                if base_confidence >= 0.3:  # Minimum threshold
                    emotions.append({emotion_type: base_confidence})

        # Default emotion if none detected
        if not emotions:
            emotions.append({"general_appreciation": 0.5})

        return emotions

    def _is_music_related(self, text: str) -> bool:
        """Check if comment is music-related"""
        music_terms = [
            "track", "song", "beat", "album", "music", "sound", "audio", "mix",
            "production", "drop", "release", "freestyle", "bars", "flow", "lyrics",
            "melody", "harmony", "rhythm", "tempo", "vibe", "mood"
        ]
        return any(term in text.lower() for term in music_terms)

    def _has_hiphop_context(self, text: str) -> bool:
        """Check for hip-hop specific cultural context"""
        text_lower = text.lower()

        # Check all tiers of hip-hop lexicon
        lexicon = self.config["hip_hop_lexicon"]

        for category in lexicon.values():
            if isinstance(category, dict):
                for tier in category.values():
                    if any(term in text_lower for term in tier):
                        self.stats["cultural_hits"] += 1
                        return True
            elif isinstance(category, list):
                if any(term in text_lower for term in category):
                    self.stats["cultural_hits"] += 1
                    return True

        return False

    def _mentions_vawn(self, text: str) -> bool:
        """Check if text specifically mentions Vawn"""
        text_lower = text.lower()
        artist_mentions = self.config["vawn_context"]["artist_aliases"]

        return any(alias.lower() in text_lower for alias in artist_mentions)

    def _detect_slang(self, text: str) -> List[str]:
        """Detect and return specific slang terms used"""
        detected = []
        text_lower = text.lower()

        lexicon = self.config["hip_hop_lexicon"]

        for category in lexicon.values():
            if isinstance(category, dict):
                for tier in category.values():
                    for term in tier:
                        if term in text_lower and term not in detected:
                            detected.append(term)
            elif isinstance(category, list):
                for term in category:
                    if term in text_lower and term not in detected:
                        detected.append(term)

        return detected[:5]  # Limit to 5 most relevant terms

    def _analyze_cultural_context(self, text: str) -> Optional[str]:
        """Analyze regional/cultural context"""
        text_lower = text.lower()

        cultural_markers = self.config["hip_hop_lexicon"]["cultural_markers"]
        vawn_context = self.config["vawn_context"]["geographic_context"]

        # Check Vawn-specific geographic markers first
        for marker in vawn_context:
            if marker in text_lower:
                return f"vawn_{marker}"

        # Check general cultural markers
        for region, markers in cultural_markers.items():
            if any(marker in text_lower for marker in markers):
                return region

        return None

    def _calculate_engagement_value(self, text: str, sentiment: str, emotions: List[Dict], platform: str) -> float:
        """
        Calculate engagement value score (0.0-1.0)
        Higher scores indicate more valuable feedback for the artist
        """
        base_value = 0.3
        text_lower = text.lower()

        # Platform weight
        platform_weight = self.config["platforms"].get(platform, {}).get("weight", 1.0)
        base_value *= platform_weight

        # Length bonus for detailed feedback
        word_count = len(text.split())
        if word_count > 15:
            base_value += 0.2
        elif word_count > 8:
            base_value += 0.1

        # Technical feedback is highly valuable
        technical_terms = ["production", "mix", "master", "sound", "quality", "engineer", "studio"]
        if any(term in text_lower for term in technical_terms):
            base_value += 0.3

        # Emotion complexity adds value
        emotion_count = len(emotions)
        if emotion_count > 1:
            base_value += 0.1 * min(emotion_count, 3)  # Cap bonus

        # Cultural context awareness adds value
        if any(term in text_lower for term in ["atlanta", "brooklyn", "culture", "scene"]):
            base_value += 0.15

        # Fan loyalty indicators
        loyalty_terms = ["day one", "since", "always", "supporter", "fan", "following"]
        if any(term in text_lower for term in loyalty_terms):
            base_value += 0.1

        # Sharing/discovery intent
        sharing_terms = ["share", "playlist", "recommend", "friends", "everyone"]
        if any(term in text_lower for term in sharing_terms):
            base_value += 0.2

        # Constructive criticism is valuable
        if sentiment in ["critical", "negative"] and word_count > 10:
            base_value += 0.15

        # Reduce value for generic responses
        generic_terms = ["good", "nice", "cool", "ok", "alright"]
        if any(term == text_lower.strip() for term in generic_terms):
            base_value *= 0.5

        # Spam indicators reduce value
        spam_indicators = ["follow", "check out", "promo", "collab?", "dm me"]
        if any(spam in text_lower for spam in spam_indicators):
            base_value *= 0.2

        return min(1.0, base_value)

    def _calculate_response_priority(self, sentiment: str, emotions: List[Dict], engagement_value: float) -> int:
        """
        Calculate response priority (1-5, where 5 is highest priority)
        """
        priority = 2  # Default low-medium priority

        # High engagement value increases priority
        if engagement_value > 0.8:
            priority += 2
        elif engagement_value > 0.6:
            priority += 1

        # Negative sentiment needs attention
        if sentiment in ["negative", "critical"]:
            priority += 1

        # Technical feedback deserves quick response
        technical_emotions = ["technical_appreciation"]
        if any(emotion_dict for emotion_dict in emotions
               if any(key in technical_emotions for key in emotion_dict.keys())):
            priority += 1

        # Fan loyalty requires acknowledgment
        if any(emotion_dict for emotion_dict in emotions
               if any(key == "loyalty" for key in emotion_dict.keys())):
            priority += 1

        return min(5, max(1, priority))

    def _fallback_sentiment_analysis(self, text: str) -> Tuple[str, float]:
        """Simple fallback sentiment analysis"""
        text_lower = text.lower()

        # Simple keyword-based analysis
        positive_words = ["love", "amazing", "fire", "great", "awesome", "perfect", "incredible"]
        negative_words = ["hate", "terrible", "awful", "bad", "worst", "trash", "weak"]

        pos_score = sum(1 for word in positive_words if word in text_lower)
        neg_score = sum(1 for word in negative_words if word in text_lower)

        if pos_score > neg_score:
            return "positive", min(0.8, 0.5 + pos_score * 0.1)
        elif neg_score > pos_score:
            return "negative", min(0.8, 0.5 + neg_score * 0.1)
        else:
            return "neutral", 0.6

    def _fallback_analysis(self, text: str, platform: str, comment_id: str, error: str) -> SentimentResult:
        """Create fallback result when analysis fails"""
        sentiment, confidence = self._fallback_sentiment_analysis(text)

        return SentimentResult(
            text=text,
            platform=platform,
            timestamp=datetime.now().isoformat(),
            comment_id=comment_id,
            sentiment=sentiment,
            sentiment_confidence=confidence,
            emotions=[{"general": 0.5}],
            music_related=False,
            hip_hop_context=False,
            artist_mention=False,
            slang_detected=[],
            cultural_context=None,
            engagement_value=0.3,
            response_priority=2,
            processing_time_ms=50,
            model_version="fallback"
        )

    def _check_cache(self, text: str) -> Optional[SentimentResult]:
        """Check if similar text has been analyzed recently"""
        # Simple implementation - in production would use more sophisticated similarity
        cache_threshold = self.cost_config["model_efficiency"]["caching"]["similar_text_threshold"]
        # Placeholder for cache implementation
        return None

    def _cache_result(self, text: str, result: SentimentResult):
        """Cache analysis result for similar future queries"""
        # Placeholder for cache implementation
        pass

    def _update_stats(self, result: SentimentResult):
        """Update performance statistics"""
        self.stats["total_analyzed"] += 1

        # Update average processing time
        current_avg = self.stats["avg_processing_time"]
        new_time = result.processing_time_ms
        total = self.stats["total_analyzed"]
        self.stats["avg_processing_time"] = ((current_avg * (total - 1)) + new_time) / total

    def _load_performance_history(self) -> Dict:
        """Load historical performance data"""
        if PERFORMANCE_LOG.exists():
            return load_json(PERFORMANCE_LOG)
        return {"daily_stats": {}, "weekly_trends": {}}

    def get_performance_summary(self) -> Dict:
        """Get current performance statistics"""
        return {
            "current_session": self.stats,
            "targets": self.config["performance_metrics"],
            "cost_efficiency": self._calculate_cost_efficiency(),
            "cultural_context_rate": self.stats["cultural_hits"] / max(1, self.stats["total_analyzed"])
        }

    def _calculate_cost_efficiency(self) -> Dict:
        """Calculate cost efficiency metrics"""
        return {
            "avg_cost_per_analysis": self.stats["cost_per_analysis"],
            "total_cost_estimate": self.stats["total_analyzed"] * self.stats["cost_per_analysis"],
            "cost_target": "Under $0.01 per analysis",
            "efficiency_rating": "Good" if self.stats["cost_per_analysis"] < 0.01 else "Needs optimization"
        }

class SentimentAnalysisIntegration:
    """
    Integration layer for connecting sentiment analysis with existing systems
    """

    def __init__(self):
        self.engine = APU112SentimentEngine()
        self.sentiment_log = load_json(SENTIMENT_LOG) if SENTIMENT_LOG.exists() else {"analyses": [], "stats": {}}

    def refresh_token(self):
        """Refresh API token for platform integration"""
        creds = load_json(CREDS_FILE)
        r = requests.post(f"{BASE_URL}/auth/refresh", json={"refresh_token": creds["refresh_token"]})
        if r.status_code != 200:
            raise RuntimeError(f"Token refresh failed: {r.status_code}")
        data = r.json()
        creds["access_token"] = data["access_token"]
        creds["refresh_token"] = data["refresh_token"]
        save_json(CREDS_FILE, creds)
        return data["access_token"]

    def fetch_comments_for_analysis(self, access_token: str) -> List[Dict]:
        """Fetch comments from existing engagement system"""
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            # Get comments from engagement endpoint
            r = requests.get(f"{BASE_URL}/posts/comments", headers=headers, timeout=30)
            if r.status_code == 404:
                print("[INFO] Comments endpoint not available - using engagement log")
                return self._get_comments_from_engagement_log()

            r.raise_for_status()
            comments = r.json().get("comments", [])

            # Filter to unprocessed comments
            processed_ids = set(self.sentiment_log.get("processed_comment_ids", []))
            new_comments = [c for c in comments if c.get("id") not in processed_ids]

            return new_comments[:MAX_COMMENTS_PER_RUN]

        except requests.exceptions.RequestException as e:
            print(f"[WARN] Could not fetch comments from API: {e}")
            return self._get_comments_from_engagement_log()

    def _get_comments_from_engagement_log(self) -> List[Dict]:
        """Fallback to get comments from local engagement log"""
        engagement_log = load_json(RESEARCH_DIR / "engagement_log.json")

        comments = []
        for entry in engagement_log.get("history", [])[:MAX_COMMENTS_PER_RUN]:
            comments.append({
                "id": f"local_{hash(entry.get('comment', ''))}",
                "text": entry.get("comment", ""),
                "platform": entry.get("platform", "unknown"),
                "author": entry.get("author", "unknown"),
                "timestamp": entry.get("date", ""),
                "metadata": {
                    "engagement_type": entry.get("engagement_type", "comment"),
                    "post_context": entry.get("post_context", ""),
                    "collection_method": entry.get("collection_method", "local")
                }
            })

        return comments

    def process_comments(self) -> Dict:
        """Main processing function for sentiment analysis"""
        print("\n=== APU-112 Sentiment Analysis Agent ===\n")

        try:
            # Get authentication token
            access_token = self.refresh_token()
            print("[OK] Authentication successful")

            # Fetch comments for analysis
            comments = self.fetch_comments_for_analysis(access_token)

            if not comments:
                print("[INFO] No new comments to analyze")
                return {"status": "ok", "analyzed": 0, "message": "No new comments"}

            print(f"[INFO] Found {len(comments)} comments for analysis")

            # Perform batch sentiment analysis
            results = self.engine.batch_analyze(comments)

            # Process and store results
            self._store_results(results)

            # Generate insights summary
            insights = self._generate_insights(results)

            # Update integration with other systems
            self._update_engagement_system(results)

            print(f"[OK] Analyzed {len(results)} comments successfully")

            return {
                "status": "ok",
                "analyzed": len(results),
                "insights": insights,
                "performance": self.engine.get_performance_summary()
            }

        except Exception as e:
            error_msg = f"Sentiment analysis failed: {e}"
            print(f"[ERROR] {error_msg}")
            log_run("APU112SentimentAgent", "error", error_msg)
            return {"status": "error", "message": error_msg}

    def _store_results(self, results: List[SentimentResult]):
        """Store analysis results to sentiment log"""
        # Convert results to serializable format
        serializable_results = [asdict(result) for result in results]

        # Update main log
        if "analyses" not in self.sentiment_log:
            self.sentiment_log["analyses"] = []

        self.sentiment_log["analyses"].extend(serializable_results)

        # Keep only last 1000 analyses
        self.sentiment_log["analyses"] = self.sentiment_log["analyses"][-1000:]

        # Track processed comment IDs
        if "processed_comment_ids" not in self.sentiment_log:
            self.sentiment_log["processed_comment_ids"] = []

        new_ids = [r.comment_id for r in results if r.comment_id]
        self.sentiment_log["processed_comment_ids"].extend(new_ids)
        self.sentiment_log["processed_comment_ids"] = self.sentiment_log["processed_comment_ids"][-2000:]

        # Update statistics
        self.sentiment_log["stats"] = {
            "total_analyzed": len(self.sentiment_log["analyses"]),
            "last_update": datetime.now().isoformat(),
            "avg_engagement_value": sum(r.engagement_value for r in results) / len(results),
            "cultural_context_rate": len([r for r in results if r.cultural_context]) / len(results)
        }

        # Save to file
        save_json(SENTIMENT_LOG, self.sentiment_log)
        print(f"[OK] Stored {len(results)} sentiment analysis results")

    def _generate_insights(self, results: List[SentimentResult]) -> Dict:
        """Generate insights from analysis results"""
        if not results:
            return {}

        total = len(results)

        # Sentiment distribution
        sentiment_dist = Counter(r.sentiment for r in results)

        # Platform breakdown
        platform_dist = Counter(r.platform for r in results)

        # High-value insights
        high_value_comments = [r for r in results if r.engagement_value > 0.7]
        high_priority_comments = [r for r in results if r.response_priority >= 4]

        # Cultural context insights
        cultural_contexts = [r.cultural_context for r in results if r.cultural_context]
        cultural_dist = Counter(cultural_contexts)

        # Emotion trends
        all_emotions = []
        for r in results:
            for emotion_dict in r.emotions:
                all_emotions.extend(emotion_dict.keys())
        emotion_dist = Counter(all_emotions)

        return {
            "sentiment_distribution": dict(sentiment_dist),
            "platform_breakdown": dict(platform_dist),
            "high_value_count": len(high_value_comments),
            "high_priority_count": len(high_priority_comments),
            "cultural_context_distribution": dict(cultural_dist),
            "top_emotions": emotion_dist.most_common(5),
            "avg_engagement_value": sum(r.engagement_value for r in results) / total,
            "music_related_percentage": len([r for r in results if r.music_related]) / total * 100,
            "hip_hop_context_percentage": len([r for r in results if r.hip_hop_context]) / total * 100
        }

    def _update_engagement_system(self, results: List[SentimentResult]):
        """Update engagement system with sentiment insights"""
        # Find high-priority comments that need responses
        priority_comments = [r for r in results if r.response_priority >= 4]

        if priority_comments:
            priority_log = {
                "timestamp": datetime.now().isoformat(),
                "high_priority_comments": len(priority_comments),
                "details": [
                    {
                        "comment_id": r.comment_id,
                        "text": r.text[:100] + "..." if len(r.text) > 100 else r.text,
                        "platform": r.platform,
                        "sentiment": r.sentiment,
                        "priority": r.response_priority,
                        "engagement_value": r.engagement_value
                    }
                    for r in priority_comments[:10]  # Top 10
                ]
            }

            # Save priority alerts
            priority_file = RESEARCH_DIR / "sentiment_priority_alerts.json"
            priority_alerts = load_json(priority_file) if priority_file.exists() else {"alerts": []}
            priority_alerts["alerts"].append(priority_log)
            priority_alerts["alerts"] = priority_alerts["alerts"][-50:]  # Keep last 50
            save_json(priority_file, priority_alerts)

            print(f"[ALERT] {len(priority_comments)} high-priority comments need attention")


def main():
    """Main execution function"""
    integration = SentimentAnalysisIntegration()

    try:
        # Process comments and generate insights
        result = integration.process_comments()

        # Log results
        status = result["status"]
        analyzed_count = result.get("analyzed", 0)
        message = result.get("message", "")

        log_run("APU112SentimentAgent", status, f"Analyzed: {analyzed_count} comments. {message}")

        # Print summary
        if status == "ok" and analyzed_count > 0:
            insights = result.get("insights", {})
            performance = result.get("performance", {})

            print(f"\n=== Analysis Summary ===")
            print(f"Comments analyzed: {analyzed_count}")
            print(f"Sentiment distribution: {insights.get('sentiment_distribution', {})}")
            print(f"High-priority responses needed: {insights.get('high_priority_count', 0)}")
            print(f"Average engagement value: {insights.get('avg_engagement_value', 0):.2f}")
            print(f"Hip-hop context rate: {insights.get('hip_hop_context_percentage', 0):.1f}%")
            print(f"Cultural context hits: {performance.get('cultural_context_rate', 0):.2f}")

            print(f"\n=== Performance ===")
            current_stats = performance.get('current_session', {})
            print(f"Average processing time: {current_stats.get('avg_processing_time', 0):.0f}ms")
            print(f"Cultural hits: {current_stats.get('cultural_hits', 0)}")

    except Exception as e:
        print(f"[FATAL] Sentiment analysis failed: {e}")
        log_run("APU112SentimentAgent", "fatal", str(e))


if __name__ == "__main__":
    main()