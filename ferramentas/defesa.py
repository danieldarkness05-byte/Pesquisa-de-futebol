#!/usr/bin/env python3
"""Defesa fraca do azarão x ataque forte do favorito, em TODAS as ligas do Sofascore.

Só Python (não gasta créditos). Três etapas:

1. **Triagem** de todos os jogos do dia que ainda não começaram e têm tabela
   casa/fora. Azarão = pior odd para vencer (sem odds: menos pontos por jogo,
   se a diferença for clara). Passa quando o azarão sofre ≥ `indice_defesa_min`
   × a média da liga na condição (casa/fora) e o favorito marca ≥
   `indice_ataque_min` × a média.
2. **Aprofundamento** dos melhores: últimos jogos de liga na condição (gols, xG,
   chutes), frequência e mediana, tendência recente, gols x xG, calendário,
   expulsões, odds bet365, probabilidade implícita do mercado (regra 8) e os
   mercados de gol do favorito por três caminhos (tabela da temporada, λ
   encolhido por gols, λ encolhido gols+xG). Vale o MENOR, limitado pela
   frequência real + tolerância.
3. **Saída**: ranking com alertas e odd mínima; o JSON alimenta o workflow
   `.claude/workflows/defesa.js` (pesquisador + cético) do /defesa-fraca.

As lições aprendidas nas pesquisas viram alertas aqui (docs/licoes.md).

Exemplos:
  python3 ferramentas/defesa.py                       # hoje, todas as ligas
  python3 ferramentas/defesa.py --data 2026-10-13
  python3 ferramentas/defesa.py --config              # só as ligas do config.json
  python3 ferramentas/defesa.py --ids 15271307,16362870   # só esses jogos (pula a triagem)
  python3 ferramentas/defesa.py --curto               # resumo de celular
  python3 ferramentas/defesa.py --json > /tmp/defesa.json

O resultado completo fica em dados/cache/sofascore/defesa-AAAA-MM-DD.json.
Odds: bet365 via Sofascore — NÃO são da Betano. Confira a odd mínima no app.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from collections import Counter
from datetime import date, datetime
from pathlib import Path

import nucleo as n
import varredura as v

DEFESA_PADRAO = {
    "todas_as_ligas": True,
    "indice_defesa_min": 1.4,
    "indice_ataque_min": 1.15,
    "tolerancia_indice": 0.02,
    "amostra_minima_tabela": 4,
    "amostra_boa": 5,
    "jogos_amostra": 10,
    "max_aprofundar": 12,
    "max_pesquisa": 4,
    "max_resposta": 4,
    "diferenca_ppg_sem_odds": 0.4,
    "risco_gols_azarao": 1.3,
    "risco_top_ataque": 0.3,
    "encolhimento_jogos": 4,
    "rho": -0.10,
    "incerteza_sigma": 0.15,
    "tolerancia_frequencia": 0.05,
    "regra8_pp": 0.10,
    "gols_acima_xg": 0.5,
    "melhora_defesa": 0.75,
    "dias_calendario": 7,
    "jogos_calendario": 3,
    "expulsoes_alerta": 2,
    "chuva": "informativa",
    "palavras_base": ["Amateur", "NCAA", "U19", "U20", "U21", "U23", "U17", "Reserve", "Women",
                      "Youth", "Primavera", "Juniors"],
}

MERCADOS = [  # (chave, rótulo, gols do favorito exigidos)
    ("fav_marca_1", "{fav} marca 1+ gol", 1),
    ("fav_marca_2", "{fav} marca 2+ gols", 2),
    ("fav_marca_3", "{fav} marca 3+ gols", 3),
]


def config() -> tuple[dict, dict]:
    cfg = n.carregar_config()
    d = dict(DEFESA_PADRAO)
    d.update({k: val for k, val in cfg.get("defesa", {}).items() if not k.startswith("_")})
    return cfg, d


# ---------------------------------------------------------------------------
# Funções puras (testadas em testes/test_ferramentas.py)
# ---------------------------------------------------------------------------

def escolher_favorito(odds: list[float] | None, ppg_casa: float | None, ppg_fora: float | None,
                      dif_min: float) -> tuple[bool | None, str]:
    """(favorito é o mandante?, critério). None quando não há favorito claro."""
    if odds and len(odds) == 3 and odds[0] != odds[2]:
        return odds[0] < odds[2], "odds"
    if ppg_casa is None or ppg_fora is None or abs(ppg_casa - ppg_fora) < dif_min:
        return None, "sem favorito claro"
    return ppg_casa > ppg_fora, f"tabela ({ppg_casa:.2f} x {ppg_fora:.2f} pts/j)"


def indice(valor: float, media_liga: float) -> float | None:
    return round(valor / media_liga, 2) if media_liga else None


def passa_triagem(ind_def: float | None, ind_atq: float | None, d: dict) -> bool:
    tol = d["tolerancia_indice"]
    return (ind_def is not None and ind_atq is not None
            and ind_def >= d["indice_defesa_min"] - tol and ind_atq >= d["indice_ataque_min"] - tol)


def eh_risco(gols_azarao_cond: float, rank_ataque: tuple[int, int] | None, d: dict) -> bool:
    """⚠️ RISCO (regra 4): o azarão também marca bem → jogo aberto."""
    if gols_azarao_cond >= d["risco_gols_azarao"]:
        return True
    if rank_ataque:
        pos, tot = rank_ataque
        return pos <= max(1, round(d["risco_top_ataque"] * tot))
    return False


def nivel_base(textos: list[str], palavras: list[str]) -> bool:
    """Liga amadora, universitária, de base, feminina ou time reserva."""
    alvo = " ".join(t for t in textos if t)
    return any(p.lower() in alvo.lower() for p in palavras) or " II" in alvo


def frequencias(fav: list[dict], az: list[dict]) -> dict:
    """Frequência real nas amostras: favorito marcou k+ e azarão sofreu k+."""
    out = {}
    for k in (1, 2, 3):
        f = [x["gf"] >= k for x in fav]
        a = [x["ga"] >= k for x in az]
        out[f"fav_{k}"] = sum(f) / len(f) if f else None
        out[f"az_{k}"] = sum(a) / len(a) if a else None
    out["mediana_ga_az"] = statistics.median([x["ga"] for x in az]) if az else None
    out["mediana_gf_fav"] = statistics.median([x["gf"] for x in fav]) if fav else None
    return out


def freq_mercado(freq: dict, k: int) -> float | None:
    """Frequência de referência do mercado 'favorito marca k+': média das duas pontas."""
    vals = [x for x in (freq.get(f"fav_{k}"), freq.get(f"az_{k}")) if x is not None]
    return sum(vals) / len(vals) if vals else None


def prob_time_marca(m: list[list[float]], fav_casa: bool, k: int) -> float:
    """P(favorito marca ≥ k) na matriz de placares (linhas = mandante)."""
    tam = len(m)
    if fav_casa:
        return sum(m[i][j] for i in range(k, tam) for j in range(tam))
    return sum(m[i][j] for i in range(tam) for j in range(k, tam))


def prob_conservadora(variantes: list[float], freq: float | None, tol: float) -> tuple[float, bool]:
    """(prob, limitada_pela_frequencia): o menor dos modelos, sem passar da
    frequência real + tolerância (o Poisson exagera com médias infladas por goleadas)."""
    p = min(variantes)
    if freq is not None and p > freq + tol:
        return freq + tol, True
    return p, False


def odd_minima(p: float, ev_min: float) -> float:
    return round((1 + ev_min) / p, 2) if p > 0 else float("inf")


def lambdas_mercado(p1x2: list[float], p_over25: float | None, total_ref: float) -> tuple[float, float]:
    """λ (mandante, visitante) que reproduzem o 1X2 sem margem e, se houver, o
    over 2.5 sem margem (busca em grade, Poisson simples). Sem over, fixa o total
    em `total_ref` (média da liga)."""
    def erro(lh, la):
        m = n.matriz_placar(lh, la, 0.0, 10)
        r = v.resultado(m)
        e = (r["1"] - p1x2[0]) ** 2 + (r["X"] - p1x2[1]) ** 2 + (r["2"] - p1x2[2]) ** 2
        if p_over25 is not None:
            e += (v.total_gols(m, 2.5, "over")[0] - p_over25) ** 2
        return e

    melhor = None
    passos = [x / 10 for x in range(1, 51)]
    if p_over25 is None:
        cand = [(lh, total_ref - lh) for lh in passos if 0.1 <= total_ref - lh]
    else:
        cand = [(lh, la) for lh in passos for la in passos]
    for lh, la in cand:
        e = erro(lh, la)
        if melhor is None or e < melhor[0]:
            melhor = (e, lh, la)
    _, lh, la = melhor
    # refinamento fino ao redor do melhor ponto
    for _ in range(2):
        passo = 0.02
        viz = [(lh + a * passo, la + b * passo) for a in range(-5, 6) for b in range(-5, 6)
               if lh + a * passo > 0.05 and la + b * passo > 0.05]
        if p_over25 is None:
            viz = [(x, total_ref - x) for x, _ in viz if total_ref - x > 0.05]
        for x, y in viz:
            e = erro(x, y)
            if e < melhor[0]:
                melhor = (e, x, y)
        _, lh, la = melhor
    return round(lh, 3), round(la, 3)


def tendencia(xs: list[dict], chave: str, ultimos: int = 5) -> tuple[float | None, float | None]:
    """(média dos últimos `ultimos`, média da amostra toda)."""
    vals = [x[chave] for x in xs if x.get(chave) is not None]
    if len(vals) < ultimos + 2:
        return None, (sum(vals) / len(vals) if vals else None)
    return sum(vals[-ultimos:]) / ultimos, sum(vals) / len(vals)


def media_chave(xs: list[dict], chave: str, cobertura: float = 0.7) -> float | None:
    vals = [x[chave] for x in xs if x.get(chave) is not None]
    return sum(vals) / len(vals) if xs and len(vals) / len(xs) >= cobertura else None


def calendario(eventos_passados: list[dict], eventos_futuros: list[dict], inicio_ts: int, dias: int) -> dict:
    """Jogos do favorito na janela de `dias` em volta deste (antes e depois)."""
    janela = dias * 86400
    antes = [e for e in eventos_passados
             if e.get("status", {}).get("type") == "finished" and 0 < inicio_ts - e["startTimestamp"] <= janela]
    depois = [e for e in eventos_futuros if 0 < e["startTimestamp"] - inicio_ts <= janela]
    ult = max((e["startTimestamp"] for e in eventos_passados
               if e.get("status", {}).get("type") == "finished" and e["startTimestamp"] < inicio_ts), default=None)
    prox = min((e["startTimestamp"] for e in eventos_futuros if e["startTimestamp"] > inicio_ts), default=None)
    return {"jogos_janela": len(antes) + len(depois) + 1,
            "dias_desde_ultimo": round((inicio_ts - ult) / 86400, 1) if ult else None,
            "dias_ate_proximo": round((prox - inicio_ts) / 86400, 1) if prox else None}


def alertas_estatisticos(info: dict, d: dict) -> list[str]:
    """Lições das pesquisas transformadas em checagem automática (docs/licoes.md)."""
    al = []
    az, fv, fr = info["azarao_amostra"], info["favorito_amostra"], info["frequencias"]
    if info.get("risco"):
        al.append("⚠️ RISCO: azarão também marca bem (jogo aberto)")
    if min(az["n"], fv["n"]) < d["amostra_boa"]:
        al.append(f"amostra pequena ({fv['n']}/{az['n']} jogos na condição)")
    if info.get("nivel_base"):
        al.append("liga amadora/base/reserva: dado mais fraco e pouca chance de ter na Betano")
    if az.get("ga") is not None and az.get("xg_contra") is not None and az["ga"] - az["xg_contra"] >= d["gols_acima_xg"]:
        al.append(f"azarão sofre bem mais que o xG cedido ({az['ga']:.2f} x {az['xg_contra']:.2f}): regressão provável")
    if fv.get("gf") is not None and fv.get("xg_pro") is not None and fv["gf"] - fv["xg_pro"] >= d["gols_acima_xg"]:
        al.append(f"favorito marca bem acima do xG ({fv['gf']:.2f} x {fv['xg_pro']:.2f}): regressão provável")
    liga_az = info["liga"]["casa"] if info["fav_casa"] else info["liga"]["fora"]
    if az.get("ga") is not None and liga_az and az["ga"] / liga_az < d["indice_defesa_min"] - d["tolerancia_indice"]:
        al.append(f"nos últimos {az['n']} jogos na condição a defesa do azarão não é tão fraca "
                  f"({az['ga']:.2f}/j = ×{az['ga'] / liga_az:.2f} da média)")
    rec, tot = az.get("ga_ultimos5"), az.get("ga")
    if rec is not None and tot and rec <= d["melhora_defesa"] * tot:
        al.append(f"defesa do azarão melhorando ({rec:.2f} nos últimos 5 x {tot:.2f}): técnico novo/ajuste?")
    if fr.get("mediana_ga_az") is not None and az.get("ga") and fr["mediana_ga_az"] <= az["ga"] - 1:
        al.append(f"média de gols sofridos inflada por goleadas (mediana {fr['mediana_ga_az']:g})")
    cal = info.get("calendario_favorito") or {}
    if cal.get("jogos_janela", 0) >= d["jogos_calendario"]:
        al.append(f"favorito com {cal['jogos_janela']} jogos em ±{d['dias_calendario']} dias: rodízio possível")
    if (cal.get("dias_desde_ultimo") or 0) >= 18:
        al.append(f"favorito parado há {cal['dias_desde_ultimo']:.0f} dias: falta de ritmo")
    if az.get("expulsoes", 0) >= d["expulsoes_alerta"]:
        al.append(f"azarão teve expulsão em {az['expulsoes']} dos jogos da amostra (gols sofridos inflados)")
    if info.get("regra8"):
        al.append(info["regra8"])
    if not info.get("odds"):
        al.append("sem odds no Sofascore (favorito pela tabela)")
    return al


def pontuacao(info: dict, d: dict) -> float:
    """Ordem para o aprofundamento: índices, com desconto por cada fraqueza."""
    s = (info["ind_def"] or 0) * (info["ind_atq"] or 0)
    for cond, fator in ((info.get("risco"), 0.7), (info.get("amostra_pequena"), 0.8),
                        (info.get("nivel_base"), 0.8), (not info.get("odds"), 0.9)):
        if cond:
            s *= fator
    return round(s, 3)


# ---------------------------------------------------------------------------
# Sofascore
# ---------------------------------------------------------------------------

def listar(api: v.Sofascore, data: str, torneios: set[int] | None) -> list[dict]:
    """Jogos não iniciados da data (horário de Brasília); `torneios` None = todos."""
    if torneios:
        return v.listar_jogos(api, data, torneios)
    cats = api.get(f"sport/football/{data}/-10800/categories").get("categories", [])
    agora, vistos = time.time(), {}
    for res in v.em_paralelo(lambda c: api.get(f"category/{c['category']['id']}/scheduled-events/{data}",
                                               cache=None), cats):
        for e in res.get("events", []):
            if (e["status"]["type"] == "notstarted" and e["startTimestamp"] > agora
                    and v.hora_br(e["startTimestamp"]).date().isoformat() == data):
                vistos[e["id"]] = e
    return sorted(vistos.values(), key=lambda e: e["startTimestamp"])


def tabela(api: v.Sofascore, ut: int, s: int, tipo: str) -> dict[int, dict]:
    rows = {}
    for g in api.get(f"unique-tournament/{ut}/season/{s}/standings/{tipo}").get("standings", []):
        for r in g.get("rows", []):
            rows[r["team"]["id"]] = r
    return rows


def ranking(rows: dict[int, dict], chave: str, tid: int) -> tuple[int, int] | None:
    vals = sorted(((r[chave] / r["matches"], t) for t, r in rows.items()
                   if r.get("matches") and r.get(chave) is not None), reverse=True)
    for i, (_, t) in enumerate(vals):
        if t == tid:
            return i + 1, len(vals)
    return None


def odds_evento(api: v.Sofascore, eid: int) -> dict:
    """{'1x2': [..], '1x2_ini': [..], 'dc': {'1X':..}, 'over': {1.5: (over, under)}, 'ambas': (sim, não)}"""
    out: dict = {"over": {}}
    for m in api.get(f"event/{eid}/odds/1/all", cache=None).get("markets", []):
        ch = {c["name"]: c for c in m.get("choices", [])}
        dec = {k: v.odd_decimal(c["fractionalValue"]) for k, c in ch.items()}
        nome = m.get("marketName")
        if nome == "Full time" and {"1", "X", "2"} <= set(dec):
            out["1x2"] = [dec["1"], dec["X"], dec["2"]]
            ini = [ch[k].get("initialFractionalValue") for k in ("1", "X", "2")]
            if all(ini):
                out["1x2_ini"] = [round(v.odd_decimal(x), 2) for x in ini]
        elif nome == "Double chance":
            out["dc"] = dec
        elif nome == "Match goals" and {"Over", "Under"} <= set(dec):
            try:
                out["over"][float(m.get("choiceGroup"))] = (dec["Over"], dec["Under"])
            except (TypeError, ValueError):
                pass
        elif nome == "Both teams to score" and {"Yes", "No"} <= set(dec):
            out["ambas"] = (dec["Yes"], dec["No"])
    return out


def amostra(api: v.Sofascore, eventos: list[dict], tid: int, ut: int, em_casa: bool, qtd: int) -> list[dict]:
    cond, _ = v.amostras_time(eventos, tid, ut, em_casa, qtd)
    out = []
    for e in cond[-qtd:]:
        est = v.ler_estatisticas(api.get(f"event/{e['id']}/statistics", cache="fixo"))
        r = v.linha_do_time(e, est, tid)
        if r:
            r["id"] = e["id"]
            out.append(r)
    return out


def expulsoes(api: v.Sofascore, xs: list[dict], tid_casa: dict[int, bool]) -> int:
    """Jogos da amostra em que o time levou cartão vermelho (direto ou 2º amarelo)."""
    tot = 0
    for x in xs:
        inc = api.get(f"event/{x['id']}/incidents", cache="fixo").get("incidents", [])
        casa = tid_casa[x["id"]]
        if any(i.get("incidentType") == "card" and i.get("incidentClass") in ("red", "yellowRed")
               and i.get("isHome") == casa for i in inc):
            tot += 1
    return tot


def resumo_amostra(xs: list[dict]) -> dict:
    def m(k):
        return media_chave(xs, k)
    r = {"n": len(xs), "gf": m("gf"), "ga": m("ga"), "xg_pro": m("xg_f"), "xg_contra": m("xg_a"),
         "chutes_pro": m("chutes_f"), "chutes_contra": m("chutes_a"), "sot_contra": m("sot_a"),
         "sem_sofrer": sum(1 for x in xs if x["ga"] == 0), "sem_marcar": sum(1 for x in xs if x["gf"] == 0),
         "placares": [f"{x['gf']}-{x['ga']} {x['adv']}" for x in xs]}
    r["ga_ultimos5"], _ = tendencia(xs, "ga")
    r["gf_ultimos5"], _ = tendencia(xs, "gf")
    return {k: (round(val, 2) if isinstance(val, float) else val) for k, val in r.items()}


# ---------------------------------------------------------------------------
# Triagem e aprofundamento
# ---------------------------------------------------------------------------

def triar(api: v.Sofascore, e: dict, d: dict, motivos: Counter, cache: dict) -> dict | None:
    ut, s = v.torneio_id(e), (e.get("season") or {}).get("id")
    if not ut or not s:
        motivos["sem torneio/temporada"] += 1
        return None
    if (ut, s) not in cache:
        cache[(ut, s)] = tuple(tabela(api, ut, s, t) for t in ("home", "away", "total"))
    th, ta, tt = cache[(ut, s)]
    h, a = e["homeTeam"]["id"], e["awayTeam"]["id"]
    if not th or not ta or h not in th or a not in ta:
        motivos["sem tabela casa/fora (copa, amistoso, seleção)"] += 1
        return None
    jogos = sum(r["matches"] for r in th.values())
    if not jogos:
        motivos["tabela vazia"] += 1
        return None
    lh = sum(r["scoresFor"] for r in th.values()) / jogos
    la = sum(r["scoresAgainst"] for r in th.values()) / jogos
    odds = odds_evento(api, e["id"])
    ppg = lambda t: (tt[t]["points"] / tt[t]["matches"]) if tt.get(t, {}).get("matches") else None  # noqa: E731
    fav_casa, crit = escolher_favorito(odds.get("1x2"), ppg(h), ppg(a), d["diferenca_ppg_sem_odds"])
    if fav_casa is None:
        motivos["sem odds e sem favorito claro"] += 1
        return None
    rh, ra = th[h], ta[a]
    fv, az = (rh, ra) if fav_casa else (ra, rh)
    t_fv, t_az = (th, ta) if fav_casa else (ta, th)
    l_fav = lh if fav_casa else la      # gols do favorito ~ média de quem joga na condição dele
    l_az = lh if fav_casa else la       # gols sofridos pelo azarão = gols do adversário na condição
    fid, aid = (h, a) if fav_casa else (a, h)
    if min(fv["matches"], az["matches"]) < d["amostra_minima_tabela"]:
        motivos["amostra < mínimo na condição"] += 1
        return None
    az_ga, az_gf = az["scoresAgainst"] / az["matches"], az["scoresFor"] / az["matches"]
    fav_gf = fv["scoresFor"] / fv["matches"]
    ind_def, ind_atq = indice(az_ga, l_az), indice(fav_gf, l_fav)
    motivos["analisado"] += 1
    if not passa_triagem(ind_def, ind_atq, d):
        return None
    casa, fora = e["homeTeam"]["name"], e["awayTeam"]["name"]
    cat = (e["tournament"].get("category") or {}).get("name")
    rank_az = ranking(tt, "scoresFor", aid) if tt else ranking(t_az, "scoresFor", aid)
    info = {
        "id": e["id"], "inicio": e["startTimestamp"], "hora": v.hora_br(e["startTimestamp"]).strftime("%H:%M"),
        "jogo": f"{casa} x {fora}", "pais": cat, "competicao": e["tournament"].get("name"), "ut": ut, "temporada": s,
        "casa": casa, "fora": fora, "ids": {"casa": h, "fora": a},
        "fav_casa": fav_casa, "favorito": casa if fav_casa else fora, "azarao": fora if fav_casa else casa,
        "favorito_por": crit, "odds": odds.get("1x2"), "odds_ini": odds.get("1x2_ini"), "mercado_odds": odds,
        "liga": {"casa": round(lh, 3), "fora": round(la, 3)},
        "tabela": {"casa": {k: rh[k] for k in ("matches", "scoresFor", "scoresAgainst")},
                   "fora": {k: ra[k] for k in ("matches", "scoresFor", "scoresAgainst")}},
        "az_ga": round(az_ga, 2), "az_gf": round(az_gf, 2), "fav_gf": round(fav_gf, 2),
        "ind_def": ind_def, "ind_atq": ind_atq,
        "rank_pior_defesa_az": ranking(t_az, "scoresAgainst", aid), "rank_ataque_fav": ranking(t_fv, "scoresFor", fid),
        "rank_ataque_az": rank_az,
        "risco": eh_risco(az_gf, rank_az, d),
        "amostra_pequena": min(fv["matches"], az["matches"]) < d["amostra_boa"],
        "nivel_base": nivel_base([cat, e["tournament"].get("name"), casa, fora], d["palavras_base"]),
    }
    info["pontuacao"] = pontuacao(info, d)
    return info


def matriz_e_probs(lh: float, la: float, fav_casa: bool, rho: float, sigma: float) -> dict:
    m = v.matriz(lh, la, rho, sigma)
    r = v.resultado(m)
    out = {f"fav_marca_{k}": prob_time_marca(m, fav_casa, k) for k in (1, 2, 3)}
    out["fav_vence"] = r["1"] if fav_casa else r["2"]
    out["fav_dc"] = r["1X"] if fav_casa else r["X2"]
    out["over_1.5"] = v.total_gols(m, 1.5, "over")[0]
    out["over_2.5"] = v.total_gols(m, 2.5, "over")[0]
    return out


def aprofundar(api: v.Sofascore, info: dict, cfg: dict, d: dict, data: str, chuva: bool = True) -> dict:
    ut, eid, fav_casa = info["ut"], info["id"], info["fav_casa"]
    h, a = info["ids"]["casa"], info["ids"]["fora"]
    fid, aid = (h, a) if fav_casa else (a, h)
    evf, eva = v.ultimos_eventos(api, fid), v.ultimos_eventos(api, aid)
    qtd = d["jogos_amostra"]
    xf = amostra(api, evf, fid, ut, fav_casa, qtd)
    xa = amostra(api, eva, aid, ut, not fav_casa, qtd)
    info["favorito_amostra"], info["azarao_amostra"] = resumo_amostra(xf), resumo_amostra(xa)
    casa_de = {e["id"]: e["homeTeam"]["id"] == aid for e in eva}
    info["azarao_amostra"]["expulsoes"] = expulsoes(api, xa, casa_de)
    info["frequencias"] = {k: (round(x, 3) if isinstance(x, float) else x) for k, x in frequencias(xf, xa).items()}
    prox = api.get(f"team/{fid}/events/next/0").get("events", [])
    info["calendario_favorito"] = calendario(evf, prox, info["inicio"], d["dias_calendario"])

    # variantes do modelo
    rho, sig = d["rho"], d["incerteza_sigma"]
    tb, lg = info["tabela"], info["liga"]
    variantes = {}
    lt = n.lambdas_por_medias(tb["casa"]["scoresFor"] / tb["casa"]["matches"],
                              tb["casa"]["scoresAgainst"] / tb["casa"]["matches"],
                              tb["fora"]["scoresFor"] / tb["fora"]["matches"],
                              tb["fora"]["scoresAgainst"] / tb["fora"]["matches"], lg["casa"], lg["fora"])
    variantes["tabela"] = (lt, matriz_e_probs(*lt, fav_casa, rho, sig))
    liga = v.medias_liga(api, ut, info["temporada"]) or (lg["casa"], lg["fora"])
    xh, xaw = (xf, xa) if fav_casa else (xa, xf)
    if min(len(xh), len(xaw)) >= 3:
        for modo in ("gols", "mix"):
            lam = v.gols_esperados(xh, xaw, liga, d["encolhimento_jogos"], modo)
            if lam and (modo == "gols" or info["favorito_amostra"]["xg_pro"] is not None):
                variantes[modo] = (lam, matriz_e_probs(*lam, fav_casa, rho, sig))
    info["lambdas"] = {k: [round(x, 2) for x in lam] for k, (lam, _) in variantes.items()}

    # mercado (regra 8)
    mo = info["mercado_odds"]
    p_merc = None
    if mo.get("1x2"):
        inv = [1 / x for x in mo["1x2"]]
        p1x2 = [x / sum(inv) for x in inv]
        ov = mo["over"].get(2.5)
        p_ov = (1 / ov[0]) / (1 / ov[0] + 1 / ov[1]) if ov else None
        lm = lambdas_mercado(p1x2, p_ov, lg["casa"] + lg["fora"])
        p_merc = matriz_e_probs(*lm, fav_casa, 0.0, 0.0)
        info["lambdas"]["mercado"] = list(lm)

    # mercados do favorito
    ev_min = cfg["criterios"]["ev_minimo"]
    mercados = []
    for chave, rot, k in MERCADOS:
        vals = [pr[chave] for _, pr in variantes.values()]
        if not vals:
            continue
        fr = freq_mercado(info["frequencias"], k)
        p, limitada = prob_conservadora(vals, fr, d["tolerancia_frequencia"])
        item = {"chave": chave, "mercado": rot.format(fav=info["favorito"]), "prob": round(p, 3),
                "variantes": {nome: round(pr[chave], 3) for nome, (_, pr) in variantes.items()},
                "frequencia": round(fr, 3) if fr is not None else None, "limitada_pela_frequencia": limitada,
                "odd_minima": odd_minima(p, ev_min), "odd_casa": None, "ev": None}
        if p_merc:
            item["prob_mercado"] = round(p_merc[chave], 3)
        mercados.append(item)
    # vitória e dupla chance com odd real
    for chave, rot in (("fav_vence", "vitória do {fav}"), ("fav_dc", "dupla chance {fav}")):
        vals = [pr[chave] for _, pr in variantes.values()]
        if not vals:
            continue
        p = min(vals)
        odd = None
        if chave == "fav_vence" and mo.get("1x2"):
            odd = mo["1x2"][0 if fav_casa else 2]
        elif chave == "fav_dc" and mo.get("dc"):
            odd = mo["dc"].get("1X" if fav_casa else "X2")
        item = {"chave": chave, "mercado": rot.format(fav=info["favorito"]), "prob": round(p, 3),
                "variantes": {nome: round(pr[chave], 3) for nome, (_, pr) in variantes.items()},
                "odd_minima": odd_minima(p, ev_min), "odd_casa": odd,
                "ev": round(p * odd - 1, 3) if odd else None}
        if p_merc:
            item["prob_mercado"] = round(p_merc[chave], 3)
        mercados.append(item)
    info["mercados"] = mercados

    crit = cfg["criterios"]
    passam = [x for x in mercados if x["prob"] >= crit["prob_minima"]
              and (x["odd_casa"] is None or x["ev"] >= crit["ev_minimo"])]
    gol = [x for x in passam if x["chave"].startswith("fav_marca")]
    info["melhor_mercado"] = (max(gol, key=lambda x: x["chave"]) if gol else (passam[0] if passam else None))
    mm = info["melhor_mercado"]
    info["regra8"] = None
    if mm and mm.get("prob_mercado") is not None and mm["prob"] - mm["prob_mercado"] > d["regra8_pp"]:
        info["regra8"] = (f"regra 8: modelo {mm['prob']:.0%} x mercado {mm['prob_mercado']:.0%} "
                          f"(+{(mm['prob'] - mm['prob_mercado']) * 100:.0f} p.p.) — procurar o que o mercado sabe")
    det = api.get(f"event/{eid}").get("event", {})
    venue = det.get("venue") or {}
    info["local"] = {"estadio": venue.get("name"), "cidade": (venue.get("city") or {}).get("name"),
                     "pais": (venue.get("country") or {}).get("alpha2"), "coord": venue.get("venueCoordinates")}
    info["chuva"] = v.checar_chuva(info, data, cfg) if chuva else {"status": "não consultada"}
    info["alertas"] = alertas_estatisticos(info, d)
    info["passa"] = mm is not None
    return info


# ---------------------------------------------------------------------------
# Saída
# ---------------------------------------------------------------------------

def mercados_que_passam(x: dict, prob_min: float, ev_min: float) -> list[dict]:
    return [m for m in x.get("mercados", []) if m["prob"] >= prob_min
            and (m.get("odd_casa") is None or (m.get("ev") or -1) >= ev_min)]


def linha_curta(i: int, x: dict, prob_min: float = 0.6, ev_min: float = 0.03) -> str:
    if x.get("erro"):
        return f"{i}) {x['hora']} {x['jogo']} — erro ao aprofundar: {x['erro']}"
    ms = mercados_que_passam(x, prob_min, ev_min)
    merc = (" · ".join(f"{m['mercado'].replace(x['favorito'], 'fav')} {m['prob']:.0%} (mín {m['odd_minima']:.2f}"
                       + (f", bet365 {m['odd_casa']:.2f} EV {m['ev']:+.0%}" if m.get("odd_casa") else "") + ")"
                       for m in ms) if ms else "nenhum mercado ≥ 60%")
    az = x["azarao_amostra"]
    return (f"{i}) {x['hora']} {x['jogo']} [{x['pais']} · {x['competicao']}]\n"
            f"   azarão {x['azarao']} sofre {x['az_ga']:.2f}/j (×{x['ind_def']}; últimos {az['n']}: {az['ga']}, "
            f"xG contra {az['xg_contra']}) | {x['favorito']} marca {x['fav_gf']:.2f}/j (×{x['ind_atq']})\n"
            f"   → {merc}" + (f"\n   alertas: {'; '.join(x['alertas'])}" if x.get("alertas") else ""))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", default=None, help="AAAA-MM-DD (padrão: hoje, horário de Brasília)")
    p.add_argument("--config", action="store_true", help="só as ligas de config.json (padrão: todas)")
    p.add_argument("--ids", help="ids de eventos do Sofascore separados por vírgula (pula a triagem)")
    p.add_argument("--max", type=int, help="quantos aprofundar (padrão: defesa.max_aprofundar)")
    p.add_argument("--sem-chuva", action="store_true", help="não consulta a previsão (mais rápido)")
    p.add_argument("--sem-cache", action="store_true")
    p.add_argument("--curto", action="store_true")
    p.add_argument("--json", action="store_true")
    a = p.parse_args()

    cfg, d = config()
    data = a.data or datetime.now(v.FUSO_BR).date().isoformat()
    date.fromisoformat(data)
    api = v.Sofascore(None if a.sem_cache else v.CACHE_PADRAO, data)
    motivos, cache = Counter(), {}
    if a.ids:
        jogos = [api.get(f"event/{i}", cache=None).get("event") for i in a.ids.split(",")]
        jogos = [e for e in jogos if e]
    else:
        tc = cfg.get("varredura", {}).get("torneios_sofascore", {})
        torneios = {int(k) for k in tc} if (a.config or not d["todas_as_ligas"]) else None
        jogos = listar(api, data, torneios)
    total = len(jogos)

    def seguro_triar(e):
        try:
            return triar(api, e, d, motivos, cache)
        except Exception as exc:  # um jogo com dado quebrado não derruba a varredura
            motivos[f"erro {type(exc).__name__}"] += 1
            return None

    if a.ids:  # sem corte da triagem: aprofunda o que foi pedido
        d = dict(d, indice_defesa_min=0, indice_ataque_min=0, amostra_minima_tabela=1)
    triados = [x for x in v.em_paralelo(seguro_triar, jogos, 6) if x]
    # profissional e com amostra boa primeiro: amador/base com índice enorme não toma a vaga
    triados.sort(key=lambda x: (x["nivel_base"], x["amostra_pequena"], -x["pontuacao"]))
    alvo = triados[: a.max or d["max_aprofundar"]]

    def seguro_aprof(x):
        try:
            return aprofundar(api, x, cfg, d, data, chuva=not a.sem_chuva)
        except Exception as exc:
            x["erro"] = f"{type(exc).__name__}: {exc}"[:200]
            x["passa"] = False
            return x

    res = v.em_paralelo(seguro_aprof, alvo, 4)
    res.sort(key=lambda x: (not x.get("passa"), x.get("risco", False), x.get("nivel_base", False),
                            -((x.get("melhor_mercado") or {}).get("prob") or 0), -x["pontuacao"]))
    for i, x in enumerate(res, 1):
        x["n"] = i
    saida = {"data": data, "gerado": datetime.now(v.FUSO_BR).strftime("%Y-%m-%d %H:%M"),
             "jogos_listados": total, "motivos": dict(motivos), "triados": len(triados),
             "aprofundados": len(res), "criterios": cfg["criterios"], "defesa": d, "candidatos": res,
             "fora_do_corte": [{"jogo": x["jogo"], "hora": x["hora"], "pontuacao": x["pontuacao"]}
                               for x in triados[len(alvo):]],
             "falhas_rede": api.falhas}
    arq = v.CACHE_PADRAO / f"defesa-{data}.json"
    arq.parent.mkdir(parents=True, exist_ok=True)
    arq.write_text(json.dumps(saida, ensure_ascii=False, indent=1), encoding="utf-8")
    if a.json:
        print(json.dumps(saida, ensure_ascii=False, indent=1))
        return
    passam = [x for x in res if x.get("passa")]
    print(f"Defesa fraca x ataque forte — {data} ({'ligas do config' if a.config else 'todas as ligas'})")
    print(f"{total} jogos não iniciados · {motivos.get('analisado', 0)} com tabela e amostra · "
          f"{len(triados)} passaram na triagem · {len(res)} aprofundados · {len(passam)} com mercado ≥ 60%")
    if api.falhas:
        print(f"⚠️ {api.falhas} falhas de rede no Sofascore: rode de novo (o cache acelera).")
    lista = passam if a.curto else res
    if not lista:
        print("Nenhum jogo com defesa fraca x ataque forte e mercado ≥ 60%.")
    for x in lista:
        print(linha_curta(x["n"], x, cfg["criterios"]["prob_minima"], cfg["criterios"]["ev_minimo"]))
    print(f"JSON completo: {arq.relative_to(n.RAIZ)}")


if __name__ == "__main__":
    main()
