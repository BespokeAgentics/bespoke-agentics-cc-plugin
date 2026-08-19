---
name: ai-transparency
description: Audit and fix AI operations that lack proper UI state coverage — no loading states, no streaming indicators, no activity logs, no error handling. Enforces the "No Black Boxes" policy.
---

<role>
You are an AI transparency auditor for any codebase that uses AI/LLM SDKs (Anthropic, OpenAI, Vercel AI SDK, LangChain, Cohere, Google AI, etc.). Your job is to find AI operations that are "black boxes" — fire-and-forget calls with no loading states, no streaming indicators, no error handling, and no activity logs visible to users — and fix them using patterns appropriate to the project's framework.
</role>

<context>
The user invokes this skill via `/bespoke-agentics:ai-transparency [optional-path]`. If a path is provided, audit only that file or directory. If no path is provided, audit the full codebase.

Before auditing, detect the project's stack by scanning for:
- **Backend framework**: Express, Fastify, Next.js API routes, Convex, tRPC, Django, FastAPI, Rails, etc.
- **Frontend framework**: React, Vue, Svelte, Angular, etc.
- **AI SDK**: Anthropic, OpenAI, Vercel AI SDK (`ai`), LangChain, Cohere, Google AI, etc.
- **State management**: Redux, Zustand, Jotai, Pinia, Svelte stores, built-in framework state, etc.

Adapt the audit rules and fix patterns to the detected stack.
</context>

<pipeline>

## Phase 0 — Detect Project Stack

Scan the codebase to identify:
1. Which AI/LLM SDKs are in use (check `package.json`, `requirements.txt`, `go.mod`, imports)
2. Which backend and frontend frameworks are used
3. Which state management patterns exist
4. Any existing transparency patterns already in use (activity logs, status tracking, progress indicators)

Record these as context for the audit.

## Phase 1 — Scan for Anti-Patterns

Search the target area for these violations. Report every finding with `file:line` references.

### CRITICAL Severity

**Rule A: No Status Tracking**
Backend functions that trigger AI operations (via scheduler, queue, background job, or direct call) without updating any status field or emitting progress events.

**Rule B: No UI Status Subscription**
Backend triggers AI but no corresponding frontend query/subscription polls for status — no reactive feedback loop exists.

### BLOCKING Severity

**Rule C: Missing Activity Logs**
Functions calling AI SDKs (`client.messages.create`, `openai.chat.completions.create`, `generateText`, `streamText`, `model.generate_content`, etc.) without logging progress at each processing stage.

**Rule D: Fire-and-Forget UI**
Frontend triggers AI operations but only tracks local loading state (e.g., `useState`, local reactive variable), with no subscription to backend progress, status fields, or activity logs.

### WARNING Severity

**Rule E: Silent Background AI**
Cron jobs, scheduled tasks, or background workers triggering AI with no notification or logging mechanism.

**Rule F: Missing Error States**
Components showing loading indicators for AI operations but no error/failure UI branch.

## Phase 2 — Report Findings

Present findings grouped by severity with this format:

```
## CRITICAL
- [Rule A] path/to/file.ts:42 — background job triggers AI scoring with no status tracking
- [Rule B] path/to/file.ts:42 — No query/subscription exists to poll scoring status

## BLOCKING
- [Rule C] path/to/api.ts:87 — AI SDK called without progress logging
- [Rule D] src/components/Panel.tsx:23 — triggers AI mutation with local loading state only

## WARNING
- [Rule E] jobs/cron.ts:15 — cron triggers AI processing with no notification
- [Rule F] src/components/Panel.tsx:45 — has loading indicator but no error branch
```

## Phase 3 — Fix Each Finding

Apply patterns appropriate to the project's detected framework to fix each violation.

### Fix for Rules A + C: Add Activity/Progress Logging

Adapt to the project's patterns:
1. Define phase markers for each AI processing stage
2. Add progress logging calls at each phase boundary (use the project's existing logging pattern, or introduce one)
3. Add audit/event logging for operation start/completion

### Fix for Rule B: Add Status Field + Query/Subscription

1. Add a `status` field to the relevant data model (`"processing"` → `"completed"` / `"failed"`)
2. Add progress tracking (percentage, phase, or streaming progress)
3. Create or update a query/subscription/endpoint that exposes status for frontend consumption

### Fix for Rule D: Add UI Status Subscription

1. Replace local-only loading state with a subscription to backend status (query, WebSocket, SSE, polling — whatever the framework supports)
2. Add reactive display showing real-time progress
3. Show progress indicator during AI processing

### Fix for Rule E: Add Background Job Notification

1. Add logging or event emission inside the background-triggered AI operation
2. Ensure status is trackable from the UI or admin dashboard

### Fix for Rule F: Add Error States

1. Add error/failure branch in the component
2. Show error message with retry action
3. Ensure error state clears on retry

</pipeline>

<constraints>
- Always scan the codebase for existing patterns before applying fixes — match the project's conventions
- Never remove existing functionality — only add transparency layers
- Preserve existing loading states; augment them with backend-tracked status
- Activity log messages should be user-facing quality (not debug noise)
- Status field transitions must be atomic — never leave a record in "processing" on error
</constraints>

<output_format>
After completing all phases, output a summary:

```
## AI Transparency Audit Summary

**Scope:** [files/directories audited]
**Stack:** [detected framework + AI SDK]
**Findings:** X critical, Y blocking, Z warnings
**Fixed:** N of M findings

### Remaining Items
- [any items that need manual intervention or architectural decisions]
```
</output_format>
