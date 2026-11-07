# Revisão de qualidade das respostas

Este fluxo prepara material para outra pessoa avaliar. **Exportar um pacote não realiza nem comprova revisão especializada ou independente.** O pacote entregue está com os 12 casos pendentes e sem nome de revisor.

## O que conferir

Cada caso apresenta a pergunta, a resposta ou recusa e o contexto identificado. A rubrica pede seis verificações: coerência com as fontes, preservação de condicionantes, suficiência das citações, adequação da recusa, respeito aos limites temporais e clareza.

Para cada critério, use `atende`, `nao_atende`, `nao_aplicavel` ou `pendente`. Não marque um caso como correto apenas porque o trecho foi copiado literalmente. Uma data presente na fonte, por exemplo, não sustenta automaticamente um prazo de igual número de dias.

Uma reprovação exige justificativa. Um caso inteiro como `nao_aplicavel` não conta como avaliação concluída. Nome, qualificação e origem são declarados; não há autenticação nem verificação dessas informações. Testes devem indicar origem `teste_automatizado`.

## Pacote pronto

- [Pacote ainda não preenchido](../runs/2026-11-07-evaluation-review/pacote-pendente.json)
- [Conferência: 12 pendentes, nenhuma revisão comprovada](../runs/2026-11-07-evaluation-review/conferencia-pendente.json)

O material é da rodada de desenvolvimento já registrada. Avaliá-lo depois não o transforma em conjunto de teste independente: a autoria dos casos, seu uso nos ajustes e a identidade do avaliador precisam ser considerados separadamente.

## Uso

```powershell
.venv/Scripts/python.exe -m taxtrace.revisao_avaliacao exportar --execucao runs/rag-db4649cc-4f9e-45d4-8c68-eacf418d08c1/avaliacao.json --saida pacote-novo.json
```

Edite somente `revisor`, `notas` e `observacoes` em uma cópia. Não altere perguntas, respostas, contexto ou hashes. Quando começar a avaliar, preencha `revisor` assim, com dados adequados e autorizados:

```json
{
    "nome": "Nome declarado",
    "qualificacao_declarada": "Descrição da qualificação e dos limites da revisão",
    "origem": "pessoa_nao_verificada"
}
```

Para conferir:

```powershell
.venv/Scripts/python.exe -m taxtrace.revisao_avaliacao conferir --execucao runs/rag-db4649cc-4f9e-45d4-8c68-eacf418d08c1/avaliacao.json --pacote pacote-preenchido.json --saida resultado-novo.json
```

A conferência recusa outra execução, material trocado, caso duplicado, rubrica inválida ou reprovação sem justificativa. Os arquivos de saída precisam ser novos, para preservar registros anteriores. Mesmo um pacote preenchido não libera publicação automaticamente nem comprova independência, especialização ou vigência jurídica.

Não inclua dados pessoais desnecessários nem publique a identificação de terceiros sem autorização. Nenhum material é enviado por email ou serviço externo por esta ferramenta.
