---
name: fortes
description: Os jogos com MUITA chance estatística de bater (pedido do Daniel em 20/10) — mapa de todo mercado com 70%+ em todas as ligas (varredura --mapa + under --varrer), pesquisa a fundo dos mais fortes (pesquisador + cético em todos) e entrega SÓ os que ficam com prob. final ≥ 80%, SEM odd. Use quando o Daniel pedir "os jogos que passaram", "os que têm muita chance de bater", "os mais certos" ou os jogos de amanhã nesse modo.
argument-hint: "[hoje | amanhã | AAAA-MM-DD]"
allowed-tools: Bash(python3 ferramentas/*) Bash(git *) Workflow Read Write Edit
---

Data: **$ARGUMENTS** (vazio = amanhã se já passou das 18:00 de Brasília, senão hoje).

**Pedido do Daniel (20/10):** "esquece a odd, só me passa os jogos que passaram na análise"; "só os que têm muita
chance de bater estatisticamente"; "vamos manter nesse módulo e ir aprimorando".

**Regras deste modo (exceção à regra 1 do CLAUDE.md, a pedido do Daniel):**

- **A entrega não depende de odd nem de EV.** O critério é a probabilidade final depois da pesquisa:
  `config.json → fortes.prob_entrega` (padrão 80%). A faixa 80–90% foi 11/11 até 20/10.
- **Odd, valor e regra 8 continuam calculados e registrados** (para a calibração e para as lições), mas **não vão na
  resposta**, a não ser que o Daniel pergunte.
- **Nunca force:** se nada ficar ≥ 80%, diga "Nenhum jogo com 80%+ amanhã" e, numa linha, quantos ficaram entre 70% e 80%.
- Chuva só informativa. Profissional antes de amador (lição 14). Lições de `docs/licoes.md` valem para a pesquisa.

## 0. Aprender

`python3 ferramentas/previsoes.py resolver` e `python3 ferramentas/previsoes.py resumo --analise fortes --curto` (e o geral).
Uma linha por resolvida em `docs/licoes.md`. **Calibração deste modo:** com ≥ 30 resolvidas, se a faixa ≥ 80% acertar
5 p.p. ou mais abaixo do previsto, suba `fortes.prob_entrega` ou aperte os filtros.

## 1. Mapa (scripts, em segundo plano)

1. `python3 ferramentas/varredura.py --data <D> --todas --prob-min 0.70 --chuva-informativa --mapa --curto`
   → `peneira-<D>-mapa.json` (todo mercado com prob. robusta ≥ 70%, com e sem valor).
2. `python3 ferramentas/under.py --data <D> --varrer` → requisitos de under (cauda, xG da temporada, dispersão...).
   Under que cai nos requisitos não vai para a pesquisa.

## 2. Escolha para a pesquisa

Os `fortes.max_pesquisa` (padrão 10) jogos com maior `p_min`, **um mercado por jogo** (o de maior p_min), profissional
antes de amador. Dossiê: `dossie.py --sufixo <arquivo> --prob-min 0.70 --json` (candidatos do mapa têm `robusto: true`;
unders têm o bloco `under`).

## 3. Pesquisa (workflows, cético em todos)

- Mercados gerais: `aprofundar.js` com `args.cetico_sempre = true`, `args.criterios.prob_minima = 0.70`,
  `args.aprofundar.modelo_agentes = null`.
- Unders: `under.js`.
- O ajuste vai do modelo até a leitura honesta (lição 56).

## 4. Veredito

`p_final` = modelo + ajustes. Se o cético deu uma leitura honesta menor que o `p_final` (texto do motivo), use a menor.
**Entra na resposta se `p_final ≥ fortes.prob_entrega` e o cético não derrubou a tese esportiva.** Refutado só pelo
valor (odd) continua valendo neste modo.

## 5. Registrar e salvar

`previsoes.py add-json` com `analise: "fortes"` para TODO jogo entregue (com odd e mínima nos campos, para a
calibração). `analises/AAAA-MM-DD-fortes.md` com os entregues, os de 70–80% e os que caíram. Lições novas. Commit e push.

## 6. Resposta (curta, sem odd)

Tabela: jogo · hora · mercado · chance. Uma linha de motivo e risco por jogo. Uma linha: "mesmo a 80%+, 1 em cada 5
perde em média" e a calibração da faixa ≥ 80%.
