"""Autoriza revisões da sessão do navegador, sem expor o token nos registros."""

import hashlib
import re
import sqlite3
import time
from contextlib import closing
from pathlib import Path
from uuid import UUID

COOKIE_VISITANTE = "taxtrace_visitante"
VALIDADE = 30 * 24 * 3600


def dono(token):
    if not isinstance(token, str) or not re.fullmatch(r"[0-9a-f]{64}", token):
        return None
    return hashlib.sha256(token.encode()).hexdigest()


class Propriedade:
    def __init__(self, raiz, relogio=time.time):
        self.caminho = Path(raiz) / "data/checkpoints/acessos.sqlite3"
        self.relogio = relogio

    def vincular(self, revisao_id, proprietario):
        if str(UUID(revisao_id)) != revisao_id or not re.fullmatch(r"[0-9a-f]{64}", proprietario):
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
        if proprietario is None or not self.caminho.exists():
            return False
        with closing(sqlite3.connect(self.caminho, timeout=5)) as conn:
            registro = conn.execute(
                "SELECT 1 FROM acessos WHERE revisao_id=? AND dono=? AND expira_em>?",
                (revisao_id, proprietario, self.relogio()),
            ).fetchone()
        return registro is not None
