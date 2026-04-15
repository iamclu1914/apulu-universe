"""
youtube_prompt_research.py -- Deep-dives Higgsfield/AI video tutorials via YouTube + NotebookLM.
Uses the research-pipeline skill to search, auto-select, source, and analyze.

Usage:
    python youtube_prompt_research.py
    python youtube_prompt_research.py --topic "higgsfield character consistency"
    python youtube_prompt_research.py --topic "ai video camera movements" --deliverable report
"""

import argparse
import asyncio
import subprocess
import sys
from pathlib import Path

RESEARCH_PIPELINE = Path(r"C:\Users\rdyal\.claude\skills\research-pipeline\scripts\research_pipeline.py")
DEFAULT_OUTPUT = Path(r"C:\Users\rdyal\Apulu Universe\research\prompt-generator\discovery")


def run(topic=None, deliverable=None, instructions=None):
    """Run YouTube prompt research via the research-pipeline skill."""
    if not topic:
        topic = "Higgsfield Cinema 2.5 prompting tips character consistency"

    print(f"\n{'='*60}")
    print(f"  YouTube Prompt Research")
    print(f"  Topic: {topic}")
    print(f"{'='*60}")

    cmd = [
        sys.executable, str(RESEARCH_PIPELINE),
        topic,
        "--count", "8",
        "--months", "3",
        "--output-dir", str(DEFAULT_OUTPUT),
    ]

    if deliverable:
        cmd.extend(["--deliverable", deliverable])
    if instructions:
        cmd.extend(["--instructions", instructions])

    result = subprocess.run(cmd, timeout=600)
    return result.returncode == 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YouTube prompt research")
    parser.add_argument("--topic", type=str, help="Research topic")
    parser.add_argument("--deliverable", type=str, choices=[
        "audio", "report", "quiz", "slide-deck", "mind-map"
    ])
    parser.add_argument("--instructions", type=str)
    args = parser.parse_args()

    run(args.topic, args.deliverable, args.instructions)
