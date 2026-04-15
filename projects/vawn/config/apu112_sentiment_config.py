"""
APU-112 Sentiment Analysis Configuration
Specific configuration for Vawn's engagement monitoring system
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vawn_config import RESEARCH_DIR, CONFIG_FILE, load_json

# Sentiment Analysis Model Configuration
SENTIMENT_CONFIG = {
    "model": {
        "primary_model": "vawn-hiphop-sentiment-v1",
        "fallback_model": "cardiffnlp/twitter-roberta-base-sentiment-latest",
        "emotion_model": "j-hartmann/emotion-english-distilroberta-base",
        "cache_dir": "./models/sentiment/",
        "max_sequence_length": 512,
        "batch_size": 16,
        "confidence_threshold": 0.65
    },

    "platforms": {
        "instagram": {
            "weight": 1.0,
            "context_sensitivity": "high",
            "slang_adaptation": "visual_culture"
        },
        "tiktok": {
            "weight": 1.2,  # Higher weight due to viral potential
            "context_sensitivity": "very_high",
            "slang_adaptation": "gen_z_heavy"
        },
        "x": {
            "weight": 0.9,
            "context_sensitivity": "medium",
            "slang_adaptation": "text_heavy"
        },
        "threads": {
            "weight": 0.8,
            "context_sensitivity": "medium",
            "slang_adaptation": "professional_casual"
        },
        "bluesky": {
            "weight": 0.7,
            "context_sensitivity": "medium",
            "slang_adaptation": "early_adopter"
        }
    },

    "vawn_context": {
        "artist_aliases": ["vawn", "@vawn", "vawn music", "vawn artist"],
        "music_style_terms": [
            "psychedelic boom bap", "atlanta trap", "trap-soul",
            "orchestral soul hip-hop", "pattern recognition",
            "quiet authority", "earned confidence"
        ],
        "thematic_territories": [
            "fear of failure", "dependability", "love", "journey",
            "long-game mentality", "anti-hype"
        ],
        "comparable_artists": ["JID", "6LACK", "Killer Mike", "Dreamville", "Baby Keem", "Smino", "Saba"],
        "geographic_context": ["brooklyn", "atlanta", "atl", "bk", "dirty south", "east coast"]
    },

    "hip_hop_lexicon": {
        "positive_energy": {
            "tier_1": ["fire", "flames", "heat", "banger", "slaps", "goes hard"],
            "tier_2": ["vibes", "mood", "energy", "flow", "bars", "beats"],
            "tier_3": ["fresh", "clean", "smooth", "cold", "nasty", "tough", "raw"]
        },
        "critical_feedback": {
            "constructive": ["could be better", "not my style", "different direction", "preferred earlier"],
            "harsh": ["mid", "trash", "weak", "basic", "played out", "boring"]
        },
        "technical_appreciation": {
            "production": ["mix", "master", "production", "engineer", "studio", "quality"],
            "musical": ["sample", "loop", "808s", "hi-hats", "melody", "harmony"],
            "performance": ["delivery", "cadence", "timing", "presence", "character"]
        },
        "cultural_markers": {
            "atlanta": ["trap", "metro", "southside", "zone 6", "atl", "dirty south"],
            "brooklyn": ["boom bap", "east coast", "bk", "flatbush", "bedstuy"],
            "general_hiphop": ["culture", "movement", "scene", "community", "real", "authentic"]
        }
    },

    "emotion_mapping": {
        "hype": {
            "indicators": ["fire", "banger", "goes hard", "slaps", "flames"],
            "confidence_boost": 0.2,
            "engagement_multiplier": 1.5
        },
        "technical_appreciation": {
            "indicators": ["production", "mix", "quality", "sound", "engineering"],
            "confidence_boost": 0.3,
            "engagement_multiplier": 2.0
        },
        "anticipation": {
            "indicators": ["when", "next", "more", "waiting", "drop", "release"],
            "confidence_boost": 0.1,
            "engagement_multiplier": 1.3
        },
        "discovery": {
            "indicators": ["new favorite", "underrated", "found", "discovered", "sharing"],
            "confidence_boost": 0.25,
            "engagement_multiplier": 1.8
        },
        "loyalty": {
            "indicators": ["day one", "since beginning", "always", "supporter", "fan"],
            "confidence_boost": 0.2,
            "engagement_multiplier": 1.4
        }
    },

    "response_prioritization": {
        "high_priority": {
            "negative_with_detail": {"min_words": 8, "sentiment_threshold": -0.6},
            "technical_feedback": {"keywords": ["production", "mix", "sound"], "min_confidence": 0.7},
            "fan_concerns": {"keywords": ["disappointed", "expected", "preferred"], "loyalty_indicators": True}
        },
        "medium_priority": {
            "positive_detailed": {"min_words": 10, "sentiment_threshold": 0.6},
            "questions": {"indicators": ["?", "when", "how", "where", "what"]},
            "sharing_intent": {"keywords": ["share", "playlist", "recommend", "tell"]}
        },
        "low_priority": {
            "generic_positive": {"max_words": 5, "generic_terms": ["good", "nice", "cool"]},
            "emoji_only": {"pattern": "emoji_heavy"},
            "spam_indicators": {"keywords": ["follow back", "check out", "promo", "collab?"]}
        }
    },

    "performance_metrics": {
        "accuracy_target": 0.85,
        "processing_time_target": 150,  # milliseconds
        "cultural_context_hit_rate_target": 0.75,
        "false_positive_rate_max": 0.15,
        "batch_size_optimal": 32
    },

    "integration": {
        "engagement_agent": {
            "sentiment_threshold_for_reply": 0.6,
            "priority_threshold_for_immediate": 4,
            "context_injection": True
        },
        "analytics_agent": {
            "sentiment_trend_tracking": True,
            "weekly_sentiment_summary": True,
            "platform_sentiment_comparison": True
        },
        "existing_apis": {
            "base_url": "https://apulustudio.onrender.com/api",
            "auth_integration": True,
            "rate_limiting": {
                "requests_per_minute": 100,
                "burst_allowance": 20
            }
        }
    },

    "storage": {
        "sentiment_log": str(RESEARCH_DIR / "sentiment_analysis_log.json"),
        "model_cache": str(RESEARCH_DIR / "models" / "sentiment"),
        "performance_log": str(RESEARCH_DIR / "sentiment_performance.json"),
        "cultural_context_log": str(RESEARCH_DIR / "cultural_context_hits.json")
    }
}

# Model fine-tuning configuration for hip-hop context
FINE_TUNING_CONFIG = {
    "base_model": "cardiffnlp/twitter-roberta-base-sentiment-latest",
    "training_data_sources": [
        "hip_hop_social_media_comments",
        "music_industry_feedback",
        "vawn_specific_engagement_history",
        "comparable_artist_comments",
        "atlanta_hiphop_culture_text",
        "brooklyn_hiphop_culture_text"
    ],
    "training_parameters": {
        "learning_rate": 2e-5,
        "epochs": 3,
        "batch_size": 16,
        "warmup_steps": 500,
        "weight_decay": 0.01
    },
    "validation_split": 0.2,
    "early_stopping_patience": 2
}

# API endpoint specifications
API_ENDPOINTS = {
    "/sentiment/analyze": {
        "method": "POST",
        "description": "Analyze single comment for sentiment and cultural context",
        "input": {
            "text": "string",
            "platform": "string",
            "metadata": "object (optional)"
        },
        "output": "SentimentScore object"
    },
    "/sentiment/batch": {
        "method": "POST",
        "description": "Batch analyze multiple comments",
        "input": {
            "comments": "array of comment objects",
            "priority": "string (optional: low|medium|high)"
        },
        "output": "array of SentimentScore objects"
    },
    "/sentiment/trends": {
        "method": "GET",
        "description": "Get sentiment trends over time",
        "parameters": {
            "days": "integer (default: 7)",
            "platform": "string (optional)",
            "granularity": "string (hour|day|week)"
        },
        "output": "trend data object"
    },
    "/sentiment/metrics": {
        "method": "GET",
        "description": "Get model performance metrics",
        "output": "performance metrics object"
    },
    "/sentiment/cultural-context": {
        "method": "GET",
        "description": "Get cultural context analysis",
        "parameters": {
            "period": "string (day|week|month)"
        },
        "output": "cultural context analysis"
    }
}

# Cost optimization strategies
COST_OPTIMIZATION = {
    "model_efficiency": {
        "quantization": "8-bit inference",
        "caching": {
            "similar_text_threshold": 0.95,
            "cache_ttl": 3600,  # 1 hour
            "max_cache_size": 10000
        },
        "batch_optimization": {
            "min_batch_size": 8,
            "max_wait_time": 2000,  # milliseconds
            "dynamic_batching": True
        }
    },
    "rate_limiting": {
        "per_platform_limits": {
            "instagram": 50,  # per minute
            "tiktok": 75,     # higher due to volume
            "x": 60,
            "threads": 40,
            "bluesky": 30
        },
        "priority_queuing": True,
        "graceful_degradation": {
            "fallback_to_simple_model": True,
            "reduced_feature_mode": True
        }
    },
    "monitoring": {
        "cost_per_request": True,
        "accuracy_vs_cost_tracking": True,
        "performance_alerts": True
    }
}

def get_sentiment_config():
    """Get the complete sentiment analysis configuration"""
    return SENTIMENT_CONFIG

def get_fine_tuning_config():
    """Get the fine-tuning configuration for hip-hop context"""
    return FINE_TUNING_CONFIG

def get_api_config():
    """Get API endpoint configurations"""
    return API_ENDPOINTS

def get_cost_optimization_config():
    """Get cost optimization strategies"""
    return COST_OPTIMIZATION

if __name__ == "__main__":
    print("APU-112 Sentiment Analysis Configuration")
    print("========================================")
    print()
    print(f"Primary model: {SENTIMENT_CONFIG['model']['primary_model']}")
    print(f"Supported platforms: {list(SENTIMENT_CONFIG['platforms'].keys())}")
    print(f"Hip-hop lexicon terms: {len(SENTIMENT_CONFIG['hip_hop_lexicon']['positive_energy']['tier_1'])}")
    print(f"Vawn-specific context terms: {len(SENTIMENT_CONFIG['vawn_context']['music_style_terms'])}")
    print()
    print("Configuration loaded successfully.")