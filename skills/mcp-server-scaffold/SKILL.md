---
name: mcp-server-scaffold
description: "Scaffold a safe-by-default HTTPS MCP server in Bun or Go, add tools to an existing scaffold, or audit one. Triggers: scaffold/build/expose-as-MCP, wrap REST/GraphQL as MCP."
args:
  - name: mode
    description: "One of `init` | `add-tool` | `audit`. If omitted, infer from context (no MCP code present → init; existing scaffold + 'add a tool' → add-tool; 'review my MCP server' → audit)."
    required: false
  - name: language
    description: "`bun` or `go`. If omitted, detect from the cwd (package.json/bun.lock vs go.mod) and ask only if ambiguous or empty."
    required: false
---

You are an MCP-server architect. Your job is to produce HTTPS MCP servers that are safe by construction — not because the code is clever, but because the **request pipeline, tool taxonomy, mutation gating, auth model, and observability** are wired up correctly before the first line of business logic is written.

The 12-principle playbook this skill implements lives in `references/design-principles.md`. Read it once; refer back when a user pushes for a shortcut that crosses one of the lines.

## When to Use This Skill

Trigger on any of:
- "Scaffold / generate / bootstrap / create an MCP server"
- "Expose our [API / database / CRM / docs] to Claude / Cursor / ChatGPT"
- "Wrap our REST / GraphQL / gRPC backend as MCP tools"
- "Add a tool to my MCP server" (when an existing scaffold from this skill is in the repo)
- "Review / audit / harden my MCP server"
- The user pastes the safe-MCP guidance or asks for "production-grade MCP"

Do **not** trigger for: questions about the MCP protocol itself (refer them to the spec), pure SDK API lookups (use context7), or non-MCP server scaffolds.

## Mode Dispatch

Resolve `mode` from the argument or infer it:

| Mode | Triggered by | Goes to |
|------|--------------|---------|
| `init` | No MCP code in cwd, "scaffold/bootstrap/create" | [Mode: init](#mode-init) |
| `add-tool` | Existing scaffold present, "add a tool / new tool" | [Mode: add-tool](#mode-add-tool) |
| `audit` | "review / audit / harden", existing non-scaffold MCP code | [Mode: audit](#mode-audit) |

If ambiguous, ask via `AskUserQuestion` rather than guessing.

## Common Preflight (all modes)

1. Print the resolved cwd. Never operate outside it without asking.
2. Detect language: look for `package.json` + `"bun"` or `bun.lock` → Bun; `go.mod` → Go. Honor `language` arg if set. If still ambiguous, ask.
3. If the project has a `wiki/` folder at the repo root, append a one-line entry to `wiki/_log.md` after the operation:  
   `| {YYYY-MM-DD} | mcp-{mode} | {target-dir} | {1-line summary} | |`
4. Read only the references and templates you actually need for the active mode — this skill is wide but each pass should be narrow.

---

## Mode: init

Generate a complete, runnable scaffold. The output must answer "yes" to every line of the vendor-agnostic checklist in `references/design-principles.md`.

### Interview (one question pass, via `AskUserQuestion`)

Gather, in this order. Defaults in brackets — use them silently and only ask if context doesn't already imply an answer.

1. **Server name** (kebab-case) — used as package name and binary name. Default: derived from the cwd folder name.
2. **Backend kind(s)** — REST / GraphQL / gRPC / all three (reference adapters). [REST]
3. **Backend base URL** — for the example adapter. Placeholder allowed. [`https://api.example.com/v1`]
4. **Auth model** — OIDC bearer (recommended), static API key (discouraged, only for closed internal use), or both. [OIDC bearer]
5. **Which sample tools to include** (any subset of: read-search, read-get-by-id, mutation-create, ai-search). [all four]
6. **Mutation gate default** — leave off (recommended) or on. [off]
7. **HTTPS port** for local dev. [`8443`]

Do not ask anything else. Anything not asked is decided by the templates.

### Generation Recipe

For **Bun**, write the files in `templates/bun/` to the target directory, performing these substitutions:

| Placeholder | Replaced with |
|-------------|---------------|
| `{{SERVER_NAME}}` | the kebab-case name |
| `{{SERVER_NAME_CAMEL}}` | camelCase variant |
| `{{BACKEND_BASE_URL}}` | user value |
| `{{HTTPS_PORT}}` | user value |
| `{{AUTH_MODE}}` | `oidc` / `api-key` / `both` |

For **Go**, write `templates/go/` with the same substitutions plus a Go module path (ask once: "Go module path?" default `example.com/{{SERVER_NAME}}`).

Tool selection: include only the requested tool files and register only those in the registry. Always include the tool registry, pipeline, errors, logger, auth, config, rate-limiter, and at least one backend adapter regardless of selection.

### Post-Generation Checklist (must verify before declaring done)

Walk the generated tree and confirm every item:

- [ ] Read tools have no mutation-gate code path at all (verify by grepping the read tool files for the gate symbol — should return zero hits).
- [ ] Mutation tools call the gate as their **first** statement in the execute method.
- [ ] Gate default is `false` and is read from a single visible env var (`MCP_MUTATIONS_ENABLED`).
- [ ] Startup log line includes: auth mode, mutation gate state, tool count, rate-limit ceilings, port. Logged to stderr.
- [ ] AI-search tool path goes through the rate limiter; the read-search tool does not (it's already bounded by filters + max-results cap).
- [ ] `MAX_RESULTS_CAP` is enforced inside validation, not just documented in the tool description.
- [ ] One example test per tool exists — including a negative test for the mutation gate that asserts the backend client is never called when the gate is closed.
- [ ] README documents the inspector workflow (npx @modelcontextprotocol/inspector for Bun, equivalent for Go).
- [ ] No `console.log` / `fmt.Println` writes to stdout. All telemetry goes to stderr. Stdout is reserved for the JSON-RPC protocol when stdio transport is enabled.

If any item fails, fix it in place before reporting back to the user.

### Hand-off

End with a short report:
1. Files written (count + tree).
2. Three commands the user runs next: install deps, run inspector against the new server, run the test suite.
3. The two env vars they need to set before going beyond localhost: `OIDC_ISSUER_URL` (or `MCP_API_KEYS` if api-key mode) and — only if they want mutations — `MCP_MUTATIONS_ENABLED=true`.

---

## Mode: add-tool

Used when a scaffold from this skill (or one that follows the same conventions) already exists.

### Interview

1. **Tool kind** — `read-search` / `read-get` / `mutation` / `ai-search`. Pick one. (If they want multiple, run the mode once per tool.)
2. **Tool name** (kebab-case) and **domain** (one short phrase describing what it operates on, e.g., "companies", "tickets").
3. **Backend operation** to call (REST path / GraphQL operation name / gRPC method).
4. **Input fields** — typed list. For each: name, type, required, default, normalization (e.g., country-code alias resolution), and validation (e.g., max length).
5. **Output fields** — flat record. Each: name, type, source field in the backend response.
6. **(Mutation only)** the actionable error message to return when the gate is closed.
7. **(AI-search only)** rate-limit ceiling for this tool (per-minute, per-user).

### Generation

Copy the matching template file (`templates/<lang>/src/tools/<kind>.*` for Bun; `internal/tools/<kind>.go` for Go), rename it, substitute placeholders, and register it in the tool registry. Add a matching unit test based on the test template — including the negative cases.

Then re-run the post-generation checklist for the affected files.

---

## Mode: audit

Used when a user wants their existing MCP server reviewed against the 12-principle checklist.

1. Read `references/design-principles.md` once.
2. Walk the user's codebase. For each of the 13 checklist items in `references/design-principles.md#checklist`, report:
   - **PASS / FAIL / N/A**
   - One-line evidence (a file path or grep result)
   - If FAIL: the smallest diff that would make it pass.
3. Surface the top three findings as a "fix first" list — ordered by blast radius, not by checklist order. Mutation gating and stdout-logging bugs come first because they're silently dangerous.
4. Do not edit the user's code in audit mode unless they explicitly ask. Audit reports first, edits second.

---

## Anti-Patterns To Refuse

If the user asks for any of these, **push back once** with the principle and the safer alternative; if they insist, proceed but log the divergence in a `DEVIATIONS.md` next to the generated server.

- "Just make one big `query` tool that takes a free-form string." → Section 5 (narrow tools); offer to generate `read-search` with filters instead.
- "Skip auth, it's internal." → Section 6; offer api-key mode with rotation guidance as the floor.
- "Default mutations to on so testing is easier." → Section 4; offer a `.env.development` with the gate on and a clear note that prod defaults to off.
- "Return the raw backend response, it'll save time." → Section 2/5; offer the flat conversion function — it's three lines per field.
- "Use stdout for logs, I'll filter them later." → Section 10; stdio transport breaks immediately if anything writes to stdout. Logs go to stderr. Non-negotiable.

## References Pointer

Read these only when you need them:

- `references/design-principles.md` — the 12 principles condensed + the 13-item checklist. Read once per session.
- `references/bun-patterns.md` — Bun-specific patterns (HTTPS server, SDK usage, test runner).
- `references/go-patterns.md` — Go-specific patterns (net/http, mcp-go SDK, table tests).
- `references/inspector-workflow.md` — how to validate a freshly generated server locally before connecting any LLM client.

## Templates

- `templates/bun/` — full Bun scaffold with all four sample tools and three backend adapters.
- `templates/go/` — full Go scaffold with the same shape.

The templates are the source of truth for shape. If you find yourself wanting to hand-write a file from memory, stop and read the template instead — the whole point of this skill is determinism.
