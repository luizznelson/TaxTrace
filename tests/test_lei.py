import unittest

from taxtrace import lei

HTML = """
<html><head><style>p {color: red}</style></head><body>
<p>LEI COMPLEMENTAR Nº 214, DE 16 DE JANEIRO DE 2025</p>
<p>Institui o IBS, a CBS e o IS.</p>
<p>LIVRO I</p>
<p>DO IMPOSTO SOBRE BENS E SERVIÇOS (IBS)</p>
<p>TÍTULO I</p>
<p>DAS NORMAS GERAIS</p>
<p>CAPÍTULO I</p>
<p>DISPOSIÇÕES PRELIMINARES</p>
<p>Art. 1º Ficam instituídos:</p>
<p>I&nbsp;- o Imposto sobre Bens e Serviços (IBS); e</p>
<p>II - a CBS.</p>
<p>Art. 2º O IBS e a CBS são informados pelo princípio
da neutralidade.</p>
<p>§ 11. O adquirente deve cumprir a regra. (Redação dada pela Lei Complementar nº 235,
de 2026)</p>
<p>Art. 2º-A. Regra nova. (Incluído pela Lei Complementar nº 227, de 2026)</p>
<p>Art. 10. Texto vigente <strike>trecho revogado</strike> e resto.</p>
<p>CAPÍTULO II</p>
<p>DO IBS E DA CBS SOBRE OPERAÇÕES</p>
<p>Seção I</p>
<p>Das Hipóteses de Incidência</p>
<p>Art. 11. O IBS incide sobre operações.</p>
<p>&ldquo;Art. 1º Texto citado de outra lei.&rdquo;</p>
<p>Art. 1º Linha fora de ordem, mantida no artigo corrente.</p>
<p>Art. 12. (Vetado)</p>
<p><strike>Art. 13. Redação antiga do artigo.</strike></p>
<p>Art. 13. Redação nova do artigo. (Redação dada pela Lei Complementar nº 227, de 2026)</p>
<p>Brasília, 16 de janeiro de 2025; 204º da Independência.</p>
<p>ANEXO I</p>
<p>Art. 99 Não deve entrar.</p>
</body></html>
"""


class LeiTest(unittest.TestCase):
    def setUp(self):
        self.artigos = lei.ler_artigos(HTML.encode("utf-8"))
        self.por_numero = {a.numero: a for a in self.artigos}

    def test_numeros_em_ordem_e_sem_anexo(self):
        numeros = [a.numero for a in self.artigos]
        self.assertEqual(numeros, ["1", "2", "2-A", "10", "11", "12", "13"])

    def test_texto_do_artigo_junta_linhas_do_mesmo_paragrafo(self):
        art2 = self.por_numero["2"].texto
        self.assertIn("princípio da neutralidade", art2)
        self.assertIn("I - o Imposto sobre Bens e Serviços (IBS); e", self.por_numero["1"].texto)

    def test_hierarquia(self):
        art1 = self.por_numero["1"]
        self.assertEqual(
            art1.hierarquia["livro"], "LIVRO I — DO IMPOSTO SOBRE BENS E SERVIÇOS (IBS)"
        )
        self.assertEqual(art1.hierarquia["capitulo"], "CAPÍTULO I — DISPOSIÇÕES PRELIMINARES")
        art11 = self.por_numero["11"]
        self.assertEqual(
            art11.hierarquia["capitulo"], "CAPÍTULO II — DO IBS E DA CBS SOBRE OPERAÇÕES"
        )
        self.assertEqual(art11.hierarquia["secao"], "SEÇÃO I — Das Hipóteses de Incidência")
        self.assertEqual(art11.hierarquia["titulo"], "TÍTULO I — DAS NORMAS GERAIS")

    def test_cabecalho_novo_limpa_niveis_inferiores(self):
        self.assertNotIn("secao", self.por_numero["1"].hierarquia)

    def test_alteracoes_registradas(self):
        art2 = self.por_numero["2"]
        self.assertEqual(len(art2.alteracoes), 1)
        alt = art2.alteracoes[0]
        self.assertEqual(
            (alt.tipo, alt.norma, alt.ano), ("redacao", "Lei Complementar nº 235", 2026)
        )
        incluido = self.por_numero["2-A"].alteracoes[0]
        self.assertEqual(
            (incluido.tipo, incluido.norma, incluido.ano),
            ("incluido", "Lei Complementar nº 227", 2026),
        )

    def test_veto(self):
        art12 = self.por_numero["12"]
        self.assertEqual([a.tipo for a in art12.alteracoes], ["vetado"])
        self.assertIsNone(art12.alteracoes[0].norma)

    def test_trecho_riscado_marcado(self):
        art10 = self.por_numero["10"]
        self.assertTrue(art10.tem_trecho_riscado)
        self.assertIn("⟦trecho revogado⟧", art10.texto)
        self.assertFalse(self.por_numero["1"].tem_trecho_riscado)

    def test_citacao_e_linha_fora_de_ordem_ficam_no_artigo_corrente(self):
        art11 = self.por_numero["11"].texto
        self.assertIn("Texto citado de outra lei", art11)
        self.assertIn("Linha fora de ordem", art11)

    def test_assinatura_e_anexos_ficam_de_fora(self):
        todo = " ".join(a.texto for a in self.artigos)
        self.assertNotIn("204º da Independência", todo)
        self.assertNotIn("Não deve entrar", todo)

    def test_cabecalho_riscado_abre_o_artigo_e_a_redacao_nova_se_junta(self):
        art13 = self.por_numero["13"]
        self.assertTrue(art13.tem_trecho_riscado)
        self.assertIn("⟦Art. 13. Redação antiga do artigo.⟧", art13.texto)
        self.assertIn("Redação nova do artigo.", art13.texto)
        self.assertNotIn("Redação antiga", self.por_numero["12"].texto)

    def test_id_estavel(self):
        self.assertEqual(self.por_numero["2-A"].id, "lc214-art-2-a")

    def test_decodifica_windows_1252(self):
        conteudo = "<p>Art. 1º Disposição preliminar.</p>".encode("cp1252")
        artigos = lei.ler_artigos(conteudo)
        self.assertEqual(artigos[0].texto, "Art. 1º Disposição preliminar.")

    def test_anotacao_com_decreto(self):
        alt = lei.extrair_alteracoes("texto (Vide Decreto nº 12.955, de 2026)")
        self.assertEqual(
            (alt[0].tipo, alt[0].norma, alt[0].ano), ("vide", "Decreto nº 12.955", 2026)
        )


if __name__ == "__main__":
    unittest.main()
