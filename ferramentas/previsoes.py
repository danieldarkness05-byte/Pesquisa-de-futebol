#!/usr/bin/env python3
"""Registro das previsões das análises (defesa fraca, favoritos...) e calibração.

Diferente do registro de APOSTAS (registro.py): aqui entra todo pick que a
análise entregou ao Daniel, apostado ou não. O resultado sai sozinho do
Sofascore, e o resumo mostra se as probabilidades estão calibradas — é assim que
a análise evolui (ver docs/licoes.md).

Mercados (do ponto de vista do lado escolhido, `--lado casa|fora`):
  marca_1, marca_2, marca_3   o time marca 1+, 2+, 3+ gols
  vence, dupla_chance          vitória / vitória ou empate
  over_1.5, over_2.5, under_2.5 ...  total de gols do jogo (lado ignorado)

Exemplos:
  python3 ferramentas/previsoes.py add --data 2026-10-13 --evento 15271307 \
      --jogo "IFK Norrköping x GIF Sundsvall" --competicao Superettan --mercado marca_1 \
      --lado casa --prob 0.83 --odd-minima 1.24 --analise defesa --alertas "pausa de 3 semanas"
  python3 ferramentas/previsoes.py add-json --arquivo /tmp/picks.json   # lista de objetos com os mesmos campos
  python3 ferramentas/previsoes.py resolver          # busca placares finais no Sofascore
  python3 ferramentas/previsoes.py pendentes
  python3 ferramentas/previsoes.py resumo [--analise defesa] [--desde 2026-10-01] [--curto]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import nucleo as n

ARQUIVO = n.RAIZ / "dados" / "previsoes.csv"
CAMPOS = ["id", "data", "hora", "evento", "jogo", "competicao", "nivel", "analise", "mercado", "lado",
          "prob", "odd_minima", "odd_casa", "alertas", "status", "placar", "acerto", "obs"]
FAIXAS = [(0.6, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.01)]


def ler(caminho: Path = ARQUIVO) -> list[dict]:
    if not caminho.exists():
        return []
    with open(caminho, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def salvar(linhas: list[dict], caminho: Path = ARQUIVO) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        w.writeheader()
        for linha in linhas:
            w.writerow({k: linha.get(k, "") for k in CAMPOS})


def avaliar(mercado: str, lado: str, gols_casa: int, gols_fora: int) -> bool | None:
    """True/False se o pick bateu; None se o mercado não é reconhecido."""
    meu, dele = (gols_casa, gols_fora) if lado == "casa" else (gols_fora, gols_casa)
    if mercado.startswith("marca_"):
        return meu >= int(mercado.split("_")[1])
    if mercado == "vence":
        return meu > dele
    if mercado == "dupla_chance":
        return meu >= dele
    if mercado == "sem_empate":  # dupla chance 12
        return meu != dele
    if mercado in ("ambas_sim", "ambas_nao"):
        return (gols_casa > 0 and gols_fora > 0) == (mercado == "ambas_sim")
    if mercado.startswith("handicap_"):  # linha .5 do ponto de vista do lado: handicap_-1.5, handicap_+1.5
        return meu - dele + float(mercado[len("handicap_"):]) > 0
    for prefixo in ("over_", "under_"):
        if mercado.startswith(prefixo):
            linha = float(mercado[len(prefixo):])
            tot = gols_casa + gols_fora
            return tot > linha if prefixo == "over_" else tot < linha
    return None


LADOS = {"casa": "casa", "fora": "fora", "home": "casa", "away": "fora", "mandante": "casa", "visitante": "fora"}


def normalizar(novo: dict) -> dict:
    """Valida e padroniza um pick (lado, listas, prob, mercado). Levanta ValueError."""
    nv = {k: val for k, val in novo.items() if k in CAMPOS and val is not None}
    for k, val in list(nv.items()):
        if isinstance(val, (list, tuple)):
            nv[k] = "; ".join(str(x) for x in val)
    nv["analise"] = str(nv.get("analise") or "defesa").strip()
    lado = str(nv.get("lado") or "").strip().lower()
    mercado = str(nv.get("mercado") or "").strip()
    precisa_lado = not mercado.startswith(("over_", "under_", "ambas_", "sem_empate"))
    if precisa_lado and lado not in LADOS:
        raise ValueError(f"lado deve ser casa ou fora (veio {nv.get('lado')!r}) no mercado {mercado}")
    nv["lado"] = LADOS.get(lado, "casa")
    nv["mercado"] = mercado
    if avaliar(mercado, nv["lado"], 0, 0) is None:
        raise ValueError(f"mercado desconhecido: {mercado}")
    for k in ("data", "evento", "jogo", "prob"):
        if not str(nv.get(k, "")).strip():
            raise ValueError(f"falta o campo {k}")
    prob = float(nv["prob"])
    if not 0 < prob <= 1:
        raise ValueError(f"prob deve estar entre 0 e 1 (veio {prob})")
    return nv


def adicionar(linhas: list[dict], novo: dict) -> dict:
    # mesmo evento + mercado + lado + análise = mesma previsão (atualiza em vez de duplicar)
    for x in linhas:
        if (x["evento"], x["mercado"], x["lado"], x["analise"]) == (
                str(novo["evento"]), novo["mercado"], novo["lado"], novo["analise"]) and x["status"] == "pendente":
            x.update({k: str(val) for k, val in novo.items() if val not in (None, "")})
            return x
    prox = max((int(x["id"]) for x in linhas), default=0) + 1
    linha = {k: "" for k in CAMPOS}
    linha.update({k: str(val) for k, val in novo.items() if val is not None})
    linha.update({"id": str(prox), "status": "pendente"})
    linhas.append(linha)
    return linha


def resolver(linhas: list[dict], buscar) -> list[dict]:
    """Resolve as pendentes com o evento já encerrado. `buscar(evento) -> dict` do Sofascore."""
    feitos = []
    for x in linhas:
        if x["status"] != "pendente" or not x["evento"]:
            continue
        e = (buscar(x["evento"]) or {}).get("event") or {}
        st = (e.get("status") or {}).get("type")
        if st in ("canceled", "postponed", "abandoned", "suspended"):
            x.update({"status": "anulada", "obs": (x["obs"] + f" {st}").strip()})
            feitos.append(x)
            continue
        if st != "finished":
            continue
        hs = (e.get("homeScore") or {}).get("normaltime", (e.get("homeScore") or {}).get("current"))
        as_ = (e.get("awayScore") or {}).get("normaltime", (e.get("awayScore") or {}).get("current"))
        if hs is None or as_ is None:
            continue
        ok = avaliar(x["mercado"], x["lado"], int(hs), int(as_))
        if ok is None:
            continue
        x.update({"status": "resolvida", "placar": f"{hs}-{as_}", "acerto": "1" if ok else "0"})
        feitos.append(x)
    return feitos


def resumo(linhas: list[dict]) -> dict:
    res = [x for x in linhas if x["status"] == "resolvida" and x["prob"]]
    out = {"n": len(res), "pendentes": sum(1 for x in linhas if x["status"] == "pendente")}
    if not res:
        return out
    ps = [float(x["prob"]) for x in res]
    ac = [int(x["acerto"]) for x in res]
    out.update({"acertos": sum(ac), "taxa": sum(ac) / len(ac), "prob_media": sum(ps) / len(ps),
                "brier": sum((p - a) ** 2 for p, a in zip(ps, ac)) / len(ps), "faixas": [], "por_mercado": {},
                "por_alerta": {}})
    for lo, hi in FAIXAS:
        sel = [(p, a) for p, a in zip(ps, ac) if lo <= p < hi]
        if sel:
            out["faixas"].append({"faixa": f"{lo:.0%}–{min(hi, 1):.0%}", "n": len(sel),
                                  "prevista": sum(p for p, _ in sel) / len(sel),
                                  "real": sum(a for _, a in sel) / len(sel)})
    for chave, grupo in (("por_mercado", lambda x: x["mercado"]),
                         ("por_alerta", lambda x: "com alertas" if x["alertas"] else "sem alertas"),
                         ("por_nivel", lambda x: x["nivel"] or "pro")):
        g: dict[str, list] = {}
        for x in res:
            g.setdefault(grupo(x), []).append(x)
        out[chave] = {k: {"n": len(xs), "real": sum(int(x["acerto"]) for x in xs) / len(xs),
                          "prevista": sum(float(x["prob"]) for x in xs) / len(xs)} for k, xs in g.items()}
    return out


def avisos_calibracao(r: dict, minimo: int = 30, folga: float = 0.05) -> list[str]:
    """Faixa com amostra razoável acertando bem menos que o previsto → ser mais conservador."""
    av = []
    for f in r.get("faixas", []):
        if f["n"] >= minimo and f["real"] < f["prevista"] - folga:
            av.append(f"faixa {f['faixa']}: acerto {f['real']:.0%} x previsto {f['prevista']:.0%} "
                      f"em {f['n']} — reduzir a probabilidade nessa faixa")
    if not av and r.get("n", 0) < minimo:
        av.append(f"amostra ainda pequena ({r.get('n', 0)} resolvidas): sem ajuste de calibração por enquanto")
    return av


def _buscar_sofascore():
    """Sofascore pelo id; evento "365-<id>" (registrado quando o Sofascore estava fora) vai ao 365Scores."""
    import plataformas as pl
    import varredura as v
    api, p365 = v.Sofascore(None, ""), pl.S365("", pasta=None)

    def buscar(evento):
        if str(evento).startswith("365-"):
            return pl.evento_sofascore(p365.detalhe(int(str(evento)[4:])))
        return api.get(f"event/{evento}", cache=None)
    return buscar


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    ad = sub.add_parser("add")
    for campo in ("data", "hora", "evento", "jogo", "competicao", "nivel", "analise", "mercado", "lado",
                  "prob", "odd-minima", "odd-casa", "alertas", "obs"):
        ad.add_argument(f"--{campo}", required=campo in ("data", "evento", "jogo", "mercado", "prob"),
                        **({"choices": sorted(LADOS)} if campo == "lado" else {}))
    aj = sub.add_parser("add-json")
    aj.add_argument("--arquivo", required=True)
    sub.add_parser("resolver")
    sub.add_parser("pendentes")
    rs = sub.add_parser("resumo")
    rs.add_argument("--analise")
    rs.add_argument("--desde")
    rs.add_argument("--curto", action="store_true")
    rs.add_argument("--json", action="store_true")
    a = p.parse_args()

    linhas = ler()
    if a.cmd in ("add", "add-json"):
        novos = ([{k.replace("-", "_"): val for k, val in vars(a).items() if k not in ("cmd",)}]
                 if a.cmd == "add" else json.loads(Path(a.arquivo).read_text(encoding="utf-8")))
        try:  # valida TUDO antes de gravar: ou entra a lista inteira, ou nada
            validos = [normalizar(nv) for nv in novos]
        except (ValueError, TypeError) as exc:
            sys.exit(f"Nada foi gravado: {exc}")
        feitos = [adicionar(linhas, nv) for nv in validos]
        salvar(linhas)
        for x in feitos:
            print(f"#{x['id']} {x['data']} {x['jogo']} — {x['mercado']} ({x['lado']}) {float(x['prob']):.0%}")
        return
    if a.cmd == "resolver":
        feitos = resolver(linhas, _buscar_sofascore())
        salvar(linhas)
        for x in feitos:
            marca = {"1": "✅", "0": "❌"}.get(x["acerto"], "➖")
            print(f"{marca} #{x['id']} {x['data']} {x['jogo']} — {x['mercado']} ({x['lado']}) "
                  f"{float(x['prob']):.0%} · {x['placar'] or x['status']}")
        print(f"{len(feitos)} resolvidas agora; {sum(1 for x in linhas if x['status'] == 'pendente')} pendentes.")
        return
    if a.cmd == "pendentes":
        for x in linhas:
            if x["status"] == "pendente":
                print(f"#{x['id']} {x['data']} {x['hora']} {x['jogo']} — {x['mercado']} ({x['lado']}) {float(x['prob']):.0%}")
        return
    sel = [x for x in linhas if (not a.analise or x["analise"] == a.analise) and (not a.desde or x["data"] >= a.desde)]
    r = resumo(sel)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return
    if not r.get("n"):
        print(f"Nenhuma previsão resolvida ainda ({r['pendentes']} pendentes).")
        return
    print(f"{r['n']} resolvidas: {r['acertos']} acertos ({r['taxa']:.0%}) · prob. média prevista "
          f"{r['prob_media']:.0%} · Brier {r['brier']:.3f} · {r['pendentes']} pendentes")
    for f in r["faixas"]:
        print(f"- {f['faixa']}: {f['n']} picks · previsto {f['prevista']:.0%} · real {f['real']:.0%}")
    if not a.curto:
        for chave, nome in (("por_mercado", "mercado"), ("por_alerta", "alertas"), ("por_nivel", "nível")):
            for k, g in r[chave].items():
                print(f"  {nome} {k}: {g['n']} · previsto {g['prevista']:.0%} · real {g['real']:.0%}")
    for av in avisos_calibracao(r):
        print(f"⚠️ {av}")


if __name__ == "__main__":
    main()
