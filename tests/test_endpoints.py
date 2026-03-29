"""Test suites for OpenEnv API endpoints."""

import pytest
from fastapi.testclient import TestClient
from server.app import app


client = TestClient(app)


# ============================================================================
# Test: GET /health
# ============================================================================

def test_health_endpoint():
    """Test GET /health returns 200 with correct schema."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "ok", "version": "1.0.0"}


# ============================================================================
# Test: POST /reset
# ============================================================================

def test_reset_endpoint_creates_session():
    """Test POST /reset returns 200 with session_id field."""
    response = client.post("/reset")
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data, "Response should contain session_id"
    assert isinstance(data["session_id"], str)
    assert len(data["session_id"]) > 0


def test_reset_endpoint_returns_observation():
    """Test POST /reset returns a valid SQLRepairObservation."""
    response = client.post("/reset")
    assert response.status_code == 200
    data = response.json()
    
    # Check required observation fields
    required_fields = [
        "session_id",
        "task_id",
        "difficulty",
        "description",
        "broken_query",
        "schema_info",
        "step_count",
        "max_steps",
    ]
    for field in required_fields:
        assert field in data, f"Missing field: {field}"


def test_reset_endpoint_with_specific_task():
    """Test POST /reset with a specific task_id."""
    response = client.post("/reset", params={"task_id": "syntax_missing_comma"})
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == "syntax_missing_comma"


# ============================================================================
# Test: GET /tasks
# ============================================================================

def test_tasks_endpoint_returns_five_tasks():
    """Test GET /tasks returns exactly 5 tasks."""
    response = client.get("/tasks")
    assert response.status_code == 200
    data = response.json()
    assert "tasks" in data
    assert isinstance(data["tasks"], list)
    assert len(data["tasks"]) == 5, "Should return exactly 5 tasks"
    assert data["count"] == 5


def test_tasks_endpoint_schema_structure():
    """Test GET /tasks response includes action_schema."""
    response = client.get("/tasks")
    assert response.status_code == 200
    data = response.json()
    
    # Check action_schema exists
    assert "action_schema" in data
    assert "fields" in data["action_schema"]
    assert "action_type" in data["action_schema"]["fields"]


def test_tasks_endpoint_all_tasks_present():
    """Verify all 5 required task IDs are present."""
    response = client.get("/tasks")
    assert response.status_code == 200
    data = response.json()
    
    task_ids = {task["task_id"] for task in data["tasks"]}
    expected_task_ids = {
        "syntax_missing_comma",
        "syntax_ambiguous_column",
        "logic_wrong_join",
        "logic_wrong_aggregation",
        "perf_n_plus_one",
    }
    assert task_ids == expected_task_ids


# ============================================================================
# Test: POST /step with valid session
# ============================================================================

def test_step_endpoint_run_query():
    """Test POST /step with run_query action returns 200 and StepResult schema."""
    # First, reset to get a session
    reset_response = client.post("/reset")
    session_id = reset_response.json()["session_id"]
    
    # Now step with a run_query action
    action = {
        "action_type": "run_query",
        "sql_query": "SELECT * FROM users LIMIT 1;",
    }
    response = client.post(f"/step?session_id={session_id}", json=action)
    assert response.status_code == 200
    data = response.json()
    
    # Check StepResult schema
    assert "observation" in data
    assert "reward" in data
    assert "done" in data


def test_step_endpoint_view_schema():
    """Test POST /step with view_schema action."""
    reset_response = client.post("/reset")
    session_id = reset_response.json()["session_id"]
    
    action = {"action_type": "view_schema"}
    response = client.post(f"/step?session_id={session_id}", json=action)
    assert response.status_code == 200
    data = response.json()
    
    # Verify observation
    assert "observation" in data
    obs = data["observation"]
    assert "schema_info" in obs


def test_step_result_observation_schema():
    """Test that StepResult observation matches SQLRepairObservation schema."""
    reset_response = client.post("/reset")
    session_id = reset_response.json()["session_id"]
    
    action = {"action_type": "view_error"}
    response = client.post(f"/step?session_id={session_id}", json=action)
    assert response.status_code == 200
    data = response.json()
    
    obs = data["observation"]
    required_obs_fields = [
        "session_id",
        "task_id",
        "difficulty",
        "description",
        "broken_query",
        "step_count",
        "max_steps",
        "available_actions",
    ]
    for field in required_obs_fields:
        assert field in obs, f"Missing observation field: {field}"


# ============================================================================
# Test: GET /state with valid session
# ============================================================================

def test_state_endpoint_returns_sql_repair_state():
    """Test GET /state returns 200 and matches SQLRepairState schema."""
    reset_response = client.post("/reset")
    session_id = reset_response.json()["session_id"]
    
    response = client.get(f"/state?session_id={session_id}")
    assert response.status_code == 200
    data = response.json()
    
    # Check SQLRepairState required fields
    required_fields = [
        "episode_id",
        "session_id",
        "step_count",
        "task_id",
        "is_done",
        "current_score",
    ]
    for field in required_fields:
        assert field in data, f"Missing state field: {field}"


def test_state_endpoint_reflects_steps():
    """Test that GET /state reflects step_count after stepping."""
    reset_response = client.post("/reset")
    session_id = reset_response.json()["session_id"]
    
    # Initial state
    state_response = client.get(f"/state?session_id={session_id}")
    initial_step_count = state_response.json()["step_count"]
    assert initial_step_count == 0
    
    # Take a step
    action = {"action_type": "view_schema"}
    client.post(f"/step?session_id={session_id}", json=action)
    
    # Check state again
    state_response = client.get(f"/state?session_id={session_id}")
    updated_step_count = state_response.json()["step_count"]
    assert updated_step_count == 1


# ============================================================================
# Test: Error cases
# ============================================================================

def test_step_endpoint_with_unknown_session_returns_404():
    """Test POST /step with unknown session_id returns 404."""
    unknown_uuid = "00000000-0000-0000-0000-000000000000"
    action = {"action_type": "view_schema"}
    response = client.post(f"/step?session_id={unknown_uuid}", json=action)
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


def test_state_endpoint_with_unknown_session_returns_404():
    """Test GET /state with unknown session_id returns 404."""
    unknown_uuid = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/state?session_id={unknown_uuid}")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


# ============================================================================
# Integration test: Full episode flow
# ============================================================================

def test_full_episode_flow():
    """Test a complete episode: reset → view schema → step → state."""
    # Reset
    reset_response = client.post("/reset", params={"task_id": "syntax_missing_comma"})
    assert reset_response.status_code == 200
    session_id = reset_response.json()["session_id"]
    
    # View schema
    action1 = {"action_type": "view_schema"}
    step1_response = client.post(f"/step?session_id={session_id}", json=action1)
    assert step1_response.status_code == 200
    
    # Run a query
    action2 = {
        "action_type": "run_query",
        "sql_query": "SELECT id, username, email FROM users;",
    }
    step2_response = client.post(f"/step?session_id={session_id}", json=action2)
    assert step2_response.status_code == 200
    
    # Check state
    state_response = client.get(f"/state?session_id={session_id}")
    assert state_response.status_code == 200
    state_data = state_response.json()
    assert state_data["step_count"] == 2
    assert state_data["task_id"] == "syntax_missing_comma"
