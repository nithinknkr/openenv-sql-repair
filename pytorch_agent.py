"""
pytorch_agent.py
================
PyTorch DQN agent for SQL Auto-Repair environment.

Architecture:
  - Observation encoder: maps dict → 16-dim float tensor
  - DQN network: 16 → 64 → 64 → 4 (one Q-value per action)
  - Replay buffer: deque with random sampling
  - Training: epsilon-greedy exploration, MSE loss, Adam optimizer

Actions:
  0: view_schema
  1: view_error
  2: run_query    (uses broken_query as candidate)
  3: submit_query (uses broken_query as candidate)

Usage:
  from pytorch_agent import train_dqn
  model, rewards = train_dqn("http://localhost:7860", "syntax_missing_comma", n_episodes=10)
"""

from __future__ import annotations

import random
from collections import deque
from typing import List, Tuple, Optional

import torch
import torch.nn as nn
import torch.optim as optim
import httpx


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ACTIONS = ["view_schema", "view_error", "run_query", "submit_query"]
N_ACTIONS = len(ACTIONS)
INPUT_DIM = 16
HIDDEN_DIM = 64
GAMMA = 0.99          # discount factor
BATCH_SIZE = 32
BUFFER_CAPACITY = 2000
LR = 1e-3
EPS_START = 1.0
EPS_END = 0.05
EPS_DECAY = 0.90      # multiply epsilon by this each episode
REQUEST_TIMEOUT = 15  # seconds


# ---------------------------------------------------------------------------
# Observation encoder
# ---------------------------------------------------------------------------

def encode_observation(obs: dict) -> torch.Tensor:
    """
    Encode a SQLRepairObservation dict into a fixed-size float tensor.

    Features (16 dimensions):
      [0]  step_count / max_steps        — episode progress [0, 1]
      [1]  has execution_error           — 1.0 if last query failed
      [2]  has schema_info               — 1.0 if agent has seen schema
      [3]  has last_query_result         — 1.0 if last query returned rows
      [4]  difficulty encoding           — easy=0, medium=0.5, hard=1
      [5]  hints unlocked / total_hints  — proportion of hints visible
      [6]  is syntax task                — 1.0 if task_id contains "syntax"
      [7]  is logic task                 — 1.0 if task_id contains "logic"
      [8]  is perf task                  — 1.0 if task_id contains "perf"
      [9]  is cascade task               — 1.0 if task_id contains "cascade"
      [10] is first step                 — 1.0 if step_count == 0
      [11] is near max steps             — 1.0 if step_count >= max_steps - 2
      [12] result row count (clamped)    — min(len(rows), 50) / 50
      [13] error length (clamped)        — min(len(error), 200) / 200
      [14] broken_query length           — min(len(broken_query), 500) / 500
      [15] task_id hash (normalized)     — stable float fingerprint per task
    """
    diff_map = {"easy": 0.0, "medium": 0.5, "hard": 1.0}
    step_count  = obs.get("step_count", 0)
    max_steps   = max(obs.get("max_steps", 15), 1)
    hints       = obs.get("hints", [])
    total_hints = obs.get("total_hints", max(len(hints), 1))
    task_id     = obs.get("task_id", "")
    error       = obs.get("execution_error") or ""
    result      = obs.get("last_query_result") or []
    broken      = obs.get("broken_query", "")

    features = [
        step_count / max_steps,
        1.0 if error else 0.0,
        1.0 if obs.get("schema_info") else 0.0,
        1.0 if result else 0.0,
        diff_map.get(obs.get("difficulty", "easy").lower(), 0.0),
        len(hints) / max(total_hints, 1),
        1.0 if "syntax"  in task_id else 0.0,
        1.0 if "logic"   in task_id else 0.0,
        1.0 if "perf"    in task_id else 0.0,
        1.0 if "cascade" in task_id else 0.0,
        1.0 if step_count == 0 else 0.0,
        1.0 if step_count >= max_steps - 2 else 0.0,
        min(len(result), 50) / 50.0,
        min(len(error), 200) / 200.0,
        min(len(broken), 500) / 500.0,
        (hash(task_id) % 1000) / 1000.0,
    ]

    assert len(features) == INPUT_DIM
    return torch.FloatTensor(features)


# ---------------------------------------------------------------------------
# DQN Network
# ---------------------------------------------------------------------------

class SQLRepairDQN(nn.Module):
    """
    Simple 3-layer MLP Q-network.
    Maps observation features → Q-values for each action.
    """

    def __init__(
        self,
        input_dim: int = INPUT_DIM,
        hidden_dim: int = HIDDEN_DIM,
        n_actions: int = N_ACTIONS,
    ) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, n_actions),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


# ---------------------------------------------------------------------------
# Replay Buffer
# ---------------------------------------------------------------------------

class ReplayBuffer:
    """Experience replay buffer for DQN training."""

    def __init__(self, capacity: int = BUFFER_CAPACITY) -> None:
        self.buffer: deque = deque(maxlen=capacity)

    def push(
        self,
        state: torch.Tensor,
        action: int,
        reward: float,
        next_state: torch.Tensor,
        done: bool,
    ) -> None:
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size: int) -> List[Tuple]:
        return random.sample(self.buffer, batch_size)

    def __len__(self) -> int:
        return len(self.buffer)


# ---------------------------------------------------------------------------
# SQL query selection for run_query / submit_query actions
# ---------------------------------------------------------------------------

def _pick_sql(obs: dict, action_type: str) -> Optional[str]:
    """
    Pick the best candidate SQL for run_query or submit_query actions.

    Strategy (simple but effective for training):
    - If we have query results and no error, try the last attempted query
    - Otherwise fall back to the broken_query from the task
    """
    if action_type == "submit_query":
        # Only submit if we have a non-empty result from the last run
        if obs.get("last_query_result") and not obs.get("execution_error"):
            return obs.get("broken_query", "SELECT 1")
    return obs.get("broken_query", "SELECT 1")


# ---------------------------------------------------------------------------
# Training loop
# ---------------------------------------------------------------------------

def train_dqn(
    server_url: str,
    task_id: str,
    n_episodes: int = 10,
    lr: float = LR,
    verbose: bool = True,
) -> Tuple[SQLRepairDQN, List[float]]:
    """
    Train a DQN agent on a single SQL repair task.

    Args:
        server_url:  Base URL of the OpenEnv server (e.g. "http://localhost:7860")
        task_id:     Task ID to train on (e.g. "syntax_missing_comma")
        n_episodes:  Number of training episodes
        lr:          Learning rate for Adam optimizer
        verbose:     Whether to print per-episode progress

    Returns:
        (trained_model, list_of_episode_total_rewards)
    """
    model  = SQLRepairDQN()
    target = SQLRepairDQN()
    target.load_state_dict(model.state_dict())
    target.eval()

    optimizer = optim.Adam(model.parameters(), lr=lr)
    buffer    = ReplayBuffer()
    epsilon   = EPS_START
    rewards_per_episode: List[float] = []
    update_target_every = 5  # sync target network every N episodes

    for episode in range(n_episodes):
        # ── Reset environment ──────────────────────────────────────────
        try:
            resp = httpx.post(
                f"{server_url}/reset",
                json={"task_id": task_id},
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            obs = resp.json()
        except Exception as exc:
            print(f"[DQN] Episode {episode+1}: reset failed — {exc}")
            rewards_per_episode.append(0.0)
            continue

        session_id = obs["session_id"]
        done       = False
        ep_reward  = 0.0

        # ── Episode loop ───────────────────────────────────────────────
        while not done:
            state = encode_observation(obs)

            # Epsilon-greedy action selection
            if random.random() < epsilon:
                action_idx = random.randrange(N_ACTIONS)
            else:
                model.eval()
                with torch.no_grad():
                    q_values   = model(state.unsqueeze(0))
                    action_idx = q_values.argmax().item()
                model.train()

            action_type = ACTIONS[action_idx]
            action_dict: dict = {"action_type": action_type}
            if action_type in ("run_query", "submit_query"):
                action_dict["sql_query"] = _pick_sql(obs, action_type)

            # ── Step ───────────────────────────────────────────────────
            try:
                step_resp = httpx.post(
                    f"{server_url}/step",
                    params={"session_id": session_id},
                    json=action_dict,
                    timeout=REQUEST_TIMEOUT,
                )
                step_resp.raise_for_status()
                step_data = step_resp.json()
            except Exception as exc:
                print(f"[DQN] Step failed — {exc}")
                break

            next_obs   = step_data["observation"]
            reward     = float(step_data["reward"])
            done       = bool(step_data["done"])

            next_state = encode_observation(next_obs)
            buffer.push(state, action_idx, reward, next_state, done)

            obs        = next_obs
            ep_reward += reward

            # ── Training step ──────────────────────────────────────────
            if len(buffer) >= BATCH_SIZE:
                batch       = buffer.sample(BATCH_SIZE)
                states      = torch.stack([b[0] for b in batch])
                actions     = torch.tensor([b[1] for b in batch], dtype=torch.long)
                rewards_t   = torch.tensor([b[2] for b in batch], dtype=torch.float)
                next_states = torch.stack([b[3] for b in batch])
                dones_t     = torch.tensor([b[4] for b in batch], dtype=torch.float)

                # Current Q-values
                q_vals = model(states).gather(1, actions.unsqueeze(1)).squeeze()

                # Target Q-values (using frozen target network)
                with torch.no_grad():
                    next_q  = target(next_states).max(1).values
                    targets = rewards_t + GAMMA * next_q * (1.0 - dones_t)

                loss = nn.functional.mse_loss(q_vals, targets)
                optimizer.zero_grad()
                loss.backward()
                # Gradient clipping for stability
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                optimizer.step()

        # ── End of episode ─────────────────────────────────────────────
        epsilon = max(EPS_END, epsilon * EPS_DECAY)
        rewards_per_episode.append(round(ep_reward, 4))

        # Sync target network periodically
        if (episode + 1) % update_target_every == 0:
            target.load_state_dict(model.state_dict())

        if verbose:
            print(
                f"[DQN] episode={episode+1:3d}/{n_episodes}"
                f"  reward={ep_reward:+.4f}"
                f"  eps={epsilon:.3f}"
                f"  buffer={len(buffer)}"
            )

    return model, rewards_per_episode


# ---------------------------------------------------------------------------
# Save / load helpers
# ---------------------------------------------------------------------------

def save_model(model: SQLRepairDQN, path: str = "dqn_model.pt") -> None:
    torch.save(model.state_dict(), path)
    print(f"[DQN] Model saved to {path}")


def load_model(path: str = "dqn_model.pt") -> SQLRepairDQN:
    model = SQLRepairDQN()
    model.load_state_dict(torch.load(path, map_location="cpu"))
    model.eval()
    return model


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    task     = sys.argv[1] if len(sys.argv) > 1 else "syntax_missing_comma"
    episodes = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    model, rewards = train_dqn(
        server_url="http://localhost:7860",
        task_id=task,
        n_episodes=episodes,
    )
    print(f"\n[DQN] Training complete.")
    print(f"[DQN] Episode rewards: {rewards}")
    print(f"[DQN] Average reward:  {sum(rewards)/len(rewards):.4f}")
    save_model(model)
