"""
outline_engine.py -- Generates content outlines with section breakdowns.
Each section includes talking points, visual aids, and source references.

Usage:
    python outline_engine.py "content idea"
    python outline_engine.py --from-ideation         # uses top pick
    python outline_engine.py "topic" --format short   # 30-60s short form
    python outline_engine.py "topic" --format long    # 10-20min long form
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


def generate_outline(client, config, topic, content_format="long"):
    """Generate a content outline."""
    profile = config["profile"]
    platforms = ", ".join(config["platforms"])

    format_guide = {
        "short": "30-60 second short form (Reel/TikTok/Short). 3-4 sections max. Punchy, one idea.",
        "medium": "2-5 minute medium form. 4-6 sections. Focused deep dive on one concept.",
        "long": "10-20 minute long form (YouTube). 6-10 sections. Comprehensive breakdown.",
    }
    format_desc = format_guide.get(content_format, format_guide["long"])

    prompt = f"""You are a content outline specialist.

ARTIST/CREATOR PROFILE:
{profile}

PLATFORMS: {platforms}
CONTENT TOPIC: {topic}
FORMAT: {format_desc}

Generate a detailed content outline. For each section:
1. section_title: Clear section name
2. duration: Estimated time (e.g., "30s", "2min")
3. talking_points: 3-5 bullet points of what to cover
4. visual_aid: What should be on screen (diagram, screenshot, b-roll, etc.)
5. source_material: Any references or examples to show
6. transition: How to move to next section

Also include:
- target_length: Total estimated duration
- key_takeaway: The ONE thing the audience should remember
- call_to_action: What to ask the audience to do

Return ONLY valid JSON:
{{
  "target_length": "Xmin",
  "key_takeaway": "one sentence",
  "call_to_action": "what to ask",
  "sections": [
    {{
      "number": 1,
      "section_title": "title",
      "duration": "Xs",
      "talking_points": ["point1", "point2"],
      "visual_aid": "what to show",
      "source_material": "references",
      "transition": "how to move to next"
    }}
  ]
}}"""

    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
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
    return {"sections": [], "raw": text}


def format_outline_obsidian(topic, outline_data, content_format, project="vawn"):
    """Format outline as Obsidian note."""
    today = datetime.now().strftime("%Y-%m-%d")
    sections = outline_data.get("sections", [])
    safe_topic = topic[:50].replace("/", "-").replace("\\", "-")

    lines = [
        "---",
        f"title: Outline -- {safe_topic}",
        f"date: {today}",
        "tags:",
        "  - scripting/outline",
        f"  - project/{project}",
        f"  - format/{content_format}",
        "---",
        "",
        f"# Outline -- {safe_topic}",
        "",
        f"> [!info] {content_format.upper()} format | Target: {outline_data.get('target_length', '?')} | {len(sections)} sections",
        "",
        f"**Key Takeaway:** {outline_data.get('key_takeaway', '')}",
        f"**CTA:** {outline_data.get('call_to_action', '')}",
        "",
    ]

    for section in sections:
        num = section.get("number", "?")
        title = section.get("section_title", "")
        duration = section.get("duration", "?")

        lines.append(f"## Section {num} -- {title} ({duration})")
        lines.append("")

        # Talking points
        lines.append("**Talking Points:**")
        for point in section.get("talking_points", []):
            lines.append(f"- {point}")
        lines.append("")

        # Visual aid
        if section.get("visual_aid"):
            lines.append(f"> [!example] Visual Aid")
            lines.append(f"> {section['visual_aid']}")
            lines.append("")

        # Source material
        if section.get("source_material"):
            lines.append(f"**Source:** {section['source_material']}")
            lines.append("")

        # Transition
        if section.get("transition"):
            lines.append(f"*Transition: {section['transition']}*")
            lines.append("")

    lines.append("## Related")
    lines.append(f"- [[Hooks -- {safe_topic}]]")
    lines.append(f"- [[Titles -- {safe_topic}]]")
    lines.append(f"- [[Content Ideation -- {today}]]")
    lines.append("")

    return "\n".join(lines)


def run(topic=None, project_name="vawn", from_ideation=False, content_format="long"):
    """Run outline generation."""
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
        print("[Outline] No topic provided.")
        return None

    print(f"\n[Outline] Generating {content_format} outline for: {topic}")
    outline_data = generate_outline(client, config, topic, content_format)

    # Save JSON
    output = {
        "project": project_name,
        "generated": now_iso(),
        "topic": topic,
        "format": content_format,
        "outline": outline_data,
    }
    save_json(output_dir / "outline_results.json", output)

    # Save Obsidian note
    content = format_outline_obsidian(topic, outline_data, content_format, project_name)
    safe_topic = topic[:50].replace("/", "-").replace("\\", "-")
    md_path = output_dir / f"Outline -- {safe_topic}.md"
    md_path.write_text(content, encoding="utf-8")
    print(f"[Outline] Wrote {md_path.name}")

    sections = outline_data.get("sections", [])
    print(f"[Outline] {len(sections)} sections, target: {outline_data.get('target_length', '?')}")
    for s in sections:
        print(f"  {s.get('number')}. {s.get('section_title', '?')} ({s.get('duration', '?')})")

    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Content outline generator")
    parser.add_argument("topic", nargs="?", help="Content topic")
    parser.add_argument("--project", default="vawn")
    parser.add_argument("--from-ideation", action="store_true")
    parser.add_argument("--format", default="long", choices=["short", "medium", "long"])
    args = parser.parse_args()

    run(args.topic, args.project, args.from_ideation, args.format)
