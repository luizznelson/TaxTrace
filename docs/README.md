# Como explorar o TaxTrace

[README principal](../README.md) · [English documentation map](README.en.md)

A leitura segue a tarefa do usuário: entender o problema, experimentar, conferir
os resultados e só então aprofundar a implementação.

## Escolha seu percurso

| Objetivo | Percurso recomendado |
| --- | --- |
| **Entender a proposta** | [Caso de uso](case-study.md) → [vídeo](DEMONSTRACAO.md) → [app publicado](https://taxtrace.onrender.com/) |
| **Avaliar a engenharia** | [Arquitetura](architecture.md) → [qualidade](quality.md) → [evidências](../runs/README.md) |
| **Reproduzir o trabalho** | [Desenvolvimento](development.md) → [avaliações](../evals/README.md) → [operações](RENDER.md) |

## Guias por responsabilidade

| Tema | Documentos |
| --- | --- |
| Problema, perguntas e escopo | [Estudo de caso](case-study.md), [plano de trabalho](../PLANO.md) |
| Decisões e fronteiras do sistema | [Arquitetura](architecture.md), [MCP](MCP.md), [agente](AGENTE.md) |
| Síntese com evidências | [RAG](RAG.md), [avaliação do RAG](../evals/RAG.md) |
| Comparação de recuperação | [Textual v4](../evals/COMPARACAO.md), [semântica](../evals/SEMANTICA.md), [híbrida](../evals/HIBRIDA.md) |
| Experiência e demonstração | [Interface](INTERFACE.md), [vídeo](DEMONSTRACAO.md) |
| Revisão e responsabilidade | [Pausa/retomada](REVISAO.md), [autenticação](AUTENTICACAO.md), [autorização](AUTORIZACAO.md) |
| Qualidade e limites | [Guia de qualidade](quality.md), [revisão especializada pendente](REVISAO_AVALIACAO.md) |
| Ambiente e publicação | [Desenvolvimento](development.md), [Docker](DOCKER.md), [Neon](NEON.md), [Render](RENDER.md) |
| Diagnósticos e estado | [Operação](OPERACAO.md), [persistência](PERSISTENCIA.md) |
| Apresentação no GitHub | [About, pins e percurso de revisão](GITHUB.md), [contribuição](../CONTRIBUTING.md) |

## Como ler as evidências

`evals/` contém gabaritos e interpretação dos experimentos. `runs/` guarda resultados
por execução, inclusive falhas e tentativas anteriores. O [índice de runs](../runs/README.md)
destaca as entregas e oferece um inventário completo sem alterar os arquivos originais.

Uma pendência dentro de um registro histórico descreve aquela execução. O estado
atual é apresentado no README e nos guias; não foi reescrito um JSON antigo para
parecer que um teste posterior já existia. `PLANO.md` orienta o trabalho e mantém
pendências abertas, mas não substitui código, medidas ou evidências.

`media/` contém somente vídeos, legendas e capa destinados à apresentação.
Downloads brutos, pesos, segredos, checkpoints e intermediários de edição não
fazem parte da distribuição Git. A [MIT](../LICENSE) é a licença do código.
