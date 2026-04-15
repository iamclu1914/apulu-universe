# APU-51 Community Intelligence Engine

## Overview

The APU-51 Community Intelligence Engine is an advanced community analytics and monitoring system that builds upon the existing APU-37 engagement monitoring infrastructure. It provides real-time community sentiment analysis, cross-platform engagement correlation, predictive analytics, and automated community strategy recommendations.

**Created by:** Dex - Community Agent (APU-51)  
**Version:** 1.0  
**Integration:** Seamless with APU-37 monitoring systems

## System Architecture

### Core Components

1. **Community Intelligence Engine** (`engagement_monitor_apu51.py`)
   - Advanced sentiment analysis using Claude AI
   - Cross-platform engagement correlation
   - Community health scoring system
   - Predictive analytics and forecasting
   - Automated recommendation generation

2. **Real-time Dashboard** (`src/community_dashboard_apu51.py`)
   - Interactive web interface at `http://localhost:8051`
   - Real-time community health visualization
   - Historical trends and analytics
   - Alert management and recommendations
   - Auto-refresh every 30 seconds

3. **Data Integration Layer**
   - Seamless integration with APU-37 monitoring
   - Persistent storage in research directory
   - Cross-system data sharing and compatibility

### Data Flow Architecture

```
APU-37 Systems → APU-51 Intelligence Engine → Analytics & Insights → Real-time Dashboard
     ↓                        ↓                       ↓                    ↓
[Agent Health]    [Community Sentiment]    [Predictions]      [Interactive UI]
[API Monitoring]  [Cross-Platform Data]    [Health Scores]    [Live Alerts]
[Engagement Log]  [Predictive Models]      [Recommendations]  [Trend Charts]
```

## Features

### 1. Community Sentiment Analysis
- **Real-time sentiment scoring** of comments and community responses
- **Emotional tone tracking** across all platforms (positive, neutral, negative)
- **Response quality assessment** measuring community satisfaction
- **Sentiment trend analysis** with directional indicators
- **Emotional theme identification** from community interactions

### 2. Cross-Platform Engagement Correlation
- **Platform performance comparison** with normalized metrics
- **Content strategy effectiveness** tracking across 5 platforms
- **Optimal timing analysis** based on engagement patterns
- **Audience overlap analysis** and reach estimation
- **Performance diversity scoring** for platform balance

### 3. Community Health Scoring System
- **Overall health score** (0.0-1.0 scale) with status classification
- **Component scoring**: Sentiment (40%), Engagement (30%), Response (20%), Growth (10%)
- **Health status categories**: Excellent (0.85+), Good (0.70+), Fair (0.55+), Poor (0.40+), Critical (<0.40)
- **Strength and improvement identification** with actionable insights
- **Historical health tracking** with trend analysis

### 4. Predictive Community Analytics
- **Engagement trend forecasting** using historical patterns
- **Community risk detection** for declining engagement/sentiment
- **Content performance prediction** based on community behavior
- **Optimal content scheduling** recommendations
- **Growth opportunity identification** with potential impact scoring

### 5. Real-time Community Intelligence Dashboard
- **Live sentiment monitoring** with alert thresholds
- **Community growth tracking** with real-time metrics
- **Platform performance visualization** with interactive charts
- **Automated recommendation alerts** for community managers
- **Historical trends display** (7-day rolling window)

## Installation & Setup

### Prerequisites
- Python 3.8+ with existing Vawn project dependencies
- APU-37 monitoring systems (recommended but not required)
- Claude AI API access (configured in `vawn_config.py`)

### Setup Steps

1. **Files are already installed** in the Vawn project directory:
   - `engagement_monitor_apu51.py` (main intelligence engine)
   - `src/community_dashboard_apu51.py` (real-time dashboard)

2. **No additional dependencies** required (uses existing project libraries)

3. **Configuration** is automatic via existing `vawn_config.py`

## Usage

### Running the Community Intelligence Engine

```bash
# Run complete community intelligence analysis
python engagement_monitor_apu51.py

# Expected output:
# - Community health analysis
# - Sentiment scoring
# - Cross-platform correlations
# - Predictive insights
# - Intelligence alerts
# - Comprehensive dashboard report
```

### Starting the Real-time Dashboard

```bash
# Start the dashboard server
cd src
python community_dashboard_apu51.py

# Access dashboard at: http://localhost:8051
# Features:
# - Real-time community metrics
# - Interactive charts and gauges
# - Historical trend visualization
# - Alert management interface
# - Auto-refresh every 30 seconds
```

### Integration with Existing Workflows

The APU-51 system automatically integrates with:
- **APU-37 agent health monitoring** (automatic fallback if not available)
- **Existing engagement logs** for sentiment analysis
- **Current metrics tracking** for cross-platform analysis
- **Research directory structure** for persistent storage

## Configuration

### Alert Thresholds (in `engagement_monitor_apu51.py`)

```python
ALERT_THRESHOLDS = {
    "sentiment_drop": -0.2,           # Alert if sentiment drops by 0.2 points
    "engagement_drop": 0.3,           # Alert if engagement drops by 30%
    "response_time_increase": 2.0,    # Alert if response time doubles
    "community_health_drop": 0.15     # Alert if health drops by 0.15 points
}
```

### Sentiment Analysis Configuration

```python
SENTIMENT_ANALYSIS_CONFIG = {
    "batch_size": 50,                 # Comments analyzed per batch
    "lookback_days": 7,               # Days of history to analyze
    "sentiment_threshold_negative": -0.3,  # Negative sentiment threshold
    "sentiment_threshold_positive": 0.3,   # Positive sentiment threshold
    "trend_significance_threshold": 0.15   # Minimum change for trend detection
}
```

### Community Health Thresholds

```python
COMMUNITY_HEALTH_THRESHOLDS = {
    "excellent": 0.85,    # 85%+ health score
    "good": 0.70,         # 70-84% health score
    "fair": 0.55,         # 55-69% health score
    "poor": 0.40,         # 40-54% health score
    "critical": 0.25      # <40% health score
}
```

### Dashboard Configuration

```python
DASHBOARD_PORT = 8051             # Dashboard port (change if needed)
DASHBOARD_HOST = "localhost"      # Dashboard host
REFRESH_INTERVAL = 30             # Auto-refresh interval (seconds)
```

## Data Storage

### Generated Log Files

The APU-51 system creates the following log files in the `research/` directory:

1. **`community_intelligence_apu51_log.json`**
   - Complete intelligence reports with all analysis data
   - Includes community health, sentiment, predictions, alerts
   - Daily entries with timestamp tracking

2. **`community_sentiment_log.json`**
   - Dedicated sentiment analysis history
   - Tracks sentiment trends, themes, satisfaction scores
   - Used for trend analysis and forecasting

3. **`community_health_log.json`**
   - Community health score history
   - Component scores, strengths, improvement areas
   - Historical health tracking for dashboard charts

4. **`community_predictions_log.json`**
   - Predictive analytics results (if enabled)
   - Forecasting models and confidence scores
   - Growth projections and opportunity tracking

### Data Retention

- **Log files**: 30-day rolling retention
- **Dashboard cache**: Session-based, cleared on restart
- **Integration data**: Uses existing APU-37 retention policies

## API Reference

### Dashboard API Endpoints

The real-time dashboard provides REST API endpoints:

#### GET `/api/data`
Returns current community intelligence data in JSON format.

**Response Structure:**
```json
{
  "timestamp": "2026-04-11T02:09:11.696958",
  "community_health": {
    "overall_score": 0.750,
    "health_status": "good",
    "component_scores": {
      "sentiment": 0.80,
      "engagement": 0.75,
      "response": 0.85,
      "growth": 0.60
    },
    "strengths": ["Excellent community sentiment"],
    "improvement_areas": []
  },
  "sentiment_analysis": {
    "overall_sentiment": 0.150,
    "community_satisfaction": 0.75,
    "sentiment_distribution": {
      "positive": 15,
      "neutral": 8,
      "negative": 2
    },
    "emotional_themes": ["appreciation", "excitement"],
    "sentiment_trend": "improving"
  },
  "cross_platform_analysis": {
    "cross_platform_trends": {
      "top_performer": "instagram",
      "average_performance": 0.65,
      "platform_diversity_score": 0.80,
      "total_reach_estimate": 12500
    }
  },
  "predictions": {
    "sentiment_forecast": {
      "predicted_trend": "stable_positive",
      "confidence": 0.7
    },
    "engagement_forecast": {
      "predicted_trend": "growing",
      "confidence": 0.6
    }
  },
  "intelligence_alerts": []
}
```

#### GET `/api/trends`
Returns historical trend data for charts (7-day window).

**Response Structure:**
```json
{
  "health_scores": [0.65, 0.70, 0.68, 0.75, 0.72, 0.78, 0.75],
  "sentiment_scores": [0.10, 0.15, 0.12, 0.18, 0.20, 0.15, 0.18],
  "satisfaction_scores": [0.70, 0.72, 0.68, 0.75, 0.78, 0.75, 0.77],
  "dates": ["2026-04-04", "2026-04-05", "2026-04-06", "2026-04-07", "2026-04-08", "2026-04-09", "2026-04-10"]
}
```

## Integration with APU-37 Systems

### Seamless Integration Features

1. **Agent Health Monitoring**
   - Automatically imports APU-37 agent health functions
   - Uses existing agent status in community health calculations
   - Fallback mode if APU-37 systems unavailable

2. **Data Compatibility**
   - Reads existing engagement logs and metrics
   - Maintains compatibility with APU-37 data formats
   - Shared configuration via `vawn_config.py`

3. **Logging Integration**
   - Uses existing `log_run()` function for main system logging
   - Integrates with research log structure
   - Maintains APU-37 logging patterns

### APU-37 System Dependencies

**Required (automatic fallback if missing):**
- `engagement_monitor_enhanced.py` - For agent health integration
- `ENGAGEMENT_LOG`, `RESEARCH_LOG`, `METRICS_LOG` - For data sources

**Recommended:**
- All APU-37 monitoring components for full functionality
- Existing agent infrastructure for comprehensive health scoring

## Troubleshooting

### Common Issues

#### 1. Unicode Encoding Errors (Windows)
**Error:** `UnicodeEncodeError: 'charmap' codec can't encode character`

**Solution:** Already fixed in APU-51 v1.0 - all Unicode characters replaced with ASCII equivalents.

#### 2. Dashboard Not Starting
**Error:** Port 8051 already in use

**Solutions:**
```bash
# Check if port is in use
netstat -an | grep 8051

# Kill existing process
taskkill /f /im python.exe

# Or change port in dashboard configuration
DASHBOARD_PORT = 8052  # Use different port
```

#### 3. No Sentiment Data
**Issue:** Sentiment analysis shows "No data available"

**Causes & Solutions:**
- **No recent comments:** Normal if no community activity in last 24 hours
- **Missing Claude AI access:** Check `vawn_config.py` configuration
- **Empty engagement log:** Ensure APU-37 engagement agents are running

#### 4. Integration Failures
**Issue:** "APU-37 integration failed"

**Solutions:**
- Check if APU-37 files exist in project directory
- Verify `vawn_config.py` is properly configured
- System will use fallback mode if APU-37 unavailable

#### 5. Critical Health Scores
**Issue:** Community health always shows "critical"

**Analysis:** This may be correct if:
- No recent community engagement
- Engagement agents not responding
- Low platform performance

**Solutions:**
- Run APU-37 engagement agents to generate data
- Check platform API connections
- Review engagement strategy effectiveness

### Debug Mode

For troubleshooting, add debug prints to the intelligence engine:

```python
# Add to main() function in engagement_monitor_apu51.py
print(f"[DEBUG] Recent comments: {len(recent_comments)}")
print(f"[DEBUG] Agent health: {agent_health}")
print(f"[DEBUG] Current metrics: {current_metrics}")
```

## Performance Considerations

### Resource Usage
- **Memory:** ~50-100MB for full analysis
- **CPU:** Moderate usage during sentiment analysis
- **Network:** Claude AI API calls for sentiment analysis
- **Storage:** ~1-5MB per day of log data

### Optimization Tips
1. **Adjust batch size** for sentiment analysis based on comment volume
2. **Modify refresh interval** on dashboard based on activity level
3. **Configure alert thresholds** to reduce noise
4. **Limit historical analysis** window if performance issues

## Future Enhancements

### Planned Features
1. **Advanced ML Models** for sentiment analysis
2. **Community Advocate Identification** system
3. **Automated Response Generation** recommendations
4. **Cross-Platform Content Optimization** suggestions
5. **Community Growth Prediction Models**
6. **Integration with Additional Platforms**

### Extensibility
The APU-51 system is designed for easy extension:
- Modular intelligence engine architecture
- Plugin-friendly dashboard system
- Configurable analysis parameters
- Extensible alert and recommendation system

## Support

For issues or questions about the APU-51 Community Intelligence Engine:

1. **Check this documentation** for configuration and troubleshooting
2. **Review log files** in `research/` directory for error details
3. **Test integration** with APU-37 systems using provided validation scripts
4. **Verify configuration** in `vawn_config.py` for API access

The APU-51 system is designed to enhance community management through intelligent analytics while maintaining compatibility with existing Vawn project infrastructure.