# Cádiz x Sporting Gijón — LaLiga 2 (rodada 9) · /aprofundar do candidato 3

- **Data/hora:** 2026-10-11 16:00 (Brasília) · 21:00 em Cádiz
- **Local:** Nuevo Mirandilla (JP Financial Estadio), Cádiz
- **Chuva:** sem chuva (seco, peneira 07:54, clima.py/Open-Meteo)
- **Árbitro:** Saúl Ais Reig (Comitê Valenciano). Mercado de cartões não analisado.
- **Pick avaliado:** Dupla chance X2 (empate ou Sporting)

## Resultado

**Nenhuma oportunidade de ouro neste jogo. Descartado.**

| Mercado | Prob. | Odd mín. | Odd Betano | Odd bet365 | EV bet365 | Veredito |
|---|---|---|---|---|---|---|
| Dupla chance X2 | 60.1% (modelo 65.1% − 5 p.p.); só 26/27: 53–56% | 1.71 | N/D | 1.727 | +3.8% (só com o ajuste no teto) | DESCARTADO, evidência FRACA |

Chance estimada de dar X2: **cerca de 55%** (faixa de 53% a 60%). O mercado sem margem dá 53.8%.

Motivos do descarte:
1. Na reavaliação das 10:20, a própria peneira derrubou o pick pela **regra 8**: modelo 65.1% contra 53.8% do mercado (+11.3 p.p.).
2. O mercado sabe o que o modelo não vê: o Sporting tem **6 dos 8 gols da liga** marcados por jogadores fora ou em dúvida.
3. Mesmo com o ajuste máximo (−5 p.p.), o pick fica no limite: 60.1% (corte 60%) e odd mínima 1.71 (bet365 1.727).
4. Só com a temporada 26/27 (xG), o prob.py dá 55.5% sem os desfalques e 52.9% com eles. Os dois ficam abaixo de 60%.

## Movimento das odds (bet365 via Sofascore)

| | Abertura | Peneira 07:54 | 10:20 |
|---|---|---|---|
| 1 (Cádiz) | 2.50 | — | 2.01 |
| X | 3.10 | — | 3.10 |
| 2 (Sporting) | 2.65 | — | 4.00 |
| X2 | 1.50 | 1.70 | 1.727 |
| Prob. X2 sem margem (mercado de dupla chance) | 63.7% | 55.5% | 54.4% |

O Sporting abriu a 2.65 e foi a 4.00: o mercado reagiu forte às lesões.

## Dados usados (Sofascore, LaLiga 2, consultado 11/10)

| Estatística | Cádiz (casa, últ. 10) | Sporting (fora, últ. 10) | Fonte / recorte |
|---|---|---|---|
| V-E-D | 2-2-6 | 4-0-6 | Sofascore, últimos 10 na condição (04/04 a 03/10/2026) |
| Gols marcados | 1.10 | 1.30 | idem |
| Gols sofridos | 1.10 | 1.50 | idem |
| xG a favor | 1.14 | 1.17 | idem |
| xG contra | 1.46 | 1.44 | idem |
| Gols esperados (modelo da peneira) | 1.22 | 1.29 | varredura.py (mistura gols + xG, encolhida à média da liga) |
| Frequência de X2 nas amostras | 8/10 sem vitória do Cádiz | 4/10 sem derrota do Sporting | 12/20 = 60% |

**Atenção:** 7 dos 10 jogos de cada amostra são da temporada 25/26. Isso inclui a sequência de 6 derrotas do Cádiz em casa entre março e maio de 2026.

Temporada 26/27 (Sofascore):
- **Cádiz:** 20º, 7 pts, 1V 4E 3D, gols 11-10. Em casa, xG 1.44 a favor e 1.41 contra.
- **Sporting:** 8º, 13 pts, 4V 1E 3D, gols 8-8. Fora, xG 0.71 a favor e 1.34 contra, em 3 jogos (ganhou de 3-1 do Andorra com xG 0.51).

## Contexto

- **Desfalques do Sporting:**
  - Fora, CONFIRMADO (Sofascore + EFE/Infobae 10/10): Antonio Casas (artilheiro, 3 gols; posterior da coxa, volta prevista 30/11), Juan Otero, Nikita Iosifov, Konrad de la Fuente e Andrés Ferrari.
  - Duñabeitia (zagueiro titular, 1 gol): fora ou dúvida (EFE: desconforto, perdeu o treino de sábado; fórum: "descartado").
  - Nacho Martín e Loum: dúvidas, treinaram parcialmente.
  - Voltam: Gelabert (suspensão), Guillamón e Bruno Rubio. O ataque deve ser Sarco, que voltou de lesão, mais Gaspar Campos e garotos do Sporting Atlético.
  - Convocação oficial ainda não publicada (sai no domingo).
- **Desfalques do Cádiz:** Tabatadze (cruzado, CONFIRMADO), Gocholeishvili e Cristian Gutiérrez (lateral-esquerdo).
- **Momento:**
  - O Cádiz vem da 1ª vitória na temporada (4-0 no Leganés, o melhor jogo do ano), com a torcida animada. Está na zona de rebaixamento e precisa pontuar em casa.
  - O Sporting ganhou do Celta Fortuna por 3-2 e quer chegar ao G-6.
- **Técnicos:** Albert Celades (Cádiz) e Nicolás Larcamón (Sporting).
- **Ajuste aplicado:** −5 p.p. no X2, o teto da regra 7. Motivo: o Sporting perde quem fez 75% dos gols na liga e o zagueiro titular. O impacto real provavelmente é maior que o teto.
- **Sanidade com o mercado:** sem margem, o mercado dá 53.8% para X2. Sem ajuste, o modelo fica +11.3 p.p. acima (regra 8 acionada); com o ajuste, +6.3 p.p. O motivo da divergência foi encontrado (lesões) e vai contra o pick.

## O que mudaria o veredito

- Convocação com Duñabeitia, Nacho Martín e Otero, mais odd ≥ 1.85 no X2. Mesmo assim, a evidência continua fraca.

## Comandos rodados

```bash
python3 ferramentas/varredura.py --jogos 16418374 --curto   # 10:20 → "Fora: 1 regra 8"
python3 ferramentas/prob.py gols --xg-casa 1.223 --xg-fora 1.293 --rho 0 --mercados 1,X,2,X2 --odds "X2=1.727,1=2.01,X=3.10,2=4.00"
python3 ferramentas/prob.py gols --xg-casa 1.39 --xg-fora 1.06 --rho 0 --mercados 1,X,2,X2   # só 26/27 (xG)
python3 ferramentas/prob.py gols --xg-casa 1.39 --xg-fora 0.95 --rho 0 --mercados 1,X,2,X2   # só 26/27 + desfalques
python3 ferramentas/valor.py --prob 0.601 --odd 1.727 --mercado-odds 1.727,2.01
```

## Fontes

- Sofascore API (evento 16418374): odds bet365, lineups/ausências, classificação, artilheiros (incidents), consultado 11/10 10:20.
- EFE via Infobae, 10/10: https://www.infobae.com/espana/agencias/2026/10/10/el-cadiz-a-consolidar-el-resurgir-y-el-sporting-a-dar-el-salto-a-las-alturas/
- Andalucía Información, 10/10: https://www.andaluciainformacion.es/articulo/corazon-cadista/cadiz-sporting-que-pare-fiesta/202610101031213503149.html
- El Gol Digital (lesões do Sporting, semana anterior): https://www.elgoldigital.com/futbol/sporting-gijon/sporting-gijon-bajas-ataque-celta-fortuna-larcamon/
- Portal Sportinguista (fórum, 10/10, só para Duñabeitia): https://www.portalsportinguista.com/viewtopic.php?t=3012&p=814051

Dados pesquisados até 10:25 (Brasília).

---

# /aprofundar dos outros candidatos (1, 2, 4, 5, 6) · reavaliação às 10:28

## Resultado

⭐ **OURO (1):**

| # | Jogo | Hora | Mercado | Prob. | Odd mín. Betano | bet365 / EV | Stake | Evidência |
|---|---|---|---|---|---|---|---|---|
| 1 | Real Betis x Osasuna (LaLiga) | 13:30 | Menos de 4.5 gols | 86.6% | 1.19 | 1.20 / +3.9% | 2% da banca (teto) | MODERADA |

**Descartados:**
- **4) Motherwell x Celtic (08:00):** já tinha começado na hora do /aprofundar.
- **5) Teplice x Sigma Olomouc (10:00):** já tinha começado na hora do /aprofundar.
- **2) Concepción x La Calera, 1X:** caiu pela regra 8 na reavaliação (modelo 84.6% contra 73.7% do mercado). A pesquisa não achou o que o mercado sabe. Com o ajuste, dá cerca de 80%, sem margem de valor.
- **6) San Lorenzo x Riestra, menos de 8.5 escanteios:** 59.3%, abaixo do corte de 60%. O contexto não justifica ajuste para cima.

## 1) Real Betis x Osasuna · Menos de 4.5 gols · ⭐ OURO

- **Jogo:** 13:30 (Brasília), Estadio de la Cartuja, Sevilha. Sem chuva (peneira). Árbitro Carlos Muñiz Muñoz.
- **Modelo da peneira:** gols esperados Betis 1.66 × Osasuna 0.87 (total 2.53) → **88.6%**.
  - Variantes: 84.6% a 90.1%.
  - Frequência nas amostras: 18/20 (Betis em casa 10/10, Osasuna fora 8/10). Sofascore, últimos 10 na condição.
- **Ajuste:** −2 p.p. → **86.6%**.
  - Contra o under: o Betis está sem os dois laterais (Firpo e Ruibal), e o Osasuna sofreu 13 gols nos últimos 6 jogos (Herrando e Del Castillo fora).
  - A favor do under: o ataque do Osasuna está sem Oroz, Barja e Moro (6 gols em 7 jogos; 1 ponto em 12 sem Oroz).
- **Mercado:**
  - Sem margem, dá 78.9% → nosso número fica +7.7 p.p. acima (regra 8 ok).
  - Contra nós: desde a abertura, o mercado foi para mais gols (under 4.5 de 1.143 para 1.20; sem margem, de 82.8% para 78.9%).
  - A média da LaLiga 26/27 é 2.89 gols por jogo, com 80.5% dos jogos em até 4 gols (n = 133).
- **A favor:** nenhum dos últimos 6 confrontos passou de 3 gols. 3 dos últimos 6 jogos do Betis foram 1-0. O Betis joga a Champions na quarta (Porto) e pode rodar o time.
- **Contra:** é o 1º jogo depois da data FIFA. O Betis levou 5-2 do Levante. O Osasuna levou 5-2 do Alavés e 4-0 do Atlético fora.
- **Por que MODERADA:** o pick é robusto no modelo e nas amostras, mas a odd é baixa e a margem é fina (odd mínima 1.19 contra bet365 1.20), e o mercado vem se movendo contra.
- **Conferir antes de entrar:**
  - Odd Betano ≥ 1.19; se for 1.18 ou menos, não entre.
  - Escalações oficiais por volta das 12:30.

## 2) Deportes Concepción x Unión La Calera · 1X · DESCARTADO

- **Modelo:** 1.72 × 0.72 gols esperados → 84.6%. Frequência nas amostras: 16/20.
- **Mercado:** sem margem, 73.7% (1X 1.286; 1 1.96, X 3.40, 2 3.60) → +10.9 p.p.: regra 8 acionada.
- **Pesquisa (imprensa chilena):** nenhum desfalque relevante no Concepción. Saldías, da La Calera, está fora desde março por embolia pulmonar; Caseres é só rumor.
- **Contra o pick:**
  - O Concepción vem abalado: eliminado da Copa Chile pelo O'Higgins (0-1 e 0-2), crise interna com a diretoria e 3 jogos sem vencer.
  - A La Calera tem técnico novo (John Armijo, desde 14/09) e chega descansada, sem jogar desde 26/09.
  - Ela está em último por causa de −6 pontos de punição (mantida pelo TAS) e ganhou o jogo do 1º turno por 1-0.
- **Com o ajuste (−4 p.p.):** 80.6%, EV +3.7% a 1.286 e odd mínima 1.28. Fica no fio da navalha, e o motivo da divergência com o mercado não foi encontrado. Chance estimada: cerca de 80% (faixa 74–85%).

## 6) San Lorenzo x Deportivo Riestra · Menos de 8.5 escanteios · DESCARTADO

- **Modelo:** média esperada de cerca de 8.0 escanteios → 59.3%, abaixo do corte final de 60%. EV +6.7% a 1.80. Sem margem, o mercado dá 51.5%.
- **Amostras:** 11/20 jogos abaixo de 8.5 (San Lorenzo em casa 5/10, Riestra fora 6/10).
- **Contexto:**
  - O San Lorenzo escalou 3 atacantes e precisa vencer (Insúa fez 1 de 9 pontos, 12º na zona). Isso puxa para mais escanteios, não para menos.
  - O Riestra está em 28º na tabela anual, brigando contra o rebaixamento.
  - Sem chuva prevista; árbitro Bruno Amiconi.
- Nada justifica ajuste para cima, e rebaixar o corte seria forçar. Chance estimada: cerca de 57–59%.

## Fontes (outros candidatos)

- Sofascore API (eventos 16421054, 15353146 e 16667358): odds bet365, amostras, desfalques e classificação, consultado 11/10 10:28.
- **Betis:**
  - https://www.comuniate.com/noticias/38336/onces-probables-del-betis-osasuna-segun-la-prensa-deportiva-especializada
  - https://comuniate.com/noticias/38371/aimar-oroz-sera-baja-para-el-partido-ante-el-betis
  - https://www.elgoldigital.com/futbol/real-betis-balompie/pellegrini-internacionales-betis-osasuna-firpo-ruibal-fidalgo/
  - https://www.sportsmole.co.uk/football/betis/preview/betis-vs-osasuna-prediction-team-news-lineups_606591.html
- **Concepción:**
  - https://www.alairelibre.cl/futbol/concepcion-vs-union-la-calera-formaciones-horario-canal-campeonato-nacional-2026/
  - https://www.alairelibre.cl/futbol/campeonato-nacional/union-la-calera-john-armijo-nuevo-dt/
  - https://www.emol.com/noticias/Deportes/2026/09/30/1212857/lacalera-tas-resta-puntos-anfp.html
- **San Lorenzo:**
  - https://vamosciclon.com/san-lorenzo-equipo-confirmado-cuatro-cambios-riestra/
  - https://www.lanacion.com.ar/deportes/futbol/a-que-hora-juega-san-lorenzo-y-deportivo-riestra-y-por-donde-se-puede-ver-en-vivo-nid11102026/
  - https://elintransigente.com/2026/10/san-lorenzo-arbitro-riestra/

Dados pesquisados até 10:36 (Brasília).

## Segunda opinião no Betis (workflow `aprofundar`, 11:00)

- **Ajuste:** pesquisador −1 p.p. e cético −1.5 p.p. → **86.2%**. EV +3.4% a 1.20, com **odd mínima 1.20** (antes, 1.19).
- **Cético (Sports Mole 11/10):** não refutou. Confirmou que o Osasuna está sem Herrando, Moro e Del Castillo, mas as fontes divergem sobre Oroz (Comuniate: fora; Sports Mole: volta).
- **Veredito:** continua ⭐ OURO marginal. Só entre com odd Betano ≥ 1.20, depois da escalação oficial.

---

# Reavaliação das 12:11 (peneira com o calendário corrigido: 70 jogos ainda por começar)

- **Bug corrigido:** a peneira listava jogos que já tinham começado, porque usava o calendário da manhã guardado no cache. Agora consulta na hora.
- **Candidatos:** Betis −4.5 (já aprofundado acima, ⭐ OURO marginal, odd mín 1.20), San Lorenzo −8.5 escanteios (59,3%, fora) e um novo, Real Potosí x The Strongest 1X.

## Real Potosí x The Strongest · Dupla chance 1X · DESCARTADO

- **Jogo:** 16:00 (Brasília), Estádio Víctor Agustín Ugarte, Potosí (~4.000 m). Sem chuva (clima.py: 0%).
- **Modelo:** 72,5% (variantes de 70% a 79%; sem xG suficiente na Bolívia). Frequência nas amostras: 12/20 = 60%.
  - Real Potosí em casa: 5V 3E 2D. The Strongest fora: 6V 3E 1D.
- **Mercado:** 1X a 1.50 e "2" a 2.45. Sem margem, 62,0%, então o modelo fica +10,5 p.p. acima (regra 8).
- **Pesquisa (Diez, Erbol, RSSSF, 11/10):**
  - The Strongest: 5 vitórias seguidas na liga, **elenco completo** (Erbol), 3º com 42 pts, a 3 da liderança, na briga pelo título. Técnico Zago desde agosto.
  - Real Potosí: 5º com 32 pts, briga por Sul-Americana. Técnico Umaña desde setembro.
  - Retrospecto: The Strongest 10V e 1E em 11 jogos; o Real Potosí nunca venceu.
  - Nenhum desfalque relevante reportado. Nenhum dos dois tem Copa no meio da semana (as quartas são em 21/10).
- **Ajuste: −5 p.p.** (teto). Motivos: forma e elenco completo do The Strongest, motivação de título, retrospecto 10-1-0 e frequência real de só 60%. Fica **67,5%**, EV +1,3% a 1.50, odd mínima 1.53 → **sem valor**.
- A divergência com o mercado foi explicada, e a explicação vai contra o pick.

Dados pesquisados até 12:20 (Brasília).
