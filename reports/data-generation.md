# Relatório de Geração de Dados — OfferExp

**Projeto**: Datathon 7MLET — Plataforma de Experimentação Adaptativa  
**Grupo**: 77 — Geremias Francisco / Wagner Ulisses  
**Data**: Junho 2025  
**Script de geração**: `data/synthetic_enrichment/generate_synthetic_data.py`

---

## 1. Fonte de Dados Base

| Campo | Valor |
|-------|-------|
| Dataset | Bank Marketing Dataset |
| Fonte | Kaggle — henriqueyamahata/bank-marketing |
| Versão usada | bank-additional-full.csv |
| Licença | CC0: Public Domain |
| Registros originais | 41.188 clientes |
| Período da campanha | 2008–2010 (banco português) |
| Target original | `y` — adesão ao depósito a prazo |

---

## 2. Tratamentos na Base Original

### 2.1 Remoção de Data Leakage

| Coluna removida | Motivo |
|----------------|--------|
| `duration` / `duracao_contato` | Informação disponível **somente após** o contato. Uso desta variável causaria data leakage, inflando artificialmente qualquer métrica de conversão. |

**Decisão**: variável descartada integralmente. Não é usada em nenhuma etapa do pipeline.

### 2.2 Tradução de Colunas

Todas as colunas foram traduzidas para português para facilitar interpretação. Mapeamento completo disponível em `notebooks/01-eda-e-baseline.ipynb`.

### 2.3 Features Derivadas

| Feature | Origem | Regra |
|---------|--------|-------|
| `cliente_ja_contatado` | `dias_desde_ultimo_contato` | `(dias_desde_ultimo_contato != 999).astype(int)` |
| `faixa_contatos` | `numero_contatos_campanha` | Bins: 1, 2-3, 4-5, 6-10, 11-20, 20+ |

---

## 3. Enriquecimento Sintético

### 3.1 Sementes Aleatórias

| Componente | Seed |
|------------|------|
| Geração de eventos | 42 |
| Atribuição de braços | 42 |
| Delayed rewards | 42 |

Seed 42 fixada em todos os componentes para reprodutibilidade total.

### 3.2 Catálogo de Braços (`offer_catalog.csv`)

| arm_id | arm_name | Tipo | Descrição |
|--------|----------|------|-----------|
| 0 | sem_oferta | controle | Grupo controle — sem oferta ativa |
| 1 | educacao_financeira | conteúdo | Conteúdo educativo sobre organização financeira |
| 2 | simulador_credito | ferramenta | Simulador de crédito para avaliar opções |
| 3 | cartao_premium | produto | Oferta de cartão premium com benefícios |

### 3.3 Eventos de Oferta (`offer_events.csv`) — Schema

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `event_id` | string | Identificador único do evento |
| `subject_key` | string | Identificador pseudoanonimizado do cliente |
| `occurred_at` | datetime | Timestamp simulado |
| `channel` | string | Canal: app, email, web, whatsapp |
| `arm_id` | int | Braço servido (0–3) |
| `arm_name` | string | Nome do braço |
| `reward` | int | Conversão observada: 0 ou 1 |
| + features do cliente | variadas | Contexto demográfico e econômico da base Kaggle |

**Hipótese de geração**: braço atribuído aleatoriamente (random logging), adequado para avaliação offline via replayer method (Li et al., 2011).

**Taxa de conversão por braço**:
- `cartao_premium`: ~11.9% (melhor braço)
- `educacao_financeira`: ~11.1%
- `sem_oferta`: ~11.1%
- `simulador_credito`: ~11.0%

### 3.4 Recompensas Atrasadas (`delayed_rewards.csv`) — Schema adicional

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `delay_days` | int | Atraso em dias até observação da recompensa |
| `reward_observed_at` | datetime | Timestamp da observação real |
| `reward_type` | string | conversao_observada / sem_conversao_observada |
| `reward_status` | string | converted / not_converted |

**Modelagem do atraso**: distribuição triangular (mínimo=0, moda=3, máximo=14 dias).  
**Horizonte temporal**: 14 dias. Recompensas além desse prazo são tratadas como não-conversão.

---

## 4. Golden Set (`data/golden_set/evaluation_cases.jsonl`)

25 casos versionados para avaliação qualitativa da política.

| Tipo | Qtd | Cobertura |
|------|-----|-----------|
| typical | 5 | Perfis comuns de clientes |
| edge | 5 | Limites: cold-start, contexto vazio, fadiga de contato |
| segment | 5 | Fairness: profissão, canal, escolaridade |
| adversarial | 5 | Abuso: reward hacking, flood, menor de idade, injeção de campo |
| extra | 5 | Cobertura complementar |

Cada caso contém: `context`, `expected_arm_id`, `expected_arm_name`, `expected_reward`, `justificativa`, `pass_criteria`.

---

## 5. Limitações e Riscos

| Limitação | Impacto | Mitigação |
|-----------|---------|-----------|
| Taxas de conversão homogêneas entre braços | Thompson Sampling tem vantagem pequena sobre Random | Esperado — demonstra robustez em cenários difíceis |
| Sem dados reais de clientes | Não representa comportamento financeiro real | Aviso explícito em todos os documentos |
| Seed única | Reduz variabilidade amostral | Múltiplos seeds testados no Notebook 06 |
| Canais sem diferenciação de taxa | Canal não influencia reward | Simplificação consciente para MVP |
| Delayed rewards não integrados na política online | Loop de atualização não considera atraso | Versão futura com Azure Service Bus |
