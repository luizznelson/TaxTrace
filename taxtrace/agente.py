"""Fluxo LangGraph via MCP: planejar, recuperar e reunir evidências para revisão."""

import argparse
import asyncio
import hashlib
import json
import sys
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from time import perf_counter
from typing import Literal, TypedDict
from uuid import uuid4

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt
from langsmith import tracing_context
from mcp import Client, StdioServerParameters
from pydantic import BaseModel, ConfigDict, Field

from taxtrace.planejamento import FalhaPlanejamento, planejar_gemini, planejar_local
from taxtrace.rag import FalhaGeracao, gerar_gemini, preparar_contexto, validar_resposta


class Estado(TypedDict, total=False):
    pergunta: str
    modo: str
    plano: dict
    planejador: dict
    coleta: dict
    respostas: dict
    erro: str
    rastro: list
    resultado: dict
    revisao: dict
    codigo_revisao: str
    versao_revisao: int
    origem_execucao: str
    rag: dict


class DecisaoRevisao(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)
    decisao: Literal["aprovar", "rejeitar"]
    revisor: str = Field(min_length=3, max_length=80)
    motivo: str = Field(min_length=5, max_length=1000)
    origem: Literal["operador_local", "teste_automatizado"]
    dossie_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


def dossie_revisao(estado):
    dados = {k: estado.get(k) for k in ("pergunta", "modo", "plano", "coleta", "respostas")}
    if estado.get("rag") is not None:
        dados["rag"] = estado["rag"]
    checksum = hashlib.sha256(
        json.dumps(dados, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return {
        "escopo": "resposta_e_evidencias"
        if estado.get("rag", {}).get("status") == "respondida"
        else "revisao_documental",
        "dossie": dados,
        "dossie_sha256": checksum,
        "aviso": "A decisão revisa este retrato documental; não valida vigência ou parecer fiscal.",
    }


def criar_grafo(
    cliente,
    raiz,
    *,
    coleta_id=None,
    planejador_ia=planejar_gemini,
    gerador_ia=gerar_gemini,
    checkpointer=None,
    revisao_humana=False,
):
    async def chamar(estado, nome, args):
        chamadas = sum("argumentos" in e for e in estado.get("rastro", []))
        if chamadas >= 3:
            return None, {"etapa": nome, "erro": "limite_de_chamadas"}
        inicio = perf_counter()
        try:
            resposta = await cliente.call_tool(nome, args)
            if resposta.is_error or not isinstance(resposta.structured_content, dict):
                raise ValueError("mcp_falhou")
            dados = resposta.structured_content
            if estado.get("coleta") and any(
                dados["coleta"].get(k) != estado["coleta"].get(k)
                for k in ("id", "manifesto_sha256", "data_consulta")
            ):
                raise ValueError("coleta_divergente")
            return dados, {
                "etapa": nome,
                "argumentos": args,
                "status": dados["status"],
                "duracao_ms": round((perf_counter() - inicio) * 1000, 3),
                "coleta_id": dados["coleta"]["id"],
                "resposta_sha256": hashlib.sha256(
                    json.dumps(dados, sort_keys=True).encode()
                ).hexdigest(),
            }
        except Exception:
            return None, {
                "etapa": nome,
                "argumentos": args,
                "erro": "falha_ou_coleta_divergente",
                "duracao_ms": round((perf_counter() - inicio) * 1000, 3),
            }

    async def planejar(estado):
        try:
            plano, meta = (
                await asyncio.to_thread(planejador_ia, estado["pergunta"], raiz)
                if estado["modo"] == "gemini"
                else planejar_local(estado["pergunta"])
            )
            return {
                "plano": plano.model_dump(),
                "planejador": meta,
                "rastro": [{"etapa": "planejar", "status": "plano_validado", **meta}],
            }
        except FalhaPlanejamento as erro:
            return {"erro": erro.codigo, "rastro": [{"etapa": "planejar", "erro": erro.codigo}]}

    async def base(estado):
        dados, evento = await chamar(estado, "consultar_base", {"coleta_id": coleta_id})
        if dados is None:
            return {"erro": "falha_operacional", "rastro": estado["rastro"] + [evento]}
        return {
            "coleta": dados["coleta"],
            "respostas": {"base": dados},
            "rastro": estado["rastro"] + [evento],
        }

    async def recuperar(estado):
        plano = estado["plano"]
        args = {"coleta_id": estado["coleta"]["id"]}
        if plano["acao"] == "buscar":
            nome = "buscar_artigos"
            args.update(consulta=plano["alvo"], limite=3)
        elif plano["acao"] == "ler_artigo":
            nome = "ler_artigo"
            args.update(
                numero=plano["alvo"], limite_caracteres=8000 if estado["modo"] == "rag" else 3000
            )
        else:
            nome = "consultar_classificacao"
            args.update(codigo=plano["alvo"])
        dados, evento = await chamar(estado, nome, args)
        return {
            "respostas": {**estado["respostas"], "consulta": dados},
            "rastro": estado["rastro"] + [evento],
            **({"erro": "falha_operacional"} if dados is None else {}),
        }

    async def aprofundar(estado):
        r = estado["respostas"]["consulta"]
        candidatos = (
            r.get("resultados", [])
            if estado["plano"]["acao"] == "buscar"
            else r.get("artigos_referenciados", [])
        )
        if not candidatos:
            return {
                "rastro": estado["rastro"]
                + [{"etapa": "aprofundar", "status": "sem_artigo_a_abrir"}]
            }
        # Escolha determinística do primeiro candidato, não julgamento de suficiência.
        numero = candidatos[0]["artigo_numero"]
        dados, evento = await chamar(
            estado,
            "ler_artigo",
            {
                "numero": numero,
                "limite_caracteres": 8000 if estado["modo"] == "rag" else 3000,
                "coleta_id": estado["coleta"]["id"],
            },
        )
        return {
            "respostas": {**estado["respostas"], "artigo": dados},
            "rastro": estado["rastro"] + [evento],
            **({"erro": "falha_operacional"} if dados is None else {}),
        }

    async def conferir(estado):
        try:
            base = estado["respostas"]["base"]
            fontes = {(f["url"], f["sha256"]) for f in base["fontes"]}
            for chave, dados in estado["respostas"].items():
                if chave == "base":
                    continue
                citacoes = ([dados["citacao"]] if "citacao" in dados else []) + dados.get(
                    "fontes", []
                )
                for item in dados.get("resultados", []):
                    if item["citacao"]["artigo"] != item["artigo_numero"]:
                        raise ValueError("artigo_divergente")
                    citacoes.append(item["citacao"])
                for citacao in citacoes:
                    if (
                        citacao["url"],
                        citacao.get("sha256", citacao.get("fonte_sha256")),
                    ) not in fontes:
                        raise ValueError("fonte_divergente")
                if dados.get("status") == "artigo_recuperado":
                    if len(dados["texto"]) != dados["fim"] - dados["inicio"]:
                        raise ValueError("paginacao_divergente")
            return {
                "rastro": estado["rastro"]
                + [{"etapa": "conferir", "status": "coleta_e_referencias_conferidas"}]
            }
        except Exception:
            return {
                "erro": "referencias_inconsistentes",
                "rastro": estado["rastro"]
                + [{"etapa": "conferir", "erro": "referencias_inconsistentes"}],
            }

    async def avaliar_contexto(estado):
        avaliacao = preparar_contexto(estado)
        return {
            "rag": {
                "status": "pronta_para_geracao" if avaliacao["elegivel"] else "recusada",
                "avaliacao": avaliacao,
                "vigencia_verificada": False,
            },
            "rastro": estado["rastro"]
            + [
                {
                    "etapa": "avaliar_contexto",
                    "status": "elegivel_tecnicamente" if avaliacao["elegivel"] else "recusada",
                    "motivo": avaliacao["motivo"],
                    "contexto_sha256": avaliacao["contexto_sha256"],
                }
            ],
        }

    async def gerar_resposta(estado):
        inicio = perf_counter()
        avaliacao = estado["rag"]["avaliacao"]
        try:
            saida, meta = await asyncio.to_thread(gerador_ia, estado["pergunta"], avaliacao, raiz)
            saida = validar_resposta(saida, avaliacao)
            rag = {
                **estado["rag"],
                **saida,
                "modelo": meta,
                "validacao": {"citacoes_literais": True, "implicacao_semantica": "exige_revisao"},
            }
            evento = {
                "etapa": "gerar_resposta",
                "status": saida["status"],
                "resposta_sha256": hashlib.sha256(
                    json.dumps(saida, sort_keys=True).encode()
                ).hexdigest(),
                "duracao_ms": round((perf_counter() - inicio) * 1000, 3),
            }
        except Exception as erro:
            codigo = erro.codigo if isinstance(erro, FalhaGeracao) else "falha_na_geracao"
            rag = {**estado["rag"], "status": "falha", "erro": codigo}
            evento = {
                "etapa": "gerar_resposta",
                "erro": codigo,
                "duracao_ms": round((perf_counter() - inicio) * 1000, 3),
            }
        return {"rag": rag, "rastro": estado["rastro"] + [evento]}

    async def revisar(estado):
        # Somente cálculo puro antes de interrupt: este início é reexecutado na retomada.
        pacote = dossie_revisao(estado)
        decisao = interrupt(pacote, response_schema=DecisaoRevisao)
        if decisao.dossie_sha256 != pacote["dossie_sha256"]:
            raise ValueError("dossie_da_decisao_divergente")
        registrada = {
            **decisao.model_dump(),
            "registrada_em": datetime.now(UTC).isoformat(),
            "identidade_verificada": False,
        }
        return {
            "revisao": registrada,
            "rastro": estado["rastro"]
            + [
                {
                    "etapa": "revisar",
                    "decisao": decisao.decisao,
                    "origem": decisao.origem,
                    "dossie_sha256": decisao.dossie_sha256,
                }
            ],
        }

    async def finalizar(estado):
        r = estado.get("respostas", {}).get("consulta", {}) or {}
        if estado.get("erro"):
            status = "execucao_nao_concluida"
        elif estado.get("revisao"):
            status = (
                (
                    "resposta_documental_aprovada"
                    if estado.get("rag", {}).get("status") == "respondida"
                    else "revisao_documental_aprovada"
                )
                if estado["revisao"]["decisao"] == "aprovar"
                else (
                    "resposta_documental_rejeitada"
                    if estado.get("rag", {}).get("status") == "respondida"
                    else "revisao_documental_rejeitada"
                )
            )
        elif estado.get("rag", {}).get("status") == "falha":
            status = "resposta_indisponivel"
        elif estado.get("rag", {}).get("status") in {
            "recusada",
            "evidencia_insuficiente",
            "fora_do_escopo",
        }:
            status = "evidencia_insuficiente_para_resposta"
        elif estado.get("rag", {}).get("status") == "respondida":
            status = "resposta_documental_gerada"
        elif estado["plano"]["acao"] == "recusar":
            status = "recusado_pelo_planejador"
        elif r.get("status") in {
            "sem_evidencia_na_busca_textual",
            "artigo_nao_encontrado_nesta_coleta",
            "classificacao_nao_encontrada_nesta_coleta",
        }:
            status = "referencia_nao_encontrada_nesta_consulta"
        else:
            status = "evidencias_para_revisao"
        return {
            "resultado": {
                "status": status,
                "suficiencia_para_resposta": estado.get("rag", {}).get("status", "nao_avaliada"),
                "resposta_documental_gerada": estado.get("rag", {}).get("status") == "respondida",
                "vigencia_verificada": False,
                "resposta_fiscal_gerada": False,
                "aprovacao_humana_realizada": (
                    estado.get("revisao", {}).get("origem") == "operador_local"
                    and estado.get("revisao", {}).get("decisao") == "aprovar"
                ),
                "revisao_registrada": bool(estado.get("revisao")),
            },
            "rastro": estado["rastro"] + [{"etapa": "finalizar", "status": status}],
        }

    def depois_plano(e):
        return "finalizar" if e.get("erro") or e["plano"]["acao"] == "recusar" else "base"

    graph = StateGraph(Estado)
    for nome, funcao in (
        ("planejar", planejar),
        ("base", base),
        ("recuperar", recuperar),
        ("aprofundar", aprofundar),
        ("conferir", conferir),
        ("avaliar_contexto", avaliar_contexto),
        ("gerar_resposta", gerar_resposta),
        ("finalizar", finalizar),
    ):
        graph.add_node(nome, funcao)
    graph.add_edge(START, "planejar")
    graph.add_conditional_edges("planejar", depois_plano)
    graph.add_conditional_edges("base", lambda e: "finalizar" if e.get("erro") else "recuperar")
    graph.add_conditional_edges(
        "recuperar", lambda e: "finalizar" if e.get("erro") else "aprofundar"
    )
    graph.add_conditional_edges(
        "aprofundar", lambda e: "finalizar" if e.get("erro") else "conferir"
    )
    if revisao_humana:
        if checkpointer is None:
            raise ValueError("revisao_exige_checkpointer")
        graph.add_node("revisar", revisar)
        graph.add_edge("revisar", "finalizar")

    def depois_conferencia(e):
        if e.get("erro"):
            return "finalizar"
        if e.get("modo") == "rag":
            return "avaliar_contexto"
        ausentes = {
            "sem_evidencia_na_busca_textual",
            "artigo_nao_encontrado_nesta_coleta",
            "classificacao_nao_encontrada_nesta_coleta",
        }
        return (
            "revisar"
            if revisao_humana
            and e.get("respostas", {}).get("consulta", {}).get("status") not in ausentes
            else "finalizar"
        )

    graph.add_conditional_edges("conferir", depois_conferencia)
    graph.add_conditional_edges(
        "avaliar_contexto",
        lambda e: "gerar_resposta" if e["rag"]["avaliacao"]["elegivel"] else "finalizar",
    )
    graph.add_conditional_edges(
        "gerar_resposta",
        lambda e: (
            "revisar" if revisao_humana and e["rag"]["status"] == "respondida" else "finalizar"
        ),
    )
    graph.add_edge("finalizar", END)
    return graph.compile(checkpointer=checkpointer)


async def executar(pergunta, *, modo="local", coleta_id=None):
    if not isinstance(pergunta, str) or not 3 <= len(pergunta.strip()) <= 500:
        raise ValueError("pergunta_invalida")
    if modo not in {"local", "gemini", "rag"} or (
        coleta_id is not None and (type(coleta_id) is not int or coleta_id < 1)
    ):
        raise ValueError("configuracao_invalida")
    raiz = Path(__file__).resolve().parent.parent
    parametros = StdioServerParameters(
        command=sys.executable,
        args=["-m", "taxtrace.servidor_mcp"],
        cwd=raiz,
        env={"PYTHONIOENCODING": "utf-8"},
    )
    with tracing_context(enabled=False):
        async with Client(parametros, read_timeout_seconds=15) as cliente:
            grafo = criar_grafo(cliente, raiz, coleta_id=coleta_id)
            estado = await grafo.ainvoke(
                {"pergunta": pergunta.strip(), "modo": modo, "rastro": []},
                config={"recursion_limit": 10, "callbacks": []},
            )
    return {
        "executado_em": datetime.now(UTC).isoformat(),
        "langgraph": version("langgraph"),
        "transporte": "mcp_stdio_subprocesso_real",
        **estado,
        "limites": [
            "Modo local usa regras, não um modelo de linguagem.",
            "No modo gemini, o modelo planeja; no modo rag, sintetiza os documentos recuperados.",
            "Síntese e citações verificadas não comprovam suficiência jurídica ou vigência.",
            "Abrir o primeiro candidato não comprova relevância ou suficiência.",
            "Esta execução direta não pausa; use o módulo revisao "
            "para checkpoint e decisão registrada.",
        ],
        "codigo_sha256": {
            n: hashlib.sha256((raiz / "taxtrace" / n).read_bytes()).hexdigest()
            for n in ("agente.py", "planejamento.py", "rag.py", "servidor_mcp.py")
        },
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--consulta", required=True)
    parser.add_argument("--modo", choices=["local", "gemini", "rag"], default="local")
    parser.add_argument("--coleta", type=int)
    args = parser.parse_args(argv)
    try:
        report = asyncio.run(executar(args.consulta, modo=args.modo, coleta_id=args.coleta))
        destino = Path(__file__).resolve().parent.parent / "runs" / f"agente-{uuid4()}"
        destino.mkdir(parents=True, exist_ok=False)
        (destino / "execucao.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(
            json.dumps(
                {
                    "registro": str(destino.relative_to(destino.parent.parent)),
                    **report["resultado"],
                },
                ensure_ascii=False,
            )
        )
        return (
            1
            if report["resultado"]["status"] in {"execucao_nao_concluida", "resposta_indisponivel"}
            else 0
        )
    except Exception as erro:
        print(json.dumps({"status": "execucao_nao_concluida", "tipo": type(erro).__name__}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
