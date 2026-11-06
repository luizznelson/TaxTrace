"""Demonstra pausa e retomada entre processos; decisões explicitamente automatizadas."""

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4


def verificar(raiz):
    chamadas = []

    def executar(args, *, falha=False):
        processo = subprocess.run(
            [sys.executable, "-m", "taxtrace.revisao", *args],
            cwd=raiz,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=45,
        )
        assert processo.returncode == (1 if falha else 0), "codigo_de_saida_inesperado"
        resposta = json.loads(processo.stdout)
        chamadas.append(
            {"argumentos": args, "codigo_saida": processo.returncode, "resultado": resposta}
        )
        return resposta

    def evento(resposta):
        caminho = (raiz / resposta["registro"] / "evento.json").resolve()
        assert caminho.is_relative_to((raiz / "runs").resolve())
        return json.loads(caminho.read_text(encoding="utf-8"))

    def argumentos_decisao(resposta, decisao, *, checksum=None):
        return [
            "decidir",
            "--revisao",
            resposta["revisao_id"],
            "--decisao",
            decisao,
            "--revisor",
            "Revisor automatizado",
            "--motivo",
            "Teste entre processos, sem parecer fiscal.",
            "--origem",
            "teste_automatizado",
            "--dossie-sha256",
            checksum or resposta["dossie_sha256"],
        ]

    inicio = executar(["iniciar", "--consulta", "Leia o artigo 125."])
    assert inicio["status"] == "aguardando_revisao"
    antes = evento(inicio)
    leitura = executar(["inspecionar", "--revisao", inicio["revisao_id"]])
    assert leitura["dossie_sha256"] == inicio["dossie_sha256"]
    erro = executar(argumentos_decisao(inicio, "aprovar", checksum="f" * 64), falha=True)
    assert erro["codigo"] == "dossie_da_decisao_divergente"
    aprovado = executar(argumentos_decisao(leitura, "aprovar"))
    assert aprovado["status"] == "revisao_documental_aprovada"
    depois = evento(aprovado)
    chamadas_antes = [e for e in antes["estado"]["rastro"] if "argumentos" in e]
    chamadas_depois = [e for e in depois["estado"]["rastro"] if "argumentos" in e]
    assert chamadas_antes == chamadas_depois
    assert not depois["estado"]["resultado"]["aprovacao_humana_realizada"]
    assert not depois["estado"]["resultado"]["resposta_fiscal_gerada"]
    erro = executar(argumentos_decisao(inicio, "rejeitar"), falha=True)
    assert erro["codigo"] == "revisao_nao_pendente"
    confirmado = executar(["inspecionar", "--revisao", inicio["revisao_id"]])
    assert confirmado["status"] == "revisao_documental_aprovada"
    print("Pausa, hash incorreto e retomada de aprovação sintética verificados.", flush=True)

    rejeicao = executar(["iniciar", "--consulta", "cesta basica"])
    assert rejeicao["status"] == "aguardando_revisao"
    rejeitado = executar(argumentos_decisao(rejeicao, "rejeitar"))
    assert rejeitado["status"] == "revisao_documental_rejeitada"
    recusado = evento(rejeitado)
    assert recusado["estado"]["revisao"]["origem"] == "teste_automatizado"
    assert not recusado["estado"]["resultado"]["aprovacao_humana_realizada"]
    ausente = executar(["iniciar", "--consulta", "Consulte o codigo 999999."])
    assert ausente["status"] == "referencia_nao_encontrada_nesta_consulta"

    relatorio = {
        "verificado_em": datetime.now(UTC).isoformat(),
        "natureza": "teste_automatizado_sem_revisao_humana_real",
        "chamadas_cli_em_processos_distintos": chamadas,
        "mesmas_chamadas_mcp_antes_e_depois_da_retomada": True,
        "hash_do_dossie_preservado": inicio["dossie_sha256"] == aprovado["dossie_sha256"],
        "decisao_duplicada_recusada": True,
        "hash_incorreto_recusado": True,
        "aprovacao_e_rejeicao_sinteticas_verificadas": True,
        "referencia_ausente_nao_vai_para_revisao": True,
        "limites": [
            "Checkpoint local sem autenticação de identidade do revisor.",
            "Não foram feitas chamadas Gemini neste teste de retomada.",
            "A decisão não gera resposta fiscal nem comprova vigência.",
        ],
    }
    pasta = raiz / "runs" / f"retomada-{uuid4()}"
    pasta.mkdir(parents=True, exist_ok=False)
    (pasta / "verificacao.json").write_text(
        json.dumps(relatorio, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return {
        "status": "retomada_verificada",
        "registro": str(pasta.relative_to(raiz)),
        "chamadas_cli": len(chamadas),
    }


def main():
    try:
        print(json.dumps(verificar(Path(__file__).resolve().parent.parent), ensure_ascii=False))
        return 0
    except Exception as erro:
        print(json.dumps({"status": "verificacao_nao_concluida", "tipo": type(erro).__name__}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
