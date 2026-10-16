---
name: azarao-forte
description: Análise "azarão forte" em TODAS as ligas do Sofascore — jogos em que o azarão tem boa chance de NÃO perder (dupla chance, empate anula ou vitória) com valor. Triagem e estatística por script (azarao.py), pesquisador + cético por candidato (workflow azarao.js), probabilidade conservadora, odd mínima, regra 8, registro das previsões e lições. Use quando o Daniel pedir jogos em que o azarão é forte e pode empatar ou ganhar.
argument-hint: "[hoje | amanhã | AAAA-MM-DD]"
allowed-tools: Bash(python3 ferramentas/*) Bash(git *) Workflow Read Write Edit
---

Data: **$ARGUMENTS** (vazio = hoje). Pedido do Daniel em 16/10: "azarão forte, com muita chance de empatar
ou ganhar, análise a fundo, resultados notáveis e com valor".

**Regras (as mesmas do projeto, olhando o lado do azarão):**

- Só passa mercado com **prob ≥ `criterios.prob_minima` e EV ≥ `criterios.ev_minimo`** na odd real.
  Sem odds no Sofascore, o jogo não entra, porque não há valor para medir.
- **Regra 8 é central aqui.** Quando o modelo dá ao azarão bem mais que o mercado (+10 p.p.), quase sempre o
  mercado sabe algo. Só entra com explicação sólida (`cetico.regra8_explicada`).
- O azarão precisa de **7+ pontos nos últimos 5 oficiais**, a mesma régua da forma do favorito na defesa fraca.
- **Técnico do azarão poupando titulares → o jogo sai.** O favorito poupar ajuda o azarão.
- **Lições:** valem as de `docs/licoes.md`, como data e mando em 2ª fonte, liga não verificável, amostra
  recente e regressão pelo xG.
- **Chuva:** só informativa.

## 0. Aprender

Rode `python3 ferramentas/previsoes.py resolver` e `python3 ferramentas/previsoes.py resumo --analise azarao --curto`.
Leia `docs/licoes.md`.

## 1. Triagem + estatística (script)

Rode `python3 ferramentas/azarao.py --data <D> --curto` (Bash `timeout: 1500000`) **uma vez**. O JSON vai para
`dados/cache/sofascore/azarao-<D>.json`.

## 2. Pesquisa

Chame `Workflow({scriptPath: ".claude/workflows/azarao.js", args: <JSON>})`.
- Ele pesquisa os candidatos com `passa` e sem RISCO.
- Para escolher outros, passe `args.ids`.
- Resultado sem `status: ok` não entra.

## 3. Veredito

1. **Mercado e probabilidade:** `mercado = cetico.mercado_final`; `p = prob do azarao.py + ajuste_final_pp/100`.
2. **O jogo cai se:**
   - `refutado`;
   - `mercado_final = nenhum`;
   - `poupa_titulares_azarao_final` for SIM_CONFIRMADO ou PROVAVEL;
   - `data_diferente` (o jogo vai para a data real);
   - **regra 8 sem explicação** (`regra8_explicada = false` com modelo > mercado + 10 p.p.).
3. **Valor:** `python3 ferramentas/valor.py --prob <p> --odd <odd bet365>` e, para a dupla chance, também
   `--mercado-odds` com o 1X2 sem margem. No empate anula, use o EV com devolução.
4. **Passa se** `p ≥ prob_minima` e o EV na odd real for ≥ `ev_minimo`. **Odd mínima** para o Daniel conferir.

## 4. Salvar e registrar

- **Análise:** grave `analises/AAAA-MM-DD-azarao.md`, com os que passaram, os que caíram e por quê, e as fontes.
- **Previsões:** `previsoes.py add-json` com `analise: "azarao"`.
  - `mercado`: `dupla_chance` ou `vence`; `lado`: o lado do AZARÃO no Sofascore.
  - O empate anula não é registrado (tem devolução); vale como informação.
- **Lições:** novas vão para `docs/licoes.md`.
- Faça commit e push.

## 5. Resposta (curta)

- **Tabela:** jogo · hora · azarão · mercado · prob · odd mínima · odd bet365 · EV.
- Uma linha de motivo e risco por jogo.
- Sem nada: "Nenhum azarão forte com valor hoje." **Nunca force.**
