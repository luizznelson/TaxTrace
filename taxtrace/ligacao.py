"""Liga cada cClassTrib ao(s) artigo(s) da LC 214 citados no seu fundamento legal."""

import re
from dataclasses import dataclass

from taxtrace.lei import Artigo
from taxtrace.tabelas import Classificacao

_PLURAL = re.compile(r"Arts\.?\s*((?:\d+(?:-[A-Z]{1,2})?º?(?:\s*(?:,|e)\s*)?)+)")
_SINGULAR = re.compile(r"Art\.?\s*(\d+(?:-[A-Z]{1,2})?)")
_NUMERO = re.compile(r"\d+(?:-[A-Z]{1,2})?")


def numeros_de_artigos(texto_curto: str) -> tuple[str, ...]:
    """Extrai os números de artigo de um fundamento como "Art. 93, IV e Art. 93, § 4º".

    Devolve na ordem em que aparecem, sem repetir. "LC 214/2025" (regra geral) não cita
    artigo e devolve vazio.
    """
    achados: list[str] = []
    for m in _PLURAL.finditer(texto_curto):
        achados.extend(_NUMERO.findall(m.group(1)))
    restante = _PLURAL.sub(" ", texto_curto)
    achados.extend(m.group(1) for m in _SINGULAR.finditer(restante))
    return tuple(dict.fromkeys(achados))


@dataclass(frozen=True, slots=True)
class Ligacao:
    codigo: str
    texto_curto: str
    artigos: tuple[str, ...]
    ausentes: tuple[str, ...]
    regra_geral: bool


def ligar(classificacoes: tuple[Classificacao, ...], artigos: list[Artigo]) -> list[Ligacao]:
    """Para cada classificação, separa os artigos achados na lei dos que não foram achados."""
    existentes = {a.numero for a in artigos}
    resultado = []
    for c in classificacoes:
        citados = numeros_de_artigos(c.texto_curto)
        resultado.append(
            Ligacao(
                codigo=c.codigo,
                texto_curto=c.texto_curto,
                artigos=tuple(n for n in citados if n in existentes),
                ausentes=tuple(n for n in citados if n not in existentes),
                regra_geral=not citados,
            )
        )
    return resultado
