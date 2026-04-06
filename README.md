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

> **Design Rationale — Dataset Size:** The schema is intentionally compact (5 tables, 50 users, 40 products, 25 orders) to ensure fully deterministic, reproducible grading across all evaluation runs. The grader compares exact row sets — larger synthetic datasets would introduce ordering non-determinism without adding evaluation signal. The *complexity* comes from the query logic, not the row count.

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

## The 8 Tasks

| Task ID | Difficulty | Bug Type | What Makes It Hard | Expected Score |
|---|---|---|---|---|
| `syntax_missing_comma`     | Easy   | Syntax      | Missing commas between SELECT columns — query fails with a clear error | ~1.00 |
| `syntax_ambiguous_column`  | Easy   | Syntax      | Ambiguous column reference across joined tables — agent must qualify with table prefix | ~1.00 |
| `logic_operator_precedence`| Medium | Logic       | Misplaced OR/AND logic — agent must add parentheses to correct the precedence | ~0.98 |
| `logic_date_boundary`      | Medium | Logic       | Wrong comparison operator or date filter — agent must adjust for inclusive ranges | ~0.96 |
| `perf_n_plus_one`          | Hard   | Performance | Correlated subquery fires once per row — agent must rewrite as single JOIN + GROUP BY | ~0.92 |
| `logic_window_partition`   | Hard   | Logic       | Global ranking instead of per-category — agent must add PARTITION BY to window function | ~0.95 |
| `logic_missing_having`     | Hard   | Logic       | Filtering groups using WHERE instead of HAVING — agent must identify correct aggregation filter | ~0.94 |
| `cascade_pipeline_bug`     | Hard   | Cascade     | Error in early CTE step propagates downstream — agent must trace through the entire logical pipeline | ~0.88 |




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

## Grader Design

**Tasks 1–4:** Counter-based multiset row diff with float normalisation and +0.10 column-name bonus. Fully deterministic across all SQLite versions.

**Task 5 (perf_n_plus_one):** correctness × 0.6 + efficiency × 0.4. Efficiency is measured via SQLite's `EXPLAIN QUERY PLAN` — correlated subqueries show `CORRELATED SCALAR SUBQUERY` in the plan text and score 0.0 efficiency. This is deterministic across all SQLite versions shipped with Python 3.11+:

| Plan result | Efficiency score |
|---|---|
| `CORRELATED` in plan text | 0.0 — N+1 anti-pattern confirmed |
| ≤ 2 table scans, no CORRELATED | 1.0 — optimal single-pass JOIN |
| 3+ table scans | 0.8 — minor overhead, acceptable |
| Error / unreadable plan | 0.5 — neutral fallback |

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

*Estimated for llama-3.3-70b-versatile.
Actual reproducible run: llama-3.1-8b-instant
achieved 0.948 avg (all 8 tasks). The 70b run
achieved 0.823 avg due to HAVING threshold
sensitivity on logic_missing_having.*

| Task | Score |
|---|---|
| syntax_missing_comma | 1.000 |
| syntax_ambiguous_column | 1.000 |
| logic_operator_precedence | 1.000 |
| logic_date_boundary | 0.580 |
| perf_n_plus_one | 1.000 |
| logic_window_partition | 1.000 |
| logic_missing_having | 0.000 |
| cascade_pipeline_bug | 1.000 |
| **Average** | **0.823** |
