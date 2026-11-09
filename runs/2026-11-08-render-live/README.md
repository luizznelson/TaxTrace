# TaxTrace publicado: verificação operacional

Endereço: https://taxtrace.onrender.com/

A interface, o processo e a leitura da base responderam HTTP 200. Cookies
seguros e HSTS foram observados. Depois da configuração da IA, uma consulta
RAG conhecida gerou resposta com citação literal A125, usando uma chamada real
ao Gemini. A revisão ficou pendente e foi recuperada na mesma sessão com o
mesmo hash do dossiê. Nenhuma aprovação humana foi realizada.

O planejamento dessa pergunta explícita foi feito por regras; a chamada ao
modelo foi de síntese. Isso não comprova o planejador Gemini em perguntas
abertas, vigência jurídica, qualidade ampla ou avaliação fiscal independente.
O teste é operacional por HTTP, sem revisão visual do navegador.

A conta de revisor continua sem configuração no serviço. Próximos passos:
configurar o hash privado, testar login e decisão, revisar a apresentação no
navegador e gravar o vídeo. Não publicar cookies, chaves ou conexões.

`verification.json` contém o resumo sanitizado das observações. As requisições
foram executadas por script local; não foi inferido sucesso apenas pelo status
Live do painel Render.
