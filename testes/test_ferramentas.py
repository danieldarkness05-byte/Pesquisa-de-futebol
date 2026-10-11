"""Testes das ferramentas. Rode com:  python3 -m unittest discover testes"""
import math
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ferramentas"))

import clima  # noqa: E402
import historico  # noqa: E402
import nucleo as n  # noqa: E402
import registro  # noqa: E402
import sistema  # noqa: E402

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


if __name__ == "__main__":
    unittest.main()
