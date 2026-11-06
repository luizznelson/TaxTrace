"""Busca textual em português, com referência e versão; ainda não é RAG vetorial."""

import argparse
import json
import re
from pathlib import Path

from psycopg.rows import dict_row

from taxtrace.conexao import conectar
from taxtrace.consulta import preparar


def pesquisar(conn, consulta: str, *, coleta_id=None, limite=5, metodo="v1") -> dict:
    if not isinstance(consulta, str) or not 3 <= len(consulta.strip()) <= 500:
        raise ValueError("consulta_deve_ter_3_a_500_caracteres")
    if type(limite) is not int or not 1 <= limite <= 20:
        raise ValueError("limite_deve_ser_1_a_20")
    if coleta_id is not None and (type(coleta_id) is not int or coleta_id < 1):
        raise ValueError("coleta_invalida")
    if metodo not in {"v1", "v2"}:
        raise ValueError("metodo_invalido")
    with conn.transaction(), conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT has_table_privilege(current_user,'coletas','INSERT') AS escreve")
        if cur.fetchone()["escreve"]:
            raise ValueError("busca_exige_papel_sem_escrita")
        cur.execute("SET LOCAL statement_timeout = '5s'")
        cur.execute(
            "SELECT id,coletado_em,data_consulta,versao_base,data_base,manifesto_sha256,fontes "
            "FROM coletas WHERE (%s::bigint IS NULL OR id=%s) "
            "ORDER BY coletado_em DESC,id DESC LIMIT 1",
            (coleta_id, coleta_id),
        )
        coleta = cur.fetchone()
        if not coleta or not coleta["manifesto_sha256"] or not coleta["fontes"]:
            raise ValueError("coleta_verificada_nao_encontrada")
        if metodo == "v1":
            cur.execute(
                "SELECT d.artigo_numero,d.texto_ativo,a.tem_trecho_riscado, "
                "ts_rank_cd(d.termos,plainto_tsquery('portuguese',%s)) AS pontuacao "
                "FROM documentos_busca d JOIN artigos a ON a.coleta_id=d.coleta_id "
                "AND a.numero=d.artigo_numero WHERE d.coleta_id=%s "
                "AND d.termos @@ plainto_tsquery('portuguese',%s) "
                "ORDER BY pontuacao DESC,d.artigo_numero LIMIT %s",
                (consulta, coleta["id"], consulta, limite),
            )
            resultados = cur.fetchall()
        else:
            resultados = buscar_v2(cur, preparar(consulta), coleta["id"], limite)
        fonte = next(f for f in coleta["fontes"] if f["nome"] == "lc214_planalto")
        for item in resultados:
            # Extrato literal em torno da primeira palavra encontrada, não prosa de LLM.
            texto = item.pop("texto_ativo")
            palavras = [p for p in re.findall(r"\w+", consulta) if len(p) > 3]
            posicoes = [texto.casefold().find(p.casefold()) for p in palavras]
            inicio = max(0, min((p for p in posicoes if p >= 0), default=0) - 100)
            item["trecho"] = texto[inicio : inicio + 1000]
            item["citacao"] = {
                "norma": "LC 214/2025",
                "artigo": item["artigo_numero"],
                "url": fonte["url"],
                "fonte_sha256": fonte["sha256"],
            }
    coleta.pop("fontes")
    return {
        "metodo": f"busca_textual_portugues_{metodo}",
        "consulta": consulta,
        "status": "encontrado" if resultados else "sem_evidencia_na_busca_textual",
        "coleta": coleta,
        "resultados": resultados,
        "limites": [
            "Ranking textual não é confiança nem parecer tributário.",
            "A busca v2 pode retornar correspondências parciais; confira os termos ausentes.",
            "Data consultada na API é distinta da data de coleta.",
            "Remover texto riscado não comprova vigência jurídica integral.",
            "Nenhum resultado nesta busca não significa ausência na legislação.",
        ],
    }


def buscar_v2(cur, consulta, coleta_id, limite):
    # Todas as partes da entrada são parâmetros. quote_literal protege a sintaxe tsquery.
    # Cobertura é contagem lexical, não probabilidade de resposta correta.
    cur.execute(
        """WITH lex AS (
          SELECT t FROM unnest(tsvector_to_array(
            to_tsvector('public.taxtrace_portugues_v2', %s))) t
        ), q AS (
          SELECT array_agg(t) AS termos, string_agg(quote_literal(t), ' | ')::tsquery AS busca
          FROM lex
        ), candidatos AS (
          SELECT d.artigo_numero,d.texto_ativo,a.tem_trecho_riscado,
                 ts_rank_cd(d.termos_v2,q.busca,2) AS pontuacao,
                 ARRAY(SELECT t FROM unnest(q.termos) t
                       WHERE NOT t=ANY(tsvector_to_array(d.termos_v2))) AS termos_ausentes,
                 cardinality(q.termos) AS total_termos
          FROM documentos_busca d JOIN artigos a
            ON a.coleta_id=d.coleta_id AND a.numero=d.artigo_numero CROSS JOIN q
          WHERE d.coleta_id=%s AND d.termos_v2 @@ q.busca
        )
        SELECT artigo_numero,texto_ativo,tem_trecho_riscado,pontuacao,termos_ausentes,
               cardinality(termos_ausentes)>0 AS correspondencia_parcial
        FROM candidatos
        WHERE cardinality(termos_ausentes)::float / total_termos <= 0.4
        ORDER BY cardinality(termos_ausentes),pontuacao DESC,artigo_numero LIMIT %s""",
        (consulta, coleta_id, limite),
    )
    return cur.fetchall()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--consulta", required=True)
    parser.add_argument("--metodo", choices=["v1", "v2"], default="v1")
    parser.add_argument("--coleta", type=int)
    parser.add_argument("--limite", type=int, default=5)
    args = parser.parse_args()
    try:
        with conectar(Path.cwd(), leitura=True, autocommit=True) as conn:
            resultado = pesquisar(
                conn, args.consulta, coleta_id=args.coleta, limite=args.limite, metodo=args.metodo
            )
        print(json.dumps(resultado, ensure_ascii=False, default=str, indent=2))
        return 0
    except Exception as erro:
        print(json.dumps({"status": "nao_foi_possivel_consultar", "tipo": type(erro).__name__}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
