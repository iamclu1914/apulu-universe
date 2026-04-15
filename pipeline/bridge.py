"""
bridge.py -- Connects the Apulu Universe content pipeline to Vawn's posting system.
Runs after both systems have produced their daily output.

Reads from:
  - Pipeline discovery results (Apulu Universe/research/vawn/discovery/)
  - Pipeline ideation results (Apulu Universe/research/vawn/ideation/)
  - Vawn's daily_brief.json (written by research_company at 6:10am)
  - Vawn's metrics_log.json (engagement feedback)
  - Vawn's PILLAR_SCHEDULE (from vawn_config.py)

Writes to:
  - Vawn's daily_brief.json (appends pipeline trends + pipeline_intel key)
  - pipeline/config/pillar_context.json
  - pipeline/config/content_rules.json
  - pipeline/config/engagement_feedback.json
  - Vawn/research/cascade_queue.json (if cascade data exists)

Usage:
    python bridge.py              # full bridge run
    python bridge.py --dry-run    # show what would change without writing
"""

import argparse
import json
import shutil
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

BRIDGE_CONFIG_PATH = Path(__file__).parent / "config" / "bridge_config.json"


def load_bridge_config():
    return json.loads(BRIDGE_CONFIG_PATH.read_text(encoding="utf-8"))


def _load(path):
    p = Path(path)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def _save(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(
        json.dumps(data, indent=2, default=str, ensure_ascii=False),
        encoding="utf-8",
    )


def _human(n):
    if n is None:
        return "N/A"
    n = int(n)
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return f"{n:,}"


# ── 1. Enrich Daily Brief ────────────────────────────────────────────────────

def _convert_x_to_trend(item):
    author = item.get("author", {})
    s = item.get("scoring", {})
    text = (item.get("text", "") or "")[:150]
    return {
        "angle": f"[X] @{author.get('handle', '?')}: {text}",
        "format": "text",
        "platforms": ["X"],
        "hook": f"engagement={s.get('engagement', 0)}, velocity={s.get('velocity', 0):.1f}",
        "evidence": f"pipeline/x, score={s.get('score', 0):.0f}",
    }


def _convert_tiktok_to_trend(item):
    author = item.get("author", {})
    s = item.get("scoring", {})
    text = (item.get("text", "") or "")[:150]
    plays = _human(item.get("plays", 0))
    fmt = "reel" if (item.get("duration") or 0) <= 60 else "video"
    return {
        "angle": f"[TikTok] @{author.get('username', '?')} ({plays} plays): {text}",
        "format": fmt,
        "platforms": ["TikTok"],
        "hook": f"shares={item.get('shares', 0)}, virality={s.get('virality', 0):.0f}",
        "evidence": f"pipeline/tiktok, score={s.get('score', 0):.0f}",
    }


def _convert_ig_to_trend(item):
    author = item.get("author", {})
    s = item.get("scoring", {})
    caption = (item.get("caption", "") or "")[:150]
    fmt = "reel" if item.get("is_reel") else "photo"
    return {
        "angle": f"[IG] @{author.get('username', '?')}: {caption}",
        "format": fmt,
        "platforms": ["Instagram"],
        "hook": f"likes={item.get('likes', 0)}, eng_rate={s.get('engagement_rate', 0):.1f}%",
        "evidence": f"pipeline/instagram, score={s.get('score', 0):.0f}",
    }


def _convert_reddit_to_trend(item):
    s = item.get("scoring", {})
    sub = (item.get("subreddit", "") or "").replace("r/", "")
    title = (item.get("title", "") or "")[:150]
    return {
        "angle": f"[Reddit] r/{sub}: {title}",
        "format": "text",
        "platforms": ["Reddit"],
        "hook": f"upvotes={s.get('upvotes', 0)}, discussion={s.get('discussion', 0):.0f}",
        "evidence": f"pipeline/reddit, score={s.get('score', 0):.0f}",
    }


CONVERTERS = {
    "x": ("x_pipeline_results.json", _convert_x_to_trend),
    "tiktok": ("tiktok_pipeline_results.json", _convert_tiktok_to_trend),
    "instagram": ("ig_pipeline_results.json", _convert_ig_to_trend),
    "reddit": ("reddit_pipeline_results.json", _convert_reddit_to_trend),
}


def enrich_daily_brief(cfg, dry_run=False):
    """Append pipeline discovery trends to Vawn's daily_brief.json."""
    discovery_dir = Path(cfg["research_dir"]) / "discovery"
    brief_path = Path(cfg["daily_brief_path"])
    top_n = cfg.get("top_n_per_platform", 3)
    max_pipeline = cfg.get("max_pipeline_trends", 5)
    max_total = cfg.get("max_total_trends", 12)

    # Load existing brief
    brief = _load(brief_path)
    existing_trends = brief.get("trends", [])
    print(f"  [Brief] Existing trends: {len(existing_trends)}")

    # Check if pipeline already enriched today
    if brief.get("_pipeline_enriched") == str(date.today()):
        print(f"  [Brief] Already enriched today, skipping")
        return brief

    # Collect pipeline trends (only from fresh data < 24h old)
    pipeline_trends = []
    for platform in cfg.get("discovery_platforms", []):
        filename, converter = CONVERTERS.get(platform, (None, None))
        if not filename or not converter:
            continue
        filepath = discovery_dir / filename
        if not filepath.exists():
            continue
        # Check file freshness -- skip if older than 24h
        from datetime import timezone
        file_age_hours = (datetime.now() - datetime.fromtimestamp(filepath.stat().st_mtime)).total_seconds() / 3600
        if file_age_hours > 24:
            print(f"  [Brief] Skipping stale {platform} data ({file_age_hours:.0f}h old)")
            continue
        data = _load(filepath)
        if not data:
            continue
        top_items = data.get("top_20", [])[:top_n]
        for item in top_items:
            pipeline_trends.append(converter(item))

    # Cap pipeline trends
    pipeline_trends = pipeline_trends[:max_pipeline]
    print(f"  [Brief] Pipeline trends to add: {len(pipeline_trends)}")

    # Merge: existing trends first, then pipeline trends
    # Insert 2-3 pipeline insights at positions 2+ so content_agent picks them up
    # (content_agent reads trends[:4], post_vawn reads trends[:2])
    merged = []
    if len(existing_trends) >= 2:
        merged.extend(existing_trends[:2])  # positions 0-1: trend_agent (for post_vawn)
        merged.extend(pipeline_trends[:3])  # positions 2-4: pipeline (for content_agent)
        merged.extend(existing_trends[2:])  # positions 5+: remaining trend_agent
        merged.extend(pipeline_trends[3:])  # positions 7+: remaining pipeline
    else:
        merged.extend(existing_trends)
        merged.extend(pipeline_trends)

    # Cap total
    merged = merged[:max_total]

    # Load ideation intel if available
    ideation = _load(Path(cfg["research_dir"]) / "ideation" / "ideation_results.json")
    pipeline_intel = None
    if ideation.get("ideation"):
        ide = ideation["ideation"]
        pipeline_intel = {
            "saturated_angles": ide.get("competitive_landscape", {}).get("saturated_angles", []),
            "open_gaps": ide.get("competitive_landscape", {}).get("open_gaps", []),
            "performance_outliers": ide.get("competitive_landscape", {}).get("performance_outliers", []),
            "top_ideas": [
                {"title": i.get("title", ""), "format": i.get("format", ""), "confidence": i.get("confidence", "")}
                for i in ide.get("content_ideas", [])[:3]
            ],
        }

    # Update brief
    brief["trends"] = merged
    if pipeline_intel:
        brief["pipeline_intel"] = pipeline_intel
    brief["_pipeline_enriched"] = str(date.today())

    if dry_run:
        print(f"  [DRY RUN] Would write {len(merged)} trends to {brief_path}")
        if pipeline_intel:
            print(f"  [DRY RUN] Would add pipeline_intel with {len(pipeline_intel.get('top_ideas', []))} ideas")
        return brief

    # Backup before writing
    if brief_path.exists():
        backup = brief_path.with_suffix(".backup.json")
        shutil.copy2(brief_path, backup)

    _save(brief_path, brief)
    print(f"  [Brief] Wrote {len(merged)} trends ({len(existing_trends)} existing + {len(pipeline_trends)} pipeline)")
    return brief


# ── 2. Export Pillar Context ──────────────────────────────────────────────────

def export_pillar_context(cfg, dry_run=False):
    """Write pillar schedule + slot energy to pipeline config for ideation."""
    sys.path.insert(0, cfg["vawn_dir"])
    from vawn_config import PILLAR_SCHEDULE

    today = date.today()
    week_ahead = []
    for i in range(7):
        d = today + timedelta(days=i)
        pillar = PILLAR_SCHEDULE.get(d.weekday(), "Unknown")
        week_ahead.append({
            "date": str(d),
            "day": d.strftime("%A"),
            "pillar": pillar,
        })

    context = {
        "generated": datetime.now().isoformat(),
        "today": {
            "date": str(today),
            "day": today.strftime("%A"),
            "pillar": PILLAR_SCHEDULE.get(today.weekday(), "Unknown"),
        },
        "week_ahead": week_ahead,
        "pillar_guide": {
            "Awareness": "artist identity, brand positioning",
            "Lyric": "quotable bars, wordplay, lyric breakdown",
            "BTS": "studio process, behind-the-scenes, craft",
            "Engagement": "questions, relatable moments, community",
            "Conversion": "follow/save CTA, album anticipation",
            "Audience": "mirror comparable artist strategies",
            "Video": "cinematic, motion, visual storytelling",
        },
        "slot_energy": {
            "morning": "sharp, intentional, quiet confidence -- not loud motivation",
            "midday": "peak swagger, charismatic, commanding the room",
            "evening": "storytelling, depth, J. Cole wordplay, the night belongs to the thinkers",
        },
    }

    out_path = Path(cfg["pipeline_dir"]) / "config" / "pillar_context.json"
    if dry_run:
        print(f"  [DRY RUN] Would write pillar context: today={context['today']['pillar']}")
        return context

    _save(out_path, context)
    print(f"  [Pillar] Today: {context['today']['pillar']} ({context['today']['day']})")
    print(f"  [Pillar] Wrote to {out_path.name}")
    return context


# ── 3. Export Content Rules ───────────────────────────────────────────────────

def export_content_rules(cfg, dry_run=False):
    """Extract Vawn's content rules into shared config for pipeline use."""
    rules = {
        "generated": datetime.now().isoformat(),
        "never_say": [
            "stream", "listen", "press play", "available now",
            "grind don't stop", "built different", "level up",
            "stay focused", "no days off", "locked in",
            "embrace the process",
        ],
        "never_reference": [
            "track names like LYR02, TRACK 7 -- internal catalog IDs",
            "streaming platforms",
            "gospel content",
        ],
        "formatting": {
            "no_markdown": True,
            "no_emoji_decoration": True,
            "straight_quotes_only": True,
        },
        "platform_constraints": {
            "threads": {"no_hashtags": True, "uses_topics": True},
            "bluesky": {"max_chars": 250},
            "x": {"max_chars": 200},
            "tiktok": {"max_caption_lines": 2},
        },
        "platform_rules": {
            "instagram": "3-5 lines, micro-story, hook first, 5-10 hashtags at end",
            "tiktok": "1-2 lines ONLY, caption IS the hook, 3-5 hashtags",
            "threads": "1-3 raw sentences, end with question, NO hashtags -- uses Topics",
            "x": "One bar or hot take, max 200 chars, 1-2 hashtags",
            "bluesky": "Same energy as X, max 250 chars, 1-2 hashtags",
        },
        "voice": {
            "brand": "anti-hype, quiet authority, pattern recognition, earned confidence",
            "cadence": "T.I. authority + J. Cole depth",
            "avoid": "motivational poster language, generic rapper talk, forced metaphors",
        },
        "humanizer": {
            "ai_vocabulary_to_strip": [
                "additionally", "align with", "crucial", "delve", "emphasizing",
                "enduring", "enhance", "fostering", "garner", "highlight",
                "interplay", "intricate", "intricacies", "key", "landscape",
                "pivotal", "showcase", "tapestry", "testament", "underscore",
                "valuable", "vibrant",
            ],
            "significance_inflation": [
                "stands as", "serves as", "is a testament", "is a reminder",
                "vital role", "pivotal moment", "underscores", "highlights its importance",
                "reflects broader", "setting the stage", "key turning point",
                "evolving landscape", "indelible mark", "deeply rooted",
            ],
            "copula_avoidance": [
                "serves as", "stands as", "functions as", "marks a",
                "represents a", "boasts", "features", "offers",
            ],
            "superficial_ing_phrases": [
                "showcasing", "reflecting", "contributing to", "emphasizing",
                "highlighting", "underscoring", "ensuring", "cultivating",
                "fostering", "encompassing",
            ],
            "filler_phrases": [
                "In order to", "At this point in time", "It is important to note",
                "Due to the fact that", "has the ability to", "In the event that",
            ],
            "generic_closers": [
                "The future looks bright", "exciting times ahead",
                "journey toward excellence", "a step in the right direction",
            ],
            "sycophantic_artifacts": [
                "Great question!", "I hope this helps!", "Let me know if",
                "You're absolutely right",
            ],
            "style_rules": [
                "No em dash overuse -- replace with commas or periods",
                "No boldface/markdown in captions",
                "No emojis as decoration (genuine expression only)",
                "Straight quotes only, never curly",
                "No rule-of-three forced triplets",
                "No negative parallelism (not just X, it's Y)",
                "No synonym cycling for the same concept",
            ],
            "soul_rules": [
                "Have opinions -- react to things, don't just report them",
                "Vary rhythm -- short punchy then longer ones that breathe",
                "Acknowledge complexity -- mixed feelings are human",
                "Be specific about feelings, not vague about significance",
                "Let the punchline land alone on its own line",
                "Let some mess in -- perfect structure feels algorithmic",
                "Sound like a person texting real thoughts, not a press release",
            ],
        },
        "humanizer_required": True,
        "cta_rotation": [
            "save this if it hit",
            "send this to someone who needs to hear it",
            "drop a comment if you felt that",
            "follow for more -- album on the way",
            "",
            "",
        ],
    }

    out_path = Path(cfg["pipeline_dir"]) / "config" / "content_rules.json"
    if dry_run:
        print(f"  [DRY RUN] Would write content rules ({len(rules['never_say'])} never_say items)")
        return rules

    _save(out_path, rules)
    print(f"  [Rules] Wrote {out_path.name} ({len(rules['never_say'])} never_say, {len(rules['platform_rules'])} platform rules)")
    return rules


# ── 4. Export Engagement Scores ───────────────────────────────────────────────

def export_engagement_scores(cfg, dry_run=False):
    """Compute per-pillar engagement scores and export for ideation feedback."""
    sys.path.insert(0, cfg["vawn_dir"])
    from vawn_config import PILLAR_SCHEDULE

    metrics = _load(cfg["metrics_log_path"])
    if not metrics:
        print("  [Engagement] No metrics data found")
        return None

    WEIGHTS = {"likes": 1, "comments": 3, "saves": 5, "shares": 4,
               "reposts": 4, "retweets": 4, "views": 0.01, "replies": 3}

    week_ago = date.today() - timedelta(days=7)
    pillar_scores = {}
    platform_totals = {}

    for img, dates in metrics.items():
        if img.startswith("_"):
            continue
        for date_str, platforms in dates.items():
            try:
                d = date.fromisoformat(date_str)
            except (ValueError, TypeError):
                continue
            if d < week_ago:
                continue

            pillar = PILLAR_SCHEDULE.get(d.weekday(), "Unknown")
            day_score = 0

            for platform, pdata in platforms.items():
                if not isinstance(pdata, dict):
                    continue
                plat_score = 0
                for metric, value in pdata.items():
                    if metric.startswith("_"):
                        continue
                    plat_score += value * WEIGHTS.get(metric, 0)
                day_score += plat_score

                if platform not in platform_totals:
                    platform_totals[platform] = {"total": 0, "count": 0}
                platform_totals[platform]["total"] += plat_score
                platform_totals[platform]["count"] += 1

            pillar_scores[pillar] = pillar_scores.get(pillar, 0) + day_score

    best_pillar = max(pillar_scores, key=pillar_scores.get) if pillar_scores else "Unknown"
    best_score = pillar_scores.get(best_pillar, 0)

    recommendation = ""
    if best_score > 0:
        recommendation = (
            f"{best_pillar} pillar posts performed best this week "
            f"(score: {best_score:.0f}) -- lean into that energy"
        )

    feedback = {
        "generated": datetime.now().isoformat(),
        "pillar_scores": pillar_scores,
        "best_pillar": best_pillar,
        "best_pillar_score": best_score,
        "platform_performance": {
            p: {"avg_score": round(d["total"] / max(d["count"], 1), 1)}
            for p, d in platform_totals.items()
        },
        "recommendation": recommendation,
    }

    out_path = Path(cfg["pipeline_dir"]) / "config" / "engagement_feedback.json"
    if dry_run:
        print(f"  [DRY RUN] Would write engagement feedback: best={best_pillar} ({best_score:.0f})")
        return feedback

    _save(out_path, feedback)
    print(f"  [Engagement] Best pillar: {best_pillar} (score: {best_score:.0f})")
    print(f"  [Engagement] Wrote {out_path.name}")
    return feedback


# ── 5. Stage Cascade Posts ────────────────────────────────────────────────────

def stage_cascade_posts(cfg, dry_run=False):
    """Copy cascade output to Vawn's research dir as a staged post queue."""
    cascade_path = Path(cfg["research_dir"]) / "cascade" / "cascade_results.json"
    queue_path = Path(cfg["cascade_queue_path"])

    if not cascade_path.exists():
        print("  [Cascade] No cascade results found, skipping")
        return None

    cascade = _load(cascade_path)
    cascade_data = cascade.get("cascade", {})
    if not cascade_data or cascade_data.get("raw"):
        print("  [Cascade] Cascade data empty or unparsed, skipping")
        return None

    queue = _load(queue_path)
    posts = queue.get("posts", [])

    new_post = {
        "id": f"cascade_{date.today()}_{len(posts) + 1}",
        "status": "staged",
        "content": cascade_data,
        "source_title": cascade.get("source", ""),
        "staged_at": datetime.now().isoformat(),
    }

    if dry_run:
        print(f"  [DRY RUN] Would stage cascade post: {new_post['id']}")
        return new_post

    posts.append(new_post)
    queue["generated"] = datetime.now().isoformat()
    queue["posts"] = posts
    _save(queue_path, queue)
    print(f"  [Cascade] Staged post {new_post['id']} to {queue_path.name}")
    return new_post


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Bridge: Pipeline ↔ Vawn")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    args = parser.parse_args()

    cfg = load_bridge_config()
    dry = args.dry_run

    print(f"\n{'='*60}")
    print(f"  Apulu Universe Bridge")
    print(f"  Date: {date.today()}")
    if dry:
        print(f"  MODE: DRY RUN")
    print(f"{'='*60}")

    steps = [
        ("Enrich Daily Brief", lambda: enrich_daily_brief(cfg, dry)),
        ("Export Pillar Context", lambda: export_pillar_context(cfg, dry)),
        ("Export Content Rules", lambda: export_content_rules(cfg, dry)),
        ("Export Engagement Scores", lambda: export_engagement_scores(cfg, dry)),
        ("Stage Cascade Posts", lambda: stage_cascade_posts(cfg, dry)),
    ]

    results = {}
    for name, fn in steps:
        print(f"\n{'─'*40}")
        print(f"  {name}")
        print(f"{'─'*40}")
        try:
            result = fn()
            results[name] = "ok"
        except Exception as e:
            results[name] = f"error: {e}"
            print(f"  [ERROR] {e}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*60}")
    print(f"  Bridge Summary")
    print(f"{'='*60}")
    for name, status in results.items():
        marker = "[OK]" if status == "ok" else "[FAIL]"
        print(f"  {marker} {name}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
