#!/usr/bin/env node
// run --contract <file> [--dir <harness>] [--graph <file>] [--policy <file>] [--workspace <dir>]
//     [--run-id <id>] [--model stub|command:<cmd>] [--inject-failure tests:2] [--kill-after <n>]
//     [--stub-extra '<ToolCall JSON>'] [--quiet]
// Starts a new run. JSON summary on stdout; the trace streams to stderr. Exit 0 completed, 2 paused, 1 failed.
import { join, resolve } from "node:path";
import { parseArgs, str, emit } from "./args.ts";
import { wire, readContract } from "./common.ts";

const a = parseArgs(process.argv.slice(2));
try {
  const contract = readContract(a);
  const harnessDir = resolve(str(a, "dir") ?? "harness");
  const runId = str(a, "run-id") ?? `run-${new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14)}-${Math.random().toString(36).slice(2, 6)}`;
  const runDir = str(a, "run") ?? join(harnessDir, "runs", runId);
  const w = wire({ ...a, flags: { ...a.flags, dir: harnessDir } }, runDir, { requireExisting: false });
  const state = await w.runner.start(runId, contract);
  emit({ run_id: runId, run_dir: runDir, status: state.status, outcome: state.outcome ?? null, current_node: state.current_node, step: state.step, retries_total: state.retries_total, pending: state.pending, failures: state.failures.slice(-5), artifacts: state.artifacts, cost: state.cost, events: state.last_seq },
    state.status === "completed" ? 0 : state.status === "paused" ? 2 : 1);
} catch (e) {
  emit({ ok: false, error: (e as Error).message }, 1);
}
