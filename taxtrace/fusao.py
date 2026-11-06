"""Fusão por posição (RRF), sem comparar as escalas dos rankings textuais."""

CONSTANTE_RRF = 60
CANDIDATOS_POR_BUSCA = 20


def fundir(rankings, limite):
    if type(limite) is not int or not 1 <= limite <= 20:
        raise ValueError("limite_invalido")
    itens = {}
    for metodo, resultados in rankings.items():
        vistos = set()
        for posicao, original in enumerate(resultados, 1):
            numero = original["artigo_numero"]
            if numero in vistos:
                continue
            vistos.add(numero)
            if numero not in itens:
                itens[numero] = {
                    **original,
                    "pontuacao": 0.0,
                    "pontuacao_tipo": "rrf",
                    "origem": "fusao",
                    "posicoes": {},
                    "correspondencia_parcial": None,
                    "termos_ausentes": None,
                }
            item = itens[numero]
            item["pontuacao"] += 1 / (CONSTANTE_RRF + posicao)
            item["posicoes"][metodo] = posicao
            if metodo in {"v2", "textual"}:
                item["correspondencia_parcial"] = original.get("correspondencia_parcial")
                item["termos_ausentes"] = original.get("termos_ausentes")
    return sorted(itens.values(), key=lambda x: (-x["pontuacao"], x["artigo_numero"]))[:limite]


def completar(principal, ampliada, limite):
    """Preserva a ordem principal; só preenche vagas com candidatos não repetidos."""
    if type(limite) is not int or not 1 <= limite <= 20:
        raise ValueError("limite_invalido")
    vistos = set()
    saida = []
    for origem, ranking in (("v1", principal), ("v2", ampliada)):
        for original in ranking:
            numero = original["artigo_numero"]
            if numero in vistos:
                continue
            vistos.add(numero)
            item = {
                **original,
                "origem": origem,
                "pontuacao_tipo": f"ranking_textual_{origem}",
                "correspondencia_parcial": original.get("correspondencia_parcial"),
                "termos_ausentes": original.get("termos_ausentes"),
            }
            saida.append(item)
            if len(saida) == limite:
                return saida
    return saida
