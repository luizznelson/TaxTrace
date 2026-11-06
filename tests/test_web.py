import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from taxtrace.web import criar_app


class WebTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.client = TestClient(criar_app(Path(self.tmp.name)), base_url="http://127.0.0.1:8015")
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)
        self.token = self.client.get("/api/contexto").json()["csrf"]

    def headers(self, key=None):
        return {
            "X-TaxTrace-CSRF": self.token,
            "Origin": "http://127.0.0.1:8015",
            "Idempotency-Key": key or str(uuid4()),
        }

    def test_pagina_assets_csp_e_arquivos_privados(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("frame-ancestors 'none'", r.headers["content-security-policy"])
        self.assertIn("TaxTrace", r.text)
        self.assertEqual(self.client.get("/assets/app.js").status_code, 200)
        module = self.client.get("/assets/query-input.mjs")
        self.assertEqual(module.status_code, 200)
        self.assertIn("javascript", module.headers["content-type"])
        self.assertEqual(self.client.get("/.env").status_code, 404)
        self.assertEqual(self.client.get("/data/checkpoints/revisoes.sqlite3").status_code, 404)
        self.assertEqual(self.client.get("/", headers={"Host": "evil.example"}).status_code, 400)

    def test_post_sem_token_ou_origem_externa_e_recusado(self):
        self.assertEqual(
            self.client.post("/api/consultas", json={"pergunta": "cesta basica"}).status_code, 403
        )
        h = self.headers()
        h["Origin"] = "https://evil.example"
        self.assertEqual(
            self.client.post(
                "/api/consultas", headers=h, json={"pergunta": "cesta basica"}
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.get("/api/contexto", headers={"Sec-Fetch-Site": "cross-site"}).status_code,
            403,
        )

    def test_limites_e_campos_extras_nao_chamam_backend(self):
        with patch("taxtrace.web.iniciar") as iniciar:
            for dados in (
                {"pergunta": "   "},
                {"pergunta": "x" * 501},
                {"pergunta": "abc", "sql": "select 1"},
                {"pergunta": "abc", "coleta_id": True},
            ):
                self.assertEqual(
                    self.client.post(
                        "/api/consultas", headers=self.headers(), json=dados
                    ).status_code,
                    422,
                )
            iniciar.assert_not_called()
        self.assertEqual(
            self.client.post(
                "/api/consultas", headers=self.headers(), content="x" * 9000
            ).status_code,
            415,
        )

    def test_mesma_tentativa_nao_repete_consulta_e_conteudo_diferente_e_recusado(self):
        count = []

        async def iniciar(*args, **kwargs):
            count.append(args)
            await asyncio.sleep(0.01)
            return {"status": "aguardando_revisao", "revisao_id": str(uuid4())}

        key = str(uuid4())
        h = self.headers(key)
        with patch("taxtrace.web.iniciar", side_effect=iniciar):
            a = self.client.post("/api/consultas", headers=h, json={"pergunta": "cesta basica"})
            b = self.client.post("/api/consultas", headers=h, json={"pergunta": "cesta basica"})
            c = self.client.post("/api/consultas", headers=h, json={"pergunta": "outro texto"})
        self.assertEqual(a.json(), b.json())
        self.assertEqual(len(count), 1)
        self.assertEqual(c.status_code, 409)

    def test_falha_privada_nao_aparece_na_resposta(self):
        with patch("taxtrace.web.inspecionar", side_effect=RuntimeError("PRIVATE_SENTINEL")):
            r = self.client.get("/api/revisoes/" + str(uuid4()))
        self.assertEqual(r.status_code, 503)
        self.assertNotIn("PRIVATE_SENTINEL", r.text)

    def test_decisao_preserva_hash_e_origem_de_teste(self):
        payload = {
            "decisao": "rejeitar",
            "revisor": "Revisor de teste",
            "motivo": "Teste automatizado",
            "origem": "teste_automatizado",
            "dossie_sha256": "a" * 64,
        }
        with patch(
            "taxtrace.web.decidir", return_value={"status": "revisao_documental_rejeitada"}
        ) as decidir:
            r = self.client.post(
                "/api/revisoes/" + str(uuid4()) + "/decisao", headers=self.headers(), json=payload
            )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(decidir.call_args.args[1], payload)


if __name__ == "__main__":
    unittest.main()
