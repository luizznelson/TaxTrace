"""Verificação operacional explícita do Neon; não executada pela suíte padrão.

Use --fase leitura para consultas sem escrita; iniciar e retomar criam uma
revisão técnica com rejeição automatizada, nunca uma aprovação humana.
O perfil privado deve ser carregado pelo operador, fora da imagem.
"""

import argparse
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from taxtrace.checkpoints import parametros
from taxtrace.conexao import conectar
from taxtrace.consultas import resumo_base
from taxtrace.fontes import ler_fonte_preservada
from taxtrace.leitura import ler_integral
from taxtrace.propriedade import criar_propriedade, dono
from taxtrace.revisao import decidir, iniciar, inspecionar


def leitura(raiz):
    with conectar(raiz, leitura=True) as conn:
        assert conn.pgconn.ssl_in_use
        base = resumo_base(conn)
        assert base["contagens"] == {
            "artigos": 580,
            "classificacoes": 170,
            "ligacoes": 169,
            "ncm": 10515,
            "divergencias": 3,
        }
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT nome,sha256,bytes_originais FROM fontes_preservadas WHERE coleta_id=%s",
                (base["coleta"]["id"],),
            )
            fontes = cur.fetchall()
            assert len(fontes) == 7
            for fonte in fontes:
                conteudo = ler_fonte_preservada(
                    cur, base["coleta"]["id"], fonte["nome"], fonte["sha256"]
                )
                assert len(conteudo) == fonte["bytes_originais"]
            cur.execute(
                "SELECT has_table_privilege(current_user,'coletas','INSERT') AS escreve, "
                "has_schema_privilege(current_user,'public','CREATE') AS cria"
            )
            assert not any(cur.fetchone().values())
        relatorio = {
            "estado": {
                "coleta": base["coleta"],
                "respostas": {
                    "base": base,
                    "consulta": {"status": "artigo_recuperado", "numero": "125"},
                },
            },
            "pacote_revisao": {"dossie_sha256": "0" * 64},
        }
        artigo = ler_integral(conn, relatorio, "125", Path("/inexistente-sem-fontes-locais"))
        assert artigo["citacao"]["url"].endswith("#art125")
    with psycopg.connect(**parametros(raiz)) as conn:
        assert conn.pgconn.ssl_in_use
        assert conn.execute(
            "SELECT has_table_privilege(current_user,'checkpoint_writes','INSERT')"
        ).fetchone()[0]
        for tabela, privilegio in [
            ("eventos_revisao", "DELETE"),
            ("acessos_revisao", "UPDATE"),
            ("acessos_revisao", "DELETE"),
            ("public.coletas", "INSERT"),
        ]:
            assert not conn.execute(
                "SELECT has_table_privilege(current_user,%s,%s)", (tabela, privilegio)
            ).fetchone()[0]
        assert not conn.execute(
            "SELECT has_schema_privilege(current_user,'taxtrace_workflow','CREATE')"
        ).fetchone()[0]
        assert conn.execute("SELECT count(*) FROM checkpoint_migrations").fetchone()[0] > 0
        assert not any(
            conn.execute(
                "SELECT rolsuper,rolcreaterole,rolcreatedb,rolbypassrls "
                "FROM pg_roles WHERE rolname=current_user"
            ).fetchone()
        )
    return {
        "status": "leitura_e_permissoes_verificadas",
        "contagens": base["contagens"],
        "fontes_e_manifesto_conferidos": 7,
        "tls_cliente_ativo_nos_dois_papeis": True,
        "artigo_sem_disco_local": artigo["citacao"]["url"],
        "texto_sha256": artigo["texto_sha256"],
    }


async def fluxo(raiz, fase, revisao_id):
    if fase == "iniciar":
        r = await iniciar("artigo 125", modo="local", raiz=raiz)
        assert r["pendente"] and r["codigo_compativel"]
        # Marcador público de teste, sem credencial real ou sessão de usuário.
        criar_propriedade(raiz).vincular(r["revisao_id"], dono("1" * 64))
        return {
            "status": r["status"],
            "revisao_id": r["revisao_id"],
            "dossie_sha256": r["pacote_revisao"]["dossie_sha256"],
            "origem": r["estado"]["origem_execucao"],
        }
    salvo = await inspecionar(revisao_id, raiz=raiz)
    assert salvo["pendente"] and salvo["codigo_compativel"]
    acessos = criar_propriedade(raiz)
    assert acessos.permite(revisao_id, dono("1" * 64))
    assert not acessos.permite(revisao_id, dono("2" * 64))
    final = await decidir(
        revisao_id,
        {
            "decisao": "rejeitar",
            "revisor": "Validação automatizada de infraestrutura",
            "motivo": (
                "Teste de persistência no Neon; não corresponde a parecer ou aprovação humana."
            ),
            "origem": "teste_automatizado",
            "dossie_sha256": salvo["pacote_revisao"]["dossie_sha256"],
        },
        raiz=raiz,
    )
    assert final["status"] == "revisao_documental_rejeitada"
    assert not final["estado"]["resultado"]["aprovacao_humana_realizada"]
    # A retomada acrescenta eventos de revisão; nenhuma ferramenta é disponível.
    conferido = await inspecionar(revisao_id, raiz=raiz)
    assert not conferido["pendente"]
    assert conferido["estado"]["revisao"]["origem"] == "teste_automatizado"
    return {
        "status": "retomada_em_outro_processo_verificada",
        "revisao_id": revisao_id,
        "decisao": final["status"],
        "aprovacao_humana_realizada": False,
        "autorizacao_de_sessao_persistida": True,
        "modelos_externos_utilizados": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fase", choices=["leitura", "iniciar", "retomar"], required=True)
    parser.add_argument("--revisao")
    args = parser.parse_args()
    if args.fase == "retomar" and not args.revisao:
        parser.error("--revisao é obrigatório para retomar")
    try:
        raiz = Path.cwd()
        resultado = (
            leitura(raiz)
            if args.fase == "leitura"
            else asyncio.run(fluxo(raiz, args.fase, args.revisao))
        )
    except Exception as erro:
        print(
            json.dumps(
                {
                    "status": "verificacao_nao_concluida",
                    "fase": args.fase,
                    "tipo": type(erro).__name__,
                }
            )
        )
        return 1
    print(
        json.dumps(
            {"registrado_em": datetime.now(UTC).isoformat(), **resultado}, ensure_ascii=False
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
