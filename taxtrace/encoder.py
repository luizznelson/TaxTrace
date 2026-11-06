"""Embeddings E5 locais: arquivos fixados, sem download durante consultas."""

import hashlib
import json
import math
import tempfile
import urllib.request
from functools import lru_cache
from importlib.metadata import version
from pathlib import Path

MODELO = "intfloat/multilingual-e5-small"
REVISAO = "614241f622f53c4eeff9890bdc4f31cfecc418b3"
ARQUIVOS = {
    "tokenizer.json": "0b44a9d7b51c3c62626640cda0e2c2f70fdacdc25bbbd68038369d14ebdf4c39",
    "onnx/model_qint8_avx512_vnni.onnx": (
        "dd476dd0c2514e9b9be83aeb3853fac0763e0bdf4a71645407587d77c48a2d88"
    ),
}
CONFIG = {
    "modelo": MODELO,
    "revisao": REVISAO,
    "arquivos": ARQUIVOS,
    "dimensoes": 384,
    "quantizacao": "qint8_avx512_vnni",
    "tokens_por_trecho": 320,
    "sobreposicao_tokens": 48,
    "pooling": "media_attention_mask_l2",
    "prefixos": ["query: ", "passage: "],
    "implementacao": 1,
    "onnxruntime": "1.31.1",
    "tokenizers": "0.23.3",
    "numpy": "2.5.4",
}
CONFIG_SHA256 = hashlib.sha256(json.dumps(CONFIG, sort_keys=True).encode()).hexdigest()


def sha256(caminho):
    with Path(caminho).open("rb") as arquivo:
        return hashlib.file_digest(arquivo, "sha256").hexdigest()


def pasta_modelo(raiz):
    return Path(raiz) / "data/models" / REVISAO


def preparar_modelo(raiz):
    pasta = pasta_modelo(raiz)
    for nome, checksum in ARQUIVOS.items():
        destino = pasta / nome
        if destino.is_file() and sha256(destino) == checksum:
            continue
        destino.parent.mkdir(parents=True, exist_ok=True)
        temporario = None
        try:
            with tempfile.NamedTemporaryFile(dir=destino.parent, delete=False) as arquivo:
                temporario = Path(arquivo.name)
                url = f"https://huggingface.co/{MODELO}/resolve/{REVISAO}/{nome}"
                with urllib.request.urlopen(url, timeout=60) as resposta:
                    while bloco := resposta.read(1024 * 1024):
                        arquivo.write(bloco)
            if sha256(temporario) != checksum:
                raise ValueError("hash_do_modelo_divergente")
            temporario.replace(destino)
        finally:
            if temporario and temporario.exists():
                temporario.unlink()
    return CONFIG


def vetor_sql(vetor):
    valores = [float(x) for x in vetor]
    if len(valores) != 384 or not all(math.isfinite(x) for x in valores):
        raise ValueError("vetor_invalido")
    norma = math.sqrt(sum(x * x for x in valores))
    if not 0.999 <= norma <= 1.001:
        raise ValueError("vetor_nao_normalizado")
    return json.dumps(valores)


def janelas(texto, offsets, *, tamanho=320, sobreposicao=48):
    if type(tamanho) is not int or not 0 <= sobreposicao < tamanho:
        raise ValueError("janela_invalida")
    offsets = [(a, b) for a, b in offsets if b > a]
    saida = []
    for inicio in range(0, len(offsets), tamanho - sobreposicao):
        fim = min(inicio + tamanho, len(offsets))
        a, b = offsets[inicio][0], offsets[fim - 1][1]
        if not 0 <= a < b <= len(texto):
            raise ValueError("offset_invalido")
        saida.append({"inicio": a, "fim": b, "texto": texto[a:b]})
        if fim == len(offsets):
            break
    return saida


class Encoder:
    def __init__(self, raiz):
        pasta = pasta_modelo(raiz)
        for nome, checksum in ARQUIVOS.items():
            if not (pasta / nome).is_file() or sha256(pasta / nome) != checksum:
                raise ValueError("modelo_local_ausente_ou_invalido")
        for nome in ("numpy", "onnxruntime", "tokenizers"):
            if version(nome) != CONFIG[nome]:
                raise ValueError("versao_de_dependencia_do_modelo_divergente")
        # Dependências opcionais: a busca textual não carrega este runtime.
        import numpy as np
        import onnxruntime as ort
        from tokenizers import Tokenizer

        self.np = np
        self.tokenizer = Tokenizer.from_file(str(pasta / "tokenizer.json"))
        self.tokenizer.no_truncation()
        self.tokenizer.no_padding()
        self.tokenizer.enable_padding(pad_id=1, pad_token="<pad>")
        opcoes = ort.SessionOptions()
        opcoes.intra_op_num_threads = 2
        opcoes.inter_op_num_threads = 1
        self.sessao = ort.InferenceSession(
            str(pasta / "onnx/model_qint8_avx512_vnni.onnx"),
            sess_options=opcoes,
            providers=["CPUExecutionProvider"],
        )

    def fragmentar(self, texto):
        codificado = self.tokenizer.encode(texto, add_special_tokens=False)
        return janelas(texto, codificado.offsets)

    def gerar(self, textos, *, consulta=False):
        if not textos:
            return []
        prefixo = "query: " if consulta else "passage: "
        codificados = self.tokenizer.encode_batch([prefixo + t for t in textos])
        if any(sum(c.attention_mask) > 512 for c in codificados):
            raise ValueError("texto_excede_janela_do_modelo")
        np = self.np
        dados = {
            "input_ids": np.array([c.ids for c in codificados], dtype=np.int64),
            "attention_mask": np.array([c.attention_mask for c in codificados], dtype=np.int64),
            "token_type_ids": np.array([c.type_ids for c in codificados], dtype=np.int64),
        }
        entradas = {i.name: dados[i.name] for i in self.sessao.get_inputs()}
        ocultos = self.sessao.run(None, entradas)[0]
        mascara = dados["attention_mask"][:, :, None].astype(np.float32)
        media = (ocultos * mascara).sum(axis=1) / mascara.sum(axis=1)
        vetores = media / np.linalg.norm(media, axis=1, keepdims=True)
        for vetor in vetores:
            vetor_sql(vetor)
        return vetores.tolist()


@lru_cache(maxsize=1)
def encoder_local(raiz):
    return Encoder(Path(raiz).resolve())
