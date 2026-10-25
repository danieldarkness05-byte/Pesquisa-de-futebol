---
name: casa
description: O que a CASA acredita (pedido do Daniel em 25/10) — varre todos os jogos do dia pelas odds da bet365 (via 365Scores, com a de abertura) e entrega, em qualquer mercado que dá para conferir (vitória, dupla chance, gols, ambas marcam, handicap .5), as seleções em que a casa dá 75%+ e ficou MAIS confiante desde a abertura (odd caindo 5%+). Só script, sem agentes. Use quando o Daniel pedir os jogos em que a casa acredita, "o que a casa acha que vai acertar" ou /casa.
argument-hint: "[hoje | amanhã | AAAA-MM-DD]"
allowed-tools: Bash(python3 ferramentas/*) Bash(git *) Read Write Edit
---

Data: **$ARGUMENTS** (vazio = hoje; depois das 18:00 de Brasília, amanhã).

Pedido do Daniel (25/10): "todas que a gente tentou deu errado. Vamos focar somente nas odds que a casa vê que vai vencer,
procurar todos os jogos com calma e não usar créditos à toa: achar os mercados em que a casa acredita que vai acertar,
pelas odds ou por alguma informação".

**Só script, sem agentes e sem pesquisa de notícias.** A informação é a própria odd: a casa põe odd baixa no que acha
provável, e a odd caindo desde a abertura mostra que a casa e o dinheiro ficaram mais confiantes.

## 1. Aprender

`python3 ferramentas/previsoes.py resolver` e `python3 ferramentas/previsoes.py resumo --analise casa --curto`.
A pergunta é uma só: **a casa acerta o que promete?** Se a faixa de 75–80% acerta bem menos (com 30+ resolvidas),
suba `config.json → casa.queda_min` ou `prob_min`.

## 2. Varredura

`python3 ferramentas/casa.py --data <D> --json > <scratchpad>/casa-<D>.json` (uns 10 segundos).

Critérios em `config.json → casa`: casa ≥ 75% sem margem, odd ≥ 1.15, odd caindo 5%+ desde a abertura, outro lado
sem despencar e margem ≤ 8%. Um jogo, uma seleção (a de maior probabilidade da casa).

O book do 365Scores é um clone da bet365, então os dois contam como uma fonte só.

## 3. Entrega (curta, para celular)

**🏦 O que a casa acredita — DD/MM**

| # | Jogo | Hora | Mercado | Casa dá | Odd (abriu) |
|---|---|---|---|---|---|

- No máximo 10, na ordem do script. Nenhum passou: "A casa não ficou mais confiante em nada hoje."
- Uma linha de aviso: a casa acerta uns 3 em 4 dessas, mas a odd já desconta isso. **Não junte tudo numa múltipla**:
  6 seleções de 77% juntas dão só ~21%.
- Mostre a calibração quando houver resolvidas: "Casa até agora: X/Y (Z%) para W% prometido".

## 4. Registrar e salvar

1. `python3 ferramentas/casa.py --data <D> --registrar --max <N>` (mesma varredura; grava com `analise: "casa"`).
2. `analises/AAAA-MM-DD-casa.md`: a lista, a hora da consulta e os critérios.
3. Commit e push, com mensagem em português.
