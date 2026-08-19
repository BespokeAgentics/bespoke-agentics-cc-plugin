# Audit Rules

Used by Mode: audit. Each rule maps to one of the four properties. Severity scale:

- **critical** — directly violates a property; users cannot tell the agent is alive
- **blocking** — silently degrades the property (e.g. UI works but log is dropped on error)
- **warning** — pattern works today but will break under load or extended thinking
- **nit** — style/consistency

Cite every finding as `file:line` with a one-line quote.

## Property 1 — Continuous progress

| ID | Severity | Rule |
|----|----------|------|
| P1-A | critical | An SDK call site uses the blocking call shape (no streaming iterator, no async-iterator consumption). Look for `await query(...)` without iteration, or `messages.create` instead of `messages.stream`. |
| P1-B | critical | Streaming iterator is consumed but only the final assistant text is rendered; tool_use / tool_result blocks are never surfaced. |
| P1-C | blocking | Tool inputs are logged server-side but the client UI shows only "Calling tool…" with no name or arguments. |
| P1-D | blocking | Thinking/reasoning blocks (extended thinking enabled) are dropped instead of rendered in a collapsed peripheral panel. |
| P1-E | warning | Stream consumption runs on the main thread without `requestAnimationFrame` throttling — layout thrash at high token rates. |
| P1-F | warning | UI logic branches off the raw SDK event shape (e.g. `if (event.type === 'content_block_delta')` in a component) instead of a normalized `AgentEvent`. |
| P1-G | nit | Step counter is absent or hard-coded ("Step 1 of 1"). |

## Property 2 — Live ETA

| ID | Severity | Rule |
|----|----------|------|
| P2-A | critical | No elapsed-time counter visible during a run. |
| P2-B | critical | ETA, if shown, is computed once and never recomputed. |
| P2-C | blocking | ETA shown but derived from a static constant (e.g. `"~30s"`), not from observed events. |
| P2-D | warning | ETA stops updating when the tab is backgrounded — use `Date.now()` deltas, not `setInterval` alone. |
| P2-E | warning | Fake progress bar that interpolates to 100% on a timer rather than mapping to real events. |
| P2-F | nit | ETA shown without uncertainty ("warming up", "refining") on cold sessions. |

## Property 3 — OS notifications

| ID | Severity | Rule |
|----|----------|------|
| P3-A | critical | Completion signaling depends on the tab being focused (`document.hasFocus()`, `visibilitychange` only). |
| P3-B | critical | No notification dispatched on terminal status (`message_stop`, error, abort). |
| P3-C | blocking | Notification permission requested on first dispatch instead of once at app start. |
| P3-D | blocking | Notification has no deep link back to the session. |
| P3-E | warning | No idle-gap heartbeat — a 5-minute silent run looks identical to a dead connection. |
| P3-F | warning | Native context (Electron/Tauri) falls back to Web Notifications when native channel is available. |

## Property 4 — Persistent readable log

| ID | Severity | Rule |
|----|----------|------|
| P4-A | critical | No durable write of streamed events; logs live only in memory or `console`. |
| P4-B | critical | Tool inputs/results truncated **in storage**, not just in UI. |
| P4-C | blocking | Log writes are throttled or coalesced — every event must persist, full fidelity. |
| P4-D | blocking | Reducer cannot be reconstructed from the log (state stored alongside but not derived from events). |
| P4-E | warning | Log lacks `sessionId`, `modelId`, or `tokenCounts` — replay and cost analysis become impossible. |
| P4-F | warning | No live tail UI — users still resort to inspecting raw files. |
| P4-G | nit | Logs not segmented per session — one giant rolling file. |

## Cross-cutting

| ID | Severity | Rule |
|----|----------|------|
| X-A | critical | Multiple UI surfaces consume the SDK stream directly — fan-out happens at the SDK boundary instead of from a single reducer. |
| X-B | blocking | Abort/pause flows do not write a lifecycle event to the log — partial state lost on cancel. |
| X-C | warning | `AbortController` is created per-render or not propagated into the SDK call. |
| X-D | warning | `useEffect` that opens an `EventSource`/`WebSocket` lacks a cleanup function. |

## Existing UI extension (only fires in extend mode)

These rules check that the project's existing AI UI was extended correctly. Run these after the scaffold writes files in extend mode.

| ID | Severity | Rule |
|----|----------|------|
| U-A | critical | Existing assistant message bubble was deleted or replaced rather than extended. |
| U-B | blocking | Extension introduces a styling primitive the project doesn't already use (e.g. Tailwind added to a CSS-Modules project). |
| U-C | blocking | A second source of truth for assistant text now exists — both `messages[]` and `session.state.textBuffer` are rendered with no mirror. |
| U-D | blocking | A new modal/drawer/sheet primitive was introduced when one already existed. |
| U-E | warning | Existing `Stop`/`Cancel` button was left wired to the old (no-op) handler instead of `session.abort`. |
| U-F | warning | Existing loading/spinner element was removed entirely instead of augmented with the ETA badge. |
| U-G | nit | className strings on unrelated elements were modified beyond what the integration required. |

## Output format

Write findings to `./ai-waiting-ux-audit.md`:

```markdown
# AI Waiting UX Audit — {ISO date}

## Detection summary
- Next.js: {version}
- SDK: {package} {version}
- React: {version}
- App Router: {yes/no}
- Existing streaming code: {file paths or "none"}

## Findings

### Property 1 — Continuous progress
- **[critical · P1-A]** `app/chat/route.ts:42` — `await query(prompt)` is blocking; users see no intermediate events.
  > `const result = await query({ prompt, options: { stream: false } });`
- ...

### Property 2 — Live ETA
...

### Property 3 — OS notifications
...

### Property 4 — Persistent readable log
...

### Cross-cutting
...

## Recommended scaffold
{generated file list with target paths}

## Suggested next step
Run `/bespoke-agentics:ai-waiting-ux scaffold` to generate the missing modules.
```

Print to chat: count by severity (e.g. "3 critical, 7 blocking, 2 warning, 1 nit") plus the top 3 findings.
