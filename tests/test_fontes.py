import gzip
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import psycopg
from psycopg.rows import dict_row
from test_tabelas import atualizar_manifesto, montar

from taxtrace import banco, conexao, fontes
from taxtrace.consultas import resumo_base
from taxtrace.leitura import ler_integral


class SourceArchiveTest(unittest.TestCase):
    def test_exact_bytes_and_corruption_are_checked(self):
        raw = b"<p id='art1'>Art. 1. Fonte sintetica</p>"
        digest = hashlib.sha256(raw).hexdigest()
        blob = gzip.compress(raw, mtime=0)
        self.assertEqual(fontes.descompactar(blob, len(raw), digest), raw)
        for compressed, size, sha in (
            (b"invalid-gzip", len(raw), digest),
            (blob, len(raw), "a" * 64),
            (blob, len(raw) + 1, digest),
        ):
            with self.subTest(size=size), self.assertRaises(ValueError):
                fontes.descompactar(compressed, size, sha)

    def test_decompression_is_bounded_even_with_forged_size(self):
        with patch.object(fontes, "LIMITE", 1024):
            with self.assertRaisesRegex(ValueError, "excede_limite"):
                fontes.descompactar(gzip.compress(b"x" * 1025), 1, "a" * 64)

    def test_old_database_missing_capture_and_divergent_archive_are_distinct(self):
        cur = MagicMock()
        cur.fetchone.return_value = {"tabela": None}
        self.assertIsNone(fontes.ler_fonte_preservada(cur, 1, "lc214_planalto", "a" * 64))
        cur.fetchone.side_effect = [{"tabela": "fontes_preservadas"}, None]
        self.assertIsNone(fontes.ler_fonte_preservada(cur, 1, "lc214_planalto", "a" * 64))
        cur.fetchone.side_effect = [{"tabela": "fontes_preservadas"}, {"sha256": "b" * 64}]
        with self.assertRaisesRegex(ValueError, "divergente"):
            fontes.ler_fonte_preservada(cur, 1, "lc214_planalto", "a" * 64)


@unittest.skipUnless(os.environ.get("TAXTRACE_TEST_DATABASE") == "1", "PostgreSQL isolado opt-in")
class PostgresSourceArchiveTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name)
        montar(self.path)
        self.html = b'<p id="art1">Art. 1. Tributo sobre operacoes.</p>'
        (self.path / "lc214_planalto.html").write_bytes(self.html)
        atualizar_manifesto(self.path)
        path = self.path / "manifesto.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        for source in manifest["arquivos"]:
            if source["nome"] == "lc214_planalto":
                source["url"] = "https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214.htm"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        self.conn = conexao.conectar(Path.cwd(), teste=True)
        self.addCleanup(self.conn.close)
        self.addCleanup(self.conn.rollback)
        banco.criar_esquema(self.conn)
        banco.preparar_leitor(self.conn, "isolated-source-test-only")
        self.cid = banco.carregar_pasta(self.conn, self.path)

    def report(self):
        self.conn.execute("SET LOCAL ROLE taxtrace_reader")
        base = resumo_base(self.conn, self.cid)
        return {
            "estado": {
                "coleta": base["coleta"],
                "respostas": {
                    "base": base,
                    "consulta": {"status": "artigo_recuperado", "numero": "1"},
                },
            },
            "pacote_revisao": {"dossie_sha256": "c" * 64},
        }

    def test_captures_are_idempotent_and_reader_works_without_local_files(self):
        self.assertEqual(fontes.preservar(self.conn, self.cid, self.path), 7)
        self.assertEqual(
            self.conn.execute(
                "SELECT count(*) FROM fontes_preservadas WHERE coleta_id=%s", (self.cid,)
            ).fetchone()[0],
            7,
        )
        with self.conn.cursor(row_factory=dict_row) as cur:
            manifesto_raw = (self.path / "manifesto.json").read_bytes()
            self.assertEqual(
                fontes.ler_fonte_preservada(
                    cur, self.cid, "manifesto", hashlib.sha256(manifesto_raw).hexdigest()
                ),
                manifesto_raw,
            )
        report = self.report()
        result = ler_integral(self.conn, report, "1", self.path / "no-local-data")
        self.assertEqual(result["citacao"]["url"].split("#")[1], "art1")
        self.assertEqual(result["localizacao_oficial"], "ancora_verificada_na_coleta")
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            with self.conn.transaction():
                self.conn.execute("DELETE FROM fontes_preservadas WHERE coleta_id=%s", (self.cid,))

    def test_corruption_fails_without_using_local_fallback(self):
        self.conn.execute(
            "UPDATE fontes_preservadas SET conteudo_gzip=%s "
            "WHERE coleta_id=%s AND nome='lc214_planalto'",
            (b"invalid-gzip", self.cid),
        )
        report = self.report()
        with patch("taxtrace.leitura.ancoras_verificadas") as local:
            with self.assertRaisesRegex(ValueError, "fonte_preservada"):
                ler_integral(self.conn, report, "1", self.path)
            local.assert_not_called()

    def test_different_manifest_does_not_overwrite_snapshot(self):
        (self.path / "lc214_planalto.html").write_bytes(b"Art. 1. Conteudo diferente")
        atualizar_manifesto(self.path)
        with self.assertRaisesRegex(ValueError, "coleta_da_fonte_divergente"):
            fontes.preservar(self.conn, self.cid, self.path)
        with self.conn.cursor(row_factory=dict_row) as cur:
            preserved = fontes.ler_fonte_preservada(
                cur, self.cid, "lc214_planalto", hashlib.sha256(self.html).hexdigest()
            )
        self.assertEqual(preserved, self.html)


if __name__ == "__main__":
    unittest.main()
