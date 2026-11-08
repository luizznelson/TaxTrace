# Neon: preparação e validação reais

Execução em 08/11/2026, após autorização do usuário. O plano de 07/11 foi
revalidado sem alteração de hash antes da aplicação. Não houve publicação
da aplicação, mudança de cobrança ou migração do histórico SQLite.

## Resultado

- `plano-revalidado.json`: inventário anterior à execução, captura e código vinculados por hash.
- `aplicacao.json`: conclusão do preparador, coleta 1 e criação do runtime privado.
- `leitura.json`: contagens reais, TLS do cliente nos dois papéis, permissões restritas e sete arquivos descompactados com integridade conferida. Leitura integral do artigo 125 com âncora verificada, sem arquivos locais.
- `inicio.json`: pausa no PostgreSQL com ferramentas MCP reais, sem modelo externo.
- `retomada.json`: outro processo Linux recuperou o estado, conferiu a autorização da sessão e registrou rejeição de teste automatizado. Não é aprovação humana ou validação fiscal.

Foram importados 580 artigos, 170 classificações, 169 ligações, 10.515 NCM e
três divergências. As seis fontes e o manifesto original estão preservados.
A captura é de 05/11/2026, V0066, com data da API 01/01/2027; não comprova vigência.

O leitor não escreve fontes nem cria objetos. O papel de estado pode gravar
checkpoints, mas não alterar fontes, criar objetos ou apagar eventos e vínculos.
Os testes de permissões usam os metadados de privilégios do PostgreSQL.

A primeira tentativa de iniciar o runtime usou `docker --env-file` com um arquivo
python-dotenv: as aspas foram preservadas e a configuração foi recusada.
O perfil foi então carregado com `load_dotenv`, montado fora da imagem e somente
para leitura. O Docker também interrompeu a conexão após criar um contêiner;
o estado foi inspecionado e o contêiner existente iniciado, sem duplicar a revisão.

A imagem foi construída em Linux. A suíte anterior do preparador tem 201 testes
descobertos, 198 aprovados e três desativados por falta da captura oficial no
ambiente padrão. Esses números são da execução local anterior; não significam
201 chamadas ao Neon. Esta execução operacional não chamou APIs de modelos.

Próximo marco: preparar a configuração de hospedagem, revisar o acesso do
revisor e verificar o serviço público antes de gravar o vídeo.
