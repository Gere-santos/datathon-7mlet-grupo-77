# Relatório Técnico — OfferExp: Plataforma de Experimentação Adaptativa para Ofertas Financeiras

**Datathon 7MLET — Pós-Tech FIAP**  
**Grupo 77**: Geremias Francisco (geremias_cte@hotmail.com) · Wagner Ulisses Fontalva (wagner.ulisses@gmail.com)  
**Versão**: 1.0.0 · **Data**: Junho 2025

---

## 1. Problema

Instituições financeiras digitais enfrentam o desafio de decidir, em tempo real e em múltiplos canais (web, app, e-mail, WhatsApp), qual oferta, mensagem ou próximo passo apresentar a cada cliente elegível. Abordagens tradicionais como regras fixas e testes A/B apresentam limitações estruturais: regras fixas não se adaptam à mudança de comportamento dos clientes, enquanto testes A/B desperdiçam tráfego ao manter braços sabidamente inferiores ativos por períodos longos.

O **OfferExp** endereça esse problema com uma plataforma de experimentação adaptativa baseada em Multi-Armed Bandits (MAB): o sistema aprende continuamente qual oferta maximiza conversão, equilibrando exploração de novas possibilidades com explotação do melhor braço observado, sem congelar decisões em regras estáticas.

**Objetivo técnico**: projetar uma solução end-to-end de Machine Learning Engineering que demonstre maturidade em formulação do problema, construção de baselines, versionamento de dados, serviço de componentes, avaliação de qualidade, monitoramento de risco, documentação de limitações e explicabilidade de decisões.

---

## 2. Base de Dados e EDA

### 2.1 Fonte

**Dataset**: Bank Marketing Dataset — Kaggle (henriqueyamahata)  
**Licença**: CC0 — Domínio Público  
**Link**: https://www.kaggle.com/datasets/henriqueyamahata/bank-marketing  
**Versão usada**: `bank-additional-full.csv` — 41.188 registros, 21 colunas  
**Referência original**: Moro et al. (2014), Journal of Banking and Finance

### 2.2 Tratamento de Data Leakage

A coluna `duration` (duração do contato em segundos) foi removida. Essa variável é disponível apenas após a conclusão da chamada, tornando-a informação pós-contato — sua inclusão causaria vazamento temporal no modelo de decisão. Todas as demais variáveis descrevem o perfil do cliente antes do contato.

### 2.3 Colunas traduzidas e features derivadas

| Feature original | Feature traduzida | Tipo |
|----------------|------------------|------|
| `age` | `idade` | Numérica |
| `job` | `profissao` | Categórica |
| `marital` | `estado_civil` | Categórica |
| `education` | `escolaridade` | Categórica |
| `contact` | `tipo_contato` | Categórica |
| `campaign` | `numero_contatos_campanha` | Numérica |
| `pdays` | `dias_desde_ultimo_contato` | Numérica |
| `y` | `conversao` | Binária (target) |

**Features derivadas**:
- `cliente_ja_contatado`: 1 se `dias_desde_ultimo_contato != 999`, 0 caso contrário.
- `faixa_contatos`: categorização de `numero_contatos_campanha` em 6 faixas (1, 2-3, 4-5, 6-10, 11-20, 20+).

### 2.4 Principais achados da EDA

- Taxa geral de conversão: **11,3%** — problema altamente desbalanceado.
- Canal `cellular` apresenta taxa de conversão 2× superior ao canal `telephone`.
- Clientes com `escolaridade=university.degree` convertem a taxas ~40% acima da média.
- Intensidade de contato tem relação inversa com conversão: clientes com 6+ contatos convertem menos.
- Variáveis macroeconômicas (`emp.var.rate`, `euribor3m`) apresentam forte correlação com conversão.

---

## 3. Enriquecimento Sintético

A base Kaggle foi usada como referência factual para construir uma **camada sintética de experimentação adaptativa**, fisicamente separada da base original:

### 3.1 Estrutura dos artefatos sintéticos

| Arquivo | Conteúdo |
|---------|---------|
| `data/synthetic_enrichment/offer_catalog.csv` | Catálogo dos 4 braços de oferta |
| `data/synthetic_enrichment/offer_events.csv` | Eventos de impressão com contexto e recompensa |
| `data/synthetic_enrichment/delayed_rewards.csv` | Recompensas com atraso uniforme: [1–14] dias (conversão) / [1–7] dias (não-conversão) |

### 3.2 Catálogo de braços (ofertas)

| arm_id | arm_name | Tipo | Taxa base |
|--------|----------|------|-----------|
| 0 | sem_oferta | Controle | ~11,1% |
| 1 | educacao_financeira | Conteúdo educativo | ~11,1% |
| 2 | simulador_credito | Ferramenta interativa | ~11,0% |
| 3 | cartao_premium | Produto financeiro | ~11,9% |

A taxa base intencional é próxima entre braços para refletir o desafio real de distinguir o melhor braço sob incerteza.

### 3.3 Modelagem de delayed rewards

Recompensas atrasadas foram modeladas com distribuição uniforme discreta independente por resultado:
- **Conversão** (`reward=1`): atraso uniforme em **[1, 14] dias** — simula o tempo até confirmação do produto.
- **Não-conversão** (`reward=0`): atraso uniforme em **[1, 7] dias** — ausência de resposta detectada mais rapidamente.

O arquivo `delayed_rewards.csv` contém `event_id`, `reward_observed_at` e `delay_days` para cada evento. Semente `RANDOM_SEED=42` garante reprodutibilidade. Detalhes em `data/synthetic_enrichment/README.md`.

### 3.4 Hipóteses de geração

- Taxas de conversão por braço derivadas da taxa base real do dataset com perturbação σ=0,001.
- Contexto de cada evento amostrado diretamente das linhas do dataset original (preservando distribuição real de perfis).
- Sementes aleatórias documentadas em `reports/data-generation.md` para reprodutibilidade.

---

## 4. Modelagem como Multi-Armed Bandit

### 4.1 Formulação do problema

O problema é modelado como um **bandit estocástico estacionário com recompensas Bernoulli**:
- **Braços**: 4 ofertas financeiras.
- **Recompensa**: `r ∈ {0, 1}` — conversão (1) ou não-conversão (0).
- **Objetivo**: maximizar reward cumulativo (equivalente a minimizar regret).

### 4.2 Políticas implementadas

**Baseline determinístico — Greedy Policy**  
Seleciona o braço com maior taxa média histórica. Nunca explora após convergência inicial. Serve como referência determinística simples.

**Política adaptativa — Thompson Sampling**  
Exploração bayesiana com prior Beta(1,1) por braço:

$$\text{Para cada braço } i: \quad \tilde{\theta}_i \sim \text{Beta}(\alpha_i, \beta_i)$$
$$\text{Seleciona: } \arg\max_i \tilde{\theta}_i$$

**Update a cada observação**:
- Conversão (r=1): α_i += 1  
- Não-conversão (r=0): β_i += 1

O prior Beta(1,1) é equivalente à distribuição uniforme — qualquer braço tem probabilidade igual no cold-start, sem favorecer nenhuma oferta a priori.

**Referência — Nilos-UCB**  
Variante da família UCB com bound analítico:

$$\text{UCB}_i(t) = \hat{\mu}_i + \sqrt{\frac{2 \ln t}{n_i}}$$

Braços não explorados recebem UCB = ∞, garantindo que cada braço seja visitado ao menos uma vez antes da comparação. Implementado no Notebook 07 como referência de comparação.

### 4.3 Escolha do algoritmo principal

Thompson Sampling foi escolhido como política principal pelos seguintes motivos:
1. **Melhor convergência empírica** em cenários com poucos dados por braço (evidência nos experimentos offline).
2. **Incerteza bayesiana**: os parâmetros α e β são diretamente auditáveis e interpretáveis por analistas de negócio.
3. **Exploração naturalmente equilibrada**: a distribuição posterior captura tanto a incerteza epistêmica (poucos dados) quanto a aleatoriedade do processo.
4. **Cold-start**: o prior Beta(1,1) distribui explorações de forma probabilística sem travar em um único braço.

### 4.4 Tratamento de cold-start

Ao inicializar o sistema (α=1, β=1 para todos os braços), Thompson Sampling se comporta como uma política uniforme — qualquer braço pode ser selecionado. Após as primeiras observações, os parâmetros divergem e o sistema começa a convergir para o braço com maior taxa de conversão. O experimento de cold-start (Notebook 07) demonstra recuperação em menos de 20 rodadas.

### 4.5 Tratamento de recompensas atrasadas

Na implementação atual (v1), o update é sincrônico: a política só é atualizada ao receber o `POST /reward`. A API mantém um dicionário `_pending` que associa `event_id` ao braço selecionado, permitindo que rewards sejam registrados com atraso. Na arquitetura Azure, o Azure Service Bus desacopla o recebimento da reward do update do estado, garantindo que rewards atrasados de até 14 dias sejam processados corretamente.

---

## 5. Comparação Quantitativa

### 5.1 Método de avaliação: Replayer Offline

A avaliação offline utiliza o **Replayer Method** (Li et al., 2011), que oferece estimativa imparcial de reward ao selecionar apenas os eventos em que a política teria escolhido o mesmo braço que o evento histórico. Isso elimina o viés de seleção inerente à avaliação de políticas em dados históricos.

### 5.2 Resultados

| Métrica | Random | Greedy | Nilos-UCB | Thompson Sampling |
|---------|--------|--------|-----------|------------------|
| Reward médio | ~11,0% | ~11,2% | ~11,5% | ~11,8% |
| Regret acumulado (5k rounds) | Alto (linear) | Médio | Sublinear | Sublinear (menor) |
| % seleções no melhor braço | ~25% | ~60% | ~65% | ~70% |
| Diversidade de exploração | Alta (uniforme) | Baixa (trava) | Alta (sistemática) | Alta (probabilística) |

Thompson Sampling apresenta o melhor trade-off entre reward médio e regret acumulado. O Greedy converge mais rápido inicialmente, mas falha em explorar e pode travar em braços sub-ótimos.

### 5.3 Multi-seed stability

O Notebook 06 registra experimentos com 5 sementes aleatórias (0, 7, 42, 123, 999) no MLflow, demonstrando que os resultados de Thompson Sampling são estáveis: coeficiente de variação do reward médio < 2% entre sementes.

---

## 6. Serviço de Decisão

### 6.1 Arquitetura da API

A decisão é exposta via **FastAPI** com contrato documentado por Pydantic v2:

```
POST /decide   → { event_id, context } → { arm_id, arm_name, reason_codes, policy_version }
POST /reward   → { event_id, arm_id, reward }  → atualiza posterior Beta
GET  /stats    → { arms: [{ arm_id, alpha, beta, reward_rate }] }
POST /assistant/ask     → pergunta em linguagem natural ao assistente LLM
POST /assistant/explain → explicação de uma decisão específica
GET  /health   → { status: "ok", policy: "thompson-v1" }
```

### 6.2 Log auditável de decisões

Cada decisão é registrada em `logs/decision_log.jsonl` (append-only) com:

```json
{
  "decision_id": "uuid",
  "event_id": "string",
  "arm_id": 3,
  "arm_name": "cartao_premium",
  "reward": 1,
  "policy_version": "thompson-v1",
  "reason_codes": ["thompson_sample_arm_3"],
  "timestamp": "2025-06-01T10:00:00Z"
}
```

### 6.3 Assistente LLM

O módulo `assistant.py` expõe um assistente com três funções:
- `ask()`: responde perguntas sobre o experimento em linguagem natural.
- `explain_decision()`: explica em português por que determinada oferta foi selecionada.
- `summarize_experiment()`: resume métricas de um experimento.

Suporta Anthropic Claude (`ANTHROPIC_API_KEY`) ou Azure OpenAI (`AZURE_OPENAI_ENDPOINT`) com fallback para modo offline (stub) quando nenhuma chave está configurada.

---

## 7. Arquitetura-Alvo Azure

A plataforma é projetada para operar exclusivamente na **Microsoft Azure** com os seguintes componentes:

| Camada | Serviço Azure | Função |
|--------|--------------|--------|
| Entrada | Azure API Management | Rate limiting, autenticação OAuth2/JWT |
| Computação | Azure Container Apps | FastAPI — escalonamento automático |
| Estado | Azure Cosmos DB | Parâmetros α, β por braço (baixa latência) |
| Logs | Azure Blob Storage | Decision log JSONL imutável (WORM) |
| Mensageria | Azure Service Bus | Fila de delayed rewards assíncronos |
| MLOps | Azure ML + MLflow | Tracking de experimentos, model registry |
| IA Generativa | Azure OpenAI Service | Assistente de explicabilidade (GPT-4o) |
| RAG | Azure AI Search | Recuperação semântica sobre logs e políticas |
| Observabilidade | Azure Monitor + App Insights | Métricas de infra e aplicação |
| Segurança | Azure Key Vault + AAD | Segredos, Managed Identity |

**Estimativa de custo (ambiente dev/staging)**: ~US$ 76/mês.

**Alternativas descartadas**:
- AWS/GCP: descartados pela restrição de usar exclusivamente Azure.
- Kubernetes direto (AKS): descartado em favor de Container Apps pelo menor overhead operacional para este porte.
- Redis para estado: descartado em favor de Cosmos DB pelo suporte nativo a consistência e persistência.

---

## 8. Ciclo de Vida MLOps

### 8.1 Rastreamento com MLflow

Cada experimento registra no MLflow: `policy_name`, `policy_version`, `seed`, métricas por rodada (`avg_reward`, `cumulative_regret`), parâmetros de política e artefatos (`policy_state.pkl`, CSVs de avaliação).

### 8.2 Critérios de promoção para produção

| Métrica | Threshold |
|---------|-----------|
| avg_reward | > baseline random + 5% |
| final_regret | < baseline random em 20% |
| best_arm_pct | > 25% |
| Testes automatizados | 100% passando |
| Golden set (25 casos) | 100% pass_criteria atendidos |

### 8.3 Deploy canary

- **Fase 1 (5%)**: 5% do tráfego, monitorar 24h.
- **Fase 2 (25%)**: expandir se reward médio ≥ threshold, monitorar 48h.
- **Fase 3 (100%)**: promoção total após aprovação humana.

### 8.4 Human-in-the-loop

Promoção para produção requer checklist assinado por analista: validação de métricas offline, revisão das distribuições posteriores, ausência de braço com < 5% de seleções, MLflow `run_id` documentado no PR de deploy.

### 8.5 Rollback

Rollback automático é acionado se: reward médio < 8% por 2h, taxa de erro 5xx > 1%, latência P95 > 500ms por 5min. Azure Container Apps reverte automaticamente para a revisão anterior via `az containerapp revision deactivate`.

---

## 9. Governança e Conformidade LGPD

O sistema utiliza exclusivamente **dados sintéticos e públicos** (Kaggle CC0). Em um cenário de produção hipotético, as seguintes medidas de conformidade com a LGPD (Lei nº 13.709/2018) seriam aplicadas:

- **Minimização**: apenas `event_id` pseudoanonimizado, sem CPF, nome ou dados sensíveis.
- **Finalidade**: dados usados exclusivamente para seleção de ofertas e auditoria.
- **Transparência**: `reason_codes` em cada decisão; assistente LLM para explicações.
- **Retenção**: decision logs por 5 anos; logs de API por 90 dias.
- **Segurança**: Blob Storage com Customer-Managed Key (CMK), acesso via Managed Identity.
- **Incidentes**: notificação à ANPD em até 72h (art. 48 da LGPD).

Detalhes completos em `docs/lgpd-plan.md`.

---

## 10. Limitações

1. **Modelo não-contextual**: Thompson Sampling na versão atual não considera features do cliente (idade, profissão) na seleção — trata todos os clientes identicamente. A extensão natural é **LinUCB** ou **Thompson Sampling Contextual** (LinThompson), que incorporaria o vetor de features na estimativa de reward esperado.

2. **Dados sintéticos**: as taxas de conversão por braço foram derivadas artificialmente com pequenas perturbações sobre a taxa base real. Em produção, as taxas reais podem diferir significativamente e ter variância maior.

3. **Estacionariedade**: o modelo assume que as taxas de conversão são estacionárias. Em contextos reais, sazonalidade (ex.: campanhas de fim de ano) e mudanças macroeconômicas podem tornar o modelo obsoleto rapidamente.

4. **Delayed rewards versão 1**: o tratamento atual de recompensas atrasadas é funcional mas simples — rewards são aceitos a qualquer momento após a decisão, sem janela de expiração. Em produção, rewards com delay > 30 dias deveriam ser descartados para evitar contaminação do aprendizado.

5. **Escalabilidade do estado**: o estado dos braços (α, β) é mantido em memória na versão local. Em produção de alta escala, múltiplas instâncias da API precisariam sincronizar o estado via Cosmos DB, introduzindo latência adicional.

---

## 11. Riscos

| Risco | Severidade | Probabilidade | Mitigação |
|-------|-----------|---------------|-----------|
| Reward hacking | Alta | Média | Validação de range [0,1], monitoramento de anomalia |
| Drift de comportamento | Alta | Alta | Monitoramento de reward médio; retreino periódico |
| Braço dominante sem exploração | Média | Baixa | Guardrail: nenhum braço < 5% de seleções |
| Abuso do assistente LLM | Média | Baixa | System prompt com restrições; logs auditáveis |
| Suitability inadequada | Alta | Baixa | Guardrails de idade, inadimplência, fadiga de contato |

Detalhes completos dos cenários de risco em `docs/system-card.md`.

---

## 12. Hipóteses e Premissas

1. **Recompensas Bernoulli independentes**: cada interação é independente das anteriores — não há efeito de memória do cliente (ex.: cansaço de ofertas repetidas). Hipótese simplificadora justificada para o cenário sintético.

2. **Estacionariedade das taxas**: as taxas de conversão por braço não variam no tempo durante o experimento.

3. **Separação braço/contexto**: os braços são ofertas genéricas, não personalizadas — a mesma oferta tem o mesmo efeito esperado para qualquer perfil de cliente.

4. **Representatividade do enriquecimento sintético**: a camada sintética preserva a distribuição real de perfis do dataset Kaggle, mas as taxas de conversão por braço são simuladas.

---

## 13. Trabalhos Futuros

1. **Thompson Sampling Contextual (LinThompson)**: incorporar features do cliente no modelo de recompensa esperada, transformando o MAB em um bandit contextual.

2. **Delayed reward com janela de validade**: implementar expiração de rewards não recebidos após janela configurável, com heurística de imputação para eventos expirados.

3. **Fairness awareness**: extender o modelo com restrições de fairness que garantam taxa mínima de exposição do melhor braço para grupos historicamente sub-servidos.

4. **A/B testing híbrido**: combinar MAB com testes A/B formais para validação estatística rigorosa antes da promoção para produção.

5. **Feedback loop completo**: integrar o pipeline de dados com Azure ML Pipeline para retreino automático baseado em dados reais de produção.

6. **Interface de monitoramento**: dashboard em Power BI ou Grafana para visualização em tempo real das distribuições Beta por braço, métricas de fairness e alertas de drift.

---

## Referências

1. Li, L., Chu, W., Langford, J., & Schapire, R. E. (2011). An unbiased offline evaluation of contextual-bandit algorithms with generalized linear models. *Proceedings of the Workshop on On-line Trading of Exploration and Exploitation*.

2. Thompson, W. R. (1933). On the likelihood that one unknown probability exceeds another in view of the evidence of two samples. *Biometrika*, 25(3-4), 285-294.

3. Auer, P., Cesa-Bianchi, N., & Fischer, P. (2002). Finite-time analysis of the multiarmed bandit problem. *Machine Learning*, 47(2-3), 235-256.

4. Chapelle, O., & Li, L. (2011). An empirical evaluation of Thompson sampling. *Advances in Neural Information Processing Systems*, 24.

5. Moro, S., Cortez, P., & Rita, P. (2014). A data-driven approach to predict the success of bank telemarketing. *Decision Support Systems*, 62, 22-31.

6. Russo, D. J., Van Roy, B., Kazerouni, A., Osband, I., & Wen, Z. (2018). A tutorial on Thompson sampling. *Foundations and Trends in Machine Learning*, 11(1), 1-96.

7. Lei nº 13.709/2018 — Lei Geral de Proteção de Dados Pessoais (LGPD). Brasília: Presidência da República, 2018.

8. Microsoft Azure Documentation — Container Apps, Cosmos DB, Azure ML, Azure OpenAI. https://learn.microsoft.com/azure.
