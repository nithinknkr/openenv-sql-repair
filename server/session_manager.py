"""Thread-safe session registry for concurrent episode isolation."""

from __future__ import annotations

import threading
import time
import uuid
from typing import Dict, Optional, Any


class SessionManager:
    """
    Manages active SQLRepairEnvironment instances keyed by UUID4 session IDs.

    Thread safety: every read/write to _sessions and _last_active is guarded
    by a single threading.Lock().  A background daemon thread evicts sessions
    that have been idle for more than `max_age_seconds` (default 5 minutes).
    """

    def __init__(self, max_age_seconds: int = 300, cleanup_interval: int = 60) -> None:
        self._sessions: Dict[str, Any] = {}
        self._last_active: Dict[str, float] = {}
        self._lock = threading.Lock()
        self._max_age = max_age_seconds

        # Daemon thread — dies automatically when the main process exits
        t = threading.Thread(
            target=self._cleanup_loop,
            args=(cleanup_interval,),
            daemon=True,
        )
        t.start()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_session(self, env: Any) -> str:
        """Register a new environment instance and return its UUID session_id."""
        session_id = str(uuid.uuid4())
        with self._lock:
            self._sessions[session_id] = env
            self._last_active[session_id] = time.time()
        return session_id

    def get_session(self, session_id: str) -> Optional[Any]:
        """Return the env for session_id, updating last-active timestamp.

        Returns None if the session does not exist or has been evicted.
        """
        with self._lock:
            env = self._sessions.get(session_id)
            if env is None:
                return None
            self._last_active[session_id] = time.time()
            return env

    def delete_session(self, session_id: str) -> None:
        """Explicitly remove a session (e.g. on /close)."""
        with self._lock:
            self._sessions.pop(session_id, None)
            self._last_active.pop(session_id, None)

    def session_count(self) -> int:
        """Return number of active sessions (for monitoring)."""
        with self._lock:
            return len(self._sessions)

    def cleanup_stale(self, max_age_seconds: Optional[int] = None) -> int:
        """Evict sessions idle longer than max_age_seconds. Returns count removed."""
        max_age = max_age_seconds if max_age_seconds is not None else self._max_age
        now = time.time()
        with self._lock:
            stale = [
                sid for sid, last in self._last_active.items()
                if now - last > max_age
            ]
            for sid in stale:
                self._sessions.pop(sid, None)
                self._last_active.pop(sid, None)
        return len(stale)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _cleanup_loop(self, interval: int) -> None:
        """Background daemon: run cleanup every `interval` seconds forever."""
        while True:
            time.sleep(interval)
            self.cleanup_stale()
