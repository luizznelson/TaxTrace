import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_tabelas import atualizar_manifesto, montar

from taxtrace import neon

ROOT = Path(__file__).resolve().parent.parent


def empty_inventory():
    return {
        "identificacao": {"banco": "neondb", "papel": "owner", "somente_leitura": "on"},
        "tls_cliente": {"ativo": True},
        "tabelas": [],
        "papeis": [],
        "schema_workflow": [],
        "vector": {"default_version": "0.8.6", "installed_version": None},
    }


class NeonPlanTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name)
        self.capture = self.path / "capture"
        self.capture.mkdir()
        montar(self.capture)
        (self.capture / "lc214_planalto.html").write_text(
            "<p>Art. 1. Texto sintético.</p>", encoding="utf-8"
        )
        atualizar_manifesto(self.capture)
        self.profile = self.path / ".env.neon"
        self.profile.write_text(
            "TAXTRACE_NEON_ADMIN_URL=postgresql://owner:synthetic-admin@ep-taxtrace-test.us-east-2.aws.neon.tech/neondb?sslmode=require\nTAXTRACE_NEON_HOST=ep-taxtrace-test.us-east-2.aws.neon.tech\nTAXTRACE_NEON_DATABASE=neondb\nTAXTRACE_NEON_READER_PASSWORD=synthetic-reader-password\nTAXTRACE_NEON_STATE_PASSWORD=synthetic-state-password\n",
            encoding="utf-8",
        )

    def test_admin_connection_is_readonly_by_default_and_uses_verified_tls(self):
        from dotenv import dotenv_values

        params = neon.parametros_admin(dotenv_values(self.profile))
        self.assertIn("default_transaction_read_only=on", params["options"])
        self.assertEqual(params["sslmode"], "verify-full")
        self.assertEqual(params["channel_binding"], "require")

    def test_plan_is_stable_and_does_not_include_private_values(self):
        with patch.object(neon, "inventario", return_value=empty_inventory()):
            a = neon.plano(ROOT, self.profile, self.capture)
            b = neon.plano(ROOT, self.profile, self.capture)
        self.assertEqual(a["plano_sha256"], b["plano_sha256"])
        for secret in ("synthetic-admin", "synthetic-reader-password", "synthetic-state-password"):
            self.assertNotIn(secret, json.dumps(a))
        self.assertFalse(a["objetos_criados"])

    def test_existing_tables_roles_or_schema_block_provisioning(self):
        for key in ("tabelas", "papeis", "schema_workflow"):
            inventory = {**empty_inventory(), key: [{"existente": "sentinela"}]}
            with self.subTest(key=key), patch.object(neon, "inventario", return_value=inventory):
                with self.assertRaisesRegex(ValueError, "destino_nao_vazio"):
                    neon.plano(ROOT, self.profile, self.capture)

    def test_changed_capture_invalidates_approval_before_database_write(self):
        with patch.object(neon, "inventario", return_value=empty_inventory()):
            approved = neon.plano(ROOT, self.profile, self.capture)["plano_sha256"]
            (self.capture / "lc214_planalto.html").write_text(
                "<p>Art. 1. Mudança sintética.</p>", encoding="utf-8"
            )
            atualizar_manifesto(self.capture)
            with patch.object(neon.psycopg, "connect") as connect:
                with self.assertRaisesRegex(ValueError, "plano_divergente"):
                    neon.aplicar(ROOT, self.profile, self.capture, approved)
                connect.assert_not_called()

    def test_existing_private_runtime_is_never_overwritten(self):
        runtime = self.path / ".env.neon.runtime"
        runtime.write_text("PRIVATE_SENTINEL", encoding="utf-8")
        with (
            patch.object(neon, "plano", return_value={"plano_sha256": "a" * 64}),
            patch.object(neon.psycopg, "connect") as connect,
        ):
            with self.assertRaisesRegex(ValueError, "runtime_privado_existente"):
                neon.aplicar(self.path, self.profile, self.capture, "a" * 64)
            connect.assert_not_called()
        self.assertEqual(runtime.read_text(), "PRIVATE_SENTINEL")


if __name__ == "__main__":
    unittest.main()
