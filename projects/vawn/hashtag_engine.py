"""
hashtag_engine.py — Intelligent hashtag rotation to avoid shadowbans.
Returns a different mix of discovery + niche + branded tags per platform per post.
"""

import json
import random
import sys
sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from datetime import date
from pathlib import Path
from vawn_config import VAWN_DIR

ROTATION_LOG = VAWN_DIR / "research" / "hashtag_rotation_log.json"

# ── Hashtag Pools ──────────────────────────────────────────────────────────────

DISCOVERY = [
    "#hiphop", "#rap", "#newmusic", "#rapper", "#hiphopmusic", "#music",
    "#newartist", "#indiemusic", "#rapmusic", "#hiphopculture",
    "#musicislife", "#bars", "#realrap", "#rappers", "#hiphophead",
]

NICHE = [
    "#boombap", "#atlantarap", "#lyricalrap", "#trapsoul",
    "#undergroundhiphop", "#indierap", "#psychedelichiphop",
    "#consciousrap", "#atlantahiphop", "#lyricist", "#wordplay",
    "#realhiphop", "#boombapcity", "#soulhiphop", "#orchestralrap",
]

BRANDED = ["#vawn", "#vawnmusic", "#apulurecords"]

# Per-platform mix: (discovery_count, niche_count, branded_count)
# Threads uses Topics (not hashtags) — handled in post_vawn.py via API
PLATFORM_MIX = {
    "instagram": (3, 4, 2),   # 9 total
    "tiktok":    (1, 1, 1),   # 3 total
    "threads":   (0, 0, 0),   # topics via API, not hashtags
    "x":         (1, 1, 0),   # 2 total
    "bluesky":   (1, 1, 0),   # 2 total
}


def _load_log():
    if ROTATION_LOG.exists():
        return json.loads(ROTATION_LOG.read_text(encoding="utf-8"))
    return {}


def _save_log(data):
    ROTATION_LOG.parent.mkdir(exist_ok=True)
    ROTATION_LOG.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_rotation_tags():
    """
    Return a dict keyed by platform with a fresh set of hashtags.
    Tracks used combos per day to avoid repetition.
    """
    today = str(date.today())
    log = _load_log()

    if today not in log:
        log[today] = {}

    used_today = log[today]
    result = {}

    for platform, (disc_n, niche_n, brand_n) in PLATFORM_MIX.items():
        # Get previously used tags today for this platform
        prev_used = set(used_today.get(platform, []))

        # Pick from pools, avoiding repeats from earlier today
        disc_pool = [t for t in DISCOVERY if t not in prev_used]
        niche_pool = [t for t in NICHE if t not in prev_used]

        # If pools exhausted, reset
        if len(disc_pool) < disc_n:
            disc_pool = list(DISCOVERY)
        if len(niche_pool) < niche_n:
            niche_pool = list(NICHE)

        picked_disc = random.sample(disc_pool, min(disc_n, len(disc_pool)))
        picked_niche = random.sample(niche_pool, min(niche_n, len(niche_pool)))
        picked_brand = random.sample(BRANDED, min(brand_n, len(BRANDED)))

        tags = picked_disc + picked_niche + picked_brand
        random.shuffle(tags)

        result[platform] = " ".join(tags)

        # Track what we used
        if platform not in used_today:
            used_today[platform] = []
        used_today[platform].extend(tags)

    log[today] = used_today
    _save_log(log)

    return result


if __name__ == "__main__":
    tags = get_rotation_tags()
    for plat, t in tags.items():
        print(f"{plat:>12s}: {t}")
