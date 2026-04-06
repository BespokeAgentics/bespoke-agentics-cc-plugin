# Domain Decomposition Heuristics

Rules for deciding how many agents to create, what scope each gets, and when to add validators or orchestrators.

## Boundary Signals

Each of these suggests a **separate agent**. The more signals present, the stronger the case for a dedicated agent.

| Signal | Example | Why it matters |
|---|---|---|
| Different framework/runtime | React app + Express API | Different code patterns, different expertise |
| Different package manager | Yarn for frontend, pip for ML service | Different tooling commands, different ecosystems |
| Different test framework | Vitest for UI, pytest for backend | Different test patterns, different validation commands |
| Different deployment target | Vercel for frontend, AWS Lambda for API | Different build outputs, different constraints |
| Independent working directory | `packages/ui/` vs `services/api/` | Can be worked on without touching the other |
| Different domain expertise | Lit web components vs Hono API routes | Fundamentally different knowledge required |
| Different programming language | TypeScript frontend + Rust backend | Completely different tooling and patterns |

## Grouping Signals

These suggest **combining** into one agent. Grouping avoids agent sprawl for closely related concerns.

| Signal | Example | Why to group |
|---|---|---|
| Small packages that change together | `types/` + `config/` (300 lines each) | Too small for dedicated agents |
| Same framework and patterns | Two React apps with identical conventions | Same expertise, same tooling |
| Shared test infrastructure | Packages sharing test utilities | Same test patterns and setup |
| Package is purely types/interfaces | `packages/types/` with no logic | No implementation work, just declarations |
| Utility package with no domain logic | `packages/utils/` | Too thin for a specialist |

## Agent Count Guidelines

| Project size | Domains | Recommended agents | Notes |
|---|---|---|---|
| Small | 1-3 | 1-3 implementation + 0-1 validator | One agent per domain, validator optional |
| Medium | 4-7 | 3-5 implementation + 1-2 validators | Group related domains, add contract validator |
| Large | 8-15 | 5-8 implementation + 2-4 validators + orchestrator | Layer-based grouping, specialized validators |
| Very large | 15+ | 8-12 implementation + 3-5 validators + orchestrator | Aggressive grouping, must have orchestrator |

## Validation Agent Triggers

Add a specialized validator when:

| Trigger | Validator type | What it checks |
|---|---|---|
| Multiple packages with shared interfaces | Contract validator | All implementations match interfaces, types consistent |
| Accessibility requirements (WCAG, Section 508) | Accessibility auditor | ARIA, keyboard nav, contrast, focus management |
| Config-driven system (feature flags, theming) | Config validator | Resolution correctness, feature flag propagation |
| Multiple platforms sharing domain types | Type consistency validator | No local type redefinitions, import sources correct |
| Security/compliance requirements | Security auditor | Auth patterns, input validation, data handling |
| API contract specifications (OpenAPI, GraphQL schema) | API contract validator | Endpoints match spec, types match schema |

## Orchestrator Triggers

Add an orchestrator when:

- **>4 implementation agents** — too many to coordinate manually
- **Phased implementation** — spec defines sequential phases with dependencies
- **Cross-package dependency graph** — agents must work in a specific order
- **Per-client/per-tenant builds** — build matrix coordination needed

Do NOT add an orchestrator for:
- ≤4 agents (user can dispatch directly)
- Fully independent services (no coordination needed)
- Single-phase projects (no sequencing needed)

## Grouping Strategies

When domains must be grouped, use one of these strategies:

**By layer:** Group packages that serve the same architectural layer.
- Foundation: types + config + tokens + utilities
- UI: components + wrappers + storybook
- Data: adapters + API clients + data transformers
- Portal/App: per-platform application code

**By platform:** Group packages that target the same platform.
- BigCommerce: embedded + headless portal code
- Shopify: Hydrogen portal code
- Shared: backend services used by all platforms

**By lifecycle:** Group packages that change at the same cadence.
- Core: packages that rarely change (types, interfaces)
- Active: packages under active development (UI, features)
- Infrastructure: build tooling, CI/CD, deployment

Choose the strategy that best matches the project's dominant organizational axis.
