#!/usr/bin/env python3
"""O que a casa acredita: os mercados em que a própria casa aposta que o resultado sai (pedido do Daniel em 25/10).

"Vamos focar somente nas odds que a casa vê que vai vencer, procurar todos os jogos com calma e não usar créditos à
toa: achar os mercados em que a casa acredita que vai acertar, pelas odds ou por alguma informação."

A odd é a opinião da casa: odd baixa = a casa acha muito provável; odd caindo desde a abertura = a casa e o dinheiro
ficaram mais confiantes. O script varre TODOS os jogos do dia no 365Scores (odds do book do 365Scores, com a de
abertura; a bet365, e o book do 365Scores, que é um clone dela, quando a bet365 não vem), tira a margem de cada mercado e fica com as seleções em que:
  - a probabilidade da casa sem margem é ≥ prob_min;
  - a odd é ≥ odd_min (abaixo disso não paga a pena);
  - a casa ficou MAIS confiante: a odd caiu pelo menos queda_min desde a abertura (com queda_min 0, a odd não pode
    subir mais que subida_max; lição 16: odd subindo = a casa perdendo a confiança);
  - a margem do mercado é ≤ margem_max (margem alta = mercado pouco líquido, a casa se protege em vez de acreditar);
  - o outro lado do mesmo mercado não está despencando (queda ≥ queda_contra_max, lição 67);
  - o jogo é masculino, profissional, oficial e começa daqui a pelo menos minutos_antes.
Um jogo, uma seleção: a de maior probabilidade da casa. Ranking: probabilidade da casa → queda desde a abertura.
Só entram mercados que o `previsoes.py` resolve sozinho (vitória, dupla chance, gols, ambas marcam, handicap .5).

Sem agentes, sem créditos. Não é "valor": com a margem, o EV fica perto de −margem por construção. A aposta aqui é na
precisão da casa, e o registro (`--registrar`, analise "casa") mede se ela acerta o que promete.

Exemplos:
  python3 ferramentas/casa.py                              # hoje, critérios do config.json → casa
  python3 ferramentas/casa.py --data 2026-10-26 --prob-min 0.80
  python3 ferramentas/casa.py --json > /tmp/casa.json
  python3 ferramentas/casa.py --registrar                  # grava os entregues em dados/previsoes.csv
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import defesa as df  # noqa: E402
import nucleo as n  # noqa: E402
import plataformas as pl  # noqa: E402

CASA_PADRAO = {
    "prob_min": 0.75,          # probabilidade da casa sem margem
    "odd_min": 1.15,           # odd abaixo disso não entra
    "queda_min": 0.05,         # a casa ficou mais confiante: odd caiu pelo menos isso desde a abertura (3% é 1 tique)
    "subida_max": 0.03,        # (com queda_min 0) odd subindo mais que isso desde a abertura: a casa perdeu confiança
    "queda_contra_max": 0.10,  # outro lado do mercado caindo isso ou mais: dinheiro contra (lição 67)
    "margem_max": 0.08,        # margem alta = mercado pouco líquido, a casa se protege em vez de acreditar
    "minutos_antes": 30,
    "max_entrega": 10,
}

ROTULO_1X2 = {"1": "casa", "2": "fora"}
# o 365Scores mostra a bet365 para o país 1 e o book próprio (clone da bet365) para o Brasil (21)
FONTES = ((1, 14, "bet365"), (21, 16, "365Scores"))
FEMININO = ["(W)", "Women", "Frauen", "Femenil", "Feminin", "Femminile", "Féminine", "NWSL", "Liga F", "WSL",
            "Damallsvenskan", "Toppserien", "Kvinde"]


def sem_margem(odds: list[float]) -> list[float]:
    """Probabilidades sem margem pelo método proporcional (1/odd normalizado)."""
    inv = [1 / o for o in odds]
    s = sum(inv)
    return [x / s for x in inv]


def _linha_num(ln: dict) -> float | None:
    for txt in (ln.get("internalOptionValue"), ln.get("internalOption")):
        m = re.search(r"[-+]?\d+(?:\.\d+)?", str(txt or ""))
        if m:
            return float(m.group(0))
    return None


def _fmt_hcp(x: float) -> str:
    return f"{x:+.1f}"


def selecoes(ln: dict, casa: str, fora: str) -> list[dict]:
    """Uma linha do 365Scores (bets/lines) → seleções que o previsoes.py resolve, com prob. da casa e movimento.

    Cada seleção: mercado e lado no formato do previsoes.py, rótulo em português, odd agora e na abertura,
    p_casa (sem margem), queda (1 − agora/abertura; positiva = odd caindo) e a queda do lado oposto mais forte."""
    ops = [o for o in ln.get("options") or [] if (o.get("rate") or {}).get("decimal", 0) > 1]
    if len(ops) < 2 or len(ops) != len(ln.get("options") or []):
        return []
    odds = [o["rate"]["decimal"] for o in ops]
    abert = [(o.get("originalRate") or {}).get("decimal") or o["rate"]["decimal"] for o in ops]
    tipo = ln.get("lineTypeId")
    vezes = 2 if tipo == 14 else 1  # dupla chance: as 3 opções se sobrepõem e somam 200%
    ps = [vezes * x for x in sem_margem(odds)]
    pa = [vezes * x for x in sem_margem(abert)]
    margem = sum(1 / o for o in odds) / vezes - 1
    nome = (ln.get("lineType") or {}).get("name") or ""
    linha = _linha_num(ln)
    quedas = [1 - o / a for o, a in zip(odds, abert)]
    saida = []
    for i, o in enumerate(ops):
        op = str(o.get("name"))
        merc = lado = rot = None
        if tipo == 1 and op in ROTULO_1X2:
            lado = ROTULO_1X2[op]
            merc, rot = "vence", f"vitória do {casa if lado == 'casa' else fora}"
        elif tipo == 14:
            if op == "1X":
                merc, lado, rot = "dupla_chance", "casa", f"{casa} ou empate"
            elif op == "X2":
                merc, lado, rot = "dupla_chance", "fora", f"{fora} ou empate"
            elif op == "12":
                merc, lado, rot = "sem_empate", "casa", "não termina empatado"
        elif tipo == 3 and linha is not None and op in ("Over", "Under"):
            merc, lado = f"{op.lower()}_{linha:g}", "casa"
            rot = f"{'mais' if op == 'Over' else 'menos'} de {linha:g} gols"
        elif tipo == 11 and linha is not None and abs(linha * 2) % 2 == 1 and op in ("Home", "Away"):
            hcp = linha if op == "Home" else -linha  # a linha do 365Scores é a do mandante
            lado = "casa" if op == "Home" else "fora"
            merc, rot = f"handicap_{_fmt_hcp(hcp)}", f"{casa if lado == 'casa' else fora} handicap {_fmt_hcp(hcp)}"
        elif "both teams" in nome.lower() and op.lower() in ("yes", "no"):
            merc, lado = ("ambas_sim" if op.lower() == "yes" else "ambas_nao"), "casa"
            rot = "ambas marcam" if op.lower() == "yes" else "ambas não marcam"
        if not merc:
            continue
        contra = max((q for j, q in enumerate(quedas) if j != i), default=0.0)
        saida.append({"mercado": merc, "lado": lado, "rotulo": rot, "tipo": nome, "odd": odds[i], "odd_abertura": abert[i],
                      "p_casa": round(ps[i], 4), "p_abertura": round(pa[i], 4), "margem": round(margem, 4),
                      "queda": round(quedas[i], 4), "queda_contra": round(contra, 4)})
    return saida


def motivo_fora(s: dict, c: dict) -> str | None:
    """Por que a seleção não entra (None = entra)."""
    if s["p_casa"] < c["prob_min"]:
        return f"casa dá {s['p_casa']:.0%} (< {c['prob_min']:.0%})"
    if s["odd"] < c["odd_min"]:
        return f"odd {s['odd']} abaixo de {c['odd_min']}"
    if -s["queda"] > c["subida_max"]:
        return f"odd subiu {-s['queda']:.0%} desde a abertura ({s['odd_abertura']} → {s['odd']})"
    if s["queda"] < c["queda_min"]:
        return f"odd não caiu {c['queda_min']:.0%} desde a abertura ({s['odd_abertura']} → {s['odd']})"
    if s["margem"] > c["margem_max"]:
        return f"margem de {s['margem']:.1%} (> {c['margem_max']:.0%})"
    if s["queda_contra"] >= c["queda_contra_max"]:
        return f"o outro lado caiu {s['queda_contra']:.0%} desde a abertura"
    return None


def melhor_do_jogo(sels: list[dict]) -> dict | None:
    """Um jogo, uma seleção: a de maior probabilidade da casa; empate → a que mais caiu."""
    return max(sels, key=lambda s: (s["p_casa"], s["queda"])) if sels else None


def ordenar(itens: list[dict]) -> list[dict]:
    return sorted(itens, key=lambda x: (-x["sel"]["p_casa"], -x["sel"]["queda"], x["hora"]))


def config() -> dict:
    cfg = n.carregar_config()
    return {**CASA_PADRAO, **{k: x for k, x in cfg.get("casa", {}).items() if not k.startswith("_")}}


def varrer(data: str, c: dict) -> dict:
    api = pl.S365(data, pasta=None)  # odds de agora, sem cache
    jogos = api.jogos()
    agora = datetime.now(pl.BRT) + timedelta(minutes=c["minutos_antes"])
    alvos, fora_nivel = [], 0
    for g in jogos:
        if g.get("statusGroup") != pl.AGENDADO or datetime.fromisoformat(g["startTime"]) < agora:
            continue
        casa, fora = g["homeCompetitor"]["name"], g["awayCompetitor"]["name"]
        comp = g.get("competitionDisplayName") or ""
        if pl.amistoso(g) or df.nivel_base([comp], df.DEFESA_PADRAO["palavras_base"] + FEMININO, [casa, fora]):
            fora_nivel += 1
            continue
        if (g.get("odds") or {}).get("options"):
            alvos.append(g)

    def linhas(g):
        for pais, book, nome in FONTES:
            lns = [ln for ln in api.get("bets/lines/", games=g["id"], userCountryId=pais).get("lines", [])
                   if ln.get("bookmakerId") == book and ln.get("gameId") == g["id"]]
            if lns:
                return g, lns, nome
        return g, [], None

    with ThreadPoolExecutor(max_workers=8) as ex:
        res = list(ex.map(linhas, alvos))
    itens, descartes = [], []
    for g, lns, fonte in res:
        casa, fora = g["homeCompetitor"]["name"], g["awayCompetitor"]["name"]
        sels = [s for ln in lns for s in selecoes(ln, casa, fora)]
        boas, motivos = [], []
        for s in sels:
            m = motivo_fora(s, c)
            (motivos if m else boas).append(m or s)
        base = {"id_365": g["id"], "evento": f"365-{g['id']}", "hora": pl.hora_br(g), "jogo": f"{casa} x {fora}",
                "competicao": g.get("competitionDisplayName"), "pais": g.get("_pais"), "fonte": fonte}
        best = melhor_do_jogo(boas)
        if best:
            itens.append({**base, "sel": best, "outras": [s for s in boas if s is not best]})
        elif sels:
            top = melhor_do_jogo(sels)
            if top["p_casa"] >= c["prob_min"]:
                descartes.append({**base, "sel": top, "motivo": motivo_fora(top, c)})
    itens = ordenar(itens)
    return {"data": data, "consultado": datetime.now(pl.BRT).strftime("%H:%M"), "criterios": c,
            "jogos_dia": len(jogos), "fora_nivel": fora_nivel, "com_linhas": len(alvos), "falhas": api.falhas,
            "itens": itens, "descartes": sorted(descartes, key=lambda x: -x["sel"]["p_casa"])}


def registrar(saida: dict, qtd: int) -> list[dict]:
    import previsoes as pv
    linhas = pv.ler()
    feitos = []
    for x in saida["itens"][:qtd]:
        s = x["sel"]
        alertas = [f"odd {s['odd_abertura']} → {s['odd']}", f"margem {s['margem']:.1%}"]
        nv = pv.normalizar({"data": saida["data"], "hora": x["hora"], "evento": x["evento"], "jogo": x["jogo"],
                            "competicao": f"{x['pais']} · {x['competicao']}", "nivel": "pro", "analise": "casa",
                            "mercado": s["mercado"], "lado": s["lado"], "prob": s["p_casa"], "odd_casa": s["odd"],
                            "alertas": alertas, "obs": f"365Scores: {s['rotulo']}"})
        feitos.append(pv.adicionar(linhas, nv))
    pv.salvar(linhas)
    return feitos


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", default=datetime.now(pl.BRT).strftime("%Y-%m-%d"))
    p.add_argument("--prob-min", type=float)
    p.add_argument("--odd-min", type=float)
    p.add_argument("--max", type=int, help="quantos entregar (padrão: config.json → casa.max_entrega)")
    p.add_argument("--registrar", action="store_true", help="grava os entregues em dados/previsoes.csv (analise casa)")
    p.add_argument("--json", action="store_true")
    a = p.parse_args()
    c = config()
    if a.prob_min is not None:
        c["prob_min"] = a.prob_min
    if a.odd_min is not None:
        c["odd_min"] = a.odd_min
    qtd = a.max or c["max_entrega"]
    saida = varrer(a.data, c)
    if a.registrar:
        for x in registrar(saida, qtd):
            print(f"registrada #{x['id']} {x['jogo']} — {x['mercado']} ({x['lado']})", file=sys.stderr)
    if a.json:
        print(json.dumps(saida, ensure_ascii=False, indent=1))
        return
    print(f"🏦 O que a casa acredita — {saida['data']} ({saida['consultado']}): {saida['jogos_dia']} jogos no dia, "
          f"{saida['com_linhas']} com odds vistos, {len(saida['itens'])} passam "
          f"(casa ≥ {c['prob_min']:.0%}, odd ≥ {c['odd_min']}, odd caindo {c['queda_min']:.0%}+, margem ≤ {c['margem_max']:.0%})")
    for i, x in enumerate(saida["itens"][:qtd], 1):
        s = x["sel"]
        mov = f"caiu {s['queda']:.0%}" if s["queda"] >= 0.005 else ("subiu " + f"{-s['queda']:.0%}" if s["queda"] <= -0.005 else "parada")
        print(f"{i}) {x['hora']} {x['jogo']} [{x['pais']} · {x['competicao']}] · {s['rotulo']} · casa {s['p_casa']:.0%} · "
              f"odd {s['odd']} (abriu {s['odd_abertura']}, {mov}){' 📉' if s['queda'] >= 0.05 else ''}")
    if len(saida["itens"]) > qtd:
        print(f"... e mais {len(saida['itens']) - qtd} (use --max ou --json)")
    if saida["falhas"]:
        print(f"⚠️ {saida['falhas']} consultas ao 365Scores falharam — rode de novo.")


if __name__ == "__main__":
    main()
