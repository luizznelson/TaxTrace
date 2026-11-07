"""Checkpoint PostgreSQL opt-in; SQLite continua disponível no desenvolvimento."""

import argparse
import asyncio
import hashlib
import json
import os
import sys
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import psycopg
from dotenv import load_dotenv
from filelock import Timeout
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict
from psycopg.rows import dict_row

from taxtrace.conexao import opcoes

SCHEMA = "taxtrace_workflow"
OPTIONS = "-c search_path=taxtrace_workflow,pg_catalog -c statement_timeout=10000"


def backend(raiz):
    load_dotenv(Path(raiz) / ".env", override=False)
    valor = os.environ.get("TAXTRACE_CHECKPOINT_BACKEND", "sqlite")
    if valor not in {"sqlite", "postgres"}:
        raise ValueError("backend_de_checkpoint_invalido")
    return valor


def parametros(raiz):
    load_dotenv(Path(raiz) / ".env", override=False)
    try:
        p = conninfo_to_dict(os.environ["TAXTRACE_CHECKPOINT_DATABASE_URL"])
    except Exception:
        raise ValueError("conexao_de_checkpoint_invalida") from None
    local = p.get("host") in {"localhost", "127.0.0.1", "::1"} and str(p.get("port")) == "15433"
    compose = (
        os.environ.get("TAXTRACE_DATABASE_MODE") == "compose"
        and p.get("host") == "db"
        and str(p.get("port")) == "5432"
    )
    if (
        not (local or compose)
        or p.get("dbname") != "taxtrace"
        or p.get("user") != "taxtrace_state"
        or any(p.get(k) for k in ("service", "hostaddr", "options", "replication"))
    ):
        raise ValueError("destino_de_checkpoint_nao_permitido")
    return {
        **p,
        "connect_timeout": 5,
        "application_name": "taxtrace-checkpoints",
        "options": OPTIONS,
    }


def chave_trava(revisao_id):
    canonico = str(UUID(revisao_id))
    if canonico != revisao_id:
        raise ValueError("id_de_revisao_invalido")
    return int.from_bytes(hashlib.sha256(canonico.encode()).digest()[:8], "big", signed=True)


@asynccontextmanager
async def abrir_postgres(raiz, revisao_id):
    if sys.platform == "win32":
        # MCP precisa de subprocessos (Proactor); psycopg async precisa de Selector.
        raise ValueError("checkpoint_postgres_exige_runtime_linux")
    # Conexão direta de sessão; não usar pool transacional para advisory locks.
    async with await psycopg.AsyncConnection.connect(
        **parametros(raiz), autocommit=True, prepare_threshold=0, row_factory=dict_row
    ) as conn:
        cur = await conn.execute(
            "SELECT pg_try_advisory_lock(%s) AS obteve", (chave_trava(revisao_id),)
        )
        if not (await cur.fetchone())["obteve"]:
            raise Timeout("checkpoint-postgres")
        # O contexto da conexão libera a trava inclusive em falha/cancelamento.
        yield AsyncPostgresSaver(conn), conn


async def registrar_evento(conn, retrato, operacao):
    if operacao not in {"iniciar", "inspecionar", "decidir"}:
        raise ValueError("operacao_de_revisao_invalida")
    evento_id = str(uuid4())
    documento = {"registrado_em": datetime.now(UTC).isoformat(), "operacao": operacao, **retrato}
    serializado = json.dumps(documento, ensure_ascii=False, sort_keys=True, default=str)
    await conn.execute(
        "INSERT INTO eventos_revisao (id,revisao_id,operacao,documento,sha256) "
        "VALUES (%s,%s,%s,%s,%s)",
        (
            evento_id,
            retrato["revisao_id"],
            operacao,
            serializado,
            hashlib.sha256(serializado.encode()).hexdigest(),
        ),
    )
    return {**retrato, "registro": f"postgres:evento:{evento_id}"}


async def preparar_estruturas(conn):
    await conn.execute("CREATE SCHEMA IF NOT EXISTS taxtrace_workflow")
    await conn.execute("REVOKE ALL ON SCHEMA taxtrace_workflow FROM PUBLIC")
    await conn.execute("SET search_path=taxtrace_workflow,pg_catalog")
    await AsyncPostgresSaver(conn).setup()
    await conn.execute("""CREATE TABLE IF NOT EXISTS eventos_revisao (
        id UUID PRIMARY KEY, revisao_id UUID NOT NULL,
        operacao TEXT NOT NULL CHECK (operacao IN ('iniciar','inspecionar','decidir')),
        documento TEXT NOT NULL CHECK (jsonb_typeof(documento::jsonb)='object'),
        sha256 CHAR(64) NOT NULL,
        registrado_em TIMESTAMPTZ NOT NULL DEFAULT now()
    )""")


async def preparar(raiz):
    # Manutenção explícita pelo administrador local; nunca executada pelo servidor web.
    async with await psycopg.AsyncConnection.connect(
        **opcoes(raiz), autocommit=True, prepare_threshold=0, row_factory=dict_row
    ) as conn:
        senha = os.environ.get("TAXTRACE_CHECKPOINT_PASSWORD", "")
        if len(senha) < 12:
            raise ValueError("senha_de_checkpoint_ausente_ou_curta")
        existe = await conn.execute("SELECT 1 FROM pg_roles WHERE rolname='taxtrace_state'")
        if not await existe.fetchone():
            await conn.execute(
                sql.SQL(
                    "CREATE ROLE taxtrace_state LOGIN NOSUPERUSER NOCREATEDB "
                    "NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD {}"
                ).format(sql.Literal(senha))
            )
        # Papel existente não recebe troca de senha implícita.
        cur = await conn.execute(
            "SELECT rolname FROM pg_roles WHERE rolname='taxtrace_state' "
            "AND NOT rolsuper AND NOT rolcreatedb AND NOT rolcreaterole AND NOT rolbypassrls "
            "AND NOT rolreplication AND NOT EXISTS "
            "(SELECT 1 FROM pg_auth_members WHERE member=pg_roles.oid)"
        )
        if not await cur.fetchone():
            raise ValueError("crie_papel_restrito_taxtrace_state_antes_da_preparacao")
        await preparar_estruturas(conn)
        await conn.execute("GRANT USAGE ON SCHEMA taxtrace_workflow TO taxtrace_state")
        await conn.execute(
            "REVOKE ALL ON ALL TABLES IN SCHEMA taxtrace_workflow FROM taxtrace_state"
        )
        await conn.execute(
            "GRANT SELECT,INSERT,UPDATE,DELETE ON checkpoints,checkpoint_blobs,"
            "checkpoint_writes TO taxtrace_state"
        )
        await conn.execute("GRANT SELECT ON checkpoint_migrations TO taxtrace_state")
        await conn.execute("GRANT SELECT,INSERT ON eventos_revisao TO taxtrace_state")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("acao", choices=["preparar"])
    parser.parse_args()
    try:
        asyncio.run(
            preparar(Path(__file__).resolve().parent.parent),
            loop_factory=asyncio.SelectorEventLoop if sys.platform == "win32" else None,
        )
    except Exception:
        print(
            json.dumps(
                {
                    "status": "preparacao_nao_concluida",
                    "orientacao": (
                        "Confira conexão local e TAXTRACE_CHECKPOINT_PASSWORD; "
                        "consulte docs/PERSISTENCIA.md."
                    ),
                }
            )
        )
        return 1
    print(json.dumps({"status": "checkpoint_postgres_preparado"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
