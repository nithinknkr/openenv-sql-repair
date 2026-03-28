"""
Deterministic grader for SQL Repair environment.

Tasks 1-4: Counter-based row-diff with float normalisation + column-name bonus.
Task 5   : correctness × 0.6 + efficiency × 0.4
           Efficiency is measured via EXPLAIN QUERY PLAN — correlated subqueries
           show 'CORRELATED' in the plan text and score 0.0 efficiency.
"""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from server.sandbox import SQLSandbox


# ---------------------------------------------------------------------------
# Row normalisation
# ---------------------------------------------------------------------------

def _normalize(rows: List[tuple]) -> List[tuple]:
    """
    Normalise every value in every row for stable comparison:
    - None   → None  (NULL stays NULL)
    - numeric → float (prevents int/float mismatch: 5 vs 5.0)
    - str    → stripped, lower-cased
    """
    result: List[tuple] = []
    for row in rows:
        normed = tuple(
            None if v is None
            else float(v) if isinstance(v, (int, float)) and not isinstance(v, bool)
            else str(v).strip().lower()
            for v in row
        )
        result.append(normed)
    return result


# ---------------------------------------------------------------------------
# Row-diff grader  (Tasks 1–4)
# ---------------------------------------------------------------------------

def row_diff_grade(
    submitted_rows: List[tuple],
    submitted_cols: List[str],
    gold_rows: List[tuple],
    gold_cols: List[str],
    include_column_bonus: bool = True,
) -> float:
    """
    Counter-based multiset comparison between submitted and gold rows.

    Returns a float in [0.0, 1.0].
    - Empty submitted or gold → 0.0 (guard against reward farming)
    - Each matched row decrements the gold counter (handles duplicate rows)
    - Optional +0.10 bonus when column names exactly match
    """
    if not gold_rows or not submitted_rows:
        return 0.0

    sub_norm = _normalize(submitted_rows)
    gold_norm = _normalize(gold_rows)

    gold_counter = Counter(gold_norm)
    matched = 0
    for row in sub_norm:
        if gold_counter.get(row, 0) > 0:
            gold_counter[row] -= 1
            matched += 1

    ratio = matched / len(gold_rows)

    bonus = 0.0
    if include_column_bonus:
        sub_cols_norm = [c.strip().lower() for c in submitted_cols]
        gold_cols_norm = [c.strip().lower() for c in gold_cols]
        if sub_cols_norm == gold_cols_norm:
            bonus = 0.10

    return min(1.0, ratio + bonus)


# ---------------------------------------------------------------------------
# Efficiency scorer via EXPLAIN QUERY PLAN  (Task 5 only)
# ---------------------------------------------------------------------------

def _get_efficiency_score(sandbox: "SQLSandbox", sql: str) -> float:
    """
    Detect N+1 correlated subqueries using SQLite's EXPLAIN QUERY PLAN.

    SQLite ≥ 3.28 returns rows with columns (id, parent, notused, detail).
    A correlated subquery shows 'CORRELATED' in the detail column.

    Score:
      'CORRELATED' found  → 0.0   (N+1 anti-pattern)
      1–2 table scans     → 1.0   (single JOIN — efficient)
      3+ table scans      → 0.8   (acceptable overhead)
      Error / unknown     → 0.5   (neutral)
    """
    try:
        rows, _cols, err = sandbox.execute(f"EXPLAIN QUERY PLAN {sql}")
        if err or not rows:
            return 0.5

        # Last column is always the human-readable detail in SQLite
        plan_text = " ".join(str(row[-1]).upper() for row in rows)

        if "CORRELATED" in plan_text:
            return 0.0

        scan_count = plan_text.count("SCAN")
        if scan_count <= 2:
            return 1.0

        return 0.8
    except Exception:
        return 0.5


# ---------------------------------------------------------------------------
# Hard task grader  (Task 5 — perf_n_plus_one)
# ---------------------------------------------------------------------------

def hard_grade(
    submitted_rows: List[tuple],
    submitted_cols: List[str],
    gold_rows: List[tuple],
    gold_cols: List[str],
    sandbox: "SQLSandbox",
    sql: str,
) -> float:
    """
    Combined correctness + efficiency score for the N+1 performance task.

    final = correctness × 0.6 + efficiency × 0.4
    """
    correctness = row_diff_grade(
        submitted_rows, submitted_cols,
        gold_rows, gold_cols,
        include_column_bonus=False,   # No column bonus for hard task
    )
    efficiency = _get_efficiency_score(sandbox, sql)
    return round(correctness * 0.6 + efficiency * 0.4, 4)
