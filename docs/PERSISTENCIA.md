# Persistência das revisões e do controle de acesso

Esta entrega adiciona um backend opcional para checkpoints e eventos da revisão. O adaptador é o `langgraph-checkpoint-postgres==3.2.0`, da implementação oficial do LangGraph. A [documentação de persistência](https://docs.langchain.com/oss/python/langgraph/persistence) distingue o estado de execução mantido por checkpointers dos demais dados da aplicação.

**O padrão continua SQLite. Nenhum dado existente foi migrado, apagado ou apontado para outro servidor.** O backend PostgreSQL agora inclui os vínculos de acesso. A credencial do revisor pode vir da configuração privada do ambiente. Ainda faltam conexão remota segura, estratégia para as fontes preservadas e configuração do destino antes do Render Free.

## O que muda quando o backend é selecionado

| Responsabilidade | SQLite padrão | PostgreSQL opcional |
| --- | --- | --- |
| Estado do grafo e pausa para revisão | Arquivo local `revisoes.sqlite3` | Tabelas do adaptador no schema `taxtrace_workflow` |
| Registro das operações | `runs/revisao-<UUID>/evento.json` | Tabela `eventos_revisao`, com documento JSON e hash |
| Exclusão mútua da revisão | Trava em arquivo | Advisory lock de sessão no PostgreSQL |
| Leitura e decisão após reinício | Mesmo arquivo local | Mesmo banco e código compatível |
| Vínculos de acesso do navegador | SQLite local | Tabela `acessos_revisao` no mesmo backend dos checkpoints |
| Conta do revisor | Arquivo privado ou configuração privada | Configuração privada, sem exigir arquivo de conta no disco |

A retomada continua usando o estado salvo e `SemFerramentas`: não repete Gemini nem MCP. Hash divergente, código incompatível e revisão já decidida continuam bloqueados. A conexão que segura a trava é mantida até terminar a operação; fechá-la libera a trava inclusive em erro. Conexão indisponível ou schema ausente não causam fallback para SQLite nem criação automática de tabelas pelo servidor web.

Os eventos têm ID próprio, tipo de operação, retrato documental, data e hash SHA-256. O documento JSON é preservado como texto validado no PostgreSQL: o hash cobre a representação exata, sem depender da normalização numérica ou da ordem de chaves do JSONB. O papel da aplicação recebe leitura e inserção nessa tabela, sem atualização ou exclusão por esse papel. Isso não torna o registro imutável contra o administrador do banco, nem é assinatura digital ou revisão independente. Checkpoints e eventos são gravados em operações separadas: uma falha posterior no registro pode deixar o estado já avançado; confira a revisão antes de repetir uma decisão.

## Execução suportada nesta etapa

O backend de execução PostgreSQL destina-se a Docker/Linux. No Windows, o subprocesso MCP depende do loop Proactor, enquanto a conexão assíncrona psycopg exige Selector. Por isso, a execução de checkpoints PostgreSQL é recusada diretamente no Windows; use o backend SQLite no Windows e o backend PostgreSQL no contêiner Linux. O comando administrativo de preparação não executa MCP e seleciona o loop compatível no Windows.

A URL de checkpoints é independente da URL de consulta e da administrativa. São aceitos apenas:

- local: papel `taxtrace_state`, banco `taxtrace`, loopback e porta 15433;
- Compose: mesmo papel e banco, host `db`, porta 5432, com modo Compose explícito.

Por padrão, hosts remotos continuam recusados. A exceção Neon exige host e banco fixados e TLS verificado; papel administrativo, banco de testes e opções arbitrárias continuam recusados no runtime. **O suporte Neon passou a ser opcional por configuração explícita, descrita em [NEON.md](NEON.md); a conexão com o destino real ainda não foi executada.** O estado usa schema próprio e a configuração de checkpoints não é encaminhada ao subprocesso MCP, que recebe apenas a conexão de leitura das fontes.

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

Os testes de integração no banco isolado são habilitados no CI Linux pelo opt-in já existente. Além dos três testes de checkpoints, há quatro de autorização PostgreSQL, incluindo os privilégios reais de `taxtrace_state`. Eles preparam o schema no banco `taxtrace_test`, usam UUIDs próprios e removem apenas esses registros ao final; não fazem TRUNCATE nem acessam o banco de desenvolvimento. Verificam pausa/retomada entre conexões, eventos, rejeição de decisão repetida, hash incorreto e disputa de trava. Usam ferramentas sintéticas, não uma revisão fiscal real. Um dos testes prepara e usa o papel restrito de runtime e verifica os bloqueios de UPDATE, DELETE e CREATE. Isso valida os grants no banco descartável; as permissões do destino de hospedagem ainda precisam ser conferidas após a preparação daquele ambiente.

A rodada inicial de checkpoints foi preservada com a integração desativada. Na rodada posterior, com o Docker ativo, a imagem foi construída e executada e a suíte Linux completa passou com PostgreSQL real: **183 testes descobertos, 180 aprovados e três desativados por ausência da coleta oficial em `data/raw`**. As sete integrações de checkpoints e autorização foram executadas. O [registro desta validação](../runs/2026-11-07-persistent-access/verification.json) diferencia esse resultado da preparação anterior. O CI remoto e a hospedagem ainda não foram executados nesta rodada.

## Vínculos persistentes

`PropriedadePostgres` usa a mesma escolha de backend, schema e conexão de estado dos checkpoints. A gravação parametrizada é transacional: tentativas concorrentes não podem transferir o dono da revisão. Repetir o vínculo existente não renova sua validade. O PostgreSQL calcula e confere a expiração pelo relógio do banco. O papel de runtime tem SELECT e INSERT na tabela, sem UPDATE ou DELETE; retenção e manutenção ficam fora desse papel. O servidor não cria tabelas ao receber consultas e não recorre ao SQLite em falha de conexão.

Para um banco já preparado na etapa anterior, execute novamente a preparação administrativa para criar a nova tabela e aplicar os grants. Isso não importa o SQLite. Vínculos antigos e checkpoints locais continuam preservados no backend original; não se atribui autorização a quem primeiro informar um UUID.

## Conta sem dependência do disco da aplicação

A configuração `TAXTRACE_REVIEWER_CREDENTIAL_JSON` pode conter a credencial com salt e hash já gerada localmente. Ela prevalece sobre o arquivo de conta quando preenchida. Não é uma senha em texto puro, mas é material privado e deve ser protegido como segredo. Configuração inválida impede inicialização, sem voltar silenciosamente ao arquivo. Quando ausente ou vazia, permanece o comportamento local anterior. Veja [como preparar o acesso](AUTENTICACAO.md).

As sessões autenticadas e o limitador de tentativas continuam em memória: reiniciar exige novo login. A credencial configurada pode ser restaurada pelo ambiente, enquanto checkpoints e vínculos permanecem no PostgreSQL. Esta entrega continua limitada a uma instância local de validação; não habilita Neon, HTTPS, cotas ou transporte público automaticamente.


As fontes originais também podem ser preservadas no PostgreSQL. Isso remove a dependência de `data/raw` para o leitor quando a captura correspondente está arquivada; veja [preparação remota e fontes](NEON.md). A carga remota ainda depende da preparação do destino.
