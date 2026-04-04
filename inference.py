"""
SQL Auto-Repair OpenEnv — Baseline Inference Script
====================================================
Uses a ReAct loop (Reason → Act → Observe) against all 8 tasks.

Environment variables:
    API_BASE_URL  — LLM API base URL  (default: https://api.groq.com/openai/v1)
    MODEL_NAME    — model identifier  (default: llama-3.3-70b-versatile)
    OPENAI_API_KEY / HF_TOKEN — API key
    SERVER_URL    — environment server (default: http://localhost:7860)

Usage:
    python inference.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Optional

import httpx
from openai import OpenAI

# ---------------------------------------------------------------------------
# Configuration (read from environment — NEVER hardcode secrets)
# ---------------------------------------------------------------------------

API_KEY: str = os.getenv("OPENAI_API_KEY") or os.getenv("HF_TOKEN") or os.getenv("GROQ_API_KEY", "")
API_BASE_URL: str = os.getenv("API_BASE_URL", "https://api.groq.com/openai/v1")
MODEL_NAME: str = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
SERVER_URL: str = os.getenv("SERVER_URL" , "http://localhost:7860")

TEMPERATURE: float = 0.0      # Must be 0 for reproducibility
MAX_TOKENS: int = 512
REQUEST_TIMEOUT: int = 30     # seconds per HTTP call

TASK_IDS = [
    "syntax_missing_comma",
    "syntax_ambiguous_column",
    "logic_operator_precedence",
    "logic_date_boundary",
    "perf_n_plus_one",
    "logic_window_partition",
    "logic_missing_having",
    "cascade_pipeline_bug",
]

# ---------------------------------------------------------------------------
# System prompt (maximises agent performance)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a SQL expert debugging broken SQL queries against an e-commerce SQLite database.

Available actions (respond with JSON only — no extra text):
  {"action_type": "view_schema"}                          — See all table definitions
  {"action_type": "view_error"}                           — See the last error message
  {"action_type": "run_query",    "sql_query": "<SQL>"}   — Test a candidate fix
  {"action_type": "submit_query", "sql_query": "<SQL>"}   — Submit final answer (ends episode)

Strategy:
1. Call view_schema first to understand the tables.
2. Call run_query to test your fix against the live DB.
3. Only call submit_query when you are confident the output is correct.
4. Avoid repeating the same query. Fix errors shown in execution_error.
5. For performance tasks: rewrite correlated subqueries as JOIN + GROUP BY.

Always output valid JSON with exactly one action. Nothing else."""

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _post(path: str, **kwargs) -> dict:
    r = httpx.post(f"{SERVER_URL}{path}", timeout=REQUEST_TIMEOUT, **kwargs)
    r.raise_for_status()
    return r.json()


def _get(path: str, **kwargs) -> dict:
    r = httpx.get(f"{SERVER_URL}{path}", timeout=REQUEST_TIMEOUT, **kwargs)
    r.raise_for_status()
    return r.json()


# ---------------------------------------------------------------------------
# Agent loop
# ---------------------------------------------------------------------------

def run_task(task_id: str, base_url: Optional[str] = None) -> float:
    """
    Run one full episode for `task_id` using the ReAct agent.
    Returns the final grader score (0.0 – 1.0).
    """
    server = base_url or SERVER_URL

    # -- Reset environment --------------------------------------------------
    try:
        r = httpx.post(
            f"{server}/reset",
            json={"task_id": task_id},
            timeout=REQUEST_TIMEOUT,
        )
        r.raise_for_status()
        obs = r.json()
    except Exception as exc:
        print(f"  [ERROR] reset failed for {task_id}: {exc}")
        return 0.0

    session_id: str = obs["session_id"]
    max_steps: int = obs.get("max_steps", 15)

    # -- Build OpenAI client ------------------------------------------------
    client = OpenAI(
        api_key=API_KEY,
        base_url=API_BASE_URL,
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(obs, indent=2)},
    ]

    # -- ReAct loop ---------------------------------------------------------
    for step_num in range(max_steps):
        # Agent generates an action
        try:
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                messages=messages,
                response_format={"type": "json_object"},
            )
            raw = completion.choices[0].message.content.strip()
            action_json = json.loads(raw)
        except Exception as exc:
            print(f"  [WARN] LLM call failed at step {step_num}: {exc}")
            # Fallback: submit broken query to end episode
            action_json = {"action_type": "submit_query", "sql_query": obs.get("broken_query", "")}

        messages.append({"role": "assistant", "content": json.dumps(action_json)})

        # Send action to environment
        try:
            step_r = httpx.post(
                f"{server}/step",
                params={"session_id": session_id},
                json=action_json,
                timeout=REQUEST_TIMEOUT,
            )
            step_r.raise_for_status()
            step_data = step_r.json()
        except Exception as exc:
            print(f"  [ERROR] step failed: {exc}")
            break

        new_obs = step_data.get("observation", {})
        messages.append({"role": "user", "content": json.dumps(new_obs, indent=2)})

        if step_data.get("done", False):
            # Fetch official grader score
            try:
                grade_r = httpx.get(
                    f"{server}/grader",
                    params={"session_id": session_id},
                    timeout=REQUEST_TIMEOUT,
                )
                return float(grade_r.json().get("score", 0.0))
            except Exception:
                return float(new_obs.get("current_score", 0.0))

    # Episode ended without submit — return 0
    return 0.0


# ---------------------------------------------------------------------------
# Main entrypoint
# ---------------------------------------------------------------------------

def main() -> None:
    print(f"\n{'='*60}")
    print(f"SQL Auto-Repair OpenEnv — Baseline Inference")
    print(f"Model   : {MODEL_NAME}")
    print(f"Server  : {SERVER_URL}")
    print(f"{'='*60}\n")

    scores: dict[str, float] = {}
    total_start = time.time()

    for task_id in TASK_IDS:
        print(f"Running task: {task_id} ...", end=" ", flush=True)
        t0 = time.time()
        score = run_task(task_id)
        elapsed = time.time() - t0
        scores[task_id] = score
        print(f"score={score:.3f}  ({elapsed:.1f}s)")

    avg = sum(scores.values()) / len(scores)
    total_elapsed = time.time() - total_start

    print(f"\n{'='*60}")
    print("Results:")
    for tid, s in scores.items():
        print(f"  {tid:<35} {s:.3f}")
    print(f"  {'Average':<35} {avg:.3f}")
    print(f"\nTotal runtime: {total_elapsed:.1f}s")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()