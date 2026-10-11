#!/usr/bin/env python3
"""Registro de apostas e balanço (dados/registro-apostas.csv).

Exemplos:
  python3 ferramentas/registro.py add --jogo "Bahia x Vitória" --competicao "Série A" \
      --mercado "Gols" --selecao "Menos de 2.5" --odd 1.72 --prob 0.66 --stake 10
  python3 ferramentas/registro.py add --tipo sistema --jogo "3 jogos" --mercado "Sistema Duplas" \
      --selecao "Under Bahia + Ambas não Sport + Esc. Ceará" --odd 0 --prob 0 --stake 15
  python3 ferramentas/registro.py pendentes
  python3 ferramentas/registro.py resolver --id 3 --resultado green --odd-fechamento 1.65
  python3 ferramentas/registro.py resolver --id 4 --retorno 22.40      # sistema: informe o retorno
  python3 ferramentas/registro.py resumo [--desde 2026-10-01]

Resultados: green, red, void (devolvida), meio-green, meio-red.
"""
from __future__ import annotations

import argparse
import csv
import sys
from datetime import date
from pathlib import Path

import nucleo as n

ARQUIVO = n.RAIZ / "dados" / "registro-apostas.csv"
CAMPOS = ["id", "data", "competicao", "jogo", "mercado", "selecao", "tipo", "odd", "prob_estimada",
          "stake", "casa", "status", "retorno", "lucro", "odd_fechamento", "obs"]
FATOR = {"green": None, "red": 0.0, "void": 1.0, "meio-green": None, "meio-red": 0.5}


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
        for l in linhas:
            w.writerow({k: l.get(k, "") for k in CAMPOS})


def adicionar(linhas: list[dict], **campos) -> dict:
    proximo = max((int(l["id"]) for l in linhas if l.get("id", "").isdigit()), default=0) + 1
    nova = {k: "" for k in CAMPOS}
    nova.update({k: ("" if v is None else str(v)) for k, v in campos.items()})
    nova.update({"id": str(proximo), "status": "pendente"})
    nova["data"] = nova["data"] or date.today().isoformat()
    linhas.append(nova)
    return nova


def resolver(linha: dict, resultado: str | None, retorno: float | None,
             odd_fechamento: float | None = None) -> dict:
    stake = float(linha["stake"])
    if retorno is None:
        if resultado not in FATOR:
            raise ValueError(f"resultado inválido: {resultado}")
        odd = float(linha["odd"])
        if resultado == "green":
            retorno = stake * odd
        elif resultado == "meio-green":
            retorno = stake / 2 * odd + stake / 2
        else:
            retorno = stake * FATOR[resultado]
    if resultado is None:
        resultado = "green" if retorno > stake + 1e-9 else ("void" if abs(retorno - stake) < 1e-9 else "red")
    linha["status"] = resultado
    linha["retorno"] = f"{retorno:.2f}"
    linha["lucro"] = f"{retorno - stake:.2f}"
    if odd_fechamento:
        linha["odd_fechamento"] = f"{odd_fechamento:.2f}"
    return linha


def resumo(linhas: list[dict], desde: str | None = None) -> str:
    feitas = [l for l in linhas if l["status"] not in ("pendente", "")
              and (not desde or l["data"] >= desde)]
    if not feitas:
        return "Nenhuma aposta resolvida no período."
    out = []
    stake = sum(float(l["stake"]) for l in feitas)
    lucro = sum(float(l["lucro"]) for l in feitas)
    decididas = [l for l in feitas if l["status"] != "void"]
    acertos = sum(1 for l in decididas if l["status"] in ("green", "meio-green"))
    out.append(f"## Balanço{' desde ' + desde if desde else ''}\n")
    out.append(f"- Apostas resolvidas: {len(feitas)} | pendentes: "
               f"{sum(1 for l in linhas if l['status'] == 'pendente')}")
    out.append(f"- Acerto: {acertos}/{len(decididas)} "
               f"({n.pct(acertos / len(decididas)) if decididas else '—'})")
    out.append(f"- Investido: R$ {stake:.2f} | lucro: R$ {lucro:+.2f} | ROI: "
               f"{(lucro / stake * 100 if stake else 0):+.1f}%")
    clv = [float(l["odd"]) / float(l["odd_fechamento"]) - 1 for l in feitas
           if l.get("odd_fechamento") and float(l.get("odd") or 0) > 1]
    if clv:
        out.append(f"- CLV médio (sua odd vs. fechamento): {sum(clv) / len(clv) * 100:+.1f}% "
                   f"em {len(clv)} apostas — positivo de forma consistente é o melhor sinal de vantagem real")

    def agrupar(campo: str) -> list[list[str]]:
        grupos: dict[str, list[dict]] = {}
        for l in feitas:
            grupos.setdefault(l[campo] or "—", []).append(l)
        linhas_tab = []
        for nome, g in sorted(grupos.items(), key=lambda x: -sum(float(l["lucro"]) for l in x[1])):
            st = sum(float(l["stake"]) for l in g)
            lu = sum(float(l["lucro"]) for l in g)
            dec = [l for l in g if l["status"] != "void"]
            ac = sum(1 for l in dec if l["status"] in ("green", "meio-green"))
            linhas_tab.append([nome, str(len(g)), n.pct(ac / len(dec)) if dec else "—",
                               f"R$ {lu:+.2f}", f"{(lu / st * 100 if st else 0):+.1f}%"])
        return linhas_tab

    for campo, titulo in (("mercado", "Por mercado"), ("competicao", "Por competição")):
        out.append(f"\n### {titulo}\n")
        out.append(n.tabela([titulo.split()[-1].capitalize(), "Apostas", "Acerto", "Lucro", "ROI"],
                            agrupar(campo)))

    simples = [l for l in decididas if l["tipo"] != "sistema" and l.get("prob_estimada")
               and float(l["prob_estimada"]) > 0]
    if simples:
        out.append("\n### Calibração (as probabilidades estimadas estão batendo?)\n")
        faixas = [(0.0, 0.60), (0.60, 0.65), (0.65, 0.70), (0.70, 0.80), (0.80, 1.01)]
        linhas_cal = []
        for lo, hi in faixas:
            g = [l for l in simples if lo <= float(l["prob_estimada"]) < hi]
            if not g:
                continue
            prev = sum(float(l["prob_estimada"]) for l in g) / len(g)
            real = sum(1 for l in g if l["status"] in ("green", "meio-green")) / len(g)
            rot = f"{lo:.0%}–{min(hi, 1):.0%}"
            linhas_cal.append([rot, str(len(g)), n.pct(prev), n.pct(real), f"{(real - prev) * 100:+.1f} p.p."])
        out.append(n.tabela(["Faixa", "Apostas", "Previsto", "Real", "Diferença"], linhas_cal))
        if len(simples) < 50:
            out.append(f"\n(Com {len(simples)} apostas a calibração ainda oscila muito; "
                       "fica confiável a partir de umas 100.)")
    return "\n".join(out)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    ad = sub.add_parser("add")
    ad.add_argument("--data")
    ad.add_argument("--competicao", default="")
    ad.add_argument("--jogo", required=True)
    ad.add_argument("--mercado", required=True)
    ad.add_argument("--selecao", required=True)
    ad.add_argument("--tipo", default="simples", choices=["simples", "multipla", "sistema"])
    ad.add_argument("--odd", type=float, required=True)
    ad.add_argument("--prob", type=float, required=True, help="probabilidade estimada (0-1)")
    ad.add_argument("--stake", type=float, required=True)
    ad.add_argument("--casa", default="Betano")
    ad.add_argument("--obs", default="")
    sub.add_parser("pendentes")
    rs = sub.add_parser("resolver")
    rs.add_argument("--id", required=True)
    rs.add_argument("--resultado", choices=list(FATOR))
    rs.add_argument("--retorno", type=float, help="valor total recebido (use em sistemas)")
    rs.add_argument("--odd-fechamento", type=float)
    rm = sub.add_parser("resumo")
    rm.add_argument("--desde")
    a = p.parse_args()

    linhas = ler()
    if a.cmd == "add":
        prob = a.prob / 100 if a.prob > 1 else a.prob
        nova = adicionar(linhas, data=a.data, competicao=a.competicao, jogo=a.jogo, mercado=a.mercado,
                         selecao=a.selecao, tipo=a.tipo, odd=f"{a.odd:.2f}", prob_estimada=f"{prob:.3f}",
                         stake=f"{a.stake:.2f}", casa=a.casa, obs=a.obs)
        salvar(linhas)
        print(f"Registrada #{nova['id']}: {nova['jogo']} — {nova['selecao']} @ {nova['odd']} (R$ {nova['stake']})")
    elif a.cmd == "pendentes":
        pend = [l for l in linhas if l["status"] == "pendente"]
        if not pend:
            print("Nenhuma aposta pendente.")
        else:
            print(n.tabela(["ID", "Data", "Jogo", "Seleção", "Odd", "Stake"],
                           [[l["id"], l["data"], l["jogo"], l["selecao"], l["odd"], l["stake"]] for l in pend]))
    elif a.cmd == "resolver":
        alvo = next((l for l in linhas if l["id"] == str(a.id)), None)
        if not alvo:
            sys.exit(f"Aposta #{a.id} não encontrada.")
        if a.resultado is None and a.retorno is None:
            sys.exit("Informe --resultado ou --retorno.")
        resolver(alvo, a.resultado, a.retorno, a.odd_fechamento)
        salvar(linhas)
        print(f"#{alvo['id']} {alvo['status']}: lucro R$ {alvo['lucro']}")
    else:
        print(resumo(linhas, a.desde))


if __name__ == "__main__":
    main()
