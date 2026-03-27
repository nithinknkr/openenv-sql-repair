"""SQLite sandbox — one in-memory DB per instance, SELECT-only allowlist."""

from __future__ import annotations

import os
import re
import sqlite3
import threading
from pathlib import Path
from typing import List, Optional, Tuple

# ---------------------------------------------------------------------------
# Compiled blocklist regex — whole-word, case-insensitive
# ---------------------------------------------------------------------------
_BLOCKED_KEYWORDS = re.compile(
    r"\b(DROP|DELETE|TRUNCATE|ALTER|CREATE|INSERT|UPDATE)\b",
    re.IGNORECASE,
)

# Default path to schema + seed SQL
_DEFAULT_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "data" / "schema.sql"

# Execution timeout in seconds
_TIMEOUT_SECONDS = 5


class SQLSandbox:
    """Isolated, read-only SQLite sandbox.

    * Fresh ``:memory:`` connection per instance — no file I/O,
      no cross-episode state leakage.
    * Schema + seed rows loaded at construction time.
    * Only ``SELECT`` statements are allowed (allowlist enforced via
      compiled regex blocklist).
    * Query execution is wrapped in ``try/except sqlite3.Error``
      with a 5-second timeout via ``threading.Timer``.
    """

    def __init__(self, schema_path: Optional[str] = None) -> None:
        self._conn = sqlite3.connect(":memory:", check_same_thread=False)
        schema_file = Path(schema_path) if schema_path else _DEFAULT_SCHEMA_PATH
        self._load_schema(schema_file)

    # -- public API ----------------------------------------------------------

    def execute(
        self, sql: str
    ) -> Tuple[List[tuple], List[str], Optional[str]]:
        """Run a SELECT query inside the sandbox.

        Returns
        -------
        (result_rows, column_names, error)
            * ``result_rows`` — list of row tuples (empty on error).
            * ``column_names`` — column names from the cursor description.
            * ``error`` — ``None`` on success, error string on failure.
        """
        # --- allowlist check ------------------------------------------------
        violation = _BLOCKED_KEYWORDS.search(sql)
        if violation:
            return (
                [],
                [],
                f"Blocked: destructive keyword '{violation.group()}' is not allowed.",
            )

        # --- execute with timeout -------------------------------------------
        result_rows: List[tuple] = []
        column_names: List[str] = []
        error: Optional[str] = None

        def _run() -> None:
            nonlocal result_rows, column_names, error
            try:
                cursor = self._conn.execute(sql)
                result_rows = cursor.fetchall()
                column_names = (
                    [desc[0] for desc in cursor.description]
                    if cursor.description
                    else []
                )
            except sqlite3.Error as exc:
                error = str(exc)

        worker = threading.Thread(target=_run, daemon=True)
        worker.start()
        worker.join(timeout=_TIMEOUT_SECONDS)

        if worker.is_alive():
            # Query exceeded the timeout — interrupt it
            self._conn.interrupt()
            worker.join()
            return [], [], f"Query timed out after {_TIMEOUT_SECONDS} seconds."

        return result_rows, column_names, error

    def get_schema_text(self) -> str:
        """Return the DDL portion of schema.sql (everything before INSERTs)."""
        rows = self._conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        return "\n\n".join(row[0] for row in rows if row[0])

    def close(self) -> None:
        """Close the underlying connection."""
        self._conn.close()

    # -- internals -----------------------------------------------------------

    def _load_schema(self, path: Path) -> None:
        """Execute every statement in the schema file."""
        sql_text = path.read_text(encoding="utf-8")
        self._conn.executescript(sql_text)
