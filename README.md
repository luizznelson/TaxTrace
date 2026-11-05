# TaxTrace

Agente de IA com servidor MCP para consultar a Reforma Tributária do consumo (IBS e CBS) com **citação da fonte oficial**, **controle de vigência** e **recusa quando não há evidência**.

> Status: em planejamento. Ainda não há funcionalidade implementada; veja o [plano](PLANO.md).

## Problema

Desde 2026 as empresas convivem com IBS e CBS (LC 214/2025), e as regras de emissão e validação dos documentos fiscais mudam por atos da Receita Federal e do Comitê Gestor do IBS. Classificar produtos e saber o que vale hoje exige consultar muitas fontes.

## Objetivo

- Responder perguntas com o trecho oficial citado e a data de vigência.
- Recusar o que a base não sustenta, sem inventar orientação tributária.
- Expor as consultas como ferramentas MCP e orquestrá-las com um agente (LangGraph).
- Medir a qualidade com um conjunto de perguntas com gabarito.

## Aviso

Apoio à consulta, não consultoria tributária. Confira sempre a fonte oficial.

English: [README.en.md](README.en.md)
