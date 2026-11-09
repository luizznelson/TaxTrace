# TaxTrace

Traceable lookup of Brazilian consumption tax reform sources: find an article, check its origin and identify the dataset version used.

Português: [README.md](README.md)

## Business purpose

A tax team needs to check the legal basis of a tax classification. Relevant information is spread across legal text and structured tables. Without a recorded source and version, reviewing a conclusion becomes harder.

TaxTrace organizes those sources to support that review. Reducing manual lookup is a goal; time savings and use by tax professionals have not yet been measured.

## Implemented

- Official-source collection with URLs, timestamps, file sizes and hashes.
- Article parsing with amendment and strikethrough records.
- Structured tax tables and links between classifications and cited articles.
- Transactional, collection-bound PostgreSQL loading with duplicate rejection.
- Portuguese full-text search with literal excerpts, citations and collection metadata.
- Read-only query login and a separate local integration-test database.

**Document RAG is implemented locally:** retrieved evidence, Gemini synthesis with checked literal citations, conservative refusals and an answer-bound review hash. See [workflow and limits](docs/RAG.md) and [development evaluation](evals/RAG.md). Authenticated multi-user review, device/date-specific legal validity verification and independent expert-reviewed answer evaluation remain **pending**. The default v4 search remains textual. Experimental local embeddings and pgvector retrieval remain explicit alternatives; the RAG workflow uses the stronger textual baseline.

## Recorded local verification

The [verification record](runs/2026-11-06-local-database/verification.json) contains 580 articles, 170 classifications, 169 links, 10,515 NCM records and three preserved source discrepancies. Capture date: 2026-11-05. API query date: 2027-01-01. Dataset: V0066. These dates have different meanings and do not establish legal validity.

The record includes successful and empty searches, read-only permission checks and duplicate-load rejection. It does not establish remote CI execution. Neon provisioning was subsequently verified separately, as documented below.

## Local setup (Windows)

Requires Python 3.14 and Docker Desktop. Run from the repository root:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt -r requirements-dev.txt
Copy-Item .env.example .env
```

Keep an existing `.env`. Replace all example passwords in the file and their matching URLs. Never commit it. No AI API key is needed yet.

```powershell
docker compose --profile tests up -d --wait
.venv/Scripts/python.exe -m taxtrace.coleta --data 2027-01-01
.venv/Scripts/python.exe -m taxtrace.banco
.venv/Scripts/python.exe -m taxtrace.busca --consulta "credito presumido" --limite 3
```

The sample date reproduces this development snapshot, not today's date. If the official law download fails, use the collector's `--lei-arquivo` option with a locally saved official HTML file. Raw downloads are excluded from Git. Source terms and API limits remain open items in [PLANO.md](PLANO.md).

Development binds only to loopback port 15433, with persistent storage. Tests bind to 15434, with temporary storage. Avoid `down -v` if development data must be kept. Remote maintenance remains blocked in normal runtime. Optional Neon access requires pinned destination settings and restricted reader/state roles; provisioning uses a separate explicit administrative command.

## Retrieval evaluation

The [current comparison](evals/COMPARACAO.md) records queries, reference articles, gains and failures. The default v4 preserves the original search order and fills empty slots with new candidates from the expanded search.

- Original development set: **19/20 references within the top five**, versus 14/20 for v1.
- Additional development questions: **11/12**, versus 6/12 for v1.
- No previously successful v1 case was lost in either comparison; the entire original prefix was preserved.

These are development results, not independent legal validation. The additional set was consulted during the choice of strategy. Two synthetic controls per set are scored separately. Article retrieval does not establish legal correctness or sufficient excerpt evidence.

```powershell
.venv/Scripts/python.exe -m taxtrace.avaliacao
.venv/Scripts/python.exe -m taxtrace.avaliacao --casos evals/recuperacao.adicional.v1.json
```

Each run records code and dataset hashes, collection and per-case outcomes. Select `--metodo v1` to reproduce the original baseline. v2 and RRF-based v3 remain experimental. For an existing database, run `.venv/Scripts/python.exe -m taxtrace.banco --somente-esquema` once to create the additive indexes.

The default v4 queries only through the read-only login. Result metadata identifies candidate origin, partial matches and missing normalized terms. Scores from different underlying searches are not directly comparable. A full original list is left unchanged, so v4 cannot improve its ordering.

## Experimental semantic retrieval

A pinned, local multilingual E5 model generated 384-dimensional vectors for **990 chunks from 580 articles**. No AI API key is required. Semantic retrieval found 12/20 and 9/12 reference articles, below textual v4 (19/20 and 11/12). It also returned neighbors for every synthetic empty-result control; no abstention threshold has been calibrated. The default search was therefore preserved.

See [setup, methodology and limitations](evals/SEMANTICA.md). Optional dependencies are in `requirements-embeddings.txt`. Download weights explicitly with `python -m taxtrace.vetores preparar-modelo`, then build the local index with `python -m taxtrace.vetores indexar`, using the virtual environment's Python. Query or evaluate with `--metodo semantica`. Model files are hashed and excluded from Git. No queries are sent to an AI provider by this encoder.

This experiment evaluates retrieval only; answer generation is evaluated separately in [RAG evaluation](evals/RAG.md). Real-model evaluation was local; core CI uses synthetic vectors and does not download model weights.

## Hybrid retrieval and excerpt checks

The [hybrid experiment](evals/HIBRIDA.md) combines textual and semantic rankings through RRF. It retrieved 16/20 and 9/12 reference articles, below the default textual search. Select `--metodo hibrida` explicitly after preparing the semantic index; the default remains v4.

Evaluation now checks that returned excerpts are literal source substrings and whether a reference anchor appears in the excerpt of the expected article. Semantic retrieval found the expected article without displaying its anchor in three queries. This metric does not establish sufficient evidence or legal correctness; sufficiency remains unevaluated. Reports preserve excerpts and hashes, and operational failures are not disguised as empty results.

## Read-only MCP tools

The [local MCP server](docs/MCP.md) exposes four structured tools: collection coverage, article search, paginated article reading and exact cClassTrib lookup. Responses identify the collection and source; they do not classify a product or provide tax advice.

```powershell
.venv/Scripts/python.exe -m taxtrace.verificar_mcp
```

The verifier launches a real stdio subprocess, discovers the tools and records successful and expected-error calls under `runs/`. The implementation uses pinned official SDK `mcp==2.3.0`, strict bounded inputs and the read-only database login. No HTTP endpoint, model API key or embeddings download is needed. LangGraph planning integration is now documented separately; desktop-host integration remains untested.

## LangGraph query workflow

The [LangGraph workflow](docs/AGENTE.md) selects a bounded action, calls the real MCP server and checks collection identity and citation metadata. Local mode uses explicit routing rules; Gemini mode uses a real model only for planning. Both have recorded local executions, including three Gemini calls. This is not an independent planning benchmark.

```powershell
.venv/Scripts/python.exe -m taxtrace.agente --consulta "Leia o artigo 125."
.venv/Scripts/python.exe -m taxtrace.agente --modo gemini --consulta "Qual artigo trata da cesta basica?"
```

Gemini mode requires `GEMINI_API_KEY` in the local `.env`; the current model setting is `GEMINI_MODEL=gemini-3.5-flash-lite`. Each run permits at most one model request and three MCP calls. Operational failures remain distinct from missing references. Local audit records include the plan, collection, tool responses and code hashes; LangSmith tracing is explicitly disabled. The separate `rag` mode generates a documentary answer with citations; it does not provide individualized tax advice. Persistent review includes the generated answer when this mode is selected.

## Persistent document review

The [review workflow](docs/REVISAO.md) uses SQLite checkpoints and a typed LangGraph interrupt. Start a query, inspect its frozen evidence package, then resume with an explicitly attributed decision and the package hash. A per-review lock prevents concurrent application operations; completed reviews reject a second decision. Resume does not restart MCP or call the model.

```powershell
.venv/Scripts/python.exe -m taxtrace.revisao iniciar --consulta "Leia o artigo 125."
.venv/Scripts/python.exe -m taxtrace.verificar_revisao
```

The verifier exercises synthetic approval/rejection across separate processes and labels them as automated. It does not claim a real human review. Operator identity is self-declared, not authenticated; document approval does not establish legal correctness. Private checkpoints and lock files are excluded from Git, while reviewed public audit exports remain under `runs/`.

## Local application

The [TaxTrace interface](docs/INTERFACE.md) brings **research, source reading and document review** into one workspace: selectable results, an adjacent reader and a decision form with the source still accessible. Navigation separates Document research, Session reviews and Collection and sources. Dedicated inputs support topics, article numbers and cClassTrib codes, with tab history and record export. Portuguese and English UI are available; official documents retain their original text.

```powershell
.venv/Scripts/python.exe -m taxtrace.web
```

Open [the local application](http://127.0.0.1:8015/). The database must be running. This is a local application, without public deployment or multiuser authentication.

## Checks

```powershell
$env:TAXTRACE_TEST_DATABASE='1'
.venv/Scripts/python.exe -m unittest discover -s tests -q
node --test tests/query-input.test.mjs
.venv/Scripts/ruff.exe check .
.venv/Scripts/ruff.exe format --check .
```

Integration tests require explicit opt-in and the dedicated local test database, user and port. They never fall back to the development URL. Their transactions are rolled back. Integration tests are skipped without opt-in; real-source tests are skipped when local raw files are absent.

## Repository guide

`taxtrace/` contains collection, integrity checks, parsers, linking, persistence and search. `tests/` contains automated checks. `runs/` holds public verification records without secrets. `PLANO.md` tracks source research and pending milestones.

## Operation and evidence

Docker/Linux execution with real PostgreSQL passed **193 tests**, with three skipped without the official raw collection. Tests covered checkpoints, events, browser isolation and runtime-role permissions. [Evidence](runs/2026-11-07-neon-runtime-preparation/verification.json) preserves preliminary failures and the cleanup fix. No deployment or automatic history migration was performed.

Authorized Neon provisioning was completed on November 8, 2026: **580 articles, 170 classifications, 10,515 NCM records and seven preserved files**. Restricted roles, client TLS, source integrity and review resumption across two Linux processes were verified. The technical review used no model API and recorded an automated rejection, not human approval. [Remote evidence](runs/2026-11-08-neon-provision/README.md). The application is not deployed yet.

- [Render Free deployment guide](docs/RENDER.md): prepared configuration, HTTPS cookies, usage limits and private environment settings. [Public service](https://taxtrace.onrender.com/) verified with one real RAG request and persisted review; reviewer setup remains pending. [Evidence](runs/2026-11-08-render-live/verification.json).
- [Neon and preserved-source preparation](docs/NEON.md): private configuration, pinned destination, TLS policy and source snapshots in PostgreSQL.
- [Docker](docs/DOCKER.md): local runtime and disposable integration environment.
- [Persistence](docs/PERSISTENCIA.md): SQLite by default; optional PostgreSQL checkpoints, events and access bindings.
- [Reviewer authentication](docs/AUTENTICACAO.md) and [access authorization](docs/AUTORIZACAO.md): authenticated decisions and browser-owned or administrative reads. Credentials may come from private runtime configuration.
- [Diagnostics and evaluation](docs/OPERACAO.md): service status and development reports.
- [Adversarial cases](evals/RAG.md) and [quality review package](docs/REVISAO_AVALIACAO.md): all 12 cases still await specialist review; exporting a package does not establish independent review. Technical guides are currently in Portuguese.

## Interpretation limits

Search depends on the entered terms and can miss relevant articles. An empty result is not proof that the law contains no evidence. Ranking is not legal confidence. Removing strikethrough text from the index does not establish legal validity; the original text remains stored. Hashes check consistency against the manifest, not the source's digital signature.

This is lookup support, not tax advice. Verify the official source before making a decision.
