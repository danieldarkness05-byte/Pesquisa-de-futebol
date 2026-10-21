# Método Under

Método único do Daniel (21/10: "vamos criar um método só para under e nada mais"). Só "menos de X.5 gols".
A pesquisa **não depende do Sofascore**: todo número-chave é conferido em fonte independente, e o método roda
inteiro pela web quando o Sofascore cai (como em 21/10, com 403 o dia todo).

Comandos: **`/under`** (tudo que passa com 70%+) e **`/under-top`** (só a elite, no máximo 3).
Os dois usam o mesmo workflow, `.claude/workflows/under.js`.

## 1. As cinco perguntas do under

Um under só é bom quando as cinco respostas apontam para ele:

1. **Os times fazem poucos gols nesta condição?** Mandante em casa e visitante fora: gols, xG e % de under na linha.
2. **A cauda é limpa?** Nos últimos 7 oficiais e nos últimos jogos na condição, quantas vezes passou da linha
   (lições 33, 48 e 50).
3. **O confronto confirma, na linha exata?** H2H dos últimos 5 a 10 contados na linha do pick (lição 34).
4. **Algo abre o jogo hoje?** Zagueiro ou goleiro titular fora, time que precisa vencer, técnico novo ofensivo,
   favorito goleador, árbitro de pênalti ou expulsão, gramado.
5. **O mercado concorda?** Odd do under estável ou caindo desde a abertura, em mais de uma casa (lições 38 e 41).

## 2. Fluxo

| Passo | Quem | O que faz |
|---|---|---|
| 0. Aprender | script | `previsoes.py resolver` + `resumo`; lições novas em `docs/licoes.md` |
| 1. Mapa | script | `varredura.py --todas --prob-min 0.70` + `under.py --varrer` (Sofascore) |
| 1a. Conferência | script | `plataformas.py confere`: refaz cada under no 365Scores e marca CONFIRMADO ou DIVERGENTE |
| 1b. Mapa sem Sofascore | script | `plataformas.py mapa`: o mapa de unders inteiro pelo 365Scores |
| 1c. Mapa web | agente **descobridor** | só se o 365Scores também falhar |
| 2. Estatística independente | agente **estatístico** | números de fontes fora do Sofascore → `prob.py gols` → `p_independente` |
| 3. Contexto | agente **pesquisador** | escalação, desfalques, estilo, motivação, árbitro, clima, mercado |
| 4. Cético | agente **cético** | confere as afirmações-chave em outra fonte e tenta derrubar o under |
| 5. Veredito | workflow (código) | probabilidade, ajuste, selo elite e ranking |

Cada passo para quando o under morre: o estatístico derruba antes do pesquisador, e o pesquisador antes do cético.
Assim os agentes só gastam com quem ainda está vivo.

## 3. Probabilidade (regra 7: sai das ferramentas)

- `p_modelo`: varredura/Sofascore (Poisson/Dixon-Coles, 7 variantes, incerteza).
- `p_independente`: `python3 ferramentas/prob.py gols` rodado pelo estatístico com as médias de **outra fonte**
  (SoccerStats, FBref, FootyStats, 365Scores, Understat).
- `p_365`: a mesma conta com os números do **365Scores** (`plataformas.py`, de graça).
- **Base = a menor das três.** Se as duas diferirem em mais de 10 p.p., avise: alguma fonte está errada ou velha.
- Ajuste qualitativo: pesquisador + cético, no máximo ±5 p.p., com o motivo escrito.
- `p_final = base + ajuste`.

## 4. Fontes (todas as que existem, com cruzamento)

**Regra do cruzamento:** cada número que decide o pick (médias, cauda, H2H, desfalque) aparece em pelo menos
**2 fontes independentes**. Divergência vai para `divergencias` e pesa contra.

| Dado | Primeira | Cruzamento |
|---|---|---|
| Jogos do dia, hora, local | Sofascore | 365Scores (API abre por curl), FlashScore, FotMob, site da liga |
| Médias e % de under por condição | Sofascore | SoccerStats (abre por curl), FootyStats e FBref (WebFetch/busca) |
| xG | Sofascore | Understat (6 grandes ligas, abre por curl), FBref, FotMob |
| Cauda e últimos jogos | Sofascore | 365Scores (jogos recentes), FlashScore, Soccerway |
| H2H na linha | Sofascore | 365Scores (`web/games/h2h`), Betexplorer, FlashScore |
| Desfalques e escalação | Sofascore | Transfermarkt (abre por curl), site e redes do clube (X/Instagram), imprensa local |
| Árbitro | imprensa/federação | Transfermarkt (perfil do árbitro), WorldFootball |
| Odds e movimento das linhas | Sofascore (bet365) | Betexplorer e Oddsportal (abrem por curl), 365Scores |
| Clima | `clima.py` (Open-Meteo) | — |
| Contexto e notícias | WebSearch na língua local | sites dos clubes, imprensa local, entrevistas do técnico |

**Conferência automática:** `ferramentas/plataformas.py` lê do 365Scores a tabela casa/fora, os resultados de cada
time, o H2H e o estádio, os mesmos dados do Sofascore, e compara. A divergência derruba o selo elite.

**Bloqueadas por curl daqui** (21/10): FBref, FootyStats, WhoScored, Forebet, WorldFootball, ogol, zerozero, BeSoccer.
Tente WebFetch ou use o trecho do WebSearch. Sites de palpite (Forebet, etc.) só servem como contraprova, nunca
como fonte de número.

**365Scores** (sem chave; datas DD/MM/AAAA):
- jogos do dia com 1X2: `https://webws.365scores.com/web/games/allscores/?appTypeId=5&langId=31&timezoneName=America/Sao_Paulo&userCountryId=21&sports=1&startDate=D&endDate=D&showOdds=true`
- jogo: `.../web/game/?appTypeId=5&langId=31&timezoneName=America/Sao_Paulo&gameId=ID`
- H2H: `.../web/games/h2h/?appTypeId=5&langId=31&timezoneName=America/Sao_Paulo&gameId=ID`
- estatísticas: `.../web/game/stats/?appTypeId=5&langId=31&timezoneName=America/Sao_Paulo&games=ID`

**SoccerStats:** `https://www.soccerstats.com/latest.asp?league=<liga>` (tabelas casa/fora e over/under por time).

Use sempre um navegador no User-Agent do curl.

## 5. Selo elite (`/under-top`)

Ganha o selo quem cumpre **tudo**:

1. `p_final ≥ 80%`.
2. Cético não refutou, com confiança alta ou média; nenhuma pesquisa derrubou o pick.
3. Cauda: no máximo 1 estouro somando os dois times.
4. H2H na linha: no máximo 1 estouro nos últimos 5 (sem H2H, neutro).
5. Nenhum goleiro ou zagueiro titular **confirmado** fora; nenhum motivo de jogo aberto.
6. Mercado: até 8 p.p. acima da prob. sem margem; odd do under sem subir desde a abertura.
7. Fontes: Sofascore e 365Scores não divergem (`plataformas.py confere`); modelo e conta independente a até 10 p.p.;
   pelo menos 2 fontes fora do Sofascore (o 365Scores conta como uma).

**Ranking:** chance final → folga (linha − gols esperados) → cauda mais limpa → EV. Máximo 3.

## 6. Entrega e evolução

- Só under, sem odd na resposta (Regra 0). Odd, odd mínima e EV ficam no arquivo e no registro.
- Registro: `previsoes.py add-json`, com `analise` `under` (o `/under`) ou `under_top` (o `/under-top`).
- Cada resultado vira uma linha em `docs/licoes.md`. Lição que se repete vira filtro no `under.py` (com teste) ou
  regra do selo neste arquivo.
