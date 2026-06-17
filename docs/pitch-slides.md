---
marp: true
theme: default
paginate: true
footer: "OfferExp · Datathon 7MLET · Grupo 77"
style: |
  :root {
    --color-azure: #0078d4;
    --color-dark:  #1a1a2e;
    --color-light: #f4f7fb;
  }
  section {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 22px;
    background: #ffffff;
    color: #1a1a2e;
    padding: 40px 60px;
  }
  section.cover {
    background: linear-gradient(135deg, #0078d4 0%, #005a9e 100%);
    color: #ffffff;
    justify-content: center;
    text-align: center;
  }
  section.cover h1 { color: #ffffff; font-size: 2.4em; border: none; margin-bottom: 0.2em; }
  section.cover h2 { color: #cce4f7; font-size: 1.1em; font-weight: 400; border: none; }
  section.cover p  { color: #e8f4fd; font-size: 0.9em; }
  section.section-break {
    background: var(--color-azure);
    color: #ffffff;
    justify-content: center;
    text-align: center;
  }
  section.section-break h2 { color: #ffffff; border: none; font-size: 2em; }
  section.section-break p  { color: #cce4f7; font-size: 1.1em; }
  h1 { color: var(--color-azure); font-size: 1.6em; border-bottom: 3px solid var(--color-azure); padding-bottom: 8px; }
  h2 { color: var(--color-azure); font-size: 1.4em; }
  table { font-size: 0.85em; width: 100%; border-collapse: collapse; }
  th { background: var(--color-azure); color: white; padding: 8px 12px; }
  td { padding: 6px 12px; border-bottom: 1px solid #e0e0e0; }
  tr:nth-child(even) { background: #f4f7fb; }
  .highlight { color: var(--color-azure); font-weight: bold; font-size: 1.1em; }
  .badge { background: var(--color-azure); color: white; border-radius: 4px; padding: 2px 8px; font-size: 0.8em; }
  code { background: #f0f4f8; padding: 2px 6px; border-radius: 3px; font-size: 0.85em; }
  footer { color: #888; font-size: 0.7em; }
---

<!-- _class: cover -->
<!-- _paginate: false -->
<!-- _footer: "" -->

# OfferExp
## Plataforma de Experimentação Adaptativa para Ofertas Financeiras

**Multi-Armed Bandits · Thompson Sampling · Azure**

---

Grupo 77 · Geremias Francisco · Wagner Ulisses Fontalva
Pós-Tech FIAP 7MLET · Junho 2026

---

# O Problema

Instituições financeiras precisam decidir, **em tempo real e em escala**,
qual oferta apresentar a cada cliente nos canais digitais.

<br>

| Abordagem | Limitação |
|-----------|-----------|
| **Regras fixas** | Não se adapta à mudança de comportamento |
| **Testes A/B** | Desperdiça tráfego em braços sabidamente ruins |
| **ML supervisionado** | Requer retraining offline periódico; não aprende em tempo real |

<br>

> **Custo real**: em um A/B test de 90 dias com 4 variantes, 75% do tráfego é
> alocado a braços sub-ótimos durante toda a duração do experimento.

---

# Nossa Solução: OfferExp

**Uma plataforma de experimentação adaptativa** que aprende continuamente
qual oferta maximiza conversão — sem regras fixas, sem testes A/B tradicionais.

<br>

```
Cliente → POST /decide → Thompson Sampling → Oferta apresentada
                                  ↓
              (dias depois) POST /reward → Modelo atualizado
```

<br>

**4 braços de oferta:**
- `sem_oferta` — grupo controle
- `educacao_financeira` — conteúdo educativo
- `simulador_credito` — ferramenta interativa
- `cartao_premium` — produto financeiro

---

# Thompson Sampling: Como Funciona

Cada braço tem uma distribuição de probabilidade de conversão — **Beta(α, β)** — que é atualizada a cada observação.

<br>

**Regra de decisão**: sorteia um valor de cada distribuição → escolhe o maior.

- Braços com **alta incerteza** (poucos dados) têm distribuições largas → alta chance de serem escolhidos para exploração
- Braços com **muitos dados** e boa taxa → distribuições estreitas em torno do valor real → explotação natural

<br>

![w:700](../reports/thompson_posteriors.png)

---

<!-- _class: section-break -->

## Demonstração ao Vivo
**API rodando localmente · 3 chamadas · 60 segundos**

---

# Demonstração

**1. Iniciar API**
```bash
make serve          # FastAPI em localhost:8000
```

**2. Solicitar decisão**
```bash
curl -s -X POST localhost:8000/decide \
  -H "Content-Type: application/json" \
  -d '{"event_id": "demo-01", "context": {"profissao": "admin"}}'
```
```json
{ "arm_name": "cartao_premium", "reason_codes": ["thompson_sample_arm_3"],
  "policy_version": "thompson-v1" }
```

**3. Registrar reward**
```bash
curl -s -X POST localhost:8000/reward \
  -d '{"event_id": "demo-01", "arm_id": 3, "reward": 1}'
```

**4. Verificar atualização**
```bash
curl -s localhost:8000/stats | python3 -m json.tool
```

---

# Evidências Quantitativas

**Método**: Replayer Offline (Li et al., 2011) — estimativa imparcial
usando apenas eventos com braço matching.

<br>

| Política | Reward médio | Regret (5k rounds) | % melhor braço |
|----------|-------------|-------------------|----------------|
| Random (baseline) | ~11,0% | Alto — linear | ~25% |
| Greedy | ~11,2% | Médio | ~60% |
| **Thompson Sampling** | **~11,8%** | **Sublinear** | **~70%** |

<br>

**Estabilidade**: 5 sementes aleatórias (0, 7, 42, 123, 999) → CV < 2%
(registrado no MLflow — Notebook 06)

---

# Regret Acumulado

![w:860](../reports/offline_eval_regret.png)

> Thompson Sampling cresce sublinearmente — a lacuna em relação ao oráculo diminui com o tempo.

---

# Arquitetura Azure

<br>

| Camada | Serviço | Decisão |
|--------|---------|---------|
| API / Gateway | API Management | Rate limiting, OAuth2 |
| Compute | Container Apps | Zero-downtime, autoscale |
| Estado bandit | Cosmos DB | Latência < 10ms para α, β |
| Logs auditáveis | Blob Storage (WORM) | Imutável, 5 anos |
| Delayed rewards | Service Bus | Exactly-once delivery |
| MLOps | Azure ML + MLflow | Tracking, model registry |
| IA / Explicabilidade | Azure OpenAI GPT-4o | Assistente em PT |
| Segredos | Key Vault + Managed Identity | Zero credenciais hardcoded |

**Custo estimado (dev/staging): ~US$ 76/mês**

---

# Riscos e Governança

**4 cenários de risco documentados e mitigados:**

| Risco | Mitigação |
|-------|-----------|
| **Reward hacking** | Validação [0,1] + alerta >50% reward=1 em 1h |
| **Manipulação de contexto** | Pydantic whitelist + validação de ranges |
| **Abuso do assistente LLM** | System prompt restritivo + logs auditáveis |
| **Violação de suitability** | Guardrails: idade < 18 → `sem_oferta`; inadimplência → sem `cartao_premium` |

<br>

**Conformidade LGPD:**
- `subject_key` = hash SHA-256 — nenhum dado direto identificável
- Dados sensíveis (art. 5, II): **não coletados**
- Retenção: logs 5 anos · API logs 90 dias · Notificação ANPD ≤ 72h

---

# Impacto e Próximos Passos

**O que entregamos:**

✅ Plataforma end-to-end: dados → API → MLOps → Azure → Governança
✅ 112 testes automatizados (`make test`) com evidências por etapa
✅ Thompson Sampling convergindo 7% acima do Random, regret sublinear
✅ Model card · System card · LGPD · Arquitetura-alvo documentados

<br>

**O que vem a seguir:**

1. **Thompson Contextual (LinThompson)** — incorporar features do cliente na seleção
2. **Fairness constraints** — taxa mínima de exposição por segmento demográfico
3. **Feedback loop completo** — retreino automático com dados reais via Azure ML Pipeline
4. **Dashboard em tempo real** — distribuições Beta por braço em Power BI / Grafana

---

<!-- _class: cover -->
<!-- _paginate: false -->
<!-- _footer: "" -->

# Obrigado

**Geremias Francisco** · geremias_cte@hotmail.com
**Wagner Ulisses** · wagner.ulisses@gmail.com

<br>

`make test` → 112 testes passando
`make serve` → API rodando em localhost:8000
`docs/` → toda a documentação versionada no repositório

<br>

*Perguntas?*
