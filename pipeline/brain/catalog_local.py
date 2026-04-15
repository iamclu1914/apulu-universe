"""
catalog_local.py -- Extracts Vawn's lyrics catalog from HTML into structured JSON.
Provides local lyric lookup so the system doesn't depend on NotebookLM for basic bar selection.

Usage:
    python catalog_local.py extract     # Parse HTML → lyrics.json
    python catalog_local.py search "bar fragment"
    python catalog_local.py random      # Random quotable bar
    python catalog_local.py match "fear of failure"  # Bars matching a territory/theme
"""

import argparse
import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

CATALOG_HTML = Path(
    r"C:\Users\rdyal\AppData\Roaming\Claude\local-agent-mode-sessions"
    r"\0d5764c2-382f-48eb-875d-761cc921ef55"
    r"\c5698935-ad26-414c-9f36-80b1831d1e37"
    r"\local_7329a933-2b6e-4f75-b000-a7611d71b068"
    r"\outputs\vawn-catalog.html"
)
LYRICS_JSON = Path(r"C:\Users\rdyal\Apulu Universe\research\vawn\catalog\lyrics.json")


def extract_catalog():
    """Parse the HTML catalog into structured JSON."""
    if not CATALOG_HTML.exists():
        print(f"[ERROR] Catalog HTML not found: {CATALOG_HTML}")
        return None

    html = CATALOG_HTML.read_text(encoding="utf-8")

    # Extract tracks: each track is in a section with class "track"
    tracks = []

    # Find track cards (each has data-territory attribute)
    card_matches = list(re.finditer(r'class="track-card"\s+data-territory="([^"]*)"', html))
    title_matches = list(re.finditer(r'class="track-title"[^>]*>([^<]+)<', html))

    for i, title_match in enumerate(title_matches):
        track_name = title_match.group(1).strip()

        # Get territory from the card's data-territory attribute
        territory = ""
        if i < len(card_matches):
            raw_territory = card_matches[i].group(1).strip()
            # Map short codes to full names
            terr_map = {"fear": "Fear of Failure", "dependability": "Dependability",
                        "love": "Love", "journey": "Journey"}
            territory = " · ".join(terr_map.get(t.strip(), t.strip().title())
                                   for t in raw_territory.split())

        # Get the HTML between this title and the next title (or end)
        start = title_match.end()
        end = title_matches[i + 1].start() if i + 1 < len(title_matches) else len(html)
        section = html[start:end]

        # Extract lyrics -- look for lyric lines
        # Lines are in divs or spans, or just plain text between tags
        lyrics_raw = re.findall(r'class="lyric-line[^"]*"[^>]*>([^<]+)<', section)

        if not lyrics_raw:
            # Fallback: extract text content between verse/section markers
            lyrics_raw = re.findall(r'>([^<]{10,})<', section)
            # Filter out HTML artifacts
            lyrics_raw = [
                l.strip() for l in lyrics_raw
                if not l.strip().startswith(('class=', 'style=', 'div', 'span', '{', '<'))
                and len(l.strip()) > 10
                and not re.match(r'^[\d\s.]+$', l.strip())
            ]

        # Filter to actual lyric bars -- skip production notes, metadata, stage directions
        bars = []
        skip_patterns = [
            r'^\d+\s*BPM',                      # tempo markers
            r'^(Minor|Major)\b',                 # key signatures
            r'^\(.*\)$',                         # pure stage directions like (808 drops...)
            r'^(Verse|Chorus|Hook|Bridge|Outro|Intro|Pre-Chorus)\s*\d*$',  # section headers
            r'^(Dark|Light|Warm|Cold|Dusty|Eerie)\s',  # production descriptors
            r'808|synth|kick|snare|loop|BPM|hi-hat|organ|Rhodes|sample|vinyl',  # production terms
            r'^(Fear of Failure|Dependability|Love|Journey)',  # territory labels
            r'^(Psychedelic|Authoritative|Polished|Orchestral)',  # sound descriptors
            r'Show full lyrics',                  # UI element
            r'No tracks match',                   # UI element
            r'^\w+ · \w+',                       # metadata like "Minor · Dark"
            r'^grrah|^that\'s right',             # ad-libs only
            r'(Southern|Cinematic|Chipmunk|Cole Structure|Verse First|Immigrant|Hook evolves)',  # production/structure notes
        ]
        for line in lyrics_raw:
            line = line.strip()
            if len(line) < 20 or len(line) > 200:
                continue
            # Skip if matches any skip pattern
            if any(re.search(pat, line, re.IGNORECASE) for pat in skip_patterns):
                continue
            # Must have at least 3 words to be a real bar
            if len(line.split()) < 4:
                continue
            bars.append(line)

        tracks.append({
            "track": track_name,
            "territory": territory,
            "lyrics": bars,
            "bar_count": len(bars),
        })

    catalog = {
        "extracted": str(Path(CATALOG_HTML)),
        "extracted_at": __import__("datetime").datetime.now().isoformat(),
        "track_count": len(tracks),
        "total_bars": sum(t["bar_count"] for t in tracks),
        "tracks": tracks,
    }

    LYRICS_JSON.parent.mkdir(parents=True, exist_ok=True)
    LYRICS_JSON.write_text(json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[Catalog] Extracted {len(tracks)} tracks, {catalog['total_bars']} bars")
    for t in tracks:
        print(f"  {t['track']:30s} -- {t['bar_count']} bars ({t['territory']})")

    return catalog


def load_catalog():
    """Load the local lyrics catalog."""
    if not LYRICS_JSON.exists():
        print("[Catalog] lyrics.json not found -- run 'extract' first")
        return None
    return json.loads(LYRICS_JSON.read_text(encoding="utf-8"))


def search_bars(query):
    """Search for bars containing a query string."""
    catalog = load_catalog()
    if not catalog:
        return []

    query_lower = query.lower()
    results = []
    for track in catalog["tracks"]:
        for bar in track["lyrics"]:
            if query_lower in bar.lower():
                results.append({
                    "bar": bar,
                    "track": track["track"],
                    "territory": track["territory"],
                })
    return results


def match_territory(territory_or_theme):
    """Find bars matching a territory or theme keyword."""
    catalog = load_catalog()
    if not catalog:
        return []

    query_lower = territory_or_theme.lower()
    results = []
    for track in catalog["tracks"]:
        # Match by territory name
        if query_lower in track["territory"].lower():
            for bar in track["lyrics"]:
                results.append({
                    "bar": bar,
                    "track": track["track"],
                    "territory": track["territory"],
                })
    return results


def random_bar():
    """Pick a random quotable bar."""
    catalog = load_catalog()
    if not catalog:
        return None

    all_bars = []
    for track in catalog["tracks"]:
        for bar in track["lyrics"]:
            all_bars.append({
                "bar": bar,
                "track": track["track"],
                "territory": track["territory"],
            })

    return random.choice(all_bars) if all_bars else None


def pick_bars_for_themes(themes, count=3):
    """Pick bars that best match a list of theme keywords.
    Used by catalog_agent as the local-first lookup.
    """
    catalog = load_catalog()
    if not catalog:
        return []

    scored = []
    themes_lower = [t.lower() for t in themes]

    for track in catalog["tracks"]:
        territory_lower = track["territory"].lower()
        for bar in track["lyrics"]:
            bar_lower = bar.lower()
            score = 0
            # Score by theme keyword matches in bar text
            for theme in themes_lower:
                words = theme.split()
                for word in words:
                    if word in bar_lower:
                        score += 1
            # Bonus for territory match
            for theme in themes_lower:
                if theme in territory_lower:
                    score += 2

            if score > 0:
                scored.append((score, {
                    "bar": bar,
                    "track": track["track"],
                    "territory": track["territory"],
                }))

    # Sort by score, take top N
    scored.sort(key=lambda x: -x[0])
    return [item for _, item in scored[:count]]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Local lyrics catalog")
    parser.add_argument("command", choices=["extract", "search", "random", "match"])
    parser.add_argument("query", nargs="?")
    args = parser.parse_args()

    if args.command == "extract":
        extract_catalog()
    elif args.command == "search":
        if not args.query:
            print("Usage: catalog_local.py search 'text'")
        else:
            results = search_bars(args.query)
            print(f"{len(results)} matches:")
            for r in results[:10]:
                print(f"  [{r['track']}] {r['bar']}")
    elif args.command == "random":
        bar = random_bar()
        if bar:
            print(f"  [{bar['track']}] {bar['bar']}")
    elif args.command == "match":
        if not args.query:
            print("Usage: catalog_local.py match 'territory'")
        else:
            results = match_territory(args.query)
            print(f"{len(results)} matches:")
            for r in results[:10]:
                print(f"  [{r['track']}] {r['bar']}")
