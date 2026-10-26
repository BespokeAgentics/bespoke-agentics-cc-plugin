# graph-harness reference runtime

TypeScript on Node ≥ 22.18 (native type stripping), zero dependencies. Vendored into a project at
`harness/runtime/` by `bootstrap --level 2`; the project's `harness/bin/*` shims call `cli/*.ts`.

| Module | Role |
|---|---|
| `core/types.ts` | the adapter seam: `StateStore`, `PolicyEngine`, `Sensor`, `ToolAdapter`, `ModelAdapter` |
| `core/graph.ts` | load + `validateGraph` (schema, reachability, outcome coverage, capped loops, gated risk, sensed outputs) |
| `core/store.ts` | `FileStore` (JSONL events, fsync per append) + `projectState` (state is a projection of the log) |
| `core/policy.ts` | `FilePolicyEngine` over `policy.yaml` (tiers, workspace boundary, allow-lists, approval records) |
| `core/sensors.ts` | sensor kinds: command, file_exists, file_contains, json_schema, contract_complete, custom |
| `core/tools.ts` | `LocalTools`: read_file, list_files, write_file, run_command, delete_path, deploy (stub), fetch |
| `core/model.ts` | `StubModel` (deterministic) and `CommandModel` (any CLI: JSON in, JSON out) |
| `core/runner.ts` | the loop: outcomes from evidence, retry caps, budget, escalation, pause/resume, receipts |
| `core/receipt.ts` · `audit.ts` · `upgrade.ts` · `bootstrap.ts` | the other scripts' logic |
| `core/schema.ts` · `yaml.ts` | vendored JSON-Schema subset validator and YAML subset parser |

Semantics (node types, outcomes, events, resume rules, the YAML subset, adapter contracts):
the skill's `references/graph-spec.md`. Tests: `node --test 'tests/*.test.ts'` from this directory.
