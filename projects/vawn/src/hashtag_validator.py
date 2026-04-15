"""
hashtag_validator.py — Quality control and validation system for AI-generated hashtags
Created for: APU-150 hashtag-scan enhancement
Author: Sage - Content Agent

Provides spell-check, format validation, and brand alignment checks for hashtags.
"""

import re
import json
from pathlib import Path
from difflib import SequenceMatcher
from typing import List, Dict, Tuple, Optional

# Brand-specific terms and variations
BRAND_KEYWORDS = {
    "vawn": ["vawn", "vawnmusic", "vawnrap"],
    "apulu": ["apulu", "apulurecords", "apulurec"],
    "boombap": ["boombap", "boombaphis", "boombaprap", "boombapcity"],  # Common variations/typos
    "orchestral": ["orchestral", "orchestralrap", "orchestralhiphop"],
    "psychedelic": ["psychedelic", "psychedelicrap", "psychedelichiphop"],
    "trap": ["trap", "trapmusic", "traprap", "trapsoul", "trapsouls"],
    "brooklyn": ["brooklyn", "brooklynrap", "brooklynhiphop", "bklyn"],
    "atlanta": ["atlanta", "atlantarap", "atlantahiphop", "atl", "atlhiphop"],
    "conscious": ["conscious", "consciousrap", "consciouship"],
    "lyrical": ["lyrical", "lyricalrap", "lyricalhiphop", "lyricist"],
}

# Common hashtag patterns and their corrections
COMMON_CORRECTIONS = {
    "boombaphis": "boombap",
    "psychedelichain": "psychedelichiphop",
    "orchestralrap": "orchestralrap",  # Already correct
    "brooklynhip": "brooklynhiphop",
    "atlantahip": "atlantahiphop",
    "rapmusics": "rapmusic",
    "hiphopmusics": "hiphopmusic",
}

# Platform-specific validation rules
PLATFORM_RULES = {
    "instagram": {
        "max_length": 100,
        "min_length": 3,
        "avoid_patterns": ["#music#", "##", "_#"],
        "required_format": r"^#[a-zA-Z0-9]+$"
    },
    "tiktok": {
        "max_length": 80,
        "min_length": 3,
        "avoid_patterns": ["#music#", "##", "_#"],
        "required_format": r"^#[a-zA-Z0-9]+$"
    },
    "x": {
        "max_length": 100,
        "min_length": 3,
        "avoid_patterns": ["#music#", "##", "_#"],
        "required_format": r"^#[a-zA-Z0-9]+$"
    },
    "threads": {
        "max_length": 80,
        "min_length": 3,
        "avoid_patterns": ["#music#", "##", "_#"],
        "required_format": r"^#[a-zA-Z0-9]+$"
    },
    "bluesky": {
        "max_length": 64,
        "min_length": 3,
        "avoid_patterns": ["#music#", "##", "_#"],
        "required_format": r"^#[a-zA-Z0-9]+$"
    }
}


class HashtagValidationResult:
    """Represents the result of hashtag validation"""

    def __init__(self, hashtag: str, is_valid: bool, issues: List[str] = None,
                 suggested_correction: str = None, confidence_score: float = 1.0):
        self.hashtag = hashtag
        self.is_valid = is_valid
        self.issues = issues or []
        self.suggested_correction = suggested_correction
        self.confidence_score = confidence_score

    def to_dict(self) -> dict:
        return {
            "hashtag": self.hashtag,
            "is_valid": self.is_valid,
            "issues": self.issues,
            "suggested_correction": self.suggested_correction,
            "confidence_score": self.confidence_score
        }


class HashtagValidator:
    """Advanced validation system for AI-generated hashtags"""

    def __init__(self):
        self.validation_log = []

    def validate_hashtag(self, hashtag: str, platform: str = "instagram") -> HashtagValidationResult:
        """
        Comprehensive validation of a single hashtag

        Args:
            hashtag: The hashtag to validate (with or without #)
            platform: Target platform for platform-specific rules

        Returns:
            HashtagValidationResult with validation details
        """
        # Normalize hashtag format
        if not hashtag.startswith("#"):
            hashtag = f"#{hashtag}"

        hashtag_clean = hashtag.lower()
        issues = []
        suggested_correction = None
        confidence_score = 1.0

        # Get platform rules
        rules = PLATFORM_RULES.get(platform.lower(), PLATFORM_RULES["instagram"])

        # 1. Format validation
        if not re.match(rules["required_format"], hashtag):
            issues.append("Invalid format: contains special characters or spaces")
            confidence_score -= 0.3

        # 2. Length validation
        if len(hashtag) > rules["max_length"]:
            issues.append(f"Too long: {len(hashtag)} characters (max: {rules['max_length']})")
            confidence_score -= 0.2
        elif len(hashtag) < rules["min_length"]:
            issues.append(f"Too short: {len(hashtag)} characters (min: {rules['min_length']})")
            confidence_score -= 0.2

        # 3. Pattern validation
        for pattern in rules["avoid_patterns"]:
            if pattern in hashtag:
                issues.append(f"Contains problematic pattern: {pattern}")
                confidence_score -= 0.2

        # 4. Spell check and correction suggestions
        correction_result = self._check_spelling_and_suggest_correction(hashtag)
        if correction_result:
            suggested_correction, similarity_score = correction_result
            if similarity_score < 0.9:  # Threshold for spell correction
                issues.append(f"Possible typo detected (similarity: {similarity_score:.2f})")
                confidence_score = similarity_score

        # 5. Brand alignment check
        brand_score = self._check_brand_alignment(hashtag)
        if brand_score < 0.3:
            issues.append(f"Low brand alignment score: {brand_score:.2f}")
            confidence_score *= brand_score

        is_valid = len(issues) == 0 and confidence_score > 0.7

        result = HashtagValidationResult(
            hashtag=hashtag,
            is_valid=is_valid,
            issues=issues,
            suggested_correction=suggested_correction,
            confidence_score=confidence_score
        )

        self.validation_log.append(result.to_dict())
        return result

    def validate_hashtag_set(self, hashtags: List[str], platform: str = "instagram") -> Dict[str, HashtagValidationResult]:
        """
        Validate a set of hashtags for a specific platform

        Args:
            hashtags: List of hashtags to validate
            platform: Target platform

        Returns:
            Dictionary mapping hashtags to validation results
        """
        results = {}

        for hashtag in hashtags:
            result = self.validate_hashtag(hashtag, platform)
            results[hashtag] = result

        return results

    def _check_spelling_and_suggest_correction(self, hashtag: str) -> Optional[Tuple[str, float]]:
        """
        Check for spelling errors and suggest corrections

        Returns:
            Tuple of (suggested_correction, similarity_score) or None
        """
        hashtag_lower = hashtag.lower().replace("#", "")

        # Check against common corrections
        if hashtag_lower in COMMON_CORRECTIONS:
            correction = f"#{COMMON_CORRECTIONS[hashtag_lower]}"
            similarity = SequenceMatcher(None, hashtag, correction).ratio()
            return correction, similarity

        # Check against brand keyword variations
        best_match = None
        best_score = 0.0

        for category, variations in BRAND_KEYWORDS.items():
            for variation in variations:
                similarity = SequenceMatcher(None, hashtag_lower, variation).ratio()
                if similarity > best_score and similarity > 0.8:
                    best_score = similarity
                    best_match = f"#{variation}"

        return (best_match, best_score) if best_match else None

    def _check_brand_alignment(self, hashtag: str) -> float:
        """
        Calculate brand alignment score for a hashtag

        Returns:
            Float score between 0.0 and 1.0
        """
        hashtag_lower = hashtag.lower().replace("#", "")

        # Core brand terms
        brand_terms = ["vawn", "apulu", "brooklyn", "atlanta", "orchestral",
                      "psychedelic", "boombap", "trap", "conscious", "lyrical"]

        # Hip-hop specific terms
        hiphop_terms = ["rap", "hiphop", "hip", "boom", "bap", "beats", "bars",
                       "flows", "rhymes", "mc", "dj", "producer"]

        # Geographic terms
        geo_terms = ["brooklyn", "atlanta", "nyc", "atl", "east", "south",
                    "coast", "street", "urban"]

        score = 0.0

        # Check for exact brand matches (high weight)
        for term in brand_terms:
            if term in hashtag_lower:
                score += 0.4
                break

        # Check for hip-hop relevance (medium weight)
        for term in hiphop_terms:
            if term in hashtag_lower:
                score += 0.3
                break

        # Check for geographic relevance (low weight)
        for term in geo_terms:
            if term in hashtag_lower:
                score += 0.2
                break

        # Bonus for indie/underground terms
        indie_terms = ["indie", "underground", "independent", "authentic", "real"]
        for term in indie_terms:
            if term in hashtag_lower:
                score += 0.1
                break

        return min(score, 1.0)  # Cap at 1.0

    def auto_fix_hashtags(self, hashtags: List[str], platform: str = "instagram") -> List[str]:
        """
        Automatically fix common issues in a list of hashtags

        Args:
            hashtags: List of hashtags to fix
            platform: Target platform

        Returns:
            List of corrected hashtags
        """
        fixed_hashtags = []

        for hashtag in hashtags:
            result = self.validate_hashtag(hashtag, platform)

            if result.is_valid:
                fixed_hashtags.append(hashtag)
            elif result.suggested_correction:
                fixed_hashtags.append(result.suggested_correction)
                print(f"[AUTO-FIX] {hashtag} → {result.suggested_correction}")
            else:
                # Keep original but log the issues
                fixed_hashtags.append(hashtag)
                print(f"[WARNING] {hashtag}: {', '.join(result.issues)}")

        return fixed_hashtags

    def get_validation_report(self) -> dict:
        """Generate a comprehensive validation report"""
        total_validations = len(self.validation_log)
        valid_count = sum(1 for log in self.validation_log if log["is_valid"])

        avg_confidence = sum(log["confidence_score"] for log in self.validation_log) / max(total_validations, 1)

        common_issues = {}
        for log in self.validation_log:
            for issue in log["issues"]:
                common_issues[issue] = common_issues.get(issue, 0) + 1

        return {
            "total_validations": total_validations,
            "valid_hashtags": valid_count,
            "invalid_hashtags": total_validations - valid_count,
            "success_rate": valid_count / max(total_validations, 1),
            "average_confidence": avg_confidence,
            "common_issues": dict(sorted(common_issues.items(), key=lambda x: x[1], reverse=True)),
            "validation_log": self.validation_log
        }


def validate_current_hashtags():
    """Validate all current hashtag files and provide fix recommendations"""

    validator = HashtagValidator()
    platforms = ["Instagram", "TikTok", "Threads", "X", "Bluesky"]

    print(f"[APU-150] Hashtag Validation System")
    print(f"=" * 50)

    validation_results = {}

    for platform in platforms:
        platform_dir = Path(f"C:/Users/rdyal/Vawn/Social_Media_Exports/Trending_Hashtags/{platform}")
        hashtag_file = platform_dir / "hashtags.txt"

        if not hashtag_file.exists():
            print(f"[WARNING] No hashtag file found for {platform}")
            continue

        # Read hashtags
        hashtags = hashtag_file.read_text(encoding="utf-8").strip().split("\n")
        hashtags = [h.strip() for h in hashtags if h.strip()]

        # Validate
        results = validator.validate_hashtag_set(hashtags, platform.lower())
        validation_results[platform] = results

        # Report results
        valid_count = sum(1 for r in results.values() if r.is_valid)
        print(f"\n{platform}: {valid_count}/{len(hashtags)} valid hashtags")

        for hashtag, result in results.items():
            if not result.is_valid:
                print(f"  [X] {hashtag}: {', '.join(result.issues)}")
                if result.suggested_correction:
                    print(f"     -> Suggest: {result.suggested_correction}")
            else:
                print(f"  [OK] {hashtag}")

    # Generate overall report
    report = validator.get_validation_report()

    print(f"\n[VALIDATION SUMMARY]")
    print(f"Total Hashtags: {report['total_validations']}")
    print(f"Valid: {report['valid_hashtags']}")
    print(f"Invalid: {report['invalid_hashtags']}")
    print(f"Success Rate: {report['success_rate']:.1%}")
    print(f"Average Confidence: {report['average_confidence']:.2f}")

    if report['common_issues']:
        print(f"\nMost Common Issues:")
        for issue, count in list(report['common_issues'].items())[:3]:
            print(f"  • {issue}: {count} occurrences")

    return validation_results, report


if __name__ == "__main__":
    validate_current_hashtags()