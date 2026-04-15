"""
phased_rollout_manager.py — Configuration system for phased platform rollout and feature management.
Enables gradual deployment as credentials become available and controlled feature rollouts.
Created by: Dex - Community Agent (APU-168)
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))
from vawn_config import load_json, save_json, VAWN_DIR, RESEARCH_DIR

# Import platform types
sys.path.insert(0, str(Path(__file__).parent))
from engagement_monitor_apu168 import PlatformStatus, HealthLevel, PLATFORM_CONFIGS

logger = logging.getLogger(__name__)

class RolloutPhase(Enum):
    """Phases of platform rollout."""
    DISABLED = "disabled"           # Platform intentionally disabled
    PLANNING = "planning"           # Planning phase, not yet started
    CREDENTIALS = "credentials"     # Waiting for credentials setup
    TESTING = "testing"            # Testing phase with limited functionality
    PILOT = "pilot"                # Limited rollout to test functionality
    PRODUCTION = "production"      # Full production rollout
    MAINTENANCE = "maintenance"    # Temporary maintenance mode
    SUNSET = "sunset"              # Being phased out

class FeatureFlag(Enum):
    """Feature flags for controlling functionality."""
    MONITORING = "monitoring"                    # Basic comment monitoring
    RESPONSE_GENERATION = "response_generation"  # AI-powered response generation
    AUTO_POSTING = "auto_posting"               # Automatic response posting
    ANALYTICS = "analytics"                     # Advanced analytics and reporting
    ALERTS = "alerts"                          # Real-time alerting
    DASHBOARD = "dashboard"                    # Web dashboard access

@dataclass
class PlatformRolloutConfig:
    """Configuration for individual platform rollout."""
    platform: str
    phase: RolloutPhase = RolloutPhase.DISABLED
    enabled_features: List[FeatureFlag] = None
    rollout_started: Optional[str] = None
    rollout_completed: Optional[str] = None
    target_completion: Optional[str] = None
    prerequisites: List[str] = None
    success_criteria: Dict[str, Any] = None
    rollback_triggers: List[str] = None
    notes: str = ""

    def __post_init__(self):
        if self.enabled_features is None:
            self.enabled_features = []
        if self.prerequisites is None:
            self.prerequisites = ["credentials_configured"]
        if self.success_criteria is None:
            self.success_criteria = {
                "health_score_threshold": 0.7,
                "error_rate_threshold": 0.05,
                "uptime_threshold": 0.95
            }
        if self.rollback_triggers is None:
            self.rollback_triggers = [
                "health_score_below_0.3",
                "error_rate_above_0.2",
                "consecutive_failures_5+"
            ]

@dataclass
class RolloutPlan:
    """Overall rollout plan across all platforms."""
    plan_name: str
    created: str
    target_completion: str
    phases: Dict[str, List[str]]  # phase -> platforms
    feature_dependencies: Dict[str, List[str]]  # feature -> required features
    global_prerequisites: List[str]
    success_metrics: Dict[str, float]
    current_phase: str = "planning"
    status: str = "active"  # active, paused, completed, cancelled

class PhasedRolloutManager:
    """Manages phased rollout of platforms and features."""

    def __init__(self):
        self.config_dir = VAWN_DIR / "config"
        self.config_dir.mkdir(exist_ok=True)

        self.rollout_config_file = self.config_dir / "platform_rollout_config.json"
        self.rollout_plans_file = self.config_dir / "rollout_plans.json"
        self.rollout_log_file = RESEARCH_DIR / "apu168_rollout_log.json"

        # Load configurations
        self.platform_configs = self._load_platform_configs()
        self.rollout_plans = self._load_rollout_plans()
        self.current_plan = None

        # Initialize default configurations if needed
        if not self.platform_configs:
            self._create_default_platform_configs()

    def _load_platform_configs(self) -> Dict[str, PlatformRolloutConfig]:
        """Load platform rollout configurations."""
        try:
            if self.rollout_config_file.exists():
                data = load_json(self.rollout_config_file)
                configs = {}
                for platform, config_data in data.items():
                    # Convert strings back to enums
                    config_data["phase"] = RolloutPhase(config_data["phase"])
                    config_data["enabled_features"] = [
                        FeatureFlag(f) for f in config_data.get("enabled_features", [])
                    ]
                    configs[platform] = PlatformRolloutConfig(**config_data)
                return configs
            else:
                return {}
        except Exception as e:
            logger.error(f"Error loading platform configs: {str(e)}")
            return {}

    def _load_rollout_plans(self) -> Dict[str, RolloutPlan]:
        """Load rollout plans."""
        try:
            if self.rollout_plans_file.exists():
                data = load_json(self.rollout_plans_file)
                plans = {}
                for plan_name, plan_data in data.items():
                    plans[plan_name] = RolloutPlan(**plan_data)
                return plans
            else:
                return {}
        except Exception as e:
            logger.error(f"Error loading rollout plans: {str(e)}")
            return {}

    def _save_platform_configs(self) -> None:
        """Save platform rollout configurations."""
        try:
            data = {}
            for platform, config in self.platform_configs.items():
                config_dict = asdict(config)
                # Convert enums to strings for JSON serialization
                config_dict["phase"] = config.phase.value
                config_dict["enabled_features"] = [f.value for f in config.enabled_features]
                data[platform] = config_dict

            save_json(self.rollout_config_file, data)
        except Exception as e:
            logger.error(f"Error saving platform configs: {str(e)}")

    def _save_rollout_plans(self) -> None:
        """Save rollout plans."""
        try:
            data = {name: asdict(plan) for name, plan in self.rollout_plans.items()}
            save_json(self.rollout_plans_file, data)
        except Exception as e:
            logger.error(f"Error saving rollout plans: {str(e)}")

    def _create_default_platform_configs(self) -> None:
        """Create default platform configurations."""
        for platform_name in PLATFORM_CONFIGS.keys():
            self.platform_configs[platform_name] = PlatformRolloutConfig(
                platform=platform_name,
                phase=RolloutPhase.CREDENTIALS,
                enabled_features=[FeatureFlag.MONITORING],
                prerequisites=[
                    "credentials_configured",
                    "api_connectivity_verified"
                ],
                success_criteria={
                    "health_score_threshold": 0.7,
                    "error_rate_threshold": 0.1,
                    "uptime_threshold": 0.9,
                    "response_time_threshold": 5000
                },
                rollback_triggers=[
                    "health_score_below_0.3",
                    "error_rate_above_0.3",
                    "uptime_below_0.7"
                ],
                notes=f"Default configuration for {platform_name}"
            )

        self._save_platform_configs()

    def create_rollout_plan(self, plan_name: str, target_completion_days: int = 30) -> RolloutPlan:
        """Create a new rollout plan."""
        target_date = (datetime.now() + timedelta(days=target_completion_days)).isoformat()

        # Default phased rollout strategy
        phases = {
            "phase_1_pilot": ["bluesky"],  # Start with most reliable platform
            "phase_2_social": ["instagram", "threads"],  # Meta platforms together
            "phase_3_micro": ["x", "tiktok"],  # Short-form content platforms
            "phase_4_optimization": []  # Full optimization phase
        }

        feature_dependencies = {
            FeatureFlag.RESPONSE_GENERATION.value: [FeatureFlag.MONITORING.value],
            FeatureFlag.AUTO_POSTING.value: [FeatureFlag.RESPONSE_GENERATION.value],
            FeatureFlag.ANALYTICS.value: [FeatureFlag.MONITORING.value],
            FeatureFlag.ALERTS.value: [FeatureFlag.MONITORING.value, FeatureFlag.ANALYTICS.value],
            FeatureFlag.DASHBOARD.value: [FeatureFlag.ANALYTICS.value]
        }

        plan = RolloutPlan(
            plan_name=plan_name,
            created=datetime.now().isoformat(),
            target_completion=target_date,
            phases=phases,
            feature_dependencies=feature_dependencies,
            global_prerequisites=[
                "enhanced_monitor_deployed",
                "health_monitor_active",
                "error_handling_tested"
            ],
            success_metrics={
                "overall_health_score": 0.8,
                "platform_success_rate": 0.9,
                "feature_adoption_rate": 0.7
            },
            current_phase="phase_1_pilot",
            status="active"
        )

        self.rollout_plans[plan_name] = plan
        self.current_plan = plan
        self._save_rollout_plans()

        logger.info(f"Created rollout plan: {plan_name}")
        return plan

    def update_platform_phase(self, platform: str, new_phase: RolloutPhase, notes: str = "") -> bool:
        """Update platform phase with validation."""
        if platform not in self.platform_configs:
            logger.error(f"Platform {platform} not found")
            return False

        config = self.platform_configs[platform]
        old_phase = config.phase

        # Validate phase transition
        if not self._validate_phase_transition(config, new_phase):
            logger.error(f"Invalid phase transition for {platform}: {old_phase.value} -> {new_phase.value}")
            return False

        # Update configuration
        config.phase = new_phase
        if notes:
            config.notes = notes

        # Update timestamps
        if new_phase != RolloutPhase.DISABLED and not config.rollout_started:
            config.rollout_started = datetime.now().isoformat()

        if new_phase == RolloutPhase.PRODUCTION:
            config.rollout_completed = datetime.now().isoformat()

        # Log phase change
        self._log_phase_change(platform, old_phase, new_phase, notes)

        # Save changes
        self._save_platform_configs()

        logger.info(f"Updated {platform} phase: {old_phase.value} -> {new_phase.value}")
        return True

    def _validate_phase_transition(self, config: PlatformRolloutConfig, new_phase: RolloutPhase) -> bool:
        """Validate if phase transition is allowed."""
        current_phase = config.phase

        # Define valid transitions
        valid_transitions = {
            RolloutPhase.DISABLED: [RolloutPhase.PLANNING, RolloutPhase.CREDENTIALS],
            RolloutPhase.PLANNING: [RolloutPhase.CREDENTIALS, RolloutPhase.DISABLED],
            RolloutPhase.CREDENTIALS: [RolloutPhase.TESTING, RolloutPhase.PLANNING, RolloutPhase.DISABLED],
            RolloutPhase.TESTING: [RolloutPhase.PILOT, RolloutPhase.CREDENTIALS, RolloutPhase.DISABLED],
            RolloutPhase.PILOT: [RolloutPhase.PRODUCTION, RolloutPhase.TESTING, RolloutPhase.MAINTENANCE],
            RolloutPhase.PRODUCTION: [RolloutPhase.MAINTENANCE, RolloutPhase.SUNSET],
            RolloutPhase.MAINTENANCE: [RolloutPhase.PRODUCTION, RolloutPhase.TESTING, RolloutPhase.DISABLED],
            RolloutPhase.SUNSET: [RolloutPhase.DISABLED]
        }

        allowed = valid_transitions.get(current_phase, [])
        return new_phase in allowed

    def enable_feature(self, platform: str, feature: FeatureFlag) -> bool:
        """Enable a feature for a platform."""
        if platform not in self.platform_configs:
            return False

        config = self.platform_configs[platform]

        # Check if feature is already enabled
        if feature in config.enabled_features:
            return True

        # Check feature dependencies
        dependencies = self._get_feature_dependencies(feature)
        for dep in dependencies:
            if dep not in config.enabled_features:
                logger.error(f"Cannot enable {feature.value} for {platform}: missing dependency {dep.value}")
                return False

        # Check if platform phase supports this feature
        if not self._feature_allowed_in_phase(feature, config.phase):
            logger.error(f"Cannot enable {feature.value} for {platform}: not allowed in phase {config.phase.value}")
            return False

        # Enable the feature
        config.enabled_features.append(feature)
        self._log_feature_change(platform, feature, "enabled")
        self._save_platform_configs()

        logger.info(f"Enabled {feature.value} for {platform}")
        return True

    def disable_feature(self, platform: str, feature: FeatureFlag) -> bool:
        """Disable a feature for a platform."""
        if platform not in self.platform_configs:
            return False

        config = self.platform_configs[platform]

        if feature not in config.enabled_features:
            return True

        # Check if other features depend on this one
        dependents = self._get_feature_dependents(platform, feature)
        if dependents:
            logger.error(f"Cannot disable {feature.value} for {platform}: required by {[f.value for f in dependents]}")
            return False

        # Disable the feature
        config.enabled_features.remove(feature)
        self._log_feature_change(platform, feature, "disabled")
        self._save_platform_configs()

        logger.info(f"Disabled {feature.value} for {platform}")
        return True

    def _get_feature_dependencies(self, feature: FeatureFlag) -> List[FeatureFlag]:
        """Get dependencies for a feature."""
        dependencies = {
            FeatureFlag.MONITORING: [],
            FeatureFlag.RESPONSE_GENERATION: [FeatureFlag.MONITORING],
            FeatureFlag.AUTO_POSTING: [FeatureFlag.MONITORING, FeatureFlag.RESPONSE_GENERATION],
            FeatureFlag.ANALYTICS: [FeatureFlag.MONITORING],
            FeatureFlag.ALERTS: [FeatureFlag.MONITORING, FeatureFlag.ANALYTICS],
            FeatureFlag.DASHBOARD: [FeatureFlag.MONITORING, FeatureFlag.ANALYTICS]
        }
        return dependencies.get(feature, [])

    def _get_feature_dependents(self, platform: str, feature: FeatureFlag) -> List[FeatureFlag]:
        """Get features that depend on the given feature."""
        config = self.platform_configs[platform]
        dependents = []

        for enabled_feature in config.enabled_features:
            dependencies = self._get_feature_dependencies(enabled_feature)
            if feature in dependencies:
                dependents.append(enabled_feature)

        return dependents

    def _feature_allowed_in_phase(self, feature: FeatureFlag, phase: RolloutPhase) -> bool:
        """Check if feature is allowed in the current phase."""
        allowed_features = {
            RolloutPhase.DISABLED: [],
            RolloutPhase.PLANNING: [],
            RolloutPhase.CREDENTIALS: [],
            RolloutPhase.TESTING: [FeatureFlag.MONITORING],
            RolloutPhase.PILOT: [FeatureFlag.MONITORING, FeatureFlag.ANALYTICS, FeatureFlag.ALERTS],
            RolloutPhase.PRODUCTION: list(FeatureFlag),  # All features allowed
            RolloutPhase.MAINTENANCE: [FeatureFlag.MONITORING, FeatureFlag.ALERTS, FeatureFlag.DASHBOARD],
            RolloutPhase.SUNSET: [FeatureFlag.MONITORING, FeatureFlag.DASHBOARD]
        }
        return feature in allowed_features.get(phase, [])

    def _log_phase_change(self, platform: str, old_phase: RolloutPhase, new_phase: RolloutPhase, notes: str) -> None:
        """Log phase change event."""
        self._log_event("phase_change", {
            "platform": platform,
            "old_phase": old_phase.value,
            "new_phase": new_phase.value,
            "notes": notes
        })

    def _log_feature_change(self, platform: str, feature: FeatureFlag, action: str) -> None:
        """Log feature change event."""
        self._log_event("feature_change", {
            "platform": platform,
            "feature": feature.value,
            "action": action
        })

    def _log_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Log rollout event."""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "data": data
            }

            log_data = load_json(self.rollout_log_file) if self.rollout_log_file.exists() else []
            log_data.append(log_entry)

            # Keep only last 1000 entries
            if len(log_data) > 1000:
                log_data = log_data[-1000:]

            save_json(self.rollout_log_file, log_data)

        except Exception as e:
            logger.error(f"Error logging event: {str(e)}")

    def get_platform_status(self, platform: str) -> Optional[Dict[str, Any]]:
        """Get current status of platform rollout."""
        if platform not in self.platform_configs:
            return None

        config = self.platform_configs[platform]

        return {
            "platform": platform,
            "phase": config.phase.value,
            "enabled_features": [f.value for f in config.enabled_features],
            "rollout_started": config.rollout_started,
            "rollout_completed": config.rollout_completed,
            "target_completion": config.target_completion,
            "prerequisites": config.prerequisites,
            "success_criteria": config.success_criteria,
            "rollback_triggers": config.rollback_triggers,
            "notes": config.notes
        }

    def get_rollout_summary(self) -> Dict[str, Any]:
        """Get summary of current rollout status."""
        phase_counts = {}
        feature_counts = {}
        total_platforms = len(self.platform_configs)

        for config in self.platform_configs.values():
            # Count phases
            phase = config.phase.value
            phase_counts[phase] = phase_counts.get(phase, 0) + 1

            # Count features
            for feature in config.enabled_features:
                feature_name = feature.value
                feature_counts[feature_name] = feature_counts.get(feature_name, 0) + 1

        return {
            "timestamp": datetime.now().isoformat(),
            "total_platforms": total_platforms,
            "phase_distribution": phase_counts,
            "feature_adoption": feature_counts,
            "current_plan": self.current_plan.plan_name if self.current_plan else None,
            "platforms": {name: self.get_platform_status(name) for name in self.platform_configs.keys()}
        }

    def display_rollout_dashboard(self) -> None:
        """Display rollout status dashboard."""
        summary = self.get_rollout_summary()

        print("=" * 80)
        print("🚀 PHASED ROLLOUT DASHBOARD (APU-168)")
        print("=" * 80)

        # Current plan
        if self.current_plan:
            print(f"\n📋 CURRENT PLAN: {self.current_plan.plan_name}")
            print(f"   Status: {self.current_plan.status}")
            print(f"   Current Phase: {self.current_plan.current_phase}")
            print(f"   Target Completion: {self.current_plan.target_completion}")

        # Phase distribution
        print(f"\n📊 PHASE DISTRIBUTION")
        for phase, count in summary["phase_distribution"].items():
            percentage = (count / summary["total_platforms"]) * 100
            print(f"   {phase.upper()}: {count} platforms ({percentage:.1f}%)")

        # Feature adoption
        print(f"\n🎯 FEATURE ADOPTION")
        for feature, count in summary["feature_adoption"].items():
            percentage = (count / summary["total_platforms"]) * 100
            print(f"   {feature.upper()}: {count} platforms ({percentage:.1f}%)")

        # Platform details
        print(f"\n🌐 PLATFORM STATUS")
        for platform_name, status in summary["platforms"].items():
            phase_icon = {
                "disabled": "⏹️",
                "planning": "📝",
                "credentials": "🔑",
                "testing": "🧪",
                "pilot": "🚁",
                "production": "✅",
                "maintenance": "🔧",
                "sunset": "🌅"
            }.get(status["phase"], "❓")

            features_count = len(status["enabled_features"])
            print(f"   {phase_icon} {platform_name.upper()}: {status['phase']} ({features_count} features)")

        print(f"\n" + "=" * 80)
        print(f"Rollout dashboard updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

def main():
    """Main execution function for phased rollout management."""
    print(f"Starting APU-168 Phased Rollout Manager at {datetime.now()}")

    try:
        manager = PhasedRolloutManager()

        # Create default rollout plan if none exists
        if not manager.rollout_plans:
            plan = manager.create_rollout_plan("apu168_initial_rollout", target_completion_days=45)
            print(f"Created initial rollout plan: {plan.plan_name}")

        # Display dashboard
        manager.display_rollout_dashboard()

        print(f"\nPhased rollout management completed successfully")

    except Exception as e:
        error_msg = f"Error in phased rollout manager: {str(e)}"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        raise

if __name__ == "__main__":
    main()