#!/usr/bin/env python3
"""Peneira do dia: varre os jogos no Sofascore e devolve só os mercados com valor.

Para cada jogo das competições de `config.json → varredura.torneios_sofascore`:
estatísticas dos últimos jogos de cada time (mesma liga, mandante em casa /
visitante fora), modelos do `nucleo.py`, comparação com TODAS as odds
disponíveis (bet365 via Sofascore) e testes de robustez. Só sobra o que tem
prob ≥ `varredura.prob_triagem` E EV ≥ `criterios.ev_minimo` em todas as
variantes, sem divergência grande com o mercado (regra 8) e sem chuva.

É barata de propósito (só Python, sem pesquisa de notícias): o resultado é a
lista de candidatos para o /aprofundar, não o veredito final.

Exemplos:
  python3 ferramentas/varredura.py                    # hoje
  python3 ferramentas/varredura.py --data 2026-10-12
  python3 ferramentas/varredura.py --torneios 325,390  # só Série A e B
  python3 ferramentas/varredura.py --curto            # resumo de celular (rotina diária)
  python3 ferramentas/varredura.py --jogos 16421054    # reavalia só esses jogos (/aprofundar)
  python3 ferramentas/varredura.py --json > /tmp/peneira.json

O resultado completo fica salvo em dados/cache/sofascore/peneira-AAAA-MM-DD.json.

Odds: bet365 via Sofascore — NÃO são odds da Betano. Use a odd mínima de cada
candidato para conferir no app.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import math
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

import nucleo as n

FUSO_BR = timezone(timedelta(hours=-3))
API = "https://api.sofascore.com/api/v1/"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
CACHE_PADRAO = n.RAIZ / "dados" / "cache" / "sofascore"
PARTE_1T = 0.45  # fração dos gols que sai no 1º tempo

VARREDURA_PADRAO = {
    "prob_triagem": 0.59,
    "odd_minima_mercado": 1.20,
    "jogos_amostra": 10,
    "amostra_minima": 5,
    "encolhimento_jogos": 4,
    "tolerancia_variantes": 0.03,
    "tolerancia_frequencia": 0.05,
    "regra8_pp": 0.10,
    "rho_variante": -0.10,
    "incerteza_sigma": 0.15,
    "torneios_sofascore": {},
}


# ---------------------------------------------------------------------------
# Acesso ao Sofascore (com cache em disco)
# ---------------------------------------------------------------------------

def _baixar(caminho: str, tentativas: int = 3) -> dict | None:
    """JSON do endpoint; {} se não existe (404); None se a rede falhou."""
    req = urllib.request.Request(API + caminho, headers={
        "User-Agent": UA, "Accept": "application/json", "Referer": "https://www.sofascore.com/"})
    for i in range(tentativas):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {}
        except (urllib.error.URLError, TimeoutError, ValueError, OSError):
            pass
        time.sleep(1 + 2 * i)
    return None


class Sofascore:
    """`cache`: "fixo" (não muda: estatística de jogo encerrado), "dia" (vale no
    dia da varredura) ou None (sempre baixa: odds)."""

    def __init__(self, pasta: Path | None, data: str):
        self.pasta, self.data, self.falhas = pasta, data, 0

    def get(self, caminho: str, cache: str | None = "dia") -> dict:
        arq = None
        if self.pasta and cache:
            nome = re.sub(r"[^A-Za-z0-9_.-]", "_", caminho) + ".json"
            arq = self.pasta / ("fixo" if cache == "fixo" else self.data) / nome
            if arq.exists():
                try:
                    return json.loads(arq.read_text(encoding="utf-8"))
                except ValueError:
                    pass
        dados = _baixar(caminho)
        if dados is None:
            self.falhas += 1
            return {}
        if arq:
            arq.parent.mkdir(parents=True, exist_ok=True)
            arq.write_text(json.dumps(dados), encoding="utf-8")
        return dados


def em_paralelo(fn, itens, trabalhadores: int = 8) -> list:
    with cf.ThreadPoolExecutor(trabalhadores) as ex:
        return list(ex.map(fn, itens))


# ---------------------------------------------------------------------------
# Jogos, amostras e estatísticas
# ---------------------------------------------------------------------------

def hora_br(ts: int) -> datetime:
    return datetime.fromtimestamp(ts, FUSO_BR)


def torneio_id(evento: dict) -> int | None:
    return ((evento.get("tournament") or {}).get("uniqueTournament") or {}).get("id")


def listar_jogos(api: Sofascore, data: str, torneios: set[int]) -> list[dict]:
    cats = api.get(f"sport/football/{data}/-10800/categories").get("categories", [])
    alvo = [c["category"]["id"] for c in cats if torneios & set(c.get("uniqueTournamentIds") or [])]
    vistos, jogos = set(), []
    agora = time.time()
    # calendário sempre na hora: o status (não começou / em andamento) muda ao longo do dia
    for res in em_paralelo(lambda cid: api.get(f"category/{cid}/scheduled-events/{data}", cache=None), alvo):
        for e in res.get("events", []):
            if e["id"] in vistos or torneio_id(e) not in torneios:
                continue
            vistos.add(e["id"])
            if (hora_br(e["startTimestamp"]).date().isoformat() == data and e["status"]["type"] == "notstarted"
                    and e["startTimestamp"] > agora):
                jogos.append(e)
    return sorted(jogos, key=lambda e: e["startTimestamp"])


def placar(e: dict, lado: str, campo: str = "normaltime"):
    s = e.get(f"{lado}Score") or {}
    return s.get(campo, s.get("current")) if campo == "normaltime" else s.get(campo)


CHAVES_ESTAT = {"expectedGoals": "xg", "totalShotsOnGoal": "chutes", "shotsOnGoal": "sot",
                "cornerKicks": "esc", "yellowCards": "am", "redCards": "vm",
                "goalkeeperSaves": "def", "fouls": "faltas"}


def _num(v) -> float | None:
    if v is None:
        return None
    try:
        return float(str(v).replace("%", "").split(" ")[0].split("/")[0])
    except ValueError:
        return None


def ler_estatisticas(d: dict) -> dict[str, tuple]:
    """{'xg': (casa, fora), ...} do período ALL; {} se não houver."""
    for per in d.get("statistics", []):
        if per.get("period") != "ALL":
            continue
        out = {}
        for g in per.get("groups", []):
            for it in g.get("statisticsItems", []):
                nome = CHAVES_ESTAT.get(it.get("key"))
                if nome and nome not in out:
                    out[nome] = (_num(it.get("homeValue", it.get("home"))),
                                 _num(it.get("awayValue", it.get("away"))))
        return out
    return {}


def linha_do_time(e: dict, estat: dict, tid: int) -> dict | None:
    """Números do jogo `e` do ponto de vista do time `tid` (a favor / contra)."""
    hs, as_ = placar(e, "home"), placar(e, "away")
    if hs is None or as_ is None:
        return None
    casa = e["homeTeam"]["id"] == tid
    r = {"t": e["startTimestamp"], "gf": hs if casa else as_, "ga": as_ if casa else hs,
         "adv": (e["awayTeam"] if casa else e["homeTeam"])["name"]}
    for nome in CHAVES_ESTAT.values():
        par = estat.get(nome)
        if par and par[0] is not None and par[1] is not None:
            r[nome + "_f"], r[nome + "_a"] = (par if casa else (par[1], par[0]))
    if "am_f" in r:
        r["cart_f"] = r["am_f"] + r.get("vm_f", 0)
        r["cart_a"] = r["am_a"] + r.get("vm_a", 0)
    return r


def media(xs: list[dict], k: str) -> tuple[float | None, int]:
    v = [x[k] for x in xs if x.get(k) is not None]
    return (sum(v) / len(v), len(v)) if v else (None, 0)


# ---------------------------------------------------------------------------
# Modelos
# ---------------------------------------------------------------------------

def ataque_defesa(xs: list[dict], modo: str = "mix") -> tuple[float, float, int] | None:
    """(marcados, sofridos, n). mix = 50% gols + 50% xG quando há xG em ≥ 70% dos jogos."""
    gf, ng = media(xs, "gf")
    ga, _ = media(xs, "ga")
    xf, nx = media(xs, "xg_f")
    xa, _ = media(xs, "xg_a")
    if not ng:
        return None
    tem_xg = xf is not None and xa is not None and nx / ng >= 0.7
    if modo == "xg":
        return (xf, xa, ng) if tem_xg else None
    if modo == "gols" or not tem_xg:
        return gf, ga, ng
    return 0.5 * gf + 0.5 * xf, 0.5 * ga + 0.5 * xa, ng


def gols_esperados(xh: list[dict], xa: list[dict], liga: tuple[float, float], k: float,
                   modo: str = "mix", geral: bool = False) -> tuple[float, float] | None:
    """λ mandante e visitante pelo método de força do nucleo, com encolhimento
    para a média da liga (peso de `k` jogos). `geral`: amostras casa+fora,
    reescaladas para a condição pela relação mandante/visitante da liga."""
    ah, aa = ataque_defesa(xh, modo), ataque_defesa(xa, modo)
    if not ah or not aa:
        return None
    lh, la = liga
    hf, hc, nh = ah
    af, ac, na = aa
    if geral:
        lm = (lh + la) / 2
        hf, hc, af, ac = hf * lh / lm, hc * la / lm, af * la / lm, ac * lh / lm
    enc = lambda v, qtd, alvo: (qtd * v + k * alvo) / (qtd + k)  # noqa: E731
    return n.lambdas_por_medias(enc(hf, nh, lh), enc(hc, nh, la), enc(af, na, la), enc(ac, na, lh), lh, la)


def dispersao(grupos: list[list[float]]) -> float:
    """Variância/média combinada (desvios em torno da média de cada grupo); mínimo 1."""
    num = den = tot = cnt = 0.0
    for g in grupos:
        g = [v for v in g if v is not None]
        if len(g) < 3:
            continue
        m = sum(g) / len(g)
        num += sum((v - m) ** 2 for v in g)
        den += len(g) - 1
        tot += sum(g)
        cnt += len(g)
    if not den or not tot:
        return 1.0
    return max(1.0, (num / den) / (tot / cnt))


def contagem(xh: list[dict], xa: list[dict], chave: str, minimo: int) -> dict | None:
    cf_, n1 = media(xh, chave + "_f")
    cc, _ = media(xh, chave + "_a")
    ff, n2 = media(xa, chave + "_f")
    fc, _ = media(xa, chave + "_a")
    if None in (cf_, cc, ff, fc) or min(n1, n2) < minimo:
        return None
    tot, mh, ma = n.media_confronto(cf_, cc, ff, fc)
    totais = [[x[chave + "_f"] + x[chave + "_a"] for x in xs if x.get(chave + "_f") is not None]
              for xs in (xh, xa)]
    return {"media": tot, "casa": mh, "fora": ma, "disp": dispersao(totais), "n": min(n1, n2)}


def _nos_lognormal(sigma: float) -> list[tuple[float, float]]:
    """Gauss-Hermite (5 nós) para um fator log-normal de média 1."""
    gh = [(-2.0201828704560856, 0.019953242059045913), (-0.9585724646138185, 0.39361932315223),
          (0.0, 0.9453087204829419), (0.9585724646138185, 0.39361932315223),
          (2.0201828704560856, 0.019953242059045913)]
    tot = sum(w for _, w in gh)
    return [(math.exp(sigma * math.sqrt(2) * x - sigma * sigma / 2), w / tot) for x, w in gh]


def matriz(lc: float, lf: float, rho: float = 0.0, sigma: float = 0.0) -> list[list[float]]:
    """Matriz de placares; com `sigma`, mistura a incerteza das médias (fator
    comum ao jogo + fator de cada time), o que alarga as caudas."""
    if not sigma:
        return n.matriz_placar(lc, lf, rho)
    acc = None
    for c, wc in _nos_lognormal(sigma):
        for a, wa in _nos_lognormal(sigma):
            for b, wb in _nos_lognormal(sigma):
                m = n.matriz_placar(lc * c * a, lf * c * b, rho)
                w = wc * wa * wb
                if acc is None:
                    acc = [[v * w for v in linha] for linha in m]
                else:
                    for i, linha in enumerate(m):
                        for j, v in enumerate(linha):
                            acc[i][j] += v * w
    return acc


def resultado(m: list[list[float]]) -> dict[str, float]:
    k = len(m)
    p1 = sum(m[i][j] for i in range(k) for j in range(k) if i > j)
    px = sum(m[i][i] for i in range(k))
    an = sum(m[0][j] for j in range(k)) + sum(m[i][0] for i in range(k)) - m[0][0]
    return {"1": p1, "X": px, "2": 1 - p1 - px, "1X": p1 + px, "X2": 1 - p1, "12": 1 - px,
            "ambas_sim": 1 - an, "ambas_nao": an}


def total_gols(m: list[list[float]], linha: float, lado: str) -> tuple[float, float]:
    """(vitória, devolução) de over/under `linha` na matriz."""
    k = len(m)
    acima = sum(m[i][j] for i in range(k) for j in range(k) if i + j > linha + 1e-9)
    igual = sum(m[i][j] for i in range(k) for j in range(k) if abs(i + j - linha) < 1e-9)
    abaixo = 1 - acima - igual
    return (acima, igual) if lado == "over" else (abaixo, igual)


def handicap_asiatico(m: list[list[float]], h: float, lado: str) -> tuple[float, float]:
    """(vitória, devolução) com handicap `h` para 'casa' ou 'fora'. Quartos de
    linha (±0.25, ±0.75) viram meia aposta em cada linha vizinha."""
    partes = [h] if abs(h * 2 - round(h * 2)) < 1e-9 else [h - 0.25, h + 0.25]
    vit = dev = 0.0
    k = len(m)
    for hh in partes:
        for i in range(k):
            for j in range(k):
                x = (i - j if lado == "casa" else j - i) + hh
                if x > 1e-9:
                    vit += m[i][j] / len(partes)
                elif abs(x) < 1e-9:
                    dev += m[i][j] / len(partes)
    return vit, dev


def linha_contagem(media_: float, linha: float, lado: str, disp: float, sigma: float = 0.0) -> tuple[float, float]:
    if not sigma:
        r = n.prob_linha(media_, linha, lado, disp)
        return r["vitoria"], r["devolucao"]
    v = d = 0.0
    for f, w in _nos_lognormal(sigma):
        r = n.prob_linha(media_ * f, linha, lado, disp)
        v += r["vitoria"] * w
        d += r["devolucao"] * w
    return v, d


# ---------------------------------------------------------------------------
# Odds e avaliação de mercados
# ---------------------------------------------------------------------------

def odd_decimal(fracao: str) -> float:
    a, _, b = fracao.partition("/")
    return 1 + float(a) / float(b)


def sem_margem(nome: str, odds: list[float]) -> list[float]:
    """Probabilidade justa de cada escolha. Na dupla chance as 3 escolhas se
    sobrepõem (somam 2), então o proporcional é multiplicado por 2."""
    probs, _ = n.remover_margem(odds)
    return [2 * p for p in probs] if nome == "Double chance" else probs


def rotulo(nome: str, grupo: str | None, escolha: str, casa: str, fora: str) -> str:
    lado = {"1": casa, "X": "empate", "2": fora}
    if nome == "Full time":
        return f"Resultado: {lado[escolha]}"
    if nome == "1st half":
        return f"1º tempo: {lado[escolha]}"
    if nome == "Double chance":
        return f"Dupla chance {escolha}"
    if nome == "Draw no bet":
        return f"Empate anula: {lado[escolha]}"
    if nome == "Both teams to score":
        return "Ambas marcam: " + ("sim" if escolha == "Yes" else "não")
    if nome == "Asian handicap":
        h, _, time_ = escolha.partition(")")
        return f"Handicap asiático {time_.strip()} {h.strip('(')}"
    if nome == "First team to score":
        return "Primeiro a marcar: " + ("ninguém" if escolha == "No goal" else escolha)
    unid = {"Match goals": "gols", "Cards in match": "cartões", "Corners 2-Way": "escanteios"}.get(nome, nome)
    return f"{'Mais' if escolha == 'Over' else 'Menos'} de {grupo} {unid}"


def avaliar(odds: dict, lam: tuple[float, float] | None, cont: dict, casa: str, fora: str,
            rho: float = 0.0, sigma: float = 0.0, ev_min: float = 0.03) -> dict[tuple, dict]:
    """Probabilidade do modelo para cada escolha com odd. Chave: (mercado, linha, escolha)."""
    out: dict[tuple, dict] = {}
    if lam:
        m = matriz(lam[0], lam[1], rho, sigma)
        r = resultado(m)
        r1t = resultado(matriz(lam[0] * PARTE_1T, lam[1] * PARTE_1T, rho, sigma))
    for mk in odds.get("markets", []):
        nome, grupo = mk.get("marketName"), mk.get("choiceGroup")
        try:
            esc = [(c["name"], odd_decimal(c["fractionalValue"])) for c in mk["choices"]]
        except (KeyError, ValueError, ZeroDivisionError):
            continue
        if not esc or any(o <= 1.0 for _, o in esc):
            continue
        justas = sem_margem(nome, [o for _, o in esc])
        for idx, ((escolha, odd), justa) in enumerate(zip(esc, justas)):
            p = dev = None
            if lam and nome in ("Full time", "Double chance"):
                p = r.get(escolha)
            elif lam and nome == "1st half":
                p = r1t.get(escolha)
            elif lam and nome == "Draw no bet":
                p, dev = (r["1"] if escolha == "1" else r["2"]), r["X"]
            elif lam and nome == "Both teams to score":
                p = r["ambas_sim"] if escolha == "Yes" else r["ambas_nao"]
            elif lam and nome == "Match goals" and grupo:
                p, dev = total_gols(m, float(grupo), escolha.lower())
            elif lam and nome == "Asian handicap":
                try:
                    h = float(escolha.split(")")[0].strip("("))
                except ValueError:
                    continue
                p, dev = handicap_asiatico(m, h, "casa" if idx == 0 else "fora")
            elif lam and nome == "First team to score":
                sem_gol = m[0][0]
                tot = lam[0] + lam[1]
                p = sem_gol if escolha == "No goal" else (1 - sem_gol) * (lam[0] if idx == 0 else lam[1]) / tot
            elif nome in ("Cards in match", "Corners 2-Way") and grupo:
                c = cont.get("cartoes" if nome == "Cards in match" else "escanteios")
                if c:
                    p, dev = linha_contagem(c["media"], float(grupo), escolha.lower(), c["disp"], sigma)
            if p is None:
                continue
            dev = dev or 0.0
            out[(nome, grupo, escolha)] = {
                "mercado": nome, "linha": grupo, "escolha": escolha, "idx": idx,
                "rotulo": rotulo(nome, grupo, escolha, casa, fora), "odd": round(odd, 3),
                "p": p, "dev": dev, "ev": n.ev(p, odd, dev), "justa_mercado": justa,
                "odd_justa": n.odd_justa(p, dev), "odd_minima": n.odd_minima(p, ev_min, dev)}
    return out


def frequencia(item: dict, xh: list[dict], xa: list[dict]) -> float | None:
    """Com que frequência o evento aconteceu nas duas amostras (mandante em
    casa + visitante fora). None quando o mercado não tem leitura direta."""
    nome, escolha = item["mercado"], item["escolha"]
    try:
        linha = float(item["linha"]) if item["linha"] else None
    except ValueError:
        linha = None
    chave = {"Match goals": ("gf", "ga"), "Cards in match": ("cart_f", "cart_a"),
             "Corners 2-Way": ("esc_f", "esc_a")}.get(nome)
    vals: list[bool] = []
    if chave and linha is not None and abs(linha - math.floor(linha) - 0.5) < 1e-9:
        for x in xh + xa:
            if x.get(chave[0]) is not None and x.get(chave[1]) is not None:
                tot = x[chave[0]] + x[chave[1]]
                vals.append(tot > linha if escolha == "Over" else tot < linha)
    elif nome == "Both teams to score":
        vals = [(x["gf"] > 0 and x["ga"] > 0) == (escolha == "Yes") for x in xh + xa]
    elif nome in ("Full time", "Double chance"):
        # resultado do ponto de vista do mandante: casa = jogos dele em casa;
        # fora = jogos do visitante fora, invertidos
        res = ["1" if x["gf"] > x["ga"] else "X" if x["gf"] == x["ga"] else "2" for x in xh]
        res += ["2" if x["gf"] > x["ga"] else "X" if x["gf"] == x["ga"] else "1" for x in xa]
        vals = [r in escolha for r in res]
    if not vals:
        return None
    return sum(vals) / len(vals)


# ---------------------------------------------------------------------------
# Varredura de um jogo
# ---------------------------------------------------------------------------

def medias_liga(api: Sofascore, ut: int, temporada: int) -> tuple[float, float] | None:
    """Gols por jogo de mandantes e visitantes (temporada atual + anterior)."""
    ids = [s["id"] for s in api.get(f"unique-tournament/{ut}/seasons").get("seasons", [])]
    temporadas = [temporada] + ([ids[ids.index(temporada) + 1]] if temporada in ids and ids.index(temporada) + 1 < len(ids) else [])
    mh = gh = ma = ga = 0
    for s in temporadas:
        for tipo in ("home", "away"):
            for st in api.get(f"unique-tournament/{ut}/season/{s}/standings/{tipo}").get("standings", []):
                for row in st.get("rows", []):
                    if tipo == "home":
                        mh += row.get("matches", 0)
                        gh += row.get("scoresFor", 0)
                    else:
                        ma += row.get("matches", 0)
                        ga += row.get("scoresFor", 0)
    if mh < 30 or ma < 30:
        return None
    return gh / mh, ga / ma


def taxa_base(api: Sofascore, ut: int, temporada: int) -> dict | None:
    """Placares recentes da liga (temporada atual + fim da anterior): empates,
    ambas marcam e distribuição de gols, para conferir o modelo."""
    ids = [s["id"] for s in api.get(f"unique-tournament/{ut}/seasons").get("seasons", [])]
    anterior = ids[ids.index(temporada) + 1] if temporada in ids and ids.index(temporada) + 1 < len(ids) else None
    placares = []
    for s, paginas in ((temporada, 4), (anterior, 2)):
        if not s:
            continue
        for pg in range(paginas):
            d = api.get(f"unique-tournament/{ut}/season/{s}/events/last/{pg}")
            for e in d.get("events", []):
                hs, as_ = placar(e, "home"), placar(e, "away")
                if e["status"]["type"] == "finished" and hs is not None and as_ is not None:
                    placares.append((hs, as_))
            if not d.get("hasNextPage"):
                break
    if len(placares) < 40:
        return None
    qtd = len(placares)
    return {"n": qtd, "empates": sum(1 for a, b in placares if a == b) / qtd,
            "ambas": sum(1 for a, b in placares if a and b) / qtd,
            "totais": [a + b for a, b in placares]}


def ajuste_empate(item: dict, p_empate_modelo: float, empates_liga: float) -> tuple[float, float]:
    """(vitória, devolução) do mercado refeito com a taxa de empates da liga
    quando o modelo dá menos empates que ela (viés conhecido da Poisson)."""
    if empates_liga <= p_empate_modelo:
        return item["p"], item["dev"]
    fator = (1 - empates_liga) / (1 - p_empate_modelo)
    nome, esc = item["mercado"], item["escolha"]
    if nome == "Full time" and esc in ("1", "2"):
        return item["p"] * fator, 0.0
    if nome == "Double chance" and esc == "12":
        return 1 - empates_liga, 0.0
    if nome == "Draw no bet":
        return item["p"] * fator, empates_liga
    return item["p"], item["dev"]


def ultimos_eventos(api: Sofascore, tid: int) -> list[dict]:
    evs = []
    for pg in (0, 1):
        evs += api.get(f"team/{tid}/events/last/{pg}").get("events", [])
    return evs


def amostras_time(eventos: list[dict], tid: int, ut: int, em_casa: bool, qtd: int) -> tuple[list, list]:
    liga = sorted((e for e in eventos if torneio_id(e) == ut and e["status"]["type"] == "finished"),
                  key=lambda e: e["startTimestamp"])
    cond = [e for e in liga if (e["homeTeam"]["id"] == tid) == em_casa]
    return cond[-(qtd + 2):], liga[-qtd:]  # +2 para a variante "sem os 2 últimos"


def analisar_jogo(api: Sofascore, e: dict, cfg: dict, cache_liga: dict) -> dict:
    v = cfg["varredura"]
    ev_min = cfg["criterios"]["ev_minimo"]
    eid, ut = e["id"], torneio_id(e)
    casa, fora = e["homeTeam"]["name"], e["awayTeam"]["name"]
    info = {"id": eid, "hora": hora_br(e["startTimestamp"]).strftime("%H:%M"),
            "jogo": f"{casa} x {fora}", "competicao": e["tournament"]["uniqueTournament"]["name"],
            "casa": casa, "fora": fora, "candidatos": [], "motivo": None}
    odds = api.get(f"event/{eid}/odds/1/all", cache=None)
    if not odds.get("markets"):
        info["motivo"] = "sem odds"
        return info
    temporada = (e.get("season") or {}).get("id")
    if (ut, temporada) not in cache_liga:
        cache_liga[(ut, temporada)] = ((medias_liga(api, ut, temporada), taxa_base(api, ut, temporada))
                                       if temporada else (None, None))
    liga, base = cache_liga[(ut, temporada)]
    if not liga:
        info["motivo"] = "sem médias da liga"
        return info
    qtd, minimo = v["jogos_amostra"], v["amostra_minima"]
    th, ta = e["homeTeam"]["id"], e["awayTeam"]["id"]
    evh, eva = ultimos_eventos(api, th), ultimos_eventos(api, ta)
    ch, gh = amostras_time(evh, th, ut, True, qtd)
    ca, ga = amostras_time(eva, ta, ut, False, qtd)
    ids = sorted({x["id"] for x in ch + gh + ca + ga})
    baixadas = em_paralelo(lambda i: api.get(f"event/{i}/statistics", cache="fixo"), ids, 4)
    estat = {i: ler_estatisticas(d) for i, d in zip(ids, baixadas)}

    def linhas(eventos, tid, tirar=0):
        xs = [x for x in (linha_do_time(ev, estat.get(ev["id"], {}), tid) for ev in eventos) if x]
        xs = xs[:len(xs) - tirar] if tirar else xs
        return xs[-qtd:]

    xh, xa = linhas(ch, th), linhas(ca, ta)
    info["amostra"] = (len(xh), len(xa))
    if min(len(xh), len(xa)) < minimo:
        info["motivo"] = f"amostra curta ({len(xh)}/{len(xa)} jogos na condição)"
        return info

    det = api.get(f"event/{eid}", cache=None).get("event", {})
    arb = det.get("referee") or {}
    arb_media = ((arb.get("yellowCards", 0) + arb.get("redCards", 0)) / arb["games"]
                 if arb.get("games", 0) >= 15 else None)
    info["arbitro"] = arb.get("name")
    venue = det.get("venue") or {}
    info["local"] = {"estadio": venue.get("name"), "cidade": (venue.get("city") or {}).get("name"),
                     "pais": (venue.get("country") or {}).get("alpha2"),
                     "coord": venue.get("venueCoordinates")}

    def conts(a, b):
        out = {}
        for chave, nome in (("esc", "escanteios"), ("cart", "cartoes")):
            c = contagem(a, b, chave, minimo)
            if c:
                if nome == "cartoes" and arb_media is not None:
                    peso = cfg["modelos"]["peso_arbitro_cartoes"]
                    c["media"] = (1 - peso) * c["media"] + peso * arb_media
                out[nome] = c
        return out

    k, rho0, rho_v, sig = v["encolhimento_jogos"], cfg["modelos"]["rho_dixon_coles"], v["rho_variante"], v["incerteza_sigma"]
    lam = gols_esperados(xh, xa, liga, k)
    cont = conts(xh, xa)
    info["lambda"] = lam
    xh2, xa2 = linhas(ch, th, 2), linhas(ca, ta, 2)
    xgh, xga = linhas(gh, th), linhas(ga, ta)
    variantes = {
        "base": avaliar(odds, lam, cont, casa, fora, rho0, 0.0, ev_min),
        "incerteza": avaliar(odds, lam, cont, casa, fora, rho0, sig, ev_min),
        "dixon_coles": avaliar(odds, lam, cont, casa, fora, rho_v, 0.0, ev_min),
        "sem_2_ultimos": avaliar(odds, gols_esperados(xh2, xa2, liga, k), conts(xh2, xa2), casa, fora, rho0, 0.0, ev_min),
        "so_gols": avaliar(odds, gols_esperados(xh, xa, liga, k, "gols"), cont, casa, fora, rho0, 0.0, ev_min),
        "so_xg": avaliar(odds, gols_esperados(xh, xa, liga, k, "xg"), cont, casa, fora, rho0, 0.0, ev_min),
    }
    if min(len(xgh), len(xga)) >= minimo:
        variantes["amostra_geral"] = avaliar(odds, gols_esperados(xgh, xga, liga, k, geral=True),
                                             conts(xgh, xga), casa, fora, rho0, 0.0, ev_min)
    # o dossie.py usa as duas para explicar por que um candidato caiu
    info["variantes"], info["amostras"], info["taxa_base"] = variantes, (xh, xa), base
    info["candidatos"], info["descartes_mercado"] = filtrar(variantes, xh, xa, v, ev_min, base)
    if not info["candidatos"]:
        info["motivo"] = info["descartes_mercado"] or MOTIVOS[0]
    return info


MOTIVOS = {
    0: "sem desalinhamento (nenhum mercado com prob. e EV no corte)",
    1: "valor some com incerteza das médias / correção de empates",
    2: "não robusto (cai sem os 2 últimos jogos, na amostra geral, só gols ou só xG)",
    3: "regra 8: modelo > 10 p.p. acima do mercado (o mercado pode saber algo)",
    4: "frequência real nas amostras abaixo da triagem",
    5: "taxa-base da liga contradiz (empates subestimados ou cauda de gols)",
}


def confere_taxa_base(b: dict, dc: dict, base: dict, triagem: float, ev_min: float) -> bool:
    """Empates: refaz 1/2/12/DNB com a taxa real de empates da liga. Gols com
    prob. ≥ 80%: a liga precisa ter o evento em pelo menos (prob − 10 p.p.)."""
    empate_dc = next((x["p"] for k, x in dc.items() if k[0] == "Full time" and k[2] == "X"), None)
    if empate_dc is not None and b["mercado"] in ("Full time", "Double chance", "Draw no bet"):
        p, dev = ajuste_empate(b, empate_dc, base["empates"])
        if p < triagem or n.ev(p, b["odd"], dev) < ev_min:
            return False
    if b["mercado"] == "Match goals" and b["p"] >= 0.80 and b["linha"]:
        linha = float(b["linha"])
        freq = sum(1 for t in base["totais"] if (t > linha) == (b["escolha"] == "Over")) / len(base["totais"])
        if freq < b["p"] - 0.10:
            return False
    return True


def filtrar(variantes: dict[str, dict], xh: list[dict], xa: list[dict], v: dict, ev_min: float,
            base: dict | None = None) -> tuple[list[dict], str | None]:
    """Mercados que passam em tudo; e o motivo de descarte mais relevante do jogo."""
    triagem, tol = v["prob_triagem"], v["tolerancia_variantes"]
    obrig = ("base", "incerteza", "dixon_coles")
    candidatos, motivos = [], []  # (etapa, motivo): fica o da etapa mais avançada
    for chave, b in variantes["base"].items():
        if b["p"] < triagem or b["ev"] < ev_min or b["odd"] < v["odd_minima_mercado"]:
            continue
        if any(chave not in variantes[o] or variantes[o][chave]["p"] < triagem
               or variantes[o][chave]["ev"] < ev_min for o in obrig):
            motivos.append((1, MOTIVOS[1]))
            continue
        outras = {k: var[chave] for k, var in variantes.items() if k not in obrig and chave in var}
        fracas = [k for k, x in outras.items() if x["p"] < triagem - tol or x["ev"] < 0]
        if fracas:
            motivos.append((2, MOTIVOS[2]))
            continue
        p_cond = b["p"] / (1 - b["dev"]) if b["dev"] else b["p"]
        if p_cond - b["justa_mercado"] > v["regra8_pp"]:
            motivos.append((3, MOTIVOS[3]))
            continue
        freq = frequencia(b, xh, xa)
        if freq is not None and freq < triagem - v["tolerancia_frequencia"]:
            motivos.append((4, MOTIVOS[4]))
            continue
        if base and not confere_taxa_base(b, variantes["dixon_coles"], base, triagem, ev_min):
            motivos.append((5, MOTIVOS[5]))
            continue
        candidatos.append({**b, "frequencia": freq, "p_min": min(x["p"] for x in [b, *outras.values(),
                          *(variantes[o][chave] for o in obrig)]),
                           "variantes": {k: round(x["p"], 3) for k, x in outras.items()}})
    candidatos.sort(key=lambda c: (-c["p"], -c["ev"]))
    return candidatos, (max(motivos)[1] if motivos else None)


# ---------------------------------------------------------------------------
# Chuva (só para quem passou na peneira)
# ---------------------------------------------------------------------------

def checar_chuva(info: dict, data: str, cfg: dict) -> dict:
    import clima
    loc = info.get("local") or {}
    c = loc.get("coord") or {}
    try:
        if "latitude" in c and abs(c["latitude"]) <= 90 and abs(c["longitude"]) <= 180:
            lat, lon = c["latitude"], c["longitude"]
        elif loc.get("cidade"):
            g = clima.geocodificar(loc["cidade"], loc.get("pais") or "BR")
            lat, lon = g["lat"], g["lon"]
        else:
            return {"status": "não verificada", "detalhe": "estádio sem localização"}
        for tentativa in range(3):
            try:
                prev = clima.buscar_previsao(lat, lon, data)
                break
            except Exception:
                if tentativa == 2:
                    raise
                time.sleep(3 + 3 * tentativa)
        r = clima.avaliar_chuva(prev, datetime.fromisoformat(f"{data}T{info['hora']}"), cfg)
    except Exception as exc:  # rede, cidade não encontrada
        return {"status": "não verificada", "detalhe": str(exc)[:80]}
    d = r["dia"]
    return {"status": "CHUVA" if r["chuva"] else "seco",
            "detalhe": f"dia {d['prob_max']}% / {d['mm_total']} mm"}


# ---------------------------------------------------------------------------
# Saída
# ---------------------------------------------------------------------------

def imprimir(res: dict) -> None:
    c = res["contagem"]
    print(f"# Peneira {res['data']} — consultado {res['consultado']} (Brasília)\n")
    print(f"{c['jogos']} jogos nas competições da lista → {c['avaliados']} com dados e odds → "
          f"{c['com_candidato']} com mercado de valor → {len(res['candidatos'])} candidatos após a chuva.\n")
    if res["candidatos"]:
        print(f"## ⭐ Candidatos (prob ≥ {res['prob_triagem']:.0%} e EV ≥ {res['ev_minimo']:.0%} "
              "em todas as variantes) — confirmar com /aprofundar\n")
        linhas = []
        for i, k in enumerate(res["candidatos"], 1):
            freq = "—" if k["frequencia"] is None else f"{k['frequencia']:.0%}"
            linhas.append([str(i), k["hora"], k["jogo"], k["rotulo"], f"{k['odd']:.2f}", n.pct(k["p"]),
                           f"{k['p_min']:.0%}", n.pct(k["justa_mercado"]), n.fmt_odd(k["odd_minima"]),
                           f"{k['ev'] * 100:+.1f}%", freq, k["chuva"]])
        print(n.tabela(["#", "Hora", "Jogo", "Mercado", "Odd bet365", "Prob.", "Pior variante",
                        "Mercado s/ margem", "Odd mín.", "EV", "Freq. amostras", "Chuva"], linhas))
    else:
        print("## Nenhuma oportunidade de valor na peneira de hoje.\n\nNão force entrada.")
    print("\n## Fora da peneira")
    for motivo, qtd in sorted(res["descartes"].items(), key=lambda x: -x[1]):
        print(f"- {qtd} × {motivo}")
    if res["chuva_excluidos"]:
        print("- Excluídos por chuva: " + "; ".join(res["chuva_excluidos"]))
    if res["falhas_rede"]:
        print(f"\n⚠️ {res['falhas_rede']} consultas ao Sofascore falharam — a varredura pode estar incompleta.")
    print("\nOdds: bet365 via Sofascore, NÃO Betano — confira a odd mínima no app. "
          "Estimativas estatísticas: um pick de 60% perde 40% das vezes.")


CURTO_MOTIVO = {MOTIVOS[0]: "sem valor", MOTIVOS[1]: "somem na incerteza", MOTIVOS[2]: "não robustos",
                MOTIVOS[3]: "regra 8", MOTIVOS[4]: "frequência baixa", MOTIVOS[5]: "taxa-base contra",
                "amostra curta": "amostra curta", "sem odds": "sem odds", "sem médias da liga": "sem liga"}


def imprimir_curto(res: dict) -> None:
    """Resumo para celular. A última linha (NOTIFICAR:) é o texto da notificação."""
    c = res["contagem"]
    dia = "/".join(reversed(res["data"].split("-")[1:]))
    cands = res["candidatos"]
    print(f"⚽ Peneira {dia} ({res['consultado']}) — {c['jogos']} jogos, {len(cands)} com valor")
    for i, k in enumerate(cands, 1):
        chuva = "" if k["chuva"] == "seco" else " · ⚠️ chuva não verificada"
        print(f"{i}) {k['hora']} {k['jogo']} · {k['rotulo']} · {k['p']:.0%} · odd mín {n.fmt_odd(k['odd_minima'])}"
              f" · bet365 {k['odd']:.2f} (EV {k['ev'] * 100:+.0f}%){chuva}")
    fora = [f"{q} {CURTO_MOTIVO.get(m, m)}" for m, q in sorted(res["descartes"].items(), key=lambda x: -x[1])]
    if res["chuva_excluidos"]:
        fora.append(f"{len(res['chuva_excluidos'])} chuva")
    if fora:
        print("Fora: " + " · ".join(fora))
    if res["falhas_rede"]:
        print(f"⚠️ {res['falhas_rede']} consultas falharam — rode de novo.")
    if cands:
        print("Odds bet365, não Betano: entre só com odd ≥ mínima. Triagem — mande /aprofundar (todos ou os números).")
        itens = [f"{k['hora']} {k['jogo'].split(' x ')[0]} {k['rotulo'].replace('Menos de ', '-').replace('Mais de ', '+')} mín {n.fmt_odd(k['odd_minima'])}"
                 for k in cands[:4]]
        msg = f"⚽ Peneira: {len(cands)} de valor — " + "; ".join(itens)
        print("NOTIFICAR: " + (msg if len(msg) <= 190 else msg[:187] + "…"))
    else:
        print("Nenhum jogo de valor na peneira de hoje.")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", help="AAAA-MM-DD (padrão: hoje, horário de Brasília)")
    p.add_argument("--torneios", help="IDs do Sofascore separados por vírgula (padrão: config.json)")
    p.add_argument("--sem-chuva", action="store_true", help="não consulta a previsão do tempo")
    p.add_argument("--sem-cache", action="store_true")
    p.add_argument("--jogos", help="IDs de jogos do Sofascore (reavalia só esses, ignora a lista de torneios)")
    p.add_argument("--curto", action="store_true", help="resumo de celular + linha NOTIFICAR")
    p.add_argument("--json", action="store_true")
    a = p.parse_args()

    cfg = n.carregar_config()
    cfg["varredura"] = {**VARREDURA_PADRAO, **{k: v for k, v in cfg.get("varredura", {}).items() if not k.startswith("_")}}
    agora = datetime.now(FUSO_BR)
    data = a.data or agora.date().isoformat()
    torneios = ({int(x) for x in a.torneios.split(",") if x.strip()} if a.torneios
                else {int(x) for x in cfg["varredura"]["torneios_sofascore"]})
    if not torneios:
        sys.exit("Nenhum torneio configurado (config.json → varredura.torneios_sofascore).")
    api = Sofascore(None if a.sem_cache else CACHE_PADRAO, data)

    if a.jogos:
        jogos = [ev for ev in (api.get(f"event/{x.strip()}", cache=None).get("event")
                               for x in a.jogos.split(",") if x.strip()) if ev and ev["status"]["type"] == "notstarted" and ev["startTimestamp"] > time.time()]
    else:
        jogos = listar_jogos(api, data, torneios)
    cache_liga: dict = {}
    infos = em_paralelo(lambda e: analisar_jogo(api, e, cfg, cache_liga), jogos, 4)

    candidatos, excl_chuva, descartes = [], [], {}
    for info in infos:
        if not info["candidatos"]:
            m = "amostra curta" if (info["motivo"] or "").startswith("amostra curta") else (info["motivo"] or MOTIVOS[0])
            descartes[m] = descartes.get(m, 0) + 1
            continue
        chuva = {"status": "não verificada", "detalhe": "--sem-chuva"} if a.sem_chuva else checar_chuva(info, data, cfg)
        if chuva["status"] == "CHUVA":
            excl_chuva.append(f"{info['jogo']} ({chuva['detalhe']})")
            continue
        for k in info["candidatos"]:
            candidatos.append({**k, "hora": info["hora"], "jogo": info["jogo"], "competicao": info["competicao"],
                               "id": info["id"], "arbitro": info.get("arbitro"),
                               "chuva": chuva["status"] if chuva["status"] == "seco" else "⚠️ não verificada"})
    candidatos.sort(key=lambda c: (-c["p"], -c["ev"]))
    res = {
        "data": data, "consultado": datetime.now(FUSO_BR).strftime("%H:%M"),
        "prob_triagem": cfg["varredura"]["prob_triagem"], "ev_minimo": cfg["criterios"]["ev_minimo"],
        "contagem": {"jogos": len(jogos), "avaliados": sum(1 for i in infos if i.get("lambda") is not None or i["candidatos"]),
                     "com_candidato": sum(1 for i in infos if i["candidatos"])},
        "candidatos": candidatos, "chuva_excluidos": excl_chuva, "descartes": descartes,
        "falhas_rede": api.falhas,
    }
    if not a.jogos and not a.sem_cache:
        CACHE_PADRAO.mkdir(parents=True, exist_ok=True)
        (CACHE_PADRAO / f"peneira-{data}.json").write_text(json.dumps(res, ensure_ascii=False, default=str), encoding="utf-8")
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=2, default=str))
    elif a.curto:
        imprimir_curto(res)
    else:
        imprimir(res)


if __name__ == "__main__":
    main()
