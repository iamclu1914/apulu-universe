"""
update_cos_adapter.py -- Patch the CoS agent in Paperclip to use the process adapter.

Reads the CoS agent ID from agent_ids.json and PATCHes it via the Paperclip API.

Usage:
    python scripts/paperclip/update_cos_adapter.py
"""

import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

PAPERCLIP_BASE = "http://localhost:3100"
SCRIPTS_DIR = Path(__file__).resolve().parent

COS_COMMAND = r"python C:\Users\rdyal\Apulu Universe\scripts\paperclip\cos_briefing.py"
COS_CWD = r"C:\Users\rdyal\Apulu Universe"
COS_TIMEOUT_SEC = 300


def load_agent_ids():
    path = SCRIPTS_DIR / "agent_ids.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def patch_agent(agent_id: str, payload: dict) -> dict:
    url = f"{PAPERCLIP_BASE}/api/agents/{agent_id}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="PATCH",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    agent_ids = load_agent_ids()
    cos_id = agent_ids.get("cos")
    if not cos_id:
        print("ERROR: 'cos' key not found in agent_ids.json", file=sys.stderr)
        sys.exit(1)

    print(f"CoS agent ID: {cos_id}")
    print("Patching adapter -> process")

    payload = {
        "adapterType": "process",
        "adapterConfig": {
            "command": COS_COMMAND,
            "cwd": COS_CWD,
            "timeoutSec": COS_TIMEOUT_SEC,
        },
    }

    try:
        result = patch_agent(cos_id, payload)
        print("PATCH response:")
        print(json.dumps(result, indent=2))
        print("\nCoS agent adapter updated successfully.")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"HTTP {e.code} error: {body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Connection error -- is Paperclip running at {PAPERCLIP_BASE}? {e.reason}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
