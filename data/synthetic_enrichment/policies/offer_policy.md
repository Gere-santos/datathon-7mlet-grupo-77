# Política Comercial de Ofertas — OfferExp (Sintética)

> **DOCUMENTO SINTÉTICO** — criado para fins de demonstração e RAG.
> Não representa política real de nenhuma instituição financeira.
> Versão: poc-v1 · Vigência: Junho 2025

---

## 1. Catálogo de Ofertas

### Braço 0 — sem_oferta (Controle)
**Descrição**: Nenhuma oferta ativa é apresentada. O cliente é servido com a experiência padrão do canal.
**Elegibilidade**: Todos os clientes.
**Objetivo**: Grupo controle para medir o efeito causal das demais ofertas.
**Restrição**: Clientes em período de carência (0–7 dias após interação anterior) devem receber este braço obrigatoriamente.

### Braço 1 — educacao_financeira (Conteúdo Educativo)
**Descrição**: Conteúdo educativo sobre planejamento financeiro, reservas de emergência e crédito consciente.
**Canal preferencial**: E-mail, notificação push.
**Elegibilidade**: Todos os clientes com `escolaridade != "illiterate"`.
**Taxa base esperada**: ~11,1% de engajamento.
**KPI primário**: Taxa de leitura / abertura do conteúdo.
**Restrição**: Não aplicar para clientes que já receberam este conteúdo nos últimos 30 dias.

### Braço 2 — simulador_credito (Ferramenta Interativa)
**Descrição**: Ferramenta digital para simulação de crédito pessoal com condições personalizadas.
**Canal preferencial**: Web, app móvel.
**Elegibilidade**: Clientes com `faixa_contatos` não superior a "11-20".
**Taxa base esperada**: ~11,0% de conversão para simulação completa.
**KPI primário**: Taxa de conclusão da simulação.
**Restrição**: Clientes com `inadimplencia=yes` recebem simulação informativa, não oferta ativa.

### Braço 3 — cartao_premium (Produto Financeiro)
**Descrição**: Oferta de cartão de crédito premium com benefícios diferenciados (cashback, lounge, seguro viagem).
**Canal preferencial**: Todos.
**Elegibilidade**: Cliente deve ter `idade >= 18`, `inadimplencia != yes`, e perfil de risco aprovado.
**Taxa base esperada**: ~11,9% de conversão.
**KPI primário**: Taxa de adesão ao produto.
**Restrição**: Proibido para menores de 18 anos (guardrail regulatório) e inadimplentes ativos.

---

## 2. Regras de Priorização

Quando mais de uma oferta é elegível, o algoritmo Thompson Sampling decide. O sistema garante:
- Nenhum braço com taxa de seleção inferior a 5% (mínimo de exploração).
- Guardrails de suitability têm precedência sobre qualquer decisão do algoritmo.

---

## 3. Histórico de Versões

| Versão | Data | Descrição |
|--------|------|-----------|
| poc-v1 | Jun/2025 | Versão inicial com 4 braços sintéticos |
