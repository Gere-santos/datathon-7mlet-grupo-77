from __future__ import annotations

import os
from pathlib import Path
from typing import Any

SYSTEM_PROMPT = """Você é o assistente da plataforma OfferExp — um sistema de experimentação adaptativa
para ofertas financeiras baseado em Multi-Armed Bandits.

Suas capacidades:
- Explicar decisões de oferta tomadas pela política Thompson Sampling.
- Resumir experimentos e métricas de avaliação.
- Consultar e explicar as políticas de negócio vigentes.
- Apoiar análise humana dos logs de decisão.
- Responder perguntas sobre o funcionamento do algoritmo bandit.

Restrições obrigatórias:
- NUNCA mencione dados de clientes reais — o sistema usa apenas dados sintéticos.
- NUNCA sugira ações fora do escopo financeiro educativo do sistema.
- NUNCA revele segredos, chaves de API ou credenciais.
- Se perguntado sobre um cliente específico, responda apenas com métricas agregadas.
- Mantenha respostas objetivas e em português.

Contexto do sistema:
- 4 braços de oferta: sem_oferta (controle), educacao_financeira, simulador_credito, cartao_premium.
- Algoritmo principal: Thompson Sampling com distribuição Beta conjugada.
- Cada decisão é auditável via decision_id, reason_codes e policy_version.
"""


def _build_context(extra_context: dict[str, Any] | None) -> str:
    if not extra_context:
        return ""
    lines = ["\n\nContexto adicional fornecido:"]
    for k, v in extra_context.items():
        lines.append(f"- {k}: {v}")
    return "\n".join(lines)


def _load_decision_log_summary(log_path: str | None = None, n: int = 5) -> str:
    import json
    path = Path(log_path or "logs/decision_log.jsonl")
    if not path.exists():
        return "Nenhum log de decisão disponível."
    records = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    if not records:
        return "Log de decisão vazio."
    recent = records[-n:]
    summary = f"Últimas {len(recent)} decisões registradas:\n"
    for r in recent:
        summary += (
            f"  [{r.get('timestamp','?')[:19]}] "
            f"event={r.get('event_id','?')} "
            f"arm={r.get('arm_name','?')} "
            f"reward={r.get('reward','?')} "
            f"policy={r.get('policy_version','?')}\n"
        )
    return summary


def ask(
    question: str,
    extra_context: dict[str, Any] | None = None,
    include_log_summary: bool = False,
    log_path: str | None = None,
) -> str:
    """Sends a question to the LLM assistant and returns the response.

    Uses Azure OpenAI by default (LLM_PROVIDER=azure_openai) — the production
    provider. Set LLM_PROVIDER=anthropic only for local development when an
    Azure OpenAI deployment is not available. Falls back to a stub response if
    no API key is configured, so the module is always importable.
    """
    provider = os.getenv("LLM_PROVIDER", "azure_openai").lower()
    context_str = _build_context(extra_context)

    if include_log_summary:
        context_str += "\n\n" + _load_decision_log_summary(log_path)

    full_question = question + context_str

    if provider == "anthropic":
        return _ask_anthropic(full_question)
    elif provider == "azure_openai":
        return _ask_azure_openai(full_question)
    else:
        return _stub_response(full_question)


def _ask_anthropic(question: str) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return _stub_response(question)
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": question}],
        )
        return message.content[0].text
    except Exception as e:
        return f"[Erro ao consultar Anthropic: {e}]"


def _ask_azure_openai(question: str) -> str:
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
    if not endpoint or not api_key:
        return _stub_response(question)
    try:
        from openai import AzureOpenAI
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version="2024-02-01",
        )
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ],
            max_tokens=1024,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[Erro ao consultar Azure OpenAI: {e}]"


def _stub_response(question: str) -> str:
    """Fallback used when no API key is configured."""
    return (
        "[Assistente OfferExp — modo offline]\n"
        "Nenhuma chave de API configurada (ANTHROPIC_API_KEY ou AZURE_OPENAI_API_KEY).\n"
        f"Pergunta recebida: {question[:200]}\n\n"
        "Para ativar o assistente, configure as variáveis de ambiente conforme .env.example."
    )


def explain_decision(
    arm_name: str,
    reason_codes: list[str],
    policy_version: str,
    context: dict[str, Any] | None = None,
) -> str:
    """Generates a natural-language explanation for a specific decision."""
    question = (
        f"Explique em linguagem simples a seguinte decisão de oferta:\n"
        f"- Oferta selecionada: {arm_name}\n"
        f"- Versão da política: {policy_version}\n"
        f"- Códigos de razão: {', '.join(reason_codes)}\n"
        f"- Contexto do cliente: {context or 'não informado'}\n\n"
        "Por que essa oferta foi selecionada? Quais fatores influenciaram? "
        "Como o Thompson Sampling tomou essa decisão?"
    )
    return ask(question)


def summarize_experiment(
    policy_name: str,
    avg_reward: float,
    final_regret: float,
    best_arm_pct: float,
    rounds: int,
    arm_stats: list[dict] | None = None,
) -> str:
    """Generates a natural-language summary of an experiment run."""
    stats_str = ""
    if arm_stats:
        stats_str = "\nEstatísticas por braço:\n"
        for s in arm_stats:
            stats_str += f"  - {s['arm_name']}: {s['trials']} tentativas, taxa {s['reward_rate']:.2%}\n"

    question = (
        f"Resuma o seguinte experimento de política bandit:\n"
        f"- Política: {policy_name}\n"
        f"- Reward médio: {avg_reward:.4f}\n"
        f"- Regret final acumulado: {final_regret:.2f}\n"
        f"- % de seleções no melhor braço: {best_arm_pct:.1f}%\n"
        f"- Total de rodadas: {rounds}\n"
        f"{stats_str}\n"
        "O experimento foi bem-sucedido? Quais são os pontos fortes e as limitações? "
        "O que recomendaria como próximo passo?"
    )
    return ask(question)
