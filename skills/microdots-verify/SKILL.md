---
name: microdots-verify
description: Verify a change to a MicroDots workspace is actually done — typecheck, lint, test, build every MicroDot bundle, then boot the system and confirm in a browser that the dots render and poll their services. Use before reporting any change to a MicroDots workspace complete.
---

Green static checks are not sufficient in a MicroDots workspace. `Runtime.embed`
runs the Foldkit runtime in a forked fiber, so a startup defect produces a blank
MicroDot with a clean console — typecheck, lint, tests and build have all passed
in real workspaces while every dot rendered nothing. **The browser step is the
point of this skill; do not skip it.**

## 0. Resolve the workspace

Do not assume script names or paths. Derive them once:

```bash
jq -r '.scripts | keys[]' package.json          # available scripts
ls -d microdots micros apps/host 2>/dev/null     # dot dir + host
```

| What you need     | Where it comes from                                                                      |
| ----------------- | ---------------------------------------------------------------------------------------- |
| Static-check cmd  | `check` script if present, else compose `typecheck` + `lint` + `test`                    |
| Build cmd         | `build` script                                                                            |
| Dev cmd           | `dev` script                                                                              |
| Dot directory     | `microdots/` (current) or `micros/` (older workspaces)                                    |
| Element package   | grep a dot's `element.ts` import — `@bespokeagentics/microdots-element`, `@microdots/element`, or `@kit/element` |
| Host URL + ports  | **read them off the `dev` output**, never from memory                                     |

If none of these resolve, this is not a MicroDots workspace — say so and stop.

## 1. Static checks

Run the resolved static-check command (typically `bun run check` → typecheck →
lint → test). Fix anything that fails before continuing.

## 2. Build every bundle

Run the build. This proves each MicroDot bundle and the host still compile.
Watch for:

- **a dot bundle that suddenly grows by hundreds of kB** — usually a Node-only
  import leaking into the browser. The runtime package is browser-only; its
  `/service` entry point is Node-only. Check which entry a file imports.
- **the host bundle growing past ~20 kB** — it must not contain MicroDot code.
  The host loads bundles by URL; it never imports a dot's source.

## 3. Boot the system

Run the dev command. Wait for the services to log `Listening on ...` and the
host to log its URL. **Note the host URL and each service port from that
output** — steps 4 and 5 need them, and hardcoding the numbers from another
workspace is how this check silently inspects nothing.

If a port is already taken, find and stop the stale process rather than
switching ports — switching hides the collision from the next run.

## 4. Confirm in a browser

Open the host URL the dev command printed and check, for **each** MicroDot:

- it rendered actual content (not an empty element)
- its value changes over time — it is polling its own service
- the host event log is receiving its events

Then exercise the wiring:

- change a host control and confirm the corresponding dot reacts
- unmount a dot and confirm the others are unaffected
- remount it and confirm it comes back live

Verify by inspecting the DOM and network activity, not just a screenshot.
Two failure modes are invisible to a naive check:

- **`Runtime.embed` replaces the container node**, so reading
  `container.innerHTML` inspects a detached element and always looks empty.
  Assert against the parent or `document.body.textContent`.
- **zero requests to a service port** means the runtime never started, even
  though `embed` returned a handle.

If the workspace runs Foldkit devtools, the `foldkit_*` MCP tools inspect Model,
Message history, and support time-travel while `dev` is up. Reach for them
before `console.log`.

## 5. If a MicroDot is blank

`embed` swallows the startup defect. Get the real error by running the program's
`start` effect directly and inspecting the `Exit` — the message is in
`cause.reasons[0].defect`. The most common cause is a mount container without an
`id`; everything must mount through the element package's `mountPoint`.

`microdots-debug-blank` walks the full protocol — the stage isolation, the known
causes, and the CORS lies that read as a blank dot.

## 6. Report honestly

State what passed and what you actually observed in the browser. If you could
not complete the browser step, say so explicitly rather than implying the change
is verified.
