# Experimento de recuperação semântica local

## Problema e decisão

Uma pessoa pode descrever uma dúvida com palavras diferentes das usadas na lei. A busca textual pode perder o artigo nessa situação. Este experimento mede se um modelo de embeddings ajuda a localizar os artigos de referência sem depender de uma API paga.

**Decisão após medir:** manter a busca textual v4 como padrão. A alternativa semântica ficou abaixo dela nos dois conjuntos e retornou vizinhos até para termos inexistentes. Ela está disponível explicitamente para investigação, sem gerar respostas ou tomar decisões fiscais. Implementar um modelo não é evidência de melhoria do produto.

## Dados e método

- Mesma coleta usada nas avaliações anteriores, identificada pelo manifesto: 580 artigos.
- 990 trechos literais, com até 320 tokens e sobreposição de 48 tokens; um trecho nunca cruza artigos.
- Modelo `intfloat/multilingual-e5-small`, revisão `614241f622f53c4eeff9890bdc4f31cfecc418b3`, artefato ONNX quantizado `qint8_avx512_vnni` do repositório do autor.
- Vetores de 384 dimensões, média das representações com máscara de atenção e normalização L2. Prefixos `query: ` nas consultas e `passage: ` nos trechos, conforme o [model card](https://huggingface.co/intfloat/multilingual-e5-small/tree/614241f622f53c4eeff9890bdc4f31cfecc418b3).
- Inferência local com [ONNX Runtime](https://onnxruntime.ai/docs/get-started/with-python.html), CPU, duas threads internas e lotes de oito trechos. A consulta é inferida individualmente.
- Busca exata por distância de cosseno com [pgvector](https://github.com/pgvector/pgvector), escolhendo o melhor trecho por artigo antes de limitar os resultados. Não há índice aproximado nesta etapa.

O tokenizer e o modelo são verificados por SHA-256 antes do carregamento. A configuração, revisão, hashes, coleta, corpus e contagens ficam registrados. Os pesos locais (aproximadamente 135 MB incluindo tokenizer) não são commitados. A licença indicada para o modelo é MIT; os pesos não são redistribuídos pelo repositório.

Os textos do índice excluem somente as marcações riscadas já tratadas pelo pipeline. Isso não estabelece vigência jurídica. Os offsets dos trechos se referem ao texto pesquisável, não à posição no HTML original.

## Resultado observado, limite de cinco artigos

| Conjunto | Textual v4 | Semântica E5 | Controles vazios: textual / semântica |
| --- | ---: | ---: | ---: |
| Original: 20 positivos + 2 controles | 19/20 (95%) | 12/20 (60%) | 2/2 / 0/2 |
| Adicional: 12 positivos + 2 controles | 11/12 (91,7%) | 9/12 (75%) | 2/2 / 0/2 |

Veja a [comparação por caso](../runs/2026-11-06-semantic-comparison/comparacao.json), o [registro de indexação](../runs/embeddings-1811bcd6-84d3-45e9-9568-60b61c123077/indice.json) e a [verificação do índice real](../runs/2026-11-06-semantic-verification/verificacao.json). As execuções completas estão ligadas no registro de comparação. Não modificamos os gabaritos para acomodar o resultado semântico.

Não há limiar de recusa calibrado: uma consulta sem relação útil com a base ainda recebe seus vizinhos mais próximos. Uma pontuação alta não comprova evidência suficiente nem confiança jurídica. Não utilizamos os controles para escolher um corte de similaridade e apresentar uma taxa artificial de acerto.

Esses conjuntos já eram conhecidos no desenvolvimento e não são um teste independente. A métrica positiva verifica a presença do artigo esperado, não se o trecho recuperado sustenta uma resposta. Latências por caso medem consulta após o carregamento inicial do modelo, não o tempo de partida de uma aplicação. A inferência quantizada pode variar com hardware, lote e padding; não foi comparada com o modelo em precisão completa.

## Como executar

Com os bancos locais ativos e a coleta já carregada, execute da raiz do projeto:

```powershell
.venv/Scripts/python.exe -m pip install -r requirements-embeddings.txt
.venv/Scripts/python.exe -m taxtrace.banco --somente-esquema
.venv/Scripts/python.exe -m taxtrace.vetores preparar-modelo
.venv/Scripts/python.exe -m taxtrace.vetores indexar
.venv/Scripts/python.exe -m taxtrace.busca --metodo semantica --consulta "Como funciona o recolhimento na liquidação financeira?"
.venv/Scripts/python.exe -m taxtrace.avaliacao --metodo semantica
.venv/Scripts/python.exe -m taxtrace.avaliacao --metodo semantica --casos evals/recuperacao.adicional.v1.json
```

O download é explícito e precisa de internet. Depois de preparado o modelo, o encoder não baixa arquivos nem envia o conteúdo das consultas para um provedor. Não é necessária chave de IA. A busca textual continua funcionando sem as dependências de embeddings e sem os pesos locais.

Repetir a indexação da mesma coleta e configuração retorna `indice_ja_existe`, sem gerar outro índice. O processo calcula os vetores antes de abrir a transação de publicação. Antes de gravar, confere novamente a coleta e o texto de origem. Os metadados e todos os fragmentos são inseridos numa única transação: uma falha durante a gravação reverte o índice inteiro. A consulta usa o login somente leitura; o comando de manutenção usa a conexão local de desenvolvimento.

## Evidências verificadas

A verificação local conferiu os 990 trechos contra os 580 artigos, a cobertura sem lacunas não brancas, os hashes individuais, as dimensões e a normalização dos vetores. Também verificou que o login de consulta não pode inserir nas tabelas semânticas e que a busca textual funciona com imports de NumPy, ONNX Runtime e Tokenizers explicitamente bloqueados.

Os testes automatizados usam vetores artificiais identificados como fixtures para testar gravação, ordenação, deduplicação por artigo, permissões, duplicatas e reversão de falhas. Não são apresentados como avaliação do modelo. O CI básico não baixa pesos nem instala as dependências opcionais; a avaliação do modelo real foi executada localmente e registrada separadamente.

## O que ainda falta

Ainda não há RAG com geração, ferramentas MCP ou agente LangGraph. Os próximos experimentos podem avaliar recuperação combinada e reordenação, mas precisam preservar a busca textual como referência e medir também evidência suficiente, citações e recusas. A troca da busca padrão não está justificada por estes resultados.
