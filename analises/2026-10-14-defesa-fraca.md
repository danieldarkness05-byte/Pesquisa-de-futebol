# Defesa fraca do azarão x ataque forte do favorito — quarta 2026-10-14

- **Pedido do Daniel (13/10, 15h):** os jogos de 14/10 pelo método da defesa fraca, extremamente criterioso,
  com foco nas melhores oportunidades de vitória do favorito.
- **Regras:**
  - prob ≥ 60%;
  - azarão com defesa muito vazada e favorito com ataque forte;
  - sem ⚠️ RISCO;
  - favorito com ≥ 8 de 15 pontos nos últimos 5 oficiais;
  - **técnico que vai poupar titulares sai (regra nova, 13/10)**;
  - chuva só informativa.
- **Triagem (`defesa.py`, 13/10 15:10; refeita às 15:45 com 2 correções):**
  - 1.467 jogos não iniciados em todas as ligas do Sofascore; 198 com tabela casa/fora e amostra.
  - 17 passaram no corte de defesa/ataque; 12 foram aprofundados.
  - 4 saíram pela forma do favorito: Batman Petrolspor, Sagaing U20, Bridlington e Sacred Heart.
- **Pesquisa (workflow `defesa.js`, 6 agentes):** Nashville x SKC, Cahul x Congaz e Santa Fe x Jaguares.
  Eram os únicos profissionais, sem RISCO e com forma ok.

## Passou

| Jogo | Hora | Azarão sofre (condição) | Mercado | Prob. | Odd mínima |
|---|---|---|---|---|---|
| **Nashville SC x Sporting KC** (MLS) | 21:30 | SKC fora: 2,79/j (2º pior da MLS); últimos 10 fora 2,9/j, xG cedido 1,86 | **Nashville marca 2+ gols** | **~68%** | **1.52** |

### Nashville SC x Sporting KC

- **A favor:**
  - Em casa, o Nashville tem 13V 1E 0D e 2,93 gols por jogo, o melhor ataque da MLS.
  - O SKC é lanterna, com a pior defesa geral (68 gols em 28 jogos). Cede 3,46 grandes chances por jogo
    e está **sem a dupla de zaga titular** (Mosquera, Blorian e Borges fora).
  - Forma do Nashville: DEVVV (10 pts).
  - O técnico **não vai poupar o ataque**: nenhuma notícia de rodízio. Surridge, Mukhtar e Espinoza
    foram titulares em 10/10.
- **Contra:**
  - O Nashville finaliza muito acima do xG: 2,93 gols por jogo em casa com 1,83 de xG. O teste só com
    xG dá 64% para 2+.
  - São 3 jogos em 8 dias. Nos meios de semana anteriores, o Callaghan trocou 3 ou 4 jogadores da
    defesa e do meio e fez só 1 gol por jogo.
  - O SKC melhorou no ataque: 15 gols nos últimos 6 jogos, com André Luiz.
- **Probabilidade:**
  - O `defesa.py` deu 69,1% pela variante gols+xG. O cético ajustou −1 p.p., para **68%**.
  - O mercado implica ~79%: o modelo está abaixo, então a regra 8 está ok.
- **Vitória do Nashville:** 62% pelo modelo conservador e ~77% pelo mercado. A 1.19, não tem valor
  (EV −26%).
- **Valor:** a odd mínima é 1.52. Com o mercado em ~79%, a Betano provavelmente paga menos que isso.
  **Só entra com odd ≥ 1.52.**

## Não passaram

- **Cahul x Congaz (Moldávia, Liga 2):** o jogo **já foi disputado em 11/10** (1-6, súmula da
  federação, fmf.md). O Sofascore mostrava a data errada (14/10). A tese estava certa no mérito, mas não
  há o que apostar. *(Correção no `defesa.py`: evento suspeito sai.)*
- **Santa Fe x Jaguares (Colômbia):**
  - A primeira triagem usou a tabela do Apertura.
  - No Finalización, o Santa Fe marca 1,43 gol por jogo em casa (na média da liga), com xG de 1,06:
    **ataque não é forte**.
  - Desgaste: jogo de Copa com 120 minutos em 11/10.
  - *(Correção no `defesa.py`: tabela do torneio certo; refeita, o jogo não passa no corte.)*
- **Fora pela forma do favorito:** Batman Petrolspor (VVDDD), Sagaing U20 (DDVDE), Bridlington (DVDVE)
  e Sacred Heart (DVDDD).
- **⚠️ RISCO:** Antalyaspor x Kayserispor e 31 de Julio x Primero de Mayo.
- **Amador, base e universitário (fora da lista; não estão na Betano):** AES x Nashy Avtobusy (Fursat
  Liga), Kutztown x Lackawanna (NCAA feminino), Wilkes x Drew (NCAA III), Terengganu U20 x Kedah U20 e
  Riga U17 x Rēzekne U17.

## Fontes

- Sofascore (API: standings, events/last, statistics, lineups, incidents, top-players, odds bet365),
  consultado em 13/10 entre 15:10 e 15:45.
- Clubes: sportingkc.com (preview e informe de lesões, 10/10 e 14/10), nashvillesc.com (health report
  e recap).
- Federações: fmf.md (Moldávia, Liga 2, etapas 11 e 13).
- Imprensa: KCTV5, MLSsoccer.com, Squawka (escalação provável) e imprensa colombiana sobre Santa Fe e
  o El Campín.
