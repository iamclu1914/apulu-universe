"""
content_agent.py — Generates a 7-day rolling content calendar with pillar rotation.
Reads daily_brief.json, writes content_calendar.json.
Splits into two API calls (days 1-3 + days 4-7) to avoid token truncation.
"""

import json
import sys
from datetime import date, timedelta
sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import (
    get_anthropic_client, load_json, save_json, DAILY_BRIEF,
    CONTENT_CALENDAR, PILLAR_SCHEDULE, VAWN_PROFILE, log_run,
)
from agents_research.trend_agent import extract_json

SYSTEM_PROMPT = (
    "You are a social media content strategist. Output ONLY raw JSON — "
    "no markdown fences, no commentary. Be concise: platform_angles values "
    "are ONE short sentence (under 20 words). anchor_line under 15 words. "
    "image_keyword entries are 1-2 words only."
)

PILLAR_GUIDE = (
    "Awareness=artist identity | Lyric=quotable bar | BTS=studio/process | "
    "Engagement=question/relatable | Conversion=stream/follow CTA | "
    "Audience=mirror comparable artists | Video=cinematic/motion"
)


def build_days(start_date, count):
    days = []
    for i in range(count):
        d = start_date + timedelta(days=i)
        pillar = PILLAR_SCHEDULE[d.weekday()]
        days.append({"date": str(d), "day": d.strftime("%A"), "pillar": pillar})
    return days


def generate_batch(client, days, context_str):
    days_str = json.dumps(days, indent=2)

    prompt = f"""{context_str}

SCHEDULE:
{days_str}

For each day, generate exactly 3 slots: morning, midday, evening.
Each slot: image_keyword (array of 2 tags), anchor_line (under 12 words), anchor_track (track name), platform_angles (instagram, tiktok, threads, x, bluesky — each 1 short sentence).

PILLAR GUIDE: {PILLAR_GUIDE}

Return ONLY a JSON array of day objects:
[{{"date":"YYYY-MM-DD","day":"DayName","pillar":"Pillar","slots":{{"morning":{{"image_keyword":["kw"],"anchor_line":"line","anchor_track":"TRACK","platform_angles":{{"instagram":"d","tiktok":"d","threads":"d","x":"d","bluesky":"d"}}}},"midday":{{...}},"evening":{{...}}}}}}]"""

    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    text = resp.content[0].text

    # extract_json finds { }, but we need [ ] for array
    # Try array parse first
    try:
        start = text.find("[")
        if start != -1:
            depth = 0
            for i in range(start, len(text)):
                if text[i] == "[":
                    depth += 1
                elif text[i] == "]":
                    depth -= 1
                    if depth == 0:
                        return json.loads(text[start:i + 1])
    except json.JSONDecodeError:
        pass

    # Fallback: try extract_json (wraps in object)
    try:
        data = extract_json(text)
        if isinstance(data, dict) and "calendar" in data:
            return data["calendar"]
        return [data] if isinstance(data, dict) else []
    except (json.JSONDecodeError, ValueError):
        raise ValueError(f"Could not parse batch: {text[:300]}")


def run():
    client = get_anthropic_client()
    brief = load_json(DAILY_BRIEF)

    trends = brief.get("trends", [])
    audience = brief.get("audience_intel", [])
    catalog = brief.get("catalog_lines", [])

    context_str = f"""ARTIST: {VAWN_PROFILE}

TRENDS: {json.dumps(trends[:4]) if trends else 'No trend data'}
AUDIENCE: {json.dumps(audience[:3]) if audience else 'No audience data'}
CATALOG: {json.dumps(catalog[:3]) if catalog else 'No catalog data'}"""

    today = date.today()
    batch1_days = build_days(today, 3)
    batch2_days = build_days(today + timedelta(days=3), 4)

    all_days = []

    # Batch 1: days 1-3
    print("[ContentAgent] Generating days 1-3...")
    try:
        result1 = generate_batch(client, batch1_days, context_str)
        all_days.extend(result1)
        print(f"[OK] Batch 1: {len(result1)} days")
    except ValueError as e:
        log_run("ContentAgent", "error", f"Batch 1 failed: {e}")
        print(f"[FAIL] Batch 1: {e}")

    # Batch 2: days 4-7
    print("[ContentAgent] Generating days 4-7...")
    try:
        result2 = generate_batch(client, batch2_days, context_str)
        all_days.extend(result2)
        print(f"[OK] Batch 2: {len(result2)} days")
    except ValueError as e:
        log_run("ContentAgent", "error", f"Batch 2 failed: {e}")
        print(f"[FAIL] Batch 2: {e}")

    if not all_days:
        log_run("ContentAgent", "error", "No days generated")
        print("[ContentAgent] ERROR: no calendar days generated")
        return None

    calendar = {
        "generated": f"{today.isoformat()}T06:10:00",
        "calendar": all_days,
    }
    save_json(CONTENT_CALENDAR, calendar)
    log_run("ContentAgent", "ok", f"{len(all_days)}-day calendar generated")
    print(f"[ContentAgent] {len(all_days)}-day calendar written to content_calendar.json")
    return calendar


if __name__ == "__main__":
    run()
