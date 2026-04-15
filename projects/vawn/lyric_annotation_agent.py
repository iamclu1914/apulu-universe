"""
lyric_annotation_agent.py — Weekly lyric self-annotation Reel.
Vawn breaks down one of his own bars: inspiration, technique, personal reflection.
Renders as 4-slide slideshow Reel with audio.
Schedule: Wednesday 10am weekly.
"""

import argparse
import json
import random
import sys
sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from datetime import date
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import requests

from vawn_config import (
    VAWN_DIR, EXPORTS_DIR, VAWN_PROFILE, load_json, save_json,
    get_anthropic_client, log_run, today_str,
    CONTENT_CALENDAR, RESEARCH_DIR,
)

CREDS_FILE = VAWN_DIR / "credentials.json"
ANNOTATION_LOG = RESEARCH_DIR / "annotation_log.json"
BASE_URL = "https://apulustudio.onrender.com/api"
BLUESKY_MAX_CHARS = 250

# Colors
BG_COLOR = (18, 18, 18)
GOLD = (201, 168, 76)
WHITE = (255, 255, 255)
GREY = (136, 136, 136)
SLIDE_W, SLIDE_H = 1080, 1920


def get_font(size, bold=True):
    paths = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/verdanab.ttf" if bold else "C:/Windows/Fonts/verdana.ttf",
    ]
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def wrap_text(text, font, max_width):
    words = text.split()
    lines = []
    current = ""
    dummy = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(dummy)
    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def render_slide(header, body_text, slide_num):
    """Render a single annotation slide."""
    img = Image.new("RGB", (SLIDE_W, SLIDE_H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    margin = 80
    max_w = SLIDE_W - margin * 2

    # Header
    header_font = get_font(48, bold=True)
    draw.text((margin, 200), header, font=header_font, fill=GOLD)

    # Divider line
    draw.line([(margin, 280), (SLIDE_W - margin, 280)], fill=GOLD, width=2)

    # Body text
    body_font = get_font(38, bold=False)
    lines = wrap_text(body_text, body_font, max_w)
    y = 320
    for line in lines:
        draw.text((margin, y), line, font=body_font, fill=WHITE)
        y += 54

    # Footer
    footer_font = get_font(28, bold=False)
    draw.text((margin, SLIDE_H - 120), f"VAWN — LYRIC BREAKDOWN {slide_num}/4",
              font=footer_font, fill=GREY)

    return img


def pick_catalog_line():
    """Pick a bar from the daily brief's catalog lines."""
    brief = load_json(RESEARCH_DIR / "daily_brief.json")
    lines = brief.get("catalog_lines", [])

    # Filter out recently annotated
    ann_log = load_json(ANNOTATION_LOG)
    used_bars = {entry.get("bar") for entry in ann_log.values() if isinstance(entry, dict)}

    available = [l for l in lines if l.get("bar") not in used_bars]
    if not available:
        available = lines  # reset if all used

    if not available:
        return {
            "bar": "I don't carry anger — I carry receipts",
            "track": "GOT THAT IN WRITING",
            "territory": "Dependability",
            "context": "About remembering who showed up and who didn't",
            "_fallback": True,
        }

    return random.choice(available)


def generate_annotation(bar_info):
    """Use Claude to generate a 3-part annotation of the bar."""
    client = get_anthropic_client()

    prompt = f"""You are Vawn, breaking down one of your own bars for fans.

{VAWN_PROFILE}

THE BAR: "{bar_info['bar']}"
FROM: {bar_info.get('track', 'unreleased')}
THEMATIC TERRITORY: {bar_info.get('territory', '')}
CONTEXT: {bar_info.get('context', '')}

Write 3 short paragraphs (2-3 sentences each):

1. THE INSPIRATION — What life moment or observation sparked this line. Be specific and personal. Reference your twin girls, Atlanta, Brooklyn, the studio, whatever is real.

2. THE TECHNIQUE — Break down the wordplay, the cadence choice, the double meaning, the rhythm. Talk about it like a craftsman explaining their work.

3. THE REAL — The deeper meaning. What this line means to you beyond the surface. What you want listeners to feel.

Keep it raw and honest. No motivational cliches. Talk like you're explaining to a close friend in the studio, not writing a press release.

Format exactly as:
INSPIRATION: [text]
TECHNIQUE: [text]
REAL: [text]"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )

    import re
    raw = message.content[0].text
    sections = {}
    for key in ["inspiration", "technique", "real"]:
        m = re.search(
            rf'(?m)^{re.escape(key.upper())}:\s*(.*?)(?=^(?:INSPIRATION|TECHNIQUE|REAL):|\Z)',
            raw, re.DOTALL
        )
        if m:
            sections[key] = m.group(1).strip()

    return sections


def refresh_token():
    creds = load_json(CREDS_FILE)
    r = requests.post(f"{BASE_URL}/auth/refresh", json={"refresh_token": creds["refresh_token"]})
    r.raise_for_status()
    data = r.json()
    creds["access_token"] = data["access_token"]
    creds["refresh_token"] = data["refresh_token"]
    save_json(CREDS_FILE, creds)
    return data["access_token"]


def upload_media(path, access_token):
    ext = str(path).rsplit(".", 1)[-1].lower()
    mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "mp4": "video/mp4"}
    mime = mime_map.get(ext, "application/octet-stream")
    with open(path, "rb") as f:
        r = requests.post(
            f"{BASE_URL}/posts/upload",
            headers={"Authorization": f"Bearer {access_token}"},
            files={"file": (Path(path).name, f, mime)}
        )
    r.raise_for_status()
    return r.json()["url"]


def post_platform(platform, content, access_token, media_url=None):
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "content": content,
        "platforms": [platform],
        "ai_generated": True,
    }
    if media_url:
        payload["media_urls"] = [media_url]
    r = requests.post(f"{BASE_URL}/posts", headers=headers, json=payload)
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
    print(f"[OK] {platform} posted")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    today = today_str()
    print(f"\n=== Lyric Annotation Agent — {today} ===\n")

    # Pick a bar
    bar_info = pick_catalog_line()
    print(f"[OK] Bar: \"{bar_info['bar']}\"")
    print(f"[OK] Track: {bar_info.get('track', 'unknown')}")
    print(f"[OK] Territory: {bar_info.get('territory', '')}")

    # Generate annotation
    sections = generate_annotation(bar_info)
    print(f"[OK] Annotation generated: {len(sections)} sections")

    # Render 4 slides
    temp_dir = VAWN_DIR / "temp"
    temp_dir.mkdir(exist_ok=True)

    slide_paths = []
    # Slide 1: The bar
    s1 = render_slide("THE BAR", f'"{bar_info["bar"]}"\n\n— VAWN', 1)
    p1 = temp_dir / "annotation_slide_1.png"
    s1.save(p1, quality=95)
    slide_paths.append(p1)

    # Slide 2-4: Annotation sections
    headers = [("THE INSPIRATION", "inspiration", 2), ("THE TECHNIQUE", "technique", 3), ("THE REAL", "real", 4)]
    for header, key, num in headers:
        text = sections.get(key, "")
        s = render_slide(header, text, num)
        p = temp_dir / f"annotation_slide_{num}.png"
        s.save(p, quality=95)
        slide_paths.append(p)

    print(f"[OK] {len(slide_paths)} slides rendered")

    # Create slideshow Reel
    from video_agent import make_slideshow_reel
    reel_path = make_slideshow_reel(slide_paths, duration=15)

    # Post
    access_token = refresh_token()

    # Instagram + TikTok: slideshow Reel
    reel_url = upload_media(reel_path, access_token)
    results = {}
    for platform in ["instagram", "tiktok"]:
        caption = f'"{bar_info["bar"]}"\n\nBreaking down the bar. Swipe to see what went into it.\n\n#vawn #lyricalrap #barbreakdown #hiphop'
        try:
            ok = post_platform(platform, caption, access_token, media_url=reel_url)
            results[platform] = ok
        except Exception as e:
            print(f"[FAIL] {platform}: {e}")
            results[platform] = False

    # X, Threads, Bluesky: text-only (the bar)
    bar_text = f'"{bar_info["bar"]}" — VAWN'
    for platform in ["x", "threads", "bluesky"]:
        text = bar_text
        if platform == "threads":
            text = f'{bar_text}\n\nWhat do you hear in this line?'
        if platform == "bluesky" and len(text) > BLUESKY_MAX_CHARS:
            text = text[:BLUESKY_MAX_CHARS].rsplit(" ", 1)[0]
        try:
            ok = post_platform(platform, text, access_token)
            results[platform] = ok
        except Exception as e:
            print(f"[FAIL] {platform}: {e}")
            results[platform] = False

    # Log
    if not args.test:
        ann_log = load_json(ANNOTATION_LOG)
        ann_log[today] = {
            "bar": bar_info["bar"],
            "track": bar_info.get("track", ""),
            "platforms": {p: ok for p, ok in results.items()},
        }
        save_json(ANNOTATION_LOG, ann_log)

    # Cleanup slides
    for p in slide_paths:
        p.unlink(missing_ok=True)

    succeeded = [p for p, ok in results.items() if ok]
    log_run("LyricAnnotationAgent", "ok" if succeeded else "error", f"Bar: {bar_info['bar'][:50]}")
    print(f"\n--- DONE — Posted: {succeeded} ---\n")


if __name__ == "__main__":
    main()
