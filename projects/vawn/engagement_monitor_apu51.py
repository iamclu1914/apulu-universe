"""
engagement_monitor_apu51.py - Community Intelligence Engine for APU-51.
Advanced community analytics, sentiment tracking, and predictive insights.
Created by: Dex - Community Agent (APU-51)

Features:
- Real-time community sentiment analysis
- Cross-platform engagement correlation
- Community health scoring system
- Predictive community analytics
- Automated community strategy recommendations
- Real-time community intelligence dashboard

Builds on APU-37 monitoring infrastructure with community-focused intelligence layers.
"""

import json
import sys
import statistics
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import (
    load_json, save_json, ENGAGEMENT_LOG, RESEARCH_LOG, METRICS_LOG,
    VAWN_DIR, log_run, today_str, get_anthropic_client
)

# Configuration
COMMUNITY_INTELLIGENCE_LOG = VAWN_DIR / "research" / "community_intelligence_apu51_log.json"
SENTIMENT_LOG = VAWN_DIR / "research" / "community_sentiment_log.json"
COMMUNITY_HEALTH_LOG = VAWN_DIR / "research" / "community_health_log.json"
PREDICTIONS_LOG = VAWN_DIR / "research" / "community_predictions_log.json"

BASE_URL = "https://apulustudio.onrender.com/api"
PLATFORMS = ["instagram", "tiktok", "x", "threads", "bluesky"]

# Community Intelligence Configuration
SENTIMENT_ANALYSIS_CONFIG = {
    "batch_size": 50,
    "lookback_days": 7,
    "sentiment_threshold_negative": -0.3,
    "sentiment_threshold_positive": 0.3,
    "trend_significance_threshold": 0.15
}

COMMUNITY_HEALTH_THRESHOLDS = {
    "excellent": 0.85,
    "good": 0.70,
    "fair": 0.55,
    "poor": 0.40,
    "critical": 0.25
}

ALERT_THRESHOLDS = {
    "sentiment_drop": -0.2,
    "engagement_drop": 0.3,
    "response_time_increase": 2.0,
    "community_health_drop": 0.15
}


class CommunityIntelligenceEngine:
    """Advanced community analytics and intelligence engine."""

    def __init__(self):
        self.claude_client = get_anthropic_client()
        self.community_data = {
            "sentiment_history": [],
            "engagement_patterns": {},
            "community_health_scores": [],
            "predictions": {},
            "recommendations": []
        }

    def analyze_comment_sentiment(self, comments: List[Dict]) -> Dict[str, Any]:
        """Analyze sentiment of community comments using Claude AI."""
        if not comments:
            return {
                "overall_sentiment": 0.0,
                "sentiment_distribution": {"positive": 0, "neutral": 0, "negative": 0},
                "emotional_themes": [],
                "community_satisfaction": 0.0,
                "analyzed_count": 0
            }

        # Batch comments for analysis
        batch_size = SENTIMENT_ANALYSIS_CONFIG["batch_size"]
        sentiment_scores = []
        emotional_themes = []
        satisfaction_indicators = []

        for i in range(0, len(comments), batch_size):
            batch = comments[i:i + batch_size]
            batch_text = "\n".join([f"Comment {j+1}: {comment.get('text', '')}"
                                   for j, comment in enumerate(batch)])

            prompt = f"""Analyze the sentiment and emotional themes in these community comments about Vawn's music content.

Comments to analyze:
{batch_text[:3000]}

Provide analysis in this format:
SENTIMENT_SCORES: [List of numerical scores from -1.0 (very negative) to +1.0 (very positive) for each comment]
EMOTIONAL_THEMES: [List of emotional themes like "excitement", "appreciation", "curiosity", "frustration", etc.]
SATISFACTION_INDICATORS: [List of numerical scores from 0.0 to 1.0 indicating community satisfaction with Vawn's content/responses]

Focus on:
- Genuine emotional response to music content
- Community satisfaction with engagement quality
- Overall community mood and energy
- Constructive vs superficial feedback"""

            try:
                response = self.claude_client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}]
                )

                analysis = response.content[0].text

                # Parse sentiment scores
                if "SENTIMENT_SCORES:" in analysis:
                    scores_line = analysis.split("SENTIMENT_SCORES:")[1].split("\n")[0]
                    batch_scores = self._parse_scores(scores_line, len(batch))
                    sentiment_scores.extend(batch_scores)

                # Parse emotional themes
                if "EMOTIONAL_THEMES:" in analysis:
                    themes_line = analysis.split("EMOTIONAL_THEMES:")[1].split("\n")[0]
                    themes = self._parse_themes(themes_line)
                    emotional_themes.extend(themes)

                # Parse satisfaction indicators
                if "SATISFACTION_INDICATORS:" in analysis:
                    satisfaction_line = analysis.split("SATISFACTION_INDICATORS:")[1].split("\n")[0]
                    batch_satisfaction = self._parse_scores(satisfaction_line, len(batch))
                    satisfaction_indicators.extend(batch_satisfaction)

            except Exception as e:
                print(f"[WARN] Sentiment analysis failed for batch: {e}")
                # Fallback to neutral scores
                sentiment_scores.extend([0.0] * len(batch))
                satisfaction_indicators.extend([0.5] * len(batch))

        # Calculate overall metrics
        overall_sentiment = statistics.mean(sentiment_scores) if sentiment_scores else 0.0
        community_satisfaction = statistics.mean(satisfaction_indicators) if satisfaction_indicators else 0.5

        # Categorize sentiment distribution
        positive_count = len([s for s in sentiment_scores if s > SENTIMENT_ANALYSIS_CONFIG["sentiment_threshold_positive"]])
        negative_count = len([s for s in sentiment_scores if s < SENTIMENT_ANALYSIS_CONFIG["sentiment_threshold_negative"]])
        neutral_count = len(sentiment_scores) - positive_count - negative_count

        return {
            "overall_sentiment": round(overall_sentiment, 3),
            "sentiment_distribution": {
                "positive": positive_count,
                "neutral": neutral_count,
                "negative": negative_count
            },
            "emotional_themes": list(set(emotional_themes))[:10],  # Top 10 unique themes
            "community_satisfaction": round(community_satisfaction, 3),
            "analyzed_count": len(sentiment_scores),
            "sentiment_trend": self._calculate_sentiment_trend(sentiment_scores),
            "satisfaction_trend": self._calculate_satisfaction_trend(satisfaction_indicators)
        }

    def _parse_scores(self, scores_text: str, expected_count: int) -> List[float]:
        """Parse numerical scores from analysis text."""
        try:
            # Extract numbers between -1.0 and 1.0
            import re
            numbers = re.findall(r'-?[01]?\.\d+|-?[01]', scores_text)
            scores = [max(-1.0, min(1.0, float(num))) for num in numbers[:expected_count]]

            # Pad with neutral if needed
            while len(scores) < expected_count:
                scores.append(0.0)

            return scores[:expected_count]
        except:
            return [0.0] * expected_count

    def _parse_themes(self, themes_text: str) -> List[str]:
        """Parse emotional themes from analysis text."""
        try:
            # Clean and extract themes
            themes = themes_text.replace('[', '').replace(']', '').replace('"', '')
            theme_list = [theme.strip().lower() for theme in themes.split(',')]
            return [theme for theme in theme_list if theme and len(theme) > 2]
        except:
            return []

    def _calculate_sentiment_trend(self, scores: List[float]) -> str:
        """Calculate sentiment trend direction."""
        if len(scores) < 10:
            return "insufficient_data"

        # Compare first and last thirds
        first_third = statistics.mean(scores[:len(scores)//3])
        last_third = statistics.mean(scores[-len(scores)//3:])

        diff = last_third - first_third
        if diff > SENTIMENT_ANALYSIS_CONFIG["trend_significance_threshold"]:
            return "improving"
        elif diff < -SENTIMENT_ANALYSIS_CONFIG["trend_significance_threshold"]:
            return "declining"
        else:
            return "stable"

    def _calculate_satisfaction_trend(self, scores: List[float]) -> str:
        """Calculate satisfaction trend direction."""
        if len(scores) < 10:
            return "insufficient_data"

        first_half = statistics.mean(scores[:len(scores)//2])
        second_half = statistics.mean(scores[len(scores)//2:])

        diff = second_half - first_half
        if diff > 0.1:
            return "improving"
        elif diff < -0.1:
            return "declining"
        else:
            return "stable"

    def analyze_cross_platform_correlation(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze engagement patterns and correlations across platforms."""
        platform_stats = metrics.get("platform_stats", {})

        correlations = {
            "platform_performance": {},
            "engagement_efficiency": {},
            "content_effectiveness": {},
            "timing_insights": {},
            "cross_platform_trends": {}
        }

        # Calculate platform performance metrics
        total_engagement = 0
        total_posts = 0

        for platform, stats in platform_stats.items():
            eng_rate = stats.get("engagement_rate", 0)
            posts = stats.get("posts", 0)

            correlations["platform_performance"][platform] = {
                "engagement_rate": eng_rate,
                "posts_count": posts,
                "avg_engagement": stats.get("avg_engagement", 0),
                "performance_score": self._calculate_performance_score(stats)
            }

            total_engagement += stats.get("total_likes", 0) + stats.get("total_comments", 0)
            total_posts += posts

        # Calculate cross-platform insights
        if platform_stats:
            platforms = list(platform_stats.keys())
            performance_scores = [correlations["platform_performance"][p]["performance_score"]
                                for p in platforms]

            correlations["cross_platform_trends"] = {
                "top_performer": max(platforms, key=lambda p: correlations["platform_performance"][p]["performance_score"]) if platforms else None,
                "average_performance": statistics.mean(performance_scores) if performance_scores else 0,
                "performance_variance": statistics.stdev(performance_scores) if len(performance_scores) > 1 else 0,
                "total_reach_estimate": self._estimate_total_reach(platform_stats),
                "platform_diversity_score": self._calculate_diversity_score(platform_stats)
            }

        return correlations

    def _calculate_performance_score(self, stats: Dict) -> float:
        """Calculate comprehensive performance score for a platform."""
        engagement = stats.get("avg_engagement", 0)
        posts = stats.get("posts", 0)
        api_available = stats.get("api_available", True)

        # Base score from engagement
        base_score = min(1.0, engagement / 10.0)  # Normalize to 0-1

        # Penalty for low post count
        post_penalty = 1.0 if posts >= 5 else posts / 5.0

        # Penalty for API unavailability
        api_penalty = 1.0 if api_available else 0.7

        return base_score * post_penalty * api_penalty

    def _estimate_total_reach(self, platform_stats: Dict) -> int:
        """Estimate total community reach across platforms."""
        # Simplified reach estimation based on engagement patterns
        reach_multipliers = {
            "instagram": 20,  # Assume 20x reach from engagement
            "tiktok": 50,     # Higher viral potential
            "x": 15,          # Lower organic reach
            "threads": 25,    # Growing platform
            "bluesky": 10     # Smaller but engaged community
        }

        total_reach = 0
        for platform, stats in platform_stats.items():
            multiplier = reach_multipliers.get(platform, 15)
            engagement = stats.get("total_likes", 0) + stats.get("total_comments", 0)
            total_reach += engagement * multiplier

        return total_reach

    def _calculate_diversity_score(self, platform_stats: Dict) -> float:
        """Calculate platform engagement diversity score."""
        if len(platform_stats) < 2:
            return 0.0

        engagement_rates = [stats.get("engagement_rate", 0) for stats in platform_stats.values()]
        avg_rate = statistics.mean(engagement_rates)

        if avg_rate == 0:
            return 0.0

        # Higher diversity = lower variance relative to mean
        variance = statistics.variance(engagement_rates) if len(engagement_rates) > 1 else 0
        diversity = 1.0 - (variance / (avg_rate + 1))  # Add 1 to prevent division by zero

        return max(0.0, min(1.0, diversity))

    def calculate_community_health_score(self, sentiment_data: Dict, correlations: Dict,
                                       agent_health: Dict) -> Dict[str, Any]:
        """Calculate comprehensive community health score."""

        # Sentiment health (40% weight)
        sentiment_score = self._score_sentiment_health(sentiment_data)

        # Engagement health (30% weight)
        engagement_score = self._score_engagement_health(correlations)

        # Response health (20% weight)
        response_score = self._score_response_health(agent_health)

        # Growth health (10% weight)
        growth_score = self._score_growth_health(correlations)

        # Calculate weighted overall score
        overall_score = (
            sentiment_score * 0.4 +
            engagement_score * 0.3 +
            response_score * 0.2 +
            growth_score * 0.1
        )

        # Determine health status
        health_status = "critical"
        for status, threshold in sorted(COMMUNITY_HEALTH_THRESHOLDS.items(),
                                      key=lambda x: x[1], reverse=True):
            if overall_score >= threshold:
                health_status = status
                break

        return {
            "overall_score": round(overall_score, 3),
            "health_status": health_status,
            "component_scores": {
                "sentiment": round(sentiment_score, 3),
                "engagement": round(engagement_score, 3),
                "response": round(response_score, 3),
                "growth": round(growth_score, 3)
            },
            "strengths": self._identify_strengths(sentiment_score, engagement_score, response_score, growth_score),
            "improvement_areas": self._identify_improvement_areas(sentiment_score, engagement_score, response_score, growth_score),
            "timestamp": datetime.now().isoformat()
        }

    def _score_sentiment_health(self, sentiment_data: Dict) -> float:
        """Score community sentiment health."""
        sentiment = sentiment_data.get("overall_sentiment", 0)
        satisfaction = sentiment_data.get("community_satisfaction", 0.5)

        # Convert sentiment (-1 to 1) to score (0 to 1)
        sentiment_score = (sentiment + 1) / 2

        # Weight satisfaction higher for community health
        combined_score = (sentiment_score * 0.4) + (satisfaction * 0.6)

        return max(0.0, min(1.0, combined_score))

    def _score_engagement_health(self, correlations: Dict) -> float:
        """Score engagement pattern health."""
        cross_platform = correlations.get("cross_platform_trends", {})
        avg_performance = cross_platform.get("average_performance", 0)
        diversity_score = cross_platform.get("platform_diversity_score", 0)

        # Combine average performance and diversity
        engagement_score = (avg_performance * 0.7) + (diversity_score * 0.3)

        return max(0.0, min(1.0, engagement_score))

    def _score_response_health(self, agent_health: Dict) -> float:
        """Score response system health."""
        healthy_agents = 0
        total_agents = len(agent_health)

        if total_agents == 0:
            return 0.0

        for agent, health in agent_health.items():
            if health.get("status") in ["healthy", "idle", "recovered"]:
                healthy_agents += 1

        return healthy_agents / total_agents

    def _score_growth_health(self, correlations: Dict) -> float:
        """Score community growth health."""
        # Simplified growth scoring based on platform performance trends
        cross_platform = correlations.get("cross_platform_trends", {})
        avg_performance = cross_platform.get("average_performance", 0)

        # Growth score based on engagement trends
        # This could be enhanced with historical comparison
        growth_score = min(1.0, avg_performance * 1.2)

        return max(0.0, growth_score)

    def _identify_strengths(self, sentiment: float, engagement: float, response: float, growth: float) -> List[str]:
        """Identify community health strengths."""
        strengths = []

        if sentiment > 0.8:
            strengths.append("Excellent community sentiment")
        if engagement > 0.75:
            strengths.append("Strong cross-platform engagement")
        if response > 0.9:
            strengths.append("Reliable response system")
        if growth > 0.7:
            strengths.append("Positive growth indicators")

        return strengths

    def _identify_improvement_areas(self, sentiment: float, engagement: float, response: float, growth: float) -> List[str]:
        """Identify areas needing improvement."""
        improvements = []

        if sentiment < 0.6:
            improvements.append("Community sentiment needs attention")
        if engagement < 0.5:
            improvements.append("Engagement patterns could be optimized")
        if response < 0.7:
            improvements.append("Response system reliability")
        if growth < 0.5:
            improvements.append("Community growth strategy needed")

        return improvements

    def generate_predictive_insights(self, historical_data: Dict) -> Dict[str, Any]:
        """Generate predictive insights for community trends."""

        predictions = {
            "sentiment_forecast": self._predict_sentiment_trends(historical_data),
            "engagement_forecast": self._predict_engagement_trends(historical_data),
            "community_growth_projection": self._predict_growth_trends(historical_data),
            "risk_indicators": self._identify_risk_indicators(historical_data),
            "opportunities": self._identify_opportunities(historical_data),
            "forecast_confidence": 0.0,
            "generated_at": datetime.now().isoformat()
        }

        # Calculate overall forecast confidence
        predictions["forecast_confidence"] = self._calculate_forecast_confidence(historical_data)

        return predictions

    def _predict_sentiment_trends(self, data: Dict) -> Dict[str, Any]:
        """Predict community sentiment trends."""
        # Simplified trend prediction - in production would use more sophisticated models
        recent_sentiment = data.get("recent_sentiment_avg", 0.0)
        sentiment_volatility = data.get("sentiment_volatility", 0.0)

        # Basic trend projection
        if recent_sentiment > 0.3 and sentiment_volatility < 0.2:
            trend = "stable_positive"
            confidence = 0.7
        elif recent_sentiment < -0.2:
            trend = "declining"
            confidence = 0.6
        else:
            trend = "neutral"
            confidence = 0.5

        return {
            "predicted_trend": trend,
            "confidence": confidence,
            "recommendation": self._get_sentiment_recommendation(trend)
        }

    def _predict_engagement_trends(self, data: Dict) -> Dict[str, Any]:
        """Predict engagement pattern trends."""
        avg_engagement = data.get("avg_engagement_rate", 0.0)
        engagement_growth = data.get("engagement_growth", 0.0)

        if engagement_growth > 0.1:
            trend = "growing"
            confidence = 0.6
        elif engagement_growth < -0.15:
            trend = "declining"
            confidence = 0.7
        else:
            trend = "stable"
            confidence = 0.5

        return {
            "predicted_trend": trend,
            "confidence": confidence,
            "recommendation": self._get_engagement_recommendation(trend)
        }

    def _predict_growth_trends(self, data: Dict) -> Dict[str, Any]:
        """Predict community growth trends."""
        # Simplified growth prediction
        community_health = data.get("avg_community_health", 0.5)

        if community_health > 0.7:
            growth_projection = "positive"
            confidence = 0.6
        elif community_health < 0.4:
            growth_projection = "at_risk"
            confidence = 0.8
        else:
            growth_projection = "stable"
            confidence = 0.5

        return {
            "projected_growth": growth_projection,
            "confidence": confidence,
            "recommendation": self._get_growth_recommendation(growth_projection)
        }

    def _identify_risk_indicators(self, data: Dict) -> List[Dict[str, str]]:
        """Identify potential risks to community health."""
        risks = []

        if data.get("recent_sentiment_avg", 0) < -0.2:
            risks.append({
                "type": "sentiment_risk",
                "severity": "high",
                "description": "Declining community sentiment detected",
                "recommended_action": "Review content strategy and increase positive engagement"
            })

        if data.get("response_rate", 1.0) < 0.3:
            risks.append({
                "type": "engagement_risk",
                "severity": "medium",
                "description": "Low response rate to community comments",
                "recommended_action": "Increase response frequency and quality"
            })

        return risks

    def _identify_opportunities(self, data: Dict) -> List[Dict[str, str]]:
        """Identify growth opportunities."""
        opportunities = []

        if data.get("platform_diversity", 0) < 0.5:
            opportunities.append({
                "type": "platform_expansion",
                "potential": "medium",
                "description": "Opportunity to diversify platform engagement",
                "recommended_action": "Focus on underperforming platforms"
            })

        if data.get("engagement_quality", 0.5) > 0.7:
            opportunities.append({
                "type": "community_advocacy",
                "potential": "high",
                "description": "Strong engagement quality indicates advocate potential",
                "recommended_action": "Identify and nurture community advocates"
            })

        return opportunities

    def _calculate_forecast_confidence(self, data: Dict) -> float:
        """Calculate overall confidence in predictions."""
        # Base confidence on data quality and completeness
        data_points = len([k for k, v in data.items() if v is not None])
        data_quality = min(1.0, data_points / 10.0)  # Expect ~10 key metrics

        # Reduce confidence for volatile data
        volatility_penalty = data.get("sentiment_volatility", 0) * 0.5

        confidence = max(0.1, data_quality - volatility_penalty)
        return round(confidence, 2)

    def _get_sentiment_recommendation(self, trend: str) -> str:
        """Get recommendation based on sentiment trend."""
        recommendations = {
            "declining": "Increase positive engagement, review content strategy",
            "stable_positive": "Maintain current engagement approach",
            "neutral": "Focus on building stronger emotional connections"
        }
        return recommendations.get(trend, "Monitor sentiment closely")

    def _get_engagement_recommendation(self, trend: str) -> str:
        """Get recommendation based on engagement trend."""
        recommendations = {
            "growing": "Capitalize on momentum with consistent content",
            "declining": "Analyze top-performing content and replicate success patterns",
            "stable": "Experiment with new content formats to drive growth"
        }
        return recommendations.get(trend, "Monitor engagement patterns")

    def _get_growth_recommendation(self, projection: str) -> str:
        """Get recommendation based on growth projection."""
        recommendations = {
            "positive": "Maintain quality while scaling engagement efforts",
            "at_risk": "Focus on community retention and satisfaction",
            "stable": "Identify growth catalysts and test new strategies"
        }
        return recommendations.get(projection, "Focus on sustainable growth")


def get_historical_data() -> Dict[str, Any]:
    """Gather historical data for analysis."""
    # Load existing logs
    sentiment_log = load_json(SENTIMENT_LOG) if Path(SENTIMENT_LOG).exists() else {}
    health_log = load_json(COMMUNITY_HEALTH_LOG) if Path(COMMUNITY_HEALTH_LOG).exists() else {}

    # Calculate historical metrics
    recent_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    # Aggregate historical sentiment
    recent_sentiments = []
    for date, entries in sentiment_log.items():
        if date >= recent_date:
            for entry in entries:
                recent_sentiments.append(entry.get("overall_sentiment", 0.0))

    # Aggregate historical health scores
    recent_health = []
    for date, entries in health_log.items():
        if date >= recent_date:
            for entry in entries:
                recent_health.append(entry.get("overall_score", 0.5))

    return {
        "recent_sentiment_avg": statistics.mean(recent_sentiments) if recent_sentiments else 0.0,
        "sentiment_volatility": statistics.stdev(recent_sentiments) if len(recent_sentiments) > 1 else 0.0,
        "avg_community_health": statistics.mean(recent_health) if recent_health else 0.5,
        "avg_engagement_rate": 0.0,  # Would be calculated from metrics log
        "engagement_growth": 0.0,    # Would be calculated from trend analysis
        "platform_diversity": 0.5,   # Would be calculated from correlation data
        "response_rate": 1.0,        # Would be calculated from engagement log
        "engagement_quality": 0.6    # Would be calculated from sentiment analysis
    }


def check_agent_health_integration() -> Dict[str, Any]:
    """Integrate with existing APU-37 agent health monitoring."""
    try:
        # Import APU-37 health check function
        from engagement_monitor_enhanced import check_agent_health
        return check_agent_health()
    except ImportError:
        # Fallback if APU-37 system not available
        return {
            "engagement_agent": {"status": "unknown", "health_score": 0.5},
            "engagement_bot": {"status": "unknown", "health_score": 0.5}
        }


def fetch_recent_comments() -> List[Dict]:
    """Fetch recent comments for sentiment analysis."""
    try:
        engagement_log = load_json(ENGAGEMENT_LOG)
        recent_comments = []

        # Get comments from last 24 hours
        cutoff = datetime.now() - timedelta(days=1)

        for entry in engagement_log.get("history", []):
            entry_date = datetime.fromisoformat(entry["date"])
            if entry_date >= cutoff:
                recent_comments.append({
                    "text": entry.get("comment", ""),
                    "platform": entry.get("platform", "unknown"),
                    "timestamp": entry["date"]
                })

        return recent_comments
    except Exception as e:
        print(f"[WARN] Could not fetch recent comments: {e}")
        return []


def generate_community_intelligence_alerts(intelligence_data: Dict) -> List[Dict[str, str]]:
    """Generate alerts based on community intelligence findings."""
    alerts = []

    sentiment = intelligence_data.get("sentiment_analysis", {})
    health = intelligence_data.get("community_health", {})
    predictions = intelligence_data.get("predictions", {})

    # Sentiment alerts
    if sentiment.get("overall_sentiment", 0) < ALERT_THRESHOLDS["sentiment_drop"]:
        alerts.append({
            "type": "community_sentiment_drop",
            "severity": "high",
            "message": f"Community sentiment dropped to {sentiment.get('overall_sentiment', 0):.2f}",
            "recommendation": "Review content strategy and increase positive engagement",
            "data": sentiment.get("sentiment_trend", "unknown")
        })

    # Community health alerts
    health_score = health.get("overall_score", 0.5)
    if health_score < COMMUNITY_HEALTH_THRESHOLDS["fair"]:
        severity = "critical" if health_score < COMMUNITY_HEALTH_THRESHOLDS["critical"] else "high"
        alerts.append({
            "type": "community_health_low",
            "severity": severity,
            "message": f"Community health score is {health_score:.2f} ({health.get('health_status', 'unknown')})",
            "recommendation": "; ".join(health.get("improvement_areas", [])),
            "strengths": "; ".join(health.get("strengths", []))
        })

    # Risk indicator alerts
    for risk in predictions.get("risk_indicators", []):
        alerts.append({
            "type": f"community_risk_{risk['type']}",
            "severity": risk["severity"],
            "message": risk["description"],
            "recommendation": risk["recommended_action"]
        })

    return alerts


def create_community_intelligence_dashboard(intelligence_data: Dict, alerts: List[Dict]) -> str:
    """Create comprehensive community intelligence dashboard."""
    dashboard = []
    dashboard.append("=" * 80)
    dashboard.append("[*] VAWN COMMUNITY INTELLIGENCE DASHBOARD (APU-51)")
    dashboard.append(f"[DATE] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    dashboard.append("=" * 80)

    # Community Health Summary
    health = intelligence_data.get("community_health", {})
    dashboard.append(f"\n[COMMUNITY HEALTH] OVERALL SCORE: {health.get('overall_score', 0.0):.3f}")
    dashboard.append(f"  Status: {health.get('health_status', 'unknown').upper()}")

    components = health.get("component_scores", {})
    dashboard.append(f"  Sentiment Health: {components.get('sentiment', 0.0):.2f} | Engagement: {components.get('engagement', 0.0):.2f}")
    dashboard.append(f"  Response Health: {components.get('response', 0.0):.2f} | Growth: {components.get('growth', 0.0):.2f}")

    # Sentiment Analysis
    sentiment = intelligence_data.get("sentiment_analysis", {})
    dashboard.append(f"\n[SENTIMENT] COMMUNITY MOOD ANALYSIS:")
    dashboard.append(f"  Overall Sentiment: {sentiment.get('overall_sentiment', 0.0):+.3f}")
    dashboard.append(f"  Community Satisfaction: {sentiment.get('community_satisfaction', 0.5):.2f}")
    dashboard.append(f"  Trend: {sentiment.get('sentiment_trend', 'unknown').upper()}")

    dist = sentiment.get("sentiment_distribution", {})
    dashboard.append(f"  Distribution: +{dist.get('positive', 0)} | ~{dist.get('neutral', 0)} | -{dist.get('negative', 0)}")

    themes = sentiment.get("emotional_themes", [])[:5]  # Top 5 themes
    if themes:
        dashboard.append(f"  Emotional Themes: {', '.join(themes)}")

    # Cross-Platform Analysis
    correlations = intelligence_data.get("cross_platform_analysis", {})
    cross_platform = correlations.get("cross_platform_trends", {})
    dashboard.append(f"\n[PLATFORMS] CROSS-PLATFORM PERFORMANCE:")
    dashboard.append(f"  Top Performer: {cross_platform.get('top_performer', 'unknown').upper()}")
    dashboard.append(f"  Average Performance: {cross_platform.get('average_performance', 0.0):.2f}")
    dashboard.append(f"  Platform Diversity: {cross_platform.get('platform_diversity_score', 0.0):.2f}")
    dashboard.append(f"  Est. Total Reach: {cross_platform.get('total_reach_estimate', 0):,}")

    # Platform breakdown
    platform_perf = correlations.get("platform_performance", {})
    for platform, stats in platform_perf.items():
        dashboard.append(f"    {platform.upper()}: {stats.get('performance_score', 0.0):.2f} score | {stats.get('engagement_rate', 0.0):.3f} rate")

    # Predictive Insights
    predictions = intelligence_data.get("predictions", {})
    dashboard.append(f"\n[PREDICTIONS] COMMUNITY FORECASTING:")
    dashboard.append(f"  Forecast Confidence: {predictions.get('forecast_confidence', 0.0):.1%}")

    sentiment_forecast = predictions.get("sentiment_forecast", {})
    dashboard.append(f"  Sentiment Trend: {sentiment_forecast.get('predicted_trend', 'unknown').upper()}")

    engagement_forecast = predictions.get("engagement_forecast", {})
    dashboard.append(f"  Engagement Trend: {engagement_forecast.get('predicted_trend', 'unknown').upper()}")

    growth_forecast = predictions.get("community_growth_projection", {})
    dashboard.append(f"  Growth Projection: {growth_forecast.get('projected_growth', 'unknown').upper()}")

    # Opportunities
    opportunities = predictions.get("opportunities", [])
    if opportunities:
        dashboard.append(f"\n[OPPORTUNITIES] GROWTH OPPORTUNITIES ({len(opportunities)}):")
        for opp in opportunities[:3]:  # Top 3 opportunities
            dashboard.append(f"  * {opp.get('description', '')} ({opp.get('potential', 'unknown')} potential)")

    # Strengths
    strengths = health.get("strengths", [])
    if strengths:
        dashboard.append(f"\n[STRENGTHS] COMMUNITY STRENGTHS ({len(strengths)}):")
        for strength in strengths:
            dashboard.append(f"  [+] {strength}")

    # Improvement Areas
    improvements = health.get("improvement_areas", [])
    if improvements:
        dashboard.append(f"\n[IMPROVEMENTS] ENHANCEMENT AREAS ({len(improvements)}):")
        for improvement in improvements:
            dashboard.append(f"  [!] {improvement}")

    # Community Intelligence Alerts
    dashboard.append(f"\n[INTELLIGENCE ALERTS] ACTIONABLE INSIGHTS ({len(alerts)}):")
    if alerts:
        for alert in alerts:
            severity_emoji = {
                "critical": "[CRIT]",
                "high": "[HIGH]",
                "medium": "[MED]",
                "low": "[LOW]",
                "info": "[INFO]"
            }.get(alert["severity"], "[INFO]")

            dashboard.append(f"  {severity_emoji} {alert['message']}")
            if alert.get("recommendation"):
                dashboard.append(f"         ->{alert['recommendation']}")
    else:
        dashboard.append("  [OK] All community intelligence metrics within normal ranges")

    dashboard.append("\n" + "=" * 80)

    return "\n".join(dashboard)


def save_community_intelligence_report(intelligence_data: Dict, alerts: List[Dict]):
    """Save comprehensive community intelligence report."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "version": "apu51_community_intelligence",
        "community_health": intelligence_data.get("community_health"),
        "sentiment_analysis": intelligence_data.get("sentiment_analysis"),
        "cross_platform_analysis": intelligence_data.get("cross_platform_analysis"),
        "predictions": intelligence_data.get("predictions"),
        "intelligence_alerts": alerts,
        "summary": {
            "community_health_score": intelligence_data.get("community_health", {}).get("overall_score", 0.0),
            "community_health_status": intelligence_data.get("community_health", {}).get("health_status", "unknown"),
            "overall_sentiment": intelligence_data.get("sentiment_analysis", {}).get("overall_sentiment", 0.0),
            "community_satisfaction": intelligence_data.get("sentiment_analysis", {}).get("community_satisfaction", 0.5),
            "top_platform": intelligence_data.get("cross_platform_analysis", {}).get("cross_platform_trends", {}).get("top_performer", "unknown"),
            "total_intelligence_alerts": len(alerts),
            "critical_alerts": len([a for a in alerts if a["severity"] == "critical"]),
            "forecast_confidence": intelligence_data.get("predictions", {}).get("forecast_confidence", 0.0),
            "generated_by": "APU-51 Community Intelligence Engine"
        }
    }

    # Save to community intelligence log
    intel_log = load_json(COMMUNITY_INTELLIGENCE_LOG) if Path(COMMUNITY_INTELLIGENCE_LOG).exists() else {}
    today = today_str()

    if today not in intel_log:
        intel_log[today] = []

    intel_log[today].append(report)

    # Keep only last 30 days
    cutoff_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    intel_log = {k: v for k, v in intel_log.items() if k >= cutoff_date}

    save_json(COMMUNITY_INTELLIGENCE_LOG, intel_log)

    # Save individual component logs
    save_sentiment_log(intelligence_data.get("sentiment_analysis"))
    save_community_health_log(intelligence_data.get("community_health"))

    return report


def save_sentiment_log(sentiment_data: Optional[Dict]):
    """Save sentiment analysis data to dedicated log."""
    if not sentiment_data:
        return

    sentiment_log = load_json(SENTIMENT_LOG) if Path(SENTIMENT_LOG).exists() else {}
    today = today_str()

    if today not in sentiment_log:
        sentiment_log[today] = []

    sentiment_entry = {
        "timestamp": datetime.now().isoformat(),
        "overall_sentiment": sentiment_data.get("overall_sentiment"),
        "sentiment_distribution": sentiment_data.get("sentiment_distribution"),
        "community_satisfaction": sentiment_data.get("community_satisfaction"),
        "sentiment_trend": sentiment_data.get("sentiment_trend"),
        "emotional_themes": sentiment_data.get("emotional_themes"),
        "analyzed_count": sentiment_data.get("analyzed_count")
    }

    sentiment_log[today].append(sentiment_entry)

    # Keep only last 30 days
    cutoff_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    sentiment_log = {k: v for k, v in sentiment_log.items() if k >= cutoff_date}

    save_json(SENTIMENT_LOG, sentiment_log)


def save_community_health_log(health_data: Optional[Dict]):
    """Save community health data to dedicated log."""
    if not health_data:
        return

    health_log = load_json(COMMUNITY_HEALTH_LOG) if Path(COMMUNITY_HEALTH_LOG).exists() else {}
    today = today_str()

    if today not in health_log:
        health_log[today] = []

    health_log[today].append(health_data)

    # Keep only last 30 days
    cutoff_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    health_log = {k: v for k, v in health_log.items() if k >= cutoff_date}

    save_json(COMMUNITY_HEALTH_LOG, health_log)


def main():
    """Main APU-51 Community Intelligence Engine execution."""
    print(f"\n[*] APU-51 Community Intelligence Engine Starting...")
    print(f"[VERSION] Community Intelligence v1.0")

    # Initialize the intelligence engine
    intelligence_engine = CommunityIntelligenceEngine()

    # Gather data from existing systems
    print("[DATA] Gathering community data...")

    # Get recent comments for sentiment analysis
    recent_comments = fetch_recent_comments()
    print(f"[DATA] Found {len(recent_comments)} recent comments for analysis")

    # Get current engagement metrics (integrate with existing APU-37 systems)
    try:
        from engagement_monitor_enhanced import analyze_engagement_metrics
        current_metrics = analyze_engagement_metrics()
    except ImportError:
        # Fallback if APU-37 not available
        current_metrics = {"platform_stats": {}, "comment_stats": {}, "overall_engagement_rate": 0.0}

    # Get agent health status
    agent_health = check_agent_health_integration()

    # Get historical data for predictions
    historical_data = get_historical_data()

    # Run community intelligence analysis
    print("[ANALYSIS] Running community intelligence analysis...")

    # 1. Sentiment Analysis
    print("  > Analyzing community sentiment...")
    sentiment_analysis = intelligence_engine.analyze_comment_sentiment(recent_comments)

    # 2. Cross-Platform Correlation Analysis
    print("  > Analyzing cross-platform patterns...")
    cross_platform_analysis = intelligence_engine.analyze_cross_platform_correlation(current_metrics)

    # 3. Community Health Scoring
    print("  > Calculating community health score...")
    community_health = intelligence_engine.calculate_community_health_score(
        sentiment_analysis, cross_platform_analysis, agent_health
    )

    # 4. Predictive Analytics
    print("  > Generating predictive insights...")
    predictions = intelligence_engine.generate_predictive_insights(historical_data)

    # Compile intelligence data
    intelligence_data = {
        "sentiment_analysis": sentiment_analysis,
        "cross_platform_analysis": cross_platform_analysis,
        "community_health": community_health,
        "predictions": predictions,
        "agent_health_integration": agent_health,
        "data_sources": {
            "comments_analyzed": len(recent_comments),
            "platforms_monitored": len(PLATFORMS),
            "historical_days": 7
        }
    }

    # Generate intelligence alerts
    print("[ALERTS] Generating community intelligence alerts...")
    alerts = generate_community_intelligence_alerts(intelligence_data)

    # Create and display dashboard
    dashboard = create_community_intelligence_dashboard(intelligence_data, alerts)
    print(dashboard)

    # Save comprehensive report
    report = save_community_intelligence_report(intelligence_data, alerts)

    # Log summary to main system
    summary = report["summary"]
    health_status = summary["community_health_status"]
    sentiment = summary["overall_sentiment"]
    satisfaction = summary["community_satisfaction"]
    critical_count = summary["critical_alerts"]

    status = "critical" if critical_count > 0 else "warning" if health_status in ["poor", "critical"] else "ok"

    log_entry = (f"Community Health: {summary['community_health_score']:.2f} ({health_status}), "
                f"Sentiment: {sentiment:+.2f}, Satisfaction: {satisfaction:.2f}, "
                f"{summary['total_intelligence_alerts']} alerts")

    log_run("CommunityIntelligenceAPU51", status, log_entry)

    print(f"\n[COMPLETE] Community Intelligence Analysis Complete")
    print(f"Health Score: {summary['community_health_score']:.3f} ({health_status})")
    print(f"Sentiment: {sentiment:+.3f} | Satisfaction: {satisfaction:.2f}")
    print(f"Alerts: {summary['total_intelligence_alerts']} total ({critical_count} critical)")
    print(f"Top Platform: {summary['top_platform']}")

    return alerts


if __name__ == "__main__":
    alerts = main()

    # Exit with appropriate code based on community intelligence health
    critical_alerts = [a for a in alerts if a["severity"] == "critical"]
    high_priority_alerts = [a for a in alerts if a["severity"] in ["critical", "high"]]

    if critical_alerts:
        print(f"\n[CRITICAL] {len(critical_alerts)} CRITICAL COMMUNITY INTELLIGENCE ALERTS!")
        print("Community requires immediate attention")
        sys.exit(2)
    elif high_priority_alerts:
        print(f"\n[WARNING] {len(high_priority_alerts)} HIGH PRIORITY COMMUNITY ALERTS!")
        sys.exit(1)
    else:
        print(f"\n[OK] Community intelligence analysis complete - {len(alerts)} total alerts")
        sys.exit(0)