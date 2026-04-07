"""
Deterministic grader for SQL Repair environment.

Tasks 1-2 (Easy syntax)  : row_diff_grade
Tasks 3-4 (Medium logic) : row_diff_grade
Task  5   (Hard perf)    : correctness × 0.6 + efficiency × 0.4
                           Efficiency measured via EXPLAIN QUERY PLAN —
                           correlated subqueries show 'CORRELATED' and score 0.0.
Tasks 6-7 (Hard logic)   : row_diff_grade (wrong window / missing HAVING)
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
# Score clamping — validator requires strictly (0, 1)
# ---------------------------------------------------------------------------

_SCORE_MIN = 0.01
_SCORE_MAX = 0.99


def _clamp(score: float) -> float:
    """Clamp score to the open interval (0, 1) as required by the validator."""
    return max(_SCORE_MIN, min(_SCORE_MAX, score))


# ---------------------------------------------------------------------------
# Row-diff grader  (Tasks 1–4, 6–8)
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

    Returns a float strictly in (0.001, 0.999).
    - Empty submitted or gold → _SCORE_MIN (guard against reward farming)
    - Each matched row decrements the gold counter (handles duplicate rows)
    - Optional +0.10 bonus when column names exactly match
    """
    if not gold_rows or not submitted_rows:
        return _SCORE_MIN

    sub_norm = _normalize(submitted_rows)
    gold_norm = _normalize(gold_rows)

    gold_counter = Counter(gold_norm)
    matched = 0
    for row in sub_norm:
        if gold_counter.get(row, 0) > 0:
            gold_counter[row] -= 1
            matched += 1

    ratio = matched / max(len(gold_rows), len(submitted_rows))

    bonus = 0.0
    if include_column_bonus:
        sub_cols_norm = [c.strip().lower() for c in submitted_cols]
        gold_cols_norm = [c.strip().lower() for c in gold_cols]
        if sub_cols_norm == gold_cols_norm:
            bonus = 0.10

    raw = min(1.0, ratio + bonus)
    return round(max(_SCORE_MIN, min(_SCORE_MAX, raw)), 4)


# ---------------------------------------------------------------------------
# Efficiency scorer via EXPLAIN QUERY PLAN  (Task 5 only)
# ---------------------------------------------------------------------------
def _get_efficiency_score(sandbox: "SQLSandbox", sql: str) -> float:
    try:
        rows, _cols, err = sandbox.execute(f"EXPLAIN QUERY PLAN {sql}")
        if err or not rows:
            return 0.5
        plan_text = " ".join(str(row[-1]).upper() for row in rows)
        if "CORRELATED" in plan_text:
            return 0.05
        scan_count = plan_text.count("SCAN")
        if scan_count <= 2:
            return 0.95
        return 0.80
    except Exception:
        return 0.50


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
    raw = correctness * 0.6 + efficiency * 0.4
    return round(max(_SCORE_MIN, min(_SCORE_MAX, raw)), 4)
