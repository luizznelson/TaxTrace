"""Interface local de consulta e revisão; não é um serviço público autenticado."""

import asyncio
import hashlib
import json
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Literal
from uuid import UUID

from dotenv import dotenv_values
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from filelock import Timeout
from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from starlette.middleware.trustedhost import TrustedHostMiddleware

from taxtrace.conexao import conectar
from taxtrace.consultas import resumo_base
from taxtrace.leitura import ler_integral
from taxtrace.revisao import decidir, iniciar, inspecionar


class ConsultaWeb(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    pergunta: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=500)]
    modo: Literal["local", "gemini", "rag"] = "local"
    coleta_id: Annotated[int, Field(ge=1)] | None = None


class DecisaoWeb(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)
    decisao: Literal["aprovar", "rejeitar"]
    revisor: str = Field(min_length=3, max_length=80)
    motivo: str = Field(min_length=5, max_length=1000)
    origem: Literal["operador_local", "teste_automatizado"]
    dossie_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


def resposta_json(dados):
    return JSONResponse(json.loads(json.dumps(dados, ensure_ascii=False, default=str)))


def falha_publica(erro):
    conflitos = {
        "revisao_nao_pendente",
        "codigo_alterado_inicie_nova_revisao",
        "dossie_da_decisao_divergente",
    }
    codigo = str(erro) if type(erro) is ValueError else "servico_indisponivel"
    if codigo in conflitos:
        return HTTPException(409, detail={"codigo": codigo})
    if codigo in {"revisao_nao_encontrada", "artigo_integral_indisponivel"}:
        return HTTPException(404, detail={"codigo": codigo})
    if isinstance(erro, Timeout):
        return HTTPException(409, detail={"codigo": "revisao_em_uso"})
    return HTTPException(503, detail={"codigo": "servico_indisponivel"})


def criar_app(raiz=None):
    raiz = Path(raiz) if raiz else Path(__file__).resolve().parent.parent
    assets = Path(__file__).resolve().parent / "static"
    cache = {}
    ativos = 0
    csrf = secrets.token_urlsafe(32)

    @asynccontextmanager
    async def lifespan(_app):
        yield
        pendentes = [r[1] for r in cache.values() if not r[1].done()]
        for tarefa in pendentes:
            tarefa.cancel()
        if pendentes:
            await asyncio.gather(*pendentes, return_exceptions=True)

    app = FastAPI(
        title="TaxTrace local", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan
    )
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"], www_redirect=False
    )

    @app.middleware("http")
    async def proteger(request: Request, call_next):
        if request.url.path.startswith("/api/"):
            origem = request.headers.get("origin")
            esperada = f"{request.url.scheme}://{request.headers.get('host', '')}"
            if (origem and origem != esperada) or request.headers.get(
                "sec-fetch-site"
            ) == "cross-site":
                return JSONResponse({"codigo": "origem_recusada"}, status_code=403)
            if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
                if not secrets.compare_digest(request.headers.get("x-taxtrace-csrf", ""), csrf):
                    return JSONResponse({"codigo": "pagina_expirada"}, status_code=403)
                if request.headers.get("content-type", "").split(";")[0] != "application/json":
                    return JSONResponse({"codigo": "json_obrigatorio"}, status_code=415)
                tamanho = request.headers.get("content-length", "")
                if not tamanho.isdigit() or int(tamanho) > 8192:
                    return JSONResponse({"codigo": "corpo_invalido_ou_grande"}, status_code=413)
        response = await call_next(request)
        response.headers.update(
            {
                "Content-Security-Policy": "default-src 'self'; script-src 'self'; "
                "style-src 'self'; "
                "img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; "
                "frame-ancestors 'none'; form-action 'self'",
                "X-Content-Type-Options": "nosniff",
                "Referrer-Policy": "no-referrer",
                "Cache-Control": "no-store",
                "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
            }
        )
        return response

    @app.exception_handler(RequestValidationError)
    async def entrada_invalida(_request, _erro):
        return JSONResponse({"codigo": "entrada_invalida"}, status_code=422)

    @app.get("/")
    async def pagina():
        return FileResponse(assets / "index.html")

    @app.get("/api/contexto")
    async def contexto():
        cfg = dotenv_values(raiz / ".env")
        return {
            "csrf": csrf,
            "gemini_disponivel": bool(cfg.get("GEMINI_API_KEY")),
            "rag_disponivel": bool(cfg.get("GEMINI_API_KEY")),
            "ambiente": "local_sem_autenticacao_multiusuario",
        }

    @app.get("/api/base")
    async def base():
        def ler():
            with conectar(raiz, leitura=True, autocommit=True) as conn:
                return resumo_base(conn)

        try:
            return resposta_json(await asyncio.to_thread(ler))
        except Exception as erro:
            raise falha_publica(erro) from None

    @app.post("/api/consultas")
    async def consultar(dados: ConsultaWeb, request: Request):
        nonlocal ativos
        try:
            identificador = str(UUID(request.headers.get("idempotency-key", "")))
        except ValueError:
            raise HTTPException(
                422, detail={"codigo": "identificador_de_tentativa_invalido"}
            ) from None
        fingerprint = hashlib.sha256(dados.model_dump_json().encode()).hexdigest()
        if identificador in cache:
            anterior, tarefa = cache[identificador]
            if anterior != fingerprint:
                raise HTTPException(409, detail={"codigo": "tentativa_com_outro_conteudo"})
        else:
            if ativos >= 2:
                raise HTTPException(429, detail={"codigo": "consultas_em_andamento"})
            if len(cache) >= 32:
                fechados = [k for k, v in cache.items() if v[1].done()]
                if not fechados:
                    raise HTTPException(429, detail={"codigo": "consultas_em_andamento"})
                del cache[fechados[0]]
            ativos += 1

            async def trabalho():
                nonlocal ativos
                try:
                    return await iniciar(
                        dados.pergunta, modo=dados.modo, coleta_id=dados.coleta_id, raiz=raiz
                    )
                finally:
                    ativos -= 1

            tarefa = asyncio.create_task(trabalho())
            cache[identificador] = (fingerprint, tarefa)
        try:
            return resposta_json(await asyncio.shield(tarefa))
        except Exception as erro:
            raise falha_publica(erro) from None

    @app.get("/api/revisoes/{revisao_id}")
    async def recuperar(revisao_id: UUID):
        try:
            return resposta_json(await inspecionar(str(revisao_id), raiz=raiz))
        except Exception as erro:
            raise falha_publica(erro) from None

    @app.get("/api/revisoes/{revisao_id}/artigos/{numero}")
    async def artigo_integral(revisao_id: UUID, numero: str):
        try:
            relatorio = await inspecionar(str(revisao_id), raiz=raiz)

            def ler():
                with conectar(raiz, leitura=True, autocommit=True) as conn:
                    return ler_integral(conn, relatorio, numero, raiz)

            return resposta_json(await asyncio.to_thread(ler))
        except Exception as erro:
            raise falha_publica(erro) from None

    @app.post("/api/revisoes/{revisao_id}/decisao")
    async def decisao(revisao_id: UUID, dados: DecisaoWeb):
        try:
            return resposta_json(await decidir(str(revisao_id), dados.model_dump(), raiz=raiz))
        except Exception as erro:
            raise falha_publica(erro) from None

    @app.get("/api/revisoes/{revisao_id}/exportar")
    async def exportar(revisao_id: UUID):
        try:
            dados = await inspecionar(str(revisao_id), raiz=raiz)
            return Response(
                json.dumps(dados, ensure_ascii=False, indent=2),
                media_type="application/json",
                headers={
                    "Content-Disposition": f'attachment; filename="taxtrace-{revisao_id}.json"'
                },
            )
        except Exception as erro:
            raise falha_publica(erro) from None

    app.mount("/assets", StaticFiles(directory=assets), name="assets")
    return app


app = criar_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8015, proxy_headers=False, access_log=False)
