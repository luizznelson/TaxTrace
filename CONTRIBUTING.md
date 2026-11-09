# Contribuir com o TaxTrace

Comece pelo [README](README.md), [mapa da arquitetura](docs/architecture.md) e
[guia de desenvolvimento](docs/development.md). A referência atual de escopo é
[PLANO.md](PLANO.md); uma marcação no plano não substitui evidência de execução.

## Mudanças pequenas e verificáveis

Explique qual comportamento muda, por que muda e como foi conferido. Separe
correções de lógica, mudanças de dados e revisão de apresentação quando forem
entregas independentes. Não mova módulos apenas para imitar a estrutura de outro
projeto: caminhos de importação, comandos, imagem e checkpoints têm consequências.

- Use linguagem de negócio para utilidade e limites; seja preciso ao explicar a
  implementação. Não invente clientes, economia de tempo ou precisão jurídica.
- Mudança no código exige verificações pertinentes ao risco. Mudança editorial
  exige conferir links, exemplos, paridade PT-BR/EN e afirmações contra a evidência.
- Testes de integração usam o banco isolado. Não aponte a suíte ao Neon hospedado.
- Preservar uma falha de avaliação é parte da entrega. Não ajuste gabaritos para
  contar a saída do próprio sistema como acerto sem justificar a alteração.

## Evidências e arquivos privados

Novos registros publicáveis vão para `runs/`, sem sobrescrever execuções anteriores.
Atualize o [índice](runs/README.md) com o propósito e o limite da nova verificação.
Amostras e decisões sintéticas precisam de identificação explícita.

Não inclua `.env` real, chaves, URLs privadas, senha/hash de revisor, bancos de
checkpoint, cookies, pesos ou intermediários de gravação. Exemplos devem usar
valores sintéticos. A licença do código não transfere a licença das fontes.

## Commits e publicação

Use um assunto curto e concreto, por exemplo:

- `fix: recusar citação divergente da fonte`
- `feat: adicionar leitura integral vinculada à coleta`
- `docs: organizar apresentação e índice de evidências`

A sequência de revisão é problema → comportamento resultante → evidência →
limitações. O deploy é configurado para aguardar checks do GitHub, com aplicação
do Blueprint no Render. Segredos são configurados no painel, não por commit.
Os comandos e os limites completos estão em [qualidade](docs/quality.md) e
[publicação](docs/RENDER.md).
