"""
apu112_engagement_metrics_aggregator.py — APU-112 Real-Time Engagement Metrics Aggregation System

Real-time engagement metrics collection, cross-platform data normalization, trend analysis,
performance correlation system, and growth funnel tracking.

Created by: Backend API Agent (APU-112)
Features:
- Real-time metrics collection API
- Cross-platform data normalization
- Engagement trend analysis
- Performance correlation (hashtag usage vs actual engagement)
- Growth funnel tracking
- Database integration for historical analysis
- Backward compatibility with existing monitoring system
"""

import json
import sys
import sqlite3
import threading
import time
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from flask import Flask, jsonify, request, render_template_string
import numpy as np
from collections import defaultdict, deque
import requests

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import (
    load_json, save_json, VAWN_DIR, ENGAGEMENT_LOG, METRICS_LOG,
    log_run, today_str, get_anthropic_client
)

# APU-112 Configuration
APU112_DB = VAWN_DIR / "database" / "apu112_engagement_metrics.db"
APU112_CONFIG = VAWN_DIR / "config" / "apu112_metrics_config.json"
APU112_LOG = VAWN_DIR / "research" / "apu112_metrics_log.json"
HASHTAG_DIR = VAWN_DIR / "Social_Media_Exports" / "Trending_Hashtags"

# Ensure directories exist
APU112_DB.parent.mkdir(exist_ok=True)
APU112_CONFIG.parent.mkdir(exist_ok=True)

# Default configuration
DEFAULT_CONFIG = {
    "collection": {
        "real_time_interval_seconds": 60,  # Collect metrics every minute
        "batch_size": 100,  # Process up to 100 metrics per batch
        "platforms": ["instagram", "tiktok", "x", "threads", "bluesky"],
        "enable_real_time_alerts": True,
        "enable_trend_analysis": True
    },
    "normalization": {
        "enable_cross_platform_normalization": True,
        "weight_factors": {
            "instagram": {"likes": 1.0, "comments": 3.0, "saves": 5.0, "shares": 4.0},
            "tiktok": {"likes": 1.0, "comments": 4.0, "shares": 6.0, "views": 0.1},
            "x": {"likes": 1.0, "retweets": 3.0, "replies": 4.0, "views": 0.05},
            "threads": {"likes": 1.0, "comments": 3.0, "reposts": 2.5},
            "bluesky": {"likes": 1.0, "reposts": 2.0, "replies": 3.0}
        }
    },
    "analysis": {
        "trend_detection_window_hours": 24,
        "correlation_analysis_days": 7,
        "growth_funnel_stages": ["awareness", "engagement", "conversion"],
        "alert_thresholds": {
            "engagement_drop_percent": 20,
            "spam_spike_threshold": 50,
            "viral_potential_score": 0.8
        }
    },
    "performance": {
        "cache_size": 1000,
        "max_historical_days": 90,
        "enable_predictive_analytics": True
    }
}

@dataclass
class MetricPoint:
    """Individual metric data point."""
    timestamp: str
    platform: str
    post_id: str
    metric_type: str  # likes, comments, saves, shares, views
    value: int
    normalized_value: float
    hashtags: List[str]
    post_caption: str

@dataclass
class EngagementSnapshot:
    """Complete engagement snapshot for analysis."""
    timestamp: str
    platform: str
    post_id: str
    metrics: Dict[str, int]  # raw metrics
    normalized_score: float
    hashtag_count: int
    hashtag_performance_score: float
    engagement_velocity: float  # change rate per hour
    viral_potential_score: float

@dataclass
class TrendAnalysis:
    """Trend analysis results."""
    timestamp: str
    platform: str
    trend_type: str  # growth, decline, stable, volatile
    confidence_score: float
    key_metrics: Dict[str, float]
    recommendations: List[str]

@dataclass
class PerformanceCorrelation:
    """Hashtag performance correlation analysis."""
    hashtag: str
    usage_count: int
    avg_engagement_score: float
    performance_trend: str  # improving, declining, stable
    platform_performance: Dict[str, float]
    correlation_confidence: float

class EngagementMetricsDB:
    """SQLite database handler for engagement metrics."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    post_id TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    value INTEGER NOT NULL,
                    normalized_value REAL NOT NULL,
                    hashtags TEXT,
                    post_caption TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Engagement snapshots table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS engagement_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    post_id TEXT NOT NULL,
                    raw_metrics TEXT NOT NULL,
                    normalized_score REAL NOT NULL,
                    hashtag_count INTEGER NOT NULL,
                    hashtag_performance_score REAL NOT NULL,
                    engagement_velocity REAL NOT NULL,
                    viral_potential_score REAL NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Trend analysis table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trend_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    trend_type TEXT NOT NULL,
                    confidence_score REAL NOT NULL,
                    key_metrics TEXT NOT NULL,
                    recommendations TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Hashtag performance table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hashtag_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hashtag TEXT NOT NULL,
                    usage_count INTEGER NOT NULL,
                    avg_engagement_score REAL NOT NULL,
                    performance_trend TEXT NOT NULL,
                    platform_performance TEXT NOT NULL,
                    correlation_confidence REAL NOT NULL,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(hashtag)
                )
            """)

            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_platform ON metrics(platform)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp ON engagement_snapshots(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trends_platform ON trend_analysis(platform)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_hashtag_performance ON hashtag_performance(hashtag)")

            conn.commit()

    def insert_metric(self, metric: MetricPoint):
        """Insert a metric point."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO metrics (timestamp, platform, post_id, metric_type,
                                   value, normalized_value, hashtags, post_caption)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metric.timestamp, metric.platform, metric.post_id, metric.metric_type,
                metric.value, metric.normalized_value, json.dumps(metric.hashtags), metric.post_caption
            ))
            conn.commit()

    def insert_engagement_snapshot(self, snapshot: EngagementSnapshot):
        """Insert an engagement snapshot."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO engagement_snapshots (timestamp, platform, post_id, raw_metrics,
                                                normalized_score, hashtag_count, hashtag_performance_score,
                                                engagement_velocity, viral_potential_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot.timestamp, snapshot.platform, snapshot.post_id, json.dumps(snapshot.metrics),
                snapshot.normalized_score, snapshot.hashtag_count, snapshot.hashtag_performance_score,
                snapshot.engagement_velocity, snapshot.viral_potential_score
            ))
            conn.commit()

    def get_recent_metrics(self, hours: int = 24, platform: Optional[str] = None) -> List[Dict]:
        """Get recent metrics data."""
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            query = """
                SELECT * FROM metrics
                WHERE timestamp > ?
            """
            params = [cutoff]

            if platform:
                query += " AND platform = ?"
                params.append(platform)

            query += " ORDER BY timestamp DESC"

            cursor.execute(query, params)
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_engagement_trends(self, days: int = 7, platform: Optional[str] = None) -> List[Dict]:
        """Get engagement trend data."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            query = """
                SELECT * FROM engagement_snapshots
                WHERE timestamp > ?
            """
            params = [cutoff]

            if platform:
                query += " AND platform = ?"
                params.append(platform)

            query += " ORDER BY timestamp DESC"

            cursor.execute(query, params)
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

class APU112EngagementAggregator:
    """Real-time engagement metrics aggregation system."""

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.db = EngagementMetricsDB(APU112_DB)
        self.client = get_anthropic_client()
        self.running = False
        self.real_time_cache = deque(maxlen=self.config["performance"]["cache_size"])
        self.trend_analyzer = TrendAnalyzer(self.config)
        self.correlation_analyzer = CorrelationAnalyzer(self.config)

    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration with fallback to defaults."""
        if config_path and Path(config_path).exists():
            config = load_json(Path(config_path))
        elif APU112_CONFIG.exists():
            config = load_json(APU112_CONFIG)
        else:
            config = DEFAULT_CONFIG
            save_json(APU112_CONFIG, DEFAULT_CONFIG)
        return config

    def collect_real_time_metrics(self) -> List[MetricPoint]:
        """Collect real-time metrics from all platforms."""
        metrics = []

        # Collect from existing logs
        metrics.extend(self._collect_from_engagement_log())
        metrics.extend(self._collect_from_metrics_log())
        metrics.extend(self._collect_from_hashtag_data())

        return metrics

    def _collect_from_engagement_log(self) -> List[MetricPoint]:
        """Collect metrics from engagement log."""
        metrics = []
        try:
            engagement_log = load_json(ENGAGEMENT_LOG)
            history = engagement_log.get("history", [])

            # Process recent entries (last hour)
            cutoff = (datetime.now() - timedelta(hours=1)).isoformat()

            for entry in history:
                if entry.get("date", "") > cutoff:
                    # Extract metrics from engagement data
                    platform = entry.get("platform", "unknown")
                    post_id = entry.get("post_id", f"engagement_{entry.get('date', '')}")

                    # Create metric points for comment engagement
                    if entry.get("comment"):
                        metric = MetricPoint(
                            timestamp=entry["date"],
                            platform=platform,
                            post_id=post_id,
                            metric_type="comments",
                            value=1,  # One comment
                            normalized_value=self._normalize_metric_value("comments", 1, platform),
                            hashtags=[],
                            post_caption=entry.get("comment", "")[:200]
                        )
                        metrics.append(metric)

        except Exception as e:
            log_run("APU112Aggregator", "warning", f"Engagement log collection failed: {e}")

        return metrics

    def _collect_from_metrics_log(self) -> List[MetricPoint]:
        """Collect metrics from metrics log."""
        metrics = []
        try:
            metrics_log = load_json(METRICS_LOG)

            # Process recent entries
            today = today_str()
            for image, dates in metrics_log.items():
                if today in dates:
                    for platform, data in dates[today].items():
                        if isinstance(data, dict):
                            post_id = f"{image}_{today}_{platform}"
                            timestamp = datetime.now().isoformat()

                            # Create metric points for each metric type
                            for metric_type, value in data.items():
                                if isinstance(value, int):
                                    metric = MetricPoint(
                                        timestamp=timestamp,
                                        platform=platform,
                                        post_id=post_id,
                                        metric_type=metric_type,
                                        value=value,
                                        normalized_value=self._normalize_metric_value(metric_type, value, platform),
                                        hashtags=self._extract_hashtags_for_post(image, platform),
                                        post_caption=image
                                    )
                                    metrics.append(metric)

        except Exception as e:
            log_run("APU112Aggregator", "warning", f"Metrics log collection failed: {e}")

        return metrics

    def _collect_from_hashtag_data(self) -> List[MetricPoint]:
        """Collect hashtag performance data."""
        metrics = []
        try:
            for platform in self.config["collection"]["platforms"]:
                platform_dir = HASHTAG_DIR / platform.title()
                if platform_dir.exists():
                    # Get latest hashtag files
                    hashtag_files = list(platform_dir.glob("hashtags_*.txt"))
                    if hashtag_files:
                        latest_file = max(hashtag_files, key=lambda x: x.stat().st_mtime)
                        hashtags = latest_file.read_text(encoding="utf-8").strip().split('\n')

                        # Create hashtag usage metrics
                        for hashtag in hashtags[:10]:  # Top 10 hashtags
                            if hashtag.strip():
                                metric = MetricPoint(
                                    timestamp=datetime.now().isoformat(),
                                    platform=platform,
                                    post_id=f"hashtag_usage_{platform}",
                                    metric_type="hashtag_usage",
                                    value=1,
                                    normalized_value=1.0,
                                    hashtags=[hashtag.strip()],
                                    post_caption=f"Trending hashtag: {hashtag.strip()}"
                                )
                                metrics.append(metric)

        except Exception as e:
            log_run("APU112Aggregator", "warning", f"Hashtag collection failed: {e}")

        return metrics

    def _normalize_metric_value(self, metric_type: str, value: int, platform: str) -> float:
        """Normalize metric value using platform-specific weights."""
        if not self.config["normalization"]["enable_cross_platform_normalization"]:
            return float(value)

        weight_factors = self.config["normalization"]["weight_factors"]
        platform_weights = weight_factors.get(platform, {})
        weight = platform_weights.get(metric_type, 1.0)

        return value * weight

    def _extract_hashtags_for_post(self, image: str, platform: str) -> List[str]:
        """Extract hashtags associated with a post."""
        try:
            platform_dir = HASHTAG_DIR / platform.title()
            if platform_dir.exists():
                hashtag_files = list(platform_dir.glob("hashtags_*.txt"))
                if hashtag_files:
                    latest_file = max(hashtag_files, key=lambda x: x.stat().st_mtime)
                    hashtags = latest_file.read_text(encoding="utf-8").strip().split('\n')
                    return [h.strip() for h in hashtags[:5] if h.strip()]  # Top 5
        except Exception:
            pass
        return []

    def process_metrics_batch(self, metrics: List[MetricPoint]) -> List[EngagementSnapshot]:
        """Process a batch of metrics and create engagement snapshots."""
        snapshots = []

        # Group metrics by post
        post_groups = defaultdict(list)
        for metric in metrics:
            post_key = f"{metric.platform}_{metric.post_id}"
            post_groups[post_key].append(metric)

        for post_key, post_metrics in post_groups.items():
            if not post_metrics:
                continue

            # Aggregate metrics for this post
            raw_metrics = defaultdict(int)
            hashtags = set()
            latest_timestamp = post_metrics[0].timestamp

            for metric in post_metrics:
                raw_metrics[metric.metric_type] += metric.value
                hashtags.update(metric.hashtags)
                if metric.timestamp > latest_timestamp:
                    latest_timestamp = metric.timestamp

            # Calculate engagement scores
            normalized_score = self._calculate_normalized_engagement_score(dict(raw_metrics), post_metrics[0].platform)
            hashtag_performance_score = self._calculate_hashtag_performance_score(list(hashtags), post_metrics[0].platform)
            engagement_velocity = self._calculate_engagement_velocity(post_metrics)
            viral_potential_score = self._calculate_viral_potential_score(dict(raw_metrics), post_metrics[0].platform)

            snapshot = EngagementSnapshot(
                timestamp=latest_timestamp,
                platform=post_metrics[0].platform,
                post_id=post_metrics[0].post_id,
                metrics=dict(raw_metrics),
                normalized_score=normalized_score,
                hashtag_count=len(hashtags),
                hashtag_performance_score=hashtag_performance_score,
                engagement_velocity=engagement_velocity,
                viral_potential_score=viral_potential_score
            )

            snapshots.append(snapshot)

        return snapshots

    def _calculate_normalized_engagement_score(self, metrics: Dict[str, int], platform: str) -> float:
        """Calculate normalized engagement score."""
        weight_factors = self.config["normalization"]["weight_factors"].get(platform, {})

        total_score = 0
        total_weight = 0

        for metric_type, value in metrics.items():
            weight = weight_factors.get(metric_type, 1.0)
            total_score += value * weight
            total_weight += weight

        return total_score / max(total_weight, 1)

    def _calculate_hashtag_performance_score(self, hashtags: List[str], platform: str) -> float:
        """Calculate hashtag performance score."""
        if not hashtags:
            return 0.0

        # Get historical hashtag performance
        performance_scores = []
        for hashtag in hashtags:
            score = self.correlation_analyzer.get_hashtag_performance(hashtag, platform)
            performance_scores.append(score)

        return sum(performance_scores) / len(performance_scores) if performance_scores else 0.0

    def _calculate_engagement_velocity(self, metrics: List[MetricPoint]) -> float:
        """Calculate engagement velocity (change rate per hour)."""
        if len(metrics) < 2:
            return 0.0

        # Sort by timestamp
        sorted_metrics = sorted(metrics, key=lambda x: x.timestamp)

        # Calculate time span
        start_time = datetime.fromisoformat(sorted_metrics[0].timestamp)
        end_time = datetime.fromisoformat(sorted_metrics[-1].timestamp)
        time_diff_hours = max((end_time - start_time).total_seconds() / 3600, 0.1)

        # Calculate value change
        start_value = sum(m.value for m in sorted_metrics[:len(sorted_metrics)//2])
        end_value = sum(m.value for m in sorted_metrics[len(sorted_metrics)//2:])

        return (end_value - start_value) / time_diff_hours

    def _calculate_viral_potential_score(self, metrics: Dict[str, int], platform: str) -> float:
        """Calculate viral potential score."""
        # Viral indicators: high engagement rate, shares/reposts, comment ratio
        likes = metrics.get("likes", 0)
        comments = metrics.get("comments", 0)
        shares = metrics.get("shares", metrics.get("reposts", metrics.get("retweets", 0)))

        if likes == 0:
            return 0.0

        # Comment ratio (higher = more engaging)
        comment_ratio = comments / likes if likes > 0 else 0

        # Share ratio (higher = more viral)
        share_ratio = shares / likes if likes > 0 else 0

        # Platform-specific viral indicators
        platform_multiplier = {
            "tiktok": 1.2,  # TikTok has higher viral potential
            "instagram": 1.0,
            "x": 1.1,
            "threads": 0.9,
            "bluesky": 0.8
        }.get(platform, 1.0)

        viral_score = (comment_ratio * 0.4 + share_ratio * 0.6) * platform_multiplier
        return min(viral_score, 1.0)  # Cap at 1.0

    def store_metrics(self, metrics: List[MetricPoint], snapshots: List[EngagementSnapshot]):
        """Store metrics and snapshots in database."""
        for metric in metrics:
            self.db.insert_metric(metric)

        for snapshot in snapshots:
            self.db.insert_engagement_snapshot(snapshot)

    def run_aggregation_cycle(self) -> Dict[str, Any]:
        """Run a single aggregation cycle."""
        try:
            # Collect real-time metrics
            metrics = self.collect_real_time_metrics()

            if not metrics:
                return {
                    "status": "success",
                    "metrics_collected": 0,
                    "snapshots_created": 0,
                    "timestamp": datetime.now().isoformat()
                }

            # Process metrics into engagement snapshots
            snapshots = self.process_metrics_batch(metrics)

            # Store in database
            self.store_metrics(metrics, snapshots)

            # Update real-time cache
            self.real_time_cache.extend(snapshots)

            # Run trend analysis
            trends = self.trend_analyzer.analyze_trends(snapshots)

            # Update hashtag correlations
            self.correlation_analyzer.update_hashtag_correlations(metrics)

            # Generate alerts if needed
            alerts = self._generate_alerts(snapshots, trends)

            result = {
                "status": "success",
                "metrics_collected": len(metrics),
                "snapshots_created": len(snapshots),
                "trends_detected": len(trends),
                "alerts_generated": len(alerts),
                "timestamp": datetime.now().isoformat()
            }

            # Log the cycle
            log_run("APU112Aggregator", "ok",
                   f"Collected {len(metrics)} metrics, created {len(snapshots)} snapshots")

            return result

        except Exception as e:
            log_run("APU112Aggregator", "error", f"Aggregation cycle failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _generate_alerts(self, snapshots: List[EngagementSnapshot], trends: List[TrendAnalysis]) -> List[Dict[str, Any]]:
        """Generate alerts based on thresholds."""
        alerts = []
        thresholds = self.config["analysis"]["alert_thresholds"]

        for snapshot in snapshots:
            # Viral potential alert
            if snapshot.viral_potential_score > thresholds["viral_potential_score"]:
                alerts.append({
                    "type": "viral_potential",
                    "platform": snapshot.platform,
                    "post_id": snapshot.post_id,
                    "score": snapshot.viral_potential_score,
                    "message": f"High viral potential detected on {snapshot.platform}",
                    "timestamp": snapshot.timestamp
                })

            # Engagement velocity alert
            if snapshot.engagement_velocity > 50:  # High engagement rate
                alerts.append({
                    "type": "high_engagement",
                    "platform": snapshot.platform,
                    "post_id": snapshot.post_id,
                    "velocity": snapshot.engagement_velocity,
                    "message": f"High engagement velocity: {snapshot.engagement_velocity:.1f}/hour",
                    "timestamp": snapshot.timestamp
                })

        return alerts

class TrendAnalyzer:
    """Trend analysis component."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def analyze_trends(self, snapshots: List[EngagementSnapshot]) -> List[TrendAnalysis]:
        """Analyze trends in engagement snapshots."""
        trends = []

        # Group by platform for trend analysis
        platform_groups = defaultdict(list)
        for snapshot in snapshots:
            platform_groups[snapshot.platform].append(snapshot)

        for platform, platform_snapshots in platform_groups.items():
            if len(platform_snapshots) < 3:  # Need minimum data points
                continue

            # Analyze engagement trends
            engagement_scores = [s.normalized_score for s in platform_snapshots]
            velocity_scores = [s.engagement_velocity for s in platform_snapshots]

            # Determine trend type
            trend_type = self._determine_trend_type(engagement_scores, velocity_scores)
            confidence = self._calculate_trend_confidence(engagement_scores)

            # Generate recommendations
            recommendations = self._generate_trend_recommendations(trend_type, platform)

            trend = TrendAnalysis(
                timestamp=datetime.now().isoformat(),
                platform=platform,
                trend_type=trend_type,
                confidence_score=confidence,
                key_metrics={
                    "avg_engagement": np.mean(engagement_scores),
                    "avg_velocity": np.mean(velocity_scores),
                    "engagement_variance": np.var(engagement_scores)
                },
                recommendations=recommendations
            )
            trends.append(trend)

        return trends

    def _determine_trend_type(self, engagement_scores: List[float], velocity_scores: List[float]) -> str:
        """Determine trend type from scores."""
        if not engagement_scores:
            return "stable"

        # Calculate trend direction
        slope = np.polyfit(range(len(engagement_scores)), engagement_scores, 1)[0]
        variance = np.var(engagement_scores)

        if slope > 0.1 and variance < 0.5:
            return "growth"
        elif slope < -0.1 and variance < 0.5:
            return "decline"
        elif variance > 1.0:
            return "volatile"
        else:
            return "stable"

    def _calculate_trend_confidence(self, scores: List[float]) -> float:
        """Calculate confidence in trend analysis."""
        if len(scores) < 3:
            return 0.0

        # Higher confidence for consistent patterns
        variance = np.var(scores)
        consistency = 1.0 / (1.0 + variance)
        data_quality = min(len(scores) / 10.0, 1.0)  # More data = higher confidence

        return (consistency + data_quality) / 2.0

    def _generate_trend_recommendations(self, trend_type: str, platform: str) -> List[str]:
        """Generate recommendations based on trend type."""
        recommendations = []

        if trend_type == "growth":
            recommendations.append(f"Capitalize on growth momentum on {platform}")
            recommendations.append("Increase posting frequency to maintain growth")

        elif trend_type == "decline":
            recommendations.append(f"Review content strategy for {platform}")
            recommendations.append("Analyze successful past posts for insights")

        elif trend_type == "volatile":
            recommendations.append(f"Stabilize content approach on {platform}")
            recommendations.append("Test consistent posting times and content types")

        else:  # stable
            recommendations.append(f"Maintain current successful strategy on {platform}")
            recommendations.append("Consider experimenting with new content formats")

        return recommendations

class CorrelationAnalyzer:
    """Performance correlation analysis component."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.hashtag_performance = {}  # Cache for hashtag performance data

    def update_hashtag_correlations(self, metrics: List[MetricPoint]):
        """Update hashtag performance correlations."""
        # Group metrics by hashtag
        hashtag_metrics = defaultdict(list)

        for metric in metrics:
            for hashtag in metric.hashtags:
                if hashtag:
                    hashtag_metrics[hashtag].append(metric)

        # Update performance for each hashtag
        for hashtag, hashtag_metric_list in hashtag_metrics.items():
            self._update_hashtag_performance(hashtag, hashtag_metric_list)

    def _update_hashtag_performance(self, hashtag: str, metrics: List[MetricPoint]):
        """Update performance data for a specific hashtag."""
        if not metrics:
            return

        # Calculate average engagement
        total_engagement = sum(m.normalized_value for m in metrics)
        avg_engagement = total_engagement / len(metrics)

        # Platform breakdown
        platform_performance = defaultdict(list)
        for metric in metrics:
            platform_performance[metric.platform].append(metric.normalized_value)

        platform_averages = {
            platform: np.mean(values)
            for platform, values in platform_performance.items()
        }

        # Store performance data
        self.hashtag_performance[hashtag] = {
            "usage_count": len(metrics),
            "avg_engagement_score": avg_engagement,
            "platform_performance": platform_averages,
            "last_updated": datetime.now().isoformat()
        }

    def get_hashtag_performance(self, hashtag: str, platform: str) -> float:
        """Get performance score for a hashtag on a platform."""
        if hashtag not in self.hashtag_performance:
            return 0.5  # Default neutral score

        perf_data = self.hashtag_performance[hashtag]
        platform_perf = perf_data["platform_performance"]

        if platform in platform_perf:
            return min(platform_perf[platform] / 10.0, 1.0)  # Normalize to 0-1
        else:
            return perf_data["avg_engagement_score"] / 10.0  # Fallback to overall average

    def get_top_performing_hashtags(self, platform: str, limit: int = 10) -> List[PerformanceCorrelation]:
        """Get top performing hashtags for a platform."""
        correlations = []

        for hashtag, perf_data in self.hashtag_performance.items():
            platform_perf = perf_data["platform_performance"]

            if platform in platform_perf:
                correlation = PerformanceCorrelation(
                    hashtag=hashtag,
                    usage_count=perf_data["usage_count"],
                    avg_engagement_score=perf_data["avg_engagement_score"],
                    performance_trend="stable",  # TODO: Implement trend calculation
                    platform_performance=platform_perf,
                    correlation_confidence=0.8  # TODO: Implement confidence calculation
                )
                correlations.append(correlation)

        # Sort by platform performance
        correlations.sort(key=lambda x: x.platform_performance.get(platform, 0), reverse=True)
        return correlations[:limit]

# Flask API endpoints for real-time access
def create_metrics_api(aggregator: APU112EngagementAggregator) -> Flask:
    """Create Flask API for metrics access."""

    api = Flask(__name__)

    @api.route('/api/v1/metrics/real-time')
    def get_real_time_metrics():
        """Get real-time metrics summary."""
        try:
            # Get recent data from cache
            recent_snapshots = list(aggregator.real_time_cache)[-50:]  # Last 50 snapshots

            if not recent_snapshots:
                return jsonify({
                    "status": "success",
                    "data": [],
                    "summary": {
                        "total_snapshots": 0,
                        "avg_engagement": 0,
                        "avg_viral_potential": 0
                    }
                })

            # Calculate summary metrics
            avg_engagement = np.mean([s.normalized_score for s in recent_snapshots])
            avg_viral_potential = np.mean([s.viral_potential_score for s in recent_snapshots])

            # Platform breakdown
            platform_breakdown = defaultdict(list)
            for snapshot in recent_snapshots:
                platform_breakdown[snapshot.platform].append(snapshot.normalized_score)

            platform_summary = {
                platform: {
                    "count": len(scores),
                    "avg_engagement": np.mean(scores),
                    "max_engagement": max(scores),
                    "min_engagement": min(scores)
                }
                for platform, scores in platform_breakdown.items()
            }

            return jsonify({
                "status": "success",
                "data": [asdict(s) for s in recent_snapshots],
                "summary": {
                    "total_snapshots": len(recent_snapshots),
                    "avg_engagement": avg_engagement,
                    "avg_viral_potential": avg_viral_potential,
                    "platform_breakdown": platform_summary
                },
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            return jsonify({
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }), 500

    @api.route('/api/v1/metrics/trends/<platform>')
    def get_platform_trends(platform: str):
        """Get trend analysis for a specific platform."""
        try:
            # Get trend data from database
            trends = aggregator.db.get_engagement_trends(days=7, platform=platform)

            if not trends:
                return jsonify({
                    "status": "success",
                    "platform": platform,
                    "trends": [],
                    "summary": {}
                })

            # Calculate trend summary
            recent_scores = [json.loads(t["raw_metrics"]).get("likes", 0) +
                           json.loads(t["raw_metrics"]).get("comments", 0) for t in trends]

            trend_summary = {
                "data_points": len(trends),
                "avg_engagement": np.mean(recent_scores) if recent_scores else 0,
                "trend_direction": "stable",  # TODO: Calculate actual trend
                "last_updated": trends[0]["timestamp"] if trends else None
            }

            return jsonify({
                "status": "success",
                "platform": platform,
                "trends": trends,
                "summary": trend_summary,
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            return jsonify({
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }), 500

    @api.route('/api/v1/hashtags/performance/<platform>')
    def get_hashtag_performance(platform: str):
        """Get hashtag performance analysis for a platform."""
        try:
            top_hashtags = aggregator.correlation_analyzer.get_top_performing_hashtags(platform, limit=20)

            return jsonify({
                "status": "success",
                "platform": platform,
                "hashtags": [asdict(h) for h in top_hashtags],
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            return jsonify({
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }), 500

    @api.route('/api/v1/metrics/dashboard')
    def get_dashboard_data():
        """Get comprehensive dashboard data."""
        try:
            # Get real-time summary
            recent_snapshots = list(aggregator.real_time_cache)[-100:]

            # Calculate cross-platform metrics
            platform_metrics = defaultdict(lambda: {"count": 0, "total_engagement": 0, "total_viral": 0})

            for snapshot in recent_snapshots:
                platform_metrics[snapshot.platform]["count"] += 1
                platform_metrics[snapshot.platform]["total_engagement"] += snapshot.normalized_score
                platform_metrics[snapshot.platform]["total_viral"] += snapshot.viral_potential_score

            # Calculate averages
            dashboard_data = {}
            for platform, data in platform_metrics.items():
                dashboard_data[platform] = {
                    "avg_engagement": data["total_engagement"] / data["count"] if data["count"] > 0 else 0,
                    "avg_viral_potential": data["total_viral"] / data["count"] if data["count"] > 0 else 0,
                    "post_count": data["count"]
                }

            # Get top hashtags across all platforms
            all_top_hashtags = {}
            for platform in aggregator.config["collection"]["platforms"]:
                top_hashtags = aggregator.correlation_analyzer.get_top_performing_hashtags(platform, limit=5)
                all_top_hashtags[platform] = [asdict(h) for h in top_hashtags]

            return jsonify({
                "status": "success",
                "dashboard": {
                    "platform_metrics": dashboard_data,
                    "top_hashtags": all_top_hashtags,
                    "total_snapshots": len(recent_snapshots),
                    "timestamp": datetime.now().isoformat()
                }
            })

        except Exception as e:
            return jsonify({
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }), 500

    return api

def main():
    """APU-112 Engagement Metrics Aggregator main function."""
    import argparse

    parser = argparse.ArgumentParser(description="APU-112 Real-Time Engagement Metrics Aggregator")
    parser.add_argument("--mode", choices=["single", "continuous", "api"], default="single",
                       help="Run mode: single check, continuous monitoring, or API server")
    parser.add_argument("--config", help="Path to custom configuration file")
    parser.add_argument("--port", type=int, default=5556, help="API server port (for api mode)")
    args = parser.parse_args()

    # Initialize aggregator
    aggregator = APU112EngagementAggregator(args.config)

    if args.mode == "api":
        # Start API server
        api = create_metrics_api(aggregator)
        print(f"\n[APU-112] Starting Engagement Metrics API on port {args.port}")
        print(f"[APU-112] API endpoints available at http://localhost:{args.port}/api/v1/")
        print(f"[APU-112] Dashboard: http://localhost:{args.port}/api/v1/metrics/dashboard")
        api.run(host='0.0.0.0', port=args.port, debug=False)

    elif args.mode == "continuous":
        # Start continuous monitoring
        print(f"\n[APU-112] Starting Real-Time Engagement Metrics Aggregator")
        print(f"[CONFIG] Collection interval: {aggregator.config['collection']['real_time_interval_seconds']} seconds")
        print(f"[CONFIG] Platforms: {', '.join(aggregator.config['collection']['platforms'])}")

        aggregator.running = True
        interval = aggregator.config["collection"]["real_time_interval_seconds"]

        while aggregator.running:
            try:
                result = aggregator.run_aggregation_cycle()

                if result["status"] == "success":
                    print(f"[APU-112] Cycle complete: {result['metrics_collected']} metrics, "
                          f"{result['snapshots_created']} snapshots, {result.get('trends_detected', 0)} trends")
                else:
                    print(f"[APU-112] Cycle failed: {result.get('error', 'Unknown error')}")

                time.sleep(interval)

            except KeyboardInterrupt:
                print(f"\n[APU-112] Monitoring stopped by user")
                break
            except Exception as e:
                print(f"[APU-112 ERROR] Unexpected error: {e}")
                time.sleep(60)  # Wait 1 minute on error

        aggregator.running = False

    else:  # single mode
        # Run single aggregation cycle
        print(f"\n[APU-112] Running single engagement metrics aggregation...")
        result = aggregator.run_aggregation_cycle()

        if result["status"] == "success":
            print(f"[APU-112] SUCCESS: Collected {result['metrics_collected']} metrics, "
                  f"created {result['snapshots_created']} snapshots")
            return 0
        else:
            print(f"[APU-112] FAILED: {result.get('error', 'Unknown error')}")
            return 1

if __name__ == "__main__":
    exit(main())