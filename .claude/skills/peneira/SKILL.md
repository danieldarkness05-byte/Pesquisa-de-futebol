---
name: peneira
description: Peneira barata do dia — roda ferramentas/varredura.py, que varre todos os jogos das competições do config.json e devolve só os mercados com valor (prob ≥ triagem, EV ≥ mínimo, robustos, sem chuva). Use quando o Daniel pedir a peneira, a varredura rápida ou os jogos de valor do dia, e na rotina diária. Não pesquisa notícias (isso é o /aprofundar).
argument-hint: "[hoje | amanhã | AAAA-MM-DD] [IDs de torneios]"
allowed-tools: Bash(python3 ferramentas/*) PushNotification
---

Peneira: **$ARGUMENTS** (vazio = hoje).

**Modo econômico.** O trabalho pesado está no script. Não pesquise notícias, não chame
subagentes e não use WebSearch/WebFetch. Não leia arquivos do repositório além desta skill.

1. Rode `python3 ferramentas/varredura.py --curto` em primeiro plano, com tempo limite de 10 min
   (Bash `timeout: 600000`). Assim não vai para segundo plano nem gasta um turno extra. Para outra data, use `--data AAAA-MM-DD`
   ("amanhã" é a data de amanhã em Brasília). Para competições específicas, use `--torneios` com os
   IDs de `config.json → varredura.torneios_sofascore`.
   - Leva de 2 a 3 min. Se a saída avisar de falhas, rode **uma** vez de novo: o cache deixa a
     segunda rodada rápida.
2. **Repasse a saída como está**, sem a linha `NOTIFICAR:`. Ela já vem no formato de celular.
   Não reescreva e não acrescente análise.
3. Se houver a linha `NOTIFICAR: <texto>`, mande `PushNotification` com esse texto.
   Sem candidatos, não notifique.
4. Não grave arquivo nem faça commit. O script já salva o resultado em
   `dados/cache/sofascore/peneira-AAAA-MM-DD.json`, que o /aprofundar reaproveita.

Corte da peneira: `varredura.prob_triagem` (59%), um pouco abaixo do corte final
(`criterios.prob_minima`, 60%), para não perder candidatos na borda. Detalhes em `docs/metodologia.md`.

Para a rotina completa (peneira + pesquisa com agentes só nos melhores candidatos), use `/ouro`.
