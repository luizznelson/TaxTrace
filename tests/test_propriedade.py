import json
import secrets
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from taxtrace.autenticacao import criar_credencial
from taxtrace.propriedade import COOKIE_VISITANTE, VALIDADE, Propriedade, dono
from taxtrace.web import criar_app


class PropriedadeTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.now = 0
        self.store = Propriedade(self.root, relogio=lambda: self.now)
        self.owner = dono(secrets.token_hex(32))
        self.other = dono(secrets.token_hex(32))
        self.rid = str(uuid4())

    def test_binding_is_persistent_and_cannot_be_transferred(self):
        self.assertFalse(self.store.permite(self.rid, self.owner))
        self.store.vincular(self.rid, self.owner)
        self.store.vincular(self.rid, self.owner)
        self.assertTrue(Propriedade(self.root, relogio=lambda: 0).permite(self.rid, self.owner))
        with self.assertRaisesRegex(ValueError, "outra_sessao"):
            self.store.vincular(self.rid, self.other)
        self.assertTrue(self.store.permite(self.rid, self.owner))
        self.assertFalse(self.store.permite(self.rid, self.other))

    def test_expiration_unknown_tokens_and_invalid_bindings(self):
        self.assertIsNone(dono("bad"))
        self.assertIsNone(dono(None))
        self.store.vincular(self.rid, self.owner)
        self.now = VALIDADE
        self.assertFalse(self.store.permite(self.rid, self.owner))
        for rid, owner in [("../other", self.owner), (self.rid, "not-a-hash")]:
            with self.assertRaises(ValueError):
                self.store.vincular(rid, owner)


class SessionIsolationTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        folder = self.root / "data/checkpoints"
        folder.mkdir(parents=True)
        (folder / "revisor.json").write_text(
            json.dumps(
                criar_credencial("teste", "Revisor sintético", "senha-sintetica-para-teste")
            ),
            encoding="utf-8",
        )
        self.app = criar_app(self.root)
        self.a, self.b = self.client(), self.client()

    def client(self, app=None):
        client = TestClient(app or self.app, base_url="http://127.0.0.1")
        client.__enter__()
        self.addCleanup(client.__exit__, None, None, None)
        client.get("/api/contexto")
        return client

    def headers(self, client, key=None):
        return {
            "X-TaxTrace-CSRF": client.get("/api/contexto").json()["csrf"],
            "Idempotency-Key": key or str(uuid4()),
        }

    def create(self, client, key=None):
        rid = str(uuid4())
        with patch("taxtrace.web.iniciar", return_value={"revisao_id": rid}):
            result = client.post(
                "/api/consultas",
                json={"pergunta": "cesta basica"},
                headers=self.headers(client, key),
            )
        self.assertEqual(result.status_code, 200)
        return rid

    def test_cookie_is_private_and_not_in_response_body_or_binding(self):
        fresh = TestClient(self.app, base_url="https://127.0.0.1")
        with fresh:
            response = fresh.get("/api/contexto")
            token = fresh.cookies.get(COOKIE_VISITANTE)
            self.assertNotIn(token, response.text)
            for attribute in ("HttpOnly", "SameSite=strict", "Secure"):
                self.assertIn(attribute, response.headers["set-cookie"])
        rid = self.create(self.a)
        store = Propriedade(self.root)
        self.assertNotIn(self.a.cookies.get(COOKIE_VISITANTE).encode(), store.caminho.read_bytes())
        self.assertTrue(store.permite(rid, dono(self.a.cookies.get(COOKIE_VISITANTE))))

    def test_other_browser_cannot_read_export_or_load_source(self):
        rid = self.create(self.a)
        with patch("taxtrace.web.inspecionar", return_value={"revisao_id": rid}) as inspect:
            self.assertEqual(self.a.get(f"/api/revisoes/{rid}").status_code, 200)
            self.assertEqual(self.a.get(f"/api/revisoes/{rid}/exportar").status_code, 200)
            inspect.reset_mock()
            for suffix in ("", "/exportar", "/artigos/125"):
                response = self.b.get(f"/api/revisoes/{rid}{suffix}")
                self.assertEqual(response.status_code, 404)
                self.assertNotIn(rid, response.text)
            inspect.assert_not_called()
        self.assertEqual(self.b.get(f"/api/revisoes/{uuid4()}").status_code, 404)

    def test_same_idempotency_key_is_scoped_to_browser(self):
        key = str(uuid4())
        ids = [str(uuid4()), str(uuid4())]
        with patch("taxtrace.web.iniciar", side_effect=[{"revisao_id": i} for i in ids]) as start:
            results = [
                client.post(
                    "/api/consultas",
                    headers=self.headers(client, key),
                    json={"pergunta": "cesta basica"},
                )
                for client in (self.a, self.a, self.b)
            ]
        self.assertEqual(start.call_count, 2)
        self.assertEqual([r.json()["revisao_id"] for r in results], [ids[0], ids[0], ids[1]])

    def test_browser_cookie_keeps_permission_after_app_restart(self):
        rid = self.create(self.a)
        restarted = self.client(criar_app(self.root))
        restarted.cookies.clear()
        restarted.cookies.set(COOKIE_VISITANTE, self.a.cookies.get(COOKIE_VISITANTE))
        with patch("taxtrace.web.inspecionar", return_value={"revisao_id": rid}):
            self.assertEqual(restarted.get(f"/api/revisoes/{rid}").status_code, 200)
            restarted.cookies.clear()
            self.assertEqual(restarted.get(f"/api/revisoes/{rid}").status_code, 404)

    def test_reviewer_can_read_legacy_records_but_logout_revokes_admin_access(self):
        rid = str(uuid4())
        self.assertEqual(self.b.get(f"/api/revisoes/{rid}").status_code, 404)
        response = self.b.post(
            "/api/acesso/entrar",
            headers=self.headers(self.b),
            json={"conta": "teste", "senha": "senha-sintetica-para-teste"},
        )
        self.assertEqual(response.status_code, 200)
        with patch("taxtrace.web.inspecionar", return_value={"revisao_id": rid}):
            self.assertEqual(self.b.get(f"/api/revisoes/{rid}").status_code, 200)
            self.b.post("/api/acesso/sair", headers=self.headers(self.b), json={})
            self.assertEqual(self.b.get(f"/api/revisoes/{rid}").status_code, 404)

    def test_missing_cookie_and_corrupt_ownership_store_fail_closed(self):
        headers = self.headers(self.a)
        self.a.cookies.clear()
        with patch("taxtrace.web.iniciar") as start:
            response = self.a.post(
                "/api/consultas", headers=headers, json={"pergunta": "cesta basica"}
            )
            self.assertEqual(response.status_code, 401)
            start.assert_not_called()
        rid = self.create(self.b)
        Propriedade(self.root).caminho.write_bytes(b"private-corrupt-database")
        with patch("taxtrace.web.inspecionar") as inspect:
            response = self.b.get(f"/api/revisoes/{rid}")
            self.assertEqual(response.status_code, 503)
            self.assertNotIn("private", response.text)
            inspect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
