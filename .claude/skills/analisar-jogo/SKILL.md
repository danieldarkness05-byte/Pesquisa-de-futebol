---
name: analisar-jogo
description: Análise estatística completa de UM jogo de futebol (gols, escanteios, cartões, chutes) com veredito de oportunidade de ouro. Use quando o Daniel pedir para analisar uma partida específica.
argument-hint: "Mandante x Visitante [data] [odds coladas]"
allowed-tools: Bash(python3 ferramentas/*) WebSearch WebFetch Read
---

Analise o jogo: **$ARGUMENTS**

Siga as regras de ouro do CLAUDE.md (≥ 60% + valor, nunca forçar, chuva exclui,
nada de número sem fonte).

1. **Identifique o jogo:** competição, data, horário (Brasília), estádio, cidade.
   Se faltar a data, procure o próximo jogo entre os dois times.
2. **Chuva:** `python3 ferramentas/clima.py --cidade "<cidade>" --data <data> --hora <HH:MM>`.
   Com CHUVA, pare aqui: informe que o jogo está excluído e por quê.
   Se der ERRO de rede, pegue a URL com `--url`, baixe com WebFetch, salve o JSON e
   rode de novo com `--arquivo`. Se ainda falhar, siga marcando "chuva não verificada".
3. **Dados:** colete o que está em `docs/fontes.md` → "O que coletar por jogo",
   começando pelo Sofascore. Anote fonte e recorte de cada número.
4. **Probabilidades:**
   - Gols: se for Série A, rode também `python3 ferramentas/historico.py confronto --casa "<A>" --fora "<B>"`
     e compare com `prob.py gols` usando as médias coletadas. Divergência grande → explique.
   - Escanteios (jogo inteiro e `--minutos 10`), cartões (com `--arbitro`), chutes:
     `python3 ferramentas/prob.py contagem ...`. Se tiver a lista jogo a jogo, use `--amostra`.
   - Passe as odds que o Daniel enviou em `--odds` (chaves como `under2.5`, `ambas_nao`, `1X`).
5. **Valor:** para cada candidato ≥ 60%, confira com `valor.py` (com `--mercado-odds`
   quando tiver os dois lados do mercado) e aplique a regra de sanidade (+10 p.p.).
6. **Responda** no formato do CLAUDE.md: OURO primeiro (ou "nenhuma oportunidade"),
   depois descartados com motivo (aqui o Daniel perguntou deste jogo), depois fontes.
7. **Salve** em `analises/<data>-<mandante>-x-<visitante>.md` (slug sem acentos),
   seguindo `templates/analise.md`.
