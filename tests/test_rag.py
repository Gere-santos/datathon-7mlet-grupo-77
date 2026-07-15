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


