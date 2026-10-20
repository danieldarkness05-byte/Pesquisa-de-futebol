# Defesa fraca x ataque forte — 20/10/2026

**Resultado: 1 jogo passou** (liga semiprofissional inglesa, dificilmente na Betano).

| Jogo | Hora | Liga | Azarão (sofre/j fora) | Mercado | Prob. | Odd mín. |
|---|---|---|---|---|---|---|
| **Uxbridge x Malvern Town** | 15:45 | Southern League Premier South (Step 3) | 3,33 (pior da liga) | **Uxbridge marca 1+** | **88,7%** | **1.17** |

Critério: azarão com índice de defesa ≥ 1,4 e favorito com ataque ≥ 1,15 na condição, favorito com 7+ pontos nos
últimos 5 oficiais, prob. ≥ 60% depois do ajuste e cético sem refutar. Chuva só informativa.
Triagem (`defesa.py`, 07:00): 826 jogos, 26 na triagem, 12 aprofundados, 10 com `passa`.
- **Sem odds e com temporada editada à mão** (City Planners x Road Lions, Nigéria; Sarsabz Yashlar x Omar Zawak,
  Afeganistão): sem como verificar e fora da Betano.
- **Amadores sem odds** (Grorud 2, Khan Tengri Reserve, Duao, March Town) e **⚠️ RISCO** (Kilia Kiel, Drury):
  ficaram fora.
- **Pesquisados:** os 2 jogos com odds bet365 (Southern League), para economizar agentes. Workflow `defesa.js`:
  4 agentes.

## Uxbridge x Malvern Town — PASSOU (Uxbridge marca 1+)

- **A favor:** o Malvern (recém-promovido) é a pior defesa fora: 20 sofridos em 6 jogos, mediana 4, 2+ em 5 de 6
  (7 de 8 com as copas). Sem expulsões, e sofre 1,97 vez o esperado pela força dos adversários (lição 30).
  O Uxbridge é 4º, invicto em casa na liga (5V 1E, 2,5 gols/j), marcou em 9 dos últimos 10 em casa e briga pelo topo.
  Sem notícia de rodízio: o clube só rodou o time na Middlesex Cup (13/10). Mando e data conferidos (365Scores e
  Betexplorer). Odds paradas desde a abertura.
- **Contra:** o ataque chega desfalcado. Moore (7 gols) é dúvida (lesão no aquecimento em 17/10), Le Paih e
  McCoy estão fora e Deadfield foi expulso em 17/10. São 3 jogos em 8 dias.
- **Ajuste:** −3 p.p. no 1+ (91,7% → 88,7%), pelos desfalques. O 2+ (85%) caiu pela regra 8: os chãos davam
  64–66% e o mercado 59–64%.
- **Mercado:** 1+ em 86,3% (proporcional) e 88,8% (potência, lição 54). Empata com o modelo: valor só com odd ≥ 1.17.

## Taunton x Bracknell — REFUTADO

O 0-7 da estreia decidia a triagem. Sem ele, a defesa do Bracknell fica na média (1,6/j fora, ×0,90), e o 1+ do
Taunton (~84%) fica igual ao mercado. A forma do Taunton só fecha os 7 pts com o FA Trophy (lição 29) e o Bracknell
reformulou o elenco em 13/10. Virou a lição 55, agora automática.

## Evolução

- **`defesa.py`:** `ga_aparada` (média sem a pior goleada); defesa na média ou melhor sem ela tira o jogo (com teste).
- Lições 54 e 55 em `docs/licoes.md`. Previsão #30 registrada.

Fontes: Sofascore (tabelas, amostras, incidentes, odds bet365); 365Scores e Betexplorer (data); uxbridgefc.com
(relatos de 10, 13 e 17/10); Malvern Observer (17/07); Football Web Pages e FotMob (Bracknell); Open-Meteo.
Até agora (defesa): 12/13 acertos (92%) para 77% previsto.
Dados pesquisados até 07:45.
