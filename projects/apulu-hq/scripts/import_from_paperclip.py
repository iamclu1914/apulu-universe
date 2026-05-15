"""CLI wrapper around apulu_hq.importer.import_all."""

from __future__ import annotations

import argparse
from pathlib import Path

from apulu_hq.importer import import_all


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Override path to the apulu-universe repo root (otherwise auto-detected).",
    )
    args = p.parse_args()
    counts = import_all(repo_root=args.repo_root)
    print(f"Imported {counts['agents']} agents and {counts['routines']} routines.")


if __name__ == "__main__":
    main()
