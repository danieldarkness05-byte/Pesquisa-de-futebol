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

## Mercados de 70%+ (/setenta)

32. **Abertura de temporada: o modelo ainda olha a temporada passada** (Central Coast x Newcastle, A-League, 17/10).
    - A amostra de 10 jogos na condição era toda de 2025/26. O Mariners teve 13 saídas e técnico novo, e o Jets
      sofreu 10 gols em 2 jogos da Champions da Ásia. O under 4.5 caiu de 79% para 75%, sem valor.
    - Nas primeiras rodadas, confira quantos jogos da amostra são da temporada atual e pese as mudanças de elenco.
    - *Candidato a automático:* alerta "amostra da temporada passada" quando a maioria dos jogos for de outra temporada.
33. **Under alto contra favorito goleador: olhe a cauda** (Telstar x Feyenoord, 17/10).
    - O Feyenoord passou de 4,5 gols em 5 dos últimos 7 oficiais (7-0, 5-0, 5-2, 1-5, 3-2). Um under 4.5 de 75%
      depende quase só do favorito não golear, e o mercado (66%) já precificava isso.
    - Antes de um under 4.5 ou 5.5, conte em quantos dos últimos 7 jogos (todas as competições) o favorito sozinho
      faria a linha cair.
34. **Estatística citada tem que ser da mesma linha do mercado** (Hamburgo x Stuttgart, 17/10).
    - "12 jogos seguidos com 2+ gols" não sustenta um over 2.5, que pede 3+. O cético pegou e tirou −2 p.p.
    - Gols sofridos que vêm de duas goleadas (dois 0-5 do HSV) também não sustentam over sozinhos (lição 1).

35. **Confronto extremo infla o λ multiplicativo** (FC Sevastopol x Neftyanik, 17/10).
    - Com a defesa do azarão a 2x ou mais da média da liga (índice 2,18), o λ foi a 4,0, mas o Sevastopol
      nunca tinha marcado mais de 3 em casa (3+ em só 2 de 12).
    - O λ implícito do mercado (2,18) ficou perto da média do favorito em casa (1,83), não do produto.
    - Com índice de defesa acima de 2, faça o teste de chão com a média geométrica entre os gols do favorito
      na condição e os sofridos pelo azarão (aqui λ 2,47, 2+ ≈ 71%), e confira o teto de gols do favorito.
36. **Defesa que desmorona no meio da temporada** (IK Uppsala x Kristianstads, 17/10).
    - Saída de técnico, titulares vendidos ou clube em crise: o teto de frequência dos últimos 10 mistura o
      elenco antigo com o atual e fica baixo demais.
    - Use a frequência de "sofreu 2+" só depois do desmonte. Confira também se o período antigo tinha gols bem
      abaixo do xG cedido: no Uppsala, o xG cedido em casa ia de 2,3 a 3,3, mas foram só 6 gols em 5 jogos.
    - É a lição 2 ao contrário: o alerta automático "defesa melhorando" não pega a piora.
37. **"Defesa melhorando" por blocos, ajustada pelo adversário** (Champs x Fraijanes, 17/10).
    - Some os gols sofridos e os esperados pelos adversários (média de cada um na condição, sem o próprio
      jogo) em blocos consecutivos, em vez de olhar só os últimos 5.
    - O Champs teve uma melhora real de R9 a R13 (0,52x) e recaiu de R14 a R16 (1,56x, já eliminado).
    - Trecho bom no meio que não se sustenta nos últimos 3 não é melhora estrutural; vale a temporada ajustada.
38. **Over com a odd subindo desde a abertura e sem notícia: o mercado sabia** (Hamburgo x Stuttgart, 17/10: 1-0).
    - O over 2.5 foi de 1.364 para 1.40 enquanto o 1X2 se mexia. Com o ataque do mandante desfalcado (Daka) e
      sem marcar em 3 de 5, a evidência era MODERADA justamente por esse ponto fraco, e o pick perdeu.
    - Em overs (e unders), odd do pick subindo desde a abertura conta como ponto fraco forte: com mais um ponto
      fraco, sai. Mesma ideia da lição 16, agora para gols.

## Under (/under)

39. **Under: o valor tem que sobreviver ao teste só com o xG DESTA temporada** (Lyngby, Pohang e Odense, 18/10).
    - Nos três, o modelo de gols ficava 6 a 10 p.p. acima do mercado porque um time (ou os dois) finalizava muito
      abaixo do xG: o FCN fez 14 gols com 23,3 de xG; o Pohang, 5 com 13,4 em casa ("13 de 13 abaixo de 3.5").
    - Com o xG da temporada atual na condição, o under caía para o nível do mercado (73–77%), e o valor sumia.
    - Sequência longa abaixo da linha só vale se o xG somado dos mesmos jogos também for baixo.
    *(automático: `under_xg_atual` no `under.py` — sai se ficar a menos de 2 p.p. do mercado ou se o EV ficar negativo)*
40. **Tabelas casa/fora com gols de disputa de pênaltis** (Iwaki x Kofu, J2 2026, 18/10).
    - Na temporada especial da J.League 2026, as tabelas casa e fora do Sofascore somam os gols das disputas de
      pênaltis (1.031 gols contra 925 na tabela total). A média da liga ficava ~11% alta e todo λ caía: um viés de
      under de ~2 p.p. nas ligas japonesas.
    *(automático: `fator_tabelas` no `varredura.medias_liga` reescala quando casa + fora passa da total em 3%+)*
41. **Movimento de odd em gols: confira as linhas vizinhas e a abertura** (Odense, Salzburg e Pérez Zeledón, 18/10).
    - A abertura do Sofascore às vezes é de outra linha, ou vem defeituosa: no OB x Brøndby, o "over 2.5 de 2.15
      para 1.60" vinha de uma abertura incoerente com o over 3.5. Só vale o movimento na mesma direção em várias linhas.
    - Dispersão: se os overs da cauda (4.5, 5.5) encurtam desde a abertura, o mercado está tirando chance do under
      3.5/4.5, mesmo com a média estável.
42. **Under curto (odd ≤ 1.30): a divisão proporcional subestima o under no mercado** (Salzburg x Altach, 18/10).
    - A casa põe mais margem no over. A 1.25/3.75, a divisão proporcional dá 75%, e o método da potência, ~78%.
    - Na regra 8 e na distância modelo x mercado, considere o método da potência. *Candidato a automático.*

43. **Mando só no papel em liga de estádio compartilhado** (Rancho Santana x Diriangén, Nicarágua, 18/10).
    - Quando o jogo é no estádio que o favorito usa como casa, o recorte "favorito fora x azarão em casa" não
      mede o mando. Nessa liga, o visitante marca mais que o mandante (1,64 contra 1,27).
    - Use as médias gerais e confira o que o favorito fez naquele estádio: o Diriangén fez 2,43 por jogo fora,
      mas só 1,5 no Estadio Nacional, onde é o jogo.
44. **Grupo da tabela com o ano no nome** (Academia Puerto Cabello x Monagas, 18/10).
    - O grupo "Primera Division 2026, Clausura" não estava contido em "Primera Division, Clausura", e o
      `defesa.py` pegou o Apertura (mais jogos). A defesa mediana do Monagas (1,67 fora) virou a 2ª pior (2,17).
    - *(automático: `escolher_grupo` compara a fase sem o ano — Apertura/Clausura/Finalización; com teste)*
45. **A estreia do técnico novo conta como período antigo** (Santa Cruz x Antofagasta, 18/10).
    - Na estreia, o Giovagnoli perdeu de 2-3 com 3,11 de xG cedido (2,9x o habitual do rival).
    - Quando o alerta "defesa melhorando" dispara e os últimos 5 na condição estão na média da liga em gols e
      no xG ajustado pelo adversário, aplique a lição 22: a tese de defesa fraca cai, mesmo que os últimos 10
      (com o técnico anterior) passem no corte.

46. **Teste de chão com xG pela metade quando falta o xG do favorito** (Belgrano x River, 18/10).
    - O `azarao.py` pula a variante xG se um dos lados não tem xG; o River não tinha, e o mínimo ficou só com gols.
    - Trocar só os números do azarão pelo xG dele (1,00 cedido em casa, contra 0,70 de gols sofridos) derrubou o 1X
      de 68% para 56%, igual ao mercado: os 8 p.p. de vantagem eram sorte defensiva do Belgrano.
    - Na rotina da tarde, confira antes no `analises/<data>-ouro.md` da manhã: o mesmo jogo já tinha sido descartado
      (mando no Kempes com torcida do River). Sem mudança a favor (odd, escalação), não gaste agentes de novo.
    - *Candidato a automático:* variante xG parcial no `azarao.py` (xG do lado que tem, gols do outro).

47. **Teste só xG com poucos jogos desta temporada: rode com 3 e com a média geral** (Wisła Płock x Radomiak, 19/10).
    - O teste da lição 39 não rodou porque a Wisła tinha só 3 jogos em casa (um adiado). Feito à mão: 77% na
      condição e 73% no geral, contra 78–81% do mercado; o modelo dava 86% com 65% da amostra de 2025/26 e
      técnicos diferentes nos dois times. Confira também se o xG cedido vem de um jogo extremo (use a mediana).
    *(automático: `under_xg_atual` tenta com 3 jogos por lado quando não há 4)*
48. **"Cauda limpa" encostada na linha** (Parma x Torino, 19/10).
    - 0 de 7 acima de 3.5 nos dois times, mas 7 de 14 jogos com exatamente 3 gols, e a Serie A 2026/27 mais aberta
      (70,6% de under 3.5, contra 75% da taxa histórica do requisito).
    - Cauda limpa com muitos jogos no limite não é folga: puxe o under para a média real de gols da temporada.
    *(automático: alerta "jogos com exatamente X gols" no `under.py`)*
49. **Linha alta (5.5): o Poisson ignora a dispersão** (Jong Ajax x De Graafschap, 19/10).
    - Time B que alterna 0-0 com 6-1: totais com média 3,8 e variância 9,1. A binomial negativa com média e
      variância da temporada atual deu ~80% para o under 5.5, contra 84,6% do modelo e ~78–81% do mercado.
    *(automático: `under_dispersao` — com variância > 1,3 × a média nos últimos 14 totais, refaz pela binomial
    negativa e sai se ficar perto do mercado)*

50. **Cauda na condição, não só a mista** (Waterford x Galway, 19/10).
    - A cauda dos últimos 7 oficiais (casa e fora, todas as competições) deu 1 de 7 e só 2 de 14 com exatamente
      4 gols. Mas nos últimos 10 do Waterford em casa pela liga foram 4 jogos de exatamente 4 gols e 1 de 6, com
      média 3,2 (a média da temporada em casa, 2,63, vinha de um início travado).
    - Confira a cauda e os jogos no limite também na condição do jogo (mandante em casa, visitante fora).
    *(automático: `cauda_amostra` no `under.py` — falha pela cauda na condição e alerta de jogos no limite)*

## Defesa fraca (19/10)

51. **Defesa fraca só nos gols, mediana no xG** (Tukums, Pendikspor e Encarnación, 19/10; antes, Monagas, 18/10).
    - Os três azarões sofriam muito mais que o xG cedido: Tukums 2,8 com 1,75; Pendik 1,9 com 1,31;
      Encarnación 1,7 com 1,13. O cético refutou os três, e os gols vinham de gols contra, expulsões e finalização.
    - Confira o outro recorte. O Tukums cedia MAIS xG em casa (1,80) e sofria MENOS gols (1,53). O Encarnación
      sofreu 27 gols em casa (pior) com 18,4 de xG e 13 fora (4ª melhor) com 23,6; no total, 40 gols com 42,0 de xG.
      Quando o xG não acompanha a divisão dos gols, o recorte casa/fora é ruído: use os números gerais.
    - *(automático: com 5+ jogos na condição, xG cedido abaixo da média de gols da liga tira o jogo, como a lição 22
      faz com os gols; teste com Pendik e com Nashville, que acertou com ×1,00 e continua.)*
    - Entre ×1,0 e ×1,2 (Tukums, ×1,07) o jogo ainda vai ao workflow: o cético decide com o xG ajustado pelo
      adversário (lição 30).
52. **Suspensão por amarelos em liga pequena** (Kfar Shalem x Acre, 19/10).
    - Lista de desfalques vazia no Sofascore não exclui suspensão. Antes de dar o artilheiro como titular, conte os
      amarelos nos incidentes e confira o acumulado no site da liga ou na imprensa (o Sport5 lista o acumulado).
    - Jogador que ficou fora logo depois de um amarelo provavelmente já cumpriu a suspensão.
53. **xG individual parcial em liga menor** (Bursaspor x Pendikspor, 19/10).
    - Na 1. Lig turca, o xG por jogador vinha zerado em 5 dos 10 jogos: a soma dava 12,2, contra 19,3 do time.
    - Antes de aplicar a lição 7 a um jogador, compare a soma do xG dos jogadores com o xG do time. Se ficar bem
      abaixo, conte os gols só dos jogos que têm xG individual.

## Defesa fraca (20/10)

54. **Mercado só com 1X2: refaça o λ pelo método da potência** (Uxbridge x Malvern, 20/10).
    - Em liga amadora (margem ~11%), a divisão proporcional joga a margem no empate e no azarão e subestima o
      favorito e o total de gols. No Uxbridge, o λ implícito foi de 1,99 para 2,19: o 2+ do mercado subiu de 59%
      para 64% e o 1+ de 86% para 89%.
    - Antes de medir a regra 8 num mercado de gols sem linha de over/under, refaça o λ: a distância no 2+ cai
      uns 5 p.p., e a vantagem que parecia existir no 1+ pode sumir.
55. **Uma goleada isolada numa amostra curta passa pelo alerta da mediana** (Taunton x Bracknell, 20/10).
    - Fora, o Bracknell sofreu 7, 2, 2, 2, 1 e 1: média 2,5 (4ª pior), mediana 2. O alerta "média inflada" não
      dispara, mas o 0-7 da estreia, com o elenco ainda em montagem, decidia a triagem (índice 1,41 contra corte de 1,38).
    - Sem esse jogo: 1,6 por jogo (×0,90), na média da liga. O elenco ainda foi reformulado em 13/10.
    - Mesma família das lições 1 e 22 e do Acre (19/10, 2 goleadas com o elenco antigo).
      *(automático: `ga_aparada` no `defesa.py` — sem a pior goleada, defesa na média ou melhor tira o jogo; com teste.
      Nos candidatos de 14 a 20/10 só o Bracknell sairia; nenhum acerto cortado.)*

## Mapa de 70%+ (/setenta e /under, 21/10)

56. **O ajuste vai do modelo até a leitura honesta** (Reading x Leyton Orient, 21/10).
    - O pesquisador escreveu que o under honesto era de 81–82%, mas deu +1 p.p. em cima dos 85% do modelo (o p final
      iria a 86%). Se a leitura honesta (xG da temporada, gols reais na condição e mercado pelo método da potência)
      fica abaixo do modelo, o ajuste é negativo até chegar nela.
    *(nos prompts do `under.js` e do `aprofundar.js`)*
    - Confira também a deriva das linhas pelo handicap asiático do favorito e pelo "marca primeiro": se tudo vai na
      mesma direção (mais gols), é o mercado sabendo algo (lições 38 e 41).
57. **Razão gols/xG da liga: compare com as temporadas anteriores antes de escalar** (Omiya x Toyama, J2, 21/10).
    - Na J2 2026/27 a razão é 0,857 em 110 jogos, mas foi 0,92 em 2025 e 0,99 na especial 2026. Reduzir o xG pela razão
      atual favorece o under; encolhida para o histórico (~0,91), o under 4.5 caiu de 77,7% para ~73,5%, abaixo do
      mercado.
    - "Melhores defesas em gols sofridos" com xG cedido na média, contra os 2 melhores ataques em xG, não é "topo
      contra topo trava" (a lição 11 não vale para times de posse e volume).
58. **Dupla chance 12 com o λ do mandante inflado** (Levante x Athletic, 21/10).
    - O modelo dava 2,32 gols ao Levante (17º, 12 gols na liga) e o fazia favorito com 62%. O mercado, pelo método da
      potência, punha o Athletic como favorito; com qualquer λ realista, a 12 ficava em 72–75%, sem valor a 1.286.
    - Antes de uma 12 ou de uma vitória, compare o λ de cada time com os gols reais dele na temporada (lição 39 para
      o resultado).

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
| 17/10 | Carrarese x Modena (/setenta) | menos de 3.5 | 78% | 2-1 | ✅ | Os 11 de 12 jogos dos dois abaixo de 3.5 na temporada e os técnicos esperando jogo travado bateram. |
| 17/10 | Hamburgo x Stuttgart (/setenta) | mais de 2.5 | 75% | 1-0 | ❌ | Os riscos do cético se confirmaram: HSV sem Daka (não marcou em 3 de 5) e odd do over subindo desde a abertura. Lição 38. |
| 17/10 | Stenhousemuir x Raith (/setenta) | menos de 3.5 | 85% | 1-1 | ✅ | Duas defesas menos vazadas da liga: o under mais seguro do dia, mesmo com valor no limite. |
| 17/10 | FC Sevastopol x Neftyanik | Sevastopol 1+ | 92% | 2-2 | ✅ | Rebaixar do 2+ para o 1+ (lição 35) foi certo: o campeão relaxou e saiu 2-2. |
| 17/10 | IK Uppsala x Kristianstads | Kristianstads 2+ | 68% | 0-5 | ✅ | A defesa desmontada do Uppsala (lição 36) confirmou: 5-0 fora. |
| 18/10 | Odense x Brøndby (/under) | menos de 4.5 | 82% | 2-1 | ✅ | Linha alta com folga: 3 gols, longe do limite. |
| 18/10 | Red Bull Salzburg x Altach (ouro) | menos de 4.5 | 81% | 3-0 | ✅ | O Salzburg goleador fez 3, mas o Altach não marcou: a cauda de 5+ não veio. |
| 17/10 | Champs Academy x Fraijanes | Fraijanes 1+ | 82% | 1-3 | ✅ | |
| 18/10 | Pérez Zeledón x Herediano (/under) | menos de 3.5 | 76% | 0-3 | ✅ | No limite (3 gols): o Herediano marcou os 3; os dois ataques mais fracos da liga seguraram o total. |
| 18/10 | Rancho Santana x Diriangén | Diriangén 2+ | 68% | 0-1 | ❌ | Os dois alertas do cético bateram: no Estadio Nacional ele faz 1,5/j (lição 43) e os gols fora estavam acima do xG. Com o recorte do estádio e o xG, o 2+ não chegava a 60%. |
| 19/10 | Parma x Torino (/under) | menos de 3.5 | 80% | 0-3 | ✅ | No limite (3 gols), todos do Torino. |
| 19/10 | Jong Ajax x De Graafschap (/under) | menos de 5.5 | 82% | 2-1 | ✅ | Linha alta com folga. |
| 19/10 | Waterford x Galway (/under) | menos de 4.5 | 77% | 3-2 | ❌ | A cauda na condição avisou (lição 50): o Waterford em casa tinha 5 de 10 com 4+ gols e precisava vencer. Modelo igual ao mercado, sem valor: não era pick de ouro. |
| 20/10 | Uxbridge x Malvern Town | Uxbridge 1+ | 89% | 3-0 | ✅ | A pior defesa fora confirmou, mesmo com o ataque desfalcado; rebaixar o 2+ pela regra 8 (lição 54) foi conservador, mas o 1+ era a leitura certa. |
| 21/10 | Reading x Leyton Orient (/fortes) | menos de 4.5 | 81% | 1-0 | ✅ | Linha alta com folga, mesmo com o mercado indo para gols e o Reading com 7 e 5 gols em casa. |
| 21/10 | Omiya x Toyama (/setenta) | menos de 4.5 | 75% | 0-3 | ✅ | Os 2 melhores ataques da J2 fizeram 3, no limite da linha 3.5 e longe da 4.5: a linha alta salvou (lição 57). |
| 21/10 | Nagoya x Cerezo (/setenta) | Nagoya 1X | 76% | 1-1 | ✅ | O empate serviu; o Cerezo sem os 2 suspensos não venceu. |
| 21/10 | FC Tokyo x Kashiwa (/setenta) | mais de 1.5 | 84% | 0-0 | ❌ | O alerta estava escrito: o FC Tokyo vinha de 5 jogos sem sofrer gol. Over de gols contra defesa em sequência de jogos limpos pede o xG cedido, não a média de gols. |
| 21/10 | Avispa x Gamba (/setenta) | mais de 1.5 | 77% | 1-2 | ✅ | Odd do over subindo (lição 38), mas o jogo de 6 pontos abriu. |
| 21/10 | Kyoto x Kashima (/setenta) | 12 | 78% | 2-2 | ❌ | O cético já tinha refutado pelo valor; o Kyoto com 1 gol em 4 jogos marcou 2 e mesmo assim empatou. Na J1, 12 a 78% tinha pouca folga. |
| 21/10 | Levante x Athletic (/setenta) | 12 | 74% | 3-1 | ✅ | Bateu com o Levante vencendo, apesar do λ inflado (lição 58). |
