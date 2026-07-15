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
  h1 { color: var(--color-azure); font-size: 1.6em; border-bottom: 3px solid var(--color-azure); padding-bottom: 8px; }
  h2 { color: var(--color-azure); font-size: 1.4em; }
  table { font-size: 0.85em; width: 100%; border-collapse: collapse; }
  th { background: var(--color-azure); color: white; padding: 8px 12px; }
  td { padding: 6px 12px; border-bottom: 1px solid #e0e0e0; }
  tr:nth-child(even) { background: #f4f7fb; }
  code { background: #f0f4f8; padding: 2px 6px; border-radius: 3px; font-size: 0.85em; }
  footer { color: #888; font-size: 0.7em; }
---

<!-- _class: cover -->
<!-- _paginate: false -->
<!-- _footer: "" -->

# OfferExp
## Plataforma de Experimentação Adaptativa para Ofertas Financeiras

**Multi-Armed Bandits · Thompson Sampling · Azure**

Grupo 77 · Geremias Francisco · Wagner Ulisses Fontalva
Pós-Tech FIAP · Datathon 7MLET

---

# Problema e Solução

**Uma instituição financeira digital** precisa decidir qual oferta apresentar a cada cliente.
Regras fixas não se adaptam. Testes A/B desperdiçam tráfego em braços sabidamente ruins.

<br>

**Nossa solução — OfferExp:** API de decisão em tempo real com Multi-Armed Bandit.

```
Cliente → POST /decide → Thompson Sampling → Oferta apresentada
                                  ↓
              (dias depois) POST /reward → Modelo atualizado automaticamente
```

**4 braços de oferta:** `sem_oferta` · `educacao_financeira` · `simulador_credito` · `cartao_premium`

> Base: Bank Marketing Dataset (Kaggle · CC0) com camada sintética de eventos, recompensas e delayed rewards.

---

# Modelo: Thompson Sampling

Cada braço tem uma distribuição **Beta(α, β)** que representa a incerteza sobre sua taxa de conversão.

**Regra de decisão**: sorteia um valor de cada distribuição → escolhe o maior.

- Alta incerteza → distribuição larga → maior chance de **exploração**
- Muitos dados e boa taxa → distribuição estreita → **explotação** natural

<br>

| Política | Reward médio | Regret | % melhor braço |
|----------|-------------|--------|----------------|
| Random (baseline) | ~11,0% | Linear | ~25% |
| Greedy | ~11,2% | Médio | ~60% |
| **Thompson Sampling** | **~11,8%** | **Sublinear** | **~70%** |

> +7% vs Random · estável em 5 sementes (CV < 2%) · rastreado no MLflow

---

# Demonstração — API ao Vivo

**`make api`** → FastAPI em `localhost:8000`

**1. Solicitar decisão**
```bash
curl -s -X POST localhost:8000/decide \
  -H "Content-Type: application/json" \
  -d '{"event_id": "demo-01", "subject_key": "cliente-42",
       "context": {"profissao": "admin", "idade": 35}}'
```
```json
{ "arm_name": "cartao_premium", "reason_codes": ["thompson_sample_arm_3"],
  "policy_version": "thompson-v1", "decided_at": "2026-07-15T..." }
```

**2. Registrar conversão** (reward atrasado)
```bash
curl -s -X POST localhost:8000/reward \
  -d '{"event_id": "demo-01", "arm_id": 3, "reward": 1}'
```

**3. Consultar estado do modelo**
```bash
curl -s localhost:8000/stats
# → Alpha/Beta atualizados por braço em tempo real
```

**4. Assistente LLM explicando a decisão**
```bash
curl -s -X POST localhost:8000/assistant/ask \
  -d '{"question": "Qual braço está performando melhor?", "include_log_summary": true}'
```

---

<!-- _class: cover -->
<!-- _paginate: false -->
<!-- _footer: "" -->

# Obrigado

**Geremias Francisco** · geremias_cte@hotmail.com
**Wagner Ulisses** · wagner.ulisses@gmail.com

<br>

`make demo` → pipeline ponta a ponta
`make test` → suíte de testes automatizados
`docs/`     → model card · system card · LGPD · arquitetura Azure

<br>

*Repositório: datathon-7mlet-grupo-77*
