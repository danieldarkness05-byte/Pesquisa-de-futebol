"""Funções matemáticas e utilidades compartilhadas pelas ferramentas.

Tudo aqui usa só a biblioteca padrão do Python, para rodar em qualquer
máquina (ou sessão do Claude Code na nuvem) sem instalar nada.
"""
from __future__ import annotations

import json
import math
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

CONFIG_PADRAO: dict = {
    "criterios": {"prob_minima": 0.60, "ev_minimo": 0.03},
    "banca": {"valor_banca": 0, "kelly_fracao": 0.25, "stake_max_pct": 0.02},
    "chuva": {
        "janela": "dia",
        "prob_limiar": 50,
        "mm_limiar": 1.0,
        "horas_antes": 1,
        "horas_depois": 3,
    },
    "modelos": {
        "duracao_partida_min": 95,
        "rho_dixon_coles": 0.0,
        "peso_arbitro_cartoes": 0.5,
        "dispersao_padrao": {"escanteios": 1.0, "cartoes": 1.0, "chutes": 1.0},
    },
}


def _mesclar(base: dict, extra: dict) -> dict:
    saida = dict(base)
    for chave, valor in extra.items():
        if chave.startswith("_"):
            continue
        if isinstance(valor, dict) and isinstance(saida.get(chave), dict):
            saida[chave] = _mesclar(saida[chave], valor)
        else:
            saida[chave] = valor
    return saida


def carregar_config(caminho: Path | None = None) -> dict:
    caminho = caminho or (RAIZ / "config.json")
    if caminho.exists():
        with open(caminho, encoding="utf-8") as f:
            return _mesclar(CONFIG_PADRAO, json.load(f))
    return json.loads(json.dumps(CONFIG_PADRAO))


# ---------------------------------------------------------------------------
# Distribuições
# ---------------------------------------------------------------------------

def poisson_pmf(k: int, media: float) -> float:
    if k < 0:
        return 0.0
    if media <= 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-media + k * math.log(media) - math.lgamma(k + 1))


def negbin_pmf(k: int, media: float, dispersao: float) -> float:
    """Binomial negativa com média `media` e variância `dispersao * media`.

    Com dispersão <= 1 cai na Poisson (a binomial negativa não representa
    variância menor que a média).
    """
    if dispersao <= 1.0 + 1e-9 or media <= 0:
        return poisson_pmf(k, media)
    if k < 0:
        return 0.0
    r = media / (dispersao - 1.0)
    p = 1.0 / dispersao
    return math.exp(
        math.lgamma(k + r) - math.lgamma(r) - math.lgamma(k + 1)
        + r * math.log(p) + k * math.log(1.0 - p)
    )


def pmf(k: int, media: float, dispersao: float = 1.0) -> float:
    return negbin_pmf(k, media, dispersao)


def cdf(k: int, media: float, dispersao: float = 1.0) -> float:
    """P(N <= k)."""
    if k < 0:
        return 0.0
    return min(1.0, sum(pmf(i, media, dispersao) for i in range(k + 1)))


def prob_linha(media: float, linha: float, lado: str, dispersao: float = 1.0,
               asiatica: bool = True) -> dict:
    """Probabilidades de vitória/devolução/derrota para over/under de uma linha.

    Linha .5 (ex.: 2.5): sem devolução.
    Linha inteira (ex.: 2): se `asiatica`, o valor exato devolve a aposta;
    senão "menos de 2" = N <= 1 e "mais de 2" = N >= 3.
    """
    lado = lado.lower()
    if lado not in ("over", "under"):
        raise ValueError("lado deve ser 'over' ou 'under'")
    inteira = abs(linha - round(linha)) < 1e-9
    if not inteira:
        corte = math.floor(linha)
        p_under = cdf(corte, media, dispersao)
        p_win = p_under if lado == "under" else 1.0 - p_under
        return {"vitoria": p_win, "devolucao": 0.0, "derrota": 1.0 - p_win}
    n = int(round(linha))
    p_menor = cdf(n - 1, media, dispersao)
    p_igual = pmf(n, media, dispersao)
    p_maior = 1.0 - p_menor - p_igual
    if asiatica:
        if lado == "under":
            return {"vitoria": p_menor, "devolucao": p_igual, "derrota": p_maior}
        return {"vitoria": p_maior, "devolucao": p_igual, "derrota": p_menor}
    if lado == "under":
        return {"vitoria": p_menor, "devolucao": 0.0, "derrota": 1.0 - p_menor}
    return {"vitoria": p_maior, "devolucao": 0.0, "derrota": 1.0 - p_maior}


# ---------------------------------------------------------------------------
# Gols (Poisson bivariada independente + ajuste opcional de Dixon-Coles)
# ---------------------------------------------------------------------------

def lambdas_por_medias(casa_marcados: float, casa_sofridos: float,
                       fora_marcados: float, fora_sofridos: float,
                       liga_gols_mandante: float | None = None,
                       liga_gols_visitante: float | None = None) -> tuple[float, float]:
    """Gols esperados do mandante e do visitante.

    casa_*  = médias do mandante jogando EM CASA.
    fora_*  = médias do visitante jogando FORA.
    Com as médias da liga, usa o método de força (ataque x defesa x média);
    sem elas, faz a média simples entre ataque de um e defesa do outro.
    """
    if liga_gols_mandante and liga_gols_visitante:
        lc = casa_marcados * fora_sofridos / liga_gols_mandante
        lf = fora_marcados * casa_sofridos / liga_gols_visitante
    else:
        lc = (casa_marcados + fora_sofridos) / 2.0
        lf = (fora_marcados + casa_sofridos) / 2.0
    return lc, lf


def matriz_placar(lc: float, lf: float, rho: float = 0.0, max_gols: int = 10) -> list[list[float]]:
    m = [[poisson_pmf(i, lc) * poisson_pmf(j, lf) for j in range(max_gols + 1)]
         for i in range(max_gols + 1)]
    if rho:
        m[0][0] *= max(0.0, 1 - lc * lf * rho)
        m[0][1] *= max(0.0, 1 + lc * rho)
        m[1][0] *= max(0.0, 1 + lf * rho)
        m[1][1] *= max(0.0, 1 - rho)
    total = sum(sum(linha) for linha in m)
    return [[v / total for v in linha] for linha in m]


def mercados_gols(lc: float, lf: float, rho: float = 0.0) -> dict[str, float]:
    m = matriz_placar(lc, lf, rho)
    n = len(m)
    res: dict[str, float] = {}
    p1 = sum(m[i][j] for i in range(n) for j in range(n) if i > j)
    px = sum(m[i][i] for i in range(n))
    p2 = 1.0 - p1 - px
    res.update({"1": p1, "X": px, "2": p2, "1X": p1 + px, "X2": px + p2, "12": p1 + p2})
    sem_gol_casa = sum(m[0][j] for j in range(n))
    sem_gol_fora = sum(m[i][0] for i in range(n))
    ambas_nao = sem_gol_casa + sem_gol_fora - m[0][0]
    res["ambas_sim"] = 1.0 - ambas_nao
    res["ambas_nao"] = ambas_nao
    for linha in (0.5, 1.5, 2.5, 3.5, 4.5):
        under = sum(m[i][j] for i in range(n) for j in range(n) if i + j <= linha)
        res[f"under{linha}"] = under
        res[f"over{linha}"] = 1.0 - under
    for linha in (0.5, 1.5, 2.5):
        cu = sum(m[i][j] for i in range(n) for j in range(n) if i <= linha)
        fu = sum(m[i][j] for i in range(n) for j in range(n) if j <= linha)
        res[f"casa_under{linha}"] = cu
        res[f"casa_over{linha}"] = 1.0 - cu
        res[f"fora_under{linha}"] = fu
        res[f"fora_over{linha}"] = 1.0 - fu
    return res


def placares_provaveis(lc: float, lf: float, rho: float = 0.0, top: int = 5) -> list[tuple[str, float]]:
    m = matriz_placar(lc, lf, rho)
    itens = [(f"{i}x{j}", m[i][j]) for i in range(len(m)) for j in range(len(m))]
    return sorted(itens, key=lambda x: -x[1])[:top]


# ---------------------------------------------------------------------------
# Contagens (escanteios, cartões, chutes)
# ---------------------------------------------------------------------------

def media_confronto(casa_favor: float, casa_contra: float,
                    fora_favor: float, fora_contra: float) -> tuple[float, float, float]:
    """Média esperada do jogo a partir de "a favor" e "contra" de cada time.

    Retorna (total, do mandante, do visitante).
    """
    mandante = (casa_favor + fora_contra) / 2.0
    visitante = (fora_favor + casa_contra) / 2.0
    return mandante + visitante, mandante, visitante


def estimar_amostra(valores: list[float]) -> tuple[float, float]:
    """Média e dispersão (variância / média) de uma amostra de jogos."""
    if not valores:
        raise ValueError("amostra vazia")
    n = len(valores)
    media = sum(valores) / n
    if n < 2 or media <= 0:
        return media, 1.0
    var = sum((v - media) ** 2 for v in valores) / (n - 1)
    return media, var / media


def escalar_janela(media_jogo: float, minutos: float, duracao: float = 95.0,
                   fator: float = 1.0) -> float:
    """Média esperada num trecho do jogo (ex.: primeiros 10 minutos)."""
    return media_jogo * (minutos / duracao) * fator


# ---------------------------------------------------------------------------
# Valor esperado e banca
# ---------------------------------------------------------------------------

def ev(p_vitoria: float, odd: float, p_devolucao: float = 0.0) -> float:
    """Lucro esperado por unidade apostada."""
    p_derrota = 1.0 - p_vitoria - p_devolucao
    return p_vitoria * (odd - 1.0) - p_derrota


def odd_justa(p_vitoria: float, p_devolucao: float = 0.0) -> float:
    if p_vitoria <= 0:
        return float("inf")
    return 1.0 + (1.0 - p_vitoria - p_devolucao) / p_vitoria


def odd_minima(p_vitoria: float, ev_min: float, p_devolucao: float = 0.0) -> float:
    """Menor odd que entrega EV >= ev_min."""
    if p_vitoria <= 0:
        return float("inf")
    return 1.0 + (ev_min + 1.0 - p_vitoria - p_devolucao) / p_vitoria


def kelly(p_vitoria: float, odd: float, p_devolucao: float = 0.0) -> float:
    """Fração de Kelly (cheia). Negativa = não apostar."""
    b = odd - 1.0
    q = 1.0 - p_vitoria - p_devolucao
    if b <= 0 or (p_vitoria + q) <= 0:
        return 0.0
    return (p_vitoria * b - q) / (b * (p_vitoria + q))


def remover_margem(odds: list[float]) -> tuple[list[float], float]:
    """Probabilidades sem a margem da casa (método proporcional) e a margem."""
    inv = [1.0 / o for o in odds]
    soma = sum(inv)
    return [x / soma for x in inv], soma - 1.0


def classificar(p_vitoria: float, odd: float | None, cfg: dict,
                p_devolucao: float = 0.0) -> str:
    crit = cfg["criterios"]
    if p_vitoria < crit["prob_minima"]:
        return "abaixo do corte"
    if odd is None:
        return "sem odd"
    valor = ev(p_vitoria, odd, p_devolucao)
    if valor >= crit["ev_minimo"]:
        return "OURO"
    if valor > 0:
        return "valor marginal"
    return "sem valor"


def stake_sugerida(p_vitoria: float, odd: float, cfg: dict, p_devolucao: float = 0.0) -> float:
    """Stake em R$ (0 se a banca não estiver configurada ou não houver valor)."""
    banca = cfg["banca"]
    valor_banca = float(banca.get("valor_banca") or 0)
    f = kelly(p_vitoria, odd, p_devolucao) * float(banca["kelly_fracao"])
    if valor_banca <= 0 or f <= 0:
        return 0.0
    return round(min(f, float(banca["stake_max_pct"])) * valor_banca, 2)


# ---------------------------------------------------------------------------
# Texto
# ---------------------------------------------------------------------------

def normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return " ".join(sem_acento.lower().replace("-", " ").split())


def pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def fmt_odd(x: float) -> str:
    return "—" if x == float("inf") else f"{x:.2f}"


def odd_acima(x: float) -> float:
    """Odd mínima com 2 casas, sempre para cima: 1.585 vira 1.59 (com 1.58 o EV não chega ao mínimo)."""
    return x if x == float("inf") else math.ceil(x * 100 - 1e-9) / 100


def fmt_odd_min(x: float) -> str:
    return fmt_odd(odd_acima(x))


def tabela(cabecalho: list[str], linhas: list[list[str]]) -> str:
    """Tabela em Markdown (fica legível no terminal e no app)."""
    out = ["| " + " | ".join(cabecalho) + " |",
           "|" + "|".join("---" for _ in cabecalho) + "|"]
    out += ["| " + " | ".join(str(c) for c in linha) + " |" for linha in linhas]
    return "\n".join(out)


def parse_odds(texto: str | None) -> dict[str, float]:
    """'under2.5=1.80,ambas_nao=1.95' -> {'under2.5': 1.8, 'ambas_nao': 1.95}"""
    if not texto:
        return {}
    saida = {}
    for par in texto.split(","):
        par = par.strip()
        if not par:
            continue
        chave, _, valor = par.partition("=")
        saida[chave.strip()] = float(valor.replace(",", ".").strip())
    return saida
