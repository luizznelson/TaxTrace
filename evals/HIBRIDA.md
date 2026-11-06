# Recuperação combinada e avaliação dos trechos

## Pergunta de engenharia

A consulta precisa trazer um documento útil e mostrar a passagem necessária para sua conferência. Encontrar o artigo esperado com um recorte que omite a regra de interesse dificulta a revisão. Este experimento combina candidatos textuais e semânticos e mede separadamente a localização do artigo e a presença de uma frase de referência no trecho exibido.

**Decisão:** manter v4 como busca padrão. A combinação RRF não superou a busca textual nesses conjuntos e retornou candidatos nos controles com termos inexistentes. Não foi adotada para geração automática de respostas.

## Como a combinação funciona

A opção `--metodo hibrida` consulta até 20 candidatos da busca textual v4 e 20 da semântica E5, na mesma coleta. Combina as posições por RRF, com constante 60 e pesos iguais. Cada artigo aparece uma única vez. A pontuação final tem tipo `rrf`; as posições nas listas de origem ficam registradas. A [referência do algoritmo](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf) descreve a técnica, não o desempenho deste projeto.

O recorte do artigo vem da primeira lista que o introduziu: a textual é processada antes da semântica. Portanto, um artigo presente nas duas mantém seu recorte textual; não há escolha do trecho usando o gabarito. Artigos exclusivos da semântica mantêm o fragmento literal indexado. Essa política também está identificada no registro da comparação.

O modo híbrido é explícito e exige o modelo e o índice locais já preparados. Falhas de modelo ou índice interrompem a tentativa; não são ocultadas como uma execução híbrida bem-sucedida. Os modos híbrido e semântico retornam o estado `candidatos_para_revisao`. A busca textual padrão continua disponível sem carregar as dependências opcionais.

## O que a nova avaliação verifica

1. A referência citada corresponde à fonte e à versão esperadas.
2. O trecho retornado é uma substring literal do texto pesquisável do artigo citado. Nos fragmentos semânticos, os offsets também precisam corresponder ao trecho.
3. Para cada artigo esperado, a frase de referência do gabarito aparece no trecho retornado?

Uma falha de literalidade ou de offsets interrompe a avaliação; não é contada como um resultado vazio. Os relatórios passam a guardar os trechos exibidos, seus hashes e os acertos de âncora por referência. O gabarito anterior foi preservado.

O campo `hit_ancora_literal_at_k` mede a proporção de consultas positivas em que pelo menos uma referência esperada exibe sua âncora. A verificação é literal, incluindo acentos e redação; uma passagem equivalente pode receber zero. As âncoras são curtas e não foram revisadas por especialista. Por isso, a suficiência para formular uma resposta fica marcada como **`nao_avaliada`**, mesmo quando a âncora aparece.

## Resultados com cinco artigos

| Conjunto / busca | Artigo esperado encontrado | Âncora no trecho do artigo esperado | Controles sem resultado |
| --- | ---: | ---: | ---: |
| Original / textual v4 | 19/20 | 19/20 | 2/2 |
| Original / semântica | 12/20 | 10/20 | 0/2 |
| Original / híbrida RRF | 16/20 | 16/20 | 0/2 |
| Adicional / textual v4 | 11/12 | 11/12 | 2/2 |
| Adicional / semântica | 9/12 | 8/12 | 0/2 |
| Adicional / híbrida RRF | 9/12 | 9/12 | 0/2 |

Veja os resultados completos e os casos de artigo recuperado sem âncora no [registro de comparação](../runs/2026-11-06-hybrid-evidence-comparison/comparacao.json). As primeiras medições desta etapa também foram preservadas em `runs/`; o registro aponta as execuções finais.

Os três casos semânticos de artigo esperado sem âncora mostram por que é útil avaliar o recorte além da referência. A presença de trechos reais em consultas de controle também demonstra que fidelidade à fonte não comprova pertinência. Não usamos esses controles para escolher um corte de similaridade que melhorasse artificialmente os resultados.

## Reprodução

Com o modelo e o índice preparados conforme [SEMANTICA.md](SEMANTICA.md):

```powershell
.venv/Scripts/python.exe -m taxtrace.busca --metodo hibrida --consulta "Como funciona o recolhimento na liquidação financeira?"
.venv/Scripts/python.exe -m taxtrace.avaliacao --metodo v4
.venv/Scripts/python.exe -m taxtrace.avaliacao --metodo hibrida
.venv/Scripts/python.exe -m taxtrace.avaliacao --metodo hibrida --casos evals/recuperacao.adicional.v1.json
```

Também é possível executar a avaliação com `--metodo semantica`. Cada tentativa concluída grava um registro novo. A coleta, o gabarito, a configuração do índice e os hashes do código ficam identificados.

## Limites e próximo passo

Os resultados são dos conjuntos de desenvolvimento já conhecidos. Não há teste independente de usuários ou validação jurídica. Um fragmento literal pode omitir exceções e condições; a métrica de âncora não valida uma resposta tributária nem sua vigência. As falhas conhecidas permanecem registradas.

A próxima integração pode expor a consulta e as evidências como ferramentas MCP, mantendo explícitos esses limites. A geração de respostas exigirá avaliação própria de suficiência, citações, recusas e data aplicável; não está liberada pelo resultado deste experimento.
