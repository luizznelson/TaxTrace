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
- Login de consulta somente leitura e banco de testes separado do banco de desenvolvimento.

**Ainda em desenvolvimento:** embeddings, RAG, ferramentas MCP, agente LangGraph, avaliação de respostas com gabarito revisado e interface. A avaliação inicial da recuperação de artigos já está disponível. A extensão pgvector está disponível no banco, mas a busca atual não usa vetores ou modelos de IA.

## Perguntas que a primeira versão ajuda a investigar

- Quais artigos mencionam os termos que preciso conferir?
- A qual artigo uma classificação da tabela se refere? Essa ligação já está armazenada, mas ainda não tem ferramenta própria de consulta.
- Qual fonte, versão e data sustentam o resultado encontrado?
- Há divergências entre as tabelas coletadas que exigem revisão?

## Evidência da execução local

A [verificação registrada](runs/2026-11-06-local-database/verification.json) carregou 580 artigos, 170 classificações, 169 ligações e 10.515 NCM. Três divergências entre tabelas foram preservadas, sem completar informações por suposição.

A captura ocorreu em **05/11/2026**, com a API consultada para **01/01/2027**, base **V0066**. Essas datas têm significados diferentes; nenhuma delas, isoladamente, comprova a vigência jurídica de uma conclusão.

O registro inclui consultas bem-sucedidas e sem resultado, conferência das permissões e recusa de uma carga repetida. É uma verificação local, não uma execução comprovada do CI remoto.

## Como executar no Windows

Pré-requisitos: Python 3.14 e Docker Desktop ativo. Execute na pasta do projeto.

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt -r requirements-dev.txt
Copy-Item .env.example .env
```

Se o `.env` já existir, preserve-o. Edite esse arquivo e substitua as três senhas de exemplo, mantendo cada senha correspondente na respectiva URL. Não publique o arquivo. Não é necessária chave de IA nesta etapa.

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

O [conjunto de avaliação](evals/README.md) contém perguntas, artigos esperados e fragmentos da fonte. Na primeira medição, o artigo de referência apareceu entre os cinco primeiros em **14 de 20 consultas**. Duas consultas de controle foram avaliadas separadamente. O resultado evidencia limitações em perguntas completas e variações de escrita; não mede precisão jurídica.

```powershell
.venv/Scripts/python.exe -m taxtrace.avaliacao --limite 5
```

Cada execução gera um registro novo em `runs/`, com resultados por caso, identificação do código, gabarito e coleta. Consulte a metodologia e os resultados completos antes de interpretar o percentual.

A versão experimental `v2` acrescenta normalização de acentos e tratamento de perguntas. No mesmo conjunto, recuperou 16 de 20 referências, mas apresentou quatro regressões. **A versão v1 permanece como padrão.** A [comparação completa](evals/README.md#experimento-de-busca-v2--comparação-preservada) explica ganhos, perdas e limites.

Para testar a v2 em um banco já carregado:

```powershell
.venv/Scripts/python.exe -m taxtrace.banco --somente-esquema
.venv/Scripts/python.exe -m taxtrace.busca --metodo v2 --consulta "cesta basica"
.venv/Scripts/python.exe -m taxtrace.avaliacao --metodo v2
```

## Como conferir a qualidade

```powershell
$env:TAXTRACE_TEST_DATABASE='1'
.venv/Scripts/python.exe -m unittest discover -s tests -q
.venv/Scripts/ruff.exe check .
.venv/Scripts/ruff.exe format --check .
```

Os testes de banco exigem a habilitação explícita acima e uma conexão local para `taxtrace_test`, na porta 15434, com usuário próprio. Não usam a conexão de desenvolvimento como alternativa. Os testes de integração desfazem suas transações; não executam limpeza das tabelas de desenvolvimento. Sem a habilitação, esses testes são ignorados. Testes que dependem da coleta real também são ignorados quando os arquivos locais não existem.

## Organização

| Local | Responsabilidade |
| --- | --- |
| `taxtrace/coleta.py`, `integridade.py` | Captura e conferência dos arquivos contra o manifesto |
| `taxtrace/lei.py`, `tabelas.py`, `ligacao.py` | Interpretação e ligação das fontes |
| `taxtrace/schema.sql`, `banco.py`, `conexao.py` | Persistência, transações e conexões separadas |
| `taxtrace/documentos.py`, `consulta.py`, `busca.py` | Texto pesquisável e busca com citações |
| `tests/` | Verificações automatizadas e isolamento do banco de testes |
| `evals/`, `taxtrace/avaliacao.py` | Gabaritos, metodologia e avaliação da recuperação |
| `runs/` | Registros públicos de validação, sem credenciais |
| `PLANO.md` | Decisões, fontes e entregas pendentes |

## Limites de interpretação

A busca atual depende dos termos digitados e pode deixar de encontrar trechos relevantes. Um resultado vazio significa apenas que essa busca não encontrou correspondência. O ranking não é uma medida de confiança jurídica.

O índice remove os trechos marcados como riscados, mas isso não substitui análise de vigência. O original e suas marcações permanecem armazenados. Os hashes verificam correspondência ao manifesto; não constituem assinatura digital da fonte. As conexões estão restritas ao ambiente local nesta etapa; Neon ficará para a publicação.

**Apoio à consulta, não parecer tributário.** Confira a fonte oficial antes de tomar uma decisão.
