# Interface local de pesquisa tributária

Uma equipe fiscal precisa localizar a base normativa, conferir seu contexto e deixar claro o que foi revisado. O TaxTrace reúne essas ações em uma bancada de pesquisa, sem gerar parecer fiscal nem afirmar economia de tempo ainda não medida.

## Organização da experiência

- **Pesquisar:** pergunta, exemplos editáveis e escolha explícita entre consulta direta e planejamento com Gemini. Cobertura e ajuda ficam em seções expansíveis.
- **Conferir fontes:** lista selecionável de referências ao lado do leitor. O conteúdo vem da coleta; trechos de busca são identificados e não apresentados como artigos completos. O link oficial permanece disponível.
- **Registrar revisão:** o leitor continua acessível. Em telas maiores, formulário e fonte aparecem lado a lado; em telas pequenas, ficam na sequência de leitura. A navegação permite voltar às fontes sem perder o formulário.
- **Retomar:** histórico da aba e abertura de revisão por identificador. Rastro e JSON técnico ficam recolhidos até serem necessários.

A interface usa tipografia de sistema, superfícies neutras e azul para ações e seleção. Alertas documentais usam âmbar. Não depende de fontes remotas, bibliotecas visuais ou conteúdo externo incorporado.

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

## Conferência e decisão

O botão de revisão e a navegação superior abrem o formulário mantendo os documentos acessíveis. A decisão exige nome declarado, motivo, origem e confirmação de leitura, e usa o hash do conjunto retornado. Origem de teste automatizado não representa revisão humana real. As decisões não validam parecer fiscal.

JSON técnico e exportação estão disponíveis para conferir os registros. Conteúdos vindos da fonte são renderizados como texto, sem interpretar HTML. Links externos aceitam somente HTTPS. Requisições de alteração usam token local e checagem de origem. Entradas são limitadas e mensagens de driver não são expostas. Repetir uma tentativa com a mesma chave reutiliza a tarefa durante a vida do processo, sem garantir idempotência depois de reiniciar o servidor. Há limite de duas consultas simultâneas.

## Verificação desta etapa

As verificações e seus limites estão registrados em [runs/2026-11-06-research-workspace/verification.md](../runs/2026-11-06-research-workspace/verification.md).

A validação visual não substitui auditoria completa de acessibilidade, teste de carga ou segurança para exposição pública. Não houve deploy nem alteração de autenticação. Veja [REVISAO.md](REVISAO.md) para os limites do checkpoint e da identidade autodeclarada.
