"""Configuração explícita de origem e limites para uma única instância pública."""

import os
import re
import time
from collections import deque
from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(frozen=True)
class Publicacao:
    origem: str | None
    host: str | None
    ia_habilitada: bool


def configuracao():
    origem = os.environ.get("TAXTRACE_PUBLIC_URL", "")
    if not origem and os.environ.get("RENDER") == "true":
        host = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "")
        if not host:
            raise ValueError("origem_publica_ausente")
        origem = "https://" + host
    if not origem:
        return Publicacao(None, None, True)
    partes = urlsplit(origem)
    host = partes.hostname or ""
    if (
        partes.scheme != "https"
        or not re.fullmatch(
            r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+", host
        )
        or partes.netloc != host
        or partes.path not in {"", "/"}
        or partes.query
        or partes.fragment
    ):
        raise ValueError("origem_publica_invalida")
    opcao = os.environ.get("TAXTRACE_PUBLIC_AI_ENABLED", "false")
    if opcao not in {"true", "false"}:
        raise ValueError("opcao_de_ia_publica_invalida")
    return Publicacao("https://" + host, host, opcao == "true")


class LimitesConsultas:
    """Limites globais em memória por processo; não são uma cota financeira."""

    def __init__(self, relogio=time.monotonic):
        self.relogio = relogio
        self.consultas = deque()
        self.ia = deque()

    def reservar(self, usa_ia):
        agora = self.relogio()
        for fila in (self.consultas, self.ia):
            while fila and fila[0] <= agora - 3600:
                fila.popleft()
        fila, maximo = (self.ia, 20) if usa_ia else (self.consultas, 60)
        if len(self.consultas) >= 60 or len(fila) >= maximo:
            return False
        self.consultas.append(agora)
        if usa_ia:
            self.ia.append(agora)
        return True
