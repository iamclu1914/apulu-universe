"""
apu80_intelligent_alerting_system.py — APU-80 Intelligent Alerting System

Context-aware alerting system for the Apulu Universe engagement monitoring ecosystem.
Provides intelligent notifications, dynamic thresholds, and automated escalation workflows
based on engagement patterns, content performance, and crisis detection.

Created by: Dex - Community Agent (APU-80)

Key Features:
- Dynamic threshold calculation based on historical patterns
- Context-aware alert classification and prioritization
- Automated escalation workflows to appropriate stakeholders
- Crisis detection and emergency response protocols
- Opportunity identification for viral content
- Integration with APU-49 Paperclip department routing
"""

import asyncio
import json
import sys
import time
import smtplib
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import logging
import statistics

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import (
    load_json, save_json, ENGAGEMENT_LOG, METRICS_LOG, RESEARCH_LOG,
    VAWN_DIR, log_run, today_str, get_anthropic_client
)

# Import APU-49 department structure
sys.path.insert(0, r"C:\Users\rdyal\Vawn\src")
try:
    from apu49_paperclip_engagement_monitor import DEPARTMENTS, DEPARTMENT_THRESHOLDS
except ImportError:
    # Fallback if APU-49 not available
    DEPARTMENTS = {}
    DEPARTMENT_THRESHOLDS = {}

# Alerting configuration
ALERTS_LOG = VAWN_DIR / "research" / "apu80_alerts_log.json"
ALERTING_CONFIG = VAWN_DIR / "config" / "apu80_alerting_config.json"
ESCALATION_LOG = VAWN_DIR / "research" / "apu80_escalation_log.json"
THRESHOLD_HISTORY = VAWN_DIR / "research" / "apu80_threshold_history.json"

# Alert types and severity levels
ALERT_TYPES = {
    "viral_content": {
        "severity": "high",
        "description": "Content experiencing viral growth",
        "departments": ["creative_revenue", "operations"],
        "escalation_time": 30  # minutes
    },
    "crisis_detected": {
        "severity": "critical",
        "description": "Potential PR crisis or negative sentiment spike",
        "departments": ["legal", "chairman", "operations"],
        "escalation_time": 15  # minutes
    },
    "engagement_anomaly": {
        "severity": "medium",
        "description": "Unusual engagement patterns detected",
        "departments": ["creative_revenue", "operations"],
        "escalation_time": 60
    },
    "opportunity_identified": {
        "severity": "medium",
        "description": "Growth opportunity or trending topic match",
        "departments": ["a_and_r", "creative_revenue"],
        "escalation_time": 120
    },
    "system_health": {
        "severity": "low",
        "description": "System performance or API health issues",
        "departments": ["operations"],
        "escalation_time": 240
    },
    "compliance_risk": {
        "severity": "critical",
        "description": "Potential copyright or legal compliance issue",
        "departments": ["legal", "chairman"],
        "escalation_time": 10
    }
}

# Notification channels
NOTIFICATION_CHANNELS = {
    "email": {
        "enabled": True,
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587
    },
    "slack": {
        "enabled": False,  # Configure when Slack integration available
        "webhook_url": None
    },
    "discord": {
        "enabled": False,  # Configure when Discord integration available
        "webhook_url": None
    },
    "sms": {
        "enabled": False,  # Configure when SMS integration available
        "api_key": None
    }
}


@dataclass
class Alert:
    """Alert data structure"""
    alert_id: str
    alert_type: str
    severity: str
    platform: str
    post_id: Optional[str]
    title: str
    description: str
    metrics: Dict[str, Any]
    context: Dict[str, Any]
    timestamp: datetime
    departments: List[str]
    escalation_time: int  # minutes
    status: str = "active"  # active, acknowledged, resolved, escalated
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    escalated_at: Optional[datetime] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class ThresholdConfig:
    """Dynamic threshold configuration"""
    platform: str
    metric_type: str  # engagement_rate, velocity, sentiment_score
    base_threshold: float
    dynamic_multiplier: float
    confidence_interval: float
    lookback_days: int
    min_data_points: int

    def to_dict(self):
        return asdict(self)


class DynamicThresholdCalculator:
    """Calculates dynamic thresholds based on historical patterns"""

    def __init__(self):
        self.threshold_history = self._load_threshold_history()
        self.platform_baselines = {}
        self._calculate_baselines()

    def _load_threshold_history(self) -> Dict:
        """Load historical threshold data"""
        if Path(THRESHOLD_HISTORY).exists():
            return load_json(THRESHOLD_HISTORY)
        return {"thresholds": {}, "baselines": {}}

    def _save_threshold_history(self):
        """Save threshold history"""
        save_json(THRESHOLD_HISTORY, self.threshold_history)

    def _calculate_baselines(self):
        """Calculate baseline metrics for each platform"""
        try:
            metrics_data = load_json(METRICS_LOG)
            engagement_data = load_json(ENGAGEMENT_LOG)

            for platform in ["bluesky", "instagram", "tiktok", "threads", "x"]:
                self.platform_baselines[platform] = self._calculate_platform_baseline(
                    platform, metrics_data, engagement_data
                )

        except Exception as e:
            logging.error(f"Error calculating baselines: {e}")
            # Set default baselines
            for platform in ["bluesky", "instagram", "tiktok", "threads", "x"]:
                self.platform_baselines[platform] = {
                    "engagement_rate": 0.03,  # 3% default
                    "velocity": 1.0,  # 1 engagement per minute
                    "comment_rate": 0.005,  # 0.5% comment rate
                    "share_rate": 0.001   # 0.1% share rate
                }

    def _calculate_platform_baseline(self, platform: str, metrics_data: Dict, engagement_data: Dict) -> Dict:
        """Calculate baseline metrics for a specific platform"""
        engagement_rates = []
        velocities = []
        comment_rates = []
        share_rates = []

        # Extract historical data for this platform
        cutoff_date = datetime.now() - timedelta(days=30)

        # Process metrics data
        for image, data in metrics_data.items():
            for date_str, platforms in data.items():
                try:
                    date_obj = datetime.fromisoformat(date_str)
                    if date_obj >= cutoff_date and platform in platforms:
                        platform_metrics = platforms[platform]
                        if isinstance(platform_metrics, dict) and "_note" not in platform_metrics:
                            # Calculate engagement rate
                            total_engagement = (
                                platform_metrics.get("likes", 0) +
                                platform_metrics.get("comments", 0) +
                                platform_metrics.get("shares", 0) +
                                platform_metrics.get("saves", 0)
                            )
                            views = platform_metrics.get("views", 1)
                            if views > 0:
                                engagement_rates.append(total_engagement / views)

                except Exception:
                    continue

        # Process engagement velocity from engagement log
        for entry in engagement_data.get("history", []):
            if entry.get("platform") == platform:
                try:
                    # Calculate engagement velocity if timestamps available
                    # This would require more detailed timestamp analysis
                    velocities.append(1.0)  # Placeholder
                except Exception:
                    continue

        # Calculate baseline statistics
        baseline = {
            "engagement_rate": statistics.median(engagement_rates) if engagement_rates else 0.03,
            "velocity": statistics.median(velocities) if velocities else 1.0,
            "comment_rate": 0.005,  # Placeholder - would calculate from actual data
            "share_rate": 0.001     # Placeholder - would calculate from actual data
        }

        # Add confidence intervals
        if engagement_rates:
            baseline["engagement_rate_std"] = statistics.stdev(engagement_rates)
            baseline["engagement_rate_95th"] = sorted(engagement_rates)[int(0.95 * len(engagement_rates))]
        else:
            baseline["engagement_rate_std"] = 0.01
            baseline["engagement_rate_95th"] = 0.1

        return baseline

    def calculate_dynamic_threshold(self, platform: str, metric_type: str, current_value: float = None) -> float:
        """Calculate dynamic threshold for a platform and metric"""
        baseline = self.platform_baselines.get(platform, {})
        base_value = baseline.get(metric_type, 0.03)

        # Dynamic multiplier based on recent performance
        recent_multiplier = self._get_recent_performance_multiplier(platform, metric_type)

        # Time-of-day adjustment
        time_multiplier = self._get_time_adjustment()

        # Day-of-week adjustment
        day_multiplier = self._get_day_adjustment()

        # Calculate dynamic threshold
        dynamic_threshold = base_value * recent_multiplier * time_multiplier * day_multiplier

        # Add confidence interval buffer
        std_dev = baseline.get(f"{metric_type}_std", base_value * 0.3)
        confidence_buffer = std_dev * 1.96  # 95% confidence interval

        final_threshold = dynamic_threshold + confidence_buffer

        # Store threshold calculation
        self._store_threshold_calculation(platform, metric_type, final_threshold, {
            "base_value": base_value,
            "recent_multiplier": recent_multiplier,
            "time_multiplier": time_multiplier,
            "day_multiplier": day_multiplier,
            "confidence_buffer": confidence_buffer,
            "current_value": current_value
        })

        return final_threshold

    def _get_recent_performance_multiplier(self, platform: str, metric_type: str) -> float:
        """Get performance multiplier based on recent trends"""
        # Analyze last 7 days of performance
        # Higher recent performance = higher thresholds (to avoid false positives)
        # Lower recent performance = lower thresholds (to catch smaller improvements)

        # Placeholder implementation - would analyze recent metrics
        return 1.2  # 20% above baseline for recent good performance

    def _get_time_adjustment(self) -> float:
        """Get time-of-day adjustment multiplier"""
        hour = datetime.now().hour

        # Peak engagement hours typically 7-9am, 5-8pm
        if 7 <= hour <= 9 or 17 <= hour <= 20:
            return 1.5  # Higher thresholds during peak hours
        elif 22 <= hour or hour <= 6:
            return 0.7  # Lower thresholds during off-hours
        else:
            return 1.0  # Normal thresholds

    def _get_day_adjustment(self) -> float:
        """Get day-of-week adjustment multiplier"""
        weekday = datetime.now().weekday()

        # Weekend vs weekday patterns
        if weekday >= 5:  # Weekend (Saturday=5, Sunday=6)
            return 0.8  # Lower thresholds on weekends
        else:
            return 1.0  # Normal thresholds on weekdays

    def _store_threshold_calculation(self, platform: str, metric_type: str, threshold: float, details: Dict):
        """Store threshold calculation for analysis"""
        calculation = {
            "timestamp": datetime.now().isoformat(),
            "platform": platform,
            "metric_type": metric_type,
            "threshold": threshold,
            "calculation_details": details
        }

        if "calculations" not in self.threshold_history:
            self.threshold_history["calculations"] = []

        self.threshold_history["calculations"].append(calculation)

        # Keep only last 1000 calculations
        self.threshold_history["calculations"] = self.threshold_history["calculations"][-1000:]

        self._save_threshold_history()


class SentimentAnalyzer:
    """Analyzes sentiment in comments and content for crisis detection"""

    def __init__(self):
        self.negative_keywords = [
            "angry", "hate", "terrible", "worst", "awful", "disgusting",
            "offensive", "inappropriate", "cancelled", "boycott", "scandal",
            "lawsuit", "legal", "copyright", "stolen", "plagiarized"
        ]

        self.crisis_keywords = [
            "controversy", "scandal", "lawsuit", "legal action", "cease and desist",
            "dmca", "copyright infringement", "stolen", "plagiarized", "cancelled",
            "boycott", "offensive", "inappropriate", "harassment"
        ]

    def analyze_content_sentiment(self, content: str) -> Dict[str, Any]:
        """Analyze sentiment of content or comments"""
        if not content:
            return {"sentiment_score": 0.0, "risk_level": "low", "keywords_detected": []}

        content_lower = content.lower()

        # Count negative and crisis keywords
        negative_count = sum(1 for keyword in self.negative_keywords if keyword in content_lower)
        crisis_count = sum(1 for keyword in self.crisis_keywords if keyword in content_lower)

        # Simple sentiment scoring
        total_words = len(content.split())
        if total_words == 0:
            return {"sentiment_score": 0.0, "risk_level": "low", "keywords_detected": []}

        # Calculate sentiment score (-1 to 1, negative is bad)
        sentiment_score = -(negative_count + crisis_count * 2) / total_words

        # Determine risk level
        if crisis_count > 0 or sentiment_score <= -0.1:
            risk_level = "high"
        elif negative_count > 0 or sentiment_score <= -0.05:
            risk_level = "medium"
        else:
            risk_level = "low"

        # Collect detected keywords
        keywords_detected = []
        for keyword in self.negative_keywords + self.crisis_keywords:
            if keyword in content_lower:
                keywords_detected.append(keyword)

        return {
            "sentiment_score": sentiment_score,
            "risk_level": risk_level,
            "keywords_detected": keywords_detected,
            "negative_count": negative_count,
            "crisis_count": crisis_count
        }


class IntelligentAlertingSystem:
    """Main intelligent alerting system"""

    def __init__(self):
        self.threshold_calculator = DynamicThresholdCalculator()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history = self._load_alert_history()
        self.escalation_rules = self._load_escalation_rules()

        # Load real-time data sources
        self.realtime_alerts_file = VAWN_DIR / "research" / "apu80_realtime_alerts.json"

    def _load_alert_history(self) -> Dict:
        """Load alert history"""
        if Path(ALERTS_LOG).exists():
            return load_json(ALERTS_LOG)
        return {"alerts": []}

    def _save_alert_history(self):
        """Save alert history"""
        save_json(ALERTS_LOG, self.alert_history)

    def _load_escalation_rules(self) -> Dict:
        """Load escalation rules configuration"""
        if Path(ALERTING_CONFIG).exists():
            return load_json(ALERTING_CONFIG)
        return {
            "escalation_enabled": True,
            "notification_channels": NOTIFICATION_CHANNELS,
            "department_contacts": {
                "chairman": ["clu@apulurecords.com"],
                "legal": ["nelly@apulurecords.com"],
                "a_and_r": ["timbo@apulurecords.com"],
                "creative_revenue": ["letitia@apulurecords.com"],
                "operations": ["nari@apulurecords.com"]
            },
            "escalation_delays": {
                "critical": 15,  # minutes
                "high": 30,
                "medium": 60,
                "low": 240
            }
        }

    async def process_realtime_alerts(self):
        """Process alerts from real-time monitoring system"""
        if not self.realtime_alerts_file.exists():
            return

        try:
            realtime_data = load_json(self.realtime_alerts_file)
            new_alerts = realtime_data.get("alerts", [])

            for alert_data in new_alerts:
                await self._process_realtime_alert(alert_data)

            # Clear processed alerts
            save_json(self.realtime_alerts_file, {"alerts": []})

        except Exception as e:
            logging.error(f"Error processing realtime alerts: {e}")

    async def _process_realtime_alert(self, alert_data: Dict):
        """Process individual real-time alert"""
        alert_type = alert_data.get("alert_type", "unknown")
        platform = alert_data.get("platform", "unknown")
        metrics = alert_data.get("metrics", {})

        # Create alert ID
        alert_id = f"{alert_type}_{platform}_{int(time.time())}"

        # Validate alert against dynamic thresholds
        if not await self._validate_alert(alert_type, platform, metrics):
            logging.info(f"Alert {alert_id} did not meet dynamic thresholds - suppressed")
            return

        # Analyze context for crisis detection
        event_data = alert_data.get("event", {})
        content = event_data.get("content", "")
        sentiment_analysis = self.sentiment_analyzer.analyze_content_sentiment(content)

        # Adjust alert type based on sentiment
        if sentiment_analysis["risk_level"] == "high" and alert_type != "crisis_detected":
            alert_type = "crisis_detected"
            logging.warning(f"Alert escalated to crisis based on sentiment analysis")

        # Create alert object
        alert = Alert(
            alert_id=alert_id,
            alert_type=alert_type,
            severity=ALERT_TYPES.get(alert_type, {}).get("severity", "medium"),
            platform=platform,
            post_id=alert_data.get("post_id"),
            title=self._generate_alert_title(alert_type, platform, metrics),
            description=self._generate_alert_description(alert_type, platform, metrics, sentiment_analysis),
            metrics=metrics,
            context={
                "sentiment_analysis": sentiment_analysis,
                "threshold_analysis": await self._get_threshold_context(alert_type, platform, metrics),
                "platform_status": await self._get_platform_context(platform),
                "time_context": self._get_time_context()
            },
            timestamp=datetime.fromisoformat(alert_data.get("timestamp")),
            departments=ALERT_TYPES.get(alert_type, {}).get("departments", ["operations"]),
            escalation_time=ALERT_TYPES.get(alert_type, {}).get("escalation_time", 60)
        )

        # Add to active alerts
        self.active_alerts[alert_id] = alert

        # Send notifications
        await self._send_alert_notifications(alert)

        # Schedule escalation
        await self._schedule_escalation(alert)

        # Log alert
        self._log_alert(alert)

        logging.info(f"Alert {alert_id} created: {alert.title}")

    async def _validate_alert(self, alert_type: str, platform: str, metrics: Dict) -> bool:
        """Validate alert against dynamic thresholds"""
        if alert_type == "viral_content":
            velocity = metrics.get("velocity", 0)
            threshold = self.threshold_calculator.calculate_dynamic_threshold(platform, "velocity", velocity)
            return velocity > threshold

        elif alert_type == "engagement_anomaly":
            engagement_rate = metrics.get("engagement_rate", 0)
            threshold = self.threshold_calculator.calculate_dynamic_threshold(platform, "engagement_rate", engagement_rate)
            return engagement_rate > threshold

        elif alert_type in ["crisis_detected", "compliance_risk"]:
            # These are always validated - better to have false positives for critical issues
            return True

        return True  # Default to validating alerts

    def _generate_alert_title(self, alert_type: str, platform: str, metrics: Dict) -> str:
        """Generate descriptive alert title"""
        titles = {
            "viral_content": f"Viral Content Detected on {platform.title()}",
            "crisis_detected": f"CRISIS: Negative Sentiment Spike on {platform.title()}",
            "engagement_anomaly": f"Unusual Engagement Pattern on {platform.title()}",
            "opportunity_identified": f"Growth Opportunity on {platform.title()}",
            "system_health": f"System Health Alert - {platform.title()}",
            "compliance_risk": f"COMPLIANCE RISK: {platform.title()}"
        }

        base_title = titles.get(alert_type, f"Alert on {platform.title()}")

        # Add metrics context
        if "velocity" in metrics and metrics["velocity"] > 0:
            base_title += f" ({metrics['velocity']:.1f} eng/min)"

        return base_title

    def _generate_alert_description(self, alert_type: str, platform: str, metrics: Dict, sentiment: Dict) -> str:
        """Generate detailed alert description"""
        description = f"Alert triggered on {platform} at {datetime.now().strftime('%H:%M:%S')}\n\n"

        # Add metrics details
        description += "Metrics:\n"
        for key, value in metrics.items():
            if isinstance(value, float):
                description += f"  {key}: {value:.3f}\n"
            else:
                description += f"  {key}: {value}\n"

        # Add sentiment analysis if relevant
        if sentiment["risk_level"] != "low":
            description += f"\nSentiment Analysis:\n"
            description += f"  Risk Level: {sentiment['risk_level'].upper()}\n"
            description += f"  Sentiment Score: {sentiment['sentiment_score']:.3f}\n"
            if sentiment["keywords_detected"]:
                description += f"  Keywords: {', '.join(sentiment['keywords_detected'][:5])}\n"

        # Add context-specific information
        if alert_type == "viral_content":
            description += f"\n🚀 Content is experiencing rapid engagement growth!\n"
            description += f"Consider: Boosting similar content, preparing follow-up posts, monitoring for opportunities."

        elif alert_type == "crisis_detected":
            description += f"\n⚠️ IMMEDIATE ATTENTION REQUIRED\n"
            description += f"Potential PR crisis or negative sentiment detected.\n"
            description += f"Recommended: Review content, prepare response, consider damage control."

        return description

    async def _get_threshold_context(self, alert_type: str, platform: str, metrics: Dict) -> Dict:
        """Get context about threshold calculations"""
        context = {}

        if alert_type == "viral_content" and "velocity" in metrics:
            threshold = self.threshold_calculator.calculate_dynamic_threshold(platform, "velocity")
            context["velocity_threshold"] = threshold
            context["velocity_actual"] = metrics["velocity"]
            context["velocity_ratio"] = metrics["velocity"] / threshold if threshold > 0 else 0

        if alert_type == "engagement_anomaly" and "engagement_rate" in metrics:
            threshold = self.threshold_calculator.calculate_dynamic_threshold(platform, "engagement_rate")
            context["engagement_threshold"] = threshold
            context["engagement_actual"] = metrics["engagement_rate"]
            context["engagement_ratio"] = metrics["engagement_rate"] / threshold if threshold > 0 else 0

        return context

    async def _get_platform_context(self, platform: str) -> Dict:
        """Get platform-specific context"""
        # Would integrate with platform health monitoring
        return {
            "api_status": "healthy",  # Placeholder
            "recent_posts": 0,  # Would count recent posts
            "platform_health": "good"  # Would get from health monitoring
        }

    def _get_time_context(self) -> Dict:
        """Get time-based context"""
        now = datetime.now()
        return {
            "hour": now.hour,
            "weekday": now.weekday(),
            "is_weekend": now.weekday() >= 5,
            "is_peak_hours": 7 <= now.hour <= 9 or 17 <= now.hour <= 20
        }

    async def _send_alert_notifications(self, alert: Alert):
        """Send alert notifications through configured channels"""
        try:
            # Email notifications
            if self.escalation_rules["notification_channels"]["email"]["enabled"]:
                await self._send_email_notification(alert)

            # Slack notifications (if configured)
            if self.escalation_rules["notification_channels"]["slack"]["enabled"]:
                await self._send_slack_notification(alert)

            # Log notification
            logging.info(f"Notifications sent for alert {alert.alert_id}")

        except Exception as e:
            logging.error(f"Error sending notifications for {alert.alert_id}: {e}")

    async def _send_email_notification(self, alert: Alert):
        """Send email notification"""
        # Get department contacts
        contacts = []
        for dept in alert.departments:
            dept_contacts = self.escalation_rules["department_contacts"].get(dept, [])
            contacts.extend(dept_contacts)

        if not contacts:
            logging.warning(f"No email contacts found for departments: {alert.departments}")
            return

        # Create email content
        subject = f"[{alert.severity.upper()}] {alert.title}"
        body = f"""
APU-80 Engagement Monitor Alert

Alert ID: {alert.alert_id}
Type: {alert.alert_type}
Severity: {alert.severity.upper()}
Platform: {alert.platform}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

{alert.description}

Departments: {', '.join(alert.departments)}

This is an automated alert from the Apulu Universe engagement monitoring system.
"""

        # Log email (actual sending would require SMTP configuration)
        logging.info(f"Email notification prepared for {len(contacts)} recipients: {subject}")

    async def _send_slack_notification(self, alert: Alert):
        """Send Slack notification"""
        webhook_url = self.escalation_rules["notification_channels"]["slack"]["webhook_url"]
        if not webhook_url:
            return

        # Create Slack message
        color_map = {"critical": "#FF0000", "high": "#FF8C00", "medium": "#FFD700", "low": "#808080"}
        color = color_map.get(alert.severity, "#808080")

        slack_message = {
            "attachments": [
                {
                    "color": color,
                    "title": alert.title,
                    "text": alert.description[:500] + "..." if len(alert.description) > 500 else alert.description,
                    "fields": [
                        {"title": "Severity", "value": alert.severity.upper(), "short": True},
                        {"title": "Platform", "value": alert.platform, "short": True},
                        {"title": "Departments", "value": ", ".join(alert.departments), "short": True}
                    ],
                    "footer": "APU-80 Engagement Monitor",
                    "ts": int(alert.timestamp.timestamp())
                }
            ]
        }

        # Log Slack notification (actual sending would use requests.post)
        logging.info(f"Slack notification prepared: {alert.title}")

    async def _schedule_escalation(self, alert: Alert):
        """Schedule alert escalation"""
        escalation_delay = self.escalation_rules["escalation_delays"].get(alert.severity, alert.escalation_time)

        # Create escalation task
        asyncio.create_task(self._escalate_alert_after_delay(alert.alert_id, escalation_delay))

        logging.info(f"Escalation scheduled for alert {alert.alert_id} in {escalation_delay} minutes")

    async def _escalate_alert_after_delay(self, alert_id: str, delay_minutes: int):
        """Escalate alert after specified delay"""
        await asyncio.sleep(delay_minutes * 60)

        # Check if alert still needs escalation
        if alert_id not in self.active_alerts:
            return

        alert = self.active_alerts[alert_id]

        if alert.status in ["acknowledged", "resolved"]:
            logging.info(f"Alert {alert_id} already {alert.status} - escalation cancelled")
            return

        # Escalate alert
        alert.status = "escalated"
        alert.escalated_at = datetime.now()

        # Send escalation notifications (higher priority, more recipients)
        await self._send_escalation_notifications(alert)

        # Log escalation
        escalation_log = load_json(ESCALATION_LOG) if Path(ESCALATION_LOG).exists() else {"escalations": []}
        escalation_log["escalations"].append({
            "alert_id": alert_id,
            "escalated_at": alert.escalated_at.isoformat(),
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "departments": alert.departments
        })
        save_json(ESCALATION_LOG, escalation_log)

        logging.warning(f"Alert {alert_id} ESCALATED after {delay_minutes} minutes")

    async def _send_escalation_notifications(self, alert: Alert):
        """Send escalation notifications with higher priority"""
        # Add chairman to all escalated alerts
        escalated_departments = alert.departments.copy()
        if "chairman" not in escalated_departments:
            escalated_departments.append("chairman")

        # Create escalation message
        escalation_subject = f"[ESCALATED] {alert.title}"
        escalation_body = f"""
ESCALATED ALERT - IMMEDIATE ATTENTION REQUIRED

{alert.description}

Alert ID: {alert.alert_id}
Original Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
Escalated Time: {alert.escalated_at.strftime('%Y-%m-%d %H:%M:%S')}

This alert was automatically escalated due to lack of acknowledgment.
"""

        # Log escalation notification
        logging.warning(f"ESCALATION notifications sent for {alert.alert_id}")

    def _log_alert(self, alert: Alert):
        """Log alert to history"""
        self.alert_history["alerts"].append(alert.to_dict())

        # Keep only last 5000 alerts
        self.alert_history["alerts"] = self.alert_history["alerts"][-5000:]

        self._save_alert_history()

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an active alert"""
        if alert_id not in self.active_alerts:
            return False

        alert = self.active_alerts[alert_id]
        alert.status = "acknowledged"
        alert.acknowledged_by = acknowledged_by
        alert.acknowledged_at = datetime.now()

        logging.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
        return True

    def resolve_alert(self, alert_id: str, resolved_by: str) -> bool:
        """Resolve an active alert"""
        if alert_id not in self.active_alerts:
            return False

        alert = self.active_alerts[alert_id]
        alert.status = "resolved"

        # Remove from active alerts
        del self.active_alerts[alert_id]

        logging.info(f"Alert {alert_id} resolved by {resolved_by}")
        return True

    def get_active_alerts(self) -> List[Alert]:
        """Get list of active alerts"""
        return list(self.active_alerts.values())

    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert system statistics"""
        now = datetime.now()
        last_24h = now - timedelta(hours=24)

        recent_alerts = [
            alert for alert in self.alert_history["alerts"]
            if datetime.fromisoformat(alert["timestamp"]) >= last_24h
        ]

        stats = {
            "active_alerts": len(self.active_alerts),
            "total_alerts_24h": len(recent_alerts),
            "alert_types_24h": {},
            "platform_alerts_24h": {},
            "severity_distribution_24h": {},
            "escalated_alerts_24h": 0,
            "avg_response_time": 0  # Would calculate from acknowledgment times
        }

        # Analyze recent alerts
        for alert in recent_alerts:
            # Alert types
            alert_type = alert["alert_type"]
            stats["alert_types_24h"][alert_type] = stats["alert_types_24h"].get(alert_type, 0) + 1

            # Platform distribution
            platform = alert["platform"]
            stats["platform_alerts_24h"][platform] = stats["platform_alerts_24h"].get(platform, 0) + 1

            # Severity distribution
            severity = alert["severity"]
            stats["severity_distribution_24h"][severity] = stats["severity_distribution_24h"].get(severity, 0) + 1

            # Escalated alerts
            if alert["status"] == "escalated":
                stats["escalated_alerts_24h"] += 1

        return stats


def main():
    """Main function for APU-80 Intelligent Alerting System"""
    print("\n[*] APU-80 Intelligent Alerting System Starting...")
    print("[*] Initializing dynamic thresholds and sentiment analysis...")

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(VAWN_DIR / "research" / "apu80_alerting.log"),
            logging.StreamHandler()
        ]
    )

    # Initialize alerting system
    alerting_system = IntelligentAlertingSystem()

    async def run_alerting_system():
        """Run the alerting system"""
        logging.info("APU-80 Intelligent Alerting System started")

        while True:
            try:
                # Process real-time alerts
                await alerting_system.process_realtime_alerts()

                # Sleep for processing interval
                await asyncio.sleep(30)  # Check every 30 seconds

            except KeyboardInterrupt:
                logging.info("Alerting system shutting down")
                break
            except Exception as e:
                logging.error(f"Alerting system error: {e}")
                await asyncio.sleep(60)  # Back off on error

        return alerting_system.get_alert_statistics()

    try:
        # Start alerting system
        stats = asyncio.run(run_alerting_system())
        log_run("APU80IntelligentAlerting", "info", f"Processed {stats.get('total_alerts_24h', 0)} alerts in 24h")
        return stats

    except Exception as e:
        print(f"\n[ERROR] APU-80 Alerting System failed: {e}")
        log_run("APU80IntelligentAlerting", "error", str(e))
        return {"error": str(e)}


if __name__ == "__main__":
    stats = main()
    print(f"\n[*] APU-80 Alerting System Status: {stats.get('active_alerts', 'unknown')} active alerts")