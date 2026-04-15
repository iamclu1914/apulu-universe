"""
apu148_nova_engagement_analytics.py — Nova Analytics Framework for APU-148

Content analytics and weekly digest automation for Apulu Records with Nova framework integration.
Complements existing response systems (APU-119, 123, 127) with comprehensive metrics and reporting.

Created by: Dex - Community Agent (APU-148)
Framework: Nova Content Analytics
Focus: Platform metrics, content pillar tracking, weekly digest automation, benchmarking
"""

import json
import sys
import sqlite3
import threading
import time
import traceback
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict, deque
import requests
import statistics

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import (
    load_json, save_json, VAWN_DIR, ENGAGEMENT_LOG, METRICS_LOG,
    log_run, today_str, RESEARCH_DIR, get_anthropic_client
)

# APU-148 Configuration
APU148_DB = VAWN_DIR / "database" / "apu148_nova_analytics.db"
APU148_CONFIG = VAWN_DIR / "config" / "apu148_config.json"
APU148_LOG = RESEARCH_DIR / "apu148_nova_analytics_log.json"
APU148_DIGEST_LOG = RESEARCH_DIR / "apu148_weekly_digest_log.json"
APU148_REPORTS_DIR = RESEARCH_DIR / "weekly_digests"

# Ensure directories exist
APU148_DB.parent.mkdir(exist_ok=True)
APU148_CONFIG.parent.mkdir(exist_ok=True)
RESEARCH_DIR.mkdir(exist_ok=True)
APU148_REPORTS_DIR.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("APU148_Nova")

# Nova Analytics Framework - Content Pillars
CONTENT_PILLARS = {
    "monday": "awareness",
    "tuesday": "lyric",
    "wednesday": "bts",
    "thursday": "engagement",
    "friday": "conversion",
    "saturday": "audience",
    "sunday": "video"
}

# Nova Engagement Scoring Formula
def calculate_nova_engagement_score(metrics: Dict[str, int]) -> float:
    """
    Nova engagement scoring:
    score = (likes * 1) + (comments * 3) + (saves * 5) + (shares * 4) + (reposts * 4) + (views * 0.01)
    """
    return (
        metrics.get("likes", 0) * 1 +
        metrics.get("comments", 0) * 3 +
        metrics.get("saves", 0) * 5 +
        metrics.get("shares", 0) * 4 +
        metrics.get("reposts", 0) * 4 +
        metrics.get("views", 0) * 0.01
    )

# Platform-specific metrics that matter most
PLATFORM_PRIMARY_METRICS = {
    "instagram": "saves",  # Strongest signal of value — user wants to return
    "tiktok": "shares",    # Virality indicator — user pushing to their network
    "x": "reposts",        # Amplification — extends reach beyond followers
    "threads": "comments", # Conversation depth — community building signal
    "bluesky": "likes"     # Smaller platform — any engagement is significant
}

# Independent Hip-Hop Benchmarks
INDIE_HIPHOP_BENCHMARKS = {
    "engagement_rate": {"concerning": 0.01, "average": 0.03, "strong": 0.05},
    "save_rate_ig": {"concerning": 0.01, "average": 0.025, "strong": 0.05},
    "share_rate_tt": {"concerning": 0.005, "average": 0.015, "strong": 0.03},
    "comments_per_post": {"concerning": 2, "average": 10, "strong": 20}
}

@dataclass
class PlatformMetrics:
    """Platform-specific engagement metrics"""
    platform: str
    timestamp: datetime
    likes: int
    comments: int
    saves: int
    shares: int
    reposts: int
    views: int
    followers: int
    nova_score: float
    primary_metric_value: int
    engagement_rate: float

@dataclass
class ContentPillarAnalysis:
    """Content pillar performance analysis"""
    pillar: str
    day_of_week: str
    post_count: int
    total_nova_score: float
    avg_nova_score: float
    best_performing_post: Dict[str, Any]
    pillar_trend: str  # improving, stable, declining

@dataclass
class WeeklyDigest:
    """Nova analytics weekly digest"""
    week_start: datetime
    week_end: datetime
    total_posts: int
    total_engagement_score: float
    best_performing_day: str
    best_performing_pillar: str
    best_performing_platform: str
    platform_breakdown: Dict[str, Dict[str, Any]]
    pillar_breakdown: Dict[str, Dict[str, Any]]
    top_posts: List[Dict[str, Any]]
    recommendations: List[str]
    benchmark_analysis: Dict[str, str]

class NovaAnalyticsEngine:
    """Core Nova analytics processing engine"""

    def __init__(self):
        self.platforms = ["instagram", "tiktok", "x", "threads", "bluesky"]
        self.metrics_cache = {}
        self.pillar_history = defaultdict(list)

    def fetch_platform_metrics(self, platform: str, access_token: str, days_back: int = 7) -> List[PlatformMetrics]:
        """Fetch metrics from platform API"""
        metrics_list = []

        try:
            # Simulate API calls - replace with actual platform APIs
            headers = {"Authorization": f"Bearer {access_token}"}
            base_url = "https://apulustudio.onrender.com/api"

            # Fetch posts from last N days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)

            posts_url = f"{base_url}/posts?platform={platform}&start_date={start_date.isoformat()}&end_date={end_date.isoformat()}"
            response = requests.get(posts_url, headers=headers, timeout=30)

            if response.status_code == 200:
                posts = response.json().get("posts", [])

                for post in posts:
                    # Extract metrics
                    metrics = post.get("metrics", {})

                    # Calculate Nova score
                    nova_score = calculate_nova_engagement_score(metrics)

                    # Calculate engagement rate
                    followers = post.get("author_metrics", {}).get("followers", 1)
                    total_interactions = sum([
                        metrics.get("likes", 0),
                        metrics.get("comments", 0),
                        metrics.get("shares", 0),
                        metrics.get("reposts", 0)
                    ])
                    engagement_rate = total_interactions / max(followers, 1)

                    # Get primary metric for platform
                    primary_metric = PLATFORM_PRIMARY_METRICS[platform]
                    primary_metric_value = metrics.get(primary_metric, 0)

                    platform_metric = PlatformMetrics(
                        platform=platform,
                        timestamp=datetime.fromisoformat(post.get("created_at")),
                        likes=metrics.get("likes", 0),
                        comments=metrics.get("comments", 0),
                        saves=metrics.get("saves", 0),
                        shares=metrics.get("shares", 0),
                        reposts=metrics.get("reposts", 0),
                        views=metrics.get("views", 0),
                        followers=followers,
                        nova_score=nova_score,
                        primary_metric_value=primary_metric_value,
                        engagement_rate=engagement_rate
                    )

                    metrics_list.append(platform_metric)

        except Exception as e:
            logger.error(f"Failed to fetch metrics for {platform}: {e}")

        return metrics_list

    def analyze_content_pillars(self, metrics_data: List[PlatformMetrics]) -> List[ContentPillarAnalysis]:
        """Analyze performance by content pillar (day of week)"""
        pillar_data = defaultdict(list)

        # Group metrics by day of week (content pillar)
        for metric in metrics_data:
            day_name = metric.timestamp.strftime("%A").lower()
            pillar = CONTENT_PILLARS.get(day_name, "unknown")
            pillar_data[pillar].append(metric)

        analyses = []

        for pillar, pillar_metrics in pillar_data.items():
            if not pillar_metrics:
                continue

            # Calculate pillar performance
            total_score = sum(m.nova_score for m in pillar_metrics)
            avg_score = total_score / len(pillar_metrics)

            # Find best performing post
            best_post = max(pillar_metrics, key=lambda x: x.nova_score)

            # Determine trend (requires historical data)
            trend = self._calculate_pillar_trend(pillar, avg_score)

            # Get day of week for this pillar
            day_of_week = next((day for day, p in CONTENT_PILLARS.items() if p == pillar), "unknown")

            analysis = ContentPillarAnalysis(
                pillar=pillar,
                day_of_week=day_of_week,
                post_count=len(pillar_metrics),
                total_nova_score=total_score,
                avg_nova_score=avg_score,
                best_performing_post={
                    "platform": best_post.platform,
                    "nova_score": best_post.nova_score,
                    "engagement_rate": best_post.engagement_rate,
                    "timestamp": best_post.timestamp.isoformat()
                },
                pillar_trend=trend
            )

            analyses.append(analysis)

        return analyses

    def _calculate_pillar_trend(self, pillar: str, current_avg: float) -> str:
        """Calculate trend for content pillar"""
        history = self.pillar_history[pillar]

        if len(history) < 2:
            history.append(current_avg)
            return "insufficient_data"

        # Compare with previous period
        previous_avg = history[-1]
        history.append(current_avg)

        # Keep only last 4 weeks of history
        self.pillar_history[pillar] = history[-4:]

        if current_avg > previous_avg * 1.1:
            return "improving"
        elif current_avg < previous_avg * 0.9:
            return "declining"
        else:
            return "stable"

    def benchmark_against_industry(self, metrics_data: List[PlatformMetrics]) -> Dict[str, str]:
        """Benchmark performance against independent hip-hop standards"""
        if not metrics_data:
            return {"overall": "insufficient_data"}

        results = {}

        # Overall engagement rate
        avg_engagement = statistics.mean([m.engagement_rate for m in metrics_data])
        engagement_benchmarks = INDIE_HIPHOP_BENCHMARKS["engagement_rate"]

        if avg_engagement >= engagement_benchmarks["strong"]:
            results["engagement_rate"] = "strong"
        elif avg_engagement >= engagement_benchmarks["average"]:
            results["engagement_rate"] = "average"
        else:
            results["engagement_rate"] = "concerning"

        # Platform-specific benchmarks
        instagram_metrics = [m for m in metrics_data if m.platform == "instagram"]
        if instagram_metrics:
            avg_saves = statistics.mean([m.saves for m in instagram_metrics])
            avg_followers = statistics.mean([m.followers for m in instagram_metrics])
            save_rate = avg_saves / max(avg_followers, 1)

            save_benchmarks = INDIE_HIPHOP_BENCHMARKS["save_rate_ig"]
            if save_rate >= save_benchmarks["strong"]:
                results["instagram_saves"] = "strong"
            elif save_rate >= save_benchmarks["average"]:
                results["instagram_saves"] = "average"
            else:
                results["instagram_saves"] = "concerning"

        # Comments per post
        avg_comments = statistics.mean([m.comments for m in metrics_data])
        comment_benchmarks = INDIE_HIPHOP_BENCHMARKS["comments_per_post"]

        if avg_comments >= comment_benchmarks["strong"]:
            results["comments_per_post"] = "strong"
        elif avg_comments >= comment_benchmarks["average"]:
            results["comments_per_post"] = "average"
        else:
            results["comments_per_post"] = "concerning"

        return results

class WeeklyDigestGenerator:
    """Generates comprehensive weekly digest reports"""

    def __init__(self, analytics_engine: NovaAnalyticsEngine):
        self.analytics = analytics_engine
        self.anthropic_client = get_anthropic_client()

    def generate_weekly_digest(self, metrics_data: List[PlatformMetrics]) -> WeeklyDigest:
        """Generate comprehensive weekly digest"""
        if not metrics_data:
            logger.warning("No metrics data available for weekly digest")
            return None

        # Calculate time range
        timestamps = [m.timestamp for m in metrics_data]
        week_start = min(timestamps)
        week_end = max(timestamps)

        # Overall stats
        total_posts = len(metrics_data)
        total_engagement_score = sum(m.nova_score for m in metrics_data)

        # Platform breakdown
        platform_breakdown = {}
        for platform in self.analytics.platforms:
            platform_metrics = [m for m in metrics_data if m.platform == platform]
            if platform_metrics:
                total_score = sum(m.nova_score for m in platform_metrics)
                avg_score = total_score / len(platform_metrics)

                platform_breakdown[platform] = {
                    "posts": len(platform_metrics),
                    "engagement": total_score,
                    "avg_score": avg_score,
                    "trend": "stable"  # Could be calculated
                }

        # Best performing metrics
        best_platform = max(platform_breakdown.items(), key=lambda x: x[1]["engagement"])[0]

        # Content pillar analysis
        pillar_analyses = self.analytics.analyze_content_pillars(metrics_data)
        pillar_breakdown = {}

        for analysis in pillar_analyses:
            pillar_breakdown[analysis.pillar] = {
                "posts": analysis.post_count,
                "engagement": analysis.total_nova_score,
                "best_post": analysis.best_performing_post,
                "trend": analysis.pillar_trend
            }

        best_pillar = max(pillar_breakdown.items(), key=lambda x: x[1]["engagement"])[0] if pillar_breakdown else "unknown"

        # Day analysis
        day_engagement = defaultdict(float)
        for metric in metrics_data:
            day = metric.timestamp.strftime("%A")
            day_engagement[day] += metric.nova_score

        best_day = max(day_engagement.items(), key=lambda x: x[1])[0] if day_engagement else "unknown"

        # Top 3 posts
        top_posts = sorted(metrics_data, key=lambda x: x.nova_score, reverse=True)[:3]

        # Generate recommendations
        recommendations = self._generate_recommendations(metrics_data, pillar_analyses)

        # Industry benchmarking
        benchmark_analysis = self.analytics.benchmark_against_industry(metrics_data)

        return WeeklyDigest(
            week_start=week_start,
            week_end=week_end,
            total_posts=total_posts,
            total_engagement_score=total_engagement_score,
            best_performing_day=best_day,
            best_performing_pillar=best_pillar,
            best_performing_platform=best_platform,
            platform_breakdown=platform_breakdown,
            pillar_breakdown=pillar_breakdown,
            top_posts=[{
                "platform": post.platform,
                "nova_score": post.nova_score,
                "engagement_rate": post.engagement_rate,
                "timestamp": post.timestamp.isoformat(),
                "metrics": {
                    "likes": post.likes,
                    "comments": post.comments,
                    "saves": post.saves,
                    "shares": post.shares,
                    "reposts": post.reposts,
                    "views": post.views
                }
            } for post in top_posts],
            recommendations=recommendations,
            benchmark_analysis=benchmark_analysis
        )

    def _generate_recommendations(self, metrics_data: List[PlatformMetrics], pillar_analyses: List[ContentPillarAnalysis]) -> List[str]:
        """Generate AI-powered recommendations"""
        try:
            # Prepare data summary for AI analysis
            platform_summary = defaultdict(lambda: {"posts": 0, "avg_score": 0})
            for metric in metrics_data:
                platform_summary[metric.platform]["posts"] += 1
                platform_summary[metric.platform]["avg_score"] += metric.nova_score

            for platform_data in platform_summary.values():
                if platform_data["posts"] > 0:
                    platform_data["avg_score"] /= platform_data["posts"]

            pillar_summary = {p.pillar: {"avg_score": p.avg_nova_score, "trend": p.pillar_trend} for p in pillar_analyses}

            prompt = f"""Analyze this week's Apulu Records engagement data and provide 3-5 specific, actionable recommendations.

Platform Performance:
{json.dumps(dict(platform_summary), indent=2)}

Content Pillar Performance:
{json.dumps(pillar_summary, indent=2)}

Nova Scoring Formula: (likes×1) + (comments×3) + (saves×5) + (shares×4) + (reposts×4) + (views×0.01)

Platform Focus:
- Instagram: Prioritize saves (strongest value signal)
- TikTok: Focus on shares (virality)
- X: Optimize for reposts (reach amplification)
- Threads: Drive conversations (comments)
- Bluesky: Any engagement significant (smaller platform)

Content Pillars:
Monday=Awareness, Tuesday=Lyric, Wednesday=BTS, Thursday=Engagement, Friday=Conversion, Saturday=Audience, Sunday=Video

Provide specific recommendations in this format:
1. [Specific action based on data]
2. [Platform-specific optimization]
3. [Content pillar improvement]
4. [Timing or format suggestion]
5. [Community engagement strategy]
"""

            response = self.anthropic_client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse recommendations
            recommendations_text = response.content[0].text.strip()
            recommendations = [line.strip() for line in recommendations_text.split('\n') if line.strip() and any(char.isdigit() for char in line[:5])]

            return recommendations[:5]  # Limit to 5 recommendations

        except Exception as e:
            logger.error(f"Failed to generate AI recommendations: {e}")
            return [
                "Increase frequency on best performing platform",
                "Focus content on highest scoring pillar",
                "Optimize posting time based on engagement patterns",
                "Experiment with content formats that drive primary metrics",
                "Engage more actively with community comments"
            ]

    def format_digest_markdown(self, digest: WeeklyDigest) -> str:
        """Format digest as markdown report"""
        date_range = f"{digest.week_start.strftime('%Y-%m-%d')} to {digest.week_end.strftime('%Y-%m-%d')}"

        report = f"""# Apulu Records — Weekly Analytics | {date_range}

## Summary
- Total posts: {digest.total_posts}
- Total engagement score: {digest.total_engagement_score:.1f}
- Best performing day: {digest.best_performing_day}
- Best performing pillar: {digest.best_performing_pillar}
- Best performing platform: {digest.best_performing_platform}

## By Platform
| Platform | Posts | Engagement | Avg Score | Trend |
|----------|-------|-----------|-----------|-------|
"""

        for platform, data in digest.platform_breakdown.items():
            report += f"| {platform.title()} | {data['posts']} | {data['engagement']:.1f} | {data['avg_score']:.1f} | {data['trend']} |\n"

        report += f"""
## By Pillar
| Pillar | Posts | Engagement | Best Post |
|--------|-------|-----------|-----------|
"""

        for pillar, data in digest.pillar_breakdown.items():
            best_post = data['best_post']
            report += f"| {pillar.title()} | {data['posts']} | {data['engagement']:.1f} | {best_post['platform']} ({best_post['nova_score']:.1f}) |\n"

        report += f"""
## Top 3 Posts
"""

        for i, post in enumerate(digest.top_posts, 1):
            report += f"{i}. **{post['platform'].title()}** — Score: {post['nova_score']:.1f} — Engagement Rate: {post['engagement_rate']:.3f}\n"
            report += f"   - Likes: {post['metrics']['likes']}, Comments: {post['metrics']['comments']}, Saves: {post['metrics']['saves']}\n\n"

        report += f"""## Recommendations
"""

        for rec in digest.recommendations:
            report += f"- {rec}\n"

        report += f"""
## Industry Benchmarks
"""

        for metric, level in digest.benchmark_analysis.items():
            icon = "🟢" if level == "strong" else "🟡" if level == "average" else "🔴"
            report += f"- {metric.replace('_', ' ').title()}: {level} {icon}\n"

        return report

class APU148NovaAnalytics:
    """Main APU-148 Nova Engagement Analytics System"""

    def __init__(self):
        self.config = self._load_config()
        self.analytics_engine = NovaAnalyticsEngine()
        self.digest_generator = WeeklyDigestGenerator(self.analytics_engine)
        self.db_connection = None
        self._setup_database()

    def _load_config(self) -> Dict[str, Any]:
        """Load APU-148 configuration"""
        default_config = {
            "analytics": {
                "platforms": ["instagram", "tiktok", "x", "threads", "bluesky"],
                "digest_generation": True,
                "benchmark_tracking": True,
                "pillar_analysis": True
            },
            "reporting": {
                "weekly_digest_enabled": True,
                "auto_generate_markdown": True,
                "include_recommendations": True,
                "anthropic_recommendations": True
            },
            "api": {
                "base_url": "https://apulustudio.onrender.com/api",
                "timeout": 30,
                "retry_count": 3
            }
        }

        try:
            if APU148_CONFIG.exists():
                return {**default_config, **load_json(APU148_CONFIG)}
            else:
                save_json(APU148_CONFIG, default_config)
                return default_config
        except Exception as e:
            logger.error(f"Config load failed, using defaults: {e}")
            return default_config

    def _setup_database(self):
        """Setup APU-148 database"""
        try:
            self.db_connection = sqlite3.connect(str(APU148_DB), check_same_thread=False)
            cursor = self.db_connection.cursor()

            # Platform metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS platform_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    likes INTEGER DEFAULT 0,
                    comments INTEGER DEFAULT 0,
                    saves INTEGER DEFAULT 0,
                    shares INTEGER DEFAULT 0,
                    reposts INTEGER DEFAULT 0,
                    views INTEGER DEFAULT 0,
                    followers INTEGER DEFAULT 0,
                    nova_score REAL DEFAULT 0.0,
                    primary_metric_value INTEGER DEFAULT 0,
                    engagement_rate REAL DEFAULT 0.0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Weekly digests table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS weekly_digests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    week_start DATE NOT NULL,
                    week_end DATE NOT NULL,
                    total_posts INTEGER DEFAULT 0,
                    total_engagement_score REAL DEFAULT 0.0,
                    best_performing_day TEXT,
                    best_performing_pillar TEXT,
                    best_performing_platform TEXT,
                    digest_data TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            self.db_connection.commit()
            logger.info("APU-148 database initialized")

        except Exception as e:
            logger.error(f"Database setup failed: {e}")

    def collect_weekly_metrics(self) -> List[PlatformMetrics]:
        """Collect metrics from all platforms for weekly analysis"""
        all_metrics = []

        try:
            # Load credentials
            creds = load_json(VAWN_DIR / "config.json")
            access_token = creds.get("access_token", "")

            if not access_token:
                logger.error("No access token found")
                return all_metrics

            # Fetch metrics from each platform
            for platform in self.config["analytics"]["platforms"]:
                try:
                    platform_metrics = self.analytics_engine.fetch_platform_metrics(
                        platform, access_token, days_back=7
                    )
                    all_metrics.extend(platform_metrics)

                    # Store in database
                    self._store_platform_metrics(platform_metrics)

                    logger.info(f"Collected {len(platform_metrics)} metrics from {platform}")

                except Exception as e:
                    logger.error(f"Failed to collect metrics from {platform}: {e}")

            logger.info(f"Total metrics collected: {len(all_metrics)}")

        except Exception as e:
            logger.error(f"Failed to collect weekly metrics: {e}")

        return all_metrics

    def _store_platform_metrics(self, metrics: List[PlatformMetrics]):
        """Store platform metrics in database"""
        try:
            cursor = self.db_connection.cursor()

            for metric in metrics:
                cursor.execute('''
                    INSERT INTO platform_metrics
                    (platform, timestamp, likes, comments, saves, shares, reposts, views,
                     followers, nova_score, primary_metric_value, engagement_rate)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    metric.platform,
                    metric.timestamp,
                    metric.likes,
                    metric.comments,
                    metric.saves,
                    metric.shares,
                    metric.reposts,
                    metric.views,
                    metric.followers,
                    metric.nova_score,
                    metric.primary_metric_value,
                    metric.engagement_rate
                ))

            self.db_connection.commit()

        except Exception as e:
            logger.error(f"Failed to store metrics: {e}")

    def generate_weekly_digest(self) -> Optional[WeeklyDigest]:
        """Generate comprehensive weekly digest"""
        try:
            # Collect metrics
            metrics_data = self.collect_weekly_metrics()

            if not metrics_data:
                logger.warning("No metrics data available for digest generation")
                return None

            # Generate digest
            digest = self.digest_generator.generate_weekly_digest(metrics_data)

            if digest:
                # Store digest in database
                self._store_weekly_digest(digest)

                # Generate markdown report
                if self.config["reporting"]["auto_generate_markdown"]:
                    markdown_report = self.digest_generator.format_digest_markdown(digest)

                    # Save markdown file
                    report_filename = f"weekly_digest_{digest.week_start.strftime('%Y%m%d')}.md"
                    report_path = APU148_REPORTS_DIR / report_filename

                    with open(report_path, 'w', encoding='utf-8') as f:
                        f.write(markdown_report)

                    logger.info(f"Weekly digest saved: {report_path}")

                # Log to research logs
                self._log_digest_generation(digest)

                return digest

        except Exception as e:
            logger.error(f"Weekly digest generation failed: {e}")

        return None

    def _store_weekly_digest(self, digest: WeeklyDigest):
        """Store weekly digest in database"""
        try:
            cursor = self.db_connection.cursor()

            cursor.execute('''
                INSERT INTO weekly_digests
                (week_start, week_end, total_posts, total_engagement_score,
                 best_performing_day, best_performing_pillar, best_performing_platform, digest_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                digest.week_start.date(),
                digest.week_end.date(),
                digest.total_posts,
                digest.total_engagement_score,
                digest.best_performing_day,
                digest.best_performing_pillar,
                digest.best_performing_platform,
                json.dumps(asdict(digest), default=str)
            ))

            self.db_connection.commit()

        except Exception as e:
            logger.error(f"Failed to store weekly digest: {e}")

    def _log_digest_generation(self, digest: WeeklyDigest):
        """Log digest generation to research logs"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "apu_version": "148",
                "digest_summary": {
                    "week_start": digest.week_start.isoformat(),
                    "week_end": digest.week_end.isoformat(),
                    "total_posts": digest.total_posts,
                    "total_engagement_score": digest.total_engagement_score,
                    "best_platform": digest.best_performing_platform,
                    "best_pillar": digest.best_performing_pillar,
                    "recommendations_count": len(digest.recommendations)
                },
                "benchmark_results": digest.benchmark_analysis
            }

            # Update main log
            existing_log = load_json(APU148_LOG) if APU148_LOG.exists() else []
            existing_log.append(log_entry)
            save_json(APU148_LOG, existing_log[-50:])  # Keep last 50 entries

            # Update digest-specific log
            digest_log = load_json(APU148_DIGEST_LOG) if APU148_DIGEST_LOG.exists() else []
            digest_log.append(log_entry)
            save_json(APU148_DIGEST_LOG, digest_log[-20:])  # Keep last 20 digests

        except Exception as e:
            logger.error(f"Failed to log digest generation: {e}")

def main():
    """Main APU-148 execution"""
    print("\n=== APU-148 Nova Engagement Analytics System ===")
    print("Content analytics and weekly digest automation for Apulu Records")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    try:
        # Initialize system
        apu148 = APU148NovaAnalytics()

        print("✅ APU-148 Nova Analytics initialized")
        print("✅ Database connection established")
        print("✅ Analytics engine ready")
        print("✅ Digest generator configured")

        # Generate weekly digest
        print("\n📊 Generating weekly digest...")
        digest = apu148.generate_weekly_digest()

        if digest:
            print("✅ Weekly digest generated successfully!")
            print(f"\n📈 Digest Summary:")
            print(f"   Week: {digest.week_start.strftime('%Y-%m-%d')} to {digest.week_end.strftime('%Y-%m-%d')}")
            print(f"   Total Posts: {digest.total_posts}")
            print(f"   Total Engagement Score: {digest.total_engagement_score:.1f}")
            print(f"   Best Platform: {digest.best_performing_platform}")
            print(f"   Best Pillar: {digest.best_performing_pillar}")
            print(f"   Recommendations: {len(digest.recommendations)}")

            # Show benchmarks
            print(f"\n🎯 Industry Benchmarks:")
            for metric, level in digest.benchmark_analysis.items():
                icon = "🟢" if level == "strong" else "🟡" if level == "average" else "🔴"
                print(f"   {icon} {metric.replace('_', ' ').title()}: {level}")

            # Show top recommendation
            if digest.recommendations:
                print(f"\n💡 Top Recommendation:")
                print(f"   {digest.recommendations[0]}")

        else:
            print("⚠️ No digest generated - insufficient data")

        print(f"\n📂 Reports saved to: {APU148_REPORTS_DIR}")
        print(f"📊 Analytics data: {APU148_DB}")
        print(f"📋 Log files: {APU148_LOG}")

        return {
            "status": "success",
            "digest_generated": digest is not None,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"\n❌ APU-148 execution failed: {e}")
        logger.error(f"APU-148 failed: {e}\n{traceback.format_exc()}")

        return {
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    result = main()
    sys.exit(0 if result["status"] == "success" else 1)