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

## Análise de Fairness

- Taxa de seleção por braço é monitorada entre segmentos demográficos (idade, profissão, estado civil).
- Os braços não são definidos por características protegidas — oferecem conteúdo ou produtos financeiros amplos acessíveis a qualquer perfil.
- Guardrail de suitability: menores de 18 anos recebem automaticamente `sem_oferta`; clientes em inadimplência não recebem `cartao_premium`. Esses guardrails são logados e auditáveis.
- Métrica de fairness monitorada: Δ taxa de seleção por braço entre faixas etárias deve ser < 10 pontos percentuais.

## Vieses Conhecidos

| Viés | Descrição | Mitigação |
|------|-----------|-----------|
| **Prior uniforme** | Beta(1,1) favorece exploração inicial igual — mas o primeiro braço a receber reward=1 no cold-start tem vantagem momentânea | Superado após ~20 rodadas (convergência demonstrada no Notebook 07) |
| **Taxa sintética quase-uniforme** | As taxas reais dos 4 braços são muito próximas (~11%), tornando o sinal ruidoso — Thompson pode levar centenas de rounds para distinguir o vencedor | Documentado como limitação; aceitável no MVP sintético |
| **Viés de canal** | Dataset Kaggle tem 2× mais conversões por `cellular` que `telephone` — distribuição de canais nos eventos sintéticos herda esse viés | Canal é feature de contexto, não influencia a seleção do braço diretamente |
| **Ausência de feedback negativo explícito** | reward=0 pode representar "não respondeu" ou "respondeu e rejeitou" — o modelo trata ambos como não-conversão | Limitação conhecida da modelagem Bernoulli simples; tratamento diferenciado requer dados rotulados |

---

## Rastreabilidade

Cada decisão é registrada em `logs/decision_log.jsonl` com:
- `decision_id`, `event_id`, `arm_id`, `arm_name`, `reward`, `policy_version`, `reason_codes`, `timestamp`

---

## Contato

Grupo 77 — Pós-Tech FIAP 7MLET  
wagner.ulisses@gmail.com | geremias_cte@hotmail.com
