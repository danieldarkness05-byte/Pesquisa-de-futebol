---
name: aprofundar
description: Análise profunda só dos candidatos da peneira (ou de jogos indicados) — escalação, desfalques, notícias, árbitro, odds atualizadas, ajuste explícito e veredito final OURO ou descartado. Use quando o Daniel mandar /aprofundar depois da /peneira.
argument-hint: "[números da peneira ou nomes dos jogos; vazio = os 5 melhores candidatos de hoje]"
allowed-tools: Bash(python3 ferramentas/*) Bash(git *) WebSearch WebFetch Read Edit Write Agent PushNotification
---

Aprofundar: **$ARGUMENTS** (vazio = os 5 melhores candidatos da peneira de hoje).

O esforço alto vai **só** nos candidatos pedidos. Para economizar créditos:

1. **Candidatos:** leia `dados/cache/sofascore/peneira-AAAA-MM-DD.json`. Se não existir, rode
   `python3 ferramentas/varredura.py --curto`.
   - Pegue os números pedidos. Vazio = os 5 primeiros; para mais, o Daniel pede.
   - Ignore jogos que começam em menos de 20 min.
2. **Odds atualizadas, só desses jogos:** rode `python3 ferramentas/varredura.py --jogos <ids> --curto`
   (o campo `id` está no JSON).
   - Se o candidato sumiu (odd caiu, linha mudou), diga o motivo e **não** pesquise esse jogo.
3. **Contexto em paralelo:** chame um subagente `pesquisador-jogo` por jogo restante, todos de uma vez.
   - Avise que as estatísticas já estão em mãos. Peça só: escalação (oficial ou provável), desfalques
     (CONFIRMADO / PROVÁVEL / RUMOR), técnico, forma, tabela e motivação, calendário/rodízio, árbitro.
   - Peça resposta curta, de no máximo 25 linhas.
4. **Ajuste explícito:** por jogo, no máximo ±5 p.p. e com o motivo escrito (regra 7). Refaça as contas
   com `prob.py` / `valor.py`.
   - Na dupla chance, passe em `--mercado-odds` a odd da escolha e a do resultado oposto
     (ex.: 1X contra "2").
5. **Critério final:** `config.json → criterios` (prob ≥ 60% e EV ≥ 3%) e regra 8.
   - Sem odd da Betano, entregue a **odd mínima**.
   - Classifique a evidência: MUITO FORTE, FORTE, MODERADA ou FRACA.
6. **Perto do jogo** (≤ 75 min): confira se `confirmed` é `true` em
   `https://api.sofascore.com/api/v1/event/<id>/lineups`, ou procure a escalação na imprensa.
   - Uma baixa que muda a tese derruba o pick.
7. **Resposta curta:**
   - ⭐ OURO ranqueado. Uma linha por pick: jogo · hora · mercado · prob. · odd mínima Betano ·
     odd/EV bet365 · evidência · motivo.
   - Descartados, uma linha cada.
   - O que conferir antes de entrar e "Dados pesquisados até HH:MM".
8. **Salve** em `analises/AAAA-MM-DD-aprofundar.md` e faça commit e push na branch da sessão.
9. **Com OURO** → `PushNotification`: "⭐ OURO 14:45 San Lorenzo x Riestra -6.5 cartões, odd mín 1.62".
   Sem ouro, não notifique.

Nunca force entrada: "nenhuma oportunidade de ouro" é resposta válida.
