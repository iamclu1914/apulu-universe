"""
content_cascade.py -- Takes a YouTube video (or any content) and repurposes it
into platform-specific posts for X, Threads, Bluesky, Instagram, and TikTok.

Usage:
    python content_cascade.py "https://youtube.com/watch?v=..."
    python content_cascade.py --transcript path/to/transcript.txt
    python content_cascade.py "https://youtube.com/..." --platforms x,threads
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline_config import (
    load_project_config, get_anthropic_client, get_output_dir,
    save_json, load_json, now_iso,
)


def get_transcript(youtube_url):
    """Extract transcript from a YouTube video using yt-dlp."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = [
            sys.executable, "-m", "yt_dlp",
            "--write-subs", "--write-auto-subs",
            "--sub-lang", "en", "--skip-download",
            "--sub-format", "json3",
            "-o", f"{tmpdir}/%(id)s",
            youtube_url,
        ]

        try:
            subprocess.run(cmd, capture_output=True, timeout=60)
        except subprocess.TimeoutExpired:
            print("  [WARN] Transcript download timed out")
            return None

        # Find the subtitle file
        sub_files = list(Path(tmpdir).glob("*.json3"))
        if not sub_files:
            print("  [WARN] No transcript found")
            return None

        data = json.loads(sub_files[0].read_text(encoding="utf-8"))
        events = data.get("events", [])
        lines = []
        for e in events:
            segs = e.get("segs", [])
            text = "".join(s.get("utf8", "") for s in segs).strip()
            if text and text != "\n":
                lines.append(text)

        return " ".join(lines)


def generate_cascade(client, config, transcript, source_title="", platforms=None):
    """Generate platform-specific content from transcript."""
    profile = config["profile"]
    active_platforms = platforms or config["platforms"]
    platforms_str = ", ".join(active_platforms)

    # Load content rules if bridge has exported them
    rules_block = ""
    config_dir = Path(__file__).resolve().parent.parent / "config"
    rules_path = config_dir / "content_rules.json"
    if rules_path.exists():
        rules = json.loads(rules_path.read_text(encoding="utf-8"))
        never_say = ", ".join(f'"{w}"' for w in rules.get("never_say", []))
        never_ref = ", ".join(rules.get("never_reference", []))
        voice = rules.get("voice", {})
        pc = rules.get("platform_constraints", {})
        rules_block = f"""

CONTENT RULES (non-negotiable):
- NEVER say: {never_say}
- NEVER reference: {never_ref}
- Threads: NO hashtags (uses Topics only)
- Bluesky: max {pc.get('bluesky', {}).get('max_chars', 250)} chars
- X: max {pc.get('x', {}).get('max_chars', 200)} chars
- TikTok: max {pc.get('tiktok', {}).get('max_caption_lines', 2)} caption lines
- Voice: {voice.get('brand', '')}
- Avoid: {voice.get('avoid', '')}
- All content must be humanized -- strip AI writing patterns"""

    # Truncate transcript to avoid token limits
    max_chars = 8000
    if len(transcript) > max_chars:
        transcript = transcript[:max_chars] + "... [truncated]"

    prompt = f"""You are a content repurposing specialist.

CREATOR PROFILE:
{profile}{rules_block}

SOURCE CONTENT TRANSCRIPT:
{transcript}

SOURCE TITLE: {source_title or "Unknown"}

Repurpose this content for these platforms: {platforms_str}

Generate for each platform:

**X/Twitter**:
- A standalone tweet (under 200 chars, one bar or hot take)
- A 4-tweet thread that breaks down the key insight

**Threads**:
- A conversational 1-3 sentence post ending with a question
- NO hashtags (Threads uses Topics)

**Bluesky**:
- Same energy as X, under 250 chars
- One punchy take

**Instagram**:
- A caption for a Reel (3-5 lines, hook first, 5-8 hashtags at end)
- A caption for a carousel post (longer, storytelling, with CTA)

**TikTok**:
- A 1-2 line caption for a Reel (pattern interrupt hook)
- 3-5 hashtags

RULES:
- NEVER use AI writing cliches ("delve", "landscape", "it's not X it's Y", "let's be honest")
- Match the creator's voice -- anti-hype, quiet authority, earned confidence
- Each platform should feel native, not copy-pasted
- Hooks should stop the scroll

Return ONLY valid JSON:
{{
  "x": {{
    "tweet": "standalone tweet",
    "thread": ["tweet 1", "tweet 2", "tweet 3", "tweet 4"]
  }},
  "threads": {{
    "post": "threads post"
  }},
  "bluesky": {{
    "post": "bluesky post"
  }},
  "instagram": {{
    "reel_caption": "reel caption",
    "carousel_caption": "carousel caption"
  }},
  "tiktok": {{
    "caption": "tiktok caption",
    "hashtags": ["tag1", "tag2"]
  }},
  "key_angles": ["angle1", "angle2", "angle3"]
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
    return {"raw": text}


def format_cascade_obsidian(source_title, cascade_data, project="vawn"):
    """Format cascade results as Obsidian note."""
    today = datetime.now().strftime("%Y-%m-%d")
    safe_title = (source_title or "Content")[:50].replace("/", "-").replace("\\", "-")

    lines = [
        "---",
        f"title: Cascade -- {safe_title}",
        f"date: {today}",
        "tags:",
        "  - cascade",
        f"  - project/{project}",
        "  - distribution",
        "---",
        "",
        f"# Content Cascade -- {safe_title}",
        "",
        f"> [!abstract] Repurposed from source content into platform-specific posts.",
        "",
    ]

    # Key angles
    angles = cascade_data.get("key_angles", [])
    if angles:
        lines.append("## Key Angles")
        lines.append("")
        for a in angles:
            lines.append(f"- {a}")
        lines.append("")

    # X
    x = cascade_data.get("x", {})
    if x:
        lines.append("## X / Twitter")
        lines.append("")
        lines.append("### Standalone Tweet")
        lines.append(f"> {x.get('tweet', '')}")
        lines.append("")
        thread = x.get("thread", [])
        if thread:
            lines.append("### Thread")
            for i, t in enumerate(thread, 1):
                lines.append(f"{i}/ {t}")
                lines.append("")

    # Threads
    threads = cascade_data.get("threads", {})
    if threads:
        lines.append("## Threads")
        lines.append(f"> {threads.get('post', '')}")
        lines.append("")

    # Bluesky
    bsky = cascade_data.get("bluesky", {})
    if bsky:
        lines.append("## Bluesky")
        lines.append(f"> {bsky.get('post', '')}")
        lines.append("")

    # Instagram
    ig = cascade_data.get("instagram", {})
    if ig:
        lines.append("## Instagram")
        lines.append("")
        lines.append("### Reel Caption")
        lines.append(f"```")
        lines.append(ig.get("reel_caption", ""))
        lines.append(f"```")
        lines.append("")
        lines.append("### Carousel Caption")
        lines.append(f"```")
        lines.append(ig.get("carousel_caption", ""))
        lines.append(f"```")
        lines.append("")

    # TikTok
    tt = cascade_data.get("tiktok", {})
    if tt:
        lines.append("## TikTok")
        lines.append(f"> {tt.get('caption', '')}")
        tags = tt.get("hashtags", [])
        if tags:
            lines.append(f"> {' '.join(f'#{t}' for t in tags)}")
        lines.append("")

    return "\n".join(lines)


def run(source=None, project_name="vawn", transcript_path=None, platforms=None):
    """Run the content cascade."""
    config = load_project_config(project_name)
    client = get_anthropic_client(config)
    output_dir = get_output_dir(config, "cascade")

    # Get transcript
    transcript = None
    source_title = source or ""

    if transcript_path:
        transcript = Path(transcript_path).read_text(encoding="utf-8")
        source_title = Path(transcript_path).stem
    elif source and source.startswith("http"):
        print(f"\n[Cascade] Fetching transcript from: {source[:60]}...")
        transcript = get_transcript(source)
        source_title = source

    if not transcript:
        print("[Cascade] No transcript available.")
        return None

    print(f"[Cascade] Transcript: {len(transcript)} chars")
    print(f"[Cascade] Generating platform-specific content...")

    # Parse platforms
    platform_list = None
    if platforms:
        platform_list = [p.strip() for p in platforms.split(",")]

    cascade_data = generate_cascade(client, config, transcript, source_title, platform_list)

    # Save JSON
    output = {
        "project": project_name,
        "generated": now_iso(),
        "source": source_title,
        "cascade": cascade_data,
    }
    save_json(output_dir / "cascade_results.json", output)

    # Save Obsidian note
    content = format_cascade_obsidian(source_title, cascade_data, project_name)
    safe_title = (source_title or "Content")[:50].replace("/", "-").replace("\\", "-")
    md_path = output_dir / f"Cascade -- {safe_title}.md"
    md_path.write_text(content, encoding="utf-8")
    print(f"[Cascade] Wrote {md_path.name}")

    # Print summary
    print(f"\n{'='*60}")
    x = cascade_data.get("x", {})
    if x.get("tweet"):
        print(f"  X: {x['tweet'][:100]}")
    threads = cascade_data.get("threads", {})
    if threads.get("post"):
        print(f"  Threads: {threads['post'][:100]}")
    bsky = cascade_data.get("bluesky", {})
    if bsky.get("post"):
        print(f"  Bluesky: {bsky['post'][:100]}")
    tt = cascade_data.get("tiktok", {})
    if tt.get("caption"):
        print(f"  TikTok: {tt['caption'][:100]}")
    print(f"{'='*60}\n")

    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Content cascade -- repurpose across platforms")
    parser.add_argument("source", nargs="?", help="YouTube URL or content source")
    parser.add_argument("--project", default="vawn")
    parser.add_argument("--transcript", type=str, help="Path to transcript file")
    parser.add_argument("--platforms", type=str, help="Comma-separated platforms")
    args = parser.parse_args()

    run(args.source, args.project, args.transcript, args.platforms)
