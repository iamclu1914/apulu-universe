"""
briefing_recycle.py -- APU-97 Content Recycling System

Takes daily briefings and recycles recommended content into platform-specific
posts using the content cascade pipeline.

Usage:
    python briefing_recycle.py --briefing path/to/Daily\ Briefing\ --\ 2026-04-12.md
    python briefing_recycle.py --auto  # Process most recent briefing
    python briefing_recycle.py --date 2026-04-12
"""

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cascade.content_cascade import generate_cascade, format_cascade_obsidian
from pipeline_config import (
    load_project_config, get_anthropic_client, get_output_dir,
    save_json, load_json, now_iso,
)


def extract_briefing_content(briefing_path):
    """Extract recommended content from daily briefing markdown."""
    if not briefing_path.exists():
        print(f"[Error] Briefing file not found: {briefing_path}")
        return None

    content = briefing_path.read_text(encoding="utf-8")

    # Extract recommended content section
    recommended_match = re.search(
        r'## Recommended Content\s*\n(.*?)(?=^## |\Z)',
        content,
        re.MULTILINE | re.DOTALL
    )

    extracted = {}

    if recommended_match:
        recommended_section = recommended_match.group(1).strip()

        # Extract main content idea from abstract
        abstract_match = re.search(
            r'> \[!abstract\] Top Pick: (.*?)(?=\n\n|\n>|\Z)',
            recommended_section,
            re.DOTALL
        )

        if abstract_match:
            top_pick = abstract_match.group(1).strip()
            # Clean up the content
            top_pick = re.sub(r'\n> ', ' ', top_pick)
            extracted['top_pick'] = top_pick

    # Extract open gaps for additional context
    gaps_match = re.search(
        r'## Open Gaps \(from ideation\)\s*\n(.*?)(?=^## |\Z)',
        content,
        re.MULTILINE | re.DOTALL
    )

    if gaps_match:
        gaps_section = gaps_match.group(1).strip()
        # Extract bullet points
        gaps = re.findall(r'- (.*?)(?=\n-|\Z)', gaps_section, re.DOTALL)
        extracted['gaps'] = [gap.strip().replace('\n', ' ') for gap in gaps]

    # Extract discovery highlights
    discovery_match = re.search(
        r'## Discovery Highlights\s*\n(.*?)(?=^## |\Z)',
        content,
        re.MULTILINE | re.DOTALL
    )

    if discovery_match:
        discovery_section = discovery_match.group(1).strip()
        extracted['discovery'] = discovery_section

    return extracted


def create_recycling_prompt(briefing_content, project_name="vawn"):
    """Create a formatted transcript-like prompt for cascade system."""
    if not briefing_content:
        return None

    # Build a comprehensive content brief
    prompt_parts = []

    if briefing_content.get('top_pick'):
        prompt_parts.append(f"KEY CONTENT IDEA: {briefing_content['top_pick']}")

    if briefing_content.get('gaps'):
        prompt_parts.append("\nCONTENT OPPORTUNITIES:")
        for i, gap in enumerate(briefing_content['gaps'], 1):
            prompt_parts.append(f"{i}. {gap}")

    if briefing_content.get('discovery'):
        # Extract meaningful insights from discovery section
        discovery_lines = briefing_content['discovery'].split('\n')
        meaningful_content = []
        for line in discovery_lines:
            if '@' in line and ('plays' in line or 'likes' in line or 'views' in line):
                meaningful_content.append(line.strip())

        if meaningful_content:
            prompt_parts.append("\nTRENDING CONTENT CONTEXT:")
            prompt_parts.extend(meaningful_content[:5])  # Limit to top 5

    return "\n".join(prompt_parts)


def recycle_briefing_content(client, config, briefing_path, platforms=None):
    """Main recycling function that processes briefing through cascade."""
    print(f"\n[Recycle] Processing briefing: {briefing_path.name}")

    # Extract content from briefing
    briefing_content = extract_briefing_content(briefing_path)
    if not briefing_content:
        print("[Error] Could not extract content from briefing")
        return None

    # Create transcript-like content for cascade
    recycling_prompt = create_recycling_prompt(briefing_content)
    if not recycling_prompt:
        print("[Error] Could not create recycling prompt")
        return None

    print(f"[Recycle] Content extracted: {len(recycling_prompt)} chars")
    print(f"[Recycle] Generating platform-specific content...")

    # Use the existing cascade system
    cascade_data = generate_cascade(
        client,
        config,
        recycling_prompt,
        f"Daily Briefing Recycle - {briefing_path.stem}",
        platforms
    )

    return cascade_data


def find_recent_briefing(research_dir, date=None):
    """Find the most recent briefing file or specific date."""
    briefings_dir = research_dir / "vawn" / "briefings"

    if not briefings_dir.exists():
        print(f"[Error] Briefings directory not found: {briefings_dir}")
        return None

    if date:
        # Look for specific date
        pattern = f"Daily Briefing*{date}.md"
        matches = list(briefings_dir.glob(pattern))
        if matches:
            return matches[0]
        else:
            print(f"[Error] No briefing found for date: {date}")
            return None
    else:
        # Find most recent
        briefing_files = list(briefings_dir.glob("Daily Briefing*.md"))
        if not briefing_files:
            print("[Error] No briefing files found")
            return None

        # Sort by modification time
        recent_briefing = max(briefing_files, key=lambda f: f.stat().st_mtime)
        return recent_briefing


def run(briefing_path=None, project_name="vawn", date=None, auto=False, platforms=None):
    """Run the briefing recycling system."""
    config = load_project_config(project_name)
    client = get_anthropic_client(config)
    output_dir = get_output_dir(config, "recycle")

    # Determine briefing file
    if auto or date:
        # Find in research directory
        research_dir = Path(__file__).resolve().parent.parent / "research"
        briefing_path = find_recent_briefing(research_dir, date)
        if not briefing_path:
            return None
    elif briefing_path:
        briefing_path = Path(briefing_path)
    else:
        print("[Error] No briefing specified")
        return None

    # Process the briefing
    cascade_data = recycle_briefing_content(client, config, briefing_path, platforms)
    if not cascade_data:
        return None

    # Save outputs
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = {
        "project": project_name,
        "generated": now_iso(),
        "source_briefing": str(briefing_path),
        "recycle_type": "daily_briefing",
        "cascade": cascade_data,
    }

    # Save JSON
    json_path = output_dir / f"recycle_results_{timestamp}.json"
    save_json(json_path, output)

    # Save Obsidian note
    content = format_cascade_obsidian(
        f"Briefing Recycle - {briefing_path.stem}",
        cascade_data,
        project_name
    )
    md_path = output_dir / f"Recycle -- {briefing_path.stem}.md"
    md_path.write_text(content, encoding="utf-8")

    print(f"[Recycle] Saved results: {json_path.name}")
    print(f"[Recycle] Saved note: {md_path.name}")

    # Print summary
    print(f"\n{'='*60}")
    print(f"APU-97 CONTENT RECYCLE COMPLETE")
    x = cascade_data.get("x", {})
    if x.get("tweet"):
        print(f"  X: {x['tweet']}")
    threads = cascade_data.get("threads", {})
    if threads.get("post"):
        print(f"  Threads: {threads['post']}")
    tt = cascade_data.get("tiktok", {})
    if tt.get("caption"):
        print(f"  TikTok: {tt['caption']}")
    print(f"{'='*60}\n")

    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="APU-97 Content Recycling System")
    parser.add_argument("--briefing", type=str, help="Path to briefing file")
    parser.add_argument("--project", default="vawn")
    parser.add_argument("--date", type=str, help="Date for specific briefing (YYYY-MM-DD)")
    parser.add_argument("--auto", action="store_true", help="Process most recent briefing")
    parser.add_argument("--platforms", type=str, help="Comma-separated platforms")
    args = parser.parse_args()

    if not any([args.briefing, args.auto, args.date]):
        print("Error: Must specify --briefing, --auto, or --date")
        sys.exit(1)

    run(args.briefing, args.project, args.date, args.auto, args.platforms)