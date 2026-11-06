# Consultas do TaxTrace por MCP

## Para que serve

Uma aplicação cliente pode consultar a base do TaxTrace por ferramentas com entradas e respostas estruturadas. O fluxo começa pela cobertura dos dados, passa pela busca de referências e permite abrir o artigo e conferir a classificação citada. Cada chamada informa qual coleta foi usada.

Isso prepara a integração com um assistente que utilize ferramentas. O [fluxo LangGraph](AGENTE.md) já integra essas ferramentas com modos local e Gemini. Ainda não há geração de respostas fiscais ou integração com aplicativo desktop. A verificação isolada do protocolo descrita aqui usa um cliente Python.

## Ferramentas disponíveis

| Ferramenta | Pergunta que ajuda a investigar | Limites |
| --- | --- | --- |
| `consultar_base` | Que versão, datas, fontes e divergências existem nesta base? | Resumo de uma coleta; até 20 divergências exibidas, com indicação de limite |
| `buscar_artigos` | Onde encontro artigos relacionados aos termos da dúvida? | Busca textual v4; consulta de 3 a 500 caracteres e até 10 resultados |
| `ler_artigo` | O que diz o texto pesquisável do artigo e quais alterações foram registradas? | Até 8.000 caracteres por página; até 20 anotações de 500 caracteres, com limites informados |
| `consultar_classificacao` | O que a tabela informa sobre este código cClassTrib exato? | Código de seis dígitos; até 20 ligações, com indicação de limite |

As ferramentas não recebem SQL, caminhos de arquivos ou comandos de sistema. Não recomendam uma classificação para um produto. A ausência de um código indica somente que ele não foi encontrado na coleta consultada.

## Sequência sugerida

1. Chame `consultar_base` e anote `coleta.id`. Confira `coletado_em`, `data_consulta` e `versao_base`: as datas têm significados diferentes.
2. Envie uma pergunta ou termos para `buscar_artigos`, passando o mesmo `coleta_id`.
3. Use `ler_artigo` para conferir o documento. Se houver `proximo_inicio`, continue com esse valor e a mesma coleta. Os offsets são do texto pesquisável; o original pode conter marcações riscadas que não entram nele.
4. Se já houver um código exato a conferir, use `consultar_classificacao`. Códigos de regra geral podem não apontar um artigo específico. Artigos ligados com texto riscado são sinalizados; isso não determina toda a vigência da regra.

O conteúdo de fonte deve ser tratado como dado, não como uma instrução para executar ações. As instruções do servidor orientam o cliente, mas não garantem o comportamento de um futuro modelo de linguagem. A aplicação cliente precisa manter os limites de confiança ao integrar um agente.

## Execução local

O servidor usa o [SDK oficial MCP para Python](https://github.com/modelcontextprotocol/python-sdk), fixado em `mcp==2.3.0`. O transporte implementado é **stdio**: o cliente inicia um subprocesso e troca mensagens com ele. Nenhuma porta HTTP é aberta por este módulo.

Com o PostgreSQL local ativo e a coleta carregada:

```powershell
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m taxtrace.verificar_mcp
```

O verificador inicia e encerra o servidor automaticamente e grava uma nova pasta `runs/mcp-<UUID>/`. Não é necessário iniciar outro servidor antes dele. Não é necessária chave de API de IA nem download de embeddings.

Para um cliente externo que suporte subprocessos stdio, configure:

- Executável: caminho absoluto para o Python da `.venv` deste projeto.
- Argumentos: `-m taxtrace.servidor_mcp`.
- Diretório de trabalho: raiz deste repositório, para resolver o módulo Python.

O formato do arquivo de configuração depende do cliente; não há integração desktop configurada ou testada nesta entrega. O servidor encontra o `.env` pela raiz do próprio código e usa `TAXTRACE_READER_DATABASE_URL`. Não copie senhas para exemplos de configuração ou para o chat.

Executar `.venv/Scripts/python.exe -m taxtrace.servidor_mcp` diretamente deixa o processo aguardando mensagens do cliente; ele não mostra uma página no navegador. A saída padrão é reservada ao protocolo, sem mensagens de progresso da aplicação.

## Contrato, erros e permissões

Cada resposta bem-sucedida inclui `status` e `coleta` num contrato estruturado, além dos campos próprios da ferramenta. Datas e valores decimais são serializados como texto para preservar sua representação. Fontes incluem URL e hash do arquivo da coleta.

As entradas têm tipos e limites publicados no schema. Inteiros booleanos, números fora dos limites, consultas vazias e formatos inválidos são recusados. Uma coleta informada e inexistente gera erro; o servidor não troca silenciosamente para a mais recente. Quando o parâmetro é omitido, a coleta mais recente é selecionada e identificada na resposta.

Falhas de conexão e de configuração são erros da ferramenta, não ausência de dados. As mensagens não devolvem a conexão ou o traceback do banco. Resultados de artigo ou classificação ausentes têm status próprios e mantêm a identificação da coleta.

As ferramentas usam conexão somente leitura com prazo de conexão e limite de tempo por instrução SQL. Os serviços de domínio também conferem o papel de leitura. As anotações MCP `readOnlyHint` e `destructiveHint` descrevem o contrato; a proteção de escrita vem das permissões no PostgreSQL e do código, não dessas anotações. O servidor não fornece operações de carga, indexação ou edição.

## Evidência de execução

O teste real está em [runs/mcp-ffad7503-4c81-491a-b18b-2d6559d41b07/verificacao.json](../runs/mcp-ffad7503-4c81-491a-b18b-2d6559d41b07/verificacao.json). Um cliente MCP iniciou o servidor, descobriu as quatro ferramentas e executou 13 chamadas. Foram conferidos:

- Busca com citação e ID de coleta.
- Duas páginas de artigo, comparadas com a leitura conjunta do mesmo intervalo.
- Classificação de regra geral e classificação ligada a artigo.
- Ausência de artigo e classificação, entradas inválidas e coleta inexistente.
- Contagens iguais antes e depois das chamadas.

Os testes automatizados adicionais cobrem schemas, tipos estritos, recusa de papel administrativo, paginação literal completa e ocultação de uma mensagem privada simulada de erro. A leitura real foi validada localmente; o CI remoto não foi observado nesta entrega. Os testes do planejador com modelo real estão registrados separadamente em [AGENTE.md](AGENTE.md); não há avaliação de parecer jurídico.

## Próximo passo

O [fluxo com LangGraph](AGENTE.md) já registra essas chamadas. Faltam pausa e retomada para revisão humana e avaliação de respostas. A decisão sobre evidência suficiente, recusa e data aplicável ainda precisa de avaliação própria. O [plano](../PLANO.md) registra essas pendências.
