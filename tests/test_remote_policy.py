import os
import unittest
from pathlib import Path
from unittest.mock import patch

from taxtrace import checkpoints, conexao, remoto

HOST = "ep-taxtrace-test.us-east-2.aws.neon.tech"
CFG = {
    "TAXTRACE_DATABASE_MODE": "neon",
    "TAXTRACE_NEON_HOST": HOST,
    "TAXTRACE_NEON_DATABASE": "taxtrace",
}


class RemotePolicyTest(unittest.TestCase):
    def params(self, role="taxtrace_reader"):
        return {
            "host": HOST,
            "port": "5432",
            "dbname": "taxtrace",
            "user": role,
            "password": "synthetic",
            "sslmode": "require",
        }

    def test_tls_and_role_are_fixed_for_runtime(self):
        with patch.dict(os.environ, CFG, clear=True):
            for role in ("taxtrace_reader", "taxtrace_state"):
                result = remoto.opcoes_neon(self.params(role), role)
                self.assertEqual(result["sslmode"], "verify-full")
                self.assertTrue(Path(result["sslrootcert"]).is_file())
                self.assertEqual(result["channel_binding"], "require")
                self.assertEqual(result["ssl_min_protocol_version"], "TLSv1.2")

    def test_wrong_host_pooling_overrides_and_weak_tls_are_rejected(self):
        for changes in (
            {"host": "remote.example"},
            {"host": HOST + ".evil.example"},
            {"host": HOST.replace(".us-east", "-pooler.us-east")},
            {"host": "127.0.0.1"},
            {"hostaddr": "203.0.113.2"},
            {"user": "neondb_owner"},
            {"dbname": "other"},
            {"port": "15433"},
            {"sslmode": "disable"},
            {"sslmode": "prefer"},
            {"channel_binding": "disable"},
            {"password": ""},
            {"sslrootcert": "/tmp/untrusted-ca"},
            {"options": "-c search_path=public"},
            {"service": "remote"},
        ):
            with self.subTest(changes=list(changes)), patch.dict(os.environ, CFG, clear=True):
                with self.assertRaisesRegex(ValueError, "destino_remoto_nao_permitido"):
                    remoto.opcoes_neon({**self.params(), **changes}, "taxtrace_reader")

    def test_endpoint_requires_explicit_neon_mode_and_exact_pin(self):
        for override in (
            {"TAXTRACE_DATABASE_MODE": "local"},
            {"TAXTRACE_NEON_HOST": ""},
            {"TAXTRACE_NEON_HOST": "ep-other.us-east-2.aws.neon.tech"},
            {"TAXTRACE_NEON_DATABASE": "other"},
        ):
            with patch.dict(os.environ, {**CFG, **override}, clear=True):
                with self.assertRaises(ValueError):
                    remoto.opcoes_neon(self.params(), "taxtrace_reader")

    def test_reader_and_checkpoint_use_policy_without_enabling_remote_maintenance(self):
        cfg = {
            **CFG,
            "TAXTRACE_READER_DATABASE_URL": f"postgresql://taxtrace_reader:synthetic@{HOST}/taxtrace?sslmode=require",
            "TAXTRACE_CHECKPOINT_DATABASE_URL": f"postgresql://taxtrace_state:synthetic@{HOST}/taxtrace?sslmode=require",
            "DATABASE_URL": f"postgresql://owner:synthetic@{HOST}/taxtrace?sslmode=require",
        }
        with (
            patch.dict(os.environ, cfg, clear=True),
            patch.object(conexao, "load_dotenv"),
            patch.object(checkpoints, "load_dotenv"),
        ):
            self.assertEqual(conexao.opcoes(Path.cwd(), leitura=True)["sslmode"], "verify-full")
            self.assertEqual(checkpoints.parametros(Path.cwd())["sslmode"], "verify-full")
            with self.assertRaisesRegex(ValueError, "somente_banco_local"):
                conexao.opcoes(Path.cwd())
            with self.assertRaises(ValueError):
                conexao.opcoes(Path.cwd(), teste=True)
            forwarded = conexao.ambiente_mcp(Path.cwd())
            self.assertEqual(forwarded["TAXTRACE_NEON_HOST"], HOST)
            self.assertEqual(forwarded["TAXTRACE_NEON_DATABASE"], "taxtrace")
            self.assertNotIn("TAXTRACE_CHECKPOINT_DATABASE_URL", forwarded)
            self.assertNotIn("DATABASE_URL", forwarded)


if __name__ == "__main__":
    unittest.main()
