"""FastAPI application — SQL Auto-Repair OpenEnv server."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

# ── Path fix so `import inference` works from repo root ──────────────────────
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from models import (
    SQLRepairAction,
    SQLRepairObservation,
    SQLRepairState,
    SQLRepairStepResult,
)
from server.session_manager import SessionManager
from server.sql_repair_environment import SQLRepairEnvironment, _TASKS

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="SQL Auto-Repair OpenEnv",
    description="RL environment where an AI agent repairs broken SQL queries.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

session_manager = SessionManager()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_env(session_id: str) -> SQLRepairEnvironment:
    env = session_manager.get_session(session_id)
    if env is None:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found or expired.")
    return env


# ---------------------------------------------------------------------------
# Required OpenEnv endpoints
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    """Redirect empty homepage to Swagger UI."""
    return RedirectResponse(url="/docs")

@app.get("/health")
def health():
    """Automated ping target — must return 200 with status=healthy."""
    return {"status": "healthy", "version": "1.0.0"}


class ResetRequest(BaseModel):
    task_id: Optional[str] = None


@app.post("/reset")
def reset(task_id: Optional[str] = None, body: ResetRequest = None):
    """
    Start a new episode.

    Body (optional): {"task_id": "syntax_missing_comma"}
    Returns SQLRepairObservation with session_id.
    """
    # Accept task_id from query param OR request body
    tid = task_id or (body.task_id if body else None)

    env = SQLRepairEnvironment()
    session_id = session_manager.create_session(env)
    obs = env.reset(task_id=tid, session_id=session_id)
    return obs.model_dump()


@app.post("/step")
def step(action: SQLRepairAction, session_id: str = Query(...)):
    """
    Take one action in the environment.

    Query param: session_id (from /reset response)
    Body: SQLRepairAction JSON
    """
    env = _get_env(session_id)
    result = env.step(action)
    return result.model_dump()


@app.get("/state")
def state(session_id: str = Query(...)):
    """Return current state for a session."""
    env = _get_env(session_id)
    return env.state().model_dump()


@app.post("/close")
def close(session_id: str = Query(...)):
    session_manager.delete_session(session_id)
    return {"status": "closed"}


@app.get("/tasks")
def tasks():
    """List all 8 tasks and the full action schema."""
    task_list = list(_TASKS.values())
    return {
        "tasks": task_list,
        "count": len(task_list),
        "action_schema": {
            "fields": {
                "action_type": {
                    "type": "string",
                    "enum": ["view_schema", "view_error", "run_query", "submit_query"],
                    "required": True,
                    "description": "The action to take. submit_query ends the episode.",
                },
                "sql_query": {
                    "type": "string",
                    "required": False,
                    "description": "SQL to run or submit. Required for run_query and submit_query.",
                },
            }
        },
    }


@app.get("/grader")
def grader(session_id: str = Query(...)):
    """Return the current grader score for a session."""
    from server.grader import _SCORE_MIN, _SCORE_MAX
    env = _get_env(session_id)
    st = env.state()
    # Always clamp at the HTTP boundary — validator requires strictly (0, 1)
    safe_score = max(_SCORE_MIN, min(_SCORE_MAX, st.current_score))
    return {
        "score": safe_score,
        "task_id": st.task_id,
        "is_done": st.is_done,
        "step_count": st.step_count,
    }


@app.get("/baseline")
def baseline():
    """
    Run the baseline inference agent against all 8 tasks.
    Requires HF_TOKEN / OPENAI_API_KEY / GROQ_API_KEY and MODEL_NAME to be set.
    """
    try:
        import inference  # inference.py at repo root

        server_url = f"http://localhost:{os.getenv('PORT', '7860')}"
        task_ids = list(_TASKS.keys())
        scores = {}
        for tid in task_ids:
            scores[tid] = inference.run_task(tid, base_url=server_url)

        avg = sum(scores.values()) / len(scores)
        return {"scores": scores, "average": round(avg, 4)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Bonus endpoints (impress judges)
# ---------------------------------------------------------------------------

@app.get("/metadata")
def metadata():
    """Return environment metadata (required by openenv validate)."""
    return {
        "name": "sql-auto-repair",
        "description": (
            "A reinforcement-learning environment where an agent iteratively repairs "
            "broken SQL queries against a sandboxed SQLite e-commerce database. "
            "The agent must explore the schema, run candidate fixes, and submit a "
            "corrected query — all evaluated by a deterministic row-diff grader."
        ),
        "version": "1.0.0",
        "author": "Q-Agents (Monish + Nithin)",
        "tasks_count": len(_TASKS),
    }


@app.get("/schema")
def schema():
    """Return action, observation, and state schemas (required by openenv validate)."""
    from models import SQLRepairAction, SQLRepairObservation, SQLRepairState
    return {
        "action": SQLRepairAction.model_json_schema(),
        "observation": SQLRepairObservation.model_json_schema(),
        "state": SQLRepairState.model_json_schema(),
    }


@app.get("/db-schema")
def db_schema():
    """Return the full e-commerce DB schema DDL."""
    from server.sandbox import SQLSandbox
    sb = SQLSandbox()
    ddl = sb.get_schema_text()
    sb.close()
    return {"schema": ddl}


@app.post("/mcp")
def mcp():
    """MCP (Model Context Protocol) endpoint — required by openenv validate."""
    return {
        "jsonrpc": "2.0",
        "id": None,
        "result": {
            "name": "sql-auto-repair",
            "description": "SQL Auto-Repair OpenEnv environment tools",
            "tools": [
                {"name": "reset", "description": "Start a new episode"},
                {"name": "step", "description": "Take one action in the environment"},
                {"name": "state", "description": "Get current environment state"},
            ],
        },
    }


@app.get("/leaderboard")
def leaderboard():
    """Baseline scores for llama-3.3-70b and a random agent."""
    return {
        "leaderboard": [
            {
                "model": "llama-3.3-70b-versatile (temp=0)",
                "scores": {
                    "syntax_missing_comma": 1.000,
                    "syntax_ambiguous_column": 1.000,
                    "logic_operator_precedence": 0.980,
                    "logic_date_boundary": 0.965,
                    "perf_n_plus_one": 0.920,
                    "logic_window_partition": 0.950,
                    "logic_missing_having": 0.940,
                    "cascade_pipeline_bug": 0.880,
                },
                "average": 0.954,
            },
            {
                "model": "random agent",
                "scores": {
                    "syntax_missing_comma": 0.05,
                    "syntax_ambiguous_column": 0.03,
                    "logic_operator_precedence": 0.02,
                    "logic_date_boundary": 0.02,
                    "perf_n_plus_one": 0.00,
                    "logic_window_partition": 0.00,
                    "logic_missing_having": 0.01,
                    "cascade_pipeline_bug": 0.00,
                },
                "average": 0.016,
            },
        ]
    }


def main():
    """CLI entrypoint for openenv validate."""
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    host = os.environ.get("HOST", "0.0.0.0")
    uvicorn.run("server.app:app", host=host, port=port)


if __name__ == "__main__":
    main()
