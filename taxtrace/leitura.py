"""Leitura complementar integral, vinculada à coleta e sem modificar a revisão."""

import hashlib
import re
from functools import lru_cache
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit

from psycopg.rows import dict_row

from taxtrace.consultas import fonte, metadados, selecionar_coleta
from taxtrace.fontes import ler_fonte_preservada
from taxtrace.lei import ABRE_RISCADO, FECHA_RISCADO, decodificar


def _fechar_segmento(partes, acumulado, profundidade):
    if acumulado:
        partes.append({"texto": "".join(acumulado), "riscado": profundidade > 0})
        acumulado.clear()


def paragrafos(texto):
    """Preserva linhas e marcações da coleta; não interpreta HTML da fonte."""
    resultado = []
    profundidade = 0
    for linha in texto.splitlines():
        partes = []
        acumulado = []

        for caractere in linha:
            if caractere == ABRE_RISCADO:
                _fechar_segmento(partes, acumulado, profundidade)
                profundidade += 1
            elif caractere == FECHA_RISCADO:
                _fechar_segmento(partes, acumulado, profundidade)
                if not profundidade:
                    raise ValueError("marcacao_de_redacao_invalida")
                profundidade -= 1
            else:
                acumulado.append(caractere)
        _fechar_segmento(partes, acumulado, profundidade)
        limpo = "".join(p["texto"] for p in partes).strip()
        if not limpo:
            continue
        tipo = "texto"
        if re.match(r"^Art\.\s*\d", limpo):
            tipo = "caput"
        elif re.match(r"^(?:§|Parágrafo único\.)", limpo):
            tipo = "paragrafo"
        elif re.match(r"^[IVXLCDM]+\s*[-–—]", limpo):
            tipo = "inciso"
        elif re.match(r"^[a-z]\)", limpo):
            tipo = "alinea"
        resultado.append({"tipo": tipo, "partes": partes})
    if profundidade:
        raise ValueError("marcacao_de_redacao_invalida")
    return resultado


class Ancora(HTMLParser):
    def __init__(self):
        super().__init__()
        self.nomes = set()

    def handle_starttag(self, _tag, attrs):
        self.nomes.update(v for k, v in attrs if k in {"name", "id"} and v)


@lru_cache(maxsize=4)
def ancoras_verificadas(raiz, sha256):
    for arquivo in sorted((Path(raiz) / "data/raw").glob("*/lc214_planalto.html")):
        conteudo = arquivo.read_bytes()
        if hashlib.sha256(conteudo).hexdigest() == sha256:
            parser = Ancora()
            parser.feed(decodificar(conteudo))
            return frozenset(parser.nomes)
    return frozenset()


def link_artigo(url, numero, ancoras=()):
    partes = urlsplit(url)
    if partes.scheme != "https" or partes.hostname not in {
        "www.planalto.gov.br",
        "planalto.gov.br",
    }:
        raise ValueError("fonte_oficial_incompativel")
    ancora = "art" + numero.replace("-", "").lower()
    # Alguns dispositivos do próprio Planalto não têm âncora: tenta localizar o texto.
    fragmento = ancora if ancora in ancoras else ":~:text=" + quote(f"Art. {numero}.", safe="")
    return urlunsplit((partes.scheme, partes.netloc, partes.path, partes.query, fragmento))


def numeros_da_consulta(relatorio):
    respostas = relatorio["estado"].get("respostas", {})
    consulta = respostas.get("consulta", {}) or {}
    numeros = {r["artigo_numero"] for r in consulta.get("resultados", [])}
    numeros.update(r["artigo_numero"] for r in consulta.get("artigos_referenciados", []))
    for documento in (respostas.get("artigo", {}), consulta):
        if documento and documento.get("status") == "artigo_recuperado":
            numeros.add(documento["numero"])
    return numeros


def ler_integral(conn, relatorio, numero, raiz):
    if not re.fullmatch(r"[1-9][0-9]{0,3}(?:-[A-Z]{1,2})?", numero):
        raise ValueError("artigo_integral_indisponivel")
    if numero not in numeros_da_consulta(relatorio):
        raise ValueError("artigo_integral_indisponivel")
    referencia = relatorio["estado"]["coleta"]
    with conn.transaction(), conn.cursor(row_factory=dict_row) as cur:
        coleta = selecionar_coleta(cur, referencia["id"])
        if coleta["manifesto_sha256"] != referencia["manifesto_sha256"]:
            raise ValueError("coleta_divergente")
        origem = fonte(coleta, "lc214_planalto")
        esperada = next(
            (
                f
                for f in relatorio["estado"]["respostas"]["base"]["fontes"]
                if f["nome"] == "lc214_planalto"
            ),
            None,
        )
        if origem != esperada:
            raise ValueError("fonte_da_leitura_divergente")
        cur.execute(
            "SELECT texto,hierarquia,tem_trecho_riscado FROM artigos "
            "WHERE coleta_id=%s AND numero=%s",
            (coleta["id"], numero),
        )
        registro = cur.fetchone()
        conteudo_fonte = ler_fonte_preservada(cur, coleta["id"], "lc214_planalto", origem["sha256"])
    if not registro:
        raise ValueError("artigo_integral_indisponivel")
    texto = registro["texto"]
    if len(texto) > 200000:
        raise ValueError("artigo_integral_excede_limite")
    if conteudo_fonte is not None:
        parser = Ancora()
        parser.feed(decodificar(conteudo_fonte))
        ancoras = frozenset(parser.nomes)
    else:
        ancoras = ancoras_verificadas(str(raiz), origem["sha256"])
    url = link_artigo(origem["url"], numero, ancoras)
    return {
        "status": "artigo_integral_da_coleta",
        "numero": numero,
        "coleta": metadados(coleta),
        "texto": texto,
        "paragrafos": paragrafos(texto),
        "texto_sha256": hashlib.sha256(texto.encode()).hexdigest(),
        "total_caracteres": len(texto),
        "hierarquia": registro["hierarquia"],
        "tem_trecho_riscado": registro["tem_trecho_riscado"],
        "citacao": {**origem, "url": url, "norma": "LC 214/2025", "artigo": numero},
        "localizacao_oficial": "ancora_verificada_na_coleta"
        if "art" + numero.replace("-", "").lower() in ancoras
        else "busca_por_fragmento_de_texto",
        "escopo": "leitura_complementar_nao_altera_dossie_da_revisao",
        "dossie_sha256": relatorio["pacote_revisao"]["dossie_sha256"],
    }
