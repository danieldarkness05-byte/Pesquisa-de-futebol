---
name: peneira
description: Peneira barata do dia — roda ferramentas/varredura.py, que varre todos os jogos das competições do config.json e devolve só os mercados com valor (prob ≥ triagem, EV ≥ mínimo, robustos, sem chuva). Use quando o Daniel pedir a peneira, a varredura rápida ou os jogos de valor do dia, e na rotina diária. Não pesquisa notícias (isso é o /aprofundar).
argument-hint: "[hoje | amanhã | AAAA-MM-DD] [IDs de torneios]"
allowed-tools: Bash(python3 ferramentas/*) PushNotification
---

Peneira: **$ARGUMENTS** (vazio = hoje).

O objetivo é gastar pouco: **não pesquise notícias, não chame subagentes, não use WebSearch.**
Todo o trabalho pesado está no script.

1. Rode `python3 ferramentas/varredura.py` (hoje) ou `--data AAAA-MM-DD`. Para "amanhã", use a
   data de amanhã em Brasília. Se pedir competições específicas, use `--torneios` com os IDs do
   `config.json → varredura.torneios_sofascore`.
   - Leva ~3 min sem cache. Se a saída avisar de falhas de rede, rode uma vez de novo: o cache
     deixa a segunda rodada rápida.
2. Responda **curto** (o Daniel lê no celular):
   - Candidatos em tabela: hora · jogo · mercado · prob. · **odd mínima** (para a Betano) ·
     odd e EV na bet365 · chuva.
   - Descartes: uma linha por motivo, com a quantidade.
   - Avise que as odds são da bet365, não da Betano.
   - Diga que é **triagem**: para o veredito, ele manda `/aprofundar` (todos ou os números escolhidos).
3. **Nenhum candidato** → "Nenhum jogo de valor na peneira de hoje." Não notifique e não force.
4. **Com candidatos** → mande `PushNotification` (uma linha, < 200 caracteres), com os jogos e a odd
   mínima. Exemplo: "⚽ Peneira: 3 de valor — Betis x Osasuna -4.5 gols (mín 1.16), Cádiz x Gijón X2 (mín 1.58)… /aprofundar"
5. Não grave arquivo nem faça commit: a peneira é triagem. O registro fica para o /aprofundar.

Corte da peneira: `varredura.prob_triagem` (59%), um pouco abaixo do corte final
(`criterios.prob_minima`, 60%), para não perder candidatos na borda. Detalhes em `docs/metodologia.md`.
