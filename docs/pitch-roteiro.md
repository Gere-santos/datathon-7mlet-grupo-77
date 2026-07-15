# Roteiro do Pitch — OfferExp
## Datathon 7MLET · Grupo 77 · 5 minutos (vídeo gravado)

---

> **Como usar este roteiro:**
> Cada bloco tem o texto sugerido para falar (em itálico) e o tempo acumulado.
> Pratique até o texto fluir naturalmente — não leia palavra por palavra da tela.
> Cronometrado para 4 min 45 seg de fala, deixando 15 seg de margem.
> Foco do POSTECH: problema de negócio → modelo usado → demonstração ao vivo.

---

## Bloco 1 — Abertura e Problema (0:00 – 1:00)

*"Somos o Grupo 77 — Geremias e Wagner — e apresentamos o OfferExp.*

*O problema: uma instituição financeira digital precisa decidir, a cada visita, qual oferta mostrar para cada cliente — crédito, cartão, educação financeira ou nenhuma.*

*Regras fixas não se adaptam. Testes A/B desperdiçam tráfego: você já sabe quem ganha no dia 10, mas é obrigado a continuar enviando clientes para os braços perdedores por semanas.*

*Existe uma terceira via: aprender em tempo real, sem travar a decisão em regras estáticas."*

---

## Bloco 2 — Solução e Modelo (1:00 – 2:00)

*"Implementamos Thompson Sampling — um algoritmo bayesiano de Multi-Armed Bandit.*

*Cada oferta tem uma distribuição de probabilidade representando nossa incerteza sobre sua taxa de conversão. A cada decisão, o algoritmo sorteia um valor de cada distribuição e escolhe a maior — braços incertos são explorados, braços bons são explotados. Automaticamente, sem hiperparâmetro para calibrar.*

*Comparamos com dois baselines: Random e Greedy. Thompson Sampling obteve reward médio 7% acima do Random com regret sublinear — a vantagem cresce com o tempo.*

*Usamos o Bank Marketing Dataset do Kaggle como base factual, com camada sintética de eventos de oferta, recompensas e delayed rewards por cima."*

---

## Bloco 3 — Demonstração ao Vivo (2:00 – 4:15)

> **Antes de gravar:** `make api` rodando em terminal separado. Confirme com `curl localhost:8000/health`.

*"Vamos ver a API funcionando. Não é mockup — é o servidor FastAPI real."*

**[Mostre o terminal e execute os comandos enquanto fala:]**

```bash
# 1. Solicitar uma decisão
curl -s -X POST http://localhost:8000/decide \
  -H "Content-Type: application/json" \
  -d '{"event_id": "demo-001", "subject_key": "cliente-A",
       "context": {"idade": 35, "profissao": "admin"}}'
```

*"Passamos o contexto do cliente. A API responde em milissegundos com a oferta recomendada, o reason code do algoritmo e a versão da política — toda decisão é auditável."*

```bash
# 2. Registrar conversão
curl -s -X POST http://localhost:8000/reward \
  -H "Content-Type: application/json" \
  -d '{"event_id": "demo-001", "arm_id": 2, "reward": 1.0}'
```

*"Dias depois, o cliente converteu. Registramos a recompensa — o modelo atualiza sua distribuição Beta para esse braço."*

```bash
# 3. Ver estado atual do modelo
curl -s http://localhost:8000/stats
```

*"Aqui estão os parâmetros Alpha e Beta de cada braço, atualizados em tempo real. O braço que acabou de receber reward subiu. Em produção Azure, esse estado fica no Cosmos DB — persiste entre deploys e entre instâncias."*

```bash
# 4. Consultar o assistente LLM
curl -s -X POST http://localhost:8000/assistant/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Qual braço está performando melhor?",
       "include_log_summary": true}'
```

*"O assistente LLM consegue resumir os experimentos e explicar as decisões em linguagem natural — isso é o que separa um sistema auditável de uma caixa-preta."*

---

## Bloco 4 — Encerramento (4:15 – 4:45)

*"Para resumir: entregamos uma plataforma end-to-end com pipeline reproduzível, Thompson Sampling superando o baseline, API com logs auditáveis, MLflow para rastreamento de experimentos e arquitetura documentada no Azure.*

*Todo o código está versionado e qualquer pessoa consegue executar com `make demo`.*

*Obrigado."*

---

## Checklist de Preparação para Gravação

### Antes de gravar
- [ ] `make api` rodando e testado (`curl localhost:8000/health` retorna `ok`)
- [ ] `make test` passando
- [ ] Comandos `curl` pré-digitados em arquivo de texto para copiar/colar durante gravação
- [ ] Tela dividida: slides/câmera de um lado, terminal do outro
- [ ] Cronômetro configurado para 5 minutos
- [ ] Estado do modelo limpo (reiniciar a API para Alpha=1, Beta=1 em todos os braços)

### Plano B se a demo travar
- Mostrar o arquivo `logs/decision_log.jsonl` com decisões já registradas
- Mostrar o `reports/golden_set_results.json` como evidência de execução anterior

### Divisão de fala sugerida
| Bloco | Responsável sugerido |
|-------|---------------------|
| 1 — Problema | Qualquer um |
| 2 — Modelo | Quem tiver mais conforto com o algoritmo |
| 3 — Demo | Quem fizer a digitação ao vivo |
| 4 — Encerramento | Qualquer um |

---

## Preparação para Q&A (se houver sessão presencial)

### "Por que Thompson Sampling e não UCB ou ε-greedy?"

*"Thompson balancea exploração e explotação automaticamente através da incerteza posterior, sem hiperparâmetro adicional. ε-greedy desperdiça tráfego mesmo quando já convergiu. Implementamos Nilos-UCB como referência no Notebook 07 — os resultados são comparáveis, mas Thompson teve melhor trade-off reward vs complexidade operacional."*

### "O modelo é contextual? Considera o perfil do cliente?"

*"A versão atual é não-contextual — trata todos os clientes identicamente. Foi uma decisão deliberada de MVP para validar o mecanismo de bandit antes de adicionar contexto. O endpoint /decide já recebe o contexto do cliente, mas a v1 o ignora na seleção do braço. A extensão natural é LinThompson."*

### "Como vocês garantem que a avaliação offline é válida?"

*"Usamos o Replayer Method (Li et al., 2011): contamos reward apenas quando a política teria escolhido o mesmo braço do evento histórico. Nosso dataset sintético atende a hipótese de logging uniforme por construção."*

### "Vocês têm dados reais ou tudo é sintético?"

*"O Bank Marketing Dataset do Kaggle é público e real — preserva a distribuição demográfica real. As taxas de conversão por braço e os eventos de oferta são sintéticos. Decisão consciente: usar dados financeiros reais sem anonimização e base legal LGPD seria inadequado para um projeto acadêmico."*
