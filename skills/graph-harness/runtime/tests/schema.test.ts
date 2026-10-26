import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { validate, unsupportedKeywords } from "../core/schema.ts";

const TEMPLATES = join(import.meta.dirname, "..", "..", "templates");

test("every shipped schema uses only keywords the validator implements", () => {
  for (const f of readdirSync(TEMPLATES).filter((f) => f.endsWith(".schema.json"))) {
    const schema = JSON.parse(readFileSync(join(TEMPLATES, f), "utf8"));
    assert.deepEqual(unsupportedKeywords(schema), [], `${f} uses unsupported keywords`);
    assert.equal(schema.$schema, "https://json-schema.org/draft/2020-12/schema", f);
  }
});

test("validator reports type, required, enum, additionalProperties, $ref and oneOf", () => {
  const schema = {
    type: "object", required: ["a"], additionalProperties: false,
    properties: { a: { type: "integer", minimum: 1 }, b: { enum: ["x", "y"] }, c: { $ref: "#/$defs/d" }, e: { oneOf: [{ type: "null" }, { type: "string" }] } },
    $defs: { d: { type: "array", items: { type: "string" }, minItems: 1 } },
  };
  assert.deepEqual(validate(schema, { a: 1, b: "x", c: ["s"], e: null }), []);
  const errs = validate(schema, { a: 0, b: "z", c: [], e: 3, extra: 1 });
  const paths = errs.map((e) => e.path).sort();
  assert.deepEqual(paths, ["$.a", "$.b", "$.c", "$.e", "$.extra"]);
  assert.ok(validate(schema, {}).some((e) => /missing required property "a"/.test(e.message)));
});
