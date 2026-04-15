"""
lyric_card_agent.py — Renders lyric card images (bar text on Vawn photo).
Reads content_calendar.json for today's lyric, renders to all 8 export folders.
Schedule: Windows Task Scheduler, 6:30am daily.
"""

import os
import random
import sys
sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from vawn_config import (
    load_json, CONTENT_CALENDAR, VAWN_DIR, VAWN_PICS, EXPORTS_DIR,
    log_run, today_str,
)

# Single output: 1080×1920 (9:16) for all platforms
TARGET_W, TARGET_H = 1080, 1920


def pick_base_image(keywords=None):
    images = [
        f for f in os.listdir(VAWN_PICS)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
        and f.startswith("vawn-")
    ]
    if not images:
        raise RuntimeError("No vawn- prefixed images found in Vawn Pics folder")
    if keywords:
        kw_lower = [k.lower() for k in keywords]
        matched = [f for f in images if any(k in f.lower() for k in kw_lower)]
        if matched:
            images = matched
    return VAWN_PICS / random.choice(images)


def get_font(size):
    for path in [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/Arial_Bold.ttf",
        "C:/Windows/Fonts/verdanab.ttf",
    ]:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def wrap_text(text, font, max_width, draw):
    words = text.split()
    lines = []
    current = ""
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


def _render_classic(img, bar_text, target_w, target_h):
    """Template 1: CLASSIC — blurred photo background, dark overlay, white text, gold attribution."""
    bg = img.copy().resize((target_w, target_h), Image.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(radius=28))
    bg = bg.point(lambda p: int(p * 0.45))

    sw, sh = img.size
    scale = min(target_w / sw, target_h / sh)
    nw, nh = int(sw * scale), int(sh * scale)
    fg = img.resize((nw, nh), Image.LANCZOS)
    bg.paste(fg, ((target_w - nw) // 2, (target_h - nh) // 2))

    draw = ImageDraw.Draw(bg)
    margin = int(target_w * 0.08)
    max_text_w = target_w - (margin * 2)

    bar_font_size = max(32, target_h // 22)
    bar_font = get_font(bar_font_size)
    lines = wrap_text(f'"{bar_text}"', bar_font, max_text_w, draw)

    attr_font_size = max(20, target_h // 40)
    attr_font = get_font(attr_font_size)

    line_height = bar_font_size + 8
    total_h = len(lines) * line_height + attr_font_size + 20

    overlay_y = target_h - total_h - int(target_h * 0.12)
    overlay_h = total_h + int(target_h * 0.08)
    overlay = Image.new("RGBA", (target_w, overlay_h), (0, 0, 0, 178))
    bg_rgba = bg.convert("RGBA")
    bg_rgba.paste(overlay, (0, overlay_y), overlay)
    bg = bg_rgba.convert("RGB")
    draw = ImageDraw.Draw(bg)

    y = overlay_y + int(target_h * 0.03)
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=bar_font)
        tw = bbox[2] - bbox[0]
        x = (target_w - tw) // 2
        draw.text((x + 2, y + 2), line, font=bar_font, fill=(0, 0, 0))
        draw.text((x, y), line, font=bar_font, fill=(255, 255, 255))
        y += line_height

    y += 10
    attr_text = "— VAWN"
    bbox = draw.textbbox((0, 0), attr_text, font=attr_font)
    tw = bbox[2] - bbox[0]
    draw.text(((target_w - tw) // 2, y), attr_text, font=attr_font, fill=(201, 168, 76))

    return bg


def _render_minimal(bar_text, target_w, target_h):
    """Template 2: MINIMAL — solid black, centered white text, gold horizontal rules."""
    bg = Image.new("RGB", (target_w, target_h), (18, 18, 18))
    draw = ImageDraw.Draw(bg)

    margin = int(target_w * 0.10)
    max_text_w = target_w - (margin * 2)

    bar_font_size = max(36, target_h // 20)
    bar_font = get_font(bar_font_size)
    lines = wrap_text(f'"{bar_text}"', bar_font, max_text_w, draw)

    attr_font_size = max(18, target_h // 50)
    attr_font = get_font(attr_font_size)

    line_height = bar_font_size + 10
    text_block_h = len(lines) * line_height
    rule_gap = 30
    attr_gap = 20
    total_block_h = rule_gap + text_block_h + rule_gap + attr_gap + attr_font_size

    start_y = (target_h - total_block_h) // 2

    # Top gold rule
    rule_x1 = margin
    rule_x2 = target_w - margin
    rule_y_top = start_y
    draw.line([(rule_x1, rule_y_top), (rule_x2, rule_y_top)], fill=(201, 168, 76), width=2)

    # Quote text
    y = rule_y_top + rule_gap
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=bar_font)
        tw = bbox[2] - bbox[0]
        x = (target_w - tw) // 2
        draw.text((x, y), line, font=bar_font, fill=(255, 255, 255))
        y += line_height

    # Bottom gold rule
    rule_y_bottom = y
    draw.line([(rule_x1, rule_y_bottom), (rule_x2, rule_y_bottom)], fill=(201, 168, 76), width=2)

    # Attribution
    y = rule_y_bottom + attr_gap
    attr_text = "— VAWN"
    bbox = draw.textbbox((0, 0), attr_text, font=attr_font)
    tw = bbox[2] - bbox[0]
    draw.text(((target_w - tw) // 2, y), attr_text, font=attr_font, fill=(136, 136, 136))

    return bg


def _render_split(img, bar_text, target_w, target_h):
    """Template 3: SPLIT — photo top half, dark bottom half with text, gold right-aligned attribution."""
    bg = Image.new("RGB", (target_w, target_h), (26, 26, 26))

    # Top half: crop photo to fill
    half_h = target_h // 2
    sw, sh = img.size
    scale = max(target_w / sw, half_h / sh)
    nw, nh = int(sw * scale), int(sh * scale)
    resized = img.resize((nw, nh), Image.LANCZOS)
    # Center-crop to target_w x half_h
    cx = (nw - target_w) // 2
    cy = (nh - half_h) // 2
    cropped = resized.crop((cx, cy, cx + target_w, cy + half_h))
    bg.paste(cropped, (0, 0))

    draw = ImageDraw.Draw(bg)
    margin = int(target_w * 0.10)
    max_text_w = target_w - (margin * 2)

    bar_font_size = max(32, target_h // 22)
    bar_font = get_font(bar_font_size)
    lines = wrap_text(f'"{bar_text}"', bar_font, max_text_w, draw)

    attr_font_size = max(20, target_h // 40)
    attr_font = get_font(attr_font_size)

    line_height = bar_font_size + 8
    text_block_h = len(lines) * line_height + 20 + attr_font_size
    # Center text block vertically within the bottom half
    text_start_y = half_h + (half_h - text_block_h) // 2

    y = text_start_y
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=bar_font)
        tw = bbox[2] - bbox[0]
        x = (target_w - tw) // 2
        draw.text((x + 2, y + 2), line, font=bar_font, fill=(0, 0, 0))
        draw.text((x, y), line, font=bar_font, fill=(255, 255, 255))
        y += line_height

    # Attribution — right-aligned
    y += 10
    attr_text = "— VAWN"
    bbox = draw.textbbox((0, 0), attr_text, font=attr_font)
    tw = bbox[2] - bbox[0]
    x = target_w - margin - tw
    draw.text((x, y), attr_text, font=attr_font, fill=(201, 168, 76))

    return bg


def _render_bold(img, bar_text, target_w, target_h):
    """Template 4: BOLD — full photo darkened to 40% opacity, very large centered text, no overlay box."""
    bg = img.copy().resize((target_w, target_h), Image.LANCZOS)
    # Darken to 40% opacity (keep 40% of pixel brightness)
    bg = bg.point(lambda p: int(p * 0.40))

    draw = ImageDraw.Draw(bg)
    margin = int(target_w * 0.08)
    max_text_w = target_w - (margin * 2)

    bar_font_size = max(48, target_h // 16)
    bar_font = get_font(bar_font_size)
    lines = wrap_text(f'"{bar_text}"', bar_font, max_text_w, draw)

    attr_font_size = max(24, target_h // 36)
    attr_font = get_font(attr_font_size)

    line_height = bar_font_size + 10
    text_block_h = len(lines) * line_height
    attr_gap = 24
    total_h = text_block_h + attr_gap + attr_font_size

    # Center everything vertically and horizontally
    start_y = (target_h - total_h) // 2

    y = start_y
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=bar_font)
        tw = bbox[2] - bbox[0]
        x = (target_w - tw) // 2
        # Drop shadow for readability
        draw.text((x + 3, y + 3), line, font=bar_font, fill=(0, 0, 0))
        draw.text((x, y), line, font=bar_font, fill=(255, 255, 255))
        y += line_height

    # Attribution — centered below
    y += attr_gap
    attr_text = "— VAWN"
    bbox = draw.textbbox((0, 0), attr_text, font=attr_font)
    tw = bbox[2] - bbox[0]
    draw.text(((target_w - tw) // 2, y), attr_text, font=attr_font, fill=(201, 168, 76))

    return bg


def render_lyric_card(img_path, bar_text, track_name, target_w, target_h, template=1):
    """Render a lyric card using one of 4 visual templates.

    Args:
        img_path: Path to the base Vawn photo.
        bar_text: The lyric quote to display.
        track_name: Kept for backward compatibility — never displayed.
        target_w: Output width (1080).
        target_h: Output height (1920).
        template: Visual template 1-4 (CLASSIC, MINIMAL, SPLIT, BOLD).

    Returns:
        PIL Image of the rendered card.
    """
    img = Image.open(img_path).convert("RGB")

    if template == 2:
        return _render_minimal(bar_text, target_w, target_h)
    elif template == 3:
        return _render_split(img, bar_text, target_w, target_h)
    elif template == 4:
        return _render_bold(img, bar_text, target_w, target_h)
    else:
        return _render_classic(img, bar_text, target_w, target_h)


def main():
    print("\n=== Lyric Card Agent ===\n")

    calendar = load_json(CONTENT_CALENDAR)
    today = today_str()

    entry = None
    for day in calendar.get("calendar", []):
        if day.get("date") == today:
            entry = day
            break

    if not entry:
        print("[WARN] No calendar entry for today — using fallback")
        bar = "I don't carry anger — I carry receipts"
        track = "GOT THAT IN WRITING"
        keywords = ["studio", "urban"]
    else:
        slot = entry.get("slots", {}).get("morning", {})
        bar = slot.get("anchor_line", "Still moving — that's the only code")
        track = slot.get("anchor_track", "STILL MOVING")
        keywords = slot.get("image_keyword", [])

    img_path = pick_base_image(keywords)
    print(f"[OK] Base image: {img_path.name}")
    print(f"[OK] Bar: {bar}")

    template = random.randint(1, 4)
    print(f"[OK] Template: {template}")

    filename = f"lyric-card-{today}.png"

    EXPORTS_DIR.mkdir(exist_ok=True)
    card = render_lyric_card(img_path, bar, "", TARGET_W, TARGET_H, template=template)
    out_path = EXPORTS_DIR / filename
    card.save(out_path, quality=95)

    log_run("LyricCardAgent", "ok", f"exported: {filename}")
    print(f"\n[OK] Lyric card exported as '{filename}' to Social_Media_Exports")


if __name__ == "__main__":
    main()
