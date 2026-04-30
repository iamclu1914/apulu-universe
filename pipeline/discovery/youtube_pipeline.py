"""
youtube_pipeline.py -- YouTube discovery pipeline.
Uses yt-dlp (via youtube-search skill script) to find videos,
then optionally feeds top results into NotebookLM for deep analysis.

Usage:
    python youtube_pipeline.py                      # uses vawn config
    python youtube_pipeline.py --project vawn
    python youtube_pipeline.py --no-notebooklm      # skip NotebookLM sourcing
    python youtube_pipeline.py --analyze-only NB_ID  # analyze existing notebook
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline_config import (
    load_project_config, get_output_dir,
    save_json, today_str, now_iso,
)

YT_SEARCH_SCRIPT = Path(r"C:\Users\rdyal\.claude\skills\youtube-search\scripts\youtube_search.py")


def search_youtube(keyword, count=10, months=3):
    """Run youtube_search.py and return structured results."""
    cmd = [
        sys.executable, str(YT_SEARCH_SCRIPT),
        keyword,
        "--count", str(count),
        "--months", str(months),
        "--json",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        # JSON is on stdout, status messages on stderr
        if result.stdout.strip():
            return json.loads(result.stdout)
        return []
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        print(f"  [ERROR] yt-dlp search failed for '{keyword}': {e}")
        return []


def source_to_notebooklm(urls, notebook_title=None):
    """Create a NotebookLM notebook and add video URLs as sources.

    Returns notebook_id if successful, None otherwise.
    """
    try:
        import asyncio

        async def _source():
            from notebooklm import NotebookLMClient

            async with await NotebookLMClient.from_storage() as client:
                title = notebook_title or f"YT Research {today_str()}"
                nb = await client.notebooks.create(title)
                print(f"  [NotebookLM] Created notebook: {nb.title} ({nb.id[:8]}...)")

                for i, url in enumerate(urls[:10]):  # NotebookLM max ~50 sources
                    try:
                        src = await client.sources.add_url(nb.id, url, wait=True, wait_timeout=90)
                        print(f"  [NotebookLM] Added source {i+1}/{len(urls[:10])}: {src.title or url[:50]}")
                    except Exception as e:
                        print(f"  [NotebookLM] Failed to add {url[:50]}: {e}")

                # Get AI summary
                desc = await client.notebooks.get_description(nb.id)
                return {
                    "notebook_id": nb.id,
                    "title": nb.title,
                    "summary": desc.summary,
                    "suggested_topics": [
                        {"question": t.question, "prompt": t.prompt}
                        for t in desc.suggested_topics
                    ],
                }

        return asyncio.run(_source())
    except Exception as e:
        print(f"  [ERROR] NotebookLM integration failed: {e}")
        return None


def run(project_name="vawn", use_notebooklm=True, analyze_notebook_id=None):
    """Run the YouTube discovery pipeline."""
    config = load_project_config(project_name)
    yt_config = config["pipelines"]["youtube"]

    if not yt_config.get("enabled"):
        print("[YT Pipeline] Disabled in config, skipping.")
        return None

    output_dir = get_output_dir(config, "discovery")
    all_results = []

    # Search each keyword
    for keyword in yt_config["keywords"]:
        print(f"\n[YT Pipeline] Searching: {keyword}")
        videos = search_youtube(
            keyword,
            count=yt_config.get("max_results", 20),
            months=yt_config.get("months", 3),
        )
        for v in videos:
            v["search_keyword"] = keyword
        all_results.extend(videos)
        print(f"  Found {len(videos)} videos")

    # Deduplicate by URL
    seen = set()
    unique = []
    for v in all_results:
        url = v.get("url", "")
        if url and url not in seen:
            seen.add(url)
            unique.append(v)
    all_results = unique

    # Sort by engagement ratio (views/subscribers)
    all_results.sort(key=lambda v: v.get("engagement_ratio") or 0, reverse=True)

    print(f"\n[YT Pipeline] {len(all_results)} unique videos total")

    # NotebookLM integration
    notebooklm_data = None
    if use_notebooklm and all_results:
        top_urls = [v["url"] for v in all_results[:10] if v.get("url")]
        if top_urls:
            print(f"\n[YT Pipeline] Sourcing top {len(top_urls)} videos into NotebookLM...")
            notebooklm_data = source_to_notebooklm(
                top_urls,
                notebook_title=f"YT Research: {config['project']} -- {today_str()}",
            )

    output = {
        "pipeline": "youtube",
        "project": project_name,
        "generated": now_iso(),
        "total_videos": len(all_results),
        "top_20": all_results[:20],
        "all_results": all_results,
        "notebooklm": notebooklm_data,
    }

    output_path = output_dir / "yt_pipeline_results.json"
    save_json(output_path, output)
    print(f"\n[YT Pipeline] Saved {len(all_results)} videos to {output_path}")

    # Print top 5
    print(f"\n{'='*60}")
    print(f"  YouTube Pipeline -- Top 5 ({today_str()})")
    print(f"{'='*60}")
    for i, v in enumerate(all_results[:5], 1):
        eng = v.get("engagement_ratio")
        eng_str = f"{eng:.1f}%" if eng else "N/A"
        subs = v.get("subscribers")
        subs_str = f"{subs:,}" if subs else "N/A"
        views = v.get("views")
        views_str = f"{views:,}" if views else "N/A"
        print(f"\n  #{i}  {v.get('title', 'Unknown')}")
        print(f"  Channel: {v.get('channel', '?')} ({subs_str} subs)")
        print(f"  Views: {views_str} | Engagement: {eng_str}")
        print(f"  {v.get('url', '')}")
    print(f"\n{'='*60}")

    if notebooklm_data:
        print(f"\n  NotebookLM notebook: {notebooklm_data.get('notebook_id', 'N/A')}")
        if notebooklm_data.get("summary"):
            print(f"  Summary: {notebooklm_data['summary'][:200]}...")
    print()

    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YouTube discovery pipeline")
    parser.add_argument("--project", default="vawn", help="Project config to use")
    parser.add_argument("--no-notebooklm", action="store_true", help="Skip NotebookLM sourcing")
    parser.add_argument("--analyze-only", type=str, help="Analyze existing notebook by ID")
    args = parser.parse_args()

    run(args.project, use_notebooklm=not args.no_notebooklm)
