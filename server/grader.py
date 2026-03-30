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

class _ExecutionCountProxy:
    """Wraps a sqlite3.Connection and counts every cursor.execute() call."""

    def __init__(self, conn) -> None:
        self._conn = conn
        self.count = 0

    def execute(self, sql: str, params=()):
        self.count += 1
        return self._conn.execute(sql, params)

    def __getattr__(self, name):
        return getattr(self._conn, name)


def _get_efficiency_score(sandbox: "SQLSandbox", sql: str) -> float:
    """
    Measure N+1 anti-pattern by counting actual cursor.execute() calls.

    The broken correlated subquery fires one inner SELECT per outer row
    (N+1 total). The correct JOIN+GROUP BY fires exactly 1 statement.

    Score:
      count == 1     → 1.0  (optimal single-pass)
      count <= 3     → 0.8  (minor overhead, acceptable)
      count <= 10    → 0.5  (partial improvement)
      count >  10    → 0.0  (still effectively N+1)
      error          → 0.0  (broken query gets no efficiency credit)
    """
    import sqlite3

    try:
        conn = sqlite3.connect(":memory:", check_same_thread=False)
        # Load schema into this fresh connection
        schema_path = sandbox._DEFAULT_SCHEMA_PATH \
            if hasattr(sandbox, "_DEFAULT_SCHEMA_PATH") \
            else __import__("pathlib").Path(__file__).resolve().parent.parent / "data" / "schema.sql"
        conn.executescript(
            __import__("pathlib").Path(schema_path).read_text(encoding="utf-8")
        )

        proxy = _ExecutionCountProxy(conn)

        try:
            cursor = proxy.execute(sql)
            cursor.fetchall()
        except sqlite3.Error:
            conn.close()
            return 0.0

        count = proxy.count
        conn.close()

        if count <= 1:
            return 1.0
        elif count <= 3:
            return 0.8
        elif count <= 10:
            return 0.5
        else:
            return 0.0

    except Exception:
        return 0.0


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
