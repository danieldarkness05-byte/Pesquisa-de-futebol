#!/usr/bin/env python3
"""Dossiê dos candidatos da peneira, para o /aprofundar e o /ouro.

Junta só com Python e o Sofascore, sem gastar agentes, o que a pesquisa de
imprensa precisa receber pronto:
- reavaliação com as odds de agora: o candidato continua vivo? Se caiu, por quê;
- movimento das odds desde a abertura (o mercado foi contra ou a favor?);
- desfalques do Sofascore e quantos gols da liga cada desfalcado marcou;
- artilheiros, forma, posição, técnicos, árbitro, local, chuva e minutos para o início.

Lê dados/cache/sofascore/peneira-AAAA-MM-DD.json (rode a varredura antes).
Ignora jogos que começam em menos de `aprofundar.min_minutos_antes` minutos.

Exemplos:
  python3 ferramentas/dossie.py                  # os N primeiros (config.json → aprofundar.max_candidatos)
  python3 ferramentas/dossie.py --numeros 1,3    # números da peneira de hoje
  python3 ferramentas/dossie.py --json           # entrada do workflow `aprofundar`
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

import nucleo as n
import varredura as V

APROF_PADRAO = {"max_candidatos": 3, "min_minutos_antes": 20, "cetico": True}


def config() -> dict:
    cfg = n.carregar_config()
    cfg["varredura"] = {**V.VARREDURA_PADRAO, **{k: v for k, v in cfg.get("varredura", {}).items()
                                                 if not k.startswith("_")}}
    cfg["aprofundar"] = {**APROF_PADRAO, **{k: v for k, v in cfg.get("aprofundar", {}).items()
                                            if not k.startswith("_")}}
    return cfg


def chave(c: dict) -> tuple:
    return (c["mercado"], c["linha"], c["escolha"])


def selecionar(cands: list[dict], numeros: list[int] | None, maximo: int) -> list[tuple[int, dict]]:
    """(número na peneira, candidato). Sem números: os `maximo` primeiros."""
    if numeros:
        return [(i, cands[i - 1]) for i in numeros if 1 <= i <= len(cands)]
    return list(enumerate(cands, 1))[:maximo]


def gols_por_jogador(incidentes: list[list[dict]], em_casa: list[bool]) -> tuple[dict[int, int], int, dict[int, str]]:
    """Gols do time por id de jogador (gol contra fica fora da conta individual)."""
    gols, total, nomes = {}, 0, {}
    for inc, casa in zip(incidentes, em_casa):
        for i in inc:
            if i.get("incidentType") != "goal" or i.get("isHome") != casa:
                continue
            total += 1
            p = i.get("player") or {}
            if i.get("incidentClass") == "ownGoal" or "id" not in p:
                continue
            gols[p["id"]] = gols.get(p["id"], 0) + 1
            nomes[p["id"]] = p.get("shortName") or p.get("name", "?")
    return gols, total, nomes


def odds_escolha(odds: dict, k: tuple) -> list | None:
    """[abertura, agora] da escolha do candidato."""
    for mk in odds.get("markets", []):
        if (mk.get("marketName"), mk.get("choiceGroup")) != (k[0], k[1]):
            continue
        for c in mk.get("choices", []):
            if c.get("name") == k[2]:
                ini = c.get("initialFractionalValue")
                return [round(V.odd_decimal(ini), 3) if ini else None, round(V.odd_decimal(c["fractionalValue"]), 3)]
    return None


def odds_1x2(odds: dict) -> dict:
    for mk in odds.get("markets", []):
        if mk.get("marketName") == "Full time":
            return {c["name"]: [round(V.odd_decimal(c["initialFractionalValue"]), 2) if c.get("initialFractionalValue") else None,
                                round(V.odd_decimal(c["fractionalValue"]), 2)] for c in mk.get("choices", [])}
    return {}


def motivo_queda(info: dict, k: tuple, cfg: dict) -> tuple[str, dict | None]:
    """Por que o candidato não passa mais, com os números de agora."""
    if not info.get("variantes"):
        return info.get("motivo") or "jogo não avaliado", None
    base = info["variantes"]["base"].get(k)
    if base is None:
        return "linha/mercado não está mais nas odds", None
    so_ele = {nome: {k: var[k]} for nome, var in info["variantes"].items() if k in var}
    xh, xa = info["amostras"]
    _, motivo = V.filtrar(so_ele, xh, xa, cfg["varredura"], cfg["criterios"]["ev_minimo"], info.get("taxa_base"))
    if not motivo:
        motivo = f"sem valor agora (prob. {base['p']:.1%}, EV {base['ev']:+.1%})"
    return motivo, base


def contexto_jogo(api: V.Sofascore, e: dict, info: dict) -> dict:
    eid, ut = e["id"], V.torneio_id(e)
    temporada = (e.get("season") or {}).get("id")
    lu = api.get(f"event/{eid}/lineups", cache=None)
    pf = api.get(f"event/{eid}/pregame-form", cache=None)
    mg = api.get(f"event/{eid}/managers", cache=None)
    out = {"escalacao_confirmada": bool(lu.get("confirmed")), "desfalques": {}, "artilheiros": {},
           "gols_liga": {}, "forma": {}, "tecnicos": [(mg.get("homeManager") or {}).get("name"),
                                                       (mg.get("awayManager") or {}).get("name")]}
    for lado, tkey, sofa in (("casa", "homeTeam", "home"), ("fora", "awayTeam", "away")):
        tid = e[tkey]["id"]
        evs = [x for x in V.ultimos_eventos(api, tid)
               if V.torneio_id(x) == ut and (x.get("season") or {}).get("id") == temporada
               and x["status"]["type"] == "finished"]
        incs = V.em_paralelo(lambda x: api.get(f"event/{x['id']}/incidents", cache="fixo").get("incidents", []), evs, 4)
        gols, total, nomes = gols_por_jogador(incs, [x["homeTeam"]["id"] == tid for x in evs])
        out["gols_liga"][lado] = total
        out["artilheiros"][lado] = [[nomes[p], g] for p, g in sorted(gols.items(), key=lambda x: -x[1])[:5]]
        out["desfalques"][lado] = [{
            "jogador": m["player"].get("name"), "posicao": m["player"].get("position"),
            "tipo": m.get("type"), "motivo": m.get("description") or m.get("reason"),
            "volta": (m.get("expectedEndDate") or "")[:10] or None,
            "gols_liga": gols.get(m["player"].get("id"), 0)} for m in (lu.get(sofa) or {}).get("missingPlayers", [])]
        f = (pf.get(f"{sofa}Team") or {})
        out["forma"][lado] = {"posicao": f.get("position"), "ultimos": f.get("form"), "pontos": f.get("value")}
    loc = info.get("local") or {}
    out["local"] = ", ".join(x for x in (loc.get("estadio"), loc.get("cidade"), loc.get("pais")) if x)
    out["arbitro"] = info.get("arbitro")
    return out


def montar(data: str, numeros: list[int] | None, cfg: dict, sufixo: str | None = None) -> dict:
    arq = V.CACHE_PADRAO / f"peneira-{data}{'-' + sufixo if sufixo else ''}.json"
    if not arq.exists():
        sys.exit(f"Sem peneira de {data}. Rode antes: python3 ferramentas/varredura.py --curto")
    pen = json.loads(arq.read_text(encoding="utf-8"))
    ap = cfg["aprofundar"]
    escolhidos = selecionar(pen["candidatos"], numeros, ap["max_candidatos"])
    api = V.Sofascore(V.CACHE_PADRAO, data)
    agora = datetime.now(V.FUSO_BR)
    res = {"data": data, "consultado": agora.strftime("%H:%M"), "peneira_das": pen.get("consultado"),
           "criterios": cfg["criterios"], "regra8_pp": cfg["varredura"]["regra8_pp"], "aprofundar": ap,
           "total_peneira": len(pen["candidatos"]), "candidatos": [], "fora": []}
    cache_liga: dict = {}
    jogos: dict[int, dict] = {}
    for num, c in escolhidos:
        if c["id"] not in jogos:
            e = api.get(f"event/{c['id']}", cache=None).get("event") or {}
            minutos = round((e.get("startTimestamp", 0) - agora.timestamp()) / 60) if e else None
            if not e or e["status"]["type"] != "notstarted" or minutos < ap["min_minutos_antes"]:
                jogos[c["id"]] = {"fora": "já começou" if e and minutos is not None and minutos <= 0
                                  else f"começa em {minutos} min" if e else "jogo não encontrado"}
            else:
                info = V.analisar_jogo(api, e, cfg, cache_liga)
                jogos[c["id"]] = {"e": e, "info": info, "minutos": minutos,
                                  "ctx": contexto_jogo(api, e, info), "odds": api.get(f"event/{c['id']}/odds/1/all", cache=None),
                                  "chuva": V.checar_chuva(info, data, cfg) if info.get("local") else
                                  {"status": "não verificada", "detalhe": "sem local"}}
        j = jogos[c["id"]]
        if "fora" in j:
            res["fora"].append({"n": num, "jogo": c["jogo"], "hora": c["hora"], "rotulo": c["rotulo"], "motivo": j["fora"]})
            continue
        k, info = chave(c), j["info"]
        vivo = next((x for x in info["candidatos"] if chave(x) == k), None)
        motivo, base = (None, vivo) if vivo else motivo_queda(info, k, cfg)
        atual = vivo or base or {}
        res["candidatos"].append({
            "n": num, "id": c["id"], "jogo": c["jogo"], "competicao": c["competicao"], "hora": c["hora"],
            "min_para_inicio": j["minutos"], "mercado": c["rotulo"], "chave": list(k),
            "status": "vivo" if vivo else "caiu", "motivo_queda": motivo,
            "p_modelo": round(atual.get("p", c["p"]), 4), "p_peneira": round(c["p"], 4),
            "p_min_variantes": round(vivo["p_min"], 4) if vivo else None,
            "variantes": vivo["variantes"] if vivo else c.get("variantes"),
            "frequencia_amostras": vivo["frequencia"] if vivo else c.get("frequencia"),
            "devolucao": round(atual.get("dev", 0.0), 4),
            "odd_peneira": c["odd"], "odd_agora": atual.get("odd"),
            "prob_mercado_sem_margem": round(atual["justa_mercado"], 4) if atual.get("justa_mercado") else None,
            "ev_agora": round(atual["ev"], 4) if "ev" in atual else None,
            "odd_minima": round(atual["odd_minima"], 3) if atual.get("odd_minima") else None,
            "gols_esperados": [round(x, 3) for x in info["lambda"]] if info.get("lambda") else None,
            "amostra_jogos": info.get("amostra"),
            "odds_movimento": {"escolha_abertura_agora": odds_escolha(j["odds"], k), "1x2_abertura_agora": odds_1x2(j["odds"])},
            "chuva": j["chuva"], **j["ctx"]})
    return res


def imprimir_curto(res: dict) -> None:
    print(f"📋 Dossiê {res['data']} ({res['consultado']}) — {len(res['candidatos'])} candidato(s)")
    for c in res["candidatos"]:
        mov = c["odds_movimento"]["escolha_abertura_agora"]
        mov_txt = f" · odd {mov[0]}→{mov[1]}" if mov and mov[0] else ""
        estado = "VIVO" if c["status"] == "vivo" else f"CAIU: {c['motivo_queda']}"
        print(f"{c['n']}) {c['hora']} {c['jogo']} · {c['mercado']} · modelo {c['p_modelo']:.1%} · "
              f"mercado {c['prob_mercado_sem_margem'] or 0:.1%}{mov_txt} · {estado}")
        for lado in ("casa", "fora"):
            ds = [f"{d['jogador']} ({d['gols_liga']}g)" if d["gols_liga"] else d["jogador"] for d in c["desfalques"][lado]]
            if ds:
                print(f"   desfalques {lado} ({c['gols_liga'][lado]} gols na liga): {', '.join(ds)}")
        print(f"   chuva: {c['chuva']['status']} · escalação confirmada: {'sim' if c['escalacao_confirmada'] else 'não'}")
    for f in res["fora"]:
        print(f"{f['n']}) {f['hora']} {f['jogo']} · {f['rotulo']} · fora: {f['motivo']}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", help="AAAA-MM-DD (padrão: hoje, Brasília)")
    p.add_argument("--numeros", help="números da peneira, ex.: 1,3 (padrão: os N primeiros do config)")
    p.add_argument("--json", action="store_true")
    p.add_argument("--sufixo", help="lê peneira-AAAA-MM-DD-<sufixo>.json (ex.: todas, da varredura --todas)")
    p.add_argument("--max", type=int, help="quantos candidatos (padrão: aprofundar.max_candidatos)")
    p.add_argument("--prob-min", type=float, help="corte da reavaliação (o mesmo da varredura), ex.: 0.70")
    a = p.parse_args()
    cfg = config()
    if a.max is not None:
        cfg["aprofundar"]["max_candidatos"] = a.max
    if a.prob_min:
        cfg["varredura"]["prob_triagem"] = a.prob_min if a.prob_min <= 1 else a.prob_min / 100
    data = a.data or datetime.now(V.FUSO_BR).date().isoformat()
    nums = [int(x) for x in a.numeros.split(",") if x.strip()] if a.numeros else None
    res = montar(data, nums, cfg, a.sufixo)
    if a.json:
        print(json.dumps(res, ensure_ascii=False, default=str))
    else:
        imprimir_curto(res)


if __name__ == "__main__":
    main()
