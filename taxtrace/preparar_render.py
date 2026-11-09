"""Gera .env.render privado, por lista permitida e sem acesso administrativo."""

import json
from pathlib import Path

from dotenv import dotenv_values
from psycopg.conninfo import conninfo_to_dict

from taxtrace.autenticacao import validar_credencial
from taxtrace.remoto import opcoes_neon

CAMPOS_NEON = (
    "TAXTRACE_DATABASE_MODE",
    "TAXTRACE_CHECKPOINT_BACKEND",
    "TAXTRACE_NEON_HOST",
    "TAXTRACE_NEON_DATABASE",
    "TAXTRACE_READER_DATABASE_URL",
    "TAXTRACE_CHECKPOINT_DATABASE_URL",
)


def valores(raiz):
    runtime = dotenv_values(raiz / ".env.neon.runtime")
    dados = {key: runtime.get(key) for key in CAMPOS_NEON}
    if (
        dados["TAXTRACE_DATABASE_MODE"] != "neon"
        or dados["TAXTRACE_CHECKPOINT_BACKEND"] != "postgres"
    ):
        raise ValueError("runtime_remoto_nao_preparado")
    for chave, papel in (
        ("TAXTRACE_READER_DATABASE_URL", "taxtrace_reader"),
        ("TAXTRACE_CHECKPOINT_DATABASE_URL", "taxtrace_state"),
    ):
        opcoes_neon(conninfo_to_dict(dados[chave]), papel, ambiente=dados)
    local = dotenv_values(raiz / ".env")
    for chave in ("GEMINI_API_KEY", "GEMINI_MODEL", "GEMINI_RAG_MODEL"):
        if local.get(chave):
            dados[chave] = local[chave]
    credencial = local.get("TAXTRACE_REVIEWER_CREDENTIAL_JSON")
    arquivo = raiz / "data/checkpoints/revisor.json"
    if credencial:
        conta = validar_credencial(json.loads(credencial))
    elif arquivo.is_file():
        conta = validar_credencial(json.loads(arquivo.read_text(encoding="utf-8")))
    else:
        conta = None
    if conta:
        dados["TAXTRACE_REVIEWER_CREDENTIAL_JSON"] = json.dumps(
            conta, ensure_ascii=False, separators=(",", ":")
        )
    # Ativação do uso público do modelo é explícita após o primeiro smoke hospedado.
    dados["TAXTRACE_PUBLIC_AI_ENABLED"] = "false"
    if any(
        not isinstance(value, str) or not value or any(c in value for c in "\r\n\0")
        for value in dados.values()
    ):
        raise ValueError("valor_de_publicacao_invalido")
    return dados


def preparar(raiz):
    dados = valores(raiz)
    destino = raiz / ".env.render"
    with destino.open("x", encoding="utf-8", newline="\n") as arquivo:
        for key, value in dados.items():
            arquivo.write(f"{key}={value}\n")
    return {
        "status": "arquivo_privado_render_criado",
        "arquivo": ".env.render",
        "credencial_de_revisor_incluida": "TAXTRACE_REVIEWER_CREDENTIAL_JSON" in dados,
        "chave_de_modelo_incluida": "GEMINI_API_KEY" in dados,
        "ia_publica_habilitada": False,
        "deploy_realizado": False,
    }


def main():
    try:
        resultado = preparar(Path(__file__).resolve().parent.parent)
    except FileExistsError:
        print(json.dumps({"status": "arquivo_privado_existente_preservado"}))
        return 1
    except Exception:
        print(json.dumps({"status": "preparacao_recusada_confira_configuracao_privada"}))
        return 1
    print(json.dumps(resultado, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
