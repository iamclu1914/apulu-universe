"""
prompt_db.py -- Structured prompt database for AI video generation.
Collects, categorizes, and scores prompts from all research sources.
Serves as the knowledge base that feeds back into the Apulu Prompt Generator.

Usage:
    python prompt_db.py ingest          # Pull from all research sources
    python prompt_db.py search "query"  # Search the database
    python prompt_db.py stats           # Show database stats
    python prompt_db.py export          # Export as Obsidian note
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline_config import load_project_config, get_output_dir, save_json, load_json, now_iso

DB_FILENAME = "prompt_database.json"


def get_db_path(config):
    return get_output_dir(config, "prompt-db") / DB_FILENAME


def load_db(config):
    db_path = get_db_path(config)
    data = load_json(db_path)
    if not data:
        data = {"prompts": [], "last_updated": None, "version": 1}
    return data


def save_db(config, db):
    db["last_updated"] = now_iso()
    save_json(get_db_path(config), db)


def ingest(project_name="prompt-generator"):
    """Ingest prompts from all research sources into the database."""
    config = load_project_config(project_name)
    db = load_db(config)
    discovery_dir = get_output_dir(config, "discovery")
    existing_urls = {p.get("source_url") for p in db["prompts"] if p.get("source_url")}

    added = 0

    # Ingest from Reddit prompt results
    reddit_data = load_json(discovery_dir / "reddit_prompt_results.json")
    for post in reddit_data.get("results", []):
        if post.get("url") in existing_urls:
            continue
        for prompt_text in post.get("extracted_prompts", []):
            db["prompts"].append({
                "id": f"reddit_{len(db['prompts'])}_{added}",
                "text": prompt_text[:500],
                "source": "reddit",
                "source_url": post.get("url", ""),
                "subreddit": post.get("subreddit", ""),
                "categories": post.get("categories", []),
                "upvotes": post.get("upvotes", 0),
                "added": now_iso(),
            })
            added += 1

    # Ingest patterns from video quality results
    vq_data = load_json(discovery_dir / "video_quality_results.json")
    pattern_summary = vq_data.get("pattern_summary", {})
    if pattern_summary:
        # Store as a meta-entry -- not a prompt but a pattern insight
        db["prompts"].append({
            "id": f"patterns_{datetime.now().strftime('%Y%m%d')}",
            "text": json.dumps(pattern_summary),
            "source": "video_quality_analysis",
            "source_url": "",
            "categories": ["pattern_insight"],
            "upvotes": 0,
            "added": now_iso(),
        })
        added += 1

    save_db(config, db)
    print(f"[Prompt DB] Ingested {added} new entries. Total: {len(db['prompts'])}")
    return db


def search(query, project_name="prompt-generator"):
    """Search the prompt database."""
    config = load_project_config(project_name)
    db = load_db(config)
    query_lower = query.lower()

    matches = []
    for p in db["prompts"]:
        text = (p.get("text", "") + " " + " ".join(p.get("categories", []))).lower()
        if query_lower in text:
            matches.append(p)

    matches.sort(key=lambda p: p.get("upvotes", 0), reverse=True)

    print(f"[Prompt DB] {len(matches)} results for '{query}'")
    for i, m in enumerate(matches[:10], 1):
        cats = ", ".join(m.get("categories", []))
        print(f"  {i}. [{m['source']}] [{cats}] {m['text'][:100]}")
    return matches


def stats(project_name="prompt-generator"):
    """Show database statistics."""
    config = load_project_config(project_name)
    db = load_db(config)
    prompts = db["prompts"]

    # Count by source
    sources = {}
    categories = {}
    for p in prompts:
        src = p.get("source", "unknown")
        sources[src] = sources.get(src, 0) + 1
        for cat in p.get("categories", []):
            categories[cat] = categories.get(cat, 0) + 1

    print(f"\n{'='*40}")
    print(f"  Prompt Database Stats")
    print(f"{'='*40}")
    print(f"  Total entries: {len(prompts)}")
    print(f"  Last updated: {db.get('last_updated', 'never')}")
    print(f"\n  By source:")
    for src, count in sorted(sources.items(), key=lambda x: -x[1]):
        print(f"    {src}: {count}")
    print(f"\n  By category:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"    {cat}: {count}")
    print()
    return db


def export_obsidian(project_name="prompt-generator"):
    """Export the database as an Obsidian note."""
    config = load_project_config(project_name)
    db = load_db(config)
    output_dir = get_output_dir(config, "prompt-db")
    today = datetime.now().strftime("%Y-%m-%d")

    # Group by category
    by_category = {}
    for p in db["prompts"]:
        for cat in p.get("categories", ["uncategorized"]):
            by_category.setdefault(cat, []).append(p)

    lines = [
        "---",
        f"title: Prompt Database -- {today}",
        f"date: {today}",
        "tags:",
        "  - prompt-research/database",
        f"  - project/{project_name}",
        "---",
        "",
        f"# Prompt Database -- {today}",
        "",
        f"> [!info] {len(db['prompts'])} entries across {len(by_category)} categories",
        "",
    ]

    for cat, prompts in sorted(by_category.items(), key=lambda x: -len(x[1])):
        lines.append(f"## {cat.replace('_', ' ').title()} ({len(prompts)})")
        lines.append("")
        for p in sorted(prompts, key=lambda x: x.get("upvotes", 0), reverse=True)[:10]:
            src = p.get("source", "?")
            lines.append(f"- **[{src}]** {p['text'][:200]}")
            if p.get("source_url"):
                lines.append(f"  [Source]({p['source_url']})")
        lines.append("")

    md_path = output_dir / f"Prompt Database -- {today}.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  [Obsidian] Wrote {md_path.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prompt database manager")
    parser.add_argument("command", choices=["ingest", "search", "stats", "export"])
    parser.add_argument("query", nargs="?", help="Search query")
    parser.add_argument("--project", default="prompt-generator")
    args = parser.parse_args()

    if args.command == "ingest":
        ingest(args.project)
    elif args.command == "search":
        if not args.query:
            print("Usage: prompt_db.py search 'query'")
        else:
            search(args.query, args.project)
    elif args.command == "stats":
        stats(args.project)
    elif args.command == "export":
        export_obsidian(args.project)
