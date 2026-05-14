"""Convenience launcher: python scripts/run_shell.py"""
import sys
from pathlib import Path

# Ensure project root is on sys.path when run directly
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apulu_hq.shell import main

if __name__ == "__main__":
    main()
