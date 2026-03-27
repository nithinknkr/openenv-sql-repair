"""SQL Repair environment client."""

from __future__ import annotations

from typing import Any, Dict, Optional

import httpx
from pydantic import BaseModel

from models import (
    SQLRepairAction,
    SQLRepairObservation,
    SQLRepairState,
    SQLRepairStepResult,
)


# ---------------------------------------------------------------------------
# Base EnvClient (mirrors openenv.core.EnvClient contract)
# ---------------------------------------------------------------------------

class EnvClient(BaseModel):
    """Base client for communicating with an OpenEnv server."""

    server_url: str = "http://localhost:8000"

    class Config:
        arbitrary_types_allowed = True


# ---------------------------------------------------------------------------
# SQLRepairEnv
# ---------------------------------------------------------------------------

class SQLRepairEnv(EnvClient):
    """Client for the SQL Repair environment.

    Stores the session_id returned on reset and automatically passes it
    to every subsequent step and state call.
    """

    session_id: Optional[str] = None

    # -- lifecycle -----------------------------------------------------------

    def reset(self, task_id: Optional[str] = None) -> SQLRepairObservation:
        """Start a new episode. Optionally specify a task_id."""
        payload: Dict[str, Any] = {}
        if task_id is not None:
            payload["task_id"] = task_id

        response = httpx.post(f"{self.server_url}/reset", json=payload)
        response.raise_for_status()
        observation = SQLRepairObservation(**response.json())
        self.session_id = observation.session_id
        return observation

    # -- step ----------------------------------------------------------------

    def step(self, action: SQLRepairAction) -> SQLRepairStepResult:
        """Send an action and receive the step result."""
        if self.session_id is None:
            raise RuntimeError("No active session. Call reset() first.")

        # FIX: session_id sent as query param, not mixed into the action body
        response = httpx.post(
            f"{self.server_url}/step",
            params={"session_id": self.session_id},
            json=action.model_dump(),
        )
        response.raise_for_status()
        return SQLRepairStepResult(**response.json())

    # -- state ---------------------------------------------------------------

    def state(self) -> SQLRepairState:
        """Retrieve the current server-side state for this session."""
        if self.session_id is None:
            raise RuntimeError("No active session. Call reset() first.")

        response = httpx.get(
            f"{self.server_url}/state",
            params={"session_id": self.session_id},
        )
        response.raise_for_status()
        return SQLRepairState(**response.json())

    # -- close ---------------------------------------------------------------

    def close(self) -> None:
        """End the current session."""
        if self.session_id is None:
            return

        httpx.post(
            f"{self.server_url}/close",
            json={"session_id": self.session_id},
        )
        self.session_id = None