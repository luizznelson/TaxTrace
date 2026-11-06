import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from taxtrace.encoder import Encoder, janelas, preparar_modelo, vetor_sql
from taxtrace.vetores import validar_fragmentos


class EncoderTest(unittest.TestCase):
    def test_janelas_sobrepostas_cobrem_fim_sem_cruzar_artigos(self):
        texto = "abcdefghijk"
        partes = janelas(texto, [(i, i + 1) for i in range(len(texto))], tamanho=4, sobreposicao=1)
        self.assertEqual([p["texto"] for p in partes], ["abcd", "defg", "ghij", "jk"])
        self.assertEqual(partes[-1]["fim"], len(texto))
        for p in partes:
            self.assertEqual(p["texto"], texto[p["inicio"] : p["fim"]])

    def test_sem_arquivo_nao_tenta_baixar_durante_consulta(self):
        with tempfile.TemporaryDirectory() as pasta:
            with self.assertRaisesRegex(ValueError, "modelo_local_ausente"):
                Encoder(Path(pasta))
            self.assertEqual(list(Path(pasta).iterdir()), [])

    def test_download_com_hash_errado_nao_publica_arquivo(self):
        with tempfile.TemporaryDirectory() as pasta:
            with patch(
                "taxtrace.encoder.urllib.request.urlopen", return_value=io.BytesIO(b"invalido")
            ):
                with self.assertRaisesRegex(ValueError, "hash_do_modelo_divergente"):
                    preparar_modelo(Path(pasta))
            self.assertEqual([p for p in Path(pasta).rglob("*") if p.is_file()], [])

    def test_vetor_recusa_nan_dimensao_errada_e_norma_invalida(self):
        for valores in ([1.0], [0.0] * 384, [float("nan")] * 384, [float("inf")] * 384):
            with self.subTest(tamanho=len(valores)), self.assertRaises(ValueError):
                vetor_sql(valores)
        self.assertEqual(len(json.loads(vetor_sql([1] + [0] * 383))), 384)

    def test_trechos_inventados_ou_com_lacuna_nao_sao_aceitos(self):
        base = {
            "artigo": "1",
            "ordem": 0,
            "inicio": 0,
            "fim": 3,
            "texto": "abc",
            "vetor": [1] + [0] * 383,
        }
        validar_fragmentos([("1", "abc")], [base])
        with self.assertRaisesRegex(ValueError, "trecho_divergente"):
            validar_fragmentos([("1", "xyz")], [base])
        with self.assertRaisesRegex(ValueError, "cobertura_incompleta"):
            validar_fragmentos([("1", "abc falta")], [base])


if __name__ == "__main__":
    unittest.main()
