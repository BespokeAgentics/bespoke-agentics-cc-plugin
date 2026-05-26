# Architecture

Why the code is shaped this way. Read this only if you are about to scaffold, customize, or explain the architecture to the user.

## Four layers, four adapters

```
              ┌────────────────────────────────────────────────────┐
              │              @anthropic-ai/claude-agent-sdk        │
              └─────────────────────┬──────────────────────────────┘
                                    │ raw SDK events
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1 — Event ingestion       SdkAdapter (interface)         │
│  ClaudeAgentSdkAdapter normalizes every SDK event into          │
│  a typed AgentEvent {id, sessionId, timestamp, type, payload}   │
└─────────────────────┬───────────────────────────────────────────┘
                      │ AgentEvent[] (single source of truth)
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  Layer 2 — State reducer         agentReducer                   │
│  Pure, event-sourced. Selectors: currentStep, activeToolCall,   │
│  completedToolCalls, cumulativeTokens, elapsedMs, etaMs, status │
└─────────────────────┬───────────────────────────────────────────┘
                      │ fan-out (all in parallel, no ordering)
                      ▼
┌──────────────┬──────────────┬──────────────────┬────────────────┐
│ Streaming UI │ Progress UI  │ Notification     │ Durable log    │
│ (token + tool│ (step + ETA  │ dispatcher       │ writer         │
│ call list)   │  + elapsed)  │ (Web/OS, idle    │ (LogSink:      │
│              │              │  heartbeat)      │  JSONL / IDB)  │
└──────────────┴──────────────┴──────────────────┴────────────────┘
                      ▲
                      │ control events (aborted, paused, resumed)
                      │
┌─────────────────────┴───────────────────────────────────────────┐
│  Control plane                                                  │
│  AbortController + pause/resume; writes lifecycle events back   │
│  into the reducer so partial state is preserved on cancel.      │
└─────────────────────────────────────────────────────────────────┘
```

## Why an adapter at every boundary

- **SdkAdapter** — Anthropic ships multiple SDKs (Claude Agent SDK, base Messages API, future product SDKs). Wrapping each one means the rest of the system never changes when the SDK does. The Claude Agent SDK adapter is the only one this skill writes by default; stubs for `@anthropic-ai/sdk` and Vercel `ai` live alongside as `.todo.ts` so users can fill them in.
- **Transport** — Next.js apps disagree on transport. SSE is the right default (one-way, auto-reconnect, simple route handler). WebSocket is needed when control commands must travel on the same channel. Server Actions work but stream ergonomics are weaker. All three implement the same interface so swapping is one line.
- **LogSink** — log destination is opinionated per environment. Node writes JSONL files; browser writes to IndexedDB. Both implement the same interface so the reducer never knows which is active.

## The `AgentEvent` discriminated union

Everything downstream depends on this shape staying stable. The skill emits:

```ts
type AgentEvent =
  | { type: 'session.start';   sessionId; timestamp; modelId; prompt }
  | { type: 'message.start';   sessionId; timestamp; messageId }
  | { type: 'text.delta';      sessionId; timestamp; messageId; text }
  | { type: 'thinking.delta';  sessionId; timestamp; messageId; text }
  | { type: 'tool.use';        sessionId; timestamp; toolUseId; toolName; input }
  | { type: 'tool.result';     sessionId; timestamp; toolUseId; output; isError }
  | { type: 'message.stop';    sessionId; timestamp; messageId; stopReason; usage }
  | { type: 'session.stop';    sessionId; timestamp; status: 'success' | 'error' | 'aborted'; error? }
  | { type: 'heartbeat';       sessionId; timestamp; lastEventAt }
  | { type: 'control.abort';   sessionId; timestamp; reason? }
  | { type: 'control.pause';   sessionId; timestamp }
  | { type: 'control.resume';  sessionId; timestamp }
```

Add new event types by extending the union — never by stuffing payload variants into an existing type. Reducers must use exhaustive switches on `event.type` so TypeScript catches missed cases at compile time.

## Reducer design

The reducer is pure and event-sourced. Its state shape:

```ts
type SessionState = {
  sessionId: string
  status: 'idle' | 'running' | 'paused' | 'success' | 'error' | 'aborted'
  startedAt: number
  endedAt: number | null
  lastEventAt: number
  currentStep: number       // ordinal — increments on tool.use
  activeToolCall: ToolCall | null
  completedToolCalls: ToolCall[]
  textBuffer: string        // current assistant message accumulating
  thinkingBuffer: string    // current thinking block (if extended thinking on)
  cumulativeUsage: { inputTokens: number; outputTokens: number }
  modelId: string | null
  etaMs: number | null      // null until enough signal
  history: { type: AgentEvent['type']; durationMs: number }[]  // for ETA
}
```

Selectors are co-located with the reducer so hooks import named functions (not raw state access) — this makes the React subscription surface stable.

## ETA derivation

Recompute on every event:

```
etaMs = (avgToolDurationMs * estimatedRemainingTools)
      + (textRemainingTokens / observedTokensPerSec * 1000)
```

- `avgToolDurationMs` — mean of `completedToolCalls[i].durationMs`; null until 2 tool calls observed.
- `estimatedRemainingTools` — heuristic: if `historicalTaskType` known, use median tool count; else `max(0, observedStepBudget - currentStep)` where `observedStepBudget` defaults to 12.
- `textRemainingTokens` — `cumulativeUsage.outputTokens`-weighted projection; floor at 0.
- `observedTokensPerSec` — rolling 5-second window.

When signals are insufficient, expose `etaMs = null` and let hooks render "warming up". Never lie with a frozen number.

## Fan-out is not orchestrated

The reducer is a passive subject. Sinks subscribe; they never coordinate. This is what makes replay trivial:

```
events.jsonl  →  agentReducer  →  fresh SessionState identical to live
```

If you find yourself adding "make sure the log writer flushes before the UI updates" — stop. They're independent. The log just appends.

## Control plane round-trip

User clicks Abort →
1. Client calls `transport.send({ type: 'control.abort', sessionId })`
2. Server receives, calls `abortController.abort('user-requested')`
3. SDK throws inside the iterator
4. Adapter catches, emits `{ type: 'session.stop', status: 'aborted' }`
5. LogSink writes the lifecycle event
6. Reducer transitions to `aborted`
7. Notification dispatcher fires "Aborted" with deep link

The same path holds for pause/resume — `pause` simply stops draining the iterator without aborting it, and `resume` reattaches the drain loop. (Pause is best-effort; some SDK operations may not be pausable mid-flight.)

## Throttling rules

- **UI updates** — coalesce to `requestAnimationFrame` (≈16 ms). Use a single subscription that batches reducer dispatches per frame.
- **Log writes** — never throttle. Every event persists.
- **Notification fires** — debounced to terminal transitions and idle gaps (>60 s default, configurable).
- **ETA recomputation** — every event; the math is O(1) and the cost is negligible.

## Where Next.js App Router fits

- The SSE route handler lives at `app/api/agent/stream/route.ts`. It returns a `Response` wrapping a `ReadableStream` of SSE-formatted events.
- Server Components cannot subscribe to the reducer — keep all hooks in client components (`'use client'`).
- Server Actions can stream via the async-iterator return pattern; the Server Action transport implementation uses it. Stream ergonomics are weaker than route handlers for high-frequency token events, so SSE remains the default.
- Edge runtime is supported by the SSE route but the JSONL LogSink needs Node runtime — set `export const runtime = 'nodejs'` if Node-side logging is required.
