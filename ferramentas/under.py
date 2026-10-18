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
    xg = extra.get("xg_somado")
    if xg is not None and xg >= linha - u["xg_folga_linha"]:
        alertas.append(f"xG somado {xg:.2f} perto da linha {linha}")
    fav = extra.get("odd_favorito")
    if fav is not None and fav <= u["favorito_goleada_odd"]:
        alertas.append(f"favorito muito forte (odd {fav:.2f}): risco de goleada")
    if k.get("frequencia") is not None and k["frequencia"] < p - 0.10:
        alertas.append(f"frequência real do under nas amostras {k['frequencia']:.0%} (modelo {p:.0%})")
    return falhas, alertas


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
        "odd_favorito": min(um_x_dois) if um_x_dois else None,
        "um_x_dois": [round(x, 2) for x in um_x_dois],
        "lambda": [round(x, 2) for x in info["lambda"]] if info.get("lambda") else None,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", help="AAAA-MM-DD (padrão: hoje, Brasília)")
    p.add_argument("--entrada", default="todas", help="sufixo da peneira de entrada (padrão: todas)")
    p.add_argument("--json", action="store_true")
    a = p.parse_args()
    cfg, u = config()
    data = a.data or datetime.now(v.FUSO_BR).date().isoformat()
    arq = v.CACHE_PADRAO / f"peneira-{data}-{a.entrada}.json"
    if not arq.exists():
        sys.exit(f"Sem {arq.name}. Rode antes: python3 ferramentas/varredura.py --data {data} --todas "
                 f"--prob-min {u['prob_min']} --chuva-informativa")
    pen = json.loads(arq.read_text(encoding="utf-8"))
    unders = [k for k in pen["candidatos"] if k["mercado"] == "Match goals" and k["escolha"] == "Under"]
    palavras = {**df.DEFESA_PADRAO, **cfg.get("defesa", {})}["palavras_amistoso"]
    api = v.Sofascore(v.CACHE_PADRAO, data)
    cache_liga: dict = {}
    jogos: dict[int, tuple] = {}

    def avaliar(k: dict) -> dict:
        if k["id"] not in jogos:
            e = api.get(f"event/{k['id']}", cache=None).get("event") or {}
            jogos[k["id"]] = (e, v.analisar_jogo(api, e, cfg, cache_liga) if e.get("status", {}).get("type") == "notstarted" else None)
        e, info = jogos[k["id"]]
        if not info:
            return {**k, "under": {"falhas": ["jogo já começou ou não encontrado"], "alertas": []}, "passa": False}
        vivo = next((x for x in info["candidatos"] if (x["mercado"], x["linha"], x["escolha"]) == (k["mercado"], k["linha"], k["escolha"])), None)
        if not vivo:
            return {**k, "under": {"falhas": [f"caiu na reavaliação: {info.get('motivo') or 'sem valor agora'}"], "alertas": []}, "passa": False}
        ex = extras_jogo(api, e, info, float(k["linha"]), cfg, u, palavras)
        falhas, alertas = requisitos(vivo, ex, u)
        return {**k, **{c: vivo[c] for c in ("p", "odd", "ev", "odd_minima", "justa_mercado", "frequencia", "p_min")},
                "under": {**ex, "falhas": falhas, "alertas": alertas}, "passa": not falhas}

    res = [avaliar(k) for k in unders]  # poucos jogos: sequencial, para reaproveitar o cache do jogo
    # por jogo, a linha principal é a de maior EV entre as que passam
    for k in res:
        k["principal"] = k["passa"] and k is max((x for x in res if x["id"] == k["id"] and x["passa"]),
                                                  key=lambda x: (x["ev"], x["p"]))
    res.sort(key=lambda k: (not k["passa"], k.get("nivel") == "base", not k.get("principal"), -k["p"], -k["ev"]))
    saida = {**{c: pen.get(c) for c in ("data", "prob_triagem", "ev_minimo", "contagem")},
             "consultado": datetime.now(v.FUSO_BR).strftime("%H:%M"), "peneira_das": pen.get("consultado"),
             "under": u, "candidatos": [k for k in res if k["passa"]], "caidos": [k for k in res if not k["passa"]],
             "descartes": pen.get("descartes"), "falhas_rede": api.falhas}
    out = v.CACHE_PADRAO / f"peneira-{data}-under.json"
    out.write_text(json.dumps(saida, ensure_ascii=False, default=str), encoding="utf-8")
    if a.json:
        print(json.dumps(saida, ensure_ascii=False, indent=1, default=str))
        return
    print(f"🧊 Under {data} — {len(unders)} unders com {u['prob_min']:.0%}+ e valor na peneira "
          f"({(pen.get('contagem') or {}).get('jogos')} jogos) → {len(saida['candidatos'])} passam nos requisitos")
    for i, k in enumerate(saida["candidatos"], 1):
        ex = k["under"]
        cauda_txt = f"cauda {ex['cauda']['casa']['acima']}/{ex['cauda']['casa']['n']} e {ex['cauda']['fora']['acima']}/{ex['cauda']['fora']['n']}"
        liga = f"liga {ex['taxa_liga']:.0%}" if ex.get("taxa_liga") is not None else "liga N/D"
        xg = f"xG {ex['xg_somado']:.2f}" if ex.get("xg_somado") is not None else "xG N/D"
        print(f"{i}) {k['hora']} {k['jogo']} [{k['competicao']}] · {k['rotulo']} · {k['p']:.0%} · mín {n.fmt_odd_min(k['odd_minima'])}"
              f" · bet365 {k['odd']:.2f} (EV {k['ev']:+.0%}) · {cauda_txt} · {liga} · {xg}{'' if k.get('principal') else ' · (linha alternativa)'}")
        if ex["alertas"]:
            print("   alertas: " + "; ".join(ex["alertas"]))
    if saida["caidos"]:
        print("Caíram nos requisitos: " + " | ".join(f"{k['jogo']} {k['rotulo']}: {k['under']['falhas'][0]}" for k in saida["caidos"]))
    print(f"JSON: {out.relative_to(n.RAIZ)}")


if __name__ == "__main__":
    main()
