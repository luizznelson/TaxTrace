"""Avaliação local do RAG com triagem reproduzível e geração real opcional, limitada."""

import argparse
import asyncio
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from langsmith import tracing_context

from taxtrace.agente import criar_grafo
from taxtrace.rag import FalhaGeracao, gerar_gemini, normalizar
from taxtrace.revisao import cliente_mcp


async def avaliar(raiz, conjunto, *, ao_vivo=False, limite_geracoes=3):
    if type(limite_geracoes) is not int or not 1 <= limite_geracoes <= 5:
        raise ValueError("limite_de_geracoes_invalido")
    usados = 0
    casos = []

    def gerar(pergunta, avaliacao, pasta):
        nonlocal usados
        if not ao_vivo:
            raise FalhaGeracao("avaliacao_somente_triagem_sem_modelo")
        if usados >= limite_geracoes:
            raise FalhaGeracao("orcamento_da_avaliacao_esgotado")
        usados += 1
        return gerar_gemini(pergunta, avaliacao, pasta)

    with tracing_context(enabled=False):
        async with cliente_mcp(raiz) as cliente:
            grafo = criar_grafo(cliente, raiz, gerador_ia=gerar)
            for caso in conjunto["casos"]:
                estado = await grafo.ainvoke(
                    {"pergunta": caso["pergunta"], "modo": "rag", "rastro": []},
                    config={"recursion_limit": 14, "callbacks": []},
                )
                if estado.get("coleta", {}).get("manifesto_sha256") != conjunto["manifesto_sha256"]:
                    raise ValueError("gabarito_de_outra_coleta_ou_recuperacao_falhou")
                rag = estado.get("rag", {})
                pre = rag.get("avaliacao", {})
                certo = pre.get("elegivel") == caso["elegivel"]
                if not caso["elegivel"]:
                    certo = certo and pre.get("motivo") == caso["motivo"]
                resultado = {
                    "id": caso["id"],
                    "pergunta": caso["pergunta"],
                    "triagem_correta": certo,
                    "elegivel_esperado": caso["elegivel"],
                    "estado": estado,
                    "geracao_avaliada": False,
                }
                if ao_vivo and caso["elegivel"]:
                    resposta = " ".join(a["texto"] for a in rag.get("afirmacoes", []))
                    citados = {
                        c["documento_id"] for a in rag.get("afirmacoes", []) for c in a["citacoes"]
                    }
                    conceitos = {
                        c: normalizar(c) in normalizar(resposta) for c in caso["conceitos"]
                    }
                    resultado.update(
                        geracao_avaliada=rag.get("status") == "respondida",
                        referencias_esperadas_presentes=set(caso["citacoes"]) <= citados,
                        conceitos_esperados=conceitos,
                        passou_gabarito_minimo=rag.get("status") == "respondida"
                        and set(caso["citacoes"]) <= citados
                        and all(conceitos.values()),
                    )
                casos.append(resultado)
    gerados = [c for c in casos if c["elegivel_esperado"] and ao_vivo]
    return {
        "executado_em": datetime.now(UTC).isoformat(),
        "ao_vivo": ao_vivo,
        "limite_geracoes": limite_geracoes,
        "tentativas_de_geracao_real": usados,
        "natureza": conjunto["natureza"],
        "manifesto_sha256": conjunto["manifesto_sha256"],
        "resumo": {
            "casos": len(casos),
            "triagens_corretas": sum(c["triagem_correta"] for c in casos),
            "casos_de_geracao": len(gerados),
            "gabaritos_minimos_atendidos": sum(
                c.get("passou_gabarito_minimo", False) for c in gerados
            ),
        },
        "limites": conjunto["criterios"],
        "casos": casos,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ao-vivo", action="store_true")
    parser.add_argument("--limite-geracoes", type=int, default=3)
    args = parser.parse_args()
    raiz = Path(__file__).resolve().parent.parent
    arquivo = raiz / "evals/rag.v1.json"
    conjunto = json.loads(arquivo.read_text(encoding="utf-8"))
    resultado = asyncio.run(
        avaliar(raiz, conjunto, ao_vivo=args.ao_vivo, limite_geracoes=args.limite_geracoes)
    )
    resultado["gabarito_sha256"] = hashlib.sha256(arquivo.read_bytes()).hexdigest()
    resultado["codigo_sha256"] = {
        nome: hashlib.sha256((raiz / "taxtrace" / nome).read_bytes()).hexdigest()
        for nome in ("rag.py", "agente.py", "avaliar_rag.py")
    }
    pasta = raiz / "runs" / f"rag-{uuid4()}"
    pasta.mkdir()
    (pasta / "avaliacao.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {"registro": str(pasta.relative_to(raiz)), **resultado["resumo"]}, ensure_ascii=False
        )
    )


if __name__ == "__main__":
    main()
