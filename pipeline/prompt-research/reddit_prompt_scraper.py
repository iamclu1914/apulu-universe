"""
reddit_prompt_scraper.py -- Scrapes Reddit for AI video prompts and techniques.
Filters for posts containing actual prompts, workflows, and character consistency tips.
Extracts and stores structured prompt data.

Usage:
    python reddit_prompt_scraper.py
    python reddit_prompt_scraper.py --project prompt-generator
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline_config import (
    load_project_config, get_apify_token, get_output_dir,
    save_json, load_json, now_iso, today_str,
)
from discovery.apify_client import ApifyRunner


def has_prompt_content(post):
    """Check if a post likely contains actual prompt text or technique details."""
    text = (post.get("title", "") + " " + post.get("text", "")).lower()
    prompt_signals = [
        "prompt:", "prompt =", "my prompt", "here's my prompt",
        "settings:", "parameters:", "workflow:", "technique:",
        "character consistency", "reference image", "seed:",
        "camera movement", "style:", "negative prompt",
        "--ar ", "--v ", "--s ", "cfg scale",
        "higgsfield", "cinema 2.5", "kling", "runway",
        "step by step", "how i made", "how to get",
    ]
    return any(signal in text for signal in prompt_signals)


def extract_prompts_from_text(text):
    """Try to extract prompt-like strings from post text."""
    prompts = []

    # Look for quoted prompts
    quoted = re.findall(r'"([^"]{20,500})"', text)
    prompts.extend(quoted)

    # Look for prompt: markers
    prompt_blocks = re.findall(r'(?:prompt|style|description):\s*(.{20,500}?)(?:\n\n|\n-|\Z)', text, re.IGNORECASE)
    prompts.extend(prompt_blocks)

    # Look for code blocks (often contain prompts)
    code_blocks = re.findall(r'```(.*?)```', text, re.DOTALL)
    for block in code_blocks:
        if len(block.strip()) > 20:
            prompts.append(block.strip())

    return prompts


def categorize_post(post):
    """Categorize a post by technique type."""
    text = (post.get("title", "") + " " + post.get("text", "")).lower()
    categories = []

    if any(w in text for w in ["character consistency", "consistent character", "same character"]):
        categories.append("character_consistency")
    if any(w in text for w in ["camera", "movement", "pan", "zoom", "dolly", "tracking"]):
        categories.append("camera_movement")
    if any(w in text for w in ["style", "aesthetic", "lighting", "mood", "cinematic"]):
        categories.append("style_lighting")
    if any(w in text for w in ["workflow", "pipeline", "step by step", "process"]):
        categories.append("workflow")
    if any(w in text for w in ["prompt", "prompting", "negative prompt", "prompt engineering"]):
        categories.append("prompting")
    if any(w in text for w in ["higgsfield", "cinema 2.5"]):
        categories.append("higgsfield")
    if any(w in text for w in ["reference", "ref image", "ip adapter", "controlnet"]):
        categories.append("reference_technique")

    return categories or ["general"]


def run(project_name="prompt-generator"):
    """Run the Reddit prompt scraper."""
    config = load_project_config(project_name)
    reddit_config = config["pipelines"]["reddit"]

    if not reddit_config.get("enabled"):
        print("[Reddit Prompts] Disabled, skipping.")
        return None

    token = get_apify_token(config)
    runner = ApifyRunner(token)
    output_dir = get_output_dir(config, "discovery")

    subreddits = reddit_config["subreddits"]
    urls = [f"https://www.reddit.com/r/{sub}/hot/" for sub in subreddits]

    print(f"\n{'='*60}")
    print(f"  Reddit Prompt Scraper -- {len(subreddits)} subreddits")
    print(f"{'='*60}")

    input_data = {
        "startUrls": [{"url": u} for u in urls],
        "maxItems": reddit_config.get("max_results", 30),
        "maxPostCount": reddit_config.get("max_results", 30),
        "sort": reddit_config.get("sort", "hot"),
    }

    try:
        items = runner.run_actor(
            reddit_config.get("actor", "trudax/reddit-scraper-lite"),
            input_data,
            timeout=180,
        )
    except Exception as e:
        print(f"  [ERROR] Scrape failed: {e}")
        return None

    # Filter for posts with prompt content
    prompt_posts = []
    for post in items:
        if has_prompt_content(post):
            title = post.get("title", "")
            text = (post.get("body", "") or post.get("selftext", "") or "")[:2000]
            subreddit = post.get("communityName", post.get("subreddit", ""))
            upvotes = post.get("upVotes", 0) or post.get("score", 0) or 0
            comments = post.get("numberOfComments", 0) or post.get("numComments", 0) or 0

            extracted_prompts = extract_prompts_from_text(title + "\n" + text)
            categories = categorize_post(post)

            prompt_posts.append({
                "title": title,
                "text": text[:1000],
                "subreddit": subreddit,
                "upvotes": upvotes,
                "comments": comments,
                "url": post.get("url", ""),
                "categories": categories,
                "extracted_prompts": extracted_prompts[:5],
                "created": post.get("createdAt", ""),
            })

    # Sort by upvotes
    prompt_posts.sort(key=lambda p: p.get("upvotes", 0), reverse=True)

    print(f"  {len(items)} total posts → {len(prompt_posts)} with prompt content")

    # Save results
    output = {
        "pipeline": "reddit-prompts",
        "project": project_name,
        "generated": now_iso(),
        "total_scraped": len(items),
        "prompt_posts": len(prompt_posts),
        "results": prompt_posts,
    }
    save_json(output_dir / "reddit_prompt_results.json", output)

    # Write Obsidian note
    _write_obsidian(prompt_posts, output_dir, project_name)

    # Print top 5
    print(f"\n  Top prompt posts:")
    for i, p in enumerate(prompt_posts[:5], 1):
        cats = ", ".join(p["categories"])
        print(f"  {i}. [{cats}] r/{p['subreddit']} ({p['upvotes']} upvotes)")
        print(f"     {p['title'][:80]}")
        if p["extracted_prompts"]:
            print(f"     Prompt: {p['extracted_prompts'][0][:80]}...")
    print()

    return output


def _write_obsidian(posts, output_dir, project):
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [
        "---",
        f"title: Reddit Prompt Research -- {today}",
        f"date: {today}",
        "tags:",
        "  - prompt-research/reddit",
        f"  - project/{project}",
        "---",
        "",
        f"# Reddit Prompt Research -- {today}",
        "",
        f"> [!info] {len(posts)} posts with prompt/technique content",
        "",
    ]

    for i, p in enumerate(posts[:15], 1):
        cats = ", ".join(f"`{c}`" for c in p["categories"])
        lines.append(f"### #{i} -- r/{p['subreddit']}")
        lines.append(f"**{p['title']}** ({p['upvotes']} upvotes, {p['comments']} comments)")
        lines.append(f"Categories: {cats}")
        lines.append("")
        if p.get("text"):
            lines.append(f"> [!quote] Post")
            lines.append(f"> {p['text'][:300]}")
            lines.append("")
        if p.get("extracted_prompts"):
            lines.append(f"> [!example] Extracted Prompts")
            for prompt in p["extracted_prompts"][:3]:
                lines.append(f"> `{prompt[:200]}`")
            lines.append("")
        if p.get("url"):
            lines.append(f"[View on Reddit]({p['url']})")
            lines.append("")

    md_path = output_dir / f"Reddit Prompt Research -- {today}.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  [Obsidian] Wrote {md_path.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reddit prompt scraper")
    parser.add_argument("--project", default="prompt-generator")
    args = parser.parse_args()
    run(args.project)
