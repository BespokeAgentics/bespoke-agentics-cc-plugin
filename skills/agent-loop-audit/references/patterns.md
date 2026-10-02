# Agent-Loop Audit — Correct-Pattern Reference

Reference shapes for fixes. Adapt names, error utilities, and logging to the project's own
conventions (Phase 0) — never paste verbatim over existing style. The canonical loop, in order:

1. Attach listener, **await open confirmation**
2. Send initial payload
3. Loop over event packets, decoding by family
4. On every idle: branch on stop reason
5. Differentiated error handling (transient → reconnect/resume; hard → surface)
6. Steering: interrupt + new message in the same session

---

## TypeScript — canonical loop (fixes EL1, EL2, SR1, SR2, SR3)

```ts
// Sends are POSTs to the session; the stream (SSE) only receives.
const send = (events: SessionEvent[]) =>
  client.beta.sessions.events.send(sessionId, { events });

// 1–2. Listener first, payload second — never in parallel (EL1).
const stream = await client.beta.sessions.events.stream(sessionId); // open BEFORE sending
await send([{ type: "user.message", content: [{ type: "text", text: task }] }]);

// 3. Consume — the stream is the control surface; never fire-and-forget (EL2).
for await (const event of stream) {
  switch (eventFamily(event)) {                            // OB1: decode by family
    case "agent":   onAgentEvent(event); break;            // reasoning, tool calls → debug layer
    case "session": {
      if (event.type === "session.status_idle") {
        // 4. Idle ≠ done (SR1). The stop reason decides (SR2/SR3).
        switch (event.stop_reason?.type) {
          case "end_turn":
            return finalize(event);   // an interrupted turn also ends here — track interrupts you sent
          case "requires_action":
            // Client responsibility: answer every pending event, or the
            // server-side process waits indefinitely (SR2 / EL3). Each ID is an
            // agent.tool_use / agent.mcp_tool_use (→ user.tool_confirmation) or
            // agent.custom_tool_use (→ user.custom_tool_result) event.
            await send(event.stop_reason.event_ids.map(answerPendingEvent));
            break; // agent resumes; keep looping
          case "budget_reached":
            return pausedAtBudget(event); // only settle events accepted until the budget changes
          default:
            await steer(); // interrupt & redirect, or keep waiting
        }
      }
      break;
    }
    case "span": recordMetrics(event); break;              // OB4: span.model_request_end.model_usage
  }
}
```

## TypeScript — differentiated errors + reconnect/resume (RS1, RS3, RS4, RS6)

```ts
async function runWithResilience(task: Task) {
  let lastEventId: string | undefined;
  for (let attempt = 0; attempt < MAX_ATTEMPTS; attempt++) {
    try {
      return await withSilenceWatchdog(WATCHDOG_MS, (signal) =>   // RS3
        consumeLoop(task, { resumeFrom: lastEventId, signal,      // RS4: resume cursor
                            onEvent: (e) => (lastEventId = e.id) }));
    } catch (err) {
      if (isTransient(err)) {              // RS1: network break / 5xx / watchdog trip
        await sleep(backoffWithJitter(attempt));                  // RS6
        continue;                          // reconnect + resume, session preserved
      }
      throw err;                           // RS1: hard API failure — surface, don't retry
    }
  }
  throw new Error("agent loop: retries exhausted");
}
```

## TypeScript — steering (RS2) and safe teardown (EL3)

```ts
// Steering: halt mid-execution and redirect IN THE SAME SESSION — no teardown,
// context preserved. Server stops, acknowledges, resumes on the new task.
await send([
  { type: "user.interrupt" },
  { type: "user.message", content: [{ type: "text", text: newInstruction }] },
]);

// Teardown: never disconnect with pending required actions (EL3).
// pendingEventIds = the event_ids from the last requires_action idle.
// Call this before leaving the `for await` loop over the stream; breaking out
// of the loop is what closes it.
async function answerPendingBeforeClose(pendingEventIds: string[]) {
  await send(pendingEventIds.map((id) =>
    decline(id, "client shutting down"))); // user.tool_confirmation {result: "deny"} or a custom_tool_result error
}
```

## TypeScript — idempotent tool execution (RS5)

```ts
const executed = new Set<string>();
async function executeToolCall(call: ToolCall) {
  if (executed.has(call.id)) return cachedResult(call.id); // replay-safe after reconnect
  executed.add(call.id);
  return await runTool(call);
}
```

---

## Python (asyncio) — canonical loop

```python
async def run_task(client, session_id: str, task: str):   # client = AsyncAnthropic()
    async def send(events):                               # sends are POSTs; the stream only receives
        await client.beta.sessions.events.send(session_id=session_id, events=events)

    # 1–2. Listener first (EL1): open the stream, then send.
    async with client.beta.sessions.events.stream(session_id=session_id) as stream:
        await send([{"type": "user.message", "content": [{"type": "text", "text": task}]}])

        # 3. Consume (EL2).
        async for event in stream:
            family = event_family(event)                  # OB1
            if family == "agent":
                on_agent_event(event)
            elif event.type == "session.status_idle":
                reason = event.stop_reason                # SR1: idle ≠ done
                if reason.type == "end_turn":             # also what an interrupted turn reports
                    return finalize(event)
                if reason.type == "requires_action":      # SR2: client must answer
                    # agent.tool_use / agent.mcp_tool_use → user.tool_confirmation;
                    # agent.custom_tool_use → user.custom_tool_result
                    await send([answer_pending_event(eid) for eid in reason.event_ids])
                    continue                              # agent resumes
                if reason.type == "budget_reached":
                    return paused_at_budget(event)        # only settle events accepted
                await steer(send)                         # interrupt & redirect
            elif family == "span":
                record_metrics(event)                     # OB4: span.model_request_end.model_usage
```

## Python — resilience wrapper

```python
async def run_with_resilience(task):
    last_event_id = None
    for attempt in range(MAX_ATTEMPTS):
        try:
            async with asyncio.timeout(WATCHDOG_S):                    # RS3
                return await consume_loop(task, resume_from=last_event_id)  # RS4
        except TRANSIENT_ERRORS as e:                                  # RS1
            await asyncio.sleep(backoff_with_jitter(attempt))          # RS6
            continue
        # hard API failures propagate (RS1) — do not blanket `except Exception`
    raise RuntimeError("agent loop: retries exhausted")
```

## Python — steering + safe teardown

```python
# RS2 — same session, no teardown:
await send([
    {"type": "user.interrupt"},
    {"type": "user.message", "content": [{"type": "text", "text": new_instruction}]},
])

# EL3 — answer pending events (event_ids from the last requires_action idle) before closing:
async def safe_close(stream, pending_event_ids):
    await send([decline(eid, reason="client shutting down") for eid in pending_event_ids])
    await stream.close()
```

---

## Layered surfacing (OB2)

Decode once; route by audience. Same stream, different layers — debug clients see reasoning and
tool activity, production clients see clean progress:

```ts
function onAgentEvent(e: AgentEvent) {
  debugLog.append(e);                       // engineering view: full narration
  if (isUserRelevant(e)) ui.progress(summarize(e)); // production view: calm summary
}
```

## Anti-pattern gallery (what the greps catch)

```ts
// EL1 — payload racing the listener:
sendTask(payload);                    // ← fired first
const es = new EventSource(url);      // ← initial events already gone

// SR1 — idle treated as done:
if (event.type === "session.status_idle") { resolve(result); } // no stop_reason check

// RS1 — conflated errors:
try { await loop(); } catch { /* retry forever */ }

// EL3 — deadlocking teardown:
finally { stream.close(); }           // pending tool approvals never answered
```
