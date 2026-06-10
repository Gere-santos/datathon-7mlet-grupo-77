"""Tests for assistant.py in stub mode (no API keys required)."""
from __future__ import annotations

import os

import pytest


def test_ask_stub_mode(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")

    from datathon_offerexp.assistant import ask

    response = ask("Qual é a melhor oferta?")
    assert "modo offline" in response.lower() or "api" in response.lower()
    assert isinstance(response, str)
    assert len(response) > 0


def test_ask_stub_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "stub")

    from datathon_offerexp.assistant import ask

    response = ask("Teste de pergunta.")
    assert "modo offline" in response.lower() or "api" in response.lower()


def test_explain_decision_stub(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")

    from datathon_offerexp.assistant import explain_decision

    response = explain_decision(
        arm_name="educacao_financeira",
        reason_codes=["thompson_sample_arm_1"],
        policy_version="thompson-v1",
        context={"profissao": "admin"},
    )
    assert isinstance(response, str)
    assert len(response) > 0


def test_ask_with_extra_context(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "stub")

    from datathon_offerexp.assistant import ask

    response = ask("Resumo do experimento.", extra_context={"rounds": 1000, "avg_reward": 0.12})
    assert isinstance(response, str)


def test_ask_include_log_summary_no_file(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_PROVIDER", "stub")

    from datathon_offerexp.assistant import ask

    response = ask(
        "Status dos logs?",
        include_log_summary=True,
        log_path=str(tmp_path / "nonexistent.jsonl"),
    )
    assert isinstance(response, str)


def test_ask_include_log_summary_with_file(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_PROVIDER", "stub")

    import json

    log_file = tmp_path / "test.jsonl"
    record = {
        "timestamp": "2025-06-01T10:00:00Z",
        "event_id": "evt-001",
        "arm_name": "educacao_financeira",
        "reward": 1,
        "policy_version": "thompson-v1",
    }
    log_file.write_text(json.dumps(record) + "\n")

    from datathon_offerexp.assistant import ask

    response = ask("Status?", include_log_summary=True, log_path=str(log_file))
    assert isinstance(response, str)


def test_summarize_experiment_stub(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "stub")

    from datathon_offerexp.assistant import summarize_experiment

    response = summarize_experiment(
        policy_name="Thompson Sampling",
        avg_reward=0.12,
        final_regret=150.0,
        best_arm_pct=45.0,
        rounds=1000,
        arm_stats=[
            {"arm_name": "sem_oferta", "trials": 250, "reward_rate": 0.05},
            {"arm_name": "educacao_financeira", "trials": 450, "reward_rate": 0.15},
        ],
    )
    assert isinstance(response, str)
    assert len(response) > 0
