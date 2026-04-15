"""
community_dashboard_apu51.py — Real-time Community Intelligence Dashboard for APU-51.
Interactive web dashboard for community engagement monitoring and insights.
Created by: Dex - Community Agent (APU-51)

Features:
- Real-time community health visualization
- Interactive sentiment tracking charts
- Cross-platform engagement analytics
- Predictive insights display
- Automated recommendation alerts
- Community growth metrics

Serves as the primary interface for community management using APU-51 intelligence data.
"""

import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse as urlparse

sys.path.insert(0, str(Path(__file__).parent.parent))
from vawn_config import load_json, VAWN_DIR

# Dashboard Configuration
DASHBOARD_PORT = 8051
DASHBOARD_HOST = "localhost"
REFRESH_INTERVAL = 30  # seconds

# Data file paths
COMMUNITY_INTELLIGENCE_LOG = VAWN_DIR / "research" / "community_intelligence_apu51_log.json"
SENTIMENT_LOG = VAWN_DIR / "research" / "community_sentiment_log.json"
COMMUNITY_HEALTH_LOG = VAWN_DIR / "research" / "community_health_log.json"


class CommunityDashboardData:
    """Data management for the community dashboard."""

    def __init__(self):
        self.cache = {}
        self.last_update = datetime.now()

    def get_latest_intelligence_data(self) -> Dict[str, Any]:
        """Get the most recent community intelligence data."""
        try:
            if not Path(COMMUNITY_INTELLIGENCE_LOG).exists():
                return self._get_default_data()

            intel_log = load_json(COMMUNITY_INTELLIGENCE_LOG)

            # Get most recent entry
            latest_date = max(intel_log.keys()) if intel_log else None
            if not latest_date:
                return self._get_default_data()

            latest_entries = intel_log[latest_date]
            latest_entry = latest_entries[-1] if latest_entries else {}

            return self._format_dashboard_data(latest_entry)

        except Exception as e:
            print(f"[ERROR] Failed to load intelligence data: {e}")
            return self._get_default_data()

    def _get_default_data(self) -> Dict[str, Any]:
        """Return default data structure when no data is available."""
        return {
            "timestamp": datetime.now().isoformat(),
            "community_health": {
                "overall_score": 0.5,
                "health_status": "unknown",
                "component_scores": {
                    "sentiment": 0.5,
                    "engagement": 0.5,
                    "response": 0.5,
                    "growth": 0.5
                },
                "strengths": [],
                "improvement_areas": ["No data available"]
            },
            "sentiment_analysis": {
                "overall_sentiment": 0.0,
                "community_satisfaction": 0.5,
                "sentiment_distribution": {
                    "positive": 0,
                    "neutral": 0,
                    "negative": 0
                },
                "emotional_themes": [],
                "sentiment_trend": "unknown"
            },
            "cross_platform_analysis": {
                "cross_platform_trends": {
                    "top_performer": "unknown",
                    "average_performance": 0.0,
                    "platform_diversity_score": 0.0,
                    "total_reach_estimate": 0
                },
                "platform_performance": {}
            },
            "predictions": {
                "sentiment_forecast": {"predicted_trend": "unknown", "confidence": 0.0},
                "engagement_forecast": {"predicted_trend": "unknown", "confidence": 0.0},
                "community_growth_projection": {"projected_growth": "unknown", "confidence": 0.0},
                "opportunities": [],
                "risk_indicators": [],
                "forecast_confidence": 0.0
            },
            "intelligence_alerts": [],
            "summary": {
                "community_health_score": 0.5,
                "community_health_status": "unknown",
                "overall_sentiment": 0.0,
                "total_intelligence_alerts": 0,
                "critical_alerts": 0
            }
        }

    def _format_dashboard_data(self, raw_data: Dict) -> Dict[str, Any]:
        """Format raw intelligence data for dashboard consumption."""
        # Ensure all required keys exist with defaults
        formatted = self._get_default_data()

        # Update with actual data where available
        if raw_data:
            for key, default_value in formatted.items():
                if key in raw_data and raw_data[key]:
                    if isinstance(default_value, dict):
                        formatted[key].update(raw_data[key])
                    else:
                        formatted[key] = raw_data[key]

        return formatted

    def get_historical_trends(self, days: int = 7) -> Dict[str, List]:
        """Get historical trends for charts."""
        trends = {
            "health_scores": [],
            "sentiment_scores": [],
            "satisfaction_scores": [],
            "dates": []
        }

        try:
            # Load sentiment history
            if Path(SENTIMENT_LOG).exists():
                sentiment_log = load_json(SENTIMENT_LOG)
                cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

                for date in sorted(sentiment_log.keys()):
                    if date >= cutoff_date:
                        entries = sentiment_log[date]
                        if entries:
                            # Take the latest entry for each day
                            latest_entry = entries[-1]
                            trends["sentiment_scores"].append(latest_entry.get("overall_sentiment", 0.0))
                            trends["satisfaction_scores"].append(latest_entry.get("community_satisfaction", 0.5))
                            trends["dates"].append(date)

            # Load health history
            if Path(COMMUNITY_HEALTH_LOG).exists():
                health_log = load_json(COMMUNITY_HEALTH_LOG)
                cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

                health_scores_by_date = {}
                for date in sorted(health_log.keys()):
                    if date >= cutoff_date:
                        entries = health_log[date]
                        if entries:
                            latest_entry = entries[-1]
                            health_scores_by_date[date] = latest_entry.get("overall_score", 0.5)

                # Align health scores with dates
                for date in trends["dates"]:
                    trends["health_scores"].append(health_scores_by_date.get(date, 0.5))

        except Exception as e:
            print(f"[ERROR] Failed to load historical trends: {e}")

        return trends


class CommunityDashboardHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the community dashboard."""

    def __init__(self, *args, dashboard_data=None, **kwargs):
        self.dashboard_data = dashboard_data
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse.urlparse(self.path)
        path = parsed_path.path

        if path == "/" or path == "/dashboard":
            self._serve_dashboard()
        elif path == "/api/data":
            self._serve_api_data()
        elif path == "/api/trends":
            self._serve_trends_data()
        elif path == "/static/dashboard.css":
            self._serve_css()
        elif path == "/static/dashboard.js":
            self._serve_javascript()
        else:
            self._serve_404()

    def _serve_dashboard(self):
        """Serve the main dashboard HTML."""
        html_content = self._generate_dashboard_html()

        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))

    def _serve_api_data(self):
        """Serve current intelligence data as JSON."""
        try:
            data = self.dashboard_data.get_latest_intelligence_data()

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            json_data = json.dumps(data, indent=2, ensure_ascii=False)
            self.wfile.write(json_data.encode('utf-8'))

        except Exception as e:
            print(f"[ERROR] API data error: {e}")
            self._serve_error(500, "Internal Server Error")

    def _serve_trends_data(self):
        """Serve historical trends data as JSON."""
        try:
            trends = self.dashboard_data.get_historical_trends()

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            json_data = json.dumps(trends, indent=2, ensure_ascii=False)
            self.wfile.write(json_data.encode('utf-8'))

        except Exception as e:
            print(f"[ERROR] Trends data error: {e}")
            self._serve_error(500, "Internal Server Error")

    def _serve_css(self):
        """Serve CSS styles."""
        css_content = self._generate_dashboard_css()

        self.send_response(200)
        self.send_header('Content-Type', 'text/css')
        self.send_header('Cache-Control', 'public, max-age=3600')
        self.end_headers()
        self.wfile.write(css_content.encode('utf-8'))

    def _serve_javascript(self):
        """Serve JavaScript functionality."""
        js_content = self._generate_dashboard_js()

        self.send_response(200)
        self.send_header('Content-Type', 'application/javascript')
        self.send_header('Cache-Control', 'public, max-age=3600')
        self.end_headers()
        self.wfile.write(js_content.encode('utf-8'))

    def _serve_404(self):
        """Serve 404 Not Found."""
        self._serve_error(404, "Not Found")

    def _serve_error(self, code, message):
        """Serve error response."""
        self.send_response(code)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()

        html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Error {code}</title></head>
        <body>
            <h1>Error {code}</h1>
            <p>{message}</p>
            <a href="/">Return to Dashboard</a>
        </body>
        </html>
        """
        self.wfile.write(html.encode('utf-8'))

    def _generate_dashboard_html(self):
        """Generate the main dashboard HTML."""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vawn Community Intelligence Dashboard (APU-51)</title>
    <link rel="stylesheet" href="/static/dashboard.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="dashboard-container">
        <header class="dashboard-header">
            <h1>🎵 Vawn Community Intelligence Dashboard</h1>
            <p class="subtitle">APU-51 Real-time Community Analytics & Insights</p>
            <div class="last-update">
                Last updated: <span id="lastUpdate">Loading...</span>
                <button id="refreshBtn" onclick="refreshData()">🔄 Refresh</button>
            </div>
        </header>

        <main class="dashboard-main">
            <!-- Community Health Overview -->
            <section class="health-overview">
                <h2>Community Health Overview</h2>
                <div class="health-grid">
                    <div class="health-card overall">
                        <h3>Overall Health</h3>
                        <div class="health-score" id="overallHealthScore">0.000</div>
                        <div class="health-status" id="healthStatus">Unknown</div>
                    </div>
                    <div class="health-card sentiment">
                        <h3>Sentiment</h3>
                        <div class="component-score" id="sentimentScore">0.00</div>
                        <div class="score-trend" id="sentimentTrend">—</div>
                    </div>
                    <div class="health-card engagement">
                        <h3>Engagement</h3>
                        <div class="component-score" id="engagementScore">0.00</div>
                        <div class="score-trend" id="engagementTrend">—</div>
                    </div>
                    <div class="health-card response">
                        <h3>Response</h3>
                        <div class="component-score" id="responseScore">0.00</div>
                        <div class="score-trend" id="responseTrend">—</div>
                    </div>
                    <div class="health-card growth">
                        <h3>Growth</h3>
                        <div class="component-score" id="growthScore">0.00</div>
                        <div class="score-trend" id="growthTrend">—</div>
                    </div>
                </div>
            </section>

            <!-- Sentiment Analysis -->
            <section class="sentiment-section">
                <h2>Community Sentiment Analysis</h2>
                <div class="sentiment-grid">
                    <div class="sentiment-overview">
                        <div class="sentiment-gauge">
                            <canvas id="sentimentGauge" width="200" height="200"></canvas>
                            <div class="gauge-labels">
                                <span class="negative">Negative</span>
                                <span class="neutral">Neutral</span>
                                <span class="positive">Positive</span>
                            </div>
                        </div>
                        <div class="sentiment-details">
                            <div class="sentiment-value">
                                <span class="label">Overall Sentiment:</span>
                                <span class="value" id="sentimentValue">0.000</span>
                            </div>
                            <div class="satisfaction-value">
                                <span class="label">Community Satisfaction:</span>
                                <span class="value" id="satisfactionValue">0.00</span>
                            </div>
                            <div class="sentiment-distribution" id="sentimentDistribution">
                                <!-- Distribution bars will be inserted here -->
                            </div>
                        </div>
                    </div>
                    <div class="emotional-themes">
                        <h3>Emotional Themes</h3>
                        <div class="themes-container" id="emotionalThemes">
                            <!-- Emotional themes will be inserted here -->
                        </div>
                    </div>
                </div>
            </section>

            <!-- Platform Performance -->
            <section class="platform-section">
                <h2>Cross-Platform Performance</h2>
                <div class="platform-grid">
                    <div class="platform-overview">
                        <div class="platform-stat">
                            <span class="label">Top Performer:</span>
                            <span class="value" id="topPlatform">Unknown</span>
                        </div>
                        <div class="platform-stat">
                            <span class="label">Avg Performance:</span>
                            <span class="value" id="avgPerformance">0.00</span>
                        </div>
                        <div class="platform-stat">
                            <span class="label">Est. Total Reach:</span>
                            <span class="value" id="totalReach">0</span>
                        </div>
                        <div class="platform-stat">
                            <span class="label">Platform Diversity:</span>
                            <span class="value" id="platformDiversity">0.00</span>
                        </div>
                    </div>
                    <div class="platform-chart">
                        <canvas id="platformChart" width="400" height="200"></canvas>
                    </div>
                </div>
            </section>

            <!-- Predictions & Insights -->
            <section class="predictions-section">
                <h2>Predictive Insights</h2>
                <div class="predictions-grid">
                    <div class="forecast-card">
                        <h3>Sentiment Forecast</h3>
                        <div class="forecast-trend" id="sentimentForecast">Unknown</div>
                        <div class="forecast-confidence" id="sentimentConfidence">0%</div>
                    </div>
                    <div class="forecast-card">
                        <h3>Engagement Forecast</h3>
                        <div class="forecast-trend" id="engagementForecast">Unknown</div>
                        <div class="forecast-confidence" id="engagementForecastConfidence">0%</div>
                    </div>
                    <div class="forecast-card">
                        <h3>Growth Projection</h3>
                        <div class="forecast-trend" id="growthProjection">Unknown</div>
                        <div class="forecast-confidence" id="growthConfidence">0%</div>
                    </div>
                </div>
                <div class="opportunities-section">
                    <h3>Growth Opportunities</h3>
                    <div class="opportunities-list" id="opportunitiesList">
                        <!-- Opportunities will be inserted here -->
                    </div>
                </div>
            </section>

            <!-- Alerts & Recommendations -->
            <section class="alerts-section">
                <h2>Intelligence Alerts & Recommendations</h2>
                <div class="alerts-container" id="alertsContainer">
                    <!-- Alerts will be inserted here -->
                </div>
            </section>

            <!-- Historical Trends -->
            <section class="trends-section">
                <h2>Historical Trends (7 Days)</h2>
                <div class="trends-chart">
                    <canvas id="trendsChart" width="800" height="300"></canvas>
                </div>
            </section>

            <!-- Community Strengths & Improvements -->
            <section class="insights-section">
                <h2>Community Insights</h2>
                <div class="insights-grid">
                    <div class="strengths-card">
                        <h3>💪 Strengths</h3>
                        <div class="insights-list" id="strengthsList">
                            <!-- Strengths will be inserted here -->
                        </div>
                    </div>
                    <div class="improvements-card">
                        <h3>🔧 Areas for Improvement</h3>
                        <div class="insights-list" id="improvementsList">
                            <!-- Improvements will be inserted here -->
                        </div>
                    </div>
                </div>
            </section>
        </main>

        <footer class="dashboard-footer">
            <p>APU-51 Community Intelligence Engine | Dex - Community Agent</p>
            <p>Auto-refresh: <span id="autoRefreshStatus">ON</span> (every 30s)</p>
        </footer>
    </div>

    <script src="/static/dashboard.js"></script>
</body>
</html>
        '''

    def _generate_dashboard_css(self):
        """Generate CSS styles for the dashboard."""
        return '''
/* APU-51 Community Intelligence Dashboard Styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f172a 100%);
    color: #e2e8f0;
    line-height: 1.6;
    min-height: 100vh;
}

.dashboard-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
}

.dashboard-header {
    text-align: center;
    margin-bottom: 40px;
    padding: 30px;
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
    border-radius: 15px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.dashboard-header h1 {
    font-size: 2.5rem;
    margin-bottom: 10px;
    background: linear-gradient(135deg, #60a5fa, #a78bfa, #f472b6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.subtitle {
    color: #94a3b8;
    font-size: 1.1rem;
    margin-bottom: 20px;
}

.last-update {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 15px;
    color: #cbd5e1;
}

#refreshBtn {
    background: linear-gradient(135deg, #3b82f6, #6366f1);
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.2s ease;
}

#refreshBtn:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

.dashboard-main {
    display: grid;
    gap: 30px;
}

section {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
    border-radius: 15px;
    padding: 25px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

section h2 {
    font-size: 1.5rem;
    margin-bottom: 20px;
    color: #f1f5f9;
    border-bottom: 2px solid rgba(96, 165, 250, 0.3);
    padding-bottom: 10px;
}

/* Health Overview */
.health-grid {
    display: grid;
    grid-template-columns: 2fr repeat(4, 1fr);
    gap: 20px;
}

.health-card {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    border: 1px solid rgba(255, 255, 255, 0.1);
    transition: all 0.3s ease;
}

.health-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
}

.health-card.overall {
    background: linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(59, 130, 246, 0.2));
}

.health-card h3 {
    color: #cbd5e1;
    font-size: 0.9rem;
    margin-bottom: 10px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.health-score {
    font-size: 2.5rem;
    font-weight: 700;
    color: #22c55e;
    margin-bottom: 5px;
}

.health-status {
    color: #94a3b8;
    text-transform: capitalize;
    font-size: 0.9rem;
}

.component-score {
    font-size: 1.8rem;
    font-weight: 600;
    color: #60a5fa;
    margin-bottom: 5px;
}

.score-trend {
    color: #94a3b8;
    font-size: 0.8rem;
}

/* Sentiment Section */
.sentiment-grid {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 30px;
}

.sentiment-overview {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 30px;
    align-items: center;
}

.sentiment-gauge {
    position: relative;
    text-align: center;
}

.gauge-labels {
    display: flex;
    justify-content: space-between;
    margin-top: 10px;
    font-size: 0.8rem;
}

.gauge-labels .negative { color: #ef4444; }
.gauge-labels .neutral { color: #94a3b8; }
.gauge-labels .positive { color: #22c55e; }

.sentiment-details {
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.sentiment-value, .satisfaction-value {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 15px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
}

.sentiment-value .label, .satisfaction-value .label {
    color: #cbd5e1;
}

.sentiment-value .value, .satisfaction-value .value {
    font-weight: 600;
    color: #60a5fa;
}

.sentiment-distribution {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.distribution-bar {
    display: flex;
    align-items: center;
    gap: 10px;
}

.distribution-label {
    min-width: 60px;
    font-size: 0.9rem;
    color: #cbd5e1;
}

.distribution-progress {
    flex: 1;
    height: 6px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 3px;
    overflow: hidden;
}

.distribution-fill {
    height: 100%;
    border-radius: 3px;
    transition: width 0.5s ease;
}

.distribution-fill.positive { background: #22c55e; }
.distribution-fill.neutral { background: #94a3b8; }
.distribution-fill.negative { background: #ef4444; }

.distribution-count {
    min-width: 30px;
    text-align: right;
    font-size: 0.9rem;
    color: #94a3b8;
}

.emotional-themes h3 {
    margin-bottom: 15px;
    color: #f1f5f9;
}

.themes-container {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.theme-tag {
    background: linear-gradient(135deg, rgba(167, 139, 250, 0.2), rgba(244, 114, 182, 0.2));
    color: #e2e8f0;
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 0.85rem;
    border: 1px solid rgba(167, 139, 250, 0.3);
}

/* Platform Section */
.platform-grid {
    display: grid;
    grid-template-columns: 1fr 2fr;
    gap: 30px;
}

.platform-overview {
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.platform-stat {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 15px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    border-left: 4px solid #60a5fa;
}

.platform-stat .label {
    color: #cbd5e1;
}

.platform-stat .value {
    font-weight: 600;
    color: #f1f5f9;
}

/* Predictions Section */
.predictions-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
    margin-bottom: 25px;
}

.forecast-card {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.forecast-card h3 {
    color: #cbd5e1;
    font-size: 0.9rem;
    margin-bottom: 15px;
    text-transform: uppercase;
}

.forecast-trend {
    font-size: 1.3rem;
    font-weight: 600;
    margin-bottom: 8px;
    text-transform: capitalize;
}

.forecast-trend.improving { color: #22c55e; }
.forecast-trend.declining { color: #ef4444; }
.forecast-trend.stable { color: #94a3b8; }
.forecast-trend.positive { color: #22c55e; }
.forecast-trend.at_risk { color: #ef4444; }

.forecast-confidence {
    color: #94a3b8;
    font-size: 0.9rem;
}

.opportunities-section h3 {
    margin-bottom: 15px;
    color: #f1f5f9;
}

.opportunities-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.opportunity-item {
    background: rgba(34, 197, 94, 0.1);
    border: 1px solid rgba(34, 197, 94, 0.3);
    border-radius: 8px;
    padding: 15px;
}

.opportunity-title {
    font-weight: 600;
    color: #22c55e;
    margin-bottom: 5px;
}

.opportunity-description {
    color: #cbd5e1;
    font-size: 0.9rem;
}

/* Alerts Section */
.alerts-container {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.alert-item {
    border-radius: 8px;
    padding: 15px;
    border-left: 4px solid;
}

.alert-item.critical {
    background: rgba(239, 68, 68, 0.1);
    border-left-color: #ef4444;
}

.alert-item.high {
    background: rgba(249, 115, 22, 0.1);
    border-left-color: #f97316;
}

.alert-item.medium {
    background: rgba(234, 179, 8, 0.1);
    border-left-color: #eab308;
}

.alert-item.low {
    background: rgba(59, 130, 246, 0.1);
    border-left-color: #3b82f6;
}

.alert-item.info {
    background: rgba(107, 114, 128, 0.1);
    border-left-color: #6b7280;
}

.alert-severity {
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 5px;
}

.alert-severity.critical { color: #ef4444; }
.alert-severity.high { color: #f97316; }
.alert-severity.medium { color: #eab308; }
.alert-severity.low { color: #3b82f6; }
.alert-severity.info { color: #6b7280; }

.alert-message {
    color: #f1f5f9;
    margin-bottom: 8px;
    font-weight: 500;
}

.alert-recommendation {
    color: #94a3b8;
    font-size: 0.9rem;
    font-style: italic;
}

/* Insights Section */
.insights-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 25px;
}

.strengths-card, .improvements-card {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    padding: 20px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.strengths-card h3 {
    color: #22c55e;
    margin-bottom: 15px;
}

.improvements-card h3 {
    color: #f97316;
    margin-bottom: 15px;
}

.insights-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.insight-item {
    padding: 10px 15px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 6px;
    color: #cbd5e1;
    font-size: 0.9rem;
}

.insight-item.strength {
    border-left: 3px solid #22c55e;
}

.insight-item.improvement {
    border-left: 3px solid #f97316;
}

/* Trends Chart */
.trends-chart {
    height: 300px;
}

.dashboard-footer {
    margin-top: 40px;
    text-align: center;
    padding: 20px;
    color: #64748b;
    font-size: 0.9rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
}

/* Responsive Design */
@media (max-width: 1200px) {
    .health-grid {
        grid-template-columns: 1fr;
    }

    .platform-grid,
    .sentiment-grid {
        grid-template-columns: 1fr;
    }

    .predictions-grid {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 768px) {
    .dashboard-container {
        padding: 10px;
    }

    .dashboard-header h1 {
        font-size: 1.8rem;
    }

    .insights-grid {
        grid-template-columns: 1fr;
    }

    section {
        padding: 15px;
    }
}

/* Loading States */
.loading {
    opacity: 0.6;
    pointer-events: none;
}

.loading::after {
    content: "";
    position: absolute;
    top: 50%;
    left: 50%;
    width: 20px;
    height: 20px;
    margin: -10px 0 0 -10px;
    border: 2px solid #60a5fa;
    border-top: 2px solid transparent;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Status Colors */
.status-excellent { color: #22c55e; }
.status-good { color: #84cc16; }
.status-fair { color: #eab308; }
.status-poor { color: #f97316; }
.status-critical { color: #ef4444; }
.status-unknown { color: #94a3b8; }
        '''

    def _generate_dashboard_js(self):
        """Generate JavaScript functionality for the dashboard."""
        return f'''
// APU-51 Community Intelligence Dashboard JavaScript

let currentData = null;
let chartsInitialized = false;
let charts = {{}};
let autoRefreshInterval = null;

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {{
    console.log('APU-51 Community Dashboard initializing...');
    initializeDashboard();
}});

async function initializeDashboard() {{
    try {{
        await loadData();
        startAutoRefresh();
        console.log('Dashboard initialized successfully');
    }} catch (error) {{
        console.error('Failed to initialize dashboard:', error);
        showError('Failed to initialize dashboard. Please refresh the page.');
    }}
}}

async function loadData() {{
    try {{
        console.log('Loading community intelligence data...');

        // Show loading state
        document.body.classList.add('loading');

        // Fetch current data
        const response = await fetch('/api/data');
        if (!response.ok) {{
            throw new Error(`HTTP ${{response.status}}: ${{response.statusText}}`);
        }}

        currentData = await response.json();
        console.log('Data loaded:', currentData);

        // Update all dashboard components
        updateHealthOverview();
        updateSentimentAnalysis();
        updatePlatformPerformance();
        updatePredictions();
        updateAlerts();
        updateInsights();
        await updateTrendsChart();
        updateLastUpdateTime();

        // Remove loading state
        document.body.classList.remove('loading');

    }} catch (error) {{
        console.error('Failed to load data:', error);
        document.body.classList.remove('loading');
        showError(`Failed to load data: ${{error.message}}`);
    }}
}}

function updateHealthOverview() {{
    if (!currentData?.community_health) return;

    const health = currentData.community_health;
    const components = health.component_scores || {{}};

    // Overall health
    document.getElementById('overallHealthScore').textContent = health.overall_score?.toFixed(3) || '0.000';

    const healthStatus = document.getElementById('healthStatus');
    healthStatus.textContent = (health.health_status || 'unknown').replace('_', ' ').toUpperCase();
    healthStatus.className = `health-status status-${{health.health_status || 'unknown'}}`;

    // Component scores
    document.getElementById('sentimentScore').textContent = components.sentiment?.toFixed(2) || '0.00';
    document.getElementById('engagementScore').textContent = components.engagement?.toFixed(2) || '0.00';
    document.getElementById('responseScore').textContent = components.response?.toFixed(2) || '0.00';
    document.getElementById('growthScore').textContent = components.growth?.toFixed(2) || '0.00';
}}

function updateSentimentAnalysis() {{
    if (!currentData?.sentiment_analysis) return;

    const sentiment = currentData.sentiment_analysis;

    // Sentiment value and satisfaction
    document.getElementById('sentimentValue').textContent = sentiment.overall_sentiment?.toFixed(3) || '0.000';
    document.getElementById('satisfactionValue').textContent = sentiment.community_satisfaction?.toFixed(2) || '0.00';

    // Sentiment gauge chart
    updateSentimentGauge(sentiment.overall_sentiment || 0);

    // Sentiment distribution
    updateSentimentDistribution(sentiment.sentiment_distribution || {{}});

    // Emotional themes
    updateEmotionalThemes(sentiment.emotional_themes || []);
}}

function updateSentimentGauge(sentimentValue) {{
    const canvas = document.getElementById('sentimentGauge');
    const ctx = canvas.getContext('2d');

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = 80;

    // Draw gauge background
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
    ctx.lineWidth = 10;
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, Math.PI, 2 * Math.PI);
    ctx.stroke();

    // Calculate angle for sentiment (-1 to 1 becomes π to 2π)
    const angle = Math.PI + (sentimentValue + 1) / 2 * Math.PI;

    // Determine color based on sentiment
    let color;
    if (sentimentValue > 0.3) {{
        color = '#22c55e'; // Green for positive
    }} else if (sentimentValue < -0.3) {{
        color = '#ef4444'; // Red for negative
    }} else {{
        color = '#94a3b8'; // Gray for neutral
    }}

    // Draw sentiment arc
    ctx.strokeStyle = color;
    ctx.lineWidth = 10;
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, Math.PI, angle);
    ctx.stroke();

    // Draw needle
    ctx.strokeStyle = '#f1f5f9';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(centerX, centerY);
    const needleX = centerX + Math.cos(angle - Math.PI / 2) * (radius - 10);
    const needleY = centerY + Math.sin(angle - Math.PI / 2) * (radius - 10);
    ctx.lineTo(needleX, needleY);
    ctx.stroke();

    // Draw center dot
    ctx.fillStyle = '#f1f5f9';
    ctx.beginPath();
    ctx.arc(centerX, centerY, 3, 0, 2 * Math.PI);
    ctx.fill();

    // Draw sentiment value text
    ctx.fillStyle = color;
    ctx.font = 'bold 16px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(sentimentValue.toFixed(3), centerX, centerY + 25);
}}

function updateSentimentDistribution(distribution) {{
    const container = document.getElementById('sentimentDistribution');
    const total = (distribution.positive || 0) + (distribution.neutral || 0) + (distribution.negative || 0);

    if (total === 0) {{
        container.innerHTML = '<p style="color: #94a3b8; font-style: italic;">No sentiment data available</p>';
        return;
    }}

    const types = [
        {{ key: 'positive', label: 'Positive', color: 'positive' }},
        {{ key: 'neutral', label: 'Neutral', color: 'neutral' }},
        {{ key: 'negative', label: 'Negative', color: 'negative' }}
    ];

    container.innerHTML = types.map(type => {{
        const count = distribution[type.key] || 0;
        const percentage = (count / total) * 100;

        return `
            <div class="distribution-bar">
                <div class="distribution-label">${{type.label}}</div>
                <div class="distribution-progress">
                    <div class="distribution-fill ${{type.color}}" style="width: ${{percentage}}%"></div>
                </div>
                <div class="distribution-count">${{count}}</div>
            </div>
        `;
    }}).join('');
}}

function updateEmotionalThemes(themes) {{
    const container = document.getElementById('emotionalThemes');

    if (!themes || themes.length === 0) {{
        container.innerHTML = '<p style="color: #94a3b8; font-style: italic;">No emotional themes detected</p>';
        return;
    }}

    container.innerHTML = themes.map(theme =>
        `<span class="theme-tag">${{theme}}</span>`
    ).join('');
}}

function updatePlatformPerformance() {{
    if (!currentData?.cross_platform_analysis) return;

    const analysis = currentData.cross_platform_analysis;
    const trends = analysis.cross_platform_trends || {{}};

    // Update platform overview stats
    document.getElementById('topPlatform').textContent = (trends.top_performer || 'unknown').toUpperCase();
    document.getElementById('avgPerformance').textContent = trends.average_performance?.toFixed(2) || '0.00';
    document.getElementById('totalReach').textContent = (trends.total_reach_estimate || 0).toLocaleString();
    document.getElementById('platformDiversity').textContent = trends.platform_diversity_score?.toFixed(2) || '0.00';

    // Update platform performance chart
    updatePlatformChart(analysis.platform_performance || {{}});
}}

function updatePlatformChart(platformData) {{
    const canvas = document.getElementById('platformChart');
    const ctx = canvas.getContext('2d');

    // Destroy existing chart if it exists
    if (charts.platform) {{
        charts.platform.destroy();
    }}

    const platforms = Object.keys(platformData);
    const scores = platforms.map(platform => platformData[platform]?.performance_score || 0);

    charts.platform = new Chart(ctx, {{
        type: 'bar',
        data: {{
            labels: platforms.map(p => p.toUpperCase()),
            datasets: [{{
                label: 'Performance Score',
                data: scores,
                backgroundColor: [
                    'rgba(59, 130, 246, 0.7)',
                    'rgba(34, 197, 94, 0.7)',
                    'rgba(167, 139, 250, 0.7)',
                    'rgba(244, 114, 182, 0.7)',
                    'rgba(249, 115, 22, 0.7)'
                ],
                borderColor: [
                    'rgba(59, 130, 246, 1)',
                    'rgba(34, 197, 94, 1)',
                    'rgba(167, 139, 250, 1)',
                    'rgba(244, 114, 182, 1)',
                    'rgba(249, 115, 22, 1)'
                ],
                borderWidth: 1
            }}]
        }},
        options: {{
            responsive: true,
            plugins: {{
                legend: {{
                    display: false
                }}
            }},
            scales: {{
                y: {{
                    beginAtZero: true,
                    max: 1,
                    ticks: {{
                        color: '#94a3b8'
                    }},
                    grid: {{
                        color: 'rgba(255, 255, 255, 0.1)'
                    }}
                }},
                x: {{
                    ticks: {{
                        color: '#94a3b8'
                    }},
                    grid: {{
                        color: 'rgba(255, 255, 255, 0.1)'
                    }}
                }}
            }}
        }}
    }});
}}

function updatePredictions() {{
    if (!currentData?.predictions) return;

    const predictions = currentData.predictions;

    // Sentiment forecast
    const sentimentForecast = predictions.sentiment_forecast || {{}};
    updateForecastElement('sentimentForecast', sentimentForecast.predicted_trend);
    updateForecastElement('sentimentConfidence', Math.round((sentimentForecast.confidence || 0) * 100) + '%');

    // Engagement forecast
    const engagementForecast = predictions.engagement_forecast || {{}};
    updateForecastElement('engagementForecast', engagementForecast.predicted_trend);
    updateForecastElement('engagementForecastConfidence', Math.round((engagementForecast.confidence || 0) * 100) + '%');

    // Growth projection
    const growthProjection = predictions.community_growth_projection || {{}};
    updateForecastElement('growthProjection', growthProjection.projected_growth);
    updateForecastElement('growthConfidence', Math.round((growthProjection.confidence || 0) * 100) + '%');

    // Opportunities
    updateOpportunities(predictions.opportunities || []);
}}

function updateForecastElement(elementId, value) {{
    const element = document.getElementById(elementId);
    if (element) {{
        element.textContent = value || 'unknown';
        element.className = `forecast-trend ${{value || 'unknown'}}`;
    }}
}}

function updateOpportunities(opportunities) {{
    const container = document.getElementById('opportunitiesList');

    if (!opportunities || opportunities.length === 0) {{
        container.innerHTML = '<p style="color: #94a3b8; font-style: italic;">No growth opportunities identified</p>';
        return;
    }}

    container.innerHTML = opportunities.map(opp => `
        <div class="opportunity-item">
            <div class="opportunity-title">${{opp.description || 'Opportunity'}}</div>
            <div class="opportunity-description">Potential: ${{(opp.potential || 'unknown').toUpperCase()}} | ${{opp.recommended_action || 'No action specified'}}</div>
        </div>
    `).join('');
}}

function updateAlerts() {{
    if (!currentData?.intelligence_alerts) return;

    const alerts = currentData.intelligence_alerts;
    const container = document.getElementById('alertsContainer');

    if (!alerts || alerts.length === 0) {{
        container.innerHTML = '<div class="alert-item info"><div class="alert-severity info">INFO</div><div class="alert-message">All community intelligence metrics within normal ranges</div></div>';
        return;
    }}

    container.innerHTML = alerts.map(alert => `
        <div class="alert-item ${{alert.severity || 'info'}}">
            <div class="alert-severity ${{alert.severity || 'info'}}">${{(alert.severity || 'info').toUpperCase()}}</div>
            <div class="alert-message">${{alert.message || 'No message'}}</div>
            ${{alert.recommendation ? `<div class="alert-recommendation">→ ${{alert.recommendation}}</div>` : ''}}
        </div>
    `).join('');
}}

function updateInsights() {{
    if (!currentData?.community_health) return;

    const health = currentData.community_health;

    // Update strengths
    const strengthsList = document.getElementById('strengthsList');
    const strengths = health.strengths || [];

    if (strengths.length === 0) {{
        strengthsList.innerHTML = '<div class="insight-item">No specific strengths identified</div>';
    }} else {{
        strengthsList.innerHTML = strengths.map(strength =>
            `<div class="insight-item strength">${{strength}}</div>`
        ).join('');
    }}

    // Update improvements
    const improvementsList = document.getElementById('improvementsList');
    const improvements = health.improvement_areas || [];

    if (improvements.length === 0) {{
        improvementsList.innerHTML = '<div class="insight-item">No specific improvements needed</div>';
    }} else {{
        improvementsList.innerHTML = improvements.map(improvement =>
            `<div class="insight-item improvement">${{improvement}}</div>`
        ).join('');
    }}
}}

async function updateTrendsChart() {{
    try {{
        const response = await fetch('/api/trends');
        if (!response.ok) return;

        const trendsData = await response.json();

        const canvas = document.getElementById('trendsChart');
        const ctx = canvas.getContext('2d');

        // Destroy existing chart if it exists
        if (charts.trends) {{
            charts.trends.destroy();
        }}

        charts.trends = new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: trendsData.dates || [],
                datasets: [
                    {{
                        label: 'Community Health',
                        data: trendsData.health_scores || [],
                        borderColor: '#60a5fa',
                        backgroundColor: 'rgba(96, 165, 250, 0.1)',
                        tension: 0.4
                    }},
                    {{
                        label: 'Sentiment',
                        data: trendsData.sentiment_scores || [],
                        borderColor: '#22c55e',
                        backgroundColor: 'rgba(34, 197, 94, 0.1)',
                        tension: 0.4
                    }},
                    {{
                        label: 'Satisfaction',
                        data: trendsData.satisfaction_scores || [],
                        borderColor: '#a78bfa',
                        backgroundColor: 'rgba(167, 139, 250, 0.1)',
                        tension: 0.4
                    }}
                ]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        labels: {{
                            color: '#94a3b8'
                        }}
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        ticks: {{
                            color: '#94a3b8'
                        }},
                        grid: {{
                            color: 'rgba(255, 255, 255, 0.1)'
                        }}
                    }},
                    x: {{
                        ticks: {{
                            color: '#94a3b8'
                        }},
                        grid: {{
                            color: 'rgba(255, 255, 255, 0.1)'
                        }}
                    }}
                }}
            }}
        }});

    }} catch (error) {{
        console.error('Failed to update trends chart:', error);
    }}
}}

function updateLastUpdateTime() {{
    const now = new Date();
    document.getElementById('lastUpdate').textContent = now.toLocaleString();
}}

function refreshData() {{
    console.log('Manual refresh triggered');
    loadData();
}}

function startAutoRefresh() {{
    // Clear any existing interval
    if (autoRefreshInterval) {{
        clearInterval(autoRefreshInterval);
    }}

    // Start new interval
    autoRefreshInterval = setInterval(() => {{
        console.log('Auto-refresh triggered');
        loadData();
    }}, {REFRESH_INTERVAL * 1000});

    document.getElementById('autoRefreshStatus').textContent = 'ON';
    console.log(`Auto-refresh started (every {REFRESH_INTERVAL}s)`);
}}

function showError(message) {{
    // Simple error display - could be enhanced with a proper notification system
    console.error('Dashboard Error:', message);

    // You could add a notification system here
    const alertsContainer = document.getElementById('alertsContainer');
    if (alertsContainer) {{
        alertsContainer.innerHTML = `
            <div class="alert-item critical">
                <div class="alert-severity critical">ERROR</div>
                <div class="alert-message">Dashboard Error: ${{message}}</div>
                <div class="alert-recommendation">→ Try refreshing the page or check the APU-51 system status</div>
            </div>
        ` + alertsContainer.innerHTML;
    }}
}}

// Cleanup on page unload
window.addEventListener('beforeunload', function() {{
    if (autoRefreshInterval) {{
        clearInterval(autoRefreshInterval);
    }}

    // Destroy all charts
    Object.values(charts).forEach(chart => {{
        if (chart && chart.destroy) {{
            chart.destroy();
        }}
    }});
}});
        '''

    def log_message(self, format, *args):
        """Suppress default HTTP server logging."""
        pass  # Comment out to enable logging


def create_dashboard_handler(dashboard_data):
    """Create a dashboard handler with data dependency injection."""
    class DashboardHandler(CommunityDashboardHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, dashboard_data=dashboard_data, **kwargs)
    return DashboardHandler


def run_dashboard_server():
    """Run the community intelligence dashboard server."""
    print(f"\n[*] Starting APU-51 Community Intelligence Dashboard...")
    print(f"[SERVER] Starting on http://{DASHBOARD_HOST}:{DASHBOARD_PORT}")

    # Initialize data manager
    dashboard_data = CommunityDashboardData()

    # Create HTTP server
    handler_class = create_dashboard_handler(dashboard_data)
    server = HTTPServer((DASHBOARD_HOST, DASHBOARD_PORT), handler_class)

    print(f"[READY] Dashboard available at: http://{DASHBOARD_HOST}:{DASHBOARD_PORT}")
    print(f"[INFO] Auto-refresh interval: {REFRESH_INTERVAL} seconds")
    print(f"[INFO] Press Ctrl+C to stop the server")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n[STOP] Shutting down dashboard server...")
        server.shutdown()
        server.server_close()
        print(f"[STOPPED] Dashboard server stopped")


def main():
    """Main dashboard application entry point."""
    try:
        run_dashboard_server()
    except Exception as e:
        print(f"[ERROR] Dashboard failed to start: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())