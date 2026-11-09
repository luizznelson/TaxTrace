# Validação da revisão autenticada no serviço público

Aplicação: https://taxtrace.onrender.com/

## O que foi executado

1. Sem login, uma consulta de teste foi criada e os resultados, artigo integral e exportação ficaram acessíveis à própria sessão. Outra sessão recebeu HTTP 404 nas três rotas. Uma decisão sem login recebeu 401; token CSRF incorreto recebeu 403. A revisão não foi alterada. Não houve chamada de modelo nesse teste.
2. O usuário autenticou a conta diretamente no navegador. O assistente não acessou a senha, não criou sessão por acesso ao banco e não contornou a autenticação.
3. Pela interface publicada, o assistente consultou o artigo 125 no modo RAG, conferiu o texto integral e as evidências e registrou uma **rejeição de teste**. A justificativa identifica o assistente como executor e afasta parecer fiscal, avaliação profissional ou confirmação de vigência.
4. O JSON foi baixado pelo botão da aplicação. O registro tem uma etapa de síntese, uma de revisão e uma de finalização; não há aprovação humana registrada. O fluxo web rotula a origem como `operador_local`, pois usa a conta autenticada; a justificativa diferencia essa execução assistida de uma revisão fiscal humana.
5. A página foi recarregada, a consulta foi reaberta pelo histórico e a decisão reapareceu. A interface foi conferida em português e inglês, no tamanho padrão estreito do navegador e em 1366 × 900. A mudança de idioma traduz a interface; os textos da lei, resposta e justificativa permanecem no idioma registrado.
6. O logout foi executado e a tela voltou a apresentar o acesso do revisor, mantendo a consulta da própria sessão visível. A dimensão temporária de teste foi removida e o idioma voltou a português.

## Evidências

- `autorizacao.json`: testes HTTP do isolamento entre visitantes e bloqueios de decisão.
- `revisao-autenticada.json`: resumo sanitizado da revisão pela interface, sem senha, cookies ou tokens.
- `revisao-mobile.jpg`: decisão identificada como teste em tela estreita.
- `revisao-desktop-pt.jpg` e `revisao-desktop-en.jpg`: decisão persistida nas duas apresentações.

Datas dos JSON estão em UTC. O nome da pasta segue a data local da execução,
08/11/2026. O exemplo usa uma pergunta conhecida de desenvolvimento e não
constitui avaliação fiscal independente ou prova de qualidade ampla do modelo.
Não foi registrada uma aprovação humana de teste.

## Ajustes encontrados e corrigidos localmente

A mensagem de uma tentativa de login anterior permanecia após o acesso correto.
O formulário passou a limpar o aviso ao iniciar login/logout. Os estados de
consultar, salvar decisão e recuperar revisão agora têm mensagens distintas
em PT/EN. Rótulos e mensagens de falha também deixaram de orientar visitantes
do serviço hospedado a operar um PostgreSQL local.

As capturas mostram a **versão publicada que foi testada**, anterior a esses
ajustes de texto. As correções locais ainda precisam de commit e novo deploy;
não se deve considerar que já estão na hospedagem. Sintaxe JavaScript e os seis
testes de entrada foram conferidos após a alteração. O vídeo continua pendente.
