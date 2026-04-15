"""
run_prompt_research.py -- Orchestrator for the prompt research pipeline.
Runs the configured scrapers and ingests results into the prompt database.

Usage:
    python run_prompt_research.py                    # all scrapers
    python run_prompt_research.py --only reddit      # specific scraper
    python run_prompt_research.py --only video       # video quality only
    python run_prompt_research.py --youtube "topic"  # deep-dive via NotebookLM
"""

import argparse
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline_config import load_project_config, now_iso, today_str


def run(project_name="prompt-generator", only=None, youtube_topic=None):
    config = load_project_config(project_name)

    print(f"\n{'='*60}")
    print(f"  Prompt Research Pipeline")
    print(f"  Project: {project_name}")
    print(f"  Date: {today_str()}")
    print(f"{'='*60}")

    results = {}

    # Reddit prompt scraper
    if only in (None, "reddit"):
        print(f"\n{'─'*40}")
        print(f"  Reddit Prompt Scraper")
        print(f"{'─'*40}")
        try:
            from prompt_research.reddit_prompt_scraper import run as run_reddit
            run_reddit(project_name)
            results["reddit"] = "ok"
        except Exception as e:
            results["reddit"] = f"error: {e}"
            print(f"  [FAIL] {e}")
            traceback.print_exc()

    # Video quality scorer
    if only in (None, "video"):
        print(f"\n{'─'*40}")
        print(f"  Video Quality Scorer")
        print(f"{'─'*40}")
        try:
            from prompt_research.video_quality_scorer import run as run_video
            run_video(project_name)
            results["video"] = "ok"
        except Exception as e:
            results["video"] = f"error: {e}"
            print(f"  [FAIL] {e}")
            traceback.print_exc()

    # YouTube deep-dive (on-demand only)
    if youtube_topic:
        print(f"\n{'─'*40}")
        print(f"  YouTube Deep Dive: {youtube_topic}")
        print(f"{'─'*40}")
        try:
            from prompt_research.youtube_prompt_research import run as run_yt
            run_yt(youtube_topic)
            results["youtube"] = "ok"
        except Exception as e:
            results["youtube"] = f"error: {e}"
            print(f"  [FAIL] {e}")
            traceback.print_exc()

    # Ingest into prompt database
    print(f"\n{'─'*40}")
    print(f"  Ingest into Prompt DB")
    print(f"{'─'*40}")
    try:
        from prompt_research.prompt_db import ingest
        ingest(project_name)
        results["ingest"] = "ok"
    except Exception as e:
        results["ingest"] = f"error: {e}"
        print(f"  [FAIL] {e}")

    # Summary
    print(f"\n{'='*60}")
    print(f"  Prompt Research -- Summary")
    print(f"{'='*60}")
    for name, status in results.items():
        marker = "[OK]" if status == "ok" else "[FAIL]"
        print(f"  {marker} {name}")
    print(f"{'='*60}\n")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run prompt research pipeline")
    parser.add_argument("--project", default="prompt-generator")
    parser.add_argument("--only", choices=["reddit", "video"])
    parser.add_argument("--youtube", type=str, help="YouTube deep-dive topic")
    args = parser.parse_args()

    run(args.project, args.only, args.youtube)
