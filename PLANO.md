# Plano do TaxTrace

## Decisões já tomadas
- Contexto: Reforma Tributária do consumo (IBS e CBS), por ser recente e ter fontes oficiais públicas.
- Entregas: servidor MCP, agente LangGraph, RAG com citação e vigência, avaliação com gabarito, recusa e guardrails.
- Projeto 4 (separado): monitor no n8n de novos atos, com aprovação humana.

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
  - `aliquota-uniao?data=2027-01-01` devolveu 404 "alíquota não encontrada". Falta descobrir com que data a alíquota de referência existe antes de usá-la.
  - Todos os endpoints têm parâmetro de data, o que permite consulta por vigência.
- **LC 214/2025, texto compilado**: https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214.htm (HTML). A página remete ao Decreto nº 12.955/2026. Falta conferir se os anexos vêm no mesmo HTML.
- **Portal**: https://consumo.tributos.gov.br (rótulo "Beta"), com calculadora online e geração de credencial de API.

### Indicado por fontes secundárias (conferir no original antes de usar)
- **Normas que alteram ou regulamentam a LC 214**: Decreto 12.955/2026 (Regulamento da CBS) e Resolução CGIBS nº 6/2026 (Regulamento do IBS), ambos de 29/04/2026; LC 227/2026 (13/01/2026, Comitê Gestor); LC 235/2026 (27/08/2026), cujo art. 6º altera a LC 214 (arts. 82 e 174, entre outros). A LC 214 já foi emendada, então o controle de vigência é requisito real, não enfeite.
- Tabela cClassTrib no Portal da NF-e (Informe Técnico 2025.002, versões 1.50 de 15/04/2026 e 1.60 de 23/06/2026): https://dfe-portal.svrs.rs.gov.br/DFE/TabelaClassificacaoTributaria. Pode ser comparada com a API como segunda fonte.
- API do Conformidade Fácil (SVRS): `https://cff.svrs.rs.gov.br/api/v1/consultas/classTrib`.
- Calculadora offline (Java, Docker ou JAR) com a mesma API local. Há repositório da Receita no GitHub, ainda sem endereço confirmado.
- NCM no Portal Único Siscomex (JSON público). Fica como alternativa; a API da Receita já entrega as NCM vigentes por data.
- Atos do Comitê Gestor do IBS e da NFS-e saem em gov.br/nfse. Sem feed identificado ainda.

### Ainda não verificado
- [ ] Termos de uso e licença da API e do repositório da calculadora.
- [ ] Limites de uso da API (taxa de requisições) e se o ambiente "piloto" continua depois de 31/12/2026.
- [ ] Texto oficial do Decreto 12.955/2026, da Resolução CGIBS 6/2026, da LC 227/2026 e da LC 235/2026, e se entram no escopo.
- [ ] Anexos da LC 214 no HTML do Planalto (listas de NCM por alíquota).
- [ ] Onde coletar atos novos da Receita e do Comitê Gestor de forma automática (base do Projeto 4).
- [ ] Alíquotas de referência: data e endpoint corretos.

### Consequência para o escopo
- Há dado oficial estruturado, versionado e com data de vigência: 170 cClassTrib, fundamentação legal por classificação, 10.515 NCM, 18 CST.
- Desenho natural: ingerir a lei por artigo (Planalto) e a API (classificações e fundamentos), ligar as duas pela referência normativa e expor tudo por MCP.
- Riscos: portal e API em fase Beta/piloto, tabelas mudando várias vezes ao ano, e a lei já alterada. Mitigação: guardar versão e data da consulta em cada resposta e recusar quando a fonte não confirmar.
- Concorrência comercial existe; o diferencial segue sendo MCP, avaliação com gabarito, recusa e vigência.

## Etapas
1. [ ] Levantar e registrar as fontes oficiais (URL, data de acesso, licença).
2. [ ] Ingestão com metadados: norma, artigo, data de publicação, vigência, status.
3. [ ] Busca (pgvector) e respostas com citação.
4. [ ] Servidor MCP com as ferramentas de consulta.
5. [ ] Agente LangGraph com recusa e aprovação humana.
6. [ ] Conjunto de perguntas com gabarito e avaliação.
7. [ ] Interface, Docker, CI, deploy, README e vídeo.

## Regras do projeto
- Nunca afirmar vigência sem data e fonte.
- Fonte indisponível significa "não consegui verificar", nunca "não há resultado".
- Sem dados pessoais ou sigilosos; catálogo de produtos de demonstração com NCM reais.
