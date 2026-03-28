# Completed Tasks (Up to Day 2)

## Day 1
- [x] Repository and folder structure created.
- [x] `openenv.yaml` manifest skeleton written.
- [x] `space.yaml` configurations defined (Docker SDK, port 7860).
- [x] Data models defined (`data/schema.sql` and `data/tasks.json`).
- [x] Seed data written completely deterministically.

## Day 2
- [x] OpenEnv-compliant Pydantic models implemented (`models.py`).
- [x] Client environment logic implemented (`client.py` using `EnvClient`).
- [x] Safety Sandbox built (`server/sandbox.py`) enforcing `:memory:` databases with SELECT-only allowlists.
- [x] Test framework foundation established (`tests/test_grader.py` covers 11 solid sandbox unit tests).

## Day 3
- [x] Minimal FastAPI server established (`server/app.py`) with `/health` endpoint.
- [x] Thread-safe `SessionManager` developed (`server/session_manager.py`).

## Day 4
- [x] Row-diff grader implemented (`server/grader.py`).
- [x] Core state machine scaffolded (`server/sql_repair_environment.py` `reset()` and `state()`).

## Day 5
- [x] Environment `step()` function complete with `view_schema`, `view_error`, `run_query`, and `submit_query`.
- [x] All rewards and penalties integrated (-0.01 per step, -0.05 repeat, -0.30 destructive, -0.20 loop, +0.70 submit).
