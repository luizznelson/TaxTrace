import hashlib
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.parse import unquote

from taxtrace.leitura import ler_integral, link_artigo, paragrafos


class LeituraTest(unittest.TestCase):
    def test_preserva_paragrafos_e_riscado_entre_linhas_sem_interpretar_html(self):
        texto = (
            "Art. 1. Texto.\n§ 1º ⟦antigo\nainda antigo⟧ novo "
            "<script>alert(1)</script>\nI - inciso\na) alínea"
        )
        blocos = paragrafos(texto)
        self.assertEqual(
            [b["tipo"] for b in blocos], ["caput", "paragrafo", "texto", "inciso", "alinea"]
        )
        self.assertEqual(blocos[1]["partes"][-1], {"texto": "antigo", "riscado": True})
        self.assertTrue(blocos[2]["partes"][0]["riscado"])
        self.assertIn("<script>", blocos[2]["partes"][1]["texto"])
        refeito = "\n".join("".join(p["texto"] for p in b["partes"]) for b in blocos)
        self.assertEqual(refeito, texto.replace("⟦", "").replace("⟧", ""))

    def test_marcacoes_invalidas_nao_viram_texto_vigente(self):
        for texto in ("⟦aberto", "fechado⟧"):
            with self.assertRaisesRegex(ValueError, "marcacao_de_redacao_invalida"):
                paragrafos(texto)

    def test_link_usa_ancora_verificada_e_tenta_texto_quando_ausente(self):
        url = "https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214.htm"
        self.assertEqual(link_artigo(url, "125", {"art125"}), url + "#art125")
        self.assertEqual(link_artigo(url, "341-G", {"art341g"}), url + "#art341g")
        self.assertIn("#:~:text=Art. 371.", unquote(link_artigo(url, "371", {"art125"})))
        with self.assertRaises(ValueError):
            link_artigo("https://planalto.gov.br.evil.example/", "125")

    def preparar(self):
        origem = {
            "nome": "lc214_planalto",
            "url": "https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214.htm",
            "sha256": "a" * 64,
        }
        coleta = {"id": 7, "manifesto_sha256": "b" * 64, "fontes": [origem]}
        relatorio = {
            "estado": {
                "coleta": {"id": 7, "manifesto_sha256": "b" * 64},
                "respostas": {
                    "base": {"fontes": [origem]},
                    "consulta": {"resultados": [{"artigo_numero": "125"}]},
                },
            },
            "pacote_revisao": {"dossie_sha256": "c" * 64},
        }
        conn = MagicMock()
        cur = conn.cursor.return_value.__enter__.return_value
        texto = "Art. 125. " + "texto da coleta " * 2200 + "\nParágrafo único. Fim."
        cur.fetchone.return_value = {"texto": texto, "hierarquia": {}, "tem_trecho_riscado": False}
        return conn, cur, coleta, relatorio, texto

    def test_artigo_integral_nao_trunca_e_nao_muda_dossie(self):
        conn, cur, coleta, relatorio, texto = self.preparar()
        with (
            patch("taxtrace.leitura.selecionar_coleta", return_value=coleta) as selecionar,
            patch("taxtrace.leitura.ancoras_verificadas", return_value={"art125"}),
        ):
            r = ler_integral(conn, relatorio, "125", Path("."))
        selecionar.assert_called_once_with(cur, 7)
        self.assertEqual(r["texto"], texto)
        self.assertGreater(r["total_caracteres"], 3000)
        self.assertEqual(r["texto_sha256"], hashlib.sha256(texto.encode()).hexdigest())
        self.assertEqual(r["dossie_sha256"], "c" * 64)
        self.assertEqual(r["citacao"]["url"].split("#")[1], "art125")
        self.assertEqual(r["escopo"], "leitura_complementar_nao_altera_dossie_da_revisao")

    def test_outro_artigo_e_outra_coleta_sao_recusados(self):
        conn, _, coleta, relatorio, _ = self.preparar()
        for numero in ("126", "125; DROP TABLE artigos"):
            with self.assertRaisesRegex(ValueError, "artigo_integral_indisponivel"):
                ler_integral(conn, relatorio, numero, Path("."))
        conn.cursor.assert_not_called()
        coleta["manifesto_sha256"] = "outro"
        with patch("taxtrace.leitura.selecionar_coleta", return_value=coleta):
            with self.assertRaisesRegex(ValueError, "coleta_divergente"):
                ler_integral(conn, relatorio, "125", Path("."))

    def test_fonte_divergente_nao_e_usada_como_contexto(self):
        conn, _, coleta, relatorio, _ = self.preparar()
        relatorio["estado"]["respostas"]["base"]["fontes"] = []
        with patch("taxtrace.leitura.selecionar_coleta", return_value=coleta):
            with self.assertRaisesRegex(ValueError, "fonte_da_leitura_divergente"):
                ler_integral(conn, relatorio, "125", Path("."))
