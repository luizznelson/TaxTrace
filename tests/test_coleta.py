import hashlib
import json
import tempfile
import unittest
import urllib.error
from datetime import UTC, datetime
from pathlib import Path

from taxtrace import coleta

VERSAO = {"versaoApp": "1.6.2", "versaoDb": "V0066", "dataVersaoDb": "2026-10-28"}


class Resposta:
    def __init__(self, corpo: bytes, status: int = 200):
        self.corpo = corpo
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.corpo


class AbrirFalso:
    """Simula urlopen: responde por trecho da URL e registra as chamadas."""

    def __init__(self, respostas):
        self.respostas = respostas
        self.chamadas = []

    def __call__(self, pedido, timeout=None):
        url = pedido.full_url
        self.chamadas.append(url)
        for trecho, resultado in self.respostas.items():
            if trecho in url:
                if isinstance(resultado, Exception):
                    raise resultado
                return Resposta(resultado)
        raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)


def respostas_ok():
    return {
        "/versao": json.dumps(VERSAO).encode(),
        "situacoes-tributarias/cbs-ibs": b"[]",
        "classificacoes-tributarias/cbs-ibs": json.dumps([{"codigo": "000001"}]).encode(),
        "fundamentacoes-legais": b"[1,2]",
        "ncm/vigentes": b"[1,2,3]",
        "lcp214.htm": "<p>Art. 1º Texto.</p>".encode("cp1252"),
    }


def agora():
    return datetime(2026, 11, 5, 21, 0, tzinfo=UTC)


class ColetaTest(unittest.TestCase):
    def test_coleta_grava_arquivos_e_manifesto(self):
        with tempfile.TemporaryDirectory() as tmp:
            abrir = AbrirFalso(respostas_ok())
            manifesto = coleta.coletar(Path(tmp), "2027-01-01", abrir=abrir, agora=agora)

            pasta = Path(tmp) / "2026-11-05"
            self.assertEqual(manifesto["erros"], [])
            self.assertEqual(len(manifesto["arquivos"]), 6)
            self.assertEqual(manifesto["versao_api"], VERSAO)
            self.assertEqual(manifesto["data_consulta"], "2027-01-01")
            salvo = json.loads((pasta / "manifesto.json").read_text(encoding="utf-8"))
            self.assertEqual(salvo, manifesto)

            ncm = next(a for a in manifesto["arquivos"] if a["nome"] == "ncm_vigentes")
            corpo = (pasta / "ncm_vigentes.json").read_bytes()
            self.assertEqual(ncm["sha256"], hashlib.sha256(corpo).hexdigest())
            self.assertEqual(ncm["itens"], 3)
            self.assertEqual(
                (pasta / "lc214_planalto.html").read_bytes(),
                "<p>Art. 1º Texto.</p>".encode("cp1252"),
            )

    def test_lei_de_arquivo_local_quando_planalto_bloqueia(self):
        with tempfile.TemporaryDirectory() as tmp:
            salvo = Path(tmp) / "lcp214.htm"
            salvo.write_bytes(b"<p>Art. 1o Texto salvo no navegador.</p>")
            respostas = respostas_ok()
            respostas["lcp214.htm"] = ConnectionResetError("conexao encerrada")
            abrir = AbrirFalso(respostas)
            manifesto = coleta.coletar(
                Path(tmp) / "raw", "2027-01-01", abrir=abrir, agora=agora, lei_arquivo=salvo
            )
            self.assertEqual(manifesto["erros"], [])
            lei = next(a for a in manifesto["arquivos"] if a["nome"] == "lc214_planalto")
            self.assertEqual(lei["origem"], "arquivo local")
            self.assertIsNone(lei["http"])
            self.assertFalse(any("planalto" in u for u in abrir.chamadas))

    def test_planalto_bloqueado_sem_arquivo_vira_erro(self):
        with tempfile.TemporaryDirectory() as tmp:
            respostas = respostas_ok()
            respostas["lcp214.htm"] = ConnectionResetError("conexao encerrada")
            manifesto = coleta.coletar(
                Path(tmp), "2027-01-01", abrir=AbrirFalso(respostas), agora=agora, espera=0
            )
            self.assertEqual([e["nome"] for e in manifesto["erros"]], ["lc214_planalto"])
            self.assertIn("ConnectionResetError", manifesto["erros"][0]["erro"])

    def test_data_vai_na_url_exceto_na_versao(self):
        with tempfile.TemporaryDirectory() as tmp:
            abrir = AbrirFalso(respostas_ok())
            coleta.coletar(Path(tmp), "2027-01-01", abrir=abrir, agora=agora)
            versao = next(u for u in abrir.chamadas if u.endswith("/versao"))
            self.assertNotIn("data=", versao)
            ncm = next(u for u in abrir.chamadas if "ncm/vigentes" in u)
            self.assertTrue(ncm.endswith("?data=2027-01-01"))

    def test_fonte_com_erro_vai_para_erros_e_nao_some(self):
        with tempfile.TemporaryDirectory() as tmp:
            respostas = respostas_ok()
            del respostas["fundamentacoes-legais"]
            abrir = AbrirFalso(respostas)
            manifesto = coleta.coletar(Path(tmp), "2027-01-01", abrir=abrir, agora=agora)

            self.assertEqual([e["nome"] for e in manifesto["erros"]], ["fundamentacoes_legais"])
            self.assertIn("HTTPError", manifesto["erros"][0]["erro"])
            self.assertEqual(len(manifesto["arquivos"]), 5)
            self.assertFalse((Path(tmp) / "2026-11-05" / "fundamentacoes_legais.json").exists())

    def test_resposta_que_nao_e_json_vira_erro(self):
        with tempfile.TemporaryDirectory() as tmp:
            respostas = respostas_ok()
            respostas["ncm/vigentes"] = b"<html>manutencao</html>"
            manifesto = coleta.coletar(
                Path(tmp), "2027-01-01", abrir=AbrirFalso(respostas), agora=agora
            )
            self.assertEqual([e["nome"] for e in manifesto["erros"]], ["ncm_vigentes"])
            self.assertFalse((Path(tmp) / "2026-11-05" / "ncm_vigentes.json").exists())

    def test_baixar_repete_em_5xx_e_desiste_em_4xx(self):
        chamadas = []

        def instavel(pedido, timeout=None):
            chamadas.append(1)
            if len(chamadas) < 3:
                raise urllib.error.HTTPError(pedido.full_url, 503, "indisponivel", {}, None)
            return Resposta(b"ok")

        status, corpo = coleta.baixar("https://exemplo.test", abrir=instavel, espera=0)
        self.assertEqual((status, corpo, len(chamadas)), (200, b"ok", 3))

        tentativas = []

        def nao_encontrado(pedido, timeout=None):
            tentativas.append(1)
            raise urllib.error.HTTPError(pedido.full_url, 404, "nf", {}, None)

        with self.assertRaises(urllib.error.HTTPError):
            coleta.baixar("https://exemplo.test", abrir=nao_encontrado, espera=0)
        self.assertEqual(len(tentativas), 1)

    def test_baixar_desiste_depois_das_tentativas_em_erro_de_rede(self):
        def sem_rede(pedido, timeout=None):
            raise urllib.error.URLError("sem rede")

        with self.assertRaises(urllib.error.URLError):
            coleta.baixar("https://exemplo.test", abrir=sem_rede, tentativas=2, espera=0)


if __name__ == "__main__":
    unittest.main()
