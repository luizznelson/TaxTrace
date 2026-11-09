"""Entrada do serviço hospedado: um worker, origem fixa e sem proxy confiado."""

import os
from pathlib import Path

import uvicorn

from taxtrace.checkpoints import parametros
from taxtrace.conexao import opcoes
from taxtrace.publicacao import configuracao


def validar():
    cfg = configuracao()
    if not cfg.origem:
        raise ValueError("servidor_hospedado_exige_origem_publica")
    if os.environ.get("TAXTRACE_CHECKPOINT_BACKEND") != "postgres":
        raise ValueError("publicacao_exige_estado_postgres")
    if os.environ.get("TAXTRACE_DATABASE_MODE") != "neon":
        raise ValueError("publicacao_exige_destino_neon")
    if any(os.environ.get(k) for k in ("DATABASE_URL", "TAXTRACE_NEON_ADMIN_URL")):
        raise ValueError("credencial_de_manutencao_proibida_no_servico")
    raiz = Path(__file__).resolve().parent.parent
    opcoes(raiz, leitura=True)
    parametros(raiz)
    porta = os.environ.get("PORT", "10000")
    if not porta.isdigit() or not 1024 <= int(porta) <= 65535:
        raise ValueError("porta_do_servico_invalida")
    return int(porta)


def main():
    try:
        porta = validar()
    except Exception:
        # Nem o erro de parsing de uma conexão pode expor credenciais no log.
        raise SystemExit("Configuração de publicação recusada. Confira docs/RENDER.md.") from None
    uvicorn.run(
        "taxtrace.web:app",
        host="0.0.0.0",
        port=porta,
        workers=1,
        proxy_headers=False,
        access_log=False,
    )


if __name__ == "__main__":
    main()
