import json
import tempfile
from pathlib import Path

import pytest
from datathon_offerexp.decision_log import DecisionLog


@pytest.fixture
def tmp_log(tmp_path):
    return DecisionLog(tmp_path / "test_log.jsonl")


def test_log_creates_file(tmp_log):
    tmp_log.log(
        event_id="e1",
        arm_id=0,
        arm_name="sem_oferta",
        reward=None,
        policy_version="thompson-v1",
    )
    assert tmp_log.path.exists()


def test_log_record_fields(tmp_log):
    decision_id = tmp_log.log(
        event_id="e2",
        arm_id=3,
        arm_name="cartao_premium",
        reward=1.0,
        policy_version="thompson-v1",
        reason_codes=["code_a"],
    )
    records = tmp_log.read_all()
    assert len(records) == 1
    r = records[0]
    assert r["decision_id"] == decision_id
    assert r["event_id"] == "e2"
    assert r["arm_id"] == 3
    assert r["reward"] == 1.0
    assert r["reason_codes"] == ["code_a"]


def test_log_appends_multiple_records(tmp_log):
    for i in range(5):
        tmp_log.log(f"evt_{i}", i % 4, "sem_oferta", 0.0, "random-v1")
    records = tmp_log.read_all()
    assert len(records) == 5


def test_read_all_empty_returns_list(tmp_log):
    assert tmp_log.read_all() == []


def test_log_null_reward(tmp_log):
    tmp_log.log("e_null", 1, "educacao_financeira", None, "thompson-v1")
    records = tmp_log.read_all()
    assert records[0]["reward"] is None
