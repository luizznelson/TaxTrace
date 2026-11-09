# Preparação do Render — 08/11/2026

A configuração de hospedagem foi implementada e ensaiada localmente.
**Nenhum serviço público foi criado nesta execução.** O banco Neon real foi
usado somente para leitura no smoke web. Não houve chamada a modelo externo,
criação de conta de revisor ou migração de histórico.

- `verification.json`: resultados, limites, falhas preliminares e pendências.
- `integration.txt`: suíte Linux com PostgreSQL descartável; 212 descobertos, 209 aprovados, três desativados por falta da captura oficial na suíte padrão.
- `build.txt`: construção da imagem final com carregamento explícito.
- `container-smoke.json`: processo, cabeçalhos, conta sem root e ausência de credenciais embutidas na imagem.
- `smoke-publico-local.json`: entrada `python -m taxtrace.servir`, porta 10000, cookie Secure com HTTP interno, origem HTTPS fixa e API consultando a captura no Neon real.

Os onze novos testes de publicação exercitam origem, cookie, login, limites,
idempotência e exportação privada. A validação YAML e as restrições do Blueprint
foram conferidas localmente; o Blueprint não foi validado pela API do Render.
O CI remoto também não foi verificado nesta execução.

A primeira integração utilizou imagem antiga devido à saída do builder não
carregada. Foi repetida após `docker build --load`, com sucesso. O teste de login
inicial apontava para uma rota inexistente e foi corrigido antes da suíte final.
A leitura das evidências deve distinguir esses ensaios do resultado aprovado.

`.env.render` foi gerado fora do Git por lista permitida. Não contém conexão
administrativa; a chave de modelo existente foi incluída privadamente, mas a IA
pública permanece desabilitada até a configuração no serviço. Não existe conta
de revisor configurada: decisões permanecem bloqueadas até cadastrá-la.

Os limites são globais em memória para um worker e reiniciam com o processo.
Não equivalem a cota financeira, proteção distribuída ou auditoria de segurança
independente. O modo local de desenvolvimento permanece disponível.

Veja o [passo a passo de publicação](../../docs/RENDER.md).
