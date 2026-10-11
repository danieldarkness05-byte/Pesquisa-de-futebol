#!/usr/bin/env python3
"""Confere se uma odd tem valor para a probabilidade estimada.

Exemplos:
  python3 ferramentas/valor.py --prob 0.66 --odd 1.70
  python3 ferramentas/valor.py --prob 0.66 --odd 1.70 --mercado-odds 1.70,2.10
  python3 ferramentas/valor.py --prob 0.62 --odd 1.95 --devolucao 0.12   # linha asiática

--mercado-odds: todas as odds do mesmo mercado (ex.: under e over) para
calcular a margem da casa e a probabilidade "justa" que a casa está dando.
"""
from __future__ import annotations

import argparse
import json

import nucleo as n


def avaliar(prob: float, odd: float, cfg: dict, devolucao: float = 0.0,
            mercado_odds: list[float] | None = None) -> dict:
    ev_min = cfg["criterios"]["ev_minimo"]
    r = {
        "prob": prob, "devolucao": devolucao, "odd": odd,
        "prob_implicita": 1.0 / odd,
        "odd_justa": n.odd_justa(prob, devolucao),
        "odd_minima": n.odd_minima(prob, ev_min, devolucao),
        "ev": n.ev(prob, odd, devolucao),
        "kelly": n.kelly(prob, odd, devolucao),
        "veredito": n.classificar(prob, odd, cfg, devolucao),
        "stake_sugerida": n.stake_sugerida(prob, odd, cfg, devolucao),
    }
    if mercado_odds:
        justas, margem = n.remover_margem(mercado_odds)
        r["margem_casa"] = margem
        if odd in mercado_odds:
            r["prob_casa_sem_margem"] = justas[mercado_odds.index(odd)]
    return r


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--prob", type=float, required=True, help="probabilidade de vitória (0-1 ou 0-100)")
    p.add_argument("--odd", type=float, required=True)
    p.add_argument("--devolucao", type=float, default=0.0, help="probabilidade de devolução (linha asiática)")
    p.add_argument("--mercado-odds", help="todas as odds do mercado, separadas por vírgula")
    p.add_argument("--json", action="store_true")
    a = p.parse_args()

    cfg = n.carregar_config()
    prob = a.prob / 100 if a.prob > 1 else a.prob
    dev = a.devolucao / 100 if a.devolucao > 1 else a.devolucao
    mercado = [float(x) for x in a.mercado_odds.split(",")] if a.mercado_odds else None
    r = avaliar(prob, a.odd, cfg, dev, mercado)

    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return
    crit = cfg["criterios"]
    print(f"Probabilidade estimada: {n.pct(prob)}" + (f" (+{n.pct(dev)} devolução)" if dev else ""))
    print(f"Odd da casa: {a.odd:.2f} → probabilidade implícita {n.pct(r['prob_implicita'])}")
    if "margem_casa" in r:
        print(f"Margem da casa no mercado: {n.pct(r['margem_casa'])}")
        if "prob_casa_sem_margem" in r:
            print(f"Probabilidade da casa sem margem: {n.pct(r['prob_casa_sem_margem'])}")
    print(f"Odd justa: {n.fmt_odd(r['odd_justa'])} | odd mínima p/ EV ≥ {crit['ev_minimo'] * 100:.0f}%: "
          f"{n.fmt_odd(r['odd_minima'])}")
    print(f"EV: {r['ev'] * 100:+.1f}% | Kelly cheio: {max(0.0, r['kelly']) * 100:.1f}% da banca")
    if r["stake_sugerida"]:
        print(f"Stake sugerida (Kelly {cfg['banca']['kelly_fracao']:.0%}, teto "
              f"{cfg['banca']['stake_max_pct']:.0%}): R$ {r['stake_sugerida']:.2f}")
    v = r["veredito"]
    print()
    if v == "OURO":
        print("⭐ OPORTUNIDADE DE OURO — probabilidade e valor dentro do critério.")
    elif v == "valor marginal":
        print("Valor marginal — EV positivo, mas abaixo do mínimo. Não entra.")
    elif v == "abaixo do corte":
        print(f"Abaixo do corte de {n.pct(crit['prob_minima'])}. Não entra.")
    else:
        print(f"Sem valor nesta odd. Só entraria a partir de {n.fmt_odd(r['odd_minima'])}.")


if __name__ == "__main__":
    main()
