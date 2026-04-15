"""
pipeline_config.py -- Shared config loader for the Apulu Universe content pipeline.
Loads project-specific config (e.g., vawn.json) and provides common helpers.
"""

import json
import sys
from datetime import date, datetime
from pathlib import Path

PIPELINE_DIR = Path(r"C:\Users\rdyal\Apulu Universe\pipeline")
CONFIG_DIR = PIPELINE_DIR / "config"
DISCOVERY_DIR = PIPELINE_DIR / "discovery"


def load_project_config(project_name="vawn"):
    """Load a project config from config/<project>.json."""
    config_path = CONFIG_DIR / f"{project_name}.json"
    if not config_path.exists():
        raise FileNotFoundError(f"Project config not found: {config_path}")
    return json.loads(config_path.read_text(encoding="utf-8"))


def get_credentials(project_config):
    """Load API credentials from the project's config_path."""
    creds_path = Path(project_config["config_path"])
    if not creds_path.exists():
        raise FileNotFoundError(f"Credentials not found: {creds_path}")
    return json.loads(creds_path.read_text(encoding="utf-8"))


def get_apify_token(project_config):
    """Get Apify API token from project credentials."""
    creds = get_credentials(project_config)
    token = creds.get("apify_api_token")
    if not token:
        raise ValueError("apify_api_token not found in credentials")
    return token


def get_anthropic_client(project_config):
    """Get Anthropic client from project credentials."""
    import anthropic
    creds = get_credentials(project_config)
    return anthropic.Anthropic(api_key=creds["anthropic_api_key"])


def get_output_dir(project_config, phase=None):
    """Get the output directory for pipeline results.

    Args:
        project_config: Project config dict
        phase: Optional phase subfolder (discovery, ideation, scripting, cascade)
    """
    out = Path(project_config["output_dir"])
    if phase:
        out = out / phase
    out.mkdir(parents=True, exist_ok=True)
    return out


def save_json(path, data):
    """Write JSON with datetime serialization."""
    Path(path).write_text(
        json.dumps(data, indent=2, default=str, ensure_ascii=False),
        encoding="utf-8",
    )


def load_json(path):
    """Load JSON file, return empty dict if missing."""
    p = Path(path)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def today_str():
    return str(date.today())


def now_iso():
    return datetime.now().isoformat()
