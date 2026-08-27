# Phases 7-8 -- The dossier and the handoff

## Why the dossier uses port-app's names

`microdots-port-app` reads a dossier at `<target>/docs/ports/<slug>/` and, when one
already exists, re-verifies its anchors instead of re-deriving them. So the handoff needs
no adapter: write the artifacts it already reads, under the names it already reads, and
declare what is pre-satisfied.

## Artifacts

| File | Written by | Contents |
| --- | --- | --- |
| `_src/` | Phase 1 | The extracted source tree -- the evidence base and the handoff's "source app" |
| `prototype-inventory.json` | Phase 2 | Module roles, store map, seam graph, drops |
| `context.md` | Phase 3 | The Stage-1 digest, ≤30 lines, passed verbatim to agents |
| `profiles/<screen>.json` | Phase 4 | One screen profile per module, schema-valid |
| `synthesis.json` | Phase 5-6 | Entities, routes, features, shared services, theater and ambiguity registers -- updated in place by Stage-2 |
| `seams.md` | Phase 5 | Candidate cut lines and their crossings |
| `trace.md` | Phase 7 | port-app's Phase 1 artifact, rendered from `_src` |
| `ui-inventory.md` | Phase 7 | port-app's Phase 2 artifact, rendered from the profiles |
| `functional-spec.md` | Phase 7 | The human-readable spec: per-screen behavior with citations |
| `dossier-manifest.json` | Phase 7 | The handoff contract |

## `trace.md` -- rendered, not re-derived

Use port-app's own section order so it reads as the artifact it replaces: `Summary` ·
`Surface` (`| What | Where | Notes |`) · `Behavior` (anchored bullets) · `Data` ·
`API` · `Dependencies` · `Seams` · `Boundary analysis` · `Not found / uncertain`.

Two sections must be honest rather than empty:

- **API.** A prototype serves nothing and calls nothing. Write exactly that, then list the
  operations the theater register implies -- clearly labeled as *required, not observed*.
- **Boundary analysis.** Ambient dependencies here are `window` globals and vendored
  design-system globals, not env vars and sessions. Tag each with what it must become:
  attribute · event out · owned RPC · explicit cut.

## `ui-inventory.md` -- labeled by provenance

Same columns as port-app's (`| # | Route | State | Screenshot | Components | Data shown |
Interactions |`), with the header line carrying the verification status. Without
`--serve`, every row is labeled `derived from prototype source` and the status line reads
**"not visually verified"**. With `--serve`, serve `_src/shell.html` on a local port and
follow `../microdots-port-app/references/visual-inventory.md` -- fresh tab with an
explicit tabId, screenshot **states not pages** as `ui/state-NN-<label>.png`, and never
simulate a walk that did not happen.

Note the known limit up front: a served prototype exercises mock data only, so no network
shapes are observable. Say so instead of leaving the section looking incomplete.

## `dossier-manifest.json` -- the handoff contract

```json
{
  "produced_by": "microdots-port-prototype",
  "generated": "<ISO-8601>",
  "source_kind": "claude-design-prototype",
  "artifact": "<abs path to the original .html>",
  "artifact_sha256": "<from _src/index.json>",
  "source_app_path": "<dossier>/_src",
  "slug": "<slug>", "target": "<abs path>", "target_mode": "monorepo|standalone",
  "phases_satisfied": {
    "trace": { "file": "trace.md", "basis": "extracted prototype source", "reverify": "anchors only" },
    "ui_inventory": { "file": "ui-inventory.md", "basis": "source-derived|browser-walk",
                      "visually_verified": false }
  },
  "phases_open": ["ground-in-target", "composition", "port-maps", "optimization-register",
                  "spec", "elicit", "execute", "verify"],
  "evidence": { "screens": 0, "features_confirmed": 0, "features_cut": 0,
                "entities": 0, "theater_findings": 0, "theater_to_implement": 0,
                "ambiguities_resolved": 0, "ambiguities_deferred": 0 },
  "constraints": { "visual_fidelity": "pixel|brand|functional",
                   "priorities": { "P0": [], "P1": [], "P2": [] },
                   "non_goals": [] },
  "caveats": ["no server existed in the source", "..."]
}
```

`phases_satisfied` is a claim about evidence, not a permission slip. `reverify: "anchors
only"` means port-app should confirm the cited lines still exist -- they will, `_src` is
immutable -- and skip re-deriving the content.

## The handoff (Phase 8)

Invoke the `microdots-port-app` skill with:

    <dossier>/_src --target <target> --slug <slug> --out <dossier> --mode <plan→spec|scaffold|full> --no-browser

`--no-browser` is dropped when `--serve` produced a real walk. `--mode plan` maps to
port-app's `--mode spec` (it stops after elicitation); `scaffold` and `full` pass through.

State three things in the invocation, in plain words, because they change what it does:

1. The dossier is **pre-populated** by `microdots-port-prototype`; read
   `dossier-manifest.json` first and skip the phases it declares satisfied.
2. The source is an **extracted prototype**, not an application: no server, no
   persistence, no auth ever existed. The theater register in `synthesis.json` is the
   list of operations that must be built, and `seams.md` is the composition evidence.
3. The composition decision and its user gate are still **its** job, not done here.

Then let it run its own phases. Do not pre-empt its composition proposal, do not answer
its decision register, and do not duplicate `spec-elicitation`.

## When the handoff cannot run

`--no-handoff`, or `microdots-port-app` unavailable: stop with the dossier as the
deliverable and say plainly, in the report, that composition, the port maps, the
optimization register and the spec have **not** been settled -- and that the dossier is
an input to that work, not a substitute for it.
