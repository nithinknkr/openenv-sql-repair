from __future__ import annotations

import json
import os
import sys
import time
from typing import Optional

import httpx
from openai import OpenAI

# Required env vars (per OpenEnv submission spec)
API_BASE_URL: str = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME: str   = os.getenv("MODEL_NAME", "meta-llama/Llama-3.3-70B-Instruct")
HF_TOKEN: str     = os.getenv("HF_TOKEN")           # No default — injected by platform
LOCAL_IMAGE_NAME: str = os.getenv("LOCAL_IMAGE_NAME")  # Optional — for docker mode

# Internal helpers
API_KEY: str    = HF_TOKEN or os.getenv("OPENAI_API_KEY") or os.getenv("GROQ_API_KEY", "")
SERVER_URL: str = os.getenv("SERVER_URL", "http://localhost:7860")

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
# Strict openenv stdout logging formats
# ---------------------------------------------------------------------------
def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str] = None) -> None:
    err_str = "null" if not error else f"\"{error}\""
    # some errors contain quotes so just escaping broadly or printing null avoids breaking things, 
    # but the sample uses 'error=null' for clean. When there is a string, it should ideally be clean.
    # To keep it completely safe from breaking parsing, we replace spaces/newlines with underscores
    if error:
        err_str = error.replace("\n", " ").replace('"', "'")
        err_str = f'"{err_str}"'
    done_str = "true" if done else "false"
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={done_str} error={err_str}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: list[float]) -> None:
    succ_str = "true" if success else "false"
    rew_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={succ_str} steps={steps} score={score:.3f} rewards={rew_str}", flush=True)


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
# Agent loop
# ---------------------------------------------------------------------------

def run_task(task_id: str, base_url: Optional[str] = None) -> float:
    """
    Run one full episode for `task_id` using the ReAct agent.
    Returns the final grader score clamped between 0.01 and 0.99.
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
        return 0.01

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

    log_start(task=task_id, env="sql-auto-repair", model=MODEL_NAME)
    
    rewards: list[float] = []
    steps_taken = 0
    score = 0.01
    success = False

    # -- ReAct loop ---------------------------------------------------------
    for step_num in range(max_steps):
        steps_taken = step_num + 1

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
            # Fallback: submit broken query to end episode safely
            action_json = {"action_type": "submit_query", "sql_query": obs.get("broken_query", "")}
            
        action_type = action_json.get("action_type", "unknown")
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

        reward = float(step_data.get("reward", 0.0))
        done = bool(step_data.get("done", False))
        error_msg = new_obs.get("execution_error")
        rewards.append(reward)

        log_step(step=steps_taken, action=action_type, reward=reward, done=done, error=error_msg)

        if done:
            # Fetch official grader score
            try:
                grade_r = httpx.get(
                    f"{server}/grader",
                    params={"session_id": session_id},
                    timeout=REQUEST_TIMEOUT,
                )
                raw_score = float(grade_r.json().get("score", 0.0))
            except Exception:
                raw_score = float(new_obs.get("current_score", 0.0))
            
            score = max(0.01, min(0.99, raw_score))
            success = score > 0.5  # Arbitrary threshold to log as "successful" completion
            
            log_end(success=success, steps=steps_taken, score=score, rewards=rewards)
            return score

    # Episode ended without submit — return clamped minimum
    score = 0.01
    log_end(success=False, steps=steps_taken, score=score, rewards=rewards)
    return score


# ---------------------------------------------------------------------------
# Main entrypoint
# ---------------------------------------------------------------------------

def main() -> None:
    # Allow single task via: python inference.py syntax_missing_comma
    task_filter = sys.argv[1] if len(sys.argv) > 1 else None
    task_ids_to_run = [task_filter] if task_filter else TASK_IDS

    scores: dict[str, float] = {}

    for task_id in task_ids_to_run:
        score = run_task(task_id)
        scores[task_id] = score


if __name__ == "__main__":
    main()