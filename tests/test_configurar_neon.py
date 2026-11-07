import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dotenv import dotenv_values

from taxtrace.configurar_neon import completar


class ConfigurationTest(unittest.TestCase):
    def test_only_uri_is_required_and_generated_passwords_are_preserved(self):
        uri = "postgresql://owner:synthetic-admin@ep-taxtrace-test.us-east-2.aws.neon.tech/neondb?sslmode=require"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env.neon"
            path.write_text("TAXTRACE_NEON_ADMIN_URL=\"psql '" + uri + "'\"\n", encoding="utf-8")
            with patch("psycopg.connect") as connect:
                self.assertFalse(completar(path)["conexao_executada"])
                first = dotenv_values(path)
                completar(path)
                connect.assert_not_called()
            self.assertEqual(first, dotenv_values(path))
            self.assertEqual(
                first["TAXTRACE_NEON_HOST"], "ep-taxtrace-test.us-east-2.aws.neon.tech"
            )
            self.assertEqual(first["TAXTRACE_NEON_DATABASE"], "neondb")
            self.assertNotEqual(
                first["TAXTRACE_NEON_READER_PASSWORD"], first["TAXTRACE_NEON_STATE_PASSWORD"]
            )

    def test_invalid_uri_does_not_modify_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env.neon"
            for value in (
                "PRIVATE_INVALID",
                "postgresql://owner:synthetic@remote.example/db",
                "psql URI; command",
            ):
                path.write_text("TAXTRACE_NEON_ADMIN_URL=" + value, encoding="utf-8")
                before = path.read_bytes()
                with self.assertRaisesRegex(ValueError, "uri_direta"):
                    completar(path)
                self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
