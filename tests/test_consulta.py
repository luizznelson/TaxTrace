import unittest

from taxtrace.consulta import preparar


class ConsultaTest(unittest.TestCase):
    def test_preserva_negacao_valores_e_datas(self):
        texto = preparar("Qual artigo não reduz IBS em 30% em 2027?")
        self.assertIn("não", texto)
        self.assertIn("30", texto)
        self.assertIn("2027", texto)
        self.assertIn("ibs", texto)
        self.assertNotIn("qual", texto.split())

    def test_normaliza_unicode_sem_alterar_o_original(self):
        self.assertEqual(preparar("CESTA ba\u0301sica"), "cesta básica")


if __name__ == "__main__":
    unittest.main()
