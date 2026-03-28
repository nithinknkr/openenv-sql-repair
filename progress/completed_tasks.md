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
