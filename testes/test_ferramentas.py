"""Testes das ferramentas. Rode com:  python3 -m unittest discover testes"""
import math
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ferramentas"))

import clima  # noqa: E402
import dossie  # noqa: E402
import historico  # noqa: E402
import nucleo as n  # noqa: E402
import registro  # noqa: E402
import sistema  # noqa: E402
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
