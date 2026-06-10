import pytest
from pydantic import ValidationError
from datathon_offerexp.contracts import (
    ArmStats,
    DecisionRequest,
    DecisionResponse,
    PolicyStatsResponse,
    RewardUpdate,
)


def test_decision_request_defaults():
    req = DecisionRequest(event_id="evt_001", subject_key="sub_001")
    assert req.context == {}


def test_decision_request_with_context():
    req = DecisionRequest(event_id="e1", subject_key="s1", context={"idade": 35})
    assert req.context["idade"] == 35


def test_decision_response_has_timestamp():
    resp = DecisionResponse(
        event_id="e1",
        arm_id=2,
        arm_name="simulador_credito",
        policy_version="thompson-v1",
    )
    assert resp.decided_at is not None
    assert resp.reason_codes == []


def test_reward_update_fields():
    upd = RewardUpdate(event_id="e1", arm_id=1, reward=1.0)
    assert upd.reward == 1.0


def test_reward_update_requires_all_fields():
    with pytest.raises(ValidationError):
        RewardUpdate(event_id="e1", reward=1.0)  # missing arm_id


def test_arm_stats_fields():
    s = ArmStats(
        arm_id=0,
        arm_name="sem_oferta",
        trials=10,
        successes=2,
        reward_rate=0.2,
        alpha=3.0,
        beta=9.0,
    )
    assert s.reward_rate == 0.2


def test_policy_stats_response():
    arms = [
        ArmStats(arm_id=i, arm_name=f"arm_{i}", trials=0, successes=0,
                 reward_rate=0.0, alpha=1.0, beta=1.0)
        for i in range(4)
    ]
    resp = PolicyStatsResponse(policy_version="thompson-v1", total_decisions=0, arms=arms)
    assert len(resp.arms) == 4
