# Dicionário de Dados — Bank Marketing Dataset

**Fonte**: Kaggle — [henriqueyamahata/bank-marketing](https://www.kaggle.com/datasets/henriqueyamahata/bank-marketing)  
**Arquivo**: `bank-additional-full.csv`  
**Licença**: CC0: Public Domain  
**Registros**: 41.188 clientes | **Período**: 2008–2010 (banco português)

---

## Colunas Originais

| Nome original | Nome PT | Tipo | Domínio / Valores | Descrição |
|---|---|---|---|---|
| `age` | `idade` | int | 17–98 | Idade do cliente em anos |
| `job` | `profissao` | str | admin., blue-collar, entrepreneur, housemaid, management, retired, self-employed, services, student, technician, unemployed, unknown | Ocupação profissional |
| `marital` | `estado_civil` | str | divorced, married, single, unknown | Estado civil (divorced inclui viúvo) |
| `education` | `escolaridade` | str | basic.4y, basic.6y, basic.9y, high.school, illiterate, professional.course, university.degree, unknown | Nível de escolaridade |
| `default` | `inadimplencia` | str | no, yes, unknown | Possui crédito em inadimplência? |
| `housing` | `emprestimo_habitacional` | str | no, yes, unknown | Possui empréstimo habitacional? |
| `loan` | `emprestimo_pessoal` | str | no, yes, unknown | Possui empréstimo pessoal? |
| `contact` | `tipo_contato` | str | cellular, telephone | Canal de contato usado na campanha |
| `month` | `mes_contato` | str | jan–dec | Mês do último contato na campanha |
| `day_of_week` | `dia_semana` | str | mon, tue, wed, thu, fri | Dia da semana do último contato |
| `duration` | `duracao_contato` | int | segundos | **REMOVIDA — data leakage.** Duração do último contato em segundos. Disponível apenas após o contato; uso inflaria artificialmente métricas de conversão |
| `campaign` | `numero_contatos_campanha` | int | 1–56 | Número de contatos realizados nesta campanha para este cliente |
| `pdays` | `dias_desde_ultimo_contato` | int | 0–999 (999 = nunca contatado) | Dias desde o último contato em campanha anterior |
| `previous` | `numero_contatos_anteriores` | int | 0–7 | Número de contatos antes desta campanha |
| `poutcome` | `resultado_campanha_anterior` | str | failure, nonexistent, success | Resultado da campanha de marketing anterior |
| `emp.var.rate` | `taxa_variacao_emprego` | float | −3.4 a 1.4 | Taxa de variação do emprego — indicador trimestral |
| `cons.price.idx` | `indice_preco_consumidor` | float | 92.2–94.8 | Índice de preços ao consumidor — indicador mensal |
| `cons.conf.idx` | `indice_confianca_consumidor` | float | −50.8 a −26.9 | Índice de confiança do consumidor — indicador mensal |
| `euribor3m` | `taxa_euribor_3_meses` | float | 0.635–5.045 | Taxa Euribor de 3 meses — indicador diário |
| `nr.employed` | `numero_empregados` | float | 4963.6–5228.1 | Número de funcionários — indicador trimestral (milhares) |
| `y` | `conversao` | str | no, yes | **Variável alvo.** Cliente aderiu ao depósito a prazo? |

---

## Features Derivadas

| Nome | Origem | Tipo | Regra | Descrição |
|---|---|---|---|---|
| `cliente_ja_contatado` | `dias_desde_ultimo_contato` | int | `(dias_desde_ultimo_contato != 999).astype(int)` | 1 se o cliente já foi contatado em campanha anterior; 0 se nunca |
| `faixa_contatos` | `numero_contatos_campanha` | category | bins: 1 / 2-3 / 4-5 / 6-10 / 11-20 / 20+ | Intensidade de contatos na campanha atual — facilita segmentação e análise |

---

## Decisão sobre Vazamento Temporal

A coluna `duration` (`duracao_contato`) foi removida integralmente do pipeline.

**Motivo**: a duração do contato é observada **somente depois** que o atendimento ocorre. Usá-la como feature em qualquer modelo preditivo constituiria *data leakage* — o modelo aprenderia a partir de informação que não existe no momento da decisão, inflando artificialmente métricas de conversão e tornando o sistema inaplicável em produção.

**Impacto**: nenhuma etapa do projeto (baseline, Thompson Sampling, avaliação offline, API) utiliza essa coluna.

---

## Qualidade da Base

| Aspecto | Resultado |
|---|---|
| Registros | 41.188 |
| Colunas originais | 21 (20 após remoção de `duration`) |
| Valores nulos | 0% em todas as colunas |
| Valores `unknown` | Presentes em `profissao`, `escolaridade`, `inadimplencia`, `emprestimo_habitacional`, `emprestimo_pessoal`, `estado_civil` — tratados como categoria válida |
| Taxa de conversão (alvo) | ~11,3% (desbalanceamento esperado em marketing bancário) |
| Período coberto | 2008–2010 |

> Valores `unknown` não foram imputados — mantê-los como categoria explícita preserva a informação de que o dado não estava disponível no momento do contato.
