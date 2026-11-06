# Avaliação da recuperação de artigos

**Estado atual:** a busca padrão é a v4 conservadora. A [avaliação semântica](SEMANTICA.md) está disponível como experimento separado, com resultados inferiores à textual. Veja a [comparação atual](COMPARACAO.md). As medições v1/v2 abaixo são registros históricos das etapas anteriores.

## Decisão que esta avaliação apoia

Antes de gerar respostas com IA, precisamos saber se a busca consegue localizar o artigo de referência. Uma resposta bem escrita não resolve a ausência do documento necessário. Esta medição cria uma base de comparação para melhorias da busca e, depois, embeddings.

## Como o gabarito foi construído

O arquivo [recuperacao.v1.json](recuperacao.v1.json) reúne 22 casos: nove temas com uma consulta curta e uma pergunta completa por tema, duas variações de escrita sobre cesta básica e dois controles sintéticos com termo inexistente. Um controle inclui texto semelhante a SQL como entrada literal; não é um teste abrangente de segurança.

Os temas foram escolhidos pela leitura da cópia oficial já coletada, antes de executar o ranking deste conjunto. Cada caso positivo indica um artigo de referência e um fragmento literal que justifica sua inclusão. As referências incluem instituição dos tributos, incidência, fato gerador, plataformas digitais, extinção de débitos, créditos, cesta básica, profissionais e Imposto Seletivo.

O avaliador confere os fragmentos no texto pesquisável do banco. O manifesto e o arquivo-fonte estão identificados por SHA-256. Se a coleta não for a esperada, ou o fragmento não conferir, a execução é interrompida. O fragmento comprova a presença textual no artigo; não constitui resposta fiscal revisada por especialista.

É um **conjunto de desenvolvimento**, elaborado com acesso aos documentos. Não é um teste independente, uma pesquisa com usuários nem uma amostra representativa do mercado. As perguntas não têm validação de profissional tributário. Não se deve escolher o artigo esperado apenas porque a busca o retornou; futuras mudanças de gabarito precisam registrar sua justificativa.

## Reprodução

Com o banco local carregado e o `.env` configurado, execute da raiz do repositório:

```powershell
.venv/Scripts/python.exe -m taxtrace.avaliacao --metodo v1 --limite 5
```

O comando usa o login somente leitura, mantém a mesma coleta durante toda a execução e grava um novo `runs/recuperacao-<UUID>/resultado.json`. Não sobrescreve execuções anteriores. `--casos` permite selecionar outro arquivo de gabarito; `--limite` aceita de 1 a 20.

Cada registro contém consultas, referências esperadas, artigos encontrados em ordem, métricas, tempo local por consulta, versão do PostgreSQL e Python, coleta, hash do conjunto, hashes do avaliador e da busca, commit de origem e indicação de alterações locais. Os dados são públicos; nenhuma conexão ou senha é gravada.

Falha de conexão, evidência inconsistente ou citação divergente encerra a avaliação com código 1, sem converter o problema em uma consulta vazia. Código 0 significa que a medição terminou; não significa que a busca atingiu um critério de qualidade. Ainda não definimos uma meta de aceitação para o produto.

## Primeira medição — 06/11/2026

Resultado da [execução completa](../runs/recuperacao-137a3c80-cb35-4071-93b7-1afbb05deec1/resultado.json), com cinco resultados por consulta:

| Tipo de consulta | Casos com artigo | Artigo esperado entre os cinco primeiros |
| --- | ---: | ---: |
| Termos curtos | 9 | 8 de 9 (88,9%) |
| Perguntas completas | 9 | 5 de 9 (55,6%) |
| Variações de escrita | 2 | 1 de 2 (50,0%) |
| Total positivo | 20 | 14 de 20 (70,0%) |

Os dois controles não retornaram resultados e ficam fora dos 70%. A [execução preliminar](../runs/recuperacao-0d4cb85a-4cca-4417-8d21-43c9aad08529/resultado.json), anterior à inclusão de métricas por categoria, foi preservada separadamente. Ambas usaram a mesma busca e o mesmo conjunto.

O MRR@5 foi **0,495**: ele atribui 1 quando a primeira referência esperada está no primeiro lugar, 1/2 no segundo, até 1/5 no quinto; ausência recebe zero. O Hit@5 mede a proporção de consultas com pelo menos uma referência esperada. O recall de referências mede a fração das referências do gabarito recuperadas; como esta versão tem uma referência por caso, coincide com o Hit@5.

## Falhas preservadas e próximos experimentos

Seis casos não localizaram a referência entre os cinco primeiros: a pergunta sobre instituição dos tributos, as duas consultas de extinção de débitos, a pergunta sobre profissionais, a pergunta sobre instituição do Imposto Seletivo e “cesta basica” sem acento. Alguns retornaram outros artigos; outros não retornaram nada.

Próximos experimentos: tratamento de acentos, processamento das perguntas completas e comparação com recuperação por embeddings. Cada mudança deve ser medida contra esta versão, preservando falhas e resultados anteriores. Como o conjunto já é conhecido durante o desenvolvimento, também será necessário um conjunto separado de validação antes de comunicar qualidade fora desses casos.

## O que estes números não demonstram

- Não medem correção jurídica, vigência, resposta de LLM nem economia de tempo.
- Não comprovam que o trecho exibido de até 1.000 caracteres sustenta a resposta: a métrica atual verifica o artigo recuperado, não o recorte apresentado.
- Outros artigos retornados podem ser pertinentes. O gabarito é mínimo e não exaustivo; não calculamos precisão.
- Controles sintéticos não medem recusa semântica para perguntas reais fora de escopo.
- As variações compartilham temas; não são observações independentes. Não estimamos significância estatística.
- Tempos locais não representam desempenho sob carga nem latência de uma aplicação hospedada.


## Experimento de busca v2 — comparação preservada

A v2 normaliza acentos com um dicionário `unaccent` antes da redução de palavras em português. Remove uma lista curta de palavras de formulação da pergunta, preservando negações, datas e números. Ela permite correspondências parciais com pelo menos 60% dos lexemas da consulta; isso amplia candidatos e também pode trazer artigos pouco úteis.

O índice experimental pondera os primeiros 600 caracteres do artigo e seu texto completo. O ranking prioriza menos termos ausentes e depois pontuação textual normalizada pelo tamanho. Esses são critérios heurísticos de desenvolvimento, não regras fiscais. Os textos originais não são alterados. A implementação se baseia nos recursos de [busca textual do PostgreSQL](https://www.postgresql.org/docs/17/textsearch-controls.html) e [dicionários](https://www.postgresql.org/docs/17/textsearch-dictionaries.html).

Atualize o esquema existente e compare explicitamente as versões:

```powershell
.venv/Scripts/python.exe -m taxtrace.banco --somente-esquema
.venv/Scripts/python.exe -m taxtrace.avaliacao --metodo v1
.venv/Scripts/python.exe -m taxtrace.avaliacao --metodo v2
.venv/Scripts/python.exe -m taxtrace.busca --metodo v2 --consulta "cesta basica"
```

A atualização é aditiva e transacional: mantém a coleta, o texto original e o índice v1. Não exige recarregar os arquivos. Em novas instalações, a carga normal já cria os dois índices. As consultas continuam usando o login somente leitura.

| Medida | v1 (padrão) | v2 (experimental) |
| --- | ---: | ---: |
| Referência entre os cinco primeiros | 14/20 (70%) | 16/20 (80%) |
| Consultas por termos | 8/9 | 7/9 |
| Perguntas completas | 5/9 | 7/9 |
| Variações de escrita | 1/2 | 2/2 |
| MRR@5 | 0,495 | 0,652 |
| Controles sintéticos vazios | 2/2 | 2/2 |

O ganho de dez pontos percentuais resulta de **seis casos recuperados e quatro regressões**. As regressões foram a pergunta sobre fato gerador, as duas consultas sobre créditos e a consulta curta sobre Imposto Seletivo. Por isso, **v1 continua sendo o padrão** e v2 exige seleção explícita; a melhoria agregada ainda não justifica uma troca automática.

Veja a [comparação por caso](../runs/2026-11-06-search-comparison/comparacao.json), a [execução v1](../runs/recuperacao-6fee1e49-eb43-46ac-91f6-a7409ee8b64b/resultado.json) e a [execução v2](../runs/recuperacao-1616278c-b2f3-4291-b628-8d9495333ea2/resultado.json). As primeiras execuções do experimento também foram mantidas em `runs/`, identificadas pelos hashes do código correspondente.

Nos resultados da busca v2, `correspondencia_parcial` informa se houve termos ausentes. `termos_ausentes` lista os lexemas normalizados que faltaram, não palavras literais nem uma medida de confiança. Preservar a palavra “não” na preparação não significa compreender uma negação jurídica. Uma correspondência parcial não deve ser usada automaticamente como fundamento suficiente para gerar uma resposta.

Próximo passo: tratar as regressões de ranking e medir em perguntas adicionais separadas dos casos usados durante o desenvolvimento. Este experimento ainda não usa embeddings ou LLMs.
