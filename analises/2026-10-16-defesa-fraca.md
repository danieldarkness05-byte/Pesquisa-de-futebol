# Defesa fraca do azarão x ataque forte do favorito — sexta 2026-10-16

- **Rotina das 06:52.**
  - Aprendizado: Real Estelí 1-1 (✅ 1+). Defesa fraca em 8/8; total de 11/12 (92%) para 75% previsto.
  - Amostra pequena, sem ajuste de calibração.
- **Triagem (`defesa.py`, 06:57):** 1.313 jogos não iniciados; 369 com tabela e amostra; 38 passaram na
  triagem; 12 aprofundados; 8 com mercado ≥ 60%.
- **Pesquisa (workflow `defesa.js`, 4 agentes):** só os 2 profissionais sem RISCO, Alashkert x Syunik e
  Al-Qadsiah x Abha. Os de base (Bragantino U20, Atlante U19) e o universitário (NCAA) ficaram sem
  pesquisa, para economizar, porque há caso profissional (regra da skill).

## Passou

| Jogo | Hora | Azarão sofre (fora) | Mercado | Prob. | Odd mínima |
|---|---|---|---|---|---|
| **FC Alashkert x FC Syunik** (Armênia, 1ª div.) | 10:00 | 2,67/j na conta real (6 jogos, mediana 3, 2+ em 5 de 6) | **Alashkert marca 2+ gols** | **~69%** | **1.50** |

### FC Alashkert x FC Syunik

- **A favor:**
  - Em casa, o Alashkert tem 16 gols em 5 jogos, 3+ em todos, e 2,19+ de xG em cada jogo.
  - O Syunik é recém-promovido e tem o pior ataque da liga (0,56 gol/jogo).
  - O teste só com xG dá 2+ entre 67% e 80%. Sem desfalques. Sem aperto de calendário: próximo jogo em 24/10.
  - O local (Football Academy, Yerevan) foi confirmado no site da liga.
- **Contra:**
  - O Alashkert marcou +3,8 acima do xG em casa (lição 7).
  - O Syunik joga com linha de 3 desde a R8 e tem um goleiro em boa fase (lição 11).
  - A forma do Alashkert está no limite (EVEEE, 7 pts).
- **Ajuste:** −1 p.p. do cético → defesa.py 69,9% − 1 = **68,9%**; odd mínima 1.50.
- **Valor:** o mercado sem margem dá ~71% para o 2+ (λ implícito do 1X2), então a casa deve pagar
  abaixo de 1.50. **Valor improvável.**
- **Dado corrigido:** o Sofascore invertia o mando e o placar do jogo da R8 (lição 31).

## Não passou

- **Al-Qadsiah x Abha (Saudi Pro League, 10:15): refutado pelo cético.**
  - Ajustado pelo adversário, o xG cedido pelo Abha é mediano (lição 30).
  - Os gols sofridos estavam inflados por 2 gols contra e 3 erros, e o 2+ cai para ~65%.
  - O mercado dá ~96% para o 1+ e 84% para o 2+, sem valor.
- **⚠️ RISCO:** BATE 2 x Slutsk, El Seka x Ismaily e St. Bernhard x Litschau.
- **Base e universitário sem pesquisa:** Bragantino U20, Atlante U19 e Arkansas State x Appalachian State.

## Fontes

- Sofascore (API, consultado em 16/10 às 06:57).
- Site oficial da Premier League armênia (premierleague.ffa.am, 16/10).
- RSSSF, FotMob, Vavel.
- Saudi Pro League: Sofascore, com 74 jogos para o xG da liga.
