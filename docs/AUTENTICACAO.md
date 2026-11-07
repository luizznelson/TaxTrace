# Acesso local do revisor

Consultar documentos continua sem login. Aprovar ou rejeitar pela interface exige uma conta local de revisor, uma sessão válida e o hash do conjunto revisado. Sem conta configurada, as decisões web ficam bloqueadas. A CLI permanece um canal administrativo local, sob controle de quem acessa o computador.

## Configurar uma vez

Na pasta do projeto, execute:

```powershell
.venv/Scripts/python.exe -m taxtrace.autenticacao --conta revisor --nome "Seu nome"
```

O programa pede a senha duas vezes, sem exibi-la ou colocá-la na linha de comando. Use de 12 a 256 caracteres e não envie a senha pelo chat. A conta aceita letras minúsculas sem acento, números, ponto, hífen e sublinhado; deve começar com letra e ter de 3 a 40 caracteres. O nome pode conter acentos.

Depois, reinicie a aplicação:

```powershell
.venv/Scripts/python.exe -m taxtrace.web
```

Abra **Acesso do revisor**, informe conta e senha e entre. A decisão usa o nome da conta autenticada, não um nome livre enviado pelo navegador. O campo `conta_revisor` registra o identificador da conta e `autenticacao=sessao_local` distingue essa decisão de uma declaração pela CLI. Isso não comprova identidade civil, especialização, independência ou correção fiscal: `identidade_verificada` permanece falso.

## Proteções e limites

- A credencial guarda salt aleatório e hash scrypt (N=16384, r=8, p=1), sem senha em texto puro.
- O arquivo privado é `data/checkpoints/revisor.json`, já excluído do Git. O comando não sobrescreve uma conta existente. Quem controla o computador e esse arquivo pode alterar a conta; preserve as permissões do sistema operacional.
- O token de sessão é aleatório, armazenado somente como hash no servidor e enviado em cookie `HttpOnly`, `SameSite=Strict`, com duração absoluta de uma hora. Em HTTPS, recebe também `Secure`. HTTP é aceito apenas no ambiente local atual. A sessão não é guardada no armazenamento JavaScript.
- Sair invalida a sessão no servidor. Entrar novamente substitui a sessão do navegador. Reiniciar o processo invalida todas as sessões. Há no máximo oito sessões ativas; ao atingir o limite, a mais antiga é descartada.
- Cinco falhas de autenticação acionam espera de 60 segundos para a conta local. Apenas uma verificação de senha é executada por vez. Esses controles são locais ao processo; não substituem proteção distribuída contra abuso.
- Login, saída e decisões mantêm a proteção de origem e CSRF. Nenhuma chamada ao modelo é necessária para autenticar.

Não há cadastro aberto, recuperação por e-mail, múltiplos perfis, MFA ou provedor de identidade externo. O servidor continua limitado a `127.0.0.1`/`localhost`. **Esta entrega não autoriza nem prepara sozinha uma publicação multiusuário.** Antes de expor o serviço, é necessário definir autorização de acesso a consultas e revisões, autenticação adequada ao ambiente público, HTTPS, armazenamento persistente e limites por usuário. As revisões agora têm autorização por sessão do navegador, descrita em [controle de acesso](AUTORIZACAO.md). A conta local de revisor tem acesso administrativo aos registros do ambiente; endpoints de leitura continuam destinados ao computador local.

Para trocar a senha, pare a aplicação, remova manualmente apenas o arquivo `data/checkpoints/revisor.json` e execute o comando de configuração novamente. Não remova checkpoints ou o banco. Reinicie a aplicação para carregar a nova credencial. Não existe troca remota nesta etapa.

Mudanças no código de revisão e autenticação alteram a impressão do código. Revisões históricas continuam acessíveis, mas uma nova decisão exige iniciar uma revisão com a versão atual. Isso preserva a correspondência entre a lógica validada e a decisão registrada.

## Validação

Os testes usam exclusivamente contas e senhas sintéticas em pastas temporárias. Cobrem recusa sem login, nome atribuído pelo servidor, hash com salt, cookie, expiração, logout, reinício, limite de sessões, espera após falhas, origem/CSRF e recusa de configuração inválida. Não representam uma revisão fiscal real nem uma auditoria externa de segurança.


## Credencial por configuração privada

Para um ambiente que perde arquivos locais, o mesmo documento de credencial pode ser fornecido em `TAXTRACE_REVIEWER_CREDENTIAL_JSON`. Gere primeiro a conta pelo comando já descrito; não monte o JSON manualmente e não use a senha como valor da variável. Abra o arquivo privado gerado em um editor e use seu conteúdo apenas na configuração secreta do destino autorizado. Não o envie pelo chat nem o publique no Git.

Se a variável estiver preenchida, ela prevalece sobre `data/checkpoints/revisor.json`. Se estiver ausente ou vazia, o arquivo continua sendo usado. Configuração preenchida mas inválida impede inicialização: não há fallback silencioso para outra conta. A estrutura aceita somente versão, conta, nome, salt e hash; campo de senha em texto puro é recusado. O valor não aparece no contexto público, não é incluído na imagem e não é encaminhado ao processo MCP.

Ao trocar a credencial configurada, reinicie a aplicação. As sessões anteriores são encerradas; a nova credencial precisa ser mantida pelo ambiente de hospedagem. Essa configuração foi testada com dados sintéticos em novas instâncias, sem criar arquivo de conta. Ela não verifica identidade civil ou qualificação e não substitui a validação de HTTPS e dos controles do destino público.
