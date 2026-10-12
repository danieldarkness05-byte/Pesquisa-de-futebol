# Defesa fraca do azarão x ataque forte do favorito — terça 2026-10-13 (todas as ligas do Sofascore)

- **Pedido do Daniel:** a mesma análise de defesa fraca, agora com todas as ligas do Sofascore. Chuva **desconsiderada**, a pedido dele, e citada só como informação.
- **Triagem (`triagem_total.py`, no scratchpad), feita em 12/10 às 18:40:**
  - 852 jogos não iniciados em 13/10. Destes, 210 tinham tabela casa/fora e pelo menos 4 jogos na condição.
  - Saíram 338 por amostra < 4, 131 por ser copa ou amistoso sem tabela e 143 por não ter odds nem favorito claro.
  - Corte: o azarão sofre ≥ 1,4× a média da liga na condição, e o favorito marca ≥ 1,15× a média.
  - Passaram 23 jogos, a maioria amadora ou universitária com 4 jogos de amostra. Deles saíram 6 candidatos com amostra de verdade. A lista inclui o Norrköping, que ficou em 1,39× e entrou com tolerância.
- **Pesquisa:** workflow `defesa-fraca-dia`, com 1 pesquisador (Sofascore + imprensa) e 1 cético por jogo, 12 agentes no total. A primeira rodada foi interrompida pelo limite de uso; retomei depois do reset.
- **Probabilidades:**
  - `prob.py gols` pelo método de força;
  - λ encolhido da peneira (k = 4), com Dixon-Coles ρ −0,10 e incerteza σ 0,15.
  - Vale o mais conservador, com o ajuste do cético (≤ ±5 p.p.) e conferido contra a frequência real.

## Passaram (cético não derrubou) — sem ⚠️ RISCO em nenhum

| Azarão · jogo | Hora | Defesa do azarão | Ataque do favorito | Mercado (prob. · odd mínima) |
|---|---|---|---|---|
| **Pakhtakor Tashkent II** · Pakhtakor II x Aral (Uzbequistão, Pro Liga) | 10:00 | Fora: 25 sofridos em 11 jogos (2,27/j); sofreu 2+ em 9 dos últimos 10 fora | Aral em casa: 25-3 em 11 jogos, 100% de vitórias, 2+ gols em 7 dos últimos 10 | Aral +1,5 gol: **~75%** · **1.37** |
| **GIF Sundsvall** · Norrköping x Sundsvall (Suécia, Superettan) | 14:00 | Pior defesa da liga (2,12/j); fora 2,08/j com xG cedido de 2,04 | 2,0/j em casa, xG 2,24 (melhor ataque da liga); Nyman tem 16 gols | Norrköping +0,5: **~83%** · **1.24**. O +1,5 dá 57–63%, no limite |
| **FC Augsburg II** · Buchbach x Augsburg II (Alemanha, Regionalliga Bayern) | 14:00 | Fora: 17 sofridos em 7 (2,43/j), 2ª pior; xG contra 2,54 | Em casa 2,17/j (13 em 6), mas o xG recente é mediano (~0,9–1,6) | Buchbach +1,5: **~61%** · **1.69**; +0,5: ~85% · 1.22 |
| **Christchurch** · Bashley x Christchurch (Inglaterra, Wessex Premier, 9ª divisão) | 15:45 | Fora: 32 sofridos em 9 (3,56/j); 0 pontos e 16 jogos sem vencer | Em casa 3,33/j, o 1º da liga | Bashley +1,5: **~65%** (o modelo dá 89%, mas a frequência real é 67–70%) · **1.58** |

**Sem odds no Sofascore para os mercados de gol do favorito.** Conferir na Betano: só entra se a odd for ≥ a mínima. Aral, Buchbach e Bashley não têm nem 1X2 no Sofascore.

### Notas por jogo

- **Pakhtakor II x Aral:**
  - O Sofascore põe o Pakhtakor II como mandante, mas a liga (PFL, jogo 4352) põe o jogo no Turon, em Nukus, casa do Aral. Calculei pelo mando real. Pelo mando do Sofascore a probabilidade dá praticamente igual: Aral 2+ ~76%.
  - O Aral não joga uma partida oficial há 22 dias (a última rodada foi W.O.).
  - O Aral depende do artilheiro Qalmagambetov (43% dos gols).
  - Ajuste do cético: +1 p.p.
- **Norrköping x Sundsvall:**
  - O Norrköping garante o acesso se vencer.
  - Os gols sofridos fora pelo Sundsvall são irregulares: mediana de 1 e 2+ em só 5 de 12 jogos. O bloco baixo segurou os jogos contra o top 4.
  - Os dois times vêm de 3 semanas parados.
  - Ajuste do cético: −3 p.p.
  - A vitória a 1.18 não tem valor (modelo 74–75% contra 77% do mercado).
- **Buchbach x Augsburg II:**
  - É o 3º jogo do Buchbach em 7 dias, e o técnico fala em rodízio.
  - Leo Haas está fora.
  - O xG do Buchbach indica regressão.
  - Ajuste do cético: −4 p.p. É o caso mais frágil dos quatro.
- **Bashley x Christchurch:**
  - Liga amadora, sem xG.
  - É o 4º jogo do Bashley em 11 dias.
  - O Christchurch sofreu 2 gols depois de uma expulsão e teve um colapso no 3-5.
  - Ajuste do cético: −2 p.p. Dificilmente está na Betano.
- **Chuva (informação):**
  - Norrköping: chuva só depois do jogo.
  - Buchbach: 75% e 1,4 mm na janela do jogo.
  - Bashley: chuva só de manhã.

## Não passaram

- **Imperial Unido x Deportes Rancagua (Chile, 3ª divisão):**
  - Com o técnico Tapia, o Imperial sofre 1,43/j em casa, perto da média.
  - O Rancagua fez 2+ fora em só 42% dos jogos.
  - O modelo ficou 13–16 p.p. acima do mercado (regra 8).
- **Queen's Park x Inverness (Escócia, Championship):**
  - O Inverness cria 1,22 xG/j fora, abaixo da média da liga.
  - A chance de 2+ fica em 45–49%.
- **Triagem (sem pesquisa):**
  - Richards Bay x Sundowns: a defesa do Richards Bay sofre só 1,3/j nos últimos 10 em casa, e o jogo tem ⚠️ RISCO.
  - Cartaginés x Puntarenas: o Puntarenas sofre 1,1/j nos últimos 10 fora.
  - O resto da lista é NCAA ou amador com 4 jogos de amostra.

## Fontes

- Sofascore (API: standings, events/last, event/statistics, lineups, incidents, odds bet365), consultado em 12/10 entre 18:40 e 19:30.
- Ligas e clubes:
  - Uzbequistão: PFL (pfl.uz).
  - Suécia: ifknorrkoping.se, gifsundsvall.se.
  - Alemanha: tsv-buchbach.de.
  - Escócia: Inverness Courier, ictfc.com.
  - Wikipedia (Wessex League, Pro League 2026).
- Open-Meteo (`clima.py`), só como informação.
