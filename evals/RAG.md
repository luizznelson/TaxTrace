# Avaliação do RAG documental

O gabarito [rag.v1.json](rag.v1.json) foi escrito antes das chamadas reais desta etapa e fixa a coleta e a fonte do corpus. São 12 casos: três positivos para geração e nove recusas esperadas. É um **conjunto de desenvolvimento**, criado e consultado durante a implementação, sem independência de autoria ou revisão fiscal.

## O que é medido

1. **Triagem técnica:** elegibilidade esperada e motivo da recusa, com ferramentas MCP e banco reais.
2. **Estrutura e rastreabilidade:** schema, citações literais, referências e números contra o contexto. Testes adversariais usam respostas sintéticas identificadas.
3. **Gabarito mínimo de geração:** status de resposta, referências esperadas e presença de conceitos lexicais. Não substitui avaliação semântica ou julgamento profissional.
4. **Revisão persistente:** hash da resposta/contexto/citações, pausa e retomada sem repetir modelo ou ferramentas.

Sem `--ao-vivo`, o avaliador não chama o Gemini: quando o contexto é elegível, interrompe a síntese com o código explícito `avaliacao_somente_triagem_sem_modelo`. Essa interrupção não é contabilizada como recusa correta do modelo nem como resposta gerada.

## Resultados desta etapa

- [Triagem sem modelo](../runs/rag-833e51f9-97d0-49ab-9bae-b4cf25984c31/avaliacao.json): 12/12 critérios atendidos; nenhuma geração.
- [Primeira rodada real](../runs/rag-4f177db8-5b2a-4dad-b83c-c1d4a29c20af/avaliacao.json): 12/12 triagens; 2/3 gabaritos mínimos de geração. Uma resposta foi bloqueada por validação de referência com ordinal, como `8º`.
- [Rodada real após correção](../runs/rag-db4649cc-4f9e-45d4-8c68-eacf418d08c1/avaliacao.json): 12/12 triagens; 3/3 gabaritos mínimos de geração. A correção tem teste de regressão; a repetição após ajuste **não é teste independente**.

Cada arquivo preserva pergunta, estado, contexto, fontes, resposta admitida ou código de falha, modelo/uso quando disponível, hashes do código e do gabarito. Respostas bloqueadas não são contabilizadas como respostas corretas. Os registros preliminares permanecem no repositório.

## Reproduzir

```powershell
# Triagem com dados e ferramentas reais, sem chamada de modelo
.venv/Scripts/python.exe -m taxtrace.avaliar_rag
# Até três tentativas reais; consome a cota da conta configurada
.venv/Scripts/python.exe -m taxtrace.avaliar_rag --ao-vivo --limite-geracoes 3
```

Os testes de CI não usam chaves e não chamam o provedor. Configuração ausente, falha ou limite de API não provam ausência de dados. O resumo conta gabaritos mínimos, não acurácia jurídica. Três respostas positivas e nove recusas não demonstram cobertura ampla de perguntas, robustez geral a injeção ou validade atual de uma regra.

A etapa de avaliação independente prevista no plano permanece aberta. Deve usar casos congelados não utilizados em ajustes, revisão de especialista e análise de afirmações sem apoio, condicionantes omitidas, citações insuficientes e recusas indevidas.
