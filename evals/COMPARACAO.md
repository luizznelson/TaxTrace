# Busca atual: preservar acertos e ampliar a cobertura

O objetivo é ajudar a encontrar o artigo de referência sem retirar resultados úteis da busca original. A versão atual, **v4**, mantém a lista da v1 na mesma ordem e usa a v2 apenas para preencher vagas. Se já houver cinco resultados e o limite for cinco, nenhuma busca ampliada é executada.

## O que foi comparado

- **v1:** busca textual original, com os termos exigidos pela consulta.
- **v2:** busca com normalização de acentos, preparação da pergunta e correspondências parciais sinalizadas.
- **v3:** experimento de fusão por posição, RRF, com constante 60 e até 20 candidatos por busca. Permanece disponível, mas não foi adotado como padrão: não resolveu as quatro regressões do primeiro conjunto. A referência do método é o [artigo de Cormack, Clarke e Büttcher](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf); seus resultados publicados não são evidência de qualidade do TaxTrace.
- **v4 (padrão):** preservação da v1 e complemento com candidatos inéditos da v2, sem reordenação global. É uma política de complemento, não fusão RRF.

## Resultados medidos com limite de cinco artigos

| Conjunto | v1 | v2 | v3 (RRF) | v4 (conservadora) |
| --- | ---: | ---: | ---: | ---: |
| Original: 20 consultas positivas | 14/20 (70%) | 16/20 (80%) | 16/20 (80%) | **19/20 (95%)** |
| Adicional: 12 consultas positivas | 6/12 (50%) | 10/12 (83,3%) | 10/12 (83,3%) | **11/12 (91,7%)** |

Cada conjunto inclui ainda dois controles sintéticos, que não entram nos percentuais. Todos ficaram vazios nas quatro estratégias. São 22 casos originais e 14 adicionais, não 36 perguntas reais de usuários.

O [registro de comparação](../runs/2026-11-06-conservative-search/comparacao.json) aponta as execuções completas, os cinco ganhos em cada conjunto e a ausência de perdas em relação à v1. Também verifica que todos os resultados originais permanecem como prefixo, inclusive nas consultas de controle. O gabarito original não foi alterado.

Na v4, o MRR@5 foi 0,712 no conjunto original e 0,715 no adicional. A v4 favorece preservar a ordem anterior, mesmo quando uma estratégia experimental coloca uma referência mais acima; ela não domina todas as métricas.

Ainda falham a consulta curta sobre extinção de débitos, no conjunto original, e a pergunta sobre segregação no split payment, no adicional. Não completamos os gabaritos com artigos retornados apenas para contar acertos.

## Como reproduzir

Com o banco local atualizado:

```powershell
.venv/Scripts/python.exe -m taxtrace.busca --consulta "cesta basica"
.venv/Scripts/python.exe -m taxtrace.avaliacao --metodo v1
.venv/Scripts/python.exe -m taxtrace.avaliacao --metodo v4
.venv/Scripts/python.exe -m taxtrace.avaliacao --casos evals/recuperacao.adicional.v1.json --metodo v1
.venv/Scripts/python.exe -m taxtrace.avaliacao --casos evals/recuperacao.adicional.v1.json --metodo v4
```

Se o banco ainda não tiver o índice v2, execute antes `python -m taxtrace.banco --somente-esquema` usando o Python da `.venv`. Não é necessário recarregar a coleta. A v4 usa os mesmos índices, fontes e conexão somente leitura. Todos os métodos aceitam seleção explícita por `--metodo`.

Nos resultados v4, `origem` mostra se o artigo veio da v1 ou do complemento v2. `pontuacao_tipo` identifica a escala; as pontuações não são comparáveis entre as duas buscas e não determinam uma reordenação global. `termos_ausentes` nulo significa que a cobertura v2 não foi aferida; lista vazia significa que nenhum lexema da consulta preparada faltou. Isso não mede compreensão jurídica.

## Como interpretar com honestidade

As novas perguntas cobrem artigos diferentes dos usados no primeiro conjunto e foram fixadas antes de executar a primeira fusão. Porém, seus resultados foram consultados durante a decisão pela v4. São validação adicional de desenvolvimento, **não teste independente ou revisão por especialista**. O mesmo tema de saúde aparece em duas variações. Não estimamos significância estatística.

A preservação do prefixo evita perder resultados da v1 no mesmo limite e na mesma coleta, mas não garante que esses resultados sejam úteis. Quando a lista original já está cheia, a v4 não tenta melhorar sua ordem. Também pode incluir correspondências parciais nas vagas restantes. Não há garantia de que o trecho de até 1.000 caracteres sustente uma resposta.

Os percentuais medem localização de artigos nesses casos, não precisão tributária, controle de vigência, economia de tempo ou qualidade de respostas geradas. Esta comparação antecede a geração de respostas. Hoje há experimentos [semântico](SEMANTICA.md) e [híbrido](HIBRIDA.md), além de [RAG avaliado separadamente](RAG.md). Esses resultados de localização de artigos não passam a medir qualidade de geração.
