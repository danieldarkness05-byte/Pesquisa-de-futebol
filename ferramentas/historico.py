#!/usr/bin/env python3
"""Histórico de resultados (football-data.co.uk) → médias e gols esperados.

O arquivo BRA cobre o Brasileirão Série A (resultados + odds de fechamento).
Outras ligas no mesmo formato: ARG, MEX, USA, CHN, JPN... (--liga ARG).
Para Série B/C, Libertadores e Copa do Nordeste não há arquivo: pesquise
as médias na web e use prob.py direto.

Exemplos:
  python3 ferramentas/historico.py times --temporada 2026
  python3 ferramentas/historico.py medias --temporada 2026 --ultimos 10
  python3 ferramentas/historico.py confronto --casa Bahia --fora Vitoria --temporada 2026 \
      --odds "under2.5=1.72"
"""
from __future__ import annotations

import argparse
import csv
import difflib
import io
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

import nucleo as n

URL = "https://www.football-data.co.uk/new/{liga}.csv"
CACHE = n.RAIZ / "dados" / "cache"


def baixar(liga: str, forcar: bool = False) -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    destino = CACHE / f"{liga}.csv"
    if destino.exists() and not forcar and time.time() - destino.stat().st_mtime < 12 * 3600:
        return destino
    req = urllib.request.Request(URL.format(liga=liga), headers={"User-Agent": "futebol-pesquisa/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            destino.write_bytes(r.read())
    except Exception as e:
        if destino.exists():
            print(f"(aviso: não atualizei o cache — {e}; usando o arquivo salvo)", file=sys.stderr)
        else:
            sys.exit(f"Não consegui baixar {URL.format(liga=liga)}: {e}")
    return destino


def ler_jogos(texto: str, temporada: str | None = None) -> list[dict]:
    jogos = []
    for row in csv.DictReader(io.StringIO(texto)):
        row = {(k or "").strip(): (v or "").strip() for k, v in row.items()}
        if temporada and row.get("Season", "").split("/")[0] != str(temporada):
            continue
        try:
            hg, ag = int(row["HG"]), int(row["AG"])
        except (KeyError, ValueError):
            continue  # jogo sem placar (ainda não aconteceu)
        try:
            data = datetime.strptime(row.get("Date", ""), "%d/%m/%Y")
        except ValueError:
            try:
                data = datetime.strptime(row.get("Date", ""), "%d/%m/%y")
            except ValueError:
                data = datetime.min
        jogos.append({"data": data, "casa": row["Home"], "fora": row["Away"], "gc": hg, "gf": ag})
    jogos.sort(key=lambda j: j["data"])
    return jogos


def carregar(liga: str, temporada: str | None, arquivo: str | None, atualizar: bool) -> list[dict]:
    caminho = Path(arquivo) if arquivo else baixar(liga, atualizar)
    texto = caminho.read_bytes().decode("utf-8-sig", errors="replace")
    jogos = ler_jogos(texto, temporada)
    if not jogos:
        sys.exit(f"Nenhum jogo encontrado para a temporada {temporada}. "
                 f"Temporadas no arquivo: {sorted(temporadas(texto))}")
    return jogos


def temporadas(texto: str) -> set[str]:
    return {r.get("Season", "").strip() for r in csv.DictReader(io.StringIO(texto))}


def achar_time(nome: str, times: list[str]) -> str:
    alvo = n.normalizar(nome)
    mapa = {n.normalizar(t): t for t in times}
    if alvo in mapa:
        return mapa[alvo]
    contem = [t for k, t in mapa.items() if alvo in k or k in alvo]
    if len(contem) == 1:
        return contem[0]
    perto = difflib.get_close_matches(alvo, list(mapa), n=3, cutoff=0.5)
    if perto and (len(perto) == 1 or not contem):
        return mapa[perto[0]]
    opcoes = contem or [mapa[p] for p in perto]
    sys.exit(f'Time "{nome}" ambíguo ou não encontrado. Opções: {", ".join(opcoes) or "nenhuma"}. '
             "Use: historico.py times")


def medias(jogos: list[dict], ultimos: int | None = None) -> dict[str, dict]:
    times = sorted({j["casa"] for j in jogos} | {j["fora"] for j in jogos})
    saida = {}
    for t in times:
        casa = [j for j in jogos if j["casa"] == t]
        fora = [j for j in jogos if j["fora"] == t]
        if ultimos:
            casa, fora = casa[-ultimos:], fora[-ultimos:]
        def m(lst, campo):
            return sum(j[campo] for j in lst) / len(lst) if lst else 0.0
        saida[t] = {"jc": len(casa), "casa_marcados": m(casa, "gc"), "casa_sofridos": m(casa, "gf"),
                    "jf": len(fora), "fora_marcados": m(fora, "gf"), "fora_sofridos": m(fora, "gc")}
    return saida


def media_liga(jogos: list[dict]) -> tuple[float, float]:
    return (sum(j["gc"] for j in jogos) / len(jogos), sum(j["gf"] for j in jogos) / len(jogos))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for nome in ("times", "medias", "confronto"):
        s = sub.add_parser(nome)
        s.add_argument("--liga", default="BRA")
        s.add_argument("--temporada", default=str(datetime.now().year))
        s.add_argument("--arquivo", help="CSV local no formato football-data")
        s.add_argument("--atualizar", action="store_true", help="baixa de novo mesmo com cache recente")
        s.add_argument("--ultimos", type=int, help="usar só os últimos N jogos em casa/fora")
        if nome == "confronto":
            s.add_argument("--casa", required=True)
            s.add_argument("--fora", required=True)
            s.add_argument("--odds")
            s.add_argument("--json", action="store_true")
    a = p.parse_args()

    jogos = carregar(a.liga, a.temporada, a.arquivo, a.atualizar)
    tab = medias(jogos, a.ultimos)

    if a.cmd == "times":
        print(f"{a.liga} {a.temporada}: {len(jogos)} jogos com placar\n")
        print("\n".join(sorted(tab)))
        return

    if a.cmd == "medias":
        lc, lf = media_liga(jogos)
        print(f"## {a.liga} {a.temporada} — médias de gols"
              + (f" (últimos {a.ultimos} em casa/fora)" if a.ultimos else "") + "\n")
        print(f"Liga: mandantes {lc:.2f} × visitantes {lf:.2f} por jogo ({len(jogos)} jogos)\n")
        linhas = [[t, d["jc"], f"{d['casa_marcados']:.2f}", f"{d['casa_sofridos']:.2f}",
                   d["jf"], f"{d['fora_marcados']:.2f}", f"{d['fora_sofridos']:.2f}"]
                  for t, d in sorted(tab.items(), key=lambda x: -x[1]["fora_sofridos"])]
        print(n.tabela(["Time", "J casa", "GM casa", "GS casa", "J fora", "GM fora", "GS fora"], linhas))
        print("\n(ordenado por gols sofridos fora — defesas mais vazadas como visitante no topo)")
        return

    casa = achar_time(a.casa, list(tab))
    fora = achar_time(a.fora, list(tab))
    dc, df = tab[casa], tab[fora]
    if dc["jc"] < 3 or df["jf"] < 3:
        print(f"⚠️ Amostra pequena: {casa} tem {dc['jc']} jogos em casa, {fora} tem {df['jf']} fora.\n")
    liga_c, liga_f = media_liga(jogos)
    cmd = [sys.executable, str(Path(__file__).with_name("prob.py")), "gols",
           "--casa-marcados", f"{dc['casa_marcados']:.4f}", "--casa-sofridos", f"{dc['casa_sofridos']:.4f}",
           "--fora-marcados", f"{df['fora_marcados']:.4f}", "--fora-sofridos", f"{df['fora_sofridos']:.4f}",
           "--liga-mandante", f"{liga_c:.4f}", "--liga-visitante", f"{liga_f:.4f}",
           "--titulo", f"{casa} x {fora} — {a.liga} {a.temporada}"]
    if a.odds:
        cmd += ["--odds", a.odds]
    if a.json:
        cmd.append("--json")
    if not a.json:
        print(f"Fonte: football-data.co.uk ({a.liga}), {dc['jc']} jogos de {casa} em casa, "
              f"{df['jf']} de {fora} fora.\n")
    sys.exit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
