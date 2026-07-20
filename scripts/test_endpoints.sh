#!/usr/bin/env bash
# Bateria manual de amostras para testar a API OfferExp já em execução.
# Uso: bash scripts/test_endpoints.sh [base_url]
# Requer: API rodando (make api / uvicorn) e `jq` instalado (opcional, só para formatar saída).
set -euo pipefail

BASE_URL="${1:-http://localhost:8000}"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RESET='\033[0m'
step() { echo -e "\n${GREEN}==>${RESET} $*"; }
warn() { echo -e "${YELLOW}[AVISO]${RESET} $*"; }

pretty() {
    if command -v jq >/dev/null 2>&1; then jq .; else cat; fi
}

step "0. Health check"
curl -s "$BASE_URL/health" | pretty

step "1. Decisão normal"
curl -s -X POST "$BASE_URL/decide" \
  -H "Content-Type: application/json" \
  -d '{"event_id": "test-01", "subject_key": "cliente-1", "context": {"idade": 35, "profissao": "admin"}}' | pretty

step "2. Guardrail — menor de idade (deve retornar arm_id=0, sem_oferta)"
curl -s -X POST "$BASE_URL/decide" \
  -H "Content-Type: application/json" \
  -d '{"event_id": "test-02", "subject_key": "cliente-2", "context": {"idade": 16, "profissao": "student"}}' | pretty

step "3. Guardrail — fadiga de contato (20+, deve retornar arm_id=0, sem_oferta)"
curl -s -X POST "$BASE_URL/decide" \
  -H "Content-Type: application/json" \
  -d '{"event_id": "test-03", "subject_key": "cliente-3", "context": {"idade": 40, "faixa_contatos": "20+"}}' | pretty

step "4. Guardrail — inadimplência (só bloqueia se o Thompson sortear cartao_premium; roda 5x)"
for i in 1 2 3 4 5; do
    curl -s -X POST "$BASE_URL/decide" \
      -H "Content-Type: application/json" \
      -d "{\"event_id\": \"test-04-$i\", \"subject_key\": \"cliente-4\", \"context\": {\"idade\": 40, \"inadimplencia\": \"yes\"}}" | pretty
done

step "5. Contexto mínimo (edge case — só event_id)"
curl -s -X POST "$BASE_URL/decide" \
  -H "Content-Type: application/json" \
  -d '{"event_id": "test-05", "subject_key": "cliente-5", "context": {}}' | pretty

step "6. Reward válido para a decisão do passo 1"
curl -s -X POST "$BASE_URL/reward" \
  -H "Content-Type: application/json" \
  -d '{"event_id": "test-01", "arm_id": 2, "reward": 1.0}' | pretty
warn "Se o arm_id não bater com o que veio no passo 1, a API retorna 400 — ajuste manualmente se necessário."

step "7. Reward fora do range (deve dar erro de validação)"
curl -s -w "\nHTTP status: %{http_code}\n" -X POST "$BASE_URL/reward" \
  -H "Content-Type: application/json" \
  -d '{"event_id": "test-01", "arm_id": 2, "reward": 5.0}'

step "8. Reward para event_id inexistente (deve dar 404)"
curl -s -w "\nHTTP status: %{http_code}\n" -X POST "$BASE_URL/reward" \
  -H "Content-Type: application/json" \
  -d '{"event_id": "nao-existe-123", "arm_id": 0, "reward": 1.0}'

step "9. Estado final do modelo"
curl -s "$BASE_URL/stats" | pretty

echo -e "\n${GREEN}Concluído.${RESET}"
