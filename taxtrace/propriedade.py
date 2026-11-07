"""Autoriza revisões da sessão do navegador, sem expor o token nos registros."""

import hashlib
import re
import sqlite3
import time
from contextlib import closing
from pathlib import Path
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

from taxtrace.checkpoints import backend, parametros

COOKIE_VISITANTE = "taxtrace_visitante"
VALIDADE = 30 * 24 * 3600


def dono(token):
    if not isinstance(token, str) or not re.fullmatch(r"[0-9a-f]{64}", token):
        return None
    return hashlib.sha256(token.encode()).hexdigest()


def vinculo_valido(revisao_id, proprietario):
    try:
        return (
            isinstance(revisao_id, str)
            and str(UUID(revisao_id)) == revisao_id
            and isinstance(proprietario, str)
            and re.fullmatch(r"[0-9a-f]{64}", proprietario) is not None
        )
    except ValueError:
        return False


class Propriedade:
    def __init__(self, raiz, relogio=time.time):
        self.caminho = Path(raiz) / "data/checkpoints/acessos.sqlite3"
        self.relogio = relogio

    def vincular(self, revisao_id, proprietario):
        if not vinculo_valido(revisao_id, proprietario):
            raise ValueError("vinculo_de_revisao_invalido")
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.caminho, timeout=5)) as conn, conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS acessos ("
                "revisao_id TEXT PRIMARY KEY, dono TEXT NOT NULL, expira_em REAL NOT NULL)"
            )
            conn.execute(
                "INSERT INTO acessos VALUES (?,?,?) ON CONFLICT(revisao_id) DO NOTHING",
                (revisao_id, proprietario, self.relogio() + VALIDADE),
            )
            registro = conn.execute(
                "SELECT dono FROM acessos WHERE revisao_id=?", (revisao_id,)
            ).fetchone()
            if registro[0] != proprietario:
                raise ValueError("revisao_ja_vinculada_a_outra_sessao")

    def permite(self, revisao_id, proprietario):
        if not vinculo_valido(revisao_id, proprietario) or not self.caminho.exists():
            return False
        with closing(sqlite3.connect(self.caminho, timeout=5)) as conn:
            registro = conn.execute(
                "SELECT 1 FROM acessos WHERE revisao_id=? AND dono=? AND expira_em>?",
                (revisao_id, proprietario, self.relogio()),
            ).fetchone()
        return registro is not None


class PropriedadePostgres:
    """Métodos síncronos usados fora do loop web por asyncio.to_thread."""

    def __init__(self, raiz):
        self.raiz = Path(raiz)

    def _conectar(self):
        return psycopg.connect(
            **{**parametros(self.raiz), "application_name": "taxtrace-acessos"},
            prepare_threshold=0,
        )

    def vincular(self, revisao_id, proprietario):
        if not vinculo_valido(revisao_id, proprietario):
            raise ValueError("vinculo_de_revisao_invalido")
        with self._conectar() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "INSERT INTO acessos_revisao (revisao_id,dono,expira_em) "
                "VALUES (%s,%s,clock_timestamp()+(%s * interval '1 second')) "
                "ON CONFLICT (revisao_id) DO NOTHING",
                (revisao_id, proprietario, VALIDADE),
            )
            cur.execute("SELECT dono FROM acessos_revisao WHERE revisao_id=%s", (revisao_id,))
            registro = cur.fetchone()
            if registro is None or registro["dono"] != proprietario:
                raise ValueError("revisao_ja_vinculada_a_outra_sessao")

    def permite(self, revisao_id, proprietario):
        if not vinculo_valido(revisao_id, proprietario):
            return False
        with self._conectar() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM acessos_revisao WHERE revisao_id=%s AND dono=%s "
                "AND expira_em>clock_timestamp()",
                (revisao_id, proprietario),
            )
            return cur.fetchone() is not None


def criar_propriedade(raiz):
    # Uma única escolha mantém checkpoints e autorizações no mesmo backend.
    return PropriedadePostgres(raiz) if backend(raiz) == "postgres" else Propriedade(raiz)
