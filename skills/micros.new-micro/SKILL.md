---
name: new-micro
description: Scaffold a new micro-app end to end — runs the generator, completes the wiring steps it only prints (bun install, tsconfig path, vitest alias, host registry + slot), and, given a feature brief, ports matching prior art from docs/reuse-catalog.md in the same run.
disable-model-invocation: true
---

Scaffold and fully wire a new micro-app from `$ARGUMENTS`: the first word is
the lower-kebab name, everything after it is an OPTIONAL feature brief
describing what the micro-app should do. With a brief, matched prior art is
ported after the scaffold; without one, the scaffold is unchanged and the
report lists which cataloged patterns look relevant.

`bun run new:micro` writes the files but deliberately leaves the wiring to the
caller. This skill does all of it, so the new micro-app is usable immediately.

## 1. Parse the arguments and consult the catalog

Split `$ARGUMENTS` into `<name>` (first word) and the brief (the rest, possibly
empty). Read `docs/reuse-catalog.md` and match the brief against its Trigger
index; write down the matched pattern IDs now — steps 6 and 9 both use the
list. This repo has solved auth gates, storage, admin dashboards and more
already; building one from scratch because nobody looked is the failure this
step exists to prevent.

With no brief: still read the catalog and shortlist the patterns whose triggers
plausibly fit the name — the report prints the shortlist instead of porting.

## 2. Generate

```bash
bun run new:micro <name>
```

The name ONLY, never the brief — the generator reads a single argument and
validates it as lower-kebab. It picks the next free port and prints the tag
(`<name>-panel`) and port. Note both — later steps need them. It refuses to
overwrite an existing micro-app or reuse a claimed port; if it errors, stop and
report rather than forcing it.

## 3. Link the workspace

```bash
bun install
```

## 4. Register the contract path

Add to `tsconfig.json` under `compilerOptions.paths`:

```json
"@micro/<name>/contract": ["./micros/<name>/src/contract.ts"]
```

And the matching alias in `vitest.config.ts` under `resolve.alias`:

```ts
'@micro/<name>/contract': resolve(here, 'micros/<name>/src/contract.ts'),
```

Keep both lists alphabetically consistent with the existing entries.

## 5. Wire the host

Append to `registry` in `apps/host/src/registry.ts`:

```ts
{
  tag: '<name>-panel',
  bundle: '/micros/<name>-panel.js',
  localPort: <port>,
  deployedApiUrl: 'https://effect-microapps-<name>.<account>.workers.dev',
  attributes: { label: 'default' },
},
```

`apiUrlFor` resolves the URL at runtime — `localhost:<localPort>` during
`bun run dev`, `deployedApiUrl` everywhere else. `deployedApiUrl` is required
by the type before any deploy exists; use the projected Workers URL — the
registry tests reject anything that is not https or that mentions localhost.

Then the section and its route, neither optional. Add to the flex-wrap container
in `apps/host/index.html`, alongside the existing sections:

```html
<section
  id="section-<name>"
  class="flex min-w-80 grow basis-[calc(50%-0.5rem)] flex-col gap-3"
>
  <div class="flex flex-col gap-1">
    <h2 class="text-sm font-semibold text-gray-900"><Name></h2>
    <p class="text-xs text-gray-600">One line on what it does.</p>
  </div>
  <div id="<name>-slot"></div>
</section>
```

and a route to `componentRoutes` in `apps/host/src/routes.ts` — the overview
route and the nav are derived from it, so this is the only place to edit:

```ts
{
  path: '/<name>',
  label: '<Name>',
  title: `<Name> — ${TITLE}`,
  sectionIds: ['section-<name>'],
  mounts: [{ tag: '<name>-panel', slotId: '<name>-slot' }],
},
```

`apps/host/src/entry.ts` needs nothing. It throws at startup for a registry tag
no route mounts, and `routes.test.ts` parses `index.html` and fails for a
section or slot id the markup does not have — skipping either step is a blank
page, not a type error. The host must never import the micro-app's source —
only the registry entry, the section and the route.

## 6. Port the matched patterns

Skip cleanly when there is no brief. Otherwise, for each pattern ID from
step 1, follow its catalog entry — but verify before trusting:

```bash
ls <each listed path>
```

A missing path means the CATALOG ENTRY rotted, not that the pattern is gone.
Grep the entry's Key symbols to find where the code moved:

```bash
grep -rn '<key symbol>' micros packages
```

Port from where the code actually is, and fix the catalog entry in this run —
a rotted entry you worked around silently will rot for the next agent too. If
the Key symbols grep to nothing, the pattern was removed: delete the entry,
fall back to step 7's scan, and say so in the report.

`shared` pieces are imported from `@kit/effect`, never copied — confirm the
export resolves (grep `packages/kit-effect/src/` and its `exports` map) before
leaning on it. `copy-adapt` pieces are ported per the entry's Adaptation notes.
A P4 (multi-tag) port loops back to step 5: one registry entry and one slot per
tag, and every entry sharing the bundle must agree on `localPort` and
`deployedApiUrl`.

## 7. Scan for uncataloged prior art

For any feature in the brief that no trigger matched, grep a couple of feature
keywords across `micros/*/src` and `micros/*/service` before writing it from
scratch. Prior art found this way gets ported the same way as step 6 AND
flagged as a catalog candidate for step 9. Nothing found: build fresh — and
consider whether what you build belongs in the catalog.

## 8. Verify

```bash
bun run check
cd micros/<name> && bunx vite build && cd -
```

Then confirm the service boots:

```bash
cd micros/<name> && timeout 6 bun service/main.ts
```

Expect `Listening on http://0.0.0.0:<port>`. Free the port first if it is
taken.

For a micro-app that will actually be used, finish with `/verify` to confirm it
renders and polls in a browser.

## 9. Update the catalog and report

Catalog maintenance is part of the run, not a TODO: fix any rotted entries
found in step 6, and append an entry (template at the bottom of the catalog)
plus a Trigger index row for any genuinely reusable pattern this micro-app
shipped.

Then report: the tag, the port, the files created, the wiring completed, the
patterns ported and what was adapted, which pieces were imported from
`@kit/effect` versus copy-adapted (and why), catalog entries added or fixed,
and that any unported scaffold pieces (contract, handler, view) are
placeholders to be replaced with the real domain. With no brief, report the
relevant-pattern shortlist here instead.
