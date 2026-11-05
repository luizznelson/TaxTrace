# Plano do TaxTrace

## Decisões já tomadas
- Contexto: Reforma Tributária do consumo (IBS e CBS), por ser recente e ter fontes oficiais públicas.
- Entregas: servidor MCP, agente LangGraph, RAG com citação e vigência, avaliação com gabarito, recusa e guardrails.
- Projeto 4 (separado): monitor no n8n de novos atos, com aprovação humana.

## Fontes oficiais (levantamento de 05/11/2026)

### Verificado diretamente
- [x] **LC 214/2025, texto compilado**: https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214.htm (HTML, acessado em 05/11/2026). A página tem o texto compilado e a nota "Vide Decreto nº 12.955, de 2026", que ainda precisa ser lido para saber o que muda. Livros, títulos, capítulos e artigos estão em HTML, o que permite dividir por artigo. Falta conferir se os anexos (NCM/NBS por alíquota) estão no mesmo HTML.
- [x] **API pública de dados abertos da calculadora (Receita)**: base `https://piloto-cbs.tributos.gov.br/servico/calculadora-consumo/api`, sem login, resposta JSON. Testado: `GET /calculadora/dados-abertos/situacoes-tributarias/imposto-seletivo?data=2027-01-01` devolveu 7 situações (000 a 600). O endpoint `classificacoes-tributarias/{idSituacaoTributaria}` existe, mas o caminho `situacoes-tributarias/ibs-cbs` deu 404. Os nomes exatos dos demais endpoints saem da documentação Swagger, ainda não aberta.
- [x] **Portal**: https://consumo.tributos.gov.br (rótulo "Beta"), com calculadora online, apuração assistida e geração de credencial de API.

### Indicado por fontes secundárias (conferir no original antes de usar)
- Tabela **cClassTrib/CST/cCredPres**: Informe Técnico 2025.002, publicado no Portal da NF-e. Versões citadas: 1.11, 1.30, 1.50 (15/04/2026) e 1.60 (23/06/2026). Download em https://dfe-portal.svrs.rs.gov.br/DFE/TabelaClassificacaoTributaria (não aberto ainda). Cada linha tem dIniVig/dFimVig e a base legal na LC 214, o que serve direto para o controle de vigência.
- API do Conformidade Fácil (SVRS): `https://cff.svrs.rs.gov.br/api/v1/consultas/classTrib`, JSON, com orientação de uma consulta por dia por empresa.
- A Calculadora da Receita é código aberto e roda local; há repositório da Receita no GitHub (endereço ainda não confirmado) e notas da Release 12 (maio/2026) que ampliaram a API com NBS por vigência, percentuais de redução e transferência de CBS/IBS entre entes.
- Atos do Comitê Gestor/NFS-e são divulgados em gov.br/nfse. Não vi ainda feed RSS ou API para os atos novos.

### Ainda não verificado
- [ ] Documentação Swagger da API (nomes dos endpoints, limites de uso, termos).
- [ ] Licença ou termos de reuso da API e do repositório da calculadora.
- [ ] Download real da tabela cClassTrib e a versão vigente (1.60 ou posterior).
- [ ] Tabela NCM oficial (o Siscomex/Receita publica; fonte e formato não conferidos).
- [ ] Onde e como coletar atos novos da Receita e do Comitê Gestor (Projeto 4).
- [ ] Conteúdo do Decreto nº 12.955/2026 e anexos da LC 214.

### Consequência para o escopo
- Há dado estruturado oficial suficiente para um agente que responde com base legal e vigência: texto da lei por artigo, mais cClassTrib com datas e dispositivo legal.
- Risco a controlar: o portal está em "Beta" e as tabelas mudam várias vezes ao ano, então toda resposta deve citar a versão da tabela e a data consultada.
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
