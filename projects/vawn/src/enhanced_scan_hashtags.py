"""
enhanced_scan_hashtags.py — AI-powered hashtag scanning with performance feedback integration
Created by: Sage - Content Agent (APU-26)

Enhanced version of scan_hashtags.py that integrates performance analytics,
quality scoring, and competitive intelligence to optimize hashtag discovery.
"""

import json
import sys
from datetime import date, datetime
from pathlib import Path
import anthropic

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import VAWN_DIR, RESEARCH_DIR, load_json, save_json

# Import our enhancement modules
sys.path.append(str(VAWN_DIR / "src"))
try:
    from hashtag_analyzer import analyze_hashtag_set, BRAND_KEYWORDS, HIGH_COMPETITION
    from hashtag_performance_tracker import HashtagPerformanceTracker
    from hashtag_file_manager import HashtagFileManager
except ImportError as e:
    print(f"[WARNING] Could not import enhancement modules: {e}")
    print("[INFO] Running in fallback mode...")

HASHTAGS_DIR = VAWN_DIR / "Social_Media_Exports" / "Trending_Hashtags"
ENHANCED_INSIGHTS_LOG = RESEARCH_DIR / "enhanced_hashtag_insights.json"

PLATFORMS = {
    "Instagram": {"count": 15, "note": "mix of high-volume, mid-range, and niche hip-hop/music hashtags"},
    "TikTok":    {"count": 5,  "note": "3-5 trending hashtags, prioritize viral music/hip-hop tags"},
    "Threads":   {"count": 2,  "note": "1-2 hashtags max, conversational music/culture tags"},
    "X":         {"count": 2,  "note": "1-2 hashtags embedded naturally, trending hip-hop/music tags"},
    "Bluesky":   {"count": 3,  "note": "1-3 hashtags, music/hip-hop community tags"},
}


class EnhancedHashtagScanner:
    """Enhanced hashtag scanning with AI feedback integration"""

    def __init__(self):
        self.performance_tracker = None
        self.file_manager = None
        self.insights = {}

        # Initialize enhancement modules if available
        try:
            self.performance_tracker = HashtagPerformanceTracker()
            self.file_manager = HashtagFileManager()
            self.load_performance_insights()
        except:
            print("[INFO] Running without enhancement modules")

    def load_performance_insights(self):
        """Load performance insights to inform AI prompting."""
        if not self.performance_tracker:
            return

        try:
            # Load performance data
            performance_report = self.performance_tracker.generate_performance_report()

            # Extract key insights for AI prompting
            self.insights = {
                "top_performing_hashtags": self._extract_top_performers(performance_report),
                "underperforming_hashtags": self._extract_underperformers(performance_report),
                "trending_opportunities": performance_report.get("trending_opportunities", []),
                "platform_preferences": self._analyze_platform_preferences(performance_report)
            }

            # Save insights
            save_json(ENHANCED_INSIGHTS_LOG, {
                "last_updated": datetime.now().isoformat(),
                "insights": self.insights
            })

        except Exception as e:
            print(f"[WARNING] Could not load performance insights: {e}")
            self.insights = {}

    def _extract_top_performers(self, report: dict) -> list:
        """Extract top performing hashtags from performance report."""
        top_performers = []

        platform_insights = report.get("platform_insights", {})
        for platform, insights in platform_insights.items():
            if "top_performing_hashtags" in insights:
                for hashtag, score in insights["top_performing_hashtags"][:3]:
                    top_performers.append({
                        "hashtag": hashtag,
                        "platform": platform,
                        "score": score
                    })

        return top_performers

    def _extract_underperformers(self, report: dict) -> list:
        """Extract underperforming hashtags to avoid."""
        underperformers = []

        platform_insights = report.get("platform_insights", {})
        for platform, insights in platform_insights.items():
            if "underperforming_hashtags" in insights:
                for hashtag, score in insights["underperforming_hashtags"][-2:]:  # Bottom 2
                    underperformers.append({
                        "hashtag": hashtag,
                        "platform": platform,
                        "score": score
                    })

        return underperformers

    def _analyze_platform_preferences(self, report: dict) -> dict:
        """Analyze platform-specific hashtag preferences."""
        preferences = {}

        platform_insights = report.get("platform_insights", {})
        for platform, insights in platform_insights.items():
            preferences[platform] = {
                "optimal_count": insights.get("optimal_hashtag_count", 5),
                "top_hashtags": [h[0] for h in insights.get("top_performing_hashtags", [])[:3]]
            }

        return preferences

    def generate_enhanced_prompt(self) -> str:
        """Generate AI prompt enhanced with performance data and brand intelligence."""
        today = date.today().strftime("%B %d, %Y")

        # Base prompt structure
        base_prompt = f"""Today is {today}. You are a data-driven social media strategist for Vawn, a Brooklyn/Atlanta hip-hop artist.

ARTIST PROFILE:
- Sound: psychedelic boom bap, authoritative Atlanta trap, polished trap-soul, orchestral soul hip-hop
- Themes: Fear of Failure, Dependability, Love, Journey
- Brand: anti-hype, quiet authority, pattern recognition, long-game mentality
- Location: Brooklyn-raised, Atlanta-based

PERFORMANCE INTELLIGENCE:"""

        # Add performance insights if available
        if self.insights.get("top_performing_hashtags"):
            base_prompt += f"\n\nTOP PERFORMING HASHTAGS (prioritize these types):"
            for performer in self.insights["top_performing_hashtags"][:5]:
                base_prompt += f"\n- {performer['hashtag']} on {performer['platform']} (score: {performer['score']:.2f})"

        if self.insights.get("underperforming_hashtags"):
            base_prompt += f"\n\nAVOID THESE UNDERPERFORMERS:"
            for underperformer in self.insights["underperforming_hashtags"][:3]:
                base_prompt += f"\n- {underperformer['hashtag']} (low engagement)"

        if self.insights.get("trending_opportunities"):
            base_prompt += f"\n\nTRENDING OPPORTUNITIES TO EXPLORE:"
            for opportunity in self.insights["trending_opportunities"][:3]:
                base_prompt += f"\n- {opportunity.get('hashtag', '')} on {opportunity.get('platform', '')}"

        # Brand-aligned keywords to prioritize
        base_prompt += f"""

BRAND-ALIGNED KEYWORDS TO PRIORITIZE:
Core Sound: psychedelic, boom bap, atlanta, trap, soul, orchestral, conscious, lyrical
Geography: brooklyn, atlanta, nyc, atl, east coast, south
Values: independent, authentic, underground, indie, anti-hype, genuine

AVOID HIGH COMPETITION: #music, #rap, #hiphop, #newmusic, #song, #artist, #rapper (use sparingly)

Generate currently trending hashtags that align with Vawn's brand and performance data.
Focus on: brand-specific terms, geographic relevance, niche communities, emerging trends.

Return ONLY this exact format — one hashtag per line under each header:"""

        # Platform-specific instructions enhanced with performance data
        for platform, config in PLATFORMS.items():
            base_prompt += f"\n\n{platform.upper()}:\n"

            # Add performance-based guidance
            if platform.lower() in self.insights.get("platform_preferences", {}):
                prefs = self.insights["platform_preferences"][platform.lower()]
                if prefs.get("top_hashtags"):
                    base_prompt += f"(Prioritize types like: {', '.join(prefs['top_hashtags'][:2])})\n"

            base_prompt += f"{config['note']}\n"
            base_prompt += f"Generate {config['count']} hashtags with brand alignment and trend potential."

        return base_prompt

    def scan_and_analyze_hashtags(self) -> dict:
        """Execute enhanced hashtag scanning with quality analysis."""
        config = load_json(VAWN_DIR / "config.json")
        client = anthropic.Anthropic(api_key=config["anthropic_api_key"])

        # Generate enhanced prompt
        enhanced_prompt = self.generate_enhanced_prompt()

        print(f"[ENHANCED SCAN] Using performance-informed AI prompting...")

        # Get AI response
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            messages=[{"role": "user", "content": enhanced_prompt}]
        )

        raw_response = message.content[0].text.strip()
        print(f"[AI RESPONSE] Generated trending hashtags with brand intelligence")

        # Parse and analyze response
        parsed_hashtags = self.parse_response(raw_response)
        analyzed_results = self.analyze_parsed_hashtags(parsed_hashtags)

        return {
            "raw_response": raw_response,
            "parsed_hashtags": parsed_hashtags,
            "analysis": analyzed_results,
            "prompt_used": enhanced_prompt,
            "enhancement_data": self.insights
        }

    def parse_response(self, raw_response: str) -> dict:
        """Parse AI response into platform-specific hashtag lists."""
        import re

        platform_hashtags = {}
        platform_names = list(PLATFORMS.keys())
        # Updated pattern to handle both "PLATFORM:" and "## PLATFORM:" formats
        marker_pattern = "|".join(f"(##\\s*{re.escape(p.upper())}|{re.escape(p.upper())})" for p in platform_names)

        for platform in platform_names:
            # Try both markdown header format and plain format
            patterns = [
                rf'(?m)^##\s*{re.escape(platform.upper())}:\s*(.*?)(?=^##\s*(?:{"|".join(re.escape(p.upper()) for p in platform_names)}):|\Z)',
                rf'(?m)^{re.escape(platform.upper())}:\s*(.*?)(?=^(?:{"|".join(re.escape(p.upper()) for p in platform_names)}):|\Z)'
            ]

            match = None
            for pattern in patterns:
                match = re.search(pattern, raw_response, re.DOTALL)
                if match:
                    break

            if match:
                content = match.group(1).strip()
                # Extract hashtags, skipping lines that are just instructions
                hashtags = []
                for line in content.splitlines():
                    line = line.strip()
                    if line.startswith("#") and len(line) > 1:
                        hashtags.append(line)

                platform_hashtags[platform] = hashtags
            else:
                platform_hashtags[platform] = []
                print(f"[WARNING] No hashtags parsed for {platform}")

        return platform_hashtags

    def analyze_parsed_hashtags(self, platform_hashtags: dict) -> dict:
        """Analyze quality and relevance of generated hashtags."""
        analysis_results = {}

        for platform, hashtags in platform_hashtags.items():
            if not hashtags:
                continue

            try:
                # Analyze hashtag quality using our analyzer
                scores = analyze_hashtag_set(hashtags, platform.lower())

                analysis_results[platform] = {
                    "total_hashtags": len(hashtags),
                    "avg_relevance": sum(s.relevance_score for s in scores) / len(scores) if scores else 0,
                    "avg_competition": sum(s.competition_score for s in scores) / len(scores) if scores else 0,
                    "avg_overall_score": sum(s.overall_score for s in scores) / len(scores) if scores else 0,
                    "top_quality_hashtags": [s.hashtag for s in scores[:5]],
                    "quality_breakdown": [
                        {
                            "hashtag": s.hashtag,
                            "relevance": s.relevance_score,
                            "overall_score": s.overall_score,
                            "reasoning": s.reasoning
                        }
                        for s in scores
                    ]
                }

            except Exception as e:
                print(f"[WARNING] Could not analyze {platform} hashtags: {e}")
                analysis_results[platform] = {
                    "total_hashtags": len(hashtags),
                    "error": str(e)
                }

        return analysis_results

    def save_enhanced_results(self, results: dict):
        """Save hashtags and create file management snapshots."""
        # Save traditional hashtag files
        for platform, hashtags in results["parsed_hashtags"].items():
            if not hashtags:
                continue

            platform_dir = HASHTAGS_DIR / platform
            platform_dir.mkdir(parents=True, exist_ok=True)

            hashtag_file = platform_dir / "hashtags.txt"
            hashtag_file.write_text("\n".join(hashtags), encoding="utf-8")

            print(f"[OK] {platform}: {len(hashtags)} hashtags saved -> {hashtag_file}")

        # Create file management snapshot
        if self.file_manager:
            try:
                self.file_manager.create_daily_snapshot()
                print(f"[OK] Daily snapshot created")
            except Exception as e:
                print(f"[WARNING] Could not create snapshot: {e}")

        # Save comprehensive analysis
        analysis_log = RESEARCH_DIR / "enhanced_scan_analysis.json"
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "date": str(date.today()),
            "results": results
        }

        # Load existing log
        if analysis_log.exists():
            existing_data = load_json(analysis_log)
            if not isinstance(existing_data, list):
                existing_data = []
        else:
            existing_data = []

        existing_data.append(log_data)

        # Keep only last 30 entries
        existing_data = existing_data[-30:]

        save_json(analysis_log, existing_data)
        print(f"[OK] Enhanced analysis saved to {analysis_log}")


def main():
    """Main enhanced scanning execution."""
    print(f"\n[*] Enhanced Hashtag Scanner - APU-26")
    print(f"[DATE] {date.today()}")
    print("=" * 60)

    scanner = EnhancedHashtagScanner()

    try:
        # Execute enhanced scanning
        results = scanner.scan_and_analyze_hashtags()

        # Display analysis summary
        print(f"\n[QUALITY ANALYSIS]")
        for platform, analysis in results["analysis"].items():
            if "error" in analysis:
                print(f"{platform}: Analysis failed - {analysis['error']}")
            else:
                relevance = analysis["avg_relevance"]
                overall = analysis["avg_overall_score"]
                print(f"{platform}: Relevance {relevance:.2f} | Overall {overall:.2f} | Count {analysis['total_hashtags']}")

        # Save results
        scanner.save_enhanced_results(results)

        # Performance summary
        total_hashtags = sum(len(h) for h in results["parsed_hashtags"].values())
        analyzed_platforms = len([p for p in results["analysis"].values() if "error" not in p])

        print(f"\n[SUMMARY]")
        print(f"Total Hashtags: {total_hashtags}")
        print(f"Platforms Analyzed: {analyzed_platforms}/{len(PLATFORMS)}")
        print(f"Performance Data: {'YES' if scanner.insights else 'NO'}")
        print(f"Enhanced Prompting: YES")

        print(f"\n[OK] Enhanced hashtag scanning complete!")

        return results

    except Exception as e:
        print(f"[ERROR] Enhanced scanning failed: {e}")
        # Fallback to basic scanning
        print(f"[FALLBACK] Running basic hashtag scan...")

        # Import and run original scan function
        from scan_hashtags import fetch_hashtags
        fetch_hashtags()

        return None


if __name__ == "__main__":
    main()