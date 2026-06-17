# Camada de Enriquecimento Sintético

Esta pasta contém os arquivos gerados sobre a base Kaggle para criar o ambiente
de experimentação adaptativa. Os dados aqui **não são reais** — são construídos
programaticamente a partir de `data/kaggle/bank-additional-full.csv`.

**Script de geração**: `data/synthetic_enrichment/generate_synthetic_data.py`  
**Semente global**: `RANDOM_SEED = 42` (todos os geradores aleatórios)  
**Pré-requisito**: `data/processed/modeling_table.csv` gerado pelo `data/kaggle/load_kaggle.py`

Para regenerar do zero:

```bash
python data/kaggle/load_kaggle.py        # gera data/processed/modeling_table.csv
python data/synthetic_enrichment/generate_synthetic_data.py
```

---

## Arquivos

### `offer_catalog.csv` — Catálogo de Braços

Define os quatro braços (ações) do experimento adaptativo.
Separado fisicamente da base Kaggle para deixar claro que é uma decisão de design,
não um dado observado.

| Coluna | Tipo | Descrição |
|---|---|---|
| `arm_id` | int | Identificador do braço (0–3) |
| `arm_name` | str | Nome do braço |
| `arm_type` | str | Categoria: `controle`, `conteudo`, `ferramenta`, `produto` |
| `description` | str | Descrição da oferta |
| `is_control` | bool | `True` apenas para `sem_oferta` (braço de controle) |

**Como os braços foram definidos**: escolhidos para representar um espectro típico
de ações em marketing financeiro digital — de não fazer nada (`sem_oferta`) até
uma oferta de produto (`cartao_premium`). Nenhum braço é superior a priori;
o algoritmo aprende qual converter melhor pela experimentação.

| arm_id | arm_name | Tipo |
|---|---|---|
| 0 | sem_oferta | controle |
| 1 | educacao_financeira | conteúdo |
| 2 | simulador_credito | ferramenta |
| 3 | cartao_premium | produto |

---

### `offer_events.csv` — Eventos de Impressão com Contexto

41.188 eventos sintéticos — um por cliente da base Kaggle. Cada evento simula
uma impressão de oferta em um canal digital com contexto demográfico e econômico.

| Coluna | Tipo | Descrição |
|---|---|---|
| `event_id` | str | Identificador único do evento (`evt_000001` … `evt_041188`) |
| `subject_key` | str | Identificador pseudoanonimizado do cliente |
| `occurred_at` | datetime | Timestamp simulado (1 evento/minuto a partir de 2025-01-01) |
| `channel` | str | Canal: `app`, `email`, `web`, `whatsapp` — atribuído aleatoriamente |
| `arm_id` | int | Braço servido (0–3) — atribuído **uniformemente ao acaso** |
| `arm_name` | str | Nome do braço |
| `reward` | int | `1` se houve conversão, `0` caso contrário |
| `idade` … `faixa_contatos` | variados | **Contexto do cliente** — as 22 colunas da tabela processada |

**Como o contexto foi definido**: as colunas de contexto são as 22 features da
base processada (`data/processed/modeling_table.csv`), incluídas integralmente
em cada evento. Isso permite que políticas contextuais (LinUCB, etc.) as usem
sem joins adicionais.

**Como o reward foi definido**: derivado diretamente da coluna `conversao` da
base Kaggle (`yes` → 1, `no` → 0). Representa a conversão histórica observada,
usada como proxy de recompensa para avaliação offline via Replayer Method.

**Hipótese de logging aleatório**: o braço foi atribuído uniformemente ao acaso
(`rng.choice([0,1,2,3])`). Isso satisfaz a premissa do Replayer Method (Li et
al., 2011) para avaliação offline não enviesada.

---

### `delayed_rewards.csv` — Recompensas com Atraso Simulado

Mesmos 41.188 eventos, com modelagem do atraso entre a impressão e a observação
da recompensa.

| Coluna | Tipo | Descrição |
|---|---|---|
| `event_id` | str | Chave estrangeira para `offer_events.csv` |
| `subject_key` | str | Identificador do cliente |
| `occurred_at` | datetime | Timestamp da impressão da oferta |
| `channel` | str | Canal do evento |
| `arm_id` | int | Braço servido |
| `arm_name` | str | Nome do braço |
| `reward` | int | Recompensa observada (0 ou 1) |
| `delay_days` | int | Atraso em dias até observação |
| `reward_observed_at` | datetime | `occurred_at + delay_days` |
| `reward_type` | str | `conversao_confirmada` / `sem_conversao_observada` |
| `reward_status` | str | `confirmed` / `not_converted` |

**Como o horizonte temporal foi modelado**:

- **Conversão** (`reward=1`): atraso uniforme em **[1, 14] dias** — simula o tempo
  entre o clique e a confirmação do produto (ex.: aprovação de cartão).
- **Não-conversão** (`reward=0`): atraso uniforme em **[1, 7] dias** — a ausência
  de resposta é detectada mais rapidamente.
- **Horizonte efetivo**: 14 dias. Nesta versão todos os eventos têm recompensa
  determinística; em produção, eventos além do horizonte seriam tratados como
  não-conversão.

---

## Separação da Base Kaggle

```
data/
├── kaggle/                      ← base factual (CC0, Kaggle)
│   ├── bank-additional-full.csv
│   ├── load_kaggle.py
│   └── README.md
├── processed/
│   └── modeling_table.csv       ← tabela intermediária (gerada pelo load_kaggle.py)
└── synthetic_enrichment/        ← camada experimental (este diretório)
    ├── offer_catalog.csv
    ├── offer_events.csv
    ├── delayed_rewards.csv
    ├── generate_synthetic_data.py
    └── README.md  ← você está aqui
```

Os arquivos sintéticos **não modificam** a base Kaggle original. A separação de
diretórios é intencional: qualquer pessoa pode inspecionar o que é dado observado
(`kaggle/`) e o que é construção experimental (`synthetic_enrichment/`).
