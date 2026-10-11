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
