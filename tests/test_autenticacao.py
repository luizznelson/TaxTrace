import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from taxtrace.autenticacao import COOKIE, DURACAO, AcessoRevisor, criar_credencial
from taxtrace.web import criar_app

SENHA = "senha-sintetica-de-teste-2026"


class AcessoTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        folder = self.root / "data/checkpoints"
        folder.mkdir(parents=True)
        self.credential = folder / "revisor.json"
        self.credential.write_text(
            json.dumps(criar_credencial("revisor.teste", "Revisor sintético", SENHA)),
            encoding="utf-8",
        )
        self.now = 0
        self.access = AcessoRevisor(self.root, relogio=lambda: self.now)

    def test_salted_hash_and_invalid_credentials(self):
        stored = self.credential.read_text(encoding="utf-8")
        self.assertNotIn(SENHA, stored)
        self.assertNotEqual(
            json.loads(stored)["hash"],
            criar_credencial("revisor.teste", "Revisor sintético", SENHA)["hash"],
        )
        self.access.verificar("revisor.teste", SENHA)
        for account, password in [("outro", SENHA), ("revisor.teste", "errada")]:
            with self.assertRaisesRegex(ValueError, "credenciais_invalidas"):
                self.access.verificar(account, password)

    def test_rate_limit_then_expiration(self):
        for _ in range(5):
            with self.assertRaisesRegex(ValueError, "credenciais_invalidas"):
                self.access.verificar("revisor.teste", "errada")
        with self.assertRaisesRegex(ValueError, "acesso_em_espera"):
            self.access.verificar("revisor.teste", SENHA)
        self.now = 61
        self.access.verificar("revisor.teste", SENHA)

    def test_logout_expiration_restart_and_session_bound(self):
        token = self.access.abrir()
        self.assertEqual(self.access.usuario(token)["conta"], "revisor.teste")
        self.assertNotIn(token, self.access.sessoes)
        self.assertIsNone(self.access.usuario("token-forjado"))
        self.assertIsNone(AcessoRevisor(self.root).usuario(token))
        self.access.sair(token)
        self.assertIsNone(self.access.usuario(token))
        token = self.access.abrir()
        self.now = DURACAO
        self.assertIsNone(self.access.usuario(token))
        tokens = [self.access.abrir() for _ in range(9)]
        self.assertEqual(len(self.access.sessoes), 8)
        self.assertIsNone(self.access.usuario(tokens[0]))

    def test_bad_file_fails_closed_and_bad_account_rejected(self):
        self.credential.write_text('{"senha":"private"}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "credencial_de_revisor_invalida"):
            criar_app(self.root)
        with self.assertRaises(ValueError):
            criar_credencial("inválida", "Teste", SENHA)
        with self.assertRaises(ValueError):
            criar_credencial("teste", "Teste", "curta")

    def client(self, scheme="http"):
        client = TestClient(criar_app(self.root), base_url=f"{scheme}://127.0.0.1")
        client.__enter__()
        self.addCleanup(client.__exit__, None, None, None)
        return client

    def login(self, client):
        token = client.get("/api/contexto").json()["csrf"]
        headers = {"X-TaxTrace-CSRF": token}
        result = client.post(
            "/api/acesso/entrar", headers=headers, json={"conta": "revisor.teste", "senha": SENHA}
        )
        self.assertEqual(result.status_code, 200)
        self.assertNotIn(SENHA, result.text)
        return headers, result

    def test_cookie_login_csrf_logout_and_identity_from_server(self):
        client = self.client()
        self.assertEqual(
            client.post(
                "/api/acesso/entrar", json={"conta": "revisor.teste", "senha": SENHA}
            ).status_code,
            403,
        )
        headers, response = self.login(client)
        cookie = response.headers["set-cookie"]
        for attribute in ("HttpOnly", "SameSite=strict", "Max-Age=3600"):
            self.assertIn(attribute, cookie)
        self.assertNotIn("senha", client.get("/api/contexto").text)
        self.assertEqual(
            client.get("/api/contexto").json()["acesso"]["usuario"]["nome"], "Revisor sintético"
        )
        body = {
            "decisao": "rejeitar",
            "revisor": "Nome forjado",
            "motivo": "Decisão de teste",
            "origem": "teste_automatizado",
            "dossie_sha256": "a" * 64,
        }
        with patch("taxtrace.web.decidir", return_value={"status": "teste"}) as decide:
            result = client.post(f"/api/revisoes/{uuid4()}/decisao", headers=headers, json=body)
            self.assertEqual(result.status_code, 200)
            recorded = decide.call_args.args[1]
            self.assertEqual(recorded["revisor"], "Revisor sintético")
            self.assertEqual(recorded["conta_revisor"], "revisor.teste")
            self.assertEqual(recorded["origem"], "operador_local")
            self.assertEqual(recorded["autenticacao"], "sessao_local")
        old_token = client.cookies.get(COOKIE)
        self.assertEqual(client.post("/api/acesso/sair", headers=headers, json={}).status_code, 200)
        client.cookies.set(COOKIE, old_token)
        with patch("taxtrace.web.decidir") as decide:
            self.assertEqual(
                client.post(
                    f"/api/revisoes/{uuid4()}/decisao", headers=headers, json=body
                ).status_code,
                401,
            )
            decide.assert_not_called()

    def test_https_cookie_and_origin(self):
        client = self.client("https")
        headers, result = self.login(client)
        self.assertIn("Secure", result.headers["set-cookie"])
        self.assertEqual(
            client.post(
                "/api/acesso/sair", headers={**headers, "Origin": "https://outro.example"}, json={}
            ).status_code,
            403,
        )


if __name__ == "__main__":
    unittest.main()
