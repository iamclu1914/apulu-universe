# APU-51 Dashboard Quick Reference

## Starting the Dashboard

```bash
cd src
python community_dashboard_apu51.py
```

**Dashboard URL:** http://localhost:8051

## Dashboard Sections

### 1. Community Health Overview
- **Overall Health Score:** 0.000-1.000 scale with status classification
- **Component Scores:** Sentiment, Engagement, Response, Growth
- **Status Colors:** Green (excellent), Yellow (fair), Red (critical)

### 2. Sentiment Analysis
- **Sentiment Gauge:** Visual representation of community mood (-1.0 to +1.0)
- **Distribution Bars:** Positive, Neutral, Negative comment breakdown
- **Emotional Themes:** Key emotional indicators from community
- **Satisfaction Score:** Overall community satisfaction (0.0-1.0)

### 3. Cross-Platform Performance
- **Top Performer:** Best performing platform
- **Average Performance:** Overall platform effectiveness
- **Total Reach:** Estimated community reach across platforms
- **Platform Diversity:** Balance of engagement across platforms
- **Platform Chart:** Visual comparison of platform performance scores

### 4. Predictive Insights
- **Sentiment Forecast:** Predicted sentiment trend (improving/stable/declining)
- **Engagement Forecast:** Predicted engagement pattern
- **Growth Projection:** Community growth outlook
- **Forecast Confidence:** Reliability of predictions (0-100%)
- **Growth Opportunities:** Identified expansion possibilities

### 5. Intelligence Alerts
- **Alert Severity:** Critical, High, Medium, Low, Info
- **Alert Types:** Community health, sentiment drops, engagement issues
- **Recommendations:** Actionable suggestions for improvement
- **Color Coding:** Red (critical), Orange (high), Yellow (medium), Blue (low)

### 6. Historical Trends
- **7-Day Chart:** Community health, sentiment, and satisfaction trends
- **Trend Lines:** Visual tracking of key metrics over time
- **Data Points:** Daily aggregated values

### 7. Community Insights
- **Strengths:** Current community advantages and positive factors
- **Improvement Areas:** Specific areas needing attention
- **Actionable Items:** Clear next steps for community management

## Key Metrics Explained

### Community Health Score Components
| Component | Weight | Description |
|-----------|--------|-------------|
| **Sentiment** | 40% | Community mood and emotional response |
| **Engagement** | 30% | Cross-platform interaction effectiveness |
| **Response** | 20% | Agent system reliability and response quality |
| **Growth** | 10% | Community expansion and retention indicators |

### Health Status Classifications
| Status | Score Range | Meaning |
|--------|-------------|---------|
| **Excellent** | 0.85+ | Community thriving, maintain approach |
| **Good** | 0.70-0.84 | Strong performance, minor optimizations |
| **Fair** | 0.55-0.69 | Adequate performance, improvement opportunities |
| **Poor** | 0.40-0.54 | Below expectations, strategy review needed |
| **Critical** | <0.40 | Immediate attention required |

### Sentiment Scale
| Range | Classification | Community Mood |
|-------|---------------|----------------|
| **+0.30 to +1.00** | Positive | Happy, engaged, satisfied |
| **-0.30 to +0.30** | Neutral | Balanced, stable interaction |
| **-1.00 to -0.30** | Negative | Frustrated, dissatisfied, declining |

## Dashboard Features

### Auto-Refresh
- **Interval:** 30 seconds
- **Status:** Shown in footer
- **Manual Refresh:** Click refresh button in header

### Interactive Elements
- **Charts:** Hover for detailed values
- **Refresh Button:** Manual data update
- **Real-time Updates:** Automatic data polling

### Responsive Design
- **Desktop:** Full feature set with multi-column layout
- **Tablet:** Responsive grid adjustments
- **Mobile:** Stacked layout with touch-friendly interface

## Alert Action Guide

### Critical Alerts (Red)
**Immediate Action Required**
- Community health <0.40
- Severe sentiment drop
- System failures

**Actions:**
1. Review recent content strategy
2. Check agent system status
3. Increase positive engagement
4. Investigate root causes

### High Priority Alerts (Orange)
**Action Needed Soon**
- Health score declining
- Platform performance issues
- Engagement drops

**Actions:**
1. Analyze platform-specific issues
2. Review engagement timing
3. Adjust content strategy
4. Monitor trends closely

### Medium/Low Alerts (Yellow/Blue)
**Monitor and Plan**
- Minor performance variations
- Optimization opportunities
- Growth potential identified

**Actions:**
1. Track trends over time
2. Plan strategic improvements
3. Test new approaches
4. Maintain current strengths

## Troubleshooting

### Dashboard Won't Load
1. Check if server is running: `ps aux | grep community_dashboard`
2. Verify port 8051 is available: `netstat -an | grep 8051`
3. Check for error messages in terminal
4. Restart dashboard server

### No Data Showing
1. Run APU-51 engine first: `python engagement_monitor_apu51.py`
2. Check research directory for log files
3. Verify APU-37 integration is working
4. Check Claude AI API configuration

### Charts Not Loading
1. Verify internet connection (Chart.js CDN)
2. Check browser console for JavaScript errors
3. Try refreshing the page
4. Clear browser cache if needed

### Old Data Showing
1. Click manual refresh button
2. Check auto-refresh status in footer
3. Verify log file timestamps in research directory
4. Restart dashboard if needed

## Best Practices

### Daily Monitoring
1. **Check health score** - Overall community status
2. **Review alerts** - Address urgent issues first
3. **Monitor sentiment** - Track community mood changes
4. **Analyze top platform** - Focus efforts effectively

### Weekly Analysis
1. **Review trends chart** - Identify patterns over 7 days
2. **Assess growth opportunities** - Plan strategic initiatives
3. **Evaluate predictions** - Adjust based on forecasts
4. **Update strategy** - Based on insights and recommendations

### Monthly Planning
1. **Health trend analysis** - Long-term performance tracking
2. **Platform strategy review** - Optimize resource allocation
3. **Community growth planning** - Based on prediction data
4. **System optimization** - Update thresholds and configuration

## Quick Actions

### Improving Low Health Scores
- **Low Sentiment:** Increase positive engagement, review content
- **Low Engagement:** Analyze top-performing platform strategies
- **Low Response:** Check agent system status and reliability
- **Low Growth:** Implement growth opportunities from predictions

### Maximizing Dashboard Value
1. **Set bookmarks** for daily dashboard check
2. **Configure alerts** based on your community goals
3. **Track patterns** using the trends chart
4. **Act on recommendations** provided in alerts section

The APU-51 dashboard is designed to provide actionable insights for effective community management. Use it regularly to stay informed about your community's health and growth opportunities.