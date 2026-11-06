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

Embeddings, RAG, MCP tools, LangGraph, answer evaluation with reviewed labels and a UI are **planned**, not implemented. The pgvector extension is available, but the current search uses neither vectors nor LLMs.

## Recorded local verification

The [verification record](runs/2026-11-06-local-database/verification.json) contains 580 articles, 170 classifications, 169 links, 10,515 NCM records and three preserved source discrepancies. Capture date: 2026-11-05. API query date: 2027-01-01. Dataset: V0066. These dates have different meanings and do not establish legal validity.

The record includes successful and empty searches, read-only permission checks and duplicate-load rejection. It does not claim that remote CI or Neon has been verified.

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

Development binds only to loopback port 15433, with persistent storage. Tests bind to 15434, with temporary storage. Avoid `down -v` if development data must be kept. Remote database connections are intentionally blocked at this stage; Neon is deferred until deployment.

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

## Checks

```powershell
$env:TAXTRACE_TEST_DATABASE='1'
.venv/Scripts/python.exe -m unittest discover -s tests -q
.venv/Scripts/ruff.exe check .
.venv/Scripts/ruff.exe format --check .
```

Integration tests require explicit opt-in and the dedicated local test database, user and port. They never fall back to the development URL. Their transactions are rolled back. Integration tests are skipped without opt-in; real-source tests are skipped when local raw files are absent.

## Repository guide

`taxtrace/` contains collection, integrity checks, parsers, linking, persistence and search. `tests/` contains automated checks. `runs/` holds public verification records without secrets. `PLANO.md` tracks source research and pending milestones.

## Interpretation limits

Search depends on the entered terms and can miss relevant articles. An empty result is not proof that the law contains no evidence. Ranking is not legal confidence. Removing strikethrough text from the index does not establish legal validity; the original text remains stored. Hashes check consistency against the manifest, not the source's digital signature.

This is lookup support, not tax advice. Verify the official source before making a decision.
