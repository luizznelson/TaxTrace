# Checkpoints PostgreSQL: primeira etapa da persistência fora do disco

Esta entrega adiciona um backend opcional para checkpoints e eventos da revisão. O adaptador é o `langgraph-checkpoint-postgres==3.2.0`, da implementação oficial do LangGraph. A [documentação de persistência](https://docs.langchain.com/oss/python/langgraph/persistence) distingue o estado de execução mantido por checkpointers dos demais dados da aplicação.

**O padrão continua SQLite. Nenhum dado existente foi migrado, apagado ou apontado para outro servidor.** Esta etapa não encerra a persistência para Render Free: vínculos de acesso, credencial local, fontes preservadas e configuração do destino continuam pendentes.

## O que muda quando o backend é selecionado

| Responsabilidade | SQLite padrão | PostgreSQL opcional |
| --- | --- | --- |
| Estado do grafo e pausa para revisão | Arquivo local `revisoes.sqlite3` | Tabelas do adaptador no schema `taxtrace_workflow` |
| Registro das operações | `runs/revisao-<UUID>/evento.json` | Tabela `eventos_revisao`, com documento JSON e hash |
| Exclusão mútua da revisão | Trava em arquivo | Advisory lock de sessão no PostgreSQL |
| Leitura e decisão após reinício | Mesmo arquivo local | Mesmo banco e código compatível |
| Vínculos de acesso do navegador | SQLite local | Ainda SQLite local; adaptação pendente |
| Conta do revisor | Arquivo privado local | Ainda arquivo privado local; adaptação pendente |

A retomada continua usando o estado salvo e `SemFerramentas`: não repete Gemini nem MCP. Hash divergente, código incompatível e revisão já decidida continuam bloqueados. A conexão que segura a trava é mantida até terminar a operação; fechá-la libera a trava inclusive em erro. Conexão indisponível ou schema ausente não causam fallback para SQLite nem criação automática de tabelas pelo servidor web.

Os eventos têm ID próprio, tipo de operação, retrato documental, data e hash SHA-256. O documento JSON é preservado como texto validado no PostgreSQL: o hash cobre a representação exata, sem depender da normalização numérica ou da ordem de chaves do JSONB. O papel da aplicação recebe leitura e inserção nessa tabela, sem atualização ou exclusão por esse papel. Isso não torna o registro imutável contra o administrador do banco, nem é assinatura digital ou revisão independente. Checkpoints e eventos são gravados em operações separadas: uma falha posterior no registro pode deixar o estado já avançado; confira a revisão antes de repetir uma decisão.

## Execução suportada nesta etapa

O backend de execução PostgreSQL destina-se a Docker/Linux. No Windows, o subprocesso MCP depende do loop Proactor, enquanto a conexão assíncrona psycopg exige Selector. Por isso, a execução de checkpoints PostgreSQL é recusada diretamente no Windows; use o backend SQLite no Windows e o backend PostgreSQL no contêiner Linux. O comando administrativo de preparação não executa MCP e seleciona o loop compatível no Windows.

A URL de checkpoints é independente da URL de consulta e da administrativa. São aceitos apenas:

- local: papel `taxtrace_state`, banco `taxtrace`, loopback e porta 15433;
- Compose: mesmo papel e banco, host `db`, porta 5432, com modo Compose explícito.

Hosts remotos, papel administrativo, banco de testes e opções arbitrárias são recusados. **A conexão Neon ainda não está habilitada por esta entrega.** O estado usa schema próprio e a configuração de checkpoints não é encaminhada ao subprocesso MCP, que recebe apenas a conexão de leitura das fontes.

## Preparar o banco local explicitamente

Com o PostgreSQL local ativo e o `.env` administrativo já configurado, acrescente uma senha exclusiva, de pelo menos 12 caracteres:

```dotenv
TAXTRACE_CHECKPOINT_PASSWORD=SUBSTITUA_POR_UMA_SENHA_EXCLUSIVA
```

Não publique o `.env` nem compartilhe URLs de conexão. Na pasta do projeto, execute:

```powershell
.venv/Scripts/python.exe -m taxtrace.checkpoints preparar
```

O comando usa a conexão administrativa local apenas para criar o papel restrito `taxtrace_state`, se ele não existir, preparar o schema e aplicar as migrações oficiais. Se o papel já existir, sua senha não é trocada silenciosamente; a URL de runtime deve corresponder à senha já configurada. Papéis elevados ou com associação a outros papéis são recusados. O comando não apaga dados, não copia o SQLite, não altera a carga das fontes e não é executado automaticamente no startup web. Como as migrações oficiais incluem índices concorrentes, a preparação usa autocommit e pode exigir nova execução após uma falha parcial.

Depois da preparação, selecione o backend para a aplicação no Docker:

```dotenv
TAXTRACE_CHECKPOINT_BACKEND=postgres
```

A composição monta a URL interna de `taxtrace_state` usando a senha configurada. Caracteres reservados da senha precisam ser codificados corretamente na URL, conforme as instruções de Docker. Não use a senha do administrador. Recrie a aplicação com a composição existente, depois de construir e validar a imagem:

```powershell
docker compose -f docker-compose.yml -f docker-compose.app.yml up -d --build --wait
```

A escolha vale para novos acessos ao backend selecionado. Históricos SQLite permanecem nos arquivos antigos e devem ser lidos com a configuração SQLite original; não são misturados ou migrados por suposição. Uma mudança de código também impede nova decisão em checkpoints de uma versão anterior, sem impedir sua inspeção no backend correspondente.

## Validação e limites

Os testes locais exercitam escolha do backend, restrição de destino/papel, ausência de fallback, controle de trava com conexão simulada, registro de evento sem arquivo local e os fluxos SQLite já existentes. Não demonstram integração PostgreSQL real.

Há três testes de integração no banco isolado de testes, habilitados no CI Linux pelo opt-in já existente. Eles preparam o schema no banco `taxtrace_test`, usam UUIDs próprios e removem apenas esses registros ao final; não fazem TRUNCATE nem acessam o banco de desenvolvimento. Verificam pausa/retomada entre conexões, eventos, rejeição de decisão repetida, hash incorreto e disputa de trava. Usam ferramentas sintéticas, não uma revisão fiscal real. A conexão privilegiada do banco isolado nesses testes não comprova, por si só, os grants do papel de runtime em um deploy.

Nesta rodada, as portas locais de desenvolvimento e testes estavam indisponíveis. Os testes de integração PostgreSQL ficaram desativados e ainda precisam de execução comprovada no CI ou Docker/Linux. A implementação não deve ser anunciada como persistência remota validada ou como hospedagem concluída.
