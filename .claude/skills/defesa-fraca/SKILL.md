---
name: defesa-fraca
description: Análise diária "defesa fraca do azarão x ataque forte do favorito" em TODAS as ligas do Sofascore — triagem e estatística por script (defesa.py), pesquisador + cético por candidato (workflow defesa.js), probabilidade conservadora, odd mínima, registro das previsões e aprendizado contínuo (previsoes.py + docs/licoes.md). Use quando o Daniel pedir jogos em que o azarão tem defesa muito fraca e o favorito ataca forte, e na rotina diária.
argument-hint: "[hoje | amanhã | AAAA-MM-DD] [--config para só as ligas do config]"
allowed-tools: Bash(python3 ferramentas/*) Bash(git *) Workflow Read Write Edit PushNotification
---

> **SUSPENSO (Daniel, 21/10): só under.** Não rode nem mande este mercado; use o `/under`.


Data: **$ARGUMENTS** (vazio = hoje; "amanhã" = data de amanhã em Brasília).

O Daniel quer **esse tipo de análise todo dia, o mais analítica possível e evoluindo a cada pesquisa**.
Regras específicas desta análise (pedido dele em 12/10):

- **Chuva é só informativa.** Ela não exclui jogo aqui; a regra 3 continua valendo no /ouro.
- **Forma do favorito (pedido de 13/10):** o favorito precisa de **7 pontos ou mais nos últimos 5 jogos
  oficiais** (todas as competições, sem amistosos; com menos jogos, a proporção 7/15). Com 6 ou menos,
  **sai da lista** (regra ajustada pelo Daniel em 14/10; antes era 8). O `defesa.py` já marca `passa = false`
  com o motivo. Se o pesquisador achar jogo oficial mais recente que o Sofascore não tem, refaça a conta.
- **Técnico poupando titulares (pedido de 13/10):** se o técnico do favorito for poupar jogadores
  (`cetico.poupa_titulares_final` = `SIM_CONFIRMADO` ou `PROVAVEL` com fonte confiável), **o jogo sai**.
  O alerta de calendário do `defesa.py` ("rodízio possível") sozinho não tira: precisa da notícia.
- **Todas as ligas do Sofascore.** Ligas profissionais vêm primeiro. Amador, base e time B só entram se faltar caso profissional.
- **Resposta:** até `defesa.max_resposta` jogos (padrão 4). Só os que passam: prob ≥ `criterios.prob_minima`
  depois do ajuste e cético sem refutar. **Nunca force:** se passarem 2, mande 2 e diga que o resto não fechou.

## 0. Aprender antes de analisar (barato)

1. Rode `python3 ferramentas/previsoes.py resolver`. Ele busca no Sofascore o placar das previsões pendentes.
2. Rode `python3 ferramentas/previsoes.py resumo --analise defesa --curto`.
   - Se aparecer aviso de calibração (faixa com ≥ 30 picks acertando 5 p.p. ou mais abaixo), aplique
     o desconto nessa faixa e registre em `docs/licoes.md`.
3. Para cada previsão resolvida agora, acrescente uma linha na tabela "Resultados" de `docs/licoes.md`.
   - Coluna "Lição": só quando o erro ou o acerto ensinar algo (por que errou? a tese falhou ou foi variância?).
   - Se a lição se repetir em 3 ou mais casos, transforme-a em alerta automático em `ferramentas/defesa.py`
     (com teste) ou em parâmetro de `config.json → defesa`.
4. Leia `docs/licoes.md` inteiro. As lições valem para o passo 4.

## 1. Triagem + estatística (script, não gasta créditos)

Rode `python3 ferramentas/defesa.py --data <D> --curto` (Bash `timeout: 900000`). Com "amanhã", use `--data`.

- Rode **uma vez só**. O resumo vai para a tela e o JSON completo é gravado em
  `dados/cache/sofascore/defesa-<D>.json`. Esse é o arquivo que vai para o workflow.
  Não rode de novo com `--json`: as odds e a lista mudam, e a numeração deixaria de bater.
- Só rode de novo (uma vez) se o resumo avisar falhas de rede.
- **Nenhum candidato com `passa`:** responda só "Nenhum jogo com defesa fraca x ataque forte hoje."
  Salve o arquivo do passo 5 com a triagem e pare.

## 2. Pesquisa (workflow, os créditos vão aqui)

Leia `dados/cache/sofascore/defesa-<D>.json` e chame
`Workflow({scriptPath: ".claude/workflows/defesa.js", args: <objeto desse JSON>})`.

- `args` vai como objeto JSON, não como string.
- Ele pega os `defesa.max_pesquisa` melhores com `passa` e sem RISCO. Para escolher outros, passe `args.ids`.
- Espere a notificação; não pesquise em paralelo.
- Resultado com `status` diferente de `ok` (pesquisa ou cético falhou): o jogo **não** entra sem pesquisa.
  Retome com `resumeFromRunId` (os que terminaram ficam em cache) ou diga que ficou sem pesquisa.

## 3. Veredito (ferramentas, não palpite)

Para cada resultado:

1. **Mercado e probabilidade.**
   - `mercado = cetico.mercado_final`. Se for `nenhum` ou `refutado = true`, o jogo cai.
   - Se `cetico.poupa_titulares_final` for `SIM_CONFIRMADO` ou `PROVAVEL`, o jogo cai (técnico poupando).
   - `p = prob do defesa.py para esse mercado + cetico.ajuste_final_pp/100`. O ajuste total vai de −5 a +5 p.p.
   - Escreva o motivo do ajuste.
2. **Data diferente (`pesquisa.data_diferente`):** o jogo sai da lista do dia e vai para a data real, registrado
   com ela (Real Estelí x Jalapa: o Sofascore dava 14/10 18:00, e o jogo real era 15/10 22:00).
3. **Mando invertido (`pesquisa.mando_invertido`):** rode de novo com os dados do mando real.
   Use `prob.py gols` com as médias da tabela, trocando casa por fora, e fique com o menor valor.
4. **Passa se** `p ≥ criterios.prob_minima` e não refutado.
5. **Odd mínima** = (1 + `criterios.ev_minimo`) / p.
   - Se houver odd real (bet365 no JSON, ou a que o Daniel colar), rode
     `python3 ferramentas/valor.py --prob <p> --odd <odd>`.
6. **⚠️ RISCO** (o azarão também ataca bem) não entra como pick. Pode aparecer como aviso.
7. **Regra 8 do mercado final:** compare o `p` final com `mercados[chave].prob_mercado` do JSON. Para a
   vitória e a dupla chance é o 1X2/DC sem margem; para os gols, o λ implícito do 1X2 e das linhas de gols.
   - Se `p` passar do mercado em mais de 10 p.p., só entra se o pesquisador explicou o que o mercado sabe.
   - Senão, desconte até 5 p.p. ou derrube.
8. **Ordem:** profissional antes de amador, depois maior p, depois menos alertas.

## 4. Salvar, registrar e evoluir

1. **Análise:** grave `analises/AAAA-MM-DD-defesa-fraca.md` com:
   - critério e dados (horário da consulta);
   - tabela dos que passaram;
   - nota por jogo (a favor, contra, ajuste e motivo);
   - os que não passaram e por quê;
   - fontes.
2. **Previsões:** registre cada jogo que passou em `ferramentas/previsoes.py`. Pode ser com `add-json`,
   numa lista com `data, hora, evento, jogo, competicao, nivel (pro|base), analise: "defesa", mercado,
   lado, prob, odd_minima, odd_casa, alertas`.
   - Mercados: `marca_1`, `marca_2`, `marca_3` (gols do favorito), `vence`, `dupla_chance`.
   - `lado`: `casa` ou `fora`, **obrigatório**: é o lado do favorito no Sofascore (`fav_casa` no JSON).
     Se o mando foi invertido, siga o Sofascore, porque é ele que resolve o placar.
   - `alertas` pode ir como lista.
   - O `add-json` valida tudo antes de gravar: ou entra a lista inteira, ou nada.
3. **Lições:** cada `cetico.licao` não vazia e nova vira um item em `docs/licoes.md`, com data e jogo.
4. Faça commit e push na branch atual, com mensagem em português.

## 5. Resposta (curta, para celular)

- **Tabela:** jogo · hora · liga · azarão (gols sofridos/jogo na condição) · mercado · prob · odd mínima (e bet365 se houver).
- **Uma linha por jogo** com o motivo principal e o maior risco.
- **Lembrete:** conferir a escalação cerca de 1 h antes e a odd na Betano ≥ mínima. Liga amadora quase nunca está na Betano.
- **Uma linha de calibração**, se já houver previsões resolvidas: "Até agora: X/Y acertos (Z%) para W% previsto".
- **Rotina diária:** com pelo menos 1 jogo, mande `PushNotification` "🛡️ Defesa fraca DD/MM: <jogo> <mercado> mín X.XX (+N)".
  Sem jogo, não notifique.
