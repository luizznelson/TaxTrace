# Diagnóstico e avaliação automática

O diagnóstico distingue duas situações: o processo responde, mas a base pode estar indisponível. Assim, uma falha de conexão não é apresentada como ausência de informação na lei.

## Diagnóstico local

Com a aplicação iniciada, abra:

- `http://127.0.0.1:8015/health/live`: retorna HTTP 200 quando o processo atende requisições. Não consulta banco ou modelo.
- `http://127.0.0.1:8015/health/ready`: retorna HTTP 200 apenas quando a conexão somente leitura consegue consultar a coleta e há artigos carregados. Sem isso, retorna HTTP 503 e `base_indisponivel`.

O segundo diagnóstico usa as mesmas verificações de papel de leitura e coleta da aplicação. Não devolve credenciais, mensagens internas, fontes ou contagens. Não faz chamadas Gemini nem verifica sua disponibilidade. Não verifica escrita de checkpoints, integridade de todos os documentos, correção das respostas ou vigência jurídica. Portanto, `pronto` significa apenas que a consulta de diagnóstico à base funcionou.

Os dois caminhos respeitam a restrição de host local e os cabeçalhos de segurança. Esta etapa não habilita acesso público nem autentica revisores.

## Avaliação no GitHub

O fluxo `Quality` executa os casos adversariais salvos em cada push ou pull request. O processo falha se o comportamento estrutural observado divergir do esperado. Ele não chama modelos, não usa chaves de API e não precisa da coleta real.

O JSON é disponibilizado como artefato `rag-adversarial-<execução>-<tentativa>`, por 30 dias. Se a avaliação produzir um relatório de falha, o envio do artefato também é tentado. Se uma etapa anterior impedir a geração, o fluxo avisa sobre a ausência do arquivo; não fabrica evidência. Somente esse JSON é enviado, sem `.env`, checkpoints ou logs locais. A execução remota precisa ser conferida na aba Actions depois do push; preparar o fluxo não comprova que ele já executou no GitHub.

Para reproduzir localmente e guardar um registro em um caminho novo:

```powershell
.venv/Scripts/python.exe -m taxtrace.avaliar_adversarial --saida runs/minha-validacao/avaliacao.json
```

O comando recusa sobrescrever um arquivo existente. Sem `--saida`, continua criando uma pasta identificada automaticamente em `runs/`.

Os 14 casos atuais incluem dez bloqueios estruturais, dois controles válidos e dois limites semânticos conhecidos. Obter o comportamento esperado nesses casos não representa 100% de acurácia, revisão fiscal ou segurança contra todos os ataques. Veja a [metodologia](../evals/RAG.md) e a [revisão ainda pendente](REVISAO_AVALIACAO.md).
