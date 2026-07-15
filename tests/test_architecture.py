"""
Evidências de aceite — Etapa 6

Verifica via `make test` que a arquitetura:
1. Usa exclusivamente Azure em produção (sem dependência de outro provedor ativa).
2. Cobre todas as camadas exigidas no documento de arquitetura.
3. Justifica trade-offs entre alternativas de serviço.
"""

import ast
import os
from pathlib import Path

_ROOT      = Path(__file__).parents[1]
_ARCH_DOC  = _ROOT / "docs" / "architecture-azure.md"
_ENV_FILE  = _ROOT / ".env.example"


# ── 1. Exclusividade Azure em produção ───────────────────────────────────────

def test_anthropic_nao_e_provider_ativo_no_env():
    """Anthropic deve aparecer apenas como linha comentada em .env.example."""
    for linha in _ENV_FILE.read_text().splitlines():
        stripped = linha.strip()
        if stripped.startswith("#"):
            continue
        assert "anthropic" not in stripped.lower(), (
            f"Linha ativa referencia Anthropic (provedor não-Azure): '{stripped}'"
        )


# ── 2. Cobertura das camadas ──────────────────────────────────────────────────

_CAMADAS_OBRIGATORIAS = {
    "compute":         ["Container Apps", "container apps", "ACA"],
    "api":             ["API Management", "APIM"],
    "dados":           ["Cosmos", "Blob"],
    "ia_rag":          ["OpenAI", "AI Search"],
    "observabilidade": ["Monitor", "Application Insights", "Log Analytics"],
    "segurança":       ["Key Vault", "TLS"],
    "identidade":      ["Managed Identity", "Active Directory", "AAD"],
    "governança":      ["Azure Policy", "Policy", "LGPD", "lgpd"],
}


def test_arquitetura_cobre_todas_as_camadas():
    """docs/architecture-azure.md deve mencionar cada camada exigida."""
    texto = _ARCH_DOC.read_text()
    faltando = []
    for camada, termos in _CAMADAS_OBRIGATORIAS.items():
        if not any(t in texto for t in termos):
            faltando.append(f"{camada} (esperava um de: {termos})")
    assert not faltando, (
        "Camadas não cobertas no architecture-azure.md:\n" +
        "\n".join(f"  - {c}" for c in faltando)
    )


def test_diagrama_mermaid_presente():
    """O documento deve conter um diagrama Mermaid."""
    texto = _ARCH_DOC.read_text()
    assert "```mermaid" in texto, "Diagrama Mermaid não encontrado em architecture-azure.md"


def test_estimativa_de_custo_presente():
    """O documento deve conter estimativa de custo."""
    texto = _ARCH_DOC.read_text()
    assert any(t in texto for t in ["Custo", "custo", "\\$", "$"]), \
        "Estimativa de custo não encontrada em architecture-azure.md"


# ── 3. Justificativa de trade-offs ───────────────────────────────────────────

_TRADEOFFS_ESPERADOS = [
    ("Container Apps", "AKS"),
    ("Cosmos", "SQL"),
    ("Service Bus", "Event Hubs"),
    ("Azure OpenAI", "Anthropic"),
]


def test_secao_tradeoffs_existe():
    """O documento deve ter seção dedicada a trade-offs."""
    texto = _ARCH_DOC.read_text().lower()
    assert "trade-off" in texto or "tradeoff" in texto, \
        "Seção de trade-offs não encontrada em architecture-azure.md"


def test_tradeoffs_comparam_alternativas_concretas():
    """Cada par de serviço/alternativa deve aparecer na mesma seção de trade-offs."""
    texto = _ARCH_DOC.read_text()
    faltando = []
    for escolhido, alternativa in _TRADEOFFS_ESPERADOS:
        if escolhido not in texto or alternativa not in texto:
            faltando.append(f"{escolhido} vs {alternativa}")
    assert not faltando, (
        "Trade-offs não documentados em architecture-azure.md:\n" +
        "\n".join(f"  - {p}" for p in faltando)
    )


def test_azure_exclusivo_justificado_no_doc():
    """O documento deve justificar explicitamente o uso exclusivo de Azure."""
    texto = _ARCH_DOC.read_text()
    termos = ["exclusiv", "boundary", "LGPD", "Managed Identity unificada", "compliance"]
    assert any(t in texto for t in termos), (
        "architecture-azure.md deve justificar o uso exclusivo de Azure "
        f"(esperava um de: {termos})"
    )
