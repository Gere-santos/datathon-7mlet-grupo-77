# Plano de Conformidade LGPD — OfferExp

**Projeto**: Datathon 7MLET — Plataforma de Experimentação Adaptativa  
**Grupo**: 77 — Geremias Francisco / Wagner Ulisses  
**Data**: Junho 2025

---

## Escopo

Este documento descreve as medidas de conformidade com a **Lei Geral de Proteção de Dados Pessoais (LGPD — Lei nº 13.709/2018)** aplicáveis à plataforma OfferExp em um cenário de produção hipotético.

> **Nota**: A versão atual do projeto utiliza **exclusivamente dados sintéticos e públicos**. Não há processamento de dados pessoais reais. Este plano descreve as medidas necessárias para um eventual uso em produção.

---

## Dados Processados (cenário produção hipotético)

| Dado | Classificação | Base Legal |
|------|--------------|-----------|
| Identificador do cliente (anonimizado) | Pseudônimo | Legítimo interesse |
| Canal de comunicação | Operacional | Execução de contrato |
| Oferta apresentada | Operacional | Legítimo interesse |
| Resultado da interação (conversão 0/1) | Comportamental | Legítimo interesse |
| Contexto demográfico agregado | Analítico | Legítimo interesse |

**Dados NÃO processados pelo sistema**:
- Nome, CPF, endereço, renda, saldo.
- Dados sensíveis (art. 5º, II da LGPD).

---

## Princípios LGPD Aplicados

### 1. Finalidade (art. 6º, I)
Dados utilizados exclusivamente para: seleção de ofertas, otimização de campanhas, auditoria de decisões. Não há compartilhamento com terceiros.

### 2. Adequação (art. 6º, II)
Os dados coletados são os mínimos necessários para o funcionamento do algoritmo bandit (event_id, arm_id, reward).

### 3. Necessidade / Minimização (art. 6º, III)
O `subject_key` é sempre um identificador pseudoanonimizado. Nenhum dado direto de identificação (nome, CPF) é armazenado.

### 4. Livre Acesso (art. 6º, IV)
Titulares podem solicitar visualização dos logs de decisões associados ao seu identificador.

### 5. Qualidade dos Dados (art. 6º, V)
Logs são imutáveis (JSONL append-only). Correções são registradas como novos eventos, não sobrescrevem histórico.

### 6. Transparência (art. 6º, VI)
`reason_codes` em cada decisão garantem explicabilidade. Assistente LLM planejado para respostas em linguagem natural.

### 7. Segurança (art. 6º, VII)
- Logs armazenados em storage criptografado (Azure Blob Storage com CMK).
- API protegida por autenticação (Azure AD).
- Acesso ao banco de dados por managed identity.

### 8. Prevenção (art. 6º, VIII)
- Monitoramento de anomalias via Azure Monitor.
- Alertas automáticos para padrões de acesso suspeitos.

### 9. Não Discriminação (art. 6º, IX)
- Braços de oferta não são definidos por características protegidas.
- Monitoramento de fairness entre segmentos demográficos.

### 10. Responsabilização (art. 6º, X)
- DPO designado (em produção).
- Logs de auditoria retidos por 5 anos.
- Relatório de Impacto à Proteção de Dados (RIPD) antes da produção.

---

## Direitos dos Titulares

| Direito | Implementação |
|---------|--------------|
| Confirmação de existência de tratamento | Endpoint `/privacy/confirm/{subject_key}` |
| Acesso aos dados | Endpoint `/privacy/data/{subject_key}` |
| Correção de dados | Processo de suporte manual |
| Anonimização / exclusão | Script de purge no pipeline de dados |
| Portabilidade | Export CSV via endpoint administrativo |
| Revogação de consentimento | Flag de opt-out no cadastro do cliente |

---

## Retenção e Descarte

| Dado | Período de Retenção | Descarte |
|------|---------------------|---------|
| Decision Log (eventos) | 5 anos | Purge automático + certificado de destruição |
| Dados brutos de campanha | 2 anos | Anonimização após 6 meses |
| Logs de API | 90 dias | Rolling window automático |

---

## Transferência Internacional

Dados não são transferidos internacionalmente na arquitetura atual. Em caso de uso de APIs externas (Azure OpenAI), aplicam-se as garantias do DPA da Microsoft com cláusulas contratuais padrão (SCCs).

---

## Incidentes de Segurança

Em caso de incidente envolvendo dados pessoais:
1. Notificação à ANPD em até **72 horas** (art. 48 da LGPD).
2. Comunicação aos titulares afetados.
3. Registro no relatório de incidentes.

---

## Contato DPO (hipotético em produção)

privacy@offerexp.com.br
