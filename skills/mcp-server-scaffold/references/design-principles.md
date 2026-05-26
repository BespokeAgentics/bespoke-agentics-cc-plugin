# Safe MCP Server — Design Principles (condensed)

This is the playbook the scaffolder enforces. Each principle has a one-line summary, the **failure mode it prevents**, and the **mechanism in the templates** that makes the principle real. Read top-to-bottom once; refer back when a decision is ambiguous.

## 1. The MCP server is a first-class interface, not a backend proxy

- **Prevents:** vague tool contracts that leak prompt-level ambiguity into backend behavior.
- **Mechanism:** every tool has a typed input struct, a bounded output type, and a validation pass before any backend call. The MCP server *never* passes raw user input to the backend and *never* returns raw backend payloads to the client.

## 2. Layer the request pipeline explicitly (6 layers)

1. Transport reception (JSON-RPC dispatch).
2. Argument parsing into typed structs.
3. Validation + normalization + alias resolution + limit capping. **Mutation tools check the gate here, first.**
4. Backend execution through an auth-handling client.
5. Response shaping — explicit flat-conversion functions.
6. Serialization + return.

- **Prevents:** layers silently doing two jobs (e.g., validation + backend call mixed together).
- **Mechanism:** the `pipeline` module in each template is the canonical implementation. Every tool calls it; nothing skips a layer.

## 3. Separate read and write at the tool level

- **Prevents:** mutation paths drifting into read tools during refactors; "could the model have written something?" being an audit question instead of an architectural answer.
- **Mechanism:** read tools have no gate code at all. Mutation tools each carry their own `mutationAllowed` flag and check it as the first statement of `execute`. Reviewers can grep the gate symbol — it must only appear in mutation tools.

## 4. Default-deny mutations behind an explicit, visible switch

- **Prevents:** organic permission creep; misconfigured complex auth models accidentally enabling writes.
- **Mechanism:** single env var `MCP_MUTATIONS_ENABLED`, default `false`. State is logged at startup. Per-tool flags are wired so each mutation tool returns a clear "mutations disabled" error if invoked while the gate is closed.

## 5. Many narrow tools beat a few broad ones

- **Prevents:** flexible mega-tools that accrete hidden prompt dependencies and resist evolution.
- **Mechanism:** the templates favor one tool per operation (e.g., `search_companies` + `get_company_by_id` instead of `companies_query`). Output records are flat; nested types are converted explicitly.

## 6. Inherit, don't bypass, the platform's identity model

- **Prevents:** static shared credentials becoming the de facto auth model.
- **Mechanism:** OIDC bearer token middleware ships as the default `auth` module. API-key mode exists but is gated behind a startup warning. Tokens flow to the backend client unchanged.

## 7. Local validation is a production concern

- **Prevents:** debug loops that always require an LLM client; contracts that drift because the local feedback loop is painful.
- **Mechanism:** every generated README includes the MCP Inspector workflow (`npx @modelcontextprotocol/inspector ...` for Bun, equivalent for Go). The scaffolder also generates a `scripts/inspector.sh` helper.

## 8. Layered testing: mocked unit tests + real-backend release gate

- **Prevents:** tests that only assert output shape and miss normalization bugs; releasing a tool that passes mocks but fails the real backend.
- **Mechanism:** each tool template ships with a unit test that injects a fake backend client and **asserts on the variables sent**, not just the response shape. A negative test for mutation gating asserts the backend client is never called when the gate is closed (TDD style). The README documents the real-backend release-gate step.

## 9. Bound queries against large datasets by design

- **Prevents:** unconstrained queries returning near-random samples; LLMs entering refinement-loop spirals.
- **Mechanism:** read-search tools require at least one filter (enforced in validation, not docs). The AI-search tool path goes through a per-user, per-tool token-bucket rate limiter whose ceilings are read from env vars (configurable per environment, no code change needed). Default ceiling: 6/min — slightly above the typical 2-4 refinement burst, no headroom for runaway loops.

## 10. Observability is built in from day one

- **Prevents:** "we'll add logging later" leading to opaque incidents.
- **Mechanism:** structured stderr logger emits a startup line with auth mode, mutation gate, tool count, rate-limit ceilings, port. Per-request log includes tool, latency, outcome, error type. **Stdout is reserved for JSON-RPC.** All log output goes to stderr; the templates have an assertion in the test suite that catches accidental stdout writes.

## 11. Errors are diagnostic, not generic

- **Prevents:** the LLM client surfacing useless errors to the user.
- **Mechanism:** typed error taxonomy — `Unauthorized`, `NotFound`, `RateLimited`, `MutationDisabled`, `ValidationFailed`, `BackendError`. Each carries a message that names the problem and the fix. Rate-limit errors include the configured ceiling. Mutation-disabled errors name the env var to flip.

## 12. The checklist (the audit mode grades against this)

A production-ready MCP server answers "yes" to every line. The audit mode walks these in order.

1. The server is treated as a first-class interface with its own contracts and tests, not a proxy.
2. Read and write are separated at the tool level; mutation flags are per-tool and checked before any backend call.
3. Mutations are off by default behind an explicit env switch visible in startup logs.
4. Tools are narrow — typed input, bounded output, flat response.
5. Auth uses short-lived user-scoped tokens that inherit the platform's authorization model.
6. Inputs are validated, normalized, and capped before reaching the backend.
7. Outputs are flat AI-friendly types; raw backend payloads never reach the client.
8. Unit tests use mocked backend clients and assert on the **variables sent**, not just responses.
9. Real-backend validation via inspector is a release gate; failing tools are deregistered until fixed.
10. Negative tests cover blocked mutations, invalid inputs, and error message content.
11. Broad-query risk is constrained at the tool contract; AI-style search paths have configurable per-environment rate limits.
12. Startup configuration logged as structured fields; per-request telemetry supported by the error taxonomy.
13. Errors are typed, specific, and include remediation paths.

## What this skill refuses to generate

- Tools that pass `req.body` straight to the backend.
- Servers that log to stdout while the stdio transport is in use.
- Mutation tools without a per-tool gate flag (even if a global gate exists).
- "Generic query" tools that take a free-form string and an opaque options blob.
- Auth implementations that store static API keys in source.

If asked for any of these, the skill pushes back once with the relevant principle, then — if the user insists — proceeds and writes a `DEVIATIONS.md` next to the server documenting the divergence and the reason.
