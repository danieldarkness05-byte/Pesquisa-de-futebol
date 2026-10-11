---
name: registrar-aposta
description: Registra no histórico uma aposta que o Daniel confirmou ter feito. Use só quando ele disser que apostou (nunca por conta própria).
argument-hint: "jogo, mercado, seleção, odd, stake [prob]"
allowed-tools: Bash(python3 ferramentas/registro.py *) Read
---

Registrar: **$ARGUMENTS**

1. Complete os campos com o que estiver na conversa ou na análise do dia em `analises/`
   (competição, probabilidade estimada). Se faltar odd ou stake, pergunte.
2. Rode `python3 ferramentas/registro.py add --jogo ... --competicao ... --mercado ...
   --selecao ... --odd ... --prob ... --stake ...` (sistema: `--tipo sistema`, odd 0, prob 0).
3. Confirme em uma linha com o número da aposta.
