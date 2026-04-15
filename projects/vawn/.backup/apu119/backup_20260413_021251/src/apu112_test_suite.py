"""
apu112_test_suite.py — APU-112 Engagement Metrics Test Suite

Comprehensive test suite for validating APU-112 engagement metrics aggregation system.
Tests all components including data collection, normalization, trend analysis, and API endpoints.

Created by: Backend API Agent (APU-112)
Usage: python apu112_test_suite.py [--verbose] [--integration-test]
"""

import json
import sys
import unittest
import tempfile
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sqlite3

sys.path.insert(0, str(Path(__file__).parent))

from apu112_engagement_metrics_aggregator import (
    APU112EngagementAggregator, EngagementMetricsDB, MetricPoint, EngagementSnapshot,
    TrendAnalyzer, CorrelationAnalyzer, TrendAnalysis, PerformanceCorrelation
)

class TestMetricPoint(unittest.TestCase):
    """Test MetricPoint data structure."""

    def test_metric_point_creation(self):
        """Test MetricPoint creation and attributes."""
        metric = MetricPoint(
            timestamp="2026-04-12T10:00:00",
            platform="instagram",
            post_id="test_post_1",
            metric_type="likes",
            value=150,
            normalized_value=150.0,
            hashtags=["#music", "#hiphop"],
            post_caption="Test post caption"
        )

        self.assertEqual(metric.platform, "instagram")
        self.assertEqual(metric.value, 150)
        self.assertEqual(len(metric.hashtags), 2)
        self.assertIn("#music", metric.hashtags)

class TestEngagementMetricsDB(unittest.TestCase):
    """Test database operations."""

    def setUp(self):
        """Setup test database."""
        self.test_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db = EngagementMetricsDB(Path(self.test_db.name))

    def tearDown(self):
        """Cleanup test database."""
        self.test_db.close()
        Path(self.test_db.name).unlink(missing_ok=True)

    def test_database_initialization(self):
        """Test database schema creation."""
        # Check if tables exist
        with sqlite3.connect(self.test_db.name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

        expected_tables = ['metrics', 'engagement_snapshots', 'trend_analysis', 'hashtag_performance']
        for table in expected_tables:
            self.assertIn(table, tables, f"Table {table} should exist")

    def test_metric_insertion(self):
        """Test metric point insertion."""
        metric = MetricPoint(
            timestamp="2026-04-12T10:00:00",
            platform="instagram",
            post_id="test_post",
            metric_type="likes",
            value=100,
            normalized_value=100.0,
            hashtags=["#test"],
            post_caption="Test caption"
        )

        self.db.insert_metric(metric)

        # Verify insertion
        with sqlite3.connect(self.test_db.name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM metrics")
            count = cursor.fetchone()[0]

        self.assertEqual(count, 1)

    def test_engagement_snapshot_insertion(self):
        """Test engagement snapshot insertion."""
        snapshot = EngagementSnapshot(
            timestamp="2026-04-12T10:00:00",
            platform="instagram",
            post_id="test_post",
            metrics={"likes": 100, "comments": 20},
            normalized_score=5.0,
            hashtag_count=3,
            hashtag_performance_score=0.8,
            engagement_velocity=2.5,
            viral_potential_score=0.6
        )

        self.db.insert_engagement_snapshot(snapshot)

        # Verify insertion
        with sqlite3.connect(self.test_db.name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM engagement_snapshots")
            count = cursor.fetchone()[0]

        self.assertEqual(count, 1)

    def test_recent_metrics_retrieval(self):
        """Test retrieving recent metrics."""
        # Insert test metrics
        for i in range(5):
            metric = MetricPoint(
                timestamp=(datetime.now() - timedelta(hours=i)).isoformat(),
                platform="instagram",
                post_id=f"test_post_{i}",
                metric_type="likes",
                value=100 + i,
                normalized_value=100.0 + i,
                hashtags=["#test"],
                post_caption=f"Test caption {i}"
            )
            self.db.insert_metric(metric)

        # Retrieve recent metrics
        recent_metrics = self.db.get_recent_metrics(hours=24)
        self.assertEqual(len(recent_metrics), 5)

        # Test platform filtering
        platform_metrics = self.db.get_recent_metrics(hours=24, platform="instagram")
        self.assertEqual(len(platform_metrics), 5)

        non_existent_metrics = self.db.get_recent_metrics(hours=24, platform="tiktok")
        self.assertEqual(len(non_existent_metrics), 0)

class TestTrendAnalyzer(unittest.TestCase):
    """Test trend analysis functionality."""

    def setUp(self):
        """Setup trend analyzer."""
        self.config = {
            "analysis": {
                "trend_detection_window_hours": 24,
                "correlation_analysis_days": 7
            }
        }
        self.analyzer = TrendAnalyzer(self.config)

    def test_trend_type_determination(self):
        """Test trend type determination."""
        # Test growth trend
        growth_scores = [1.0, 2.0, 3.0, 4.0, 5.0]
        velocity_scores = [1.0, 1.0, 1.0, 1.0, 1.0]
        trend_type = self.analyzer._determine_trend_type(growth_scores, velocity_scores)
        self.assertEqual(trend_type, "growth")

        # Test decline trend
        decline_scores = [5.0, 4.0, 3.0, 2.0, 1.0]
        trend_type = self.analyzer._determine_trend_type(decline_scores, velocity_scores)
        self.assertEqual(trend_type, "decline")

        # Test stable trend
        stable_scores = [3.0, 3.1, 2.9, 3.0, 3.0]
        trend_type = self.analyzer._determine_trend_type(stable_scores, velocity_scores)
        self.assertEqual(trend_type, "stable")

    def test_trend_confidence_calculation(self):
        """Test trend confidence calculation."""
        # Consistent scores should have high confidence
        consistent_scores = [3.0, 3.1, 2.9, 3.0, 3.0]
        confidence = self.analyzer._calculate_trend_confidence(consistent_scores)
        self.assertGreater(confidence, 0.5)

        # Volatile scores should have lower confidence
        volatile_scores = [1.0, 5.0, 2.0, 4.0, 1.5]
        confidence = self.analyzer._calculate_trend_confidence(volatile_scores)
        self.assertLess(confidence, 0.8)

    def test_analyze_trends(self):
        """Test trend analysis with snapshots."""
        snapshots = []

        # Create test snapshots for Instagram with growth trend
        for i in range(5):
            snapshot = EngagementSnapshot(
                timestamp=(datetime.now() - timedelta(hours=i)).isoformat(),
                platform="instagram",
                post_id=f"test_post_{i}",
                metrics={"likes": 100 + i*20},
                normalized_score=1.0 + i*0.5,  # Growing trend
                hashtag_count=3,
                hashtag_performance_score=0.8,
                engagement_velocity=2.0 + i*0.2,  # Growing velocity
                viral_potential_score=0.6
            )
            snapshots.append(snapshot)

        trends = self.analyzer.analyze_trends(snapshots)
        self.assertEqual(len(trends), 1)  # One platform
        self.assertEqual(trends[0].platform, "instagram")
        self.assertIn(trends[0].trend_type, ["growth", "stable"])  # Should detect growth or stable

class TestCorrelationAnalyzer(unittest.TestCase):
    """Test correlation analysis functionality."""

    def setUp(self):
        """Setup correlation analyzer."""
        self.config = {
            "analysis": {
                "trend_detection_window_hours": 24,
                "correlation_analysis_days": 7
            }
        }
        self.analyzer = CorrelationAnalyzer(self.config)

    def test_hashtag_performance_update(self):
        """Test hashtag performance tracking."""
        metrics = []

        # Create metrics with hashtags
        for i in range(5):
            metric = MetricPoint(
                timestamp=(datetime.now() - timedelta(hours=i)).isoformat(),
                platform="instagram",
                post_id=f"test_post_{i}",
                metric_type="likes",
                value=100 + i*10,
                normalized_value=100.0 + i*10,
                hashtags=["#music", "#hiphop"],
                post_caption=f"Test post {i}"
            )
            metrics.append(metric)

        self.analyzer.update_hashtag_correlations(metrics)

        # Check if hashtag performance was tracked
        self.assertIn("#music", self.analyzer.hashtag_performance)
        self.assertIn("#hiphop", self.analyzer.hashtag_performance)

        music_perf = self.analyzer.hashtag_performance["#music"]
        self.assertEqual(music_perf["usage_count"], 5)
        self.assertGreater(music_perf["avg_engagement_score"], 0)

    def test_hashtag_performance_retrieval(self):
        """Test hashtag performance score retrieval."""
        # Setup test data
        self.analyzer.hashtag_performance["#test"] = {
            "usage_count": 10,
            "avg_engagement_score": 8.5,
            "platform_performance": {"instagram": 9.0, "tiktok": 7.0},
            "last_updated": datetime.now().isoformat()
        }

        # Test platform-specific performance
        instagram_score = self.analyzer.get_hashtag_performance("#test", "instagram")
        self.assertGreater(instagram_score, 0.5)  # Should be normalized

        tiktok_score = self.analyzer.get_hashtag_performance("#test", "tiktok")
        self.assertGreater(tiktok_score, 0.5)

        # Test unknown hashtag
        unknown_score = self.analyzer.get_hashtag_performance("#unknown", "instagram")
        self.assertEqual(unknown_score, 0.5)  # Default neutral score

    def test_top_performing_hashtags(self):
        """Test top performing hashtags retrieval."""
        # Setup test data
        self.analyzer.hashtag_performance = {
            "#highperformer": {
                "usage_count": 20,
                "avg_engagement_score": 10.0,
                "platform_performance": {"instagram": 12.0, "tiktok": 8.0},
                "last_updated": datetime.now().isoformat()
            },
            "#lowperformer": {
                "usage_count": 5,
                "avg_engagement_score": 3.0,
                "platform_performance": {"instagram": 2.0, "tiktok": 4.0},
                "last_updated": datetime.now().isoformat()
            }
        }

        top_hashtags = self.analyzer.get_top_performing_hashtags("instagram", limit=5)
        self.assertGreater(len(top_hashtags), 0)

        # Should be sorted by performance
        if len(top_hashtags) > 1:
            self.assertGreaterEqual(
                top_hashtags[0].platform_performance.get("instagram", 0),
                top_hashtags[1].platform_performance.get("instagram", 0)
            )

class TestAPU112Aggregator(unittest.TestCase):
    """Test main aggregator functionality."""

    def setUp(self):
        """Setup test aggregator."""
        self.test_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)

        # Create test config
        self.test_config = {
            "collection": {
                "real_time_interval_seconds": 60,
                "batch_size": 100,
                "platforms": ["instagram", "tiktok"],
                "enable_real_time_alerts": True
            },
            "normalization": {
                "enable_cross_platform_normalization": True,
                "weight_factors": {
                    "instagram": {"likes": 1.0, "comments": 3.0},
                    "tiktok": {"likes": 1.0, "comments": 4.0}
                }
            },
            "performance": {"cache_size": 100}
        }

        with patch('apu112_engagement_metrics_aggregator.APU112_DB', Path(self.test_db.name)):
            self.aggregator = APU112EngagementAggregator()
            self.aggregator.config = self.test_config

    def tearDown(self):
        """Cleanup test resources."""
        self.test_db.close()
        Path(self.test_db.name).unlink(missing_ok=True)

    def test_metric_value_normalization(self):
        """Test metric value normalization."""
        # Test Instagram comment normalization
        normalized = self.aggregator._normalize_metric_value("comments", 10, "instagram")
        expected = 10 * 3.0  # Weight factor for Instagram comments
        self.assertEqual(normalized, expected)

        # Test TikTok comment normalization
        normalized = self.aggregator._normalize_metric_value("comments", 10, "tiktok")
        expected = 10 * 4.0  # Weight factor for TikTok comments
        self.assertEqual(normalized, expected)

        # Test unknown metric type
        normalized = self.aggregator._normalize_metric_value("unknown", 10, "instagram")
        self.assertEqual(normalized, 10.0)  # Default weight of 1.0

    def test_engagement_score_calculation(self):
        """Test normalized engagement score calculation."""
        metrics = {"likes": 100, "comments": 20}

        # Test Instagram scoring
        score = self.aggregator._calculate_normalized_engagement_score(metrics, "instagram")
        expected = (100 * 1.0 + 20 * 3.0) / (1.0 + 3.0)  # Weighted average
        self.assertEqual(score, expected)

    def test_viral_potential_calculation(self):
        """Test viral potential score calculation."""
        # High engagement metrics
        high_metrics = {"likes": 1000, "comments": 200, "shares": 100}
        high_score = self.aggregator._calculate_viral_potential_score(high_metrics, "instagram")
        self.assertGreater(high_score, 0.5)

        # Low engagement metrics
        low_metrics = {"likes": 10, "comments": 1, "shares": 0}
        low_score = self.aggregator._calculate_viral_potential_score(low_metrics, "instagram")
        self.assertLess(low_score, high_score)

        # No likes should result in 0 score
        zero_metrics = {"likes": 0, "comments": 5, "shares": 2}
        zero_score = self.aggregator._calculate_viral_potential_score(zero_metrics, "instagram")
        self.assertEqual(zero_score, 0.0)

    @patch('apu112_engagement_metrics_aggregator.load_json')
    def test_collect_from_engagement_log(self, mock_load_json):
        """Test collection from engagement log."""
        # Mock engagement log data
        mock_engagement_data = {
            "history": [
                {
                    "date": datetime.now().isoformat(),
                    "platform": "instagram",
                    "comment": "Great post!",
                    "post_id": "test_post_1"
                }
            ]
        }
        mock_load_json.return_value = mock_engagement_data

        metrics = self.aggregator._collect_from_engagement_log()
        self.assertGreater(len(metrics), 0)
        self.assertEqual(metrics[0].platform, "instagram")
        self.assertEqual(metrics[0].metric_type, "comments")

    def test_process_metrics_batch(self):
        """Test metrics batch processing."""
        metrics = [
            MetricPoint(
                timestamp=datetime.now().isoformat(),
                platform="instagram",
                post_id="test_post_1",
                metric_type="likes",
                value=100,
                normalized_value=100.0,
                hashtags=["#music"],
                post_caption="Test post"
            ),
            MetricPoint(
                timestamp=datetime.now().isoformat(),
                platform="instagram",
                post_id="test_post_1",
                metric_type="comments",
                value=20,
                normalized_value=60.0,  # 20 * 3.0 weight
                hashtags=["#music"],
                post_caption="Test post"
            )
        ]

        snapshots = self.aggregator.process_metrics_batch(metrics)
        self.assertEqual(len(snapshots), 1)  # Should be grouped by post

        snapshot = snapshots[0]
        self.assertEqual(snapshot.platform, "instagram")
        self.assertEqual(snapshot.post_id, "test_post_1")
        self.assertEqual(snapshot.metrics["likes"], 100)
        self.assertEqual(snapshot.metrics["comments"], 20)

class TestIntegrationScenarios(unittest.TestCase):
    """Integration tests for complete workflows."""

    def setUp(self):
        """Setup integration test environment."""
        self.test_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)

        with patch('apu112_engagement_metrics_aggregator.APU112_DB', Path(self.test_db.name)):
            self.aggregator = APU112EngagementAggregator()

    def tearDown(self):
        """Cleanup integration test environment."""
        self.test_db.close()
        Path(self.test_db.name).unlink(missing_ok=True)

    @patch('apu112_engagement_metrics_aggregator.load_json')
    def test_full_aggregation_cycle(self, mock_load_json):
        """Test complete aggregation cycle."""
        # Mock data sources
        mock_load_json.side_effect = [
            {"history": []},  # engagement_log
            {  # metrics_log
                "test_image": {
                    "2026-04-12": {
                        "instagram": {"likes": 150, "comments": 30}
                    }
                }
            }
        ]

        # Run aggregation cycle
        result = self.aggregator.run_aggregation_cycle()

        self.assertEqual(result["status"], "success")
        self.assertGreaterEqual(result["metrics_collected"], 0)
        self.assertGreaterEqual(result["snapshots_created"], 0)

    def test_alert_generation(self):
        """Test alert generation functionality."""
        # Create high viral potential snapshot
        high_viral_snapshot = EngagementSnapshot(
            timestamp=datetime.now().isoformat(),
            platform="instagram",
            post_id="viral_post",
            metrics={"likes": 1000, "comments": 200, "shares": 150},
            normalized_score=8.5,
            hashtag_count=5,
            hashtag_performance_score=0.9,
            engagement_velocity=50.0,  # High velocity
            viral_potential_score=0.95  # High viral potential
        )

        snapshots = [high_viral_snapshot]
        trends = []  # Empty trends for this test

        alerts = self.aggregator._generate_alerts(snapshots, trends)

        # Should generate alerts for high viral potential and engagement velocity
        alert_types = [alert["type"] for alert in alerts]
        self.assertIn("viral_potential", alert_types)
        self.assertIn("high_engagement", alert_types)

def run_performance_tests():
    """Run performance tests for APU-112 system."""
    print("\n[PERFORMANCE TESTS]")

    # Test database performance
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_db:
        db = EngagementMetricsDB(Path(temp_db.name))

        # Time metric insertion
        start_time = time.time()
        for i in range(1000):
            metric = MetricPoint(
                timestamp=datetime.now().isoformat(),
                platform="instagram",
                post_id=f"perf_test_{i}",
                metric_type="likes",
                value=i,
                normalized_value=float(i),
                hashtags=["#perftest"],
                post_caption=f"Performance test {i}"
            )
            db.insert_metric(metric)

        insertion_time = time.time() - start_time
        print(f"✅ Inserted 1000 metrics in {insertion_time:.2f}s ({1000/insertion_time:.1f} metrics/sec)")

        # Time retrieval
        start_time = time.time()
        recent_metrics = db.get_recent_metrics(hours=24)
        retrieval_time = time.time() - start_time
        print(f"✅ Retrieved {len(recent_metrics)} metrics in {retrieval_time:.3f}s")

        # Cleanup
        Path(temp_db.name).unlink()

def run_integration_tests():
    """Run integration tests with real data simulation."""
    print("\n[INTEGRATION TESTS]")

    try:
        # Test aggregator initialization
        aggregator = APU112EngagementAggregator()
        print("✅ Aggregator initialization successful")

        # Test configuration loading
        config_keys = ["collection", "normalization", "analysis", "performance"]
        for key in config_keys:
            assert key in aggregator.config, f"Missing config key: {key}"
        print("✅ Configuration validation successful")

        # Test database operations
        test_metric = MetricPoint(
            timestamp=datetime.now().isoformat(),
            platform="instagram",
            post_id="integration_test",
            metric_type="likes",
            value=100,
            normalized_value=100.0,
            hashtags=["#test"],
            post_caption="Integration test"
        )

        aggregator.db.insert_metric(test_metric)
        recent_metrics = aggregator.db.get_recent_metrics(hours=1)
        assert len(recent_metrics) > 0, "Failed to retrieve inserted metric"
        print("✅ Database operations successful")

        # Test trend analysis
        analyzer = TrendAnalyzer(aggregator.config)
        assert analyzer is not None, "Failed to initialize trend analyzer"
        print("✅ Trend analyzer initialization successful")

        # Test correlation analysis
        correlation_analyzer = CorrelationAnalyzer(aggregator.config)
        assert correlation_analyzer is not None, "Failed to initialize correlation analyzer"
        print("✅ Correlation analyzer initialization successful")

        print("🎉 All integration tests passed!")
        return True

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def main():
    """Main test runner function."""
    import argparse

    parser = argparse.ArgumentParser(description="APU-112 Engagement Metrics Test Suite")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose test output")
    parser.add_argument("--integration-test", action="store_true", help="Run integration tests")
    parser.add_argument("--performance-test", action="store_true", help="Run performance tests")
    parser.add_argument("--unit-only", action="store_true", help="Run unit tests only")

    args = parser.parse_args()

    print("=" * 80)
    print("[*] APU-112 Engagement Metrics Aggregation System - Test Suite")
    print("=" * 80)

    # Set verbosity
    verbosity = 2 if args.verbose else 1

    success = True

    if not args.integration_test and not args.performance_test:
        # Run unit tests
        print("\n[UNIT TESTS]")

        # Discover and run unit tests
        loader = unittest.TestLoader()
        start_dir = Path(__file__).parent
        suite = loader.discover(start_dir, pattern='apu112_test_suite.py')

        runner = unittest.TextTestRunner(verbosity=verbosity)
        result = runner.run(suite)

        if not result.wasSuccessful():
            success = False
            print(f"❌ Unit tests failed: {len(result.failures)} failures, {len(result.errors)} errors")
        else:
            print("✅ All unit tests passed!")

    if args.integration_test or not args.unit_only:
        # Run integration tests
        integration_success = run_integration_tests()
        if not integration_success:
            success = False

    if args.performance_test:
        # Run performance tests
        run_performance_tests()

    if success:
        print(f"\n🎉 APU-112 test suite completed successfully!")
        return 0
    else:
        print(f"\n❌ APU-112 test suite failed!")
        return 1

if __name__ == "__main__":
    exit(main())