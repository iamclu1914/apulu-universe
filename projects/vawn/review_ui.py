"""
review_ui.py — Vawn Social Media Post Review UI
Run: python review_ui.py
Opens at http://localhost:5555
"""

import base64
import io
import json
import os
import re
import random
import threading
import webbrowser
from datetime import date
from pathlib import Path

import anthropic
import requests
from flask import Flask, jsonify, request, send_file, abort
from PIL import Image, ImageDraw, ImageFont

# APU-112 Real-Time Engagement Metrics Integration
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))
try:
    from apu112_flask_integration import init_metrics_integration
    APU112_INTEGRATION_AVAILABLE = True
except ImportError as e:
    print(f"[WARNING] APU-112 metrics integration not available: {e}")
    APU112_INTEGRATION_AVAILABLE = False

# ── Config ────────────────────────────────────────────────────────────────────
VAWN_DIR   = Path(r"C:\Users\rdyal\Vawn")
EXPORTS_DIR = VAWN_DIR / "Social_Media_Exports"
CREDS_FILE  = VAWN_DIR / "credentials.json"
CONFIG_FILE = VAWN_DIR / "config.json"
LOG_FILE    = VAWN_DIR / "posted_log.json"
TEMP_DIR    = VAWN_DIR / "temp"
BASE_URL    = "https://apulustudio.onrender.com/api"

TEMP_DIR.mkdir(exist_ok=True)

PLATFORMS = ["instagram", "tiktok", "threads", "x", "bluesky"]
BLUESKY_MAX_CHARS = 300

CRON_CONFIG = {
    "morning": {
        "energy": "8am morning grind — motivational, speaking to the ones up early, locked-in hustle",
        "hook":   "curiosity hook OR story hook OR lyrical bar that lands like a punchline",
        "folders": {
            "instagram": "Instagram_Post_1080x1350_4-5",
            "threads":   "Threads_Post_1080x1350_4-5",
            "tiktok":    "TikTok_Post_1080x1920_9-16",
            "x":         "X_Post_1200x675_16-9",
            "bluesky":   "Bluesky_Post_1080x1080_1-1",
        }
    },
    "midday": {
        "energy": "12pm midday flex — confidence, swagger, peak of day, charismatic ladies man energy",
        "hook":   "contrarian hook OR value hook OR lyrical wordplay punchline",
        "folders": {
            "instagram": "Instagram_Reel_1080x1920_9-16",
            "threads":   "Threads_Post_1080x1350_4-5",
            "tiktok":    "TikTok_Reel_1080x1920_9-16",
            "x":         "X_Post_1200x675_16-9",
            "bluesky":   "Bluesky_Post_1080x1080_1-1",
        }
    },
    "evening": {
        "energy": "6pm evening — storytelling, depth, J. Cole wordplay, reflective but powerful",
        "hook":   "story hook OR emotional hook — start with the feeling, not the fact",
        "folders": {
            "instagram": "Instagram_Story_1080x1920_9-16",
            "threads":   "Threads_Post_1080x1350_4-5",
            "tiktok":    "TikTok_Post_1080x1920_9-16",
            "x":         "X_Post_1200x675_16-9",
            "bluesky":   "Bluesky_Post_1080x1080_1-1",
        }
    }
}

PLATFORM_RULES = {
    "instagram": "2-4 sentences max. Start with one specific detail from the image or moment. End with a line that makes someone feel something, then 5-10 hashtags on a new line.",
    "tiktok":    "First line = strong hook. Then 1-2 more lines. 3-5 hashtags. No motivational poster language.",
    "threads":   "Sound like a real person thinking out loud. Specific, a little vulnerable or funny. End with a real question. 1-2 hashtags max.",
    "x":         "One specific observation or take. Max 240 chars. No emojis unless perfect. 1-2 hashtags embedded.",
    "bluesky":   "Behind-the-curtain moment. Specific and personal. 1-2 hashtags. HARD LIMIT: under 300 characters total.",
}

PLATFORM_ICONS = {
    "instagram": "📸",
    "tiktok":    "🎵",
    "threads":   "🧵",
    "x":         "✖",
    "bluesky":   "🦋",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_json(path):
    p = Path(path)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}

def save_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")

def refresh_token():
    creds = load_json(CREDS_FILE)
    r = requests.post(f"{BASE_URL}/auth/refresh",
                      json={"refresh_token": creds["refresh_token"]}, timeout=30)
    r.raise_for_status()
    data = r.json()
    creds["access_token"] = data["access_token"]
    creds["refresh_token"] = data["refresh_token"]
    save_json(CREDS_FILE, creds)
    return data["access_token"]

def upload_image(img_path, access_token):
    img_path = Path(img_path)
    ext = img_path.suffix.lower().lstrip(".")
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else "image/png"
    with open(img_path, "rb") as f:
        r = requests.post(
            f"{BASE_URL}/posts/upload",
            headers={"Authorization": f"Bearer {access_token}"},
            files={"file": (img_path.name, f, mime)},
            timeout=60,
        )
    r.raise_for_status()
    return r.json()["url"]

def post_platform_api(platform, img_url, caption, access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.post(f"{BASE_URL}/posts", headers=headers, json={
        "content": caption, "platforms": [platform],
        "media_urls": [img_url], "ai_generated": True
    }, timeout=30)
    r.raise_for_status()
    post_id = r.json()["id"]
    pub = requests.post(f"{BASE_URL}/posts/{post_id}/publish", headers=headers, timeout=30)
    pub.raise_for_status()
    try:
        pub_data = pub.json()
        if isinstance(pub_data, dict) and "results" in pub_data:
            for pid, result in pub_data["results"].items():
                if not result.get("success"):
                    return False, result.get("error", "unknown error")
    except Exception:
        pass
    return True, None

def get_available_images(slot):
    """Return sorted list of images available in ALL platform folders for a slot, minus posted today."""
    folders = CRON_CONFIG[slot]["folders"]
    log = load_json(LOG_FILE)
    today = str(date.today())

    sets = []
    for folder_name in folders.values():
        folder = EXPORTS_DIR / folder_name
        if not folder.exists():
            continue
        files = {f for f in os.listdir(folder)
                 if f.lower().endswith((".jpg", ".jpeg", ".png"))}
        sets.append(files)

    if not sets:
        return []

    available = sets[0]
    for s in sets[1:]:
        available &= s

    posted_today = {
        fname for fname, entries in log.items()
        if not fname.startswith("_") and today in entries
    }

    unposted = sorted(available - posted_today)
    already_posted = sorted(available & posted_today)
    return unposted + already_posted  # unposted first

def generate_captions(filename, slot):
    config = load_json(CONFIG_FILE)
    client = anthropic.Anthropic(api_key=config["anthropic_api_key"])
    cc = CRON_CONFIG[slot]
    energy = cc["energy"]
    hook = cc["hook"]
    platform_list = "\n".join([f"- {p.upper()}: {rule}" for p, rule in PLATFORM_RULES.items()])

    prompt = f"""You are writing social media captions for Vawn — a Brooklyn/Atlanta rapper, lyrical, charismatic, J. Cole energy.

IMAGE: {filename}
Use the filename to infer the setting and mood. Write from what's actually in the image, not a generic idea about it.

TONE: {energy}
Use this to guide the emotional register only — do NOT reference the time of day literally. Never write "8am", "midday", "morning", "evening" in the caption.

HOOK TYPE: {hook}

NON-NEGOTIABLE RULES:
- NO generic hip-hop clichés: "grind don't stop", "built different", "no days off", "stay focused", "the journey", "level up", "locked in", "embrace the process"
- NO forced metaphors
- NO motivational poster language
- NO markdown — plain text only, no **, *, __, --
- Be specific. Reference what's actually in the image.
- Short sentences. Let lines breathe.
- NEVER reference the time of day.

Write exactly 5 captions:
INSTAGRAM: [caption]
TIKTOK: [caption]
THREADS: [caption]
X: [caption]
BLUESKY: [caption]

Platform rules:
{platform_list}"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text
    captions = {}
    for platform in PLATFORMS:
        marker = f"{platform.upper()}:"
        if marker in raw:
            start = raw.index(marker) + len(marker)
            nexts = [raw.index(f"{p.upper()}:") for p in PLATFORMS
                     if f"{p.upper()}:" in raw and raw.index(f"{p.upper()}:") > start]
            end = min(nexts) if nexts else len(raw)
            captions[platform] = raw[start:end].strip()

    for p in list(captions.keys()):
        captions[p] = re.sub(r'\*+|__+|-{2,}', '', captions[p]).strip()

    if "bluesky" in captions and len(captions["bluesky"]) > BLUESKY_MAX_CHARS:
        text = captions["bluesky"]
        cut = text[:BLUESKY_MAX_CHARS].rsplit(" ", 1)[0]
        captions["bluesky"] = cut

    return captions

def add_text_overlay(img_path, text, position="bottom"):
    img = Image.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    w, h = img.size

    font_size = max(36, h // 18)
    font = None
    for font_path in [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/Arial Bold.ttf",
        "C:/Windows/Fonts/verdanab.ttf",
        "C:/Windows/Fonts/calibrib.ttf",
    ]:
        try:
            font = ImageFont.truetype(font_path, size=font_size)
            break
        except Exception:
            continue
    if font is None:
        font = ImageFont.load_default()

    # Word-wrap text
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] > w - 60:
            if current:
                lines.append(current)
            current = word
        else:
            current = test
    if current:
        lines.append(current)

    # Measure total text block
    line_height = font_size + 8
    total_text_h = len(lines) * line_height
    bar_h = total_text_h + 48

    if position == "top":
        y0 = 20
    elif position == "center":
        y0 = (h - bar_h) // 2
    else:  # bottom
        y0 = h - bar_h - 20

    # Draw semi-transparent bar
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle([(0, y0), (w, y0 + bar_h)], fill=(0, 0, 0, 170))
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Draw each line centered
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        tx = (w - tw) // 2
        ty = y0 + 24 + i * line_height
        # Drop shadow
        draw.text((tx + 2, ty + 2), line, font=font, fill=(0, 0, 0, 180))
        draw.text((tx, ty), line, font=font, fill=(255, 255, 255))

    out = TEMP_DIR / f"overlay_{Path(img_path).name}"
    img.save(out, quality=95)
    return out

def make_thumbnail(img_path, max_w=400):
    """Return image as base64 JPEG thumbnail."""
    img = Image.open(img_path).convert("RGB")
    w, h = img.size
    if w > max_w:
        ratio = max_w / w
        img = img.resize((max_w, int(h * ratio)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=82)
    return base64.b64encode(buf.getvalue()).decode()

def update_log(filename, platforms_succeeded):
    log = load_json(LOG_FILE)
    today = str(date.today())
    if filename not in log:
        log[filename] = {}
    if today not in log[filename]:
        log[filename][today] = []
    for p in platforms_succeeded:
        if p not in log[filename][today]:
            log[filename][today].append(p)
    save_json(LOG_FILE, log)

# ── Flask App ─────────────────────────────────────────────────────────────────
app = Flask(__name__)

# Initialize APU-112 engagement metrics integration
if APU112_INTEGRATION_AVAILABLE:
    try:
        apu112_aggregator = init_metrics_integration(app)
        print("[APU-112] SUCCESS: Real-time engagement metrics integration initialized")
        print("[APU-112] Dashboard: http://localhost:5555/api/v1/metrics/live-dashboard")
        print("[APU-112] API docs: http://localhost:5555/api/v1/metrics/dashboard")
    except Exception as e:
        print(f"[APU-112] WARNING: Integration failed: {e}")
        APU112_INTEGRATION_AVAILABLE = False
else:
    print("[APU-112] ERROR: Integration not available - install requirements")

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return HTML_PAGE

@app.route("/api/images")
def api_images():
    slot = request.args.get("slot", "morning")
    if slot not in CRON_CONFIG:
        return jsonify({"error": "invalid slot"}), 400
    images = get_available_images(slot)
    today = str(date.today())
    log = load_json(LOG_FILE)
    posted_today = {
        fname for fname, entries in log.items()
        if not fname.startswith("_") and today in entries
    }
    result = [{"name": img, "posted_today": img in posted_today} for img in images]
    return jsonify(result)

@app.route("/api/generate", methods=["POST"])
def api_generate():
    data = request.json
    slot = data.get("slot", "morning")
    image = data.get("image")
    if not slot or not image:
        return jsonify({"error": "slot and image required"}), 400
    if slot not in CRON_CONFIG:
        return jsonify({"error": "invalid slot"}), 400
    try:
        captions = generate_captions(image, slot)
        # Also return thumbnail for each platform
        thumbs = {}
        for platform, folder_name in CRON_CONFIG[slot]["folders"].items():
            img_path = EXPORTS_DIR / folder_name / image
            if img_path.exists():
                thumbs[platform] = make_thumbnail(img_path)
        return jsonify({"captions": captions, "thumbnails": thumbs})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/preview/<slot>/<platform>")
def api_preview(slot, platform):
    image = request.args.get("image")
    if not image or slot not in CRON_CONFIG or platform not in CRON_CONFIG[slot]["folders"]:
        abort(404)
    folder_name = CRON_CONFIG[slot]["folders"][platform]
    img_path = EXPORTS_DIR / folder_name / image
    if not img_path.exists():
        abort(404)
    # Serve as thumbnail
    img = Image.open(img_path).convert("RGB")
    w, h = img.size
    max_w = 400
    if w > max_w:
        ratio = max_w / w
        img = img.resize((max_w, int(h * ratio)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=82)
    buf.seek(0)
    return send_file(buf, mimetype="image/jpeg")

@app.route("/api/overlay-preview", methods=["POST"])
def api_overlay_preview():
    data = request.json
    slot = data.get("slot")
    image = data.get("image")
    platform = data.get("platform")
    text = data.get("text", "")
    position = data.get("position", "bottom")

    if not all([slot, image, platform, text]):
        return jsonify({"error": "slot, image, platform, text required"}), 400
    if slot not in CRON_CONFIG or platform not in CRON_CONFIG[slot]["folders"]:
        return jsonify({"error": "invalid slot/platform"}), 400

    folder_name = CRON_CONFIG[slot]["folders"][platform]
    img_path = EXPORTS_DIR / folder_name / image
    if not img_path.exists():
        return jsonify({"error": "image not found"}), 404

    try:
        out_path = add_text_overlay(img_path, text, position)
        thumb = make_thumbnail(out_path)
        return jsonify({"preview": thumb})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/post", methods=["POST"])
def api_post():
    data = request.json
    slot = data.get("slot")
    image = data.get("image")
    platforms_data = data.get("platforms", [])  # [{platform, caption, overlay_text?, overlay_position?}]

    if not slot or not image or not platforms_data:
        return jsonify({"error": "slot, image, platforms required"}), 400

    try:
        access_token = refresh_token()
    except Exception as e:
        return jsonify({"error": f"Token refresh failed: {e}"}), 500

    results = {}
    succeeded = []

    for pdata in platforms_data:
        platform = pdata.get("platform")
        caption = pdata.get("caption", "")
        overlay_text = pdata.get("overlay_text", "").strip()
        overlay_position = pdata.get("overlay_position", "bottom")

        if platform not in CRON_CONFIG.get(slot, {}).get("folders", {}):
            results[platform] = {"success": False, "error": "invalid platform for slot"}
            continue

        folder_name = CRON_CONFIG[slot]["folders"][platform]
        img_path = EXPORTS_DIR / folder_name / image

        if not img_path.exists():
            results[platform] = {"success": False, "error": f"image not found: {img_path.name}"}
            continue

        # Apply overlay if requested
        upload_path = img_path
        if overlay_text:
            try:
                upload_path = add_text_overlay(img_path, overlay_text, overlay_position)
            except Exception as e:
                results[platform] = {"success": False, "error": f"Overlay failed: {e}"}
                continue

        # Bluesky cap
        if platform == "bluesky" and len(caption) > BLUESKY_MAX_CHARS:
            caption = caption[:BLUESKY_MAX_CHARS].rsplit(" ", 1)[0]

        try:
            img_url = upload_image(upload_path, access_token)
            ok, err = post_platform_api(platform, img_url, caption, access_token)
            results[platform] = {"success": ok, "error": err}
            if ok:
                succeeded.append(platform)
        except Exception as e:
            results[platform] = {"success": False, "error": str(e)}

    # Update log for succeeded platforms
    if succeeded:
        update_log(image, succeeded)

    return jsonify({"results": results, "succeeded": succeeded})

# ── HTML ──────────────────────────────────────────────────────────────────────

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Vawn — Post Review</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg:       #0a0a0a;
    --surface:  #141414;
    --surface2: #1e1e1e;
    --border:   #2a2a2a;
    --purple:   #7C3AED;
    --purple-h: #6D28D9;
    --purple-l: #8B5CF6;
    --text:     #f0f0f0;
    --muted:    #888;
    --success:  #22c55e;
    --error:    #ef4444;
    --warn:     #f59e0b;
  }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: 14px;
    min-height: 100vh;
  }

  /* ── Header ── */
  header {
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 16px 24px;
    display: flex;
    align-items: center;
    gap: 20px;
    position: sticky;
    top: 0;
    z-index: 100;
  }
  header h1 {
    font-size: 18px;
    font-weight: 700;
    letter-spacing: -.3px;
    color: var(--text);
  }
  header h1 span { color: var(--purple-l); }

  /* ── Controls ── */
  .controls {
    padding: 20px 24px;
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    align-items: flex-end;
    background: var(--surface);
    border-bottom: 1px solid var(--border);
  }
  .field { display: flex; flex-direction: column; gap: 6px; }
  .field label { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: .5px; }

  select, input[type="text"], textarea {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--text);
    font-size: 14px;
    padding: 8px 12px;
    outline: none;
    transition: border-color .15s;
  }
  select:focus, input[type="text"]:focus, textarea:focus {
    border-color: var(--purple);
  }
  select { cursor: pointer; min-width: 140px; }

  /* ── Buttons ── */
  .btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 600;
    padding: 9px 18px;
    transition: all .15s;
    white-space: nowrap;
  }
  .btn-primary { background: var(--purple); color: #fff; }
  .btn-primary:hover:not(:disabled) { background: var(--purple-h); }
  .btn-secondary { background: var(--surface2); color: var(--text); border: 1px solid var(--border); }
  .btn-secondary:hover:not(:disabled) { border-color: var(--purple); color: var(--purple-l); }
  .btn-success { background: var(--success); color: #fff; }
  .btn-success:hover:not(:disabled) { background: #16a34a; }
  .btn-sm { padding: 6px 12px; font-size: 12px; }
  .btn:disabled { opacity: .45; cursor: not-allowed; }

  /* ── Main layout ── */
  main { padding: 24px; max-width: 1400px; margin: 0 auto; }

  /* ── Platform tabs ── */
  .tab-bar {
    display: flex;
    gap: 4px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 24px;
    overflow-x: auto;
    padding-bottom: 0;
  }
  .tab-btn {
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    border-radius: 0;
    color: var(--muted);
    cursor: pointer;
    font-size: 13px;
    font-weight: 600;
    padding: 10px 18px;
    transition: all .15s;
    white-space: nowrap;
  }
  .tab-btn:hover { color: var(--text); }
  .tab-btn.active { color: var(--purple-l); border-bottom-color: var(--purple-l); }
  .tab-btn .badge {
    display: inline-block;
    background: var(--success);
    border-radius: 99px;
    font-size: 10px;
    padding: 1px 5px;
    margin-left: 4px;
    color: #fff;
  }
  .tab-btn .badge.fail { background: var(--error); }

  /* ── Platform panel ── */
  .platform-panels { display: none; }
  .platform-panels.ready { display: block; }

  .panel { display: none; }
  .panel.active { display: grid; grid-template-columns: 320px 1fr; gap: 24px; }

  @media (max-width: 900px) {
    .panel.active { grid-template-columns: 1fr; }
  }

  /* ── Image preview column ── */
  .img-col {}
  .img-preview-wrap {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
    cursor: pointer;
    position: relative;
    transition: border-color .15s;
  }
  .img-preview-wrap:hover { border-color: var(--purple); }
  .img-preview-wrap img {
    display: block;
    width: 100%;
    height: auto;
  }
  .img-placeholder {
    height: 260px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--muted);
    font-size: 13px;
  }
  .img-label {
    font-size: 11px;
    color: var(--muted);
    margin-top: 8px;
    text-align: center;
  }

  /* Overlay controls */
  .overlay-section {
    margin-top: 16px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px;
  }
  .overlay-section h4 {
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: .5px;
    color: var(--muted);
    margin-bottom: 10px;
  }
  .overlay-row { display: flex; gap: 8px; align-items: flex-end; flex-wrap: wrap; margin-bottom: 8px; }
  .overlay-row .field { flex: 1; min-width: 120px; }
  .overlay-row input { width: 100%; }
  .overlay-preview-img {
    border-radius: 8px;
    overflow: hidden;
    margin-top: 10px;
    display: none;
  }
  .overlay-preview-img img { width: 100%; display: block; }
  .overlay-status { font-size: 12px; color: var(--muted); margin-top: 6px; }

  /* ── Caption column ── */
  .caption-col {}
  .caption-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
  }
  .caption-header h3 { font-size: 15px; font-weight: 700; }
  .char-count { font-size: 12px; color: var(--muted); }
  .char-count.warn { color: var(--warn); }
  .char-count.over { color: var(--error); }

  textarea.caption-area {
    width: 100%;
    min-height: 160px;
    resize: vertical;
    line-height: 1.6;
    font-size: 14px;
    border-radius: 10px;
    padding: 12px;
  }

  .tiktok-extras {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-bottom: 12px;
  }

  .post-row {
    display: flex;
    gap: 10px;
    margin-top: 16px;
    align-items: center;
    flex-wrap: wrap;
  }
  .platform-status {
    font-size: 13px;
    padding: 6px 12px;
    border-radius: 6px;
    display: none;
  }
  .platform-status.success { display: inline; background: rgba(34,197,94,.15); color: var(--success); }
  .platform-status.error { display: inline; background: rgba(239,68,68,.15); color: var(--error); }

  /* ── Bottom bar ── */
  .bottom-bar {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: var(--surface);
    border-top: 1px solid var(--border);
    padding: 14px 24px;
    display: flex;
    gap: 12px;
    align-items: center;
    flex-wrap: wrap;
    z-index: 100;
    display: none;
  }
  .bottom-bar.visible { display: flex; }
  .bottom-bar-left { flex: 1; display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
  .post-all-status { font-size: 13px; color: var(--muted); }

  /* ── Loading spinner ── */
  .spinner {
    width: 18px; height: 18px;
    border: 2px solid rgba(255,255,255,.2);
    border-top-color: #fff;
    border-radius: 50%;
    animation: spin .7s linear infinite;
    display: inline-block;
    vertical-align: middle;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* ── Empty/generate state ── */
  .empty-state {
    text-align: center;
    padding: 80px 24px;
    color: var(--muted);
  }
  .empty-state .icon { font-size: 48px; margin-bottom: 16px; }
  .empty-state p { font-size: 15px; }

  /* ── Lightbox ── */
  #lightbox {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,.92);
    z-index: 1000;
    align-items: center;
    justify-content: center;
    cursor: zoom-out;
  }
  #lightbox.open { display: flex; }
  #lightbox img { max-width: 90vw; max-height: 90vh; border-radius: 8px; object-fit: contain; }

  /* ── Toast ── */
  #toast-container {
    position: fixed;
    bottom: 80px;
    right: 24px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    z-index: 999;
  }
  .toast {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 12px 16px;
    font-size: 13px;
    animation: slideIn .2s ease;
    max-width: 320px;
  }
  .toast.success { border-color: var(--success); color: var(--success); }
  .toast.error { border-color: var(--error); color: var(--error); }
  @keyframes slideIn { from { transform: translateX(20px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }

  /* scrollbar */
  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

  /* padding for fixed bottom bar */
  .spacer { height: 80px; }
</style>
</head>
<body>

<header>
  <h1>Vawn <span>Post Review</span></h1>
</header>

<div class="controls">
  <div class="field">
    <label>Slot</label>
    <select id="slot-select">
      <option value="morning">Morning (7:58am)</option>
      <option value="midday">Midday (11:58am)</option>
      <option value="evening">Evening (5:58pm)</option>
    </select>
  </div>
  <div class="field">
    <label>Image</label>
    <select id="image-select" style="min-width:280px;">
      <option value="">Loading…</option>
    </select>
  </div>
  <button class="btn btn-primary" id="generate-btn" onclick="generateCaptions()">
    ✨ Generate Captions
  </button>
</div>

<main>
  <div id="empty-state" class="empty-state">
    <div class="icon">🎙️</div>
    <p>Pick a slot and image, then click Generate Captions.</p>
  </div>

  <div id="platform-panels" class="platform-panels">
    <div class="tab-bar" id="tab-bar">
      <button class="tab-btn active" onclick="switchTab('instagram')" id="tab-instagram">📸 Instagram</button>
      <button class="tab-btn" onclick="switchTab('tiktok')" id="tab-tiktok">🎵 TikTok</button>
      <button class="tab-btn" onclick="switchTab('threads')" id="tab-threads">🧵 Threads</button>
      <button class="tab-btn" onclick="switchTab('x')" id="tab-x">✖ X</button>
      <button class="tab-btn" onclick="switchTab('bluesky')" id="tab-bluesky">🦋 Bluesky</button>
    </div>

    <!-- Instagram -->
    <div class="panel active" id="panel-instagram">
      <div class="img-col">
        <div class="img-preview-wrap" onclick="openLightbox('instagram')">
          <div class="img-placeholder" id="thumb-placeholder-instagram">No image</div>
          <img id="thumb-instagram" style="display:none" alt="Instagram preview">
        </div>
        <p class="img-label">1080×1350 — 4:5 Feed Post</p>
        <div class="overlay-section">
          <h4>Text Overlay</h4>
          <div class="overlay-row">
            <div class="field" style="flex:2">
              <label>Text</label>
              <input type="text" id="overlay-text-instagram" placeholder="e.g. New single out now">
            </div>
            <div class="field">
              <label>Position</label>
              <select id="overlay-pos-instagram">
                <option value="bottom">Bottom</option>
                <option value="top">Top</option>
                <option value="center">Center</option>
              </select>
            </div>
            <button class="btn btn-secondary btn-sm" onclick="previewOverlay('instagram')">Preview</button>
          </div>
          <div class="overlay-preview-img" id="overlay-preview-instagram">
            <img id="overlay-img-instagram" alt="Overlay preview">
          </div>
          <div class="overlay-status" id="overlay-status-instagram"></div>
        </div>
      </div>
      <div class="caption-col">
        <div class="caption-header">
          <h3>📸 Instagram Caption</h3>
          <span class="char-count" id="cc-instagram">0 chars</span>
        </div>
        <textarea class="caption-area" id="caption-instagram"
          oninput="updateCharCount('instagram')"
          placeholder="Caption will appear here after generation…"></textarea>
        <div class="post-row">
          <button class="btn btn-success" onclick="postSingle('instagram')">Post Instagram</button>
          <span class="platform-status" id="status-instagram"></span>
        </div>
      </div>
    </div>

    <!-- TikTok -->
    <div class="panel" id="panel-tiktok">
      <div class="img-col">
        <div class="img-preview-wrap" onclick="openLightbox('tiktok')">
          <div class="img-placeholder" id="thumb-placeholder-tiktok">No image</div>
          <img id="thumb-tiktok" style="display:none" alt="TikTok preview">
        </div>
        <p class="img-label" id="tiktok-img-label">1080×1920 — 9:16</p>
        <div class="overlay-section">
          <h4>Text Overlay</h4>
          <div class="overlay-row">
            <div class="field" style="flex:2">
              <label>Text</label>
              <input type="text" id="overlay-text-tiktok" placeholder="e.g. New single out now">
            </div>
            <div class="field">
              <label>Position</label>
              <select id="overlay-pos-tiktok">
                <option value="bottom">Bottom</option>
                <option value="top">Top</option>
                <option value="center">Center</option>
              </select>
            </div>
            <button class="btn btn-secondary btn-sm" onclick="previewOverlay('tiktok')">Preview</button>
          </div>
          <div class="overlay-preview-img" id="overlay-preview-tiktok">
            <img id="overlay-img-tiktok" alt="Overlay preview">
          </div>
          <div class="overlay-status" id="overlay-status-tiktok"></div>
        </div>
      </div>
      <div class="caption-col">
        <div class="tiktok-extras">
          <div class="field">
            <label>Title (shown on TikTok)</label>
            <input type="text" id="tiktok-title" placeholder="Short punchy title for the video…">
          </div>
          <div class="field">
            <label>Sound / Audio Note (add in-app after posting)</label>
            <input type="text" id="tiktok-sound" placeholder="e.g. trending sound name to add in TikTok app">
          </div>
        </div>
        <div class="caption-header">
          <h3>🎵 TikTok Caption</h3>
          <span class="char-count" id="cc-tiktok">0 chars</span>
        </div>
        <textarea class="caption-area" id="caption-tiktok"
          oninput="updateCharCount('tiktok')"
          placeholder="Caption will appear here after generation…"></textarea>
        <div class="post-row">
          <button class="btn btn-success" onclick="postSingle('tiktok')">Post TikTok</button>
          <span class="platform-status" id="status-tiktok"></span>
        </div>
      </div>
    </div>

    <!-- Threads -->
    <div class="panel" id="panel-threads">
      <div class="img-col">
        <div class="img-preview-wrap" onclick="openLightbox('threads')">
          <div class="img-placeholder" id="thumb-placeholder-threads">No image</div>
          <img id="thumb-threads" style="display:none" alt="Threads preview">
        </div>
        <p class="img-label">1080×1350 — 4:5</p>
        <div class="overlay-section">
          <h4>Text Overlay</h4>
          <div class="overlay-row">
            <div class="field" style="flex:2">
              <label>Text</label>
              <input type="text" id="overlay-text-threads" placeholder="e.g. New single out now">
            </div>
            <div class="field">
              <label>Position</label>
              <select id="overlay-pos-threads">
                <option value="bottom">Bottom</option>
                <option value="top">Top</option>
                <option value="center">Center</option>
              </select>
            </div>
            <button class="btn btn-secondary btn-sm" onclick="previewOverlay('threads')">Preview</button>
          </div>
          <div class="overlay-preview-img" id="overlay-preview-threads">
            <img id="overlay-img-threads" alt="Overlay preview">
          </div>
          <div class="overlay-status" id="overlay-status-threads"></div>
        </div>
      </div>
      <div class="caption-col">
        <div class="caption-header">
          <h3>🧵 Threads Caption</h3>
          <span class="char-count" id="cc-threads">0 chars</span>
        </div>
        <textarea class="caption-area" id="caption-threads"
          oninput="updateCharCount('threads')"
          placeholder="Caption will appear here after generation…"></textarea>
        <div class="post-row">
          <button class="btn btn-success" onclick="postSingle('threads')">Post Threads</button>
          <span class="platform-status" id="status-threads"></span>
        </div>
      </div>
    </div>

    <!-- X -->
    <div class="panel" id="panel-x">
      <div class="img-col">
        <div class="img-preview-wrap" onclick="openLightbox('x')">
          <div class="img-placeholder" id="thumb-placeholder-x">No image</div>
          <img id="thumb-x" style="display:none" alt="X preview">
        </div>
        <p class="img-label">1200×675 — 16:9</p>
        <div class="overlay-section">
          <h4>Text Overlay</h4>
          <div class="overlay-row">
            <div class="field" style="flex:2">
              <label>Text</label>
              <input type="text" id="overlay-text-x" placeholder="e.g. New single out now">
            </div>
            <div class="field">
              <label>Position</label>
              <select id="overlay-pos-x">
                <option value="bottom">Bottom</option>
                <option value="top">Top</option>
                <option value="center">Center</option>
              </select>
            </div>
            <button class="btn btn-secondary btn-sm" onclick="previewOverlay('x')">Preview</button>
          </div>
          <div class="overlay-preview-img" id="overlay-preview-x">
            <img id="overlay-img-x" alt="Overlay preview">
          </div>
          <div class="overlay-status" id="overlay-status-x"></div>
        </div>
      </div>
      <div class="caption-col">
        <div class="caption-header">
          <h3>✖ X Caption</h3>
          <span class="char-count" id="cc-x">0 chars</span>
        </div>
        <textarea class="caption-area" id="caption-x"
          oninput="updateCharCount('x')"
          placeholder="Caption will appear here after generation… (max 280 chars)"></textarea>
        <div class="post-row">
          <button class="btn btn-success" onclick="postSingle('x')">Post X</button>
          <span class="platform-status" id="status-x"></span>
        </div>
      </div>
    </div>

    <!-- Bluesky -->
    <div class="panel" id="panel-bluesky">
      <div class="img-col">
        <div class="img-preview-wrap" onclick="openLightbox('bluesky')">
          <div class="img-placeholder" id="thumb-placeholder-bluesky">No image</div>
          <img id="thumb-bluesky" style="display:none" alt="Bluesky preview">
        </div>
        <p class="img-label">1080×1080 — 1:1</p>
        <div class="overlay-section">
          <h4>Text Overlay</h4>
          <div class="overlay-row">
            <div class="field" style="flex:2">
              <label>Text</label>
              <input type="text" id="overlay-text-bluesky" placeholder="e.g. New single out now">
            </div>
            <div class="field">
              <label>Position</label>
              <select id="overlay-pos-bluesky">
                <option value="bottom">Bottom</option>
                <option value="top">Top</option>
                <option value="center">Center</option>
              </select>
            </div>
            <button class="btn btn-secondary btn-sm" onclick="previewOverlay('bluesky')">Preview</button>
          </div>
          <div class="overlay-preview-img" id="overlay-preview-bluesky">
            <img id="overlay-img-bluesky" alt="Overlay preview">
          </div>
          <div class="overlay-status" id="overlay-status-bluesky"></div>
        </div>
      </div>
      <div class="caption-col">
        <div class="caption-header">
          <h3>🦋 Bluesky Caption</h3>
          <span class="char-count" id="cc-bluesky">0 chars</span>
        </div>
        <textarea class="caption-area" id="caption-bluesky"
          oninput="updateCharCount('bluesky')"
          placeholder="Caption will appear here after generation… (max 300 chars)"></textarea>
        <div class="post-row">
          <button class="btn btn-success" onclick="postSingle('bluesky')">Post Bluesky</button>
          <span class="platform-status" id="status-bluesky"></span>
        </div>
      </div>
    </div>

  </div><!-- /platform-panels -->

  <div class="spacer"></div>
</main>

<!-- Bottom bar -->
<div class="bottom-bar" id="bottom-bar">
  <div class="bottom-bar-left">
    <span class="post-all-status" id="post-all-status"></span>
  </div>
  <button class="btn btn-primary" id="post-all-btn" onclick="postAll()">
    🚀 Post All Platforms
  </button>
</div>

<!-- Lightbox -->
<div id="lightbox" onclick="closeLightbox()">
  <img id="lightbox-img" src="" alt="Full size preview">
</div>

<!-- Toast container -->
<div id="toast-container"></div>

<script>
const PLATFORMS = ['instagram','tiktok','threads','x','bluesky'];
const CHAR_LIMITS = { x: 280, bluesky: 300 };

let state = {
  slot: 'morning',
  image: null,
  captions: {},
  thumbnails: {},      // base64 from /api/generate
  fullImages: {},      // full-size image URLs for lightbox
  currentTab: 'instagram',
  overlayPreviews: {}, // platform -> base64
};

// ── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('slot-select').addEventListener('change', e => {
    state.slot = e.target.value;
    loadImages();
  });
  document.getElementById('image-select').addEventListener('change', e => {
    state.image = e.target.value;
  });
  loadImages();
});

async function loadImages() {
  const sel = document.getElementById('image-select');
  sel.innerHTML = '<option value="">Loading…</option>';
  try {
    const r = await fetch(`/api/images?slot=${state.slot}`);
    const images = await r.json();
    sel.innerHTML = '';
    if (!images.length) {
      sel.innerHTML = '<option value="">No images available</option>';
      return;
    }
    images.forEach(img => {
      const opt = document.createElement('option');
      opt.value = img.name;
      opt.textContent = img.posted_today ? `✓ ${img.name}` : img.name;
      if (img.posted_today) opt.style.color = '#888';
      sel.appendChild(opt);
    });
    state.image = sel.value;
  } catch(e) {
    sel.innerHTML = '<option value="">Error loading images</option>';
    toast('Failed to load images: ' + e.message, 'error');
  }
}

// ── Generate ──────────────────────────────────────────────────────────────────
async function generateCaptions() {
  state.image = document.getElementById('image-select').value;
  state.slot  = document.getElementById('slot-select').value;
  if (!state.image) { toast('Please select an image', 'error'); return; }

  const btn = document.getElementById('generate-btn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Generating…';

  try {
    const r = await fetch('/api/generate', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ slot: state.slot, image: state.image })
    });
    const data = await r.json();
    if (data.error) throw new Error(data.error);

    state.captions = data.captions || {};
    state.thumbnails = data.thumbnails || {};
    state.overlayPreviews = {};

    // Populate captions & thumbnails
    PLATFORMS.forEach(p => {
      const ta = document.getElementById(`caption-${p}`);
      if (ta) {
        ta.value = state.captions[p] || '';
        updateCharCount(p);
      }

      // Show thumbnail
      const thumb = document.getElementById(`thumb-${p}`);
      const placeholder = document.getElementById(`thumb-placeholder-${p}`);
      if (state.thumbnails[p]) {
        thumb.src = `data:image/jpeg;base64,${state.thumbnails[p]}`;
        thumb.style.display = 'block';
        placeholder.style.display = 'none';
        state.fullImages[p] = `/api/preview/${state.slot}/${p}?image=${encodeURIComponent(state.image)}`;
      }

      // Reset overlay previews
      const op = document.getElementById(`overlay-preview-${p}`);
      if (op) op.style.display = 'none';
      const os = document.getElementById(`overlay-status-${p}`);
      if (os) os.textContent = '';

      // Reset status badges
      clearPlatformStatus(p);
    });

    // Show panels
    document.getElementById('empty-state').style.display = 'none';
    document.getElementById('platform-panels').classList.add('ready');
    document.getElementById('bottom-bar').classList.add('visible');

    switchTab(state.currentTab);
    toast('Captions generated!', 'success');
  } catch(e) {
    toast('Generation failed: ' + e.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '✨ Generate Captions';
  }
}

// ── Tabs ──────────────────────────────────────────────────────────────────────
function switchTab(p) {
  state.currentTab = p;
  PLATFORMS.forEach(pl => {
    document.getElementById(`panel-${pl}`).classList.toggle('active', pl === p);
    document.getElementById(`tab-${pl}`).classList.toggle('active', pl === p);
  });
}

// ── Char counter ──────────────────────────────────────────────────────────────
function updateCharCount(p) {
  const ta = document.getElementById(`caption-${p}`);
  const cc = document.getElementById(`cc-${p}`);
  if (!ta || !cc) return;
  const len = ta.value.length;
  const limit = CHAR_LIMITS[p];
  cc.textContent = limit ? `${len} / ${limit}` : `${len} chars`;
  cc.className = 'char-count';
  if (limit) {
    if (len > limit) cc.classList.add('over');
    else if (len > limit * 0.85) cc.classList.add('warn');
  }
}

// ── Overlay preview ───────────────────────────────────────────────────────────
async function previewOverlay(p) {
  const text = document.getElementById(`overlay-text-${p}`).value.trim();
  const position = document.getElementById(`overlay-pos-${p}`).value;
  const statusEl = document.getElementById(`overlay-status-${p}`);
  const previewWrap = document.getElementById(`overlay-preview-${p}`);
  const previewImg = document.getElementById(`overlay-img-${p}`);

  if (!text) { statusEl.textContent = 'Enter text first.'; return; }
  if (!state.image) { statusEl.textContent = 'Generate captions first.'; return; }

  statusEl.textContent = 'Generating preview…';
  try {
    const r = await fetch('/api/overlay-preview', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ slot: state.slot, image: state.image, platform: p, text, position })
    });
    const data = await r.json();
    if (data.error) throw new Error(data.error);
    previewImg.src = `data:image/jpeg;base64,${data.preview}`;
    previewWrap.style.display = 'block';
    state.overlayPreviews[p] = data.preview;
    statusEl.textContent = 'Preview updated.';
  } catch(e) {
    statusEl.textContent = 'Error: ' + e.message;
  }
}

// ── Post ──────────────────────────────────────────────────────────────────────
function buildPlatformPayload(p) {
  const caption = document.getElementById(`caption-${p}`)?.value || '';
  const overlay_text = document.getElementById(`overlay-text-${p}`)?.value?.trim() || '';
  const overlay_position = document.getElementById(`overlay-pos-${p}`)?.value || 'bottom';
  return { platform: p, caption, overlay_text, overlay_position };
}

async function postSingle(p) {
  if (!state.image) { toast('No image selected', 'error'); return; }
  const btn = document.querySelector(`#panel-${p} .btn-success`);
  if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> Posting…'; }

  try {
    const r = await fetch('/api/post', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        slot: state.slot,
        image: state.image,
        platforms: [buildPlatformPayload(p)]
      })
    });
    const data = await r.json();
    if (data.error) throw new Error(data.error);
    const result = data.results[p];
    if (result?.success) {
      setPlatformStatus(p, 'success', 'Posted!');
      setTabBadge(p, 'success');
      toast(`${p} posted!`, 'success');
    } else {
      setPlatformStatus(p, 'error', result?.error || 'Failed');
      setTabBadge(p, 'fail');
      toast(`${p} failed: ${result?.error || 'unknown error'}`, 'error');
    }
  } catch(e) {
    setPlatformStatus(p, 'error', e.message);
    setTabBadge(p, 'fail');
    toast(`${p} error: ${e.message}`, 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.innerHTML = `Post ${p.charAt(0).toUpperCase()+p.slice(1)}`; }
  }
}

async function postAll() {
  if (!state.image) { toast('No image selected', 'error'); return; }
  const btn = document.getElementById('post-all-btn');
  const statusEl = document.getElementById('post-all-status');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Posting all…';
  statusEl.textContent = '';

  const platforms = PLATFORMS.map(buildPlatformPayload);

  try {
    const r = await fetch('/api/post', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ slot: state.slot, image: state.image, platforms })
    });
    const data = await r.json();
    if (data.error) throw new Error(data.error);

    let succeeded = 0, failed = 0;
    PLATFORMS.forEach(p => {
      const result = data.results[p];
      if (result?.success) {
        setPlatformStatus(p, 'success', 'Posted!');
        setTabBadge(p, 'success');
        succeeded++;
      } else {
        setPlatformStatus(p, 'error', result?.error || 'Failed');
        setTabBadge(p, 'fail');
        failed++;
      }
    });

    const msg = `${succeeded} posted, ${failed} failed`;
    statusEl.textContent = msg;
    toast(msg, succeeded > 0 ? 'success' : 'error');
  } catch(e) {
    statusEl.textContent = 'Error: ' + e.message;
    toast('Post all failed: ' + e.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '🚀 Post All Platforms';
  }
}

// ── Status helpers ────────────────────────────────────────────────────────────
function setPlatformStatus(p, type, msg) {
  const el = document.getElementById(`status-${p}`);
  if (!el) return;
  el.className = `platform-status ${type}`;
  el.textContent = msg;
}

function clearPlatformStatus(p) {
  const el = document.getElementById(`status-${p}`);
  if (el) { el.className = 'platform-status'; el.textContent = ''; }
  const tab = document.getElementById(`tab-${p}`);
  if (tab) {
    const badge = tab.querySelector('.badge');
    if (badge) badge.remove();
  }
}

function setTabBadge(p, type) {
  const tab = document.getElementById(`tab-${p}`);
  if (!tab) return;
  let badge = tab.querySelector('.badge');
  if (!badge) {
    badge = document.createElement('span');
    badge.className = 'badge';
    tab.appendChild(badge);
  }
  badge.className = `badge ${type === 'fail' ? 'fail' : ''}`;
  badge.textContent = type === 'success' ? '✓' : '✗';
}

// ── Lightbox ──────────────────────────────────────────────────────────────────
function openLightbox(p) {
  const url = state.fullImages[p];
  if (!url) return;
  document.getElementById('lightbox-img').src = url;
  document.getElementById('lightbox').classList.add('open');
}
function closeLightbox() {
  document.getElementById('lightbox').classList.remove('open');
}
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeLightbox(); });

// ── Toast ─────────────────────────────────────────────────────────────────────
function toast(msg, type='') {
  const container = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.textContent = msg;
  container.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}
</script>
</body>
</html>
"""

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    def open_browser():
        import time
        time.sleep(1.2)
        webbrowser.open("http://localhost:5555")

    threading.Thread(target=open_browser, daemon=True).start()
    print("Vawn Post Review UI -> http://localhost:5555")
    app.run(host="0.0.0.0", port=5555, debug=False)
