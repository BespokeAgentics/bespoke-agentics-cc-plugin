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
// 1–2. Listener first, payload second — never in parallel (EL1).
const stream = await client.sessions.connect(sessionId);   // resolves when listener is OPEN
await stream.ready;                                        // explicit open confirmation
await stream.send({ type: "user.message", content: task }); // payload only after confirmation

// 3. Consume — the stream is the control surface; never fire-and-forget (EL2).
for await (const event of stream) {
  switch (eventFamily(event)) {                            // OB1: decode by family
    case "agent":   onAgentEvent(event); break;            // reasoning, tool calls → debug layer
    case "session": {
      if (event.type === "session.status.idle") {
        // 4. Idle ≠ done (SR1). The stop reason decides (SR2/SR3).
        switch (event.stop_reason?.kind) {
          case "completed":
            return finalize(event);
          case "requires_action":
            // Client responsibility: answer every pending tool call, or the
            // server-side process deadlocks indefinitely (SR2 / EL3).
            for (const toolCallId of event.stop_reason.pending_tool_call_ids) {
              await stream.send(approveOrDecline(toolCallId));
            }
            break; // agent resumes; keep looping
          default:
            await steer(stream); // interrupt & redirect, or keep waiting
        }
      }
      break;
    }
    case "fan": recordMetrics(event); break;               // OB4: timing/tokens
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
await stream.send({ type: "user.interrupt" });
await stream.send({ type: "user.message", content: newInstruction });

// Teardown: never disconnect with pending required actions (EL3).
async function safeClose(stream: AgentStream) {
  for (const id of stream.pendingToolCallIds()) {
    await stream.send(decline(id, "client shutting down"));
  }
  await stream.close();
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
async def run_task(client, session_id: str, task: str):
    # 1–2. Listener first (EL1): connect resolves only when the stream is open.
    stream = await client.sessions.connect(session_id)
    await stream.wait_ready()
    await stream.send(type="user.message", content=task)

    # 3. Consume (EL2).
    async for event in stream:
        family = event_family(event)                      # OB1
        if family == "agent":
            on_agent_event(event)
        elif family == "session" and event.type == "session.status.idle":
            reason = event.stop_reason                    # SR1: idle ≠ done
            if reason.kind == "completed":
                return finalize(event)
            if reason.kind == "requires_action":          # SR2: client must answer
                for call_id in reason.pending_tool_call_ids:
                    await stream.send(approve_or_decline(call_id))
                continue                                  # agent resumes
            await steer(stream)                           # interrupt & redirect
        elif family == "fan":
            record_metrics(event)                         # OB4
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
await stream.send(type="user.interrupt")
await stream.send(type="user.message", content=new_instruction)

# EL3 — answer pending calls before closing:
async def safe_close(stream):
    for call_id in stream.pending_tool_call_ids():
        await stream.send(decline(call_id, reason="client shutting down"))
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
if (event.type === "session.status.idle") { resolve(result); } // no stop_reason check

// RS1 — conflated errors:
try { await loop(); } catch { /* retry forever */ }

// EL3 — deadlocking teardown:
finally { stream.close(); }           // pending tool approvals never answered
```
