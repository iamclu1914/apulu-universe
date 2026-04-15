#!/usr/bin/env python3
"""
setup_company.py -- Create the Apulu Records company in Paperclip via REST API.

Usage:
    python scripts/paperclip/setup_company.py

Saves the company ID to scripts/paperclip/company_id.txt for use by subsequent scripts.
"""

import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

BASE_URL = "http://localhost:3100/api"
SCRIPT_DIR = Path(__file__).parent
COMPANY_ID_FILE = SCRIPT_DIR / "company_id.txt"

COMPANY_NAME = "Apulu Records"
COMPANY_PAYLOAD = {
    "name": COMPANY_NAME,
    "description": (
        "AI-powered record label. Departments: Marketing, Research, Production, "
        "Post-Production. Hub-and-spoke coordination via Chief of Staff agent. "
        "First artist: Vawn."
    ),
    "budgetMonthlyCents": 11600,
}


def api_get(path: str) -> dict:
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def api_post(path: str, payload: dict) -> dict:
    url = f"{BASE_URL}{path}"
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def find_existing_company(companies: list) -> dict | None:
    """Return the first company whose name matches COMPANY_NAME, or None."""
    for company in companies:
        if company.get("name") == COMPANY_NAME:
            return company
    return None


def main():
    print(f"Connecting to Paperclip at {BASE_URL} ...")

    # 1. Check if company already exists
    try:
        result = api_get("/companies")
    except urllib.error.URLError as exc:
        print(f"ERROR: Could not reach Paperclip API -- {exc}")
        print("Make sure Paperclip is running on port 3100.")
        sys.exit(1)

    # Handle both list response and {data: [...]} envelope
    companies = result if isinstance(result, list) else result.get("data", result.get("companies", []))

    existing = find_existing_company(companies)

    if existing:
        company_id = existing.get("id") or existing.get("_id")
        print(f"Company '{COMPANY_NAME}' already exists (id={company_id}). Skipping creation.")
    else:
        print(f"Creating company '{COMPANY_NAME}' ...")
        try:
            created = api_post("/companies", COMPANY_PAYLOAD)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode()
            print(f"ERROR: POST /api/companies returned {exc.code}: {body}")
            sys.exit(1)
        except urllib.error.URLError as exc:
            print(f"ERROR: {exc}")
            sys.exit(1)

        # Handle envelope or direct object
        company_data = created.get("data") or created.get("company") or created
        company_id = company_data.get("id") or company_data.get("_id")

        if not company_id:
            print(f"ERROR: Could not extract company ID from response: {json.dumps(created, indent=2)}")
            sys.exit(1)

        print(f"Company created successfully.")

    # 2. Save company ID
    COMPANY_ID_FILE.write_text(str(company_id))
    print(f"Company ID saved to: {COMPANY_ID_FILE}")
    print(f"  company_id = {company_id}")
    print("Done.")


if __name__ == "__main__":
    main()
