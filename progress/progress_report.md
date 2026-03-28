# SQL Auto-Repair OpenEnv — Full Progress Report
*Last Updated: March 28, 2026 | Team: Q-Agents (Monish + Nithin)*

---

## 1. Executive Summary

| Phase | Status | Notes |
|---|---|---|
| Day 1 — Repo + Data Layer | ⚠️ Mostly Done | 1 manual step pending (HF Space creation) |
| Day 2 — Models + Sandbox | ✅ Complete | All files written and tests passing |
| Day 3 — Deploy Skeleton + Session Manager | 🔴 NOT STARTED | Today's priority |
| Day 4 — Environment Core + Grader | 🔴 NOT STARTED | Depends on Day 3 |
| Day 5+ | 🔴 NOT STARTED | — |

---

## 2. ✅ What Is Fully Completed (Days 1 & 2)

### 2.1 Configuration & DevOps Files
| File | Status | Notes |
|---|---|---|
| `pyproject.toml` | ✅ Done | All 6 dependencies correctly listed |
| `Dockerfile` | ✅ Done | python:3.11-slim, pip install ., EXPOSE 7860 |
| `space.yaml` | ✅ Done | sdk: docker, app_port: 7860, tags: [openenv] |
| `openenv.yaml` | ✅ Done | Full manifest with endpoints, action/obs spaces, 5 tasks, grader info |

### 2.2 Data Layer
| File | Status | Notes |
|---|---|---|
| `data/schema.sql` | ✅ Done | 5 tables (categories, products, users, orders, order_items), ~240 hardcoded rows |
| `data/tasks.json` | ✅ Done | All 5 tasks with broken_query, gold_query, hints, max_steps |
| `data/generate_gold.py` | ✅ Done (empty placeholder) | |

### 2.3 Core Python Models & Client
| File | Status | Notes |
|---|---|---|
| `models.py` | ✅ Done | SQLRepairAction, SQLRepairObservation, SQLRepairState, SQLRepairStepResult — all Pydantic v2 |
| `client.py` | ✅ Done | SQLRepairEnv(EnvClient), session_id auto-propagation, reset/step/state/close methods |
| `__init__.py` | ✅ Done | Exports all 4 models |

### 2.4 Sandbox (server/sandbox.py)
| Feature | Status |
|---|---|
| `:memory:` SQLite connection, `check_same_thread=False` | ✅ |
| Blocklist regex: DROP, DELETE, TRUNCATE, ALTER, CREATE, INSERT, UPDATE | ✅ |
| `safe_execute()` with 5-second threading.Timer timeout | ✅ |
| Returns `(result_rows, column_names, error_or_None)` | ✅ |
| `get_schema_text()` from sqlite_master | ✅ |
| `_load_schema()` runs schema.sql on init | ✅ |

### 2.5 Tests (tests/test_grader.py)
- 11 unit tests written and passing against `server/sandbox.py`
- Covers: all 7 blocklist keywords rejected, SELECT allowed, COUNT confirmed, syntax error handling, schema text retrieval

---

## 3. ⚠️ Pending Day 1 Item — MANUAL ACTION REQUIRED

### Create the HuggingFace Space (Cannot be done by code)

This is the **only remaining Day 1 item**. It requires your HuggingFace account:

1. Go to → https://huggingface.co/new-space
2. **Space name:** `openenv-sql-repair`
3. **SDK:** Select **Docker**
4. **Visibility:** Public
5. Click **Create Space**
6. Go to Space → **Settings** → **Variables and Secrets**
7. Add secret: Name = `OPENAI_API_KEY`, Value = your key
8. Connect your GitHub repo `nithinknkr/openenv-sql-repair` (Settings → Repository → Link GitHub repo)

Once this is done, every `git push` will automatically redeploy to the HF Space.

---

## 4. 🔴 Day 3 — Detailed Technical Plan (TODAY)

Day 3 has two objectives:
- **A. Stand up a minimal FastAPI server with `/health`** → deploy to HF Space immediately as insurance
- **B. Build the thread-safe SessionManager**

Both are independent and can be done in parallel by two people.

---

### Task A: Minimal FastAPI App (`server/app.py`)

**Why first?** We get a live HF Space URL responding HTTP 200 immediately. Even if everything else breaks, the Phase 1 gate is safe.

#### Technique: FastAPI + Uvicorn with application factory pattern

```
FastAPI()
  └── GET /health
        └── returns {"status": "ok", "version": "1.0.0"}
```

**What to write:**
```python
# server/app.py
from fastapi import FastAPI
app = FastAPI(title="SQL Auto-Repair OpenEnv", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}
```

**Then verify locally:**
```bash
pip install -e .
uvicorn server.app:app --port 7860
curl http://localhost:7860/health  # must return 200
```

**Then push to HF Space:**
```bash
git add server/app.py
git commit -m "feat: minimal /health endpoint"
git push
# HF Space auto-deploys in ~2 minutes
# Verify: curl https://your-space.hf.space/health
```

**Responsibility:** Monish

---

### Task B: Thread-Safe Session Manager (`server/session_manager.py`)

#### Why This Is Non-Trivial

When Phase 2 automated evaluation runs, the Nemotron agent fires parallel HTTP requests. If two `/reset` calls arrive simultaneously and both try to write to the same dict, you get a race condition — sessions overwrite each other, episodes corrupt silently. We use `threading.Lock()` to prevent this.

#### Technique 1: Dict + threading.Lock (Industry Standard)

```
_sessions: Dict[str, SQLRepairEnvironment]
_lock: threading.Lock()

Every read AND write to _sessions is wrapped in:
    with self._lock:
        ...
```

This is the simplest, most robust approach for FastAPI's multi-threaded Uvicorn workers. We do NOT use asyncio locks because our SQLite operations are synchronous.

#### Technique 2: UUID4 Session IDs

```python
import uuid
session_id = str(uuid.uuid4())
# Example: "3f8a2c9e-4b1d-4e7a-9f3c-1a2b3c4d5e6f"
```

UUID4 is random — statistically impossible to guess, no sequential patterns to exploit, no collisions at scale. This isolates every episode perfectly.

#### Technique 3: Daemon Thread for Stale Session Cleanup

```
threading.Thread(target=_cleanup_loop, daemon=True).start()
```

`daemon=True` means this cleanup thread dies automatically when the main process exits — no zombie threads. It runs every 60 seconds and evicts any session idle for 5+ minutes. This prevents memory leaks from abandoned episodes.

#### Full implementation to write:

```python
# server/session_manager.py
import threading
import time
import uuid
from typing import Dict, Optional

class SessionManager:
    def __init__(self):
        self._sessions: Dict[str, any] = {}         # session_id → env instance
        self._last_active: Dict[str, float] = {}    # session_id → last access timestamp
        self._lock = threading.Lock()               # guards both dicts
        
        # Start background cleanup daemon
        t = threading.Thread(target=self._cleanup_loop, daemon=True)
        t.start()

    def create_session(self, env) -> str:
        """Register a new environment instance, return its UUID session_id."""
        session_id = str(uuid.uuid4())
        with self._lock:
            self._sessions[session_id] = env
            self._last_active[session_id] = time.time()
        return session_id

    def get_session(self, session_id: str) -> Optional[any]:
        """Retrieve a session by ID, updating its last-active timestamp."""
        with self._lock:
            if session_id not in self._sessions:
                return None
            self._last_active[session_id] = time.time()
            return self._sessions[session_id]

    def delete_session(self, session_id: str) -> None:
        """Explicitly remove a session (e.g. on close)."""
        with self._lock:
            self._sessions.pop(session_id, None)
            self._last_active.pop(session_id, None)

    def cleanup_stale(self, max_age_seconds: int = 300) -> int:
        """Remove sessions idle for longer than max_age_seconds. Returns count evicted."""
        now = time.time()
        with self._lock:
            stale = [sid for sid, t in self._last_active.items()
                     if now - t > max_age_seconds]
            for sid in stale:
                self._sessions.pop(sid, None)
                self._last_active.pop(sid, None)
        return len(stale)

    def _cleanup_loop(self) -> None:
        """Background daemon: runs cleanup every 60 seconds forever."""
        while True:
            time.sleep(60)
            self.cleanup_stale()
```

**Unit test to write immediately after:**
```python
# tests/test_concurrency.py (partial)
def test_10_parallel_resets_give_distinct_ids():
    from concurrent.futures import ThreadPoolExecutor
    sm = SessionManager()
    ids = []
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = [pool.submit(sm.create_session, object()) for _ in range(10)]
        ids = [f.result() for f in futures]
    assert len(set(ids)) == 10  # all unique
```

**Responsibility:** Nithin

---

## 5. 🔴 Day 4 — Technical Plan (Tomorrow)

### Task A: Pure Grader Engine (`server/grader.py`)

#### Part 1: Row-Diff Grader (Tasks 1–4)

**Technique: Counter-based multiset comparison**

Instead of sorting both lists and comparing (fragile with NULLs), we use `collections.Counter`. This correctly handles duplicate rows and is O(n).

```
Steps:
1. _normalize() both submitted_rows and gold_rows
   - NULL → None (explicit)
   - int/float → float() (prevents 5 vs 5.0 mismatch)
   - str → str.strip().lower() (prevents whitespace/case mismatch)
   - None sorts last via "\x00" sentinel in sort key
2. Counter(gold_norm) → decrement for each matching submitted row
3. ratio = matched / len(gold_norm)
4. column_bonus = +0.10 if column names match exactly
5. return min(1.0, ratio + column_bonus)
```

**Edge case guards:**
- `if not gold_rows or not submitted_rows: return 0.0` (empty result = 0, no farming)
- Counter handles duplicate rows correctly (e.g. 3 identical rows in gold, agent finds 2 → ratio = 0.66)

#### Part 2: N+1 Efficiency Grader (Task 5 only)

**Technique: Proxy Pattern / Decorator Pattern**

```python
class ExecutionCountProxy:
    """Wraps a sqlite3 connection to count execute() calls."""
    def __init__(self, conn):
        self._conn = conn
        self.count = 0
    def execute(self, sql, params=()):
        self.count += 1
        return self._conn.execute(sql, params)
```

**Why this works for N+1 detection:**
- Correlated subquery: `SELECT ..., (SELECT COUNT(*) FROM orders WHERE user_id = u.id) FROM users`
  → executes once for outer query + N times for subquery = N+1 total
- Single JOIN: `SELECT ... FROM users LEFT JOIN orders ON ... GROUP BY ...`
  → executes exactly 1 time

**Efficiency scoring:**
```
count == 1    → efficiency = 1.0 (perfect single query)
count <= 3    → efficiency = 0.8 (acceptable — small overhead)
count <= 10   → efficiency = 0.5 (partial credit)
count > 10    → efficiency = 0.0 (N+1 pattern confirmed)
```

**Final score:**
```
final = (correctness × 0.6) + (efficiency × 0.4)
```

---

### Task B: Core Environment (`server/sql_repair_environment.py`)

**Technique: State Machine + Information Gating**

```
State:
  task: dict           # from tasks.json
  sandbox: SQLSandbox  # fresh :memory: DB
  step_count: int
  current_query: str   # last attempted query
  last_result: list    # rows from last run
  last_error: str      # last SQLite error
  history: list[str]   # ALL queries this episode
  total_reward: float
  is_done: bool
  current_score: float
```

**reset() contract:**
1. Load task by task_id (random if None given)
2. `SQLSandbox()` → fresh `:memory:` DB with schema loaded
3. Reset all state fields
4. Return `SQLRepairObservation` with `schema_info=None` ← information gating: agent MUST call view_schema

**step() dispatch:**
```
view_schema   → return schema DDL from sandbox.get_schema_text(), no reward
view_error    → return last_error from state, no reward
run_query     → sandbox.execute(sql), compute partial reward
submit_query  → sandbox.execute(sql), call grader, done=True
```

**Reward logic for run_query:**
```python
if blocklist hit → reward = -0.30
elif same as previous query → reward = -0.05
elif empty result → reward = 0.0
elif rows returned:
    partial = row_diff_grade(result, gold_rows)
    reward = 0.05 + (0.10 * partial)
reward += -0.01   # per-step tax always applies
```

**Loop detection (submit_query):**  
If `action.sql_query` appears 3+ times in `history` → additional -0.20 penalty before grading

---

## 6. File Status Summary

```
COMPLETED ✅                    EMPTY (TO BUILD) 🔴
-----------                     -----------------
pyproject.toml                  server/session_manager.py  ← Day 3 (TODAY)
Dockerfile                      server/app.py              ← Day 3 (TODAY)
space.yaml                      server/grader.py           ← Day 4
openenv.yaml                    server/sql_repair_environment.py  ← Day 4
data/schema.sql                 baseline/inference.py       ← Day 8
data/tasks.json                 tests/test_episode.py       ← Day 7
models.py                       tests/test_endpoints.py     ← Day 7
client.py                       tests/test_concurrency.py   ← Day 7
__init__.py
server/sandbox.py
tests/test_grader.py (sandbox tests)
```

---

## 7. Risk Flags

| Risk | Severity | Status |
|---|---|---|
| HF Space not created yet | 🔴 Critical | Pending manual action |
| `server/app.py` empty (no health endpoint) | 🔴 Critical | Fix TODAY |
| `server/session_manager.py` empty | 🔴 Critical | Fix TODAY |
| `server/grader.py` empty | 🟡 High | Fix Day 4 |
| `server/sql_repair_environment.py` empty | 🟡 High | Fix Day 4 |
| `baseline/inference.py` empty | 🟡 High | Fix Day 8 |
| `openenv` package not in `pyproject.toml` | 🔴 Critical | Must add before `openenv validate` runs |
