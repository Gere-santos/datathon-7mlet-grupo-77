# System Card — OfferExp: Plataforma de Experimentação Adaptativa

**Projeto**: Datathon 7MLET  
**Grupo**: 77 — Geremias Francisco / Wagner Ulisses  
**Versão**: 1.0.0  
**Data**: Junho 2025

---

## Descrição do Sistema

**OfferExp** é uma plataforma acadêmica de experimentação adaptativa para seleção de ofertas financeiras personalizadas em canais digitais.

O sistema combina:
- Algoritmo de Multi-Armed Bandit (Thompson Sampling) para seleção de ofertas.
- API de decisão em tempo real (FastAPI).
- Logs auditáveis de decisões.
- Assistente de explicabilidade via LLM (planejado).

---

## Componentes

| Componente | Tecnologia | Função |
|------------|-----------|--------|
| Decision API | FastAPI / Python | Expõe endpoints `/decide`, `/reward`, `/stats` |
| Política adaptativa | Thompson Sampling | Seleciona braço por amostragem Beta |
| Decision Log | JSONL | Auditoria e rastreabilidade |
| Notebooks | Jupyter | EDA, Baseline, Thompson Sampling, Avaliação |
| MLOps | MLflow | Tracking de experimentos e métricas |
| Cloud | Microsoft Azure | Hospedagem e infraestrutura |

---

## Fluxo de Decisão

```
Cliente → POST /decide
           ↓
    Thompson Sampling seleciona braço
           ↓
    Decisão registrada em decision_log.jsonl
           ↓
    Resposta: arm_id, arm_name, reason_codes
           ↓
    (após interação) POST /reward
           ↓
    Modelo atualizado (Beta posterior)
```

---

## Propósito e Contexto

O sistema foi desenvolvido **exclusivamente para fins acadêmicos** no Datathon 7MLET da Pós-Tech FIAP. Utiliza dados sintéticos derivados de base pública do Kaggle.

**Não deve ser utilizado para**:
- Decisões financeiras reais.
- Avaliação de crédito ou inadimplência.
- Processamento de dados pessoais reais.

---

## Riscos e Mitigações

| Risco | Severidade | Mitigação |
|-------|-----------|-----------|
| Exploração excessiva de braços ruins | Média | Thompson Sampling equilibra automaticamente exploração/explotação |
| Drift de comportamento dos clientes | Alta | Monitoramento contínuo de reward médio; resets periódicos de prior |
| Viés nos dados sintéticos | Baixa | Dados gerados com distribuição uniforme entre braços |
| Uso não autorizado em produção | Alta | Aviso explícito: sistema acadêmico, sem dados reais |
| Falta de explicabilidade | Média | reason_codes em cada decisão; assistente LLM para explicações em linguagem natural |

---

## Cenários de Risco Detalhados

### Reward Hacking
**Descrição**: Um agente externo ou bug no sistema envia rewards artificialmente altos para inflar a taxa de um braço específico, distorcendo as distribuições Beta do Thompson Sampling.  
**Impacto**: O braço inflado passa a ser selecionado quase exclusivamente, causando exploração zero e resultados enviesados.  
**Mitigação**:
- Validação de range: rewards aceitos apenas no intervalo [0.0, 1.0].
- Monitoramento de anomalia: alerta se um braço receber reward=1 em >50% das respostas em uma janela de 1h.
- Human-in-the-loop: analista revisa distribuições posteriores semanalmente.

### Manipulação do Contexto
**Descrição**: Requisições com contexto forjado (campos falsos, valores extremos) para forçar seleção de um braço específico.  
**Impacto**: Decisões incorretas para clientes reais; logs poluídos.  
**Mitigação**:
- API ignora campos desconhecidos (Pydantic com `extra='ignore'`).
- Valores numéricos são validados em ranges históricos do dataset.
- Campos críticos têm whitelist de valores aceitos.

### Abuso do Assistente LLM
**Descrição**: Usuário tenta usar o assistente para extrair informações sobre clientes reais, contornar políticas ou gerar conteúdo inadequado.  
**Impacto**: Violação de privacidade, desvio de propósito, risco reputacional.  
**Mitigação**:
- Assistente responde apenas sobre experimentos, métricas e políticas sintéticas.
- Prompt system proíbe explicitamente mencionar dados de clientes reais.
- Respostas limitadas a contexto do repositório (RAG sobre docs do projeto).
- Logs de interações do assistente auditáveis.

### Violação de Suitability
**Descrição**: Sistema apresenta produto financeiro inadequado para perfil do cliente (ex.: crédito para menor de idade, produto de risco para cliente em default).  
**Impacto**: Risco regulatório, dano ao cliente, responsabilidade legal.  
**Mitigação**:
- Guardrail de idade: clientes < 18 anos recebem automaticamente `sem_oferta` (arm_id=0).
- Guardrail de inadimplência: clientes com `inadimplencia=yes` não recebem `cartao_premium`.
- Guardrail de fadiga: clientes com `faixa_contatos=20+` recebem automaticamente `sem_oferta`.
- Todos os guardrails são logados com `reason_code` específico para auditoria.

---

## Observabilidade

### Métricas Técnicas (API)
- Latência de resposta (P50, P95, P99)
- Throughput (req/s)
- Taxa de erro (4xx, 5xx)
- Disponibilidade (uptime %)

### Métricas de Negócio
- Reward médio por rodada
- Taxa de conversão por braço
- Regret acumulado
- Taxa de exploração (% seleções fora do braço líder)
- Distribuição de seleções entre segmentos (fairness)

---

## Governança e Controles

- **Human-in-the-loop**: revisão periódica dos parâmetros Alpha/Beta por analistas.
- **Guardrails**: nenhum braço pode ter taxa de seleção < 5% (mínimo de exploração garantida).
- **Auditoria**: todos os eventos registrados em JSONL imutável.
- **Versionamento**: cada política tem `policy_version` rastreável.
- **LGPD**: ver `docs/lgpd-plan.md`.

---

## Arquitetura Azure

Ver `docs/architecture-azure.md` para detalhes de infraestrutura em nuvem.

---

## Contato e Responsabilidade

**Grupo 77 — Pós-Tech FIAP 7MLET**  
Geremias Francisco: geremias_cte@hotmail.com  
Wagner Ulisses: wagner.ulisses@gmail.com
