"""
generate_gold.py
================
Utility script — runs every gold query against the seeded SQLite database
and prints the expected result set for each task.

Usage:
    python tests/generate_gold.py

Run this before submission to verify:
  - All gold queries execute without errors
  - All gold result sets are non-empty
  - Seed data is deterministic (run twice, compare output)
"""

import json
import sys
from pathlib import Path

# ── path setup so imports work from any working directory ──────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from server.sandbox import SQLSandbox

TASKS_PATH = ROOT / "data" / "tasks.json"

SEPARATOR = "─" * 60


def run_gold_queries() -> bool:
    """
    Execute every gold_query against a fresh sandbox.
    Returns True if all pass, False if any fail.
    """
    tasks = json.loads(TASKS_PATH.read_text(encoding="utf-8"))
    all_passed = True

    print(f"\n{'='*60}")
    print("  SQL Auto-Repair OpenEnv — Gold Query Verification")
    print(f"{'='*60}\n")

    for task in tasks:
        task_id   = task["task_id"]
        difficulty = task["difficulty"]
        gold_query = task["gold_query"]

        print(SEPARATOR)
        print(f"Task     : {task_id}")
        print(f"Difficulty: {difficulty}")
        print(f"Query    : {gold_query}")
        print()

        sandbox = SQLSandbox()
        rows, cols, error = sandbox.execute(gold_query)
        sandbox.close()

        if error:
            print(f"  [FAIL] Error: {error}")
            all_passed = False
        elif not rows:
            print(f"  [WARN] Gold query returned 0 rows — check seed data!")
            all_passed = False
        else:
            print(f"  [PASS] {len(rows)} row(s) returned")
            print(f"  Columns : {cols}")
            print(f"  First 3 rows:")
            for row in rows[:3]:
                print(f"    {row}")
            if len(rows) > 3:
                print(f"    ... and {len(rows) - 3} more")

        print()

    print(SEPARATOR)
    if all_passed:
        print("  ALL GOLD QUERIES PASSED")
    else:
        print("  SOME GOLD QUERIES FAILED — fix before submission!")
    print(f"{'='*60}\n")

    return all_passed


if __name__ == "__main__":
    success = run_gold_queries()
    sys.exit(0 if success else 1)