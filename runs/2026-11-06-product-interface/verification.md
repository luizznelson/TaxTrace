# Interface organizada por tarefa — validação local

Data: 2026-11-06. Objetivo: explicar a utilidade da aplicação e organizar as funções em Consulta documental, Revisões da sessão e Base e fontes.

## Mudanças verificadas

- Pesquisa por assunto, abertura de artigo e consulta de cClassTrib têm orientações, exemplos e validações próprios.
- Artigos e classificações usam referências explícitas no fluxo local. O planejamento com Gemini permanece uma opção para perguntas por tema.
- A classificação mantém zeros iniciais e rejeita entradas incompletas. O sistema não infere NCM nem enquadramento de produto.
- O histórico aparece em uma área própria, preservando o limite de dez consultas da aba. Revisões podem ser retomadas pelo identificador local.
- Versão, cobertura e datas aparecem na área Base e fontes, com limite explícito de coleta e vigência.
- O leitor permanece acessível na revisão. O formulário continua exigindo confirmação e justificativa para decidir.

## Verificações executadas

- Python: `python -m unittest discover -s tests -q`: 111 casos descobertos, 90 passaram e 21 foram ignorados pelas condições opcionais da suíte. Não se trata de 111 testes executados com sucesso.
- JavaScript: `node --test tests/query-input.test.mjs`: seis testes passaram, cobrindo zeros iniciais, códigos inválidos, artigos de um dígito, entradas malformadas, limite de perguntas e tarefas desconhecidas.
- Ruff: análise e formatação aprovadas; sintaxe JavaScript conferida com `node --check`.
- O teste da página também verifica a entrega do módulo `.mjs` com tipo de conteúdo JavaScript.
- O fluxo de qualidade do repositório inclui os testes JavaScript. Não foi executada uma rodada remota de GitHub Actions nesta etapa.

## Conferência no navegador

- Código inválido `123` mostrou uma orientação e não iniciou consulta.
- `cClassTrib 000001` retornou descrição, percentuais informados e fontes da coleta.
- Artigo `125` retornou o texto e a fonte oficial.
- Consultas persistiram no histórico após recarregar a página.
- Retomar a classificação e editar a consulta recuperou o campo `000001` na tarefa de classificação.
- A troca para inglês na área de fontes preservou a área selecionada e traduziu os controles.
- O leitor de artigo e o formulário apareceram lado a lado no computador. Nenhuma decisão foi enviada durante esta conferência.
- Tela de 390 × 844: navegação e formulário adaptados, largura do documento 375 px, sem rolagem horizontal no cenário observado.
- Nenhum erro capturado no console da sessão.

## Capturas

- [Consulta documental no computador](desktop.jpg)
- [Consulta documental em tela pequena](mobile.jpg)
- [Leitor e revisão](review.jpg)

As capturas usam a coleta local. Não comprovam revisão fiscal, economia de tempo medida, uso por uma equipe ou operação pública. Sem mudança de autenticação, deploy ou nova avaliação do modelo Gemini. Esta conferência não substitui auditoria completa de acessibilidade, segurança ou teste de carga.
