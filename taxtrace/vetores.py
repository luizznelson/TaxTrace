"""Índice semântico local e busca exata por cosseno com pgvector."""

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from psycopg.types.json import Jsonb

from taxtrace.conexao import conectar
from taxtrace.encoder import CONFIG, CONFIG_SHA256, encoder_local, preparar_modelo, vetor_sql


def corpus_sha256(linhas):
    return hashlib.sha256(json.dumps(linhas, ensure_ascii=False).encode()).hexdigest()


def validar_fragmentos(artigos, fragmentos):
    textos = dict(artigos)
    if not fragmentos or {f["artigo"] for f in fragmentos} != set(textos):
        raise ValueError("indice_incompleto")
    anteriores = {}
    for f in fragmentos:
        numero = f["artigo"]
        texto = textos[numero]
        ordem, fim_anterior = anteriores.get(numero, (-1, 0))
        if (
            f["ordem"] != ordem + 1
            or not 0 <= f["inicio"] < f["fim"] <= len(texto)
            or texto[f["inicio"] : f["fim"]] != f["texto"]
        ):
            raise ValueError("trecho_divergente_do_artigo")
        if texto[fim_anterior : f["inicio"]].strip():
            raise ValueError("cobertura_incompleta_do_artigo")
        vetor_sql(f["vetor"])
        anteriores[numero] = (f["ordem"], f["fim"])
    if any(textos[n][fim:].strip() for n, (_, fim) in anteriores.items()):
        raise ValueError("cobertura_incompleta_do_artigo")


def gravar_indice(conn, coleta_id, manifesto, artigos, fragmentos):
    validar_fragmentos(artigos, fragmentos)
    with conn.transaction():
        fonte = conn.execute(
            "SELECT manifesto_sha256 FROM coletas WHERE id=%s FOR UPDATE", (coleta_id,)
        ).fetchone()
        atuais = conn.execute(
            "SELECT artigo_numero,texto_ativo FROM documentos_busca "
            "WHERE coleta_id=%s ORDER BY artigo_numero FOR SHARE",
            (coleta_id,),
        ).fetchall()
        if not fonte or fonte[0] != manifesto or atuais != artigos:
            raise ValueError("coleta_alterada_durante_indexacao")
        indice_id = uuid4()
        conn.execute(
            "INSERT INTO indices_semanticos "
            "(id,coleta_id,config_sha256,config,corpus_sha256,artigos,fragmentos) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (
                indice_id,
                coleta_id,
                CONFIG_SHA256,
                Jsonb(CONFIG),
                corpus_sha256(artigos),
                len(artigos),
                len(fragmentos),
            ),
        )
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO fragmentos_semanticos "
                "(indice_id,coleta_id,artigo_numero,ordem,inicio,fim,texto,texto_sha256,vetor) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s::vector)",
                [
                    (
                        indice_id,
                        coleta_id,
                        f["artigo"],
                        f["ordem"],
                        f["inicio"],
                        f["fim"],
                        f["texto"],
                        hashlib.sha256(f["texto"].encode()).hexdigest(),
                        vetor_sql(f["vetor"]),
                    )
                    for f in fragmentos
                ],
            )
    return indice_id


def indexar(raiz):
    inicio = perf_counter()
    with conectar(raiz, leitura=True, autocommit=True) as conn:
        coleta = conn.execute(
            "SELECT id,manifesto_sha256 FROM coletas WHERE manifesto_sha256 IS NOT NULL "
            "ORDER BY coletado_em DESC,id DESC LIMIT 1"
        ).fetchone()
        if not coleta:
            raise ValueError("coleta_ausente")
        existente = conn.execute(
            "SELECT id FROM indices_semanticos WHERE coleta_id=%s AND config_sha256=%s",
            (coleta[0], CONFIG_SHA256),
        ).fetchone()
        if existente:
            return {"status": "indice_ja_existe", "indice_id": str(existente[0])}
        artigos = conn.execute(
            "SELECT artigo_numero,texto_ativo FROM documentos_busca "
            "WHERE coleta_id=%s ORDER BY artigo_numero",
            (coleta[0],),
        ).fetchall()
    modelo = encoder_local(Path(raiz))
    fragmentos = []
    for numero, texto in artigos:
        for ordem, frag in enumerate(modelo.fragmentar(texto)):
            fragmentos.append({**frag, "artigo": numero, "ordem": ordem})
    for offset in range(0, len(fragmentos), 8):
        lote = fragmentos[offset : offset + 8]
        vetores = modelo.gerar([f["texto"] for f in lote])
        for frag, vetor in zip(lote, vetores, strict=True):
            frag["vetor"] = vetor
        if offset % 400 == 0:
            print(
                f"Fragmentos vetorizados: {min(offset + 8, len(fragmentos))}/{len(fragmentos)}",
                flush=True,
            )
    with conectar(raiz, autocommit=True) as conn:
        indice_id = gravar_indice(conn, coleta[0], coleta[1], artigos, fragmentos)
    return {
        "status": "indexado",
        "indice_id": str(indice_id),
        "coleta_id": coleta[0],
        "manifesto_sha256": coleta[1],
        "config_sha256": CONFIG_SHA256,
        "config": CONFIG,
        "corpus_sha256": corpus_sha256(artigos),
        "artigos": len(artigos),
        "fragmentos": len(fragmentos),
        "duracao_segundos": round(perf_counter() - inicio, 3),
        "executado_em": datetime.now(UTC).isoformat(),
        "limites": [
            "Índice local; não há geração de resposta por IA.",
            "Busca semântica não tem limiar calibrado de recusa.",
        ],
    }


def buscar_semantica(cur, vetor, coleta_id, limite):
    cur.execute(
        "SELECT id,config_sha256,config,corpus_sha256,artigos,fragmentos "
        "FROM indices_semanticos WHERE coleta_id=%s AND config_sha256=%s",
        (coleta_id, CONFIG_SHA256),
    )
    indice = cur.fetchone()
    if not indice:
        raise ValueError("indice_semantico_ausente")
    indice["id"] = str(indice["id"])
    cur.execute(
        """WITH ordenados AS (
          SELECT f.artigo_numero,f.texto AS texto_ativo,a.tem_trecho_riscado,
                 f.inicio,f.fim,f.ordem,f.texto_sha256,
                 f.vetor <=> %s::vector AS distancia_cosseno,
                 row_number() OVER (PARTITION BY f.artigo_numero
                    ORDER BY f.vetor <=> %s::vector,f.ordem) AS posicao
          FROM fragmentos_semanticos f JOIN artigos a
            ON a.coleta_id=f.coleta_id AND a.numero=f.artigo_numero
          WHERE f.indice_id=%s AND f.coleta_id=%s
        ) SELECT artigo_numero,texto_ativo,tem_trecho_riscado,inicio,fim,ordem,texto_sha256,
                 1-distancia_cosseno AS pontuacao
          FROM ordenados WHERE posicao=1 ORDER BY distancia_cosseno,artigo_numero LIMIT %s""",
        (vetor_sql(vetor), vetor_sql(vetor), indice["id"], coleta_id, limite),
    )
    return cur.fetchall(), indice


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("acao", choices=["preparar-modelo", "indexar"])
    args = parser.parse_args(argv)
    try:
        raiz = Path.cwd()
        if args.acao == "preparar-modelo":
            preparar_modelo(raiz)
            print(json.dumps({"status": "modelo_preparado", "config_sha256": CONFIG_SHA256}))
        else:
            resultado = indexar(raiz)
            if resultado["status"] == "indexado":
                pasta = raiz / "runs" / f"embeddings-{uuid4()}"
                pasta.mkdir(parents=True, exist_ok=False)
                (pasta / "indice.json").write_text(
                    json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
                )
                resultado["registro"] = str(pasta.relative_to(raiz))
            print(json.dumps(resultado, ensure_ascii=False))
        return 0
    except Exception as erro:
        print(json.dumps({"status": "operacao_nao_concluida", "tipo": type(erro).__name__}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
