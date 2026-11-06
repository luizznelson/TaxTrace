"""Confere bytes e caminhos antes de usar uma coleta preservada."""

import hashlib
import json
from pathlib import Path

API = {
    "versao": "versao.json",
    "situacoes_cbs_ibs": "situacoes_cbs_ibs.json",
    "classificacoes_cbs_ibs": "classificacoes_cbs_ibs.json",
    "fundamentacoes_legais": "fundamentacoes_legais.json",
    "ncm_vigentes": "ncm_vigentes.json",
}


def verificar(pasta: Path, *, exigir_lei=False) -> tuple[dict, str]:
    pasta = pasta.resolve()
    bruto = (pasta / "manifesto.json").read_bytes()
    manifesto = json.loads(bruto)
    if manifesto["erros"]:
        nomes = ", ".join(item["nome"] for item in manifesto["erros"])
        raise ValueError(f"coleta incompleta, fontes não verificadas: {nomes}")
    esperados = {**API, "lc214_planalto": "lc214_planalto.html"}
    vistos = set()
    for item in manifesto["arquivos"]:
        nome = item["nome"]
        if nome not in esperados or nome in vistos or item["arquivo"] != esperados[nome]:
            raise ValueError("arquivo_de_coleta_invalido")
        caminho = pasta / item["arquivo"]
        if caminho.is_symlink() or caminho.resolve().parent != pasta:
            raise ValueError("arquivo_fora_da_coleta")
        corpo = caminho.read_bytes()
        if len(corpo) != item["bytes"] or hashlib.sha256(corpo).hexdigest() != item["sha256"]:
            raise ValueError("integridade_da_coleta_divergente")
        vistos.add(nome)
    obrigatorios = set(API) | ({"lc214_planalto"} if exigir_lei else set())
    if not obrigatorios.issubset(vistos):
        raise ValueError("manifesto_sem_fontes_obrigatorias")
    return manifesto, hashlib.sha256(bruto).hexdigest()
