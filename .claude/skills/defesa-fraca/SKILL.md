---
name: defesa-fraca
description: Compara vários jogos e aponta quais azarões têm a defesa mais fraca, marcando RISCO quando o azarão também ataca bem. Use quando o Daniel pedir análise cruzada de defesa fraca de um lote de jogos.
argument-hint: "[lista de jogos | data | competição]"
allowed-tools: Bash(python3 ferramentas/*) WebSearch WebFetch Read
---

Jogos: **$ARGUMENTS** (sem lista = jogos de hoje nas competições do `config.json`).

1. Para cada jogo, identifique o **azarão** (pior odd para vencer; sem odds, pior
   posição/forma) e a condição em que ele joga (casa ou fora).
2. Colete do azarão, **na condição do jogo**, começando pelo Sofascore:
   gols sofridos/jogo, chutes sofridos/jogo, xG contra (se houver), jogos sem sofrer gol,
   e também gols marcados/jogo e chutes a favor (para medir o ataque).
3. Monte o ranking das defesas mais fracas (gols sofridos/jogo, desempate por chutes
   sofridos). Use pelo menos 5 jogos na condição; menos que isso → "amostra pequena".
4. **⚠️ RISCO:** marque quando o azarão também marca ≥ 1,3 gol/jogo na condição ou está
   entre os 30% melhores ataques da competição. Defesa fraca + ataque forte = jogo aberto,
   o favorito pode sofrer gol.
5. Exclua jogos com chuva (`clima.py`).
6. Para os 3 melhores casos sem RISCO, rode `prob.py gols` e mostre os mercados que
   passam no critério (ex.: favorito over 1.5 gols, vitória do favorito, dupla chance).

Resposta: tabela curta (azarão · jogo · gols sofridos · chutes sofridos · ataque · RISCO)
seguida dos mercados de ouro, se houver. Fontes no final.
