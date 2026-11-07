"""Verifica uma imagem local sem banco, credenciais ou chamadas a modelos."""

import argparse
import json
import subprocess
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4


def docker(*args):
    return subprocess.run(
        ["docker", *args], check=True, capture_output=True, text=True, timeout=30
    ).stdout.strip()


def verificar(imagem):
    nome = "taxtrace-smoke-" + uuid4().hex[:12]
    iniciado = False
    verificacoes = []
    resultado = {
        "executado_em": datetime.now(UTC).isoformat(),
        "imagem": imagem,
        "natureza": "smoke_sem_banco_sem_modelo",
        "verificacoes": verificacoes,
        "aprovado": False,
    }
    try:
        docker(
            "run",
            "--detach",
            "--rm",
            "--name",
            nome,
            "--read-only",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=64m",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges:true",
            "-p",
            "127.0.0.1::8015",
            imagem,
        )
        iniciado = True
        porta = int(docker("port", nome, "8015/tcp").rsplit(":", 1)[1])
        base = f"http://127.0.0.1:{porta}"
        limite = time.monotonic() + 30
        while True:
            try:
                with urllib.request.urlopen(base + "/health/live", timeout=2) as response:
                    assert json.load(response) == {"status": "vivo"}
                break
            except OSError, ValueError:
                if time.monotonic() >= limite:
                    raise TimeoutError("aplicacao_nao_iniciou") from None
                time.sleep(0.5)
        verificacoes.append("processo_ativo")
        try:
            urllib.request.urlopen(base + "/health/ready", timeout=10).close()
            raise AssertionError("base_sem_configuracao_nao_deve_estar_pronta")
        except urllib.error.HTTPError as error:
            with error:
                assert error.code == 503
                assert json.load(error) == {"status": "base_indisponivel"}
        verificacoes.append("base_indisponivel_explicitamente_sem_conexao")
        with urllib.request.urlopen(base + "/", timeout=5) as response:
            assert "TaxTrace" in response.read().decode()
            assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]
        verificacoes.append("interface_com_cabecalhos_de_seguranca")
        with urllib.request.urlopen(base + "/api/contexto", timeout=5) as response:
            context = json.load(response)
            assert not context["gemini_disponivel"]
            assert context["acesso"] == {"configurado": False, "usuario": None}
        verificacoes.append("nenhuma_chave_ou_conta_embutida")
        docker(
            "exec",
            nome,
            "python",
            "-c",
            "import os; from pathlib import Path; assert os.getuid() == 10001; "
            "assert not Path('/app/.env').exists(); assert not Path('/app/.git').exists(); "
            "assert not list(Path('/app/data/checkpoints').iterdir()); "
            "assert not list(Path('/app/data/raw').iterdir()); "
            "assert not list(Path('/app/runs').iterdir())",
        )
        verificacoes.append("usuario_sem_root_e_imagem_sem_dados_privados")
        resultado["aprovado"] = True
    except Exception as erro:
        # Não registrar saída bruta do Docker ou conexões privadas em artefatos.
        resultado["tipo_de_falha"] = type(erro).__name__
    finally:
        if iniciado:
            try:
                docker("stop", "--time", "5", nome)
            except subprocess.SubprocessError, OSError:
                resultado["limpeza_do_container"] = "conferir_manualmente"
                resultado["container_de_teste"] = nome
                resultado["aprovado"] = False
    return resultado


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--imagem", default="taxtrace:ci")
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()
    if args.saida.exists():
        parser.error("O arquivo de evidência já existe; escolha outro caminho.")
    resultado = verificar(args.imagem)
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    with args.saida.open("x", encoding="utf-8") as arquivo:
        arquivo.write(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(resultado, ensure_ascii=False))
    return 0 if resultado["aprovado"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
