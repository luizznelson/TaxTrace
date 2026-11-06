"""Avaliação reproduzível da recuperação de artigos; não avalia aconselhamento fiscal."""

import argparse
import hashlib
import json
import platform
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from taxtrace.busca import pesquisar
from taxtrace.conexao import conectar


def carregar_casos(caminho):
    bruto = Path(caminho).read_bytes()
    conjunto = json.loads(bruto)
    if (
        type(conjunto.get("schema")) is not int
        or conjunto["schema"] != 1
        or not isinstance(conjunto.get("casos"), list)
        or not conjunto["casos"]
    ):
        raise ValueError("conjunto_invalido")
    for chave in ("manifesto_sha256", "fonte_sha256"):
        if not isinstance(conjunto.get(chave), str) or not re.fullmatch(
            r"[0-9a-f]{64}", conjunto[chave]
        ):
            raise ValueError("hash_de_referencia_invalido")
    if not isinstance(conjunto.get("fonte_url"), str) or not conjunto["fonte_url"].startswith(
        "https://"
    ):
        raise ValueError("fonte_invalida")
    if not isinstance(conjunto.get("limites"), list) or not all(
        isinstance(item, str) for item in conjunto["limites"]
    ):
        raise ValueError("limites_obrigatorios")
    ids = set()
    for caso in conjunto["casos"]:
        if not isinstance(caso, dict):
            raise ValueError("caso_invalido")
        if not isinstance(caso.get("id"), str) or not caso["id"] or caso["id"] in ids:
            raise ValueError("id_invalido_ou_duplicado")
        ids.add(caso["id"])
        if not isinstance(caso.get("categoria"), str) or not caso["categoria"]:
            raise ValueError("categoria_obrigatoria")
        if caso.get("tipo") not in {"artigo", "controle_sem_resultado"}:
            raise ValueError("tipo_invalido")
        if not isinstance(caso.get("consulta"), str) or not 3 <= len(caso["consulta"]) <= 500:
            raise ValueError("consulta_invalida")
        esperados = caso.get("esperados")
        if (
            not isinstance(esperados, list)
            or not all(isinstance(x, str) for x in esperados)
            or len(set(esperados)) != len(esperados)
        ):
            raise ValueError("gabarito_invalido")
        if caso["tipo"] == "artigo" and not esperados:
            raise ValueError("artigo_esperado_obrigatorio")
        if caso["tipo"] == "controle_sem_resultado" and esperados:
            raise ValueError("controle_nao_pode_exigir_artigo")
        for item in esperados:
            if (
                not isinstance(caso.get("evidencias"), dict)
                or not isinstance(caso["evidencias"].get(item), str)
                or not caso["evidencias"][item].strip()
            ):
                raise ValueError("evidencia_obrigatoria")
    return conjunto, hashlib.sha256(bruto).hexdigest()


def pontuar(esperados, encontrados):
    """Gabarito é um conjunto mínimo, não rotulagem exaustiva de relevância."""
    esperados = set(esperados)
    if not esperados:
        raise ValueError("pontuacao_exige_artigo_esperado")
    posicoes = [i for i, numero in enumerate(encontrados, 1) if numero in esperados]
    recuperados = esperados.intersection(encontrados)
    return {
        "acertou": bool(recuperados),
        "recall_referencias": len(recuperados) / len(esperados),
        "reciproco_primeiro_relevante": 1 / min(posicoes) if posicoes else 0.0,
    }


def pontuar_trechos(caso, resultados):
    referencias = {
        artigo: any(r["artigo_numero"] == artigo and ancora in r["trecho"] for r in resultados)
        for artigo in caso["esperados"]
        for ancora in [caso["evidencias"][artigo]]
    }
    return {
        "ancoras_literais_exibidas": referencias,
        "hit_ancora_no_trecho": any(referencias.values()),
        "suficiencia_para_resposta": "nao_avaliada",
    }


def verificar_trechos(conn, coleta_id, resultados):
    for resultado in resultados:
        origem = conn.execute(
            "SELECT texto_ativo FROM documentos_busca WHERE coleta_id=%s AND artigo_numero=%s",
            (coleta_id, resultado["artigo_numero"]),
        ).fetchone()
        trecho = resultado.get("trecho")
        if (
            not origem
            or not isinstance(trecho, str)
            or not trecho.strip()
            or trecho not in origem[0]
        ):
            raise ValueError("trecho_nao_confere_com_fonte")
        if resultado.get("tipo_trecho") == "fragmento_semantico":
            if origem[0][resultado["inicio"] : resultado["fim"]] != trecho:
                raise ValueError("offsets_do_trecho_divergentes")


def resumir(casos):
    artigos = [c for c in casos if c["tipo"] == "artigo"]
    controles = [c for c in casos if c["tipo"] == "controle_sem_resultado"]
    return {
        "casos": len(casos),
        "casos_com_artigo": len(artigos),
        "hit_at_k": sum(c["acertou"] for c in artigos) / len(artigos) if artigos else None,
        "recall_referencias_at_k": (
            sum(c["recall_referencias"] for c in artigos) / len(artigos) if artigos else None
        ),
        "mrr_at_k": (
            sum(c["reciproco_primeiro_relevante"] for c in artigos) / len(artigos)
            if artigos
            else None
        ),
        "hit_ancora_literal_at_k": (
            sum(c.get("hit_ancora_no_trecho", False) for c in artigos) / len(artigos)
            if artigos
            else None
        ),
        "controles_sem_resultado": len(controles),
        "controles_corretos": sum(not c["encontrados"] for c in controles),
    }


def avaliar(conn, conjunto, *, limite=5, metodo="v4"):
    if type(limite) is not int or not 1 <= limite <= 20:
        raise ValueError("limite_invalido")
    with conn.transaction():
        conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        postgres = conn.execute("SHOW server_version").fetchone()[0]
        coleta = pesquisar(conn, "referencia", limite=1, metodo=metodo)["coleta"]
        if coleta["manifesto_sha256"] != conjunto["manifesto_sha256"]:
            raise ValueError("gabarito_de_outra_coleta")
        # O gabarito é conferido no documento inteiro, independente do ranking.
        for caso in conjunto["casos"]:
            for artigo in caso["esperados"]:
                linha = conn.execute(
                    "SELECT texto_ativo FROM documentos_busca "
                    "WHERE coleta_id=%s AND artigo_numero=%s",
                    (coleta["id"], artigo),
                ).fetchone()
                if not linha or caso["evidencias"][artigo] not in linha[0]:
                    raise ValueError("evidencia_do_gabarito_nao_confere")
        saidas = []
        indice_semantico = None
        for caso in conjunto["casos"]:
            inicio = perf_counter()
            resposta = pesquisar(
                conn, caso["consulta"], coleta_id=coleta["id"], limite=limite, metodo=metodo
            )
            duracao = round((perf_counter() - inicio) * 1000, 3)
            resultados = resposta["resultados"]
            indice_semantico = resposta.get("indice_semantico")
            if any(
                r["citacao"]["fonte_sha256"] != conjunto["fonte_sha256"]
                or r["citacao"]["url"] != conjunto["fonte_url"]
                or r["citacao"]["artigo"] != r["artigo_numero"]
                for r in resultados
            ):
                raise ValueError("citacao_divergente")
            verificar_trechos(conn, coleta["id"], resultados)
            encontrados = [r["artigo_numero"] for r in resultados]
            saida = {
                **caso,
                "encontrados": encontrados,
                "status": resposta["status"],
                "duracao_ms": duracao,
                "correspondencias": [
                    {
                        "artigo": r["artigo_numero"],
                        "trecho": r["trecho"],
                        "trecho_sha256": hashlib.sha256(r["trecho"].encode()).hexdigest(),
                        "tipo_trecho": r.get("tipo_trecho", "recorte_textual"),
                        "inicio": r.get("inicio"),
                        "fim": r.get("fim"),
                        "posicoes": r.get("posicoes"),
                        "origem": r.get("origem"),
                        "parcial_v2": r.get("correspondencia_parcial"),
                        "termos_ausentes_v2": r.get("termos_ausentes"),
                    }
                    for r in resultados
                ],
            }
            if caso["esperados"]:
                saida.update(pontuar(caso["esperados"], encontrados))
                saida.update(pontuar_trechos(caso, resultados))
            saidas.append(saida)
    return {
        "coleta": coleta,
        "indice_semantico": indice_semantico,
        "k": limite,
        "resumo": resumir(saidas),
        "casos": saidas,
        "ambiente": {"postgres": postgres, "python": platform.python_version()},
        "por_categoria": {
            categoria: resumir([c for c in saidas if c["categoria"] == categoria])
            for categoria in sorted({c["categoria"] for c in saidas})
        },
    }


def versao_codigo(raiz):
    try:
        revisao = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=raiz, text=True, stderr=subprocess.DEVNULL
        ).strip()
        alterado = bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=raiz, stderr=subprocess.DEVNULL
            )
        )
        return {"commit": revisao, "alteracoes_locais": alterado}
    except OSError, subprocess.CalledProcessError:
        return {"commit": None, "alteracoes_locais": None}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--metodo", choices=["v1", "v2", "v3", "v4", "semantica", "hibrida"], default="v4"
    )
    parser.add_argument("--casos", type=Path, default=Path("evals/recuperacao.v1.json"))
    parser.add_argument("--limite", type=int, default=5)
    args = parser.parse_args(argv)
    raiz = Path.cwd()
    try:
        conjunto, checksum = carregar_casos(args.casos)
        with conectar(raiz, leitura=True, autocommit=True) as conn:
            relatorio = avaliar(conn, conjunto, limite=args.limite, metodo=args.metodo)
        relatorio.update(
            {
                "executado_em": datetime.now(UTC).isoformat(),
                "metodo": (
                    "busca_semantica_e5_v1"
                    if args.metodo == "semantica"
                    else "busca_hibrida_rrf_v1"
                    if args.metodo == "hibrida"
                    else f"busca_textual_portugues_{args.metodo}"
                ),
                "embeddings_codigo_sha256": {
                    nome: hashlib.sha256((Path(__file__).parent / nome).read_bytes()).hexdigest()
                    for nome in ("encoder.py", "vetores.py")
                },
                "conjunto_sha256": checksum,
                "codigo": versao_codigo(raiz),
                "avaliador_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "fusao_sha256": hashlib.sha256(
                    (Path(__file__).parent / "fusao.py").read_bytes()
                ).hexdigest(),
                "schema_sha256": hashlib.sha256(
                    (Path(__file__).parent / "schema.sql").read_bytes()
                ).hexdigest(),
                "consulta_sha256": hashlib.sha256(
                    (Path(__file__).parent / "consulta.py").read_bytes()
                ).hexdigest(),
                "busca_sha256": hashlib.sha256(
                    (Path(__file__).parent / "busca.py").read_bytes()
                ).hexdigest(),
                "limites": conjunto["limites"],
            }
        )
        destino = raiz / "runs" / f"recuperacao-{uuid4()}"
        destino.mkdir(parents=True, exist_ok=False)
        (destino / "resultado.json").write_text(
            json.dumps(relatorio, ensure_ascii=False, indent=2, default=str) + "\n",
            encoding="utf-8",
        )
        print(
            json.dumps(
                {
                    "status": "avaliado",
                    "registro": str(destino.relative_to(raiz)),
                    **relatorio["resumo"],
                },
                ensure_ascii=False,
            )
        )
        return 0
    except Exception as erro:
        # Falhas operacionais invalidam a execução; não viram resultado vazio ou acerto.
        print(json.dumps({"status": "avaliacao_nao_concluida", "tipo": type(erro).__name__}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
