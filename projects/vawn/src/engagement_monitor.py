"""
engagement_monitor.py — Real-time engagement monitoring system for APU-133.
Continuous monitoring with priority scoring, sentiment analysis, and alert system.
Created by: Dex - Community Agent (APU-133)
"""

import json
import sys
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from vawn_config import (
    get_anthropic_client, load_json, save_json, CREDS_FILE,
    ENGAGEMENT_LOG, VAWN_PROFILE, log_run, today_str, RESEARCH_DIR
)

BASE_URL = "https://apulustudio.onrender.com/api"
MONITOR_LOG = RESEARCH_DIR / "engagement_monitor_log.json"
ALERTS_LOG = RESEARCH_DIR / "engagement_alerts.json"

class EngagementMonitor:
    def __init__(self):
        self.client = get_anthropic_client()
        self.last_check = datetime.now() - timedelta(hours=1)  # Start with last hour
        self.priority_keywords = {
            "high": ["fire", "incredible", "amazing", "love", "best", "favorite", "obsessed", "masterpiece"],
            "negative": ["disappointed", "not feeling", "prefer", "better", "worst", "hate", "bad"],
            "influencer": ["playlist", "curator", "blogger", "journalist", "critic", "producer"],
            "opportunity": ["collab", "feature", "work together", "booking", "show", "interview"],
            "viral": ["everyone", "all over", "trending", "viral", "sharing", "repost"]
        }

    def refresh_token(self):
        """Get fresh access token."""
        creds = load_json(CREDS_FILE)
        r = requests.post(f"{BASE_URL}/auth/refresh", json={"refresh_token": creds["refresh_token"]})
        if r.status_code != 200:
            raise RuntimeError(f"Token refresh failed: {r.status_code}")
        data = r.json()
        creds["access_token"] = data["access_token"]
        creds["refresh_token"] = data["refresh_token"]
        save_json(CREDS_FILE, creds)
        return data["access_token"]

    def analyze_comment_priority(self, comment):
        """Score comment priority based on content, author, platform, and timing."""
        text = comment.get("text", "").lower()
        platform = comment.get("platform", "")
        author = comment.get("author", "")
        timestamp = comment.get("timestamp", "")

        score = 0
        alerts = []

        # Content analysis
        for keyword in self.priority_keywords["high"]:
            if keyword in text:
                score += 2

        for keyword in self.priority_keywords["negative"]:
            if keyword in text:
                score += 3  # Negative sentiment needs immediate attention
                alerts.append(f"Negative sentiment detected: '{keyword}'")

        for keyword in self.priority_keywords["influencer"]:
            if keyword in text or keyword in author.lower():
                score += 4
                alerts.append(f"Potential influencer engagement: '{keyword}'")

        for keyword in self.priority_keywords["opportunity"]:
            if keyword in text:
                score += 3
                alerts.append(f"Business opportunity: '{keyword}'")

        for keyword in self.priority_keywords["viral"]:
            if keyword in text:
                score += 3
                alerts.append(f"Viral potential: '{keyword}'")

        # Platform weighting (X and Instagram have higher reach potential)
        platform_weight = {"x": 1.5, "instagram": 1.3, "threads": 1.2, "bluesky": 1.0, "tiktok": 1.1}
        score *= platform_weight.get(platform, 1.0)

        # Timing - recent comments get priority boost
        try:
            comment_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            age_hours = (datetime.now() - comment_time.replace(tzinfo=None)).total_seconds() / 3600
            if age_hours < 2:  # Very fresh
                score += 1
            elif age_hours < 6:  # Recent
                score += 0.5
        except:
            pass

        # Length analysis - substantial comments get more attention
        word_count = len(text.split())
        if word_count > 10:  # Thoughtful comment
            score += 1
        elif word_count < 3:  # Likely spam/low-effort
            score -= 1

        priority = "low"
        if score >= 7:
            priority = "critical"
        elif score >= 4:
            priority = "high"
        elif score >= 2:
            priority = "medium"

        return {
            "score": round(score, 1),
            "priority": priority,
            "alerts": alerts,
            "analysis": {
                "platform": platform,
                "word_count": word_count,
                "timestamp": timestamp
            }
        }

    def generate_sentiment_analysis(self, comment_text):
        """Analyze comment sentiment and emotional tone."""
        prompt = f"""Analyze this social media comment for sentiment and tone:

"{comment_text}"

Provide analysis in this JSON format:
{{
    "sentiment": "positive|negative|neutral",
    "emotion": "excited|frustrated|curious|appreciative|critical|other",
    "urgency": "low|medium|high",
    "response_needed": true|false,
    "key_themes": ["theme1", "theme2"],
    "summary": "brief summary of comment intent"
}}

Focus on whether this comment needs immediate attention or response."""

        try:
            resp = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}],
            )
            analysis_text = resp.content[0].text.strip()
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {"error": "Could not parse sentiment analysis"}
        except Exception as e:
            return {"error": f"Sentiment analysis failed: {e}"}

    def fetch_new_comments(self, access_token):
        """Fetch comments since last check by checking all posts."""
        headers = {"Authorization": f"Bearer {access_token}"}
        all_comments = []

        try:
            # First, get all recent posts
            posts_response = requests.get(f"{BASE_URL}/posts", headers=headers, timeout=30)
            if posts_response.status_code == 404:
                return {"status": "api_unavailable", "comments": []}
            posts_response.raise_for_status()

            posts_data = posts_response.json()
            posts = posts_data.get("posts", [])

            # For each post, try to get its comments
            for post in posts:
                post_id = post.get("id")
                if not post_id:
                    continue

                try:
                    comments_response = requests.get(f"{BASE_URL}/posts/{post_id}/comments", headers=headers, timeout=10)

                    # Skip if no comments endpoint or not found (expected for posts without comments)
                    if comments_response.status_code in [404, 422]:
                        continue

                    comments_response.raise_for_status()
                    post_comments = comments_response.json().get("comments", [])

                    # Add post context to each comment
                    for comment in post_comments:
                        comment["post_id"] = post_id
                        comment["post_content"] = post.get("content", "")[:100]  # First 100 chars
                        all_comments.append(comment)

                except requests.exceptions.RequestException:
                    # Skip individual post comment errors, continue with others
                    continue

            # Filter for new comments since last check
            new_comments = []
            for comment in all_comments:
                try:
                    # Try different timestamp formats
                    timestamp = comment.get("timestamp") or comment.get("created_at", "")
                    if timestamp:
                        comment_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        if comment_time.replace(tzinfo=None) > self.last_check:
                            new_comments.append(comment)
                except:
                    # If timestamp parsing fails, include it to be safe
                    new_comments.append(comment)

            return {"status": "success", "comments": new_comments}

        except requests.exceptions.RequestException as e:
            return {"status": "error", "error": str(e), "comments": []}

    def process_monitoring_cycle(self):
        """Single monitoring cycle - fetch, analyze, alert."""
        cycle_start = datetime.now()

        try:
            access_token = self.refresh_token()
        except Exception as e:
            self.log_cycle("error", f"Auth failed: {e}")
            return {"status": "auth_error", "error": str(e)}

        # Fetch new comments
        result = self.fetch_new_comments(access_token)
        if result["status"] != "success":
            self.log_cycle("warning", f"Comment fetch failed: {result.get('error', 'API unavailable')}")
            return result

        new_comments = result["comments"]
        if not new_comments:
            self.log_cycle("ok", "No new comments to monitor")
            return {"status": "no_new_comments", "processed": 0}

        # Process each new comment
        high_priority_alerts = []
        processed_comments = []

        for comment in new_comments:
            # Priority scoring
            priority_analysis = self.analyze_comment_priority(comment)

            # Sentiment analysis for high-priority comments
            sentiment_analysis = {}
            if priority_analysis["priority"] in ["high", "critical"]:
                sentiment_analysis = self.generate_sentiment_analysis(comment.get("text", ""))

            # Build processed comment record
            processed_comment = {
                "id": comment.get("id", ""),
                "text": comment.get("text", "")[:200],  # Truncate for storage
                "platform": comment.get("platform", ""),
                "author": comment.get("author", ""),
                "timestamp": comment.get("timestamp", ""),
                "priority": priority_analysis,
                "sentiment": sentiment_analysis,
                "processed_at": datetime.now().isoformat()
            }
            processed_comments.append(processed_comment)

            # Generate alerts for critical/high priority
            if priority_analysis["priority"] in ["critical", "high"]:
                alert = {
                    "id": comment.get("id", ""),
                    "priority": priority_analysis["priority"],
                    "score": priority_analysis["score"],
                    "platform": comment.get("platform", ""),
                    "author": comment.get("author", ""),
                    "text": comment.get("text", ""),
                    "alerts": priority_analysis["alerts"],
                    "sentiment": sentiment_analysis,
                    "timestamp": datetime.now().isoformat(),
                    "action_needed": True
                }
                high_priority_alerts.append(alert)

        # Update last check time
        self.last_check = cycle_start

        # Save monitoring results
        self.save_monitoring_results(processed_comments, high_priority_alerts)

        # Log cycle completion
        cycle_duration = (datetime.now() - cycle_start).total_seconds()
        status_msg = f"Processed {len(new_comments)} comments, {len(high_priority_alerts)} high-priority alerts, {cycle_duration:.1f}s"
        self.log_cycle("ok", status_msg)

        return {
            "status": "success",
            "processed": len(new_comments),
            "high_priority_alerts": len(high_priority_alerts),
            "cycle_duration": cycle_duration
        }

    def save_monitoring_results(self, processed_comments, alerts):
        """Save monitoring results to log files."""
        # Save to monitor log using date-based structure
        monitor_log = load_json(MONITOR_LOG) if MONITOR_LOG.exists() else {}
        today = today_str()

        cycle_record = {
            "timestamp": datetime.now().isoformat(),
            "processed_count": len(processed_comments),
            "alert_count": len(alerts),
            "comments": processed_comments
        }

        # Initialize today's entry if it doesn't exist
        if today not in monitor_log:
            monitor_log[today] = []

        monitor_log[today].append(cycle_record)

        # Keep last 50 cycles per day (prevent excessive growth)
        monitor_log[today] = monitor_log[today][-50:]

        save_json(MONITOR_LOG, monitor_log)

        # Save high-priority alerts
        if alerts:
            alerts_log = load_json(ALERTS_LOG) if ALERTS_LOG.exists() else {"alerts": []}
            alerts_log["alerts"].extend(alerts)
            # Keep last 200 alerts
            alerts_log["alerts"] = alerts_log["alerts"][-200:]
            alerts_log["last_updated"] = datetime.now().isoformat()
            save_json(ALERTS_LOG, alerts_log)

    def log_cycle(self, status, message):
        """Log monitoring cycle to research log."""
        log_run("EngagementMonitor", status, message)

    def get_monitoring_status(self):
        """Get current monitoring status and health metrics."""
        monitor_log = load_json(MONITOR_LOG) if MONITOR_LOG.exists() else {}
        alerts_log = load_json(ALERTS_LOG) if ALERTS_LOG.exists() else {"alerts": []}

        # Flatten all cycles from date-based structure
        all_cycles = []
        for date_key, cycles in monitor_log.items():
            if isinstance(cycles, list):  # Skip stats or other non-list entries
                all_cycles.extend(cycles)

        # Sort by timestamp to get most recent
        all_cycles.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        # Calculate health metrics
        recent_cycles = all_cycles[:10]  # Last 10 cycles
        avg_processing_time = 0
        if len(recent_cycles) > 1:
            # Estimate processing time from cycle frequency
            timestamps = [datetime.fromisoformat(c["timestamp"]) for c in recent_cycles]
            intervals = [(timestamps[i-1] - timestamps[i]).total_seconds() for i in range(1, len(timestamps))]
            avg_processing_time = sum(intervals) / len(intervals) if intervals else 0

        # Recent alert analysis
        recent_alerts = [a for a in alerts_log.get("alerts", [])
                        if datetime.fromisoformat(a["timestamp"]) > datetime.now() - timedelta(hours=24)]

        # Calculate totals
        total_processed = sum(cycle.get("processed_count", 0) for cycle in all_cycles)
        total_alerts = sum(cycle.get("alert_count", 0) for cycle in all_cycles)

        return {
            "status": "active",
            "last_check": self.last_check.isoformat(),
            "total_cycles": len(all_cycles),
            "total_processed": total_processed,
            "total_alerts": total_alerts,
            "recent_alerts_24h": len(recent_alerts),
            "avg_cycle_interval": avg_processing_time,
            "health": "healthy" if recent_cycles else "inactive"
        }


def main_monitoring_loop():
    """Main monitoring loop for continuous engagement monitoring."""
    print("\n=== Engagement Monitor (APU-133) Starting ===\n")

    monitor = EngagementMonitor()
    cycle_count = 0

    while True:
        try:
            cycle_count += 1
            print(f"\n--- Monitoring Cycle #{cycle_count} ---")

            result = monitor.process_monitoring_cycle()

            if result["status"] == "success":
                print(f"✅ Processed {result['processed']} comments")
                if result["high_priority_alerts"] > 0:
                    print(f"🚨 {result['high_priority_alerts']} high-priority alerts generated")
                print(f"⏱️  Cycle completed in {result['cycle_duration']:.1f}s")
            elif result["status"] == "no_new_comments":
                print("ℹ️  No new comments to process")
            else:
                print(f"⚠️  Cycle issue: {result['status']}")
                if "error" in result:
                    print(f"   Error: {result['error']}")

            # Wait before next cycle (2-minute intervals for real-time monitoring)
            print("⏳ Waiting 2 minutes until next cycle...")
            time.sleep(120)

        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
            break
        except Exception as e:
            print(f"❌ Monitoring error: {e}")
            monitor.log_cycle("error", f"Monitoring loop error: {e}")
            # Wait longer on errors to avoid spam
            time.sleep(300)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", action="store_true", help="Show monitoring status and exit")
    parser.add_argument("--single", action="store_true", help="Run single monitoring cycle and exit")
    args = parser.parse_args()

    monitor = EngagementMonitor()

    if args.status:
        status = monitor.get_monitoring_status()
        print(f"\n=== Engagement Monitor Status ===")
        print(f"Status: {status['status']}")
        print(f"Health: {status['health']}")
        print(f"Last Check: {status['last_check']}")
        print(f"Total Cycles: {status['total_cycles']}")
        print(f"Total Processed: {status['total_processed']}")
        print(f"Total Alerts: {status['total_alerts']}")
        print(f"Recent Alerts (24h): {status['recent_alerts_24h']}")
        if status['avg_cycle_interval'] > 0:
            print(f"Avg Cycle Interval: {status['avg_cycle_interval']:.1f}s")
    elif args.single:
        result = monitor.process_monitoring_cycle()
        print(f"Single cycle result: {result}")
    else:
        main_monitoring_loop()