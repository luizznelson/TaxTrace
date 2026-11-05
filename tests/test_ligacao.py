import unittest

from taxtrace.lei import Artigo
from taxtrace.ligacao import ligar, numeros_de_artigos
from taxtrace.tabelas import Classificacao


def classificacao(codigo: str, texto_curto: str) -> Classificacao:
    zero = 0
    return Classificacao(
        codigo=codigo,
        cst=codigo[:3],
        descricao="",
        descricao_tratamento="",
        tipo_aliquota="Padrão",
        nomenclatura="NBS ou NCM",
        percentual_reducao_cbs=zero,
        percentual_reducao_ibs_uf=zero,
        percentual_reducao_ibs_mun=zero,
        data_atualizacao="2026-10-01",
        texto_curto=texto_curto,
        hierarquia_referencia="",
    )


class NumerosDeArtigosTest(unittest.TestCase):
    def casos(self):
        return {
            "Art. 10, § 3º": ("10",),
            "Art. 102": ("102",),
            "Art. 4º": ("4",),
            "Art. 6º, VIII": ("6",),
            "Art 28, parágrafos 3° e 4°": ("28",),
            "Art. 12, §2º III": ("12",),
            "Art. 127, I a XVIII": ("127",),
            "Art. 128, I, II, VIII, IX, X, XI, XII e XIII": ("128",),
            "Art. 26, § 5º-A, I e II": ("26",),
            "Art. 47, § 6º  ": ("47",),
            "Art. 93, IV e Art. 93, § 4º": ("93",),
            "Art. 9º, I e § 1º": ("9",),
            "Arts. 99 e 100": ("99", "100"),
            "Arts. 99, 100 e 101": ("99", "100", "101"),
            "Art. 482-A, § 1º": ("482-A",),
            "LC 214/2025": (),
            "": (),
        }

    def test_padroes_da_api(self):
        for texto, esperado in self.casos().items():
            with self.subTest(texto=texto):
                self.assertEqual(numeros_de_artigos(texto), esperado)


class LigarTest(unittest.TestCase):
    def test_separa_achados_ausentes_e_regra_geral(self):
        artigos = [Artigo(numero="10", texto="Art. 10"), Artigo(numero="99", texto="Art. 99")]
        classificacoes = (
            classificacao("000001", "LC 214/2025"),
            classificacao("200001", "Art. 10, § 3º"),
            classificacao("200002", "Arts. 99 e 100"),
        )
        geral, simples, parcial = ligar(classificacoes, artigos)
        self.assertTrue(geral.regra_geral)
        self.assertEqual(geral.artigos, ())
        self.assertEqual((simples.artigos, simples.ausentes), (("10",), ()))
        self.assertEqual((parcial.artigos, parcial.ausentes), (("99",), ("100",)))
        self.assertFalse(parcial.regra_geral)


if __name__ == "__main__":
    unittest.main()
