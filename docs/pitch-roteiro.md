# Roteiro do Pitch — OfferExp
## Datathon 7MLET · Grupo 77 · ~7min45 (vídeo gravado)

---

> **Como usar este roteiro:**
> Cada bloco tem o texto sugerido para falar (em itálico) e o tempo acumulado.
> Pratique até o texto fluir naturalmente — não leia palavra por palavra da tela.
> Cronometrado para 7 min 30 seg de fala, deixando ~15 seg de margem por bloco.
> Foco do POSTECH: problema de negócio → dados → modelo → demonstração ao vivo → arquitetura → governança.

---

## Bloco 1 — Abertura e Problema (0:00 – 1:00)

*"Somos o Grupo 77 — Geremias e Wagner — e apresentamos o OfferExp.*

*O problema: uma instituição financeira digital precisa decidir, a cada visita, qual oferta mostrar para cada cliente — crédito, cartão, educação financeira ou nenhuma.*

*Regras fixas não se adaptam. Testes A/B desperdiçam tráfego: você já sabe quem ganha no dia 10, mas é obrigado a continuar enviando clientes para os braços perdedores por semanas.*

*Existe uma terceira via: aprender em tempo real, sem travar a decisão em regras estáticas."*

---

## Bloco 2 — Dados (1:00 – 1:45)

*"Nossa base é o Bank Marketing Dataset do Kaggle: 41 mil clientes reais de um banco português, sem valores nulos.*

*Uma decisão importante de modelagem: removemos a coluna `duration` — a duração da ligação. Ela só é conhecida depois que o contato já aconteceu. Usá-la como feature seria data leakage: o modelo aprenderia com uma informação que não existe no momento real da decisão.*

*Por cima dessa base real, adicionamos uma camada sintética: eventos de oferta, recompensas e delayed rewards — necessária porque o dataset original não tem esse mecanismo de bandit."*

---

## Bloco 3 — Solução e Modelo (1:45 – 3:15)

*"Nossa solução, o OfferExp: uma API de decisão em tempo real com Multi-Armed Bandit, usando Thompson Sampling — um algoritmo bayesiano.*

*Cada oferta tem uma distribuição de probabilidade representando nossa incerteza sobre sua taxa de conversão. A cada decisão, o algoritmo sorteia um valor de cada distribuição e escolhe a maior — braços incertos são explorados, braços bons são explotados. Automaticamente, sem hiperparâmetro para calibrar.*

*Comparamos com dois baselines: Random e Greedy. Thompson Sampling obteve reward médio 7% acima do Random, com regret sublinear — a vantagem cresce com o tempo.*

*E não é só o reward: implementamos três guardrails automáticos de suitability. Cliente menor de idade nunca recebe oferta de crédito. Cliente inadimplente nunca recebe cartão premium. Cliente com fadiga de contato para de receber ofertas. Tudo logado e auditável, e monitoramos fairness entre faixas etárias e profissões para garantir que nenhum grupo seja sistematicamente prejudicado."*

---

## Bloco 4 — Demonstração ao Vivo (3:15 – 5:15)

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

---

## Bloco 5 — Arquitetura Azure (5:15 – 6:15)

*"Do ponto de vista de infraestrutura, desenhamos tudo em cima de Azure, exclusivamente. O cliente chega pela API Management, que faz autenticação OAuth2, e cai no Container Apps rodando o FastAPI.*

*O estado do bandit — os parâmetros alpha e beta de cada braço — vive no Cosmos DB, com latência baixa para leitura ponto-a-ponto. Os logs de decisão vão para o Blob Storage, imutáveis e auditáveis. Rewards atrasados passam por uma fila no Service Bus, que garante entrega exactly-once.*

*E todo experimento é rastreado no MLflow, dentro do Azure Machine Learning. Usamos só Azure — não por modismo, mas porque isso nos dá um único plano de identidade gerenciada cobrindo tudo, sem credencial nenhuma em texto claro no código. O deploy é automatizado via GitHub Actions, com rollout canary de 10%, depois 50%, depois 100%, e rollback em um comando se algo der errado."*

---

## Bloco 6 — Governança, LGPD e Próximos Passos (6:15 – 7:15)

*"Pensamos também nos riscos. Reward hacking — alguém tentando inflar artificialmente um braço — é mitigado com validação de range e alerta de anomalia. Drift de comportamento dos clientes é monitorado continuamente.*

*Sobre dados pessoais: hoje só usamos dados sintéticos e públicos. Mas desenhamos o sistema já pensando em LGPD — o identificador do cliente é sempre um hash, nunca armazenamos nome, CPF ou dado sensível, e documentamos isso no plano de conformidade.*

*Para o futuro, os próximos passos são: tornar o modelo contextual com LinUCB, usando o perfil do cliente que a API já recebe mas ainda ignora; um assistente baseado em LLM para explicar decisões em linguagem natural; e um processo formal de human-in-the-loop para aprovar novas políticas antes de irem para produção."*

---

## Bloco 7 — Encerramento (7:15 – 7:45)

*"Para resumir: entregamos uma plataforma end-to-end com pipeline reproduzível, Thompson Sampling superando o baseline com guardrails de suitability, API com logs auditáveis, arquitetura Azure documentada e um plano claro de governança e próximos passos.*

*Todo o código está versionado e qualquer pessoa consegue executar com `make demo`.*

*Obrigado."*

---

## Checklist de Preparação para Gravação

### Antes de gravar
- [ ] `make api` rodando e testado (`curl localhost:8000/health` retorna `ok`)
- [ ] `make test` passando
- [ ] Comandos `curl` pré-digitados em arquivo de texto para copiar/colar durante gravação
- [ ] Tela dividida: slides/câmera de um lado, terminal do outro
- [ ] Cronômetro configurado para 8 minutos
- [ ] Estado do modelo limpo (reiniciar a API para Alpha=1, Beta=1 em todos os braços)

### Plano B se a demo travar
- Mostrar o arquivo `logs/decision_log.jsonl` com decisões já registradas
- Mostrar o `reports/golden_set_results.json` como evidência de execução anterior

### Divisão de fala sugerida
| Bloco | Responsável sugerido |
|-------|---------------------|
| 1 — Problema | Qualquer um |
| 2 — Dados | Quem tiver mais conforto com o dataset/pipeline |
| 3 — Modelo | Quem tiver mais conforto com o algoritmo |
| 4 — Demo | Quem fizer a digitação ao vivo |
| 5 — Arquitetura | Quem tiver mais conforto com Azure |
| 6 — Governança | Qualquer um |
| 7 — Encerramento | Qualquer um |

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

### "Por que só Azure e não multi-cloud?"

*"Um único plano de identidade gerenciada (Azure AD/Managed Identity) cobre todos os serviços sem cross-cloud credential management, e mantém os dados dentro do boundary de compliance financeiro brasileiro. Multi-cloud adicionaria complexidade operacional sem benefício claro para o volume atual do MVP."*

### "Quais são os guardrails de suitability e por que eles existem?"

*"Três regras determinísticas rodam antes do Thompson Sampling: menor de 18 anos nunca recebe oferta de crédito, cliente inadimplente nunca recebe cartão premium, e cliente com fadiga de contato (20+ contatos) para de receber ofertas. Existem porque o algoritmo por si só otimiza reward, não suitability — sem esses guardrails, o bandit poderia aprender a empurrar produtos inadequados para um perfil só porque converte bem estatisticamente."*
