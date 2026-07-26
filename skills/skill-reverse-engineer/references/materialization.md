# Knowledge materialization — formats and policy

Single source of truth for everything KM: the qualification test, the `host-context.json`
contract, the `_provenance` block, artifact placement, and the honesty labels. `rules.md` (the
KM family) and `refactor-recipes.md` (Recipe 7) point here rather than restating — if this file
and another disagree, this file wins and the other is an AM3 defect.

The idea in one line: when a target skill answers the same question from the same host source on
every run — by re-deriving, re-inferring, or worst of all from an unlabeled hardcoded copy — the
answer should be **materialized**: mined once by a generator script into a JSON artifact with
provenance, consulted at runtime, re-mined when the source drifts.

## 1. The materialization test

A fact qualifies for materialization only if **all four** hold:

1. **Stable** — the correct answer changes on release/schema cadence, not per run or per request.
2. **Written down** — a citable defining source exists in the host (a schema file, an enum in
   source, a registry, a migration set), or a stack-native introspection command can produce one.
3. **Mechanical to extract** — a script can mine the answer from the source without judgment.
4. **Worth caching** — the source is scattered, large, or expensive to derive from; if one
   compact machine-readable file already answers the question (a `package.json`, a single small
   JSON config), the recipe is *point the consuming instruction at that source directly* — a
   derived artifact there is pure indirection plus a new staleness surface.

**When re-derivation is RIGHT** (the anti-list — none of these get KM findings):

- **Volatile state** — git status, failing tests, live data, anything current-working-state.
- **One-shot facts** — consumed once, never again; generation costs more than it saves.
- **Compact machine-readable sources** — read them (test 4 above).
- **One-time hosts** — a skill that meets each host once has nothing to amortize.
- **No defining source** — a fact that exists only as model inference is judgment, not data.
  Freezing a guess into JSON launders judgment into false determinism. The only legitimate
  non-mined facts are `declared` ones — stated by the user in the interview, recorded with date.

The distill test, extended for KM: *would two competent runs be wrong to differ — and is the
correct answer written down in the host?* Written + compact → read the source. Written +
scattered/expensive → materialize with provenance. Not written → judgment (or ask the user).

## 2. The `host-context.json` contract

Written to `./reviews/skill-re-<name>.host-context.json` at the end of Phase 1, in all modes.
Schema by example (comments explain fields; the real file is plain JSON):

```jsonc
{
  "generated_at": "2026-07-24",
  "host_root": "/abs/path/to/the/repo/this/run/is/inside",
  "host_state": "host-grounded",       // host-grounded | host-generic | no-host
  "host_state_reason": "cwd contains the wiki vault the target skill operates on",
  "probe": { "script": "scripts/host_probe.py", "exit": 0 },
  "stack": [                            // model-interpreted, each fact tied to probe evidence
    { "fact": "Python-scripted Claude plugin repo, no app runtime", "evidence": "hooks/, scripts/*.py, no package manifest" }
  ],
  "data_schemas": [
    { "kind": "wiki-schema", "path": "wiki/_schema/SCHEMA.md", "summary": "frontmatter types + enums for the vault's page types" }
  ],
  "data_stores": [
    { "kind": "filesystem-vault", "evidence": "wiki/" }
  ],
  "knowledge_sources": [               // the Phase-1 → Phase-2 bridge: one row per stable fact
    {                                  // a model-* step of the TARGET consumes
      "question_the_target_answers": "which frontmatter values are valid per page type",
      "consumed_by_step": 4,           // row number in the step-executor matrix
      "answered_by": "wiki/_schema/SCHEMA.md:120-540",   // or "nowhere found"
      "stability": "stable",           // stable | volatile
      "materialization_candidate": true,
      "note": "target hardcodes a drifted copy at references/checks.md:118-125"
    }
  ]
}
```

`knowledge_sources` is the KM worklist: Phase 2 files KM findings from its
`materialization_candidate: true` rows, and the essential-judgment register absorbs the rest.
`stack` / `data_schemas` / `data_stores` are the model's *interpretation* of the probe's raw
candidates — the probe enumerates, the model concludes, this file records both sides.

## 3. The `_provenance` block

Every materialized artifact is JSON whose **first key** is `_provenance` (the `_` prefix sorts
first and marks it reserved). Two kinds exist; nothing else is expressible:

```jsonc
{
  "_provenance": {
    "kind": "mined",                   // mined | declared
    "generated_by": "scripts/generate_frontmatter_matrix.py",
    "generated_at": "2026-07-24",
    "sources": [ { "path": "wiki/_schema/SCHEMA.md", "sha256": "…" } ],
    "regenerate": "python3 scripts/generate_frontmatter_matrix.py wiki/_schema/SCHEMA.md --out <this-file>",
    "check": "python3 scripts/generate_frontmatter_matrix.py --check <this-file>",
    "ttl_days": 30,                    // fallback freshness bound when sources aren't hashable
    "policy": "check before trust; stale -> regenerate; generator unavailable -> derive fresh from sources and label"
  },
  "facts": { "…": "shaped for the consuming decision, keyed by the question not the source layout" }
}
```

A `declared` fact (from the interview, no defining source) replaces `generated_by` / `check`
with `"declared_by": "interview 2026-07-24"` and relies on TTL / re-interview for refresh.
There is deliberately no third kind: "the model inferred it once and we froze it" cannot be
written down in this format, which is the point.

## 4. Placement policy

| Fact scope | Project-local skill | Portable / plugin skill |
|---|---|---|
| Skill-invariant (KM4 decision matrices) | inside the skill (`references/` or `assets/`) | inside the skill |
| Host-specific (KM1–KM3, KM5 replacements) | inside the skill or host-side — interview picks | **host-side**: the domain-owned config dir if one exists (e.g. `wiki/_schema/generated/`), else `.claude/skill-facts/<skill-name>/` |

Invariants regardless of cell: the **generator always ships in the skill**; the consuming
instruction always handles artifact-absent (generate it if possible, else derive fresh from the
source, label the output, and suggest generating). In `new-version` mode with a read-only or
absent host, generate the artifact into the output directory with an explicit
"move to `<intended host path>`" note — never silently skip it.

## 5. Honesty labels

Same policy as the wireframe reuse library: **labels never lie**; the artifact is a cache, not
an authority; the source wins every conflict. Outputs that used materialized facts label them:

- `per <artifact> (mined from <source> — checked fresh <date>)` — `--check` passed this run
- `per <artifact> (cached — within TTL, generated <date>)` — no check run; TTL not exceeded
- `derived fresh — artifact stale/absent` — the fallback ladder bottomed out at the source

Fallback ladder on every consult: run `--check` → on stale, regenerate → if the generator is
unavailable, derive fresh from the cited sources and label. A stale artifact is never consulted
silently, and never beats a fresh source.
