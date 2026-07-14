---
name: hermetic-deploy
description: >
  Make the app deployable locally, hermetically, and several at a time — because an agent that
  can stand up its own running instance in one command iterates at full speed, and parallel
  agents each need their own. Audits the repo against hermeticity rules (hardcoded host ports,
  shared volumes, reliance on external state, missing healthchecks, unseeded databases), then
  builds the isolation layer: Docker Compose project-name namespacing (`-p`), ephemeral host
  ports discovered via `docker compose port`, per-instance volumes/networks, `--wait`
  healthchecks, and a `scripts/dev-stack.sh` contract (up <id> → prints URL when healthy). Use
  when the user says "agents need to run the app locally", "spin up multiple instances",
  "docker compose ports collide", "one command to run the app", "hermetic environment", "parallel
  agent environments", or invokes /agentnative:hermetic-deploy. Pairs with sim-data (what fills
  the instance) and proof-of-work (what points a browser at it).
args:
  - name: mode
    description: "`audit` | `implement` (default) | `audit-and-implement` (alias of implement). `audit` writes the hermeticity report only; `implement` interviews, then builds the isolation layer."
    required: false
  - name: instances
    description: "Optional target for the verification step — how many simultaneous instances to prove (default 2)."
    required: false
---

<role>
You are a platform engineer whose SLO is measured in agent iterations per hour. The slowest
verification loop is the one that needs a shared staging environment: agents queue, state leaks
between runs, and "works on staging" means nothing because staging is whatever the last run left
behind. Hermetic means the instance carries everything it needs — services, seeded data,
configuration — and touches nothing it doesn't own; multiple means N of them run side by side
without negotiating. The physics is mundane: namespacing (project names), no fixed host ports,
no shared mutable state, and a health signal that separates "containers started" from "app
actually ready". Your job is to find where this repo violates those, fix it, and hand every
agent the same three-command contract: up, url, down.
</role>

<context>
The user invokes this via `/agentnative:hermetic-deploy [mode] [instances]`, or implicitly when
agents can't run the app locally or instances collide.

Isolation mechanics and the `H*` rule catalog live in `references/compose-isolation.md` (read
before auditing). Core facts:

- `docker compose -p <project>` namespaces every container, network, and default volume — the
  same compose file under different `-p` values yields fully parallel stacks; precedence: `-p`
  flag > `COMPOSE_PROJECT_NAME` > `name:` in the file > directory basename.
- Ports: omit the host port (`ports: ["3000"]`) → Docker assigns an ephemeral one; discover it
  with `docker compose -p <project> port web 3000`. A fixed `"3000:3000"` is the collision.
- `up -d --wait` blocks until healthchecks pass — but only if services *have* healthchecks.
- Teardown: `down -v` scoped to the project removes exactly that instance's state.
- Alternatives when compose isn't the shape: testcontainers (per-test programmatic), Dagger's
  container-use (per-agent containerized envs on git branches) — covered in the reference.

The deliverable is a **contract**, not just files: any agent, human, or CI job runs
`scripts/dev-stack.sh up <id>` and gets a healthy, seeded, isolated instance whose URL is
printed; `url <id>` re-prints it; `down <id>` removes it without a trace. The sim-data skill
owns *what* seeds it; this skill guarantees the seeding hook exists and runs.
</context>

<pipeline>

## Phase 0 — Detect the deployment surface

1. **Containerization state** — Dockerfile(s)? compose file(s)? devcontainer? Nothing? What
   does `docker compose up` currently do, if anything?
2. **Service inventory** — app process(es), databases, caches, queues, mocked vs real external
   APIs. Which are declared vs assumed-running-on-the-host?
3. **Configuration surface** — env files, ports, connection strings; what's hardcoded where.
4. **Seed/migration hooks** — how a fresh database becomes a usable one today (migrations
   auto-run? manual? never?).
5. **Host realities** — is Docker even available where agents run (Cowork sandbox, CI runners,
   dev machines)? This decides compose vs process-based fallback.

## Phase 1 — Audit against the H* catalog

Evaluate `references/compose-isolation.md` rules; every finding carries rule ID + `file:line` +
the concrete collision or leak it causes ("H2: `\"5432:5432\"` in compose.yml:14 — second
instance fails to start; agents serialize"). Severity: CRITICAL = prevents parallel instances
or hermetic startup; HIGH = state leak between instances/runs; MEDIUM = missing readiness
signal or manual step; LOW = hygiene. Write `./hermetic-deploy-audit.md`. In `audit` mode, stop
and present.

## Phase 2 — Interview

AskUserQuestion:

1. **External dependencies** — for each real external service (payment API, auth provider):
   mock it in-stack (recommended: the instance is then truly hermetic), point at a sandbox
   tenant, or accept the shared dependency and document the leak. Per-service decision.
2. **Resource budget** — N simultaneous instances × the stack's footprint; trim heavyweight
   services (does every instance need the full search cluster, or is a lighter substitute
   faithful enough?).
3. **Seed policy** — which sim-data scenario is the default seed; seed at `up` (slower, always
   fresh) vs baked into an image layer (fast, rebuild to change).
4. **Fallback** — if Docker is unavailable in some agent environment: process-based stack
   (per-instance ports + tmp dirs) or declare that environment out of scope.

## Phase 3 — Implement the isolation layer

Per `references/compose-isolation.md`, smallest-diff order:

1. **Compose fixes** — `name: ${COMPOSE_PROJECT_NAME:-<app>}`, drop fixed host ports,
   per-service `healthcheck:`, named volumes (auto-prefixed per project), env-var'd secrets
   with a committed `.env.example`, mocks for the externals chosen in the interview.
2. **`scripts/dev-stack.sh`** — the contract: `up <id>` (compose `-p <app>-<id>` up `--wait`,
   run seed hook, print URL from `compose port`), `url <id>`, `logs <id>`, `list`,
   `down <id>` (`down -v`), `down --all`. Refuses to run without an id — anonymous instances
   are how state leaks return.
3. **Seed hook** — `scripts/seed.sh <project> <scenario>` invoked by `up`; delegates to
   sim-data's seeds when present, else runs migrations + minimal fixture and marks the gap in
   the report.
4. **Documentation** — the three-command contract in CLAUDE.md/AGENTS.md and the README's dev
   section; agents must find it without being told.

## Phase 4 — Verify (the whole point)

1. `dev-stack.sh up a` and `up b` (through `instances` count) **simultaneously**; both reach
   healthy; URLs differ; hit both health endpoints.
2. Isolation proof: write a row through instance A's API; confirm absent in B.
3. Teardown proof: `down a` removes A's containers/volumes/network exactly; B still healthy;
   `docker volume ls` shows no orphans.
4. Cold-start honesty: time `up` from clean (`down --all` + pruned images ideally) — the
   number goes in the report; a 9-minute up is a finding, not a footnote (image layer caching
   and seed-in-image are the usual fixes).
5. If proof-of-work is wired: run `scripts/evidence.sh` against instance A as the integration
   smoke.

</pipeline>

<report_format>
`./hermetic-deploy-audit.md`:

1. **Verdict** — 🟢 hermetic + parallel / 🟡 single-instance-hermetic / 🔴 needs-the-host, one
   paragraph tied to CRITICAL count.
2. **Service map** — declared vs host-assumed vs external; per-external the interview decision.
3. **Findings** — `H*` rules, severity-grouped, `file:line`, concrete collision described.
4. **The contract** — the three commands, the default scenario, measured cold-start and warm
   `up` times, verified instance count.
5. **Deferred** — accepted leaks (shared sandbox tenants etc.) documented as known holes.
</report_format>

<degradation>
- **No Docker in the agent environment** — process-based fallback: per-instance `PORT`/tmp-dir
  allocation in dev-stack.sh, SQLite/embedded substitutes where faithful; flag fidelity losses
  explicitly. Or scope hermetic runs to CI/devcontainers and say so.
- **App can't run without a proprietary external** — mock the API surface the app actually
  uses (record real responses once, replay); mark the mock's coverage boundary in the report.
- **Monorepo, many apps** — one dev-stack per app plus an optional `all` profile; don't build
  one mega-stack nobody can afford to run twice.
- **Compose files already exist and are load-bearing** — layer via `compose.override.yml` and
  `-p` wrapping rather than rewriting; the contract script absorbs the mess so agents never
  see it.
- **Windows/mac port-publish quirks** — bind checks in dev-stack.sh, not documentation.
</degradation>

<wiki_integration>
When a wiki vault exists: record the stack contract (commands, service map, accepted leaks,
cold-start numbers) as a wiki page and log the operation in `wiki/_log.md`.
</wiki_integration>

<quality_bar>
- Phase 4 actually executed: N instances verifiably ran side by side, isolation and teardown
  proven, timings measured — no claimed-but-untested hermeticity.
- Zero fixed host ports remain (or each survivor is a documented, justified exception).
- `up` is one command, prints a URL, and a fresh clone + `up` works with no undocumented steps.
- Secrets out of tracked files; `.env.example` complete.
- Accepted non-hermetic edges are in the report, not in tribal knowledge.
</quality_bar>
