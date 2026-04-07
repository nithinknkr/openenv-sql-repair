"""Core environment state machine for SQL Auto-Repair OpenEnv."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from models import (
    SQLRepairAction,
    SQLRepairObservation,
    SQLRepairState,
    SQLRepairStepResult,
    ActionType,
)
from server.sandbox import SQLSandbox
from server.grader import row_diff_grade, hard_grade, _SCORE_MIN, _SCORE_MAX

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_TASKS_PATH = Path(__file__).resolve().parent.parent / "data" / "tasks.json"
# Tasks that use the combined correctness+efficiency grader
_HARD_TASK_IDS = {"perf_n_plus_one"} # Only N+1 task uses efficiency scoring

# Destructive keyword pattern (mirrors sandbox blocklist)
_DESTRUCTIVE_RE = re.compile(
    r"\b(DROP|DELETE|TRUNCATE|ALTER|CREATE|INSERT|UPDATE)\b",
    re.IGNORECASE,
)

# Rewards
_REWARD_PER_STEP     = -0.01
_REWARD_VALID_QUERY  = +0.05
_REWARD_PARTIAL_MULT = +0.10
_REWARD_DESTRUCTIVE  = -0.30
_REWARD_REPETITION   = -0.05
_REWARD_SUBMIT_MULT  = +0.70
_REWARD_LOOP_PENALTY = -0.20


# ---------------------------------------------------------------------------
# Task loader (module-level cache — loaded once at startup)
# ---------------------------------------------------------------------------

def _load_tasks() -> Dict[str, dict]:
    raw = json.loads(_TASKS_PATH.read_text(encoding="utf-8"))
    return {t["task_id"]: t for t in raw}


_TASKS: Dict[str, dict] = _load_tasks()


# ---------------------------------------------------------------------------
# SQLRepairEnvironment
# ---------------------------------------------------------------------------

class SQLRepairEnvironment:
    """
    Per-session state machine for one SQL repair episode.

    Lifecycle:
        env = SQLRepairEnvironment()
        obs = env.reset(task_id="syntax_missing_comma")
        result = env.step(action)
        ...
        state = env.state()
    """

    def __init__(self) -> None:
        self.task: Optional[dict] = None
        self.sandbox: Optional[SQLSandbox] = None
        self.step_count: int = 0
        self.current_query: Optional[str] = None
        self.last_result: List[tuple] = []
        self.last_cols: List[str] = []
        self.last_error: Optional[str] = None
        self.last_execution_time_ms: Optional[float] = None
        self.history: List[str] = []          # all queries attempted this episode
        self.submitted_queries: List[str] = [] # only submit_query calls
        self.total_reward: float = 0.0
        self.is_done: bool = False
        self.current_score: float = _SCORE_MIN
        self._cached_schema: str = ""
        self._gold_rows: List[tuple] = []
        self._gold_cols: List[str] = []
        self._session_id: str = ""

    # ------------------------------------------------------------------
    # reset()
    # ------------------------------------------------------------------

    def reset(self, task_id: Optional[str] = None, session_id: str = "") -> SQLRepairObservation:
        """Start a fresh episode. Creates a new in-memory SQLite sandbox."""
        import random

        if task_id and task_id in _TASKS:
            self.task = _TASKS[task_id]
        else:
            self.task = random.choice(list(_TASKS.values()))

        # Fresh sandbox — zero cross-episode contamination
        self.sandbox = SQLSandbox()

        # Pre-compute gold rows using the same sandbox
        gold_rows, gold_cols, err = self.sandbox.execute(self.task["gold_query"])
        self._gold_rows = gold_rows
        self._gold_cols = gold_cols

        # Reset all state
        self.step_count = 0
        self.current_query = None
        self.last_result = []
        self.last_cols = []
        self.last_error = None
        self.last_execution_time_ms = None
        self.history = []
        self.submitted_queries = []
        self.total_reward = 0.0
        self.is_done = False
        self.current_score = _SCORE_MIN
        self._cached_schema = ""
        self._session_id = session_id

        return self._build_observation(schema_info=None)

    # ------------------------------------------------------------------
    # step()
    # ------------------------------------------------------------------


    def step(self, action: SQLRepairAction) -> SQLRepairStepResult:
        """Dispatch one agent action and return (observation, reward, done)."""
        if self.is_done:
            return SQLRepairStepResult(
                observation=self._build_observation(),
                reward=0.0,
                done=True,
        )  # step_count does NOT increment — episode is over

        reward = _REWARD_PER_STEP   # per-step tax
        schema_info: Optional[str] = None

        # ---- Dispatch ----
        if action.action_type == ActionType.view_schema:
            if not self._cached_schema:
                self._cached_schema = self.sandbox.get_schema_text()
            schema_info = self._cached_schema

        elif action.action_type == ActionType.view_error:
            pass  # last_error already in observation

        elif action.action_type == ActionType.run_query:
            reward += self._handle_run_query(action.sql_query or "")

        elif action.action_type == ActionType.submit_query:
            reward += self._handle_submit_query(action.sql_query or "")
        
        self.step_count += 1
        self.total_reward += reward

        # Max steps exceeded
        if self.step_count >= (self.task or {}).get("max_steps", 15):
            self.is_done = True

        return SQLRepairStepResult(
            observation=self._build_observation(schema_info=schema_info),
            reward=round(reward, 4),
            done=self.is_done,
        )

    # ------------------------------------------------------------------
    # state()
    # ------------------------------------------------------------------

    def state(self) -> SQLRepairState:
        return SQLRepairState(
            episode_id=self._session_id,
            session_id=self._session_id,
            step_count=self.step_count,
            task_id=self.task["task_id"] if self.task else "",
            is_done=self.is_done,
            current_score=self.current_score,
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _handle_run_query(self, sql: str) -> float:
        """Execute a test query and compute partial-progress reward."""
        # Destructive keyword check
        if _DESTRUCTIVE_RE.search(sql):
            self.last_error = "Blocked: destructive keyword detected."
            self.last_result = []
            self.last_cols = []
            return _REWARD_DESTRUCTIVE

        # Repetition penalty
        if sql and sql == self.current_query:
            return _REWARD_REPETITION

        import time
        t0 = time.perf_counter()
        rows, cols, err = self.sandbox.execute(sql)
        t1 = time.perf_counter()
        
        self.last_execution_time_ms = (t1 - t0) * 1000.0
        self.current_query = sql
        self.last_result = rows
        self.last_cols = cols
        self.last_error = err
        self.history.append(sql)

        if err:
            return 0.0

        if not rows:
            return 0.0

        # Anti-exploit: check column count matches gold schema signature
        # SELECT 1, SELECT 42 etc return wrong column count → no reward
        if len(cols) != len(self._gold_cols):
            return 0.0

        # Partial match reward
        partial = row_diff_grade(rows, cols, self._gold_rows, self._gold_cols)
        if partial == 0.0:
            return 0.0  # no reward for zero match — blocks SELECT 1 exploit
        return _REWARD_VALID_QUERY + _REWARD_PARTIAL_MULT * partial
        

    def _handle_submit_query(self, sql: str) -> float:
        """Run the grader and finalize the episode."""
        self.is_done = True
        self.submitted_queries.append(sql)

        import time
        t0 = time.perf_counter()
        rows, cols, err = self.sandbox.execute(sql)
        t1 = time.perf_counter()
        
        self.last_execution_time_ms = (t1 - t0) * 1000.0
        self.last_result = rows
        self.last_cols = cols
        self.last_error = err

        # Loop penalty: same query submitted 3+ times
        loop_penalty = 0.0
        if self.submitted_queries.count(sql) >= 3:
            loop_penalty = _REWARD_LOOP_PENALTY

        if err or not rows:
            self.current_score = _SCORE_MIN
            return loop_penalty

        # Grade
        task_id = self.task["task_id"] if self.task else ""
        if task_id in _HARD_TASK_IDS:
            score = hard_grade(rows, cols, self._gold_rows, self._gold_cols, self.sandbox, sql)
        else:
            score = row_diff_grade(rows, cols, self._gold_rows, self._gold_cols)

        self.current_score = round(max(_SCORE_MIN, min(_SCORE_MAX, score)), 4)
        return round(score * _REWARD_SUBMIT_MULT, 4) + loop_penalty

    def _build_observation(self, schema_info: Optional[str] = None) -> SQLRepairObservation:
        """Construct the current observation for the agent.

        schema_info is only populated when the agent explicitly calls view_schema.
        It is NOT persisted across steps to prevent free information leakage.
        """
        task = self.task or {}
        return SQLRepairObservation(
            session_id=self._session_id,
            task_id=task.get("task_id", ""),
            difficulty=task.get("difficulty", ""),
            description=task.get("description", ""),
            broken_query=task.get("broken_query", ""),
            schema_info=schema_info or "",  # Only shown when agent explicitly requests it
            last_query_result=self.last_result or None,
            execution_error=self.last_error,
            execution_time_ms=self.last_execution_time_ms if task.get("task_id") == "perf_n_plus_one" else None,
            step_count=self.step_count,
            max_steps=task.get("max_steps", 15),
            hints=task.get("hints", []),
            available_actions=["view_schema", "view_error", "run_query", "submit_query"],
        )
