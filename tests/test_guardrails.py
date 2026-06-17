"""
Evidências de aceite — Etapa 4 (cenários adversariais)

Testa os guardrails de suitability e validações de input da API
com entradas adversariais. Todos os testes usam o TestClient do FastAPI —
sem servidor real necessário.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    from datathon_offerexp.app import app
    return TestClient(app)


# ── Validação de reward ───────────────────────────────────────────────────────

def test_reward_acima_de_1_e_rejeitado(client):
    """reward > 1.0 deve ser rejeitado com 422 (Pydantic Field ge/le)."""
    client.post("/decide", json={"event_id": "adv-r1", "subject_key": "s1"})
    r = client.post("/reward", json={"event_id": "adv-r1", "arm_id": 0, "reward": 1.5})
    assert r.status_code == 422, f"Esperava 422, recebeu {r.status_code}: {r.text}"


def test_reward_abaixo_de_0_e_rejeitado(client):
    """reward < 0.0 deve ser rejeitado com 422."""
    client.post("/decide", json={"event_id": "adv-r2", "subject_key": "s1"})
    r = client.post("/reward", json={"event_id": "adv-r2", "arm_id": 0, "reward": -0.1})
    assert r.status_code == 422, f"Esperava 422, recebeu {r.status_code}: {r.text}"


def test_reward_string_e_rejeitado(client):
    """reward como string não-numérica deve ser rejeitado."""
    client.post("/decide", json={"event_id": "adv-r3", "subject_key": "s1"})
    r = client.post("/reward", json={"event_id": "adv-r3", "arm_id": 0, "reward": "sim"})
    assert r.status_code == 422


def test_reward_em_event_id_desconhecido_retorna_404(client):
    """reward para event_id nunca registrado deve retornar 404."""
    r = client.post("/reward", json={"event_id": "nao-existe-xyz", "arm_id": 0, "reward": 1.0})
    assert r.status_code == 404


# ── Guardrail: idade < 18 ─────────────────────────────────────────────────────

def test_menor_de_18_recebe_sem_oferta(client):
    """Cliente com idade < 18 deve receber sem_oferta independente do Thompson Sampling."""
    r = client.post("/decide", json={
        "event_id": "adv-age-1",
        "subject_key": "minor-01",
        "context": {"idade": 16, "profissao": "student"},
    })
    assert r.status_code == 200
    data = r.json()
    assert data["arm_name"] == "sem_oferta", (
        f"Menor de 18 deve receber sem_oferta, recebeu '{data['arm_name']}'"
    )
    assert "guardrail_age_under_18" in data["reason_codes"], (
        f"reason_codes deve conter guardrail_age_under_18, recebeu {data['reason_codes']}"
    )


def test_menor_de_18_limiar_exato(client):
    """Cliente com exatamente 17 anos deve ser bloqueado."""
    r = client.post("/decide", json={
        "event_id": "adv-age-2",
        "subject_key": "minor-02",
        "context": {"idade": 17},
    })
    assert r.json()["arm_name"] == "sem_oferta"


def test_cliente_com_18_anos_nao_bloqueado(client):
    """Cliente com 18 anos não deve ser bloqueado pelo guardrail de idade."""
    r = client.post("/decide", json={
        "event_id": "adv-age-3",
        "subject_key": "adult-01",
        "context": {"idade": 18},
    })
    assert r.status_code == 200
    data = r.json()
    assert "guardrail_age_under_18" not in data["reason_codes"]


# ── Guardrail: inadimplência + cartao_premium ─────────────────────────────────

def test_inadimplente_forcado_para_cartao_premium_recebe_sem_oferta(client):
    """Se o Thompson escolhesse cartao_premium para um inadimplente, o guardrail
    deve desviar para sem_oferta. Testamos com monkey-patch da política."""
    from unittest.mock import patch
    from datathon_offerexp.app import _policy

    with patch.object(_policy, "select_arm", return_value=3):  # força cartao_premium
        r = client.post("/decide", json={
            "event_id": "adv-inad-1",
            "subject_key": "inadimplente-01",
            "context": {"inadimplencia": "yes"},
        })
    assert r.status_code == 200
    data = r.json()
    assert data["arm_name"] == "sem_oferta", (
        f"Inadimplente não deve receber cartao_premium, recebeu '{data['arm_name']}'"
    )
    assert "guardrail_inadimplencia_cartao_premium" in data["reason_codes"]


# ── Guardrail: fadiga de contato ──────────────────────────────────────────────

def test_fadiga_de_contato_recebe_sem_oferta(client):
    """Cliente com faixa_contatos=20+ deve receber sem_oferta."""
    from unittest.mock import patch
    from datathon_offerexp.app import _policy

    with patch.object(_policy, "select_arm", return_value=1):  # Thompson teria escolhido outro
        r = client.post("/decide", json={
            "event_id": "adv-fatiga-1",
            "subject_key": "cansado-01",
            "context": {"faixa_contatos": "20+"},
        })
    assert r.status_code == 200
    data = r.json()
    assert data["arm_name"] == "sem_oferta"
    assert "guardrail_contact_fatigue_20plus" in data["reason_codes"]


# ── Guardrail: campos desconhecidos ignorados ─────────────────────────────────

def test_campos_injetados_sao_ignorados_em_decide(client):
    """Campos extras na requisição devem ser silenciosamente descartados (extra='ignore')."""
    r = client.post("/decide", json={
        "event_id": "adv-inject-1",
        "subject_key": "attacker",
        "context": {"profissao": "admin"},
        "arm_override": 3,          # campo injetado — deve ser ignorado
        "policy_version": "evil-v1",  # campo injetado — deve ser ignorado
        "__class__": "exploit",        # campo injetado
    })
    assert r.status_code == 200


def test_campos_injetados_sao_ignorados_em_reward(client):
    """Campos extras no payload de reward devem ser silenciosamente ignorados."""
    dec = client.post("/decide", json={"event_id": "adv-inject-2", "subject_key": "s1"})
    arm_id = dec.json()["arm_id"]
    r = client.post("/reward", json={
        "event_id": "adv-inject-2",
        "arm_id": arm_id,
        "reward": 0.0,
        "bonus_reward": 999,    # campo injetado — deve ser ignorado
        "override": True,       # campo injetado — deve ser ignorado
    })
    assert r.status_code == 200


# ── Integridade do log ────────────────────────────────────────────────────────

def test_guardrail_e_logado_com_reason_code(client, tmp_path):
    """Decisão com guardrail deve aparecer no decision log com reason_code correto."""
    import json
    from datathon_offerexp.decision_log import DecisionLog
    from datathon_offerexp import app as app_module

    log_path = tmp_path / "test_guardrail_log.jsonl"
    original_log = app_module._log
    app_module._log = DecisionLog(str(log_path))

    try:
        client.post("/decide", json={
            "event_id": "adv-log-1",
            "subject_key": "minor-log",
            "context": {"idade": 15},
        })
    finally:
        app_module._log = original_log

    lines = log_path.read_text().strip().splitlines()
    assert lines, "Log deve ter pelo menos uma entrada"
    entry = json.loads(lines[-1])
    assert "guardrail_age_under_18" in entry.get("reason_codes", []), (
        f"Guardrail deve aparecer no log, mas reason_codes foi {entry.get('reason_codes')}"
    )
