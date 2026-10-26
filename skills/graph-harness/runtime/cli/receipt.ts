#!/usr/bin/env node
// receipt --run <run-dir> [--graph <file>] [--write]
// Emits the change receipt for a run (validated against receipt.schema.json). --write also saves receipt.json.
import { existsSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { parseArgs, str, emit } from "./args.ts";
import { FileStore, projectState } from "../core/store.ts";
import { buildReceipt } from "../core/receipt.ts";
import { loadGraph, loadSchema } from "../core/graph.ts";
import { validate } from "../core/schema.ts";

const a = parseArgs(process.argv.slice(2));
try {
  const runDir = resolve(str(a, "run") ?? a.positional[0] ?? "");
  if (!runDir || !FileStore.exists(runDir)) throw new Error(`no run at ${runDir || "(missing --run)"}`);
  const store = new FileStore(runDir);
  const events = store.events();
  const state = projectState(events);
  const graphPath = str(a, "graph") ?? (typeof events[0].data.graph_path === "string" ? events[0].data.graph_path : undefined);
  const graph = graphPath && existsSync(graphPath) ? loadGraph(graphPath) : undefined;
  const receipt = buildReceipt(events, state, graph);
  const errs = validate(loadSchema("receipt.schema.json"), receipt);
  if (errs.length) throw new Error("receipt does not match receipt.schema.json: " + errs.map((e) => `${e.path}: ${e.message}`).join("; "));
  if (a.flags.write) writeFileSync(join(runDir, "receipt.json"), JSON.stringify(receipt, null, 2) + "\n");
  emit(receipt, 0);
} catch (e) {
  emit({ ok: false, error: (e as Error).message }, 1);
}
