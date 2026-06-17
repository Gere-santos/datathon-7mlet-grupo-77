"""
Evidências de aceite — Etapa 8

Verifica via `make test` que os documentos de governança existem e cobrem
todos os itens exigidos: model card, system card, LGPD e relatório técnico.
"""

from pathlib import Path

_ROOT       = Path(__file__).parents[1]
_MODEL_CARD = _ROOT / "docs" / "model-card.md"
_SYS_CARD   = _ROOT / "docs" / "system-card.md"
_LGPD       = _ROOT / "docs" / "lgpd-plan.md"
_RELATORIO  = _ROOT / "reports" / "relatorio-tecnico.md"


# ── model-card.md ─────────────────────────────────────────────────────────────

def test_model_card_existe():
    assert _MODEL_CARD.exists(), "docs/model-card.md não encontrado"


def test_model_card_nome_versao():
    t = _MODEL_CARD.read_text()
    assert "thompson" in t.lower(), "model card deve nomear o algoritmo Thompson Sampling"
    assert "thompson-v1" in t or "v1" in t, "model card deve indicar versão do modelo"


def test_model_card_dados_treino():
    t = _MODEL_CARD.read_text()
    assert "kaggle" in t.lower() or "bank marketing" in t.lower(), \
        "model card deve referenciar o dataset de treinamento"
    assert "sintéti" in t.lower() or "synthetic" in t.lower(), \
        "model card deve indicar que os dados de treinamento são sintéticos"


def test_model_card_metricas():
    t = _MODEL_CARD.read_text()
    assert "reward" in t.lower(), "model card deve conter métricas de avaliação (reward)"
    assert "regret" in t.lower(), "model card deve conter métricas de avaliação (regret)"
    assert "replayer" in t.lower() or "offline" in t.lower(), \
        "model card deve indicar o método de avaliação (Replayer Offline)"


def test_model_card_intended_use():
    t = _MODEL_CARD.read_text()
    termos = ["caso de uso", "pretendido", "intended", "uso pretendido"]
    assert any(t2.lower() in t.lower() for t2 in termos), \
        "model card deve descrever casos de uso pretendidos"


def test_model_card_out_of_scope():
    t = _MODEL_CARD.read_text()
    termos = ["não pretendido", "out-of-scope", "não deve", "not intended"]
    assert any(t2.lower() in t.lower() for t2 in termos), \
        "model card deve descrever casos de uso NÃO pretendidos"


def test_model_card_fairness():
    t = _MODEL_CARD.read_text()
    assert "fairness" in t.lower() or "equidade" in t.lower() or "discrimina" in t.lower(), \
        "model card deve ter análise de fairness"


def test_model_card_vieses_conhecidos():
    t = _MODEL_CARD.read_text()
    assert "viés" in t.lower() or "vieses" in t.lower() or "bias" in t.lower(), \
        "model card deve listar vieses conhecidos"


def test_model_card_limitacoes():
    t = _MODEL_CARD.read_text()
    assert "limitaç" in t.lower() or "limitação" in t.lower(), \
        "model card deve descrever limitações técnicas"


# ── system-card.md ────────────────────────────────────────────────────────────

def test_system_card_existe():
    assert _SYS_CARD.exists(), "docs/system-card.md não encontrado"


def test_system_card_escopo():
    t = _SYS_CARD.read_text()
    assert "acadêmi" in t.lower() or "escopo" in t.lower() or "propósito" in t.lower(), \
        "system card deve definir escopo/propósito do sistema"


def test_system_card_fluxo_decisao():
    t = _SYS_CARD.read_text()
    assert "/decide" in t or "decide" in t.lower(), \
        "system card deve descrever o fluxo de decisão"
    assert "/reward" in t or "reward" in t.lower(), \
        "system card deve mencionar o endpoint de reward"


def test_system_card_dependencias():
    t = _SYS_CARD.read_text()
    assert "fastapi" in t.lower() or "api" in t.lower(), \
        "system card deve listar dependências/componentes"
    assert "mlflow" in t.lower() or "mlops" in t.lower(), \
        "system card deve mencionar MLOps"


def test_system_card_guardrails():
    t = _SYS_CARD.read_text()
    assert "guardrail" in t.lower() or "suitability" in t.lower(), \
        "system card deve descrever guardrails de suitability"


def test_system_card_cenario_reward_hacking():
    t = _SYS_CARD.read_text().lower()
    assert "reward hacking" in t or "hacking" in t, \
        "system card deve cobrir cenário de reward hacking"


def test_system_card_cenario_manipulacao_contexto():
    t = _SYS_CARD.read_text().lower()
    assert "manipulação" in t or "contexto" in t, \
        "system card deve cobrir cenário de manipulação de contexto"


def test_system_card_cenario_abuso_assistente():
    t = _SYS_CARD.read_text().lower()
    assert "assistente" in t or "llm" in t, \
        "system card deve cobrir cenário de abuso do assistente LLM"


def test_system_card_cenario_suitability():
    t = _SYS_CARD.read_text().lower()
    assert "suitability" in t or "inadequad" in t, \
        "system card deve cobrir cenário de violação de suitability"


def test_system_card_plano_monitoramento():
    t = _SYS_CARD.read_text().lower()
    assert "monitor" in t or "observabilidade" in t or "métrica" in t, \
        "system card deve ter plano de monitoramento"


# ── lgpd-plan.md ──────────────────────────────────────────────────────────────

def test_lgpd_existe():
    assert _LGPD.exists(), "docs/lgpd-plan.md não encontrado"


def test_lgpd_base_legal():
    t = _LGPD.read_text().lower()
    assert "base legal" in t or "legítimo interesse" in t or "execução de contrato" in t, \
        "lgpd-plan deve indicar base legal"


def test_lgpd_finalidade():
    t = _LGPD.read_text().lower()
    assert "finalidade" in t, "lgpd-plan deve descrever finalidade do tratamento"


def test_lgpd_minimizacao():
    t = _LGPD.read_text().lower()
    assert "minimizaç" in t or "minimização" in t or "necessidade" in t, \
        "lgpd-plan deve cobrir princípio de minimização/necessidade"


def test_lgpd_retencao():
    t = _LGPD.read_text().lower()
    assert "retençã" in t or "retenção" in t or "descarte" in t, \
        "lgpd-plan deve definir ciclo de retenção e descarte"


def test_lgpd_identificadores():
    t = _LGPD.read_text().lower()
    assert "subject_key" in t or "pseudoanon" in t or "identificador" in t, \
        "lgpd-plan deve mapear identificadores (subject_key, pseudoanonimização)"


def test_lgpd_atributos_protegidos():
    t = _LGPD.read_text().lower()
    assert "atributo protegido" in t or "dado sensível" in t or "art. 5" in t, \
        "lgpd-plan deve mapear atributos protegidos (LGPD art. 5, II)"


def test_lgpd_politica_logs():
    t = _LGPD.read_text().lower()
    assert "log" in t and ("telemetria" in t or "política" in t or "registrado" in t), \
        "lgpd-plan deve ter política de logs/telemetria"


def test_lgpd_resposta_incidentes():
    t = _LGPD.read_text().lower()
    assert "incidente" in t or "72" in t or "anpd" in t, \
        "lgpd-plan deve ter plano de resposta a incidentes (notificação ANPD 72h)"


# ── relatorio-tecnico.md ──────────────────────────────────────────────────────

def test_relatorio_existe():
    assert _RELATORIO.exists(), "reports/relatorio-tecnico.md não encontrado"


_SECOES_OBRIGATORIAS = [
    ("problema",               ["Problema", "problema"]),
    ("base de dados",          ["Base de Dados", "Fonte", "Kaggle", "kaggle"]),
    ("enriquecimento",         ["Enriquecimento", "sintétic", "Sintéti"]),
    ("multi-armed bandit",     ["Multi-Armed Bandit", "Thompson", "bandit"]),
    ("comparação quantitativa",["Comparação", "Quantitativa", "quantitativa", "Replayer"]),
    ("arquitetura azure",      ["Azure", "Container Apps", "Cosmos"]),
    ("mlops",                  ["MLOps", "mlops", "MLflow", "ciclo de vida"]),
    ("limitações",             ["Limitações", "limitações", "Limitacao"]),
    ("riscos",                 ["Risco", "risco"]),
    ("hipóteses",              ["Hipótese", "hipótese", "premissa", "Premissa"]),
    ("trabalhos futuros",      ["Trabalhos Futuros", "trabalhos futuros", "Futuro"]),
    ("referências",            ["Referência", "referência", "Li et al", "Thompson, W"]),
]


def test_relatorio_cobre_todas_as_secoes():
    texto = _RELATORIO.read_text()
    faltando = []
    for secao, termos in _SECOES_OBRIGATORIAS:
        if not any(t in texto for t in termos):
            faltando.append(f"{secao} (esperava um de: {termos})")
    assert not faltando, (
        "Seções ausentes em relatorio-tecnico.md:\n" +
        "\n".join(f"  - {s}" for s in faltando)
    )


def test_relatorio_referencia_li_et_al_2011():
    t = _RELATORIO.read_text()
    assert "Li" in t and "2011" in t, \
        "Relatório deve citar Li et al. (2011) — Replayer Method"


def test_relatorio_menciona_lgpd():
    t = _RELATORIO.read_text()
    assert "LGPD" in t or "13.709" in t, \
        "Relatório deve mencionar LGPD"


def test_relatorio_azure_openai_e_default_producao():
    t = _RELATORIO.read_text()
    assert "azure_openai" in t.lower() or "Azure OpenAI" in t, \
        "Relatório deve referenciar Azure OpenAI como provider de produção"
    assert "padrão" in t.lower() or "produção" in t.lower(), \
        "Relatório deve indicar Azure OpenAI como padrão de produção"
