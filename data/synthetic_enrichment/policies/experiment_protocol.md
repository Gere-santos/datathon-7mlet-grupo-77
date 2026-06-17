# Protocolo de Experimentos — OfferExp (Sintético)

> **DOCUMENTO SINTÉTICO** — criado para fins de demonstração e RAG.
> Versão: poc-v1 · Vigência: Junho 2025

---

## 1. Ciclo de Vida de um Experimento

```
Proposta → Revisão → Aprovação → Staging → Canary → Produção → Monitoramento
```

---

## 2. Critérios de Promoção

Para uma nova política ser promovida para produção, deve atender **todos** os critérios:

| Critério | Threshold |
|----------|-----------|
| `avg_reward` | > baseline Random + 5% |
| `final_regret` | < baseline Random em 20% |
| `best_arm_pct` | > 25% das seleções no melhor braço |
| Testes automatizados | 100% passing |
| Golden set (25 casos) | 100% dos `pass_criteria` atendidos |

---

## 3. Processo de Aprovação Human-in-the-Loop

1. **Analista de dados**: valida métricas offline no MLflow.
2. **Analista de risco**: revisa distribuições posteriores (α, β) por braço — nenhum braço pode ter < 5% de seleções.
3. **Responsável de conformidade**: verifica guardrails e logs de suitability.
4. **Aprovação formal**: checklist assinado com MLflow `run_id` documentado no PR de deploy.

---

## 4. Rollout Canary

| Fase | Tráfego | Critério de Avanço |
|------|---------|-------------------|
| Canary | 10% | Latência p95 < 200ms, error rate < 1% por 30 min |
| Staged | 50% | Reward médio ≥ threshold por 2h |
| Full | 100% | Zero alertas ativos no Azure Monitor |

---

## 5. Critérios de Rollback Automático

O sistema aciona rollback automático se:
- Reward médio < 8% por 2 horas consecutivas.
- Taxa de erro 5xx > 1%.
- Latência P95 > 500ms por 5 minutos.

---

## 6. Registro de Experimentos (MLflow)

Cada experimento deve registrar:
- `policy_name`, `policy_version`, `seed`
- Métricas: `avg_reward`, `cumulative_regret`, `best_arm_pct`
- Artefatos: `policy_state.pkl`, CSV de avaliação offline
- Tags: `environment` (dev/staging/prod), `promoted_by`, `promotion_date`

---

## 7. Multi-seed Stability

Antes da promoção, o experimento deve ser executado com pelo menos 5 sementes (0, 7, 42, 123, 999). O coeficiente de variação do `avg_reward` entre sementes deve ser < 5%.
