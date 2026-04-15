"""
ideation_engine.py -- Takes discovery pipeline results and generates content ideas.
Analyzes competitive landscape, identifies gaps, and produces ranked video/post ideas.

Usage:
    python ideation_engine.py                      # uses vawn config + latest research
    python ideation_engine.py --project vawn
    python ideation_engine.py --focus "suno ai"    # focus ideation on specific topic
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline_config import (
    load_project_config, get_anthropic_client, get_output_dir,
    save_json, load_json, today_str, now_iso,
)
from obsidian_formatter import _human_number


def gather_research(output_dir):
    """Load the latest results from all discovery pipelines."""
    research = {}
    pipeline_files = {
        "x": "x_pipeline_results.json",
        "tiktok": "tiktok_pipeline_results.json",
        "instagram": "ig_pipeline_results.json",
        "reddit": "reddit_pipeline_results.json",
        "youtube": "yt_pipeline_results.json",
    }

    for name, filename in pipeline_files.items():
        path = output_dir / filename
        if path.exists():
            data = load_json(path)
            # Only include top 10 to keep prompt manageable
            top = data.get("top_20", [])[:10]
            research[name] = {
                "total": data.get(f"total_{'tweets' if name == 'x' else 'posts' if name in ('instagram', 'reddit') else 'videos'}", 0),
                "top": top,
            }

    return research


def summarize_research(research):
    """Condense research into a prompt-friendly summary."""
    lines = []
    for platform, data in research.items():
        lines.append(f"\n### {platform.upper()} ({data['total']} items found)")
        for item in data["top"][:5]:
            if platform == "x":
                author = item.get("author", {}).get("handle", "?")
                text = (item.get("text", "") or "")[:150]
                eng = item.get("scoring", {}).get("engagement", 0)
                lines.append(f"- @{author} ({eng} engagement): {text}")
            elif platform == "tiktok":
                author = item.get("author", {}).get("username", "?")
                text = (item.get("text", "") or "")[:150]
                plays = _human_number(item.get("plays", 0))
                lines.append(f"- @{author} ({plays} plays): {text}")
            elif platform == "instagram":
                author = item.get("author", {}).get("username", "?")
                caption = (item.get("caption", "") or "")[:150]
                likes = _human_number(item.get("likes", 0))
                lines.append(f"- @{author} ({likes} likes): {caption}")
            elif platform == "reddit":
                sub = item.get("subreddit", "?")
                title = (item.get("title", "") or "")[:150]
                upvotes = item.get("scoring", {}).get("upvotes", 0)
                lines.append(f"- r/{sub} ({upvotes} upvotes): {title}")
            elif platform == "youtube":
                title = (item.get("title", "") or "")[:100]
                channel = item.get("channel", "?")
                views = _human_number(item.get("views", 0))
                lines.append(f"- {channel} ({views} views): {title}")

    return "\n".join(lines)


def run_ideation(client, config, research_summary, focus=None):
    """Use Claude to analyze research and generate content ideas."""
    profile = config["profile"]
    niches = ", ".join(config["niches"])
    comparable = ", ".join(config.get("comparable_artists", []))
    platforms = ", ".join(config["platforms"])

    focus_str = f"\n\nFOCUS AREA: {focus}\nPrioritize ideas related to this topic." if focus else ""

    # Load pillar context if bridge has exported it
    pillar_str = ""
    config_dir = Path(__file__).resolve().parent.parent / "config"
    pillar_data = load_json(config_dir / "pillar_context.json")
    if pillar_data.get("today"):
        today_pillar = pillar_data["today"].get("pillar", "")
        week = pillar_data.get("week_ahead", [])
        week_lines = "\n".join(f"  {d['day']}: {d['pillar']}" for d in week)
        pillar_str = f"""

POSTING SCHEDULE (7-day pillar rotation):
  Today's pillar: {today_pillar}
{week_lines}

Map your 7 content ideas across these pillars where possible. Prioritize ideas that fit today's pillar ({today_pillar})."""

    # Load engagement feedback if bridge has exported it
    engagement_str = ""
    engagement_data = load_json(config_dir / "engagement_feedback.json")
    if engagement_data.get("recommendation"):
        engagement_str = f"\n\nENGAGEMENT FEEDBACK: {engagement_data['recommendation']}"

    prompt = f"""You are a content strategist for an independent artist.

ARTIST PROFILE:
{profile}

NICHES: {niches}
COMPARABLE ARTISTS: {comparable}
ACTIVE PLATFORMS: {platforms}{focus_str}{pillar_str}{engagement_str}

TODAY'S DISCOVERY RESEARCH (scraped from X, Instagram, TikTok, Reddit, YouTube):
{research_summary}

Based on this research, produce a structured content ideation report:

1. **COMPETITIVE LANDSCAPE** -- What angles are saturated right now? What are 3-5 topics everyone is already talking about?

2. **OPEN GAPS** -- What are 3-5 topics or angles that nobody is covering well, or that have untapped potential?

3. **PERFORMANCE OUTLIERS** -- From the research, what 2-3 pieces of content performed way above average? Why did they work?

4. **CONTENT IDEAS** -- Generate exactly 7 content ideas ranked by potential. For each:
   - Title/hook (one line)
   - Angle (what makes this different)
   - Format (reel, carousel, text post, video, thread)
   - Platforms (which of {platforms} to post on)
   - Desire it maps to (curiosity, aspiration, fear, identity, entertainment)
   - Competitive gap it fills
   - Confidence (high/medium/low)

5. **RECOMMENDED PRIORITY** -- Pick the top 3 and explain why they should be done first.

Return ONLY valid JSON with this exact structure:
{{
  "competitive_landscape": {{
    "saturated_angles": ["angle1", "angle2"],
    "open_gaps": ["gap1", "gap2"],
    "performance_outliers": [
      {{"content": "description", "why_it_worked": "reason", "platform": "platform"}}
    ]
  }},
  "content_ideas": [
    {{
      "rank": 1,
      "title": "title",
      "angle": "what makes it different",
      "format": "reel|carousel|text|video|thread",
      "platforms": ["platform1", "platform2"],
      "desire": "curiosity|aspiration|fear|identity|entertainment",
      "competitive_gap": "what gap this fills",
      "confidence": "high|medium|low"
    }}
  ],
  "priority_picks": [
    {{"rank": 1, "title": "title", "reason": "why this first"}}
  ]
}}"""

    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    text = resp.content[0].text

    # Parse JSON from response
    try:
        start = text.find("{")
        if start == -1:
            raise ValueError("No JSON found")
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(text[start:i + 1])
        raise ValueError("Unbalanced braces")
    except (json.JSONDecodeError, ValueError) as e:
        print(f"  [WARN] JSON parse failed, returning raw text: {e}")
        return {"raw_response": text}


def format_ideation_obsidian(ideation, project="vawn"):
    """Format ideation results as Obsidian note."""
    today = datetime.now().strftime("%Y-%m-%d")
    cl = ideation.get("competitive_landscape", {})
    ideas = ideation.get("content_ideas", [])
    picks = ideation.get("priority_picks", [])

    lines = [
        "---",
        f"title: Content Ideation -- {today}",
        f"date: {today}",
        "tags:",
        "  - ideation",
        f"  - project/{project}",
        "  - research",
        "---",
        "",
        f"# Content Ideation -- {today}",
        "",
        f"> [!abstract] Summary",
        f"> Generated {len(ideas)} content ideas from cross-platform discovery research.",
        "",
        "## Competitive Landscape",
        "",
        "### Saturated Angles",
        "",
    ]

    for angle in cl.get("saturated_angles", []):
        lines.append(f"- {angle}")
    lines.append("")

    lines.append("### Open Gaps")
    lines.append("")
    for gap in cl.get("open_gaps", []):
        lines.append(f"- {gap}")
    lines.append("")

    lines.append("### Performance Outliers")
    lines.append("")
    for outlier in cl.get("performance_outliers", []):
        lines.append(f"> [!example] {outlier.get('platform', '?').upper()}")
        lines.append(f"> {outlier.get('content', '')}")
        lines.append(f"> **Why it worked:** {outlier.get('why_it_worked', '')}")
        lines.append("")

    lines.append("## Content Ideas (Ranked)")
    lines.append("")

    for idea in ideas:
        rank = idea.get("rank", "?")
        confidence = idea.get("confidence", "?")
        conf_icon = {"high": "tip", "medium": "info", "low": "warning"}.get(confidence, "note")

        lines.append(f"### #{rank} -- {idea.get('title', 'Untitled')}")
        lines.append("")
        lines.append(f"> [!{conf_icon}] Confidence: {confidence}")
        lines.append(f"> {idea.get('angle', '')}")
        lines.append("")
        lines.append(f"| Detail | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Format | {idea.get('format', '?')} |")
        lines.append(f"| Platforms | {', '.join(idea.get('platforms', []))} |")
        lines.append(f"| Desire | {idea.get('desire', '?')} |")
        lines.append(f"| Gap | {idea.get('competitive_gap', '?')} |")
        lines.append("")

    if picks:
        lines.append("## Priority Picks")
        lines.append("")
        lines.append("> [!important] Do These First")
        for pick in picks:
            lines.append(f"> **#{pick.get('rank', '?')} -- {pick.get('title', '')}**")
            lines.append(f"> {pick.get('reason', '')}")
            lines.append(f"> ")
        lines.append("")

    # Link back to discovery
    lines.append("## Source Research")
    lines.append("")
    lines.append(f"- [[Discovery Brief -- {today}]]")
    lines.append(f"- [[X Pipeline -- {today}]]")
    lines.append(f"- [[TikTok Pipeline -- {today}]]")
    lines.append(f"- [[Instagram Pipeline -- {today}]]")
    lines.append(f"- [[Reddit Pipeline -- {today}]]")
    lines.append("")

    return "\n".join(lines)


def run(project_name="vawn", focus=None):
    """Run the ideation engine."""
    config = load_project_config(project_name)
    client = get_anthropic_client(config)
    discovery_dir = get_output_dir(config, "discovery")
    output_dir = get_output_dir(config, "ideation")

    print(f"\n{'='*60}")
    print(f"  Ideation Engine -- {project_name}")
    print(f"{'='*60}")

    # Gather research from discovery phase
    print("\n[Ideation] Loading discovery research...")
    research = gather_research(discovery_dir)
    if not research:
        print("[Ideation] No research found. Run discovery pipelines first.")
        return None

    platforms_found = list(research.keys())
    print(f"[Ideation] Found research from: {', '.join(platforms_found)}")

    research_summary = summarize_research(research)

    # Run ideation
    print("[Ideation] Generating content ideas...")
    ideation = run_ideation(client, config, research_summary, focus)

    # Save JSON
    output = {
        "project": project_name,
        "generated": now_iso(),
        "focus": focus,
        "research_sources": platforms_found,
        "ideation": ideation,
    }
    json_path = output_dir / "ideation_results.json"
    save_json(json_path, output)

    # Save Obsidian note
    today = datetime.now().strftime("%Y-%m-%d")
    obsidian_content = format_ideation_obsidian(ideation, project_name)
    md_path = output_dir / f"Content Ideation -- {today}.md"
    md_path.write_text(obsidian_content, encoding="utf-8")
    print(f"[Ideation] Wrote {md_path.name}")

    # Print summary
    ideas = ideation.get("content_ideas", [])
    picks = ideation.get("priority_picks", [])

    print(f"\n{'='*60}")
    print(f"  Ideation Results -- {len(ideas)} ideas generated")
    print(f"{'='*60}")
    for idea in ideas[:5]:
        print(f"  #{idea.get('rank', '?')} [{idea.get('confidence', '?')}] {idea.get('title', '')}")
        print(f"       {idea.get('format', '?')} → {', '.join(idea.get('platforms', []))}")
    if picks:
        pick_nums = ", ".join(f"#{p.get('rank')}" for p in picks)
        print(f"\n  Priority: {pick_nums}")
    print(f"{'='*60}\n")

    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Content ideation engine")
    parser.add_argument("--project", default="vawn", help="Project config to use")
    parser.add_argument("--focus", type=str, help="Focus ideation on specific topic")
    args = parser.parse_args()

    run(args.project, args.focus)
