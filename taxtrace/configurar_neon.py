"""Completa somente o arquivo privado; não conecta nem cria objetos no Neon."""

import argparse
import secrets
import shlex
from pathlib import Path

from dotenv import dotenv_values, set_key
from psycopg.conninfo import conninfo_to_dict

from taxtrace.remoto import opcoes_neon


def completar(caminho):
    caminho = Path(caminho)
    cfg = dotenv_values(caminho)
    uri = (cfg.get("TAXTRACE_NEON_ADMIN_URL") or "").strip()
    try:
        if uri.startswith("psql "):
            partes = shlex.split(uri)
            if len(partes) != 2 or partes[0] != "psql":
                raise ValueError
            uri = partes[1]
        if not uri.startswith(("postgresql://", "postgres://")) or any(ord(c) < 32 for c in uri):
            raise ValueError
        parsed = conninfo_to_dict(uri)
        if not parsed.get("user") or not parsed.get("password"):
            raise ValueError
        host, database = parsed["host"], parsed["dbname"]
        opcoes_neon(
            {**parsed, "user": "taxtrace_reader"},
            "taxtrace_reader",
            ambiente={
                "TAXTRACE_DATABASE_MODE": "neon",
                "TAXTRACE_NEON_HOST": host,
                "TAXTRACE_NEON_DATABASE": database,
            },
        )
    except Exception:
        raise ValueError("copie_a_uri_direta_do_projeto_neon_sem_pooling") from None
    valores = {
        "TAXTRACE_NEON_ADMIN_URL": uri,
        "TAXTRACE_NEON_HOST": host,
        "TAXTRACE_NEON_DATABASE": database,
    }
    for key in ("TAXTRACE_NEON_READER_PASSWORD", "TAXTRACE_NEON_STATE_PASSWORD"):
        value = cfg.get(key) or secrets.token_urlsafe(32)
        if len(value) < 12 or any(ord(c) < 32 for c in value):
            raise ValueError("senha_de_runtime_curta_ou_invalida")
        valores[key] = value
    if valores["TAXTRACE_NEON_READER_PASSWORD"] == valores["TAXTRACE_NEON_STATE_PASSWORD"]:
        raise ValueError("use_senhas_distintas_para_os_papeis")
    for key, value in valores.items():
        set_key(str(caminho), key, value)
    return {
        "status": "configuracao_privada_preparada",
        "conexao_executada": False,
        "objetos_criados": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--arquivo", type=Path, default=Path(__file__).resolve().parent.parent / ".env.neon"
    )
    args = parser.parse_args()
    try:
        completar(args.arquivo)
    except ValueError, OSError:
        print(
            "Não foi possível preparar. Confira a URI direta no arquivo privado; "
            "não envie o valor pelo chat."
        )
        return 1
    print("Arquivo privado preparado. Nenhuma conexão, tabela ou papel foi criado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
