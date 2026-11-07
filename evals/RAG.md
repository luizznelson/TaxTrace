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

## Avaliação adversarial posterior

A etapa seguinte adicionou saídas sinteticamente adulteradas sobre um contexto real salvo, sem novas chamadas de modelo. O conjunto [v1](rag.adversarial.v1.json) e seu resultado preliminar foram preservados. Um gabarito tratava “20 dias” como número ausente, mas a fonte contém o dia 20 de uma data: o problema era semântico, não ausência literal do número.

Na [v2](rag.adversarial.v2.json), esse caso passou a controle semântico, e um caso `202` versus `2023` testa número parcial. São 14 casos: dez rejeições estruturais esperadas, dois controles válidos e dois limites semânticos explícitos. Os dez bloqueios foram observados no [registro final](../runs/rag-adversarial-c7ee6ed3-225a-4c77-9dcf-a6cfe9dd5146/avaliacao.json).

Os dois controles semânticos mostram que números e citações presentes não bastam: uma frase pode contradizer a fonte ou transformar uma data em prazo sem que o validador estrutural resolva a interpretação. Esses casos **não contam como respostas corretas**, nem como prova de robustez semântica. Eles fundamentam a necessidade de revisão e avaliação especializada antes de ampliar o uso.

```powershell
.venv/Scripts/python.exe -m taxtrace.avaliar_adversarial
```

O pacote e a rubrica para revisão declarada estão em [REVISAO_AVALIACAO.md](../docs/REVISAO_AVALIACAO.md). Exportação, testes sintéticos e revisão independente são entregas distintas.
