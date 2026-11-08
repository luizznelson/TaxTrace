"""Planeja por padrão; aplica somente com hash do plano aprovado pelo operador."""

import argparse
import asyncio
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

import psycopg
from dotenv import dotenv_values
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict
from psycopg.rows import dict_row

from taxtrace import banco, checkpoints, lei, tabelas
from taxtrace.integridade import verificar
from taxtrace.remoto import opcoes_neon


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def parametros_admin(cfg, *, leitura=True):
    raw = conninfo_to_dict(cfg["TAXTRACE_NEON_ADMIN_URL"])
    profile = {
        "TAXTRACE_DATABASE_MODE": "neon",
        "TAXTRACE_NEON_HOST": cfg["TAXTRACE_NEON_HOST"],
        "TAXTRACE_NEON_DATABASE": cfg["TAXTRACE_NEON_DATABASE"],
    }
    params = opcoes_neon({**raw, "user": "taxtrace_reader"}, "taxtrace_reader", ambiente=profile)
    if raw["user"] in {"taxtrace_reader", "taxtrace_state"}:
        raise ValueError("use_conexao_administrativa_no_perfil_privado")
    params.update(
        user=raw["user"],
        connect_timeout=10,
        application_name="taxtrace-neon-preparation",
        options=(
            "-c statement_timeout=30000 "
            f"-c default_transaction_read_only={'on' if leitura else 'off'}"
        ),
    )
    return params


def inventario(cfg):
    params = parametros_admin(cfg)
    with psycopg.connect(**params, row_factory=dict_row) as conn:
        if not conn.pgconn.ssl_in_use:
            raise ValueError("conexao_sem_tls")
        who = conn.execute(
            "SELECT current_database() AS banco,current_user AS papel,"
            "current_setting('transaction_read_only') AS somente_leitura"
        ).fetchone()
        if (
            who["banco"] != params["dbname"]
            or who["papel"] != params["user"]
            or who["somente_leitura"] != "on"
        ):
            raise ValueError("identidade_do_destino_divergente")
        tables = conn.execute(
            "SELECT schemaname,tablename FROM pg_tables "
            "WHERE schemaname NOT IN ('pg_catalog','information_schema') ORDER BY 1,2"
        ).fetchall()
        roles = conn.execute(
            "SELECT rolname FROM pg_roles "
            "WHERE rolname IN ('taxtrace_reader','taxtrace_state') ORDER BY 1"
        ).fetchall()
        workflow = conn.execute(
            "SELECT nspname FROM pg_namespace WHERE nspname='taxtrace_workflow'"
        ).fetchall()
        vector = conn.execute(
            "SELECT default_version,installed_version FROM pg_available_extensions "
            "WHERE name='vector'"
        ).fetchone()
        server_tls = conn.execute(
            "SELECT ssl,version,cipher FROM pg_stat_ssl WHERE pid=pg_backend_pid()"
        ).fetchone()
    return {
        "identificacao": who,
        "tls_cliente": {"ativo": True, "modo": "verify-full", "channel_binding": "require"},
        "estatistica_ssl_backend": server_tls,
        "tabelas": tables,
        "papeis": roles,
        "schema_workflow": workflow,
        "vector": vector,
    }


def plano(raiz, arquivo, pasta):
    cfg = dotenv_values(arquivo)
    for key in ("TAXTRACE_NEON_READER_PASSWORD", "TAXTRACE_NEON_STATE_PASSWORD"):
        if not cfg.get(key) or len(cfg[key]) < 12:
            raise ValueError("complete_o_perfil_privado_antes_de_planejar")
    if cfg["TAXTRACE_NEON_READER_PASSWORD"] == cfg["TAXTRACE_NEON_STATE_PASSWORD"]:
        raise ValueError("senhas_de_runtime_devem_ser_distintas")
    manifest, checksum = verificar(pasta, exigir_lei=True)
    captured = tabelas.carregar(pasta)
    articles = lei.ler_artigos((pasta / "lc214_planalto.html").read_bytes())
    inventory = inventario(cfg)
    if inventory["tabelas"] or inventory["papeis"] or inventory["schema_workflow"]:
        raise ValueError("destino_nao_vazio_exige_revisao_manual")
    if inventory["vector"] is None:
        raise ValueError("extensao_vector_indisponivel")
    files = ("requirements.txt", "taxtrace/schema.sql") + tuple(
        str(path.relative_to(raiz)).replace("\\", "/")
        for path in sorted((raiz / "taxtrace").glob("*.py"))
    )
    document = {
        "versao": 1,
        "destino": {
            "banco": cfg["TAXTRACE_NEON_DATABASE"],
            "endpoint_sha256": digest(cfg["TAXTRACE_NEON_HOST"]),
        },
        "precondicoes": {
            "tabelas_existentes": 0,
            "papeis_runtime_existentes": 0,
            "schema_workflow_existente": False,
        },
        "captura": {
            "manifesto_sha256": checksum,
            "capturada_em": manifest["coletado_em"],
            "data_api": manifest["data_consulta"],
            "versao_base": captured.versao.base,
            "artigos": len(articles),
            "classificacoes": len(captured.classificacoes),
            "ncm": len(captured.ncm),
            "fontes": len(manifest["arquivos"]),
            "manifesto_preservado": True,
        },
        "acoes": [
            "criar taxtrace_reader e taxtrace_state sem privilégios administrativos",
            "preparar extensão vector e tabelas de fontes",
            "importar captura e preservar seis fontes e manifesto",
            "preparar schema taxtrace_workflow com checkpoints, eventos e vínculos",
            "conceder leitura de fontes e permissões mínimas de estado",
            "gravar configuração de runtime local privada, sem URI administrativa",
        ],
        "codigo_sha256": {
            name: hashlib.sha256((raiz / name).read_bytes()).hexdigest() for name in files
        },
        "exclusoes": [
            "não alterar banco de desenvolvimento",
            "não substituir roles existentes ou importar dados em destino não vazio",
            "não transferir históricos SQLite",
            "não publicar app, criar serviço ou contratar recurso",
        ],
    }
    return {
        "plano": document,
        "plano_sha256": digest(document),
        "preflight": inventory,
        "objetos_criados": False,
    }


async def preparar_estado(cfg):
    async with await psycopg.AsyncConnection.connect(
        **parametros_admin(cfg, leitura=False),
        autocommit=True,
        prepare_threshold=0,
        row_factory=dict_row,
    ) as conn:
        await checkpoints.preparar_estruturas(conn)
        await checkpoints.conceder_permissoes_estado(conn)


def url_runtime(cfg, role, key):
    return (
        "postgresql://"
        + quote(role, safe="")
        + ":"
        + quote(cfg[key], safe="")
        + "@"
        + cfg["TAXTRACE_NEON_HOST"]
        + ":5432/"
        + quote(cfg["TAXTRACE_NEON_DATABASE"], safe="")
        + "?sslmode=verify-full&channel_binding=require"
    )


def aplicar(raiz, arquivo, pasta, aprovado):
    current = plano(raiz, arquivo, pasta)
    if not aprovado or current["plano_sha256"] != aprovado:
        raise ValueError("plano_divergente_nao_aplicado")
    runtime = raiz / ".env.neon.runtime"
    if runtime.exists():
        raise ValueError("runtime_privado_existente_nao_sobrescrever")
    cfg = dotenv_values(arquivo)
    with psycopg.connect(**parametros_admin(cfg, leitura=False)) as conn:
        with conn.transaction():
            # CREATE sem IF NOT EXISTS: uma criação concorrente aborta sem trocar senha.
            for role, key in (
                ("taxtrace_reader", "TAXTRACE_NEON_READER_PASSWORD"),
                ("taxtrace_state", "TAXTRACE_NEON_STATE_PASSWORD"),
            ):
                conn.execute(
                    sql.SQL(
                        "CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE "
                        "NOREPLICATION NOBYPASSRLS NOINHERIT PASSWORD {}"
                    ).format(sql.Identifier(role), sql.Literal(cfg[key]))
                )
            banco.criar_esquema(conn)
            banco.preparar_leitor(conn, cfg["TAXTRACE_NEON_READER_PASSWORD"])
            cid = banco.carregar_pasta(conn, pasta)
            loaded = conn.execute(
                "SELECT manifesto_sha256 FROM coletas WHERE id=%s", (cid,)
            ).fetchone()
            if loaded[0] != current["plano"]["captura"]["manifesto_sha256"]:
                raise ValueError("captura_alterada_nao_aplicada")
    try:
        asyncio.run(
            preparar_estado(cfg),
            loop_factory=asyncio.SelectorEventLoop if sys.platform == "win32" else None,
        )
    except Exception:
        raise ValueError("fontes_importadas_estado_nao_concluido_revisar_destino") from None
    values = {
        "TAXTRACE_DATABASE_MODE": "neon",
        "TAXTRACE_NEON_HOST": cfg["TAXTRACE_NEON_HOST"],
        "TAXTRACE_NEON_DATABASE": cfg["TAXTRACE_NEON_DATABASE"],
        "TAXTRACE_CHECKPOINT_BACKEND": "postgres",
        "TAXTRACE_READER_DATABASE_URL": url_runtime(
            cfg, "taxtrace_reader", "TAXTRACE_NEON_READER_PASSWORD"
        ),
        "TAXTRACE_CHECKPOINT_DATABASE_URL": url_runtime(
            cfg, "taxtrace_state", "TAXTRACE_NEON_STATE_PASSWORD"
        ),
    }
    with runtime.open("x", encoding="utf-8") as f:
        f.write("# Runtime privado; nunca publicar. Sem credencial administrativa.\n")
        for key, value in values.items():
            f.write(key + "='" + value.replace("'", "\\'") + "'\n")
    return {
        "status": "estrutura_neon_preparada",
        "plano_sha256": aprovado,
        "coleta_id": cid,
        "runtime_privado_criado": True,
        "deploy_realizado": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arquivo", type=Path)
    parser.add_argument("--pasta", type=Path)
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--aplicar", action="store_true")
    parser.add_argument("--plano-sha256")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    if args.saida.exists():
        parser.error("Registro já existe; escolha outro arquivo.")
    try:
        arquivo = args.arquivo or root / ".env.neon"
        pasta = args.pasta or tabelas.pasta_mais_recente(root / "data/raw")
        result = (
            aplicar(root, arquivo, pasta, args.plano_sha256)
            if args.aplicar
            else plano(root, arquivo, pasta)
        )
    except Exception as error:
        seguros = {
            "destino_nao_vazio_exige_revisao_manual",
            "plano_divergente_nao_aplicado",
            "runtime_privado_existente_nao_sobrescrever",
            "fontes_importadas_estado_nao_concluido_revisar_destino",
        }
        result = {
            "status": "preparacao_nao_concluida",
            "codigo": str(error)
            if type(error) is ValueError and str(error) in seguros
            else "configuracao_ou_conexao_recusada",
            "fase": "aplicar" if args.aplicar else "planejar",
        }
    result = {"registrado_em": datetime.now(UTC).isoformat(), **result}
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    with args.saida.open("x", encoding="utf-8") as f:
        f.write(json.dumps(result, ensure_ascii=False, indent=2, default=str) + "\n")
    print(
        json.dumps(
            {
                "registro": str(args.saida),
                "plano_sha256": result.get("plano_sha256"),
                "status": result.get("status", "plano_preparado"),
            },
            ensure_ascii=False,
        )
    )
    return 1 if result.get("status") == "preparacao_nao_concluida" else 0


if __name__ == "__main__":
    raise SystemExit(main())
