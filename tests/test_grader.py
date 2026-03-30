"""Unit tests for server.sandbox.SQLSandbox and grader functions."""

import sys
import os
import unittest

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from server.sandbox import SQLSandbox


class TestSandboxBlocklist(unittest.TestCase):
    """Verify that the blocklist rejects destructive SQL and allows SELECT."""

    def setUp(self) -> None:
        self.sandbox = SQLSandbox()

    def tearDown(self) -> None:
        self.sandbox.close()

    # -- blocked statements --------------------------------------------------

    def test_drop_table_is_blocked(self) -> None:
        rows, cols, error = self.sandbox.execute("DROP TABLE users;")
        self.assertEqual(rows, [])
        self.assertEqual(cols, [])
        self.assertIsNotNone(error)
        self.assertIn("Blocked", error)
        self.assertIn("DROP", error)

    def test_delete_is_blocked(self) -> None:
        _, _, error = self.sandbox.execute("DELETE FROM users WHERE id = 1;")
        self.assertIn("Blocked", error)

    def test_truncate_is_blocked(self) -> None:
        _, _, error = self.sandbox.execute("TRUNCATE TABLE users;")
        self.assertIn("Blocked", error)

    def test_insert_is_blocked(self) -> None:
        _, _, error = self.sandbox.execute(
            "INSERT INTO users (id, username, email, created_at) VALUES (999, 'x', 'x@x.com', '2025-01-01');"
        )
        self.assertIn("Blocked", error)

    def test_update_is_blocked(self) -> None:
        _, _, error = self.sandbox.execute(
            "UPDATE users SET username = 'hacked' WHERE id = 1;"
        )
        self.assertIn("Blocked", error)

    def test_alter_is_blocked(self) -> None:
        _, _, error = self.sandbox.execute("ALTER TABLE users ADD COLUMN foo TEXT;")
        self.assertIn("Blocked", error)

    def test_create_is_blocked(self) -> None:
        _, _, error = self.sandbox.execute("CREATE TABLE evil (id INTEGER);")
        self.assertIn("Blocked", error)

    # -- allowed statements --------------------------------------------------

    def test_select_is_allowed(self) -> None:
        rows, cols, error = self.sandbox.execute("SELECT id, username FROM users LIMIT 3;")
        self.assertIsNone(error)
        self.assertEqual(len(rows), 3)
        self.assertEqual(cols, ["id", "username"])

    def test_select_count(self) -> None:
        rows, cols, error = self.sandbox.execute("SELECT COUNT(*) FROM products;")
        self.assertIsNone(error)
        self.assertEqual(rows[0][0], 40)

    # -- error handling ------------------------------------------------------

    def test_syntax_error_returns_error_string(self) -> None:
        rows, cols, error = self.sandbox.execute("SELEC * FROM users;")
        self.assertIsNotNone(error)
        self.assertEqual(rows, [])

    # -- schema text ---------------------------------------------------------

    def test_get_schema_text(self) -> None:
        schema = self.sandbox.get_schema_text()
        self.assertIn("CREATE TABLE", schema)
        self.assertIn("users", schema)


from server.grader import row_diff_grade, hard_grade, _get_efficiency_score
from server.sql_repair_environment import _TASKS


class TestGraderScoring(unittest.TestCase):
    def test_determinism(self) -> None:
        gold_rows = [(1, "alice"), (2, "bob")]
        gold_cols = ["id", "name"]
        submitted_rows = [(1, "alice"), (2, "bob")]
        submitted_cols = ["id", "name"]

        row_score = row_diff_grade(submitted_rows, submitted_cols, gold_rows, gold_cols)
        self.assertEqual(row_score, 1.0)

        # Run 10x deterministic for row_diff
        row_scores = [row_diff_grade(submitted_rows, submitted_cols, gold_rows, gold_cols) for _ in range(10)]
        self.assertTrue(all(s == row_score for s in row_scores))

        # Hard score determinism on a safe join query using sandbox model
        sandbox = SQLSandbox()
        try:
            sql = "SELECT users.username, orders.id FROM users LEFT JOIN orders ON users.id = orders.user_id;"
            hard_scores = [hard_grade(submitted_rows, submitted_cols, gold_rows, gold_cols, sandbox, sql) for _ in range(10)]
            self.assertTrue(all(s == hard_scores[0] for s in hard_scores))
        finally:
            sandbox.close()

    def test_score_range_always_between_zero_and_one(self) -> None:
        gold_rows = [(1, "a"), (2, "b")]
        gold_cols = ["id", "name"]
        submitted_rows = [(1, "a")]
        submitted_cols = ["id", "name"]

        r = row_diff_grade(submitted_rows, submitted_cols, gold_rows, gold_cols)
        self.assertGreaterEqual(r, 0.0)
        self.assertLessEqual(r, 1.0)

        sandbox = SQLSandbox()
        try:
            e = _get_efficiency_score(sandbox, "SELECT users.username, orders.id FROM users LEFT JOIN orders ON users.id = orders.user_id;")
            self.assertGreaterEqual(e, 0.0)
            self.assertLessEqual(e, 1.0)
        finally:
            sandbox.close()

    def test_null_handling_works(self) -> None:
        gold_rows = [(None,)]
        gold_cols = ["x"]
        submitted_rows = [(None,)]
        submitted_cols = ["x"]
        score = row_diff_grade(submitted_rows, submitted_cols, gold_rows, gold_cols)
        self.assertEqual(score, 1.0)

    def test_empty_result_guard_select_one_against_expected_rows(self) -> None:
        gold_rows = [(10,), (20,)]
        gold_cols = ["x"]
        submitted_rows = [(1,)]  # SELECT 1-like result does not match rows
        submitted_cols = ["y"]  # different column to avoid column bonus
        score = row_diff_grade(submitted_rows, submitted_cols, gold_rows, gold_cols)
        self.assertEqual(score, 0.0)

    def test_perfect_match_score_is_one(self) -> None:
        gold_rows = [(1, "a"), (2, "b")]
        gold_cols = ["id", "name"]
        submitted_rows = [(1, "a"), (2, "b")]
        submitted_cols = ["id", "name"]
        score = row_diff_grade(submitted_rows, submitted_cols, gold_rows, gold_cols)
        self.assertEqual(score, 1.0)

    def test_partial_match_score_between_0_3_and_0_7(self) -> None:
        gold_rows = [(1,), (2,), (3,), (4,)]
        gold_cols = ["x"]
        submitted_rows = [(1,), (2,)]
        submitted_cols = ["x"]
        score = row_diff_grade(submitted_rows, submitted_cols, gold_rows, gold_cols)
        self.assertGreaterEqual(score, 0.3)
        self.assertLessEqual(score, 0.7)

    def test_column_mismatch_has_no_column_bonus(self) -> None:
        gold_rows = [(1,), (2,), (3,), (4,)]
        gold_cols = ["x"]
        submitted_rows = [(1,), (2,), (3,)]
        submitted_cols = ["wrong"]
        score = row_diff_grade(submitted_rows, submitted_cols, gold_rows, gold_cols)
        self.assertLess(score, 1.0)

    def test_hard_task_single_join_scores_one(self) -> None:
        """A single JOIN executes exactly 1 statement → efficiency 1.0"""
        sandbox = SQLSandbox()
        try:
            sql = (
                "SELECT products.id, products.name, "
                "COALESCE(SUM(order_items.quantity), 0) AS total_sold "
                "FROM products "
                "LEFT JOIN order_items ON products.id = order_items.product_id "
                "GROUP BY products.id, products.name;"
            )
            eff = _get_efficiency_score(sandbox, sql)
            self.assertEqual(eff, 1.0)
        finally:
            sandbox.close()

    def test_hard_task_correlated_subquery_scores_zero(self) -> None:
        """Correlated subquery fires N+1 times → count > 10 → efficiency 0.0"""
        sandbox = SQLSandbox()
        try:
            sql = _TASKS["perf_n_plus_one"]["broken_query"]
            eff = _get_efficiency_score(sandbox, sql)
            self.assertEqual(eff, 0.0)
        finally:
            sandbox.close()

    def test_hard_task_statement_count_determinism(self) -> None:
        """Same query must return identical efficiency score across 10 runs."""
        sandbox = SQLSandbox()
        try:
            sql = _TASKS["perf_n_plus_one"]["broken_query"]
            scores = [_get_efficiency_score(sandbox, sql) for _ in range(10)]
            self.assertTrue(all(s == scores[0] for s in scores))
        finally:
            sandbox.close()


if __name__ == "__main__":
    unittest.main()
