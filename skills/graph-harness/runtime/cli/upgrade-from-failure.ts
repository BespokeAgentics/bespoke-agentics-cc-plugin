#!/usr/bin/env node
// upgrade-from-failure --run <run-dir> | --trace <events.jsonl> [--class <failure-class>] [--write]
// Turns a trace into a Guide + Check proposal. --write saves it under <harness>/upgrades/.
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { parseArgs, str, emit } from "./args.ts";
import { FileStore } from "../core/store.ts";
import { propose, FAILURE_CLASSES, type FailureClass } from "../core/upgrade.ts";
import type { HarnessEvent } from "../core/types.ts";

const a = parseArgs(process.argv.slice(2));
try {
  let events: HarnessEvent[];
  let harnessDir: string | undefined;
  const runDir = str(a, "run") ?? a.positional[0];
  if (runDir) { const d = resolve(runDir); if (!FileStore.exists(d)) throw new Error(`no run at ${d}`); events = new FileStore(d).events(); harnessDir = resolve(d, "..", ".."); }
  else if (str(a, "trace")) { events = readFileSync(resolve(str(a, "trace")!), "utf8").split("\n").filter((l) => l.trim()).map((l) => JSON.parse(l)); }
  else throw new Error("--run <run-dir> or --trace <events.jsonl> is required");
  const cls = str(a, "class") as FailureClass | undefined;
  if (cls && !FAILURE_CLASSES.includes(cls)) throw new Error(`--class must be one of ${FAILURE_CLASSES.join(", ")}`);
  const p = propose(events, cls);
  let written: string | undefined;
  if (a.flags.write) {
    const dir = str(a, "dir") ?? (harnessDir && existsSync(join(harnessDir, "policy.yaml")) ? harnessDir : "harness");
    mkdirSync(join(dir, "upgrades"), { recursive: true });
    written = join(dir, "upgrades", `${events[0]?.run_id ?? "trace"}-${p.failure_class}.json`);
    writeFileSync(written, JSON.stringify({ run_id: events[0]?.run_id, created_at: new Date().toISOString(), ...p }, null, 2) + "\n");
  }
  emit({ run_id: events[0]?.run_id ?? null, written: written ?? null, ...p }, 0);
} catch (e) { emit({ ok: false, error: (e as Error).message }, 1); }
