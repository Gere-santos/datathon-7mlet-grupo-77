#!/usr/bin/env bash
# Pipeline ponta a ponta — OfferExp
# Uso: bash scripts/run_demo.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; RESET='\033[0m'
step() { echo -e "\n${GREEN}==>${RESET} $*"; }
warn() { echo -e "${YELLOW}[AVISO]${RESET} $*"; }
fail() { echo -e "${RED}[ERRO]${RESET} $*"; exit 1; }

# ── 1. Dependências ─────────────────────────────────────────────────────────
step "Verificando dependências..."
if python3 -c "import datathon_offerexp" 2>/dev/null; then
    echo "  Pacote já instalado — pulando instalação."
else
    echo "  Instalando..."
    python3 -m pip install -e ".[dev]" -q || fail "Falha ao instalar dependências. Execute: pip install -e '[dev]' manualmente e tente novamente."
fi

# ── 2. Dados sintéticos ──────────────────────────────────────────────────────
EVENTS="data/synthetic_enrichment/offer_events.csv"
if [ ! -f "$EVENTS" ]; then
    step "Gerando dados sintéticos..."
    python3 data/synthetic_enrichment/generate_synthetic_data.py
else
    step "Dados sintéticos já existem — pulando geração."
fi

# ── 3. Testes automatizados ──────────────────────────────────────────────────
step "Executando suíte de testes (33 testes)..."
python3 -m pytest tests/ -v --tb=short || fail "Testes falharam — corrija antes de continuar."

# ── 4. Avaliação offline — Golden Set ────────────────────────────────────────
step "Executando avaliação offline (golden set)..."
# exit code 1 = casos falharam (comportamento esperado para política não-contextual)
python3 scripts/run_golden_set.py --seed 42 || warn "Golden set com falhas — veja o relatório acima (comportamento documentado)."

# ── 5. Instrução para API ────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${RESET}"
echo -e "${GREEN}║  Pipeline concluído com sucesso.                         ║${RESET}"
echo -e "${GREEN}║                                                          ║${RESET}"
echo -e "${GREEN}║  Para iniciar a API:   make api                          ║${RESET}"
echo -e "${GREEN}║  Swagger UI:           http://localhost:8000/docs         ║${RESET}"
echo -e "${GREEN}║  MLflow UI:            make mlflow  (porta 5000)         ║${RESET}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${RESET}"
