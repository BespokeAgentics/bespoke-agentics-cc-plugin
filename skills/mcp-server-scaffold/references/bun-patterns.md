# Bun-specific patterns

How the scaffold uses Bun, the `@modelcontextprotocol/sdk`, and Bun's test runner. Read when generating or modifying Bun output.

## Runtime + dependencies

- **Runtime:** Bun ≥ 1.1 (uses `Bun.serve` with TLS, native test runner).
- **SDK:** `@modelcontextprotocol/sdk` — official TypeScript SDK. Imports come from `@modelcontextprotocol/sdk/server/index.js` and `@modelcontextprotocol/sdk/server/streamableHttp.js`.
- **Validation:** `zod` — every tool input schema is a `z.object`. The schema is the single source of truth for parsing and for the public `inputSchema` advertised over MCP.

## HTTPS transport

The scaffold uses **Streamable HTTP** (the modern MCP HTTP transport), not stdio. Reason: the user asked for HTTPS. Stdio mode is still supported for inspector runs via a flag, but the default `bun run start` boots an HTTPS server on `MCP_PORT` with TLS from `MCP_TLS_CERT` / `MCP_TLS_KEY` paths (self-signed by default; the scaffolder generates a dev cert script).

### Critical rule (Section 10)

When the stdio transport is enabled for inspector workflows, **stdout is reserved for JSON-RPC**. The logger writes exclusively to stderr via `process.stderr.write`. The test suite includes an assertion that catches accidental stdout writes from the tool code paths.

## Tool registry pattern

Each tool exports a `Tool` object with this shape:

```ts
export type Tool<TInput, TOutput> = {
  name: string;
  description: string;
  inputSchema: z.ZodType<TInput>;
  outputSchema: z.ZodType<TOutput>;
  mutates: boolean;                  // false for read tools, true for mutation tools
  rateLimit?: { keyPrefix: string; perMinute: number };
  execute(ctx: ToolContext, input: TInput): Promise<TOutput>;
};
```

The registry is just `tools: Tool<any, any>[]`. Server boot iterates and calls `server.setRequestHandler(...)` for each. Tool count is logged at startup; if the count changes between expected and registered, the test asserts mismatch.

Read tools do not import the gate module at all. Mutation tools import `assertMutationsEnabled` and call it as the **first** statement of `execute`. Grep test:

```bash
rg "assertMutationsEnabled" src/tools/ --files-with-matches
# must list ONLY mutation tool files
```

## Validation + normalization layer

Lives in `src/pipeline.ts`. Shape:

```ts
export async function runPipeline<TIn, TOut>(
  tool: Tool<TIn, TOut>,
  ctx: ToolContext,
  rawArgs: unknown,
): Promise<TOut> {
  // 2. Parse with zod
  const parsed = tool.inputSchema.parse(rawArgs);
  // 3a. Mutation gate (if applicable)
  if (tool.mutates) assertMutationsEnabled(ctx.config);
  // 3b. Rate limit (if applicable)
  if (tool.rateLimit) await ctx.rateLimiter.consume(tool.rateLimit, ctx.user.id);
  // 4 + 5 happen inside tool.execute
  const out = await tool.execute(ctx, parsed);
  // 6. Re-validate the output shape against the bounded schema
  return tool.outputSchema.parse(out);
}
```

The output re-validation is intentional. It is the structural promise that raw backend payloads never reach the client — if the conversion function forgot a field, the parse fails loudly during tests.

## Backend client interface

`src/backends/client.ts` defines a single `BackendClient` interface. Each adapter (`rest.ts`, `graphql.ts`, `grpc.ts`) implements it. Auth flows in via the constructor — the client never reads tokens from the environment. The user's OIDC bearer is passed through unchanged.

## Tests

- Bun's native runner: `bun test`.
- Mocked backend: a `FakeBackendClient` that records calls into a `recordedRequests` array. Each tool test asserts on the **recorded request** before checking the response (Section 8).
- Mutation-gate negative test: instantiate the tool with `config.mutationsEnabled = false`, call `execute`, assert that `recordedRequests.length === 0` and that the thrown error is the typed `MutationDisabled` error with the env-var name in its message.

## Startup log line

A single structured line written to stderr at boot:

```
{"event":"startup","auth":"oidc","mutationsEnabled":false,"tools":4,"rateLimits":{"ai_search":6},"port":8443}
```

This line is also asserted by the test suite — accidentally dropping a field is caught immediately.

## Inspector workflow

The generated README links to `npx @modelcontextprotocol/inspector` and includes a `scripts/inspector.sh` that boots the server in stdio mode against the inspector. See `inspector-workflow.md` for the full sequence.
