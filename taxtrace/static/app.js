import { prepareQuery } from "./query-input.mjs";
const $ = (q) => document.querySelector(q);
const strings = {
    pt: {
        skip: "Ir para a consulta",
        brand: "PESQUISA TRIBUTÁRIA",
        local: "Ambiente local",
        new: "Nova consulta",
        session: "Consultas nesta aba",
        resume: "Abrir revisão por identificador",
        identifier: "Identificador da revisão",
        open: "Abrir revisão",
        sideNote:
            "Histórico desta aba. Os registros de revisão podem ser retomados pelo identificador.",
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
        notFound: "Revisão não encontrada neste ambiente.",
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
        check: "Conferi o material exibido. Esta decisão registra somente a revisão documental.",
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
            "Encontre a base legal de IBS e CBS, confira a origem e registre sua revisão documental.",
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
        purposeTitle: "Conferir a base normativa com a origem à vista.",
        purposeText:
            "A lei e as tabelas tributárias estão em fontes separadas. O TaxTrace ajuda a localizar referências de IBS e CBS e a registrar quais documentos sustentam sua análise.",
        deliverTitle: "O que a consulta entrega",
        deliver1: "Referências da coleta",
        deliver1Sub: "Artigos ou classificação correspondentes à consulta.",
        deliver2: "Origem para conferência",
        deliver2Sub: "Texto recuperado, link oficial e versão dos dados.",
        deliver3: "Revisão documentada",
        deliver3Sub:
            "Sua decisão e justificativa ligadas ao material conferido.",
        scopeTitle: "O que não é feito aqui",
        scopeText:
            "Cálculo de tributos, enquadramento automático de produtos ou emissão de parecer fiscal.",
        sessionLimit: "Até 10 consultas · histórico da aba",
        restoreText: "Use o identificador de um registro salvo neste ambiente.",
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
    },
    en: {
        skip: "Skip to query",
        brand: "TAX RESEARCH",
        local: "Local workspace",
        new: "New query",
        session: "Queries in this tab",
        resume: "Open a review by identifier",
        identifier: "Review identifier",
        open: "Open review",
        sideNote:
            "History for this tab. Review records can be resumed using their identifier.",
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
        notFound: "Review not found in this environment.",
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
        check: "I checked the displayed material. This decision records document review only.",
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
            "Find IBS and CBS legal references, inspect their origin and record your document review.",
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
        purposeTitle: "Check the legal basis with its origin in view.",
        purposeText:
            "Legal text and tax tables are published separately. TaxTrace helps locate IBS and CBS references and record which documents support your analysis.",
        deliverTitle: "What the lookup provides",
        deliver1: "Snapshot references",
        deliver1Sub: "Articles or a classification matching the query.",
        deliver2: "Sources for verification",
        deliver2Sub: "Retrieved text, official links and the dataset version.",
        deliver3: "Documented review",
        deliver3Sub:
            "Your decision and reasoning bound to the inspected material.",
        scopeTitle: "Outside this application",
        scopeText:
            "Tax calculation, automatic product classification or tax advice.",
        sessionLimit: "Up to 10 queries · tab history",
        restoreText:
            "Use the identifier of a record saved in this environment.",
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
    },
};

let selectedDocument = 0;
let activeStep = "query";
function setStep(step) {
    if (step !== "query" && !current) return;
    activeStep = step;
    document.body.dataset.step = step;
    setView("research", false);

    document.querySelectorAll("[data-step-target]").forEach((b) => {
        b.disabled = busy || (b.dataset.stepTarget !== "query" && !current);
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
            (b) =>
                (b.disabled =
                    value || (b.dataset.stepTarget !== "query" && !current)),
        );
    $("#working").hidden = !value;
    $("#send").disabled = value || !base || !context;
    $("#question").disabled = value;
    $("#mode").disabled = value;
    document
        .querySelectorAll(
            "[data-query],button[data-task],[data-view-target],#task-example,#new-query,#restore-button,#language",
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
            response.status === 403
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
    $("#mode-help").textContent =
        $("#mode").value === "gemini" ? t("aiHelp") : t("directHelp");
    if (context && !context.gemini_disponivel)
        $('#mode option[value="gemini"]').disabled = true;
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
        const a = el("a", "source-link", label);
        a.href = url.href;
        a.target = "_blank";
        a.rel = "noopener noreferrer";
        return a;
    } catch {
        return el("small", "", t("unknown"));
    }
}
function documentCard(numberValue, text, source, warnings = {}) {
    const card = el("article", "document");
    card.append(el("h3", "", `${t("article")} ${numberValue}`));
    card.append(el("p", "", text));

    if (warnings.excerpt) card.append(el("p", "notice", t("excerptNotice")));
    if (warnings.partial) card.append(el("p", "notice", t("partial")));
    if (warnings.struck) card.append(el("small", "", t("struck")));
    if (source) card.append(sourceLink(source));
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
            documentCard(opened.numero, opened.texto, opened.citacao, {
                partial: opened.proximo_inicio != null,
                struck: opened.tem_trecho_riscado,
            }),
        );
    (query.resultados || [])
        .filter((x) => x.artigo_numero !== opened?.numero)
        .forEach((r) =>
            documents.append(
                documentCard(r.artigo_numero, r.trecho, r.citacao, {
                    struck: r.tem_trecho_riscado,
                    excerpt: true,
                }),
            ),
        );
    if (query.registro) {
        const c = el("article", "document");
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
            report.estado.modo === "gemini" ? t("planAI") : t("planRule"),
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
                `${t("recorded")}: ${t(r.decisao === "aprovar" ? "approved" : "rejected")}\n${r.revisor} · ${r.origem === "teste_automatizado" ? t("autoLabel") : t("declared")}\n${t("reasonSaved")}: ${r.motivo}`,
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
    if (!report.pendente && !report.estado.revisao) {
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
function reviewForm(report) {
    const form = el("form", "review-panel");
    form.append(el("h3", "", t("reviewTitle")), el("p", "", t("reviewText")));
    const row = el("div", "form-row");
    const name = el("input");
    name.name = "revisor";
    name.required = true;
    name.minLength = 3;
    name.maxLength = 80;
    const nameLabel = el("label", "", t("reviewer"));
    nameLabel.append(name);
    const origin = el("select");
    origin.name = "origem";
    origin.setAttribute("aria-label", t("origin"));
    [
        ["operador_local", "person"],
        ["teste_automatizado", "automatic"],
    ].forEach(([v, k]) => {
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
    checkLabel.append(check, el("span", "", t("check")));
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
    form.append(actions, el("small", "", t("declared")));
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
    $("#task-example").textContent = t(`${activeTask}Example`);
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
$("#task-example").addEventListener("click", () => {
    $("#question").value = {
        search: "cesta basica",
        article: "125",
        code: "000001",
    }[activeTask];
    $("#question").dispatchEvent(new Event("input"));
    $("#question").focus();
});
$("#brand-home").addEventListener("click", () => setView("research"));
applyLanguage();
setBusy(false);
try {
    context = await api("/api/contexto");
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
