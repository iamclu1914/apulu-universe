"""
research_company.py — Autonomous orchestrator for the Vawn Research Company.
Runs 4 agents in sequence: TrendAgent → AudienceAgent → CatalogAgent → ContentAgent.
Schedule: Windows Task Scheduler, 6:10am daily.
"""

import sys
import traceback
sys.path.insert(0, r"C:\Users\rdyal\Vawn")
from vawn_config import log_run, RESEARCH_DIR

RESEARCH_DIR.mkdir(exist_ok=True)


def main():
    print("\n=== Vawn Research Company ===\n")

    agents = [
        ("TrendAgent", "agents_research.trend_agent"),
        ("AudienceAgent", "agents_research.audience_agent"),
        ("CatalogAgent", "agents_research.catalog_agent"),
        ("ContentAgent", "agents_research.content_agent"),
    ]

    results = {}
    for name, module_path in agents:
        print(f"\n--- Running {name} ---")
        try:
            mod = __import__(module_path, fromlist=["run"])
            result = mod.run()
            results[name] = "ok"
            print(f"[OK] {name} complete")
        except Exception as e:
            results[name] = f"error: {e}"
            print(f"[FAIL] {name}: {e}")
            traceback.print_exc()
            log_run(name, "error", str(e))

    print("\n=== Research Company Summary ===")
    for name, status in results.items():
        marker = "[OK]" if status == "ok" else "[FAIL]"
        print(f"  {marker} {name}: {status}")
    print()


if __name__ == "__main__":
    main()
