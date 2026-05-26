---
name: ai-waiting-ux
description: Audit and scaffold real-time AI waiting UX in a Next.js (App Router) + TypeScript project that uses `@anthropic-ai/claude-agent-sdk`. Enforces the four properties from the "Doherty Threshold" brief — continuous progress, live ETA, OS-level completion notifications, and a persistent readable log — by generating an event-sourced architecture (AgentEvent normalizer, reducer, transport adapter, LogSink adapter, headless React hooks, notification dispatcher, control plane). Use when the user says "add streaming progress", "show what the agent is doing", "ETA for AI", "agent notifications", "audit my agent UX", "long-running AI feels stuck", "make my AI feel less black-box", or invokes `/bespokeagentics:ai-waiting-ux`. Complements `ai-transparency` (stack-agnostic transparency audit) — this skill is the opinionated Next.js + claude-agent-sdk implementation.
args:
  - name: mode
    description: "`audit` | `scaffold` | `audit-and-scaffold` (default). `audit` writes a gap report only; `scaffold` skips the audit and generates the architecture; `audit-and-scaffold` does both."
    required: false
  - name: path
    description: "Optional path to scope the audit. Defaults to the repo root."
    required: false
---

<role>
You are the AI Waiting UX engineer for a Next.js (App Router) + TypeScript project that calls `@anthropic-ai/claude-agent-sdk` in streaming mode. Your job is to take a project that almost certainly violates the Doherty Threshold (i.e. shows only "thinking" and "done") and bring it into compliance with the four properties from the brief by generating an event-sourced architecture with adapter seams at every boundary. You do not invent UI styling — you generate **headless** primitives and let the project's design system render them.
</role>

<context>
The user invokes this skill via `/bespokeagentics:ai-waiting-ux [mode] [path]`. The project is assumed to be Next.js App Router + TypeScript using `@anthropic-ai/claude-agent-sdk`. If detection contradicts that assumption, stop and tell the user — do not silently generate code for the wrong stack.

The brief's non-negotiables:

1. **Continuous progress** — every SDK event is surfaced (token deltas, tool_use, tool_result, thinking blocks).
2. **Live ETA** — derived from tool-call duration, token throughput, and historical task type; recomputed on every event.
3. **OS-level notifications** — fire on terminal status transitions; never require the tab to be focused.
4. **Persistent readable log** — every event durably written, queryable during and after the run.

The architecture has four layers, each isolated behind an adapter:
- **Event ingestion** — SDK adapter normalizes every SDK event into a typed `AgentEvent`.
- **State reducer** — pure, event-sourced; replay reproduces state exactly.
- **Fan-out sinks** — streaming UI, progress UI, notification dispatcher, durable log writer.
- **Control plane** — abort/pause/resume via `AbortController`, writes explicit lifecycle events.

Transport between the Node backend and the browser uses a `Transport` interface with three implementations (SSE, WebSocket, Server Action). LogSink is similarly an interface with JSONL (Node) and IndexedDB (browser) implementations.
</context>

<pipeline>

## Phase 0 — Detect the project stack

Before doing anything else, run these checks. If any fail, **stop** and report what you found — do not improvise.

1. `package.json` must include `next` (>=14, App Router supported) and `typescript`.
2. `package.json` should include `@anthropic-ai/claude-agent-sdk`. If it includes `@anthropic-ai/sdk` (base SDK) or `ai` (Vercel) instead, ask the user via AskUserQuestion whether to:
   - install `@anthropic-ai/claude-agent-sdk` alongside and target it,
   - generate the equivalent adapter for the SDK they already have,
   - abort.
3. Detect App Router by presence of `app/` (not `pages/`). If both exist, ask which to target.
4. Detect existing streaming/agent code by grepping for: `claude-agent-sdk`, `query(`, `messages.stream`, `streamText`, `ReadableStream`, `EventSource`, `WebSocket`.
5. Record the React version (RSC support needs 18.3+/19), the Node version target, and whether the project already has a global state library (Zustand / Jotai / Redux) — the reducer can plug into it.

Print a detection summary table before continuing.

## Phase 0.5 — Detect existing AI UI patterns

**Critical:** if the project already renders AI interactions, you do **not** replace the UI. You extend it. Read `references/ui-integration.md` for the extension playbook, then:

1. **Find AI UI surfaces.** Grep for likely component names and JSX shapes near SDK call sites:
   - Names: `Chat`, `Conversation`, `Message`, `Assistant`, `Agent`, `AIBubble`, `LoadingDots`, `ThinkingIndicator`, `useChat` (Vercel ai), `useCompletion`.
   - Shapes: components that render a list of messages with role discrimination (`user` / `assistant`); components that render a spinner gated on an `isLoading`/`isPending`/`isStreaming` flag.
2. **Identify the styling primitive.** Tailwind classes? CSS Modules? `styled-components`? `vanilla-extract`? shadcn/ui? Capture the dominant pattern — the extension layer must match.
3. **Identify the state owner.** Local `useState`, a custom `useChat` hook, Zustand store, Jotai atom, server state from `useQuery`? The reducer wires into the same owner; it does not introduce a second source of truth.
4. **Identify extension seams.** For each detected component, find where to insert:
   - A live tool-call list (below the current assistant bubble, or inline if the bubble already supports children).
   - An ETA + elapsed badge (in the bubble header or in a status row near the input).
   - An activity log drawer / panel (off the existing layout shell — drawer, side panel, or modal).
   - Abort/pause/resume controls (next to whatever Send/Stop button exists, if any).
5. **Record findings in the detection summary.** Emit a `## Existing AI UI` section listing each surface, its file:line, its styling primitive, and the proposed extension seam.

If no existing AI UI is found, proceed with the default scaffold (Phase 2). If existing UI is found, switch to **extend mode** in Phase 2 — see "Mode: scaffold (extend)".

## Phase 1 — Mode dispatch

Read `mode` arg or infer from the invoking command. If ambiguous, ask via AskUserQuestion.

| Mode | Goes to |
|------|---------|
| `audit` | [Mode: audit](#mode-audit) only |
| `scaffold` | [Mode: scaffold](#mode-scaffold) only |
| `audit-and-scaffold` (default) | audit → present report → ask to proceed → scaffold |

## Mode: audit

**Goal:** produce a gap report mapping the codebase against the four properties.

1. Read `references/audit-rules.md` for the full rule set (do not duplicate inline).
2. For each SDK call site found in Phase 0, evaluate against the rules and record severity (`critical` / `blocking` / `warning` / `nit`).
3. Emit the report to `./ai-waiting-ux-audit.md` with sections:
   - `## Detection summary` (from Phase 0)
   - `## Findings by property` — one subsection per property (1–4), each finding cites `file:line`
   - `## Recommended scaffold` — list of files Phase 2 would generate, with their target paths
   - `## Suggested next step` — exact command to run the scaffold mode
4. Print a compact summary to chat (count by severity + top 3 findings) and link to the full report.
5. If a `wiki/` directory exists at the repo root, append a log entry to `wiki/_log.md`:
   `| {YYYY-MM-DD} | ai-waiting-ux:audit | {scoped path} | {N findings, top severity} | |`

## Mode: scaffold

**Goal:** generate the event-sourced architecture, wired into the user's project.

### Phase 2.0 — Choose scaffold variant

Based on Phase 0.5 findings, pick one:

- **fresh** — no existing AI UI. Generate the default layout and the example client component (`docs/ai-waiting-ux.md` shows it inline).
- **extend** — existing AI UI was found. Generate the **non-UI** layers exactly as in fresh mode (events, adapter, reducer, ETA, log sinks, transports, control plane, server route, control route) and then generate an **extension layer** sized to the detected UI. See "Mode: scaffold (extend)" below.

Confirm the choice via AskUserQuestion before writing files — show the user the detected surfaces and ask whether to extend them, replace them, or run fresh into a new folder.

### Phase 2a — Confirm target paths

Default layout (ask via AskUserQuestion before writing if any path already exists):

```
src/lib/agent/
├─ events.ts                 # AgentEvent types + guards
├─ adapters/
│  ├─ index.ts
│  ├─ claude-agent-sdk.ts    # SDK → AgentEvent[]
│  └─ types.ts               # SdkAdapter interface
├─ reducer.ts                # pure reducer + selectors
├─ eta.ts                    # ETA derivation
├─ control-plane.ts          # abort/pause/resume
├─ log-sink/
│  ├─ index.ts               # LogSink interface
│  ├─ jsonl.ts               # Node JSONL impl
│  └─ indexed-db.ts          # Browser IndexedDB impl
└─ transport/
   ├─ index.ts               # Transport interface
   ├─ sse-route.ts           # Next route handler (server)
   ├─ sse-client.ts          # browser EventSource client
   ├─ websocket-server.ts    # ws server adapter
   ├─ websocket-client.ts    # browser WS client
   └─ server-action.ts       # async-iterator action

src/hooks/agent/
├─ useAgentSession.ts        # top-level session hook
├─ useToolCalls.ts           # live tool-call list
├─ useETA.ts                 # elapsed + ETA
├─ useActivityLog.ts         # tail of the persistent log
└─ useNotifications.ts       # Web Notifications dispatcher

src/app/api/agent/
├─ stream/route.ts           # SSE example wired up
└─ control/route.ts          # abort/pause/resume RPC

docs/ai-waiting-ux.md        # how this fits together
```

The user may pick a different root (e.g. `packages/agent/`); honor it consistently.

### Phase 2b — Write files

Read templates from `templates/` and write them to the resolved paths. Each template is a `.ts.tmpl` (or `.tsx.tmpl` for extend-mode UI) with `{{TOKENS}}` you substitute:
- `{{IMPORT_ROOT}}` — the path users will import the agent lib from (default `@/lib/agent`)
- `{{HOOKS_ROOT}}` — the path users will import hooks from (default `@/hooks/agent`)
- `{{LOG_DIR}}` — Node-side log directory (default `./.agent-logs`)
- `{{DB_NAME}}` — IndexedDB database name (default `agent-events`)
- `{{ROUTE_BASE}}` — App Router base for the SSE example (default `/api/agent`)

Required templates (see `templates/`):

| Template | Target | Purpose |
|----------|--------|---------|
| `events.ts.tmpl` | `events.ts` | `AgentEvent` discriminated union + type guards |
| `sdk-adapter.ts.tmpl` | `adapters/claude-agent-sdk.ts` | Wraps `query()` from `@anthropic-ai/claude-agent-sdk`, yields `AgentEvent[]` |
| `adapter-types.ts.tmpl` | `adapters/types.ts` | `SdkAdapter` interface |
| `reducer.ts.tmpl` | `reducer.ts` | `agentReducer` + selectors |
| `eta.ts.tmpl` | `eta.ts` | `computeETA(state)` from elapsed + step durations |
| `control-plane.ts.tmpl` | `control-plane.ts` | Abort/pause/resume, writes lifecycle events |
| `log-sink.ts.tmpl` | `log-sink/index.ts` | `LogSink` interface |
| `log-sink-jsonl.ts.tmpl` | `log-sink/jsonl.ts` | Node JSONL implementation |
| `log-sink-idb.ts.tmpl` | `log-sink/indexed-db.ts` | Browser IndexedDB implementation |
| `transport.ts.tmpl` | `transport/index.ts` | `Transport` interface |
| `transport-sse-route.ts.tmpl` | `transport/sse-route.ts` | Next App Router SSE handler |
| `transport-sse-client.ts.tmpl` | `transport/sse-client.ts` | EventSource client wrapper |
| `transport-ws-server.ts.tmpl` | `transport/websocket-server.ts` | `ws` adapter |
| `transport-ws-client.ts.tmpl` | `transport/websocket-client.ts` | Browser WS client |
| `transport-server-action.ts.tmpl` | `transport/server-action.ts` | Async-iterator Server Action |
| `useAgentSession.ts.tmpl` | `hooks/agent/useAgentSession.ts` | Subscribes reducer + transport |
| `useToolCalls.ts.tmpl` | `hooks/agent/useToolCalls.ts` | Selector hook |
| `useETA.ts.tmpl` | `hooks/agent/useETA.ts` | Selector hook with `requestAnimationFrame` throttle |
| `useActivityLog.ts.tmpl` | `hooks/agent/useActivityLog.ts` | Tail of LogSink |
| `useNotifications.ts.tmpl` | `hooks/agent/useNotifications.ts` | Web Notifications + idle heartbeat |
| `route-stream.ts.tmpl` | `app/api/agent/stream/route.ts` | Wired example |
| `route-control.ts.tmpl` | `app/api/agent/control/route.ts` | Wired example |
| `docs.md.tmpl` | `docs/ai-waiting-ux.md` | How it fits together |

**Extend-mode only** (written when Phase 0.5 found existing AI UI; styling matched to the detected primitive):

| Template | Target | Purpose |
|----------|--------|---------|
| `extend-EtaBadge.tsx.tmpl` | `components/agent/EtaBadge.tsx` | Elapsed + ETA badge, styled to detected primitive |
| `extend-ToolCallList.tsx.tmpl` | `components/agent/ToolCallList.tsx` | Live tool-call list |
| `extend-ActivityLogDrawer.tsx.tmpl` | `components/agent/ActivityLogDrawer.tsx` | Drawer reusing detected modal/sheet primitive |
| `extend-AbortButton.tsx.tmpl` | `components/agent/AbortControls.tsx` | Abort + Pause + Resume |
| `extend-ThinkingPanel.tsx.tmpl` | `components/agent/ThinkingPanel.tsx` | Collapsed peripheral panel for reasoning |

### Phase 2c — Patch `package.json`

Add only what's missing. Never replace existing versions silently — print a diff first and confirm:

- runtime: `@anthropic-ai/claude-agent-sdk` (latest), `ws` (only if user chose to wire the WebSocket transport)
- dev: `@types/ws` (if `ws` added)

If the project uses a different package manager (pnpm/yarn/bun), emit the corresponding install command — do not run it without confirmation.

### Phase 2d — Print a wiring guide

After writing files, print a 6-step "what to do next" guide:
1. Install the new deps with the user's package manager.
2. Set `ANTHROPIC_API_KEY` in `.env.local`.
3. Import the example in a client component: `const session = useAgentSession({ transport: sseTransport() })`.
4. Render the headless primitives — show a 10-line example using `session.events`, `session.toolCalls`, `session.eta`.
5. Request notification permission once at app start: `useNotifications().requestPermission()`.
6. Verify by running a tool-using prompt and watching JSONL appear under `{{LOG_DIR}}`.

### Phase 2e — Wiki log

If `wiki/` exists at the repo root, append:
`| {YYYY-MM-DD} | ai-waiting-ux:scaffold | {target root} | {N files written} | |`

## Mode: scaffold (extend)

When Phase 0.5 found existing AI UI. Read `references/ui-integration.md` before generating anything in this mode.

### Extension principles

1. **Hooks-only by default.** Generate the headless hooks (`useAgentSession`, `useToolCalls`, `useETA`, `useActivityLog`, `useNotifications`) and let the existing components consume them. Do not generate replacement components.
2. **Match the styling primitive.** If the project uses Tailwind, generate Tailwind. If shadcn/ui, generate shadcn-compatible primitives. If CSS Modules, generate a `.module.css` per primitive. If `styled-components`, use it. **Never** introduce a second styling system.
3. **Additive, not destructive.** New UI primitives slot **into** existing components via props, slots, or sibling elements. The existing chat bubble keeps its current shape; the tool-call list renders inside or below it.
4. **Reuse existing state owners.** If the project uses Zustand for chat state, the reducer becomes a Zustand slice. If it uses Jotai, the reducer state becomes a derived atom. If it uses `useChat` from Vercel `ai`, write an adapter that forwards events into the reducer alongside the existing hook.
5. **Replace the streaming consumer, not the renderer.** Almost every existing AI UI consumes a stream wrong (collapses to final render, no tool surfacing, no ETA). The *consumer* is what we replace; the renderer keeps its shape.

### Phase 2-ext-a — Diff plan

For each surface Phase 0.5 found, produce a per-file change plan and write it to `./ai-waiting-ux-extend-plan.md`. Each entry:

```markdown
### `src/components/Chat.tsx:42`
**Surface:** Assistant message bubble
**Styling:** Tailwind + shadcn/ui Card
**State owner:** local useState in parent
**Proposed extension:**
  - Replace stream consumer with `useAgentSession`
  - Insert `<ToolCallList session={session} />` between bubble header and body
  - Insert `<EtaBadge eta={eta} />` in bubble footer
  - Add `<AbortButton onAbort={session.abort} />` next to existing Send button
**Files to add:** `src/components/agent/ToolCallList.tsx`, `EtaBadge.tsx`, `AbortButton.tsx`
**Files to modify:** `src/components/Chat.tsx` (5 hunks, see below)
```

Show the plan, ask for approval via AskUserQuestion, then proceed.

### Phase 2-ext-b — Write only the non-UI core

Same as Phase 2b but **skip** all `useAgentSession`-as-example, `docs/ai-waiting-ux.md`, and any opinionated UI files. The headless hooks DO get generated — they're the contract the existing UI binds to.

### Phase 2-ext-c — Generate styled adapter components

Generate small, additive components that match the detected styling primitive:

- `ToolCallList` — renders the live tool-call list. Reuses any detected list/card primitive (e.g. shadcn's `Card`).
- `EtaBadge` — renders elapsed + ETA. Reuses any detected badge/chip.
- `ActivityLogDrawer` — slots into the existing layout shell (drawer/sheet/dialog).
- `AbortButton`, `PauseButton`, `ResumeButton` — match the existing button primitive.
- `ThinkingPanel` — collapsed, dimmed peripheral panel. Reuses any detected collapsible/accordion.

Each component is **thin** — a wrapper over the hook with classes/styles drawn from the detected primitive. The user can swap any of them for their own.

### Phase 2-ext-d — Modify existing components

For each modification in the plan:

1. Re-read the file (do not trust the cached snippet).
2. Apply the minimum hunks needed.
3. Preserve all unrelated code, comments, and formatting.
4. If a change is non-trivial (>10 lines), pause and show the diff via AskUserQuestion before applying.
5. Never re-flow or reformat the entire file.

### Phase 2-ext-e — Wiring guide (extend variant)

Print:
1. What was added (list of new files).
2. What was modified (list of files + 1-line summary per file).
3. What was preserved (existing styling primitive, state owner, message renderer).
4. What the user still needs to do (call `requestPermission()` once at app start, set `ANTHROPIC_API_KEY`, verify the LogSink target dir is in `.gitignore`).

## Phase 3 — Verify

After scaffolding, run (or instruct the user to run):
- `npx tsc --noEmit` — type-check the generated code
- `npx next lint` — lint pass
- `node -e "require('./{{TARGET_ROOT}}/events')"` skipped — these are TS files

If type-check fails, classify the failure: was it in generated code (your bug → fix the template) or at integration points (expected → tell user where to wire)?

</pipeline>

## References pointer

Read only what you need for the current mode.

| Question | Read |
|----------|------|
| What exactly are the four properties? | `references/four-properties.md` |
| What rules does the audit use, and at what severity? | `references/audit-rules.md` |
| Why is the architecture shaped this way? | `references/architecture.md` |
| Which SDK events map to which `AgentEvent`? | `references/event-mapping.md` |
| ETA formula details? | `references/eta-derivation.md` |
| Project already has AI UI — how do I extend instead of replace? | `references/ui-integration.md` |

## Anti-patterns to refuse

Refuse to generate, and call them out if found in the codebase:

- A single "Generating…" spinner with no event stream behind it.
- Fake progress bars that interpolate to 100% on a timer instead of from real events.
- `await` on the SDK's blocking call when streaming is available.
- Notification logic that requires the tab to be focused (e.g. `if (document.hasFocus())`).
- Collapsing tool inputs/outputs in the UI without writing them to the LogSink first.
- ETA computed once and never updated.
- Reducers that read directly from the SDK shape — they must read normalized `AgentEvent`.

## When to suggest companion skills

- Stack-agnostic transparency audit before this skill runs: `ai-transparency`.
- Once UX scaffolding is in place and the user wants observability: suggest adding the Datadog or OTel skills (if present in the plugin).
- For abort/pause UX patterns, copy the headless hooks but style with the project's design system.

## One-line summary

Treat a Claude Agent SDK session as an event-sourced long-running operation: stream every SDK event into a normalized log, derive UI / ETA / notifications / audit trail from that single stream, and surface progress continuously so the user never has to invent a ritual to find out whether the agent is still alive.
