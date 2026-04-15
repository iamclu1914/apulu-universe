"""
apu123_test_validation.py — APU-123 Test and Validation Suite

Comprehensive testing and validation for APU-123 Community Engagement Quality Optimizer:
- Response quality testing
- Integration validation
- Performance benchmarking
- System reliability testing
- Quality improvement validation

Created by: Dex - Community Agent (APU-123)
Purpose: Ensure APU-123 delivers reliable engagement quality improvements
"""

import json
import sys
import time
import traceback
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import unittest
from unittest.mock import Mock, patch
import logging

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import load_json, save_json, VAWN_DIR, RESEARCH_DIR
from src.apu123_engagement_monitor import APU123EngagementMonitor, ConversationContext, EngagementResponse
from src.apu123_system_integration import APU123SystemIntegration

logger = logging.getLogger("APU123_Testing")

class APU123TestSuite:
    """Comprehensive test suite for APU-123"""

    def __init__(self):
        self.test_results = []
        self.performance_metrics = []
        self.validation_log = RESEARCH_DIR / "apu123_validation_log.json"

        # Test configurations
        self.test_interactions = [
            {
                "platform": "instagram",
                "author": "music_producer_23",
                "content": "Just dropped my first beat! Been working on this track for weeks. The 808s are hitting different on this one. What y'all think?",
                "community_topic": "music_production",
                "expected_quality_min": 0.6
            },
            {
                "platform": "tiktok",
                "author": "aspiring_rapper",
                "content": "Freestyle Friday! Drop a word and I'll make a bar out of it 🎤",
                "community_topic": "freestyle_rap",
                "expected_quality_min": 0.7
            },
            {
                "platform": "x",
                "author": "hip_hop_head",
                "content": "Who's the most underrated producer in hip hop right now? Need some new sounds for my playlist",
                "community_topic": "hip_hop_discussion",
                "expected_quality_min": 0.6
            },
            {
                "platform": "threads",
                "author": "studio_engineer",
                "content": "Pro tip: Always check your mix on different speakers before finalizing. Car speakers tell no lies!",
                "community_topic": "audio_engineering",
                "expected_quality_min": 0.5
            },
            {
                "platform": "bluesky",
                "author": "indie_artist",
                "content": "Sometimes I wonder if I should quit my day job to focus on music full time. The grind is real but the passion is stronger",
                "community_topic": "artist_journey",
                "expected_quality_min": 0.7
            }
        ]

    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run all APU-123 tests and return results"""
        print("🧪 APU-123 Comprehensive Test Suite")
        print("=" * 50)

        test_start_time = time.time()

        # Initialize systems
        monitor = APU123EngagementMonitor()
        integration = APU123SystemIntegration()

        test_results = {
            "timestamp": datetime.now().isoformat(),
            "test_suite_version": "apu123_v1.0",
            "tests": {}
        }

        try:
            # Test 1: Response Quality Testing
            print("1. Testing response quality generation...")
            test_results["tests"]["response_quality"] = self._test_response_quality(monitor)

            # Test 2: Integration Testing
            print("2. Testing system integration...")
            test_results["tests"]["integration"] = self._test_system_integration(integration)

            # Test 3: Performance Testing
            print("3. Testing performance benchmarks...")
            test_results["tests"]["performance"] = self._test_performance(monitor)

            # Test 4: Quality Score Validation
            print("4. Testing quality scoring accuracy...")
            test_results["tests"]["quality_scoring"] = self._test_quality_scoring(monitor)

            # Test 5: Edge Case Testing
            print("5. Testing edge cases...")
            test_results["tests"]["edge_cases"] = self._test_edge_cases(monitor)

            # Test 6: Integration Reliability
            print("6. Testing integration reliability...")
            test_results["tests"]["integration_reliability"] = self._test_integration_reliability(integration)

        except Exception as e:
            test_results["error"] = str(e)
            test_results["traceback"] = traceback.format_exc()
            logger.error(f"Test suite error: {e}")

        # Calculate overall results
        test_duration = time.time() - test_start_time
        test_results["duration_seconds"] = test_duration
        test_results["overall_status"] = self._calculate_overall_status(test_results["tests"])

        # Save results
        self._save_test_results(test_results)

        return test_results

    def _test_response_quality(self, monitor: APU123EngagementMonitor) -> Dict[str, Any]:
        """Test response quality generation"""
        quality_results = {
            "test_start": datetime.now().isoformat(),
            "interactions_tested": len(self.test_interactions),
            "results": [],
            "summary": {}
        }

        total_score = 0
        passed_tests = 0

        for interaction in self.test_interactions:
            try:
                start_time = time.time()

                response = monitor.process_community_interaction(
                    platform=interaction["platform"],
                    author=interaction["author"],
                    content=interaction["content"],
                    community_topic=interaction["community_topic"]
                )

                response_time = time.time() - start_time

                if response:
                    quality_score = response.quality_metrics.overall_score
                    meets_threshold = quality_score >= interaction["expected_quality_min"]

                    result = {
                        "platform": interaction["platform"],
                        "author": interaction["author"],
                        "content_preview": interaction["content"][:50] + "...",
                        "quality_score": quality_score,
                        "expected_min": interaction["expected_quality_min"],
                        "meets_threshold": meets_threshold,
                        "response_time": response_time,
                        "response_preview": response.content[:100] + "...",
                        "personalization_score": response.quality_metrics.personalization_score,
                        "conversation_score": response.quality_metrics.conversation_score,
                        "engagement_score": response.quality_metrics.engagement_score,
                        "has_follow_up": len(response.follow_up_questions) > 0,
                        "has_community_hooks": len(response.community_hooks) > 0
                    }

                    total_score += quality_score
                    if meets_threshold:
                        passed_tests += 1

                else:
                    result = {
                        "platform": interaction["platform"],
                        "error": "No response generated",
                        "meets_threshold": False,
                        "response_time": response_time
                    }

                quality_results["results"].append(result)

            except Exception as e:
                quality_results["results"].append({
                    "platform": interaction["platform"],
                    "error": str(e),
                    "meets_threshold": False
                })

        # Calculate summary
        quality_results["summary"] = {
            "tests_passed": passed_tests,
            "total_tests": len(self.test_interactions),
            "pass_rate": passed_tests / len(self.test_interactions),
            "average_quality_score": total_score / len(self.test_interactions) if self.test_interactions else 0,
            "average_response_time": sum(r.get("response_time", 0) for r in quality_results["results"]) / len(quality_results["results"]),
            "status": "passed" if passed_tests >= len(self.test_interactions) * 0.8 else "failed"
        }

        return quality_results

    def _test_system_integration(self, integration: APU123SystemIntegration) -> Dict[str, Any]:
        """Test system integration functionality"""
        integration_results = {
            "test_start": datetime.now().isoformat(),
            "integrations_tested": [],
            "results": {},
            "summary": {}
        }

        integrations_to_test = ["live_dashboard", "paperclip"]
        successful_integrations = 0

        for integration_name in integrations_to_test:
            try:
                start_time = time.time()

                if integration_name == "live_dashboard":
                    result = integration.sync_with_live_dashboard()
                elif integration_name == "paperclip":
                    result = integration.sync_with_paperclip_coordination()
                else:
                    result = {"status": "not_implemented"}

                integration_time = time.time() - start_time

                integration_results["results"][integration_name] = {
                    "status": result.get("status", "unknown"),
                    "integration_time": integration_time,
                    "error": result.get("error"),
                    "success": result.get("status") == "success"
                }

                if result.get("status") == "success":
                    successful_integrations += 1

                integration_results["integrations_tested"].append(integration_name)

            except Exception as e:
                integration_results["results"][integration_name] = {
                    "status": "error",
                    "error": str(e),
                    "success": False
                }

        # Calculate summary
        integration_results["summary"] = {
            "successful_integrations": successful_integrations,
            "total_integrations": len(integrations_to_test),
            "integration_success_rate": successful_integrations / len(integrations_to_test),
            "status": "passed" if successful_integrations >= len(integrations_to_test) * 0.5 else "failed"
        }

        return integration_results

    def _test_performance(self, monitor: APU123EngagementMonitor) -> Dict[str, Any]:
        """Test performance benchmarks"""
        performance_results = {
            "test_start": datetime.now().isoformat(),
            "benchmark_tests": [],
            "summary": {}
        }

        # Test response generation speed
        response_times = []
        for i in range(5):  # Test 5 times for average
            test_interaction = self.test_interactions[0]  # Use first test case

            start_time = time.time()
            response = monitor.process_community_interaction(
                platform=test_interaction["platform"],
                author=f"test_user_{i}",
                content=test_interaction["content"],
                community_topic=test_interaction["community_topic"]
            )
            end_time = time.time()

            response_time = end_time - start_time
            response_times.append(response_time)

        # Test database operations
        db_start = time.time()
        dashboard = monitor.get_quality_dashboard()
        db_time = time.time() - db_start

        performance_results["benchmark_tests"] = [
            {
                "test": "response_generation_speed",
                "average_time": sum(response_times) / len(response_times),
                "min_time": min(response_times),
                "max_time": max(response_times),
                "threshold": 5.0,  # 5 seconds
                "passed": max(response_times) < 5.0
            },
            {
                "test": "database_query_speed",
                "time": db_time,
                "threshold": 1.0,  # 1 second
                "passed": db_time < 1.0
            }
        ]

        # Calculate summary
        passed_benchmarks = sum(1 for test in performance_results["benchmark_tests"] if test["passed"])
        total_benchmarks = len(performance_results["benchmark_tests"])

        performance_results["summary"] = {
            "passed_benchmarks": passed_benchmarks,
            "total_benchmarks": total_benchmarks,
            "performance_score": passed_benchmarks / total_benchmarks,
            "status": "passed" if passed_benchmarks == total_benchmarks else "failed"
        }

        return performance_results

    def _test_quality_scoring(self, monitor: APU123EngagementMonitor) -> Dict[str, Any]:
        """Test quality scoring accuracy"""
        scoring_results = {
            "test_start": datetime.now().isoformat(),
            "scoring_tests": [],
            "summary": {}
        }

        # Test known good vs bad responses
        test_cases = [
            {
                "content": "Great beat! What DAW did you use? I'm trying to get into production myself",
                "expected_quality": "high",
                "expected_min_score": 0.7
            },
            {
                "content": "Nice",
                "expected_quality": "low",
                "expected_max_score": 0.4
            },
            {
                "content": "This is fire! How long did it take you to make this? I'm working on something similar and would love some tips on mixing the 808s",
                "expected_quality": "high",
                "expected_min_score": 0.8
            }
        ]

        correct_scores = 0

        for i, test_case in enumerate(test_cases):
            try:
                # Create a mock response to test scoring
                context = ConversationContext(
                    platform="test",
                    content=test_case["content"],
                    author=f"test_user_{i}",
                    timestamp=datetime.now(),
                    engagement_level=0.5,
                    sentiment="neutral",
                    community_topic="test",
                    previous_interactions=[]
                )

                response = monitor.response_engine.generate_personalized_response(context)

                if response:
                    quality_score = response.quality_metrics.overall_score

                    if test_case["expected_quality"] == "high":
                        correct = quality_score >= test_case["expected_min_score"]
                    else:
                        correct = quality_score <= test_case["expected_max_score"]

                    if correct:
                        correct_scores += 1

                    scoring_results["scoring_tests"].append({
                        "test_case": i + 1,
                        "content_preview": test_case["content"][:50] + "...",
                        "expected_quality": test_case["expected_quality"],
                        "actual_score": quality_score,
                        "correct_classification": correct
                    })

            except Exception as e:
                scoring_results["scoring_tests"].append({
                    "test_case": i + 1,
                    "error": str(e),
                    "correct_classification": False
                })

        scoring_results["summary"] = {
            "correct_scores": correct_scores,
            "total_tests": len(test_cases),
            "accuracy": correct_scores / len(test_cases),
            "status": "passed" if correct_scores >= len(test_cases) * 0.8 else "failed"
        }

        return scoring_results

    def _test_edge_cases(self, monitor: APU123EngagementMonitor) -> Dict[str, Any]:
        """Test edge cases and error handling"""
        edge_case_results = {
            "test_start": datetime.now().isoformat(),
            "edge_cases": [],
            "summary": {}
        }

        edge_cases = [
            {
                "name": "empty_content",
                "platform": "test",
                "author": "test_user",
                "content": "",
                "community_topic": "test"
            },
            {
                "name": "very_long_content",
                "platform": "test",
                "author": "test_user",
                "content": "A" * 5000,  # Very long content
                "community_topic": "test"
            },
            {
                "name": "special_characters",
                "platform": "test",
                "author": "test_user",
                "content": "🎵🎤🔥 What's good with these beats? 💯 #NewMusic @everyone",
                "community_topic": "test"
            },
            {
                "name": "non_english",
                "platform": "test",
                "author": "test_user",
                "content": "Este beat está increíble! ¿Qué opinas?",
                "community_topic": "test"
            }
        ]

        successful_cases = 0

        for edge_case in edge_cases:
            try:
                start_time = time.time()
                response = monitor.process_community_interaction(**{k: v for k, v in edge_case.items() if k != "name"})
                response_time = time.time() - start_time

                success = response is not None
                if success:
                    successful_cases += 1

                edge_case_results["edge_cases"].append({
                    "case_name": edge_case["name"],
                    "success": success,
                    "response_time": response_time,
                    "has_response": response is not None,
                    "quality_score": response.quality_metrics.overall_score if response else None
                })

            except Exception as e:
                edge_case_results["edge_cases"].append({
                    "case_name": edge_case["name"],
                    "success": False,
                    "error": str(e)
                })

        edge_case_results["summary"] = {
            "successful_cases": successful_cases,
            "total_cases": len(edge_cases),
            "success_rate": successful_cases / len(edge_cases),
            "status": "passed" if successful_cases >= len(edge_cases) * 0.75 else "failed"
        }

        return edge_case_results

    def _test_integration_reliability(self, integration: APU123SystemIntegration) -> Dict[str, Any]:
        """Test integration reliability under load"""
        reliability_results = {
            "test_start": datetime.now().isoformat(),
            "reliability_tests": [],
            "summary": {}
        }

        # Test multiple rapid integrations
        successful_syncs = 0
        total_syncs = 5

        for i in range(total_syncs):
            try:
                start_time = time.time()
                result = integration.sync_with_live_dashboard()
                sync_time = time.time() - start_time

                success = result.get("status") == "success"
                if success:
                    successful_syncs += 1

                reliability_results["reliability_tests"].append({
                    "sync_attempt": i + 1,
                    "success": success,
                    "sync_time": sync_time,
                    "status": result.get("status", "unknown")
                })

                # Small delay between syncs
                time.sleep(0.5)

            except Exception as e:
                reliability_results["reliability_tests"].append({
                    "sync_attempt": i + 1,
                    "success": False,
                    "error": str(e)
                })

        reliability_results["summary"] = {
            "successful_syncs": successful_syncs,
            "total_syncs": total_syncs,
            "reliability_rate": successful_syncs / total_syncs,
            "status": "passed" if successful_syncs >= total_syncs * 0.8 else "failed"
        }

        return reliability_results

    def _calculate_overall_status(self, tests: Dict[str, Any]) -> str:
        """Calculate overall test status"""
        passed_tests = sum(1 for test in tests.values() if test.get("summary", {}).get("status") == "passed")
        total_tests = len(tests)

        if passed_tests == total_tests:
            return "all_passed"
        elif passed_tests >= total_tests * 0.8:
            return "mostly_passed"
        elif passed_tests >= total_tests * 0.5:
            return "partially_passed"
        else:
            return "failed"

    def _save_test_results(self, results: Dict[str, Any]):
        """Save test results to log file"""
        try:
            existing_log = load_json(self.validation_log) if self.validation_log.exists() else []
            existing_log.append(results)
            save_json(self.validation_log, existing_log[-20:])  # Keep last 20 test runs
        except Exception as e:
            logger.error(f"Failed to save test results: {e}")

def main():
    """Run APU-123 test and validation suite"""
    test_suite = APU123TestSuite()
    results = test_suite.run_comprehensive_tests()

    print(f"\n📊 APU-123 Test Results Summary")
    print("=" * 50)
    print(f"Overall Status: {results['overall_status']}")
    print(f"Duration: {results.get('duration_seconds', 0):.2f} seconds")

    if 'tests' in results:
        for test_name, test_data in results['tests'].items():
            summary = test_data.get('summary', {})
            status = summary.get('status', 'unknown')
            print(f"{test_name}: {status}")

    if results.get('error'):
        print(f"\n❌ Test Suite Error: {results['error']}")
    else:
        print(f"\n✅ APU-123 validation complete!")

    return results

if __name__ == "__main__":
    main()