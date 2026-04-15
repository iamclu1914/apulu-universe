"""
obsidian_formatter.py -- Converts pipeline results into Obsidian-flavored markdown notes.
Each pipeline run produces a dated note with frontmatter, callouts, and wikilinks.
"""

from datetime import datetime
from pathlib import Path


def _human_number(n):
    """Format number: 1500000 -> 1.5M."""
    if n is None:
        return "N/A"
    n = int(n)
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return f"{n:,}"


def _date_display(timestamp):
    """Parse various timestamp formats into readable date."""
    if not timestamp:
        return "Unknown"
    try:
        if isinstance(timestamp, (int, float)) and timestamp > 1_000_000_000:
            return datetime.fromtimestamp(timestamp).strftime("%b %d, %Y %I:%M %p")
        dt = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y %I:%M %p")
    except (ValueError, TypeError, OSError):
        return str(timestamp)[:20]


def format_x_note(results, project="vawn"):
    """Format X/Twitter pipeline results as Obsidian note."""
    today = datetime.now().strftime("%Y-%m-%d")
    total = results.get("total_tweets", 0)
    top = results.get("top_20", [])

    lines = [
        "---",
        f"title: X Pipeline -- {today}",
        f"date: {today}",
        "tags:",
        "  - pipeline/x",
        f"  - project/{project}",
        "  - research",
        "---",
        "",
        f"# X/Twitter Discovery -- {today}",
        "",
        f"> [!info] Pipeline Run",
        f"> **{total}** tweets scraped and scored.",
        "",
        "## Top Results",
        "",
    ]

    for i, t in enumerate(top[:20], 1):
        s = t.get("scoring", {})
        author = t.get("author", {})
        handle = author.get("handle", "?")
        followers = _human_number(author.get("followers", 0))
        text = (t.get("text", "") or "").replace("\n", " ")[:200]
        url = t.get("url", "")

        lines.append(f"### #{i} -- @{handle}")
        lines.append("")
        lines.append(f"> [!quote] Tweet")
        lines.append(f"> {text}")
        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Followers | {followers} |")
        lines.append(f"| Score | {s.get('score', 0)} |")
        lines.append(f"| Velocity | {s.get('velocity', 0)} |")
        lines.append(f"| Engagement | {_human_number(s.get('engagement', 0))} |")
        lines.append(f"| Views | {_human_number(t.get('views', 0))} |")
        if url:
            lines.append(f"| Link | [View on X]({url}) |")
        lines.append("")

    return "\n".join(lines)


def format_ig_note(results, project="vawn"):
    """Format Instagram pipeline results as Obsidian note."""
    today = datetime.now().strftime("%Y-%m-%d")
    total = results.get("total_posts", 0)
    top = results.get("top_20", [])

    lines = [
        "---",
        f"title: Instagram Pipeline -- {today}",
        f"date: {today}",
        "tags:",
        "  - pipeline/instagram",
        f"  - project/{project}",
        "  - research",
        "---",
        "",
        f"# Instagram Discovery -- {today}",
        "",
        f"> [!info] Pipeline Run",
        f"> **{total}** posts scraped and scored.",
        "",
        "## Top Results",
        "",
    ]

    for i, p in enumerate(top[:20], 1):
        s = p.get("scoring", {})
        author = p.get("author", {})
        username = author.get("username", "?")
        caption = (p.get("caption", "") or "").replace("\n", " ")[:200]
        url = p.get("url", "")
        reel = " ==REEL==" if p.get("is_reel") else ""
        music = f" 🎵 {p.get('music')}" if p.get("music") else ""

        lines.append(f"### #{i} -- @{username}{reel}")
        lines.append("")
        if caption:
            lines.append(f"> [!quote] Caption")
            lines.append(f"> {caption}")
            lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Score | {s.get('score', 0)} |")
        lines.append(f"| Likes | {_human_number(p.get('likes', 0))} |")
        lines.append(f"| Comments | {_human_number(p.get('comments', 0))} |")
        lines.append(f"| Engagement Rate | {s.get('engagement_rate', 0)}% |")
        if p.get("views"):
            lines.append(f"| Views | {_human_number(p.get('views', 0))} |")
        if p.get("music"):
            lines.append(f"| Music | {p['music']} |")
        if url:
            lines.append(f"| Link | [View on IG]({url}) |")
        lines.append("")

    return "\n".join(lines)


def format_tiktok_note(results, project="vawn"):
    """Format TikTok pipeline results as Obsidian note."""
    today = datetime.now().strftime("%Y-%m-%d")
    total = results.get("total_videos", 0)
    top = results.get("top_20", [])

    lines = [
        "---",
        f"title: TikTok Pipeline -- {today}",
        f"date: {today}",
        "tags:",
        "  - pipeline/tiktok",
        f"  - project/{project}",
        "  - research",
        "---",
        "",
        f"# TikTok Discovery -- {today}",
        "",
        f"> [!info] Pipeline Run",
        f"> **{total}** videos scraped and scored.",
        "",
        "## Top Results",
        "",
    ]

    for i, v in enumerate(top[:20], 1):
        s = v.get("scoring", {})
        author = v.get("author", {})
        username = author.get("username", "?")
        text = (v.get("text", "") or "").replace("\n", " ")[:200]
        url = v.get("url", "")

        lines.append(f"### #{i} -- @{username}")
        lines.append("")
        if text:
            lines.append(f"> [!quote] Caption")
            lines.append(f"> {text}")
            lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Score | {s.get('score', 0)} |")
        lines.append(f"| Plays | {_human_number(v.get('plays', 0))} |")
        lines.append(f"| Likes | {_human_number(v.get('likes', 0))} |")
        lines.append(f"| Shares | {_human_number(v.get('shares', 0))} |")
        lines.append(f"| Virality | {s.get('virality', 0)} |")
        if v.get("music"):
            lines.append(f"| Music | {v['music']} |")
        if v.get("duration"):
            lines.append(f"| Duration | {v['duration']}s |")
        if url:
            lines.append(f"| Link | [View on TikTok]({url}) |")
        lines.append("")

    return "\n".join(lines)


def format_reddit_note(results, project="vawn"):
    """Format Reddit pipeline results as Obsidian note."""
    today = datetime.now().strftime("%Y-%m-%d")
    total = results.get("total_posts", 0)
    top = results.get("top_20", [])

    lines = [
        "---",
        f"title: Reddit Pipeline -- {today}",
        f"date: {today}",
        "tags:",
        "  - pipeline/reddit",
        f"  - project/{project}",
        "  - research",
        "---",
        "",
        f"# Reddit Discovery -- {today}",
        "",
        f"> [!info] Pipeline Run",
        f"> **{total}** posts scraped and scored.",
        "",
        "## Top Results",
        "",
    ]

    for i, p in enumerate(top[:20], 1):
        s = p.get("scoring", {})
        subreddit = p.get("subreddit", "?").replace("r/", "")
        author = p.get("author", "?")
        title = p.get("title", "No title")
        text = (p.get("text", "") or "").replace("\n", " ")[:300]
        url = p.get("url", "")

        lines.append(f"### #{i} -- r/{subreddit}")
        lines.append("")
        lines.append(f"**{title}** -- u/{author}")
        lines.append("")
        if text:
            lines.append(f"> [!quote] Post")
            lines.append(f"> {text}")
            lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Score | {s.get('score', 0)} |")
        lines.append(f"| Upvotes | {_human_number(s.get('upvotes', 0))} |")
        lines.append(f"| Comments | {_human_number(s.get('comments', 0))} |")
        lines.append(f"| Discussion Depth | {s.get('discussion', 0)} |")
        lines.append(f"| Upvote Ratio | {s.get('upvote_ratio', 0)} |")
        if url:
            lines.append(f"| Link | [View on Reddit]({url}) |")
        lines.append("")

    return "\n".join(lines)


def format_youtube_note(results, project="vawn"):
    """Format YouTube pipeline results as Obsidian note."""
    today = datetime.now().strftime("%Y-%m-%d")
    total = results.get("total_videos", 0)
    top = results.get("top_20", [])
    nlm = results.get("notebooklm")

    lines = [
        "---",
        f"title: YouTube Pipeline -- {today}",
        f"date: {today}",
        "tags:",
        "  - pipeline/youtube",
        f"  - project/{project}",
        "  - research",
        "---",
        "",
        f"# YouTube Discovery -- {today}",
        "",
        f"> [!info] Pipeline Run",
        f"> **{total}** videos found across keyword searches.",
        "",
    ]

    if nlm:
        lines.append("> [!success] NotebookLM Integration")
        lines.append(f"> Notebook: `{nlm.get('notebook_id', 'N/A')}`")
        if nlm.get("summary"):
            lines.append(f"> ")
            lines.append(f"> {nlm['summary'][:500]}")
        if nlm.get("suggested_topics"):
            lines.append(f"> ")
            lines.append(f"> **Suggested topics:**")
            for topic in nlm["suggested_topics"][:5]:
                lines.append(f"> - {topic.get('question', '')}")
        lines.append("")

    lines.append("## Top Results")
    lines.append("")

    for i, v in enumerate(top[:20], 1):
        title = v.get("title", "Unknown")
        channel = v.get("channel", "?")
        subs = _human_number(v.get("subscribers"))
        views = _human_number(v.get("views"))
        eng = v.get("engagement_ratio")
        eng_str = f"{eng:.1f}%" if eng else "N/A"
        url = v.get("url", "")
        duration = v.get("duration")

        lines.append(f"### #{i} -- {title}")
        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Channel | {channel} |")
        lines.append(f"| Subscribers | {subs} |")
        lines.append(f"| Views | {views} |")
        lines.append(f"| Engagement | {eng_str} |")
        if duration:
            m, s = divmod(int(duration), 60)
            lines.append(f"| Duration | {m}:{s:02d} |")
        if url:
            lines.append(f"| Link | [Watch on YouTube]({url}) |")
        lines.append("")

    return "\n".join(lines)


def format_discovery_brief(results, project="vawn"):
    """Format the unified discovery brief as Obsidian note."""
    today = datetime.now().strftime("%Y-%m-%d")
    pipelines = results.get("pipelines", {})
    top_content = results.get("top_content", [])

    lines = [
        "---",
        f"title: Discovery Brief -- {today}",
        f"date: {today}",
        "tags:",
        "  - pipeline/brief",
        f"  - project/{project}",
        "  - research",
        "---",
        "",
        f"# Discovery Brief -- {today}",
        "",
        "> [!abstract] Summary",
        "> Daily discovery brief across all active pipelines.",
        "",
        "## Pipeline Status",
        "",
        "| Pipeline | Status | Items |",
        "|----------|--------|-------|",
    ]

    for name, info in pipelines.items():
        status = "Pass" if info.get("status") == "ok" else "Fail"
        icon = "checkmark" if status == "Pass" else "cross"
        count = info.get("total", "?")
        lines.append(f"| {name} | {status} | {count} |")

    lines.append("")
    lines.append("## Cross-Platform Highlights")
    lines.append("")

    # Group top content by pipeline
    by_pipeline = {}
    for item in top_content:
        p = item.get("_pipeline", "unknown")
        by_pipeline.setdefault(p, []).append(item)

    for pipeline, items in by_pipeline.items():
        lines.append(f"### {pipeline.upper()}")
        lines.append("")
        for item in items[:3]:
            # Adapt based on pipeline type
            if pipeline == "x":
                author = item.get("author", {}).get("handle", "?")
                text = (item.get("text", "") or "")[:120]
                lines.append(f"- **@{author}**: {text}")
            elif pipeline == "tiktok":
                author = item.get("author", {}).get("username", "?")
                text = (item.get("text", "") or "")[:120]
                plays = _human_number(item.get("plays", 0))
                lines.append(f"- **@{author}** ({plays} plays): {text}")
            elif pipeline == "instagram":
                author = item.get("author", {}).get("username", "?")
                caption = (item.get("caption", "") or "")[:120]
                lines.append(f"- **@{author}**: {caption}")
            elif pipeline == "reddit":
                sub = item.get("subreddit", "?")
                title = item.get("title", "")[:120]
                lines.append(f"- **r/{sub}**: {title}")
            elif pipeline == "youtube":
                title = (item.get("title", "") or "")[:100]
                channel = item.get("channel", "?")
                lines.append(f"- **{channel}**: {title}")
        lines.append("")

    # Link to individual pipeline notes
    lines.append("## Pipeline Notes")
    lines.append("")
    lines.append(f"- [[X Pipeline -- {today}]]")
    lines.append(f"- [[Instagram Pipeline -- {today}]]")
    lines.append(f"- [[TikTok Pipeline -- {today}]]")
    lines.append(f"- [[Reddit Pipeline -- {today}]]")
    lines.append(f"- [[YouTube Pipeline -- {today}]]")
    lines.append("")

    return "\n".join(lines)


# Mapping of pipeline names to formatters
FORMATTERS = {
    "x": format_x_note,
    "instagram": format_ig_note,
    "tiktok": format_tiktok_note,
    "reddit": format_reddit_note,
    "youtube": format_youtube_note,
    "brief": format_discovery_brief,
}


def write_obsidian_note(pipeline_name, results, output_dir, project="vawn"):
    """Write pipeline results as an Obsidian markdown note.

    Args:
        pipeline_name: Key from FORMATTERS (x, instagram, tiktok, reddit, youtube, brief)
        results: Pipeline output dict
        output_dir: Directory to write the note
        project: Project name for tags

    Returns:
        Path to the written note.
    """
    formatter = FORMATTERS.get(pipeline_name)
    if not formatter:
        raise ValueError(f"No formatter for pipeline: {pipeline_name}")

    today = datetime.now().strftime("%Y-%m-%d")
    content = formatter(results, project)

    # Use pipeline-specific naming
    if pipeline_name == "brief":
        filename = f"Discovery Brief -- {today}.md"
    else:
        name_map = {
            "x": "X Pipeline",
            "instagram": "Instagram Pipeline",
            "tiktok": "TikTok Pipeline",
            "reddit": "Reddit Pipeline",
            "youtube": "YouTube Pipeline",
        }
        display = name_map.get(pipeline_name, pipeline_name)
        filename = f"{display} -- {today}.md"

    out_path = Path(output_dir) / filename
    out_path.write_text(content, encoding="utf-8")
    print(f"  [Obsidian] Wrote {filename}")
    return out_path
