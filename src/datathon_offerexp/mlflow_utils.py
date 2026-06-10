from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import mlflow
import pandas as pd

EXPERIMENT_NAME = "offerexp-bandits"

# MLflow 3.x requer backend de banco de dados. SQLite local é o padrão para desenvolvimento.
DEFAULT_TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI",
    "sqlite:///mlruns/mlflow.db",
)


def configure_tracking(tracking_uri: str | None = None) -> None:
    """Sets the MLflow tracking URI. Call once at application/notebook startup."""
    uri = tracking_uri or DEFAULT_TRACKING_URI
    Path("mlruns").mkdir(exist_ok=True)
    mlflow.set_tracking_uri(uri)


def get_or_create_experiment() -> str:
    """Returns the MLflow experiment ID, creating it if needed."""
    experiment = mlflow.get_experiment_by_name(EXPERIMENT_NAME)
    if experiment is None:
        return mlflow.create_experiment(
            EXPERIMENT_NAME,
            tags={"project": "datathon-7mlet", "grupo": "77"},
        )
    return experiment.experiment_id


def log_policy_run(
    policy_name: str,
    policy_version: str,
    eval_df: pd.DataFrame,
    best_arm_rate: float,
    best_arm_name: str,
    n_events: int,
    seed: int = 42,
    extra_params: dict[str, Any] | None = None,
    artifacts_dir: str | Path | None = None,
) -> str:
    """Logs a complete bandit policy evaluation run to MLflow.

    Returns the run_id.
    """
    exp_id = get_or_create_experiment()

    with mlflow.start_run(experiment_id=exp_id, run_name=policy_name) as run:
        # --- Parâmetros ---
        params = {
            "policy": policy_name,
            "policy_version": policy_version,
            "seed": seed,
            "n_arms": 4,
            "n_events_total": n_events,
            "oracle_best_arm": best_arm_name,
            "oracle_best_arm_rate": round(best_arm_rate, 4),
        }
        if extra_params:
            params.update(extra_params)
        mlflow.log_params(params)

        # --- Métricas finais ---
        if not eval_df.empty:
            best_arm_pct = round((eval_df["arm_name"] == best_arm_name).mean() * 100, 2)
            final_regret = float(eval_df["cumulative_regret"].iloc[-1])
            avg_reward = float(eval_df["avg_reward"].iloc[-1])
            total_reward = float(eval_df["cumulative_reward"].iloc[-1])
            rounds = len(eval_df)
        else:
            best_arm_pct = avg_reward = total_reward = final_regret = 0.0
            rounds = 0

        mlflow.log_metrics({
            "avg_reward": round(avg_reward, 4),
            "total_reward": round(total_reward, 2),
            "rounds": rounds,
            "final_regret": round(final_regret, 4),
            "best_arm_pct": best_arm_pct,
            "oracle_rate": round(best_arm_rate, 4),
            "regret_per_round": round(final_regret / rounds, 6) if rounds > 0 else 0.0,
        })

        # --- Métricas step-by-step (subamostradas para até 500 pontos) ---
        step_df = _subsample(eval_df, max_points=500)
        for _, row in step_df.iterrows():
            step = int(row["round"])
            mlflow.log_metric("step_avg_reward", row["avg_reward"], step=step)
            mlflow.log_metric("step_cumulative_regret", row["cumulative_regret"], step=step)

        # --- Tags ---
        mlflow.set_tags({
            "data_source": "offer_events.csv",
            "data_type": "synthetic",
        })

        # --- Artefatos ---
        if artifacts_dir:
            artifacts_dir = Path(artifacts_dir)
            _log_artifacts(artifacts_dir, eval_df)

        return run.info.run_id


def _subsample(df: pd.DataFrame, max_points: int = 500) -> pd.DataFrame:
    if len(df) <= max_points:
        return df
    step = len(df) // max_points
    return df.iloc[::step]


def _log_artifacts(artifacts_dir: Path, eval_df: pd.DataFrame) -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # CSV do resultado
        csv_path = tmp_path / "eval_results.csv"
        eval_df.to_csv(csv_path, index=False)
        mlflow.log_artifact(str(csv_path), artifact_path="data")

        # Gráficos gerados no artifacts_dir
        for png in artifacts_dir.glob("*.png"):
            mlflow.log_artifact(str(png), artifact_path="plots")


def log_comparison_table(summary_rows: list[dict]) -> None:
    """Logs a comparison table as a text artifact."""
    import tempfile

    df = pd.DataFrame(summary_rows)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "comparison_table.csv"
        df.to_csv(path, index=False)
        mlflow.log_artifact(str(path), artifact_path="data")
