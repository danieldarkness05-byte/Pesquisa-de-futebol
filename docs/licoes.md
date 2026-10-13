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

## Mercado (regra 8)

15. **Modelo mais de 10 p.p. acima do mercado:** quase sempre o mercado sabia algo.
    - Katowice: o modelo exagerava com 3 jogos de amostra.
    - Rancagua: viagem e chuva.
    - Nacional: odd subindo sem notícia.
    *(automático: λ implícito do 1X2 + over 2,5)*
16. **Odd que sobe contra o favorito sem notícia** (Nacional, de 1,53 para 1,67) é sinal de alerta.
    Procure escalação e desfalques antes.

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
