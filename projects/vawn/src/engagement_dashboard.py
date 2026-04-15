"""
engagement_dashboard.py — Real-time engagement monitoring dashboard for APU-133.
Displays engagement health, alerts, trends, and actionable insights.
Created by: Dex - Community Agent (APU-133)
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from vawn_config import load_json, RESEARCH_DIR

MONITOR_LOG = RESEARCH_DIR / "engagement_monitor_log.json"
ALERTS_LOG = RESEARCH_DIR / "engagement_alerts.json"
ENGAGEMENT_LOG = RESEARCH_DIR / "engagement_log.json"

class EngagementDashboard:
    def __init__(self):
        self.monitor_data = load_json(MONITOR_LOG) if MONITOR_LOG.exists() else {"cycles": [], "stats": {}}
        self.alerts_data = load_json(ALERTS_LOG) if ALERTS_LOG.exists() else {"alerts": []}
        self.engagement_data = load_json(ENGAGEMENT_LOG) if ENGAGEMENT_LOG.exists() else {"history": []}

    def get_health_status(self):
        """Generate overall engagement health status."""
        now = datetime.now()
        recent_cycles = [c for c in self.monitor_data.get("cycles", [])
                        if datetime.fromisoformat(c["timestamp"]) > now - timedelta(hours=2)]

        recent_alerts = [a for a in self.alerts_data.get("alerts", [])
                        if datetime.fromisoformat(a["timestamp"]) > now - timedelta(hours=24)]

        critical_alerts = [a for a in recent_alerts if a.get("priority") == "critical"]

        if not recent_cycles:
            status = "⚠️ INACTIVE"
            health = "red"
        elif len(critical_alerts) > 3:
            status = "🚨 CRITICAL ALERTS"
            health = "red"
        elif len(recent_alerts) > 10:
            status = "⚡ HIGH ACTIVITY"
            health = "yellow"
        else:
            status = "✅ HEALTHY"
            health = "green"

        return {
            "status": status,
            "health": health,
            "recent_cycles": len(recent_cycles),
            "recent_alerts": len(recent_alerts),
            "critical_alerts": len(critical_alerts)
        }

    def get_platform_breakdown(self):
        """Analyze engagement by platform."""
        recent_comments = []
        for cycle in self.monitor_data.get("cycles", [])[-20:]:  # Last 20 cycles
            recent_comments.extend(cycle.get("comments", []))

        platform_stats = {}
        for comment in recent_comments:
            platform = comment.get("platform", "unknown")
            if platform not in platform_stats:
                platform_stats[platform] = {
                    "total": 0,
                    "high_priority": 0,
                    "critical": 0,
                    "avg_score": 0,
                    "scores": []
                }

            platform_stats[platform]["total"] += 1

            priority = comment.get("priority", {})
            if priority.get("priority") == "high":
                platform_stats[platform]["high_priority"] += 1
            elif priority.get("priority") == "critical":
                platform_stats[platform]["critical"] += 1

            score = priority.get("score", 0)
            if score > 0:
                platform_stats[platform]["scores"].append(score)

        # Calculate averages
        for platform, stats in platform_stats.items():
            if stats["scores"]:
                stats["avg_score"] = round(sum(stats["scores"]) / len(stats["scores"]), 1)

        return platform_stats

    def get_trending_topics(self):
        """Identify trending topics and keywords from recent engagement."""
        recent_comments = []
        for cycle in self.monitor_data.get("cycles", [])[-10:]:  # Last 10 cycles
            recent_comments.extend(cycle.get("comments", []))

        # Extract keywords from high-priority comments
        keywords = {}
        for comment in recent_comments:
            priority = comment.get("priority", {})
            if priority.get("priority") in ["high", "critical"]:
                text = comment.get("text", "").lower()
                sentiment = comment.get("sentiment", {})
                themes = sentiment.get("key_themes", []) if sentiment else []

                for theme in themes:
                    theme_key = theme.lower()
                    if theme_key not in keywords:
                        keywords[theme_key] = {
                            "count": 0,
                            "sentiment": [],
                            "platforms": set(),
                            "priority_scores": []
                        }
                    keywords[theme_key]["count"] += 1
                    keywords[theme_key]["platforms"].add(comment.get("platform", ""))
                    keywords[theme_key]["priority_scores"].append(priority.get("score", 0))

                    if sentiment:
                        keywords[theme_key]["sentiment"].append(sentiment.get("sentiment", "neutral"))

        # Process and rank trending topics
        trending = []
        for keyword, data in keywords.items():
            if data["count"] >= 2:  # Minimum threshold
                avg_score = sum(data["priority_scores"]) / len(data["priority_scores"]) if data["priority_scores"] else 0
                sentiment_summary = max(set(data["sentiment"]), key=data["sentiment"].count) if data["sentiment"] else "neutral"

                trending.append({
                    "topic": keyword,
                    "count": data["count"],
                    "avg_priority_score": round(avg_score, 1),
                    "dominant_sentiment": sentiment_summary,
                    "platforms": list(data["platforms"]),
                    "trend_score": data["count"] * avg_score
                })

        return sorted(trending, key=lambda x: x["trend_score"], reverse=True)[:10]

    def get_response_recommendations(self):
        """Generate actionable response recommendations."""
        recent_alerts = [a for a in self.alerts_data.get("alerts", [])
                        if datetime.fromisoformat(a["timestamp"]) > datetime.now() - timedelta(hours=6)]

        recommendations = []

        # Immediate action needed
        critical_unresponded = [a for a in recent_alerts
                              if a.get("priority") == "critical" and a.get("action_needed")]

        if critical_unresponded:
            recommendations.append({
                "priority": "IMMEDIATE",
                "action": f"Respond to {len(critical_unresponded)} critical comments",
                "details": [f"{a['platform']}: {a['text'][:60]}..." for a in critical_unresponded[:3]]
            })

        # Negative sentiment alerts
        negative_comments = [a for a in recent_alerts
                           if a.get("sentiment", {}).get("sentiment") == "negative"]

        if negative_comments:
            recommendations.append({
                "priority": "HIGH",
                "action": f"Address {len(negative_comments)} negative sentiment comments",
                "details": [f"{a['platform']}: {a['text'][:60]}..." for a in negative_comments[:3]]
            })

        # Opportunity alerts
        opportunity_comments = [a for a in recent_alerts
                              if "opportunity" in str(a.get("alerts", []))]

        if opportunity_comments:
            recommendations.append({
                "priority": "OPPORTUNITY",
                "action": f"Follow up on {len(opportunity_comments)} business opportunities",
                "details": [f"{a['platform']}: {a['text'][:60]}..." for a in opportunity_comments[:2]]
            })

        # Viral potential
        viral_comments = [a for a in recent_alerts
                         if "viral" in str(a.get("alerts", []))]

        if viral_comments:
            recommendations.append({
                "priority": "VIRAL",
                "action": f"Amplify {len(viral_comments)} viral potential comments",
                "details": [f"{a['platform']}: {a['text'][:60]}..." for a in viral_comments[:2]]
            })

        return recommendations

    def get_engagement_metrics(self):
        """Calculate key engagement metrics."""
        # Recent monitoring data (last 24 hours)
        recent_cycles = [c for c in self.monitor_data.get("cycles", [])
                        if datetime.fromisoformat(c["timestamp"]) > datetime.now() - timedelta(hours=24)]

        total_monitored = sum(c.get("processed_count", 0) for c in recent_cycles)
        total_alerts = sum(c.get("alert_count", 0) for c in recent_cycles)

        # Historical engagement data
        engagement_history = self.engagement_data.get("history", [])
        recent_engagement = [h for h in engagement_history
                           if datetime.fromisoformat(h["date"]) > datetime.now() - timedelta(hours=24)]

        # Response rate from existing engagement system
        reply_success_rate = 0
        if engagement_history:
            replied_count = sum(1 for h in engagement_history if h.get("reply"))
            reply_success_rate = (replied_count / len(engagement_history)) * 100 if engagement_history else 0

        return {
            "monitoring": {
                "comments_monitored_24h": total_monitored,
                "alerts_generated_24h": total_alerts,
                "alert_rate": round((total_alerts / total_monitored) * 100, 1) if total_monitored > 0 else 0,
                "monitoring_cycles_24h": len(recent_cycles)
            },
            "engagement": {
                "total_comments_processed": len(engagement_history),
                "recent_comments_24h": len(recent_engagement),
                "reply_success_rate": round(reply_success_rate, 1),
                "avg_response_time": "2-4 hours"  # Based on scheduled agent runs
            }
        }

    def display_dashboard(self):
        """Display the complete engagement dashboard."""
        print("=" * 80)
        print("🎯 VAWN ENGAGEMENT MONITOR DASHBOARD (APU-133)")
        print("=" * 80)

        # Health Status
        health = self.get_health_status()
        print(f"\n📊 SYSTEM HEALTH: {health['status']}")
        print(f"   Recent Activity: {health['recent_cycles']} monitoring cycles, {health['recent_alerts']} alerts")
        if health['critical_alerts'] > 0:
            print(f"   🚨 {health['critical_alerts']} critical alerts require attention")

        # Key Metrics
        print(f"\n📈 KEY METRICS (24H)")
        metrics = self.get_engagement_metrics()
        mon = metrics["monitoring"]
        eng = metrics["engagement"]
        print(f"   Comments Monitored: {mon['comments_monitored_24h']}")
        print(f"   Alerts Generated: {mon['alerts_generated_24h']} ({mon['alert_rate']}% alert rate)")
        print(f"   Reply Success Rate: {eng['reply_success_rate']}%")
        print(f"   Avg Response Time: {eng['avg_response_time']}")

        # Platform Breakdown
        print(f"\n🌐 PLATFORM ACTIVITY")
        platform_stats = self.get_platform_breakdown()
        for platform, stats in sorted(platform_stats.items(), key=lambda x: x[1]["total"], reverse=True):
            priority_info = f"{stats['high_priority']}H/{stats['critical']}C" if stats['high_priority'] or stats['critical'] else "0 priority"
            print(f"   {platform.upper()}: {stats['total']} comments (avg score: {stats['avg_score']}, {priority_info})")

        # Trending Topics
        print(f"\n🔥 TRENDING TOPICS")
        trending = self.get_trending_topics()
        if trending:
            for topic in trending[:5]:
                platforms_str = "/".join(topic['platforms'])
                print(f"   '{topic['topic']}': {topic['count']} mentions (score: {topic['avg_priority_score']}, {topic['dominant_sentiment']}) [{platforms_str}]")
        else:
            print("   No trending topics identified")

        # Action Items
        print(f"\n🎯 RECOMMENDED ACTIONS")
        recommendations = self.get_response_recommendations()
        if recommendations:
            for rec in recommendations:
                print(f"   [{rec['priority']}] {rec['action']}")
                for detail in rec.get('details', [])[:2]:
                    print(f"      • {detail}")
        else:
            print("   ✅ No immediate actions required")

        # Recent Alerts Summary
        recent_alerts = [a for a in self.alerts_data.get("alerts", [])
                        if datetime.fromisoformat(a["timestamp"]) > datetime.now() - timedelta(hours=6)]

        if recent_alerts:
            print(f"\n🚨 RECENT HIGH-PRIORITY ALERTS (6H)")
            for alert in recent_alerts[:5]:
                timestamp = datetime.fromisoformat(alert["timestamp"]).strftime("%H:%M")
                platform = alert.get("platform", "").upper()
                priority = alert.get("priority", "").upper()
                text = alert.get("text", "")[:50]
                print(f"   [{timestamp}] {platform} {priority}: {text}...")

        print(f"\n" + "=" * 80)
        print(f"Dashboard updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)


def main():
    """Main dashboard display function."""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", type=int, default=0, help="Auto-refresh every N seconds")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    dashboard = EngagementDashboard()

    if args.json:
        # JSON output for API/integration use
        data = {
            "health": dashboard.get_health_status(),
            "metrics": dashboard.get_engagement_metrics(),
            "platforms": dashboard.get_platform_breakdown(),
            "trending": dashboard.get_trending_topics(),
            "recommendations": dashboard.get_response_recommendations(),
            "timestamp": datetime.now().isoformat()
        }
        print(json.dumps(data, indent=2))
        return

    if args.refresh > 0:
        import time
        import os
        try:
            while True:
                os.system('cls' if os.name == 'nt' else 'clear')  # Clear screen
                dashboard = EngagementDashboard()  # Refresh data
                dashboard.display_dashboard()
                print(f"\nRefreshing in {args.refresh} seconds... (Ctrl+C to stop)")
                time.sleep(args.refresh)
        except KeyboardInterrupt:
            print("\nDashboard stopped.")
    else:
        dashboard.display_dashboard()


if __name__ == "__main__":
    main()