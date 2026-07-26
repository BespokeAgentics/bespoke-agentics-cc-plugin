# Detection — candidate classes, seed-and-trace, liveness checklist

## Candidate classes

What a coding session typically leaves behind, roughly in order of frequency:

| Class | What it looks like | Primary signal |
|-------|--------------------|----------------|
| Dead import | Imported symbol never used in the importing file | Linter/compiler warning; grep within file |
| Unused local / private | Un-exported function, variable, method with zero in-file references | Compiler flags (`noUnusedLocals`, `F841`); in-file grep |
| Orphaned export | Exported symbol with zero importers anywhere | Detector (knip/ts-prune/vulture) + project-wide grep |
| Orphaned file | File with zero inbound imports/references | Detector + import-path grep (resolve aliases first) |
| Superseded implementation | Old version left beside its replacement (renamed fn, `v2` component, rewritten helper) | Diff shows a new symbol whose shape/name mirrors an existing one; the old one's references migrated |
| Stale test | Test whose subject was removed or renamed | Test imports a now-gone symbol, or its `describe`/name references a removed feature |
| Orphaned test scaffolding | Mocks, fixtures, factories, snapshots whose only consumer test is gone | Reference search from remaining tests; snapshot runners flag obsolete snapshots |
| Test-only-referenced production code | Prod symbol whose only references are its own tests | Reference search partitioned into test vs non-test hits |
| Unused dependency | Manifest entry with zero import sites | Detector (knip, `cargo machete`) + import grep incl. subpaths (`lodash/get` counts for `lodash`) |
| Commented-out block | Code disabled during the session and left behind | Diff shows added comment lines that parse as code |
| Unreachable branch | `if (false)`, dead switch arm, code after unconditional return | Compiler/linter; manual read of touched functions |
| Cascade dead | Code whose only consumer was removed in an earlier wave | Re-scan after each wave |

## Seed-and-trace (diff scopes)

The diff is a list of *reference movements*. For each hunk:

1. **Removed references.** Every deleted line that contained a call, import, JSX usage, or
   subclass/implements points at a target that lost one consumer. Collect targets; for each, count
   remaining references project-wide. Zero remaining → candidate.
2. **Renames and rewrites.** An added symbol that mirrors an existing one (same name modulo
   prefix/suffix/casing, same signature shape, same file area) suggests the existing one was
   superseded. Check whether the old one's callers moved to the new one.
3. **Touched-file hygiene.** Within every modified file: unused imports, unused locals, private
   functions with no remaining in-file callers, newly commented-out blocks (present in `+` lines
   as comments that parse as code).
4. **Test shadow.** For every symbol/file the session removed or renamed, find the tests, mocks,
   fixtures, and snapshots that referenced the old name. For renames, tests referencing the old
   name are stale even though a same-purpose test may exist for the new name.
5. **Dependency delta.** For every import site the diff removed, check whether it was the
   package's last import site in the project.

Trace transitively but stay inside scope discipline: a candidate is in scope when its deadness is
*attributable* to the change set (the change set removed its last consumer, or it lives in a
touched file). A symbol that was already dead before the session goes to out-of-scope
observations.

## Liveness checklist

A candidate survives (is NOT removable) if any of these find a reference. Run the cheap checks
first; record which checks ran per candidate — the report cites them as evidence.

1. **Static references, non-test.** Project-wide search for the symbol/file, excluding its own
   definition and its dedicated tests. Search both the bare name and qualified/aliased forms;
   resolve path aliases (`tsconfig.json` `paths`, bundler aliases) before declaring a file
   orphaned.
2. **Static references, test-only.** Hits only in its own tests → still a candidate. High
   confidence when the change set itself removed the last production reference (the diff is the
   author's expressed intent to migrate away; the stale tests join the removal unit); medium
   otherwise (project scope or pre-existing test-only state — may be intended public API or
   half-built work).
3. **Dynamic references.** The name inside string literals, template strings, or computed access:
   config files (JSON/YAML/TOML), route tables, CLI command maps, DI/service-container
   registrations, event names, feature-flag maps, `getattr`/`globals()[...]`/`import_module`
   (Python), `require(variable)`/`import(variable)` (JS), reflection (Java/C#), dotted-path
   strings (Django `settings`, Celery tasks, Airflow DAGs). A near-miss (generic name appearing in
   strings for other reasons) is a medium-confidence marker, not proof of life — read the hit.
4. **Framework conventions** — files that are live with zero importers: Next.js `app/`/`pages/`
   entries (`layout`, `loading`, `error`, route handlers, `generateMetadata`), SvelteKit
   `+page`/`+server`/`+layout`, Remix routes, Nuxt `pages/`, Convex `convex/` exports, serverless
   handlers referenced from `serverless.yml`/`wrangler.toml`/SAM templates, DB migrations, Storybook
   `*.stories.*`, seed/CLI scripts referenced from manifest `scripts`.
5. **Public API surface.** `package.json` `exports`/`main`/`module`/`types`/`bin`; the root
   barrel of a published package; `__init__.py` re-exports of a published Python package; `pub`
   items of a published crate's `lib.rs`; `.d.ts` declarations. If the project is an application
   (not published), barrel exports are ordinary exports — check whether the package is actually
   published before granting API status.
6. **Keep-markers.** `@keep`, `@public`, `@api`, `@preserve` in doc comments; linter disable
   comments specifically for unused checks (someone already decided to keep it).
7. **Entry points and tooling references.** Manifest `scripts`, CI workflows, Dockerfiles,
   Procfiles, and config files that name files/commands directly.

Documentation references (README, comments elsewhere) do not make code live, but note them in the
report so the user can fix the docs.

## Confidence rubric

- **High** — zero non-test references via ≥2 independent strategies (detector + manual sweep
  count as two; two manual sweeps with different patterns also count), no checklist match,
  in-scope, gates runnable. Auto-remove, gated.
- **Medium** — dead by primary analysis, one risk marker: test-only references without diff
  intent; barrel/root export of a possibly-published package; generic name with unread or
  ambiguous string hits; commented-out block; unused dependency; single detection method only.
  Batch-confirm.
- **Low** — any checklist match, or evidence incomplete (a search you couldn't run, an alias you
  couldn't resolve). Report only, with what you did and didn't verify stated plainly.

The rubric only moves candidates *down*. Nothing promotes a medium to high — not detector
unanimity, not user impatience, not a green build.
