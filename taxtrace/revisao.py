"""Revisão documental local: iniciar, inspecionar e decidir com checkpoint SQLite."""

import argparse
import asyncio
import hashlib
import json
import sys
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from uuid import UUID, uuid4

from filelock import FileLock, Timeout
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.types import Command
from langsmith import tracing_context
from mcp import Client, StdioServerParameters

from taxtrace.agente import DecisaoRevisao, criar_grafo, dossie_revisao

VERSAO = 1


def impressao_codigo():
    raiz = Path(__file__).resolve().parent.parent
    arquivos = [raiz / "requirements.txt"] + [
        raiz / "taxtrace" / n
        for n in (
            "agente.py",
            "planejamento.py",
            "revisao.py",
            "servidor_mcp.py",
            "consultas.py",
            "busca.py",
        )
    ]
    dados = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in arquivos}
    dados["langgraph"] = version("langgraph")
    dados["checkpointer"] = version("langgraph-checkpoint-sqlite")
    return hashlib.sha256(json.dumps(dados, sort_keys=True).encode()).hexdigest()


def validar_id(valor):
    if not isinstance(valor, str):
        raise ValueError("id_de_revisao_invalido")
    try:
        canonico = str(UUID(valor))
    except ValueError:
        raise ValueError("id_de_revisao_invalido") from None
    if valor != canonico:
        raise ValueError("id_de_revisao_invalido")
    return valor


class SemFerramentas:
    async def call_tool(self, *args, **kwargs):
        raise RuntimeError("retomada_nao_deve_consultar_ferramentas")


@asynccontextmanager
async def cliente_mcp(raiz, cliente=None):
    if cliente is not None:
        yield cliente
    else:
        parametros = StdioServerParameters(
            command=sys.executable,
            args=["-m", "taxtrace.servidor_mcp"],
            cwd=raiz,
            env={"PYTHONIOENCODING": "utf-8"},
        )
        async with Client(parametros, read_timeout_seconds=15) as remoto:
            yield remoto


def caminhos(raiz, revisao_id):
    validar_id(revisao_id)
    pasta = raiz / "data/checkpoints"
    return pasta / "revisoes.sqlite3", pasta / f"{revisao_id}.lock"


def config(revisao_id):
    return {"configurable": {"thread_id": revisao_id}, "recursion_limit": 12, "callbacks": []}


def retrato(snapshot, revisao_id):
    estado = dict(snapshot.values)
    if not estado:
        raise ValueError("revisao_nao_encontrada")
    interrupcoes = [i for t in snapshot.tasks for i in t.interrupts]
    pendente = tuple(snapshot.next) == ("revisar",) and len(interrupcoes) == 1
    return {
        "revisao_id": revisao_id,
        "status": "aguardando_revisao"
        if pendente
        else estado.get("resultado", {}).get("status", "execucao_nao_concluida"),
        "pendente": pendente,
        "estado": estado,
        "pacote_revisao": dossie_revisao(estado),
        "codigo_compativel": estado.get("codigo_revisao") == impressao_codigo(),
        "escopo": "snapshot_documental_local_sem_validacao_juridica",
    }


def registrar(raiz, retrato_atual, operacao):
    pasta = raiz / "runs" / f"revisao-{uuid4()}"
    pasta.mkdir(parents=True, exist_ok=False)
    documento = {
        "registrado_em": datetime.now(UTC).isoformat(),
        "operacao": operacao,
        **retrato_atual,
    }
    (pasta / "evento.json").write_text(
        json.dumps(documento, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return {**retrato_atual, "registro": str(pasta.relative_to(raiz))}


async def iniciar(pergunta, *, modo="local", coleta_id=None, raiz=None, cliente=None):
    if not isinstance(pergunta, str) or not 3 <= len(pergunta.strip()) <= 500:
        raise ValueError("pergunta_invalida")
    if modo not in {"local", "gemini"} or (
        coleta_id is not None and (type(coleta_id) is not int or coleta_id < 1)
    ):
        raise ValueError("configuracao_invalida")
    raiz = Path(raiz) if raiz else Path(__file__).resolve().parent.parent
    revisao_id = str(uuid4())
    banco, trava = caminhos(raiz, revisao_id)
    banco.parent.mkdir(parents=True, exist_ok=True)
    with FileLock(trava, timeout=0), tracing_context(enabled=False):
        async with AsyncSqliteSaver.from_conn_string(str(banco)) as saver:
            async with cliente_mcp(raiz, cliente) as remoto:
                grafo = criar_grafo(
                    remoto, raiz, coleta_id=coleta_id, checkpointer=saver, revisao_humana=True
                )
                await grafo.ainvoke(
                    {
                        "pergunta": pergunta.strip(),
                        "modo": modo,
                        "rastro": [],
                        "versao_revisao": VERSAO,
                        "codigo_revisao": impressao_codigo(),
                        "origem_execucao": "mcp_stdio_real"
                        if cliente is None
                        else "cliente_sintetico_de_teste",
                    },
                    config(revisao_id),
                )
                atual = retrato(await grafo.aget_state(config(revisao_id)), revisao_id)
        return registrar(raiz, atual, "iniciar")


async def inspecionar(revisao_id, *, raiz=None):
    raiz = Path(raiz) if raiz else Path(__file__).resolve().parent.parent
    banco, trava = caminhos(raiz, revisao_id)
    if not banco.is_file():
        raise ValueError("revisao_nao_encontrada")
    with FileLock(trava, timeout=0), tracing_context(enabled=False):
        async with AsyncSqliteSaver.from_conn_string(str(banco)) as saver:
            grafo = criar_grafo(SemFerramentas(), raiz, checkpointer=saver, revisao_humana=True)
            atual = retrato(await grafo.aget_state(config(revisao_id)), revisao_id)
        return registrar(raiz, atual, "inspecionar")


async def decidir(revisao_id, decisao, *, raiz=None):
    decisao = DecisaoRevisao.model_validate(decisao)
    raiz = Path(raiz) if raiz else Path(__file__).resolve().parent.parent
    banco, trava = caminhos(raiz, revisao_id)
    if not banco.is_file():
        raise ValueError("revisao_nao_encontrada")
    with FileLock(trava, timeout=0), tracing_context(enabled=False):
        async with AsyncSqliteSaver.from_conn_string(str(banco)) as saver:
            grafo = criar_grafo(SemFerramentas(), raiz, checkpointer=saver, revisao_humana=True)
            antes = retrato(await grafo.aget_state(config(revisao_id)), revisao_id)
            if not antes["pendente"]:
                raise ValueError("revisao_nao_pendente")
            if not antes["codigo_compativel"] or antes["estado"].get("versao_revisao") != VERSAO:
                raise ValueError("codigo_alterado_inicie_nova_revisao")
            if antes["pacote_revisao"]["dossie_sha256"] != decisao.dossie_sha256:
                raise ValueError("dossie_da_decisao_divergente")
            await grafo.ainvoke(Command(resume=decisao.model_dump()), config(revisao_id))
            depois = retrato(await grafo.aget_state(config(revisao_id)), revisao_id)
        return registrar(raiz, depois, "decidir")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    comandos = parser.add_subparsers(dest="acao", required=True)
    novo = comandos.add_parser("iniciar")
    novo.add_argument("--consulta", required=True)
    novo.add_argument("--modo", choices=["local", "gemini"], default="local")
    novo.add_argument("--coleta", type=int)
    olhar = comandos.add_parser("inspecionar")
    olhar.add_argument("--revisao", required=True)
    retomar = comandos.add_parser("decidir")
    retomar.add_argument("--revisao", required=True)
    retomar.add_argument("--decisao", choices=["aprovar", "rejeitar"], required=True)
    retomar.add_argument("--revisor", required=True)
    retomar.add_argument("--motivo", required=True)
    retomar.add_argument(
        "--origem", choices=["operador_local", "teste_automatizado"], required=True
    )
    retomar.add_argument("--dossie-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        if args.acao == "iniciar":
            futuro = iniciar(args.consulta, modo=args.modo, coleta_id=args.coleta)
        elif args.acao == "inspecionar":
            futuro = inspecionar(args.revisao)
        else:
            futuro = decidir(
                args.revisao,
                {
                    "decisao": args.decisao,
                    "revisor": args.revisor,
                    "motivo": args.motivo,
                    "origem": args.origem,
                    "dossie_sha256": args.dossie_sha256,
                },
            )
        report = asyncio.run(futuro)
        print(
            json.dumps(
                {
                    "status": report["status"],
                    "revisao_id": report["revisao_id"],
                    "dossie_sha256": report["pacote_revisao"]["dossie_sha256"],
                    "registro": report["registro"],
                },
                ensure_ascii=False,
            )
        )
        return 1 if report["status"] == "execucao_nao_concluida" else 0
    except Timeout:
        print(json.dumps({"status": "revisao_em_uso_tente_novamente"}))
        return 1
    except Exception as erro:
        seguros = {
            "id_de_revisao_invalido",
            "revisao_nao_encontrada",
            "revisao_nao_pendente",
            "codigo_alterado_inicie_nova_revisao",
            "dossie_da_decisao_divergente",
            "pergunta_invalida",
            "configuracao_invalida",
        }
        codigo = (
            str(erro)
            if type(erro) is ValueError and str(erro) in seguros
            else "falha_ou_decisao_invalida"
        )
        print(json.dumps({"status": "operacao_nao_concluida", "codigo": codigo}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
