# Datathon 7MLET — Plataforma de Experimentação Adaptativa para Ofertas Financeiras

> Projeto desenvolvido para o Datathon 7MLET da Pós-Tech FIAP com foco em **Multi-Armed Bandits**, **MLOps**, **LLMOps**, **Governança de IA** e **Arquitetura Azure**.

---

# Visão Geral

Este projeto propõe a construção de uma plataforma inteligente capaz de decidir automaticamente qual oferta, mensagem ou próximo passo apresentar a um cliente em canais digitais.

A solução utiliza uma base pública do Kaggle como referência factual e cria uma camada sintética de experimentação adaptativa para simular:

* ofertas financeiras;
* canais de comunicação;
* recompensas observadas;
* recompensas atrasadas (Delayed Rewards);
* políticas adaptativas de decisão.

O objetivo é comparar abordagens tradicionais de decisão com algoritmos de **Multi-Armed Bandits**, permitindo aprendizado contínuo e otimização de resultados.

---

# Problema de Negócio

Instituições financeiras realizam milhares de interações diariamente com clientes elegíveis para diferentes produtos e serviços.

Métodos tradicionais como:

* regras estáticas;
* segmentações fixas;
* campanhas manuais;
* testes A/B convencionais;

possuem limitações importantes:

Demoram para reagir a mudanças de comportamento.

Desperdiçam tráfego em ofertas pouco eficientes.

Possuem baixa capacidade de personalização.

Dificultam auditoria e explicabilidade.

Este projeto propõe uma abordagem adaptativa baseada em aprendizado contínuo.

---

# Objetivos

## Objetivo Principal

Construir uma plataforma capaz de:

 Selecionar automaticamente ofertas.

 Aprender com recompensas observadas.

 Explicar decisões.

 Monitorar desempenho.

 Garantir rastreabilidade e governança.

---

## Objetivos Técnicos

*  Pipeline de dados reproduzível.
*  Baseline determinístico.
*  Thompson Sampling.
*  Avaliação offline.
*  API de decisão.
*  Logs auditáveis.
*  Observabilidade.
*  Arquitetura Microsoft Azure.
*  Governança e LGPD.

---

# Dataset

## Base Escolhida

**Bank Marketing Dataset**

 https://www.kaggle.com/datasets/henriqueyamahata/bank-marketing

### Justificativa

A base contém informações relacionadas a campanhas bancárias e conversão de clientes, sendo adequada para:

* marketing financeiro;
* recomendação de ofertas;
* campanhas adaptativas;
* modelagem de propensão à conversão.

---

##  Variável Alvo

| Coluna | Descrição                        |
| ------ | -------------------------------- |
| y      | Conversão do cliente na campanha |

---

## Tratamento de Vazamento Temporal

A coluna abaixo será removida da modelagem:

| Coluna   | Motivo                                     |
| -------- | ------------------------------------------ |
| duration | Informação conhecida apenas após o contato |

O uso dessa variável geraria **data leakage**, comprometendo a validade da avaliação.

---

# Arquitetura Conceitual

```text
Base Kaggle
     │
     ▼
Tratamento de Dados
     │
     ▼
Enriquecimento Sintético
     │
     ▼
Baseline
     │
     ▼
Thompson Sampling
     │
     ▼
API de Decisão
     │
     ▼
Decision Logs
     │
     ▼
Monitoramento
```

---

# Estrutura do Projeto

```text
datathon-7mlet-grupo-77/
├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
├── LICENSE
├── Makefile
├── data/
│   ├── kaggle/
│   │   └── README.md
│   ├── synthetic_enrichment/
│   │   ├── offer_catalog.csv
│   │   ├── offer_events.csv
│   │   ├── delayed_rewards.csv
│   │   └── generate_synthetic_data.py
│   └── golden_set/
│       └── evaluation_cases.jsonl     # 25 casos de teste
├── docs/
│   ├── architecture-azure.md          # diagrama Mermaid + custo Azure
│   ├── model-card.md                  # limitações, fairness, rastreabilidade
│   ├── system-card.md                 # riscos, cenários adversariais
│   ├── lgpd-plan.md                   # conformidade LGPD
│   └── mlops-lifecycle.md             # canary deploy, rollback, human-in-the-loop
├── notebooks/
│   ├── 01-eda-e-baseline.ipynb        # EDA + baseline estatístico
│   ├── 02-synthetic-enrichment.ipynb  # geração de dados sintéticos
│   ├── 03-baseline.ipynb              # políticas Random e Greedy
│   ├── 04-thompson-sampling.ipynb     # Thompson Sampling Beta conjugado
│   ├── 05-offline-evaluation.ipynb    # Replayer Method + golden set
│   ├── 06-mlflow-experiments.ipynb    # experimentos multi-seed + Model Registry
│   ├── 07-nilos-ucb-fairness.ipynb    # Nilos-UCB, cold-start, fairness
│   ├── 08-mlops-promotion-demo.ipynb  # promoção, gate check, rollback
│   ├── 09-monitoring-dashboard.ipynb  # drift, alertas, dashboard
│   └── 10-banca-demo.ipynb            # demonstração ponta a ponta para banca
├── reports/
│   ├── data-generation.md
│   ├── relatorio-tecnico.md           # relatório técnico completo
│   ├── golden_set_results.json
│   ├── promotion_record.json
│   ├── retrain_record.json
│   ├── monitoring_report.json
│   └── *.png                          # gráficos gerados pelos notebooks
├── scripts/
│   ├── run_golden_set.py              # avaliação offline reproduzível (CLI)
│   └── run_demo.sh                    # pipeline ponta a ponta (make demo)
├── src/
│   └── datathon_offerexp/
│       ├── __init__.py
│       ├── contracts.py               # Pydantic v2: DecisionRequest/Response
│       ├── policies.py                # Random, Greedy, ThompsonSampling
│       ├── evaluation.py              # Replayer Method, compute_regret
│       ├── decision_log.py            # log auditável JSONL append-only
│       ├── mlflow_utils.py            # rastreamento SQLite backend
│       ├── assistant.py               # assistente LLM (Anthropic / Azure / stub)
│       └── app.py                     # FastAPI: /decide /reward /stats /health
└── tests/
    ├── test_contracts.py              # contratos Pydantic
    ├── test_policies.py               # políticas de decisão
    ├── test_decision_log.py           # log auditável
    ├── test_mlflow_utils.py           # rastreamento MLflow
    └── test_assistant.py              # assistente LLM
```

---

# Componentes Principais

## Política Adaptativa

Algoritmo principal:

* Thompson Sampling

Referências complementares:

* Nilos-UCB
* LinUCB

---

## Catálogo de Ofertas

Braços simulados:

| Braço               |
| ------------------- |
| sem_oferta          |
| educacao_financeira |
| simulador_credito   |
| cartao_premium      |

---

## Logs Auditáveis

Cada decisão registra:

* Decision ID
* Event ID
* Policy Version
* Braço selecionado
* Reward
* Timestamp
* Reason Codes

---

## Trabalhos Futuros

* **Assistente com LLM** — integração com Azure OpenAI para explicar decisões em linguagem natural, resumir experimentos e recuperar políticas via RAG. Não implementado nesta versão por não ser requisito do escopo atual.
* **Thompson Contextual (LinThompson)** — incorporar features do cliente na seleção do braço.
* **Fairness constraints** — taxa mínima de exposição por segmento demográfico.

---

# Observabilidade

## Métricas Técnicas

* Latência
* Throughput
* Disponibilidade
* Taxa de erro

## Métricas de Negócio

* Reward médio
* Conversão
* Regret acumulado
* Taxa de exploração
* Fairness entre segmentos

---

#  Governança

A solução contempla:

*  Model Card
*  System Card
*  Fairness Review
*  LGPD Plan
*  Guardrails
*  Human-in-the-loop

---

#  Tecnologias

| Categoria     | Ferramentas     |
| ------------- | --------------- |
| Linguagem     | Python 3.11     |
| Dados         | Pandas, NumPy   |
| ML            | Scikit-Learn    |
| API           | FastAPI         |
| Testes        | Pytest          |
| Qualidade     | Ruff, MyPy      |
| MLOps         | MLflow          |
| Cloud         | Microsoft Azure |

---

#  Execução Local

### Pipeline ponta a ponta (comando único)

```bash
make demo
```

Equivalente a:

```bash
bash scripts/run_demo.sh
```

O script executa em sequência: instala dependências → verifica dados sintéticos → roda os 33 testes → executa o golden set → exibe instruções para iniciar a API.

### Passo a passo manual

#### Criar e ativar ambiente virtual

> Requer Python 3.11. Verifique com `python3.11 --version` antes de prosseguir.

Linux / Mac:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

Windows:

```bash
py -3.11 -m venv .venv
.venv\Scripts\activate
```

#### Instalar dependências

```bash
pip install -e ".[dev]"
```

#### Executar testes

```bash
make test
# ou: python -m pytest tests/ -v
```

#### Iniciar API

```bash
make api
# ou: uvicorn src.datathon_offerexp.app:app --reload --host 0.0.0.0 --port 8000
# Swagger UI: http://localhost:8000/docs
```

---

# Contrato da API — Exemplos de Chamada

A API deve estar rodando em `http://localhost:8000` (`make api`).

## GET /health

```bash
curl http://localhost:8000/health
```

```json
{"status": "ok", "policy": "thompson-v1"}
```

## POST /decide

Recebe um contexto de cliente e devolve a oferta selecionada pela política.

```bash
curl -s -X POST http://localhost:8000/decide \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "evt-001",
    "subject_key": "cliente-123",
    "context": {
      "idade": 35,
      "profissao": "engenheiro",
      "escolaridade": "superior"
    }
  }'
```

**Resposta (200)**:

```json
{
  "event_id": "evt-001",
  "arm_id": 2,
  "arm_name": "simulador_credito",
  "policy_version": "thompson-v1",
  "reason_codes": ["thompson_sample_arm_2"],
  "decided_at": "2025-01-15T10:30:00.000000"
}
```

**Erro — campos obrigatórios ausentes (422)**:

```bash
curl -s -X POST http://localhost:8000/decide \
  -H "Content-Type: application/json" \
  -d '{"event_id": "evt-001"}'
```

```json
{
  "detail": [{"type": "missing", "loc": ["body", "subject_key"], "msg": "Field required"}]
}
```

## POST /reward

Registra a recompensa observada e atualiza a distribuição Beta do braço.

```bash
curl -s -X POST http://localhost:8000/reward \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "evt-001",
    "arm_id": 2,
    "reward": 1.0
  }'
```

**Resposta (200)**:

```json
{"status": "updated", "arm_id": 2, "reward": 1.0}
```

**Erro — event_id não encontrado (404)**:

```bash
curl -s -X POST http://localhost:8000/reward \
  -H "Content-Type: application/json" \
  -d '{"event_id": "nao-existe", "arm_id": 2, "reward": 1.0}'
```

```json
{"detail": "event_id não encontrado ou recompensa já registrada"}
```

**Erro — arm_id diverge da decisão registrada (400)**:

```json
{"detail": "arm_id não corresponde à decisão registrada"}
```

## GET /stats

Retorna as distribuições Beta atuais de todos os braços.

```bash
curl http://localhost:8000/stats
```

```json
{
  "policy_version": "thompson-v1",
  "total_decisions": 1,
  "arms": [
    {"arm_id": 0, "arm_name": "sem_oferta",          "trials": 0, "successes": 0, "reward_rate": 0.0, "alpha": 1.0, "beta": 1.0},
    {"arm_id": 1, "arm_name": "educacao_financeira",  "trials": 0, "successes": 0, "reward_rate": 0.0, "alpha": 1.0, "beta": 1.0},
    {"arm_id": 2, "arm_name": "simulador_credito",    "trials": 1, "successes": 1, "reward_rate": 1.0, "alpha": 2.0, "beta": 1.0},
    {"arm_id": 3, "arm_name": "cartao_premium",       "trials": 0, "successes": 0, "reward_rate": 0.0, "alpha": 1.0, "beta": 1.0}
  ]
}
```

## POST /assistant/ask

Consulta o assistente LLM sobre experimentos e métricas.

```bash
curl -s -X POST http://localhost:8000/assistant/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Qual braço está performando melhor?", "include_log_summary": true}'
```

```json
{"question": "Qual braço está performando melhor?", "answer": "..."}
```

---

#  Limitações

* Utiliza dados públicos do Kaggle.
* Utiliza enriquecimento sintético.
* Não utiliza dados reais de clientes.
* Não representa sistema financeiro real.
* Não deve ser utilizado para decisões financeiras reais.

---

#  Roadmap

| Etapa                    | Status |
| ------------------------ | ------ |
| Organização do Projeto   | ✅     |
| Base Kaggle + EDA        | ✅     |
| Enriquecimento Sintético | ✅     |
| Thompson Sampling        | ✅     |
| Avaliação Offline        | ✅     |
| API e Logs               | ✅     |
| Azure                    | ✅     |
| MLOps                    | ✅     |
| Governança               | ✅     |

---

#  Licença

Projeto desenvolvido exclusivamente para fins acadêmicos no contexto do Datathon 7MLET da Pós-Tech FIAP.

---

#  Equipe

**Grupo  — Datathon 7MLET**

- GEREMIAS FRANCISCO DE OLIVEIRA SANTOS
  - geremias_cte@hotmail.com
  
- WAGNER ULISSES FONTALVA
  - wagner.ulisses@gmail.com

Pós-Tech FIAP — Machine Learning Engineering


