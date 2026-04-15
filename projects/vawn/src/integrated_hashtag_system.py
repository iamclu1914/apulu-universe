"""
integrated_hashtag_system.py — Integrated hashtag system with validation and optimization
Created for: APU-150 hashtag-scan enhancement
Author: Sage - Content Agent

Combines enhanced scanning, validation, platform optimization, and error handling
into a unified system for reliable hashtag generation and quality control.
"""

import json
import sys
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import VAWN_DIR, RESEARCH_DIR, load_json, save_json

# Import our enhancement modules
sys.path.append(str(VAWN_DIR / "src"))
try:
    from enhanced_scan_hashtags import EnhancedHashtagScanner
    from hashtag_validator import HashtagValidator
    from platform_optimizer import PlatformOptimizer
    from enhanced_performance_tracker import EnhancedPerformanceTracker
except ImportError as e:
    print(f"[ERROR] Could not import required modules: {e}")
    sys.exit(1)


class IntegratedHashtagSystem:
    """Unified hashtag generation and optimization system with comprehensive error handling"""

    def __init__(self):
        self.scanner = EnhancedHashtagScanner()
        self.validator = HashtagValidator()
        self.optimizer = PlatformOptimizer()
        self.performance_tracker = EnhancedPerformanceTracker()

        self.processing_log = []
        self.error_log = []
        self.quality_metrics = {}

    def generate_and_optimize_hashtags(self, max_retries: int = 3) -> Dict:
        """
        Generate, validate, and optimize hashtags with comprehensive error handling

        Args:
            max_retries: Maximum number of retry attempts for failed generations

        Returns:
            Dict containing results, errors, and quality metrics
        """
        print(f"\n[*] Integrated Hashtag System - APU-150")
        print(f"[DATE] {date.today()}")
        print("=" * 60)

        results = {
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "generated_hashtags": {},
            "validated_hashtags": {},
            "optimized_hashtags": {},
            "quality_metrics": {},
            "errors": [],
            "warnings": [],
            "performance_data": {},
            "processing_log": []
        }

        retry_count = 0
        generation_successful = False

        while retry_count < max_retries and not generation_successful:
            try:
                print(f"\n[ATTEMPT {retry_count + 1}] Generating hashtags...")

                # Step 1: Generate hashtags using enhanced scanner
                generation_result = self._safe_generate_hashtags()
                if generation_result["success"]:
                    results["generated_hashtags"] = generation_result["data"]
                    generation_successful = True
                    print(f"[OK] Hashtag generation successful")
                else:
                    results["errors"].extend(generation_result["errors"])
                    retry_count += 1
                    print(f"[WARNING] Generation failed, retrying... ({retry_count}/{max_retries})")
                    continue

            except Exception as e:
                error_msg = f"Generation attempt {retry_count + 1} failed: {str(e)}"
                results["errors"].append(error_msg)
                self.error_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "error": error_msg,
                    "step": "generation"
                })
                retry_count += 1

        if not generation_successful:
            results["errors"].append(f"Failed to generate hashtags after {max_retries} attempts")
            return results

        try:
            # Step 2: Validate generated hashtags
            print(f"\n[VALIDATION] Validating hashtag quality...")
            validation_result = self._safe_validate_hashtags(results["generated_hashtags"])
            results["validated_hashtags"] = validation_result["data"]
            results["quality_metrics"].update(validation_result["metrics"])

            if validation_result["errors"]:
                results["warnings"].extend(validation_result["errors"])

            print(f"[OK] Validation complete - {validation_result['metrics']['success_rate']:.1%} success rate")

        except Exception as e:
            error_msg = f"Validation failed: {str(e)}"
            results["errors"].append(error_msg)
            results["validated_hashtags"] = results["generated_hashtags"]  # Fallback

        try:
            # Step 3: Optimize for platforms
            print(f"\n[OPTIMIZATION] Optimizing for platform-specific performance...")
            optimization_result = self._safe_optimize_hashtags(results["validated_hashtags"])
            results["optimized_hashtags"] = optimization_result["data"]
            results["quality_metrics"].update(optimization_result["metrics"])

            if optimization_result["errors"]:
                results["warnings"].extend(optimization_result["errors"])

            print(f"[OK] Platform optimization complete")

        except Exception as e:
            error_msg = f"Optimization failed: {str(e)}"
            results["errors"].append(error_msg)
            results["optimized_hashtags"] = results["validated_hashtags"]  # Fallback

        try:
            # Step 4: Update performance tracking
            print(f"\n[PERFORMANCE] Updating performance metrics...")
            performance_result = self._safe_update_performance()
            results["performance_data"] = performance_result["data"]

            if performance_result["errors"]:
                results["warnings"].extend(performance_result["errors"])

            print(f"[OK] Performance tracking updated")

        except Exception as e:
            error_msg = f"Performance tracking failed: {str(e)}"
            results["warnings"].append(error_msg)  # Non-critical

        # Step 5: Save results and apply fixes
        try:
            print(f"\n[SAVE] Applying optimized hashtags...")
            save_result = self._safe_save_optimized_hashtags(results["optimized_hashtags"])

            if save_result["success"]:
                results["success"] = True
                print(f"[OK] Optimized hashtags saved successfully")
            else:
                results["errors"].extend(save_result["errors"])

        except Exception as e:
            error_msg = f"Save operation failed: {str(e)}"
            results["errors"].append(error_msg)

        # Generate comprehensive report
        results["processing_log"] = self.processing_log
        results["error_log"] = self.error_log
        results["summary"] = self._generate_execution_summary(results)

        return results

    def _safe_generate_hashtags(self) -> Dict:
        """Safely generate hashtags with error handling"""
        try:
            generation_result = self.scanner.scan_and_analyze_hashtags()

            self.processing_log.append({
                "step": "generation",
                "timestamp": datetime.now().isoformat(),
                "status": "success",
                "details": f"Generated hashtags for {len(generation_result['parsed_hashtags'])} platforms"
            })

            return {
                "success": True,
                "data": generation_result["parsed_hashtags"],
                "errors": [],
                "raw_response": generation_result.get("raw_response", "")
            }

        except Exception as e:
            self.processing_log.append({
                "step": "generation",
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "details": str(e)
            })

            return {
                "success": False,
                "data": {},
                "errors": [f"Generation error: {str(e)}"]
            }

    def _safe_validate_hashtags(self, hashtags_by_platform: Dict[str, List[str]]) -> Dict:
        """Safely validate hashtags with error handling"""
        validated_data = {}
        validation_metrics = {
            "total_hashtags": 0,
            "valid_hashtags": 0,
            "fixed_hashtags": 0,
            "success_rate": 0.0
        }
        errors = []

        for platform, hashtags in hashtags_by_platform.items():
            try:
                # Validate hashtag set
                validation_results = self.validator.validate_hashtag_set(hashtags, platform.lower())

                # Auto-fix issues
                fixed_hashtags = self.validator.auto_fix_hashtags(hashtags, platform.lower())

                validated_data[platform] = fixed_hashtags

                # Track metrics
                valid_count = sum(1 for result in validation_results.values() if result.is_valid)
                fixed_count = len([h for h, orig in zip(fixed_hashtags, hashtags) if h != orig])

                validation_metrics["total_hashtags"] += len(hashtags)
                validation_metrics["valid_hashtags"] += valid_count
                validation_metrics["fixed_hashtags"] += fixed_count

                self.processing_log.append({
                    "step": "validation",
                    "platform": platform,
                    "timestamp": datetime.now().isoformat(),
                    "status": "success",
                    "details": f"{valid_count}/{len(hashtags)} valid, {fixed_count} fixed"
                })

            except Exception as e:
                error_msg = f"Validation error for {platform}: {str(e)}"
                errors.append(error_msg)
                validated_data[platform] = hashtags  # Fallback to original

                self.processing_log.append({
                    "step": "validation",
                    "platform": platform,
                    "timestamp": datetime.now().isoformat(),
                    "status": "error",
                    "details": error_msg
                })

        # Calculate overall success rate
        if validation_metrics["total_hashtags"] > 0:
            validation_metrics["success_rate"] = validation_metrics["valid_hashtags"] / validation_metrics["total_hashtags"]

        return {
            "data": validated_data,
            "metrics": validation_metrics,
            "errors": errors
        }

    def _safe_optimize_hashtags(self, hashtags_by_platform: Dict[str, List[str]]) -> Dict:
        """Safely optimize hashtags for platforms with error handling"""
        optimized_data = {}
        optimization_metrics = {
            "platforms_optimized": 0,
            "avg_optimization_score": 0.0,
            "top_performers": []
        }
        errors = []

        total_score = 0.0
        platform_count = 0

        for platform, hashtags in hashtags_by_platform.items():
            try:
                # Optimize for specific platform
                optimization_result = self.optimizer.optimize_hashtags_for_platform(
                    hashtags, platform.lower()
                )

                # Extract optimized hashtags
                optimized_hashtags = [h["hashtag"] for h in optimization_result["selected_hashtags"]]
                optimized_data[platform] = optimized_hashtags

                # Track performance
                avg_score = sum(h["score"] for h in optimization_result["selected_hashtags"]) / max(len(optimization_result["selected_hashtags"]), 1)
                total_score += avg_score
                platform_count += 1

                optimization_metrics["top_performers"].append({
                    "platform": platform,
                    "avg_score": avg_score,
                    "best_hashtag": optimization_result["selected_hashtags"][0]["hashtag"] if optimization_result["selected_hashtags"] else None
                })

                self.processing_log.append({
                    "step": "optimization",
                    "platform": platform,
                    "timestamp": datetime.now().isoformat(),
                    "status": "success",
                    "details": f"Optimized to {len(optimized_hashtags)} hashtags (avg score: {avg_score:.1f})"
                })

            except Exception as e:
                error_msg = f"Optimization error for {platform}: {str(e)}"
                errors.append(error_msg)
                optimized_data[platform] = hashtags  # Fallback to original

                self.processing_log.append({
                    "step": "optimization",
                    "platform": platform,
                    "timestamp": datetime.now().isoformat(),
                    "status": "error",
                    "details": error_msg
                })

        # Calculate overall metrics
        optimization_metrics["platforms_optimized"] = platform_count
        if platform_count > 0:
            optimization_metrics["avg_optimization_score"] = total_score / platform_count

        # Sort top performers
        optimization_metrics["top_performers"].sort(key=lambda x: x["avg_score"], reverse=True)

        return {
            "data": optimized_data,
            "metrics": optimization_metrics,
            "errors": errors
        }

    def _safe_update_performance(self) -> Dict:
        """Safely update performance tracking with error handling"""
        try:
            performance_report = self.performance_tracker.generate_enhanced_performance_report()

            self.processing_log.append({
                "step": "performance_tracking",
                "timestamp": datetime.now().isoformat(),
                "status": "success",
                "details": f"Updated performance data for {performance_report['summary']['platforms_analyzed']} platforms"
            })

            return {
                "success": True,
                "data": performance_report["summary"],
                "errors": []
            }

        except Exception as e:
            error_msg = f"Performance tracking error: {str(e)}"

            self.processing_log.append({
                "step": "performance_tracking",
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "details": error_msg
            })

            return {
                "success": False,
                "data": {},
                "errors": [error_msg]
            }

    def _safe_save_optimized_hashtags(self, optimized_hashtags: Dict[str, List[str]]) -> Dict:
        """Safely save optimized hashtags with error handling"""
        success_count = 0
        errors = []

        hashtags_dir = VAWN_DIR / "Social_Media_Exports" / "Trending_Hashtags"

        for platform, hashtags in optimized_hashtags.items():
            try:
                platform_dir = hashtags_dir / platform
                platform_dir.mkdir(parents=True, exist_ok=True)

                hashtag_file = platform_dir / "hashtags.txt"
                hashtag_file.write_text("\n".join(hashtags), encoding="utf-8")

                success_count += 1

                self.processing_log.append({
                    "step": "save",
                    "platform": platform,
                    "timestamp": datetime.now().isoformat(),
                    "status": "success",
                    "details": f"Saved {len(hashtags)} hashtags to {hashtag_file}"
                })

            except Exception as e:
                error_msg = f"Save error for {platform}: {str(e)}"
                errors.append(error_msg)

                self.processing_log.append({
                    "step": "save",
                    "platform": platform,
                    "timestamp": datetime.now().isoformat(),
                    "status": "error",
                    "details": error_msg
                })

        return {
            "success": success_count == len(optimized_hashtags),
            "platforms_saved": success_count,
            "total_platforms": len(optimized_hashtags),
            "errors": errors
        }

    def _generate_execution_summary(self, results: Dict) -> Dict:
        """Generate comprehensive execution summary"""

        # Count successes and failures
        total_steps = len(self.processing_log)
        successful_steps = len([log for log in self.processing_log if log["status"] == "success"])
        error_steps = total_steps - successful_steps

        # Platform analysis
        platforms_processed = len(results.get("optimized_hashtags", {}))
        total_hashtags = sum(len(hashtags) for hashtags in results.get("optimized_hashtags", {}).values())

        # Quality metrics
        quality_metrics = results.get("quality_metrics", {})
        validation_rate = quality_metrics.get("success_rate", 0.0)
        optimization_score = quality_metrics.get("avg_optimization_score", 0.0)

        return {
            "overall_success": results["success"],
            "execution_stats": {
                "total_steps": total_steps,
                "successful_steps": successful_steps,
                "error_steps": error_steps,
                "success_rate": successful_steps / max(total_steps, 1)
            },
            "hashtag_stats": {
                "platforms_processed": platforms_processed,
                "total_hashtags_generated": total_hashtags,
                "validation_success_rate": validation_rate,
                "optimization_score": optimization_score
            },
            "error_summary": {
                "total_errors": len(results["errors"]),
                "total_warnings": len(results["warnings"]),
                "critical_errors": [e for e in results["errors"] if "generation" in e.lower() or "save" in e.lower()]
            },
            "recommendations": self._generate_recommendations_from_results(results)
        }

    def _generate_recommendations_from_results(self, results: Dict) -> List[str]:
        """Generate recommendations based on execution results"""
        recommendations = []

        # Error-based recommendations
        if results["errors"]:
            recommendations.append("[ERROR] Review error log for critical issues that need attention")

        if len(results["errors"]) > 3:
            recommendations.append("[WARNING] Multiple errors detected - system may need maintenance")

        # Performance-based recommendations
        quality_metrics = results.get("quality_metrics", {})

        validation_rate = quality_metrics.get("success_rate", 1.0)
        if validation_rate < 0.9:
            recommendations.append(f"[REVIEW] Validation rate ({validation_rate:.1%}) below optimal - review AI prompting")

        optimization_score = quality_metrics.get("avg_optimization_score", 0.0)
        if optimization_score > 2.0:
            recommendations.append(f"[EXCELLENT] Optimization performance ({optimization_score:.1f}) - current strategy is working well")
        elif optimization_score < 1.5:
            recommendations.append(f"[IMPROVE] Optimization score ({optimization_score:.1f}) has room for improvement")

        # Success-based recommendations
        if results["success"]:
            recommendations.append("[SUCCESS] System operating successfully - monitor performance trends")
            recommendations.append("[SCHEDULE] Consider running weekly to maintain hashtag freshness")

        # Platform-specific recommendations
        platforms = results.get("optimized_hashtags", {})
        if "instagram" in platforms and len(platforms["instagram"]) < 10:
            recommendations.append("[INSTAGRAM] Consider using more hashtags (10-15 recommended)")

        if "tiktok" in platforms and len(platforms["tiktok"]) > 5:
            recommendations.append("[TIKTOK] Consider using fewer hashtags (3-5 recommended)")

        return recommendations


def main():
    """Main integrated system execution"""
    system = IntegratedHashtagSystem()

    try:
        results = system.generate_and_optimize_hashtags(max_retries=2)

        # Display comprehensive summary
        summary = results["summary"]

        print(f"\n[EXECUTION SUMMARY]")
        print(f"Overall Success: {'[YES]' if summary['overall_success'] else '[NO]'}")
        print(f"Steps Completed: {summary['execution_stats']['successful_steps']}/{summary['execution_stats']['total_steps']}")
        print(f"Platforms Processed: {summary['hashtag_stats']['platforms_processed']}")
        print(f"Total Hashtags: {summary['hashtag_stats']['total_hashtags_generated']}")
        print(f"Validation Rate: {summary['hashtag_stats']['validation_success_rate']:.1%}")
        print(f"Optimization Score: {summary['hashtag_stats']['optimization_score']:.1f}")

        if results["errors"]:
            print(f"\nERRORS ({len(results['errors'])}):")
            for error in results["errors"][:3]:  # Show first 3
                print(f"  • {error}")

            if len(results["errors"]) > 3:
                print(f"  ... and {len(results['errors']) - 3} more")

        if results["warnings"]:
            print(f"\nWARNINGS ({len(results['warnings'])}):")
            for warning in results["warnings"][:2]:  # Show first 2
                print(f"  • {warning}")

        print(f"\nRECOMMENDATIONS:")
        for rec in summary["recommendations"][:5]:
            # Remove any potential Unicode characters from recommendations
            clean_rec = rec.encode('ascii', 'ignore').decode('ascii')
            print(f"  {clean_rec}")

        # Save comprehensive log
        log_path = RESEARCH_DIR / "apu150_integrated_system_log.json"
        save_json(log_path, results)
        print(f"\n[OK] Comprehensive log saved to {log_path}")

        return results

    except Exception as e:
        print(f"[CRITICAL ERROR] Integrated system failed: {e}")
        return None


if __name__ == "__main__":
    main()