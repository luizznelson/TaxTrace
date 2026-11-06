# Leitura integral e links por artigo

Data: 2026-11-06. Sem deploy, nova coleta ou chamada de modelo externo.

## Problema e correção

O leitor anterior mostrava trechos de busca ou até 3.000 caracteres de texto pesquisável, que havia perdido as quebras de linha. Os links apontavam ao documento inteiro. O novo leitor usa o artigo integral preservado na mesma coleta, com parágrafos, incisos, alíneas e risco das redações antigas. O trecho original permanece na aba Evidência da consulta.

O artigo completo é leitura de contexto: não substitui silenciosamente o conjunto associado ao hash da decisão. O formulário identifica as evidências da revisão e o JSON complementar é exportado separadamente.

## Conferência executada

- Python: 118 casos descobertos, 97 passaram, 21 ignorados pelas condições opcionais da suíte.
- JavaScript: seis testes de entradas passaram.
- Ruff (análise e formatação), sintaxe JavaScript e formatação dos arquivos conferidos.
- Testes novos cobrem preservação de parágrafos e marcações, conteúdo com aparência de HTML mantido como texto, rejeição de marcações inválidas, ausência de truncamento de artigo longo, fonte/coleta divergentes e artigo fora das referências da consulta.
- No navegador: artigo 125 completo em dois parágrafos, link `#art125`, troca PT/EN e exportação complementar disponível.
- Artigo 517: 151 parágrafos no leitor, 24.930 caracteres de conteúdo visível (sem delimitadores de risco e separadores de linha). A evidência original permaneceu com 3.000 caracteres. Final do artigo presente no leitor.
- Tela de 390 × 844: largura de conteúdo 375 px, sem rolagem horizontal no cenário observado. Leitor de artigo longo com rolagem própria e foco por teclado.
- Falha de inicialização do cache do cliente foi encontrada no primeiro teste real, corrigida e a leitura foi repetida com sucesso. Nenhum erro capturado no console ao final.
- Não foi enviada decisão de revisão.

## Limites e evidências

As âncoras foram conferidas no HTML local pelo hash da fonte. Das 580 entradas da coleta, 526 têm a âncora esperada; quando ausente, usa-se tentativa por fragmento de texto. Isso depende do navegador e da página. O acesso automatizado atual ao Planalto foi bloqueado pelo serviço; não se afirma uma verificação ao vivo do salto de página.

Os JSONs abaixo preservam origem, coleta, texto, estrutura e hashes. As capturas mostram a execução local. Nenhum desses registros comprova vigência jurídica ou revisão fiscal.

- [Artigo 125 e origem](artigo-125.json)
- [Artigo 517 e origem](artigo-517.json)
- [Leitor no computador](desktop.jpg)
- [Leitor em tela pequena](mobile.jpg)
