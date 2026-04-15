#!/usr/bin/env python3
"""
deploy_apu163.py — Production Deployment Script for APU-163
Automated deployment and configuration of APU-163 Advanced Engagement Monitor.

Created by: Dex - Community Agent (APU-163)
Purpose: Deploy APU-163 to production with optimal configuration and monitoring

DEPLOYMENT FEATURES:
[NEW] Automated Production Configuration
[NEW] Database Schema Validation and Migration
[NEW] Paperclip Integration Setup
[NEW] Department Coordination Configuration
[NEW] Self-Healing Strategy Optimization
[NEW] Real-time Monitoring Setup
[NEW] Health Check and Alerting Configuration
[NEW] Performance Optimization
[NEW] Security Configuration
[NEW] Backup and Recovery Setup
"""

import sys
import json
import time
import shutil
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent))

from vawn_config import VAWN_DIR, load_json, save_json, today_str, log_run

# Import APU-163 components
try:
    from src.apu163_engagement_monitor import APU163EngagementMonitor, DepartmentType, AutomationLevel
    from src.apu163_paperclip_integration import APU163PaperclipIntegration, IssueType
    from test_apu163_comprehensive_suite import APU163TestSuite
except ImportError as e:
    print(f"ERROR: Could not import APU-163 components: {e}")
    sys.exit(1)


class APU163ProductionDeployer:
    """Production deployment manager for APU-163."""

    def __init__(self):
        self.deployment_id = f"deploy_apu163_{int(datetime.now().timestamp())}"
        self.start_time = datetime.now()

        # Deployment configuration
        self.production_config = {
            "automation_level": AutomationLevel.AUTOMATED,
            "self_healing_enabled": True,
            "real_time_monitoring": True,
            "paperclip_integration": True,
            "department_coordination": True,
            "ai_features_enabled": True,
            "performance_optimization": True,
            "security_hardening": True,
            "backup_enabled": True,
            "monitoring_interval_seconds": 300,  # 5 minutes
            "health_check_interval_seconds": 60,  # 1 minute
            "log_retention_days": 30,
            "database_backup_interval_hours": 6
        }

        # Setup logging
        self.deployment_log = VAWN_DIR / "research" / f"apu163_deployment_{today_str()}.log"
        self._setup_deployment_logging()

        # Directories
        self.production_dirs = {
            "database": VAWN_DIR / "database",
            "paperclip": VAWN_DIR / "paperclip",
            "research": VAWN_DIR / "research",
            "logs": VAWN_DIR / "research" / "apu163_logs",
            "backups": VAWN_DIR / "backups" / "apu163",
            "config": VAWN_DIR / "config" / "apu163"
        }

        print(f"[DEPLOY] APU-163 Production Deployment Initiated")
        print(f"[DEPLOY] Deployment ID: {self.deployment_id}")
        print(f"[DEPLOY] Started: {self.start_time.isoformat()}")

    def _setup_deployment_logging(self):
        """Setup deployment logging."""
        self.deployment_log.parent.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.deployment_log),
                logging.StreamHandler()
            ]
        )

        self.logger = logging.getLogger("APU163Deployer")

    def run_pre_deployment_tests(self) -> bool:
        """Run pre-deployment validation tests."""
        self.logger.info("Running pre-deployment validation tests...")
        print(f"[DEPLOY] Running pre-deployment validation tests...")

        try:
            # Run comprehensive test suite
            test_suite = APU163TestSuite()
            test_success = test_suite.run_comprehensive_test_suite()

            if not test_success:
                self.logger.error("Pre-deployment tests failed - aborting deployment")
                print(f"[DEPLOY ERROR] Pre-deployment tests failed - deployment aborted")
                return False

            self.logger.info("Pre-deployment tests passed successfully")
            print(f"[DEPLOY] ✅ Pre-deployment validation completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error running pre-deployment tests: {e}")
            print(f"[DEPLOY ERROR] Test execution failed: {e}")
            return False

    def setup_production_directories(self) -> bool:
        """Setup production directory structure."""
        self.logger.info("Setting up production directories...")
        print(f"[DEPLOY] Setting up production directory structure...")

        try:
            for dir_name, dir_path in self.production_dirs.items():
                dir_path.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"Created/verified directory: {dir_path}")

            # Create subdirectories
            subdirs = [
                self.production_dirs["paperclip"] / "tasks",
                self.production_dirs["paperclip"] / "alerts",
                self.production_dirs["paperclip"] / "reports",
                self.production_dirs["logs"] / "health_checks",
                self.production_dirs["logs"] / "self_healing",
                self.production_dirs["logs"] / "department_coordination",
                self.production_dirs["backups"] / "database",
                self.production_dirs["backups"] / "config"
            ]

            for subdir in subdirs:
                subdir.mkdir(parents=True, exist_ok=True)

            self.logger.info(f"Production directories setup completed")
            print(f"[DEPLOY] ✅ Directory structure created successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error setting up directories: {e}")
            print(f"[DEPLOY ERROR] Directory setup failed: {e}")
            return False

    def deploy_production_configuration(self) -> bool:
        """Deploy production configuration files."""
        self.logger.info("Deploying production configuration...")
        print(f"[DEPLOY] Configuring production settings...")

        try:
            # APU-163 production config
            production_config_file = self.production_dirs["config"] / "apu163_production.json"

            config_data = {
                "deployment_id": self.deployment_id,
                "deployed_at": datetime.now().isoformat(),
                "version": "APU-163.1.0",
                "environment": "production",
                "configuration": self.production_config,
                "departments": {
                    dept.value: {
                        "enabled": True,
                        "coordinator": f"{dept.value}_coordinator",
                        "priority_weight": 1.0 / len(DepartmentType),
                        "alert_threshold": 0.3,
                        "escalation_enabled": True
                    }
                    for dept in DepartmentType
                },
                "self_healing_strategies": {
                    "api_timeout": {
                        "enabled": True,
                        "confidence_threshold": 0.8,
                        "max_attempts": 3,
                        "backoff_strategy": "exponential"
                    },
                    "auth_failure": {
                        "enabled": True,
                        "confidence_threshold": 0.9,
                        "max_attempts": 2,
                        "token_refresh_enabled": True
                    },
                    "rate_limit": {
                        "enabled": True,
                        "confidence_threshold": 0.95,
                        "backoff_multiplier": 2.0,
                        "max_backoff_seconds": 300
                    },
                    "infrastructure_degradation": {
                        "enabled": True,
                        "confidence_threshold": 0.7,
                        "fallback_endpoints": True,
                        "health_monitoring": True
                    }
                },
                "paperclip_integration": {
                    "auto_issue_creation": True,
                    "department_routing": True,
                    "escalation_thresholds": {
                        "api_infrastructure": 3,
                        "platform_timeout": 5,
                        "authentication": 2,
                        "engagement_anomaly": 4,
                        "performance_degradation": 3
                    },
                    "resolution_tracking": True,
                    "bi_directional_sync": True
                },
                "monitoring": {
                    "health_check_interval": self.production_config["health_check_interval_seconds"],
                    "monitoring_interval": self.production_config["monitoring_interval_seconds"],
                    "alert_channels": ["paperclip", "log"],
                    "metrics_retention_days": 90,
                    "performance_thresholds": {
                        "max_cycle_duration": 60.0,
                        "max_init_time": 5.0,
                        "max_db_operation_time": 2.0
                    }
                },
                "ai_models": {
                    "engagement_predictor": {
                        "enabled": True,
                        "retrain_interval_days": 7,
                        "confidence_threshold": 0.8
                    },
                    "growth_optimizer": {
                        "enabled": True,
                        "retrain_interval_days": 14,
                        "impact_threshold": 0.1
                    },
                    "anomaly_detector": {
                        "enabled": True,
                        "sensitivity": 0.85,
                        "alert_threshold": 0.9
                    }
                },
                "security": {
                    "api_key_rotation_days": 30,
                    "log_sanitization": True,
                    "access_logging": True,
                    "rate_limiting": True
                }
            }

            save_json(production_config_file, config_data)

            # Create monitoring schedule configuration
            schedule_config_file = self.production_dirs["config"] / "monitoring_schedule.json"
            schedule_data = {
                "schedules": {
                    "continuous_monitoring": {
                        "enabled": True,
                        "interval_seconds": self.production_config["monitoring_interval_seconds"],
                        "command": "python src/apu163_engagement_monitor.py",
                        "restart_on_failure": True,
                        "max_failures": 5
                    },
                    "health_checks": {
                        "enabled": True,
                        "interval_seconds": self.production_config["health_check_interval_seconds"],
                        "command": "python scripts/apu163_health_check.py",
                        "alert_on_failure": True
                    },
                    "database_backup": {
                        "enabled": True,
                        "interval_seconds": self.production_config["database_backup_interval_hours"] * 3600,
                        "command": "python scripts/apu163_backup.py",
                        "retention_days": 7
                    },
                    "log_cleanup": {
                        "enabled": True,
                        "interval_seconds": 24 * 3600,  # Daily
                        "retention_days": self.production_config["log_retention_days"]
                    }
                }
            }

            save_json(schedule_config_file, schedule_data)

            self.logger.info("Production configuration deployed successfully")
            print(f"[DEPLOY] ✅ Production configuration deployed")
            return True

        except Exception as e:
            self.logger.error(f"Error deploying configuration: {e}")
            print(f"[DEPLOY ERROR] Configuration deployment failed: {e}")
            return False

    def initialize_production_database(self) -> bool:
        """Initialize and optimize production database."""
        self.logger.info("Initializing production database...")
        print(f"[DEPLOY] Initializing production database...")

        try:
            # Initialize APU-163 monitor to create database
            monitor = APU163EngagementMonitor()

            # Verify database creation
            if not monitor.db_path.exists():
                raise Exception("Database not created during initialization")

            # Optimize database for production
            with sqlite3.connect(monitor.db_path) as conn:
                cursor = conn.cursor()

                # Create indexes for performance
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_healing_actions_timestamp ON self_healing_actions(timestamp)",
                    "CREATE INDEX IF NOT EXISTS idx_healing_actions_problem_type ON self_healing_actions(problem_type)",
                    "CREATE INDEX IF NOT EXISTS idx_paperclip_issues_status ON paperclip_issues(status)",
                    "CREATE INDEX IF NOT EXISTS idx_paperclip_issues_priority ON paperclip_issues(priority)",
                    "CREATE INDEX IF NOT EXISTS idx_department_engagement_timestamp ON department_engagement(timestamp)",
                    "CREATE INDEX IF NOT EXISTS idx_growth_strategies_timestamp ON growth_strategies(timestamp)"
                ]

                for index_sql in indexes:
                    cursor.execute(index_sql)

                # Set production database settings
                production_settings = [
                    "PRAGMA journal_mode = WAL",  # Write-Ahead Logging for better performance
                    "PRAGMA synchronous = NORMAL",  # Balance safety and performance
                    "PRAGMA cache_size = -64000",  # 64MB cache
                    "PRAGMA temp_store = MEMORY",  # Use memory for temp operations
                    "PRAGMA mmap_size = 268435456"  # 256MB memory map
                ]

                for setting in production_settings:
                    cursor.execute(setting)

                conn.commit()

            # Create database backup
            backup_path = self.production_dirs["backups"] / "database" / f"apu163_initial_{today_str()}.db"
            shutil.copy2(monitor.db_path, backup_path)

            self.logger.info(f"Database initialized and optimized for production")
            self.logger.info(f"Initial backup created: {backup_path}")
            print(f"[DEPLOY] ✅ Database initialized and optimized")
            return True

        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")
            print(f"[DEPLOY ERROR] Database initialization failed: {e}")
            return False

    def setup_monitoring_and_alerting(self) -> bool:
        """Setup production monitoring and alerting."""
        self.logger.info("Setting up monitoring and alerting...")
        print(f"[DEPLOY] Configuring monitoring and alerting...")

        try:
            # Create health check script
            health_check_script = self.production_dirs["config"] / ".." / ".." / "scripts" / "apu163_health_check.py"
            health_check_script.parent.mkdir(parents=True, exist_ok=True)

            health_check_code = '''#!/usr/bin/env python3
"""
APU-163 Health Check Script
Monitors system health and generates alerts for issues.
"""

import sys
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from vawn_config import VAWN_DIR, save_json

def check_database_health():
    """Check database health."""
    db_path = VAWN_DIR / "database" / "apu163_engagement_intelligence.db"

    if not db_path.exists():
        return {"status": "ERROR", "message": "Database not found"}

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]

            if table_count < 4:  # Minimum expected tables
                return {"status": "WARNING", "message": f"Only {table_count} tables found"}

        return {"status": "OK", "message": f"Database healthy with {table_count} tables"}

    except Exception as e:
        return {"status": "ERROR", "message": f"Database error: {e}"}

def check_recent_activity():
    """Check for recent monitoring activity."""
    log_dir = VAWN_DIR / "research"
    recent_files = []

    for log_file in log_dir.glob("apu163_*.json"):
        if log_file.stat().st_mtime > (datetime.now() - timedelta(hours=1)).timestamp():
            recent_files.append(log_file.name)

    if len(recent_files) == 0:
        return {"status": "WARNING", "message": "No recent activity detected"}

    return {"status": "OK", "message": f"Recent activity: {len(recent_files)} files"}

def main():
    health_status = {
        "timestamp": datetime.now().isoformat(),
        "checks": {
            "database": check_database_health(),
            "recent_activity": check_recent_activity()
        }
    }

    # Determine overall status
    check_statuses = [check["status"] for check in health_status["checks"].values()]

    if "ERROR" in check_statuses:
        health_status["overall_status"] = "ERROR"
    elif "WARNING" in check_statuses:
        health_status["overall_status"] = "WARNING"
    else:
        health_status["overall_status"] = "OK"

    # Save health check result
    health_file = VAWN_DIR / "research" / f"apu163_health_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    save_json(health_file, health_status)

    # Print status for logging
    print(f"APU-163 Health: {health_status['overall_status']}")

    return 0 if health_status["overall_status"] == "OK" else 1

if __name__ == "__main__":
    exit(main())
'''

            with open(health_check_script, 'w') as f:
                f.write(health_check_code)

            health_check_script.chmod(0o755)  # Make executable

            # Create backup script
            backup_script = self.production_dirs["config"] / ".." / ".." / "scripts" / "apu163_backup.py"

            backup_code = '''#!/usr/bin/env python3
"""
APU-163 Backup Script
Creates backups of database and configuration files.
"""

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from vawn_config import VAWN_DIR, save_json

def backup_database():
    """Backup APU-163 database."""
    db_path = VAWN_DIR / "database" / "apu163_engagement_intelligence.db"
    backup_dir = VAWN_DIR / "backups" / "apu163" / "database"
    backup_dir.mkdir(parents=True, exist_ok=True)

    if db_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"apu163_db_{timestamp}.db"
        shutil.copy2(db_path, backup_path)
        return str(backup_path)

    return None

def backup_config():
    """Backup configuration files."""
    config_dir = VAWN_DIR / "config" / "apu163"
    backup_dir = VAWN_DIR / "backups" / "apu163" / "config"
    backup_dir.mkdir(parents=True, exist_ok=True)

    backed_up_files = []

    if config_dir.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for config_file in config_dir.glob("*.json"):
            backup_path = backup_dir / f"{config_file.stem}_{timestamp}.json"
            shutil.copy2(config_file, backup_path)
            backed_up_files.append(str(backup_path))

    return backed_up_files

def main():
    backup_result = {
        "timestamp": datetime.now().isoformat(),
        "database_backup": backup_database(),
        "config_backups": backup_config()
    }

    # Save backup log
    log_file = VAWN_DIR / "backups" / "apu163" / f"backup_log_{datetime.now().strftime('%Y%m%d')}.json"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    save_json(log_file, backup_result)

    print(f"APU-163 Backup completed: {backup_result['timestamp']}")
    return 0

if __name__ == "__main__":
    exit(main())
'''

            with open(backup_script, 'w') as f:
                f.write(backup_code)

            backup_script.chmod(0o755)  # Make executable

            self.logger.info("Monitoring and alerting setup completed")
            print(f"[DEPLOY] ✅ Monitoring and alerting configured")
            return True

        except Exception as e:
            self.logger.error(f"Error setting up monitoring: {e}")
            print(f"[DEPLOY ERROR] Monitoring setup failed: {e}")
            return False

    def verify_deployment(self) -> bool:
        """Verify deployment success."""
        self.logger.info("Verifying deployment...")
        print(f"[DEPLOY] Verifying deployment integrity...")

        try:
            verification_results = {
                "directories": {},
                "configuration": {},
                "database": {},
                "integration": {}
            }

            # Verify directories
            for dir_name, dir_path in self.production_dirs.items():
                verification_results["directories"][dir_name] = {
                    "exists": dir_path.exists(),
                    "path": str(dir_path)
                }

            # Verify configuration files
            config_files = [
                "apu163_production.json",
                "monitoring_schedule.json"
            ]

            for config_file in config_files:
                config_path = self.production_dirs["config"] / config_file
                verification_results["configuration"][config_file] = {
                    "exists": config_path.exists(),
                    "size_bytes": config_path.stat().st_size if config_path.exists() else 0
                }

            # Verify database
            db_path = self.production_dirs["database"] / "apu163_engagement_intelligence.db"
            if db_path.exists():
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]

                verification_results["database"] = {
                    "exists": True,
                    "table_count": len(tables),
                    "tables": tables,
                    "size_bytes": db_path.stat().st_size
                }
            else:
                verification_results["database"] = {"exists": False}

            # Verify APU-163 can initialize
            try:
                monitor = APU163EngagementMonitor()
                integration = APU163PaperclipIntegration(monitor)

                verification_results["integration"] = {
                    "monitor_initialization": True,
                    "paperclip_integration": True,
                    "session_id": monitor.session_id,
                    "departments_configured": len(monitor.departments),
                    "healing_strategies": len(monitor.healing_strategies)
                }

            except Exception as e:
                verification_results["integration"] = {
                    "monitor_initialization": False,
                    "error": str(e)
                }

            # Save verification results
            verification_file = self.production_dirs["logs"] / f"deployment_verification_{today_str()}.json"
            save_json(verification_file, verification_results)

            # Check if deployment is successful
            deployment_success = (
                all(dir_info["exists"] for dir_info in verification_results["directories"].values()) and
                all(config_info["exists"] for config_info in verification_results["configuration"].values()) and
                verification_results["database"]["exists"] and
                verification_results["integration"].get("monitor_initialization", False)
            )

            if deployment_success:
                self.logger.info("Deployment verification passed")
                print(f"[DEPLOY] ✅ Deployment verification successful")
            else:
                self.logger.error("Deployment verification failed")
                print(f"[DEPLOY ERROR] Deployment verification failed")

            return deployment_success

        except Exception as e:
            self.logger.error(f"Error during verification: {e}")
            print(f"[DEPLOY ERROR] Verification failed: {e}")
            return False

    def generate_deployment_report(self, success: bool, duration: float) -> Dict[str, Any]:
        """Generate deployment report."""
        report = {
            "deployment_id": self.deployment_id,
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "duration_seconds": duration,
            "version": "APU-163.1.0",
            "configuration": self.production_config,
            "directories_created": list(self.production_dirs.keys()),
            "components_deployed": [
                "APU-163 Engagement Monitor",
                "Paperclip Integration",
                "Self-Healing System",
                "Department Coordination",
                "Growth Strategy Engine",
                "Real-time Monitoring",
                "Health Checks",
                "Automated Backups"
            ],
            "next_steps": [
                "Start continuous monitoring service",
                "Configure alert channels",
                "Monitor initial system performance",
                "Validate department coordination",
                "Review self-healing effectiveness",
                "Schedule regular maintenance"
            ]
        }

        if not success:
            report["failure_reason"] = "Check deployment logs for detailed error information"
            report["recovery_steps"] = [
                "Review deployment logs",
                "Verify system requirements",
                "Check file permissions",
                "Validate configuration",
                "Re-run deployment with fixes"
            ]

        return report

    def deploy_to_production(self) -> bool:
        """Execute complete production deployment."""
        deployment_start = time.time()

        print(f"")
        print(f"🚀 APU-163 PRODUCTION DEPLOYMENT STARTING 🚀")
        print(f"=" * 60)

        deployment_steps = [
            ("Pre-deployment Tests", self.run_pre_deployment_tests),
            ("Directory Setup", self.setup_production_directories),
            ("Configuration Deployment", self.deploy_production_configuration),
            ("Database Initialization", self.initialize_production_database),
            ("Monitoring Setup", self.setup_monitoring_and_alerting),
            ("Deployment Verification", self.verify_deployment)
        ]

        for step_name, step_function in deployment_steps:
            print(f"\n📋 {step_name}...")
            step_start = time.time()

            try:
                step_success = step_function()
                step_duration = time.time() - step_start

                if step_success:
                    print(f"✅ {step_name} completed in {step_duration:.2f}s")
                else:
                    print(f"❌ {step_name} failed after {step_duration:.2f}s")
                    return False

            except Exception as e:
                step_duration = time.time() - step_start
                print(f"❌ {step_name} failed with error after {step_duration:.2f}s: {e}")
                self.logger.error(f"Step '{step_name}' failed: {e}")
                return False

        deployment_duration = time.time() - deployment_start

        # Generate and save deployment report
        report = self.generate_deployment_report(True, deployment_duration)
        report_file = self.production_dirs["logs"] / f"deployment_report_{today_str()}.json"
        save_json(report_file, report)

        print(f"\n🎉 APU-163 PRODUCTION DEPLOYMENT COMPLETE! 🎉")
        print(f"=" * 60)
        print(f"⏱️  Total Duration: {deployment_duration:.2f} seconds")
        print(f"📊 Components Deployed: {len(report['components_deployed'])}")
        print(f"📁 Directories Created: {len(report['directories_created'])}")
        print(f"📋 Deployment Report: {report_file}")

        print(f"\n🔧 Next Steps:")
        for step in report["next_steps"]:
            print(f"   • {step}")

        # Log successful deployment
        log_run("APU163ProductionDeployment", "ok",
               f"Deployed successfully in {deployment_duration:.1f}s with {len(report['components_deployed'])} components")

        return True


def main():
    """Main deployment execution."""
    print("APU-163 Advanced Community Engagement Orchestrator")
    print("Production Deployment Script")
    print("=" * 60)

    deployer = APU163ProductionDeployer()
    success = deployer.deploy_to_production()

    if success:
        print(f"\n🚀 APU-163 is now ready for production monitoring!")
        print(f"🔍 Start monitoring: python src/apu163_engagement_monitor.py")
        return 0
    else:
        print(f"\n❌ Deployment failed. Check logs for details.")
        print(f"📋 Log file: {deployer.deployment_log}")
        return 1


if __name__ == "__main__":
    exit(main())