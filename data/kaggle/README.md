# Bank Marketing Dataset

## Fonte

Dataset público obtido no Kaggle.

Objetivo original: prever a adesão de clientes a campanhas de marketing bancário.

---

## Variável Alvo

**conversao**

Indica se o cliente aderiu ou não à campanha realizada.

---

## Tratamentos Realizados

### Remoção de Variável

* `duracao_contato`

Motivo:

A variável representa uma informação disponível apenas após a interação com o cliente, caracterizando vazamento temporal (data leakage).

---

### Features Derivadas

#### cliente_ja_contatado

Criada a partir da variável:

* `dias_desde_ultimo_contato`

Regra:

```python
(dias_desde_ultimo_contato != 999).astype(int)
```

Significado:

* 0 = cliente nunca contatado
* 1 = cliente já contatado anteriormente

---

#### faixa_contatos

Criada a partir da variável:

* `numero_contatos_campanha`

Objetivo:

Agrupar a intensidade de contatos realizados durante a campanha para facilitar interpretação e análise.

Faixas utilizadas:

* 1
* 2-3
* 4-5
* 6-10
* 11-20
* 20+


---

## Principais Achados da EDA

### Conversão

* Taxa geral de conversão: 11.3%



### Tipo de Contato

* Foram observadas diferenças relevantes de conversão entre os canais disponíveis.

### Intensidade de Contato

* A quantidade de contatos realizados durante a campanha influencia a taxa de conversão.

### Segmentação

* Foram identificadas diferenças de conversão entre perfis de profissão, escolaridade e estado civil.

---

## Aplicação no Projeto

As seguintes variáveis serão utilizadas como contexto para a política adaptativa:

* idade
* profissao
* estado_civil
* escolaridade
* tipo_contato
* cliente_ja_contatado
* resultado_campanha_anterior
* faixa_contatos
* variáveis econômicas

O dataset será utilizado como referência factual para construção da camada sintética de experimentação adaptativa.
