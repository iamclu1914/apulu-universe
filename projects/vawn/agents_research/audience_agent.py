"""
audience_agent.py — Researches comparable artists to find what content is driving growth.
"""

import json
import re
import sys
sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import (
    get_anthropic_client, load_json, save_json, DAILY_BRIEF,
    COMPARABLE_ARTISTS, VAWN_PROFILE, log_run, today_str,
)
from agents_research.trend_agent import extract_json


def run():
    client = get_anthropic_client()
    artists_str = ", ".join(COMPARABLE_ARTISTS)

    prompt = f"""You are a social media analyst researching comparable hip-hop artists.

ARTIST BEING RESEARCHED FOR:
{VAWN_PROFILE}

COMPARABLE ARTISTS TO RESEARCH: {artists_str}

TASK: Search the web for recent social media activity from these comparable artists. Focus on:
- What recent posts or content got high engagement
- What format they used (video, carousel, text post, behind-the-scenes, etc.)
- What topics or hooks drove the engagement
- Content gaps — things Vawn could do that these artists aren't doing

Return EXACTLY this JSON structure — no markdown fencing, raw JSON only:
{{
  "audience_intel": [
    {{
      "artist": "artist name",
      "observation": "what they did / what worked",
      "format": "reel|carousel|text|photo|video",
      "takeaway": "what Vawn can learn or do differently"
    }}
  ]
}}

Return 4-6 observations. Be specific about what actually happened, not generic advice."""

    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}],
        messages=[{"role": "user", "content": prompt}],
    )

    text = ""
    for block in resp.content:
        if hasattr(block, "text"):
            text = block.text  # keep overwriting to get the last text block

    try:
        data = extract_json(text)
    except (json.JSONDecodeError, ValueError):
        log_run("AudienceAgent", "error", f"Failed to parse JSON: {text[:300]}")
        data = {"audience_intel": []}

    brief = load_json(DAILY_BRIEF)
    brief["audience_intel"] = data.get("audience_intel", [])
    save_json(DAILY_BRIEF, brief)

    log_run("AudienceAgent", "ok", f"{len(data.get('audience_intel', []))} observations")
    print(f"[AudienceAgent] {len(data.get('audience_intel', []))} observations written")
    return data


if __name__ == "__main__":
    run()
