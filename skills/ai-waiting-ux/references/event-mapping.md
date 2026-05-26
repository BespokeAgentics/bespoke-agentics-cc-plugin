# SDK Event → AgentEvent Mapping

Source: `@anthropic-ai/claude-agent-sdk` streaming async iterator. The exact event names follow the Messages streaming protocol the Claude Agent SDK is built on.

| SDK event | AgentEvent type | Notes |
|-----------|-----------------|-------|
| `message_start` | `message.start` | Capture `message.id`, `message.model` → set `modelId` if not yet set |
| `content_block_start` (type=`text`) | (none — buffer only) | Reset text buffer for the new block |
| `content_block_delta` (delta=`text_delta`) | `text.delta` | Append `delta.text` |
| `content_block_start` (type=`thinking`) | (none — buffer only) | Reset thinking buffer |
| `content_block_delta` (delta=`thinking_delta`) | `thinking.delta` | Append `delta.thinking` |
| `content_block_start` (type=`tool_use`) | `tool.use` | Emit immediately with `tool_use.id`, `name`, `input` (input may be partial — see below) |
| `content_block_delta` (delta=`input_json_delta`) | (none — buffer only) | Accumulate partial tool input JSON |
| `content_block_stop` (type=`tool_use`) | (none — buffer only) | Finalize input JSON; emit a corrected `tool.use` if the early one had partial input |
| `content_block_stop` (type=`text` / `thinking`) | (none — buffer only) | Marks the block boundary |
| `tool_result` (back from a tool runner, surfaced by the Claude Agent SDK as a content block) | `tool.result` | Match by `tool_use_id`; `output` is the result content; `isError` from the SDK's flag |
| `message_delta` | (update usage only) | Update `cumulativeUsage` from `usage.input_tokens` / `usage.output_tokens` |
| `message_stop` | `message.stop` | Capture `stop_reason` and `usage`. If `stop_reason === 'end_turn'`, the agent loop may continue; if `tool_use`, expect a tool result next; if `end_turn` and no further tool round-trip pending, the **session** is done. |
| (iterator returns / completes) | `session.stop` (status=`success`) | Emit once the async iterator is exhausted with no error |
| (iterator throws non-abort) | `session.stop` (status=`error`, error=`...`) | Capture `error.message` and `error.name` |
| `AbortController.abort()` | `control.abort` then `session.stop` (status=`aborted`) | Distinguish from `error`; preserve the reason string |

## Partial tool input

The SDK streams tool input as `input_json_delta` chunks. You have two options:

1. **Emit `tool.use` early** with `input: {}` and emit a second `tool.use` (or a new `tool.input.update` event) when complete. The UI shows the tool name immediately, then fills in args.
2. **Buffer until complete** and emit `tool.use` only once at `content_block_stop`. Simpler reducer, but the user sees a one-second delay where the tool name is hidden.

The skill's default template uses option 1 with a dedicated `tool.input.update` event to keep the reducer's switch exhaustive. Document the trade-off in the generated code header.

## Heartbeats

The SDK does not emit heartbeats. Your adapter must:
1. Track `lastEventAt` on every yield.
2. Run a `setInterval` (every 15 s by default) that, if `Date.now() - lastEventAt > idleThresholdMs` (default 60 s), emits a synthetic `heartbeat` event into the AgentEvent stream.
3. Cancel the interval on `session.stop`.

Heartbeats are events too. They flow through the reducer, persist to the LogSink, and drive the "Still running — last event 73 s ago" UI sub-state.

## When extended thinking is off

Skip `thinking.delta` events entirely. Reducer should still handle them (they may appear if a config change happens mid-session) but UI may omit the peripheral panel.

## When the model ID changes mid-session

Don't allow it. The reducer should warn and keep the original `modelId`. If a user genuinely needs cross-model sessions, start a new `sessionId`.
