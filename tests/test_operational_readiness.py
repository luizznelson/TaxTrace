import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from taxtrace.avaliar_adversarial import main
from taxtrace.web import criar_app


class ReadinessTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.client = TestClient(criar_app(Path(tmp.name)), base_url="http://127.0.0.1")
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    def test_process_alive_even_when_database_is_down(self):
        with patch("taxtrace.web.conectar", side_effect=RuntimeError("PRIVATE_URL")) as db:
            result = self.client.get("/health/live")
            self.assertEqual(result.status_code, 200)
            db.assert_not_called()
            unavailable = self.client.get("/health/ready")
        self.assertEqual(unavailable.status_code, 503)
        self.assertEqual(unavailable.json(), {"status": "base_indisponivel"})
        self.assertNotIn("PRIVATE_URL", unavailable.text)
        self.assertEqual(unavailable.headers["cache-control"], "no-store")

    def test_ready_requires_loaded_articles_without_model_call(self):
        with (
            patch("taxtrace.web.conectar"),
            patch("taxtrace.web.iniciar") as agent,
            patch("taxtrace.web.resumo_base") as summary,
        ):
            summary.return_value = {"status": "base_disponivel", "contagens": {"artigos": 580}}
            ready = self.client.get("/health/ready")
            self.assertEqual(ready.status_code, 200)
            self.assertEqual(ready.json(), {"status": "pronto"})
            for data in (
                {"status": "base_disponivel", "contagens": {"artigos": 0}},
                {"status": "base_disponivel"},
                {"status": "base_indisponivel", "contagens": {"artigos": 580}},
            ):
                summary.return_value = data
                self.assertEqual(self.client.get("/health/ready").status_code, 503)
            agent.assert_not_called()


class EvaluationCommandTest(unittest.TestCase):
    def test_export_and_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            output = Path(tmp) / "evidence" / "result.json"
            self.assertEqual(main(["--saida", str(output)]), 0)
            original = output.read_bytes()
            report = json.loads(original)
            self.assertEqual(report["chamadas_de_modelo"], 0)
            self.assertEqual(report["resumo"]["bloqueios_corretos"], 10)
            with self.assertRaises(FileExistsError):
                main(["--saida", str(output)])
            self.assertEqual(output.read_bytes(), original)

    def test_mismatch_fails_command_but_preserves_report(self):
        report = {"resumo": {}, "casos": [{"comportamento_estrutural_esperado": False}]}
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch("taxtrace.avaliar_adversarial.avaliar", return_value=report),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            output = Path(tmp) / "failure.json"
            self.assertEqual(main(["--saida", str(output)]), 1)
            self.assertFalse(
                json.loads(output.read_text())["casos"][0]["comportamento_estrutural_esperado"]
            )


if __name__ == "__main__":
    unittest.main()
