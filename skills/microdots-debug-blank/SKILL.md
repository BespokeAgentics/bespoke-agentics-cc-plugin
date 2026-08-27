---
name: microdots-debug-blank
description: Diagnose a MicroDot that renders nothing, renders stale, or never reaches its service — the framework's most expensive failure shape, because every signal you would normally trust says the system is healthy. Use when a MicroDot is blank, when the console is clean but nothing appears, when a dot stops polling, or when "Could not reach the service" comes from a page that plainly exists.
---

A blank MicroDot is the one failure in this framework that defeats every normal
signal. `Runtime.embed` forks the runtime, so a startup defect never reaches the
console — typecheck, lint, tests and build have all passed in real workspaces
while every MicroDot on the page rendered nothing.

Work the steps in order. Each is cheaper than the one after it, and step 1 rules
out the most common false alarm: a MicroDot that is fine and a check that is
wrong.

## 0. Resolve the workspace

Derive these once; do not carry numbers or paths over from another workspace.

```bash
ls -d microdots micros apps/host packages wiki 2>/dev/null
grep -rn "defineMicroDot\|mountPoint" --include=*.ts . | head
```

| What you need    | How to find it                                                                     |
| ---------------- | ------------------------------------------------------------------------------------ |
| Dot directory    | `microdots/` (current) or `micros/` (older workspaces)                                |
| Element package  | the import in a dot's `element.ts` — `@bespokeagentics/microdots-element`, `@microdots/element`, or `@kit/element` |
| Runtime package  | the import in a dot's `app.ts` / `service/main.ts`                                     |
| Bundle URL path  | the `bundle` field in `apps/host/src/registry.ts` (`/microdots/<tag>.js` or `/micros/<tag>.js`) |
| Service ports    | the host registry's `localPort` values, or the `dev` output — **never assume a range** |
| Host URL         | the `dev` command's own output                                                         |

## 1. Confirm it is actually blank

`Runtime.embed` **replaces** the container node rather than filling it. Any
reference you held is detached the moment the runtime starts, so
`container.innerHTML` reads empty on a MicroDot that is rendering perfectly. The
mechanism is documented at the top of the element package's `mountPoint`
source:

```bash
grep -rn -A6 "mountPoint" packages/*element*/src/mountPoint.ts
```

Assert against the **parent** or `document.body.textContent`:

```js
document.querySelector('#<name>-slot')?.textContent
```

If that has content, the MicroDot is fine and the test or check is wrong. Fix
the assertion, not the component.

## 2. Establish which stage failed

Three stages can fail, and they look identical on screen. Separate them before
theorising.

**Did the bundle load?** Look for a 404 on the dot's bundle URL in the network
panel. During `dev` the bundles are served by the workspace's bundle-serving
script; after `build` they are copied into the host.

**Did the element register?**

```js
customElements.get('<tag>')
```

`undefined` means the bundle never executed its `entry.ts`, or `element.ts`
never called `defineMicroDot`.

**Did the runtime start?** Filter the network panel to that dot's service port
(from the registry's `localPort`). **Zero requests means the runtime never
started**, even though `embed` returned a handle. That is the signature of a
swallowed startup defect — go to step 3.

Requests present but failing is a different problem — go to step 4.

With `dev` up, the `foldkit_*` MCP tools inspect Model, Message history and
support time-travel on the devtools port the dev output prints. Reach for them
before `console.log`.

## 3. Extract the swallowed defect

This is the step that exists because nothing else will tell you. Run the
program's `start` effect directly instead of through `embed`, and inspect the
`Exit`:

```
cause.reasons[0].defect
```

That is where the real message is. `embed` discards it.

Then match the message against the known causes, most common first:

| Message or symptom                            | Cause                                                                              | Fix                                                                                       |
| --------------------------------------------- | ---------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| ``Runtime container must have an `id` ``      | Foldkit keys HMR model preservation off the container `id` and throws without one  | Mount through the element package's `mountPoint`. **Never hand-roll a container**          |
| A `bun:*` or Node built-in failing to resolve | A Node-only import leaked into the browser bundle                                  | The runtime package is browser-only; its `/service` entry is Node. Check which entry the file imports |
| `Array.filterMap` returned `[]`               | Effect v4 expects a `Result`, not an `Option`                                      | `Array.getSomes(Array.map(xs, f))`                                                          |
| Nothing throws, model never updates           | An init effect that never completes                                                | Inspect the Model with `foldkit_*` and find the port that never fires                       |

## 4. The dot renders but cannot reach its service

"Could not reach the service" from a page that plainly exists is almost always
CORS, and it presents as three different lies.

**Origin not allowlisted.** The runtime's origins allowlist (`MICRODOT_ORIGINS`,
read in the runtime package's `cors.ts`) is **exact-matched against what the
browser sends**. `http://127.0.0.1:5173` does not match `http://localhost:5173`.
A new port, a new dev server or a new deploy target needs an entry:

```bash
grep -rn "MICRODOT_ORIGINS" packages/*runtime*/src/cors.ts
```

**A crash wearing a CORS costume.** Cloudflare's 1101 error page carries no
allow-origin header, so a Worker that threw reads in the console as a CORS
failure. Check the Worker's own logs before believing the browser.

**A Worker that hangs after the first request.** `toWebHandler` at module scope.
The entry must be a single call to `makeMicroDotWorker`. Diff the failing dot's
`service/worker.ts` against a dot in the same workspace that deploys correctly.

## 5. The dot renders once and then goes stale

A brokered nudge is an optimisation; **a poll is the floor**. A dot that
refreshes only on a host-brokered event goes stale on any host that does not
broker — including a foreign host embedding it alone. Confirm the dot polls its
own service on its own schedule, then treat the broker as the accelerator it is.

If the dot is stale only on one route, check the host topology
(`apps/host/host-topology.json`): a mount whose `slotId` is not in
`slotManifest.slots`, or a `sectionIds` entry with no matching `<section id>`,
renders as a blank page rather than an error. The host's own suites catch both:

```bash
bunx vitest run apps/host/src/topology.test.ts apps/host/src/routes.test.ts
```

## 6. Check the trap index before inventing a theory

If the workspace has a wiki, its trap pages are indexed by **symptom**
(`wiki/patterns-and-traps/_index.md`). Most cost hours precisely because the
symptom points at the wrong cause. If steps 1–5 did not land it, search that
index by what you are seeing, not by what you think is wrong.

## 7. Write the page before you commit the fix

A trap that cost real time gets its page in `wiki/patterns-and-traps/`
**before** the fix is committed — `type: gap`, tagged `#trap`, with `severity`
set to the cost of rediscovering it, linked both to the MicroDot it bit and to
the component responsible. Every claim cites `file.ts:line`. Then append to
`wiki/_log.md`. Conform to the workspace's own `wiki/_schema/SCHEMA.md`.

No wiki in the workspace: record the trap wherever that project keeps durable
knowledge, and say where you put it.

Finish with `microdots-verify` — a blank MicroDot is exactly the defect that
green static checks do not catch, so the browser step is the only proof the fix
worked.
