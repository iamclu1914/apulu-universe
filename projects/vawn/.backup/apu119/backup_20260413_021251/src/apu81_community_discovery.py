"""
apu81_community_discovery.py — APU-81 Community Discovery System for Vawn
Intelligent community mapping and target audience identification system.
Discovers and analyzes Vawn's ideal audience segments for strategic engagement.

Created by: Dex - Community Agent (APU-81)
Integrates with: apu81_enhanced_engagement_bot.py
"""

import json
import sys
import re
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Set, Optional
from collections import Counter, defaultdict

sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import (
    VAWN_DIR, load_json, save_json, log_run, today_str, VAWN_PROFILE, COMPARABLE_ARTISTS
)

# Configuration
COMMUNITY_DISCOVERY_LOG = VAWN_DIR / "research" / "apu81_community_discovery.json"
AUDIENCE_PROFILES = VAWN_DIR / "research" / "vawn_audience_profiles.json"
INFLUENCER_MAP = VAWN_DIR / "research" / "hip_hop_influencer_map.json"

# Vawn's target audience segments
TARGET_AUDIENCE_SEGMENTS = {
    "lyrical_heads": {
        "keywords": ["lyrical", "bars", "wordplay", "conscious rap", "storytelling", "flow"],
        "artists": ["J. Cole", "Kendrick", "JID", "Saba", "Lupe Fiasco", "Black Thought"],
        "characteristics": "Values lyrical complexity and meaningful content",
        "engagement_style": "thoughtful comments, in-depth discussions"
    },
    "atlanta_scene": {
        "keywords": ["atlanta", "atl", "zone 6", "eastside", "decatur", "clayton county"],
        "artists": ["T.I.", "Killer Mike", "6LACK", "Dreamville", "JID", "Earthgang"],
        "characteristics": "Connected to Atlanta hip-hop culture and scene",
        "engagement_style": "local pride, scene support, collaboration-focused"
    },
    "brooklyn_diaspora": {
        "keywords": ["brooklyn", "bk", "bedstuy", "flatbush", "crown heights", "williamsburg"],
        "artists": ["Joey Badass", "Flatbush Zombies", "Pro Era", "Beast Coast", "Talib Kweli"],
        "characteristics": "Brooklyn hip-hop heritage and culture",
        "engagement_style": "authenticity-focused, old school appreciation"
    },
    "boom_bap_purists": {
        "keywords": ["boom bap", "90s hip hop", "golden age", "real hip hop", "underground"],
        "artists": ["Nas", "Gang Starr", "A Tribe Called Quest", "MF DOOM", "Madlib"],
        "characteristics": "Prefers traditional hip-hop production and aesthetics",
        "engagement_style": "nostalgic references, production appreciation"
    },
    "creative_collaborators": {
        "keywords": ["producer", "engineer", "collab", "studio", "beat maker", "artist"],
        "artists": ["Metro Boomin", "9th Wonder", "The Alchemist", "Statik Selektah"],
        "characteristics": "Industry professionals and serious creatives",
        "engagement_style": "professional networking, skill appreciation"
    }
}

# Community discovery patterns
COMMUNITY_HUB_INDICATORS = [
    "RT if you", "share if you", "tag someone who", "who's your favorite",
    "drop your", "what's your favorite", "best rapper", "underrated artist"
]

INFLUENCER_INDICATORS = [
    "verified", "k followers", "playlist curator", "blog", "podcast",
    "radio", "dj", "music industry", "a&r", "label"
]


def get_bluesky_credentials():
    """Get Bluesky credentials for community discovery."""
    creds = load_json(VAWN_DIR / "credentials.json")
    return creds.get("bluesky_handle"), creds.get("bluesky_app_password")


def analyze_account_audience_fit(account_data, post_data=None) -> Dict[str, Any]:
    """
    Analyze how well an account fits Vawn's target audience segments.
    Returns segment scores and overall audience compatibility.
    """
    if not account_data:
        return {"total_score": 0, "segments": {}, "fit_level": "none"}

    # Extract analyzable data
    bio = getattr(account_data, 'description', '') or ''
    handle = getattr(account_data, 'handle', '')
    display_name = getattr(account_data, 'displayName', '') or ''

    # Combine text for analysis
    text_to_analyze = f"{bio} {handle} {display_name}".lower()

    if post_data:
        post_text = getattr(post_data.record, 'text', '') or ''
        text_to_analyze += f" {post_text.lower()}"

    segment_scores = {}
    total_score = 0

    # Analyze fit for each target audience segment
    for segment_name, segment_data in TARGET_AUDIENCE_SEGMENTS.items():
        score = 0

        # Check keyword matches
        keyword_matches = sum(1 for keyword in segment_data["keywords"] if keyword in text_to_analyze)
        score += keyword_matches * 2

        # Check artist mentions
        artist_matches = sum(1 for artist in segment_data["artists"] if artist.lower() in text_to_analyze)
        score += artist_matches * 3

        # Bonus for multiple indicators
        if keyword_matches > 1 and artist_matches > 0:
            score += 2

        segment_scores[segment_name] = score
        total_score += score

    # Determine fit level
    if total_score >= 10:
        fit_level = "excellent"
    elif total_score >= 6:
        fit_level = "good"
    elif total_score >= 3:
        fit_level = "moderate"
    elif total_score >= 1:
        fit_level = "low"
    else:
        fit_level = "none"

    # Identify primary segment
    primary_segment = max(segment_scores.keys(), key=lambda k: segment_scores[k]) if segment_scores else None

    return {
        "total_score": total_score,
        "segments": segment_scores,
        "primary_segment": primary_segment,
        "fit_level": fit_level,
        "analysis_text": text_to_analyze[:200] + "..." if len(text_to_analyze) > 200 else text_to_analyze
    }


def discover_community_hubs(client, search_terms: List[str], max_results: int = 50) -> List[Dict[str, Any]]:
    """
    Discover community hubs - accounts and posts that serve as gathering points.
    Looks for engagement patterns that indicate community activity.
    """
    community_hubs = []

    for term in search_terms[:3]:  # Limit to avoid rate limits
        try:
            results = client.app.bsky.feed.search_posts({"q": term, "limit": max_results})
            posts = results.posts if hasattr(results, 'posts') else []

            for post in posts[:20]:  # Analyze top 20 per search
                # Check for community hub indicators
                text = post.record.text.lower()
                hub_score = 0

                for indicator in COMMUNITY_HUB_INDICATORS:
                    if indicator in text:
                        hub_score += 2

                # High engagement indicates community activity
                total_engagement = (getattr(post, 'likeCount', 0) or 0) + (getattr(post, 'repostCount', 0) or 0)
                if total_engagement > 10:
                    hub_score += 1

                # Questions and discussions indicate community engagement
                if '?' in text or any(word in text for word in ['what', 'who', 'how', 'why', 'when']):
                    hub_score += 1

                if hub_score >= 3:  # Threshold for community hub
                    audience_fit = analyze_account_audience_fit(post.author, post)

                    community_hubs.append({
                        "author_handle": post.author.handle,
                        "author_name": getattr(post.author, 'displayName', ''),
                        "post_text": text[:200],
                        "hub_score": hub_score,
                        "audience_fit": audience_fit,
                        "engagement": total_engagement,
                        "discovered_via": term,
                        "post_uri": post.uri,
                        "discovered_at": datetime.now().isoformat()
                    })

        except Exception as e:
            print(f"[WARN] Community hub discovery failed for '{term}': {e}")
            continue

    # Sort by combination of hub score and audience fit
    community_hubs.sort(key=lambda x: (x["audience_fit"]["total_score"] + x["hub_score"]), reverse=True)

    return community_hubs[:15]  # Top 15 community hubs


def discover_target_influencers(client, audience_segments: List[str] = None) -> List[Dict[str, Any]]:
    """
    Discover influencers and key accounts within Vawn's target audience.
    Focuses on accounts that could amplify Vawn's reach.
    """
    if not audience_segments:
        audience_segments = list(TARGET_AUDIENCE_SEGMENTS.keys())

    influencers = []

    # Search for each audience segment
    for segment in audience_segments[:3]:  # Limit to avoid rate limits
        segment_data = TARGET_AUDIENCE_SEGMENTS[segment]
        search_terms = segment_data["keywords"][:2] + segment_data["artists"][:2]

        for term in search_terms:
            try:
                results = client.app.bsky.feed.search_posts({"q": term, "limit": 20})
                posts = results.posts if hasattr(results, 'posts') else []

                for post in posts[:10]:
                    author = post.author
                    bio = getattr(author, 'description', '') or ''

                    # Check for influencer indicators
                    influencer_score = 0

                    # Follower count (if available)
                    followers = getattr(author, 'followersCount', 0) or 0
                    if 1000 <= followers <= 100000:  # Sweet spot for micro-influencers
                        influencer_score += 3
                    elif followers > 100000:  # Macro influencer
                        influencer_score += 2

                    # Bio indicators
                    for indicator in INFLUENCER_INDICATORS:
                        if indicator.lower() in bio.lower():
                            influencer_score += 2

                    # Content quality indicators
                    if len(post.record.text) > 100:  # Substantial content
                        influencer_score += 1

                    # Engagement ratio
                    total_engagement = (getattr(post, 'likeCount', 0) or 0) + (getattr(post, 'repostCount', 0) or 0)
                    if total_engagement > 20:
                        influencer_score += 2

                    if influencer_score >= 4:  # Threshold for influencer
                        audience_fit = analyze_account_audience_fit(author, post)

                        # Only include if good audience fit
                        if audience_fit["fit_level"] in ["excellent", "good", "moderate"]:
                            influencers.append({
                                "handle": author.handle,
                                "display_name": getattr(author, 'displayName', ''),
                                "bio": bio[:150],
                                "followers": followers,
                                "influencer_score": influencer_score,
                                "audience_fit": audience_fit,
                                "segment": segment,
                                "discovered_via": term,
                                "discovered_at": datetime.now().isoformat()
                            })

            except Exception as e:
                print(f"[WARN] Influencer discovery failed for '{term}': {e}")
                continue

    # Remove duplicates and sort by combined score
    unique_influencers = {}
    for inf in influencers:
        handle = inf["handle"]
        if handle not in unique_influencers or inf["influencer_score"] > unique_influencers[handle]["influencer_score"]:
            unique_influencers[handle] = inf

    sorted_influencers = list(unique_influencers.values())
    sorted_influencers.sort(key=lambda x: (x["audience_fit"]["total_score"] + x["influencer_score"]), reverse=True)

    return sorted_influencers[:10]  # Top 10 influencers


def analyze_audience_growth_opportunities(community_hubs: List[Dict], influencers: List[Dict]) -> Dict[str, Any]:
    """
    Analyze the discovered community data to identify growth opportunities for Vawn.
    """
    # Analyze segment distribution
    segment_distribution = defaultdict(int)
    total_audience_score = 0

    for hub in community_hubs:
        primary_segment = hub["audience_fit"].get("primary_segment")
        if primary_segment:
            segment_distribution[primary_segment] += 1
        total_audience_score += hub["audience_fit"]["total_score"]

    for inf in influencers:
        primary_segment = inf["audience_fit"].get("primary_segment")
        if primary_segment:
            segment_distribution[primary_segment] += 1
        total_audience_score += inf["audience_fit"]["total_score"]

    # Identify top opportunities
    top_segments = sorted(segment_distribution.items(), key=lambda x: x[1], reverse=True)

    # Calculate engagement potential
    high_value_targets = []
    for hub in community_hubs[:5]:
        if hub["audience_fit"]["fit_level"] in ["excellent", "good"]:
            high_value_targets.append({
                "type": "community_hub",
                "handle": hub["author_handle"],
                "value_score": hub["audience_fit"]["total_score"] + hub["hub_score"],
                "reason": f"Community hub in {hub['audience_fit']['primary_segment']} segment"
            })

    for inf in influencers[:5]:
        if inf["audience_fit"]["fit_level"] in ["excellent", "good"]:
            high_value_targets.append({
                "type": "influencer",
                "handle": inf["handle"],
                "value_score": inf["audience_fit"]["total_score"] + inf["influencer_score"],
                "reason": f"Influencer in {inf['audience_fit']['primary_segment']} segment"
            })

    high_value_targets.sort(key=lambda x: x["value_score"], reverse=True)

    return {
        "segment_distribution": dict(segment_distribution),
        "top_segments": top_segments[:3],
        "high_value_targets": high_value_targets[:8],
        "total_opportunities": len(community_hubs) + len(influencers),
        "avg_audience_score": total_audience_score / max(len(community_hubs) + len(influencers), 1),
        "growth_recommendations": generate_growth_recommendations(segment_distribution, high_value_targets)
    }


def generate_growth_recommendations(segment_distribution: Dict, high_value_targets: List[Dict]) -> List[str]:
    """Generate actionable growth recommendations based on community analysis."""
    recommendations = []

    # Segment-based recommendations
    if "lyrical_heads" in segment_distribution and segment_distribution["lyrical_heads"] > 2:
        recommendations.append("Focus on lyrical content and wordplay - strong lyrical audience discovered")

    if "atlanta_scene" in segment_distribution and segment_distribution["atlanta_scene"] > 2:
        recommendations.append("Engage with Atlanta hip-hop community - local scene presence found")

    if "creative_collaborators" in segment_distribution and segment_distribution["creative_collaborators"] > 1:
        recommendations.append("Target producer/creative collaborations - industry professionals identified")

    # Target-based recommendations
    influencer_targets = [t for t in high_value_targets if t["type"] == "influencer"]
    if len(influencer_targets) >= 3:
        recommendations.append(f"Priority engagement with {len(influencer_targets)} identified micro-influencers")

    hub_targets = [t for t in high_value_targets if t["type"] == "community_hub"]
    if len(hub_targets) >= 3:
        recommendations.append(f"Engage with {len(hub_targets)} community hub conversations")

    # Default recommendations if low discovery
    if len(recommendations) == 0:
        recommendations.append("Expand search terms - limited target audience discovered")
        recommendations.append("Focus on comparable artist followers from COMPARABLE_ARTISTS list")

    return recommendations


def run_community_discovery():
    """Main community discovery function."""
    print("\n=== APU-81 Community Discovery ===\n")

    handle, app_password = get_bluesky_credentials()
    if not handle or not app_password:
        print("[INFO] Bluesky credentials required for community discovery")
        return {"error": "Missing credentials"}

    try:
        from atproto import Client
    except ImportError:
        print("[INFO] atproto library required. Run: pip install atproto")
        return {"error": "Missing atproto library"}

    client = Client()
    try:
        client.login(handle, app_password)
        print(f"[OK] Connected to Bluesky for community discovery")
    except Exception as e:
        print(f"[FAIL] Bluesky connection failed: {e}")
        return {"error": f"Connection failed: {e}"}

    # Discover community hubs
    print("[DISCOVERY] Finding community hubs...")
    hub_search_terms = ["hip hop community", "atlanta rap", "boom bap", "lyrical rap"]
    community_hubs = discover_community_hubs(client, hub_search_terms)
    print(f"[OK] Found {len(community_hubs)} community hubs")

    # Discover influencers
    print("[DISCOVERY] Finding target influencers...")
    influencers = discover_target_influencers(client)
    print(f"[OK] Found {len(influencers)} potential influencers")

    # Analyze growth opportunities
    print("[ANALYSIS] Analyzing growth opportunities...")
    growth_analysis = analyze_audience_growth_opportunities(community_hubs, influencers)
    print(f"[OK] Identified {len(growth_analysis['high_value_targets'])} high-value targets")

    # Save discovery results
    today = today_str()
    discovery_data = {
        "discovery_date": today,
        "discovery_time": datetime.now().isoformat(),
        "community_hubs": community_hubs,
        "influencers": influencers,
        "growth_analysis": growth_analysis,
        "target_audience_segments": TARGET_AUDIENCE_SEGMENTS
    }

    # Update community discovery log
    discovery_log = load_json(COMMUNITY_DISCOVERY_LOG)
    if today not in discovery_log:
        discovery_log[today] = []
    discovery_log[today].append(discovery_data)
    save_json(COMMUNITY_DISCOVERY_LOG, discovery_log)

    # Save audience profiles
    save_json(AUDIENCE_PROFILES, {
        "last_updated": datetime.now().isoformat(),
        "segments": TARGET_AUDIENCE_SEGMENTS,
        "discovered_communities": community_hubs[:5],  # Top 5
        "key_influencers": influencers[:5]  # Top 5
    })

    # Log for monitoring integration
    log_run(
        "APU81CommunityDiscovery",
        "ok",
        f"Discovered {len(community_hubs)} hubs, {len(influencers)} influencers, "
        f"{len(growth_analysis['high_value_targets'])} high-value targets"
    )

    return {
        "community_hubs": len(community_hubs),
        "influencers": len(influencers),
        "high_value_targets": len(growth_analysis['high_value_targets']),
        "top_segment": growth_analysis["top_segments"][0][0] if growth_analysis["top_segments"] else None,
        "growth_recommendations": growth_analysis["growth_recommendations"]
    }


def main():
    """Main function with reporting."""
    results = run_community_discovery()

    if "error" in results:
        print(f"\n[ERROR] Community discovery failed: {results['error']}")
        return

    # Display results
    print(f"\n=== Community Discovery Results ===")
    print(f"Community Hubs: {results['community_hubs']}")
    print(f"Influencers: {results['influencers']}")
    print(f"High-Value Targets: {results['high_value_targets']}")
    print(f"Top Audience Segment: {results.get('top_segment', 'Unknown')}")

    print(f"\n=== Growth Recommendations ===")
    for i, rec in enumerate(results.get('growth_recommendations', []), 1):
        print(f"{i}. {rec}")

    print(f"\n=== Community Discovery Complete ===\n")


if __name__ == "__main__":
    main()