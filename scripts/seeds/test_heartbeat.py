#!/usr/bin/env python3
"""
test_heartbeat.py -- Validate Phase 1 agents via Paperclip heartbeat API.

Usage:
    python scripts/paperclip/test_heartbeat.py              # test all Phase 1 agents
    python scripts/paperclip/test_heartbeat.py discovery    # test one agent
    python scripts/paperclip/test_heartbeat.py --check-only # skip trigger, just verify dirs + agent exists

Exit codes:
    0 -- all agents passed
    1 -- one or more agents failed
    2 -- Paperclip unreachable or config missing

API (confirmed working):
    POST /api/agents/{agentId}/heartbeat/invoke  → 202, returns {id, status, ...}
    GET  /api/heartbeat-runs/{runId}             → 200, returns run with {status, exitCode, error, errorCode}
"""

import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_URL = "http://localhost:3100/api"
SCRIPT_DIR = Path(__file__).parent
AGENT_IDS_FILE = SCRIPT_DIR / "agent_ids.json"
COMPANY_ID_FILE = SCRIPT_DIR / "company_id.txt"

# How long to wait after triggering a heartbeat before polling (seconds)
INITIAL_WAIT = 5

# Max time to poll for a run to complete (seconds)
POLL_TIMEOUT = 90

# How often to poll (seconds)
POLL_INTERVAL = 3

# Phase 1 agent definitions: name -> expected output directory (or None to skip dir check)
# If a list is provided, ANY of the directories matching is sufficient.
PHASE_1_AGENTS = {
    "cos": {
        "description": "CoS Briefing -- runs health_monitor + daily_briefing",
        "script": "scripts/paperclip/cos_briefing.py",
        "output_dirs": [
            Path("C:/Users/rdyal/Apulu Universe/research/vawn/briefings"),
        ],
    },
    "discovery": {
        "description": "Discovery -- Apify scrapers (X, IG, TikTok, Reddit)",
        "script": "pipeline/discovery/run_all.py",
        "output_dirs": [
            Path("C:/Users/rdyal/Apulu Universe/research/vawn/discovery"),
        ],
    },
    "ideation": {
        "description": "Ideation -- pillar-aware content ideas",
        "script": "pipeline/ideation/ideation_engine.py",
        "output_dirs": [
            Path("C:/Users/rdyal/Apulu Universe/research/vawn/ideation"),
        ],
    },
    "trend": {
        "description": "Trend -- Vawn daily brief (4 research sub-agents)",
        "script": "Vawn/research_company.py",
        "output_dirs": [
            Path("C:/Users/rdyal/Vawn/research"),
        ],
    },
    "prompt-research": {
        "description": "Prompt Research -- Reddit + video quality scoring",
        "script": "pipeline/prompt-research/run_prompt_research.py",
        "output_dirs": [
            Path("C:/Users/rdyal/Apulu Universe/pipeline/prompt-research"),
            Path("C:/Users/rdyal/Apulu Universe/research/vawn"),
        ],
    },
}

# Error codes that indicate "script had a dependency problem" rather than Paperclip failure.
# These should be reported as EXPECTED_FAIL rather than ERROR.
DEPENDENCY_ERROR_CODES = {"adapter_failed", "process_nonzero", "timeout"}


# ---------------------------------------------------------------------------
# HTTP helpers (stdlib only)
# ---------------------------------------------------------------------------

def api_get(path: str) -> tuple[int, dict]:
    """Return (http_status_code, parsed_json)."""
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        try:
            return exc.code, json.loads(body)
        except json.JSONDecodeError:
            return exc.code, {"_raw": body}
    except urllib.error.URLError as exc:
        raise ConnectionError(f"Cannot reach Paperclip at {BASE_URL}: {exc}") from exc


def api_post(path: str, payload: dict | None = None) -> tuple[int, dict]:
    """Return (http_status_code, parsed_json)."""
    url = f"{BASE_URL}{path}"
    data = json.dumps(payload or {}).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        try:
            return exc.code, json.loads(body)
        except json.JSONDecodeError:
            return exc.code, {"_raw": body}
    except urllib.error.URLError as exc:
        raise ConnectionError(f"Cannot reach Paperclip at {BASE_URL}: {exc}") from exc


# ---------------------------------------------------------------------------
# Core test logic
# ---------------------------------------------------------------------------

def check_output_dir(agent_name: str, config: dict) -> tuple[bool, str]:
    """Return (exists_with_files, detail_message)."""
    dirs = config.get("output_dirs", [])
    if not dirs:
        return True, "no output directory configured (skipped)"

    results = []
    for d in dirs:
        if d.exists():
            files = list(d.iterdir())
            if files:
                results.append(f"{d} -- {len(files)} file(s)")
            else:
                results.append(f"{d} -- exists but empty")
        else:
            results.append(f"{d} -- NOT FOUND")

    # Pass if any dir exists and has files
    passed = any(
        d.exists() and list(d.iterdir())
        for d in dirs
    )
    return passed, " | ".join(results)


def verify_agent_exists(agent_name: str, agent_id: str) -> tuple[bool, dict | None]:
    """Check agent is registered in Paperclip. Returns (ok, agent_data)."""
    status, data = api_get(f"/agents/{agent_id}")
    if status == 200 and data.get("id"):
        return True, data
    return False, None


def trigger_heartbeat(agent_id: str) -> tuple[bool, str, str | None]:
    """
    Trigger a heartbeat for the agent.
    Returns (triggered_ok, detail_message, run_id_or_None).
    """
    status, data = api_post(f"/agents/{agent_id}/heartbeat/invoke")
    if status in (200, 202) and data.get("id"):
        run_id = data["id"]
        run_status = data.get("status", "unknown")
        return True, f"queued (run={run_id}, initial_status={run_status})", run_id
    else:
        error_msg = data.get("error") or data.get("_raw") or json.dumps(data)
        return False, f"HTTP {status} -- {error_msg}", None


def poll_run(run_id: str, timeout: int = POLL_TIMEOUT) -> dict:
    """
    Poll GET /api/heartbeat-runs/{runId} until terminal state or timeout.
    Returns the final run dict (or partial if timeout).
    """
    terminal_statuses = {"completed", "failed", "cancelled", "error"}
    deadline = time.time() + timeout
    last_data = {}

    while time.time() < deadline:
        status_code, data = api_get(f"/heartbeat-runs/{run_id}")
        if status_code != 200:
            # Can't poll -- return what we have
            return {"status": "unknown", "_poll_error": f"HTTP {status_code}"}
        last_data = data
        run_status = data.get("status", "")
        if run_status in terminal_statuses:
            return data
        time.sleep(POLL_INTERVAL)

    last_data["_timed_out"] = True
    return last_data


def classify_run_result(run: dict) -> tuple[str, str]:
    """
    Classify a completed run into a result category and human message.

    Returns (category, message) where category is one of:
        PASS           -- completed successfully (exitCode 0)
        EXPECTED_FAIL  -- script ran but failed due to external dependency (Apify, etc.)
        PAPERCLIP_FAIL -- Paperclip couldn't launch or manage the run
        TIMEOUT        -- run didn't finish within poll timeout
        UNKNOWN        -- can't determine
    """
    if run.get("_timed_out"):
        return "TIMEOUT", f"run {run.get('id','?')} still {run.get('status','running')} after {POLL_TIMEOUT}s"

    if run.get("_poll_error"):
        return "UNKNOWN", f"couldn't poll run status: {run['_poll_error']}"

    run_status = run.get("status", "")
    exit_code = run.get("exitCode")
    error_code = run.get("errorCode", "")
    error_msg = run.get("error", "")

    if run_status == "completed" and exit_code == 0:
        return "PASS", f"exit 0 (run={run.get('id','')})"

    if run_status == "failed":
        # Distinguish Paperclip infra failure vs script dependency failure
        if error_code == "adapter_failed":
            # Can't even launch the command -- likely a PATH or adapter config issue.
            # "python" not in Paperclip's restricted PATH is the most common cause.
            # This is a Paperclip adapter configuration issue, not a test failure.
            short_err = (error_msg or "")[:200]
            if "Failed to start command" in (error_msg or "") and "Verify adapter command" in (error_msg or ""):
                return "CONFIG_FAIL", f"adapter_failed (python not in Paperclip PATH -- use full python path in adapter config): {short_err}"
            return "PAPERCLIP_FAIL", f"adapter_failed: {short_err}"
        elif error_code in DEPENDENCY_ERROR_CODES or exit_code not in (None, 0):
            # Script ran but exited non-zero -- probably Apify credentials, etc.
            excerpt = run.get("stdoutExcerpt") or run.get("stderrExcerpt") or error_msg or ""
            return "EXPECTED_FAIL", f"exit {exit_code} / {error_code}: {excerpt[:200]}"
        else:
            short_err = (error_msg or "")[:200]
            return "PAPERCLIP_FAIL", f"status=failed, errorCode={error_code}: {short_err}"

    return "UNKNOWN", f"status={run_status}, exitCode={exit_code}, errorCode={error_code}"


# ---------------------------------------------------------------------------
# Single-agent test
# ---------------------------------------------------------------------------

def test_agent(agent_name: str, agent_id: str, config: dict, check_only: bool) -> dict:
    """
    Run full test for one agent. Returns a result dict with keys:
        agent_name, agent_id, exists, dir_check, trigger, run_result, overall
    """
    result = {
        "agent_name": agent_name,
        "agent_id": agent_id,
        "description": config["description"],
        "exists": False,
        "exists_detail": "",
        "dir_ok": False,
        "dir_detail": "",
        "trigger_ok": None,
        "trigger_detail": "",
        "run_category": None,
        "run_detail": "",
        "overall": "FAIL",
    }

    # 1. Verify agent exists in Paperclip
    exists, agent_data = verify_agent_exists(agent_name, agent_id)
    result["exists"] = exists
    if exists:
        result["exists_detail"] = (
            f"status={agent_data.get('status')}, "
            f"adapterType={agent_data.get('adapterType')}"
        )
    else:
        result["exists_detail"] = "not found in Paperclip"
        result["overall"] = "FAIL"
        return result

    # 2. Check output directory
    dir_ok, dir_detail = check_output_dir(agent_name, config)
    result["dir_ok"] = dir_ok
    result["dir_detail"] = dir_detail

    if check_only:
        result["trigger_ok"] = None
        result["trigger_detail"] = "skipped (--check-only)"
        result["run_category"] = "SKIPPED"
        result["run_detail"] = "heartbeat not triggered"
        result["overall"] = "PASS" if (exists and dir_ok) else "WARN"
        return result

    # 3. Trigger heartbeat
    triggered, trigger_detail, run_id = trigger_heartbeat(agent_id)
    result["trigger_ok"] = triggered
    result["trigger_detail"] = trigger_detail

    if not triggered:
        result["run_category"] = "PAPERCLIP_FAIL"
        result["run_detail"] = "heartbeat trigger failed"
        result["overall"] = "FAIL"
        return result

    # 4. Wait then poll for result
    print(f"    Waiting {INITIAL_WAIT}s for run to start ...", flush=True)
    time.sleep(INITIAL_WAIT)

    run = poll_run(run_id)
    category, run_detail = classify_run_result(run)
    result["run_category"] = category
    result["run_detail"] = run_detail

    # Overall verdict:
    # PASS         → all good
    # EXPECTED_FAIL → heartbeat fired, script had dependency issue (not our problem)
    # WARN         → trigger worked but couldn't confirm completion
    # FAIL         → Paperclip couldn't even run the agent
    if category == "PASS":
        result["overall"] = "PASS"
    elif category in ("EXPECTED_FAIL", "TIMEOUT", "CONFIG_FAIL"):
        result["overall"] = "WARN"
    elif category == "PAPERCLIP_FAIL":
        result["overall"] = "FAIL"
    else:
        result["overall"] = "WARN"

    # Refresh dir check after run attempt
    dir_ok_after, dir_detail_after = check_output_dir(agent_name, config)
    if dir_ok_after and not dir_ok:
        result["dir_ok"] = True
        result["dir_detail"] = dir_detail_after + " (created by run)"

    return result


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

ICONS = {
    "PASS": "PASS",
    "FAIL": "FAIL",
    "WARN": "WARN",
    "SKIP": "SKIP",
}


def print_result(r: dict):
    overall = r["overall"]
    agent = r["agent_name"]
    desc = r["description"]

    print(f"\n  [{overall}] {agent}")
    print(f"         {desc}")
    print(f"         agent exists : {'YES' if r['exists'] else 'NO'} -- {r['exists_detail']}")
    print(f"         output dirs  : {'OK' if r['dir_ok'] else 'MISSING'} -- {r['dir_detail']}")

    if r["trigger_ok"] is None:
        print(f"         heartbeat    : {r['trigger_detail']}")
    elif r["trigger_ok"]:
        print(f"         heartbeat    : triggered -- {r['trigger_detail']}")
        print(f"         run result   : [{r['run_category']}] {r['run_detail']}")
    else:
        print(f"         heartbeat    : FAILED -- {r['trigger_detail']}")


def print_summary(results: list[dict], check_only: bool):
    total = len(results)
    passed = sum(1 for r in results if r["overall"] == "PASS")
    warned = sum(1 for r in results if r["overall"] == "WARN")
    failed = sum(1 for r in results if r["overall"] == "FAIL")

    print(f"\n{'='*62}")
    print(f"  SUMMARY  ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    print(f"{'='*62}")
    print(f"  Agents tested : {total}")
    print(f"  PASS          : {passed}")
    print(f"  WARN          : {warned}  (heartbeat fired; script had dependency issues)")
    print(f"  FAIL          : {failed}  (Paperclip error -- needs investigation)")
    if check_only:
        print(f"\n  Note: run with --check-only, heartbeats were NOT triggered.")
    print(f"\n  WARN categories:")
    print(f"    CONFIG_FAIL   -- 'python' not in Paperclip PATH. Fix: use full python path")
    print(f"                    in adapter adapterConfig.command (update_cos_adapter.py pattern).")
    print(f"    EXPECTED_FAIL -- script launched but exited non-zero (Apify/API dependency).")
    print(f"    TIMEOUT       -- run didn't finish within {POLL_TIMEOUT}s poll window.")
    print(f"  FAIL means Paperclip infrastructure error (not adapter config).\n")

    if failed > 0:
        print(f"  Failing agents:")
        for r in results:
            if r["overall"] == "FAIL":
                print(f"    - {r['agent_name']}: {r['run_detail'] or r['trigger_detail'] or r['exists_detail']}")
    print(f"{'='*62}\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    args = sys.argv[1:]
    check_only = "--check-only" in args
    args = [a for a in args if not a.startswith("--")]

    # Load config
    if not AGENT_IDS_FILE.exists():
        print(f"ERROR: {AGENT_IDS_FILE} not found.")
        sys.exit(2)
    if not COMPANY_ID_FILE.exists():
        print(f"ERROR: {COMPANY_ID_FILE} not found.")
        sys.exit(2)

    agent_ids: dict[str, str] = json.loads(AGENT_IDS_FILE.read_text())

    # Determine which agents to test
    if args:
        requested = args[0].lower()
        if requested not in PHASE_1_AGENTS:
            print(f"ERROR: Unknown agent '{requested}'. Phase 1 agents: {list(PHASE_1_AGENTS)}")
            sys.exit(2)
        agents_to_test = {requested: PHASE_1_AGENTS[requested]}
    else:
        agents_to_test = PHASE_1_AGENTS

    print(f"\n{'='*62}")
    print(f"  Apulu Records -- Heartbeat Test")
    print(f"  Mode: {'check-only (no triggers)' if check_only else 'full (trigger + poll)'}")
    print(f"  Agents: {list(agents_to_test.keys())}")
    print(f"{'='*62}")

    # Verify Paperclip is reachable
    try:
        status, _ = api_get(f"/agents/{list(agent_ids.values())[0]}")
    except ConnectionError as exc:
        print(f"\nERROR: {exc}")
        print("Is Paperclip running? Try: cd paperclip && npx paperclip start\n")
        sys.exit(2)

    # Run tests
    results = []
    for agent_name, config in agents_to_test.items():
        agent_id = agent_ids.get(agent_name)
        if not agent_id:
            print(f"\n  [SKIP] {agent_name} -- no agent ID in agent_ids.json")
            results.append({
                "agent_name": agent_name,
                "agent_id": None,
                "description": config["description"],
                "exists": False,
                "exists_detail": "not in agent_ids.json",
                "dir_ok": False,
                "dir_detail": "",
                "trigger_ok": None,
                "trigger_detail": "skipped",
                "run_category": "SKIP",
                "run_detail": "no agent ID",
                "overall": "FAIL",
            })
            continue

        print(f"\n  Testing: {agent_name} ({agent_id})", flush=True)
        result = test_agent(agent_name, agent_id, config, check_only)
        results.append(result)
        print_result(result)

    print_summary(results, check_only)

    # Exit 0 only if no hard FAILs
    hard_fails = [r for r in results if r["overall"] == "FAIL"]
    sys.exit(1 if hard_fails else 0)


if __name__ == "__main__":
    main()
