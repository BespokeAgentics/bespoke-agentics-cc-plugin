import { test } from "node:test";
import assert from "node:assert/strict";
import { parseYaml, toYaml, YamlError } from "../core/yaml.ts";

test("parses block maps, sequences, flow lists, scalars and comments", () => {
  const doc = parseYaml(`
# comment
version: 1
name: "quoted: name"
budget:
  max_steps: 40
  max_cost_usd: 2.5
nodes:
  verify:
    sensors: [tests, lint]
    edges: { pass: gate, fail: repair }
    parallel: true
    empty: ~
items:
  - one
  - kind: command
    cmd: "npm test -- --x"   # trailing comment
  - [a, b]
`);
  assert.deepEqual(doc, {
    version: 1,
    name: "quoted: name",
    budget: { max_steps: 40, max_cost_usd: 2.5 },
    nodes: { verify: { sensors: ["tests", "lint"], edges: { pass: "gate", fail: "repair" }, parallel: true, empty: null } },
    items: ["one", { kind: "command", cmd: "npm test -- --x" }, ["a", "b"]],
  });
});

test("rejects features outside the subset", () => {
  assert.throws(() => parseYaml("a: &anchor 1"), YamlError);
  assert.throws(() => parseYaml("a: |\n  text"), YamlError);
  assert.throws(() => parseYaml("a: [1, [2]"), YamlError);
  assert.deepEqual(parseYaml("a: { b: [1, 2], c: { d: x } }"), { a: { b: [1, 2], c: { d: "x" } } });
  assert.throws(() => parseYaml("a: 1\na: 2"), /duplicate/);
  assert.throws(() => parseYaml("a:\n\tb: 1"), /tabs/);
});

test("round-trips through the emitter", () => {
  const v = { version: 1, list: ["x", "y"], nested: { a: "needs: quoting", b: 2, c: null, d: [{ k: "v", n: 1 }] }, s: "2026-10-26", e: {} };
  assert.deepEqual(parseYaml(toYaml(v)), v);
});
