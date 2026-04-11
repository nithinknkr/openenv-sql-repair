"""
Simulates EXACTLY what the evaluator does:
  POST /reset  → POST /step (submit broken_query) → GET /grader
  Score must be strictly in (0.0, 1.0)
"""
import sys, time, json, httpx

BASE = "http://localhost:7860"

tasks = json.loads(open("data/tasks.json", encoding="utf-8").read())

# Wait for server
for _ in range(10):
    try:
        httpx.get(f"{BASE}/health", timeout=2).raise_for_status()
        break
    except:
        time.sleep(1)
else:
    print("ERROR: server not running on 7860")
    sys.exit(1)

print("=== EVALUATOR SIMULATION: reset + submit broken_query + grader ===\n")
fails = []

for t in tasks:
    tid = t["task_id"]
    broken = t["broken_query"]

    # 1. Reset
    r = httpx.post(f"{BASE}/reset", json={"task_id": tid}, timeout=10)
    if r.status_code != 200:
        print(f"[FAIL] {tid}: /reset returned {r.status_code}")
        fails.append(tid)
        continue
    session_id = r.json()["session_id"]

    # 2. Submit the broken query directly
    action = {"action_type": "submit_query", "sql_query": broken}
    r = httpx.post(f"{BASE}/step", params={"session_id": session_id}, json=action, timeout=10)
    if r.status_code != 200:
        print(f"[FAIL] {tid}: /step returned {r.status_code}")
        fails.append(tid)
        continue
    step_data = r.json()

    # 3. Get grader score
    r = httpx.get(f"{BASE}/grader", params={"session_id": session_id}, timeout=10)
    score = r.json().get("score", -1) if r.status_code == 200 else -1

    # Also get score from step result
    step_score = step_data.get("observation", {}).get("current_score", score)

    if score <= 0.0:
        status = "FAIL - score=0.0 (must be >0)"
        fails.append(tid)
    elif score >= 1.0:
        status = "FAIL - score=1.0 (must be <1)"
        fails.append(tid)
    else:
        status = "OK"

    marker = "[FAIL]" if "FAIL" in status else "[ OK ]"
    print(f"{marker} {tid:<32} grader_score={score:.4f}  {status}")

print()
if not fails:
    print("ALL 8 TASKS PASS - evaluator will accept")
else:
    print(f"FAILING TASKS ({len(fails)}): {fails}")
    sys.exit(1)
