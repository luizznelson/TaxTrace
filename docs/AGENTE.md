# Agente LangGraph: consulta e RAG documental

O grafo reúne planejamento, ferramentas MCP, conferência de origem e, quando escolhido, geração de uma resposta citada. Não executa SQL produzido por modelo, não escreve nas tabelas da fonte e não decide enquadramento tributário.

## Modos disponíveis

| Modo     | Planejamento                     | Resultado                                       | Chamadas de modelo      |
| -------- | -------------------------------- | ----------------------------------------------- | ----------------------- |
| `local`  | Regras de entrada                | Evidências documentais                          | Nenhuma                 |
| `gemini` | Gemini escolhe uma ação limitada | Evidências documentais                          | Até uma de planejamento |
| `rag`    | Regras de entrada                | Rascunho com citações ou recusa/falha explícita | Até uma de síntese      |

Os modos não fazem fallback silencioso. O usuário escolhe se a pergunta será enviada ao provedor. No RAG, o contexto público recuperado também é enviado. O modelo e o uso informado pelo provedor são registrados; cotas e cobrança continuam sujeitos à conta e ao serviço.

## Contrato e limites

O plano permite buscar termos, ler artigo explícito, consultar cClassTrib explícito ou recusar. Referências propostas pelo planejador precisam existir na pergunta para consultas diretas. Regras locais detectam referências ambíguas; isso não representa interpretação semântica completa.

Cada execução usa até três chamadas MCP: identificar a base, consultar e, quando houver candidato, abrir o primeiro artigo. A coleta é fixada e conferida por ID, manifesto e data de consulta. O papel do banco é somente leitura e os parâmetros são validados pelo servidor. O primeiro candidato não é automaticamente declarado juridicamente suficiente.

No modo RAG, a leitura tem limite de 8.000 caracteres; nos modos documentais, 3.000. A triagem exige contexto completo e bloqueia os casos descritos em [RAG.md](RAG.md). A síntese só chega à revisão se o schema, as citações literais, os números e as referências passarem pelos validadores. Essas verificações não provam implicação semântica ou validade jurídica.

Falhas operacionais não viram ausência de dados. Falha ou cota de geração não vira resposta por regras. Não há retry automático. LangSmith tracing permanece desativado; os registros são locais.

## Execução

```powershell
.venv/Scripts/python.exe -m taxtrace.agente --consulta "cesta basica"
.venv/Scripts/python.exe -m taxtrace.agente --modo gemini --consulta "Leia o artigo 125."
.venv/Scripts/python.exe -m taxtrace.agente --modo rag --consulta "O que o artigo 125 informa sobre as alíquotas do IBS e da CBS?"
```

O comando direto grava um registro de execução e não pausa para decisão. Para o fluxo persistente, use `python -m taxtrace.revisao iniciar --modo rag` com a consulta. Veja [REVISAO.md](REVISAO.md).

`GEMINI_API_KEY` e `GEMINI_MODEL` ficam no `.env`; `GEMINI_RAG_MODEL` é opcional e vazio reutiliza o modelo existente. Não há chave nos prompts ou registros. Use somente dados públicos.

## Evidências e pendências

As entregas documentais anteriores permanecem em `runs/2026-11-06-langgraph-delivery/` e `runs/2026-11-06-review-delivery/`. Elas não mediram geração. Os resultados atuais e as falhas preliminares de RAG estão em [evals/RAG.md](../evals/RAG.md).

Continuam pendentes avaliação independente, revisão fiscal especializada e verificação temporal por dispositivo/data. O acesso público foi preparado e validado separadamente: [publicação](RENDER.md), [evidências](../runs/2026-11-08-render-live/verification.json). Nenhuma execução de desenvolvimento é apresentada como aprovação profissional real.
