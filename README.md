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
*  Assistente com LLM.
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
     │
     ▼
Assistente LLM
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
│   ├── processed/
│   ├── synthetic_enrichment/
│   └── golden_set/
├── docs/
│   ├── architecture-azure.md
│   ├── model-card.md
│   ├── system-card.md
│   └── lgpd-plan.md
├── notebooks/
│   └── 01-eda-e-baseline.ipynb
├── reports/
│   └── data-generation.md
├── src/
│   └── datathon_offerexp/
│       ├── __init__.py
│       ├── contracts.py
│       ├── policies.py
│       ├── evaluation.py
│       ├── decision_log.py
│       └── app.py
└── tests/
    ├── test_contracts.py
    ├── test_policies.py
    └── test_decision_log.py
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

## Assistente com LLM

Capacidades:

* Explicar decisões.
* Resumir experimentos.
* Consultar políticas.
* Apoiar análise humana.
* Recuperar conhecimento via RAG.

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
| IA Generativa | Azure OpenAI    |
| Cloud         | Microsoft Azure |

---

#  Execução Local

### Criar ambiente virtual

```bash
python -m venv .venv
```

### Ativar ambiente

Linux / Mac

```bash
source .venv/bin/activate
```

Windows

```bash
.venv\Scripts\activate
```

### Instalar dependências

```bash
pip install -e ".[dev]"
```

### Executar testes

```bash
pytest
```

### Iniciar API

```bash
uvicorn src.datathon_offerexp.app:app --reload
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
| Enriquecimento Sintético | ⏳      |
| Thompson Sampling        | ⏳      |
| Avaliação Offline        | ⏳      |
| API e Logs               | ⏳      |
| Azure                    | ⏳      |
| MLOps                    | ⏳      |
| Governança               | ⏳      |

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


