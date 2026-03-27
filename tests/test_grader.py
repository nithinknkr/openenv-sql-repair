 """Unit tests for server.sandbox.SQLSandbox."""

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


if __name__ == "__main__":
    unittest.main()
