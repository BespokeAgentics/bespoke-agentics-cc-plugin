// Request -> Contract. The guide says "reject vague done_when entries"; this is the check.
// A done_when entry is vague when it names no sensor AND either matches a vagueness pattern
// or contains no verifiable anchor (a path, a command, a number, a status code, a quoted string).

import { loadSchema } from "./graph.ts";
import { validate } from "./schema.ts";
import type { Contract } from "./types.ts";

export const VAGUE_PATTERNS: RegExp[] = [
  /\b(works?|working)\b/i,
  /\blooks? (good|right|fine|ok)\b/i,
  /\b(is|are) (done|complete|finished|correct|good|fine|ok|ready)\b/i,
  /\bproperly\b/i,
  /\bas expected\b/i,
  /\bno (bugs|issues|problems)\b/i,
  /\bbehaves? correctly\b/i,
  /\bimproved?\b/i,
  /\bbetter\b/i,
];

const ANCHOR = /(`[^`]+`|"[^"]+"|'[^']+'|\b\d+\b|\/[\w.\-\/]+|\b[\w\-]+\.(ts|js|tsx|py|md|json|yaml|yml|css|html|sql)\b|\b(exit(s)? 0|status 2\d\d|returns?)\b)/;

export interface ContractReport { ok: boolean; errors: { path: string; message: string }[] }

export function vaguenessOf(check: string): string | null {
  for (const p of VAGUE_PATTERNS) if (p.test(check)) return `matches vague pattern ${p}`;
  if (!ANCHOR.test(check)) return "names nothing verifiable (no path, command, number, status code or quoted string)";
  return null;
}

export function validateContract(contract: unknown, knownSensors: Set<string> = new Set()): ContractReport {
  const errors = validate(loadSchema("contract.schema.json"), contract).map((e) => ({ path: e.path, message: e.message }));
  if (errors.length) return { ok: false, errors };
  const c = contract as Contract;
  c.done_when.forEach((d, i) => {
    if (d.sensor) {
      if (knownSensors.size && !knownSensors.has(d.sensor) && d.sensor !== "contract_complete") errors.push({ path: `$.done_when[${i}].sensor`, message: `sensor "${d.sensor}" is not declared in the graph` });
      return;
    }
    const why = vaguenessOf(d.check);
    if (why) errors.push({ path: `$.done_when[${i}].check`, message: `"${d.check}" is not verifiable: ${why}. Name a sensor or state a concrete predicate.` });
  });
  if (c.output.kind !== "research" && c.output.kind !== "document" && !c.output.path) {
    errors.push({ path: "$.output.path", message: `output.kind ${c.output.kind} needs an output.path so a sensor can find it` });
  }
  if (/\b(deploy|delete|send|publish|email|pay)\b/i.test(c.goal) && c.risk === "reversible") {
    errors.push({ path: "$.risk", message: "goal names an irreversible verb but risk is reversible" });
  }
  return { ok: errors.length === 0, errors };
}
