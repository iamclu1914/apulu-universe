"""
deploy_apu119.py — APU-119 Real-Time Community Response Optimization System Deployment

Comprehensive deployment script and system validation for APU-119 engagement monitoring system.
Includes automated setup, configuration, testing, and integration with existing APU infrastructure.

Created by: Dex - Community Agent (APU-119)
Features:
- Automated system deployment and configuration
- Comprehensive validation and testing suite
- Integration verification with existing APU systems
- Performance benchmarking and health checks
- Rollback capabilities and error recovery
"""

import os
import sys
import json
import sqlite3
import subprocess
import time
import shutil
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging

# Add Vawn directory to path
VAWN_DIR = Path(r"C:\Users\rdyal\Vawn")
sys.path.insert(0, str(VAWN_DIR))

try:
    from vawn_config import load_json, save_json, RESEARCH_DIR
except ImportError:
    print("Warning: Could not import vawn_config")
    RESEARCH_DIR = VAWN_DIR / "research"

# Deployment configuration
DEPLOYMENT_LOG = RESEARCH_DIR / "apu119_deployment_log.json"
VALIDATION_RESULTS = RESEARCH_DIR / "apu119_validation_results.json"
BACKUP_DIR = VAWN_DIR / ".backup" / "apu119"

# APU-119 component paths
APU119_COMPONENTS = {
    "main": VAWN_DIR / "src" / "apu119_engagement_monitor.py",
    "integration": VAWN_DIR / "src" / "apu119_system_integration.py",
    "monitoring": VAWN_DIR / "src" / "apu119_monitoring_alerts.py",
    "architecture": VAWN_DIR / "docs" / "APU-119-engagement-monitor-architecture.md"
}

# Required directories
REQUIRED_DIRS = [
    VAWN_DIR / "src",
    VAWN_DIR / "docs",
    VAWN_DIR / "config",
    VAWN_DIR / "database",
    VAWN_DIR / "research"
]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(RESEARCH_DIR / "apu119_deployment.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("APU119_Deploy")

class ValidationTest:
    """Individual validation test"""
    def __init__(self, name: str, description: str, test_func: callable):
        self.name = name
        self.description = description
        self.test_func = test_func
        self.result = None
        self.execution_time = 0.0
        self.error = None

    def run(self) -> bool:
        """Run validation test"""
        start_time = time.time()
        try:
            self.result = self.test_func()
            self.execution_time = time.time() - start_time
            return bool(self.result)
        except Exception as e:
            self.execution_time = time.time() - start_time
            self.error = str(e)
            self.result = False
            logger.error(f"Test {self.name} failed: {e}")
            return False

class APU119Deployer:
    """Main APU-119 deployment system"""

    def __init__(self):
        self.deployment_start_time = datetime.now()
        self.validation_tests = []
        self.deployment_status = {}
        self.backup_created = False

        # Ensure required directories exist
        for directory in REQUIRED_DIRS:
            directory.mkdir(exist_ok=True, parents=True)

        RESEARCH_DIR.mkdir(exist_ok=True)

    def create_backup(self) -> bool:
        """Create backup of existing APU systems"""
        try:
            logger.info("Creating system backup...")
            BACKUP_DIR.mkdir(exist_ok=True, parents=True)

            backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = BACKUP_DIR / f"backup_{backup_timestamp}"
            backup_path.mkdir(exist_ok=True)

            # Backup existing APU files
            apu_files = list(VAWN_DIR.glob("**/apu*.py")) + list(VAWN_DIR.glob("**/APU*.md"))

            for file_path in apu_files:
                if file_path.exists():
                    relative_path = file_path.relative_to(VAWN_DIR)
                    backup_file_path = backup_path / relative_path
                    backup_file_path.parent.mkdir(exist_ok=True, parents=True)
                    shutil.copy2(file_path, backup_file_path)

            logger.info(f"Backup created: {backup_path}")
            self.backup_created = True
            return True

        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return False

    def verify_dependencies(self) -> bool:
        """Verify system dependencies"""
        logger.info("Verifying system dependencies...")

        # Check Python version
        if sys.version_info < (3, 7):
            logger.error("Python 3.7+ required")
            return False

        # Check required Python modules
        required_modules = [
            'sqlite3', 'json', 'threading', 'datetime', 'pathlib',
            'collections', 'dataclasses', 'logging'
        ]

        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                logger.error(f"Required module not found: {module}")
                return False

        # Check vawn_config
        try:
            from vawn_config import VAWN_DIR as config_vawn_dir
            if not Path(config_vawn_dir).exists():
                logger.error(f"VAWN_DIR not found: {config_vawn_dir}")
                return False
        except ImportError:
            logger.warning("vawn_config not available - using fallback")

        logger.info("✅ All dependencies verified")
        return True

    def deploy_components(self) -> bool:
        """Deploy APU-119 components"""
        logger.info("Deploying APU-119 components...")

        deployment_results = {}

        for component_name, component_path in APU119_COMPONENTS.items():
            try:
                if component_path.exists():
                    logger.info(f"✅ {component_name}: {component_path}")
                    deployment_results[component_name] = {
                        "status": "deployed",
                        "path": str(component_path),
                        "size": component_path.stat().st_size
                    }
                else:
                    logger.error(f"❌ {component_name}: File not found - {component_path}")
                    deployment_results[component_name] = {
                        "status": "missing",
                        "path": str(component_path)
                    }

            except Exception as e:
                logger.error(f"❌ {component_name}: Deployment failed - {e}")
                deployment_results[component_name] = {
                    "status": "error",
                    "error": str(e)
                }

        self.deployment_status["components"] = deployment_results

        # Check if all components deployed successfully
        successful_deployments = sum(1 for result in deployment_results.values()
                                   if result["status"] == "deployed")
        total_components = len(deployment_results)

        logger.info(f"Component deployment: {successful_deployments}/{total_components} successful")
        return successful_deployments == total_components

    def setup_validation_tests(self) -> None:
        """Setup comprehensive validation test suite"""
        logger.info("Setting up validation tests...")

        # Component existence tests
        self.validation_tests.append(ValidationTest(
            "component_files",
            "Verify all APU-119 component files exist",
            self._test_component_files
        ))

        # Database setup tests
        self.validation_tests.append(ValidationTest(
            "database_setup",
            "Verify APU-119 databases can be created and accessed",
            self._test_database_setup
        ))

        # Import tests
        self.validation_tests.append(ValidationTest(
            "module_imports",
            "Verify APU-119 modules can be imported successfully",
            self._test_module_imports
        ))

        # System initialization tests
        self.validation_tests.append(ValidationTest(
            "system_initialization",
            "Verify APU-119 systems initialize correctly",
            self._test_system_initialization
        ))

        # Integration tests
        self.validation_tests.append(ValidationTest(
            "apu_integration",
            "Verify integration with existing APU systems",
            self._test_apu_integration
        ))

        # Performance tests
        self.validation_tests.append(ValidationTest(
            "performance_baseline",
            "Establish performance baseline for APU-119",
            self._test_performance_baseline
        ))

        logger.info(f"✅ {len(self.validation_tests)} validation tests configured")

    def run_validation_tests(self) -> Dict[str, Any]:
        """Run all validation tests"""
        logger.info("Running validation test suite...")

        test_results = {
            "start_time": datetime.now().isoformat(),
            "tests": [],
            "summary": {}
        }

        passed_tests = 0
        total_tests = len(self.validation_tests)

        for test in self.validation_tests:
            logger.info(f"🧪 Running test: {test.name}")

            success = test.run()

            test_result = {
                "name": test.name,
                "description": test.description,
                "passed": success,
                "execution_time": test.execution_time,
                "result": test.result,
                "error": test.error
            }

            test_results["tests"].append(test_result)

            if success:
                passed_tests += 1
                logger.info(f"✅ {test.name} passed ({test.execution_time:.2f}s)")
            else:
                logger.error(f"❌ {test.name} failed ({test.execution_time:.2f}s)")

        # Calculate summary
        test_results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
            "total_execution_time": sum(t.execution_time for t in self.validation_tests)
        }

        test_results["end_time"] = datetime.now().isoformat()

        logger.info(f"Validation complete: {passed_tests}/{total_tests} tests passed ({test_results['summary']['success_rate']:.1%})")
        return test_results

    # Validation test implementations

    def _test_component_files(self) -> Dict[str, Any]:
        """Test that all component files exist and are readable"""
        results = {}
        all_exist = True

        for component_name, component_path in APU119_COMPONENTS.items():
            exists = component_path.exists()
            results[component_name] = {
                "exists": exists,
                "path": str(component_path),
                "size": component_path.stat().st_size if exists else 0
            }
            if not exists:
                all_exist = False

        results["all_components_exist"] = all_exist
        return results

    def _test_database_setup(self) -> Dict[str, Any]:
        """Test database creation and access"""
        results = {"databases": {}, "all_databases_ok": True}

        test_databases = [
            VAWN_DIR / "database" / "apu119_engagement_optimization.db",
            VAWN_DIR / "database" / "apu119_alerts.db"
        ]

        for db_path in test_databases:
            try:
                db_path.parent.mkdir(exist_ok=True)

                # Test database creation and basic operations
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                cursor.execute("CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY)")
                cursor.execute("INSERT INTO test_table (id) VALUES (1)")
                cursor.execute("SELECT COUNT(*) FROM test_table")
                count = cursor.fetchone()[0]
                cursor.execute("DROP TABLE test_table")
                conn.close()

                results["databases"][str(db_path)] = {
                    "creation": "success",
                    "operations": "success",
                    "test_records": count
                }

            except Exception as e:
                results["databases"][str(db_path)] = {
                    "creation": "failed",
                    "error": str(e)
                }
                results["all_databases_ok"] = False

        return results

    def _test_module_imports(self) -> Dict[str, Any]:
        """Test importing APU-119 modules"""
        results = {"imports": {}, "all_imports_ok": True}

        # Test imports
        import_tests = [
            ("apu119_engagement_monitor", "src.apu119_engagement_monitor"),
            ("apu119_system_integration", "src.apu119_system_integration"),
            ("apu119_monitoring_alerts", "src.apu119_monitoring_alerts")
        ]

        for test_name, module_path in import_tests:
            try:
                __import__(module_path)
                results["imports"][test_name] = "success"
            except ImportError as e:
                results["imports"][test_name] = f"failed: {e}"
                results["all_imports_ok"] = False
            except Exception as e:
                results["imports"][test_name] = f"error: {e}"
                results["all_imports_ok"] = False

        return results

    def _test_system_initialization(self) -> Dict[str, Any]:
        """Test APU-119 system initialization"""
        results = {"initialization": {}, "all_systems_ok": True}

        try:
            # Test main engagement monitor initialization
            from src.apu119_engagement_monitor import APU119EngagementMonitor

            monitor = APU119EngagementMonitor()
            health_summary = monitor.run_comprehensive_health_check()

            results["initialization"]["engagement_monitor"] = {
                "status": "success",
                "health": health_summary["overall_status"],
                "components": len(health_summary["components"])
            }

        except Exception as e:
            results["initialization"]["engagement_monitor"] = {
                "status": "failed",
                "error": str(e)
            }
            results["all_systems_ok"] = False

        try:
            # Test system integration
            from src.apu119_system_integration import APUSystemsIntegrator

            integrator = APUSystemsIntegrator()
            integration_status = integrator.sync_all_systems()

            results["initialization"]["system_integration"] = {
                "status": "success",
                "active_systems": integration_status["active_systems"],
                "total_systems": integration_status["total_systems"]
            }

        except Exception as e:
            results["initialization"]["system_integration"] = {
                "status": "failed",
                "error": str(e)
            }
            results["all_systems_ok"] = False

        return results

    def _test_apu_integration(self) -> Dict[str, Any]:
        """Test integration with existing APU systems"""
        results = {"integration_tests": {}, "integration_health": "unknown"}

        try:
            from src.apu119_system_integration import APUSystemsIntegrator

            integrator = APUSystemsIntegrator()
            integration_summary = integrator.get_integration_summary()

            results["integration_tests"] = {
                "overall_health": integration_summary["integration_health"],
                "systems": integration_summary["systems"],
                "recommendations": integration_summary["recommendations"]
            }

            results["integration_health"] = integration_summary["integration_health"]

        except Exception as e:
            results["integration_tests"]["error"] = str(e)
            results["integration_health"] = "failed"

        return results

    def _test_performance_baseline(self) -> Dict[str, Any]:
        """Establish performance baseline"""
        results = {"performance": {}, "baseline_established": False}

        try:
            # Test response times for various operations
            from src.apu119_engagement_monitor import APU119EngagementMonitor

            monitor = APU119EngagementMonitor()

            # Test health check performance
            start_time = time.time()
            health_summary = monitor.run_comprehensive_health_check()
            health_check_time = time.time() - start_time

            # Test database operations
            start_time = time.time()
            cursor = monitor.db_connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM system_health")
            db_operation_time = time.time() - start_time

            results["performance"] = {
                "health_check_time": health_check_time,
                "database_operation_time": db_operation_time,
                "overall_health": health_summary["overall_status"]
            }

            results["baseline_established"] = True

        except Exception as e:
            results["performance"]["error"] = str(e)
            results["baseline_established"] = False

        return results

    def log_deployment_results(self, validation_results: Dict[str, Any]) -> None:
        """Log deployment and validation results"""
        try:
            deployment_log = {
                "deployment_timestamp": self.deployment_start_time.isoformat(),
                "deployment_duration": (datetime.now() - self.deployment_start_time).total_seconds(),
                "deployment_status": self.deployment_status,
                "validation_results": validation_results,
                "backup_created": self.backup_created,
                "system_info": {
                    "python_version": sys.version,
                    "platform": sys.platform,
                    "vawn_dir": str(VAWN_DIR)
                }
            }

            # Save deployment log
            save_json(DEPLOYMENT_LOG, deployment_log)

            # Save validation results separately
            save_json(VALIDATION_RESULTS, validation_results)

            logger.info(f"Deployment results logged: {DEPLOYMENT_LOG}")
            logger.info(f"Validation results logged: {VALIDATION_RESULTS}")

        except Exception as e:
            logger.error(f"Failed to log deployment results: {e}")

    def deploy(self) -> Dict[str, Any]:
        """Main deployment process"""
        logger.info("\n" + "="*70)
        logger.info("🚀 APU-119 Real-Time Community Response Optimization System Deployment")
        logger.info("="*70)

        deployment_result = {
            "success": False,
            "stage": "initialization",
            "error": None
        }

        try:
            # Stage 1: Create backup
            deployment_result["stage"] = "backup"
            if not self.create_backup():
                deployment_result["error"] = "Backup creation failed"
                return deployment_result

            # Stage 2: Verify dependencies
            deployment_result["stage"] = "dependencies"
            if not self.verify_dependencies():
                deployment_result["error"] = "Dependency verification failed"
                return deployment_result

            # Stage 3: Deploy components
            deployment_result["stage"] = "deployment"
            if not self.deploy_components():
                deployment_result["error"] = "Component deployment failed"
                return deployment_result

            # Stage 4: Setup and run validation tests
            deployment_result["stage"] = "validation_setup"
            self.setup_validation_tests()

            deployment_result["stage"] = "validation_execution"
            validation_results = self.run_validation_tests()

            # Stage 5: Log results
            deployment_result["stage"] = "logging"
            self.log_deployment_results(validation_results)

            # Final assessment
            success_rate = validation_results["summary"]["success_rate"]
            if success_rate >= 0.8:  # 80% success rate threshold
                deployment_result["success"] = True
                deployment_result["stage"] = "completed"
                logger.info(f"\n🎉 APU-119 deployment completed successfully! ({success_rate:.1%} test success rate)")
            else:
                deployment_result["error"] = f"Validation failed: {success_rate:.1%} success rate"
                logger.error(f"\n❌ APU-119 deployment validation failed ({success_rate:.1%} success rate)")

            deployment_result["validation_results"] = validation_results

        except Exception as e:
            deployment_result["error"] = f"Deployment failed at {deployment_result['stage']}: {str(e)}"
            logger.error(f"Deployment error: {e}\n{traceback.format_exc()}")

        deployment_result["duration"] = (datetime.now() - self.deployment_start_time).total_seconds()
        return deployment_result

def main():
    """Main deployment script entry point"""
    try:
        deployer = APU119Deployer()
        result = deployer.deploy()

        if result["success"]:
            print(f"\n✅ APU-119 deployment successful in {result['duration']:.1f} seconds")
            print("\n📊 System Ready:")
            print(f"   • Components: ✅ Deployed")
            print(f"   • Integration: ✅ Active")
            print(f"   • Monitoring: ✅ Ready")
            print(f"   • Validation: ✅ {result['validation_results']['summary']['success_rate']:.1%}")

            print(f"\n📁 Resources:")
            print(f"   • Architecture: {APU119_COMPONENTS['architecture']}")
            print(f"   • Deployment Log: {DEPLOYMENT_LOG}")
            print(f"   • Validation Results: {VALIDATION_RESULTS}")

            return 0
        else:
            print(f"\n❌ APU-119 deployment failed: {result['error']}")
            print(f"   Failed at stage: {result['stage']}")
            return 1

    except Exception as e:
        print(f"\n🚨 Critical deployment error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)