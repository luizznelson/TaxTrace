import { prepareQuery } from "./query-input.mjs";
const $ = (q) => document.querySelector(q);
const strings = {
    pt: {
        browserSessionRequired:
            "Recarregue a página e permita cookies deste site para iniciar uma consulta.",
        reviewerScope:
            "Esta conta de revisor tem acesso administrativo às revisões deste ambiente.",
        accountAuthenticated: "Conta de revisor autenticada localmente",
        accessTitle: "Acesso do revisor",
        accessHint:
            "Consultar fontes não exige login. Para aprovar ou rejeitar, entre com a conta de revisor.",
        accessMissing:
            "A conta de revisor ainda não foi configurada neste computador. As consultas continuam disponíveis; decisões estão bloqueadas.",
        accessAccount: "Conta",
        accessPassword: "Senha",
        accessEnter: "Entrar para revisar",
        accessExit: "Encerrar sessão",
        accessActive: "Sessão de revisão",
        accessLimit:
            "Conta autenticada localmente; identidade civil e qualificação fiscal não verificadas. A sessão expira em uma hora.",
        loginRequired:
            "Entre com a conta de revisor para registrar uma decisão. Confira a área de acesso no início da página.",
        loginError: "Não foi possível entrar. Confira a conta e a senha.",
        accessWait:
            "Muitas tentativas de acesso. Aguarde um minuto e tente novamente.",
        skip: "Ir para a consulta",
        brand: "PESQUISA TRIBUTÁRIA",
        local: "Ambiente local",
        new: "Nova consulta",
        session: "Consultas nesta aba",
        resume: "Abrir revisão por identificador",
        identifier: "Identificador da revisão",
        open: "Abrir revisão",
        sideNote:
            "Histórico desta aba. Abra registros do mesmo navegador ou entre como revisor para acessar outros registros.",
        understand: "Como usar",
        scope: "REFORMA TRIBUTÁRIA · IBS E CBS",
        hero: "Qual referência você precisa conferir?",
        lead: "Pesquise dispositivos de IBS e CBS, confira o texto da fonte e registre o que foi revisado. Sem perder o contexto entre uma etapa e outra.",
        seal: "Documentos primeiro.\nConclusões com critério.",
        dataset: "BASE DOCUMENTAL",
        articles: "artigos organizados",
        classes: "classificações tributárias",
        ncm: "códigos NCM na coleta",
        captured: "Captura:",
        apiDate: "Data consultada na API:",
        dateLimit: "Data de consulta não comprova vigência.",
        start: "NOVA PESQUISA",
        publicOnly: "Use somente dados públicos",
        question: "Sua pergunta",
        placeholder: "O que você precisa conferir na base?",
        mode: "Como executar",
        direct: "Busca direta · sem IA",
        ai: "Planejar consulta com IA",
        directHelp:
            "Consulta a coleta armazenada. Nenhuma pergunta é enviada a um modelo.",
        aiHelp: "Envia a pergunta ao Gemini para escolher uma ação de consulta. A IA não redige pareceres.",
        aiOff: "Assistente IA indisponível neste ambiente.",
        send: "Consultar",
        example1: "Encontrar a base legal",
        example1sub: "Explore a cesta básica",
        example2: "Ler um artigo",
        example2sub: "Abra o artigo 125",
        example3: "Conferir um código",
        example3sub: "Consulte o cClassTrib 000001",
        working: "Consultando a base documental…",
        workingSub:
            "A resposta mostrará os documentos encontrados e a coleta utilizada.",
        method: "DO DOCUMENTO À REVISÃO",
        methodTitle: "Como funciona esta pesquisa?",
        step1: "Escolher a referência",
        step1text:
            "A consulta começa pela base identificada. A IA, quando escolhida, apenas planeja uma ação limitada.",
        step2: "Conferir a evidência",
        step2text:
            "Veja os artigos, as fontes e a coleta usada. Um documento encontrado ainda precisa de interpretação.",
        step3: "Registrar a revisão",
        step3text:
            "Aprove ou rejeite o conjunto exibido. A decisão fica ligada ao seu hash, sem gerar um parecer fiscal.",
        footer: "Pesquisa documental com fontes identificadas. A interpretação tributária exige conferência profissional.",
        emptyHistory:
            "Nenhuma consulta nesta aba. Inicie pela Consulta documental para pesquisar um tema, artigo ou classificação.",
        baseError:
            "Não foi possível acessar a base. Confira se o PostgreSQL local está ativo e recarregue a página.",
        error: "Não foi possível concluir. Tente novamente; se a consulta já tiver um identificador, use “Retomar uma revisão”.",
        inputError: "Confira o texto e os campos obrigatórios.",
        expired:
            "Esta página perdeu a autorização local. Recarregue antes de continuar.",
        conflict:
            "A revisão mudou ou já foi encerrada. Abra-a novamente antes de decidir.",
        busy: "Já há consultas em andamento. Aguarde e tente novamente.",
        notFound:
            "Revisão não disponível para esta sessão. Confira o identificador ou entre como revisor.",
        evidence: "Resultados da pesquisa",
        pending: "Aguardando revisão",
        approved: "Revisão aprovada",
        rejected: "Revisão rejeitada",
        absent: "Referência não encontrada",
        refused: "Pedido não encaminhado",
        failed: "Consulta não concluída",
        article: "Artigo",
        source: "Abrir fonte oficial ↗",
        full: "Ver trecho completo",
        partial:
            "Leitura parcial. Há mais texto disponível na fonte ou pela ferramenta de leitura.",
        struck: "Este artigo tem marcações de texto riscado na coleta. A vigência exige conferência.",
        trace: "Como esta pesquisa foi executada",
        collection: "Coleta",
        version: "Versão",
        noData: "Nenhuma referência foi encontrada nesta consulta. Isso não comprova ausência na legislação.",
        refusal:
            "O planejador recusou a solicitação. Você pode reformular uma consulta documental sobre IBS e CBS.",
        failedText:
            "Uma etapa não pôde ser concluída. Os dados não devem ser interpretados como uma resposta vazia.",
        reviewTitle: "Registrar revisão documental",
        reviewText:
            "Confira o material e as fontes antes de decidir. A aprovação se refere a este conjunto documental, sem validar enquadramento ou parecer fiscal.",
        reviewer: "Nome do revisor",
        origin: "Origem do registro",
        person: "Pessoa neste computador",
        automatic: "Teste automatizado",
        reason: "O que foi conferido? Quais são as ressalvas?",
        check: "Conferi as evidências registradas nesta consulta. Esta decisão registra somente a revisão documental.",
        approve: "Registrar aprovação",
        reject: "Registrar rejeição",
        recorded: "Decisão registrada",
        declared: "Registro local, com identidade declarada pelo revisor.",
        stale: "O código mudou desde esta execução. Inicie uma nova consulta para revisar com o fluxo atual.",
        technical: "Registro técnico e evidências",
        export: "Baixar registro JSON ↓",
        general:
            "A fonte descreve uma regra geral, sem artigo específico vinculado.",
        classification: "Classificação",
        cbs: "Redução CBS informada",
        ibs: "Redução IBS estadual informada",
        unknown: "Não informado",
        note: "Percentuais da tabela, sem enquadramento automático de produto.",
        plan: "Planejamento da consulta",
        consultar_base: "Identificação da base",
        buscar_artigos: "Busca de referências",
        ler_artigo: "Leitura do artigo",
        consultar_classificacao: "Consulta do código",
        aprofundar: "Conferência de documentos",
        conferir: "Conferência de fontes e coleta",
        finalizar: "Encerramento do fluxo",
        revisar: "Decisão de revisão",
        planRule: "Por regras de entrada",
        planAI: "Planejado com Gemini",
        sources: "Fontes desta coleta",
        reasonSaved: "Motivo",
        autoLabel: "Decisão de teste automatizado",
        restoreHint: "Informe um identificador de revisão válido.",
        navQuery: "Editar consulta",
        navQuerySub: "Defina o que conferir",
        navEvidence: "Documentos encontrados",
        navEvidenceSub: "Leia e confronte fontes",
        navReview: "Revisão documental",
        navReviewSub: "Registre sua decisão",
        toReview: "Registrar revisão →",
        backEvidence: "Voltar à leitura",
        dossier: "PESQUISA DOCUMENTAL",
        skipRead: "Sem leitura adicional",
        baseSummary: "Cobertura da coleta",
        baseNav: "Base documental",
        findings: "Referências encontradas",
        reader: "Leitura da fonte",
        selectDocument:
            "Selecione uma referência para ler o texto recuperado e conferir sua origem.",
        excerptNotice:
            "Este é um trecho de busca, não o artigo completo. Abra a fonte oficial para conferir o contexto.",
        excerpt: "Trecho recuperado",
        openedText: "Texto recuperado",
        evidenceCount: "referência(s)",
        sourceContext:
            "Conteúdo da coleta identificada. Confira a fonte oficial e as limitações antes de concluir.",
        reviewClosed: "Registro da revisão",
        workspace: "ÁREA DE TRABALHO",
        workspaceName: "Espaço de pesquisa",
        researchNav: "Consulta documental",
        sessionsNav: "Revisões da sessão",
        sourcesNav: "Base e fontes",
        snapshotLabel: "Coleta documental",
        researchDescription:
            "Pesquise a legislação e as classificações de IBS e CBS. No modo Resposta com fontes, receba uma explicação com citações para conferir e revisar.",
        sessionsDescription:
            "Retome as consultas desta aba para conferir fontes, concluir uma revisão ou baixar o registro.",
        sourcesDescription:
            "Conheça o conteúdo disponível e a versão dos dados utilizada nas consultas.",
        taskHeading: "O que você precisa conferir?",
        taskSearch: "Pesquisar um tema",
        taskSearchSub: "Localizar artigos por assunto",
        taskArticle: "Abrir um artigo",
        taskArticleSub: "Ler um dispositivo específico",
        taskCode: "Consultar cClassTrib",
        taskCodeSub: "Conferir a classificação da tabela",
        searchLabel: "Assunto ou pergunta sobre IBS e CBS",
        articleLabel: "Número do artigo da LC 214/2025",
        codeLabel: "Código de classificação tributária (cClassTrib)",
        searchPlaceholder:
            "Ex.: cesta básica, redução de alíquotas ou crédito presumido",
        articlePlaceholder: "Ex.: 125",
        codePlaceholder: "Ex.: 000001",
        searchHelp:
            "A busca direta localiza termos nos artigos. Para interpretar uma pergunta e planejar a consulta, selecione o modo com IA.",
        articleHelp:
            "Informe apenas o número do artigo. A consulta abre o texto disponível na coleta, com seu link oficial.",
        codeHelp:
            "Informe os seis dígitos do cClassTrib, incluindo os zeros iniciais. Você verá a descrição e os percentuais informados na tabela.",
        tryExample: "Exemplo:",
        searchExample: "cesta básica",
        articleExample: "Artigo 125",
        codeExample: "cClassTrib 000001",
        purposeTitle: "O que você consegue fazer aqui?",
        purposeText:
            "Localizar onde a lei trata de um assunto, abrir um artigo pelo número e conferir a descrição e os percentuais de um cClassTrib. Depois, registrar quais documentos foram conferidos e por quê.",
        deliverTitle: "O que a consulta entrega",
        deliver1: "Encontre uma referência",
        deliver1Sub:
            "Pesquise por assunto, número de artigo ou código cClassTrib.",
        deliver2: "Confira o documento",
        deliver2Sub:
            "Leia o texto recuperado e abra a fonte oficial. A versão da coleta acompanha a consulta.",
        deliver3: "Registre o que foi revisado",
        deliver3Sub:
            "Informe sua decisão e justificativa. O registro e as evidências podem ser baixados.",
        scopeTitle: "O que não é feito aqui",
        scopeText:
            "Cálculo de tributos, enquadramento automático de produtos ou confirmação de vigência atual. A resposta com IA é uma síntese documental, sujeita a revisão.",
        sessionLimit: "Até 10 consultas · histórico da aba",
        restoreText:
            "Use o identificador de uma consulta deste navegador. Registros antigos ou de outro navegador exigem acesso de revisor.",
        sourceIntro:
            "As consultas usam uma coleta identificada, não uma busca em tempo real na legislação. Confira as datas e a fonte oficial antes de interpretar o resultado.",
        catalogTitle: "Conteúdo das fontes",
        lawDescription:
            "Texto legal organizado por artigo, com marcas de alteração preservadas.",
        tableDescription:
            "Tabelas de classificação tributária e códigos NCM da coleta. Os totais não significam que todos os códigos tenham consulta disponível na interface.",
        articleInputError: "Informe somente o número do artigo, de 1 a 9999.",
        codeInputError:
            "Informe um cClassTrib com exatamente seis dígitos, incluindo os zeros iniciais.",
        purposeLabel: "APOIO À ANÁLISE TRIBUTÁRIA",
        navigationLabel: "Áreas da aplicação",
        queryTypeLabel: "Tipo de consulta",
        queryViewLabel: "Visualização da consulta",
        examplesTitle: "Exemplos para começar",
        examplesHint: "Clique para preencher; depois, consulte.",
        exampleBasket: "Cesta básica",
        exampleCredit: "Crédito presumido",
        exampleReduction: "Redução de alíquotas",
        exampleArticle125: "Artigo 125 · cesta básica",
        exampleArticle126: "Artigo 126",
        exampleCode000001: "000001 · tributação integral",
        fullExport: "Baixar artigo e origem (JSON) ↓",
        fullArticle: "Artigo integral",
        queryEvidence: "Evidência da consulta",
        loadingArticle: "Carregando o artigo integral da coleta…",
        fullReadNote:
            "Texto integral preservado na coleta, com parágrafos e marcações de redações riscadas. A leitura não comprova vigência atual.",
        fullReadScope:
            "Leitura de apoio. A decisão de revisão permanece vinculada às evidências registradas na consulta.",
        fullReadError:
            "Não foi possível carregar o artigo integral. A evidência original continua disponível; tente novamente.",
        retryRead: "Tentar carregar novamente",
        reviewScope: "Evidências vinculadas a esta revisão",
        reviewScopeText:
            "A decisão registra o material recuperado abaixo. A leitura integral ao lado serve para conferir o contexto e não amplia esse conjunto.",
        textLocator:
            "A fonte não tem uma âncora de artigo identificada na coleta. O link tenta localizar o texto; o comportamento depende do navegador.",
        ragNotGenerated: "Resposta não gerada",
        ragMode: "Resposta com fontes · RAG",
        ragHelp:
            "Busca documentos e envia a pergunta e o contexto público ao Gemini para gerar uma explicação com citações. Uma chamada de síntese; sem parecer fiscal.",
        provenanceTitle: "Base utilizada nesta resposta",
        temporalUnverified: "Vigência atual não confirmada",
        datesHelp:
            "Captura é quando os dados foram coletados. A data consultada na API identifica o recorte solicitado à Receita; nenhuma delas, sozinha, comprova vigência jurídica.",
        ragTitle: "Resposta com fontes",
        ragDraft: "Rascunho · aguardando revisão",
        ragApproved: "Resposta revisada e aprovada",
        ragRejected: "Resposta revisada e rejeitada",
        ragUnavailable: "Geração indisponível",
        ragInsufficient:
            "Não há evidência suficiente para responder com segurança",
        ragLimit:
            "Esta é uma síntese documental da coleta, não confirmação de vigência atual ou orientação de enquadramento. As citações foram conferidas literalmente; a interpretação ainda exige revisão.",
        ragQuotes: "Conferir trechos de apoio",
        ragCitation: "Abrir evidência",
        ragFailed:
            "A resposta não foi liberada. O modelo pode estar indisponível ou a saída pode ter sido recusada pela validação. Os documentos recuperados continuam disponíveis.",
        ragReviewTitle: "Revisar resposta e evidências",
        ragReviewText:
            "Confira as afirmações e seus trechos de apoio antes de decidir. A decisão fica vinculada ao texto da resposta, contexto e citações registrados; não é validação fiscal.",
        ragScopeText:
            "Este conjunto inclui a resposta gerada, suas citações e os documentos recuperados. A leitura integral complementar continua separada.",
        ragCheck:
            "Conferi a resposta e as evidências registradas. Esta decisão não certifica vigência ou enquadramento fiscal.",
        ragRule: "Busca por regras e síntese com Gemini",
        avaliar_contexto: "Verificação dos critérios de evidência",
        gerar_resposta: "Geração e conferência das citações",
        reason_vigencia_nao_verificada:
            "A coleta não permite confirmar a vigência de uma regra na data solicitada. Consulte o documento e confira as alterações na fonte oficial.",
        reason_aplicacao_individual_fora_do_escopo:
            "O TaxTrace não calcula tributos nem decide o enquadramento de uma empresa ou produto. Reformule como uma pergunta sobre o que um documento informa.",
        reason_anexo_nao_disponivel:
            "A resposta exige conteúdo de anexo que não está disponível como evidência neste fluxo. O artigo pode mencionar o anexo sem listar os seus itens.",
        reason_pedido_inseguro:
            "Este pedido não pode ser atendido. A aplicação se limita à pesquisa e explicação documental de IBS e CBS.",
        reason_fora_do_escopo:
            "A pergunta não pertence ao escopo documental de IBS e CBS.",
        reason_evidencia_incompleta:
            "O contexto enviado para síntese não contém o artigo completo. Você pode ler a versão integral no leitor, mas ela não foi usada nesta geração.",
        reason_redacao_alterada_exige_conferencia:
            "O artigo tem histórico de texto riscado na coleta e exige conferência das redações. A síntese automática foi bloqueada nesta versão.",
        reason_sem_contexto_completo:
            "A recuperação não trouxe um documento completo para sustentar a resposta. Experimente um assunto mais específico ou informe um artigo.",
        reason_conteudo_suspeito_na_evidencia:
            "O documento contém conteúdo que exige conferência antes de gerar uma resposta.",
        reason_contexto_nao_cobre_pergunta:
            "Os documentos disponíveis não sustentaram uma resposta para esta pergunta. Reformule ou confira as fontes.",
    },
    en: {
        browserSessionRequired:
            "Reload the page and allow cookies for this site before starting a query.",
        reviewerScope:
            "This reviewer account has administrative access to reviews in this environment.",
        accountAuthenticated: "Locally authenticated reviewer account",
        accessTitle: "Reviewer access",
        accessHint:
            "Reading sources does not require a login. Sign in with the reviewer account to approve or reject.",
        accessMissing:
            "No reviewer account is configured on this computer. Queries remain available; decisions are blocked.",
        accessAccount: "Account",
        accessPassword: "Password",
        accessEnter: "Sign in to review",
        accessExit: "Sign out",
        accessActive: "Review session",
        accessLimit:
            "Locally authenticated account; civil identity and tax qualifications are unverified. The session expires in one hour.",
        loginRequired:
            "Sign in as a reviewer before recording a decision. See reviewer access at the top of the page.",
        loginError: "Unable to sign in. Check the account and password.",
        accessWait:
            "Too many sign-in attempts. Wait one minute before trying again.",
        skip: "Skip to query",
        brand: "TAX RESEARCH",
        local: "Local workspace",
        new: "New query",
        session: "Queries in this tab",
        resume: "Open a review by identifier",
        identifier: "Review identifier",
        open: "Open review",
        sideNote:
            "History for this tab. Open records from the same browser or sign in as a reviewer to access other records.",
        understand: "How to use",
        scope: "BRAZILIAN TAX REFORM · IBS AND CBS",
        hero: "Which reference do you need to check?",
        lead: "Find IBS and CBS provisions, inspect the source text and record your review. Keep the context throughout the process.",
        seal: "Documents first.\nConclusions with care.",
        dataset: "DOCUMENT COLLECTION",
        articles: "organized articles",
        classes: "tax classifications",
        ncm: "NCM codes in the snapshot",
        captured: "Captured:",
        apiDate: "API query date:",
        dateLimit: "Query date does not establish legal validity.",
        start: "NEW RESEARCH",
        publicOnly: "Use public data only",
        question: "Your question",
        placeholder: "Use Portuguese terms, or try one of the examples.",
        mode: "Execution method",
        direct: "Direct search · no AI",
        ai: "Plan the query with AI",
        directHelp:
            "Queries the stored snapshot. No question is sent to a model.",
        aiHelp: "Sends your question to Gemini to choose a lookup action. AI does not write tax advice.",
        aiOff: "AI assistant unavailable in this environment.",
        send: "Look up",
        example1: "Find the legal reference",
        example1sub: "Explore the basic food basket",
        example2: "Read an article",
        example2sub: "Open article 125",
        example3: "Check a code",
        example3sub: "Look up cClassTrib 000001",
        working: "Querying the document collection…",
        workingSub:
            "The result will identify the retrieved documents and the snapshot used.",
        method: "FROM DOCUMENT TO REVIEW",
        methodTitle: "How does this research work?",
        step1: "Choose the reference",
        step1text:
            "The query starts with an identified collection. When selected, AI only plans a bounded action.",
        step2: "Check the evidence",
        step2text:
            "Inspect articles, sources and the snapshot used. A retrieved document still requires interpretation.",
        step3: "Record the review",
        step3text:
            "Approve or reject the displayed package. The decision is bound to its hash, without generating tax advice.",
        footer: "Document research with identified sources. Tax interpretation requires professional verification.",
        emptyHistory:
            "No queries in this tab. Start in Document research to look up a topic, article or classification.",
        baseError:
            "The collection could not be accessed. Check that local PostgreSQL is running, then reload.",
        error: "The operation could not finish. Try again; if you have a review identifier, use “Resume a review”.",
        inputError: "Check your text and required fields.",
        expired:
            "This page lost its local authorization. Reload before continuing.",
        conflict:
            "The review changed or is already closed. Open it again before deciding.",
        busy: "Other queries are running. Please wait and try again.",
        notFound:
            "Review unavailable for this session. Check the identifier or sign in as a reviewer.",
        evidence: "Research results",
        pending: "Awaiting review",
        approved: "Review approved",
        rejected: "Review rejected",
        absent: "Reference not found",
        refused: "Request not forwarded",
        failed: "Query not completed",
        article: "Article",
        source: "Open official source ↗",
        full: "Read full excerpt",
        partial:
            "Partial reading. More text is available in the source or through the article-reading tool.",
        struck: "This article has strikethrough markings in the snapshot. Legal validity needs checking.",
        trace: "How this research was executed",
        collection: "Collection",
        version: "Version",
        noData: "No reference was found in this query. This does not establish absence in the law.",
        refusal:
            "The planner declined the request. You may rephrase a document query about IBS and CBS.",
        failedText:
            "A step could not finish. This must not be interpreted as an empty data answer.",
        reviewTitle: "Record document review",
        reviewText:
            "Check the material and sources first. Approval concerns this document package; it does not validate a product classification or tax advice.",
        reviewer: "Reviewer name",
        origin: "Record origin",
        person: "Person on this computer",
        automatic: "Automated test",
        reason: "What was checked? What caveats remain?",
        check: "I checked the evidence recorded in this query. This decision records document review only.",
        approve: "Record approval",
        reject: "Record rejection",
        recorded: "Decision recorded",
        declared: "Local record, with a self-declared reviewer identity.",
        stale: "Code changed since this run. Start a new query to review using the current workflow.",
        technical: "Technical record and evidence",
        export: "Download JSON record ↓",
        general:
            "The source describes a general rule, without a specific linked article.",
        classification: "Classification",
        cbs: "Reported CBS reduction",
        ibs: "Reported state IBS reduction",
        unknown: "Not reported",
        note: "Table percentages, without automatic product classification.",
        plan: "Query planning",
        consultar_base: "Collection identification",
        buscar_artigos: "Reference search",
        ler_artigo: "Article reading",
        consultar_classificacao: "Code lookup",
        aprofundar: "Document inspection",
        conferir: "Source and collection checks",
        finalizar: "Workflow completion",
        revisar: "Review decision",
        planRule: "Input-rule routing",
        planAI: "Planned with Gemini",
        sources: "Sources in this collection",
        reasonSaved: "Reason",
        autoLabel: "Automated test decision",
        restoreHint: "Enter a valid review identifier.",
        navQuery: "Edit query",
        navQuerySub: "Define what to check",
        navEvidence: "Retrieved documents",
        navEvidenceSub: "Read and compare sources",
        navReview: "Document review",
        navReviewSub: "Record your decision",
        toReview: "Record review →",
        backEvidence: "Return to reading",
        dossier: "DOCUMENT RESEARCH",
        skipRead: "No additional article reading",
        baseSummary: "Snapshot coverage",
        baseNav: "Document collection",
        findings: "Retrieved references",
        reader: "Source reader",
        selectDocument:
            "Select a reference to read the retrieved text and inspect its origin.",
        excerptNotice:
            "This is a search excerpt, not the complete article. Open the official source to check the context.",
        excerpt: "Retrieved excerpt",
        openedText: "Retrieved text",
        evidenceCount: "reference(s)",
        sourceContext:
            "Content from the identified snapshot. Check the official source and limitations before concluding.",
        reviewClosed: "Review record",
        workspace: "WORKSPACE",
        workspaceName: "Research workspace",
        researchNav: "Document research",
        sessionsNav: "Session reviews",
        sourcesNav: "Collection and sources",
        snapshotLabel: "Document snapshot",
        researchDescription:
            "Search IBS and CBS legislation and classifications. Answer with sources provides a cited explanation for inspection and review.",
        sessionsDescription:
            "Resume queries from this tab to inspect sources, complete a review or download the record.",
        sourcesDescription:
            "Check available content and the dataset version used for queries.",
        taskHeading: "What do you need to check?",
        taskSearch: "Research a topic",
        taskSearchSub: "Find articles by subject",
        taskArticle: "Open an article",
        taskArticleSub: "Read a specific legal provision",
        taskCode: "Look up cClassTrib",
        taskCodeSub: "Check a tax classification",
        searchLabel: "Topic or question about IBS and CBS",
        articleLabel: "Article number in LC 214/2025",
        codeLabel: "Tax classification code (cClassTrib)",
        searchPlaceholder:
            "Use Portuguese terms, e.g. cesta básica or crédito presumido",
        articlePlaceholder: "E.g. 125",
        codePlaceholder: "E.g. 000001",
        searchHelp:
            "Direct search matches article terms. Select AI planning to interpret a question and choose a lookup action.",
        articleHelp:
            "Enter the article number only. The lookup opens the text available in the snapshot and its official source link.",
        codeHelp:
            "Enter all six cClassTrib digits, including leading zeros. The lookup returns the description and percentages reported in the table.",
        tryExample: "Example:",
        searchExample: "cesta básica",
        articleExample: "Article 125",
        codeExample: "cClassTrib 000001",
        purposeTitle: "What can you do here?",
        purposeText:
            "Find where the law addresses a topic, open an article by number and check a cClassTrib description and reported percentages. Then record which documents were checked and why.",
        deliverTitle: "What the lookup provides",
        deliver1: "Find a reference",
        deliver1Sub: "Search by topic, article number or cClassTrib code.",
        deliver2: "Inspect the document",
        deliver2Sub:
            "Read the retrieved text and open the official source. Each query identifies its snapshot version.",
        deliver3: "Record your review",
        deliver3Sub:
            "Enter your decision and reasoning. The record and evidence can be downloaded.",
        scopeTitle: "Outside this application",
        scopeText:
            "Tax calculation, automatic product classification or confirmation of current legal validity. AI answers are document syntheses requiring review.",
        sessionLimit: "Up to 10 queries · tab history",
        restoreText:
            "Use the identifier of a query from this browser. Older records or records from another browser require reviewer access.",
        sourceIntro:
            "Queries use an identified snapshot, not a live legal search. Check capture dates and official sources before interpreting results.",
        catalogTitle: "Source content",
        lawDescription:
            "Legal text organized by article, preserving amendment markings.",
        tableDescription:
            "Tax classification tables and NCM codes from the snapshot. Counts do not mean every code is available for lookup in this interface.",
        articleInputError:
            "Enter an article number from 1 to 9999, using digits only.",
        codeInputError:
            "Enter exactly six cClassTrib digits, including leading zeros.",
        purposeLabel: "TAX RESEARCH SUPPORT",
        navigationLabel: "Application areas",
        queryTypeLabel: "Query type",
        queryViewLabel: "Query view",
        examplesTitle: "Examples to get started",
        examplesHint: "Click to fill in the field, then run the lookup.",
        exampleBasket: "Basic food basket",
        exampleCredit: "Presumed tax credit",
        exampleReduction: "Rate reductions",
        exampleArticle125: "Article 125 · basic food basket",
        exampleArticle126: "Article 126",
        exampleCode000001: "000001 · full taxation",
        fullExport: "Download article and source (JSON) ↓",
        fullArticle: "Full article",
        queryEvidence: "Query evidence",
        loadingArticle: "Loading the complete article from the snapshot…",
        fullReadNote:
            "Complete text preserved in the snapshot, including paragraphs and strikethrough markings. Reading does not establish current legal validity.",
        fullReadScope:
            "Context reading. The review decision remains bound to the evidence recorded in the query.",
        fullReadError:
            "The complete article could not be loaded. The original evidence remains available; try again.",
        retryRead: "Retry loading",
        reviewScope: "Evidence bound to this review",
        reviewScopeText:
            "Your decision records the retrieved material below. The full article alongside provides context and does not expand this evidence set.",
        textLocator:
            "No article anchor was identified in the snapshot. The link attempts a text lookup; behavior depends on the browser.",
        ragNotGenerated: "Answer not generated",
        ragMode: "Answer with sources · RAG",
        ragHelp:
            "Retrieves documents and sends the question and public context to Gemini for a cited explanation. One synthesis call; no tax advice.",
        provenanceTitle: "Collection used for this answer",
        temporalUnverified: "Current legal validity not confirmed",
        datesHelp:
            "Capture is when the data was collected. The API query date identifies the requested Federal Revenue snapshot; neither date alone establishes legal validity.",
        ragTitle: "Answer with sources",
        ragDraft: "Draft · awaiting review",
        ragApproved: "Answer reviewed and approved",
        ragRejected: "Answer reviewed and rejected",
        ragUnavailable: "Generation unavailable",
        ragInsufficient: "Insufficient evidence to answer safely",
        ragLimit:
            "This is a snapshot-based document synthesis, not confirmation of current legal validity or product classification advice. Quotes were checked literally; interpretation still requires review.",
        ragQuotes: "Inspect supporting excerpts",
        ragCitation: "Open evidence",
        ragFailed:
            "No answer was released. The model may be unavailable or validation may have rejected its output. Retrieved documents remain available.",
        ragReviewTitle: "Review answer and evidence",
        ragReviewText:
            "Check claims and supporting excerpts before deciding. The decision is bound to the recorded answer, context and citations; it is not a tax validation.",
        ragScopeText:
            "This package includes the generated answer, its citations and retrieved documents. Supplementary full-article reading remains separate.",
        ragCheck:
            "I checked the recorded answer and evidence. This decision does not certify legal validity or tax classification.",
        ragRule: "Rule-based retrieval and Gemini synthesis",
        avaliar_contexto: "Evidence eligibility checks",
        gerar_resposta: "Generation and citation validation",
        reason_vigencia_nao_verificada:
            "The snapshot cannot confirm legal validity at the requested date. Inspect the document and changes in the official source.",
        reason_aplicacao_individual_fora_do_escopo:
            "TaxTrace does not calculate taxes or classify a company or product. Ask what a document states instead.",
        reason_anexo_nao_disponivel:
            "Answering requires annex content not available as evidence in this workflow. An article may mention an annex without listing its items.",
        reason_pedido_inseguro:
            "This request cannot be fulfilled. The application only supports IBS and CBS document research and explanation.",
        reason_fora_do_escopo:
            "The question is outside the IBS and CBS document scope.",
        reason_evidencia_incompleta:
            "The synthesis context does not contain the complete article. You can read it in the reader, but that supplementary text was not used for this generation.",
        reason_redacao_alterada_exige_conferencia:
            "The article contains historical strikethrough text requiring verification. Automatic synthesis is blocked in this version.",
        reason_sem_contexto_completo:
            "Retrieval did not provide a complete document to support an answer. Try a more specific topic or an article number.",
        reason_conteudo_suspeito_na_evidencia:
            "The document contains content requiring inspection before answer generation.",
        reason_contexto_nao_cobre_pergunta:
            "The available documents did not support an answer. Rephrase or inspect the sources.",
    },
};

let selectedDocument = 0;
const fullArticles = new Map();
let activeStep = "query";
function stepDisabled(step) {
    if (step === "query") return false;
    if (!current) return true;
    return (
        step === "review" &&
        !(
            (current.pendente && current.codigo_compativel) ||
            current.estado.revisao
        )
    );
}
function setStep(step) {
    if (stepDisabled(step)) return;
    activeStep = step;
    document.body.dataset.step = step;
    setView("research", false);

    document.querySelectorAll("[data-step-target]").forEach((b) => {
        b.disabled = busy || stepDisabled(b.dataset.stepTarget);
        if (b.dataset.stepTarget === step)
            b.setAttribute("aria-current", "step");
        else b.removeAttribute("aria-current");
    });
    if (step !== "query") {
        const target =
            step === "review"
                ? $(".review-panel, .decision-note, .review-empty")
                : $("#result");
        target?.scrollIntoView({ block: "start", behavior: "smooth" });
        if (step === "review")
            target?.querySelector("input")?.focus({ preventScroll: true });
    }
}
document
    .querySelectorAll("[data-step-target]")
    .forEach((b) =>
        b.addEventListener("click", () => setStep(b.dataset.stepTarget)),
    );

let lang = "pt",
    context = null,
    base = null,
    current = null,
    busy = false,
    attempt = null;
let history = [];
try {
    lang = sessionStorage.getItem("taxtrace.lang") || "pt";
    history = JSON.parse(sessionStorage.getItem("taxtrace.history") || "[]");
} catch {
    /* Storage is optional. */
}
if (!strings[lang]) lang = "pt";
if (!Array.isArray(history)) history = [];
const t = (key) => strings[lang][key] || key;
const el = (tag, cls, text) => {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text !== undefined) n.textContent = text;
    return n;
};
const number = (n) =>
    n == null
        ? "—"
        : new Intl.NumberFormat(lang === "pt" ? "pt-BR" : "en-US").format(n);
function date(value) {
    if (!value) return "—";
    const onlyDate = /^\d{4}-\d{2}-\d{2}$/.test(value);
    const d = new Date(
        onlyDate ? `${value}T12:00:00Z` : value.replace(" ", "T"),
    );
    return Number.isNaN(d.valueOf())
        ? value
        : new Intl.DateTimeFormat(lang === "pt" ? "pt-BR" : "en-US", {
              dateStyle: "medium",
              timeZone: onlyDate ? "UTC" : "America/Sao_Paulo",
          }).format(d);
}
function persist() {
    try {
        sessionStorage.setItem("taxtrace.lang", lang);
        sessionStorage.setItem(
            "taxtrace.history",
            JSON.stringify(history.slice(0, 10)),
        );
    } catch {
        /* The workflow also works without storage. */
    }
}
function feedback(key, error = true) {
    const box = $("#feedback");
    box.textContent = t(key);
    box.className = error ? "notice error" : "notice";
    box.hidden = false;
}
function setBusy(value) {
    busy = value;
    document
        .querySelectorAll("[data-step-target]")
        .forEach(
            (b) => (b.disabled = value || stepDisabled(b.dataset.stepTarget)),
        );
    $("#working").hidden = !value;
    $("#send").disabled = value || !base || !context;
    $("#question").disabled = value;
    $("#mode").disabled = value;
    document
        .querySelectorAll(
            "[data-query],button[data-task],[data-view-target],#task-examples button,#new-query,#restore-button,#language",
        )
        .forEach((n) => (n.disabled = value));
}
async function api(path, options = {}) {
    const response = await fetch(path, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            "X-TaxTrace-CSRF": context?.csrf || "",
            ...options.headers,
        },
    });
    let data;
    try {
        data = await response.json();
    } catch {
        throw new Error("error");
    }
    if (!response.ok) {
        const key =
            data.detail?.codigo === "sessao_navegador_necessaria"
                ? "browserSessionRequired"
                : response.status === 401
                  ? path === "/api/acesso/entrar"
                      ? "loginError"
                      : "loginRequired"
                  : data.codigo === "acesso_em_espera"
                    ? "accessWait"
                    : response.status === 403
                      ? "expired"
                      : response.status === 409
                        ? "conflict"
                        : response.status === 429
                          ? "busy"
                          : response.status === 404
                            ? "notFound"
                            : response.status === 422
                              ? "inputError"
                              : "error";
        throw new Error(key);
    }
    return data;
}
function applyLanguage() {
    const form = document.querySelector(".review-panel");
    const draft = form
        ? {
              revisor: form.elements.revisor.value,
              motivo: form.elements.motivo.value,
              origem: form.elements.origem.value,
          }
        : null;

    if (!$("#base-error").hidden) $("#base-error").textContent = t("baseError");
    document.documentElement.lang = lang === "pt" ? "pt-BR" : "en";
    document.title =
        lang === "pt"
            ? "TaxTrace · Consulta documental"
            : "TaxTrace · Document workspace";
    document.querySelectorAll("[data-i18n]").forEach((n) => {
        n.textContent = t(n.dataset.i18n);
    });
    document
        .querySelectorAll("[data-i18n-aria]")
        .forEach((n) => n.setAttribute("aria-label", t(n.dataset.i18nAria)));
    document.querySelectorAll("[data-placeholder]").forEach((n) => {
        n.placeholder = t(n.dataset.placeholder);
    });
    $("#language").textContent = lang === "pt" ? "EN ↗" : "PT ↗";
    $("#language").setAttribute(
        "aria-label",
        lang === "pt" ? "Switch to English" : "Mudar para português",
    );
    setView(activeView, false);
    renderTask();
    renderBase();
    renderHistory();
    renderAccess();
    modeHelp();
    if (current) renderResult(current);
    if (draft && document.querySelector(".review-panel")) {
        const f = document.querySelector(".review-panel");
        Object.entries(draft).forEach(([k, v]) => (f.elements[k].value = v));
    }
    const view = activeView;
    setStep(activeStep);
    setView(view, false);
    persist();
}
function modeHelp() {
    $("#mode-help").textContent = t(
        { local: "directHelp", gemini: "aiHelp", rag: "ragHelp" }[
            $("#mode").value
        ],
    );
    if (context) {
        $('#mode option[value="gemini"]').disabled = !context.gemini_disponivel;
        $('#mode option[value="rag"]').disabled = !context.rag_disponivel;
    }
}
function renderBase() {
    if (!base) return;
    $("#article-count").textContent = number(base.contagens.artigos);
    $("#class-count").textContent = number(base.contagens.classificacoes);
    $("#ncm-count").textContent = number(base.contagens.ncm);
    $("#version").textContent = base.coleta.versao_base;
    $("#sidebar-version").textContent = base.coleta.versao_base;
    $("#captured").textContent = date(base.coleta.coletado_em);
    $("#api-date").textContent = date(base.coleta.data_consulta);
}
function statusKey(status) {
    return (
        {
            aguardando_revisao: "pending",
            revisao_documental_aprovada: "approved",
            revisao_documental_rejeitada: "rejected",
            resposta_documental_aprovada: "ragApproved",
            resposta_documental_rejeitada: "ragRejected",
            resposta_indisponivel: "ragUnavailable",
            evidencia_insuficiente_para_resposta: "ragNotGenerated",
            referencia_nao_encontrada_nesta_consulta: "absent",
            recusado_pelo_planejador: "refused",
            execucao_nao_concluida: "failed",
        }[status] || "evidence"
    );
}
function renderHistory() {
    const box = $("#history");
    box.replaceChildren();
    $("#session-count").textContent = String(history.length);
    if (!history.length) {
        box.append(el("p", "", t("emptyHistory")));
        return;
    }
    history.slice(0, 10).forEach((item) => {
        if (!/^[0-9a-f-]{36}$/.test(item.id || "")) return;
        const b = el(
            "button",
            current?.revisao_id === item.id ? "active" : "",
            String(item.question || "").slice(0, 100),
        );
        b.append(el("small", "", t(statusKey(item.status))));
        b.addEventListener("click", () => restore(item.id));
        box.append(b);
    });
}
function remember(report) {
    history = [
        {
            id: report.revisao_id,
            question: report.estado.pergunta,
            status: report.status,
        },
        ...history.filter((x) => x.id !== report.revisao_id),
    ].slice(0, 10);
    persist();
    renderHistory();
}
function sourceLink(source, label = t("source")) {
    try {
        const url = new URL(source.url);
        if (url.protocol !== "https:") return el("small", "", t("unknown"));
        if (
            source.artigo &&
            /(^|\.)planalto\.gov\.br$/.test(url.hostname) &&
            !url.hash
        ) {
            url.hash = `:~:text=${encodeURIComponent(`Art. ${source.artigo}.`)}`;
        }
        const a = el("a", "source-link", label);
        a.href = url.href;
        a.target = "_blank";
        a.rel = "noopener noreferrer";
        return a;
    } catch {
        return el("small", "", t("unknown"));
    }
}
function legalParagraphs(paragraphs) {
    const container = el("div", "law-text");
    container.tabIndex = 0;
    container.setAttribute("role", "region");
    container.setAttribute("aria-label", t("fullArticle"));
    for (const block of paragraphs) {
        const p = el(
            "p",
            `law-${["caput", "inciso", "paragrafo", "alinea"].includes(block.tipo) ? block.tipo : "texto"}`,
        );
        for (const part of block.partes)
            p.append(el(part.riscado ? "del" : "span", "", part.texto));
        container.append(p);
    }
    return container;
}
function documentCard(numberValue, text, source, warnings = {}, report) {
    const card = el("article", "document");
    card.dataset.article = numberValue;
    card.append(el("h3", "", `${t("article")} ${numberValue}`));
    const tabs = el("div", "reading-tabs");
    const full = el("button", "", t("fullArticle"));
    const original = el("button", "", t("queryEvidence"));
    full.type = original.type = "button";
    const fullPane = el("div", "full-article-pane");
    const evidencePane = el("div", "query-evidence-pane");
    evidencePane.append(el("p", "", text));
    if (warnings.excerpt)
        evidencePane.append(el("p", "notice", t("excerptNotice")));
    if (warnings.partial) evidencePane.append(el("p", "notice", t("partial")));
    if (warnings.struck) evidencePane.append(el("small", "", t("struck")));
    if (source) evidencePane.append(sourceLink(source));
    tabs.append(full, original);
    card.append(tabs, evidencePane, fullPane);
    let loading = false;
    let loaded = false;
    function show(isFull) {
        fullPane.hidden = !isFull;
        evidencePane.hidden = isFull;
        full.setAttribute("aria-pressed", String(isFull));
        original.setAttribute("aria-pressed", String(!isFull));
    }
    async function loadComplete() {
        if (loading || loaded) return;
        loading = true;
        fullPane.replaceChildren(el("p", "reader-status", t("loadingArticle")));
        const key = `${report.revisao_id}:${numberValue}`;
        try {
            const data =
                fullArticles.get(key) ||
                (await api(
                    `/api/revisoes/${encodeURIComponent(report.revisao_id)}/artigos/${encodeURIComponent(numberValue)}`,
                ));
            if (
                data.numero !== numberValue ||
                data.coleta.id !== report.estado.coleta.id ||
                data.coleta.manifesto_sha256 !==
                    report.estado.coleta.manifesto_sha256 ||
                data.dossie_sha256 !== report.pacote_revisao.dossie_sha256
            )
                throw new Error("error");
            if (fullArticles.size >= 30)
                fullArticles.delete(fullArticles.keys().next().value);
            fullArticles.set(key, data);
            fullPane.replaceChildren(
                el("p", "reader-status", t("fullReadNote")),
                legalParagraphs(data.paragrafos),
                sourceLink(data.citacao),
                el("p", "reader-scope", t("fullReadScope")),
            );
            if (data.localizacao_oficial === "busca_por_fragmento_de_texto")
                fullPane.append(el("p", "reader-status", t("textLocator")));
            const download = el("a", "source-link", t("fullExport"));
            download.href = `/api/revisoes/${encodeURIComponent(report.revisao_id)}/artigos/${encodeURIComponent(numberValue)}`;
            download.download = `taxtrace-artigo-${numberValue}-${report.revisao_id}.json`;
            fullPane.append(download);
            loaded = true;
        } catch {
            const retry = el("button", "button quiet", t("retryRead"));
            retry.type = "button";
            retry.addEventListener("click", loadComplete);
            fullPane.replaceChildren(
                el("p", "notice error", t("fullReadError")),
                retry,
            );
        } finally {
            loading = false;
        }
    }
    card.loadComplete = loadComplete;
    card.showEvidence = (quote) => {
        show(false);
        const p = evidencePane.querySelector("p");
        const index = text.indexOf(quote);
        if (index >= 0)
            p.replaceChildren(
                document.createTextNode(text.slice(0, index)),
                el("mark", "", quote),
                document.createTextNode(text.slice(index + quote.length)),
            );
    };
    full.addEventListener("click", () => {
        show(true);
        loadComplete();
    });
    original.addEventListener("click", () => show(false));
    show(true);
    return card;
}
function renderResult(report) {
    document
        .querySelectorAll("[data-step-target]")
        .forEach((b) => (b.disabled = false));

    const root = $("#result");
    root.replaceChildren();
    root.hidden = false;
    const heading = el("div", "result-heading");
    heading.append(
        el("h2", "", t("evidence")),
        el("span", "badge", t(statusKey(report.status))),
    );
    root.append(heading, el("p", "result-question", report.estado.pergunta));
    const grid = el("div", "result-grid"),
        documents = el("div", "document-reader");
    const replies = report.estado.respostas || {},
        query = replies.consulta || {},
        opened =
            replies.artigo ||
            (query.status === "artigo_recuperado" ? query : null);
    if (opened?.texto)
        documents.append(
            documentCard(
                opened.numero,
                opened.texto,
                opened.citacao,
                {
                    partial: opened.proximo_inicio != null,
                    struck: opened.tem_trecho_riscado,
                },
                report,
            ),
        );
    (query.resultados || [])
        .filter((x) => x.artigo_numero !== opened?.numero)
        .forEach((r) =>
            documents.append(
                documentCard(
                    r.artigo_numero,
                    r.trecho,
                    r.citacao,
                    {
                        struck: r.tem_trecho_riscado,
                        excerpt: true,
                    },
                    report,
                ),
            ),
        );
    if (query.registro) {
        const c = el("article", "document");
        c.dataset.code = query.registro.codigo;
        c.append(
            el("h3", "", `${t("classification")} ${query.registro.codigo}`),
            el("p", "", query.registro.descricao),
        );
        const dl = el("dl", "data-list");
        [
            ["cbs", "percentual_reducao_cbs"],
            ["ibs", "percentual_reducao_ibs_uf"],
        ].forEach(([label, key]) => {
            const cell = el("div");
            cell.append(
                el("dt", "", t(label)),
                el(
                    "dd",
                    "",
                    query.registro[key] == null
                        ? t("unknown")
                        : `${number(Number(query.registro[key]))}%`,
                ),
            );
            dl.append(cell);
        });
        c.append(dl, el("small", "", t("note")));
        if (query.registro.regra_geral) c.append(el("p", "", t("general")));
        (query.fontes || [])
            .slice(0, 2)
            .forEach((s, i) =>
                c.append(sourceLink(s, `${t("sources")} ${i + 1} ↗`)),
            );
        documents.append(c);
    }
    if (!documents.children.length)
        documents.append(
            el(
                "p",
                "notice",
                t(
                    report.status === "recusado_pelo_planejador"
                        ? "refusal"
                        : report.status === "execucao_nao_concluida"
                          ? "failedText"
                          : "noData",
                ),
            ),
        );
    const trace = el("details", "trace-panel");
    trace.append(el("summary", "", t("trace")));
    const list = el("ol");
    (report.estado.rastro || []).forEach((e) => {
        const li = el(
            "li",
            "",
            t(
                e.etapa === "aprofundar" && e.status === "sem_artigo_a_abrir"
                    ? "skipRead"
                    : e.etapa === "planejar"
                      ? "plan"
                      : e.etapa,
            ),
        );
        if (e.duracao_ms != null)
            li.append(
                el("small", "", `${number(Math.round(e.duracao_ms))} ms`),
            );
        if (e.erro) li.append(el("small", "", t("failed")));
        list.append(li);
    });
    trace.append(list);
    const meta = el("div", "meta");
    meta.append(
        el("p", "", `${t("collection")}: ${report.estado.coleta?.id ?? "—"}`),
        el(
            "p",
            "",
            `${t("version")}: ${report.estado.coleta?.versao_base ?? "—"}`,
        ),
        el(
            "p",
            "",
            report.estado.modo === "rag"
                ? t("ragRule")
                : report.estado.modo === "gemini"
                  ? t("planAI")
                  : t("planRule"),
        ),
    );
    trace.append(meta);
    const cards = [...documents.querySelectorAll(".document")];
    const findings = el("aside", "findings");
    findings.setAttribute("aria-label", t("findings"));
    findings.append(
        el("h3", "", t("findings")),
        el(
            "small",
            "result-count",
            `${number(cards.length)} ${t("evidenceCount")}`,
        ),
    );
    const readerHead = el("div", "reader-heading", t("reader"));
    documents.prepend(readerHead);
    const selected = Math.min(selectedDocument, Math.max(0, cards.length - 1));
    const selectCard = (index) => {
        selectedDocument = index;
        cards[index]?.loadComplete?.();
        cards.forEach((card, i) => {
            card.hidden = i !== index;
        });
        findings.querySelectorAll("button").forEach((button, i) => {
            button.setAttribute("aria-pressed", String(i === index));
        });
    };
    cards.forEach((card, i) => {
        card.id = `source-document-${i}`;
        const button = el("button", "finding");
        button.type = "button";
        button.setAttribute("aria-controls", card.id);
        const title = card.querySelector("h3").textContent;
        const text = card.querySelector("p")?.textContent || "";
        button.append(
            el("span", "finding-number", String(i + 1).padStart(2, "0")),
            el("b", "", title),
            el(
                "small",
                "",
                text.slice(0, 150) + (text.length > 150 ? "…" : ""),
            ),
            el(
                "span",
                "finding-type",
                title.startsWith(t("classification"))
                    ? t("classification")
                    : i === 0 && opened?.texto
                      ? t("openedText")
                      : t("excerpt"),
            ),
        );
        button.addEventListener("click", () => selectCard(i));
        findings.append(button);
    });
    if (!cards.length) findings.append(el("p", "", t("selectDocument")));
    selectCard(selected);
    documents.append(el("p", "reader-note", t("sourceContext")));
    grid.append(findings, documents);
    if (report.estado.rag)
        root.append(
            answerPanel(report, (doc, quote) => {
                const index = cards.findIndex((c) =>
                    doc.artigo
                        ? c.dataset.article === doc.artigo
                        : c.dataset.code === doc.codigo,
                );
                if (index >= 0) {
                    selectCard(index);
                    cards[index].showEvidence?.(quote);
                    cards[index].scrollIntoView({
                        block: "start",
                        behavior: "smooth",
                    });
                }
            }),
        );
    root.append(grid, trace);
    if (report.pendente && report.codigo_compativel)
        root.append(reviewForm(report));
    if (report.pendente && !report.codigo_compativel)
        root.append(el("p", "notice", t("stale")));
    if (report.estado.revisao) {
        const r = report.estado.revisao;
        root.append(
            el(
                "p",
                "decision-note",
                `${t("recorded")}: ${t(r.decisao === "aprovar" ? "approved" : "rejected")}\n${r.revisor} · ${r.origem === "teste_automatizado" ? t("autoLabel") : r.autenticacao === "sessao_local" ? t("accountAuthenticated") : t("declared")}\n${t("reasonSaved")}: ${r.motivo}`,
            ),
        );
    }
    const exportLink = el("a", "export", t("export"));
    exportLink.href = `/api/revisoes/${encodeURIComponent(report.revisao_id)}/exportar`;
    exportLink.download = "";
    root.append(exportLink);
    const technical = el("details", "technical");
    technical.append(
        el("summary", "", t("technical")),
        el("pre", "", JSON.stringify(report, null, 2)),
    );
    root.append(technical);
    if (!report.pendente && !report.estado.revisao && !report.estado.rag) {
        root.append(
            el(
                "p",
                "review-empty notice",
                t(
                    report.status === "execucao_nao_concluida"
                        ? "failedText"
                        : "noData",
                ),
            ),
        );
    }
    const actions = el("div", "stage-actions");
    const forward = el("button", "button primary", t("toReview"));
    forward.type = "button";
    forward.addEventListener("click", () => setStep("review"));
    const back = el("button", "button quiet back-evidence", t("backEvidence"));
    back.type = "button";
    back.addEventListener("click", () => setStep("evidence"));
    if (report.pendente && report.codigo_compativel) actions.append(forward);
    heading.append(actions);
    root.append(back);
}
function answerPanel(report, openEvidence) {
    const rag = report.estado.rag;
    const panel = el("section", "rag-answer");
    const answered = rag.status === "respondida";
    panel.append(
        el(
            "h2",
            "",
            t(
                answered
                    ? "ragTitle"
                    : rag.status === "falha"
                      ? "ragUnavailable"
                      : "ragInsufficient",
            ),
        ),
    );
    const collection = report.estado.coleta || {};
    const provenance = el("dl", "answer-provenance");
    provenance.setAttribute("aria-label", t("provenanceTitle"));
    for (const [label, value] of [
        ["version", collection.versao_base || "—"],
        ["captured", date(collection.coletado_em)],
        ["apiDate", date(collection.data_consulta)],
    ]) {
        const cell = el("div");
        cell.append(el("dt", "", t(label)), el("dd", "", value));
        provenance.append(cell);
    }
    panel.append(
        provenance,
        el("p", "answer-date-note", t("temporalUnverified")),
    );
    const dates = el("details", "answer-date-help");
    dates.append(
        el("summary", "", t("provenanceTitle")),
        el("p", "", t("datesHelp")),
    );
    panel.append(dates);
    if (!answered) {
        const reason = rag.avaliacao?.motivo;
        const key = `reason_${reason}`;
        panel.append(
            el(
                "p",
                "",
                t(
                    rag.status === "falha"
                        ? "ragFailed"
                        : strings[lang][key]
                          ? key
                          : "reason_contexto_nao_cobre_pergunta",
                ),
            ),
        );
        return panel;
    }
    panel.append(
        el(
            "span",
            "badge",
            t(
                report.estado.revisao
                    ? report.estado.revisao.decisao === "aprovar"
                        ? "ragApproved"
                        : "ragRejected"
                    : "ragDraft",
            ),
        ),
    );
    const docs = new Map(
        rag.avaliacao.contexto.documentos.map((d) => [d.id, d]),
    );
    for (const point of rag.afirmacoes) {
        const item = el("div", "rag-point");
        item.append(el("p", "", point.texto));
        const quotes = el("details", "rag-quotes");
        quotes.append(el("summary", "", t("ragQuotes")));
        for (const cite of point.citacoes) {
            const doc = docs.get(cite.documento_id);
            if (!doc) continue;
            const button = el(
                "button",
                "citation",
                doc.artigo
                    ? `${t("article")} ${doc.artigo}`
                    : `cClassTrib ${doc.codigo}`,
            );
            button.type = "button";
            button.title = t("ragCitation");
            button.addEventListener("click", () =>
                openEvidence(doc, cite.trecho_literal),
            );
            item.append(button);
            quotes.append(el("blockquote", "", cite.trecho_literal));
        }
        item.append(quotes);
        panel.append(item);
    }
    panel.append(el("p", "rag-limit", t("ragLimit")));
    return panel;
}
function renderAccess() {
    const panel = $("#reviewer-access");
    panel.replaceChildren();
    if (!context) return;
    panel.setAttribute("aria-label", t("accessTitle"));
    const access = context.acesso;
    if (access?.usuario) {
        panel.append(
            el("strong", "", `${t("accessActive")}: ${access.usuario.nome}`),
        );
        panel.append(el("p", "", t("accessLimit")));
        panel.append(el("p", "", t("reviewerScope")));
        const exit = el("button", "button quiet", t("accessExit"));
        exit.type = "button";
        exit.addEventListener("click", async () => {
            exit.disabled = true;
            try {
                await api("/api/acesso/sair", { method: "POST", body: "{}" });
                context = await api("/api/contexto");
                renderAccess();
                if (current) renderResult(current);
            } catch (e) {
                feedback(e.message);
                exit.disabled = false;
            }
        });
        panel.append(exit);
        return;
    }
    const details = el("details");
    details.append(el("summary", "", t("accessTitle")));
    details.append(
        el("p", "", t(access?.configurado ? "accessHint" : "accessMissing")),
    );
    if (!access?.configurado) {
        panel.append(details);
        return;
    }
    const form = el("form", "access-form");
    const account = el("input"),
        password = el("input");
    account.name = "conta";
    account.autocomplete = "username";
    account.required = true;
    account.maxLength = 40;
    password.name = "senha";
    password.type = "password";
    password.autocomplete = "current-password";
    password.required = true;
    password.maxLength = 256;
    const accountLabel = el("label", "", t("accessAccount"));
    accountLabel.append(account);
    const passwordLabel = el("label", "", t("accessPassword"));
    passwordLabel.append(password);
    const enter = el("button", "button primary", t("accessEnter"));
    enter.type = "submit";
    form.append(accountLabel, passwordLabel, enter);
    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        enter.disabled = true;
        try {
            await api("/api/acesso/entrar", {
                method: "POST",
                body: JSON.stringify({
                    conta: account.value,
                    senha: password.value,
                }),
            });
            context = await api("/api/contexto");
            renderAccess();
            if (current) renderResult(current);
        } catch (e) {
            feedback(e.message);
            enter.disabled = false;
        } finally {
            password.value = "";
        }
    });
    details.append(form);
    panel.append(details);
}
function reviewForm(report) {
    if (!context?.acesso?.usuario) {
        const notice = el("div", "notice", t("loginRequired"));
        const link = el("a", "", t("accessTitle"));
        link.href = "#reviewer-access";
        notice.append(el("br"), link);
        return notice;
    }
    const form = el("form", "review-panel");
    const isRag = report.estado.rag?.status === "respondida";
    form.append(
        el("h3", "", t(isRag ? "ragReviewTitle" : "reviewTitle")),
        el("p", "", t(isRag ? "ragReviewText" : "reviewText")),
    );
    const scope = el("details", "review-scope");
    scope.append(
        el("summary", "", t("reviewScope")),
        el("p", "", t(isRag ? "ragScopeText" : "reviewScopeText")),
    );
    if (isRag)
        for (const point of report.estado.rag.afirmacoes)
            scope.append(
                el("p", "", point.texto),
                ...point.citacoes.map((c) =>
                    el("blockquote", "", c.trecho_literal),
                ),
            );
    const responses = report.estado.respostas || {};
    const query = responses.consulta || {};
    const seen = new Set();
    for (const item of [responses.artigo, query]) {
        if (item?.texto && !seen.has(item.numero)) {
            scope.append(
                el("h4", "", `${t("article")} ${item.numero}`),
                el("p", "", item.texto),
            );
            seen.add(item.numero);
        }
    }
    for (const item of query.resultados || [])
        scope.append(
            el("h4", "", `${t("article")} ${item.artigo_numero}`),
            el("p", "", item.trecho),
        );
    if (query.registro)
        scope.append(
            el(
                "p",
                "",
                `${t("classification")} ${query.registro.codigo}: ${query.registro.descricao}`,
            ),
        );
    form.append(scope);
    const row = el("div", "form-row");
    const name = el("input");
    name.name = "revisor";
    name.value = context.acesso.usuario.nome;
    name.readOnly = true;
    name.required = true;
    name.minLength = 3;
    name.maxLength = 80;
    const nameLabel = el("label", "", t("reviewer"));
    nameLabel.append(name);
    const origin = el("select");
    origin.name = "origem";
    origin.disabled = true;
    origin.setAttribute("aria-label", t("origin"));
    [["operador_local", "person"]].forEach(([v, k]) => {
        const o = el("option", "", t(k));
        o.value = v;
        origin.append(o);
    });
    const originLabel = el("label", "", t("origin"));
    originLabel.append(origin);
    row.append(nameLabel, originLabel);
    form.append(row);
    const reason = el("textarea");
    reason.name = "motivo";
    reason.required = true;
    reason.minLength = 5;
    reason.maxLength = 1000;
    const reasonLabel = el("label", "", t("reason"));
    reasonLabel.append(reason);
    form.append(reasonLabel);
    const checkLabel = el("label", "check"),
        check = el("input");
    check.type = "checkbox";
    check.required = true;
    checkLabel.append(check, el("span", "", t(isRag ? "ragCheck" : "check")));
    form.append(checkLabel);
    const actions = el("div", "review-actions");
    [
        ["aprovar", "approve", "button primary"],
        ["rejeitar", "reject", "button quiet"],
    ].forEach(([value, label, cls]) => {
        const b = el("button", cls, t(label));
        b.type = "submit";
        b.value = value;
        actions.append(b);
    });
    form.append(actions, el("small", "", t("accessLimit")));
    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (!form.reportValidity() || busy) return;
        const choice = event.submitter?.value;
        if (!["aprovar", "rejeitar"].includes(choice)) return;
        setBusy(true);
        actions.querySelectorAll("button").forEach((n) => (n.disabled = true));
        $("#feedback").hidden = true;
        try {
            current = await api(`/api/revisoes/${report.revisao_id}/decisao`, {
                method: "POST",
                body: JSON.stringify({
                    decisao: choice,
                    revisor: name.value,
                    motivo: reason.value,
                    origem: origin.value,
                    dossie_sha256: report.pacote_revisao.dossie_sha256,
                }),
            });
            remember(current);
            renderResult(current);
            setStep("review");
        } catch (e) {
            feedback(e.message);
            actions
                .querySelectorAll("button")
                .forEach((n) => (n.disabled = false));
        } finally {
            setBusy(false);
        }
    });
    return form;
}
async function restore(id) {
    if (busy) return;
    if (!/^[0-9a-f-]{36}$/.test(id)) {
        feedback("restoreHint");
        return;
    }
    setBusy(true);
    $("#feedback").hidden = true;
    try {
        current = await api(`/api/revisoes/${id}`);
        const question = current.estado.pergunta;
        const article = /^Leia o artigo ([1-9][0-9]{0,3})\.$/.exec(question);
        const code = /^Consulte o cClassTrib ([0-9]{6})\.$/.exec(question);
        activeTask = article ? "article" : code ? "code" : "search";
        $("#mode").value = ["local", "gemini", "rag"].includes(
            current.estado.modo,
        )
            ? current.estado.modo
            : "local";
        modeHelp();
        $("#question").value = article?.[1] || code?.[1] || question;
        taskDrafts[activeTask] = $("#question").value;
        renderTask();
        $("#question").dispatchEvent(new Event("input"));
        remember(current);
        selectedDocument = 0;
        renderResult(current);
        setStep("evidence");
        $("#result").focus({ preventScroll: true });
        $("#result").scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (e) {
        feedback(e.message);
    } finally {
        setBusy(false);
    }
}
$("#query-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (busy || !base || !context) return;
    let question;
    try {
        question = prepareQuery(activeTask, $("#question").value);
    } catch (error) {
        feedback(error.message);
        return;
    }
    const body = JSON.stringify({
        pergunta: question,
        modo: activeTask === "search" ? $("#mode").value : "local",
        coleta_id: base.coleta.id,
    });
    if (!attempt || attempt.body !== body)
        attempt = { body, id: crypto.randomUUID() };
    setBusy(true);
    $("#feedback").hidden = true;
    try {
        current = await api("/api/consultas", {
            method: "POST",
            body,
            headers: { "Idempotency-Key": attempt.id },
        });
        attempt = null;
        remember(current);
        selectedDocument = 0;
        renderResult(current);
        setStep("evidence");
        $("#result").focus({ preventScroll: true });
        $("#result").scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (e) {
        feedback(e.message);
    } finally {
        setBusy(false);
    }
});
$("#question").addEventListener("input", () => {
    $("#counter").textContent = `${$("#question").value.length} / 500`;
});
$("#question").addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        $("#query-form").requestSubmit();
    }
});
$("#mode").addEventListener("change", modeHelp);
$("#language").addEventListener("click", () => {
    lang = lang === "pt" ? "en" : "pt";
    applyLanguage();
});
$("#new-query").addEventListener("click", () => {
    current = null;
    setStep("query");
    attempt = null;
    $("#result").hidden = true;
    $("#question").value = "";
    taskDrafts[activeTask] = "";
    $("#question").dispatchEvent(new Event("input"));
    $("#feedback").hidden = true;
    renderHistory();
    $("#question").focus();
});
$("#restore-button").addEventListener("click", () =>
    restore($("#restore-id").value.trim()),
);
let activeView = "research";
let activeTask = "search";
const taskDrafts = { search: "", article: "", code: "" };
function setView(view, scroll = true) {
    activeView = ["research", "sessions", "sources"].includes(view)
        ? view
        : "research";
    document.body.dataset.view = activeView;
    const key = {
        research: "researchNav",
        sessions: "sessionsNav",
        sources: "sourcesNav",
    }[activeView];
    $("#view-title").textContent = t(key);
    $("#page-title").textContent = t(key);
    $("#page-description").textContent = t(`${activeView}Description`);
    document.querySelectorAll("[data-view-target]").forEach((b) => {
        if (b.dataset.viewTarget === activeView)
            b.setAttribute("aria-current", "page");
        else b.removeAttribute("aria-current");
    });
    if (scroll) {
        $("#feedback").hidden = true;
        $("#inicio").scrollIntoView({ block: "start" });
    }
}
const queryExamples = {
    search: [
        ["exampleBasket", "cesta basica"],
        ["exampleCredit", "credito presumido"],
        ["exampleReduction", "reducao de aliquotas"],
    ],
    article: [
        ["exampleArticle125", "125"],
        ["exampleArticle126", "126"],
    ],
    code: [["exampleCode000001", "000001"]],
};
function renderExamples() {
    const list = $("#task-examples");
    list.replaceChildren();
    queryExamples[activeTask].forEach(([key, value]) => {
        const button = el("button", "example-option", t(key));
        button.type = "button";
        button.disabled = busy;
        button.addEventListener("click", () => {
            if (busy) return;
            $("#question").value = value;
            taskDrafts[activeTask] = value;
            $("#question").dispatchEvent(new Event("input"));
            $("#feedback").hidden = true;
            $("#question").focus();
        });
        list.append(button);
    });
}
function renderTask() {
    $("#query-label").textContent = t(`${activeTask}Label`);
    $("#question").placeholder = t(`${activeTask}Placeholder`);
    $("#question").maxLength =
        activeTask === "code" ? 6 : activeTask === "article" ? 4 : 500;
    $("#question").rows = activeTask === "search" ? 3 : 1;
    $("#question").setAttribute(
        "inputmode",
        activeTask === "search" ? "text" : "numeric",
    );
    $("#task-help").textContent = t(`${activeTask}Help`);
    renderExamples();
    $("#mode-control").hidden = activeTask !== "search";
    $("#counter").hidden = activeTask !== "search";
    document.body.dataset.task = activeTask;
    document
        .querySelectorAll("button[data-task]")
        .forEach((b) =>
            b.setAttribute(
                "aria-pressed",
                String(b.dataset.task === activeTask),
            ),
        );
}
document
    .querySelectorAll("[data-view-target]")
    .forEach((b) =>
        b.addEventListener("click", () => setView(b.dataset.viewTarget)),
    );
document.querySelectorAll("button[data-task]").forEach((b) =>
    b.addEventListener("click", () => {
        taskDrafts[activeTask] = $("#question").value;
        activeTask = b.dataset.task;
        $("#question").value = taskDrafts[activeTask];
        renderTask();
        $("#question").dispatchEvent(new Event("input"));
        $("#feedback").hidden = true;
        $("#question").focus();
    }),
);
$("#brand-home").addEventListener("click", () => setView("research"));
applyLanguage();
setBusy(false);
try {
    context = await api("/api/contexto");
    renderAccess();
    modeHelp();
} catch {
    feedback("error");
}
try {
    base = await api("/api/base");
    renderBase();
} catch {
    $("#base-error").hidden = false;
    $("#base-error").textContent = t("baseError");
    feedback("baseError");
}
setBusy(false);
