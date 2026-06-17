# Regras de Suitability — OfferExp (Sintéticas)

> **DOCUMENTO SINTÉTICO** — criado para fins de demonstração e RAG.
> Versão: poc-v1 · Vigência: Junho 2025

---

## 1. Definição de Suitability

Suitability é o processo de verificar se uma oferta é adequada para o perfil do cliente antes de apresentá-la. O objetivo é proteger o cliente de produtos inadequados e a instituição de riscos regulatórios e reputacionais.

---

## 2. Regras Obrigatórias (Guardrails)

Estas regras têm **precedência absoluta** sobre qualquer decisão do algoritmo bandit.

### 2.1 Restrição de Idade
- **Regra**: Clientes com `idade < 18 anos` não podem receber `cartao_premium`, `simulador_credito` ou qualquer oferta de produto financeiro.
- **Ação automática**: Desvio obrigatório para `sem_oferta` (arm_id=0).
- **Reason code**: `guardrail_age_under_18`
- **Base legal**: Código Civil Brasileiro, art. 3º — menores de 18 anos são absolutamente incapazes para atos da vida civil.

### 2.2 Restrição por Inadimplência
- **Regra**: Clientes com `inadimplencia=yes` não podem receber `cartao_premium`.
- **Ação automática**: Desvio para `sem_oferta` se o algoritmo selecionar arm_id=3.
- **Reason code**: `guardrail_inadimplencia_cartao_premium`
- **Justificativa**: Concessão de crédito premium para inadimplente representa risco de crédito e potencial dano ao consumidor (superendividamento).

### 2.3 Restrição de Fadiga de Contato
- **Regra**: Clientes com `faixa_contatos = "20+"` (mais de 20 contatos na campanha atual) recebem automaticamente `sem_oferta`.
- **Ação automática**: Desvio obrigatório para arm_id=0.
- **Reason code**: `guardrail_contact_fatigue_20plus`
- **Base legal**: LGPD art. 6º, III (necessidade/minimização) e art. 6º, IX (não discriminação).

---

## 3. Regras Recomendadas (Soft Rules)

Estas regras são aplicadas quando possível, mas podem ser overriden por contexto de negócio.

### 3.1 Carência Pós-Interação
- Clientes que já interagiram nos últimos 7 dias preferivelmente recebem `sem_oferta`.
- Implementado como peso na função de priorização, não como bloqueio rígido.

### 3.2 Escolaridade Mínima para Conteúdo
- `educacao_financeira` não é apresentado para `escolaridade=illiterate`.
- Justificativa: acessibilidade — conteúdo textual pode não ser adequado.

---

## 4. Auditoria de Suitability

Toda aplicação de guardrail deve ser registrada no `decision_log.jsonl` com:
- `reason_codes` contendo o código do guardrail aplicado
- `arm_id` e `arm_name` refletindo o braço após desvio (não o braço original)
- `policy_version` rastreável para fins de auditoria regulatória

---

## 5. Revisão Periódica

As regras de suitability devem ser revisadas semestralmente por um analista de conformidade e aprovadas pelo responsável da política comercial antes de qualquer mudança.
