# Go-specific patterns

How the scaffold uses Go, an MCP SDK, and Go's standard testing. Read when generating or modifying Go output.

## Runtime + dependencies

- **Go:** 1.22+ (uses `slog` and the routing improvements in `net/http`).
- **SDK:** `github.com/mark3labs/mcp-go` — the most widely used community Go SDK. The scaffold pins a minor version in `go.mod` so generation is reproducible.
- **Validation:** Custom validators in `internal/pipeline/validate.go`. Go's stdlib is enough — no third-party schema library is required. Each tool defines an `Args` struct with field tags (`json`, `validate`) and a small `Validate()` method.

## HTTPS transport

`cmd/mcp-server/main.go` boots `http.Server` with `ListenAndServeTLS`. The MCP SDK's Streamable HTTP handler is mounted on `/mcp`. A separate `/healthz` returns 200 unauthenticated for liveness probes. The dev cert script (`scripts/gen-dev-cert.sh`) generates a self-signed cert into `./certs/`.

### Critical rule (Section 10)

When stdio mode is enabled (`--stdio` flag for inspector runs), **stdout is reserved for JSON-RPC**. The logger (`internal/logger/logger.go`) writes to `os.Stderr` exclusively. The test suite captures stdout during a tool invocation and fails if anything is written there.

## Tool registry pattern

Each tool is a struct that implements:

```go
type Tool interface {
    Name() string
    Description() string
    InputSchema() any           // JSON schema for MCP advertisement
    Mutates() bool
    RateLimit() *RateLimitSpec  // nil for tools that bypass the limiter
    Execute(ctx context.Context, tctx *ToolContext, raw json.RawMessage) (any, error)
}
```

The registry is `[]Tool` in `internal/tools/registry.go`. Read tools and mutation tools live in separate files; the gate-checking helper `pipeline.AssertMutationsEnabled` is imported **only** by mutation tool files. Grep test:

```bash
go list -f '{{.GoFiles}}' ./internal/tools/... | xargs grep -l "AssertMutationsEnabled"
# must match only mutation tool files
```

## Validation + normalization layer

`internal/pipeline/pipeline.go` exposes `Run`:

```go
func Run[A any, R any](
    ctx context.Context,
    tctx *ToolContext,
    tool Tool,
    raw json.RawMessage,
    decode func(json.RawMessage) (A, error),
    exec  func(context.Context, *ToolContext, A) (R, error),
) (R, error) {
    args, err := decode(raw)                                 // 2. parse
    if err != nil { return zero, errors.Validation(err) }
    if err := args.(Validator).Validate(); err != nil {      // 3. validate
        return zero, errors.Validation(err)
    }
    if tool.Mutates() {                                      // 3a. gate
        if err := AssertMutationsEnabled(tctx.Config); err != nil { return zero, err }
    }
    if spec := tool.RateLimit(); spec != nil {               // 3b. rate limit
        if err := tctx.Limiter.Consume(spec, tctx.User.ID); err != nil { return zero, err }
    }
    out, err := exec(ctx, tctx, args)                        // 4. backend, 5. shape
    return out, err
}
```

Output structs are flat and intentionally narrow — the JSON tags are the contract. No `interface{}` in output types.

## Backend client interface

`internal/backends/client.go`:

```go
type Client interface {
    GetCompany(ctx context.Context, in GetCompanyInput) (Company, error)
    SearchCompanies(ctx context.Context, in SearchCompaniesInput) ([]Company, error)
    AISearch(ctx context.Context, q string) ([]Company, error)
    CreateTicket(ctx context.Context, in CreateTicketInput) (Ticket, error)
}
```

Three adapters live alongside: `rest.go`, `graphql.go`, `grpc.go`. Each accepts an `auth.TokenSource` so the OIDC bearer flows through unchanged.

## Tests

- `go test ./...` for the whole suite.
- `internal/backends/fake.go` is a `FakeClient` that records the inputs of every method call into exposed slices (e.g., `f.SearchCalls`, `f.CreateTicketCalls`). Tool tests **assert on the recorded inputs** before checking the response (Section 8).
- Mutation-gate negative test (TDD-style):

  ```go
  func TestCreateTicket_GateClosed_BackendNotCalled(t *testing.T) {
      cfg := config.Config{MutationsEnabled: false}
      fake := &backends.FakeClient{}
      tctx := &pipeline.ToolContext{Config: cfg, Backend: fake, /*...*/ }
      _, err := tools.CreateTicket{}.Execute(ctx, tctx, validInput)
      require.ErrorIs(t, err, errors.ErrMutationDisabled)
      require.Empty(t, fake.CreateTicketCalls, "backend MUST NOT be called when gate is closed")
  }
  ```

## Startup log line

Emitted via `slog` to stderr at boot, as a single structured record:

```json
{"time":"...","level":"INFO","msg":"startup","auth":"oidc","mutations_enabled":false,"tools":4,"rate_limits":{"ai_search":6},"port":8443}
```

A test asserts every field is present so accidental drops fail loudly.

## Inspector workflow

`scripts/inspector.sh` boots the server in stdio mode and pipes to `npx @modelcontextprotocol/inspector` (yes — the inspector ships as an npm package; Go users still call it via npx). See `inspector-workflow.md` for full sequence.
