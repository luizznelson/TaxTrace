"""Ensaio local do preparador em cluster descartável; nunca usa o Neon real."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import psycopg
from dotenv import dotenv_values

from taxtrace import conexao, neon
from taxtrace.consultas import resumo_base


def verificar():
    from sys import path

    path.insert(0, str(Path.cwd() / "tests"))
    from test_tabelas import atualizar_manifesto, montar

    params = conexao.opcoes(Path.cwd(), teste=True)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "taxtrace").symlink_to(Path.cwd() / "taxtrace", target_is_directory=True)
        (root / "requirements.txt").symlink_to(Path.cwd() / "requirements.txt")
        capture = root / "capture"
        capture.mkdir()
        montar(capture)
        (capture / "lc214_planalto.html").write_text(
            "<p>Art. 1. Texto de teste.</p><p>Art. 138. Crédito de teste.</p>", encoding="utf-8"
        )
        atualizar_manifesto(capture)
        profile = root / ".env.neon"
        profile.write_text(
            "TAXTRACE_NEON_ADMIN_URL=postgresql://owner:synthetic-admin@ep-taxtrace-test.us-east-2.aws.neon.tech/neondb?sslmode=require\nTAXTRACE_NEON_HOST=ep-taxtrace-test.us-east-2.aws.neon.tech\nTAXTRACE_NEON_DATABASE=neondb\nTAXTRACE_NEON_READER_PASSWORD=synthetic-reader-password\nTAXTRACE_NEON_STATE_PASSWORD=synthetic-state-password\n",
            encoding="utf-8",
        )
        inventory = {
            "identificacao": {"banco": "neondb", "papel": "owner", "somente_leitura": "on"},
            "tls_cliente": {"ativo": True},
            "tabelas": [],
            "papeis": [],
            "schema_workflow": [],
            "vector": {"default_version": "0.8.6", "installed_version": None},
        }

        def local_params(_cfg, *, leitura=True):
            return {
                **params,
                "options": "-c statement_timeout=30000 -c default_transaction_read_only="
                + ("on" if leitura else "off"),
            }

        with (
            patch.object(neon, "inventario", return_value=inventory),
            patch.object(neon, "parametros_admin", side_effect=local_params),
        ):
            plan = neon.plano(root, profile, capture)
            result = neon.aplicar(root, profile, capture, plan["plano_sha256"])
        runtime = dotenv_values(root / ".env.neon.runtime")
        assert "TAXTRACE_NEON_ADMIN_URL" not in runtime
        assert "synthetic-admin" not in (root / ".env.neon.runtime").read_text()
        with psycopg.connect(
            **{**params, "user": "taxtrace_reader", "password": "synthetic-reader-password"}
        ) as conn:
            base = resumo_base(conn, result["coleta_id"])
            assert base["contagens"]["artigos"] == 2
            assert conn.execute("SELECT count(*) FROM fontes_preservadas").fetchone()[0] == 7
            assert not conn.execute(
                "SELECT has_table_privilege(current_user,'coletas','INSERT')"
            ).fetchone()[0]
        state = {
            **params,
            "user": "taxtrace_state",
            "password": "synthetic-state-password",
            "options": "-c search_path=taxtrace_workflow,pg_catalog",
        }
        with psycopg.connect(**state) as conn:
            assert conn.execute(
                "SELECT has_table_privilege(current_user,'checkpoint_writes','INSERT')"
            ).fetchone()[0]
            assert not conn.execute(
                "SELECT has_table_privilege(current_user,'eventos_revisao','DELETE')"
            ).fetchone()[0]
        return {
            "status": "preparador_ensaiado_no_postgres_descartavel",
            "neon_real_utilizado": False,
            "papeis_criados_somente_no_cluster_de_teste": 2,
            "fontes_e_manifesto": 7,
            "artigos_sinteticos": 2,
            "credencial_administrativa_excluida_do_runtime": True,
            "permissoes_restritas_verificadas": True,
        }


if __name__ == "__main__":
    try:
        result = verificar()
    except Exception as error:
        print(json.dumps({"status": "ensaio_nao_concluido", "tipo": type(error).__name__}))
        raise SystemExit(1) from None
    print(json.dumps(result, ensure_ascii=False))
