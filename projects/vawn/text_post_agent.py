"""
text_post_agent.py — Text-only posts for X, Threads, Bluesky.
Short bars, observations, and one-liners in Vawn's voice.
Runs 2x daily between image post slots (10:30am, 3:30pm).
"""

import argparse
import json
import random
import sys
sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from datetime import date, datetime
from pathlib import Path
import requests

from vawn_config import (
    VAWN_DIR, VAWN_PROFILE, RESEARCH_DIR, load_json, save_json,
    get_anthropic_client, log_run, today_str,
    CONTENT_CALENDAR,
)

CREDS_FILE = VAWN_DIR / "credentials.json"
CONFIG_FILE = VAWN_DIR / "config.json"
TEXT_LOG = VAWN_DIR / "research" / "text_post_log.json"
BASE_URL = "https://apulustudio.onrender.com/api"
BLUESKY_MAX_CHARS = 250

PLATFORMS = ["x", "threads", "bluesky"]


def refresh_token():
    creds = load_json(CREDS_FILE)
    r = requests.post(f"{BASE_URL}/auth/refresh", json={"refresh_token": creds["refresh_token"]})
    r.raise_for_status()
    data = r.json()
    creds["access_token"] = data["access_token"]
    creds["refresh_token"] = data["refresh_token"]
    save_json(CREDS_FILE, creds)
    return data["access_token"]


def get_week_momentum():
    """Get weekday-specific morning energy context."""
    weekday = datetime.now().weekday()  # 0=Monday, 6=Sunday
    momentum_map = {
        0: "Monday morning intention — week-opening quiet authority",      # Monday
        1: "Tuesday clarity — mid-beginning focus, coffee still hot",     # Tuesday
        2: "Wednesday perspective — mid-week father wisdom",              # Wednesday
        3: "Thursday momentum — building toward completion energy",       # Thursday
        4: "Friday completion — week accomplished, weekend earned",       # Friday
        5: "Saturday morning freedom — different energy entirely",        # Saturday
        6: "Sunday reflection — quiet preparation for new week"           # Sunday
    }
    return momentum_map.get(weekday, "New day morning energy")


def load_daily_context(slot_name="morning"):
    """Load today's pillar, anchor line, and trending angles for specified slot."""
    cal = load_json(CONTENT_CALENDAR)
    today = today_str()
    context = None
    for day in cal.get("calendar", []):
        if day.get("date") == today:
            # APU-71: Support evening slot from content calendar
            slot = day.get("slots", {}).get(slot_name, {})
            context = {
                "pillar": day.get("pillar", ""),
                "anchor_line": slot.get("anchor_line", ""),
                "anchor_track": slot.get("anchor_track", ""),
                "trending_angles": [],
            }
            break

    # Load trending angles from daily brief
    brief_path = RESEARCH_DIR / "daily_brief.json"
    if context and brief_path.exists():
        try:
            brief = load_json(brief_path)
            trends = brief.get("trends", [])
            context["trending_angles"] = [
                t.get("angle", "")[:150] for t in trends[:2]
            ]
        except Exception:
            pass

    # Load ideation top pick (for afternoon X thread — highest reach slot)
    ideation_path = Path(r"C:\Users\rdyal\Apulu Universe\research\vawn\ideation\ideation_results.json")
    if context and ideation_path.exists():
        try:
            ideation = load_json(ideation_path)
            ide = ideation.get("ideation", {})
            picks = ide.get("priority_picks", [])
            ideas = ide.get("content_ideas", [])
            if picks:
                context["ideation_pick"] = picks[0].get("title", "")
                context["ideation_reason"] = picks[0].get("reason", "")
            elif ideas:
                context["ideation_pick"] = ideas[0].get("title", "")
                context["ideation_reason"] = ideas[0].get("angle", "")
        except Exception:
            pass

    return context


def generate_text_posts(context=None):
    """Generate short text-only posts for X, Threads, Bluesky."""
    client = get_anthropic_client()

    context_block = ""
    if context:
        context_block = f"""
TODAY'S CONTENT PILLAR: {context.get('pillar', '')}
ANCHOR LINE: "{context.get('anchor_line', '')}"
Use this theme as morning inspiration — channel it through 10:30am father/artist energy. Don't quote directly."""

        trending = context.get("trending_angles", [])
        if trending:
            trends_str = "\n".join([f"  - {t}" for t in trending])
            context_block += f"""

TRENDING IN HIP-HOP RIGHT NOW (morning perspective on these waves):
{trends_str}
Channel these through morning clarity — how would someone building an album with twin 1-year-olds see these trends?"""

        ideation_pick = context.get("ideation_pick", "")
        if ideation_pick:
            context_block += f"""

IDEATION ENGINE TOP PICK: "{ideation_pick}"
Reason: {context.get('ideation_reason', '')}
Use this angle as the PRIMARY direction for the X thread (post #3). The ideation engine analyzed cross-platform discovery data and ranked this as the highest-potential content idea today. Don't reference it literally — channel the energy and angle into a thread that feels like your own thought."""

    # APU-90: Morning and evening-specific voice and energy context
    time_energy = ""
    current_hour = datetime.now().hour

    if current_hour < 14:  # Morning slot (before 2pm)
        weekday_energy = get_week_momentum()
        time_energy = f"""
TIME CONTEXT: Morning energy (10:30am) — before the world fully wakes up energy.
ENERGY SHIFT: Coffee table morning clarity, twin girls still sleeping, quiet house authority.
VOICE TONE: Anti-hype quiet authority, father/artist morning routine authenticity.
SETTING: Early light observations, 20-minute windows between life happening.

MORNING VOICE (10:30am) - "Before the world fully wakes up":
- Week momentum: {weekday_energy}
- Father/artist morning routine authenticity — dependable presence over flashy performance
- Coffee still hot, checking on the twins — quiet authority over loud proclamations
- 7am energy captured at 10:30am posting — fresh perspective before chaos starts
- Brooklyn memories over Atlanta beats — geographic dual consciousness
- Building an album with twin 1-year-olds — real life doesn't pause for creativity
- Morning intention over day processing wisdom
- "YOU WERE THERE" energy — showing up when nobody's watching
- Anti-hype positioning: quiet confidence over viral moments
- Psychedelic boom bap mindset: making sense of multiple realities"""

    elif current_hour >= 18:  # Evening slot (6pm+)
        time_energy = """
TIME CONTEXT: Evening energy (6-8pm) — day completion, studio preparation mode.
ENERGY SHIFT: From coffee table morning clarity to studio creative authority.
VOICE TONE: Contemplative depth, after-hours creative preparation, day processing wisdom.
SETTING: Studio lights on, creative mode activation, real work begins energy.

EVENING VOICE (6-8pm):
- Studio presence over coffee table intimacy
- Creative preparation over daily motivation
- Day processing over new day intention
- "Real work begins" over "fresh start" energy
- Contemplative authority over morning urgency
- Evening creative transition over morning routine authenticity"""

    prompt = f"""You are Vawn — a Brooklyn-raised, Atlanta-based hip-hop artist. {VAWN_PROFILE}
{time_energy}

Write 3 text-only social media posts. These are NOT captions for images — they stand alone as pure text. Think: a bar that makes someone screenshot it, an observation that starts a debate, or a one-liner that haunts.
{context_block}

MORNING CONTENT RULES:
- Sound like a real person thinking out loud at 10:30am, not a brand posting motivational content
- Capture "before the world fully wakes up" energy — quiet authority over loud proclamations
- Father/artist morning authenticity: coffee table realness, not studio late-night introspection
- NO motivational cliches: "grind don't stop", "stay focused", "level up", "built different"
- NO generic rapper talk or hype machine language
- NEVER say "stream", "listen", "press play", "available now", or reference streaming platforms. Music is NOT released yet.
- NEVER mention track names like "LYR02", "TRACK 7" — these are internal IDs.
- Have a POINT OF VIEW — say something specific that comes from morning clarity
- Morning observation over afternoon reflection — fresh perspective meets earned confidence
- Anti-hype positioning: dependable presence over flashy performance
- Short. Let it breathe. Morning energy is quiet, not frantic.
- NO markdown, no emojis as decoration, no formatting symbols
- Plain text only, straight quotes only

Write exactly 3 posts in this format:

X: [Morning bar or observation, max 200 chars, no hashtags. Think: commuter-friendly content, retweet-worthy morning wisdom that captures "before the world wakes up" energy]

THREADS: [1-3 raw sentences capturing morning father/artist authenticity. End with a genuine question that feels like early morning coffee table conversation — something you'd ask while checking on the twins. Examples: "what's something you had to unlearn to become dependable?", "what's a responsibility you didn't expect to change how you see everything?", "who taught you what showing up actually costs?" The question should feel like 7am clarity, not 2am overthinking. No hashtags.]

BLUESKY: [Mirror X morning energy but more intimate — authentic artist-to-artist morning thoughts, early adopter community vibe, less polished more real, max 250 chars, no hashtags]"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    import re
    raw = message.content[0].text
    posts = {}
    for key in PLATFORMS:
        m = re.search(
            rf'(?m)^{re.escape(key.upper())}:\s*(.*?)(?=^(?:X|THREADS|BLUESKY):|\Z)',
            raw, re.DOTALL
        )
        if m:
            text = m.group(1).strip()
            text = re.sub(r'\*+|__+|-{2,}', '', text).strip()
            text = text.replace('\u201c', '"').replace('\u201d', '"')
            text = text.replace('\u2018', "'").replace('\u2019', "'")
            posts[key] = text

    # Enforce Bluesky char limit
    if "bluesky" in posts and len(posts["bluesky"]) > BLUESKY_MAX_CHARS:
        posts["bluesky"] = posts["bluesky"][:BLUESKY_MAX_CHARS].rsplit(" ", 1)[0]

    return posts


THREADS_TOPIC_TAGS = [
    "#undergroundhiphop", "#bars", "#lyricism", "#studiolife",
    "#realrap", "#indierap", "#wordplay", "#rappers",
    "#fatherhood", "#blackmen", "#hiphopculture",
]

# ── Feature: X Long-Form Threads (afternoon slot) ─────────────────────────────

def generate_x_thread(context=None):
    """Generate a 3-4 tweet thread for X. Used in the afternoon slot for higher reach."""
    client = get_anthropic_client()

    context_block = ""
    if context:
        context_block = f"""
TODAY'S CONTENT PILLAR: {context.get('pillar', '')}
ANCHOR LINE: "{context.get('anchor_line', '')}"
Use this theme as inspiration — don't quote it directly. Don't mention track names."""

        trending = context.get("trending_angles", [])
        if trending:
            trends_str = "\n".join([f"  - {t}" for t in trending])
            context_block += f"""

TRENDING IN HIP-HOP RIGHT NOW (ride these waves):
{trends_str}
Channel these trends into the thread — don't describe them, embody them."""

    prompt = f"""You are Vawn — a Brooklyn-raised, Atlanta-based hip-hop artist. {VAWN_PROFILE}

Write a 3-4 tweet thread for X (Twitter). This is a rapper's late-night thought process — stream of consciousness that builds to a revelation.
{context_block}

THREAD STRUCTURE:
- Tweet 1 (HOOK): The provocative opening that stops the scroll. A question, a contradiction, a bar that demands attention.
- Tweet 2 (DEPTH): The story or observation. The thing you noticed that nobody talks about. Give it room to breathe.
- Tweet 3 (PUNCHLINE): The revelation or the line that makes people screenshot. This is the payoff.
- Tweet 4 (CLOSER — optional, only if it adds something): Tie it back to the bigger picture without being preachy. Skip this tweet entirely if 3 tweets land harder.

RULES:
- Each tweet MUST be under 280 characters
- Do NOT number them ("1/4", "2/4") — they should connect by theme, not numbering
- Sound like a real person thinking, not a content strategy
- NEVER say "stream", "listen", "press play", "available now", or reference streaming platforms
- NEVER mention track names like "LYR02", "TRACK 7" — these are internal IDs
- NO motivational cliches: "grind don't stop", "stay focused", "level up", "built different"
- NO generic rapper talk
- NO markdown, no emojis as decoration, no formatting symbols
- Plain text only, straight quotes only
- Have a point of view. Say something that could start an argument.

Return EXACTLY this format (3 or 4 tweets):
TWEET_1: [hook tweet]
TWEET_2: [depth tweet]
TWEET_3: [punchline tweet]
TWEET_4: [closer tweet — or leave this line out entirely if 3 is enough]"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}]
    )

    import re
    raw = message.content[0].text
    tweets = []
    for i in range(1, 5):
        m = re.search(
            rf'(?m)^TWEET_{i}:\s*(.*?)(?=^TWEET_\d:|\Z)',
            raw, re.DOTALL
        )
        if m:
            text = m.group(1).strip()
            text = re.sub(r'\*+|__+|-{2,}', '', text).strip()
            text = text.replace('\u201c', '"').replace('\u201d', '"')
            text = text.replace('\u2018', "'").replace('\u2019', "'")
            # Enforce 280-char limit
            if len(text) > 280:
                text = text[:280].rsplit(" ", 1)[0]
            if text:
                tweets.append(text)

    return tweets


def post_x_thread(tweets, access_token):
    """Post a thread on X — each tweet replies to the previous one.
    Falls back to posting as separate tweets 30s apart if reply threading isn't supported."""
    import time
    headers = {"Authorization": f"Bearer {access_token}"}
    posted_ids = []

    for i, tweet_text in enumerate(tweets):
        payload = {
            "content": tweet_text,
            "platforms": ["x"],
            "media_urls": [],
            "ai_generated": True,
        }
        # Try to thread: reply to previous tweet if API supports it
        if posted_ids:
            payload["in_reply_to"] = posted_ids[-1]

        try:
            r = requests.post(f"{BASE_URL}/posts", headers=headers, json=payload)
            r.raise_for_status()
            post_id = r.json()["id"]

            pub = requests.post(f"{BASE_URL}/posts/{post_id}/publish", headers=headers)
            pub.raise_for_status()

            posted_ids.append(post_id)
            print(f"[OK] X thread tweet {i+1}/{len(tweets)} posted")

            # Wait between tweets to avoid rate limits and let threading settle
            if i < len(tweets) - 1:
                time.sleep(30)

        except Exception as e:
            print(f"[FAIL] X thread tweet {i+1} failed: {e}")
            return False

    print(f"[OK] X thread complete — {len(posted_ids)} tweets posted")
    return True


def post_text(platform, text, access_token):
    """Post text-only (no image) to a platform."""
    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.post(f"{BASE_URL}/posts", headers=headers, json={
        "content": text,
        "platforms": [platform],
        "media_urls": [],
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
                    err = result.get("error", "unknown error")
                    print(f"[FAIL] {platform} publish failed: {err}")
                    return False
    except Exception:
        pass
    print(f"[OK] {platform} text posted")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Test mode — post but don't log")
    args = parser.parse_args()

    today = today_str()
    now_hour = datetime.now().hour

    # APU-71: Evening slot support for 6-8pm content enhancement
    if now_hour < 12:
        slot = "morning"    # 10:30am slot
    elif 12 <= now_hour < 18:
        slot = "afternoon"  # 3:30pm slot
    else:
        slot = "evening"    # 6-8pm slot (NEW for APU-71)

    print(f"\n--- Vawn TEXT POST ({slot}) -- {today} ---\n")

    # File-based lock to prevent race condition (Windows + Paperclip both firing)
    lock_file = VAWN_DIR / "research" / f".text_post_lock_{today}_{slot}"
    if not args.test:
        if lock_file.exists():
            print(f"[SKIP] Lock file exists -- another instance is running or already ran: {lock_file.name}")
            return
        lock_file.write_text(datetime.now().isoformat())

    # Check if already posted this slot
    log = load_json(TEXT_LOG)
    slot_key = f"{today}_{slot}"
    if not args.test and log.get(slot_key):
        print(f"[SKIP] Text already posted for {slot_key}")
        return

    # Load context + generate
    context = load_daily_context(slot)
    if context:
        print(f"[OK] Pillar: {context['pillar']}")

    posts = generate_text_posts(context)
    print(f"[OK] Generated {len(posts)} text posts")

    for p, text in posts.items():
        print(f"  {p.upper()}: {text[:80]}{'...' if len(text) > 80 else ''}")

    # Afternoon slot: generate X thread instead of single tweet
    x_thread_tweets = None
    if slot == "afternoon":
        try:
            x_thread_tweets = generate_x_thread(context)
            if x_thread_tweets:
                print(f"[OK] Generated X thread — {len(x_thread_tweets)} tweets")
                for i, t in enumerate(x_thread_tweets):
                    print(f"  TWEET {i+1}: {t[:80]}{'...' if len(t) > 80 else ''}")
            else:
                print("[WARN] X thread generation returned empty — falling back to single post")
        except Exception as e:
            print(f"[WARN] X thread generation failed, falling back to single post: {e}")

    # Post
    access_token = refresh_token()
    results = {}
    for platform in PLATFORMS:
        if platform not in posts:
            continue
        try:
            # Afternoon X: post as thread instead of single tweet
            if platform == "x" and x_thread_tweets:
                ok = post_x_thread(x_thread_tweets, access_token)
                results[platform] = ok
                continue

            post_content = posts[platform]
            if platform == "threads":
                tag = random.choice(THREADS_TOPIC_TAGS)
                post_content = f"{post_content}\n\n{tag}"
                print(f"[OK] Threads topic tag: {tag}")
            ok = post_text(platform, post_content, access_token)
            results[platform] = ok
        except Exception as e:
            print(f"[FAIL] {platform}: {e}")
            results[platform] = False

    # Log
    if not args.test:
        log[slot_key] = {
            "platforms": results,
            "time": datetime.now().isoformat(),
        }
        save_json(TEXT_LOG, log)

    succeeded = [p for p, ok in results.items() if ok]
    failed = [p for p, ok in results.items() if not ok]
    log_run("TextPostAgent", "ok" if succeeded else "error",
            f"Posted: {succeeded}, Failed: {failed}")
    print(f"\n--- DONE — Posted: {succeeded} | Failed: {failed} ---\n")


if __name__ == "__main__":
    main()
