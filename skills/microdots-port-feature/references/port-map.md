# Phases 3–4 — Micros grounding and the port map

`port-map.md` is two things at once: the implementer's worklist (every traced
unit gets a disposition) and the decision feed for the spec interview (every
genuinely open choice gets a register row). It is where source-side evidence
meets target-side law.

## Phase 3 — Ground in the workspace (read at runtime)

This skill embeds none of the micros workspace's rules, deliberately: the
workspace evolves, and an embedded copy would rot and then lie with
confidence. Read the law fresh every run:

1. **`AGENTS.md`** — the layout contract (which files a micro comprises), the
   hard rules (what a micro may and may not do), and the trap table. Pull the
   trap rows that plausibly apply to *this* port into the trap register with
   their citations — a port that needs persistence cares about different traps
   than a streaming port.
2. **`docs/reuse-catalog.md`** — run the feature's needs (from the trace and
   inventory) against the Trigger index the way a requester's words would hit
   it: gating/PIN, persistence, polling, streaming, multi-element, admin
   surfaces. Note matched pattern IDs. Then **verify before trusting**, per
   the catalog's own maintenance protocol: `ls` every listed path; on a miss,
   grep the entry's Key symbols to find where the code moved; fix a rotted
   entry in this run — a rot you worked around silently will rot for the next
   agent too.
3. **The existing micros** — list them, and pick the one closest in shape to
   this feature (a poll-only display, a stateful gated CRUD surface, a
   streaming interaction) as the working reference. The nearest micro answers
   idiom questions the docs never will: how big `update` gets, how views are
   factored, what a store seam looks like in practice.

Also confirm what the workspace's shared kit actually exports today (its
browser/service/worker entry points and helpers) — the disposition
`import-shared` is only real when the export resolves.

## Phase 4 — The port map

### 1. Public surface

Resolve every boundary crossing from the trace into the micro's entire public
surface: **attributes in, events out**. For each attribute: name, type,
who sets it (which host, from what knowledge), default, and what changes when
it changes at runtime. For each event: name, payload schema, and who is
expected to listen. Two tests keep the surface honest:

- If a crossing resolves to neither an attribute, an event, an RPC the micro
  owns, nor an explicit cut, the boundary analysis missed something — go back.
- If the attribute list starts encoding *behavior* rather than configuration
  ("mode=advanced-with-legacy-sorting"), the scope cut is wrong, not the
  attribute.

### 2. Contract draft

RPC names, payload/success schemas, and tagged errors — drafted, not final;
the spec interview may reshape it. Sources, in rank order: the **observed
network shapes** (what the feature actually depends on), intersected with the
**traced types** (what the source code declares), tempered by what the micro
actually needs (a port is also a chance to shed accreted fields — shedding is
a `defer`/`drop` disposition, visible, not an accident). Observed error
responses and validation rules name the tagged errors. If concurrent edits
were observed or traced, say so — the contract will need a versioning story.

### 3. TEA sketch

The Elm-architecture design, derived from the behavior lane and the state
catalog — never from the source markup:

- **Model**: the states as data. Prefer discriminated unions over boolean
  soup — every impossible-but-representable state the source app allowed is a
  bug this port gets to delete. Async data needs a refreshing/stale notion so
  a poll never blanks a rendered value.
- **Messages**: one per thing-that-happened, named as facts (past tense), not
  as commands.
- **Subscriptions**: the polls, timers, and streams the behavior lane found,
  with their intervals.
- **View zones**: the regions of the UI, mapped from the state catalog.

Then the **coverage check, both directions**: every state observed in Phase 2
maps to a Model state, and every Model state has a decided view. A state
observed but unmodeled is a silent feature loss; a state modeled but unviewed
is a blank screen waiting to ship. Unreached states from the inventory's
"Not reached" table show up here as explicit gaps, not as guesses.

### 4. Data & storage

If the feature is stateful: the tables the micro will own, the storage-seam
shape (a service interface the handlers depend on, with per-platform adapters
providing it — the workspace's stateful reference micro shows the idiom),
migrations as numbered SQL, and the seed strategy. If the register's
data-ownership row is still open, sketch the leading option and mark the
dependency.

### 5. Disposition table

One row per traced unit — file, or coherent piece of one:

| Source (file:line) | Disposition | Target | Notes |
|---|---|---|---|

Dispositions, aligned with the catalog's own status vocabulary:

- **`import-shared`** — the workspace kit already provides it; import, never
  copy. Only real once the export is confirmed to resolve.
- **`copy-adapt`** — a cataloged pattern or an existing micro's piece, ported
  per its adaptation notes.
- **`reimplement`** — re-expressed in the target idiom from the behavior map.
  The default for all source UI code.
- **`drop`** — dies at the boundary (shell affordances, framework glue,
  features cut from scope). Dropping is a decision, so it is a row, not an
  omission.
- **`defer`** — explicitly out of v1; lands in the spec's out-of-scope section
  with its reason.

The table is complete when every file the trace touched appears at least once.
An implementer should be able to work top to bottom without re-deriving intent.

### 6. Trap register

The applicable trap-table rows, quoted short and cited, next to the wave they
threaten. This is cheap insurance: the traps are exactly the failures that
pass typecheck and fail silently.

### 7. Decision register

The interchange format for the spec interview — one row per genuinely open
decision:

| ID | Decision | Options | Recommendation (evidence) | Status |
|---|---|---|---|---|

Status ∈ `open` / `assumed` (non-interactive run picked the recommendation —
labeled, never silent) / `decided` (by whom, when). The standard set — include
each unless the dossier makes it moot:

- **D-data** — data ownership: fresh start · one-off import · keep reading the
  source system (an external call from the service — likely new ground; flag
  it). The "other readers/writers" table decides how hard this one is.
- **D-auth** — none · per-call gate · something the workspace has not done
  yet. A micro has no ambient session; "port the session" is not an option.
- **D-deploy** — edge/Workers (isolates recycle: no in-memory state; managed
  SQL) · long-lived runtime (filesystem, processes, streams allowed). The
  behavior lane usually answers this: streaming and child processes force the
  choice.
- **D-scope** — which subfeatures are v1, which defer. Cite the disposition
  table.
- **D-ux** — re-skin to the workspace's semantic tokens (the default —
  palette literals are banned there anyway) vs. mimicking the source look
  within tokens.
- **D-tags** — one element or several (a public surface plus an admin surface
  is the classic split; the catalog has the multi-tag conversion).
- **D-old-app** — what happens to the feature in the source app: dual-run,
  redirect, retire. Out of this skill's hands (the source is never modified),
  but the spec must record the intent.

Add feature-specific rows freely; delete none silently. Every row the
interview settles gets its status flipped in place — the register stays the
single truthful record of what was decided and what was assumed.
