---
name: microdots-new-micro
description: Create a MicroDot — either an application workspace through the catalog-locked compiler, or a deliberate repository extension (reference dot, capability proof) carrying every integration and knowledge-record obligation. The two modes never share source-writing duties. Use for "new MicroDot", "scaffold a micro-app", "add a dot to this workspace".
disable-model-invocation: true
---

Create a MicroDot from `$ARGUMENTS`, but **classify the workflow before writing
anything.** Ordinary product/application requests use **application mode**. A
reference dot, capability proof, catalog definition or accepted `catalog-gap`
uses **repository-extension mode**. A generic request for "a new MicroDot" is an
application request; do not silently turn it into a repository extension.

## 0. Resolve the workspace and the available modes

```bash
jq -r '.scripts | keys[]' package.json
ls -d microdots micros apps/host packages docs/reuse-catalog.md wiki 2>/dev/null
ls scripts/microdots-authoring.ts scripts/new-microdot.ts scripts/new-micro.ts 2>/dev/null
```

| Marker                          | What it means                                                              |
| ------------------------------- | -------------------------------------------------------------------------- |
| `scripts/microdots-authoring.ts` + a `new:microdot` script taking `application` | **Both modes available.** Use the classification above. |
| Only a generator script (`new:microdot` / `new:micro` with a bare name) | **Repository-extension mode only** — the compiler lane does not exist here. Say so before proceeding. |
| `microdots/`                    | current framework layout; bundles live under `/microdots/`                  |
| `micros/`                       | older workspace layout; bundles live under `/micros/`                       |
| `docs/reuse-catalog.md`         | the prior-art catalog steps 1, 10 and 14 depend on                          |
| `wiki/`                         | the knowledge-record obligations in step 13 apply                           |

Where both modes exist, the executable boundary is explicit:

```text
bun run new:microdot application --input <selection.json> --destination <dir>
bun run new:microdot repository <name>
```

A bare `bun run new:microdot <name>` remains a repository compatibility alias
for humans and old automation. **This skill always names the mode.**

---

# Application mode — compiler-owned workspace

Use this mode when the outcome is an application workspace. The model may
interpret the brief and fill semantic JSON; **it does not read or copy existing
MicroDot source, choose tags/ports/imports, or edit generated files.**

1. Read `docs/reuse-catalog.md`, then query only the executable slice the
   request needs:

   ```bash
   bun scripts/microdots-authoring.ts inspect-catalog
   bun scripts/microdots-authoring.ts schema-for-selection
   ```

   Both read one JSON object from stdin or `--input <path>`. Re-run the schema
   operation after each shape, target or capability choice so parameter controls
   stay catalog-derived.

2. Produce one `AuthoringSelectionV1` JSON value. Workbench-originated choices
   require `selectedBy: human` or `model-recommended-human-confirmed`; a
   headless skill call uses `selectedBy: caller`. Set `client` to `cli`. A
   degraded option needs the exact consequence acknowledgement the schema or
   catalog returned.

3. Compile into an **empty destination whose parent already exists**:

   ```bash
   bun run new:microdot application \
     --input <selection.json> \
     --destination <workspace-dir>
   ```

   A destination inside the repository's own dot directory is rejected,
   including through a symlinked parent: application mode never acquires host
   registry, deploy inventory, invariant or wiki authority.

4. Verify structurally through the same operation surface:

   ```bash
   bun scripts/microdots-authoring.ts verify-workspace --input <verify-input.json>
   ```

   Then use `microdots-verify` for build, service, DOM, RPC and polling
   evidence. **The structural report is not browser proof.**

5. If compilation returns `catalog-gap`, **stop the application lane.** Explain
   it with `explain-issue` and offer a deliberate repository/framework
   extension; never fall through to general source generation.

Report the selection, catalog lock, receipt hash, destination and the evidence
actually run.

Application mode performs **no** `bun install`, root tsconfig/alias edit, host
registry/markup/topology edit, deploy-discovery edit or wiki inventory edit.

---

# Repository-extension mode — framework/reference integration

Use the remaining steps only when the request explicitly adds a reference dot,
capability proof or other repository-owned framework artifact. This lane keeps
the full integration and knowledge-record obligations.

## 1. Parse the arguments and consult the catalog

Split `$ARGUMENTS` into `<name>` (lower-kebab) and the brief (the rest, possibly
empty). Read `docs/reuse-catalog.md` and match the brief against its Trigger
index; **write down the matched pattern IDs now** — steps 10 and 13 both use the
list. A mature workspace has usually solved auth gates, storage and dashboards
already; building one from scratch because nobody looked is the failure this
step exists to prevent.

With no brief: still read the catalog and shortlist the patterns whose triggers
plausibly fit the name — the report prints the shortlist instead of porting.

## 2. Generate

```bash
bun run new:microdot repository <name>
```

**The name ONLY, never the brief** — the mode validates it as lower-kebab.

The generator computes the port as **one past the highest claimed port**, not
`base + count`: ports stop being contiguous the moment a dot is removed or
moved, and the counting form hands out a port that is already bound. Read the
generator's own port logic if the number surprises you:

```bash
grep -rn "nextFreePort\|highest" scripts/new-microdot.ts packages/*generate*/src/index.ts
```

It prints the tag (`<name>-panel`) and port. **Note both** — later steps need
them. It refuses to overwrite an existing MicroDot or reuse a claimed port; if
it errors, stop and report rather than forcing it.

The generator prints numbered next steps. Steps 3–9 below are those steps,
**done rather than printed.**

Before moving on, confirm the generated `vite.config.ts` registers the manifest
plugin — the `emitMicroDotManifest` import and its entry in `plugins`. Without
it the bundle still builds, nothing goes red, and every badge for the dot's tags
quietly derives `draft`. **The specifier is BARE, never a relative path**: the
generator writes this config at several depths and a relative path is correct at
only one of them. It resolves through the ROOT `package.json` devDependency —
do not move that declaration onto a dot.

## 3. Link the workspace

```bash
bun install
```

## 4. Register the contract path

Add to `tsconfig.json` under `compilerOptions.paths`:

```json
"@microdots/<name>/contract": ["./<dot-dir>/<name>/src/contract.ts"]
```

And the matching alias in `vitest.config.ts` under `resolve.alias`. **Append**
both — the existing lists are insertion-ordered, not alphabetical. Keep tsconfig
and vitest consistent with each other. Match the alias prefix the workspace
already uses; do not introduce a new one.

## 5. Register the element with the host

Append to `registry` in `apps/host/src/registry.ts`:

```ts
{
  tag: '<name>-panel',
  bundle: '/<bundle-prefix>/<name>-panel.js',
  localPort: <port>,
  deployedApiUrl: 'https://<projected-workers-url>',
  attributes: {},
},
```

`<bundle-prefix>` matches the existing entries exactly — copy it, do not guess.

**One entry per registered ELEMENT, not per MicroDot.** A dot registering two
tags gets two entries sharing one bundle, and every entry sharing a bundle must
agree on `localPort` and `deployedApiUrl`.

`apiUrlFor` resolves the URL at runtime — `localhost:<localPort>` during `dev`,
`deployedApiUrl` everywhere else. `deployedApiUrl` is required by the type
before any deploy exists; use the projected Workers URL. The registry tests
reject anything that is not https or that mentions localhost.

`attributes` stays `{}` where the workspace carries attribute VALUES on the
topology placement's `values` (step 7). Check an existing entry before deciding.

## 6. Add the markup slot

Add to the host's section container in `apps/host/index.html`, alongside the
existing sections:

```html
<section
  id="section-<name>"
  class="flex min-w-80 grow basis-[calc(50%-0.5rem)] flex-col gap-3"
>
  <div class="flex flex-col gap-1">
    <h2 class="text-body-m font-semibold text-fg-heading"><Name></h2>
    <p class="text-body-s text-fg-muted">One line on what it does.</p>
  </div>
  <div id="<name>-slot"></div>
</section>
```

**Brand tokens only** — `text-fg-heading`, not `text-gray-900`.

## 7. Add the route to the topology

The host's `routes.ts` decodes `apps/host/host-topology.json` at module scope —
**the route is DATA, not authored code.** Append to `routes`:

```json
{
  "path": "/<name>",
  "label": "<Name>",
  "title": "<Name> — <the file's own host.label>",
  "sectionIds": ["section-<name>"],
  "mounts": [{ "tag": "<name>-panel", "slotId": "<name>-slot" }]
}
```

A mount may also carry `values` (the attributes this placement supplies), and
`condition` / `envs` / `span` / `order` — all optional, none needed for a plain
scaffold. The overview route stays DERIVED; there is nothing to add for it.

## 8. Declare the slot in the slot manifest

A new slot needs markup **AND** a `slotManifest` entry. Append to
`slotManifest.slots` in the SAME file:

```json
{ "id": "<name>-slot", "kind": "band", "row": <next free row>, "capacity": 1 }
```

`band` with `capacity: 1` on a fresh `row` is what a flex-wrap host markup
actually holds — do not invent a grid. Skip this and the host's
"every mounted slotId is a declared slot" assertion fails; the routes suite
fails in the other direction if the manifest declares a slot the markup has no
element for.

`apps/host/src/entry.ts` needs nothing. It throws at startup for a registry tag
no route mounts, and the two suites above fail for a missing section, slot or
manifest entry — **skipping any of steps 5–8 is a blank page, not a type
error.** The host must never import the dot's source; the registry entry, the
section, the route and the slot declaration are the whole seam.

## 9. Register a deployable dot with deploy discovery

**Applies to every plain scaffold** where the workspace ships a deploy MicroDot.
The generator writes both `service/worker.ts` and `wrangler.jsonc`, so a freshly
generated dot IS deployable and this step is due immediately. Skip it only for a
dot whose `wrangler.jsonc` you deliberately delete.

```bash
ls <dot-dir>/deploy/service/discovery.test.ts 2>/dev/null
```

Deploy discovery treats a `wrangler.jsonc` as the whole signal and asserts the
discovered set against the **real repository**, not a fixture. Add `repo:<name>`
to the expected list, keeping the file's existing ordering. That assertion
exists so a new deployable dot cannot quietly grow a row on the deploy screen —
so it is **supposed** to fail once. **The fix is to accept the new dot there,
never to loosen the assertion.** A deliberately Worker-less dot belongs in the
second test's absent list instead.

This is the step the generator does not print, and the one this skill exists to
stop you from missing.

## 10. Port the matched patterns

Skip cleanly when there is no brief. Otherwise, for each pattern ID from step 1,
follow its catalog entry — **but verify before trusting**:

```bash
ls <each listed path>
```

A missing path means the CATALOG ENTRY rotted, not that the pattern is gone.
Grep the entry's Key symbols to find where the code moved:

```bash
grep -rn '<key symbol>' <dot-dir> packages
```

Port from where the code actually is, and **fix the catalog entry in this run** —
a rotted entry you worked around silently will rot for the next agent too. If
the Key symbols grep to nothing, the pattern was removed: delete the entry, fall
back to step 11's scan, and say so in the report.

`shared` pieces are **imported from the runtime package, never copied** —
confirm the export resolves (grep the runtime's `src/` and its `exports` map)
before leaning on it. `copy-adapt` pieces are ported per the entry's Adaptation
notes. A multi-tag port loops back through steps 5–8: one registry entry, one
markup slot, one mount and one manifest slot **per tag**.

## 11. Scan for uncataloged prior art

For any feature in the brief that no trigger matched, grep a couple of feature
keywords across `<dot-dir>/*/src` and `<dot-dir>/*/service` before writing it
from scratch. Prior art found this way gets ported the same way as step 10 AND
flagged as a catalog candidate for step 14. Nothing found: build fresh — and
consider whether what you build belongs in the catalog.

## 12. Verify

```bash
bun run check
cd <dot-dir>/<name> && bunx vite build && cd -
cd <dot-dir>/<name> && timeout 6 bun service/main.ts
```

Expect `Listening on http://0.0.0.0:<port>`. Free the port first if it is taken.

For a MicroDot that will actually be used, finish with `microdots-verify` to
confirm it renders and polls in a browser.

## 13. Record it in the wiki

Only where the workspace has a `wiki/`. It is the source of record, and a
MicroDot with no page is invisible to the next session. Four edits, **all in the
same run as the code**:

- `wiki/examples/<name>.md` — an `entity` page, `entity-type: microdot`, with a
  `## Surface` table (directory, tags, port, attributes in, events out, storage,
  secrets, Worker entry, host route) and `## Source References`. Copy the shape
  from an existing example page.
- a row in the inventory table of `wiki/examples/_index.md`
- the inventory sentence in `AGENTS.md` (count, port range, the dot's tags)
- a row in `wiki/_log.md`

With a brief, also author `wiki/plans/active/<name>.md` as a `decision` page
with a `status-color` and an `## Outcome` block; it moves to `shipped/` only
when its own done-bar is met.

## 14. Update the catalog and report

**Catalog maintenance is part of the run, not a TODO.** Fix any rotted entries
found in step 10, and append an entry (template at the bottom of the catalog)
plus a Trigger index row for any genuinely reusable pattern this MicroDot
shipped.

Then report: the tag, the port, the files created, the wiring completed, the
patterns ported and what was adapted, which pieces were imported from the
runtime package versus copy-adapted (and why), catalog entries added or fixed,
and that any unported scaffold pieces (contract, handler, view) are placeholders
to be replaced with the real domain. With no brief, report the relevant-pattern
shortlist here instead.
