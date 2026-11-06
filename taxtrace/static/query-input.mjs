// Keep explicit lookups deterministic; never infer or pad a tax code.
export function prepareQuery(task, input) {
    const value = input.trim();
    if (task === "article") {
        if (!/^[1-9][0-9]{0,3}$/.test(value))
            throw new Error("articleInputError");
        return `Leia o artigo ${value}.`;
    }
    if (task === "code") {
        if (!/^[0-9]{6}$/.test(value)) throw new Error("codeInputError");
        return `Consulte o cClassTrib ${value}.`;
    }
    if (task !== "search" || value.length < 3 || value.length > 500)
        throw new Error("inputError");
    return value;
}
