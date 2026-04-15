"""
vawn_config.py — Shared config, paths, and helpers for the Vawn Research Company.
"""

import json
import sys
from datetime import date, datetime
from pathlib import Path

VAWN_DIR = Path(r"C:\Users\rdyal\Vawn")
VAWN_PICS = VAWN_DIR / "Vawn Pics"
RESEARCH_DIR = VAWN_DIR / "research"
EXPORTS_DIR = VAWN_DIR / "Social_Media_Exports"
CONFIG_FILE = VAWN_DIR / "config.json"
CREDS_FILE = VAWN_DIR / "credentials.json"

DAILY_BRIEF = RESEARCH_DIR / "daily_brief.json"
CONTENT_CALENDAR = RESEARCH_DIR / "content_calendar.json"
ENGAGEMENT_LOG = RESEARCH_DIR / "engagement_log.json"
METRICS_LOG = RESEARCH_DIR / "metrics_log.json"
RESEARCH_LOG = RESEARCH_DIR / "research_log.json"
NOTEBOOKLM_STATE = RESEARCH_DIR / "notebooklm_state.json"

CATALOG_HTML = Path(
    r"C:\Users\rdyal\AppData\Roaming\Claude\local-agent-mode-sessions"
    r"\0d5764c2-382f-48eb-875d-761cc921ef55"
    r"\c5698935-ad26-414c-9f36-80b1831d1e37"
    r"\local_7329a933-2b6e-4f75-b000-a7611d71b068"
    r"\outputs\vawn-catalog.html"
)

EXPORT_FOLDER = "Social_Media_Exports"  # single 1080×1920 (9:16) for all platforms

PILLAR_SCHEDULE = {
    0: "Awareness",
    1: "Lyric",
    2: "BTS",
    3: "Engagement",
    4: "Conversion",
    5: "Audience",
    6: "Video",
}

COMPARABLE_ARTISTS = ["JID", "6LACK", "Killer Mike", "Dreamville", "Baby Keem", "Smino", "Saba"]

VAWN_PROFILE = """Vawn is a Brooklyn-raised, Atlanta-based hip-hop artist. Wife and 1-year-old twin girls.
Sound: psychedelic boom bap, authoritative Atlanta trap, polished trap-soul, orchestral soul hip-hop. NO gospel.
Cadence: T.I. authority + J. Cole depth.
Thematic territories: Fear of Failure, Dependability, Love, Journey.
Brand: anti-hype, quiet authority, pattern recognition, long-game mentality, earned confidence.
11-track debut album in progress."""


def load_json(path):
    p = Path(path)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def save_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def get_anthropic_client():
    import anthropic
    config = load_json(CONFIG_FILE)
    return anthropic.Anthropic(api_key=config["anthropic_api_key"])


def log_run(agent_name, status, detail=""):
    log = load_json(RESEARCH_LOG)
    today = str(date.today())
    if today not in log:
        log[today] = []
    log[today].append({
        "agent": agent_name,
        "status": status,
        "detail": detail[:500],
        "time": datetime.now().isoformat(),
    })
    save_json(RESEARCH_LOG, log)


def today_str():
    return str(date.today())
