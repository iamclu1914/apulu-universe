"""
obsidian_search.py -- Search Apulu Records Obsidian vault for institutional knowledge.
Agents can use this to find prior research, briefings, and intelligence.

Usage:
    python obsidian_search.py "higgsfield prompting"
    python obsidian_search.py "streaming strategy" --type briefing
    python obsidian_search.py "boom bap" --recent 7

Types: all, briefing, discovery, ideation, scripting, cascade, prompt-research
"""

import argparse
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

VAULT_ROOT = Path(r"C:\Users\rdyal\Apulu Universe")
RESEARCH_DIR = VAULT_ROOT / "research" / "vawn"
WIKI_DIR = VAULT_ROOT / "wiki"

SEARCH_DIRS = {
    "all": [RESEARCH_DIR, WIKI_DIR],
    "briefing": [RESEARCH_DIR / "briefings"],
    "discovery": [RESEARCH_DIR / "discovery"],
    "ideation": [RESEARCH_DIR / "ideation"],
    "scripting": [RESEARCH_DIR / "scripting"],
    "cascade": [RESEARCH_DIR / "cascade"],
    "prompt-research": [RESEARCH_DIR / "prompt-research"],
    "wiki": [WIKI_DIR],
}


def search_vault(query, search_type="all", recent_days=None, max_results=10):
    """Search Obsidian vault for notes matching query."""
    dirs = SEARCH_DIRS.get(search_type, SEARCH_DIRS["all"])
    query_lower = query.lower()
    keywords = query_lower.split()
    results = []

    cutoff = None
    if recent_days:
        cutoff = datetime.now() - timedelta(days=recent_days)

    for search_dir in dirs:
        if not search_dir.exists():
            continue
        for md_file in search_dir.rglob("*.md"):
            # Skip hidden files
            if any(part.startswith(".") for part in md_file.parts):
                continue

            # Check recency
            if cutoff:
                mtime = datetime.fromtimestamp(md_file.stat().st_mtime)
                if mtime < cutoff:
                    continue

            try:
                content = md_file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            content_lower = content.lower()

            # Score: how many keywords match
            score = sum(1 for kw in keywords if kw in content_lower)
            # Bonus for title match
            title = md_file.stem.lower()
            title_score = sum(2 for kw in keywords if kw in title)
            total_score = score + title_score

            if total_score > 0:
                # Extract relevant snippet
                snippet = extract_snippet(content, keywords)
                results.append({
                    "file": str(md_file.relative_to(VAULT_ROOT)),
                    "title": md_file.stem,
                    "score": total_score,
                    "modified": md_file.stat().st_mtime,
                    "snippet": snippet,
                    "size": len(content),
                })

    # Sort by score (desc), then recency (desc)
    results.sort(key=lambda r: (r["score"], r["modified"]), reverse=True)
    return results[:max_results]


def extract_snippet(content, keywords, context_chars=150):
    """Extract a relevant snippet around the first keyword match."""
    content_lower = content.lower()
    for kw in keywords:
        pos = content_lower.find(kw)
        if pos >= 0:
            start = max(0, pos - context_chars // 2)
            end = min(len(content), pos + len(kw) + context_chars // 2)
            snippet = content[start:end].strip()
            # Clean up
            snippet = re.sub(r"\s+", " ", snippet)
            if start > 0:
                snippet = "..." + snippet
            if end < len(content):
                snippet = snippet + "..."
            return snippet
    return content[:context_chars].strip() + "..."


def main():
    parser = argparse.ArgumentParser(description="Search Apulu Records Obsidian vault")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--type", default="all", choices=list(SEARCH_DIRS.keys()), help="Note type to search")
    parser.add_argument("--recent", type=int, help="Only notes from last N days")
    parser.add_argument("--max", type=int, default=10, help="Max results")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    results = search_vault(args.query, args.type, args.recent, args.max)

    if args.json:
        print(json.dumps(results, indent=2, default=str))
    else:
        if not results:
            print(f"No results for '{args.query}' in {args.type}")
            return

        print(f"\nSearch: '{args.query}' (type={args.type}, results={len(results)})")
        print("=" * 60)
        for i, r in enumerate(results, 1):
            modified = datetime.fromtimestamp(r["modified"]).strftime("%Y-%m-%d")
            print(f"\n#{i}  {r['title']}")
            print(f"    File: {r['file']}")
            print(f"    Score: {r['score']} | Modified: {modified} | Size: {r['size']:,} chars")
            print(f"    {r['snippet'][:200]}")


if __name__ == "__main__":
    main()
