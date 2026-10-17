---
name: aprofundar
description: Análise profunda só dos candidatos da peneira (ou de números indicados) — dossiê do Sofascore (script), workflow com pesquisador de imprensa + cético por candidato, ajuste explícito e veredito final OURO ou descartado. Use quando o Daniel mandar /aprofundar depois da /peneira.
argument-hint: "[números da peneira; vazio = os N melhores do config]"
allowed-tools: Bash(python3 ferramentas/*) Bash(git *) Workflow Read Edit Write PushNotification
---

Aprofundar: **$ARGUMENTS** (vazio = os N primeiros da peneira de hoje, `config.json → aprofundar.max_candidatos`).

O esforço alto vai **só** nos candidatos pedidos. Para economizar créditos:

1. **Dossiê (script, sem agentes):**
   - Rode `python3 ferramentas/dossie.py [--numeros 1,3]`.
     - Se não houver peneira de hoje, rode antes `python3 ferramentas/varredura.py --curto` (Bash `timeout: 600000`).
     - O script reavalia com as odds de agora e diz quem continua `vivo` e quem `caiu`, com o motivo.
     - Também traz o movimento das odds, os desfalques do Sofascore com os gols de cada um, a forma, a chuva e os minutos para o início.
     - Jogos a menos de 20 min do início ficam fora.
   - Depois rode `python3 ferramentas/dossie.py [--numeros ...] --json > <scratchpad>/dossie.json`.
2. **Quem caiu** (regra 8, odd caiu, linha sumiu): diga o motivo e **não** pesquise.
   - Exceção: o Daniel pediu aquele número de propósito. Nesse caso, passe `investigar_caidos: true` nos args para entender o que o mercado sabe.
3. **Workflow:** `Workflow({scriptPath: ".claude/workflows/aprofundar.js", args: <objeto do dossiê>})`.
   - Por candidato, roda 1 pesquisador de imprensa (escalação, desfalques, técnicos, motivação,
     rodízio, árbitro, o que o mercado sabe) e 1 cético, que tenta derrubar o pick e confere as
     afirmações-chave.
   - O cético só roda se a pesquisa não matou o pick. Os dois usam o modelo de `aprofundar.modelo_agentes`.
   - O workflow devolve o ajuste (limitado a ±5 p.p., regra 7), a prob. final, o EV, a odd mínima, a
     distância do mercado e um `veredito_previo`.
4. **Veredito final pelas ferramentas:**
   - Confirme cada `OURO` prévio com `python3 ferramentas/valor.py --prob P --odd O --mercado-odds <escolha>,<oposto>`.
     Na dupla chance, use 1X contra 2, X2 contra 1, 12 contra X.
   - Critérios: `config.json → criterios` (prob ≥ 60% e EV ≥ 3%) e regra 8. Sem odd da Betano, entregue a **odd mínima**.
   - Evidência: MUITO FORTE, FORTE, MODERADA ou FRACA, com as regras do `/ouro`, passo 4. FRACA = descartado.
5. **Perto do jogo** (≤ 75 min): confira se `confirmed` é `true` em
   `https://api.sofascore.com/api/v1/event/<id>/lineups`. O `dossie.py` mostra isso em "escalação confirmada".
   - Uma baixa que muda a tese derruba o pick.
6. **Resposta curta, SÓ com o que passou no critério** (regra do Daniel):
   - ⭐ OURO ranqueado. Uma linha por pick: jogo · hora · mercado · prob. · odd mínima Betano ·
     odd/EV bet365 · evidência · motivo.
   - O que conferir antes de entrar e "Dados pesquisados até HH:MM".
   - **Não** liste descartados nem "quase" na mensagem: eles ficam só no arquivo do passo 7.
   - Sem ouro: só "Nenhuma oportunidade de ouro hoje."
7. **Salve** em `analises/AAAA-MM-DD-aprofundar.md` e faça commit e push na branch da sessão.
8. **Com OURO** → `PushNotification`: "⭐ OURO 14:45 San Lorenzo x Riestra -6.5 cartões, odd mín 1.62".
   Sem ouro, não notifique.

Nunca force entrada: "nenhuma oportunidade de ouro" é resposta válida.
