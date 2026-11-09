# Explore TaxTrace

[Main README](../README.en.md) · [Português](README.md)

Start with the problem and user workflow, inspect measured results, then move to
implementation. The main README and this map are available in English; detailed
technical guides are primarily in Portuguese. Code, contracts and evidence files
are linked directly from those guides.

| Goal | Recommended route |
| --- | --- |
| Understand the proposed use | [Case study](case-study.md) → [video](DEMONSTRACAO.md) → [live app](https://taxtrace.onrender.com/) |
| Assess the engineering | [Architecture](architecture.md) → [quality and limitations](quality.md) → [recorded runs](../runs/README.md) |
| Reproduce the implementation | [Development](development.md) → [retrieval evaluation](../evals/README.md) → [deployment](RENDER.md) |
| Inspect retrieval choices | [Textual v4](../evals/COMPARACAO.md), [semantic](../evals/SEMANTICA.md), [hybrid](../evals/HIBRIDA.md) |
| Inspect generation and tools | [RAG](RAG.md), [MCP](MCP.md), [agent](AGENTE.md), [RAG evaluation](../evals/RAG.md) |
| Inspect state and trust | [Review](REVISAO.md), [authentication](AUTENTICACAO.md), [authorization](AUTORIZACAO.md), [persistence](PERSISTENCIA.md) |
| Operate the app | [Docker](DOCKER.md), [Neon](NEON.md), [Render](RENDER.md), [diagnostics](OPERACAO.md) |
| Review contribution and presentation | [Contributing](../CONTRIBUTING.md), [GitHub metadata](GITHUB.md), [pending expert evaluation](REVISAO_AVALIACAO.md) |

`evals/` holds rubrics and experiment interpretation; `runs/` preserves individual
results, including failures. A historical record describes its original run, not
the current product status. The [run index](../runs/README.md) separates the key
milestones from the full inventory. Historical JSON files were not rewritten.

`media/` contains the final videos, captions and cover. Secrets, raw downloads,
model weights, private checkpoints and editing intermediates are excluded from
Git. The [MIT license](../LICENSE) covers code, not third-party source material.
