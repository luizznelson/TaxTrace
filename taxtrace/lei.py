"""Leitura do texto compilado da LC 214/2025 (HTML do Planalto), artigo por artigo.

O compilado do Planalto traz as alterações dentro do texto, em anotações como
"(Redação dada pela Lei Complementar nº 235, de 2026)". Este módulo preserva essas
anotações por artigo e marca trechos riscados (texto revogado) com ⟦ ⟧, para que a busca
nunca trate texto revogado como vigente.
"""

import re
import unicodedata
from dataclasses import dataclass, field
from html.parser import HTMLParser

ABRE_RISCADO = "⟦"
FECHA_RISCADO = "⟧"

_BLOCOS = {"p", "div", "br", "li", "tr", "table", "blockquote", "h1", "h2", "h3", "h4", "h5", "h6"}
_RISCADO = {"strike", "s", "del"}
_IGNORADOS = {"script", "style"}


class _Extrator(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.partes: list[str] = []
        self._ignorando = 0
        self._riscado = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _IGNORADOS:
            self._ignorando += 1
        elif tag in _BLOCOS:
            self.partes.append("\n")
        elif tag in _RISCADO:
            self._riscado += 1
            self.partes.append(ABRE_RISCADO)

    def handle_endtag(self, tag: str) -> None:
        if tag in _IGNORADOS:
            self._ignorando = max(0, self._ignorando - 1)
        elif tag in _BLOCOS:
            self.partes.append("\n")
        elif tag in _RISCADO and self._riscado:
            self._riscado -= 1
            self.partes.append(FECHA_RISCADO)

    def handle_data(self, data: str) -> None:
        if not self._ignorando:
            self.partes.append(data.replace("\n", " ").replace("\r", " "))


def decodificar(conteudo: bytes) -> str:
    """Decodifica o HTML: tenta UTF-8 e, se falhar, usa Windows-1252 (comum no Planalto)."""
    try:
        return conteudo.decode("utf-8")
    except UnicodeDecodeError:
        return conteudo.decode("cp1252", errors="replace")


def html_para_texto(html: str) -> str:
    """Converte o HTML em linhas de texto limpas, uma por parágrafo."""
    extrator = _Extrator()
    extrator.feed(html)
    extrator.close()
    bruto = "".join(extrator.partes).replace("\xa0", " ")
    linhas = (re.sub(r"[ \t]+", " ", linha).strip() for linha in bruto.split("\n"))
    return "\n".join(linha for linha in linhas if linha)


@dataclass(frozen=True, slots=True)
class Alteracao:
    """Uma anotação do compilado, por exemplo "Incluído pela Lei Complementar nº 227, de 2026"."""

    tipo: str
    norma: str | None
    ano: int | None
    texto: str


@dataclass(frozen=True, slots=True)
class Artigo:
    numero: str
    texto: str
    hierarquia: dict[str, str] = field(default_factory=dict)
    alteracoes: tuple[Alteracao, ...] = ()
    tem_trecho_riscado: bool = False

    @property
    def id(self) -> str:
        return f"lc214-art-{self.numero.lower()}"


_ART = re.compile(f"^{ABRE_RISCADO}?\\s*Art\\.\\s*(\\d+)(?:[º°])?(?:-([A-Z]{{1,2}}))?(?=[\\s.]|$)")
_CABECALHO = re.compile(
    r"^(LIVRO|T[ÍI]TULO|CAP[ÍI]TULO|SE[ÇC][ÃA]O|SUBSE[ÇC][ÃA]O)\s+"
    r"([IVXLCDM]+|[ÚU]NICO)(?:-([A-Z]))?\s*(?:\(.*\))?$",
    re.IGNORECASE,
)
_FIM = re.compile(r"^(ANEXO\s+[IVXLC]+\b|Bras[íi]lia,)", re.IGNORECASE)
_ANOTACAO = re.compile(
    r"\(((?:Redação dada|Incluíd[oa]|Revogad[oa]|Vetad[oa]|Vide|Produção de efeitos"
    r"|Regulamento)[^()]*)\)"
)
_NORMA = re.compile(
    r"(Lei Complementar|Decreto-Lei|Decreto|Emenda Constitucional|Medida Provisória|Lei)"
    r"\s+n[ºo°]\s*([\d.]+)(?:\s*,\s*de\s+(?:\d{1,2}\s+de\s+\w+\s+de\s+)?(\d{4}))?"
)
_TIPOS = (
    ("redação dada", "redacao"),
    ("incluíd", "incluido"),
    ("revogad", "revogado"),
    ("vetad", "vetado"),
    ("vide", "vide"),
    ("produção de efeitos", "producao_efeitos"),
    ("regulamento", "regulamento"),
)
_NIVEIS = ("livro", "titulo", "capitulo", "secao", "subsecao")


def _sem_acento(texto: str) -> str:
    decomposto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in decomposto if not unicodedata.combining(c))


def _nivel(rotulo: str) -> str:
    chave = _sem_acento(rotulo).lower()
    for nivel in ("subsecao", "secao", "livro", "titulo", "capitulo"):
        if chave.startswith(nivel):
            return nivel
    raise ValueError(f"nível desconhecido: {rotulo!r}")


def extrair_alteracoes(texto: str) -> tuple[Alteracao, ...]:
    """Lista as anotações de alteração, veto, revogação e vigência presentes no texto."""
    achadas = []
    for m in _ANOTACAO.finditer(texto):
        conteudo = m.group(1).strip()
        minusculo = conteudo.lower()
        tipo = next(nome for prefixo, nome in _TIPOS if minusculo.startswith(prefixo))
        norma = ano = None
        n = _NORMA.search(conteudo)
        if n:
            norma = f"{n.group(1)} nº {n.group(2)}"
            ano = int(n.group(3)) if n.group(3) else None
        achadas.append(Alteracao(tipo=tipo, norma=norma, ano=ano, texto=conteudo))
    return tuple(achadas)


def dividir_em_artigos(texto: str) -> list[Artigo]:
    """Divide o texto em artigos, do art. 1º até o início dos anexos ou da assinatura.

    Só aceita um cabeçalho "Art. N" se o número for maior que o do artigo anterior; linhas
    fora de ordem (citações de outras leis, por exemplo) ficam no texto do artigo corrente.
    """
    linhas = [linha for linha in texto.split("\n") if linha]
    artigos: list[Artigo] = []
    hierarquia: dict[str, str] = {}
    atual: dict | None = None
    ultima = (0, "")

    def fechar() -> None:
        if atual is None:
            return
        corpo = "\n".join(atual["linhas"])
        artigos.append(
            Artigo(
                numero=atual["numero"],
                texto=corpo,
                hierarquia=atual["hierarquia"],
                alteracoes=extrair_alteracoes(corpo),
                tem_trecho_riscado=ABRE_RISCADO in corpo,
            )
        )

    i = 0
    while i < len(linhas):
        linha = linhas[i]
        i += 1
        if atual is not None and _FIM.match(linha):
            break
        cab = _CABECALHO.match(linha)
        if cab:
            nivel = _nivel(cab.group(1))
            rotulo = f"{cab.group(1).upper()} {cab.group(2).upper()}"
            if cab.group(3):
                rotulo += f"-{cab.group(3).upper()}"
            if i < len(linhas) and not _ART.match(linhas[i]) and not _CABECALHO.match(linhas[i]):
                rotulo += f" — {linhas[i]}"
                i += 1
            for inferior in _NIVEIS[_NIVEIS.index(nivel) :]:
                hierarquia.pop(inferior, None)
            hierarquia[nivel] = rotulo
            continue
        art = _ART.match(linha)
        if art:
            chave = (int(art.group(1)), art.group(2) or "")
            if chave > ultima:
                fechar()
                numero = art.group(1) + (f"-{art.group(2)}" if art.group(2) else "")
                atual = {"numero": numero, "linhas": [linha], "hierarquia": dict(hierarquia)}
                ultima = chave
                continue
        if atual is not None:
            atual["linhas"].append(linha)
    fechar()
    return artigos


def ler_artigos(conteudo: bytes) -> list[Artigo]:
    """Atalho: bytes do HTML do Planalto → lista de artigos."""
    return dividir_em_artigos(html_para_texto(decodificar(conteudo)))
