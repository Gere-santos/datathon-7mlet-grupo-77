# Model Card — Thompson Sampling para Ofertas Financeiras

**Projeto**: Datathon 7MLET — Plataforma de Experimentação Adaptativa  
**Grupo**: Grupo 77 — Geremias Francisco / Wagner Ulisses  
**Versão do modelo**: `thompson-v1`  
**Data**: Junho 2025

---

## Descrição do Modelo

Algoritmo de Multi-Armed Bandit baseado em **Thompson Sampling** com distribuições Beta conjugadas para recompensas Bernoulli (conversão 0/1).

O modelo decide qual oferta financeira apresentar a um cliente, balanceando exploração de novas ofertas com explotação do melhor braço observado.

---

## Detalhes do Algoritmo

| Item | Detalhe |
|------|---------|
| Família | Multi-Armed Bandit |
| Algoritmo | Thompson Sampling |
| Prior | Beta(α=1, β=1) por braço |
| Tipo de recompensa | Bernoulli (conversão 0/1) |
| Update | Bayesiano conjugado |
| Política de seleção | argmax de amostras Beta |

**Atualização a cada decisão**:
- Conversão (reward=1): α_braço += 1
- Sem conversão (reward=0): β_braço += 1

---

## Dados de Treinamento

- **Fonte**: Bank Marketing Dataset (Kaggle) + enriquecimento sintético
- **Tamanho**: 41.188 eventos
- **Braços (ofertas)**:
  | arm_id | arm_name | Tipo |
  |--------|----------|------|
  | 0 | sem_oferta | Controle |
  | 1 | educacao_financeira | Conteúdo |
  | 2 | simulador_credito | Ferramenta |
  | 3 | cartao_premium | Produto |

- **Taxa de conversão real por braço** (oráculo):
  - `cartao_premium`: ~11.9%
  - `educacao_financeira`: ~11.1%
  - `sem_oferta`: ~11.1%
  - `simulador_credito`: ~11.0%

> **Aviso**: Os dados de treinamento são **sintéticos**, derivados de base pública do Kaggle. Não representam comportamento financeiro real.

---

## Métricas de Avaliação (Offline Replay)

| Métrica | Random | Greedy | Thompson Sampling |
|---------|--------|--------|------------------|
| Reward médio | ~11.0% | ~11.2% | ~11.8% |
| Regret acumulado | Alto (linear) | Médio | Baixo (sublinear) |
| % seleções no melhor braço | ~25% | ~60%+ | ~70%+ |

Método de avaliação: **Replayer Offline** (Li et al., 2011) — garante estimativa imparcial usando apenas eventos com braço matching.

---

## Casos de Uso Pretendidos

- Personalização de ofertas financeiras em canais digitais (web, app, e-mail, whatsapp).
- Otimização de campanhas com aprendizado contínuo.
- Experimentação adaptativa em substituição a testes A/B tradicionais.

## Casos de Uso Não Pretendidos

- Decisões de crédito ou avaliação de risco de inadimplência.
- Perfis de clientes reais — o modelo usa dados sintéticos.
- Discriminação de grupos por características protegidas (raça, gênero, religião).

---

## Limitações

- Modelo não é contextual (não considera features do cliente na seleção). Versão futura com LinUCB pode incorporar contexto.
- Recompensas potencialmente atrasadas não são tratadas na versão `thompson-v1`.
- Dados sintéticos podem não refletir dinâmica real do mercado.

---

## Considerações de Fairness

- Monitored: taxa de seleção por braço entre segmentos (idade, profissão).
- Os braços não são discriminatórios por natureza — oferecem conteúdo ou produtos financeiros amplos.
- Não há braço que exclua ou penalize grupos protegidos.

---

## Rastreabilidade

Cada decisão é registrada em `logs/decision_log.jsonl` com:
- `decision_id`, `event_id`, `arm_id`, `arm_name`, `reward`, `policy_version`, `reason_codes`, `timestamp`

---

## Contato

Grupo 77 — Pós-Tech FIAP 7MLET  
wagner.ulisses@gmail.com | geremias_cte@hotmail.com
