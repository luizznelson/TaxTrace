# Estudo de caso — da pergunta à evidência

[Visão geral](../README.md) · [Arquitetura](architecture.md) · [Qualidade](quality.md) · [Documentação](README.md)

## A tarefa de negócio

**Cenário ilustrativo, não relato de cliente:** uma pessoa que prepara uma análise
tributária precisa conferir uma informação de IBS/CBS. Encontrar uma frase não
resolve toda a tarefa: é preciso saber de qual fonte veio, qual recorte foi
consultado e o que foi efetivamente revisado.

O TaxTrace foi construído para reunir essa conferência em uma experiência:
perguntar, inspecionar o documento, manter a origem acessível e registrar uma
decisão justificada. Não há pesquisa com usuários ou medição de economia de tempo;
o público e o benefício são propostos, não resultados comerciais comprovados.

## Perguntas que orientam a experiência

| Pergunta da pessoa | Entrega implementada | O que continua dependendo de análise |
| --- | --- | --- |
| Onde a lei trata deste assunto? | Busca textual com artigo e trechos de origem | Pertinência e suficiência dos dispositivos |
| O que este artigo informa? | Síntese citada, quando os critérios técnicos permitem | Fidelidade semântica, condicionantes e aplicabilidade |
| Qual é a descrição deste cClassTrib? | Consulta exata da tabela, preservando o código | Escolha do código para um produto ou operação |
| Como explicar o que foi conferido? | Coleta, rastro, decisão com motivo e exportação | Responsabilidade e qualificação do revisor |

## Uma jornada concreta

A pergunta demonstrada é **“O que o artigo 125 informa sobre as alíquotas do IBS
e da CBS?”**. O modo RAG faz o seguinte:

1. Identifica o artigo por regras e consulta a base por ferramentas MCP de leitura.
2. Confere coleta, fonte e presença do documento completo permitido.
3. Envia o contexto público identificado ao Gemini para síntese estruturada.
4. Confere citações, referências e números antes de apresentar um rascunho.
5. Mantém o artigo integral e a fonte acessíveis. O usuário pode exportar; uma
   conta autorizada pode registrar uma decisão vinculada ao conjunto.

A [demonstração](DEMONSTRACAO.md) e o [teste hospedado](../runs/2026-11-08-reviewer-hosted/README.md)
mostram essa jornada. A decisão gravada é uma rejeição de teste operacional,
executada pelo assistente com autorização do titular da sessão e identificada
no motivo. Não comprova revisão fiscal humana ou qualidade geral da resposta.

## Fontes e recorte

| Fonte | Papel no projeto |
| --- | --- |
| [LC 214/2025 no Planalto](https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214.htm) | Texto por artigo, alterações e marcações de redação |
| [API pública da calculadora da Receita Federal](https://piloto-cbs.tributos.gov.br/servico/calculadora-consumo/api) | Versão, classificações tributárias, ligações e catálogo NCM |

A captura de referência ocorreu em **05/11/2026**. A API foi consultada para
**01/01/2027**, base **V0066**, ambiente informado pela fonte `apr`. Esse parâmetro
é parte do recorte registrado, não a data atual nem prova de vigência.

Foram preservados 580 artigos, 170 classificações, 169 ligações, 10.515 NCM e três
divergências. As divergências não foram completadas por suposição. Seis arquivos
originais e o manifesto estão preservados no Neon. Os hashes verificam os bytes
contra o manifesto; não são assinatura das fontes. [Carga inicial](../runs/2026-11-06-local-database/verification.json)
e [verificação remota](../runs/2026-11-08-neon-provision/README.md).

## Decisões que mudaram o resultado

- **Manter a busca textual:** a v4 encontrou mais referências nos conjuntos conhecidos
  que embeddings e RRF. A escolha foi guiada pela comparação, não pela quantidade
  de tecnologias presentes. [Método](../evals/COMPARACAO.md).
- **Não entregar qualquer texto do modelo:** schema e citações são conferidos; falhas
  não viram resposta válida nem ausência de documentos. Isso ainda não prova
  correção semântica. [RAG](RAG.md).
- **Separar leitura de decisão:** visitantes consultam; a conta de revisor decide.
  O estado da consulta e a decisão têm persistência e origem identificadas.
- **Preservar o recorte:** não trocar silenciosamente a fonte por uma versão nova
  durante a revisão de um conjunto já registrado.

## Resultado e próximos critérios de validação

O resultado comprovado é técnico: aplicação publicada, busca comparada, uma
jornada RAG real e revisão rastreável. A comparação de recuperação tem 19/20 e
11/12 referências no top 5; não mede precisão jurídica ou utilidade em uma equipe.

Para avaliar valor operacional, um estudo futuro precisa de tarefas e documentos
reservados, revisores qualificados e medidas de correções necessárias, afirmações
sem apoio e tempo de conferência. Não há resultados dessas medidas nesta entrega.
Validação temporal e avaliação independente continuam explícitas no [plano](../PLANO.md).
