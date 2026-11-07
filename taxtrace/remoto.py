"""Política explícita de runtime Neon; não libera manutenção remota."""

import os
import re

import certifi


def opcoes_neon(params, papel, *, ambiente=None):
    ambiente = os.environ if ambiente is None else ambiente
    host = ambiente.get("TAXTRACE_NEON_HOST", "")
    database = ambiente.get("TAXTRACE_NEON_DATABASE", "taxtrace")
    permitidos = {"host", "port", "dbname", "user", "password", "sslmode", "channel_binding"}
    if (
        ambiente.get("TAXTRACE_DATABASE_MODE") != "neon"
        or not re.fullmatch(r"ep-[a-z0-9-]+(?:\.[a-z0-9-]+)+\.neon\.tech", host)
        or "-pooler" in host.split(".")[0]
        or not re.fullmatch(r"[a-z][a-z0-9_]{2,62}", database)
        or params.get("host") != host
        or params.get("dbname") != database
        or params.get("user") != papel
        or papel not in {"taxtrace_reader", "taxtrace_state"}
        or str(params.get("port", "5432")) != "5432"
        or not params.get("password")
        or set(params) - permitidos
        or params.get("sslmode") not in {None, "require", "verify-full"}
        or params.get("channel_binding") not in {None, "require"}
    ):
        raise ValueError("destino_remoto_nao_permitido")
    return {
        **params,
        "port": "5432",
        "sslmode": "verify-full",
        "sslrootcert": certifi.where(),
        "ssl_min_protocol_version": "TLSv1.2",
        "channel_binding": "require",
    }
