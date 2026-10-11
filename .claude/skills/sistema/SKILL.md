---
name: sistema
description: Monta e simula uma aposta de Sistema (Duplas, Triplas) com as seleções de ouro, mostrando custo, retorno esperado e chance de lucro. Use quando o Daniel pedir duplas, triplas ou sistema.
argument-hint: "[duplas|triplas|2,3] [stake por combinação]"
allowed-tools: Bash(python3 ferramentas/*) Read
---

Pedido: **$ARGUMENTS**

1. Use só seleções aprovadas como OURO nesta conversa ou na análise mais recente em
   `analises/`. Não complete o sistema com seleções fora do critério.
2. Evite duas seleções do mesmo jogo (resultados correlacionados).
3. Rode:
   `python3 ferramentas/sistema.py --tamanhos <2|3|2,3> --stake <valor> --sel "rótulo|jogo|odd|prob" ...`
4. Mostre: número de combinações, custo total, retorno esperado (EV), chance de lucro,
   chance de perder tudo e a tabela por número de acertos.
5. Se o Daniel não disser a stake, use R$ 1 por combinação e mostre os resultados em
   proporção. Se o custo total passar do teto de stake do `config.json`, avise.
