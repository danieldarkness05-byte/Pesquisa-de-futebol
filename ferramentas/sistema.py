#!/usr/bin/env python3
"""Simula apostas de Sistema (Duplas, Triplas...) com as seleções aprovadas.

Cada seleção: "rótulo|jogo|odd|prob"
  python3 ferramentas/sistema.py --tamanhos 2 --stake 5 \
      --sel "Under 2.5|Bahia x Vitória|1.72|0.66" \
      --sel "Ambas não|Sport x Náutico|1.85|0.62" \
      --sel "Menos de 10.5 esc.|Ceará x Fortaleza|1.65|0.68"

--tamanhos 2,3 = Duplas + Triplas. --stake = valor por combinação.
Assume seleções independentes (por isso avisa se houver duas do mesmo jogo).
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import sys

import nucleo as n

LIMITE_SELECOES = 14


def parse_sel(texto: str) -> dict:
    partes = [p.strip() for p in texto.split("|")]
    if len(partes) != 4:
        sys.exit(f'Seleção inválida: "{texto}". Formato: "rótulo|jogo|odd|prob"')
    rotulo, jogo, odd, prob = partes
    prob_f = float(prob.replace(",", "."))
    return {"rotulo": rotulo, "jogo": jogo, "odd": float(odd.replace(",", ".")),
            "prob": prob_f / 100 if prob_f > 1 else prob_f}


def simular(sels: list[dict], tamanhos: list[int], stake: float) -> dict:
    k = len(sels)
    combos = [c for t in tamanhos for c in itertools.combinations(range(k), t)]
    if not combos:
        raise ValueError("nenhuma combinação — confira os tamanhos")
    total = stake * len(combos)
    odds_combo = {c: math.prod(sels[i]["odd"] for i in c) for c in combos}

    distribuicao = []
    ev_ret = 0.0
    p_lucro = p_perda_total = 0.0
    for acertos in itertools.product([True, False], repeat=k):
        p = math.prod(s["prob"] if ok else 1 - s["prob"] for s, ok in zip(sels, acertos))
        retorno = sum(stake * odds_combo[c] for c in combos if all(acertos[i] for i in c))
        ev_ret += p * retorno
        if retorno > total + 1e-9:
            p_lucro += p
        if retorno <= 1e-9:
            p_perda_total += p
        distribuicao.append((sum(acertos), retorno, p))

    por_acertos = {}
    for qtd, ret, p in distribuicao:
        d = por_acertos.setdefault(qtd, {"p": 0.0, "min": float("inf"), "max": 0.0})
        d["p"] += p
        d["min"] = min(d["min"], ret)
        d["max"] = max(d["max"], ret)

    vistos: dict[str, str] = {}
    contagem: dict[str, int] = {}
    for s in sels:
        chave = n.normalizar(s["jogo"])
        vistos.setdefault(chave, s["jogo"])
        contagem[chave] = contagem.get(chave, 0) + 1
    repetidos = sorted(vistos[k] for k, c in contagem.items() if c > 1)
    return {
        "combinacoes": len(combos), "stake_total": total,
        "retorno_esperado": ev_ret, "ev": ev_ret / total - 1,
        "p_lucro": p_lucro, "p_perda_total": p_perda_total,
        "por_acertos": {q: por_acertos[q] for q in sorted(por_acertos, reverse=True)},
        "jogos_repetidos": repetidos,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--sel", action="append", required=True, help='"rótulo|jogo|odd|prob"')
    p.add_argument("--tamanhos", default="2", help="2 = Duplas, 3 = Triplas, 2,3 = ambas")
    p.add_argument("--stake", type=float, default=1.0, help="valor por combinação (R$)")
    p.add_argument("--json", action="store_true")
    a = p.parse_args()

    sels = [parse_sel(s) for s in a.sel]
    if len(sels) > LIMITE_SELECOES:
        sys.exit(f"Máximo de {LIMITE_SELECOES} seleções.")
    tamanhos = sorted({int(t) for t in a.tamanhos.split(",")})
    if any(t < 1 or t > len(sels) for t in tamanhos):
        sys.exit("Tamanho de combinação maior que o número de seleções.")
    r = simular(sels, tamanhos, a.stake)

    if a.json:
        print(json.dumps({"selecoes": sels, **{k: v for k, v in r.items() if k != "por_acertos"},
                          "por_acertos": {str(k): v for k, v in r["por_acertos"].items()}},
                         ensure_ascii=False, indent=2))
        return

    nomes = {1: "Simples", 2: "Duplas", 3: "Triplas", 4: "Quádruplas"}
    print("## Sistema " + " + ".join(nomes.get(t, f"{t}-plas") for t in tamanhos) + "\n")
    print(n.tabela(["Seleção", "Jogo", "Odd", "Prob.", "EV"],
                   [[s["rotulo"], s["jogo"], f"{s['odd']:.2f}", n.pct(s["prob"]),
                     f"{n.ev(s['prob'], s['odd']) * 100:+.1f}%"] for s in sels]))
    print(f"\n- {r['combinacoes']} combinações × R$ {a.stake:.2f} = **R$ {r['stake_total']:.2f}**")
    print(f"- Retorno esperado: R$ {r['retorno_esperado']:.2f} (EV {r['ev'] * 100:+.1f}%)")
    print(f"- Chance de lucro: {n.pct(r['p_lucro'])} | chance de perder tudo: {n.pct(r['p_perda_total'])}\n")
    linhas = []
    for qtd, d in r["por_acertos"].items():
        ret = (f"R$ {d['min']:.2f}" if abs(d["min"] - d["max"]) < 0.005
               else f"R$ {d['min']:.2f}–{d['max']:.2f}")
        linhas.append([f"{qtd}/{len(sels)}", n.pct(d["p"]), ret,
                       "lucro" if d["min"] > r["stake_total"] else
                       ("depende" if d["max"] > r["stake_total"] else "prejuízo")])
    print(n.tabela(["Acertos", "Chance", "Retorno", "Resultado"], linhas))
    if r["jogos_repetidos"]:
        print(f"\n⚠️ Seleções do mesmo jogo ({', '.join(r['jogos_repetidos'])}): resultados "
              "correlacionados, a simulação fica otimista. A casa também costuma bloquear.")
    ruins = [s["rotulo"] for s in sels if n.ev(s["prob"], s["odd"]) <= 0]
    if ruins:
        print(f"\n⚠️ Seleções sem valor individual: {', '.join(ruins)}. Combinar não cria valor.")


if __name__ == "__main__":
    main()
