"""Confere captura oficial em banco isolado e desfaz todas as alterações."""

import json
from pathlib import Path

from taxtrace import banco, conexao, tabelas
from taxtrace.consultas import resumo_base
from taxtrace.leitura import ler_integral


def verificar():
    root = Path.cwd()
    path = tabelas.pasta_mais_recente(root / "data/raw")
    with conexao.conectar(root, teste=True) as conn:
        with conn.transaction(force_rollback=True):
            banco.criar_esquema(conn)
            banco.preparar_leitor(conn, "isolated-source-verification-only")
            cid = banco.carregar_pasta(conn, path)
            counts = conn.execute(
                "SELECT count(*),sum(bytes_originais),sum(octet_length(conteudo_gzip)) "
                "FROM fontes_preservadas WHERE coleta_id=%s",
                (cid,),
            ).fetchone()
            conn.execute("SET LOCAL ROLE taxtrace_reader")
            base = resumo_base(conn, cid)
            report = {
                "estado": {
                    "coleta": base["coleta"],
                    "respostas": {
                        "base": base,
                        "consulta": {"status": "artigo_recuperado", "numero": "125"},
                    },
                },
                "pacote_revisao": {"dossie_sha256": "0" * 64},
            }
            article = ler_integral(conn, report, "125", Path("/no-local-raw-files"))
            result = {
                "status": "captura_preservada_verificada",
                "pasta_da_captura": path.name,
                "versao_base": base["coleta"]["versao_base"],
                "contagens": base["contagens"],
                "arquivos_preservados": counts[0],
                "fontes_oficiais": len(base["fontes"]),
                "inclui_manifesto_original": True,
                "bytes_originais": int(counts[1]),
                "bytes_gzip": int(counts[2]),
                "leitura_sem_arquivos_locais": {
                    "artigo": "125",
                    "localizacao": article["localizacao_oficial"],
                    "url": article["citacao"]["url"],
                    "texto_sha256": article["texto_sha256"],
                },
                "alteracoes_desfeitas": True,
                "suficiencia_juridica": "nao_avaliada",
                "chamadas_de_modelo": 0,
            }
    return result


if __name__ == "__main__":
    try:
        result = verificar()
    except Exception:
        print(json.dumps({"status": "verificacao_nao_concluida"}))
        raise SystemExit(1) from None
    print(json.dumps(result, ensure_ascii=False, default=str))
