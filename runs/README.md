# Evidências e histórico de execução

[Visão geral](../README.md) · [Qualidade](../docs/quality.md) · [Avaliações](../evals/README.md)

Este índice organiza as execuções por pergunta e etapa. Os arquivos originais,
inclusive tentativas com falha, foram preservados. Um resultado antigo não foi
reescrito para refletir uma entrega posterior.

## Comece pelas entregas

| Etapa | Registro | O que conferir |
| --- | --- | --- |
| Preparar dados reais | [2026-11-06-local-database](2026-11-06-local-database/verification.json) | Carga, contagens e três divergências preservadas |
| Comparar a busca | [2026-11-06-conservative-search](2026-11-06-conservative-search/comparacao.json) | v4 preserva o prefixo e amplia a cobertura nos conjuntos conhecidos |
| Comparar embeddings | [2026-11-06-semantic-comparison](2026-11-06-semantic-comparison/comparacao.json) | Recuperação experimental; não é geração |
| Comparar busca híbrida | [2026-11-06-hybrid-evidence-comparison](2026-11-06-hybrid-evidence-comparison/comparacao.json) | RRF e qualidade dos trechos; abaixo da textual nesses conjuntos |
| Verificar o protocolo | [2026-11-06-mcp-delivery](2026-11-06-mcp-delivery/verificacao.json) | Cliente/servidor MCP reais, sem precisar de modelo |
| Integrar o fluxo | [2026-11-06-langgraph-delivery](2026-11-06-langgraph-delivery/verificacao.json) | Planejamento e chamadas limitadas |
| Introduzir geração | [2026-11-06-rag-delivery](2026-11-06-rag-delivery/verification.json) | RAG, testes e falhas preliminares; não avaliação independente |
| Preparar persistência | [2026-11-07-persistent-access](2026-11-07-persistent-access/verification.json) | Integrações PostgreSQL e autorização |
| Conferir a imagem | [2026-11-07-neon-runtime-preparation](2026-11-07-neon-runtime-preparation/verification.json) | Fontes preservadas e smoke; etapa anterior ao deploy |
| Preparar Neon real | [2026-11-08-neon-provision](2026-11-08-neon-provision/README.md) | Criação autorizada, TLS, leitura restrita e retomada entre processos |
| Validar para hospedagem | [2026-11-08-render-preparation](2026-11-08-render-preparation/README.md) | 209 testes aprovados e três desativados; não é o deploy |
| Conferir RAG público | [2026-11-08-render-live](2026-11-08-render-live/README.md) | Uma consulta real, citações e revisão recuperada |
| Conferir revisão autenticada | [2026-11-08-reviewer-hosted](2026-11-08-reviewer-hosted/README.md) | Isolamento de sessão, rejeição de teste, exportação, reload e logout |
| Apresentar a jornada | [2026-11-08-demo-video](2026-11-08-demo-video/README.md) | Vídeos PT-BR/EN; cortes e revisão anterior identificados |

## Como interpretar

- `evals/` explica a metodologia; este diretório contém saídas e verificações.
- Um teste de software não é uma medida de precisão jurídica ou produtividade.
- Decisões de teste são identificadas. O registro web atribui a conta autenticada;
  a justificativa informa quando o assistente executou o teste, sem aprovação fiscal.
- Pendências em um JSON histórico descrevem a execução original. Consulte o README
  e os guias atuais para o estado publicado.
- Datas nos JSON podem estar em UTC; nomes de pastas datadas seguem o trabalho local.

## Inventário completo

<details>
<summary>Expandir todas as execuções preservadas</summary>

| Execução | Arquivos versionados |
| --- | ---: |
| [2026-11-06-conservative-search](2026-11-06-conservative-search/comparacao.json) | 1 |
| [2026-11-06-hybrid-evidence-comparison](2026-11-06-hybrid-evidence-comparison/comparacao.json) | 1 |
| [2026-11-06-integral-reading](2026-11-06-integral-reading/verification.md) | 6 |
| [2026-11-06-interface-redesign](2026-11-06-interface-redesign/verificacao.json) | 1 |
| [2026-11-06-langgraph-delivery](2026-11-06-langgraph-delivery/verificacao.json) | 1 |
| [2026-11-06-local-database](2026-11-06-local-database/verification.json) | 1 |
| [2026-11-06-mcp-delivery](2026-11-06-mcp-delivery/verificacao.json) | 1 |
| [2026-11-06-product-interface](2026-11-06-product-interface/verification.md) | 6 |
| [2026-11-06-rag-delivery](2026-11-06-rag-delivery/verification.json) | 9 |
| [2026-11-06-research-workspace](2026-11-06-research-workspace/verification.md) | 4 |
| [2026-11-06-review-delivery](2026-11-06-review-delivery/verificacao.json) | 1 |
| [2026-11-06-search-comparison](2026-11-06-search-comparison/comparacao.json) | 1 |
| [2026-11-06-semantic-comparison](2026-11-06-semantic-comparison/comparacao.json) | 1 |
| [2026-11-06-semantic-verification](2026-11-06-semantic-verification/verificacao.json) | 1 |
| [2026-11-07-container-preparation](2026-11-07-container-preparation/verification.json) | 1 |
| [2026-11-07-evaluation-review](2026-11-07-evaluation-review/verification.json) | 4 |
| [2026-11-07-neon-preflight](2026-11-07-neon-preflight/) | 3 |
| [2026-11-07-neon-runtime-preparation](2026-11-07-neon-runtime-preparation/verification.json) | 5 |
| [2026-11-07-operational-readiness](2026-11-07-operational-readiness/verification.json) | 2 |
| [2026-11-07-persistent-access](2026-11-07-persistent-access/verification.json) | 9 |
| [2026-11-07-postgres-checkpoints](2026-11-07-postgres-checkpoints/verification.json) | 1 |
| [2026-11-07-reviewer-auth](2026-11-07-reviewer-auth/verification.json) | 2 |
| [2026-11-07-session-isolation](2026-11-07-session-isolation/verification.json) | 1 |
| [2026-11-08-demo-video](2026-11-08-demo-video/README.md) | 2 |
| [2026-11-08-neon-provision](2026-11-08-neon-provision/README.md) | 6 |
| [2026-11-08-render-live](2026-11-08-render-live/README.md) | 2 |
| [2026-11-08-render-preparation](2026-11-08-render-preparation/README.md) | 6 |
| [2026-11-08-reviewer-hosted](2026-11-08-reviewer-hosted/README.md) | 6 |
| [agente-0234f4f4-91af-430a-836d-5167054805c4](agente-0234f4f4-91af-430a-836d-5167054805c4/) | 1 |
| [agente-0425d61d-dfe8-44d4-8f9e-b4dec98fcf75](agente-0425d61d-dfe8-44d4-8f9e-b4dec98fcf75/) | 1 |
| [agente-2d837887-79da-4569-9cb3-0100f4a2f53b](agente-2d837887-79da-4569-9cb3-0100f4a2f53b/) | 1 |
| [agente-581c5265-5fd7-4a48-a4da-71a63e15e4c5](agente-581c5265-5fd7-4a48-a4da-71a63e15e4c5/) | 1 |
| [agente-6d10681b-7000-4a2e-92a0-70099d0eb0ad](agente-6d10681b-7000-4a2e-92a0-70099d0eb0ad/) | 1 |
| [agente-b4bfcd9e-6237-4918-8d78-ad85415b1e94](agente-b4bfcd9e-6237-4918-8d78-ad85415b1e94/) | 1 |
| [agente-b647f4a7-579d-4325-99f0-118e2c5a5a33](agente-b647f4a7-579d-4325-99f0-118e2c5a5a33/) | 1 |
| [agente-d20ace41-99c0-4679-8a34-740b22aaf503](agente-d20ace41-99c0-4679-8a34-740b22aaf503/) | 1 |
| [agente-fb43b91c-ce53-47d5-b6ab-8b29f91605c1](agente-fb43b91c-ce53-47d5-b6ab-8b29f91605c1/) | 1 |
| [embeddings-1811bcd6-84d3-45e9-9568-60b61c123077](embeddings-1811bcd6-84d3-45e9-9568-60b61c123077/) | 1 |
| [mcp-b71885d5-c961-47e6-a0f5-bbbf06819b29](mcp-b71885d5-c961-47e6-a0f5-bbbf06819b29/verificacao.json) | 1 |
| [mcp-ffad7503-4c81-491a-b18b-2d6559d41b07](mcp-ffad7503-4c81-491a-b18b-2d6559d41b07/verificacao.json) | 1 |
| [rag-4f177db8-5b2a-4dad-b83c-c1d4a29c20af](rag-4f177db8-5b2a-4dad-b83c-c1d4a29c20af/avaliacao.json) | 1 |
| [rag-833e51f9-97d0-49ab-9bae-b4cf25984c31](rag-833e51f9-97d0-49ab-9bae-b4cf25984c31/avaliacao.json) | 1 |
| [rag-adversarial-7e3f781c-477e-43b3-aac7-75466fa1c808](rag-adversarial-7e3f781c-477e-43b3-aac7-75466fa1c808/avaliacao.json) | 1 |
| [rag-adversarial-c7ee6ed3-225a-4c77-9dcf-a6cfe9dd5146](rag-adversarial-c7ee6ed3-225a-4c77-9dcf-a6cfe9dd5146/avaliacao.json) | 1 |
| [rag-db4649cc-4f9e-45d4-8c68-eacf418d08c1](rag-db4649cc-4f9e-45d4-8c68-eacf418d08c1/avaliacao.json) | 1 |
| [recuperacao-0bcd7d45-6325-492c-9497-ff4ffafbb79a](recuperacao-0bcd7d45-6325-492c-9497-ff4ffafbb79a/resultado.json) | 1 |
| [recuperacao-0d4cb85a-4cca-4417-8d21-43c9aad08529](recuperacao-0d4cb85a-4cca-4417-8d21-43c9aad08529/resultado.json) | 1 |
| [recuperacao-0e794f73-3fd5-4990-9a97-b72e438af345](recuperacao-0e794f73-3fd5-4990-9a97-b72e438af345/resultado.json) | 1 |
| [recuperacao-0ee09d6a-b7fb-49ae-bfd4-a5e15c32dda9](recuperacao-0ee09d6a-b7fb-49ae-bfd4-a5e15c32dda9/resultado.json) | 1 |
| [recuperacao-10b3e641-177c-47eb-be07-e2188d064beb](recuperacao-10b3e641-177c-47eb-be07-e2188d064beb/resultado.json) | 1 |
| [recuperacao-137a3c80-cb35-4071-93b7-1afbb05deec1](recuperacao-137a3c80-cb35-4071-93b7-1afbb05deec1/resultado.json) | 1 |
| [recuperacao-1616278c-b2f3-4291-b628-8d9495333ea2](recuperacao-1616278c-b2f3-4291-b628-8d9495333ea2/resultado.json) | 1 |
| [recuperacao-1724b178-c6c1-4e8a-8588-43b49d49d70f](recuperacao-1724b178-c6c1-4e8a-8588-43b49d49d70f/resultado.json) | 1 |
| [recuperacao-18a55091-77bc-4086-9ad4-6fd43589f5b5](recuperacao-18a55091-77bc-4086-9ad4-6fd43589f5b5/resultado.json) | 1 |
| [recuperacao-1d1e2ba8-5e95-465c-81ee-c9ba82b2ce38](recuperacao-1d1e2ba8-5e95-465c-81ee-c9ba82b2ce38/resultado.json) | 1 |
| [recuperacao-3423b570-ae03-44f6-9113-76e06ca9c1a6](recuperacao-3423b570-ae03-44f6-9113-76e06ca9c1a6/resultado.json) | 1 |
| [recuperacao-385f485a-f361-42a2-b445-0db1a7d10d95](recuperacao-385f485a-f361-42a2-b445-0db1a7d10d95/resultado.json) | 1 |
| [recuperacao-3888034f-1808-464a-8171-abd7df81a161](recuperacao-3888034f-1808-464a-8171-abd7df81a161/resultado.json) | 1 |
| [recuperacao-43d05d3e-34d7-4c55-b234-59c3ad66b014](recuperacao-43d05d3e-34d7-4c55-b234-59c3ad66b014/resultado.json) | 1 |
| [recuperacao-44864da6-a9ac-48ef-97c1-7a9d7da94b3c](recuperacao-44864da6-a9ac-48ef-97c1-7a9d7da94b3c/resultado.json) | 1 |
| [recuperacao-44f11b2e-388a-4906-aa7e-95c87bf6f9b5](recuperacao-44f11b2e-388a-4906-aa7e-95c87bf6f9b5/resultado.json) | 1 |
| [recuperacao-4a4de808-f350-43d0-ba6c-78f04c93b355](recuperacao-4a4de808-f350-43d0-ba6c-78f04c93b355/resultado.json) | 1 |
| [recuperacao-617e87ca-6619-49cb-8926-5a34c69e5e59](recuperacao-617e87ca-6619-49cb-8926-5a34c69e5e59/resultado.json) | 1 |
| [recuperacao-636c1062-b845-42c9-bf61-b332f0489013](recuperacao-636c1062-b845-42c9-bf61-b332f0489013/resultado.json) | 1 |
| [recuperacao-6fee1e49-eb43-46ac-91f6-a7409ee8b64b](recuperacao-6fee1e49-eb43-46ac-91f6-a7409ee8b64b/resultado.json) | 1 |
| [recuperacao-7423a901-02d1-4303-8ece-f974499390b6](recuperacao-7423a901-02d1-4303-8ece-f974499390b6/resultado.json) | 1 |
| [recuperacao-7742a059-3703-47cc-8217-886e2f4191be](recuperacao-7742a059-3703-47cc-8217-886e2f4191be/resultado.json) | 1 |
| [recuperacao-81eca15c-cbc3-4858-b809-a9ef6b2c8af9](recuperacao-81eca15c-cbc3-4858-b809-a9ef6b2c8af9/resultado.json) | 1 |
| [recuperacao-8ca0d900-df8a-4422-b945-67044f504137](recuperacao-8ca0d900-df8a-4422-b945-67044f504137/resultado.json) | 1 |
| [recuperacao-992e45a8-5382-40de-a7d4-3bc12ec106e8](recuperacao-992e45a8-5382-40de-a7d4-3bc12ec106e8/resultado.json) | 1 |
| [recuperacao-b1010301-9f92-4929-8644-3339f89c330b](recuperacao-b1010301-9f92-4929-8644-3339f89c330b/resultado.json) | 1 |
| [recuperacao-c5b697f1-f401-43bf-9cdb-c1023d5488f2](recuperacao-c5b697f1-f401-43bf-9cdb-c1023d5488f2/resultado.json) | 1 |
| [recuperacao-c88fad7e-f028-45ca-a819-409effe771ec](recuperacao-c88fad7e-f028-45ca-a819-409effe771ec/resultado.json) | 1 |
| [recuperacao-d1cdd1f9-4351-495e-8b66-52a1bcd36783](recuperacao-d1cdd1f9-4351-495e-8b66-52a1bcd36783/resultado.json) | 1 |
| [recuperacao-df0dcd6a-99a0-412a-947b-e0c2da38b52e](recuperacao-df0dcd6a-99a0-412a-947b-e0c2da38b52e/resultado.json) | 1 |
| [recuperacao-e087a546-1cc9-43b3-b1af-ce96a37dc67d](recuperacao-e087a546-1cc9-43b3-b1af-ce96a37dc67d/resultado.json) | 1 |
| [recuperacao-f66a97c1-cd27-4b13-90cf-ed53deab936e](recuperacao-f66a97c1-cd27-4b13-90cf-ed53deab936e/resultado.json) | 1 |
| [recuperacao-f70329ba-71bf-4cdb-90e5-4cdbdaf092ae](recuperacao-f70329ba-71bf-4cdb-90e5-4cdbdaf092ae/resultado.json) | 1 |
| [recuperacao-fa65a529-a9e6-465c-b4c3-200c1b3d8d56](recuperacao-fa65a529-a9e6-465c-b4c3-200c1b3d8d56/resultado.json) | 1 |
| [retomada-0f882f55-3f7b-49a6-8f33-cbb7af25f4ea](retomada-0f882f55-3f7b-49a6-8f33-cbb7af25f4ea/verificacao.json) | 1 |
| [revisao-17428445-3436-4899-92d6-6c5992d8eab2](revisao-17428445-3436-4899-92d6-6c5992d8eab2/) | 1 |
| [revisao-206a3144-6a13-43d5-897a-271ec2c97674](revisao-206a3144-6a13-43d5-897a-271ec2c97674/) | 1 |
| [revisao-23fca01d-a21c-492c-afe5-b0a43c79e86b](revisao-23fca01d-a21c-492c-afe5-b0a43c79e86b/) | 1 |
| [revisao-34caffb6-8c5d-43d5-aee3-5164aa7a5e9d](revisao-34caffb6-8c5d-43d5-aee3-5164aa7a5e9d/) | 1 |
| [revisao-3801e5a1-ffe4-4a9a-bf26-1ff73ddab8ea](revisao-3801e5a1-ffe4-4a9a-bf26-1ff73ddab8ea/) | 1 |
| [revisao-3a54fd01-2fd3-4cb1-8f56-67109b8b3338](revisao-3a54fd01-2fd3-4cb1-8f56-67109b8b3338/) | 1 |
| [revisao-3c95d244-2ba9-40b6-8267-b0359416115c](revisao-3c95d244-2ba9-40b6-8267-b0359416115c/) | 1 |
| [revisao-3e56689d-d553-4704-809b-10d3339545bf](revisao-3e56689d-d553-4704-809b-10d3339545bf/) | 1 |
| [revisao-41e9722c-51d0-4da5-a5f8-7ed46b2997d9](revisao-41e9722c-51d0-4da5-a5f8-7ed46b2997d9/) | 1 |
| [revisao-42447c80-26f4-4528-a823-3b9a4395043f](revisao-42447c80-26f4-4528-a823-3b9a4395043f/) | 1 |
| [revisao-4f7c4d10-b69e-456c-bd13-a4b553b73fe6](revisao-4f7c4d10-b69e-456c-bd13-a4b553b73fe6/) | 1 |
| [revisao-52067a7c-cd80-4864-9fc7-808258081b97](revisao-52067a7c-cd80-4864-9fc7-808258081b97/) | 1 |
| [revisao-53207afa-347f-4211-965c-ba6b1ccc2999](revisao-53207afa-347f-4211-965c-ba6b1ccc2999/) | 1 |
| [revisao-577d6794-8fee-4e48-b863-1a44d15ea442](revisao-577d6794-8fee-4e48-b863-1a44d15ea442/) | 1 |
| [revisao-588fd395-a68f-45e2-9fb1-e91e41738a9c](revisao-588fd395-a68f-45e2-9fb1-e91e41738a9c/) | 1 |
| [revisao-5fa88ff6-f269-480b-be14-c7ddef0fe6cf](revisao-5fa88ff6-f269-480b-be14-c7ddef0fe6cf/) | 1 |
| [revisao-64fa83ce-f4a5-481d-ba62-21f7344e60c6](revisao-64fa83ce-f4a5-481d-ba62-21f7344e60c6/) | 1 |
| [revisao-65ffe09b-df0d-4a46-aaf3-76d25f968511](revisao-65ffe09b-df0d-4a46-aaf3-76d25f968511/) | 1 |
| [revisao-67a7fc07-a2b9-4f85-b506-0fd7823fe24b](revisao-67a7fc07-a2b9-4f85-b506-0fd7823fe24b/) | 1 |
| [revisao-69a498f2-e416-4dc7-84b0-9397dec32488](revisao-69a498f2-e416-4dc7-84b0-9397dec32488/) | 1 |
| [revisao-7212c21f-dd1a-4eaf-89df-ece1af9497ed](revisao-7212c21f-dd1a-4eaf-89df-ece1af9497ed/) | 1 |
| [revisao-8c1bd4f9-ab62-4153-83b9-02a7df629519](revisao-8c1bd4f9-ab62-4153-83b9-02a7df629519/) | 1 |
| [revisao-8ecd0dda-a850-4020-912e-47019d748b39](revisao-8ecd0dda-a850-4020-912e-47019d748b39/) | 1 |
| [revisao-91aa84ac-38c8-4521-99bc-be060b0338a0](revisao-91aa84ac-38c8-4521-99bc-be060b0338a0/) | 1 |
| [revisao-92520c55-811f-4cc5-a8b4-562c41e58b11](revisao-92520c55-811f-4cc5-a8b4-562c41e58b11/) | 1 |
| [revisao-99670a9a-a1cf-4d28-9aa2-c42da60ddb9e](revisao-99670a9a-a1cf-4d28-9aa2-c42da60ddb9e/) | 1 |
| [revisao-a19c98c9-cecd-45d7-9d0c-37eef9857be9](revisao-a19c98c9-cecd-45d7-9d0c-37eef9857be9/) | 1 |
| [revisao-a29620d5-8160-4b34-9135-81b2cca21d51](revisao-a29620d5-8160-4b34-9135-81b2cca21d51/) | 1 |
| [revisao-a49960f0-cb8d-4784-874c-2b34bf54d9c5](revisao-a49960f0-cb8d-4784-874c-2b34bf54d9c5/) | 1 |
| [revisao-ad45aa50-3051-4672-99c5-25aba0b70196](revisao-ad45aa50-3051-4672-99c5-25aba0b70196/) | 1 |
| [revisao-ba59389f-8ca9-4d86-801b-9b344feb219d](revisao-ba59389f-8ca9-4d86-801b-9b344feb219d/) | 1 |
| [revisao-ba6378fa-3f96-4936-9388-9497f244e9ce](revisao-ba6378fa-3f96-4936-9388-9497f244e9ce/) | 1 |
| [revisao-ba8420e2-eb80-44a1-90fb-4880a6cfc62e](revisao-ba8420e2-eb80-44a1-90fb-4880a6cfc62e/) | 1 |
| [revisao-bd692c79-2713-450b-8fae-61d36fd4d4b1](revisao-bd692c79-2713-450b-8fae-61d36fd4d4b1/) | 1 |
| [revisao-bed7b387-39ee-4ef8-8b05-5eb32c0be8f6](revisao-bed7b387-39ee-4ef8-8b05-5eb32c0be8f6/) | 1 |
| [revisao-cc85f330-1d14-4264-bd1d-3938902ba9a5](revisao-cc85f330-1d14-4264-bd1d-3938902ba9a5/) | 1 |
| [revisao-ccf956d8-d374-4ad5-ade6-968bc8055b4d](revisao-ccf956d8-d374-4ad5-ade6-968bc8055b4d/) | 1 |
| [revisao-d0e45211-e37e-47ca-83c4-ceba303083fd](revisao-d0e45211-e37e-47ca-83c4-ceba303083fd/) | 1 |
| [revisao-d2b6cd48-36ba-4725-a130-75ae0e85f9d4](revisao-d2b6cd48-36ba-4725-a130-75ae0e85f9d4/) | 1 |
| [revisao-d63cbcb1-bd93-4091-a6eb-3324ea1396d8](revisao-d63cbcb1-bd93-4091-a6eb-3324ea1396d8/) | 1 |
| [revisao-de84ee73-d7bc-4608-9635-7a98437f5399](revisao-de84ee73-d7bc-4608-9635-7a98437f5399/) | 1 |
| [revisao-e2349244-f8ab-468a-934b-843b64eb6edf](revisao-e2349244-f8ab-468a-934b-843b64eb6edf/) | 1 |
| [revisao-e7d5f679-48dd-49ba-acf9-ce8ffd1056cb](revisao-e7d5f679-48dd-49ba-acf9-ce8ffd1056cb/) | 1 |
| [revisao-e98d50c0-1d3d-48b5-8a2f-c74bffd839d2](revisao-e98d50c0-1d3d-48b5-8a2f-c74bffd839d2/) | 1 |
| [revisao-ef53de48-fbee-4448-ad28-7cae43013f9f](revisao-ef53de48-fbee-4448-ad28-7cae43013f9f/) | 1 |
| [revisao-f1d885f8-9865-4dd1-8b6a-14be7cc5c89e](revisao-f1d885f8-9865-4dd1-8b6a-14be7cc5c89e/) | 1 |
| [revisao-f75ccc87-e8b0-44d3-8358-9df065841c80](revisao-f75ccc87-e8b0-44d3-8358-9df065841c80/) | 1 |
| [revisao-fd6068b2-bcbe-4613-bf35-152ff13bb934](revisao-fd6068b2-bcbe-4613-bf35-152ff13bb934/) | 1 |
| [revisao-fed9f6ae-7a83-491a-9b75-56872153e316](revisao-fed9f6ae-7a83-491a-9b75-56872153e316/) | 1 |

</details>

Prefixos `recuperacao-`, `rag-`, `agente-`, `mcp-` e `revisao-` identificam
execuções individuais. Pastas datadas sintetizam entregas e apontam para esses
registros. Nenhum prefixo representa uma certificação automática de qualidade.
