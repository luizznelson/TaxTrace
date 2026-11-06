# Entrega local do RAG documental

Data: 2026-11-06. Escopo: critérios de evidência/recusa, geração citada, validação estrutural, revisão persistente e interface. Não houve deploy.

## Resultado observado

- 132 casos Python descobertos: 111 aprovados e 21 ignorados pelas condições opcionais. Seis testes JavaScript aprovados. Ruff (análise/formatação), sintaxe e formatação do frontend conferidos.
- Triagem: 12/12 critérios do conjunto de desenvolvimento atendidos com MCP e banco reais, sem chamar o modelo.
- Geração real: primeira rodada 2/3 gabaritos mínimos. A validação tratava incorretamente ordinais como `8º`. Após correção com regressão automatizada, 3/3 gabaritos mínimos; o primeiro registro foi preservado.
- Reexecução das três saídas salvas contra o validador final passou sem nova chamada ao provedor. Os 12 critérios também continuaram compatíveis. Ver `replay-final.json`.
- No navegador: resposta real do Gemini, citação abrindo e destacando o trecho, leitura integral preservada e revisão da resposta/contexto no mesmo hash.
- Troca PT/EN preservou o revisor, a justificativa e a origem do rascunho. O texto gerado permaneceu em português.
- Decisão de rejeição declarada como `teste_automatizado` foi persistida. A retomada não repetiu geração ou MCP; a verificação observou uma etapa de geração e duas chamadas MCP na execução de artigo explícito. Não se afirma revisão humana/fiscal real.
- Pergunta sobre vigência atual foi recusada com motivo, sem etapa de geração e sem encaminhamento para aprovação. Os documentos permaneceram disponíveis.
- Tela de 390 × 844: painel de recusa sem rolagem horizontal (conteúdo 375 px); nenhum erro capturado no console.
- Registros novos de avaliação e entrega foram conferidos contra valores de chaves e conexões locais, sem encontrá-los. Nenhum valor privado é incluído neste relatório.

## Evidências

- [Resposta real antes da decisão](answer.jpg)
- [Formulário com origem de teste identificada](review.jpg)
- [Recusa explicada](refusal.jpg)
- [Tela pequena](mobile.jpg)
- [Resposta/contexto e decisão sintética](revisao-real-com-decisao-sintetica.json)
- [Recusa sem geração](recusa-vigencia-sem-modelo.json)
- [Validador final aplicado às saídas salvas](replay-final.json)

Os conjuntos foram consultados durante a implementação e não representam avaliação independente. Citação literal, identificação de fonte e conceitos lexicais não provam implicação semântica, suficiência jurídica ou vigência. Revisão especializada, casos independentes e preparação de autenticação/consumo para publicação continuam pendentes. Não se afirma acurácia jurídica de 100%, custo zero ou ausência de risco de alucinação.

Metodologia e todos os resultados preliminares: [evals/RAG.md](../../evals/RAG.md). Critérios e implementação: [docs/RAG.md](../../docs/RAG.md).
