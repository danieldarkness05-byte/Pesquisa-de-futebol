---
name: aprofundar
description: Análise profunda só dos candidatos da peneira (ou de jogos indicados) — escalação, desfalques, notícias, árbitro, odds atualizadas, ajuste explícito e veredito final OURO ou descartado. Use quando o Daniel mandar /aprofundar depois da /peneira.
argument-hint: "[números da peneira ou nomes dos jogos; vazio = todos os candidatos de hoje]"
allowed-tools: Bash(python3 ferramentas/*) Bash(git *) WebSearch WebFetch Read Edit Write Agent PushNotification
---

Aprofundar: **$ARGUMENTS** (vazio = todos os candidatos da peneira de hoje).

O esforço alto vai **só** nos candidatos. Não reabra jogos que a peneira já descartou, a não ser
que o Daniel peça.

1. **Candidatos e odds atualizadas:** rode `python3 ferramentas/varredura.py --json` (o cache deixa
   rápido) e pegue os candidatos pedidos. Se a odd mudou ou a linha sumiu desde a peneira, diga.
   Se o candidato sumiu, diga e explique o motivo.
2. **Contexto em paralelo:** chame um subagente `pesquisador-jogo` por jogo, todos de uma vez.
   - Avise que as estatísticas já estão em mãos. Peça só: escalação (oficial ou provável), desfalques
     (CONFIRMADO / PROVÁVEL / RUMOR), técnico e mudanças, forma recente, tabela e motivação,
     calendário/rodízio, árbitro.
3. **Ajuste explícito:** por jogo, no máximo ±5 p.p. e com o motivo escrito (regra 7). Refaça as contas
   com `prob.py` / `valor.py`.
   - Na dupla chance, passe em `--mercado-odds` a odd da escolha e a do resultado oposto
     (ex.: 1X contra "2").
4. **Critério final:** `config.json → criterios` (prob ≥ 60% e EV ≥ 3%) e regra 8.
   - Sem odd da Betano, entregue a **odd mínima**.
   - Classifique a evidência: MUITO FORTE, FORTE, MODERADA ou FRACA.
5. **Perto do jogo** (≤ 75 min): confira a escalação oficial e veja se `confirmed` é `true` em
   `https://api.sofascore.com/api/v1/event/<id>/lineups`; se não, procure na imprensa.
   - Uma baixa importante que muda a tese derruba o pick.
6. **Resposta curta:**
   - ⭐ OURO ranqueado. Uma linha por pick: jogo · hora · mercado · prob. · odd mínima Betano ·
     odd/EV bet365 · evidência · motivo.
   - Depois os descartados, uma linha cada.
   - Por fim, o que conferir antes de entrar e "Dados pesquisados até HH:MM".
7. **Salve** em `analises/AAAA-MM-DD-aprofundar.md`, com fontes e ajustes, e faça commit e push na
   branch da sessão.
8. **Com OURO** → `PushNotification` com o pick: "⭐ OURO 14:45 San Lorenzo x Riestra -6.5 cartões, odd mín 1.62".
   Sem ouro, não notifique.

Nunca force entrada: "nenhuma oportunidade de ouro" é resposta válida.
