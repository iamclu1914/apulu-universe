"""
recycle_agent.py — Reposts best-performing images from 30+ days ago with fresh captions.
Schedule: Sunday 2pm weekly.
"""

import argparse
import json
import sys
sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from datetime import date, datetime, timedelta
from pathlib import Path
import requests

from vawn_config import (
    VAWN_DIR, EXPORTS_DIR, VAWN_PROFILE, load_json, save_json,
    get_anthropic_client, log_run, today_str,
)

CREDS_FILE = VAWN_DIR / "credentials.json"
LOG_FILE = VAWN_DIR / "posted_log.json"
RECYCLE_LOG = VAWN_DIR / "research" / "recycle_log.json"
BASE_URL = "https://apulustudio.onrender.com/api"
PLATFORMS = ["instagram", "tiktok", "threads", "x", "bluesky"]
BLUESKY_MAX_CHARS = 300
MIN_AGE_DAYS = 30
RECYCLE_COOLDOWN_DAYS = 60


def refresh_token():
    creds = load_json(CREDS_FILE)
    r = requests.post(f"{BASE_URL}/auth/refresh", json={"refresh_token": creds["refresh_token"]})
    r.raise_for_status()
    data = r.json()
    creds["access_token"] = data["access_token"]
    creds["refresh_token"] = data["refresh_token"]
    save_json(CREDS_FILE, creds)
    return data["access_token"]


def find_recyclable_images():
    """Find images posted 30+ days ago, ranked by platform count (most successful first)."""
    log = load_json(LOG_FILE)
    recycle_log = load_json(RECYCLE_LOG)
    today = date.today()
    cutoff = today - timedelta(days=MIN_AGE_DAYS)
    cooldown_cutoff = today - timedelta(days=RECYCLE_COOLDOWN_DAYS)

    # Images recently recycled
    recently_recycled = set()
    for fname, entries in recycle_log.items():
        for d in entries:
            try:
                if date.fromisoformat(d) > cooldown_cutoff:
                    recently_recycled.add(fname)
            except (ValueError, TypeError):
                pass

    candidates = []
    for fname, entries in log.items():
        if fname.startswith("_"):
            continue
        if fname in recently_recycled:
            continue
        if not (EXPORTS_DIR / fname).exists():
            continue

        # Count total platforms posted to across all dates
        total_platforms = 0
        oldest_date = None
        for d, platforms in entries.items():
            try:
                post_date = date.fromisoformat(d)
                if post_date <= cutoff:
                    if isinstance(platforms, list):
                        total_platforms += len(platforms)
                    if oldest_date is None or post_date < oldest_date:
                        oldest_date = post_date
            except (ValueError, TypeError):
                pass

        if total_platforms > 0 and oldest_date:
            candidates.append((total_platforms, fname))

    candidates.sort(key=lambda x: -x[0])
    return [fname for _, fname in candidates]


def generate_fresh_caption(filename):
    """Generate a completely fresh caption for a recycled image."""
    client = get_anthropic_client()

    prompt = f"""You are writing social media captions for Vawn — a Brooklyn/Atlanta rapper, lyrical, charismatic, J. Cole energy.

{VAWN_PROFILE}

IMAGE: {filename}
This is a RECYCLED post — it's been posted before. Write completely FRESH captions that feel new.

Write exactly 5 captions. Plain text only. No markdown.
INSTAGRAM: [3-5 lines, micro-story, hook first, punchline alone, end with question, 5-8 hashtags]
TIKTOK: [1-2 lines, the caption IS the hook, 3-5 hashtags]
THREADS: [1-3 raw sentences, texting energy, end with question, 1-2 hashtags]
X: [one bar or hot take, max 200 chars, 1-2 hashtags]
BLUESKY: [mirror X energy, max 250 chars, 1-2 hashtags]"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}]
    )

    import re
    raw = message.content[0].text
    captions = {}
    all_markers = ["instagram", "tiktok", "threads", "x", "bluesky"]
    marker_pattern = "|".join(re.escape(m.upper()) for m in all_markers)
    for key in all_markers:
        m = re.search(
            rf'(?m)^{re.escape(key.upper())}:\s*(.*?)(?=^(?:{marker_pattern}):|\Z)',
            raw, re.DOTALL
        )
        if m:
            captions[key] = re.sub(r'\*+|__+|-{2,}', '', m.group(1).strip()).strip()

    if "bluesky" in captions and len(captions["bluesky"]) > BLUESKY_MAX_CHARS:
        captions["bluesky"] = captions["bluesky"][:BLUESKY_MAX_CHARS].rsplit(" ", 1)[0]

    return captions


def upload_image(img_path, access_token):
    ext = str(img_path).rsplit(".", 1)[-1].lower()
    mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
                "mp4": "video/mp4"}
    mime = mime_map.get(ext, "application/octet-stream")
    with open(img_path, "rb") as f:
        r = requests.post(
            f"{BASE_URL}/posts/upload",
            headers={"Authorization": f"Bearer {access_token}"},
            files={"file": (Path(img_path).name, f, mime)}
        )
    r.raise_for_status()
    return r.json()["url"]


def post_platform(platform, media_url, caption, access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.post(f"{BASE_URL}/posts", headers=headers, json={
        "content": caption,
        "platforms": [platform],
        "media_urls": [media_url],
        "ai_generated": True,
    })
    r.raise_for_status()
    post_id = r.json()["id"]
    pub = requests.post(f"{BASE_URL}/posts/{post_id}/publish", headers=headers)
    pub.raise_for_status()
    try:
        pub_data = pub.json()
        if isinstance(pub_data, dict) and "results" in pub_data:
            for pid, result in pub_data["results"].items():
                if not result.get("success"):
                    print(f"[FAIL] {platform}: {result.get('error', 'unknown')}")
                    return False
    except Exception:
        pass
    print(f"[OK] {platform} recycled post published")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    today = today_str()
    print(f"\n=== Recycle Agent — {today} ===\n")

    candidates = find_recyclable_images()
    if not candidates:
        print("[INFO] No recyclable images found (all too recent or already recycled)")
        return

    chosen = candidates[0]
    print(f"[OK] Recycling: {chosen}")

    captions = generate_fresh_caption(chosen)
    print(f"[OK] Fresh captions generated for {len(captions)} platforms")

    access_token = refresh_token()
    img_path = EXPORTS_DIR / chosen

    # TikTok + Instagram: convert to video
    video_path = None
    try:
        from video_agent import make_tiktok_video
        video_path = make_tiktok_video(img_path, duration=15)
    except Exception as e:
        print(f"[WARN] Video gen failed: {e}")

    results = {}
    for platform in PLATFORMS:
        if platform not in captions:
            continue
        try:
            upload_path = video_path if (platform in ("tiktok", "instagram") and video_path) else img_path
            media_url = upload_image(upload_path, access_token)
            ok = post_platform(platform, media_url, captions[platform], access_token)
            results[platform] = ok
        except Exception as e:
            print(f"[FAIL] {platform}: {e}")
            results[platform] = False

    # Log recycled post
    if not args.test:
        recycle_log = load_json(RECYCLE_LOG)
        if chosen not in recycle_log:
            recycle_log[chosen] = []
        recycle_log[chosen].append(today)
        save_json(RECYCLE_LOG, recycle_log)

    succeeded = [p for p, ok in results.items() if ok]
    log_run("RecycleAgent", "ok" if succeeded else "error", f"Recycled {chosen}: {succeeded}")
    print(f"\n--- DONE — Recycled: {succeeded} ---\n")


if __name__ == "__main__":
    main()
