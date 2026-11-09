# Publicar o TaxTrace no Render Free

O banco Neon foi preparado e validado. Esta etapa prepara o **servidor web**;
o `render.yaml` não cria outro banco, não importa fontes e não altera papéis.
O serviço foi publicado em [taxtrace.onrender.com](https://taxtrace.onrender.com/) e uma consulta RAG real foi validada, com revisão persistida. A conta de revisor ainda precisa de configuração. Veja [evidências públicas](../runs/2026-11-08-render-live/verification.json). O ensaio local do comando de hospedagem
com o Neon real está em [evidências](../runs/2026-11-08-render-preparation/README.md).

## 1. Enviar a versão revisada

Faça o commit e envie ao repositório `luizznelson/TaxTrace`, na branch `main`.
O Blueprint usa Docker, plano Free e atualização manual. Não cria discos,
serviços auxiliares ou bancos pagos. Para atualizar depois, publique um novo
commit e escolha o deploy manual no painel.

## 2. Configurar o serviço

No [Render](https://dashboard.render.com/), selecione **New → Blueprint** e o
repositório TaxTrace. Confira o plano **Free**, o nome `taxtrace`, a região e
as mudanças propostas antes de aplicar. Se o nome gerar um subdomínio com
sufixo, a origem é derivada do hostname atribuído pelo Render; não precisa
adivinhar o endereço no código.

Os quatro valores pedidos pelo Blueprint estão no arquivo privado
`.env.render`, já preparado neste computador. Copie cada **valor** para a
variável correspondente no painel, sem adicionar aspas. O arquivo não é
commitado nem incluído na imagem. Nunca inclua `DATABASE_URL`,
`TAXTRACE_NEON_ADMIN_URL` ou o perfil administrativo `.env.neon` no serviço.

| Variável | Finalidade |
| --- | --- |
| `TAXTRACE_NEON_HOST` | Host direto, sem `-pooler`, já validado |
| `TAXTRACE_NEON_DATABASE` | Banco exclusivo do TaxTrace |
| `TAXTRACE_READER_DATABASE_URL` | Conta que apenas consulta as fontes |
| `TAXTRACE_CHECKPOINT_DATABASE_URL` | Conta restrita de checkpoints e autorizações |

Modo Neon e backend PostgreSQL já estão no Blueprint. A porta vem de `PORT`.
O comando é `python -m taxtrace.servir`, com um único worker, sem confiar em
cabeçalhos `X-Forwarded-*` enviados pelo visitante. A origem HTTPS esperada é
fixada pela configuração do serviço, separadamente do HTTP interno do proxy.
Cookies de sessão pública são `Secure`, `HttpOnly` e `SameSite=Strict`.

O comando recusa SQLite, destino remoto inválido e variável administrativa
no ambiente antes de iniciar. A preparação não migra o histórico SQLite.

## 3. Conferir o primeiro deploy

A busca direta funciona sem modelo externo. A IA pública começa desabilitada
por configuração. Isso permite conferir conexão e sessão antes de expor a chave
à utilização pública; a chave nunca é enviada ao navegador.

- `/health/live`: processo ativo, sem consultar banco ou modelo. É o health check do Render.
- `/health/ready`: leitura da base, sem gastar cota de modelo. Deve responder `pronto`.
- Na interface, abra a busca direta e consulte `artigo 125`.
- Abra o texto completo, confira fonte, coleta e link do artigo; atualize a página e recupere a revisão pelo histórico da mesma aba.
- Em outra sessão do navegador, a revisão privada não deve ser acessível pelo ID.

O histórico visual pertence à aba. Checkpoints e vínculos estão no Neon, mas
uma sessão de revisor em memória termina quando a instância reinicia.
Mudanças no código identificado do fluxo podem exigir iniciar outra revisão.

## 4. Ativar o modelo e o revisor

Para disponibilizar o planejador e o RAG, adicione nas variáveis do serviço
`GEMINI_API_KEY` e o `GEMINI_MODEL` usados na configuração local; `GEMINI_RAG_MODEL`
é opcional. Os valores privados já foram copiados para `.env.render` quando
existentes. Depois altere `TAXTRACE_PUBLIC_AI_ENABLED` para `true`, salve e teste
uma consulta com IA. A busca direta continua disponível sem chamada ao modelo.
Verifique as cotas e a configuração de cobrança da conta do provedor: o
controle da aplicação não constitui garantia financeira ou gratuidade da API.

Não há uma conta de revisor criada nesta preparação. Para habilitar decisões,
crie uma conta no computador, pelo comando interativo abaixo, com sua própria
senha. A senha não aparece no comando nem é enviada ao chat:

```powershell
.venv/Scripts/python.exe -m taxtrace.autenticacao --conta revisor --nome "Seu nome"
```

Copie o **conteúdo JSON** de `data/checkpoints/revisor.json` para a variável privada
`TAXTRACE_REVIEWER_CREDENTIAL_JSON` do Render. É um hash com salt, não uma senha
em texto puro, e ainda deve ser tratado como segredo. Não envie esse arquivo
para o Git. Sem essa configuração, os visitantes podem pesquisar, mas as decisões
permanecem bloqueadas. A conta tem acesso administrativo às revisões deste
ambiente; não compartilhe sua senha como credencial de demonstração.

Login não comprova identidade civil ou qualificação fiscal. O resultado continua
sendo apoio documental e não parecer tributário ou vigência validada.

## Limites da instância

- Até duas consultas simultâneas; prazo de até 60 segundos para preparar uma consulta.
- Até 60 novas consultas por hora no total; no máximo 20 delas usando IA.
- Limites globais por processo, em memória: reinício zera a contagem. Não são cota mensal, controle financeiro nem proteção distribuída.
- Uma tentativa idempotente ainda presente no cache reutiliza a tarefa, sem reservar nova cota; o cache é limitado e não atravessa reinícios.
- Não aumente o número de workers ou réplicas sem substituir limites e sessões por armazenamento compartilhado.
- Solicitações recusadas por limite recebem HTTP 429 e `Retry-After`; a interface explica a espera em PT/EN.

O Free suspende o serviço após 15 minutos sem tráfego. O primeiro acesso pode
levar cerca de um minuto para reativar. As 750 horas gratuitas mensais são
compartilhadas pelos serviços Free do workspace. Arquivos locais são efêmeros;
por isso o TaxTrace usa o Neon e não SQLite na hospedagem. O Free serve para
demonstração com limitações de capacidade, sem promessa de disponibilidade.

Se uma chave for exposta, revogue-a no provedor e substitua-a no painel. Para
interromper chamadas de IA, configure `TAXTRACE_PUBLIC_AI_ENABLED=false`; isso
preserva a busca direta. Suspender o serviço interrompe o acesso ao app sem
apagar o banco Neon. Não execute o preparador administrativo como start command.

## Reprodução da configuração privada

`python -m taxtrace.preparar_render` gera `.env.render` a partir do runtime Neon,
com lista permitida de variáveis e sem copiar a conexão administrativa. Inclui
modelo e hash do revisor somente quando já configurados localmente. O comando
não acessa o Render, não configura cobrança e não sobrescreve arquivo existente.
O `.env.render` tem linhas de ambiente sem aspas delimitadoras; o perfil
`.env.neon.runtime` usa python-dotenv. São formatos distintos: não passe o perfil
Neon diretamente a `docker --env-file`.

## Referências

- [Web Services e terminação TLS](https://render.com/docs/web-services)
- [Blueprint: Docker, variáveis privadas e deploy manual](https://render.com/docs/blueprint-spec)
- [Limites do plano gratuito](https://render.com/docs/free)
