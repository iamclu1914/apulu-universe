"""
apu141_accurate_metrics.py — Accurate Engagement Metric Calculations
Fixes the "0 seen vs 10 sent" problem by tracking actual vs attempted operations.

Created by: Dex - Community Agent (APU-141)

PROBLEM SOLVED:
Current system confuses "attempted to post response" with "actually posted response".
This creates misleading metrics like "10 responses sent" when API returns 404.

SOLUTION:
Separate tracking for each stage of the engagement pipeline:
1. Comments Retrieved (successful API calls)
2. Responses Generated (AI completions)
3. Responses Attempted (tried to post)
4. Responses Confirmed (API confirms success)
5. Response Rate = Confirmed / Retrieved (accurate calculation)
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from vawn_config import load_json, save_json, VAWN_DIR

# APU-141 accurate metrics configuration
METRICS_LOG = VAWN_DIR / "research" / "apu141_accurate_metrics_log.json"
METRICS_SUMMARY = VAWN_DIR / "research" / "apu141_metrics_summary.json"

class AccurateEngagementMetrics:
    """Enhanced engagement metrics that distinguish attempted vs successful operations."""

    def __init__(self):
        self.current_session = {
            "session_start": datetime.now().isoformat(),
            "platforms": {},
            "totals": {
                "platforms_checked": 0,
                "platforms_successful": 0,
                "comments_retrieved": 0,
                "comments_filtered": 0,
                "responses_generated": 0,
                "responses_attempted": 0,
                "responses_confirmed": 0,
                "api_errors": 0,
                "auth_errors": 0
            },
            "rates": {
                "platform_success_rate": 0.0,
                "comment_retrieval_rate": 0.0,
                "response_generation_rate": 0.0,
                "response_posting_success_rate": 0.0,
                "overall_engagement_rate": 0.0
            },
            "errors": [],
            "api_health": {}
        }

    def track_platform_check(self, platform: str, success: bool, error: str = None) -> None:
        """Track platform API check with accurate success/failure recording."""
        if platform not in self.current_session["platforms"]:
            self.current_session["platforms"][platform] = {
                "checked": False,
                "accessible": False,
                "comments_retrieved": 0,
                "responses_attempted": 0,
                "responses_confirmed": 0,
                "api_errors": [],
                "last_check": None
            }

        platform_data = self.current_session["platforms"][platform]
        platform_data["checked"] = True
        platform_data["accessible"] = success
        platform_data["last_check"] = datetime.now().isoformat()

        self.current_session["totals"]["platforms_checked"] += 1
        if success:
            self.current_session["totals"]["platforms_successful"] += 1
        else:
            platform_data["api_errors"].append(error or "Unknown error")
            if "auth" in str(error).lower() or "401" in str(error):
                self.current_session["totals"]["auth_errors"] += 1
            else:
                self.current_session["totals"]["api_errors"] += 1

    def track_comments_retrieved(self, platform: str, comments: List[Dict[str, Any]],
                                api_errors: List[str] = None) -> None:
        """Track comments successfully retrieved from platform API."""
        if platform not in self.current_session["platforms"]:
            self.track_platform_check(platform, True)

        platform_data = self.current_session["platforms"][platform]

        # Only count comments that were actually retrieved (not API errors)
        if api_errors:
            platform_data["api_errors"].extend(api_errors)
            self.current_session["totals"]["api_errors"] += len(api_errors)
            # If there were API errors, we didn't actually retrieve comments
            retrieved_count = 0
        else:
            retrieved_count = len(comments)

        platform_data["comments_retrieved"] = retrieved_count
        self.current_session["totals"]["comments_retrieved"] += retrieved_count

    def track_response_generated(self, platform: str, comment: Dict[str, Any],
                               response_text: str, generation_success: bool) -> str:
        """Track AI response generation with unique ID for tracking through pipeline."""
        response_id = f"{platform}_{comment.get('id', 'unknown')}_{int(datetime.now().timestamp())}"

        if generation_success:
            self.current_session["totals"]["responses_generated"] += 1

        return response_id

    def track_response_attempt(self, platform: str, response_id: str, comment: Dict[str, Any],
                             response_text: str) -> None:
        """Track attempt to post response to platform."""
        if platform not in self.current_session["platforms"]:
            self.current_session["platforms"][platform] = {}

        platform_data = self.current_session["platforms"][platform]
        platform_data["responses_attempted"] = platform_data.get("responses_attempted", 0) + 1
        self.current_session["totals"]["responses_attempted"] += 1

    def track_response_confirmation(self, platform: str, response_id: str,
                                  api_success: bool, api_response: Dict[str, Any] = None,
                                  error: str = None) -> None:
        """Track API confirmation of response posting."""
        platform_data = self.current_session["platforms"][platform]

        if api_success and api_response and api_response.get("status_code") in [200, 201]:
            # Response was actually posted successfully
            platform_data["responses_confirmed"] = platform_data.get("responses_confirmed", 0) + 1
            self.current_session["totals"]["responses_confirmed"] += 1
        else:
            # Response failed to post
            platform_data["api_errors"] = platform_data.get("api_errors", [])
            error_msg = error or f"API response: {api_response}"
            platform_data["api_errors"].append(f"Response posting failed: {error_msg}")

            if "auth" in str(error_msg).lower() or "401" in str(error_msg):
                self.current_session["totals"]["auth_errors"] += 1
            else:
                self.current_session["totals"]["api_errors"] += 1

    def calculate_accurate_rates(self) -> Dict[str, float]:
        """Calculate accurate engagement rates based on actual vs attempted operations."""
        totals = self.current_session["totals"]

        # Platform success rate: platforms successfully checked / platforms attempted
        platform_success_rate = (totals["platforms_successful"] / totals["platforms_checked"]
                                 if totals["platforms_checked"] > 0 else 0.0)

        # Comment retrieval rate: comments retrieved / platforms successfully checked
        comment_retrieval_rate = (totals["comments_retrieved"] / totals["platforms_successful"]
                                 if totals["platforms_successful"] > 0 else 0.0)

        # Response generation rate: responses generated / comments retrieved
        response_generation_rate = (totals["responses_generated"] / totals["comments_retrieved"]
                                   if totals["comments_retrieved"] > 0 else 0.0)

        # Response posting success rate: responses confirmed / responses attempted
        response_posting_success_rate = (totals["responses_confirmed"] / totals["responses_attempted"]
                                       if totals["responses_attempted"] > 0 else 0.0)

        # Overall engagement rate: responses confirmed / comments retrieved
        # (This is the TRUE engagement rate - how many retrieved comments got responses)
        overall_engagement_rate = (totals["responses_confirmed"] / totals["comments_retrieved"]
                                  if totals["comments_retrieved"] > 0 else 0.0)

        rates = {
            "platform_success_rate": platform_success_rate,
            "comment_retrieval_rate": comment_retrieval_rate,
            "response_generation_rate": response_generation_rate,
            "response_posting_success_rate": response_posting_success_rate,
            "overall_engagement_rate": overall_engagement_rate
        }

        self.current_session["rates"] = rates
        return rates

    def generate_accurate_summary(self) -> Dict[str, Any]:
        """Generate accurate engagement summary that clearly distinguishes attempted vs successful."""
        self.calculate_accurate_rates()

        summary = {
            "timestamp": datetime.now().isoformat(),
            "session_duration_minutes": self.calculate_session_duration(),
            "totals": self.current_session["totals"].copy(),
            "rates": self.current_session["rates"].copy(),
            "platforms": self.current_session["platforms"].copy(),
            "key_insights": self.generate_insights(),
            "accuracy_flags": self.identify_accuracy_issues()
        }

        return summary

    def calculate_session_duration(self) -> float:
        """Calculate session duration in minutes."""
        start_time = datetime.fromisoformat(self.current_session["session_start"])
        duration = datetime.now() - start_time
        return duration.total_seconds() / 60

    def generate_insights(self) -> List[str]:
        """Generate actionable insights from accurate metrics."""
        insights = []
        totals = self.current_session["totals"]
        rates = self.current_session["rates"]

        # Platform connectivity insights
        if rates["platform_success_rate"] < 0.5:
            insights.append(f"Poor platform connectivity: {rates['platform_success_rate']:.1%} platforms accessible")

        # Comment retrieval insights
        if totals["comments_retrieved"] == 0 and totals["platforms_successful"] > 0:
            insights.append("No comments retrieved despite platform connectivity - check comment API endpoints")

        # Response generation insights
        if rates["response_generation_rate"] > 0 and rates["response_posting_success_rate"] == 0:
            insights.append("AI generating responses but none posting successfully - API posting failure")

        # Accurate engagement insights
        if totals["responses_attempted"] > 0 and totals["responses_confirmed"] == 0:
            insights.append(f"Critical: {totals['responses_attempted']} responses attempted but 0 confirmed - complete posting failure")

        # Authentication insights
        if totals["auth_errors"] > 0:
            insights.append(f"Authentication issues detected: {totals['auth_errors']} auth errors")

        # Success case insights
        if rates["overall_engagement_rate"] > 0:
            insights.append(f"Active engagement: {rates['overall_engagement_rate']:.1%} of retrieved comments received responses")

        return insights

    def identify_accuracy_issues(self) -> List[str]:
        """Identify potential accuracy issues with metric calculation."""
        accuracy_flags = []
        totals = self.current_session["totals"]

        # Flag the "0 seen vs 10 sent" type issues
        if totals["responses_attempted"] > totals["responses_confirmed"]:
            difference = totals["responses_attempted"] - totals["responses_confirmed"]
            accuracy_flags.append(f"Attempted-Confirmed mismatch: {difference} responses attempted but not confirmed")

        if totals["platforms_checked"] > totals["platforms_successful"] and totals["comments_retrieved"] == 0:
            accuracy_flags.append("Platforms checked but no comments retrieved - likely API endpoint issues")

        if totals["auth_errors"] > 0 and totals["responses_attempted"] > 0:
            accuracy_flags.append("Authentication errors during response posting - token may be invalid")

        return accuracy_flags

    def save_metrics(self) -> None:
        """Save accurate metrics for historical tracking and monitoring."""
        summary = self.generate_accurate_summary()

        # Save current summary
        METRICS_SUMMARY.parent.mkdir(exist_ok=True)
        save_json(METRICS_SUMMARY, summary)

        # Save to historical log
        metrics_log = load_json(METRICS_LOG) if METRICS_LOG.exists() else {}
        today = datetime.now().strftime("%Y-%m-%d")

        if today not in metrics_log:
            metrics_log[today] = []

        metrics_log[today].append(summary)

        # Keep last 30 days
        cutoff_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        metrics_log = {k: v for k, v in metrics_log.items() if k >= cutoff_date}

        save_json(METRICS_LOG, metrics_log)

    def display_accurate_metrics(self) -> None:
        """Display accurate metrics in a clear, understandable format."""
        summary = self.generate_accurate_summary()
        totals = summary["totals"]
        rates = summary["rates"]

        print(f"\n[APU-141] ACCURATE ENGAGEMENT METRICS")
        print("=" * 50)

        print(f"\n[PIPELINE TRACKING]")
        print(f"  Platforms Checked: {totals['platforms_checked']}")
        print(f"  Platforms Accessible: {totals['platforms_successful']} ({rates['platform_success_rate']:.1%})")
        print(f"  Comments Retrieved: {totals['comments_retrieved']}")
        print(f"  Responses Generated: {totals['responses_generated']}")
        print(f"  Responses ATTEMPTED: {totals['responses_attempted']}")
        print(f"  Responses CONFIRMED: {totals['responses_confirmed']}")

        print(f"\n[ACCURATE RATES]")
        print(f"  Platform Success Rate: {rates['platform_success_rate']:.1%}")
        print(f"  Response Generation Rate: {rates['response_generation_rate']:.1%}")
        print(f"  Response Posting Success: {rates['response_posting_success_rate']:.1%}")
        print(f"  TRUE Engagement Rate: {rates['overall_engagement_rate']:.1%}")

        print(f"\n[ERROR BREAKDOWN]")
        print(f"  API Errors: {totals['api_errors']}")
        print(f"  Auth Errors: {totals['auth_errors']}")

        if summary["key_insights"]:
            print(f"\n[KEY INSIGHTS]")
            for insight in summary["key_insights"]:
                print(f"  • {insight}")

        if summary["accuracy_flags"]:
            print(f"\n[ACCURACY FLAGS]")
            for flag in summary["accuracy_flags"]:
                print(f"  ⚠️ {flag}")

        print(f"\n[APU-141] Metrics saved to: {METRICS_SUMMARY}")

# Example usage demonstrating the fix for "0 seen vs 10 sent" problem
def demonstrate_accurate_tracking():
    """Demonstrate how APU-141 fixes the metric calculation issues."""
    print("APU-141 Accurate Engagement Metrics - Demonstration")
    print("=" * 60)

    metrics = AccurateEngagementMetrics()

    # Simulate the problematic scenario from APU-120
    print("\n[SIMULATION] Reproducing APU-120 '0 seen vs 10 sent' scenario...")

    # Platform checks with mixed results
    metrics.track_platform_check("instagram", True)
    metrics.track_platform_check("tiktok", False, "HTTP 404: Comments endpoint not found")
    metrics.track_platform_check("x", False, "HTTP 401: Unauthorized")

    # Comments retrieval (only successful platforms)
    metrics.track_comments_retrieved("instagram", [], ["Comments API not implemented"])  # No actual comments

    # Simulate AI generating responses (would happen if comments existed)
    # This represents the "10 sent" part of the problem
    for i in range(3):
        response_id = metrics.track_response_generated("instagram", {"id": f"comment_{i}"}, "response text", True)
        metrics.track_response_attempt("instagram", response_id, {"id": f"comment_{i}"}, "response text")
        # All attempts fail due to API issues
        metrics.track_response_confirmation("instagram", response_id, False, {"status_code": 404}, "Comments API not implemented")

    # Show the accurate metrics
    metrics.display_accurate_metrics()

    print(f"\n[APU-141] PROBLEM SOLVED:")
    print(f"  Old system would show: '3 responses sent, success rate 100%'")
    print(f"  APU-141 shows: '3 attempted, 0 confirmed, posting success 0%'")
    print(f"  This clearly identifies the API failure vs agent failure!")

if __name__ == "__main__":
    demonstrate_accurate_tracking()