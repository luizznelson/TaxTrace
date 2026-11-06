import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from filelock import FileLock, Timeout
from test_agente import ClienteFake

from taxtrace.agente import DecisaoRevisao
from taxtrace.revisao import caminhos, decidir, iniciar, inspecionar, validar_id


class RevisaoTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.raiz = Path(self.tmp.name)
        self.cliente = ClienteFake()

    async def nova(self):
        return await iniciar("cesta basica", raiz=self.raiz, cliente=self.cliente)

    def decisao(self, r, *, valor="aprovar", hash_=None):
        return {
            "decisao": valor,
            "revisor": "Revisor sintético",
            "motivo": "Decisão de teste automatizado",
            "origem": "teste_automatizado",
            "dossie_sha256": hash_ or r["pacote_revisao"]["dossie_sha256"],
        }

    async def test_pausa_persistida_e_retomada_sem_repetir_ferramentas(self):
        inicio = await self.nova()
        self.assertEqual(inicio["status"], "aguardando_revisao")
        self.assertNotIn("revisao", inicio["estado"])
        self.assertEqual(len(self.cliente.calls), 3)
        salvo = await inspecionar(inicio["revisao_id"], raiz=self.raiz)
        self.assertEqual(salvo["pacote_revisao"], inicio["pacote_revisao"])
        final = await decidir(inicio["revisao_id"], self.decisao(salvo), raiz=self.raiz)
        self.assertEqual(final["status"], "revisao_documental_aprovada")
        self.assertFalse(final["estado"]["resultado"]["aprovacao_humana_realizada"])
        self.assertFalse(final["estado"]["resultado"]["resposta_fiscal_gerada"])
        self.assertEqual(len(self.cliente.calls), 3)

    async def test_rejeicao_fica_registrada_e_nao_admite_segunda_decisao(self):
        r = await self.nova()
        final = await decidir(r["revisao_id"], self.decisao(r, valor="rejeitar"), raiz=self.raiz)
        self.assertEqual(final["status"], "revisao_documental_rejeitada")
        with self.assertRaisesRegex(ValueError, "revisao_nao_pendente"):
            await decidir(r["revisao_id"], self.decisao(r), raiz=self.raiz)
        salvo = await inspecionar(r["revisao_id"], raiz=self.raiz)
        self.assertEqual(salvo["estado"]["revisao"]["decisao"], "rejeitar")

    async def test_hash_divergente_preserva_pendencia(self):
        r = await self.nova()
        with self.assertRaisesRegex(ValueError, "dossie_da_decisao_divergente"):
            await decidir(r["revisao_id"], self.decisao(r, hash_="f" * 64), raiz=self.raiz)
        self.assertTrue((await inspecionar(r["revisao_id"], raiz=self.raiz))["pendente"])

    async def test_codigo_modificado_bloqueia_retomada_mas_permite_inspecao(self):
        r = await self.nova()
        with patch("taxtrace.revisao.impressao_codigo", return_value="codigo_novo"):
            visto = await inspecionar(r["revisao_id"], raiz=self.raiz)
            self.assertFalse(visto["codigo_compativel"])
            with self.assertRaisesRegex(ValueError, "codigo_alterado"):
                await decidir(r["revisao_id"], self.decisao(r), raiz=self.raiz)

    async def test_trava_impede_duas_operacoes_simultaneas(self):
        r = await self.nova()
        _, trava = caminhos(self.raiz, r["revisao_id"])
        with FileLock(trava, timeout=0):
            with self.assertRaises(Timeout):
                await decidir(r["revisao_id"], self.decisao(r), raiz=self.raiz)
        self.assertTrue((await inspecionar(r["revisao_id"], raiz=self.raiz))["pendente"])

    async def test_id_inexistente_e_id_com_caminho_nao_criam_revisao(self):
        with self.assertRaisesRegex(ValueError, "revisao_nao_encontrada"):
            await inspecionar(str(uuid4()), raiz=self.raiz)
        with self.assertRaisesRegex(ValueError, "id_de_revisao_invalido"):
            validar_id("../../outro.sqlite3")
        self.assertEqual(list(self.raiz.iterdir()), [])

    async def test_falha_mcp_nao_e_encaminhada_para_aprovacao(self):
        r = await iniciar(
            "cesta basica", raiz=self.raiz, cliente=ClienteFake(falha="buscar_artigos")
        )
        self.assertFalse(r["pendente"])
        self.assertEqual(r["status"], "execucao_nao_concluida")

    async def test_revisoes_distintas_nao_compartilham_decisoes(self):
        a, b = await self.nova(), await self.nova()
        self.assertNotEqual(a["revisao_id"], b["revisao_id"])
        await decidir(a["revisao_id"], self.decisao(a), raiz=self.raiz)
        self.assertTrue((await inspecionar(b["revisao_id"], raiz=self.raiz))["pendente"])


class DecisaoTest(unittest.TestCase):
    def test_decisao_exige_origem_explicita_e_nao_aceita_aprovacao_coerciva(self):
        valores = {
            "decisao": "aprovar",
            "revisor": "Revisor de teste",
            "motivo": "Teste local",
            "dossie_sha256": "a" * 64,
        }
        with self.assertRaises(ValueError):
            DecisaoRevisao.model_validate(valores)
        with self.assertRaises(ValueError):
            DecisaoRevisao.model_validate(
                {**valores, "origem": "teste_automatizado", "decisao": True}
            )
