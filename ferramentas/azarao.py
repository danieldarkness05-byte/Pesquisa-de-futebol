#!/usr/bin/env python3
"""Azarão forte: jogos em que o azarão (pior odd) tem boa chance de NÃO PERDER.

Só Python (não gasta créditos). Usa a mesma base do defesa.py (tabelas casa/fora,
amostras na condição, forma, mercado, filtros de dado ruim), olhando para o lado do azarão:

1. **Triagem** de todos os jogos do dia com odds e tabela casa/fora. Passa quando o azarão
   (odd de vitória ≥ `odd_azarao_min`) rende na condição dele quase tanto quanto o favorito
   na dele (pontos por jogo), tem defesa sólida na condição e ataque razoável.
2. **Aprofundamento**: últimos jogos na condição, frequência real de "não perdeu", forma
   (o azarão precisa de `forma_pontos_min` nos últimos 5 oficiais), calendário, mercado.
3. **Mercados do azarão**: dupla chance (empate ou vitória), empate anula e vitória.
   Probabilidade = menor entre tabela, médias gerais, λ por gols e λ gols+xG, com Poisson
   simples e Dixon-Coles (vale a menor), limitada pela frequência real + tolerância.
   Valor contra a odd bet365 e regra 8 contra o 1X2 sem margem.

Exemplos:
  python3 ferramentas/azarao.py                      # hoje, todas as ligas
  python3 ferramentas/azarao.py --data 2026-10-16 --curto
  python3 ferramentas/azarao.py --ids 15171700       # só esses jogos (pula a triagem)

O JSON completo fica em dados/cache/sofascore/azarao-AAAA-MM-DD.json.
Odds: bet365 via Sofascore — NÃO são da Betano. Confira a odd mínima no app.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import date, datetime

import defesa as df
import nucleo as n
import varredura as v

AZARAO_PADRAO = {
    "odd_azarao_min": 2.2,
    "ppg_folga": 0.25,
    "defesa_az_max": 1.10,
    "ataque_az_min": 0.85,
    "forma_pontos_min": 7,
    "forma_jogos": 5,
    "amostra_minima_tabela": 4,
    "amostra_boa": 5,
    "jogos_amostra": 10,
    "max_aprofundar": 15,
    "max_pesquisa": 4,
    "max_resposta": 4,
    "encolhimento_jogos": 4,
    "incerteza_sigma": 0.15,
    "tolerancia_frequencia": 0.05,
    "regra8_pp": 0.10,
    "ataque_fav_risco": 1.4,
    "sorte_xg": 0.5,
}


def config() -> tuple[dict, dict, dict]:
    cfg, d_def = df.config()
    a = dict(AZARAO_PADRAO)
    a.update({k: val for k, val in cfg.get("azarao", {}).items() if not k.startswith("_")})
    return cfg, d_def, a


# ---------------------------------------------------------------------------
# Funções puras (testadas)
# ---------------------------------------------------------------------------

def ppg(row: dict) -> float | None:
    """Pontos por jogo de uma linha de tabela (vitória 3, empate 1)."""
    m = row.get("matches") or 0
    if not m:
        return None
    if row.get("wins") is not None and row.get("draws") is not None:
        return (3 * row["wins"] + row["draws"]) / m
    return (row.get("points") or 0) / m


def ppg_amostra(xs: list[dict]) -> float | None:
    if not xs:
        return None
    return sum(3 if x["gf"] > x["ga"] else 1 if x["gf"] == x["ga"] else 0 for x in xs) / len(xs)


def passa_triagem_azarao(odd_az: float, ppg_az: float | None, ppg_fav: float | None,
                         ind_def_az: float | None, ind_atq_az: float | None, a: dict) -> bool:
    """Azarão de verdade (odd alta) que rende na condição quase como o favorito, com defesa
    sólida e algum ataque."""
    return (odd_az >= a["odd_azarao_min"] and None not in (ppg_az, ppg_fav, ind_def_az, ind_atq_az)
            and ppg_az >= ppg_fav - a["ppg_folga"] and ind_def_az <= a["defesa_az_max"]
            and ind_atq_az >= a["ataque_az_min"])


def frequencias_azarao(az: list[dict], fav: list[dict]) -> dict:
    """Frequência real: azarão não perdeu/venceu na condição dele; favorito não venceu/perdeu na dele."""
    def f(xs, cond):
        return sum(1 for x in xs if cond(x)) / len(xs) if xs else None
    return {"az_nao_perde": f(az, lambda x: x["gf"] >= x["ga"]), "az_vence": f(az, lambda x: x["gf"] > x["ga"]),
            "fav_nao_vence": f(fav, lambda x: x["gf"] <= x["ga"]), "fav_perde": f(fav, lambda x: x["gf"] < x["ga"])}


def freq_mercado_az(fr: dict, chave: str) -> float | None:
    pares = {"az_dc": ("az_nao_perde", "fav_nao_vence"), "az_vence": ("az_vence", "fav_perde")}
    vals = [fr.get(k) for k in pares.get(chave, ())]
    vals = [x for x in vals if x is not None]
    return sum(vals) / len(vals) if vals else None


def ev_empate_anula(p_vence: float, p_empate: float, odd: float) -> float:
    """EV do empate anula: vitória paga a odd, empate devolve a aposta."""
    return p_vence * odd + p_empate - 1


def probs_lado(lh: float, la: float, lado_casa: bool, rho: float, sigma: float) -> dict:
    """P(vitória), P(empate), P(não perde) do lado escolhido (mandante se lado_casa)."""
    m = v.matriz(lh, la, rho, sigma)
    r = v.resultado(m)
    vence = r["1"] if lado_casa else r["2"]
    return {"az_vence": vence, "empate": r["X"], "az_dc": vence + r["X"]}


def lambdas_amostra(xh: list[dict], xaw: list[dict], liga: tuple[float, float], k: float) -> dict:
    """λ pelas amostras na condição (mandante, visitante): gols, mix e só xG.
    A variante "xg" é o teste de chão da lição 24: tira a sorte defensiva e a finalização
    (Henan x Tianjin, 16/10: gols 61%, xG 48%, mercado 49%). Mix e xG exigem xG nos dois lados."""
    if min(len(xh), len(xaw)) < 3:
        return {}
    lams = {"gols": v.gols_esperados(xh, xaw, liga, k, "gols")}
    xg = v.gols_esperados(xh, xaw, liga, k, "xg")
    if xg:
        lams["mix"] = v.gols_esperados(xh, xaw, liga, k, "mix")
        lams["xg"] = xg
    return {m: lam for m, lam in lams.items() if lam}


def alertas_azarao(info: dict, a: dict) -> list[str]:
    al = []
    az, fv = info["azarao_amostra"], info["favorito_amostra"]
    liga_fav = info["liga"]["casa"] if info["fav_casa"] else info["liga"]["fora"]
    if fv.get("gf") is not None and liga_fav and fv["gf"] / liga_fav >= a["ataque_fav_risco"]:
        al.append(f"⚠️ RISCO: favorito ataca muito na condição ({fv['gf']:.2f}/j = ×{fv['gf'] / liga_fav:.2f} da média)")
    if az.get("ga") is not None and az.get("xg_contra") is not None and az["xg_contra"] - az["ga"] >= a["sorte_xg"]:
        al.append(f"defesa do azarão com sorte: sofre {az['ga']:.2f} com xG cedido de {az['xg_contra']:.2f} (regressão provável)")
    if fv.get("gf") is not None and fv.get("xg_pro") is not None and fv["xg_pro"] - fv["gf"] >= a["sorte_xg"]:
        al.append(f"favorito marca abaixo do xG ({fv['gf']:.2f} x {fv['xg_pro']:.2f}): pode melhorar")
    if min(az.get("n", 0), fv.get("n", 0)) < a["amostra_boa"]:
        al.append(f"amostra pequena ({az.get('n', 0)}/{fv.get('n', 0)} jogos na condição)")
    if info.get("nivel_base"):
        al.append("liga amadora/base/reserva: dado mais fraco e pouca chance de ter na Betano")
    if info.get("editado"):
        al.append("temporada editada à mão no Sofascore: confira data e placares numa 2ª fonte")
    cal = info.get("calendario_azarao") or {}
    if cal.get("jogos_janela", 0) >= 3:
        al.append(f"azarão com {cal['jogos_janela']} jogos em ±7 dias: rodízio possível")
    ff = info.get("forma_favorito") or {}
    if ff.get("n") and ff["pts"] >= 12:
        al.append(f"favorito em grande fase ({ff['seq']}, {ff['pts']} pts)")
    for r8 in info.get("regra8_mercados") or []:
        al.append(r8)
    if info.get("motivo"):
        al.append(info["motivo"])
    return al


# ---------------------------------------------------------------------------
# Triagem e aprofundamento
# ---------------------------------------------------------------------------

def triar(api: v.Sofascore, e: dict, a: dict, motivos: Counter, cache: dict) -> dict | None:
    ut, s = v.torneio_id(e), (e.get("season") or {}).get("id")
    if not ut or not s:
        motivos["sem torneio/temporada"] += 1
        return None
    if df.liga_nao_verificavel(e):
        motivos["liga não verificável"] += 1
        return None
    if (ut, s) not in cache:
        cache[(ut, s)] = tuple(df.grupos_tabela(api, ut, s, t) for t in ("home", "away", "total"))
    h, aw = e["homeTeam"]["id"], e["awayTeam"]["id"]
    th, ta, tt = (df.escolher_grupo(g, (h, aw), e["tournament"].get("name")) for g in cache[(ut, s)])
    if not th or not ta or h not in th or aw not in ta:
        motivos["sem tabela casa/fora (copa, amistoso, seleção)"] += 1
        return None
    jogos = sum(r.get("matches") or 0 for r in th.values())
    if not jogos:
        motivos["tabela vazia"] += 1
        return None
    lh = sum(r.get("scoresFor") or 0 for r in th.values()) / jogos
    la = sum(r.get("scoresAgainst") or 0 for r in th.values()) / jogos
    odds = df.odds_evento(api, e["id"])
    o = odds.get("1x2")
    if not o:
        motivos["sem odds (sem valor para medir)"] += 1
        return None
    az_casa = o[0] > o[2]
    rh, ra = th[h], ta[aw]
    if min(rh["matches"], ra["matches"]) < a["amostra_minima_tabela"]:
        motivos["amostra < mínimo na condição"] += 1
        return None
    az, fv = (rh, ra) if az_casa else (ra, rh)
    l_az_gf = lh if az_casa else la          # gols de quem joga na condição do azarão
    l_az_ga = la if az_casa else lh          # gols sofridos na condição do azarão = gols do rival
    ppg_az, ppg_fav = ppg(az), ppg(fv)
    ind_def = df.indice(az["scoresAgainst"] / az["matches"], l_az_ga)
    ind_atq = df.indice(az["scoresFor"] / az["matches"], l_az_gf)
    motivos["analisado"] += 1
    odd_az = o[0] if az_casa else o[2]
    if not passa_triagem_azarao(odd_az, ppg_az, ppg_fav, ind_def, ind_atq, a):
        return None
    casa, fora = e["homeTeam"]["name"], e["awayTeam"]["name"]
    cat = (e["tournament"].get("category") or {}).get("name")
    tot_j = sum(r.get("matches", 0) for r in tt.values())
    empates = (sum(r.get("draws", 0) for r in tt.values()) / tot_j) if tot_j else None
    return {
        "id": e["id"], "inicio": e["startTimestamp"], "hora": v.hora_br(e["startTimestamp"]).strftime("%H:%M"),
        "jogo": f"{casa} x {fora}", "pais": cat, "competicao": e["tournament"].get("name"), "ut": ut, "temporada": s,
        "casa": casa, "fora": fora, "ids": {"casa": h, "fora": aw},
        "az_casa": az_casa, "fav_casa": not az_casa,
        "azarao": casa if az_casa else fora, "favorito": fora if az_casa else casa,
        "odds": o, "odds_ini": odds.get("1x2_ini"), "mercado_odds": odds,
        "liga": {"casa": round(lh, 3), "fora": round(la, 3), "empates": round(empates, 3) if empates is not None else None},
        "tabela": {"casa": {k: rh.get(k) for k in ("matches", "wins", "draws", "losses", "scoresFor", "scoresAgainst")},
                   "fora": {k: ra.get(k) for k in ("matches", "wins", "draws", "losses", "scoresFor", "scoresAgainst")}},
        "tabela_geral": {lado: ({k: tt[t][k] for k in ("matches", "scoresFor", "scoresAgainst")}
                                if t in tt and all(tt[t].get(k) is not None for k in ("matches", "scoresFor", "scoresAgainst")) else None)
                         for lado, t in (("casa", h), ("fora", aw))},
        "ppg_az_cond": round(ppg_az, 2), "ppg_fav_cond": round(ppg_fav, 2),
        "ind_def_az": ind_def, "ind_atq_az": ind_atq, "odd_az": odd_az,
        "pos_total": {lado: (tt.get(t) or {}).get("position") for lado, t in (("casa", h), ("fora", aw))},
        "nivel_base": df.nivel_base([cat, e["tournament"].get("name")], df.DEFESA_PADRAO["palavras_base"], [casa, fora]),
        "editado": bool((e.get("season") or {}).get("editor")),
        "pontuacao": round((ppg_az - ppg_fav + 1) * (2 - ind_def), 3),
    }


def aprofundar(api: v.Sofascore, info: dict, cfg: dict, d_def: dict, a: dict, dia: str, chuva: bool) -> dict:
    ut, az_casa = info["ut"], info["az_casa"]
    h, aw = info["ids"]["casa"], info["ids"]["fora"]
    aid, fid = (h, aw) if az_casa else (aw, h)
    eva, evf = v.ultimos_eventos(api, aid), v.ultimos_eventos(api, fid)
    qtd = a["jogos_amostra"]
    xa = df.amostra(api, eva, aid, ut, az_casa, qtd)
    xf = df.amostra(api, evf, fid, ut, not az_casa, qtd)
    info["azarao_amostra"], info["favorito_amostra"] = df.resumo_amostra(xa), df.resumo_amostra(xf)
    info["azarao_amostra"]["ppg"] = round(ppg_amostra(xa), 2) if xa else None
    info["favorito_amostra"]["ppg"] = round(ppg_amostra(xf), 2) if xf else None
    info["frequencias"] = {k: (round(x, 3) if isinstance(x, float) else x) for k, x in frequencias_azarao(xa, xf).items()}
    info["forma_azarao"] = df.forma(eva, aid, info["inicio"], a["forma_jogos"], d_def["palavras_amistoso"])
    info["forma_favorito"] = df.forma(evf, fid, info["inicio"], a["forma_jogos"], d_def["palavras_amistoso"])
    prox = api.get(f"team/{aid}/events/next/0").get("events", [])
    info["calendario_azarao"] = df.calendario(eva, prox, info["inicio"], 7)

    # variantes (todas do ponto de vista do azarão); Dixon-Coles com ρ 0 e −0,10: vale a menor
    sig, tb, lg = a["incerteza_sigma"], info["tabela"], info["liga"]
    lams = {"tabela": n.lambdas_por_medias(tb["casa"]["scoresFor"] / tb["casa"]["matches"],
                                           tb["casa"]["scoresAgainst"] / tb["casa"]["matches"],
                                           tb["fora"]["scoresFor"] / tb["fora"]["matches"],
                                           tb["fora"]["scoresAgainst"] / tb["fora"]["matches"], lg["casa"], lg["fora"])}
    tg = info.get("tabela_geral") or {}
    if tg.get("casa") and tg.get("fora"):
        lgg = df.lambdas_gerais(tg["casa"], tg["fora"], lg["casa"], lg["fora"])
        if lgg:
            lams["geral"] = lgg
    liga = v.medias_liga(api, ut, info["temporada"]) or (lg["casa"], lg["fora"])
    xh, xaw = (xa, xf) if az_casa else (xf, xa)
    lams.update(lambdas_amostra(xh, xaw, liga, a["encolhimento_jogos"]))
    info["lambdas"] = {k: [round(x, 2) for x in lam] for k, lam in lams.items()}
    variantes = {}
    for nome, lam in lams.items():
        for rho in (0.0, -0.10):
            variantes[f"{nome}{'' if rho == 0 else '_dc'}"] = probs_lado(*lam, az_casa, rho, sig)

    # mercado sem margem (regra 8)
    o = info["odds"]
    inv = [1 / x for x in o]
    p1x2 = [x / sum(inv) for x in inv]
    p_az, p_x = (p1x2[0] if az_casa else p1x2[2]), p1x2[1]
    merc = {"az_dc": p_az + p_x, "az_vence": p_az}
    mo = info["mercado_odds"]
    odd_dc = (mo.get("dc") or {}).get("1X" if az_casa else "X2")
    odd_dnb = None
    for m in api.get(f"event/{info['id']}/odds/1/all", cache=None).get("markets", []):
        if m.get("marketName") == "Draw no bet":
            ch = {c["name"]: v.odd_decimal(c["fractionalValue"]) for c in m.get("choices", [])}
            odd_dnb = ch.get("1" if az_casa else "2")

    ev_min = cfg["criterios"]["ev_minimo"]
    mercados = []
    for chave, rot, odd in (("az_dc", "{az} ou empate (dupla chance)", odd_dc), ("az_vence", "vitória do {az}", o[0] if az_casa else o[2])):
        vals = [pr[chave] for pr in variantes.values()]
        fr = freq_mercado_az(info["frequencias"], chave)
        p, limitada = df.prob_conservadora(vals, fr, a["tolerancia_frequencia"])
        item = {"chave": chave, "mercado": rot.format(az=info["azarao"]), "prob": round(p, 3),
                "variantes": {k: round(pr[chave], 3) for k, pr in variantes.items()},
                "frequencia": round(fr, 3) if fr is not None else None, "limitada_pela_frequencia": limitada,
                "odd_minima": df.odd_minima(p, ev_min), "odd_casa": round(odd, 3) if odd else None,
                "ev": round(p * odd - 1, 3) if odd else None, "prob_mercado": round(merc[chave], 3),
                "regra8": p - merc[chave] > a["regra8_pp"]}
        mercados.append(item)
    # empate anula: p de "não perde" dividida em vitória/empate pela variante mais conservadora
    if odd_dnb:
        pior = min(variantes.values(), key=lambda pr: pr["az_dc"])
        dc = next(m for m in mercados if m["chave"] == "az_dc")["prob"]
        pv = pior["az_vence"] / pior["az_dc"] * dc if pior["az_dc"] else 0
        pe = dc - pv
        p_sem_empate = pv / (1 - pe) if pe < 1 else 0
        mercados.append({"chave": "az_dnb", "mercado": f"{info['azarao']} empate anula", "prob": round(p_sem_empate, 3),
                         "prob_vence": round(pv, 3), "prob_empate": round(pe, 3), "odd_casa": round(odd_dnb, 3),
                         "ev": round(ev_empate_anula(pv, pe, odd_dnb), 3),
                         "odd_minima": round((1 + ev_min - pe) / pv, 2) if pv > 0 else None,
                         "prob_mercado": round(p_az / (p_az + (1 - p_az - p_x)), 3), "regra8": False})
    info["mercados"] = mercados
    crit = cfg["criterios"]
    passam = [m for m in mercados if m["prob"] >= crit["prob_minima"] and m.get("ev") is not None and m["ev"] >= crit["ev_minimo"]]
    info["regra8_mercados"] = [f"regra 8 ({m['mercado']}): modelo {m['prob']:.0%} x mercado {m['prob_mercado']:.0%} "
                               f"(+{(m['prob'] - m['prob_mercado']) * 100:.0f} p.p.) — procurar o que o mercado sabe"
                               for m in passam if m.get("regra8")]
    info["melhor_mercado"] = max(passam, key=lambda m: (m["ev"], m["prob"])) if passam else None

    # filtros (dado faltando, forma do azarão, amostra recente que desmente)
    info["motivo"] = None
    fa = info["forma_azarao"]
    if min(len(xa), len(xf)) < 3:
        info["motivo"] = f"dado faltando: só {len(xa)}/{len(xf)} jogos recentes na condição"
    elif df.forma_negativa(fa, a["forma_pontos_min"], a["forma_jogos"]):
        info["motivo"] = f"fora pela forma: azarão fez {fa['pts']} de {3 * fa['n']} pontos nos últimos {fa['n']} ({fa['seq']})"
    elif (info["azarao_amostra"].get("ppg") is not None and info["favorito_amostra"].get("ppg") is not None
          and len(xa) >= a["amostra_boa"]
          and info["azarao_amostra"]["ppg"] < info["favorito_amostra"]["ppg"] - a["ppg_folga"] - 0.5):
        info["motivo"] = (f"fora: nos últimos jogos na condição o azarão rende bem menos "
                          f"({info['azarao_amostra']['ppg']} x {info['favorito_amostra']['ppg']} pts/j)")
    det = api.get(f"event/{info['id']}").get("event", {})
    venue = det.get("venue") or {}
    info["local"] = {"estadio": venue.get("name"), "cidade": (venue.get("city") or {}).get("name"),
                     "pais": (venue.get("country") or {}).get("alpha2"), "coord": venue.get("venueCoordinates")}
    info["chuva"] = v.checar_chuva(info, dia, cfg) if chuva else {"status": "não consultada"}
    info["alertas"] = alertas_azarao(info, a)
    info["risco"] = any(x.startswith("⚠️ RISCO") for x in info["alertas"])
    info["passa"] = info["melhor_mercado"] is not None and info["motivo"] is None
    return info


def linha_curta(i: int, x: dict, crit: dict) -> str:
    if x.get("erro"):
        return f"{i}) {x['hora']} {x['jogo']} — erro: {x['erro']}"
    ms = [m for m in x.get("mercados", []) if m["prob"] >= crit["prob_minima"] and (m.get("ev") or -1) >= crit["ev_minimo"]]
    merc = " · ".join(f"{m['mercado'].replace(x['azarao'], 'az')} {m['prob']:.0%} (mín {m['odd_minima'] or 0:.2f}, "
                      f"bet365 {m['odd_casa']:.2f} EV {m['ev']:+.0%}, mercado {m['prob_mercado']:.0%})" for m in ms)
    if not x.get("passa"):
        merc = x.get("motivo") or "nenhum mercado com prob ≥ 60% e valor"
    az, fv = x["azarao_amostra"], x["favorito_amostra"]
    return (f"{i}) {x['hora']} {x['jogo']} [{x['pais']} · {x['competicao']}] odds {x['odds']}\n"
            f"   azarão {x['azarao']}: {x['ppg_az_cond']} pts/j na condição (fav {x['ppg_fav_cond']}), defesa ×{x['ind_def_az']}, "
            f"últimos {az['n']}: {az.get('ppg')} pts/j, forma {(x.get('forma_azarao') or {}).get('seq')} | "
            f"fav forma {(x.get('forma_favorito') or {}).get('seq')}\n"
            f"   → {merc}" + (f"\n   alertas: {'; '.join(x['alertas'])}" if x.get("alertas") else ""))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", default=None)
    p.add_argument("--config", action="store_true", help="só as ligas de config.json (padrão: todas)")
    p.add_argument("--ids", help="ids de eventos do Sofascore (pula a triagem)")
    p.add_argument("--max", type=int)
    p.add_argument("--sem-chuva", action="store_true")
    p.add_argument("--curto", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    cfg, d_def, a = config()
    data = args.data or datetime.now(v.FUSO_BR).date().isoformat()
    date.fromisoformat(data)
    api = v.Sofascore(v.CACHE_PADRAO, data)
    motivos, cache = Counter(), {}
    if args.ids:
        jogos = [api.get(f"event/{i}", cache=None).get("event") for i in args.ids.split(",")]
        jogos = [e for e in jogos if e]
        if not args.data and jogos:
            data = v.hora_br(jogos[0]["startTimestamp"]).date().isoformat()
    else:
        tc = cfg.get("varredura", {}).get("torneios_sofascore", {})
        jogos = df.listar(api, data, {int(k) for k in tc} if args.config else None)
    suspeitos = df.eventos_suspeitos(jogos)
    jogos = [e for e in jogos if e["id"] not in suspeitos]
    if suspeitos:
        motivos["evento suspeito"] += len(suspeitos)
    a_tri = dict(a, odd_azarao_min=0, ppg_folga=99, defesa_az_max=99, ataque_az_min=0, amostra_minima_tabela=1) if args.ids else a

    def seguro_triar(e):
        try:
            return triar(api, e, a_tri, motivos, cache)
        except Exception as exc:
            motivos[f"erro {type(exc).__name__}"] += 1
            return None

    triados = [x for x in v.em_paralelo(seguro_triar, jogos, 6) if x]
    triados.sort(key=lambda x: (x["nivel_base"], -x["pontuacao"]))
    alvo = triados[: args.max or a["max_aprofundar"]]

    def seguro_aprof(x):
        try:
            return aprofundar(api, x, cfg, d_def, a, v.hora_br(x["inicio"]).date().isoformat(), not args.sem_chuva)
        except Exception as exc:
            x.update({"erro": f"{type(exc).__name__}: {exc}"[:200], "passa": False})
            return x

    res = v.em_paralelo(seguro_aprof, alvo, 4)
    res.sort(key=lambda x: (not x.get("passa"), x.get("risco", False), x.get("nivel_base", False),
                            -((x.get("melhor_mercado") or {}).get("ev") or -1)))
    for i, x in enumerate(res, 1):
        x["n"] = i
    saida = {"data": data, "gerado": datetime.now(v.FUSO_BR).strftime("%Y-%m-%d %H:%M"), "jogos_listados": len(jogos),
             "motivos": dict(motivos), "triados": len(triados), "aprofundados": len(res), "criterios": cfg["criterios"],
             "azarao": a, "candidatos": res, "falhas_rede": api.falhas}
    arq = v.CACHE_PADRAO / (f"azarao-{data}-ids.json" if args.ids else f"azarao-{data}.json")
    arq.parent.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(saida, ensure_ascii=False, indent=1, allow_nan=False)
    arq.write_text(texto, encoding="utf-8")
    if args.json:
        print(texto)
        return
    passam = [x for x in res if x.get("passa")]
    print(f"Azarão forte — {data}: {len(jogos)} jogos · {motivos.get('analisado', 0)} com odds, tabela e amostra · "
          f"{len(triados)} na triagem · {len(res)} aprofundados · {len(passam)} com mercado de valor")
    if api.falhas:
        print(f"⚠️ {api.falhas} falhas de rede no Sofascore: rode de novo (o cache acelera).")
    for x in (passam if args.curto else res):
        print(linha_curta(x["n"], x, cfg["criterios"]))
    if not passam:
        print("Nenhum azarão forte com mercado de valor.")
    print(f"JSON completo: {arq.relative_to(n.RAIZ)}")


if __name__ == "__main__":
    main()
