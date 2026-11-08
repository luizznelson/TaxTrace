# Plano de preparação do Neon do TaxTrace

O destino é o banco `neondb` do projeto indicado no arquivo privado `.env.neon`. A verificação usou conexão direta com TLS `verify-full`, certificado validado pelo cliente e consulta somente leitura. O banco não contém tabelas de aplicação e os dois papéis de runtime ainda não existem.

## Alterações propostas

1. Criar `taxtrace_reader`, com leitura das fontes e sem privilégios administrativos.
2. Criar `taxtrace_state`, restrito aos checkpoints e vínculos; eventos e autorizações sem UPDATE/DELETE concedidos ao papel.
3. Preparar a extensão `vector`, as tabelas de fontes e o schema separado `taxtrace_workflow`.
4. Importar a captura de 05/11/2026: 580 artigos, 170 classificações e 10515 NCM, com as ligações e divergências preservadas. A base é V0066, consultada na API para 01/01/2027; isso não comprova vigência atual.
5. Preservar os seis arquivos de fonte e o manifesto original no banco, com hashes.
6. Gerar apenas no computador o arquivo privado `.env.neon.runtime`, sem a conexão administrativa, para a futura configuração da aplicação.

Não serão alterados bancos locais de desenvolvimento, substituídos papéis existentes, migrados históricos SQLite, publicados serviços ou contratados recursos. O aplicador recusa destino que deixe de estar vazio, plano com hash divergente ou arquivo privado de runtime já existente.

## Validação concluída

O preparador foi ensaiado em outro cluster PostgreSQL descartável: criou os dois papéis, importou dados sintéticos, preservou sete arquivos, preparou o estado e conferiu as permissões e a ausência da credencial administrativa no runtime. A suíte completa em Linux passou com 198 testes aprovados e três desativados por ausência da coleta oficial na suíte padrão. O teste não modificou o Neon.

O preflight remoto confirmou TLS no cliente libpq. A estatística `pg_stat_ssl` do backend retornou SSL falso e não foi usada como prova do transporte do cliente; os dois valores estão separados no JSON do plano.

## Controle de aplicação

Hash do plano: `c32aaec5a5b934a46dd7a335fb28078936e361144e9cd5b9b4c7ef398aa01afd`.

O JSON liga destino, captura e código. Se qualquer condição vinculada mudar, o plano precisa ser refeito antes da aplicação. Há transações separadas para carga das fontes e migrações de estado; uma falha na segunda etapa pode deixar a carga concluída, e a ferramenta interrompe sem repetir ou sobrescrever automaticamente. Não há exclusão automática para simular rollback completo de etapas já confirmadas.

**Situação na emissão (07/11): plano pronto, aplicação remota ainda não executada.**

Atualização de 08/11/2026: o usuário autorizou a aplicação, o hash foi revalidado sem alterações e a preparação foi concluída. Ver [resultado e verificações reais](../2026-11-08-neon-provision/README.md). O texto acima preserva as condições anteriores à aplicação.
