import copy
import os
import unittest
import urllib.error
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from taxtrace.agente import criar_grafo
from taxtrace.planejamento import (
    FalhaPlanejamento,
    Plano,
    planejar_gemini,
    planejar_local,
    validar_plano,
)

COLETA = {"id": 1, "manifesto_sha256": "a" * 64, "data_consulta": "2027-01-01"}
FONTE = {"url": "https://example.invalid/lei", "sha256": "b" * 64}


class ClienteFake:
    def __init__(self, *, falha=None, mistura=False, citacao_ruim=False):
        self.calls = []
        self.falha = falha
        self.mistura = mistura
        self.citacao_ruim = citacao_ruim

    async def call_tool(self, nome, args):
        self.calls.append((nome, args))
        dados = {"coleta": copy.deepcopy(COLETA)}
        if nome == "consultar_base":
            dados.update(status="base_disponivel", fontes=[FONTE])
        elif nome == "buscar_artigos":
            dados.update(
                status="encontrado",
                resultados=[
                    {
                        "artigo_numero": "125",
                        "trecho": "regra",
                        "citacao": {
                            "artigo": "125",
                            "url": FONTE["url"],
                            "fonte_sha256": "x" if self.citacao_ruim else FONTE["sha256"],
                        },
                    }
                ],
            )
            if self.mistura:
                dados["coleta"]["id"] = 2
        else:
            dados.update(
                status="artigo_recuperado",
                texto="regra",
                inicio=0,
                fim=5,
                citacao={**FONTE, "artigo": "125"},
            )
        return SimpleNamespace(is_error=nome == self.falha, structured_content=dados)


class GrafoTest(unittest.IsolatedAsyncioTestCase):
    async def executar(self, cliente, **kwargs):
        grafo = criar_grafo(cliente, Path.cwd(), **kwargs)
        return await grafo.ainvoke(
            {"pergunta": "cesta basica", "modo": "local", "rastro": []},
            config={"recursion_limit": 10, "callbacks": []},
        )

    async def test_fluxo_real_do_grafo_chama_ferramentas_e_fixa_coleta(self):
        c = ClienteFake()
        estado = await self.executar(c)
        self.assertEqual(
            [n for n, _ in c.calls], ["consultar_base", "buscar_artigos", "ler_artigo"]
        )
        self.assertTrue(all(a["coleta_id"] == 1 for _, a in c.calls[1:]))
        self.assertEqual(estado["resultado"]["status"], "evidencias_para_revisao")
        self.assertFalse(estado["resultado"]["resposta_fiscal_gerada"])
        self.assertFalse(estado["resultado"]["aprovacao_humana_realizada"])
        self.assertIn("conferir", [e["etapa"] for e in estado["rastro"]])

    async def test_falha_operacional_nao_vira_ausencia_de_dados(self):
        c = ClienteFake(falha="buscar_artigos")
        e = await self.executar(c)
        self.assertEqual(e["resultado"]["status"], "execucao_nao_concluida")
        self.assertEqual(len(c.calls), 2)

    async def test_coleta_misturada_interrompe_antes_de_ler_artigo(self):
        c = ClienteFake(mistura=True)
        e = await self.executar(c)
        self.assertEqual(e["resultado"]["status"], "execucao_nao_concluida")
        self.assertEqual(len(c.calls), 2)

    async def test_citacao_de_fonte_diferente_e_recusada(self):
        e = await self.executar(ClienteFake(citacao_ruim=True))
        self.assertEqual(e["erro"], "referencias_inconsistentes")

    async def test_recusa_do_planejador_sintetico_nao_consulta_banco(self):
        c = ClienteFake()

        def plano(_pergunta, _raiz):
            return Plano(acao="recusar", alvo="", motivo="fora_do_escopo"), {"tipo": "fixture"}

        g = criar_grafo(c, Path.cwd(), planejador_ia=plano)
        e = await g.ainvoke({"pergunta": "teste", "modo": "gemini", "rastro": []})
        self.assertEqual(e["resultado"]["status"], "recusado_pelo_planejador")
        self.assertEqual(c.calls, [])

    async def test_orcamento_de_chamadas_nao_acumula_entre_invocacoes(self):
        c = ClienteFake()
        g = criar_grafo(c, Path.cwd())
        for _ in range(2):
            e = await g.ainvoke({"pergunta": "cesta basica", "modo": "local", "rastro": []})
            self.assertEqual(e["resultado"]["status"], "evidencias_para_revisao")
        self.assertEqual(len(c.calls), 6)


class PlanejamentoTest(unittest.TestCase):
    def test_regras_explicitas_e_ambiguidades(self):
        self.assertEqual(planejar_local("leia artigo 2-A")[0].alvo, "2-A")
        self.assertEqual(planejar_local("cClassTrib 000001")[0].acao, "classificacao")
        for q in ("artigo 1 e artigo 2", "artigo 1 e codigo 000001"):
            with self.assertRaisesRegex(FalhaPlanejamento, "ambiguas"):
                planejar_local(q)

    def test_modelo_nao_pode_inventar_referencia_ou_acao(self):
        for acao, alvo in (("ler_artigo", "125"), ("classificacao", "000001")):
            with self.assertRaisesRegex(FalhaPlanejamento, "referencia_nao_explicita"):
                validar_plano(
                    Plano(acao=acao, alvo=alvo, motivo="consulta_documental"), "qual a regra?"
                )
        with self.assertRaises(ValueError):
            Plano(acao="executar_sql", alvo="select 1", motivo="consulta_documental")

    def test_limite_de_api_sem_retry_e_sem_detalhe_privado(self):
        erro = urllib.error.HTTPError("https://example.invalid", 429, "PRIVATE_SENTINEL", {}, None)
        with (
            patch.dict(
                os.environ,
                {"GEMINI_API_KEY": "fixture-key", "GEMINI_MODEL": "gemini-3.5-flash-lite"},
            ),
            patch("taxtrace.planejamento.urllib.request.urlopen", side_effect=erro) as abrir,
        ):
            with self.assertRaisesRegex(FalhaPlanejamento, "gemini_http_429") as capturado:
                planejar_gemini("cesta basica", Path.cwd())
        self.assertEqual(abrir.call_count, 1)
        self.assertNotIn("PRIVATE_SENTINEL", str(capturado.exception))


if __name__ == "__main__":
    unittest.main()
