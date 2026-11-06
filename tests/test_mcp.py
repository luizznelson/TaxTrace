import unittest
from unittest.mock import patch

from mcp import Client

from taxtrace.servidor_mcp import criar_servidor


class MCPTest(unittest.IsolatedAsyncioTestCase):
    async def test_descoberta_schemas_e_anotacoes_somente_leitura(self):
        async with Client(criar_servidor()) as cliente:
            ferramentas = (await cliente.list_tools()).tools
        self.assertEqual(
            {t.name for t in ferramentas},
            {"consultar_base", "buscar_artigos", "ler_artigo", "consultar_classificacao"},
        )
        for tool in ferramentas:
            self.assertTrue(tool.annotations.read_only_hint)
            self.assertFalse(tool.annotations.destructive_hint)
            self.assertIsNotNone(tool.output_schema)

    async def test_falha_de_banco_nao_vaza_detalhe_privado(self):
        with patch("taxtrace.servidor_mcp.conectar", side_effect=RuntimeError("PRIVATE_SENTINEL")):
            async with Client(criar_servidor()) as cliente:
                r = await cliente.call_tool("consultar_base", {})
        self.assertTrue(r.is_error)
        self.assertNotIn("PRIVATE_SENTINEL", str(r))
        self.assertIn("consulta_indisponivel", str(r))

    async def test_entradas_invalidas_nao_abrem_conexao(self):
        casos = [
            ("buscar_artigos", {"consulta": "abc", "limite": 11}),
            ("consultar_base", {"coleta_id": True}),
            ("buscar_artigos", {"consulta": "   "}),
            ("buscar_artigos", {"consulta": "x" * 501}),
            ("ler_artigo", {"numero": "1; DROP TABLE artigos;"}),
            ("ler_artigo", {"numero": "1", "inicio": -1}),
            ("consultar_classificacao", {"codigo": 1}),
        ]
        with patch("taxtrace.servidor_mcp.conectar") as conectar:
            async with Client(criar_servidor()) as cliente:
                for nome, args in casos:
                    with self.subTest(nome=nome, args=args):
                        r = await cliente.call_tool(nome, args)
                        self.assertTrue(r.is_error)
            conectar.assert_not_called()


if __name__ == "__main__":
    unittest.main()
