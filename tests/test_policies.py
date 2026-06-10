import pytest
from datathon_offerexp.policies import GreedyPolicy, RandomPolicy, ThompsonSamplingPolicy


def test_random_policy_returns_valid_arm():
    policy = RandomPolicy()
    for _ in range(50):
        arm = policy.select_arm()
        assert 0 <= arm < policy.n_arms


def test_greedy_policy_prefers_best_arm():
    policy = GreedyPolicy()
    # Simulate arm 2 having a much better reward rate
    for _ in range(20):
        policy.update(2, 1.0)
    for _ in range(20):
        policy.update(0, 0.0)
        policy.update(1, 0.0)
        policy.update(3, 0.0)

    assert policy.select_arm() == 2


def test_greedy_policy_breaks_ties_by_least_explored():
    policy = GreedyPolicy()
    # All arms at rate=0 initially; arm 0 has 1 trial, arm 1 has none
    policy.update(0, 0.0)
    # Arm 1 has 0 trials → should be chosen (least explored among tied arms)
    selected = policy.select_arm()
    assert selected in {1, 2, 3}


def test_thompson_sampling_returns_valid_arm():
    policy = ThompsonSamplingPolicy(seed=0)
    for _ in range(50):
        arm = policy.select_arm()
        assert 0 <= arm < policy.n_arms


def test_thompson_sampling_converges_to_best_arm():
    policy = ThompsonSamplingPolicy(seed=42)
    # Arm 1 has clear dominance
    for _ in range(200):
        policy.update(1, 1.0)
    for _ in range(200):
        policy.update(0, 0.0)
        policy.update(2, 0.0)
        policy.update(3, 0.0)

    selections = [policy.select_arm() for _ in range(100)]
    assert selections.count(1) > 80


def test_update_increments_trials_and_successes():
    policy = ThompsonSamplingPolicy()
    policy.update(0, 1.0)
    policy.update(0, 0.0)
    assert policy.trials[0] == 2
    assert policy.successes[0] == 1


def test_stats_returns_correct_structure():
    policy = ThompsonSamplingPolicy()
    policy.update(0, 1.0)
    s = policy.stats()
    assert len(s) == 4
    assert all("arm_id" in r and "reward_rate" in r and "alpha" in r for r in s)
