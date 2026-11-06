import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_tabelas import montar

from taxtrace import conexao
from taxtrace.documentos import texto_ativo
from taxtrace.integridade import verificar


class IsolamentoTest(unittest.TestCase):
    def test_teste_nao_usa_conexao_de_desenvolvimento_ou_neon(self):
        casos = [
            {},
            {
                "TAXTRACE_TEST_DATABASE_URL": "postgresql://taxtrace_test:example@remote.neon.tech:15434/"
                "taxtrace_test"
            },
            {
                "TAXTRACE_TEST_DATABASE_URL": "postgresql://taxtrace_test:example@localhost:15434/taxtrace"
            },
            {
                "TAXTRACE_TEST_DATABASE_URL": "postgresql://taxtrace:example@localhost:15434/taxtrace_test"
            },
            {
                "TAXTRACE_TEST_DATABASE_URL": "postgresql://taxtrace_test:example@localhost:5432/taxtrace_test"
            },
            {
                "TAXTRACE_TEST_DATABASE_URL": (
                    "host=localhost hostaddr=203.0.113.2 port=15434 "
                    "user=taxtrace_test dbname=taxtrace_test"
                )
            },
        ]
        for caso in casos:
            with (
                self.subTest(caso=list(caso)),
                patch.dict(
                    os.environ,
                    {
                        "DATABASE_URL": "postgresql://owner:example@remote.neon.tech/production",
                        "TAXTRACE_TEST_DATABASE": "1",
                        **caso,
                    },
                    clear=True,
                ),
                patch.object(conexao, "load_dotenv"),
                patch.object(conexao.psycopg, "connect") as conectar,
            ):
                with self.assertRaises(ValueError):
                    conexao.conectar(Path.cwd(), teste=True)
                conectar.assert_not_called()

    def test_sem_opt_in_e_leitura_com_administrador_sao_recusados(self):
        with (
            patch.dict(
                os.environ,
                {
                    "TAXTRACE_READER_DATABASE_URL": "postgresql://taxtrace:example@localhost:15433/taxtrace"
                },
                clear=True,
            ),
            patch.object(conexao, "load_dotenv"),
        ):
            with self.assertRaisesRegex(ValueError, "opt_in"):
                conexao.opcoes(Path.cwd(), teste=True)
            with self.assertRaisesRegex(ValueError, "login_restrito"):
                conexao.opcoes(Path.cwd(), leitura=True)

    def test_hash_alterado_e_manifesto_com_travessia_sao_recusados(self):
        with tempfile.TemporaryDirectory() as temporario:
            pasta = Path(temporario)
            montar(pasta)
            verificar(pasta)
            caminho = pasta / "ncm_vigentes.json"
            original = caminho.read_bytes()
            caminho.write_bytes(original + b" ")
            with self.assertRaisesRegex(ValueError, "integridade"):
                verificar(pasta)
            caminho.write_bytes(original)
            manifesto = json.loads((pasta / "manifesto.json").read_bytes())
            manifesto["arquivos"][0]["arquivo"] = "../fora.json"
            (pasta / "manifesto.json").write_text(json.dumps(manifesto))
            with self.assertRaisesRegex(ValueError, "arquivo_de_coleta_invalido"):
                verificar(pasta)

    def test_lei_obrigatoria_na_carga(self):
        with tempfile.TemporaryDirectory() as temporario:
            pasta = Path(temporario)
            montar(pasta)
            with self.assertRaisesRegex(ValueError, "fontes_obrigatorias"):
                verificar(pasta, exigir_lei=True)

    def test_texto_riscado_fica_fora_da_busca_sem_excluir_redacao_nova(self):
        self.assertEqual(
            texto_ativo("Atual ⟦antigo ⟦interno⟧ também antigo⟧ texto."), "Atual texto."
        )
        for texto in ("Atual ⟦sem fechar", "Fechado⟧"):
            with self.assertRaises(ValueError):
                texto_ativo(texto)
