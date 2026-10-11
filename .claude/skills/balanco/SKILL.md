---
name: balanco
description: Atualiza os resultados das apostas pendentes e mostra o balanço (acerto, lucro, ROI, CLV, calibração por faixa de probabilidade). Use quando o Daniel pedir resultados, balanço ou desempenho.
argument-hint: "[desde AAAA-MM-DD]"
allowed-tools: Bash(python3 ferramentas/registro.py *) WebSearch WebFetch Read
---

Período: **$ARGUMENTS** (vazio = tudo).

1. `python3 ferramentas/registro.py pendentes`.
2. Para cada pendente de jogo já encerrado, procure o resultado e a estatística do mercado
   (placar, escanteios, cartões, chutes) e resolva com
   `registro.py resolver --id N --resultado green|red|void|meio-green|meio-red`.
   Se encontrar a odd de fechamento, passe `--odd-fechamento`. Sistemas: peça ao Daniel
   o valor recebido e use `--retorno`. Em dúvida sobre o resultado, não resolva: pergunte.
3. `python3 ferramentas/registro.py resumo --desde <data>`.
4. Comente em até 3 linhas: o que está funcionando, o que não está, e se alguma faixa de
   probabilidade acerta bem menos do que o previsto (só com amostra ≥ 30). Seja honesto
   sobre resultados ruins e sobre o tamanho da amostra.
