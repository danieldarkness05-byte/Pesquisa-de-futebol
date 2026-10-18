---
name: ouro
description: Rotina diária completa e econômica — peneira (script) → dossiê (script) → workflow aprofundar (1 pesquisador + 1 cético só nos melhores candidatos vivos) → veredito pelas ferramentas → salva, faz commit e notifica só se houver OURO. Use na rotina diária e quando o Daniel mandar /ouro.
argument-hint: "[hoje | amanhã | AAAA-MM-DD] [números da peneira]"
allowed-tools: Bash(python3 ferramentas/*) Bash(git *) Workflow Read Write Edit PushNotification
---

Ouro do dia: **$ARGUMENTS** (vazio = hoje, candidatos automáticos).

**Economia de créditos.** O trabalho pesado é Python, que não gasta créditos. Agentes só entram no
passo 3, só nos candidatos **vivos**, e no máximo `config.json → aprofundar.max_candidatos` (padrão 3).
Fora do workflow: sem WebSearch, sem subagentes avulsos e sem ler arquivos além do necessário.

0. **Aprender (sempre, barato):**
   - Rode `python3 ferramentas/previsoes.py resolver` e depois `python3 ferramentas/previsoes.py resumo --curto`.
   - Cada previsão resolvida agora vira uma linha na tabela "Resultados" de `docs/licoes.md`, com lição só
     quando o caso ensinar algo.
   - Leia `docs/licoes.md`.
1. **Peneira:** rode `python3 ferramentas/varredura.py --curto` em primeiro plano (Bash `timeout: 600000`).
   - Se o Daniel passou uma data, use `--data`.
   - Se a saída avisar falhas, rode **uma** vez de novo (o cache acelera).
   - Sem candidatos: não há ouro. Não grave arquivo do ouro e pule para o passo 7 (de manhã) ou para a resposta.
2. **Dossiê (de graça):**
   - Rode `python3 ferramentas/dossie.py` (resumo).
   - Depois rode `python3 ferramentas/dossie.py --json > <scratchpad>/dossie.json`.
   - Se o Daniel pediu números, use `--numeros`. Sem números, entram os N primeiros do config; jogos a menos de 20 min do início ficam fora.
   - Nenhum candidato `vivo`: não há ouro e nenhum agente roda aqui. Pule para o passo 7 (de manhã) ou para a resposta.
   - Na rodada da tarde, confira o `analises/<data>-ouro.md` da manhã: candidato que já foi descartado lá só vai ao workflow se algo mudou a favor (odd, escalação, desfalque). Senão, repita o veredito sem gastar agentes (lição 46).
3. **Workflow:** leia o JSON e chame
   `Workflow({scriptPath: ".claude/workflows/aprofundar.js", args: <objeto do dossiê>})`.
   - `args` vai como objeto JSON, não como string.
   - Ele roda em segundo plano. Espere a notificação; não pesquise em paralelo.
4. **Veredito (ferramentas, não palpite):**
   - **Confira com `valor.py`:** para cada resultado com `veredito_previo = OURO`, rode
     `python3 ferramentas/valor.py --prob <p_final> --odd <odd_agora> --mercado-odds <escolha>,<oposto>`.
     Na dupla chance, o oposto é o resultado que falta (1X contra 2). Nas linhas, é o outro lado. Na linha asiática, acrescente `--devolucao`.
   - **OURO só se** prob ≥ `criterios.prob_minima`, EV ≥ `criterios.ev_minimo`, a regra 8 está ok e o cético não refutou.
   - **Classifique a evidência:**
     - MUITO FORTE: variantes ≥ corte + 10 p.p., frequência nas amostras ≥ prob − 5 p.p., até 5 p.p. acima do mercado e cético com confiança alta.
     - FORTE: variantes ≥ corte + 5 p.p., até 8 p.p. acima do mercado e cético sem refutar.
     - MODERADA: passa, mas com **um** ponto fraco: de 8 a 10 p.p. acima do mercado, odd de agora a menos de 2% da mínima, mercado indo contra desde a abertura, ou escalação não confirmada num pick que depende dela.
     - FRACA: dois ou mais pontos fracos. **Descarte.** Nunca force entrada.
   - **Stake:** Kelly × `banca.kelly_fracao`, com teto em `banca.stake_max_pct`. Se `valor_banca` for 0, mostre em % da banca.
5. **Salvar:** grave `analises/AAAA-MM-DD-ouro.md` e faça commit e push na branch atual.
   - O arquivo é curto: resultado, uma seção por candidato (modelo → ajuste e motivo → prob. final → mercado → veredito), fontes e "Dados pesquisados até HH:MM".
6. **Resposta curta, SÓ com o que passou no critério** (regra do Daniel):
   - ⭐ OURO ranqueado, uma linha por pick: jogo · hora · mercado · prob. · odd mínima Betano · odd/EV bet365 · evidência · motivo.
   - O que conferir antes de entrar: escalação oficial cerca de 1 h antes e a odd na Betano ≥ mínima.
   - **Não** liste descartados, candidatos nem "quase": isso fica só no arquivo do passo 5.
   - Sem ouro e sem 🛡️ defesa fraca: só "Nenhuma oportunidade hoje."
     Sem ouro, mas com defesa fraca: só a seção 🛡️.
   - Termine com quantos agentes o workflow usou, em uma linha curta.
7. **Defesa fraca (só na execução da MANHÃ, antes das 12:00):** siga `.claude/skills/defesa-fraca/SKILL.md`
   para HOJE, em todas as ligas do Sofascore.
   - Um workflow de cada vez: primeiro termine o do /ouro.
   - A chuva é só informativa nessa análise.
   - Os jogos que passarem entram na MESMA resposta, numa seção "🛡️ Defesa fraca" (até 4), e contam como
     pick para a notificação, mesmo sem ⭐ OURO.
   - O arquivo, o registro das previsões e as lições seguem a skill. Faça commit e push junto.
8. **Notificação:**
   - Com OURO: `PushNotification` "⭐ OURO HH:MM <jogo> <mercado>, odd mín X.XX".
   - Com 🛡️ Defesa fraca: `PushNotification` "🛡️ Defesa fraca DD/MM: <jogo> <mercado> mín X.XX (+N)".
     Se houver os dois, junte numa notificação só.
   - Sem ouro e sem defesa fraca: não notifique.

Para gastar menos: em `config.json → aprofundar`, baixe `max_candidatos` ou use `cetico: false`.
Com `max_candidatos: 0`, o /ouro vira só a peneira.
