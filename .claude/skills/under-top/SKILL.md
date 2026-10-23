---
name: under-top
description: Só os MELHORES under do dia (pedido do Daniel em 21/10) — usa o mapa e a pesquisa do /under, mas aplica o "selo elite" (chance final ≥ 80%, folga grande para a linha, cauda limpa, mercado a favor, cético confiante) e entrega no máximo 3, ranqueados. Use quando o Daniel pedir os melhores under, o top do dia, "só os under mais certos" ou /under-top.
argument-hint: "[hoje | amanhã | AAAA-MM-DD]"
allowed-tools: Bash(python3 ferramentas/*) Bash(git *) Workflow Read Write Edit PushNotification
---

Data: **$ARGUMENTS** (vazio = amanhã se já passou das 18:00 de Brasília, senão hoje).

Pedido do Daniel (21/10): "um prompt de under especializado que separa somente os melhores under do dia, com as
melhores oportunidades e as melhores chances de entrar". O `/under` entrega tudo o que passa com 70%+. O `/under-top`
fica só com a **elite**: no máximo 3 jogos, e nenhum se ninguém merecer.

O método completo (fontes, cruzamento, selo) está em **`docs/metodo-under.md`**. A pesquisa usa **todas as fontes
da internet**, não só o Sofascore: cada número-chave precisa estar em 2 fontes independentes.

**Regra 0 continua valendo:** só "menos de X.5 gols". Sem odd na resposta (20/10). Odd, odd mínima e EV vão só para o
arquivo e o registro. **Nunca force:** "Nenhum under elite hoje." é resposta honesta.

## 0. Aprender (barato)

1. `python3 ferramentas/previsoes.py resolver` e `python3 ferramentas/previsoes.py resumo --analise under_top --curto`.
2. Cada previsão resolvida vira uma linha em "Resultados" de `docs/licoes.md`.
3. Leia a seção **Under** de `docs/licoes.md`, sobretudo as lições 33, 34, 39 a 42 e 47 a 50 (cauda, H2H na linha,
   xG da temporada, jogos no limite, linha alta, cauda na condição).

## 1. Mapa de unders (scripts, não gasta créditos)

Igual ao `/under`, passo 1. Se o mapa do dia já existe, reaproveite e não rode de novo.

1. `python3 ferramentas/varredura.py --data <D> --todas --prob-min 0.70 --chuva-informativa --curto` (segundo plano,
   10 a 30 min), só se `dados/cache/sofascore/peneira-<D>-todas.json` não existir.
2. `python3 ferramentas/under.py --data <D> --varrer --json > <scratchpad>/under-<D>.json`.
3. **Confirme em outra plataforma (de graça):** `python3 ferramentas/plataformas.py confere --data <D>`. Cada under é
   refeito no **365Scores** (mesmas informações do Sofascore) e sai CONFIRMADO, DIVERGENTE ou NAO_ACHADO.
   **DIVERGENTE não entra na elite.**
4. **Sofascore fora do ar** (403, ou peneira com 0 jogos e falhas, mesmo depois de 1 nova tentativa):
   `python3 ferramentas/plataformas.py mapa --data <D> --json > <scratchpad>/dossie-365-<D>.json`. Use esse mapa no
   pré-filtro: `p_modelo` no lugar de `p_min`, a soma de `gols_esperados` no lugar do xG, e os campos que faltam não
   cortam. Pule o passo 3.1. Se o 365Scores também falhar, chame o workflow no **modo web**:
   `args = {data, modo: "web", criterios: {prob_minima: 0.80, ev_minimo: 0.03}, under: {max_pesquisa: 5}}`.

## 2. Pré-filtro elite (de graça, antes de gastar agente)

Leia o JSON do `under.py`. Fica só o candidato que cumpre **tudo**:

| Requisito | Campo | Corte elite |
|---|---|---|
| Passou nos requisitos do under | `passa` | `true` e `under.falhas` vazio |
| Chance do modelo, inclusive na pior variante | `p_min` | ≥ 0,75 |
| Nenhum alerta | `under.alertas` | vazio (sem xG perto da linha, favorito ≤ 1.30, jogos no limite, frequência abaixo do modelo, valor que some no xG) |
| Cauda recente limpa | `under.cauda.casa/fora.acima` | no máximo 1 estouro somando os dois times |
| Cauda na condição limpa | `under.cauda_cond.casa/fora.acima` | no máximo 1 estouro somando os dois |
| Folga para a linha | `under.xg_somado` | ≤ linha − 1,0 (sem xG: média de gols somada ≤ linha − 1,0) |
| Liga que fica no under | `under.taxa_liga` | ≥ p − 10 p.p. |
| Amostra desta temporada | `under.temporada_atual` | ≥ 50% |
| Liga profissional | `nivel` / competição | profissional (lição 14) |

- **Um jogo, uma linha.** Use a `principal`. Se ela não passa e outra linha do mesmo jogo passa, use a outra.
- Ordene por `p_min` e fique com **até 5**.
- Ninguém passou: responda só **"Nenhum under elite hoje."**, salve o arquivo (passo 6) e pare. Nenhum agente roda.

## 3. Dossiê e pesquisa a fundo (os créditos vão aqui)

1. `python3 ferramentas/dossie.py --data <D> --sufixo under --prob-min 0.70 --numeros <os do passo 2> --json > <scratchpad>/dossie-top-<D>.json`.
   Em seguida: `python3 ferramentas/plataformas.py anexa --dossie <scratchpad>/dossie-top-<D>.json`.
2. **Mercado a favor (corte):** sai quem tem a odd do under **subindo mais de 3%** desde a abertura sem notícia
   (lições 38 e 41), ou o modelo mais de **8 p.p.** acima do mercado sem margem.
3. `Workflow({scriptPath: ".claude/workflows/under.js", args: <dossiê>})`, com `args.criterios.prob_minima = 0.80`,
   `args.under.max_pesquisa = 5` e `args.aprofundar.modelo_agentes = null`. Por jogo: estatístico independente →
   pesquisador de contexto → cético. O workflow para no primeiro que derruba e devolve `top`, `selo_elite` e
   `elite_falhas` de cada jogo.

## 4. Selo elite (veredito)

`p_final` = a menor entre o modelo e a conta independente, mais os ajustes (±5 p.p.). O workflow calcula o selo
(`selo_elite`) com as regras abaixo; confira o resultado. Se o cético escreveu uma leitura menor, use a menor. Ganha o selo quem cumpre
**tudo**:

1. `p_final ≥ 0,80`.
2. Cético **não refutou** e com confiança `alta` ou `media`; pesquisa sem `derruba_pick`.
3. **H2H na linha exata** (lição 34): no máximo 1 estouro nos últimos 5 confrontos.
4. **Sem desfalque defensivo titular CONFIRMADO** (goleiro ou zagueiro).
5. **Fontes concordam:** modelo e conta independente a até 10 p.p.; pelo menos 2 fontes fora do Sofascore.
6. **Sem motivo de jogo aberto:** ninguém precisa vencer de qualquer jeito com ataque forte; ninguém precisa de
   saldo; sem técnico novo ofensivo; sem favorito goleador.
6b. **1X2 sem despencar:** nenhum time com a odd caindo 10% ou mais desde a abertura (lição 67). Confira de novo 1 a 2 h
   antes do jogo e avise o Daniel se cair.
7. **Escalação provável sem surpresa:** time misto ou reserva no ataque conta a favor; na defesa, contra.

## 4b. Recheca do 1X2 (Daniel, 23/10)

`python3 ferramentas/plataformas.py recheca --dossie <dossiê>` logo antes de entregar. CORTA sai do top (lição 67).
Repita 1 a 2 h antes de cada jogo e avise o Daniel se um entregue virar CORTA.

## 5. Ranking (as melhores chances e as melhores oportunidades)

1. Maior `p_final`.
2. Empate: mais folga (linha − xG somado).
3. Depois: menos estouros na cauda.
4. Depois: maior EV (selo 💰 quando a odd da bet365 ≥ odd mínima).

Entregue **no máximo 3**. Se só 1 ganhou o selo, mande 1.

## 6. Salvar, registrar e evoluir

1. `analises/AAAA-MM-DD-under-top.md`: o top (modelo → ajuste e motivo → chance final, folga, cauda, H2H, mercado),
   os que caíram e por quê (pré-filtro, mercado, selo), odd/EV e fontes.
2. `previsoes.py add-json` só com os entregues: `analise: "under_top"`, `mercado: "under_X.5"`, `lado: "casa"`, `prob`,
   `odd_minima`, `odd_casa` e `alertas`. Assim a calibração do top fica separada.
3. Lição nova do cético (`licao`) vai para `docs/licoes.md`. Lição que se repete vira filtro no `under.py` (com teste).
4. Commit e push, com mensagem em português.

## 7. Resposta (curta, para celular)

**🏆 Top under do dia**

| # | Jogo | Hora | Liga | Linha | Chance |
|---|---|---|---|---|---|

- Uma linha por jogo: por que é elite (folga, cauda, H2H) e o maior risco. 💰 se tiver valor.
- Lembrete: conferir a escalação cerca de 1 h antes.
- Uma linha de calibração do top, quando houver resolvidas: "Top até agora: X/Y (Z%) para W% previsto".
- Sem elite: só "Nenhum under elite hoje."
- Termine com quantos agentes o workflow usou.

**Notificação:** com pelo menos 1, mande `PushNotification` "🏆 Under top DD/MM: <jogo> menos de X.5 (NN%) (+N)".
Sem elite, não notifique.
