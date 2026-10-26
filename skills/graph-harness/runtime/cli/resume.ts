#!/usr/bin/env node
// resume --run <run-dir> [--decision approved|rejected] [--note '...'] [--dir <harness>] [--model ...] [--quiet]
// Rebuilds state from events.jsonl and continues. Exit 0 completed, 2 paused, 1 failed.
import { resolve } from "node:path";
import { parseArgs, str, emit } from "./args.ts";
import { projectState } from "../core/store.ts";
import { wire } from "./common.ts";

const a = parseArgs(process.argv.slice(2));
try {
  const runDir = resolve(str(a, "run") ?? a.positional[0] ?? "");
  if (!runDir) throw new Error("--run <run-dir> is required");
  const w = wire(a, runDir, { requireExisting: true });
  const before = projectState(w.store.events());
  const state = await w.runner.continue();
  emit({ run_id: state.run_id, run_dir: runDir, resumed_from: { node: before.current_node, step: before.step, status: before.status }, status: state.status, outcome: state.outcome ?? null, current_node: state.current_node, step: state.step, retries_total: state.retries_total, pending: state.pending, failures: state.failures.slice(-5), artifacts: state.artifacts, events: state.last_seq },
    state.status === "completed" ? 0 : state.status === "paused" ? 2 : 1);
} catch (e) {
  emit({ ok: false, error: (e as Error).message }, 1);
}
