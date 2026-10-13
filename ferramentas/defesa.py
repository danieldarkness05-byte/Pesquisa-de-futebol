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
import re
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
    "forma_jogos": 5,
    "forma_aproveitamento_min": 0.5,
    "palavras_amistoso": ["Friendly", "Friendlies", "Amistoso"],
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


def nivel_base(textos: list[str], palavras: list[str], times: list[str] = ()) -> bool:
    """Liga amadora, universitária, de base, feminina ou time reserva (" II"/" B"
    no fim do NOME DO TIME; numeral na liga, como "NB II", não conta)."""
    alvo = " ".join(t for t in list(textos) + list(times) if t).lower()
    return (any(p.lower() in alvo for p in palavras)
            or any(re.search(r"\s(II|B)$", t or "") for t in times))


def frequencias(fav: list[dict], az: list[dict]) -> dict:
    """Frequência real nas amostras: favorito marcou k+ e azarão sofreu k+."""
    out = {}
    for k in (1, 2, 3):
        f = [x["gf"] >= k for x in fav]
        a = [x["ga"] >= k for x in az]
        out[f"fav_{k}"] = sum(f) / len(f) if f else None
        out[f"az_{k}"] = sum(a) / len(a) if a else None
    out["fav_vence"] = sum(x["gf"] > x["ga"] for x in fav) / len(fav) if fav else None
    out["az_perde"] = sum(x["ga"] > x["gf"] for x in az) / len(az) if az else None
    out["fav_nao_perde"] = sum(x["gf"] >= x["ga"] for x in fav) / len(fav) if fav else None
    out["az_nao_vence"] = sum(x["ga"] >= x["gf"] for x in az) / len(az) if az else None
    out["mediana_ga_az"] = statistics.median([x["ga"] for x in az]) if az else None
    out["mediana_gf_fav"] = statistics.median([x["gf"] for x in fav]) if fav else None
    return out


FREQ_CHAVES = {"fav_marca_1": ("fav_1", "az_1"), "fav_marca_2": ("fav_2", "az_2"), "fav_marca_3": ("fav_3", "az_3"),
               "fav_vence": ("fav_vence", "az_perde"), "fav_dc": ("fav_nao_perde", "az_nao_vence")}


def freq_mercado(freq: dict, chave: str | int) -> float | None:
    """Frequência de referência do mercado: média das duas pontas (favorito na
    condição dele e azarão na condição dele). `chave` int = 'favorito marca k+'."""
    if isinstance(chave, int):
        chave = f"fav_marca_{chave}"
    vals = [freq.get(k) for k in FREQ_CHAVES.get(chave, ())]
    vals = [x for x in vals if x is not None]
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


def odd_minima(p: float, ev_min: float) -> float | None:
    return round((1 + ev_min) / p, 2) if p > 0 else None


def ajuste_empate_vitoria(p_vence: float, p_empate: float, empates_liga: float | None) -> float:
    """A Poisson subestima empates: com a taxa real da liga maior, reescala a vitória."""
    if empates_liga is None or empates_liga <= p_empate or p_empate >= 1:
        return p_vence
    return p_vence * (1 - empates_liga) / (1 - p_empate)


def lambdas_mercado(p1x2: list[float], p_overs: dict[float, float] | None = None) -> tuple[float, float]:
    """λ (mandante, visitante) que reproduzem o 1X2 sem margem e as linhas de gols
    sem margem que houver (`p_overs` = {linha: P(over)}). Busca em grade 2D com
    Poisson simples; o 1X2 sozinho já identifica os dois λ."""
    linhas = sorted((p_overs or {}).items())

    def erro(lh, la):
        m = n.matriz_placar(lh, la, 0.0, 10)
        r = v.resultado(m)
        e = (r["1"] - p1x2[0]) ** 2 + (r["X"] - p1x2[1]) ** 2 + (r["2"] - p1x2[2]) ** 2
        for linha, po in linhas:
            e += (v.total_gols(m, linha, "over")[0] - po) ** 2
        return e

    passos = [x / 10 for x in range(1, 51)]
    melhor = min((erro(lh, la), lh, la) for lh in passos for la in passos)
    for passo in (0.02, 0.005):  # refinamento ao redor do melhor ponto
        _, lh, la = melhor
        viz = [(lh + a * passo, la + b * passo) for a in range(-6, 7) for b in range(-6, 7)
               if lh + a * passo > 0.02 and la + b * passo > 0.02]
        melhor = min([melhor] + [(erro(x, y), x, y) for x, y in viz])
    return round(melhor[1], 3), round(melhor[2], 3)


def tendencia(xs: list[dict], chave: str, ultimos: int = 5) -> tuple[float | None, float | None]:
    """(média dos últimos `ultimos`, média da amostra toda)."""
    vals = [x[chave] for x in xs if x.get(chave) is not None]
    if len(vals) < ultimos + 2:
        return None, (sum(vals) / len(vals) if vals else None)
    return sum(vals[-ultimos:]) / ultimos, sum(vals) / len(vals)


def media_chave(xs: list[dict], chave: str, cobertura: float = 0.7) -> float | None:
    vals = [x[chave] for x in xs if x.get(chave) is not None]
    return sum(vals) / len(vals) if xs and len(vals) / len(xs) >= cobertura else None


def forma(eventos: list[dict], tid: int, antes_ts: int, qtd: int, palavras_amistoso: list[str]) -> dict:
    """Últimos `qtd` jogos OFICIAIS encerrados do time antes de `antes_ts` (todas as
    competições, sem amistosos), do mais antigo ao mais recente. Placar dos 90 min."""
    oficiais = []
    for e in sorted(eventos, key=lambda e: e["startTimestamp"]):
        torneio = " ".join(str(x) for x in ((e.get("tournament") or {}).get("name"),
                                            ((e.get("tournament") or {}).get("uniqueTournament") or {}).get("name")))
        if (e.get("status", {}).get("type") != "finished" or e["startTimestamp"] >= antes_ts
                or any(p.lower() in torneio.lower() for p in palavras_amistoso)):
            continue
        hs, as_ = v.placar(e, "home"), v.placar(e, "away")
        if hs is None or as_ is None:
            continue
        meu, dele = (hs, as_) if e["homeTeam"]["id"] == tid else (as_, hs)
        oficiais.append("V" if meu > dele else "E" if meu == dele else "D")
    seq = oficiais[-qtd:]
    return {"seq": "".join(seq), "v": seq.count("V"), "e": seq.count("E"), "d": seq.count("D"),
            "pts": 3 * seq.count("V") + seq.count("E"), "n": len(seq)}


def forma_negativa(f: dict, aproveitamento_min: float = 0.5) -> bool:
    """Regra do Daniel (13/10): favorito com menos da metade dos pontos nos últimos
    jogos oficiais sai da lista (em 5 jogos: menos de 8 de 15)."""
    return f.get("n", 0) > 0 and f["pts"] < aproveitamento_min * 3 * f["n"]


def calendario(eventos_passados: list[dict], eventos_futuros: list[dict], inicio_ts: int, dias: int) -> dict:
    """Jogos do favorito na janela de `dias` em volta deste (antes e depois)."""
    janela = dias * 86400
    antes = [e for e in eventos_passados
             if e.get("status", {}).get("type") == "finished" and 0 < inicio_ts - e["startTimestamp"] < janela]
    depois = [e for e in eventos_futuros if 0 < e["startTimestamp"] - inicio_ts < janela]
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
    for r8 in info.get("regra8_mercados") or []:
        al.append(r8)
    if info.get("motivo"):
        al.append(info["motivo"])
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


def grupos_tabela(api: v.Sofascore, ut: int, s: int, tipo: str) -> list[dict]:
    """[{nome, rows: {time: linha}}] — uma liga pode ter vários grupos ou fases."""
    return [{"nome": g.get("name"), "rows": {r["team"]["id"]: r for r in g.get("rows", [])}}
            for g in api.get(f"unique-tournament/{ut}/season/{s}/standings/{tipo}").get("standings", [])]


def escolher_grupo(grupos: list[dict], times: tuple[int, int], nome_torneio: str | None = None) -> dict[int, dict]:
    """Linhas do grupo em que os DOIS times do jogo já jogaram (no empate, o de nome
    igual ao do torneio ou o de mais jogos). Sem grupo comum: junta ficando com a
    linha de mais jogos de cada time — nunca a do último grupo listado."""
    comuns = [g for g in grupos if all(g["rows"].get(t, {}).get("matches", 0) > 0 for t in times)]
    if comuns:
        def chave(g):
            return (g["nome"] == nome_torneio, sum(r.get("matches", 0) for r in g["rows"].values()))
        return max(comuns, key=chave)["rows"]
    rows: dict[int, dict] = {}
    for g in grupos:
        for t, r in g["rows"].items():
            if t not in rows or r.get("matches", 0) > rows[t].get("matches", 0):
                rows[t] = r
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


def expulsao_relevante(i: dict, casa: bool, minuto_max: int = 80) -> bool:
    """Vermelho (direto ou 2º amarelo) de JOGADOR do time, não anulado, até `minuto_max`
    (expulsão nos acréscimos não infla os gols sofridos; técnico não conta)."""
    return (i.get("incidentType") == "card" and i.get("incidentClass") in ("red", "yellowRed")
            and i.get("isHome") == casa and not i.get("rescinded") and "manager" not in i
            and (i.get("player") is not None or "playerName" in i) and (i.get("time") or 0) <= minuto_max)


def expulsoes(api: v.Sofascore, xs: list[dict], tid_casa: dict[int, bool]) -> int:
    """Jogos da amostra em que o time teve jogador expulso até os 80'."""
    tot = 0
    for x in xs:
        inc = api.get(f"event/{x['id']}/incidents", cache="fixo").get("incidents", [])
        casa = tid_casa[x["id"]]
        if any(expulsao_relevante(i, casa) for i in inc):
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
        cache[(ut, s)] = tuple(grupos_tabela(api, ut, s, t) for t in ("home", "away", "total"))
    h, a = e["homeTeam"]["id"], e["awayTeam"]["id"]
    nome_t = e["tournament"].get("name")
    th, ta, tt = (escolher_grupo(g, (h, a), nome_t) for g in cache[(ut, s)])
    if not th or not ta or h not in th or a not in ta:
        motivos["sem tabela casa/fora (copa, amistoso, seleção)"] += 1
        return None
    jogos = sum(r["matches"] for r in th.values())
    if not jogos:
        motivos["tabela vazia"] += 1
        return None
    lh = sum(r["scoresFor"] for r in th.values()) / jogos
    la = sum(r["scoresAgainst"] for r in th.values()) / jogos
    tot_j = sum(r.get("matches", 0) for r in tt.values())
    empates = (sum(r.get("draws", 0) for r in tt.values()) / tot_j) if tot_j else None
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
        "liga": {"casa": round(lh, 3), "fora": round(la, 3),
                 "empates": round(empates, 3) if empates is not None else None},
        "tabela": {"casa": {k: rh[k] for k in ("matches", "scoresFor", "scoresAgainst")},
                   "fora": {k: ra[k] for k in ("matches", "scoresFor", "scoresAgainst")}},
        "az_ga": round(az_ga, 2), "az_gf": round(az_gf, 2), "fav_gf": round(fav_gf, 2),
        "ind_def": ind_def, "ind_atq": ind_atq,
        "rank_pior_defesa_az": ranking(t_az, "scoresAgainst", aid), "rank_ataque_fav": ranking(t_fv, "scoresFor", fid),
        "rank_ataque_az": rank_az,
        "risco": eh_risco(az_gf, rank_az, d),
        "amostra_pequena": min(fv["matches"], az["matches"]) < d["amostra_boa"],
        "nivel_base": nivel_base([cat, e["tournament"].get("name")], d["palavras_base"], [casa, fora]),
    }
    info["pontuacao"] = pontuacao(info, d)
    return info


def matriz_e_probs(lh: float, la: float, fav_casa: bool, rho: float, sigma: float) -> dict:
    m = v.matriz(lh, la, rho, sigma)
    r = v.resultado(m)
    out = {f"fav_marca_{k}": prob_time_marca(m, fav_casa, k) for k in (1, 2, 3)}
    out["fav_vence"] = r["1"] if fav_casa else r["2"]
    out["fav_dc"] = r["1X"] if fav_casa else r["X2"]
    out["empate"] = r["X"]
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
    info["forma_favorito"] = forma(evf, fid, info["inicio"], d["forma_jogos"], d["palavras_amistoso"])

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

    # mercado: λ implícito do 1X2 + linhas de gols (regra 8); vitória/DC direto do 1X2/DC sem margem
    mo = info["mercado_odds"]
    p_merc = None
    if mo.get("1x2"):
        inv = [1 / x for x in mo["1x2"]]
        p1x2 = [x / sum(inv) for x in inv]
        p_ov = {float(lin): (1 / o) / (1 / o + 1 / u) for lin, (o, u) in mo["over"].items()}
        lm = lambdas_mercado(p1x2, p_ov)
        p_merc = matriz_e_probs(*lm, fav_casa, 0.0, 0.0)
        p_merc["fav_vence"] = p1x2[0 if fav_casa else 2]
        p_merc["fav_dc"] = p1x2[0 if fav_casa else 2] + p1x2[1]
        info["lambdas"]["mercado"] = list(lm)

    # mercados do favorito (todos com o teto da frequência real)
    ev_min = cfg["criterios"]["ev_minimo"]
    empates_liga = lg.get("empates")
    mercados = []
    rotulos = {c: r for c, r, _ in MERCADOS}
    rotulos.update({"fav_vence": "vitória do {fav}", "fav_dc": "dupla chance {fav}"})
    for chave, rot in rotulos.items():
        if not variantes:
            break
        vals = []
        for _, pr in variantes.values():
            val = pr[chave]
            if chave == "fav_vence":   # a Poisson subestima empates
                val = ajuste_empate_vitoria(val, pr["empate"], empates_liga)
            vals.append(val)
        fr = freq_mercado(info["frequencias"], chave)
        p, limitada = prob_conservadora(vals, fr, d["tolerancia_frequencia"])
        odd = None
        if chave == "fav_vence" and mo.get("1x2"):
            odd = mo["1x2"][0 if fav_casa else 2]
        elif chave == "fav_dc" and mo.get("dc"):
            odd = mo["dc"].get("1X" if fav_casa else "X2")
        item = {"chave": chave, "mercado": rot.format(fav=info["favorito"]), "prob": round(p, 3),
                "variantes": {nome: round(pr[chave], 3) for nome, (_, pr) in variantes.items()},
                "frequencia": round(fr, 3) if fr is not None else None, "limitada_pela_frequencia": limitada,
                "odd_minima": odd_minima(p, ev_min), "odd_casa": odd,
                "ev": round(p * odd - 1, 3) if odd else None, "prob_mercado": None, "regra8": False}
        if p_merc:
            item["prob_mercado"] = round(p_merc[chave], 3)
            item["regra8"] = p - p_merc[chave] > d["regra8_pp"]
        mercados.append(item)
    info["mercados"] = mercados

    crit = cfg["criterios"]
    passam = mercados_que_passam(info, crit["prob_minima"], crit["ev_minimo"])
    gol = [x for x in passam if x["chave"].startswith("fav_marca")]
    info["melhor_mercado"] = (max(gol, key=lambda x: x["chave"]) if gol else (passam[0] if passam else None))
    info["regra8_mercados"] = [
        f"regra 8 ({x['mercado'].replace(info['favorito'], 'fav')}): modelo {x['prob']:.0%} x mercado "
        f"{x['prob_mercado']:.0%} (+{(x['prob'] - x['prob_mercado']) * 100:.0f} p.p.) — procurar o que o mercado sabe"
        for x in passam if x.get("regra8")]
    # dado faltando (regra 6): sem amostra de últimos jogos não há teto de frequência nem λ encolhido
    info["motivo"] = None
    if min(len(xf), len(xa)) < 3 or freq_mercado(info["frequencias"], 1) is None:
        info["motivo"] = f"dado faltando: só {len(xf)}/{len(xa)} jogos recentes na condição"
    fm = info["forma_favorito"]
    if not info["motivo"] and forma_negativa(fm, d["forma_aproveitamento_min"]):
        info["motivo"] = (f"fora pela forma: favorito fez {fm['pts']} de {3 * fm['n']} pontos nos últimos {fm['n']} "
                          f"oficiais ({fm['v']}V {fm['e']}E {fm['d']}D: {fm['seq']})")
    det = api.get(f"event/{eid}").get("event", {})
    venue = det.get("venue") or {}
    info["local"] = {"estadio": venue.get("name"), "cidade": (venue.get("city") or {}).get("name"),
                     "pais": (venue.get("country") or {}).get("alpha2"), "coord": venue.get("venueCoordinates")}
    info["chuva"] = v.checar_chuva(info, data, cfg) if chuva else {"status": "não consultada"}
    info["alertas"] = alertas_estatisticos(info, d)
    info["passa"] = info["melhor_mercado"] is not None and info["motivo"] is None
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
    ms = mercados_que_passam(x, prob_min, ev_min) if x.get("passa") else []
    merc = (" · ".join(f"{m['mercado'].replace(x['favorito'], 'fav')} {m['prob']:.0%} (mín {m['odd_minima'] or 0:.2f}"
                       + (f", bet365 {m['odd_casa']:.2f} EV {m['ev']:+.0%}" if m.get("odd_casa") else "") + ")"
                       for m in ms) if ms else (x.get("motivo") or "nenhum mercado ≥ 60%"))
    az = x["azarao_amostra"]
    return (f"{i}) {x['hora']} {x['jogo']} [{x['pais']} · {x['competicao']}]\n"
            f"   azarão {x['azarao']} sofre {x['az_ga']:.2f}/j (×{x['ind_def']}; últimos {az['n']}: {az['ga']}, "
            f"xG contra {az['xg_contra']}) | {x['favorito']} marca {x['fav_gf']:.2f}/j (×{x['ind_atq']}), "
            f"forma {(x.get('forma_favorito') or {}).get('seq') or 'N/D'}\n"
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
        if not a.data and jogos:  # sem --data, o rótulo e o arquivo seguem a data do jogo
            data = v.hora_br(jogos[0]["startTimestamp"]).date().isoformat()
    else:
        tc = cfg.get("varredura", {}).get("torneios_sofascore", {})
        torneios = {int(k) for k in tc} if (a.config or not d["todas_as_ligas"]) else None
        jogos = listar(api, data, torneios)
    total = len(jogos)

    # --ids: sem corte da triagem (aprofunda o que foi pedido), mas o resto usa o d original
    d_triagem = dict(d, indice_defesa_min=0, indice_ataque_min=0, amostra_minima_tabela=1) if a.ids else d

    def seguro_triar(e):
        try:
            return triar(api, e, d_triagem, motivos, cache)
        except Exception as exc:  # um jogo com dado quebrado não derruba a varredura
            motivos[f"erro {type(exc).__name__}"] += 1
            return None

    triados = [x for x in v.em_paralelo(seguro_triar, jogos, 6) if x]
    # profissional e com amostra boa primeiro: amador/base com índice enorme não toma a vaga
    triados.sort(key=lambda x: (x["nivel_base"], x["amostra_pequena"], -x["pontuacao"]))
    alvo = triados[: a.max or d["max_aprofundar"]]

    def seguro_aprof(x):
        try:
            dia = v.hora_br(x["inicio"]).date().isoformat()   # no --ids o jogo pode ser de outro dia
            return aprofundar(api, x, cfg, d, dia, chuva=not a.sem_chuva)
        except Exception as exc:
            x["erro"] = f"{type(exc).__name__}: {exc}"[:200]
            x["passa"] = False
            return x

    res = v.em_paralelo(seguro_aprof, alvo, 4)
    # ordem comparável entre jogos: prob. de "favorito marca 1+" e quantos mercados passam
    def p_marca1(x):
        return next((m["prob"] for m in x.get("mercados", []) if m["chave"] == "fav_marca_1"), 0)

    crit = cfg["criterios"]
    res.sort(key=lambda x: (not x.get("passa"), x.get("risco", False), x.get("nivel_base", False), -p_marca1(x),
                            -len(mercados_que_passam(x, crit["prob_minima"], crit["ev_minimo"])), -x["pontuacao"]))
    for i, x in enumerate(res, 1):
        x["n"] = i
    saida = {"data": data, "gerado": datetime.now(v.FUSO_BR).strftime("%Y-%m-%d %H:%M"),
             "jogos_listados": total, "motivos": dict(motivos), "triados": len(triados),
             "aprofundados": len(res), "criterios": cfg["criterios"], "defesa": d, "candidatos": res,
             "fora_do_corte": [{"jogo": x["jogo"], "hora": x["hora"], "pontuacao": x["pontuacao"]}
                               for x in triados[len(alvo):]],
             "falhas_rede": api.falhas}
    arq = v.CACHE_PADRAO / (f"defesa-{data}-ids.json" if a.ids else f"defesa-{data}.json")
    arq.parent.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(saida, ensure_ascii=False, indent=1, allow_nan=False)
    arq.write_text(texto, encoding="utf-8")
    if a.json:
        print(texto)
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
