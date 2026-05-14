"""Initialise an empty hq.db with schema applied. Idempotent."""

from __future__ import annotations

from apulu_hq.config import settings
from apulu_hq.db import get_conn


def main() -> None:
    settings.ensure_dirs()
    conn = get_conn()
    n_agents = conn.execute("SELECT COUNT(*) AS c FROM agents").fetchone()["c"]
    n_routines = conn.execute("SELECT COUNT(*) AS c FROM routines").fetchone()["c"]
    print(f"DB ready at {settings.db_path}")
    print(f"  agents:   {n_agents}")
    print(f"  routines: {n_routines}")


if __name__ == "__main__":
    main()
