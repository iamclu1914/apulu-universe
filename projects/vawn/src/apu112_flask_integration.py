"""
apu112_flask_integration.py — APU-112 Flask Integration for Engagement Metrics

Integration module to add real-time engagement metrics endpoints to the existing
review_ui.py Flask application. Provides backward compatibility and unified API.

Created by: Backend API Agent (APU-112)
Features:
- Seamless integration with existing Flask app
- Unified metrics dashboard
- Real-time WebSocket endpoints for live data
- Engagement analytics visualization
- Growth funnel tracking API
"""

import json
import asyncio
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from flask import Blueprint, jsonify, request, render_template_string
from flask_socketio import SocketIO, emit, join_room, leave_room
import numpy as np
from collections import defaultdict

from apu112_engagement_metrics_aggregator import (
    APU112EngagementAggregator, EngagementSnapshot, TrendAnalysis
)

# Blueprint for metrics endpoints
metrics_bp = Blueprint('metrics', __name__, url_prefix='/api/v1/metrics')

# Global aggregator instance
_aggregator_instance = None
_socketio_instance = None

def init_metrics_integration(app, config_path: Optional[str] = None) -> APU112EngagementAggregator:
    """Initialize metrics integration with Flask app."""
    global _aggregator_instance, _socketio_instance

    # Initialize aggregator
    _aggregator_instance = APU112EngagementAggregator(config_path)

    # Initialize SocketIO for real-time updates
    _socketio_instance = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

    # Register blueprint
    app.register_blueprint(metrics_bp)

    # Setup SocketIO handlers
    setup_socketio_handlers(_socketio_instance)

    # Start background metrics collection
    start_background_metrics_collection()

    return _aggregator_instance

def setup_socketio_handlers(socketio):
    """Setup SocketIO event handlers for real-time metrics."""

    @socketio.on('connect')
    def handle_connect():
        """Handle client connection."""
        print("[APU-112] Client connected to real-time metrics")
        emit('status', {'msg': 'Connected to APU-112 metrics stream'})

    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection."""
        print("[APU-112] Client disconnected from real-time metrics")

    @socketio.on('join_platform')
    def handle_join_platform(data):
        """Join platform-specific room for targeted updates."""
        platform = data.get('platform', 'all')
        join_room(f"platform_{platform}")
        emit('status', {'msg': f'Joined {platform} metrics stream'})

    @socketio.on('leave_platform')
    def handle_leave_platform(data):
        """Leave platform-specific room."""
        platform = data.get('platform', 'all')
        leave_room(f"platform_{platform}")
        emit('status', {'msg': f'Left {platform} metrics stream'})

def start_background_metrics_collection():
    """Start background thread for continuous metrics collection."""
    def metrics_worker():
        """Background worker for metrics collection."""
        global _aggregator_instance, _socketio_instance

        if not _aggregator_instance or not _socketio_instance:
            return

        _aggregator_instance.running = True
        interval = _aggregator_instance.config["collection"]["real_time_interval_seconds"]

        while _aggregator_instance.running:
            try:
                # Run aggregation cycle
                result = _aggregator_instance.run_aggregation_cycle()

                if result["status"] == "success" and result["snapshots_created"] > 0:
                    # Emit real-time updates via SocketIO
                    emit_real_time_updates(result)

                # Wait for next cycle
                threading.Event().wait(interval)

            except Exception as e:
                print(f"[APU-112] Background worker error: {e}")
                threading.Event().wait(60)  # Wait 1 minute on error

    # Start worker thread
    worker_thread = threading.Thread(target=metrics_worker, daemon=True)
    worker_thread.start()

def emit_real_time_updates(result: Dict[str, Any]):
    """Emit real-time updates to connected clients."""
    global _aggregator_instance, _socketio_instance

    if not _socketio_instance or not _aggregator_instance:
        return

    try:
        # Get recent snapshots from cache
        recent_snapshots = list(_aggregator_instance.real_time_cache)[-10:]

        if recent_snapshots:
            # Emit general update
            _socketio_instance.emit('metrics_update', {
                'timestamp': datetime.now().isoformat(),
                'snapshots': [
                    {
                        'platform': s.platform,
                        'normalized_score': s.normalized_score,
                        'viral_potential': s.viral_potential_score,
                        'engagement_velocity': s.engagement_velocity,
                        'hashtag_count': s.hashtag_count
                    } for s in recent_snapshots
                ]
            })

            # Emit platform-specific updates
            platform_groups = defaultdict(list)
            for snapshot in recent_snapshots:
                platform_groups[snapshot.platform].append(snapshot)

            for platform, snapshots in platform_groups.items():
                avg_engagement = np.mean([s.normalized_score for s in snapshots])
                avg_viral = np.mean([s.viral_potential_score for s in snapshots])

                _socketio_instance.emit('platform_update', {
                    'platform': platform,
                    'avg_engagement': avg_engagement,
                    'avg_viral_potential': avg_viral,
                    'snapshot_count': len(snapshots),
                    'timestamp': datetime.now().isoformat()
                }, room=f"platform_{platform}")

    except Exception as e:
        print(f"[APU-112] Error emitting updates: {e}")

# API Endpoints

@metrics_bp.route('/dashboard')
def get_metrics_dashboard():
    """Get comprehensive metrics dashboard data."""
    global _aggregator_instance

    if not _aggregator_instance:
        return jsonify({"error": "Metrics aggregator not initialized"}), 500

    try:
        # Get recent data
        recent_snapshots = list(_aggregator_instance.real_time_cache)[-100:]

        # Calculate platform metrics
        platform_metrics = defaultdict(lambda: {
            "count": 0, "total_engagement": 0, "total_viral": 0,
            "total_velocity": 0, "hashtag_counts": []
        })

        for snapshot in recent_snapshots:
            pm = platform_metrics[snapshot.platform]
            pm["count"] += 1
            pm["total_engagement"] += snapshot.normalized_score
            pm["total_viral"] += snapshot.viral_potential_score
            pm["total_velocity"] += snapshot.engagement_velocity
            pm["hashtag_counts"].append(snapshot.hashtag_count)

        # Calculate averages and insights
        dashboard_data = {}
        for platform, data in platform_metrics.items():
            count = data["count"]
            dashboard_data[platform] = {
                "avg_engagement": data["total_engagement"] / count if count > 0 else 0,
                "avg_viral_potential": data["total_viral"] / count if count > 0 else 0,
                "avg_velocity": data["total_velocity"] / count if count > 0 else 0,
                "avg_hashtag_count": np.mean(data["hashtag_counts"]) if data["hashtag_counts"] else 0,
                "post_count": count,
                "engagement_trend": _calculate_simple_trend([s.normalized_score for s in recent_snapshots if s.platform == platform])
            }

        # Get hashtag performance
        hashtag_performance = {}
        for platform in _aggregator_instance.config["collection"]["platforms"]:
            top_hashtags = _aggregator_instance.correlation_analyzer.get_top_performing_hashtags(platform, limit=10)
            hashtag_performance[platform] = [
                {
                    "hashtag": h.hashtag,
                    "performance_score": h.platform_performance.get(platform, 0),
                    "usage_count": h.usage_count
                } for h in top_hashtags
            ]

        # Recent alerts
        recent_alerts = _get_recent_alerts()

        return jsonify({
            "status": "success",
            "dashboard": {
                "platform_metrics": dashboard_data,
                "hashtag_performance": hashtag_performance,
                "recent_alerts": recent_alerts,
                "total_snapshots": len(recent_snapshots),
                "last_updated": datetime.now().isoformat()
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@metrics_bp.route('/real-time')
def get_real_time_metrics():
    """Get current real-time metrics."""
    global _aggregator_instance

    if not _aggregator_instance:
        return jsonify({"error": "Metrics aggregator not initialized"}), 500

    try:
        recent_snapshots = list(_aggregator_instance.real_time_cache)[-20:]

        if not recent_snapshots:
            return jsonify({
                "status": "success",
                "data": [],
                "summary": {"total_snapshots": 0, "avg_engagement": 0}
            })

        # Calculate real-time summary
        avg_engagement = np.mean([s.normalized_score for s in recent_snapshots])
        avg_viral = np.mean([s.viral_potential_score for s in recent_snapshots])
        avg_velocity = np.mean([s.engagement_velocity for s in recent_snapshots])

        return jsonify({
            "status": "success",
            "data": [
                {
                    "timestamp": s.timestamp,
                    "platform": s.platform,
                    "normalized_score": s.normalized_score,
                    "viral_potential": s.viral_potential_score,
                    "engagement_velocity": s.engagement_velocity,
                    "hashtag_count": s.hashtag_count
                } for s in recent_snapshots
            ],
            "summary": {
                "total_snapshots": len(recent_snapshots),
                "avg_engagement": avg_engagement,
                "avg_viral_potential": avg_viral,
                "avg_velocity": avg_velocity,
                "timestamp": datetime.now().isoformat()
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@metrics_bp.route('/trends/<platform>')
def get_platform_trends(platform: str):
    """Get trend analysis for specific platform."""
    global _aggregator_instance

    if not _aggregator_instance:
        return jsonify({"error": "Metrics aggregator not initialized"}), 500

    try:
        # Get historical data from database
        historical_data = _aggregator_instance.db.get_engagement_trends(days=7, platform=platform)

        if not historical_data:
            return jsonify({
                "status": "success",
                "platform": platform,
                "trends": [],
                "summary": {"message": "No historical data available"}
            })

        # Process trends
        engagement_scores = []
        timestamps = []

        for record in historical_data[-50:]:  # Last 50 records
            engagement_scores.append(record["normalized_score"])
            timestamps.append(record["timestamp"])

        # Calculate trend metrics
        trend_direction = _calculate_simple_trend(engagement_scores)
        trend_strength = _calculate_trend_strength(engagement_scores)

        # Generate insights
        insights = _generate_trend_insights(platform, trend_direction, trend_strength, engagement_scores)

        return jsonify({
            "status": "success",
            "platform": platform,
            "trends": {
                "direction": trend_direction,
                "strength": trend_strength,
                "data_points": len(engagement_scores),
                "avg_engagement": np.mean(engagement_scores) if engagement_scores else 0,
                "latest_score": engagement_scores[-1] if engagement_scores else 0,
                "timestamps": timestamps[-10:],  # Last 10 timestamps
                "scores": engagement_scores[-10:]  # Last 10 scores
            },
            "insights": insights,
            "last_updated": datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@metrics_bp.route('/correlation/<platform>')
def get_hashtag_correlation(platform: str):
    """Get hashtag performance correlation for platform."""
    global _aggregator_instance

    if not _aggregator_instance:
        return jsonify({"error": "Metrics aggregator not initialized"}), 500

    try:
        # Get hashtag performance data
        top_hashtags = _aggregator_instance.correlation_analyzer.get_top_performing_hashtags(platform, limit=20)

        correlation_data = []
        for hashtag in top_hashtags:
            platform_score = hashtag.platform_performance.get(platform, 0)
            correlation_data.append({
                "hashtag": hashtag.hashtag,
                "performance_score": platform_score,
                "usage_count": hashtag.usage_count,
                "avg_engagement": hashtag.avg_engagement_score,
                "trend": hashtag.performance_trend,
                "confidence": hashtag.correlation_confidence
            })

        # Calculate overall correlation insights
        if correlation_data:
            avg_performance = np.mean([h["performance_score"] for h in correlation_data])
            top_performer = max(correlation_data, key=lambda x: x["performance_score"])
            most_used = max(correlation_data, key=lambda x: x["usage_count"])
        else:
            avg_performance = 0
            top_performer = None
            most_used = None

        return jsonify({
            "status": "success",
            "platform": platform,
            "hashtags": correlation_data,
            "insights": {
                "total_hashtags": len(correlation_data),
                "avg_performance": avg_performance,
                "top_performer": top_performer,
                "most_used": most_used
            },
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@metrics_bp.route('/growth-funnel')
def get_growth_funnel():
    """Get growth funnel analysis across all platforms."""
    global _aggregator_instance

    if not _aggregator_instance:
        return jsonify({"error": "Metrics aggregator not initialized"}), 500

    try:
        # Get recent snapshots for funnel analysis
        recent_snapshots = list(_aggregator_instance.real_time_cache)[-100:]

        # Define funnel stages
        funnel_stages = {
            "awareness": {"min_score": 0, "max_score": 3},
            "engagement": {"min_score": 3, "max_score": 7},
            "conversion": {"min_score": 7, "max_score": float('inf')}
        }

        # Categorize snapshots by funnel stage
        funnel_data = {stage: [] for stage in funnel_stages.keys()}

        for snapshot in recent_snapshots:
            score = snapshot.normalized_score
            for stage, range_def in funnel_stages.items():
                if range_def["min_score"] <= score < range_def["max_score"]:
                    funnel_data[stage].append(snapshot)
                    break

        # Calculate funnel metrics
        funnel_metrics = {}
        for stage, snapshots in funnel_data.items():
            if snapshots:
                funnel_metrics[stage] = {
                    "count": len(snapshots),
                    "avg_engagement": np.mean([s.normalized_score for s in snapshots]),
                    "avg_viral_potential": np.mean([s.viral_potential_score for s in snapshots]),
                    "platform_breakdown": _get_platform_breakdown(snapshots)
                }
            else:
                funnel_metrics[stage] = {
                    "count": 0,
                    "avg_engagement": 0,
                    "avg_viral_potential": 0,
                    "platform_breakdown": {}
                }

        # Calculate conversion rates
        total_posts = len(recent_snapshots)
        conversion_rates = {
            "awareness_to_engagement": (
                funnel_metrics["engagement"]["count"] / max(funnel_metrics["awareness"]["count"], 1)
            ) * 100,
            "engagement_to_conversion": (
                funnel_metrics["conversion"]["count"] / max(funnel_metrics["engagement"]["count"], 1)
            ) * 100,
            "overall_conversion": (
                funnel_metrics["conversion"]["count"] / max(total_posts, 1)
            ) * 100
        }

        return jsonify({
            "status": "success",
            "funnel": {
                "stages": funnel_metrics,
                "conversion_rates": conversion_rates,
                "total_posts": total_posts,
                "funnel_health": _calculate_funnel_health(funnel_metrics, conversion_rates)
            },
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@metrics_bp.route('/alerts')
def get_current_alerts():
    """Get current system alerts."""
    try:
        alerts = _get_recent_alerts()

        return jsonify({
            "status": "success",
            "alerts": alerts,
            "alert_count": len(alerts),
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Helper Functions

def _calculate_simple_trend(scores: List[float]) -> str:
    """Calculate simple trend direction."""
    if len(scores) < 2:
        return "stable"

    # Simple trend calculation
    slope = np.polyfit(range(len(scores)), scores, 1)[0] if len(scores) > 1 else 0

    if slope > 0.1:
        return "increasing"
    elif slope < -0.1:
        return "decreasing"
    else:
        return "stable"

def _calculate_trend_strength(scores: List[float]) -> float:
    """Calculate trend strength (0-1)."""
    if len(scores) < 2:
        return 0.0

    # Calculate variance to determine strength
    variance = np.var(scores)
    trend_strength = min(variance / 10.0, 1.0)  # Normalize variance

    return trend_strength

def _generate_trend_insights(platform: str, direction: str, strength: float, scores: List[float]) -> List[str]:
    """Generate trend insights."""
    insights = []

    if direction == "increasing":
        insights.append(f"📈 {platform.title()} engagement is trending upward")
        if strength > 0.7:
            insights.append("Strong growth momentum - consider increasing content frequency")
        else:
            insights.append("Steady growth - maintain current strategy")

    elif direction == "decreasing":
        insights.append(f"📉 {platform.title()} engagement is declining")
        if strength > 0.7:
            insights.append("⚠️ Significant decline detected - review content strategy")
        else:
            insights.append("Minor decline - monitor and adjust if trend continues")

    else:  # stable
        insights.append(f"📊 {platform.title()} engagement is stable")
        insights.append("Consider experimenting with new content formats for growth")

    # Add score-based insights
    if scores:
        avg_score = np.mean(scores)
        if avg_score > 8:
            insights.append("🔥 High engagement levels - excellent performance")
        elif avg_score > 5:
            insights.append("✅ Good engagement levels")
        else:
            insights.append("💡 Room for engagement improvement")

    return insights

def _get_platform_breakdown(snapshots: List[EngagementSnapshot]) -> Dict[str, int]:
    """Get platform breakdown from snapshots."""
    breakdown = defaultdict(int)
    for snapshot in snapshots:
        breakdown[snapshot.platform] += 1
    return dict(breakdown)

def _calculate_funnel_health(funnel_metrics: Dict, conversion_rates: Dict) -> str:
    """Calculate overall funnel health."""
    overall_conversion = conversion_rates["overall_conversion"]

    if overall_conversion > 15:
        return "excellent"
    elif overall_conversion > 10:
        return "good"
    elif overall_conversion > 5:
        return "fair"
    else:
        return "needs_improvement"

def _get_recent_alerts() -> List[Dict[str, Any]]:
    """Get recent system alerts."""
    global _aggregator_instance

    if not _aggregator_instance:
        return []

    try:
        # Get recent snapshots for alert generation
        recent_snapshots = list(_aggregator_instance.real_time_cache)[-20:]
        alerts = []

        for snapshot in recent_snapshots:
            # High viral potential alert
            if snapshot.viral_potential_score > 0.8:
                alerts.append({
                    "type": "viral_potential",
                    "platform": snapshot.platform,
                    "message": f"High viral potential detected on {snapshot.platform}",
                    "score": snapshot.viral_potential_score,
                    "timestamp": snapshot.timestamp,
                    "severity": "info"
                })

            # High engagement velocity
            if snapshot.engagement_velocity > 20:
                alerts.append({
                    "type": "high_velocity",
                    "platform": snapshot.platform,
                    "message": f"High engagement velocity: {snapshot.engagement_velocity:.1f}/hour",
                    "velocity": snapshot.engagement_velocity,
                    "timestamp": snapshot.timestamp,
                    "severity": "info"
                })

            # Low engagement warning
            if snapshot.normalized_score < 1 and snapshot.hashtag_count > 3:
                alerts.append({
                    "type": "low_engagement",
                    "platform": snapshot.platform,
                    "message": f"Low engagement despite {snapshot.hashtag_count} hashtags",
                    "score": snapshot.normalized_score,
                    "timestamp": snapshot.timestamp,
                    "severity": "warning"
                })

        # Remove duplicates and limit to recent
        unique_alerts = []
        seen_combinations = set()

        for alert in alerts[-10:]:  # Last 10 alerts
            key = (alert["type"], alert["platform"])
            if key not in seen_combinations:
                unique_alerts.append(alert)
                seen_combinations.add(key)

        return unique_alerts

    except Exception as e:
        return [{"type": "system_error", "message": f"Error generating alerts: {e}", "severity": "error"}]

# WebSocket real-time dashboard HTML template
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>APU-112 Real-Time Engagement Dashboard</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .dashboard { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric { display: flex; justify-content: space-between; margin: 10px 0; }
        .platform { margin: 15px 0; padding: 10px; background: #f9f9f9; border-radius: 4px; }
        .alert { padding: 10px; margin: 5px 0; border-radius: 4px; }
        .alert.info { background: #d1ecf1; border: 1px solid #bee5eb; }
        .alert.warning { background: #fff3cd; border: 1px solid #ffeaa7; }
        .alert.error { background: #f8d7da; border: 1px solid #f5c6cb; }
        #status { position: fixed; top: 10px; right: 10px; padding: 10px; background: #28a745; color: white; border-radius: 4px; }
    </style>
</head>
<body>
    <div id="status">Connecting...</div>

    <h1>APU-112 Real-Time Engagement Dashboard</h1>

    <div class="dashboard">
        <div class="card">
            <h3>📊 Platform Metrics</h3>
            <div id="platform-metrics"></div>
        </div>

        <div class="card">
            <h3>🔥 Real-Time Activity</h3>
            <canvas id="activity-chart" width="400" height="200"></canvas>
        </div>

        <div class="card">
            <h3>🚨 Recent Alerts</h3>
            <div id="alerts"></div>
        </div>

        <div class="card">
            <h3>📈 Top Hashtags</h3>
            <div id="hashtags"></div>
        </div>
    </div>

    <script>
        const socket = io();

        socket.on('connect', function() {
            document.getElementById('status').textContent = 'Connected';
            document.getElementById('status').style.background = '#28a745';
        });

        socket.on('disconnect', function() {
            document.getElementById('status').textContent = 'Disconnected';
            document.getElementById('status').style.background = '#dc3545';
        });

        socket.on('metrics_update', function(data) {
            updateDashboard(data);
        });

        // Initialize activity chart
        const ctx = document.getElementById('activity-chart').getContext('2d');
        const activityChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Engagement Score',
                    data: [],
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: { y: { beginAtZero: true } }
            }
        });

        function updateDashboard(data) {
            // Update platform metrics
            const platformsDiv = document.getElementById('platform-metrics');
            const platforms = {};

            data.snapshots.forEach(s => {
                if (!platforms[s.platform]) {
                    platforms[s.platform] = { count: 0, totalScore: 0, totalViral: 0 };
                }
                platforms[s.platform].count++;
                platforms[s.platform].totalScore += s.normalized_score;
                platforms[s.platform].totalViral += s.viral_potential;
            });

            platformsDiv.innerHTML = '';
            Object.entries(platforms).forEach(([platform, data]) => {
                const avgScore = (data.totalScore / data.count).toFixed(2);
                const avgViral = (data.totalViral / data.count).toFixed(2);

                platformsDiv.innerHTML += `
                    <div class="platform">
                        <strong>${platform.toUpperCase()}</strong><br>
                        Avg Score: ${avgScore} | Viral: ${avgViral} | Posts: ${data.count}
                    </div>
                `;
            });

            // Update activity chart
            const now = new Date().toLocaleTimeString();
            const avgScore = data.snapshots.reduce((sum, s) => sum + s.normalized_score, 0) / data.snapshots.length;

            activityChart.data.labels.push(now);
            activityChart.data.datasets[0].data.push(avgScore);

            // Keep only last 20 data points
            if (activityChart.data.labels.length > 20) {
                activityChart.data.labels.shift();
                activityChart.data.datasets[0].data.shift();
            }

            activityChart.update();
        }

        // Load initial data
        fetch('/api/v1/metrics/dashboard')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Initial platform metrics update
                    // ... implementation for initial data loading
                }
            });
    </script>
</body>
</html>
"""

@metrics_bp.route('/live-dashboard')
def live_dashboard():
    """Serve live dashboard with WebSocket integration."""
    return render_template_string(DASHBOARD_TEMPLATE)