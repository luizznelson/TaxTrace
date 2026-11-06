"""Verifica um subprocesso MCP stdio real e registra chamadas públicas de leitura."""

import asyncio
import hashlib
import json
import sys
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from mcp import Client, StdioServerParameters


async def verificar(raiz):
    parametros = StdioServerParameters(
        command=sys.executable,
        args=["-m", "taxtrace.servidor_mcp"],
        cwd=raiz,
        env={"PYTHONIOENCODING": "utf-8"},
    )
    chamadas = []
    async with Client(parametros, read_timeout_seconds=15) as cliente:
        ferramentas = (await cliente.list_tools()).tools
        assert {t.name for t in ferramentas} == {
            "consultar_base",
            "buscar_artigos",
            "ler_artigo",
            "consultar_classificacao",
        }
        assert all(
            t.annotations.read_only_hint and not t.annotations.destructive_hint for t in ferramentas
        )

        async def chamar(nome, args, *, erro=False):
            inicio = perf_counter()
            resultado = await cliente.call_tool(nome, args)
            assert resultado.is_error == erro
            chamadas.append(
                {
                    "ferramenta": nome,
                    "argumentos": args,
                    "erro": resultado.is_error,
                    "duracao_ms": round((perf_counter() - inicio) * 1000, 3),
                    "resultado": resultado.structured_content,
                    "mensagens": [c.text for c in resultado.content if c.type == "text"]
                    if erro
                    else [],
                }
            )
            return resultado.structured_content

        base = await chamar("consultar_base", {})
        cid = base["coleta"]["id"]
        busca = await chamar(
            "buscar_artigos", {"consulta": "cesta basica", "limite": 3, "coleta_id": cid}
        )
        assert any(r["artigo_numero"] == "125" for r in busca["resultados"])
        pagina1 = await chamar(
            "ler_artigo", {"numero": "22", "inicio": 0, "limite_caracteres": 100, "coleta_id": cid}
        )
        assert pagina1["proximo_inicio"] == 100
        pagina2 = await chamar(
            "ler_artigo",
            {
                "numero": "22",
                "inicio": pagina1["proximo_inicio"],
                "limite_caracteres": 100,
                "coleta_id": cid,
            },
        )
        juntas = await chamar(
            "ler_artigo", {"numero": "22", "limite_caracteres": 200, "coleta_id": cid}
        )
        assert pagina1["texto"] + pagina2["texto"] == juntas["texto"]
        geral = await chamar("consultar_classificacao", {"codigo": "000001", "coleta_id": cid})
        assert geral["registro"]["regra_geral"] and not geral["artigos_referenciados"]
        vinculada = await chamar("consultar_classificacao", {"codigo": "000002", "coleta_id": cid})
        assert vinculada["artigos_referenciados"]
        ausente = await chamar("consultar_classificacao", {"codigo": "999999", "coleta_id": cid})
        assert ausente["status"] == "classificacao_nao_encontrada_nesta_coleta"
        await chamar("ler_artigo", {"numero": "9999", "coleta_id": cid})
        await chamar("buscar_artigos", {"consulta": "teste", "limite": 11}, erro=True)
        await chamar("ler_artigo", {"numero": "1; DROP TABLE artigos;"}, erro=True)
        await chamar("consultar_base", {"coleta_id": 9223372036854775807}, erro=True)
        depois = await chamar("consultar_base", {"coleta_id": cid})
        assert base["contagens"] == depois["contagens"]
        assert all(c["resultado"]["coleta"]["id"] == cid for c in chamadas if not c["erro"])
    report = {
        "verificado_em": datetime.now(UTC).isoformat(),
        "transporte": "stdio_subprocesso_real",
        "sdk_mcp": version("mcp"),
        "coleta": base["coleta"],
        "ferramentas": [t.model_dump(mode="json", by_alias=True) for t in ferramentas],
        "chamadas": chamadas,
        "contagens_antes_depois_iguais": True,
        "paginacao_literal_verificada": True,
        "codigo_sha256": {
            n: hashlib.sha256((raiz / "taxtrace" / n).read_bytes()).hexdigest()
            for n in ("servidor_mcp.py", "consultas.py", "busca.py")
        },
        "limites": [
            "Teste local do protocolo; não foi conectado a um agente LLM ou cliente desktop.",
            "Consultas fornecem dados e fontes; não comprovam aplicabilidade ou vigência.",
        ],
    }
    destino = raiz / "runs" / f"mcp-{uuid4()}"
    destino.mkdir(parents=True, exist_ok=False)
    (destino / "verificacao.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return {
        "status": "mcp_verificado",
        "registro": str(destino.relative_to(raiz)),
        "ferramentas": len(ferramentas),
        "chamadas": len(chamadas),
    }


def main():
    try:
        raiz = Path(__file__).resolve().parent.parent
        print(json.dumps(asyncio.run(verificar(raiz)), ensure_ascii=False))
        return 0
    except Exception as erro:
        print(json.dumps({"status": "verificacao_nao_concluida", "tipo": type(erro).__name__}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
