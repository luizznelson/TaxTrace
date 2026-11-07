import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from taxtrace import conexao
from taxtrace.web import criar_app


class ContainerRuntimeTest(unittest.TestCase):
    def options(self, url, mode=None, leitura=True, teste=False):
        cfg = {
            "TAXTRACE_READER_DATABASE_URL": url,
            "DATABASE_URL": url,
            "TAXTRACE_TEST_DATABASE_URL": url,
            "TAXTRACE_TEST_DATABASE": "1",
        }
        if mode:
            cfg["TAXTRACE_DATABASE_MODE"] = mode
        with patch.dict(os.environ, cfg, clear=True), patch.object(conexao, "load_dotenv"):
            return conexao.opcoes(Path.cwd(), leitura=leitura, teste=teste)

    def test_compose_reader_requires_explicit_mode_and_keeps_read_only(self):
        url = "postgresql://taxtrace_reader:synthetic@db:5432/taxtrace"
        with self.assertRaisesRegex(ValueError, "somente_banco_local"):
            self.options(url)
        params = self.options(url, "compose")
        self.assertEqual(params["host"], "db")
        self.assertIn("default_transaction_read_only=on", params["options"])
        self.assertIn("statement_timeout=5000", params["options"])
        self.assertEqual(params["connect_timeout"], 5)
        with self.assertRaises(ValueError):
            self.options(url, "compose", leitura=False)

    def test_compose_does_not_allow_arbitrary_host_port_database_or_admin(self):
        for url in (
            "postgresql://taxtrace_reader:x@remote.example:5432/taxtrace",
            "postgresql://taxtrace_reader:x@db:15433/taxtrace",
            "postgresql://taxtrace_reader:x@db:5432/production",
            "postgresql://taxtrace:x@db:5432/taxtrace",
            "host=db hostaddr=203.0.113.2 port=5432 user=taxtrace_reader dbname=taxtrace",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                self.options(url, "compose")

    def test_compose_does_not_relax_test_database_isolation(self):
        with self.assertRaisesRegex(ValueError, "teste_exige_banco_local_isolado"):
            self.options(
                "postgresql://taxtrace_test:x@db:5432/taxtrace_test", "compose", teste=True
            )

    def test_mcp_inherits_reader_configuration_without_other_secrets(self):
        cfg = {
            "TAXTRACE_DATABASE_MODE": "compose",
            "TAXTRACE_READER_DATABASE_URL": "postgresql://taxtrace_reader:synthetic@db:5432/taxtrace",
            "DATABASE_URL": "PRIVATE_ADMIN_CONNECTION",
            "GEMINI_API_KEY": "PRIVATE_MODEL_KEY",
            "TAXTRACE_READER_PASSWORD": "PRIVATE_PASSWORD",
            "OTHER_SECRET": "PRIVATE_OTHER",
        }
        with patch.dict(os.environ, cfg, clear=True), patch.object(conexao, "load_dotenv"):
            forwarded = conexao.ambiente_mcp(Path.cwd())
        self.assertEqual(
            set(forwarded),
            {"PYTHONIOENCODING", "TAXTRACE_DATABASE_MODE", "TAXTRACE_READER_DATABASE_URL"},
        )
        self.assertEqual(
            forwarded["TAXTRACE_READER_DATABASE_URL"], cfg["TAXTRACE_READER_DATABASE_URL"]
        )
        self.assertNotIn("PRIVATE_", str(forwarded))

    def test_model_availability_uses_runtime_environment_without_exposing_key(self):
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.dict(os.environ, {"GEMINI_API_KEY": "PRIVATE_SYNTHETIC_KEY"}, clear=True),
        ):
            with TestClient(criar_app(Path(tmp)), base_url="http://127.0.0.1") as client:
                result = client.get("/api/contexto")
        self.assertTrue(result.json()["gemini_disponivel"])
        self.assertTrue(result.json()["rag_disponivel"])
        self.assertNotIn("PRIVATE_SYNTHETIC_KEY", result.text)


if __name__ == "__main__":
    unittest.main()
