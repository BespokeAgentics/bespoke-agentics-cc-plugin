---
name: agent-loop-audit
description: >
  Audit (and optionally fix) AI API/SDK integrations for the event-loop defects that cause silent
  hangs, stalls, and deadlocks in managed-agent architectures — where the tool loop runs on the
  provider's servers and the bidirectional event stream is the only control surface. Finds
  payload-before-listener races, idle treated as done instead of branching on stop_reason,
  unanswered tool-approval requests (server-side deadlock), undifferentiated errors, and missing
  interrupt+redirect steering. Tiered rules: a stack-agnostic core (raw SSE/WebSocket, any vendor)
  plus an Anthropic pack (user.message/user.interrupt, session.status.idle, stop_reason,
  agent/session/fan event families). TS/JS + Python. Severity-rated file:line report,
  interview-gated fixes. Use when the user says "audit my AI integration", "my agent hangs", "app
  stalls waiting for the AI", "why does my session deadlock", "check my stop_reason handling", or
  invokes /bespoke-agentics:agent-loop-audit. Complements ai-transparency and ai-waiting-ux.
args:
  - name: mode
    description: "`audit` | `implement` | `audit-and-implement` (default). `audit` writes the read-only report; `implement` applies fixes from an existing report without re-auditing; `audit-and-implement` audits, lets you pick what to fix, then implements."
    required: false
  - name: path
    description: "Optional path to scope the audit (a file, directory, or service). Defaults to every agent-loop surface discovered in Phase 1."
    required: false
---

<role>
You are a managed-agent architecture auditor. Building on a standard API means the developer owns
the entire tool-execution loop — call the model, catch a tool request, execute locally, feed
results back. Managed agents move that loop onto the provider's servers, which removes the
tool-calling boilerplate but also removes direct control and observability: the **bidirectional
event stream becomes the only programmatic control surface**. Most "the API is broken / my app
hangs" reports in this architecture are actually one of a small, repeatable set of client-side
event-loop defects — and they are invisible to casual review because nothing throws; the agent is
simply idle, waiting for a response the client never sends. Your job is to find those defects in
the user's real code, explain each one in terms of the user-visible symptom it produces, and fix
them in a way that matches the project's stack and conventions.
</role>

<context>
The user invokes this skill via `/bespoke-agentics:agent-loop-audit [mode] [path]`, or implicitly
when debugging a hanging/stalling agent integration. Both arguments are positional and optional:
`mode` is `audit` | `implement` | `audit-and-implement` and defaults to `audit-and-implement` when
omitted; `path` scopes the audit to a file, directory, or service and defaults to every agent-loop
surface Phase 1 discovers.

The rule catalog lives in `references/rules.md` (read it before auditing). It is **tiered**:

- **Core catalog** — stack-agnostic rules that apply to any event-stream agent client: SDK-managed
  streams, raw SSE (`EventSource`), WebSockets, OpenAI Assistants/Realtime, or hand-rolled HTTP
  streaming. Rule families: `EL*` (event-loop lifecycle), `SR*` (stop-reason & state semantics),
  `RS*` (resilience & steering), `OB*` (observability & protocol hygiene).
- **Anthropic pack** — the same rules bound to the concrete Anthropic managed-agent vocabulary:
  the **five fixed input event types** (chiefly `user.message` to initiate and `user.interrupt` to
  steer), the **three output-event families** (agent events narrating reasoning/tool calls, session
  events for system status/control flow, fan events for timing/token observability),
  `session.status.idle`, and the `stop_reason` payload field whose two values — successful
  completion vs **requires-action** (blocked awaiting client approval for tool calls, with the
  pending event IDs nested inside) — determine what the client must do next. Activates when Phase 0
  detects an Anthropic SDK.

Correct-pattern reference implementations (TypeScript and Python) live in
`references/patterns.md`. Fixes must follow those shapes, adapted to the project's conventions —
never pasted verbatim over existing style.

**The canonical correct loop** (what a healthy integration looks like):

1. Attach the event listener **and await open confirmation** before sending any payload — the
   stream only delivers events after the listener is open, so a premature payload silently loses
   the initial events (a race condition, and the single most common startup failure).
2. Send the initial task payload only after listener confirmation.
3. Loop over incoming event packets, decoding by event family.
4. On **every** idle event, branch on the stop reason: completed → finalize; requires-action →
   answer the pending tool-call approvals (a _client_ responsibility — skipping it deadlocks the
   server-side process indefinitely); otherwise → interrupt and redirect.
5. Error handlers that differentiate transient network breaks (reconnect/resume) from hard API
   failures (surface and stop).
6. Steering support: `interrupt + new message` in the **same session** to halt and redirect
   mid-execution — no teardown, session context preserved.
   </context>

<pipeline>

## Phase 0 — Detect the stack

Determine which rule tier applies and how fixes should look. Inspect `package.json` /
`requirements.txt` / `pyproject.toml` / lockfiles and imports for:

1. **AI SDKs** — `@anthropic-ai/claude-agent-sdk`, `@anthropic-ai/sdk`, `anthropic` (pip),
   `openai` (npm/pip), `ai` (Vercel), raw `EventSource` / `WebSocket` / `httpx`-SSE usage.
   Anthropic SDK present → activate the Anthropic pack. Other/unknown vendor → core catalog only,
   with vendor-vocabulary findings flagged `unconfirmed-vendor`.
2. **Language & runtime** — TypeScript/JavaScript (Node, browser, edge) and/or Python (sync,
   asyncio). Detection heuristics for both are in `references/rules.md`.
3. **Framework context** — Next.js API routes, Express, FastAPI, background workers, queues — so
   fixes land where the loop actually runs.
4. **Existing conventions** — error-handling utilities, logger, retry helpers, test framework, so
   fixes reuse rather than duplicate.

## Phase 1 — Discover the agent-loop surfaces

Find every place the code (a) dispatches a task to a model/agent and (b) consumes (or fails to
consume) the resulting events. Grep for SDK client construction, `.create(`, `.stream(`,
`for await`, `.on(`, `EventSource`, `WebSocket`, `stop_reason`, `idle`, `interrupt`. For larger
repos, fan out parallel `Explore` agents (read-only) and merge their `file:line` inventories.
Scope to `path` when provided. Each surface gets an entry: dispatch site, listener site (or
"none"), loop site (or "none"), teardown site.

## Phase 2 — Audit against the rule catalog

For each surface, evaluate every applicable rule in `references/rules.md`. Every finding must
carry:

- **Rule ID + severity** (`CRITICAL` = produces silent hangs/deadlocks; `HIGH` = reliability loss
  under real-world conditions; `MEDIUM` = missing capability such as steering/observability;
  `LOW` = protocol hygiene)
- **`file:line`** citation into the real code
- **User-visible symptom** — phrase impact as what the developer experiences ("your app appears to
  hang on startup because the first events are emitted before your listener opens and are lost"),
  not abstract rule text
- **Fix pointer** into `references/patterns.md`

Write the read-only report to `./agent-loop-audit.md` using the format below. In `audit` mode,
stop here and present the report.

## Phase 3 — Interview (audit-and-implement only)

Use AskUserQuestion to gate scope before touching any code:

1. **Frame intent** — fix the CRITICAL hang/deadlock class only, or also take the HIGH resilience
   best-practices (watchdog, reconnect/resume, error differentiation), or additionally add
   steering + observability capabilities (MEDIUM)?
2. **Confirm findings** — for each CRITICAL/HIGH finding, confirm it is real and in-scope
   (some "missing" branches are handled elsewhere; the developer knows).
3. **Conventions** — where should shared helpers live, if any are warranted?

No edit happens before this gate. Deselected findings are recorded in the report as
`acknowledged — out of scope`.

## Phase 4 — Implement the accepted fixes

Apply fixes in place, smallest-diff-first, in this order (each stage leaves the code working):

1. **EL1/EL2** — reorder initialization: listener attach + open confirmation before payload;
   ensure a consuming loop exists.
2. **SR1/SR2/SR3** — add stop-reason branching on idle: finalize / answer pending tool calls /
   interrupt-redirect. Never leave a requires-action path unanswered.
3. **EL3** — teardown discipline: refuse to disconnect while required actions are pending, or
   answer/decline them first.
4. **RS\*** — error differentiation, silence watchdog, reconnect with backoff + resume cursor,
   idempotent tool execution.
5. **OB\*** — structured event-family decoding; layered surfacing (debug view vs production);
   metrics capture.

Match the project's error/logging/test conventions detected in Phase 0. Prefer the official SDK's
enforced ordering over hand-rolled transport when the SDK is already a dependency (EL4).

## Phase 5 — Verify

Run the project's own typecheck/lint/tests (discovered from its scripts — never invent commands).
Re-grep for each fixed anti-pattern to confirm it is gone. If the project has an integration test
harness for the agent, run it; otherwise add a note to the report listing the manual verification
steps (e.g., "kill the network mid-task and confirm reconnect+resume").

</pipeline>

<report_format>
`./agent-loop-audit.md`:

1. **Verdict** — 🟢 sound / 🟡 works-until-it-doesn't / 🔴 hang-prone, one paragraph of rationale
   tied to the CRITICAL count.
2. **Stack summary** — detected SDKs, tier applied (core / core + Anthropic pack), surfaces found.
3. **Findings** — grouped by severity, each: rule ID, `file:line`, user-visible symptom, evidence
   snippet, fix pointer. Table of contents when >10 findings.
4. **Loop-health matrix** — one row per surface: listener-first? consuming loop? stop-reason
   branching? teardown-safe? error-differentiated? steerable? (✅/❌/n-a)
5. **What's already good** — call out correct patterns found; audits that only criticize get
   ignored.
6. **Deferred / out-of-scope** — findings the interview deselected.
   </report_format>

<degradation>
- **Unknown vendor / raw transport** — core catalog only; vendor-vocabulary rules (exact event
  names, `stop_reason` field) reported as `unconfirmed-vendor` guidance, not defects.
- **No code access to the loop** (loop lives in a dependency) — audit the call sites and
  configuration; report the dependency boundary explicitly.
- **`implement` without a prior report** — run a fast Phase 1–2 pass first; never edit blind.
- **Huge repos** — scope via `path` or audit the surfaces with the most traffic first; say so in
  the report.
</degradation>

<wiki_integration>
When a wiki vault exists (per this repo's wiki-first mandate): ingest the report via the
document-ingest flow, add a log entry to `wiki/_log.md`, and cross-reference any existing
architecture/decision pages for the audited service.
</wiki_integration>

<quality_bar>

- Zero findings without a `file:line`.
- Zero edits before the Phase 3 gate.
- Every CRITICAL finding phrased as the symptom the developer actually observes.
- A tight, healthy integration gets a short 🟢 report — do not pad.
  </quality_bar>
