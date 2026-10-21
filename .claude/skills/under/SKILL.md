---
name: under
description: Especialista em UNDER de gols — todos os jogos do dia em TODAS as ligas do Sofascore, só "menos de X.5 gols" com 70%+ e valor, passando pelos requisitos de under (cauda dos dois times, taxa da liga, amostra da temporada atual, xG somado, favorito goleador) e por pesquisa a fundo (desfalques no ataque e na defesa, estilo, motivação, H2H na linha certa, árbitro, clima, mercado). Use quando o Daniel pedir under, "menos gols" ou jogos para under.
argument-hint: "[hoje | amanhã | AAAA-MM-DD]"
allowed-tools: Bash(python3 ferramentas/*) Bash(git *) Workflow Read Write Edit
---

Data: **$ARGUMENTS** (vazio = amanhã se já passou das 18:00 de Brasília, senão hoje). Pedido do Daniel em 17/10:
"fica especialista em um mercado, veja todos os requisitos para ir no under... estatísticas, desfalques, tudo que
comporta uma partida para possivelmente um under", com a porcentagem de 70%.

**Regra 0 (21/10): este é o ÚNICO modo.** O Daniel só quer under: nenhum outro mercado vai na resposta.

**Regras:** prob ≥ 70% (variantes e veredito), chuva só informativa, profissional antes de amador (lição 14).
**Sem odd na resposta** (20/10: "esquece a odd, só me passa os que passaram na análise"): odd, odd mínima, EV e regra 8
continuam calculados e registrados para a calibração e as lições, mas a entrega é pela **chance final**. Nunca force:
sem nada, "Nenhum under com 70%+ amanhã".

## Os requisitos do under (o que o especialista confere)

| Requisito | Onde | Efeito |
|---|---|---|
| Modelo de gols (Poisson/Dixon-Coles, 7 variantes, incerteza) ≥ 70% | `varredura.py` | corte |
| Robustez: sem os 2 últimos, só gols, só xG, amostra geral | `varredura.py` | corte |
| Frequência real do under nas amostras | `varredura.py` | corte (e alerta) |
| Regra 8 (modelo ≤ mercado + 10 p.p.) | `varredura.py` | corte |
| Cauda: últimos 7 oficiais de cada time acima da linha (lição 33) | `under.py` | corte |
| Taxa de under da liga ≥ p − 15 p.p. | `under.py` | corte |
| Amostra da temporada atual ≥ 30% (lição 32) | `under.py` | corte |
| xG somado perto da linha; favorito com odd ≤ 1.30 | `under.py` | alerta |
| Desfalques no ataque (a favor) e na defesa (contra), escalação | pesquisador | ajuste |
| Estilo, técnico, motivação (empate serve? alguém precisa vencer?) | pesquisador | ajuste |
| H2H na LINHA exata (lição 34), árbitro (pênaltis, expulsões), calendário | pesquisador | ajuste |
| Movimento da odd do under (abertura → agora) | dossiê + pesquisador | alerta |

## 0. Aprender

`python3 ferramentas/previsoes.py resolver` e `resumo --curto`; uma linha por resolvida em `docs/licoes.md`; leia o arquivo.

## 1. Peneira e filtro de under (scripts)

1. `python3 ferramentas/varredura.py --data <D> --todas --prob-min 0.70 --chuva-informativa --curto`
   (segundo plano; 10 a 30 min). Se já rodou para a data (`peneira-<D>-todas.json`), não rode de novo.
2. `python3 ferramentas/under.py --data <D>`: grava `peneira-<D>-under.json` só com os unders que passam nos
   requisitos (e `caidos` com o motivo).
3. Sem candidato: responda "Nenhum under com 70%+ amanhã" e salve a análise.
4. **Sofascore fora do ar** (403, peneira com 0 jogos e falhas, mesmo depois de 1 nova tentativa): não pare. Pule para
   o passo 3 no **modo web**: `args = {data, modo: "web", criterios: {prob_minima: 0.70, ev_minimo: 0.03}}`. Um agente
   descobridor acha os unders do dia em 365Scores, SoccerStats, FootyStats e outras fontes (`docs/metodo-under.md`).

## 2. Dossiê

Entram na pesquisa os unders que passaram nos requisitos, **com ou sem valor** (`candidatos` + `sem_valor` do
`under.py --varrer`), até `config.json → under.max_pesquisa`, por `p_min`.

`python3 ferramentas/dossie.py --data <D> --sufixo under --prob-min 0.70 --max 5 --json > <scratchpad>/dossie-under-<D>.json`.
Um pick por jogo: se o mesmo jogo tem 2.5 e 3.5, fica a linha `principal` do `under.py` (maior EV).

## 3. Workflow

`Workflow({scriptPath: ".claude/workflows/under.js", args: <dossiê>})` com `args.criterios.prob_minima = 0.70`,
`args.aprofundar.modelo_agentes = null` e `args.under.max_pesquisa` (padrão `config.json → under.max_pesquisa`).

É o **Método Under** (`docs/metodo-under.md`), com 3 agentes por jogo e parada assim que o under morre:
**estatístico independente** (médias de fontes fora do Sofascore → `prob.py` → `p_independente`, cauda e H2H na
linha) → **pesquisador de contexto** (imprensa, clubes, Transfermarkt, árbitro, clima, odds em 2+ casas) →
**cético** (confere em outra fonte). Cada número-chave em 2 fontes independentes.

## 4. Veredito

`p_final` = **a menor entre o modelo e a conta independente** + ajustes (±5); o workflow já calcula. Se o cético
escreveu uma leitura honesta menor, use a menor. Avisos de "fontes divergem" vão para o arquivo e pesam contra.
**Passa se `p_final ≥ 0.70` e o cético não derrubou a tese esportiva** (refutado só por valor/odd continua valendo).
Ordene pela chance; **≥ 80% = "mais fortes"** (a faixa que mais acerta). Odd e EV vão só para o registro.

## 5. Salvar, registrar e evoluir

`analises/AAAA-MM-DD-under.md`; `previsoes.py add-json` com `analise: "under"`, `mercado: "under_X.5"`; lições novas
(campo `licao` do cético) em `docs/licoes.md`; commit e push.

## 6. Resposta (curta)

Só under. Tabela: jogo · hora · linha · chance (ordem decrescente; ≥ 80% marcados como mais fortes). Uma linha de
motivo e risco por jogo. Lembrete: conferir a escalação 1 h antes. Uma linha de calibração dos unders.
