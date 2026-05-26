# ETA Derivation

The brief's Property 2 demands an ETA that updates on every event. Here is the exact formula the scaffolded `eta.ts` uses, and the reasoning behind each term.

## Formula

```
etaMs = toolPhaseMs + textPhaseMs
       where
         toolPhaseMs  = avgToolDurationMs * estimatedRemainingTools
         textPhaseMs  = projectedRemainingOutputTokens / observedTokensPerSec * 1000
```

Both terms are clamped to ≥ 0. If either input is insufficient, that term contributes 0 (not `undefined`).

## Inputs and their fallbacks

### `avgToolDurationMs`

Mean of `completedToolCalls[i].durationMs` within the current session. Use a simple arithmetic mean — exponential weighting overreacts to a single slow file read.

- **Cold start (0 or 1 tool call complete):** `null` → contributes 0 to ETA. Surface "warming up" in UI.
- **After 2+ completions:** valid number.
- **Outlier handling:** drop any single tool call that is >3× the median once `completedToolCalls.length >= 4`. This prevents one network timeout from blowing up the whole estimate.

### `estimatedRemainingTools`

Three sources, in priority order:

1. **Historical task-type median** — if the caller tagged the session with a `taskType` (e.g. `"refactor"`, `"summarize"`, `"search-codebase"`) and history exists in the LogSink, use the median tool count for that type.
2. **Per-session budget** — if the caller passed a `stepBudget` (e.g. "this should take about 8 tool calls"), use it.
3. **Default budget** — `12`, with `max(0, budget - currentStep)`.

Persist `taskType` history in the LogSink between sessions so source 1 gets stronger over time.

### `projectedRemainingOutputTokens`

A coarse projection based on assistant text-block patterns:

- If `currentStep === 0` and no text has streamed yet → use a default `expectedOutputTokens = 800`.
- Once text has streamed, project remaining based on the rate of "thinking-to-text" transitions and the typical tail length (default `200` tokens after the final tool call). The skill's template uses a simple linear model — improve later if needed.

This term often contributes most of the noise. That's fine — the ETA is allowed to wobble; it's not allowed to freeze.

### `observedTokensPerSec`

Tokens per second over a rolling 5-second window. Compute by:

```ts
const windowMs = 5000;
const recent = events.filter(e => e.type === 'text.delta' && now - e.timestamp < windowMs);
const tokensInWindow = recent.reduce((sum, e) => sum + estimateTokens(e.text), 0);
const tokensPerSec = (tokensInWindow / windowMs) * 1000;
```

Use a tokenizer-aware estimate (`@anthropic-ai/tokenizer` or a 4-char heuristic). If the project doesn't bundle a tokenizer, the 4-chars-per-token heuristic is close enough for ETA.

If `tokensPerSec < 1`, treat as `null` and zero out the text phase.

## Recompute cadence

On **every** AgentEvent. The function is O(N) over a small recent window — keep N bounded (default last 50 events). At animation-frame cadence (60 fps) this is negligible.

Do **not** recompute on a `setInterval`. Tying it to events means the ETA updates exactly when something changes, which is the brief's "updating" requirement.

## Output shape

```ts
type EtaReport = {
  etaMs: number | null              // null when both phases zero
  elapsedMs: number
  confidence: 'cold' | 'warming' | 'stable'
  lastUpdatedAt: number             // for heartbeat staleness display
  breakdown: {
    toolPhaseMs: number
    textPhaseMs: number
    avgToolDurationMs: number | null
    estimatedRemainingTools: number
    observedTokensPerSec: number | null
  }
}
```

Expose `breakdown` in dev mode only — production UI shows the headline number plus confidence label.

## What the UI does with `null`

- `etaMs === null && confidence === 'cold'` → "Working… (estimating)"
- `etaMs !== null && confidence === 'warming'` → show the number with a wavy underline / italic
- `etaMs !== null && confidence === 'stable'` → show the number plain

Never blank the elapsed counter. It is always visible and always counting.
