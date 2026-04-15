"""
post_vawn.py — Autonomous social media poster for Vawn
Usage: python post_vawn.py --cron morning|midday|evening
"""

import argparse
import json
import os
import random
import sys
from datetime import date
from pathlib import Path
import requests
import anthropic

# ── Config ─────────────────────────────────────────────────────────────────────
VAWN_DIR = Path(r"C:\Users\rdyal\Vawn")
EXPORTS_BASE = VAWN_DIR / "Social_Media_Exports"
# All platforms use same 9:16 images — single folder, no cropping
EXPORTS_DIR = EXPORTS_BASE
# Pre-made videos (Higgsfield, etc.) for posting to all outlets
VIDEOS_DIR = Path(r"G:\My Drive\Videos")
CREDS_FILE = VAWN_DIR / "credentials.json"
CONFIG_FILE = VAWN_DIR / "config.json"
LOG_FILE = VAWN_DIR / "posted_log.json"
BASE_URL = "https://apulustudio.onrender.com/api"

# Key used inside the log to track which slots have already been posted today.
# Prevents double-posting when both Windows Scheduler and Claude crons fire.
SLOT_KEY = "_posted_slots"

PLATFORMS = ["instagram", "tiktok", "threads", "x", "bluesky"]

# Smart CTA rotation — randomly selected per post. Two blanks = ~33% chance of no CTA.
CTA_POOL = [
    "save this if it hit",
    "send this to someone who needs to hear it",
    "drop a comment if you felt that",
    "follow for more — album on the way",
    "",  # no CTA — sometimes less is more
    "",  # weighted: 2 blank entries = 33% chance of no CTA
]

# Bluesky enforces a hard 300-char caption limit at the API level — captions
# exceeding this cause a 400 before the post is even created.
BLUESKY_MAX_CHARS = 300

METRICS_FILE = VAWN_DIR / "research" / "metrics_log.json"

# Engagement score weights (mirrors metrics_agent.py)
_WEIGHTS = {
    "likes": 1, "comments": 3, "saves": 5, "shares": 4,
    "reposts": 4, "retweets": 4, "views": 0.01, "replies": 3,
}

CRON_CONFIG = {
    "morning": {
        "energy": "9am — sharp, intentional, the one who's already been up. Quiet confidence, not loud motivation",
        "hook": "curiosity hook OR story hook OR lyrical bar that lands like a punchline",
        "keywords": ["casual", "portrait", "profile", "urban", "alley", "courtside", "party", "headshot", "grey-suit", "city-street", "house-party", "le-jardin"],
        "image_strategy": "keyword",
    },
    "midday": {
        "energy": "1pm — peak swagger, charismatic ladies man energy, commanding the room",
        "hook": "contrarian hook OR value hook OR lyrical wordplay punchline",
        "keywords": ["studio", "recording", "session", "booth", "headphones", "microphone", "mixer", "production", "vocal", "overhead", "penthouse", "vinyl"],
        "image_strategy": "keyword",
    },
    "evening": {
        "energy": "8pm prime time — storytelling, depth, J. Cole wordplay, the night belongs to the thinkers",
        "hook": "story hook OR emotional hook — start with the feeling, not the fact",
        "keywords": [],
        "image_strategy": "newest",
    }
}

PLATFORM_RULES = {
    "instagram": "3-5 lines that tell a micro-story or drop a revelation. First line is the hook — stop the scroll. Let a punchline sit alone on its own line. End with a question or call to save/share. 5-10 hashtags at the very end. This is the growth platform — give people a reason to stay.",
    "tiktok":    "1-2 lines ONLY. The caption IS the hook. Pattern-interrupt. 3-5 hashtags. Nothing else.",
    "threads":   "1-3 raw sentences. Talk like you're texting. End with a question. NO hashtags — Threads uses Topics not hashtags.",
    "x":         "One bar or hot take. Max 200 chars. 1-2 hashtags embedded. Let it land.",
    "bluesky":   "Same energy as X. One bar or hot take. Max 200 chars. 1-2 hashtags. Let it land. HARD LIMIT: under 250 chars total.",
}

# ── Helpers ─────────────────────────────────────────────────────────────────────

def load_json(path):
    if Path(path).exists():
        return json.loads(Path(path).read_text())
    return {}

def save_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2))


def load_image_scores():
    """
    Read metrics_log.json and return {image_filename: total_engagement_score}.
    Images with no metrics data return 0.
    """
    metrics = load_json(METRICS_FILE)
    scores = {}
    for img, dates in metrics.items():
        total = 0
        for date_str, platforms in dates.items():
            for platform, pdata in platforms.items():
                if not isinstance(pdata, dict):
                    continue
                for metric, value in pdata.items():
                    if metric.startswith("_"):
                        continue  # skip notes
                    weight = _WEIGHTS.get(metric, 0)
                    total += value * weight
        scores[img] = total
    return scores


def load_best_caption_style():
    """
    Identify which content pillar days got the highest engagement.
    Returns a guidance string for the caption prompt, or empty string.
    """
    from vawn_config import PILLAR_SCHEDULE
    from datetime import timedelta

    metrics = load_json(METRICS_FILE)
    if not metrics:
        return ""

    log = load_json(LOG_FILE)

    # Score each pillar by summing engagement across all images posted on pillar days
    pillar_scores = {}
    week_ago = date.today() - timedelta(days=7)

    for img, dates in metrics.items():
        for date_str, platforms in dates.items():
            try:
                d = date.fromisoformat(date_str)
            except (ValueError, TypeError):
                continue
            if d < week_ago:
                continue

            # Determine which pillar this day was
            weekday = d.weekday()
            pillar = PILLAR_SCHEDULE.get(weekday, "")
            if not pillar:
                continue

            day_score = 0
            for platform, pdata in platforms.items():
                if not isinstance(pdata, dict):
                    continue
                for metric, value in pdata.items():
                    if metric.startswith("_"):
                        continue
                    day_score += value * _WEIGHTS.get(metric, 0)

            pillar_scores[pillar] = pillar_scores.get(pillar, 0) + day_score

    if not pillar_scores:
        return ""

    best_pillar = max(pillar_scores, key=pillar_scores.get)
    best_score = pillar_scores[best_pillar]

    if best_score <= 0:
        return ""

    return (
        f"Posts with {best_pillar} theme performed best this week "
        f"(score: {best_score:.0f}) — lean into that energy"
    )


def refresh_token():
    creds = load_json(CREDS_FILE)
    r = requests.post(f"{BASE_URL}/auth/refresh", json={"refresh_token": creds["refresh_token"]})
    r.raise_for_status()
    data = r.json()
    creds["access_token"] = data["access_token"]
    creds["refresh_token"] = data["refresh_token"]
    save_json(CREDS_FILE, creds)
    print("[OK] Token refreshed")
    return data["access_token"]

def slot_already_posted(log, today, slot):
    """Return True if this time slot was already posted today (prevents double-posting)."""
    return log.get(SLOT_KEY, {}).get(today, {}).get(slot, False)

def mark_slot_posted(log, today, slot):
    if SLOT_KEY not in log:
        log[SLOT_KEY] = {}
    if today not in log[SLOT_KEY]:
        log[SLOT_KEY][today] = {}
    log[SLOT_KEY][today][slot] = True

def _weighted_pick(pool, scores):
    """
    Engagement-weighted image selection from a pool.
    70% chance: pick from top quartile by engagement score.
    30% chance: pick randomly (variety / discovery).
    Images with no data get a neutral score so they still get selected.
    """
    if not pool:
        return None

    if len(pool) == 1:
        return pool[0]

    # If no scores exist at all, fall back to pure random
    if not scores or all(scores.get(f, 0) == 0 for f in pool):
        return random.choice(pool)

    # Assign neutral score (median of scored images) to unscored ones
    scored_vals = [scores[f] for f in pool if scores.get(f, 0) > 0]
    neutral = sorted(scored_vals)[len(scored_vals) // 2] if scored_vals else 0

    ranked = sorted(pool, key=lambda f: scores.get(f, neutral), reverse=True)

    if random.random() < 0.70:
        # Top quartile
        cutoff = max(1, len(ranked) // 4)
        top = ranked[:cutoff]
        chosen = random.choice(top)
        print(f"[OK] Engagement-weighted pick (top quartile): {chosen} "
              f"(score: {scores.get(chosen, neutral):.0f})")
    else:
        # Random pick for variety
        chosen = random.choice(ranked)
        print(f"[OK] Random variety pick: {chosen} "
              f"(score: {scores.get(chosen, neutral):.0f})")

    return chosen


def pick_image(log, today, keywords=None, strategy="random"):
    """
    Pick an image from Social_Media_Exports (9:16 folder).
    All platforms use the same 1080x1920 images — no per-platform cropping.
    Uses engagement scores to weight toward higher-performing images.
    """
    import time
    now = time.time()
    ONE_DAY = 86400

    folder = EXPORTS_DIR
    if not folder.exists():
        raise RuntimeError(f"Export folder not found: {folder}")

    available = [
        f for f in os.listdir(folder)
        if f.lower().endswith((".jpg", ".jpeg", ".png")) and not os.path.isdir(folder / f)
    ]
    # Fallback: if no images in root, check 9:16 subfolder
    if not available:
        reel_folder = folder / "Instagram_Reel_1080x1920_9-16"
        if reel_folder.exists():
            available = [
                f for f in os.listdir(reel_folder)
                if f.lower().endswith((".jpg", ".jpeg", ".png"))
            ]
            if available:
                folder = reel_folder  # redirect to subfolder
                print("[WARN] Images found in subfolder — using Instagram_Reel_1080x1920_9-16")
    if not available:
        raise RuntimeError(f"No images in {folder}")

    # Exclude already posted today
    posted_today = {
        fname for fname, entries in log.items()
        if not fname.startswith("_") and today in entries
    }
    unposted = [f for f in available if f not in posted_today]

    if not unposted:
        print("[WARN] All images posted today — picking from full set")
        unposted = available

    # Load engagement scores for weighted selection
    scores = load_image_scores()

    def mtime(fname):
        try:
            return (folder / fname).stat().st_mtime
        except Exception:
            return 0

    if strategy == "newest":
        chosen = max(unposted, key=mtime)

    elif strategy == "keyword" and keywords:
        kw_lower = [k.lower() for k in keywords]
        matched = [f for f in unposted if any(k in f.lower() for k in kw_lower)]
        pool = matched if matched else unposted
        if not matched:
            print("[WARN] No keyword matches — using full unposted pool")
        recent = [f for f in pool if now - mtime(f) <= ONE_DAY]
        candidate_pool = recent if recent else pool
        chosen = _weighted_pick(candidate_pool, scores)

    else:
        chosen = _weighted_pick(unposted, scores)

    print(f"[OK] Image selected: {chosen}")
    return chosen


def pick_carousel_images(primary_image, log, today, count=4):
    """
    Pick additional images for an Instagram carousel.
    Returns list of filenames (including the primary) — max 5 total.
    Picks images with similar keywords in the filename.
    """
    folder = EXPORTS_DIR
    available = [
        f for f in os.listdir(folder)
        if f.lower().endswith((".jpg", ".jpeg", ".png")) and f != primary_image
    ]

    # Exclude already posted today
    posted_today = {
        fname for fname, entries in log.items()
        if not fname.startswith("_") and today in entries
    }
    unposted = [f for f in available if f not in posted_today]
    if len(unposted) < count:
        unposted = available

    # Try to pick thematically similar images (share keywords in filename)
    primary_words = set(Path(primary_image).stem.lower().replace("-", " ").split())
    scored = []
    for f in unposted:
        words = set(Path(f).stem.lower().replace("-", " ").split())
        overlap = len(primary_words & words)
        scored.append((overlap, f))
    scored.sort(key=lambda x: -x[0])

    extras = [f for _, f in scored[:count]]
    carousel = [primary_image] + extras
    print(f"[OK] Carousel: {len(carousel)} images")
    return carousel

def load_trending_hashtags():
    """Merge trending hashtags from scan + rotation engine. Returns dict keyed by platform.
    Threads gets NO hashtags — it uses Topics (appended separately in the posting loop)."""
    # 1. Load scanned trending tags (skip Threads — uses Topics not hashtags)
    hashtags_dir = EXPORTS_BASE / "Trending_Hashtags"
    trending = {}
    platform_map = {
        "instagram": "Instagram",
        "tiktok": "TikTok",
        "x": "X",
        "bluesky": "Bluesky",
    }
    for key, folder in platform_map.items():
        f = hashtags_dir / folder / "hashtags.txt"
        if f.exists():
            tags = [line.strip() for line in f.read_text(encoding="utf-8").splitlines() if line.strip()]
            trending[key] = " ".join(tags)
        else:
            trending[key] = ""
    trending["threads"] = ""  # no hashtags for Threads

    # 2. Merge with rotation engine (anti-shadowban variety)
    try:
        from hashtag_engine import get_rotation_tags
        rotation = get_rotation_tags()
        for platform in trending:
            if platform == "threads":
                continue  # no hashtags for Threads
            parts = [trending[platform], rotation.get(platform, "")]
            trending[platform] = " ".join(p for p in parts if p).strip()
    except Exception as e:
        print(f"[WARN] Hashtag rotation failed, using trending only: {e}")

    return trending

def load_content_context(cron_slot):
    """Load today's content context + trending angles from research company output."""
    calendar_path = VAWN_DIR / "research" / "content_calendar.json"
    brief_path = VAWN_DIR / "research" / "daily_brief.json"

    context = None
    # Calendar data
    if calendar_path.exists():
        try:
            data = json.loads(calendar_path.read_text(encoding="utf-8"))
            today = str(date.today())
            for day in data.get("calendar", []):
                if day.get("date") == today:
                    slot = day.get("slots", {}).get(cron_slot, {})
                    context = {
                        "pillar": day.get("pillar", ""),
                        "anchor_line": slot.get("anchor_line", ""),
                        "anchor_track": slot.get("anchor_track", ""),
                        "platform_angles": slot.get("platform_angles", {}),
                        "image_keyword": slot.get("image_keyword", []),
                        "trending_angles": [],
                    }
                    break
        except Exception:
            pass

    # Daily brief trending data — feed into captions
    if brief_path.exists() and context is not None:
        try:
            brief = json.loads(brief_path.read_text(encoding="utf-8"))
            trends = brief.get("trends", [])
            # Pick top 2 most relevant trends for caption inspiration
            context["trending_angles"] = [
                {"angle": t.get("angle", ""), "hook": t.get("hook", "")}
                for t in trends[:2]
            ]
        except Exception:
            pass

    return context

def _load_humanizer_rules():
    """Load humanizer rules from shared content_rules.json if available."""
    rules_path = Path(r"C:\Users\rdyal\Apulu Universe\pipeline\config\content_rules.json")
    if rules_path.exists():
        try:
            rules = json.loads(rules_path.read_text(encoding="utf-8"))
            return rules.get("humanizer", {})
        except Exception:
            pass
    return {}


def humanize_captions(client, captions):
    """
    Two-pass humanizer: strips AI writing patterns then audits for remaining tells.
    Reads rules from shared content_rules.json (exported by bridge).
    Skips tiktok_text since it's a short overlay label, not a caption.
    """
    platforms_to_humanize = [p for p in captions if p != "tiktok_text"]
    if not platforms_to_humanize:
        return captions

    blocks = "\n\n".join([
        f"{p.upper()}:\n{captions[p]}"
        for p in platforms_to_humanize
    ])

    # Load rules from shared config (bridge exports these)
    h = _load_humanizer_rules()
    ai_vocab = ", ".join(f'"{w}"' for w in h.get("ai_vocabulary_to_strip", []))
    inflation = ", ".join(f'"{w}"' for w in h.get("significance_inflation", []))
    copula = ", ".join(f'"{w}"' for w in h.get("copula_avoidance", []))
    ing_phrases = ", ".join(f'"{w}"' for w in h.get("superficial_ing_phrases", []))
    filler = ", ".join(f'"{w}"' for w in h.get("filler_phrases", []))
    closers = ", ".join(f'"{w}"' for w in h.get("generic_closers", []))
    sycophant = ", ".join(f'"{w}"' for w in h.get("sycophantic_artifacts", []))
    style = "\n".join(f"- {r}" for r in h.get("style_rules", []))
    soul = "\n".join(f"- {r}" for r in h.get("soul_rules", []))

    # Fallback if rules not loaded
    if not ai_vocab:
        ai_vocab = '"additionally", "align with", "crucial", "delve", "enduring", "enhance", "foster", "garner", "highlight", "interplay", "intricate", "key", "landscape", "pivotal", "showcase", "tapestry", "testament", "underscore", "valuable", "vibrant"'
    if not soul:
        soul = "- Have opinions. React to things, don't just report them.\n- Vary rhythm. Short punchy. Then longer ones that breathe.\n- Sound like a person texting real thoughts, not a press release."

    prompt = f"""You are a writing editor. The captions below were written by AI for a hip-hop artist named Vawn. Rewrite each one to remove AI writing patterns while keeping Vawn's voice — Brooklyn/Atlanta, lyrical, J. Cole energy, charismatic.

STRIP THESE AI PATTERNS:
- AI vocabulary: {ai_vocab}
- Significance inflation: {inflation}
- Copula avoidance (use "is"/"are"/"has" instead): {copula}
- Superficial -ing phrases: {ing_phrases}
- Filler phrases: {filler}
- Generic closers: {closers}
- Sycophantic artifacts: {sycophant}

STYLE RULES:
{style}

ADD SOUL — this is the most important part. Without this the captions are dead:
{soul}

VAWN'S VOICE — this is how he actually sounds:
- Brooklyn-raised, Atlanta-based. Not a motivational speaker. Not a brand account.
- Talks like he's telling you something over drinks, not performing for a camera
- Lets silence do the work. Doesn't over-explain.
- Punchlines sit alone. One line. Then space.
- References real things — the studio at midnight, the twins asleep, the coat he wore
- Has an opinion about everything but doesn't force it
- Quiet confidence. The opposite of loud.

ANTI-AI AUDIT — after rewriting, ask yourself: "Would a real person actually post this?" If the answer is "maybe on a brand account" then rewrite it again. Look for: uniform sentence length, neutral reporting tone, no personality, reads like it was assembled not written.

Keep all hashtags exactly as written. Keep character limits (X: 280 max, Bluesky: 300 max total including hashtags). Use straight quotes only. No markdown.

Return ONLY the final rewritten captions in this exact format, nothing else:

{chr(10).join([f"{p.upper()}:" for p in platforms_to_humanize])}

---

{blocks}"""

    try:
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        import re as _re
        raw = resp.content[0].text

        marker_pattern = "|".join(_re.escape(p.upper()) for p in platforms_to_humanize)
        for p in platforms_to_humanize:
            m = _re.search(
                rf'(?m)^{_re.escape(p.upper())}:\s*(.*?)(?=^(?:{marker_pattern}):|\Z)',
                raw,
                _re.DOTALL
            )
            if m:
                humanized = m.group(1).strip()
                humanized = _re.sub(r'\*+|__+|-{2,}', '', humanized).strip()
                humanized = humanized.replace('\u201c', '"').replace('\u201d', '"')
                humanized = humanized.replace('\u2018', "'").replace('\u2019', "'")
                if humanized:
                    captions[p] = humanized

        print("[OK] Humanizer pass complete (full skill sync)")
    except Exception as e:
        print(f"[WARN] Humanizer pass failed, using original captions: {e}")

    return captions

def generate_captions(filename, energy, hook, content_context=None):
    config = load_json(CONFIG_FILE)
    client = anthropic.Anthropic(api_key=config["anthropic_api_key"])
    cta = random.choice(CTA_POOL)

    platform_list = "\n".join([f"- {p.upper()}: {rule}" for p, rule in PLATFORM_RULES.items()])
    trending = load_trending_hashtags()
    hashtag_block = "\n".join([
        f"- {p.upper()}: {trending.get(p, '(none)')}"
        for p in ["instagram", "tiktok", "x", "bluesky"]
    ])

    context_block = ""
    if content_context:
        pillar = content_context.get("pillar", "")
        anchor = content_context.get("anchor_line", "")
        track = content_context.get("anchor_track", "")
        angles = content_context.get("platform_angles", {})
        angles_str = "\n".join([f"  - {p.upper()}: {a}" for p, a in angles.items()])
        context_block = f"""

CONTENT PILLAR FOR TODAY: {pillar}
This shapes the overall tone — stay within this pillar's intent.

ANCHOR LINE FROM CATALOG: "{anchor}" — from {track}
Weave this line or its theme into the captions where it fits naturally. Don't force it.

PLATFORM-SPECIFIC ANGLES (use these as creative direction):
{angles_str}"""

        # Add trending angles from daily research
        trending_angles = content_context.get("trending_angles", [])
        if trending_angles:
            trends_str = "\n".join([
                f"  - {t['angle'][:150]}"
                for t in trending_angles
            ])
            context_block += f"""

TRENDING IN HIP-HOP RIGHT NOW (ride these waves in your captions):
{trends_str}
Adapt these trends to Vawn's voice — don't copy, interpret."""

    # Engagement feedback — tell the model which pillar style resonates most
    best_style = load_best_caption_style()
    if best_style:
        context_block += f"""

ENGAGEMENT FEEDBACK: {best_style}"""

    prompt = f"""You are writing social media captions for Vawn — a Brooklyn/Atlanta rapper, lyrical, charismatic, J. Cole energy.

IMAGE: {filename}
Use the filename to infer the setting and mood. Write from what's actually in the image, not a generic idea about it.

TONE FOR THIS POST: {energy}
Use this to guide the emotional register only — do NOT reference the time of day literally in the caption. Never write "8am", "midday", "morning", "evening" in the caption.

HOOK TYPE: {hook}{context_block}

NON-NEGOTIABLE RULES:
- NO generic hip-hop clichés: "grind don't stop", "built different", "no days off", "stay focused", "the journey", "level up", "locked in", "embrace the process"
- NO forced metaphors — if the wordplay doesn't come naturally, skip it
- NO motivational poster language
- NO markdown — do not use **, *, __, --, or any formatting symbols. Plain text only.
- NO filler phrases that don't mean anything
- NEVER say "stream", "listen", "press play", "available now", or reference any streaming platform. The music is NOT released yet. This is brand-building content only.
- NEVER reference track names like "LYR02", "TRACK 7", etc. — these are internal catalog IDs, not real song titles. Do not mention them.
- Be specific. Reference what's actually happening in the image — the setting, the outfit, the energy, the moment
- Short sentences. Let lines breathe. A punchline should stand alone on its own line.
- NEVER reference the time of day based on the posting slot

CTA FOR THIS POST: "{cta}"
If a CTA is provided, weave it naturally into the Instagram caption (not as a separate line — make it feel organic). Do NOT add CTAs to X or Bluesky (too short). Threads can have it as the closing question. TikTok can have it if it fits in 1-2 lines.
If CTA is empty, skip it — no call to action needed.

Write exactly 6 items. Plain text only. No markdown. This exact format:
INSTAGRAM: [caption — this is the LONGEST one. 3-5 lines, micro-story, hook first, punchline alone, end with question or CTA, then hashtags]
TIKTOK_TEXT: [MUST start with "POV:" followed by 3-5 words max — burned onto the image as bold text. Example: "POV: you made it". No hashtags.]
TIKTOK: [caption — does NOT repeat the TIKTOK_TEXT line]
THREADS: [caption]
X: [caption — one bar or hot take, max 200 chars]
BLUESKY: [caption — MIRROR the X caption. Same energy, same brevity. One bar or hot take. Max 200 chars.]

Platform rules:
{platform_list}

TRENDING HASHTAGS (use these — already selected for today, append to each caption):
{hashtag_block}"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )

    import re as _re
    raw = message.content[0].text

    # Anchor each marker to start-of-line to avoid TIKTOK matching inside TIKTOK_TEXT
    all_markers = ["instagram", "tiktok_text", "tiktok", "threads", "x", "bluesky"]
    marker_pattern = "|".join(_re.escape(m.upper()) for m in all_markers)
    captions = {}
    for key in all_markers:
        m = _re.search(
            rf'(?m)^{_re.escape(key.upper())}:\s*(.*?)(?=^(?:{marker_pattern}):|\Z)',
            raw,
            _re.DOTALL
        )
        if m:
            captions[key] = m.group(1).strip()

    # Strip ALL markdown
    for k in list(captions.keys()):
        captions[k] = _re.sub(r'\*+|__+|-{2,}', '', captions[k]).strip()

    # Humanizer pass — strip AI writing patterns from each caption (skip tiktok_text overlay)
    captions = humanize_captions(client, captions)

    # Enforce Bluesky 300-char cap
    if "bluesky" in captions and len(captions["bluesky"]) > BLUESKY_MAX_CHARS:
        text = captions["bluesky"]
        cut = text[:BLUESKY_MAX_CHARS].rsplit(" ", 1)[0]
        captions["bluesky"] = cut
        print(f"[WARN] Bluesky caption truncated to {len(cut)} chars (was {len(text)})")

    if "tiktok_text" in captions:
        print(f"[OK] TikTok image text: {captions['tiktok_text']}")

    print(f"[OK] Captions generated for {len([p for p in PLATFORMS if p in captions])} platforms")
    return captions

def burn_text_on_image(img_path, text):
    """Burn bold text onto the upper third of an image (avoids TikTok UI at bottom). Returns path to modified copy."""
    from PIL import Image, ImageDraw, ImageFont
    img = Image.open(img_path).convert("RGB")
    w, h = img.size

    # Font — try bold system font, fallback gracefully
    font_size = max(36, h // 28)
    font = None
    for font_path in [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/Arial_Bold.ttf",
        "C:/Windows/Fonts/verdanab.ttf",
    ]:
        try:
            font = ImageFont.truetype(font_path, font_size)
            break
        except Exception:
            continue
    if font is None:
        font = ImageFont.load_default()

    # Measure text
    draw = ImageDraw.Draw(img)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

    # Semi-transparent black bar in upper third (TikTok UI covers bottom ~30%)
    bar_h = th + 60
    bar_y = h // 6  # place bar at ~17% from top
    overlay = Image.new("RGBA", (w, bar_h), (0, 0, 0, 190))
    img_rgba = img.convert("RGBA")
    img_rgba.paste(overlay, (0, bar_y), overlay)
    img = img_rgba.convert("RGB")

    # White text centered on the bar
    draw = ImageDraw.Draw(img)
    tx = (w - tw) // 2
    ty = bar_y + (bar_h - th) // 2
    # Shadow for readability
    draw.text((tx + 2, ty + 2), text, font=font, fill=(0, 0, 0, 200))
    draw.text((tx, ty), text, font=font, fill=(255, 255, 255))

    temp_dir = VAWN_DIR / "temp"
    temp_dir.mkdir(exist_ok=True)
    out_path = temp_dir / f"overlay_{img_path.name}"
    img.save(out_path, quality=95)
    print(f"[OK] Text overlay applied: '{text}' -> {out_path.name}")
    return out_path


def upload_image(img_path, access_token):
    ext = str(img_path).rsplit(".", 1)[-1].lower()
    mime_map = {
        "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
        "mp4": "video/mp4", "mov": "video/quicktime", "webm": "video/webm",
    }
    mime = mime_map.get(ext, "application/octet-stream")
    with open(img_path, "rb") as f:
        r = requests.post(
            f"{BASE_URL}/posts/upload",
            headers={"Authorization": f"Bearer {access_token}"},
            files={"file": (Path(img_path).name, f, mime)}
        )
    r.raise_for_status()
    return r.json()["url"]

def generate_alt_text(filename):
    """Generate accessibility alt text from the image filename."""
    # Parse descriptive filename: vawn-studio-headphones-dark.jpg → meaningful alt text
    stem = Path(filename).stem
    words = stem.replace("-", " ").replace("_", " ")
    # Capitalize and make it a proper description
    alt = f"Vawn — {words}"
    if len(alt) > 200:
        alt = alt[:197] + "..."
    return alt


# Threads topic tags — ONE per post, niche > broad for discoverability
# Smaller communities = less competition = more views per post
THREADS_TOPIC_TAGS = {
    "Awareness": ["#undergroundhiphop", "#indierap", "#rapartist"],
    "Lyric": ["#bars", "#lyricism", "#wordplay"],
    "BTS": ["#studiolife", "#beatmaking", "#musicproduction"],
    "Engagement": ["#rappers", "#hiphopculture", "#realrap"],
    "Conversion": ["#newartist", "#indiemusic", "#unsigned"],
    "Audience": ["#fatherhood", "#blackmen", "#atlanta"],
    "Video": ["#musicvideo", "#rapper", "#hiphophead"],
}


def get_threads_topic_tag(pillar=None):
    """Get a single niche topic tag for Threads discoverability."""
    if pillar and pillar in THREADS_TOPIC_TAGS:
        return random.choice(THREADS_TOPIC_TAGS[pillar])
    all_tags = [t for tags in THREADS_TOPIC_TAGS.values() for t in tags]
    return random.choice(all_tags)


def post_platform(platform, img_url, caption, access_token, alt_text="", post_type=None, threads_topic=None):
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "content": caption,
        "platforms": [platform],
        "media_urls": [img_url],
        "ai_generated": True,
    }
    if alt_text:
        payload["alt_text"] = alt_text
    if post_type:
        payload["post_type"] = post_type
    if threads_topic and platform == "threads":
        payload["threads_topic"] = threads_topic
    r = requests.post(f"{BASE_URL}/posts", headers=headers, json=payload)
    r.raise_for_status()
    post_id = r.json()["id"]
    pub = requests.post(f"{BASE_URL}/posts/{post_id}/publish", headers=headers)
    pub.raise_for_status()
    post_url = None
    try:
        pub_data = pub.json()
        if isinstance(pub_data, dict) and "results" in pub_data:
            for pid, result in pub_data["results"].items():
                if not result.get("success"):
                    err = result.get("error", "unknown error")
                    print(f"[FAIL] {platform} publish failed: {err}")
                    return False, None
                post_url = result.get("url") or result.get("platform_post_url")
    except Exception:
        pass
    print(f"[OK] {platform} posted")
    return True, post_url

# ── Main ─────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cron", choices=["morning", "midday", "evening"], required=True)
    parser.add_argument("--platforms", metavar="LIST",
                        help="Comma-separated platforms to post (e.g. x,bluesky). Default: all")
    parser.add_argument("--slideshow", action="store_true",
                        help="Post Instagram as slideshow Reel (5 images cycling with audio)")
    parser.add_argument("--test-platform", metavar="PLATFORM",
                        help="Test a single platform only — skips slot lock and log update")
    args = parser.parse_args()

    config = CRON_CONFIG[args.cron]
    today = str(date.today())
    test_mode = args.test_platform

    if test_mode:
        print(f"\n--- Vawn TEST: {test_mode.upper()} ({args.cron} slot) — {today} ---\n")
    else:
        print(f"\n--- Vawn {args.cron.upper()} POST — {today} ---\n")

    # 1. Load log + slot lock check (skip in test mode)
    # Use platform-group suffix so early/main slots don't block each other
    slot_key = f"{args.cron}_{args.platforms}" if args.platforms else args.cron
    log = load_json(LOG_FILE)
    if not test_mode and slot_already_posted(log, today, slot_key):
        print(f"[SKIP] {slot_key} already posted today — exiting to prevent duplicate post")
        return

    # 2. Refresh token
    access_token = refresh_token()

    # 2.5 Load content context from research company
    content_ctx = load_content_context(args.cron)
    if content_ctx:
        print(f"[OK] Content context loaded — pillar: {content_ctx['pillar']}")
        # Override image keywords if calendar provides them
        if content_ctx.get("image_keyword"):
            config = dict(config)  # make mutable copy
            config["keywords"] = content_ctx["image_keyword"]

    # 3. Pick image from single Social_Media_Exports folder
    chosen = pick_image(
        log, today,
        keywords=config.get("keywords", []),
        strategy=config.get("image_strategy", "random"),
    )

    # 4. Generate captions
    captions = generate_captions(chosen, config["energy"], config["hook"], content_context=content_ctx)

    # 5. Upload + post each platform
    if test_mode:
        platforms_to_run = [test_mode] if test_mode in PLATFORMS else []
        if not platforms_to_run:
            print(f"[ERROR] Platform '{test_mode}' not valid. Valid: {PLATFORMS}")
            return
    elif args.platforms:
        platforms_to_run = [p.strip() for p in args.platforms.split(",") if p.strip() in PLATFORMS]
        print(f"[OK] Platform filter: {platforms_to_run}")
    else:
        platforms_to_run = list(PLATFORMS)

    img_path = EXPORTS_DIR / chosen
    if not img_path.exists():
        print(f"[FAIL] Image not found: {img_path}")
        return

    # Generate alt text for accessibility (boosts IG + X algorithms)
    alt_text = generate_alt_text(chosen)
    print(f"[OK] Alt text: {alt_text}")

    # Post TikTok first — fastest discovery platform, captures URL for cross-linking
    post_order = sorted(platforms_to_run, key=lambda p: 0 if p == "tiktok" else 1)

    # Pick video: prefer pre-made videos from G:\My Drive\Videos\
    # and overlay a Vawn audio clip on top. Fall back to Ken Burns generation.
    video_path = None
    if VIDEOS_DIR.exists():
        vids = [f for f in VIDEOS_DIR.iterdir()
                if f.suffix.lower() in (".mp4", ".mov", ".webm")]
        if vids:
            import random
            src_video = random.choice(vids)
            print(f"[INFO] Using pre-made video: {src_video.name}")
            try:
                from video_agent import overlay_audio_on_video, pick_audio_clip
                audio_clip = pick_audio_clip()
                if audio_clip:
                    out_video = VAWN_DIR / "temp" / f"posted_{src_video.name}"
                    out_video.parent.mkdir(exist_ok=True)
                    video_path = overlay_audio_on_video(
                        src_video, out_video, audio_path=audio_clip, duration=15)
                else:
                    video_path = src_video
            except Exception as e:
                print(f"[WARN] Audio overlay failed: {e} — using video as-is")
                video_path = src_video
    if video_path is None:
        try:
            from video_agent import make_tiktok_video
            video_path = make_tiktok_video(img_path, duration=15)
        except Exception as e:
            print(f"[WARN] Video gen failed, TikTok/IG will post image: {e}")

    # Instagram: Reels by default (5.8% engagement, 55% non-follower views)
    # --slideshow flag: 5 images cycling with crossfades + audio (evening variety)
    ig_slideshow_path = None
    ig_carousel = None
    if args.slideshow and "instagram" in platforms_to_run:
        try:
            slideshow_files = pick_carousel_images(chosen, log, today, count=4)
            if len(slideshow_files) >= 3:
                slideshow_paths = [EXPORTS_DIR / f for f in slideshow_files if (EXPORTS_DIR / f).exists()]
                if len(slideshow_paths) >= 3:
                    from video_agent import make_slideshow_reel
                    ig_slideshow_path = make_slideshow_reel(slideshow_paths, duration=15)
        except Exception as e:
            print(f"[WARN] Slideshow gen failed, IG will post Ken Burns Reel: {e}")

    results = {}
    post_urls = {}
    for platform in post_order:
        caption = captions.get(platform, "")

        # Cross-platform linking: append TikTok URL to Threads/X if available
        tiktok_url = post_urls.get("tiktok")
        if tiktok_url and platform in ("threads", "x"):
            caption = f"{caption}\n\n{tiktok_url}"

        if platform == "bluesky":
            print(f"[INFO] Bluesky caption ({len(caption)} chars): {caption[:80]}{'...' if len(caption) > 80 else ''}")
        try:
            # TikTok + Instagram: use video with audio
            # Instagram slideshow Reel (--slideshow flag) overrides Ken Burns
            if platform == "instagram" and ig_slideshow_path:
                upload_path = ig_slideshow_path
            elif platform in ("tiktok", "instagram") and video_path:
                upload_path = video_path
            else:
                upload_path = img_path

            img_url = upload_image(upload_path, access_token)

            # Threads: append topic hashtag to trigger community/topic attachment
            post_caption = caption
            if platform == "threads":
                pillar = content_ctx.get("pillar") if content_ctx else None
                tag = get_threads_topic_tag(pillar)
                post_caption = f"{caption}\n\n{tag}"
                print(f"[OK] Threads topic tag: {tag}")

            ok, url = post_platform(platform, img_url, post_caption, access_token, alt_text=alt_text)
            results[platform] = ok
            if url:
                post_urls[platform] = url
        except Exception as e:
            print(f"[FAIL] {platform} FAILED: {e}")
            results[platform] = False

    # 5.5 Instagram Stories auto-repost — share the Reel to Stories for extra visibility
    if results.get("instagram") and not test_mode:
        try:
            story_url = upload_image(img_path, access_token)
            hook = captions.get("instagram", "").split("\n")[0][:100]  # first line as story caption
            ok_story, _ = post_platform("instagram", story_url, hook, access_token, post_type="story")
            if ok_story:
                print("[OK] Instagram Story auto-reposted")
        except Exception as e:
            print(f"[WARN] Story repost failed (non-critical): {e}")

    # 6. Update log (skipped in test mode)
    if not test_mode:
        if chosen not in log:
            log[chosen] = {}
        if today not in log[chosen]:
            log[chosen][today] = []
        for platform, success in results.items():
            if success and platform not in log[chosen][today]:
                log[chosen][today].append(platform)
        mark_slot_posted(log, today, slot_key)
        save_json(LOG_FILE, log)

    succeeded = [p for p, ok in results.items() if ok]
    failed = [p for p, ok in results.items() if not ok]
    print(f"\n--- DONE — Posted: {succeeded} | Failed: {failed} ---\n")

if __name__ == "__main__":
    main()
