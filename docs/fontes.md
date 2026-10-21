# Fontes de dados

> **Under:** a tabela completa de fontes, o cruzamento obrigatório e o que abre ou é bloqueado daqui estão em
> `docs/metodo-under.md` (seção 4).

Ordem de preferência. Sempre registre de onde veio cada número e o recorte
(temporada, últimos N jogos, casa/fora).

| Fonte | Bom para | Observação |
|---|---|---|
| **Sofascore** (sofascore.com) | estatísticas por jogo e por time, escalações, árbitro, notas | **Preferida do Daniel — tente primeiro.** As páginas carregam via JavaScript; se o WebFetch vier vazio, busque "sofascore <time> estatísticas" ou passe para a próxima fonte |
| FootyStats (footystats.org) | médias de escanteios, cartões, over/under, BTTS por time e por árbitro | bom para mercados de nicho |
| FBref (fbref.com) | chutes, chutes no alvo, xG | cobre Série A/B e Libertadores |
| ogol.com.br | resultados, elencos, Série C e Copa do Nordeste | útil quando faltam estatísticas avançadas |
| ge.globo.com | escalação provável, desfalques, notícias, gramado | contexto qualitativo |
| Transfermarkt | lesões e suspensões | confirmar desfalques |
| CBF (cbf.com.br) | tabela, escala de arbitragem | para saber o árbitro do jogo |
| football-data.co.uk | histórico da Série A com odds de fechamento | usado pelo `historico.py` |
| Open-Meteo | previsão de chuva | usado pelo `clima.py` |

## O que coletar por jogo

- Competição, data, horário (Brasília), estádio e cidade
- Gols marcados/sofridos: mandante **em casa**, visitante **fora** (temporada e últimos 5–10)
- Escanteios a favor/contra (mesmo recorte); se possível, escanteios nos primeiros 10–15 min
- Cartões a favor/contra e média do árbitro escalado
- Chutes a favor/contra
- Desfalques importantes, escalação provável, momento (sequência, rodízio, decisão de copa)
- Odds da Betano, se o Daniel enviar

## Quando o dado não existe

Séries B/C e Copa do Nordeste costumam ter menos estatística avançada. Sem
amostra mínima (≈ 5 jogos na condição casa/fora), o mercado fica **N/D** e não
entra no ranking. Não preencha com média de outra competição sem avisar.
