"""Preparação conservadora de consultas: acentos ficam a cargo do dicionário SQL."""

import re
import unicodedata

# Palavras de formulação da pergunta, não regras ou sinônimos tributários.
# Negações, valores, datas e os termos IBS/CBS são preservados.
FORMULACAO = frozenset(
    {
        "qual",
        "quais",
        "artigo",
        "artigos",
        "quando",
        "como",
        "onde",
        "pode",
        "podem",
        "são",
        "sao",
        "tem",
        "têm",
    }
)


def preparar(consulta):
    palavras = re.findall(
        r"[^\W_]+", unicodedata.normalize("NFC", consulta).casefold(), flags=re.UNICODE
    )
    return " ".join(p for p in palavras if p not in FORMULACAO)
