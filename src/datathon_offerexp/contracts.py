from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class DecisionRequest(BaseModel):
    event_id: str
    subject_key: str
    context: dict[str, Any] = Field(default_factory=dict)


class DecisionResponse(BaseModel):
    event_id: str
    arm_id: int
    arm_name: str
    policy_version: str
    reason_codes: list[str] = Field(default_factory=list)
    decided_at: datetime = Field(default_factory=datetime.utcnow)


class RewardUpdate(BaseModel):
    event_id: str
    arm_id: int
    reward: float


class ArmStats(BaseModel):
    arm_id: int
    arm_name: str
    trials: int
    successes: int
    reward_rate: float
    alpha: float
    beta: float


class PolicyStatsResponse(BaseModel):
    policy_version: str
    total_decisions: int
    arms: list[ArmStats]
