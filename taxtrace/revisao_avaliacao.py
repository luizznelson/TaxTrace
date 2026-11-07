"""Pacotes para revisão declarada do RAG, sem simular revisão independente."""

import argparse
import copy
import json
from datetime import UTC, datetime
from pathlib import Path

from taxtrace.rag import checksum

CRITERIOS = (
    "coerencia_com_fontes",
    "condicionantes_preservadas",
    "citacoes_suficientes",
    "recusa_adequada",
    "limites_temporais_respeitados",
    "clareza",
)
NOTAS = {"pendente", "atende", "nao_atende", "nao_aplicavel"}


def _casos(execucao):
    casos = execucao.get("casos")
    if not isinstance(casos, list) or not casos:
        raise ValueError("execucao_sem_casos")
    if any(not isinstance(c, dict) for c in casos):
        raise ValueError("caso_invalido")
    ids = [c.get("id") for c in casos]
    if any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
        raise ValueError("ids_de_casos_invalidos")
    return casos


def _material(caso):
    if not isinstance(caso.get("pergunta"), str) or not isinstance(caso.get("estado"), dict):
        raise ValueError("material_invalido")
    return copy.deepcopy({"pergunta": caso["pergunta"], "rag": caso["estado"].get("rag", {})})


def exportar(execucao):
    casos = []
    for caso in _casos(execucao):
        material = _material(caso)
        casos.append(
            {
                "id": caso["id"],
                "material_sha256": checksum(material),
                "material": material,
                "notas": dict.fromkeys(CRITERIOS, "pendente"),
                "observacoes": "",
            }
        )
    return {
        "schema": 1,
        "exportado_em": datetime.now(UTC).isoformat(),
        "execucao_sha256": checksum(execucao),
        "revisor": None,
        "instrucoes": [
            "Leia a pergunta, a resposta ou recusa e os documentos de apoio.",
            "Preencha notas e observações sem modificar o material nem seus hashes.",
            "Não marque atende apenas porque a citação é literal; confira a interpretação.",
            "Identifique nome, qualificação declarada e origem. "
            "A ferramenta não verifica identidade ou independência.",
            "Não inclua dados pessoais desnecessários nem publique "
            "identificação de terceiros sem autorização.",
        ],
        "casos": casos,
    }


def conferir(pacote, execucao):
    if type(pacote.get("schema")) is not int or pacote["schema"] != 1:
        raise ValueError("schema_de_revisao_invalido")
    if pacote.get("execucao_sha256") != checksum(execucao):
        raise ValueError("pacote_de_outra_execucao")
    originais = {c["id"]: c for c in _casos(execucao)}
    casos = pacote.get("casos")
    if not isinstance(casos, list) or len(casos) != len(originais):
        raise ValueError("casos_da_revisao_divergentes")
    vistos = set()
    completos = 0
    reprovacoes = []
    iniciado = False
    for c in casos:
        if not isinstance(c, dict):
            raise ValueError("caso_invalido")
        id_ = c.get("id")
        if id_ not in originais or id_ in vistos:
            raise ValueError("caso_duplicado_ou_desconhecido")
        vistos.add(id_)
        material = _material(originais[id_])
        if c.get("material_sha256") != checksum(material) or c.get("material") != material:
            raise ValueError("material_da_revisao_alterado")
        notas = c.get("notas")
        if (
            not isinstance(notas, dict)
            or set(notas) != set(CRITERIOS)
            or any(type(n) is not str or n not in NOTAS for n in notas.values())
        ):
            raise ValueError("rubrica_invalida")
        observacoes = c.get("observacoes")
        if not isinstance(observacoes, str) or len(observacoes) > 3000:
            raise ValueError("observacoes_invalidas")
        iniciado |= any(n != "pendente" for n in notas.values())
        if "pendente" not in notas.values() and any(
            n in {"atende", "nao_atende"} for n in notas.values()
        ):
            completos += 1
        if "nao_atende" in notas.values():
            if len(observacoes.strip()) < 5:
                raise ValueError("reprovacao_exige_justificativa")
            reprovacoes.append(id_)
    revisor = pacote.get("revisor")
    if iniciado:
        if not isinstance(revisor, dict) or set(revisor) != {
            "nome",
            "qualificacao_declarada",
            "origem",
        }:
            raise ValueError("revisor_declarado_obrigatorio")
        if not isinstance(revisor["nome"], str) or not 3 <= len(revisor["nome"].strip()) <= 80:
            raise ValueError("nome_de_revisor_invalido")
        if (
            not isinstance(revisor["qualificacao_declarada"], str)
            or not 3 <= len(revisor["qualificacao_declarada"].strip()) <= 250
        ):
            raise ValueError("qualificacao_declarada_invalida")
        if revisor["origem"] not in {"pessoa_nao_verificada", "teste_automatizado"}:
            raise ValueError("origem_de_revisao_invalida")
    elif revisor is not None:
        raise ValueError("pacote_nao_iniciado_deve_ter_revisor_nulo")
    return {
        "execucao_sha256": pacote["execucao_sha256"],
        "pacote_sha256": checksum(pacote),
        "casos": len(casos),
        "casos_completos": completos,
        "casos_pendentes": len(casos) - completos,
        "casos_com_reprovacao": reprovacoes,
        "revisor": revisor,
        "identidade_verificada": False,
        "independencia_comprovada": False,
        "revisao_especializada_comprovada": False,
        "publicacao_autorizada_automaticamente": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("acao", choices=["exportar", "conferir"])
    parser.add_argument("--execucao", type=Path, required=True)
    parser.add_argument("--pacote", type=Path)
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        execucao = json.loads(args.execucao.read_text(encoding="utf-8"))
        if args.acao == "exportar":
            resultado = exportar(execucao)
        else:
            if args.pacote is None:
                raise ValueError("pacote_obrigatorio")
            resultado = conferir(json.loads(args.pacote.read_text(encoding="utf-8")), execucao)
        with args.saida.open("x", encoding="utf-8") as file:
            json.dump(resultado, file, ensure_ascii=False, indent=2)
            file.write("\n")
        print(json.dumps({"status": "arquivo_criado", "acao": args.acao, "saida": str(args.saida)}))
        return 0
    except ValueError, KeyError, TypeError, OSError:
        print(
            json.dumps(
                {
                    "status": "operacao_nao_concluida",
                    "motivo": "confira_execucao_pacote_e_saida_nova",
                }
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
