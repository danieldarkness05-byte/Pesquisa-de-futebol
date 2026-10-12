# Defesa fraca do azarão x ataque forte do favorito — segunda 2026-10-12

- **Pedido do Daniel:** 4 jogos de hoje em que o azarão tem defesa extremamente fraca e o favorito tem ataque forte. **A regra da chuva ficou de fora** desta análise, a pedido dele.
- **Coleta (14:06–14:30):**
  - Sofascore: os 20 jogos não iniciados das ligas do `config.json`. Para cada um, a tabela casa/fora da temporada e os últimos 10 jogos de liga na condição (gols, chutes, xG contra).
  - Triagem ampla dos 243 jogos do dia no Sofascore: nenhum caso novo forte fora do config, só a Série C italiana com amostra de 4 jogos.
- **Pesquisa:** 7 jogos foram para os workflows `defesa-fraca-segunda`, com 1 pesquisador (Sofascore + imprensa) e 1 cético por jogo, 14 agentes no total.
- **Probabilidades:** `prob.py gols`, por dois métodos:
  - método de força, com médias casa/fora da temporada;
  - λ da peneira, com mix de gols e xG encolhido.
  Vale o mais conservador, mais o ajuste do cético (teto de ±5 p.p.).

## Passaram (tese de pé no cético)

| Azarão · jogo | Hora | Defesa do azarão (na condição) | Ataque do favorito (na condição) | RISCO |
|---|---|---|---|---|
| **Ponte Preta** · Novorizontino x Ponte Preta | 19:00 | Fora: 2,69 sofridos/jogo, pior da Série B (média 1,33). Últimos 10: xG contra 2,65, 20,8 chutes contra, 0 jogos sem sofrer | Casa: 1,63/jogo (5º), xG 2,2 nos últimos 10 | não (Ponte marca 0,44 fora) |
| **Recoleta** · Nacional x Recoleta | 19:20 | Fora: 1,83/jogo, 3ª pior (média 1,28). Geral: 2,00/jogo, a pior da liga. xG cedido fora 1,86 | Casa: 1,83/jogo (3º), xG 2,09; 2+ gols em 4 de 6 | não (0,83 fora) |
| **Wieczysta Kraków** · GKS Katowice x Wieczysta | 15:30 | Fora: 2,33/jogo, 2ª pior (média 1,64); sofreu 2+ em todos os 6 jogos fora | Casa: 3,67/jogo (1º), xG 2,38; temporada xG 1,90 (3º) | **⚠️ sim** (Wieczysta marca 1,5 fora) |

### Novorizontino x Ponte Preta
- **A favor:**
  - Fora, a Ponte tem 1V 0E 15D.
  - O xG confirma os gols sofridos, então não há regressão a esperar.
  - Sofre gols até de times fracos e está rebaixada, com salário atrasado.
- **Contra:**
  - **Robson (16 gols) está fora** (lesão), e Reidiney e Léo Naldi estão suspensos. O cético aplicou −3 p.p.
  - Os dois 6x0 inflam a média de gols sofridos da Ponte; sem eles, ela sofre 2,1 por jogo.
- **Mercados (`prob.py`):**
  - Novorizontino +1,5 gol: 82,6–84,0%, ou **~80%** com o ajuste → **odd mínima 1.30**. A bet365 não oferece esse mercado; conferir na Betano.
  - Vitória a 1.06 e over 2,5 a 1.29: sem valor.
- **Sanidade (regra 8):** o mercado implica uns 2,7 gols do Novorizontino, cerca de 75% de chance de 2+. Fica dentro dos 10 p.p.
- **Chuva (desconsiderada):** 61% e 3,0 mm no dia; 25% e 0 mm na janela do jogo.

### Nacional x Recoleta
- **A favor:**
  - O Recoleta está há 9 jogos sem vencer.
  - Tem 4 expulsões e 5 pênaltis cometidos no Clausura.
  - O artilheiro Benítez (5 gols e 5 assistências) volta da seleção.
- **Contra:**
  - O Recoleta marcou em todos os confrontos diretos do último ano.
  - A odd do Nacional subiu de 1.53 para 1.67 sem notícia que explique.
  - O mercado dá uns 48–50% para o Nacional fazer 2+ gols, contra 55–74% dos modelos (regra 8).
  - O cético deu ajuste 0.
- **Mercados:**
  - Nacional +0,5 gol: **84%** → **odd mínima 1.22** (o mercado implica cerca de 80%).
  - Nacional +1,5: 55%, abaixo do corte.
  - Vitória: 59,5% a 1.67, EV de −1%, sem valor.
- **Chuva (desconsiderada):** 98% e 9,9 mm em Assunção. O jogo do Recoleta contra o Libertad em 03/10 foi suspenso por chuva.

### GKS Katowice x Wieczysta Kraków
- **A favor:**
  - O zagueiro Milić saiu lesionado em 09/10 e a situação dele é N/D.
  - O time já usou 3 goleiros na temporada.
  - Shkurin e Nowak, do Katowice, marcaram em 09/10.
- **Contra:**
  - Pelo xG, a defesa do Wieczysta fora é só a 7ª pior (1,80, com média de 1,70). Há azar e goleiro nos gols sofridos.
  - O técnico novo, Kopić, melhorou a defesa.
  - A amostra do Katowice em casa é de 3 jogos.
- **Mercados:** o mercado dá 46% de vitória do Katowice e o modelo 62%, mais de 10 p.p. de diferença (regra 8). Com ⚠️ RISCO, **nenhum mercado**.

## Não passaram (o cético derrubou)

- **Chapecoense x Athletico (19:30):**
  - A Chape tem a pior defesa em casa (2,23/jogo), mas está uns 0,9 gol/jogo acima do xG.
  - O Athletico é mediano fora pelo xG (1,10).
  - Kerwin Vargas e Benavídez estão fora, e o técnico está suspenso.
  - ⚠️ RISCO: a Chape marca 1,38 em casa.
- **Always Ready x Independiente Petrolero (18:15):**
  - O Independiente é a pior defesa da liga em volume, mas sofre 1,89 gol/jogo fora, contra média de 1,84 (mediana em gols).
  - ⚠️ RISCO: marca 1,56 fora.
- **Fortaleza x CRB (16:00):**
  - Com Fábio Matias, o CRB sofre 1,29 gol/jogo fora (xG 1,13).
  - O Fortaleza de Autuori faz 1,17/jogo em casa.
  - ⚠️ RISCO: o CRB tem o 2º melhor ataque da liga.
- **GV San José x Guabirá (16:00):**
  - O Guabirá tem a pior defesa fora (2,9), inflada por 3 goleadas na altitude e uma expulsão.
  - O GV tem ataque fraco: 1,3 em casa, 13º de 16, e é o lanterna.
- **Triagem (sem pesquisa):**
  - Criciúma x América-MG e Gimnasia x Newell's: favorito com ataque fraco em casa.
  - Torino x Udinese, Levante x Sevilla, Famalicão x Alverca, Coventry x Newcastle: não encaixam.

## Fontes

- Sofascore (API: standings home/away/total, events/last, event/statistics, lineups, incidents, top-players, odds bet365), consultado em 12/10 entre 14:06 e 14:30.
- Imprensa:
  - Brasil: site oficial do Novorizontino, Hora Campinas, Futebol Interior, O Povo, Diário do Nordeste, Gazeta Esportiva, DGABC, Paraná Jor.
  - Paraguai: ABC Color, D10, Crónica, 1000 Noticias.
  - Polônia: Flashscore.pl, ekstraklasa.org.
  - Bolívia: Visión 360, La Patria, El Deber/Diez.
- Open-Meteo (`clima.py`), apenas como informação.
