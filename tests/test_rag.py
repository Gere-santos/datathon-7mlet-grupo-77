"""
Evidências de aceite — RAG sobre políticas internas sintéticas

Verifica que:
1. Os documentos de política existem e têm os tópicos obrigatórios.
2. A função retrieve_policies() retorna seções relevantes para queries relacionadas.
3. O endpoint /assistant/ask aceita include_policy_context=True.
"""

from pathlib import Path

import pytest

_POLICIES_DIR = Path(__file__).parents[1] / "data" / "synthetic_enrichment" / "policies"


# ── 1. Documentos de política existem ────────────────────────────────────────

def test_policies_directory_existe():
    assert _POLICIES_DIR.is_dir(), "data/synthetic_enrichment/policies/ não encontrado"


def test_offer_policy_existe():
    assert (_POLICIES_DIR / "offer_policy.md").exists()


def test_suitability_rules_existe():
    assert (_POLICIES_DIR / "suitability_rules.md").exists()


def test_experiment_protocol_existe():
    assert (_POLICIES_DIR / "experiment_protocol.md").exists()


def test_offer_policy_cobre_todos_os_bracos():
    texto = (_POLICIES_DIR / "offer_policy.md").read_text()
    for arm in ["sem_oferta", "educacao_financeira", "simulador_credito", "cartao_premium"]:
        assert arm in texto, f"offer_policy.md deve descrever braço '{arm}'"


def test_suitability_rules_cobre_guardrails_implementados():
    texto = (_POLICIES_DIR / "suitability_rules.md").read_text()
    assert "18" in texto, "suitability_rules deve mencionar restrição de idade < 18"
    assert "inadimplencia" in texto.lower() or "inadimplência" in texto.lower(), \
        "suitability_rules deve mencionar restrição de inadimplência"
    assert "20+" in texto, "suitability_rules deve mencionar fadiga de contato (20+)"


def test_experiment_protocol_cobre_criterios_de_promocao():
    texto = (_POLICIES_DIR / "experiment_protocol.md").read_text()
    assert "promoção" in texto.lower() or "promocao" in texto.lower() or "promov" in texto.lower()
    assert "mlflow" in texto.lower() or "MLflow" in texto


# ── 2. retrieve_policies() retorna conteúdo relevante ────────────────────────

def test_retrieve_policies_retorna_string():
    from datathon_offerexp.assistant import retrieve_policies
    result = retrieve_policies("cartao_premium elegibilidade")
    assert isinstance(result, str)


def test_retrieve_policies_cartao_premium_retorna_politica_de_oferta():
    from datathon_offerexp.assistant import retrieve_policies
    result = retrieve_policies("cartao_premium elegibilidade idade")
    assert len(result) > 0, "Deve retornar conteúdo para query sobre cartao_premium"
    assert "cartao_premium" in result.lower() or "premium" in result.lower()


def test_retrieve_policies_suitability_retorna_regras():
    from datathon_offerexp.assistant import retrieve_policies
    result = retrieve_policies("suitability idade menor inadimplência guardrail")
    assert len(result) > 0, "Deve retornar conteúdo de suitability"


def test_retrieve_policies_promocao_retorna_protocolo():
    from datathon_offerexp.assistant import retrieve_policies
    result = retrieve_policies("promoção experimento aprovação threshold")
    assert len(result) > 0, "Deve retornar protocolo de experimentos"


def test_retrieve_policies_query_sem_match_retorna_vazio_ou_string():
    from datathon_offerexp.assistant import retrieve_policies
    result = retrieve_policies("xyzxyzxyz termos que nao existem abc")
    assert isinstance(result, str)


# ── 3. ask() com include_policy_context injeta contexto de política ──────────

def test_ask_com_policy_context_nao_quebra(monkeypatch):
    """ask() com include_policy_context=True não deve lançar exceção (stub mode)."""
    monkeypatch.setenv("LLM_PROVIDER", "stub")
    from datathon_offerexp.assistant import ask
    result = ask(
        "Quais são as regras de elegibilidade para cartao_premium?",
        include_policy_context=True,
    )
    assert isinstance(result, str)
    assert len(result) > 0


def test_endpoint_assistant_ask_aceita_policy_context():
    """POST /assistant/ask com include_policy_context=True deve retornar 200."""
    from fastapi.testclient import TestClient
    from datathon_offerexp.app import app
    client = TestClient(app)
    r = client.post("/assistant/ask", json={
        "question": "Quais clientes não podem receber cartao_premium?",
        "include_policy_context": True,
    })
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data
    assert isinstance(data["answer"], str)
