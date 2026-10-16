# Lições das pesquisas (a análise evolui por aqui)

Arquivo vivo. O `/defesa-fraca` (e o `/ouro`) **lê este arquivo antes de cada análise**, e os
pesquisadores e céticos do workflow também. Cada lição vem de um caso real, com data. Quando uma
lição puder virar conta, ela vira alerta automático em `ferramentas/defesa.py`. Nesse caso,
anote "(automático)".

Calibração: `python3 ferramentas/previsoes.py resumo`. Com **≥ 30 previsões resolvidas** numa faixa
de probabilidade que acerta **5 p.p. ou mais abaixo** do previsto, fique mais conservador nessa
faixa e registre aqui.

## Defesa do azarão

1. **A média engana quando vem de goleadas.** Olhe a mediana e a frequência de "sofreu 2+".
   - Sundsvall fora, 12/10: média 2,08, mas mediana 1 e só 42% dos jogos com 2+ sofridos.
   - Ponte Preta: dois 6x0 inflavam a média. *(automático: "média inflada por goleadas"; prob
     limitada pela frequência)*
2. **Técnico novo muda a defesa.** Use o recorte depois da troca.
   - CRB com Fábio Matias: 1,29 sofrido/jogo fora, contra 1,69 na temporada.
   - Imperial Unido com Tapia: 1,43, contra 1,83.
   - Wieczysta com Kopić. *(automático em parte: "defesa melhorando" nos últimos 5)*
3. **Gols sofridos bem acima do xG cedido = azar que tende a passar.**
   - Chapecoense em casa: 2,23 sofridos com 1,33 de xG.
   - Wieczysta fora: +3,2 gols acima do xG. *(automático)*
4. **Expulsões inflam os gols sofridos.**
   - Recoleta: 4 expulsões no Clausura.
   - Guabirá: 5x0 com um a menos.
   - Christchurch: 2 gols depois de um vermelho. *(automático: expulsões na amostra)*
5. **A tabela da temporada com 4 jogos engana.** Compare com os últimos 10 na condição.
   - Richards Bay: 2,25 na temporada, 1,3 nos últimos 10. *(automático)*
6. **Pior defesa no volume não é pior defesa em gols.** O Independiente Petrolero cedia 18,8
   chutes/jogo, mas sofria gols na média da liga. Confira os dois.

## Ataque do favorito

7. **Gols acima do xG regridem.**
   - Inverness: 9 gols com 5,05 de xG.
   - Buchbach: 8 gols com 4,4.
   - Shkurin (Katowice): 7 gols com 3,93 de xG. *(automático)*
8. **Artilheiro fora pesa muito.** O Robson tinha 30% dos gols do Novorizontino: ajuste de −3 p.p.
   Se um jogador tem mais de 40% dos gols (Qalmagambetov, Aral), escalação não confirmada é risco.
9. **Calendário apertado → rodízio.** *Regra do Daniel (13/10): técnico que vai poupar titulares tira o
   jogo da lista; a notícia confirma, o calendário só alerta.* Três jogos em 7 dias (Buchbach, Bashley). *(automático)*
10. **Pausa longa → falta de ritmo.** Norrköping e Aral, com 3 semanas sem jogo oficial.
    - Com goleiro titular fora junto, o desconto é maior: o PAOK perdeu de 1-3 em 12/10, com xG de 1,25 a 2,36.
    *(automático para mais de 18 dias; amistosos contam como jogo)*
11. **Time grande se fecha contra time grande; o azarão fechado segura o placar.** O Sundsvall perdeu
    de 1-0 para todo o top 4 fora. Contra bloco baixo, prefira "marca 1+" a "marca 2+".

## Dados e fontes

12. **O Sofascore pode inverter o mando.** Pakhtakor II x Aral aparecia em Tashkent, mas a liga
    (PFL) marcou o jogo em Nukus, casa do Aral. O pesquisador confirma o estádio no site da liga ou
    do clube.
13. **Coordenadas de estádio erradas no Sofascore** (LASK, San Luis Potosí): a cidade confere
    (`localizar`).
14. **Ligas amadoras, de base e times B** (a "Fursat Liga" do Azerbaijão é amadora: 14/10):
    - não têm xG, a amostra é curta e o elenco muda;
    - dificilmente estão na Betano;
    - entram na lista só se não houver caso profissional melhor.
    *(automático: alerta e ordem)*

17. **Teste de chão só com xG antes de um 2+** (Nashville, 14/10).
    - λ_xG = xG pró do favorito na condição × xG cedido do azarão na condição ÷ xG médio dos mandantes da liga.
    - Ranking por gols esconde ataque de chances medianas com finalização excepcional: o Nashville é o 1º em
      gols em casa, mas tem xG de 1,83, na média da liga.
    - Se o 2+ ainda passar de 60% com esse λ, fica; senão, rebaixe para 1+.
    - "Defesa melhorando" só vale se o xG cedido dos últimos 5 também cair. Se o xG ficar igual, é só
      goleada saindo da amostra.

## Dados e fontes (continuação)

18. **Liga editada à mão no Sofascore lista jogo já disputado como futuro** (Cahul x Congaz, Moldávia:
    o jogo foi em 11/10, 1-6, e aparecia como 14/10). Sinais:
    - o mesmo time com dois eventos no mesmo horário;
    - evento "não iniciado" com placar preenchido.
    *(automático: "evento suspeito", sai da lista)*
19. **Apertura x Finalización (ou Clausura) na mesma temporada:** a tabela tem que ser a do torneio do
    jogo. Santa Fe x Jaguares, 14/10: com a do Apertura, o λ dava 2,83; com a do Finalización, ~2,0, e o
    ataque do Santa Fe era só médio. *(automático: grupo cujo nome está no nome do torneio)*

20. **Sem xG, o teste de chão do 2+ usa as médias GERAIS da temporada** (Bridlington, 14/10): com 5 ou 6
    jogos por condição, o recorte casa/fora infla o favorito que marca muito mais em uma delas
    (2,0 fora contra 1,2 em casa). O λ caiu de 2,18 para 1,97, e o 2+ de 63% para 59%.
    *(automático: variante "geral" no `defesa.py`)*
21. **Data do jogo em liga pequena:** confira numa 2ª fonte (365Scores ou Flashscore). Em Real Estelí x
    Jalapa (Nicarágua), o Sofascore dava 14/10 18:00, e o jogo real era 15/10 22:00. O campo
    `changeTimestamp` não ajuda, porque vem 0 em todos os jogos. *(o pesquisador confere `data_confirmada`)*

22. **A tabela da temporada passa no corte, mas a amostra recente na condição desmente** (15/10):
    - o Cumbayá marcava 1,36 por jogo em casa na tabela, mas 0,9 nos últimos 10 em casa (marcou em só 4);
    - a defesa do La Viena sofria 1,5 por jogo na tabela, mas 0,7 nos últimos 10.
    Com 5 ou mais jogos recentes na média da liga (ou melhor, no caso da defesa), o jogo sai.
    *(automático: `contradiz_tese_recente` no `defesa.py`)*

23. **Liga criada à mão no Sofascore** (United Front x Prime Athletic, "East Championship League" da
    África do Sul, 15/10):
    - temporada editada e os 16 times criados pelo editor, com nomes genéricos;
    - sem estádio, árbitro ou jogadores;
    - resultados lançados em lote, e nenhuma 2ª fonte (Flashscore, 365Scores, web).
    Não dá para verificar nada: sai. Só a temporada editada (amadoras reais, como a Wessex) vira alerta.
    *(automático: `liga_nao_verificavel`)*

## Mercado (regra 8)

15. **Modelo mais de 10 p.p. acima do mercado:** quase sempre o mercado sabia algo.
    - Katowice: o modelo exagerava com 3 jogos de amostra.
    - Rancagua: viagem e chuva.
    - Nacional: odd subindo sem notícia.
    *(automático: λ implícito do 1X2 + over 2,5)*
16. **Odd que sobe contra o favorito sem notícia** (Nacional, de 1,53 para 1,67) é sinal de alerta.
    Procure escalação e desfalques antes.
24. **Azarão forte: teste de chão só com xG antes da dupla chance** (Henan x Tianjin, 16/10).
    - O modelo de gols dava 61% para o Tianjin não perder; só com xG, 51%; o mercado sem margem, 49%.
    - O Tianjin pontuava fora com sorte: sofreu 12 gols com 21,1 de xG cedido e perdeu o xG em 8 de 13 jogos.
    - Quando o xG traz a prob. para perto do mercado, os +10 p.p. da regra 8 são sorte defensiva ou de
      finalização, não informação que o mercado perdeu.
    - Vale também para o favorito: sequência de empates em casa com xG dominante (Henan, 1,54 x 0,95) é
      finalização azarada, não time fraco.
    - Mesma ideia das lições 3 e 17 (3º caso) → *(automático: variante "xg" no mínimo do `azarao.py`)*

## Azarão forte

25. **Variante só xG na escala de gols infla os λ** (Livorno x Grosseto, 16/10).
    - O `azarao.py` normaliza o xG pela média de GOLS da liga. Na Serie C B, o xG médio é 1,67 x 1,46 e os
      gols são 1,40 x 1,10: o λ do visitante inflava 33% e o do mandante 19%, a favor do azarão visitante.
    - Normalizado pelo xG da liga, a dupla chance do Grosseto caiu de 70% para 67%.
    - *Candidato a automático:* guardar o xG médio da liga e reescalar. Até lá, o cético confere.
26. **Azarão que só pontua contra a metade de baixo** (Locomotive x Merani, 16/10).
    - Meça o ppg do azarão contra times do nível ATUAL do favorito, não pela posição na tabela.
    - Favorito que mudou no meio da temporada (rebaixado, reformulado, técnico novo): use o ppg dos últimos
      10 a 14 jogos para saber em que faixa ele está. O Locomotive era 10º, mas fazia 2,07 pt/j desde a R10;
      o Merani fazia 0,78 pt/j contra o top 8, e a forma VVVEE veio só contra o 11º ao 16º.
    - O Grosseto também: 10 pts fora, todos contra o 14º, 16º, 17º e 20º.
27. **Sem xG, o teste de chão usa três sinais** (Scheiblingkirchen x Krems, 16/10).
    - Muitos pontos com saldo perto de zero (19 pts com 19-19);
    - escanteios e posse perdidos em quase todo jogo, inclusive em casa (escanteios 22 x 62);
    - recém-promovido em início de temporada.
    - Com os três, refaça a prob. com uma amostra mais longa do favorito (temporada anterior, se o elenco é o
      mesmo): o Krems com 27 jogos derrubou a dupla chance de 61% para 54%, perto do mercado (57%).
28. **Margem da casa em liga pequena estreita a janela de valor** (Jonava, Merani e Scheiblingkirchen, 16/10).
    - Com ~11% de margem no 1X2, a dupla chance do azarão só tem EV ≥ 3% se o modelo ficar uns 8 p.p. acima do
      mercado sem margem. A partir de +10 p.p. a regra 8 já desconfia: sobra pouco espaço.
    - Sem odd de DC na bet365, a casa paga mais ou menos a DC implícita no 1X2: 1/(1/odd_empate + 1/odd_azarão).
    - Os 3 casos tinham DC implícita abaixo da odd mínima (1.47, 1.56 e 1.50).
    *(automático: `odd_dc_sintetica` no `azarao.py`, marcada como "1X2 implícita")*
29. **Forma 7+ que só passa por causa de jogo de copa** (AB, 16/10).
    - O AB tinha 9 pts nos últimos 5 com a vitória sobre o Sønderjyske na copa; só na liga, 6.
    - Duas das vitórias na liga vieram com xG negativo. Confira a forma só da liga e o xG das vitórias antes
      de chamar o azarão de "em boa fase" (a régua do Daniel continua contando todos os jogos oficiais).

30. **Ajuste o xG cedido pela força do adversário antes de chamar a defesa de muito fraca** (Al-Qadsiah x
    Abha, 16/10).
    - Com poucos jogos na condição, divida o xG cedido em cada jogo pelo xG que aquele adversário costuma
      criar na mesma condição, sem contar o próprio jogo.
    - Se a mediana dessa razão ficar perto de 1 ou abaixo, a defesa é mediana, mesmo com xG bruto alto.
    - O Abha cedia 1,91 de xG fora (5º pior), mas só 0,57 a 0,61 do xG habitual do Ahli e do Nassr. O número
      alto vinha de um jogo atípico, e os gols estavam inflados por 2 gols contra e 3 erros. O cético refutou.
31. **Placar do evento que contradiz os incidentes e a tabela** (Alashkert x Syunik, 16/10).
    - Na R8, o Sofascore marcava Ararat 0-1 Syunik, mas o gol era do Ararat (Bakayoko, 77'), e a liga (FFA)
      registra Syunik 0-1 Ararat em Sisian (mando invertido).
    - O `defesa.py` leu o placar do evento e contou um jogo fora sem sofrer gol que não existiu: a média caiu
      de 2,67 para 2,29 e gerou um falso alerta de "defesa não tão fraca".
    - Antes de confiar na amostra, compare os gols da amostra com a tabela da condição.

## Resultados (preenchido pelo `previsoes.py resolver` + revisão)

| Data | Jogo | Pick | Prob. | Placar | Bateu? | Lição |
|---|---|---|---|---|---|---|
| 12/10 | Novorizontino x Ponte Preta | Novorizontino 2+ | 80% | 5-1 | ✅ | A Ponte teve 2 expulsões (62' e 88'), e o xG ficou em só 1,69 a 1,17: o placar exagerou o domínio. |
| 12/10 | Nacional x Recoleta | Nacional 1+ | 84% | 1-0 | ✅ | O mercado acertou em desconfiar do 2+ (regra 8): saiu só 1 gol. |
| 12/10 | PAOK x Kalamata (favoritos) | PAOK vence | 78% | 1-3 | ❌ | xG de 1,25 contra 2,36: o Kalamata mereceu. O PAOK estava **22 dias parado e com o goleiro titular fora**, e teve um expulso aos 62'. Pausa longa + goleiro reserva pede desconto maior que −1 p.p. |
| 12/10 | Always Ready x Ind. Petrolero (favoritos) | vence | 78% | 2-0 | ✅ | |
| 12/10 | Elfsborg x Halmstad (favoritos) | vence | 67% | 4-0 | ✅ | |
| 12/10 | Atalanta x Venezia (favoritos, no limite) | vence | 60% | 3-1 | ✅ | |
| 13/10 | Pakhtakor II x Aral | Aral 2+ (fora no Sofascore; mando real em Nukus) | 75% | 1-2 | ✅ | O Aral fez os 2 gols, apesar dos 22 dias sem jogo oficial. |
| 13/10 | IFK Norrköping x GIF Sundsvall | Norrköping 1+ | 83% | 4-0 | ✅ | A pausa longa do Norrköping (lição 10) não pesou desta vez. |
| 13/10 | Bashley x Christchurch | Bashley 2+ | 65% | 6-0 | ✅ | Liga amadora; a frequência real (67–70%) segurou a prob. abaixo dos 89% do modelo, e o placar passou longe. |
| 14/10 | Stocksbridge x Bridlington | Bridlington 1+ | 83% | 0-1 | ✅ | Liga amadora: o 1+ passou no limite (1 gol); fez bem não ir no 2+, que caiu no teste das médias gerais. |
| 14/10 | Nashville x Sporting KC | Nashville 2+ | 68% | 4-0 | ✅ | A defesa do SKC sem os zagueiros titulares confirmou a tese. O teste só com xG (64%) era conservador demais neste caso. |
| 15/10 | Real Estelí x ART Jalapa | Real Estelí 1+ | 80% | 1-1 | ✅ | Passou no limite (1 gol): fez bem rebaixar o 2+ (51% no teste das médias gerais, lição 20). |
| 16/10 | Livorno x Grosseto (azarão) | Grosseto ou empate | 65% | 4-4 | ✅ | O Grosseto forte no xG confirmou; jogo aberto (8 gols), não o "travado" que a tradição sugeria. |
| 16/10 | FC Alashkert x FC Syunik | Alashkert 2+ | 69% | 5-1 | ✅ | Corrigir o placar da R8 (lição 31) acertou a leitura: a defesa do Syunik era mesmo das piores fora. |
