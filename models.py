"""Pydantic models for the SQL Repair environment."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Base classes (mirrors openenv.core contracts)
# ---------------------------------------------------------------------------

class Action(BaseModel):
    """Base class for environment actions."""
    pass


class Observation(BaseModel):
    """Base class for environment observations."""
    # FIX: session_id removed from base class — it belongs only on SQLRepairObservation
    pass


class State(BaseModel):
    """Base class for environment state."""
    pass


# ---------------------------------------------------------------------------
# 1. ActionType enum
# ---------------------------------------------------------------------------

class ActionType(str, Enum):
    """Allowed action types an agent can take."""
    submit_query  = "submit_query"
    run_query     = "run_query"
    view_schema   = "view_schema"
    view_error    = "view_error"


# ---------------------------------------------------------------------------
# 2. SQLRepairAction
# ---------------------------------------------------------------------------

class SQLRepairAction(Action):
    """An action submitted by the agent to interact with the SQL environment."""

    action_type: ActionType = Field(
        ...,
        description="The kind of action the agent wants to perform",
    )
    sql_query: Optional[str] = Field(
        None,
        description="SQL query string (required for submit_query and run_query)",
    )


# ---------------------------------------------------------------------------
# 3. SQLRepairObservation
# ---------------------------------------------------------------------------

class SQLRepairObservation(Observation):
    """Observation returned to the agent after each step."""

    # FIX: session_id moved here from base Observation class
    session_id: str = Field(..., description="Unique session identifier")
    task_id: str = Field(..., description="Identifier of the current task")
    difficulty: str = Field(..., description="Task difficulty (easy / medium / hard)")
    description: str = Field(..., description="Human-readable task description")
    broken_query: str = Field(..., description="The original buggy SQL query")
    schema_info: str = Field("", description="Database schema definition text")
    error_message: Optional[str] = Field(
        None, description="Error message from the broken query execution"
    )
    last_query_result: Optional[list] = Field(
        None, description="Rows returned by the most recent run_query action"
    )
    execution_error: Optional[str] = Field(
        None, description="Error encountered during the last run_query"
    )
    step_count: int = Field(0, description="Number of steps taken so far")
    max_steps: int = Field(15, description="Maximum allowed steps for this task")
    hints: List[str] = Field(
        default_factory=list,
        description="Optional progressive hints for the agent",
    )
    available_actions: List[str] = Field(
        default_factory=lambda: ["view_schema", "view_error", "run_query", "submit_query"],
        description="Valid action_type values at this step",
    )


# ---------------------------------------------------------------------------
# 4. SQLRepairState
# ---------------------------------------------------------------------------

class SQLRepairState(State):
    """Internal server-side state for an active episode."""

    episode_id: str = Field(..., description="Unique episode identifier")
    session_id: str = Field(..., description="Unique session identifier")
    step_count: int = Field(0, description="Steps consumed so far")
    task_id: str = Field(..., description="Identifier of the current task")
    is_done: bool = Field(False, description="Whether the episode has ended")
    current_score: float = Field(
        0.0, description="Current score for this episode (0.0 – 1.0)"
    )


# ---------------------------------------------------------------------------
# 5. StepResult + SQLRepairStepResult
# ---------------------------------------------------------------------------

class StepResult(BaseModel):
    """Base class for step results returned by the environment."""
    pass


class SQLRepairStepResult(StepResult):
    """Result returned after each environment step."""

    observation: SQLRepairObservation = Field(
        ..., description="The observation returned after this step"
    )
    reward: float = Field(0.0, description="Reward signal for this step")
    done: bool = Field(False, description="Whether the episode has ended")