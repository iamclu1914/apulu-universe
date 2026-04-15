"""
titles_engine.py -- Generates tiered title options with thumbnail text.
Analyzes past performance patterns to inform title strategy.

Usage:
    python titles_engine.py "content idea"
    python titles_engine.py --from-ideation
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline_config import (
    load_project_config, get_anthropic_client, get_output_dir,
    save_json, load_json, now_iso,
)


def generate_titles(client, config, topic):
    """Generate tiered title options with thumbnail text."""
    profile = config["profile"]
    platforms = ", ".join(config["platforms"])

    prompt = f"""You are a social media title/caption optimization specialist.

ARTIST/CREATOR PROFILE:
{profile}

PLATFORMS: {platforms}
CONTENT TOPIC: {topic}

Generate title options in three tiers:

**Tier 1 -- Proven Patterns** (3 titles): Safe, high-probability titles based on formats that consistently work (how-to, numbered lists, transformations, reveals).

**Tier 2 -- Calculated Risks** (3 titles): More provocative, pattern-breaking titles. These could hit big or miss -- worth A/B testing.

**Tier 3 -- Platform-Specific** (5 titles): Optimized per platform:
- X: punchy, under 200 chars, hashtag-friendly
- Instagram: hook-first, emoji-optional, 1-2 lines
- TikTok: pattern-interrupt, 1 line max
- Threads: conversational, question-ending
- Bluesky: same energy as X, under 250 chars

For each title, provide:
1. title: The actual title text
2. tier: 1, 2, or 3
3. platform: "all" for tier 1/2, specific platform for tier 3
4. rationale: Why this works (1 sentence)
5. thumbnail_text: Bold text for thumbnail/cover (4-6 words max)

Return ONLY valid JSON:
{{
  "titles": [
    {{
      "title": "title text",
      "tier": 1,
      "platform": "all",
      "rationale": "why this works",
      "thumbnail_text": "BOLD THUMBNAIL TEXT"
    }}
  ]
}}"""

    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    text = resp.content[0].text
    try:
        start = text.find("{")
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(text[start:i + 1])
    except (json.JSONDecodeError, ValueError):
        pass
    return {"titles": [], "raw": text}


def format_titles_obsidian(topic, titles_data, project="vawn"):
    """Format titles as Obsidian note."""
    today = datetime.now().strftime("%Y-%m-%d")
    titles = titles_data.get("titles", [])
    safe_topic = topic[:50].replace("/", "-").replace("\\", "-")

    lines = [
        "---",
        f"title: Titles -- {safe_topic}",
        f"date: {today}",
        "tags:",
        "  - scripting/titles",
        f"  - project/{project}",
        "---",
        "",
        f"# Titles -- {safe_topic}",
        "",
        f"> [!info] {len(titles)} title options across 3 tiers",
        "",
    ]

    for tier in [1, 2, 3]:
        tier_titles = [t for t in titles if t.get("tier") == tier]
        if not tier_titles:
            continue

        tier_names = {1: "Proven Patterns", 2: "Calculated Risks", 3: "Platform-Specific"}
        tier_callout = {1: "tip", 2: "warning", 3: "example"}

        lines.append(f"## Tier {tier} -- {tier_names.get(tier, '?')}")
        lines.append("")

        for t in tier_titles:
            platform = t.get("platform", "all")
            platform_tag = f" ({platform})" if platform != "all" else ""

            lines.append(f"### {t.get('title', '')}{platform_tag}")
            lines.append("")
            lines.append(f"> [!{tier_callout.get(tier, 'note')}] Rationale")
            lines.append(f"> {t.get('rationale', '')}")
            lines.append("")
            lines.append(f"**Thumbnail:** =={t.get('thumbnail_text', '')}==")
            lines.append("")

    lines.append("## Related")
    lines.append(f"- [[Hooks -- {safe_topic}]]")
    lines.append(f"- [[Outline -- {safe_topic}]]")
    lines.append(f"- [[Content Ideation -- {today}]]")
    lines.append("")

    return "\n".join(lines)


def run(topic=None, project_name="vawn", from_ideation=False):
    """Run title generation."""
    config = load_project_config(project_name)
    client = get_anthropic_client(config)
    output_dir = get_output_dir(config, "scripting")

    if from_ideation and not topic:
        ideation_dir = get_output_dir(config, "ideation")
        ideation = load_json(ideation_dir / "ideation_results.json")
        picks = ideation.get("ideation", {}).get("priority_picks", [])
        ideas = ideation.get("ideation", {}).get("content_ideas", [])
        if picks:
            topic = picks[0].get("title", "")
        elif ideas:
            topic = ideas[0].get("title", "")

    if not topic:
        print("[Titles] No topic provided.")
        return None

    print(f"\n[Titles] Generating titles for: {topic}")
    titles_data = generate_titles(client, config, topic)

    # Save JSON
    output = {
        "project": project_name,
        "generated": now_iso(),
        "topic": topic,
        "titles": titles_data,
    }
    save_json(output_dir / "titles_results.json", output)

    # Save Obsidian note
    content = format_titles_obsidian(topic, titles_data, project_name)
    safe_topic = topic[:50].replace("/", "-").replace("\\", "-")
    md_path = output_dir / f"Titles -- {safe_topic}.md"
    md_path.write_text(content, encoding="utf-8")
    print(f"[Titles] Wrote {md_path.name}")

    titles = titles_data.get("titles", [])
    for t in titles:
        print(f"  T{t.get('tier')} [{t.get('platform', 'all')}]: {t.get('title', '')[:80]}")

    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Title generator")
    parser.add_argument("topic", nargs="?", help="Content topic")
    parser.add_argument("--project", default="vawn")
    parser.add_argument("--from-ideation", action="store_true")
    args = parser.parse_args()

    run(args.topic, args.project, args.from_ideation)
