from __future__ import annotations

import os

import mlflow
from fastapi import FastAPI, HTTPException

from datathon_offerexp.contracts import (
    ArmStats,
    DecisionRequest,
    DecisionResponse,
    PolicyStatsResponse,
    RewardUpdate,
)
from datathon_offerexp.assistant import ask, explain_decision
from datathon_offerexp.decision_log import DecisionLog
from datathon_offerexp.mlflow_utils import EXPERIMENT_NAME, configure_tracking, get_or_create_experiment
from datathon_offerexp.policies import OFFER_CATALOG, ThompsonSamplingPolicy

MLFLOW_LOG_INTERVAL = int(os.getenv("MLFLOW_LOG_INTERVAL", "100"))

app = FastAPI(
    title="OfferExp Decision API",
    description="Plataforma de experimentação adaptativa para ofertas financeiras — Datathon 7MLET",
    version="1.0.0",
)

configure_tracking(os.getenv("MLFLOW_TRACKING_URI"))
_exp_id = get_or_create_experiment()
_active_run: mlflow.ActiveRun | None = None
_decisions_since_log = 0

_policy = ThompsonSamplingPolicy()
_log = DecisionLog("logs/decision_log.jsonl")
_pending: dict[str, int] = {}  # event_id → arm_id awaiting reward


def _ensure_run() -> None:
    global _active_run
    if _active_run is None:
        _active_run = mlflow.start_run(
            experiment_id=_exp_id,
            run_name="online-thompson-v1",
            tags={"mode": "online", "policy": _policy.version},
        )
        mlflow.log_params({"policy": "Thompson Sampling", "policy_version": _policy.version})


def _flush_metrics(total_decisions: int) -> None:
    for s in _policy.stats():
        prefix = s["arm_name"]
        mlflow.log_metric(f"{prefix}_trials", s["trials"], step=total_decisions)
        mlflow.log_metric(f"{prefix}_reward_rate", s["reward_rate"], step=total_decisions)
        mlflow.log_metric(f"{prefix}_alpha", s.get("alpha", 1), step=total_decisions)
        mlflow.log_metric(f"{prefix}_beta", s.get("beta", 1), step=total_decisions)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "policy": _policy.version}


@app.post("/decide", response_model=DecisionResponse)
def decide(request: DecisionRequest) -> DecisionResponse:
    arm_idx = _policy.select_arm()
    arm = OFFER_CATALOG[arm_idx]

    arm_stats = {s["arm_id"]: s for s in _policy.stats()}
    s = arm_stats[arm_idx]
    reason = [
        f"thompson_sample_arm_{arm_idx}",
        f"alpha={s.get('alpha', 1):.1f}",
        f"beta={s.get('beta', 1):.1f}",
        f"reward_rate={s['reward_rate']:.4f}",
        f"trials={s['trials']}",
    ]

    _pending[request.event_id] = arm_idx
    _log.log(
        event_id=request.event_id,
        arm_id=arm_idx,
        arm_name=arm["arm_name"],
        reward=None,
        policy_version=_policy.version,
        reason_codes=reason,
    )

    return DecisionResponse(
        event_id=request.event_id,
        arm_id=arm_idx,
        arm_name=arm["arm_name"],
        policy_version=_policy.version,
        reason_codes=reason,
    )


@app.post("/reward")
def reward(update: RewardUpdate) -> dict:
    if update.event_id not in _pending:
        raise HTTPException(status_code=404, detail="event_id não encontrado ou recompensa já registrada")

    arm_idx = _pending.pop(update.event_id)
    if arm_idx != update.arm_id:
        raise HTTPException(status_code=400, detail="arm_id não corresponde à decisão registrada")

    _policy.update(arm_idx, update.reward)
    _log.log(
        event_id=update.event_id,
        arm_id=arm_idx,
        arm_name=OFFER_CATALOG[arm_idx]["arm_name"],
        reward=update.reward,
        policy_version=_policy.version,
    )

    global _decisions_since_log
    _decisions_since_log += 1
    if _decisions_since_log >= MLFLOW_LOG_INTERVAL:
        _ensure_run()
        total = sum(s["trials"] for s in _policy.stats())
        _flush_metrics(total)
        _decisions_since_log = 0

    return {"status": "updated", "arm_id": arm_idx, "reward": update.reward}


@app.get("/stats", response_model=PolicyStatsResponse)
def stats() -> PolicyStatsResponse:
    arm_stats = [
        ArmStats(
            arm_id=s["arm_id"],
            arm_name=s["arm_name"],
            trials=s["trials"],
            successes=s["successes"],
            reward_rate=s["reward_rate"],
            alpha=s.get("alpha", s["successes"] + 1),
            beta=s.get("beta", s["trials"] - s["successes"] + 1),
        )
        for s in _policy.stats()
    ]
    return PolicyStatsResponse(
        policy_version=_policy.version,
        total_decisions=sum(s.trials for s in arm_stats),
        arms=arm_stats,
    )


from pydantic import BaseModel


class AskRequest(BaseModel):
    question: str
    include_log_summary: bool = False


class ExplainRequest(BaseModel):
    event_id: str
    arm_name: str
    reason_codes: list[str] = []
    context: dict = {}


@app.post("/assistant/ask")
def assistant_ask(req: AskRequest) -> dict:
    answer = ask(
        req.question,
        include_log_summary=req.include_log_summary,
        log_path=str(_log.path),
    )
    return {"question": req.question, "answer": answer}


@app.post("/assistant/explain")
def assistant_explain(req: ExplainRequest) -> dict:
    explanation = explain_decision(
        arm_name=req.arm_name,
        reason_codes=req.reason_codes,
        policy_version=_policy.version,
        context=req.context,
    )
    return {"event_id": req.event_id, "explanation": explanation}
