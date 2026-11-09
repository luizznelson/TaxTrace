# Plano do TaxTrace

## Decisões já tomadas
- Contexto: Reforma Tributária do consumo (IBS e CBS), por ser recente e ter fontes oficiais públicas.
- Entregas: servidor MCP, agente LangGraph, RAG com citação e vigência, avaliação com gabarito, recusa e guardrails.
- Projeto 4 (separado): monitor no n8n de novos atos, com aprovação humana.

## Prioridade atual e critério de conclusão

RAG com geração de respostas fundamentadas faz parte do escopo original. A primeira versão documental está implementada e avaliada em desenvolvimento; avaliação independente e validação temporal continuam pendentes. A interface de consulta, a recuperação de documentos e a leitura integral não encerram essa entrega. Hospedagem e vídeo não substituem as etapas 3, 5 e 6.

Ordem de trabalho a partir da interface atual:
1. Definir e avaliar suficiência das evidências, casos de recusa e limites de interpretação temporal, antes de habilitar geração para o usuário.
2. Implementar geração limitada aos documentos recuperados, com citações verificáveis, coleta/data identificadas e indicação de evidência insuficiente.
3. Integrar resposta, fontes e revisão humana ao mesmo conjunto registrado, com hash e rastreabilidade. A revisão documental existente não deve ser apresentada como aprovação de uma resposta ainda não implementada.
4. Avaliar respostas, citações e recusas com gabarito, distinguindo conjuntos de desenvolvimento de avaliação independente e registrando a ausência de revisão especializada quando aplicável.
5. Concluir a preparação para acesso público e, depois, publicação, apresentação e vídeo.

Antes de recomendar uma próxima etapa ou afirmar que uma habilidade foi atendida, conferir este plano, o código e as evidências em `runs/` e `evals/`. Distinguir implementação, teste local, avaliação independente e operação publicada. As marcações pendentes abaixo só devem ser concluídas com evidência correspondente.

## Fontes oficiais (levantamento de 05/11/2026)

### Verificado diretamente (acesso em 05/11/2026)
- **API pública de dados abertos da calculadora da Receita**
  - Base: `https://piloto-cbs.tributos.gov.br/servico/calculadora-consumo/api`. Sem login nem chave, resposta JSON.
  - Especificação OpenAPI 3.1 em `/api-docs`, interface em `/swagger-ui/index.html`. São 52 operações; as de dados abertos ficam em `/calculadora/dados-abertos/...`.
  - Versão no momento do teste (`/calculadora/dados-abertos/versao`): app 1.6.2, base V0066 de 28/10/2026, ambiente "apr". Toda resposta do TaxTrace deve citar essa versão e a data de consulta.
  - Testado com `data=2027-01-01`:
    - `classificacoes-tributarias/cbs-ibs`: 170 cClassTrib, com tipo de alíquota, percentuais de redução, indicadores de crédito e tipos de DF-e.
    - `fundamentacoes-legais`: 170 registros ligando cada cClassTrib ao trecho da LC 214 (texto curto e referência normativa).
    - `situacoes-tributarias/cbs-ibs`: 18 CST, cada uma com suas classificações.
    - `ncm/vigentes`: 10.515 NCM vigentes. Há também `ncm`, `nbs`, `nbs/lista`, `classificacoes-tributarias/ncm-aplicavel` e `nbs-aplicavel`, que cruzam NCM/NBS com cClassTrib.
  - `aliquota-uniao?data=2027-01-01` devolveu 404 "alíquota não encontrada". Falta descobrir com que data a alíquota de referência existe.
- **LC 214/2025, texto compilado no Planalto**: https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214.htm (HTML, cerca de 943 mil caracteres).
  - Artigos 1 a 544 e 29 títulos de anexo (ANEXO I a XXIII, mais anexos da LC 123 e outros), todos no mesmo HTML.
  - O compilado já traz as alterações marcadas no texto: 766 anotações da LC 227/2026 e 2 da LC 235/2026 ("Redação dada pela Lei Complementar nº 235, de 2026"), além de 190 "Redação dada" e 543 "Incluído" no total. Serve de base para saber a origem de cada alteração.
  - Há 1 marca "(Vetado)" e a nota "Vide Decreto nº 12.955, de 2026".
  - Conferido que LC 225 e LC 229 não aparecem como alteradoras da LC 214 nesse texto.
- **Comitê Gestor do IBS (cgibs.gov.br)**: seções em HTML estático para `/resolucoes`, `/portarias`, `/atos-conjuntos`, `/atos-tecnicos-conjuntos` e `/legislacoes`. Cada ato tem link direto para PDF em `/upload/arquivos/AAAAMM/...`. Sem feed RSS. A lista de resoluções ia da nº 1 (23/02/2026) à nº 18 (15/09/2026). Base do Projeto 4: coleta por raspagem periódica, comparando a lista com a última leitura.
- **Portal**: https://consumo.tributos.gov.br (rótulo "Beta"), com calculadora online e geração de credencial de API.

### Achados da primeira coleta real (05/11/2026, data=2027-01-01)
- Coletados sem erro: versão, 18 CST, 170 cClassTrib, 170 fundamentos legais e 10.515 NCM. Base V0066 de 28/10/2026.
- `classificacoes-tributarias/cbs-ibs` e `fundamentacoes-legais` têm exatamente os mesmos 170 códigos, 1 fundamento por classificação.
- Divergência da fonte: `situacoes-tributarias/cbs-ibs` lista 173 classificações; as 3 a mais (220001, 220002, 220003, todas da CST 220) não aparecem em `classificacoes-tributarias/cbs-ibs`. A ingestão deve registrar essa diferença, não esconder.
- `dataAtualizacao` é 2026-10-01 em todas as 170 classificações, mais recente que a versão 1.60 (23/06/2026) citada pelas fontes secundárias. Vale a data da API.
- `textoCurto` aponta o artigo em 168 dos 170 casos (ex.: "Art. 10, § 3º", "Arts. 99 e 100"); 2 dizem só "LC 214/2025" (regra geral). O formato não é uniforme ("Art 28, parágrafos 3° e 4°"), então o ligador precisa tolerar variações.
- `referenciaNormativa` traz a hierarquia (livro/título/capítulo) com `\n` literal, não o artigo.
- O download do Planalto foi encerrado pelo servidor (`ConnectionResetError`) com o cliente Python; o coletor agora envia cabeçalhos comuns de navegador e aceita `--lei-arquivo` com o HTML salvo pelo navegador.

### Indicado por fontes secundárias (conferir no original antes de usar)
- **Regulamentos**: Decreto 12.955/2026 (CBS, 29/04/2026, DOU de 30/04) e Resolução CGIBS nº 6/2026 (IBS, 30/04/2026), com Livro I comum aos dois, reconhecido pela Portaria Conjunta MF/CGIBS nº 7/2026. A Resolução CGIBS 13/2026 adiou exigências para pessoas físicas para 01/01/2027. A Resolução CGIBS 17/2026 (30/07/2026) trata de atos técnicos operacionais.
- **Leis que mexem na LC 214**: LC 227/2026 (13/01/2026, Comitê Gestor e procedimentos) e LC 235/2026 (27/08/2026, DOU de 28/08; art. 6º altera a LC 214, ex.: art. 82 e art. 174). Há projetos em tramitação (PLP 18/2026, que altera o art. 127 § 3º), então a lei continuará mudando.
- Tabela cClassTrib no Portal da NF-e (Informe Técnico 2025.002, versões 1.50 de 15/04/2026 e 1.60 de 23/06/2026): https://dfe-portal.svrs.rs.gov.br/DFE/TabelaClassificacaoTributaria. Pode servir de segunda fonte para comparar com a API.
- API do Conformidade Fácil (SVRS): `https://cff.svrs.rs.gov.br/api/v1/consultas/classTrib`.
- Calculadora offline (Java em Docker ou JAR) com a mesma API local. A Receita informou ter repositório no GitHub; o endereço oficial não foi confirmado.
- Cliente Python não oficial `rfbcalc` (PyPI, MIT) confirma a base URL e que não há chave; serve como referência, não como dependência.

### Ainda não verificado
- [ ] Termos de uso e licença da API e do repositório da calculadora (nenhuma página de termos encontrada). Até confirmar: guardar cópia local, citar a fonte e a data, não redistribuir como produto próprio.
- [ ] Limites de uso (taxa de requisições) e se o ambiente "piloto" continua depois de 31/12/2026.
- [ ] Texto oficial do Decreto 12.955/2026, da Resolução CGIBS 6/2026 e da Portaria Conjunta 7/2026, e se entram no escopo da primeira versão.
- [ ] Alíquotas de referência: data e endpoint corretos.
- [ ] Atos novos da Receita Federal (a fonte do lado do CGIBS já está mapeada).

### Consequência para o escopo
- Há dado oficial estruturado, versionado e com data: 170 cClassTrib, fundamentação legal por classificação, 10.515 NCM, 18 CST, mais a lei completa com anexos e alterações marcadas.
- Desenho natural: ingerir a lei por artigo (Planalto) e a API (classificações e fundamentos), ligar as duas pela referência normativa e expor tudo por MCP. Primeira versão só com a LC 214 e a API; regulamentos entram depois.
- Riscos: API em fase piloto, tabelas mudando várias vezes ao ano, lei já alterada e com mais mudanças a caminho. Mitigação: guardar versão e data da consulta em cada resposta e recusar quando a fonte não confirmar.
- Concorrência comercial existe; o diferencial segue sendo MCP, avaliação com gabarito, recusa e vigência.

## Etapas
1. [x] Levantar e registrar as fontes oficiais (URL, data de acesso, licença). Termos de uso e limites da API seguem em aberto (ver acima).
2. [ ] Ingestão com metadados: norma, artigo, data de publicação, vigência, status.
   - [x] Coletor (`python -m taxtrace.coleta --data AAAA-MM-DD`): baixa lei e API para `data/raw/AAAA-MM-DD/` com manifesto (URL, hash, versão da base). Rodado contra os sites reais em 05/11/2026, sem erros (lei: 5,4 MB).
   - [x] Leitor da lei (`taxtrace/lei.py`): validado com o HTML real. Resultado: 580 artigos (1 a 544 sem buraco, 36 com sufixo como 2-A), 35 com texto riscado, 537 anotações "Incluído", 181 "Redação dada", 58 "Revogado", 7 "Vide ADI" e 1 veto. Cabeçalho de artigo riscado abre o artigo e a redação nova se junta a ele.
   - [x] Tabelas da API em estruturas tipadas (`taxtrace/tabelas.py`), com versão da base, data da coleta e lista de divergências da fonte (hoje: 220001, 220002 e 220003).
   - [x] Ligação cClassTrib → artigo (`taxtrace/ligacao.py`): 168 de 170 ligadas, 2 de regra geral (000001 e 000006), nenhum artigo citado ausente da lei, 110 artigos distintos. Alertas de vigência nos artigos ligados: 9 ligações caem em artigo com texto revogado (ex.: 000002→art. 11, 010002→art. 233) e 1 em artigo com "Vide ADI 7779/7790" (200015→art. 149).
   - [x] Banco (Postgres + pgvector): `docker-compose.yml`, `taxtrace/schema.sql` e `taxtrace/banco.py` (`python -m taxtrace.banco`). Cada carga prende tudo a uma coleta (versão da base + data); recarregar a mesma coleta é recusado. Decisão: Docker local para desenvolver, Neon só no deploy. Validado em 06/11/2026 com PostgreSQL local: 580 artigos, 784 alterações, 170 classificações, 169 ligações, 10.515 NCM e 3 divergências. Banco de testes separado, sem TRUNCATE; transações desfeitas ao final. Evidência: `runs/2026-11-06-local-database/verification.json`.
3. [ ] Busca (pgvector) e respostas com citação.
   - [x] Base de comparação: busca textual em português, com artigo, trecho literal, fonte e versão; login somente leitura. 580 documentos pesquisáveis. Sem embeddings ou geração por IA nesta etapa.
   - [x] Avaliação inicial da recuperação: 22 casos (20 positivos e 2 controles), com fragmentos e coleta fixados. Hit@5 de 70% nos positivos; perguntas completas 5/9. Metodologia em `evals/README.md`. Conjunto de desenvolvimento, sem revisão fiscal independente; falhas por variações de termos preservadas.
   - [x] Experimento textual v2: acentos, palavras de formulação e correspondências parciais sinalizadas. Hit@5 de 80% (v1: 70%), com seis ganhos e quatro regressões; v1 mantida como padrão. Comparação em `runs/2026-11-06-search-comparison/comparacao.json`.
   - [x] Tratar regressões e avaliar perguntas adicionais: v4 preserva a ordem v1 e completa vagas. Hit@5 de 95% no conjunto original e 91,7% no adicional, sem perdas contra v1; v4 adotada como padrão. RRF v3 não resolveu as regressões e ficou experimental. Metodologia em `evals/COMPARACAO.md`. O conjunto adicional foi consultado durante a decisão, portanto não é teste independente.
   - [x] Primeira síntese RAG documental: triagem técnica, até uma chamada Gemini, schema e citações literais verificadas, recusa e erros explícitos. Contexto completo de até 8.000 caracteres por artigo e 12.000 por conjunto; sem confirmação de vigência atual. Ver `docs/RAG.md`.
   - [ ] Avaliação independente de recuperação e suficiência dos trechos; ainda sem revisão fiscal especializada.
   - [x] Embeddings e comparação com a busca textual: E5-small local ONNX quantizado, revisão e hashes fixados, 990 trechos/580 artigos, vetores 384D e busca exata pgvector. Recuperação semântica de 60% e 75% nos conjuntos conhecidos, inferior à v4 (95% e 91,7%); controles vazios 0/2 em ambos. Textual mantida como padrão. Ver `evals/SEMANTICA.md`.
   - [x] Experimento de recuperação combinada RRF: 80% e 75% nos conjuntos conhecidos, inferior à textual v4; mantido como opção explícita. Avaliador verifica trechos literais na fonte e presença de âncora do gabarito, separadamente do acerto de artigo. Ver `evals/HIBRIDA.md`.
   - [ ] Avaliar suficiência para resposta e recusa antes de usar os vetores em geração. Âncora literal não comprova suficiência jurídica.
   - [ ] Validar vigência por dispositivo/data; remover trechos riscados do índice não resolve toda a análise temporal.
4. [x] Servidor MCP com as ferramentas de consulta: SDK oficial 2.3.0, stdio local, `consultar_base`, `buscar_artigos`, `ler_artigo` e `consultar_classificacao`. Conexão somente leitura, entradas limitadas, contrato estruturado e erros sanitizados. Cliente/servidor reais verificados em 13 chamadas; ver `docs/MCP.md`. Planejador Gemini integrado pelo fluxo LangGraph (ver etapa 5); cliente desktop e transporte HTTP seguem pendentes.
5. [ ] Agente LangGraph com recusa e aprovação humana.
   - [x] Fluxo de planejamento limitado, consultas MCP reais, conferência de coleta/citações e rastro local. Modo por regras e modo Gemini (gemini-3.5-flash-lite), com três chamadas reais registradas. Até uma requisição de modelo e três chamadas MCP; sem síntese fiscal. Ver `docs/AGENTE.md`.
   - [x] Checkpoint SQLite local e pausa/retomada tipada para revisão documental. Decisão exige hash, origem e motivo; trava por revisão, recusa de decisão duplicada e bloqueio após mudança do código identificado. Retomada sem chamadas MCP/Gemini. Teste entre processos com decisões sintéticas identificado; sem alegar revisão humana real. Ver `docs/REVISAO.md`.
   - [x] Interface local de revisão documental com fontes acessíveis e decisão vinculada ao conjunto exibido.
   - [x] Resposta, contexto, citações e metadados vinculados ao hash da revisão; checkpoint v2 e retomada sem repetir modelo/MCP. Origem sintética identificada nos testes.
   - [x] Conta local de revisor, senha com hash scrypt, sessão expiráveis e decisão com identidade da conta atribuída pelo servidor. Sem conta/sessão, decisões web bloqueadas. Identidade civil e qualificação continuam não verificadas. Ver `docs/AUTENTICACAO.md`.
   - [ ] Autenticação de revisores para exposição pública e revisão fiscal especializada.
   - [x] Critérios de evidência/recusa anteriores ao modelo e gabarito de desenvolvimento de 12 casos; três perguntas de geração real, com falhas preliminares preservadas. Ver `evals/RAG.md`.
   - [ ] Avaliação independente de planejamento, recusa, suficiência e respostas; a triagem técnica não certifica suficiência jurídica.
6. [ ] Conjunto de perguntas com gabarito e avaliação.
   - [x] Primeira avaliação de recuperação de artigos, sem geração de resposta.
   - [x] Gabarito mínimo de respostas/citações e recusas no desenvolvimento: 12/12 triagens e 3/3 positivos após correção. Não independente, sem revisão fiscal; ver `evals/RAG.md`.
   - [x] Avaliação adversarial de saídas: 14 casos, dez bloqueios estruturais esperados e dois limites semânticos explicitados, sem novas chamadas de modelo. Números passam a ser comparados por tokens completos, preservando a identidade dos códigos.
   - [x] Exportação e conferência de pacote para revisão de qualidade, com rubrica, hashes e pendências explícitas. Pacote entregue sem revisor e sem notas; não representa revisão independente realizada.
   - [ ] Revisão por especialista, conjunto independente e avaliação de respostas/citações/recusas.
7. [ ] Interface, Docker, CI, deploy, README e vídeo.
   - [x] Interface local FastAPI com bancada de pesquisa, lista selecionável, leitor de fontes e revisão contextual, PT/EN, histórico da aba, exportação e decisão vinculada ao hash. Teste visual de computador e tela pequena; ver `docs/INTERFACE.md`.
   - [x] Versão, captura e data consultada na API visíveis no painel de cada resposta, com aviso de vigência não confirmada. Essa apresentação não encerra a validação temporal por dispositivo.
   - [x] Diagnósticos separados de processo e base, sem chamadas ao modelo; avaliação adversarial incorporada ao CI com relatório preservado e falha em divergências estruturais. Execução remota ainda precisa ser conferida após o push. Ver `docs/OPERACAO.md`.
   - [x] Autorização de revisões por sessão do navegador: leitura, exportação e fonte vinculada protegidas, idempotência isolada, vínculo persistente e acesso administrativo explícito do revisor. Validado localmente com dados sintéticos; ver `docs/AUTORIZACAO.md`.
   - [x] Pacote Docker local e composição com volumes privados, coleta somente leitura e usuário sem root; configuração Compose validada. Ambiente mínimo de leitura encaminhado ao MCP; disponibilidade de IA considera variáveis do processo.
   - [x] Imagem construída e smoke executado no Docker local após ativação do motor. Suíte Linux com PostgreSQL descartável: 180 aprovados, três desativados sem coleta oficial. CI remoto ainda não verificado; ver `docs/DOCKER.md`.
   - [x] Implementação opcional de checkpoints e eventos PostgreSQL com adaptador oficial, schema e papel separados e trava por revisão. SQLite mantido como padrão; integração real PostgreSQL comprovada na rodada Docker posterior. Ver `docs/PERSISTENCIA.md`.
   - [x] Três testes reais de checkpoints executados em PostgreSQL isolado no Docker/Linux, com retomada entre conexões e trava por revisão.
   - [x] Vínculos PostgreSQL no mesmo backend dos checkpoints, gravação transacional e grants restritos, com quatro integrações reais aprovadas. Credencial de revisor opcional por configuração privada, sem arquivo obrigatório no disco da aplicação.
   - [x] Runtime Neon opt-in com host/banco fixados, TLS verify-full, CA do pacote e canal SCRAM vinculado; manutenção e testes remotos continuam bloqueados. Política testada e conexões reais dos dois papéis verificadas em 08/11/2026.
   - [x] Fontes e manifesto originais preservados com gzip e hashes no PostgreSQL; leitura integral com âncoras sem disco local. Suíte Linux: 193 aprovados e três sem coleta; captura oficial também conferida no banco descartável com rollback. Ver `docs/NEON.md`.
   - [x] Preparar schemas/papéis e importar a captura no projeto Neon autorizado; TLS e permissões dos dois acessos restritos confirmados em 08/11/2026. Pausa e retomada em processos Linux separados, controle de sessão e originais sem disco local verificados. Ver `runs/2026-11-08-neon-provision/README.md`. A hospedagem segue pendente.
   - [x] Configuração Render Free preparada com origem HTTPS explícita, cookies seguros atrás do proxy, um worker, limites globais e prazo de consulta. Ensaio local do comando hospedado com Neon real aprovado; IA pública desabilitada por padrão. Ver `docs/RENDER.md`.
   - [ ] Configurar conta privada de revisor no serviço, validar hospedagem pública, testar IA hospedada e gravar vídeo. Preparação não equivale a deploy.

## Regras do projeto
- Nunca afirmar vigência sem data e fonte.
- Fonte indisponível significa "não consegui verificar", nunca "não há resultado".
- Sem dados pessoais ou sigilosos; catálogo de produtos de demonstração com NCM reais.
