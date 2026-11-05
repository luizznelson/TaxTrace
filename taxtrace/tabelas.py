"""Carrega as tabelas da API da Receita gravadas pelo coletor em ``data/raw/AAAA-MM-DD/``.

Mantém junto de cada tabela a versão da base e a data da coleta, e lista as divergências
entre as próprias tabelas da fonte em vez de escondê-las.
"""

import json
import re
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path


@dataclass(frozen=True, slots=True)
class VersaoBase:
    app: str
    base: str
    descricao_base: str
    data_base: str
    ambiente: str
    coletado_em: str
    data_consulta: str


@dataclass(frozen=True, slots=True)
class Classificacao:
    """Um cClassTrib com seu fundamento legal."""

    codigo: str
    cst: str
    descricao: str
    descricao_tratamento: str
    tipo_aliquota: str
    nomenclatura: str
    percentual_reducao_cbs: Decimal
    percentual_reducao_ibs_uf: Decimal
    percentual_reducao_ibs_mun: Decimal
    data_atualizacao: str
    texto_curto: str
    hierarquia_referencia: str


@dataclass(frozen=True, slots=True)
class Tabelas:
    versao: VersaoBase
    situacoes: dict[str, str]
    classificacoes: tuple[Classificacao, ...]
    ncm: dict[str, str]
    divergencias: tuple[str, ...]


def _json(caminho: Path):
    return json.loads(caminho.read_text(encoding="utf-8"), parse_float=Decimal)


def _hierarquia(referencia: str) -> str:
    """A API traz a hierarquia com "\\n" literal; devolve as partes separadas por " > "."""
    partes = (p.strip() for p in re.split(r"(?:\\n)+|\n+", referencia))
    return " > ".join(p for p in partes if p)


def pasta_mais_recente(raiz: Path) -> Path:
    """Devolve a coleta mais recente (pasta AAAA-MM-DD com manifesto) em ``raiz``."""
    pastas = sorted(p for p in raiz.glob("????-??-??") if (p / "manifesto.json").exists())
    if not pastas:
        raise FileNotFoundError(f"nenhuma coleta com manifesto em {raiz}")
    return pastas[-1]


def carregar(pasta: Path) -> Tabelas:
    manifesto = _json(pasta / "manifesto.json")
    if manifesto["erros"]:
        nomes = ", ".join(e["nome"] for e in manifesto["erros"])
        raise ValueError(f"coleta incompleta, fontes não verificadas: {nomes}")

    v = _json(pasta / "versao.json")
    versao = VersaoBase(
        app=v["versaoApp"],
        base=v["versaoDb"],
        descricao_base=v["descricaoVersaoDb"],
        data_base=v["dataVersaoDb"],
        ambiente=v["ambiente"],
        coletado_em=manifesto["coletado_em"],
        data_consulta=manifesto["data_consulta"],
    )

    situacoes_brutas = _json(pasta / "situacoes_cbs_ibs.json")
    situacoes = {s["codigo"]: s["descricao"] for s in situacoes_brutas}
    nas_situacoes = {c["codigo"] for s in situacoes_brutas for c in s["classificacoesTributarias"]}
    fundamentos = {
        f["codigoClassificacaoTributaria"]: f for f in _json(pasta / "fundamentacoes_legais.json")
    }

    classificacoes = []
    for c in _json(pasta / "classificacoes_cbs_ibs.json"):
        f = fundamentos.get(c["codigo"], {})
        classificacoes.append(
            Classificacao(
                codigo=c["codigo"],
                cst=c["codigo"][:3],
                descricao=c["descricao"],
                descricao_tratamento=c["descricaoTratamentoTributario"],
                tipo_aliquota=c["tipoAliquota"],
                nomenclatura=c["nomenclatura"],
                percentual_reducao_cbs=Decimal(str(c["percentualReducaoCbs"])),
                percentual_reducao_ibs_uf=Decimal(str(c["percentualReducaoIbsUf"])),
                percentual_reducao_ibs_mun=Decimal(str(c["percentualReducaoIbsMun"])),
                data_atualizacao=c["dataAtualizacao"],
                texto_curto=f.get("textoCurto", "").strip(),
                hierarquia_referencia=_hierarquia(f.get("referenciaNormativa", "")),
            )
        )

    codigos = {c.codigo for c in classificacoes}
    divergencias = []
    for codigo in sorted(nas_situacoes - codigos):
        divergencias.append(f"{codigo}: listada em situações, ausente em classificações")
    for codigo in sorted(codigos - nas_situacoes):
        divergencias.append(f"{codigo}: listada em classificações, ausente em situações")
    for codigo in sorted(codigos - fundamentos.keys()):
        divergencias.append(f"{codigo}: sem fundamento legal")
    for codigo in sorted(fundamentos.keys() - codigos):
        divergencias.append(f"{codigo}: fundamento sem classificação")
    for c in classificacoes:
        if c.cst not in situacoes:
            divergencias.append(f"{c.codigo}: CST {c.cst} ausente da tabela de situações")

    ncm = {n["ncm"]: n["descricao"] for n in _json(pasta / "ncm_vigentes.json")}
    return Tabelas(versao, situacoes, tuple(classificacoes), ncm, tuple(divergencias))
