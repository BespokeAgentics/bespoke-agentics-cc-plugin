# Phase 0 — Surface mapping

Cases come from the surface. Before generating any, write down everything the target touches, with
`file:line` wherever code exists. A thin surface map produces generic cases. A precise one produces
cases like "the `>` on `coupons.js:21` excludes an order of exactly $50.00, which the brief says
qualifies".

## `surface.md` format

Write `{WORK_DIR}/surface.md` with these sections. Leave a section out only if it truly does not
apply, and say so in one line ("Persisted data: none — pure function").

```markdown
# Surface — {target title}

Target: {kind} `{spec}` · built: {yes|no} · grounded: {yes|no} · level: {level}

## What it is
One paragraph: what the feature, plan, or change does for whom, in the target's own words where
possible (quote the document).

## Actors
Who or what triggers it: user kinds, roles, services, schedulers, webhooks.

## Entry points
Routes, handlers, UI controls, CLI commands, jobs, exported functions — `file:line` each.

## Inputs
| Input | Type / format | Source | Validation present (file:line) | Notes |

## Rules and thresholds
Every constant, limit, comparison, and policy that decides an outcome, with the **exact operator**
(`>` vs `>=` matters) — `file:line`, or the document quote for plans.

## States and transitions
Status fields, steps of a flow, lifecycle states, and which transitions the code allows.

## Persisted data
Tables, collections, files, keys and caches read or written; their shape; what older records look like.

## Dependencies
Network calls, database, filesystem, third-party APIs, queues, the clock, randomness, env vars,
config and feature flags — `file:line` each.

## Existing tests
What is covered today (`file:line` of the test). Cases already pinned by a test are usually HANDLED;
the gaps are where to look.

## What changed            (changes targets only)
Per changed hunk: the behavior before and after, in one line each. Then the callers of every changed
symbol — one hop at standard, two at deep — `file:line` each.

## What the document states   (plan targets only)
Stated behaviors, flows, acceptance criteria and non-goals, quoted. These become `spec` sources.

## Unknowns
What could not be determined and why.
```

## Who maps it

**`quick`** — the main session, from the target and its direct dependencies (the files it imports and
the files that import it). Keep it short; skip sections that need a wide search, and list them under
Unknowns.

**`standard`** — launch up to three `Explore` agents in one response, split by concern:

| Agent | Sections |
| --- | --- |
| A — entry and rules | Entry points, Inputs, Rules and thresholds |
| B — state and dependencies | States and transitions, Persisted data, Dependencies |
| C — tests and change | Existing tests; for changes targets, What changed (callers one hop) |

For a small target (one or two files), one agent covering everything is enough.

**`deep` / `prove`** — the same split, wider: callers two hops out, the shape of persisted data
(migrations, schema files, fixtures, seed data), every config and flag the path reads, and the
deploy/migration order when the target changes stored data.

### Explore prompt

```
Map the surface of {kind} `{spec}` in {PROJECT_DIR} for an edge-case analysis. Cover ONLY these
sections: {sections}. {For changes: the diff is `{diff_cmd}`; untracked files: {list}.}
{For plans: the document is {path}; ground the components it names.}

Return markdown under the given section headings. Cite file:line for every code fact. When something
cannot be found, say "not found" — never guess a location. Record exact comparison operators and
constant values. Do not suggest edge cases; only map what exists.
```

## Plans and unbuilt features

**Plan target, grounded** — the document gives What it is, What the document states, and most of the
Actors, Inputs and Rules. Grounding (as in plan-review) adds the existing code the plan touches: the
current entry points it modifies, the persisted data it will meet, the callers of what it changes. The
`change` lens applies whenever the plan modifies existing behavior.

**Unbuilt feature or `--no-ground`** — every fact comes from the document or description. Mark
inferred elements `(inferred)`, leave every `file:line` column empty, and say in Unknowns that current
behavior cannot be assessed.
