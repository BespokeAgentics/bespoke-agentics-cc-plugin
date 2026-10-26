// Shared wiring for run / resume: builds a Runner from a harness directory.
import { existsSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { loadGraph, loadPolicy, validateGraph } from "../core/graph.ts";
import { FileStore } from "../core/store.ts";
import { FilePolicyEngine } from "../core/policy.ts";
import { LocalTools } from "../core/tools.ts";
import { buildSensors } from "../core/sensors.ts";
import { makeModel } from "../core/model.ts";
import { Runner, type RunnerOptions } from "../core/runner.ts";
import type { ToolCall } from "../core/types.ts";
import { type Args, str } from "./args.ts";

export interface Wiring { runner: Runner; store: FileStore; runDir: string; graphPath: string; policyPath: string; workspace: string }

export function wire(a: Args, runDir: string, opts: { requireExisting: boolean }): Wiring {
  const harnessDir = resolve(str(a, "dir") ?? inferHarnessDir(runDir) ?? "harness");
  const graphPath = resolve(str(a, "graph") ?? join(harnessDir, "graph.yaml"));
  const policyPath = resolve(str(a, "policy") ?? join(harnessDir, "policy.yaml"));
  const workspace = resolve(str(a, "workspace") ?? dirname(harnessDir));
  if (!existsSync(graphPath)) throw new Error(`graph not found: ${graphPath}`);
  if (!existsSync(policyPath)) throw new Error(`policy not found: ${policyPath}`);
  if (opts.requireExisting && !FileStore.exists(runDir)) throw new Error(`no run at ${runDir}`);

  const graph = loadGraph(graphPath);
  const policy = loadPolicy(policyPath);
  const v = validateGraph(graph, policy, graphPath);
  if (!v.ok) throw new Error("graph is invalid; run validate-graph:\n" + v.errors.map((e) => `  ${e.code}${e.node ? ` [${e.node}]` : ""}: ${e.message}`).join("\n"));

  const injectFailures: Record<string, number> = {};
  for (const spec of String(str(a, "inject-failure") ?? "").split(",").filter(Boolean)) {
    const [name, n] = spec.split(":");
    injectFailures[name] = Number(n ?? 1);
  }
  const extraCalls: ToolCall[] = [];
  const extra = str(a, "stub-extra");
  if (extra) { const parsed = JSON.parse(extra); extraCalls.push(...(Array.isArray(parsed) ? parsed : [parsed]) as ToolCall[]); }
  const decision = str(a, "decision") as "approved" | "rejected" | undefined;
  if (decision && decision !== "approved" && decision !== "rejected") throw new Error("--decision must be approved or rejected");

  const store = new FileStore(runDir);
  const options: RunnerOptions = {
    graph, graphPath, store,
    policy: new FilePolicyEngine(policy, workspace),
    tools: new LocalTools({ deployLog: join(harnessDir, "deploys.log") }),
    sensors: buildSensors(graph.sensors, dirname(graphPath)),
    model: makeModel(str(a, "model") ?? "stub", { extraCalls }),
    workspace,
    killAfterSteps: str(a, "kill-after") ? Number(str(a, "kill-after")) : undefined,
    injectFailures,
    decision,
    decisionNote: str(a, "note"),
    log: a.flags.quiet ? undefined : (l) => process.stderr.write(l + "\n"),
  };
  return { runner: new Runner(options), store, runDir, graphPath, policyPath, workspace };
}

function inferHarnessDir(runDir: string): string | undefined {
  // runs live at <harness>/runs/<id>; walk up two levels when that shape holds
  const up = resolve(runDir, "..", "..");
  return existsSync(join(up, "graph.yaml")) ? up : undefined;
}

export function readContract(a: Args): unknown {
  const p = str(a, "contract");
  if (!p) throw new Error("--contract <file.json> is required");
  return JSON.parse(readFileSync(resolve(p), "utf8"));
}
