# Agent-Loop Audit — Rule Catalog

Tiered: the **core catalog** applies to any event-stream agent client; the **Anthropic pack**
(§ at the end) binds the same rules to concrete Anthropic managed-agent vocabulary and activates
when Phase 0 detects an Anthropic SDK. Rules marked **[BP]** are best-practice extensions beyond
the source teaching; everything else is distilled directly from it.

Severity scale:

| Severity | Meaning |
|----------|---------|
| CRITICAL | Produces silent hangs, stalls, or server-side deadlocks — the "it just freezes" class |
| HIGH     | Reliability loss under real-world conditions (network breaks, long tasks, redelivery) |
| MEDIUM   | Missing capability — steering, observability, layered UI |
| LOW      | Protocol hygiene |

---

## EL — Event-Loop Lifecycle

### EL1 · CRITICAL · Payload-before-listener race
The task payload is sent before the event listener/stream subscription is confirmed open. The
stream only delivers events after the listener is open, so the initial events are **lost** —
missed signals, then a stall that looks like a network or server fault.
**Symptom:** app hangs at startup; works intermittently (the race sometimes wins).
**Correct:** attach listener → await open/ready confirmation → then send payload. The official
SDKs enforce this ordering; hand-rolled transport must reproduce it.

Detection (TS/JS):
- A `fetch`/`POST`/`client.*.create(...)` dispatch that precedes `new EventSource(...)`,
  `ws.addEventListener('open', ...)`, or a stream subscription in the same flow
- Listener attached but dispatch not awaited behind the open event/ready promise
- `Promise.all([subscribe(), sendTask()])` — parallel, not sequenced

Detection (Python):
- `client.messages.create(...)` / task POST issued before `async for event in stream` is entered
  or before the SSE/WebSocket connect coroutine resolves
- `asyncio.gather(subscribe(), send_task())` without ordering

### EL2 · CRITICAL · Fire-and-forget dispatch
A task is dispatched but nothing consumes the event stream — no `for await`, no `.on('message')`,
no `async for`. The agent narrates its work to nobody; completion and requires-action signals are
never seen.
**Symptom:** task "runs" but the app never learns the outcome.

Detection: dispatch call whose returned stream/response is unused; subscription callback that is
empty or only logs.

### EL3 · CRITICAL · Unsafe teardown with pending required actions
The client disconnects, returns, or exits while the server is blocked awaiting a client response
(tool-call approval/permission). The server-side process enters an **indefinite deadlock**.
**Symptom:** session hangs forever server-side; retries pile up.
**Correct:** before closing, check for pending required actions and answer (approve/decline) each
pending tool-call ID first.

Detection: `close()` / `abort()` / process-exit / request-handler return paths with no check of
pending-action state; `finally` blocks that only close the socket.

### EL4 · MEDIUM · Hand-rolled loop where the official SDK exists
Raw SSE/WebSocket/HTTP reimplementation of a loop the already-installed official SDK manages —
reintroducing the EL1 race class and losing enforced ordering.
Detection: SDK in dependencies but transport built from `EventSource`/`fetch` streaming for the
same provider.

---

## SR — Stop-Reason & State Semantics

### SR1 · CRITICAL · Idle treated as done
The session is finalized/terminated upon receiving an idle status. **Idle means momentarily
inactive, not finished.** The actual stopping criterion is the stop-reason field in the event
payload.
**Symptom:** truncated results; tasks "complete" half-done; or (when idle precedes a
requires-action) the app exits while the server still waits — see EL3.

Detection: branch on the idle event that resolves/returns/`break`s without reading a stop-reason
field.

### SR2 · CRITICAL · Requires-action never answered
No code path handles the "blocked awaiting client approval" stop reason. The pending tool-call
event IDs nested in the payload are the client's responsibility to answer; silence = indefinite
server-side hang.
**Symptom:** the canonical silent hang — agent idle, waiting for a response the client never sends.

Detection: stop-reason handling with only a success arm; no reference to tool-approval /
permission-response APIs anywhere in the surface; `switch`/`if` on stop reason lacking a
default/blocked arm.

### SR3 · HIGH · No branch logic on idle
Events are consumed but idle handling doesn't route: finalize on completion, answer approvals on
requires-action, or interrupt-and-redirect otherwise. Idle events are ignored or merely logged.

Detection: event loop with no conditional on session-status/idle events.

### SR4 · MEDIUM · Every stop conflated with success
Terminal handling assumes completion; blocked/interrupted outcomes surface to the user as success.

Detection: single "done" handler; no distinct UX/logging for blocked vs completed.

---

## RS — Resilience & Steering

### RS1 · HIGH · No error differentiation
Transient network breaks and hard API failures take the same path (or none). Transient breaks
should reconnect/resume; hard failures should surface and stop. Conflating them yields either
infinite retry of a permanent failure or a dead session after a Wi-Fi blip.

Detection: single generic `catch`/`except` around the loop; no status-code or error-class
inspection; no reconnect path.

### RS2 · MEDIUM · No steering path
No way to halt the agent mid-execution and redirect. Because the stream is bidirectional, the
client can send an interrupt followed by a new instruction **in the same session** — the server
stops the current process, acknowledges, and resumes on the new task, preserving session context.
Without this, corrections require full teardown + resend (wasted tokens, lost context).

Detection: no interrupt/cancel API usage; "cancel" implemented as socket close + new session.

### RS3 · HIGH · No silence watchdog **[BP]**
No timeout on event silence. A healthy loop expects a steady narration; N seconds of nothing
should trigger a health probe or reconnect, not an indefinite wait.
Detection: no timer/deadline around the consume loop.

### RS4 · HIGH · No reconnect/resumption **[BP]**
A dropped stream loses the session: no backoff-with-jitter reconnect, no resume
cursor/last-event-ID replay.
Detection: no retry wrapper on connect; no persisted last-event marker.

### RS5 · MEDIUM · Non-idempotent tool execution **[BP]**
Redelivered tool-call events (after reconnect/replay) execute side effects twice.
Detection: tool executor keyed on nothing; no seen-ID set or idempotency key.

### RS6 · LOW · Unbounded/naive retries **[BP]**
Retries without cap or jitter; hammering during provider incidents.

---

## OB — Observability & Protocol Hygiene

### OB1 · MEDIUM · Event families not decoded
The protocol's output events arrive in distinct families — agent narration (reasoning, tool
calls), session status/control flow, and observability metrics — but the client lumps or drops
them instead of decoding the structured JSON packets. Debugging and UI are both blinded.
Detection: `JSON.parse` result used only for one field; event-type field never switched on.

### OB2 · MEDIUM · No layered surfacing
Fine-grained agent events (internal reasoning, tool activity) aren't available to any
engineering/debug view. The modular pattern: decode once, show detail in debug clients, hide it in
clean production clients — same stream, different layers.
Detection: events go straight to a single UI string or nowhere.

### OB3 · LOW · Outgoing events outside the input vocabulary
The input side of the protocol is a small fixed set of event types. Sending improvised event
shapes yields silent drops.
Detection: hand-built event objects with nonstandard `type` values.

### OB4 · LOW · Metrics ignored **[BP]**
Timing/token observability events discarded — no latency or cost capture.

### OB5 · HIGH · Secrets in client **[BP]**
API key present in browser/client-bundled code.
Detection: SDK constructed with a key in frontend source; `dangerouslyAllowBrowser`.

---

## Anthropic Pack (activates on SDK detection)

Detection: `@anthropic-ai/claude-agent-sdk` or `@anthropic-ai/sdk` in package.json;
`anthropic` in requirements/pyproject; imports thereof.

Vocabulary bindings — audit against these concrete names when the pack is active:

| Core concept | Anthropic vocabulary |
|---|---|
| Input events (fixed set of 5) | chiefly `user.message` (initiate task), `user.interrupt` (halt/steer) |
| Output family 1 — agent narration | agent events: reasoning text, tool calls |
| Output family 2 — system status/control | session events, incl. `session.status.idle` |
| Output family 3 — observability | fan events: timing, token metrics |
| Idle signal | `session.status.idle` — momentary inactivity, **not** completion (SR1) |
| Stopping criterion | `stop_reason` field in the event payload (SR1–SR4) |
| Blocked-on-client value | requires-action: pending tool-call event IDs nested inside `stop_reason` payload; client must approve/respond (SR2, EL3) |
| Steering | combined `user.interrupt` + new `user.message` packet in the same session (RS2) |

Pack-specific greps: `stop_reason`, `session.status`, `user.interrupt`, `user.message`,
`tool_use`/approval APIs, `client.beta.*` agent endpoints.

For other vendors (OpenAI Assistants/Realtime, etc.) apply the core rules and note the analogous
vocabulary (`requires_action` + `submit_tool_outputs`, `response.done`, etc.) as
`unconfirmed-vendor` mappings unless verified against that SDK's docs.
