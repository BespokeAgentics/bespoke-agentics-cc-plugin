# Phase 4 — Composition, port maps, the Effect-optimization register

`port-map.md` is the implementer's worklist and the decision feed for the spec
interview. For a whole-app port it opens with the settled composition and then
carries one port-map section per MicroDot. It is where source-side evidence
meets target-side law.

## 1. The composition proposal (user-confirmed, always)

From the seams lane, the boundary analysis, and the inventory, draft **2–3
candidate compositions**. Each candidate states:

- The MicroDots — name, one-line purpose, and the custom-element **tags** each
  registers (one directory may register several tags, the way the monorepo's
  `auction` ships `auction-card` + `auction-dashboard`).
- Per dot: the contract sketch (RPC names only), the data it would own.
- **What the host brokers** between dots — each cross-dot dependency named,
  with its floor: **a brokered nudge is an optimisation; a poll is the
  floor**. A dependency that cannot survive on polling argues against the cut.
- What the cut severs (shell affordances, shared stores) and what that costs.

Include the single-MicroDot composition as a candidate whenever it is
defensible — more dots is not more virtue; every cut buys independent deploys
at the price of a brokered seam.

Present via **one AskUserQuestion**, recommendation first with the evidence
that ranks it, alternatives as the other options, each with a short ASCII
sketch of the dot/tag layout in its preview. The user's choice becomes
**D-composition: decided** and heads `port-map.md`. In a non-interactive run
composition may NOT be assumed — stop and say the run needs the user.

## 2. Grounding checks (before drafting per-dot maps)

- Monorepo mode: verify every `import-shared` you plan to lean on actually
  resolves in `@bespokeagentics/microdots-runtime`'s entry points today; verify catalog
  entries per the catalog's own maintenance protocol (`ls` listed paths; on a
  miss grep the Key symbols; fix rot in this run).
- Standalone mode: verify the published `@bespokeagentics/microdots-*` exports you plan to
  import exist at the published version — `import-shared` is only real when
  the export resolves.

## 3. Per-MicroDot port maps

One section per dot in the confirmed composition:

### 3a. Public surface

Attributes in (name, type, who sets it, default, what changes when it changes
at runtime) and events out (name, payload schema, who listens — the host
broker or the embedding page). Two honesty tests: a crossing that resolves to
neither an attribute, an event, an owned RPC, nor an explicit cut means the
boundary analysis missed something; an attribute encoding _behavior_ rather
than configuration means the scope cut is wrong.

### 3b. Contract draft

RPC names, payload/success schemas, tagged errors — drafted, not final.
Sources, in rank order: observed network shapes ∩ traced types, tempered by
what the dot actually needs (shedding accreted fields is a visible
`defer`/`drop`, not an accident). Observed error responses name the tagged
errors.

### 3c. TEA sketch

Model as data (discriminated unions over boolean soup — every
impossible-but-representable state the source app allowed is a bug this port
deletes; async data gets a refreshing/stale notion so a poll never blanks a
rendered value), Messages as past-tense facts, subscriptions with intervals,
view zones. Then the **coverage check, both directions**: every observed state
maps to a Model state, and every Model state has a decided view.

### 3d. Data & storage

Owned tables, the storage-seam shape (a `Context.Service` interface the
handlers depend on, with per-platform adapters), migrations as numbered SQL,
seeding. If D-data is still open, sketch the leading option and mark the
dependency.

### 3e. Disposition table

One row per traced unit that lands in this dot:

| Source (file:line) | Disposition | Target | Notes |
| ------------------ | ----------- | ------ | ----- |

Dispositions: **`import-shared`** (the runtime provides it; import, never
copy) · **`copy-adapt`** (a cataloged pattern or an existing MicroDot's piece)
· **`reimplement`** (re-expressed from the behavior map — the default for all
source UI code) · **`drop`** (dies at the boundary; a row, not an omission) ·
**`defer`** (out of v1, with its reason). Complete when every file the trace
touched appears in exactly one dot's table (or in the shared `drop`/`defer`
lists).

## 4. The Effect-optimization register

The whole-app port's own artifact: one row per source idiom the trace found,
mapped to the idiom it becomes in the target. This is where "optimizations
applied when porting to Effect" stops being a vibe and becomes a checklist.

| Source idiom (file:line) | Target idiom | Provenance | Notes |
| ------------------------ | ------------ | ---------- | ----- |

Provenance ∈ **`standard`** (the framework's documented shape) ·
**`prior`** (a memory mapping row — name the record) · **`novel`** (this port
mints it — a Phase 8 memory-write candidate).

The standard rows — instantiate each that the trace evidences, never copy
rows the trace does not support:

| Source idiom                              | Target idiom                                                                       |
| ----------------------------------------- | ---------------------------------------------------------------------------------- |
| React `useState`/`useReducer`/context     | Model as effect Schema discriminated union; Messages; `update`                     |
| Boolean loading/error flags               | Async-data union states with a refreshing/stale notion                             |
| zod / io-ts / hand-rolled validation      | effect Schema (shared in the contract, one source of truth both sides)             |
| `fetch`/axios call sites                  | RPC client from the contract, a function of the base URL                           |
| Express/node/route handlers               | RpcGroup handlers, platform-free; platform bindings at the entry only              |
| Thrown errors / status-code branching     | Tagged errors in the contract                                                      |
| `setInterval`/`setTimeout` polling        | Foldkit subscriptions with declared intervals                                      |
| SSE/websocket streaming                   | Effect streams service-side; subscription client-side — and a D-deploy consequence |
| `process.env` / build-time config         | Attributes — the mounting host chooses, never the build                            |
| Module-scope singletons / service objects | `Context.Service` + Layers                                                         |
| `Promise.all` chains                      | `Effect.all` with explicit concurrency                                             |
| localStorage session/resume state         | The storage seam or the catalog's resume-after-reload pattern                      |
| Ad-hoc CORS / server wiring               | `@bespokeagentics/microdots-runtime` service entry (origins registered, not improvised)            |

## 5. Trap register

The applicable trap rows from the target's own trap table (monorepo:
`AGENTS.md` + `wiki/patterns-and-traps/_index.md`), quoted short and cited,
next to the wave they threaten. Standalone mode: the traps recorded in the
port memory's records, same treatment.

## 6. Decision register

The interchange format for the spec interview — one row per genuinely open
decision:

| ID  | Decision | Options | Recommendation (evidence) | Status |
| --- | -------- | ------- | ------------------------- | ------ |

Status ∈ `open` / `assumed` (labeled, never silent) / `decided` (by whom,
when). D-composition arrives already `decided` from §1. The standard set —
include each unless the dossier makes it moot:

- **D-data** — fresh start · one-off import · keep reading the source system.
- **D-auth** — none · per-call gate · something new. A MicroDot has no ambient
  session; "port the session" is not an option. Secrets fail closed.
- **D-deploy** — Workers (isolates recycle: no in-memory state; D1) ·
  long-lived runtime (streams, processes, an Agent SDK allowed). Streaming and
  child processes usually force this; a dot forced long-lived gets **no Worker
  entry, deliberately** — record it so nobody adds one later.
- **D-scope** — which subfeatures are v1, which defer. Cite the disposition
  tables.
- **D-ux** — re-skin to `@bespokeagentics/microdots-theme` semantic tokens (the default) vs.
  mimicking the source look within tokens.
- **D-old-app** — dual-run, redirect, retire. Out of this skill's hands, but
  the spec records the intent.

Add app-specific rows freely; delete none silently. Every row the interview
settles gets its status flipped in place — the register stays the single
truthful record of what was decided and what was assumed.
