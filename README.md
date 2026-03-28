---
title: SQL Auto-Repair OpenEnv
emoji: 🔧
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
tags:
  - openenv
  - sql
  - reinforcement-learning
  - data-engineering
pinned: false
---

# 🔧 SQL Auto-Repair OpenEnv

A complete **reinforcement learning environment** built on the OpenEnv framework. An AI agent interacts with a sandboxed SQLite e-commerce database to iteratively diagnose and repair broken SQL queries.

Unlike static linters (SQLFluff, etc.), this environment requires an agent to **iteratively explore a live database** — running queries, reading errors, and rewriting SQL based on live feedback. Static analysis tools cannot replicate this workflow.

---

## What the Agent Does

```
reset()  →  Agent receives: broken SQL query + task description + session_id
              (schema is HIDDEN — agent must call view_schema to see it)

step(view_schema)   →  Agent sees all 5 table definitions and column types
step(run_query)     →  Agent tests a fix, sees rows or error message
step(run_query)     →  Agent refines — partial reward signal guides it
step(submit_query)  →  Agent submits final answer → grader scores 0.0–1.0 → done
```

---

## Action Space

| action_type | sql_query required | Description |
|---|---|---|
| `view_schema` | No | Reveals full DB schema DDL |
| `view_error` | No | Shows last execution error |
| `run_query` | Yes | Executes SQL, returns rows or error |
| `submit_query` | Yes | Submits final answer, ends episode |

## Observation Space

| Field | Type | Description |
|---|---|---|
| `session_id` | string | UUID4 episode identifier |
| `task_id` | string | Active task identifier |
| `difficulty` | string | easy / medium / hard |
| `broken_query` | string | The original buggy SQL |
| `schema_info` | string | DB schema (null until view_schema called) |
| `last_query_result` | list | Rows from last run_query |
| `execution_error` | string | SQLite error from last query |
| `step_count` | int | Steps taken so far |
| `max_steps` | int | Maximum allowed steps |
| `hints` | list | Optional hints for the agent |

---

## The 5 Tasks

| Task ID | Difficulty | Bug Type | Expected Score |
|---|---|---|---|
| `syntax_missing_comma` | Easy | Syntax | ~0.90 |
| `syntax_wrong_keyword` | Easy | Syntax | ~0.90 |
| `logic_wrong_join` | Medium | Logic | ~0.45 |
| `logic_wrong_aggregation` | Medium | Logic | ~0.50 |
| `perf_n_plus_one` | Hard | Performance | ~0.28 |

---

## Reward Function

| Event | Reward |
|---|---|
| Every step taken | −0.01 |
| Valid `run_query` (no error) | +0.05 |
| Partial row match on `run_query` | +0.10 × ratio |
| Empty result | 0.0 |
| Same query repeated | −0.05 |
| Destructive keyword (DROP, etc.) | −0.30 |
| `submit_query` final score G | G × 0.70 |

---

## Setup & Usage

```bash
# Clone and install
git clone https://github.com/nithinknkr/openenv-sql-repair.git
cd openenv-sql-repair
pip install -e .

# Run locally
uvicorn server.app:app --host 0.0.0.0 --port 7860

# Run baseline inference
export HF_TOKEN=hf_...
export MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
export API_BASE_URL=https://router.huggingface.co/v1
python inference.py

# Docker
docker build -t sql-auto-repair .
docker run -p 7860:7860 -e HF_TOKEN=hf_... -e MODEL_NAME=Qwen/Qwen2.5-72B-Instruct sql-auto-repair
```

---

## Baseline Scores

*(Recorded with Qwen/Qwen2.5-72B-Instruct, temperature=0)*

| Task | Score |
|---|---|
| syntax_missing_comma | 0.90 |
| syntax_wrong_keyword | 0.90 |
| logic_wrong_join | 0.45 |
| logic_wrong_aggregation | 0.50 |
| perf_n_plus_one | 0.28 |
| **Average** | **0.61** |
