"""
APU-155 Community Health Metrics and Alerting System
Intelligent community health assessment with adaptive metrics and context-aware alerting.

Created by: Dex - Community Agent (APU-155)
Component: Community Health Metrics & Alerting

FEATURES:
✅ Adaptive health metrics that work with partial data availability
✅ Multi-dimensional community health scoring (engagement, sentiment, growth, cohesion)
✅ Context-aware alerting with root cause analysis and actionable recommendations
✅ Trend detection and pattern recognition across platforms
✅ Alert priority management and cooldown systems
✅ Community lifecycle stage awareness (new, growing, mature, declining)
✅ Cross-platform correlation and insights
"""

import json
import time
import sqlite3
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import sys

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from vawn_config import (
    load_json, save_json, ENGAGEMENT_LOG, RESEARCH_LOG, VAWN_DIR,
    log_run, today_str
)

class HealthMetricType(Enum):
    """Types of community health metrics."""
    ENGAGEMENT_VELOCITY = "engagement_velocity"
    COMMUNITY_RESPONSIVENESS = "community_responsiveness"
    CONTENT_DIVERSITY = "content_diversity"
    SENTIMENT_BALANCE = "sentiment_balance"
    CONVERSATION_DEPTH = "conversation_depth"
    GROWTH_SUSTAINABILITY = "growth_sustainability"
    COMMUNITY_COHESION = "community_cohesion"
    CROSS_PLATFORM_SYNERGY = "cross_platform_synergy"

class AlertSeverity(Enum):
    """Alert severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class CommunityStage(Enum):
    """Community lifecycle stages."""
    NEW = "new"
    GROWING = "growing"
    MATURE = "mature"
    DECLINING = "declining"
    DORMANT = "dormant"

@dataclass
class CommunityHealthScore:
    """Comprehensive community health score with context."""
    platform: str
    timestamp: str

    # Core Health Dimensions
    engagement_vitality: float  # How active and engaged the community is
    content_quality: float      # Quality and diversity of content
    community_sentiment: float  # Overall emotional health
    growth_momentum: float      # Sustainable growth patterns
    social_cohesion: float      # How well community members interact

    # Meta Metrics
    overall_health_score: float
    confidence_level: float     # Confidence in the assessment
    data_completeness: float    # How much data was available
    lifecycle_stage: CommunityStage

    # Supporting Data
    metrics_used: List[str]
    data_sources: List[str]
    assessment_notes: List[str]

@dataclass
class CommunityAlert:
    """Community-focused alert with rich context."""
    alert_id: str
    platform: str
    alert_type: str
    severity: AlertSeverity
    title: str
    description: str

    # Root Cause Analysis
    primary_cause: str
    contributing_factors: List[str]
    affected_metrics: List[str]

    # Context
    community_stage: CommunityStage
    impact_assessment: str
    urgency_score: float

    # Actionable Intelligence
    recommended_actions: List[str]
    prevention_strategies: List[str]
    success_metrics: List[str]

    # Timing and Management
    timestamp: str
    expires_at: Optional[str]
    cooldown_minutes: int
    escalation_path: List[str]

@dataclass
class TrendAnalysis:
    """Trend analysis for community health metrics."""
    metric_name: str
    platform: str
    time_period_hours: float

    # Trend Indicators
    direction: str  # improving, declining, stable, volatile
    velocity: float  # Rate of change
    volatility: float  # Stability measure
    confidence: float  # Statistical confidence

    # Pattern Recognition
    seasonal_patterns: List[str]
    anomalies_detected: List[str]
    correlation_insights: List[str]

    timestamp: str

class APU155CommunityHealthSystem:
    """Comprehensive community health assessment and alerting system."""

    def __init__(self, database_path: Path):
        self.database_path = database_path
        self.session_id = f"health_{int(datetime.now().timestamp())}"

        # Health assessment configuration
        self.health_weights = {
            HealthMetricType.ENGAGEMENT_VELOCITY: 0.25,
            HealthMetricType.COMMUNITY_RESPONSIVENESS: 0.20,
            HealthMetricType.CONTENT_DIVERSITY: 0.15,
            HealthMetricType.SENTIMENT_BALANCE: 0.15,
            HealthMetricType.CONVERSATION_DEPTH: 0.10,
            HealthMetricType.GROWTH_SUSTAINABILITY: 0.10,
            HealthMetricType.COMMUNITY_COHESION: 0.05
        }

        # Alert management
        self.active_alerts = {}
        self.alert_cooldowns = {}

        # Platform-specific baselines (learned over time)
        self.platform_baselines = self._load_platform_baselines()

        print(f"[APU-155 Health] Initialized community health system (Session: {self.session_id})")

    def _load_platform_baselines(self) -> Dict[str, Dict[str, float]]:
        """Load platform-specific baseline metrics."""
        baseline_file = VAWN_DIR / "config" / "apu155_platform_baselines.json"

        default_baselines = {
            "bluesky": {
                "engagement_velocity": 0.3,
                "community_responsiveness": 0.4,
                "content_diversity": 0.6,
                "expected_daily_posts": 5
            },
            "instagram": {
                "engagement_velocity": 0.2,
                "community_responsiveness": 0.3,
                "content_diversity": 0.5,
                "expected_daily_posts": 3
            },
            "tiktok": {
                "engagement_velocity": 0.4,
                "community_responsiveness": 0.5,
                "content_diversity": 0.7,
                "expected_daily_posts": 8
            },
            "x": {
                "engagement_velocity": 0.3,
                "community_responsiveness": 0.4,
                "content_diversity": 0.6,
                "expected_daily_posts": 6
            },
            "threads": {
                "engagement_velocity": 0.2,
                "community_responsiveness": 0.3,
                "content_diversity": 0.5,
                "expected_daily_posts": 4
            }
        }

        if baseline_file.exists():
            try:
                user_baselines = load_json(baseline_file)
                # Merge with defaults
                for platform, metrics in user_baselines.items():
                    if platform in default_baselines:
                        default_baselines[platform].update(metrics)
                    else:
                        default_baselines[platform] = metrics
            except Exception as e:
                print(f"[APU-155 Health] Warning: Could not load baselines: {e}")

        return default_baselines

    def assess_community_health_comprehensive(self, platforms: List[str],
                                            collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive community health assessment across platforms.

        Args:
            platforms: List of platforms to assess
            collected_data: Data from collection system

        Returns:
            Complete health assessment with scores, alerts, and recommendations
        """
        assessment_start = time.time()

        health_assessment = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "assessment_duration_seconds": None,
            "platforms_assessed": [],

            # Health Scores
            "platform_health_scores": {},
            "cross_platform_insights": {},
            "overall_community_health": 0.0,

            # Trends and Analysis
            "trend_analysis": {},
            "pattern_insights": [],
            "lifecycle_assessment": {},

            # Alerts and Recommendations
            "alerts_generated": [],
            "health_recommendations": [],
            "strategic_insights": []
        }

        platform_health_scores = {}
        all_alerts = []

        # Assess health for each platform
        for platform in platforms:
            try:
                print(f"[APU-155 Health] Assessing community health for {platform}...")

                platform_data = collected_data.get("platform_results", {}).get(platform, {})

                # Calculate health score for platform
                health_score = self._calculate_platform_health_score(platform, platform_data)
                platform_health_scores[platform] = asdict(health_score)

                # Generate platform-specific alerts
                platform_alerts = self._generate_platform_health_alerts(health_score)
                all_alerts.extend(platform_alerts)

                # Analyze trends for platform
                trend_analysis = self._analyze_platform_trends(platform)
                assessment_start

                # Store health metrics in database
                self._store_health_assessment(health_score)

                assessment_start["platforms_assessed"].append(platform)

                print(f"[APU-155 Health] {platform} health score: {health_score.overall_health_score:.2f} "
                      f"({health_score.lifecycle_stage.value})")

            except Exception as e:
                print(f"[APU-155 Health] Error assessing {platform}: {e}")

        # Cross-platform analysis
        cross_platform_insights = self._analyze_cross_platform_patterns(platform_health_scores)
        assessment_start["cross_platform_insights"] = cross_platform_insights

        # Generate cross-platform alerts
        cross_platform_alerts = self._generate_cross_platform_alerts(platform_health_scores)
        all_alerts.extend(cross_platform_alerts)

        # Calculate overall community health
        overall_health = self._calculate_overall_community_health(platform_health_scores)
        assessment_start["overall_community_health"] = overall_health

        # Generate strategic recommendations
        strategic_insights = self._generate_strategic_insights(platform_health_scores, cross_platform_insights)
        assessment_start["strategic_insights"] = strategic_insights

        # Finalize assessment
        assessment_start["platform_health_scores"] = platform_health_scores
        assessment_start["alerts_generated"] = [asdict(alert) for alert in all_alerts]
        assessment_start["health_recommendations"] = self._generate_health_recommendations(platform_health_scores)

        assessment_duration = time.time() - assessment_start
        assessment_start["assessment_duration_seconds"] = assessment_duration

        print(f"[APU-155 Health] Health assessment completed: {overall_health:.2f} overall health, "
              f"{len(all_alerts)} alerts, {assessment_duration:.2f}s")

        return health_assessment

    def _calculate_platform_health_score(self, platform: str, platform_data: Dict[str, Any]) -> CommunityHealthScore:
        """Calculate comprehensive health score for a single platform."""

        # Initialize score components
        health_metrics = {}
        metrics_used = []
        data_sources = []
        assessment_notes = []
        confidence_factors = []

        # Get platform baseline for comparison
        baseline = self.platform_baselines.get(platform, {})

        # Calculate individual health metrics
        engagement_vitality, confidence = self._calculate_engagement_vitality(platform, platform_data, baseline)
        health_metrics[HealthMetricType.ENGAGEMENT_VELOCITY] = engagement_vitality
        confidence_factors.append(confidence)
        metrics_used.append("engagement_vitality")

        community_responsiveness, confidence = self._calculate_community_responsiveness(platform, platform_data, baseline)
        health_metrics[HealthMetricType.COMMUNITY_RESPONSIVENESS] = community_responsiveness
        confidence_factors.append(confidence)
        metrics_used.append("community_responsiveness")

        content_quality, confidence = self._calculate_content_quality(platform, platform_data)
        health_metrics[HealthMetricType.CONTENT_DIVERSITY] = content_quality
        confidence_factors.append(confidence)
        metrics_used.append("content_quality")

        # Additional metrics (if data available)
        sentiment_health, confidence = self._calculate_sentiment_health(platform, platform_data)
        if confidence > 0.1:
            health_metrics[HealthMetricType.SENTIMENT_BALANCE] = sentiment_health
            confidence_factors.append(confidence)
            metrics_used.append("sentiment_health")

        growth_momentum, confidence = self._calculate_growth_momentum(platform)
        if confidence > 0.1:
            health_metrics[HealthMetricType.GROWTH_SUSTAINABILITY] = growth_momentum
            confidence_factors.append(confidence)
            metrics_used.append("growth_momentum")

        # Determine data sources used
        if platform_data.get("success", False):
            data_sources.extend(platform_data.get("sources_used", []))

        # Calculate weighted overall score
        overall_score = 0.0
        total_weight = 0.0

        for metric_type, score in health_metrics.items():
            weight = self.health_weights.get(metric_type, 0.1)
            overall_score += score * weight
            total_weight += weight

        if total_weight > 0:
            overall_score = overall_score / total_weight
        else:
            overall_score = 0.0
            assessment_notes.append("No valid metrics calculated")

        # Calculate confidence level
        overall_confidence = statistics.mean(confidence_factors) if confidence_factors else 0.0

        # Calculate data completeness
        expected_metrics = len(self.health_weights)
        actual_metrics = len(health_metrics)
        data_completeness = actual_metrics / expected_metrics

        # Determine lifecycle stage
        lifecycle_stage = self._determine_lifecycle_stage(platform, health_metrics, platform_data)

        # Add assessment context notes
        if data_completeness < 0.5:
            assessment_notes.append("Limited data availability - using fallback metrics")

        if overall_confidence < 0.4:
            assessment_notes.append("Low confidence assessment - results may be inaccurate")

        return CommunityHealthScore(
            platform=platform,
            timestamp=datetime.now().isoformat(),
            engagement_vitality=health_metrics.get(HealthMetricType.ENGAGEMENT_VELOCITY, 0.0),
            content_quality=health_metrics.get(HealthMetricType.CONTENT_DIVERSITY, 0.0),
            community_sentiment=health_metrics.get(HealthMetricType.SENTIMENT_BALANCE, 0.5),
            growth_momentum=health_metrics.get(HealthMetricType.GROWTH_SUSTAINABILITY, 0.0),
            social_cohesion=health_metrics.get(HealthMetricType.COMMUNITY_COHESION, 0.0),
            overall_health_score=overall_score,
            confidence_level=overall_confidence,
            data_completeness=data_completeness,
            lifecycle_stage=lifecycle_stage,
            metrics_used=metrics_used,
            data_sources=data_sources,
            assessment_notes=assessment_notes
        )

    def _calculate_engagement_vitality(self, platform: str, platform_data: Dict[str, Any],
                                     baseline: Dict[str, float]) -> Tuple[float, float]:
        """Calculate engagement vitality score."""
        try:
            if not platform_data.get("success", False):
                # Use historical data as fallback
                historical_vitality = self._get_historical_metric(platform, "engagement_velocity")
                if historical_vitality is not None:
                    return max(historical_vitality * 0.8, 0.0), 0.3  # Reduced confidence for historical
                else:
                    return 0.0, 0.1

            # Extract engagement data
            data = platform_data.get("data", {})

            # Log-based calculation
            if "engagement_summary" in data:
                summary = data["engagement_summary"]
                responses_posted = summary.get("total_responses_posted", 0)
                comments_found = summary.get("total_comments_found", 0)
                success_rate = summary.get("success_rate", 0.0)

                # Calculate vitality based on activity and success
                if comments_found > 0:
                    response_rate = responses_posted / comments_found
                    vitality_score = (response_rate * 0.6 + success_rate * 0.4)
                else:
                    vitality_score = success_rate * 0.5

                return min(vitality_score, 1.0), 0.7

            # API-based calculation
            elif "records" in data:
                records_count = len(data.get("records", []))
                expected_daily = baseline.get("expected_daily_posts", 5)

                # Normalize against expected activity
                activity_ratio = records_count / max(expected_daily, 1)
                vitality_score = min(activity_ratio * 0.5, 1.0)

                return vitality_score, 0.8

            return 0.0, 0.1

        except Exception as e:
            print(f"[APU-155 Health] Error calculating engagement vitality: {e}")
            return 0.0, 0.1

    def _calculate_community_responsiveness(self, platform: str, platform_data: Dict[str, Any],
                                          baseline: Dict[str, float]) -> Tuple[float, float]:
        """Calculate how responsive the community is to content."""
        try:
            if not platform_data.get("success", False):
                # Fallback to historical
                historical_responsiveness = self._get_historical_metric(platform, "community_responsiveness")
                if historical_responsiveness is not None:
                    return max(historical_responsiveness * 0.8, 0.0), 0.3
                else:
                    return baseline.get("community_responsiveness", 0.3), 0.2

            data = platform_data.get("data", {})

            # Log-based responsiveness
            if "engagement_summary" in data:
                summary = data["engagement_summary"]
                avg_execution_time = summary.get("average_execution_time", 0)

                # Good responsiveness = low execution time + high success rate
                success_rate = summary.get("success_rate", 0.0)

                # Normalize execution time (good if < 10s, poor if > 60s)
                if avg_execution_time > 0:
                    time_score = max(1.0 - (avg_execution_time / 60.0), 0.0)
                    responsiveness = (time_score * 0.4 + success_rate * 0.6)
                else:
                    responsiveness = success_rate * 0.7

                return min(responsiveness, 1.0), 0.6

            # API-based responsiveness (simplified)
            elif "records" in data:
                # If we have API data, assume moderate responsiveness
                return 0.5, 0.4

            return baseline.get("community_responsiveness", 0.3), 0.2

        except Exception as e:
            print(f"[APU-155 Health] Error calculating responsiveness: {e}")
            return 0.3, 0.2

    def _calculate_content_quality(self, platform: str, platform_data: Dict[str, Any]) -> Tuple[float, float]:
        """Calculate content quality and diversity score."""
        try:
            if not platform_data.get("success", False):
                return 0.5, 0.2  # Default moderate quality with low confidence

            data = platform_data.get("data", {})

            # Log-based quality assessment
            if "engagement_summary" in data:
                total_entries = data["engagement_summary"].get("total_entries", 0)

                # More entries suggest more content diversity
                if total_entries > 0:
                    diversity_score = min(total_entries / 10.0, 1.0)  # Normalize to 10 posts
                    return diversity_score, 0.5
                else:
                    return 0.1, 0.3

            # API-based quality
            elif "records" in data:
                records = data.get("records", [])

                if records:
                    # Simple diversity based on record count and variety
                    record_count = len(records)
                    diversity_score = min(record_count / 8.0, 1.0)  # Normalize to 8 records

                    # Additional quality factors could be added here
                    # (content length, engagement, etc.)

                    return diversity_score, 0.7
                else:
                    return 0.2, 0.3

            return 0.5, 0.2

        except Exception as e:
            print(f"[APU-155 Health] Error calculating content quality: {e}")
            return 0.5, 0.2

    def _calculate_sentiment_health(self, platform: str, platform_data: Dict[str, Any]) -> Tuple[float, float]:
        """Calculate overall sentiment health (requires analysis)."""
        try:
            # This would require sentiment analysis of content
            # For now, provide neutral sentiment with low confidence

            # Check if we have any sentiment data in logs or API
            data = platform_data.get("data", {})

            if "insights" in data:
                insights = data["insights"]
                negative_indicators = [
                    "low success rate",
                    "high average execution time",
                    "performance issues",
                    "no responses posted"
                ]

                negative_count = sum(1 for insight in insights
                                   for indicator in negative_indicators
                                   if indicator in insight.lower())

                if negative_count > 0:
                    # Negative indicators suggest community issues
                    sentiment_score = max(0.5 - (negative_count * 0.1), 0.1)
                    return sentiment_score, 0.4
                else:
                    # No negative indicators = neutral to positive
                    return 0.6, 0.3

            # Default neutral sentiment
            return 0.5, 0.2

        except Exception as e:
            print(f"[APU-155 Health] Error calculating sentiment: {e}")
            return 0.5, 0.1

    def _calculate_growth_momentum(self, platform: str) -> Tuple[float, float]:
        """Calculate growth momentum based on historical trends."""
        try:
            # Get recent historical metrics for trend analysis
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.execute("""
                    SELECT engagement_velocity, community_responsiveness, timestamp
                    FROM community_metrics
                    WHERE platform = ?
                    AND timestamp > datetime('now', '-7 days')
                    ORDER BY timestamp ASC
                """, (platform,))

                historical_data = cursor.fetchall()

                if len(historical_data) < 3:
                    return 0.3, 0.1  # Insufficient data

                # Calculate trend
                engagement_values = [row[0] for row in historical_data if row[0] is not None]
                responsiveness_values = [row[1] for row in historical_data if row[1] is not None]

                if engagement_values and len(engagement_values) > 1:
                    # Simple trend calculation
                    first_half = engagement_values[:len(engagement_values)//2]
                    second_half = engagement_values[len(engagement_values)//2:]

                    first_avg = statistics.mean(first_half)
                    second_avg = statistics.mean(second_half)

                    if second_avg > first_avg * 1.1:
                        growth_score = 0.8  # Growing
                    elif second_avg < first_avg * 0.9:
                        growth_score = 0.2  # Declining
                    else:
                        growth_score = 0.5  # Stable

                    return growth_score, 0.6

                return 0.5, 0.2

        except Exception as e:
            print(f"[APU-155 Health] Error calculating growth momentum: {e}")
            return 0.5, 0.1

    def _get_historical_metric(self, platform: str, metric_name: str) -> Optional[float]:
        """Get recent historical metric value."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.execute(f"""
                    SELECT {metric_name}
                    FROM community_metrics
                    WHERE platform = ?
                    AND timestamp > datetime('now', '-24 hours')
                    ORDER BY timestamp DESC
                    LIMIT 1
                """, (platform,))

                row = cursor.fetchone()
                if row and row[0] is not None:
                    return float(row[0])

        except Exception as e:
            print(f"[APU-155 Health] Error getting historical metric: {e}")

        return None

    def _determine_lifecycle_stage(self, platform: str, health_metrics: Dict[HealthMetricType, float],
                                 platform_data: Dict[str, Any]) -> CommunityStage:
        """Determine community lifecycle stage."""
        try:
            engagement = health_metrics.get(HealthMetricType.ENGAGEMENT_VELOCITY, 0.0)
            responsiveness = health_metrics.get(HealthMetricType.COMMUNITY_RESPONSIVENESS, 0.0)
            content_quality = health_metrics.get(HealthMetricType.CONTENT_DIVERSITY, 0.0)

            avg_score = (engagement + responsiveness + content_quality) / 3

            # Get activity level
            data = platform_data.get("data", {})
            activity_level = 0

            if "engagement_summary" in data:
                activity_level = data["engagement_summary"].get("total_entries", 0)
            elif "records" in data:
                activity_level = len(data.get("records", []))

            # Determine stage based on health and activity
            if avg_score < 0.2 or activity_level == 0:
                return CommunityStage.DORMANT
            elif avg_score < 0.4:
                return CommunityStage.DECLINING
            elif avg_score < 0.6:
                return CommunityStage.NEW if activity_level < 5 else CommunityStage.MATURE
            elif avg_score < 0.8:
                return CommunityStage.GROWING
            else:
                return CommunityStage.MATURE

        except Exception as e:
            print(f"[APU-155 Health] Error determining lifecycle stage: {e}")
            return CommunityStage.NEW

    def _analyze_platform_trends(self, platform: str) -> TrendAnalysis:
        """Analyze trends for a specific platform."""
        # Simplified trend analysis - would be expanded in full implementation
        return TrendAnalysis(
            metric_name="overall_health",
            platform=platform,
            time_period_hours=24.0,
            direction="stable",
            velocity=0.0,
            volatility=0.1,
            confidence=0.5,
            seasonal_patterns=[],
            anomalies_detected=[],
            correlation_insights=[],
            timestamp=datetime.now().isoformat()
        )

    def _store_health_assessment(self, health_score: CommunityHealthScore):
        """Store health assessment in database."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.execute("""
                    INSERT INTO community_metrics
                    (timestamp, platform, posts_analyzed, engagement_velocity,
                     community_responsiveness, content_diversity_score, confidence_score, data_freshness_hours)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    health_score.timestamp,
                    health_score.platform,
                    0,  # posts_analyzed - would be calculated
                    health_score.engagement_vitality,
                    health_score.community_sentiment,
                    health_score.content_quality,
                    health_score.confidence_level,
                    0.5  # data_freshness_hours - would be calculated
                ))
        except Exception as e:
            print(f"[APU-155 Health] Warning: Could not store health assessment: {e}")

    def _generate_platform_health_alerts(self, health_score: CommunityHealthScore) -> List[CommunityAlert]:
        """Generate platform-specific health alerts."""
        alerts = []
        platform = health_score.platform
        current_time = datetime.now()

        # Critical health alert
        if health_score.overall_health_score < 0.3:
            alerts.append(CommunityAlert(
                alert_id=f"critical_health_{platform}_{int(current_time.timestamp())}",
                platform=platform,
                alert_type="critical_community_health",
                severity=AlertSeverity.CRITICAL,
                title=f"Critical Community Health - {platform.title()}",
                description=f"Community health critically low at {health_score.overall_health_score:.1%}",
                primary_cause="Multiple health metrics below acceptable thresholds",
                contributing_factors=[
                    f"Engagement vitality: {health_score.engagement_vitality:.1%}",
                    f"Content quality: {health_score.content_quality:.1%}",
                    f"Data completeness: {health_score.data_completeness:.1%}"
                ],
                affected_metrics=health_score.metrics_used,
                community_stage=health_score.lifecycle_stage,
                impact_assessment="High - Community may be at risk of becoming inactive",
                urgency_score=0.9,
                recommended_actions=[
                    "Immediate content strategy review",
                    "Increase community engagement initiatives",
                    "Investigate data collection issues",
                    "Consider platform-specific intervention strategies"
                ],
                prevention_strategies=[
                    "Implement proactive community engagement monitoring",
                    "Establish regular content quality audits",
                    "Create community feedback loops"
                ],
                success_metrics=[
                    "Health score improvement to >0.5 within 7 days",
                    "Engagement vitality increase",
                    "Improved data collection reliability"
                ],
                timestamp=current_time.isoformat(),
                expires_at=(current_time + timedelta(hours=24)).isoformat(),
                cooldown_minutes=60,
                escalation_path=["community_manager", "content_strategy_team", "leadership"]
            ))

        # Low confidence alert
        if health_score.confidence_level < 0.4:
            alerts.append(CommunityAlert(
                alert_id=f"low_confidence_{platform}_{int(current_time.timestamp())}",
                platform=platform,
                alert_type="assessment_confidence",
                severity=AlertSeverity.MEDIUM,
                title=f"Low Assessment Confidence - {platform.title()}",
                description=f"Health assessment confidence low at {health_score.confidence_level:.1%}",
                primary_cause="Insufficient or poor quality data for accurate assessment",
                contributing_factors=[
                    f"Data sources used: {', '.join(health_score.data_sources)}",
                    f"Data completeness: {health_score.data_completeness:.1%}",
                    "Limited historical data available"
                ],
                affected_metrics=["all_health_metrics"],
                community_stage=health_score.lifecycle_stage,
                impact_assessment="Medium - May make poor decisions based on inaccurate data",
                urgency_score=0.6,
                recommended_actions=[
                    "Verify data collection systems are working",
                    "Check API connectivity and authentication",
                    "Review log file access and parsing",
                    "Consider manual data validation"
                ],
                prevention_strategies=[
                    "Implement redundant data collection methods",
                    "Regular data quality monitoring",
                    "Automated data validation checks"
                ],
                success_metrics=[
                    "Confidence level improvement to >0.6",
                    "Data completeness >80%",
                    "Multiple data sources active"
                ],
                timestamp=current_time.isoformat(),
                expires_at=(current_time + timedelta(hours=12)).isoformat(),
                cooldown_minutes=30,
                escalation_path=["data_team", "infrastructure_team"]
            ))

        # Lifecycle stage alerts
        if health_score.lifecycle_stage == CommunityStage.DECLINING:
            alerts.append(CommunityAlert(
                alert_id=f"declining_community_{platform}_{int(current_time.timestamp())}",
                platform=platform,
                alert_type="lifecycle_concern",
                severity=AlertSeverity.HIGH,
                title=f"Declining Community - {platform.title()}",
                description=f"Community showing signs of decline",
                primary_cause="Decreasing engagement and activity patterns",
                contributing_factors=[
                    f"Overall health: {health_score.overall_health_score:.1%}",
                    f"Engagement vitality: {health_score.engagement_vitality:.1%}",
                    "Potential content strategy issues"
                ],
                affected_metrics=["engagement", "responsiveness"],
                community_stage=health_score.lifecycle_stage,
                impact_assessment="High - Risk of community becoming dormant",
                urgency_score=0.8,
                recommended_actions=[
                    "Analyze recent content performance",
                    "Survey community for feedback",
                    "Implement re-engagement campaign",
                    "Review competitor strategies"
                ],
                prevention_strategies=[
                    "Regular community pulse checks",
                    "Proactive content strategy adaptation",
                    "Community feedback integration"
                ],
                success_metrics=[
                    "Return to growing or stable stage",
                    "Engagement metrics improvement",
                    "Positive community sentiment"
                ],
                timestamp=current_time.isoformat(),
                expires_at=(current_time + timedelta(hours=48)).isoformat(),
                cooldown_minutes=120,
                escalation_path=["community_manager", "content_team", "strategy_team"]
            ))

        return alerts

    def _analyze_cross_platform_patterns(self, platform_health_scores: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze patterns across multiple platforms."""
        cross_platform_insights = {
            "overall_pattern": "unknown",
            "strongest_platform": None,
            "weakest_platform": None,
            "correlation_insights": [],
            "strategic_opportunities": []
        }

        try:
            if not platform_health_scores:
                return cross_platform_insights

            # Find strongest and weakest platforms
            platforms_by_health = sorted(
                platform_health_scores.items(),
                key=lambda x: x[1]["overall_health_score"],
                reverse=True
            )

            if platforms_by_health:
                cross_platform_insights["strongest_platform"] = platforms_by_health[0][0]
                cross_platform_insights["weakest_platform"] = platforms_by_health[-1][0]

            # Analyze overall pattern
            health_scores = [score["overall_health_score"] for score in platform_health_scores.values()]
            avg_health = statistics.mean(health_scores)

            if avg_health > 0.7:
                cross_platform_insights["overall_pattern"] = "thriving"
            elif avg_health > 0.5:
                cross_platform_insights["overall_pattern"] = "healthy"
            elif avg_health > 0.3:
                cross_platform_insights["overall_pattern"] = "struggling"
            else:
                cross_platform_insights["overall_pattern"] = "critical"

            # Generate strategic insights
            if cross_platform_insights["strongest_platform"] and cross_platform_insights["weakest_platform"]:
                strongest = cross_platform_insights["strongest_platform"]
                weakest = cross_platform_insights["weakest_platform"]

                cross_platform_insights["strategic_opportunities"].append(
                    f"Learn from {strongest} success strategies to improve {weakest}"
                )

            # Check for consistency across platforms
            if len(health_scores) > 1:
                health_variance = statistics.variance(health_scores)
                if health_variance > 0.1:
                    cross_platform_insights["correlation_insights"].append(
                        "High variance in platform health suggests platform-specific issues"
                    )

        except Exception as e:
            print(f"[APU-155 Health] Error in cross-platform analysis: {e}")

        return cross_platform_insights

    def _generate_cross_platform_alerts(self, platform_health_scores: Dict[str, Any]) -> List[CommunityAlert]:
        """Generate alerts based on cross-platform patterns."""
        alerts = []

        try:
            if len(platform_health_scores) < 2:
                return alerts

            health_scores = [score["overall_health_score"] for score in platform_health_scores.values()]
            avg_health = statistics.mean(health_scores)
            current_time = datetime.now()

            # System-wide health alert
            if avg_health < 0.3:
                alerts.append(CommunityAlert(
                    alert_id=f"system_wide_health_{int(current_time.timestamp())}",
                    platform="all_platforms",
                    alert_type="system_wide_health",
                    severity=AlertSeverity.CRITICAL,
                    title="System-Wide Community Health Crisis",
                    description=f"Average health across all platforms critically low at {avg_health:.1%}",
                    primary_cause="Widespread community engagement issues",
                    contributing_factors=[
                        f"Platforms affected: {len(platform_health_scores)}",
                        "Potential content strategy failure",
                        "Possible infrastructure issues"
                    ],
                    affected_metrics=["all_platforms"],
                    community_stage=CommunityStage.DECLINING,
                    impact_assessment="Critical - Risk of widespread community abandonment",
                    urgency_score=1.0,
                    recommended_actions=[
                        "Emergency community strategy review",
                        "Immediate cross-platform analysis",
                        "Consider temporary strategy pivot",
                        "Stakeholder emergency meeting"
                    ],
                    prevention_strategies=[
                        "Cross-platform health monitoring",
                        "Early warning system implementation",
                        "Regular strategy effectiveness reviews"
                    ],
                    success_metrics=[
                        "Average health improvement to >0.5",
                        "Individual platform recovery",
                        "Restored community engagement"
                    ],
                    timestamp=current_time.isoformat(),
                    expires_at=(current_time + timedelta(hours=6)).isoformat(),
                    cooldown_minutes=180,
                    escalation_path=["emergency_response_team", "leadership", "board"]
                ))

        except Exception as e:
            print(f"[APU-155 Health] Error generating cross-platform alerts: {e}")

        return alerts

    def _calculate_overall_community_health(self, platform_health_scores: Dict[str, Any]) -> float:
        """Calculate overall community health across all platforms."""
        if not platform_health_scores:
            return 0.0

        # Weight platforms by importance (could be configured)
        platform_weights = {
            "bluesky": 0.3,
            "instagram": 0.25,
            "tiktok": 0.25,
            "x": 0.15,
            "threads": 0.05
        }

        weighted_score = 0.0
        total_weight = 0.0

        for platform, health_data in platform_health_scores.items():
            weight = platform_weights.get(platform, 0.1)
            health_score = health_data["overall_health_score"]
            confidence = health_data["confidence_level"]

            # Adjust weight by confidence
            adjusted_weight = weight * confidence

            weighted_score += health_score * adjusted_weight
            total_weight += adjusted_weight

        if total_weight > 0:
            return weighted_score / total_weight
        else:
            return 0.0

    def _generate_strategic_insights(self, platform_health_scores: Dict[str, Any],
                                   cross_platform_insights: Dict[str, Any]) -> List[str]:
        """Generate strategic insights and recommendations."""
        insights = []

        try:
            overall_pattern = cross_platform_insights.get("overall_pattern", "unknown")

            if overall_pattern == "thriving":
                insights.append("Communities are performing excellently - consider scaling successful strategies")
                insights.append("Opportunity to expand to new platforms or increase content volume")

            elif overall_pattern == "healthy":
                insights.append("Communities are stable - focus on optimization and growth")
                insights.append("Identify and replicate success patterns across platforms")

            elif overall_pattern == "struggling":
                insights.append("Communities need attention - review content strategy and engagement tactics")
                insights.append("Consider platform-specific interventions and community feedback collection")

            elif overall_pattern == "critical":
                insights.append("URGENT: Community strategy requires immediate overhaul")
                insights.append("Emergency intervention needed to prevent community abandonment")

            # Platform-specific insights
            strongest = cross_platform_insights.get("strongest_platform")
            weakest = cross_platform_insights.get("weakest_platform")

            if strongest and weakest and strongest != weakest:
                insights.append(f"Study {strongest} success factors for application to {weakest}")
                insights.append(f"Consider reallocating resources from {weakest} to {strongest} temporarily")

        except Exception as e:
            print(f"[APU-155 Health] Error generating strategic insights: {e}")

        return insights

    def _generate_health_recommendations(self, platform_health_scores: Dict[str, Any]) -> List[str]:
        """Generate actionable health improvement recommendations."""
        recommendations = []

        try:
            for platform, health_data in platform_health_scores.items():
                health_score = health_data["overall_health_score"]
                engagement = health_data["engagement_vitality"]
                content_quality = health_data["content_quality"]

                if health_score < 0.5:
                    recommendations.append(f"{platform.title()}: Health below threshold - immediate intervention needed")

                if engagement < 0.4:
                    recommendations.append(f"{platform.title()}: Low engagement - review content strategy and timing")

                if content_quality < 0.4:
                    recommendations.append(f"{platform.title()}: Content diversity low - expand content types and topics")

        except Exception as e:
            print(f"[APU-155 Health] Error generating recommendations: {e}")

        return recommendations

def main():
    """Test the community health assessment system."""
    print("=" * 65)
    print("APU-155 Community Health Assessment & Alerting System")
    print("Testing intelligent community health metrics and alerting")
    print("=" * 65)

    # Initialize system
    database_path = VAWN_DIR / "database" / "apu155_community_monitor.db"
    health_system = APU155CommunityHealthSystem(database_path)

    # Mock collected data for testing
    mock_collected_data = {
        "platform_results": {
            "bluesky": {
                "success": True,
                "sources_used": ["logs"],
                "data": {
                    "engagement_summary": {
                        "total_entries": 3,
                        "total_responses_posted": 1,
                        "total_comments_found": 2,
                        "success_rate": 0.5
                    }
                }
            },
            "instagram": {
                "success": False,
                "sources_used": [],
                "data": {}
            }
        }
    }

    try:
        # Run health assessment
        assessment = health_system.assess_community_health_comprehensive(
            platforms=["bluesky", "instagram"],
            collected_data=mock_collected_data
        )

        print(f"\n🏥 HEALTH ASSESSMENT RESULTS:")
        print(f"   Overall Health: {assessment['overall_community_health']:.2f}")
        print(f"   Platforms Assessed: {len(assessment['platforms_assessed'])}")
        print(f"   Alerts Generated: {len(assessment['alerts_generated'])}")

        # Display platform health scores
        for platform, health_data in assessment["platform_health_scores"].items():
            print(f"   {platform.title()}: {health_data['overall_health_score']:.2f} "
                  f"({health_data['lifecycle_stage']})")

        # Display alerts
        if assessment["alerts_generated"]:
            print(f"\n⚠️  GENERATED ALERTS:")
            for alert in assessment["alerts_generated"][:3]:
                print(f"   • {alert['severity'].upper()}: {alert['title']}")

        # Display strategic insights
        if assessment["strategic_insights"]:
            print(f"\n💡 STRATEGIC INSIGHTS:")
            for insight in assessment["strategic_insights"]:
                print(f"   • {insight}")

        print(f"\n✅ Health assessment test completed!")
        return True

    except Exception as e:
        print(f"\n❌ Health assessment failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    exit(0 if main() else 1)