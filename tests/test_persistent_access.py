import json
import os
import secrets
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

import psycopg
from fastapi.testclient import TestClient
from psycopg.rows import dict_row

from taxtrace import checkpoints, conexao, propriedade
from taxtrace.autenticacao import AcessoRevisor, criar_credencial
from taxtrace.propriedade import COOKIE_VISITANTE, Propriedade, PropriedadePostgres, dono
from taxtrace.web import criar_app


class PersistentAccessTest(unittest.TestCase):
    def test_factory_uses_same_backend_as_checkpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(propriedade, "backend", return_value="postgres"):
                self.assertIsInstance(propriedade.criar_propriedade(tmp), PropriedadePostgres)
            with patch.object(propriedade, "backend", return_value="sqlite"):
                self.assertIsInstance(propriedade.criar_propriedade(tmp), Propriedade)
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_bad_inputs_do_not_open_database(self):
        with patch.object(propriedade.psycopg, "connect") as connect:
            store = PropriedadePostgres(Path.cwd())
            for rid, owner in [("../../private", "a" * 64), (str(uuid4()), None), (None, "a" * 64)]:
                self.assertFalse(store.permite(rid, owner))
                with self.assertRaises(ValueError):
                    store.vincular(rid, owner)
            connect.assert_not_called()

    def test_postgres_failure_does_not_use_an_existing_sqlite_permission(self):
        rid, owner = str(uuid4()), dono(secrets.token_hex(32))
        with tempfile.TemporaryDirectory() as tmp:
            local = Propriedade(tmp)
            local.vincular(rid, owner)
            before = local.caminho.read_bytes()
            with patch.object(
                PropriedadePostgres, "_conectar", side_effect=RuntimeError("PRIVATE_DSN")
            ):
                with self.assertRaises(RuntimeError):
                    PropriedadePostgres(tmp).permite(rid, owner)
            self.assertEqual(local.caminho.read_bytes(), before)

    def test_conflicting_owner_cannot_bind(self):
        conn, cursor = MagicMock(), MagicMock()
        conn.__enter__.return_value = conn
        conn.cursor.return_value.__enter__.return_value = cursor
        cursor.fetchone.return_value = {"dono": "b" * 64}
        with patch.object(PropriedadePostgres, "_conectar", return_value=conn):
            with self.assertRaisesRegex(ValueError, "outra_sessao"):
                PropriedadePostgres(Path.cwd()).vincular(str(uuid4()), "a" * 64)


class CredentialConfigurationTest(unittest.TestCase):
    def test_configured_hash_survives_new_instance_without_file_or_key_disclosure(self):
        password = "senha-sintetica-de-configuracao"
        credential = criar_credencial("teste.env", "Revisor sintético", password)
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.dict(os.environ, {"TAXTRACE_REVIEWER_CREDENTIAL_JSON": json.dumps(credential)}),
        ):
            root = Path(tmp)
            for _ in range(2):
                AcessoRevisor(root).verificar("teste.env", password)
            with TestClient(criar_app(root), base_url="http://127.0.0.1") as client:
                context = client.get("/api/contexto")
                self.assertTrue(context.json()["acesso"]["configurado"])
                self.assertNotIn(credential["hash"], context.text)
                self.assertNotIn(password, context.text)
            self.assertEqual(list(root.iterdir()), [])

    def test_explicit_configuration_has_priority_but_invalid_configuration_fails_closed(self):
        credential = criar_credencial(
            "teste.local", "Revisor sintético", "senha-sintetica-do-arquivo"
        )
        configured = criar_credencial(
            "teste.env", "Revisor configurado", "senha-sintetica-da-configuracao"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "data/checkpoints/revisor.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(credential), encoding="utf-8")
            original = path.read_bytes()
            with patch.dict(
                os.environ, {"TAXTRACE_REVIEWER_CREDENTIAL_JSON": json.dumps(configured)}
            ):
                self.assertEqual(AcessoRevisor(root).credencial["conta"], "teste.env")
            for value in (
                "PRIVATE_INVALID_JSON",
                "[]",
                json.dumps({**credential, "versao": True}),
                json.dumps({**credential, "senha": "PRIVATE_PASSWORD"}),
            ):
                with patch.dict(os.environ, {"TAXTRACE_REVIEWER_CREDENTIAL_JSON": value}):
                    with self.assertRaisesRegex(ValueError, "^credencial_de_revisor_invalida$"):
                        AcessoRevisor(root)
            with patch.dict(os.environ, {"TAXTRACE_REVIEWER_CREDENTIAL_JSON": ""}):
                self.assertEqual(AcessoRevisor(root).credencial["conta"], "teste.local")
            self.assertEqual(path.read_bytes(), original)


@unittest.skipUnless(
    os.environ.get("TAXTRACE_TEST_DATABASE") == "1" and sys.platform != "win32",
    "PostgreSQL isolado opt-in, execução Linux",
)
class PostgresAccessIntegrationTest(unittest.IsolatedAsyncioTestCase):
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
        self.enterContext(patch.object(propriedade, "parametros", return_value=params))
        self.enterContext(patch.object(propriedade, "backend", return_value="postgres"))
        self.ids = []

    async def asyncTearDown(self):
        for rid in self.ids:
            await self.conn.execute("DELETE FROM acessos_revisao WHERE revisao_id=%s", (rid,))

    def rid(self):
        rid = str(uuid4())
        self.ids.append(rid)
        return rid

    async def test_two_owners_racing_have_only_one_winner_and_do_not_renew_expiration(self):
        rid = self.rid()
        owners = [dono(secrets.token_hex(32)) for _ in range(2)]

        def bind(owner):
            try:
                PropriedadePostgres(self.root).vincular(rid, owner)
                return owner
            except ValueError:
                return None

        with ThreadPoolExecutor(max_workers=2) as pool:
            winners = [owner for owner in pool.map(bind, owners) if owner]
        self.assertEqual(len(winners), 1)
        cur = await self.conn.execute(
            "SELECT expira_em FROM acessos_revisao WHERE revisao_id=%s", (rid,)
        )
        before = (await cur.fetchone())["expira_em"]
        PropriedadePostgres(self.root).vincular(rid, winners[0])
        cur = await self.conn.execute(
            "SELECT expira_em FROM acessos_revisao WHERE revisao_id=%s", (rid,)
        )
        self.assertEqual((await cur.fetchone())["expira_em"], before)
        for owner in owners:
            self.assertEqual(
                PropriedadePostgres(self.root).permite(rid, owner), owner == winners[0]
            )

    async def test_new_store_keeps_permission_and_expiration_uses_database_clock(self):
        rid, owner = self.rid(), dono(secrets.token_hex(32))
        PropriedadePostgres(self.root).vincular(rid, owner)
        self.assertTrue(PropriedadePostgres(self.root).permite(rid, owner))
        await self.conn.execute(
            "UPDATE acessos_revisao SET expira_em=clock_timestamp()-interval '1 second' "
            "WHERE revisao_id=%s",
            (rid,),
        )
        self.assertFalse(PropriedadePostgres(self.root).permite(rid, owner))
        self.assertEqual(list(self.root.iterdir()), [])

    async def test_runtime_role_can_bind_but_cannot_change_delete_or_create_tables(self):
        password = "isolated-state-role-test-only"
        params = {**conexao.opcoes(Path.cwd(), teste=True), "options": checkpoints.OPTIONS}
        with (
            patch.object(checkpoints, "opcoes", return_value=params),
            patch.dict(os.environ, {"TAXTRACE_CHECKPOINT_PASSWORD": password}),
        ):
            await checkpoints.preparar(self.root)
        runtime = {**params, "user": "taxtrace_state", "password": password}
        rid, owner = self.rid(), dono(secrets.token_hex(32))
        with patch.object(propriedade, "parametros", return_value=runtime):
            PropriedadePostgres(self.root).vincular(rid, owner)
            self.assertTrue(PropriedadePostgres(self.root).permite(rid, owner))
        for query, values in (
            ("UPDATE acessos_revisao SET dono=%s WHERE revisao_id=%s", ("a" * 64, rid)),
            ("DELETE FROM acessos_revisao WHERE revisao_id=%s", (rid,)),
            ("DELETE FROM eventos_revisao WHERE revisao_id=%s", (rid,)),
            ("CREATE TABLE taxtrace_workflow.nao_permitida (id INT)", ()),
        ):
            with self.subTest(query=query), self.assertRaises(psycopg.errors.InsufficientPrivilege):
                with psycopg.connect(**runtime) as conn:
                    conn.execute(query, values)

    async def test_web_sessions_are_isolated_with_real_postgres_bindings(self):
        app = criar_app(self.root)
        rid = self.rid()
        with (
            TestClient(app, base_url="http://127.0.0.1") as a,
            TestClient(app, base_url="http://127.0.0.1") as b,
        ):
            context = a.get("/api/contexto").json()
            b.get("/api/contexto")
            with patch("taxtrace.web.iniciar", return_value={"revisao_id": rid}):
                result = a.post(
                    "/api/consultas",
                    headers={"X-TaxTrace-CSRF": context["csrf"], "Idempotency-Key": str(uuid4())},
                    json={"pergunta": "Consulta sintética"},
                )
            self.assertEqual(result.status_code, 200)
            with patch("taxtrace.web.inspecionar", return_value={"revisao_id": rid}) as inspect:
                self.assertEqual(a.get(f"/api/revisoes/{rid}").status_code, 200)
                inspect.reset_mock()
                for suffix in ("", "/exportar", "/artigos/125"):
                    self.assertEqual(b.get(f"/api/revisoes/{rid}{suffix}").status_code, 404)
                inspect.assert_not_called()
            self.assertNotEqual(a.cookies.get(COOKIE_VISITANTE), b.cookies.get(COOKIE_VISITANTE))
        self.assertEqual(list(self.root.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
