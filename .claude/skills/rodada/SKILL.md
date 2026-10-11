---
name: rodada
description: Varre todos os jogos de um dia (ou de uma competição) e devolve só as oportunidades de ouro ranqueadas, excluindo jogos com chuva. Use quando o Daniel pedir os jogos de hoje/amanhã, uma rodada inteira ou uma varredura de várias partidas.
argument-hint: "[data AAAA-MM-DD ou hoje/amanhã] [competição]"
allowed-tools: Bash(python3 ferramentas/*) WebSearch WebFetch Read
---

Varredura: **$ARGUMENTS** (sem data = hoje; sem competição = todas de `config.json` → `competicoes`).

1. **Lista de jogos:** procure os jogos do dia nas competições pedidas. Monte uma tabela
   com horário (Brasília), jogo, competição e cidade. Diga a fonte da lista.
2. **Chuva:** rode `clima.py` para cada jogo. Tire da lista os que derem CHUVA
   (anote em "excluídos por chuva"). Erro de rede → veja a alternativa `--url`/`--arquivo`
   no `--help`; se não resolver, marque "chuva não verificada".
3. **Coleta em paralelo:** para cada jogo restante, chame o subagente
   `pesquisador-jogo` (vários ao mesmo tempo, um por jogo) passando competição, data,
   horário e times. Cada um devolve as estatísticas com fonte.
4. **Probabilidades:** com os dados de cada jogo, rode `prob.py` para os mercados:
   under/over 2.5 gols, ambas marcam, dupla chance, escanteios (jogo e primeiros 10 min),
   cartões (com árbitro), chutes. Dado N/D → mercado fora.
5. **Odds:** use as odds que o Daniel enviou. Se ele não enviou, procure odds atuais em
   comparadores públicos e diga a fonte; sem odd confiável, mostre só a **odd mínima**
   e marque "conferir na Betano".
6. **Defesa fraca:** destaque azarões com defesa muito vazada e marque **⚠️ RISCO** quando
   também tiverem ataque forte (regra 4 do CLAUDE.md).
7. **Resultado:** só OURO (≥ 60% e EV ≥ mínimo, ou ≥ 60% aguardando conferência da odd),
   ranqueado por probabilidade e depois EV. Nenhum? Diga claramente: "nenhuma oportunidade
   de ouro hoje". Em seguida, uma linha por jogo descartado com o motivo.
8. **Salve** o resumo em `analises/<data>-rodada.md`.

Mantenha a resposta curta (celular): tabela de ouros + lista de descartes + fontes.
