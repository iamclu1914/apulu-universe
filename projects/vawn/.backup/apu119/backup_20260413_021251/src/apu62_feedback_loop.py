"""
apu62_feedback_loop.py — Department Health Feedback Loop Integration
Part of APU-62 by Dex - Community Agent for closed-loop engagement optimization.

Features:
- Bidirectional feedback between engagement activities and department health
- Dynamic strategy adjustment based on health score changes
- Correlation analysis between engagement and department improvements
- Automated optimization recommendations
- Real-time feedback loop monitoring and adjustment
- Integration with existing unified monitoring system

Feedback Loop Components:
1. Health Impact Analysis: Track how engagement affects department scores
2. Strategy Adaptation: Adjust engagement based on health changes
3. Correlation Tracking: Identify which engagement types improve which departments
4. Optimization Engine: Continuously improve engagement-to-health mapping
5. Feedback Validation: Ensure feedback loops are improving overall effectiveness
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
import statistics
from collections import defaultdict, deque

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import VAWN_DIR, load_json, save_json, log_run, today_str

# Configuration
FEEDBACK_LOG = VAWN_DIR / "research" / "apu62_feedback_log.json"
CORRELATION_ANALYTICS = VAWN_DIR / "research" / "apu62_correlation_analytics.json"
OPTIMIZATION_TRACKING = VAWN_DIR / "research" / "apu62_optimization_tracking.json"
FEEDBACK_MODEL = VAWN_DIR / "research" / "apu62_feedback_model.json"

# Department health target thresholds
HEALTH_TARGETS = {
    "legal": {"excellent": 0.9, "good": 0.7, "acceptable": 0.5, "poor": 0.3},
    "a_and_r": {"excellent": 0.9, "good": 0.7, "acceptable": 0.5, "poor": 0.3},
    "creative_revenue": {"excellent": 0.9, "good": 0.7, "acceptable": 0.5, "poor": 0.3},
    "operations": {"excellent": 0.9, "good": 0.7, "acceptable": 0.5, "poor": 0.3}
}

# Engagement impact weights (how much different engagement types affect departments)
ENGAGEMENT_IMPACT_WEIGHTS = {
    "bluesky_likes": {
        "legal": 0.1,  # Legal content doesn't get many likes
        "a_and_r": 0.4,  # Artist discovery content gets good engagement
        "creative_revenue": 0.3,  # Marketing content gets moderate engagement
        "operations": 0.2   # Behind-scenes content gets some engagement
    },
    "cross_platform_reach": {
        "legal": 0.2,
        "a_and_r": 0.4,
        "creative_revenue": 0.5,  # Marketing benefits most from reach
        "operations": 0.3
    },
    "content_quality": {
        "legal": 0.4,  # Quality matters most for legal content
        "a_and_r": 0.3,
        "creative_revenue": 0.3,
        "operations": 0.2
    },
    "timing_optimization": {
        "legal": 0.3,
        "a_and_r": 0.2,
        "creative_revenue": 0.4,  # Timing crucial for marketing
        "operations": 0.1
    }
}


class DepartmentHealthTracker:
    """Tracks department health changes over time."""

    def __init__(self, max_history=50):
        self.max_history = max_history
        self.health_history = defaultdict(lambda: deque(maxlen=max_history))
        self.last_update = {}

    def update_health_scores(self, health_data):
        """Update health scores and track changes."""
        timestamp = datetime.now().isoformat()

        changes = {}
        for department, score in health_data.items():
            if department == "timestamp":
                continue

            # Calculate change from last update
            last_score = self.get_latest_score(department)
            change = score - last_score if last_score is not None else 0

            # Store health record
            health_record = {
                "timestamp": timestamp,
                "score": score,
                "change": change,
                "trend": self.calculate_trend(department)
            }

            self.health_history[department].append(health_record)
            self.last_update[department] = timestamp
            changes[department] = change

        return changes

    def get_latest_score(self, department):
        """Get most recent health score for department."""
        history = self.health_history[department]
        return history[-1]["score"] if history else None

    def calculate_trend(self, department, lookback=5):
        """Calculate health trend for department."""
        history = list(self.health_history[department])
        if len(history) < 2:
            return "stable"

        recent_scores = [record["score"] for record in history[-lookback:]]

        if len(recent_scores) < 2:
            return "stable"

        # Calculate linear trend
        x_vals = list(range(len(recent_scores)))
        if len(set(recent_scores)) == 1:
            return "stable"

        # Simple trend calculation
        first_half_avg = statistics.mean(recent_scores[:len(recent_scores)//2]) if len(recent_scores) >= 4 else recent_scores[0]
        second_half_avg = statistics.mean(recent_scores[len(recent_scores)//2:])

        trend_strength = second_half_avg - first_half_avg

        if trend_strength > 0.05:
            return "improving"
        elif trend_strength < -0.05:
            return "declining"
        else:
            return "stable"

    def get_department_analytics(self, department, days=7):
        """Get analytics for a specific department."""
        cutoff_time = datetime.now() - timedelta(days=days)

        recent_records = [
            record for record in self.health_history[department]
            if datetime.fromisoformat(record["timestamp"]) >= cutoff_time
        ]

        if not recent_records:
            return None

        scores = [record["score"] for record in recent_records]
        changes = [record["change"] for record in recent_records]

        return {
            "department": department,
            "current_score": scores[-1] if scores else 0,
            "average_score": statistics.mean(scores),
            "score_range": (min(scores), max(scores)),
            "total_change": sum(changes),
            "trend": recent_records[-1]["trend"] if recent_records else "stable",
            "volatility": statistics.stdev(scores) if len(scores) > 1 else 0,
            "records_analyzed": len(recent_records)
        }


class EngagementImpactAnalyzer:
    """Analyzes the impact of engagement activities on department health."""

    def __init__(self):
        self.engagement_history = deque(maxlen=100)
        self.impact_correlations = {}

    def record_engagement_activity(self, activity_data):
        """Record engagement activity for impact analysis."""
        activity_record = {
            "timestamp": datetime.now().isoformat(),
            "platform": activity_data.get("platform", "unknown"),
            "engagement_type": activity_data.get("type", "general"),
            "department_focus": activity_data.get("department_focus", "general"),
            "metrics": activity_data.get("metrics", {}),
            "quality_score": activity_data.get("quality_score", 0.5),
            "effectiveness_score": activity_data.get("effectiveness_score", 0.5)
        }

        self.engagement_history.append(activity_record)
        return activity_record

    def analyze_department_impact(self, department, health_changes, engagement_activities):
        """Analyze how engagement activities impacted specific department health."""
        impact_analysis = {
            "department": department,
            "health_change": health_changes.get(department, 0),
            "contributing_activities": [],
            "impact_score": 0,
            "confidence": 0
        }

        # Find engagement activities that could have impacted this department
        for activity in engagement_activities:
            if activity.get("department_focus") == department or activity.get("department_focus") == "general":

                # Calculate potential impact based on engagement type and metrics
                base_impact = self.calculate_base_impact(activity, department)

                # Weight by engagement effectiveness
                effectiveness = activity.get("effectiveness_score", 0.5)
                quality = activity.get("quality_score", 0.5)

                weighted_impact = base_impact * effectiveness * quality

                contributing_activity = {
                    "activity_type": activity.get("engagement_type", "general"),
                    "platform": activity.get("platform", "unknown"),
                    "base_impact": base_impact,
                    "weighted_impact": weighted_impact,
                    "effectiveness": effectiveness,
                    "quality": quality
                }

                impact_analysis["contributing_activities"].append(contributing_activity)
                impact_analysis["impact_score"] += weighted_impact

        # Calculate confidence based on number of activities and consistency
        num_activities = len(impact_analysis["contributing_activities"])
        impact_analysis["confidence"] = min(1.0, num_activities / 3.0)  # Max confidence with 3+ activities

        return impact_analysis

    def calculate_base_impact(self, activity, department):
        """Calculate base impact of activity on department."""
        engagement_type = activity.get("engagement_type", "general")

        # Map engagement types to impact weights
        type_weights = {
            "bluesky_like": ENGAGEMENT_IMPACT_WEIGHTS["bluesky_likes"],
            "cross_platform": ENGAGEMENT_IMPACT_WEIGHTS["cross_platform_reach"],
            "quality_content": ENGAGEMENT_IMPACT_WEIGHTS["content_quality"],
            "timing_optimization": ENGAGEMENT_IMPACT_WEIGHTS["timing_optimization"]
        }

        weight_map = type_weights.get(engagement_type, ENGAGEMENT_IMPACT_WEIGHTS["bluesky_likes"])
        return weight_map.get(department, 0.1)

    def identify_optimization_opportunities(self, department_analytics):
        """Identify opportunities to optimize engagement for better health outcomes."""
        opportunities = []

        for department, analytics in department_analytics.items():
            if not analytics:
                continue

            current_score = analytics["current_score"]
            trend = analytics["trend"]

            # Identify departments needing attention
            if current_score < HEALTH_TARGETS[department]["acceptable"]:
                opportunity = {
                    "department": department,
                    "priority": "high",
                    "current_score": current_score,
                    "target_score": HEALTH_TARGETS[department]["good"],
                    "recommended_actions": self.get_recommended_actions(department, current_score, trend),
                    "estimated_impact": self.estimate_improvement_potential(department, current_score)
                }
                opportunities.append(opportunity)

            elif current_score < HEALTH_TARGETS[department]["good"] and trend == "declining":
                opportunity = {
                    "department": department,
                    "priority": "medium",
                    "current_score": current_score,
                    "target_score": HEALTH_TARGETS[department]["good"],
                    "recommended_actions": self.get_recommended_actions(department, current_score, trend),
                    "estimated_impact": self.estimate_improvement_potential(department, current_score)
                }
                opportunities.append(opportunity)

        # Sort by priority and potential impact
        opportunities.sort(key=lambda x: (
            {"high": 3, "medium": 2, "low": 1}[x["priority"]],
            x["estimated_impact"]
        ), reverse=True)

        return opportunities

    def get_recommended_actions(self, department, current_score, trend):
        """Get recommended engagement actions for department improvement."""
        actions = []

        # Base actions for all departments
        if current_score < 0.4:
            actions.append("Increase engagement frequency for this department")
            actions.append("Focus on high-quality content targeting this department")

        # Department-specific actions
        dept_actions = {
            "legal": [
                "Engage with copyright and legal music content",
                "Share legal compliance and rights management information",
                "Connect with music law and rights management accounts"
            ],
            "a_and_r": [
                "Actively discover and engage with new talent",
                "Share and promote unsigned artist content",
                "Engage with demo submissions and artist discovery posts"
            ],
            "creative_revenue": [
                "Optimize timing for maximum audience reach",
                "Focus on conversion-oriented engagement",
                "Engage with marketing and promotional content"
            ],
            "operations": [
                "Share behind-the-scenes and production content",
                "Engage with industry workflow and process discussions",
                "Connect with studio and production-focused accounts"
            ]
        }

        actions.extend(dept_actions.get(department, []))

        # Trend-based actions
        if trend == "declining":
            actions.append("Implement immediate intervention strategies")
            actions.append("Review and adjust current engagement approach")

        return actions[:5]  # Limit to top 5 actions

    def estimate_improvement_potential(self, department, current_score):
        """Estimate potential improvement from optimized engagement."""
        # Simple model - could be enhanced with ML
        target_score = HEALTH_TARGETS[department]["good"]
        potential_improvement = target_score - current_score

        # Factor in engagement effectiveness for this department
        avg_effectiveness = statistics.mean(ENGAGEMENT_IMPACT_WEIGHTS["bluesky_likes"].values())
        dept_effectiveness = ENGAGEMENT_IMPACT_WEIGHTS["bluesky_likes"].get(department, avg_effectiveness)

        # Estimate achievable improvement (conservative)
        estimated_improvement = potential_improvement * dept_effectiveness * 0.7  # 70% achievability factor

        return max(0, min(0.3, estimated_improvement))  # Cap at 0.3 improvement


class FeedbackLoopCoordinator:
    """Coordinates the entire feedback loop between engagement and department health."""

    def __init__(self):
        self.health_tracker = DepartmentHealthTracker()
        self.impact_analyzer = EngagementImpactAnalyzer()
        self.feedback_model = self.load_feedback_model()

    def load_feedback_model(self):
        """Load or initialize feedback loop model."""
        try:
            return load_json(FEEDBACK_MODEL)
        except:
            return {
                "version": "1.0",
                "last_updated": datetime.now().isoformat(),
                "learning_cycles": 0,
                "effectiveness_history": [],
                "optimization_rules": {},
                "correlation_patterns": {}
            }

    def save_feedback_model(self):
        """Save feedback model to persistent storage."""
        self.feedback_model["last_updated"] = datetime.now().isoformat()
        save_json(FEEDBACK_MODEL, self.feedback_model)

    def process_feedback_cycle(self, engagement_data, health_data):
        """Process a complete feedback cycle."""
        cycle_timestamp = datetime.now().isoformat()

        # Update health tracking
        health_changes = self.health_tracker.update_health_scores(health_data)

        # Record engagement activities
        engagement_activities = []
        for activity in engagement_data:
            activity_record = self.impact_analyzer.record_engagement_activity(activity)
            engagement_activities.append(activity_record)

        # Analyze impact correlations
        impact_analysis = {}
        for department in health_changes:
            impact_analysis[department] = self.impact_analyzer.analyze_department_impact(
                department, health_changes, engagement_activities
            )

        # Get department analytics
        department_analytics = {}
        for department in ["legal", "a_and_r", "creative_revenue", "operations"]:
            analytics = self.health_tracker.get_department_analytics(department)
            if analytics:
                department_analytics[department] = analytics

        # Identify optimization opportunities
        opportunities = self.impact_analyzer.identify_optimization_opportunities(department_analytics)

        # Update feedback model
        self.update_feedback_model(impact_analysis, department_analytics, opportunities)

        # Create feedback cycle report
        cycle_report = {
            "timestamp": cycle_timestamp,
            "health_changes": health_changes,
            "impact_analysis": impact_analysis,
            "department_analytics": department_analytics,
            "optimization_opportunities": opportunities,
            "feedback_effectiveness": self.calculate_feedback_effectiveness(department_analytics),
            "recommendations": self.generate_adaptive_recommendations(opportunities, department_analytics)
        }

        # Log cycle
        self.log_feedback_cycle(cycle_report)

        return cycle_report

    def update_feedback_model(self, impact_analysis, department_analytics, opportunities):
        """Update feedback model with new learning data."""
        self.feedback_model["learning_cycles"] += 1

        # Update correlation patterns
        for department, analysis in impact_analysis.items():
            if department not in self.feedback_model["correlation_patterns"]:
                self.feedback_model["correlation_patterns"][department] = {
                    "activity_correlations": {},
                    "effectiveness_factors": {}
                }

            # Track which activities correlate with positive health changes
            for activity in analysis["contributing_activities"]:
                activity_type = activity["activity_type"]
                impact = activity["weighted_impact"]

                if activity_type not in self.feedback_model["correlation_patterns"][department]["activity_correlations"]:
                    self.feedback_model["correlation_patterns"][department]["activity_correlations"][activity_type] = []

                self.feedback_model["correlation_patterns"][department]["activity_correlations"][activity_type].append(impact)

        # Update optimization rules based on successful opportunities
        for opportunity in opportunities:
            department = opportunity["department"]
            if opportunity["priority"] == "high":
                if department not in self.feedback_model["optimization_rules"]:
                    self.feedback_model["optimization_rules"][department] = {
                        "priority_triggers": [],
                        "successful_interventions": []
                    }

                self.feedback_model["optimization_rules"][department]["priority_triggers"].append({
                    "score_threshold": opportunity["current_score"],
                    "recommended_actions": opportunity["recommended_actions"][:3],  # Top 3 actions
                    "timestamp": datetime.now().isoformat()
                })

        self.save_feedback_model()

    def calculate_feedback_effectiveness(self, department_analytics):
        """Calculate overall effectiveness of the feedback loop."""
        if not department_analytics:
            return 0.0

        effectiveness_scores = []

        for department, analytics in department_analytics.items():
            if analytics:
                # Score based on current health, trend, and stability
                current_score = analytics["current_score"]
                trend_bonus = {"improving": 0.2, "stable": 0.0, "declining": -0.2}[analytics["trend"]]
                stability_bonus = max(0, 0.1 - analytics["volatility"])  # Lower volatility is better

                dept_effectiveness = current_score + trend_bonus + stability_bonus
                effectiveness_scores.append(max(0, min(1.0, dept_effectiveness)))

        overall_effectiveness = statistics.mean(effectiveness_scores) if effectiveness_scores else 0.0

        # Track effectiveness history
        self.feedback_model["effectiveness_history"].append({
            "timestamp": datetime.now().isoformat(),
            "effectiveness": overall_effectiveness,
            "department_scores": effectiveness_scores
        })

        # Keep only last 30 effectiveness measurements
        if len(self.feedback_model["effectiveness_history"]) > 30:
            self.feedback_model["effectiveness_history"] = self.feedback_model["effectiveness_history"][-30:]

        return overall_effectiveness

    def generate_adaptive_recommendations(self, opportunities, department_analytics):
        """Generate adaptive recommendations based on feedback patterns."""
        recommendations = []

        # Priority-based recommendations
        high_priority_depts = [opp["department"] for opp in opportunities if opp["priority"] == "high"]
        if high_priority_depts:
            recommendations.append({
                "type": "immediate_action",
                "priority": "high",
                "message": f"Immediate attention needed: {', '.join(high_priority_depts)}",
                "actions": [opp["recommended_actions"][0] for opp in opportunities if opp["priority"] == "high"]
            })

        # Pattern-based recommendations from feedback model
        for department, patterns in self.feedback_model.get("correlation_patterns", {}).items():
            correlations = patterns.get("activity_correlations", {})

            if correlations:
                # Find most effective activity type for this department
                avg_impacts = {}
                for activity_type, impacts in correlations.items():
                    if impacts:
                        avg_impacts[activity_type] = statistics.mean(impacts)

                if avg_impacts:
                    best_activity = max(avg_impacts, key=avg_impacts.get)
                    if avg_impacts[best_activity] > 0.1:  # Meaningful impact threshold
                        recommendations.append({
                            "type": "optimization",
                            "priority": "medium",
                            "message": f"Increase {best_activity} activities for {department} department",
                            "expected_impact": avg_impacts[best_activity],
                            "confidence": len(correlations[best_activity]) / 10.0  # Based on sample size
                        })

        # System-wide recommendations
        overall_health = statistics.mean([
            analytics["current_score"] for analytics in department_analytics.values()
            if analytics
        ]) if department_analytics else 0.5

        if overall_health < 0.6:
            recommendations.append({
                "type": "strategic",
                "priority": "high",
                "message": "Overall department health below target - consider engagement strategy review",
                "overall_health": overall_health
            })

        return recommendations

    def log_feedback_cycle(self, cycle_report):
        """Log feedback cycle data for analysis."""
        try:
            log_data = load_json(FEEDBACK_LOG)
            today = today_str()

            if today not in log_data:
                log_data[today] = []

            log_data[today].append(cycle_report)

            # Keep only last 30 days
            cutoff_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            log_data = {k: v for k, v in log_data.items() if k >= cutoff_date}

            save_json(FEEDBACK_LOG, log_data)

        except Exception as e:
            print(f"[WARN] Could not log feedback cycle: {e}")

    def get_integration_data_for_unified_monitor(self):
        """Generate integration data for the unified monitoring system."""
        recent_analytics = {}
        for department in ["legal", "a_and_r", "creative_revenue", "operations"]:
            analytics = self.health_tracker.get_department_analytics(department)
            if analytics:
                recent_analytics[department] = {
                    "current_score": analytics["current_score"],
                    "trend": analytics["trend"],
                    "volatility": analytics["volatility"]
                }

        effectiveness_history = self.feedback_model.get("effectiveness_history", [])
        recent_effectiveness = effectiveness_history[-1]["effectiveness"] if effectiveness_history else 0.0

        integration_payload = {
            "apu62_feedback_loop": {
                "timestamp": datetime.now().isoformat(),
                "department_analytics": recent_analytics,
                "feedback_effectiveness": recent_effectiveness,
                "learning_cycles": self.feedback_model["learning_cycles"],
                "integration_status": "active",
                "health_improvement_trends": {
                    dept: analytics["trend"] for dept, analytics in recent_analytics.items()
                }
            }
        }

        return integration_payload


# Global feedback loop coordinator
feedback_coordinator = FeedbackLoopCoordinator()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="APU-62 Department Health Feedback Loop")
    parser.add_argument("--process-cycle", action="store_true", help="Process a feedback cycle with latest data")
    parser.add_argument("--analytics", action="store_true", help="Show department health analytics")
    parser.add_argument("--opportunities", action="store_true", help="Show optimization opportunities")
    parser.add_argument("--effectiveness", action="store_true", help="Show feedback loop effectiveness")
    parser.add_argument("--simulate-data", action="store_true", help="Simulate sample data for testing")

    args = parser.parse_args()

    print(f"\n=== APU-62 Department Health Feedback Loop ===")
    print(f"Learning Cycles: {feedback_coordinator.feedback_model['learning_cycles']}")

    if args.simulate_data:
        print(f"\n--- Simulating Sample Data ---")

        # Simulate engagement data
        sample_engagement = [
            {
                "platform": "bluesky",
                "type": "bluesky_like",
                "department_focus": "a_and_r",
                "metrics": {"likes": 8, "quality_score": 0.7},
                "effectiveness_score": 0.8,
                "quality_score": 0.7
            },
            {
                "platform": "instagram",
                "type": "cross_platform",
                "department_focus": "creative_revenue",
                "metrics": {"manual_actions": 12},
                "effectiveness_score": 0.6,
                "quality_score": 0.5
            }
        ]

        # Simulate health data
        sample_health = {
            "legal": 0.45,
            "a_and_r": 0.55,
            "creative_revenue": 0.40,
            "operations": 0.50
        }

        cycle_report = feedback_coordinator.process_feedback_cycle(sample_engagement, sample_health)
        print(f"✅ Processed feedback cycle with simulated data")
        print(f"📊 Health changes: {cycle_report['health_changes']}")
        print(f"🎯 Opportunities identified: {len(cycle_report['optimization_opportunities'])}")

    elif args.process_cycle:
        print(f"\n--- Processing Latest Feedback Cycle ---")

        try:
            # Load latest unified report for health data
            import glob
            pattern = str(VAWN_DIR / "research" / "unified_reports" / "unified_engagement_report_*.json")
            reports = glob.glob(pattern)

            if reports:
                latest_report = max(reports, key=lambda x: Path(x).stat().st_mtime)
                report_data = load_json(Path(latest_report))

                health_data = report_data.get("unified_metrics", {}).get("department_health", {})

                # Load recent engagement data
                engagement_data = []
                try:
                    coord_log = load_json(VAWN_DIR / "research" / "apu62_coordination_log.json")
                    today = today_str()

                    if today in coord_log:
                        for event in coord_log[today].get("coordination_events", []):
                            engagement_data.append({
                                "platform": event["platform"],
                                "type": "bluesky_like" if event["platform"] == "bluesky" else "cross_platform",
                                "department_focus": "general",
                                "metrics": {"roi": event["calculated_roi"]},
                                "effectiveness_score": min(1.0, event["calculated_roi"]),
                                "quality_score": 0.5
                            })
                except:
                    pass

                if health_data:
                    cycle_report = feedback_coordinator.process_feedback_cycle(engagement_data, health_data)
                    print(f"✅ Processed feedback cycle with latest data")
                    print(f"📊 Health changes: {cycle_report['health_changes']}")
                    print(f"🎯 Optimization opportunities: {len(cycle_report['optimization_opportunities'])}")
                    print(f"📈 Feedback effectiveness: {cycle_report['feedback_effectiveness']:.3f}")
                else:
                    print(f"❌ No health data available in latest report")
            else:
                print(f"❌ No unified reports found")

        except Exception as e:
            print(f"❌ Error processing feedback cycle: {e}")

    elif args.analytics:
        print(f"\n--- Department Health Analytics ---")

        for department in ["legal", "a_and_r", "creative_revenue", "operations"]:
            analytics = feedback_coordinator.health_tracker.get_department_analytics(department)

            if analytics:
                trend_emoji = {"improving": "📈", "stable": "📊", "declining": "📉"}[analytics["trend"]]
                health_emoji = "🟢" if analytics["current_score"] > 0.7 else "🟡" if analytics["current_score"] > 0.5 else "🔴"

                print(f"\n{health_emoji} {department.title()}:")
                print(f"   Score: {analytics['current_score']:.3f} {trend_emoji}")
                print(f"   Trend: {analytics['trend']}")
                print(f"   Range: {analytics['score_range'][0]:.3f} - {analytics['score_range'][1]:.3f}")
                print(f"   Volatility: {analytics['volatility']:.3f}")
                print(f"   Records: {analytics['records_analyzed']}")
            else:
                print(f"\n⚪ {department.title()}: No data available")

    elif args.opportunities:
        print(f"\n--- Optimization Opportunities ---")

        # Get current analytics for opportunity identification
        department_analytics = {}
        for department in ["legal", "a_and_r", "creative_revenue", "operations"]:
            analytics = feedback_coordinator.health_tracker.get_department_analytics(department)
            if analytics:
                department_analytics[department] = analytics

        opportunities = feedback_coordinator.impact_analyzer.identify_optimization_opportunities(department_analytics)

        if opportunities:
            for i, opp in enumerate(opportunities, 1):
                priority_emoji = {"high": "🚨", "medium": "⚠️", "low": "💡"}[opp["priority"]]

                print(f"\n{priority_emoji} Opportunity #{i}: {opp['department'].title()}")
                print(f"   Priority: {opp['priority']}")
                print(f"   Current Score: {opp['current_score']:.3f}")
                print(f"   Target Score: {opp['target_score']:.3f}")
                print(f"   Potential Impact: {opp['estimated_impact']:.3f}")

                print(f"   Recommended Actions:")
                for action in opp['recommended_actions'][:3]:
                    print(f"     • {action}")
        else:
            print("✅ No optimization opportunities identified - all departments healthy!")

    elif args.effectiveness:
        print(f"\n--- Feedback Loop Effectiveness ---")

        effectiveness_history = feedback_coordinator.feedback_model.get("effectiveness_history", [])

        if effectiveness_history:
            recent = effectiveness_history[-5:]  # Last 5 measurements

            print(f"📊 Recent Effectiveness Trend:")
            for measurement in recent:
                timestamp = measurement["timestamp"][:19]  # Remove microseconds
                effectiveness = measurement["effectiveness"]

                effectiveness_emoji = "🟢" if effectiveness > 0.8 else "🟡" if effectiveness > 0.6 else "🔴"
                print(f"   {effectiveness_emoji} {timestamp}: {effectiveness:.3f}")

            if len(recent) >= 2:
                trend = recent[-1]["effectiveness"] - recent[0]["effectiveness"]
                trend_emoji = "📈" if trend > 0.05 else "📉" if trend < -0.05 else "📊"
                print(f"\n{trend_emoji} Effectiveness Trend: {trend:+.3f}")

            current_effectiveness = recent[-1]["effectiveness"]
            print(f"\n🎯 Current Effectiveness: {current_effectiveness:.3f}")

            # Show correlation patterns
            patterns = feedback_coordinator.feedback_model.get("correlation_patterns", {})
            if patterns:
                print(f"\n🔍 Learned Patterns:")
                for department, dept_patterns in patterns.items():
                    correlations = dept_patterns.get("activity_correlations", {})
                    if correlations:
                        print(f"   📋 {department.title()}:")
                        for activity_type, impacts in correlations.items():
                            if impacts:
                                avg_impact = statistics.mean(impacts)
                                print(f"      • {activity_type}: {avg_impact:.3f} avg impact")
        else:
            print("📊 No effectiveness data available yet")

    else:
        print(f"\n--- Quick Status ---")

        # Show recent effectiveness
        effectiveness_history = feedback_coordinator.feedback_model.get("effectiveness_history", [])
        if effectiveness_history:
            current_effectiveness = effectiveness_history[-1]["effectiveness"]
            effectiveness_emoji = "🟢" if current_effectiveness > 0.8 else "🟡" if current_effectiveness > 0.6 else "🔴"
            print(f"🎯 Current Effectiveness: {effectiveness_emoji} {current_effectiveness:.3f}")
        else:
            print(f"🎯 Current Effectiveness: ⚪ No data")

        # Show learning progress
        cycles = feedback_coordinator.feedback_model["learning_cycles"]
        print(f"🧠 Learning Cycles: {cycles}")

        # Quick department status
        health_summary = []
        for department in ["legal", "a_and_r", "creative_revenue", "operations"]:
            analytics = feedback_coordinator.health_tracker.get_department_analytics(department)
            if analytics:
                score = analytics["current_score"]
                emoji = "🟢" if score > 0.7 else "🟡" if score > 0.5 else "🔴"
                health_summary.append(f"{emoji} {department[:3]}")
            else:
                health_summary.append(f"⚪ {department[:3]}")

        print(f"🏥 Department Health: {' '.join(health_summary)}")

        print(f"\nAvailable Commands:")
        print(f"   --process-cycle   : Process feedback cycle with latest data")
        print(f"   --analytics       : Show department health analytics")
        print(f"   --opportunities   : Show optimization opportunities")
        print(f"   --effectiveness   : Show feedback loop effectiveness")

    print()


if __name__ == "__main__":
    main()