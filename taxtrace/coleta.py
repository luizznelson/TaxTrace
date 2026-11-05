"""Coleta das fontes oficiais do TaxTrace para ``data/raw``.

Uso (na sua máquina, com acesso à internet)::

    python -m taxtrace.coleta --data 2027-01-01

Cada coleta vira uma pasta ``data/raw/AAAA-MM-DD/`` com os arquivos originais, sem
alteração, e um ``manifesto.json`` com URL, status HTTP, tamanho, SHA-256 e a versão
da base da API. Fonte que não respondeu entra em ``erros``: nunca vira "sem resultado".
"""

import argparse
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

API = "https://piloto-cbs.tributos.gov.br/servico/calculadora-consumo/api"
DADOS_ABERTOS = f"{API}/calculadora/dados-abertos"
LEI_URL = "https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214.htm"
USER_AGENT = "Mozilla/5.0 (compatible; taxtrace/0.0.1; projeto de portfolio)"
CABECALHOS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9",
}

# nome do arquivo -> (caminho em dados-abertos, usa o parâmetro data?)
ENDPOINTS_API = {
    "versao": ("versao", False),
    "situacoes_cbs_ibs": ("situacoes-tributarias/cbs-ibs", True),
    "classificacoes_cbs_ibs": ("classificacoes-tributarias/cbs-ibs", True),
    "fundamentacoes_legais": ("fundamentacoes-legais", True),
    "ncm_vigentes": ("ncm/vigentes", True),
}

Abrir = Callable[..., object]


def baixar(
    url: str,
    *,
    abrir: Abrir = urllib.request.urlopen,
    tentativas: int = 3,
    espera: float = 2.0,
    timeout: float = 60.0,
) -> tuple[int, bytes]:
    """Baixa uma URL com novas tentativas para erro de rede e HTTP 5xx.

    Devolve ``(status, corpo)``. Erros 4xx não são repetidos e levantam ``HTTPError``.
    """
    ultimo: Exception | None = None
    for tentativa in range(1, tentativas + 1):
        pedido = urllib.request.Request(url, headers=CABECALHOS)
        try:
            with abrir(pedido, timeout=timeout) as resposta:
                return resposta.status, resposta.read()
        except urllib.error.HTTPError as erro:
            if erro.code < 500:
                raise
            ultimo = erro
        except (urllib.error.URLError, TimeoutError, ConnectionError) as erro:
            ultimo = erro
        if tentativa < tentativas:
            time.sleep(espera * tentativa)
    assert ultimo is not None
    raise ultimo


def coletar(
    destino: Path,
    data_consulta: str,
    *,
    abrir: Abrir = urllib.request.urlopen,
    agora: Callable[[], datetime] = lambda: datetime.now(UTC),
    espera: float = 2.0,
    lei_arquivo: Path | None = None,
) -> dict:
    """Baixa as fontes e grava os arquivos e o manifesto. Devolve o manifesto.

    Se o Planalto bloquear o download, ``lei_arquivo`` aceita o HTML da lei salvo pelo
    navegador; o manifesto registra que veio de arquivo local.
    """
    momento = agora()
    pasta = destino / momento.strftime("%Y-%m-%d")
    pasta.mkdir(parents=True, exist_ok=True)

    alvos = []
    for nome, (caminho, usa_data) in ENDPOINTS_API.items():
        url = f"{DADOS_ABERTOS}/{caminho}"
        if usa_data:
            url += f"?data={data_consulta}"
        alvos.append((nome, url, ".json"))
    alvos.append(("lc214_planalto", LEI_URL, ".html"))

    arquivos, erros, versao = [], [], None
    for nome, url, extensao in alvos:
        try:
            if nome == "lc214_planalto" and lei_arquivo is not None:
                status, corpo, origem = None, lei_arquivo.read_bytes(), "arquivo local"
            else:
                status, corpo = baixar(url, abrir=abrir, espera=espera)
                origem = "download"
            item = {
                "nome": nome,
                "url": url,
                "origem": origem,
                "http": status,
                "bytes": len(corpo),
                "sha256": hashlib.sha256(corpo).hexdigest(),
                "arquivo": f"{nome}{extensao}",
            }
            if extensao == ".json":
                dados = json.loads(corpo)
                if isinstance(dados, list):
                    item["itens"] = len(dados)
                if nome == "versao":
                    versao = dados
            (pasta / item["arquivo"]).write_bytes(corpo)
            arquivos.append(item)
        except (OSError, ValueError) as erro:
            erros.append({"nome": nome, "url": url, "erro": f"{type(erro).__name__}: {erro}"})

    manifesto = {
        "coletado_em": momento.isoformat(timespec="seconds"),
        "data_consulta": data_consulta,
        "versao_api": versao,
        "arquivos": arquivos,
        "erros": erros,
    }
    texto = json.dumps(manifesto, ensure_ascii=False, indent=2)
    (pasta / "manifesto.json").write_text(texto + "\n", encoding="utf-8")
    return manifesto


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Coleta as fontes oficiais do TaxTrace.")
    parser.add_argument(
        "--data",
        default=datetime.now(UTC).strftime("%Y-%m-%d"),
        help="data de vigência consultada na API (AAAA-MM-DD); padrão: hoje",
    )
    parser.add_argument("--destino", type=Path, default=Path("data/raw"))
    parser.add_argument(
        "--lei-arquivo",
        type=Path,
        help="HTML da LC 214 salvo pelo navegador, caso o download do Planalto seja bloqueado",
    )
    args = parser.parse_args(argv)

    manifesto = coletar(args.destino, args.data, lei_arquivo=args.lei_arquivo)
    for item in manifesto["arquivos"]:
        extra = f", {item['itens']} itens" if "itens" in item else ""
        print(f"ok   {item['nome']}: {item['bytes']} bytes{extra}")
    for erro in manifesto["erros"]:
        print(f"ERRO {erro['nome']}: {erro['erro']}", file=sys.stderr)
    if manifesto["erros"]:
        print("Coleta incompleta: as fontes com erro não foram verificadas.", file=sys.stderr)
        return 1
    versao = manifesto["versao_api"] or {}
    print(f"Base da API: {versao.get('versaoDb')} de {versao.get('dataVersaoDb')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
