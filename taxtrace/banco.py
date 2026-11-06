"""Grava a coleta (lei, tabelas da Receita e ligações) no Postgres.

Cada carga cria uma linha em ``coletas`` e prende tudo a ela, então várias versões da
base convivem e dá para responder "o que valia na coleta de tal dia". Carregar a mesma
coleta duas vezes é recusado, nunca duplica.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb

from taxtrace import lei, ligacao, tabelas
from taxtrace.conexao import conectar
from taxtrace.documentos import texto_ativo
from taxtrace.integridade import verificar
from taxtrace.tabelas import Tabelas

SCHEMA = Path(__file__).with_name("schema.sql")


class ColetaJaCarregada(Exception):
    pass


def criar_esquema(conn: psycopg.Connection) -> None:
    conn.execute(SCHEMA.read_text(encoding="utf-8"))


def linhas_artigos(artigos: list[lei.Artigo]) -> list[tuple]:
    return [(a.numero, a.texto, a.hierarquia, a.tem_trecho_riscado) for a in artigos]


def linhas_alteracoes(artigos: list[lei.Artigo]) -> list[tuple]:
    return [
        (a.numero, i, al.tipo, al.norma, al.ano, al.texto)
        for a in artigos
        for i, al in enumerate(a.alteracoes)
    ]


def linhas_classificacoes(t: Tabelas, ligacoes: list[ligacao.Ligacao]) -> list[tuple]:
    geral = {lig.codigo: lig.regra_geral for lig in ligacoes}
    return [
        (
            c.codigo,
            c.cst,
            t.situacoes.get(c.cst),
            c.descricao,
            c.descricao_tratamento,
            c.tipo_aliquota,
            c.nomenclatura,
            c.percentual_reducao_cbs,
            c.percentual_reducao_ibs_uf,
            c.percentual_reducao_ibs_mun,
            c.data_atualizacao,
            c.texto_curto,
            c.hierarquia_referencia,
            geral[c.codigo],
        )
        for c in t.classificacoes
    ]


def linhas_ligacoes(ligacoes: list[ligacao.Ligacao]) -> list[tuple]:
    return [(lig.codigo, n) for lig in ligacoes for n in lig.artigos]


def linhas_divergencias(t: Tabelas, ligacoes: list[ligacao.Ligacao]) -> list[tuple]:
    textos = list(t.divergencias)
    for lig in ligacoes:
        for n in lig.ausentes:
            textos.append(f"{lig.codigo}: cita o art. {n}, que não existe no texto da lei")
    return list(enumerate(textos))


def _com_coleta(coleta_id: int, linhas: list[tuple]) -> list[tuple]:
    return [(coleta_id, *linha) for linha in linhas]


def gravar(
    conn: psycopg.Connection,
    t: Tabelas,
    artigos: list[lei.Artigo],
    ligacoes: list[ligacao.Ligacao],
    *,
    manifesto: dict,
    manifesto_sha256: str,
) -> int:
    """Grava tudo numa transação e devolve o id da coleta."""
    v = t.versao
    with conn.transaction(), conn.cursor() as cur:
        cur.execute(
            "INSERT INTO coletas (coletado_em, data_consulta, versao_app, versao_base,"
            " descricao_base, data_base, ambiente,manifesto_sha256,fontes) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            " ON CONFLICT (coletado_em) DO NOTHING RETURNING id",
            (
                datetime.fromisoformat(v.coletado_em),
                v.data_consulta,
                v.app,
                v.base,
                v.descricao_base,
                v.data_base,
                v.ambiente,
                manifesto_sha256,
                Jsonb(manifesto["arquivos"]),
            ),
        )
        achado = cur.fetchone()
        if achado is None:
            raise ColetaJaCarregada(f"a coleta de {v.coletado_em} já está no banco")
        cid = achado[0]

        artigos_linhas = [(n, tx, Jsonb(h), r) for n, tx, h, r in linhas_artigos(artigos)]
        cur.executemany(
            "INSERT INTO artigos VALUES (%s,%s,%s,%s,%s)", _com_coleta(cid, artigos_linhas)
        )
        cur.executemany(
            "INSERT INTO alteracoes VALUES (%s,%s,%s,%s,%s,%s,%s)",
            _com_coleta(cid, linhas_alteracoes(artigos)),
        )
        cur.executemany(
            "INSERT INTO classificacoes VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            _com_coleta(cid, linhas_classificacoes(t, ligacoes)),
        )
        cur.executemany(
            "INSERT INTO ligacoes VALUES (%s,%s,%s)", _com_coleta(cid, linhas_ligacoes(ligacoes))
        )
        cur.executemany(
            "INSERT INTO ncm VALUES (%s,%s,%s)", _com_coleta(cid, sorted(t.ncm.items()))
        )
        cur.executemany(
            "INSERT INTO divergencias VALUES (%s,%s,%s)",
            _com_coleta(cid, linhas_divergencias(t, ligacoes)),
        )
        documentos = [(cid, a.numero, texto_ativo(a.texto)) for a in artigos]
        cur.executemany(
            "INSERT INTO documentos_busca(coleta_id,artigo_numero,texto_ativo) VALUES (%s,%s,%s)",
            [linha for linha in documentos if linha[2].strip()],
        )
    return cid


def carregar_pasta(conn: psycopg.Connection, pasta: Path) -> int:
    manifesto, checksum = verificar(pasta, exigir_lei=True)
    t = tabelas.carregar(pasta)
    artigos = lei.ler_artigos((pasta / "lc214_planalto.html").read_bytes())
    ligacoes = ligacao.ligar(t.classificacoes, artigos)
    return gravar(conn, t, artigos, ligacoes, manifesto=manifesto, manifesto_sha256=checksum)


def preparar_leitor(conn, senha):
    if not senha:
        raise ValueError("senha_do_leitor_ausente")
    conn.execute("""DO $$ BEGIN
      IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='taxtrace_reader') THEN
        CREATE ROLE taxtrace_reader NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
      END IF;
    END $$""")
    conn.execute(sql.SQL("ALTER ROLE taxtrace_reader LOGIN PASSWORD {}").format(sql.Literal(senha)))
    conn.execute("ALTER ROLE taxtrace_reader SET default_transaction_read_only=on")
    conn.execute("GRANT USAGE ON SCHEMA public TO taxtrace_reader")
    conn.execute("REVOKE ALL ON ALL TABLES IN SCHEMA public FROM taxtrace_reader")
    conn.execute(
        "GRANT SELECT ON coletas,artigos,alteracoes,classificacoes,ligacoes,ncm,"
        "divergencias,documentos_busca TO taxtrace_reader"
    )


def main(argv: list[str] | None = None) -> int:
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Carrega uma coleta verificada no Postgres local.")
    parser.add_argument("--pasta", type=Path)
    args = parser.parse_args(argv)
    try:
        with conectar(Path.cwd(), autocommit=True) as conn:
            senha = os.environ.get("TAXTRACE_READER_PASSWORD")
            if not senha:
                raise ValueError("senha_do_leitor_ausente")
            pasta = args.pasta or tabelas.pasta_mais_recente(Path("data/raw"))
            with conn.transaction():
                criar_esquema(conn)
                cid = carregar_pasta(conn, pasta)
                preparar_leitor(conn, senha)
                contagens = {
                    nome: conn.execute(
                        sql.SQL("SELECT count(*) FROM {} WHERE coleta_id=%s").format(
                            sql.Identifier(nome)
                        ),
                        (cid,),
                    ).fetchone()[0]
                    for nome in (
                        "artigos",
                        "alteracoes",
                        "classificacoes",
                        "ligacoes",
                        "ncm",
                        "divergencias",
                        "documentos_busca",
                    )
                }
        print(json.dumps({"status": "carregada", "coleta_id": cid, "contagens": contagens}))
        return 0
    except ColetaJaCarregada:
        print(json.dumps({"status": "coleta_ja_carregada"}))
        return 1
    except Exception as erro:
        # Não imprimir mensagens do driver: elas podem incluir a conexão configurada.
        print(json.dumps({"status": "nao_foi_possivel_carregar", "tipo": type(erro).__name__}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
