"""
hooks_engine.py -- Generates hook variations for a content idea.
Each hook includes spoken hook, visual hook, and text overlay.

Usage:
    python hooks_engine.py "content idea title or description"
    python hooks_engine.py "context engineering for rappers" --project vawn
    python hooks_engine.py --from-ideation          # uses top pick from ideation
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


def generate_hooks(client, config, topic, count=5):
    """Generate hook variations for a content topic."""
    profile = config["profile"]
    platforms = ", ".join(config["platforms"])

    prompt = f"""You are a social media hook specialist for an independent artist.

ARTIST PROFILE:
{profile}

PLATFORMS: {platforms}

CONTENT TOPIC: {topic}

Generate exactly {count} hook variations. Each hook should be designed to stop the scroll in the first 3 seconds.

Hook types to use (mix them):
- Curiosity hook: creates an information gap the viewer must close
- Contrarian hook: challenges a common belief
- Story hook: starts mid-action to pull the viewer in
- Result hook: leads with an impressive outcome
- Pattern interrupt: does something unexpected

For each hook, provide:
1. spoken_hook: What is said out loud (15-25 words, conversational, NOT generic motivational)
2. visual_hook: What the viewer sees in the first 3 seconds
3. text_overlay: Bold text on screen (5-8 words max, for short form)
4. hook_type: Which type this is
5. energy: The vibe/tone

Return ONLY valid JSON:
{{
  "hooks": [
    {{
      "number": 1,
      "spoken_hook": "exact words to say",
      "visual_hook": "what viewer sees",
      "text_overlay": "BOLD TEXT ON SCREEN",
      "hook_type": "curiosity|contrarian|story|result|pattern_interrupt",
      "energy": "brief vibe description"
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
    return {"hooks": [], "raw": text}


def format_hooks_obsidian(topic, hooks_data, project="vawn"):
    """Format hooks as Obsidian note."""
    today = datetime.now().strftime("%Y-%m-%d")
    hooks = hooks_data.get("hooks", [])
    safe_topic = topic[:50].replace("/", "-").replace("\\", "-")

    lines = [
        "---",
        f"title: Hooks -- {safe_topic}",
        f"date: {today}",
        "tags:",
        "  - scripting/hooks",
        f"  - project/{project}",
        "---",
        "",
        f"# Hooks -- {safe_topic}",
        "",
        f"> [!info] {len(hooks)} hook variations generated",
        "",
    ]

    for hook in hooks:
        num = hook.get("number", "?")
        htype = hook.get("hook_type", "?")
        energy = hook.get("energy", "")

        lines.append(f"## Hook #{num} -- {htype}")
        lines.append("")
        lines.append(f"*{energy}*")
        lines.append("")
        lines.append(f"> [!quote] Spoken Hook")
        lines.append(f"> \"{hook.get('spoken_hook', '')}\"")
        lines.append("")
        lines.append(f"> [!example] Visual Hook")
        lines.append(f"> {hook.get('visual_hook', '')}")
        lines.append("")
        lines.append(f"**Text Overlay:** =={hook.get('text_overlay', '')}==")
        lines.append("")

    lines.append(f"## Source")
    lines.append(f"- [[Content Ideation -- {today}]]")
    lines.append("")

    return "\n".join(lines)


def run(topic=None, project_name="vawn", from_ideation=False):
    """Run hook generation."""
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
        print("[Hooks] No topic provided. Use --from-ideation or pass a topic.")
        return None

    print(f"\n[Hooks] Generating hooks for: {topic}")
    hooks_data = generate_hooks(client, config, topic)

    # Save JSON
    output = {
        "project": project_name,
        "generated": now_iso(),
        "topic": topic,
        "hooks": hooks_data,
    }
    save_json(output_dir / "hooks_results.json", output)

    # Save Obsidian note
    content = format_hooks_obsidian(topic, hooks_data, project_name)
    safe_topic = topic[:50].replace("/", "-").replace("\\", "-")
    md_path = output_dir / f"Hooks -- {safe_topic}.md"
    md_path.write_text(content, encoding="utf-8")
    print(f"[Hooks] Wrote {md_path.name}")

    hooks = hooks_data.get("hooks", [])
    for h in hooks:
        print(f"  #{h.get('number')} [{h.get('hook_type')}]: \"{h.get('spoken_hook', '')[:80]}\"")

    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hook generator")
    parser.add_argument("topic", nargs="?", help="Content topic")
    parser.add_argument("--project", default="vawn")
    parser.add_argument("--from-ideation", action="store_true")
    args = parser.parse_args()

    run(args.topic, args.project, args.from_ideation)
