import pytest

from models import SQLRepairAction, ActionType
from server.sql_repair_environment import SQLRepairEnvironment, _TASKS


def test_full_episode_submit_query_marks_done():
    env = SQLRepairEnvironment()
    obs = env.reset(task_id="syntax_missing_comma", session_id="sess-1")
    assert obs.step_count == 0

    # some agent actions (not strictly needed)
    env.step(SQLRepairAction(action_type=ActionType.view_schema))
    env.step(SQLRepairAction(action_type=ActionType.view_error))

    result = env.step(
        SQLRepairAction(action_type=ActionType.submit_query, sql_query=_TASKS["syntax_missing_comma"]["gold_query"])
    )
    assert result.done is True
    assert env.state().is_done is True
    assert env.state().step_count == 3


def test_max_steps_enforced_marks_done_when_exceeded():
    env = SQLRepairEnvironment()
    env.reset(task_id="syntax_missing_comma")
    max_steps = env.task["max_steps"]

    for i in range(max_steps):
        result = env.step(SQLRepairAction(action_type=ActionType.view_schema))
        if i < max_steps - 1:
            assert not result.done

    # final step should mark done
    assert env.state().step_count == max_steps
    assert env.state().is_done is True


def test_reset_clears_previous_episode_state():
    env = SQLRepairEnvironment()
    env.reset(task_id="syntax_missing_comma")
    env.step(SQLRepairAction(action_type=ActionType.view_schema))
    env.step(SQLRepairAction(action_type=ActionType.run_query, sql_query="SELECT 1;"))
    env.step(SQLRepairAction(action_type=ActionType.view_error))

    # enforce state changed
    assert env.step_count > 0
    assert env.last_result is not None

    env.reset(task_id="syntax_missing_comma")

    assert env.step_count == 0
    assert env.last_result == []
    assert env.last_cols == []
    assert env.is_done is False
    assert env.total_reward == 0.0


def test_destructive_penalty_for_drop_table():
    env = SQLRepairEnvironment()
    env.reset(task_id="syntax_missing_comma")

    result = env.step(SQLRepairAction(action_type=ActionType.run_query, sql_query="DROP TABLE users;"))
    assert result.reward <= -0.30
    assert result.reward == -0.31
    assert "Blocked" in (env.last_error or "")


def test_infinite_loop_penalty_submit_same_query_three_times():
    env = SQLRepairEnvironment()
    env.reset(task_id="syntax_missing_comma")
    gold_sql = _TASKS["syntax_missing_comma"]["gold_query"]

    r1 = env._handle_submit_query(gold_sql)
    r2 = env._handle_submit_query(gold_sql)
    r3 = env._handle_submit_query(gold_sql)

    assert r1 > 0
    assert r2 > 0
    assert r3 < r2
    assert r3 == pytest.approx(0.5, abs=1e-6) or r3 <= 0.5


def test_empty_query_guard_select_one_no_partial_progress_reward():
    env = SQLRepairEnvironment()
    env.reset(task_id="syntax_missing_comma")

    result = env.step(SQLRepairAction(action_type=ActionType.run_query, sql_query="SELECT 1;"))
    # row_diff should not produce partial reward for a generic constant query
    assert pytest.approx(result.reward, rel=1e-6) == 0.04


def test_reward_accumulation_equals_per_step_sum():
    env = SQLRepairEnvironment()
    env.reset(task_id="syntax_missing_comma")

    rewards = []
    actions = [
        SQLRepairAction(action_type=ActionType.view_schema),
        SQLRepairAction(action_type=ActionType.run_query, sql_query="SELECT 1;"),
        SQLRepairAction(action_type=ActionType.view_error),
    ]

    for action in actions:
        result = env.step(action)
        rewards.append(result.reward)

    assert env.total_reward == pytest.approx(sum(rewards), abs=1e-6)
