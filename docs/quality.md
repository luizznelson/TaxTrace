# Qualidade — o que foi testado e o que foi medido

[Visão geral](../README.md) · [Arquitetura](architecture.md) · [Reprodução](development.md) · [Evidências](../runs/README.md)

Um teste de contrato, uma referência recuperada e uma conclusão tributária correta
são resultados diferentes. O projeto mantém essas verificações separadas.

## Evidências por pergunta

| Pergunta | Verificação disponível | Evidência |
| --- | --- | --- |
| O software mantém seus contratos em Linux/PostgreSQL? | Última suíte completa registrada: 212 descobertos, 209 aprovados e três desativados sem captura oficial; seis testes Node | [Resumo](../runs/2026-11-08-render-preparation/verification.json), [saída da suíte](../runs/2026-11-08-render-preparation/integration.txt) |
| A busca localiza a referência esperada? | v4: 19/20 e 11/12 casos positivos no top 5; dois controles sintéticos por conjunto separados | [Comparação](../evals/COMPARACAO.md) |
| Embeddings justificam trocar o padrão? | Semântica: 12/20 e 9/12; híbrida: 16/20 e 9/12, abaixo da textual nesses conjuntos | [Semântica](../evals/SEMANTICA.md), [híbrida](../evals/HIBRIDA.md) |
| A síntese atende ao gabarito mínimo? | Primeira rodada 2/3; após correção, 3/3 casos positivos. Triagem de 12 casos e falhas preservadas | [RAG](../evals/RAG.md) |
| Os bloqueios estruturais têm limites conhecidos? | 14 casos adversariais: dez rejeições esperadas, dois controles válidos e dois limites semânticos explícitos | [Método adversarial](../evals/RAG.md#avaliação-adversarial-posterior) |
| A imagem funciona sem credenciais embutidas? | Processo, cabeçalhos, usuário sem root e ausência de segredos na imagem | [Smoke](../runs/2026-11-08-render-preparation/container-smoke.json) |
| O estado sobrevive fora do disco efêmero? | Pausa/retomada em processos Linux distintos, originais no Neon e papéis restritos conferidos | [Neon real](../runs/2026-11-08-neon-provision/README.md) |
| A hospedagem permite conferir a jornada? | RAG real, exportação, rejeição autenticada de teste, recuperação após reload e logout | [Revisão publicada](../runs/2026-11-08-reviewer-hosted/README.md) |

Os números da suíte identificam uma execução registrada; não são um contador
atualizado automaticamente. O badge do GitHub reflete o workflow remoto. A CI
configurada não comprova, por si só, que uma execução remota já foi conferida.

## Interpretação da avaliação de IA

Os gabaritos foram usados durante o desenvolvimento. Não há conjunto independente,
revisão fiscal especializada ou amostra de usuários. Métricas de recuperação
avaliam a localização de artigos, não a correção da explicação ou sua suficiência.

A v4 mantém o prefixo da v1. Por isso não perde os mesmos acertos no mesmo recorte,
mas também não melhora sua ordem quando já há resultados suficientes. As perguntas
adicionais foram observadas durante a escolha do método; não são teste reservado.

A checagem literal de citações é necessária, mas não suficiente. Uma saída pode
citar números presentes e ainda relacioná-los incorretamente. Os dois controles
semânticos não contam como respostas corretas. [Rubrica especializada ainda sem
notas independentes](REVISAO_AVALIACAO.md).

## Separação dos ambientes

- Testes padrão não chamam APIs de modelos nem usam a conta Neon da aplicação.
- Integrações exigem opt-in e o destino de teste local dedicado, não uma URL de
  desenvolvimento como alternativa. Casos de banco usam transações e UUIDs próprios.
- A integração Linux usa PostgreSQL descartável, sem portas públicas e com dados
  sintéticos; a captura oficial é uma verificação adicional explícita.
- Verificadores Neon são comandos operacionais: fases que criam revisão deixam
  estado no destino. Não são testes a executar automaticamente contra produção.

## Reproduzir

Com o ambiente local preparado, siga [desenvolvimento](development.md#verificações).
A sequência do CI está em [quality.yml](../.github/workflows/quality.yml): testes
Python e Node, Ruff, avaliação adversarial salva e smoke da imagem em job separado.
O job não recebe a chave de modelo da aplicação.

Preserve falhas e resultados anteriores. Atualizar um gabarito exige justificar
o motivo; não se altera a referência apenas para transformar uma falha em acerto.
Nenhum resultado desta página certifica vigência, enquadramento fiscal, segurança
absoluta, capacidade sob carga ou produtividade de uma equipe.
