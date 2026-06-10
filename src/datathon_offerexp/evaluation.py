from __future__ import annotations

import pandas as pd
import numpy as np

from datathon_offerexp.policies import BasePolicy


def replay_evaluate(
    policy: BasePolicy,
    events: pd.DataFrame,
    arm_col: str = "arm_id",
    reward_col: str = "reward",
    seed: int | None = 42,
) -> pd.DataFrame:
    """Offline policy evaluation via the replayer method.

    Only counts rounds where the policy's selected arm matches the logged arm,
    ensuring unbiased reward estimation from logged data.
    """
    if seed is not None:
        import random, numpy as np
        random.seed(seed)
        np.random.seed(seed)

    records = []
    cumulative_reward = 0.0
    matched = 0

    for _, row in events.iterrows():
        selected = policy.select_arm()
        logged_arm = int(row[arm_col])

        if selected == logged_arm:
            reward = float(row[reward_col])
            policy.update(selected, reward)
            cumulative_reward += reward
            matched += 1
            records.append(
                {
                    "round": matched,
                    "arm_id": selected,
                    "arm_name": row["arm_name"] if "arm_name" in row else str(selected),
                    "reward": reward,
                    "cumulative_reward": cumulative_reward,
                    "avg_reward": cumulative_reward / matched,
                }
            )

    return pd.DataFrame(records)


def compute_regret(
    eval_df: pd.DataFrame,
    best_arm_rate: float,
) -> pd.DataFrame:
    """Adds cumulative regret column to an evaluation DataFrame."""
    df = eval_df.copy()
    df["expected_best"] = best_arm_rate * df["round"]
    df["cumulative_regret"] = df["expected_best"] - df["cumulative_reward"]
    return df


def summarize(eval_df: pd.DataFrame, policy_name: str) -> dict:
    if eval_df.empty:
        return {"policy": policy_name, "rounds": 0, "avg_reward": 0.0, "total_reward": 0.0}
    return {
        "policy": policy_name,
        "rounds": len(eval_df),
        "avg_reward": round(eval_df["avg_reward"].iloc[-1], 4),
        "total_reward": round(eval_df["cumulative_reward"].iloc[-1], 2),
    }
