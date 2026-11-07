"""Conexões de manutenção, leitura e testes com destinos separados."""

import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg.conninfo import conninfo_to_dict

from taxtrace.remoto import opcoes_neon


def opcoes(raiz: Path, *, teste=False, leitura=False) -> dict:
    load_dotenv(raiz / ".env", override=False)
    if teste:
        if os.environ.get("TAXTRACE_TEST_DATABASE") != "1":
            raise ValueError("teste_exige_opt_in")
        chave = "TAXTRACE_TEST_DATABASE_URL"
    else:
        chave = "TAXTRACE_READER_DATABASE_URL" if leitura else "DATABASE_URL"
    try:
        valor = os.environ.get(chave)
        if not valor:
            raise ValueError("conexao_ausente")
        params = conninfo_to_dict(valor)
    except Exception:
        raise ValueError("configuracao_de_conexao_invalida") from None
    if any(params.get(k) for k in ("service", "hostaddr")):
        raise ValueError("destino_explicito_obrigatorio")
    local = params.get("host") in {"127.0.0.1", "::1", "localhost"}
    if teste:
        if not (
            local
            and params.get("dbname") == "taxtrace_test"
            and params.get("user") == "taxtrace_test"
            and str(params.get("port")) == "15434"
        ):
            raise ValueError("teste_exige_banco_local_isolado")
    elif not local:
        # Exceção explícita para leitura no serviço privado do Compose local.
        compose = (
            os.environ.get("TAXTRACE_DATABASE_MODE") == "compose"
            and leitura
            and params.get("host") == "db"
            and str(params.get("port")) == "5432"
            and params.get("dbname") == "taxtrace"
        )
        if not compose:
            if leitura and os.environ.get("TAXTRACE_DATABASE_MODE") == "neon":
                params = opcoes_neon(params, "taxtrace_reader")
            else:
                raise ValueError("somente_banco_local_nesta_etapa")
    if leitura and params.get("user") != "taxtrace_reader":
        raise ValueError("leitura_exige_login_restrito")
    params.update(connect_timeout=5, application_name="taxtrace-test" if teste else "taxtrace")
    if leitura:
        params["options"] = "-c default_transaction_read_only=on -c statement_timeout=5000"
    return params


def conectar(raiz: Path, *, teste=False, leitura=False, **kwargs):
    return psycopg.connect(**opcoes(raiz, teste=teste, leitura=leitura), **kwargs)


def ambiente_mcp(raiz: Path) -> dict:
    """Encaminha somente a conexão de leitura; nunca a chave de IA ou a de manutenção."""
    load_dotenv(raiz / ".env", override=False)
    return {
        "PYTHONIOENCODING": "utf-8",
        **{
            chave: os.environ[chave]
            for chave in (
                "TAXTRACE_READER_DATABASE_URL",
                "TAXTRACE_DATABASE_MODE",
                "TAXTRACE_NEON_HOST",
                "TAXTRACE_NEON_DATABASE",
            )
            if os.environ.get(chave)
        },
    }
