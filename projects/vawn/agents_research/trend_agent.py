"""
trend_agent.py — Searches for trending content formats in Vawn's genre space.
Uses Claude web search tool for real-time trend intelligence.
"""

import json
import re
import sys
sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import get_anthropic_client, load_json, save_json, DAILY_BRIEF, VAWN_PROFILE, log_run, today_str


def extract_json(text):
    """Robustly extract JSON from Claude response that may have preamble/postamble text."""
    # Try markdown fence first
    m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if m:
        return json.loads(m.group(1))
    # Find outermost { ... } pair
    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object found")
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start:i + 1])
    raise ValueError("Unbalanced JSON braces")


def run():
    client = get_anthropic_client()

    prompt = f"""You are a social media growth strategist researching for a hip-hop artist.

ARTIST PROFILE:
{VAWN_PROFILE}

TASK: Search the web for what content formats and strategies are currently growing audiences for independent hip-hop artists on Instagram, TikTok, X/Twitter, Threads, and Bluesky in 2026.

Focus on:
- What types of posts (reels, carousels, text, photos) are getting the most engagement
- What hooks and formats are working for rap/hip-hop artists specifically
- ATL trap and lyrical rap scenes specifically
- Indie artist growth tactics (not major label strategies)

Return EXACTLY this JSON structure — no markdown fencing, raw JSON only:
{{
  "trends": [
    {{
      "angle": "specific content format or tactic description",
      "format": "reel|carousel|text|photo|video",
      "platforms": ["platform1", "platform2"],
      "hook": "why this works / example hook",
      "evidence": "source or reasoning"
    }}
  ]
}}

Return 5-7 trends. Be specific and actionable, not generic."""

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
        log_run("TrendAgent", "error", f"Failed to parse JSON: {text[:300]}")
        data = {"trends": []}

    brief = load_json(DAILY_BRIEF)
    brief["date"] = today_str()
    brief["trends"] = data.get("trends", [])
    save_json(DAILY_BRIEF, brief)

    log_run("TrendAgent", "ok", f"{len(data.get('trends', []))} trends found")
    print(f"[TrendAgent] {len(data.get('trends', []))} trends written to daily_brief.json")
    return data


if __name__ == "__main__":
    run()
