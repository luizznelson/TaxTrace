# Bancada de pesquisa — verificação local

Data: 2026-11-06. Escopo: apresentação, navegação, leitura das referências e formulário de revisão. Sem deploy, mudança de autenticação, alteração do recuperador ou execução de modelo externo.

## Verificações automatizadas

- `python -m unittest discover -s tests -q`: 111 casos descobertos, 90 passaram, 21 ignorados pelas condições opcionais da suíte (incluindo integração PostgreSQL opt-in). Não representam 111 execuções bem-sucedidas.
- Os seis testes de `tests.test_web` passaram, incluindo proteção de origem, limites de entrada, idempotência e não exposição de detalhes privados.
- `python -m ruff check .`: passou.
- `node --check taxtrace/static/app.js`: passou.
- Formatação dos arquivos de interface conferida com Prettier disponível localmente.

## Conferência no navegador

- Consulta direta real por `cesta basica`, com retorno dos artigos 125 e 475.
- Seleção das duas referências alternou o documento exibido e seu estado selecionado.
- Artigo 475 identificado como trecho de busca, com aviso de conteúdo incompleto e link da fonte oficial.
- Revisão em computador manteve leitor e formulário lado a lado.
- Nome e justificativa de teste preservados entre evidência/revisão e PT/EN; confirmação não foi marcada. Nenhuma decisão foi enviada nesta conferência.
- Histórico preservado após recarregar e consulta retomada pelo histórico.
- Tela de 390 × 844: leitura e lista empilhadas, sem rolagem horizontal da página no cenário observado (largura do documento 375 px, viewport 390 px).
- Nenhum erro capturado no console durante a sessão.

## Capturas

- [Pesquisa e leitor](research-desktop.jpg)
- [Fonte e formulário de revisão](review-desktop.jpg)
- [Tela pequena](research-mobile.jpg)

São capturas de uma execução local com dados da coleta e rascunho de teste. Não comprovam revisão fiscal, uso por equipe real, ganhos de produtividade ou operação pública. A validação não substitui auditoria completa de acessibilidade ou segurança.
