#!/usr/bin/env node
// validate-graph [--graph <file>] [--policy <file>] [--dir <harness-dir>]
// Structured JSON to stdout; exit 1 when the graph is invalid.
import { existsSync } from "node:fs";
import { join, resolve } from "node:path";
import { parseArgs, str, emit } from "./args.ts";
import { loadStructured, loadPolicy, validateGraph, TEMPLATES_DIR } from "../core/graph.ts";

const a = parseArgs(process.argv.slice(2));
const dir = str(a, "dir");
const graphPath = resolve(str(a, "graph") ?? (dir ? join(dir, "graph.yaml") : a.positional[0] ?? join(TEMPLATES_DIR, "graph.default.yaml")));
const policyArg = str(a, "policy") ?? (dir ? join(dir, "policy.yaml") : undefined);
const policyPath = policyArg ? resolve(policyArg) : existsSync(join(TEMPLATES_DIR, "policy.yaml")) ? join(TEMPLATES_DIR, "policy.yaml") : undefined;

let graph: unknown;
try { graph = loadStructured(graphPath); }
catch (e) { emit({ ok: false, graph: graphPath, errors: [{ code: "PARSE", message: String((e as Error).message) }], warnings: [], stats: {} }, 1); }
const policy = policyPath && existsSync(policyPath) ? loadPolicy(policyPath) : undefined;
const report = validateGraph(graph, policy, graphPath);
emit({ ...report, policy: policyPath ?? null }, report.ok ? 0 : 1);
