import { test } from "node:test";
import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { loadStructured, loadPolicy, validateGraph, findCycles, TEMPLATES_DIR } from "../core/graph.ts";

const FIXTURES = join(import.meta.dirname, "..", "..", "fixtures", "broken-graphs");
const policy = loadPolicy(join(TEMPLATES_DIR, "policy.yaml"));

test("graph.default.yaml passes validate-graph with the shipped policy", () => {
  const r = validateGraph(loadStructured(join(TEMPLATES_DIR, "graph.default.yaml")), policy);
  assert.deepEqual(r.errors, []);
  assert.equal(r.ok, true);
  assert.equal(r.stats.cycles >= 1, true, "the repair loop is a cycle");
});

test("every broken fixture is rejected with the error codes its header names", () => {
  const files = readdirSync(FIXTURES).filter((f) => f.endsWith(".yaml"));
  assert.ok(files.length >= 4, "at least four broken fixtures");
  for (const f of files) {
    const text = readFileSync(join(FIXTURES, f), "utf8");
    const expected = [...text.split("\n")[0].matchAll(/\b([A-Z][A-Z_]+)\b/g)].map((m) => m[1]).filter((c) => c !== "Expect");
    const r = validateGraph(loadStructured(join(FIXTURES, f)), policy, f);
    assert.equal(r.ok, false, `${f} should fail`);
    const codes = new Set(r.errors.map((e) => e.code));
    for (const c of expected) assert.ok(codes.has(c), `${f}: expected ${c}, got ${[...codes].join(",")}`);
  }
});

test("findCycles enumerates elementary cycles once", () => {
  const cycles = findCycles({ a: ["b"], b: ["c"], c: ["a", "b"], d: ["a"] });
  const sigs = cycles.map((c) => c.join(">")).sort();
  assert.deepEqual(sigs, ["a>b>c", "b>c"]);
});
