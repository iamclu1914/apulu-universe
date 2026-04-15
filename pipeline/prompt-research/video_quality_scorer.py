"""
video_quality_scorer.py -- Scrapes TikTok/X for high-performing AI-generated videos.
Scores by engagement to identify what visual styles and techniques resonate with audiences.
Extracts creative patterns (not prompts) to feed back into the prompt generator.

Usage:
    python video_quality_scorer.py
    python video_quality_scorer.py --project prompt-generator
    python video_quality_scorer.py --platform tiktok
"""

import argparse
import math
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline_config import (
    load_project_config, get_apify_token, get_output_dir,
    save_json, now_iso, today_str,
)
from discovery.apify_client import ApifyRunner


def is_ai_video(item, platform):
    """Check if content is likely AI-generated based on hashtags and text."""
    text = ""
    hashtags = []

    if platform == "tiktok":
        text = (item.get("text", "") or "").lower()
        hashtags = [h.get("name", "").lower() for h in item.get("hashtags", []) if h]
    elif platform == "x":
        text = (item.get("text", "") or "").lower()
        hashtags = [h.lower() for h in item.get("hashtags", []) if h]

    ai_signals = [
        "higgsfield", "ai video", "ai generated", "ai film",
        "kling", "runway", "sora", "pika", "luma",
        "aivideo", "aifilm", "aiart", "ai animation",
        "text to video", "image to video",
    ]

    all_text = text + " " + " ".join(hashtags)
    return any(signal in all_text for signal in ai_signals)


def score_video_quality(item, platform):
    """Score an AI video by engagement signals."""
    if platform == "tiktok":
        plays = item.get("playCount", 0) or item.get("plays", 0) or 0
        likes = item.get("diggCount", 0) or item.get("likes", 0) or 0
        shares = item.get("shareCount", 0) or item.get("shares", 0) or 0
        comments = item.get("commentCount", 0) or item.get("comments", 0) or 0
        followers = item.get("authorMeta", {}).get("fans", 0) or 0
    else:  # x
        plays = item.get("viewCount", 0) or 0
        likes = item.get("likeCount", 0) or 0
        shares = item.get("retweetCount", 0) or 0
        comments = item.get("replyCount", 0) or 0
        followers = item.get("author", {}).get("followers", 0) or 0

    engagement = likes + (comments * 3) + (shares * 5)
    eng_rate = (engagement / max(plays, 1)) * 100 if plays > 0 else 0
    virality = shares * 5 + math.log10(max(plays, 1)) * 10

    return {
        "score": round(virality + (eng_rate * 2), 2),
        "plays": plays,
        "likes": likes,
        "shares": shares,
        "comments": comments,
        "engagement_rate": round(eng_rate, 2),
        "virality": round(virality, 2),
    }


def extract_creative_patterns(item, platform):
    """Extract what we can infer about the video's creative approach."""
    text = ""
    if platform == "tiktok":
        text = (item.get("text", "") or "").lower()
    else:
        text = (item.get("text", "") or "").lower()

    patterns = []

    # Camera/motion
    if any(w in text for w in ["camera", "pan", "zoom", "dolly", "tracking", "orbit"]):
        patterns.append("camera_movement")
    if any(w in text for w in ["cinematic", "film", "movie", "cinema"]):
        patterns.append("cinematic")
    if any(w in text for w in ["slow motion", "slowmo", "timelapse"]):
        patterns.append("tempo_effect")

    # Style
    if any(w in text for w in ["anime", "cartoon", "animated"]):
        patterns.append("anime_style")
    if any(w in text for w in ["realistic", "photorealistic", "hyperreal"]):
        patterns.append("photorealistic")
    if any(w in text for w in ["dark", "moody", "noir"]):
        patterns.append("dark_mood")
    if any(w in text for w in ["music video", "mv", "lyric video"]):
        patterns.append("music_video")

    # Subject
    if any(w in text for w in ["character", "person", "face", "portrait"]):
        patterns.append("character_focused")
    if any(w in text for w in ["landscape", "city", "nature", "aerial"]):
        patterns.append("environment")

    # Tool
    if "higgsfield" in text:
        patterns.append("higgsfield")
    if "kling" in text:
        patterns.append("kling")
    if "runway" in text:
        patterns.append("runway")

    return patterns or ["unclassified"]


def scrape_tiktok(runner, config):
    """Scrape TikTok for AI video content."""
    tt_config = config["pipelines"]["tiktok"]
    print(f"\n  [TikTok] Searching {len(tt_config['keywords'])} keywords...")

    input_data = {
        "searchQueries": tt_config["keywords"][:8],
        "resultsPerPage": tt_config.get("max_results", 30),
        "shouldDownloadVideos": False,
    }

    try:
        items = runner.run_actor(tt_config["actor"], input_data, timeout=180)
        return [("tiktok", item) for item in items if is_ai_video(item, "tiktok")]
    except Exception as e:
        print(f"  [ERROR] TikTok scrape failed: {e}")
        return []


def scrape_x(runner, config):
    """Scrape X for AI video content."""
    x_config = config["pipelines"]["x"]
    query = " OR ".join(f'"{kw}"' for kw in x_config["keywords"][:8])
    print(f"\n  [X] Searching keywords...")

    input_data = {
        "searchTerms": [query],
        "maxTweets": x_config.get("max_results", 50),
        "sort": "Top",
        "tweetLanguage": "en",
    }

    try:
        items = runner.run_actor(x_config["actor"], input_data, timeout=120)
        return [("x", item) for item in items if is_ai_video(item, "x")]
    except Exception as e:
        print(f"  [ERROR] X scrape failed: {e}")
        return []


def run(project_name="prompt-generator", platform=None):
    """Run the video quality scorer."""
    config = load_project_config(project_name)
    token = get_apify_token(config)
    runner = ApifyRunner(token)
    output_dir = get_output_dir(config, "discovery")

    print(f"\n{'='*60}")
    print(f"  Video Quality Scorer -- AI Video Engagement Analysis")
    print(f"{'='*60}")

    all_videos = []

    if platform in (None, "tiktok"):
        all_videos.extend(scrape_tiktok(runner, config))
    if platform in (None, "x"):
        all_videos.extend(scrape_x(runner, config))

    print(f"\n  {len(all_videos)} AI videos identified")

    # Score and enrich
    results = []
    for plat, item in all_videos:
        scoring = score_video_quality(item, plat)
        patterns = extract_creative_patterns(item, plat)

        if plat == "tiktok":
            author = item.get("authorMeta", {})
            text = (item.get("text", "") or "")[:300]
            url = item.get("webVideoUrl", "")
            music = item.get("musicMeta", {}).get("musicName", "") if item.get("musicMeta") else ""
        else:
            author = item.get("author", {})
            text = (item.get("text", "") or "")[:300]
            url = item.get("url", "")
            music = ""

        results.append({
            "platform": plat,
            "text": text,
            "author": author.get("name", author.get("userName", "?")),
            "scoring": scoring,
            "creative_patterns": patterns,
            "music": music,
            "url": url,
        })

    results.sort(key=lambda v: v["scoring"]["score"], reverse=True)

    # Save
    output = {
        "pipeline": "video-quality",
        "project": project_name,
        "generated": now_iso(),
        "total_videos": len(results),
        "top_20": results[:20],
        "all_results": results,
        "pattern_summary": _summarize_patterns(results),
    }
    save_json(output_dir / "video_quality_results.json", output)
    _write_obsidian(results, output.get("pattern_summary", {}), output_dir, project_name)

    # Print top 5
    print(f"\n  Top AI videos by engagement:")
    for i, v in enumerate(results[:5], 1):
        s = v["scoring"]
        pats = ", ".join(v["creative_patterns"])
        print(f"  {i}. [{v['platform']}] Score: {s['score']} | {s['plays']:,} plays | {s['shares']} shares")
        print(f"     Patterns: {pats}")
        print(f"     {v['text'][:80]}")
    print()

    return output


def _summarize_patterns(results):
    """Count pattern frequency across all results."""
    counts = {}
    for r in results:
        for p in r["creative_patterns"]:
            counts[p] = counts.get(p, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: -x[1]))


def _write_obsidian(results, pattern_summary, output_dir, project):
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [
        "---",
        f"title: Video Quality Research -- {today}",
        f"date: {today}",
        "tags:",
        "  - prompt-research/video-quality",
        f"  - project/{project}",
        "---",
        "",
        f"# AI Video Quality Research -- {today}",
        "",
        f"> [!info] {len(results)} AI videos scored by engagement",
        "",
        "## Pattern Frequency",
        "",
        "| Pattern | Count |",
        "|---------|-------|",
    ]
    for pat, count in pattern_summary.items():
        lines.append(f"| {pat} | {count} |")
    lines.append("")

    lines.append("## Top Performing Videos")
    lines.append("")
    for i, v in enumerate(results[:15], 1):
        s = v["scoring"]
        pats = ", ".join(f"`{p}`" for p in v["creative_patterns"])
        lines.append(f"### #{i} -- {v['platform'].upper()}")
        lines.append(f"**@{v['author']}** | Score: {s['score']} | {s['plays']:,} plays | {s['shares']} shares")
        lines.append(f"Patterns: {pats}")
        lines.append("")
        if v["text"]:
            lines.append(f"> [!quote]")
            lines.append(f"> {v['text'][:200]}")
            lines.append("")
        if v.get("url"):
            lines.append(f"[View]({v['url']})")
            lines.append("")

    md_path = output_dir / f"Video Quality Research -- {today}.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  [Obsidian] Wrote {md_path.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI video quality scorer")
    parser.add_argument("--project", default="prompt-generator")
    parser.add_argument("--platform", choices=["tiktok", "x"])
    args = parser.parse_args()
    run(args.project, args.platform)
