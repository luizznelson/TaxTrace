import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import psycopg
from filelock import Timeout
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg.rows import dict_row
from test_agente import ClienteFake

from taxtrace import checkpoints, conexao, revisao


class ConfigCheckpointTest(unittest.TestCase):
    def test_backend_default_and_invalid_value(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(checkpoints, "load_dotenv"):
            self.assertEqual(checkpoints.backend(Path.cwd()), "sqlite")
            os.environ["TAXTRACE_CHECKPOINT_BACKEND"] = "unknown"
            with self.assertRaisesRegex(ValueError, "backend_de_checkpoint_invalido"):
                checkpoints.backend(Path.cwd())

    def test_role_and_destination_are_restricted_without_fallback(self):
        for url, mode, allowed in (
            ("postgresql://taxtrace_state:synthetic@127.0.0.1:15433/taxtrace", "local", True),
            ("postgresql://taxtrace_state:synthetic@db:5432/taxtrace", "compose", True),
            ("postgresql://taxtrace_state:synthetic@db:5432/taxtrace", "local", False),
            ("postgresql://owner:synthetic@127.0.0.1:15433/taxtrace", "local", False),
            (
                "postgresql://taxtrace_state:synthetic@remote.neon.tech:5432/taxtrace",
                "local",
                False,
            ),
            ("postgresql://taxtrace_state:synthetic@127.0.0.1:15434/taxtrace_test", "local", False),
            (
                "host=localhost hostaddr=203.0.113.2 port=15433 "
                "user=taxtrace_state dbname=taxtrace",
                "local",
                False,
            ),
            (
                "host=localhost port=15433 user=taxtrace_state dbname=taxtrace "
                "options='-c search_path=public'",
                "local",
                False,
            ),
        ):
            with (
                self.subTest(url=url),
                patch.dict(
                    os.environ,
                    {"TAXTRACE_CHECKPOINT_DATABASE_URL": url, "TAXTRACE_DATABASE_MODE": mode},
                    clear=True,
                ),
                patch.object(checkpoints, "load_dotenv"),
            ):
                if allowed:
                    self.assertEqual(
                        checkpoints.parametros(Path.cwd())["options"], checkpoints.OPTIONS
                    )
                else:
                    with self.assertRaisesRegex(ValueError, "destino_de_checkpoint_nao_permitido"):
                        checkpoints.parametros(Path.cwd())

    def test_missing_dsn_is_not_replaced_by_admin_or_reader_connection(self):
        with (
            patch.dict(
                os.environ,
                {"DATABASE_URL": "PRIVATE_ADMIN", "TAXTRACE_READER_DATABASE_URL": "PRIVATE_READER"},
                clear=True,
            ),
            patch.object(checkpoints, "load_dotenv"),
        ):
            with self.assertRaisesRegex(ValueError, "conexao_de_checkpoint_invalida"):
                checkpoints.parametros(Path.cwd())


class CheckpointControlTest(unittest.IsolatedAsyncioTestCase):
    async def test_lock_collision_closes_connection_before_yield(self):
        conn = AsyncMock()
        conn.__aenter__.return_value = conn
        cursor = AsyncMock()
        cursor.fetchone.return_value = {"obteve": False}
        conn.execute.return_value = cursor
        with (
            patch.object(checkpoints, "sys", SimpleNamespace(platform="linux")),
            patch.object(checkpoints, "parametros", return_value={}),
            patch.object(checkpoints.psycopg.AsyncConnection, "connect", return_value=conn),
        ):
            with self.assertRaises(Timeout):
                async with checkpoints.abrir_postgres(Path.cwd(), str(uuid4())):
                    self.fail("Lock ocupado não pode entregar um saver")
        conn.__aexit__.assert_awaited_once()

    async def test_event_is_written_to_database_without_local_run_files(self):
        conn = AsyncMock()
        snapshot = {
            "revisao_id": str(uuid4()),
            "estado": {"pergunta": "Dado público sintético", "numero": -0.0},
        }
        with tempfile.TemporaryDirectory() as tmp, patch.object(revisao, "registrar") as local:
            result = await revisao.persistir_registro(Path(tmp), snapshot, "inspecionar", conn)
            local.assert_not_called()
            self.assertEqual(list(Path(tmp).iterdir()), [])
        self.assertTrue(result["registro"].startswith("postgres:evento:"))
        args = conn.execute.call_args.args[1]
        document = json.loads(args[3])

        encoded = json.dumps(document, ensure_ascii=False, sort_keys=True, default=str).encode()
        self.assertEqual(args[4], hashlib.sha256(encoded).hexdigest())
        self.assertIn("-0.0", args[3])
        self.assertEqual(args[4], hashlib.sha256(args[3].encode()).hexdigest())

    async def test_postgres_failure_does_not_open_sqlite(self):
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.object(revisao, "backend", return_value="postgres"),
            patch.object(checkpoints, "sys", SimpleNamespace(platform="linux")),
            patch.object(checkpoints, "parametros", return_value={}),
            patch.object(
                checkpoints.psycopg.AsyncConnection,
                "connect",
                side_effect=RuntimeError("PRIVATE_CONNECTION"),
            ),
        ):
            with self.assertRaises(RuntimeError):
                await revisao.inspecionar(str(uuid4()), raiz=Path(tmp))
            self.assertEqual(list(Path(tmp).iterdir()), [])


@unittest.skipUnless(
    os.environ.get("TAXTRACE_TEST_DATABASE") == "1" and sys.platform != "win32",
    "PostgreSQL isolado opt-in, execução Linux",
)
class PostgresCheckpointTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        params = {**conexao.opcoes(Path.cwd(), teste=True), "options": checkpoints.OPTIONS}
        self.conn = await psycopg.AsyncConnection.connect(
            **params, autocommit=True, prepare_threshold=0, row_factory=dict_row
        )
        self.addAsyncCleanup(self.conn.close)
        await checkpoints.preparar_estruturas(self.conn)
        self.enterContext(patch.object(revisao, "backend", return_value="postgres"))
        self.enterContext(patch.object(checkpoints, "parametros", return_value=params))
        self.ids = []

    async def asyncTearDown(self):
        for rid in self.ids:
            await AsyncPostgresSaver(self.conn).adelete_thread(rid)
            await self.conn.execute("DELETE FROM eventos_revisao WHERE revisao_id=%s", (rid,))

    async def new(self):
        client = ClienteFake()
        result = await revisao.iniciar("cesta basica", raiz=self.root, cliente=client)
        self.ids.append(result["revisao_id"])
        return result, client

    def decision(self, result):
        return {
            "decisao": "rejeitar",
            "revisor": "Revisor sintético",
            "motivo": "Teste de persistência",
            "origem": "teste_automatizado",
            "dossie_sha256": result["pacote_revisao"]["dossie_sha256"],
        }

    async def test_resume_across_connections_without_tools_and_with_events(self):
        initial, client = await self.new()
        self.assertTrue(initial["pendente"])
        saved = await revisao.inspecionar(initial["revisao_id"], raiz=self.root)
        final = await revisao.decidir(initial["revisao_id"], self.decision(saved), raiz=self.root)
        self.assertEqual(final["status"], "revisao_documental_rejeitada")
        self.assertEqual(len(client.calls), 3)
        self.assertEqual(list(self.root.iterdir()), [])
        rows = await self.conn.execute(
            "SELECT operacao FROM eventos_revisao WHERE revisao_id=%s ORDER BY registrado_em",
            (initial["revisao_id"],),
        )
        self.assertEqual(
            [r["operacao"] for r in await rows.fetchall()], ["iniciar", "inspecionar", "decidir"]
        )
        with self.assertRaisesRegex(ValueError, "revisao_nao_pendente"):
            await revisao.decidir(initial["revisao_id"], self.decision(saved), raiz=self.root)

    async def test_two_connections_cannot_decide_same_review_concurrently(self):
        initial, _ = await self.new()
        async with checkpoints.abrir_postgres(self.root, initial["revisao_id"]):
            with self.assertRaises(Timeout):
                await revisao.decidir(initial["revisao_id"], self.decision(initial), raiz=self.root)
        self.assertTrue(
            (await revisao.inspecionar(initial["revisao_id"], raiz=self.root))["pendente"]
        )

    async def test_hash_mismatch_does_not_consume_pending_review(self):
        initial, _ = await self.new()
        bad = {**self.decision(initial), "dossie_sha256": "f" * 64}
        with self.assertRaisesRegex(ValueError, "dossie_da_decisao_divergente"):
            await revisao.decidir(initial["revisao_id"], bad, raiz=self.root)
        self.assertTrue(
            (await revisao.inspecionar(initial["revisao_id"], raiz=self.root))["pendente"]
        )


if __name__ == "__main__":
    unittest.main()
