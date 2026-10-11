#!/usr/bin/env python3
"""Previsão de chuva para o dia/horário do jogo (Open-Meteo, grátis, sem chave).

Exemplos:
  python3 ferramentas/clima.py --cidade "Salvador" --data 2026-10-12 --hora 19:00
  python3 ferramentas/clima.py --lat -8.04 --lon -34.92 --data 2026-10-12 --hora 16:00
  python3 ferramentas/clima.py --cidade "Recife" --data 2026-10-12 --hora 16:00 --janela jogo

--hora é no horário de Brasília. A regra padrão (config.json → chuva.janela)
é "dia": exclui o jogo se houver previsão de chuva em qualquer hora do dia
da partida. Com "jogo", olha só de 1h antes até 3h depois do início.

Sem acesso direto à internet (ex.: sessão na nuvem com rede restrita)?
Use --url para ver o endereço, baixe o JSON com o WebFetch e passe
--arquivo previsao.json.

Saída: CHUVA (excluir), SEM CHUVA ou ERRO (verificar manualmente).
Código de saída: 0 = consultou (com ou sem chuva), 2 = erro.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta

import nucleo as n

FUSO = "America/Sao_Paulo"
GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
PREV_URL = "https://api.open-meteo.com/v1/forecast"


def _get_json(url: str, params: dict) -> dict:
    req = urllib.request.Request(f"{url}?{urllib.parse.urlencode(params)}",
                                 headers={"User-Agent": "futebol-pesquisa/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def geocodificar(cidade: str, pais: str = "BR") -> dict:
    dados = _get_json(GEO_URL, {"name": cidade, "count": 1, "language": "pt", "countryCode": pais})
    res = dados.get("results") or []
    if not res:
        raise LookupError(f'cidade "{cidade}" não encontrada ({pais})')
    r = res[0]
    return {"nome": f"{r.get('name')}, {r.get('admin1', '')}".strip(", "),
            "lat": r["latitude"], "lon": r["longitude"]}


def buscar_previsao(lat: float, lon: float, data: str) -> dict:
    return _get_json(PREV_URL, {
        "latitude": lat, "longitude": lon, "timezone": FUSO,
        "hourly": "precipitation_probability,precipitation",
        "start_date": data, "end_date": data,
    })


def avaliar_chuva(previsao: dict, inicio: datetime, cfg: dict, janela: str | None = None) -> dict:
    c = cfg["chuva"]
    janela = janela or c["janela"]
    h = previsao.get("hourly") or {}
    horas = h.get("time") or []
    probs = h.get("precipitation_probability") or [None] * len(horas)
    mms = h.get("precipitation") or [None] * len(horas)
    if not horas:
        raise ValueError("previsão sem dados horários (data fora do alcance de ~16 dias?)")

    ini_jogo = inicio - timedelta(hours=c["horas_antes"])
    fim_jogo = inicio + timedelta(hours=c["horas_depois"])
    linhas = []
    for t, pr, mm in zip(horas, probs, mms):
        dt = datetime.fromisoformat(t)
        linhas.append({"hora": dt, "prob": pr, "mm": mm,
                       "no_jogo": ini_jogo <= dt <= fim_jogo})

    def resumo(sel: list[dict]) -> dict:
        ps = [x["prob"] for x in sel if x["prob"] is not None]
        ms = [x["mm"] for x in sel if x["mm"] is not None]
        return {"prob_max": max(ps) if ps else None, "mm_total": round(sum(ms), 1) if ms else None,
                "horas_chuva": [x["hora"].strftime("%H:%M") for x in sel
                                if (x["prob"] or 0) >= c["prob_limiar"] or (x["mm"] or 0) >= 0.5]}

    dia = resumo(linhas)
    jogo = resumo([x for x in linhas if x["no_jogo"]])
    base = dia if janela == "dia" else jogo
    chuva = ((base["prob_max"] or 0) >= c["prob_limiar"]
             or (base["mm_total"] or 0) >= c["mm_limiar"])
    return {"janela": janela, "chuva": chuva, "dia": dia, "jogo": jogo,
            "criterio": f"prob ≥ {c['prob_limiar']}% ou ≥ {c['mm_limiar']} mm"}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--cidade")
    p.add_argument("--pais", default="BR", help="código do país (padrão BR)")
    p.add_argument("--lat", type=float)
    p.add_argument("--lon", type=float)
    p.add_argument("--data", required=True, help="AAAA-MM-DD")
    p.add_argument("--hora", default="16:00", help="início do jogo, horário de Brasília (HH:MM)")
    p.add_argument("--janela", choices=["dia", "jogo"], help="sobrescreve config.json")
    p.add_argument("--arquivo", help="JSON da Open-Meteo já baixado (pula a consulta)")
    p.add_argument("--url", action="store_true", help="só mostra a URL da previsão e sai")
    p.add_argument("--json", action="store_true")
    a = p.parse_args()
    cfg = n.carregar_config()

    try:
        if a.arquivo:
            local = {"nome": a.cidade or a.arquivo, "lat": a.lat, "lon": a.lon}
        elif a.lat is not None and a.lon is not None:
            local = {"nome": f"{a.lat:.3f}, {a.lon:.3f}", "lat": a.lat, "lon": a.lon}
        elif a.cidade:
            local = geocodificar(a.cidade, a.pais)
        else:
            sys.exit("Informe --cidade ou --lat/--lon.")
        if a.url:
            print(f"{PREV_URL}?{urllib.parse.urlencode({'latitude': local['lat'], 'longitude': local['lon'], 'timezone': FUSO, 'hourly': 'precipitation_probability,precipitation', 'start_date': a.data, 'end_date': a.data})}")
            return
        inicio = datetime.fromisoformat(f"{a.data}T{a.hora}")
        if a.arquivo:
            with open(a.arquivo, encoding="utf-8") as f:
                previsao = json.load(f)
        else:
            previsao = buscar_previsao(local["lat"], local["lon"], a.data)
        r = avaliar_chuva(previsao, inicio, cfg, a.janela)
    except Exception as e:  # rede, cidade não encontrada, data fora do alcance
        msg = f"ERRO: não consegui consultar a previsão ({e}). Verifique manualmente — não exclua nem aprove automaticamente."
        print(json.dumps({"erro": str(e)}, ensure_ascii=False) if a.json else msg)
        sys.exit(2)

    if a.json:
        print(json.dumps({"local": local, **r}, ensure_ascii=False, indent=2, default=str))
    else:
        status = "🌧️ CHUVA — excluir da lista" if r["chuva"] else "☀️ SEM CHUVA"
        print(f"{local['nome']} — {a.data} {a.hora} (Brasília)")
        for nome, d in (("Dia todo", r["dia"]), ("Janela do jogo", r["jogo"])):
            horas = ", ".join(d["horas_chuva"]) or "nenhuma"
            print(f"- {nome}: prob. máx {d['prob_max']}% | {d['mm_total']} mm | horas com chuva: {horas}")
        print(f"- Regra usada: janela '{r['janela']}', {r['criterio']}")
        print(status)


if __name__ == "__main__":
    main()
