# Roteiro do Pitch — OfferExp
## Datathon 7MLET · Grupo 77 · 10 minutos + 5 minutos de perguntas

---

> **Como usar este roteiro:**
> Cada slide tem o texto sugerido para falar (em itálico), dicas de transição e tempo acumulado.
> Pratique até o texto fluir naturalmente — não leia palavra por palavra da tela.
> Cronometrado para 9 min 30 seg de fala, deixando 30 seg de margem.

---

## Slide 1 — Capa (0:00 – 0:30)

*"Bom dia / Boa tarde. Somos o Grupo 77 — Geremias e Wagner — e vamos apresentar o OfferExp: uma plataforma de experimentação adaptativa para ofertas financeiras usando Multi-Armed Bandits e infraestrutura Azure.*

*Em 10 minutos vocês vão ver o problema que atacamos, como funciona o algoritmo, uma demonstração ao vivo, as evidências quantitativas, e como tratamos riscos e governança."*

**Dica:** Falem com calma, pausem após "Multi-Armed Bandits" — é um conceito que a banca pode não conhecer bem, e a pausa prepara a explicação que vem no slide 3.

---

## Slide 2 — O Problema (0:30 – 1:30)

*"O problema é clássico em fintechs e bancos digitais: a cada visita de um cliente, o sistema precisa decidir qual oferta apresentar — crédito, cartão, conteúdo educativo ou nada.*

*A abordagem mais comum ainda hoje é o teste A/B. O problema: durante os 90 dias de um teste com 4 variantes, 75% do tráfego vai para braços sub-ótimos. Você já sabe quem está ganhando no dia 10, mas precisa continuar mandando tráfego para os perdedores até o fim do experimento para ter significância estatística.*

*Regras fixas são ainda piores — não se adaptam à mudança de comportamento dos clientes.*

*Existe uma terceira via."*

**Transição:** *"E é exatamente essa terceira via que nós implementamos."*

---

## Slide 3 — Nossa Solução: OfferExp (1:30 – 2:30)

*"O OfferExp é uma API de decisão em tempo real baseada em Multi-Armed Bandits. A ideia central é simples: o sistema decide qual oferta apresentar, observa o resultado, e atualiza sua estimativa — continuamente, sem interrupções para análise.*

*Temos quatro braços: sem oferta como controle, educação financeira, simulador de crédito e cartão premium. O cliente chega, a API decide em milissegundos qual oferta mostrar, dias depois a conversão chega de volta, e o modelo aprende.*

*Esse ciclo acontece 24 horas por dia, 7 dias por semana, sem um cientista de dados precisar interferir manualmente.*"

**Transição:** *"A pergunta natural é: como o algoritmo toma essa decisão?"*

---

## Slide 4 — Thompson Sampling (2:30 – 4:00)

*"Usamos Thompson Sampling — um algoritmo bayesiano com mais de 90 anos de história, mas que ganhou força no setor de tecnologia na última década.*

*A ideia é que cada braço tem uma distribuição Beta — que você pode enxergar como 'nossa incerteza sobre a taxa de conversão desse braço'. No início, todas as distribuições são largas e iguais — sabemos pouco. À medida que observamos conversões, as distribuições vão se estreitando e se deslocando para o valor real.*

*Na hora de tomar uma decisão, o algoritmo sorteia um número de cada distribuição e escolhe o maior. Braços com alta incerteza têm distribuições largas — maior chance de ser escolhido para exploração. Braços com boa taxa conhecida têm distribuições estreitas no valor alto — são escolhidos por explotação.*

*Esse balanceamento acontece automaticamente, sem parâmetro de exploração para calibrar.*"

*[Aponte para o gráfico do slide]* 
*"Aqui vocês veem as distribuições depois de alguns milhares de rodadas. O braço 3 — cartão premium — tem a distribuição mais deslocada para a direita, indicando que o modelo aprendeu que ele converte melhor."*

**Transição:** *"Vamos ver isso funcionando ao vivo."*

---

## Slide 5 — Demonstração (4:00 – 6:00)

> **Antes da apresentação:** Garantir que `make serve` está rodando em outro terminal.

*"Aqui está a API rodando localmente. Não é um mockup — é o servidor FastAPI real."*

**Execute os comandos um a um enquanto fala:**

*"Primeiro, pedimos uma decisão. Passamos um event_id e o contexto do cliente — profissão: admin."*
[Execute o curl /decide]

*"A API respondeu: cartão premium, com o reason code 'thompson_sample_arm_3'. E veja — a versão da política está registrada. Toda decisão é auditável."*

*"Agora vamos registrar que esse cliente converteu — reward 1."*
[Execute o curl /reward]

*"E consultamos o estado atual do modelo."*
[Execute o curl /stats]

*"Vocês podem ver os parâmetros Alpha e Beta por braço, atualizados em tempo real. Esse estado vai para o Cosmos DB em produção — persiste entre deploys, entre instâncias, entre reinicializações."*

**Transição:** *"Demonstração de mecanismo. Mas o que os números dizem?"*

---

## Slide 6 — Evidências Quantitativas (6:00 – 7:30)

*"Para avaliar a política offline — sem precisar de um A/B test real — usamos o Replayer Method, publicado por Li et al. em 2011. A ideia é simples: para cada evento histórico, se a política teria escolhido o mesmo braço que o evento registrado, contamos aquele reward. Caso contrário, pulamos. Isso garante uma estimativa imparcial sem viés de seleção.*

*Rodamos isso para três políticas: Random como baseline puro, Greedy como baseline determinístico, e Thompson Sampling.*

*Thompson teve reward médio 7% acima do Random e regret sublinear — a lacuna em relação ao oráculo diminui com o tempo. O Greedy foi interessante: converge rápido no início, mas trava em um braço sub-ótimo quando encontra um resultado bom cedo. Isso é exatamente por que não usamos Greedy como política principal.*

*E o resultado é robusto: rodamos com 5 sementes aleatórias diferentes e o coeficiente de variação foi menor que 2% — o Thompson Sampling não está com sorte, está convergindo de forma consistente."*

---

## Slide 7 — Regret Acumulado (7:30 – 8:00)

*"Esse gráfico ilustra o ponto central: o Random acumula regret linearmente — toda rodada adicional adiciona a mesma lacuna em relação ao oráculo. Thompson acumula sublinearmente — a curva vai achatando. Em produção com milhões de decisões, essa diferença é significativa."*

**Transição rápida:** *"Falando em produção — como isso ficaria na Azure?"*

---

## Slide 8 — Arquitetura Azure (8:00 – 8:45)

*"A arquitetura usa exclusivamente Azure — sem dependência de outro provedor de nuvem.*

*Container Apps roda a API FastAPI com autoscale zero-downtime. O estado do bandit — os parâmetros Alpha e Beta — fica no Cosmos DB por latência abaixo de 10 milissegundos. Rewards atrasados trafegam pelo Service Bus com entrega exactly-once — essencial porque uma conversão 14 dias depois do contato não pode ser perdida.*

*Toda credencial está no Key Vault acessado via Managed Identity — zero credenciais hardcoded. E o assistente de explicabilidade usa Azure OpenAI, o que mantém os dados dentro do boundary Azure — necessário para LGPD.*

*Custo estimado para um ambiente de dev e staging: 76 dólares por mês."*

---

## Slide 9 — Riscos e Governança (8:45 – 9:30)

*"Documentamos e mitigamos quatro cenários de risco.*

*Reward hacking: alguém poderia inflar artificialmente a taxa de um braço enviando rewards falsos. Mitigamos com validação de range e alerta automático se um braço receber reward igual a 1 em mais de 50% das respostas numa janela de uma hora.*

*Violação de suitability: o sistema não pode oferecer cartão de crédito para um menor de 18 anos. Temos guardrails que desviam automaticamente para sem_oferta, e cada desvio é logado com reason code específico para auditoria.*

*Do lado da LGPD: o identificador do cliente é sempre um hash SHA-256 — o valor real nunca é persistido. Nenhum dado sensível do art. 5 da LGPD — raça, religião, saúde — é sequer coletado. Incidentes devem ser notificados à ANPD em até 72 horas.*"

---

## Slide 10 — Impacto e Próximos Passos (9:30 – 10:00)

*"Para resumir o que entregamos: uma plataforma end-to-end, da ingestão de dados até a arquitetura de produção Azure, com 112 testes automatizados rodando em make test — incluindo testes que verificam os documentos de governança, não apenas o código.*

*O que vem a seguir: Thompson Contextual para incorporar as features do cliente na decisão, fairness constraints para garantir exposição mínima por segmento demográfico, e retreino automático com dados reais via Azure ML Pipeline.*

*Todo o código, documentação e evidências estão versionados no repositório. Obrigado."*

---

## Slide 11 — Q&A

*Deixem o slide de obrigado na tela. Anotem as perguntas antes de responder.*

---

## Preparação para Q&A — Perguntas Prováveis

### "Por que Thompson Sampling e não UCB ou ε-greedy?"

*"Thompson Sampling tem convergência empírica superior em cenários com poucas amostras por braço, que é exatamente o nosso caso com 4 braços. UCB exige calibração do bound — um hiperparâmetro a mais para tunar. ε-greedy é determinístico na exploração e desperdiça tráfego mesmo quando já convergiu. Thompson balancea automaticamente através da incerteza posterior, sem hiperparâmetro adicional. Implementamos Nilos-UCB como referência no Notebook 07 — os resultados são comparáveis, mas Thompson teve melhor trade-off reward vs complexidade operacional."*

### "O modelo é contextual? Considera o perfil do cliente?"

*"A versão atual — thompson-v1 — é não-contextual: trata todos os clientes identicamente. Essa foi uma decisão deliberada de MVP para validar o mecanismo de bandit antes de adicionar contexto. A extensão natural é LinThompson, que incorpora o vetor de features do cliente na estimativa de reward esperado. Já documentamos isso como primeiro trabalho futuro, e a infraestrutura de contexto já está implementada — o endpoint /decide recebe o contexto do cliente, mas a versão 1 o ignora na seleção do braço."*

### "Como vocês garantem que o Replayer é uma avaliação válida?"

*"Li et al., 2011 demonstrou que o Replayer fornece estimativa imparcial desde que os dados de treinamento tenham sido coletados com uma política de logging uniforme — ou seja, cada braço foi apresentado com probabilidade igual. Nosso dataset sintético atende essa hipótese por construção: ao gerar os eventos, amostramos o braço uniformemente entre os 4. Em dados reais de produção, isso exigiria uma fase inicial de exploração uniforme antes de ativar o bandit."*

### "E se dois braços tiverem taxas iguais? O sistema trava?"

*"Não. Thompson Sampling com prior Beta(1,1) nunca trava em empate — ele amostra de cada distribuição independentemente, então há sempre uma resolução estocástica do empate. Isso é demonstrado no teste de cold-start: com zero observações e todos os braços com Alpha=1 e Beta=1, o modelo ainda assim seleciona todos os braços ao longo de 40 rodadas."*

### "Qual é o custo computacional de selecionar um braço?"

*"Constante em relação ao número de rodadas: para cada decisão, o algoritmo faz 4 sorteios de distribuição Beta e retorna o argmax. Isso é O(K) onde K é o número de braços — independente do histórico. O histórico está resumido nos parâmetros Alpha e Beta, não em séries temporais completas. Na prática, a latência da chamada ao Cosmos DB para buscar esses parâmetros vai dominar sobre o cálculo do Thompson Sampling."*

### "O sistema escala horizontalmente? Como múltiplas instâncias sincronizam o estado?"

*"Na versão local, o estado fica em memória — funciona apenas com uma instância. Na arquitetura Azure, o estado fica no Cosmos DB com consistência de sessão: múltiplas instâncias do Container App leem e escrevem os parâmetros Alpha e Beta no banco. Há uma race condition teórica em updates concorrentes, mas o impacto em um bandit é baixo — uma atualização perdida num contexto de milhares de rodadas não altera materialmente a política. Para produção crítica, implementaríamos transações otimistas com ETag no Cosmos DB."*

### "Vocês têm dados reais ou tudo é sintético?"

*"Tudo é sintético neste MVP. Usamos o Bank Marketing Dataset do Kaggle como base de perfis de clientes reais — preservando a distribuição demográfica real — mas as taxas de conversão por braço e os eventos de oferta são sintéticos. Isso foi uma decisão consciente: não temos acesso a dados financeiros reais, e usar dados reais sem anonimização e base legal LGPD seria inadequado para um projeto acadêmico. O design da plataforma, no entanto, funciona identicamente com dados reais — a única mudança seria na fonte dos eventos de entrada."*

---

## Checklist de Preparação para o Dia

### 30 minutos antes
- [ ] `make serve` rodando e testado (`curl localhost:8000/health`)
- [ ] `make test` passando (112 testes)
- [ ] Slides abertos em tela cheia
- [ ] Terminal em segundo monitor ou aba pronta para demo
- [ ] `curl` commands pré-digitados em arquivo para copiar/colar
- [ ] Cronômetro configurado para 10 minutos

### Durante
- [ ] Slide 1 → 0:00 | Slide 5 (demo) → 4:00 | Slide 10 → 9:30
- [ ] Se a demo travar: *"Vou mostrar nos slides o output esperado"* — mostrar os json blocks do slide 5
- [ ] Se o tempo apertar: pular slide 7 (regret curve) — é reforço, não novo conteúdo

### Divisão de fala sugerida
| Slides | Responsável sugerido |
|--------|---------------------|
| 1 – 3 (Problema, Solução) | Qualquer um |
| 4 (Thompson Sampling) | Quem tiver mais conforto com o algoritmo |
| 5 (Demo) | Quem fizer a demo técnica |
| 6 – 7 (Evidências) | Quem apresentou os experimentos |
| 8 – 10 (Azure, Riscos, Impacto) | Outro membro |
