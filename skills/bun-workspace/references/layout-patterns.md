# Layout Patterns

How to organize a Bun workspace, and how packages reference each other.

## Two layouts worth considering

### Flat-preserving (default for migrations)

```
my-monorepo/
├── package.json          # workspaces: ["package-a", "package-b", "package-c"]
├── bun.lock
├── tsconfig.base.json
├── package-a/
│   └── package.json
├── package-b/
│   └── package.json
└── package-c/
    └── package.json
```

Keep each package where it already lives. Lowest disruption — no moves, no broken imports, no churn in git history. Best when migrating *into* a workspace because every commit before today still resolves.

### Buckets (`apps/*` + `packages/*`)

```
my-monorepo/
├── package.json          # workspaces: ["apps/*", "packages/*"]
├── apps/
│   ├── web/
│   └── admin/
└── packages/
    ├── ui/
    └── utils/
```

Two-level structure that separates *deployables* (apps — Next, Astro, Workers) from *libraries* (packages — code consumed by apps). Worth the moves when:

- There are clear apps vs libs (≥ 2 of each)
- The team will add more packages over time
- You'll have CI matrices that test apps and packages differently

**Don't bucket prematurely.** A 3-package monorepo with one app and two libs is fine flat. Buckets are an organizational tool for ~6+ packages.

### Other layouts (mention only on request)

- **`services/*` + `libs/*`** — common for backend-heavy monorepos. Same idea as `apps/*` + `packages/*`, different vocab.
- **Domain folders** (`accounts/{api,web,lib}`, `billing/{api,web,lib}`) — only if the team already thinks in domains. Risk of awkward cross-domain coupling.

## Cross-package imports

Two mechanisms, used together:

### 1. The `workspace:*` protocol

In a consumer's `package.json`:

```json
{
  "dependencies": {
    "@org/utils": "workspace:*"
  }
}
```

`workspace:*` means "the local workspace version, whatever it is." When you publish, Bun rewrites it to a concrete version. When developing, Bun symlinks. This is the *only* correct way to express a workspace dep — never use `file:` or hardcoded paths.

### 2. TypeScript paths (optional, only if needed)

If a package imports another *before* the dep is wired (during initial scaffolding) or you want better cross-package navigation, add to `tsconfig.base.json`:

```json
{
  "compilerOptions": {
    "paths": {
      "@org/utils": ["./packages/utils/src/index.ts"]
    }
  }
}
```

In practice the `workspace:*` protocol alone is sufficient if every package has a proper `main`/`exports` field pointing at its built (or source) entry. Reach for tsconfig paths only when there's a gap.

## Scoped names matter

Always scope workspace packages: `@<org>/<name>` rather than bare `<name>`. Three reasons:

1. **Collision-proof.** Two unscoped packages named `app` will break workspace resolution.
2. **Greppable.** `@org/` makes internal imports stand out from npm packages.
3. **Publishable later.** Scoped names map cleanly to npm namespaces if anything ever needs to ship.

The scope is just an organizational prefix — it does not need to match a real npm org until the package is published.

## Don't workspace-ize everything

Non-package directories (`docs/`, `marketing/`, `plans/`, `scripts/`, `wiki/`) stay where they are and are simply *not* in the `workspaces` array. They live alongside the workspace, not inside it. The user often expects "monorepo" to mean "every folder is a workspace member"; it doesn't.
