"""
run_all.py -- Master orchestrator for all discovery pipelines.
Runs enabled pipelines in sequence and produces a unified daily brief.

Usage:
    python run_all.py                          # all pipelines, vawn project
    python run_all.py --project vawn
    python run_all.py --only x,tiktok          # specific pipelines only
    python run_all.py --skip youtube            # skip specific pipelines
    python run_all.py --no-notebooklm          # skip NotebookLM for YouTube
"""

import argparse
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline_config import (
    load_project_config, get_output_dir,
    save_json, load_json, now_iso, today_str,
)
from obsidian_formatter import write_obsidian_note
from discovery.apify_client import ApifyBillingExhaustedError


# Pipelines that depend on Apify and should short-circuit when the monthly cap is hit.
APIFY_BACKED_PIPELINES = {"x", "instagram", "tiktok"}

# Distinct exit code so WTS / paperclip_run_monitor can classify billing-cap failures
# without false-flagging them as transient backend errors.
EXIT_APIFY_BILLING_EXHAUSTED = 4


def run(project_name="vawn", only=None, skip=None, use_notebooklm=True):
    """Run all enabled discovery pipelines."""
    config = load_project_config(project_name)
    output_dir = get_output_dir(config, "discovery")

    pipelines = {
        "x": ("discovery.x_pipeline", "run"),
        "instagram": ("discovery.instagram_pipeline", "run"),
        "tiktok": ("discovery.tiktok_pipeline", "run"),
        "reddit": ("discovery.reddit_pipeline", "run"),
        "youtube": ("discovery.youtube_pipeline", "run"),
    }

    # Filter pipelines
    if only:
        selected = [p.strip() for p in only.split(",")]
        pipelines = {k: v for k, v in pipelines.items() if k in selected}
    if skip:
        skipped = [p.strip() for p in skip.split(",")]
        pipelines = {k: v for k, v in pipelines.items() if k not in skipped}

    print(f"\n{'='*60}")
    print(f"  Apulu Universe -- Discovery Pipeline")
    print(f"  Project: {project_name}")
    print(f"  Date: {today_str()}")
    print(f"  Pipelines: {', '.join(pipelines.keys())}")
    print(f"{'='*60}")

    results = {}
    errors = {}
    apify_billing_exhausted = False

    for name, (module_path, func_name) in pipelines.items():
        print(f"\n{'-'*40}")
        print(f"  Running: {name}")
        print(f"{'-'*40}")

        if apify_billing_exhausted and name in APIFY_BACKED_PIPELINES:
            msg = "Apify monthly usage hard limit exceeded -- skipping (raise cap in Apify console or wait for cycle reset)"
            results[name] = {"status": "skipped", "error": msg}
            errors[name] = msg
            print(f"  [SKIP] {name}: {msg}")
            continue

        try:
            mod = __import__(module_path, fromlist=[func_name])
            run_fn = getattr(mod, func_name)

            if name == "youtube":
                result = run_fn(project_name, use_notebooklm=use_notebooklm)
            elif name in ("x", "instagram", "tiktok"):
                result = run_fn(project_name)
            else:
                result = run_fn(project_name)

            results[name] = {
                "status": "ok",
                "total": result.get(f"total_{'tweets' if name == 'x' else 'posts' if name in ('instagram', 'reddit') else 'videos'}", 0) if result else 0,
            }

            # Write Obsidian note for this pipeline
            if result:
                try:
                    write_obsidian_note(name, result, output_dir, project_name)
                except Exception as obs_err:
                    print(f"  [WARN] Obsidian note failed: {obs_err}")

            print(f"  [OK] {name}")

        except ApifyBillingExhaustedError as e:
            apify_billing_exhausted = True
            results[name] = {"status": "billing_exhausted", "error": str(e)}
            errors[name] = f"apify_billing_exhausted: {e}"
            print(f"  [BILLING] {name}: Apify monthly cap hit -- {e}")
            print(f"  [BILLING] Short-circuiting remaining Apify-backed pipelines: {sorted(APIFY_BACKED_PIPELINES)}")

        except Exception as e:
            results[name] = {"status": "error", "error": str(e)}
            errors[name] = str(e)
            print(f"  [FAIL] {name}: {e}")
            traceback.print_exc()

    # Build unified daily brief
    brief = {
        "project": project_name,
        "generated": now_iso(),
        "pipelines": results,
        "errors": errors,
    }

    # Merge top results from each pipeline into brief
    top_content = []
    for name in pipelines:
        pipeline_file = output_dir / f"{name.replace('/', '_')}_pipeline_results.json"
        if pipeline_file.exists():
            import json
            data = json.loads(pipeline_file.read_text(encoding="utf-8"))
            for item in data.get("top_20", [])[:5]:
                item["_pipeline"] = name
                top_content.append(item)

    brief["top_content"] = top_content
    brief["apify_billing_exhausted"] = apify_billing_exhausted
    brief_path = output_dir / "discovery_brief.json"
    save_json(brief_path, brief)

    # Write unified Obsidian brief note
    try:
        write_obsidian_note("brief", brief, output_dir, project_name)
    except Exception as obs_err:
        print(f"  [WARN] Obsidian brief note failed: {obs_err}")

    # Summary
    print(f"\n{'='*60}")
    print(f"  Discovery Pipeline -- Summary")
    print(f"{'='*60}")
    MARKERS = {"ok": "[OK]", "error": "[FAIL]", "billing_exhausted": "[BILLING]", "skipped": "[SKIP]"}
    for name, result in results.items():
        status = result["status"]
        marker = MARKERS.get(status, "[FAIL]")
        count = result.get("total", "?")
        err = f" -- {result.get('error', '')[:80]}" if status not in ("ok",) else ""
        print(f"  {marker} {name}: {count} items{err}")
    print(f"\n  Brief saved to: {brief_path}")
    print(f"{'='*60}\n")

    return brief


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run all discovery pipelines")
    parser.add_argument("--project", default="vawn", help="Project config to use")
    parser.add_argument("--only", type=str, help="Comma-separated pipelines to run")
    parser.add_argument("--skip", type=str, help="Comma-separated pipelines to skip")
    parser.add_argument("--no-notebooklm", action="store_true", help="Skip NotebookLM for YouTube")
    args = parser.parse_args()

    brief = run(args.project, args.only, args.skip, not args.no_notebooklm)
    if brief.get("apify_billing_exhausted"):
        sys.exit(EXIT_APIFY_BILLING_EXHAUSTED)
