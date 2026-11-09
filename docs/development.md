# Desenvolvimento e reprodução

[Visão geral](../README.md) · [Arquitetura](architecture.md) · [Qualidade](quality.md) · [Documentação](README.md)

Para experimentar sem preparar dados, use [o app publicado](https://taxtrace.onrender.com/).
Este guia é para desenvolver e reproduzir no computador. Os comandos PowerShell
partem da raiz do repositório; no Linux, o Python do ambiente é `.venv/bin/python`.

## 1. Ambiente e configuração privada

Requisitos: Python 3.14, Docker Desktop ativo e Node para os testes JavaScript.
Dependências de embeddings são opcionais e ficam fora da imagem de runtime.

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt -r requirements-dev.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Edite `.env` e substitua as senhas de desenvolvimento, teste e leitor, mantendo
cada senha correspondente em sua URL. Preserve um arquivo já configurado.
[Modelo sem segredos](../.env.example). O modo direto não exige chave; planejamento
com IA e RAG usam `GEMINI_API_KEY`, com `GEMINI_MODEL` e, opcionalmente,
`GEMINI_RAG_MODEL`. A chave não é usada pelos testes padrão.

Não troque a conexão administrativa local por uma URL Neon. Hospedagem tem
[preparação e papéis separados](NEON.md); arquivos `.env*` reais não são commitados.

## 2. Banco, captura e carga

```powershell
docker compose --profile tests up -d --wait
.venv/Scripts/python.exe -m taxtrace.coleta --data 2027-01-01
.venv/Scripts/python.exe -m taxtrace.banco
.venv/Scripts/python.exe -m taxtrace.busca --consulta "credito presumido" --limite 3
```

A data acima reproduz o **parâmetro** da captura de desenvolvimento, não promete
obter os mesmos bytes hoje. A API e a página legal podem mudar; os hashes dos
registros não substituem os arquivos originais. Quando o Planalto interromper
o download, o coletor aceita `--lei-arquivo` com o HTML oficial salvo localmente.
Downloads ficam em `data/raw/`, ignorado pelo Git.

A carga valida manifesto e fonte, preserva a coleta e recusa duplicatas. Para
acrescentar os índices a um banco existente, sem recarregar a captura:

```powershell
.venv/Scripts/python.exe -m taxtrace.banco --somente-esquema
```

Desenvolvimento usa loopback na porta 15433, com volume persistente. Testes usam
15434 e armazenamento temporário. Não use `down -v` para encerrar o desenvolvimento:
isso excluiria o volume. A composição de integração, abaixo, é outro projeto.

## 3. Aplicação, ferramentas e revisão

```powershell
.venv/Scripts/python.exe -m taxtrace.web
```

Abra [a aplicação local](http://127.0.0.1:8015/). A interface depende da base carregada.
SQLite é o padrão local para checkpoints; o app hospedado usa PostgreSQL.

Para investigar o fluxo sem navegar:

```powershell
.venv/Scripts/python.exe -m taxtrace.verificar_mcp
.venv/Scripts/python.exe -m taxtrace.agente --consulta "Leia o artigo 125."
.venv/Scripts/python.exe -m taxtrace.agente --modo gemini --consulta "Qual artigo trata da cesta basica?"
.venv/Scripts/python.exe -m taxtrace.revisao iniciar --modo rag --consulta "O que o artigo 125 informa sobre as alíquotas do IBS e da CBS?"
```

O primeiro comando inicia cliente/servidor MCP locais, sem modelo. O modo `gemini`
usa IA no planejamento; `rag` usa IA na síntese e pode consumir a cota da conta.
Não execute chamadas ao vivo apenas para repetir um teste já registrado.
[Contrato MCP](MCP.md), [fluxo](AGENTE.md), [RAG](RAG.md), [revisão](REVISAO.md).

Para decisões na interface, crie sua conta por entrada interativa da senha:

```powershell
.venv/Scripts/python.exe -m taxtrace.autenticacao --conta revisor --nome "Seu nome"
```

A conta local não é enviada à hospedagem por commit. O Render recebe o hash em
variável privada, conforme [publicação](RENDER.md). Não compartilhe a conta de
revisor como acesso público de demonstração. O [verificador de revisão](../taxtrace/verificar_revisao.py)
usa decisões sintéticas identificadas; não comprova aprovação fiscal humana.

## Verificações

Com o banco de testes local ativo e a URL dedicada no `.env`:

```powershell
$env:TAXTRACE_TEST_DATABASE='1'
.venv/Scripts/python.exe -m unittest discover -s tests -q
node --test tests/query-input.test.mjs
.venv/Scripts/ruff.exe check .
.venv/Scripts/ruff.exe format --check .
```

Sem opt-in, integrações são desativadas. Sem captura oficial local, os testes
que dependem dela também são desativados. Isso precisa ser declarado ao relatar
resultados; não transforme um teste ignorado em aprovado. O destino de teste é
`taxtrace_test`, com usuário próprio, loopback e porta 15434.

Para conferir o runtime Linux com PostgreSQL descartável, sem usar a base de
desenvolvimento ou o Neon:

```powershell
docker build --load -t taxtrace:ci .
docker compose -p taxtrace-integration -f docker-compose.integration.yml up --abort-on-container-exit --exit-code-from integration-tests
docker compose -p taxtrace-integration -f docker-compose.integration.yml down
```

Use o nome do projeto de integração na limpeza; não substitua pelo projeto de
desenvolvimento. O `--load` garante que o resultado do builder fique disponível
ao motor local. [Docker e smoke](DOCKER.md).

## Avaliar recuperação e geração

```powershell
.venv/Scripts/python.exe -m taxtrace.avaliacao
.venv/Scripts/python.exe -m taxtrace.avaliacao --casos evals/recuperacao.adicional.v1.json
.venv/Scripts/python.exe -m taxtrace.avaliar_adversarial --saida artifacts/rag-adversarial.json
```

A comparação textual, instalação do encoder, busca híbrida e chamadas RAG ao
vivo têm guias próprios: [avaliações](../evals/README.md), [semântica](../evals/SEMANTICA.md),
[híbrida](../evals/HIBRIDA.md), [RAG](../evals/RAG.md). Cada avaliação deve gravar
nova evidência, preservar falhas e identificar código, coleta e gabarito.

## Organização e publicação

[CONTRIBUTING.md](../CONTRIBUTING.md) resume contribuição e revisão. `.editorconfig`
e `.gitattributes` padronizam texto e distinguem binários; não foi feita uma
renormalização em massa do código nem reescrito o histórico Git.

O [Blueprint](../render.yaml) pede publicação após checks do GitHub. A ativação no
serviço depende da sincronização no painel; ter o YAML não comprova um deploy
automático concluído. [Passo a passo](RENDER.md).
