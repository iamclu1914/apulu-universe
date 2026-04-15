"""
scan_hashtags.py — Fetches trending hashtags for each platform and writes them to
Vawn/Social_Media_Exports/Trending_Hashtags/[Platform]/hashtags.txt
Runs at 6:30am before the 7:58am morning post.
"""

import json
from datetime import date
from pathlib import Path
import anthropic

VAWN_DIR = Path(r"C:\Users\rdyal\Vawn")
HASHTAGS_DIR = VAWN_DIR / "Social_Media_Exports" / "Trending_Hashtags"

PLATFORMS = {
    "Instagram": {"count": 15, "note": "mix of high-volume, mid-range, and niche hip-hop/music hashtags"},
    "TikTok":    {"count": 5,  "note": "3-5 trending hashtags, prioritize viral music/hip-hop tags"},
    "Threads":   {"count": 2,  "note": "1-2 hashtags max, conversational music/culture tags"},
    "X":         {"count": 2,  "note": "1-2 hashtags embedded naturally, trending hip-hop/music tags"},
    "Bluesky":   {"count": 3,  "note": "1-3 hashtags, music/hip-hop community tags"},
}

def fetch_hashtags():
    config = json.loads((VAWN_DIR / "config.json").read_text())
    client = anthropic.Anthropic(api_key=config["anthropic_api_key"])

    today = date.today().strftime("%B %d, %Y")

    prompt = f"""Today is {today}. You are a social media strategist for Vawn, a Brooklyn/Atlanta hip-hop artist.

Generate currently trending hashtags for each platform for a hip-hop music artist posting today.
Focus on: hip-hop, music culture, artist grind, studio life, Brooklyn/Atlanta scenes, Black excellence.
Avoid: overly generic tags, banned tags, dead tags.

Return ONLY this exact format — one hashtag per line under each header:

INSTAGRAM:
#tag1
#tag2
(up to 15 tags — mix high-volume like #hiphop, mid-range like #brooklynrap, niche like #independentartist)

TIKTOK:
#tag1
#tag2
(3-5 tags — trending viral music/hip-hop tags)

THREADS:
#tag1
#tag2
(1-2 tags only)

X:
#tag1
#tag2
(1-2 tags only)

BLUESKY:
#tag1
#tag2
(1-3 tags)"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()
    print(f"[scan] Raw response:\n{raw}\n")

    # Parse each platform block
    import re
    platform_names = list(PLATFORMS.keys())
    marker_pattern = "|".join(re.escape(p.upper()) for p in platform_names)

    for platform in platform_names:
        m = re.search(
            rf'(?m)^{re.escape(platform.upper())}:\s*(.*?)(?=^(?:{marker_pattern}):|\Z)',
            raw,
            re.DOTALL
        )
        if m:
            tags = [line.strip() for line in m.group(1).strip().splitlines() if line.strip().startswith("#")]
            out_file = HASHTAGS_DIR / platform / "hashtags.txt"
            out_file.write_text("\n".join(tags), encoding="utf-8")
            print(f"[OK] {platform}: {len(tags)} hashtags saved -> {out_file}")
        else:
            print(f"[WARN] {platform}: no hashtags parsed")

if __name__ == "__main__":
    print(f"[scan_hashtags] Running for {date.today()}")
    fetch_hashtags()
    print("[scan_hashtags] Done.")
