"""Prepara texto pesquisável sem tratar redações riscadas como texto corrente."""

from taxtrace.lei import ABRE_RISCADO, FECHA_RISCADO


def texto_ativo(texto: str) -> str:
    profundidade = 0
    partes = []
    for caractere in texto:
        if caractere == ABRE_RISCADO:
            profundidade += 1
        elif caractere == FECHA_RISCADO:
            if not profundidade:
                raise ValueError("marcacao_de_redacao_invalida")
            profundidade -= 1
        elif not profundidade:
            partes.append(caractere)
    if profundidade:
        raise ValueError("marcacao_de_redacao_invalida")
    return " ".join("".join(partes).split())
