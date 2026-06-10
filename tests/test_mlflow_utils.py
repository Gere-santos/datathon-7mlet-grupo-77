import os
import tempfile

import pandas as pd
import pytest
import mlflow

from datathon_offerexp.mlflow_utils import (
    EXPERIMENT_NAME,
    get_or_create_experiment,
    log_policy_run,
    log_comparison_table,
)
from datathon_offerexp.policies import ThompsonSamplingPolicy, RandomPolicy
from datathon_offerexp.evaluation import replay_evaluate, compute_regret


@pytest.fixture(autouse=True)
def isolated_mlflow(tmp_path):
    """Cada teste usa banco SQLite isolado para não poluir o projeto."""
    db_path = tmp_path / "mlflow.db"
    uri = f"sqlite:///{db_path}"
    mlflow.set_tracking_uri(uri)
    yield
    mlflow.set_tracking_uri("sqlite:///mlruns/mlflow.db")


@pytest.fixture
def small_events():
    """DataFrame mínimo simulando offer_events para testes rápidos."""
    rows = []
    for i in range(400):
        arm_id = i % 4
        arm_names = ["sem_oferta", "educacao_financeira", "simulador_credito", "cartao_premium"]
        reward = 1 if (arm_id == 3 and i % 5 == 0) else 0
        rows.append({"arm_id": arm_id, "arm_name": arm_names[arm_id], "reward": reward})
    return pd.DataFrame(rows)


def test_get_or_create_experiment_creates():
    exp_id = get_or_create_experiment()
    assert exp_id is not None
    exp = mlflow.get_experiment_by_name(EXPERIMENT_NAME)
    assert exp is not None


def test_get_or_create_experiment_idempotent():
    id1 = get_or_create_experiment()
    id2 = get_or_create_experiment()
    assert id1 == id2


def test_log_policy_run_returns_run_id(small_events):
    policy = RandomPolicy()
    df = replay_evaluate(policy, small_events, seed=0)
    df = compute_regret(df, best_arm_rate=0.1)

    run_id = log_policy_run(
        policy_name="Random",
        policy_version=policy.version,
        eval_df=df,
        best_arm_rate=0.1,
        best_arm_name="cartao_premium",
        n_events=len(small_events),
        seed=0,
    )
    assert isinstance(run_id, str) and len(run_id) > 0


def test_log_policy_run_records_metrics(small_events):
    policy = ThompsonSamplingPolicy(seed=42)
    df = replay_evaluate(policy, small_events, seed=42)
    df = compute_regret(df, best_arm_rate=0.1)

    run_id = log_policy_run(
        policy_name="Thompson Sampling",
        policy_version=policy.version,
        eval_df=df,
        best_arm_rate=0.1,
        best_arm_name="cartao_premium",
        n_events=len(small_events),
        seed=42,
    )

    run = mlflow.get_run(run_id)
    metrics = run.data.metrics
    assert "avg_reward" in metrics
    assert "final_regret" in metrics
    assert "rounds" in metrics
    assert "best_arm_pct" in metrics


def test_log_policy_run_records_params(small_events):
    policy = RandomPolicy()
    df = replay_evaluate(policy, small_events, seed=0)
    df = compute_regret(df, best_arm_rate=0.1)

    run_id = log_policy_run(
        policy_name="Random",
        policy_version=policy.version,
        eval_df=df,
        best_arm_rate=0.1,
        best_arm_name="cartao_premium",
        n_events=len(small_events),
        seed=0,
        extra_params={"custom_param": "test_value"},
    )

    run = mlflow.get_run(run_id)
    assert run.data.params.get("custom_param") == "test_value"
    assert run.data.params.get("policy") == "Random"


def test_log_policy_run_empty_df():
    run_id = log_policy_run(
        policy_name="Empty",
        policy_version="v0",
        eval_df=pd.DataFrame(),
        best_arm_rate=0.1,
        best_arm_name="cartao_premium",
        n_events=0,
    )
    run = mlflow.get_run(run_id)
    assert run.data.metrics.get("rounds") == 0


def test_log_comparison_table():
    rows = [
        {"policy": "Random", "avg_reward": 0.11, "rounds": 1000},
        {"policy": "Thompson", "avg_reward": 0.12, "rounds": 1000},
    ]
    get_or_create_experiment()
    exp_id = mlflow.get_experiment_by_name(EXPERIMENT_NAME).experiment_id
    with mlflow.start_run(experiment_id=exp_id):
        log_comparison_table(rows)
