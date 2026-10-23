#!/usr/bin/env python3
"""Outras plataformas com as mesmas informações do Sofascore (pedido do Daniel em 21/10).

Hoje: **365Scores** (API pública, abre daqui mesmo quando o Sofascore responde 403). Tem o mesmo conteúdo:
jogos do dia, tabela casa/fora, resultados de cada time, H2H, estádio, escalação e 1X2.

  confere  confirma no 365Scores os unders do Sofascore (peneira-<D>-under.json): hora, estádio, médias
           casa/fora, cauda, cauda na condição, H2H na linha e a prob. do under refeita com os números do
           365Scores. Marca CONFIRMADO, DIVERGENTE ou NAO_ACHADO e grava confere-<D>.json.
  mapa     sem o Sofascore: todos os jogos do dia no 365Scores, under 2.5/3.5/4.5 com prob. ≥ prob_min e cauda
           limpa, no formato do dossiê (entra direto no workflow under.js). Under com o 1X2 de um time caindo
           10% ou mais desde a abertura sai (status "caiu"; lição 67, Daniel 22/10: "tirar o under da lista").
  recheca  relê o 1X2 de agora (sem cache) dos unders do dossiê ou das previsões pendentes da data e diz OK ou
           CORTA pela mesma régua. Rode antes de entregar e de novo 1 a 2 h antes de cada jogo.

Probabilidade: método de força (nucleo) com as médias casa/fora da temporada e da liga do 365Scores,
encolhidas para a média da liga, e matriz com a incerteza da varredura. Vale a menor entre a tabela da
temporada e os últimos 10 jogos na condição (como as variantes da varredura).

Exemplos:
  python3 ferramentas/plataformas.py confere --data 2026-10-21
  python3 ferramentas/plataformas.py mapa --data 2026-10-21 --json > dossie-365.json
  python3 ferramentas/plataformas.py anexa --dossie dossie-under.json   # põe a conferência em cada candidato
  python3 ferramentas/plataformas.py recheca --data 2026-10-22            # previsões pendentes da data
  python3 ferramentas/plataformas.py recheca --dossie dossie-under.json   # candidatos do dossiê

Só Python padrão. Cache em dados/cache/365scores/<data>/.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import defesa as df  # noqa: E402
import nucleo as n  # noqa: E402
import under as un  # noqa: E402
import varredura as v  # noqa: E402

API = "https://webws.365scores.com/web/"
BASE_Q = {"appTypeId": 5, "langId": 1, "timezoneName": "America/Sao_Paulo", "userCountryId": 21}
RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "dados" / "cache" / "365scores"
SOFA = RAIZ / "dados" / "cache" / "sofascore"
BRT = timezone(timedelta(hours=-3))
LINHAS = (2.5, 3.5, 4.5)
FIM, AGENDADO = 4, 2
QUEDA_1X2_MAX = 0.10   # lição 67: odd de vitória de um time caindo 10%+ desde a abertura tira o under


class S365:
    """Cliente do 365Scores com cache em disco (vale para o dia da consulta)."""

    def __init__(self, data: str, pasta: Path | None = PASTA):
        self.data, self.pasta, self.falhas = data, pasta, 0

    def get(self, caminho: str, **q) -> dict:
        arq = None
        if self.pasta:
            nome = re.sub(r"[^A-Za-z0-9_.-]", "_", caminho + "_" + urllib.parse.urlencode(sorted(q.items()))) + ".json"
            arq = self.pasta / self.data / f"lang{BASE_Q['langId']}" / nome
            if arq.exists():
                try:
                    return json.loads(arq.read_text(encoding="utf-8"))
                except ValueError:
                    pass
        url = API + caminho + "?" + urllib.parse.urlencode({**BASE_Q, **q})
        req = urllib.request.Request(url, headers={"User-Agent": v.UA, "Accept": "application/json"})
        for i in range(3):
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    dado = json.loads(r.read().decode("utf-8"))
                time.sleep(0.1)
                if arq:
                    arq.parent.mkdir(parents=True, exist_ok=True)
                    arq.write_text(json.dumps(dado, ensure_ascii=False), encoding="utf-8")
                return dado
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    return {}
            except (urllib.error.URLError, TimeoutError, ValueError, OSError):
                pass
            time.sleep(1 + 2 * i)
        self.falhas += 1
        return {}

    def jogos(self) -> list[dict]:
        """Jogos do dia; cada um ganha `_pais` (a liga sozinha é ambígua: "Premier League")."""
        d = datetime.strptime(self.data, "%Y-%m-%d").strftime("%d/%m/%Y")
        r = self.get("games/allscores/", sports=1, startDate=d, endDate=d, showOdds="true",
                     onlyMajorGames="false", withTop="true")
        paises = {c["id"]: c.get("name") for c in r.get("countries", [])}
        comp_pais = {c["id"]: paises.get(c.get("countryId")) for c in r.get("competitions", [])}
        gs = r.get("games", [])
        for g in gs:
            g["_pais"] = comp_pais.get(g.get("competitionId"))
        return gs

    def tabela(self, comp: int, tipo: int) -> dict[int, dict]:
        """tipo 1 = geral, 2 = casa, 3 = fora → {id do time: linha}."""
        rows = {}
        for st in self.get("standings/", competitions=comp, type=tipo).get("standings", []):
            for r in st.get("rows", []):
                rows[r["competitor"]["id"]] = r
        return rows

    def resultados(self, time_id: int) -> list[dict]:
        gs = self.get("games/results/", competitors=time_id).get("games", [])
        return sorted((g for g in gs if g.get("statusGroup") == FIM and placar(g)), key=lambda g: g["startTime"], reverse=True)

    def h2h(self, jogo_id: int) -> list[dict]:
        gs = (self.get("games/h2h/", gameId=jogo_id).get("game") or {}).get("h2hGames", [])
        return sorted((g for g in gs if placar(g)), key=lambda g: g["startTime"], reverse=True)

    def detalhe(self, jogo_id: int) -> dict:
        return self.get("game/", gameId=jogo_id).get("game") or {}


# ---------------------------------------------------------------------------
# Funções puras (testadas)
# ---------------------------------------------------------------------------

def queda_1x2(odds: dict | None) -> dict | None:
    """Maior queda da odd de vitória (1 ou 2) desde a abertura: {"lado", "de", "para", "queda"}; None sem odds.

    Queda = 1 − agora/abertura. Lição 67: El Sekka 2.00 → 1.73 (13,5%) e 9 de Octubre 2.00 → 1.55 (22,5%) no
    dia do jogo, e os dois unders perderam (1-5 e 3-3)."""
    melhor = None
    for o in (odds or {}).get("options") or []:
        lado = {"1": "casa", "2": "fora"}.get(str(o.get("name")))
        de, para = (o.get("originalRate") or {}).get("decimal"), (o.get("rate") or {}).get("decimal")
        if not lado or not de or not para or de <= 1 or para <= 1:
            continue
        q = 1 - para / de
        if melhor is None or q > melhor["queda"]:
            melhor = {"lado": lado, "de": de, "para": para, "queda": round(q, 4)}
    return melhor


def corta_1x2(mov: dict | None, maximo: float) -> str | None:
    """Motivo do corte se a odd de um time caiu `maximo` ou mais desde a abertura (lição 67)."""
    if mov and mov["queda"] >= maximo:
        return f"1X2 do time de {mov['lado']} caiu {mov['queda']:.0%} desde a abertura ({mov['de']} → {mov['para']}; lição 67)"
    return None


def placar(g: dict) -> tuple[int, int] | None:
    h, a = (g.get("homeCompetitor") or {}).get("score"), (g.get("awayCompetitor") or {}).get("score")
    if h is None or a is None or h < 0 or a < 0:
        return None
    return int(h), int(a)


def amistoso(g: dict) -> bool:
    nome = (g.get("competitionDisplayName") or "").lower()
    return any(p in nome for p in ("amistoso", "friendl", "club friendly"))


def acima(totais: list[int], linha: float) -> int:
    return sum(1 for t in totais if t > linha)


def normaliza(nome: str) -> set[str]:
    s = unicodedata.normalize("NFKD", nome or "").encode("ascii", "ignore").decode().lower()
    fora = {"fc", "cf", "sc", "ac", "cd", "club", "de", "the", "afc", "fk", "sk", "if", "bk", "cp", "ca", "sd", "ud", "rc"}
    return {t for t in re.split(r"[^a-z0-9]+", s) if t and t not in fora}


def mesmo_time(a: str, b: str) -> bool:
    ta, tb = normaliza(a), normaliza(b)
    if not ta or not tb:
        return False
    return ta <= tb or tb <= ta or len(ta & tb) / len(ta | tb) >= 0.5


def medias_liga(casa: dict[int, dict], fora: dict[int, dict]) -> tuple[float, float] | None:
    """Gols por jogo do mandante e do visitante na liga, pelas tabelas casa e fora."""
    gc, jc = sum(r.get("for", 0) for r in casa.values()), sum(r.get("gamePlayed", 0) for r in casa.values())
    gf, jf = sum(r.get("for", 0) for r in fora.values()), sum(r.get("gamePlayed", 0) for r in fora.values())
    return (gc / jc, gf / jf) if jc and jf else None


def lambdas(h: tuple[float, float, int], a: tuple[float, float, int], liga: tuple[float, float], k: float) -> tuple[float, float]:
    """h = (marcados, sofridos, jogos) do mandante em casa; a = idem do visitante fora; encolhe para a liga."""
    lh, la = liga
    enc = lambda x, qtd, alvo: (qtd * x + k * alvo) / (qtd + k)  # noqa: E731
    return n.lambdas_por_medias(enc(h[0], h[2], lh), enc(h[1], h[2], la), enc(a[0], a[2], la), enc(a[1], a[2], lh), lh, la)


def p_under(lh: float, la: float, linha: float, sigma: float) -> float:
    return v.total_gols(v.matriz(lh, la, 0.0, sigma), linha, "under")[0]


def condicao(jogos: list[dict], time_id: int, em_casa: bool, comp: int | None, qtd: int) -> list[dict]:
    """Últimos jogos do time como mandante (ou visitante) na competição."""
    lado = "homeCompetitor" if em_casa else "awayCompetitor"
    return [g for g in jogos if g[lado]["id"] == time_id and (comp is None or g.get("competitionId") == comp)][:qtd]


def medias_de(jogos: list[dict], em_casa: bool) -> tuple[float, float, int] | None:
    pls = [placar(g) for g in jogos]
    pls = [p for p in pls if p]
    if not pls:
        return None
    gf = sum(p[0] if em_casa else p[1] for p in pls) / len(pls)
    ga = sum(p[1] if em_casa else p[0] for p in pls) / len(pls)
    return gf, ga, len(pls)


def nivel_base(competicao: str, times: list[str], palavras: list[str]) -> bool:
    """Liga de base/reserva/amadora pelo nome da liga; time reserva pelo fim do nome ("II", "B", "Res.", "Reserve").
    As palavras não valem no nome do time ("Balzan Youths" é profissional)."""
    comp = (competicao or "").lower()
    return (any(p.lower() in comp for p in palavras + ["Reserva"])
            or any(re.search(r"\s(II|B|Res\.?|Reserves?)$", t or "", re.I) for t in times))


def evento_sofascore(g: dict) -> dict:
    """Jogo do 365Scores no formato que o previsoes.resolver espera (só tempo normal)."""
    st = g.get("statusText") or ""
    tipos = {"Postponed": "postponed", "Cancelled": "canceled", "Abandoned": "abandoned", "Suspended": "suspended"}
    if st in tipos:
        return {"event": {"status": {"type": tipos[st]}}}
    if g.get("statusGroup") == FIM and st == "Ended" and placar(g):
        h, a = placar(g)
        return {"event": {"status": {"type": "finished"}, "homeScore": {"normaltime": h}, "awayScore": {"normaltime": a}}}
    return {}  # em andamento, prorrogação ou pênaltis: o 365Scores não dá o placar dos 90 min; resolva à mão


def hora_br(g: dict) -> str:
    return datetime.fromisoformat(g["startTime"]).astimezone(BRT).strftime("%H:%M")


def linha_de(k: dict) -> float | None:
    for campo in ("linha",):
        if k.get(campo) is not None:
            try:
                return float(k[campo])
            except (TypeError, ValueError):
                pass
    ch = k.get("chave")
    if isinstance(ch, (list, tuple)) and len(ch) > 1 and ch[1] is not None:
        try:
            return float(ch[1])
        except (TypeError, ValueError):
            pass
    m = re.search(r"(\d+[.,]5)", str(k.get("rotulo") or k.get("mercado") or ""))
    return float(m.group(1).replace(",", ".")) if m else None


def status_confere(p_sofa: float | None, p365: float | None, cauda_sofa: int | None, cauda365: int | None,
                   dif_min: int | None) -> tuple[str, list[str]]:
    motivos = []
    if p_sofa is not None and p365 is not None and abs(p_sofa - p365) > 0.10:
        motivos.append(f"prob. diverge: Sofascore {p_sofa:.0%} x 365Scores {p365:.0%}")
    if cauda_sofa is not None and cauda365 is not None and abs(cauda_sofa - cauda365) >= 2:
        motivos.append(f"cauda diverge: Sofascore {cauda_sofa} x 365Scores {cauda365} estouros")
    if dif_min is not None and dif_min > 30:
        motivos.append(f"horário diverge em {dif_min} min")
    return ("DIVERGENTE" if motivos else "CONFIRMADO"), motivos


# ---------------------------------------------------------------------------
# Análise de um jogo no 365Scores
# ---------------------------------------------------------------------------

def analisar(api: S365, g: dict, linhas: tuple[float, ...], cfg: dict) -> dict | None:
    vr = cfg["varredura"]
    comp, h, a = g.get("competitionId"), g["homeCompetitor"], g["awayCompetitor"]
    tc, tf = api.tabela(comp, 2), api.tabela(comp, 3)
    liga = medias_liga(tc, tf)
    rh, ra = tc.get(h["id"]), tf.get(a["id"])
    if not liga or not rh or not ra or min(rh.get("gamePlayed", 0), ra.get("gamePlayed", 0)) < 3:
        return None
    th = (rh["for"] / rh["gamePlayed"], rh["against"] / rh["gamePlayed"], rh["gamePlayed"])
    ta = (ra["for"] / ra["gamePlayed"], ra["against"] / ra["gamePlayed"], ra["gamePlayed"])
    res_h, res_a = api.resultados(h["id"]), api.resultados(a["id"])
    ch, ca = condicao(res_h, h["id"], True, comp, 10), condicao(res_a, a["id"], False, comp, 10)
    rec_h, rec_a = medias_de(ch, True), medias_de(ca, False)
    k, sig = vr["encolhimento_jogos"], vr["incerteza_sigma"]
    lam_t = lambdas(th, ta, liga, k)
    lam_r = lambdas(rec_h, rec_a, liga, k) if rec_h and rec_a and min(rec_h[2], rec_a[2]) >= 3 else None
    of = lambda js: [sum(placar(x)) for x in js if not amistoso(x)][:7]  # noqa: E731
    tot_h, tot_a = of(res_h), of(res_a)
    tot_ch, tot_ca = [sum(placar(x)) for x in ch], [sum(placar(x)) for x in ca]
    hh = [sum(placar(x)) for x in api.h2h(g["id"])][:5]
    liga_nome = g.get("competitionDisplayName") or ""
    out = {"id_365": g["id"], "jogo": f"{h['name']} x {a['name']}",
           "competicao": f"{g['_pais']} · {liga_nome}" if g.get("_pais") else liga_nome,
           "hora": hora_br(g), "inicio": g["startTime"], "liga": [round(x, 3) for x in liga],
           "tabela": {"casa": [round(x, 2) for x in th[:2]] + [th[2]], "fora": [round(x, 2) for x in ta[:2]] + [ta[2]]},
           "recentes": {"casa": rec_h and [round(rec_h[0], 2), round(rec_h[1], 2), rec_h[2]],
                        "fora": rec_a and [round(rec_a[0], 2), round(rec_a[1], 2), rec_a[2]]},
           "lambdas": {"tabela": [round(x, 3) for x in lam_t], "recentes": lam_r and [round(x, 3) for x in lam_r]},
           "totais": {"casa_7": tot_h, "fora_7": tot_a, "casa_cond": tot_ch, "fora_cond": tot_ca, "h2h_5": hh},
           "linhas": {}}
    for linha in linhas:
        ps = [p_under(*lam_t, linha, sig)] + ([p_under(*lam_r, linha, sig)] if lam_r else [])
        p = min(ps)
        cauda = {"casa": {"acima": acima(tot_h, linha), "n": len(tot_h)}, "fora": {"acima": acima(tot_a, linha), "n": len(tot_a)}}
        cond = {"casa": {"acima": acima(tot_ch, linha), "n": len(tot_ch)}, "fora": {"acima": acima(tot_ca, linha), "n": len(tot_ca)}}
        fr = lambda c: c["acima"] / c["n"] if c["n"] else None  # noqa: E731
        out["linhas"][str(linha)] = {
            "p": round(p, 4), "p_tabela": round(ps[0], 4), "p_recentes": round(ps[1], 4) if lam_r else None,
            "cauda": cauda, "cauda_cond": cond, "h2h": {"acima": acima(hh, linha), "n": len(hh)},
            "estoura": un.estoura_cauda([fr(cauda["casa"]), fr(cauda["fora"]), fr(cond["casa"]), fr(cond["fora"])], p,
                                        cfg["under"]["cauda_folga"])}
    return out


def config() -> dict:
    cfg = n.carregar_config()
    cfg["varredura"] = {**v.VARREDURA_PADRAO, **{k: x for k, x in cfg.get("varredura", {}).items() if not k.startswith("_")}}
    cfg["under"] = {**un.UNDER_PADRAO, **{k: x for k, x in cfg.get("under", {}).items() if not k.startswith("_")}}
    return cfg


# ---------------------------------------------------------------------------
# confere e mapa
# ---------------------------------------------------------------------------

def achar(jogos: list[dict], jogo: str, hora: str | None) -> dict | None:
    casa, _, fora = (jogo or "").partition(" x ")
    cand = [g for g in jogos if mesmo_time(casa, g["homeCompetitor"]["name"]) and mesmo_time(fora, g["awayCompetitor"]["name"])]
    if len(cand) > 1 and hora:
        cand.sort(key=lambda g: abs(minutos(hora_br(g)) - minutos(hora)))
    return cand[0] if cand else None


def minutos(hhmm: str) -> int:
    hh, mm = hhmm.split(":")
    return int(hh) * 60 + int(mm)


def cmd_confere(a: argparse.Namespace, cfg: dict) -> dict:
    arq = SOFA / f"peneira-{a.data}-under.json"
    if not arq.exists():
        sys.exit(f"Sem {arq.name}: rode antes o under.py (ou use o modo mapa se o Sofascore estiver fora).")
    pen = json.loads(arq.read_text(encoding="utf-8"))
    api = S365(a.data)
    jogos = api.jogos()
    itens = []
    for k in pen.get("candidatos", []) + pen.get("sem_valor", []):
        linha = linha_de(k)
        g = achar(jogos, k.get("jogo"), k.get("hora"))
        base = {"id_sofascore": k.get("id"), "jogo": k.get("jogo"), "hora": k.get("hora"), "linha": linha,
                "p_sofascore": k.get("p_min") or k.get("p")}
        if not g or linha is None:
            itens.append({**base, "status": "NAO_ACHADO", "motivos": ["jogo não achado no 365Scores"]})
            continue
        r = analisar(api, g, (linha,), cfg)
        if not r:
            itens.append({**base, "id_365": g["id"], "status": "NAO_ACHADO", "motivos": ["365Scores sem tabela casa/fora"]})
            continue
        lin = r["linhas"][str(linha)]
        cs = (k.get("under") or {}).get("cauda") or {}
        cauda_sofa = sum((cs.get(l) or {}).get("acima", 0) for l in ("casa", "fora")) if cs else None
        cauda365 = lin["cauda"]["casa"]["acima"] + lin["cauda"]["fora"]["acima"]
        dif = abs(minutos(r["hora"]) - minutos(k["hora"])) if k.get("hora") else None
        st, motivos = status_confere(base["p_sofascore"], lin["p"], cauda_sofa, cauda365, dif)
        local = (api.detalhe(g["id"]).get("venue") or {}).get("name")
        itens.append({**base, "id_365": g["id"], "status": st, "motivos": motivos, "p_365": lin["p"],
                      "cauda_sofascore": cauda_sofa, "cauda_365": cauda365, "cauda_cond_365": lin["cauda_cond"],
                      "h2h_365": lin["h2h"], "hora_365": r["hora"], "local_365": local, "medias_365": r["tabela"],
                      "liga_365": r["liga"], "totais_365": r["totais"]})
    saida = {"data": a.data, "fonte": "365Scores", "consultado": datetime.now(BRT).strftime("%H:%M"),
             "falhas": api.falhas, "itens": itens}
    (SOFA / f"confere-{a.data}.json").write_text(json.dumps(saida, ensure_ascii=False), encoding="utf-8")
    return saida


def cmd_mapa(a: argparse.Namespace, cfg: dict) -> dict:
    api = S365(a.data)
    agora = datetime.now(BRT)
    palavras = {**df.DEFESA_PADRAO, **cfg.get("defesa", {})}["palavras_base"]
    maximo = cfg["under"].get("queda_1x2_max", QUEDA_1X2_MAX)
    cands, vistos = [], 0
    for g in api.jogos():
        if g.get("statusGroup") != AGENDADO or not g.get("hasStandings"):
            continue
        if datetime.fromisoformat(g["startTime"]).astimezone(BRT) < agora + timedelta(minutes=20):
            continue
        vistos += 1
        r = analisar(api, g, LINHAS, cfg)
        if not r:
            continue
        passam = [(float(l), x) for l, x in r["linhas"].items() if x["p"] >= a.prob_min and not x["estoura"]]
        if not passam:
            continue
        linha, x = min(passam, key=lambda t: t[0])  # a menor linha que passa: mais odd com a mesma régua
        base = nivel_base(r["competicao"], r["jogo"].split(" x "), palavras)
        mov = queda_1x2(g.get("odds"))
        corte = corta_1x2(mov, maximo)
        cands.append({
            "id": r["id_365"], "jogo": r["jogo"], "competicao": r["competicao"], "hora": r["hora"],
            "mercado": f"Menos de {linha} gols", "chave": ["Match goals", str(linha), "Under"],
            "status": "caiu" if corte else "vivo", **({"motivo_queda": corte} if corte else {}), "mov_1x2": mov,
            "nivel": "base" if base else "pro", "p_modelo": x["p"], "prob_mercado_sem_margem": None, "odd_agora": None,
            "gols_esperados": r["lambdas"]["tabela"],
            "under": {"cauda": x["cauda"], "cauda_cond": x["cauda_cond"], "h2h": x["h2h"], "fonte": "365Scores"},
            "confere": {"status": "SO_365", "p_365": x["p"], "totais_365": r["totais"], "medias_365": r["tabela"], "liga_365": r["liga"]},
        })
    cands.sort(key=lambda c: (c["status"] != "vivo", c["nivel"] == "base", -c["p_modelo"]))
    for i, c in enumerate(cands, 1):
        c["n"] = i
    return {"data": a.data, "consultado": agora.strftime("%H:%M"), "fonte": "365Scores", "jogos_vistos": vistos,
            "falhas": api.falhas, "criterios": {**cfg["criterios"], "prob_minima": a.prob_min},
            "under": {"max_pesquisa": cfg["under"].get("max_pesquisa", 5)}, "aprofundar": {"modelo_agentes": None},
            "candidatos": cands}


def cmd_recheca(a: argparse.Namespace, cfg: dict) -> dict:
    """1X2 de agora (sem cache) dos unders do dossiê ou das previsões pendentes da data → OK ou CORTA (lição 67)."""
    maximo = cfg["under"].get("queda_1x2_max", QUEDA_1X2_MAX)
    if a.dossie:
        dos = json.loads(Path(a.dossie).read_text(encoding="utf-8"))
        alvos = [{"id_365": c.get("id_365") or (c.get("confere") or {}).get("id_365") or c.get("id"), "jogo": c.get("jogo"),
                  "hora": c.get("hora")} for c in dos.get("candidatos", []) if c.get("status", "vivo") == "vivo"]
        a.data = dos.get("data") or a.data
    else:
        import previsoes as pv
        alvos = [{"id_365": int(x["evento"][4:]) if str(x["evento"]).startswith("365-") else None, "jogo": x["jogo"],
                  "hora": x["hora"]} for x in pv.ler() if x["status"] == "pendente" and x["data"] == a.data
                 and x["mercado"].startswith("under")]
    jogos = S365(a.data, pasta=None).jogos()
    por_id = {g["id"]: g for g in jogos}
    itens = []
    for x in alvos:
        g = por_id.get(x["id_365"]) or achar(jogos, x["jogo"], x["hora"])
        if not g:
            itens.append({**x, "status": "NAO_ACHADO", "motivo": "jogo não achado no 365Scores"})
            continue
        if g.get("statusGroup") != AGENDADO:  # com bola rolando a odd é ao vivo: não serve para a régua
            itens.append({**x, "id_365": g["id"], "status": "COMECOU", "motivo": "jogo já começou", "mov_1x2": None})
            continue
        mov = queda_1x2(g.get("odds"))
        corte = corta_1x2(mov, maximo)
        itens.append({**x, "id_365": g["id"], "status": "CORTA" if corte else ("OK" if mov else "SEM_ODD"),
                      "motivo": corte or "", "mov_1x2": mov})
    return {"data": a.data, "consultado": datetime.now(BRT).strftime("%H:%M"), "queda_max": maximo, "itens": itens}


def cmd_anexa(a: argparse.Namespace) -> dict:
    """Põe o bloco `confere` de confere-<D>.json em cada candidato do dossiê (pelo id do Sofascore)."""
    arq = Path(a.dossie)
    dos = json.loads(arq.read_text(encoding="utf-8"))
    conf = SOFA / f"confere-{dos.get('data') or a.data}.json"
    itens = {x["id_sofascore"]: x for x in json.loads(conf.read_text(encoding="utf-8"))["itens"]} if conf.exists() else {}
    for c in dos.get("candidatos", []):
        if c.get("id") in itens:
            c["confere"] = itens[c["id"]]
    arq.write_text(json.dumps(dos, ensure_ascii=False), encoding="utf-8")
    return {"anexados": sum(1 for c in dos.get("candidatos", []) if c.get("confere")), "candidatos": len(dos.get("candidatos", []))}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("modo", choices=["confere", "mapa", "anexa", "recheca"])
    p.add_argument("--dossie", help="anexa: dossiê (JSON) que recebe o bloco confere; recheca: dossiê a reconferir")
    p.add_argument("--data", default=datetime.now(BRT).strftime("%Y-%m-%d"))
    p.add_argument("--prob-min", type=float, default=0.70)
    p.add_argument("--json", action="store_true")
    a = p.parse_args()
    if a.modo == "anexa":
        if not a.dossie:
            sys.exit("anexa precisa de --dossie <arquivo>")
        r = cmd_anexa(a)
        print(f"conferência anexada em {r['anexados']} de {r['candidatos']} candidatos")
        return
    cfg = config()
    if a.modo == "recheca":
        saida = cmd_recheca(a, cfg)
        if a.json:
            print(json.dumps(saida, ensure_ascii=False, indent=1))
            return
        print(f"🔁 1X2 de agora no 365Scores {saida['data']} ({saida['consultado']}) — corte com queda de "
              f"{saida['queda_max']:.0%} ou mais (lição 67)")
        for x in saida["itens"]:
            m = x.get("mov_1x2")
            mov = (f" · {m['lado']} {m['de']} → {m['para']} ("
                   + (f"caiu {m['queda']:.0%}" if m["queda"] > 0 else "não caiu") + ")") if m else ""
            print(f"- {x.get('hora') or '?'} {x['jogo']} · {x['status']}{mov}")
        return
    saida = cmd_confere(a, cfg) if a.modo == "confere" else cmd_mapa(a, cfg)
    if a.json:
        print(json.dumps(saida, ensure_ascii=False, indent=1))
        return
    if a.modo == "confere":
        print(f"🔎 Conferência no 365Scores {a.data} ({saida['consultado']}) — {len(saida['itens'])} under(s)")
        for x in saida["itens"]:
            extra = f" · Sofascore {x['p_sofascore']:.0%} x 365 {x['p_365']:.0%}" if x.get("p_365") is not None and x.get("p_sofascore") else ""
            print(f"- {x['hora']} {x['jogo']} · menos de {x['linha']} · {x['status']}{extra}"
                  + (f" — {'; '.join(x['motivos'])}" if x["motivos"] else ""))
    else:
        vivos = [c for c in saida["candidatos"] if c["status"] == "vivo"]
        print(f"🗺️ Mapa de under pelo 365Scores {a.data} ({saida['consultado']}) — {saida['jogos_vistos']} jogos vistos, "
              f"{len(vivos)} com {a.prob_min:.0%}+ e cauda limpa")
        for c in saida["candidatos"]:
            if c["status"] != "vivo":
                print(f"✂️ {c['hora']} {c['jogo']} · {c['mercado']} — {c['motivo_queda']}")
                continue
            u = c["under"]
            print(f"{c['n']}) {c['hora']} {c['jogo']} [{c['competicao']}{' · base' if c['nivel'] == 'base' else ''}] · "
                  f"{c['mercado']} · {c['p_modelo']:.0%} · cauda {u['cauda']['casa']['acima']}/{u['cauda']['casa']['n']} e "
                  f"{u['cauda']['fora']['acima']}/{u['cauda']['fora']['n']} · H2H {u['h2h']['acima']}/{u['h2h']['n']}")
    if saida.get("falhas"):
        print(f"⚠️ {saida['falhas']} consultas ao 365Scores falharam — rode de novo (o cache acelera).")


if __name__ == "__main__":
    main()
