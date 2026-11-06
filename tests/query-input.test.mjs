import { strict as assert } from "node:assert";
import { test } from "node:test";
import { prepareQuery } from "../taxtrace/static/query-input.mjs";

test("classification lookup preserves all leading zeros", () => {
    assert.equal(
        prepareQuery("code", " 000001 "),
        "Consulte o cClassTrib 000001.",
    );
});
test("incomplete or malformed codes are not guessed", () => {
    for (const input of [
        "1",
        "00001",
        "0000001",
        "00-001",
        "1.0000",
        "00001a",
        "０００００１",
    ])
        assert.throws(() => prepareQuery("code", input), /codeInputError/);
});
test("single digit articles remain valid", () => {
    assert.equal(prepareQuery("article", "1"), "Leia o artigo 1.");
    assert.equal(prepareQuery("article", "125"), "Leia o artigo 125.");
});
test("invalid article input never becomes a natural language lookup", () => {
    for (const input of ["0", "-1", "1.5", "125; outro", "10000", "0001"])
        assert.throws(
            () => prepareQuery("article", input),
            /articleInputError/,
        );
});
test("topic searches retain accents and respect request size limits", () => {
    assert.equal(prepareQuery("search", " cesta básica "), "cesta básica");
    assert.throws(() => prepareQuery("search", "  "), /inputError/);
    assert.throws(() => prepareQuery("search", "x".repeat(501)), /inputError/);
});
test("unknown task types fail closed", () => {
    assert.throws(
        () => prepareQuery("unsupported", "qualquer texto"),
        /inputError/,
    );
});
