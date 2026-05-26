# Inspector workflow

Local validation matters more than it looks (Section 7). The inspector is how engineers issue MCP tool calls directly without an LLM client in the loop. The scaffold generates the harness; this doc explains what to write into the README.

## What the inspector is

`@modelcontextprotocol/inspector` is an official MCP debugging UI. It speaks the protocol over stdio or HTTP, lists registered tools, lets you fill out inputs against the advertised schema, fires the call, and shows the raw response. It is the fastest possible local feedback loop and the single best way to keep tool contracts honest.

## Bun: connecting the inspector

The scaffold ships `scripts/inspector.sh`:

```sh
#!/usr/bin/env bash
set -euo pipefail
# Boot the server in stdio mode and pipe to the inspector.
exec npx -y @modelcontextprotocol/inspector \
  bun run src/server.ts --stdio
```

When the user runs `bun run inspect`, the inspector opens at `http://localhost:6274` (its default UI port). The user picks a tool, fills in inputs, fires it. Every call is also logged to stderr by the server.

## Go: connecting the inspector

Same approach — the inspector is npm-distributed even for Go users:

```sh
#!/usr/bin/env bash
set -euo pipefail
exec npx -y @modelcontextprotocol/inspector \
  go run ./cmd/mcp-server --stdio
```

## The release-gate test sequence (must be in the README)

1. `bun test` / `go test ./...` — unit tests pass with mocked backend.
2. `bun run inspect` / `./scripts/inspector.sh` — boot inspector + server, list tools. **Verify tool count matches expected.**
3. Fire each read tool against the real backend. Check response shape matches the bounded schema.
4. With `MCP_MUTATIONS_ENABLED=false`: fire each mutation tool. Verify it returns `MutationDisabled` and includes the env-var name in the message.
5. With `MCP_MUTATIONS_ENABLED=true`: fire each mutation tool against a test backend. Verify the success path produces the expected flat output.
6. Negative cases: send malformed input. Verify each tool returns `ValidationFailed` with a specific message — not a generic 500.
7. Rate-limit case: fire the AI-search tool more times than the configured ceiling within a minute. Verify the `RateLimited` error includes the configured limit.

If any of those fail, the corresponding tool is **deregistered** (commented out in the registry with a `// FIXME(inspector):` note linking to the failing case) until the backend issue is fixed. This is the equivalent of "fail closed."

## Why this matters

A `create_collection` tool can pass mocked tests cleanly and still null-pointer on the real backend (the cautionary example from the source guidance). Mocked tests verify tool logic; inspector + real backend verifies the integration. The release gate is non-negotiable for that reason.
