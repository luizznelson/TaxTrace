"""Conta local de revisor; não autentica identidade civil ou qualificação fiscal."""

import argparse
import getpass
import hashlib
import hmac
import json
import os
import re
import secrets
import time
from pathlib import Path

from dotenv import dotenv_values

COOKIE = "taxtrace_revisor"
DURACAO = 3600


def derivar(senha, salt):
    return hashlib.scrypt(senha.encode("utf-8"), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()


def criar_credencial(conta, nome, senha):
    if not re.fullmatch(r"[a-z][a-z0-9_.-]{2,39}", conta):
        raise ValueError("conta_invalida")
    if not 3 <= len(nome.strip()) <= 80 or any(ord(c) < 32 for c in nome):
        raise ValueError("nome_invalido")
    if not 12 <= len(senha) <= 256:
        raise ValueError("senha_deve_ter_12_a_256_caracteres")
    salt = secrets.token_hex(16)
    return {
        "versao": 1,
        "conta": conta,
        "nome": nome.strip(),
        "salt": salt,
        "hash": derivar(senha, salt),
    }


def validar_credencial(c):
    if (
        not isinstance(c, dict)
        or set(c) != {"versao", "conta", "nome", "salt", "hash"}
        or type(c["versao"]) is not int
        or c["versao"] != 1
        or not all(isinstance(c[k], str) for k in ("conta", "nome", "salt", "hash"))
        or not re.fullmatch(r"[a-z][a-z0-9_.-]{2,39}", c["conta"])
        or not 3 <= len(c["nome"].strip()) <= 80
        or any(ord(ch) < 32 for ch in c["nome"])
        or not re.fullmatch(r"[0-9a-f]{32}", c["salt"])
        or not re.fullmatch(r"[0-9a-f]{128}", c["hash"])
    ):
        raise ValueError("credencial_de_revisor_invalida")
    return dict(c)


class AcessoRevisor:
    def __init__(self, raiz, relogio=time.monotonic):
        self.relogio = relogio
        self.sessoes = {}
        self.falhas = 0
        self.bloqueado_ate = 0
        self.credencial = None
        caminho = Path(raiz) / "data/checkpoints/revisor.json"
        cfg = dotenv_values(Path(raiz) / ".env")
        configurada = os.environ.get(
            "TAXTRACE_REVIEWER_CREDENTIAL_JSON", cfg.get("TAXTRACE_REVIEWER_CREDENTIAL_JSON")
        )
        try:
            # Configuração explícita prevalece; inválida não volta ao arquivo.
            if configurada:
                self.credencial = validar_credencial(json.loads(configurada))
            elif caminho.exists():
                self.credencial = validar_credencial(
                    json.loads(caminho.read_text(encoding="utf-8"))
                )
        except Exception:
            raise ValueError("credencial_de_revisor_invalida") from None

    def verificar(self, conta, senha):
        if self.relogio() < self.bloqueado_ate:
            raise ValueError("acesso_em_espera")
        if self.credencial is None:
            raise ValueError("revisor_nao_configurado")
        c = self.credencial
        # Deriva mesmo para conta desconhecida, evitando diferença trivial de tempo.
        valido = hmac.compare_digest(derivar(senha, c["salt"]), c["hash"])
        if not (hmac.compare_digest(conta.encode(), c["conta"].encode()) and valido):
            self.falhas += 1
            if self.falhas >= 5:
                self.bloqueado_ate = self.relogio() + 60
                self.falhas = 0
            raise ValueError("credenciais_invalidas")
        self.falhas = 0

    def abrir(self):
        self.limpar()
        if len(self.sessoes) >= 8:
            del self.sessoes[next(iter(self.sessoes))]
        token = secrets.token_urlsafe(32)
        self.sessoes[hashlib.sha256(token.encode()).hexdigest()] = self.relogio() + DURACAO
        return token

    def limpar(self):
        agora = self.relogio()
        self.sessoes = {k: v for k, v in self.sessoes.items() if v > agora}

    def usuario(self, token):
        self.limpar()
        if not self.credencial or not token or len(token) > 128:
            return None
        if hashlib.sha256(token.encode()).hexdigest() not in self.sessoes:
            return None
        return {k: self.credencial[k] for k in ("conta", "nome")}

    def sair(self, token):
        if token and len(token) <= 128:
            self.sessoes.pop(hashlib.sha256(token.encode()).hexdigest(), None)


def main():
    parser = argparse.ArgumentParser(description="Configurar uma conta local de revisor.")
    parser.add_argument("--conta", required=True)
    parser.add_argument("--nome", required=True)
    args = parser.parse_args()
    senha = getpass.getpass("Senha (mínimo 12 caracteres): ")
    confirmar = getpass.getpass("Confirme a senha: ")
    if senha != confirmar:
        raise SystemExit("As senhas não coincidem. Nenhum arquivo foi criado.")
    try:
        credencial = criar_credencial(args.conta, args.nome, senha)
        destino = Path(__file__).resolve().parent.parent / "data/checkpoints/revisor.json"
        destino.parent.mkdir(parents=True, exist_ok=True)
        with destino.open("x", encoding="utf-8") as arquivo:
            arquivo.write(json.dumps(credencial, ensure_ascii=False, indent=2) + "\n")
    except (ValueError, FileExistsError) as erro:
        raise SystemExit(
            "Credencial existente: preserve-a ou remova-a manualmente para substituir."
            if isinstance(erro, FileExistsError)
            else str(erro)
        ) from None
    print("Conta criada. Reinicie a aplicação. Não publique o arquivo de credencial.")


if __name__ == "__main__":
    main()
