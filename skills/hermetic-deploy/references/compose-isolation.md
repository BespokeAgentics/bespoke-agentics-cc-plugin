# H* — Hermeticity Rules & Compose Isolation Mechanics

Compose semantics verified July 2026 against docs.docker.com (project-name precedence, port
publishing, `compose port`).

## The mechanics

**Project namespacing.** `docker compose -p <project> up` prefixes every container
(`<project>_web-1`), network (`<project>_default`), and default named volume
(`<project>_dbdata`). Same file, different `-p` → fully parallel stacks. Precedence
(highest→lowest): `-p` flag > `COMPOSE_PROJECT_NAME` env > top-level `name:` in the file >
directory basename. Put `name: ${COMPOSE_PROJECT_NAME:-<app>}` in the file so bare
`docker compose up` still works for humans.

**Ports.** The collision is `"3000:3000"`. Publish the container port only and let Docker
assign an ephemeral host port:

```yaml
services:
  web:
    ports:
      - "3000"          # host port auto-assigned
```

Discover it: `docker compose -p app-a port web 3000` → `0.0.0.0:49155`. (The `"0:3000"` form
also auto-assigns in practice but isn't documented behavior — prefer the bare form.)

**Readiness.** `up -d --wait` returns when healthchecks pass — meaningless without them:

```yaml
  web:
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:3000/healthz"]
      interval: 5s
      timeout: 3s
      retries: 20
      start_period: 15s
  db:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER}"]
      interval: 5s
      retries: 20
    # web should depend_on: db: { condition: service_healthy }
```

**Teardown.** `docker compose -p app-a down -v` removes that project's containers, networks,
and volumes — exactly and only its own. Resources marked `external: true` are shared and
survive; that's the escape hatch for deliberately-shared infra, and it should be rare.

## H* rule catalog

| ID | Severity | Rule | Symptom when violated |
|----|----------|------|----------------------|
| H1 | CRITICAL | No one-command startup (compose absent/broken, undocumented manual steps) | agents can't self-serve an instance at all |
| H2 | CRITICAL | Fixed host ports (`"5432:5432"`) | second instance fails to bind; agents serialize |
| H3 | CRITICAL | State on the host or in shared paths (bind-mounted data dirs, host DB, `/tmp` fixtures) | instances read each other's writes; runs aren't reproducible |
| H4 | HIGH | Missing `name:`/project discipline (relies on directory basename) | two checkouts/worktrees silently share or clobber a stack |
| H5 | HIGH | Hard dependency on a live external service with shared mutable state | tests interfere across instances and with production sandboxes |
| H6 | HIGH | No healthchecks / `depends_on` without `condition: service_healthy` | "up" ≠ ready; agents race the database and flake |
| H7 | MEDIUM | Fresh instance isn't usable (no migration/seed hook at startup) | every agent hand-rolls setup; drift between instances |
| H8 | MEDIUM | Secrets/config baked into compose or images instead of env (`.env.example` missing/stale) | fresh clone fails; credentials leak into git |
| H9 | LOW | No scoped teardown path (`down -v` undocumented; orphan volumes accumulate) | disk bloat; stale state resurrections |
| H10 | LOW | Anonymous instances (nothing enforces an instance id) | untracked stacks nobody owns or cleans |

## scripts/dev-stack.sh (shape)

```bash
#!/usr/bin/env bash
set -euo pipefail
APP="myapp"                                   # substitute
CMD="${1:?usage: dev-stack.sh up|url|logs|list|down <id>|--all}"; ID="${2:-}"

project() { echo "${APP}-${1:?instance id required}"; }

case "$CMD" in
  up)
    P=$(project "$ID")
    docker compose -p "$P" up -d --build --wait
    scripts/seed.sh "$P" "${SEED_SCENARIO:-default}"
    HOSTPORT=$(docker compose -p "$P" port web 3000 | sed 's/0.0.0.0/localhost/')
    echo "ready: http://$HOSTPORT" ;;
  url)
    docker compose -p "$(project "$ID")" port web 3000 | sed 's/^/http:\/\//;s/0.0.0.0/localhost/' ;;
  logs)  docker compose -p "$(project "$ID")" logs -f ;;
  list)  docker compose ls --filter "name=${APP}-" ;;
  down)
    if [ "$ID" = "--all" ]; then
      docker compose ls -q --filter "name=${APP}-" | xargs -I{} docker compose -p {} down -v
    else
      docker compose -p "$(project "$ID")" down -v
    fi ;;
esac
```

Seed hook contract: `scripts/seed.sh <project> <scenario>` — runs migrations then loads the
scenario (delegates to the sim-data skill's seeds when present). Must be idempotent: seeding an
already-seeded instance is a no-op or a clean reset, never a duplicate-pile.

## Mocking externals

For each real third-party the app calls: capture the response surface the app actually uses
(record once against the sandbox), replay from an in-stack mock service (WireMock, MSW in a
sidecar, or a 50-line express stub — match the repo's language). The mock is a service in the
compose file like any other, healthchecked and namespaced. Document the coverage boundary: the
mock proves the app's behavior, not the vendor's.

## Alternatives to compose

- **testcontainers** (Docker-owned) — programmatic, per-*test* containers with random ports by
  design (`container.getMappedPort(3000)`); right when the need is test isolation rather than a
  long-lived instance an agent explores. Can coexist with the dev-stack.
- **Dagger container-use** — MCP server giving each coding agent its own containerized
  environment on its own git branch; right when agents need isolated *workspaces* (code +
  environment), not just app instances. Heavier adoption; propose, don't default.
- **Process-based fallback** (no Docker): dev-stack.sh allocates `PORT=$(get_free_port)`,
  per-instance tmp dirs, SQLite/embedded substitutes; loses fidelity (note which services
  diverge from production shape). Better than nothing; label the fidelity gap.

## Cold-start budget

Measure `time dev-stack.sh up bench` from clean. Levers, in payoff order: image layer caching
(dependency layers before source layers in the Dockerfile), seed-in-image (bake the default
scenario into the db image; `up` then only migrates deltas), trimming services agents rarely
need behind a compose `profiles:` flag, and pre-pulled base images in CI/devcontainer setup.
Target: warm `up` under a minute; report whatever the truth is.
