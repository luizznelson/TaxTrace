import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from taxtrace.avaliacao import (
    avaliar,
    carregar_casos,
    main,
    pontuar,
    pontuar_trechos,
    resumir,
    verificar_trechos,
)


class MetricasTest(unittest.TestCase):
    @staticmethod
    def conjunto(casos):
        return {
            "schema": 1,
            "casos": casos,
            "manifesto_sha256": "a" * 64,
            "fonte_sha256": "b" * 64,
            "fonte_url": "https://example.invalid/lei",
            "limites": ["fixture sintética"],
        }

    def test_outra_coleta_interrompe_sem_medir(self):
        conn = MagicMock()
        with patch(
            "taxtrace.avaliacao.pesquisar", return_value={"coleta": {"manifesto_sha256": "c" * 64}}
        ) as busca:
            with self.assertRaisesRegex(ValueError, "outra_coleta"):
                avaliar(conn, self.conjunto([]))
            self.assertEqual(busca.call_count, 1)

    def test_fragmento_incorreto_interrompe_antes_das_perguntas(self):
        conn = MagicMock()
        conn.execute.return_value.fetchone.return_value = ("texto real",)
        caso = {"esperados": ["1"], "evidencias": {"1": "texto inventado"}}
        with patch(
            "taxtrace.avaliacao.pesquisar",
            return_value={"coleta": {"id": 1, "manifesto_sha256": "a" * 64}},
        ) as busca:
            with self.assertRaisesRegex(ValueError, "evidencia_do_gabarito"):
                avaliar(conn, self.conjunto([caso]))
            self.assertEqual(busca.call_count, 1)

    def test_falha_operacional_nao_grava_resultado_nem_expoe_conexao(self):
        with tempfile.TemporaryDirectory() as pasta:
            saida = io.StringIO()
            with (
                patch("taxtrace.avaliacao.Path.cwd", return_value=Path(pasta)),
                patch("taxtrace.avaliacao.carregar_casos", return_value=({}, "hash")),
                patch("taxtrace.avaliacao.conectar", side_effect=RuntimeError("segredo")),
                contextlib.redirect_stdout(saida),
            ):
                self.assertEqual(main([]), 1)
            self.assertNotIn("segredo", saida.getvalue())
            self.assertEqual(json.loads(saida.getvalue())["status"], "avaliacao_nao_concluida")
            self.assertFalse((Path(pasta) / "runs").exists())

    def test_ranking_parcial_e_duplicatas(self):
        resultado = pontuar(["125", "127"], ["4", "125", "125"])
        self.assertEqual(resultado["recall_referencias"], 0.5)
        self.assertEqual(resultado["reciproco_primeiro_relevante"], 0.5)

    def test_sem_correspondencia_nao_pontua(self):
        self.assertFalse(pontuar(["125"], ["4"])["acertou"])
        self.assertEqual(pontuar(["125"], [])["recall_referencias"], 0)

    def test_controles_nao_inflam_metrica_de_artigos(self):
        caso = {"tipo": "artigo", **pontuar(["125"], []), "encontrados": []}
        controle = {"tipo": "controle_sem_resultado", "encontrados": []}
        resumo = resumir([caso, controle, controle])
        self.assertEqual(resumo["hit_at_k"], 0)
        self.assertEqual(resumo["controles_corretos"], 2)
        self.assertIsNone(resumir([controle])["mrr_at_k"])

    def test_gabarito_invalido_recusado(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "casos.json"
            caso = {
                "id": "a",
                "tipo": "artigo",
                "categoria": "termos",
                "consulta": "termos",
                "esperados": ["1"],
            }
            caminho.write_text(json.dumps(self.conjunto([caso])), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "evidencia_obrigatoria"):
                carregar_casos(caminho)
            caso["evidencias"] = {"1": "trecho"}
            caminho.write_text(json.dumps(self.conjunto([caso, caso])), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicado"):
                carregar_casos(caminho)


if __name__ == "__main__":
    unittest.main()


class TrechosTest(unittest.TestCase):
    def test_artigo_correto_sem_ancora_nao_conta_como_trecho_util(self):
        caso = {"esperados": ["1"], "evidencias": {"1": "base esperada"}}
        r = pontuar_trechos(caso, [{"artigo_numero": "1", "trecho": "outro trecho do artigo"}])
        self.assertFalse(r["hit_ancora_no_trecho"])
        self.assertEqual(r["suficiencia_para_resposta"], "nao_avaliada")

    def test_ancora_em_artigo_errado_ou_chave_extra_nao_inflam_resultado(self):
        caso = {"esperados": ["1"], "evidencias": {"1": "ancora", "2": "ancora"}}
        r = pontuar_trechos(caso, [{"artigo_numero": "2", "trecho": "ancora"}])
        self.assertFalse(r["hit_ancora_no_trecho"])
        self.assertEqual(r["ancoras_literais_exibidas"], {"1": False})

    def test_ancora_literal_correta_nao_comprova_suficiencia(self):
        r = pontuar_trechos(
            {"esperados": ["1"], "evidencias": {"1": "regra"}},
            [{"artigo_numero": "1", "trecho": "A regra inclui ressalvas."}],
        )
        self.assertTrue(r["hit_ancora_no_trecho"])
        self.assertEqual(r["suficiencia_para_resposta"], "nao_avaliada")

    def test_trecho_inventado_ou_vazio_interrompe_verificacao(self):
        conn = MagicMock()
        conn.execute.return_value.fetchone.return_value = ("texto da fonte",)
        for trecho in ("inventado", "", None):
            with (
                self.subTest(trecho=trecho),
                self.assertRaisesRegex(ValueError, "trecho_nao_confere"),
            ):
                verificar_trechos(conn, 1, [{"artigo_numero": "1", "trecho": trecho}])

    def test_offset_incorreto_nao_e_aceito_mesmo_com_trecho_literal(self):
        conn = MagicMock()
        conn.execute.return_value.fetchone.return_value = ("abc def",)
        item = {
            "artigo_numero": "1",
            "trecho": "def",
            "tipo_trecho": "fragmento_semantico",
            "inicio": 0,
            "fim": 3,
        }
        with self.assertRaisesRegex(ValueError, "offsets_do_trecho"):
            verificar_trechos(conn, 1, [item])
