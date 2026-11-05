# Plano do TaxTrace

## Decisões já tomadas
- Contexto: Reforma Tributária do consumo (IBS e CBS), por ser recente e ter fontes oficiais públicas.
- Entregas: servidor MCP, agente LangGraph, RAG com citação e vigência, avaliação com gabarito, recusa e guardrails.
- Projeto 4 (separado): monitor no n8n de novos atos, com aprovação humana.

## Ainda não verificado (decide o escopo)
- [ ] Texto oficial da LC 214/2025 em formato utilizável e sua licença de reuso.
- [ ] Tabelas oficiais de CST e cClassTrib em formato estruturado (planilha/API).
- [ ] Tabela NCM oficial.
- [ ] Atos recentes da Receita/Comitê Gestor: onde são publicados e se dá para coletar.
- [ ] Calculadora da Receita: se há API pública utilizável.

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
