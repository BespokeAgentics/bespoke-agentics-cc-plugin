// Custom sensor stub. A sensor is evidence, not opinion: return pass/fail plus the evidence
// that justifies it. The harness turns the result into an edge; the model never sees this code.
//
// Wire it in harness/graph.yaml:
//   sensors:
//     my_check: { kind: custom, module: "sensors/my_check.ts" }
//
// `ctx` has workspace, contract, artifacts, attempt. `def` is the sensor's YAML entry.

export interface SensorContext { workspace: string; contract?: { output: { path?: string } }; artifacts: { path: string }[]; attempt: number }
export interface SensorResult { pass: boolean; summary: string; evidence?: Record<string, unknown> }

export async function run(ctx: SensorContext, def: Record<string, unknown>): Promise<SensorResult> {
  const target = ctx.contract?.output.path ?? ctx.artifacts.at(-1)?.path;
  if (!target) return { pass: false, summary: "nothing to inspect: no output path and no artifact" };
  // Replace with a real check. Returning pass=false by default keeps an unfinished sensor from going green.
  return { pass: false, summary: `custom sensor not implemented for ${target} (def: ${JSON.stringify(def)})`, evidence: { target } };
}
