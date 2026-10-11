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

1. **Peneira:** rode `python3 ferramentas/varredura.py --curto` em primeiro plano (Bash `timeout: 600000`).
   - Se o Daniel passou uma data, use `--data`.
   - Se a saída avisar falhas, rode **uma** vez de novo (o cache acelera).
   - Sem candidatos: responda "Nenhum jogo de valor na peneira de hoje." e pare, sem notificar e sem gravar arquivo.
2. **Dossiê (de graça):**
   - Rode `python3 ferramentas/dossie.py` (resumo).
   - Depois rode `python3 ferramentas/dossie.py --json > <scratchpad>/dossie.json`.
   - Se o Daniel pediu números, use `--numeros`. Sem números, entram os N primeiros do config; jogos a menos de 20 min do início ficam fora.
   - Nenhum candidato `vivo`: responda em até 4 linhas com o motivo de cada um e pare, sem agentes.
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
6. **Resposta curta**, no formato do CLAUDE.md:
   - ⭐ OURO ranqueado, uma linha por pick: jogo · hora · mercado · prob. · odd mínima Betano · odd/EV bet365 · evidência · motivo.
   - Descartados, uma linha cada com o motivo.
   - O que conferir antes de entrar: escalação oficial cerca de 1 h antes e a odd na Betano ≥ mínima.
   - Termine com quantos agentes o workflow usou.
7. **Notificação:**
   - Com OURO: `PushNotification` "⭐ OURO HH:MM <jogo> <mercado>, odd mín X.XX".
   - Sem ouro: não notifique.

Para gastar menos: em `config.json → aprofundar`, baixe `max_candidatos` ou use `cetico: false`.
Com `max_candidatos: 0`, o /ouro vira só a peneira.
