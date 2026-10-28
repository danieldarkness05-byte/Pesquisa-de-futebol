---
name: setenta
description: Alta confiança — QUALQUER mercado (resultado, dupla chance, empate anula, gols, ambas marcam, handicap, escanteios, cartões, 1º tempo) com 70%+ de chance, em TODAS as ligas do Sofascore, para hoje e amanhã. Peneira (varredura.py --todas --prob-min 0.70) → dossiê → workflow aprofundar (pesquisador + cético) → veredito, registro e lições. Use quando o Daniel pedir mercados de 70% ou mais, "os mais certos", ou todos os jogos de hoje e amanhã.
argument-hint: "[hoje | amanhã | hoje e amanhã | AAAA-MM-DD]"
allowed-tools: Bash(python3 ferramentas/*) Bash(git *) Workflow Read Write Edit
---

> **SUSPENSO (Daniel, 21/10): só under.** Não rode nem mande este mercado; use o `/under`.


Datas: **$ARGUMENTS** (vazio = hoje e amanhã). Pedido do Daniel em 16/10: "analisamos muitos jogos e aprendemos com
isso; qualquer mercado que chegue a 70% ou mais de chance; todos os jogos de hoje e amanhã; aprenda e evolua".

**Regras:**

- **Corte de 70%** em todas as variantes do modelo (a peneira usa `--prob-min 0.70`), e o veredito final
  também exige `p_final ≥ 0.70`.
- **Valor continua obrigatório:** EV ≥ `criterios.ev_minimo` na odd real (bet365) ou, sem odd, a odd
  mínima para o Daniel conferir na Betano. Com 70%, a odd mínima é 1.48; com 80%, 1.29.
- **Regra 8 e lições** valem como no /ouro. **Chuva é só informativa** (Daniel, 16/10: "pode mandar com chuva ou
  não, isso não interfere"): a varredura roda com `--chuva-informativa`.
- **Todas as ligas**, mas profissional primeiro. Amador, base, feminino e time B (`nivel = base`) só entram se
  faltar caso profissional (lição 14). A varredura já tira ligas editadas à mão e eventos suspeitos
  (lições 18 e 23).
- **Nunca force.** Se nada passar, a resposta é "Nenhum mercado com 70%+ e valor".

## 0. Aprender

`python3 ferramentas/previsoes.py resolver` e `python3 ferramentas/previsoes.py resumo --curto`. Uma linha por
resolvida na tabela de `docs/licoes.md`. Leia `docs/licoes.md`.

## 1. Peneira (script, por data)

`python3 ferramentas/varredura.py --data <D> --todas --prob-min 0.70 --chuva-informativa --curto` (Bash em segundo plano; um dia
cheio leva de 10 a 30 min). O JSON vai para `dados/cache/sofascore/peneira-<D>-todas.json`.

## 2. Dossiê

`python3 ferramentas/dossie.py --data <D> --sufixo todas --prob-min 0.70 --max <N> --json > <scratchpad>/dossie-<D>.json`
- N padrão 6 por dia (pesquisa cara). Jogos a menos de 20 min do início ficam fora.
- Prefira candidatos profissionais e mercados diferentes do mesmo jogo só se forem independentes
  (não mande "vitória" e "dupla chance" do mesmo time).

## 3. Workflow

`Workflow({scriptPath: ".claude/workflows/aprofundar.js", args: <dossiê>})`, com
`args.criterios.prob_minima = 0.70` e `args.aprofundar.modelo_agentes = null` (modelo da sessão: pesquisa mais funda).

## 4. Veredito

Como no /ouro (passo 4): `valor.py`, regra 8, classificação da evidência. **Passa só com `p_final ≥ 0.70`**,
EV ≥ mínimo e cético sem refutar. Evidência como no /ouro: MUITO FORTE, FORTE ou MODERADA passam (MODERADA com o
ponto fraco escrito); FRACA (2+ pontos fracos) sai. Se a FRACA for só pelo valor (odd a menos de 2% da mínima), o pick
pode ir como **condicional** ("só com odd ≥ mínima na Betano"), registrado com essa observação.

## 5. Salvar, registrar e evoluir

- `analises/AAAA-MM-DD-setenta.md`: o que passou, os que caíram e por quê, fontes.
- `previsoes.py add-json` com `analise: "setenta"` para cada pick que passou.
  - Mercados que o `previsoes.py` resolve: `vence`, `dupla_chance`, `sem_empate`, `marca_k`, `over_X.5`, `under_X.5`,
    `ambas_sim`, `ambas_nao`, `handicap_-1.5` (linha .5, do lado escolhido).
  - Escanteios e cartões ainda não: anote em `obs` e resolva à mão.
- Lições novas em `docs/licoes.md`. Commit e push.

## 6. Resposta (curta)

Tabela: jogo · hora · mercado · prob. · odd mínima · odd bet365 · EV. Uma linha de motivo e risco por pick.
Lembrete: escalação 1 h antes e a odd na Betano ≥ mínima. Linha de calibração das previsões.
