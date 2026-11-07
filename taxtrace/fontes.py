"""Preserva os bytes das fontes verificadas, sem servir HTML bruto ao navegador."""

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path

from psycopg.rows import tuple_row

from taxtrace.integridade import verificar

LIMITE = 16 * 1024 * 1024


def conferir_bytes(conteudo, tamanho, sha256):
    if len(conteudo) != tamanho or hashlib.sha256(conteudo).hexdigest() != sha256:
        raise ValueError("fonte_preservada_divergente")
    return conteudo


def descompactar(blob, tamanho, sha256):
    if type(tamanho) is not int or not 0 <= tamanho <= LIMITE or len(blob) > 2 * LIMITE:
        raise ValueError("fonte_preservada_excede_limite")
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(bytes(blob))) as arquivo:
            conteudo = arquivo.read(LIMITE + 1)
    except OSError, EOFError:
        raise ValueError("fonte_preservada_corrompida") from None
    if len(conteudo) > LIMITE:
        raise ValueError("fonte_preservada_excede_limite")
    return conferir_bytes(conteudo, tamanho, sha256)


def ler_fonte_preservada(cur, coleta_id, nome, sha256):
    # Compatibilidade com bancos locais antigos; não cria schema durante leitura.
    cur.execute("SELECT to_regclass('public.fontes_preservadas') AS tabela")
    if not cur.fetchone()["tabela"]:
        return None
    cur.execute(
        "SELECT sha256,bytes_originais,conteudo_gzip FROM public.fontes_preservadas "
        "WHERE coleta_id=%s AND nome=%s",
        (coleta_id, nome),
    )
    registro = cur.fetchone()
    if registro is None:
        return None
    if registro["sha256"] != sha256:
        raise ValueError("fonte_preservada_divergente")
    return descompactar(registro["conteudo_gzip"], registro["bytes_originais"], sha256)


def preservar(conn, coleta_id, pasta):
    if type(coleta_id) is not int or coleta_id < 1:
        raise ValueError("coleta_invalida")
    manifesto, checksum = verificar(Path(pasta), exigir_lei=True)
    arquivos = []
    for fonte in manifesto["arquivos"]:
        if not 0 <= fonte["bytes"] <= LIMITE:
            raise ValueError("fonte_preservada_excede_limite")
        conteudo = conferir_bytes(
            (Path(pasta) / fonte["arquivo"]).read_bytes(), fonte["bytes"], fonte["sha256"]
        )
        arquivos.append((fonte, conteudo))
    manifesto_bruto = (Path(pasta) / "manifesto.json").read_bytes()
    if len(manifesto_bruto) > LIMITE or hashlib.sha256(manifesto_bruto).hexdigest() != checksum:
        raise ValueError("manifesto_da_fonte_divergente")
    arquivos.append(
        (
            {
                "nome": "manifesto",
                "sha256": checksum,
                "bytes": len(manifesto_bruto),
            },
            manifesto_bruto,
        )
    )
    with conn.transaction(), conn.cursor(row_factory=tuple_row) as cur:
        cur.execute("SELECT manifesto_sha256 FROM coletas WHERE id=%s", (coleta_id,))
        row = cur.fetchone()
        if row is None or row[0] != checksum:
            raise ValueError("coleta_da_fonte_divergente")
        for fonte, conteudo in arquivos:
            cur.execute(
                "INSERT INTO public.fontes_preservadas "
                "(coleta_id,nome,sha256,bytes_originais,conteudo_gzip) VALUES (%s,%s,%s,%s,%s) "
                "ON CONFLICT (coleta_id,nome) DO NOTHING",
                (
                    coleta_id,
                    fonte["nome"],
                    fonte["sha256"],
                    len(conteudo),
                    gzip.compress(conteudo, mtime=0),
                ),
            )
            cur.execute(
                "SELECT sha256,bytes_originais,conteudo_gzip FROM public.fontes_preservadas "
                "WHERE coleta_id=%s AND nome=%s",
                (coleta_id, fonte["nome"]),
            )
            registrado = cur.fetchone()
            if registrado[0] != fonte["sha256"]:
                raise ValueError("fonte_preservada_divergente")
            descompactar(registrado[2], registrado[1], fonte["sha256"])
    return len(arquivos)


def main():
    from taxtrace.conexao import conectar

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coleta", type=int, required=True)
    parser.add_argument("--pasta", type=Path, required=True)
    args = parser.parse_args()
    try:
        with conectar(Path.cwd()) as conn:
            total = preservar(conn, args.coleta, args.pasta)
    except Exception:
        print(json.dumps({"status": "preservacao_nao_concluida"}))
        return 1
    print(json.dumps({"status": "fontes_preservadas", "arquivos": total}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
