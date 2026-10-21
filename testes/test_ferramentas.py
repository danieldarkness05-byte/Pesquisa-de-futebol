"""Testes das ferramentas. Rode com:  python3 -m unittest discover testes"""
import math
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ferramentas"))

import clima  # noqa: E402
import azarao as azr  # noqa: E402
import defesa as df  # noqa: E402
import dossie  # noqa: E402
import historico  # noqa: E402
import nucleo as n  # noqa: E402
import plataformas as pl  # noqa: E402
import previsoes  # noqa: E402
import registro  # noqa: E402
import sistema  # noqa: E402
import under as und  # noqa: E402
import varredura as vr  # noqa: E402

CFG = n.carregar_config()


class TestDistribuicoes(unittest.TestCase):
    def test_poisson_soma_um(self):
        self.assertAlmostEqual(sum(n.poisson_pmf(k, 2.7) for k in range(60)), 1.0, places=9)

    def test_negbin_media_e_variancia(self):
        media, disp = 9.5, 1.4
        ps = [n.negbin_pmf(k, media, disp) for k in range(200)]
        m = sum(k * p for k, p in enumerate(ps))
        v = sum((k - m) ** 2 * p for k, p in enumerate(ps))
        self.assertAlmostEqual(sum(ps), 1.0, places=6)
        self.assertAlmostEqual(m, media, places=4)
        self.assertAlmostEqual(v / m, disp, places=3)

    def test_under_2_5_poisson(self):
        lam = 2.5
        esperado = sum(math.exp(-lam) * lam ** k / math.factorial(k) for k in range(3))
        self.assertAlmostEqual(n.prob_linha(lam, 2.5, "under")["vitoria"], esperado, places=9)

    def test_linha_inteira_asiatica(self):
        r = n.prob_linha(1.0, 2, "under")
        self.assertAlmostEqual(r["vitoria"] + r["devolucao"] + r["derrota"], 1.0, places=9)
        self.assertAlmostEqual(r["devolucao"], n.poisson_pmf(2, 1.0), places=9)
        sem = n.prob_linha(1.0, 2, "under", asiatica=False)
        self.assertAlmostEqual(sem["vitoria"], n.cdf(1, 1.0), places=9)

    def test_janela_10_minutos(self):
        media = n.escalar_janela(9.5, 10, 95)
        self.assertAlmostEqual(media, 1.0)
        self.assertAlmostEqual(n.prob_linha(media, 1.5, "under")["vitoria"], 2 * math.exp(-1), places=9)


class TestGols(unittest.TestCase):
    def test_mercados_consistentes(self):
        m = n.mercados_gols(1.4, 1.1)
        self.assertAlmostEqual(m["1"] + m["X"] + m["2"], 1.0, places=9)
        self.assertAlmostEqual(m["ambas_sim"] + m["ambas_nao"], 1.0, places=9)
        self.assertAlmostEqual(m["under2.5"], n.prob_linha(2.5, 2.5, "under")["vitoria"], places=6)

    def test_dixon_coles_aumenta_empates_baixos(self):
        sem = n.mercados_gols(1.2, 1.0, 0.0)["X"]
        com = n.mercados_gols(1.2, 1.0, -0.1)["X"]
        self.assertGreater(com, sem)

    def test_lambdas(self):
        self.assertEqual(n.lambdas_por_medias(2, 1, 1, 2), (2.0, 1.0))
        lc, lf = n.lambdas_por_medias(1.8, 0.8, 1.0, 1.5, 1.5, 1.0)
        self.assertAlmostEqual(lc, 1.8 * 1.5 / 1.5)
        self.assertAlmostEqual(lf, 1.0 * 0.8 / 1.0)


class TestValor(unittest.TestCase):
    def test_ev_e_odds(self):
        self.assertAlmostEqual(n.ev(0.6, 2.0), 0.2)
        self.assertAlmostEqual(n.odd_justa(0.5), 2.0)
        self.assertAlmostEqual(n.ev(0.62, n.odd_minima(0.62, 0.03)), 0.03, places=9)

    def test_kelly(self):
        self.assertAlmostEqual(n.kelly(0.6, 2.0), 0.2)
        self.assertLess(n.kelly(0.4, 2.0), 0)

    def test_classificacao(self):
        self.assertEqual(n.classificar(0.66, 1.70, CFG), "OURO")
        self.assertEqual(n.classificar(0.66, 1.53, CFG), "valor marginal")
        self.assertEqual(n.classificar(0.66, 1.45, CFG), "sem valor")
        self.assertEqual(n.classificar(0.55, 3.00, CFG), "abaixo do corte")

    def test_remover_margem(self):
        probs, margem = n.remover_margem([1.90, 1.90])
        self.assertAlmostEqual(probs[0], 0.5)
        self.assertAlmostEqual(margem, 2 / 1.9 - 1)


class TestSistema(unittest.TestCase):
    def test_duplas_tres_selecoes(self):
        sels = [{"rotulo": c, "jogo": c, "odd": 2.0, "prob": 0.5} for c in "ABC"]
        r = sistema.simular(sels, [2], 1.0)
        self.assertEqual(r["combinacoes"], 3)
        # EV de cada dupla = 0.25 * 4 - 1 = 0
        self.assertAlmostEqual(r["ev"], 0.0, places=9)
        # lucro só com 2 ou 3 acertos (2 acertos devolvem 4 > 3)
        self.assertAlmostEqual(r["p_lucro"], 0.5, places=9)

    def test_avisa_jogo_repetido(self):
        sels = [{"rotulo": "a", "jogo": "X x Y", "odd": 1.8, "prob": 0.6},
                {"rotulo": "b", "jogo": "x x y", "odd": 1.8, "prob": 0.6}]
        self.assertEqual(sistema.simular(sels, [2], 1.0)["jogos_repetidos"], ["X x Y"])


class TestClima(unittest.TestCase):
    def previsao(self, probs, mms):
        horas = [f"2026-10-12T{h:02d}:00" for h in range(24)]
        return {"hourly": {"time": horas, "precipitation_probability": probs, "precipitation": mms}}

    def test_chuva_de_manha_conta_no_dia_mas_nao_no_jogo(self):
        probs = [0] * 24
        mms = [0.0] * 24
        probs[7], mms[7] = 80, 2.0
        prev = self.previsao(probs, mms)
        inicio = datetime(2026, 10, 12, 19, 0)
        self.assertTrue(clima.avaliar_chuva(prev, inicio, CFG, "dia")["chuva"])
        self.assertFalse(clima.avaliar_chuva(prev, inicio, CFG, "jogo")["chuva"])

    def test_sem_chuva(self):
        prev = self.previsao([10] * 24, [0.0] * 24)
        self.assertFalse(clima.avaliar_chuva(prev, datetime(2026, 10, 12, 16), CFG)["chuva"])


class TestHistorico(unittest.TestCase):
    CSV = ("Country,League,Season,Date,Time,Home,Away,HG,AG,Res\n"
           "Brazil,Serie A,2026,01/04/2026,16:00,Bahia,Vitoria,2,0,H\n"
           "Brazil,Serie A,2026,08/04/2026,16:00,Vitoria,Bahia,1,1,D\n"
           "Brazil,Serie A,2025,08/04/2025,16:00,Vitoria,Bahia,3,1,H\n"
           "Brazil,Serie A,2026,15/04/2026,16:00,Bahia,Sport,,,\n")

    def test_le_e_calcula(self):
        jogos = historico.ler_jogos(self.CSV, "2026")
        self.assertEqual(len(jogos), 2)
        m = historico.medias(jogos)
        self.assertEqual(m["Bahia"]["casa_marcados"], 2.0)
        self.assertEqual(m["Bahia"]["fora_sofridos"], 1.0)
        self.assertEqual(historico.achar_time("vitória", list(m)), "Vitoria")


class TestRegistro(unittest.TestCase):
    def test_fluxo_completo(self):
        with tempfile.TemporaryDirectory() as d:
            arq = Path(d) / "r.csv"
            linhas = registro.ler(arq)
            registro.adicionar(linhas, jogo="A x B", mercado="Gols", selecao="Under 2.5", tipo="simples",
                               odd="1.80", prob_estimada="0.65", stake="10.00")
            registro.adicionar(linhas, jogo="C x D", mercado="Gols", selecao="Under 2.5", tipo="simples",
                               odd="1.70", prob_estimada="0.62", stake="10.00")
            registro.resolver(linhas[0], "green", None, 1.70)
            registro.resolver(linhas[1], "red", None)
            registro.salvar(linhas, arq)
            de_novo = registro.ler(arq)
            self.assertEqual(de_novo[0]["lucro"], "8.00")
            self.assertEqual(de_novo[1]["lucro"], "-10.00")
            txt = registro.resumo(de_novo)
            self.assertIn("Acerto: 1/2", txt)
            self.assertIn("CLV", txt)


class TestDossie(unittest.TestCase):
    def test_selecionar(self):
        cands = [{"x": i} for i in range(5)]
        self.assertEqual([i for i, _ in dossie.selecionar(cands, None, 3)], [1, 2, 3])
        self.assertEqual([i for i, _ in dossie.selecionar(cands, [5, 2, 9], 3)], [5, 2])

    def test_gols_por_jogador_ignora_gol_contra_e_adversario(self):
        inc = [[{"incidentType": "goal", "isHome": True, "player": {"id": 7, "shortName": "A"}},
                {"incidentType": "goal", "isHome": False, "player": {"id": 9, "shortName": "Rival"}},
                {"incidentType": "goal", "isHome": True, "incidentClass": "ownGoal", "player": {"id": 9}},
                {"incidentType": "card", "isHome": True, "player": {"id": 7}}],
               [{"incidentType": "goal", "isHome": False, "player": {"id": 7, "shortName": "A"}}]]
        gols, total, nomes = dossie.gols_por_jogador(inc, [True, False])
        self.assertEqual(total, 3)
        self.assertEqual(gols, {7: 2})
        self.assertEqual(nomes[7], "A")

    def test_odds_escolha(self):
        odds = {"markets": [{"marketName": "Double chance", "choiceGroup": None, "choices": [
            {"name": "X2", "fractionalValue": "4/5", "initialFractionalValue": "1/2"}]}]}
        self.assertEqual(dossie.odds_escolha(odds, ("Double chance", None, "X2")), [1.5, 1.8])
        self.assertIsNone(dossie.odds_escolha(odds, ("Double chance", None, "1X")))

    def test_motivo_queda_regra8(self):
        cfg = dossie.config()
        k = ("Double chance", None, "X2")
        item = {"mercado": "Double chance", "linha": None, "escolha": "X2", "p": 0.65, "dev": 0.0,
                "ev": 0.17, "odd": 1.8, "justa_mercado": 0.53}
        info = {"variantes": {v: {k: dict(item)} for v in ("base", "incerteza", "dixon_coles")},
                "amostras": ([], []), "taxa_base": None}
        motivo, base = dossie.motivo_queda(info, k, cfg)
        self.assertIn("regra 8", motivo)
        self.assertEqual(base["odd"], 1.8)
        self.assertIn("não está mais", dossie.motivo_queda(info, ("Double chance", None, "1X"), cfg)[0])


if __name__ == "__main__":
    unittest.main()


class TestVarredura(unittest.TestCase):
    V = {**vr.VARREDURA_PADRAO}

    def amostra(self, placares):
        return [{"gf": a, "ga": b} for a, b in placares]

    def test_odd_e_dupla_chance_sem_margem(self):
        self.assertAlmostEqual(vr.odd_decimal("9/20"), 1.45)
        dc = vr.sem_margem("Double chance", [1.25, 1.833, 1.286])
        self.assertAlmostEqual(sum(dc), 2.0, places=9)
        self.assertAlmostEqual(sum(vr.sem_margem("Full time", [1.86, 3.5, 3.75])), 1.0, places=9)

    def test_matriz_com_incerteza_soma_um_e_alarga_cauda(self):
        pura = vr.matriz(1.5, 1.2)
        mista = vr.matriz(1.5, 1.2, sigma=0.15)
        self.assertAlmostEqual(sum(map(sum, mista)), 1.0, places=6)
        self.assertGreater(vr.total_gols(mista, 5.5, "over")[0], vr.total_gols(pura, 5.5, "over")[0])

    def test_totais_e_handicap(self):
        m = vr.matriz(1.4, 1.0)
        r = n.mercados_gols(1.4, 1.0)
        self.assertAlmostEqual(vr.total_gols(m, 2.5, "under")[0], r["under2.5"], places=9)
        # handicap 0 = empate anula
        vit, dev = vr.handicap_asiatico(m, 0.0, "casa")
        self.assertAlmostEqual(vit, r["1"], places=9)
        self.assertAlmostEqual(dev, r["X"], places=9)
        # -0.25 = metade em 0 e metade em -0.5
        vit, dev = vr.handicap_asiatico(m, -0.25, "casa")
        self.assertAlmostEqual(vit, r["1"], places=9)
        self.assertAlmostEqual(dev, r["X"] / 2, places=9)
        # +1 do visitante: vence se não perder por 2+, devolve se perder por 1
        vit, dev = vr.handicap_asiatico(m, 1.0, "fora")
        um_gol = sum(m[i][i - 1] for i in range(1, len(m)))
        self.assertAlmostEqual(vit + dev, 1 - (r["1"] - um_gol), places=9)
        self.assertAlmostEqual(dev, um_gol, places=9)

    def test_le_estatisticas_e_linha_do_time(self):
        d = {"statistics": [{"period": "ALL", "groups": [{"statisticsItems": [
            {"key": "expectedGoals", "homeValue": 1.8, "awayValue": 0.6},
            {"key": "yellowCards", "homeValue": 2, "awayValue": 3},
            {"key": "redCards", "homeValue": 0, "awayValue": 1},
            {"key": "cornerKicks", "home": "7", "away": "2"}]}]}]}
        est = vr.ler_estatisticas(d)
        ev = {"startTimestamp": 1, "homeTeam": {"id": 1, "name": "A"}, "awayTeam": {"id": 2, "name": "B"},
              "homeScore": {"normaltime": 2}, "awayScore": {"normaltime": 1}}
        fora = vr.linha_do_time(ev, est, 2)
        self.assertEqual((fora["gf"], fora["ga"]), (1, 2))
        self.assertEqual((fora["xg_f"], fora["xg_a"]), (0.6, 1.8))
        self.assertEqual((fora["cart_f"], fora["cart_a"]), (4, 2))
        self.assertEqual((fora["esc_f"], fora["esc_a"]), (2.0, 7.0))

    def test_frequencia(self):
        xh = self.amostra([(2, 1), (0, 0), (3, 2)])   # mandante em casa
        xa = self.amostra([(1, 1), (0, 2), (2, 0)])   # visitante fora (gf = do visitante)
        under = {"mercado": "Match goals", "linha": "3.5", "escolha": "Under"}
        self.assertAlmostEqual(vr.frequencia(under, xh, xa), 5 / 6)
        um_x = {"mercado": "Double chance", "linha": None, "escolha": "1X"}
        # casa: V, E, V | visitante fora: E, D (vitória do mandante), V (do visitante)
        self.assertAlmostEqual(vr.frequencia(um_x, xh, xa), 5 / 6)
        ambas = {"mercado": "Both teams to score", "linha": None, "escolha": "Yes"}
        self.assertAlmostEqual(vr.frequencia(ambas, xh, xa), 3 / 6)

    def test_ajuste_empate(self):
        item = {"mercado": "Double chance", "escolha": "12", "p": 0.79, "dev": 0.0}
        self.assertAlmostEqual(vr.ajuste_empate(item, 0.21, 0.30)[0], 0.70)
        um = {"mercado": "Full time", "escolha": "1", "p": 0.50, "dev": 0.0}
        self.assertAlmostEqual(vr.ajuste_empate(um, 0.20, 0.28)[0], 0.50 * 0.72 / 0.80)
        self.assertEqual(vr.ajuste_empate(um, 0.30, 0.28), (0.50, 0.0))

    def item(self, p, odd, justa, dev=0.0):
        return {"mercado": "Match goals", "linha": "3.5", "escolha": "Under", "rotulo": "Menos de 3.5 gols",
                "p": p, "dev": dev, "odd": odd, "ev": n.ev(p, odd, dev), "justa_mercado": justa,
                "odd_justa": n.odd_justa(p, dev), "odd_minima": n.odd_minima(p, 0.03, dev)}

    def test_filtro(self):
        chave = ("Match goals", "3.5", "Under")
        xs = self.amostra([(1, 1)] * 10)
        bom = {k: {chave: self.item(0.65, 1.70, 0.58)} for k in
               ("base", "incerteza", "dixon_coles", "sem_2_ultimos", "so_gols", "so_xg")}
        cands, motivo = vr.filtrar(bom, xs, xs, self.V, 0.03)
        self.assertEqual(len(cands), 1)
        self.assertIsNone(motivo)
        # uma variante derruba
        fraco = {**bom, "so_xg": {chave: self.item(0.52, 1.70, 0.58)}}
        self.assertEqual(vr.filtrar(fraco, xs, xs, self.V, 0.03)[0], [])
        # regra 8: 18 p.p. acima do mercado
        r8 = {k: {chave: self.item(0.72, 1.70, 0.54)} for k in bom}
        cands, motivo = vr.filtrar(r8, xs, xs, self.V, 0.03)
        self.assertEqual(cands, [])
        self.assertTrue(motivo.startswith("regra 8"))
        # frequência real baixa: 10 jogos com 4 gols
        cheio = self.amostra([(2, 2)] * 10)
        self.assertEqual(vr.filtrar(bom, cheio, cheio, self.V, 0.03)[0], [])
        # linha curta demais
        curta = {k: {chave: self.item(0.95, 1.10, 0.90)} for k in bom}
        self.assertEqual(vr.filtrar(curta, xs, xs, self.V, 0.03)[0], [])

    def test_localizar_descarta_coordenada_errada(self):
        geo = lambda cidade, pais: {"lat": 22.15, "lon": -100.98}   # San Luis Potosí
        errada = {"cidade": "San Luis de Potosi", "pais": "MX", "coord": {"latitude": 37.93, "longitude": -90.78}}
        self.assertEqual(vr.localizar(errada, geo), (22.15, -100.98))
        certa = {"cidade": "San Luis de Potosi", "pais": "MX", "coord": {"latitude": 22.16, "longitude": -100.97}}
        self.assertEqual(vr.localizar(certa, geo), (22.16, -100.97))
        self.assertEqual(vr.localizar({"coord": {"latitude": 1.0, "longitude": 2.0}}, geo), (1.0, 2.0))
        self.assertIsNone(vr.localizar({}, geo))


class TestDefesa(unittest.TestCase):
    D = dict(df.DEFESA_PADRAO)

    def test_favorito_por_odds_e_tabela(self):
        self.assertEqual(df.escolher_favorito([1.5, 4.0, 6.0], None, None, 0.4), (True, "odds"))
        self.assertEqual(df.escolher_favorito([4.0, 3.5, 1.9], None, None, 0.4), (False, "odds"))
        self.assertTrue(df.escolher_favorito(None, 2.1, 1.0, 0.4)[0])
        self.assertIsNone(df.escolher_favorito(None, 1.5, 1.3, 0.4)[0])   # diferença pequena

    def test_triagem_e_risco(self):
        self.assertTrue(df.passa_triagem(1.39, 1.33, self.D))     # tolerância (caso Norrköping)
        self.assertFalse(df.passa_triagem(1.30, 1.50, self.D))
        self.assertFalse(df.passa_triagem(1.80, 1.00, self.D))
        self.assertTrue(df.eh_risco(1.5, None, self.D))
        self.assertTrue(df.eh_risco(0.9, (2, 20), self.D))        # top 30% de ataques
        self.assertFalse(df.eh_risco(0.9, (12, 20), self.D))

    def test_nivel_base(self):
        pal = self.D["palavras_base"]
        self.assertTrue(df.nivel_base(["England Amateur", "Wessex League"], pal, ["Bashley FC", "Christchurch FC"]))
        self.assertTrue(df.nivel_base(["Germany", "Regionalliga"], pal, ["TSV Buchbach", "FC Augsburg II"]))
        self.assertFalse(df.nivel_base(["Sweden", "Superettan"], pal, ["IFK Norrköping", "GIF Sundsvall"]))
        self.assertFalse(df.nivel_base(["Hungary", "NB II"], pal, ["Kazincbarcika", "Vasas"]))   # numeral da liga

    def test_frequencia_e_mediana(self):
        fav = [{"gf": g, "ga": 0} for g in (2, 2, 1, 3, 0)]
        az = [{"gf": 0, "ga": g} for g in (5, 1, 1, 0, 5, 1)]        # média 2,17 inflada; mediana 1
        fr = df.frequencias(fav, az)
        self.assertAlmostEqual(fr["fav_2"], 0.6)
        self.assertAlmostEqual(fr["az_2"], 2 / 6)
        self.assertEqual(fr["mediana_ga_az"], 1)
        self.assertAlmostEqual(df.freq_mercado(fr, 2), (0.6 + 2 / 6) / 2)
        self.assertAlmostEqual(df.freq_mercado(fr, "fav_vence"), (4 / 5 + 5 / 6) / 2)   # venceu 4 de 5; azarão perdeu 5 de 6

    def test_prob_conservadora_limita_pela_frequencia(self):
        self.assertEqual(df.prob_conservadora([0.80, 0.72, 0.76], None, 0.05), (0.72, False))
        p, lim = df.prob_conservadora([0.80, 0.76], 0.55, 0.05)
        self.assertTrue(lim)
        self.assertAlmostEqual(p, 0.60)
        self.assertAlmostEqual(df.odd_minima(0.75, 0.03), 1.38)    # 1.3733 → para cima
        self.assertAlmostEqual(df.odd_minima(0.65, 0.03), 1.59)    # 1.5846 → 1.59 (com 1.58 o EV é 2,7%)
        self.assertAlmostEqual(n.odd_acima(1.6), 1.6)
        self.assertIsNone(df.odd_minima(0.0, 0.03))      # nada de Infinity no JSON
        self.assertAlmostEqual(df.ajuste_empate_vitoria(0.70, 0.20, 0.28), 0.70 * 0.72 / 0.80)
        self.assertEqual(df.ajuste_empate_vitoria(0.70, 0.30, 0.25), 0.70)

    def test_prob_time_marca_bate_com_poisson(self):
        m = n.matriz_placar(2.0, 0.8, 0.0, 12)
        self.assertAlmostEqual(df.prob_time_marca(m, True, 1), 1 - math.exp(-2.0), places=4)
        self.assertAlmostEqual(df.prob_time_marca(m, False, 1), 1 - math.exp(-0.8), places=4)
        p2 = 1 - math.exp(-2.0) * (1 + 2.0)
        self.assertAlmostEqual(df.prob_time_marca(m, True, 2), p2, places=4)

    def test_lambdas_mercado_recupera_os_lambdas(self):
        m = n.matriz_placar(2.1, 0.7, 0.0, 10)
        r = vr.resultado(m)
        over = vr.total_gols(m, 2.5, "over")[0]
        lh, la = df.lambdas_mercado([r["1"], r["X"], r["2"]], {2.5: over})
        self.assertAlmostEqual(lh, 2.1, delta=0.03)
        self.assertAlmostEqual(la, 0.7, delta=0.03)
        lh2, la2 = df.lambdas_mercado([r["1"], r["X"], r["2"]])   # só o 1X2 já identifica os dois λ
        self.assertAlmostEqual(lh2, 2.1, delta=0.05)
        self.assertAlmostEqual(la2, 0.7, delta=0.05)

    def test_calendario(self):
        dia = 86400
        t0 = 100 * dia
        passados = [{"startTimestamp": t0 - 3 * dia, "status": {"type": "finished"}},
                    {"startTimestamp": t0 - 30 * dia, "status": {"type": "finished"}}]
        futuros = [{"startTimestamp": t0 + 4 * dia}]
        c = df.calendario(passados, futuros, t0, 7)
        self.assertEqual(c["jogos_janela"], 3)
        semanal = df.calendario([{"startTimestamp": t0 - 7 * dia, "status": {"type": "finished"}}],
                                [{"startTimestamp": t0 + 7 * dia}], t0, 7)
        self.assertEqual(semanal["jogos_janela"], 1)    # um jogo por semana não é calendário apertado
        self.assertEqual(c["dias_desde_ultimo"], 3.0)
        self.assertEqual(c["dias_ate_proximo"], 4.0)

    def test_alertas_licoes(self):
        info = {"risco": False, "nivel_base": False, "odds": [1.2, 6, 11], "regra8": None, "fav_casa": True,
                "liga": {"casa": 1.5, "fora": 1.3},
                "azarao_amostra": {"n": 10, "ga": 2.1, "xg_contra": 1.3, "ga_ultimos5": 1.2, "expulsoes": 3},
                "favorito_amostra": {"n": 10, "gf": 2.4, "xg_pro": 1.6},
                "frequencias": {"mediana_ga_az": 1},
                "calendario_favorito": {"jogos_janela": 3, "dias_desde_ultimo": 2},
                "regra8_mercados": ["regra 8 (fav vence): modelo 63% x mercado 52%"], "motivo": None}
        al = " | ".join(df.alertas_estatisticos(info, self.D))
        for trecho in ("regressão provável", "acima do xG", "melhorando", "goleadas", "rodízio", "expulsão", "regra 8"):
            self.assertIn(trecho, al)

    def test_forma_ultimos_oficiais(self):
        def ev(ts, casa, gc, gf, torneio="Liga"):
            return {"startTimestamp": ts, "status": {"type": "finished"}, "tournament": {"name": torneio},
                    "homeTeam": {"id": 7 if casa else 8}, "awayTeam": {"id": 8 if casa else 7},
                    "homeScore": {"normaltime": gc}, "awayScore": {"normaltime": gf}}
        evs = [ev(1, True, 2, 0), ev(2, False, 1, 0), ev(3, True, 0, 1), ev(4, True, 3, 0, "Club Friendly Games"),
               ev(5, False, 0, 0), ev(6, True, 1, 2), ev(7, False, 2, 1)]
        f = df.forma(evs, 7, antes_ts=10, qtd=5, palavras_amistoso=self.D["palavras_amistoso"])
        # sem o amistoso: (2) D, (3) D, (5) E, (6) D, (7) D  → 0V 1E 4D
        self.assertEqual(f["seq"], "DDEDD")
        self.assertEqual((f["v"], f["e"], f["d"], f["pts"]), (0, 1, 4, 1))
        self.assertTrue(df.forma_negativa(f))
        self.assertFalse(df.forma_negativa({"n": 5, "pts": 7}))     # 2V 1E 2D = 7 de 15: fica (regra de 14/10)
        self.assertTrue(df.forma_negativa({"n": 5, "pts": 6}))      # 1V 3E 1D (Buchbach 13/10): sai
        self.assertFalse(df.forma_negativa({"n": 5, "pts": 8}))     # 8 de 15: fica
        self.assertTrue(df.forma_negativa({"n": 4, "pts": 5}))      # só 4 oficiais: 7/15 de 12 = 5,6
        self.assertFalse(df.forma_negativa({"n": 3, "pts": 5}))     # 3 oficiais: 7/15 de 9 = 4,2
        self.assertFalse(df.forma_negativa({"n": 0, "pts": 0}))     # sem dado não tira

    def test_escolher_grupo_da_fase_certa(self):
        apertura = {"nome": "Torneo Final", "rows": {1: {"matches": 6}, 2: {"matches": 6}, 3: {"matches": 6}}}
        copa = {"nome": "Qualifiers - Copa", "rows": {1: {"matches": 0}, 9: {"matches": 0}}}
        self.assertIs(df.escolher_grupo([apertura, copa], (1, 2)), apertura["rows"])
        junto = df.escolher_grupo([apertura, copa], (1, 9))    # sem grupo comum: linha de mais jogos
        self.assertEqual(junto[1]["matches"], 6)
        # Santa Fe x Jaguares 14/10: Apertura tem mais jogos, mas o torneio é o Finalización
        ape = {"nome": "Apertura", "rows": {1: {"matches": 19}, 2: {"matches": 19}}}
        fin = {"nome": "Finalización", "rows": {1: {"matches": 12}, 2: {"matches": 12}}}
        self.assertIs(df.escolher_grupo([ape, fin], (1, 2), "Liga DIMAYOR, Finalizacion"), fin["rows"])
        # Academia x Monagas 18/10: o grupo leva o ano no nome ("Primera Division 2026, Clausura")
        ape26 = {"nome": "Primera Division 2026, Apertura", "rows": {1: {"matches": 13}, 2: {"matches": 13}}}
        cla26 = {"nome": "Primera Division 2026, Clausura", "rows": {1: {"matches": 6}, 2: {"matches": 6}}}
        self.assertIs(df.escolher_grupo([ape26, cla26], (1, 2), "Primera Division, Clausura"), cla26["rows"])

    def test_tese_recente_contradiz_a_tabela(self):
        base = {"fav_casa": True, "liga": {"casa": 1.15, "fora": 0.70}}
        cumbaya = dict(base, azarao_amostra={"n": 10, "ga": 2.2}, favorito_amostra={"n": 10, "gf": 0.9})
        self.assertIn("ataque do favorito", df.contradiz_tese_recente(cumbaya, self.D))
        la_viena = dict(base, fav_casa=False, liga={"casa": 1.25, "fora": 0.975},
                        azarao_amostra={"n": 10, "ga": 0.7}, favorito_amostra={"n": 10, "gf": 1.5})
        self.assertIn("defesa do azarão", df.contradiz_tese_recente(la_viena, self.D))
        bom = dict(base, azarao_amostra={"n": 10, "ga": 2.0}, favorito_amostra={"n": 10, "gf": 1.6})
        self.assertIsNone(df.contradiz_tese_recente(bom, self.D))
        pouco = dict(base, azarao_amostra={"n": 3, "ga": 0.3}, favorito_amostra={"n": 3, "gf": 0.3})
        self.assertIsNone(df.contradiz_tese_recente(pouco, self.D))     # amostra curta: só alerta
        # Bursaspor x Pendikspor 19/10: sofre 1,9 fora, mas cede 1,31 de xG (×0,96 da liga) → sai
        pendik = dict(base, liga={"casa": 1.371, "fora": 1.229},
                      azarao_amostra={"n": 10, "ga": 1.9, "xg_contra": 1.31}, favorito_amostra={"n": 4, "gf": 2.0})
        self.assertIn("xG cedido", df.contradiz_tese_recente(pendik, self.D))
        # Nashville x Sporting KC 14/10 (acertou 4-0): xG cedido ×1,00 da liga continua
        skc = dict(base, liga={"casa": 1.852, "fora": 1.3},
                   azarao_amostra={"n": 10, "ga": 2.9, "xg_contra": 1.86}, favorito_amostra={"n": 10, "gf": 2.5})
        self.assertIsNone(df.contradiz_tese_recente(skc, self.D))
        # Taunton x Bracknell 20/10: 2,1/j fora, mas 1,56 sem o 0-7 da estreia (×0,88) → sai
        bracknell = dict(base, liga={"casa": 1.776, "fora": 1.4},
                         azarao_amostra={"n": 10, "ga": 2.1, "ga_aparada": 1.56}, favorito_amostra={"n": 10, "gf": 2.1})
        self.assertIn("pior goleada", df.contradiz_tese_recente(bracknell, self.D))
        xs = [{"gf": 0, "ga": g, "adv": "x"} for g in (7, 2, 2, 2, 1, 1)]
        self.assertAlmostEqual(df.resumo_amostra(xs)["ga_aparada"], 1.6)

    def test_lambdas_gerais_tira_o_inflado_da_condicao(self):
        # Bridlington (fora) 14/10: 18 gols em 11 no geral; Stocksbridge (casa) sofreu 23 em 11 no geral
        casa = {"matches": 11, "scoresFor": 8, "scoresAgainst": 23}
        fora = {"matches": 11, "scoresFor": 18, "scoresAgainst": 16}
        lh, la = df.lambdas_gerais(casa, fora, 1.667, 1.121)
        self.assertAlmostEqual(la, 1.97, delta=0.02)    # o cético achou ~1,97; o recorte fora dava 2,18
        self.assertIsNone(df.lambdas_gerais({"matches": 0}, fora, 1.6, 1.1))

    def test_liga_nao_verificavel(self):
        fantasma = {"season": {"editor": True}, "homeTeam": {"createdByEditor": True}, "awayTeam": {"createdByEditor": True}}
        wessex = {"season": {"editor": True}, "homeTeam": {}, "awayTeam": {}}
        mls = {"season": {"editor": False}, "homeTeam": {}, "awayTeam": {}}
        self.assertTrue(df.liga_nao_verificavel(fantasma))
        self.assertFalse(df.liga_nao_verificavel(wessex))   # amadora real: só alerta
        self.assertFalse(df.liga_nao_verificavel(mls))

    def test_eventos_suspeitos(self):
        def ev(i, h, a, ts, placar=None):
            e = {"id": i, "homeTeam": {"id": h}, "awayTeam": {"id": a}, "startTimestamp": ts, "homeScore": {}, "awayScore": {}}
            if placar:
                e["homeScore"], e["awayScore"] = {"current": placar[0]}, {"current": placar[1]}
            return e
        evs = [ev(1, 10, 11, 100), ev(2, 10, 12, 100), ev(3, 20, 21, 100, (2, 3)), ev(4, 30, 31, 100)]
        self.assertEqual(df.eventos_suspeitos(evs), {1, 2, 3})   # Cahul com 2 jogos no mesmo horário; placar já preenchido

    def test_expulsao_relevante(self):
        jog = {"incidentType": "card", "incidentClass": "red", "isHome": True, "time": 30, "player": {"name": "X"}}
        self.assertTrue(df.expulsao_relevante(jog, True))
        self.assertFalse(df.expulsao_relevante(jog, False))                       # foi do outro time
        self.assertFalse(df.expulsao_relevante(dict(jog, time=90), True))          # acréscimos
        tec = {"incidentType": "card", "incidentClass": "red", "isHome": True, "time": 30, "manager": {"name": "T"}}
        self.assertFalse(df.expulsao_relevante(tec, True))                        # técnico
        self.assertFalse(df.expulsao_relevante(dict(jog, rescinded=True), True))


class TestPrevisoes(unittest.TestCase):
    def test_avaliar_mercados(self):
        self.assertTrue(previsoes.avaliar("marca_2", "casa", 2, 0))
        self.assertFalse(previsoes.avaliar("marca_2", "fora", 2, 1))
        self.assertTrue(previsoes.avaliar("marca_1", "fora", 0, 1))
        self.assertTrue(previsoes.avaliar("vence", "fora", 0, 1))
        self.assertTrue(previsoes.avaliar("dupla_chance", "casa", 1, 1))
        self.assertTrue(previsoes.avaliar("over_2.5", "casa", 2, 1))
        self.assertFalse(previsoes.avaliar("under_2.5", "casa", 2, 1))
        self.assertTrue(previsoes.avaliar("ambas_sim", "casa", 1, 2))
        self.assertTrue(previsoes.avaliar("ambas_nao", "casa", 3, 0))
        self.assertTrue(previsoes.avaliar("sem_empate", "casa", 0, 1))
        self.assertFalse(previsoes.avaliar("handicap_-1.5", "casa", 2, 1))
        self.assertTrue(previsoes.avaliar("handicap_+1.5", "fora", 2, 1))
        self.assertIsNone(previsoes.avaliar("escanteios", "casa", 1, 1))

    def test_fluxo_resolver_e_resumo(self):
        with tempfile.TemporaryDirectory() as d:
            arq = Path(d) / "p.csv"
            linhas = previsoes.ler(arq)
            base = {"data": "2026-10-12", "jogo": "A x B", "analise": "defesa", "lado": "casa"}
            previsoes.adicionar(linhas, dict(base, evento="1", mercado="marca_2", prob="0.80"))
            previsoes.adicionar(linhas, dict(base, evento="2", mercado="marca_1", prob="0.84"))
            previsoes.adicionar(linhas, dict(base, evento="3", mercado="marca_1", prob="0.70"))
            previsoes.adicionar(linhas, dict(base, evento="1", mercado="marca_2", prob="0.78"))  # atualiza, não duplica
            self.assertEqual(len(linhas), 3)
            self.assertEqual(linhas[0]["prob"], "0.78")
            eventos = {"1": {"event": {"status": {"type": "finished"}, "homeScore": {"normaltime": 3},
                                       "awayScore": {"normaltime": 0}}},
                       "2": {"event": {"status": {"type": "finished"}, "homeScore": {"normaltime": 0},
                                       "awayScore": {"normaltime": 0}}},
                       "3": {"event": {"status": {"type": "notstarted"}}}}
            feitos = previsoes.resolver(linhas, eventos.get)
            self.assertEqual([x["acerto"] for x in feitos], ["1", "0"])
            previsoes.salvar(linhas, arq)
            r = previsoes.resumo(previsoes.ler(arq))
            self.assertEqual((r["n"], r["acertos"], r["pendentes"]), (2, 1, 1))
            self.assertAlmostEqual(r["brier"], ((0.78 - 1) ** 2 + 0.84 ** 2) / 2)
            self.assertTrue(previsoes.avisos_calibracao(r))   # amostra pequena → aviso

    def test_normalizar_valida_lado_e_listas(self):
        base = {"data": "2026-10-13", "evento": 9, "jogo": "A x B", "mercado": "marca_1", "prob": 0.8}
        self.assertEqual(previsoes.normalizar(dict(base, lado="Fora"))["lado"], "fora")
        self.assertEqual(previsoes.normalizar(dict(base, lado="home"))["lado"], "casa")
        with self.assertRaises(ValueError):
            previsoes.normalizar(base)                         # sem lado num mercado do time
        with self.assertRaises(ValueError):
            previsoes.normalizar(dict(base, lado="casa", mercado="fav_dc"))
        self.assertEqual(previsoes.normalizar(dict(base, mercado="over_2.5"))["lado"], "casa")   # total não precisa
        self.assertEqual(previsoes.normalizar(dict(base, lado="casa", alertas=[]))["alertas"], "")
        self.assertEqual(previsoes.normalizar(dict(base, lado="casa", alertas=["a", "b"]))["alertas"], "a; b")


class TestAzarao(unittest.TestCase):
    A = dict(azr.AZARAO_PADRAO)

    def test_ppg(self):
        self.assertAlmostEqual(azr.ppg({"matches": 10, "wins": 5, "draws": 3}), 1.8)
        self.assertAlmostEqual(azr.ppg({"matches": 4, "points": 7}), 1.75)
        self.assertIsNone(azr.ppg({"matches": 0}))
        xs = [{"gf": 2, "ga": 1}, {"gf": 1, "ga": 1}, {"gf": 0, "ga": 2}]
        self.assertAlmostEqual(azr.ppg_amostra(xs), 4 / 3)

    def test_triagem_azarao(self):
        self.assertTrue(azr.passa_triagem_azarao(4.1, 1.46, 1.31, 0.52, 0.92, self.A))     # Tianjin 16/10
        self.assertFalse(azr.passa_triagem_azarao(1.9, 1.8, 1.0, 0.6, 1.0, self.A))      # não é azarão
        self.assertFalse(azr.passa_triagem_azarao(3.5, 0.9, 1.8, 0.8, 1.0, self.A))      # rende bem menos
        self.assertFalse(azr.passa_triagem_azarao(3.5, 1.6, 1.5, 1.3, 1.0, self.A))      # defesa fraca
        self.assertFalse(azr.passa_triagem_azarao(3.5, 1.6, 1.5, 0.8, 0.6, self.A))      # sem ataque

    def test_frequencias_e_dnb(self):
        az = [{"gf": 1, "ga": 1}, {"gf": 2, "ga": 0}, {"gf": 0, "ga": 1}, {"gf": 1, "ga": 0}]
        fav = [{"gf": 0, "ga": 0}, {"gf": 2, "ga": 1}, {"gf": 1, "ga": 2}, {"gf": 3, "ga": 0}]
        fr = azr.frequencias_azarao(az, fav)
        self.assertAlmostEqual(fr["az_nao_perde"], 0.75)
        self.assertAlmostEqual(fr["fav_nao_vence"], 0.5)
        self.assertAlmostEqual(azr.freq_mercado_az(fr, "az_dc"), 0.625)
        self.assertAlmostEqual(azr.ev_empate_anula(0.4, 0.3, 2.0), 0.1)   # 0,8 + 0,3 − 1

    def test_probs_lado(self):
        p = azr.probs_lado(1.2, 1.0, False, 0.0, 0.0)          # lado = visitante
        m = n.matriz_placar(1.2, 1.0, 0.0, 10)
        r = vr.resultado(m)
        self.assertAlmostEqual(p["az_vence"], r["2"], places=6)
        self.assertAlmostEqual(p["az_dc"], r["2"] + r["X"], places=6)

    def test_odd_dc_sintetica(self):
        # Livorno x Grosseto 16/10: 2.05/3.20/3.20 → X2 implícita 1.60; Jonava x BFA 3.75/2.50 → 1.50
        self.assertAlmostEqual(azr.odd_dc_sintetica(3.2, 3.2), 1.6)
        self.assertAlmostEqual(azr.odd_dc_sintetica(3.75, 2.5), 1.5)

    def test_lambdas_amostra_xg(self):
        # visitante "com sorte": sofre 0,8 com 1,55 de xG cedido (Henan x Tianjin, 16/10)
        jogo = lambda gf, ga, xf, xa: {"gf": gf, "ga": ga, "xg_f": xf, "xg_a": xa}  # noqa: E731
        casa = [jogo(1.3, 1.0, 1.54, 1.04)] * 10
        fora = [jogo(1.3, 0.8, 1.06, 1.55)] * 10
        lams = azr.lambdas_amostra(casa, fora, (1.5, 1.2), 4)
        self.assertEqual(set(lams), {"gols", "mix", "xg"})
        dc = {m: azr.probs_lado(*lam, False, 0.0, 0.0)["az_dc"] for m, lam in lams.items()}
        self.assertLess(dc["xg"], dc["mix"])
        self.assertLess(dc["mix"], dc["gols"])
        # sem xG: só a variante de gols; amostra curta: nada
        sem = [dict(j, xg_f=None, xg_a=None) for j in casa]
        self.assertEqual(set(azr.lambdas_amostra(sem, fora, (1.5, 1.2), 4)), {"gols"})
        self.assertEqual(azr.lambdas_amostra(casa[:2], fora, (1.5, 1.2), 4), {})


class TestUnder(unittest.TestCase):
    U = dict(und.UNDER_PADRAO)

    @staticmethod
    def ev(ts, hs, as_, torneio="Eredivisie", status="finished", season=1):
        return {"startTimestamp": ts, "status": {"type": status}, "homeScore": {"normaltime": hs},
                "awayScore": {"normaltime": as_}, "tournament": {"name": torneio, "uniqueTournament": {"name": torneio}},
                "season": {"id": season}}

    def test_cauda_feyenoord(self):
        # lição 33: 5 dos últimos 7 com 5+ gols derrubam o under 4.5 de 75%
        placares = [(1, 0), (2, 1), (5, 2), (7, 0), (5, 0), (1, 5), (3, 2), (2, 2)]
        evs = [self.ev(100 + i, a, b) for i, (a, b) in enumerate(placares)]
        evs.append(self.ev(50, 9, 0, torneio="Club Friendly Games"))   # amistoso não conta
        evs.append(self.ev(500, 9, 0))                                    # depois do jogo: não conta
        c = und.cauda(evs, 400, 4.5, 7, ["Friendly"])
        self.assertEqual((c["n"], c["acima"]), (7, 5))
        self.assertTrue(und.estoura_cauda([c["frac"], 0.0], 0.75, 0.15))
        self.assertFalse(und.estoura_cauda([2 / 7, None], 0.75, 0.15))   # 29% ≤ 25% + 15%

    def test_liga_temporada_xg(self):
        self.assertAlmostEqual(und.taxa_liga_under([1, 2, 3, 4, 5], 3.5), 0.6)
        self.assertIsNone(und.taxa_liga_under([], 3.5))
        self.assertAlmostEqual(und.fracao_temporada([{"season": {"id": 2}}, {"season": {"id": 1}}], 2), 0.5)
        xh = [{"xg_f": 1.5, "xg_a": 1.0}] * 4
        xa = [{"xg_f": 1.0, "xg_a": 1.5}] * 4
        self.assertAlmostEqual(und.xg_somado(xh, xa), 2.5)
        self.assertIsNone(und.xg_somado([{"xg_f": None, "xg_a": None}] * 4, xa))

    def test_requisitos(self):
        k = {"p": 0.75, "linha": "4.5", "frequencia": 0.8}
        ok = {"casa": {"n": 7, "acima": 1, "frac": 1 / 7}, "fora": {"n": 7, "acima": 1, "frac": 1 / 7}}
        ex = {"cauda": ok, "taxa_liga": 0.85, "temporada_atual": 0.9, "xg_somado": 2.6, "odd_favorito": 1.33}
        self.assertEqual(und.requisitos(k, ex, self.U), ([], []))
        ruim = dict(ex, cauda={**ok, "fora": {"n": 7, "acima": 5, "frac": 5 / 7}}, taxa_liga=0.5,
                    temporada_atual=0.0, xg_somado=4.0, odd_favorito=1.2)
        falhas, alertas = und.requisitos(k, ruim, self.U)
        self.assertEqual(len(falhas), 3)       # cauda, liga e temporada passada (Central Coast, lição 32)
        self.assertEqual(len(alertas), 2)      # xG perto da linha e favorito muito forte

    def test_unders_do_jogo(self):
        cfg = {"varredura": dict(vr.VARREDURA_PADRAO), "criterios": {"ev_minimo": 0.03}}
        item = lambda p, odd=1.30, justa=0.70: {"mercado": "Match goals", "linha": "3.5", "escolha": "Under",  # noqa: E731
                                                "p": p, "odd": odd, "ev": p * odd - 1, "justa_mercado": justa, "dev": 0.0}
        k = ("Match goals", "3.5", "Under")
        jogo = [{"gf": 1, "ga": 0}] * 6
        info = {"variantes": {"base": {k: item(0.78)}, "incerteza": {k: item(0.76)}, "dixon_coles": {k: item(0.77)},
                              "so_xg": {k: item(0.69)}}, "amostras": (jogo, jogo), "taxa_base": None}
        r = und.unders_do_jogo(info, cfg, self.U)
        self.assertEqual(len(r), 1)
        self.assertFalse(r[0]["com_valor"])                    # 0.78 × 1.30 → EV +1,4% < 3%: bate a prob., sem valor
        info["variantes"]["base"][k] = item(0.78, odd=1.40)
        self.assertTrue(und.unders_do_jogo(info, cfg, self.U)[0]["com_valor"])   # EV +9,2%
        info["variantes"]["so_xg"][k] = item(0.66)             # outra variante abaixo de 70% − 3 p.p.
        self.assertEqual(und.unders_do_jogo(info, cfg, self.U), [])

    def test_xg_atual_e_tabelas(self):
        # lição 39: 13 de 13 abaixo da linha, mas 1,3 gol por jogo com 2,9 de xG somado → under ≈ mercado
        jogo = lambda t: {"t": t, "gf": 1, "ga": 0, "xg_f": 1.5, "xg_a": 1.4}  # noqa: E731
        xh = [jogo(t) for t in range(10)]
        xa = [jogo(t) for t in range(100, 110)]
        r = und.under_xg_atual(xh, xa, set(range(5, 10)) | set(range(105, 110)), 3.5)
        self.assertEqual(r["n"], [5, 5])
        self.assertAlmostEqual(r["xg_jogo"], 2.9)
        self.assertLess(r["p"], 0.72)
        self.assertIsNone(und.under_xg_atual(xh, xa, {1, 2}, 3.5))        # poucos jogos desta temporada
        sem = [dict(x, xg_f=None, xg_a=None) for x in xa]                  # lição 46: só um lado com xG
        parcial = und.under_xg_atual(xh, sem, set(range(5, 10)) | set(range(105, 110)), 3.5)
        self.assertTrue(parcial["parcial"])
        self.assertIsNone(und.under_xg_atual([dict(x, xg_f=None, xg_a=None) for x in xh], sem,
                                             set(range(5, 10)) | set(range(105, 110)), 3.5))
        k = {"p": 0.83, "linha": "3.5", "frequencia": 0.9, "justa_mercado": 0.73}
        ok = {"casa": {"n": 7, "acima": 1, "frac": 1 / 7}, "fora": {"n": 7, "acima": 1, "frac": 1 / 7}}
        falhas, _ = und.requisitos(k, {"cauda": ok, "xg_atual": dict(r, p=0.74)}, self.U)
        self.assertEqual(len(falhas), 1)                                   # 74% < 73% + 2 p.p.
        self.assertEqual(und.requisitos(k, {"cauda": ok, "xg_atual": dict(r, p=0.78)}, self.U)[0], [])
        # lição 40: tabelas casa/fora com pênaltis (J2 2026)
        self.assertAlmostEqual(vr.fator_tabelas(540, 491, 925), 925 / 1031)
        self.assertEqual(vr.fator_tabelas(500, 425, 925), 1.0)

    def test_dispersao_e_limite(self):
        # lição 49: totais dispersos (0-0 e goleadas) derrubam a P(under 5.5) do Poisson
        tots = [3, 10, 5, 5, 2, 1, 2, 7, 0, 3, 5, 5, 3, 3]
        d = und.under_dispersao(tots, 5.5)
        self.assertGreater(d["variancia"], 1.3 * d["media"])
        m = sum(tots) / len(tots)
        poisson = sum(math.exp(-m) * m ** k / math.factorial(k) for k in range(6))
        self.assertLess(d["p"], poisson)
        self.assertIsNone(und.under_dispersao([2, 3, 2, 3, 2, 3, 2, 3], 3.5))   # sem sobredispersão
        self.assertIsNone(und.under_dispersao([1, 9], 3.5))                     # poucos jogos
        # lição 48: jogos exatamente no limite
        evs = [self.ev(100 + i, a, b) for i, (a, b) in enumerate([(2, 1), (1, 2), (3, 0), (1, 1), (0, 0), (2, 1), (1, 0)])]
        c = und.cauda(evs, 400, 3.5, 7, ["Friendly"])
        self.assertEqual((c["acima"], c["no_limite"]), (0, 4))
        k = {"p": 0.82, "linha": "3.5", "frequencia": 0.9, "justa_mercado": 0.78}
        falhas, alertas = und.requisitos(k, {"cauda": {"casa": c, "fora": c}}, self.U)
        self.assertEqual(falhas, [])
        self.assertTrue(any("exatamente 3 gols" in a for a in alertas))

    def test_cauda_na_condicao(self):
        # lição 50: cauda mista limpa, mas o mandante em casa tem 4+ em metade dos jogos
        casa = [{"gf": a, "ga": b} for a, b in [(2, 2), (3, 1), (1, 3), (2, 2), (3, 3), (1, 0), (2, 1), (0, 1), (1, 1), (2, 0)]]
        c = und.cauda_amostra(casa, 4.5)
        self.assertEqual((c["n"], c["acima"], c["no_limite"]), (10, 1, 4))
        ok = {"n": 7, "acima": 1, "frac": 1 / 7, "no_limite": 0}
        k = {"p": 0.77, "linha": "4.5", "frequencia": 0.9, "justa_mercado": 0.77}
        falhas, alertas = und.requisitos(k, {"cauda": {"casa": ok, "fora": ok},
                                              "cauda_cond": {"casa": c, "fora": und.cauda_amostra(casa[:5], 4.5)}}, self.U)
        self.assertEqual(falhas, [])
        self.assertTrue(any("na condição" in a for a in alertas))
        ruim = und.cauda_amostra([{"gf": 3, "ga": 3}] * 4 + [{"gf": 1, "ga": 0}] * 6, 4.5)   # 40% acima
        self.assertTrue(und.requisitos(k, {"cauda": {"casa": ok, "fora": ok}, "cauda_cond": {"casa": ruim, "fora": c}}, self.U)[0])

    def test_mercados_robustos_qualquer_mercado(self):
        cfg = {"varredura": dict(vr.VARREDURA_PADRAO), "criterios": {"ev_minimo": 0.03}}
        it = lambda m, l, e, p, odd, justa: {"mercado": m, "linha": l, "escolha": e, "p": p, "odd": odd,  # noqa: E731
                                             "ev": p * odd - 1, "justa_mercado": justa, "dev": 0.0}
        k1, k2 = ("Double chance", None, "1X"), ("Match goals", "2.5", "Over")
        var = lambda p1, p2: {k1: it("Double chance", None, "1X", p1, 1.30, 0.74), k2: it("Match goals", "2.5", "Over", p2, 1.50, 0.62)}  # noqa: E731
        info = {"variantes": {"base": var(0.78, 0.72), "incerteza": var(0.77, 0.71), "dixon_coles": var(0.78, 0.69)},
                "amostras": ([], []), "taxa_base": None}
        r = vr.mercados_robustos(info, cfg, 0.70)
        self.assertEqual([x["mercado"] for x in r], ["Double chance"])      # o over cai: 69% numa obrigatória
        self.assertFalse(r[0]["com_valor"])                                 # 0,78 × 1,30 → EV +1,4% < 3%: bate a prob., sem valor


class TestPlataformas(unittest.TestCase):
    """365Scores como 2ª plataforma (pedido do Daniel em 21/10: confirmar os dados fora do Sofascore)."""

    def jogo(self, h, a, sh, sa, comp=11, ini="2026-10-10T16:00:00-03:00", nome="LaLiga"):
        return {"homeCompetitor": {"id": h, "score": sh}, "awayCompetitor": {"id": a, "score": sa},
                "competitionId": comp, "startTime": ini, "competitionDisplayName": nome}

    def test_placar_e_amistoso(self):
        self.assertEqual(pl.placar(self.jogo(1, 2, 2.0, 1.0)), (2, 1))
        self.assertIsNone(pl.placar(self.jogo(1, 2, -1.0, -1.0)))           # jogo ainda não começou
        self.assertTrue(pl.amistoso(self.jogo(1, 2, 0, 0, nome="Club Friendly Games")))

    def test_mesmo_time(self):
        self.assertTrue(pl.mesmo_time("Athletic Club", "Athletic Bilbao"))
        self.assertTrue(pl.mesmo_time("Club Atlético Belgrano", "Belgrano"))
        self.assertFalse(pl.mesmo_time("Real Madrid", "Real Sociedad"))

    def test_medias_liga_e_condicao(self):
        casa = {1: {"for": 10, "gamePlayed": 5}, 2: {"for": 5, "gamePlayed": 5}}
        fora = {1: {"for": 4, "gamePlayed": 5}, 2: {"for": 6, "gamePlayed": 5}}
        self.assertEqual(pl.medias_liga(casa, fora), (1.5, 1.0))
        js = [self.jogo(1, 2, 2, 0), self.jogo(3, 1, 1, 1), self.jogo(1, 4, 0, 1), self.jogo(1, 5, 3, 3, comp=99)]
        em_casa = pl.condicao(js, 1, True, 11, 10)
        self.assertEqual(len(em_casa), 2)                                   # o jogo da copa (99) e o de fora ficam de fora
        self.assertEqual(pl.medias_de(em_casa, True), (1.0, 0.5, 2))
        self.assertEqual(pl.acima([1, 2, 3, 5], 2.5), 2)

    def test_status_confere(self):
        st, mot = pl.status_confere(0.82, 0.80, 1, 2, 0)
        self.assertEqual((st, mot), ("CONFIRMADO", []))
        st, mot = pl.status_confere(0.82, 0.68, 1, 3, 45)
        self.assertEqual(st, "DIVERGENTE")
        self.assertEqual(len(mot), 3)                                       # prob., cauda e horário

    def test_linha_e_nivel(self):
        self.assertEqual(pl.linha_de({"chave": ["Match goals", "3.5", "Under"]}), 3.5)
        self.assertEqual(pl.linha_de({"rotulo": "Menos de 2.5 gols"}), 2.5)
        self.assertTrue(pl.nivel_base("Argentina · Liga Profesional - Reserva", ["River Plate Res."], ["Reserve"]))
        self.assertFalse(pl.nivel_base("Malta · Premier League", ["Hamrun Spartans", "Balzan Youths FC"], ["Youth"]))

