"""Testes adversariais reproduzíveis de saída RAG, sem chamadas ao modelo."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from pydantic import ValidationError

from taxtrace.rag import FalhaGeracao, checksum, validar_resposta


def avaliar(conjunto):
    resultados = []
    for caso in conjunto["casos"]:
        erro = None
        try:
            validar_resposta(caso["saida"], conjunto["avaliacao"])
        except FalhaGeracao as exc:
            erro = exc.codigo
        except ValidationError:
            erro = "schema_invalido"
        resultados.append(
            {
                "id": caso["id"],
                "aceita": erro is None,
                "erro": erro,
                "comportamento_estrutural_esperado": (erro is None) == caso["aceita_esperada"]
                and erro == caso["erro_esperado"],
                "exige_julgamento_semantico": caso.get("exige_julgamento_semantico", False),
            }
        )
    negativos = [
        r for c, r in zip(conjunto["casos"], resultados, strict=True) if not c["aceita_esperada"]
    ]
    return {
        "executado_em": datetime.now(UTC).isoformat(),
        "conjunto_sha256": checksum(conjunto),
        "natureza": conjunto["natureza"],
        "chamadas_de_modelo": 0,
        "resumo": {
            "casos": len(resultados),
            "bloqueios_esperados": len(negativos),
            "bloqueios_corretos": sum(r["comportamento_estrutural_esperado"] for r in negativos),
            "controles_semanticos_nao_cobertos": sum(
                r["exige_julgamento_semantico"] for r in resultados
            ),
        },
        "limites": conjunto["limites"],
        "casos": resultados,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--casos", type=Path)
    parser.add_argument("--saida", type=Path, help="Arquivo JSON novo; não sobrescreve evidências.")
    args = parser.parse_args(argv)
    raiz = Path(__file__).resolve().parent.parent
    caminho = args.casos or raiz / "evals/rag.adversarial.v2.json"
    r = avaliar(json.loads(caminho.read_text(encoding="utf-8")))
    r["codigo_sha256"] = checksum((raiz / "taxtrace/rag.py").read_text(encoding="utf-8"))
    if args.saida:
        destino = args.saida
    else:
        destino = raiz / "runs" / f"rag-adversarial-{uuid4()}" / "avaliacao.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("x", encoding="utf-8") as arquivo:
        arquivo.write(json.dumps(r, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"registro": str(destino), **r["resumo"]}, ensure_ascii=False))
    return 0 if all(c["comportamento_estrutural_esperado"] for c in r["casos"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
