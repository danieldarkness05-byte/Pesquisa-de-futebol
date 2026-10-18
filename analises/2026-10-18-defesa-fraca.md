# Defesa fraca do azarão x ataque forte do favorito — domingo 2026-10-18

- **Rotina das 06:52.** Aprendizado: 17/19 previsões resolvidas, 75% previsto; amostra pequena, sem ajuste.
- **Triagem (`defesa.py`, 07:15):** 6.916 jogos não iniciados; 1.096 com tabela e amostra; 138 passaram na
  triagem; 12 aprofundados; 8 com mercado ≥ 60%.
- **Pesquisa (workflow `defesa.js`, 6 agentes):** Puerto Cabello x Monagas, Santa Cruz x Antofagasta e
  Rancho Santana x Diriangén (1ª e 2ª divisões com odds).
  - Ficaram de fora: BK Olympic (08:00, sem tempo), Mictlán (2ª da Guatemala, 2+ a 70% contra 68% do
    mercado), Viltis e Huehuetecos (sem odds) e Tatran (RISCO). Os outros 4 saíram pela forma do favorito.

## Passou

| Jogo | Hora | Azarão sofre | Mercado | Prob. | Odd mínima |
|---|---|---|---|---|---|
| **Rancho Santana x Diriangén** (Nicarágua, 1ª div.) | 22:00 | 2,33/j em casa; xG cedido de 2,28/j (pior da liga) | **Diriangén marca 2+** | **~68%** | **1.52** |

- **A favor:**
  - O Diriangén é o melhor visitante da liga (2,43/j, 2+ em 6 de 7 fora).
  - O Rancho é o lanterna e cede 1,40x o xG habitual dos adversários.
  - No H2H, o Diriangén fez 2+ em 8 de 9.
  - O técnico não vai poupar: o próximo jogo é só em 25/10, e o time já está fora da Copa Centroamericana.
- **Contra:**
  - O jogo é no Estadio Nacional, que o Diriangén usa como casa, e lá ele fez só 1,5/j (lição 43).
  - Luis Coronel (5 gols) ficou fora dos relacionados no J12.
  - O Rancho tem técnico novo (Urroz, ex-Diriangén). Os gols do Diriangén fora estão acima do xG.
- **Ajuste:** −2 p.p. → 70% − 2 = **68%**; odd mínima 1.52.
- **Mercado:** só há 1X2 (1.27). O λ implícito dá ~65% para o 2+, então o valor só aparece se a Betano
  pagar ≥ 1.52.

## Não passaram (refutados pelo cético)

- **Academia Puerto Cabello x Monagas:** o `defesa.py` leu a tabela do Apertura.
  - No Clausura, a defesa do Monagas fora é mediana (1,67/j) e o ataque é bom (RISCO).
  - **Corrigido no `escolher_grupo`, com teste (lição 44).**
- **Santa Cruz x Antofagasta:** com o técnico atual, a defesa do Santa Cruz em casa está na média da liga
  (xG ajustado 1,01; últimos 5 com 1,0 gol/j). O rótulo de pior defesa vem do técnico anterior (lição 45).

## Fontes

- Sofascore (API, consultado em 18/10 às 07:15).
- Site oficial da Liga Primera da Nicarágua (ligaprimera.com), 365Scores, Flashscore, Wikipedia.
