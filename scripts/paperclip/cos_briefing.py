"""
cos_briefing.py -- CoS Agent wrapper for daily health check + briefing.

Runs health_monitor.py then daily_briefing.py, logs results to a dated JSON,
and exits 0 if both succeed or 1 if either fails.

Usage:
    python scripts/paperclip/cos_briefing.py
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

UNIVERSE_DIR = Path(r"C:\Users\rdyal\Apulu Universe")
BRIEFINGS_DIR = UNIVERSE_DIR / "research" / "vawn" / "briefings"
BRAIN_DIR = UNIVERSE_DIR / "pipeline" / "brain"

SCRIPTS = [
    {
        "name": "health_monitor",
        "path": BRAIN_DIR / "health_monitor.py",
        "label": "Health Monitor",
    },
    {
        "name": "daily_briefing",
        "path": BRAIN_DIR / "daily_briefing.py",
        "label": "Daily Briefing",
    },
]

TIMEOUT_SECONDS = 120


def run_script(script: dict) -> dict:
    """Run a single brain script and return a result record."""
    start = datetime.now()
    result = {
        "name": script["name"],
        "label": script["label"],
        "path": str(script["path"]),
        "started": start.isoformat(),
        "stdout": "",
        "stderr": "",
        "returncode": None,
        "success": False,
        "error": None,
    }

    print(f"\n[CoS] Running: {script['label']} ...")

    try:
        proc = subprocess.run(
            [sys.executable, str(script["path"])],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            cwd=str(script["path"].parent),
        )
        result["returncode"] = proc.returncode
        result["stdout"] = proc.stdout
        result["stderr"] = proc.stderr
        result["success"] = proc.returncode == 0

        if proc.stdout:
            print(proc.stdout, end="")
        if proc.stderr:
            print(proc.stderr, end="", file=sys.stderr)

        status = "PASS" if result["success"] else "FAIL"
        print(f"[CoS] {script['label']}: {status} (exit {proc.returncode})")

    except subprocess.TimeoutExpired as e:
        result["error"] = f"Timed out after {TIMEOUT_SECONDS}s"
        result["success"] = False
        print(f"[CoS] {script['label']}: TIMEOUT -- {result['error']}", file=sys.stderr)

    except Exception as e:
        result["error"] = str(e)
        result["success"] = False
        print(f"[CoS] {script['label']}: ERROR -- {result['error']}", file=sys.stderr)

    result["elapsed_seconds"] = round(
        (datetime.now() - start).total_seconds(), 2
    )
    result["finished"] = datetime.now().isoformat()
    return result


def main():
    run_start = datetime.now()
    today = run_start.strftime("%Y-%m-%d")

    print(f"\n{'='*60}")
    print(f"  CoS Briefing Agent -- {today}")
    print(f"{'='*60}")

    BRIEFINGS_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    for script in SCRIPTS:
        results.append(run_script(script))

    # Summary
    passed = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    overall_success = len(failed) == 0

    print(f"\n{'='*60}")
    print(f"  Summary: {len(passed)}/{len(results)} passed")
    for r in results:
        marker = "PASS" if r["success"] else "FAIL"
        print(f"  [{marker}] {r['label']} ({r['elapsed_seconds']}s)")
    if failed:
        print(f"\n  Failed scripts:")
        for r in failed:
            detail = r.get("error") or r.get("stderr", "")[:200] or "(no detail)"
            print(f"    - {r['label']}: {detail}")
    print(f"{'='*60}\n")

    # Write dated log
    log = {
        "date": today,
        "generated": run_start.isoformat(),
        "overall_success": overall_success,
        "passed": len(passed),
        "failed": len(failed),
        "total": len(results),
        "elapsed_seconds": round((datetime.now() - run_start).total_seconds(), 2),
        "scripts": results,
    }

    log_path = BRIEFINGS_DIR / f"cos_log_{today}.json"
    log_path.write_text(json.dumps(log, indent=2, default=str), encoding="utf-8")
    print(f"[CoS] Log written: {log_path}")

    sys.exit(0 if overall_success else 1)


if __name__ == "__main__":
    main()
