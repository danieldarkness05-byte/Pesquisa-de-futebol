# Defesa fraca x ataque forte — 19/10/2026

**Resultado: nenhum jogo passou.** O cético refutou os 4 pesquisados.

Critério: azarão com defesa muito vazada na condição (índice ≥ 1,4) e favorito com ataque forte (≥ 1,15),
favorito com 7+ pontos nos últimos 5 oficiais, prob. ≥ 60% depois do ajuste, cético sem refutar. Chuva só informativa.
Triagem (`defesa.py`, 07:00): 615 jogos não iniciados, 150 com tabela e amostra, 17 na triagem, 12 aprofundados,
6 com mercado ≥ 60% (4 profissionais pesquisados; Tammeka U21 e Sarpsborg II são base/amador e ficaram fora).
Workflow `defesa.js`: 8 agentes (4 pesquisadores + 4 céticos).

| Jogo | Hora | Azarão (sofre/j na condição · xG cedido) | Melhor mercado | Veredito |
|---|---|---|---|---|
| RFS x FK Tukums 2000 (Letônia) | 13:00 | 2,47 · xG 1,64 (×1,12 da liga) | RFS 1+ ~92% | refutado; mercado 96,5%, sem valor |
| Hapoel Kfar Shelem x Hapoel Acre (Israel, 2ª) | 13:00 | 2,75 · xG 1,58 (= média) | Kfar Shelem 1+ ~87% | refutado; mercado 86,9%, sem valor |
| Bursaspor x Pendikspor (Turquia, 1. Lig) | 14:00 | 2,60 · xG 1,31–1,36 (13º de 20) | Bursaspor 1+ ~80% | refutado; mercado 87,6%, sem valor |
| Encarnación x General Caballero (Paraguai, Intermedia) | 16:30 | 1,93 · xG 1,13–1,31 (7º de 16) | Gral. Caballero 1+ ~75% | refutado; mercado 84%, sem valor |

## Notas

- **RFS x Tukums:** o RFS briga pelo título (80 pts contra 79 do Riga FC) e não vai poupar. Mas o Tukums só é
  muito vazado em gols fora: o xG cedido é mediano (mediana ajustada pelo adversário de 0,95), com gols contra,
  2 expulsões e 2,47 sofridos com 1,64 de xG. No teste só com xG, o RFS 3+ dá 47–52% e o 2+ dá 72–76%, abaixo do
  mercado. Em casa, o Tukums cede mais xG e sofre menos gols: o recorte é ruído (lição 51). O goleiro titular
  Vilkovs ficou fora dos últimos 2 jogos (motivo N/D).
- **Kfar Shelem x Acre:** a defesa do Acre só é a pior em gols por causa de 2 goleadas com o elenco antigo. No xG
  fora ela é mediana (1,58, igual à média da liga) e melhorou com os reforços (1,2 sofrido por jogo nos últimos 5).
  O Beit Yaakov já cumpriu a suspensão (lição 52).
- **Bursaspor x Pendikspor:** os gols sofridos pelo Pendik estão inflados por 2 expulsões e por finalização dos
  adversários. Pelo xG ele cede 0,99 do habitual dos rivais. O Bursaspor marcou em 10 de 10 em casa, mas o 1+
  (~80%) fica abaixo do mercado (87,6%).
- **Encarnación x General Caballero:** pior defesa da liga em casa (27 gols com 18,4 de xG) e 4ª melhor fora; no
  total, 40 gols com 42,0 de xG. Divisão casa/fora sem respaldo no xG (lição 51).

## Evolução

- **`defesa.py`:** com 5+ jogos na condição, xG cedido abaixo da média de gols da liga agora tira o jogo, como a
  lição 22 faz com os gols (com teste). Hoje isso teria poupado 2 pesquisas (Pendik ×0,96 e Encarnación ×0,88).
  Nashville (14/10, acertou 4-0, ×1,00) continua passando.
- Lições 51 a 53 em `docs/licoes.md`.

Fontes: Sofascore (tabelas, amostras, xG, odds bet365, escalações e incidentes); FotMob e Starting11 (data do RFS);
Wikipedia (Virslīga 2026); Sport5 (amarelos em Israel); imprensa turca e paraguaia citada pelos agentes; Open-Meteo.
Até agora (defesa): 12/13 acertos (92%) para 77% previsto.
Dados pesquisados até 07:30.
