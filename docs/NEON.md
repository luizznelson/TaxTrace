# Preparação do Neon sem expor credenciais

**Neon preparado e validado em 08/11/2026, conforme o plano autorizado.** Os dois papéis restritos, as tabelas, a captura pública e os checkpoints estão no destino real. Consultas, TLS do cliente, permissões, fontes preservadas e retomada em outro processo foram verificados. **A aplicação foi publicada posteriormente no Render.** Veja [operação](RENDER.md) e [validação hospedada](../runs/2026-11-08-reviewer-hosted/README.md). Veja as [evidências da execução](../runs/2026-11-08-neon-provision/README.md).

## Configuração privada usada na preparação

Abra o projeto TaxTrace no painel Neon, clique em **Connect** e desligue **Connection pooling**. Copie a URI direta e cole apenas na linha `TAXTRACE_NEON_ADMIN_URL=` do arquivo privado `.env.neon` na raiz do projeto. Não envie a conexão pelo chat. Deixe os demais campos como estão.

O arquivo `.env.neon` está fora do Git e do contexto Docker. O modelo sem segredos é `.env.neon.example`. Ele não é carregado automaticamente pelo servidor web, nem ativa o modo remoto.

Depois de salvar e confirmar o preenchimento, o configurador local pode completar os campos:

```powershell
.venv/Scripts/python.exe -m taxtrace.configurar_neon
```

O comando deriva host e banco da URI e gera duas senhas aleatórias distintas quando os campos estão vazios. Senhas existentes são preservadas. Se o painel copiar o invólucro `psql 'URI'`, ele é tratado como texto e retirado, sem executar comandos. O configurador não acessa o Neon e não cria papéis, tabelas ou conexões de runtime. Dados inválidos são recusados antes de modificar o arquivo. Não publique seu conteúdo.

## Restrições do runtime

O modo remoto exige `TAXTRACE_DATABASE_MODE=neon`, host direto explicitamente fixado em `TAXTRACE_NEON_HOST` e banco fixado em `TAXTRACE_NEON_DATABASE`. Os papéis aceitos são somente `taxtrace_reader` para consulta e `taxtrace_state` para checkpoints e autorizações. Hosts diferentes, sufixos falsos, IPs, `hostaddr`, endpoints `-pooler`, papéis administrativos e parâmetros extras são recusados.

As conexões usam `sslmode=verify-full`, CA do pacote `certifi`, mínimo TLS 1.2 e `channel_binding=require`. A opção `require` que pode vir no painel é reforçada para `verify-full`; opções que desabilitam ou reduzem a verificação são recusadas. A confiança não depende de um arquivo CA fornecido na URL. A política foi testada e o transporte TLS do cliente foi confirmado nas conexões reais dos dois papéis. O certificado é verificado por `verify-full`; a estatística SSL do backend não substitui a observação do transporte do cliente.

O host sem pool é necessário porque as revisões usam advisory locks de sessão. O pool transacional não preserva esse recurso. Veja [pooling e suas limitações](https://neon.com/docs/connect/connection-pooling), [segurança do Neon](https://neon.com/docs/connect/connect-securely) e [verificação de certificado no PostgreSQL](https://www.postgresql.org/docs/current/libpq-ssl.html).

O processo MCP recebe apenas conexão de leitura, modo e identificação do destino. Não recebe a conexão administrativa, a de estado, senhas isoladas ou a credencial do revisor. Testes continuam restritos ao banco local isolado. A função administrativa padrão também continua recusando destino remoto: preparar o arquivo privado não autoriza executar migração pela conexão de runtime.

## Fontes disponíveis sem disco local

Novas cargas guardam os seis arquivos de fonte e o manifesto original em `public.fontes_preservadas`, com gzip, tamanho original e SHA-256. A preservação ocorre na mesma transação da carga. O manifesto deve corresponder à coleta e os bytes são conferidos novamente antes da gravação. Registros já existentes não são sobrescritos; divergência aborta a operação. Um arquivo pode ter até 16 MiB descompactados, e a leitura é limitada e conferida antes do uso.

O leitor integral consulta a cópia preservada para verificar âncoras do Planalto. Se o banco antigo não tiver tabela ou captura, o leitor ainda pode usar o arquivo local correspondente. Cópia presente mas corrompida ou com hash divergente produz falha, sem fallback silencioso. Nenhum HTML bruto é servido por uma rota pública nova.

Para um banco local já carregado, a preparação deve ser explícita:

```powershell
.venv/Scripts/python.exe -m taxtrace.banco --somente-esquema
.venv/Scripts/python.exe -m taxtrace.fontes --coleta ID_DA_COLETA --pasta data/raw/2026-11-05
```

Substitua o ID pelo registro correspondente à captura; não copie o exemplo literalmente sem conferir. Esses comandos ainda usam manutenção local. O primeiro prepara a tabela e a leitura restrita; o segundo preserva a captura já existente sem criar outra coleta ou apagar arquivos. Não foram executados contra os dados de desenvolvimento nesta entrega.

## O que foi validado

- Suíte Docker/Linux: 196 testes descobertos, 193 aprovados e três desativados sem coleta oficial no ambiente padrão de integração.
- Testes PostgreSQL reais verificam captura idempotente, leitura sem `data/raw`, bloqueio de escrita pelo leitor, corrupção e divergência do manifesto.
- Em uma verificação adicional, a captura pública de 05/11/2026 foi montada somente para leitura e carregada no banco descartável. Foram preservadas seis fontes mais o manifesto, 6.482.869 bytes originais em 517.414 bytes gzip. O artigo 125 foi lido pelo banco e seu link de âncora foi verificado. A transação foi desfeita ao final.
- Smoke da imagem passou sem root, sem conta ou chaves embutidas e sem chamar modelos.

Esses testes locais não comprovam vigência atual ou adequação fiscal. A validação adicional do destino remoto está registrada separadamente nas evidências de 08/11/2026. A captura conserva a versão V0066 e a data da API original; não representa atualização para hoje. Veja [evidências](../runs/2026-11-07-neon-runtime-preparation/verification.json).

## Próxima etapa

A preparação autorizada e a publicação foram concluídas. A configuração do servidor, variáveis privadas, conta de revisor e limites estão em [RENDER.md](RENDER.md), com evidência hospedada separada do ensaio local. Não enviar a conexão administrativa ao servidor web. O histórico SQLite local não foi migrado. Nenhuma configuração deste documento habilita acesso público automaticamente.


## Planejamento explícito e ensaio

`python -m taxtrace.neon --saida CAMINHO_NOVO.json` consulta o destino somente para leitura e prepara um plano com hashes. Não cria objetos. O parâmetro `--aplicar` exige `--plano-sha256` do plano aprovado, confere novamente as condições e só então executa a preparação. Esse é um canal administrativo explícito; a conexão administrativa não é incluída no runtime e as funções comuns da aplicação continuam recusando manutenção remota.

O [plano preparado](../runs/2026-11-07-neon-preflight/PLANO.md) descreve o destino e as mudanças. O ensaio completo usa `scripts/verify_neon_provisioning.py` em cluster local descartável, com dados e credenciais sintéticos. As fases confirmadas são registradas; falhas não são tratadas como uma preparação integral desfeita automaticamente.


## Verificação operacional do destino real

`scripts/verify_neon_runtime.py` é um comando operacional explícito, fora da suíte
padrão. A fase `leitura` apenas consulta o destino. As fases `iniciar` e `retomar`
criam e encerram uma revisão técnica, identificada como `teste_automatizado`.
Não execute essas fases como monitoramento periódico: elas deixam evidência
persistente no banco. A decisão de teste é uma rejeição, sem aprovação humana
ou parecer fiscal, e não chama modelos externos.

Em 08/11/2026, dois processos Linux separados confirmaram a pausa e a retomada
com MCP real e controle de acesso da sessão persistido. O teste usou imagem
sem privilégios, sistema de arquivos somente leitura e perfil privado montado
somente para leitura fora da imagem. O perfil `.env.neon.runtime` tem formato
**python-dotenv**: carregue-o com `load_dotenv`, ou configure os valores individuais
no serviço de hospedagem. Não o passe diretamente a `docker run --env-file`,
pois esse comando preserva aspas que o formato dotenv usa como delimitadores.
O primeiro ensaio com esse carregamento incorreto foi recusado pela política
de configuração antes de criar a revisão; o teste com dotenv passou.
