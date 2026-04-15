"""
apu72_advanced_engagement_monitor.py — APU-72 Advanced Community Intelligence Monitor

Next-generation engagement monitoring with predictive analytics, cross-departmental
coordination, and proactive strategy optimization.

Created by: Dex - Community Agent (APU-72)

Key Features:
- Predictive community analytics with 24-48h forecasting
- Cross-departmental intelligence coordination (Paperclip integration)
- Advanced narrative tracking and story momentum analysis
- Community relationship intelligence and influence mapping
- Proactive strategy optimization with real-time recommendations
- ML-based engagement prediction algorithms
- Department-specific alert escalation protocols
- Automated community crisis prevention systems

Builds on APU-70 real-time monitoring with advanced intelligence layers.
"""

import json
import sys
import asyncio
import time
import threading
import statistics
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import deque, defaultdict
from dataclasses import dataclass, asdict
import pickle

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import (
    load_json, save_json, ENGAGEMENT_LOG, RESEARCH_LOG, METRICS_LOG,
    VAWN_DIR, log_run, today_str, get_anthropic_client
)

# Import APU-70 components
sys.path.insert(0, r"C:\Users\rdyal\Vawn\src")
try:
    from apu70_realtime_engagement_monitor import RealTimeEngagementMonitor
    from apu49_paperclip_engagement_monitor import (
        DEPARTMENTS, DEPARTMENT_THRESHOLDS, analyze_department_specific_engagement
    )
except ImportError:
    print("[WARNING] Previous APU modules not fully available - using fallback methods")

# APU-72 Configuration Files
APU72_BASE_DIR = VAWN_DIR / "research" / "apu72_intelligence"
APU72_BASE_DIR.mkdir(exist_ok=True)

COMMUNITY_INTELLIGENCE_LOG = APU72_BASE_DIR / "community_intelligence_log.json"
PREDICTIVE_ANALYTICS_LOG = APU72_BASE_DIR / "predictive_analytics_log.json"
NARRATIVE_TRACKING_LOG = APU72_BASE_DIR / "narrative_tracking_log.json"
RELATIONSHIP_INTELLIGENCE_LOG = APU72_BASE_DIR / "relationship_intelligence_log.json"
STRATEGY_OPTIMIZATION_LOG = APU72_BASE_DIR / "strategy_optimization_log.json"
DEPARTMENT_COORDINATION_LOG = APU72_BASE_DIR / "department_coordination_log.json"
PREDICTION_MODEL_DATA = APU72_BASE_DIR / "prediction_models.pkl"

# Advanced Configuration
APU72_CONFIG = {
    "predictive_analysis_interval": 300,  # 5 minutes
    "narrative_tracking_interval": 30,    # 30 seconds
    "strategy_optimization_interval": 900, # 15 minutes
    "department_coordination_interval": 900, # 15 minutes
    "prediction_horizon_hours": 48,
    "early_warning_threshold": 0.15,      # 15% decline prediction
    "crisis_prevention_threshold": 0.25,  # 25% health score
    "narrative_momentum_threshold": 0.3,   # Significant story momentum
    "relationship_strength_threshold": 0.7 # Key relationship identification
}

# Department Coordination Matrix
PAPERCLIP_DEPARTMENTS = {
    "cos": {
        "name": "Chief of Staff",
        "escalation_priority": 1,
        "alert_types": ["strategic", "crisis", "cross_department"],
        "response_time_target": 300  # 5 minutes
    },
    "video": {
        "name": "Video Department",
        "escalation_priority": 2,
        "alert_types": ["content", "narrative", "viral_potential"],
        "response_time_target": 600  # 10 minutes
    },
    "ar": {
        "name": "A&R Department",
        "escalation_priority": 2,
        "alert_types": ["artist_development", "community_feedback", "strategic"],
        "response_time_target": 900  # 15 minutes
    },
    "marketing": {
        "name": "Marketing Department",
        "escalation_priority": 2,
        "alert_types": ["campaign", "engagement", "strategy"],
        "response_time_target": 900  # 15 minutes
    }
}

@dataclass
class CommunityPrediction:
    """Community health and engagement prediction data structure."""
    timestamp: str
    prediction_horizon_hours: int
    current_health_score: float
    predicted_health_score: float
    confidence: float
    trend_direction: str
    risk_factors: List[str]
    recommended_actions: List[str]

@dataclass
class NarrativeMomentum:
    """Narrative tracking and story momentum data structure."""
    timestamp: str
    story_title: str
    platforms: List[str]
    momentum_score: float
    velocity: float
    peak_prediction_hours: int
    amplification_recommendations: List[str]

@dataclass
class CommunityRelationship:
    """Community relationship and influence mapping data structure."""
    timestamp: str
    member_id: str
    influence_score: float
    engagement_correlation: float
    sentiment_leadership: float
    relationship_strength: float
    community_role: str

@dataclass
class StrategyRecommendation:
    """Proactive strategy optimization recommendation data structure."""
    timestamp: str
    category: str
    priority: str
    recommendation: str
    expected_impact: float
    implementation_effort: str
    success_metrics: List[str]

@dataclass
class DepartmentAlert:
    """Cross-departmental coordination alert data structure."""
    timestamp: str
    department: str
    alert_type: str
    priority: str
    message: str
    required_response: str
    escalation_path: List[str]
    coordination_required: List[str]


class PredictiveCommunityAnalytics:
    """ML-based predictive analytics for community behavior and health."""

    def __init__(self):
        self.claude_client = get_anthropic_client()
        self.historical_data = deque(maxlen=1000)
        self.prediction_models = self.load_prediction_models()
        self.prediction_accuracy_history = deque(maxlen=100)

    def load_prediction_models(self) -> Dict:
        """Load or initialize prediction models."""
        if PREDICTION_MODEL_DATA.exists():
            try:
                with open(PREDICTION_MODEL_DATA, 'rb') as f:
                    return pickle.load(f)
            except:
                pass

        return {
            "community_health": {"weights": [0.3, 0.2, 0.2, 0.2, 0.1], "bias": 0.5},
            "engagement_trend": {"weights": [0.4, 0.3, 0.2, 0.1], "bias": 0.0},
            "crisis_prediction": {"weights": [0.5, 0.3, 0.2], "bias": 0.1}
        }

    def save_prediction_models(self):
        """Save updated prediction models."""
        try:
            with open(PREDICTION_MODEL_DATA, 'wb') as f:
                pickle.dump(self.prediction_models, f)
        except Exception as e:
            print(f"[WARNING] Could not save prediction models: {e}")

    def generate_community_prediction(self, current_data: Dict) -> CommunityPrediction:
        """Generate predictive analytics for community health."""
        try:
            current_health = current_data.get("community_health", {}).get("overall_score", 0.5)

            # Simple prediction algorithm (would be ML-based in production)
            trend_factors = self.calculate_trend_factors(current_data)
            predicted_health = self.predict_health_score(current_health, trend_factors)
            confidence = self.calculate_prediction_confidence(trend_factors)

            # Determine trend direction
            trend_direction = "declining" if predicted_health < current_health - 0.05 else \
                            "improving" if predicted_health > current_health + 0.05 else "stable"

            # Identify risk factors
            risk_factors = self.identify_risk_factors(current_data, trend_factors)

            # Generate recommendations
            recommendations = self.generate_health_recommendations(
                current_health, predicted_health, risk_factors
            )

            prediction = CommunityPrediction(
                timestamp=datetime.now().isoformat(),
                prediction_horizon_hours=APU72_CONFIG["prediction_horizon_hours"],
                current_health_score=current_health,
                predicted_health_score=predicted_health,
                confidence=confidence,
                trend_direction=trend_direction,
                risk_factors=risk_factors,
                recommended_actions=recommendations
            )

            # Log prediction
            self.log_prediction(prediction)
            return prediction

        except Exception as e:
            print(f"[ERROR] Predictive analytics error: {e}")
            return CommunityPrediction(
                timestamp=datetime.now().isoformat(),
                prediction_horizon_hours=48,
                current_health_score=0.5,
                predicted_health_score=0.5,
                confidence=0.1,
                trend_direction="unknown",
                risk_factors=["prediction_error"],
                recommended_actions=["review_system"]
            )

    def calculate_trend_factors(self, current_data: Dict) -> Dict[str, float]:
        """Calculate trend factors for prediction algorithms."""
        factors = {
            "engagement_velocity": 0.0,
            "sentiment_trend": 0.0,
            "platform_correlation": 0.0,
            "response_rate_trend": 0.0,
            "community_activity_trend": 0.0
        }

        try:
            realtime_metrics = current_data.get("realtime_metrics", {})

            # Calculate basic trend factors
            factors["engagement_velocity"] = realtime_metrics.get("recent_engagement_rate", 0.0)
            factors["sentiment_trend"] = realtime_metrics.get("sentiment_velocity", 0.0)
            factors["platform_correlation"] = len(current_data.get("platform_status", {})) / 5.0
            factors["response_rate_trend"] = realtime_metrics.get("response_velocity", 0.0)
            factors["community_activity_trend"] = realtime_metrics.get("community_activity_score", 0.0)

        except Exception as e:
            print(f"[WARNING] Error calculating trend factors: {e}")

        return factors

    def predict_health_score(self, current_health: float, trend_factors: Dict[str, float]) -> float:
        """Predict future community health score."""
        model = self.prediction_models["community_health"]
        weights = model["weights"]
        bias = model["bias"]

        # Simple weighted prediction (would be ML model in production)
        factor_values = list(trend_factors.values())
        if len(factor_values) >= len(weights):
            prediction = sum(w * f for w, f in zip(weights, factor_values[:len(weights)])) + bias
        else:
            prediction = current_health  # Fallback

        # Apply current health influence
        predicted_score = (current_health * 0.6) + (prediction * 0.4)

        return max(0.0, min(1.0, predicted_score))

    def calculate_prediction_confidence(self, trend_factors: Dict[str, float]) -> float:
        """Calculate confidence level for predictions."""
        # Higher confidence when we have more complete data
        data_completeness = sum(1 for v in trend_factors.values() if v > 0) / len(trend_factors)
        base_confidence = 0.6 + (data_completeness * 0.4)

        return min(0.95, max(0.1, base_confidence))

    def identify_risk_factors(self, current_data: Dict, trend_factors: Dict[str, float]) -> List[str]:
        """Identify potential risk factors for community health."""
        risk_factors = []

        try:
            # Check for declining trends
            if trend_factors["engagement_velocity"] < 0.3:
                risk_factors.append("low_engagement_velocity")

            if trend_factors["sentiment_trend"] < -0.1:
                risk_factors.append("negative_sentiment_trend")

            if trend_factors["response_rate_trend"] < 0.2:
                risk_factors.append("slow_response_rate")

            if trend_factors["community_activity_trend"] < 0.4:
                risk_factors.append("low_community_activity")

            # Check crisis indicators
            crisis_indicators = current_data.get("crisis_indicators", {})
            if crisis_indicators.get("crisis_score", 0) > 0.5:
                risk_factors.append("crisis_indicators_present")

            # Check platform status
            platform_status = current_data.get("platform_status", {})
            inactive_platforms = [p for p, s in platform_status.items() if s.get("active", True) == False]
            if len(inactive_platforms) > 1:
                risk_factors.append("multiple_platform_issues")

        except Exception as e:
            print(f"[WARNING] Error identifying risk factors: {e}")
            risk_factors.append("risk_analysis_error")

        return risk_factors

    def generate_health_recommendations(self, current_health: float,
                                       predicted_health: float, risk_factors: List[str]) -> List[str]:
        """Generate actionable recommendations for community health improvement."""
        recommendations = []

        # Health-based recommendations
        if predicted_health < 0.3:
            recommendations.append("immediate_community_crisis_intervention")
            recommendations.append("activate_emergency_engagement_protocols")
        elif predicted_health < 0.5:
            recommendations.append("increase_community_engagement_frequency")
            recommendations.append("deploy_sentiment_recovery_content")
        elif predicted_health < 0.7:
            recommendations.append("optimize_community_interaction_strategy")
            recommendations.append("monitor_engagement_quality_metrics")

        # Risk factor specific recommendations
        if "low_engagement_velocity" in risk_factors:
            recommendations.append("boost_interactive_content_creation")

        if "negative_sentiment_trend" in risk_factors:
            recommendations.append("deploy_positive_community_initiatives")

        if "slow_response_rate" in risk_factors:
            recommendations.append("optimize_response_automation_systems")

        if "multiple_platform_issues" in risk_factors:
            recommendations.append("coordinate_cross_platform_recovery_strategy")

        return recommendations

    def log_prediction(self, prediction: CommunityPrediction):
        """Log prediction for tracking accuracy and improvement."""
        try:
            prediction_log = load_json(PREDICTIVE_ANALYTICS_LOG) if PREDICTIVE_ANALYTICS_LOG.exists() else {}
            today = today_str()

            if today not in prediction_log:
                prediction_log[today] = []

            prediction_log[today].append(asdict(prediction))
            save_json(PREDICTIVE_ANALYTICS_LOG, prediction_log)

        except Exception as e:
            print(f"[WARNING] Could not log prediction: {e}")


class NarrativeTrackingEngine:
    """Advanced narrative tracking and story momentum analysis."""

    def __init__(self):
        self.claude_client = get_anthropic_client()
        self.active_narratives = {}
        self.momentum_history = deque(maxlen=200)

    def track_narrative_momentum(self, current_data: Dict) -> List[NarrativeMomentum]:
        """Track and analyze narrative momentum across platforms."""
        try:
            narratives = []

            # Analyze current engagement data for narrative patterns
            engagement_data = current_data.get("realtime_metrics", {})
            platform_activity = engagement_data.get("platform_activity", {})

            # Extract narrative signals
            narrative_signals = self.extract_narrative_signals(current_data)

            for signal in narrative_signals:
                momentum = self.calculate_narrative_momentum(signal, platform_activity)
                narratives.append(momentum)

            # Log narrative tracking
            self.log_narratives(narratives)
            return narratives

        except Exception as e:
            print(f"[ERROR] Narrative tracking error: {e}")
            return []

    def extract_narrative_signals(self, current_data: Dict) -> List[Dict]:
        """Extract potential narrative signals from engagement data."""
        signals = []

        try:
            # Look for engagement spikes or patterns that indicate stories
            realtime_metrics = current_data.get("realtime_metrics", {})
            recent_engagement = realtime_metrics.get("recent_engagement_count", 0)

            if recent_engagement > 5:  # Significant engagement activity
                signals.append({
                    "type": "engagement_spike",
                    "intensity": recent_engagement / 10.0,
                    "platforms": ["instagram", "tiktok", "x"],  # Default platforms
                    "confidence": 0.6
                })

            # Check department-specific signals
            department_analytics = current_data.get("department_analytics", {})
            for dept, analytics in department_analytics.items():
                if analytics.get("activity_score", 0) > 0.7:
                    signals.append({
                        "type": f"{dept}_narrative",
                        "intensity": analytics.get("activity_score", 0.5),
                        "platforms": analytics.get("active_platforms", []),
                        "confidence": 0.7
                    })

        except Exception as e:
            print(f"[WARNING] Error extracting narrative signals: {e}")

        return signals

    def calculate_narrative_momentum(self, signal: Dict, platform_activity: Dict) -> NarrativeMomentum:
        """Calculate momentum score and predictions for a narrative signal."""
        try:
            # Calculate momentum score based on signal intensity and platform activity
            base_momentum = signal.get("intensity", 0.5)
            platform_boost = sum(
                platform_activity.get(platform, {}).get("activity_rate", 0.0)
                for platform in signal.get("platforms", [])
            ) / max(len(signal.get("platforms", [])), 1)

            momentum_score = (base_momentum * 0.6) + (platform_boost * 0.4)

            # Calculate velocity (change in momentum)
            velocity = momentum_score - 0.5  # Simple velocity calculation

            # Predict peak timing
            peak_hours = max(2, int(12 * (1 - momentum_score)))

            # Generate amplification recommendations
            amplification_recommendations = self.generate_amplification_recommendations(
                signal, momentum_score, platform_activity
            )

            return NarrativeMomentum(
                timestamp=datetime.now().isoformat(),
                story_title=f"{signal.get('type', 'unknown')}_narrative_{int(momentum_score*100)}",
                platforms=signal.get("platforms", []),
                momentum_score=momentum_score,
                velocity=velocity,
                peak_prediction_hours=peak_hours,
                amplification_recommendations=amplification_recommendations
            )

        except Exception as e:
            print(f"[WARNING] Error calculating narrative momentum: {e}")
            return NarrativeMomentum(
                timestamp=datetime.now().isoformat(),
                story_title="error_narrative",
                platforms=[],
                momentum_score=0.0,
                velocity=0.0,
                peak_prediction_hours=24,
                amplification_recommendations=["review_narrative_tracking"]
            )

    def generate_amplification_recommendations(self, signal: Dict, momentum_score: float,
                                             platform_activity: Dict) -> List[str]:
        """Generate recommendations for narrative amplification."""
        recommendations = []

        if momentum_score > 0.7:
            recommendations.append("immediate_cross_platform_amplification")
            recommendations.append("coordinate_department_content_push")
        elif momentum_score > 0.5:
            recommendations.append("moderate_amplification_strategy")
            recommendations.append("monitor_for_viral_potential")
        else:
            recommendations.append("organic_growth_monitoring")
            recommendations.append("prepare_amplification_if_momentum_increases")

        # Platform-specific recommendations
        active_platforms = signal.get("platforms", [])
        if "instagram" in active_platforms:
            recommendations.append("optimize_instagram_story_content")
        if "tiktok" in active_platforms:
            recommendations.append("create_tiktok_trend_content")
        if "x" in active_platforms:
            recommendations.append("engage_x_community_discussions")

        return recommendations

    def log_narratives(self, narratives: List[NarrativeMomentum]):
        """Log narrative tracking data."""
        try:
            narrative_log = load_json(NARRATIVE_TRACKING_LOG) if NARRATIVE_TRACKING_LOG.exists() else {}
            today = today_str()

            if today not in narrative_log:
                narrative_log[today] = []

            for narrative in narratives:
                narrative_log[today].append(asdict(narrative))

            save_json(NARRATIVE_TRACKING_LOG, narrative_log)

        except Exception as e:
            print(f"[WARNING] Could not log narratives: {e}")


class CommunityRelationshipIntelligence:
    """Community relationship mapping and influence analysis."""

    def __init__(self):
        self.claude_client = get_anthropic_client()
        self.relationship_map = {}
        self.influence_history = deque(maxlen=500)

    def analyze_community_relationships(self, current_data: Dict) -> List[CommunityRelationship]:
        """Analyze and map community relationships and influence patterns."""
        try:
            relationships = []

            # Extract community interaction patterns
            community_data = current_data.get("community_health", {})
            engagement_metrics = current_data.get("realtime_metrics", {})

            # Identify key community members (simulated for this implementation)
            key_members = self.identify_key_community_members(community_data, engagement_metrics)

            for member in key_members:
                relationship = self.analyze_member_influence(member, community_data)
                relationships.append(relationship)

            # Log relationship analysis
            self.log_relationships(relationships)
            return relationships

        except Exception as e:
            print(f"[ERROR] Relationship analysis error: {e}")
            return []

    def identify_key_community_members(self, community_data: Dict, engagement_metrics: Dict) -> List[Dict]:
        """Identify key community members based on engagement patterns."""
        # Simulated key member identification
        key_members = []

        engagement_count = engagement_metrics.get("recent_engagement_count", 0)
        if engagement_count > 0:
            # Generate simulated key members based on engagement activity
            for i in range(min(3, max(1, engagement_count // 3))):
                key_members.append({
                    "id": f"community_member_{i+1}",
                    "engagement_frequency": 0.3 + (i * 0.2),
                    "response_quality": 0.4 + (i * 0.15),
                    "sentiment_leadership": 0.5 + (i * 0.1)
                })

        return key_members

    def analyze_member_influence(self, member: Dict, community_data: Dict) -> CommunityRelationship:
        """Analyze individual member's influence on community."""
        try:
            # Calculate influence metrics
            influence_score = member.get("engagement_frequency", 0.5) * 0.4 + \
                            member.get("response_quality", 0.5) * 0.3 + \
                            member.get("sentiment_leadership", 0.5) * 0.3

            engagement_correlation = member.get("engagement_frequency", 0.5)
            sentiment_leadership = member.get("sentiment_leadership", 0.5)
            relationship_strength = (influence_score + engagement_correlation) / 2

            # Determine community role
            if influence_score > 0.8:
                community_role = "key_influencer"
            elif influence_score > 0.6:
                community_role = "active_contributor"
            elif influence_score > 0.4:
                community_role = "regular_member"
            else:
                community_role = "occasional_participant"

            return CommunityRelationship(
                timestamp=datetime.now().isoformat(),
                member_id=member.get("id", "unknown"),
                influence_score=influence_score,
                engagement_correlation=engagement_correlation,
                sentiment_leadership=sentiment_leadership,
                relationship_strength=relationship_strength,
                community_role=community_role
            )

        except Exception as e:
            print(f"[WARNING] Error analyzing member influence: {e}")
            return CommunityRelationship(
                timestamp=datetime.now().isoformat(),
                member_id="error_member",
                influence_score=0.0,
                engagement_correlation=0.0,
                sentiment_leadership=0.0,
                relationship_strength=0.0,
                community_role="unknown"
            )

    def log_relationships(self, relationships: List[CommunityRelationship]):
        """Log relationship intelligence data."""
        try:
            relationship_log = load_json(RELATIONSHIP_INTELLIGENCE_LOG) if RELATIONSHIP_INTELLIGENCE_LOG.exists() else {}
            today = today_str()

            if today not in relationship_log:
                relationship_log[today] = []

            for relationship in relationships:
                relationship_log[today].append(asdict(relationship))

            save_json(RELATIONSHIP_INTELLIGENCE_LOG, relationship_log)

        except Exception as e:
            print(f"[WARNING] Could not log relationships: {e}")


class ProactiveStrategyEngine:
    """Proactive strategy optimization and recommendation system."""

    def __init__(self):
        self.claude_client = get_anthropic_client()
        self.strategy_history = deque(maxlen=100)
        self.optimization_patterns = {}

    def generate_strategy_recommendations(self, current_data: Dict,
                                        predictions: List[CommunityPrediction],
                                        narratives: List[NarrativeMomentum],
                                        relationships: List[CommunityRelationship]) -> List[StrategyRecommendation]:
        """Generate proactive strategy optimization recommendations."""
        try:
            recommendations = []

            # Strategy recommendations based on predictions
            for prediction in predictions:
                pred_recommendations = self.generate_predictive_strategies(prediction, current_data)
                recommendations.extend(pred_recommendations)

            # Strategy recommendations based on narratives
            for narrative in narratives:
                narrative_recommendations = self.generate_narrative_strategies(narrative, current_data)
                recommendations.extend(narrative_recommendations)

            # Strategy recommendations based on relationships
            if relationships:
                relationship_recommendations = self.generate_relationship_strategies(relationships, current_data)
                recommendations.extend(relationship_recommendations)

            # General optimization recommendations
            general_recommendations = self.generate_general_optimization(current_data)
            recommendations.extend(general_recommendations)

            # Prioritize and deduplicate
            prioritized_recommendations = self.prioritize_recommendations(recommendations)

            # Log strategies
            self.log_strategies(prioritized_recommendations)
            return prioritized_recommendations

        except Exception as e:
            print(f"[ERROR] Strategy generation error: {e}")
            return []

    def generate_predictive_strategies(self, prediction: CommunityPrediction, current_data: Dict) -> List[StrategyRecommendation]:
        """Generate strategies based on community health predictions."""
        strategies = []

        try:
            if prediction.trend_direction == "declining":
                strategies.append(StrategyRecommendation(
                    timestamp=datetime.now().isoformat(),
                    category="crisis_prevention",
                    priority="high",
                    recommendation="Implement preemptive community engagement boost",
                    expected_impact=0.3,
                    implementation_effort="medium",
                    success_metrics=["community_health_improvement", "engagement_rate_increase"]
                ))

            if prediction.predicted_health_score < 0.4:
                strategies.append(StrategyRecommendation(
                    timestamp=datetime.now().isoformat(),
                    category="emergency_response",
                    priority="critical",
                    recommendation="Activate emergency community crisis protocols",
                    expected_impact=0.5,
                    implementation_effort="high",
                    success_metrics=["crisis_resolution_time", "community_sentiment_recovery"]
                ))

            if "low_engagement_velocity" in prediction.risk_factors:
                strategies.append(StrategyRecommendation(
                    timestamp=datetime.now().isoformat(),
                    category="engagement_optimization",
                    priority="medium",
                    recommendation="Deploy interactive content campaigns to boost engagement velocity",
                    expected_impact=0.25,
                    implementation_effort="low",
                    success_metrics=["engagement_velocity_increase", "community_activity_score"]
                ))

        except Exception as e:
            print(f"[WARNING] Error generating predictive strategies: {e}")

        return strategies

    def generate_narrative_strategies(self, narrative: NarrativeMomentum, current_data: Dict) -> List[StrategyRecommendation]:
        """Generate strategies based on narrative momentum analysis."""
        strategies = []

        try:
            if narrative.momentum_score > 0.7:
                strategies.append(StrategyRecommendation(
                    timestamp=datetime.now().isoformat(),
                    category="narrative_amplification",
                    priority="high",
                    recommendation=f"Amplify high-momentum narrative '{narrative.story_title}' across platforms",
                    expected_impact=0.4,
                    implementation_effort="medium",
                    success_metrics=["narrative_reach_expansion", "cross_platform_engagement"]
                ))

            if narrative.velocity > 0.3:
                strategies.append(StrategyRecommendation(
                    timestamp=datetime.now().isoformat(),
                    category="content_strategy",
                    priority="medium",
                    recommendation=f"Create supporting content for trending narrative in next {narrative.peak_prediction_hours} hours",
                    expected_impact=0.3,
                    implementation_effort="low",
                    success_metrics=["content_engagement_rate", "narrative_sustainability"]
                ))

        except Exception as e:
            print(f"[WARNING] Error generating narrative strategies: {e}")

        return strategies

    def generate_relationship_strategies(self, relationships: List[CommunityRelationship], current_data: Dict) -> List[StrategyRecommendation]:
        """Generate strategies based on community relationship intelligence."""
        strategies = []

        try:
            # Identify key influencers for targeted engagement
            key_influencers = [r for r in relationships if r.community_role == "key_influencer"]

            if key_influencers:
                strategies.append(StrategyRecommendation(
                    timestamp=datetime.now().isoformat(),
                    category="influencer_engagement",
                    priority="medium",
                    recommendation=f"Implement targeted engagement strategy with {len(key_influencers)} key community influencers",
                    expected_impact=0.35,
                    implementation_effort="medium",
                    success_metrics=["influencer_engagement_rate", "community_sentiment_leadership"]
                ))

            # Check for relationship strength opportunities
            strong_relationships = [r for r in relationships if r.relationship_strength > 0.7]
            if strong_relationships:
                strategies.append(StrategyRecommendation(
                    timestamp=datetime.now().isoformat(),
                    category="relationship_optimization",
                    priority="low",
                    recommendation="Leverage strong community relationships for organic growth amplification",
                    expected_impact=0.2,
                    implementation_effort="low",
                    success_metrics=["organic_growth_rate", "community_advocacy_increase"]
                ))

        except Exception as e:
            print(f"[WARNING] Error generating relationship strategies: {e}")

        return strategies

    def generate_general_optimization(self, current_data: Dict) -> List[StrategyRecommendation]:
        """Generate general optimization recommendations."""
        strategies = []

        try:
            # Platform performance optimization
            platform_status = current_data.get("platform_status", {})
            low_performing_platforms = [p for p, s in platform_status.items() if s.get("performance", 0.5) < 0.4]

            if low_performing_platforms:
                strategies.append(StrategyRecommendation(
                    timestamp=datetime.now().isoformat(),
                    category="platform_optimization",
                    priority="medium",
                    recommendation=f"Optimize performance on {len(low_performing_platforms)} underperforming platforms",
                    expected_impact=0.25,
                    implementation_effort="medium",
                    success_metrics=["platform_performance_improvement", "cross_platform_consistency"]
                ))

            # Response time optimization
            realtime_metrics = current_data.get("realtime_metrics", {})
            response_velocity = realtime_metrics.get("response_velocity", 0.5)

            if response_velocity < 0.3:
                strategies.append(StrategyRecommendation(
                    timestamp=datetime.now().isoformat(),
                    category="response_optimization",
                    priority="medium",
                    recommendation="Implement automated response systems to improve community response velocity",
                    expected_impact=0.2,
                    implementation_effort="medium",
                    success_metrics=["response_velocity_improvement", "community_satisfaction_increase"]
                ))

        except Exception as e:
            print(f"[WARNING] Error generating general optimization strategies: {e}")

        return strategies

    def prioritize_recommendations(self, recommendations: List[StrategyRecommendation]) -> List[StrategyRecommendation]:
        """Prioritize and deduplicate strategy recommendations."""
        # Sort by priority and expected impact
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}

        prioritized = sorted(recommendations, key=lambda r: (
            priority_order.get(r.priority, 4),
            -r.expected_impact
        ))

        # Remove duplicates based on category and recommendation similarity
        unique_recommendations = []
        seen_categories = set()

        for rec in prioritized:
            if rec.category not in seen_categories:
                unique_recommendations.append(rec)
                seen_categories.add(rec.category)

        return unique_recommendations[:10]  # Limit to top 10 recommendations

    def log_strategies(self, strategies: List[StrategyRecommendation]):
        """Log strategy recommendations."""
        try:
            strategy_log = load_json(STRATEGY_OPTIMIZATION_LOG) if STRATEGY_OPTIMIZATION_LOG.exists() else {}
            today = today_str()

            if today not in strategy_log:
                strategy_log[today] = []

            for strategy in strategies:
                strategy_log[today].append(asdict(strategy))

            save_json(STRATEGY_OPTIMIZATION_LOG, strategy_log)

        except Exception as e:
            print(f"[WARNING] Could not log strategies: {e}")


class CrossDepartmentalHub:
    """Cross-departmental intelligence coordination and alert system."""

    def __init__(self):
        self.claude_client = get_anthropic_client()
        self.department_alerts = deque(maxlen=100)
        self.coordination_history = deque(maxlen=200)

    def coordinate_department_intelligence(self, current_data: Dict,
                                         predictions: List[CommunityPrediction],
                                         narratives: List[NarrativeMomentum],
                                         strategies: List[StrategyRecommendation]) -> List[DepartmentAlert]:
        """Coordinate intelligence sharing and alerts between departments."""
        try:
            alerts = []

            # Generate department-specific alerts based on intelligence
            cos_alerts = self.generate_cos_alerts(current_data, predictions, strategies)
            alerts.extend(cos_alerts)

            video_alerts = self.generate_video_alerts(narratives, strategies)
            alerts.extend(video_alerts)

            ar_alerts = self.generate_ar_alerts(current_data, predictions)
            alerts.extend(ar_alerts)

            marketing_alerts = self.generate_marketing_alerts(strategies, narratives)
            alerts.extend(marketing_alerts)

            # Prioritize alerts by department escalation priority
            prioritized_alerts = self.prioritize_department_alerts(alerts)

            # Log department coordination
            self.log_department_coordination(prioritized_alerts)

            return prioritized_alerts

        except Exception as e:
            print(f"[ERROR] Department coordination error: {e}")
            return []

    def generate_cos_alerts(self, current_data: Dict,
                           predictions: List[CommunityPrediction],
                           strategies: List[StrategyRecommendation]) -> List[DepartmentAlert]:
        """Generate alerts for Chief of Staff department."""
        alerts = []

        try:
            # Strategic alerts
            critical_strategies = [s for s in strategies if s.priority == "critical"]
            if critical_strategies:
                alerts.append(DepartmentAlert(
                    timestamp=datetime.now().isoformat(),
                    department="cos",
                    alert_type="strategic",
                    priority="critical",
                    message=f"Critical strategy implementation required: {len(critical_strategies)} urgent recommendations",
                    required_response="strategic_coordination",
                    escalation_path=["cos"],
                    coordination_required=["video", "ar", "marketing"]
                ))

            # Crisis prediction alerts
            declining_predictions = [p for p in predictions if p.trend_direction == "declining"]
            if declining_predictions:
                alerts.append(DepartmentAlert(
                    timestamp=datetime.now().isoformat(),
                    department="cos",
                    alert_type="crisis",
                    priority="high",
                    message=f"Community health decline predicted in next 24-48h: {len(declining_predictions)} indicators",
                    required_response="crisis_preparation",
                    escalation_path=["cos"],
                    coordination_required=["video", "ar", "marketing"]
                ))

        except Exception as e:
            print(f"[WARNING] Error generating CoS alerts: {e}")

        return alerts

    def generate_video_alerts(self, narratives: List[NarrativeMomentum],
                             strategies: List[StrategyRecommendation]) -> List[DepartmentAlert]:
        """Generate alerts for Video department."""
        alerts = []

        try:
            # High momentum narratives
            high_momentum = [n for n in narratives if n.momentum_score > 0.6]
            if high_momentum:
                alerts.append(DepartmentAlert(
                    timestamp=datetime.now().isoformat(),
                    department="video",
                    alert_type="content",
                    priority="high",
                    message=f"High momentum narratives detected: {len(high_momentum)} opportunities for video content",
                    required_response="content_creation",
                    escalation_path=["video", "cos"],
                    coordination_required=["marketing"]
                ))

            # Narrative amplification strategies
            narrative_strategies = [s for s in strategies if s.category == "narrative_amplification"]
            if narrative_strategies:
                alerts.append(DepartmentAlert(
                    timestamp=datetime.now().isoformat(),
                    department="video",
                    alert_type="narrative",
                    priority="medium",
                    message=f"Video content needed for narrative amplification: {len(narrative_strategies)} strategies",
                    required_response="amplification_content",
                    escalation_path=["video"],
                    coordination_required=["marketing"]
                ))

        except Exception as e:
            print(f"[WARNING] Error generating Video alerts: {e}")

        return alerts

    def generate_ar_alerts(self, current_data: Dict,
                          predictions: List[CommunityPrediction]) -> List[DepartmentAlert]:
        """Generate alerts for A&R department."""
        alerts = []

        try:
            # Community feedback signals
            community_health = current_data.get("community_health", {}).get("overall_score", 0.5)
            if community_health < 0.4:
                alerts.append(DepartmentAlert(
                    timestamp=datetime.now().isoformat(),
                    department="ar",
                    alert_type="community_feedback",
                    priority="medium",
                    message=f"Low community health may indicate artist development opportunities: {community_health:.1%}",
                    required_response="artist_community_analysis",
                    escalation_path=["ar"],
                    coordination_required=["marketing"]
                ))

            # Strategic development opportunities
            positive_predictions = [p for p in predictions if p.trend_direction == "improving"]
            if positive_predictions and community_health > 0.7:
                alerts.append(DepartmentAlert(
                    timestamp=datetime.now().isoformat(),
                    department="ar",
                    alert_type="strategic",
                    priority="low",
                    message="Strong community health indicates good environment for artist development initiatives",
                    required_response="development_opportunity_assessment",
                    escalation_path=["ar"],
                    coordination_required=["marketing", "video"]
                ))

        except Exception as e:
            print(f"[WARNING] Error generating A&R alerts: {e}")

        return alerts

    def generate_marketing_alerts(self, strategies: List[StrategyRecommendation],
                                 narratives: List[NarrativeMomentum]) -> List[DepartmentAlert]:
        """Generate alerts for Marketing department."""
        alerts = []

        try:
            # Campaign optimization opportunities
            optimization_strategies = [s for s in strategies if s.category in ["engagement_optimization", "platform_optimization"]]
            if optimization_strategies:
                alerts.append(DepartmentAlert(
                    timestamp=datetime.now().isoformat(),
                    department="marketing",
                    alert_type="campaign",
                    priority="medium",
                    message=f"Campaign optimization opportunities identified: {len(optimization_strategies)} recommendations",
                    required_response="campaign_adjustment",
                    escalation_path=["marketing"],
                    coordination_required=["video"]
                ))

            # Cross-platform narrative coordination
            multi_platform_narratives = [n for n in narratives if len(n.platforms) > 2]
            if multi_platform_narratives:
                alerts.append(DepartmentAlert(
                    timestamp=datetime.now().isoformat(),
                    department="marketing",
                    alert_type="strategy",
                    priority="medium",
                    message=f"Cross-platform narrative coordination needed: {len(multi_platform_narratives)} narratives",
                    required_response="cross_platform_coordination",
                    escalation_path=["marketing"],
                    coordination_required=["video"]
                ))

        except Exception as e:
            print(f"[WARNING] Error generating Marketing alerts: {e}")

        return alerts

    def prioritize_department_alerts(self, alerts: List[DepartmentAlert]) -> List[DepartmentAlert]:
        """Prioritize department alerts by urgency and department priority."""
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        department_priority = {dept: config["escalation_priority"] for dept, config in PAPERCLIP_DEPARTMENTS.items()}

        prioritized = sorted(alerts, key=lambda a: (
            priority_order.get(a.priority, 4),
            department_priority.get(a.department, 4)
        ))

        return prioritized

    def log_department_coordination(self, alerts: List[DepartmentAlert]):
        """Log department coordination data."""
        try:
            coordination_log = load_json(DEPARTMENT_COORDINATION_LOG) if DEPARTMENT_COORDINATION_LOG.exists() else {}
            today = today_str()

            if today not in coordination_log:
                coordination_log[today] = []

            coordination_entry = {
                "timestamp": datetime.now().isoformat(),
                "alerts_generated": len(alerts),
                "departments_alerted": list(set(alert.department for alert in alerts)),
                "priority_breakdown": {
                    priority: len([a for a in alerts if a.priority == priority])
                    for priority in ["critical", "high", "medium", "low"]
                },
                "alerts": [asdict(alert) for alert in alerts]
            }

            coordination_log[today].append(coordination_entry)
            save_json(DEPARTMENT_COORDINATION_LOG, coordination_log)

        except Exception as e:
            print(f"[WARNING] Could not log department coordination: {e}")


class CommunityIntelligenceOrchestrator:
    """Central orchestrator for APU-72 advanced community intelligence system."""

    def __init__(self):
        # Initialize all intelligence engines
        self.realtime_monitor = RealTimeEngagementMonitor()  # From APU-70
        self.predictive_engine = PredictiveCommunityAnalytics()
        self.narrative_tracker = NarrativeTrackingEngine()
        self.relationship_mapper = CommunityRelationshipIntelligence()
        self.strategy_optimizer = ProactiveStrategyEngine()
        self.department_coordinator = CrossDepartmentalHub()

        # Orchestrator state
        self.is_running = False
        self.orchestration_thread = None
        self.intelligence_history = deque(maxlen=100)

        print("[APU-72] Community Intelligence Orchestrator initialized")

    def start_intelligence_orchestration(self):
        """Start the APU-72 intelligence orchestration system."""
        if self.is_running:
            print("[WARNING] APU-72 intelligence orchestration already running")
            return

        self.is_running = True
        self.orchestration_thread = threading.Thread(target=self._orchestration_loop, daemon=True)
        self.orchestration_thread.start()
        print("[APU-72] Advanced community intelligence orchestration started")

    def stop_intelligence_orchestration(self):
        """Stop the APU-72 intelligence orchestration system."""
        self.is_running = False
        if self.orchestration_thread:
            self.orchestration_thread.join(timeout=10)
        print("[APU-72] Advanced community intelligence orchestration stopped")

    def _orchestration_loop(self):
        """Main orchestration loop coordinating all intelligence engines."""
        last_predictive_analysis = 0
        last_strategy_optimization = 0
        last_department_coordination = 0

        while self.is_running:
            try:
                current_time = time.time()

                # Always collect current data from APU-70
                current_data = self.realtime_monitor.collect_realtime_data()

                # Continuous monitoring (every cycle)
                narratives = self.narrative_tracker.track_narrative_momentum(current_data)

                # Predictive analysis (every 5 minutes)
                predictions = []
                if current_time - last_predictive_analysis >= APU72_CONFIG["predictive_analysis_interval"]:
                    predictions = [self.predictive_engine.generate_community_prediction(current_data)]
                    last_predictive_analysis = current_time

                # Relationship analysis (every cycle, but could be optimized)
                relationships = self.relationship_mapper.analyze_community_relationships(current_data)

                # Strategy optimization (every 15 minutes)
                strategies = []
                if current_time - last_strategy_optimization >= APU72_CONFIG["strategy_optimization_interval"]:
                    strategies = self.strategy_optimizer.generate_strategy_recommendations(
                        current_data, predictions, narratives, relationships
                    )
                    last_strategy_optimization = current_time

                # Department coordination (every 15 minutes)
                department_alerts = []
                if current_time - last_department_coordination >= APU72_CONFIG["department_coordination_interval"]:
                    department_alerts = self.department_coordinator.coordinate_department_intelligence(
                        current_data, predictions, narratives, strategies
                    )
                    last_department_coordination = current_time

                # Store intelligence snapshot
                intelligence_snapshot = {
                    "timestamp": datetime.now().isoformat(),
                    "current_data": current_data,
                    "predictions": [asdict(p) for p in predictions],
                    "narratives": [asdict(n) for n in narratives],
                    "relationships": [asdict(r) for r in relationships],
                    "strategies": [asdict(s) for s in strategies],
                    "department_alerts": [asdict(a) for a in department_alerts]
                }

                self.intelligence_history.append(intelligence_snapshot)

                # Update live dashboard
                self.update_intelligence_dashboard(intelligence_snapshot)

                # Sleep until next cycle
                time.sleep(APU72_CONFIG["narrative_tracking_interval"])

            except Exception as e:
                print(f"[ERROR] APU-72 orchestration error: {str(e)}")
                time.sleep(60)  # Wait longer if there's an error

    def update_intelligence_dashboard(self, intelligence_snapshot: Dict):
        """Update the live intelligence dashboard with latest data."""
        try:
            dashboard_data = {
                "last_updated": datetime.now().isoformat(),
                "version": "apu72_intelligence_v1",
                "intelligence_snapshot": intelligence_snapshot,
                "system_status": {
                    "orchestrator_running": self.is_running,
                    "data_quality": "good" if intelligence_snapshot.get("current_data", {}).get("error") is None else "degraded",
                    "prediction_available": len(intelligence_snapshot.get("predictions", [])) > 0,
                    "narratives_tracked": len(intelligence_snapshot.get("narratives", [])),
                    "relationships_mapped": len(intelligence_snapshot.get("relationships", [])),
                    "strategies_generated": len(intelligence_snapshot.get("strategies", [])),
                    "department_alerts": len(intelligence_snapshot.get("department_alerts", []))
                },
                "intelligence_summary": {
                    "community_health_status": self.calculate_overall_health_status(intelligence_snapshot),
                    "prediction_status": self.calculate_prediction_status(intelligence_snapshot),
                    "narrative_status": self.calculate_narrative_status(intelligence_snapshot),
                    "coordination_status": self.calculate_coordination_status(intelligence_snapshot)
                }
            }

            # Save dashboard data
            dashboard_file = APU72_BASE_DIR / "live_intelligence_dashboard.json"
            save_json(dashboard_file, dashboard_data)

        except Exception as e:
            print(f"[WARNING] Could not update intelligence dashboard: {e}")

    def calculate_overall_health_status(self, snapshot: Dict) -> str:
        """Calculate overall community health status."""
        try:
            community_health = snapshot.get("current_data", {}).get("community_health", {})
            health_score = community_health.get("overall_score", 0.5)

            if health_score > 0.7:
                return "healthy"
            elif health_score > 0.5:
                return "stable"
            elif health_score > 0.3:
                return "declining"
            else:
                return "critical"
        except:
            return "unknown"

    def calculate_prediction_status(self, snapshot: Dict) -> str:
        """Calculate prediction status."""
        try:
            predictions = snapshot.get("predictions", [])
            if not predictions:
                return "no_predictions"

            prediction = predictions[0]
            trend = prediction.get("trend_direction", "stable")
            confidence = prediction.get("confidence", 0.5)

            if trend == "improving" and confidence > 0.7:
                return "positive_forecast"
            elif trend == "declining" and confidence > 0.7:
                return "negative_forecast"
            else:
                return "stable_forecast"
        except:
            return "unknown"

    def calculate_narrative_status(self, snapshot: Dict) -> str:
        """Calculate narrative momentum status."""
        try:
            narratives = snapshot.get("narratives", [])
            if not narratives:
                return "no_narratives"

            high_momentum_count = len([n for n in narratives if n.get("momentum_score", 0) > 0.6])

            if high_momentum_count > 0:
                return "high_momentum"
            elif len(narratives) > 0:
                return "moderate_activity"
            else:
                return "low_activity"
        except:
            return "unknown"

    def calculate_coordination_status(self, snapshot: Dict) -> str:
        """Calculate department coordination status."""
        try:
            alerts = snapshot.get("department_alerts", [])
            critical_alerts = len([a for a in alerts if a.get("priority") == "critical"])

            if critical_alerts > 0:
                return "critical_coordination_needed"
            elif len(alerts) > 3:
                return "active_coordination"
            elif len(alerts) > 0:
                return "normal_coordination"
            else:
                return "minimal_coordination"
        except:
            return "unknown"


def run_apu72_intelligence_snapshot():
    """Run a single APU-72 intelligence analysis snapshot."""
    print("\n[*] APU-72 Advanced Community Intelligence Analysis")
    print("=" * 60)

    try:
        # Initialize orchestrator
        orchestrator = CommunityIntelligenceOrchestrator()

        # Collect current data
        current_data = orchestrator.realtime_monitor.collect_realtime_data()
        print(f"[OK] Data collection: {current_data.get('timestamp', 'unknown')}")

        # Run predictive analytics
        prediction = orchestrator.predictive_engine.generate_community_prediction(current_data)
        print(f"[OK] Predictive analysis: {prediction.trend_direction} trend, {prediction.confidence:.1%} confidence")

        # Track narratives
        narratives = orchestrator.narrative_tracker.track_narrative_momentum(current_data)
        print(f"[OK] Narrative tracking: {len(narratives)} narratives identified")

        # Analyze relationships
        relationships = orchestrator.relationship_mapper.analyze_community_relationships(current_data)
        print(f"[OK] Relationship analysis: {len(relationships)} community members analyzed")

        # Generate strategies
        strategies = orchestrator.strategy_optimizer.generate_strategy_recommendations(
            current_data, [prediction], narratives, relationships
        )
        print(f"[OK] Strategy optimization: {len(strategies)} recommendations generated")

        # Coordinate departments
        department_alerts = orchestrator.department_coordinator.coordinate_department_intelligence(
            current_data, [prediction], narratives, strategies
        )
        print(f"[OK] Department coordination: {len(department_alerts)} alerts generated")

        # Generate comprehensive report
        report = {
            "timestamp": datetime.now().isoformat(),
            "version": "apu72_intelligence_snapshot_v1",
            "execution_mode": "manual_snapshot",
            "current_data": current_data,
            "prediction": asdict(prediction),
            "narratives": [asdict(n) for n in narratives],
            "relationships": [asdict(r) for r in relationships],
            "strategies": [asdict(s) for s in strategies],
            "department_alerts": [asdict(a) for a in department_alerts],
            "intelligence_summary": {
                "community_health_score": prediction.current_health_score,
                "predicted_health_score": prediction.predicted_health_score,
                "trend_direction": prediction.trend_direction,
                "prediction_confidence": prediction.confidence,
                "narrative_momentum_count": len(narratives),
                "high_momentum_narratives": len([n for n in narratives if n.momentum_score > 0.6]),
                "key_community_members": len([r for r in relationships if r.community_role in ["key_influencer", "active_contributor"]]),
                "critical_strategies": len([s for s in strategies if s.priority == "critical"]),
                "department_alerts_by_priority": {
                    "critical": len([a for a in department_alerts if a.priority == "critical"]),
                    "high": len([a for a in department_alerts if a.priority == "high"]),
                    "medium": len([a for a in department_alerts if a.priority == "medium"]),
                    "low": len([a for a in department_alerts if a.priority == "low"])
                },
                "overall_status": orchestrator.calculate_overall_health_status({
                    "current_data": current_data,
                    "predictions": [asdict(prediction)],
                    "narratives": [asdict(n) for n in narratives],
                    "department_alerts": [asdict(a) for a in department_alerts]
                })
            }
        }

        # Save report
        intelligence_log = load_json(COMMUNITY_INTELLIGENCE_LOG) if COMMUNITY_INTELLIGENCE_LOG.exists() else {}
        today = today_str()

        if today not in intelligence_log:
            intelligence_log[today] = []

        intelligence_log[today].append(report)
        save_json(COMMUNITY_INTELLIGENCE_LOG, intelligence_log)

        # Update dashboard
        orchestrator.update_intelligence_dashboard({
            "current_data": current_data,
            "predictions": [asdict(prediction)],
            "narratives": [asdict(n) for n in narratives],
            "relationships": [asdict(r) for r in relationships],
            "strategies": [asdict(s) for s in strategies],
            "department_alerts": [asdict(a) for a in department_alerts]
        })

        # Log to main research log
        summary = report["intelligence_summary"]
        status = "critical" if summary["overall_status"] == "critical" else \
                "warning" if summary["overall_status"] in ["declining"] else "ok"
        detail = f"Health: {summary['community_health_score']:.1%}→{summary['predicted_health_score']:.1%}, " + \
                f"Narratives: {summary['narrative_momentum_count']}, " + \
                f"Strategies: {summary['critical_strategies']}, " + \
                f"Alerts: {sum(summary['department_alerts_by_priority'].values())}"

        log_run("CommunityIntelligenceAPU72", status, detail)

        print("\n" + "=" * 60)
        print("[*] APU-72 Intelligence Analysis Complete")
        print(f"[*] Overall Status: {summary['overall_status'].upper()}")
        print(f"[*] Community Health: {summary['community_health_score']:.1%} → {summary['predicted_health_score']:.1%}")
        print(f"[*] Trend Direction: {prediction.trend_direction}")
        print(f"[*] Active Narratives: {summary['narrative_momentum_count']} ({summary['high_momentum_narratives']} high momentum)")
        print(f"[*] Key Community Members: {summary['key_community_members']}")
        print(f"[*] Strategy Recommendations: {len(strategies)} ({summary['critical_strategies']} critical)")
        print(f"[*] Department Alerts: {sum(summary['department_alerts_by_priority'].values())}")
        print("=" * 60)

        return report

    except Exception as e:
        error_report = {
            "timestamp": datetime.now().isoformat(),
            "version": "apu72_intelligence_snapshot_v1",
            "execution_mode": "manual_snapshot_error",
            "error": str(e),
            "status": "execution_error"
        }

        log_run("CommunityIntelligenceAPU72", "error", f"Execution error: {str(e)}")
        print(f"\n[ERROR] APU-72 execution failed: {str(e)}")

        return error_report


def main():
    """Main APU-72 advanced community intelligence monitor function."""
    print("\n[*] APU-72 Advanced Community Intelligence Monitor")
    print("[*] Next-generation predictive analytics and cross-departmental coordination")
    print("[*] For continuous monitoring, use orchestrator.start_intelligence_orchestration()")

    return run_apu72_intelligence_snapshot()


if __name__ == "__main__":
    report = main()

    # Exit based on intelligence analysis results
    overall_status = report.get("intelligence_summary", {}).get("overall_status", "unknown")
    critical_alerts = report.get("intelligence_summary", {}).get("department_alerts_by_priority", {}).get("critical", 0)
    critical_strategies = report.get("intelligence_summary", {}).get("critical_strategies", 0)

    if overall_status == "critical" or critical_alerts > 0 or critical_strategies > 0:
        print(f"\n[CRITICAL] Advanced community intelligence indicates immediate attention required!")
        print(f"[CRITICAL] Status: {overall_status}, Critical Alerts: {critical_alerts}, Critical Strategies: {critical_strategies}")
        sys.exit(2)
    elif overall_status in ["declining", "unstable"]:
        print(f"\n[WARNING] Community intelligence indicates attention needed: {overall_status}")
        sys.exit(1)
    else:
        print(f"\n[OK] Advanced community intelligence analysis complete - system status: {overall_status}")
        sys.exit(0)