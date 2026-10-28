---
name: favorito
description: Favorito que PRECISA vencer (pedido do Daniel em 21/10, num chat próprio) — jogos de hoje em que o favorito tem muito em jogo (mata-mata, final, briga por título/vaga/rebaixamento) e vai com todos os titulares; mercado vitória ou dupla chance; pesquisa em todas as fontes, com cético. Use quando o Daniel pedir jogos em que o favorito precisa ganhar.
argument-hint: "[hoje | amanhã | AAAA-MM-DD]"
allowed-tools: Bash(python3 ferramentas/*) Bash(git *) Workflow Read Write Edit
---

Pedido do Daniel (21/10): "me mande os jogos de hoje em que o favorito precisa muito ganhar e vai jogar com todos os
titulares; só os jogos muito importantes para o favorito ganhar, ou empatar ou somente ganhar; análise em todas as fontes
possíveis, cheque todos os dados possíveis". É uma **exceção à Regra 0**, só quando o Daniel pedir este modo.

## 1. Triagem (script, de graça)

1. Liste os jogos de hoje que ainda não começaram, com o 1X2, pelo 365Scores (`plataformas.S365(data).jogos()`; o
   Sofascore costuma dar 403). Favorito = menor odd de vitória; fique com favorito claro (odd ≤ ~1.90), só no futebol
   masculino profissional.
2. Para cada um, levante a tabela (`tabela(comp, 1)`, posição e pontos dos dois) e a fase (`detalhe(id)`: `stageName`,
   `legNum`).
3. Escolha até 6 jogos em que o favorito tem mais em jogo: final, mata-mata (sobretudo o jogo da volta), briga direta
   por título, vaga ou rebaixamento, ou time que precisa reagir (ex.: 0 pontos na fase de liga).
4. Probabilidades de partida, por jogo:
   - mercado sem margem (vitória, empate e dupla chance);
   - modelo do 365Scores pelas tabelas casa/fora (`plataformas.lambdas` + `varredura.matriz`), só em liga com 4+ jogos
     na condição.

## 2. Pesquisa (workflow)

`Workflow({scriptPath: ".claude/workflows/favorito.js", args: {data, criterios, candidatos}})`.

- **Pesquisador:** o que está em jogo (com números), se o empate serve, XI provável e titulares (TODOS / QUASE_TODOS /
  RODIZIO), desfalques, adversário, dados cruzados em 2 fontes, `prob.py` com as médias da temporada e odds em 2+ casas.
- **Cético:** confere em outra fonte e devolve `importancia_final`, `titulares_final` e `mercado_final`.
- Jogo de importância média ou baixa, ou com rodízio, não vai ao cético.

## 3. Veredito

- **Passa:** importância MUITO_ALTA ou ALTA, titulares TODOS ou QUASE_TODOS, cético sem refutar e chance final ≥
  `criterios.prob_minima`.
- **Chance final** = a menor entre a conta independente e o modelo do 365Scores (sem nenhuma das duas, o mercado), mais
  os ajustes (±5 p.p.).
- **Mercado:** vitória quando o favorito precisa ganhar e consegue; dupla chance quando o empate serve ou é o mais seguro.
- **Mostre a odd mínima** (EV 3%) para o Daniel conferir na Betano. Odd de referência sem valor vira aviso. Regra 8: mais
  de 10 p.p. acima do mercado, desconfie e avise.

## 4. Entrega e registro

- Tabela curta: jogo · hora · competição · mercado · chance · odd mínima · o que está em jogo · titulares. Uma linha de
  risco por jogo. Sem jogo: "Nenhum jogo de favorito que precisa vencer hoje."
- Salve `analises/AAAA-MM-DD-favorito.md`.
- Registre com `previsoes.py add-json`: `analise: "favorito"`, `mercado: "vence"` ou `"dupla_chance"`, `lado` = lado do
  favorito.
- Lição nova do cético vai para `docs/licoes.md`.
- Faça commit e push.
