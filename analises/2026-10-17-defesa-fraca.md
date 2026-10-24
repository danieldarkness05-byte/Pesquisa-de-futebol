# Defesa fraca do azarão x ataque forte do favorito — sábado 2026-10-17

- **Rotina das 06:52.** Aprendizado: 13/14 previsões resolvidas, 74% previsto; amostra pequena, sem ajuste.
- **Triagem (`defesa.py`, 07:05):** 7.036 jogos não iniciados; 1.816 com tabela e amostra; 208 passaram na
  triagem; 12 aprofundados; 8 com mercado ≥ 60%.
- **Pesquisa (workflow `defesa.js`, 6 agentes):** 3 de 8.
  - Ficaram de fora: os 3 com temporada editada à mão no Sofascore (Pécsi, Cigánd, Ilhas Cook; lição 23),
    o Råde (4ª divisão da Noruega, sem odds) e o Górnik Łęczna (regra 8: +13 p.p.).
  - Os 4 que saíram pela forma do favorito: Skeid, Amkar, Ganzhou e Talleres.

## Passou

| Jogo | Hora | Azarão sofre | Mercado | Prob. | Odd mínima |
|---|---|---|---|---|---|
| **FC Sevastopol x Neftyanik** (Rússia, 4ª div.) | 09:00 | 3,33/j fora (pior da liga; mediana 3; 2+ em 10 de 12) | **Sevastopol marca 1+** | **~92%** | **1.12** |
| **Champs Academy x Fraijanes** (Guatemala, 2ª div.) | 18:00 (site da liga: 19:00) | 1,75/j em casa (pior da liga) | **Fraijanes marca 1+** | **~82%** | **1.26** |
| **IK Uppsala x Kristianstads** (Suécia, Damallsvenskan) | 10:00 | 2,7/j em casa; desde o desmonte, 3,7 de xG cedido | **Kristianstads marca 2+** | **~68%** | **1.51** |

### Notas

- **Sevastopol:**
  - O 2+ (80%) caiu: regra 8, com o mercado em 64%, o teto do Sevastopol em casa (nunca passou de 3) e o
    título já decidido em 11/10. Fica o 1+, com −3 p.p.
  - O mercado (Winline 1.28/5.20/9.40) implica ~89% para o 1+, então o valor é improvável.
  - Liga sem xG, que dificilmente está na Betano.
- **Fraijanes:**
  - O Fraijanes marcou em todos os 16 jogos e precisa da vitória.
  - −2 p.p. pelo trecho de defesa mediana do Champs (R9 a R13). Sem odds. O 2+ fica de fora.
- **Kristianstads:**
  - +3 p.p.: o teto de frequência vinha da amostra mista (lição 36). Desconto pela saída da Boama e pelo xG
    mediano do KDFF fora (1,54).
  - O mercado dá ~83% para o 2+ (odd perto de 1.18), então o **valor é muito improvável**.

## Fontes

- Sofascore (API, consultado em 17/10 às 07:05).
- ruinformer.com e bookmaker-ratings.ru (Sevastopol).
- tvmatchen.nu e FotMob (Uppsala).
- primeradivision-gt.com e 365Scores (Guatemala).
