# Execução da aplicação em Docker

O pacote separa código, fontes e estado da aplicação. Esta configuração é para um único computador e uma instância; ainda não é um deploy público. A porta da aplicação fica vinculada a `127.0.0.1`.

## O que vai para cada local

| Local | Conteúdo | Persistência |
| --- | --- | --- |
| Imagem `taxtrace:local` | Python, dependências e código da aplicação | Recriada pelo build |
| Volume `taxtrace-db` | PostgreSQL já usado no desenvolvimento | Preservado entre reinícios |
| Volume `taxtrace-checkpoints` | Checkpoints, vínculos de autorização e conta local de revisor | Preservado entre recriações |
| Volume `taxtrace-runs` | Eventos de consulta e revisão exportados pela aplicação | Preservado entre recriações |
| Montagem `data/raw` | Coleta oficial preservada no computador | Somente leitura no contêiner |

Os volumes têm o prefixo do projeto Compose. Não use `down -v`: isso remove dados persistentes. Os volumes de revisão e registros começam separados das pastas usadas pela aplicação executada diretamente no Windows; esta entrega não migra ou substitui seu histórico local automaticamente.

O build usa uma lista de arquivos permitidos e cópias explícitas de código. `.env`, Git, downloads, modelos, credenciais e registros locais ficam fora da imagem. A aplicação executa como UID/GID 10001, sem root, com sistema de arquivos raiz somente leitura, permissões Linux reduzidas e área temporária limitada. Os diretórios de estado necessários continuam graváveis pelos volumes.

## Pré-requisitos

Docker Desktop ativo, `.env` local existente com as senhas correspondentes às URLs e uma coleta em `data/raw`. O caminho de fontes deve existir; o Compose não cria uma pasta vazia silenciosamente. O banco precisa estar carregado e o papel `taxtrace_reader` preparado conforme o README. O comando de build não realiza coleta, migração, carga ou download de modelos.

Senhas interpoladas na URL do serviço precisam estar codificadas para uso em URL caso contenham caracteres reservados, mantendo o valor real correspondente no banco. Não imprima `docker compose config` ou inspeções completas de ambiente para compartilhar: a configuração resolvida contém segredos. Para conferir a sintaxe sem mostrá-los, use `config --quiet`.

## Executar

Na pasta do projeto:

```powershell
docker compose -f docker-compose.yml -f docker-compose.app.yml config --quiet
docker compose -f docker-compose.yml -f docker-compose.app.yml up -d --build --wait
```

Abra `http://127.0.0.1:8017`. Essa porta não conflita com a instância Windows que usa 8015. O healthcheck da imagem verifica o processo, não a prontidão da base; use `/health/ready` na porta 8017 para conferir a base. Uma aplicação saudável ainda pode estar sem dados ou conexão.

O serviço recebe somente a URL do papel de leitura e as configurações opcionais Gemini. O modo `TAXTRACE_DATABASE_MODE=compose` permite apenas leitura no host `db`, porta 5432, banco `taxtrace`, com papel `taxtrace_reader`. Não libera banco remoto, acesso de manutenção ou teste fora do destino isolado. O processo MCP recebe explicitamente a URL de leitura e esse modo; não recebe a URL administrativa ou a chave Gemini do processo pai.

## Conta do revisor no volume

O volume novo não tem a conta configurada no Windows. Para criar uma conta no contêiner, com o serviço iniciado:

```powershell
docker compose -f docker-compose.yml -f docker-compose.app.yml exec app python -m taxtrace.autenticacao --conta revisor --nome "Seu nome"
docker compose -f docker-compose.yml -f docker-compose.app.yml restart app
```

A senha é pedida de forma interativa, sem aparecer na linha de comando. Não copie o arquivo de credencial para a imagem ou para o Git. Reiniciar carrega a conta e encerra sessões de revisor anteriores; os vínculos de autorização e checkpoints permanecem no volume. As [limitações da conta local](AUTENTICACAO.md) e a [política de acesso](AUTORIZACAO.md) continuam válidas.

## Parar sem apagar

```powershell
docker compose -f docker-compose.yml -f docker-compose.app.yml stop app
```

Isso para apenas a aplicação, preservando banco e volumes. Eventos no volume `taxtrace-runs` não aparecem automaticamente no Git: extraia e revise somente os registros que pretende publicar. Nunca copie o volume privado de checkpoints para o repositório.

## Verificação da imagem no CI

O job `container` do GitHub Actions constrói a imagem sem credenciais e executa `scripts/smoke_container.py`. O verificador usa um contêiner temporário identificado, porta local aleatória e nenhuma conexão de banco ou modelo. Confere processo ativo, base explicitamente indisponível, interface e cabeçalhos, ausência de chave/conta embutida e usuário sem root. O contêiner criado pelo verificador é parado ao final; nenhum volume do projeto é removido.

Para reproduzir quando o Docker estiver ativo:

```powershell
docker build --load --pull -t taxtrace:ci .
python scripts/smoke_container.py --imagem taxtrace:ci --saida runs/minha-validacao-container/smoke.json
```

O relatório não sobrescreve evidência anterior. No CI, o artefato `container-smoke-<execução>-<tentativa>` é preservado por 30 dias quando houver relatório. Uma falha de build impede sua geração e não deve ser chamada de teste de runtime aprovado.

Nesta entrega local, o Compose foi validado sem exibir configuração, mas o Docker não respondeu à verificação do motor. **Esse registro descreve a preparação inicial; a imagem foi construída e executada na validação posterior, abaixo.** O job remoto também precisa ser conferido após o push. Os testes Python validam configurações e isolamento, não substituem o smoke real nem validam consultas MCP contra PostgreSQL dentro do contêiner.

A imagem usa a tag oficial `python:3.14-slim`, sem digest fixado nesta etapa. Dependências diretas têm versões fixadas; a tag e dependências transitivas ainda podem mudar. Não alegamos build idêntico byte a byte. Depois do primeiro build validado, registrar digest e avaliar congelamento completo das dependências continua sendo uma melhoria possível.

## Consequência para hospedagem gratuita

O estado atual depende de arquivos persistentes: SQLite de checkpoints, vínculos e credencial local. Segundo a [documentação oficial do Render Free](https://render.com/docs/free), arquivos locais são perdidos em reinícios, redeploys e suspensão, e serviços Free não aceitam disco persistente. Portanto, publicar esta versão diretamente no Free pode perder revisões e autorizações.

Para manter essa hospedagem, a próxima adaptação precisa mover o estado persistente para um serviço adequado, tratar identidade/segredos fora do filesystem efêmero e validar conexão remota segura. As fontes preservadas também precisam de uma estratégia de disponibilização sem embutir dados privados. Ainda faltam configuração de domínio/HTTPS, cotas, acesso público e validação de recursos. Nenhum deploy foi realizado nem custo assumido nesta etapa.

Referências de implementação: [boas práticas de build](https://docs.docker.com/build/building/best-practices/), [contexto e dockerignore](https://docs.docker.com/build/concepts/context/#dockerignore-files), [serviços do Compose](https://docs.docker.com/reference/compose-file/services/).


## Backend de checkpoints opcional

A composição também permite selecionar checkpoints e eventos PostgreSQL, após preparação explícita do schema e do papel `taxtrace_state`. O backend PostgreSQL também guarda os vínculos de acesso; a credencial pode vir da configuração privada. Isso não migra dados locais automaticamente nem habilita Neon ou Render. Veja [persistência e validações pendentes](PERSISTENCIA.md). O padrão permanece SQLite.


## Integração Linux validada

Depois de ativar o Docker, a suíte passou em um PostgreSQL descartável: 180 testes aprovados e três desativados por ausência da coleta oficial. O smoke da imagem também passou, verificando processo ativo, diagnóstico da base, cabeçalhos, usuário sem root e ausência de dados privados na imagem. A primeira tentativa e a falha inicial por gabaritos não montados foram preservadas; o ambiente de testes passou a montar `evals/` somente para leitura. Os gabaritos continuam fora da imagem de runtime.

Para reproduzir sem utilizar o banco de desenvolvimento, construa a imagem e execute:

```powershell
docker build --load --pull -t taxtrace:ci .
docker compose -p taxtrace-integration -f docker-compose.integration.yml up --abort-on-container-exit --exit-code-from integration-tests
```

A composição de integração usa um banco em memória temporária, sem portas publicadas e com senha exclusiva de teste. Monta apenas `tests/` e `evals/` como leitura; não recebe `.env`, coleta bruta ou chaves reais. A imagem executa os testes em Linux, inclusive os checkpoints PostgreSQL. Para limpar apenas os contêineres e a rede desse projeto de testes:

```powershell
docker compose -p taxtrace-integration -f docker-compose.integration.yml down
```

Não substitua esse comando pelo projeto de desenvolvimento nem acrescente exclusão de volumes. Essa validação local não comprova que o CI remoto já executou. Veja [o registro completo](../runs/2026-11-07-persistent-access/verification.json).


## Preparação posterior para Render Free

A dependência de arquivos locais descrita acima foi removida no modo hospedado: fontes, checkpoints e vínculos usam Neon; o hash do revisor vem de variável privada. O comando hospedado recusa SQLite. A validação ocorreu localmente com o Neon real, sem publicar o serviço. Veja [configuração e limites](RENDER.md). O Compose local permanece independente.
