#!/usr/bin/env python3
"""Especialista em UNDER de gols (pedido do Daniel em 17/10): todos os jogos do dia,
só "menos de X.5 gols" com prob. ≥ 70% e valor, passando pelos requisitos de under.

Lê a peneira de todas as ligas (`varredura.py --todas --prob-min 0.70`), fica só com
os unders e confere, com o Sofascore (cache), o que o modelo de gols não vê sozinho:

- **cauda** (lição 33): nos últimos 7 jogos oficiais de cada time (todas as
  competições), quantas vezes o total passou da linha. Um time que estoura a linha
  com frequência derruba o under sozinho → sai;
- **taxa da liga**: quantos jogos da liga (temporada atual + fim da anterior) ficaram
  abaixo da linha. Muito abaixo da prob. do modelo → sai;
- **amostra da temporada passada** (lição 32): no início de temporada a amostra é de
  outro elenco → sai se quase nada for da temporada atual;
- **xG somado** dos dois times na condição: perto da linha → alerta;
- **favorito muito forte** (odd ≤ 1.30): risco de goleada → alerta;
- **frequência real** do under nas amostras (já vem da peneira).

Saída: `dados/cache/sofascore/peneira-<D>-under.json` (formato da peneira, com o
bloco `under` em cada candidato). O `dossie.py --sufixo under` lê esse arquivo.

Exemplos:
  python3 ferramentas/varredura.py --data 2026-10-18 --todas --prob-min 0.70 --chuva-informativa
  python3 ferramentas/under.py --data 2026-10-18
  python3 ferramentas/under.py --data 2026-10-18 --json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

import defesa as df
import nucleo as n
import varredura as v

UNDER_PADRAO = {
    "prob_min": 0.70,
    "cauda_jogos": 7,
    "cauda_folga": 0.15,          # estouro aceito = (1 − p) + folga
    "liga_folga": 0.15,           # taxa de under da liga ≥ p − folga
    "temporada_atual_min": 0.30,  # fração mínima da amostra na temporada atual
    "favorito_goleada_odd": 1.30,
    "xg_folga_linha": 0.6,        # alerta se o xG somado ≥ linha − folga
    "xg_margem_mercado": 0.02,    # lição 39: P(under) só com xG desta temporada ≥ mercado + margem
    "max_pesquisa": 6,
}


def config() -> tuple[dict, dict]:
    cfg = n.carregar_config()
    cfg["varredura"] = {**v.VARREDURA_PADRAO, **{k: x for k, x in cfg.get("varredura", {}).items() if not k.startswith("_")}}
    u = {**UNDER_PADRAO, **{k: x for k, x in cfg.get("under", {}).items() if not k.startswith("_")}}
    cfg["varredura"]["prob_triagem"] = u["prob_min"]
    return cfg, u


def total_90(e: dict) -> int | None:
    hs, as_ = v.placar(e, "home"), v.placar(e, "away")
    return None if hs is None or as_ is None else hs + as_


def cauda(eventos: list[dict], antes_ts: int, linha: float, qtd: int, palavras_amistoso: list[str]) -> dict:
    """Últimos `qtd` jogos oficiais encerrados antes de `antes_ts`: quantos passaram da linha."""
    tots = []
    for e in sorted(eventos, key=lambda e: e["startTimestamp"]):
        torneio = " ".join(str(x) for x in ((e.get("tournament") or {}).get("name"),
                                            ((e.get("tournament") or {}).get("uniqueTournament") or {}).get("name")))
        if (e.get("status", {}).get("type") != "finished" or e["startTimestamp"] >= antes_ts
                or any(p.lower() in torneio.lower() for p in palavras_amistoso)):
            continue
        t = total_90(e)
        if t is not None:
            tots.append(t)
    tots = tots[-qtd:]
    acima = sum(1 for t in tots if t > linha)
    return {"n": len(tots), "acima": acima, "frac": acima / len(tots) if tots else None, "totais": tots}


def estoura_cauda(fracs: list[float | None], p: float, folga: float) -> bool:
    """Lição 33: se um dos times passa da linha em mais de (1 − p) + folga dos jogos, o under cai."""
    return any(f is not None and f > (1 - p) + folga + 1e-9 for f in fracs)


def taxa_liga_under(totais: list[int] | None, linha: float) -> float | None:
    return sum(1 for t in totais if t < linha) / len(totais) if totais else None


def fracao_temporada(eventos: list[dict], temporada: int | None) -> float | None:
    if not eventos or temporada is None:
        return None
    return sum(1 for e in eventos if (e.get("season") or {}).get("id") == temporada) / len(eventos)


def xg_somado(xh: list[dict], xa: list[dict]) -> float | None:
    """Total esperado só pelo xG: (xG pró do mandante + xG cedido do visitante)/2 + o inverso."""
    m = lambda xs, k: (sum(x[k] for x in xs if x.get(k) is not None) / c  # noqa: E731
                       if (c := sum(1 for x in xs if x.get(k) is not None)) >= 0.7 * len(xs) and c else None)
    partes = [m(xh, "xg_f"), m(xa, "xg_a"), m(xa, "xg_f"), m(xh, "xg_a")]
    if any(x is None for x in partes):
        return None
    return (partes[0] + partes[1]) / 2 + (partes[2] + partes[3]) / 2


def under_xg_atual(xh: list[dict], xa: list[dict], ts_atual: set[int], linha: float, minimo: int = 4) -> dict | None:
    """Lição 39 (Lyngby, Pohang e Odense, 18/10): P(under) só com o xG dos jogos DESTA temporada na
    condição. Se fica perto do mercado, a vantagem do modelo era finalização ruim (que regride).
    Lição 46: se só um lado tem xG, o outro entra com gols (teste parcial); sem xG nos dois, None."""
    ha = [x for x in xh if x.get("t") in ts_atual]
    aa = [x for x in xa if x.get("t") in ts_atual]
    if min(len(ha), len(aa)) < minimo:
        return None

    def medias(xs):  # (pró, contra, usou_xg)
        com = [x for x in xs if x.get("xg_f") is not None and x.get("xg_a") is not None]
        if len(com) >= minimo:
            return sum(x["xg_f"] for x in com) / len(com), sum(x["xg_a"] for x in com) / len(com), True
        return sum(x["gf"] for x in xs) / len(xs), sum(x["ga"] for x in xs) / len(xs), False

    (hf, hc, hx), (af, ac, ax) = medias(ha), medias(aa)
    if not (hx or ax):
        return None
    lh, la = (hf + ac) / 2, (af + hc) / 2
    p, _ = v.total_gols(v.matriz(lh, la), linha, "under")
    gols = sum(x["gf"] + x["ga"] for x in ha + aa) / len(ha + aa)
    return {"p": round(p, 4), "lambda": [round(lh, 2), round(la, 2)], "gols_jogo": round(gols, 2),
            "xg_jogo": round(lh + la, 2), "n": [len(ha), len(aa)], "parcial": not (hx and ax)}


def requisitos(k: dict, extra: dict, u: dict) -> tuple[list[str], list[str]]:
    """(falhas, alertas) do under `k` com os dados extras do jogo."""
    p, linha = k["p"], float(k["linha"])
    falhas, alertas = [], []
    fc, ff = extra["cauda"]["casa"], extra["cauda"]["fora"]
    if estoura_cauda([fc["frac"], ff["frac"]], p, u["cauda_folga"]):
        pior = max((fc, "mandante"), (ff, "visitante"), key=lambda x: x[0]["frac"] or 0)
        falhas.append(f"cauda: o {pior[1]} passou de {linha} gols em {pior[0]['acima']} dos últimos {pior[0]['n']} oficiais")
    tl = extra.get("taxa_liga")
    if tl is not None and tl < p - u["liga_folga"]:
        falhas.append(f"liga: só {tl:.0%} dos jogos abaixo de {linha} (modelo {p:.0%})")
    ft = extra.get("temporada_atual")
    if ft is not None and ft < u["temporada_atual_min"]:
        falhas.append(f"amostra da temporada passada: só {ft:.0%} dos jogos são desta temporada (lição 32)")
    xa = extra.get("xg_atual")
    if xa:
        merc = k.get("justa_mercado")
        if xa["p"] < u["prob_min"]:
            falhas.append(f"teste só xG desta temporada: under {xa['p']:.0%} < {u['prob_min']:.0%} (lição 39)")
        elif merc is not None and xa["p"] < merc + u["xg_margem_mercado"]:
            falhas.append(f"teste só xG desta temporada: under {xa['p']:.0%} ≈ mercado {merc:.0%} — a vantagem é "
                          f"finalização ruim ({xa['gols_jogo']} gols x {xa['xg_jogo']} xG por jogo), que regride (lição 39)")
    xg = extra.get("xg_somado")
    if xg is not None and xg >= linha - u["xg_folga_linha"]:
        alertas.append(f"xG somado {xg:.2f} perto da linha {linha}")
    fav = extra.get("odd_favorito")
    if fav is not None and fav <= u["favorito_goleada_odd"]:
        alertas.append(f"favorito muito forte (odd {fav:.2f}): risco de goleada")
    if k.get("frequencia") is not None and k["frequencia"] < p - 0.10:
        alertas.append(f"frequência real do under nas amostras {k['frequencia']:.0%} (modelo {p:.0%})")
    return falhas, alertas


OBRIG = ("base", "incerteza", "dixon_coles")


def unders_do_jogo(info: dict, cfg: dict, u: dict) -> list[dict]:
    """Todas as linhas de under do jogo que batem a PROBABILIDADE (com ou sem valor): ≥ prob_min nas
    variantes obrigatórias, ≥ prob_min − tolerância nas outras, frequência real, regra 8 e taxa-base."""
    vs = info.get("variantes") or {}
    if not vs.get("base"):
        return []
    vc, pm = cfg["varredura"], u["prob_min"]
    xh, xa = info.get("amostras") or ([], [])
    base = info.get("taxa_base")
    out = []
    for chave, b in vs["base"].items():
        if b["mercado"] != "Match goals" or b["escolha"] != "Under" or b["odd"] < vc["odd_minima_mercado"]:
            continue
        if any(chave not in vs.get(o, {}) or vs[o][chave]["p"] < pm for o in OBRIG):
            continue
        outras = {k: var[chave]["p"] for k, var in vs.items() if k not in OBRIG and chave in var}
        if any(x < pm - vc["tolerancia_variantes"] for x in outras.values()):
            continue
        if b["p"] - b["justa_mercado"] > vc["regra8_pp"]:
            continue
        freq = v.frequencia(b, xh, xa)
        if freq is not None and freq < pm - vc["tolerancia_frequencia"]:
            continue
        if base and b["p"] >= 0.80:
            linha = float(b["linha"])
            if sum(1 for t in base["totais"] if t < linha) / len(base["totais"]) < b["p"] - 0.10:
                continue
        out.append({**b, "frequencia": freq, "variantes": {k: round(x, 3) for k, x in outras.items()},
                    "p_min": min([b["p"], *outras.values(), *(vs[o][chave]["p"] for o in OBRIG)]),
                    "com_valor": b["ev"] >= cfg["criterios"]["ev_minimo"]})
    return out


def extras_jogo(api: v.Sofascore, e: dict, info: dict, linha: float, cfg: dict, u: dict, palavras: list[str]) -> dict:
    th, ta = e["homeTeam"]["id"], e["awayTeam"]["id"]
    evh, eva = v.ultimos_eventos(api, th), v.ultimos_eventos(api, ta)
    ut, temporada = v.torneio_id(e), (e.get("season") or {}).get("id")
    qtd = cfg["varredura"]["jogos_amostra"]
    ch, _ = v.amostras_time(evh, th, ut, True, qtd)
    ca, _ = v.amostras_time(eva, ta, ut, False, qtd)
    xh, xa = info.get("amostras") or ([], [])
    odds = api.get(f"event/{e['id']}/odds/1/all", cache=None)
    ft = next((m for m in odds.get("markets", []) if m.get("marketName") == "Full time"), None)
    um_x_dois = [v.odd_decimal(c["fractionalValue"]) for c in ft["choices"]] if ft else []
    return {
        "cauda": {"casa": cauda(evh, e["startTimestamp"], linha, u["cauda_jogos"], palavras),
                  "fora": cauda(eva, e["startTimestamp"], linha, u["cauda_jogos"], palavras)},
        "taxa_liga": taxa_liga_under((info.get("taxa_base") or {}).get("totais"), linha),
        "temporada_atual": fracao_temporada(ch[-qtd:] + ca[-qtd:], temporada),
        "xg_somado": xg_somado(xh, xa),
        "xg_atual": under_xg_atual(xh, xa, {x["startTimestamp"] for x in ch + ca
                                            if (x.get("season") or {}).get("id") == temporada}, linha),
        "odd_favorito": min(um_x_dois) if um_x_dois else None,
        "um_x_dois": [round(x, 2) for x in um_x_dois],
        "lambda": [round(x, 2) for x in info["lambda"]] if info.get("lambda") else None,
    }


def linha_txt(i: int, k: dict) -> str:
    ex = k["under"]
    cauda_txt = f"cauda {ex['cauda']['casa']['acima']}/{ex['cauda']['casa']['n']} e {ex['cauda']['fora']['acima']}/{ex['cauda']['fora']['n']}"
    liga = f"liga {ex['taxa_liga']:.0%}" if ex.get("taxa_liga") is not None else "liga N/D"
    xg = f"xG {ex['xg_somado']:.2f}" if ex.get("xg_somado") is not None else "xG N/D"
    txt = (f"{i}) {k['hora']} {k['jogo']} [{k['competicao']}] · {k['rotulo']} · {k['p']:.0%} (pior {k['p_min']:.0%})"
           f" · mín {n.fmt_odd_min(k['odd_minima'])} · bet365 {k['odd']:.2f} (EV {k['ev']:+.0%}) · mercado {k['justa_mercado']:.0%}"
           f" · {cauda_txt} · {liga} · {xg}{'' if k.get('principal') else ' · (linha alternativa)'}")
    return txt + ("\n   alertas: " + "; ".join(ex["alertas"]) if ex["alertas"] else "")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", help="AAAA-MM-DD (padrão: hoje, Brasília)")
    p.add_argument("--entrada", default="todas", help="sufixo da peneira de entrada (padrão: todas)")
    p.add_argument("--varrer", action="store_true",
                   help="varre todos os jogos de novo e mapeia TODO under com prob ≥ prob_min, com ou sem valor (lista sem_valor com a odd mínima)")
    p.add_argument("--json", action="store_true")
    a = p.parse_args()
    cfg, u = config()
    data = a.data or datetime.now(v.FUSO_BR).date().isoformat()
    palavras = {**df.DEFESA_PADRAO, **cfg.get("defesa", {})}["palavras_amistoso"]
    api = v.Sofascore(v.CACHE_PADRAO, data)
    cache_liga: dict = {}
    pen: dict = {}

    def completar(e: dict, info: dict, k: dict) -> dict:
        ex = extras_jogo(api, e, info, float(k["linha"]), cfg, u, palavras)
        falhas, alertas = requisitos(k, ex, u)
        return {**k, "under": {**ex, "falhas": falhas, "alertas": alertas}, "passa": not falhas}

    if a.varrer:
        jogos = v.listar_jogos(api, data, None)
        sus = df.eventos_suspeitos(jogos)
        jogos = [e for e in jogos if e["id"] not in sus and not df.liga_nao_verificavel(e)]

        def um(e):
            try:
                info = v.analisar_jogo(api, e, cfg, cache_liga)
                base = {"hora": info["hora"], "jogo": info["jogo"], "competicao": info["competicao"], "id": e["id"]}
                return [completar(e, info, {**k, **base}) for k in unders_do_jogo(info, cfg, u)]
            except Exception:  # noqa: BLE001 — um jogo estranho não derruba a varredura
                return []
        res = [k for lista in v.em_paralelo(um, jogos, 6) for k in lista]
        contagem = {"jogos": len(jogos)}
    else:
        arq = v.CACHE_PADRAO / f"peneira-{data}-{a.entrada}.json"
        if not arq.exists():
            sys.exit(f"Sem {arq.name}. Rode antes: python3 ferramentas/varredura.py --data {data} --todas "
                     f"--prob-min {u['prob_min']} --chuva-informativa (ou use --varrer)")
        pen = json.loads(arq.read_text(encoding="utf-8"))
        contagem = pen.get("contagem")
        jogos_info: dict[int, tuple] = {}
        res = []
        for k in pen["candidatos"]:
            if k["mercado"] != "Match goals" or k["escolha"] != "Under":
                continue
            if k["id"] not in jogos_info:
                e = api.get(f"event/{k['id']}", cache=None).get("event") or {}
                jogos_info[k["id"]] = (e, v.analisar_jogo(api, e, cfg, cache_liga) if e.get("status", {}).get("type") == "notstarted" else None)
            e, info = jogos_info[k["id"]]
            vivo = next((x for x in unders_do_jogo(info, cfg, u) if (x["linha"], x["escolha"]) == (k["linha"], k["escolha"])), None) if info else None
            res.append(completar(e, info, {**k, **vivo}) if vivo else
                       {**k, "under": {"falhas": ["caiu na reavaliação"], "alertas": []}, "passa": False})
    for k in res:
        k["com_valor"] = k.get("com_valor", k["ev"] >= cfg["criterios"]["ev_minimo"])
        xa = (k.get("under") or {}).get("xg_atual")
        if k["com_valor"] and xa and xa["p"] * k["odd"] < 1:  # lição 39: o valor tem que sobreviver ao teste só xG
            k["com_valor"] = False
            k["under"]["alertas"].append(f"valor some no teste só xG desta temporada ({xa['p']:.0%} a {k['odd']:.2f})")
    # por jogo, a linha principal é a de maior EV entre as que passam nos requisitos
    for k in res:
        k["principal"] = k["passa"] and k is max((x for x in res if x["id"] == k["id"] and x["passa"]),
                                                  key=lambda x: (x["ev"], x["p"]))
    res.sort(key=lambda k: (not k["passa"], not k["com_valor"], not k.get("principal"), -k["p_min"], -k["ev"]))
    saida = {"data": data, "contagem": contagem, "consultado": datetime.now(v.FUSO_BR).strftime("%H:%M"),
             "prob_triagem": u["prob_min"], "ev_minimo": cfg["criterios"]["ev_minimo"], "under": u,
             "candidatos": [k for k in res if k["passa"] and k["com_valor"]],
             "sem_valor": [k for k in res if k["passa"] and not k["com_valor"]],
             "caidos": [k for k in res if not k["passa"]], "falhas_rede": api.falhas}
    out = v.CACHE_PADRAO / f"peneira-{data}-under.json"
    out.write_text(json.dumps(saida, ensure_ascii=False, default=str), encoding="utf-8")
    if a.json:
        print(json.dumps(saida, ensure_ascii=False, indent=1, default=str))
        return
    print(f"🧊 Under {data} — {(contagem or {}).get('jogos')} jogos · {len(res)} unders com {u['prob_min']:.0%}+ "
          f"→ {len(saida['candidatos'])} com valor e requisitos · {len(saida['sem_valor'])} batem a prob. mas sem valor na bet365")
    for i, k in enumerate(saida["candidatos"], 1):
        print(linha_txt(i, k))
    if saida["sem_valor"]:
        print("Batem a prob. e os requisitos, mas a bet365 paga abaixo da odd mínima (conferir a Betano):")
        for i, k in enumerate(saida["sem_valor"], 1):
            print(linha_txt(i, k))
    if saida["caidos"]:
        print("Caíram nos requisitos de under: " + " | ".join(f"{k['jogo']} {k['rotulo']}: {k['under']['falhas'][0]}" for k in saida["caidos"]))
    print(f"JSON: {out.relative_to(n.RAIZ)}")


if __name__ == "__main__":
    main()
