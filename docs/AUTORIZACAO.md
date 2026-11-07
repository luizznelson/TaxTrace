# Quem pode acessar cada revisão

O identificador da revisão serve para localizar um registro. Ele não concede acesso por si só. A aplicação separa a consulta de fontes públicas dos registros criados por cada navegador.

| Operação | Visitante | Conta de revisor autenticada |
| --- | --- | --- |
| Consultar a cobertura da base | Permitido | Permitido |
| Iniciar consulta | Exige cookie válido do navegador | Exige cookie válido do navegador |
| Abrir revisão, baixar JSON e carregar artigo vinculado | Apenas revisões vinculadas à sessão do navegador, dentro do prazo | Acesso administrativo a todas as revisões deste ambiente |
| Aprovar ou rejeitar | Bloqueado | Permitido, com hash e demais verificações de revisão |

## Como funciona

Ao carregar o contexto, o servidor emite um token aleatório de 256 bits em cookie `HttpOnly`, `SameSite=Strict`, com duração de 30 dias. Em HTTPS, o cookie recebe `Secure`; HTTP continua restrito ao desenvolvimento local. O token não aparece no JSON do contexto, no histórico JavaScript ou nas evidências exportadas.

Ao concluir uma consulta, o identificador da revisão é associado ao hash SHA-256 desse token em `data/checkpoints/acessos.sqlite3` no backend SQLite, ou em `taxtrace_workflow.acessos_revisao` no backend PostgreSQL. A vinculação é persistente, parametrizada e não pode ser transferida para outra sessão. Uma falha ao salvar a vinculação impede a entrega da resposta à chamada; o checkpoint pode continuar existente e acessível ao revisor. O banco de vínculos não guarda perguntas ou respostas, apenas identificador, hash do token e expiração.

O visitante pode recuperar essa revisão por até 30 dias a partir da criação do vínculo, desde que preserve o cookie. A abertura não renova o prazo. Vínculos expirados permanecem no banco nesta etapa, mas deixam de autorizar leitura. Não há limpeza automática do histórico fiscal ou dos checkpoints.

Reiniciar o servidor preserva os vínculos se o armazenamento do backend correspondente for mantido. No PostgreSQL, os vínculos deixam de depender do disco da aplicação. A sessão do revisor, por outro lado, continua em memória e exige novo login após reinício. Apagar cookies, trocar de navegador ou usar outro perfil elimina o acesso anônimo aos registros anteriores; a conta de revisor continua podendo recuperá-los. Abas do mesmo navegador/perfil compartilham o cookie de acesso, embora a lista visual de histórico continue separada por aba.

Revisões anteriores à implementação não recebem dono por suposição nem são atribuídas a quem primeiro informar seu UUID. Para abri-las, entre como revisor. O histórico não é apagado. Conhecer um UUID existente sem autorização retorna o mesmo HTTP 404 de um registro desconhecido; a aplicação não consulta o checkpoint nem o artigo nesses casos.

A chave de idempotência também fica vinculada ao navegador: repetir uma tentativa na mesma sessão reutiliza o resultado, enquanto outro navegador que envie o mesmo identificador de tentativa não recebe essa resposta.

## Arquivos privados

No modo SQLite, o banco de vínculos e a credencial local ficam em `data/checkpoints/`, fora do Git. No PostgreSQL, os vínculos ficam no banco; a credencial pode ser fornecida pela configuração privada do ambiente. Não os publique, exponha por rota estática ou copie para as evidências. Quem controla esses arquivos locais controla a autorização do ambiente. O cookie é uma credencial de posse: mantê-lo secreto é necessário, e esta implementação não protege contra comprometimento do computador ou da origem da aplicação.

## Limites para publicação

Esta etapa foi validada em um único processo local, com armazenamento persistente no computador. Não há autenticação federada, papéis por organização, compartilhamento entre equipes, revogação individual de visitantes, limites distribuídos ou múltiplas instâncias. A conta local de revisor é administrativa, não deve ser compartilhada com visitantes. O serviço continua restrito a localhost. A preparação não significa que o deploy já está liberado: HTTPS, autenticação adequada ao destino, política de uso/cotas e armazenamento persistente ainda precisam de configuração e validação.

Os testes cobrem dois navegadores isolados, leitura e exportação, carregamento de fontes, idempotência, reinício, expiração, arquivo de vínculos corrompido, acesso administrativo e logout. Os dados são sintéticos; não representam revisão fiscal real ou auditoria independente de segurança.


## Validação PostgreSQL

A implementação compartilha a seleção do backend dos checkpoints e usa relógio do banco para validade de 30 dias. Os vínculos são criados atomicamente e não têm atualização ou exclusão concedida ao papel da aplicação. Quatro testes de integração foram executados no Docker com PostgreSQL descartável: disputa entre donos, expiração, isolamento das rotas e permissões reais do papel restrito. As credenciais e os dados usados são sintéticos. Veja [persistência](PERSISTENCIA.md) e [evidências](../runs/2026-11-07-persistent-access/verification.json). Não foi realizado deploy ou migração automática do histórico local.
