"""Test suites for concurrency and session isolation in OpenEnv."""

import threading
import time
import uuid
from typing import List, Tuple
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from server.app import app, session_manager


client = TestClient(app)


# ============================================================================
# Test: Parallel reset
# ============================================================================

def test_parallel_reset_ten_simultaneous_requests():
    """
    Fire 10 simultaneous POST /reset requests using threading.Thread.
    Verify all 10 return distinct session_id values and all 10 sessions are independently usable.
    """
    session_ids: List[str] = []
    errors: List[str] = []
    lock = threading.Lock()
    
    def make_reset_request():
        try:
            response = client.post("/reset")
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            data = response.json()
            assert "session_id" in data, "Missing session_id in response"
            
            with lock:
                session_ids.append(data["session_id"])
        except Exception as e:
            with lock:
                errors.append(str(e))
    
    # Create 10 threads
    threads = [threading.Thread(target=make_reset_request) for _ in range(10)]
    
    # Start all threads
    for t in threads:
        t.start()
    
    # Wait for all threads to complete
    for t in threads:
        t.join(timeout=10)
    
    # Verify results
    assert len(errors) == 0, f"Errors occurred: {errors}"
    assert len(session_ids) == 10, f"Expected 10 sessions, got {len(session_ids)}"
    
    # Verify all session IDs are unique
    unique_ids = set(session_ids)
    assert len(unique_ids) == 10, "Session IDs should be unique"


def test_parallel_reset_all_sessions_independent():
    """
    Test that 10 parallel reset requests result in independently usable sessions.
    Each session can be stepped independently without interference.
    """
    session_ids: List[str] = []
    errors: List[str] = []
    lock = threading.Lock()
    
    def make_reset_request():
        try:
            response = client.post("/reset")
            assert response.status_code == 200
            session_ids.append(response.json()["session_id"])
        except Exception as e:
            with lock:
                errors.append(str(e))
    
    # Create sessions in parallel
    threads = [threading.Thread(target=make_reset_request) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)
    
    assert len(errors) == 0
    assert len(session_ids) == 10
    
    # Now verify each session is independently usable — step each one
    def step_session(session_id: str):
        try:
            action = {"action_type": "view_schema"}
            response = client.post(f"/step?session_id={session_id}", json=action)
            assert response.status_code == 200, f"Step failed for {session_id}: {response.status_code}"
        except Exception as e:
            with lock:
                errors.append(f"Step error for {session_id}: {str(e)}")
    
    step_threads = [threading.Thread(target=step_session, args=(sid,)) for sid in session_ids]
    for t in step_threads:
        t.start()
    for t in step_threads:
        t.join(timeout=10)
    
    assert len(errors) == 0, f"Errors during stepping: {errors}"


# ============================================================================
# Test: Cross-session isolation
# ============================================================================

def test_cross_session_isolation():
    """
    Create sessions S1 (task A) and S2 (task B).
    Step S1 five times.
    Verify S2 still shows step_count == 0 and returns task B's broken query.
    """
    # Create session S1 with task A
    reset_s1 = client.post("/reset", params={"task_id": "syntax_missing_comma"})
    session_id_s1 = reset_s1.json()["session_id"]
    task_id_s1 = reset_s1.json()["task_id"]
    
    # Create session S2 with task B
    reset_s2 = client.post("/reset", params={"task_id": "syntax_ambiguous_column"})
    session_id_s2 = reset_s2.json()["session_id"]
    task_id_s2 = reset_s2.json()["task_id"]
    broken_query_s2 = reset_s2.json()["broken_query"]
    
    # Verify they are different tasks
    assert task_id_s1 == "syntax_missing_comma"
    assert task_id_s2 == "syntax_ambiguous_column"
    assert task_id_s1 != task_id_s2
    
    # Step S1 five times
    for i in range(5):
        action = {"action_type": "view_schema"}
        response = client.post(f"/step?session_id={session_id_s1}", json=action)
        assert response.status_code == 200
    
    # Verify S1 has step_count == 5
    state_s1 = client.get(f"/state?session_id={session_id_s1}").json()
    assert state_s1["step_count"] == 5
    
    # Verify S2 still has step_count == 0 (isolated)
    state_s2 = client.get(f"/state?session_id={session_id_s2}").json()
    assert state_s2["step_count"] == 0, "S2 should not be affected by S1's steps"
    
    # Verify S2 still has its original task
    obs_s2 = client.get(f"/state?session_id={session_id_s2}").json()
    assert obs_s2["task_id"] == "syntax_ambiguous_column"
    
    # Verify S2's observation still shows broken_query from task B
    step_s2 = client.post(
        f"/step?session_id={session_id_s2}",
        json={"action_type": "view_error"}
    ).json()
    obs_s2_after = step_s2["observation"]
    assert obs_s2_after["broken_query"] == broken_query_s2


# ============================================================================
# Test: Stale session cleanup
# ============================================================================

def test_stale_session_cleanup():
    """
    Create a session, mock last_activity to 6 minutes ago,
    trigger cleanup, verify the session is evicted and a subsequent
    GET /state?session_id=<evicted> returns 404.
    """
    # Create a session
    reset_response = client.post("/reset")
    session_id = reset_response.json()["session_id"]
    
    # Verify session exists
    state_response = client.get(f"/state?session_id={session_id}")
    assert state_response.status_code == 200, "Session should exist initially"
    
    # Mock last_activity to 6 minutes ago (360 seconds)
    # Lock the session manager and modify timestamps
    with session_manager._lock:
        current_time = time.time()
        session_manager._last_active[session_id] = current_time - 360  # 6 minutes ago
    
    # Trigger cleanup with max_age_seconds=300 (5 minutes)
    evicted_count = session_manager.cleanup_stale(max_age_seconds=300)
    assert evicted_count > 0, "At least one session should have been evicted"
    
    # Verify the session is now gone
    state_response = client.get(f"/state?session_id={session_id}")
    assert state_response.status_code == 404, "Session should be evicted"
    data = state_response.json()
    assert "detail" in data


def test_stale_session_cleanup_preserves_fresh_sessions():
    """
    Test that cleanup does not evict fresh sessions while removing stale ones.
    """
    # Create a fresh session
    fresh_response = client.post("/reset")
    fresh_session_id = fresh_response.json()["session_id"]
    
    # Create a stale session
    stale_response = client.post("/reset")
    stale_session_id = stale_response.json()["session_id"]
    
    # Mock stale session to 6 minutes ago
    with session_manager._lock:
        current_time = time.time()
        session_manager._last_active[stale_session_id] = current_time - 360
    
    # Trigger cleanup
    evicted_count = session_manager.cleanup_stale(max_age_seconds=300)
    assert evicted_count >= 1
    
    # Verify fresh session still exists
    fresh_state = client.get(f"/state?session_id={fresh_session_id}")
    assert fresh_state.status_code == 200, "Fresh session should still exist"
    
    # Verify stale session is gone
    stale_state = client.get(f"/state?session_id={stale_session_id}")
    assert stale_state.status_code == 404, "Stale session should be evicted"


# ============================================================================
# Additional concurrency tests
# ============================================================================

def test_parallel_steps_same_session_thread_safe():
    """
    Test that taking steps in the same session from multiple threads is thread-safe.
    """
    reset_response = client.post("/reset")
    session_id = reset_response.json()["session_id"]
    
    errors: List[str] = []
    step_results: List[int] = []
    lock = threading.Lock()
    
    def take_step():
        try:
            action = {"action_type": "view_error"}
            response = client.post(f"/step?session_id={session_id}", json=action)
            assert response.status_code == 200
            with lock:
                step_results.append(response.status_code)
        except Exception as e:
            with lock:
                errors.append(str(e))
    
    # Take 5 steps from 5 different threads on the same session
    threads = [threading.Thread(target=take_step) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)
    
    assert len(errors) == 0, f"Errors: {errors}"
    assert len(step_results) == 5
    
    # Verify step_count is 5 (all steps were applied)
    state_response = client.get(f"/state?session_id={session_id}")
    assert state_response.status_code == 200
    state = state_response.json()
    assert state["step_count"] == 5


def test_session_isolation_with_different_task_ids():
    """
    Test that creating 8 sessions with different task IDs keeps them isolated.
    """
    task_ids = [
        "syntax_missing_comma",
        "syntax_ambiguous_column",
        "logic_operator_precedence",
        "logic_date_boundary",
        "perf_n_plus_one",
        "logic_window_partition",
        "logic_missing_having",
        "cascade_pipeline_bug",
    ]
    
    sessions = {}
    for task_id in task_ids:
        response = client.post("/reset", params={"task_id": task_id})
        assert response.status_code == 200
        data = response.json()
        sessions[task_id] = {
            "session_id": data["session_id"],
            "task_id": data["task_id"],
            "broken_query": data["broken_query"],
        }
    
    # Verify each session has its correct task
    for task_id, session_info in sessions.items():
        state = client.get(f"/state?session_id={session_info['session_id']}").json()
        assert state["task_id"] == task_id, f"Task {task_id} mismatch"


# ============================================================================
# Stress tests
# ============================================================================

def test_stress_100_sequential_resets():
    """Stress test: Create 100 sessions sequentially and verify all are valid."""
    session_ids = []
    for _ in range(100):
        response = client.post("/reset")
        assert response.status_code == 200
        session_ids.append(response.json()["session_id"])
    
    # Verify all are unique
    assert len(set(session_ids)) == 100
    
    # Spot check: verify a few sessions are still accessible
    for session_id in session_ids[::10]:  # Check every 10th
        state = client.get(f"/state?session_id={session_id}")
        assert state.status_code == 200


def test_stress_parallel_mixed_operations():
    """
    Stress test: Mix of parallel resets, steps, and state checks.
    """
    errors: List[str] = []
    lock = threading.Lock()
    session_ids = []
    
    def mixed_operations(task_num: int):
        try:
            # Reset
            reset_response = client.post("/reset")
            assert reset_response.status_code == 200
            session_id = reset_response.json()["session_id"]
            
            with lock:
                session_ids.append(session_id)
            
            # Step
            step_response = client.post(
                f"/step?session_id={session_id}",
                json={"action_type": "view_schema"}
            )
            assert step_response.status_code == 200
            
            # Get state
            state_response = client.get(f"/state?session_id={session_id}")
            assert state_response.status_code == 200
            
        except Exception as e:
            with lock:
                errors.append(f"Task {task_num}: {str(e)}")
    
    threads = [threading.Thread(target=mixed_operations, args=(i,)) for i in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=20)
    
    assert len(errors) == 0, f"Errors: {errors}"
    assert len(session_ids) == 20
