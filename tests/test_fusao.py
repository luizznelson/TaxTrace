import unittest

from taxtrace.fusao import completar, fundir


def item(numero, *, parcial=False):
    return {
        "artigo_numero": numero,
        "pontuacao": 99999,
        "correspondencia_parcial": parcial,
        "termos_ausentes": ["falta"] if parcial else [],
    }


class FusaoTest(unittest.TestCase):
    def test_consenso_supera_item_em_uma_unica_lista(self):
        r = fundir({"v1": [item("1"), item("2")], "v2": [item("3"), item("2")]}, 3)
        self.assertEqual(r[0]["artigo_numero"], "2")
        self.assertEqual(r[0]["posicoes"], {"v1": 2, "v2": 2})
        self.assertAlmostEqual(r[0]["pontuacao"], 2 / 62)

    def test_duplicata_nao_duplica_voto(self):
        r = fundir({"v1": [item("1"), item("1")]}, 5)
        self.assertEqual(len(r), 1)
        self.assertAlmostEqual(r[0]["pontuacao"], 1 / 61)

    def test_vazio_empate_e_limite(self):
        self.assertEqual(fundir({"v1": [], "v2": []}, 5), [])
        self.assertEqual(fundir({"v1": [item("2")], "v2": [item("1")]}, 1)[0]["artigo_numero"], "1")

    def test_metadados_parciais_e_entradas_preservados(self):
        original = item("1")
        r = fundir({"v1": [original], "v2": [item("1", parcial=True), item("2")]}, 5)
        self.assertTrue(r[0]["correspondencia_parcial"])
        self.assertEqual(r[0]["termos_ausentes"], ["falta"])
        self.assertEqual(original["pontuacao"], 99999)
        apenas_v1 = fundir({"v1": [original]}, 1)[0]
        self.assertIsNone(apenas_v1["correspondencia_parcial"])
        self.assertIsNone(apenas_v1["termos_ausentes"])


class ComplementoTest(unittest.TestCase):
    def test_preserva_prefixo_e_preenche_sem_duplicatas(self):
        a = [item("3"), item("1")]
        r = completar(a, [item("1"), item("2"), item("4")], 3)
        self.assertEqual([x["artigo_numero"] for x in r], ["3", "1", "2"])
        self.assertEqual([x["origem"] for x in r], ["v1", "v1", "v2"])
        self.assertNotIn("origem", a[0])

    def test_lista_principal_cheia_nao_perde_resultados(self):
        principal = [item(str(i)) for i in range(5)]
        r = completar(principal, [item("9")], 5)
        self.assertEqual([x["artigo_numero"] for x in r], [str(i) for i in range(5)])
        self.assertEqual(completar([], [], 5), [])
