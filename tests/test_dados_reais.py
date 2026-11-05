"""Confere a coleta real em ``data/raw``. É ignorado quando a pasta não existe (ex.: no CI)."""

import unittest
from pathlib import Path

from taxtrace import lei, ligacao, tabelas

RAIZ = Path(__file__).resolve().parent.parent / "data" / "raw"


def _pasta() -> Path | None:
    try:
        pasta = tabelas.pasta_mais_recente(RAIZ)
    except FileNotFoundError:
        return None
    return pasta if (pasta / "lc214_planalto.html").exists() else None


@unittest.skipUnless(_pasta(), "sem coleta completa em data/raw")
class DadosReaisTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pasta = _pasta()
        cls.artigos = lei.ler_artigos((pasta / "lc214_planalto.html").read_bytes())
        cls.tabelas = tabelas.carregar(pasta)

    def test_lei_vai_do_artigo_1_ao_544_sem_buracos(self):
        bases = {int(a.numero.split("-")[0]) for a in self.artigos}
        self.assertEqual(bases, set(range(1, 545)))
        numeros = [a.numero for a in self.artigos]
        self.assertEqual(len(numeros), len(set(numeros)))

    def test_todo_artigo_citado_pelas_classificacoes_existe_na_lei(self):
        ligacoes = ligacao.ligar(self.tabelas.classificacoes, self.artigos)
        self.assertEqual([lig.codigo for lig in ligacoes if lig.ausentes], [])

    def test_classificacoes_tem_versao_da_base(self):
        self.assertTrue(self.tabelas.versao.base.startswith("V"))
        self.assertGreater(len(self.tabelas.classificacoes), 100)


if __name__ == "__main__":
    unittest.main()
