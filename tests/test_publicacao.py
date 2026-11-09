"""Cenários de publicação: proxy HTTPS, origem, custos e falhas fechadas."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from taxtrace.autenticacao import COOKIE, criar_credencial
from taxtrace.preparar_render import preparar, valores
from taxtrace.publicacao import LimitesConsultas, configuracao
from taxtrace.servir import validar
from taxtrace.web import criar_app


class PublicacaoTest(unittest.TestCase):
    def test_origem_recusa_http_wildcard_porta_credencial_e_caminho(self):
        for origem in (
            "http://taxtrace.onrender.com",
            "https://*.onrender.com",
            "https://user:pass@taxtrace.onrender.com",
            "https://taxtrace.onrender.com:443",
            "https://taxtrace.onrender.com/app",
            "https://taxtrace.onrender.com?x=1",
        ):
            with (
                self.subTest(origem=origem),
                patch.dict("os.environ", {"TAXTRACE_PUBLIC_URL": origem}, clear=True),
            ):
                with self.assertRaises(ValueError):
                    configuracao()

    def test_render_origem_derivada_e_ia_desabilitada_por_padrao(self):
        with patch.dict(
            "os.environ",
            {"RENDER": "true", "RENDER_EXTERNAL_HOSTNAME": "taxtrace.onrender.com"},
            clear=True,
        ):
            cfg = configuracao()
        self.assertEqual(cfg.origem, "https://taxtrace.onrender.com")
        self.assertFalse(cfg.ia_habilitada)
        with patch.dict("os.environ", {"RENDER": "true"}, clear=True):
            with self.assertRaises(ValueError):
                configuracao()

    def test_limites_globais_somam_ia_e_local_e_expiram(self):
        clock = [0]
        limites = LimitesConsultas(lambda: clock[0])
        for _ in range(20):
            self.assertTrue(limites.reservar(True))
        self.assertFalse(limites.reservar(True))
        for _ in range(40):
            self.assertTrue(limites.reservar(False))
        self.assertFalse(limites.reservar(False))
        clock[0] = 3600
        self.assertTrue(limites.reservar(True))

    def test_entrada_hospedada_recusa_sqlite_admin_e_porta_invalida(self):
        cfg = {
            "TAXTRACE_PUBLIC_URL": "https://taxtrace.onrender.com",
            "TAXTRACE_CHECKPOINT_BACKEND": "postgres",
            "TAXTRACE_DATABASE_MODE": "neon",
            "PORT": "10000",
        }
        with patch("taxtrace.servir.opcoes"), patch("taxtrace.servir.parametros"):
            with patch.dict("os.environ", cfg, clear=True):
                self.assertEqual(validar(), 10000)
            for alteracao in (
                {"TAXTRACE_CHECKPOINT_BACKEND": "sqlite"},
                {"DATABASE_URL": "PRIVATE"},
                {"TAXTRACE_NEON_ADMIN_URL": "PRIVATE"},
                {"PORT": "80"},
                {"PORT": "invalid"},
            ):
                with (
                    self.subTest(alteracao=alteracao),
                    patch.dict("os.environ", {**cfg, **alteracao}, clear=True),
                ):
                    with self.assertRaises(ValueError):
                        validar()


class ProxyPublicoTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        env = patch.dict(
            "os.environ",
            {
                "TAXTRACE_PUBLIC_URL": "https://taxtrace.onrender.com",
                "TAXTRACE_PUBLIC_AI_ENABLED": "false",
                "TAXTRACE_CHECKPOINT_BACKEND": "sqlite",
                "GEMINI_API_KEY": "synthetic-key",
            },
        )
        env.start()
        self.addCleanup(env.stop)
        app = criar_app(Path(self.tmp.name))

        async def proxy(scope, receive, send):
            # O navegador usa HTTPS; o servidor recebe HTTP após terminação TLS.
            if scope["type"] == "http":
                scope = {**scope, "scheme": "http"}
            await app(scope, receive, send)

        self.client = TestClient(proxy, base_url="https://taxtrace.onrender.com")
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)
        r = self.client.get("/api/contexto")
        self.contexto = r.json()
        self.cookie = r.headers["set-cookie"]

    def headers(self, key=None):
        return {
            "Origin": "https://taxtrace.onrender.com",
            "X-TaxTrace-CSRF": self.contexto["csrf"],
            "Idempotency-Key": key or str(uuid4()),
        }

    def test_cookie_secure_hsts_e_nao_confia_em_headers_de_proxy(self):
        self.assertIn("Secure", self.cookie)
        self.assertFalse(self.contexto["gemini_disponivel"])
        r = self.client.get(
            "/", headers={"Host": "outro.example", "X-Forwarded-Host": "taxtrace.onrender.com"}
        )
        self.assertEqual(r.status_code, 400)
        r = self.client.get("/", headers={"X-Forwarded-Proto": "http"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers["strict-transport-security"], "max-age=31536000")
        r = self.client.post(
            "/api/consultas",
            headers={**self.headers(), "Origin": "http://taxtrace.onrender.com"},
            json={"pergunta": "artigo 125"},
        )
        self.assertEqual(r.status_code, 403)

    def test_ia_publica_desativada_nao_chama_modelo(self):
        with patch("taxtrace.web.iniciar") as iniciar:
            r = self.client.post(
                "/api/consultas",
                headers=self.headers(),
                json={"pergunta": "artigo 125", "modo": "rag"},
            )
        self.assertEqual(r.status_code, 503)
        iniciar.assert_not_called()

    def test_limite_retorna_429_e_idempotencia_nao_gasta_nova_cota(self):
        with patch("taxtrace.web.iniciar", return_value={"revisao_id": str(uuid4())}) as iniciar:
            key = str(uuid4())
            for _ in range(2):
                self.assertEqual(
                    self.client.post(
                        "/api/consultas", headers=self.headers(key), json={"pergunta": "artigo 125"}
                    ).status_code,
                    200,
                )
            for _ in range(59):
                self.assertEqual(
                    self.client.post(
                        "/api/consultas", headers=self.headers(), json={"pergunta": "artigo 125"}
                    ).status_code,
                    200,
                )
            r = self.client.post(
                "/api/consultas", headers=self.headers(), json={"pergunta": "artigo 125"}
            )
        self.assertEqual(iniciar.call_count, 60)
        self.assertEqual(r.status_code, 429)
        self.assertEqual(r.headers["retry-after"], "3600")

    def test_login_em_https_emite_cookie_secure(self):
        credencial = criar_credencial("revisor", "Revisor de teste", "synthetic-password")

        with patch.dict(
            "os.environ", {"TAXTRACE_REVIEWER_CREDENTIAL_JSON": json.dumps(credencial)}
        ):
            app = criar_app(Path(self.tmp.name))
        with TestClient(app, base_url="https://taxtrace.onrender.com") as client:
            csrf = client.get("/api/contexto").json()["csrf"]
            headers = {"Origin": "https://taxtrace.onrender.com", "X-TaxTrace-CSRF": csrf}
            r = client.post(
                "/api/acesso/entrar",
                headers=headers,
                json={"conta": "revisor", "senha": "synthetic-password"},
            )
            self.assertEqual(r.status_code, 200)
            self.assertIn("Secure", r.headers["set-cookie"])
            self.assertIn(COOKIE, r.headers["set-cookie"])


class ArquivoPrivadoRenderTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.runtime = {
            "TAXTRACE_DATABASE_MODE": "neon",
            "TAXTRACE_CHECKPOINT_BACKEND": "postgres",
            "TAXTRACE_NEON_HOST": "ep-synthetic.us-east-2.aws.neon.tech",
            "TAXTRACE_NEON_DATABASE": "neondb",
            "TAXTRACE_READER_DATABASE_URL": "postgresql://taxtrace_reader:synthetic-reader@ep-synthetic.us-east-2.aws.neon.tech/neondb?sslmode=require",
            "TAXTRACE_CHECKPOINT_DATABASE_URL": "postgresql://taxtrace_state:synthetic-state@ep-synthetic.us-east-2.aws.neon.tech/neondb?sslmode=require",
        }
        self.gravar()

    def gravar(self):
        (self.root / ".env.neon.runtime").write_text(
            "".join(f"{k}={v}\n" for k, v in self.runtime.items()), encoding="utf-8"
        )

    def test_exporta_somente_lista_permitida_e_preserva_arquivo_existente(self):
        (self.root / ".env").write_text(
            "DATABASE_URL=PRIVATE-ADMIN\nTAXTRACE_NEON_ADMIN_URL=PRIVATE-ADMIN\nGEMINI_API_KEY=synthetic-key\n",
            encoding="utf-8",
        )
        resultado = preparar(self.root)
        texto = (self.root / ".env.render").read_text(encoding="utf-8")
        self.assertNotIn("PRIVATE-ADMIN", texto)
        self.assertNotIn("TAXTRACE_NEON_ADMIN_URL", texto)
        self.assertFalse(resultado["ia_publica_habilitada"])
        self.assertTrue(resultado["chave_de_modelo_incluida"])
        with self.assertRaises(FileExistsError):
            preparar(self.root)
        self.assertEqual((self.root / ".env.render").read_text(encoding="utf-8"), texto)

    def test_runtime_com_papel_administrativo_recusado_antes_de_escrever(self):
        self.runtime["TAXTRACE_READER_DATABASE_URL"] = self.runtime[
            "TAXTRACE_READER_DATABASE_URL"
        ].replace("taxtrace_reader:", "owner:")
        self.gravar()
        with self.assertRaises(ValueError):
            preparar(self.root)
        self.assertFalse((self.root / ".env.render").exists())

    def test_credencial_do_revisor_e_json_valido_sem_senha_em_texto(self):
        pasta = self.root / "data/checkpoints"
        pasta.mkdir(parents=True)
        credencial = criar_credencial("revisor", "Revisor de teste", "synthetic-password")
        (pasta / "revisor.json").write_text(json.dumps(credencial), encoding="utf-8")
        cfg = valores(self.root)
        self.assertEqual(json.loads(cfg["TAXTRACE_REVIEWER_CREDENTIAL_JSON"]), credencial)
        self.assertNotIn("synthetic-password", cfg["TAXTRACE_REVIEWER_CREDENTIAL_JSON"])
