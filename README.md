# TaxTrace

Consulta rastreável de fontes da Reforma Tributária do consumo: encontre o artigo, confira sua origem e identifique qual versão dos dados foi utilizada.

English: [README.en.md](README.en.md)

## O problema que orienta o projeto

Uma equipe fiscal precisa conferir a base normativa de uma classificação tributária. A informação está distribuída entre o texto legal e tabelas estruturadas; encontrar um trecho sem registrar a fonte e a versão dificulta revisar a conclusão depois.

O TaxTrace organiza essas fontes para apoiar essa conferência. A proposta é reduzir a procura manual e tornar cada consulta verificável. Ainda não medimos economia de tempo nem validamos o uso por uma equipe fiscal.

## O que funciona hoje

- Coleta de fontes oficiais com URL, data, tamanho e hash dos arquivos.
- Leitura da LC 214/2025 por artigo, preservando o registro de alterações e texto riscado.
- Organização das tabelas da API da Receita e ligação das classificações aos artigos citados.
- Carga transacional em PostgreSQL local, vinculada à versão da coleta; duplicatas são recusadas.
- Busca textual em português, com trechos literais, artigo, URL e identificação da coleta.
- Recuperação semântica experimental: embeddings locais, trechos por artigo e vetores no pgvector.
- Servidor MCP local com quatro ferramentas de consulta, fontes e coleta identificada.
- **RAG documental:** explicação com citações clicáveis, recusa quando o contexto não atende aos critérios e resposta vinculada à revisão. Veja [funcionamento e limites](docs/RAG.md).
- Login de consulta somente leitura e banco de testes separado do banco de desenvolvimento.

**Pendente:** autenticação para publicação multiusuário, validação temporal por dispositivo/data e avaliação independente de respostas com revisão especializada. A avaliação inicial da recuperação de artigos já está disponível. A busca textual v4 permanece como padrão; a alternativa semântica é selecionada explicitamente.

## Perguntas que a primeira versão ajuda a investigar

- Quais artigos mencionam os termos que preciso conferir?
- A qual artigo uma classificação da tabela se refere? Consulte o código no modo cClassTrib e confira sua fundamentação recuperada.
- Qual fonte, versão e data sustentam o resultado encontrado?
- Há divergências entre as tabelas coletadas que exigem revisão?

## Evidência da execução local

A [verificação registrada](runs/2026-11-06-local-database/verification.json) carregou 580 artigos, 170 classificações, 169 ligações e 10.515 NCM. Três divergências entre tabelas foram preservadas, sem completar informações por suposição.

A captura ocorreu em **05/11/2026**, com a API consultada para **01/01/2027**, base **V0066**. Essas datas têm significados diferentes; nenhuma delas, isoladamente, comprova a vigência jurídica de uma conclusão.

O registro inclui consultas bem-sucedidas e sem resultado, conferência das permissões e recusa de uma carga repetida. É uma verificação local, não uma execução comprovada do CI remoto.

## Resposta com fontes

Na interface, escolha **Pesquisar um tema → Resposta com fontes · RAG**. Exemplo: “O que o artigo 125 informa sobre as alíquotas do IBS e da CBS?”. Cada afirmação traz uma citação para abrir o trecho de apoio. A resposta é um rascunho documental, com revisão declarada; não certifica enquadramento ou vigência. Os [resultados de desenvolvimento](evals/RAG.md) distinguem triagem, geração e suas limitações.

## Como executar no Windows

Pré-requisitos: Python 3.14 e Docker Desktop ativo. Execute na pasta do projeto.

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt -r requirements-dev.txt
Copy-Item .env.example .env
```

Se o `.env` já existir, preserve-o. Edite esse arquivo e substitua as três senhas de exemplo, mantendo cada senha correspondente na respectiva URL. Não publique o arquivo. O modo direto não exige chave. Planejamento com Gemini e síntese RAG usam a chave opcional configurada no `.env`.

```powershell
docker compose --profile tests up -d --wait
```

Os bancos aceitam conexões apenas pelo próprio computador: desenvolvimento na porta 15433 e testes na 15434. O volume de desenvolvimento é persistente; o banco de testes usa armazenamento temporário. Não use `down -v` se quiser preservar os dados de desenvolvimento.

Para obter uma nova coleta e carregá-la:

```powershell
.venv/Scripts/python.exe -m taxtrace.coleta --data 2027-01-01
.venv/Scripts/python.exe -m taxtrace.banco
.venv/Scripts/python.exe -m taxtrace.busca --consulta "credito presumido" --limite 3
```

A data acima reproduz o recorte usado nesta etapa; não representa automaticamente a data atual. Se o Planalto interromper o download, o coletor aceita `--lei-arquivo` com o HTML oficial salvo localmente. Os arquivos brutos ficam fora do Git. Consulte o [plano](PLANO.md) para fontes, achados e pendências de termos de uso.

## Como medir a busca

A [avaliação da busca](evals/COMPARACAO.md) compara as versões com gabaritos e resultados por caso. A busca atual mantém os resultados originais e preenche as vagas com candidatos da busca ampliada:

- Conjunto original: **19 de 20 referências entre os cinco primeiros** (antes: 14 de 20).
- Perguntas adicionais: **11 de 12 referências** (antes: 6 de 12).
- Nenhum acerto da versão original foi perdido nas duas comparações.

Esses números são de desenvolvimento, sem revisão fiscal independente. Não medem precisão jurídica. Dois controles sintéticos por conjunto ficam fora dos percentuais; as falhas também estão publicadas.

```powershell
.venv/Scripts/python.exe -m taxtrace.avaliacao
.venv/Scripts/python.exe -m taxtrace.avaliacao --casos evals/recuperacao.adicional.v1.json
```

Cada execução grava um novo registro em `runs/`, identificando código, gabarito, coleta, artigos e origem dos candidatos. A versão v4 é o padrão; `--metodo v1` reproduz a referência anterior. As versões v2 e v3 permanecem experimentais. Para atualizar um banco já carregado, use `python -m taxtrace.banco --somente-esquema` com o Python da `.venv`.

## Recuperação semântica experimental

O modelo de embeddings roda localmente, sem chave de API, e indexou **990 trechos de 580 artigos**. Na avaliação, recuperou 12/20 e 9/12 referências, abaixo da busca textual (19/20 e 11/12). Também retornou vizinhos para termos inexistentes; não há recusa semântica calibrada. Por isso, a busca padrão foi preservada.

Consulte [instalação, comparação e limites](evals/SEMANTICA.md) para testar com `--metodo semantica`. Os arquivos do modelo ficam fora do Git e seu download é explícito. Embeddings são recuperação de informação; a aplicação ainda não gera respostas por IA.

## Qualidade dos trechos e busca combinada

O [experimento híbrido](evals/HIBRIDA.md) combina candidatos textuais e semânticos, mas ficou abaixo da busca padrão: 16/20 e 9/12 referências encontradas. A avaliação agora também confere a literalidade dos recortes na fonte e a presença da frase de referência no trecho exibido. Na busca semântica, três consultas encontraram o artigo esperado sem mostrar essa frase.

O comando `python -m taxtrace.avaliacao` com o Python da `.venv` gera esses novos indicadores. A presença da frase é uma verificação textual limitada; a suficiência jurídica para uma resposta continua sem avaliação. Use `--metodo hibrida` apenas para explorar o experimento, com o índice semântico já preparado.

## Ferramentas para um assistente

O [servidor MCP](docs/MCP.md) permite que um cliente consulte a base, busque artigos, leia o texto por partes e confira um cClassTrib exato. As quatro ferramentas são somente leitura e informam fonte e versão da coleta. Nenhuma decide o enquadramento de um produto.

```powershell
.venv/Scripts/python.exe -m taxtrace.verificar_mcp
```

O comando inicia um cliente e um servidor locais, confere as chamadas e grava evidências em `runs/`. O fluxo LangGraph já usa essas ferramentas; não é necessária chave de modelo para testar o MCP isolado.

## Fluxo LangGraph com rastro das chamadas

O [fluxo de consulta](docs/AGENTE.md) planeja uma ação limitada, consulta a base por MCP, recupera referências e confere a coleta e as citações. O modo local usa regras; o modo Gemini usa IA apenas no planejamento. Foram executados testes reais de ambos, com registros em `runs/`.

```powershell
.venv/Scripts/python.exe -m taxtrace.agente --consulta "Leia o artigo 125."
.venv/Scripts/python.exe -m taxtrace.agente --modo gemini --consulta "Qual artigo trata da cesta basica?"
```

O modo Gemini exige a chave no `.env`. O resultado é um conjunto de evidências para revisão, com no máximo três chamadas MCP; ainda não há parecer fiscal ou memória de conversa. A pausa e a retomada já estão disponíveis no módulo de revisão documental.

## Revisão com pausa e retomada

O [fluxo de revisão](docs/REVISAO.md) salva o estado em SQLite, permite inspecionar as evidências e retoma com uma decisão declarada de aprovação ou rejeição. A decisão exige o hash do conjunto revisado; revisão encerrada não aceita outra decisão. A retomada não repete chamadas MCP ou Gemini.

```powershell
.venv/Scripts/python.exe -m taxtrace.revisao iniciar --consulta "Leia o artigo 125."
.venv/Scripts/python.exe -m taxtrace.verificar_revisao
```

O segundo comando é uma demonstração automatizada identificada, não revisão humana real. Checkpoints privados ficam fora do Git; os eventos publicáveis ficam em `runs/`. A identidade do revisor é autodeclarada e a decisão documental não valida um parecer fiscal.

## Aplicação local

A [interface do TaxTrace](docs/INTERFACE.md) reúne **pesquisa, leitura das fontes e revisão documental** em uma bancada: lista selecionável de resultados, leitor ao lado e decisão com a fonte acessível. A navegação separa Consulta documental, Revisões da sessão e Base e fontes. Há entradas específicas para tema, número de artigo e cClassTrib, histórico da aba e exportação do registro. Português e inglês disponíveis; os documentos oficiais preservam o texto original.

```powershell
.venv/Scripts/python.exe -m taxtrace.web
```

Abra [a aplicação local](http://127.0.0.1:8015/). A base precisa estar ativa. Esta etapa não publica o app nem oferece autenticação multiusuário.

## Como conferir a qualidade

```powershell
$env:TAXTRACE_TEST_DATABASE='1'
.venv/Scripts/python.exe -m unittest discover -s tests -q
node --test tests/query-input.test.mjs
.venv/Scripts/ruff.exe check .
.venv/Scripts/ruff.exe format --check .
```

Os testes de banco exigem a habilitação explícita acima e uma conexão local para `taxtrace_test`, na porta 15434, com usuário próprio. Não usam a conexão de desenvolvimento como alternativa. Os testes de integração desfazem suas transações; não executam limpeza das tabelas de desenvolvimento. Sem a habilitação, esses testes são ignorados. Testes que dependem da coleta real também são ignorados quando os arquivos locais não existem.

## Organização

| Local                                                          | Responsabilidade                                                      |
| -------------------------------------------------------------- | --------------------------------------------------------------------- |
| `taxtrace/coleta.py`, `integridade.py`                         | Captura e conferência dos arquivos contra o manifesto                 |
| `taxtrace/lei.py`, `tabelas.py`, `ligacao.py`                  | Interpretação e ligação das fontes                                    |
| `taxtrace/schema.sql`, `banco.py`, `conexao.py`                | Persistência, transações e conexões separadas                         |
| `taxtrace/documentos.py`, `consulta.py`, `busca.py`            | Texto pesquisável e busca com citações                                |
| `taxtrace/encoder.py`, `vetores.py`                            | Modelo local fixado, fragmentação e índice vetorial experimental      |
| `taxtrace/consultas.py`, `servidor_mcp.py`, `verificar_mcp.py` | Consultas de domínio, ferramentas MCP e verificação real do protocolo |
| `tests/`                                                       | Verificações automatizadas e isolamento do banco de testes            |
| `evals/`, `taxtrace/avaliacao.py`                              | Gabaritos, metodologia e avaliação da recuperação                     |
| `runs/`                                                        | Registros públicos de validação, sem credenciais                      |
| `PLANO.md`                                                     | Decisões, fontes e entregas pendentes                                 |

## Operação e evidências

A aplicação foi construída e executada no Docker/Linux com PostgreSQL real: **193 testes aprovados e três desativados sem a coleta oficial**. Checkpoints, eventos, isolamento entre navegadores e permissões do papel de aplicação foram exercitados. A [evidência completa](runs/2026-11-07-neon-runtime-preparation/verification.json) registra também falhas preliminares e a correção da limpeza de testes. Não houve deploy ou migração automática do histórico.

A preparação autorizada no Neon também foi concluída: **580 artigos, 170 classificações, 10.515 NCM e sete arquivos preservados**, com acesso de leitura e estado separados. A revisão técnica foi retomada em outro processo Linux, sem chamadas a modelos e sem aprovação humana. [Evidências no destino real](runs/2026-11-08-neon-provision/README.md).

- [Publicação no Render Free](docs/RENDER.md): configuração preparada, cookies HTTPS, limites de uso e variáveis privadas. [Serviço publicado](https://taxtrace.onrender.com/) com consulta RAG real e revisão persistida verificadas; conta de revisor pendente. [Evidências](runs/2026-11-08-render-live/verification.json).
- [Preparação do Neon e das fontes](docs/NEON.md): configuração privada, política TLS e originais preservados no banco.
- [Docker](docs/DOCKER.md): execução local com volumes privados e ambiente descartável de integração.
- [Persistência](docs/PERSISTENCIA.md): SQLite como padrão; checkpoints, eventos e vínculos PostgreSQL opcionais.
- [Acesso do revisor](docs/AUTENTICACAO.md) e [autorização dos registros](docs/AUTORIZACAO.md): decisões com login; leitura pela sessão proprietária ou conta administrativa. A credencial também pode vir da configuração privada.
- [Diagnósticos e avaliação automática](docs/OPERACAO.md): processo ativo, base disponível e relatórios de desenvolvimento.
- [Casos adversariais](evals/RAG.md) e [revisão de qualidade](docs/REVISAO_AVALIACAO.md): 12 casos ainda aguardam avaliação especializada; exportar o pacote não comprova revisão independente.

## Limites de interpretação

A busca atual depende dos termos digitados e pode deixar de encontrar trechos relevantes. Um resultado vazio significa apenas que essa busca não encontrou correspondência. O ranking não é uma medida de confiança jurídica.

O índice remove os trechos marcados como riscados, mas isso não substitui análise de vigência. O original e suas marcações permanecem armazenados. Os hashes verificam correspondência ao manifesto; não constituem assinatura digital da fonte. O uso local continua como padrão. A conexão Neon é opcional, exige destino fixado e TLS verificado e foi validada contra o projeto real em 08/11/2026; a publicação permanece pendente.

**Apoio à consulta, não parecer tributário.** Confira a fonte oficial antes de tomar uma decisão.
