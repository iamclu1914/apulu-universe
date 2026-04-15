"""
test_apu127_engagement_monitor.py — Test suite for APU-127 engagement monitor
Validates functionality without making actual API calls.
"""

import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from engagement_monitor_apu127 import (
    calculate_comment_priority,
    should_respond_to_comment,
    check_rate_limits,
    get_comment_hash,
    ENGAGEMENT_CONFIG
)


def test_comment_priority_scoring():
    """Test the comment priority scoring algorithm."""
    print("Testing comment priority scoring...")

    # Test high-priority comment (question from verified user)
    high_priority_comment = {
        "text": "How did you come up with that flow? It's incredible!",
        "author": {
            "username": "musicfan",
            "verified": True,
            "followers": 15000
        },
        "created_at": datetime.now().isoformat()
    }

    high_score = calculate_comment_priority(high_priority_comment)
    print(f"High priority comment score: {high_score}")
    assert high_score > 100, f"Expected high score > 100, got {high_score}"

    # Test low-priority comment
    low_priority_comment = {
        "text": "check out my music link in bio",
        "author": {
            "username": "spammer",
            "verified": False,
            "followers": 10
        },
        "created_at": (datetime.now() - timedelta(hours=12)).isoformat()
    }

    low_score = calculate_comment_priority(low_priority_comment)
    print(f"Low priority comment score: {low_score}")
    assert low_score < 50, f"Expected low score < 50, got {low_score}"

    # Test mention comment
    mention_comment = {
        "text": "@vawn this track is fire bro keep going",
        "author": {
            "username": "supporter",
            "verified": False,
            "followers": 500
        },
        "created_at": datetime.now().isoformat()
    }

    mention_score = calculate_comment_priority(mention_comment)
    print(f"Mention comment score: {mention_score}")
    assert mention_score > 60, f"Expected mention score > 60, got {mention_score}"

    print("PASS: Comment priority scoring tests passed")


def test_response_decision_logic():
    """Test the decision logic for whether to respond to comments."""
    print("\nTesting response decision logic...")

    # Mock comments cache
    comments_cache = {"responded": [], "processed": []}

    # Test question comment (should respond)
    question_comment = {
        "text": "What's your next album about?",
        "author": {"username": "fan", "verified": False, "followers": 100},
        "created_at": datetime.now().isoformat(),
        "platform": "instagram",
        "post_id": "test123",
        "id": "comment456"
    }

    should_respond, reason = should_respond_to_comment(question_comment, comments_cache)
    print(f"Question comment - Should respond: {should_respond}, Reason: {reason}")
    assert should_respond, f"Expected to respond to question, but got: {reason}"

    # Test mention comment (should respond)
    mention_comment = {
        "text": "@vawn appreciate the music bro",
        "author": {"username": "supporter", "verified": False, "followers": 200},
        "created_at": datetime.now().isoformat(),
        "platform": "instagram",
        "post_id": "test124",
        "id": "comment457"
    }

    should_respond, reason = should_respond_to_comment(mention_comment, comments_cache)
    print(f"Mention comment - Should respond: {should_respond}, Reason: {reason}")
    assert should_respond, f"Expected to respond to mention, but got: {reason}"

    # Test spam comment (should not respond)
    spam_comment = {
        "text": "follow for follow check out my link www.spam.com",
        "author": {"username": "spammer", "verified": False, "followers": 5},
        "created_at": datetime.now().isoformat(),
        "platform": "instagram",
        "post_id": "test125",
        "id": "comment458"
    }

    should_respond, reason = should_respond_to_comment(spam_comment, comments_cache)
    print(f"Spam comment - Should respond: {should_respond}, Reason: {reason}")
    assert not should_respond, f"Expected NOT to respond to spam, but got: {reason}"

    print("PASS: Response decision logic tests passed")


def test_comment_hashing():
    """Test comment hash generation for deduplication."""
    print("\nTesting comment hash generation...")

    comment1 = {
        "platform": "instagram",
        "post_id": "123",
        "id": "456",
        "text": "Great track!",
        "author": "fan1"
    }

    comment2 = {
        "platform": "instagram",
        "post_id": "123",
        "id": "456",
        "text": "Great track!",
        "author": "fan1"
    }

    comment3 = {
        "platform": "instagram",
        "post_id": "123",
        "id": "457",  # Different ID
        "text": "Great track!",
        "author": "fan1"
    }

    hash1 = get_comment_hash(comment1)
    hash2 = get_comment_hash(comment2)
    hash3 = get_comment_hash(comment3)

    print(f"Hash 1: {hash1}")
    print(f"Hash 2: {hash2}")
    print(f"Hash 3: {hash3}")

    assert hash1 == hash2, "Same comments should have same hash"
    assert hash1 != hash3, "Different comments should have different hashes"

    print("PASS: Comment hashing tests passed")


def test_configuration_validation():
    """Test that configuration values are reasonable."""
    print("\nTesting configuration validation...")

    # Check rate limiting config
    rate_limits = ENGAGEMENT_CONFIG["response_rate_limit"]
    assert rate_limits["max_responses_per_hour"] > 0, "Max responses per hour must be positive"
    assert rate_limits["cooldown_between_responses_minutes"] > 0, "Cooldown must be positive"

    # Check priority scoring config
    priority = ENGAGEMENT_CONFIG["priority_scoring"]
    assert priority["verified_user_bonus"] > 0, "Verified user bonus should be positive"
    assert priority["negative_sentiment_penalty"] < 0, "Negative sentiment should be penalty"

    # Check response triggers config
    triggers = ENGAGEMENT_CONFIG["response_triggers"]
    assert triggers["min_priority_score"] > 0, "Min priority score must be positive"

    print(f"Rate limit config: {rate_limits}")
    print(f"Priority scoring config: {priority}")
    print(f"Response triggers config: {triggers}")

    print("PASS: Configuration validation tests passed")


def run_all_tests():
    """Run all test functions."""
    print("Starting APU-127 engagement monitor tests...\n")

    try:
        test_comment_priority_scoring()
        test_response_decision_logic()
        test_comment_hashing()
        test_configuration_validation()

        print("\n" + "="*50)
        print("SUCCESS: ALL TESTS PASSED! APU-127 is ready for deployment.")
        print("="*50)

        return True

    except AssertionError as e:
        print(f"\nFAIL: TEST FAILED: {str(e)}")
        return False

    except Exception as e:
        print(f"\nERROR: UNEXPECTED ERROR: {str(e)}")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)