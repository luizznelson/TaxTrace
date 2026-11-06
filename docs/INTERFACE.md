# Interface local de pesquisa tributária

Uma equipe fiscal precisa localizar a base normativa, conferir seu contexto e deixar claro o que foi revisado. O TaxTrace reúne essas ações em uma bancada de pesquisa, sem gerar parecer fiscal nem afirmar economia de tempo ainda não medida.

## Organização da experiência

A navegação fixa tem três áreas, nomeadas pelas tarefas do usuário:

- **Consulta documental:** pesquisar um tema da legislação, abrir um artigo por número ou consultar um cClassTrib com seis dígitos. Cada opção tem campo, orientação e exemplo próprios. Só a pesquisa de temas oferece planejamento por IA; as referências explícitas usam o modo direto. Nenhum NCM é convertido automaticamente em classificação.
- **Revisões da sessão:** lista das últimas dez consultas desta aba, com status e retomada. É possível abrir outro registro local pelo identificador. O histórico da aba não é apresentado como cadastro permanente de usuários.
- **Base e fontes:** cobertura real, versão, datas e conteúdo das fontes. As consultas usam uma coleta, não acesso em tempo real à legislação. Os totais de NCM não significam uma ferramenta de enquadramento disponível.

A abertura explica em linguagem direta o que o TaxTrace pesquisa e entrega. Os exemplos ficam antes do campo: cesta básica, crédito presumido e redução de alíquotas; nas tarefas específicas, artigos 125/126 e cClassTrib 000001. Clicar em um exemplo apenas preenche o campo; o usuário pode editar e precisa acionar Consultar. Os textos da interface têm versão em português e inglês.

Após consultar, o usuário seleciona os documentos para ler o texto e conferir a fonte. Trechos de busca são identificados como parciais. A revisão mantém o leitor acessível e exige decisão, justificativa e confirmação do conjunto documental. Navegar entre áreas ou alternar evidência/revisão preserva os campos ainda não enviados; trocar de idioma mantém o rascunho, mas reinicia a confirmação.

O visual usa navegação lateral persistente, cabeçalho de localização, formulários com rótulos explícitos, hierarquia tipográfica e controles consistentes. Não depende de fontes remotas ou bibliotecas visuais. A entrada explica a utilidade e as entregas, sem prometer cálculo de tributos ou parecer fiscal.

## Referências de interação

Foram consultadas páginas e telas públicas, sem testes nas áreas pagas: [Legora](https://legora.com/product/tabular-review), para relação entre resultado e fonte; [V7 Go](https://www.v7labs.com/changelog/ai-citations), para conferência da evidência; [Elicit](https://support.elicit.com/en/articles/14759154-systematic-reviews-in-elicit), para etapas de revisão; e [Linear](https://linear.app/now/behind-the-latest-design-refresh), para hierarquia visual. São referências de organização, não equivalência de funcionalidades.

## Executar

```powershell
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m taxtrace.web
```

Abra [http://127.0.0.1:8015/](http://127.0.0.1:8015/). PostgreSQL e a coleta precisam estar disponíveis. O servidor aceita somente conexões locais por padrão. Não é uma publicação com autenticação multiusuário.

O modo direto não usa API de IA. A escolha do Gemini envia a pergunta ao planejador configurado. Não há síntese fiscal. A interface tem português e inglês; o texto oficial e os dados da fonte permanecem no idioma original. Para consulta direta, use termos em português ou os exemplos.

O histórico mantém até dez identificadores e perguntas no armazenamento da aba. Recarregar preserva essa lista; os checkpoints ficam no servidor. Também é possível retomar uma revisão pelo UUID. Trocar de idioma preserva os campos de nome e motivo ainda não enviados; a confirmação deve ser marcada novamente.

## Leitura integral e navegação na fonte

O leitor abre o **Artigo integral** preservado em `artigos.texto`: parágrafos, incisos, alíneas e redações riscadas. A pesquisa continua usando seus trechos limitados; a aba **Evidência da consulta** permite conferir exatamente o material recuperado pelo agente.

A leitura complementar usa `GET /api/revisoes/{id}/artigos/{numero}`. O artigo precisa ter aparecido nas respostas ou referências da consulta. A coleta, o manifesto e a fonte devem coincidir com o registro original; a conexão é somente leitura. Textos acima de 200 mil caracteres são recusados com erro, sem truncamento silencioso. A maior extensão da coleta local inspecionada é de 25.082 caracteres. Não há chamada de modelo ou alteração do checkpoint nessa leitura.

Os links oficiais usam âncoras verificadas no HTML de origem pelo hash da fonte (`#art125`, por exemplo). Quando o HTML não tem uma âncora correspondente ou não está disponível localmente, o link tenta um fragmento de texto; o funcionamento depende do navegador e da página oficial. A leitura no app não depende de o Planalto aceitar acesso naquele momento.

O JSON complementar inclui o texto, a estrutura, os hashes, a coleta e a localização oficial. O download separado **Baixar artigo e origem (JSON)** não substitui o registro da revisão. O conjunto original continua identificado pelo mesmo hash; o formulário explicita as evidências vinculadas à decisão e distingue a leitura de contexto. A interface não interpreta HTML da fonte: monta os elementos de texto e de risco explicitamente.

## Conferência e decisão

O botão de revisão e a navegação superior abrem o formulário mantendo os documentos acessíveis. A decisão exige nome declarado, motivo, origem e confirmação de leitura, e usa o hash do conjunto retornado. Origem de teste automatizado não representa revisão humana real. As decisões não validam parecer fiscal.

JSON técnico e exportação estão disponíveis para conferir os registros. Conteúdos vindos da fonte são renderizados como texto, sem interpretar HTML. Links externos aceitam somente HTTPS. Requisições de alteração usam token local e checagem de origem. Entradas são limitadas e mensagens de driver não são expostas. Repetir uma tentativa com a mesma chave reutiliza a tarefa durante a vida do processo, sem garantir idempotência depois de reiniciar o servidor. Há limite de duas consultas simultâneas.

## Verificação desta etapa

A leitura integral e seus limites estão registrados em [integral-reading](../runs/2026-11-06-integral-reading/verification.md).

As verificações desta reorganização estão em [runs/2026-11-06-product-interface/verification.md](../runs/2026-11-06-product-interface/verification.md). A etapa anterior está preservada em [research-workspace](../runs/2026-11-06-research-workspace/verification.md).

Os testes das entradas estruturadas podem ser executados com `node --test tests/query-input.test.mjs` (Node.js 24).

A validação visual não substitui auditoria completa de acessibilidade, teste de carga ou segurança para exposição pública. Não houve deploy nem alteração de autenticação. Veja [REVISAO.md](REVISAO.md) para os limites do checkpoint e da identidade autodeclarada.
