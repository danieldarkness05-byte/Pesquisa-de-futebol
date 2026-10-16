#!/usr/bin/env python3
"""Probabilidades por mercado e comparação com as odds da casa.

Exemplos:
  # Gols a partir dos gols esperados (xG ou médias já combinadas)
  python3 ferramentas/prob.py gols --xg-casa 1.35 --xg-fora 0.95 --odds "under2.5=1.72,ambas_nao=1.90"

  # Gols a partir das médias (mandante em casa / visitante fora) + médias da liga
  python3 ferramentas/prob.py gols --casa-marcados 1.6 --casa-sofridos 0.9 \
      --fora-marcados 0.8 --fora-sofridos 1.4 --liga-mandante 1.35 --liga-visitante 1.0

  # Escanteios no jogo inteiro
  python3 ferramentas/prob.py contagem --mercado escanteios --casa-favor 6.1 \
      --casa-contra 4.2 --fora-favor 4.5 --fora-contra 5.8 --linhas 8.5,9.5,10.5

  # Escanteios nos primeiros 10 minutos (menos de 2 = under 1.5)
  python3 ferramentas/prob.py contagem --mercado escanteios --media 9.8 --minutos 10 --linhas 1.5 --odds "under1.5=1.40"

  # Cartões combinando times + árbitro
  python3 ferramentas/prob.py contagem --mercado cartoes --casa-favor 2.3 --casa-contra 2.0 \
      --fora-favor 2.6 --fora-contra 2.1 --arbitro 5.4 --linhas 3.5,4.5,5.5

  # Média e dispersão estimadas de uma amostra de jogos
  python3 ferramentas/prob.py contagem --mercado chutes --amostra "22,25,19,28,24,21,30,18"
"""
from __future__ import annotations

import argparse
import json
import math
import sys

import nucleo as n

NOMES_GOLS = {
    "1": "Vitória mandante (1)", "X": "Empate (X)", "2": "Vitória visitante (2)",
    "1X": "Dupla chance 1X", "X2": "Dupla chance X2", "12": "Dupla chance 12",
    "ambas_sim": "Ambas marcam: sim", "ambas_nao": "Ambas marcam: não",
}
PADRAO_GOLS = ["1", "X", "2", "1X", "X2", "ambas_sim", "ambas_nao",
               "over1.5", "under1.5", "over2.5", "under2.5", "over3.5", "under3.5",
               "casa_over0.5", "fora_over0.5", "casa_under1.5", "fora_under1.5"]


def nome_mercado(chave: str) -> str:
    if chave in NOMES_GOLS:
        return NOMES_GOLS[chave]
    for prefixo, rotulo in (("casa_", "Mandante "), ("fora_", "Visitante "), ("", "Total ")):
        if chave.startswith(prefixo + "over") or chave.startswith(prefixo + "under"):
            resto = chave[len(prefixo):]
            lado = "mais de" if resto.startswith("over") else "menos de"
            linha = resto.replace("over", "").replace("under", "")
            return f"{rotulo}{lado} {linha}".strip()
    return chave


def linhas_saida(itens: list[dict], cfg: dict) -> tuple[list[list[str]], list[dict]]:
    ev_min = cfg["criterios"]["ev_minimo"]
    tabela, dados = [], []
    for it in itens:
        p, pd = it["vitoria"], it.get("devolucao", 0.0)
        odd = it.get("odd")
        veredito = n.classificar(p, odd, cfg, pd)
        valor = n.ev(p, odd, pd) if odd else None
        registro = {
            "mercado": it["chave"], "nome": it["nome"], "prob": round(p, 4),
            "devolucao": round(pd, 4), "odd_justa": round(n.odd_justa(p, pd), 3),
            "odd_minima": round(n.odd_minima(p, ev_min, pd), 3),
            "odd_casa": odd, "ev": None if valor is None else round(valor, 6),
            "veredito": veredito,
        }
        if odd and veredito == "OURO":
            registro["stake_sugerida"] = n.stake_sugerida(p, odd, cfg, pd)
        dados.append(registro)
        marca = "⭐ OURO" if veredito == "OURO" else veredito
        prob_txt = n.pct(p) + (f" (+{n.pct(pd)} dev.)" if pd > 0.0005 else "")
        tabela.append([
            it["nome"], prob_txt, n.fmt_odd(n.odd_justa(p, pd)),
            n.fmt_odd_min(n.odd_minima(p, ev_min, pd)),
            f"{odd:.2f}" if odd else "—",
            "—" if valor is None else f"{valor * 100:+.1f}%", marca,
        ])
    return tabela, dados


def imprimir(titulo: str, contexto: list[str], itens: list[dict], cfg: dict, como_json: bool,
             extra: dict | None = None) -> None:
    tabela, dados = linhas_saida(itens, cfg)
    if como_json:
        print(json.dumps({"titulo": titulo, "contexto": contexto, "mercados": dados,
                          **(extra or {})}, ensure_ascii=False, indent=2))
        return
    crit = cfg["criterios"]
    print(f"## {titulo}\n")
    for c in contexto:
        print(f"- {c}")
    print(f"- Critério: prob ≥ {n.pct(crit['prob_minima'])} e EV ≥ {crit['ev_minimo'] * 100:.0f}%\n")
    print(n.tabela(["Mercado", "Prob.", "Odd justa", f"Odd mín. (EV {crit['ev_minimo'] * 100:.0f}%)",
                    "Odd casa", "EV", "Veredito"], tabela))
    ouros = [d for d in dados if d["veredito"] == "OURO"]
    print()
    if ouros:
        for d in ouros:
            stake = d.get("stake_sugerida")
            txt = f" — stake sugerida R$ {stake:.2f}" if stake else ""
            print(f"⭐ {d['nome']}: {n.pct(d['prob'])} @ {d['odd_casa']:.2f} (EV {d['ev'] * 100:+.1f}%){txt}")
    else:
        print("Nenhuma oportunidade de ouro com as odds informadas. Não force entrada.")
    faltam = [d for d in dados if d["veredito"] == "sem odd"]
    if faltam:
        print("\nAcima do corte, falta conferir a odd na casa (só entra se for ≥ a odd mínima):")
        for d in faltam:
            print(f"- {d['nome']}: {n.pct(d['prob'])} → odd mínima {n.fmt_odd_min(d['odd_minima'])}")


def cmd_gols(a: argparse.Namespace, cfg: dict) -> None:
    if a.xg_casa is not None and a.xg_fora is not None:
        lc, lf = a.xg_casa, a.xg_fora
        origem = "gols esperados informados"
    else:
        req = [a.casa_marcados, a.casa_sofridos, a.fora_marcados, a.fora_sofridos]
        if any(v is None for v in req):
            sys.exit("Informe --xg-casa/--xg-fora OU as quatro médias "
                     "(--casa-marcados --casa-sofridos --fora-marcados --fora-sofridos).")
        lc, lf = n.lambdas_por_medias(*req, a.liga_mandante, a.liga_visitante)
        origem = ("método de força (médias da liga)" if a.liga_mandante and a.liga_visitante
                  else "média simples ataque × defesa")
    rho = cfg["modelos"]["rho_dixon_coles"] if a.rho is None else a.rho
    probs = n.mercados_gols(lc, lf, rho)
    odds = n.parse_odds(a.odds)
    chaves = a.mercados.split(",") if a.mercados else list(PADRAO_GOLS)
    for c in odds:
        if c not in chaves:
            chaves.append(c)
    desconhecidas = [c for c in chaves if c not in probs]
    if desconhecidas:
        sys.exit(f"Mercado(s) desconhecido(s): {', '.join(desconhecidas)}. "
                 f"Disponíveis: {', '.join(sorted(probs))}")
    itens = [{"chave": c, "nome": nome_mercado(c), "vitoria": probs[c], "odd": odds.get(c)}
             for c in chaves]
    placares = n.placares_provaveis(lc, lf, rho)
    contexto = [
        f"Gols esperados: mandante {lc:.2f} × visitante {lf:.2f} (total {lc + lf:.2f}) — {origem}",
        "Placares mais prováveis: " + ", ".join(f"{s} ({n.pct(p)})" for s, p in placares),
    ]
    if rho:
        contexto.append(f"Ajuste Dixon-Coles rho = {rho}")
    imprimir(a.titulo or "Mercados de gols", contexto, itens, cfg, a.json,
             {"lambda_casa": round(lc, 3), "lambda_fora": round(lf, 3)})


def cmd_contagem(a: argparse.Namespace, cfg: dict) -> None:
    contexto = []
    dispersao = a.dispersao
    if a.amostra:
        valores = [float(x) for x in a.amostra.replace(";", ",").split(",") if x.strip()]
        media, disp_amostra = n.estimar_amostra(valores)
        if dispersao is None:
            dispersao = max(1.0, disp_amostra)
        contexto.append(f"Amostra de {len(valores)} jogos: média {media:.2f}, "
                        f"dispersão observada {disp_amostra:.2f}")
    elif a.media is not None:
        media = a.media
    else:
        req = [a.casa_favor, a.casa_contra, a.fora_favor, a.fora_contra]
        if any(v is None for v in req):
            sys.exit("Informe --media, --amostra, ou as quatro médias "
                     "(--casa-favor --casa-contra --fora-favor --fora-contra).")
        media, m_casa, m_fora = n.media_confronto(*req)
        contexto.append(f"Pelos times: mandante {m_casa:.2f} + visitante {m_fora:.2f} = {media:.2f}")
    if a.arbitro is not None:
        peso = cfg["modelos"]["peso_arbitro_cartoes"] if a.peso_arbitro is None else a.peso_arbitro
        media_times = media
        media = (1 - peso) * media_times + peso * a.arbitro
        contexto.append(f"Árbitro {a.arbitro:.2f}/jogo com peso {peso:.0%} → média ajustada {media:.2f}")
    if dispersao is None:
        dispersao = cfg["modelos"]["dispersao_padrao"].get(a.mercado, 1.0)
    media_jogo = media
    if a.minutos:
        duracao = cfg["modelos"]["duracao_partida_min"]
        media = n.escalar_janela(media_jogo, a.minutos, duracao, a.fator)
        contexto.append(f"Janela de {a.minutos:g} min (de ~{duracao} jogados, fator {a.fator:g}): "
                        f"média esperada {media:.2f}")
    contexto.append(f"Modelo: {'Poisson' if dispersao <= 1.0 else f'binomial negativa (dispersão {dispersao:.2f})'}")

    if a.linhas:
        linhas = [float(x) for x in a.linhas.split(",") if x.strip()]
    else:
        base = math.floor(media)
        linhas = [x + 0.5 for x in range(max(0, base - 2), base + 2)]
    odds = n.parse_odds(a.odds)
    lados = ["under", "over"] if a.lado == "ambos" else [a.lado]
    itens = []
    rotulo = {"escanteios": "escanteios", "cartoes": "cartões", "chutes": "chutes"}.get(a.mercado, a.mercado)
    janela = f" ({a.minutos:g} min)" if a.minutos else ""
    for linha in linhas:
        for lado in lados:
            r = n.prob_linha(media, linha, lado, dispersao, asiatica=not a.sem_devolucao)
            chave = f"{lado}{linha:g}"
            itens.append({
                "chave": chave,
                "nome": f"{'Menos' if lado == 'under' else 'Mais'} de {linha:g} {rotulo}{janela}",
                "vitoria": r["vitoria"], "devolucao": r["devolucao"],
                "odd": odds.get(chave) or odds.get(f"{lado}{linha}"),
            })
    titulo = a.titulo or f"Mercado de {rotulo}{janela}"
    imprimir(titulo, contexto, itens, cfg, a.json,
             {"media": round(media, 3), "dispersao": round(dispersao, 3)})


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("gols", help="1X2, dupla chance, ambas marcam, over/under de gols")
    g.add_argument("--xg-casa", type=float)
    g.add_argument("--xg-fora", type=float)
    g.add_argument("--casa-marcados", type=float, help="gols marcados pelo mandante em casa (média)")
    g.add_argument("--casa-sofridos", type=float, help="gols sofridos pelo mandante em casa (média)")
    g.add_argument("--fora-marcados", type=float, help="gols marcados pelo visitante fora (média)")
    g.add_argument("--fora-sofridos", type=float, help="gols sofridos pelo visitante fora (média)")
    g.add_argument("--liga-mandante", type=float, help="média de gols dos mandantes na liga")
    g.add_argument("--liga-visitante", type=float, help="média de gols dos visitantes na liga")
    g.add_argument("--rho", type=float, help="ajuste Dixon-Coles (ex.: -0.05)")
    g.add_argument("--mercados", help="lista separada por vírgula (padrão: principais)")
    g.add_argument("--odds", help='ex.: "under2.5=1.72,ambas_nao=1.90" (use ponto decimal)')
    g.add_argument("--titulo")
    g.add_argument("--json", action="store_true")

    c = sub.add_parser("contagem", help="escanteios, cartões, chutes (jogo inteiro ou janela)")
    c.add_argument("--mercado", default="escanteios", help="escanteios | cartoes | chutes | outro")
    c.add_argument("--media", type=float, help="média total esperada no jogo")
    c.add_argument("--amostra", help="valores por jogo separados por vírgula")
    c.add_argument("--casa-favor", type=float)
    c.add_argument("--casa-contra", type=float)
    c.add_argument("--fora-favor", type=float)
    c.add_argument("--fora-contra", type=float)
    c.add_argument("--arbitro", type=float, help="média do árbitro por jogo (cartões)")
    c.add_argument("--peso-arbitro", type=float)
    c.add_argument("--dispersao", type=float, help="variância/média (1 = Poisson)")
    c.add_argument("--minutos", type=float, help="janela do início do jogo, ex.: 10")
    c.add_argument("--fator", type=float, default=1.0, help="ajuste do ritmo na janela (padrão 1.0)")
    c.add_argument("--linhas", help="ex.: 8.5,9.5,10.5")
    c.add_argument("--lado", default="ambos", choices=["under", "over", "ambos"])
    c.add_argument("--sem-devolucao", action="store_true",
                   help="linha inteira sem devolução ('menos de 2' = 0 ou 1)")
    c.add_argument("--odds", help='ex.: "under9.5=1.85,over9.5=1.95"')
    c.add_argument("--titulo")
    c.add_argument("--json", action="store_true")

    a = p.parse_args()
    cfg = n.carregar_config()
    if a.cmd == "gols":
        cmd_gols(a, cfg)
    else:
        cmd_contagem(a, cfg)


if __name__ == "__main__":
    main()
