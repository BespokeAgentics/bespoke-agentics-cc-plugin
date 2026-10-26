// Shared types for the graph harness runtime. Everything pluggable is an interface here:
// StateStore, PolicyEngine, Sensor, ToolAdapter, ModelAdapter. The file-based implementations
// in this directory are the reference; durable backends (XState, DBOS, Restate) implement the
// same interfaces (see references/graph-spec.md § Adapter seam).

export type NodeType =
  | "contract" | "load_context" | "plan" | "act" | "verify"
  | "policy_gate" | "repair" | "human_review" | "receipt";

export type Tier = "read" | "sandbox" | "write" | "network" | "approve";
export const TIER_ORDER: Tier[] = ["read", "sandbox", "write", "network", "approve"];

export type TaskClass = "code" | "ui" | "research" | "data" | "mixed";
export type Risk = "reversible" | "shared" | "irreversible";

/** Outcomes the harness can compute for each node type. Edges must cover the required set. */
export const OUTCOMES: Record<NodeType, { required: string[]; optional: string[] }> = {
  contract:     { required: ["ok", "fail"], optional: [] },
  load_context: { required: ["ok"], optional: ["fail"] },
  plan:         { required: ["ok"], optional: ["fail"] },
  act:          { required: ["ok", "fail", "blocked"], optional: [] },
  verify:       { required: ["pass", "fail"], optional: [] },
  policy_gate:  { required: ["allow", "deny", "needs_approval"], optional: [] },
  repair:       { required: ["ok"], optional: [] },          // "exhausted" routes via retry.on_exhausted
  human_review: { required: ["approved", "rejected"], optional: [] }, // "pending" pauses the run
  receipt:      { required: [], optional: [] },
};

export interface SensorDef {
  kind: "command" | "file_exists" | "file_contains" | "json_schema" | "contract_complete" | "custom";
  cmd?: string;
  path?: string;
  pattern?: string;
  schema?: string;
  module?: string;
  applies_to?: string[];
  timeout_ms?: number;
  todo?: string;
  allow_todo?: boolean;
}

export interface NodeDef {
  type: NodeType;
  guides?: string[];
  tools?: string[];
  tier?: Tier;
  sensors?: string[];
  parallel?: boolean;
  subgraph?: string;
  risk?: Risk;
  retry?: { max: number; on_exhausted: string };
  edges?: Record<string, string>;
  terminal?: boolean;
  description?: string;
}

export interface Graph {
  version: 1;
  name: string;
  level: 1 | 2 | 3;
  entry: string;
  budget: { max_steps: number; max_retries_total: number; max_cost_usd?: number };
  sensors?: Record<string, SensorDef>;
  nodes: Record<string, NodeDef>;
}

export interface ToolDef { tier: Tier; purpose: string; output?: string; failure?: string; boundary?: string }
export type TierRule = "allow" | "allow_in_workspace" | "allow_listed" | "require_approval" | "deny";

export interface Policy {
  version: string;
  tiers: Record<Tier, TierRule>;
  tools: Record<string, ToolDef>;
  workspace: string;
  deny_paths?: string[];
  network_allow?: string[];
  sandbox_allow?: string[];
  approvals_file?: string;
}

export interface Approval { tool: string; run_id?: string; granted_by: string; ts: string; note?: string }

export interface Contract {
  id: string;
  goal: string;
  inputs: string[];
  output: { kind: string; path?: string; description: string };
  constraints: string[];
  done_when: { check: string; sensor?: string }[];
  task_class: TaskClass;
  risk: Risk;
  requested_by?: string;
  created_at?: string;
}

export type EventType =
  | "run.started" | "contract.accepted" | "contract.rejected" | "context.loaded"
  | "node.entered" | "node.exited"
  | "tool.requested" | "policy.decided" | "tool.executed"
  | "sensor.ran" | "artifact.produced"
  | "retry.scheduled" | "retry.exhausted" | "escalated" | "human.decided"
  | "cost.recorded" | "rollback.point" | "subgraph.completed"
  | "run.paused" | "run.resumed" | "run.completed" | "run.failed";

export interface HarnessEvent {
  seq: number;
  ts: string;
  run_id: string;
  type: EventType;
  node?: string;
  attempt?: number;
  data: Record<string, unknown>;
}

export interface RunState {
  run_id: string;
  graph: string;
  level: number;
  status: "running" | "paused" | "completed" | "failed";
  current_node: string;
  step: number;
  attempts: Record<string, number>;
  retries_total: number;
  contract?: Contract;
  decisions: { seq: number; kind: "policy" | "human" | "harness"; summary: string; node?: string }[];
  artifacts: { seq: number; path: string; kind?: string; node?: string }[];
  failures: { seq: number; node: string; summary: string; sensor?: string; tool?: string }[];
  pending: { seq: number; kind: "approval" | "review" | "input"; summary: string; node?: string; tool?: string }[];
  cost: { input_tokens: number; output_tokens: number; usd: number; model_calls?: number };
  rollback_point?: Record<string, unknown>;
  last_seq: number;
  outcome?: string;
  last_outcome?: string;
}

// ---- Adapter seam -------------------------------------------------------------------------

export interface StateStore {
  /** Append one event; returns the event with seq and ts filled in. Must be durable before returning. */
  append(e: Omit<HarnessEvent, "seq" | "ts">): HarnessEvent;
  /** All events in order. */
  events(): HarnessEvent[];
  /** Persist a snapshot of the projected state (optional optimisation; the log is the truth). */
  snapshot(state: RunState): void;
  /** Directory or key the run lives under, for humans and for receipts. */
  location(): string;
}

export interface PolicyDecision {
  decision: "allow" | "deny" | "needs_approval";
  rule: string;
  reason: string;
  tier: Tier;
}

export interface PolicyEngine {
  version(): string;
  decide(req: { tool: string; args: Record<string, unknown>; node: string; contract?: Contract; run_id: string }): PolicyDecision;
  toolTier(tool: string): Tier | undefined;
}

export interface SensorResult { name: string; pass: boolean; summary: string; evidence?: Record<string, unknown>; error?: boolean }

export interface Sensor {
  name: string;
  run(ctx: SensorContext): Promise<SensorResult>;
}

export interface SensorContext {
  workspace: string;
  contract?: Contract;
  artifacts: { path: string; kind?: string }[];
  attempt: number;
  injectFailure?: (sensor: string, attempt: number) => boolean;
}

export interface ToolCall { tool: string; args: Record<string, unknown> }
export interface ToolResult { ok: boolean; output?: unknown; error?: string; artifact?: { path: string; kind?: string } }

export interface ToolAdapter {
  has(tool: string): boolean;
  execute(call: ToolCall, ctx: { workspace: string; run_id: string }): Promise<ToolResult>;
}

export interface ModelInput {
  node: string;
  node_type: NodeType;
  attempt: number;
  contract?: Contract;
  guides: { path: string; content: string }[];
  tools: string[];
  history: { node: string; outcome?: string; failures: string[] }[];
  last_failures: string[];
  plan?: string[];
}

export interface ModelOutput {
  /** For plan: the steps. For act: tool calls. For repair: what to change (free text) + optional calls. */
  plan?: string[];
  calls?: ToolCall[];
  notes?: string;
  usage?: { input_tokens: number; output_tokens: number; usd?: number };
}

export interface ModelAdapter {
  route(): string;
  propose(input: ModelInput): Promise<ModelOutput>;
}
