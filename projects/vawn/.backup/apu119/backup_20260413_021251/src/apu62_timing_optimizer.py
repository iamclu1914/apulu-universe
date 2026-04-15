"""
apu62_timing_optimizer.py — Adaptive Engagement Timing Optimization
Part of APU-62 by Dex - Community Agent for intelligent engagement scheduling.

Features:
- Learns from historical engagement effectiveness data
- Adapts timing recommendations based on audience behavior patterns
- Optimizes scheduling for different departments and content types
- Provides intelligent recommendations for the 3-slot schedule
- Tracks cross-platform timing correlations and effectiveness

Machine Learning Approach:
- Time-series analysis of engagement effectiveness
- Department-specific timing pattern recognition
- Platform-specific audience behavior analysis
- Adaptive threshold adjustment based on performance feedback
"""

import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
import statistics
from collections import defaultdict

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import VAWN_DIR, load_json, save_json, log_run, today_str

# Configuration
TIMING_ANALYTICS_LOG = VAWN_DIR / "research" / "apu62_timing_analytics.json"
OPTIMIZATION_MODEL = VAWN_DIR / "research" / "apu62_timing_model.json"
TIMING_RECOMMENDATIONS = VAWN_DIR / "research" / "apu62_timing_recommendations.json"

# Base engagement schedule (existing system)
BASE_SCHEDULE = {
    "morning": {"time": "09:30", "base_priority": 0.8, "window_minutes": 60},
    "midday": {"time": "13:00", "base_priority": 0.6, "window_minutes": 90},
    "evening": {"time": "20:30", "base_priority": 0.9, "window_minutes": 45}
}

# Platform-specific timing factors
PLATFORM_TIMING_FACTORS = {
    "bluesky": {
        "peak_hours": [9, 13, 17, 20],  # When Bluesky users are most active
        "timezone_consideration": "EST",  # Primary timezone for engagement
        "response_window_hours": 2  # How long likes/follows remain effective
    },
    "instagram": {
        "peak_hours": [11, 15, 19, 21],
        "timezone_consideration": "EST",
        "response_window_hours": 4
    },
    "tiktok": {
        "peak_hours": [18, 19, 20, 21, 22],
        "timezone_consideration": "EST",
        "response_window_hours": 6
    },
    "x": {
        "peak_hours": [9, 12, 17, 19],
        "timezone_consideration": "EST",
        "response_window_hours": 3
    },
    "threads": {
        "peak_hours": [10, 14, 18, 20],
        "timezone_consideration": "EST",
        "response_window_hours": 3
    }
}


class EngagementTimingOptimizer:
    def __init__(self):
        self.today = today_str()
        self.model_data = self.load_timing_model()
        self.analytics_data = self.load_analytics_data()

    def load_timing_model(self):
        """Load or initialize the timing optimization model."""
        try:
            return load_json(OPTIMIZATION_MODEL)
        except:
            return {
                "version": "1.0",
                "last_updated": datetime.now().isoformat(),
                "platform_patterns": {},
                "department_patterns": {},
                "effectiveness_thresholds": {
                    "excellent": 2.5,
                    "good": 1.5,
                    "average": 1.0,
                    "poor": 0.5
                },
                "learning_data": {
                    "total_sessions": 0,
                    "pattern_confidence": 0.0
                }
            }

    def save_timing_model(self):
        """Save the updated timing optimization model."""
        self.model_data["last_updated"] = datetime.now().isoformat()
        save_json(OPTIMIZATION_MODEL, self.model_data)

    def load_analytics_data(self):
        """Load historical analytics data for pattern analysis."""
        analytics = []

        # Load APU-62 coordination logs
        try:
            coord_data = load_json(VAWN_DIR / "research" / "apu62_coordination_log.json")
            for date_str, day_data in coord_data.items():
                for event in day_data.get("coordination_events", []):
                    analytics.append({
                        "date": date_str,
                        "timestamp": event["timestamp"],
                        "platform": event["platform"],
                        "roi": event["calculated_roi"],
                        "slot_type": event["slot_type"]
                    })
        except:
            pass

        # Load enhanced bot logs
        try:
            enhanced_data = load_json(VAWN_DIR / "research" / "engagement_bot_enhanced_log.json")
            for date_str, day_entries in enhanced_data.items():
                for entry in day_entries:
                    if entry.get("success", False):
                        # Calculate effectiveness from enhanced bot data
                        likes = entry.get("metrics", {}).get("likes", 0)
                        time_ms = entry.get("metrics", {}).get("performance", {}).get("total_time_ms", 1000)
                        effectiveness = likes / (time_ms / 60000)  # likes per minute

                        analytics.append({
                            "date": date_str,
                            "timestamp": entry["time"],
                            "platform": "bluesky",
                            "roi": effectiveness,
                            "slot_type": self.classify_time_slot(entry["time"])
                        })
        except:
            pass

        return analytics

    def classify_time_slot(self, timestamp_str):
        """Classify a timestamp into morning/midday/evening slot."""
        try:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            hour = dt.hour

            if 8 <= hour <= 11:
                return "morning"
            elif 11 < hour <= 15:
                return "midday"
            elif 17 <= hour <= 23:
                return "evening"
            else:
                return "off_schedule"
        except:
            return "unknown"

    def analyze_platform_timing_patterns(self, platform):
        """Analyze timing effectiveness patterns for a specific platform."""
        platform_data = [d for d in self.analytics_data if d["platform"] == platform]

        if len(platform_data) < 5:  # Need minimum data for pattern analysis
            return None

        # Group by hour of day
        hourly_effectiveness = defaultdict(list)
        for data_point in platform_data:
            try:
                dt = datetime.fromisoformat(data_point["timestamp"].replace('Z', '+00:00'))
                hour = dt.hour
                hourly_effectiveness[hour].append(data_point["roi"])
            except:
                continue

        # Calculate average effectiveness by hour
        hourly_averages = {}
        for hour, roi_values in hourly_effectiveness.items():
            if len(roi_values) >= 2:  # Need multiple data points
                hourly_averages[hour] = {
                    "average_roi": statistics.mean(roi_values),
                    "median_roi": statistics.median(roi_values),
                    "sample_size": len(roi_values),
                    "std_dev": statistics.stdev(roi_values) if len(roi_values) > 1 else 0
                }

        # Find peak effectiveness hours
        if hourly_averages:
            best_hours = sorted(hourly_averages.items(), key=lambda x: x[1]["average_roi"], reverse=True)
            peak_hours = [hour for hour, data in best_hours[:3] if data["average_roi"] > 1.0]

            return {
                "platform": platform,
                "peak_hours": peak_hours,
                "hourly_patterns": hourly_averages,
                "best_performance_hour": best_hours[0][0] if best_hours else None,
                "pattern_confidence": min(1.0, len(platform_data) / 20.0)  # Confidence based on sample size
            }

        return None

    def analyze_department_timing_preferences(self):
        """Analyze timing preferences based on department focus."""
        # This would integrate with department health data over time
        # For now, provide baseline recommendations

        department_timing = {
            "legal": {
                "preferred_hours": [9, 10, 14, 15],  # Business hours
                "avoid_hours": [20, 21, 22],  # After business hours
                "reasoning": "Professional content performs better during business hours"
            },
            "a_and_r": {
                "preferred_hours": [11, 15, 19, 20],  # Creative peak times
                "avoid_hours": [8, 9],  # Early morning
                "reasoning": "Artist discovery content performs well mid-day and evening"
            },
            "creative_revenue": {
                "preferred_hours": [13, 17, 19, 21],  # Marketing peak times
                "avoid_hours": [6, 7, 8],  # Very early
                "reasoning": "Marketing content performs well during engagement peaks"
            },
            "operations": {
                "preferred_hours": [9, 13, 17],  # Operational hours
                "avoid_hours": [22, 23, 0],  # Late night
                "reasoning": "Operational content aligns with work schedules"
            }
        }

        return department_timing

    def calculate_optimal_timing_score(self, hour, platform, department):
        """Calculate optimization score for specific hour/platform/department combination."""
        base_score = 0.5

        # Platform timing factor
        platform_config = PLATFORM_TIMING_FACTORS.get(platform, {})
        peak_hours = platform_config.get("peak_hours", [])

        if hour in peak_hours:
            base_score += 0.3
        elif abs(min(peak_hours, key=lambda x: abs(x - hour)) - hour) <= 1:
            base_score += 0.15  # Near peak hours

        # Department preference factor
        dept_timing = self.analyze_department_timing_preferences()
        dept_config = dept_timing.get(department, {})

        preferred_hours = dept_config.get("preferred_hours", [])
        avoid_hours = dept_config.get("avoid_hours", [])

        if hour in preferred_hours:
            base_score += 0.2
        elif hour in avoid_hours:
            base_score -= 0.3

        # Historical pattern factor (if available)
        platform_patterns = self.model_data.get("platform_patterns", {}).get(platform, {})
        if platform_patterns:
            hourly_data = platform_patterns.get("hourly_patterns", {})
            if str(hour) in hourly_data:
                historical_roi = hourly_data[str(hour)]["average_roi"]
                # Normalize historical performance to score component
                if historical_roi > 2.0:
                    base_score += 0.25
                elif historical_roi > 1.5:
                    base_score += 0.15
                elif historical_roi < 0.5:
                    base_score -= 0.2

        return max(0.0, min(1.0, base_score))

    def generate_timing_recommendations(self, target_date=None):
        """Generate adaptive timing recommendations for engagement."""
        if target_date is None:
            target_date = datetime.now().date()

        recommendations = {
            "date": target_date.isoformat(),
            "generated_at": datetime.now().isoformat(),
            "base_schedule_adjustments": {},
            "platform_specific": {},
            "department_optimization": {},
            "confidence_level": self.model_data["learning_data"]["pattern_confidence"]
        }

        # Analyze each base schedule slot
        for slot_name, slot_config in BASE_SCHEDULE.items():
            slot_hour = int(slot_config["time"].split(":")[0])
            base_priority = slot_config["base_priority"]

            # Calculate platform-specific scores for this slot
            platform_scores = {}
            for platform in PLATFORM_TIMING_FACTORS.keys():
                score = self.calculate_optimal_timing_score(slot_hour, platform, "general")
                platform_scores[platform] = score

            # Determine if slot timing should be adjusted
            avg_platform_score = statistics.mean(platform_scores.values())
            adjustment_factor = avg_platform_score - 0.6  # 0.6 is neutral

            recommendations["base_schedule_adjustments"][slot_name] = {
                "original_time": slot_config["time"],
                "priority_adjustment": adjustment_factor,
                "recommended_priority": min(1.0, max(0.1, base_priority + adjustment_factor)),
                "platform_scores": platform_scores,
                "adjustment_reasoning": self.get_adjustment_reasoning(adjustment_factor)
            }

        # Department-specific optimization
        for department in ["legal", "a_and_r", "creative_revenue", "operations"]:
            dept_recommendations = []

            for slot_name, slot_config in BASE_SCHEDULE.items():
                slot_hour = int(slot_config["time"].split(":")[0])

                # Find best platform for this department at this time
                best_platform_score = 0
                best_platform = None

                for platform in PLATFORM_TIMING_FACTORS.keys():
                    score = self.calculate_optimal_timing_score(slot_hour, platform, department)
                    if score > best_platform_score:
                        best_platform_score = score
                        best_platform = platform

                if best_platform_score > 0.6:
                    dept_recommendations.append({
                        "slot": slot_name,
                        "time": slot_config["time"],
                        "recommended_platform": best_platform,
                        "effectiveness_score": best_platform_score,
                        "action": "high_priority" if best_platform_score > 0.8 else "standard"
                    })

            recommendations["department_optimization"][department] = dept_recommendations

        # Platform-specific timing windows
        for platform, config in PLATFORM_TIMING_FACTORS.items():
            platform_recs = []

            for peak_hour in config["peak_hours"]:
                # Find which base slot this aligns with
                best_slot = None
                min_diff = float('inf')

                for slot_name, slot_config in BASE_SCHEDULE.items():
                    slot_hour = int(slot_config["time"].split(":")[0])
                    diff = abs(slot_hour - peak_hour)
                    if diff < min_diff:
                        min_diff = diff
                        best_slot = slot_name

                platform_recs.append({
                    "peak_hour": f"{peak_hour:02d}:00",
                    "aligned_slot": best_slot,
                    "alignment_quality": "excellent" if min_diff <= 1 else "good" if min_diff <= 2 else "poor",
                    "recommendation": "use_slot" if min_diff <= 2 else "consider_additional_timing"
                })

            recommendations["platform_specific"][platform] = platform_recs

        return recommendations

    def get_adjustment_reasoning(self, adjustment_factor):
        """Get human-readable reasoning for timing adjustments."""
        if adjustment_factor > 0.2:
            return "Historical data shows high engagement potential - increase priority"
        elif adjustment_factor > 0.1:
            return "Slightly above average performance - modest priority increase"
        elif adjustment_factor < -0.2:
            return "Below average performance - consider alternative timing"
        elif adjustment_factor < -0.1:
            return "Slightly below average - reduce priority or optimize content"
        else:
            return "Performance aligns with baseline expectations"

    def update_model_with_feedback(self, engagement_results):
        """Update timing model with new engagement effectiveness data."""
        # Update platform patterns
        for result in engagement_results:
            platform = result.get("platform")
            timestamp = result.get("timestamp")
            roi = result.get("roi", 0)

            if platform and timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    hour = dt.hour

                    # Initialize platform data if needed
                    if platform not in self.model_data["platform_patterns"]:
                        self.model_data["platform_patterns"][platform] = {
                            "hourly_patterns": {},
                            "total_sessions": 0,
                            "last_updated": datetime.now().isoformat()
                        }

                    platform_data = self.model_data["platform_patterns"][platform]

                    # Update hourly pattern
                    if str(hour) not in platform_data["hourly_patterns"]:
                        platform_data["hourly_patterns"][str(hour)] = {
                            "total_roi": 0,
                            "session_count": 0,
                            "average_roi": 0
                        }

                    hour_data = platform_data["hourly_patterns"][str(hour)]
                    hour_data["total_roi"] += roi
                    hour_data["session_count"] += 1
                    hour_data["average_roi"] = hour_data["total_roi"] / hour_data["session_count"]

                    platform_data["total_sessions"] += 1
                    platform_data["last_updated"] = datetime.now().isoformat()

                except Exception as e:
                    print(f"[WARN] Could not update model with result: {e}")

        # Update learning data
        self.model_data["learning_data"]["total_sessions"] += len(engagement_results)

        # Update pattern confidence based on data volume
        total_sessions = self.model_data["learning_data"]["total_sessions"]
        self.model_data["learning_data"]["pattern_confidence"] = min(1.0, total_sessions / 100.0)

        self.save_timing_model()

    def get_next_optimal_engagement_time(self, platform=None, department=None):
        """Get the next optimal engagement time for given parameters."""
        now = datetime.now()
        current_hour = now.hour

        # Generate recommendations for today
        recommendations = self.generate_timing_recommendations()

        # Find the next best timing opportunity
        best_opportunities = []

        # Check remaining slots today
        for slot_name, adjustment in recommendations["base_schedule_adjustments"].items():
            slot_time = BASE_SCHEDULE[slot_name]["time"]
            slot_hour = int(slot_time.split(":")[0])
            slot_minute = int(slot_time.split(":")[1])

            # Check if slot is in the future today
            slot_datetime = now.replace(hour=slot_hour, minute=slot_minute, second=0, microsecond=0)
            if slot_datetime > now:
                opportunity = {
                    "datetime": slot_datetime,
                    "slot_name": slot_name,
                    "priority_score": adjustment["recommended_priority"],
                    "platform_scores": adjustment["platform_scores"],
                    "time_until": str(slot_datetime - now)
                }
                best_opportunities.append(opportunity)

        # Sort by priority score
        best_opportunities.sort(key=lambda x: x["priority_score"], reverse=True)

        if best_opportunities:
            next_optimal = best_opportunities[0]

            # Filter by platform if specified
            if platform and platform in next_optimal["platform_scores"]:
                platform_score = next_optimal["platform_scores"][platform]
                next_optimal["platform_specific_score"] = platform_score
                next_optimal["platform_recommendation"] = "excellent" if platform_score > 0.8 else "good" if platform_score > 0.6 else "fair"

            return next_optimal

        return None


def main():
    import argparse

    parser = argparse.ArgumentParser(description="APU-62 Adaptive Engagement Timing Optimizer")
    parser.add_argument("--analyze", action="store_true", help="Analyze timing patterns")
    parser.add_argument("--recommend", action="store_true", help="Generate timing recommendations")
    parser.add_argument("--next-optimal", help="Get next optimal time (specify platform)")
    parser.add_argument("--update-model", help="Update model with feedback (JSON file path)")
    parser.add_argument("--department", help="Filter recommendations by department")

    args = parser.parse_args()

    optimizer = EngagementTimingOptimizer()

    print(f"\n=== APU-62 Adaptive Timing Optimizer ===")
    print(f"Model Confidence: {optimizer.model_data['learning_data']['pattern_confidence']:.2f}")
    print(f"Total Learning Sessions: {optimizer.model_data['learning_data']['total_sessions']}")

    if args.analyze:
        print(f"\n--- Platform Timing Analysis ---")

        for platform in PLATFORM_TIMING_FACTORS.keys():
            patterns = optimizer.analyze_platform_timing_patterns(platform)

            if patterns:
                print(f"\n📊 {platform.title()}:")
                print(f"   Peak Hours: {patterns['peak_hours']}")
                print(f"   Best Hour: {patterns['best_performance_hour']:02d}:00")
                print(f"   Confidence: {patterns['pattern_confidence']:.2f}")

                # Show top 3 performing hours
                hourly = patterns['hourly_patterns']
                if hourly:
                    top_hours = sorted(hourly.items(), key=lambda x: x[1]['average_roi'], reverse=True)[:3]
                    print(f"   Top Performance:")
                    for hour, data in top_hours:
                        print(f"     {hour:02d}:00 - ROI: {data['average_roi']:.2f} (n={data['sample_size']})")
            else:
                print(f"\n📊 {platform.title()}: Insufficient data for analysis")

    elif args.recommend:
        print(f"\n--- Timing Recommendations ---")
        recommendations = optimizer.generate_timing_recommendations()

        print(f"📅 Recommendations for {recommendations['date']}")
        print(f"🔬 Confidence Level: {recommendations['confidence_level']:.2f}")

        print(f"\n⏰ Base Schedule Adjustments:")
        for slot, adjustment in recommendations["base_schedule_adjustments"].items():
            original_priority = BASE_SCHEDULE[slot]["base_priority"]
            new_priority = adjustment["recommended_priority"]
            change = new_priority - original_priority

            status_emoji = "📈" if change > 0.1 else "📉" if change < -0.1 else "📊"
            print(f"   {status_emoji} {slot.title()} ({adjustment['original_time']}):")
            print(f"      Priority: {original_priority:.2f} → {new_priority:.2f} ({change:+.2f})")
            print(f"      {adjustment['adjustment_reasoning']}")

        if args.department and args.department in recommendations["department_optimization"]:
            print(f"\n🎯 {args.department.title()} Department Optimization:")
            dept_recs = recommendations["department_optimization"][args.department]

            for rec in dept_recs:
                action_emoji = "🚀" if rec["action"] == "high_priority" else "✅"
                print(f"   {action_emoji} {rec['slot'].title()} ({rec['time']}):")
                print(f"      Platform: {rec['recommended_platform'].title()}")
                print(f"      Score: {rec['effectiveness_score']:.2f}")

    elif args.next_optimal:
        print(f"\n--- Next Optimal Engagement Time ---")
        platform = args.next_optimal.lower()

        next_time = optimizer.get_next_optimal_engagement_time(platform=platform, department=args.department)

        if next_time:
            print(f"🎯 Next Opportunity: {next_time['datetime'].strftime('%H:%M')} ({next_time['slot_name']})")
            print(f"⏱️  Time Until: {next_time['time_until']}")
            print(f"📊 Priority Score: {next_time['priority_score']:.2f}")

            if "platform_specific_score" in next_time:
                print(f"📱 {platform.title()} Score: {next_time['platform_specific_score']:.2f} ({next_time['platform_recommendation']})")

            print(f"\n💡 Platform Scores for this slot:")
            for plat, score in next_time["platform_scores"].items():
                status = "🟢" if score > 0.7 else "🟡" if score > 0.5 else "🔴"
                print(f"   {status} {plat.title()}: {score:.2f}")
        else:
            print(f"❌ No optimal timing found for today")

    elif args.update_model:
        print(f"\n--- Updating Timing Model ---")
        try:
            feedback_data = load_json(Path(args.update_model))

            if isinstance(feedback_data, list):
                optimizer.update_model_with_feedback(feedback_data)
                print(f"✅ Updated model with {len(feedback_data)} feedback entries")
            else:
                print(f"❌ Feedback data must be a list of engagement results")

        except Exception as e:
            print(f"❌ Failed to update model: {e}")

    else:
        print(f"\n--- Quick Status ---")
        now = datetime.now()

        # Check current slot timing
        current_slot = None
        for slot_name, config in BASE_SCHEDULE.items():
            slot_hour = int(config["time"].split(":")[0])
            window = config["window_minutes"]

            if abs(now.hour - slot_hour) * 60 + abs(now.minute - int(config["time"].split(":")[1])) <= window:
                current_slot = slot_name
                break

        if current_slot:
            print(f"⏰ Current Slot: {current_slot} (optimal timing window)")
        else:
            print(f"⏸️  Off Schedule: {now.strftime('%H:%M')} (consider waiting)")

        # Show next optimal time
        next_time = optimizer.get_next_optimal_engagement_time()
        if next_time:
            print(f"🔮 Next Optimal: {next_time['datetime'].strftime('%H:%M')} ({next_time['time_until']})")

        print(f"\nAvailable Commands:")
        print(f"   --analyze    : Analyze platform timing patterns")
        print(f"   --recommend  : Generate timing recommendations")
        print(f"   --next-optimal <platform> : Find next optimal time")

    print()


if __name__ == "__main__":
    main()